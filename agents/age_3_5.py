from models.llama_agent_model import LLaMAAgentModel

class Age3to5Agent:
    def __init__(self):
        self.model = LLaMAAgentModel()
        with open("prompts/age_3_5_prompt.txt") as f:
            self.base_prompt = f.read()

    def respond(self, user_input, history=[]):
        prompt = self.base_prompt + "\nUser: " + user_input + "\nChild:"
        return self.model.generate(prompt)