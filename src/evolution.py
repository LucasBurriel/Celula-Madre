"""
Evolutionary engine module for Célula Madre MVP.
Handles agent selection, mutation, and evolution.
"""

from dotenv import load_dotenv
load_dotenv()

import random
from typing import List
from anthropic import Anthropic

from src.agent import SimpleAgent
from src.database import AgentConfig, Database


class EvolutionaryEngine:
    """Engine for evolving agent prompts based on market performance."""

    def __init__(self, use_guided_mutation: bool = True):
        """
        Initialize evolutionary engine with Claude client.

        Args:
            use_guided_mutation: If True, use Claude to evolve prompts based on performance.
                                 If False, use random mutations (control group).
        """
        self.client = Anthropic()
        self.use_guided_mutation = use_guided_mutation

    def select_parent(self, agents: List[SimpleAgent], db: Database) -> SimpleAgent:
        """
        Select parent agent using CMP (Clade-Metaproductivity) + epsilon-random.

        Strategy:
        - 80% probability: Select best agent by LINEAGE revenue (CMP)
        - 20% probability: Select random agent (exploration)

        CMP measures the success of an agent's entire family tree,
        not just individual performance. This identifies "good seeds"
        that produce successful descendants.

        Args:
            agents: List of available agents
            db: Database to query lineage information

        Returns:
            Selected parent agent
        """
        if random.random() < 0.8:
            # CMP: Best by lineage revenue (agent + all descendants)
            lineage_scores = {
                agent: db.get_lineage_revenue(agent.config.agent_id)
                for agent in agents
            }
            return max(lineage_scores, key=lineage_scores.get)
        else:
            # Exploration: Random
            return random.choice(agents)

    def mutate_prompt_random(self, parent_prompt: str) -> str:
        """
        Generate random mutation of prompt (control group).

        Applies simple random text transformations without using performance data.

        Args:
            parent_prompt: Current agent's system prompt

        Returns:
            Randomly mutated system prompt
        """
        mutations = [
            lambda p: p.replace("You are", "You're"),
            lambda p: p.replace("code", "programs"),
            lambda p: p + " Be concise.",
            lambda p: p + " Prioritize clarity.",
            lambda p: p.replace("Python", "Python programming"),
            lambda p: p.replace(".", ". Always").replace(". Always Always", ". Always"),
            lambda p: " ".join(p.split()[:10]) + " and write excellent code.",
        ]

        # Apply random mutation
        mutation = random.choice(mutations)
        return mutation(parent_prompt)

    def mutate_prompt(self, parent_prompt: str, performance_data: dict) -> str:
        """
        Generate improved prompt based on parent and performance data.

        Uses Claude to evolve the system prompt based on market feedback,
        or applies random mutations if in control mode.

        Args:
            parent_prompt: Current agent's system prompt
            performance_data: Dict with revenue, transactions, avg_price, feedback

        Returns:
            New evolved system prompt
        """
        # Control group: random mutations
        if not self.use_guided_mutation:
            return self.mutate_prompt_random(parent_prompt)

        # Experimental group: guided evolution
        mutation_instruction = f"""You are optimizing a coding agent's system prompt based on market feedback.

Current prompt:
{parent_prompt}

Performance data:
- Total revenue: ${performance_data['total_revenue']:.2f}
- Transactions: {performance_data['transaction_count']}
- Average price: ${performance_data['avg_price']:.2f}

Client feedback samples:
{performance_data['feedback_samples']}

Generate an IMPROVED system prompt that might increase revenue.
Consider what clients valued (brevity, documentation, tests, simplicity).

Return ONLY the new prompt, no explanation."""

        response = self.client.messages.create(
            model="claude-3-5-haiku-20241022",
            messages=[{"role": "user", "content": mutation_instruction}],
            max_tokens=512
        )

        return response.content[0].text.strip()

    def evolve_generation(self, agents: List[SimpleAgent], db: Database) -> SimpleAgent:
        """
        Create new agent variant from population.

        Process:
        1. Select parent (CMP + epsilon)
        2. Mutate parent's prompt
        3. Create new agent with evolved prompt

        Args:
            agents: Current agent population
            db: Database for feedback and persistence

        Returns:
            Newly created agent
        """
        # Select parent using CMP
        parent = self.select_parent(agents, db)

        # Get feedback from recent transactions
        feedback = db.get_recent_feedback(parent.config.agent_id, limit=5)

        # Prepare performance data
        performance_data = {
            'total_revenue': parent.config.total_revenue,
            'transaction_count': parent.config.transaction_count,
            'avg_price': parent.config.total_revenue / max(1, parent.config.transaction_count),
            'feedback_samples': '\n'.join([f"- {f}" for f in feedback]) if feedback else "- No feedback yet"
        }

        # Mutate prompt
        new_prompt = self.mutate_prompt(parent.config.system_prompt, performance_data)

        # Create new agent
        new_config = AgentConfig(
            agent_id=f"agent_gen{parent.config.generation + 1}_{random.randint(1000, 9999)}",
            generation=parent.config.generation + 1,
            parent_id=parent.config.agent_id,
            system_prompt=new_prompt
        )

        new_agent = SimpleAgent(new_config)

        # Save to DB
        db.save_agent(new_config)

        return new_agent
