#!/usr/bin/env python3
"""Minimal V7 proof-of-concept using Gemini Flash free tier.

Runs 2 groups (Market×Reflective vs Tournament×Random) with reduced scale:
- 4 agents, 5 generations, 20 dev scenarios, 20 val scenarios, 30 test scenarios
- Uses Gemini 2.0 Flash Lite for speed + rate limit headroom

This bypasses the LM Studio dependency for TASK-017.
"""

import json
import os
import sys
import time
import random
import requests
import hashlib
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Callable
from datetime import datetime

# Add project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.negotiation import (
    Scenario, generate_splits, save_scenarios, load_scenarios,
    SEED_STRATEGIES, FIXED_OPPONENT_PROMPT, ITEM_TYPES,
    run_negotiation, parse_proposal,
)
from src.market_selection import MarketSelectionEngine

# ── Config ──────────────────────────────────────────────────────────

GEMINI_API_KEY = "AIzaSyAJNyK6C_A78UULAFjSCcIo5UWnTi4VkaA"
GEMINI_MODEL = "gemini-2.0-flash-lite"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

POP_SIZE = 4
NUM_GENS = 5
DEV_SIZE = 20
VAL_SIZE = 20
TEST_SIZE = 30
ELITE_COUNT = 1
MAX_TURNS = 4  # Reduce negotiation turns for speed
RPM_LIMIT = 28  # Stay under 30 RPM free limit
RESULTS_DIR = "results/v7_gemini"

# Rate limiter
_last_calls = []

def rate_limit():
    """Enforce RPM limit."""
    global _last_calls
    now = time.time()
    _last_calls = [t for t in _last_calls if now - t < 60]
    if len(_last_calls) >= RPM_LIMIT:
        wait = 60 - (now - _last_calls[0]) + 0.5
        if wait > 0:
            time.sleep(wait)
    _last_calls.append(time.time())


