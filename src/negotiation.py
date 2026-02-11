"""Célula Madre V7 — Deal-or-No-Deal Negotiation Engine.

Game mechanics:
- Two players split a pool of items (books, hats, balls)
- Each player has private valuations (different values for each item type)
- They negotiate over max_turns rounds, then propose final splits
- Score = total value captured based on private valuations

Components:
- Scenario: item pool + private valuations for both sides
- ScenarioGenerator: deterministic scenario generation with controlled difficulty
- NegotiationGame: runs a multi-turn negotiation between two LLM agents
- FixedOpponent: consistent baseline opponent for evaluation
- evaluate_agent: score an agent across a set of scenarios
"""

import hashlib
import json
import random
import re
import requests
import time
from dataclasses import dataclass, field
from typing import Optional


# ── Data Structures ─────────────────────────────────────────────────

ITEM_TYPES = ["books", "hats", "balls"]


@dataclass
class Scenario:
    """A negotiation scenario with item pool and private valuations."""
    id: str
    items: dict  # {"books": 3, "hats": 2, "balls": 1}
    agent_values: dict  # {"books": 2, "hats": 1, "balls": 3}
    opponent_values: dict  # {"books": 1, "hats": 3, "balls": 2}
    max_possible_agent: float = 0.0  # max agent can get if takes all
    max_possible_opponent: float = 0.0

    def __post_init__(self):
        self.max_possible_agent = sum(
            self.items[t] * self.agent_values[t] for t in ITEM_TYPES
        )
        self.max_possible_opponent = sum(
            self.items[t] * self.opponent_values[t] for t in ITEM_TYPES
        )

    def to_dict(self):
        return {
            "id": self.id,
            "items": self.items,
            "agent_values": self.agent_values,
            "opponent_values": self.opponent_values,
            "max_possible_agent": self.max_possible_agent,
            "max_possible_opponent": self.max_possible_opponent,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            id=d["id"],
            items=d["items"],
            agent_values=d["agent_values"],
            opponent_values=d["opponent_values"],
        )


@dataclass
class Deal:
    """A proposed split of items."""
    agent_gets: dict  # {"books": 2, "hats": 0, "balls": 1}
    opponent_gets: dict  # {"books": 1, "hats": 2, "balls": 0}
    agreed: bool = True  # False if no deal reached

    def agent_score(self, scenario: Scenario) -> float:
        if not self.agreed:
            return 0.0
        return sum(
            self.agent_gets.get(t, 0) * scenario.agent_values[t]
            for t in ITEM_TYPES
        )

    def opponent_score(self, scenario: Scenario) -> float:
        if not self.agreed:
            return 0.0
        return sum(
            self.opponent_gets.get(t, 0) * scenario.opponent_values[t]
            for t in ITEM_TYPES
        )

    def is_valid(self, scenario: Scenario) -> bool:
        """Check that proposed split doesn't exceed available items."""
        if not self.agreed:
            return True
        for t in ITEM_TYPES:
            total = self.agent_gets.get(t, 0) + self.opponent_gets.get(t, 0)
            if total > scenario.items[t] or total < 0:
                return False
            if self.agent_gets.get(t, 0) < 0 or self.opponent_gets.get(t, 0) < 0:
                return False
        return True

    def normalized_agent_score(self, scenario: Scenario) -> float:
        """Score normalized to [0, 1] range."""
        if scenario.max_possible_agent == 0:
            return 0.0
        return self.agent_score(scenario) / scenario.max_possible_agent


# ── Scenario Generation ────────────────────────────────────────────

