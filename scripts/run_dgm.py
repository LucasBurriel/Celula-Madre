#!/usr/bin/env python3
"""Run DGM (Darwin Gödel Machine) replication experiment."""

import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dgm_core.benchmark import get_task_ids, load_task, evaluate_task, setup_task_workspace
from dgm_core.dgm_loop import DGMLoop
from dgm_core.llm import create_client


def main():
    parser = argparse.ArgumentParser(description="Run DGM Evolution")
    parser.add_argument("--output-dir", default="results/dgm", help="Output directory")
    parser.add_argument("--generations", type=int, default=10)
    parser.add_argument("--children", type=int, default=2)
    parser.add_argument("--test-only", action="store_true", help="Test LLM + eval initial agent")
    parser.add_argument("--tasks", nargs="*", help="Specific task IDs (default: all)")
    parser.add_argument("--hard-only", action="store_true", help="Only use hard tasks")
    args = parser.parse_args()

    # Test LLM
    print("Testing LLM connection...")
    try:
        client, model = create_client()
        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=10,
        )
        print(f"LLM OK: {r.choices[0].message.content.strip()}")
    except Exception as e:
        print(f"LLM FAILED: {e}")
        sys.exit(1)

    # Get tasks
    all_tasks = get_task_ids()
    easy_tasks = {"calculator", "fizzbuzz", "linked_list", "lru_cache", "matrix_rotate"}
    
    if args.tasks:
        task_ids = args.tasks
    elif args.hard_only:
        task_ids = [t for t in all_tasks if t not in easy_tasks]
    else:
        task_ids = all_tasks
    
    print(f"Tasks ({len(task_ids)}): {task_ids}")

    if args.test_only:
        # Quick eval of initial agent
        from dgm_core.coding_agent import get_default_agent_code, CodingAgent
        import tempfile
        from pathlib import Path
        
        code = get_default_agent_code()
        total, passed_count = 0, 0
        for tid in task_ids:
            task = load_task(tid)
            with tempfile.TemporaryDirectory() as tmpdir:
                ws = Path(tmpdir)
                setup_task_workspace(task, ws)
                agent = CodingAgent(endpoint=None, model=None)
                try:
                    agent.forward(task["description"], str(ws), task.get("test_file", "test_solution.py"))
                    result = evaluate_task(ws, task)
                    status = "✅" if result["score"] >= 1.0 else f"❌ ({result['score']:.0%})"
                    if result["score"] >= 1.0:
                        passed_count += 1
                except Exception as e:
                    result = {"score": 0}
                    status = f"💥 {e}"
                total += 1
                print(f"  {tid}: {status}")
        
        print(f"\nInitial agent: {passed_count}/{total} tasks passed ({passed_count/total:.0%})")
        return

    # Run DGM
    dgm = DGMLoop(
        output_dir=args.output_dir,
        task_ids=task_ids,
        max_generations=args.generations,
        attempts_per_generation=args.children,
    )
    dgm.run()


if __name__ == "__main__":
    main()
