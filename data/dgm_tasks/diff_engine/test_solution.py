import pytest
from solution import unified_diff

def test_identical():
    assert unified_diff("a\nb\nc", "a\nb\nc") == [" a", " b", " c"]

def test_add_line():
    result = unified_diff("a\nc", "a\nb\nc")
    assert result == [" a", "+b", " c"]

def test_remove_line():
    result = unified_diff("a\nb\nc", "a\nc")
    assert result == [" a", "-b", " c"]

def test_modify_line():
    result = unified_diff("a\nb\nc", "a\nB\nc")
    assert result == [" a", "-b", "+B", " c"]

def test_empty_to_content():
    result = unified_diff("", "a\nb")
    assert result == ["+a", "+b"]

def test_content_to_empty():
    result = unified_diff("a\nb", "")
    assert result == ["-a", "-b"]

def test_both_empty():
    assert unified_diff("", "") == []

def test_complete_rewrite():
    result = unified_diff("a\nb", "c\nd")
    assert "-a" in result and "-b" in result
    assert "+c" in result and "+d" in result

def test_add_at_end():
    result = unified_diff("a", "a\nb")
    assert result == [" a", "+b"]

def test_longer_example():
    old = "the\nquick\nbrown\nfox"
    new = "the\nslow\nbrown\ndog"
    result = unified_diff(old, new)
    assert " the" in result
    assert "-quick" in result
    assert "+slow" in result
    assert " brown" in result
    assert "-fox" in result
    assert "+dog" in result
