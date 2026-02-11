# Literature Survey: LLM Prompt Evolution & Agent Markets (2025-2026)

**Date:** 2026-02-11
**Author:** Tesla ⚡

## Directly Relevant Papers

### SCOPE: Prompt Evolution for Enhancing Agent Effectiveness
- **Authors:** Pei, Zhen, Kai, Pan, Wang, Yuan, Yu
- **Date:** December 2025
- **arXiv:** 2512.15374
- **Relevance:** ★★★★★ — Most directly comparable to Célula Madre
- **Summary:** Frames context management as online optimization, evolving agent prompts from execution traces. Uses "Dual-Stream" mechanism balancing tactical specificity (immediate error fixes) with strategic generality (long-term principles). "Perspective-Driven Exploration" maximizes strategy coverage. Results: 14.23% → 38.64% on HLE benchmark.
- **Comparison to Célula Madre:** SCOPE evolves a *single* agent's prompt over time (online learning), while we evolve a *population* under selection pressure. SCOPE's dual-stream is analogous to our reflective mutation but without population dynamics. Key difference: we test whether population-level selection adds value beyond single-agent self-improvement. SCOPE doesn't compare reflective vs random mutation.
- **Citation priority:** HIGH — must cite in Related Work.

### FinEvo: Ecological Market Games for Multi-Agent Financial Strategy Evolution
- **Authors:** Zou, Chen, Luo, Dai, Zhang, Sun, Xu
- **Date:** January 2026
- **arXiv:** 2602.00948
- **Relevance:** ★★★★★ — Closest to our V7 market-based selection vision
- **Summary:** Models trading strategies as adaptive agents in a shared market ecology. Three evolutionary mechanisms: selection, innovation, and environmental perturbation. Strategies interact — may dominate, collapse, or form coalitions depending on competitors. Links evolutionary game theory with modern learning dynamics.
- **Comparison to Célula Madre:** FinEvo studies *existing* strategies (rule-based, DL, RL, LLM) competing ecologically. We *evolve new strategies* through mutation. FinEvo's ecological perspective validates our market-based selection intuition — strategy evaluation should be competitive, not isolated. Key difference: they don't optimize prompts; they study pre-built strategy interactions. Our V7 combines both: evolving prompts AND market-based evaluation.
- **Citation priority:** HIGH — validates our ecological/market approach from a different angle.

### EvoLattice: Persistent Internal-Population Evolution through Quality-Diversity Graph Representations
- **Date:** December 2025
- **Relevance:** ★★★★ — Addresses population diversity, our key concern
- **Summary:** Introduces persistent internal population for LLM-guided program discovery. Maintains multiple candidates via graph representations instead of overwrite-based mutations that discard useful variants. Quality-Diversity approach prevents destructive edits and structural failure.
- **Comparison to Célula Madre:** EvoLattice's quality-diversity preservation parallels our Pareto frontier and market-based diversity maintenance. Their critique of "overwrite-based mutations" validates our elitism mechanism. Different domain (program synthesis vs prompt optimization) but shared evolutionary principles.
- **Citation priority:** MEDIUM — cite for diversity preservation discussion.

### MulVul: Cross-Model Prompt Evolution for Vulnerability Detection
- **Authors:** Wu, Xu, Peng, Chong, Jia
- **Date:** January 2026
- **Relevance:** ★★★ — Applied prompt evolution
- **Summary:** Uses multi-agent cross-model prompt evolution for code vulnerability detection. RAG-augmented.
- **Comparison to Célula Madre:** Application of prompt evolution to a specific domain. Less methodological novelty for our purposes but shows the approach generalizing to security domains.
- **Citation priority:** LOW — mention briefly if space permits.

## Tangentially Relevant Papers

### MAGIC: Co-Evolving Attacker-Defender Adversarial Game (Feb 2026)
- Co-evolution of attack and defense prompts for LLM safety. Interesting ecological framing but different goal (safety, not optimization).

### PathWise: Planning through World Model for Automated Heuristic Design (Jan 2026)
- Self-evolving LLMs for heuristic design. Uses world model planning, not population-based evolution.

### Learn Like Humans: Meta-cognitive Reflection for Self-Improvement (Jan 2026)
- Meta-cognitive self-improvement for LLM agents. Related to our reflective mutation but single-agent, not population-based.

### Youtu-Agent: Scaling Agent Productivity with Hybrid Policy Optimization (Dec 2025)
- Automated agent generation with policy optimization. Different approach (RL-based, not evolutionary).

## Key Finding: No Market-Based Agent Selection Paper Exists

**This is our key differentiator.** No paper found that uses market-based selection (clients choosing agents via price signals / track record) as the evolutionary selection mechanism for prompt optimization. FinEvo comes closest by studying ecological dynamics, but doesn't use market selection to *drive* evolution — they study pre-built strategies.

The combination of:
1. Population-based prompt evolution (shared with EvoPrompt, Promptbreeder, SCOPE)
2. Market-based selection via client choice (NOVEL)
3. Controlled comparison of reflective vs random mutation (shared concern, but our null result is unique)
4. Austrian economics theoretical grounding (NOVEL)

...positions Célula Madre uniquely in the literature.

## Recommendations for Paper

1. **Add SCOPE** to Related Work — most direct comparison, emphasize population vs single-agent difference
2. **Add FinEvo** to Related Work — validates ecological/market intuition, differentiate our evolutionary optimization focus
3. **Add EvoLattice** briefly — quality-diversity angle
4. **Strengthen positioning:** Our paper is the first to (a) rigorously compare reflective vs random mutation with statistical controls, and (b) propose market-based selection for prompt evolution
5. **Update paper timeline note:** Field is moving fast (4+ relevant papers in Dec 2025 - Feb 2026 alone)
