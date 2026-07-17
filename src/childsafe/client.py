"""Client-facing ChildSafe SDK entrypoints.

This module exposes the primary orchestration objects that most SDK users
interact with directly.

Default available dimensions:
- `content_appropriateness`
- `privacy_protection`
- `emotional_safety`
- `boundary_respect`
"""

from childsafe.engine.orchestrator import AuditReport, ParametricProbe

__all__ = [
    "AuditReport",
    "ParametricProbe",
]
