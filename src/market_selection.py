"""Célula Madre V7 — Market-Based Selection Engine.

Implements Austrian-economics-inspired selection where "clients" (scenarios)
choose agents based on historical performance, creating endogenous fitness
through revenue accumulation rather than centralized tournament scoring.

Key differences from tournament selection:
  - Fitness is emergent: agents earn revenue from client choices
  - Popular agents get more evaluations (richer signal)
  - Unpopular agents starve (fewer evals, noisier fitness)
  - Reproduction is proportional to revenue (not rank)
  - Diversity is preserved through niche specialization
"""

import math
import random
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ClientMemory:
    """A client's memory of agent performance on their scenario."""
    scenario_id: int
    # {agent_id: [score_gen0, score_gen1, ...]} — most recent `memory_depth` entries
    agent_scores: dict[int, list[float]] = field(default_factory=dict)

    def record(self, agent_id: int, score: float, memory_depth: int = 3):
        """Record an agent's performance on this scenario."""
        if agent_id not in self.agent_scores:
            self.agent_scores[agent_id] = []
        self.agent_scores[agent_id].append(score)
        # Keep only last `memory_depth` scores
        if len(self.agent_scores[agent_id]) > memory_depth:
            self.agent_scores[agent_id] = self.agent_scores[agent_id][-memory_depth:]

    def get_mean_score(self, agent_id: int) -> Optional[float]:
        """Get mean historical score for an agent."""
        scores = self.agent_scores.get(agent_id)
        if not scores:
            return None
        return sum(scores) / len(scores)

    def prune_dead_agents(self, alive_ids: set[int]):
        """Remove memories of agents that no longer exist."""
        self.agent_scores = {
            aid: scores for aid, scores in self.agent_scores.items()
            if aid in alive_ids
        }


@dataclass
class MarketConfig:
    """Configuration for market-based selection."""
    softmax_temperature: float = 2.0     # Higher = more exploratory client choices
    survival_threshold: float = 0.3      # Bottom 30% by revenue dies
    client_memory_depth: int = 3         # How many generations clients remember
    exploration_bonus: float = 0.1       # Bonus score for unknown agents (encourages trying new ones)
    min_assignments: int = 3             # Minimum scenarios per agent (prevents total starvation)


