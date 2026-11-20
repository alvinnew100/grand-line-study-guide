import random as _r

_r.seed(31)


def _bst_ops(n, seed, keyrange):
    rnd = _r.Random(seed)
    ops, args = ["BST"], [[]]
    for _ in range(n):
        x = rnd.random()
        k = rnd.randint(0, keyrange)
        if x < 0.40:
            ops.append("insert"); args.append([k])
        elif x < 0.62:
            ops.append("delete"); args.append([k])
        elif x < 0.77:
            ops.append("contains"); args.append([k])
        elif x < 0.87:
            ops.append("floor"); args.append([k])
        elif x < 0.92:
            ops.append("min"); args.append([])
        elif x < 0.96:
            ops.append("max"); args.append([])
        else:
            ops.append("inorder"); args.append([])
    ops += ["size", "inorder"]; args += [[], []]
    return [ops, args]


def _avl_level(keys):
    """Reference AVL build -> level-order list with None holes (for is-AVL test inputs)."""
    def h(n): return n[3] if n else 0
    def fix(n): n[3] = 1 + max(h(n[1]), h(n[2]))
    def rr(y):
        x = y[1]; y[1], x[2] = x[2], y; fix(y); fix(x); return x
    def rl(x):
        y = x[2]; x[2], y[1] = y[1], x; fix(x); fix(y); return y
    def ins(n, k):
        if n is None: return [k, None, None, 1]
        if k < n[0]: n[1] = ins(n[1], k)
        elif k > n[0]: n[2] = ins(n[2], k)
        fix(n)
        b = h(n[1]) - h(n[2])
        if b > 1:
            if h(n[1][1]) < h(n[1][2]): n[1] = rl(n[1])
            return rr(n)
        if b < -1:
            if h(n[2][2]) < h(n[2][1]): n[2] = rr(n[2])
            return rl(n)
        return n
    root = None
    for k in keys: root = ins(root, k)
    out, q = [], [root]
    while q:
        n = q.pop(0)
        if n is None: out.append(None); continue
        out.append(n[0]); q.append(n[1]); q.append(n[2])
    while out and out[-1] is None: out.pop()
    return out


_big_avl = _avl_level(_r.sample(range(5000), 400))
_big_avl_bad = list(_big_avl)
_big_avl_bad[len(_big_avl_bad) - 1] = -7          # a deep leaf that violates an ancestor bound

