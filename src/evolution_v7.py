"""Célula Madre V7 — Market-Based Selection on Deal-or-No-Deal Negotiation.

Four-group experiment:
  A: Tournament × Reflective mutation
  B: Market × Random mutation  
  C: Market × Reflective mutation (full Célula Madre vision)
  D: Tournament × Random mutation (control)

Reuses: negotiation engine (src/negotiation.py), market selection (src/market_selection.py).
"""

import json
import os
import random
import time
from dataclasses import dataclass, field
from typing import Optional

from src.negotiation import (
    call_llm, evaluate_agent, load_scenarios, generate_splits,
    save_scenarios, SEED_STRATEGIES, FIXED_OPPONENT_PROMPT, ITEM_TYPES,
)
from src.market_selection import MarketSelectionEngine


# ── Agent ───────────────────────────────────────────────────────────

@dataclass
class Agent:
    id: str
    name: str
    prompt: str
    generation: int = 0
    parent_id: Optional[str] = None
    val_score: float = 0.0
    dev_score: float = 0.0
    test_score: float = 0.0

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "prompt": self.prompt,
            "generation": self.generation,
            "parent_id": self.parent_id,
            "val_score": self.val_score,
            "dev_score": self.dev_score,
            "test_score": self.test_score,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# ── Mutation ────────────────────────────────────────────────────────

REFLECTIVE_MUTATION_PROMPT = """You are an AI prompt engineer specializing in negotiation strategy optimization.

An agent with the following negotiation strategy was evaluated:

STRATEGY:
{strategy}

PERFORMANCE SUMMARY:
- Average normalized score: {mean_score:.2%}
- Deal rate: {deal_rate:.0%} ({n_deals}/{n_total} scenarios resulted in deals)
- Sample failures (scenarios where score was low):
{failures}

TASK: Analyze what's wrong with this strategy and create an IMPROVED version.

Think about:
1. Is the agent too aggressive/passive? 
2. Is it failing to identify opponent preferences?
3. Is it making invalid proposals?
4. Is it conceding too much or too little?
5. Are there specific tactical improvements?

OUTPUT: Write ONLY the improved strategy prompt (no explanation, no preamble). The prompt should be a complete negotiation strategy instruction, similar in format to the original but with specific improvements."""

RANDOM_MUTATION_PROMPT = """You are an AI prompt engineer. Create a variation of this negotiation strategy prompt.

ORIGINAL:
{strategy}

Make random changes: adjust thresholds, change tactics, reword instructions, add or remove rules.
Don't try to optimize — just create a different version.

OUTPUT: Write ONLY the new strategy prompt (no explanation, no preamble)."""


def reflective_mutate(agent: Agent, eval_results: dict, llm_fn=None) -> str:
    """Generate improved prompt via error analysis."""
    if llm_fn is None:
        llm_fn = call_llm

    # Find worst scenarios
    deals = eval_results.get("deals", [])
    failures = sorted(deals, key=lambda d: d.get("normalized", 0))[:5]
    failure_text = "\n".join(
        f"  - {d['scenario_id']}: score={d.get('normalized', 0):.2f}, "
        f"agreed={d.get('agreed', False)}, error={d.get('error', 'none')}"
        for d in failures
    )

    prompt = REFLECTIVE_MUTATION_PROMPT.format(
        strategy=agent.prompt,
        mean_score=eval_results["mean_score"],
        deal_rate=eval_results["deal_rate"],
        n_deals=sum(1 for d in deals if d.get("agreed")),
        n_total=len(deals),
        failures=failure_text,
    )
    return llm_fn("You are a prompt optimization expert.", prompt, max_tokens=600)


def random_mutate(agent: Agent, llm_fn=None) -> str:
    """Generate random variation of prompt."""
    if llm_fn is None:
        llm_fn = call_llm
    prompt = RANDOM_MUTATION_PROMPT.format(strategy=agent.prompt)
    return llm_fn("You are a prompt engineer.", prompt, max_tokens=600)


# ── Evolution Engine ────────────────────────────────────────────────

