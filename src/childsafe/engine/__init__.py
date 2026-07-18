"""Runtime orchestration components for ChildSafe probes."""

from __future__ import annotations

from typing import Any

__all__ = [
    "AuditReport",
    "DiscourseState",
    "DiscourseStateMachine",
    "ParametricProbe",
]


def __getattr__(name: str) -> Any:
    """Lazily resolve engine exports to avoid circular import initialization."""

    if name in {"DiscourseState", "DiscourseStateMachine"}:
        from childsafe.engine.state_machine import DiscourseState, DiscourseStateMachine

        return {
            "DiscourseState": DiscourseState,
            "DiscourseStateMachine": DiscourseStateMachine,
        }[name]
    if name in {"AuditReport", "ParametricProbe"}:
        from childsafe.engine.orchestrator import AuditReport, ParametricProbe

        return {
            "AuditReport": AuditReport,
            "ParametricProbe": ParametricProbe,
        }[name]
    raise AttributeError(f"module 'childsafe.engine' has no attribute {name!r}")
