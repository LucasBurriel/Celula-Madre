#!/usr/bin/env python3
"""V7 Minimal Proof-of-Concept: 2 groups, small scale, fast model.

Goal: Prove the V7 machinery works end-to-end and get preliminary results.
Scale: pop=4, gens=5, dev=10, val=10, test=20, max_turns=3
Groups: tournament_reflective vs tournament_random
Model: gemma-3-4b (faster than qwen3-30b for negotiation)
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.negotiation import call_llm, generate_splits, save_scenarios, load_scenarios
from src.evolution_v7 import EvolutionEngineV7

# Config
MODEL = "google/gemma-3-4b"
BASE_URL = "http://172.17.0.1:1234"
POP_SIZE = 4
NUM_GENS = 5
DEV_SCENARIOS = 10
VAL_SCENARIOS = 10
TEST_SCENARIOS = 20
MAX_TURNS = 3
RESULTS_BASE = "results/v7_minimal"

def fast_llm(system_prompt, user_prompt, **kwargs):
    """Use gemma-3-4b for speed."""
    max_tokens = kwargs.get("max_tokens", 300)
    return call_llm(system_prompt, user_prompt, model=MODEL, base_url=BASE_URL,
                    max_tokens=max_tokens, temperature=0.7)


def run_group(mode: str, scenarios: dict):
    """Run one group experiment."""
    results_dir = os.path.join(RESULTS_BASE, mode)
    os.makedirs(results_dir, exist_ok=True)
    
    engine = EvolutionEngineV7(
        mode=mode,
        population_size=POP_SIZE,
        num_generations=NUM_GENS,
        elite_count=1,
        tournament_k=2,
        dev_scenarios=DEV_SCENARIOS,
        val_scenarios=VAL_SCENARIOS,
        max_turns=MAX_TURNS,
        results_dir=results_dir,
        llm_fn=fast_llm,
    )
    
    print(f"\n{'#'*60}")
    print(f"# V7 Minimal: {mode}")
    print(f"# Pop={POP_SIZE}, Gens={NUM_GENS}, Dev={DEV_SCENARIOS}, Val={VAL_SCENARIOS}")
    print(f"# Model: {MODEL}")
    print(f"{'#'*60}\n")
    
    t0 = time.time()
    result = engine.run(scenarios, resume=True)
    elapsed = time.time() - t0
    
    print(f"\n⏱️  {mode} completed in {elapsed/60:.1f} minutes")
    print(f"   Best test score: {result['test_accuracy']:.2%}")
    print(f"   Best test deal rate: {result['test_deal_rate']:.0%}")
    
    return result


def main():
    os.makedirs(RESULTS_BASE, exist_ok=True)
    
    # Generate or load scenarios
    scenario_path = os.path.join(RESULTS_BASE, "scenarios.json")
    if os.path.exists(scenario_path):
        scenarios = load_scenarios(scenario_path)
    else:
        scenarios = generate_splits(seed=42)
        save_scenarios(scenarios, scenario_path)
    # Trim to minimal size
    scenarios = {
        "dev": scenarios["dev"][:DEV_SCENARIOS],
        "val": scenarios["val"][:VAL_SCENARIOS],
        "test": scenarios["test"][:TEST_SCENARIOS],
    }
    print(f"Scenarios: dev={len(scenarios['dev'])}, val={len(scenarios['val'])}, test={len(scenarios['test'])}")
    
    # Test LLM connectivity
    print("Testing LLM connectivity...")
    try:
        resp = fast_llm("You are helpful.", "Say 'OK' in one word.")
        print(f"  LLM OK: {resp[:50]}")
    except Exception as e:
        print(f"  LLM FAILED: {e}")
        sys.exit(1)
    
    # Run both groups
    all_results = {}
    
    for mode in ["tournament_reflective", "tournament_random"]:
        try:
            result = run_group(mode, scenarios)
            all_results[mode] = result
        except Exception as e:
            print(f"\n❌ {mode} FAILED: {e}")
            import traceback
            traceback.print_exc()
            all_results[mode] = {"error": str(e)}
    
    # Summary
    print(f"\n{'='*60}")
    print("V7 MINIMAL RESULTS SUMMARY")
    print(f"{'='*60}")
    for mode, result in all_results.items():
        if "error" in result:
            print(f"  {mode}: FAILED - {result['error']}")
        else:
            print(f"  {mode}: test={result['test_accuracy']:.2%}, deal_rate={result['test_deal_rate']:.0%}")
            # Gen-over-gen
            for h in result.get("history", []):
                print(f"    Gen {h['generation']}: mean={h['mean_score']:.2%}, best={h['best_score']:.2%}")
    
    # Save summary
    with open(os.path.join(RESULTS_BASE, "summary.json"), "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\nResults saved to {RESULTS_BASE}/")


if __name__ == "__main__":
    main()
