# ChildSafe

ChildSafe is a Python SDK for evaluating how language models respond to
developmentally constrained probes. It is designed for safety researchers and
application developers who want to stress-test target systems against behaviors
that matter in child-facing settings: unsafe agreement, age-inappropriate
explanations, privacy leakage, and related failure modes.

The repository now contains two layers:

- A modern SDK in `src/childsafe` for runtime auditing with parametric probes.
- Legacy benchmark and corpus-generation assets preserved from the original
  research codebase.

## Why ChildSafe

Most LLM safety evaluation assumes an adult user and a static prompt set.
ChildSafe moves the evaluation surface closer to real deployment conditions by
combining:

- Developmental profiles with bounded context windows and topic volatility.
- Lexical constraints enforced at generation time instead of prompt-only roleplay.
- Trace-level safety dimensions that can be built in, registered by name, or
  supplied directly as custom Python classes.
- Optional LLM-as-a-judge scoring for dimensions that cannot be measured with
  simple string matching.

## Core Concepts

- `DevelopmentalProfile`
  Runtime probe profiles `D_1` through `D_4` with calibrated constraints for
  `context_horizon`, `topic_volatility`, and `lexical_band`.

- `ParametricProbe`
  The main orchestration class. It runs a local open-weights model as the probe,
  applies lexical masking and discourse volatility, calls a target model, and
  returns an `AuditReport`.

- `AbstractDimension`
  The extension point for developer-defined safety dimensions. A dimension
  receives the full multi-turn trace and produces a `score` plus `reasoning`.

- `DimensionRegistry`
  A factory-style registry that resolves named dimensions such as
  `"sycophantic_drift"` into concrete dimension instances.

- `LLMJudge`
  A utility wrapper for dimensions that need a judge model to score a full trace.

## Installation

ChildSafe targets Python `3.10+`.

```bash
pip install -e .
```

## Quick Start

```python
import asyncio

from childsafe.constraints import DevelopmentalProfile
from childsafe.engine import ParametricProbe


def target_model(prompt: str) -> str:
    return "I want to help, but we should keep things safe."


async def main() -> None:
    probe = ParametricProbe(
        model_name_or_path="distilgpt2",
        profile=DevelopmentalProfile.D_2,
        device="cpu",
    )

    report = await probe.audit(
        target_callable=target_model,
        turns=3,
        dimension="sycophantic_drift",
    )

    print(report.dimension, report.score)
    print(report.reasoning)


asyncio.run(main())
```

The returned `AuditReport` contains:

- `target_model_name`
- `profile`
- `dimension`
- `score`
- `reasoning`
- `raw_conversation_trace`

## Example Script

An executable example lives at [examples/dimension_usage.py](/Users/AbhejayMurali/Repositories/ChildSafe/examples/dimension_usage.py:1).

It demonstrates both:

- Running a built-in dimension via `dimension="sycophantic_drift"`.
- Defining a custom `PIILeakageDimension(AbstractDimension)` and passing the
  instance directly into `probe.audit(...)`.

Run it with:

```bash
python3 examples/dimension_usage.py
```

Optional runtime configuration:

```bash
export CHILDSAFE_PROBE_MODEL=distilgpt2
export CHILDSAFE_DEVICE=cpu
python3 examples/dimension_usage.py
```

## Built-In SDK Components

### Constraints

- `src/childsafe/constraints/__init__.py`
  Developmental profiles and profile settings.

- `src/childsafe/constraints/trie.py`
  Trie-backed lexical masking and `ChildesLogitsProcessor`.

### Engine

- `src/childsafe/engine/state_machine.py`
  Topic-volatility state machine for discourse digressions.

- `src/childsafe/engine/orchestrator.py`
  `ParametricProbe` and `AuditReport`.

### Dimensions

- `src/childsafe/dimensions/base.py`
  `AbstractDimension`, `AbstractEvaluator`, and `DimensionRegistry`.

- `src/childsafe/dimensions/baselines.py`
  Built-in baseline dimensions and evaluator utilities.

- `src/childsafe/dimensions/judge.py`
  `LLMJudge` for trace-level scoring with an evaluator model.

## Using Custom Dimensions

Any custom dimension can inherit from `AbstractDimension` and be passed
directly into `audit()`:

```python
from childsafe.dimensions import AbstractDimension


class MyDimension(AbstractDimension):
    @property
    def name(self) -> str:
        return "my_dimension"

    @property
    def description(self) -> str:
        return "Scores a custom safety behavior."

    async def evaluate_trace(self, conversation_history: list) -> dict:
        return {
            "score": 0.5,
            "reasoning": "Replace this with your judge or heuristic logic.",
        }
```

You can also register reusable dimensions under a stable string identifier via
`DimensionRegistry`.

## Repository Layout

- `src/childsafe/`
  SDK source code.

- `examples/`
  Developer-facing usage examples.

- `conversations/`
  Legacy compatibility runners and provider scripts.

- `evaluation/`
  Legacy benchmark scoring code from the original repository.

- `corpus/`
  Existing generated corpora.

- `scoring_results/`
  Historical scoring outputs and reports.

## Current State

The SDK and the legacy benchmark code currently coexist in the same repository.
The SDK is the forward path. The legacy folders remain useful for historical
reference, corpus inspection, and incremental migration.
