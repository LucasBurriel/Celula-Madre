# DESIGN-V8: Market Selection on Strategy-Sensitive Tasks

## Motivation

V6 proved evolution works (+4.7pp over static, p=0.041) but reflective ≈ random on AG News.
V7 negotiation was computationally infeasible with local LLMs (6 LLM calls per scenario).
V6.5 (market selection on AG News) is blocked by LM Studio instability.

**Core question:** Does market-based selection outperform tournament selection on tasks where strategy diversity genuinely matters?

AG News is too "flat" — one good prompt dominates all categories. We need a task where **different strategies excel on different subsets**, making market allocation valuable.

## Task Selection: Multi-Domain Sentiment Analysis

**Winner: SST-2 + Amazon + Yelp + Tweet Sentiment — mixed-domain sentiment.**

### Why This Task
1. **Strategy diversity matters:** Formal reviews (Amazon/Yelp), tweets (informal, sarcasm), movie reviews (SST-2) all need different approaches
2. **1 LLM call per example** (same as AG News — fast, proven feasible)
3. **Market selection has clear advantage:** Agents can specialize by domain; market routes examples to domain-specialist agents
4. **Easy baseline:** Random/majority class ~50% (binary sentiment), plenty of room for improvement
5. **Data freely available:** HuggingFace datasets

### Domain Split
| Domain | Source | Style | Challenge |
|--------|--------|-------|-----------|
| Movies | SST-2 | Formal reviews | Nuanced, mixed sentiment |
| Products | Amazon Reviews | Terse, star-rating aligned | Sarcasm, "great for the price" |
| Restaurants | Yelp | Descriptive, emotional | Service vs food distinction |
| Social | Tweet Eval | Slang, hashtags, irony | Very short, context-dependent |

### Why Market Selection Wins Here
In tournament selection, ALL agents are ranked on ALL domains. A generalist always wins.

In market selection, **clients (examples) choose agents based on past performance on similar examples**. An agent that's 95% on tweets but 60% on Amazon reviews still gets all the tweet clients. This naturally creates **specialization** — the Austrian economics insight: price signals (client choice) allocate resources better than central planning (tournament ranking).

## Experiment Design

### Groups (2×2 factorial, same as V7)
| Group | Selection | Mutation | Runs |
|-------|-----------|----------|------|
| A | Market | Reflective | 3 |
| B | Tournament | Reflective | 3 |
| C | Market | Random | 3 |
| D | Tournament | Random | 3 |

**12 runs total** (same as V7 design, proven feasible on AG News scale).

### Parameters
- Population: 8 agents
- Generations: 10
- Dev set: 100 examples (25 per domain)
- Val set: 100 examples (25 per domain)
- Test set: 200 examples (50 per domain)
- Gating tolerance: 3% (from TASK-032 fix)
- Elitism: top 2
- Fresh injection: 1 per generation

### Seed Strategies (8, domain-biased)
1. **Generalist** — balanced approach across all domains
2. **Formal analyzer** — focus on review structure, adjectives, comparative language
3. **Slang decoder** — optimize for tweets, informal text, hashtags
4. **Sarcasm detector** — look for irony markers, contradictions
5. **Keyword spotter** — positive/negative word lists
6. **Context reader** — consider full context, qualifiers, "but" clauses
7. **Emotion mapper** — map emotional language to sentiment
8. **Minimalist** — shortest possible classification rule

### Metrics
- **Primary:** Test accuracy (overall + per-domain)
- **Market-specific:** Gini coefficient, HHI, per-domain agent specialization
- **Evolution:** Gen-over-gen improvement, mutation acceptance rate
- **Key comparison:** Market vs Tournament on per-domain accuracy (do market agents specialize?)

### Success Criteria
1. Market groups show agent specialization (different agents dominate different domains)
2. Market overall accuracy ≥ Tournament (or within noise)
3. Market per-domain accuracy > Tournament per-domain (specialization bonus)
4. Gini coefficient indicates healthy market (0.15-0.40, not monopoly)

## Implementation Plan

### Phase 1: Data Pipeline
- Download SST-2, Amazon, Yelp, TweetEval from HuggingFace
- Unify format: `{text, label, domain}`
- Create balanced splits (25 per domain per split)
- Save as JSON (same pattern as AG News)

### Phase 2: Eval Function
- Extend `evaluate_agent` to track per-domain accuracy
- Market engine client memory includes domain metadata
- Domain-aware client choice: similar examples (same domain) inform agent selection

### Phase 3: Evolution Engine
- Reuse V6.5 `EvolutionEngineV65` with domain-aware market config
- Reflective mutation gets per-domain error breakdown
- Add specialization metric: for each agent, which domain has highest accuracy?

### Phase 4: Run Experiments
- Same infrastructure as V6.5 (`run_v6_market.py --provider openrouter`)
- **Requires:** OpenRouter API key OR reliable LM Studio

## Fallback: If No Cloud API

If we can't get any API key, V8 can still run on LM Studio when it's available. AG News V6 proved local LLMs work for classification (89% accuracy with Qwen3-30B). The key is LM Studio stability, not capability.

**Priority order:**
1. OpenRouter free tier (qwen3-coder) — needs Lucas to sign up
2. LM Studio (Qwen3-30B) — needs Lucas to load models
3. Groq free tier (llama-3.3-70b) — rate-limited but works

## Timeline

- Data pipeline: ~2h (straightforward, follows AG News pattern)
- Eval function: ~1h (extend existing)
- Engine adaptation: ~1h (mostly config changes)
- Run experiments: ~20-40h (depending on provider speed)
- Analysis: ~2h

**Total active work: ~6h. Total wall clock: 1-2 days.**

## Connection to Paper

V8 results would be **Section 6: Market Selection** in the paper, replacing the preliminary V6.5 data. This is the strongest possible evidence for the Austrian economics thesis: price signals (market selection) create specialization that central planning (tournament selection) cannot.

If market selection shows domain specialization, this is a publishable result on its own — novel contribution to both prompt optimization and agent coordination literature.
