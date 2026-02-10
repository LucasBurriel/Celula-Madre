from solution import TreeNode, serialize, deserialize

def trees_equal(a, b):
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return a.val == b.val and trees_equal(a.left, b.left) and trees_equal(a.right, b.right)

def test_basic():
    root = TreeNode(1, TreeNode(2), TreeNode(3, TreeNode(4), TreeNode(5)))
    assert trees_equal(deserialize(serialize(root)), root)

def test_empty():
    assert deserialize(serialize(None)) is None

def test_single():
    root = TreeNode(42)
    result = deserialize(serialize(root))
    assert result.val == 42 and result.left is None and result.right is None

def test_left_skewed():
    root = TreeNode(1, TreeNode(2, TreeNode(3, TreeNode(4))))
    assert trees_equal(deserialize(serialize(root)), root)

def test_negative():
    root = TreeNode(-1, TreeNode(-2), TreeNode(-3))
    assert trees_equal(deserialize(serialize(root)), root)

def test_large():
    # Build a complete binary tree of depth 8
    def build(depth):
        if depth == 0:
            return None
        return TreeNode(depth, build(depth-1), build(depth-1))
    root = build(8)
    assert trees_equal(deserialize(serialize(root)), root)
