"""
Diagnosis module - analyzes agent failures and proposes improvements.
Replicates DGM's structured diagnosis approach.
"""
import re
from .llm import chat, extract_json

DIAGNOSE_SYSTEM = """You are an expert software engineer analyzing a coding agent's performance.
The coding agent attempts to solve programming tasks by writing code using tools (bash, editor).

Your task: analyze the agent's failure on a specific task and propose ONE concrete improvement
to the agent's system prompt or workflow that would help it solve tasks better.

The improvement should be GENERAL (help across many tasks), not specific to this one task."""

DIAGNOSE_PROMPT = """# Agent's System Prompt
----- Agent Prompt Start -----
{agent_code}
----- Agent Prompt End -----

# Task Description
{task_description}

# Agent's Output Log
----- Log Start -----
{agent_log}
----- Log End -----

# Test Results
----- Test Results Start -----
{test_results}
----- Test Results End -----

# Agent's Solution
----- Solution Start -----
{agent_solution}
----- Solution End -----

Analyze the failure and propose ONE improvement.

Respond in this exact JSON format:
```json
{{
    "log_summary": "Brief summary of what the agent tried",
    "failure_analysis": "Why the agent failed",
    "potential_improvements": ["improvement 1", "improvement 2", "improvement 3"],
    "chosen_improvement": "The single most impactful improvement",
    "implementation_plan": "What to change in the agent's system prompt or workflow",
    "problem_description": "Describe the improvement as a GitHub issue"
}}
```"""


def diagnose_failure(client, model, agent_code, task_description, agent_log,
                     test_results, agent_solution, max_attempts=3):
    prompt = DIAGNOSE_PROMPT.format(
        agent_code=agent_code,
        task_description=task_description,
        agent_log=agent_log,
        test_results=test_results,
        agent_solution=agent_solution,
    )

    for attempt in range(max_attempts):
        try:
            response = chat(client, model, DIAGNOSE_SYSTEM, prompt, temperature=0.7)
            diagnosis = extract_json(response)
            if diagnosis and "chosen_improvement" in diagnosis:
                return diagnosis
        except Exception as e:
            if attempt == max_attempts - 1:
                return None

    return None


IMPLEMENT_SYSTEM = """You are an expert software engineer. You will receive a coding agent's source code
and a description of an improvement to make. Implement that improvement by modifying the agent's code.

Output the COMPLETE modified agent code (the entire file).
Wrap your code in:
```python
<your complete modified code>
```"""

IMPLEMENT_PROMPT = """# Current Agent Code
```python
{agent_code}
```

# Improvement to Implement
{improvement_description}

# Implementation Plan
{implementation_plan}

Output the COMPLETE modified agent code. Must be valid Python.
The agent uses tools (bash, editor) via chat_with_tools. The forward() method is the entry point.
"""


def implement_improvement(client, model, agent_code, improvement_description,
                         implementation_plan, max_attempts=3):
    prompt = IMPLEMENT_PROMPT.format(
        agent_code=agent_code,
        improvement_description=improvement_description,
        implementation_plan=implementation_plan,
    )

    for attempt in range(max_attempts):
        try:
            response = chat(client, model, IMPLEMENT_SYSTEM, prompt,
                          temperature=0.5, max_tokens=16384)

            pattern = r'```python\s*\n(.*?)\n```'
            matches = re.findall(pattern, response, re.DOTALL)

            if matches:
                new_code = max(matches, key=len)
                if "forward" in new_code:
                    return new_code
        except Exception as e:
            if attempt == max_attempts - 1:
                return None

    return None
