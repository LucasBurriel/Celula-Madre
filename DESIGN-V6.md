# DESIGN-V6: Proving Evolution Works

**Date:** 2026-02-10
**Author:** Tesla ⚡
**Goal:** Isolate and prove that the evolutionary mechanism (reflective mutation + selection) produces measurable improvement over random mutation and static seeds.

## Why V6?

V4 showed random > guided (but both were marketplace simulations with high noise).
V5 showed the framework works mechanically, but BTC prediction was the wrong testbed:
- Near-random task (EMH makes it ~50/50)
- Class imbalance masked non-learning
- 20 examples per eval = ±20% noise, can't detect real improvement
- Best agent was always Gen 0 seed — evolution added nothing

**V6 must answer one question:** Does reflective mutation + selection produce better prompts than random mutation + selection, on a task where improvement is actually possible?

## Task Selection: Multi-Class Text Classification (AG News)

### Why AG News?
- **4-class news classification** (World, Sports, Business, Sci/Tech) — well-studied, clear ground truth
- **Strategy matters:** prompt engineering genuinely affects accuracy (naive ~70%, good prompt ~85%+)
- **Room to improve:** unlike BTC prediction, there's a 15+ point gap between naive and optimal
- **Fast eval:** short texts, deterministic labels, no domain expertise needed
- **Large dataset:** 7600 test examples — can use 200+ per eval with no noise problems
- **No API cost for data:** freely available, included in many NLP benchmarks

### Why not other tasks?
- **Sentiment (SST-2):** binary, too easy for LLMs (>90% with any prompt), little room for evolution
- **Code review:** slow eval, complex outputs, hard to score automatically
- **Summarization:** no clear ground truth, needs human eval
- **Math/reasoning:** interesting but evaluating prompt quality is confounded with model capability

## Experiment Design

### Core Comparison (3 groups, 5 runs each)

| Group | Mutation | Selection | Purpose |
|-------|----------|-----------|---------|
| **Experimental** | Reflective (GEPA-style: analyze errors → improve) | Elitism + gating | Does guided evolution work? |
| **Control-Random** | Random LLM mutation (no error analysis) | Same elitism + gating | Is reflection the key ingredient? |
| **Control-Static** | No mutation (keep seeds forever) | Same selection | Does ANY mutation help? |

### Parameters
- Population: 8
- Generations: 10
- Dev set: 100 examples (eval fitness)
- Val set: 100 examples (gating: child must beat parent)
- Test set: 200 examples (final evaluation, never seen during evolution)
- Runs per group: 5 (for statistical power)
- Total: 15 runs

### Evaluation Metrics
- **Primary:** Test accuracy (4-class)
- **Secondary:** Per-class F1 (to detect if agents specialize)
- **Evolution dynamics:** Best fitness per generation, population diversity (prompt similarity), mutation acceptance rate

### Statistical Analysis
- **Between groups:** One-way ANOVA + Tukey HSD on best-test-accuracy across 5 runs
- **Within group:** Paired t-test Gen 0 best vs Gen 10 best (did evolution improve?)
- **Effect size:** Cohen's d for experimental vs each control
- **Power:** With 5 runs, can detect d=1.5 at 80% power — sufficient for "does it work at all?"

## Data Pipeline

```
AG News dataset (from HuggingFace or CSV)
→ Shuffle with fixed seed
→ Split: dev=100, val=100, test=200, pool=remaining
→ Format: {"text": "...", "label": "World|Sports|Business|SciTech"}
→ Agent gets text, must output one of 4 labels
→ Score: exact match
```

## Agent Design

### Seed Strategies (Gen 0, shared across all groups)
1. **Vanilla:** "Classify this news article into one of: World, Sports, Business, Sci/Tech."
2. **Chain-of-thought:** "Read the article. Think step by step about the topic. Output: [category]."
3. **Keyword-based:** "Look for keywords that indicate the category..."
4. **Structured:** "First identify the subject, then the domain, then classify."
5-8: Minor variations of above

### Reflective Mutation (Experimental only)
```
Given your current prompt and these examples you got WRONG:
[show 5-10 misclassified examples with correct labels]

Analyze WHY you got these wrong. What pattern did you miss?
Write an improved version of your prompt that addresses these failures.
```

### Random Mutation (Control-Random)
```
Here is a prompt for text classification:
[current prompt]

Write a different version that might work better. Change the approach, wording, or structure.
Do NOT see any examples or error analysis.
```

## Implementation Notes

- Reuse V5 EvolutionEngine with minimal changes (swap task, add control groups)
- AG News data: download once, cache locally
- Eval function: send text + agent prompt to LLM, parse label, compare
- **Model for agents:** Qwen3-30B via LM Studio (same as V5, proven to work)
- **Model for mutation:** Same Qwen3-30B
- **Speed estimate:** ~1.5s per example × 100 dev × 8 agents = ~20 min per generation → ~3.5 hours per run → ~17 hours per group → ~52 hours total (can parallelize across days)

## Success Criteria

**V6 succeeds if:**
1. Experimental group shows statistically significant improvement Gen 0 → Gen 10 (p < 0.05)
2. Experimental beats Control-Static (evolution helps) with d > 0.8
3. Experimental beats Control-Random (reflection helps) with d > 0.5

**V6 partially succeeds if:**
- Both Experimental and Control-Random beat Static (evolution works, but reflection doesn't add much)
- This would still validate the core Célula Madre thesis: LLM-based evolution > static agents

**V6 fails if:**
- No group improves over Gen 0 seeds → problem is in the framework, not the task
- This would require fundamental rethinking

## Timeline
- TASK-009: This design document ✅
- TASK-010: Implement data pipeline + eval for AG News
- TASK-011: Implement 3-group experiment runner
- TASK-012: Run all 15 experiments + analysis
- TASK-013: Write results paper (if successful)

---

*The point of V6 isn't to solve text classification. It's to prove that evolutionary prompt optimization works, period. Once proven, we can apply it to harder problems with confidence.*
