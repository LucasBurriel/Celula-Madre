#!/usr/bin/env python3
"""Run V5 evolution experiment — Célula Madre.

Usage:
    python -m scripts.run_v5 [--generations N] [--population N] [--dev-batch N] [--resume PATH]
"""

import argparse
import os
import sys
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.market_data import create_examples, split_examples
from src.evolution_v5 import (
    EvolutionConfig, EvolutionEngine, SEED_STRATEGIES,
)


def main():
    parser = argparse.ArgumentParser(description="Run Célula Madre V5 evolution")
    parser.add_argument("--generations", type=int, default=10)
    parser.add_argument("--population", type=int, default=8)
    parser.add_argument("--dev-batch", type=int, default=20)
    parser.add_argument("--val-batch", type=int, default=0, help="Val batch size (0=all)")
    parser.add_argument("--asset", default="bitcoin", help="CoinGecko asset id")
    parser.add_argument("--resume", type=str, help="Path to checkpoint JSON to resume from")
    parser.add_argument("--eval-model", type=str, default="", help="Model for predictions (faster)")
    parser.add_argument("--mutation-model", type=str, default="", help="Model for mutation/merge (smarter)")
    args = parser.parse_args()

    print(f"{'='*60}")
    print(f"Célula Madre V5 — Market-Driven Prompt Evolution")
    print(f"Started: {datetime.now().isoformat()}")
    print(f"Asset: {args.asset} | Pop: {args.population} | Gens: {args.generations} | Dev batch: {args.dev_batch}")
    print(f"{'='*60}\n")

    # Load data
    print("Loading market data...")
    data_file = f"data/{'btc' if 'bitcoin' in args.asset else 'eth'}_daily_365.json"
    examples = create_examples(data_file, asset=args.asset.upper().replace('BITCOIN','BTC').replace('ETHEREUM','ETH'))
    train, val, test = split_examples(examples)
    print(f"Data: {len(examples)} total → train={len(train)}, val={len(val)}, test={len(test)}")

    # Config
    config = EvolutionConfig(
        population_size=args.population,
        max_generations=args.generations,
        mutation_rate=0.5,
        dev_batch_size=args.dev_batch,
        val_batch_size=args.val_batch,
        enable_merge=True,
        max_merges_per_gen=2,
        elitism_count=2,
        fresh_injection=2,
        eval_model=args.eval_model,
        mutation_model=args.mutation_model,
    )

    # Checkpoint dir
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    checkpoint_dir = f"results/v5_{args.asset}_{timestamp}"
    os.makedirs(checkpoint_dir, exist_ok=True)

    # Log file
    log_path = os.path.join(checkpoint_dir, "evolution.log")
    log_file = open(log_path, "w")

    def log_callback(msg):
        log_file.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        log_file.flush()

    # Resume?
    resume_checkpoint = None
    if args.resume:
        print(f"Loading checkpoint: {args.resume}")
        resume_checkpoint = EvolutionEngine.load_checkpoint(args.resume)

    # Run
    engine = EvolutionEngine(config)
    best_agent = engine.run(
        train_examples=train,
        val_examples=val,
        test_examples=test,
        seed_strategies=SEED_STRATEGIES,
        log_callback=log_callback,
        checkpoint_dir=checkpoint_dir,
        resume_checkpoint=resume_checkpoint,
    )

    # Final test
    from src.evolution_v5 import evaluate_batch
    test_accuracy, test_preds = evaluate_batch(best_agent, test, config.llm_kwargs)

    # Save results
    results_path = os.path.join(checkpoint_dir, "final_results.json")
    engine.save_results(results_path, best_agent, test_accuracy)

    log_file.close()

    print(f"\n✅ Evolution complete. Results in {checkpoint_dir}/")
    print(f"Best agent {best_agent.id}: val={best_agent.val_accuracy:.0%}, test={test_accuracy:.0%}")


if __name__ == "__main__":
    main()
