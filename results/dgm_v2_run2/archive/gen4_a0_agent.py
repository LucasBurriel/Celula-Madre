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
{initial_code}

Test cases:
{test_content}"""
    
    try:
        response = llm_call(SYSTEM_PROMPT, prompt)
        log.append(f"LLM Response: {response[:200]}...")
        
        # Extract Python code from markdown
        code_match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
        if code_match:
            extracted_code = code_match.group(1)
        else:
            # If no markdown formatting found, use the entire response
            extracted_code = response.strip()
        
        solution = extracted_code
        
        # Run tests
        test_output = ""
        try:
            # Write the solution to the file
            sol_path.write_text(solution)
            
            # Run the tests
            result = subprocess.run(
                ["python", str(test_path)],
                cwd=workspace_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            test_output = result.stdout + result.stderr
            
        except Exception as e:
            log.append(f"Error running tests: {str(e)}")
            test_output = f"Test execution error: {str(e)}"
            
    except Exception as e:
        log.append(f"LLM call failed: {str(e)}")
        solution = initial_code
        test_output = f"LLM generation failed: {str(e)}"
    
    return {
        'solution': solution,
        'test_output': test_output,
        'log': log
    }