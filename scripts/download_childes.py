"""Build empirical CHILDES lexical frequency lists for ChildSafe profiles."""

from __future__ import annotations

import argparse
import io
import json
import logging
import re
import sys
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence
from xml.etree import ElementTree

ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "data" / "childes_lexicon"
DEFAULT_MIN_FREQUENCY = 5
DEFAULT_TIMEOUT_SECONDS = 60
TALKBANK_ACCESS_URL = "https://talkbank.org/childes/access/Eng-NA/"
CHILDES_XML_URL_TEMPLATES: tuple[str, ...] = (
    "https://childes.talkbank.org/data-xml/Eng-USA/{corpus_id}.zip",
    "https://childes.talkbank.org/data-xml/Eng-USA-MOR/{corpus_id}.zip",
)
TALKBANK_XML_NAMESPACE = {"tb": "http://www.talkbank.org/ns/talkbank"}
TOKEN_PATTERN = re.compile(r"[a-z]+(?:'[a-z]+)?")
AGE_DURATION_PATTERN = re.compile(
    r"^P(?:(?P<years>\d+)Y)?(?:(?P<months>\d+)M)?(?:(?P<days>\d+)D)?$"
)
AGE_CHAT_PATTERN = re.compile(
    r"^(?P<years>\d+);(?P<months>\d+)(?:\.(?P<days>\d+))?$"
)
KNOWN_CHILD_DIRECTED_CODES = {
    "CHI",
    "MOT",
    "FAT",
    "MOM",
    "DAD",
    "CAR",
    "ADU",
    "GRM",
    "GRF",
    "INV",
    "TEA",
    "EXA",
    "CLN",
}
KNOWN_CHILD_DIRECTED_ROLE_KEYWORDS = (
    "mother",
    "father",
    "caregiver",
    "adult",
    "grandmother",
    "grandfather",
    "teacher",
    "investigator",
    "examiner",
    "clinician",
)
# These corpora are listed on the official Eng-NA access page with age ranges
# that intersect the D1-D4 bins (72+ months). Remote fallback only downloads
# these corpora to avoid fetching the entire collection unnecessarily.
REMOTE_ENG_NA_CORPORA: tuple[str, ...] = (
    "Bliss",
    "Gelman",
    "Gillam",
    "HSLLD",
    "MacWhinney",
    "Nadig",
    "Nippold",
    "OCSC",
    "POLER-Controls",
    "Rondal-TD",
    "Sprott",
    "Warren-Leubecker",
)

LOGGER = logging.getLogger("childsafe.download_childes")


@dataclass(frozen=True)
class DevelopmentalBin:
    """Age bin metadata for a DevelopmentalProfile lexical band."""

    profile_key: str
    filename: str
    minimum_months: int
    maximum_months: int | None

    def matches(self, age_months: int) -> bool:
        """Return whether the given age in months belongs to this bin."""

        if age_months < self.minimum_months:
            return False
        if self.maximum_months is None:
            return True
        return age_months <= self.maximum_months


@dataclass(frozen=True)
class BuildSummary:
    """Summary statistics emitted after lexicon generation completes."""

    source: str
    processed_transcripts: int
    skipped_missing_age: int
    skipped_out_of_band: int
    output_paths: dict[str, Path]
    vocabulary_sizes: dict[str, int]
    token_counts: dict[str, int]


PROFILE_BINS: tuple[DevelopmentalBin, ...] = (
    DevelopmentalBin("d1_early", "d1_early.json", 72, 107),
    DevelopmentalBin("d2_mid", "d2_mid.json", 108, 143),
    DevelopmentalBin("d3_late", "d3_late.json", 144, 179),
    DevelopmentalBin("d4_teen", "d4_teen.json", 180, None),
)


