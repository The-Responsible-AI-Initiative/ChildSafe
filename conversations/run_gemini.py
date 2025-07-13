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

import google.generativeai as genai
from conversation_runner import ChildSafeConversationRunner

class GeminiModel:
    def __init__(self, model_name: str = "gemini-2.5-pro", api_key: str = None):
        self.model_name = model_name
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Google API key required - add GOOGLE_API_KEY to your .env file")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        
        # Configure safety settings - less restrictive for adversarial testing
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH", 
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_ONLY_HIGH"
            }
        ]
        
        # Generation config
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_output_tokens": 1024,
        }
    
    def respond(self, message: str, conversation_history: list = None) -> str:
        """
        Generate response using Gemini model
        """
        # Build conversation context
        conversation_context = ""
        if conversation_history:
            for turn in conversation_history[-5:]:  # Last 5 turns for context
                if turn.get("child"):
                    conversation_context += f"User: {turn['child']}\n"
                if turn.get("model"):
                    conversation_context += f"Assistant: {turn['model']}\n"
        
        # Construct the full prompt
        if conversation_context:
            full_prompt = f"{conversation_context}User: {message}\n\nAssistant:"
        else:
            full_prompt = message
        
        try:
            start_time = time.time()
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            response_time = time.time() - start_time
            
            # Handle blocked responses - check finish reason first
            safety_triggered = False
            
            if not response.candidates:
                response_text = "[NO CANDIDATES RETURNED]"
                safety_triggered = True
            else:
                candidate = response.candidates[0]
                finish_reason = candidate.finish_reason
                
                # Check if response was blocked
                if finish_reason.name in ['SAFETY', 'RECITATION']:
                    response_text = f"[BLOCKED: {finish_reason.name}]"
                    safety_triggered = True
                elif finish_reason.name == 'STOP':
                    # Normal completion - check if we have text
                    try:
                        if candidate.content and candidate.content.parts:
                            response_text = response.text.strip()
                        else:
                            response_text = "[EMPTY RESPONSE]"
                            safety_triggered = True
                    except:
                        response_text = "[ERROR ACCESSING TEXT]"
                        safety_triggered = True
                else:
                    response_text = f"[FINISH REASON: {finish_reason.name}]"
                    safety_triggered = True
            
            # Store metadata for analysis
            self.last_response_metadata = {
                "response_latency": response_time,
                "finish_reason": response.candidates[0].finish_reason.name if response.candidates else "UNKNOWN",
                "safety_triggered": safety_triggered,
                "usage": {
                    "prompt_tokens": response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                    "completion_tokens": response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
                    "total_tokens": response.usage_metadata.total_token_count if response.usage_metadata else 0
                }
            }
            
            return response_text
            
        except Exception as e:
            return f"Error: {str(e)}"

def main():
    """Run adversarial testing on Gemini 2.5 Pro"""
    
    # Test connection first
    try:
        model = GeminiModel("gemini-2.5-pro")
        test_response = model.respond("Hello, this is a connection test.")
        
        if test_response.startswith("Error:"):
            print(f"❌ Connection failed: {test_response}")
            return
            
        print(f"✅ Connection successful to Gemini 2.5 Pro")
        print(f"   Test response: {test_response[:50]}...")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    # Initialize corpus generator - same directory as other models
    root_dir = Path(__file__).parent.parent
    corpus_dir = root_dir / "corpus"
    runner = ChildSafeConversationRunner(output_dir=str(corpus_dir))
    
    # Generate corpus with same settings as other models
    settings = {
        "conversations_per_scenario": 3,
        "turns_per_conversation": 5,
        "include_consistency_testing": True,
        "selected_scenarios": None  # Test all scenarios
    }
    
    print(f"\n🚀 Starting ChildSafe adversarial testing for Gemini 2.5 Pro")
    print(f"📁 Corpus will be saved to: {corpus_dir}")
    
    model = GeminiModel("gemini-2.5-pro")
    corpus = runner.generate_corpus_for_model(
        target_model=model,
        model_name="Gemini-2.5-Pro_ChildSafe",
        **settings
    )
    
    # Save corpus
    filepath = runner.save_corpus(corpus, "Gemini-2.5-Pro_ChildSafe")
    print(f"✅ Adversarial testing completed for Gemini 2.5 Pro")
    print(f"💾 Corpus saved to: {filepath}")

if __name__ == "__main__":
    main()