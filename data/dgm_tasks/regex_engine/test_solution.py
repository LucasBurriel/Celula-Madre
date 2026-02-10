import pytest
from solution import match

def test_literal():
    assert match("abc", "abc") == True
    assert match("abc", "abd") == False

def test_dot():
    assert match("a.c", "abc") == True
    assert match("a.c", "adc") == True
    assert match("a.c", "ac") == False

def test_star():
    assert match("ab*c", "ac") == True
    assert match("ab*c", "abc") == True
    assert match("ab*c", "abbc") == True
    assert match("ab*c", "abbbc") == True

def test_plus():
    assert match("ab+c", "ac") == False
    assert match("ab+c", "abc") == True
    assert match("ab+c", "abbc") == True

def test_question():
    assert match("ab?c", "ac") == True
    assert match("ab?c", "abc") == True
    assert match("ab?c", "abbc") == False

def test_char_class():
    assert match("[abc]d", "ad") == True
    assert match("[abc]d", "bd") == True
    assert match("[abc]d", "dd") == False

def test_complex():
    assert match("a.*b", "ab") == True
    assert match("a.*b", "axxb") == True
    assert match("a.*b", "axxc") == False

def test_dot_star():
    assert match(".*", "") == True
    assert match(".*", "anything") == True

def test_empty():
    assert match("", "") == True
    assert match("", "a") == False
