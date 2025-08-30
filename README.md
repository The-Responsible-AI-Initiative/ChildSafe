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
