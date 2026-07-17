"""Abstract interfaces and registry primitives for ChildSafe dimensions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AbstractEvaluator(ABC):
    """
    Base interface for turn-level evaluators in the ChildSafe SDK.

    Implementations are intended to be injected into a runtime testing loop and
    accumulate state across turns before emitting an aggregate score.
    """

    @property
    def name(self) -> str:
        """Return a stable evaluator name for reporting and registration."""

        return self.__class__.__name__

    @abstractmethod
    async def evaluate_turn(self, prompt: str, response: str) -> dict[str, Any]:
        """
        Evaluate a single interaction turn and update internal evaluator state.

        Args:
            prompt: Probe-side text shown to the target model.
            response: Target model output for the current turn.

        Returns:
            A serializable per-turn assessment payload.
        """

    @abstractmethod
    def aggregate_score(self) -> dict[str, Any]:
        """
        Compute an aggregate evaluator result over all observed turns.

        Returns:
            A serializable aggregate assessment payload.
        """


class AbstractDimension(ABC):
    """
    Base interface for full-trace safety dimensions in the ChildSafe SDK.

    A dimension consumes the complete conversation history and produces a
    score plus explanatory reasoning. Implementations are intended to be
    registered and instantiated dynamically through `DimensionRegistry`.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the stable string identifier for this dimension.

        This identifier is used as the lookup key within the registry.
        """

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Return a brief human-readable description of the dimension.

        The description should explain what behavior the dimension evaluates.
        """

    @abstractmethod
    async def evaluate_trace(
        self,
        conversation_history: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Evaluate an entire multi-turn exchange.

        Args:
            conversation_history: Ordered conversation records for the full
                exchange under evaluation.

        Returns:
            A serializable mapping containing, at minimum, a numeric `score`
            and textual `reasoning`.
        """


class DimensionRegistry:
    """
    Factory-style registry for ChildSafe safety dimensions.

    The registry stores dimension classes keyed by their string identifiers and
    returns fresh instances on lookup. This allows SDK users to register custom
    dimensions without changing the orchestration code.
    """

    def __init__(self) -> None:
        """Initialize an empty dimension registry."""

        self._registry: dict[str, type[AbstractDimension]] = {}

    def register(self, dimension_cls: type[AbstractDimension]) -> None:
        """
        Register a dimension class by its declared `name`.

        Args:
            dimension_cls: Concrete `AbstractDimension` subclass to register.

        Raises:
            ValueError: If the dimension name is empty or already registered.
        """

        dimension = dimension_cls()
        name = dimension.name.strip()
        if not name:
            raise ValueError("dimension name must not be empty")
        if name in self._registry:
            raise ValueError(f"dimension '{name}' is already registered")
        self._registry[name] = dimension_cls

    def get(self, dimension_name: str) -> AbstractDimension:
        """
        Instantiate a registered dimension by string identifier.

        Args:
            dimension_name: Registered dimension name.

        Returns:
            A new instance of the requested dimension.

        Raises:
            KeyError: If no dimension exists for `dimension_name`.
        """

        try:
            dimension_cls = self._registry[dimension_name]
        except KeyError as exc:
            raise KeyError(f"unknown dimension '{dimension_name}'") from exc
        return dimension_cls()

    def names(self) -> tuple[str, ...]:
        """Return the registered dimension identifiers in insertion order."""

        return tuple(self._registry.keys())
