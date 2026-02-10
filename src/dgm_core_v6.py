"""
DGM Core — Simplified Darwin Gödel Machine replication.

Replicates the DGM self-improvement loop using local LLM (Qwen3-30B).
Phase 1: Benchmark fitness (replicate DGM)
Phase 2: Market fitness (Célula Madre thesis)
"""

import json
import math
import os
import random
import datetime
import subprocess
import tempfile
import shutil
from dataclasses import dataclass, field, asdict
from typing import Optional

from openai import OpenAI


# ── LLM Config ──────────────────────────────────────────────────────────

LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://172.17.0.1:1234/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3-coder-30b-a3b-instruct")
LLM_API_KEY = os.getenv("LLM_API_KEY", "lm-studio")


def get_client():
    return OpenAI(base_url=LLM_ENDPOINT, api_key=LLM_API_KEY)


def llm_call(messages: list, temperature: float = 0.7, max_tokens: int = 4096) -> str:
    """Simple LLM call via OpenAI-compatible API."""
    client = get_client()
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def extract_json(text: str) -> Optional[dict]:
    """Extract JSON from LLM response (between ```json markers or raw)."""
    import re
    # Try ```json block first
    match = re.search(r'```json\s*\n(.*?)```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass
    # Fallback: find first { ... }
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return None


# ── Data Structures ──────────────────────────────────────────────────────

@dataclass
class Agent:
    """An agent in the archive."""
    agent_id: str
    parent_id: Optional[str]  # None for initial
    generation: int
    code: str  # The full agent code (Python)
    accuracy: float = 0.0
    resolved_tasks: list = field(default_factory=list)
    unresolved_tasks: list = field(default_factory=list)
    children_count: int = 0
    diagnosis: Optional[str] = None  # What was diagnosed to create this agent
    patch: Optional[str] = None  # The diff that created this agent
    created_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())


@dataclass
class Task:
    """A coding task for evaluation."""
    task_id: str
    description: str
    test_code: str  # Code that tests the solution
    initial_code: str  # Starting code / template
    language: str = "python"


# ── Selection (from DGM) ────────────────────────────────────────────────

def score_child_prop_select(archive: list[Agent], k: int = 1) -> list[Agent]:
    """
    DGM's score_child_prop selection.
    P(parent) ∝ sigmoid(score) × 1/(1 + children_count)
    """
    if not archive:
        return []
    
    scores = []
    for agent in archive:
        # Sigmoid transform on accuracy
        sig = 1.0 / (1.0 + math.exp(-10 * (agent.accuracy - 0.5)))
        # Penalty for having many children (encourage exploration)
        child_penalty = 1.0 / (1.0 + agent.children_count)
        scores.append(sig * child_penalty)
    
    total = sum(scores)
    if total == 0:
        probs = [1.0 / len(archive)] * len(archive)
    else:
        probs = [s / total for s in scores]
    
    selected = random.choices(archive, weights=probs, k=k)
    return selected


# ── Diagnosis (from DGM) ────────────────────────────────────────────────

DIAGNOSE_SYSTEM = """You are an expert software engineer analyzing a coding agent's performance.

The agent's current code is:
```python
{agent_code}
```

Your task: identify ONE specific improvement that would make this agent solve more coding tasks correctly. Focus on general capability improvements, not task-specific fixes."""

DIAGNOSE_PROMPT = """The agent attempted to solve a task but failed.

## Task Description
{task_description}

## Agent's Output
{agent_output}

## Test Results
{test_results}

Analyze why the agent failed and propose ONE high-impact improvement.

Respond in JSON:
```json
{{
    "failure_analysis": "Why the agent failed on this specific task",
    "root_cause": "The underlying general weakness this reveals",
    "improvement_proposal": "Detailed description of ONE improvement",
    "implementation_plan": "Specific code changes to make"
}}
```"""


def diagnose(agent: Agent, task: Task, agent_output: str, test_results: str) -> Optional[dict]:
    """Diagnose why an agent failed on a task. Returns structured improvement proposal."""
    messages = [
        {"role": "system", "content": DIAGNOSE_SYSTEM.format(agent_code=agent.code)},
        {"role": "user", "content": DIAGNOSE_PROMPT.format(
            task_description=task.description,
            agent_output=agent_output,
            test_results=test_results,
        )},
    ]
    response = llm_call(messages, temperature=0.7)
    return extract_json(response)


# ── Mutation (Code Modification) ────────────────────────────────────────

MUTATE_SYSTEM = """You are an expert Python programmer. You will receive:
1. The current code of a coding agent
2. A diagnosis of what needs to be improved
3. An implementation plan

Your job: modify the agent's code to implement the improvement.
Return ONLY the complete modified Python code, wrapped in ```python blocks.
Do not explain — just return the code."""

