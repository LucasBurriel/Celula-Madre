#!/usr/bin/env python3
"""Evaluate all V5 seed strategies on the full test set.

Provides baseline performance for each strategy without evolution.
This gives us: (1) how each seed performs, (2) comparison to random, (3) statistical significance.
"""

import os
import sys
import json
import time
import random
import numpy as np
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.market_data import create_examples, split_examples
from src.evolution_v5 import Agent, evaluate_batch, SEED_STRATEGIES

SEED_NAMES = ["Trend Follower", "Mean Reversion", "Volatility", "Pattern Recognition"]


def binomial_ci(k, n, z=1.96):
    """Wilson score interval for binomial proportion."""
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2*n)) / denom
    margin = z * np.sqrt(p*(1-p)/n + z**2/(4*n**2)) / denom
    return max(0, center - margin), min(1, center + margin)


def binomial_test_p(k, n, p0=0.5):
    """One-sided binomial test: P(X >= k) under p0."""
    from math import comb
    p = sum(comb(n, i) * p0**i * (1-p0)**(n-i) for i in range(k, n+1))
    return p


def main():
    print(f"{'='*60}")
    print("Célula Madre V5 — Seed Strategy Evaluation on Test Set")
    print(f"Started: {datetime.now().isoformat()}")
    print(f"{'='*60}\n")

    # Load data
    examples = create_examples("data/btc_daily_365.json", asset="BTC")
    train, val, test = split_examples(examples)
    
    actual = [ex.direction for ex in test]
    n = len(actual)
    up_count = sum(1 for d in actual if d == "UP")
    down_count = n - up_count
    
    print(f"Test set: {n} examples, {up_count} UP ({up_count/n:.1%}), {down_count} DOWN ({down_count/n:.1%})")
    
    # Naive baselines
    print(f"\n--- Naive Baselines ---")
    print(f"Always UP:  {up_count/n:.1%}")
    print(f"Always DOWN: {down_count/n:.1%}")
    print(f"Random 50/50: ~50.0% (95% CI: [40.6%, 59.4%])")
    
    # Significance thresholds
    # Against 50% (random):
    sig_50 = None
    for k in range(n+1):
        if binomial_test_p(k, n, 0.5) < 0.05:
            sig_50 = k
            break
    print(f"\nTo beat 50% random at p<0.05: need >= {sig_50}/{n} = {sig_50/n:.1%}")
    
    # Against best naive (58.4%):
    p_naive = down_count / n  # Always DOWN
    sig_naive = None
    for k in range(n+1):
        if binomial_test_p(k, n, p_naive) < 0.05:
            sig_naive = k
            break
    print(f"To beat always-DOWN ({p_naive:.1%}) at p<0.05: need >= {sig_naive}/{n} = {sig_naive/n:.1%}")
    
    # Evaluate each seed strategy
    print(f"\n--- Seed Strategy Results ---\n")
    
    results = []
    for i, (strategy, name) in enumerate(zip(SEED_STRATEGIES, SEED_NAMES)):
        agent = Agent(id=i, strategy_prompt=strategy, generation=0)
        print(f"Evaluating {name} (Agent {i})...")
        start = time.time()
        accuracy, predictions = evaluate_batch(agent, test)
        elapsed = time.time() - start
        
        correct = int(accuracy * n)
        ci_lo, ci_hi = binomial_ci(correct, n)
        p_vs_random = binomial_test_p(correct, n, 0.5)
        p_vs_naive = binomial_test_p(correct, n, p_naive)
        
        results.append({
            "name": name,
            "accuracy": accuracy,
            "correct": correct,
            "total": n,
            "ci_95": [ci_lo, ci_hi],
            "p_vs_random": p_vs_random,
            "p_vs_naive": p_vs_naive,
            "elapsed_s": elapsed,
            "predictions": predictions,
        })
        
        sig_r = "✓" if p_vs_random < 0.05 else "✗"
        sig_n = "✓" if p_vs_naive < 0.05 else "✗"
        print(f"  {name}: {accuracy:.1%} ({correct}/{n})")
        print(f"    95% CI: [{ci_lo:.1%}, {ci_hi:.1%}]")
        print(f"    vs random: p={p_vs_random:.4f} {sig_r}")
        print(f"    vs always-DOWN: p={p_vs_naive:.4f} {sig_n}")
        print(f"    Time: {elapsed:.0f}s\n")
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"{'Strategy':<22} {'Acc':>6} {'p(random)':>10} {'p(naive)':>10}")
    print(f"{'-'*22} {'-'*6} {'-'*10} {'-'*10}")
    for r in results:
        print(f"{r['name']:<22} {r['accuracy']:>5.1%} {r['p_vs_random']:>10.4f} {r['p_vs_naive']:>10.4f}")
    
    # Save results
    output = {
        "timestamp": datetime.now().isoformat(),
        "test_set": {"n": n, "up": up_count, "down": down_count},
        "strategies": [{k: v for k, v in r.items() if k != "predictions"} for r in results],
    }
    
    os.makedirs("results", exist_ok=True)
    out_path = f"results/seed_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
