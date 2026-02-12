"""Célula Madre V6 — Proving Evolution Works via AG News Classification.

Three-group experiment:
  - Experimental: reflective mutation (GEPA-style error analysis)
  - Control-Random: random mutation (no error info)
  - Control-Static: no mutation (seeds only, selection still applies)

Reuses V5 LLM interface. Task: 4-class AG News classification.
"""

import json
import os
import random
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from src.ag_news_data import LABELS, evaluate_agent, load_splits

# ── LLM Interface (reuse from V5) ──────────────────────────────────

import requests


def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str = "qwen3-coder-30b-a3b-instruct",
    base_url: str = "http://172.17.0.1:1234",
    temperature: float = 0.7,
    max_tokens: int = 512,
) -> str:
    for attempt in range(3):
        try:
            r = requests.post(
                f"{base_url}/v1/chat/completions",
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "no_think": True,
                },
                timeout=60,
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except requests.exceptions.Timeout:
            print(f"  ⚠️ LLM timeout (attempt {attempt+1}/3)", flush=True)
            time.sleep(3)
        except Exception as e:
            return f"ERROR: {e}"
    return "ERROR: LLM timeout after 3 attempts"


# ── Agent ───────────────────────────────────────────────────────────

@dataclass
class Agent:
    id: int
    strategy_prompt: str
    generation: int = 0
    parents: list[int] = field(default_factory=list)
    dev_accuracy: float = 0.0
    val_accuracy: float = 0.0
    dev_errors: list = field(default_factory=list)
    per_class: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "strategy_prompt": self.strategy_prompt,
            "generation": self.generation,
            "parents": self.parents,
            "dev_accuracy": self.dev_accuracy,
            "val_accuracy": self.val_accuracy,
        }

    @staticmethod
    def from_dict(d: dict) -> "Agent":
        a = Agent(
            id=d["id"],
            strategy_prompt=d["strategy_prompt"],
            generation=d.get("generation", 0),
            parents=d.get("parents", []),
        )
        a.dev_accuracy = d.get("dev_accuracy", 0.0)
        a.val_accuracy = d.get("val_accuracy", 0.0)
        return a


# ── Seed Strategies ─────────────────────────────────────────────────

SEED_STRATEGIES = [
    # 1. Vanilla
    """You are a news article classifier. Classify each article into exactly one of these four categories: World, Sports, Business, Sci/Tech.
Read the article carefully and respond with ONLY the category name.""",

    # 2. Chain-of-thought
    """You are a news classifier. For each article:
1. Read the full text
2. Identify the main subject and domain
3. Determine which category fits best: World, Sports, Business, or Sci/Tech
Respond with ONLY the category name, nothing else.""",

    # 3. Keyword-oriented
    """You are a news classifier. Use keyword signals to classify articles:
- World: countries, diplomacy, politics, international events, government, war, elections
- Sports: teams, players, scores, games, tournaments, championships, athletes
- Business: companies, stocks, markets, revenue, CEO, economy, trade, earnings
- Sci/Tech: software, research, internet, computers, technology, science, space, discovery
Respond with ONLY the category name.""",

    # 4. Structured reasoning
    """Classify the news article into one category.
Step 1: What is the article about? (one sentence)
Step 2: Which domain does it belong to?
Categories: World (politics/international), Sports (athletics/games), Business (economy/companies), Sci/Tech (technology/science)
Output ONLY the category name on its own line at the end.""",

    # 5. Elimination
    """You are a precise news classifier. Use elimination:
- Is it about sports, athletes, or games? → Sports
- Is it about technology, science, or computing? → Sci/Tech
- Is it about companies, markets, or economy? → Business
- Otherwise → World
Respond with ONLY: World, Sports, Business, or Sci/Tech""",

    # 6. Context-aware
    """Classify the following news article into one of four categories.
Think about the PRIMARY focus of the article, not secondary mentions.
An article mentioning a tech company's stock price is Business, not Sci/Tech.
An article about a sports league's financial deal is Business, not Sports.
Categories: World, Sports, Business, Sci/Tech
Respond with ONLY the category name.""",

    # 7. Brief direct
    """News classifier. Categories: World, Sports, Business, Sci/Tech.
Read → classify → output category name only.""",

    # 8. Example-anchored
    """You classify news articles. The four categories are:
- World: e.g., UN decisions, wars, elections, diplomacy
- Sports: e.g., NBA finals, Olympics, player transfers
- Business: e.g., stock prices, mergers, quarterly earnings
- Sci/Tech: e.g., new software, space missions, research papers
Read the article and respond with ONLY the matching category name.""",
]

