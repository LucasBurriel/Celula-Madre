import pytest
from solution import interpret

def test_assignment_and_print():
    assert interpret("x = 5\nprint x") == ["5"]

def test_arithmetic():
    assert interpret("x = 3 + 4 * 2\nprint x") == ["11"]

def test_variables():
    assert interpret("x = 10\ny = x + 5\nprint y") == ["15"]

def test_if_true():
    assert interpret("x = 10\nif x > 5\n  print x\nend") == ["10"]

def test_if_false():
    assert interpret("x = 3\nif x > 5\n  print x\nend") == []

def test_if_else():
    assert interpret("x = 3\nif x > 5\n  print 1\nelse\n  print 0\nend") == ["0"]

def test_while():
    assert interpret("x = 0\nwhile x < 3\n  x = x + 1\nend\nprint x") == ["3"]

def test_nested_while():
    prog = "sum = 0\ni = 1\nwhile i <= 3\n  j = 1\n  while j <= 3\n    sum = sum + 1\n    j = j + 1\n  end\n  i = i + 1\nend\nprint sum"
    assert interpret(prog) == ["9"]

def test_multiple_prints():
    assert interpret("print 1\nprint 2\nprint 3") == ["1", "2", "3"]

def test_modulo():
    assert interpret("x = 17 % 5\nprint x") == ["2"]

def test_comparison_in_if():
    assert interpret("x = 5\nif x == 5\n  print yes\nend") == ["yes"]

def test_string_print():
    assert interpret("print hello world") == ["hello world"]
