"""Célula Madre V6.5 — Market Selection on AG News.

Tests whether market-based selection (Austrian economics) outperforms
tournament selection on the same task (AG News classification).

Key difference from V6:
  - Tournament: all agents evaluated on ALL examples, ranked by accuracy
  - Market: each example ("client") chooses an agent based on history,
    agents earn revenue from correct classifications, revenue determines
    reproduction and survival.

Uses MarketSelectionEngine from V7 + AG News eval from V6.
"""

import json
import os
import random
import time
from dataclasses import dataclass, field
from typing import Optional

from src.ag_news_data import LABELS, evaluate_agent, load_splits
from src.market_selection import MarketConfig, MarketSelectionEngine
from src.evolution_v6 import (
    Agent, SEED_STRATEGIES, call_llm,
    reflective_mutate, random_mutate,
)


@dataclass
class V65Config:
    population_size: int = 8
    max_generations: int = 10
    elitism_count: int = 2
    fresh_injection: int = 1
    gating_tolerance: float = 0.03    # Accept child if child_acc >= parent_acc - tolerance
    mutation_mode: str = "reflective"  # "reflective" | "random" | "static"
    selection_mode: str = "market"     # "market" | "tournament"
    market_config: MarketConfig = field(default_factory=MarketConfig)
    llm_kwargs: dict = field(default_factory=dict)