class MarketSelectionEngine:
    """Market-based selection: clients choose agents, revenue determines fitness.
    
    Flow per generation:
      1. assign_scenarios() — clients choose agents based on history
      2. (external) evaluate each agent on its assigned scenarios
      3. record_results() — update client memories and agent revenues
      4. select_survivors() — kill agents below survival threshold
      5. reproduce() — agents with more revenue get more offspring
    """

    def __init__(self, config: MarketConfig = MarketConfig()):
        self.config = config
        self.client_memories: dict[int, ClientMemory] = {}  # scenario_id → memory
        self.agent_revenues: dict[int, float] = {}  # agent_id → total revenue this gen
        self.revenue_history: list[dict[int, float]] = []  # per-generation revenue snapshots

    def _softmax(self, scores: dict[int, float]) -> dict[int, float]:
        """Softmax over agent scores to get selection probabilities."""
        if not scores:
            return {}
        t = self.config.softmax_temperature
        # Shift for numerical stability
        max_s = max(scores.values())
        exp_scores = {aid: math.exp((s - max_s) / t) for aid, s in scores.items()}
        total = sum(exp_scores.values())
        if total == 0:
            # Uniform
            n = len(scores)
            return {aid: 1.0 / n for aid in scores}
        return {aid: e / total for aid, e in exp_scores.items()}

    def assign_scenarios(
        self,
        agent_ids: list[int],
        scenario_ids: list[int],
        generation: int,
    ) -> dict[int, list[int]]:
        """Assign scenarios to agents based on client preferences.
        
        Returns: {agent_id: [scenario_ids assigned to this agent]}
        
        Gen 0: random assignment (no history).
        Gen 1+: clients choose agents via softmax over historical scores.
        """
        assignments: dict[int, list[int]] = {aid: [] for aid in agent_ids}

        if generation == 0:
            # Random assignment: each scenario goes to a random agent
            for sid in scenario_ids:
                chosen = random.choice(agent_ids)
                assignments[chosen].append(sid)
        else:
            # Market-based: each client chooses an agent
            for sid in scenario_ids:
                memory = self.client_memories.get(sid)

                if memory is None or not memory.agent_scores:
                    # No history for this scenario — random
                    chosen = random.choice(agent_ids)
                else:
                    # Build scores for available agents
                    scores = {}
                    for aid in agent_ids:
                        mean = memory.get_mean_score(aid)
                        if mean is not None:
                            scores[aid] = mean
                        else:
                            # Unknown agent gets exploration bonus
                            scores[aid] = self.config.exploration_bonus

                    # Sample from softmax distribution
                    probs = self._softmax(scores)
                    agents = list(probs.keys())
                    weights = [probs[a] for a in agents]
                    chosen = random.choices(agents, weights=weights, k=1)[0]

                assignments[chosen].append(sid)

        # Enforce minimum assignments (prevent total starvation)
        self._enforce_minimums(assignments, scenario_ids, agent_ids)

        return assignments

    def _enforce_minimums(
        self,
        assignments: dict[int, list[int]],
        scenario_ids: list[int],
        agent_ids: list[int],
    ):
        """Ensure every agent gets at least min_assignments scenarios."""
        min_a = self.config.min_assignments
        starved = [aid for aid in agent_ids if len(assignments[aid]) < min_a]
        if not starved:
            return

        # Find agents with excess scenarios
        avg = len(scenario_ids) / len(agent_ids)
        for aid in starved:
            needed = min_a - len(assignments[aid])
            # Steal from over-assigned agents
            donors = sorted(
                [a for a in agent_ids if len(assignments[a]) > avg],
                key=lambda a: len(assignments[a]),
                reverse=True,
            )
            for donor in donors:
                if needed <= 0:
                    break
                while len(assignments[donor]) > min_a and needed > 0:
                    scenario = assignments[donor].pop()
                    assignments[aid].append(scenario)
                    needed -= 1

    def record_results(
        self,
        results: dict[int, dict[int, float]],  # {agent_id: {scenario_id: score}}
        generation: int,
    ):
        """Record evaluation results: update client memories and compute revenues.
        
        Args:
            results: {agent_id: {scenario_id: normalized_score (0-1)}}
            generation: current generation number
        """
        self.agent_revenues = {}

        for agent_id, scenario_scores in results.items():
            total_revenue = 0.0
            for scenario_id, score in scenario_scores.items():
                # Update client memory
                if scenario_id not in self.client_memories:
                    self.client_memories[scenario_id] = ClientMemory(scenario_id=scenario_id)
                self.client_memories[scenario_id].record(
                    agent_id, score, self.config.client_memory_depth
                )
                total_revenue += score

            self.agent_revenues[agent_id] = total_revenue

        self.revenue_history.append(dict(self.agent_revenues))

    def select_survivors(self, agent_ids: list[int], elite_ids: list[int] = []) -> list[int]:
        """Kill agents below survival threshold. Elites are always protected.
        
        Returns: list of surviving agent IDs.
        """
        if not self.agent_revenues:
            return agent_ids  # No data yet

        revenues = [(aid, self.agent_revenues.get(aid, 0.0)) for aid in agent_ids]
        revenues.sort(key=lambda x: x[1])

        # Bottom X% die (unless elite)
        kill_count = max(1, int(len(agent_ids) * self.config.survival_threshold))
        killed = set()
        for aid, rev in revenues:
            if len(killed) >= kill_count:
                break
            if aid not in elite_ids:
                killed.add(aid)

        survivors = [aid for aid in agent_ids if aid not in killed]

        # Prune dead agents from client memories
        alive_set = set(survivors)
        for memory in self.client_memories.values():
            memory.prune_dead_agents(alive_set)

        return survivors

    def select_parents(
        self,
        survivor_ids: list[int],
        n_offspring: int,
    ) -> list[int]:
        """Select parents for reproduction, proportional to revenue.
        
        Returns: list of parent IDs (length = n_offspring).
        """
        if not survivor_ids:
            return []

        revenues = {aid: max(self.agent_revenues.get(aid, 0.0), 0.001) for aid in survivor_ids}
        total = sum(revenues.values())
        weights = [revenues[aid] / total for aid in survivor_ids]

        parents = random.choices(survivor_ids, weights=weights, k=n_offspring)
        return parents

    def get_market_stats(self) -> dict:
        """Compute market dynamics statistics."""
        if not self.agent_revenues:
            return {}

        revenues = list(self.agent_revenues.values())
        n = len(revenues)
        if n == 0:
            return {}

        total = sum(revenues)
        mean_rev = total / n
        max_rev = max(revenues)
        min_rev = min(revenues)

        # Gini coefficient
        sorted_rev = sorted(revenues)
        cumulative = 0.0
        gini_sum = 0.0
        for i, r in enumerate(sorted_rev):
            cumulative += r
            gini_sum += (2 * (i + 1) - n - 1) * r
        gini = gini_sum / (n * total) if total > 0 else 0.0

        # HHI (Herfindahl-Hirschman Index) — market concentration
        shares = [r / total for r in revenues] if total > 0 else [1.0 / n] * n
        hhi = sum(s ** 2 for s in shares)

        return {
            "mean_revenue": round(mean_rev, 4),
            "max_revenue": round(max_rev, 4),
            "min_revenue": round(min_rev, 4),
            "gini_coefficient": round(gini, 4),
            "hhi": round(hhi, 4),
            "revenue_distribution": {aid: round(r, 4) for aid, r in self.agent_revenues.items()},
        }

    def to_dict(self) -> dict:
        """Serialize market state for checkpointing."""
        return {
            "config": {
                "softmax_temperature": self.config.softmax_temperature,
                "survival_threshold": self.config.survival_threshold,
                "client_memory_depth": self.config.client_memory_depth,
                "exploration_bonus": self.config.exploration_bonus,
                "min_assignments": self.config.min_assignments,
            },
            "client_memories": {
                str(sid): {
                    "scenario_id": mem.scenario_id,
                    "agent_scores": {str(k): v for k, v in mem.agent_scores.items()},
                }
                for sid, mem in self.client_memories.items()
            },
            "revenue_history": self.revenue_history,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MarketSelectionEngine":
        """Deserialize market state from checkpoint."""
        cfg = MarketConfig(**data.get("config", {}))
        engine = cls(config=cfg)
        engine.revenue_history = data.get("revenue_history", [])

        for sid_str, mem_data in data.get("client_memories", {}).items():
            sid = int(sid_str)
            memory = ClientMemory(scenario_id=sid)
            memory.agent_scores = {
                int(k): v for k, v in mem_data.get("agent_scores", {}).items()
            }
            engine.client_memories[sid] = memory

        return engine
