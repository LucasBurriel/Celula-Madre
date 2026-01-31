"""
Marketplace module for Célula Madre MVP.
Generates requests, assigns agents, and processes transactions.
"""

import random
from typing import List
from dataclasses import dataclass

from src.agent import SimpleAgent
from src.clients import MinimalistClient, DocumenterClient, TesterClient, PragmaticClient
from src.database import Transaction, Database


@dataclass
class Request:
    """Marketplace request for code generation."""
    request_id: str
    description: str
    client: object  # One of the bot client classes


class Marketplace:
    """Simulated marketplace connecting agents with bot clients."""

    def __init__(self, agents: List[SimpleAgent], db: Database):
        """
        Initialize marketplace with agent population.

        Args:
            agents: List of SimpleAgent instances
            db: Database for client decision-making
        """
        self.agents = agents
        self.db = db
        self.clients = [
            MinimalistClient(),
            DocumenterClient(),
            TesterClient(),
            PragmaticClient()
        ]
        self.transactions = []

    def generate_request(self) -> Request:
        """
        Generate random request with random client.

        Returns:
            Request with description and assigned client
        """
        descriptions = [
            "Function to calculate factorial",
            "Class to parse CSV files",
            "Function to validate email addresses",
            "Function to merge two sorted lists",
            "Class for a simple stack data structure"
        ]

        return Request(
            request_id=f"req_{len(self.transactions)}",
            description=random.choice(descriptions),
            client=random.choice(self.clients)
        )

    def process_request(self, request: Request) -> Transaction:
        """
        Process complete request: CLIENT CHOOSES → generate → evaluate → pay.

        Args:
            request: Request to process

        Returns:
            Transaction record with all details

        Raises:
            RuntimeError: If agent fails to generate code
        """
        # CLIENT CHOICE: Client selects agent based on track record
        agent = request.client.select_agent(self.agents, self.db)

        # Generate solution (now returns cost info)
        code, tokens_used, api_cost = agent.solve_request(request.description)

        # Evaluate with client
        evaluation = request.client.evaluate(code)

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
        Remove agents that are too old or have too many transactions.

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
            # Retirement conditions
            too_many_txs = agent.config.transaction_count >= max_lifespan
            too_old = (current_generation - agent.config.generation) > max_gen_gap

            if too_many_txs or too_old:
                retired.append(agent)
                agent.config.status = "retired"
                self.db.update_agent_status(agent.config.agent_id, "retired")
            else:
                active.append(agent)

        self.agents = active
        return retired
