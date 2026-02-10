"""
Simple coding benchmark for DGM validation.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

TASKS_DIR = Path(__file__).parent.parent.parent / "data" / "dgm_tasks"


def get_task_ids():
    if not TASKS_DIR.exists():
        return []
    return sorted([d.name for d in TASKS_DIR.iterdir() if d.is_dir()])


def load_task(task_id):
    task_dir = TASKS_DIR / task_id
    task_json = task_dir / "task.json"
    if not task_json.exists():
        raise ValueError(f"Task {task_id} not found")

    with open(task_json) as f:
        task = json.load(f)

    test_file = task_dir / task.get("test_file", "test_solution.py")
    if test_file.exists():
        task["test_content"] = test_file.read_text()

    code_file = task_dir / task.get("code_file", "solution.py")
    if code_file.exists():
        task["initial_code"] = code_file.read_text()

    task["task_dir"] = str(task_dir)
    return task


def setup_task_workspace(task, workspace_dir):
    task_dir = Path(task["task_dir"])
    workspace_dir = Path(workspace_dir)
    workspace_dir.mkdir(parents=True, exist_ok=True)

    for f in task_dir.iterdir():
        if f.name != "task.json":
            shutil.copy2(f, workspace_dir / f.name)

    subprocess.run(["git", "init"], cwd=workspace_dir, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=workspace_dir, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.name=dgm", "-c", "user.email=dgm@test",
         "commit", "-m", "initial"],
        cwd=workspace_dir, capture_output=True
    )
    return workspace_dir


def evaluate_task(workspace_dir, task, timeout=60):
    test_file = task.get("test_file", "test_solution.py")
    try:
        result = subprocess.run(
            ["python3", "-m", "pytest", test_file, "-v", "--tb=short"],
            cwd=workspace_dir, capture_output=True, text=True, timeout=timeout,
        )
        output = result.stdout + result.stderr
        passed = 0
        failed = 0
        for line in output.split("\n"):
            m = re.search(r"(\d+) passed", line)
            if m:
                passed = int(m.group(1))
            m = re.search(r"(\d+) failed", line)
            if m:
                failed = int(m.group(1))

        total = passed + failed
        score = passed / total if total > 0 else 0.0
        return {
            "passed": passed, "failed": failed, "total": total,
            "score": score, "output": output[:5000], "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"passed": 0, "failed": 0, "total": 0, "score": 0.0, "output": "TIMEOUT", "returncode": -1}
    except Exception as e:
        return {"passed": 0, "failed": 0, "total": 0, "score": 0.0, "output": str(e), "returncode": -1}


def create_sample_tasks():
    """Create sample benchmark tasks."""
    TASKS_DIR.mkdir(parents=True, exist_ok=True)

    tasks = [
        {
            "id": "fizzbuzz",
            "description": "Implement the FizzBuzz function. For numbers 1 to n: return 'Fizz' for multiples of 3, 'Buzz' for multiples of 5, 'FizzBuzz' for multiples of both, and the number as string otherwise. Return a list.",
            "initial_code": 'def fizzbuzz(n):\n    """Return list of FizzBuzz results from 1 to n."""\n    pass\n',
            "test_code": '''import pytest
from solution import fizzbuzz

def test_fizzbuzz_basic():
    result = fizzbuzz(15)
    assert result[0] == "1"
    assert result[2] == "Fizz"
    assert result[4] == "Buzz"
    assert result[14] == "FizzBuzz"

def test_fizzbuzz_length():
    assert len(fizzbuzz(20)) == 20

def test_fizzbuzz_multiples_of_3():
    result = fizzbuzz(15)
    for i in [2, 5, 8, 11]:
        assert result[i] == "Fizz" or result[i] == "FizzBuzz"

def test_fizzbuzz_multiples_of_5():
    result = fizzbuzz(15)
    assert result[4] == "Buzz"
    assert result[9] == "Buzz"

def test_fizzbuzz_one():
    assert fizzbuzz(1) == ["1"]
''',
        },
        {
            "id": "matrix_rotate",
            "description": "Implement a function to rotate a square matrix 90 degrees clockwise in-place. Return the matrix.",
            "initial_code": 'def rotate_matrix(matrix):\n    """Rotate NxN matrix 90 degrees clockwise in-place. Return the matrix."""\n    pass\n',
            "test_code": '''import pytest
from solution import rotate_matrix

def test_2x2():
    m = [[1,2],[3,4]]
    assert rotate_matrix(m) == [[3,1],[4,2]]

def test_3x3():
    m = [[1,2,3],[4,5,6],[7,8,9]]
    assert rotate_matrix(m) == [[7,4,1],[8,5,2],[9,6,3]]

def test_1x1():
    assert rotate_matrix([[1]]) == [[1]]

def test_4x4():
    m = [[1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16]]
    expected = [[13,9,5,1],[14,10,6,2],[15,11,7,3],[16,12,8,4]]
    assert rotate_matrix(m) == expected

def test_in_place():
    m = [[1,2],[3,4]]
    result = rotate_matrix(m)
    assert result is m
''',
        },
        {
            "id": "linked_list",
            "description": "Implement a singly linked list with append, prepend, delete (first occurrence, return bool), find (return bool), and to_list methods.",
            "initial_code": '''class Node:
    def __init__(self, val, next=None):
        self.val = val
        self.next = next

class LinkedList:
    def __init__(self):
        self.head = None

    def append(self, val):
        pass

    def prepend(self, val):
        pass

    def delete(self, val):
        pass

    def find(self, val):
        pass

    def to_list(self):
        pass
''',
            "test_code": '''import pytest
from solution import LinkedList

def test_append():
    ll = LinkedList()
    ll.append(1); ll.append(2); ll.append(3)
    assert ll.to_list() == [1, 2, 3]

def test_prepend():
    ll = LinkedList()
    ll.prepend(3); ll.prepend(2); ll.prepend(1)
    assert ll.to_list() == [1, 2, 3]

def test_delete():
    ll = LinkedList()
    ll.append(1); ll.append(2); ll.append(3)
    assert ll.delete(2) == True
    assert ll.to_list() == [1, 3]

def test_delete_head():
    ll = LinkedList()
    ll.append(1); ll.append(2)
    assert ll.delete(1) == True
    assert ll.to_list() == [2]

def test_delete_not_found():
    ll = LinkedList()
    ll.append(1)
    assert ll.delete(5) == False

def test_find():
    ll = LinkedList()
    ll.append(1); ll.append(2)
    assert ll.find(2) == True
    assert ll.find(5) == False

def test_empty():
    ll = LinkedList()
    assert ll.to_list() == []
    assert ll.find(1) == False
    assert ll.delete(1) == False
''',
        },
        {
            "id": "lru_cache",
            "description": "Implement an LRU (Least Recently Used) cache with get(key)->value/-1 and put(key,value) operations. Evict least recently used when at capacity.",
            "initial_code": '''class LRUCache:
    def __init__(self, capacity):
        pass

    def get(self, key):
        pass

    def put(self, key, value):
        pass
''',
            "test_code": '''import pytest
from solution import LRUCache

def test_basic():
    cache = LRUCache(2)
    cache.put(1, 1); cache.put(2, 2)
    assert cache.get(1) == 1
    cache.put(3, 3)
    assert cache.get(2) == -1

def test_update():
    cache = LRUCache(2)
    cache.put(1, 1); cache.put(2, 2); cache.put(1, 10)
    assert cache.get(1) == 10

def test_eviction_order():
    cache = LRUCache(2)
    cache.put(1, 1); cache.put(2, 2)
    cache.get(1)
    cache.put(3, 3)
    assert cache.get(2) == -1
    assert cache.get(1) == 1

def test_capacity_one():
    cache = LRUCache(1)
    cache.put(1, 1); cache.put(2, 2)
    assert cache.get(1) == -1
    assert cache.get(2) == 2

def test_miss():
    cache = LRUCache(3)
    assert cache.get(99) == -1

def test_many_ops():
    cache = LRUCache(3)
    for i in range(10):
        cache.put(i, i * 10)
    assert cache.get(7) == 70
    assert cache.get(8) == 80
    assert cache.get(9) == 90
    assert cache.get(6) == -1
''',
        },
        {
            "id": "calculator",
            "description": "Implement a calculator that evaluates math expressions with +, -, *, / and parentheses. Follow operator precedence. Return float.",
            "initial_code": 'def calculate(expression):\n    """Evaluate a mathematical expression string. Return float."""\n    pass\n',
            "test_code": '''import pytest
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

    print(f"Created {len(tasks)} tasks in {TASKS_DIR}")
    return [t["id"] for t in tasks]


if __name__ == "__main__":
    create_sample_tasks()
