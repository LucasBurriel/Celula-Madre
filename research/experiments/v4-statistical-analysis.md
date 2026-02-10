# V4 Statistical Analysis: Guided Evolution vs Random Mutation (Control)

**Date:** 2026-02-09
**Author:** Tesla ⚡

## Experiment Overview

V4 tested whether **guided mutation** (LLM-driven prompt evolution based on market feedback) outperforms **random mutation** (shuffled/random prompt changes) in a simulated code marketplace.

- **Experimental group:** 24 agents across 6 generations (Gen0-Gen5), 200 transactions
- **Control group:** 11 agents across 5 generations (Gen0-Gen4), 200 transactions
- Both groups started with identical Gen0 prompts (minimalist, documenter, tester, pragmatist)
- Clients chose agents based on specialization match; agents earned revenue from code tasks

## Key Finding

**The control group (random mutation) dramatically outperformed the experimental group (guided mutation).**

This is the opposite of what we hypothesized.

## Statistical Results

### Net Profit

| Metric | Experimental | Control |
|--------|-------------|---------|
| Mean profit | 90.81 | 208.57 |
| Std dev | 71.48 | 37.58 |
| N agents | 24 | 11 |

- **Welch's t-test:** t = -6.18, p < 0.0001 (highly significant)
- **Cohen's d:** -2.01 (very large effect size)
- **Bootstrap 95% CI** (1000 resamples): mean diff = -118.44, CI = [-154.39, -82.61]

The control group earned **2.3x more profit** on average. The effect is enormous (d > 2.0).

### Transaction Prices

| Metric | Experimental | Control |
|--------|-------------|---------|
| Mean price | 12.87 | 13.01 |
| Median price | 13.00 | 13.00 |

- **t-test:** t = -0.30, p = 0.77 (not significant)
- **Mann-Whitney U:** U = 19496, p = 0.66 (not significant)

Prices were identical between groups — the market didn't pay more for either group's output. The difference is entirely in **volume and selection**, not pricing.

### Temporal Price Trends

| Quartile | Experimental | Control |
|----------|-------------|---------|
| Q1 (txs 1-50) | 12.90 | 12.82 |
| Q2 (txs 51-100) | 12.35 | 12.75 |
| Q3 (txs 101-150) | 13.68 | 12.91 |
| Q4 (txs 151-200) | 12.55 | 13.58 |

No meaningful temporal trends in either group.

## Generation-Over-Generation Trajectory

### Experimental (Guided Mutation)
```
Gen0: 174.5 → Gen1: 80.1 → Gen2: 99.4 → Gen3: 99.3 → Gen4: 32.1 → Gen5: 30.2
```
**Declining trajectory.** Each generation tended to perform worse than its predecessor. Gen0 was the peak.

### Control (Random Mutation)
```
Gen0: 227.7 → Gen1: 208.5 → Gen2: 184.4 → Gen3: 151.0 → Gen4: 238.2
```
**Stable with recovery.** Some decline in mid-generations, but Gen4 bounced back to near-Gen0 levels.

### Best Agent Per Generation

| Gen | Experimental Best | Control Best |
|-----|------------------|-------------|
| 0 | 227.03 | 272.07 |
| 1 | 207.09 | 226.12 |
| 2 | 190.62 | 227.44 |
| 3 | 156.32 | 151.00 |
| 4 | 50.57 | 238.16 |
| 5 | 74.22 | — |

Even the **best** experimental agent in each generation was usually worse than the control's best.

## Population Dynamics

A critical structural difference: Experimental had **24 agents** across 6 generations; Control had **11 agents** across 5 generations. This means:

- Experimental created more agents but spread transactions thinner (avg 8.3 txs/agent)
- Control had fewer agents getting more transactions each (avg 18.2 txs/agent)
- Experimental had agents with **0 transactions** (agent_gen1_1146, agent_gen5_1406)

This suggests guided mutation over-explored: it kept spawning new variants that diluted market share instead of concentrating on winners.

## Why Did Guided Mutation Fail?

### Hypothesis 1: Overfitting to Feedback (Most Likely)
Guided mutation used LLM analysis of market feedback to propose "improvements." But the feedback was noisy (simulated client scores), and the LLM likely overfit to specific complaint patterns, producing increasingly specialized-but-fragile prompts.

### Hypothesis 2: Over-Exploration
24 agents vs 11 — guided mutation explored too aggressively. Each new agent got fewer transactions to prove itself, making the signal-to-noise ratio worse. A vicious cycle: more agents → less data per agent → worse selection → worse next generation.

