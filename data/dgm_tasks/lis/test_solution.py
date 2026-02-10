from solution import lis
import time

def test_basic():
    assert lis([10, 9, 2, 5, 3, 7, 101, 18]) == 4

def test_all_inc():
    assert lis([1, 2, 3, 4, 5]) == 5

def test_all_dec():
    assert lis([5, 4, 3, 2, 1]) == 1

def test_single():
    assert lis([7]) == 1

def test_dups():
    assert lis([1, 3, 6, 7, 9, 4, 10, 5, 6]) == 6

def test_performance():
    import random
    random.seed(42)
    nums = [random.randint(0, 100000) for _ in range(50000)]
    start = time.time()
    result = lis(nums)
    elapsed = time.time() - start
    assert elapsed < 5.0, f"Too slow: {elapsed:.1f}s (must be <5s for n=50000)"
    assert result > 0
