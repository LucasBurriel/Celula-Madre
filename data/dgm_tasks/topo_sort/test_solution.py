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
