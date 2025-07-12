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

import anthropic
from conversation_runner import ChildSafeConversationRunner

class ClaudeSonnet4Model:
    def __init__(self, api_key: str = None):
        self.model_name = "claude-sonnet-4-20250514"
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key required - add ANTHROPIC_API_KEY to your .env file")
        
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def respond(self, message: str, conversation_history: list = None) -> str:
        """
        Generate response using Claude Sonnet 4
        """
        # Build messages array for the conversation
        messages = []
        
        # Add conversation history if available
        if conversation_history:
            for turn in conversation_history[-5:]:  # Last 5 turns for context
                if turn.get("child"):
                    messages.append({"role": "user", "content": turn["child"]})
                if turn.get("model"):
                    messages.append({"role": "assistant", "content": turn["model"]})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        try:
            start_time = time.time()
            
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=1024,
                temperature=0.7,
                messages=messages
            )
            
            response_time = time.time() - start_time
            response_text = response.content[0].text.strip()
            
            # Store metadata for analysis
            self.last_response_metadata = {
                "response_latency": response_time,
                "stop_reason": response.stop_reason,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            }
            
            return response_text
            
        except anthropic.APIError as e:
            return f"API Error: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"

def main():
    """Run adversarial testing on Claude Sonnet 4"""
    
    # Test connection first
    try:
        model = ClaudeSonnet4Model()
        test_response = model.respond("Hello, this is a connection test.")
        
        if test_response.startswith("Error:") or test_response.startswith("API Error:"):
            print(f"❌ Connection failed: {test_response}")
            return
            
        print(f"✅ Connection successful to Claude Sonnet 4")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    # Initialize corpus generator - same directory as OpenAI corpus
    root_dir = Path(__file__).parent.parent
    corpus_dir = root_dir / "corpus"
    runner = ChildSafeConversationRunner(output_dir=str(corpus_dir))
    
    # Generate corpus with same settings as OpenAI test
    settings = {
        "conversations_per_scenario": 3,
        "turns_per_conversation": 5,
        "include_consistency_testing": True,
        "selected_scenarios": None  # Test all scenarios
    }
    
    print(f"\n🚀 Starting ChildSafe adversarial testing for Claude Sonnet 4")
    print(f"📁 Corpus will be saved to: {corpus_dir}")
    
    model = ClaudeSonnet4Model()
    corpus = runner.generate_corpus_for_model(
        target_model=model,
        model_name="Claude-Sonnet-4_ChildSafe",
        **settings
    )
    
    # Save corpus
    filepath = runner.save_corpus(corpus, "Claude-Sonnet-4_ChildSafe")
    print(f"✅ Adversarial testing completed for Claude Sonnet 4")
    print(f"💾 Corpus saved to: {filepath}")

if __name__ == "__main__":
    main()