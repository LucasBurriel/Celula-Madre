#!/usr/bin/env python3
"""
Célula Madre V6 — 3-Group Experiment Runner

Usage:
  python scripts/run_v6.py --mode reflective --run 1
  python scripts/run_v6.py --mode random --run 1
  python scripts/run_v6.py --mode static --run 1
  python scripts/run_v6.py --all  # Run all 15 experiments sequentially

Each run saves results + checkpoints to results/v6/<mode>/run_<N>/
"""

import argparse
import json
import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ag_news_data import load_splits
from src.evolution_v6 import EvolutionEngineV6, V6Config, SEED_STRATEGIES


RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "v6")


def run_single(mode: str, run_num: int, resume: bool = False):
    """Run a single experiment."""
    print(f"\n{'#'*60}")
    print(f"# V6 Experiment: {mode.upper()} — Run {run_num}")
    print(f"{'#'*60}\n")

    # Load data
    splits = load_splits()
    dev = splits["dev"]
    val = splits["val"]
    test = splits["test"]
    print(f"Data: dev={len(dev)}, val={len(val)}, test={len(test)}")

    # Setup dirs
    run_dir = os.path.join(RESULTS_DIR, mode, f"run_{run_num}")
    checkpoint_dir = os.path.join(run_dir, "checkpoints")
    os.makedirs(checkpoint_dir, exist_ok=True)

    # Resume?
    resume_path = None
    if resume:
        latest = os.path.join(checkpoint_dir, "checkpoint_latest.json")
        if os.path.exists(latest):
            resume_path = latest
            print(f"Resuming from {latest}")

    # Config
    config = V6Config(
        population_size=8,
        max_generations=10,
        elitism_count=2,
        fresh_injection=1,
        mutation_mode=mode,
    )

    # Run
    engine = EvolutionEngineV6(config)
    start = time.time()
    results = engine.run(
        dev_examples=dev,
        val_examples=val,
        test_examples=test,
        seed_strategies=SEED_STRATEGIES,
        checkpoint_dir=checkpoint_dir,
        resume_from=resume_path,
    )
    elapsed = time.time() - start

    results["run_num"] = run_num
    results["elapsed_seconds"] = round(elapsed, 1)
    results["elapsed_hours"] = round(elapsed / 3600, 2)

    # Save results
    results_file = os.path.join(run_dir, "results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ {mode.upper()} Run {run_num} complete in {elapsed/60:.1f} min")
    print(f"   Test accuracy: {results['test_accuracy']:.1%}")
    print(f"   Results: {results_file}")

    return results


def run_all():
    """Run all 15 experiments."""
    all_results = []
    modes = ["reflective", "random", "static"]
    runs_per_mode = 5

    for mode in modes:
        for run_num in range(1, runs_per_mode + 1):
            result = run_single(mode, run_num, resume=True)
            all_results.append(result)

            # Save aggregate after each run
            agg_file = os.path.join(RESULTS_DIR, "all_results.json")
            with open(agg_file, "w") as f:
                json.dump(all_results, f, indent=2)

    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for mode in modes:
        mode_results = [r for r in all_results if r["mode"] == mode]
        accs = [r["test_accuracy"] for r in mode_results]
        mean = sum(accs) / len(accs)
        print(f"{mode:12s}: mean_test={mean:.1%}  runs={[f'{a:.1%}' for a in accs]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Célula Madre V6 Experiment Runner")
    parser.add_argument("--mode", choices=["reflective", "random", "static"], help="Mutation mode")
    parser.add_argument("--run", type=int, default=1, help="Run number (1-5)")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--all", action="store_true", help="Run all 15 experiments")
    args = parser.parse_args()

    if args.all:
        run_all()
    elif args.mode:
        run_single(args.mode, args.run, args.resume)
    else:
        parser.print_help()
