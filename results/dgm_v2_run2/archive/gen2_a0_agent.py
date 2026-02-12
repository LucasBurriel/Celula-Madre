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
write a complete Python solution that passes all tests. For JSON parsing tasks, implement a proper recursive descent parser with functions like parse_value(), parse_object(), parse_array(). Ensure your implementation handles complete JSON structures correctly from the start.

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
    
    max_attempts = 3
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = llm_call(SYSTEM_PROMPT, prompt)
            log.append(f"LLM Response (attempt {attempt + 1}): {response[:200]}...")
            
            # Extract Python code from response
            code_match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
            if not code_match:
                # Try to find any python code block
                code_match = re.search(r'```\s*.*?python\s*(.*?)\s*```', response, re.DOTALL)
            
            if code_match:
                solution_code = code_match.group(1).strip()
            else:
                # If no code block found, use the entire response as fallback
                solution_code = response.strip()
                
            log.append("Code extraction successful")
            
        except Exception as e:
            error_msg = f"LLM call failed: {str(e)}"
            log.append(error_msg)
            return {
                'solution': None,
                'test_output': None,
                'log': log
            }
        
        # Write solution to file
        try:
            sol_path.write_text(solution_code)
            log.append("Solution written to file")
        except Exception as e:
            error_msg = f"Failed to write solution: {str(e)}"
            log.append(error_msg)
            return {
                'solution': None,
                'test_output': None,
                'log': log
            }
        
        # Run tests
        try:
            result = subprocess.run(
                ['python', str(test_path)],
                cwd=workspace_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            test_output = {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
            
            log.append(f"Tests completed. Return code: {result.returncode}")
            
            # Check if this is a parsing error that might be fixed with recursive descent
            stderr_content = test_output['stderr'].lower()
            stdout_content = test_output['stdout'].lower()
            
            has_parsing_error = any(keyword in stderr_content or keyword in stdout_content 
                                  for keyword in ['parse', 'json', 'syntax', 'error'])
            
            # If tests pass, we're done
            if result.returncode == 0:
                return {
                    'solution': solution_code,
                    'test_output': test_output,
                    'log': log
                }
            
            # If it's a parsing error and we haven't exhausted attempts, retry with enhanced prompt
            if has_parsing_error and attempt < max_attempts - 1:
                log.append("Detected potential parsing issue. Retrying with enhanced prompt...")
                prompt = f"""Task: {task_description}

Initial code stub:
{initial_code}

Test cases:
{test_content}

IMPORTANT: For JSON parsing tasks, implement a proper recursive descent parser with these specific functions:
- parse_value(json_string, index)
- parse_object(json_string, index) 
- parse_array(json_string, index)
- parse_string(json_string, index)
- parse_number(json_string, index)

Ensure your implementation handles complete JSON structures correctly from the start.
"""
                attempt += 1
                continue
            else:
                # Tests failed and we're at max attempts or not a parsing error
                return {
                    'solution': solution_code,
                    'test_output': test_output,
                    'log': log
                }
                
        except subprocess.TimeoutExpired:
            error_msg = "Test execution timed out"
            log.append(error_msg)
            return {
                'solution': solution_code,
                'test_output': None,
                'log': log
            }
        except Exception as e:
            error_msg = f"Failed to run tests: {str(e)}"
            log.append(error_msg)
            return {
                'solution': solution_code,
                'test_output': None,
                'log': log
            }
    
    # If we reach here, we've exhausted all attempts
    return {
        'solution': solution_code,
        'test_output': test_output,
        'log': log
    }