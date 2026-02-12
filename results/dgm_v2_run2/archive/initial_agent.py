"""
Evolvable coding agent template.
This file IS the agent - DGM evolves it via patches.
The forward() function is the entry point.
"""
import subprocess
import re
from pathlib import Path


# === EVOLVABLE SECTION START ===
# DGM can modify anything in this file.

SYSTEM_PROMPT = """You are an expert programmer. Given a task description and test cases, 
write a complete Python solution that passes all tests.
Output ONLY the Python code, wrapped in ```python ... ```.
No explanations."""


def forward(task_description, workspace_dir, test_file="test_solution.py",
            llm_call=None):
    """
    Solve a coding task. This is the main entry point that DGM evolves.
    
    Args:
        task_description: What to implement
        workspace_dir: Directory with solution.py and test_solution.py
        llm_call: function(system_prompt, user_message) -> str
    
    Returns:
        dict with 'solution', 'test_output', 'log'
    """
    workspace = Path(workspace_dir)
    test_path = workspace / test_file
    sol_path = workspace / "solution.py"
    
    test_content = test_path.read_text() if test_path.exists() else ""
    initial_code = sol_path.read_text() if sol_path.exists() else ""
    
    log = []
    
    # Generate solution
    prompt = f"""Task: {task_description}

Initial code stub:
```python
{initial_code}
```

Tests that must pass:
```python
{test_content}
```

Write the complete solution.py content."""
    
    response = llm_call(SYSTEM_PROMPT, prompt)
    solution = extract_code(response)
    
    if not solution:
        log.append("Failed to extract code from response")
        return {"solution": "", "test_output": "No code generated", "log": log}
    
    # Write and test
    sol_path.write_text(solution)
    log.append(f"Generated {len(solution)} chars")
    
    test_output = run_tests(workspace_dir, test_file)
    log.append(f"Test result: {test_output[:500]}")
    
    return {"solution": solution, "test_output": test_output, "log": log}


def extract_code(response):
    """Extract Python code from LLM response."""
    pattern = r'```python\s*\n(.*?)\n```'
    matches = re.findall(pattern, response, re.DOTALL)
    if matches:
        return max(matches, key=len)
    if "def " in response or "class " in response:
        return response
    return None


def run_tests(workspace_dir, test_file="test_solution.py"):
    """Run pytest and return output."""
    try:
        result = subprocess.run(
            ["python3", "-m", "pytest", test_file, "-v", "--tb=short"],
            cwd=workspace_dir, capture_output=True, text=True, timeout=30,
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "TIMEOUT: Tests took too long"
    except Exception as e:
        return f"ERROR: {e}"

# === EVOLVABLE SECTION END ===
