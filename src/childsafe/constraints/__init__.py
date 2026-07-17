"""Runtime developmental constraint profiles for ChildSafe probes."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from childsafe.constraints.trie import ChildesLogitsProcessor, Trie, TrieNode


class DevelopmentalProfile(str, Enum):
    """Canonical runtime probe profiles ordered by increasing capability."""

    D_1 = "D_1"
    D_2 = "D_2"
    D_3 = "D_3"
    D_4 = "D_4"


class DevelopmentalConstraintSettings(BaseModel):
    """
    Generative constraints for a parametric developmental probe.

    `context_horizon` approximates a finite working-memory window over the last
    `k` turns, `topic_volatility` controls the probability of a topic transition,
    and `lexical_band` selects the target CHILDES-derived vocabulary band.
    """

    model_config = ConfigDict(frozen=True)

    profile: DevelopmentalProfile
    context_horizon: int = Field(gt=0)
    topic_volatility: float = Field(ge=0.0, le=1.0)
    lexical_band: str


DEVELOPMENTAL_PROFILES: dict[DevelopmentalProfile, DevelopmentalConstraintSettings] = {
    DevelopmentalProfile.D_1: DevelopmentalConstraintSettings(
        profile=DevelopmentalProfile.D_1,
        context_horizon=2,
        topic_volatility=0.80,
        lexical_band="early",
    ),
    DevelopmentalProfile.D_2: DevelopmentalConstraintSettings(
        profile=DevelopmentalProfile.D_2,
        context_horizon=4,
        topic_volatility=0.55,
        lexical_band="mid",
    ),
    DevelopmentalProfile.D_3: DevelopmentalConstraintSettings(
        profile=DevelopmentalProfile.D_3,
        context_horizon=6,
        topic_volatility=0.30,
        lexical_band="late",
    ),
    DevelopmentalProfile.D_4: DevelopmentalConstraintSettings(
        profile=DevelopmentalProfile.D_4,
        context_horizon=8,
        topic_volatility=0.15,
        lexical_band="teen",
    ),
}


def get_developmental_profile(
    profile: DevelopmentalProfile,
) -> DevelopmentalConstraintSettings:
    """Return immutable constraint settings for a developmental probe profile."""

    return DEVELOPMENTAL_PROFILES[profile]


__all__ = [
    "ChildesLogitsProcessor",
    "DEVELOPMENTAL_PROFILES",
    "DevelopmentalConstraintSettings",
    "DevelopmentalProfile",
    "Trie",
    "TrieNode",
    "get_developmental_profile",
]
