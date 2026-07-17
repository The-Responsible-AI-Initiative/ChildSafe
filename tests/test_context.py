"""Tests for bounded-context prompt construction."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

from childsafe.constraints import DevelopmentalProfile
from childsafe.dimensions import AbstractDimension
from childsafe.engine.orchestrator import ParametricProbe
from childsafe.engine.state_machine import DiscourseState


class StaticDimension(AbstractDimension):
    """Minimal dimension used to complete audit calls in tests."""

    @property
    def name(self) -> str:
        return "static_dimension"

    @property
    def description(self) -> str:
        return "Returns a fixed score for context truncation tests."

    async def evaluate_trace(
        self,
        conversation_history: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "score": 0.5,
            "reasoning": f"Observed {len(conversation_history)} turns.",
        }


class StaticStateMachine:
    """Deterministic state machine used to avoid random digressions in tests."""

    def __init__(self) -> None:
        self.state = DiscourseState.CONTEXT_ADHERENCE

    def step(self) -> None:
        self.state = DiscourseState.CONTEXT_ADHERENCE
        return None

    def reset(self) -> None:
        self.state = DiscourseState.CONTEXT_ADHERENCE


@pytest.fixture
def context_probe(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[ParametricProbe, list[list[dict[str, Any]]], list[str]]:
    """Provide a lightweight probe stub that records bounded histories."""

    probe = object.__new__(ParametricProbe)
    probe.model_name_or_path = "dummy-probe"
    probe.profile = DevelopmentalProfile.D_2
    probe.device = "cpu"
    probe.torch_dtype = None
    probe.dimension_registry = None
    probe.profile_settings = SimpleNamespace(context_horizon=3, lexical_band="mid")
    probe.discourse_state_machine = StaticStateMachine()
    probe.seed_prompt = "seed prompt"

    history_snapshots: list[list[dict[str, Any]]] = []
    rendered_prompts: list[str] = []

    async def fake_generate_prompt(
        self: ParametricProbe,
        history: list[dict[str, Any]],
        digression_anchor: str | None,
    ) -> str:
        history_snapshots.append([dict(item) for item in history])
        rendered_prompts.append(self._render_generation_context(history, digression_anchor))
        return f"probe-turn-{len(history_snapshots)}"

    async def fake_call_target(
        self: ParametricProbe,
        target_callable,
        prompt: str,
    ) -> str:
        return str(target_callable(prompt))

    monkeypatch.setattr(ParametricProbe, "_generate_probe_prompt", fake_generate_prompt)
    monkeypatch.setattr(ParametricProbe, "_call_target", fake_call_target)
    return probe, history_snapshots, rendered_prompts


def test_context_horizon_truncates_prompt_history_without_mutating_full_trace(
    context_probe: tuple[ParametricProbe, list[list[dict[str, Any]]], list[str]],
) -> None:
    """Only the last `k` turns should shape the next prompt, while full history remains."""

    probe, history_snapshots, rendered_prompts = context_probe

    def target_callable(prompt: str) -> str:
        return f"target-response-for-{prompt}"

    report = asyncio.run(
        probe.audit(
            target_callable=target_callable,
            turns=10,
            dimension=StaticDimension(),
        )
    )

    assert [len(snapshot) for snapshot in history_snapshots] == [0, 1, 2, 3, 3, 3, 3, 3, 3, 3]
    assert len(report.raw_conversation_trace) == 10
    assert report.raw_conversation_trace[0]["probe_prompt"] == "probe-turn-1"
    assert report.raw_conversation_trace[-1]["probe_prompt"] == "probe-turn-10"

    for turn_index in range(3, 10):
        assert history_snapshots[turn_index] == report.raw_conversation_trace[
            turn_index - 3 : turn_index
        ]

    assert "probe-turn-1" not in rendered_prompts[4]
    assert "probe-turn-2" in rendered_prompts[4]
    assert "probe-turn-3" in rendered_prompts[4]
    assert "probe-turn-4" in rendered_prompts[4]
