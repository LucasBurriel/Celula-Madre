"""
Bot client module V3 for Célula Madre.
Improved clients with:
- Epsilon-greedy exploration (try new agents naturally)
- Neutral defaults for unknown agents
- More granular pricing (continuous scale)
"""

import ast
import random
import math
from dataclasses import dataclass


@dataclass
class EvaluationResult:
    """Result of client evaluation of generated code."""
    client_name: str
    price_paid: float
    feedback: str


# Exploration rate: probability of trying a random agent
EXPLORATION_RATE = 0.30


class BaseClient:
    """Base client with shared exploration logic."""

    BASE_PRICE = 10.0
    EXPLORATION_RATE = EXPLORATION_RATE

    def _explore_or_exploit(self, agents, scores):
        """
        Epsilon-greedy agent selection.
        
        - With probability EXPLORATION_RATE: pick random agent
        - Otherwise: pick best-scoring agent
        
        This models natural consumer behavior (trying new things)
        not subsidies.
        """
        if random.random() < self.EXPLORATION_RATE:
            return random.choice(agents)
        
        if not scores or max(scores) == 0:
            return random.choice(agents)
        
        return agents[scores.index(max(scores))]


class MinimalistClient(BaseClient):
    """Client that pays more for concise code. Continuous pricing."""

    def select_agent(self, agents, db):
        agent_scores = []
        for agent in agents:
            tx_count = db.get_transaction_count(agent.config.agent_id)
            if tx_count < 2:
                # Neutral default: average score for unknowns
                agent_scores.append(0.5)
                continue
            
            avg_lines = db.get_avg_code_length(agent.config.agent_id)
            verbose_rate = db.get_feedback_rate(agent.config.agent_id, "Too verbose")
            
            # Lower lines = higher score, normalized
            score = 1.0 / (1.0 + avg_lines / 30.0)
            score *= (1.0 - verbose_rate * 0.5)
            agent_scores.append(score)

        return self._explore_or_exploit(agents, agent_scores)

    def evaluate(self, code: str) -> EvaluationResult:
        """Continuous pricing based on line count."""
        lines = len([l for l in code.split('\n') if l.strip()])
        
        # Continuous scale: fewer lines = more money
        # Sweet spot at 10-15 lines, diminishing returns below
        if lines <= 5:
            multiplier = 1.3  # Too short might miss things
        elif lines <= 15:
            multiplier = 1.8  # Sweet spot
        elif lines <= 25:
            multiplier = 1.4
        elif lines <= 40:
            multiplier = 1.0
        elif lines <= 60:
            multiplier = 0.7
        else:
            multiplier = 0.5
        
        price = round(self.BASE_PRICE * multiplier, 2)
        
        if lines <= 15:
            feedback = f"Excellent brevity ({lines} lines)"
        elif lines <= 40:
            feedback = f"Acceptable length ({lines} lines)"
        else:
            feedback = f"Too verbose ({lines} lines)"

        return EvaluationResult("MinimalistClient", price, feedback)


class DocumenterClient(BaseClient):
    """Client that pays more for good documentation. Counts quality markers."""

    def select_agent(self, agents, db):
        agent_scores = []
        for agent in agents:
            tx_count = db.get_transaction_count(agent.config.agent_id)
            if tx_count < 2:
                agent_scores.append(0.5)
                continue
            
            excellent_rate = db.get_feedback_rate(agent.config.agent_id, "Excellent documentation")
            good_rate = db.get_feedback_rate(agent.config.agent_id, "Good documentation")
            score = excellent_rate * 2.0 + good_rate * 1.0
            agent_scores.append(max(score, 0.1))

        return self._explore_or_exploit(agents, agent_scores)

    def evaluate(self, code: str) -> EvaluationResult:
        """Granular documentation scoring."""
        docstring_count = code.count('"""') // 2 + code.count("'''") // 2
        comment_lines = sum(1 for l in code.split('\n') if l.strip().startswith('#'))
        has_type_hints = ':' in code and '->' in code
        
        # Documentation score 0-10
        doc_score = min(docstring_count * 2, 6) + min(comment_lines, 3) + (1 if has_type_hints else 0)
        doc_score = min(doc_score, 10)
        
        # Continuous pricing: score/10 maps to 0.5x-2.0x
        multiplier = 0.5 + (doc_score / 10.0) * 1.5
        price = round(self.BASE_PRICE * multiplier, 2)
        
        if doc_score >= 7:
            feedback = f"Excellent documentation (score: {doc_score}/10)"
        elif doc_score >= 4:
            feedback = f"Good documentation (score: {doc_score}/10)"
        else:
            feedback = f"Poor documentation (score: {doc_score}/10)"

        return EvaluationResult("DocumenterClient", price, feedback)


