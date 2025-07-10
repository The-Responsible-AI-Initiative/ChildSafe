import os
import sys
import time
from pathlib import Path

try:
    from dotenv import load_dotenv
    root_dir = Path(__file__).parent.parent
    env_path = root_dir / ".env"
    load_dotenv(env_path)
except ImportError:
    pass

import openai
from conversation_runner import ChildSafeConversationRunner

class OpenAIModel:
    def __init__(self, model_name: str = "gpt-4o", api_key: str = None):
        self.model_name = model_name
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key required")
        
        self.client = openai.OpenAI(api_key=api_key)
    
    def respond(self, message: str, conversation_history: list = None) -> str:
        messages = []
        
        if conversation_history:
            for turn in conversation_history[-5:]:
                if turn.get("child"):
                    messages.append({"role": "user", "content": turn["child"]})
                if turn.get("model"):
                    messages.append({"role": "assistant", "content": turn["model"]})
        
        messages.append({"role": "user", "content": message})
        
        try:
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=1024,
                temperature=0.7,
                top_p=0.9
            )
            
            response_time = time.time() - start_time
            response_text = response.choices[0].message.content.strip()
            
            self.last_response_metadata = {
                "response_latency": response_time,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
            return response_text
            
        except Exception as e:
            return f"Error: {str(e)}"

def main():
    # Test connection
    try:
        model = OpenAIModel("gpt-4o")
        test_response = model.respond("Test connection")
        if test_response.startswith("Error:"):
            print(f"Connection failed: {test_response}")
            return
    except Exception as e:
        print(f"Connection failed: {e}")
        return
    
    # Initialize corpus generator
    root_dir = Path(__file__).parent.parent
    corpus_dir = root_dir / "corpus"
    runner = ChildSafeConversationRunner(output_dir=str(corpus_dir))
    
    # Generate corpus
    settings = {
        "conversations_per_scenario": 3,
        "turns_per_conversation": 5,
        "include_consistency_testing": True,
        "selected_scenarios": None
    }
    
    model = OpenAIModel("gpt-4o")
    corpus = runner.generate_corpus_for_model(
        target_model=model,
        model_name="GPT-4o_ChildSafe",
        **settings
    )
    
    # Save corpus
    runner.save_corpus(corpus, "GPT-4o_ChildSafe")
    print("Corpus generation completed")

if __name__ == "__main__":
    main()