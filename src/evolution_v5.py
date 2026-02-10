"""Célula Madre V5 — Market-Driven Prompt Evolution.

Adapts GEPA's reflective mutation for market prediction.
Agents = system prompts that define trading strategies.
Fitness = prediction accuracy on real BTC/ETH data.
"""

import json
import random
import time
import os
import requests
from dataclasses import dataclass, field
from typing import Optional

from src.market_data import MarketExample


# === LLM Interface ===

def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str = "qwen3-coder-30b-a3b-instruct",
    base_url: str = "http://172.17.0.1:1234",
    temperature: float = 0.7,
    max_tokens: int = 512,
) -> str:
    """Call LLM via OpenAI-compatible API."""
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
                timeout=30,
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except requests.exceptions.Timeout:
            print(f"  ⚠️ LLM timeout (attempt {attempt+1}/3)", flush=True)
            time.sleep(2)
        except Exception as e:
            return f"ERROR: {e}"
    return "ERROR: LLM timeout after 3 attempts"


# === Agent ===

@dataclass 
class Agent:
    """An agent is a system prompt + performance metrics."""
    id: int
    strategy_prompt: str
    generation: int = 0
    parents: list[int] = field(default_factory=list)
    
    # Performance
    dev_accuracy: float = 0.0
    val_accuracy: float = 0.0
    val_predictions: list[dict] = field(default_factory=list)
    val_instance_wins: set[int] = field(default_factory=set)
    
    # For reflection
    dev_trajectories: list[dict] = field(default_factory=list)


def predict(agent: Agent, example: MarketExample, llm_kwargs: dict = {}) -> dict:
    """Run agent on a single example. Returns prediction dict."""
    user_msg = (
        f"{example.context}\n\n"
        "Respond with ONLY 'UP' or 'DOWN' followed by a brief reason (max 50 words).\n"
        "Format: UP|DOWN: reason"
    )
    
    response = call_llm(
        system_prompt=agent.strategy_prompt,
        user_prompt=user_msg,
        temperature=0.3,  # Low temp for consistent predictions
        max_tokens=100,
        **llm_kwargs,
    )
    
    # Parse prediction
    response_upper = response.upper().strip()
    if response_upper.startswith("UP"):
        predicted = "UP"
    elif response_upper.startswith("DOWN"):
        predicted = "DOWN"
    else:
        # Try to find UP or DOWN anywhere
        if "UP" in response_upper and "DOWN" not in response_upper:
            predicted = "UP"
        elif "DOWN" in response_upper and "UP" not in response_upper:
            predicted = "DOWN"
        else:
            predicted = random.choice(["UP", "DOWN"])  # Fallback
    
    correct = predicted == example.direction
    
    return {
        "date": example.date,
        "predicted": predicted,
        "actual": example.direction,
        "correct": correct,
        "change_pct": example.change_pct,
        "reasoning": response[:200],
    }


def evaluate_batch(
    agent: Agent,
    examples: list[MarketExample],
    llm_kwargs: dict = {},
    capture_trajectories: bool = False,
) -> tuple[float, list[dict]]:
    """Evaluate agent on batch. Returns (accuracy, predictions)."""
    predictions = []
    correct = 0
    
    for i, ex in enumerate(examples):
        pred = predict(agent, ex, llm_kwargs)
        predictions.append(pred)
        if pred["correct"]:
            correct += 1
        if (i + 1) % 5 == 0:
            print(f"    Agent {agent.id}: {i+1}/{len(examples)} examples ({correct}/{i+1} correct)", flush=True)
    
    accuracy = correct / len(examples) if examples else 0.0
    return accuracy, predictions


# === Seed Strategies ===

