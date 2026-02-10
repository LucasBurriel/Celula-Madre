# V4 Conclusions & V5 Design Decisions

**Date:** 2026-02-09
**Author:** Tesla ⚡

## V4 Verdict: Guided Evolution Failed — But We Learned Why

### The Result
Control (random mutation) earned **2.3x more profit** than experimental (guided mutation). p < 0.0001, Cohen's d = -2.01. This isn't marginal — it's a demolition.

### The Three Killers

**1. Over-exploration without exploitation**
Guided mutation spawned 24 agents vs control's 11. Each agent got ~8 transactions on average — not enough data to evaluate fitness, let alone select. The "improvement" signal was noise. Random mutation, constrained by fewer agents, accidentally achieved better exploitation: fewer agents → more data per agent → better natural selection.

**2. No elitism**
Both groups retired entire generations. But this hurt guided more because it kept producing variants that needed proving. The control's simpler structure meant its survivors accumulated more transactions before being replaced.

**3. Feedback overfitting**
The LLM analyzed client complaints and "improved" prompts accordingly. But client scores were stochastic — the LLM was fitting to noise, producing increasingly specialized-but-fragile prompts. Gen0 (hand-crafted) remained the experimental group's best generation.

### What V4 Validated
- The marketplace simulation works mechanically
- Agents compete, earn revenue, get selected
- Population dynamics (agent count, txs/agent) matter more than mutation quality
- LLM-generated "random" mutations aren't actually random — they have structural intelligence

### What V4 Refuted
- ❌ LLM-guided mutation from market feedback → better agents (at this scale)
- ❌ More agents = better exploration
- ❌ Direct feedback analysis = good mutation signal

## V5 Design Decisions

### Decision 1: Switch to Real Data (BTC/ETH Prediction)
**Why:** The simulated marketplace had two fatal flaws: (a) client scoring was stochastic, providing noisy fitness signal, and (b) "code quality" evaluation by an LLM is inherently subjective. 

Real price prediction has **deterministic ground truth**: price went up or down. This gives us a clean fitness function. If reflective mutation can't improve agents against clean signal, the approach is fundamentally broken.

**Implementation:** Historical BTC/ETH OHLCV data → predict next-day direction → accuracy = fitness.

### Decision 2: GEPA-Style Reflective Mutation (Not Feedback-Based)
**Why:** V4's guided mutation analyzed *client complaints* — noisy, subjective signal. GEPA-style reflection analyzes *the agent's own reasoning trajectory against ground truth*. The agent sees: "I predicted UP because of X, Y, Z. Price actually went DOWN. Here's what I missed." This is a fundamentally richer signal.

**Key difference:** V4 = "clients said your code was bad" → improve. V5 = "you predicted wrong because your analysis missed the volume spike" → improve.

### Decision 3: Mandatory Gating
**Why:** V4 never gated — every mutant entered the population. V5 gates: a child prompt must score ≥ parent on the dev set before it can replace the parent. This prevents regression and naturally limits over-exploration.

### Decision 4: Elitism + Smaller Population
**Why:** V4's experimental group had 24 agents. V5 will have 8, with the top 2 always surviving to the next generation unchanged. This ensures exploitation of proven strategies while still allowing exploration.

**Parameters:**
- Population: 8 agents
- Elitism: top 2 survive unchanged
- Mutation: 4 agents mutated via reflection
- New: 2 fresh agents (diversity injection)
- Gating: child ≥ parent on dev set

### Decision 5: Fitness Sharing (Pareto Diversity)
**Why:** Even with elitism, a single dominant strategy can take over. Fitness sharing penalizes agents that are too similar to each other, maintaining a diverse frontier. Track performance across market regimes (bull, bear, sideways) and preserve specialists.

### Decision 6: Train/Dev/Val/Test Split
**Why:** V4 had no holdout — agents were evaluated on the same data they "trained" on. V5 separates:
- **Dev set:** Used for gating (child vs parent)
- **Val set:** Used for generation-level selection
- **Test set:** Final evaluation, never seen during evolution

### Decision 7: All Local (Qwen3, $0 Cost)
**Why:** V5 uses Qwen3-30B for both agent execution and reflective mutation. Zero API cost means we can run longer experiments without budget constraints. If results are promising, we can later test with stronger models.

## V5 Architecture Summary

```
Historical Data (BTC/ETH OHLCV)
    ↓
Train/Dev/Val/Test Split
    ↓
┌─────────────────────────────────┐
│ Generation Loop (10-20 gens)    │
│                                 │
│  1. Evaluate all agents on dev  │
│  2. Rank by accuracy            │
│  3. Top 2 → elite (survive)    │
│  4. Next 4 → reflect + mutate  │
│     - See own failures          │
│     - Propose improved prompt   │
│     - Gate: child ≥ parent?     │
│  5. Bottom 2 → replace with    │
│     fresh random agents         │
│  6. Fitness sharing adjustment  │
│  7. Validate on val set         │
│  8. Log everything              │
└─────────────────────────────────┘
    ↓
Final evaluation on test set
    ↓
Compare: Gen0 vs GenN vs random baseline
```

## Success Criteria for V5

1. **Primary:** Final-generation agents outperform Gen0 on test set (direction accuracy)
2. **Secondary:** Reflective mutation produces better children than random mutation (A/B within V5)
3. **Tertiary:** Population maintains diversity (≥3 distinct strategy types in final gen)

If V5 meets criterion 1, reflective mutation works. If it meets 1+2, it works *better* than random. If it meets all three, we have a publishable result.

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| BTC prediction is too hard for any prompt | Medium | Use longer context (30d), allow "uncertain" predictions |
| Qwen3-30B too weak for reflection | Low | Already shown capable in V4 mutations |
| Overfitting to historical patterns | Medium | Strict train/test separation, multiple time periods |
| Not enough data | Low | BTC has 10+ years of daily data |

## Timeline
- TASK-003: Data pipeline (fetch + split)
- TASK-004: Agent evaluation framework  
- TASK-005: Evolution loop implementation
- TASK-006: Run experiment + analyze

---

*V4 taught us that smart mutation without smart selection is worse than dumb mutation. V5 fixes the selection.*
