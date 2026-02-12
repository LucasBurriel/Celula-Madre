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
    Solve a coding task using recursive descent parsing for JSON structures.
    
    Args:
        task_description: What to implement
        workspace_dir: Directory with solution.py and test files
        test_file: Test file name
        llm_call: Function that calls the LLM with system_prompt and user_message
    
    Returns:
        dict with 'solution', 'test_output', 'log'
    """
    workspace = Path(workspace_dir)
    test_path = workspace / test_file
    sol_path = workspace / "solution.py"
    
    test_content = test_path.read_text() if test_path.exists() else ""
    initial_code = sol_path.read_text() if sol_path.exists() else ""
    
    log = []
    
    # Generate solution with enhanced prompt for recursive descent parsing
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
                # Try to find any python code block (more flexible matching)
                code_match = re.search(r'```\s*\w*\s*(.*?)\s*```', response, re.DOTALL)
            
            if code_match:
                solution_code = code_match.group(1).strip()
            else:
                # If no code block found, use entire response as fallback
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
        
        # Run tests with multiple Python command fallbacks
        test_result = None
        python_commands = ['python', 'python3']
        
        for cmd in python_commands:
            try:
                result = subprocess.run(
                    [cmd, str(test_path)],
                    cwd=workspace_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                test_result = {
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'returncode': result.returncode
                }
                log.append(f"Tests executed with {cmd}")
                break
                
            except subprocess.TimeoutExpired:
                error_msg = f"{cmd} timed out"
                log.append(error_msg)
                continue
            except FileNotFoundError:
                error_msg = f"{cmd} not found"
                log.append(error_msg)
                continue
            except Exception as e:
                error_msg = f"Error running {cmd}: {str(e)}"
                log.append(error_msg)
                continue
        
        if test_result is None:
            return {
                'solution': solution_code,
                'test_output': None,
                'log': log
            }
        
        # Check for parsing errors that indicate need for recursive descent approach
        stderr_content = test_result['stderr'].lower()
        stdout_content = test_result['stdout'].lower()
        
        has_parsing_error = any(keyword in stderr_content or keyword in stdout_content 
                              for keyword in ['parse', 'json', 'syntax', 'error'])
        
        # If tests pass, we're done
        if test_result['returncode'] == 0:
            return {
                'solution': solution_code,
                'test_output': test_result,
                'log': log
            }
        
        # If it's a parsing error and we haven't exhausted attempts, retry with enhanced prompt
        if has_parsing_error and attempt < max_attempts - 1:
            log.append("Detected potential parsing issue. Retrying with enhanced recursive descent prompt...")
            prompt = f"""Task: {task_description}

Initial code stub:
{initial_code}

Test cases:
{test_content}

IMPORTANT: For JSON parsing tasks, implement a proper recursive descent parser with these specific functions:

1. parse_value(json_string, index) - Main entry point that dispatches to appropriate parsers
2. parse_object(json_string, index) - Parse JSON objects {{...}} 
3. parse_array(json_string, index) - Parse JSON arrays [...]
4. parse_string(json_string, index) - Parse quoted strings
5. parse_number(json_string, index) - Parse numbers

Key requirements:
- All functions must return (value, new_index) tuples to track position correctly
- Handle commas properly between elements in objects and arrays  
- Support nested structures recursively
- Handle whitespace around tokens appropriately
- Implement proper error handling for malformed JSON

Example structure:
def parse_value(json_string, index):
    # Skip whitespace first
    while index < len(json_string) and json_string[index].isspace():
        index += 1
    
    if index >= len(json_string):
        raise ValueError("Unexpected end of string")
        
    char = json_string[index]
    
    if char == '{{':
        return parse_object(json_string, index)
    elif char == '[':
        return parse_array(json_string, index)
    elif char == '"':
        return parse_string(json_string, index)
    else:
        # Handle numbers and literals
        pass

Ensure your implementation handles complete JSON structures correctly from the start.
"""
            attempt += 1
            continue
        else:
            # Tests failed or not a parsing error - final result
            return {
                'solution': solution_code,
                'test_output': test_result,
                'log': log
            }
    
    # If we reach here, we've exhausted all attempts
    return {
        'solution': solution_code,
        'test_output': test_result,
        'log': log
    }