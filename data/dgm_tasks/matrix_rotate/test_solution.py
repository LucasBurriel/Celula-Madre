import pytest
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
