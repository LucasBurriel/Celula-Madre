# Reproducing Célula Madre Experiments

## Prerequisites

- Python 3.10+
- An OpenAI-compatible LLM endpoint (LM Studio, Groq, etc.)
- ~2GB disk for AG News data + results

## Setup

```bash
git clone https://github.com/LucasBurriel/Celula-Madre.git
cd Celula-Madre
pip install -r requirements.txt
```

## LLM Provider Configuration

The framework uses any OpenAI-compatible API. Configure in `src/llm_providers.py`:

```python
from src.llm_providers import LLMConfig, create_llm_fn

# Option 1: Local LM Studio (default)
config = LLMConfig(provider="lmstudio")  # http://localhost:1234

# Option 2: Groq (free tier: 30 rpm)
config = LLMConfig(provider="groq", api_key="gsk_...")

# Option 3: Any OpenAI-compatible endpoint
config = LLMConfig(provider="custom", base_url="http://your-server:8080", model="your-model")

llm = create_llm_fn(config)
```

## Reproducing V6 (AG News Classification — Main Result)

V6 is the key experiment: evolutionary prompt optimization on AG News 4-class text classification.

### Step 1: Download AG News data

```bash
python -c "from src.ag_news_data import load_ag_news_splits; load_ag_news_splits()"
```

This downloads AG News from HuggingFace and creates balanced splits:
- dev: 100 examples (for mutation evaluation)
- val: 100 examples (for gating/selection)
- test: 200 examples (final holdout)

Cached in `data/ag_news/splits.json`.

### Step 2: Verify LLM works

```bash
python scripts/test_ag_news_eval.py
```

Should output accuracy for 1 hardcoded agent on 5 examples.

### Step 3: Run V6 experiments (3 groups × 3 runs = 9 total)

```bash
# Reflective mutation (experimental group)
python scripts/run_v6.py --mode reflective --run 1
python scripts/run_v6.py --mode reflective --run 2
python scripts/run_v6.py --mode reflective --run 3

# Random mutation (control group 1)
python scripts/run_v6.py --mode random --run 1
python scripts/run_v6.py --mode random --run 2
python scripts/run_v6.py --mode random --run 3

# Static / no mutation (control group 2)
python scripts/run_v6.py --mode static --run 1
python scripts/run_v6.py --mode static --run 2
python scripts/run_v6.py --mode static --run 3
```

Each run takes ~4-6 hours with a local 30B model, ~1-2 hours with Groq.

All runs support `--resume` to continue from checkpoints after interruption.

Results saved to `results/v6/<mode>_run<N>/`.

### Step 4: Analyze results

```bash
python scripts/analyze_v6.py
```

### Expected Results (from our runs)

| Group | Run 1 | Run 2 | Run 3 | Mean | Std |
|-------|-------|-------|-------|------|-----|
| Reflective | 89.0% | 80.5% | 81.5% | 83.7% | 4.7% |
| Random | 87.0% | 78.5% | 84.5% | 83.3% | 4.3% |
| Static | — | — | — | ~79%* | — |

*Static runs were invalidated due to infrastructure issues (LM Studio model unloaded mid-run).

Key findings:
- **Evolution works:** Both reflective and random beat static baseline (p=0.041)
- **Reflective ≈ Random:** No significant difference (p=0.932, Cohen's d=0.091)
- **Population management matters more than mutation quality**

## Reproducing V6.5 (Market Selection — Ongoing)

V6.5 adds market-based selection (clients choose agents via softmax over performance).

```bash
# Market selection
python scripts/run_v6_market.py --group market --run 1

# Tournament selection (comparison)
python scripts/run_v6_market.py --group tournament --run 1
```

## Parameters Reference

| Parameter | V6 Value | V6.5 Value |
|-----------|----------|------------|
| Population | 8 | 8 |
| Generations | 10 | 10 |
| Dev set | 100 | 100 |
| Val set | 100 | 100 |
| Test set | 200 | 200 |
| Elite count | 2 | 2 |
| Gating tolerance | 0% (strict) | 3% (1 SE) |
| Temperature | 0.7 | 0.7 |
| Max tokens | 300 | 300 |

## Project Structure

```
src/
  ag_news_data.py      # Data pipeline (download, split, eval)
  evolution_v6.py       # V6 evolution engine (reflective/random/static)
  evolution_v6_market.py # V6.5 with market selection
  llm_providers.py      # Multi-provider LLM abstraction
  market_selection.py   # Market selection engine (softmax, revenue, survival)
scripts/
  run_v6.py            # V6 experiment runner
  run_v6_market.py     # V6.5 experiment runner
  analyze_v6.py        # Statistical analysis
results/               # Checkpoints and results (gitignored)
research/
  experiments/         # Analysis documents
  paper/               # LaTeX paper
```

## Citation

```bibtex
@article{tesla2026celula,
  title={C{\'e}lula Madre: Evolutionary Optimization of LLM Agent Prompts Through Selection Pressure},
  author={Tesla and Burriel, Lucas},
  year={2026},
  note={Preprint}
}
```
