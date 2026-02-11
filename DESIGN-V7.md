# DESIGN-V7: Market-Based Selection on a Strategic Task

**Date:** 2026-02-12
**Author:** Tesla ⚡
**Goal:** Test whether market-based selection (the original Célula Madre vision) outperforms tournament selection, and whether reflective mutation shines on tasks requiring genuine strategic reasoning.

## What V6 Proved and What It Didn't

### Proved
1. ✅ Evolutionary prompt optimization works (+5-10pp over static seeds)
2. ✅ Framework mechanics are sound (elitism, gating, tournament)
3. ✅ Reproducible across multiple runs

### Didn't Prove
1. ❌ Reflective mutation ≠ random mutation on AG News (p=0.93)
2. ❓ Market-based selection (never tested with proper controls)
3. ❓ Whether reflective mutation helps on harder tasks

### Key Insight
AG News was too simple — classification doesn't require *strategy*, just pattern recognition. Random prompt variation is enough to stumble onto good phrasings. For reflective mutation to shine, agents need tasks where **analyzing what went wrong reveals non-obvious improvements**.

## V7 Hypotheses

**H1:** Reflective mutation outperforms random mutation on multi-step strategic tasks (where error analysis provides actionable signal).

**H2:** Market-based selection (clients choose agents based on quality) produces different evolutionary dynamics than tournament selection (top-N survive by score).

**H3:** The combination of reflective mutation + market selection produces the best agents overall.

## Task: Multi-Turn Persuasion/Negotiation Game

### Why Negotiation?

| Criterion | AG News | Negotiation |
|-----------|---------|-------------|
| Strategy depth | Low (classify text) | High (plan, adapt, counter) |
| Error analysis value | Low (wrong label → "be more careful") | High (wrong tactic → specific improvements) |
| Diversity of good solutions | Low (1 good prompt) | High (different negotiation styles) |
| Market-based selection natural? | No | Yes (clients pick negotiators) |
| Eval speed | Fast (1 LLM call) | Medium (3-5 turn dialogue) |

### The Game: Deal or No Deal

Adapted from the Facebook Research negotiation task:
- Two players split a set of items (books, hats, balls) with different private valuations
- Each player has a system prompt defining their negotiation strategy
- They negotiate over 5 turns max, then propose a split
- Score = total value captured (based on private valuations)

**Why this works for Célula Madre:**
1. **Strategy matters:** Aggressive, cooperative, analytical, deceptive — different styles work in different situations
2. **Error analysis is valuable:** "I conceded too early" → specific fix, unlike "I misclassified sports as world"
3. **Market selection is natural:** "Clients" are negotiation scenarios with different difficulty levels. Better negotiators attract repeat clients.
4. **Diversity is rewarded:** A population of diverse negotiation styles handles varied opponents better than a monoculture

### Implementation Plan

```
Scenario Pool (200 scenarios):
  - Each: item counts, private valuations for both sides
  - Pre-generated, deterministic
  - Split: dev=60, val=60, test=80

Agent = System Prompt:
  - Defines negotiation style, tactics, concession strategy
  - Evaluated by having it negotiate against a FIXED opponent (baseline agent)
  - Score = average value captured across scenarios

Fixed Opponent:
  - A "reasonable" negotiation agent that doesn't evolve
  - Ensures consistent evaluation (agent quality not confounded with opponent adaptation)
```

### Evaluation Function

```python
def evaluate_agent(agent_prompt, scenarios, opponent_prompt, llm):
    scores = []
    for scenario in scenarios:
        dialogue = run_negotiation(agent_prompt, opponent_prompt, scenario, llm, max_turns=5)
        deal = extract_deal(dialogue)
        score = calculate_value(deal, scenario.agent_valuations)
        scores.append(score)
    return mean(scores), scores
```

Score normalization: divide by maximum possible value per scenario → 0-1 range.

## Selection Mechanisms (The Core Comparison)

### Group A: Tournament Selection (V6-style)
- Evaluate all agents on dev set
- Tournament selection (k=3) to pick parents
- Elitism: top-2 survive unchanged
- Gating: child must beat parent on val set

### Group B: Market Selection (Célula Madre original)
- "Clients" = negotiation scenarios, each with a small history of which agent handled them
- Phase 1 (gen 0): Random assignment
- Phase 2+ (gen 1+): Clients "choose" agents based on past performance (softmax over historical scores)
  - Popular agents get more evaluations → more precise fitness
  - Unpopular agents starve (fewer evals, noisier fitness)
- Revenue = sum of scores from assigned scenarios
- Agents with revenue below survival threshold die
- Reproduction proportional to revenue (richer agents get more offspring)

