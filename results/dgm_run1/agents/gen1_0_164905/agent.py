import os
from openai import OpenAI

LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://172.17.0.1:1234/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3-coder-30b-a3b-instruct")
LLM_API_KEY = os.getenv("LLM_API_KEY", "lm-studio")


def solve(task_description: str, initial_code: str, reasoning_steps: int = 1) -> str:
    """
    Solve a coding task by generating Python code.
    
    Args:
        task_description: Description of what the code should do
        initial_code: Template/starter code to build on
        reasoning_steps: Number of reasoning steps for complex problems (default: 1)
    
    Returns:
        Complete Python code that solves the task
    """
    client = OpenAI(base_url=LLM_ENDPOINT, api_key=LLM_API_KEY)
    
    # Enhanced system message with chain-of-thought prompting
    system_prompt = f"""You are an expert Python programmer. Follow this structured approach for complex tasks:
1. First analyze the problem requirements step-by-step
2. Then design your solution approach 
3. Finally generate the implementation

Output ONLY valid Python code. No markdown, no explanations, no