class TesterClient(BaseClient):
    """Client that pays more for tests. Counts test functions and assertions."""

    def select_agent(self, agents, db):
        agent_scores = []
        for agent in agents:
            tx_count = db.get_transaction_count(agent.config.agent_id)
            if tx_count < 2:
                agent_scores.append(0.5)
                continue
            
            comprehensive_rate = db.get_feedback_rate(agent.config.agent_id, "Comprehensive tests")
            basic_rate = db.get_feedback_rate(agent.config.agent_id, "Basic tests included")
            score = comprehensive_rate * 2.0 + basic_rate * 1.0
            agent_scores.append(max(score, 0.1))

        return self._explore_or_exploit(agents, agent_scores)

    def evaluate(self, code: str) -> EvaluationResult:
        """Granular test scoring."""
        test_funcs = code.count('def test_')
        assert_count = code.count('assert ')
        has_setup = 'setUp' in code or 'setup' in code or 'fixture' in code
        
        # Test score 0-10
        test_score = min(test_funcs * 2, 6) + min(assert_count, 3) + (1 if has_setup else 0)
        test_score = min(test_score, 10)
        
        # Continuous pricing
        multiplier = 0.4 + (test_score / 10.0) * 1.8
        price = round(self.BASE_PRICE * multiplier, 2)
        
        if test_score >= 7:
            feedback = f"Comprehensive tests (score: {test_score}/10)"
        elif test_score >= 3:
            feedback = f"Basic tests included (score: {test_score}/10)"
        else:
            feedback = f"No tests (score: {test_score}/10)"

        return EvaluationResult("TesterClient", price, feedback)


class PragmaticClient(BaseClient):
    """Client that pays for simplicity and working code."""

    def select_agent(self, agents, db):
        agent_scores = []
        for agent in agents:
            tx_count = db.get_transaction_count(agent.config.agent_id)
            if tx_count < 2:
                agent_scores.append(0.5)
                continue
            
            success_rate = db.get_success_rate(agent.config.agent_id)
            reputation = db.get_reputation(agent.config.agent_id)
            score = success_rate * 0.6 + reputation * 0.4
            agent_scores.append(score)

        return self._explore_or_exploit(agents, agent_scores)

    def evaluate(self, code: str) -> EvaluationResult:
        """Granular pragmatic scoring."""
        # Parseable?
        try:
            ast.parse(code)
            parseable = True
        except SyntaxError:
            parseable = False

        lines = len([l for l in code.split('\n') if l.strip()])
        has_main = '__main__' in code or 'def main' in code
        has_error_handling = 'try:' in code or 'except' in code
        
        if not parseable:
            price = round(self.BASE_PRICE * 0.2, 2)
            feedback = "Broken code"
            return EvaluationResult("PragmaticClient", price, feedback)
        
        # Pragmatic score: works + simple + robust
        pragma_score = 4  # Base: it parses
        if lines < 30:
            pragma_score += 2
        elif lines < 50:
            pragma_score += 1
        if has_error_handling:
            pragma_score += 2
        if has_main:
            pragma_score += 1
        pragma_score = min(pragma_score, 10)
        
        multiplier = 0.5 + (pragma_score / 10.0) * 1.5
        price = round(self.BASE_PRICE * multiplier, 2)
        
        if pragma_score >= 7:
            feedback = f"Simple and works (score: {pragma_score}/10)"
        elif pragma_score >= 4:
            feedback = f"Works (score: {pragma_score}/10)"
        else:
            feedback = f"Barely functional (score: {pragma_score}/10)"

        return EvaluationResult("PragmaticClient", price, feedback)
