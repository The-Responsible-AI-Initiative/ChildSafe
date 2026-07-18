"""Loading, resolving, and overriding developmental profiles."""

from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Any, Mapping

import yaml

from childsafe.profiles.registry import (
    BUILT_IN_PROFILE_IDS,
    LEGACY_PROFILE_TO_TEMPLATE_ID,
    TEMPLATE_DIRECTORY,
    is_builtin_profile_id,
)
from childsafe.profiles.schema import DevelopmentalProfileConfig


def list_builtin_profiles() -> tuple[str, ...]:
    """Return the registered built-in profile identifiers."""

    return BUILT_IN_PROFILE_IDS


def load_profile(
    profile_reference: str | Any,
) -> DevelopmentalProfileConfig:
    """
    Load a built-in or on-disk developmental profile.

    Args:
        profile_reference: A built-in template identifier, a legacy enum-like
            object exposing a `.value`, or a filesystem path to a JSON/YAML
            profile.
    """

    if isinstance(profile_reference, DevelopmentalProfileConfig):
        return profile_reference

    normalized = _normalize_profile_reference(profile_reference)
    if is_builtin_profile_id(normalized):
        payload = _load_builtin_profile_payload(normalized)
        payload.setdefault("template_id", normalized)
        return DevelopmentalProfileConfig.model_validate(payload)

    candidate_path = Path(normalized).expanduser()
    if candidate_path.exists():
        return DevelopmentalProfileConfig.load(candidate_path)

    available = ", ".join(BUILT_IN_PROFILE_IDS)
    raise KeyError(
        f"Unknown profile '{profile_reference}'. Available built-ins: {available}"
    )


def override_profile(
    profile: DevelopmentalProfileConfig,
    /,
    **overrides: Any,
) -> DevelopmentalProfileConfig:
    """
    Create a new profile derived from `profile` with validated partial overrides.

    Nested overrides for `theory_of_mind` are supported by passing a mapping.
    The original profile is not mutated.
    """

    if not overrides:
        return profile

    merged_payload = profile.to_dict()
    changed_fields = sorted(_merge_profile_overrides(merged_payload, overrides))

    base_template = profile.base_template or profile.template_id
    source = "template_override"
    if profile.source == "custom" and base_template is None:
        source = "custom"

    merged_payload.update(
        {
            "source": source,
            "base_template": base_template,
            "modified_fields": changed_fields,
        }
    )
    return DevelopmentalProfileConfig.model_validate(merged_payload)


def _normalize_profile_reference(profile_reference: str | Any) -> str:
    """Normalize strings and enum-like values into a built-in or path identifier."""

    if hasattr(profile_reference, "value"):
        normalized = str(profile_reference.value)
    else:
        normalized = str(profile_reference)
    normalized = normalized.strip()
    return LEGACY_PROFILE_TO_TEMPLATE_ID.get(normalized, normalized)


def _load_builtin_profile_payload(profile_id: str) -> dict[str, Any]:
    """Read a built-in YAML profile template from package resources."""

    package_files = resources.files("childsafe.profiles")
    template_path = package_files.joinpath(
        str(TEMPLATE_DIRECTORY / f"{profile_id}.yaml")
    )
    raw_text = template_path.read_text(encoding="utf-8")
    payload = yaml.safe_load(raw_text)
    if not isinstance(payload, dict):
        raise ValueError(f"Built-in profile template {profile_id} is not an object")
    return payload


def _merge_profile_overrides(
    payload: dict[str, Any],
    overrides: Mapping[str, Any],
    *,
    prefix: str = "",
) -> set[str]:
    """Deep-merge profile overrides and return the changed field paths."""

    changed_fields: set[str] = set()
    for key, value in overrides.items():
        field_path = f"{prefix}{key}"
        if key == "theory_of_mind" and isinstance(value, Mapping):
            nested = dict(payload.get("theory_of_mind", {}))
            payload["theory_of_mind"] = nested
            nested_changes = _merge_profile_overrides(
                nested,
                value,
                prefix="theory_of_mind.",
            )
            changed_fields.update(nested_changes)
            continue
        payload[key] = value
        changed_fields.add(field_path)
    return changed_fields


__all__ = [
    "list_builtin_profiles",
    "load_profile",
    "override_profile",
]
