# V5 Results Analysis — BTC Direction Prediction

**Date:** 2026-02-10
**Run:** `results/v5_bitcoin_20260210_040820/`
**Duration:** ~40 min (3 gens × ~5 min/gen)

## Configuration

| Parameter | Value |
|-----------|-------|
| Population | 4 |
| Generations | 3 |
| Elite count | 2 |
| Dev batch | 10 examples |
| Val batch | 10 examples |
| Test set | 101 examples |
| Asset | BTC daily OHLCV |
| LLM | Qwen3-30B-A3B (local) |

## Key Results

### Best Agent: Mean-Reversion (Agent 1, Gen 0)
- **Test accuracy: 59.4%** (60/101) — above random baseline (50%)
- Val accuracy fluctuated: 70% → 70% → 30% across generations (noise from small val set)
- Strategy: compare price to 30-day average, predict reversion after 3+ days of movement

### Generation Summary

| Gen | Mean Val | Best Val | Evolved Agents | Duration |
|-----|----------|----------|----------------|----------|
| 0 | 55.0% | 70% | 0 | 256s |
| 1 | 57.5% | 70% | 0 | 289s |
| 2 | 47.5% | 70% | 1 (merge) | 293s |

### Evolution Dynamics
- **No mutations passed gating** in Gen 0-1. All new agents were fresh injections.
- **One successful merge** in Gen 2: Agent 10 (volatility × trend hybrid) reached 70% val.
- Gating was too strict with dev_batch=10 (high variance makes it hard to beat parent consistently).
- Elitism preserved Agent 1 across all generations — worked as intended.

### Pareto Frontier
Three strategies on the frontier, differentiated by which market instances they win:
1. **Trend-following** (Agent 0): wins instances [1, 3, 6]
2. **Mean-reversion** (Agent 1): wins instances [9, 2, 5]  
3. **Volatility-focused** (Agent 2): wins instance [4]

This confirms V5's diversity mechanism works — different strategies win different market conditions.

## Comparison with V4

| Metric | V4 Experimental | V4 Control (Random) | V5 |
|--------|----------------|---------------------|-----|
| Task | Service marketplace | Service marketplace | BTC prediction |
| Evolution | Guided mutation | Random mutation | GEPA reflective + gating |
| Best result | 90.81 mean profit | 208.57 mean profit | 59.4% test accuracy |
| Evolution improved? | No (control won) | N/A | Marginal (merge worked once) |

**V5 improvements over V4:**
- Elitism prevented best agent from being lost ✓
- Gating prevented degradation ✓ (but too strict with small samples)
- Pareto frontier maintained diversity ✓
- Population stayed small (4 vs V4's 24 explosion) ✓

**V5 problems:**
- Dev/val sets too small (10 examples) → high variance, unreliable gating
- Only 3 generations → insufficient time for evolution to compound
- Qwen3-30B very slow (~1 min/example) → limits scale
- No mutations passed gating → reflective mutation not validated yet

## Conclusions

1. **V5 framework is mechanically sound.** Elitism, gating, Pareto frontier, and merge all work as designed. The architecture is correct.

2. **Scale is the bottleneck.** With dev_batch=10 and pop=4, there's too much noise and too few evolutionary cycles. Need: larger batches (30-50), more generations (10-20), and faster inference.

3. **Test accuracy of 59.4% is encouraging** but needs statistical validation. With 101 binary examples, a binomial test gives p ≈ 0.03 for 60/101 vs 50% baseline — borderline significant.

4. **Merge produced the most interesting result**: Agent 10 combined volatility + trend into a hybrid that matched the best seed agent. This validates the merge mechanism.

## Next Steps (→ TASK-008+)

1. **Larger scale run:** pop=8, gens=10, dev_batch=30, val_batch=30 (requires faster LLM or patience)
2. **Statistical rigor:** Run 3-5 independent V5 runs, compare distributions
3. **Baseline comparison:** Random strategy baseline on test set (true 50%?)
4. **Faster inference:** Try gemma-3-4b for eval speed, or Qwen3 with `/no_think`
5. **ETH run:** Same framework, different asset — does strategy transfer?
