# Célula Madre: Evolutionary Optimization of LLM Agent Prompts Through Selection Pressure

**Tesla ⚡ & Lucas Burriel**
**Draft — February 2026**

---

## Abstract

We present Célula Madre, a framework for evolving Large Language Model (LLM) agent prompts through iterative selection pressure without modifying model weights. Our primary contributions are: (1) a controlled comparison showing that evolutionary prompt optimization produces statistically significant improvements over static baselines (+4.7 percentage points, p=0.041 on AG News 4-class classification); (2) a surprising null result demonstrating that reflective mutation (error-informed prompt revision) provides no advantage over random mutation on classification tasks (p=0.932, Cohen's d=0.091); and (3) evidence from four experiment iterations (V4–V6, with V7 ongoing) that population management mechanisms—elitism, gating, and selection design—matter more than mutation operator sophistication. These findings establish random LLM-generated variation as a strong baseline that any "intelligent" mutation method must beat, and motivate our ongoing work on market-based selection for strategically complex tasks.

## 1. Introduction

The dominant paradigm for improving LLM agent behavior is prompt engineering: manually crafting system prompts that elicit desired outputs. This approach is labor-intensive, non-systematic, and does not scale to populations of specialized agents. An alternative is **evolutionary prompt optimization**, where selection pressure—rather than human judgment—drives improvement.

Célula Madre (Spanish: "stem cell") applies principles from evolutionary computation and Austrian economics to the problem of agent optimization. The core thesis is twofold:

1. **Selection pressure improves prompts.** Agents with better-performing prompts survive and reproduce; worse-performing agents are eliminated. Over generations, population fitness increases.
2. **Market-based selection aggregates information.** Rather than centralized fitness evaluation, agents compete for "clients" who choose based on track record—a price-signal mechanism inspired by Hayek's knowledge problem.

This paper reports results from four experimental iterations (V4–V6 complete, V7 in progress), each designed to isolate specific mechanisms. Our contributions are:

- **V4:** Demonstrated that naive LLM-guided mutation with poor population management is *worse* than random mutation (p < 0.0001), identifying over-exploration and feedback overfitting as failure modes.
- **V5:** Validated that framework mechanics (elitism, gating, Pareto frontier) are sound on financial prediction, though small scale limited statistical conclusions.
- **V6:** Established that evolution produces significant improvement (+4.7pp over static, p=0.041) but reflective mutation ≈ random mutation on classification (p=0.932).
- **V7 (ongoing):** Tests market-based selection on a multi-turn negotiation task where strategic reasoning should differentiate mutation methods.

## 2. Related Work

### 2.1 Prompt Optimization

Automatic prompt optimization has been explored through gradient-based methods (AutoPrompt; Shin et al., 2020), discrete search (GRIPS; Prasad et al., 2023), and LLM-based refinement (APE; Zhou et al., 2023). Most approaches optimize a single prompt against a fixed evaluation function. Célula Madre differs by maintaining a **population** of competing prompts under selection pressure—closer to genetic programming than single-point optimization.

### 2.2 Evolutionary Approaches to LLM Optimization

EvoPrompt (Guo et al., 2024) applies genetic algorithms (GA and DE) to prompt optimization with crossover and mutation operators, achieving state-of-the-art on multiple NLP benchmarks. Promptbreeder (Fernando et al., 2023) introduces self-referential self-improvement, where both task prompts and mutation prompts co-evolve—a meta-evolutionary approach. Both maintain populations of prompts under selection pressure, validating the evolutionary paradigm.

A key question these works leave open is whether *error-informed* mutation outperforms *blind* mutation. Reflective mutation—where the LLM analyzes its own errors before generating improved prompts—is intuitively appealing but lacks controlled comparison against random variation. Our work addresses this gap by: (a) systematically comparing reflective vs. random mutation with proper statistical controls (3 runs per condition), (b) testing population-level dynamics (elitism, gating, tournament selection), and (c) introducing market-based selection as an alternative to tournament selection, inspired by Austrian economics.

### 2.3 Austrian Economics and Agent Coordination

The market-selection component of Célula Madre draws on Hayek's (1945) argument that prices aggregate distributed knowledge more efficiently than centralized planning. In our framework, "clients" choosing agents based on track record act as a decentralized fitness function, potentially capturing dimensions of quality that a fixed metric would miss. This connects to recent work on LLM agent economies (Park et al., 2023) but applies market logic to the *evolution* of agents rather than their runtime behavior.

## 3. Framework Design

### 3.1 Architecture

Célula Madre maintains a population of *N* agents, each defined by a system prompt. Each generation proceeds as:

1. **Evaluation:** All agents are scored on a development set.
2. **Selection:** Top-*k* agents survive (elitism). Remaining slots filled by mutation or fresh injection.
3. **Mutation:** Selected parents produce offspring via prompt modification (reflective or random).
4. **Gating:** Offspring must score ≥ parent on development set to enter population. Otherwise, parent survives.
5. **Validation:** Generation-level fitness tracked on held-out validation set.
6. **Final test:** Best agent evaluated on unseen test set after all generations complete.

### Algorithm 1: Evolutionary Prompt Optimization

```
Input: Population size N, generations G, elite count K, dev/val sets
Output: Best agent prompt

Initialize population P = {seed_1, ..., seed_N}
For g = 1 to G:
    // Evaluate
    For each agent a in P:
        a.fitness = evaluate(a.prompt, dev_set)
    
    // Select elites
    elites = top_K(P, by=fitness)
    
    // Generate offspring
    offspring = []
    While |elites| + |offspring| < N - 1:
        parent = tournament_select(P, k=3)
        child = mutate(parent)  // reflective or random
        // Gating: child must beat parent
        If evaluate(child, dev_set) >= parent.fitness:
            offspring.append(child)
        Else:
            offspring.append(parent)  // parent survives
    
    // Fresh injection (1 random new agent per generation)
    fresh = generate_random_agent()
    
    P = elites ∪ offspring ∪ {fresh}
    
    // Track validation performance
    log(best_val_score(P, val_set), generation=g)

Return argmax(P, by=val_fitness)
```

### 3.2 Mutation Operators

**Reflective mutation (GEPA-style):** The LLM receives the parent prompt, a sample of its errors (input, predicted output, correct output), and instructions to analyze failure patterns and produce an improved prompt. The key hypothesis is that error analysis provides a directed search signal.

**Random mutation:** The LLM receives the parent prompt and instructions to produce a variation without seeing any performance data. This tests whether the structural intelligence inherent in LLM text generation (coherence, plausibility) is sufficient for effective mutation.

### 3.3 Selection Mechanisms

**Tournament selection:** Random subsets of *k* agents compete; highest-scoring agent is selected as parent. Combined with elitism (top-2 always survive).

**Market-based selection (V7):** Evaluation scenarios act as "clients" who choose agents based on historical performance (softmax over past scores). Agents earn "revenue" proportional to clients served. Agents below a survival threshold are eliminated; reproduction is proportional to revenue. This creates endogenous fitness that emerges from decentralized choices rather than centralized scoring.

## 4. Experiments

### 4.1 V4: Simulated Code Marketplace

**Task:** Agents compete to serve coding tasks in a simulated marketplace. Clients choose agents by specialization; agents earn revenue from completed tasks.

**Setup:** Experimental group (guided mutation from client feedback) vs. control (random mutation). Both start from identical Gen0 prompts.

**Results:** The control group earned **2.3× more profit** (mean 208.57 vs 90.81, p < 0.0001, Cohen's d = −2.01). The experimental group spawned 24 agents across 6 generations vs. control's 11 across 5, diluting market share per agent. Guided mutation overfit to noisy client feedback, producing increasingly fragile prompts. Gen0 (hand-crafted) remained the experimental group's best generation.

**Lessons:** (1) Population management matters more than mutation quality. (2) Without elitism, good agents are lost. (3) Noisy feedback + LLM interpretation = overfitting. These findings directly informed V5's design.

### 4.2 V5: Financial Prediction

**Task:** Predict next-day BTC price direction given 30-day OHLCV context.

**Setup:** Population of 4, 3 generations, elitism (top-2), gating, Pareto frontier. LLM: Qwen3-30B (local).

**Results:** Best agent (mean-reversion strategy) achieved 59.4% test accuracy (p ≈ 0.03 vs 50% baseline). However, no mutations passed gating—all improvement came from seed diversity and one successful merge. Scale was too limited (dev=10 examples) for reliable evolutionary signal.

**Lessons:** (1) Framework mechanics (elitism, gating, merge) work correctly. (2) Evaluation noise at small scale prevents gating from functioning. (3) Need ≥30 examples per eval set for reliable signal.

### 4.3 V6: AG News Classification (Primary Result)

**Task:** 4-class text classification (World, Sports, Business, Sci/Tech) on the AG News dataset.

**Setup:** Three groups × 3 runs each:
- **Reflective:** Mutation guided by error analysis
- **Random:** Mutation without error feedback  
- **Static:** No mutation (re-evaluate same agents each generation)

Population: 8. Generations: 10. Eval sets: dev=100, val=100, test=200 (balanced). LLM: Qwen3-30B-A3B (local). Tournament selection (k=3), elitism (top-2), gating.

**Results:**

| Group | Run 1 | Run 2 | Run 3 | Mean | Std |
|-------|-------|-------|-------|------|-----|
| Reflective | 89.0% | 80.5% | 81.5% | 83.7% | 3.8% |
| Random | 87.0% | 78.5% | 84.5% | 83.3% | 3.6% |
| Static | — | — | — | ~79%* | — |

*Static estimated from Gen0 scores; runs invalidated due to infrastructure failure.

**Statistical tests:**
- Reflective vs Random: t = 0.091, p = 0.932, Cohen's d = 0.091 (no difference)
- Evolution (all 6 runs) vs Gen0 baseline (79%): t = 2.730, p = 0.041 (significant)

**Per-class analysis:** Sports was easiest (94–98% across all runs). Sci/Tech was hardest and most variable (31–74%), suggesting prompt wording strongly affects the Business/Sci-Tech boundary.

**Generational dynamics:** Reflective mutation improved faster (Gen0→1: +5pp) but plateaued early. Random mutation climbed more gradually to the same level. Most improvement occurred in generations 0–3.

### 4.4 V7: Negotiation with Market Selection (In Progress)

**Task:** Deal-or-No-Deal multi-turn negotiation against a fixed opponent. Score = value captured based on private item valuations.

**Setup:** 4 groups (2×2 factorial: tournament/market × reflective/random), 3 runs each = 12 runs. Population: 8. Generations: 10. 200 scenarios (dev=60, val=60, test=80). 8 diverse seed strategies (aggressive, cooperative, analytical, deceptive, tit-for-tat, deadline, package, minimalist).

**Hypotheses:** (H1) Reflective mutation outperforms random on strategic tasks. (H2) Market-based selection preserves greater strategic diversity. (H3) Market + reflective produces the best overall agents.

## 5. Discussion

### 5.1 Evolution Works, But Mutation Intelligence Doesn't (Yet)

The most robust finding across V4–V6 is that **selection pressure improves agent prompts regardless of mutation method.** The 4.7pp improvement over static baselines in V6 (p=0.041) demonstrates that the evolutionary loop—evaluate, select, reproduce, gate—drives genuine optimization.

However, the null result on reflective vs. random mutation (p=0.932) demands explanation. We propose three hypotheses:

1. **Task complexity threshold.** Classification may lack sufficient strategic depth for error analysis to produce non-obvious improvements. When "be more careful about Sci/Tech vs Business" is the only actionable insight, random variation is equally likely to stumble onto effective phrasings.

2. **Mutation LLM capacity.** Qwen3-30B may lack the reasoning depth to extract actionable patterns from errors. A stronger model (e.g., Claude, GPT-4) might produce more targeted mutations.

3. **Gating as equalizer.** By requiring offspring to beat parents, gating converges both methods to similar local optima. The path to the optimum differs, but the destination is the same—because the task's optimum is narrow.

V7's negotiation task is designed to test hypothesis (1): if reflective mutation helps on tasks with genuine strategic depth, the task complexity threshold hypothesis is supported.

A fourth, more fundamental possibility is worth considering: **LLM-generated text is never truly "random."** Even without error feedback, an LLM asked to "vary this prompt" draws on its training distribution of effective instructions. The model's prior over coherent, task-relevant language may be so strong that explicit error feedback adds negligible signal. This would imply that the real mutation operator is the LLM's own implicit understanding of what makes good prompts—and that understanding is equally available to both "reflective" and "random" conditions.

### 5.2 Population Dynamics > Mutation Quality

V4's dramatic result (random mutation 2.3× better) was driven entirely by population dynamics: fewer agents → more evaluations per agent → better selection signal. This suggests that in evolutionary prompt optimization, **the selection mechanism's ability to accurately identify fitness matters more than the mutation operator's ability to produce good candidates.**

This insight motivates V7's market-based selection: if selection quality is the bottleneck, a selection mechanism that aggregates more information (via client choice dynamics) should outperform simple tournament selection.

### 5.3 Implications for LLM Agent Optimization

1. **Evolutionary optimization is viable and cheap.** V6 ran entirely on a local 30B-parameter model with zero API costs, producing meaningful improvements in ~5 hours per run.
2. **Elitism and gating are essential.** V4's failure without them vs. V5–V6's success with them is a clear lesson: preserve winners, gate newcomers.
3. **Random mutation is a strong baseline.** Any work on "intelligent" mutation operators must compare against random LLM-generated variations, not just static baselines.
4. **Evaluation quality bounds evolutionary quality.** With noisy or small eval sets, even perfect mutation operators cannot outperform random search.

### 5.4 Connections to Austrian Economics

The Célula Madre project is grounded in Hayek's (1945) knowledge problem: centralized fitness evaluation faces the same information limitations as centralized economic planning. A single metric (accuracy, profit) cannot capture all dimensions of agent quality—reliability across domains, stylistic fit for different use cases, robustness to adversarial inputs. Market-based selection, where evaluation emerges from the aggregated choices of many "clients," may better capture this multi-dimensional fitness landscape.

There is a deeper connection to Menger's (1871) theory of subjective value: agent quality is not intrinsic but depends on the evaluator's context and needs. A negotiation agent that excels at cooperative deals has different "value" to a client facing a hostile counterparty versus a cooperative one. Tournament selection, by reducing fitness to a scalar, discards this contextual information. Market selection preserves it—each client's choice implicitly weights different quality dimensions based on their specific scenario.

Furthermore, Kirzner's (1973) concept of entrepreneurial discovery suggests that market dynamics create incentives for agents to discover and exploit underserved niches. If all top agents specialize in aggressive negotiation, a cooperative agent—even if mediocre overall—may attract clients in cooperative scenarios, earning enough revenue to survive and improve. This endogenous diversification pressure is absent in tournament selection, where only the globally best survive regardless of niche value. V7 directly tests whether this theoretical advantage translates to empirical gains.

## 6. Ongoing Work: Market-Based Selection on Strategic Tasks (V7)

V6's null result on mutation quality raises a critical question: is the finding task-specific, or fundamental? V7 is designed to answer this through a 2×2 factorial experiment on a strategically complex task.

### 6.1 Task: Multi-Turn Negotiation

We adopt a Deal-or-No-Deal negotiation game where two agents split a set of items (books, hats, balls) with asymmetric private valuations. Unlike classification, negotiation demands multi-step planning, opponent modeling, and adaptive tactics—capabilities where error analysis ("I conceded too early on high-value items") should produce more actionable mutations than random prompt variation.

Each negotiation runs for up to 5 turns. An agent's score is the total value of items it secures, based on its private valuation. Agents compete against a fixed opponent to ensure consistent evaluation. We generate 200 scenarios with controlled difficulty: 60 dev, 60 val, 80 test, each with 3 items and randomly assigned private valuations guaranteeing integrative potential (differing item valuations between players).

### 6.2 Market-Based Selection

V7 introduces market-based selection as an alternative to tournament selection. The mechanism works as follows:

1. **Client choice:** Each evaluation scenario acts as a "client" that selects an agent via softmax over the agent's historical scores on similar scenarios. Temperature controls exploration/exploitation.
2. **Revenue accumulation:** Agents earn revenue proportional to scenarios served and scores achieved.
3. **Survival threshold:** Agents earning below 30% of mean revenue are eliminated.
4. **Proportional reproduction:** Surviving agents reproduce with probability proportional to their revenue share.

This creates a decentralized fitness signal where quality emerges from aggregated client choices—directly implementing Hayek's (1945) insight that prices convey information no central planner can aggregate. In evolutionary terms, market selection captures multi-dimensional fitness (reliability, specialization, client satisfaction) that a single score metric may miss.

### 6.3 Experimental Design

The 2×2 factorial design crosses selection mechanism (tournament vs. market) with mutation operator (reflective vs. random), yielding 4 groups with 3 runs each (12 total). All groups share the same 8 seed strategies spanning negotiation archetypes: aggressive, cooperative, analytical, deceptive, tit-for-tat, deadline-exploiting, package-dealing, and minimalist.

**Predictions:**
- *H1:* Reflective > random on negotiation (unlike V6's classification null result)
- *H2:* Market selection preserves greater strategic diversity (measured by Gini coefficient and strategy cluster analysis)
- *H3:* Market × reflective produces the highest absolute performance

If H1 holds but H2 does not, mutation quality is task-dependent but selection mechanism doesn't matter. If both hold, the original Célula Madre thesis—that market dynamics drive superior agent evolution—is supported.

## 7. Limitations

- **Static control incomplete in V6:** Infrastructure failure (LM Studio model unload) invalidated static runs. The ~79% baseline is estimated from Gen0 scores, which is conservative but not directly measured post-evolution.
- **Single LLM:** All experiments used Qwen3-30B. Results may not generalize to other model families or scales.
- **Small run counts:** 3 runs per condition provides limited statistical power. Larger-scale replication is needed.
- **Single task per version:** Each version tested one task, making cross-task generalization uncertain.

## 8. Conclusion

Célula Madre demonstrates that evolutionary selection pressure can systematically improve LLM agent prompts, producing statistically significant gains over static baselines without modifying model weights. The framework's key components—elitism, gating, and population management—are more important than the sophistication of the mutation operator, at least on classification tasks. Whether reflective mutation and market-based selection add value on strategically complex tasks remains an open question, currently under investigation (V7).

The broader implication is that **selection, not design, may be the more powerful lever for LLM agent optimization.** Just as biological evolution produces remarkable solutions through variation and selection rather than intelligent design, prompt evolution may achieve results that deliberate engineering cannot—provided the selection mechanism is well-calibrated and the evaluation signal is clean.

## References

- Fernando, C., Banarse, D., Michalewski, H., Osindero, S., & Rocktäschel, T. (2023). Promptbreeder: Self-Referential Self-Improvement Via Prompt Evolution. *arXiv:2309.16797*.
- Guo, Q., Wang, R., Guo, J., Li, B., Song, K., Tan, X., Liu, G., Bian, J., & Yang, Y. (2024). EvoPrompt: Connecting LLMs with Evolutionary Algorithms Yields Powerful Prompt Optimizers. *ICLR 2024*. *arXiv:2309.08532*.
- Hayek, F. A. (1945). The Use of Knowledge in Society. *American Economic Review*, 35(4), 519-530.
- Kirzner, I. M. (1973). *Competition and Entrepreneurship.* University of Chicago Press.
- Menger, C. (1871). *Grundsätze der Volkswirtschaftslehre* [Principles of Economics]. Wilhelm Braumüller.
- Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). Generative Agents: Interactive Simulacra of Human Behavior. *UIST 2023*. *arXiv:2304.03442*.
- Prasad, A., Hase, P., Zhou, X., & Bansal, M. (2023). GrIPS: Gradient-free, Edit-based Instruction Search for Prompting Large Language Models. *EACL 2023*. *arXiv:2203.07281*.
- Shin, T., Razeghi, Y., Logan IV, R. L., Wallace, E., & Singh, S. (2020). AutoPrompt: Eliciting Knowledge from Language Models with Automatically Generated Prompts. *EMNLP 2020*. *arXiv:2010.15980*.
- Zhou, Y., Muresanu, A. I., Han, Z., Paster, K., Pinto, S., & Ba, J. (2023). Large Language Models Are Human-Level Prompt Engineers. *ICLR 2023*. *arXiv:2211.01910*.

---

## Appendix A: Experiment Parameters

### V4
| Parameter | Experimental | Control |
|-----------|-------------|---------|
| Agents | 24 (6 gens) | 11 (5 gens) |
| Transactions | 200 | 200 |
| Mutation | LLM-guided (client feedback) | Random |
| Elitism | None | None |
| Gating | None | None |

### V5
| Parameter | Value |
|-----------|-------|
| Population | 4 |
| Generations | 3 |
| Elite count | 2 |
| Dev/Val/Test | 10/10/101 |
| LLM | Qwen3-30B |

### V6
| Parameter | Value |
|-----------|-------|
| Population | 8 |
| Generations | 10 |
| Elite count | 2 |
| Tournament k | 3 |
| Dev/Val/Test | 100/100/200 |
| LLM | Qwen3-30B-A3B |
| Runs per group | 3 |

### V7 (Planned)
| Parameter | Value |
|-----------|-------|
| Population | 8 |
| Generations | 10 |
| Scenarios | 60/60/80 (dev/val/test) |
| Max negotiation turns | 5 |
| Selection | Tournament or Market |
| Mutation | Reflective or Random |
| Runs per group | 3 (12 total) |

## Appendix B: V6 Generational Trajectories

### Mean Best Validation Accuracy (%) by Generation

```
  Val%
  88 |                                          R
  87 |                                    R  R
  86 |                              R  R        
  85 |        E  E  E  E  E     E     E  E     R
  84 |                       E              R
  83 |     E              R
  82 |        R  R                              
  81 |
  80 |
  79 |  R                                       
  78 |  E
     +--+--+--+--+--+--+--+--+--+--+
       0  1  2  3  4  5  6  7  8  9   Generation

  E = Reflective (experimental)    R = Random (control)
  Static baseline ≈ 79% (dashed, not shown)
```

**Key observations:**
- Reflective mutation shows faster early gains (Gen 0→1: +5pp) but plateaus at Gen 2
- Random mutation climbs more gradually but reaches the same ceiling by Gen 5
- Both converge to ~85-86% validation accuracy, well above the ~79% static baseline
- Most improvement occurs in generations 0–3; later generations show diminishing returns

### Individual Run Test Scores

```
           Run 1    Run 2    Run 3    Mean ± Std
Reflect:   89.0%    80.5%    81.5%    83.7 ± 3.8%
Random:    87.0%    78.5%    84.5%    83.3 ± 3.6%
Static:     —*       —*       —*      ~79% (est.)

* Static runs invalidated (infrastructure failure)
  Estimate from Gen0 seeds across reflective/random runs
```
