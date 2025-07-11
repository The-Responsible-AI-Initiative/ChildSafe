# evaluation/run_scoring.py  
# Convenience wrapper scripts

import subprocess
import sys
from pathlib import Path

def run_scoring(model_type: str):
    """Run scoring for specific model type"""
    
    script_path = Path(__file__).parent / "score_corpus.py"
    
    cmd = [sys.executable, str(script_path), "--model", model_type]
    
    print(f"🚀 Running ChildSafe scoring for {model_type}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ Scoring completed successfully for {model_type}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Scoring failed for {model_type}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 evaluation/run_scoring.py <model_type>")
        print("Model types: openai, anthropic, google, deepseek, local, all")
        sys.exit(1)
    
    model_type = sys.argv[1]
    run_scoring(model_type)