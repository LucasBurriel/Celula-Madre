# Cloud API Options for V6.5 Experiments

**Date:** 2026-02-12 | **Author:** Tesla ⚡

## Problem
LM Studio on Lucas's PC keeps dying (models unloaded, OOM, etc.). V6.5 experiments have been blocked for 2+ days. We need a reliable alternative.

## Option 1: OpenRouter Free Tier (RECOMMENDED)
- **33 free models** available including strong ones:
  - `qwen/qwen3-coder:free` (262K ctx) — same family as our local Qwen3
  - `openai/gpt-oss-120b:free` (131K ctx)
  - `deepseek/deepseek-r1-0528:free` (163K ctx)
  - `nvidia/nemotron-3-nano-30b-a3b:free` (256K ctx)
- **Rate limits:** Unknown for free tier, likely ~20-60 RPM
- **Signup:** Required (free account at openrouter.ai)
- **Cost:** $0 for :free models
- **Quality:** Qwen3-coder free should match our local Qwen3-30B
- **Estimate:** 1 V6.5 run ≈ 16K calls. At 30 RPM = ~9h. At 60 RPM = ~4.5h.

## Option 2: Groq Free Tier
- **Models:** llama-3.3-70b (30 RPM, 1K RPD), llama-3.1-8b (30 RPM, 14.4K RPD)
- **Problem:** llama-3.3-70b only 1K RPD — way too low for experiments
- **llama-3.1-8b:** 14.4K RPD might work for 1 run but quality questionable for AG News
- **Signup:** Required (free at console.groq.com)
- **Speed:** Very fast (LPU inference)

## Option 3: Groq Developer Plan ($0.10/M tokens for llama-3.1-8b)
- Higher limits, very cheap
- Still needs signup + payment method

## Recommendation
1. **Ask Lucas to sign up for OpenRouter** (free, takes 2 min)
2. Use `qwen/qwen3-coder:free` for V6.5 experiments
3. Adapter already exists in `src/llm_providers.py` — just need the API key
4. Fallback: Groq with llama-3.1-8b if OpenRouter rate limits are too tight

## V6.5 Experiment Feasibility
- 1 full run (10 gens, 8 agents, 100 dev + 100 val examples): ~16K LLM calls
- 6 runs total (3 market + 3 tournament): ~96K calls
- At 30 RPM: ~53h total (~9h per run) — feasible over 3-4 days
- At 60 RPM: ~27h total (~4.5h per run) — feasible in 2 days
