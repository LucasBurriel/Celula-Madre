#!/usr/bin/env python3
"""
Célula Madre V6 — Fast 3-Group Experiment Runner

Uses gemma-3-4b for evaluation (fast) and qwen3-30b for mutation (smart).
Reduced params for practical runtime: pop=6, gens=5, dev=40, val=40, test=100.

Usage:
  python scripts/run_v6_fast.py --all          # All 15 runs
  python scripts/run_v6_fast.py --mode reflective --run 1
"""

import argparse
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ag_news_data import load_splits, evaluate_agent, LABELS
from src.evolution_v6 import (
    Agent, V6Config, SEED_STRATEGIES,
    call_llm, reflective_mutate, random_mutate,
)

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "v6_fast")

# Eval model (fast)
EVAL_MODEL = "google/gemma-3-4b"
# Mutation model (smart)  
MUTATION_MODEL = "qwen3-coder-30b-a3b-instruct"

# Reduced sizes for practical runtime
DEV_SIZE = 40
VAL_SIZE = 40
TEST_SIZE = 100
POP_SIZE = 6
MAX_GENS = 5
ELITE = 2
FRESH = 1


def eval_agent_fast(strategy: str, examples: list) -> dict:
    """Evaluate using fast model."""
    def llm_fn(sys_p, usr_p):
        return call_llm(sys_p, usr_p, model=EVAL_MODEL, temperature=0.1, max_tokens=20)
    return evaluate_agent(strategy, examples, llm_fn)


