#!/usr/bin/env python3
"""Tasks designed to be hard enough that the initial agent fails some."""
import json, os, sys
from pathlib import Path

TASKS_DIR = Path(__file__).parent.parent / "data" / "dgm_tasks"

tasks = [
    {
        "id": "mini_interpreter",
        "description": "Implement an interpreter for a mini language. Supports: variable assignment (x = 5), arithmetic (+,-,*,/,%), if/else blocks, while loops, print statements, and nested scopes. Execute a program string, return list of printed outputs.",
        "initial_code": 'def interpret(program):\n    """Execute mini-language program. Return list of print outputs."""\n    pass\n',
        "test_code": '''import pytest
from solution import interpret

def test_assignment_and_print():
    assert interpret("x = 5\\nprint x") == ["5"]

def test_arithmetic():
    assert interpret("x = 3 + 4 * 2\\nprint x") == ["11"]

def test_variables():
    assert interpret("x = 10\\ny = x + 5\\nprint y") == ["15"]

def test_if_true():
    assert interpret("x = 10\\nif x > 5\\n  print x\\nend") == ["10"]

def test_if_false():
    assert interpret("x = 3\\nif x > 5\\n  print x\\nend") == []

def test_if_else():
    assert interpret("x = 3\\nif x > 5\\n  print 1\\nelse\\n  print 0\\nend") == ["0"]

def test_while():
    assert interpret("x = 0\\nwhile x < 3\\n  x = x + 1\\nend\\nprint x") == ["3"]

def test_nested_while():
    prog = "sum = 0\\ni = 1\\nwhile i <= 3\\n  j = 1\\n  while j <= 3\\n    sum = sum + 1\\n    j = j + 1\\n  end\\n  i = i + 1\\nend\\nprint sum"
    assert interpret(prog) == ["9"]

def test_multiple_prints():
    assert interpret("print 1\\nprint 2\\nprint 3") == ["1", "2", "3"]

def test_modulo():
    assert interpret("x = 17 % 5\\nprint x") == ["2"]

def test_comparison_in_if():
    assert interpret("x = 5\\nif x == 5\\n  print yes\\nend") == ["yes"]

def test_string_print():
    assert interpret("print hello world") == ["hello world"]
''',
    },
    {
        "id": "constraint_solver",
        "description": "Implement a simple constraint satisfaction solver. Given variables with domains and binary constraints, find all solutions using backtracking with forward checking. Variables are strings, domains are lists of values, constraints are functions.",
        "initial_code": '''def solve_csp(variables, domains, constraints):
    """
    Solve a CSP problem.
    variables: list of variable names
    domains: dict {var: [possible values]}
    constraints: list of (var1, var2, func) where func(val1, val2) -> bool
    Returns: list of solutions, each solution is dict {var: value}
    """
    pass
''',
        "test_code": '''import pytest
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
''',
    },
    {
        "id": "diff_engine",
        "description": "Implement a unified diff engine. Given two strings (old and new), compute the minimal edit script using the Myers diff algorithm or similar. Output unified diff format lines: unchanged lines prefixed with ' ', removed with '-', added with '+'.",
        "initial_code": '''def unified_diff(old_text, new_text):
    """
    Compute unified diff between old and new text.
    Returns list of strings: ' line' (unchanged), '-line' (removed), '+line' (added).
    """
    pass
''',
        "test_code": '''import pytest
from solution import unified_diff

def test_identical():
    assert unified_diff("a\\nb\\nc", "a\\nb\\nc") == [" a", " b", " c"]

def test_add_line():
    result = unified_diff("a\\nc", "a\\nb\\nc")
    assert result == [" a", "+b", " c"]

def test_remove_line():
    result = unified_diff("a\\nb\\nc", "a\\nc")
    assert result == [" a", "-b", " c"]

def test_modify_line():
    result = unified_diff("a\\nb\\nc", "a\\nB\\nc")
    assert result == [" a", "-b", "+B", " c"]

def test_empty_to_content():
    result = unified_diff("", "a\\nb")
    assert result == ["+a", "+b"]

def test_content_to_empty():
    result = unified_diff("a\\nb", "")
    assert result == ["-a", "-b"]

def test_both_empty():
    assert unified_diff("", "") == []

def test_complete_rewrite():
    result = unified_diff("a\\nb", "c\\nd")
    assert "-a" in result and "-b" in result
    assert "+c" in result and "+d" in result

def test_add_at_end():
    result = unified_diff("a", "a\\nb")
    assert result == [" a", "+b"]

def test_longer_example():
    old = "the\\nquick\\nbrown\\nfox"
    new = "the\\nslow\\nbrown\\ndog"
    result = unified_diff(old, new)
    assert " the" in result
    assert "-quick" in result
    assert "+slow" in result
    assert " brown" in result
    assert "-fox" in result
    assert "+dog" in result
''',
    },
    {
        "id": "promise_chain",
        "description": "Implement a Promise class (like JavaScript Promises) with then, catch, and resolve/reject. Supports chaining, error propagation, and async-style resolution. All synchronous (no actual async).",
        "initial_code": '''class Promise:
    def __init__(self, executor):
        """executor is a function(resolve, reject)"""
        pass

    def then(self, on_fulfilled=None, on_rejected=None):
        """Return new Promise. Chain callbacks."""
        pass

    def catch(self, on_rejected):
        """Shorthand for then(None, on_rejected)."""
        pass

    @staticmethod
    def resolve(value):
        """Return a resolved Promise."""
        pass

    @staticmethod
    def reject(reason):
        """Return a rejected Promise."""
        pass
''',
        "test_code": '''import pytest
from solution import Promise

def test_resolve():
    result = []
    p = Promise(lambda resolve, reject: resolve(42))
    p.then(lambda v: result.append(v))
    assert result == [42]

def test_reject():
    result = []
    p = Promise(lambda resolve, reject: reject("error"))
    p.catch(lambda e: result.append(e))
    assert result == ["error"]

def test_chain():
    result = []
    p = Promise(lambda resolve, reject: resolve(1))
    p.then(lambda v: v + 1).then(lambda v: result.append(v))
    assert result == [2]

def test_long_chain():
    result = []
    p = Promise(lambda resolve, reject: resolve(0))
    p.then(lambda v: v + 1).then(lambda v: v * 2).then(lambda v: v + 3).then(lambda v: result.append(v))
    assert result == [5]

def test_error_propagation():
    result = []
    p = Promise(lambda resolve, reject: reject("fail"))
    p.then(lambda v: v + 1).then(lambda v: v + 2).catch(lambda e: result.append(e))
    assert result == ["fail"]

def test_catch_and_continue():
    result = []
    p = Promise(lambda resolve, reject: reject("err"))
    p.catch(lambda e: 99).then(lambda v: result.append(v))
    assert result == [99]

def test_then_raises():
    result = []
    def bad(v):
        raise ValueError("boom")
    p = Promise(lambda resolve, reject: resolve(1))
    p.then(bad).catch(lambda e: result.append(str(e)))
    assert result == ["boom"]

def test_static_resolve():
    result = []
    Promise.resolve(10).then(lambda v: result.append(v))
    assert result == [10]

def test_static_reject():
    result = []
    Promise.reject("no").catch(lambda e: result.append(e))
    assert result == ["no"]

def test_then_returns_promise():
    result = []
    p = Promise.resolve(1)
    p2 = p.then(lambda v: Promise.resolve(v + 10))
    p2.then(lambda v: result.append(v))
    assert result == [11]
''',
    },
]

TASKS_DIR.mkdir(parents=True, exist_ok=True)
for task in tasks:
    task_dir = TASKS_DIR / task["id"]
    task_dir.mkdir(parents=True, exist_ok=True)
    meta = {"id": task["id"], "description": task["description"],
            "code_file": "solution.py", "test_file": "test_solution.py"}
    (task_dir / "task.json").write_text(json.dumps(meta, indent=2))
    (task_dir / "solution.py").write_text(task["initial_code"])
    (task_dir / "test_solution.py").write_text(task["test_code"])
print(f"Created {len(tasks)} brutal tasks")
