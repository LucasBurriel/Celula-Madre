import pytest
from solution import calculate

def test_addition():
    assert calculate("2 + 3") == 5.0

def test_subtraction():
    assert calculate("10 - 4") == 6.0

def test_multiplication():
    assert calculate("3 * 4") == 12.0

def test_division():
    assert calculate("15 / 3") == 5.0

def test_precedence():
    assert calculate("2 + 3 * 4") == 14.0

def test_parentheses():
    assert calculate("(2 + 3) * 4") == 20.0

def test_nested_parens():
    assert calculate("((2 + 3) * (4 - 1))") == 15.0

def test_complex():
    assert abs(calculate("3.5 * 2 + 1") - 8.0) < 1e-9

def test_negative_result():
    assert calculate("3 - 10") == -7.0
