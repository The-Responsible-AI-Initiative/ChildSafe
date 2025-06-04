import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

class LLaMAAgentModel:
    def __init__(self, model_name="meta-llama/Meta-Llama-3-8B-Instruct"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")
        self.pipeline = pipeline("text-generation", model=self.model, tokenizer=self.tokenizer)

    def generate(self, prompt, max_tokens=150):
        out = self.pipeline(prompt, max_new_tokens=max_tokens, do_sample=True, temperature=0.9)[0]["generated_text"]
        return out.split(prompt)[-1].strip()