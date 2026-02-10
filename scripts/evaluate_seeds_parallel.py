#!/usr/bin/env python3
"""Evaluate all V5 seed strategies on test set — PARALLEL version.

Uses ThreadPoolExecutor for concurrent LLM calls.
"""

import os
import sys
import json
import time
import random
import numpy as np
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.market_data import create_examples, split_examples
from src.evolution_v5 import Agent, predict, SEED_STRATEGIES

SEED_NAMES = ["Trend Follower", "Mean Reversion", "Volatility", "Pattern Recognition"]
MAX_WORKERS = 4  # Concurrent requests to LM Studio


def binomial_ci(k, n, z=1.96):
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2*n)) / denom
    margin = z * np.sqrt(p*(1-p)/n + z**2/(4*n**2)) / denom
    return max(0, center - margin), min(1, center + margin)


def binomial_test_p(k, n, p0=0.5):
    from math import comb
    return sum(comb(n, i) * p0**i * (1-p0)**(n-i) for i in range(k, n+1))


def evaluate_agent_parallel(agent, examples, max_workers=MAX_WORKERS):
    """Evaluate agent on examples using parallel LLM calls."""
    predictions = [None] * len(examples)
    
    def eval_one(idx):
        return idx, predict(agent, examples[idx])
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(eval_one, i): i for i in range(len(examples))}
        done = 0
        correct = 0
        for future in as_completed(futures):
            idx, pred = future.result()
            predictions[idx] = pred
            done += 1
            if pred["correct"]:
                correct += 1
            if done % 10 == 0:
                print(f"    {done}/{len(examples)} ({correct}/{done} correct)", flush=True)
    
    accuracy = sum(1 for p in predictions if p["correct"]) / len(predictions)
    return accuracy, predictions


def main():
    print(f"{'='*60}")
    print("Célula Madre V5 — Seed Strategy Evaluation (Parallel)")
    print(f"Started: {datetime.now().isoformat()}")
    print(f"Workers: {MAX_WORKERS}")
    print(f"{'='*60}\n")

    examples = create_examples("data/btc_daily_365.json", asset="BTC")
    train, val, test = split_examples(examples)
    
    actual = [ex.direction for ex in test]
    n = len(actual)
    up_count = sum(1 for d in actual if d == "UP")
    down_count = n - up_count
    p_naive = down_count / n
    
    print(f"Test set: {n} examples, {up_count} UP ({up_count/n:.1%}), {down_count} DOWN ({down_count/n:.1%})")
    print(f"Significance threshold (vs 50%): >= 60/{n} = 59.4%")
    print(f"Significance threshold (vs always-DOWN {p_naive:.1%}): >= 68/{n} = 67.3%\n")
    
    results = []
    for i, (strategy, name) in enumerate(zip(SEED_STRATEGIES, SEED_NAMES)):
        agent = Agent(id=i, strategy_prompt=strategy, generation=0)
        print(f"Evaluating {name}...")
        start = time.time()
        accuracy, predictions = evaluate_agent_parallel(agent, test)
        elapsed = time.time() - start
        
        correct = sum(1 for p in predictions if p["correct"])
        ci_lo, ci_hi = binomial_ci(correct, n)
        p_random = binomial_test_p(correct, n, 0.5)
        p_vs_naive = binomial_test_p(correct, n, p_naive)
        
        results.append({
            "name": name,
            "accuracy": accuracy,
            "correct": correct,
            "total": n,
            "ci_95": [ci_lo, ci_hi],
            "p_vs_random": p_random,
            "p_vs_naive": p_vs_naive,
            "elapsed_s": elapsed,
        })
        
        sig_r = "✓" if p_random < 0.05 else "✗"
        print(f"  → {accuracy:.1%} ({correct}/{n}) | CI:[{ci_lo:.1%},{ci_hi:.1%}] | p={p_random:.4f} {sig_r} | {elapsed:.0f}s\n")
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"{'Strategy':<22} {'Acc':>6} {'Correct':>8} {'p(rand)':>8} {'p(naive)':>9}")
    for r in results:
        print(f"{r['name']:<22} {r['accuracy']:>5.1%} {r['correct']:>4}/{r['total']:<3} {r['p_vs_random']:>8.4f} {r['p_vs_naive']:>9.4f}")
    
    # Best
    best = max(results, key=lambda r: r["accuracy"])
    print(f"\nBest: {best['name']} at {best['accuracy']:.1%}")
    if best["p_vs_random"] < 0.05:
        print("  → Statistically significant vs random (p<0.05) ✓")
    else:
        print("  → NOT significant vs random ✗")
    
    # Save
    os.makedirs("results", exist_ok=True)
    out_path = f"results/seed_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_path, "w") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "test_n": n, "results": results}, f, indent=2)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
