#!/usr/bin/env python3
"""TASK-004: Dry run — evaluate 1 hardcoded agent on a small batch to validate the framework."""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.market_data import create_examples, split_examples
from src.evolution_v5 import Agent, predict, evaluate_batch, SEED_STRATEGIES

def main():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    btc_file = os.path.join(data_dir, "btc_daily_365.json")
    
    if not os.path.exists(btc_file):
        print("ERROR: BTC data not found. Run scripts/fetch_market_data.py first.")
        return
    
    # Load examples
    print("Loading BTC examples...")
    examples = create_examples(btc_file, asset="BTC", lookback=30)
    train, val, test = split_examples(examples)
    print(f"Train: {len(train)} | Val: {len(val)} | Test: {len(test)}")
    
    # Create 1 hardcoded agent (trend follower)
    agent = Agent(
        id=0,
        strategy_prompt=SEED_STRATEGIES[0],  # Trend follower
        generation=0,
    )
    print(f"\nAgent 0: Trend Follower")
    print(f"Strategy: {agent.strategy_prompt[:100]}...")
    
    # Evaluate on small batch (5 examples from dev set)
    batch = train[:5]
    print(f"\n--- Evaluating on {len(batch)} examples ---")
    
    start = time.time()
    accuracy, predictions = evaluate_batch(agent, batch)
    elapsed = time.time() - start
    
    print(f"\nResults ({elapsed:.1f}s):")
    print(f"Accuracy: {accuracy:.0%} ({sum(1 for p in predictions if p['correct'])}/{len(predictions)})")
    print()
    
    for p in predictions:
        status = "✓" if p["correct"] else "✗"
        print(f"  {status} {p['date']}: predicted={p['predicted']} actual={p['actual']} ({p['change_pct']:+.1f}%)")
        print(f"    Reasoning: {p['reasoning'][:120]}")
    
    # Now test on full dev set (all train examples)
    print(f"\n--- Full dev evaluation ({len(train)} examples) ---")
    start = time.time()
    full_acc, full_preds = evaluate_batch(agent, train)
    elapsed = time.time() - start
    
    correct = sum(1 for p in full_preds if p["correct"])
    print(f"Accuracy: {full_acc:.1%} ({correct}/{len(train)})")
    print(f"Time: {elapsed:.1f}s ({elapsed/len(train):.1f}s per example)")
    
    # Breakdown by direction
    up_preds = [p for p in full_preds if p["actual"] == "UP"]
    down_preds = [p for p in full_preds if p["actual"] == "DOWN"]
    up_correct = sum(1 for p in up_preds if p["correct"])
    down_correct = sum(1 for p in down_preds if p["correct"])
    print(f"UP accuracy: {up_correct}/{len(up_preds)} ({up_correct/len(up_preds)*100:.0f}%)" if up_preds else "No UP examples")
    print(f"DOWN accuracy: {down_correct}/{len(down_preds)} ({down_correct/len(down_preds)*100:.0f}%)" if down_preds else "No DOWN examples")
    
    print("\n✅ Agent evaluation framework validated!")

if __name__ == "__main__":
    main()
