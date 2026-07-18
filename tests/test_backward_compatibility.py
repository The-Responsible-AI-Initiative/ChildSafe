"""Tests for backward-compatible wrappers and runtime metadata."""

from __future__ import annotations

import asyncio
from typing import Any

from childsafe.agents import (
    Age12to14Agent,
    Age15to17Agent,
    Age6to8Agent,
    Age9to11Agent,
    DevelopmentalAgent,
)
from childsafe.cognition import BeliefState, ToMPolicy
from childsafe.dimensions import AbstractDimension
from childsafe.engine import ParametricProbe


class StaticDimension(AbstractDimension):
    """Minimal dimension used to complete audit calls in tests."""

    @property
    def name(self) -> str:
        return "static_dimension"

    @property
    def description(self) -> str:
        return "Returns a fixed score for runtime metadata tests."

    async def evaluate_trace(
        self,
        conversation_history: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "score": 0.5,
            "reasoning": f"Observed {len(conversation_history)} turns.",
        }


class EchoToMPolicy:
    """Deterministic custom ToM policy used to verify dependency injection."""

    def update(
        self,
        prior_state: BeliefState,
        assistant_response: str,
        *,
        world_state=None,
    ) -> BeliefState:
        del assistant_response, world_state
        new_state = prior_state.copy()
        new_state.turn_number += 1
        new_state.known_facts.add("custom-policy")
        return new_state

    def render_generation_context(self, belief_state: BeliefState) -> str:
        return f"Custom policy facts: {sorted(belief_state.known_facts)}"


def test_age_specific_agents_instantiate_expected_built_in_profiles(
    dummy_model_assets,
) -> None:
    """Backward-compatible age wrappers should resolve the expected templates."""

    tokenizer, model = dummy_model_assets
    wrappers = [
        Age6to8Agent(model=model, tokenizer=tokenizer),
        Age9to11Agent(model=model, tokenizer=tokenizer),
        Age12to14Agent(model=model, tokenizer=tokenizer),
        Age15to17Agent(model=model, tokenizer=tokenizer),
    ]

    assert [agent.active_profile.template_id for agent in wrappers] == [
        "d1_age_6_8",
        "d2_age_9_11",
        "d3_age_12_14",
        "d4_age_15_17",
    ]


def test_custom_theory_of_mind_policy_can_be_injected(
    custom_profile,
    dummy_model_assets,
) -> None:
    """Developers should be able to inject a custom ToM policy."""

    tokenizer, model = dummy_model_assets
    agent = DevelopmentalAgent(
        profile=custom_profile,
        model=model,
        tokenizer=tokenizer,
        tom_policy=EchoToMPolicy(),
    )

    prompt = agent.respond()
    agent.observe_target_response("Any response.")

    assert isinstance(prompt, str)
    assert "custom-policy" in agent.belief_state.known_facts


def test_profile_metadata_is_included_in_run_outputs(
    custom_profile,
    dummy_model_assets,
) -> None:
    """Audit reports should include structured profile metadata."""

    tokenizer, model = dummy_model_assets
    probe = ParametricProbe(
        profile=custom_profile,
        model=model,
        tokenizer=tokenizer,
        seed=99,
    )

    def target_callable(prompt: str) -> str:
        return f"target:{prompt}"

    report = asyncio.run(
        probe.audit(
            target_callable=target_callable,
            turns=2,
            dimension=StaticDimension(),
        )
    )

    assert report.run_metadata["profile_name"] == custom_profile.name
    assert report.run_metadata["profile_source"] == custom_profile.source
    assert report.run_metadata["random_seed"] == 99
    assert report.run_metadata["theory_of_mind"]["recursive_depth"] == 1
