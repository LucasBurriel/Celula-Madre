"""Célula Madre V8 — Market Selection on Multi-Domain Sentiment Analysis.

Tests whether market-based selection creates agent specialization across
different text domains (movies, products, restaurants, social media).

Key insight: AG News is too "flat" — one generalist wins all. Multi-domain
sentiment creates natural niches where different agents can specialize,
making market allocation genuinely valuable.

2×2 factorial: Market/Tournament × Reflective/Random (4 groups, 3 runs each).
"""

import json
import os
import random
import time
from dataclasses import dataclass, field
from typing import Optional

from src.sentiment_data import (
    DOMAINS, LABELS, SEED_STRATEGIES,
    evaluate_agent as eval_sentiment, load_splits, parse_sentiment,
)
from src.market_selection import MarketConfig, MarketSelectionEngine
from src.evolution_v6 import Agent, call_llm


# ── V8-specific mutation prompts (sentiment-aware) ──────────────────

REFLECTIVE_MUTATION_PROMPT = """I have a sentiment classification prompt that classifies text as positive or negative.
It handles 4 domains: movies (SST-2), products (Amazon), restaurants (Yelp), social media (tweets).

Current prompt:
```
{strategy}
```

Overall accuracy: {accuracy:.0%}
Per-domain accuracy:
{domain_breakdown}

Here are examples it got WRONG:
{error_examples}

Analyze the failure patterns. Which domains or text styles is it struggling with, and why?
Then write an IMPROVED version of the classification prompt that addresses these failures.

Return ONLY the new prompt text (the system instruction for the classifier), nothing else."""

RANDOM_MUTATION_PROMPT = """I have a sentiment classification prompt that classifies text as positive or negative across multiple domains (movies, products, restaurants, tweets).

Current prompt:
```
{strategy}
```

Write a DIFFERENT version of this prompt. Change the approach, wording, structure, or strategy.
Try to make it better at classifying sentiment across diverse text types.

Return ONLY the new prompt text, nothing else."""


def reflective_mutate_v8(agent: "AgentV8", llm_kwargs: dict = {}) -> str:
    """Reflective mutation with domain-aware error analysis."""
    error_lines = []
    for err in agent.dev_errors[:10]:
        error_lines.append(
            f"  - [{err.get('domain', '?')}] Text: \"{err['text'][:120]}...\"\n"
            f"    True: {err['true']}, Predicted: {err['predicted']}"
        )
    error_text = "\n".join(error_lines) if error_lines else "No errors available."

    domain_lines = []
    for d in DOMAINS:
        if d in agent.per_domain:
            acc = agent.per_domain[d].get("accuracy", 0)
            total = agent.per_domain[d].get("total", 0)
            domain_lines.append(f"  {d}: {acc:.0%} ({total} examples)")
    domain_text = "\n".join(domain_lines) if domain_lines else "No domain breakdown available."

    prompt = REFLECTIVE_MUTATION_PROMPT.format(
        strategy=agent.strategy_prompt,
        accuracy=agent.dev_accuracy,
        domain_breakdown=domain_text,
        error_examples=error_text,
    )
    new_strategy = call_llm(
        system_prompt="You are an expert prompt engineer. Improve sentiment classification prompts based on error analysis.",
        user_prompt=prompt,
        temperature=0.8,
        max_tokens=600,
        **llm_kwargs,
    )
    if len(new_strategy) < 30 or "ERROR" in new_strategy:
        return agent.strategy_prompt
    return new_strategy


def random_mutate_v8(agent: "AgentV8", llm_kwargs: dict = {}) -> str:
    """Random mutation for sentiment task."""
    prompt = RANDOM_MUTATION_PROMPT.format(strategy=agent.strategy_prompt)
    new_strategy = call_llm(
        system_prompt="You are a prompt engineer. Rewrite the given prompt with a different approach.",
        user_prompt=prompt,
        temperature=0.9,
        max_tokens=600,
        **llm_kwargs,
    )
    if len(new_strategy) < 30 or "ERROR" in new_strategy:
        return agent.strategy_prompt
    return new_strategy


# ── Agent with domain tracking ──────────────────────────────────────

@dataclass
class AgentV8(Agent):
    """Agent with per-domain accuracy tracking."""
    per_domain: dict = field(default_factory=dict)
    dev_errors: list = field(default_factory=list)

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["per_domain"] = self.per_domain
        return d

    @staticmethod
    def from_dict(d: dict) -> "AgentV8":
        a = AgentV8(
            id=d["id"],
            strategy_prompt=d["strategy_prompt"],
            generation=d.get("generation", 0),
            parents=d.get("parents", []),
        )
        a.dev_accuracy = d.get("dev_accuracy", 0.0)
        a.val_accuracy = d.get("val_accuracy", 0.0)
        a.per_domain = d.get("per_domain", {})
        return a


