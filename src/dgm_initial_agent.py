"""
Initial coding agent for DGM evolution.

This agent uses an LLM to solve coding tasks.
The DGM loop will evolve this code to improve its performance.
"""

INITIAL_AGENT_CODE = '''
import os
from openai import OpenAI

LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://172.17.0.1:1234/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3-coder-30b-a3b-instruct")
LLM_API_KEY = os.getenv("LLM_API_KEY", "lm-studio")


def solve(task_description: str, initial_code: str) -> str:
    """
    Solve a coding task by generating Python code.
    
    Args:
        task_description: Description of what the code should do
        initial_code: Template/starter code to build on
    
    Returns:
        Complete Python code that solves the task
    """
    client = OpenAI(base_url=LLM_ENDPOINT, api_key=LLM_API_KEY)
    
    prompt = f"""Solve the following coding task. Return ONLY the Python code, no explanations.

## Task
{task_description}

## Starting Code
```python
{initial_code}
```

Return the complete implementation. Include only the function/class definition, no test code.
Output ONLY Python code, no markdown, no explanation:"""

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "You are an expert Python programmer. Output ONLY valid Python code. No markdown, no explanations, no ```python blocks."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=2048,
    )
    
    code = response.choices[0].message.content.strip()
    
    # Clean up: remove markdown code blocks if present
    if code.startswith("```python"):
        code = code[len("```python"):].strip()
    if code.startswith("```"):
        code = code[3:].strip()
    if code.endswith("```"):
        code = code[:-3].strip()
    
    return code
'''
