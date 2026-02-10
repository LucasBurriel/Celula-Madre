"""
Harder coding tasks for DGM evaluation.
These should be challenging enough that a naive LLM prompt doesn't solve them all.
"""

from dgm_core import Task


def get_hard_tasks() -> list[Task]:
    """Return harder coding tasks."""
    tasks = []
    
    # ── Task 1: Regex Parser ──
    tasks.append(Task(
        task_id="regex_match",
        description="""Implement a function `regex_match(text, pattern)` that supports '.' (any single char) 
and '*' (zero or more of the preceding element). The matching should cover the ENTIRE input string.
Examples: regex_match("aa", "a") -> False, regex_match("aa", "a*") -> True, 
regex_match("ab", ".*") -> True, regex_match("aab", "c*a*b") -> True""",
        initial_code="def regex_match(text, pattern):\n    pass\n",
        test_code="""
from solution import regex_match

def test_exact():
    assert regex_match("abc", "abc") == True

def test_no_match():
    assert regex_match("aa", "a") == False

def test_star():
    assert regex_match("aa", "a*") == True

def test_dot_star():
    assert regex_match("ab", ".*") == True

def test_complex():
    assert regex_match("aab", "c*a*b") == True

def test_dot():
    assert regex_match("abc", "a.c") == True

def test_empty():
    assert regex_match("", "a*") == True

def test_star_complex():
    assert regex_match("mississippi", "mis*is*ip*.") == True

def test_false_star():
    assert regex_match("mississippi", "mis*is*p*.") == False

def test_nested():
    assert regex_match("aaa", "a*a") == True

def test_dot_star_prefix():
    assert regex_match("abcd", ".*d") == True
""",
    ))
    
    # ── Task 2: Longest Increasing Subsequence ──
    tasks.append(Task(
        task_id="lis",
        description="""Write a function `lis(nums)` that returns the LENGTH of the longest strictly 
increasing subsequence. Must be O(n log n) — O(n^2) solutions will TLE on the large test.""",
        initial_code="def lis(nums):\n    pass\n",
        test_code="""
from solution import lis
import time

def test_basic():
    assert lis([10, 9, 2, 5, 3, 7, 101, 18]) == 4

def test_all_inc():
    assert lis([1, 2, 3, 4, 5]) == 5

def test_all_dec():
    assert lis([5, 4, 3, 2, 1]) == 1

def test_single():
    assert lis([7]) == 1

def test_dups():
    assert lis([1, 3, 6, 7, 9, 4, 10, 5, 6]) == 6

def test_performance():
    import random
    random.seed(42)
    nums = [random.randint(0, 100000) for _ in range(50000)]
    start = time.time()
    result = lis(nums)
    elapsed = time.time() - start
    assert elapsed < 5.0, f"Too slow: {elapsed:.1f}s (must be <5s for n=50000)"
    assert result > 0
""",
    ))
    
    # ── Task 3: Serialize/Deserialize Binary Tree ──
    tasks.append(Task(
        task_id="tree_serde",
        description="""Implement two functions:
- `serialize(root)`: Encodes a binary tree to a string
- `deserialize(data)`: Decodes the string back to a tree

TreeNode class: 
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

The serialization format is up to you, but deserialize(serialize(tree)) must reproduce the original tree.""",
        initial_code="""class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def serialize(root):
    pass

def deserialize(data):
    pass
""",
        test_code="""
from solution import TreeNode, serialize, deserialize

def trees_equal(a, b):
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return a.val == b.val and trees_equal(a.left, b.left) and trees_equal(a.right, b.right)

def test_basic():
    root = TreeNode(1, TreeNode(2), TreeNode(3, TreeNode(4), TreeNode(5)))
    assert trees_equal(deserialize(serialize(root)), root)

def test_empty():
    assert deserialize(serialize(None)) is None

def test_single():
    root = TreeNode(42)
    result = deserialize(serialize(root))
    assert result.val == 42 and result.left is None and result.right is None

def test_left_skewed():
    root = TreeNode(1, TreeNode(2, TreeNode(3, TreeNode(4))))
    assert trees_equal(deserialize(serialize(root)), root)

def test_negative():
    root = TreeNode(-1, TreeNode(-2), TreeNode(-3))
    assert trees_equal(deserialize(serialize(root)), root)

def test_large():
    # Build a complete binary tree of depth 8
    def build(depth):
        if depth == 0:
            return None
        return TreeNode(depth, build(depth-1), build(depth-1))
    root = build(8)
    assert trees_equal(deserialize(serialize(root)), root)
""",
    ))
    
    # ── Task 4: Interval Merge with Queries ──
    tasks.append(Task(
        task_id="interval_merge",
        description="""Write a function `merge_intervals(intervals)` that merges overlapping intervals.
Input: list of [start, end] pairs. Output: merged non-overlapping intervals, sorted by start.
Also write `query_point(merged, point)` that returns True if the point is in any merged interval.""",
        initial_code="""def merge_intervals(intervals):
    pass

def query_point(merged, point):
    pass
""",
        test_code="""
from solution import merge_intervals, query_point

def test_merge_basic():
    assert merge_intervals([[1,3],[2,6],[8,10],[15,18]]) == [[1,6],[8,10],[15,18]]

def test_merge_overlap():
    assert merge_intervals([[1,4],[4,5]]) == [[1,5]]

def test_merge_single():
    assert merge_intervals([[1,2]]) == [[1,2]]

def test_merge_nested():
    assert merge_intervals([[1,10],[2,3],[4,5]]) == [[1,10]]

def test_merge_unsorted():
    assert merge_intervals([[3,4],[1,2],[5,6]]) == [[1,2],[3,4],[5,6]]

def test_query():
    merged = [[1,6],[8,10],[15,18]]
    assert query_point(merged, 5) == True
    assert query_point(merged, 7) == False
    assert query_point(merged, 8) == True
    assert query_point(merged, 20) == False

def test_query_edge():
    merged = [[1,5]]
    assert query_point(merged, 1) == True
    assert query_point(merged, 5) == True
    assert query_point(merged, 0) == False
""",
    ))
    
    # ── Task 5: Trie with Autocomplete ──
    tasks.append(Task(
        task_id="trie",
        description="""Implement a Trie (prefix tree) with autocomplete:
- `insert(word)`: Insert a word
- `search(word)`: Return True if word exists
- `starts_with(prefix)`: Return True if any word starts with prefix
- `autocomplete(prefix, limit=5)`: Return up to `limit` words that start with prefix, 
  sorted alphabetically""",
        initial_code="""class Trie:
    def __init__(self):
        pass
    
    def insert(self, word):
        pass
    
    def search(self, word):
        pass
    
    def starts_with(self, prefix):
        pass
    
    def autocomplete(self, prefix, limit=5):
        pass
""",
        test_code="""
from solution import Trie

def test_basic():
    t = Trie()
    t.insert("apple")
    assert t.search("apple") == True
    assert t.search("app") == False
    assert t.starts_with("app") == True

def test_autocomplete():
    t = Trie()
    for w in ["apple", "app", "application", "apply", "banana"]:
        t.insert(w)
    result = t.autocomplete("app")
    assert result == ["app", "apple", "application", "apply"]

def test_autocomplete_limit():
    t = Trie()
    for w in ["a" + str(i) for i in range(20)]:
        t.insert(w)
    result = t.autocomplete("a", limit=5)
    assert len(result) == 5

def test_empty_prefix():
    t = Trie()
    t.insert("hello")
    t.insert("world")
    result = t.autocomplete("")
    assert "hello" in result and "world" in result

def test_no_match():
    t = Trie()
    t.insert("hello")
    assert t.autocomplete("xyz") == []
    assert t.search("xyz") == False
    assert t.starts_with("xyz") == False
""",
    ))
    
    # ── Task 6: Expression Evaluator ──
    tasks.append(Task(
        task_id="eval_expr",
        description="""Write a function `evaluate(expr)` that evaluates a mathematical expression string.
Support: +, -, *, / (integer division), parentheses, unary minus.
No eval() or exec() allowed. Handle operator precedence correctly.
Examples: evaluate("3+2*2") -> 7, evaluate("(1+2)*3") -> 9, evaluate("-1+2") -> 1""",
        initial_code="def evaluate(expr):\n    pass\n",
        test_code="""
from solution import evaluate

def test_simple():
    assert evaluate("3+2") == 5

def test_precedence():
    assert evaluate("3+2*2") == 7

def test_parens():
    assert evaluate("(1+2)*3") == 9

def test_division():
    assert evaluate("10/3") == 3

def test_complex():
    assert evaluate("2*(3+4)-5") == 9

def test_nested_parens():
    assert evaluate("((2+3)*4)/2") == 10

def test_unary_minus():
    assert evaluate("-1+2") == 1

def test_spaces():
    assert evaluate(" 3 + 2 * 2 ") == 7

def test_multi_digit():
    assert evaluate("100+200*3") == 700
""",
    ))
    
    # ── Task 7: Topological Sort with Cycle Detection ──
    tasks.append(Task(
        task_id="topo_sort",
        description="""Write a function `topo_sort(num_nodes, edges)` where edges is a list of [from, to] pairs.
Return a valid topological ordering as a list, or an empty list if a cycle is detected.
Nodes are numbered 0 to num_nodes-1.""",
        initial_code="def topo_sort(num_nodes, edges):\n    pass\n",
        test_code="""
from solution import topo_sort

def test_basic():
    result = topo_sort(4, [[0,1],[0,2],[1,3],[2,3]])
    assert result.index(0) < result.index(1)
    assert result.index(0) < result.index(2)
    assert result.index(1) < result.index(3)
    assert len(result) == 4

def test_linear():
    assert topo_sort(3, [[0,1],[1,2]]) == [0, 1, 2]

def test_cycle():
    assert topo_sort(3, [[0,1],[1,2],[2,0]]) == []

def test_no_edges():
    result = topo_sort(3, [])
    assert len(result) == 3 and set(result) == {0, 1, 2}

def test_single():
    assert topo_sort(1, []) == [0]

def test_diamond():
    result = topo_sort(4, [[0,1],[0,2],[1,3],[2,3]])
    assert result[0] == 0 and result[-1] == 3
""",
    ))
    
    # ── Task 8: Minimum Window Substring ──
    tasks.append(Task(
        task_id="min_window",
        description="""Write a function `min_window(s, t)` that finds the minimum window substring 
of s that contains all characters of t (including duplicates).
Return "" if no such window exists. If multiple valid windows of same length, return the first one.""",
        initial_code="def min_window(s, t):\n    pass\n",
        test_code="""
from solution import min_window

def test_basic():
    assert min_window("ADOBECODEBANC", "ABC") == "BANC"

def test_exact():
    assert min_window("a", "a") == "a"

def test_no_match():
    assert min_window("a", "aa") == ""

def test_full_string():
    assert min_window("abc", "abc") == "abc"

def test_duplicates():
    assert min_window("aaabbbccc", "abc") == "abbbc" or min_window("aaabbbccc", "abc") == "bbbcc" or len(min_window("aaabbbccc", "abc")) == 5

def test_empty():
    assert min_window("", "a") == ""
    assert min_window("a", "") == ""
""",
    ))
    
    # ── Task 9: Word Break with Reconstruction ──
    tasks.append(Task(
        task_id="word_break",
        description="""Write two functions:
- `can_break(s, word_dict)`: Return True if s can be segmented into words from word_dict
- `break_sentence(s, word_dict)`: Return ONE valid segmentation as a list of words, or empty list if impossible.
word_dict is a list of strings.""",
        initial_code="""def can_break(s, word_dict):
    pass

def break_sentence(s, word_dict):
    pass
""",
        test_code="""
from solution import can_break, break_sentence

def test_can_break_true():
    assert can_break("leetcode", ["leet", "code"]) == True

def test_can_break_false():
    assert can_break("catsandog", ["cats", "dog", "sand", "and", "cat"]) == False

def test_can_break_reuse():
    assert can_break("applepenapple", ["apple", "pen"]) == True

def test_break_sentence():
    result = break_sentence("leetcode", ["leet", "code"])
    assert result == ["leet", "code"]

def test_break_sentence_impossible():
    result = break_sentence("catsandog", ["cats", "dog", "sand", "and", "cat"])
    assert result == []

def test_break_sentence_reuse():
    result = break_sentence("applepenapple", ["apple", "pen"])
    assert "".join(result) == "applepenapple"
    assert all(w in ["apple", "pen"] for w in result)
""",
    ))
    
    # ── Task 10: Consistent Hashing ──
    tasks.append(Task(
        task_id="consistent_hash",
        description="""Implement a consistent hashing ring:
- `__init__(self, num_replicas=3)`: Initialize with virtual node count per real node
- `add_node(self, node_id)`: Add a node to the ring
- `remove_node(self, node_id)`: Remove a node from the ring
- `get_node(self, key)`: Return which node a key maps to
- Use hashlib.md5 for hashing. The ring should distribute keys roughly evenly.""",
        initial_code="""import hashlib

class ConsistentHash:
    def __init__(self, num_replicas=3):
        pass
    
    def add_node(self, node_id):
        pass
    
    def remove_node(self, node_id):
        pass
    
    def get_node(self, key):
        pass
""",
        test_code="""
from solution import ConsistentHash

def test_basic():
    ch = ConsistentHash(num_replicas=3)
    ch.add_node("server1")
    ch.add_node("server2")
    node = ch.get_node("my_key")
    assert node in ["server1", "server2"]

def test_consistency():
    ch = ConsistentHash(num_replicas=3)
    ch.add_node("s1")
    ch.add_node("s2")
    results = [ch.get_node(f"key_{i}") for i in range(100)]
    # Adding a new node should keep most keys stable
    ch.add_node("s3")
    new_results = [ch.get_node(f"key_{i}") for i in range(100)]
    unchanged = sum(1 for a, b in zip(results, new_results) if a == b)
    # At least 50% should stay the same
    assert unchanged >= 50, f"Only {unchanged}/100 keys stayed the same"

def test_distribution():
    ch = ConsistentHash(num_replicas=100)
    for i in range(3):
        ch.add_node(f"server{i}")
    counts = {}
    for i in range(3000):
        node = ch.get_node(f"key_{i}")
        counts[node] = counts.get(node, 0) + 1
    # Each server should get at least 500 keys (of 3000 total, expect ~1000 each)
    for node, count in counts.items():
        assert count >= 500, f"{node} only got {count} keys"

def test_remove():
    ch = ConsistentHash(num_replicas=3)
    ch.add_node("s1")
    ch.add_node("s2")
    ch.remove_node("s1")
    # All keys should now go to s2
    for i in range(10):
        assert ch.get_node(f"key_{i}") == "s2"

def test_empty():
    ch = ConsistentHash()
    assert ch.get_node("key") is None
""",
    ))
    
    return tasks
