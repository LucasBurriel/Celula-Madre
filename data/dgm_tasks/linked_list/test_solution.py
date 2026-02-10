import pytest
from solution import LinkedList

def test_append():
    ll = LinkedList()
    ll.append(1); ll.append(2); ll.append(3)
    assert ll.to_list() == [1, 2, 3]

def test_prepend():
    ll = LinkedList()
    ll.prepend(3); ll.prepend(2); ll.prepend(1)
    assert ll.to_list() == [1, 2, 3]

def test_delete():
    ll = LinkedList()
    ll.append(1); ll.append(2); ll.append(3)
    assert ll.delete(2) == True
    assert ll.to_list() == [1, 3]

def test_delete_head():
    ll = LinkedList()
    ll.append(1); ll.append(2)
    assert ll.delete(1) == True
    assert ll.to_list() == [2]

def test_delete_not_found():
    ll = LinkedList()
    ll.append(1)
    assert ll.delete(5) == False

def test_find():
    ll = LinkedList()
    ll.append(1); ll.append(2)
    assert ll.find(2) == True
    assert ll.find(5) == False

def test_empty():
    ll = LinkedList()
    assert ll.to_list() == []
    assert ll.find(1) == False
    assert ll.delete(1) == False
