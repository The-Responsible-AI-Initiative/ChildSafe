"""Runtime belief-state tracking for developmental probe agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class BeliefState:
    """
    Mutable runtime belief state for a simulated developmental probe.

    This state intentionally represents a bounded, configurable approximation
    of epistemic constraints rather than any claim of genuine child cognition.
    """

    known_facts: set[str] = field(default_factory=set)
    attributed_model_knowledge: set[str] = field(default_factory=set)
    attributed_model_intentions: set[str] = field(default_factory=set)
    attributed_model_emotions: set[str] = field(default_factory=set)
    recognizes_possible_harm: bool = False
    recognizes_model_fallibility: bool = False
    recognizes_persuasion: bool = False
    turn_number: int = 0

    def copy(self) -> "BeliefState":
        """Return an isolated copy of the belief state."""

        return BeliefState(
            known_facts=set(self.known_facts),
            attributed_model_knowledge=set(self.attributed_model_knowledge),
            attributed_model_intentions=set(self.attributed_model_intentions),
            attributed_model_emotions=set(self.attributed_model_emotions),
            recognizes_possible_harm=self.recognizes_possible_harm,
            recognizes_model_fallibility=self.recognizes_model_fallibility,
            recognizes_persuasion=self.recognizes_persuasion,
            turn_number=self.turn_number,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic, serializable state snapshot."""

        return {
            "known_facts": sorted(self.known_facts),
            "attributed_model_knowledge": sorted(self.attributed_model_knowledge),
            "attributed_model_intentions": sorted(self.attributed_model_intentions),
            "attributed_model_emotions": sorted(self.attributed_model_emotions),
            "recognizes_possible_harm": self.recognizes_possible_harm,
            "recognizes_model_fallibility": self.recognizes_model_fallibility,
            "recognizes_persuasion": self.recognizes_persuasion,
            "turn_number": self.turn_number,
        }


__all__ = [
    "BeliefState",
]