# ── Config ──────────────────────────────────────────────────────────

@dataclass
class V8Config:
    population_size: int = 8
    max_generations: int = 10
    elitism_count: int = 2
    fresh_injection: int = 1
    gating_tolerance: float = 0.03
    mutation_mode: str = "reflective"   # "reflective" | "random" | "static"
    selection_mode: str = "market"      # "market" | "tournament"
    market_config: MarketConfig = field(default_factory=MarketConfig)
    llm_kwargs: dict = field(default_factory=dict)


# ── Evolution Engine V8 ────────────────────────────────────────────

class EvolutionEngineV8:
    """V8: Multi-domain sentiment with market or tournament selection."""

    def __init__(self, config: V8Config):
        self.config = config
        self.agent_counter = 0
        self.generation = 0
        self.history: list[dict] = []
        self.checkpoint_dir: Optional[str] = None
        self.market = (
            MarketSelectionEngine(config.market_config)
            if config.selection_mode == "market" else None
        )

    def _new_agent(self, strategy: str, parents: list[int] = []) -> AgentV8:
        a = AgentV8(
            id=self.agent_counter,
            strategy_prompt=strategy,
            generation=self.generation,
            parents=parents,
        )
        self.agent_counter += 1
        return a

    def _make_llm_fn(self):
        """Create an llm_fn compatible with sentiment_data.evaluate_agent."""
        kwargs = self.config.llm_kwargs

        def llm_fn(sys_prompt, user_msg):
            return call_llm(
                sys_prompt, user_msg,
                temperature=0.1, max_tokens=50,
                **kwargs,
            )
        return llm_fn

    def _eval_agent(self, agent: AgentV8, examples: list) -> dict:
        """Evaluate agent on sentiment examples. Returns evaluate_agent result."""
        llm_fn = self._make_llm_fn()
        return eval_sentiment(llm_fn, agent.strategy_prompt, examples)

    def _eval_agent_on_indices(self, agent: AgentV8, all_examples: list, indices: list[int]) -> dict:
        """Evaluate agent on specific example indices."""
        subset = [all_examples[i] for i in indices]
        return self._eval_agent(agent, subset)

    def _update_agent_from_result(self, agent: AgentV8, result: dict, field_prefix: str = "dev"):
        """Update agent metrics from eval result."""
        acc = result["accuracy"]
        if field_prefix == "dev":
            agent.dev_accuracy = acc
            agent.per_domain = result.get("per_domain", {})
            # Build error list with domain info
            agent.dev_errors = []
            # sentiment_data.evaluate_agent doesn't return errors list,
            # so we need to re-derive from per_domain stats
        elif field_prefix == "val":
            agent.val_accuracy = acc

    def save_checkpoint(self, population: list[AgentV8], gen: int, extra: dict = {}):
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
        print(f"  💾 Checkpoint: {path}", flush=True)

    def load_checkpoint(self, filepath: str) -> tuple[list[AgentV8], int]:
        with open(filepath) as f:
            cp = json.load(f)
        self.agent_counter = cp["agent_counter"]
        self.history = cp["history"]
        population = [AgentV8.from_dict(d) for d in cp["population"]]
        if cp.get("market_state") and self.market:
            self.market = MarketSelectionEngine.from_dict(cp["market_state"])
        return population, cp["generation"]

    def _tournament_generation(
        self, population: list[AgentV8], dev_examples: list, val_examples: list, gen: int
    ) -> list[AgentV8]:
        """Standard tournament selection."""
        for agent in population:
            result = self._eval_agent(agent, dev_examples)
            self._update_agent_from_result(agent, result, "dev")
            pd = agent.per_domain
            dom_str = " | ".join(
                f"{d[:4]}={pd[d]['accuracy']:.0%}" for d in DOMAINS if d in pd
            )
            print(f"  Agent {agent.id} (gen{agent.generation}): dev={agent.dev_accuracy:.1%} [{dom_str}]", flush=True)

        for agent in population:
            result = self._eval_agent(agent, val_examples)
            self._update_agent_from_result(agent, result, "val")

        return sorted(population, key=lambda a: a.val_accuracy, reverse=True)

    def _market_generation(
        self, population: list[AgentV8], dev_examples: list, val_examples: list, gen: int
    ) -> list[AgentV8]:
        """Market-based selection with domain-aware client choice."""
        agent_ids = [a.id for a in population]
        agent_map = {a.id: a for a in population}
        scenario_ids = list(range(len(dev_examples)))

        # Assign scenarios to agents via market
        assignments = self.market.assign_scenarios(agent_ids, scenario_ids, gen)

        for aid in agent_ids:
            print(f"  Agent {aid}: assigned {len(assignments[aid])} dev examples", flush=True)

        # Evaluate each agent on assigned examples
        results_for_market: dict[int, dict[int, float]] = {}
        for agent in population:
            assigned = assignments[agent.id]
            if not assigned:
                agent.dev_accuracy = 0.0
                agent.per_domain = {}
                results_for_market[agent.id] = {}
                continue

            subset = [dev_examples[i] for i in assigned]
            result = self._eval_agent(agent, subset)
            self._update_agent_from_result(agent, result, "dev")

            # Per-example scores for market
            # Re-evaluate to get individual results (evaluate_agent doesn't track per-example)
            llm_fn = self._make_llm_fn()
            scenario_scores = {}
            for i, idx in enumerate(assigned):
                ex = subset[i]
                try:
                    response = llm_fn(agent.strategy_prompt,
                        f"Classify the sentiment of the following text as exactly 'positive' or 'negative'. Reply with ONLY the label.\n\nText: {ex['text']}")
                    pred = parse_sentiment(response)
                    scenario_scores[idx] = 1.0 if pred == ex["label"] else 0.0
                except Exception:
                    scenario_scores[idx] = 0.0
            results_for_market[agent.id] = scenario_scores

            pd = agent.per_domain
            dom_str = " | ".join(
                f"{d[:4]}={pd[d]['accuracy']:.0%}" for d in DOMAINS if d in pd
            )
            print(f"  Agent {agent.id} (gen{agent.generation}): dev={agent.dev_accuracy:.1%} [{dom_str}] ({len(assigned)} examples)", flush=True)

        # Record in market
        self.market.record_results(results_for_market, gen)
        stats = self.market.get_market_stats()
        print(f"  📊 Market: Gini={stats.get('gini_coefficient', 0):.3f}, HHI={stats.get('hhi', 0):.3f}", flush=True)

        # Validate ALL agents on full val set
        for agent in population:
            result = self._eval_agent(agent, val_examples)
            self._update_agent_from_result(agent, result, "val")

        return sorted(population, key=lambda a: a.val_accuracy, reverse=True)

    def run(
        self,
        dev_examples: list,
        val_examples: list,
        test_examples: list,
        seed_strategies: list[str] = None,
        checkpoint_dir: str = None,
        resume_from: str = None,
    ) -> dict:
        """Run full evolution."""
        if seed_strategies is None:
            seed_strategies = SEED_STRATEGIES

        cfg = self.config
        self.checkpoint_dir = checkpoint_dir
        if checkpoint_dir:
            os.makedirs(checkpoint_dir, exist_ok=True)

        start_gen = 0
        if resume_from and os.path.exists(resume_from):
            population, last_gen = self.load_checkpoint(resume_from)
            start_gen = last_gen + 1
            print(f"  ⏩ Resuming from gen {start_gen}", flush=True)
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
            print(f"\n{'='*50}\n[{mode_label}] Generation {gen}/{cfg.max_generations}\n{'='*50}", flush=True)

            # Evaluate + rank
            if cfg.selection_mode == "market":
                ranked = self._market_generation(population, dev_examples, val_examples, gen)
            else:
                ranked = self._tournament_generation(population, dev_examples, val_examples, gen)

            gen_best = ranked[0]
            print(f"  Gen {gen} best: Agent {gen_best.id} val={gen_best.val_accuracy:.1%}", flush=True)

            # Health check
            if gen == 0 and all(a.val_accuracy == 0.0 for a in ranked):
                print("  ❌ ABORT: All agents scored 0% on val set. LLM likely broken.", flush=True)
                raise RuntimeError("LLM health check failed: all agents scored 0% in gen 0")

            # Collect per-domain specialization info
            specialization = {}
            for a in ranked:
                if a.per_domain:
                    best_domain = max(a.per_domain.items(),
                                      key=lambda x: x[1].get("accuracy", 0))[0] if a.per_domain else "?"
                    specialization[a.id] = best_domain

            market_stats = self.market.get_market_stats() if self.market else {}
            gen_info = {
                "generation": gen,
                "selection_mode": cfg.selection_mode,
                "mutation_mode": cfg.mutation_mode,
                "agents": [
                    {"id": a.id, "gen": a.generation, "dev": round(a.dev_accuracy, 4),
                     "val": round(a.val_accuracy, 4), "parents": a.parents,
                     "per_domain": {d: round(v.get("accuracy", 0), 3)
                                    for d, v in a.per_domain.items()} if a.per_domain else {},
                     "specialization": specialization.get(a.id, "?")}
                    for a in ranked
                ],
                "best_val": round(gen_best.val_accuracy, 4),
                "mean_val": round(sum(a.val_accuracy for a in population) / len(population), 4),
                "duration_sec": round(time.time() - gen_start, 1),
                "market_stats": market_stats,
                "specialization": specialization,
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

            # Elitism
            elite = ranked[:cfg.elitism_count]
            elite_ids = [a.id for a in elite]
            for a in elite:
                new_pop.append(a)
                print(f"  👑 Elite: Agent {a.id} (val={a.val_accuracy:.1%})", flush=True)

            mutation_slots = cfg.population_size - cfg.elitism_count - cfg.fresh_injection

            if cfg.selection_mode == "market" and self.market:
                survivors = self.market.select_survivors(
                    [a.id for a in population], elite_ids=elite_ids
                )
                survivor_agents = {a.id: a for a in population if a.id in survivors}
                parent_ids = self.market.select_parents(
                    list(survivor_agents.keys()), mutation_slots
                )
                parents_for_mutation = [survivor_agents[pid] for pid in parent_ids]
            else:
                parents_for_mutation = []
                for _ in range(mutation_slots):
                    candidates = random.sample(population, min(3, len(population)))
                    parent = max(candidates, key=lambda a: a.val_accuracy)
                    parents_for_mutation.append(parent)

            for parent in parents_for_mutation:
                if cfg.mutation_mode == "reflective":
                    child_strategy = reflective_mutate_v8(parent, cfg.llm_kwargs)
                else:
                    child_strategy = random_mutate_v8(parent, cfg.llm_kwargs)

                child = self._new_agent(child_strategy, parents=[parent.id])

                # Gating
                child_result = self._eval_agent(child, val_examples)
                self._update_agent_from_result(child, child_result, "val")

                tolerance = cfg.gating_tolerance
                if child.val_accuracy >= parent.val_accuracy - tolerance:
                    new_pop.append(child)
                    delta = child.val_accuracy - parent.val_accuracy
                    marker = "✓" if delta >= 0 else "≈"
                    print(f"  {marker} Mutation: {parent.id}→{child.id} ({parent.val_accuracy:.1%}→{child.val_accuracy:.1%}, Δ={delta:+.1%})", flush=True)
                else:
                    new_pop.append(parent)
                    print(f"  ✗ Rejected: {parent.id}→{child.id} ({parent.val_accuracy:.1%}→{child.val_accuracy:.1%})", flush=True)

            # Fresh injection
            for _ in range(cfg.fresh_injection):
                fresh = self._new_agent(random.choice(seed_strategies))
                new_pop.append(fresh)
                print(f"  🌱 Fresh: Agent {fresh.id}", flush=True)

            population = new_pop[:cfg.population_size]
            # Save checkpoint AFTER mutations
            self.save_checkpoint(population, gen)

        # Final test
        print(f"\n{'='*50}\nFinal Test ({cfg.selection_mode}×{cfg.mutation_mode})\n{'='*50}", flush=True)
        best_agent = max(population, key=lambda a: a.val_accuracy)
        test_result = self._eval_agent(best_agent, test_examples)
        test_acc = test_result["accuracy"]
        test_per_domain = test_result.get("per_domain", {})

        dom_str = " | ".join(
            f"{d}={test_per_domain[d]['accuracy']:.1%}" for d in DOMAINS if d in test_per_domain
        )
        print(f"Best Agent {best_agent.id}: val={best_agent.val_accuracy:.1%} test={test_acc:.1%} [{dom_str}]", flush=True)

        return {
            "selection_mode": cfg.selection_mode,
            "mutation_mode": cfg.mutation_mode,
            "best_agent_id": best_agent.id,
            "best_agent_generation": best_agent.generation,
            "best_agent_strategy": best_agent.strategy_prompt,
            "best_val_accuracy": round(best_agent.val_accuracy, 4),
            "test_accuracy": round(test_acc, 4),
            "test_per_domain": {d: round(v["accuracy"], 3) for d, v in test_per_domain.items()},
            "history": self.history,
            "config": {
                "population_size": cfg.population_size,
                "max_generations": cfg.max_generations,
                "selection_mode": cfg.selection_mode,
                "mutation_mode": cfg.mutation_mode,
            },
        }
