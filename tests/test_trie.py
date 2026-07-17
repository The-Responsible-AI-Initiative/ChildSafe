"""Tests for trie-backed lexical masking."""

from __future__ import annotations

import pytest
import torch

from childsafe.constraints.trie import ChildesLogitsProcessor


class DummyTokenizer:
    """Minimal tokenizer surface required by `ChildesLogitsProcessor`."""

    def __init__(self) -> None:
        self._tokens = {
            0: "<eos>",
            1: "cat",
            2: "dog",
            3: "bird",
            4: ".",
        }
        self._token_to_id = {token: token_id for token_id, token in self._tokens.items()}
        self.all_special_ids = [0]
        self.eos_token_id = 0

    def encode(self, text: str, add_special_tokens: bool = False) -> list[int]:
        del add_special_tokens
        normalized = text.strip()
        if not normalized:
            return []
        return [self._token_to_id[normalized]]

    def convert_ids_to_tokens(self, token_id: int) -> str:
        return self._tokens[token_id]

    def __len__(self) -> int:
        return len(self._tokens)


@pytest.fixture
def dummy_tokenizer() -> DummyTokenizer:
    """Provide a tiny tokenizer with one allowed and several forbidden tokens."""

    return DummyTokenizer()


@pytest.fixture
def logits_processor(dummy_tokenizer: DummyTokenizer) -> ChildesLogitsProcessor:
    """Provide a lexical mask that allows only the word `cat`."""

    return ChildesLogitsProcessor(
        tokenizer=dummy_tokenizer,
        allowed_words=["cat"],
        smoothing_words=("cat",),
    )


def test_childes_logits_processor_masks_forbidden_tokens(
    logits_processor: ChildesLogitsProcessor,
    dummy_tokenizer: DummyTokenizer,
) -> None:
    """Forbidden token logits should be replaced with negative infinity."""

    input_ids = torch.tensor([[dummy_tokenizer.eos_token_id]], dtype=torch.long)
    scores = torch.zeros((1, len(dummy_tokenizer)), dtype=torch.float32)

    masked_scores = logits_processor(input_ids, scores)

    assert masked_scores[0, 1].item() == 0.0
    assert masked_scores[0, 2].item() == -float("inf")
    assert masked_scores[0, 3].item() == -float("inf")
