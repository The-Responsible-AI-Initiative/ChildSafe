"""Tests for agent-local belief state and isolated runtime history."""

from __future__ import annotations

from childsafe.agents import DevelopmentalAgent


def test_belief_state_is_not_shared_between_agent_instances(
    custom_profile,
    dummy_model_assets,
) -> None:
    """Each agent instance should maintain its own belief state."""

    tokenizer, model = dummy_model_assets
    agent_a = DevelopmentalAgent(
        profile=custom_profile,
        model=model,
        tokenizer=tokenizer,
        seed=11,
    )
    agent_b = DevelopmentalAgent(
        profile=custom_profile,
        model=model,
        tokenizer=tokenizer,
        seed=11,
    )

    agent_a.respond()
    agent_a.observe_target_response("Trust me and keep this secret.")

    assert agent_a.belief_state.turn_number == 1
    assert agent_b.belief_state.turn_number == 0
    assert agent_b.belief_state.to_dict()["known_facts"] == []


def test_conversation_history_is_not_shared_between_agent_instances(
    custom_profile,
    dummy_model_assets,
) -> None:
    """Conversation history should be isolated per agent instance."""

    tokenizer, model = dummy_model_assets
    agent_a = DevelopmentalAgent(
        profile=custom_profile,
        model=model,
        tokenizer=tokenizer,
        seed=12,
    )
    agent_b = DevelopmentalAgent(
        profile=custom_profile,
        model=model,
        tokenizer=tokenizer,
        seed=12,
    )

    agent_a.respond()
    assert len(agent_a.conversation_history) == 1
    assert agent_b.conversation_history == []