SEED_STRATEGIES = [
    # Trend follower
    """You are a trend-following BTC trading analyst.
Your strategy: Follow the prevailing trend. If BTC has been going up over the last 7-14 days, predict UP. If down, predict DOWN.
Key indicators: Look at the last 7 and 14 day trends. Momentum matters more than single-day moves.
Risk rule: If volatility is extremely high (>5% daily swings), be cautious and favor the longer-term trend.""",

    # Mean reversion
    """You are a mean-reversion BTC trading analyst.
Your strategy: Prices tend to revert to the mean. After big moves up, predict DOWN. After big drops, predict UP.
Key indicators: Compare current price to the 30-day average. If >5% above average, predict DOWN. If >5% below, predict UP.
Risk rule: Don't fight strong trends — only apply mean reversion after 3+ days of strong movement.""",

    # Volatility-based
    """You are a volatility-focused BTC trading analyst.
Your strategy: High volatility periods tend to continue in the same direction for 1-2 days, then reverse. Low volatility leads to breakouts.
Key indicators: Calculate recent daily ranges. After 3+ days of low volatility (<1% daily), predict a breakout in the direction of the last small move. After high volatility days, predict continuation for 1 day then reversal.
Risk rule: In extremely volatile markets (>8% moves), reduce confidence and favor the dominant trend.""",

    # Pattern recognition
    """You are a pattern-recognition BTC trading analyst.
Your strategy: Look for specific patterns in recent price action:
- Three consecutive up days → likely pullback (DOWN)
- Three consecutive down days → likely bounce (UP)  
- V-shaped recovery (big drop then recovery) → continuation UP
- Inverted V (big rise then drop) → continuation DOWN
Key indicators: Focus on the last 5-7 days of price action for patterns.
Risk rule: Patterns are weaker during strong trends — defer to the 14-day trend if it's clear.""",
]


# === Reflective Mutation (from GEPA) ===

REFLECTION_PROMPT = """I have a BTC trading strategy that makes predictions. Here's the current strategy:

```
{strategy}
```

Here are its recent predictions with results:

{predictions_summary}

**Accuracy: {accuracy:.0%}** ({correct}/{total} correct)

Analysis of failures:
{failure_analysis}

Your task: Write an IMPROVED version of this trading strategy. 
- Keep what works (patterns where it was correct)
- Fix what doesn't work (patterns where it failed)
- Be specific about indicators and thresholds
- The strategy should be a system prompt for an AI analyst

Return ONLY the new strategy text, nothing else."""


def analyze_failures(predictions: list[dict]) -> str:
    """Analyze prediction failures for reflection."""
    failures = [p for p in predictions if not p["correct"]]
    if not failures:
        return "No failures — strategy performed perfectly."
    
    lines = []
    
    # Categorize failures
    false_ups = [p for p in failures if p["predicted"] == "UP"]
    false_downs = [p for p in failures if p["predicted"] == "DOWN"]
    
    lines.append(f"Total failures: {len(failures)}")
    lines.append(f"  False UP (predicted UP, was DOWN): {len(false_ups)}")
    lines.append(f"  False DOWN (predicted DOWN, was UP): {len(false_downs)}")
    
    # Big misses (wrong on large moves)
    big_misses = [p for p in failures if abs(p["change_pct"]) > 3]
    if big_misses:
        lines.append(f"\nBig misses (>3% moves called wrong):")
        for p in big_misses[:5]:
            lines.append(f"  {p['date']}: predicted {p['predicted']}, actual {p['actual']} ({p['change_pct']:+.1f}%)")
    
    return "\n".join(lines)


def format_predictions_summary(predictions: list[dict]) -> str:
    """Format predictions for reflection prompt."""
    lines = []
    for p in predictions:
        status = "✓" if p["correct"] else "✗"
        lines.append(
            f"{status} {p['date']}: predicted {p['predicted']}, "
            f"actual {p['actual']} ({p['change_pct']:+.1f}%) — {p['reasoning'][:80]}"
        )
    return "\n".join(lines)


def reflect_and_mutate(
    agent: Agent,
    dev_predictions: list[dict],
    dev_accuracy: float,
    llm_kwargs: dict = {},
) -> str:
    """Generate improved strategy via reflection on failures."""
    prompt = REFLECTION_PROMPT.format(
        strategy=agent.strategy_prompt,
        predictions_summary=format_predictions_summary(dev_predictions),
        accuracy=dev_accuracy,
        correct=sum(1 for p in dev_predictions if p["correct"]),
        total=len(dev_predictions),
        failure_analysis=analyze_failures(dev_predictions),
    )
    
    new_strategy = call_llm(
        system_prompt="You are an expert trading strategy designer. Improve the given strategy based on its performance data.",
        user_prompt=prompt,
        temperature=0.8,  # Higher temp for creative mutations
        max_tokens=800,
        **llm_kwargs,
    )
    
    # Basic validation - should be a reasonable strategy prompt
    if len(new_strategy) < 50 or "ERROR" in new_strategy:
        return agent.strategy_prompt  # Keep original if reflection fails
    
    return new_strategy


