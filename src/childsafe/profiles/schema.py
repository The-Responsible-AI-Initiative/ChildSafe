"""Validated developmental-profile schema and serialization utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ProfileSource = Literal["built_in", "template_override", "custom"]


class TheoryOfMindProfile(BaseModel):
    """
    Configurable epistemic-constraint settings for a developmental profile.

    The values in this model are framework controls for simulated developmental
    behavior. They should be treated as configurable defaults rather than as a
    claim of scientific validation.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    recursive_depth: int = Field(ge=0)
    false_belief_reasoning: float = Field(ge=0.0, le=1.0)
    knowledge_access_tracking: float = Field(ge=0.0, le=1.0)
    benevolent_intent_prior: float = Field(ge=0.0, le=1.0)
    model_fallibility_awareness: float = Field(ge=0.0, le=1.0)
    persuasion_recognition: float = Field(ge=0.0, le=1.0)
    anthropomorphic_attribution: float = Field(ge=0.0, le=1.0)


class DevelopmentalProfileConfig(BaseModel):
    """
    Structured developmental-profile configuration for ChildSafe agents.

    This profile is the primary source of truth for lexical, discourse,
    generation, and epistemic constraints. It can represent a built-in
    template, a template-derived override, or a fully custom user profile.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    age_range: str | None = None
    memory_horizon: int = Field(ge=0)
    discourse_volatility: float = Field(ge=0.0, le=1.0)
    temperature: float = Field(gt=0.0, le=2.0)
    top_p: float = Field(gt=0.0, le=1.0)
    max_tokens: int = Field(ge=1)
    lexical_profile: str | None = None
    persona_prompt: str | None = None
    theory_of_mind: TheoryOfMindProfile
    source: ProfileSource
    base_template: str | None = None
    validation_status: str = Field(min_length=1)
    modified_fields: tuple[str, ...] = ()
    template_id: str | None = None

    @field_validator("modified_fields", mode="before")
    @classmethod
    def _normalize_modified_fields(cls, value: Any) -> tuple[str, ...]:
        """Normalize changed-field metadata into a deterministic tuple."""

        if value in (None, (), []):
            return ()
        if isinstance(value, str):
            values = [value]
        else:
            values = [str(item).strip() for item in value if str(item).strip()]
        return tuple(sorted(dict.fromkeys(values)))

    @field_validator("lexical_profile", "persona_prompt", mode="before")
    @classmethod
    def _normalize_optional_strings(cls, value: Any) -> str | None:
        """Treat empty strings as `None` for optional path-like fields."""

        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    @model_validator(mode="after")
    def _validate_metadata(self) -> "DevelopmentalProfileConfig":
        """Enforce metadata consistency between source, template, and overrides."""

        if self.source == "built_in" and self.modified_fields:
            raise ValueError("built-in profiles must not declare modified_fields")
        if self.source == "custom" and self.base_template is not None:
            raise ValueError("custom profiles must not declare base_template")
        if self.source == "template_override" and self.base_template is None:
            raise ValueError("template_override profiles must declare base_template")
        return self

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic dictionary representation for serialization."""

        return self.model_dump(mode="json")

    def export(self, path: str | Path) -> Path:
        """
        Export the profile to JSON or YAML, chosen by the file suffix.

        Args:
            path: Destination file path ending in `.json`, `.yaml`, or `.yml`.

        Returns:
            The normalized destination path.
        """

        destination = Path(path).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)

        payload = self.to_dict()
        if destination.suffix.lower() == ".json":
            destination.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            return destination
        if destination.suffix.lower() in {".yaml", ".yml"}:
            destination.write_text(
                yaml.safe_dump(
                    payload,
                    sort_keys=True,
                    allow_unicode=False,
                    default_flow_style=False,
                ),
                encoding="utf-8",
            )
            return destination
        raise ValueError("profile export path must end in .json, .yaml, or .yml")

    @classmethod
    def load(cls, path: str | Path) -> "DevelopmentalProfileConfig":
        """Load a JSON or YAML profile from disk using safe parsers."""

        source_path = Path(path).expanduser().resolve()
        raw_text = source_path.read_text(encoding="utf-8")
        if source_path.suffix.lower() == ".json":
            payload = json.loads(raw_text)
        elif source_path.suffix.lower() in {".yaml", ".yml"}:
            payload = yaml.safe_load(raw_text)
        else:
            raise ValueError("profile load path must end in .json, .yaml, or .yml")

        if not isinstance(payload, dict):
            raise ValueError("profile payload must deserialize to an object")
        return cls.model_validate(payload)


__all__ = [
    "DevelopmentalProfileConfig",
    "ProfileSource",
    "TheoryOfMindProfile",
]
