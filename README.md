# Célula Madre

**Price-Driven Evolution of AI Agents via Market Selection**

An experimental system where AI agents evolve based on market price signals rather than traditional benchmarks, inspired by Austrian economics and Darwinian selection.

## Core Hypothesis

Can price signals from a competitive marketplace guide agent evolution more effectively than random mutation?

## Status: V5 In Progress

### Completed Experiments

| Version | What | Result |
|---------|------|--------|
| MVP-1 | Basic marketplace + mutation | ✅ Agents evolved, prices emerged |
| MVP-2 | Generational death + client choice | ✅ Gen1 > Gen0, validated core hypothesis |
| V3 | Clade-Metaproductivity selection | ⚠️ Mixed results |
| V4 | Control group (random vs guided) | ❌ Random mutation won — guided over-explored |
| V5 | GEPA-style reflective mutation + real market data | 🔄 In progress |

### V4 Key Finding
Guided evolution with LLM-driven mutation **lost** to random mutation (Cohen's d = -2.01, p < 0.0001). Root causes: over-exploration (too many agents), no elitism, feedback overfitting.

### V5 Design (current)
- **Task:** BTC/ETH price direction prediction (real historical data)
- **Population:** 8 agents, 10-20 generations
- **Selection:** Elitism (top-2 survive), tournament selection
- **Mutation:** GEPA-style reflective mutation (LLM analyzes failures)
- **Gating:** New prompts must beat parent on dev set
- **Diversity:** Fitness sharing to prevent convergence

## Project Structure

```
├── main_v5.py              # V5 experiment runner
├── src/
│   ├── evolution_v5.py     # V5 evolution engine
│   ├── market_data.py      # BTC/ETH data pipeline
│   ├── agent.py            # Agent class
│   ├── database.py         # SQLite persistence
│   └── ...                 # Earlier version modules
├── scripts/
│   └── fetch_market_data.py # Data download script
├── research/
│   ├── experiments/         # Statistical analyses
│   │   ├── v4-statistical-analysis.md
│   │   └── v4-conclusions-and-v5-decisions.md
│   ├── cell-physiology-deep.md
│   └── cell-regulation-notes.md
├── data/                   # Market data (BTC/ETH OHLCV)
├── checkpoints/            # V5 evolution checkpoints
├── archive/                # Old versions, DBs, scripts
├── logs/                   # Experiment logs (v3, v4, v5)
├── DESIGN-V5.md            # V5 detailed design document
└── hayek.pdf               # Reference: Hayek on price signals
```

## Research

Analysis documents in `research/experiments/`:
- **v4-statistical-analysis.md** — Full statistical analysis of V4 (t-test, bootstrap CI, Cohen's d)
- **v4-conclusions-and-v5-decisions.md** — What went wrong in V4 and design decisions for V5

## Author

Developed by **Tesla** ⚡ (AI research agent), project granted by Lucas Burriel.

Repository: [github.com/LucasBurriel/Celula-Madre](https://github.com/LucasBurriel/Celula-Madre)
