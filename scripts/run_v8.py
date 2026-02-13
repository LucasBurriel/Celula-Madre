#!/usr/bin/env python3
"""Run V8 multi-domain sentiment evolution experiments.

Usage:
    python scripts/run_v8.py --group market_reflective --run 1
    python scripts/run_v8.py --group tournament_random --run 2 --resume
    python scripts/run_v8.py --all
    python scripts/run_v8.py --all --provider openrouter --api-key KEY
"""

import argparse
import json
import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sentiment_data import load_splits, SEED_STRATEGIES
from src.evolution_v8 import EvolutionEngineV8, V8Config
from src.market_selection import MarketConfig

GROUPS = {
    "market_reflective":    {"selection": "market",     "mutation": "reflective"},
    "market_random":        {"selection": "market",     "mutation": "random"},
    "tournament_reflective": {"selection": "tournament", "mutation": "reflective"},
    "tournament_random":    {"selection": "tournament",  "mutation": "random"},
}

RESULTS_DIR = "results/v8"
RUNS_PER_GROUP = 3


def run_single(group: str, run_num: int, resume: bool = False, llm_kwargs: dict = {}):
    """Run a single V8 experiment."""
    gconfig = GROUPS[group]
    run_dir = os.path.join(RESULTS_DIR, group, f"run{run_num}")
    os.makedirs(run_dir, exist_ok=True)

    print(f"\n{'#'*60}")
    print(f"V8 — {group} — Run {run_num}")
    print(f"Selection: {gconfig['selection']}, Mutation: {gconfig['mutation']}")
    print(f"{'#'*60}\n", flush=True)

    # Load data
    splits = load_splits()
    dev = splits["dev"]
    val = splits["val"]
    test = splits["test"]

    config = V8Config(
        population_size=8,
        max_generations=10,
        elitism_count=2,
        fresh_injection=1,
        gating_tolerance=0.03,
        mutation_mode=gconfig["mutation"],
        selection_mode=gconfig["selection"],
        market_config=MarketConfig(),
        llm_kwargs=llm_kwargs,
    )

    engine = EvolutionEngineV8(config)

    resume_path = None
    if resume:
        latest = os.path.join(run_dir, "checkpoint_latest.json")
        if os.path.exists(latest):
            resume_path = latest
            print(f"  Resuming from {latest}", flush=True)

    result = engine.run(
        dev_examples=dev,
        val_examples=val,
        test_examples=test,
        seed_strategies=SEED_STRATEGIES,
        checkpoint_dir=run_dir,
        resume_from=resume_path,
    )

    # Save final result
    result_path = os.path.join(run_dir, "final_result.json")
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Result saved: {result_path}", flush=True)
    print(f"   Test accuracy: {result['test_accuracy']:.1%}", flush=True)
    if result.get("test_per_domain"):
        for d, acc in result["test_per_domain"].items():
            print(f"   {d}: {acc:.1%}", flush=True)

    return result


def run_all(resume: bool = False, llm_kwargs: dict = {}):
    """Run all 12 experiments sequentially."""
    results = {}
    for group in GROUPS:
        for run_num in range(1, RUNS_PER_GROUP + 1):
            key = f"{group}_run{run_num}"
            try:
                result = run_single(group, run_num, resume=resume, llm_kwargs=llm_kwargs)
                results[key] = {
                    "test_accuracy": result["test_accuracy"],
                    "test_per_domain": result.get("test_per_domain", {}),
                    "best_agent_id": result["best_agent_id"],
                }
            except Exception as e:
                print(f"\n❌ FAILED: {key}: {e}", flush=True)
                results[key] = {"error": str(e)}

    # Save summary
    summary_path = os.path.join(RESULTS_DIR, "v8_summary.json")
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n📊 Summary saved: {summary_path}", flush=True)
    return results


def main():
    parser = argparse.ArgumentParser(description="Run V8 multi-domain sentiment experiments")
    parser.add_argument("--group", choices=list(GROUPS.keys()), help="Experiment group")
    parser.add_argument("--run", type=int, default=1, help="Run number (1-3)")
    parser.add_argument("--all", action="store_true", help="Run all 12 experiments")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--provider", default="lmstudio", help="LLM provider")
    parser.add_argument("--api-key", default="", help="API key for cloud providers")
    parser.add_argument("--model", default="", help="Model name override")
    args = parser.parse_args()

    llm_kwargs = {}
    if args.provider != "lmstudio":
        llm_kwargs["provider"] = args.provider
    if args.api_key:
        llm_kwargs["api_key"] = args.api_key
    if args.model:
        llm_kwargs["model"] = args.model

    if args.all:
        run_all(resume=args.resume, llm_kwargs=llm_kwargs)
    elif args.group:
        run_single(args.group, args.run, resume=args.resume, llm_kwargs=llm_kwargs)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