# ── Mutation Functions ──────────────────────────────────────────────

REFLECTIVE_MUTATION_PROMPT = """I have a text classification prompt that categorizes news into: World, Sports, Business, Sci/Tech.

Current prompt:
```
{strategy}
```

Performance: {accuracy:.0%} accuracy ({correct}/{total})

Here are examples it got WRONG:
{error_examples}

Analyze the failure patterns. What types of articles is it misclassifying, and why?
Then write an IMPROVED version of the classification prompt that addresses these failures.

Return ONLY the new prompt text (the system instruction for the classifier), nothing else."""


RANDOM_MUTATION_PROMPT = """I have a text classification prompt that categorizes news into: World, Sports, Business, Sci/Tech.

Current prompt:
```
{strategy}
```

Write a DIFFERENT version of this prompt. Change the approach, wording, structure, or strategy.
Try to make it better at classifying news articles accurately.

Return ONLY the new prompt text, nothing else."""


def reflective_mutate(agent: Agent, llm_kwargs: dict = {}) -> str:
    """GEPA-style mutation: analyze errors, then improve."""
    error_lines = []
    for err in agent.dev_errors[:10]:
        error_lines.append(
            f"  - Text: \"{err['text'][:150]}...\"\n"
            f"    True: {err['true']}, Predicted: {err['predicted']}"
        )
    error_text = "\n".join(error_lines) if error_lines else "No errors available."

    prompt = REFLECTIVE_MUTATION_PROMPT.format(
        strategy=agent.strategy_prompt,
        accuracy=agent.dev_accuracy,
        correct=int(agent.dev_accuracy * 100),  # approx
        total=100,
        error_examples=error_text,
    )
    new_strategy = call_llm(
        system_prompt="You are an expert prompt engineer. Improve classification prompts based on error analysis.",
        user_prompt=prompt,
        temperature=0.8,
        max_tokens=600,
        **llm_kwargs,
    )
    if len(new_strategy) < 30 or "ERROR" in new_strategy:
        return agent.strategy_prompt
    return new_strategy


def random_mutate(agent: Agent, llm_kwargs: dict = {}) -> str:
    """Random mutation: no error info, just rewrite."""
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


# ── Evolution Engine V6 ────────────────────────────────────────────

@dataclass
class V6Config:
    population_size: int = 8
    max_generations: int = 10
    elitism_count: int = 2
    fresh_injection: int = 1
    gating_tolerance: float = 0.03    # Accept child if child_acc >= parent_acc - tolerance
    mutation_mode: str = "reflective"  # "reflective" | "random" | "static"
    llm_kwargs: dict = field(default_factory=dict)


