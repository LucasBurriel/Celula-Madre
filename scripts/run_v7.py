"""Run V7 evolution experiments.

Usage:
  python3 scripts/run_v7.py --group A --run 1        # Single run
  python3 scripts/run_v7.py --all                     # All 12 runs
  python3 scripts/run_v7.py --group A --run 1 --resume  # Resume from checkpoint
"""

import argparse
import os
import sys
import time

sys.path.insert(0, ".")

from src.negotiation import generate_splits, save_scenarios, load_scenarios
from src.evolution_v7 import EvolutionEngineV7

# Group → mode mapping
GROUPS = {
    "A": "tournament_reflective",
    "B": "market_random",
    "C": "market_reflective",
    "D": "tournament_random",
}

GROUP_NAMES = {
    "A": "Tournament × Reflective",
    "B": "Market × Random",
    "C": "Market × Reflective (Full CM)",
    "D": "Tournament × Random (Control)",
}


def ensure_scenarios():
    path = "data/v7_scenarios.json"
    if not os.path.exists(path):
        print("Generating scenarios...")
        splits = generate_splits(seed=42)
        save_scenarios(splits, path)
    return load_scenarios(path)


def run_single(group: str, run_num: int, resume: bool = False):
    mode = GROUPS[group]
    results_dir = f"results/v7/{group}_{mode}/run_{run_num}"

    print(f"\n{'#'*60}")
    print(f"V7 Experiment: Group {group} ({GROUP_NAMES[group]})")
    print(f"Run {run_num} | Mode: {mode}")
    print(f"Results: {results_dir}")
    print(f"{'#'*60}")

    scenarios = ensure_scenarios()

    engine = EvolutionEngineV7(
        mode=mode,
        population_size=8,
        num_generations=10,
        elite_count=2,
        tournament_k=3,
        dev_scenarios=60,
        val_scenarios=60,
        max_turns=5,
        results_dir=results_dir,
    )

    start = time.time()
    results = engine.run(scenarios, resume=resume)
    elapsed = (time.time() - start) / 60

    print(f"\n⏱️ Completed in {elapsed:.1f} minutes")
    print(f"📊 Test score: {results['test_accuracy']:.2%}")
    return results


def run_all(resume: bool = False):
    for group in ["A", "B", "C", "D"]:
        for run_num in range(1, 4):
            results_path = f"results/v7/{group}_{GROUPS[group]}/run_{run_num}/results.json"
            if os.path.exists(results_path) and not resume:
                print(f"Skipping Group {group} Run {run_num} (already complete)")
                continue
            try:
                run_single(group, run_num, resume=resume)
            except Exception as e:
                print(f"ERROR in Group {group} Run {run_num}: {e}")
                continue


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run V7 experiments")
    parser.add_argument("--group", choices=["A", "B", "C", "D"])
    parser.add_argument("--run", type=int, choices=[1, 2, 3])
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    if args.all:
        run_all(resume=args.resume)
    elif args.group and args.run:
        run_single(args.group, args.run, resume=args.resume)
    else:
        parser.print_help()
