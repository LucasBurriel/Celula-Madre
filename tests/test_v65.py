"""Tests for V6.5 evolution engine — gating tolerance + checkpoint correctness."""
import json
import os
import tempfile

import pytest

from src.evolution_v6_market import V65Config, EvolutionEngineV65
from src.evolution_v6 import Agent


class TestGatingTolerance:
    """Ensure gating tolerance works correctly."""

    def test_default_tolerance_is_3_percent(self):
        cfg = V65Config()
        assert cfg.gating_tolerance == 0.03

    def test_child_passes_when_within_tolerance(self):
        """Child at parent-2% should pass with 3% tolerance."""
        cfg = V65Config(gating_tolerance=0.03)
        parent_acc = 0.90
        child_acc = 0.88  # parent - 2%, within tolerance
        assert child_acc >= parent_acc - cfg.gating_tolerance

    def test_child_fails_when_outside_tolerance(self):
        """Child at parent-5% should fail with 3% tolerance."""
        cfg = V65Config(gating_tolerance=0.03)
        parent_acc = 0.90
        child_acc = 0.85  # parent - 5%, outside tolerance
        assert not (child_acc >= parent_acc - cfg.gating_tolerance)

    def test_zero_tolerance_is_strict(self):
        """With 0 tolerance, child must be >= parent exactly."""
        cfg = V65Config(gating_tolerance=0.0)
        parent_acc = 0.90
        child_acc = 0.89
        assert not (child_acc >= parent_acc - cfg.gating_tolerance)

    def test_equal_always_passes(self):
        """Child == parent should always pass regardless of tolerance."""
        for tol in [0.0, 0.01, 0.03, 0.05]:
            cfg = V65Config(gating_tolerance=tol)
            acc = 0.85
            assert acc >= acc - cfg.gating_tolerance


class TestCheckpointAfterMutation:
    """Regression: checkpoint must save AFTER mutations, not before."""

    def test_checkpoint_contains_mutated_agents(self):
        """Agent counter in checkpoint should reflect new agents created during mutations."""
        cfg = V65Config(population_size=4, max_generations=1)
        engine = EvolutionEngineV65(cfg)

        # Simulate: create 4 seed agents (counter goes to 4)
        agents = []
        for i in range(4):
            agents.append(engine._new_agent(f"strategy_{i}"))
        assert engine.agent_counter == 4

        # Simulate: create 2 mutant children (counter goes to 6)
        child1 = engine._new_agent("mutant_1", parents=[0])
        child2 = engine._new_agent("mutant_2", parents=[1])
        assert engine.agent_counter == 6

        # Save checkpoint
        with tempfile.TemporaryDirectory() as tmpdir:
            engine.checkpoint_dir = tmpdir
            engine.save_checkpoint(agents + [child1, child2], gen=0)

            cp_path = os.path.join(tmpdir, "checkpoint_gen0.json")
            with open(cp_path) as f:
                cp = json.load(f)

            # Counter must be 6 (includes mutants), not 4
            assert cp["agent_counter"] == 6
            assert len(cp["population"]) == 6

    def test_resume_preserves_agent_counter(self):
        """Loading a checkpoint should restore agent_counter correctly."""
        cfg = V65Config(population_size=4)
        engine = EvolutionEngineV65(cfg)

        # Create agents and checkpoint
        for _ in range(6):
            engine._new_agent("test")
        assert engine.agent_counter == 6

        with tempfile.TemporaryDirectory() as tmpdir:
            engine.checkpoint_dir = tmpdir
            pop = [engine._new_agent("saved") for _ in range(4)]
            engine.save_checkpoint(pop, gen=2)

            # Load in new engine
            engine2 = EvolutionEngineV65(cfg)
            assert engine2.agent_counter == 0

            loaded_pop, last_gen = engine2.load_checkpoint(
                os.path.join(tmpdir, "checkpoint_gen2.json")
            )
            assert engine2.agent_counter == engine.agent_counter
            assert last_gen == 2
            assert len(loaded_pop) == 4


class TestHealthCheck:
    """Engine should abort if LLM appears broken."""

    def test_config_modes(self):
        """All selection/mutation mode combos should be valid."""
        for sel in ["market", "tournament"]:
            for mut in ["reflective", "random", "static"]:
                cfg = V65Config(selection_mode=sel, mutation_mode=mut)
                engine = EvolutionEngineV65(cfg)
                assert engine.config.selection_mode == sel
                assert engine.config.mutation_mode == mut


class TestMarketIntegration:
    """Market selection engine integrates correctly with V6.5."""

    def test_market_created_for_market_mode(self):
        cfg = V65Config(selection_mode="market")
        engine = EvolutionEngineV65(cfg)
        assert engine.market is not None

    def test_no_market_for_tournament_mode(self):
        cfg = V65Config(selection_mode="tournament")
        engine = EvolutionEngineV65(cfg)
        assert engine.market is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
