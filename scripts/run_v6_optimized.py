#!/usr/bin/env python3
"""V6 Optimized Runner — reduced eval sizes for practical runtime.

3 runs per mode × 3 modes = 9 total.
dev=30, val=30, test=200 (full test for final eval).
pop=6, gens=8.
Estimated: ~20-30 min per run, ~3-4 hours total.
"""
import json, os, sys, time, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ag_news_data import load_splits
from src.evolution_v6 import EvolutionEngineV6, V6Config, SEED_STRATEGIES

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "v6")

def subsample(examples, n, seed=42):
    """Balanced subsample."""
    rng = random.Random(seed)
    by_label = {}
    for ex in examples:
        by_label.setdefault(ex['label'], []).append(ex)
    per_class = max(1, n // len(by_label))
    result = []
    for label, exs in sorted(by_label.items()):
        result.extend(rng.sample(exs, min(per_class, len(exs))))
    rng.shuffle(result)
    return result[:n]

def run_single(mode, run_num, dev, val, test):
    print(f"\n{'#'*60}", flush=True)
    print(f"# V6: {mode.upper()} — Run {run_num}", flush=True)
    print(f"# dev={len(dev)}, val={len(val)}, test={len(test)}", flush=True)
    print(f"{'#'*60}\n", flush=True)

    run_dir = os.path.join(RESULTS_DIR, mode, f"run_{run_num}")
    cp_dir = os.path.join(run_dir, "checkpoints")
    os.makedirs(cp_dir, exist_ok=True)

    # Check for existing results
    results_file = os.path.join(run_dir, "results.json")
    if os.path.exists(results_file):
        print(f"  ⏭️  Already completed, skipping", flush=True)
        with open(results_file) as f:
            return json.load(f)

    # Resume from checkpoint if available
    resume_path = None
    latest = os.path.join(cp_dir, "checkpoint_latest.json")
    if os.path.exists(latest):
        resume_path = latest

    config = V6Config(
        population_size=6,
        max_generations=8,
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
        seed_strategies=SEED_STRATEGIES[:6],
        checkpoint_dir=cp_dir,
        resume_from=resume_path,
    )
    elapsed = time.time() - start
    results["run_num"] = run_num
    results["elapsed_seconds"] = round(elapsed, 1)

    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ {mode.upper()} Run {run_num}: test={results['test_accuracy']:.1%} in {elapsed/60:.1f}min", flush=True)
    return results

def main():
    splits = load_splits()
    # Use smaller dev/val for speed, full test for rigor
    dev = subsample(splits["dev"], 30, seed=42)
    val = subsample(splits["val"], 30, seed=123)
    test = splits["test"]  # full 200

    print(f"Data: dev={len(dev)}, val={len(val)}, test={len(test)}", flush=True)

    all_results = []
    modes = ["reflective", "random", "static"]

    for mode in modes:
        for run_num in range(1, 4):  # 3 runs each
            result = run_single(mode, run_num, dev, val, test)
            all_results.append(result)
            # Save aggregate
            with open(os.path.join(RESULTS_DIR, "all_results_optimized.json"), "w") as f:
                json.dump(all_results, f, indent=2)

    # Summary
    print(f"\n{'='*60}", flush=True)
    print("SUMMARY", flush=True)
    print(f"{'='*60}", flush=True)
    for mode in modes:
        mode_r = [r for r in all_results if r["mode"] == mode]
        accs = [r["test_accuracy"] for r in mode_r]
        mean = sum(accs) / len(accs) if accs else 0
        print(f"{mode:12s}: mean_test={mean:.1%}  runs={[f'{a:.1%}' for a in accs]}", flush=True)

if __name__ == "__main__":
    main()
