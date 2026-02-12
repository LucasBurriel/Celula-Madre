#!/usr/bin/env python3
"""Run DGM V2 - faithful Darwin Gödel Machine replication."""

import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dgm_core.dgm_loop_v2 import DGMLoopV2


def main():
    parser = argparse.ArgumentParser(description="Run DGM V2 Evolution")
    parser.add_argument("--output-dir", default="results/dgm_v2", help="Output directory")
    parser.add_argument("--generations", type=int, default=10)
    parser.add_argument("--children", type=int, default=2)
    parser.add_argument("--tasks", nargs="*", help="Specific task IDs")
    parser.add_argument("--agent-model", default="google/gemma-3-4b")
    parser.add_argument("--diagnose-model", default="qwen3-coder-30b-a3b-instruct")
    args = parser.parse_args()

    # Quick LLM test
    from dgm_core.llm import create_client, chat
    print("Testing diagnosis model (Qwen)...", flush=True)
    c, m = create_client(model=args.diagnose_model)
    r = chat(c, m, "You are helpful.", "Say 'ready'", max_tokens=10)
    print(f"  Qwen: {r.strip()}", flush=True)
    
    print("Testing agent model (Gemma)...", flush=True)
    c, m = create_client(model=args.agent_model)
    r = chat(c, m, "You are helpful.", "Say 'ready'", max_tokens=10)
    print(f"  Gemma: {r.strip()}", flush=True)

    dgm = DGMLoopV2(
        output_dir=args.output_dir,
        task_ids=args.tasks,
        agent_model=args.agent_model,
        diagnose_model=args.diagnose_model,
        max_generations=args.generations,
        attempts_per_generation=args.children,
    )
    dgm.run()


if __name__ == "__main__":
    main()
