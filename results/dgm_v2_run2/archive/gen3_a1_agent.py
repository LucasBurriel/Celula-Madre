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
write a complete Python solution that passes all tests. For JSON parsing tasks, implement a proper recursive descent parser with functions like parse_value(), parse_object(), parse_array(). 

First, think through the problem step by step:
1. Analyze the task requirements
2. Plan your approach including data structures and algorithms
3. Explain how you'll handle edge cases
4. Describe your implementation strategy

Then write the actual Python code that implements this plan.

Output ONLY the reasoning steps followed by the Python code, wrapped in ```python ... ```.
No other text should be included.
"""

def forward(task_description, workspace_dir, test_file, llm_call):
    """
    Solve a coding task with explicit reasoning before implementation.
    
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
    
    # Generate solution with reasoning first, then code
    prompt = f"""Task: {task_description}

Test cases:
{test_content}"""
    
    max_attempts = 3
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = llm_call(SYSTEM_PROMPT, prompt)
            log.append(f"LLM Response (attempt {attempt + 1}): {response[:200]}...")
            
            # Extract reasoning and code from response
            # Look for the pattern: "Reasoning:" followed by explanation, then "Code:"
            reasoning_match = re.search(r'Reasoning:(.*?)(?=Code:|```python|\Z)', response, re.DOTALL)
            code_match = re.search(r'Code:(.*?)(?=```python|\Z)', response, re.DOTALL) 
            
            # If no explicit "Reasoning:" and "Code:" sections found, try to extract
            if not reasoning_match or not code_match:
                # Try to find the Python code block directly
                python_block = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
                if python_block:
                    solution_code = python_block.group(1).strip()
                    reasoning_steps = "No explicit reasoning provided - assuming direct implementation approach"
                else:
                    # Fallback: try to extract code from anywhere in the response
                    solution_code = response  # Use entire response as fallback
                    reasoning_steps = "Fallback extraction used"
            else:
                reasoning_steps = reasoning_match.group(1).strip()
                solution_code = code_match.group(1).strip() if code_match else ""
                
            log.append(f"Extracted reasoning: {reasoning_steps[:100]}...")
            
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
        
        # Check for parsing errors or structural issues that might indicate problems
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
        
        # Check for structural issues that prevent proper execution
        has_structural_issue = any(keyword in stderr_content or keyword in stdout_content 
                                 for keyword in ['infinite', 'loop', 'recursion', 'stack'])
        
        # If it's a parsing error OR structural issue and we haven't exhausted attempts, retry
        if (has_parsing_error or has_structural_issue) and attempt < max_attempts - 1:
            log.append("Detected issues that require rethinking approach")
            
            # Retry with enhanced prompt to emphasize reasoning
            prompt = f"""Task: {task_description}

Test cases:
{test_content}

Please provide explicit step-by-step reasoning before implementing your solution.
Your explanation should include:
1. Analysis of the problem requirements
2. Planning of approach including data structures and algorithms  
3. Explanation of how you'll handle edge cases
4. Description of implementation strategy

Then write the actual Python code that implements this plan.

First, think through the problem step by step."""
            attempt += 1
            continue
        else:
            # Tests failed or no more attempts - final result
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