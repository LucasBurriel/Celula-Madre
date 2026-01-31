"""
Unit tests for Bot Clients component.
Tests based on acceptance criteria from plan.
"""

import pytest
from src.clients import (
    MinimalistClient,
    DocumenterClient,
    TesterClient,
    PragmaticClient,
    EvaluationResult
)


def test_minimalist_prefers_short_code():
    """
    Acceptance criteria: Minimalist pays more for code < 20 LOC than code > 50 LOC
    """
    # Arrange
    client = MinimalistClient()
    short_code = "def sum(a, b):\n    return a + b"  # ~2 lines
    long_code = "\n".join([f"# Comment {i}" for i in range(60)])  # 60 lines

    # Act
    result_short = client.evaluate(short_code)
    result_long = client.evaluate(long_code)

    # Assert
    assert result_short.price_paid > result_long.price_paid
    assert result_short.price_paid == 15.0  # 1.5x base
    assert result_long.price_paid == 7.0    # 0.7x base
    assert result_short.feedback == "Excellent brevity"


def test_documenter_prefers_docstrings():
    """
    Acceptance criteria: Documenter pays more for code with docstrings than without
    """
    # Arrange
    client = DocumenterClient()

    code_with_docs = '''
def factorial(n):
    """Calculate factorial of n."""
    # Handle base case
    return 1 if n == 0 else n * factorial(n-1)
'''

    code_without_docs = '''
def factorial(n):
    return 1 if n == 0 else n * factorial(n-1)
'''

    # Act
    result_with_docs = client.evaluate(code_with_docs)
    result_without_docs = client.evaluate(code_without_docs)

    # Assert
    assert result_with_docs.price_paid > result_without_docs.price_paid
    assert result_with_docs.price_paid == 18.0  # 1.8x base (docstring + comments)
    assert result_without_docs.price_paid == 6.0  # 0.6x base (no docs)


def test_tester_prefers_tests():
    """
    Acceptance criteria: Tester pays more for code with 3+ tests than code without tests
    """
    # Arrange
    client = TesterClient()

    code_with_tests = '''
def add(a, b):
    return a + b

def test_add_positive():
    assert add(2, 3) == 5

def test_add_negative():
    assert add(-1, -1) == -2

def test_add_zero():
    assert add(0, 5) == 5
'''

    code_without_tests = '''
def add(a, b):
    return a + b
'''

    # Act
    result_with_tests = client.evaluate(code_with_tests)
    result_without_tests = client.evaluate(code_without_tests)

    # Assert
    assert result_with_tests.price_paid > result_without_tests.price_paid
    assert result_with_tests.price_paid == 20.0  # 2.0x base (3+ tests)
    assert result_without_tests.price_paid == 5.0  # 0.5x base (no tests)
    assert result_with_tests.feedback == "Comprehensive tests"


def test_pragmatic_prefers_simple_working_code():
    """
    Test that pragmatic client prefers simple, parseable code
    """
    # Arrange
    client = PragmaticClient()

    simple_working = "def greet():\n    return 'hello'"  # < 30 lines, parseable
    complex_working = "\n".join([f"x{i} = {i}" for i in range(50)])  # > 30 lines, parseable
    broken_code = "def broken(\n    return"  # Syntax error

    # Act
    result_simple = client.evaluate(simple_working)
    result_complex = client.evaluate(complex_working)
    result_broken = client.evaluate(broken_code)

    # Assert
    assert result_simple.price_paid > result_complex.price_paid
    assert result_simple.price_paid > result_broken.price_paid
    assert result_simple.price_paid == 14.0  # 1.4x base (parseable + < 30 lines)
    assert result_complex.price_paid == 10.0  # 1.0x base (parseable but verbose)
    assert result_broken.price_paid == 3.0   # 0.3x base (syntax error)


def test_same_code_different_prices():
    """
    Acceptance criteria: Same code evaluated by 4 bots → 4 different prices
    """
    # Arrange
    code = '''
def factorial(n):
    """Calculate factorial."""
    return 1 if n == 0 else n * factorial(n-1)

def test_factorial():
    assert factorial(5) == 120
'''

    minimalist = MinimalistClient()
    documenter = DocumenterClient()
    tester = TesterClient()
    pragmatic = PragmaticClient()

    # Act
    prices = [
        minimalist.evaluate(code).price_paid,
        documenter.evaluate(code).price_paid,
        tester.evaluate(code).price_paid,
        pragmatic.evaluate(code).price_paid
    ]

    # Assert - All prices should be different
    assert len(set(prices)) == 4, f"Expected 4 unique prices, got: {prices}"


def test_evaluation_deterministic():
    """
    Acceptance criteria: Evaluation is deterministic (same code → same price)
    """
    # Arrange
    client = MinimalistClient()
    code = "def hello(): return 'world'"

    # Act - Evaluate same code 3 times
    result1 = client.evaluate(code)
    result2 = client.evaluate(code)
    result3 = client.evaluate(code)

    # Assert - All results should be identical
    assert result1.price_paid == result2.price_paid == result3.price_paid
    assert result1.feedback == result2.feedback == result3.feedback
    assert result1.client_name == result2.client_name == result3.client_name


def test_evaluation_result_structure():
    """
    Test that EvaluationResult has correct structure
    """
    # Arrange & Act
    result = EvaluationResult("TestClient", 15.5, "Great code")

    # Assert
    assert result.client_name == "TestClient"
    assert result.price_paid == 15.5
    assert result.feedback == "Great code"
    assert hasattr(result, 'client_name')
    assert hasattr(result, 'price_paid')
    assert hasattr(result, 'feedback')
