#!/usr/bin/env python3
"""Quick test: verify OpenRouter provider works for AG News eval.

Usage:
  OPENROUTER_API_KEY=sk-or-... python3 scripts/test_openrouter.py
  # or
  python3 scripts/test_openrouter.py --api-key sk-or-...
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.evolution_v6 import call_llm
from src.ag_news_data import load_splits, evaluate_agent, LABELS
from src.llm_providers import LLMConfig, create_llm_fn, check_provider


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", default=os.environ.get("OPENROUTER_API_KEY", ""))
    parser.add_argument("--model", default="qwen/qwen3-coder:free")
    parser.add_argument("--examples", type=int, default=10)
    args = parser.parse_args()

    if not args.api_key:
        print("❌ No API key. Set OPENROUTER_API_KEY or use --api-key")
        sys.exit(1)

    # 1. Health check
    print(f"Testing OpenRouter ({args.model})...")
    cfg = LLMConfig(provider="openrouter", api_key=args.api_key, model=args.model)
    result = check_provider(cfg)
    if result["ok"]:
        print(f"  ✅ Connected: {result['response']} ({result['latency_ms']}ms)")
    else:
        print(f"  ❌ Failed: {result['error']}")
        sys.exit(1)

    # 2. AG News eval with a simple strategy
    print(f"\nEvaluating on {args.examples} AG News examples...")
    splits = load_splits()
    test_examples = splits["dev"][:args.examples]

    strategy = """Classify news articles into exactly one category:
- World: International affairs, diplomacy, wars, foreign policy
- Sports: Athletic events, scores, players, teams, competitions
- Business: Markets, companies, economy, finance, trade
- Sci/Tech: Technology, science discoveries, computing, space

Reply with ONLY the category name."""

    def llm_fn(sys_prompt, user_msg):
        return call_llm(
            sys_prompt, user_msg,
            provider="openrouter", api_key=args.api_key,
            model=args.model, temperature=0.1, max_tokens=50,
        )

    t0 = time.time()
    result = evaluate_agent(strategy, test_examples, llm_fn)
    elapsed = time.time() - t0

    print(f"  Accuracy: {result['accuracy']:.1%} ({result['correct']}/{result['total']})")
    print(f"  Time: {elapsed:.1f}s ({elapsed/args.examples:.1f}s/example)")
    print(f"  Per class: {result.get('per_class', {})}")

    # 3. Estimate full V6.5 run
    per_example_s = elapsed / args.examples
    full_run_calls = 8 * 100 * 10 * 2  # pop * examples * gens * ~2 evals
    full_run_hours = (full_run_calls * per_example_s) / 3600
    print(f"\n📊 Full V6.5 run estimate:")
    print(f"  ~{full_run_calls} LLM calls")
    print(f"  ~{full_run_hours:.1f} hours at {per_example_s:.1f}s/call")
    print(f"  Rate limit: check OpenRouter dashboard for remaining credits")


if __name__ == "__main__":
    main()
