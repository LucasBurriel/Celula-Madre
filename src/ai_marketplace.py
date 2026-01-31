"""
AI Marketplace module for Célula Madre.
Marketplace where both agents (supply) and clients (demand) are AI-powered.
"""

import random
from typing import List
from dataclasses import dataclass

from src.agent import SimpleAgent
from src.ai_clients import AIClient
from src.database import Transaction, Database


@dataclass
class Request:
    """Marketplace request for code generation."""
    request_id: str
    description: str
    client: AIClient


class AIMarketplace:
    """AI-powered marketplace connecting AI agents with AI clients."""

    def __init__(self, agents: List[SimpleAgent], clients: List[AIClient], db: Database):
        """
        Initialize AI marketplace.

        Args:
            agents: List of code-generating agents
            clients: List of AI clients with preferences and budgets
            db: Database for persistence
        """
        self.agents = agents
        self.clients = clients
        self.db = db
        self.transactions = []

        # Task descriptions for clients to request
        self.task_descriptions = [
            "Function to calculate factorial",
            "Class to parse CSV files",
            "Function to validate email addresses",
            "Function to merge two sorted lists",
            "Class for a simple stack data structure",
            "Function to find prime numbers",
            "Binary search tree implementation",
            "Function to reverse a linked list",
            "Class for a simple cache with LRU eviction",
            "Function to check if string is palindrome"
        ]

    def generate_request(self) -> Request:
        """
        Generate random request from a random client.

        Returns:
            Request with description and client
        """
        client = random.choice(self.clients)
        description = random.choice(self.task_descriptions)

        return Request(
            request_id=f"req_{len(self.transactions)}",
            description=description,
            client=client
        )

    def process_request(self, request: Request) -> Transaction:
        """
        Process complete AI-driven request: AI CLIENT CHOOSES → generate → AI EVALUATES → pay.

        Args:
            request: Request to process

        Returns:
            Transaction record with all details

        Raises:
            RuntimeError: If agent fails to generate code
        """
        # AI CLIENT CHOICE: AI client selects agent based on preferences and experience
        agent = request.client.select_agent(self.agents, self.db)

        # Agent generates solution (returns code, tokens, cost)
        code, tokens_used, api_cost = agent.solve_request(request.description)

        # AI CLIENT EVALUATION: AI client evaluates quality and decides price
        evaluation = request.client.evaluate(code, agent)

        # Create transaction
        transaction = Transaction(
            request_id=request.request_id,
            agent_id=agent.config.agent_id,
            code_generated=code,
            price_paid=evaluation.price_paid,
            client_name=evaluation.client_name,
            feedback=evaluation.feedback,
            tokens_used=tokens_used,
            api_cost=api_cost
        )

        # Update agent revenue, costs, and profit
        agent.config.total_revenue += evaluation.price_paid
        agent.config.total_costs += api_cost
        agent.config.net_profit = agent.config.total_revenue - agent.config.total_costs
        agent.config.transaction_count += 1

        self.transactions.append(transaction)
        return transaction

    def retire_old_agents(self, current_generation: int, max_lifespan: int = 40, max_gen_gap: int = 3):
        """
        Remove agents based on market-driven criteria.

        Args:
            current_generation: Current max generation in population
            max_lifespan: Max transactions before retirement
            max_gen_gap: Max generations behind current

        Returns:
            List of retired agents
        """
        active = []
        retired = []

        for agent in self.agents:
            # Market-driven retirement criteria
            too_many_txs = agent.config.transaction_count >= max_lifespan
            too_old = (current_generation - agent.config.generation) > max_gen_gap

            # Could add more market-driven criteria:
            # - Bankruptcy: agent.config.net_profit < -50
            # - Market rejection: no transactions in last 20
            # - Performance collapse: recent_avg_price < 0.25 * historical_avg

            if too_many_txs or too_old:
                retired.append(agent)
                agent.config.status = "retired"
                self.db.update_agent_status(agent.config.agent_id, "retired")
            else:
                active.append(agent)

        self.agents = active
        return retired

    def get_market_stats(self) -> dict:
        """Get current market statistics."""
        total_revenue = sum(a.config.total_revenue for a in self.agents)
        total_costs = sum(a.config.total_costs for a in self.agents)
        total_profit = sum(a.config.net_profit for a in self.agents)

        # Client budget stats
        total_client_budget = sum(c.initial_budget for c in self.clients)
        total_client_spent = sum(c.spent for c in self.clients)
        total_client_remaining = sum(c.budget for c in self.clients)

        return {
            'total_transactions': len(self.transactions),
            'active_agents': len(self.agents),
            'total_revenue': total_revenue,
            'total_costs': total_costs,
            'total_profit': total_profit,
            'client_budget_initial': total_client_budget,
            'client_spent': total_client_spent,
            'client_remaining': total_client_remaining
        }
