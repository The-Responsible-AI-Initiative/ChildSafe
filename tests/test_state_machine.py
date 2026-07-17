"""Tests for the discourse volatility state machine."""

from __future__ import annotations

import pytest

from childsafe.engine.state_machine import DiscourseState, DiscourseStateMachine


@pytest.fixture
def high_tau_state_machine() -> DiscourseStateMachine:
    """Provide a seeded high-volatility state machine."""

    return DiscourseStateMachine.from_topics(
        tau_i=0.9,
        semantic_cache=["dinosaurs", "rockets", "music"],
        seed=2026,
    )


def test_state_machine_digresses_at_high_tau(
    high_tau_state_machine: DiscourseStateMachine,
) -> None:
    """A high `tau_i` should trigger digressions on roughly 90% of turns."""

    digression_count = 0
    anchor_count = 0

    for _ in range(100):
        anchor = high_tau_state_machine.step()
        if anchor is None:
            assert high_tau_state_machine.state == DiscourseState.CONTEXT_ADHERENCE
            continue

        digression_count += 1
        anchor_count += 1
        assert high_tau_state_machine.state == DiscourseState.DIGRESSION
        assert isinstance(anchor, str)
        assert anchor.endswith("?")

    assert digression_count == pytest.approx(90, abs=10)
    assert anchor_count == digression_count
