import pytest
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
