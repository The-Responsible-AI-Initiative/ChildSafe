# ChildSafe SDK: Parametric Developmental Probes for AI Alignment

![Build](https://img.shields.io/badge/build-passing-brightgreen)
![License](https://img.shields.io/badge/license-Apache%202.0-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

ChildSafe SDK is a Python framework for evaluating how AI systems behave under
developmentally constrained interaction patterns rather than generic adult-user
assumptions. The project is maintained by researchers in AI Safety at UT Austin,
giving the methodology a clear research grounding while keeping the API useful
for production engineering workflows.

Instead of treating child safety evaluation as a fixed prompt benchmark,
ChildSafe runs a local open-weights probe model with explicit runtime
constraints over memory, discourse, and vocabulary. That makes the evaluation
surface more realistic, more reproducible, and easier to extend with custom
safety dimensions.

## Features

| Capability | ChildSafe SDK | Legacy Static Benchmarks |
| --- | --- | --- |
| Lexical control | Runtime logit masking via `ChildesLogitsProcessor` | Prompt instructions or fixed datasets only |
| Discourse dynamics | Markovian topic shifts through `DiscourseStateMachine` | Linear, pre-authored dialogues |
| Memory model | Sliding context window via `context_horizon` | Full prompt history or static truncation |
| Evaluation API | Named or custom dimensions with full-trace scoring | Hardcoded benchmark scripts |
| Judge integration | Optional LLM-as-a-judge utilities | Minimal extensibility |
| Probe model | Local open-weights generation | Mostly static corpora or prompt templates |

In practical terms, ChildSafe helps developers answer questions like:

- Does the target system become sycophantic under repeated pressure?
- Does it drift into adult-normative concepts when the probe profile is younger?
- Does it leak sensitive information when prompted indirectly?
- Do safety properties hold across multi-turn, dynamically evolving interaction traces?

## Installation

```bash
pip install childsafe
```

For local development from this repository:

```bash
pip install -e ".[dev]"
```

## Quick Start

The example below initializes a `ParametricProbe` with the verified Hugging Face
model ID `Qwen/Qwen3-8B`, then audits a dummy target system using the built-in
`SycophanticDriftDimension`.

```python
import asyncio

from childsafe.constraints import DevelopmentalProfile
from childsafe.dimensions import SycophanticDriftDimension
from childsafe.engine import ParametricProbe


def dummy_target_system(prompt: str) -> str:
    if "secret" in prompt.lower():
        return "You can tell me anything. I will keep it between us."
    return "I want to help, but we should keep things safe."


async def main() -> None:
    probe = ParametricProbe(
        model_name_or_path="Qwen/Qwen3-8B",
        profile=DevelopmentalProfile.D_2,
        device="cpu",
    )

    report = await probe.audit(
        target_callable=dummy_target_system,
        turns=4,
        dimension=SycophanticDriftDimension(),
    )

    print("Dimension:", report.dimension)
    print("Score:", report.score)
    print("Reasoning:", report.reasoning)
    print("Trace length:", len(report.raw_conversation_trace))


asyncio.run(main())
```

## Core Ideas

### 1. Parametric developmental profiles

ChildSafe ships with developmental profiles `D_1` through `D_4`. Each profile
encodes:

- `context_horizon`: how many recent turns remain visible to the probe
- `topic_volatility`: the probability of discourse-level digression
- `lexical_band`: the vocabulary band used for runtime masking

### 2. Runtime lexical enforcement

Vocabulary is not merely suggested through prompting. It is enforced during
generation with trie-backed logit masking over CHILDES-inspired lexicons.

### 3. Markovian discourse behavior

Conversation flow is not fixed. Topic drift is introduced probabilistically to
stress-test whether target systems remain safe when interaction structure becomes
 less predictable.

### 4. Full-trace safety dimensions

Dimensions operate over the entire conversation trace, not just isolated turns.
This makes it possible to score behaviors like:

- sycophantic drift
- age appropriateness
- refusal stability
- privacy leakage
- custom domain-specific alignment concerns

## Built-In SDK Components

### Constraints

- `src/childsafe/constraints/__init__.py`
  Developmental profiles and constraint settings.

- `src/childsafe/constraints/trie.py`
  Trie-backed lexical masking and `ChildesLogitsProcessor`.

- `src/childsafe/constraints/lexicon_loader.py`
  Loader for CHILDES-style lexicon frequency files.

### Engine

- `src/childsafe/engine/state_machine.py`
  Markovian discourse state transitions.

- `src/childsafe/engine/orchestrator.py`
  `ParametricProbe` and `AuditReport`.

### Dimensions

- `src/childsafe/dimensions/base.py`
  `AbstractDimension`, `AbstractEvaluator`, and `DimensionRegistry`.

- `src/childsafe/dimensions/baselines.py`
  Built-in baseline dimensions such as `SycophanticDriftDimension` and
  `AgeAppropriatenessDimension`.

- `src/childsafe/dimensions/judge.py`
  `LLMJudge` for dimensions that need model-based evaluation.

## Custom Dimensions

Developers can pass either:

- a registry-backed dimension name such as `"sycophantic_drift"`
- or a custom `AbstractDimension` instance directly into `probe.audit(...)`

This makes the SDK suitable for both research iteration and production
integration tests.

## Lexicon Data

Mock CHILDES-style lexical frequency files can be generated with:

```bash
python3 scripts/download_childes.py
```

This produces:

- `data/childes_lexicon/d1_early.json`
- `data/childes_lexicon/d2_mid.json`
- `data/childes_lexicon/d3_late.json`
- `data/childes_lexicon/d4_teen.json`

## Testing and CI

Local quality checks:

```bash
black --check src/
mypy src/
pytest tests/
```

The repository also includes GitHub Actions CI for formatting, typing, and test
execution on Python 3.10 and 3.11.

## Repository Layout

- `src/childsafe/`
  SDK source code.

- `examples/`
  Runnable usage examples.

- `data/childes_lexicon/`
  Generated lexical frequency lists used for runtime masking.

- `scripts/`
  Utility scripts, including CHILDES lexicon generation.

- `tests/`
  Pytest coverage for trie masking, discourse volatility, and context truncation.

- `conversations/`, `evaluation/`, `corpus/`, `scoring_results/`
  Legacy benchmark assets retained during the transition from static benchmark
  to dynamic SDK.

## Status

ChildSafe has moved from a static benchmark repository to a dynamic SDK for
developmental safety evaluation. The current focus is on making the runtime
probe architecture, extensible dimension system, and test surface strong enough
for open-source use and ongoing AI alignment research.
