"""Run V7 mini experiments with gemma-3-4b.

Scaled down for feasibility:
- pop=4, gens=5, dev=10, val=10, test=20, max_turns=3
- Uses gemma-3-4b (~7s per negotiation call)
- Est. ~2-3h per run, ~20h for all 8 runs
"""

import os
import sys
import time
import json
from functools import partial

sys.path.insert(0, ".")

from src.negotiation import generate_splits, save_scenarios, load_scenarios, call_llm
from src.evolution_v7 import EvolutionEngineV7

gemma_llm = partial(call_llm, model="google/gemma-3-4b")

GROUPS = {
    "A": "tournament_reflective",
    "B": "market_random",
    "C": "market_reflective",
    "D": "tournament_random",
}

GROUP_NAMES = {
    "A": "Tournament × Reflective",
    "B": "Market × Random",
    "C": "Market × Reflective (Full CM)",
    "D": "Tournament × Random (Control)",
}


def ensure_scenarios():
    """Generate mini scenario set (40 total: 10 dev, 10 val, 20 test)."""
    path = "data/v7_scenarios_mini.json"
    if not os.path.exists(path):
        print("Generating mini scenarios...")
        # Generate full set and slice
        splits = generate_splits(seed=42)
        mini = {
            "dev": splits["dev"][:10],
            "val": splits["val"][:10],
            "test": splits["test"][:20],
        }
        save_scenarios(mini, path)
    return load_scenarios(path)


def run_single(group, run_num, resume=False):
    mode = GROUPS[group]
    results_dir = f"results/v7_mini/{group}_{mode}/run_{run_num}"

    print(f"\n{'#'*60}")
    print(f"V7 MINI: Group {group} ({GROUP_NAMES[group]}) Run {run_num}")
    print(f"Model: gemma-3-4b | Mode: {mode}")
    print(f"Config: pop=4, gens=5, dev=10, val=10, test=20, turns=3")
    print(f"Results: {results_dir}")
    print(f"{'#'*60}\n")

    scenarios = ensure_scenarios()

    engine = EvolutionEngineV7(
        mode=mode,
        population_size=4,
        num_generations=5,
        elite_count=1,
        tournament_k=2,
        dev_scenarios=10,
        val_scenarios=10,
        max_turns=3,
        results_dir=results_dir,
        llm_fn=gemma_llm,
    )

    start = time.time()
    results = engine.run(scenarios, resume=resume)
    elapsed = (time.time() - start) / 60

    print(f"\n⏱️ Completed in {elapsed:.1f} minutes")
    if isinstance(results, dict):
        print(f"📊 Test score: {results.get('test_accuracy', results.get('test_score', 'N/A'))}")
    return results


def run_all(resume=False):
    for group in ["A", "B", "C", "D"]:
        for run_num in range(1, 3):  # 2 runs per group
            done_path = f"results/v7_mini/{group}_{GROUPS[group]}/run_{run_num}/results.json"
            if os.path.exists(done_path) and not resume:
                print(f"Skipping Group {group} Run {run_num} (already complete)")
                continue
            try:
                run_single(group, run_num, resume=resume)
            except Exception as e:
                print(f"ERROR in Group {group} Run {run_num}: {e}")
                import traceback
                traceback.print_exc()
                continue


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", choices=["A", "B", "C", "D"])
    parser.add_argument("--run", type=int, choices=[1, 2, 3])
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    if args.all:
        run_all(resume=args.resume)
    elif args.group and args.run:
        run_single(args.group, args.run, resume=args.resume)
    else:
        parser.print_help()
