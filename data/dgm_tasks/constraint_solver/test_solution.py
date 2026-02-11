import pytest
from solution import solve_csp

def test_simple():
    variables = ["A", "B"]
    domains = {"A": [1, 2], "B": [1, 2]}
    constraints = [("A", "B", lambda a, b: a != b)]
    solutions = solve_csp(variables, domains, constraints)
    assert len(solutions) == 2
    assert {"A": 1, "B": 2} in solutions
    assert {"A": 2, "B": 1} in solutions

def test_three_vars():
    variables = ["A", "B", "C"]
    domains = {"A": [1, 2, 3], "B": [1, 2, 3], "C": [1, 2, 3]}
    constraints = [
        ("A", "B", lambda a, b: a != b),
        ("B", "C", lambda b, c: b != c),
        ("A", "C", lambda a, c: a != c),
    ]
    solutions = solve_csp(variables, domains, constraints)
    assert len(solutions) == 6  # 3! permutations

def test_no_solution():
    variables = ["A", "B"]
    domains = {"A": [1], "B": [1]}
    constraints = [("A", "B", lambda a, b: a != b)]
    assert solve_csp(variables, domains, constraints) == []

def test_ordering_constraint():
    variables = ["X", "Y", "Z"]
    domains = {"X": [1, 2, 3], "Y": [1, 2, 3], "Z": [1, 2, 3]}
    constraints = [
        ("X", "Y", lambda x, y: x < y),
        ("Y", "Z", lambda y, z: y < z),
    ]
    solutions = solve_csp(variables, domains, constraints)
    assert len(solutions) == 1
    assert solutions[0] == {"X": 1, "Y": 2, "Z": 3}

def test_single_variable():
    solutions = solve_csp(["A"], {"A": [1, 2, 3]}, [])
    assert len(solutions) == 3

def test_empty():
    assert solve_csp([], {}, []) == [{}]

def test_four_coloring():
    variables = ["WA", "NT", "SA", "Q", "NSW", "V"]
    domains = {v: ["R", "G", "B"] for v in variables}
    constraints = [
        ("WA", "NT", lambda a, b: a != b),
        ("WA", "SA", lambda a, b: a != b),
        ("NT", "SA", lambda a, b: a != b),
        ("NT", "Q", lambda a, b: a != b),
        ("SA", "Q", lambda a, b: a != b),
        ("SA", "NSW", lambda a, b: a != b),
        ("SA", "V", lambda a, b: a != b),
        ("Q", "NSW", lambda a, b: a != b),
        ("NSW", "V", lambda a, b: a != b),
    ]
    solutions = solve_csp(variables, domains, constraints)
    assert len(solutions) == 18  # Australia map coloring with 3 colors
