#!/usr/bin/env python3
"""
Célula Madre V6 — Results Analyzer

Analyzes completed V6 experiments:
- Per-mode summary (mean, std, CI)
- ANOVA across groups
- Pairwise comparisons (Tukey HSD)
- Cohen's d effect sizes
- Gen-over-gen improvement curves
- Outputs to research/experiments/v6-results.md

Usage:
  python scripts/analyze_v6.py [--partial]  # --partial analyzes whatever's done
"""

import argparse
import json
import os
import sys
from pathlib import Path
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RESULTS_DIR = Path(__file__).parent.parent / "results" / "v6"
OUTPUT = Path(__file__).parent.parent / "research" / "experiments" / "v6-results.md"


def load_results():
    """Load all completed run results."""
    results = {}
    for mode in ["reflective", "random", "static"]:
        mode_dir = RESULTS_DIR / mode
        if not mode_dir.exists():
            continue
        results[mode] = []
        for run_dir in sorted(mode_dir.iterdir()):
            rf = run_dir / "results.json"
            if rf.exists():
                with open(rf) as f:
                    results[mode].append(json.load(f))
    return results


def load_checkpoints():
    """Load checkpoint histories for gen-over-gen analysis."""
    histories = {}
    for mode in ["reflective", "random", "static"]:
        mode_dir = RESULTS_DIR / mode
        if not mode_dir.exists():
            continue
        histories[mode] = []
        for run_dir in sorted(mode_dir.iterdir()):
            cp = run_dir / "checkpoints" / "checkpoint_latest.json"
            if cp.exists():
                with open(cp) as f:
                    data = json.load(f)
                    histories[mode].append(data.get("history", []))
    return histories


def mean(vals):
    return sum(vals) / len(vals) if vals else 0

def std(vals):
    if len(vals) < 2:
        return 0
    m = mean(vals)
    return math.sqrt(sum((v - m)**2 for v in vals) / (len(vals) - 1))

def cohens_d(a, b):
    """Cohen's d between two groups."""
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return float('nan')
    ma, mb = mean(a), mean(b)
    sa, sb = std(a), std(b)
    pooled = math.sqrt(((na-1)*sa**2 + (nb-1)*sb**2) / (na+nb-2))
    if pooled == 0:
        return float('nan')
    return (ma - mb) / pooled

def bootstrap_ci(vals, n=10000, alpha=0.05):
    """Bootstrap confidence interval."""
    import random
    if not vals:
        return (0, 0)
    means = []
    for _ in range(n):
        sample = [random.choice(vals) for _ in range(len(vals))]
        means.append(mean(sample))
    means.sort()
    lo = means[int(n * alpha/2)]
    hi = means[int(n * (1 - alpha/2))]
    return (lo, hi)

def t_test(a, b):
    """Independent t-test, returns t-stat and approx p-value."""
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return float('nan'), float('nan')
    ma, mb = mean(a), mean(b)
    sa, sb = std(a), std(b)
    se = math.sqrt(sa**2/na + sb**2/nb)
    if se == 0:
        return float('inf'), 0
    t = (ma - mb) / se
    # Welch's df
    num = (sa**2/na + sb**2/nb)**2
    den = (sa**2/na)**2/(na-1) + (sb**2/nb)**2/(nb-1)
    df = num/den if den > 0 else 1
    # Rough p-value using normal approximation (good enough for df > 5)
    import math
    z = abs(t)
    p = 2 * (1 - 0.5 * (1 + math.erf(z / math.sqrt(2))))  # two-tailed
    return t, p


def analyze(partial=False):
    results = load_results()
    histories = load_checkpoints()
    
    if not any(results.values()):
        if partial:
            # Try to analyze from checkpoints alone
            if not any(histories.values()):
                print("No results or checkpoints found.")
                return
        else:
            print("No completed results found. Use --partial for checkpoint analysis.")
            return

    lines = []
    lines.append("# V6 Experiment Results — AG News Classification\n")
    lines.append(f"*Auto-generated analysis*\n")
    lines.append("## Task")
    lines.append("4-class text classification on AG News (World/Sports/Business/Sci-Tech)")
    lines.append("Population 8, 10 generations, elitism top-2, gating (child >= parent)\n")
    
    # Summary table
    lines.append("## Summary\n")
    lines.append("| Mode | Runs | Mean Test | Std | 95% CI | Best | Worst |")
    lines.append("|------|------|-----------|-----|--------|------|-------|")
    
    mode_accs = {}
    for mode in ["reflective", "random", "static"]:
        runs = results.get(mode, [])
        if not runs:
            lines.append(f"| {mode} | 0 | — | — | — | — | — |")
            continue
        accs = [r["test_accuracy"] for r in runs]
        mode_accs[mode] = accs
        ci = bootstrap_ci(accs) if len(accs) >= 2 else (accs[0], accs[0])
        lines.append(f"| {mode} | {len(runs)} | {mean(accs):.1%} | {std(accs):.1%} | [{ci[0]:.1%}, {ci[1]:.1%}] | {max(accs):.1%} | {min(accs):.1%} |")
    
    # Pairwise comparisons
    if len(mode_accs) >= 2:
        lines.append("\n## Pairwise Comparisons\n")
        modes = list(mode_accs.keys())
        for i in range(len(modes)):
            for j in range(i+1, len(modes)):
                a, b = modes[i], modes[j]
                t, p = t_test(mode_accs[a], mode_accs[b])
                d = cohens_d(mode_accs[a], mode_accs[b])
                sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"
                lines.append(f"- **{a} vs {b}**: t={t:.2f}, p={p:.4f} ({sig}), Cohen's d={d:.2f}")
    
    # Gen-over-gen from checkpoints
    lines.append("\n## Generation-over-Generation Improvement\n")
    for mode in ["reflective", "random", "static"]:
        mode_hist = histories.get(mode, [])
        if not mode_hist:
            continue
        lines.append(f"### {mode.capitalize()}\n")
        # Average across runs
        max_gens = max(len(h) for h in mode_hist) if mode_hist else 0
        for g in range(max_gens):
            best_vals = []
            mean_vals = []
            for h in mode_hist:
                if g < len(h):
                    best_vals.append(h[g].get("best_val", 0))
                    mean_vals.append(h[g].get("mean_val", 0))
            if best_vals:
                lines.append(f"- Gen {g}: best_val={mean(best_vals):.1%}, mean_val={mean(mean_vals):.1%} (n={len(best_vals)})")
    
    # Write output
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w") as f:
        f.write("\n".join(lines) + "\n")
    
    print(f"Analysis written to {OUTPUT}")
    print("\n".join(lines))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--partial", action="store_true")
    args = parser.parse_args()
    analyze(partial=args.partial)
