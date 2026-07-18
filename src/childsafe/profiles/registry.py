"""Registry metadata for built-in ChildSafe developmental profiles."""

from __future__ import annotations

from pathlib import PurePosixPath

BUILT_IN_PROFILE_IDS: tuple[str, ...] = (
    "d1_age_6_8",
    "d2_age_9_11",
    "d3_age_12_14",
    "d4_age_15_17",
)

LEGACY_PROFILE_TO_TEMPLATE_ID: dict[str, str] = {
    "D_1": "d1_age_6_8",
    "D_2": "d2_age_9_11",
    "D_3": "d3_age_12_14",
    "D_4": "d4_age_15_17",
}

TEMPLATE_DIRECTORY = PurePosixPath("templates")


def is_builtin_profile_id(profile_id: str) -> bool:
    """Return whether the supplied identifier is a registered built-in profile."""

    return profile_id in BUILT_IN_PROFILE_IDS


__all__ = [
    "BUILT_IN_PROFILE_IDS",
    "LEGACY_PROFILE_TO_TEMPLATE_ID",
    "TEMPLATE_DIRECTORY",
    "is_builtin_profile_id",
]
