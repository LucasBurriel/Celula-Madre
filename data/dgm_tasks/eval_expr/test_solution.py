from solution import evaluate

def test_simple():
    assert evaluate("3+2") == 5

def test_precedence():
    assert evaluate("3+2*2") == 7

def test_parens():
    assert evaluate("(1+2)*3") == 9

def test_division():
    assert evaluate("10/3") == 3

def test_complex():
    assert evaluate("2*(3+4)-5") == 9

def test_nested_parens():
    assert evaluate("((2+3)*4)/2") == 10

def test_unary_minus():
    assert evaluate("-1+2") == 1

def test_spaces():
    assert evaluate(" 3 + 2 * 2 ") == 7

def test_multi_digit():
    assert evaluate("100+200*3") == 700