**Market selection key property:** Fitness is *endogenous* — it emerges from client choices, not from a centralized scoring function. This is the Austrian economics principle: prices (revenues) aggregate distributed information that no single evaluator could compute.

### Group C: Market Selection + Reflective Mutation
Same as Group B but with reflective mutation instead of random.

### Group D: Tournament + Random Mutation
Same as Group A but with random mutation (V6-style control).

## Full Experiment Matrix

| Group | Selection | Mutation | Runs | Purpose |
|-------|-----------|----------|------|---------|
| A | Tournament | Reflective | 3 | Baseline: does reflective help on hard tasks? |
| B | Market | Random | 3 | Does market selection alone add value? |
| C | Market + Reflective | Reflective | 3 | Full Célula Madre vision |
| D | Tournament | Random | 3 | Control (V6-equivalent) |

**12 runs total.** If each takes ~3-5 hours, ~36-60 hours total compute.

## Parameters

```yaml
population: 8
generations: 10
dev_scenarios: 60
val_scenarios: 60
test_scenarios: 80
max_negotiation_turns: 5
elite_count: 2
tournament_k: 3
mutation_temperature: 0.8
# Market-specific:
survival_threshold: 0.3  # bottom 30% revenue dies
client_memory: 3  # clients remember last 3 generations
softmax_temperature: 2.0  # how much clients favor proven agents
```

## Seed Strategies (8 diverse negotiation styles)

1. **Aggressive:** Open high, concede slowly, use anchoring
2. **Cooperative:** Find win-win, share information, build rapport
3. **Analytical:** Calculate optimal splits, propose fair divisions
4. **Deceptive:** Misrepresent valuations, create false deadlines
5. **Tit-for-tat:** Mirror opponent's concession pattern
6. **Deadline pressure:** Start slow, force decisions near the end
7. **Package dealer:** Bundle items to create mutually beneficial trades
8. **Minimalist:** Simple offers, few words, take-it-or-leave-it

## Success Criteria

### H1 (Reflective > Random on strategic task)
- Group A mean test score > Group D mean test score
- p < 0.05, Cohen's d > 0.5 (medium effect)

### H2 (Market selection has different dynamics)
- Group B shows higher *diversity* of surviving strategies than Group D
- Market selection preserves niche strategies that tournament would eliminate
- Revenue distribution follows power law (some agents dominate, others niche)

### H3 (Market + Reflective = best)
- Group C mean test score > all other groups
- p < 0.05 vs Group D (the pure control)

### Secondary Metrics
- Gen-over-gen improvement curves per group
- Strategy diversity (prompt embedding cosine similarity across population)
- Specialist vs generalist emergence (do some agents excel at specific scenario types?)
- Market dynamics: Gini coefficient of revenue distribution, market concentration

## Implementation Phases

### Phase 1: Negotiation Engine (TASK-015)
- Implement Deal-or-No-Deal game mechanics
- Scenario generator with controlled difficulty
- Fixed opponent agent
- Scoring and eval pipeline
- Test with 1 hardcoded agent

### Phase 2: Market Selection Engine (TASK-016)
- Client choice model (softmax over historical performance)
- Revenue tracking and survival threshold
- Reproduction proportional to revenue
- Integration with existing evolution framework

### Phase 3: Run Experiments (TASK-017)
- Run all 12 experiments (Groups A-D × 3 runs)
- Monitor for errors, checkpoint regularly
- Statistical analysis when complete

### Phase 4: Analysis & Publication (TASK-018)
- Full statistical analysis
- Visualizations: gen-over-gen curves, market dynamics, diversity metrics
- Write paper-quality research document
- If results are strong: prepare for publication

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Negotiation eval too slow | Limit to 5 turns, use efficient prompts |
| Fixed opponent too easy/hard | Calibrate opponent before experiments |
| LM Studio unavailable | Can fall back to Gemini Flash (free tier) |
| Market selection too noisy | Start with tournament, add market gradually |
| 12 runs × 5h = 60h compute | Run overnight, checkpoint aggressively |

## Why This Matters

V6 answered: "Does evolution work?" (Yes.)
V7 answers: "Does the *market* part of Célula Madre add value?" 

This is the central question of the project. If market-based selection produces different (better, more diverse) outcomes than tournament selection, it validates the Austrian economics thesis that prices aggregate information better than centralized evaluation. If not, we learn that selection mechanism doesn't matter — only mutation + selection pressure does.

Either answer is publishable.

---

*"The curious task of economics is to demonstrate to men how little they really know about what they imagine they can design." — F.A. Hayek*
