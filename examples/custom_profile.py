"""Build a fully custom developmental profile and instantiate an agent."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from childsafe import (
    DevelopmentalAgent,
    DevelopmentalProfileConfig,
    TheoryOfMindProfile,
)


def main() -> None:
    """Construct an agent from a fully custom user-defined profile."""

    profile = DevelopmentalProfileConfig(
        name="high_trust_user",
        version="1.0",
        age_range=None,
        memory_horizon=3,
        discourse_volatility=0.3,
        temperature=0.8,
        top_p=0.9,
        max_tokens=32,
        lexical_profile=None,
        persona_prompt=None,
        theory_of_mind=TheoryOfMindProfile(
            recursive_depth=1,
            false_belief_reasoning=0.4,
            knowledge_access_tracking=0.35,
            benevolent_intent_prior=0.9,
            model_fallibility_awareness=0.1,
            persuasion_recognition=0.15,
            anthropomorphic_attribution=0.85,
        ),
        source="custom",
        base_template=None,
        validation_status="user_defined",
    )
    agent = DevelopmentalAgent(
        profile=profile,
        model_name_or_path=os.getenv("CHILDSAFE_PROBE_MODEL", "distilgpt2"),
        device=os.getenv("CHILDSAFE_DEVICE", "cpu"),
        seed=42,
    )

    print("Profile:", agent.active_profile.name)
    print("Profile source:", agent.active_profile.source)
    print("Prompt:", agent.respond())


if __name__ == "__main__":
    main()
