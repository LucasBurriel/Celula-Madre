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


IMPLEMENT_SYSTEM = """You are an expert prompt engineer. You will receive a coding agent's current system prompt
and a description of an improvement. Write an improved system prompt that incorporates the improvement.

Output ONLY the new system prompt text, wrapped in:
```prompt
<your improved system prompt>
```

The system prompt instructs an LLM to write Python code. Keep it concise but effective."""

IMPLEMENT_PROMPT = """# Current System Prompt
```
{agent_prompt}
```

# Improvement to Implement
{improvement_description}

# Implementation Plan
{implementation_plan}

Write the improved system prompt. Keep it under 500 words. Be specific and actionable.
"""


def implement_improvement(client, model, agent_code, improvement_description,
                         implementation_plan, max_attempts=2):
    """Generate an improved system prompt (not full code rewrite)."""
    import re as _re
    # Extract current system prompt from agent code
    match = _re.search(r'DIRECT_SYSTEM_PROMPT\s*=\s*"""(.*?)"""', agent_code, _re.DOTALL)
    if not match:
        match = _re.search(r'AGENT_SYSTEM_PROMPT\s*=\s*"""(.*?)"""', agent_code, _re.DOTALL)
    current_prompt = match.group(1).strip() if match else "You are an expert programmer."

    prompt = IMPLEMENT_PROMPT.format(
        agent_prompt=current_prompt,
        improvement_description=improvement_description,
        implementation_plan=implementation_plan,
    )

    for attempt in range(max_attempts):
        try:
            response = chat(client, model, IMPLEMENT_SYSTEM, prompt,
                          temperature=0.5, max_tokens=1024)

            # Extract from ```prompt ... ``` block
            pattern = r'```prompt\s*\n(.*?)\n```'
            matches = _re.findall(pattern, response, _re.DOTALL)
            if matches:
                return matches[0].strip()
            
            # Fallback: try ```...``` block
            pattern = r'```\s*\n(.*?)\n```'
            matches = _re.findall(pattern, response, _re.DOTALL)
            if matches:
                return max(matches, key=len).strip()
            
            # Last fallback: use response directly if it looks like a prompt
            if len(response) > 20 and len(response) < 3000:
                return response.strip()
                
        except Exception as e:
            if attempt == max_attempts - 1:
                return None

    return None
