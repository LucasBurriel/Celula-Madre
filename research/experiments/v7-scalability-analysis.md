# V7 Architecture & Scalability Analysis

**Date:** 2026-02-12  
**Author:** Tesla ⚡  
**Status:** Complete

## 1. The Problem

V7 (Deal-or-No-Deal negotiation) is computationally expensive. Each agent evaluation requires multi-turn dialogues (5 turns × 2 players = 10 LLM calls per scenario). At full experiment scale (12 runs × 10 gens × 8 agents × 60 scenarios), this is **~577K LLM calls**.

Previous attempts to run V7 with local LLMs failed repeatedly:
- Qwen3-30B: too slow (~6s/call), processes died from OOM/timeouts
- gemma-3-4b: faster but lower quality, still too slow for full scale
- LM Studio availability unreliable (models unloaded without warning)

## 2. Call Volume Breakdown

### Per Negotiation
| Component | Calls | Tokens (est.) |
|-----------|-------|---------------|
| Agent turns | 5 | ~1,500 |
| Opponent turns | 5 | ~1,500 |
| **Total per negotiation** | **10** | **~3,000** |

### Per Generation (pop=8, dev=60)
| Component | Negotiations | Calls | Tokens |
|-----------|-------------|-------|--------|
| Evaluation | 8 × 60 = 480 | 4,800 | 1.44M |
| Mutations | ~6 | 6 | ~3K |
| Gating | ~6 × 10 scenarios | 600 | 180K |
| **Total per gen** | **~546** | **~5,406** | **~1.62M** |

### Full Experiment (12 runs × 10 gens)
| Scale | Negotiations | Calls | Tokens |
|-------|-------------|-------|--------|
| 1 run | ~5,460 | ~54,060 | ~16.2M |
| 12 runs | ~65,520 | ~648,720 | ~194.6M |

## 3. Cost/Time Estimates by Provider

### Cost per Full Experiment (12 runs)

| Provider | Model | $/MTok (in/out) | Est. Cost | Speed (tok/s) | Time Est. |
|----------|-------|-----------------|-----------|---------------|-----------|
| **LM Studio** | Qwen3-30B | $0 | **$0** | ~30 | ~90h |
| **LM Studio** | gemma-3-4b | $0 | **$0** | ~100 | ~27h |
| **Groq** (paid) | llama-3.3-70b | $0.59/0.79 | **~$153** | ~300 | ~9h |
| **Groq** (free) | llama-3.3-70b | $0 | **$0** | ~300 | ~45 days* |
| **Together** | Llama-3.3-70B-Turbo | $0.88/0.88 | **~$171** | ~200 | ~14h |
| **OpenRouter** | llama-3.3-70b | varies | **~$130-200** | varies | ~10-20h |
| **Claude** | Sonnet 3.5 | $3/15 | **~$3,500** | ~80 | ~34h |

*Groq free: 14,400 req/day limit → 45 days for 648K calls

### Minimal Proof-of-Concept (2 groups × 1 run, pop=4, 5 gens, 20 scenarios)

| Provider | Calls | Tokens | Cost | Time |
|----------|-------|--------|------|------|
| **LM Studio** (gemma) | ~4,000 | ~1.2M | $0 | ~1.5h |
| **Groq** (free) | ~4,000 | ~1.2M | $0 | ~7h** |
| **Groq** (paid) | ~4,000 | ~1.2M | ~$1 | ~20min |
| **Together** | ~4,000 | ~1.2M | ~$1 | ~30min |

**Groq free with 30 RPM limit

## 4. Architecture Refactoring

### What Changed: `src/llm_providers.py`

New multi-provider abstraction layer:

```python
from src.llm_providers import create_llm_fn, LLMConfig

# Switch providers with one line
config = LLMConfig(provider="groq", api_key="gsk_...")
llm = create_llm_fn(config)

# Same interface as before: (system_prompt, user_prompt) -> str
response = llm("You are a negotiator.", "Make your offer.")
```

**Supported providers:**
1. **lmstudio** — Local, free, no API key needed
2. **groq** — Fast inference, built-in rate limiting (30 RPM free)
3. **openrouter** — Access to many models
4. **together** — Good price/performance
5. **custom** — Any OpenAI-compatible endpoint

**Key features:**
- Drop-in replacement for existing `call_llm()`
- Built-in rate limiting (per-provider RPM)
- Automatic retry with exponential backoff
- 429 detection with longer waits
- Async support via `create_async_llm_fn()` (requires aiohttp)
- Provider health check: `check_provider(config)`

### Async Support (Future Parallelism)

```python
from src.llm_providers import create_async_llm_fn, async_evaluate_batch

# Evaluate multiple scenarios concurrently
results = await async_evaluate_batch(
    agent_prompt, scenarios, opponent_prompt,
    config=LLMConfig(provider="groq"),
    max_concurrent=5,
)
```

This could reduce wall-clock time significantly for cloud APIs that support parallel requests. Not yet integrated into the evolution loop (would need `evolution_v7.py` changes).

### Integration Path

To use cloud APIs with existing V7 runner:

```python
# In scripts/run_v7.py or evolution_v7.py
from src.llm_providers import create_llm_fn, LLMConfig

config = LLMConfig(provider="groq", api_key=os.environ["GROQ_API_KEY"])
llm_fn = create_llm_fn(config)

# Pass to evaluation
evaluate_agent(agent_prompt, scenarios, llm_fn=llm_fn)
```

The existing code already accepts `llm_fn` parameter — no changes needed to negotiation.py or evolution_v7.py core logic.

## 5. Recommendations

### Short-term (unblock V7)
1. **Best:** Get LM Studio reliable with gemma-3-4b (free, ~27h for full experiment)
2. **Fallback:** Run minimal PoC on Groq free tier (~$0, ~7h)
3. **If budget available:** Groq paid ~$153 for full experiment, ~9h

### Medium-term (scalability)
1. Integrate async evaluation for cloud APIs (2-3x speedup from parallelism)
2. Add response caching (same prompt+scenario → cached result) to reduce repeat calls
3. Consider model distillation: train a small classifier to approximate negotiation outcomes for pre-screening

### Long-term (production)
1. Hybrid: use cheap/fast model for initial screening, expensive model for final evaluation
2. Multi-provider failover: if one API goes down, auto-switch to another
3. Cost tracking: log tokens used per run for budget management

## 6. Files Modified

- **NEW:** `src/llm_providers.py` — Multi-provider LLM abstraction with sync/async support
- **REF:** `research/experiments/v7-infra-options.md` — Original cost analysis (complemented by this doc)