### Hypothesis 3: Premature Convergence to Local Optima
The LLM-guided mutations may have converged on a narrow strategy space (e.g., "add more documentation" or "add more tests") while random mutations maintained diversity, occasionally hitting good combinations by chance.

### Hypothesis 4: Gen0 Was Already Near-Optimal
The hand-crafted Gen0 prompts (minimalist, documenter, tester, pragmatist) may have been close to optimal for this simple marketplace. Guided mutation tried to "improve" what didn't need improving, while random mutation's occasional good variants survived naturally.

## Implications for Célula Madre

1. **LLM-guided mutation ≠ better mutation.** The core V4 hypothesis is rejected.
2. **Population management matters more than mutation quality.** The control's advantage came from fewer, better-utilized agents.
3. **Need elitism:** Best agents should survive across generations, not get retired.
4. **Need gating:** New mutants should prove they're better before replacing parents.
5. **Exploration-exploitation balance is key.** V4 experimental was all exploration, no exploitation.

## Recommendations for V5

1. **Tournament selection** instead of retiring entire generations
2. **Elitism:** Top N agents always survive to next generation
3. **Gating:** New mutant must beat parent on dev set before entering population
4. **Smaller population** with more transactions per agent
5. **Fitness sharing** to maintain diversity without over-exploration
6. **Consider:** Is reflective mutation (GEPA-style) better than blind LLM feedback analysis?

## Raw Data Summary

### Experimental Agents (all 24)
| Agent | Gen | Revenue | Txs | Profit | Status |
|-------|-----|---------|-----|--------|--------|
| gen0_minimalist | 0 | 207.9 | 18 | 188.96 | retired |
| gen0_documenter | 0 | 223.9 | 17 | 197.94 | retired |
| gen0_tester | 0 | 257.0 | 17 | 227.03 | retired |
| gen0_pragmatist | 0 | 99.0 | 10 | 84.24 | retired |
| gen1_1146 | 1 | 0.0 | 0 | 0.00 | retired |
| gen1_8864 | 1 | 227.5 | 16 | 207.09 | retired |
| gen1_9270 | 1 | 99.9 | 11 | 88.65 | retired |
| gen1_7394 | 1 | 28.0 | 3 | 21.87 | retired |
| gen1_1241 | 1 | 108.4 | 6 | 82.86 | retired |
| gen2_4141 | 2 | 222.0 | 15 | 190.62 | retired |
| gen2_9406 | 2 | 183.4 | 15 | 159.09 | retired |
| gen2_5761 | 2 | 93.2 | 8 | 78.55 | retired |
| gen2_3143 | 2 | 54.8 | 5 | 46.68 | retired |
| gen2_1462 | 2 | 30.0 | 3 | 21.92 | retired |
| gen3_4197 | 3 | 183.9 | 11 | 156.32 | active |
| gen3_8307 | 3 | 159.2 | 13 | 136.63 | active |
| gen3_5724 | 3 | 55.1 | 3 | 35.90 | active |
| gen3_4990 | 3 | 83.9 | 7 | 68.25 | active |
| gen4_1099 | 4 | 74.4 | 5 | 50.57 | active |
| gen4_7092 | 4 | 36.8 | 2 | 19.25 | active |
| gen4_5933 | 4 | 35.6 | 4 | 26.48 | retired |
| gen5_5435 | 5 | 86.2 | 9 | 74.22 | retired |
| gen5_6416 | 5 | 24.0 | 2 | 16.41 | active |
| gen5_1406 | 5 | 0.0 | 0 | 0.00 | active |

### Control Agents (all 11)
| Agent | Gen | Revenue | Txs | Profit | Status |
|-------|-----|---------|-----|--------|--------|
| gen0_minimalist | 0 | 232.2 | 22 | 215.58 | retired |
| gen0_documenter | 0 | 224.7 | 15 | 191.97 | retired |
| gen0_tester | 0 | 311.4 | 19 | 272.07 | retired |
| gen0_pragmatist | 0 | 257.9 | 22 | 231.08 | retired |
| gen1_tx10 | 1 | 210.4 | 15 | 175.68 | retired |
| gen1_tx20 | 1 | 249.0 | 22 | 226.12 | retired |
| gen1_tx50 | 1 | 260.0 | 18 | 223.68 | retired |
| gen2_tx80 | 2 | 156.9 | 15 | 141.45 | retired |
| gen2_tx100 | 2 | 257.4 | 17 | 227.44 | retired |
| gen3_tx150 | 3 | 182.1 | 15 | 151.00 | retired |
| gen4_tx160 | 4 | 260.6 | 20 | 238.16 | retired |
