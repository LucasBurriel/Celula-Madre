#!/usr/bin/env python3
"""Run DGM V2 - Code evolution with dual models."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.dgm_core.dgm_loop_v2 import DGMLoopV2

ENDPOINT = os.environ.get("LM_STUDIO_URL", "http://172.17.0.1:1234/v1")
TASK_IDS = ["regex_engine", "json_parser", "task_scheduler"]
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "results", "dgm_v2_code_evo")

if __name__ == "__main__":
    loop = DGMLoopV2(
        output_dir=OUTPUT_DIR,
        task_ids=TASK_IDS,
        endpoint=ENDPOINT,
        agent_model="google/gemma-3-4b",
        diagnose_model="qwen3-coder-30b-a3b-instruct",
        max_generations=10,
        attempts_per_generation=2,
    )
    loop.run()
