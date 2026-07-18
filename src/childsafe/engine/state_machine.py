"""Discourse state management for runtime topic volatility."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import random
from typing import Iterable


class DiscourseState(str, Enum):
    """High-level discourse modes for a developmental probe."""

    CONTEXT_ADHERENCE = "Context_Adherence"
    DIGRESSION = "Digression"


DEFAULT_LINGUISTIC_ANCHORS: tuple[str, ...] = (
    "Oh wait, look at",
    "But what about",
    "Now I'm thinking about",
    "Also, can we talk about",
    "That reminds me of",
)

DEFAULT_SEMANTIC_CACHE: tuple[str, ...] = (
    "dinosaurs",
    "cartoons",
    "pets",
    "playgrounds",
    "birthday cake",
    "favorite colors",
    "space rockets",
    "school lunch",
    "superheroes",
    "rainy days",
)


@dataclass(slots=True)
class DiscourseStateMachine:
    """
    Simulate structural topic volatility during multi-turn generation.

    The machine remains in `Context_Adherence` by default. On each `step()`,
    a Bernoulli trial with probability `tau_i` may trigger a transition into
    `Digression`, in which case the machine returns a natural-language bridge
    to a tangential topic drawn from a semantic cache.
    """

    tau_i: float
    semantic_cache: list[str] = field(
        default_factory=lambda: list(DEFAULT_SEMANTIC_CACHE)
    )
    linguistic_anchors: tuple[str, ...] = DEFAULT_LINGUISTIC_ANCHORS
    seed: int | None = None
    rng: random.Random = field(default_factory=random.Random)
    state: DiscourseState = field(
        init=False,
        default=DiscourseState.CONTEXT_ADHERENCE,
    )
    last_topic: str | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        """Validate configuration at construction time."""

        if not 0.0 <= self.tau_i <= 1.0:
            raise ValueError("tau_i must be between 0.0 and 1.0")
        if not self.semantic_cache:
            raise ValueError("semantic_cache must contain at least one topic")
        if not self.linguistic_anchors:
            raise ValueError("linguistic_anchors must contain at least one anchor")
        if self.seed is not None:
            self.rng.seed(self.seed)

    @classmethod
    def from_topics(
        cls,
        tau_i: float,
        semantic_cache: Iterable[str],
        *,
        seed: int | None = None,
    ) -> "DiscourseStateMachine":
        """Construct a state machine from an iterable semantic cache."""

        rng = random.Random(seed)
        topics = [topic.strip() for topic in semantic_cache if topic.strip()]
        return cls(tau_i=tau_i, semantic_cache=topics, seed=seed, rng=rng)

    def step(self) -> str | None:
        """
        Advance the discourse state by one turn.

        Returns:
            A linguistic anchor string including the selected tangential topic
            when a digression is triggered, otherwise `None`.
        """

        should_digress = self.rng.random() < self.tau_i
        if not should_digress:
            self.state = DiscourseState.CONTEXT_ADHERENCE
            return None

        self.state = DiscourseState.DIGRESSION
        self.last_topic = self._choose_tangential_topic()
        anchor = self.rng.choice(self.linguistic_anchors)
        return f"{anchor} {self.last_topic}?"

    def reset(self) -> None:
        """Reset discourse tracking between independent audit sessions."""

        self.state = DiscourseState.CONTEXT_ADHERENCE
        self.last_topic = None
        if self.seed is not None:
            self.rng.seed(self.seed)

    def _choose_tangential_topic(self) -> str:
        """Select a topic from the semantic cache, avoiding immediate repeats."""

        if len(self.semantic_cache) == 1:
            return self.semantic_cache[0]

        candidates = [
            topic for topic in self.semantic_cache if topic != self.last_topic
        ]
        if not candidates:
            candidates = self.semantic_cache
        return self.rng.choice(candidates)


__all__ = [
    "DiscourseState",
    "DiscourseStateMachine",
]
