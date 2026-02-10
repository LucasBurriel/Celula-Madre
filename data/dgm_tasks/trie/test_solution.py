from solution import Trie

def test_basic():
    t = Trie()
    t.insert("apple")
    assert t.search("apple") == True
    assert t.search("app") == False
    assert t.starts_with("app") == True

def test_autocomplete():
    t = Trie()
    for w in ["apple", "app", "application", "apply", "banana"]:
        t.insert(w)
    result = t.autocomplete("app")
    assert result == ["app", "apple", "application", "apply"]

def test_autocomplete_limit():
    t = Trie()
    for w in ["a" + str(i) for i in range(20)]:
        t.insert(w)
    result = t.autocomplete("a", limit=5)
    assert len(result) == 5

def test_empty_prefix():
    t = Trie()
    t.insert("hello")
    t.insert("world")
    result = t.autocomplete("")
    assert "hello" in result and "world" in result

def test_no_match():
    t = Trie()
    t.insert("hello")
    assert t.autocomplete("xyz") == []
    assert t.search("xyz") == False
    assert t.starts_with("xyz") == False
