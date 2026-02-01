# Cell Regulation — Applied to Agent Evolution

## Biological mechanisms and their analogs

### 1. Apoptosis (Programmed Cell Death)
- **Bio:** Cells have internal death clocks. Also die when receiving external "death signals" or when DNA damage is irreparable.
- **Current:** Lifespan retirement (15 txs) + bankruptcy.
- **Missing:** No death signal from the MARKET. In biology, cells that aren't receiving growth signals die. We should kill agents that go N transactions without being selected by ANY client.
- **Improvement:** "Starvation death" — if an agent isn't selected for 20+ marketplace rounds, it dies. The market is voting with its feet.

### 2. Differentiation (Specialization)
- **Bio:** Stem cells become specialized (neuron, muscle, skin) based on environmental signals. Differentiated cells are BETTER at their niche but can't do everything.
- **Current:** All agents try to be generic "helpful coders". No pressure to specialize.
- **Missing:** Agents should evolve toward serving specific client types. A "minimalist specialist" that only serves MinimalistClient well should outperform a generalist.
- **Improvement:** Track which client type gives each agent the most revenue. During mutation, tell the LLM "this agent performs best with clients who value X — lean into that."
- **Key insight:** Specialization is how biological systems achieve efficiency. A generalist cell wastes energy. A specialized cell is optimal for its niche.

### 3. Mutation Rate Regulation (DNA Repair)
- **Bio:** Too few mutations = no adaptation (extinction). Too many = cancer (non-functional offspring). Cells have repair mechanisms that control mutation rate dynamically.
- **Current:** Every mutation is equally aggressive. No control over HOW MUCH changes.
- **Improvement:** 
  - Successful parents → conservative mutations (preserve what works, small tweaks)
  - Unsuccessful parents → aggressive mutations (big changes, nothing to lose)
  - This is like biological "stress-induced mutagenesis" — cells under stress mutate MORE

### 4. Sexual Reproduction (Crossover/Recombination)
- **Bio:** Two parents contribute DNA, creating novel combinations. This is THE key advantage of sex over cloning — it creates diversity without destroying what works.
- **Current:** Single parent, mutated. This is asexual reproduction. Leads to convergence.
- **Improvement:** Select TWO parents, combine their best traits. "Take the brevity focus from Parent A and the documentation style from Parent B."
- **This is probably the single biggest improvement we can make.**

### 5. Contact Inhibition (Population Density Control)
- **Bio:** Cells stop dividing when surrounded by other cells. Prevents tumors.
- **Current:** Population grows without limit, old agents accumulate.
- **Improvement:** Cap active population at N. If full, new agent only born if it REPLACES the worst performer. This creates real competitive pressure.

### 6. Niche Partitioning (Ecology)
- **Bio:** Species that occupy the same niche compete most fiercely (competitive exclusion principle). Stable ecosystems have species in DIFFERENT niches.
- **Current:** All agents compete in the same generic niche.
- **Improvement:** Anti-convergence pressure. If two agents have very similar prompts, one should die (competitive exclusion). This FORCES diversification.

### 7. Growth Factors / Signaling
- **Bio:** Cells only divide when receiving external growth signals. No signal = no division.
- **Analog:** Evolution should only happen when there's market demand for it. If all clients are satisfied, don't evolve. If some client type is underserved, create agents for that niche.

### 8. Epigenetics (Context-Dependent Expression)
- **Bio:** Same DNA, different expression based on environment. A liver cell and a brain cell have the same genome but express different genes.
- **Future idea:** Same base agent, different behavior depending on client context. Not for V4 but interesting for later.

## V4 Design Priorities

Based on biological insights, ranked by expected impact:

1. **Crossover reproduction** (sexual recombination) — biggest diversity win
2. **Niche specialization** — push agents toward client-specific excellence
3. **Adaptive mutation rate** — conservative for winners, aggressive for losers
4. **Population cap with replacement** — competitive pressure
5. **Better mutation prompts** — Qwen needs better instructions for diverse mutations
6. **Starvation death** — unused agents die

## The Qwen Problem

Qwen is generating bland, convergent mutations. Options:
- A) Better mutation prompts (more specific, demand creativity)
- B) Higher temperature (more randomness)
- C) Use thinking mode / chain of thought to force more creative mutations
- D) Two-step: first analyze what's DIFFERENT about top performers, then mutate toward that difference

Going with A + B + C for V4.