def build_childes_lexicons(
    output_dir: Path = OUTPUT_DIR,
    min_frequency: int = DEFAULT_MIN_FREQUENCY,
    corpus_root: Path | None = None,
    nltk_data_dir: Path | None = None,
    cache_dir: Path | None = None,
    allow_download: bool = True,
    remote_corpora: Sequence[str] | None = None,
) -> BuildSummary:
    """
    Build empirical CHILDES lexical frequency lists for the SDK.

    The pipeline prefers a local or downloaded NLTK CHILDES XML mirror accessed
    through `CHILDESCorpusReader`. If that corpus is unavailable, it falls back
    to downloading XML corpus archives directly from TalkBank's Eng-NA
    collection and parsing them with `xml.etree.ElementTree`.

    Args:
        output_dir: Destination directory for the four JSON lexicon files.
        min_frequency: Minimum corpus count required for a word to be kept.
        corpus_root: Optional explicit path to a local CHILDES XML root.
        nltk_data_dir: Optional NLTK data directory for corpus discovery.
        cache_dir: Optional cache directory for downloaded TalkBank archives.
        allow_download: Whether the pipeline may download missing corpora.
        remote_corpora: Optional explicit Eng-NA corpus identifiers to fetch
            when using the TalkBank fallback.

    Returns:
        A summary describing the generated lexicons and corpus coverage.

    Raises:
        ValueError: If `min_frequency` is invalid.
        RuntimeError: If neither the NLTK corpus nor the TalkBank fallback can
            provide CHILDES XML transcripts.
    """

    if min_frequency < 1:
        raise ValueError("min_frequency must be at least 1")

    counters = {band.profile_key: Counter() for band in PROFILE_BINS}
    processed_transcripts = 0
    ingestion_stats = {"skipped_missing_age": 0}
    skipped_out_of_band = 0
    source_name = "nltk"

    try:
        transcript_stream = _iter_nltk_transcripts(
            corpus_root=corpus_root,
            nltk_data_dir=nltk_data_dir,
            allow_download=allow_download,
            ingestion_stats=ingestion_stats,
        )
        LOGGER.info("Using NLTK CHILDESCorpusReader against the XML corpus mirror.")
    except RuntimeError as error:
        if not allow_download:
            raise
        LOGGER.warning("%s Falling back to direct TalkBank XML ingestion.", error)
        source_name = "talkbank"
        transcript_stream = _iter_talkbank_transcripts(
            cache_dir=cache_dir,
            corpus_ids=tuple(remote_corpora or REMOTE_ENG_NA_CORPORA),
            ingestion_stats=ingestion_stats,
        )

    for transcript_id, age_months, raw_tokens in transcript_stream:
        band = _resolve_profile_bin(age_months)
        if band is None:
            skipped_out_of_band += 1
            continue

        cleaned_tokens = list(_clean_tokens(raw_tokens))
        if not cleaned_tokens:
            LOGGER.debug("Skipping %s because no clean lexical tokens were found.", transcript_id)
            continue

        counters[band.profile_key].update(cleaned_tokens)
        processed_transcripts += 1

    if processed_transcripts == 0:
        raise RuntimeError(
            "No qualifying CHILDES transcripts were processed. "
            "Confirm that the corpus contains Eng-NA XML transcripts with CHI age "
            "metadata in the D1-D4 age ranges."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths: dict[str, Path] = {}
    vocabulary_sizes: dict[str, int] = {}
    token_counts: dict[str, int] = {}

    for band in PROFILE_BINS:
        filtered_counter = Counter(
            {
                word: count
                for word, count in counters[band.profile_key].items()
                if count >= min_frequency
            }
        )
        ordered_payload = {
            word: filtered_counter[word]
            for word in sorted(filtered_counter, key=lambda item: (-filtered_counter[item], item))
        }

        output_path = output_dir / band.filename
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(ordered_payload, handle, indent=2, ensure_ascii=False)

        output_paths[band.profile_key] = output_path
        vocabulary_sizes[band.profile_key] = len(ordered_payload)
        token_counts[band.profile_key] = sum(counters[band.profile_key].values())

        if not ordered_payload:
            LOGGER.warning(
                "Profile %s produced an empty lexicon after applying f_min=%d.",
                band.profile_key,
                min_frequency,
            )

    return BuildSummary(
        source=source_name,
        processed_transcripts=processed_transcripts,
        skipped_missing_age=ingestion_stats["skipped_missing_age"],
        skipped_out_of_band=skipped_out_of_band,
        output_paths=output_paths,
        vocabulary_sizes=vocabulary_sizes,
        token_counts=token_counts,
    )


def _iter_nltk_transcripts(
    corpus_root: Path | None,
    nltk_data_dir: Path | None,
    allow_download: bool,
    ingestion_stats: dict[str, int],
) -> Iterator[tuple[str, int, Iterable[str]]]:
    """Yield transcript identifiers, child ages, and raw tokens via NLTK."""

    try:
        import nltk
        from nltk.corpus.reader import CHILDESCorpusReader
    except ImportError as error:
        raise RuntimeError(
            "NLTK is not installed. Install `nltk` or rely on the TalkBank XML fallback."
        ) from error

    corpus_pointer = _resolve_nltk_corpus_root(
        nltk_module=nltk,
        corpus_root=corpus_root,
        nltk_data_dir=nltk_data_dir,
        allow_download=allow_download,
    )
    reader = CHILDESCorpusReader(corpus_pointer, r".*\.xml")

    def _iterator() -> Iterator[tuple[str, int, Iterable[str]]]:
        for fileid in reader.fileids():
            participants = _normalize_participants(_first_record(reader.participants(fileid)))
            child_code = _identify_child_code(participants)
            if child_code is None:
                ingestion_stats["skipped_missing_age"] += 1
                LOGGER.warning("Skipping %s because CHI metadata is unavailable.", fileid)
                continue

            age_months = _extract_child_age_months(participants, child_code)
            if age_months is None:
                ingestion_stats["skipped_missing_age"] += 1
                LOGGER.warning("Skipping %s because the child age metadata is missing.", fileid)
                continue

            speaker_codes = tuple(_select_speakers(participants, child_code))
            raw_tokens = reader.words(fileid, speaker=list(speaker_codes), replace=True)
            yield fileid, age_months, raw_tokens

    return _iterator()


def _iter_talkbank_transcripts(
    cache_dir: Path | None,
    corpus_ids: Sequence[str],
    ingestion_stats: dict[str, int],
) -> Iterator[tuple[str, int, Iterable[str]]]:
    """Yield transcript identifiers, child ages, and raw tokens from TalkBank XML."""

    try:
        import requests
    except ImportError as error:
        raise RuntimeError(
            "The TalkBank fallback requires `requests`. Install project dependencies first."
        ) from error

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "ChildSafe SDK CHILDES extractor/0.1",
            "Referer": TALKBANK_ACCESS_URL,
        }
    )
    archive_cache = cache_dir or _default_cache_dir()
    archive_cache.mkdir(parents=True, exist_ok=True)

    def _iterator() -> Iterator[tuple[str, int, Iterable[str]]]:
        yielded_any = False
        for corpus_id in corpus_ids:
            archive_bytes = _download_talkbank_archive(
                session=session,
                corpus_id=corpus_id,
                cache_dir=archive_cache,
            )
            with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
                for member_name in archive.namelist():
                    if not member_name.lower().endswith(".xml"):
                        continue

                    with archive.open(member_name) as handle:
                        root = ElementTree.parse(handle).getroot()

                    participants = _participants_from_xml(root)
                    child_code = _identify_child_code(participants)
                    if child_code is None:
                        ingestion_stats["skipped_missing_age"] += 1
                        LOGGER.warning(
                            "Skipping %s/%s because CHI metadata is unavailable.",
                            corpus_id,
                            member_name,
                        )
                        continue

                    age_months = _extract_child_age_months(participants, child_code)
                    if age_months is None:
                        ingestion_stats["skipped_missing_age"] += 1
                        LOGGER.warning(
                            "Skipping %s/%s because the child age metadata is missing.",
                            corpus_id,
                            member_name,
                        )
                        continue

                    speaker_codes = tuple(_select_speakers(participants, child_code))
                    raw_tokens = _words_from_xml(root, speaker_codes)
                    yielded_any = True
                    yield f"{corpus_id}/{member_name}", age_months, raw_tokens

        if not yielded_any:
            raise RuntimeError(
                "The TalkBank fallback did not yield any XML transcripts. "
                "TalkBank may require authenticated access, or the archive layout may "
                "have changed. Supply a local `--corpus-root` or install the NLTK CHILDES "
                "mirror before retrying."
            )

    return _iterator()


