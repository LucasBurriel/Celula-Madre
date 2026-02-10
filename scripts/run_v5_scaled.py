#!/usr/bin/env python3
"""Run V5 scaled experiment — 3 independent runs + random baseline.

TASK-008: Larger-scale V5 run with statistical rigor.
- pop=8, gens=10, dev_batch=30, val_batch=30
- 3 independent evolution runs
- Random baseline on test set
- Statistical comparison
"""

import json
import os
import sys
import random
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.market_data import create_examples, split_examples
from src.evolution_v5 import (
    EvolutionConfig, EvolutionEngine, SEED_STRATEGIES,
    Agent, evaluate_batch,
)


def random_baseline(test_examples, n_trials=1000):
    """Run random baseline: random UP/DOWN for each example, n_trials times."""
    accuracies = []
    for _ in range(n_trials):
        correct = sum(
            1 for ex in test_examples
            if random.choice(["UP", "DOWN"]) == ex.direction
        )
        accuracies.append(correct / len(test_examples))
    return accuracies


def run_single_evolution(run_id, train, val, test, base_dir):
    """Run one evolution experiment."""
    print(f"\n{'#'*60}")
    print(f"# RUN {run_id}")
    print(f"{'#'*60}\n")
    
    config = EvolutionConfig(
        population_size=8,
        max_generations=10,
        mutation_rate=0.5,
        dev_batch_size=30,
        val_batch_size=30,
        enable_merge=True,
        max_merges_per_gen=2,
        elitism_count=2,
        fresh_injection=2,
    )
    
    checkpoint_dir = os.path.join(base_dir, f"run_{run_id}")
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    log_path = os.path.join(checkpoint_dir, "evolution.log")
    log_file = open(log_path, "w")
    
    def log_cb(msg):
        log_file.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        log_file.flush()
    
    engine = EvolutionEngine(config)
    start = time.time()
    best_agent = engine.run(
        train_examples=train,
        val_examples=val,
        test_examples=test,
        seed_strategies=SEED_STRATEGIES,
        log_callback=log_cb,
        checkpoint_dir=checkpoint_dir,
    )
    duration = time.time() - start
    
    # Final test eval
    test_accuracy, test_preds = evaluate_batch(best_agent, test, config.llm_kwargs)
    
    # Save results
    engine.save_results(
        os.path.join(checkpoint_dir, "final_results.json"),
        best_agent, test_accuracy,
    )
    
    log_file.close()
    
    return {
        "run_id": run_id,
        "best_agent_id": best_agent.id,
        "best_generation": best_agent.generation,
        "val_accuracy": best_agent.val_accuracy,
        "test_accuracy": test_accuracy,
        "strategy_preview": best_agent.strategy_prompt[:300],
        "full_strategy": best_agent.strategy_prompt,
        "duration_sec": round(duration, 1),
        "history": engine.history,
    }


def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_dir = f"results/v5_scaled_{timestamp}"
    os.makedirs(base_dir, exist_ok=True)
    
    print(f"Célula Madre V5 — Scaled Experiment")
    print(f"Started: {datetime.now().isoformat()}")
    print(f"Output: {base_dir}")
    print(f"Config: pop=8, gens=10, dev=30, val=30, 3 runs")
    
    # Load data
    data_file = "data/btc_daily_365.json"
    examples = create_examples(data_file, asset="BTC")
    train, val, test = split_examples(examples)
    print(f"Data: {len(examples)} → train={len(train)}, val={len(val)}, test={len(test)}")
    
    # Random baseline
    print("\n--- Random Baseline (1000 trials) ---")
    baseline_accs = random_baseline(test)
    baseline_mean = sum(baseline_accs) / len(baseline_accs)
    baseline_sorted = sorted(baseline_accs)
    baseline_p95 = baseline_sorted[int(0.95 * len(baseline_sorted))]
    print(f"Random baseline: mean={baseline_mean:.3f}, 95th percentile={baseline_p95:.3f}")
    
    # Run 3 independent evolutions
    all_results = []
    for run_id in range(1, 4):
        result = run_single_evolution(run_id, train, val, test, base_dir)
        all_results.append(result)
        print(f"\n✅ Run {run_id} complete: test={result['test_accuracy']:.1%} in {result['duration_sec']}s")
    
    # Summary
    test_accs = [r["test_accuracy"] for r in all_results]
    mean_test = sum(test_accs) / len(test_accs)
    
    summary = {
        "timestamp": timestamp,
        "config": {"pop": 8, "gens": 10, "dev_batch": 30, "val_batch": 30, "runs": 3},
        "baseline": {
            "mean": round(baseline_mean, 4),
            "p95": round(baseline_p95, 4),
            "n_trials": 1000,
        },
        "runs": [
            {
                "run_id": r["run_id"],
                "test_accuracy": round(r["test_accuracy"], 4),
                "val_accuracy": round(r["val_accuracy"], 4),
                "best_generation": r["best_generation"],
                "duration_sec": r["duration_sec"],
                "strategy_preview": r["strategy_preview"],
            }
            for r in all_results
        ],
        "aggregate": {
            "mean_test": round(mean_test, 4),
            "min_test": round(min(test_accs), 4),
            "max_test": round(max(test_accs), 4),
            "vs_baseline": round(mean_test - baseline_mean, 4),
        },
    }
    
    summary_path = os.path.join(base_dir, "summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"Random baseline: {baseline_mean:.1%} (95th: {baseline_p95:.1%})")
    for r in all_results:
        print(f"Run {r['run_id']}: test={r['test_accuracy']:.1%} val={r['val_accuracy']:.1%} ({r['duration_sec']}s)")
    print(f"Mean test accuracy: {mean_test:.1%} (Δ vs baseline: {mean_test - baseline_mean:+.1%})")
    print(f"\nResults saved to {base_dir}/")


if __name__ == "__main__":
    main()
