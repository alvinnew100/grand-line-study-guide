"""Test-data generators shared by this track's problem files (not a problem file itself)."""
import collections
import random


class _T:
    __slots__ = ("val", "left", "right")

    def __init__(self, v):
        self.val, self.left, self.right = v, None, None


def level_order(root):
    """TreeNode-like -> LeetCode level-order list (trailing Nones trimmed)."""
    if root is None:
        return []
    out, q = [], collections.deque([root])
    while q:
        n = q.popleft()
        if n is None:
            out.append(None)
            continue
        out.append(n.val)
        q.append(n.left)
        q.append(n.right)
    while out and out[-1] is None:
        out.pop()
    return out


def bst_from_keys(keys):
    """Insert keys (in the given order) into a plain BST; return level-order list."""
    root = None
    for k in keys:
        if root is None:
            root = _T(k)
            continue
        cur = root
        while True:
            if k < cur.val:
                if cur.left is None:
                    cur.left = _T(k)
                    break
                cur = cur.left
            elif k > cur.val:
                if cur.right is None:
                    cur.right = _T(k)
                    break
                cur = cur.right
            else:
                break
    return level_order(root)


def balanced_bst(lo, hi):
    """Perfectly balanced BST over the integers lo..hi (inclusive) as level order."""
    def build(a, b):
        if a > b:
            return None
        m = (a + b) // 2
        n = _T(m)
        n.left = build(a, m - 1)
        n.right = build(m + 1, b)
        return n
    return level_order(build(lo, hi))


def random_tree(n, seed, lo=-100, hi=100, depth_cap=None):
    """Random-shaped binary tree with n nodes (random values) as level order."""
    rnd = random.Random(seed)
    root = _T(rnd.randint(lo, hi))
    nodes = [(root, 0)]
    for _ in range(n - 1):
        while True:
            parent, d = rnd.choice(nodes)
            if depth_cap is not None and d + 1 > depth_cap:
                continue
            side = rnd.choice(("left", "right"))
            if getattr(parent, side) is None:
                child = _T(rnd.randint(lo, hi))
                setattr(parent, side, child)
                nodes.append((child, d + 1))
                break
    return level_order(root)


def skewed(values, side="right"):
    """A chain-shaped tree (each node has only one child) as level order."""
    if not values:
        return []
    out = [values[0]]
    for v in values[1:]:
        out += [None, v] if side == "right" else [v, None]
    while out and out[-1] is None:
        out.pop()
    return out


def complete(values):
    """Complete binary tree: the level-order list is just the values."""
    return list(values)


def build(arr):
    """Level-order list -> _T tree (same rules as the judge)."""
    if not arr or arr[0] is None:
        return None
    it = iter(arr)
    root = _T(next(it))
    q = collections.deque([root])
    while q:
        node = q.popleft()
        for side in ("left", "right"):
            try:
                v = next(it)
            except StopIteration:
                return root
            if v is not None:
                child = _T(v)
                setattr(node, side, child)
                q.append(child)
    return root


def preorder(arr):
    out, st = [], [build(arr)]
    while st:
        n = st.pop()
        if n:
            out.append(n.val)
            st.append(n.right)
            st.append(n.left)
    return out


def inorder(arr):
    out, st, cur = [], [], build(arr)
    while st or cur:
        while cur:
            st.append(cur)
            cur = cur.left
        cur = st.pop()
        out.append(cur.val)
        cur = cur.right
    return out


def relabel_distinct(arr, seed=0):
    """Give every node of a level-order tree a distinct value (shuffled 1..n)."""
    n = sum(v is not None for v in arr)
    vals = list(range(1, n + 1))
    random.Random(seed).shuffle(vals)
    it = iter(vals)
    return [None if v is None else next(it) for v in arr]
