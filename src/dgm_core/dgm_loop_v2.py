"""
DGM Loop V2 - Faithful replication of Darwin Gödel Machine.

Key differences from V1:
- Evolves the FULL agent code (not just system prompt)
- Uses strong model (Qwen) for diagnosis + implementation
- Uses weak model (Gemma) for agent execution
- Agents are self-contained Python files with forward() entry point
"""
import json
import os
import re
import shutil
import tempfile
import time
import traceback
from datetime import datetime
from pathlib import Path

from .llm import create_client, chat, MAX_TOKENS
from .benchmark import load_task, setup_task_workspace, evaluate_task, get_task_ids
from .selection import score_child_prop, random_selection


# Default models
DIAGNOSE_MODEL = os.environ.get("DGM_DIAGNOSE_MODEL", "qwen3-coder-30b-a3b-instruct")
AGENT_MODEL = os.environ.get("DGM_AGENT_MODEL", "google/gemma-3-4b")

# Read initial agent template
INITIAL_AGENT_CODE = (Path(__file__).parent / "agent_template.py").read_text()


class Archive:
    """Population archive - stores all agent variants."""
    
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.entries = []
        self._state_file = self.output_dir / "archive.json"
        self._load()
    
    def _load(self):
        if self._state_file.exists():
            with open(self._state_file) as f:
                self.entries = json.load(f).get("entries", [])
    
    def _save(self):
        with open(self._state_file, "w") as f:
            json.dump({"entries": self.entries}, f, indent=2)
    
    def add(self, entry_id, code, score, parent_id=None, metadata=None):
        code_file = self.output_dir / f"{entry_id}_agent.py"
        code_file.write_text(code)
        
        entry = {
            "id": entry_id,
            "code_file": str(code_file),
            "score": score,
            "parent_id": parent_id,
            "children_count": 0,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        self.entries.append(entry)
        
        if parent_id:
            for e in self.entries:
                if e["id"] == parent_id:
                    e["children_count"] += 1
                    break
        
        self._save()
        return entry
    
    def get_code(self, entry_id):
        for e in self.entries:
            if e["id"] == entry_id:
                cf = e.get("code_file")
                if cf and os.path.exists(cf):
                    return Path(cf).read_text()
        return None
    
    def get_best(self):
        return max(self.entries, key=lambda e: e.get("score", 0)) if self.entries else None
    
    def get_for_selection(self):
        return [
            {"id": e["id"], "score": e["score"], "children_count": e["children_count"]}
            for e in self.entries if e.get("score") is not None
        ]


def execute_agent(agent_code, task, agent_model=AGENT_MODEL, endpoint=None):
    """
    Execute an agent (Python code) on a task.
    The agent code defines forward() which we call.
    Returns evaluation result dict.
    """
    client, model = create_client(endpoint=endpoint, model=agent_model)
    
    def llm_call(system_prompt, user_message):
        return chat(client, model, system_prompt, user_message, temperature=0.7)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        setup_task_workspace(task, workspace)
        
        try:
            # Execute agent code in isolated namespace
            namespace = {}
            exec(agent_code, namespace)
            
            forward_fn = namespace.get("forward")
            if not forward_fn:
                return {
                    "passed": 0, "failed": 0, "total": 0,
                    "score": 0.0, "output": "No forward() function found",
                    "agent_log": "", "agent_solution": "",
                }
            
            # Run agent
            result = forward_fn(
                task_description=task["description"],
                workspace_dir=str(workspace),
                test_file=task.get("test_file", "test_solution.py"),
                llm_call=llm_call,
            )
            
            # Evaluate
            eval_result = evaluate_task(workspace, task)
            eval_result["agent_log"] = "\n".join(result.get("log", []))
            eval_result["agent_solution"] = result.get("solution", "")
            return eval_result
            
        except Exception as e:
            return {
                "passed": 0, "failed": 0, "total": 0,
                "score": 0.0, "output": f"Agent execution error: {e}\n{traceback.format_exc()[:500]}",
                "agent_log": "", "agent_solution": "",
            }


# ============================================================
# Diagnosis prompts - closely following DGM original
# ============================================================

DIAGNOSE_SYSTEM = """You are an expert software engineer analyzing a coding agent's performance.
The agent is a Python program with a forward() function that solves coding tasks using an LLM.

Your task: analyze the agent's failure and propose ONE concrete improvement to the agent's CODE
that would help it solve tasks better. The improvement should be GENERAL (help across many tasks).

The agent can be improved by:
- Modifying the system prompt (SYSTEM_PROMPT variable)
- Changing the forward() logic (e.g., add retry, chain-of-thought, decomposition)
- Adding helper functions
- Changing how code is extracted or tested"""

DIAGNOSE_PROMPT = """# Agent's Source Code
----- Agent Code Start -----
{agent_code}
----- Agent Code End -----

# Task Description
{task_description}

# Agent's Log
----- Log Start -----
{agent_log}
----- Log End -----

# Test Results
----- Test Results Start -----
{test_results}
----- Test Results End -----

# Agent's Solution Code
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
    "implementation_plan": "Specific code changes to make",
    "problem_description": "Describe the improvement as a GitHub issue"
}}
```"""

IMPLEMENT_SYSTEM = """You are an expert Python developer. You will receive a coding agent's source code
and a description of an improvement to implement. Modify the agent's code to implement the improvement.

RULES:
- Output the COMPLETE modified agent source code
- The code must define a forward() function as the entry point
- The forward() function signature must be: forward(task_description, workspace_dir, test_file, llm_call)
- llm_call is a function: llm_call(system_prompt, user_message) -> str
- Keep all imports at the top
- The code must be self-contained (no external dependencies except stdlib + subprocess)
- Wrap your code in ```python ... ```

DO NOT remove existing functionality unless replacing it with something better."""

IMPLEMENT_PROMPT = """# Current Agent Code
```python
{agent_code}
```

# Improvement to Implement
{improvement_description}

# Implementation Plan
{implementation_plan}

Output the COMPLETE modified agent code. It must be valid Python with a forward() function."""


def diagnose_failure(client, model, agent_code, task_description, agent_log,
                     test_results, agent_solution, max_attempts=2):
    """Use strong model to diagnose agent failure."""
    from .llm import extract_json
    
    prompt = DIAGNOSE_PROMPT.format(
        agent_code=agent_code,
        task_description=task_description,
        agent_log=agent_log[:2000],
        test_results=test_results[:2000],
        agent_solution=agent_solution[:1500],
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


def implement_improvement(client, model, agent_code, improvement_description,
                         implementation_plan, max_attempts=2):
    """Use strong model to implement code improvement."""
    prompt = IMPLEMENT_PROMPT.format(
        agent_code=agent_code,
        improvement_description=improvement_description,
        implementation_plan=implementation_plan,
    )
    
    for attempt in range(max_attempts):
        try:
            response = chat(client, model, IMPLEMENT_SYSTEM, prompt,
                          temperature=0.5, max_tokens=4096)
            
            # Extract code
            pattern = r'```python\s*\n(.*?)\n```'
            matches = re.findall(pattern, response, re.DOTALL)
            
            if matches:
                new_code = max(matches, key=len)
                # Validate it has forward()
                if "def forward" in new_code:
                    # Quick syntax check
                    try:
                        compile(new_code, "<agent>", "exec")
                        return new_code
                    except SyntaxError:
                        continue
        except Exception as e:
            if attempt == max_attempts - 1:
                return None
    return None


class DGMLoopV2:
    """
    DGM Evolution Loop V2 - faithful replication.
    
    Uses:
    - Strong model (Qwen) for diagnosis + implementation
    - Weak model (Gemma) for agent execution
    - Full code evolution (not just prompts)
    """
    
    def __init__(self, output_dir, task_ids=None, endpoint=None,
                 agent_model=None, diagnose_model=None,
                 selection_method="score_child_prop",
                 max_generations=20, attempts_per_generation=2):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.task_ids = task_ids or get_task_ids()
        self.endpoint = endpoint
        self.agent_model = agent_model or AGENT_MODEL
        self.diagnose_model = diagnose_model or DIAGNOSE_MODEL
        self.selection_method = selection_method
        self.max_generations = max_generations
        self.attempts_per_generation = attempts_per_generation
        
        self.archive = Archive(self.output_dir / "archive")
        # Strong model client for diagnosis
        self.diag_client, self.diag_model = create_client(
            endpoint=endpoint, model=self.diagnose_model
        )
        
        self.log_file = self.output_dir / "dgm_log.jsonl"
    
    def _log(self, event):
        event["timestamp"] = datetime.now().isoformat()
        with open(self.log_file, "a") as f:
            f.write(json.dumps(event) + "\n")
        # Also print
        msg = event.get("message", "")
        print(f"[{event.get('type', '?')}] {msg}", flush=True)
    
    def _evaluate_agent(self, agent_code):
        """Evaluate agent on all tasks. Returns {task_id: result}, score."""
        results = {}
        total = 0.0
        
        for tid in self.task_ids:
            task = load_task(tid)
            result = execute_agent(
                agent_code, task,
                agent_model=self.agent_model,
                endpoint=self.endpoint,
            )
            results[tid] = result
            total += result["score"]
        
        score = total / len(self.task_ids) if self.task_ids else 0.0
        return results, score
    
    def _find_failed_task(self, results):
        """Find a task the agent failed on."""
        import random
        failed = [(tid, r) for tid, r in results.items() if r["score"] < 1.0]
        if not failed:
            return None, None
        # Prefer partially solved (more diagnostic info)
        failed.sort(key=lambda x: x[1]["score"], reverse=True)
        if len(failed) > 1 and failed[0][1]["score"] > 0:
            return failed[0]
        return random.choice(failed)
    
    def initialize(self):
        """Add initial agent to archive."""
        if self.archive.entries:
            self._log({"type": "init", "message": f"Archive has {len(self.archive.entries)} entries"})
            return
        
        self._log({"type": "init", "message": "Evaluating initial agent..."})
        results, score = self._evaluate_agent(INITIAL_AGENT_CODE)
        
        self.archive.add("initial", INITIAL_AGENT_CODE, score, metadata={
            "results": {k: {"score": v["score"], "passed": v["passed"], "total": v["total"]}
                       for k, v in results.items()},
        })
        
        self._log({
            "type": "init_done",
            "message": f"Initial agent score: {score:.3f}",
            "score": score,
            "task_results": {k: v["score"] for k, v in results.items()},
        })
    
    def run_generation(self, gen_num):
        """Run one generation."""
        self._log({"type": "gen_start", "message": f"Generation {gen_num}"})
        new_entries = []
        
        for attempt in range(self.attempts_per_generation):
            attempt_id = f"gen{gen_num}_a{attempt}"
            self._log({"type": "attempt_start", "message": attempt_id})
            
            # 1. Select parent
            candidates = self.archive.get_for_selection()
            if self.selection_method == "score_child_prop":
                parent_ids = score_child_prop(candidates, k=1)
            else:
                parent_ids = random_selection(candidates, k=1)
            
            parent_id = parent_ids[0]
            parent_code = self.archive.get_code(parent_id)
            self._log({"type": "parent", "message": f"Parent: {parent_id}"})
            
            # 2. Evaluate parent to find failures
            results, parent_score = self._evaluate_agent(parent_code)
            self._log({"type": "parent_eval", "message": f"Parent score: {parent_score:.3f}"})
            
            # 3. Pick failed task
            failed_tid, failed_result = self._find_failed_task(results)
            if not failed_tid:
                self._log({"type": "skip", "message": "Parent passes all tasks!"})
                continue
            
            task = load_task(failed_tid)
            self._log({"type": "diagnosing", "message": f"Failed task: {failed_tid}"})
            
            # 4. Diagnose (strong model)
            diagnosis = diagnose_failure(
                self.diag_client, self.diag_model,
                agent_code=parent_code,
                task_description=task["description"],
                agent_log=failed_result.get("agent_log", ""),
                test_results=failed_result.get("output", "")[:2000],
                agent_solution=failed_result.get("agent_solution", ""),
            )
            
            if not diagnosis:
                self._log({"type": "diag_failed", "message": "Diagnosis failed"})
                continue
            
            self._log({
                "type": "diagnosed",
                "message": diagnosis.get("chosen_improvement", "?")[:200],
            })
            
            # 5. Implement improvement (strong model)
            new_code = implement_improvement(
                self.diag_client, self.diag_model,
                agent_code=parent_code,
                improvement_description=diagnosis.get("chosen_improvement", ""),
                implementation_plan=diagnosis.get("implementation_plan", ""),
            )
            
            if not new_code:
                self._log({"type": "impl_failed", "message": "Implementation failed"})
                continue
            
            self._log({"type": "implemented", "message": f"New code: {len(new_code)} chars"})
            
            # 6. Evaluate new agent (weak model)
            new_results, new_score = self._evaluate_agent(new_code)
            
            improved = new_score > parent_score
            self._log({
                "type": "evaluated",
                "message": f"Score: {new_score:.3f} (parent: {parent_score:.3f}) {'✅' if improved else '❌'}",
                "new_score": new_score,
                "parent_score": parent_score,
            })
            
            # 7. Archive (keep_all - same as DGM)
            self.archive.add(attempt_id, new_code, new_score, parent_id=parent_id, metadata={
                "diagnosis": diagnosis,
                "parent_score": parent_score,
                "improved": improved,
                "results": {k: {"score": v["score"], "passed": v["passed"], "total": v["total"]}
                           for k, v in new_results.items()},
            })
            new_entries.append(attempt_id)
        
        best = self.archive.get_best()
        self._log({
            "type": "gen_done",
            "message": f"Gen {gen_num} done. Archive: {len(self.archive.entries)}. Best: {best['score']:.3f}" if best else "done",
            "archive_size": len(self.archive.entries),
            "best_score": best["score"] if best else None,
        })
    
    def run(self):
        """Run full DGM evolution."""
        self._log({
            "type": "start",
            "message": f"DGM V2: {len(self.task_ids)} tasks, {self.max_generations} gens, "
                       f"agent={self.agent_model}, diagnose={self.diagnose_model}",
        })
        
        self.initialize()
        
        for gen in range(self.max_generations):
            try:
                self.run_generation(gen)
            except Exception as e:
                self._log({"type": "error", "message": f"Gen {gen} error: {e}"})
                traceback.print_exc()
        
        best = self.archive.get_best()
        initial = next((e for e in self.archive.entries if e["id"] == "initial"), None)
        
        self._log({
            "type": "finished",
            "message": f"Done. Initial: {initial['score']:.3f}, Best: {best['score']:.3f} ({best['id']})",
            "initial_score": initial["score"] if initial else None,
            "best_score": best["score"] if best else None,
            "best_id": best["id"] if best else None,
            "archive_size": len(self.archive.entries),
        })
