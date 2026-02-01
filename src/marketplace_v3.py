"""
Marketplace V3 for Célula Madre.
Improvements:
- Simulated token costs (efficiency pressure)
- Aggressive retirement (faster turnover)
- Death by losses (bankrupt agents die)
- More diverse requests
"""

import random
from typing import List
from dataclasses import dataclass

from src.agent import SimpleAgent
from src.clients_v3 import MinimalistClient, DocumenterClient, TesterClient, PragmaticClient
from src.database import Transaction, Database


# Simulated cost per token (creates efficiency pressure even with local LLM)
COST_PER_TOKEN = 0.001

# Retirement settings
MAX_LIFESPAN = 15       # txs before forced retirement (was 40)
MAX_GEN_GAP = 2         # max generations behind (was 3)

# Bankruptcy threshold
BANKRUPTCY_MIN_TXS = 5  # minimum txs before bankruptcy check
BANKRUPTCY_AVG_PRICE = 6.0  # avg price below this = death


@dataclass
class Request:
    """Marketplace request for code generation."""
    request_id: str
    description: str
    client: object


class MarketplaceV3:
    """Improved marketplace with real competitive pressure."""

    def __init__(self, agents: List[SimpleAgent], db: Database):
        self.agents = agents
        self.db = db
        self.clients = [
            MinimalistClient(),
            DocumenterClient(),
            TesterClient(),
            PragmaticClient()
        ]
        self.transactions = []
        self.request_counter = 0

    def generate_request(self) -> Request:
        """Generate request with more variety."""
        descriptions = [
            "Function to calculate factorial",
            "Class to parse CSV files",
            "Function to validate email addresses",
            "Function to merge two sorted lists",
            "Class for a simple stack data structure",
            "Function to find the longest common subsequence",
            "Class for a binary search tree",
            "Function to convert Roman numerals to integers",
            "Function to implement a simple cache (LRU)",
            "Class for a priority queue",
            "Function to flatten a nested dictionary",
            "Function to check if a string is a valid palindrome",
            "Function to generate Fibonacci sequence with memoization",
            "Class for a simple linked list with insert/delete/search",
            "Function to find all permutations of a string",
        ]

        self.request_counter += 1
        return Request(
            request_id=f"req_{self.request_counter}",
            description=random.choice(descriptions),
            client=random.choice(self.clients)
        )

    def process_request(self, request: Request) -> Transaction:
        """Process request with simulated token costs."""
        # Client selects agent
        agent = request.client.select_agent(self.agents, self.db)

        # Generate solution
        code, tokens_used, _ = agent.solve_request(request.description)

        # Calculate simulated cost (creates efficiency pressure)
        simulated_cost = tokens_used * COST_PER_TOKEN

        # Evaluate
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
            api_cost=simulated_cost
        )

        # Update agent state
        agent.config.total_revenue += evaluation.price_paid
        agent.config.total_costs += simulated_cost
        agent.config.net_profit = agent.config.total_revenue - agent.config.total_costs
        agent.config.transaction_count += 1

        self.transactions.append(transaction)
        return transaction

    def retire_old_agents(self, current_generation: int):
        """
        Aggressive retirement + bankruptcy.
        
        Agents die if:
        1. Too many transactions (max_lifespan)
        2. Too many generations behind
        3. Bankrupt (avg price too low after min txs)
        """
        active = []
        retired = []

        for agent in self.agents:
            # Retirement conditions
            too_many_txs = agent.config.transaction_count >= MAX_LIFESPAN
            too_old = (current_generation - agent.config.generation) > MAX_GEN_GAP
            
            # Bankruptcy check
            bankrupt = False
            if agent.config.transaction_count >= BANKRUPTCY_MIN_TXS:
                avg_price = agent.config.total_revenue / agent.config.transaction_count
                if avg_price < BANKRUPTCY_AVG_PRICE:
                    bankrupt = True

            if too_many_txs or too_old or bankrupt:
                reason = "lifespan" if too_many_txs else ("gen_gap" if too_old else "bankrupt")
                retired.append((agent, reason))
                agent.config.status = "retired"
                self.db.update_agent_status(agent.config.agent_id, "retired")
            else:
                active.append(agent)

        self.agents = active
        return retired

    def get_market_stats(self):
        """Get current market statistics."""
        active = [a for a in self.agents if a.config.status == "active"]
        return {
            'active_agents': len(active),
            'total_transactions': len(self.transactions),
            'avg_price': sum(t.price_paid for t in self.transactions) / max(1, len(self.transactions)),
            'total_revenue': sum(a.config.total_revenue for a in self.agents),
            'total_costs': sum(a.config.total_costs for a in self.agents),
        }
