"""Tests for developmental profile loading, validation, and serialization."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from childsafe.profiles import (
    DevelopmentalProfileConfig,
    TheoryOfMindProfile,
    list_builtin_profiles,
    load_profile,
)


def test_builtin_profiles_load_successfully() -> None:
    """All registered built-in profiles should load with stable metadata."""

    profile_ids = list_builtin_profiles()
    assert profile_ids

    for profile_id in profile_ids:
        profile = load_profile(profile_id)
        assert profile.template_id == profile_id
        assert profile.source == "built_in"
        assert profile.validation_status == "developmentally_motivated"


def test_invalid_probability_is_rejected() -> None:
    """Probability-like Theory-of-Mind values must stay within `[0, 1]`."""

    with pytest.raises(ValidationError):
        TheoryOfMindProfile(
            recursive_depth=1,
            false_belief_reasoning=1.1,
            knowledge_access_tracking=0.5,
            benevolent_intent_prior=0.5,
            model_fallibility_awareness=0.5,
            persuasion_recognition=0.5,
            anthropomorphic_attribution=0.5,
        )


def test_invalid_recursive_depth_is_rejected() -> None:
    """Recursive depth must be a non-negative integer."""

    with pytest.raises(ValidationError):
        TheoryOfMindProfile(
            recursive_depth=-1,
            false_belief_reasoning=0.5,
            knowledge_access_tracking=0.5,
            benevolent_intent_prior=0.5,
            model_fallibility_awareness=0.5,
            persuasion_recognition=0.5,
            anthropomorphic_attribution=0.5,
        )


def test_invalid_memory_horizon_is_rejected(
    custom_profile: DevelopmentalProfileConfig,
) -> None:
    """Memory horizon must be non-negative."""

    with pytest.raises(ValidationError):
        DevelopmentalProfileConfig.model_validate(
            {
                **custom_profile.to_dict(),
                "memory_horizon": -1,
            }
        )


def test_custom_profiles_can_roundtrip_and_serialize_deterministically(
    custom_profile: DevelopmentalProfileConfig,
    tmp_path: Path,
) -> None:
    """Custom profiles should export/load cleanly with deterministic output."""

    json_path = tmp_path / "custom_profile.json"
    yaml_path = tmp_path / "custom_profile.yaml"

    custom_profile.export(json_path)
    custom_profile.export(yaml_path)

    roundtrip_json = DevelopmentalProfileConfig.load(json_path)
    roundtrip_yaml = DevelopmentalProfileConfig.load(yaml_path)
    assert roundtrip_json == custom_profile
    assert roundtrip_yaml == custom_profile

    first_json = json_path.read_text(encoding="utf-8")
    custom_profile.export(json_path)
    second_json = json_path.read_text(encoding="utf-8")
    assert first_json == second_json