MUTATE_PROMPT = """## Current Agent Code
```python
{agent_code}
```

## Diagnosis
{diagnosis}

## Implementation Plan
{implementation_plan}

Return the COMPLETE modified agent code:"""


def mutate(agent: Agent, diagnosis: dict) -> Optional[str]:
    """Apply a mutation to an agent's code based on diagnosis. Returns new code or None."""
    messages = [
        {"role": "system", "content": MUTATE_SYSTEM},
        {"role": "user", "content": MUTATE_PROMPT.format(
            agent_code=agent.code,
            diagnosis=diagnosis.get("improvement_proposal", ""),
            implementation_plan=diagnosis.get("implementation_plan", ""),
        )},
    ]
    response = llm_call(messages, temperature=0.7, max_tokens=8192)
    
    # Extract code from response
    import re
    match = re.search(r'```python\s*\n(.*?)```', response, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # If no code block, return the whole response if it looks like Python
    if "def " in response or "class " in response:
        return response.strip()
    
    return None


# ── Evaluation ──────────────────────────────────────────────────────────

def evaluate_agent_on_task(agent_code: str, task: Task, timeout: int = 30) -> dict:
    """
    Run an agent on a task and evaluate with tests.
    Returns: {"passed": bool, "output": str, "error": str}
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write agent code
        agent_file = os.path.join(tmpdir, "agent.py")
        with open(agent_file, "w") as f:
            f.write(agent_code)
        
        # Write task initial code
        task_file = os.path.join(tmpdir, "solution.py")
        with open(task_file, "w") as f:
            f.write(task.initial_code)
        
        # Write test code
        test_file = os.path.join(tmpdir, "test_solution.py")
        with open(test_file, "w") as f:
            f.write(task.test_code)
        
        # Run agent to generate solution
        try:
            # The agent reads the task and writes a solution
            run_script = f"""
import sys
sys.path.insert(0, '{tmpdir}')
from agent import solve
result = solve('''{task.description}''', '''{task.initial_code}''')
with open('{tmpdir}/solution.py', 'w') as f:
    f.write(result)
"""
            run_file = os.path.join(tmpdir, "run_agent.py")
            with open(run_file, "w") as f:
                f.write(run_script)
            
            agent_result = subprocess.run(
                ["python3", run_file],
                capture_output=True, text=True, timeout=timeout,
                cwd=tmpdir,
            )
            agent_output = agent_result.stdout + agent_result.stderr
        except subprocess.TimeoutExpired:
            return {"passed": False, "output": "", "error": "Agent timeout"}
        except Exception as e:
            return {"passed": False, "output": "", "error": str(e)}
        
        # Run tests
        try:
            test_result = subprocess.run(
                ["python3", "-m", "pytest", test_file, "-v", "--tb=short"],
                capture_output=True, text=True, timeout=timeout,
                cwd=tmpdir,
            )
            passed = test_result.returncode == 0
            return {
                "passed": passed,
                "output": agent_output,
                "test_output": test_result.stdout + test_result.stderr,
                "error": "" if passed else "Tests failed",
            }
        except subprocess.TimeoutExpired:
            return {"passed": False, "output": agent_output, "error": "Test timeout"}
        except Exception as e:
            return {"passed": False, "output": agent_output, "error": str(e)}


def evaluate_agent(agent: Agent, tasks: list[Task], timeout: int = 30) -> float:
    """Evaluate an agent on all tasks. Returns accuracy score."""
    resolved = []
    unresolved = []
    
    for task in tasks:
        result = evaluate_agent_on_task(agent.code, task, timeout)
        if result["passed"]:
            resolved.append(task.task_id)
        else:
            unresolved.append(task.task_id)
    
    agent.resolved_tasks = resolved
    agent.unresolved_tasks = unresolved
    agent.accuracy = len(resolved) / len(tasks) if tasks else 0.0
    
    return agent.accuracy


# ── DGM Loop ────────────────────────────────────────────────────────────

class DGMLoop:
    """Main Darwin Gödel Machine evolution loop."""
    
    def __init__(
        self,
        initial_agent_code: str,
        tasks: list[Task],
        output_dir: str = "results/dgm",
        max_generations: int = 20,
        children_per_gen: int = 2,
    ):
        self.tasks = tasks
        self.output_dir = output_dir
        self.max_generations = max_generations
        self.children_per_gen = children_per_gen
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize archive with initial agent
        initial = Agent(
            agent_id="initial",
            parent_id=None,
            generation=0,
            code=initial_agent_code,
        )
        evaluate_agent(initial, tasks)
        self.archive: list[Agent] = [initial]
        
        self._log(f"Initial agent accuracy: {initial.accuracy:.2%}")
        self._save_state(0)
    
    def _log(self, msg: str):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {msg}"
        print(line)
        with open(os.path.join(self.output_dir, "dgm.log"), "a") as f:
            f.write(line + "\n")
    
    def _save_state(self, generation: int):
        state = {
            "generation": generation,
            "archive_size": len(self.archive),
            "best_accuracy": max(a.accuracy for a in self.archive),
            "agents": [
                {
                    "agent_id": a.agent_id,
                    "parent_id": a.parent_id,
                    "generation": a.generation,
                    "accuracy": a.accuracy,
                    "children_count": a.children_count,
                    "resolved": len(a.resolved_tasks),
                    "unresolved": len(a.unresolved_tasks),
                }
                for a in self.archive
            ],
        }
        with open(os.path.join(self.output_dir, "state.json"), "w") as f:
            json.dump(state, f, indent=2)
        
        # Append to history
        with open(os.path.join(self.output_dir, "history.jsonl"), "a") as f:
            f.write(json.dumps(state) + "\n")
    
    def _save_agent(self, agent: Agent):
        agent_dir = os.path.join(self.output_dir, "agents", agent.agent_id)
        os.makedirs(agent_dir, exist_ok=True)
        with open(os.path.join(agent_dir, "agent.py"), "w") as f:
            f.write(agent.code)
        with open(os.path.join(agent_dir, "metadata.json"), "w") as f:
            json.dump({
                "agent_id": agent.agent_id,
                "parent_id": agent.parent_id,
                "generation": agent.generation,
                "accuracy": agent.accuracy,
                "resolved_tasks": agent.resolved_tasks,
                "unresolved_tasks": agent.unresolved_tasks,
                "diagnosis": agent.diagnosis,
                "created_at": agent.created_at,
            }, f, indent=2)
    
    def run_generation(self, gen_num: int):
        """Run one generation of the DGM loop."""
        self._log(f"=== Generation {gen_num} ===")
        
        # Select parents
        parents = score_child_prop_select(self.archive, k=self.children_per_gen)
        
        for i, parent in enumerate(parents):
            child_id = f"gen{gen_num}_{i}_{datetime.datetime.now().strftime('%H%M%S')}"
            self._log(f"Parent: {parent.agent_id} (acc={parent.accuracy:.2%}, children={parent.children_count})")
            
            # Pick an unresolved task to diagnose
            if parent.unresolved_tasks:
                task_id = random.choice(parent.unresolved_tasks)
            else:
                # Parent solves everything — pick random task
                task_id = random.choice([t.task_id for t in self.tasks])
            
            task = next(t for t in self.tasks if t.task_id == task_id)
            
            # Re-evaluate parent on this task to get output
            eval_result = evaluate_agent_on_task(parent.code, task)
            
            # Diagnose
            self._log(f"Diagnosing failure on task {task_id}...")
            diagnosis = diagnose(
                parent, task,
                agent_output=eval_result.get("output", ""),
                test_results=eval_result.get("test_output", eval_result.get("error", "")),
            )
            
            if not diagnosis:
                self._log(f"Diagnosis failed for {child_id}, skipping")
                continue
            
            self._log(f"Diagnosis: {diagnosis.get('root_cause', 'unknown')[:100]}")
            
            # Mutate
            self._log(f"Mutating agent...")
            new_code = mutate(parent, diagnosis)
            
            if not new_code:
                self._log(f"Mutation failed for {child_id}, skipping")
                continue
            
            # Create child agent
            child = Agent(
                agent_id=child_id,
                parent_id=parent.agent_id,
                generation=gen_num,
                code=new_code,
                diagnosis=json.dumps(diagnosis),
            )
            
            # Evaluate child
            self._log(f"Evaluating child {child_id}...")
            evaluate_agent(child, self.tasks)
            self._log(f"Child accuracy: {child.accuracy:.2%} (parent: {parent.accuracy:.2%})")
            
            # Gating: add to archive if it compiles and runs
            # (DGM keeps everything that compiles; we can be stricter later)
            if child.accuracy >= 0:  # Always add if it ran
                self.archive.append(child)
                parent.children_count += 1
                self._save_agent(child)
                self._log(f"Added {child_id} to archive (size={len(self.archive)})")
            else:
                self._log(f"Rejected {child_id}")
        
        best = max(self.archive, key=lambda a: a.accuracy)
        self._log(f"Best in archive: {best.agent_id} ({best.accuracy:.2%})")
        self._save_state(gen_num)
    
    def run(self):
        """Run the full DGM loop."""
        self._log(f"Starting DGM loop: {self.max_generations} generations, {self.children_per_gen} children/gen")
        
        for gen in range(1, self.max_generations + 1):
            self.run_generation(gen)
        
        best = max(self.archive, key=lambda a: a.accuracy)
        self._log(f"=== DGM Complete ===")
        self._log(f"Archive size: {len(self.archive)}")
        self._log(f"Best agent: {best.agent_id} ({best.accuracy:.2%})")
        return best
