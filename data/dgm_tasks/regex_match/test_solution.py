from solution import regex_match

def test_exact():
    assert regex_match("abc", "abc") == True

def test_no_match():
    assert regex_match("aa", "a") == False

def test_star():
    assert regex_match("aa", "a*") == True

def test_dot_star():
    assert regex_match("ab", ".*") == True

def test_complex():
    assert regex_match("aab", "c*a*b") == True

def test_dot():
    assert regex_match("abc", "a.c") == True

def test_empty():
    assert regex_match("", "a*") == True

def test_star_complex():
    assert regex_match("mississippi", "mis*is*ip*.") == True

def test_false_star():
    assert regex_match("mississippi", "mis*is*p*.") == False

def test_nested():
    assert regex_match("aaa", "a*a") == True

def test_dot_star_prefix():
    assert regex_match("abcd", ".*d") == True
