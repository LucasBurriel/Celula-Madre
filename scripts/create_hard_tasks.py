#!/usr/bin/env python3
"""Create harder benchmark tasks that the initial agent might fail on."""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path

TASKS_DIR = Path(__file__).parent.parent / "data" / "dgm_tasks"

tasks = [
    {
        "id": "regex_engine",
        "description": "Implement a simple regex engine that supports: literal chars, '.' (any char), '*' (zero or more of previous), '+' (one or more of previous), '?' (zero or one of previous), and character classes [abc]. The match function should check if the FULL string matches the pattern.",
        "initial_code": 'def match(pattern, text):\n    """Return True if text fully matches pattern."""\n    pass\n',
        "test_code": '''import pytest
from solution import match

def test_literal():
    assert match("abc", "abc") == True
    assert match("abc", "abd") == False

def test_dot():
    assert match("a.c", "abc") == True
    assert match("a.c", "adc") == True
    assert match("a.c", "ac") == False

def test_star():
    assert match("ab*c", "ac") == True
    assert match("ab*c", "abc") == True
    assert match("ab*c", "abbc") == True
    assert match("ab*c", "abbbc") == True

def test_plus():
    assert match("ab+c", "ac") == False
    assert match("ab+c", "abc") == True
    assert match("ab+c", "abbc") == True

def test_question():
    assert match("ab?c", "ac") == True
    assert match("ab?c", "abc") == True
    assert match("ab?c", "abbc") == False

def test_char_class():
    assert match("[abc]d", "ad") == True
    assert match("[abc]d", "bd") == True
    assert match("[abc]d", "dd") == False

def test_complex():
    assert match("a.*b", "ab") == True
    assert match("a.*b", "axxb") == True
    assert match("a.*b", "axxc") == False

def test_dot_star():
    assert match(".*", "") == True
    assert match(".*", "anything") == True

def test_empty():
    assert match("", "") == True
    assert match("", "a") == False
''',
    },
    {
        "id": "json_parser",
        "description": "Implement a JSON parser from scratch (no json module). Support: strings (with escape sequences \\n \\t \\\\ \\\"), numbers (int and float), booleans (true/false), null, arrays, and nested objects. Return Python equivalents.",
        "initial_code": 'def parse_json(text):\n    """Parse a JSON string and return Python object."""\n    pass\n',
        "test_code": '''import pytest
from solution import parse_json

def test_string():
    assert parse_json('"hello"') == "hello"

def test_number_int():
    assert parse_json('42') == 42

def test_number_float():
    assert parse_json('3.14') == 3.14

def test_negative():
    assert parse_json('-5') == -5

def test_bool():
    assert parse_json('true') == True
    assert parse_json('false') == False

def test_null():
    assert parse_json('null') is None

def test_array():
    assert parse_json('[1, 2, 3]') == [1, 2, 3]

def test_nested_array():
    assert parse_json('[[1, 2], [3, 4]]') == [[1, 2], [3, 4]]

def test_object():
    assert parse_json('{"a": 1, "b": 2}') == {"a": 1, "b": 2}

def test_nested():
    result = parse_json('{"name": "test", "values": [1, true, null]}')
    assert result == {"name": "test", "values": [1, True, None]}

def test_escape():
    assert parse_json('"hello\\\\nworld"') == "hello\\nworld"

def test_empty_structures():
    assert parse_json('[]') == []
    assert parse_json('{}') == {}

def test_whitespace():
    assert parse_json('  { "a" : 1 }  ') == {"a": 1}
''',
    },
    {
        "id": "graph_shortest",
        "description": "Implement Dijkstra's shortest path algorithm. Given a weighted directed graph as adjacency list {node: [(neighbor, weight), ...]}, find shortest distances from a source node to all other nodes. Return dict {node: distance}. Unreachable nodes should have distance float('inf').",
        "initial_code": 'def dijkstra(graph, source):\n    """Return dict of shortest distances from source to all nodes."""\n    pass\n',
        "test_code": '''import pytest
from solution import dijkstra

def test_simple():
    g = {'A': [('B', 1), ('C', 4)], 'B': [('C', 2)], 'C': []}
    d = dijkstra(g, 'A')
    assert d['A'] == 0
    assert d['B'] == 1
    assert d['C'] == 3

def test_unreachable():
    g = {'A': [('B', 1)], 'B': [], 'C': [('A', 1)]}
    d = dijkstra(g, 'A')
    assert d['C'] == float('inf')

def test_single_node():
    g = {'A': []}
    d = dijkstra(g, 'A')
    assert d == {'A': 0}

def test_cycle():
    g = {'A': [('B', 1)], 'B': [('C', 2)], 'C': [('A', 10)]}
    d = dijkstra(g, 'A')
    assert d['A'] == 0
    assert d['B'] == 1
    assert d['C'] == 3

def test_multiple_paths():
    g = {
        'A': [('B', 10), ('C', 3)],
        'B': [('D', 2)],
        'C': [('B', 1), ('D', 8)],
        'D': []
    }
    d = dijkstra(g, 'A')
    assert d['B'] == 4  # A->C->B
    assert d['D'] == 6  # A->C->B->D

def test_all_nodes_in_result():
    g = {'A': [('B', 1)], 'B': [('C', 1)], 'C': [], 'D': []}
    d = dijkstra(g, 'A')
    assert set(d.keys()) == {'A', 'B', 'C', 'D'}
''',
    },
    {
        "id": "btree",
        "description": "Implement a self-balancing Binary Search Tree (AVL tree) with insert, search, delete, and in_order traversal. Each operation must maintain the AVL balance property.",
        "initial_code": '''class AVLTree:
    class Node:
        def __init__(self, key):
            self.key = key
            self.left = None
            self.right = None
            self.height = 1

    def __init__(self):
        self.root = None

    def insert(self, key):
        pass

    def search(self, key):
        """Return True if key exists."""
        pass

    def delete(self, key):
        pass

    def in_order(self):
        """Return sorted list of all keys."""
        pass

    def height(self):
        """Return tree height."""
        pass
''',
        "test_code": '''import pytest
from solution import AVLTree

def test_insert_and_search():
    t = AVLTree()
    t.insert(10); t.insert(20); t.insert(30)
    assert t.search(10) == True
    assert t.search(20) == True
    assert t.search(30) == True
    assert t.search(40) == False

def test_in_order():
    t = AVLTree()
    for v in [5, 3, 7, 1, 4, 6, 8]:
        t.insert(v)
    assert t.in_order() == [1, 3, 4, 5, 6, 7, 8]

def test_balance():
    t = AVLTree()
    # Insert in sorted order - should still be balanced
    for i in range(1, 16):
        t.insert(i)
    # AVL tree of 15 nodes should have height 4
    h = t.height()
    assert h <= 5, f"Tree not balanced: height {h} for 15 nodes"

def test_delete():
    t = AVLTree()
    for v in [5, 3, 7, 1, 4]:
        t.insert(v)
    t.delete(3)
    assert t.search(3) == False
    assert t.in_order() == [1, 4, 5, 7]

def test_delete_root():
    t = AVLTree()
    t.insert(5); t.insert(3); t.insert(7)
    t.delete(5)
    assert t.search(5) == False
    assert sorted(t.in_order()) == [3, 7]

def test_delete_nonexistent():
    t = AVLTree()
    t.insert(1)
    t.delete(99)  # should not crash
    assert t.in_order() == [1]

def test_duplicate_insert():
    t = AVLTree()
    t.insert(5); t.insert(5); t.insert(5)
    assert t.in_order() == [5]  # no duplicates

def test_empty():
    t = AVLTree()
    assert t.in_order() == []
    assert t.search(1) == False
''',
    },
    {
        "id": "task_scheduler",
        "description": "Implement a task scheduler. Given a list of tasks (chars) and a cooldown period n, find the minimum number of intervals needed to execute all tasks. Same tasks must be separated by at least n intervals. Idle intervals count. Tasks can be executed in any order.",
        "initial_code": 'def schedule_tasks(tasks, n):\n    """Return minimum intervals to complete all tasks with cooldown n."""\n    pass\n',
        "test_code": '''import pytest
from solution import schedule_tasks

def test_basic():
    assert schedule_tasks(["A","A","A","B","B","B"], 2) == 8

def test_no_cooldown():
    assert schedule_tasks(["A","A","A","B","B","B"], 0) == 6

def test_single_task():
    assert schedule_tasks(["A"], 2) == 1

def test_all_same():
    assert schedule_tasks(["A","A","A"], 2) == 7

def test_many_types():
    assert schedule_tasks(["A","B","C","A","B","C"], 2) == 6

def test_empty():
    assert schedule_tasks([], 2) == 0

def test_large_cooldown():
    assert schedule_tasks(["A","A","A","B","B","B"], 50) == 104

def test_single_type_many():
    assert schedule_tasks(["A","A","A","A"], 1) == 7
''',
    },
]

for task in tasks:
    task_dir = TASKS_DIR / task["id"]
    task_dir.mkdir(parents=True, exist_ok=True)
    
    meta = {"id": task["id"], "description": task["description"],
            "code_file": "solution.py", "test_file": "test_solution.py"}
    (task_dir / "task.json").write_text(json.dumps(meta, indent=2))
    (task_dir / "solution.py").write_text(task["initial_code"])
    (task_dir / "test_solution.py").write_text(task["test_code"])

print(f"Created {len(tasks)} hard tasks")
