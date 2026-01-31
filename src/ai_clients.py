"""
AI Client module for Célula Madre.
Clients powered by LLMs that make intelligent decisions about agent selection and pricing.
"""

import random
import re
from dataclasses import dataclass
from typing import List, Dict
from anthropic import Anthropic

from src.database import Database


@dataclass
class EvaluationResult:
    """Result of client evaluation of generated code."""
    client_name: str
    price_paid: float
    feedback: str


@dataclass
class ClientExperience:
    """Record of past transaction from client perspective."""
    agent_id: str
    price_paid: float
    feedback: str
    satisfaction: float  # 0-10 scale


class AIClient:
    """AI-powered client that uses LLM to make selection and evaluation decisions."""

    def __init__(self, client_id: str, preferences: str, budget: float):
        """
        Initialize AI client.

        Args:
            client_id: Unique identifier for this client
            preferences: Natural language description of what client values
            budget: Total budget available for transactions
        """
        self.client_id = client_id
        self.preferences = preferences
        self.initial_budget = budget
        self.budget = budget
        self.spent = 0.0
        self.experience: List[ClientExperience] = []
        self.exploration_rate = 0.3  # Initial uncertainty
        self.client = Anthropic()

    def select_agent(self, agents, db: Database):
        """
        AI-driven agent selection based on preferences and experience.

        Args:
            agents: List of available agents
            db: Database for agent history

        Returns:
            Selected agent
        """
        # Build agent profiles
        agent_descriptions = self._build_agent_profiles(agents, db)
        recent_exp = self._format_recent_experience()

        prompt = f"""You are a software client making a hiring decision.

YOUR PROFILE:
{self.preferences}

BUDGET STATUS:
- Initial budget: ${self.initial_budget:.2f}
- Remaining: ${self.budget:.2f}
- Already spent: ${self.spent:.2f}

AVAILABLE AGENTS:
{agent_descriptions}

YOUR RECENT EXPERIENCE:
{recent_exp if recent_exp else "No prior experience with these agents."}

TASK: Select which agent to hire for a Python coding task.

CONSIDERATIONS:
1. Quality/price trade-off based on your values
2. Your past experience with agents (if any)
3. Risk of trying new vs sticking with known agents
4. Your remaining budget

INSTRUCTIONS:
Think step-by-step about your decision, then output ONLY the agent_id to select on the last line.
Format: SELECTED: agent_id
"""

        response = self.client.messages.create(
            model="claude-3-5-haiku-20241022",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800
        )

        # Parse selected agent ID
        text = response.content[0].text
        selected_id = self._parse_agent_id(text, agents)

        return self._find_agent_by_id(agents, selected_id)

    def evaluate(self, code: str, agent) -> EvaluationResult:
        """
        AI-driven evaluation and pricing of generated code.

        Args:
            code: Generated code to evaluate
            agent: Agent that generated the code

        Returns:
            Evaluation with price and feedback
        """
        prompt = f"""You are a software client evaluating code you commissioned.

YOUR PREFERENCES:
{self.preferences}

AGENT: {agent.config.agent_id}
AGENT'S TRACK RECORD: {agent.config.transaction_count} completed tasks

CODE TO EVALUATE:
```python
{code}
```

YOUR BUDGET: ${self.budget:.2f} remaining

TASK: Evaluate this code and decide how much to pay (between $3-20).

CONSIDERATIONS:
1. Does it meet your quality standards based on your preferences?
2. How does quality compare to price?
3. Is it worth the cost relative to your budget?
4. How does it compare to past work (if you've hired this agent before)?

OUTPUT FORMAT (must follow exactly):
PRICE: $XX.XX
FEEDBACK: <one concise sentence about the code>

Example:
PRICE: $15.00
FEEDBACK: Excellent documentation and clean structure
"""

        response = self.client.messages.create(
            model="claude-3-5-haiku-20241022",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )

        # Parse price and feedback
        text = response.content[0].text
        price, feedback = self._parse_evaluation(text)

        # Update client state
        satisfaction = self._calculate_satisfaction(price, self.budget)
        self.experience.append(ClientExperience(
            agent_id=agent.config.agent_id,
            price_paid=price,
            feedback=feedback,
            satisfaction=satisfaction
        ))

        self.spent += price
        self.budget -= price

        # Decrease exploration rate as client gains experience
        self.exploration_rate *= 0.95

        return EvaluationResult(
            client_name=self.client_id,
            price_paid=price,
            feedback=feedback
        )

    def _build_agent_profiles(self, agents, db: Database) -> str:
        """Build text description of available agents."""
        profiles = []

        for agent in agents:
            avg_price = agent.config.total_revenue / max(1, agent.config.transaction_count)
            success_rate = db.get_success_rate(agent.config.agent_id)
            tx_count = agent.config.transaction_count

            status = "NEW (no track record)" if tx_count < 3 else f"ESTABLISHED ({tx_count} tasks)"

            profile = f"""
• {agent.config.agent_id}
  - Status: {status}
  - Avg Price: ${avg_price:.2f}
  - Success Rate: {success_rate:.0%}
  - Generation: {agent.config.generation}
"""
            profiles.append(profile)

        return "\n".join(profiles)

    def _format_recent_experience(self) -> str:
        """Format recent experience for context."""
        if not self.experience:
            return ""

        recent = self.experience[-5:]  # Last 5 transactions
        formatted = []

        for exp in recent:
            formatted.append(
                f"• {exp.agent_id}: Paid ${exp.price_paid:.2f} - {exp.feedback} "
                f"(Satisfaction: {exp.satisfaction:.1f}/10)"
            )

        return "\n".join(formatted)

    def _parse_agent_id(self, text: str, agents) -> str:
        """Extract agent_id from LLM response."""
        # Look for SELECTED: pattern
        match = re.search(r'SELECTED:\s*(\S+)', text, re.IGNORECASE)
        if match:
            return match.group(1)

        # Fallback: look for any agent_id mentioned
        agent_ids = [a.config.agent_id for a in agents]
        for agent_id in agent_ids:
            if agent_id in text:
                return agent_id

        # Last resort: random choice
        return random.choice(agents).config.agent_id

    def _parse_evaluation(self, text: str) -> tuple[float, str]:
        """Parse price and feedback from evaluation response."""
        # Extract price
        price_match = re.search(r'PRICE:\s*\$?(\d+\.?\d*)', text, re.IGNORECASE)
        if price_match:
            price = float(price_match.group(1))
        else:
            price = 10.0  # Default

        # Clamp price to reasonable range
        price = max(3.0, min(20.0, price))

        # Extract feedback
        feedback_match = re.search(r'FEEDBACK:\s*(.+)', text, re.IGNORECASE)
        if feedback_match:
            feedback = feedback_match.group(1).strip()
        else:
            feedback = "Code evaluated"

        # Truncate long feedback
        if len(feedback) > 100:
            feedback = feedback[:97] + "..."

        return price, feedback

    def _calculate_satisfaction(self, price: float, budget_remaining: float) -> float:
        """Calculate satisfaction score (0-10) based on transaction."""
        # Higher satisfaction if:
        # - Price is reasonable relative to budget
        # - Client got what they wanted (implicit in AI evaluation)

        budget_ratio = price / (budget_remaining + price)

        if budget_ratio < 0.1:  # Cheap relative to budget
            base_satisfaction = 8.0
        elif budget_ratio < 0.2:  # Reasonable
            base_satisfaction = 7.0
        elif budget_ratio < 0.3:  # Pricey
            base_satisfaction = 6.0
        else:  # Expensive
            base_satisfaction = 5.0

        # Add some randomness
        satisfaction = base_satisfaction + random.uniform(-1, 1)
        return max(0, min(10, satisfaction))

    def _find_agent_by_id(self, agents, agent_id: str):
        """Find agent by ID."""
        for agent in agents:
            if agent.config.agent_id == agent_id:
                return agent

        # Fallback: return random agent
        return random.choice(agents)


