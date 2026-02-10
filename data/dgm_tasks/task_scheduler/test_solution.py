import pytest
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