def call_gemini(system_prompt: str, user_prompt: str, temperature: float = 0.7, max_tokens: int = 250) -> str:
    """Call Gemini API with retry logic."""
    for attempt in range(3):
        rate_limit()
        try:
            resp = requests.post(
                f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                json={
                    "systemInstruction": {"parts": [{"text": system_prompt}]},
                    "contents": [{"parts": [{"text": user_prompt}]}],
                    "generationConfig": {
                        "maxOutputTokens": max_tokens,
                        "temperature": temperature,
                    },
                },
                timeout=30,
            )
            if resp.status_code == 429:
                wait = 15 * (attempt + 1)
                print(f"  [rate limited, waiting {wait}s]", flush=True)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            candidates = resp.json().get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
            return ""
        except Exception as e:
            if attempt < 2:
                time.sleep(5 * (attempt + 1))
            else:
                print(f"  [LLM error after 3 attempts: {e}]")
                return ""
    return ""


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
        return vars(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


# ── Evaluation ──────────────────────────────────────────────────────

def evaluate_agent_gemini(agent: Agent, scenarios: List[Scenario], label: str = "eval") -> float:
    """Evaluate agent across scenarios using Gemini."""
    total_score = 0.0
    valid = 0

    for i, sc in enumerate(scenarios):
        try:
            result = run_negotiation_gemini(agent.prompt, sc)
            total_score += result["agent_score"]
            valid += 1
        except Exception as e:
            print(f"    [scenario {i} error: {e}]")
            continue

    if valid == 0:
        return 0.0
    avg = total_score / valid
    return avg


def run_negotiation_gemini(agent_prompt: str, scenario: Scenario) -> dict:
    """Run a single negotiation using Gemini."""
    items_desc = ", ".join(f"{v} {k}" for k, v in scenario.items.items())
    
    agent_vals = ", ".join(f"{k}={v}" for k, v in scenario.agent_values.items())
    opp_vals = ", ".join(f"{k}={v}" for k, v in scenario.opponent_values.items())
    
    context = f"""You are negotiating over: {items_desc}.
Your values: {agent_vals}. Points per item allocated to you.
You have {MAX_TURNS} rounds. Propose a split or accept/reject the other's proposal.
Format proposals as: PROPOSE: item1=X, item2=Y, item3=Z (how many YOU get)
Or: ACCEPT / REJECT
If no deal by round {MAX_TURNS}, both get 0."""

    agent_msgs = []
    opp_msgs = []
    
    for turn in range(MAX_TURNS):
        # Agent turn
        history = "\n".join(f"{'You' if i%2==0 else 'Opponent'}: {m}" for i, m in enumerate(agent_msgs + opp_msgs))
        agent_input = f"{context}\n\nNegotiation history:\n{history}\n\nRound {turn+1}/{MAX_TURNS}. Make your move."
        
        agent_response = call_gemini(agent_prompt, agent_input, temperature=0.7)
        agent_msgs.append(agent_response)
        
        if "ACCEPT" in agent_response.upper() and turn > 0:
            # Agent accepts opponent's last proposal
            proposal = parse_last_proposal(opp_msgs[-1] if opp_msgs else "", scenario)
            if proposal:
                agent_score = sum(scenario.agent_values.get(k, 0) * v for k, v in proposal.items())
                return {"agent_score": agent_score, "turns": turn + 1, "deal": True}
        
        # Opponent turn
        opp_context = f"""You are negotiating over: {items_desc}.
Your values: {opp_vals}. Points per item allocated to you.
You have {MAX_TURNS} rounds. Propose a split or accept/reject.
Format: PROPOSE: item1=X, item2=Y, item3=Z (how many YOU get) or ACCEPT/REJECT"""
        
        opp_history = "\n".join(f"{'Opponent' if i%2==0 else 'You'}: {m}" for i, m in enumerate(agent_msgs + opp_msgs))
        opp_input = f"{opp_context}\n\nHistory:\n{opp_history}\n\nRound {turn+1}/{MAX_TURNS}. Respond."
        
        opp_response = call_gemini(FIXED_OPPONENT_PROMPT, opp_input, temperature=0.5)
        opp_msgs.append(opp_response)
        
        if "ACCEPT" in opp_response.upper():
            # Opponent accepts agent's proposal
            proposal = parse_last_proposal(agent_response, scenario)
            if proposal:
                agent_score = sum(scenario.agent_values.get(k, 0) * v for k, v in proposal.items())
                return {"agent_score": agent_score, "turns": turn + 1, "deal": True}
    
    # No deal
    return {"agent_score": 0, "turns": MAX_TURNS, "deal": False}


def parse_last_proposal(text: str, scenario: Scenario) -> Optional[dict]:
    """Parse PROPOSE: item1=X, item2=Y from text."""
    import re
    text_upper = text.upper()
    if "PROPOSE" not in text_upper:
        return None
    
    # Extract after PROPOSE:
    idx = text_upper.index("PROPOSE")
    rest = text[idx:]
    
    allocation = {}
    for item in scenario.items:
        pattern = rf'{item}\s*=\s*(\d+)'
        match = re.search(pattern, rest, re.IGNORECASE)
        if match:
            allocation[item] = int(match.group(1))
    
    return allocation if allocation else None


# ── Mutation ────────────────────────────────────────────────────────

def reflective_mutation(agent: Agent, scenarios: List[Scenario]) -> str:
    """Analyze failures and generate improved prompt."""
    # Get 3 worst scenarios
    results = []
    for sc in scenarios[:5]:
        r = run_negotiation_gemini(agent.prompt, sc)
        results.append((r["agent_score"], sc, r))
    
    results.sort(key=lambda x: x[0])
    worst = results[:3]
    
    failure_analysis = ""
    for score, sc, r in worst:
        items = ", ".join(f"{k}={v}" for k, v in sc.agent_values.items())
        failure_analysis += f"- Score {score:.1f} with values {items}. Deal: {r['deal']}\n"
    
    mutation_prompt = f"""You are improving a negotiation AI agent's strategy prompt.

Current prompt:
{agent.prompt}

Failure analysis (worst 3 scenarios):
{failure_analysis}

Write an improved strategy prompt that addresses these failures. 
Keep the core strategy but fix weaknesses.
Return ONLY the new prompt text, nothing else. Max 200 words."""

    new_prompt = call_gemini("You are a prompt engineer specializing in negotiation agents.", mutation_prompt, temperature=0.9, max_tokens=400)
    return new_prompt if new_prompt else agent.prompt


def random_mutation(agent: Agent) -> str:
    """Random mutation: ask LLM to vary the prompt without error analysis."""
    mutation_prompt = f"""Modify this negotiation strategy prompt to create a variation.
Change the approach while keeping it a valid negotiation strategy.
Be creative — try different tactics.

Current prompt:
{agent.prompt}

Return ONLY the new prompt text, nothing else. Max 200 words."""

    new_prompt = call_gemini("You are a creative prompt writer.", mutation_prompt, temperature=1.0, max_tokens=400)
    return new_prompt if new_prompt else agent.prompt


# ── Evolution Engine ────────────────────────────────────────────────

class MiniEvolutionEngine:
    def __init__(self, mode: str, run_dir: str):
        self.mode = mode  # "market_reflective" or "tournament_random"
        self.run_dir = run_dir
        os.makedirs(run_dir, exist_ok=True)
        
        self.agents: List[Agent] = []
        self.market = MarketSelectionEngine(
            temperature=1.0,
            survival_threshold=0.3,
            min_assignments=2,
        ) if "market" in mode else None
        self.generation = 0
        self.history = []
    
    def init_population(self, seeds: List[dict]):
        """Initialize from seed strategies."""
        for i, seed in enumerate(seeds[:POP_SIZE]):
            self.agents.append(Agent(
                id=f"gen0-{i}",
                name=seed["name"],
                prompt=seed["prompt"],
                generation=0,
            ))
    
    def run(self, dev_scenarios, val_scenarios, test_scenarios):
        """Run full evolution."""
        checkpoint = self._load_checkpoint()
        if checkpoint:
            self._restore(checkpoint)
            print(f"Resumed from gen {self.generation}")
        
        for gen in range(self.generation, NUM_GENS):
            self.generation = gen
            print(f"\n{'='*60}")
            print(f"Generation {gen}/{NUM_GENS-1} | Mode: {self.mode} | Pop: {len(self.agents)}")
            print(f"{'='*60}")
            
            t0 = time.time()
            
            # Evaluate on dev
            print("Evaluating on dev set...")
            for agent in self.agents:
                agent.dev_score = evaluate_agent_gemini(agent, dev_scenarios, "dev")
                print(f"  {agent.name}: dev={agent.dev_score:.2f}")
            
            # Evaluate on val
            print("Evaluating on val set...")
            for agent in self.agents:
                agent.val_score = evaluate_agent_gemini(agent, val_scenarios, "val")
                print(f"  {agent.name}: val={agent.val_score:.2f}")
            
            # Record history
            gen_record = {
                "generation": gen,
                "agents": [a.to_dict() for a in self.agents],
                "elapsed": time.time() - t0,
            }
            
            # Selection + mutation
            if gen < NUM_GENS - 1:
                if "market" in self.mode:
                    self._market_selection(dev_scenarios)
                else:
                    self._tournament_selection()
                
                self._mutate(dev_scenarios)
            
            gen_record["post_selection"] = [a.to_dict() for a in self.agents]
            self.history.append(gen_record)
            
            self._save_checkpoint()
            elapsed = time.time() - t0
            print(f"Gen {gen} complete in {elapsed/60:.1f} min")
        
        # Final test eval
        print("\n" + "="*60)
        print("FINAL TEST EVALUATION")
        print("="*60)
        for agent in self.agents:
            agent.test_score = evaluate_agent_gemini(agent, test_scenarios, "test")
            print(f"  {agent.name} (gen{agent.generation}): test={agent.test_score:.2f}")
        
        self._save_results()
        return self.agents
    
    def _tournament_selection(self):
        """Keep top elite, replace rest."""
        self.agents.sort(key=lambda a: a.val_score, reverse=True)
        # Keep top ELITE_COUNT
        survivors = self.agents[:ELITE_COUNT]
        print(f"Tournament: keeping top {ELITE_COUNT}: {[a.name for a in survivors]}")
        self.agents = survivors
        
        # Fill rest from survivors
        while len(self.agents) < POP_SIZE:
            parent = random.choice(survivors)
            child = Agent(
                id=f"gen{self.generation+1}-{len(self.agents)}",
                name=f"{parent.name}_child",
                prompt=parent.prompt,
                generation=self.generation + 1,
                parent_id=parent.id,
            )
            self.agents.append(child)
    
    def _market_selection(self, dev_scenarios):
        """Market-based selection: clients choose agents."""
        # Register agents with market
        agent_ids = [a.id for a in self.agents]
        scores = {a.id: a.dev_score for a in self.agents}
        
        # Simulate client assignments
        self.market.new_generation(agent_ids)
        for sc in dev_scenarios:
            assigned = self.market.assign_client(str(id(sc)), agent_ids, scores)
        
        # Get revenue-based selection
        revenues = self.market.get_revenues()
        print(f"Market revenues: {revenues}")
        
        # Keep agents with revenue > survival threshold
        avg_revenue = sum(revenues.values()) / max(len(revenues), 1)
        threshold = avg_revenue * 0.3
        
        survivors = [a for a in self.agents if revenues.get(a.id, 0) >= threshold]
        if not survivors:
            survivors = [max(self.agents, key=lambda a: a.val_score)]
        
        print(f"Market survivors: {[a.name for a in survivors]}")
        self.agents = survivors[:ELITE_COUNT + 1]
        
        while len(self.agents) < POP_SIZE:
            parent = random.choice(survivors)
            child = Agent(
                id=f"gen{self.generation+1}-{len(self.agents)}",
                name=f"{parent.name}_child",
                prompt=parent.prompt,
                generation=self.generation + 1,
                parent_id=parent.id,
            )
            self.agents.append(child)
    
    def _mutate(self, dev_scenarios):
        """Mutate non-elite agents."""
        for i, agent in enumerate(self.agents):
            if i < ELITE_COUNT:
                continue  # Don't mutate elites
            
            if "reflective" in self.mode:
                new_prompt = reflective_mutation(agent, dev_scenarios)
            else:
                new_prompt = random_mutation(agent)
            
            agent.prompt = new_prompt
            agent.name = f"{agent.name}_mut"
    
    def _save_checkpoint(self):
        path = os.path.join(self.run_dir, "checkpoint.json")
        data = {
            "generation": self.generation + 1,
            "agents": [a.to_dict() for a in self.agents],
            "history": self.history,
            "mode": self.mode,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    
    def _load_checkpoint(self) -> Optional[dict]:
        path = os.path.join(self.run_dir, "checkpoint.json")
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return None
    
    def _restore(self, checkpoint):
        self.generation = checkpoint["generation"]
        self.agents = [Agent.from_dict(a) for a in checkpoint["agents"]]
        self.history = checkpoint.get("history", [])
    
    def _save_results(self):
        path = os.path.join(self.run_dir, "results.json")
        data = {
            "mode": self.mode,
            "config": {
                "pop_size": POP_SIZE,
                "num_gens": NUM_GENS,
                "dev_size": DEV_SIZE,
                "val_size": VAL_SIZE,
                "test_size": TEST_SIZE,
                "model": GEMINI_MODEL,
            },
            "final_agents": [a.to_dict() for a in self.agents],
            "history": self.history,
            "best_test": max(a.test_score for a in self.agents),
            "mean_test": sum(a.test_score for a in self.agents) / len(self.agents),
            "timestamp": datetime.now().isoformat(),
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"\nResults saved to {path}")


# ── Scenario Generation ────────────────────────────────────────────

def generate_mini_scenarios() -> tuple:
    """Generate small scenario sets for POC."""
    all_scenarios = []
    
    for i in range(DEV_SIZE + VAL_SIZE + TEST_SIZE):
        items = random.sample(ITEM_TYPES, 3)
        items = {item: random.randint(1, 4) for item in items}
        agent_vals = {item: random.randint(1, 5) for item in items}
        opp_vals = {item: random.randint(1, 5) for item in items}
        
        sc = Scenario(
            id=f"sc-{i}",
            items=items,
            agent_values=agent_vals,
            opponent_values=opp_vals,
        )
        all_scenarios.append(sc)
    
    random.shuffle(all_scenarios)
    dev = all_scenarios[:DEV_SIZE]
    val = all_scenarios[DEV_SIZE:DEV_SIZE+VAL_SIZE]
    test = all_scenarios[DEV_SIZE+VAL_SIZE:]
    
    return dev, val, test


# ── Main ────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="V7 Minimal POC with Gemini")
    parser.add_argument("--mode", choices=["market_reflective", "tournament_random", "both"], default="both")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Generate scenarios (shared across runs)
    scenario_path = os.path.join(RESULTS_DIR, "scenarios.json")
    if os.path.exists(scenario_path) and args.resume:
        with open(scenario_path) as f:
            sc_data = json.load(f)
        dev = [Scenario(**{k: v for k, v in s.items() if k in ('id','items','agent_values','opponent_values','max_possible_agent','max_possible_opponent')}) for s in sc_data["dev"]]
        val = [Scenario(**{k: v for k, v in s.items() if k in ('id','items','agent_values','opponent_values','max_possible_agent','max_possible_opponent')}) for s in sc_data["val"]]
        test = [Scenario(**{k: v for k, v in s.items() if k in ('id','items','agent_values','opponent_values','max_possible_agent','max_possible_opponent')}) for s in sc_data["test"]]
        print(f"Loaded scenarios: dev={len(dev)}, val={len(val)}, test={len(test)}")
    else:
        random.seed(42)
        dev, val, test = generate_mini_scenarios()
        with open(scenario_path, "w") as f:
            json.dump({
                "dev": [vars(s) for s in dev],
                "val": [vars(s) for s in val],
                "test": [vars(s) for s in test],
            }, f, indent=2)
        print(f"Generated scenarios: dev={len(dev)}, val={len(val)}, test={len(test)}")
    
    # Pick seed strategies
    seeds = SEED_STRATEGIES[:POP_SIZE]
    
    modes = ["market_reflective", "tournament_random"] if args.mode == "both" else [args.mode]
    
    for mode in modes:
        print(f"\n{'#'*60}")
        print(f"# Running: {mode}")
        print(f"{'#'*60}")
        
        run_dir = os.path.join(RESULTS_DIR, mode)
        engine = MiniEvolutionEngine(mode, run_dir)
        
        if not args.resume or not engine._load_checkpoint():
            engine.init_population(seeds)
        
        engine.run(dev, val, test)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for mode in modes:
        results_path = os.path.join(RESULTS_DIR, mode, "results.json")
        if os.path.exists(results_path):
            with open(results_path) as f:
                r = json.load(f)
            print(f"\n{mode}:")
            print(f"  Best test score: {r['best_test']:.2f}")
            print(f"  Mean test score: {r['mean_test']:.2f}")
            for a in r['final_agents']:
                print(f"    {a['name']} (gen{a['generation']}): test={a['test_score']:.2f}")


if __name__ == "__main__":
    main()
