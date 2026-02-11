import pytest
from solution import Promise

def test_resolve():
    result = []
    p = Promise(lambda resolve, reject: resolve(42))
    p.then(lambda v: result.append(v))
    assert result == [42]

def test_reject():
    result = []
    p = Promise(lambda resolve, reject: reject("error"))
    p.catch(lambda e: result.append(e))
    assert result == ["error"]

def test_chain():
    result = []
    p = Promise(lambda resolve, reject: resolve(1))
    p.then(lambda v: v + 1).then(lambda v: result.append(v))
    assert result == [2]

def test_long_chain():
    result = []
    p = Promise(lambda resolve, reject: resolve(0))
    p.then(lambda v: v + 1).then(lambda v: v * 2).then(lambda v: v + 3).then(lambda v: result.append(v))
    assert result == [5]

def test_error_propagation():
    result = []
    p = Promise(lambda resolve, reject: reject("fail"))
    p.then(lambda v: v + 1).then(lambda v: v + 2).catch(lambda e: result.append(e))
    assert result == ["fail"]

def test_catch_and_continue():
    result = []
    p = Promise(lambda resolve, reject: reject("err"))
    p.catch(lambda e: 99).then(lambda v: result.append(v))
    assert result == [99]

def test_then_raises():
    result = []
    def bad(v):
        raise ValueError("boom")
    p = Promise(lambda resolve, reject: resolve(1))
    p.then(bad).catch(lambda e: result.append(str(e)))
    assert result == ["boom"]

def test_static_resolve():
    result = []
    Promise.resolve(10).then(lambda v: result.append(v))
    assert result == [10]

def test_static_reject():
    result = []
    Promise.reject("no").catch(lambda e: result.append(e))
    assert result == ["no"]

def test_then_returns_promise():
    result = []
    p = Promise.resolve(1)
    p2 = p.then(lambda v: Promise.resolve(v + 10))
    p2.then(lambda v: result.append(v))
    assert result == [11]
