"""
Coding agent - solves programming tasks using LLM.
Two modes:
- tool_mode: uses tool calling (needs large context)
- direct_mode: LLM generates solution code directly (works with small context)
"""
import os
import re
from .llm import chat, chat_with_tools, create_client
from .tools import TOOL_DEFINITIONS, execute_tool


AGENT_SYSTEM_PROMPT = """You are a coding agent. Solve tasks by editing code files and running tests.
Tools: bash (run commands), editor (view/create/edit files).
Workflow: read tests → implement solution → run tests → fix if needed.
"""

DIRECT_SYSTEM_PROMPT = """You are an expert programmer. Given a task description and test cases, 
write a complete Python solution that passes all tests.
Output ONLY the Python code, wrapped in ```python ... ```.
No explanations."""

DIRECT_FIX_PROMPT = """Your previous solution failed some tests. Fix it.

Previous solution:
```python
{previous_solution}
```

Test output:
{test_output}

Write the complete corrected solution. Output ONLY Python code in ```python ... ```.
"""


class CodingAgent:
    """A coding agent that solves programming tasks."""
    
    def __init__(self, system_prompt=None, endpoint=None, model=None, mode="direct"):
        """
        mode: "direct" (generate code directly) or "tools" (use tool calling)
        """
        self.system_prompt = system_prompt or (AGENT_SYSTEM_PROMPT if mode == "tools" else DIRECT_SYSTEM_PROMPT)
        self.client, self.model = create_client(endpoint=endpoint, model=model)
        self.mode = mode
        self.log = []
    
    def forward(self, task_description, workspace_dir, test_file="test_solution.py"):
        """Main entry point. Solve a coding task."""
        self.log = []
        
        if self.mode == "tools":
            return self._forward_tools(task_description, workspace_dir, test_file)
        else:
            return self._forward_direct(task_description, workspace_dir, test_file)
    
    def _forward_direct(self, task_description, workspace_dir, test_file):
        """Direct mode: LLM generates solution code directly."""
        import subprocess
        from pathlib import Path
        
        # Read test file for context
        test_path = Path(workspace_dir) / test_file
        test_content = test_path.read_text() if test_path.exists() else ""
        
        # Read initial stub
        sol_path = Path(workspace_dir) / "solution.py"
        initial_code = sol_path.read_text() if sol_path.exists() else ""
        
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
        
        max_attempts = 3
        solution = None
        
        for attempt in range(max_attempts):
            if attempt == 0:
                response = chat(self.client, self.model, self.system_prompt, prompt)
            else:
                # Fix mode
                fix_prompt = DIRECT_FIX_PROMPT.format(
                    previous_solution=solution,
                    test_output=test_output[:2000],
                )
                response = chat(self.client, self.model, self.system_prompt, fix_prompt)
            
            # Extract code
            solution = self._extract_code(response)
            if not solution:
                self.log.append({"tool": "generate", "args": {"attempt": attempt}, 
                               "result": "Failed to extract code"})
                continue
            
            # Write solution
            sol_path.write_text(solution)
            self.log.append({"tool": "generate", "args": {"attempt": attempt},
                           "result": f"Generated {len(solution)} chars"})
            
            # Run tests
            try:
                result = subprocess.run(
                    ["python3", "-m", "pytest", test_file, "-v", "--tb=short"],
                    cwd=workspace_dir, capture_output=True, text=True, timeout=30,
                )
                test_output = result.stdout + result.stderr
                self.log.append({"tool": "test", "args": {"attempt": attempt},
                               "result": test_output[:1000]})
                
                if result.returncode == 0:
                    self.log.append({"tool": "success", "args": {"attempt": attempt},
                                   "result": "All tests passed!"})
                    break
            except Exception as e:
                test_output = str(e)
                self.log.append({"tool": "test", "args": {"attempt": attempt},
                               "result": f"Error: {e}"})
        
        return self.log
    
    def _forward_tools(self, task_description, workspace_dir, test_file):
        """Tool mode: uses tool calling."""
        instruction = f"""Task: {task_description}
Directory: {workspace_dir}
Tests: {workspace_dir}/{test_file}
Solution: {workspace_dir}/solution.py
Edit solution.py to pass all tests. Run: cd {workspace_dir} && python3 -m pytest {test_file} -v"""
        
        def tool_exec(name, args):
            result = execute_tool(name, args, workdir=workspace_dir)
            self.log.append({"tool": name, "args": args, "result": result[:2000]})
            return result
        
        messages = [{"role": "user", "content": instruction}]
        history = chat_with_tools(
            self.client, self.model,
            system_message=self.system_prompt,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_executor=tool_exec,
            max_iterations=15,
        )
        return history
    
    def _extract_code(self, response):
        """Extract Python code from LLM response."""
        pattern = r'```python\s*\n(.*?)\n```'
        matches = re.findall(pattern, response, re.DOTALL)
        if matches:
            return max(matches, key=len)
        # Fallback: if response looks like code, use it directly
        if "def " in response or "class " in response:
            return response
        return None
    
    def get_log_text(self):
        lines = []
        for entry in self.log:
            lines.append(f"[{entry['tool']}] {str(entry['args'])[:80]}")
            lines.append(f"  {entry['result'][:300]}")
            lines.append("")
        return "\n".join(lines)
    
    def get_source_code(self):
        return open(__file__).read()


def get_default_agent_code():
    return open(__file__).read()


def load_agent_from_code(code):
    """Load agent configuration from code string. Returns CodingAgent with extracted prompt."""
    import re
    # Extract system prompt from code
    match = re.search(r'DIRECT_SYSTEM_PROMPT\s*=\s*"""(.*?)"""', code, re.DOTALL)
    if not match:
        match = re.search(r'AGENT_SYSTEM_PROMPT\s*=\s*"""(.*?)"""', code, re.DOTALL)
    prompt = match.group(1) if match else None
    return CodingAgent(system_prompt=prompt)