class EvolutionEngineV65:
    """V6.5: AG News evolution with market or tournament selection."""

    def __init__(self, config: V65Config):
        self.config = config
        self.agent_counter = 0
        self.generation = 0
        self.history: list[dict] = []
        self.checkpoint_dir: Optional[str] = None
        self.market = MarketSelectionEngine(config.market_config) if config.selection_mode == "market" else None

    def _new_agent(self, strategy: str, parents: list[int] = []) -> Agent:
        a = Agent(
            id=self.agent_counter,
            strategy_prompt=strategy,
            generation=self.generation,
            parents=parents,
        )
        self.agent_counter += 1
        return a

    def _eval_agent_on_examples(self, agent: Agent, examples: list) -> dict:
        """Evaluate agent on a list of examples. Returns evaluate_agent result."""
        def llm_fn(sys_prompt, user_msg):
            return call_llm(
                sys_prompt, user_msg,
                temperature=0.1, max_tokens=50,
                **self.config.llm_kwargs,
            )
        return evaluate_agent(agent.strategy_prompt, examples, llm_fn)

    def _eval_agent_on_indices(self, agent: Agent, all_examples: list, indices: list[int]) -> dict:
        """Evaluate agent on specific example indices."""
        subset = [all_examples[i] for i in indices]
        return self._eval_agent_on_examples(agent, subset)

    def save_checkpoint(self, population: list[Agent], gen: int, extra: dict = {}):
        if not self.checkpoint_dir:
            return
        cp = {
            "generation": gen,
            "agent_counter": self.agent_counter,
            "selection_mode": self.config.selection_mode,
            "mutation_mode": self.config.mutation_mode,
            "history": self.history,
            "population": [a.to_dict() for a in population],
            "market_state": self.market.to_dict() if self.market else None,
            **extra,
        }
        path = os.path.join(self.checkpoint_dir, f"checkpoint_gen{gen}.json")
        latest = os.path.join(self.checkpoint_dir, "checkpoint_latest.json")
        for p in (path, latest):
            with open(p, "w") as f:
                json.dump(cp, f, indent=2, ensure_ascii=False)
        print(f"  💾 Checkpoint: {path}")

    def load_checkpoint(self, filepath: str) -> tuple[list[Agent], int]:
        with open(filepath) as f:
            cp = json.load(f)
        self.agent_counter = cp["agent_counter"]
        self.history = cp["history"]
        population = [Agent.from_dict(d) for d in cp["population"]]
        if cp.get("market_state") and self.market:
            self.market = MarketSelectionEngine.from_dict(cp["market_state"])
        return population, cp["generation"]

    def _tournament_generation(self, population: list[Agent], dev_examples: list, val_examples: list, gen: int) -> list[Agent]:
        """Standard tournament selection (same as V6)."""
        cfg = self.config

        # Evaluate ALL agents on ALL dev examples
        for agent in population:
            result = self._eval_agent_on_examples(agent, dev_examples)
            agent.dev_accuracy = result["accuracy"]
            agent.dev_errors = result["errors"]
            agent.per_class = result["per_class"]
            print(f"  Agent {agent.id} (gen{agent.generation}): dev={agent.dev_accuracy:.1%}")

        # Validate on val set
        for agent in population:
            result = self._eval_agent_on_examples(agent, val_examples)
            agent.val_accuracy = result["accuracy"]

        ranked = sorted(population, key=lambda a: a.val_accuracy, reverse=True)
        return ranked

    def _market_generation(self, population: list[Agent], dev_examples: list, val_examples: list, gen: int) -> list[Agent]:
        """Market-based selection: clients choose agents."""
        cfg = self.config

        agent_ids = [a.id for a in population]
        agent_map = {a.id: a for a in population}
        scenario_ids = list(range(len(dev_examples)))

        # Phase 1: Clients assign scenarios to agents
        assignments = self.market.assign_scenarios(agent_ids, scenario_ids, gen)
        
        for aid in agent_ids:
            print(f"  Agent {aid}: assigned {len(assignments[aid])} dev examples")

        # Phase 2: Evaluate each agent on assigned examples, track per-example results
        results_for_market: dict[int, dict[int, float]] = {}
        for agent in population:
            assigned = assignments[agent.id]
            if not assigned:
                agent.dev_accuracy = 0.0
                agent.dev_errors = []
                agent.per_class = {}
                results_for_market[agent.id] = {}
                continue

            # Evaluate on assigned subset
            subset = [dev_examples[i] for i in assigned]
            result = self._eval_agent_on_examples(agent, subset)
            agent.dev_accuracy = result["accuracy"]
            agent.dev_errors = result["errors"]
            agent.per_class = result["per_class"]

            # Map results back to scenario indices for market
            # Each example was evaluated in order, so result tracks match subset order
            scenario_scores = {}
            correct_set = set()
            for err in result["errors"]:
                # errors contain the wrong ones; everything else was correct
                pass
            # Simpler: re-derive from accuracy and count
            n_correct = int(result["accuracy"] * len(subset))
            # We need per-example scores. Use a simple approach:
            # evaluate_agent returns errors list with text/true/predicted
            error_texts = {e["text"][:100] for e in result["errors"]}
            for i, idx in enumerate(assigned):
                ex = subset[i]
                text_key = ex["text"][:100]
                scenario_scores[idx] = 0.0 if text_key in error_texts else 1.0
            results_for_market[agent.id] = scenario_scores

            print(f"  Agent {agent.id} (gen{agent.generation}): dev={agent.dev_accuracy:.1%} ({len(assigned)} examples)")

        # Phase 3: Record results in market
        self.market.record_results(results_for_market, gen)
        stats = self.market.get_market_stats()
        print(f"  📊 Market: Gini={stats.get('gini_coefficient', 0):.3f}, HHI={stats.get('hhi', 0):.3f}")

        # Phase 4: Validate ALL agents on full val set (for fair comparison)
        for agent in population:
            result = self._eval_agent_on_examples(agent, val_examples)
            agent.val_accuracy = result["accuracy"]

        ranked = sorted(population, key=lambda a: a.val_accuracy, reverse=True)
        return ranked

    def run(
        self,
        dev_examples: list,
        val_examples: list,
        test_examples: list,
        seed_strategies: list[str] = SEED_STRATEGIES,
        checkpoint_dir: str = None,
        resume_from: str = None,
    ) -> dict:
        """Run full evolution."""
        cfg = self.config
        self.checkpoint_dir = checkpoint_dir
        if checkpoint_dir:
            os.makedirs(checkpoint_dir, exist_ok=True)

        start_gen = 0
        if resume_from and os.path.exists(resume_from):
            population, last_gen = self.load_checkpoint(resume_from)
            start_gen = last_gen + 1
            print(f"  ⏩ Resuming from gen {start_gen}")
        else:
            population = []
            for s in seed_strategies[:cfg.population_size]:
                population.append(self._new_agent(s))
            while len(population) < cfg.population_size:
                population.append(self._new_agent(random.choice(seed_strategies)))

        for gen in range(start_gen, cfg.max_generations):
            self.generation = gen
            gen_start = time.time()
            mode_label = f"{cfg.selection_mode.upper()}×{cfg.mutation_mode.upper()}"
            print(f"\n{'='*50}\n[{mode_label}] Generation {gen}/{cfg.max_generations}\n{'='*50}")

            # Evaluate + rank
            if cfg.selection_mode == "market":
                ranked = self._market_generation(population, dev_examples, val_examples, gen)
            else:
                ranked = self._tournament_generation(population, dev_examples, val_examples, gen)

            gen_best = ranked[0]
            print(f"  Gen {gen} best: Agent {gen_best.id} val={gen_best.val_accuracy:.1%}")

            # Health check: abort if LLM is broken (all agents 0%)
            if gen == 0 and all(a.val_accuracy == 0.0 for a in ranked):
                print("  ❌ ABORT: All agents scored 0% on val set. LLM likely broken/unloaded.")
                raise RuntimeError("LLM health check failed: all agents scored 0% in gen 0")

            market_stats = self.market.get_market_stats() if self.market else {}
            gen_info = {
                "generation": gen,
                "selection_mode": cfg.selection_mode,
                "mutation_mode": cfg.mutation_mode,
                "agents": [
                    {"id": a.id, "gen": a.generation, "dev": round(a.dev_accuracy, 4),
                     "val": round(a.val_accuracy, 4), "parents": a.parents}
                    for a in ranked
                ],
                "best_val": round(gen_best.val_accuracy, 4),
                "mean_val": round(sum(a.val_accuracy for a in population) / len(population), 4),
                "duration_sec": round(time.time() - gen_start, 1),
                "market_stats": market_stats,
            }
            self.history.append(gen_info)

            if gen >= cfg.max_generations - 1:
                self.save_checkpoint(population, gen)
                break

            if cfg.mutation_mode == "static":
                self.save_checkpoint(population, gen)
                continue

            # Build next generation
            new_pop = []

            # Elitism (always by val accuracy)
            elite = ranked[:cfg.elitism_count]
            elite_ids = [a.id for a in elite]
            for a in elite:
                new_pop.append(a)
                print(f"  👑 Elite: Agent {a.id} (val={a.val_accuracy:.1%})")

            mutation_slots = cfg.population_size - cfg.elitism_count - cfg.fresh_injection

            if cfg.selection_mode == "market" and self.market:
                # Market: survival + proportional reproduction
                survivors = self.market.select_survivors(
                    [a.id for a in population], elite_ids=elite_ids
                )
                survivor_agents = {a.id: a for a in population if a.id in survivors}
                parent_ids = self.market.select_parents(
                    list(survivor_agents.keys()), mutation_slots
                )
                parents_for_mutation = [survivor_agents[pid] for pid in parent_ids]
            else:
                # Tournament: pick best of 3 random
                parents_for_mutation = []
                for _ in range(mutation_slots):
                    candidates = random.sample(population, min(3, len(population)))
                    parent = max(candidates, key=lambda a: a.val_accuracy)
                    parents_for_mutation.append(parent)

            for parent in parents_for_mutation:
                if cfg.mutation_mode == "reflective":
                    child_strategy = reflective_mutate(parent, cfg.llm_kwargs)
                else:
                    child_strategy = random_mutate(parent, cfg.llm_kwargs)

                child = self._new_agent(child_strategy, parents=[parent.id])

                # Gating
                child_result = self._eval_agent_on_examples(child, val_examples)
                child.val_accuracy = child_result["accuracy"]

                tolerance = cfg.gating_tolerance
                if child.val_accuracy >= parent.val_accuracy - tolerance:
                    new_pop.append(child)
                    delta = child.val_accuracy - parent.val_accuracy
                    marker = "✓" if delta >= 0 else "≈"
                    print(f"  {marker} Mutation: {parent.id}→{child.id} ({parent.val_accuracy:.1%}→{child.val_accuracy:.1%}, Δ={delta:+.1%})")
                else:
                    new_pop.append(parent)
                    print(f"  ✗ Rejected: {parent.id}→{child.id} ({parent.val_accuracy:.1%}→{child.val_accuracy:.1%})")

            # Fresh injection
            for _ in range(cfg.fresh_injection):
                fresh = self._new_agent(random.choice(seed_strategies))
                new_pop.append(fresh)
                print(f"  🌱 Fresh: Agent {fresh.id}")

            population = new_pop[:cfg.population_size]
            # Save checkpoint AFTER mutations so resume loads mutated population
            self.save_checkpoint(population, gen)

        # Final test
        print(f"\n{'='*50}\nFinal Test ({cfg.selection_mode}×{cfg.mutation_mode})\n{'='*50}")
        best_agent = max(population, key=lambda a: a.val_accuracy)
        test_result = self._eval_agent_on_examples(best_agent, test_examples)
        test_acc = test_result["accuracy"]
        print(f"Best Agent {best_agent.id}: val={best_agent.val_accuracy:.1%} test={test_acc:.1%}")

        return {
            "selection_mode": cfg.selection_mode,
            "mutation_mode": cfg.mutation_mode,
            "best_agent_id": best_agent.id,
            "best_agent_generation": best_agent.generation,
            "best_agent_strategy": best_agent.strategy_prompt,
            "best_val_accuracy": round(best_agent.val_accuracy, 4),
            "test_accuracy": round(test_acc, 4),
            "test_per_class": {k: round(v["accuracy"], 3) for k, v in test_result["per_class"].items()},
            "history": self.history,
            "config": {
                "population_size": cfg.population_size,
                "max_generations": cfg.max_generations,
                "selection_mode": cfg.selection_mode,
                "mutation_mode": cfg.mutation_mode,
            },
        }
