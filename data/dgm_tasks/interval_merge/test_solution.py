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
