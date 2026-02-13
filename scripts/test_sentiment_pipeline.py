#!/usr/bin/env python3
"""Test V8 sentiment data pipeline without LLM."""
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent))

from src.sentiment_data import load_splits, parse_sentiment, SEED_STRATEGIES, DOMAINS

def test_splits():
    splits = load_splits()
    for name, examples in splits.items():
        print(f"\n{name}: {len(examples)} examples")
        # Check domain balance
        domains = {}
        labels = {}
        for e in examples:
            domains[e["domain"]] = domains.get(e["domain"], 0) + 1
            labels[e["label"]] = labels.get(e["label"], 0) + 1
        print(f"  Domains: {domains}")
        print(f"  Labels: {labels}")
        # Verify all domains present
        for d in DOMAINS:
            assert d in domains, f"Missing domain {d} in {name}"
        # Verify labels
        for l in ["positive", "negative"]:
            assert l in labels, f"Missing label {l} in {name}"

def test_parse():
    cases = [
        ("positive", "positive"),
        ("Positive.", "positive"),
        ("NEGATIVE", "negative"),
        ("The sentiment is positive.", "positive"),
        ("I think this is negative overall", "negative"),
        ("positive\n", "positive"),
    ]
    for inp, expected in cases:
        result = parse_sentiment(inp)
        status = "✓" if result == expected else "✗"
        print(f"  {status} parse('{inp.strip()}') = '{result}' (expected '{expected}')")
        assert result == expected, f"Failed: {inp} -> {result}"

def test_strategies():
    print(f"\n{len(SEED_STRATEGIES)} seed strategies:")
    for i, s in enumerate(SEED_STRATEGIES):
        print(f"  {i+1}. {s[:80]}...")
    assert len(SEED_STRATEGIES) == 8

def test_eval_mock():
    """Test evaluate_agent with a mock LLM."""
    from src.sentiment_data import evaluate_agent
    splits = load_splits()
    
    # Mock LLM that always says "positive"
    def mock_llm(system, user):
        return "positive"
    
    result = evaluate_agent(mock_llm, "test", splits["dev"][:10])
    print(f"\nMock eval (always positive, 10 examples):")
    print(f"  Overall: {result['accuracy']:.1%} ({result['correct']}/{result['total']})")
    for d, s in result["per_domain"].items():
        if s["total"] > 0:
            print(f"  {d}: {s['accuracy']:.1%} ({s['correct']}/{s['total']})")

if __name__ == "__main__":
    print("=== V8 Sentiment Pipeline Test ===")
    print("\n1. Testing splits...")
    test_splits()
    print("\n2. Testing parse_sentiment...")
    test_parse()
    print("\n3. Testing seed strategies...")
    test_strategies()
    print("\n4. Testing evaluate_agent (mock)...")
    test_eval_mock()
    print("\n✓ All tests passed!")
