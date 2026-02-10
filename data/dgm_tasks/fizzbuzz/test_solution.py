import pytest
from solution import fizzbuzz

def test_fizzbuzz_basic():
    result = fizzbuzz(15)
    assert result[0] == "1"
    assert result[2] == "Fizz"
    assert result[4] == "Buzz"
    assert result[14] == "FizzBuzz"

def test_fizzbuzz_length():
    assert len(fizzbuzz(20)) == 20

def test_fizzbuzz_multiples_of_3():
    result = fizzbuzz(15)
    for i in [2, 5, 8, 11]:
        assert result[i] == "Fizz" or result[i] == "FizzBuzz"

def test_fizzbuzz_multiples_of_5():
    result = fizzbuzz(15)
    assert result[4] == "Buzz"
    assert result[9] == "Buzz"

def test_fizzbuzz_one():
    assert fizzbuzz(1) == ["1"]
