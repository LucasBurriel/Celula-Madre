class AVLTree:
    class Node:
        def __init__(self, key):
            self.key = key
            self.left = None
            self.right = None
            self.height = 1

    def __init__(self):
        self.root = None

    def insert(self, key):
        pass

    def search(self, key):
        """Return True if key exists."""
        pass

    def delete(self, key):
        pass

    def in_order(self):
        """Return sorted list of all keys."""
        pass

    def height(self):
        """Return tree height."""
        pass
