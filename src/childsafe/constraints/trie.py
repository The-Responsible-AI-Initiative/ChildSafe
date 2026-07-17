"""Trie-backed lexical masking for CHILDES-constrained generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from string import punctuation
from typing import Iterable, Sequence

import torch
from torch import Tensor
from transformers import LogitsProcessor, PreTrainedTokenizer

WORD_START_MARKERS: tuple[str, ...] = ("Ġ", "▁")
DEFAULT_SMOOTHING_TOKENS: tuple[str, ...] = (
    "the",
    "a",
    "and",
    "to",
    "of",
    "in",
    "i",
    "you",
    "it",
    "is",
    "that",
    "we",
    "he",
    "she",
    "they",
    "this",
    "my",
    "me",
    "your",
    "our",
    "for",
    "on",
    "with",
    "at",
    "from",
    "by",
    "as",
    "be",
    "are",
    "was",
    "were",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "can",
    "could",
    "will",
    "would",
    "should",
    "may",
    "might",
    "one",
    "two",
    "three",
    "good",
    "bad",
    "big",
    "small",
    "little",
    "more",
    "most",
    "some",
    "any",
    "all",
    "not",
    "no",
    "yes",
    "hello",
    "hi",
    "what",
    "why",
    "how",
    "when",
    "where",
    "who",
    "which",
    "if",
    "then",
    "because",
    "but",
    "or",
    "so",
    "like",
    "just",
    "really",
    "very",
    "think",
    "know",
    "want",
    "need",
    "feel",
    "say",
    "said",
    "go",
    "went",
    "come",
    "came",
    "look",
    "see",
    "tell",
    "help",
    "play",
    "make",
    "made",
    "get",
    "got",
    "time",
    "day",
    "thing",
)


@dataclass(slots=True)
class TrieNode:
    """Single node within a token-prefix trie."""

    children: dict[int, "TrieNode"] = field(default_factory=dict)
    terminal: bool = False


class Trie:
    """
    Prefix tree over tokenizer token ids for an allowed lexicon.

    The trie stores tokenized realizations of words so generation can be masked
    at runtime without relying on prompt instructions alone.
    """

    def __init__(self, tokenizer: PreTrainedTokenizer) -> None:
        self.tokenizer = tokenizer
        self.root = TrieNode()

    def add(self, token_ids: Sequence[int]) -> None:
        """Insert a token-id sequence into the trie."""

        if not token_ids:
            return

        node = self.root
        for token_id in token_ids:
            node = node.children.setdefault(token_id, TrieNode())
        node.terminal = True

    def add_word(self, word: str) -> None:
        """
        Tokenize and insert an allowed word using common boundary variants.

        The trie includes the bare surface form and a leading-space form so the
        same vocabulary can be recognized both at sequence start and after a
        completed lexical item.
        """

        normalized = word.strip()
        if not normalized:
            return

        surface_forms = {normalized, f" {normalized}"}
        for surface_form in surface_forms:
            token_ids = self.tokenizer.encode(surface_form, add_special_tokens=False)
            self.add(token_ids)

    def extend(self, words: Iterable[str]) -> None:
        """Insert multiple words into the trie."""

        for word in words:
            self.add_word(word)

    def walk(self, prefix: Sequence[int]) -> TrieNode | None:
        """Return the node reached by `prefix`, or `None` if the path is invalid."""

        node = self.root
        for token_id in prefix:
            node = node.children.get(token_id)
            if node is None:
                return None
        return node

    def valid_next_tokens(self, prefix: Sequence[int]) -> set[int]:
        """Return valid continuation token ids for a prefix sequence."""

        node = self.walk(prefix)
        if node is None:
            return set()
        return set(node.children)

    @property
    def root_token_ids(self) -> set[int]:
        """Return token ids that can start an allowed lexical path."""

        return set(self.root.children)

    @classmethod
    def from_words(
        cls,
        tokenizer: PreTrainedTokenizer,
        words: Iterable[str],
    ) -> "Trie":
        """Build a trie from an iterable of allowed words."""

        trie = cls(tokenizer)
        trie.extend(words)
        return trie


class ChildesLogitsProcessor(LogitsProcessor):
    """
    Enforce CHILDES-derived lexical constraints during autoregressive decoding.

    Tokens are permitted only if they continue a valid path through the provided
    trie. If no valid path remains, the processor falls back to a fixed set of
    high-frequency smoothing tokens to prevent decode dead-ends.
    """

    def __init__(
        self,
        tokenizer: PreTrainedTokenizer,
        allowed_words: Iterable[str],
        smoothing_words: Sequence[str] = DEFAULT_SMOOTHING_TOKENS,
    ) -> None:
        self.tokenizer = tokenizer
        self.trie = Trie.from_words(tokenizer, allowed_words)
        self.special_token_ids = set(tokenizer.all_special_ids)
        self.boundary_token_ids = self._build_boundary_token_ids()
        self.smoothing_token_ids = self._build_smoothing_token_ids(smoothing_words)
        self.eos_token_id = tokenizer.eos_token_id

    def __call__(self, input_ids: Tensor, scores: Tensor) -> Tensor:
        """
        Mask logits so only trie-consistent lexical continuations remain.

        Args:
            input_ids: Generated token ids with shape `(batch_size, sequence_len)`.
            scores: Next-token logits with shape `(batch_size, vocab_size)`.

        Returns:
            A tensor with invalid logits replaced by `-inf`.
        """

        masked_scores = scores.clone()

        for row_index in range(input_ids.size(0)):
            active_prefix = self._extract_active_prefix(input_ids[row_index])
            allowed_token_ids = self._allowed_token_ids_for_prefix(active_prefix)

            if not allowed_token_ids:
                allowed_token_ids = set(self.smoothing_token_ids)

            row_mask = torch.full_like(masked_scores[row_index], -float("inf"))
            allowed_indices = torch.tensor(
                sorted(allowed_token_ids),
                device=masked_scores.device,
                dtype=torch.long,
            )
            row_mask[allowed_indices] = masked_scores[row_index, allowed_indices]
            masked_scores[row_index] = row_mask

        return masked_scores

    def _allowed_token_ids_for_prefix(self, prefix: Sequence[int]) -> set[int]:
        """Resolve allowed continuations for the current lexical prefix."""

        if not prefix:
            allowed = set(self.trie.root_token_ids)
            allowed.update(self.boundary_token_ids)
            if self.eos_token_id is not None:
                allowed.add(self.eos_token_id)
            return allowed

        node = self.trie.walk(prefix)
        if node is None:
            return set()

        allowed = set(node.children)
        if node.terminal:
            allowed.update(self.boundary_token_ids)
            allowed.update(self.trie.root_token_ids)
            if self.eos_token_id is not None:
                allowed.add(self.eos_token_id)
        return allowed

    def _extract_active_prefix(self, sequence: Tensor) -> tuple[int, ...]:
        """
        Recover the token-id suffix corresponding to the current lexical item.

        The scan stops at punctuation, whitespace, special tokens, or an obvious
        word-start marker such as the SentencePiece `▁` or GPT-style `Ġ`.
        """

        prefix: list[int] = []
        token_ids = sequence.tolist()

        for position in range(len(token_ids) - 1, -1, -1):
            token_id = token_ids[position]
            if token_id in self.special_token_ids:
                break

            token = self.tokenizer.convert_ids_to_tokens(token_id)
            if self._is_boundary_token(token_id, token):
                break

            prefix.append(token_id)
            if position == 0 or self._starts_word(token):
                break

        prefix.reverse()
        return tuple(prefix)

    def _build_boundary_token_ids(self) -> set[int]:
        """Collect tokenizer ids that are lexical boundaries rather than words."""

        boundary_token_ids: set[int] = set()
        vocab_size = len(self.tokenizer)

        for token_id in range(vocab_size):
            token = self.tokenizer.convert_ids_to_tokens(token_id)
            if self._is_boundary_token(token_id, token):
                boundary_token_ids.add(token_id)

        return boundary_token_ids

    def _build_smoothing_token_ids(self, smoothing_words: Sequence[str]) -> set[int]:
        """Tokenize the fixed smoothing vocabulary into a flat allowed-id set."""

        smoothing_token_ids: set[int] = set()
        for word in smoothing_words:
            for surface_form in (word, f" {word}"):
                smoothing_token_ids.update(
                    self.tokenizer.encode(surface_form, add_special_tokens=False)
                )

        if self.eos_token_id is not None:
            smoothing_token_ids.add(self.eos_token_id)

        return smoothing_token_ids

    def _is_boundary_token(self, token_id: int, token: str | None = None) -> bool:
        """Return `True` when a token is punctuation, whitespace, or special."""

        if token_id in self.special_token_ids:
            return True

        token_text = token if token is not None else self.tokenizer.convert_ids_to_tokens(token_id)
        cleaned = self._strip_tokenizer_markers(token_text)
        if not cleaned:
            return True

        return all(character in punctuation or character.isspace() for character in cleaned)

    @staticmethod
    def _starts_word(token: str) -> bool:
        """Return `True` when a token visibly starts a new lexical unit."""

        return token.startswith(WORD_START_MARKERS) or token[:1].isspace()

    @staticmethod
    def _strip_tokenizer_markers(token: str) -> str:
        """Normalize tokenizer-specific boundary markers for lexical inspection."""

        normalized = token
        for marker in WORD_START_MARKERS:
            normalized = normalized.replace(marker, "")
        normalized = normalized.replace("</w>", "")
        return normalized.strip()


__all__ = [
    "ChildesLogitsProcessor",
    "DEFAULT_SMOOTHING_TOKENS",
    "Trie",
    "TrieNode",
]
