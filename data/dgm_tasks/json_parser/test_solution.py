import pytest
from solution import parse_json

def test_string():
    assert parse_json('"hello"') == "hello"

def test_number_int():
    assert parse_json('42') == 42

def test_number_float():
    assert parse_json('3.14') == 3.14

def test_negative():
    assert parse_json('-5') == -5

def test_bool():
    assert parse_json('true') == True
    assert parse_json('false') == False

def test_null():
    assert parse_json('null') is None

def test_array():
    assert parse_json('[1, 2, 3]') == [1, 2, 3]

def test_nested_array():
    assert parse_json('[[1, 2], [3, 4]]') == [[1, 2], [3, 4]]

def test_object():
    assert parse_json('{"a": 1, "b": 2}') == {"a": 1, "b": 2}

def test_nested():
    result = parse_json('{"name": "test", "values": [1, true, null]}')
    assert result == {"name": "test", "values": [1, True, None]}

def test_escape():
    assert parse_json('"hello\\nworld"') == "hello\nworld"

def test_empty_structures():
    assert parse_json('[]') == []
    assert parse_json('{}') == {}

def test_whitespace():
    assert parse_json('  { "a" : 1 }  ') == {"a": 1}