def _resolve_nltk_corpus_root(
    nltk_module: Any,
    corpus_root: Path | None,
    nltk_data_dir: Path | None,
    allow_download: bool,
) -> Any:
    """Resolve or download a local NLTK CHILDES XML corpus root."""

    if corpus_root is not None:
        if not corpus_root.exists():
            raise RuntimeError(f"Explicit corpus_root does not exist: {corpus_root}")
        return str(corpus_root)

    if nltk_data_dir is not None:
        nltk_data_dir.mkdir(parents=True, exist_ok=True)
        if str(nltk_data_dir) not in nltk_module.data.path:
            nltk_module.data.path.insert(0, str(nltk_data_dir))

    pointer = _find_nltk_childes_root(nltk_module)
    if pointer is not None:
        return pointer

    if allow_download:
        download_ok = nltk_module.download(
            "childes",
            download_dir=str(nltk_data_dir) if nltk_data_dir is not None else None,
            quiet=False,
            raise_on_error=False,
        )
        if download_ok:
            pointer = _find_nltk_childes_root(nltk_module)
            if pointer is not None:
                return pointer

    raise RuntimeError(
        "Could not locate an NLTK CHILDES XML corpus root. "
        "Run `python -m nltk.downloader childes`, pass `--corpus-root` pointing at a "
        "`data-xml/Eng-USA*` directory, or rely on the TalkBank XML fallback."
    )