class EvolutionEngineV6:
    def __init__(self, config: V6Config):
        self.config = config
        self.agent_counter = 0
        self.generation = 0
        self.history: list[dict] = []
        self.checkpoint_dir: Optional[str] = None

    def _new_agent(self, strategy: str, parents: list[int] = []) -> Agent:
        a = Agent(
            id=self.agent_counter,
            strategy_prompt=strategy,
            generation=self.generation,
            parents=parents,
        )
        self.agent_counter += 1
        return a

    def _eval_agent(self, agent: Agent, examples: list) -> dict:
        """Evaluate agent using LLM. Returns evaluate_agent result."""
        def llm_fn(sys_prompt, user_msg):
            return call_llm(
                sys_prompt, user_msg,
                temperature=0.1, max_tokens=50,
                **self.config.llm_kwargs,
            )
        return evaluate_agent(agent.strategy_prompt, examples, llm_fn)

    def save_checkpoint(self, population: list[Agent], gen: int, extra: dict = {}):
        if not self.checkpoint_dir:
            return
        cp = {
            "generation": gen,
            "agent_counter": self.agent_counter,
            "config_mode": self.config.mutation_mode,
            "history": self.history,
            "population": [a.to_dict() for a in population],
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
        return population, cp["generation"]

    def run(
        self,
        dev_examples: list,
        val_examples: list,
        test_examples: list,
        seed_strategies: list[str] = SEED_STRATEGIES,
        checkpoint_dir: str = None,
        resume_from: str = None,
    ) -> dict:
        """Run full evolution. Returns results dict."""
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
            # Init population from seeds
            population = []
            for s in seed_strategies[:cfg.population_size]:
                population.append(self._new_agent(s))
            while len(population) < cfg.population_size:
                population.append(self._new_agent(random.choice(seed_strategies)))

        best_test_acc = 0.0
        best_agent = population[0]

        for gen in range(start_gen, cfg.max_generations):
            self.generation = gen
            gen_start = time.time()
            print(f"\n{'='*50}\n[{cfg.mutation_mode.upper()}] Generation {gen}/{cfg.max_generations}\n{'='*50}")

            # ── Phase 1: Evaluate all on dev ──
            for agent in population:
                result = self._eval_agent(agent, dev_examples)
                agent.dev_accuracy = result["accuracy"]
                agent.dev_errors = result["errors"]
                agent.per_class = result["per_class"]
                print(f"  Agent {agent.id} (gen{agent.generation}): dev={agent.dev_accuracy:.1%}")

            # ── Phase 2: Validate on val set ──
            for agent in population:
                result = self._eval_agent(agent, val_examples)
                agent.val_accuracy = result["accuracy"]

            ranked = sorted(population, key=lambda a: a.val_accuracy, reverse=True)
            gen_best = ranked[0]
            print(f"  Gen {gen} best: Agent {gen_best.id} val={gen_best.val_accuracy:.1%} dev={gen_best.dev_accuracy:.1%}")

            gen_info = {
                "generation": gen,
                "mode": cfg.mutation_mode,
                "agents": [
                    {"id": a.id, "gen": a.generation, "dev": round(a.dev_accuracy, 4),
                     "val": round(a.val_accuracy, 4), "parents": a.parents}
                    for a in ranked
                ],
                "best_val": round(gen_best.val_accuracy, 4),
                "mean_val": round(sum(a.val_accuracy for a in population) / len(population), 4),
                "duration_sec": round(time.time() - gen_start, 1),
            }
            self.history.append(gen_info)

            self.save_checkpoint(population, gen)

            # ── Phase 3: Generate next gen (unless last) ──
            if gen >= cfg.max_generations - 1:
                break

            if cfg.mutation_mode == "static":
                # No mutation — keep same population, just re-evaluate next gen
                # (stochastic eval means scores may shift slightly)
                continue

            new_pop = []

            # Elitism
            elite = ranked[:cfg.elitism_count]
            for a in elite:
                new_pop.append(a)
                print(f"  👑 Elite: Agent {a.id} (val={a.val_accuracy:.1%})")

            # Mutation slots
            mutation_slots = cfg.population_size - cfg.elitism_count - cfg.fresh_injection
            for _ in range(mutation_slots):
                # Tournament selection (pick best of 3 random)
                candidates = random.sample(population, min(3, len(population)))
                parent = max(candidates, key=lambda a: a.val_accuracy)

                if cfg.mutation_mode == "reflective":
                    child_strategy = reflective_mutate(parent, cfg.llm_kwargs)
                else:  # random
                    child_strategy = random_mutate(parent, cfg.llm_kwargs)

                child = self._new_agent(child_strategy, parents=[parent.id])

                # Gating: eval child on val, must beat parent
                child_result = self._eval_agent(child, val_examples)
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

        # ── Final test ──
        print(f"\n{'='*50}\nFinal Test ({cfg.mutation_mode})\n{'='*50}")
        # Find best by val across all history
        best_agent = max(population, key=lambda a: a.val_accuracy)
        test_result = self._eval_agent(best_agent, test_examples)
        test_acc = test_result["accuracy"]
        print(f"Best Agent {best_agent.id}: val={best_agent.val_accuracy:.1%} test={test_acc:.1%}")
        print(f"Per-class: {json.dumps({k: round(v['accuracy'], 2) for k, v in test_result['per_class'].items()})}")

        results = {
            "mode": cfg.mutation_mode,
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
                "elitism_count": cfg.elitism_count,
                "mutation_mode": cfg.mutation_mode,
            },
        }
        return results