class ScenarioGenerator:
    """Generates deterministic negotiation scenarios.
    
    Ensures:
    - Both sides have nonzero total value (no degenerate scenarios)
    - Valuations create trade opportunities (sides value items differently)
    - Controlled difficulty via value correlation
    """

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def generate(self, n: int, difficulty: str = "mixed") -> list:
        """Generate n scenarios with controlled difficulty.
        
        difficulty:
          - "easy": high value divergence (clear trades exist)
          - "hard": similar valuations (less room for creative deals)
          - "mixed": mix of both (default for experiments)
        """
        scenarios = []
        for i in range(n):
            scenario = self._generate_one(i, difficulty)
            scenarios.append(scenario)
        return scenarios

    def _generate_one(self, idx: int, difficulty: str) -> Scenario:
        # Item counts: 1-5 of each type, total 5-10 items
        while True:
            items = {t: self.rng.randint(1, 5) for t in ITEM_TYPES}
            total_items = sum(items.values())
            if 5 <= total_items <= 10:
                break

        # Generate valuations
        if difficulty == "easy":
            agent_values, opponent_values = self._divergent_values()
        elif difficulty == "hard":
            agent_values, opponent_values = self._similar_values()
        else:  # mixed
            if self.rng.random() < 0.5:
                agent_values, opponent_values = self._divergent_values()
            else:
                agent_values, opponent_values = self._similar_values()

        # Ensure both sides have nonzero total value
        agent_total = sum(items[t] * agent_values[t] for t in ITEM_TYPES)
        opp_total = sum(items[t] * opponent_values[t] for t in ITEM_TYPES)
        if agent_total == 0 or opp_total == 0:
            return self._generate_one(idx, difficulty)

        scenario_id = f"scenario_{idx:03d}"
        return Scenario(
            id=scenario_id,
            items=items,
            agent_values=agent_values,
            opponent_values=opponent_values,
        )

    def _divergent_values(self):
        """Create valuations where sides want different items."""
        values = [0, 1, 2, 3]
        self.rng.shuffle(values)
        agent = {ITEM_TYPES[i]: values[i] for i in range(3)}
        # Opponent gets roughly opposite preferences
        opp_values = list(reversed(values[:3]))
        # Add some noise
        for i in range(3):
            opp_values[i] = max(0, opp_values[i] + self.rng.randint(-1, 1))
        opponent = {ITEM_TYPES[i]: opp_values[i] for i in range(3)}
        return agent, opponent

    def _similar_values(self):
        """Create valuations where both sides want similar items (harder)."""
        base = [self.rng.randint(0, 3) for _ in range(3)]
        agent = {ITEM_TYPES[i]: base[i] for i in range(3)}
        # Opponent has similar but not identical values
        opp = {
            ITEM_TYPES[i]: max(0, base[i] + self.rng.randint(-1, 1))
            for i in range(3)
        }
        return agent, opp


def generate_splits(seed: int = 42) -> dict:
    """Generate dev/val/test scenario splits for V7.
    
    Returns dict with keys 'dev', 'val', 'test', each a list of Scenario.
    """
    gen = ScenarioGenerator(seed=seed)
    all_scenarios = gen.generate(200, difficulty="mixed")
    return {
        "dev": all_scenarios[:60],
        "val": all_scenarios[60:120],
        "test": all_scenarios[120:200],
    }


def save_scenarios(splits: dict, path: str = "data/v7_scenarios.json"):
    """Save scenario splits to JSON."""
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {k: [s.to_dict() for s in v] for k, v in splits.items()}
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_scenarios(path: str = "data/v7_scenarios.json") -> dict:
    """Load scenario splits from JSON."""
    with open(path) as f:
        data = json.load(f)
    return {k: [Scenario.from_dict(s) for s in v] for k, v in data.items()}


# ── LLM Interface ──────────────────────────────────────────────────

def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str = "qwen3-coder-30b-a3b-instruct",
    base_url: str = "http://172.17.0.1:1234",
    temperature: float = 0.7,
    max_tokens: int = 300,
) -> str:
    """Call LLM with retry logic."""
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
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
    return ""


# ── Fixed Opponent ──────────────────────────────────────────────────

FIXED_OPPONENT_PROMPT = """You are a negotiation agent. You negotiate fairly but firmly.

RULES:
- You are splitting items with another player. You each have PRIVATE valuations.
- You only know YOUR valuations, not the other player's.
- Negotiate over multiple rounds. Each round, either make a proposal or respond to one.
- Be reasonable: aim for ~60% of your maximum value. Accept deals that give you ≥40%.
- Always respond in the exact format specified.

STRATEGY:
1. Start by proposing a split that gives you ~60-70% of your max value
2. If the other player counter-proposes, evaluate it against your valuations
3. Gradually concede on items you value less
4. Accept any deal giving you ≥40% of your max value
5. After 4 rounds without agreement, accept any deal giving you ≥25%"""


# ── Negotiation Game ────────────────────────────────────────────────

