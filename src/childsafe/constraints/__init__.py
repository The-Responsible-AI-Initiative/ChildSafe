"""Runtime developmental constraint profiles for ChildSafe probes."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from childsafe.constraints.lexicon_loader import load_lexicon
from childsafe.constraints.trie import ChildesLogitsProcessor, Trie, TrieNode
from childsafe.profiles.loader import load_profile
from childsafe.profiles.registry import LEGACY_PROFILE_TO_TEMPLATE_ID
from childsafe.profiles.schema import DevelopmentalProfileConfig, TheoryOfMindProfile


class DevelopmentalProfile(str, Enum):
    """Legacy built-in profile identifiers preserved for backward compatibility."""

    D_1 = "D_1"
    D_2 = "D_2"
    D_3 = "D_3"
    D_4 = "D_4"


class DevelopmentalConstraintSettings(BaseModel):
    """
    Legacy compatibility view over the richer developmental profile schema.

    Existing runtime code historically depended on `context_horizon`,
    `topic_volatility`, and `lexical_band`. Those values now derive from the
    structured profile templates while preserving the old access pattern.
    """

    model_config = ConfigDict(frozen=True)

    profile: DevelopmentalProfile | None = None
    name: str
    template_id: str | None = None
    context_horizon: int = Field(ge=0)
    topic_volatility: float = Field(ge=0.0, le=1.0)
    lexical_band: str | None = None
    temperature: float = Field(gt=0.0, le=2.0)
    top_p: float = Field(gt=0.0, le=1.0)
    max_tokens: int = Field(ge=1)
    source: str
    base_template: str | None = None
    modified_fields: tuple[str, ...] = ()
    validation_status: str
    theory_of_mind: TheoryOfMindProfile


def profile_to_constraint_settings(
    profile: DevelopmentalProfileConfig,
) -> DevelopmentalConstraintSettings:
    """Convert a full profile config into the legacy constraint view."""

    legacy_profile = _legacy_profile_from_name(profile.name)
    return DevelopmentalConstraintSettings(
        profile=legacy_profile,
        name=profile.name,
        template_id=profile.template_id,
        context_horizon=profile.memory_horizon,
        topic_volatility=profile.discourse_volatility,
        lexical_band=profile.lexical_profile,
        temperature=profile.temperature,
        top_p=profile.top_p,
        max_tokens=profile.max_tokens,
        source=profile.source,
        base_template=profile.base_template,
        modified_fields=profile.modified_fields,
        validation_status=profile.validation_status,
        theory_of_mind=profile.theory_of_mind,
    )


def _legacy_profile_from_name(profile_name: str) -> DevelopmentalProfile | None:
    """Return the legacy enum member if the profile name matches one."""

    try:
        return DevelopmentalProfile(profile_name)
    except ValueError:
        return None


DEVELOPMENTAL_PROFILES: dict[DevelopmentalProfile, DevelopmentalConstraintSettings] = {
    enum_value: profile_to_constraint_settings(load_profile(template_id))
    for enum_name, template_id in LEGACY_PROFILE_TO_TEMPLATE_ID.items()
    for enum_value in (DevelopmentalProfile(enum_name),)
}


def get_developmental_profile(
    profile: DevelopmentalProfile,
) -> DevelopmentalConstraintSettings:
    """Return immutable constraint settings for a built-in developmental profile."""

    return DEVELOPMENTAL_PROFILES[profile]


__all__ = [
    "ChildesLogitsProcessor",
    "DEVELOPMENTAL_PROFILES",
    "DevelopmentalConstraintSettings",
    "DevelopmentalProfile",
    "DevelopmentalProfileConfig",
    "TheoryOfMindProfile",
    "Trie",
    "TrieNode",
    "get_developmental_profile",
    "load_lexicon",
    "profile_to_constraint_settings",
]
