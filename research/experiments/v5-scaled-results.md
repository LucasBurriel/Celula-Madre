# V5 Scaled Results — Analysis

**Date:** 2026-02-10
**Status:** In progress (Run 3 still executing)

## Runs Summary

| Run | Config | Status | Best Val | Best Test | Notes |
|-----|--------|--------|----------|-----------|-------|
| Run 1 | pop=4, gens=3, dev=10, val=10 | ✅ Complete | 70% | 59.4% | Mean-reversion agent |
| Run 2 | pop=6, gens=5, dev=20, val=20 | ❌ Died Gen 1 | 75% (Gen 0) | N/A | Timeout/kill |
| Run 3 | pop=4, gens=5, dev=20, val=20 | 🔄 Running | TBD | TBD | Started 09:04 |

## Baselines

| Baseline | Test Accuracy | Notes |
|----------|--------------|-------|
| Random (coin flip) | 49.9% ± 5% | 1000 simulations, 95% CI [41.6%, 58.4%] |
| Always DOWN | 58.4% | Majority class in test set |
| Always UP | 41.6% | Minority class |
| **Best V5 agent** | **59.4%** | Mean-reversion, p=0.038 vs random |

## Critical Finding: Class Imbalance

The test set is imbalanced: **58.4% DOWN, 41.6% UP** (101 examples).

The best V5 agent (59.4%) barely beats the "always DOWN" naive baseline (58.4%) by **1 percentage point**. This suggests the agent may have learned to predict DOWN most of the time rather than developing genuine market insight.

**Against random baseline:** p=0.038 (significant at α=0.05)
**Against majority-class baseline:** +1.0% (not meaningful)

## Evolution Dynamics

### No generational improvement
From Run 1 (the only complete run):
- Gen 0 best val: 70%
- Gen 1 best val: 70% (same agent, no improvement)
- Gen 2 best val: 70% (same agent, still no improvement)

The best agent was **always the Gen 0 seed** (mean-reversion). Evolution produced no improvement over initial seed strategies.

### Mutation gating too strict
- Most mutations were rejected (child didn't beat parent on dev set)
- With dev_batch=10-20, evaluation is too noisy to distinguish genuine improvements
- A real improvement of 5% would need ~400 examples to detect at p<0.05

### Merges unsuccessful
- Run 1: 1 merge survived (Agent 10) but only matched parent performance
- Run 2: Both merges rejected (val 52% < threshold)
- Merge requires outperforming the average of both parents — high bar with noisy evals

## Variance Problem

With small batch sizes, agent accuracy varies wildly across evaluations:
- Run 1, Agent 1: Gen 0 val=70%, Gen 2 val=30% (same agent, same strategy!)
- This 40% swing means gating decisions are essentially random

**Root cause:** Binomial variance. For n=20, σ ≈ 11%. A "true 55%" agent will score anywhere from 33% to 77% on a given batch.

## Architectural Assessment

The V5 framework (elitism, gating, Pareto frontier, reflective mutation, merge) is **mechanically sound** but faces fundamental limitations:

1. **Evaluation noise:** LLM predictions on 20-30 examples are too noisy for evolution to work. Need 200+ examples per eval, but that's prohibitively slow with Qwen3-30B (~90s per example).

2. **Task difficulty:** BTC direction prediction may not be learnable from price history alone (efficient market hypothesis). Even sophisticated quantitative strategies barely beat random.

3. **Prompt space limitations:** The strategy space reachable by mutating system prompts is narrow. LLMs interpret prompts inconsistently, adding another noise layer.

4. **Speed constraint:** Full eval (100 examples) takes ~25 min per agent. A serious run (pop=8, gens=10) with proper eval would take ~33 hours.

## Recommendations for V6

1. **Switch to a learnable task:** Use a domain where strategy clearly matters (e.g., text classification, customer segmentation, code review). This isolates evolution effectiveness from task learnability.

2. **Reduce evaluation noise:** Either use a faster model (flash-tier) or a non-LLM fitness function. If keeping LLMs, need 200+ examples.

3. **Softer gating:** Instead of binary gate (child >= parent), use probabilistic acceptance (simulated annealing style). Accept slightly worse children with decreasing probability.

4. **Separate evolution proof from market prediction:** Prove the evolution mechanism works on a task with known optimal strategies before applying to hard problems.

## Raw Data

### Run 1 Gen-over-gen
```
Gen 0: mean_val=55%, best_val=70%, mean_dev=32%, frontier=3
Gen 1: mean_val=57%, best_val=70%, mean_dev=35%, frontier=3
Gen 2: mean_val=48%, best_val=70%, mean_dev=45%, frontier=3
```

### Run 2 Gen 0 (pop=6)
```
Agent 0: dev=50% val=75% wins=15
Agent 1: dev=30% val=60% wins=3
Agent 2: dev=45% val=65% wins=1
Agent 3: dev=40% val=55% wins=1
Agent 4: dev=50% val=40% wins=0
Agent 5: dev=50% val=45% wins=0
```

### Random Baseline Distribution
- Mean: 49.9%
- 95% CI: [41.6%, 58.4%]
- P(random >= 59.4%) = 3.8%
- Test set: 101 examples, 41.6% UP / 58.4% DOWN