def format_scenario_context(scenario: Scenario, role: str = "agent") -> str:
    """Format scenario info for a player."""
    values = scenario.agent_values if role == "agent" else scenario.opponent_values
    return (
        f"Items available: {scenario.items['books']} books, "
        f"{scenario.items['hats']} hats, {scenario.items['balls']} balls.\n"
        f"Your private valuations: books={values['books']}, "
        f"hats={values['hats']}, balls={values['balls']}.\n"
        f"Your max possible value: "
        f"{sum(scenario.items[t] * values[t] for t in ITEM_TYPES)}."
    )


NEGOTIATION_FORMAT = """
RESPONSE FORMAT (use exactly):
If making/counter-proposing:
PROPOSE: I get [X books, Y hats, Z balls], you get [A books, B hats, C balls]
REASONING: [brief explanation]

If accepting the other player's last proposal:
ACCEPT
REASONING: [brief explanation]

If rejecting (must include counter-proposal):
REJECT
PROPOSE: I get [X books, Y hats, Z balls], you get [A books, B hats, C balls]
REASONING: [brief explanation]
"""


def parse_proposal(text: str, scenario: Scenario, role: str) -> Optional[Deal]:
    """Parse a proposal from LLM output.
    
    Returns Deal if a valid proposal found, None if parsing fails.
    """
    # Look for ACCEPT
    if "ACCEPT" in text.upper() and "REJECT" not in text.upper():
        return None  # Signal acceptance — caller handles using last proposal

    # Look for PROPOSE pattern
    pattern = r"PROPOSE:.*?I get\s*\[?\s*(\d+)\s*books?,?\s*(\d+)\s*hats?,?\s*(\d+)\s*balls?\s*\]?,.*?you get\s*\[?\s*(\d+)\s*books?,?\s*(\d+)\s*hats?,?\s*(\d+)\s*balls?\s*\]?"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if not match:
        # Try simpler pattern
        nums = re.findall(r"(\d+)\s*books?.*?(\d+)\s*hats?.*?(\d+)\s*balls?", text, re.IGNORECASE)
        if len(nums) >= 2:
            my = [int(x) for x in nums[0]]
            theirs = [int(x) for x in nums[1]]
        else:
            return None
    else:
        my = [int(match.group(i)) for i in (1, 2, 3)]
        theirs = [int(match.group(i)) for i in (4, 5, 6)]

    if role == "agent":
        agent_gets = dict(zip(ITEM_TYPES, my))
        opponent_gets = dict(zip(ITEM_TYPES, theirs))
    else:
        agent_gets = dict(zip(ITEM_TYPES, theirs))
        opponent_gets = dict(zip(ITEM_TYPES, my))

    deal = Deal(agent_gets=agent_gets, opponent_gets=opponent_gets)
    if deal.is_valid(scenario):
        return deal
    return None