def run_single(mode: str, run_num: int):
    """Run a single experiment."""
    print(f"\n{'#'*60}")
    print(f"# V6-FAST: {mode.upper()} — Run {run_num}")
    print(f"{'#'*60}\n")

    # Load and subsample data (fixed seed per run for reproducibility)
    splits = load_splits()
    rng = random.Random(run_num * 1000 + hash(mode) % 1000)
    
    dev = rng.sample(splits["dev"], DEV_SIZE)
    val = rng.sample(splits["val"], VAL_SIZE)
    test = rng.sample(splits["test"], TEST_SIZE)
    print(f"Data: dev={len(dev)}, val={len(val)}, test={len(test)}")

    run_dir = os.path.join(RESULTS_DIR, mode, f"run_{run_num}")
    os.makedirs(run_dir, exist_ok=True)

    # Check for existing results
    results_file = os.path.join(run_dir, "results.json")
    if os.path.exists(results_file):
        print(f"  ⏩ Already completed, skipping.")
        with open(results_file) as f:
            return json.load(f)

    # Init population
    agent_counter = 0
    def new_agent(strategy, gen=0, parents=[]):
        nonlocal agent_counter
        a = Agent(id=agent_counter, strategy_prompt=strategy, generation=gen, parents=parents)
        agent_counter += 1
        return a

    seeds = SEED_STRATEGIES[:POP_SIZE]
    population = [new_agent(s) for s in seeds]
    history = []
    start_time = time.time()

    for gen in range(MAX_GENS):
        gen_start = time.time()
        print(f"\n{'='*50}\n[{mode.upper()}] Generation {gen}/{MAX_GENS}\n{'='*50}")

        # Phase 1: Eval on dev
        for agent in population:
            result = eval_agent_fast(agent.strategy_prompt, dev)
            agent.dev_accuracy = result["accuracy"]
            agent.dev_errors = result["errors"]
            agent.per_class = result["per_class"]
            print(f"  Agent {agent.id} (gen{agent.generation}): dev={agent.dev_accuracy:.1%}")

        # Phase 2: Eval on val
        for agent in population:
            result = eval_agent_fast(agent.strategy_prompt, val)
            agent.val_accuracy = result["accuracy"]

        ranked = sorted(population, key=lambda a: a.val_accuracy, reverse=True)
        gen_best = ranked[0]
        print(f"  Gen {gen} best: Agent {gen_best.id} val={gen_best.val_accuracy:.1%} dev={gen_best.dev_accuracy:.1%}")

        gen_info = {
            "generation": gen,
            "mode": mode,
            "agents": [
                {"id": a.id, "gen": a.generation, "dev": round(a.dev_accuracy, 4),
                 "val": round(a.val_accuracy, 4), "parents": a.parents}
                for a in ranked
            ],
            "best_val": round(gen_best.val_accuracy, 4),
            "mean_val": round(sum(a.val_accuracy for a in population) / len(population), 4),
            "duration_sec": round(time.time() - gen_start, 1),
        }
        history.append(gen_info)

        # Save checkpoint
        cp = {"generation": gen, "history": history, 
              "population": [a.to_dict() for a in ranked]}
        with open(os.path.join(run_dir, f"checkpoint_gen{gen}.json"), "w") as f:
            json.dump(cp, f, indent=2)

        # Phase 3: Generate next gen (unless last)
        if gen >= MAX_GENS - 1:
            break

        if mode == "static":
            continue

        new_pop = []

        # Elitism
        for a in ranked[:ELITE]:
            new_pop.append(a)
            print(f"  👑 Elite: Agent {a.id} (val={a.val_accuracy:.1%})")

        # Mutations
        mutation_slots = POP_SIZE - ELITE - FRESH
        for _ in range(mutation_slots):
            candidates = random.sample(population, min(3, len(population)))
            parent = max(candidates, key=lambda a: a.val_accuracy)

            # Use smart model for mutation
            llm_kw = {"model": MUTATION_MODEL}
            if mode == "reflective":
                child_strategy = reflective_mutate(parent, llm_kw)
            else:
                child_strategy = random_mutate(parent, llm_kw)

            child = new_agent(child_strategy, gen=gen+1, parents=[parent.id])

            # Gating: eval on val with fast model
            child_result = eval_agent_fast(child.strategy_prompt, val)
            child.val_accuracy = child_result["accuracy"]

            if child.val_accuracy >= parent.val_accuracy:
                new_pop.append(child)
                print(f"  ✓ Mutation: {parent.id}→{child.id} ({parent.val_accuracy:.1%}→{child.val_accuracy:.1%})")
            else:
                new_pop.append(parent)
                print(f"  ✗ Rejected: {parent.id}→{child.id} ({parent.val_accuracy:.1%}→{child.val_accuracy:.1%})")

        # Fresh injection
        for _ in range(FRESH):
            fresh = new_agent(random.choice(SEED_STRATEGIES), gen=gen+1)
            new_pop.append(fresh)
            print(f"  🌱 Fresh: Agent {fresh.id}")

        population = new_pop[:POP_SIZE]

    # Final test
    print(f"\n{'='*50}\nFinal Test ({mode})\n{'='*50}")
    best_agent = max(population, key=lambda a: a.val_accuracy)
    test_result = eval_agent_fast(best_agent.strategy_prompt, test)
    test_acc = test_result["accuracy"]
    print(f"Best Agent {best_agent.id}: val={best_agent.val_accuracy:.1%} test={test_acc:.1%}")

    elapsed = time.time() - start_time
    results = {
        "mode": mode,
        "run_num": run_num,
        "best_agent_id": best_agent.id,
        "best_agent_generation": best_agent.generation,
        "best_agent_strategy": best_agent.strategy_prompt,
        "best_val_accuracy": round(best_agent.val_accuracy, 4),
        "test_accuracy": round(test_acc, 4),
        "test_per_class": {k: round(v["accuracy"], 3) for k, v in test_result["per_class"].items()},
        "history": history,
        "elapsed_seconds": round(elapsed, 1),
        "elapsed_minutes": round(elapsed / 60, 1),
        "config": {
            "pop": POP_SIZE, "gens": MAX_GENS, "elite": ELITE,
            "dev": DEV_SIZE, "val": VAL_SIZE, "test": TEST_SIZE,
            "eval_model": EVAL_MODEL, "mutation_model": MUTATION_MODEL,
        },
    }

    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ {mode.upper()} Run {run_num} done in {elapsed/60:.1f} min | test={test_acc:.1%}")
    return results


def run_all():
    """Run all 15 experiments."""
    all_results = []
    modes = ["reflective", "random", "static"]

    for mode in modes:
        for run_num in range(1, 6):
            result = run_single(mode, run_num)
            all_results.append(result)

            # Save aggregate
            with open(os.path.join(RESULTS_DIR, "all_results.json"), "w") as f:
                json.dump(all_results, f, indent=2)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for mode in modes:
        mr = [r for r in all_results if r["mode"] == mode]
        accs = [r["test_accuracy"] for r in mr]
        mean = sum(accs) / len(accs) if accs else 0
        print(f"{mode:12s}: mean_test={mean:.1%}  runs={[f'{a:.1%}' for a in accs]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["reflective", "random", "static"])
    parser.add_argument("--run", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    if args.all:
        run_all()
    elif args.mode:
        run_single(args.mode, args.run)
    else:
        parser.print_help()