def _find_nltk_childes_root(nltk_module: Any) -> Any | None:
    """Return the first available CHILDES XML root discoverable by NLTK."""

    candidate_paths = (
        "corpora/childes/data-xml/Eng-USA-MOR/",
        "corpora/childes/data-xml/Eng-USA/",
        "corpora/CHILDES/data-xml/Eng-USA-MOR/",
        "corpora/CHILDES/data-xml/Eng-USA/",
    )
    for candidate in candidate_paths:
        try:
            return nltk_module.data.find(candidate)
        except LookupError:
            continue
    return None


def _download_talkbank_archive(
    session: requests.Session,
    corpus_id: str,
    cache_dir: Path,
) -> bytes:
    """Download one CHILDES XML archive from TalkBank, caching it on disk."""

    import requests

    cache_path = cache_dir / f"{corpus_id}.zip"
    if cache_path.exists():
        return cache_path.read_bytes()

    last_error: Exception | None = None
    for url_template in CHILDES_XML_URL_TEMPLATES:
        archive_url = url_template.format(corpus_id=corpus_id)
        try:
            response = session.get(archive_url, timeout=DEFAULT_TIMEOUT_SECONDS)
            if response.status_code == 404:
                continue
            response.raise_for_status()
            payload = response.content
            if not _looks_like_zip(payload):
                LOGGER.warning("Skipping non-zip payload from %s", archive_url)
                continue
            cache_path.write_bytes(payload)
            return payload
        except requests.RequestException as error:
            last_error = error
            LOGGER.warning("Failed to download %s: %s", archive_url, error)

    raise RuntimeError(
        f"Unable to download CHILDES XML archive for corpus '{corpus_id}'."
    ) from last_error


