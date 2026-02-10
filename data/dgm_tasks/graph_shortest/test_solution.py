import pytest
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