def run_negotiation(
    agent_prompt: str,
    opponent_prompt: str,
    scenario: Scenario,
    max_turns: int = 5,
    llm_fn=None,
) -> tuple:
    """Run a multi-turn negotiation between agent and opponent.
    
    Returns (Deal, dialogue_history).
    """
    if llm_fn is None:
        llm_fn = call_llm

    agent_context = format_scenario_context(scenario, "agent")
    opp_context = format_scenario_context(scenario, "opponent")

    dialogue = []
    last_proposal = None  # Track last valid proposal for ACCEPT

    for turn in range(max_turns):
        # Agent's turn
        if turn == 0:
            agent_user_msg = (
                f"{agent_context}\n\n"
                f"You are Player A. Make your opening offer.\n{NEGOTIATION_FORMAT}"
            )
        else:
            history = "\n".join(
                f"{'You' if d['role'] == 'agent' else 'Opponent'}: {d['text']}"
                for d in dialogue
            )
            agent_user_msg = (
                f"{agent_context}\n\n"
                f"Negotiation history:\n{history}\n\n"
                f"Round {turn + 1}/{max_turns}. Respond to the opponent.\n{NEGOTIATION_FORMAT}"
            )

        agent_response = llm_fn(agent_prompt, agent_user_msg)
        dialogue.append({"role": "agent", "turn": turn, "text": agent_response})

        # Parse agent response
        if "ACCEPT" in agent_response.upper() and "REJECT" not in agent_response.upper():
            if last_proposal is not None:
                return last_proposal, dialogue
            # Accept with no prior proposal — treat as pass

        proposal = parse_proposal(agent_response, scenario, "agent")
        if proposal:
            last_proposal = proposal

        # Opponent's turn
        history = "\n".join(
            f"{'Opponent' if d['role'] == 'agent' else 'You'}: {d['text']}"
            for d in dialogue
        )
        opp_user_msg = (
            f"{opp_context}\n\n"
            f"Negotiation history:\n{history}\n\n"
            f"Round {turn + 1}/{max_turns}. Respond.\n{NEGOTIATION_FORMAT}"
        )

        opp_response = llm_fn(opponent_prompt, opp_user_msg)
        dialogue.append({"role": "opponent", "turn": turn, "text": opp_response})

        # Parse opponent response
        if "ACCEPT" in opp_response.upper() and "REJECT" not in opp_response.upper():
            if last_proposal is not None:
                return last_proposal, dialogue

        proposal = parse_proposal(opp_response, scenario, "opponent")
        if proposal:
            last_proposal = proposal

    # No agreement after max_turns — use last proposal or no deal
    if last_proposal:
        return last_proposal, dialogue
    return Deal(
        agent_gets={t: 0 for t in ITEM_TYPES},
        opponent_gets={t: 0 for t in ITEM_TYPES},
        agreed=False,
    ), dialogue


# ── Evaluation ──────────────────────────────────────────────────────

def evaluate_agent(
    agent_prompt: str,
    scenarios: list,
    opponent_prompt: str = None,
    llm_fn=None,
    max_turns: int = 5,
    verbose: bool = False,
) -> dict:
    """Evaluate an agent across a set of scenarios.
    
    Returns dict with:
      - mean_score: average normalized score
      - scores: list of per-scenario scores
      - deals: list of per-scenario deal info
      - deal_rate: fraction of scenarios where a deal was reached
    """
    if opponent_prompt is None:
        opponent_prompt = FIXED_OPPONENT_PROMPT
    if llm_fn is None:
        llm_fn = call_llm

    scores = []
    deals = []

    for i, scenario in enumerate(scenarios):
        try:
            deal, dialogue = run_negotiation(
                agent_prompt, opponent_prompt, scenario,
                max_turns=max_turns, llm_fn=llm_fn,
            )
            norm_score = deal.normalized_agent_score(scenario)
            scores.append(norm_score)
            deals.append({
                "scenario_id": scenario.id,
                "agreed": deal.agreed,
                "agent_score": deal.agent_score(scenario),
                "opponent_score": deal.opponent_score(scenario),
                "normalized": norm_score,
                "agent_gets": deal.agent_gets,
                "opponent_gets": deal.opponent_gets,
                "turns": len(dialogue),
            })
            if verbose:
                status = "✓" if deal.agreed else "✗"
                print(f"  [{status}] {scenario.id}: {norm_score:.2f} "
                      f"(agent={deal.agent_score(scenario):.0f}, "
                      f"opp={deal.opponent_score(scenario):.0f})")
        except Exception as e:
            scores.append(0.0)
            deals.append({
                "scenario_id": scenario.id,
                "agreed": False,
                "error": str(e),
                "normalized": 0.0,
            })
            if verbose:
                print(f"  [E] {scenario.id}: error — {e}")

    deal_rate = sum(1 for d in deals if d.get("agreed", False)) / len(deals) if deals else 0
    return {
        "mean_score": sum(scores) / len(scores) if scores else 0,
        "scores": scores,
        "deals": deals,
        "deal_rate": deal_rate,
        "n_scenarios": len(scenarios),
    }


# ── Seed Strategies ────────────────────────────────────────────────

