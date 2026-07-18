"""Client-facing ChildSafe SDK entrypoints.

This module exposes the primary runtime objects most SDK users interact with.

Default available dimensions:
- `content_appropriateness`
- `privacy_protection`
- `emotional_safety`
- `boundary_respect`

Built-in developmental profiles can be loaded with
`childsafe.profiles.load_profile(...)` and then passed into
`DevelopmentalAgent` or `ParametricProbe`.
"""

from childsafe.agents import DevelopmentalAgent
from childsafe.engine.orchestrator import AuditReport, ParametricProbe
from childsafe.profiles import DevelopmentalProfileConfig, TheoryOfMindProfile

__all__ = [
    "AuditReport",
    "DevelopmentalAgent",
    "DevelopmentalProfileConfig",
    "ParametricProbe",
    "TheoryOfMindProfile",
]