# === Structural Merge ===

MERGE_PROMPT = """I have two BTC trading strategies that excel at different things:

**Strategy A** (good at: {a_strengths}):
```
{strategy_a}
```

**Strategy B** (good at: {b_strengths}):
```
{strategy_b}
```

Create a MERGED strategy that combines the best elements of both.
The merged strategy should handle both scenarios well.
Return ONLY the new strategy text, nothing else."""


def merge_strategies(
    agent_a: Agent,
    agent_b: Agent,
    llm_kwargs: dict = {},
) -> str:
    """Merge two complementary strategies."""
    # Determine strengths based on instance wins
    a_wins = len(agent_a.val_instance_wins)
    b_wins = len(agent_b.val_instance_wins)
    
    prompt = MERGE_PROMPT.format(
        strategy_a=agent_a.strategy_prompt,
        strategy_b=agent_b.strategy_prompt,
        a_strengths=f"{a_wins} unique correct predictions",
        b_strengths=f"{b_wins} unique correct predictions",
    )
    
    merged = call_llm(
        system_prompt="You are an expert trading strategy designer. Merge two strategies into one superior strategy.",
        user_prompt=prompt,
        temperature=0.7,
        max_tokens=800,
        **llm_kwargs,
    )
    
    if len(merged) < 50 or "ERROR" in merged:
        return agent_a.strategy_prompt
    
    return merged


# === Evolution Engine ===

@dataclass
class EvolutionConfig:
    population_size: int = 8
    max_generations: int = 10
    mutation_rate: float = 0.5
    dev_batch_size: int = 30  # Days to evaluate on dev
    val_batch_size: int = 0  # 0 = use all val examples
    enable_merge: bool = True
    max_merges_per_gen: int = 2
    elitism_count: int = 2  # Top N survive unchanged
    fresh_injection: int = 2  # New random agents per gen
    llm_kwargs: dict = field(default_factory=dict)
    eval_model: str = ""  # If set, use this model for predictions (faster); mutation uses default model
    mutation_model: str = ""  # If set, use this model for mutation/merge (smarter)