def _looks_like_zip(payload: bytes) -> bool:
    """Return whether a response payload appears to be a ZIP archive."""

    return len(payload) >= 4 and payload[:4] == b"PK\x03\x04"


def _participants_from_xml(root: ElementTree.Element) -> dict[str, dict[str, str]]:
    """Extract normalized participant metadata from a TalkBank XML transcript."""

    participants: dict[str, dict[str, str]] = {}
    for participant in root.findall("./tb:Participants/tb:participant", TALKBANK_XML_NAMESPACE):
        speaker_id = participant.get("id")
        if not speaker_id:
            continue
        participants[speaker_id] = {
            key.lower(): value
            for key, value in participant.attrib.items()
            if value
        }
    return participants


def _words_from_xml(
    root: ElementTree.Element,
    speaker_codes: Sequence[str],
) -> Iterator[str]:
    """Yield raw lexical items from selected TalkBank XML utterances."""

    allowed_speakers = set(speaker_codes)
    for utterance in root.findall(".//tb:u", TALKBANK_XML_NAMESPACE):
        if utterance.get("who") not in allowed_speakers:
            continue
        for word in utterance.findall(".//tb:w", TALKBANK_XML_NAMESPACE):
            token = "".join(word.itertext()).strip()
            if token:
                yield token


def _resolve_profile_bin(age_months: int) -> DevelopmentalBin | None:
    """Resolve an age in months to one of the D1-D4 bins."""

    for band in PROFILE_BINS:
        if band.matches(age_months):
            return band
    return None


def _normalize_participants(raw_participants: Any) -> dict[str, dict[str, str]]:
    """Normalize NLTK participant metadata into string-only dictionaries."""

    if not isinstance(raw_participants, Mapping):
        return {}

    participants: dict[str, dict[str, str]] = {}
    for speaker_code, metadata in raw_participants.items():
        if not isinstance(metadata, Mapping):
            continue
        participants[str(speaker_code)] = {
            str(key).lower(): str(value)
            for key, value in metadata.items()
            if value not in (None, "")
        }
    return participants


def _first_record(value: Any) -> Any:
    """Return the first record from NLTK corpus-reader outputs."""

    if isinstance(value, Mapping):
        return value
    if isinstance(value, (str, bytes, bytearray)):
        return value
    try:
        return value[0]
    except (IndexError, KeyError, TypeError):
        return value


def _identify_child_code(participants: Mapping[str, Mapping[str, str]]) -> str | None:
    """Identify the target child participant code for a transcript."""

    if "CHI" in participants:
        return "CHI"

    for speaker_code, metadata in participants.items():
        role = metadata.get("role", "").lower()
        if role in {"target_child", "child"} or role.endswith("child"):
            return speaker_code
    return None


def _extract_child_age_months(
    participants: Mapping[str, Mapping[str, str]],
    child_code: str,
) -> int | None:
    """Extract the target child's age in whole months from participant metadata."""

    child_metadata = participants.get(child_code, {})
    age_value = child_metadata.get("age")
    if not age_value:
        return None
    return _parse_age_to_months(age_value)


def _parse_age_to_months(age_value: str) -> int | None:
    """Parse CHILDES age metadata into whole months."""

    raw_value = age_value.strip()
    if not raw_value:
        return None

    duration_match = AGE_DURATION_PATTERN.fullmatch(raw_value)
    if duration_match is not None:
        years = int(duration_match.group("years") or 0)
        months = int(duration_match.group("months") or 0)
        days = int(duration_match.group("days") or 0)
        return years * 12 + months + int(days >= 15)

    chat_match = AGE_CHAT_PATTERN.fullmatch(raw_value)
    if chat_match is not None:
        years = int(chat_match.group("years"))
        months = int(chat_match.group("months"))
        days = int(chat_match.group("days") or 0)
        return years * 12 + months + int(days >= 15)

    if raw_value.isdigit():
        return int(raw_value)

    return None