PROBLEMS = [
dict(
    id="dsaf-bst-class",
    title="Binary Search Tree: Insert, Search, Delete",
    difficulty="Medium",
    pattern="Search Trees",
    kind="class",
    entry="BST",
    description=r"""
Implement an (unbalanced) binary search tree of distinct integer keys (Goodrich ch. 11.1) with
linked nodes — do not keep the keys in a list or set.

- `insert(k)` → `True` if `k` was added, `False` if it was already present.
- `contains(k)` → bool.
- `delete(k)` → `True` if `k` was present and removed, else `False`. Handle all three cases: leaf,
  one child, two children (replace with the inorder predecessor or successor).
- `min()` / `max()` → smallest / largest key, or `None` if empty.
- `floor(k)` → the largest key `<= k`, or `None` if there is none.
- `inorder()` → list of all keys in increasing order.
- `size()`.

The tests only observe keys (never the tree's shape), so either deletion strategy is accepted.

**Example:** `["BST","insert","insert","insert","insert","inorder","floor","delete","inorder","contains"]`,
`[[],[44],[17],[88],[32],[],[40],[44],[],[44]]` → `[null,true,true,true,true,[17,32,44,88],32,true,[17,32,88],false]`
""",
    starter='''class _Node:
    __slots__ = "key", "left", "right"
    def __init__(self, key):
        self.key, self.left, self.right = key, None, None


class BST:
    def __init__(self):
        self._root = None
        self._size = 0

    def insert(self, k):
        pass

    def contains(self, k):
        pass

    def delete(self, k):
        pass

    def min(self):
        pass

    def max(self):
        pass

    def floor(self, k):
        pass

    def inorder(self):
        pass

    def size(self):
        pass
''',
    solution='''class _Node:
    __slots__ = "key", "left", "right"
    def __init__(self, key):
        self.key, self.left, self.right = key, None, None


class BST:
    def __init__(self):
        self._root = None
        self._size = 0

    def insert(self, k):
        if self._root is None:
            self._root = _Node(k)
            self._size = 1
            return True
        p = self._root
        while True:
            if k == p.key:
                return False
            if k < p.key:
                if p.left is None:
                    p.left = _Node(k)
                    break
                p = p.left
            else:
                if p.right is None:
                    p.right = _Node(k)
                    break
                p = p.right
        self._size += 1
        return True

    def contains(self, k):
        p = self._root
        while p is not None:
            if k == p.key:
                return True
            p = p.left if k < p.key else p.right
        return False

    def delete(self, k):
        parent, p = None, self._root
        while p is not None and p.key != k:
            parent, p = p, (p.left if k < p.key else p.right)
        if p is None:
            return False
        if p.left is not None and p.right is not None:
            rp, r = p, p.left
            while r.right is not None:
                rp, r = r, r.right
            p.key = r.key
            parent, p = rp, r
        child = p.left if p.left is not None else p.right
        if parent is None:
            self._root = child
        elif parent.left is p:
            parent.left = child
        else:
            parent.right = child
        self._size -= 1
        return True

    def min(self):
        p = self._root
        if p is None:
            return None
        while p.left is not None:
            p = p.left
        return p.key

    def max(self):
        p = self._root
        if p is None:
            return None
        while p.right is not None:
            p = p.right
        return p.key

    def floor(self, k):
        best, p = None, self._root
        while p is not None:
            if p.key == k:
                return k
            if p.key < k:
                best = p.key
                p = p.right
            else:
                p = p.left
        return best

    def inorder(self):
        out, stack, p = [], [], self._root
        while stack or p is not None:
            while p is not None:
                stack.append(p)
                p = p.left
            p = stack.pop()
            out.append(p.key)
            p = p.right
        return out

    def size(self):
        return self._size
''',
    tests=[
        [["BST", "insert", "insert", "insert", "insert", "inorder", "floor", "delete", "inorder", "contains"],
         [[], [44], [17], [88], [32], [], [40], [44], [], [44]]],
        [["BST", "min", "max", "floor", "contains", "delete", "inorder", "size"], [[], [], [], [5], [5], [5], [], []]],
        [["BST", "insert", "insert", "size", "delete", "delete", "size", "min", "insert", "max"],
         [[], [5], [5], [], [5], [5], [], [], [9], []]],
        [["BST"] + ["insert"] * 15 + ["delete", "inorder", "delete", "inorder", "delete", "inorder", "min", "max", "floor", "floor", "floor"],
         [[]] + [[k] for k in [44, 17, 88, 8, 32, 65, 97, 28, 54, 82, 93, 21, 29, 76, 80]]
         + [[88], [], [32], [], [8], [], [], [], [20], [7], [1000]]],
        [["BST"] + ["insert"] * 7 + ["delete"] * 7 + ["inorder", "size", "insert", "inorder"],
         [[]] + [[k] for k in [4, 2, 6, 1, 3, 5, 7]] + [[k] for k in [4, 2, 6, 1, 3, 5, 7]] + [[], [], [10], []]],
        [["BST"] + ["insert"] * 6 + ["delete", "inorder", "delete", "inorder", "delete", "inorder"],
         [[]] + [[k] for k in [10, 5, 15, 12, 20, 11]] + [[10], [], [15], [], [5], []]],
        [["BST"] + ["insert"] * 300 + ["size", "min", "max", "floor", "delete", "delete", "min", "max"],
         [[]] + [[k] for k in range(300)] + [[], [], [], [150], [0], [299], [], []]],
        _bst_ops(120, 1, 20),
        _bst_ops(800, 2, 60),
        _bst_ops(1500, 3, 400),
    ],
    examples=2,
    wrong_solutions=[
        '''class BST:
    def __init__(self):
        self.s = {}
    def _ins(self, t, k):
        if t is None: return [k, None, None]
        if k < t[0]: t[1] = self._ins(t[1], k)
        elif k > t[0]: t[2] = self._ins(t[2], k)
        return t
    def insert(self, k):
        if self.contains(k): return False
        self.root = self._ins(getattr(self, "root", None), k); return True
    def contains(self, k):
        t = getattr(self, "root", None)
        while t:
            if t[0] == k: return True
            t = t[1] if k < t[0] else t[2]
        return False
    def _del(self, t, k):
        if t is None: return None
        if k < t[0]: t[1] = self._del(t[1], k)
        elif k > t[0]: t[2] = self._del(t[2], k)
        else:
            return t[1] if t[1] is not None else t[2]
        return t
    def delete(self, k):
        if not self.contains(k): return False
        self.root = self._del(self.root, k); return True
    def inorder(self):
        out = []
        def go(t):
            if t: go(t[1]); out.append(t[0]); go(t[2])
        go(getattr(self, "root", None)); return out
    def min(self):
        a = self.inorder(); return a[0] if a else None
    def max(self):
        a = self.inorder(); return a[-1] if a else None
    def floor(self, k):
        a = [x for x in self.inorder() if x <= k]; return a[-1] if a else None
    def size(self):
        return len(self.inorder())
''',
        '''class BST:
    def __init__(self):
        self.keys = set()
    def insert(self, k):
        if k in self.keys: return False
        self.keys.add(k); return True
    def contains(self, k): return k in self.keys
    def delete(self, k):
        if k in self.keys:
            self.keys.remove(k); return True
        return False
    def min(self): return min(self.keys) if self.keys else None
    def max(self): return max(self.keys) if self.keys else None
    def floor(self, k):
        a = [x for x in self.keys if x < k]
        return max(a) if a else None
    def inorder(self): return sorted(self.keys)
    def size(self): return len(self.keys)
''',
    ],
    guide=dict(
        prereqs="Lesson *Binary search trees*.",
        intuition="Every operation walks one root-to-leaf path guided by comparisons. Deletion is the only delicate part: a node with two children is not removed — its key is overwritten by its inorder predecessor, and the predecessor's old node (which has no right child) is removed instead.",
        hints=["Keep a `parent` pointer while walking down so you can relink.",
               "Two children: r = rightmost node of p.left; copy r.key into p; then splice out r.",
               "Splicing out a node with at most one child: make its parent point to that child (or update the root).",
               "floor(k): walk down; whenever you go right from a node with key < k, remember it as the best so far."],
        brute_force="A sorted Python list with bisect gives O(log n) search but O(n) insert/delete; an unsorted list is O(n) for everything.",
        approach="""
- insert / contains: standard descent.
- delete: find p and its parent. If two children: find predecessor r (with its parent), copy key, set (parent, p) = (rp, r). Then replace p by its only child in parent (or root).
- min / max: leftmost / rightmost.
- inorder: iterative with a stack (safe for chains of 300+ nodes).

Example: deleting 88 in the lesson's tree copies 82 over 88 and promotes 76 into 82's old place.
""",
        complexity="All operations O(h) where h is the height: O(log n) for random insertion orders, O(n) in the worst case (sorted insertions). inorder is O(n). Space O(n).",
        pitfalls="The first wrong solution drops the whole right subtree when deleting a node with two children. When the predecessor is p.left itself, its parent is p — relink p.left, not p.right. Do not forget to update the root when the deleted node is the root. floor must include k itself (<=).",
        follow_up="Add `ceiling`, `rank(k)` (store subtree sizes), and then self-balancing (AVL rotations).",
    ),
),
dict(
    id="dsaf-avl-check",
    title="Is It an AVL Tree?",
    difficulty="Medium",
    pattern="Search Trees",
    entry="is_avl",
    arg_types=["tree"],
    description=r"""
Given the root of a binary tree, return `True` iff it is a valid **AVL tree** (Goodrich ch. 11.3):

1. it is a binary search tree with **distinct** keys — every key in a node's left subtree is strictly
   smaller, every key in its right subtree strictly larger; and
2. it satisfies the **height-balance property** — for *every* node, the heights of its two subtrees
   differ by at most 1.

An empty tree is an AVL tree. Aim for $O(n)$: compute heights bottom-up in the same traversal.

**Example:** `[44, 17, 78, null, 32, 50, 88, null, null, 48, 62]` → `true`

**Example:** `[3, 2, null, 1]` → `false` (a left chain: BST, but unbalanced at the root)
""",
    starter='''class Solution:
    def is_avl(self, root):
        pass
''',
    solution='''class Solution:
    def is_avl(self, root):
        ok = True

        def rec(p, lo, hi):
            nonlocal ok
            if p is None or not ok:
                return 0
            if (lo is not None and p.val <= lo) or (hi is not None and p.val >= hi):
                ok = False
                return 0
            hl = rec(p.left, lo, p.val)
            hr = rec(p.right, p.val, hi)
            if abs(hl - hr) > 1:
                ok = False
            return 1 + max(hl, hr)

        rec(root, None, None)
        return ok
''',
    tests=[
        [[44, 17, 78, None, 32, 50, 88, None, None, 48, 62]],
        [[3, 2, None, 1]],
        [[]],
        [[1]],
        [[2, 1, 3]],
        [[2, 3, 1]],
        [[2, 2]],
        [[10, 5, 15, None, None, 6, 20]],
        [[10, 5, 15, 2, 7, 12, 20, 1]],
        [[8, 4, 12, 2, 6, None, None, 1]],
        [[50, 30, 70, 20, 40, 60, 80, 10, None, None, None, None, None, None, 90]],
        [[5, 3, 8, 2, 4, 7, 9, 1, None, None, None, 6]],
        [[5, 3, 8, 2, 4, None, None, 1, None, None, None, 0]],
        [[10, 5, 15, 3, None, None, 20, 2]],
        [[10, 5, 15, 3, 7, 12, 20, 2, None, None, None, None, None, None, 30, 1]],
        [_big_avl],
        [_big_avl_bad],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def is_avl(self, root):
        def h(p):
            return 0 if p is None else 1 + max(h(p.left), h(p.right))
        def ok(p):
            if p is None: return True
            if p.left and p.left.val >= p.val: return False
            if p.right and p.right.val <= p.val: return False
            return abs(h(p.left) - h(p.right)) <= 1 and ok(p.left) and ok(p.right)
        return ok(root)
''',
        '''class Solution:
    def is_avl(self, root):
        def h(p):
            return 0 if p is None else 1 + max(h(p.left), h(p.right))
        def bst(p, lo, hi):
            if p is None: return True
            if (lo is not None and p.val <= lo) or (hi is not None and p.val >= hi): return False
            return bst(p.left, lo, p.val) and bst(p.right, p.val, hi)
        return bst(root, None, None) and (root is None or abs(h(root.left) - h(root.right)) <= 1)
''',
        '''class Solution:
    def is_avl(self, root):
        def rec(p):
            if p is None: return 0
            hl, hr = rec(p.left), rec(p.right)
            if hl < 0 or hr < 0 or abs(hl - hr) > 1: return -1
            return 1 + max(hl, hr)
        return rec(root) >= 0
''',
    ],
    guide=dict(
        prereqs="Lessons *Binary search trees* (validation pitfall) and *Rotations and AVL trees*.",
        intuition="Two independent conditions. BST order is a constraint from ancestors, so pass (low, high) bounds DOWN. Balance depends on subtree heights, so return heights UP. One postorder-style recursion does both.",
        hints=["A node is valid if low < val < high; the left child gets (low, val), the right child (val, high).",
               "Return the subtree height from the recursion and compare the two children's heights.",
               "Balance must hold at every node, not just the root."],
        brute_force="Calling a separate height() at every node is O(n log n) on balanced trees and O(n^2) on chains; checking only parent/child key order misses violations deeper in a subtree.",
        approach="""
`rec(p, lo, hi)` returns the height of p's subtree and records failure in a flag:
1. None → 0.
2. If val is outside (lo, hi) → fail.
3. hl = rec(left, lo, val); hr = rec(right, val, hi); if |hl - hr| > 1 → fail.
4. return 1 + max(hl, hr).

Example `[10,5,15,null,null,6,20]`: 6 is in the right subtree of 10 but 6 < 10 → not a BST → False, even though each parent/child pair looks fine locally.
""",
        complexity="Time O(n), each node visited once; space O(h) recursion (h = O(log n) for a real AVL tree, but the input may be a chain).",
        pitfalls="Local-only BST checks (first wrong solution); checking balance only at the root (second); forgetting the BST condition entirely (third); allowing duplicates (use strict inequalities).",
        follow_up="Return the first unbalanced node; or, given a sorted array, build a perfectly balanced BST in O(n).",
    ),
),
dict(
    id="dsaf-avl-insert",
    title="AVL Insertion with Rotations",
    difficulty="Hard",
    pattern="Search Trees",
    entry="avl_insert",
    return_type="tree",
    description=r"""
Insert the integers of `keys`, in order, into an initially empty **AVL tree** and return the root of
the final tree (Goodrich ch. 11.3). Ignore keys that are already present.

After each insertion, restore the height-balance property with the standard trinode restructuring
at the lowest unbalanced ancestor: a **single rotation** for the left-left / right-right cases and a
**double rotation** for left-right / right-left. The resulting tree is unique, and the grader
compares its exact shape (level order).

Build the tree from `TreeNode(val, left, right)` objects (you may add attributes such as `height`).

**Example:** `keys = [1, 2, 3]` → `[2, 1, 3]` (a single left rotation at 1)

**Example:** `keys = [44, 17, 78, 32, 50, 88, 48, 62, 54]` → `[44, 17, 62, null, 32, 50, 78, null, null, 48, 54, null, 88]`
""",
    starter='''class Solution:
    def avl_insert(self, keys):
        root = None
        # insert each key, rebalancing on the way back up
        return root
''',
    solution='''class Solution:
    def avl_insert(self, keys):
        def h(n):
            return n.height if n else 0

        def fix(n):
            n.height = 1 + max(h(n.left), h(n.right))

        def rot_right(y):
            x = y.left
            y.left, x.right = x.right, y
            fix(y); fix(x)
            return x

        def rot_left(x):
            y = x.right
            x.right, y.left = y.left, x
            fix(x); fix(y)
            return y

        def insert(n, k):
            if n is None:
                t = TreeNode(k)
                t.height = 1
                return t
            if k < n.val:
                n.left = insert(n.left, k)
            elif k > n.val:
                n.right = insert(n.right, k)
            else:
                return n
            fix(n)
            bal = h(n.left) - h(n.right)
            if bal > 1:
                if h(n.left.left) < h(n.left.right):
                    n.left = rot_left(n.left)
                return rot_right(n)
            if bal < -1:
                if h(n.right.right) < h(n.right.left):
                    n.right = rot_right(n.right)
                return rot_left(n)
            return n

        root = None
        for k in keys:
            root = insert(root, k)
        return root
''',
    tests=[
        [[1, 2, 3]],
        [[44, 17, 78, 32, 50, 88, 48, 62, 54]],
        [[]],
        [[5]],
        [[3, 2, 1]],
        [[3, 1, 2]],
        [[1, 3, 2]],
        [[2, 1, 3, 3, 1, 2]],
        [[10, 20, 30, 40, 50, 25]],
        [list(range(1, 16))],
        [list(range(31, 0, -1))],
        [[50, 25, 75, 10, 30, 60, 80, 5, 15, 27, 55, 1]],
        [_r.sample(range(1000), 120)],
        [[_r.randint(0, 300) for _ in range(600)]],
        [list(range(1, 1001))],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def avl_insert(self, keys):
        def insert(n, k):
            if n is None: return TreeNode(k)
            if k < n.val: n.left = insert(n.left, k)
            elif k > n.val: n.right = insert(n.right, k)
            return n
        root = None
        for k in keys: root = insert(root, k)
        return root
''',
        '''class Solution:
    def avl_insert(self, keys):
        def h(n): return n.height if n else 0
        def fix(n): n.height = 1 + max(h(n.left), h(n.right))
        def rot_right(y):
            x = y.left; y.left, x.right = x.right, y; fix(y); fix(x); return x
        def rot_left(x):
            y = x.right; x.right, y.left = y.left, x; fix(x); fix(y); return y
        def insert(n, k):
            if n is None:
                t = TreeNode(k); t.height = 1; return t
            if k < n.val: n.left = insert(n.left, k)
            elif k > n.val: n.right = insert(n.right, k)
            else: return n
            fix(n)
            bal = h(n.left) - h(n.right)
            if bal > 1: return rot_right(n)
            if bal < -1: return rot_left(n)
            return n
        root = None
        for k in keys: root = insert(root, k)
        return root
''',
    ],
    guide=dict(
        prereqs="Lesson *Rotations and AVL trees*.",
        intuition="Insert like a BST, then on the way back up the recursion recompute heights. At the first node whose children differ in height by 2, look at which grandchild subtree is taller: same side → one rotation, opposite side (zig-zag) → rotate the child first, then the node.",
        hints=["Store a height in each node (leaf = 1, None = 0).",
               "rot_right(y): x = y.left; y.left = x.right; x.right = y; fix heights of y THEN x; return x.",
               "Left-heavy (balance > 1): if left child's right subtree is taller than its left, rot_left the child first; then rot_right the node. Mirror for right-heavy."],
        brute_force="Rebuilding a perfectly balanced tree from sorted keys after each insertion is O(n) per insert and yields a different shape than AVL rotations — the grader would reject it.",
        approach="""
Recursive `insert(n, k)` returns the (possibly new) subtree root:
1. Base: new node of height 1. Duplicate: return n unchanged.
2. Recurse left/right, then `fix(n)`.
3. balance = h(left) - h(right). Apply the LL / LR / RR / RL fix and return the new root.

Dry run `[1,2,3]`: insert 3 → node 1 has balance -2 with a right-right shape → rot_left(1) → root 2 with children 1 and 3.

Dry run for the lesson's example: inserting 54 unbalances 78 (left-right): rot_left(50) then rot_right(78) puts 62 on top of 50 and 78.
""",
        complexity="Each insertion is O(log n): one root-to-leaf path, O(1) work per level, at most two rotations. Total O(n log n) for n keys; height stays <= 1.44 log2(n+1). Space O(n).",
        pitfalls="Using single rotations in zig-zag cases (second wrong solution) leaves the tree unbalanced; updating the upper node's height before the lower node's; forgetting to reassign the rotated subtree to the parent link (return the new root!).",
        follow_up="Implement AVL deletion — rebalancing may be needed at every level on the way up.",
    ),
),
]
