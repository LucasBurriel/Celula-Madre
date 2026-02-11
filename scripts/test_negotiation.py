"""Test V7 negotiation engine with a mock LLM (no LM Studio needed)."""
import sys
sys.path.insert(0, ".")

from src.negotiation import (
    Scenario, Deal, ScenarioGenerator, generate_splits,
    parse_proposal, run_negotiation, evaluate_agent,
    FIXED_OPPONENT_PROMPT, SEED_STRATEGIES, ITEM_TYPES,
    save_scenarios, load_scenarios,
)


def test_scenario_generation():
    splits = generate_splits(seed=42)
    assert len(splits["dev"]) == 60
    assert len(splits["val"]) == 60
    assert len(splits["test"]) == 80

    for split_name, scenarios in splits.items():
        for s in scenarios:
            assert s.max_possible_agent > 0, f"{s.id} has zero agent value"
            assert s.max_possible_opponent > 0, f"{s.id} has zero opp value"
            total_items = sum(s.items[t] for t in ITEM_TYPES)
            assert 5 <= total_items <= 10, f"{s.id} has {total_items} items"
    print("✓ Scenario generation OK (200 scenarios, all valid)")


def test_deal_scoring():
    s = Scenario(
        id="test",
        items={"books": 3, "hats": 2, "balls": 1},
        agent_values={"books": 2, "hats": 1, "balls": 3},
        opponent_values={"books": 1, "hats": 3, "balls": 2},
    )
    # Agent takes 2 books + 1 ball = 2*2 + 1*3 = 7
    # Opponent takes 1 book + 2 hats = 1*1 + 2*3 = 7
    d = Deal(
        agent_gets={"books": 2, "hats": 0, "balls": 1},
        opponent_gets={"books": 1, "hats": 2, "balls": 0},
    )
    assert d.is_valid(s)
    assert d.agent_score(s) == 7
    assert d.opponent_score(s) == 7
    assert d.normalized_agent_score(s) == 7 / 11  # max = 3*2 + 2*1 + 1*3 = 11
    print("✓ Deal scoring OK")


def test_no_deal():
    s = Scenario(
        id="test",
        items={"books": 1, "hats": 1, "balls": 1},
        agent_values={"books": 1, "hats": 1, "balls": 1},
        opponent_values={"books": 1, "hats": 1, "balls": 1},
    )
    d = Deal(
        agent_gets={"books": 0, "hats": 0, "balls": 0},
        opponent_gets={"books": 0, "hats": 0, "balls": 0},
        agreed=False,
    )
    assert d.agent_score(s) == 0
    assert d.normalized_agent_score(s) == 0
    print("✓ No-deal scoring OK")


def test_parse_proposal():
    s = Scenario(
        id="test",
        items={"books": 3, "hats": 2, "balls": 1},
        agent_values={"books": 1, "hats": 1, "balls": 1},
        opponent_values={"books": 1, "hats": 1, "balls": 1},
    )
    text = "PROPOSE: I get [2 books, 1 hat, 1 ball], you get [1 book, 1 hat, 0 balls]\nREASONING: Fair split."
    deal = parse_proposal(text, s, "agent")
    assert deal is not None
    assert deal.agent_gets["books"] == 2
    assert deal.opponent_gets["books"] == 1
    print("✓ Proposal parsing OK")

    # Invalid split (too many items)
    text2 = "PROPOSE: I get [3 books, 2 hats, 1 ball], you get [3 books, 2 hats, 1 ball]"
    deal2 = parse_proposal(text2, s, "agent")
    assert deal2 is None
    print("✓ Invalid proposal rejected OK")


def test_mock_negotiation():
    """Test negotiation with a deterministic mock LLM."""
    s = Scenario(
        id="test",
        items={"books": 2, "hats": 2, "balls": 2},
        agent_values={"books": 3, "hats": 1, "balls": 2},
        opponent_values={"books": 1, "hats": 3, "balls": 2},
    )

    call_count = [0]

    def mock_llm(system, user):
        call_count[0] += 1
        if call_count[0] == 1:  # Agent opens
            return "PROPOSE: I get [2 books, 0 hats, 1 ball], you get [0 books, 2 hats, 1 ball]\nREASONING: I want the books."
        elif call_count[0] == 2:  # Opponent responds
            return "ACCEPT\nREASONING: Fair enough."
        return "ACCEPT"

    deal, dialogue = run_negotiation(
        "You are agent.", "You are opponent.", s,
        max_turns=5, llm_fn=mock_llm,
    )
    assert deal.agreed
    assert deal.agent_gets["books"] == 2
    assert deal.agent_score(s) == 2 * 3 + 0 * 1 + 1 * 2  # = 8
    assert len(dialogue) == 2
    print(f"✓ Mock negotiation OK (score={deal.agent_score(s)}, turns={len(dialogue)})")


def test_evaluate_with_mock():
    """Test evaluation pipeline with mock LLM."""
    scenarios = generate_splits(seed=42)["dev"][:3]

    call_count = [0]

    def mock_llm(system, user):
        call_count[0] += 1
        # Alternating: agent proposes, opponent accepts
        if call_count[0] % 2 == 1:
            return "PROPOSE: I get [1 books, 1 hats, 1 balls], you get [1 books, 1 hats, 1 balls]\nREASONING: Fair."
        return "ACCEPT\nREASONING: OK."

    results = evaluate_agent(
        "Test agent", scenarios, llm_fn=mock_llm, verbose=True,
    )
    print(f"✓ Evaluation OK (mean={results['mean_score']:.2f}, "
          f"deal_rate={results['deal_rate']:.0%}, n={results['n_scenarios']})")


def test_save_load():
    splits = generate_splits(seed=42)
    save_scenarios(splits, "data/v7_scenarios_test.json")
    reloaded = load_scenarios("data/v7_scenarios_test.json")
    assert len(reloaded["dev"]) == 60
    assert reloaded["dev"][0].id == splits["dev"][0].id
    assert reloaded["dev"][0].max_possible_agent == splits["dev"][0].max_possible_agent
    import os
    os.remove("data/v7_scenarios_test.json")
    print("✓ Save/Load OK")


if __name__ == "__main__":
    test_scenario_generation()
    test_deal_scoring()
    test_no_deal()
    test_parse_proposal()
    test_mock_negotiation()
    test_evaluate_with_mock()
    test_save_load()
    print("\n✅ All tests passed!")
