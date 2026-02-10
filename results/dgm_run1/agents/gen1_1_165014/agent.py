import os
import ast
import sys
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