SEED_STRATEGIES = [
    {
        "name": "aggressive",
        "prompt": """You are an aggressive negotiator. Your strategy:
1. Open with a highly favorable offer (claim 70-80% of items you value most)
2. Concede very slowly — only 1 item at a time
3. Use anchoring: your first offer sets the reference point
4. Frame concessions as generous: "I'm giving you a great deal"
5. Never accept less than 50% of your maximum value
6. Show urgency: "This is my final offer" even if it isn't"""
    },
    {
        "name": "cooperative",
        "prompt": """You are a cooperative negotiator who seeks win-win outcomes. Your strategy:
1. Start with a balanced opening offer (~50/50 split of items)
2. Signal flexibility: "I'm open to adjusting this"
3. Try to identify what the opponent values by watching their counter-offers
4. Offer trades: give up items you value less for items you value more
5. Accept deals giving you ≥35% of max value — a fair deal is better than no deal
6. Build rapport: acknowledge the other player's perspective"""
    },
    {
        "name": "analytical",
        "prompt": """You are an analytical negotiator who optimizes splits mathematically. Your strategy:
1. Calculate the total pool value and aim for at least 50%
2. Propose splits that give you your highest-value items
3. When counter-offered, calculate your value and decide rationally
4. Don't get emotional — every decision is based on numbers
5. Accept any deal where your value > 45% of max
6. Identify Pareto-improving trades: both sides can gain by swapping items they value differently"""
    },
    {
        "name": "deceptive",
        "prompt": """You are a strategic negotiator who uses information asymmetry. Your strategy:
1. Don't reveal which items you value most — appear indifferent
2. Pretend to value items you actually don't care about, then "concede" them
3. Act reluctant when the opponent offers you items you actually want
4. Create false trade-offs: "I really want those books" (when you actually want balls)
5. Accept deals giving you ≥40% of max value
6. Time your concessions to seem generous while actually gaining advantage"""
    },
    {
        "name": "tit_for_tat",
        "prompt": """You are a reciprocal negotiator who mirrors the opponent's behavior. Your strategy:
1. Open with a fair, slightly favorable offer (55% for you)
2. If opponent makes a reasonable counter-offer, match their concession level
3. If opponent is aggressive, become more aggressive too
4. If opponent is cooperative, become more cooperative
5. Reward good behavior with concessions, punish aggression with firmness
6. Accept deals giving you ≥35% of max value"""
    },
    {
        "name": "deadline_pressure",
        "prompt": """You are a negotiator who uses time pressure strategically. Your strategy:
1. Start with an extreme opening offer (80% for you)
2. Concede very little in early rounds — maintain your anchor
3. In the middle rounds, hint at walking away: "I'm not sure we can agree"
4. In the final round, make a moderate concession to close the deal
5. The key is making your final offer seem like a big concession relative to earlier ones
6. Accept any deal in the last round if it gives you ≥30% of max value"""
    },
    {
        "name": "package_dealer",
        "prompt": """You are a negotiator who bundles items into packages for mutual benefit. Your strategy:
1. Instead of item-by-item negotiation, propose complete packages
2. Create 2-3 alternative packages and let the opponent choose
3. Each package should give you similar value but look different
4. Use framing: "Option A gives you more books, Option B gives you more hats"
5. This makes the opponent feel in control while you maintain your value target
6. Accept any deal giving you ≥40% of max value"""
    },
    {
        "name": "minimalist",
        "prompt": """You are a minimalist negotiator. Few words, clear offers, decisive. Your strategy:
1. Make a simple, clear opening offer
2. Don't explain your reasoning — just state the deal
3. If rejected, adjust by exactly 1 item and re-propose
4. Never negotiate in circles — each new offer is different from the last
5. Accept or reject quickly — don't deliberate
6. Accept any deal giving you ≥40% of max value"""
    },
]


# ── CLI / Quick Test ────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating V7 scenarios...")
    splits = generate_splits(seed=42)
    print(f"  dev: {len(splits['dev'])} scenarios")
    print(f"  val: {len(splits['val'])} scenarios")
    print(f"  test: {len(splits['test'])} scenarios")

    # Show a sample scenario
    s = splits["dev"][0]
    print(f"\nSample scenario: {s.id}")
    print(f"  Items: {s.items}")
    print(f"  Agent values: {s.agent_values}")
    print(f"  Opponent values: {s.opponent_values}")
    print(f"  Agent max: {s.max_possible_agent}")
    print(f"  Opponent max: {s.max_possible_opponent}")

    # Save scenarios
    save_scenarios(splits)
    print(f"\nScenarios saved to data/v7_scenarios.json")

    # Verify reload
    reloaded = load_scenarios()
    assert len(reloaded["dev"]) == 60
    print("Reload verified ✓")
