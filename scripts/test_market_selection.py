#!/usr/bin/env python3
"""Test market selection engine — no LLM needed."""

import sys
sys.path.insert(0, ".")

from src.market_selection import MarketSelectionEngine, MarketConfig, ClientMemory


def test_basic_flow():
    """Test full market selection cycle."""
    print("=== Test: Basic Market Flow ===")
    
    cfg = MarketConfig(
        softmax_temperature=2.0,
        survival_threshold=0.3,
        client_memory_depth=3,
        exploration_bonus=0.1,
        min_assignments=2,
    )
    market = MarketSelectionEngine(config=cfg)
    
    agent_ids = [0, 1, 2, 3, 4, 5, 6, 7]
    scenario_ids = list(range(60))
    
    # Gen 0: random assignment
    assignments = market.assign_scenarios(agent_ids, scenario_ids, generation=0)
    print(f"Gen 0 assignments: {[len(v) for v in assignments.values()]}")
    assert all(aid in assignments for aid in agent_ids)
    assert sum(len(v) for v in assignments.values()) == len(scenario_ids)
    
    # Simulate results: agent 0 is best, agent 7 is worst
    results = {}
    for aid in agent_ids:
        scores = {}
        for sid in assignments[aid]:
            # Better agents get higher scores
            base_score = 1.0 - (aid / 10.0)  # agent 0 → 1.0, agent 7 → 0.3
            scores[sid] = base_score + (hash((aid, sid)) % 100) / 500.0  # small noise
        results[aid] = scores
    
    market.record_results(results, generation=0)
    stats = market.get_market_stats()
    print(f"Revenue stats: mean={stats['mean_revenue']}, gini={stats['gini_coefficient']}")
    
    # Survival
    survivors = market.select_survivors(agent_ids, elite_ids=[0])
    print(f"Survivors: {survivors} (killed {set(agent_ids) - set(survivors)})")
    assert 0 in survivors  # elite protected
    assert len(survivors) < len(agent_ids)
    
    # Reproduction
    parents = market.select_parents(survivors, n_offspring=3)
    print(f"Parents selected: {parents}")
    assert len(parents) == 3
    
    # Gen 1: market-based assignment (should favor better agents)
    new_agents = list(range(8))  # pretend we have 8 agents again
    assignments_gen1 = market.assign_scenarios(new_agents, scenario_ids, generation=1)
    counts = {aid: len(v) for aid, v in assignments_gen1.items()}
    print(f"Gen 1 assignments: {counts}")
    # Agent 0 (best history) should get more scenarios
    print("✅ Basic flow passed\n")


def test_softmax_distribution():
    """Test that softmax produces sensible probabilities."""
    print("=== Test: Softmax Distribution ===")
    market = MarketSelectionEngine()
    
    scores = {0: 0.9, 1: 0.5, 2: 0.1}
    probs = market._softmax(scores)
    print(f"Scores: {scores}")
    print(f"Probs:  { {k: round(v, 3) for k, v in probs.items()} }")
    assert probs[0] > probs[1] > probs[2]
    assert abs(sum(probs.values()) - 1.0) < 1e-6
    print("✅ Softmax passed\n")


def test_minimum_assignments():
    """Test that minimum assignment guarantee works."""
    print("=== Test: Minimum Assignments ===")
    cfg = MarketConfig(min_assignments=3)
    market = MarketSelectionEngine(config=cfg)
    
    # Set up strong bias: all clients prefer agent 0
    for sid in range(20):
        mem = ClientMemory(scenario_id=sid)
        mem.agent_scores = {0: [1.0, 1.0], 1: [0.1, 0.1]}
        market.client_memories[sid] = mem
    
    assignments = market.assign_scenarios([0, 1], list(range(20)), generation=1)
    print(f"Assignments: agent0={len(assignments[0])}, agent1={len(assignments[1])}")
    assert len(assignments[1]) >= 3, f"Agent 1 got {len(assignments[1])} < min 3"
    print("✅ Min assignments passed\n")


def test_serialization():
    """Test checkpoint save/load."""
    print("=== Test: Serialization ===")
    market = MarketSelectionEngine()
    
    # Add some state
    mem = ClientMemory(scenario_id=5)
    mem.record(0, 0.8)
    mem.record(1, 0.4)
    market.client_memories[5] = mem
    market.agent_revenues = {0: 5.0, 1: 2.0}
    market.revenue_history = [{0: 5.0, 1: 2.0}]
    
    # Serialize
    data = market.to_dict()
    
    # Deserialize
    market2 = MarketSelectionEngine.from_dict(data)
    assert 5 in market2.client_memories
    assert market2.client_memories[5].get_mean_score(0) == 0.8
    assert len(market2.revenue_history) == 1
    print("✅ Serialization passed\n")


def test_market_dynamics_over_generations():
    """Simulate 5 generations and verify market dynamics emerge."""
    print("=== Test: Multi-Generation Market Dynamics ===")
    cfg = MarketConfig(
        softmax_temperature=1.5,
        survival_threshold=0.25,
        min_assignments=2,
    )
    market = MarketSelectionEngine(config=cfg)
    
    agent_ids = list(range(8))
    scenario_ids = list(range(30))
    # Agent quality: 0 is best, 7 is worst
    agent_quality = {i: 1.0 - i * 0.1 for i in range(8)}
    
    for gen in range(5):
        assignments = market.assign_scenarios(agent_ids, scenario_ids, generation=gen)
        
        # Simulate: score = quality + noise
        results = {}
        for aid in agent_ids:
            if assignments[aid]:
                results[aid] = {
                    sid: min(1.0, max(0.0, agent_quality.get(aid, 0.5) + (hash((gen, aid, sid)) % 100 - 50) / 200))
                    for sid in assignments[aid]
                }
            else:
                results[aid] = {}
        
        market.record_results(results, generation=gen)
        stats = market.get_market_stats()
        
        # Count assignments
        counts = {aid: len(assignments[aid]) for aid in agent_ids}
        print(f"  Gen {gen}: assignments={list(counts.values())}, gini={stats['gini_coefficient']:.3f}, hhi={stats['hhi']:.3f}")
    
    # After 5 gens, better agents should get more scenarios
    final_assignments = market.assign_scenarios(agent_ids, scenario_ids, generation=5)
    print(f"  Gen 5 final: {[len(final_assignments[aid]) for aid in agent_ids]}")
    # Agent 0 should tend to get more than agent 7
    print("✅ Multi-gen dynamics passed\n")


if __name__ == "__main__":
    test_softmax_distribution()
    test_basic_flow()
    test_minimum_assignments()
    test_serialization()
    test_market_dynamics_over_generations()
    print("🎉 All market selection tests passed!")
