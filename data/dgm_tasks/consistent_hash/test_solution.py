from solution import ConsistentHash

def test_basic():
    ch = ConsistentHash(num_replicas=3)
    ch.add_node("server1")
    ch.add_node("server2")
    node = ch.get_node("my_key")
    assert node in ["server1", "server2"]

def test_consistency():
    ch = ConsistentHash(num_replicas=3)
    ch.add_node("s1")
    ch.add_node("s2")
    results = [ch.get_node(f"key_{i}") for i in range(100)]
    # Adding a new node should keep most keys stable
    ch.add_node("s3")
    new_results = [ch.get_node(f"key_{i}") for i in range(100)]
    unchanged = sum(1 for a, b in zip(results, new_results) if a == b)
    # At least 50% should stay the same
    assert unchanged >= 50, f"Only {unchanged}/100 keys stayed the same"

def test_distribution():
    ch = ConsistentHash(num_replicas=100)
    for i in range(3):
        ch.add_node(f"server{i}")
    counts = {}
    for i in range(3000):
        node = ch.get_node(f"key_{i}")
        counts[node] = counts.get(node, 0) + 1
    # Each server should get at least 500 keys (of 3000 total, expect ~1000 each)
    for node, count in counts.items():
        assert count >= 500, f"{node} only got {count} keys"

def test_remove():
    ch = ConsistentHash(num_replicas=3)
    ch.add_node("s1")
    ch.add_node("s2")
    ch.remove_node("s1")
    # All keys should now go to s2
    for i in range(10):
        assert ch.get_node(f"key_{i}") == "s2"

def test_empty():
    ch = ConsistentHash()
    assert ch.get_node("key") is None