class EvolutionEngineV7:
    """V7 evolution engine with tournament or market selection."""

    def __init__(
        self,
        mode: str = "tournament_reflective",  # tournament_reflective|market_random|market_reflective|tournament_random
        population_size: int = 8,
        num_generations: int = 10,
        elite_count: int = 2,
        tournament_k: int = 3,
        dev_scenarios: int = 60,
        val_scenarios: int = 60,
        max_turns: int = 5,
        results_dir: str = "results/v7",
        llm_fn=None,
    ):
        self.mode = mode
        self.pop_size = population_size
        self.num_gens = num_generations
        self.elite_count = elite_count
        self.tournament_k = tournament_k
        self.dev_scenarios = dev_scenarios
        self.val_scenarios = val_scenarios
        self.max_turns = max_turns
        self.results_dir = results_dir
        self.llm_fn = llm_fn or call_llm

        # Parse mode
        parts = mode.split("_", 1)
        self.selection_type = parts[0]  # "tournament" or "market"
        self.mutation_type = parts[1] if len(parts) > 1 else "reflective"

        # Market engine (if needed)
        self.market = None
        if self.selection_type == "market":
            from src.market_selection import MarketConfig
            self.market = MarketSelectionEngine(
                config=MarketConfig(
                    softmax_temperature=2.0,
                    survival_threshold=0.3,
                    client_memory_depth=3,
                    min_assignments=2,
                )
            )

        os.makedirs(results_dir, exist_ok=True)

    def _create_seeds(self) -> list:
        """Create initial population from seed strategies."""
        agents = []
        for i, seed in enumerate(SEED_STRATEGIES[:self.pop_size]):
            agents.append(Agent(
                id=f"gen0_{seed['name']}",
                name=seed["name"],
                prompt=seed["prompt"],
                generation=0,
            ))
        return agents

    def _evaluate_population(self, population: list, scenarios: list) -> dict:
        """Evaluate all agents on given scenarios."""
        results = {}
        for agent in population:
            print(f"    Evaluating {agent.id}...", flush=True)
            result = evaluate_agent(
                agent.prompt, scenarios,
                llm_fn=self.llm_fn,
                max_turns=self.max_turns,
            )
            results[agent.id] = result
            agent.dev_score = result["mean_score"]
            print(f"      Score: {result['mean_score']:.2%}, "
                  f"Deal rate: {result['deal_rate']:.0%}")
        return results

    def _tournament_select(self, population: list) -> Agent:
        """Tournament selection."""
        candidates = random.sample(population, min(self.tournament_k, len(population)))
        return max(candidates, key=lambda a: a.dev_score)

    def _mutate(self, agent: Agent, eval_results: dict = None) -> str:
        """Generate mutated prompt based on mutation type."""
        if self.mutation_type == "reflective" and eval_results:
            return reflective_mutate(agent, eval_results, self.llm_fn)
        else:
            return random_mutate(agent, self.llm_fn)

    def _gate(self, child_prompt: str, parent: Agent, val_scenarios: list) -> tuple:
        """Gating: child must beat parent on val set."""
        child_result = evaluate_agent(
            child_prompt, val_scenarios,
            llm_fn=self.llm_fn, max_turns=self.max_turns,
        )
        parent_result = evaluate_agent(
            parent.prompt, val_scenarios,
            llm_fn=self.llm_fn, max_turns=self.max_turns,
        )
        passed = child_result["mean_score"] >= parent_result["mean_score"]
        return passed, child_result["mean_score"], parent_result["mean_score"]

    def _save_checkpoint(self, generation: int, population: list, history: list):
        """Save checkpoint."""
        cp_dir = os.path.join(self.results_dir, "checkpoints")
        os.makedirs(cp_dir, exist_ok=True)
        data = {
            "generation": generation,
            "mode": self.mode,
            "population": [a.to_dict() for a in population],
            "history": history,
            "config": {
                "population_size": self.pop_size,
                "num_generations": self.num_gens,
                "elite_count": self.elite_count,
                "tournament_k": self.tournament_k,
            },
        }
        path = os.path.join(cp_dir, f"checkpoint_gen{generation}.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        # Also save as latest
        with open(os.path.join(cp_dir, "checkpoint_latest.json"), "w") as f:
            json.dump(data, f, indent=2)

    def _load_checkpoint(self) -> tuple:
        """Load latest checkpoint if exists. Returns (generation, population, history) or None."""
        cp_path = os.path.join(self.results_dir, "checkpoints", "checkpoint_latest.json")
        if not os.path.exists(cp_path):
            return None
        with open(cp_path) as f:
            data = json.load(f)
        population = [Agent.from_dict(a) for a in data["population"]]
        return data["generation"], population, data.get("history", [])

    def run(self, scenarios: dict, resume: bool = True):
        """Run the evolution experiment.
        
        scenarios: dict with 'dev', 'val', 'test' keys.
        """
        dev = scenarios["dev"][:self.dev_scenarios]
        val = scenarios["val"][:self.val_scenarios]
        test = scenarios["test"]

        # Resume or start fresh
        start_gen = 0
        history = []
        checkpoint = self._load_checkpoint() if resume else None
        if checkpoint:
            start_gen, population, history = checkpoint
            start_gen += 1  # Resume from next gen
            print(f"Resumed from gen {start_gen - 1}", flush=True)
        else:
            population = self._create_seeds()

        for gen in range(start_gen, self.num_gens):
            print(f"\n{'='*60}", flush=True)
            print(f"Generation {gen}/{self.num_gens} | Mode: {self.mode}", flush=True)
            print(f"{'='*60}", flush=True)

            # Evaluate on dev set
            print("  Evaluating population on dev set...")
            eval_results = self._evaluate_population(population, dev)

            # Record generation stats
            scores = [a.dev_score for a in population]
            gen_stats = {
                "generation": gen,
                "mean_score": sum(scores) / len(scores),
                "best_score": max(scores),
                "worst_score": min(scores),
                "best_agent": max(population, key=lambda a: a.dev_score).id,
                "population_size": len(population),
            }
            history.append(gen_stats)
            print(f"  Gen {gen} stats: mean={gen_stats['mean_score']:.2%}, "
                  f"best={gen_stats['best_score']:.2%}")

            # Selection + Reproduction
            if gen < self.num_gens - 1:
                # Sort by fitness
                population.sort(key=lambda a: a.dev_score, reverse=True)
                elites = population[:self.elite_count]
                new_pop = list(elites)  # Elites survive

                if self.selection_type == "tournament":
                    # Tournament selection for remaining slots
                    while len(new_pop) < self.pop_size:
                        parent = self._tournament_select(population)
                        child_prompt = self._mutate(parent, eval_results.get(parent.id))
                        child_name = f"gen{gen+1}_{parent.name}_mut{len(new_pop)}"

                        # Gating on small val subset
                        val_subset = random.sample(val, min(15, len(val)))
                        passed, child_score, parent_score = self._gate(
                            child_prompt, parent, val_subset
                        )
                        if passed:
                            child = Agent(
                                id=child_name, name=child_name,
                                prompt=child_prompt, generation=gen + 1,
                                parent_id=parent.id, val_score=child_score,
                            )
                            new_pop.append(child)
                            print(f"    ✓ {child_name} passed gating "
                                  f"({child_score:.2%} >= {parent_score:.2%})")
                        else:
                            # Failed gating — clone parent with small tweak
                            new_pop.append(Agent(
                                id=child_name, name=child_name,
                                prompt=parent.prompt, generation=gen + 1,
                                parent_id=parent.id,
                            ))
                            print(f"    ✗ {child_name} failed gating "
                                  f"({child_score:.2%} < {parent_score:.2%}), cloning parent")

                elif self.selection_type == "market":
                    # Map string agent IDs to ints for MarketSelectionEngine
                    id_to_idx = {a.id: i for i, a in enumerate(population)}
                    idx_to_agent = {i: a for i, a in enumerate(population)}
                    int_agent_ids = list(range(len(population)))
                    int_scenario_ids = list(range(len(dev)))

                    # Market assigns scenarios to agents
                    assignments = self.market.assign_scenarios(
                        int_agent_ids, int_scenario_ids, generation=gen
                    )

                    # Record results: {agent_int_id: {scenario_int_id: score}}
                    results_map = {}
                    for idx, agent in idx_to_agent.items():
                        assigned = assignments.get(idx, [])
                        scores_map = {}
                        for sid in assigned:
                            # Use overall dev score as proxy (all scenarios evaluated)
                            scores_map[sid] = eval_results[agent.id]["mean_score"]
                        if scores_map:
                            results_map[idx] = scores_map
                    self.market.record_results(results_map, gen)

                    # Select survivors (elites get immunity)
                    elite_idxs = [id_to_idx[a.id] for a in elites]
                    survivor_idxs = self.market.select_survivors(int_agent_ids, elite_idxs)
                    survivor_agents = [idx_to_agent[i] for i in survivor_idxs]

                    # Reproduce via market's parent selection
                    n_needed = self.pop_size - len(new_pop)
                    parent_idxs = self.market.select_parents(survivor_idxs, n_needed)

                    for pidx in parent_idxs:
                        parent = idx_to_agent[pidx]
                        child_prompt = self._mutate(parent, eval_results.get(parent.id))
                        child_name = f"gen{gen+1}_{parent.name}_mkt{len(new_pop)}"

                        child = Agent(
                            id=child_name, name=child_name,
                            prompt=child_prompt, generation=gen + 1,
                            parent_id=parent.id,
                        )
                        new_pop.append(child)
                        rev = self.market.agent_revenues.get(pidx, 0)
                        print(f"    + {child_name} (parent revenue: {rev:.2f})", flush=True)

                population = new_pop[:self.pop_size]

            # Checkpoint
            self._save_checkpoint(gen, population, history)

        # Final evaluation on test set
        print(f"\n{'='*60}", flush=True)
        print("FINAL: Evaluating best agent on test set")
        print(f"{'='*60}", flush=True)
        best = max(population, key=lambda a: a.dev_score)
        test_result = evaluate_agent(
            best.prompt, test,
            llm_fn=self.llm_fn, max_turns=self.max_turns, verbose=True,
        )
        best.test_score = test_result["mean_score"]

        # Save final results
        final = {
            "mode": self.mode,
            "best_agent": best.to_dict(),
            "test_accuracy": test_result["mean_score"],
            "test_deal_rate": test_result["deal_rate"],
            "history": history,
            "population": [a.to_dict() for a in population],
        }
        with open(os.path.join(self.results_dir, "results.json"), "w") as f:
            json.dump(final, f, indent=2)

        print(f"\n🏆 Best agent: {best.id}", flush=True)
        print(f"   Test score: {test_result['mean_score']:.2%}", flush=True)
        print(f"   Deal rate: {test_result['deal_rate']:.0%}", flush=True)
        return final
