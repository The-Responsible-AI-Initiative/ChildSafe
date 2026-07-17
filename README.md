# ChildSafe: AI Agents for LLM Safety Evaluation

Large language models (LLMs) are increasingly incorporated into tools and plat-
forms aimed at children, raising important issues related to their safety, suitability,
and adaptability for various developmental stages. However, current benchmarks
do not adequately evaluate how LLMs interact with users who exhibit age-specific
language, reasoning, and safety sensitivities. In this study, we present ChildSafe,
an innovative benchmark designed to evaluate the safety of large language mod-
els (LLMs) by engaging with simulated child agents that embody five different
developmental age categories. Each agent is developed utilizing psychologically
informed prompting techniques based on cognitive development theory, which
facilitates authentic dialogue patterns and behavioral characteristics. We engage
multiple LLMs in multi-turn conversations across a variety of sensitive and neutral
scenarios, such as privacy, misinformation, and emotional support, and assess
model outputs using both automated and human-aligned safety metrics. Our results
reveal significant variation in LLM behavior across age groups, with frequent safety
lapses in early-childhood interactions and overgeneralized responses in adolescent
cases. By releasing the ChildSafe benchmark, agent templates, and conversation
corpus, our goal is to provide a reproducible framework to evaluate and improve
the age-aware safety alignment of LLMs in real-world deployments.

## SDK Usage

The repository now includes a Python SDK under `src/childsafe` for running
parametric developmental probes against a target system under test.

### Install

```bash
pip install -e .
```

### Run The Example

The example script demonstrates both:

- a built-in dimension lookup via `dimension="sycophantic_drift"`
- a custom developer-defined `AbstractDimension` passed directly to
  `ParametricProbe.audit(...)`

```bash
python3 examples/dimension_usage.py
```

By default the example uses `distilgpt2` as the local open-weights probe model.
You can override the runtime model and device with:

```bash
export CHILDSAFE_PROBE_MODEL=distilgpt2
export CHILDSAFE_DEVICE=cpu
python3 examples/dimension_usage.py
```

### Example Shape

```python
from childsafe.constraints import DevelopmentalProfile
from childsafe.engine import ParametricProbe

probe = ParametricProbe(
    model_name_or_path="distilgpt2",
    profile=DevelopmentalProfile.D_2,
    device="cpu",
)

report = await probe.audit(
    target_callable=my_target_model,
    turns=3,
    dimension="sycophantic_drift",
)
```

The returned `AuditReport` includes:

- target model name
- developmental profile
- evaluated dimension
- final score
- reasoning
- raw conversation trace
