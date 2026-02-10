"""
DGM Main Loop - Darwin Gödel Machine evolution loop.
Replicates Sakana's DGM with local LLM.
"""
import json
import os
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path

from .llm import create_client
from .selection import score_child_prop, random_selection
from .diagnose import diagnose_failure, implement_improvement
from .benchmark import load_task, setup_task_workspace, evaluate_task, get_task_ids
from .coding_agent import CodingAgent, get_default_agent_code, load_agent_from_code


class Archive:
    """Manages the population archive of agent variants."""
    
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.entries = []  # list of {id, code, score, children_count, parent_id, ...}
        self._state_file = self.output_dir / "archive.json"
        self._load()
    
    def _load(self):
        if self._state_file.exists():
            with open(self._state_file) as f:
                data = json.load(f)
                self.entries = data.get("entries", [])
    
    def _save(self):
        with open(self._state_file, "w") as f:
            json.dump({"entries": self.entries}, f, indent=2)
    
    def add(self, entry_id, code, score, parent_id=None, metadata=None):
        entry = {
            "id": entry_id,
            "score": score,
            "parent_id": parent_id,
            "children_count": 0,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        # Save code to file
        code_file = self.output_dir / f"{entry_id}_agent.py"
        code_file.write_text(code)
        entry["code_file"] = str(code_file)
        
        self.entries.append(entry)
        
        # Update parent's children count
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
                code_file = e.get("code_file")
                if code_file and os.path.exists(code_file):
                    return Path(code_file).read_text()
        return None
    
    def get_best(self):
        if not self.entries:
            return None
        return max(self.entries, key=lambda e: e.get("score", 0))
    
    def get_for_selection(self):
        """Get entries formatted for selection functions."""
        return [
            {"id": e["id"], "score": e["score"], "children_count": e["children_count"]}
            for e in self.entries
            if e.get("score") is not None
        ]


class DGMLoop:
    """
    Main DGM evolution loop.
    
    1. Select parent from archive
    2. Pick a task the parent fails on
    3. Diagnose the failure
    4. Implement improvement
    5. Evaluate new agent
    6. If better → add to archive
    """
    
    def __init__(self, output_dir, task_ids=None, endpoint=None, model=None,
                 selection_method="score_child_prop", max_generations=20,
                 attempts_per_generation=2):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.task_ids = task_ids or get_task_ids()
        self.endpoint = endpoint
        self.model = model
        self.selection_method = selection_method
        self.max_generations = max_generations
        self.attempts_per_generation = attempts_per_generation
        
        self.archive = Archive(self.output_dir / "archive")
        self.client, self.model_name = create_client(endpoint=endpoint, model=model)
        
        # Log file
        self.log_file = self.output_dir / "dgm_log.jsonl"
    
    def _log(self, event):
        event["timestamp"] = datetime.now().isoformat()
        with open(self.log_file, "a") as f:
            f.write(json.dumps(event) + "\n")
        print(f"[DGM] {event.get('type', 'unknown')}: {event.get('message', '')}")
    
    def _evaluate_agent_code(self, agent_code):
        """Evaluate agent code on all tasks. Returns {task_id: result}, overall_score."""
        results = {}
        total_score = 0.0
        
        for task_id in self.task_ids:
            task = load_task(task_id)
            
            with tempfile.TemporaryDirectory() as tmpdir:
                workspace = Path(tmpdir)
                setup_task_workspace(task, workspace)
                
                # Create agent from code
                try:
                    agent = CodingAgent(
                        system_prompt=self._extract_system_prompt(agent_code),
                        endpoint=self.endpoint,
                        model=self.model,
                    )
                    
                    # Run agent on task
                    agent.forward(task["description"], str(workspace), task.get("test_file", "test_solution.py"))
                    
                    # Evaluate
                    result = evaluate_task(workspace, task)
                    result["agent_log"] = agent.get_log_text()
                    
                    # Read agent's solution
                    sol_file = workspace / task.get("code_file", "solution.py")
                    result["agent_solution"] = sol_file.read_text() if sol_file.exists() else ""
                    
                except Exception as e:
                    result = {
                        "passed": 0, "failed": 0, "total": 0,
                        "score": 0.0, "output": f"Agent error: {e}",
                        "agent_log": "", "agent_solution": "",
                    }
                
                results[task_id] = result
                total_score += result["score"]
        
        overall_score = total_score / len(self.task_ids) if self.task_ids else 0.0
        return results, overall_score
    
    def _extract_system_prompt(self, agent_code):
        """Extract AGENT_SYSTEM_PROMPT from agent code."""
        # Find the system prompt string in the code
        import re
        # Look for AGENT_SYSTEM_PROMPT = """..."""
        match = re.search(r'AGENT_SYSTEM_PROMPT\s*=\s*"""(.*?)"""', agent_code, re.DOTALL)
        if match:
            return match.group(1)
        match = re.search(r"AGENT_SYSTEM_PROMPT\s*=\s*'''(.*?)'''", agent_code, re.DOTALL)
        if match:
            return match.group(1)
        # Fallback to default
        from .coding_agent import AGENT_SYSTEM_PROMPT
        return AGENT_SYSTEM_PROMPT
    
    def _find_failed_task(self, results):
        """Find a task the agent failed on (for diagnosis)."""
        failed = [(tid, r) for tid, r in results.items() if r["score"] < 1.0]
        if not failed:
            return None, None
        # Prefer partially solved over completely failed
        failed.sort(key=lambda x: x[1]["score"], reverse=True)
        # Pick one (prefer tasks with some progress)
        import random
        if len(failed) > 1 and failed[0][1]["score"] > 0:
            return failed[0]
        return random.choice(failed)
    
    def initialize(self):
        """Initialize archive with the default agent."""
        if self.archive.entries:
            self._log({"type": "init", "message": f"Archive already has {len(self.archive.entries)} entries"})
            return
        
        self._log({"type": "init", "message": "Evaluating initial agent..."})
        
        initial_code = get_default_agent_code()
        results, score = self._evaluate_agent_code(initial_code)
        
        self.archive.add("initial", initial_code, score, metadata={
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
        """Run one generation of evolution."""
        self._log({"type": "gen_start", "message": f"Generation {gen_num}"})
        
        new_entries = []
        
        for attempt in range(self.attempts_per_generation):
            attempt_id = f"gen{gen_num}_attempt{attempt}"
            self._log({"type": "attempt_start", "message": f"Attempt {attempt_id}"})
            
            # 1. Select parent
            archive_for_selection = self.archive.get_for_selection()
            if self.selection_method == "score_child_prop":
                parent_ids = score_child_prop(archive_for_selection, k=1)
            else:
                parent_ids = random_selection(archive_for_selection, k=1)
            
            parent_id = parent_ids[0]
            parent_code = self.archive.get_code(parent_id)
            
            self._log({"type": "parent_selected", "message": f"Parent: {parent_id}"})
            
            # 2. Evaluate parent to find failed tasks
            results, parent_score = self._evaluate_agent_code(parent_code)
            
            # 3. Find a failed task
            failed_task_id, failed_result = self._find_failed_task(results)
            if not failed_task_id:
                self._log({"type": "skip", "message": "Parent passes all tasks!"})
                continue
            
            task = load_task(failed_task_id)
            
            self._log({"type": "diagnosing", "message": f"Diagnosing failure on {failed_task_id}"})
            
            # 4. Diagnose the failure
            diagnosis = diagnose_failure(
                self.client, self.model_name,
                agent_code=parent_code,
                task_description=task["description"],
                agent_log=failed_result.get("agent_log", "No log"),
                test_results=failed_result.get("output", "No output"),
                agent_solution=failed_result.get("agent_solution", "No solution"),
            )
            
            if not diagnosis:
                self._log({"type": "diagnosis_failed", "message": "Failed to diagnose"})
                continue
            
            self._log({
                "type": "diagnosis_done",
                "message": diagnosis.get("chosen_improvement", "?")[:200],
            })
            
            # 5. Implement the improvement
            new_code = implement_improvement(
                self.client, self.model_name,
                agent_code=parent_code,
                improvement_description=diagnosis.get("chosen_improvement", ""),
                implementation_plan=diagnosis.get("implementation_plan", ""),
            )
            
            if not new_code:
                self._log({"type": "impl_failed", "message": "Failed to implement improvement"})
                continue
            
            self._log({"type": "impl_done", "message": f"New agent code: {len(new_code)} chars"})
            
            # 6. Evaluate new agent
            new_results, new_score = self._evaluate_agent_code(new_code)
            
            self._log({
                "type": "eval_done",
                "message": f"New score: {new_score:.3f} (parent: {parent_score:.3f})",
                "new_score": new_score,
                "parent_score": parent_score,
            })
            
            # 7. Gating: add to archive if it compiles and runs
            # DGM uses keep_all by default, so we add everything that compiles
            entry_id = f"gen{gen_num}_{attempt}"
            self.archive.add(entry_id, new_code, new_score, parent_id=parent_id, metadata={
                "diagnosis": diagnosis,
                "parent_score": parent_score,
                "results": {k: {"score": v["score"], "passed": v["passed"], "total": v["total"]}
                           for k, v in new_results.items()},
            })
            
            new_entries.append(entry_id)
            
            improved = "✅ IMPROVED" if new_score > parent_score else "❌ no improvement"
            self._log({
                "type": "archived",
                "message": f"{entry_id}: {new_score:.3f} ({improved})",
            })
        
        # Generation summary
        best = self.archive.get_best()
        self._log({
            "type": "gen_done",
            "message": f"Gen {gen_num} done. Archive size: {len(self.archive.entries)}. Best: {best['score']:.3f}" if best else "Gen done",
            "archive_size": len(self.archive.entries),
            "best_score": best["score"] if best else None,
            "new_entries": new_entries,
        })
    
    def run(self):
        """Run the full DGM loop."""
        self._log({"type": "start", "message": f"Starting DGM with {len(self.task_ids)} tasks, {self.max_generations} generations"})
        
        self.initialize()
        
        for gen in range(self.max_generations):
            try:
                self.run_generation(gen)
            except Exception as e:
                self._log({"type": "error", "message": f"Generation {gen} failed: {e}"})
                import traceback
                traceback.print_exc()
        
        # Final summary
        best = self.archive.get_best()
        initial = next((e for e in self.archive.entries if e["id"] == "initial"), None)
        
        self._log({
            "type": "finished",
            "message": f"DGM complete. Initial: {initial['score']:.3f}, Best: {best['score']:.3f}, Archive: {len(self.archive.entries)}",
            "initial_score": initial["score"] if initial else None,
            "best_score": best["score"] if best else None,
            "best_id": best["id"] if best else None,
            "archive_size": len(self.archive.entries),
        })
