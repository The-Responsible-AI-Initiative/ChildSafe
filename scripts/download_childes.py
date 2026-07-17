"""Generate mock CHILDES-derived frequency lists for ChildSafe profiles."""

from __future__ import annotations

import json
from pathlib import Path

TARGET_VOCABULARY_SIZE = 1000
ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "data" / "childes_lexicon"

PROFILE_SEED_WORDS: dict[str, tuple[str, ...]] = {
    "d1_early": (
        "mom",
        "dad",
        "baby",
        "ball",
        "toy",
        "dog",
        "cat",
        "book",
        "milk",
        "cookie",
        "play",
        "run",
        "jump",
        "hug",
        "happy",
        "sad",
        "red",
        "blue",
        "sun",
        "moon",
        "bed",
        "bath",
        "home",
        "friend",
        "hello",
    ),
    "d2_mid": (
        "school",
        "teacher",
        "pencil",
        "friend",
        "soccer",
        "music",
        "pizza",
        "family",
        "story",
        "question",
        "answer",
        "secret",
        "outside",
        "inside",
        "share",
        "learn",
        "worry",
        "sorry",
        "favorite",
        "birthday",
        "backpack",
        "lunch",
        "science",
        "reading",
        "please",
    ),
    "d3_late": (
        "actually",
        "probably",
        "online",
        "private",
        "boundary",
        "problem",
        "decision",
        "explain",
        "support",
        "advice",
        "different",
        "remember",
        "discussion",
        "feeling",
        "situation",
        "pressure",
        "honest",
        "trust",
        "curious",
        "anxious",
        "identity",
        "future",
        "internet",
        "question",
        "change",
    ),
    "d4_teen": (
        "identity",
        "relationship",
        "privacy",
        "pressure",
        "seriously",
        "honestly",
        "complicated",
        "frustrated",
        "independent",
        "awkward",
        "responsible",
        "consequence",
        "argument",
        "context",
        "emotion",
        "future",
        "schoolwork",
        "internet",
        "conversation",
        "boundary",
        "choice",
        "social",
        "adults",
        "comfort",
        "unsafe",
    ),
}


def generate_mock_childes_lexicons(
    output_dir: Path = OUTPUT_DIR,
    target_size: int = TARGET_VOCABULARY_SIZE,
) -> list[Path]:
    """
    Generate deterministic placeholder CHILDES frequency lists.

    Args:
        output_dir: Directory where the JSON files should be written.
        target_size: Number of unique words to include per profile band.

    Returns:
        The list of generated JSON file paths.
    """

    output_dir.mkdir(parents=True, exist_ok=True)
    generated_paths: list[Path] = []

    for filename_stem, seed_words in PROFILE_SEED_WORDS.items():
        frequency_map = _build_frequency_map(
            seed_words=seed_words,
            band_label=filename_stem,
            target_size=target_size,
        )
        output_path = output_dir / f"{filename_stem}.json"
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(frequency_map, handle, indent=2, ensure_ascii=False, sort_keys=True)
        generated_paths.append(output_path)

    return generated_paths


def _build_frequency_map(
    seed_words: tuple[str, ...],
    band_label: str,
    target_size: int,
) -> dict[str, int]:
    """Build a deterministic placeholder vocabulary-to-frequency mapping."""

    if target_size <= 0:
        raise ValueError("target_size must be positive")

    words: list[str] = []
    seen: set[str] = set()

    for word in seed_words:
        normalized = _normalize_word(word)
        if normalized not in seen:
            words.append(normalized)
            seen.add(normalized)

    filler_index = 1
    while len(words) < target_size:
        seed_word = _normalize_word(seed_words[(filler_index - 1) % len(seed_words)])
        candidate = f"{band_label}_{seed_word}_{filler_index:04d}"
        if candidate not in seen:
            words.append(candidate)
            seen.add(candidate)
        filler_index += 1

    return {
        word: target_size - index
        for index, word in enumerate(words)
    }


def _normalize_word(word: str) -> str:
    """Normalize a placeholder vocabulary item into a file-safe token."""

    return word.strip().lower().replace(" ", "_").replace("-", "_")


def main() -> None:
    """Generate the mock CHILDES lexicon files and print a short summary."""

    generated_paths = generate_mock_childes_lexicons()
    print(f"Generated {len(generated_paths)} CHILDES mock lexicons in {OUTPUT_DIR}")
    for path in generated_paths:
        print(f" - {path.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    main()
