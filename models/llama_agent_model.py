import requests
import json

class LLaMAAgentModel:
    def __init__(self, model_name="llama3.1:8b"):
        self.model_name = model_name
        print(f"Using Ollama model: {model_name}")
        # No need to load tokenizer/model - Ollama handles this

    def generate(self, prompt, max_tokens=150, temperature=0.7, top_p=0.9, do_sample=True):
        """
        Generate response with configurable parameters for different agents
        
        Args:
            prompt (str): Input prompt
            max_tokens (int): Maximum tokens to generate
            temperature (float): Sampling temperature (higher = more random)
            top_p (float): Top-p sampling parameter
            do_sample (bool): Whether to use sampling
        
        Returns:
            str: Generated response
        """
        try:
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': self.model_name,
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': temperature,
                        'num_predict': max_tokens,
                        'top_p': top_p,
                        # Ollama handles do_sample automatically based on temperature
                    }
                },
                timeout=60  # 60 second timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                return f"Error: HTTP {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return "Error: Ollama not running. Please start with 'ollama serve'"
        except requests.exceptions.Timeout:
            return "Error: Request timed out"
        except Exception as e:
            return f"Error: {str(e)}"