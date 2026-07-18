"""Tests for profile overrides and nested Theory-of-Mind updates."""

from __future__ import annotations

from childsafe.profiles import load_profile, override_profile


def test_overrides_do_not_mutate_base_template() -> None:
    """Overriding a profile should return a new validated object."""

    base_profile = load_profile("d1_age_6_8")
    overridden_profile = override_profile(base_profile, memory_horizon=3)

    assert base_profile.memory_horizon == 2
    assert overridden_profile.memory_horizon == 3
    assert overridden_profile is not base_profile


def test_nested_theory_of_mind_overrides_work() -> None:
    """Nested Theory-of-Mind overrides should preserve unspecified fields."""

    base_profile = load_profile("d1_age_6_8")
    overridden_profile = override_profile(
        base_profile,
        theory_of_mind={
            "persuasion_recognition": 0.25,
            "model_fallibility_awareness": 0.2,
        },
    )

    assert overridden_profile.theory_of_mind.persuasion_recognition == 0.25
    assert overridden_profile.theory_of_mind.model_fallibility_awareness == 0.2
    assert (
        overridden_profile.theory_of_mind.false_belief_reasoning
        == base_profile.theory_of_mind.false_belief_reasoning
    )


def test_override_metadata_records_changed_fields() -> None:
    """Override metadata should record the base template and changed fields."""

    base_profile = load_profile("d2_age_9_11")
    overridden_profile = override_profile(
        base_profile,
        memory_horizon=5,
        theory_of_mind={"persuasion_recognition": 0.3},
    )

    assert overridden_profile.source == "template_override"
    assert overridden_profile.base_template == "d2_age_9_11"
    assert overridden_profile.modified_fields == (
        "memory_horizon",
        "theory_of_mind.persuasion_recognition",
    )
