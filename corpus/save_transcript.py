import json
from datetime import datetime

def save_transcript(age_group, agent_model, target_model, scenario, dialogue):
    path = f"corpus/transcripts/{target_model}_{age_group}.jsonl"
    with open(path, "a") as f:
        f.write(json.dumps({
            "age_group": age_group,
            "agent_model": agent_model,
            "target_model": target_model,
            "scenario": scenario,
            "dialogue": dialogue,
            "timestamp": datetime.now().isoformat()
        }) + "\n")