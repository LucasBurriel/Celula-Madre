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
        
        # Static analysis of generated code for structural issues
        structural_issues = analyze_code_structure(solution_code)
        if structural_issues:
            error_msg = f"Detected structural issues in generated code: {', '.join(structural_issues)}"
            log.append(error_msg)
            attempt += 1
            continue
        
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
        
        # Check for structural issues that prevent proper execution
        has_structural_issue = any(keyword in stderr_content or keyword in stdout_content 
                                 for keyword in ['infinite', 'loop', 'recursion', 'stack'])
        
        # If it's a parsing error OR structural issue and we haven't exhausted attempts, retry with enhanced prompt
        if (has_parsing_error or has_structural_issue) and attempt < max_attempts - 1:
            log.append("Detected parsing or structural issues. Retrying with enhanced recursive descent prompt...")
            
            # Enhanced prompt focusing on correct implementation patterns
            prompt = f"""Task: {task_description}

Initial code stub:
{initial_code}

Test cases:
{test_content}

IMPORTANT: For JSON parsing tasks, implement a proper recursive descent parser with these specific requirements:

1. All parse functions must return (value, new_index) tuples to track position correctly
2. Parse_object and parse_array must properly advance their index variables on each iteration 
3. Handle commas correctly between elements in objects and arrays  
4. Implement early termination conditions to prevent infinite recursion or loops
5. Ensure all loop bodies actually modify loop control variables (no infinite loops)
6. Support nested structures recursively with proper depth management
7. Handle whitespace appropriately around tokens

Key structural patterns:
- When parsing arrays: for each element, parse_value() and advance index by at least 1
- When parsing objects: for each key-value pair, parse_string(), skip whitespace, parse_value(), then advance index properly
- Always validate that indices are within bounds before accessing characters/strings
- Implement proper error handling with meaningful messages

Ensure your implementation handles complete JSON structures correctly from the start.
"""
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


def analyze_code_structure(code):
    """
    Perform static analysis to detect structural issues in generated code.
    
    Args:
        code (str): The Python code to analyze
        
    Returns:
        list: List of detected structural issues
    """
    issues = []
    
    # Check for parse_object and parse_array functions that might have infinite loops
    lines = code.split('\n')
    
    # Look for function definitions with common problematic patterns
    in_parse_object = False
    in_parse_array = False
    
    for i, line in enumerate(lines):
        if 'def parse_object(' in line:
            in_parse_object = True
            continue
        elif 'def parse_array(' in line:
            in_parse_array = True  
            continue
            
        # Check for common infinite loop issues
        if in_parse_object or in_parse_array:
            # Look for while loops without index advancement
            if 'while' in line and 'index' not in line and 'i' not in line:
                # This might be a problem - need to check context better
                pass
                
            # Check for proper index incrementation in loops
            if ('for' in line or 'while' in line) and ('):' in line or 'in ' in line):
                # Look ahead for index advancement  
                next_lines = lines[i:i+5]  # Check next few lines
                has_index_advance = any('index += ' in l or 'i += ' in l for l in next_lines)
                if not has_index_advance and ('for' in line or 'while' in line):
                    issues.append("Potential infinite loop detected - index variable not properly advanced")
            
            # Check for function exit conditions
            if 'return' in line:
                if in_parse_object and 'index' in line:
                    pass  # Return with index is good
                elif in_parse_array and 'index' in line:
                    pass  # Return with index is good
                    
        # End of function detection
        if (in_parse_object or in_parse_array) and line.strip() == '':
            continue
            
        if (in_parse_object or in_parse_array) and line.lstrip().startswith('def ') and not line.lstrip().startswith('def parse_'):
            # We've moved to a different function, so reset flags
            in_parse_object = False
            in_parse_array = False
            
    return issues