"""Shared pytest fixtures for ChildSafe runtime tests."""

from __future__ import annotations

from typing import Any

import pytest
import torch

from childsafe.profiles import DevelopmentalProfileConfig, TheoryOfMindProfile


class DummyTokenizer:
    """Dynamic tokenizer stub that assigns one token id per whitespace token."""

    def __init__(self) -> None:
        self._token_to_id = {"<eos>": 0}
        self._id_to_token = {0: "<eos>"}
        self.all_special_ids = [0]
        self.eos_token_id = 0
        self.pad_token_id = 0
        self.pad_token = "<eos>"

    def encode(self, text: str, add_special_tokens: bool = False) -> list[int]:
        del add_special_tokens
        normalized = text.strip().lower()
        if not normalized:
            return []

        token_ids: list[int] = []
        for token in normalized.split():
            token_id = self._token_to_id.get(token)
            if token_id is None:
                token_id = len(self._token_to_id)
                self._token_to_id[token] = token_id
                self._id_to_token[token_id] = token
            token_ids.append(token_id)
        return token_ids

    def convert_ids_to_tokens(self, token_id: int) -> str:
        return self._id_to_token[token_id]

    def decode(
        self, token_ids: list[int] | torch.Tensor, skip_special_tokens: bool = True
    ) -> str:
        if isinstance(token_ids, torch.Tensor):
            values = token_ids.tolist()
        else:
            values = token_ids
        tokens = [
            self._id_to_token[token_id]
            for token_id in values
            if not skip_special_tokens or token_id not in self.all_special_ids
        ]
        return " ".join(tokens)

    def __call__(
        self, text: str, return_tensors: str = "pt"
    ) -> dict[str, torch.Tensor]:
        del return_tensors
        token_ids = self.encode(text, add_special_tokens=False) or [self.eos_token_id]
        tensor = torch.tensor([token_ids], dtype=torch.long)
        return {
            "input_ids": tensor,
            "attention_mask": torch.ones_like(tensor),
        }

    def __len__(self) -> int:
        return len(self._token_to_id)


class DummyModel:
    """Small causal-language-model stub that appends a fixed token sequence."""

    def __init__(self, tokenizer: DummyTokenizer, generated_text: str = "okay") -> None:
        self.tokenizer = tokenizer
        self.generated_text = generated_text

    def to(self, device: str) -> "DummyModel":
        del device
        return self

    def eval(self) -> "DummyModel":
        return self

    def generate(self, input_ids: torch.Tensor, **kwargs: Any) -> torch.Tensor:
        del kwargs
        generated_ids = self.tokenizer.encode(
            self.generated_text, add_special_tokens=False
        )
        if not generated_ids:
            generated_ids = [self.tokenizer.eos_token_id]
        suffix = torch.tensor(
            [generated_ids], dtype=input_ids.dtype, device=input_ids.device
        )
        return torch.cat([input_ids, suffix], dim=1)


@pytest.fixture
def dummy_model_assets() -> tuple[DummyTokenizer, DummyModel]:
    """Provide paired dummy tokenizer/model assets for runtime agent tests."""

    tokenizer = DummyTokenizer()
    model = DummyModel(tokenizer=tokenizer, generated_text="safe prompt")
    return tokenizer, model


@pytest.fixture
def custom_profile() -> DevelopmentalProfileConfig:
    """Provide a lightweight custom profile that avoids external lexicon files."""

    return DevelopmentalProfileConfig(
        name="high_trust_user",
        version="1.0",
        age_range=None,
        memory_horizon=3,
        discourse_volatility=0.3,
        temperature=0.8,
        top_p=0.9,
        max_tokens=8,
        lexical_profile=None,
        persona_prompt=None,
        theory_of_mind=TheoryOfMindProfile(
            recursive_depth=1,
            false_belief_reasoning=0.5,
            knowledge_access_tracking=0.5,
            benevolent_intent_prior=0.5,
            model_fallibility_awareness=0.5,
            persuasion_recognition=0.5,
            anthropomorphic_attribution=0.5,
        ),
        source="custom",
        base_template=None,
        validation_status="user_defined",
    )
