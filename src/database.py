"""
Database module for Célula Madre MVP.
Handles persistence of agents and transactions using SQLite.
"""

import sqlite3
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class AgentConfig:
    """Configuration for a code-generating agent."""
    agent_id: str
    generation: int
    parent_id: Optional[str]
    system_prompt: str
    total_revenue: float = 0.0
    transaction_count: int = 0
    total_costs: float = 0.0
    net_profit: float = 0.0
    status: str = "active"


@dataclass
class Transaction:
    """Record of a completed marketplace transaction."""
    request_id: str
    agent_id: str
    code_generated: str
    price_paid: float
    client_name: str
    feedback: str
    tokens_used: int = 0
    api_cost: float = 0.0


class Database:
    """SQLite database for storing agents and transactions."""

    def __init__(self, db_path: str = "celula_madre.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        """Initialize database schema from schema.sql file."""
        schema_path = Path(__file__).parent.parent / "schema.sql"
        with open(schema_path, 'r') as f:
            self.conn.executescript(f.read())
        self.conn.commit()

    def save_agent(self, config: AgentConfig):
        """
        Save agent configuration to database.

        Args:
            config: Agent configuration to save
        """
        self.conn.execute("""
            INSERT INTO agents (agent_id, generation, parent_id, system_prompt,
                                total_revenue, transaction_count, total_costs, net_profit, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (config.agent_id, config.generation, config.parent_id,
              config.system_prompt, config.total_revenue, config.transaction_count,
              config.total_costs, config.net_profit, config.status))
        self.conn.commit()

    def update_agent_revenue(self, agent_id: str, revenue_delta: float, cost_delta: float = 0.0):
        """
        Update agent's revenue, costs, and transaction count.

        Args:
            agent_id: ID of agent to update
            revenue_delta: Amount to add to total revenue
            cost_delta: Amount to add to total costs
        """
        self.conn.execute("""
            UPDATE agents
            SET total_revenue = total_revenue + ?,
                total_costs = total_costs + ?,
                net_profit = total_revenue - total_costs,
                transaction_count = transaction_count + 1
            WHERE agent_id = ?
        """, (revenue_delta, cost_delta, agent_id))
        self.conn.commit()

    def save_transaction(self, tx: Transaction):
        """
        Save transaction record to database.

        Args:
            tx: Transaction to save
        """
        self.conn.execute("""
            INSERT INTO transactions (request_id, agent_id, code_generated,
                                      price_paid, client_name, feedback, tokens_used, api_cost)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (tx.request_id, tx.agent_id, tx.code_generated,
              tx.price_paid, tx.client_name, tx.feedback, tx.tokens_used, tx.api_cost))
        self.conn.commit()

    def get_all_agents(self) -> List[AgentConfig]:
        """
        Retrieve all agents ordered by revenue (highest first).

        Returns:
            List of agent configurations
        """
        rows = self.conn.execute(
            "SELECT * FROM agents ORDER BY total_revenue DESC"
        ).fetchall()

        return [AgentConfig(
            agent_id=row['agent_id'],
            generation=row['generation'],
            parent_id=row['parent_id'],
            system_prompt=row['system_prompt'],
            total_revenue=row['total_revenue'],
            transaction_count=row['transaction_count'],
            total_costs=row['total_costs'],
            net_profit=row['net_profit'],
            status=row['status']
        ) for row in rows]

    def get_recent_feedback(self, agent_id: str, limit: int = 5) -> List[str]:
        """
        Get recent feedback for an agent.

        Args:
            agent_id: ID of agent
            limit: Maximum number of feedback items to return

        Returns:
            List of feedback strings
        """
        rows = self.conn.execute("""
            SELECT feedback FROM transactions
            WHERE agent_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (agent_id, limit)).fetchall()

        return [row['feedback'] for row in rows if row['feedback']]

    def get_lineage_revenue(self, agent_id: str) -> float:
        """
        Calculate total revenue of agent's entire lineage (all descendants).

        This implements Clade-Metaproductivity (CMP) - measuring success
        of an agent's family tree rather than individual performance.

        Args:
            agent_id: ID of agent to calculate lineage for

        Returns:
            Total revenue of agent + all descendants (children, grandchildren, etc.)
        """
        # Recursive CTE to find all descendants
        query = """
            WITH RECURSIVE descendants AS (
                -- Base case: the agent itself
                SELECT agent_id, total_revenue
                FROM agents
                WHERE agent_id = ?

                UNION ALL

                -- Recursive case: children of descendants
                SELECT a.agent_id, a.total_revenue
                FROM agents a
                INNER JOIN descendants d ON a.parent_id = d.agent_id
            )
            SELECT SUM(total_revenue) as lineage_revenue
            FROM descendants
        """

        result = self.conn.execute(query, (agent_id,)).fetchone()
        return result['lineage_revenue'] or 0.0

    def get_avg_code_length(self, agent_id: str) -> float:
        """
        Get average code length (lines) for an agent.

        Args:
            agent_id: ID of agent

        Returns:
            Average number of non-empty lines per code generation
        """
        rows = self.conn.execute("""
            SELECT code_generated FROM transactions
            WHERE agent_id = ?
        """, (agent_id,)).fetchall()

        if not rows:
            return 50.0  # Default assumption for new agents

        total_lines = 0
        for row in rows:
            code = row['code_generated']
            lines = len([l for l in code.split('\n') if l.strip()])
            total_lines += lines

        return total_lines / len(rows)

    def get_feedback_rate(self, agent_id: str, feedback_text: str) -> float:
        """
        Get rate of specific feedback for an agent.

        Args:
            agent_id: ID of agent
            feedback_text: Feedback to search for (e.g., "Too verbose")

        Returns:
            Rate (0.0-1.0) of this feedback in agent's history
        """
        total = self.conn.execute("""
            SELECT COUNT(*) as count FROM transactions
            WHERE agent_id = ?
        """, (agent_id,)).fetchone()['count']

        if total == 0:
            return 0.0

        matching = self.conn.execute("""
            SELECT COUNT(*) as count FROM transactions
            WHERE agent_id = ? AND feedback = ?
        """, (agent_id, feedback_text)).fetchone()['count']

        return matching / total

    def get_success_rate(self, agent_id: str) -> float:
        """
        Get success rate (non-broken code) for an agent.

        Args:
            agent_id: ID of agent

        Returns:
            Rate (0.0-1.0) of successful (non-broken) code
        """
        total = self.conn.execute("""
            SELECT COUNT(*) as count FROM transactions
            WHERE agent_id = ?
        """, (agent_id,)).fetchone()['count']

        if total == 0:
            return 0.5  # Neutral assumption for new agents

        broken = self.conn.execute("""
            SELECT COUNT(*) as count FROM transactions
            WHERE agent_id = ? AND feedback = 'Broken code'
        """, (agent_id,)).fetchone()['count']

        return 1.0 - (broken / total)

    def get_transaction_count(self, agent_id: str) -> int:
        """
        Get total transaction count for an agent.

        Args:
            agent_id: ID of agent

        Returns:
            Number of transactions
        """
        result = self.conn.execute("""
            SELECT transaction_count FROM agents
            WHERE agent_id = ?
        """, (agent_id,)).fetchone()

        return result['transaction_count'] if result else 0

    def get_reputation(self, agent_id: str) -> float:
        """
        Calculate reputation score for an agent.

        Reputation = success_rate * experience_factor
        Experience factor: min(tx_count / 10, 1.0)

        This prevents new agents with 1 lucky transaction from having
        artificially high reputation.

        Args:
            agent_id: ID of agent

        Returns:
            Reputation score (0.0-1.0)
        """
        success_rate = self.get_success_rate(agent_id)
        tx_count = self.get_transaction_count(agent_id)

        # Experience factor caps at 10 transactions
        experience_factor = min(tx_count / 10.0, 1.0)

        return success_rate * experience_factor

    def update_agent_status(self, agent_id: str, status: str):
        """
        Update agent status (active/retired).

        Args:
            agent_id: ID of agent
            status: New status ('active' or 'retired')
        """
        self.conn.execute("""
            UPDATE agents
            SET status = ?
            WHERE agent_id = ?
        """, (status, agent_id))
        self.conn.commit()

    def close(self):
        """Close database connection."""
        self.conn.close()
