"""
Bot client module for Célula Madre MVP.
Simulates clients with different code quality preferences.
"""

import ast
from dataclasses import dataclass


@dataclass
class EvaluationResult:
    """Result of client evaluation of generated code."""
    client_name: str
    price_paid: float
    feedback: str


class MinimalistClient:
    """Client that pays more for concise code."""

    BASE_PRICE = 10.0

    def select_agent(self, agents, db):
        """
        MinimalistClient prefers agents with low avg line count.

        Strategy: Avoid "too verbose" agents, prefer those with brevity track record.
        """
        from src.agent import SimpleAgent

        # Get track records
        agent_scores = []
        for agent in agents:
            avg_lines = db.get_avg_code_length(agent.config.agent_id)
            verbose_rate = db.get_feedback_rate(agent.config.agent_id, "Too verbose")

            # Penalize verbose history
            score = 1.0 / (avg_lines + 10)  # Lower lines = higher score
            score *= (1.0 - verbose_rate)    # Penalize verbose feedback

            agent_scores.append(score)

        # Weighted random (prefer high scores but allow exploration)
        if sum(agent_scores) > 0:
            return agents[agent_scores.index(max(agent_scores))]
        else:
            return agents[0]  # Fallback

    def evaluate(self, code: str) -> EvaluationResult:
        """
        Evaluate code based on brevity.

        Args:
            code: Generated Python code

        Returns:
            Evaluation with price based on code length
        """
        lines = len([l for l in code.split('\n') if l.strip()])

        if lines < 20:
            price = self.BASE_PRICE * 1.5  # $15
            feedback = "Excellent brevity"
        elif lines < 40:
            price = self.BASE_PRICE  # $10
            feedback = "Good length"
        else:
            price = self.BASE_PRICE * 0.7  # $7
            feedback = "Too verbose"

        return EvaluationResult("MinimalistClient", price, feedback)


class DocumenterClient:
    """Client that pays more for good documentation."""

    BASE_PRICE = 10.0

    def select_agent(self, agents, db):
        """
        DocumenterClient prefers agents with good documentation track record.

        Strategy: Prefer "Excellent documentation" history.
        """
        agent_scores = []
        for agent in agents:
            excellent_rate = db.get_feedback_rate(agent.config.agent_id, "Excellent documentation")
            good_rate = db.get_feedback_rate(agent.config.agent_id, "Good documentation")

            # Score = weighted preference for good docs
            score = excellent_rate * 2.0 + good_rate * 1.0

            agent_scores.append(score)

        # Select best, or random if all tied
        if sum(agent_scores) > 0:
            return agents[agent_scores.index(max(agent_scores))]
        else:
            import random
            return random.choice(agents)

    def evaluate(self, code: str) -> EvaluationResult:
        """
        Evaluate code based on documentation quality.

        Args:
            code: Generated Python code

        Returns:
            Evaluation with price based on docstrings and comments
        """
        has_docstring = '"""' in code or "'''" in code
        has_comments = '#' in code

        if has_docstring and has_comments:
            price = self.BASE_PRICE * 1.8  # $18
            feedback = "Excellent documentation"
        elif has_docstring or has_comments:
            price = self.BASE_PRICE * 1.2  # $12
            feedback = "Good documentation"
        else:
            price = self.BASE_PRICE * 0.6  # $6
            feedback = "Poor documentation"

        return EvaluationResult("DocumenterClient", price, feedback)


class TesterClient:
    """Client that pays more for tests."""

    BASE_PRICE = 10.0

    def select_agent(self, agents, db):
        """
        TesterClient prefers agents with comprehensive test track record.

        Strategy: Prefer "Comprehensive tests" history.
        """
        agent_scores = []
        for agent in agents:
            comprehensive_rate = db.get_feedback_rate(agent.config.agent_id, "Comprehensive tests")
            basic_rate = db.get_feedback_rate(agent.config.agent_id, "Basic tests included")

            # Score = weighted preference for tests
            score = comprehensive_rate * 2.0 + basic_rate * 1.0

            agent_scores.append(score)

        if sum(agent_scores) > 0:
            return agents[agent_scores.index(max(agent_scores))]
        else:
            import random
            return random.choice(agents)

    def evaluate(self, code: str) -> EvaluationResult:
        """
        Evaluate code based on test coverage.

        Args:
            code: Generated Python code

        Returns:
            Evaluation with price based on number of tests
        """
        has_test = 'def test_' in code or 'assert' in code
        test_count = code.count('def test_')

        if test_count >= 3:
            price = self.BASE_PRICE * 2.0  # $20
            feedback = "Comprehensive tests"
        elif has_test:
            price = self.BASE_PRICE * 1.3  # $13
            feedback = "Basic tests included"
        else:
            price = self.BASE_PRICE * 0.5  # $5
            feedback = "No tests"

        return EvaluationResult("TesterClient", price, feedback)


class PragmaticClient:
    """Client that pays for simplicity and working code."""

    BASE_PRICE = 10.0

    def select_agent(self, agents, db):
        """
        PragmaticClient prefers agents with high success rate and simplicity.

        Strategy: Avoid "Broken code", prefer "Simple and works".
        """
        agent_scores = []
        for agent in agents:
            success_rate = db.get_success_rate(agent.config.agent_id)
            simple_rate = db.get_feedback_rate(agent.config.agent_id, "Simple and works")

            # Score = success + simplicity bonus
            score = success_rate + simple_rate * 0.5

            agent_scores.append(score)

        if sum(agent_scores) > 0:
            return agents[agent_scores.index(max(agent_scores))]
        else:
            import random
            return random.choice(agents)

    def evaluate(self, code: str) -> EvaluationResult:
        """
        Evaluate code based on simplicity and correctness.

        Args:
            code: Generated Python code

        Returns:
            Evaluation with price based on parseability and simplicity
        """
        # Validate: code is parseable
        try:
            ast.parse(code)
            parseable = True
        except SyntaxError:
            parseable = False

        lines = len([l for l in code.split('\n') if l.strip()])

        if parseable and lines < 30:
            price = self.BASE_PRICE * 1.4  # $14
            feedback = "Simple and works"
        elif parseable:
            price = self.BASE_PRICE  # $10
            feedback = "Works"
        else:
            price = self.BASE_PRICE * 0.3  # $3
            feedback = "Broken code"

        return EvaluationResult("PragmaticClient", price, feedback)
