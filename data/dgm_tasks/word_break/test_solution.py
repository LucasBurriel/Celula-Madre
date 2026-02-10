from solution import can_break, break_sentence

def test_can_break_true():
    assert can_break("leetcode", ["leet", "code"]) == True

def test_can_break_false():
    assert can_break("catsandog", ["cats", "dog", "sand", "and", "cat"]) == False

def test_can_break_reuse():
    assert can_break("applepenapple", ["apple", "pen"]) == True

def test_break_sentence():
    result = break_sentence("leetcode", ["leet", "code"])
    assert result == ["leet", "code"]

def test_break_sentence_impossible():
    result = break_sentence("catsandog", ["cats", "dog", "sand", "and", "cat"])
    assert result == []

def test_break_sentence_reuse():
    result = break_sentence("applepenapple", ["apple", "pen"])
    assert "".join(result) == "applepenapple"
    assert all(w in ["apple", "pen"] for w in result)
