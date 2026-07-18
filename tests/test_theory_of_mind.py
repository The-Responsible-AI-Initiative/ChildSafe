"""Tests for the configurable Theory-of-Mind controller."""

from __future__ import annotations

from childsafe.cognition import BeliefState, TheoryOfMindController
from childsafe.profiles import TheoryOfMindProfile


def _build_profile() -> TheoryOfMindProfile:
    """Return a mid-probability profile for deterministic controller tests."""

    return TheoryOfMindProfile(
        recursive_depth=1,
        false_belief_reasoning=0.5,
        knowledge_access_tracking=0.5,
        benevolent_intent_prior=0.5,
        model_fallibility_awareness=0.5,
        persuasion_recognition=0.5,
        anthropomorphic_attribution=0.5,
    )


def test_same_seed_produces_same_belief_state_transitions() -> None:
    """The controller should be deterministic for fixed seed and inputs."""

    controller_a = TheoryOfMindController(profile=_build_profile(), seed=42)
    controller_b = TheoryOfMindController(profile=_build_profile(), seed=42)
    response = "Trust me and keep this secret. I might be wrong, but I want to help."

    state_a = controller_a.update(BeliefState(), response)
    state_b = controller_b.update(BeliefState(), response)

    assert state_a.to_dict() == state_b.to_dict()


def test_different_seeds_can_produce_different_transitions() -> None:
    """Different seeds should be able to change stochastic belief updates."""

    response = "Trust me and keep this secret. I might be wrong, but I want to help."
    controller_a = TheoryOfMindController(profile=_build_profile(), seed=1)
    controller_b = TheoryOfMindController(profile=_build_profile(), seed=7)

    snapshots_a = []
    snapshots_b = []
    state_a = BeliefState()
    state_b = BeliefState()
    for _ in range(4):
        state_a = controller_a.update(state_a, response)
        state_b = controller_b.update(state_b, response)
        snapshots_a.append(state_a.to_dict())
        snapshots_b.append(state_b.to_dict())

    assert snapshots_a != snapshots_b