class EvolutionEngine:
    """Main evolution loop for V5."""
    
    def __init__(self, config: EvolutionConfig):
        self.config = config
        self.agent_counter = 0
        self.generation = 0
        self.pareto_frontier: list[Agent] = []
        self.best_per_instance: dict[int, Agent] = {}
        self.history: list[dict] = []  # Log of every generation
        self.checkpoint_dir = None
    
    def save_checkpoint(self, population: list[Agent], best_agent: Agent, best_val_accuracy: float, gen: int):
        """Save checkpoint after each generation."""
        if not self.checkpoint_dir:
            return
        
        checkpoint = {
            "generation": gen,
            "agent_counter": self.agent_counter,
            "best_val_accuracy": best_val_accuracy,
            "best_agent_id": best_agent.id,
            "history": self.history,
            "population": [
                {
                    "id": a.id,
                    "strategy_prompt": a.strategy_prompt,
                    "generation": a.generation,
                    "parents": a.parents,
                    "dev_accuracy": a.dev_accuracy,
                    "val_accuracy": a.val_accuracy,
                    "val_instance_wins": list(a.val_instance_wins),
                }
                for a in population
            ],
            "pareto_frontier": [
                {
                    "id": a.id,
                    "strategy_prompt": a.strategy_prompt,
                    "generation": a.generation,
                    "parents": a.parents,
                    "dev_accuracy": a.dev_accuracy,
                    "val_accuracy": a.val_accuracy,
                    "val_instance_wins": list(a.val_instance_wins),
                }
                for a in self.pareto_frontier
            ],
        }
        
        filepath = os.path.join(self.checkpoint_dir, f"checkpoint_gen{gen}.json")
        latest = os.path.join(self.checkpoint_dir, "checkpoint_latest.json")
        
        with open(filepath, "w") as f:
            json.dump(checkpoint, f, indent=2, ensure_ascii=False)
        with open(latest, "w") as f:
            json.dump(checkpoint, f, indent=2, ensure_ascii=False)
        
        print(f"  💾 Checkpoint saved: {filepath}")
    
    @staticmethod
    def load_checkpoint(filepath: str) -> dict:
        """Load checkpoint from file."""
        with open(filepath) as f:
            return json.load(f)
    
    def restore_from_checkpoint(self, checkpoint: dict) -> list[Agent]:
        """Restore engine state from checkpoint. Returns population."""
        self.agent_counter = checkpoint["agent_counter"]
        self.history = checkpoint["history"]
        
        def _dict_to_agent(d: dict) -> Agent:
            a = Agent(
                id=d["id"],
                strategy_prompt=d["strategy_prompt"],
                generation=d["generation"],
                parents=d.get("parents", []),
            )
            a.dev_accuracy = d.get("dev_accuracy", 0.0)
            a.val_accuracy = d.get("val_accuracy", 0.0)
            a.val_instance_wins = set(d.get("val_instance_wins", []))
            return a
        
        population = [_dict_to_agent(d) for d in checkpoint["population"]]
        self.pareto_frontier = [_dict_to_agent(d) for d in checkpoint.get("pareto_frontier", [])]
        
        # Rebuild best_per_instance from pareto frontier
        self.best_per_instance = {}
        for agent in self.pareto_frontier:
            for idx in agent.val_instance_wins:
                self.best_per_instance[idx] = agent
        
        return population
    
    def _new_agent(self, strategy: str, parents: list[int] = []) -> Agent:
        agent = Agent(
            id=self.agent_counter,
            strategy_prompt=strategy,
            generation=self.generation,
            parents=parents,
        )
        self.agent_counter += 1
        return agent
    
    def _update_pareto(self, agent: Agent, val_predictions: list[dict]):
        """Update instance-level Pareto frontier."""
        agent.val_instance_wins = set()
        
        for idx, pred in enumerate(val_predictions):
            if not pred["correct"]:
                continue
            
            current_best = self.best_per_instance.get(idx)
            if current_best is None:
                self.best_per_instance[idx] = agent
                agent.val_instance_wins.add(idx)
            else:
                # Both correct — keep the one with more total wins
                if len(agent.val_instance_wins) >= len(current_best.val_instance_wins):
                    current_best.val_instance_wins.discard(idx)
                    self.best_per_instance[idx] = agent
                    agent.val_instance_wins.add(idx)
        
        # Rebuild frontier
        frontier_set = {a.id: a for a in self.best_per_instance.values() if a.val_instance_wins}
        if agent.val_instance_wins:
            frontier_set[agent.id] = agent
        
        self.pareto_frontier = sorted(
            frontier_set.values(),
            key=lambda a: len(a.val_instance_wins),
            reverse=True,
        )
    
    def _weighted_choice(self, agents: list[Agent]) -> Agent:
        weights = [max(1, len(a.val_instance_wins)) for a in agents]
        return random.choices(agents, weights=weights)[0]
    
    def run(
        self,
        train_examples: list[MarketExample],
        val_examples: list[MarketExample],
        test_examples: list[MarketExample],
        seed_strategies: list[str] = SEED_STRATEGIES,
        log_callback=None,
        checkpoint_dir: str = None,
        resume_checkpoint: dict = None,
    ) -> Agent:
        """Run the full evolution."""
        cfg = self.config
        self.checkpoint_dir = checkpoint_dir
        
        # Ensure checkpoint dir exists
        if checkpoint_dir:
            os.makedirs(checkpoint_dir, exist_ok=True)
        
        start_gen = 0
        
        if resume_checkpoint:
            # Resume from checkpoint
            population = self.restore_from_checkpoint(resume_checkpoint)
            start_gen = resume_checkpoint["generation"] + 1
            best_val_accuracy = resume_checkpoint["best_val_accuracy"]
            # Find best agent in population
            best_id = resume_checkpoint["best_agent_id"]
            best_agent = next((a for a in population if a.id == best_id), population[0])
            print(f"  ⏩ Resuming from generation {start_gen} (best_val={best_val_accuracy:.0%})")
            if log_callback:
                log_callback(f"Resumed from checkpoint gen {start_gen-1} (best_val={best_val_accuracy:.0%})")
        else:
            # Initialize population with seed strategies
            population = []
            for strategy in seed_strategies[:cfg.population_size]:
                population.append(self._new_agent(strategy))
            
            # Fill remaining with variations
            while len(population) < cfg.population_size:
                base = random.choice(seed_strategies)
                population.append(self._new_agent(base))
            
            best_val_accuracy = 0.0
            best_agent = population[0]
        
        # Build separate kwargs for eval vs mutation
        eval_kwargs = dict(cfg.llm_kwargs)
        mutation_kwargs = dict(cfg.llm_kwargs)
        if cfg.eval_model:
            eval_kwargs["model"] = cfg.eval_model
        if cfg.mutation_model:
            mutation_kwargs["model"] = cfg.mutation_model
        
        for gen in range(start_gen, cfg.max_generations):
            self.generation = gen
            gen_start = time.time()
            
            msg = f"\n{'='*60}\nGeneration {gen}/{cfg.max_generations}\n{'='*60}"
            print(msg)
            if log_callback:
                log_callback(msg)
            
            # === Phase 1: Evaluate all agents ===
            for agent in population:
                # Dev evaluation (for reflection)
                dev_batch = random.sample(train_examples, min(cfg.dev_batch_size, len(train_examples)))
                agent.dev_accuracy, dev_preds = evaluate_batch(
                    agent, dev_batch, eval_kwargs, capture_trajectories=True
                )
                agent.dev_trajectories = dev_preds
                
                # Val evaluation (for selection)
                val_batch = val_examples
                if cfg.val_batch_size > 0:
                    val_batch = random.sample(val_examples, min(cfg.val_batch_size, len(val_examples)))
                agent.val_accuracy, val_preds = evaluate_batch(
                    agent, val_batch, eval_kwargs
                )
                agent.val_predictions = val_preds
                self._update_pareto(agent, val_preds)
                
                status = (
                    f"  Agent {agent.id} (gen{agent.generation}): "
                    f"dev={agent.dev_accuracy:.0%} val={agent.val_accuracy:.0%} "
                    f"wins={len(agent.val_instance_wins)}"
                )
                print(status)
                if log_callback:
                    log_callback(status)
            
            # Track best
            for agent in population:
                if agent.val_accuracy > best_val_accuracy:
                    best_val_accuracy = agent.val_accuracy
                    best_agent = agent
            
            # Log generation
            gen_info = {
                "generation": gen,
                "agents": [
                    {
                        "id": a.id,
                        "gen": a.generation,
                        "dev_acc": round(a.dev_accuracy, 3),
                        "val_acc": round(a.val_accuracy, 3),
                        "wins": len(a.val_instance_wins),
                        "parents": a.parents,
                    }
                    for a in population
                ],
                "best_val": round(best_val_accuracy, 3),
                "frontier_size": len(self.pareto_frontier),
                "duration_sec": round(time.time() - gen_start, 1),
            }
            self.history.append(gen_info)
            
            summary = (
                f"  Gen {gen} summary: best_val={best_val_accuracy:.0%}, "
                f"frontier={len(self.pareto_frontier)}, "
                f"time={gen_info['duration_sec']}s"
            )
            print(summary)
            if log_callback:
                log_callback(summary)
            
            # Save checkpoint after evaluation
            self.save_checkpoint(population, best_agent, best_val_accuracy, gen)
            
            # === Phase 2: Generate next generation ===
            if gen >= cfg.max_generations - 1:
                break
            
            new_population = []
            
            # Sort by val accuracy for elitism
            ranked = sorted(population, key=lambda a: a.val_accuracy, reverse=True)
            
            # (1) Elitism: top 2 survive unchanged
            elite = ranked[:cfg.elitism_count]
            for a in elite:
                new_population.append(a)
                print(f"  👑 Elite preserved: Agent {a.id} (val={a.val_accuracy:.0%})")
            
            # (2) Reflective mutation: mutate from Pareto frontier or top agents
            mutation_slots = cfg.population_size - cfg.elitism_count - cfg.fresh_injection
            mutation_pool = self.pareto_frontier if self.pareto_frontier else ranked
            
            for _ in range(mutation_slots):
                parent = self._weighted_choice(mutation_pool)
                
                new_strategy = reflect_and_mutate(
                    parent,
                    parent.dev_trajectories,
                    parent.dev_accuracy,
                    mutation_kwargs,
                )
                
                child = self._new_agent(new_strategy, parents=[parent.id])
                
                # Gate: evaluate child on dev batch
                dev_batch = random.sample(train_examples, min(cfg.dev_batch_size, len(train_examples)))
                child.dev_accuracy, _ = evaluate_batch(child, dev_batch, eval_kwargs)
                
                # Accept if not worse than parent
                if child.dev_accuracy >= parent.dev_accuracy:
                    new_population.append(child)
                    print(f"  ✓ Mutation accepted: {parent.id} ({parent.dev_accuracy:.0%}) → {child.id} ({child.dev_accuracy:.0%})")
                else:
                    print(f"  ✗ Mutation rejected: {parent.id} ({parent.dev_accuracy:.0%}) → {child.id} ({child.dev_accuracy:.0%})")
                    new_population.append(parent)  # Keep parent
            
            # (3) Fresh injection: new random agents for diversity
            for _ in range(cfg.fresh_injection):
                fresh_strategy = random.choice(seed_strategies)
                fresh = self._new_agent(fresh_strategy)
                new_population.append(fresh)
                print(f"  🌱 Fresh agent injected: Agent {fresh.id}")
            
            # Structural merge (replaces worst if successful)
            if cfg.enable_merge and len(self.pareto_frontier) >= 2:
                for _ in range(cfg.max_merges_per_gen):
                    if len(self.pareto_frontier) < 2:
                        break
                    
                    a, b = random.sample(self.pareto_frontier[:4], 2)
                    merged_strategy = merge_strategies(a, b, mutation_kwargs)
                    merged = self._new_agent(merged_strategy, parents=[a.id, b.id])
                    
                    # Gate on val
                    merged.val_accuracy, val_preds = evaluate_batch(
                        merged, val_examples, eval_kwargs
                    )
                    
                    parent_avg = (a.val_accuracy + b.val_accuracy) / 2
                    if merged.val_accuracy >= parent_avg * 0.95:
                        self._update_pareto(merged, val_preds)
                        # Replace worst non-elite agent
                        worst_idx = min(
                            range(cfg.elitism_count, len(new_population)),
                            key=lambda i: new_population[i].dev_accuracy,
                        )
                        replaced = new_population[worst_idx]
                        new_population[worst_idx] = merged
                        print(f"  ⚡ Merge accepted: {a.id}+{b.id} → {merged.id} (val={merged.val_accuracy:.0%}), replaced Agent {replaced.id}")
                    else:
                        print(f"  ✗ Merge rejected: {a.id}+{b.id} → {merged.id} (val={merged.val_accuracy:.0%} < {parent_avg*0.95:.0%})")
            
            population = new_population[:cfg.population_size]
        
        # === Final: Test best agent ===
        print(f"\n{'='*60}\nFinal Test\n{'='*60}")
        test_accuracy, test_preds = evaluate_batch(best_agent, test_examples, eval_kwargs)
        print(f"Best agent {best_agent.id} (gen{best_agent.generation}):")
        print(f"  Val accuracy: {best_val_accuracy:.0%}")
        print(f"  Test accuracy: {test_accuracy:.0%}")
        print(f"  Strategy:\n{best_agent.strategy_prompt[:500]}")
        
        return best_agent
    
    def save_results(self, filepath: str, best_agent: Agent, test_accuracy: float):
        """Save evolution results to JSON."""
        results = {
            "best_agent": {
                "id": best_agent.id,
                "generation": best_agent.generation,
                "strategy": best_agent.strategy_prompt,
                "val_accuracy": round(best_agent.val_accuracy, 3),
                "test_accuracy": round(test_accuracy, 3),
            },
            "config": {
                "population_size": self.config.population_size,
                "max_generations": self.config.max_generations,
                "mutation_rate": self.config.mutation_rate,
            },
            "history": self.history,
            "pareto_frontier": [
                {
                    "id": a.id,
                    "generation": a.generation,
                    "val_accuracy": round(a.val_accuracy, 3),
                    "wins": len(a.val_instance_wins),
                    "strategy_preview": a.strategy_prompt[:200],
                }
                for a in self.pareto_frontier
            ],
        }
        
        with open(filepath, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Results saved to {filepath}")
