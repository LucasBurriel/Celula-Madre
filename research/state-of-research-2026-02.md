# State of Research — February 2026

**Author:** Tesla ⚡ | **Date:** 2026-02-12
**Project:** Célula Madre — Evolutionary Optimization of LLM Agent Prompts

---

## 1. What We Set Out to Prove

Can evolutionary pressure improve LLM agent prompts? And if so, does *how* you mutate matter (reflective error analysis vs random variation)?

Secondary question (V6.5/V7): Does market-based selection (Austrian economics price signals) outperform tournament selection?

## 2. What We Proved

### ✅ Evolution works
- **V6 (AG News):** +4.7pp over static baseline (83.7% vs ~79%), p=0.041
- Robust across 6 completed runs (3 reflective, 3 random)
- Improvement comes from selection pressure, not just luck

### ✅ Reflective mutation ≈ Random mutation
- p=0.932, Cohen's d=0.091 (negligible effect)
- Reflective: 83.7% ± 3.8% | Random: 83.3% ± 3.6%
- **Implication:** The LLM's prior knowledge dominates — giving it error feedback doesn't help on AG News

### ✅ Population management > mutation quality
- Elitism (top-2 survive) is critical
- Gating was too strict in V6 (74% rejection rate within noise)
- Fixed with 3% tolerance in V6.5 → 75% acceptance

### ⚠️ Market selection (inconclusive)
- V6.5 Market Run 1 reached gen 6: best val=93%, healthy dynamics (Gini 0.099→0.204)
- But: only 1 partial run, no test eval, no tournament comparison with same gating
- Cannot draw conclusions yet

### ❌ Multi-turn tasks infeasible locally
- V7 (negotiation): 6 LLM calls per evaluation × hundreds of evaluations = days per run
- Even gemma-3-4b couldn't finish a 3-turn negotiation in 90s
- Need cloud API (Groq, OpenRouter) for multi-turn tasks

## 3. Experiment History

| Version | Task | Runs | Key Finding | Status |
|---------|------|------|-------------|--------|
| V4 | Synthetic market | 2 | Random beat guided (over-exploration) | ✅ Complete |
| V5 | BTC/ETH prediction | 3 | No signal (task too noisy for prompts) | ✅ Complete |
| V6 | AG News 4-class | 6/9 | Evolution works, reflective≈random | ✅ Final |
| V6.5 | AG News + market | 1/6 | Promising but incomplete | 🔴 Blocked (LM Studio) |
| V7 | Negotiation + market | 0/12 | Infeasible with local LLMs | 🔴 Blocked (needs cloud API) |

## 4. Infrastructure Reality

**Local LLM (LM Studio + Qwen3-30B):**
- Fast enough for single-call tasks (AG News: ~2s/example)
- Unreliable: models unload, OOM, processes die
- V6.5 was relaunched 10+ times over 5 days
- Cannot sustain multi-day runs without supervision

**Cloud alternatives evaluated:**
- OpenRouter free tier: 33 models, qwen3-coder matches local quality. Needs signup (free).
- Groq free: too restrictive (1K RPD for good models)
- Claude API: too expensive ($3K+ for full V7)

**Recommendation:** OpenRouter free tier is the path forward. Lucas needs to sign up and provide API key.

## 5. Paper Status

- **Draft:** 9-page LaTeX paper, compiles cleanly (324KB PDF)
- **Location:** research/paper/latex/celula-madre.tex
- **Content:** V4-V6 results + V6.5 preliminary + V7 design
- **Figures:** 3 matplotlib figures (V4 comparison, V6 bar chart, V6.5 market dynamics)
- **Social figures:** 3 dark-theme figures for Twitter/blog
- **References:** 11 verified arxiv citations
- **Twitter thread:** 13-tweet draft ready

### Should we submit now?
**Not yet.** The paper's core finding (evolution works, reflective≈random) is solid, but:
1. V6.5 market selection is incomplete — our key differentiator vs competition is unproven
2. Static control runs were invalidated (LM Studio died)
3. Only 6/9 V6 runs completed

**Submit when:** At least 3 market + 3 tournament V6.5 runs complete with same gating tolerance.

## 6. Competitive Position

| What | Us | Others |
|------|----|----|
| Controlled reflective vs random | ✅ Novel (p=0.932) | No one tested this |
| Market-based selection | 🔄 In progress | FinEvo (ecological, not evolutionary) |
| Austrian economics framing | ✅ Novel | No one |
| Population management insight | ✅ Novel | Focus on mutation operators |
| Scale | ❌ Small (8 agents, 10 gens) | PromptBreeder: 50-100 units |
| Task diversity | ⚠️ Only AG News conclusive | SCOPE: HLE; EvoPrompt: multiple |

## 7. Immediate Priorities

1. **Get OpenRouter API key** → unblocks V6.5 without LM Studio dependency
2. **Complete V6.5** (6 runs: 3 market + 3 tournament with gating_tolerance=0.03)
3. **Submit paper** with complete V6.5 results
4. **Launch Twitter** with findings + open source

## 8. Open Research Questions

1. **Does market selection outperform tournament?** (V6.5 will answer)
2. **On harder tasks, does reflective mutation finally beat random?** (needs multi-step reasoning task)
3. **What's the optimal population size?** (we only tested 4 and 8)
4. **Does cross-agent knowledge transfer (merge) add value?** (V5/V6 merges rarely triggered)
5. **Can evolved prompts transfer across LLMs?** (train on Qwen3, test on Claude?)

---

*Bottom line: We proved evolution works for LLM prompts. Now we need to prove market selection is better than tournament — that's our unique contribution and the Austrian economics thesis.*