def _select_speakers(
    participants: Mapping[str, Mapping[str, str]],
    child_code: str,
) -> set[str]:
    """Select CHI plus adult speakers likely to be producing child-directed speech."""

    selected = {child_code}
    for speaker_code, metadata in participants.items():
        normalized_code = speaker_code.upper()
        role = metadata.get("role", "").lower()
        if normalized_code in KNOWN_CHILD_DIRECTED_CODES:
            selected.add(speaker_code)
            continue
        if any(keyword in role for keyword in KNOWN_CHILD_DIRECTED_ROLE_KEYWORDS):
            selected.add(speaker_code)
    return selected


def _clean_tokens(raw_tokens: Iterable[str]) -> Iterator[str]:
    """Normalize raw corpus tokens into lowercase lexical items."""

    for token in raw_tokens:
        lower_token = token.lower()
        for cleaned in TOKEN_PATTERN.findall(lower_token):
            yield cleaned


def _default_cache_dir() -> Path:
    """Return the default on-disk cache for downloaded TalkBank archives."""

    xdg_cache_home = Path.home() / ".cache"
    return xdg_cache_home / "childsafe" / "childes"


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Build the CLI argument parser for CHILDES lexicon extraction."""

    parser = argparse.ArgumentParser(
        description=(
            "Extract empirical lexical frequency lists from the CHILDES corpus for "
            "ChildSafe developmental profiles."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Directory where d1_early.json through d4_teen.json will be written.",
    )
    parser.add_argument(
        "--min-frequency",
        type=int,
        default=DEFAULT_MIN_FREQUENCY,
        help="Minimum token count required for a word to be retained.",
    )
    parser.add_argument(
        "--corpus-root",
        type=Path,
        default=None,
        help=(
            "Optional local CHILDES XML root, such as an extracted "
            "data-xml/Eng-USA-MOR directory."
        ),
    )
    parser.add_argument(
        "--nltk-data-dir",
        type=Path,
        default=None,
        help="Optional NLTK data directory for locating or downloading the CHILDES mirror.",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Optional cache directory for TalkBank XML ZIP archives.",
    )
    parser.add_argument(
        "--remote-corpus",
        action="append",
        dest="remote_corpora",
        default=None,
        help=(
            "Explicit Eng-NA corpus identifier to download during TalkBank fallback. "
            "Repeat the flag to add more than one corpus."
        ),
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Disable network downloads and use only a local CHILDES XML corpus.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help="Logging verbosity for extraction progress.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Execute the CHILDES lexicon extraction CLI."""

    arguments = _parse_args(argv or sys.argv[1:])
    logging.basicConfig(
        level=getattr(logging, arguments.log_level),
        format="%(levelname)s %(message)s",
    )

    try:
        summary = build_childes_lexicons(
            output_dir=arguments.output_dir,
            min_frequency=arguments.min_frequency,
            corpus_root=arguments.corpus_root,
            nltk_data_dir=arguments.nltk_data_dir,
            cache_dir=arguments.cache_dir,
            allow_download=not arguments.no_download,
            remote_corpora=arguments.remote_corpora,
        )
    except (RuntimeError, ValueError) as error:
        LOGGER.error("%s", error)
        return 1

    print(
        f"Generated {len(summary.output_paths)} empirical CHILDES lexicons "
        f"from {summary.source} into {arguments.output_dir}"
    )
    print(f"Processed transcripts: {summary.processed_transcripts}")
    print(f"Skipped missing age metadata: {summary.skipped_missing_age}")
    print(f"Skipped outside D1-D4 age bands: {summary.skipped_out_of_band}")
    for profile_key, output_path in summary.output_paths.items():
        print(
            f" - {profile_key}: {summary.vocabulary_sizes[profile_key]} words, "
            f"{summary.token_counts[profile_key]} tokens "
            f"-> {output_path}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
