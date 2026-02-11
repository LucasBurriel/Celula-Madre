# V7 Infrastructure Options — Bypassing LM Studio Dependency

**Date:** 2026-02-11
**Author:** Tesla ⚡
**Problem:** TASK-017 (V7 experiments) blocked for 2+ days because LM Studio has no models loaded. Need alternative.

## Call Volume Estimate

Per DESIGN-V7.md: 4 groups × 3 runs = 12 runs.
Per run (10 gens, 8 agents, 60 dev scenarios):
- **Evaluation:** 8 agents × 60 scenarios × ~5 turns × 2 players = ~4,800 LLM calls/gen × 10 gens = 48,000 per run
- **Mutation:** ~6 mutations/gen × 10 gens = 60 per run
- **Total per run:** ~48,060 calls
- **Total 12 runs:** ~576,720 calls

At ~300 tokens avg per call: ~173M tokens total.

## Option Analysis

### A) Wait for LM Studio (current approach)
- **Cost:** $0
- **Risk:** Indefinite delay, depends on Lucas loading models
- **Verdict:** ❌ Already waited 2 days, not reliable

### B) Claude API (current model)
- Sonnet: ~$3/MTok input, $15/MTok output → ~$173×3 + $173×15 ≈ $3,114
- **Verdict:** ❌ Way too expensive

### C) Google Gemini Flash (free tier)
- 2.0 Flash: free tier = 15 RPM, 1M TPD
- At 1M tokens/day, need ~173 days
- **Verdict:** ❌ Too slow for free tier

### D) Groq (free tier)
- Free: 30 RPM, 14,400 RPD for llama-3.3-70b
- At 14,400 calls/day: ~40 days for all 12 runs
- Paid: $0.59/$0.79 per MTok → ~$173×0.59 + $173×0.79 ≈ $239
- **Verdict:** ⚠️ Paid is viable but still expensive

### E) Minimal V7 proof-of-concept (reduce scale)
- 2 groups × 1 run, 5 gens, 4 agents, 20 dev scenarios
- Per run: 4 agents × 20 scenarios × 5 turns × 2 = 800 calls/gen × 5 = 4,000
- 2 runs: ~8,000 calls, ~2.4M tokens
- **With Groq free:** ~0.6 days (feasible!)
- **With Gemini Flash free:** ~2.4 days
- **Verdict:** ✅ This is the move

### F) Ask Lucas to load models
- Simple, $0, fast
- **Verdict:** ✅ Best option if Lucas is available

## Decision

**Primary:** Ask Lucas to load Qwen3-30B in LM Studio (Option F).
**Fallback:** Run minimal V7 proof-of-concept with Groq free tier (Option E).

For the proof-of-concept:
- Market×Reflective vs Tournament×Random (the two most different groups)
- 1 run each, 5 gens, 4 agents, 20 dev scenarios
- ~8,000 LLM calls, feasible with free API
- Enough to validate negotiation + market mechanics work before committing to full scale

## Implementation: Groq Fallback

The codebase uses OpenAI-compatible API. Just change:
```python
base_url = "https://api.groq.com/openai"  
model = "llama-3.3-70b-versatile"
# Add API key header
```

Need to add API key support to `call_llm()` function.
