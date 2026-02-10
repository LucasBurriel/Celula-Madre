"""
Coding tasks for DGM evaluation.
Simple Python tasks with test suites — like a mini HumanEval.
"""

from dgm_core import Task


def get_tasks() -> list[Task]:
    """Return a list of coding tasks for evaluation."""
    tasks = []
    
    # ── Task 1: Two Sum ──
    tasks.append(Task(
        task_id="two_sum",
        description="""Write a function `two_sum(nums, target)` that returns the indices of two numbers 
in `nums` that add up to `target`. Each input has exactly one solution.
You may not use the same element twice. Return the indices as a list [i, j] where i < j.""",
        initial_code="def two_sum(nums, target):\n    pass\n",
        test_code="""
from solution import two_sum

def test_basic():
    assert two_sum([2, 7, 11, 15], 9) == [0, 1]

def test_middle():
    assert two_sum([3, 2, 4], 6) == [1, 2]

def test_negative():
    assert two_sum([-1, -2, -3, -4, -5], -8) == [2, 4]

def test_large():
    nums = list(range(1000))
    assert two_sum(nums, 1997) == [998, 999]
""",
    ))
    
    # ── Task 2: Valid Parentheses ──
    tasks.append(Task(
        task_id="valid_parens",
        description="""Write a function `is_valid(s)` that takes a string containing just the characters 
'(', ')', '{', '}', '[' and ']', and determines if the input string is valid.
A string is valid if: open brackets are closed by the same type, and in the correct order.""",
        initial_code="def is_valid(s):\n    pass\n",
        test_code="""
from solution import is_valid

def test_simple():
    assert is_valid("()") == True

def test_multiple():
    assert is_valid("()[]{}") == True

def test_nested():
    assert is_valid("{[()]}") == True

def test_invalid():
    assert is_valid("(]") == False

def test_incomplete():
    assert is_valid("([)") == False

def test_empty():
    assert is_valid("") == True
""",
    ))
    
    # ── Task 3: Flatten Nested List ──
    tasks.append(Task(
        task_id="flatten",
        description="""Write a function `flatten(lst)` that takes an arbitrarily nested list of integers 
and returns a flat list of all integers in order.""",
        initial_code="def flatten(lst):\n    pass\n",
        test_code="""
from solution import flatten

def test_simple():
    assert flatten([1, [2, 3], [4, [5, 6]]]) == [1, 2, 3, 4, 5, 6]

def test_deep():
    assert flatten([[[1]], [[2]], [[3]]]) == [1, 2, 3]

def test_empty():
    assert flatten([]) == []

def test_flat():
    assert flatten([1, 2, 3]) == [1, 2, 3]

def test_mixed():
    assert flatten([1, [2, [3, [4, [5]]]]]) == [1, 2, 3, 4, 5]
""",
    ))
    
    # ── Task 4: Caesar Cipher ──
    tasks.append(Task(
        task_id="caesar",
        description="""Write a function `caesar(text, shift)` that applies a Caesar cipher to the text.
Only shift alphabetic characters. Preserve case. Wrap around (z+1=a).
Shift can be negative for decryption.""",
        initial_code="def caesar(text, shift):\n    pass\n",
        test_code="""
from solution import caesar

def test_basic():
    assert caesar("abc", 1) == "bcd"

def test_wrap():
    assert caesar("xyz", 3) == "abc"

def test_preserve_case():
    assert caesar("Hello", 13) == "Uryyb"

def test_non_alpha():
    assert caesar("Hello, World!", 5) == "Mjqqt, Btwqi!"

def test_negative():
    assert caesar("bcd", -1) == "abc"

def test_full_rotation():
    assert caesar("abc", 26) == "abc"
""",
    ))
    
    # ── Task 5: Matrix Transpose ──
    tasks.append(Task(
        task_id="transpose",
        description="""Write a function `transpose(matrix)` that returns the transpose of a 2D matrix.
The matrix is a list of lists. Rows become columns and vice versa.""",
        initial_code="def transpose(matrix):\n    pass\n",
        test_code="""
from solution import transpose

def test_square():
    assert transpose([[1, 2], [3, 4]]) == [[1, 3], [2, 4]]

def test_rectangular():
    assert transpose([[1, 2, 3], [4, 5, 6]]) == [[1, 4], [2, 5], [3, 6]]

def test_single_row():
    assert transpose([[1, 2, 3]]) == [[1], [2], [3]]

def test_single_col():
    assert transpose([[1], [2], [3]]) == [[1, 2, 3]]
""",
    ))
    
    # ── Task 6: Run Length Encoding ──
    tasks.append(Task(
        task_id="rle",
        description="""Write a function `rle_encode(s)` that performs run-length encoding on a string.
Consecutive identical characters are replaced by the character followed by the count.
If count is 1, don't include the number. Example: "aaabbc" -> "a3b2c" """,
        initial_code="def rle_encode(s):\n    pass\n",
        test_code="""
from solution import rle_encode

def test_basic():
    assert rle_encode("aaabbc") == "a3b2c"

def test_no_repeat():
    assert rle_encode("abc") == "abc"

def test_all_same():
    assert rle_encode("aaaa") == "a4"

def test_single():
    assert rle_encode("a") == "a"

def test_empty():
    assert rle_encode("") == ""

def test_mixed():
    assert rle_encode("aabbbccddddde") == "a2b3c2d5e"
""",
    ))
    
    # ── Task 7: Binary Search ──
    tasks.append(Task(
        task_id="binary_search",
        description="""Write a function `binary_search(arr, target)` that returns the index of target 
in a sorted array, or -1 if not found. Must use binary search (O(log n)).""",
        initial_code="def binary_search(arr, target):\n    pass\n",
        test_code="""
from solution import binary_search

def test_found():
    assert binary_search([1, 3, 5, 7, 9], 5) == 2

def test_first():
    assert binary_search([1, 3, 5, 7, 9], 1) == 0

def test_last():
    assert binary_search([1, 3, 5, 7, 9], 9) == 4

def test_not_found():
    assert binary_search([1, 3, 5, 7, 9], 4) == -1

def test_empty():
    assert binary_search([], 5) == -1

def test_single():
    assert binary_search([5], 5) == 0
""",
    ))
    
    # ── Task 8: Merge Sorted Lists ──
    tasks.append(Task(
        task_id="merge_sorted",
        description="""Write a function `merge_sorted(list1, list2)` that merges two sorted lists 
into one sorted list. Do not use built-in sort.""",
        initial_code="def merge_sorted(list1, list2):\n    pass\n",
        test_code="""
from solution import merge_sorted

def test_basic():
    assert merge_sorted([1, 3, 5], [2, 4, 6]) == [1, 2, 3, 4, 5, 6]

def test_empty_first():
    assert merge_sorted([], [1, 2, 3]) == [1, 2, 3]

def test_empty_second():
    assert merge_sorted([1, 2, 3], []) == [1, 2, 3]

def test_duplicates():
    assert merge_sorted([1, 2, 2], [2, 3, 3]) == [1, 2, 2, 2, 3, 3]

def test_single():
    assert merge_sorted([1], [2]) == [1, 2]
""",
    ))
    
    # ── Task 9: Spiral Matrix ──
    tasks.append(Task(
        task_id="spiral",
        description="""Write a function `spiral_order(matrix)` that returns all elements of a 2D matrix 
in spiral order (clockwise, starting from top-left).""",
        initial_code="def spiral_order(matrix):\n    pass\n",
        test_code="""
from solution import spiral_order

def test_3x3():
    assert spiral_order([[1,2,3],[4,5,6],[7,8,9]]) == [1,2,3,6,9,8,7,4,5]

def test_3x4():
    assert spiral_order([[1,2,3,4],[5,6,7,8],[9,10,11,12]]) == [1,2,3,4,8,12,11,10,9,5,6,7]

def test_1x1():
    assert spiral_order([[1]]) == [1]

def test_1_row():
    assert spiral_order([[1,2,3]]) == [1,2,3]

def test_1_col():
    assert spiral_order([[1],[2],[3]]) == [1,2,3]
""",
    ))
    
    # ── Task 10: LRU Cache ──
    tasks.append(Task(
        task_id="lru_cache",
        description="""Implement a class `LRUCache` with:
- `__init__(self, capacity)`: Initialize with positive capacity
- `get(self, key)`: Return the value if key exists, else -1
- `put(self, key, value)`: Insert or update. If capacity exceeded, evict least recently used.
Both get and put must run in O(1) average time.""",
        initial_code="""class LRUCache:
    def __init__(self, capacity):
        pass
    
    def get(self, key):
        pass
    
    def put(self, key, value):
        pass
""",
        test_code="""
from solution import LRUCache

def test_basic():
    cache = LRUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    assert cache.get(1) == 1
    cache.put(3, 3)  # evicts key 2
    assert cache.get(2) == -1
    cache.put(4, 4)  # evicts key 1
    assert cache.get(1) == -1
    assert cache.get(3) == 3
    assert cache.get(4) == 4

def test_update():
    cache = LRUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    cache.put(1, 10)  # update
    assert cache.get(1) == 10
    cache.put(3, 3)  # evicts key 2 (1 was recently used)
    assert cache.get(2) == -1

def test_get_refreshes():
    cache = LRUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    cache.get(1)  # refreshes key 1
    cache.put(3, 3)  # evicts key 2
    assert cache.get(1) == 1
    assert cache.get(2) == -1
""",
    ))
    
    return tasks


if __name__ == "__main__":
    tasks = get_tasks()
    print(f"Loaded {len(tasks)} tasks:")
    for t in tasks:
        print(f"  - {t.task_id}: {t.description[:60]}...")
