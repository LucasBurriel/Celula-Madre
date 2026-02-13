# Célula Madre 🧬

**Evolutionary Optimization of LLM Agent Prompts Through Selection Pressure**

> Can selection pressure alone improve AI agent prompts — without modifying model weights?

Célula Madre ("stem cell" in Spanish) evolves LLM agent system prompts through iterative selection, mutation, and reproduction. Inspired by Austrian economics and Darwinian evolution.

**[📄 Paper (Preprint)](research/paper/latex/celula-madre.pdf)** · **[📊 Results](research/experiments/)** · **[🧪 Reproduce](REPRODUCTION.md)**

---

## Key Findings

| Finding | Evidence |
|---------|----------|
| ✅ **Evolution works** | +4.7pp over static baseline (p=0.041) on AG News 4-class classification |
| 🤔 **Reflective ≈ Random mutation** | Error-informed mutation provides no advantage over random (p=0.932, d=0.09) |
| 🏗️ **Population management > mutation quality** | Elitism, gating, and selection design drive improvement — not mutation sophistication |
| 🏪 **Market selection (preliminary)** | Austrian economics-inspired client choice shows promising diversity dynamics |

## Experiment History

| Version | Task | Key Result |
|---------|------|------------|
| V4 | Financial prediction (synthetic) | Guided mutation worse than random — over-exploration kills |
| V5 | BTC/ETH direction prediction | Framework validated, scale too small for conclusions |
| V6 | AG News 4-class classification | **Main result:** Evolution +4.7pp, reflective ≈ random |
| V6.5 | AG News + market selection | Preliminary: market dynamics working, run incomplete |
| V7 | Deal-or-No-Deal negotiation | Designed + implemented, blocked on compute |

## Quick Start

```bash
# Clone
git clone https://github.com/LucasBurriel/Celula-Madre.git
cd Celula-Madre

# Install dependencies
pip install -r requirements.txt

# Download AG News data
python -c "from src.ag_news_data import download_ag_news; download_ag_news()"

# Run V6 experiment (needs OpenAI-compatible LLM endpoint)
export LLM_ENDPOINT="http://localhost:1234"  # LM Studio, Ollama, etc.
python scripts/run_v6.py --mode reflective --run 1

# Analyze results
python scripts/analyze_v6.py
```

See **[REPRODUCTION.md](REPRODUCTION.md)** for detailed step-by-step instructions.

## Architecture

```
Population (8 agents) → Evaluate (dev set) → Select (tournament/market)
     ↑                                              ↓
     └──── Mutate (reflective/random) ← ── Reproduce (top agents)
```

**Selection modes:**
- **Tournament** (V6): Top-k elitism, deterministic
- **Market** (V6.5/V7): Clients choose agents via softmax over track record (Austrian economics price signal)

**Mutation modes:**
- **Reflective**: LLM analyzes errors and proposes targeted improvements
- **Random**: LLM generates variation without error context
- **Static**: No mutation (control group)

## Project Structure

```
src/
├── ag_news_data.py          # AG News dataset pipeline
├── evolution_v6.py          # V6 evolution engine (tournament selection)
├── evolution_v6_market.py   # V6.5 engine (market selection)
├── evolution_v7.py          # V7 engine (negotiation task)
├── market_selection.py      # Market selection engine
├── negotiation.py           # Deal-or-No-Deal game engine
├── llm_providers.py         # Multi-provider LLM abstraction
└── market_data.py           # BTC/ETH data pipeline

scripts/
├── run_v6.py                # Run V6 experiments
├── run_v6_market.py         # Run V6.5 market experiments
├── run_v7.py                # Run V7 negotiation experiments
├── analyze_v6.py            # Statistical analysis
└── fetch_market_data.py     # Download price data

research/
├── paper/                   # Academic paper (LaTeX + PDF)
├── experiments/             # Detailed experiment analyses
├── literature/              # Literature review
└── competitive-analysis.md  # Comparison with related work
```

## Citation

```bibtex
@misc{tesla2026celula,
  title={Célula Madre: Evolutionary Optimization of LLM Agent Prompts Through Selection Pressure},
  author={Tesla and Burriel, Lucas},
  year={2026},
  note={Preprint}
}
```

## License

MIT License. See [LICENSE](LICENSE).

---

*Built by [Tesla](https://github.com/LucasBurriel/Celula-Madre) ⚡ — an AI research agent named after a cat.*
