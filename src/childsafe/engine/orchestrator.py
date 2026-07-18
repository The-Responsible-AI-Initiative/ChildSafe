"""Asynchronous orchestration loop for parametric ChildSafe probes."""

from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass, field
from typing import Any, Awaitable, Protocol, cast

from childsafe.agents.developmental_agent import DevelopmentalAgent
from childsafe.dimensions import (
    DEFAULT_DIMENSION_REGISTRY,
    AbstractDimension,
    DimensionRegistry,
)


class TargetCallable(Protocol):
    """Protocol for the audited system under test."""

    def __call__(self, prompt: str) -> str | Any:
        """Return or await a target-model response for the supplied prompt."""


@dataclass(slots=True)
class AuditReport:
    """
    Structured result for a completed ChildSafe audit run.

    Attributes:
        target_model_name: Human-readable identifier for the system under test.
        profile: Resolved profile name used by the probe.
        dimension: Name of the evaluated safety dimension.
        score: Final dimension score in the range `[0.0, 1.0]`.
        reasoning: Judge or heuristic explanation for the score.
        raw_conversation_trace: Full ordered exchange trace.
        run_metadata: Reproducibility metadata for the probe run.
    """

    target_model_name: str
    profile: str
    dimension: str
    score: float
    reasoning: str
    raw_conversation_trace: list[dict[str, Any]]
    run_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ParametricProbe(DevelopmentalAgent):
    """
    Async audit orchestrator layered on the reusable `DevelopmentalAgent`.

    The probe uses profile-driven memory, discourse, lexical masking, and
    optional Theory-of-Mind belief-state updates to generate the user-side
    prompts sent to the target system under test.
    """

    dimension_registry: DimensionRegistry = field(
        default_factory=lambda: DEFAULT_DIMENSION_REGISTRY
    )

    async def audit(
        self,
        target_callable: TargetCallable,
        turns: int,
        dimension: str | AbstractDimension,
    ) -> AuditReport:
        """
        Run a multi-turn audit against a target system under test.

        Args:
            target_callable: Sync or async callable representing the audited model.
            turns: Number of audit turns to execute.
            dimension: Registered dimension name or a concrete dimension
                instance supplied by the SDK user.
        """

        resolved_dimension = self._resolve_dimension(dimension)
        target_model_name = self._get_target_model_name(target_callable)
        self.reset()

        for _ in range(turns):
            prompt = self.respond()
            response = await self._call_target(target_callable, prompt)
            self.observe_target_response(response)
            if self.conversation_history:
                self.conversation_history[-1]["target_model_name"] = target_model_name

        dimension_result = await resolved_dimension.evaluate_trace(
            self.conversation_history
        )
        score = float(dimension_result["score"])
        reasoning = str(dimension_result["reasoning"])

        return AuditReport(
            target_model_name=target_model_name,
            profile=self.active_profile.name,
            dimension=resolved_dimension.name,
            score=score,
            reasoning=reasoning,
            raw_conversation_trace=[
                dict(exchange) for exchange in self.conversation_history
            ],
            run_metadata=self.run_metadata,
        )

    async def _call_target(
        self,
        target_callable: TargetCallable,
        prompt: str,
    ) -> str:
        """Call the system under test, supporting both sync and async callables."""

        call_method = getattr(target_callable, "__call__", None)
        if inspect.iscoroutinefunction(target_callable) or inspect.iscoroutinefunction(
            call_method
        ):
            resolved = await cast(Awaitable[Any], target_callable(prompt))
        else:
            resolved = await asyncio.to_thread(target_callable, prompt)
        return str(resolved)

    def _resolve_dimension(
        self,
        dimension: str | AbstractDimension,
    ) -> AbstractDimension:
        """Resolve a user-supplied dimension reference into an instance."""

        if isinstance(dimension, str):
            try:
                return self.dimension_registry.get(dimension)
            except KeyError as exc:
                available = ", ".join(self.dimension_registry.names()) or "<none>"
                raise ValueError(
                    f"Unknown dimension '{dimension}'. Available dimensions: {available}"
                ) from exc
        if isinstance(dimension, AbstractDimension):
            return dimension
        raise TypeError(
            "dimension must be a registered name or an AbstractDimension instance"
        )

    @staticmethod
    def _get_target_model_name(target_callable: TargetCallable) -> str:
        """Best-effort extraction of a user-facing target model name."""

        model_name = getattr(target_callable, "model_name", None)
        if isinstance(model_name, str) and model_name.strip():
            return model_name
        return target_callable.__class__.__name__


__all__ = [
    "AuditReport",
    "ParametricProbe",
]
