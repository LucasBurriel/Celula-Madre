#!/usr/bin/env python3
"""Célula Madre V5 — Run market-driven prompt evolution.

Usage:
    python3 main_v5.py [--generations N] [--population N] [--base-url URL]
"""

import argparse
import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.market_data import create_examples, split_examples
from src.evolution_v5 import EvolutionEngine, EvolutionConfig, evaluate_batch, SEED_STRATEGIES


def main():
    parser = argparse.ArgumentParser(description="Célula Madre V5")
    parser.add_argument("--generations", type=int, default=5, help="Evolution generations")
    parser.add_argument("--population", type=int, default=4, help="Population size")
    parser.add_argument("--mutation-rate", type=float, default=0.5, help="Mutation rate")
    parser.add_argument("--dev-batch", type=int, default=20, help="Dev batch size")
    parser.add_argument("--base-url", type=str, default="http://172.17.0.1:1234", help="LLM API base URL")
    parser.add_argument("--model", type=str, default="qwen3-coder-30b-a3b-instruct", help="Model name")
    parser.add_argument("--asset", type=str, default="BTC", help="Asset (BTC or ETH)")
    parser.add_argument("--lookback", type=int, default=30, help="Days of history per example")
    parser.add_argument("--no-merge", action="store_true", help="Disable structural merge")
    parser.add_argument("--output", type=str, default=None, help="Output JSON file")
    args = parser.parse_args()
    
    # Load data
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    asset_file = f"{args.asset.lower()}_daily_365.json"
    filepath = os.path.join(data_dir, asset_file)
    
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found. Run src/market_data.py first.")
        sys.exit(1)
    
    print(f"Loading {args.asset} data from {filepath}...")
    examples = create_examples(filepath, asset=args.asset, lookback=args.lookback)
    train, val, test = split_examples(examples)
    
    print(f"Examples: {len(examples)} total")
    print(f"  Train: {len(train)} | Val: {len(val)} | Test: {len(test)}")
    
    up = sum(1 for e in examples if e.direction == "UP")
    print(f"  Baseline (always UP): {up/len(examples)*100:.1f}%")
    print(f"  Baseline (random): 50.0%")
    
    # Configure
    llm_kwargs = {"base_url": args.base_url, "model": args.model}
    
    config = EvolutionConfig(
        population_size=args.population,
        max_generations=args.generations,
        mutation_rate=args.mutation_rate,
        dev_batch_size=args.dev_batch,
        enable_merge=not args.no_merge,
        llm_kwargs=llm_kwargs,
    )
    
    # Log file
    log_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"v5_output_{args.asset.lower()}_{int(time.time())}.log"
    )
    
    def log_callback(msg):
        with open(log_file, "a") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    
    print(f"\nLog: {log_file}")
    print(f"Config: pop={config.population_size}, gens={config.max_generations}, "
          f"mut={config.mutation_rate}, merge={'on' if config.enable_merge else 'off'}")
    print(f"LLM: {args.model} @ {args.base_url}")
    
    # Run evolution
    engine = EvolutionEngine(config)
    
    start_time = time.time()
    best = engine.run(
        train_examples=train,
        val_examples=val,
        test_examples=test,
        seed_strategies=SEED_STRATEGIES[:config.population_size],
        log_callback=log_callback,
    )
    
    total_time = time.time() - start_time
    
    # Final test
    test_accuracy, test_preds = evaluate_batch(best, test, llm_kwargs)
    
    print(f"\n{'='*60}")
    print(f"FINAL RESULTS — Célula Madre V5 ({args.asset})")
    print(f"{'='*60}")
    print(f"Total time: {total_time/60:.1f} minutes")
    print(f"Best agent: #{best.id} (generation {best.generation})")
    print(f"Val accuracy: {best.val_accuracy:.1%}")
    print(f"Test accuracy: {test_accuracy:.1%}")
    print(f"Baseline: {up/len(examples)*100:.1f}% (always majority)")
    print(f"\nBest strategy:\n{best.strategy_prompt}")
    
    # Save results
    output = args.output or os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"v5_results_{args.asset.lower()}.json"
    )
    engine.save_results(output, best, test_accuracy)


if __name__ == "__main__":
    main()