# Predefined client personalities
def create_budget_client():
    """Budget-conscious startup client."""
    return AIClient(
        client_id="BudgetStartup",
        preferences="""I'm a startup with limited budget. I value:
- Code that works reliably
- Reasonable prices (prefer $8-12 range)
- Willing to sacrifice extensive documentation for lower cost
- Simplicity and practicality over perfection
- Need to stretch my budget across multiple tasks""",
        budget=100.0
    )


def create_quality_client():
    """Quality-focused enterprise client."""
    return AIClient(
        client_id="EnterpriseQuality",
        preferences="""I'm an enterprise client with high standards. I value:
- Comprehensive documentation (critical for team collaboration)
- Extensive test coverage
- Clean, maintainable code
- Professional quality above all else
- Price is secondary to quality (willing to pay $15-20 for excellence)""",
        budget=400.0
    )


def create_experimental_client():
    """Research-focused experimental client."""
    return AIClient(
        client_id="ResearchLab",
        preferences="""I'm a research lab exploring new approaches. I value:
- Novelty and creative solutions
- Willing to try new, unproven agents
- Tolerate some risk for potential innovation
- Interested in seeing different coding styles
- Moderate budget, looking for good value ($10-15 range)""",
        budget=200.0
    )


def create_pragmatic_client():
    """Balanced pragmatic freelancer client."""
    return AIClient(
        client_id="PragmaticFreelancer",
        preferences="""I'm a freelancer balancing quality and cost. I value:
- "Good enough" code that works well
- Fair pricing in the $10-14 range
- Balance between documentation and brevity
- Reliability and consistency
- Not interested in paying premium for perfection""",
        budget=150.0
    )
