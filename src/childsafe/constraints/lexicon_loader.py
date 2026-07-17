"""Utilities for loading CHILDES-derived lexical frequency lists."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_MIN_FREQUENCY = 5
LEXICON_SUBDIR = Path("data") / "childes_lexicon"
PROFILE_BAND_FILES: dict[str, str] = {
    "early": "d1_early.json",
    "d1": "d1_early.json",
    "d1_early": "d1_early.json",
    "mid": "d2_mid.json",
    "d2": "d2_mid.json",
    "d2_mid": "d2_mid.json",
    "late": "d3_late.json",
    "d3": "d3_late.json",
    "d3_late": "d3_late.json",
    "teen": "d4_teen.json",
    "d4": "d4_teen.json",
    "d4_teen": "d4_teen.json",
}


def load_lexicon(profile_band: str) -> list[str]:
    """
    Load the allowed lexicon for a developmental profile band.

    The loader reads the corresponding JSON frequency list and returns only
    words whose frequency meets the configured minimum threshold.

    Args:
        profile_band: Lexical band identifier such as `early`, `mid`, `late`,
            `teen`, or the explicit file stem aliases like `d1_early`.

    Returns:
        A frequency-sorted list of allowed words for the specified profile band.

    Raises:
        FileNotFoundError: If the lexicon directory or requested file is missing.
        KeyError: If `profile_band` does not map to a known lexicon file.
        ValueError: If the file contents are invalid or no words meet the
            minimum frequency threshold.
    """

    normalized_band = profile_band.strip().lower()
    try:
        filename = PROFILE_BAND_FILES[normalized_band]
    except KeyError as exc:
        available = ", ".join(sorted(PROFILE_BAND_FILES))
        raise KeyError(
            f"Unknown profile band '{profile_band}'. Available bands: {available}"
        ) from exc

    lexicon_dir = _resolve_lexicon_dir()
    lexicon_path = lexicon_dir / filename
    if not lexicon_path.exists():
        raise FileNotFoundError(
            f"Lexicon file not found: {lexicon_path}. "
            "Run `python3 scripts/download_childes.py` to build the CHILDES lexicons."
        )

    with lexicon_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        raise ValueError(f"Lexicon payload must be a JSON object: {lexicon_path}")

    min_frequency = _minimum_frequency_threshold()
    filtered_words = [
        word
        for word, frequency in sorted(
            payload.items(),
            key=lambda item: _coerce_frequency(item[1]),
            reverse=True,
        )
        if isinstance(word, str) and _coerce_frequency(frequency) >= min_frequency
    ]

    if not filtered_words:
        raise ValueError(
            f"No lexicon entries met the minimum frequency threshold of {min_frequency} "
            f"for band '{profile_band}'."
        )

    return filtered_words


def _resolve_lexicon_dir() -> Path:
    """Locate the CHILDES lexicon directory from the environment or repo layout."""

    env_dir = os.getenv("CHILDSAFE_LEXICON_DIR")
    candidate_dirs: list[Path] = []

    if env_dir:
        candidate_dirs.append(Path(env_dir).expanduser())

    module_path = Path(__file__).resolve()
    candidate_dirs.extend(parent / LEXICON_SUBDIR for parent in module_path.parents)
    candidate_dirs.append(Path.cwd() / LEXICON_SUBDIR)

    for candidate in candidate_dirs:
        if candidate.exists():
            return candidate

    return candidate_dirs[0]


def _minimum_frequency_threshold() -> int:
    """Read the minimum allowed frequency threshold from the environment."""

    raw_value = os.getenv("CHILDSAFE_LEXICON_MIN_FREQ", str(DEFAULT_MIN_FREQUENCY))
    try:
        threshold = int(raw_value)
    except ValueError as exc:
        raise ValueError("CHILDSAFE_LEXICON_MIN_FREQ must be an integer") from exc
    if threshold < 0:
        raise ValueError("CHILDSAFE_LEXICON_MIN_FREQ must be non-negative")
    return threshold


def _coerce_frequency(value: Any) -> int:
    """Normalize a raw frequency value into an integer."""

    if isinstance(value, bool):
        raise ValueError("Boolean values are not valid frequencies")
    if not isinstance(value, (int, float)):
        raise ValueError(f"Invalid frequency value: {value!r}")
    return int(value)


__all__ = [
    "load_lexicon",
]
