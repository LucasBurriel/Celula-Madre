#!/usr/bin/env python3
"""V6.5 Runner — Market vs Tournament selection on AG News.

Usage:
  python scripts/run_v6_market.py --group market --run 1
  python scripts/run_v6_market.py --group tournament --run 1
  python scripts/run_v6_market.py --all          # Run all 6 experiments
  python scripts/run_v6_market.py --all --resume  # Resume interrupted batch
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ag_news_data import load_splits
from src.evolution_v6_market import EvolutionEngineV65, V65Config
from src.market_selection import MarketConfig

RESULTS_BASE = "results/v6.5"
GROUPS = {
    "market": {"selection_mode": "market", "mutation_mode": "reflective"},
    "tournament": {"selection_mode": "tournament", "mutation_mode": "reflective"},
}
RUNS_PER_GROUP = 3


def run_experiment(group: str, run_num: int, resume: bool = False):
    """Run a single experiment."""
    group_cfg = GROUPS[group]
    results_dir = os.path.join(RESULTS_BASE, f"{group}", f"run_{run_num}")
    os.makedirs(results_dir, exist_ok=True)

    print(f"\n{'#'*60}")
    print(f"# V6.5: {group.upper()} Run {run_num}")
    print(f"# Selection: {group_cfg['selection_mode']}, Mutation: {group_cfg['mutation_mode']}")
    print(f"# Results: {results_dir}")
    print(f"{'#'*60}\n")

    # Load data
    splits = load_splits()
    dev = splits["dev"]
    val = splits["val"]
    test = splits["test"]
    print(f"Data: dev={len(dev)}, val={len(val)}, test={len(test)}")

    # Config
    market_config = MarketConfig(
        softmax_temperature=2.0,
        survival_threshold=0.3,
        client_memory_depth=3,
        exploration_bonus=0.1,
        min_assignments=5,  # At least 5 examples per agent
    )

    # Allow model override via environment variable
    llm_kwargs = {}
    if os.environ.get("V65_MODEL"):
        llm_kwargs["model"] = os.environ["V65_MODEL"]
        print(f"Using model: {llm_kwargs['model']}")

    config = V65Config(
        population_size=8,
        max_generations=10,
        elitism_count=2,
        fresh_injection=1,
        mutation_mode=group_cfg["mutation_mode"],
        selection_mode=group_cfg["selection_mode"],
        market_config=market_config,
        llm_kwargs=llm_kwargs,
    )

    engine = EvolutionEngineV65(config)

    # Resume?
    resume_path = os.path.join(results_dir, "checkpoint_latest.json")
    resume_from = resume_path if (resume and os.path.exists(resume_path)) else None

    t0 = time.time()
    result = engine.run(
        dev_examples=dev,
        val_examples=val,
        test_examples=test,
        checkpoint_dir=results_dir,
        resume_from=resume_from,
    )
    elapsed = time.time() - t0

    result["elapsed_minutes"] = round(elapsed / 60, 1)
    result["run"] = run_num
    result["group"] = group

    # Save results
    with open(os.path.join(results_dir, "results.json"), "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n⏱️  {group} Run {run_num} completed in {elapsed/60:.1f} minutes")
    print(f"   Test accuracy: {result['test_accuracy']:.1%}")
    return result


def main():
    parser = argparse.ArgumentParser(description="V6.5 Market vs Tournament experiments")
    parser.add_argument("--group", choices=list(GROUPS.keys()), help="Group to run")
    parser.add_argument("--run", type=int, default=1, help="Run number (1-3)")
    parser.add_argument("--all", action="store_true", help="Run all experiments")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    args = parser.parse_args()

    os.makedirs(RESULTS_BASE, exist_ok=True)

    if args.all:
        all_results = {}
        for group in GROUPS:
            for run_num in range(1, RUNS_PER_GROUP + 1):
                key = f"{group}_run{run_num}"
                # Skip if already complete
                results_file = os.path.join(RESULTS_BASE, group, f"run_{run_num}", "results.json")
                if os.path.exists(results_file) and not args.resume:
                    print(f"\n⏭️  Skipping {key} (already complete)")
                    with open(results_file) as f:
                        all_results[key] = json.load(f)
                    continue
                try:
                    result = run_experiment(group, run_num, resume=args.resume)
                    all_results[key] = result
                except Exception as e:
                    print(f"\n❌ {key} FAILED: {e}")
                    import traceback
                    traceback.print_exc()
                    all_results[key] = {"error": str(e)}

        # Summary
        print(f"\n{'='*60}")
        print("V6.5 RESULTS SUMMARY")
        print(f"{'='*60}")
        for key, result in sorted(all_results.items()):
            if "error" in result:
                print(f"  {key}: FAILED - {result['error']}")
            else:
                print(f"  {key}: test={result['test_accuracy']:.1%}")

        with open(os.path.join(RESULTS_BASE, "summary.json"), "w") as f:
            json.dump(all_results, f, indent=2, default=str)
    else:
        if not args.group:
            parser.error("--group required unless --all")
        run_experiment(args.group, args.run, resume=args.resume)


if __name__ == "__main__":
    main()
