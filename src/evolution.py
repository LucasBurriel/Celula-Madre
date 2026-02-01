"""
Evolutionary engine module for Célula Madre MVP.
Handles agent selection, mutation, and evolution.
Supports Anthropic Claude and Google Gemini as backends.
"""

import os
from dotenv import load_dotenv
load_dotenv()

import random
from typing import List

from src.agent import SimpleAgent, PROVIDER
from src.database import AgentConfig, Database


class EvolutionaryEngine:
    """Engine for evolving agent prompts based on market performance."""

    def __init__(self, use_guided_mutation: bool = True):
        """
        Initialize evolutionary engine.

        Args:
            use_guided_mutation: If True, use LLM to evolve prompts based on performance.
                                 If False, use random mutations (control group).
        """
        self.use_guided_mutation = use_guided_mutation
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
            api_key = os.environ.get("GOOGLE_API_KEY")
            self.client = genai.Client(api_key=api_key)

    def _llm_generate(self, prompt: str) -> str:
        """Generate text using the configured LLM provider."""
        if self.provider == "local":
            response = self.client.chat.completions.create(
                model=self.local_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512
            )
            return response.content[0].text.strip()
        else:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            return response.text.strip()

    def select_parent(self, agents: List[SimpleAgent], db: Database) -> SimpleAgent:
        """
        Select parent agent using CMP (Clade-Metaproductivity) + epsilon-random.

        Strategy:
        - 80% probability: Select best agent by LINEAGE revenue (CMP)
        - 20% probability: Select random agent (exploration)

        Args:
            agents: List of available agents
            db: Database to query lineage information

        Returns:
            Selected parent agent
        """
        if random.random() < 0.8:
            lineage_scores = {
                agent: db.get_lineage_revenue(agent.config.agent_id)
                for agent in agents
            }
            return max(lineage_scores, key=lineage_scores.get)
        else:
            return random.choice(agents)

    def mutate_prompt_random(self, parent_prompt: str) -> str:
        """
        Generate random mutation of prompt (control group).

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

        mutation = random.choice(mutations)
        return mutation(parent_prompt)

    def mutate_prompt(self, parent_prompt: str, performance_data: dict) -> str:
        """
        Generate improved prompt based on parent and performance data.

        Args:
            parent_prompt: Current agent's system prompt
            performance_data: Dict with revenue, transactions, avg_price, feedback

        Returns:
            New evolved system prompt
        """
        if not self.use_guided_mutation:
            return self.mutate_prompt_random(parent_prompt)

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

        return self._llm_generate(mutation_instruction)

    def evolve_generation(self, agents: List[SimpleAgent], db: Database) -> SimpleAgent:
        """
        Create new agent variant from population.

        Args:
            agents: Current agent population
            db: Database for feedback and persistence

        Returns:
            Newly created agent
        """
        parent = self.select_parent(agents, db)

        feedback = db.get_recent_feedback(parent.config.agent_id, limit=5)

        performance_data = {
            'total_revenue': parent.config.total_revenue,
            'transaction_count': parent.config.transaction_count,
            'avg_price': parent.config.total_revenue / max(1, parent.config.transaction_count),
            'feedback_samples': '\n'.join([f"- {f}" for f in feedback]) if feedback else "- No feedback yet"
        }

        new_prompt = self.mutate_prompt(parent.config.system_prompt, performance_data)

        new_config = AgentConfig(
            agent_id=f"agent_gen{parent.config.generation + 1}_{random.randint(1000, 9999)}",
            generation=parent.config.generation + 1,
            parent_id=parent.config.agent_id,
            system_prompt=new_prompt
        )

        new_agent = SimpleAgent(new_config)
        db.save_agent(new_config)

        return new_agent
