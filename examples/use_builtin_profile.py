"""Initialize a developmental agent from a built-in profile template."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from childsafe import DevelopmentalAgent, load_profile


def main() -> None:
    """Construct an agent from the standardized D_1 built-in profile."""

    profile = load_profile("d1_age_6_8")
    agent = DevelopmentalAgent(
        profile=profile,
        model_name_or_path=os.getenv("CHILDSAFE_PROBE_MODEL", "distilgpt2"),
        device=os.getenv("CHILDSAFE_DEVICE", "cpu"),
        seed=42,
    )

    prompt = agent.respond()
    print("Profile:", agent.active_profile.name)
    print("Prompt:", prompt)
    print("Run metadata:", agent.run_metadata)


if __name__ == "__main__":
    main()
