#!/usr/bin/env python3
"""
Célula Madre V6 — Quick Experiment Runner (reduced scale for feasibility)

Uses smaller eval sets and fewer generations to complete 15 runs in reasonable time.
"""

import argparse
import json
import os
import sys
import time
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ag_news_data import load_splits
from src.evolution_v6 import EvolutionEngineV6, V6Config, SEED_STRATEGIES

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "v6")


def subsample(examples, n, seed=None):
    """Balanced subsample: pick equal from each class."""
    if seed is not None:
        rng = random.Random(seed)
    else:
        rng = random.Random()
    by_class = {}
    for ex in examples:
        by_class.setdefault(ex["label"], []).append(ex)
    per_class = max(1, n // len(by_class))
    result = []
    for cls, items in by_class.items():
        result.extend(rng.sample(items, min(per_class, len(items))))
    rng.shuffle(result)
    return result[:n]


def run_single(mode: str, run_num: int):
    print(f"\n{'#'*60}", flush=True)
    print(f"# V6 Quick: {mode.upper()} — Run {run_num}", flush=True)
    print(f"{'#'*60}\n", flush=True)

    splits = load_splits()
    # Use smaller subsets but different seed per run for robustness
    dev = subsample(splits["dev"], 32, seed=run_num * 100 + 1)
    val = subsample(splits["val"], 32, seed=run_num * 100 + 2)
    test = splits["test"]  # full test set for final eval
    print(f"Data: dev={len(dev)}, val={len(val)}, test={len(test)}", flush=True)

    run_dir = os.path.join(RESULTS_DIR, f"quick_{mode}", f"run_{run_num}")
    checkpoint_dir = os.path.join(run_dir, "checkpoints")
    os.makedirs(checkpoint_dir, exist_ok=True)

    # Resume support
    resume_path = None
    latest = os.path.join(checkpoint_dir, "checkpoint_latest.json")
    if os.path.exists(latest):
        resume_path = latest
        print(f"Resuming from {latest}", flush=True)

    config = V6Config(
        population_size=6,
        max_generations=5,
        elitism_count=2,
        fresh_injection=1,
        mutation_mode=mode,
    )

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
    results["elapsed_minutes"] = round(elapsed / 60, 1)
    results["scale"] = "quick_32"

    results_file = os.path.join(run_dir, "results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ {mode.upper()} Run {run_num} done in {elapsed/60:.1f} min | test={results['test_accuracy']:.1%}", flush=True)
    return results


def run_all():
    all_results = []
    modes = ["reflective", "random", "static"]
    runs_per = 5

    for mode in modes:
        for run_num in range(1, runs_per + 1):
            result = run_single(mode, run_num)
            all_results.append(result)
            agg_file = os.path.join(RESULTS_DIR, "quick_all_results.json")
            with open(agg_file, "w") as f:
                json.dump(all_results, f, indent=2)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for mode in modes:
        mode_results = [r for r in all_results if r["mode"] == mode]
        accs = [r["test_accuracy"] for r in mode_results]
        mean = sum(accs) / len(accs)
        std = (sum((a - mean)**2 for a in accs) / len(accs)) ** 0.5
        print(f"{mode:12s}: mean={mean:.1%} ± {std:.1%}  runs={[f'{a:.1%}' for a in accs]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["reflective", "random", "static"])
    parser.add_argument("--run", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    if args.all:
        run_all()
    elif args.mode:
        run_single(args.mode, args.run)
    else:
        parser.print_help()
