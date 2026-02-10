import pytest
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
