from solution import min_window

def test_basic():
    assert min_window("ADOBECODEBANC", "ABC") == "BANC"

def test_exact():
    assert min_window("a", "a") == "a"

def test_no_match():
    assert min_window("a", "aa") == ""

def test_full_string():
    assert min_window("abc", "abc") == "abc"

def test_duplicates():
    assert min_window("aaabbbccc", "abc") == "abbbc" or min_window("aaabbbccc", "abc") == "bbbcc" or len(min_window("aaabbbccc", "abc")) == 5

def test_empty():
    assert min_window("", "a") == ""
    assert min_window("a", "") == ""
