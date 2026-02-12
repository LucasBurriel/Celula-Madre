#!/usr/bin/env python3
"""Run exactly ONE generation of V6.5, then exit cleanly.

Designed to be called repeatedly by cron/heartbeat.
Each call advances one generation with checkpoint save.

Usage:
  python scripts/run_v6_one_gen.py --group market --run 1
  V65_MODEL=google/gemma-3-4b python scripts/run_v6_one_gen.py --group market --run 1
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
MAX_GENS = 10


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", required=True, choices=GROUPS.keys())
    parser.add_argument("--run", type=int, required=True)
    args = parser.parse_args()

    group_cfg = GROUPS[args.group]
    results_dir = os.path.join(RESULTS_BASE, args.group, f"run_{args.run}")
    os.makedirs(results_dir, exist_ok=True)
    
    checkpoint_path = os.path.join(results_dir, "checkpoint_latest.json")
    
    # Check current state
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path) as f:
            cp = json.load(f)
        current_gen = cp["generation"]
        if current_gen >= MAX_GENS - 1:
            print(f"✅ {args.group} run {args.run} COMPLETE (gen {current_gen})")
            return 0
        print(f"Resuming from gen {current_gen + 1}")
    else:
        print("Starting fresh (gen 0)")

    # Load data
    splits = load_splits()
    
    # Config
    llm_kwargs = {}
    if os.environ.get("V65_MODEL"):
        llm_kwargs["model"] = os.environ["V65_MODEL"]
        print(f"Using model: {llm_kwargs['model']}")

    market_config = MarketConfig(
        softmax_temperature=2.0,
        survival_threshold=0.3,
        client_memory_depth=3,
        exploration_bonus=0.1,
        min_assignments=5,
    )

    config = V65Config(
        population_size=8,
        max_generations=MAX_GENS,
        elitism_count=2,
        fresh_injection=1,
        mutation_mode=group_cfg["mutation_mode"],
        selection_mode=group_cfg["selection_mode"],
        market_config=market_config,
        llm_kwargs=llm_kwargs,
    )

    engine = EvolutionEngineV65(config)

    # Run with max_gens = current + 1 (single gen advance)
    # Actually, let's just use the run method with resume
    resume_from = checkpoint_path if os.path.exists(checkpoint_path) else None
    
    # Override max_gens to stop after 1 more gen
    if resume_from:
        with open(resume_from) as f:
            cp = json.load(f)
        next_gen = cp["generation"] + 1
        config.max_generations = next_gen + 1  # Will stop after completing next_gen
    else:
        config.max_generations = 1  # Just gen 0
    
    t0 = time.time()
    result = engine.run(
        dev_examples=splits["dev"],
        val_examples=splits["val"],
        test_examples=splits["test"],
        checkpoint_dir=results_dir,
        resume_from=resume_from,
    )
    elapsed = time.time() - t0
    
    # Check new state
    new_cp_path = os.path.join(results_dir, "checkpoint_latest.json")
    if os.path.exists(new_cp_path):
        with open(new_cp_path) as f:
            new_cp = json.load(f)
        print(f"\n✅ Completed gen {new_cp['generation']} in {elapsed:.0f}s")
        print(f"   Best val: {new_cp['history'][-1]['best_val']:.1%}")
        if new_cp['generation'] >= MAX_GENS - 1:
            print(f"   🏁 RUN COMPLETE!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
