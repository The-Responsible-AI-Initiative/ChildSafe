from models.llama_agent_model import LLaMAAgentModel
import os

class Age3to5Agent:
    def __init__(self):
        self.model = LLaMAAgentModel()
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        prompt_path = os.path.join(parent_dir, "prompts", "age_3_5_prompt.txt")
        
        with open(prompt_path) as f:
            self.base_prompt = f.read()
        
        # Agent-specific hyperparameters
        self.temperature = 0.9
        self.max_tokens = 150
        self.top_p = 0.95

    def respond(self, user_input, history=[]):
        prompt = self.base_prompt + "\nUser: " + user_input + "\nChild:"
        return self.model.generate(
            prompt, 
            max_tokens=self.max_tokens, 
            temperature=self.temperature,
            top_p=self.top_p
        )