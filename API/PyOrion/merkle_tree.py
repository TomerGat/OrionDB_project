from hash import hash_function


class TreeNode:
    def __init__(self, hash_value):
        self.hash = hash_value
        self.left = None
        self.right = None


class MerkleTree:
    def __init__(self, items):
        self.root = self.build(items)

    def build(self, items):
        n = len(items)
        if n == 0:
            return None
        elif n == 1:
            return TreeNode(hash_function(items[0]))

        # split the transactions into two halves
        mid = n // 2
        left_items = items[:mid]
        right_items = items[mid:]

        # recursively build a Merkle tree for each half
        left_subtree = self.build(left_items)
        right_subtree = self.build(right_items)

        # combine the two subtrees to create the final Merkle tree
        root_hash = hash_function(left_subtree.hash + right_subtree.hash)
        return TreeNode(root_hash)
