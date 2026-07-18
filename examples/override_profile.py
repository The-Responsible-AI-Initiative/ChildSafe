"""Create a template-derived profile override and inspect its metadata."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from childsafe import DevelopmentalAgent, load_profile, override_profile


def main() -> None:
    """Construct an agent from a built-in profile with selected overrides."""

    base_profile = load_profile("d1_age_6_8")
    profile = override_profile(
        base_profile,
        memory_horizon=3,
        theory_of_mind={
            "persuasion_recognition": 0.25,
            "model_fallibility_awareness": 0.2,
        },
    )
    agent = DevelopmentalAgent(
        profile=profile,
        model_name_or_path=os.getenv("CHILDSAFE_PROBE_MODEL", "distilgpt2"),
        device=os.getenv("CHILDSAFE_DEVICE", "cpu"),
        seed=42,
    )

    print("Profile source:", agent.active_profile.source)
    print("Base template:", agent.active_profile.base_template)
    print("Modified fields:", agent.active_profile.modified_fields)
    print("Run metadata:", agent.run_metadata)


if __name__ == "__main__":
    main()
