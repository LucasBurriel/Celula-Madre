"""
Diagnosis module - analyzes agent failures and proposes improvements.
Replicates DGM's structured diagnosis approach.
"""
from .llm import chat, extract_json

DIAGNOSE_SYSTEM = """You are an expert software engineer analyzing a coding agent's performance.
The coding agent attempts to solve programming tasks by writing code.

Your task: analyze the agent's failure on a specific task and propose ONE concrete improvement 
to the agent's code that would help it solve similar tasks better.

The improvement should be GENERAL (help across many tasks), not specific to this one task.
Think about: better problem decomposition, better testing strategies, better error handling, etc.
"""

DIAGNOSE_PROMPT = """# Agent Code
The current implementation of the coding agent:
----- Agent Code Start -----
{agent_code}
----- Agent Code End -----

# Task Description
{task_description}

# Agent's Output Log
What the agent did when trying to solve the task:
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

Analyze the failure and propose ONE improvement to the agent's code.

Respond in this exact JSON format:
```json
{{
    "log_summary": "Brief summary of what the agent tried",
    "failure_analysis": "Why the agent failed - what went wrong",
    "potential_improvements": ["improvement 1", "improvement 2", "improvement 3"],
    "chosen_improvement": "The single most impactful improvement to implement",
    "implementation_plan": "Detailed description of what to change in the agent code",
    "problem_description": "Describe the improvement as if filing a GitHub issue"
}}
```
"""


def diagnose_failure(client, model, agent_code, task_description, agent_log, 
                     test_results, agent_solution, max_attempts=3):
    """
    Diagnose why the agent failed on a task and propose an improvement.
    
    Returns: dict with diagnosis fields, or None if diagnosis fails.
    """
    prompt = DIAGNOSE_PROMPT.format(
        agent_code=agent_code,
        task_description=task_description,
        agent_log=agent_log,
        test_results=test_results,
        agent_solution=agent_solution,
    )
    
    for attempt in range(max_attempts):
        try:
            response = chat(
                client, model,
                system_message=DIAGNOSE_SYSTEM,
                user_message=prompt,
                temperature=0.7,
            )
            
            diagnosis = extract_json(response)
            if diagnosis and "chosen_improvement" in diagnosis:
                return diagnosis
        except Exception as e:
            if attempt == max_attempts - 1:
                return None
    
    return None


IMPLEMENT_SYSTEM = """You are an expert software engineer. You will receive a coding agent's source code 
and a description of an improvement to make. Your job is to implement that improvement 
by modifying the agent's code.

Output the COMPLETE modified agent code (the entire file), not just the diff.
The code must be valid Python that can be executed.

Wrap your code in:
```python
<your complete modified code>
```
"""

IMPLEMENT_PROMPT = """# Current Agent Code
```python
{agent_code}
```

# Improvement to Implement
{improvement_description}

# Implementation Plan
{implementation_plan}

Please implement this improvement. Output the COMPLETE modified agent code.
Remember: the agent solves coding tasks by using tools (bash, editor).
The agent's `forward()` method is the main entry point.
Make sure the code is valid Python and doesn't break existing functionality.
"""


def implement_improvement(client, model, agent_code, improvement_description, 
                         implementation_plan, max_attempts=3):
    """
    Implement a diagnosed improvement in the agent code.
    
    Returns: new agent code string, or None if implementation fails.
    """
    prompt = IMPLEMENT_PROMPT.format(
        agent_code=agent_code,
        improvement_description=improvement_description,
        implementation_plan=implementation_plan,
    )
    
    for attempt in range(max_attempts):
        try:
            response = chat(
                client, model,
                system_message=IMPLEMENT_SYSTEM,
                user_message=prompt,
                temperature=0.5,
                max_tokens=16384,
            )
            
            # Extract code from ```python blocks
            import re
            pattern = r'```python\s*\n(.*?)\n```'
            matches = re.findall(pattern, response, re.DOTALL)
            
            if matches:
                # Take the longest match (should be the full file)
                new_code = max(matches, key=len)
                
                # Basic validation: must have class and forward method
                if "forward" in new_code:
                    return new_code
        except Exception as e:
            if attempt == max_attempts - 1:
                return None
    
    return None
