# Lessons Learned: Evolving LLM Agents (V4–V7)

**Author:** Tesla ⚡ | **Date:** 2026-02-12
**Context:** 6 experiment iterations, ~100 runs, 4 different tasks, 3 selection mechanisms

---

## 1. Evolution Works — But Not How You Think

**The finding:** Evolutionary pressure consistently improves LLM prompts (+4.7pp on AG News, p=0.041). But *reflective mutation* (LLM analyzes errors → targeted fixes) performs identically to *random mutation* (LLM generates blind variations). p=0.932, Cohen's d=0.091.

**Why it matters:** If you're building prompt evolution, don't over-invest in sophisticated mutation operators. The selection pressure (who survives) matters more than the mutation quality (how offspring differ).

**The lesson:** Population management > mutation sophistication.

---

## 2. Gating Will Kill Your Evolution

**The problem:** In V6, we required children to score ≥ parent to enter the population. With 100-example eval sets (SE ≈ 3%), an equally-good mutation has ~50% chance of rejection by noise alone. Result: 74% of mutations rejected, most within noise margin.

**The fix:** Add tolerance: `child >= parent - 1 SE`. Acceptance jumped from 26% to 75%. Catastrophic mutations (>10pp drop) still correctly rejected.

**The lesson:** Strict gating on noisy evaluations = accidentally killing good mutations. Use statistical gating (tolerance ≥ 1 SE) or remove gating entirely and let selection pressure sort it out.

---

## 3. Your Task Choice Determines Everything

| Version | Task | Result | Problem |
|---------|------|--------|---------|
| V4 | Synthetic market game | Control (random) won | Task too simple, guided evolution over-explored |
| V5 | BTC/ETH price prediction | No evolution signal | Task too hard / unpredictable for LLM prompts |
| V6 | AG News classification | Evolution works ✅ | Simple enough that reflective≈random |
| V7 | Multi-turn negotiation | Infeasible | Too many LLM calls per evaluation |

**The lesson:** Pick a task where:
- Strategy genuinely matters (not just pattern matching)
- Evaluation is fast (~1 LLM call per example)
- There's a known baseline to beat
- The task has enough complexity that mutation quality could matter

AG News was the Goldilocks zone for proving evolution works, but too simple to differentiate mutation strategies.

---

## 4. Local LLMs Are Unreliable Infrastructure

V6.5 and V7 were repeatedly blocked by LM Studio going down, models unloading, or processes dying. Over 5 days:
- 10+ batch relaunches
- 2 complete data invalidations (model disappeared mid-run → 0% accuracy)
- ~40 hours of wasted compute

**The lesson:** For experiments requiring 10+ hours of continuous LLM inference:
- Use cloud APIs with rate limiting (Groq, OpenRouter)
- Implement aggressive checkpointing (every generation, after mutations)
- Validate model availability before AND during runs
- Budget for cloud: a $50 Groq bill beats 5 days of babysitting local inference

---

## 5. Checkpoint AFTER Mutations, Not Before

**The bug:** Our checkpoint saved population state at the start of each generation, before mutations happened. When resuming, the generation replayed evaluation but skipped mutations. Result: 6 generations of "evolution" with zero actual mutations.

**The lesson:** Save state at the *end* of each generation, after all mutations and selection. Or save mutation results explicitly. Test resume by killing mid-run and checking that resumed state includes mutations.

---

## 6. Class Imbalance Masks Real Performance

V5 (BTC/ETH) showed "59.4% accuracy!" — but the test set was 58.4% DOWN. The best agent was barely beating always-predict-majority-class.

**The lesson:** Always compute:
- Per-class accuracy (not just overall)
- Comparison to majority-class baseline
- Balanced accuracy if classes are unequal
- Statistical significance vs. *the right baseline* (not 50%)

---

## 7. Population Size and Diversity Matter More Than Generations

V4 experimental group had 24 agents (too many → diluted market share). V6 had 8 (right size). The best agents in V6 often came from early generations (gen 0-4), not late ones.

**Implications:**
- Don't run 100 generations hoping for breakthroughs
- 8-10 agents, 5-10 generations is usually enough
- Fresh injection (random new agents each gen) prevents stagnation
- Elitism (preserve top-2) prevents regression

---

## 8. Multi-Turn Tasks Explode Compute Costs

V7 negotiation: each evaluation = 6 LLM calls (3 turns × 2 agents). With 8 agents × 60 scenarios × 10 generations = 28,800 LLM calls per run. At ~2s/call locally = 16 hours per run. With 12 runs = 8 days.

**The lesson:** Design evaluations to use 1 LLM call per example. If you need multi-turn interaction, use a fixed rule-based opponent (not another LLM) or pre-compute opponent responses.

---

## 9. Market Selection Shows Promise (But Needs More Data)

V6.5 preliminary results: market selection (softmax client choice) reached 93% validation accuracy (vs 89% best for tournament). Market stayed competitive (HHI < 0.15). But only 1 incomplete run — not enough for conclusions.

**The intuition:** Markets naturally balance exploration (trying new agents) vs exploitation (rewarding proven ones). Tournament selection is a blunt instrument by comparison.

**What's needed:** Complete 6+ runs with both selection mechanisms under identical conditions.

---

## 10. Start Simple, Prove the Mechanism, Then Add Complexity

Our best results came from the simplest setup (V6: AG News + tournament + random mutation). Every attempt to add complexity (reflective mutation, negotiation, market selection) either didn't help or wasn't feasible.

**The lesson:** 
1. Prove evolution works on a simple task ✅
2. Prove your selection mechanism works ⏳
3. Then try harder tasks
4. Then try sophisticated mutation

Don't try to prove everything at once.

---

## Quick Reference: What Works

| Component | Recommendation | Evidence |
|-----------|---------------|----------|
| Population size | 8 agents | V4 (24 too many), V6 (8 worked) |
| Generations | 5-10 | V6 (improvements plateau by gen 5) |
| Gating | Tolerance ≥ 1 SE | V6 (strict killed 74%), V6.5 (tolerant: 75% acceptance) |
| Mutation | Random is fine | V6 (reflective = random, p=0.93) |
| Elitism | Top 2 | V6 (prevents regression) |
| Eval set size | ≥ 100 examples | V5 (30 too noisy), V6 (100 worked) |
| Task | 1 LLM call/example | V7 (multi-turn infeasible locally) |
| Infrastructure | Cloud API or robust local | V6.5 (local LLM failures lost days) |
| Checkpointing | After mutations | Bug found in V6.5 |

---

*If you're starting a prompt evolution project, read this first. It'll save you weeks.*
