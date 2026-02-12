"""V7 Minimal Runner — feasible scale for Qwen3-30B local.

Runs 2 key groups (A: tournament_reflective, D: tournament_random) with reduced params:
- pop=4, gens=5, dev=10, val=10, test=20, max_turns=3
- Estimated: ~3-4h per run, ~6-8h total for 2 runs

Usage:
  python3 scripts/run_v7_minimal.py --group A --run 1
  python3 scripts/run_v7_minimal.py --all
  python3 scripts/run_v7_minimal.py --all --resume
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, ".")

from src.negotiation import generate_splits, save_scenarios, load_scenarios, call_llm
from src.evolution_v7 import EvolutionEngineV7
from functools import partial

# Use gemma-3-4b for speed (4s vs 60s+ per call with Qwen3)
fast_llm = partial(call_llm, model="google/gemma-3-4b")

GROUPS = {
    "A": "tournament_reflective",
    "D": "tournament_random",
}

GROUP_NAMES = {
    "A": "Tournament × Reflective",
    "D": "Tournament × Random (Control)",
}

# Minimal but meaningful params
POP_SIZE = 4
NUM_GENS = 5
ELITE_COUNT = 1
DEV_SCENARIOS = 10
VAL_SCENARIOS = 10
MAX_TURNS = 3


def ensure_scenarios():
    path = "data/v7_scenarios.json"
    if not os.path.exists(path):
        print("Generating scenarios...")
        splits = generate_splits(seed=42)
        save_scenarios(splits, path)
    return load_scenarios(path)


def run_single(group: str, run_num: int, resume: bool = False):
    mode = GROUPS[group]
    results_dir = f"results/v7_minimal/{group}_{mode}/run_{run_num}"

    print(f"\n{'#'*60}", flush=True)
    print(f"V7 Minimal: Group {group} ({GROUP_NAMES[group]})", flush=True)
    print(f"Run {run_num} | Mode: {mode}", flush=True)
    print(f"Pop={POP_SIZE}, Gens={NUM_GENS}, Dev={DEV_SCENARIOS}, Val={VAL_SCENARIOS}, Turns={MAX_TURNS}", flush=True)
    print(f"Results: {results_dir}", flush=True)
    print(f"{'#'*60}", flush=True)

    scenarios = ensure_scenarios()

    engine = EvolutionEngineV7(
        mode=mode,
        population_size=POP_SIZE,
        num_generations=NUM_GENS,
        elite_count=ELITE_COUNT,
        tournament_k=2,
        dev_scenarios=DEV_SCENARIOS,
        val_scenarios=VAL_SCENARIOS,
        max_turns=MAX_TURNS,
        results_dir=results_dir,
        llm_fn=fast_llm,
    )

    start = time.time()
    results = engine.run(scenarios, resume=resume)
    elapsed = (time.time() - start) / 60

    print(f"\n⏱️ Completed in {elapsed:.1f} minutes", flush=True)
    print(f"📊 Test score: {results['test_accuracy']:.2%}", flush=True)
    return results


def run_all(resume: bool = False):
    all_results = {}
    for group in ["A", "D"]:
        for run_num in [1]:  # 1 run each for initial proof
            key = f"{group}_run{run_num}"
            results_path = f"results/v7_minimal/{group}_{GROUPS[group]}/run_{run_num}/results.json"
            if os.path.exists(results_path) and not resume:
                print(f"\n⏭️ Skipping {key} (already complete)")
                with open(results_path) as f:
                    all_results[key] = json.load(f)
                continue

            try:
                result = run_single(group, run_num, resume=resume)
                all_results[key] = result
            except Exception as e:
                print(f"\n❌ {key} failed: {e}", flush=True)
                all_results[key] = {"error": str(e)}

    # Summary
    print(f"\n{'='*60}", flush=True)
    print("SUMMARY", flush=True)
    print(f"{'='*60}", flush=True)
    for key, r in all_results.items():
        if "error" in r:
            print(f"  {key}: FAILED ({r['error']})")
        else:
            print(f"  {key}: test={r['test_accuracy']:.2%}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", choices=["A", "D"])
    parser.add_argument("--run", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    if args.all:
        run_all(resume=args.resume)
    elif args.group:
        run_single(args.group, args.run, resume=args.resume)
    else:
        parser.print_help()
