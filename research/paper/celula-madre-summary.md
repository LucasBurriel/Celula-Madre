# Célula Madre — Executive Summary

**Evolutionary Optimization of LLM Agent Prompts Through Selection Pressure**

Tesla ⚡ & Lucas Burriel | February 2026

---

## The Problem

Prompt engineering is manual, non-systematic, and doesn't scale. When you need populations of specialized AI agents, hand-tuning each prompt is a dead end.

## Our Approach

Célula Madre evolves LLM agent prompts through **selection pressure** — the same mechanism that drives biological evolution. No weight changes, no fine-tuning. Just variation, selection, and reproduction of system prompts.

**Core loop:** Evaluate agents → Select the best → Mutate to create offspring → Gate (offspring must beat parent) → Repeat.

**Key design elements:**
- Elitism (top performers always survive)
- Gating (new prompts must prove themselves)
- Tournament selection (competitive pressure)
- Market-based selection (clients choose agents — V7, in progress)

## What We Found

### ✅ Evolution works (+4.7pp, p=0.041)

Across 6 independent runs on AG News 4-class classification, evolved agents achieved **83.5% mean accuracy** vs **~79% static baseline** — a statistically significant improvement driven purely by selection pressure.

| Condition | Mean Test Accuracy | Std |
|-----------|-------------------|-----|
| Reflective mutation | 83.7% | 3.8% |
| Random mutation | 83.3% | 3.6% |
| Static (no evolution) | ~79% | — |

### ⚖️ Reflective mutation ≈ Random mutation (p=0.932)

**Surprise finding:** Error-informed "intelligent" mutation provides *no advantage* over random LLM-generated variations on classification. Cohen's d = 0.09 (negligible). This establishes random mutation as a **strong baseline** any sophisticated method must beat.

### 🏗️ Population management > Mutation quality

V4 showed that without elitism and gating, guided mutation *hurts* — the experimental group earned 2.3× less than random controls (p < 0.0001). The selection mechanism's accuracy matters more than the mutation operator's sophistication.

## Experiment History

| Version | Task | Key Finding |
|---------|------|-------------|
| **V4** | Code marketplace | Guided mutation without elitism = catastrophic (over-exploration, feedback overfitting) |
| **V5** | BTC price prediction | Framework mechanics validated; scale too small for conclusions |
| **V6** | AG News classification | Evolution works; reflective = random; population management is king |
| **V7** | Deal-or-No-Deal negotiation | In progress — testing market-based selection + strategic tasks |

## Why It Matters

1. **Cheap and accessible.** V6 ran entirely on a local 30B model with zero API costs (~5h per run).
2. **Model-agnostic.** Works on any LLM that can follow a system prompt — no fine-tuning infrastructure needed.
3. **Random mutation is underrated.** LLMs generate structurally coherent variations even without error feedback. This free lunch should not be ignored.
4. **Selection design is the bottleneck.** Better selection mechanisms (market-based, multi-dimensional) likely matter more than smarter mutation.

## What's Next

**V7: Market-Based Selection on Negotiation**

We're testing whether reflective mutation *does* help on tasks with genuine strategic depth (multi-turn negotiation), and whether market-based selection (inspired by Hayek's price signal theory) outperforms tournament selection by capturing multi-dimensional fitness.

- 4 experimental groups (2×2: tournament/market × reflective/random)
- 12 total runs with full statistical analysis
- If market + reflective wins: evidence for Austrian economics applied to agent evolution

**Longer term:**
- Breeding-as-a-service: optimize agent prompts for paying clients
- Agent marketplace: evolved specialists competing for real tasks
- arXiv preprint once V7 results are in

## Resources

- **Paper draft:** [celula-madre-draft.md](celula-madre-draft.md)
- **Code:** [github.com/LucasBurriel/Celula-Madre](https://github.com/LucasBurriel/Celula-Madre)
- **V6 full analysis:** [../experiments/v6-results.md](../experiments/v6-results.md)

---

*"Selection, not design, may be the more powerful lever for LLM agent optimization."*
