#!/usr/bin/env python3
"""
Célula Madre V6 — Statistical Analysis

Analyzes completed V6 experiment results:
- ANOVA across 3 groups (reflective, random, static)
- Tukey HSD post-hoc
- Cohen's d effect sizes
- Gen-over-gen improvement curves
- Best agent comparison
"""

import json
import os
import sys
import numpy as np
from pathlib import Path

RESULTS_DIR = Path(__file__).parent.parent / "results" / "v6"

def load_all_results():
    """Load all completed run results."""
    results = {}
    for mode in ["reflective", "random", "static"]:
        mode_dir = RESULTS_DIR / mode
        if not mode_dir.exists():
            continue
        runs = []
        for run_dir in sorted(mode_dir.iterdir()):
            rf = run_dir / "results.json"
            if rf.exists():
                with open(rf) as f:
                    runs.append(json.load(f))
        if runs:
            results[mode] = runs
    return results

def load_checkpoints(mode, run_num):
    """Load generation-by-generation data from checkpoints."""
    cp_dir = RESULTS_DIR / mode / f"run_{run_num}" / "checkpoints"
    gens = []
    for i in range(20):
        cp = cp_dir / f"checkpoint_gen{i}.json"
        if cp.exists():
            with open(cp) as f:
                gens.append(json.load(f))
    return gens

def cohens_d(a, b):
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return float('nan')
    pooled_std = np.sqrt(((na-1)*np.std(a,ddof=1)**2 + (nb-1)*np.std(b,ddof=1)**2) / (na+nb-2))
    if pooled_std == 0:
        return float('inf') if np.mean(a) != np.mean(b) else 0
    return (np.mean(a) - np.mean(b)) / pooled_std

def main():
    results = load_all_results()
    
    if not results:
        # Check for in-progress runs
        print("No completed results yet. Checking in-progress runs...")
        for mode in ["reflective", "random", "static"]:
            mode_dir = RESULTS_DIR / mode
            if not mode_dir.exists():
                continue
            for run_dir in sorted(mode_dir.iterdir()):
                cp_dir = run_dir / "checkpoints"
                if cp_dir.exists():
                    cps = sorted(cp_dir.glob("checkpoint_gen*.json"))
                    if cps:
                        latest = cps[-1]
                        with open(latest) as f:
                            d = json.load(f)
                        pop = d.get("population", [])
                        best_val = max((a.get("val_accuracy", 0) for a in pop), default=0)
                        print(f"  {mode}/{run_dir.name}: gen {d['generation']}, best_val={best_val:.1%}, agents={len(pop)}")
        return

    print("=" * 70)
    print("CÉLULA MADRE V6 — EXPERIMENT RESULTS")
    print("=" * 70)
    
    # Summary per mode
    for mode, runs in results.items():
        test_accs = [r["test_accuracy"] for r in runs]
        print(f"\n{mode.upper()} ({len(runs)} runs):")
        print(f"  Test accuracy: {np.mean(test_accs):.1%} ± {np.std(test_accs):.1%}")
        print(f"  Range: [{min(test_accs):.1%}, {max(test_accs):.1%}]")
        for r in runs:
            print(f"    Run {r.get('run_num','?')}: test={r['test_accuracy']:.1%} ({r.get('elapsed_hours','?')}h)")

    # ANOVA
    modes = list(results.keys())
    if len(modes) >= 2:
        from scipy import stats
        groups = [np.array([r["test_accuracy"] for r in results[m]]) for m in modes]
        
        if len(modes) >= 3 and all(len(g) >= 2 for g in groups):
            f_stat, p_val = stats.f_oneway(*groups)
            print(f"\n--- ONE-WAY ANOVA ---")
            print(f"F={f_stat:.3f}, p={p_val:.4f}")
            if p_val < 0.05:
                print("→ Significant difference between groups (p<0.05)")
            else:
                print("→ No significant difference (p≥0.05)")
        
        # Pairwise comparisons
        print(f"\n--- PAIRWISE (t-test, Cohen's d) ---")
        for i in range(len(modes)):
            for j in range(i+1, len(modes)):
                a, b = groups[i], groups[j]
                if len(a) >= 2 and len(b) >= 2:
                    t, p = stats.ttest_ind(a, b)
                    d = cohens_d(a, b)
                    print(f"  {modes[i]} vs {modes[j]}: t={t:.3f}, p={p:.4f}, d={d:.3f}")

    # Gen-over-gen analysis
    print(f"\n--- GENERATIONAL IMPROVEMENT ---")
    for mode in modes:
        mode_dir = RESULTS_DIR / mode
        for run_dir in sorted(mode_dir.iterdir()):
            gens = load_checkpoints(mode, run_dir.name.split("_")[1])
            if gens:
                best_vals = []
                for g in gens:
                    pop = g.get("population", [])
                    bv = max((a.get("val_accuracy", 0) for a in pop), default=0)
                    best_vals.append(bv)
                print(f"  {mode}/{run_dir.name}: {' → '.join(f'{v:.0%}' for v in best_vals)}")

    print(f"\n{'='*70}")

if __name__ == "__main__":
    main()
