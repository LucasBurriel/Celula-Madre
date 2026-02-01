"""
Evolution V4 — Biologically-inspired agent evolution.

Key changes:
1. Sexual reproduction (crossover): combine TWO parents
2. Niche specialization: evolve toward best client type
3. Adaptive mutation rate: conservative for winners, aggressive for losers
4. Better mutation prompts: demand creativity and diversity
5. Population cap with competitive replacement
"""

import os
import random
from typing import List, Tuple, Optional
from dotenv import load_dotenv
load_dotenv()

from src.agent import SimpleAgent, PROVIDER
from src.database import AgentConfig, Database


# Population limits
MAX_POPULATION = 8
MIN_POPULATION = 3


class EvolutionV4:
    """Biologically-inspired evolutionary engine."""

    def __init__(self):
        self.provider = PROVIDER

        if self.provider == "local":
            from openai import OpenAI
            from src.agent import LOCAL_BASE_URL, LOCAL_MODEL
            self.client = OpenAI(base_url=LOCAL_BASE_URL, api_key="lm-studio")
            self.local_model = LOCAL_MODEL
        elif self.provider == "anthropic":
            from anthropic import Anthropic
            self.client = Anthropic()
        else:
            from google import genai
            self.client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

    def _llm_generate(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate text with configurable temperature."""
        if self.provider == "local":
            response = self.client.chat.completions.create(
                model=self.local_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
                temperature=min(temperature, 1.0)
            )
            return response.content[0].text.strip()
        else:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            return response.text.strip()

    def _get_agent_niche(self, agent_id: str, db: Database) -> Optional[str]:
        """Determine which client type this agent serves best."""
        rows = db.conn.execute("""
            SELECT client_name, AVG(price_paid) as avg_price, COUNT(*) as cnt
            FROM transactions
            WHERE agent_id = ?
            GROUP BY client_name
            ORDER BY avg_price DESC
            LIMIT 1
        """, (agent_id,)).fetchone()
        
        if rows and rows['cnt'] >= 2:
            return rows['client_name']
        return None

    def _get_niche_feedback(self, agent_id: str, niche: str, db: Database) -> List[str]:
        """Get feedback specifically from this agent's best client type."""
        rows = db.conn.execute("""
            SELECT feedback, price_paid FROM transactions
            WHERE agent_id = ? AND client_name = ?
            ORDER BY created_at DESC
            LIMIT 5
        """, (agent_id, niche)).fetchall()
        return [f"${r['price_paid']:.2f} - {r['feedback']}" for r in rows]

    def select_parents(self, agents: List[SimpleAgent], db: Database) -> Tuple[SimpleAgent, SimpleAgent]:
        """
        Select TWO parents for crossover.
        
        Parent 1: Best by lineage revenue (CMP) — the "winner"
        Parent 2: Best in a DIFFERENT niche — forces diversity
        """
        if len(agents) < 2:
            return agents[0], agents[0]

        # Parent 1: CMP selection (80% best lineage, 20% random)
        if random.random() < 0.8:
            lineage_scores = {
                agent: db.get_lineage_revenue(agent.config.agent_id)
                for agent in agents
            }
            parent1 = max(lineage_scores, key=lineage_scores.get)
        else:
            parent1 = random.choice(agents)

        # Parent 2: Different niche or random (never same as parent1)
        candidates = [a for a in agents if a.config.agent_id != parent1.config.agent_id]
        if not candidates:
            return parent1, parent1

        parent1_niche = self._get_agent_niche(parent1.config.agent_id, db)
        
        # Try to find an agent in a different niche
        different_niche = []
        for a in candidates:
            a_niche = self._get_agent_niche(a.config.agent_id, db)
            if a_niche and a_niche != parent1_niche:
                different_niche.append(a)
        
        if different_niche:
            parent2 = random.choice(different_niche)
        else:
            parent2 = random.choice(candidates)

        return parent1, parent2

    def crossover_and_mutate(self, parent1: SimpleAgent, parent2: SimpleAgent,
                              db: Database) -> str:
        """
        Sexual reproduction: combine two parents' strengths + mutate.
        
        Adaptive mutation rate:
        - High-performing parents → low temperature (preserve)
        - Low-performing parents → high temperature (explore)
        """
        p1_avg = parent1.config.total_revenue / max(1, parent1.config.transaction_count)
        p2_avg = parent2.config.total_revenue / max(1, parent2.config.transaction_count)
        combined_avg = (p1_avg + p2_avg) / 2

        # Adaptive temperature: high performers → conservative, low → aggressive
        if combined_avg > 14:
            temperature = 0.5  # Conservative: preserve winning traits
            strategy = "conservative"
        elif combined_avg > 10:
            temperature = 0.8  # Moderate
            strategy = "moderate"
        else:
            temperature = 1.2  # Aggressive: big changes needed
            strategy = "aggressive"

        # Get niches
        p1_niche = self._get_agent_niche(parent1.config.agent_id, db) or "unknown"
        p2_niche = self._get_agent_niche(parent2.config.agent_id, db) or "unknown"
        
        p1_feedback = db.get_recent_feedback(parent1.config.agent_id, limit=3)
        p2_feedback = db.get_recent_feedback(parent2.config.agent_id, limit=3)

        prompt = f"""You are designing a system prompt for a Python coding agent in a competitive marketplace.

PARENT 1 (avg ${p1_avg:.2f}/tx, best with: {p1_niche}):
Prompt: {parent1.config.system_prompt}
Recent feedback: {'; '.join(p1_feedback) if p1_feedback else 'none'}

PARENT 2 (avg ${p2_avg:.2f}/tx, best with: {p2_niche}):  
Prompt: {parent2.config.system_prompt}
Recent feedback: {'; '.join(p2_feedback) if p2_feedback else 'none'}

MARKET INFO:
- MinimalistClient pays up to $18 for concise code (10-15 lines ideal)
- DocumenterClient pays up to $20 for docstrings, comments, type hints
- TesterClient pays up to $22 for test functions and assertions
- PragmaticClient pays up to $15 for simple, parseable, working code

TASK: Create a NEW system prompt that combines the BEST traits of both parents.
Strategy: {strategy} ({"small refinements, preserve what works" if strategy == "conservative" else "moderate changes, balance old and new" if strategy == "moderate" else "big creative changes, try something very different"})

RULES:
- The prompt must be DIFFERENT from both parents (not just reworded)
- Be specific about coding style, not generic ("clean code" means nothing)
- Include concrete instructions (line count targets, when to use docstrings, test patterns)
- Maximum 3 sentences. Concise = better.

Return ONLY the new system prompt, nothing else."""

        return self._llm_generate(prompt, temperature=temperature)

    def find_weakest(self, agents: List[SimpleAgent], db: Database) -> Optional[SimpleAgent]:
        """Find the weakest agent for replacement (competitive exclusion)."""
        if len(agents) <= MIN_POPULATION:
            return None
        
        scored = []
        for agent in agents:
            if agent.config.transaction_count < 3:
                continue  # Don't kill newborns
            avg_price = agent.config.total_revenue / agent.config.transaction_count
            scored.append((agent, avg_price))
        
        if not scored:
            return None
        
        scored.sort(key=lambda x: x[1])
        return scored[0][0]

    def check_starvation(self, agents: List[SimpleAgent], tx_number: int, db: Database) -> List[SimpleAgent]:
        """Kill agents that haven't been selected in too long (market voted them out)."""
        starved = []
        for agent in agents:
            if agent.config.transaction_count == 0 and tx_number > 15:
                # Never selected after 15 rounds = market doesn't want you
                starved.append(agent)
        return starved

    def evolve_generation(self, agents: List[SimpleAgent], db: Database, 
                           tx_number: int = 0) -> Optional[SimpleAgent]:
        """
        Create new agent via crossover + mutation.
        
        If population is at cap, replaces weakest agent.
        """
        active = [a for a in agents if a.config.status == "active"]
        
        # Population cap: only evolve if under limit OR can replace someone
        if len(active) >= MAX_POPULATION:
            weakest = self.find_weakest(active, db)
            if weakest:
                weakest.config.status = "retired"
                db.update_agent_status(weakest.config.agent_id, "retired")
                avg_p = weakest.config.total_revenue / max(1, weakest.config.transaction_count)
                print(f"  ⚔️  REPLACED: {weakest.config.agent_id} "
                      f"(avg ${avg_p:.2f}, weakest in population)")

        # Select two parents
        parent1, parent2 = self.select_parents(active, db)

        # Crossover + adaptive mutation
        new_prompt = self.crossover_and_mutate(parent1, parent2, db)

        # Create new agent
        new_gen = max(parent1.config.generation, parent2.config.generation) + 1
        new_config = AgentConfig(
            agent_id=f"agent_gen{new_gen}_{random.randint(1000, 9999)}",
            generation=new_gen,
            parent_id=f"{parent1.config.agent_id}+{parent2.config.agent_id}",
            system_prompt=new_prompt
        )

        new_agent = SimpleAgent(new_config)
        db.save_agent(new_config)

        return new_agent
