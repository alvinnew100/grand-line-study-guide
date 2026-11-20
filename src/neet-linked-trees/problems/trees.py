import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nlt_gen import (balanced_bst, bst_from_keys, complete, inorder, preorder,  # noqa: E402
                     random_tree, relabel_distinct, skewed)

TN = '''# TreeNode is pre-defined by the judge (no need to paste it):
# class TreeNode:
#     def __init__(self, val=0, left=None, right=None):
#         self.val = val
#         self.left = left
#         self.right = right
'''

TREE_FORMAT = ("\n\n**Judge input format:** a tree is written in LeetCode *level order*: node values level by level, "
               "left to right, with `None` for a missing child and trailing `None`s dropped. `[]` is the empty tree "
               "(`root = None`). Example: `[3,9,20,None,None,15,7]` is 3 with children 9 and 20, where 20 has children "
               "15 and 7. The judge builds the `TreeNode`s for you, and a returned tree is printed in the same format.\n")

r = random.Random(2024)

BIG = random_tree(10000, 1, -1000, 1000)          # random shape, 10^4 nodes
BIG5 = random_tree(5000, 2, -1000, 1000)
SKEW_R = skewed(list(range(1, 501)), "right")      # depth 500 (recursion-safe)
SKEW_L = skewed(list(range(500, 0, -1)), "left")
COMPLETE = complete(range(1, 10001))
BST_BIG = bst_from_keys(r.sample(range(-10 ** 6, 10 ** 6), 5000))
BST_BAL = balanced_bst(1, 4095)

# checker shared by the two BST-modification problems: any valid BST holding the right keys is accepted
BST_CHECKER = '''
def check(args, got, expected):
    import collections

    class N:
        __slots__ = ("val", "left", "right")

        def __init__(self, v):
            self.val, self.left, self.right = v, None, None

    def build(arr):
        if not arr or arr[0] is None:
            return None
        it = iter(arr)
        root = N(next(it))
        q = collections.deque([root])
        while q:
            node = q.popleft()
            for side in ("left", "right"):
                try:
                    v = next(it)
                except StopIteration:
                    return root
                if v is not None:
                    c = N(v)
                    setattr(node, side, c)
                    q.append(c)
        return root

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

    if not isinstance(got, list):
        return False
    try:
        return inorder(got) == inorder(expected)
    except Exception:
        return False
'''

LCA_ADAPTER = '''

# ---- judge adapter: do not edit -------------------------------------------
# Each test is (root, p, q) with p and q given as VALUES. The adapter finds the
# two TreeNode objects, calls lowestCommonAncestor(root, p_node, q_node) and
# reports the value of the node you return.
def judge(root, p, q):
    def find(node, v):
        while node and node.val != v:
            node = node.left if v < node.val else node.right
        return node
    ans = Solution().lowestCommonAncestor(root, find(root, p), find(root, q))
    return None if ans is None else ans.val
'''

CODEC_ADAPTER = '''

# ---- judge adapter: do not edit -------------------------------------------
# The judge passes a tree, then checks a round trip through two SEPARATE Codec
# objects: Codec().deserialize(Codec().serialize(root)) must rebuild the tree.
def judge(root):
    data = Codec().serialize(root)
    if not isinstance(data, str):
        raise TypeError("serialize() must return a str, got %s" % type(data).__name__)
    return Codec().deserialize(data)
'''


def _lca_tests():
    tests = [[[6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 2, 8], [[6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 2, 4],
             [[2, 1], 2, 1], [[2, 1, 3], 1, 3], [[6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 3, 5],
             [[6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 0, 5], [[6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 7, 7]]
    tests.append([SKEW_R, 250, 500])
    keys = inorder(BST_BIG)
    for _ in range(2):
        a, b = r.sample(keys, 2)
        tests.append([BST_BIG, a, b])
    tests.append([BST_BAL, 1, 4095])
    return tests


def _build_tests():
    out = [[[3, 9, 20, 15, 7], [9, 3, 15, 20, 7]], [[-1], [-1]], [[1, 2], [2, 1]], [[1, 2], [1, 2]],
           [[1, 2, 3], [2, 1, 3]], [[1, 2, 4, 5, 3, 6, 7], [4, 2, 5, 1, 6, 3, 7]]]
    for t in (skewed(list(range(1, 401)), "left"), skewed(list(range(1, 401)), "right"),
              relabel_distinct(random_tree(3000, 5), 5), relabel_distinct(complete(range(4095)), 6)):
        out.append([preorder(t), inorder(t)])
    return out


PROBLEMS = [
# ============================================================================================
dict(
    id="invert-binary-tree",
    title="Invert Binary Tree",
    difficulty="Easy",
    pattern="Trees — DFS",
    leetcode="https://leetcode.com/problems/invert-binary-tree/",
    neetcode="https://neetcode.io/problems/invert-a-binary-tree",
    entry="invertTree",
    arg_types=["tree"],
    return_type="tree",
    description=r"""
Produce the **mirror image** of a binary tree: at every node, the left and right subtrees trade places.
Return the root of the mirrored tree (modifying the given tree is fine).

**Constraints**

- 0 to 100 nodes classically (the judge also uses 10,000), `-100 <= Node.val <= 100`.

**Example 1:** `root = [4,2,7,1,3,6,9]` → `[4,7,2,9,6,3,1]`

**Example 2:** `root = [2,1,3]` → `[2,3,1]`

**Example 3:** `root = []` → `[]`
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def invertTree(self, root: Optional[TreeNode]) -> Optional[TreeNode]:
        pass
''',
    solution='''class Solution:
    def invertTree(self, root):
        stack = [root]
        while stack:
            node = stack.pop()
            if node:
                node.left, node.right = node.right, node.left
                stack.append(node.left)
                stack.append(node.right)
        return root
''',
    tests=[[[4, 2, 7, 1, 3, 6, 9]], [[2, 1, 3]], [[]], [[1]], [[1, 2]], [[1, None, 2]], [[1, 2, 3, 4, None, None, 5]],
           [SKEW_R], [SKEW_L], [BIG5], [complete(range(1, 4096))]],
    wrong_solutions=[
        '''class Solution:
    def invertTree(self, root):
        if root:
            root.left, root.right = root.right, root.left   # only the root level
        return root
''',
    ],
    guide=dict(
        prereqs="Tree traversals — lesson *Traversals: DFS (pre/in/post) and BFS*.",
        intuition="Mirroring a tree = swap the two children of the root, then mirror each subtree. Every node needs the same local operation, so *any* traversal that visits every node once works.",
        hints=["What is the mirror of an empty tree? (Base case.)",
               "Recursively: swap `root.left` and `root.right`, then invert both children.",
               "Iteratively: pop a node from a stack (or queue), swap its children, push the children."],
        brute_force="This problem is already linear; the 'brute force' would be building a brand-new mirrored copy, which also costs O(n) but O(n) extra memory.",
        approach="""Recursive one-liner:

```python
def invertTree(self, root):
    if root:
        root.left, root.right = self.invertTree(root.right), self.invertTree(root.left)
    return root
```

The reference uses an explicit stack (pre-order) so very deep trees cannot overflow Python's recursion limit. Dry run on `[2,1,3]`: pop 2, swap → children (3,1); pop 1 and 3 — leaves, swap Nones. Result `[2,3,1]`.""",
        complexity="Time O(n). Space O(h) for the recursion/stack, h = height (O(n) for a skewed tree).",
        pitfalls="- Writing `root.left = invert(root.right); root.right = invert(root.left)` on two lines — the second line sees the *already replaced* left child. Use simultaneous assignment or a temp.\n- Forgetting to return `root`.",
        follow_up="Symmetric Tree (LeetCode 101): is a tree equal to its own mirror?",
    ),
),
# ============================================================================================
dict(
    id="maximum-depth-of-binary-tree",
    title="Maximum Depth of Binary Tree",
    difficulty="Easy",
    pattern="Trees — DFS / BFS",
    leetcode="https://leetcode.com/problems/maximum-depth-of-binary-tree/",
    neetcode="https://neetcode.io/problems/depth-of-binary-tree",
    entry="maxDepth",
    arg_types=["tree"],
    description=r"""
Return the number of **nodes** on the longest path from the root down to any leaf. An empty tree has
depth 0 and a single node has depth 1.

**Constraints**

- 0 to $10^4$ nodes, `-100 <= Node.val <= 100`.

**Example 1:** `root = [3,9,20,None,None,15,7]` → `3`

**Example 2:** `root = [1,None,2]` → `2`
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def maxDepth(self, root: Optional[TreeNode]) -> int:
        pass
''',
    solution='''class Solution:
    def maxDepth(self, root):
        if not root:
            return 0
        return 1 + max(self.maxDepth(root.left), self.maxDepth(root.right))
''',
    tests=[[[3, 9, 20, None, None, 15, 7]], [[1, None, 2]], [[]], [[0]], [[1, 2]], [[1, 2, 3, 4, None, None, 5, 6]],
           [[1, 2, 3, None, None, 4, None, None, 5]], [SKEW_R], [SKEW_L], [BIG], [COMPLETE]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def maxDepth(self, root):
        d = 0
        while root:                 # follows left children only
            d += 1
            root = root.left
        return d
''',
        '''class Solution:
    def maxDepth(self, root):
        if not root:
            return 0
        return 1 + min(self.maxDepth(root.left), self.maxDepth(root.right))
''',
    ],
    guide=dict(
        prereqs="Recursion on trees; height vs depth — lesson *Tree vocabulary*.",
        intuition="The depth of a tree is one (for the root) plus the depth of its deeper subtree. That is a post-order computation: ask both children first, then combine.",
        hints=["Base case: an empty tree has depth 0.",
               "`1 + max(depth(left), depth(right))`.",
               "Iterative alternative: BFS and count the levels."],
        brute_force="Enumerate every root-to-leaf path and take the longest — still O(n) if done by DFS, but storing paths costs O(n·h) memory.",
        approach="""Dry run on `[3,9,20,None,None,15,7]`: depth(9) = 1, depth(15) = depth(7) = 1, depth(20) = 2, depth(3) = 1 + max(1, 2) = 3.

BFS version: push the root, then process one whole level per loop iteration (`for _ in range(len(q))`), incrementing a counter per level.""",
        complexity="Time O(n). Space O(h) recursion (BFS: O(width)).",
        pitfalls="- Using `min` (that is *Minimum Depth*, and even that needs care with one-child nodes).\n- Counting edges instead of nodes: this problem counts nodes.",
        follow_up="Minimum Depth of Binary Tree (LeetCode 111); Maximum Depth of N-ary Tree (559).",
    ),
),
# ============================================================================================
dict(
    id="binary-tree-inorder-traversal",
    title="Binary Tree Inorder Traversal",
    difficulty="Easy",
    pattern="Trees — DFS (iterative)",
    leetcode="https://leetcode.com/problems/binary-tree-inorder-traversal/",
    entry="inorderTraversal",
    arg_types=["tree"],
    description=r"""
Return the list of node values in **inorder**: everything in the left subtree, then the node, then
everything in the right subtree.

**Constraints**

- 0 to 100 nodes classically (judge: up to 10,000), `-100 <= Node.val <= 100`.
- Follow-up: the recursive solution is trivial — can you do it with an explicit stack?

**Example 1:** `root = [1,None,2,3]` → `[1,3,2]`

**Example 2:** `root = [1,2,3,4,5,None,8,None,None,6,7,9]` → `[4,2,6,5,7,1,3,9,8]`
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def inorderTraversal(self, root: Optional[TreeNode]) -> List[int]:
        pass
''',
    solution='''class Solution:
    def inorderTraversal(self, root):
        out, stack, cur = [], [], root
        while stack or cur:
            while cur:
                stack.append(cur)
                cur = cur.left
            cur = stack.pop()
            out.append(cur.val)
            cur = cur.right
        return out
''',
    tests=[[[1, None, 2, 3]], [[1, 2, 3, 4, 5, None, 8, None, None, 6, 7, 9]], [[]], [[1]], [[2, 1]], [[1, None, 2]],
           [[3, 1, 5, 0, 2, 4, 6]], [SKEW_L], [BIG], [complete(range(2000))]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def inorderTraversal(self, root):
        out, stack = [], [root]
        while stack:                 # this is PRE-order
            n = stack.pop()
            if n:
                out.append(n.val)
                stack.append(n.right)
                stack.append(n.left)
        return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Traversals: DFS (pre/in/post) and BFS*.",
        intuition="Inorder means 'left, me, right'. Iteratively: dive left as far as possible, pushing every node you pass; when you cannot go further, pop — that node is next — then turn right once and repeat.",
        hints=["Recursive: `inorder(left); visit(node); inorder(right)`.",
               "For the stack version you need a `cur` pointer in addition to the stack.",
               "Loop while `stack or cur`: push-and-go-left until `cur` is None; pop, record, `cur = popped.right`."],
        brute_force="The recursive version is already optimal; its only weakness is recursion depth on very deep trees.",
        approach="Dry run `[1,None,2,3]`: push 1, cur=None → pop 1 (out [1]), cur = 2. Push 2, go left → push 3, cur None → pop 3 (out [1,3]), cur = 3.right = None → pop 2 (out [1,3,2]), cur = None, stack empty → done.",
        complexity="Time O(n). Space O(h) for the stack.",
        pitfalls="- Loop condition `while stack:` alone misses the case where the stack is empty but `cur` (a right child) is not.\n- Confusing the three orders: write the 'visit' line in the right place.",
        follow_up="Morris traversal does inorder with O(1) extra space by temporarily threading the tree. Pre-order (144) and post-order (145) traversal problems.",
    ),
),
# ============================================================================================
dict(
    id="same-tree",
    title="Same Tree",
    difficulty="Easy",
    pattern="Trees — Simultaneous DFS",
    leetcode="https://leetcode.com/problems/same-tree/",
    neetcode="https://neetcode.io/problems/same-binary-tree",
    entry="isSameTree",
    arg_types=["tree", "tree"],
    description=r"""
Given the roots of two binary trees `p` and `q`, decide whether they are identical: the same shape, and
equal values in corresponding nodes.

**Constraints**

- Each tree has 0 to 100 nodes classically (judge: up to 10,000), `-10^4 <= Node.val <= 10^4`.

**Example 1:** `p = [1,2,3], q = [1,2,3]` → `True`

**Example 2:** `p = [1,2], q = [1,None,2]` → `False` (the 2 hangs on different sides)

**Example 3:** `p = [1,2,1], q = [1,1,2]` → `False`
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def isSameTree(self, p: Optional[TreeNode], q: Optional[TreeNode]) -> bool:
        pass
''',
    solution='''class Solution:
    def isSameTree(self, p, q):
        stack = [(p, q)]
        while stack:
            a, b = stack.pop()
            if a is None and b is None:
                continue
            if a is None or b is None or a.val != b.val:
                return False
            stack.append((a.left, b.left))
            stack.append((a.right, b.right))
        return True
''',
    tests=[[[1, 2, 3], [1, 2, 3]], [[1, 2], [1, None, 2]], [[1, 2, 1], [1, 1, 2]], [[], []], [[], [0]], [[0], []],
           [[1, 2], [2, None, 1]], [[5], [5]], [[1, None, 2, 3], [1, None, 2, None, 3]], [BIG5, BIG5],
           [BIG5, BIG5[:-1] + [BIG5[-1] + 1]], [SKEW_R, SKEW_R]],
    wrong_solutions=[
        '''class Solution:
    def isSameTree(self, p, q):
        def ino(n):
            return ino(n.left) + [n.val] + ino(n.right) if n else []
        return ino(p) == ino(q)      # same inorder does not mean same tree
''',
        '''class Solution:
    def isSameTree(self, p, q):
        if not p or not q:
            return p is q
        return p.val == q.val          # only compares the roots
''',
    ],
    guide=dict(
        prereqs="DFS on trees.",
        intuition="Two trees are the same exactly when their roots match and their left subtrees are the same and their right subtrees are the same. Walk both trees in lock-step.",
        hints=["Handle the `None` cases first: both None → True; exactly one None → False.",
               "Then compare values and recurse on (left, left) and (right, right).",
               "A single traversal list (e.g. inorder) is *not* enough to identify a tree's shape."],
        brute_force="Serialise both trees with `None` markers (e.g. level order) and compare strings: O(n) time but O(n) extra memory.",
        approach="Recursive: `if not p and not q: return True; if not p or not q or p.val != q.val: return False; return same(p.left, q.left) and same(p.right, q.right)`. The reference uses a stack of pairs so deep trees are safe. On Example 2: roots 1 = 1; left pair (2, None) → exactly one is None → False.",
        complexity="Time O(min(n, m)) — stops at the first mismatch. Space O(h).",
        pitfalls="- Comparing only values from one traversal order (`[1,2]` and `[2,None,1]` share an inorder).\n- Checking `p.val` before checking for None.",
        follow_up="This function is the inner loop of *Subtree of Another Tree*.",
    ),
),
# ============================================================================================
dict(
    id="subtree-of-another-tree",
    title="Subtree of Another Tree",
    difficulty="Easy",
    pattern="Trees — DFS + Same Tree",
    leetcode="https://leetcode.com/problems/subtree-of-another-tree/",
    neetcode="https://neetcode.io/problems/subtree-of-a-binary-tree",
    entry="isSubtree",
    arg_types=["tree", "tree"],
    description=r"""
Return `True` if `subRoot` appears inside `root` as a **complete subtree**: some node of `root` together
with *all* of its descendants is identical (same shape and values) to `subRoot`. A tree counts as a subtree
of itself.

**Constraints**

- `root` has 1 to 2000 nodes, `subRoot` has 1 to 1000 nodes, values in `[-10^4, 10^4]`.

**Example 1:** `root = [3,4,5,1,2], subRoot = [4,1,2]` → `True`

**Example 2:** `root = [3,4,5,1,2,None,None,None,None,0], subRoot = [4,1,2]` → `False`
(the 4-subtree of `root` has an extra node 0 below the 2)
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def isSubtree(self, root: Optional[TreeNode], subRoot: Optional[TreeNode]) -> bool:
        pass
''',
    solution='''class Solution:
    def isSubtree(self, root, subRoot):
        def same(a, b):
            if not a and not b:
                return True
            if not a or not b or a.val != b.val:
                return False
            return same(a.left, b.left) and same(a.right, b.right)
        stack = [root]
        while stack:
            node = stack.pop()
            if node:
                if node.val == subRoot.val and same(node, subRoot):
                    return True
                stack.append(node.left)
                stack.append(node.right)
        return False
''',
    tests=[[[3, 4, 5, 1, 2], [4, 1, 2]], [[3, 4, 5, 1, 2, None, None, None, None, 0], [4, 1, 2]], [[1], [1]], [[1, 1], [1]],
           [[1, 2, 3], [1, 2]], [[2, 2, 2, 2, None, None, 2, 2], [2, 2]], [[12], [2]], [[3, 4, 5, 1, None, 2], [3, 1, 2]],
           [[1, None, 1, None, 1, None, 1, None, 1, None, 1, 2], [1, None, 1, 2]],
           [random_tree(2000, 9, 0, 3), [1, 2]], [skewed([1] * 450 + [2]), skewed([1] * 30 + [2])],
           [skewed([1] * 450 + [2]), skewed([1] * 30 + [3])]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def isSubtree(self, root, subRoot):
        # "prefix" match: ignores extra nodes below subRoot's leaves
        def match(a, b):
            if not b:
                return True
            if not a or a.val != b.val:
                return False
            return match(a.left, b.left) and match(a.right, b.right)
        def walk(n):
            return bool(n) and (match(n, subRoot) or walk(n.left) or walk(n.right))
        return walk(root)
''',
        '''class Solution:
    def isSubtree(self, root, subRoot):
        def same(a, b):
            if not a and not b:
                return True
            if not a or not b or a.val != b.val:
                return False
            return same(a.left, b.left) and same(a.right, b.right)
        return same(root, subRoot) or same(root.left, subRoot) or same(root.right, subRoot)   # only top 2 levels
''',
    ],
    guide=dict(
        prereqs="*Same Tree*.",
        intuition="Every node of `root` is a candidate starting point. At each candidate, run the *Same Tree* check against `subRoot`.",
        hints=["Write `same(a, b)` first.",
               "Traverse every node of `root`; return True as soon as `same(node, subRoot)` holds.",
               "Quick filter: only call `same` when the values match."],
        brute_force="The nested approach above *is* the standard answer: O(n·m) worst case. A faster alternative serialises both trees (with null markers and delimiters) and does substring search (KMP) or tree hashing: O(n + m).",
        approach="Example 2: candidates 3 (fails at root value), 4 (values match; left 1 = 1; right 2 vs 2, then 2 has left child 0 in `root` but None in `subRoot` → not same), 5, 1, 2, 0 all fail → False.",
        complexity="Time O(n·m) worst case (n = |root|, m = |subRoot|), typically much faster. Space O(h).",
        pitfalls="- Matching a *prefix* of the subtree (forgetting that the leaves of `subRoot` must also be leaves in `root`).\n- Serialising without null markers or without delimiters (`12` vs `2`) when using the string approach.",
        follow_up="Merkle-style hashing of subtrees: Find Duplicate Subtrees (LeetCode 652).",
    ),
),
# ============================================================================================
dict(
    id="path-sum",
    title="Path Sum",
    difficulty="Easy",
    pattern="Trees — Passing State Down",
    leetcode="https://leetcode.com/problems/path-sum/",
    entry="hasPathSum",
    arg_types=["tree", None],
    description=r"""
Is there a path from the root down to a **leaf** (a node with no children) whose values add up to
`targetSum`? Return `True` or `False`.

**Constraints**

- 0 to 5000 nodes, `-1000 <= Node.val <= 1000`, `-1000 <= targetSum <= 1000` (the judge's large case uses a bigger target).
- An empty tree has no paths at all.

**Arguments:** `root` (tree format below) and the integer `targetSum`.

**Example 1:** `root = [5,4,8,11,None,13,4,7,2,None,None,None,1], targetSum = 22` → `True` (5+4+11+2)

**Example 2:** `root = [1,2,3], targetSum = 5` → `False`

**Example 3:** `root = [], targetSum = 0` → `False`
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def hasPathSum(self, root: Optional[TreeNode], targetSum: int) -> bool:
        pass
''',
    solution='''class Solution:
    def hasPathSum(self, root, targetSum):
        stack = [(root, targetSum)]
        while stack:
            node, rem = stack.pop()
            if not node:
                continue
            rem -= node.val
            if not node.left and not node.right and rem == 0:
                return True
            stack.append((node.left, rem))
            stack.append((node.right, rem))
        return False
''',
    tests=[[[5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, 1], 22], [[1, 2, 3], 5], [[], 0], [[1, 2], 1], [[1, 2], 3],
           [[1], 1], [[-2, None, -3], -5], [[1, -2, -3, 1, 3, -2, None, -1], -1], [[1, 2, None, 3, None, 4], 6],
           [SKEW_R, sum(range(1, 501))], [SKEW_R, 3], [BIG5, 0]],
    wrong_solutions=[
        '''class Solution:
    def hasPathSum(self, root, targetSum):
        # accepts paths that stop at ANY node, not only at leaves
        def dfs(n, rem):
            if not n:
                return False
            rem -= n.val
            return rem == 0 or dfs(n.left, rem) or dfs(n.right, rem)
        return dfs(root, targetSum)
''',
        '''class Solution:
    def hasPathSum(self, root, targetSum):
        def dfs(n, rem):
            if not n:
                return rem == 0          # None child of a one-child node is not a leaf
            return dfs(n.left, rem - n.val) or dfs(n.right, rem - n.val)
        return dfs(root, targetSum)
''',
    ],
    guide=dict(
        prereqs="DFS; the idea of carrying information *down* the recursion — lesson *Returning values up the tree*.",
        intuition="As you walk down, subtract each node's value from the target. When you reach a leaf, the path works exactly if what remains is 0.",
        hints=["Pass the remaining sum to the children: `rem - node.val`.",
               "The check belongs at **leaves**, i.e. nodes with neither child.",
               "An empty root returns False — even when the target is 0."],
        brute_force="List every root-to-leaf path explicitly and sum each: O(n·h).",
        approach="Example 1: 5 → rem 17 → 4 → 13 → 11 → 2 → leaf 2 → 0 ✔. The reference does this with an explicit stack of `(node, remaining)` pairs.",
        complexity="Time O(n), space O(h).",
        pitfalls="- Treating a `None` child of a one-child node as the end of a path: in `[1,2]` with target 1, the root is *not* a leaf.\n- Returning early on negative remainders — values can be negative.",
        follow_up="Path Sum II (list the paths), Path Sum III (paths may start anywhere — prefix sums on a tree).",
    ),
),
# ============================================================================================
dict(
    id="diameter-of-binary-tree",
    title="Diameter of Binary Tree",
    difficulty="Easy",
    pattern="Trees — Return Values Up",
    leetcode="https://leetcode.com/problems/diameter-of-binary-tree/",
    neetcode="https://neetcode.io/problems/binary-tree-diameter",
    entry="diameterOfBinaryTree",
    arg_types=["tree"],
    description=r"""
The **diameter** of a binary tree is the number of **edges** on the longest path between any two nodes.
The path may or may not go through the root. Return the diameter.

**Constraints**

- 1 to $10^4$ nodes, `-100 <= Node.val <= 100`.

**Example 1:** `root = [1,2,3,4,5]` → `3` (path 4–2–1–3 or 5–2–1–3)

**Example 2:** `root = [1,2]` → `1`
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def diameterOfBinaryTree(self, root: Optional[TreeNode]) -> int:
        pass
''',
    solution='''class Solution:
    def diameterOfBinaryTree(self, root):
        best = 0
        def height(node):          # number of nodes on the longest downward path
            nonlocal best
            if not node:
                return 0
            l, r = height(node.left), height(node.right)
            best = max(best, l + r)
            return 1 + max(l, r)
        height(root)
        return best
''',
    tests=[[[1, 2, 3, 4, 5]], [[1, 2]], [[1]], [[1, 2, 3]], [[1, None, 2, None, 3]],
           [[4, -7, -3, None, None, -9, -3, 9, -7, -4, None, 6, None, -6, -6, None, None, 0, 6, 5, None, 9, None, None, -1, -4, None, None, None, -2]],
           [[1, 2, None, 3, 4, 5, None, None, 6, 7, None, None, 8]], [SKEW_L], [BIG], [COMPLETE]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def diameterOfBinaryTree(self, root):
        def h(n):
            return 1 + max(h(n.left), h(n.right)) if n else 0
        return h(root.left) + h(root.right)     # assumes the path passes through the root
''',
    ],
    guide=dict(
        prereqs="Height of a tree; the *return values up the tree* pattern.",
        intuition="Any path has a single highest node, where it 'bends'. If the bend is at node `v`, the longest such path is `height(left) + height(right)` edges. So compute heights bottom-up and, at every node, update a global best with the bend through that node.",
        hints=["The longest path does not have to pass through the root — test `[1,2,None,3,4,5,None,None,6]`-like shapes.",
               "One DFS can return each subtree's height while recording the best `left + right` seen so far.",
               "Return `1 + max(l, r)` to the parent but record `l + r` as a candidate answer."],
        brute_force="For every node, compute the heights of its two subtrees from scratch: O(n²) on a skewed tree.",
        approach="""Example 1, heights in nodes (h(None)=0): h(4)=h(5)=1, h(2)=2 with candidate 1+1=2, h(3)=1, at root candidate 2+1=3 ✔.

The function does two jobs: it **returns** what the parent needs (height) and **records** what the problem asks (diameter). That split is the heart of the lesson *Returning values up the tree*.""",
        complexity="Time O(n), space O(h).",
        pitfalls="- Counting nodes instead of edges (off by one).\n- Assuming the answer passes through the root.\n- Recomputing heights in nested recursion (O(n²)).",
        follow_up="*Binary Tree Maximum Path Sum* is the weighted version of this exact pattern.",
    ),
),
# ============================================================================================
dict(
    id="balanced-binary-tree",
    title="Balanced Binary Tree",
    difficulty="Easy",
    pattern="Trees — Return Values Up",
    leetcode="https://leetcode.com/problems/balanced-binary-tree/",
    neetcode="https://neetcode.io/problems/balanced-binary-tree",
    entry="isBalanced",
    arg_types=["tree"],
    description=r"""
A binary tree is **height-balanced** if, at *every* node, the heights of the left and right subtrees differ
by at most 1. Return whether the given tree is height-balanced. The empty tree is balanced.

**Constraints**

- 0 to 5000 nodes, `-10^4 <= Node.val <= 10^4`.

**Example 1:** `root = [3,9,20,None,None,15,7]` → `True`

**Example 2:** `root = [1,2,2,3,3,None,None,4,4]` → `False`

**Example 3:** `root = []` → `True`
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def isBalanced(self, root: Optional[TreeNode]) -> bool:
        pass
''',
    solution='''class Solution:
    def isBalanced(self, root):
        def h(node):                 # height, or -1 if unbalanced somewhere below
            if not node:
                return 0
            l = h(node.left)
            if l < 0:
                return -1
            r = h(node.right)
            if r < 0 or abs(l - r) > 1:
                return -1
            return 1 + max(l, r)
        return h(root) >= 0
''',
    tests=[[[3, 9, 20, None, None, 15, 7]], [[1, 2, 2, 3, 3, None, None, 4, 4]], [[]], [[1]], [[1, 2]], [[1, None, 2, None, 3]],
           [[1, 2, 2, 3, None, None, 3, 4, None, None, 4]], [[1, 2, 3, 4, 5, None, 6, 7]], [COMPLETE[:5000]], [SKEW_R],
           [balanced_bst(1, 4000)], [complete(range(4000)) + [None] * 20]],
    wrong_solutions=[
        '''class Solution:
    def isBalanced(self, root):
        def h(n):
            return 1 + max(h(n.left), h(n.right)) if n else 0
        return not root or abs(h(root.left) - h(root.right)) <= 1     # only checks the root
''',
    ],
    guide=dict(
        prereqs="Height; post-order DFS; lesson *Returning values up the tree*.",
        intuition="A node needs its children's heights to check itself, so compute heights bottom-up. Use a sentinel (-1) to signal 'already unbalanced below', which lets every ancestor fail fast.",
        hints=["Checking only the root is not enough — see `[1,2,2,3,None,None,3,4,None,None,4]`.",
               "Calling a separate `height()` at every node is O(n²) on skewed trees.",
               "Return the height normally, or -1 if any subtree is unbalanced; propagate -1 upward."],
        brute_force="`isBalanced(n) = abs(height(n.left) - height(n.right)) <= 1 and isBalanced(n.left) and isBalanced(n.right)` — correct but O(n²) worst case (O(n log n) on balanced trees).",
        approach="On `[1,2,2,3,3,None,None,4,4]`: h(4)=1 (both), h(3 left)=2, h(3 right)=1, h(2 left)=3; h(2 right)=1; at root |3-1| = 2 → -1 → False.",
        complexity="Time O(n), space O(h).",
        pitfalls="- Only checking the root.\n- Forgetting to propagate the -1 sentinel (an unbalanced subtree with equal 'heights' can slip through).",
        follow_up="AVL trees keep exactly this invariant with rotations — see Goodrich ch. 11.3.",
    ),
),
# ============================================================================================
dict(
    id="binary-tree-level-order-traversal",
    title="Binary Tree Level Order Traversal",
    difficulty="Medium",
    pattern="Trees — BFS",
    leetcode="https://leetcode.com/problems/binary-tree-level-order-traversal/",
    neetcode="https://neetcode.io/problems/level-order-traversal-of-binary-tree",
    entry="levelOrder",
    arg_types=["tree"],
    description=r"""
Return the values of a binary tree **level by level**: a list containing one inner list per depth, top to
bottom, with each inner list ordered left to right.

**Constraints**

- 0 to 2000 nodes classically (judge: up to 10,000), `-1000 <= Node.val <= 1000`.

**Example 1:** `root = [3,9,20,None,None,15,7]` → `[[3],[9,20],[15,7]]`

**Example 2:** `root = [1]` → `[[1]]`

**Example 3:** `root = []` → `[]`
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def levelOrder(self, root: Optional[TreeNode]) -> List[List[int]]:
        pass
''',
    solution='''class Solution:
    def levelOrder(self, root):
        res = []
        q = collections.deque([root] if root else [])
        while q:
            level = []
            for _ in range(len(q)):
                node = q.popleft()
                level.append(node.val)
                if node.left:
                    q.append(node.left)
                if node.right:
                    q.append(node.right)
            res.append(level)
        return res
''',
    tests=[[[3, 9, 20, None, None, 15, 7]], [[1]], [[]], [[1, 2]], [[1, None, 2]], [[1, 2, 3, 4, None, None, 5]],
           [[1, 2, 3, 4, 5, 6, 7, 8]], [SKEW_L], [BIG], [complete(range(3000))]],
    wrong_solutions=[
        '''class Solution:
    def levelOrder(self, root):
        res = []
        q = collections.deque([root] if root else [])
        while q:
            level = []
            for _ in range(len(q)):
                node = q.popleft()
                level.append(node.val)
                if node.right:              # right before left
                    q.append(node.right)
                if node.left:
                    q.append(node.left)
            res.append(level)
        return res
''',
        '''class Solution:
    def levelOrder(self, root):
        out = []
        q = collections.deque([root] if root else [])
        while q:
            n = q.popleft()
            out.append([n.val])           # one list per node, not per level
            for c in (n.left, n.right):
                if c:
                    q.append(c)
        return out
''',
    ],
    guide=dict(
        prereqs="Queues (`collections.deque`); lesson *Traversals: DFS and BFS*.",
        intuition="A queue processes nodes in the order they were discovered, which is exactly top-to-bottom, left-to-right. The trick to grouping by level: at the start of each round, the queue holds *exactly* one level — so process `len(q)` nodes and stop.",
        hints=["Use `collections.deque` — `list.pop(0)` is O(n).",
               "Freeze the level size with `for _ in range(len(q))` before you start appending children.",
               "DFS works too: pass the depth down and append to `res[depth]`."],
        brute_force="Compute the depth of every node with DFS, then bucket values by depth — same O(n), just less direct.",
        approach="`[3,9,20,None,None,15,7]`: q = [3] → level [3], q = [9,20] → level [9,20], q = [15,7] → level [15,7], q empty.",
        complexity="Time O(n), space O(w) where w is the maximum width (up to n/2 for a complete tree).",
        pitfalls="- Using `len(q)` *inside* the loop condition instead of freezing it.\n- Pushing `None` children and then crashing on `.val`.",
        follow_up="Zigzag order (103), bottom-up (107), averages per level (637), and *Binary Tree Right Side View*.",
    ),
),
# ============================================================================================
dict(
    id="binary-tree-right-side-view",
    title="Binary Tree Right Side View",
    difficulty="Medium",
    pattern="Trees — BFS",
    leetcode="https://leetcode.com/problems/binary-tree-right-side-view/",
    neetcode="https://neetcode.io/problems/binary-tree-right-side-view",
    entry="rightSideView",
    arg_types=["tree"],
    description=r"""
Picture yourself standing to the right of a binary tree. For each level, you see only the **rightmost**
node. Return those values from top to bottom.

**Constraints**

- 0 to 100 nodes classically (judge: up to 10,000), `-100 <= Node.val <= 100`.

**Example 1:** `root = [1,2,3,None,5,None,4]` → `[1,3,4]`

**Example 2:** `root = [1,2,3,4]` → `[1,3,4]` (the 4 is visible because nothing on the right is that deep)

**Example 3:** `root = []` → `[]`
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def rightSideView(self, root: Optional[TreeNode]) -> List[int]:
        pass
''',
    solution='''class Solution:
    def rightSideView(self, root):
        res = []
        q = collections.deque([root] if root else [])
        while q:
            res.append(q[-1].val)
            for _ in range(len(q)):
                node = q.popleft()
                if node.left:
                    q.append(node.left)
                if node.right:
                    q.append(node.right)
        return res
''',
    tests=[[[1, 2, 3, None, 5, None, 4]], [[1, 2, 3, 4]], [[]], [[1, None, 3]], [[1, 2]], [[1, 2, 3, 4, 5, 6, 7, None, None, 8]],
           [SKEW_L], [SKEW_R], [BIG], [COMPLETE]],
    wrong_solutions=[
        '''class Solution:
    def rightSideView(self, root):
        res = []
        while root:                       # walks right children only
            res.append(root.val)
            root = root.right
        return res
''',
    ],
    guide=dict(
        prereqs="*Binary Tree Level Order Traversal*.",
        intuition="Do a level-order traversal and keep the last node of every level.",
        hints=["Following `.right` pointers only fails when the left side is deeper (Example 2).",
               "In BFS, after building each level, the queue's last element is that level's rightmost node.",
               "DFS alternative: visit right child first and record a node when its depth equals `len(res)`."],
        brute_force="Full level-order traversal and take `level[-1]` of each — that's already optimal, just with extra lists.",
        approach="`[1,2,3,4]`: q=[1] → see 1; q=[2,3] → see 3; q=[4] → see 4. Answer `[1,3,4]`.",
        complexity="Time O(n), space O(w).",
        pitfalls="Assuming the rightmost node is always reached through right children.",
        follow_up="Left side view (mirror), or 'boundary of binary tree' (545).",
    ),
),
# ============================================================================================
dict(
    id="count-good-nodes-in-binary-tree",
    title="Count Good Nodes in Binary Tree",
    difficulty="Medium",
    pattern="Trees — Passing State Down",
    leetcode="https://leetcode.com/problems/count-good-nodes-in-binary-tree/",
    neetcode="https://neetcode.io/problems/count-good-nodes-in-binary-tree",
    entry="goodNodes",
    arg_types=["tree"],
    description=r"""
A node `X` is **good** if no node on the path from the root to `X` (inclusive of the root, exclusive of X)
has a value greater than `X.val`. In other words, `X` is at least as large as everything above it. The root
is always good. Count the good nodes.

**Constraints**

- 1 to $10^5$ nodes classically (judge: up to 10,000), values in `[-10^4, 10^4]`.

**Example 1:** `root = [3,1,4,3,None,1,5]` → `4` (3, the 4, the lower 3 and 5)

**Example 2:** `root = [3,3,None,4,2]` → `3`

**Example 3:** `root = [1]` → `1`
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def goodNodes(self, root: TreeNode) -> int:
        pass
''',
    solution='''class Solution:
    def goodNodes(self, root):
        count = 0
        stack = [(root, float("-inf"))]
        while stack:
            node, best = stack.pop()
            if not node:
                continue
            if node.val >= best:
                count += 1
                best = node.val
            stack.append((node.left, best))
            stack.append((node.right, best))
        return count
''',
    tests=[[[3, 1, 4, 3, None, 1, 5]], [[3, 3, None, 4, 2]], [[1]], [[2, None, 4, 10, 8, None, None, 4]], [[9, None, 3, 6]],
           [[-1, 5, -2, 4, 4, 2, -2, None, None, -4, None, -2, 3, None, -2, 0, None, -1, None, -3, None, -4, -3, 3, None, None, None, None, None, None, None, 3, -3]],
           [[5, 5, 5, 5]], [SKEW_R], [list(reversed(SKEW_R))[::-1]], [BIG], [COMPLETE]],
    wrong_solutions=[
        '''class Solution:
    def goodNodes(self, root):
        # compares with the parent only
        count = 1
        stack = [root]
        while stack:
            n = stack.pop()
            for c in (n.left, n.right):
                if c:
                    if c.val >= n.val:
                        count += 1
                    stack.append(c)
        return count
''',
        '''class Solution:
    def goodNodes(self, root):
        count = 0
        stack = [(root, float("-inf"))]
        while stack:
            node, best = stack.pop()
            if not node:
                continue
            if node.val > best:            # strict: misses equal values
                count += 1
                best = node.val
            stack.append((node.left, best))
            stack.append((node.right, best))
        return count
''',
    ],
    guide=dict(
        prereqs="DFS with an accumulator carried downward — lesson *Returning values up the tree* (the 'pass state down' half).",
        intuition="Whether a node is good depends only on the **maximum value on the path above it**. Carry that maximum down as a parameter.",
        hints=["Comparing to the parent alone is not enough: an ancestor further up may be larger.",
               "DFS with `(node, max_so_far)`; the root starts with `-inf` (or its own value).",
               "A node is good if `node.val >= max_so_far`; pass `max(max_so_far, node.val)` to the children."],
        brute_force="For every node, walk back up the path (needs parent pointers or stored paths) and check: O(n·h).",
        approach="Example 1: 3 (max -inf) good → 1 (max 3) no → 3 (max 3) good; 4 (max 3) good → 1 (max 4) no, 5 (max 4) good. Total 4.",
        complexity="Time O(n), space O(h).",
        pitfalls="- Using `>` instead of `>=`: equal values count as good.\n- Updating a *shared* max variable instead of a per-path one (siblings would see each other's maximum).",
        follow_up="Maximum Difference Between Node and Ancestor (1026) carries both a min and a max down.",
    ),
),
# ============================================================================================
dict(
    id="lowest-common-ancestor-of-a-binary-search-tree",
    title="Lowest Common Ancestor of a Binary Search Tree",
    difficulty="Medium",
    pattern="Trees — BST Property",
    leetcode="https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-search-tree/",
    neetcode="https://neetcode.io/problems/lowest-common-ancestor-in-binary-search-tree",
    entry="judge",
    arg_types=["tree", None, None],
    description=r"""
In a binary search tree, the **lowest common ancestor** (LCA) of two nodes `p` and `q` is the deepest node that
has both of them in its subtree (a node is considered part of its own subtree, so a node can be the LCA of
itself and one of its descendants). Return the LCA.

**Constraints**

- 2 to $10^5$ nodes classically (judge: up to 10,000); all values are **distinct**; `p` and `q` both exist in the tree.

**Judge input format:** each test is `root, p, q`, where `root` is a level-order list and `p`, `q` are the
**values** of the two nodes. The small adapter at the bottom of the starter finds the two `TreeNode` objects,
calls your LeetCode-style `lowestCommonAncestor(root, p, q)` with real nodes, and reports the **value** of the
node you return.

**Example 1:** `root = [6,2,8,0,4,7,9,None,None,3,5], p = 2, q = 8` → `6`

**Example 2:** `root = [6,2,8,0,4,7,9,None,None,3,5], p = 2, q = 4` → `2`
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def lowestCommonAncestor(self, root: 'TreeNode', p: 'TreeNode', q: 'TreeNode') -> 'TreeNode':
        pass
''' + LCA_ADAPTER,
    solution='''class Solution:
    def lowestCommonAncestor(self, root, p, q):
        cur = root
        while cur:
            if p.val < cur.val and q.val < cur.val:
                cur = cur.left
            elif p.val > cur.val and q.val > cur.val:
                cur = cur.right
            else:
                return cur
''' + LCA_ADAPTER,
    tests=_lca_tests(),
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def lowestCommonAncestor(self, root, p, q):
        return root
''' + LCA_ADAPTER,
        '''class Solution:
    def lowestCommonAncestor(self, root, p, q):
        # stops as soon as p is on one side (wrong when both go the same way)
        cur = root
        while cur:
            if p.val < cur.val and q.val < cur.val:
                cur = cur.left
            else:
                return cur
''' + LCA_ADAPTER,
    ],
    guide=dict(
        prereqs="BST ordering property — lesson *Binary search trees*.",
        intuition="Start at the root. If both targets are smaller, the LCA must be in the left subtree; if both are larger, the right subtree. The first node where they 'split' (or where one of them *is* the current node) is the answer.",
        hints=["You never need to look at both subtrees — the BST ordering tells you which way to go.",
               "Compare `p.val` and `q.val` with `cur.val`.",
               "If they are on different sides, or one equals `cur.val`, return `cur`."],
        brute_force="The general-binary-tree LCA (LeetCode 236): post-order DFS returning 'found p or q' up the tree — O(n) and ignores the BST property.",
        approach="Example 1: at 6, p=2 < 6 < 8 = q → split → 6. Example 2: at 6 both < 6 → go to 2; `p.val == 2` → return 2.",
        complexity="Time O(h) — O(log n) in a balanced BST, O(n) when skewed. Space O(1) iteratively.",
        pitfalls="- Using `<=`/`>=` in the descend conditions (then you walk past a node that equals p or q).\n- Applying this shortcut to a general binary tree (no ordering) — it is only valid for BSTs.",
        follow_up="LCA of a general binary tree (236), LCA with parent pointers (1650) — the latter is *Intersection of Two Linked Lists* in disguise.",
    ),
),
# ============================================================================================
dict(
    id="insert-into-a-binary-search-tree",
    title="Insert into a Binary Search Tree",
    difficulty="Medium",
    pattern="Trees — BST Operations",
    leetcode="https://leetcode.com/problems/insert-into-a-binary-search-tree/",
    entry="insertIntoBST",
    arg_types=["tree", None],
    return_type="tree",
    checker=BST_CHECKER,
    description=r"""
Insert `val` into a binary search tree and return the (possibly new) root. `val` is guaranteed not to be in
the tree already. Several resulting trees can be valid; **any valid BST containing the original keys plus
`val` is accepted** (the judge checks the BST property and the key set, not the exact shape).

**Constraints**

- 0 to $10^4$ nodes, all keys distinct, `-10^8 <= Node.val, val <= 10^8`.

**Arguments:** `root` (level-order list) and the integer `val`.

**Example 1:** `root = [4,2,7,1,3], val = 5` → `[4,2,7,1,3,5]`

**Example 2:** `root = [], val = 5` → `[5]`
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def insertIntoBST(self, root: Optional[TreeNode], val: int) -> Optional[TreeNode]:
        pass
''',
    solution='''class Solution:
    def insertIntoBST(self, root, val):
        new = TreeNode(val)
        if not root:
            return new
        cur = root
        while True:
            if val < cur.val:
                if not cur.left:
                    cur.left = new
                    return root
                cur = cur.left
            else:
                if not cur.right:
                    cur.right = new
                    return root
                cur = cur.right
''',
    tests=[[[4, 2, 7, 1, 3], 5], [[], 5], [[40, 20, 60, 10, 30, 50, 70], 25], [[1], 0], [[1], 2], [[5, 3, 8], 4],
           [[5, 3, 8], 9], [skewed(list(range(1, 400)), "right"), 1000], [skewed(list(range(400, 0, -1)), "left"), -5],
           [BST_BIG, 10 ** 7], [BST_BIG, 7]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def insertIntoBST(self, root, val):
        if not root:
            return TreeNode(val)
        # always hangs the value off the root's left side
        root.left = TreeNode(val, root.left)
        return root
''',
        '''class Solution:
    def insertIntoBST(self, root, val):
        return root          # forgets to insert
''',
    ],
    guide=dict(
        prereqs="BST search — lesson *Binary search trees*.",
        intuition="Search for `val` as if it were in the tree. The search ends by stepping onto a `None` child — that empty spot is exactly where `val` belongs.",
        hints=["Handle the empty tree: return a new node.",
               "Walk down: go left if `val < cur.val`, else right.",
               "When the child in that direction is `None`, attach the new node there."],
        brute_force="Collect all keys, add `val`, sort, and rebuild a balanced BST — O(n log n) and much more work than needed.",
        approach="Example 1: 5 > 4 → right to 7; 5 < 7 and 7.left is None → attach. Level order: `[4,2,7,1,3,5]`.",
        complexity="Time O(h), space O(1) iteratively (O(h) recursively).",
        pitfalls="- Forgetting the empty-tree case.\n- Returning the new node instead of the original root.",
        follow_up="Self-balancing trees (AVL, red-black) do this insertion followed by rotations to keep h = O(log n).",
    ),
),
# ============================================================================================
dict(
    id="delete-node-in-a-bst",
    title="Delete Node in a BST",
    difficulty="Medium",
    pattern="Trees — BST Operations",
    leetcode="https://leetcode.com/problems/delete-node-in-a-bst/",
    entry="deleteNode",
    arg_types=["tree", None],
    return_type="tree",
    checker=BST_CHECKER,
    description=r"""
Remove the node whose value is `key` from a binary search tree (if it exists) and return the root of the
resulting tree. The result must still be a valid BST. Several shapes are valid; **any valid BST holding the
remaining keys is accepted**.

**Constraints**

- 0 to $10^4$ nodes, distinct keys, `-10^5 <= Node.val, key <= 10^5`; `key` may be absent.
- Follow-up: O(height) time.

**Arguments:** `root` (level-order list) and the integer `key`.

**Example 1:** `root = [5,3,6,2,4,None,7], key = 3` → e.g. `[5,4,6,2,None,None,7]`

**Example 2:** `root = [5,3,6,2,4,None,7], key = 0` → `[5,3,6,2,4,None,7]`

**Example 3:** `root = [], key = 0` → `[]`
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def deleteNode(self, root: Optional[TreeNode], key: int) -> Optional[TreeNode]:
        pass
''',
    solution='''class Solution:
    def deleteNode(self, root, key):
        if not root:
            return None
        if key < root.val:
            root.left = self.deleteNode(root.left, key)
        elif key > root.val:
            root.right = self.deleteNode(root.right, key)
        else:
            if not root.left:
                return root.right
            if not root.right:
                return root.left
            succ = root.right
            while succ.left:
                succ = succ.left
            root.val = succ.val
            root.right = self.deleteNode(root.right, succ.val)
        return root
''',
    tests=[[[5, 3, 6, 2, 4, None, 7], 3], [[5, 3, 6, 2, 4, None, 7], 0], [[], 0], [[1], 1], [[2, 1], 2], [[2, None, 3], 2],
           [[5, 3, 6, 2, 4, None, 7], 5], [[5, 3, 6, 2, 4, None, 7], 7], [[50, 30, 70, 20, 40, 60, 80, None, None, 35, 45], 30],
           [skewed(list(range(1, 400)), "right"), 200], [BST_BIG, inorder(BST_BIG)[2500]], [BST_BIG, BST_BIG[0]]],
    wrong_solutions=[
        '''class Solution:
    def deleteNode(self, root, key):
        # drops the whole subtree of the deleted node
        if not root:
            return None
        if root.val == key:
            return None
        if key < root.val:
            root.left = self.deleteNode(root.left, key)
        else:
            root.right = self.deleteNode(root.right, key)
        return root
''',
        '''class Solution:
    def deleteNode(self, root, key):
        if not root:
            return None
        if key < root.val:
            root.left = self.deleteNode(root.left, key)
        elif key > root.val:
            root.right = self.deleteNode(root.right, key)
        else:
            if not root.left:
                return root.right
            # keeps only the left subtree when there are two children
            return root.left
        return root
''',
    ],
    guide=dict(
        prereqs="BST search and insert; inorder successor — lesson *Binary search trees*.",
        intuition="Deleting a leaf or a node with one child is easy: let its parent point to the only child (or None). For a node with **two** children, copy in its inorder successor (smallest key of the right subtree — it has no left child) and then delete that successor from the right subtree, which is an easy case.",
        hints=["First find the node, recursing left/right and re-assigning `root.left = deleteNode(root.left, key)`.",
               "Zero or one child: return the other child.",
               "Two children: find the minimum of `root.right`, copy its value, delete it from `root.right`."],
        brute_force="Inorder-traverse into a sorted list, remove `key`, rebuild a balanced BST: O(n) time and space.",
        approach="""Example 1, delete 3 (two children 2 and 4): successor = min of right subtree = 4. Copy 4 into the node, delete 4 from the right subtree (it is a leaf). Result `[5,4,6,2,None,None,7]`.

Using the inorder **predecessor** (max of the left subtree) is equally valid — that's why the judge accepts any valid BST.""",
        complexity="Time O(h), space O(h) for the recursion.",
        pitfalls="- Forgetting to re-link: the recursive call's return value must be assigned to `root.left`/`root.right`.\n- Losing a subtree when the node has two children.\n- Not handling an absent key (should return the tree unchanged).",
        follow_up="Goodrich §11.1.3 does the same with positions; balanced trees add rebalancing after the delete.",
    ),
),
# ============================================================================================
dict(
    id="validate-binary-search-tree",
    title="Validate Binary Search Tree",
    difficulty="Medium",
    pattern="Trees — BST Bounds",
    leetcode="https://leetcode.com/problems/validate-binary-search-tree/",
    neetcode="https://neetcode.io/problems/valid-binary-search-tree",
    entry="isValidBST",
    arg_types=["tree"],
    description=r"""
Check whether a binary tree is a valid **binary search tree**: for every node, *all* keys in its left
subtree are strictly smaller than the node's key and *all* keys in its right subtree are strictly larger.
(Equal keys are not allowed.)

**Constraints**

- 1 to $10^4$ nodes, `-2^31 <= Node.val <= 2^31 - 1`.

**Example 1:** `root = [2,1,3]` → `True`

**Example 2:** `root = [5,1,4,None,None,3,6]` → `False` (4 is in the right subtree of 5 but smaller)

**Example 3:** `root = [5,4,6,None,None,3,7]` → `False` (3 is below 6 correctly, but it is in 5's right subtree)
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def isValidBST(self, root: Optional[TreeNode]) -> bool:
        pass
''',
    solution='''class Solution:
    def isValidBST(self, root):
        stack = [(root, float("-inf"), float("inf"))]
        while stack:
            node, lo, hi = stack.pop()
            if not node:
                continue
            if not (lo < node.val < hi):
                return False
            stack.append((node.left, lo, node.val))
            stack.append((node.right, node.val, hi))
        return True
''',
    tests=[[[2, 1, 3]], [[5, 1, 4, None, None, 3, 6]], [[5, 4, 6, None, None, 3, 7]], [[1]], [[2, 2, 2]], [[1, 1]],
           [[2147483647]], [[-2147483648, None, 2147483647]], [[3, 1, 5, 0, 2, 4, 6]], [[32, 26, 47, 19, None, None, 56, None, 27]],
           [BST_BIG], [BST_BAL], [BST_BAL[:-1] + [10 ** 9]], [SKEW_R]],
    wrong_solutions=[
        '''class Solution:
    def isValidBST(self, root):
        # only compares each node with its direct children
        stack = [root]
        while stack:
            n = stack.pop()
            if not n:
                continue
            if n.left and n.left.val >= n.val:
                return False
            if n.right and n.right.val <= n.val:
                return False
            stack += [n.left, n.right]
        return True
''',
        '''class Solution:
    def isValidBST(self, root):
        vals = []
        def ino(n):
            if n:
                ino(n.left); vals.append(n.val); ino(n.right)
        ino(root)
        return vals == sorted(vals)        # allows duplicates
''',
    ],
    guide=dict(
        prereqs="BST definition; passing bounds down a DFS.",
        intuition="Each node does not just have to beat its parent — it has to fit inside an **interval** determined by all its ancestors. Going left tightens the upper bound to the parent's key; going right tightens the lower bound.",
        hints=["Checking `left.val < node.val < right.val` at each node is not sufficient (Example 3).",
               "Carry `(low, high)` bounds down; the root starts with `(-inf, +inf)`.",
               "Alternative: an inorder traversal of a BST must be *strictly* increasing."],
        brute_force="For each node, compute the max of its left subtree and the min of its right subtree from scratch: O(n²) worst case.",
        approach="Example 3: 5 (−∞,∞) ok; 4 (−∞,5) ok; 6 (5,∞) ok; 3 (5,6) ✗ → False. Using `float('inf')` bounds avoids the classic bug of using `±2^31` sentinels when keys can equal those extremes.",
        complexity="Time O(n), space O(h).",
        pitfalls="- Local parent/child comparison only.\n- Allowing duplicates (`<=`).\n- Sentinels like `-2**31` that collide with real keys — use infinity or `None`.",
        follow_up="Recover a BST where exactly two nodes were swapped (99), using the same inorder idea.",
    ),
),
# ============================================================================================
dict(
    id="kth-smallest-element-in-a-bst",
    title="Kth Smallest Element in a BST",
    difficulty="Medium",
    pattern="Trees — BST Inorder",
    leetcode="https://leetcode.com/problems/kth-smallest-element-in-a-bst/",
    neetcode="https://neetcode.io/problems/kth-smallest-integer-in-bst",
    entry="kthSmallest",
    arg_types=["tree", None],
    description=r"""
Return the `k`-th smallest key (1-indexed) stored in a binary search tree.

**Constraints**

- The tree has `n` nodes, `1 <= k <= n <= 10^4`, `0 <= Node.val <= 10^4` classically (the judge's large BST uses bigger keys), keys distinct.
- Follow-up: what if the BST is modified often and you must answer many such queries?

**Arguments:** `root` (level-order list) and the integer `k`.

**Example 1:** `root = [3,1,4,None,2], k = 1` → `1`

**Example 2:** `root = [5,3,6,2,4,None,None,1], k = 3` → `3`
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def kthSmallest(self, root: Optional[TreeNode], k: int) -> int:
        pass
''',
    solution='''class Solution:
    def kthSmallest(self, root, k):
        stack, cur = [], root
        while True:
            while cur:
                stack.append(cur)
                cur = cur.left
            cur = stack.pop()
            k -= 1
            if k == 0:
                return cur.val
            cur = cur.right
''',
    tests=[[[3, 1, 4, None, 2], 1], [[5, 3, 6, 2, 4, None, None, 1], 3], [[1], 1], [[2, 1, 3], 3], [[2, 1, 3], 2],
           [[5, 3, 6, 2, 4, None, None, 1], 6], [skewed(list(range(400, 0, -1)), "left"), 400],
           [skewed(list(range(1, 401)), "right"), 1], [BST_BIG, 1], [BST_BIG, 5000], [BST_BIG, 4242], [BST_BAL, 2048]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def kthSmallest(self, root, k):
        # k-th node in LEVEL order
        q = collections.deque([root])
        while q:
            n = q.popleft()
            k -= 1
            if k == 0:
                return n.val
            for c in (n.left, n.right):
                if c:
                    q.append(c)
''',
    ],
    guide=dict(
        prereqs="Inorder traversal of a BST yields keys in sorted order.",
        intuition="The inorder sequence of a BST is sorted, so the k-th smallest is the k-th node an inorder traversal visits. Stop as soon as you reach it.",
        hints=["Inorder traversal into a list and return `lst[k-1]` — O(n).",
               "Use the iterative inorder (stack) so you can stop early.",
               "Decrement k each time you pop; when it hits 0, return that node's value."],
        brute_force="Collect all values, sort, index: O(n log n) (or O(n) using inorder's sortedness).",
        approach="Example 2: inorder visits 1, 2, 3 → third pop is 3. The traversal does O(h + k) work.",
        complexity="Time O(h + k), space O(h).",
        pitfalls="- Using level order or pre-order.\n- Off-by-one with 1-indexed k.",
        follow_up="Frequent updates + queries: augment each node with the size of its subtree (an *order-statistic tree*); then each query is O(h): go left if `k <= size(left)`, else subtract.",
    ),
),
# ============================================================================================
dict(
    id="construct-binary-tree-from-preorder-and-inorder-traversal",
    title="Construct Binary Tree from Preorder and Inorder Traversal",
    difficulty="Medium",
    pattern="Trees — Construction",
    leetcode="https://leetcode.com/problems/construct-binary-tree-from-preorder-and-inorder-traversal/",
    neetcode="https://neetcode.io/problems/binary-tree-from-preorder-and-inorder-traversal",
    entry="buildTree",
    return_type="tree",
    description=r"""
You are given two lists describing the same binary tree: its **preorder** traversal (node, left, right) and
its **inorder** traversal (left, node, right). All values are distinct. Rebuild the tree and return its root.

**Constraints**

- `1 <= len(preorder) == len(inorder) <= 3000` (judge: up to 4,095), values distinct, in `[-3000, 3000]` classically.

**Arguments:** two plain Python lists. The returned tree is printed in level order.

**Example 1:** `preorder = [3,9,20,15,7], inorder = [9,3,15,20,7]` → `[3,9,20,None,None,15,7]`

**Example 2:** `preorder = [-1], inorder = [-1]` → `[-1]`
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def buildTree(self, preorder: List[int], inorder: List[int]) -> Optional[TreeNode]:
        pass
''',
    solution='''class Solution:
    def buildTree(self, preorder, inorder):
        where = {v: i for i, v in enumerate(inorder)}
        it = iter(preorder)
        def build(lo, hi):           # builds the subtree whose inorder slice is [lo, hi)
            if lo >= hi:
                return None
            val = next(it)
            node = TreeNode(val)
            mid = where[val]
            node.left = build(lo, mid)
            node.right = build(mid + 1, hi)
            return node
        return build(0, len(inorder))
''',
    tests=_build_tests(),
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def buildTree(self, preorder, inorder):
        # inserts preorder values as if it were a BST
        root = None
        for v in preorder:
            if root is None:
                root = TreeNode(v); continue
            cur = root
            while True:
                if v < cur.val:
                    if not cur.left:
                        cur.left = TreeNode(v); break
                    cur = cur.left
                else:
                    if not cur.right:
                        cur.right = TreeNode(v); break
                    cur = cur.right
        return root
''',
        '''class Solution:
    def buildTree(self, preorder, inorder):
        # always splits into left = next element, ignores inorder
        root = None
        for v in reversed(preorder):
            root = TreeNode(v, root)
        return root
''',
    ],
    guide=dict(
        prereqs="Pre/in-order traversals; recursion on index ranges — lesson *Binary search trees, construction and serialization*.",
        intuition="Preorder's first value is the root. Find that value in inorder: everything to its left is the left subtree, everything to its right the right subtree. The sizes tell you how to split preorder too. Recurse.",
        hints=["`preorder[0]` is the root; its index `mid` in `inorder` splits the inorder list.",
               "The left subtree has `mid` nodes, so its preorder is `preorder[1:mid+1]`.",
               "Avoid O(n) `index()` calls and slicing: precompute a value→index dict and consume preorder with a moving pointer/iterator."],
        brute_force="Slicing version: `root = preorder[0]; mid = inorder.index(root); left = build(preorder[1:mid+1], inorder[:mid]); right = build(preorder[mid+1:], inorder[mid+1:])` — O(n²) time due to slicing and `index`.",
        approach="""Example 1: root 3, inorder splits `[9] | 3 | [15,20,7]`. Left subtree: preorder `[9]` → leaf 9. Right: preorder `[20,15,7]`, inorder `[15,20,7]` → root 20 with 15 and 7.

The reference builds in preorder sequence (root, then left, then right), so the next unused preorder value is always the root of the subtree currently being built — just pull it from an iterator. Inorder bounds `[lo, hi)` say when a subtree is empty.""",
        complexity="Time O(n) with the dict; space O(n) for the dict plus O(h) recursion.",
        pitfalls="- Duplicated values break the 'find root in inorder' step — the problem guarantees distinct values.\n- Building the right subtree before the left when consuming preorder sequentially.",
        follow_up="Inorder + postorder (106) — consume postorder from the end and build right before left. Preorder + postorder (889) is not unique in general.",
    ),
),
# ============================================================================================
dict(
    id="binary-tree-maximum-path-sum",
    title="Binary Tree Maximum Path Sum",
    difficulty="Hard",
    pattern="Trees — Return Values Up",
    leetcode="https://leetcode.com/problems/binary-tree-maximum-path-sum/",
    neetcode="https://neetcode.io/problems/binary-tree-maximum-path-sum",
    entry="maxPathSum",
    arg_types=["tree"],
    description=r"""
A **path** is a sequence of nodes where consecutive nodes are joined by an edge and no node appears twice.
It need not pass through the root and need not start or end at a leaf, but it must contain at least one
node. Return the largest possible sum of node values along any path.

**Constraints**

- 1 to $3 \cdot 10^4$ nodes classically (judge: up to 10,000), `-1000 <= Node.val <= 1000`.

**Example 1:** `root = [1,2,3]` → `6` (2 → 1 → 3)

**Example 2:** `root = [-10,9,20,None,None,15,7]` → `42` (15 → 20 → 7)

**Example 3:** `root = [-3]` → `-3`
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def maxPathSum(self, root: Optional[TreeNode]) -> int:
        pass
''',
    solution='''class Solution:
    def maxPathSum(self, root):
        best = root.val
        def gain(node):              # best sum of a path that starts at node and goes down
            nonlocal best
            if not node:
                return 0
            l = max(gain(node.left), 0)
            r = max(gain(node.right), 0)
            best = max(best, node.val + l + r)
            return node.val + max(l, r)
        gain(root)
        return best
''',
    tests=[[[1, 2, 3]], [[-10, 9, 20, None, None, 15, 7]], [[-3]], [[2, -1]], [[-2, -1]], [[-1, -2, -3]], [[5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, 1]],
           [[1, -2, 3]], [[10, 2, 10, 20, 1, None, -25, None, None, None, None, 3, 4]], [skewed([-1] * 300 + [5] + [-1] * 100)],
           [BIG], [random_tree(5000, 11, -1000, -1)], [COMPLETE]],
    wrong_solutions=[
        '''class Solution:
    def maxPathSum(self, root):
        # best root-to-leaf path only
        def down(n):
            if not n:
                return float("-inf")
            if not n.left and not n.right:
                return n.val
            return n.val + max(down(n.left), down(n.right))
        return down(root)
''',
        '''class Solution:
    def maxPathSum(self, root):
        best = 0                     # wrong initial value: fails when all values are negative
        def gain(node):
            nonlocal best
            if not node:
                return 0
            l = max(gain(node.left), 0)
            r = max(gain(node.right), 0)
            best = max(best, node.val + l + r)
            return node.val + max(l, r)
        gain(root)
        return best
''',
    ],
    guide=dict(
        prereqs="*Diameter of Binary Tree*; lesson *Returning values up the tree*.",
        intuition="Same shape as the diameter: every path has a top node where it bends. At node `v`, the best path bending there is `v.val + best downward gain from left + best downward gain from right`, where a negative gain is replaced by 0 (just don't go that way). What you return upward is a path that does **not** bend: `v.val + max(left, right)`.",
        hints=["Define `gain(node)` = the best sum of a path that starts at `node` and goes downward.",
               "Clamp negative child gains to 0 — you may simply not extend into that subtree.",
               "Update a global answer with `node.val + left + right`, but return `node.val + max(left, right)`. Initialise the answer to `root.val`, not 0."],
        brute_force="Try every node as the bend and compute the best downward gains from scratch: O(n²).",
        approach="Example 2: gain(9)=9, gain(15)=15, gain(7)=7, at 20: candidate 20+15+7 = 42, returns 35. At -10: candidate -10+9+35 = 34. Answer 42.",
        complexity="Time O(n), space O(h).",
        pitfalls="- Returning `node.val + l + r` upward (a parent cannot use a path that already bends).\n- Initialising the answer to 0 (all-negative trees must return the largest single value).\n- Forgetting to clamp negative gains.",
        follow_up="Longest Univalue Path (687) and Longest ZigZag Path (1372) use the same 'record vs return' split.",
    ),
),
# ============================================================================================
dict(
    id="serialize-and-deserialize-binary-tree",
    title="Serialize and Deserialize Binary Tree",
    difficulty="Hard",
    pattern="Trees — Serialization",
    leetcode="https://leetcode.com/problems/serialize-and-deserialize-binary-tree/",
    neetcode="https://neetcode.io/problems/serialize-and-deserialize-binary-tree",
    entry="judge",
    arg_types=["tree"],
    return_type="tree",
    description=r"""
Design a `Codec` class with two methods:

- `serialize(root) -> str` turns a binary tree into a string.
- `deserialize(data) -> TreeNode` turns such a string back into an identical tree.

You choose the string format. The only requirement is the round trip: deserialising what you serialised must
give back a tree with the same shape and values.

**Constraints**

- 0 to $10^4$ nodes, `-1000 <= Node.val <= 1000` (values can be negative and repeat).

**Judge input format:** each test is one tree (level order). The adapter at the bottom of the starter runs
`Codec().deserialize(Codec().serialize(root))` using **two separate** `Codec` objects (so you cannot stash the
tree in `self`), checks that `serialize` returned a `str`, and prints the rebuilt tree. The expected output
is therefore the input tree itself.

**Example 1:** `root = [1,2,3,None,None,4,5]` → `[1,2,3,None,None,4,5]`

**Example 2:** `root = []` → `[]`
""" + TREE_FORMAT,
    starter=TN + '''class Codec:

    def serialize(self, root: Optional[TreeNode]) -> str:
        """Encodes a tree to a single string."""
        pass

    def deserialize(self, data: str) -> Optional[TreeNode]:
        """Decodes your encoded data to tree."""
        pass
''' + CODEC_ADAPTER,
    solution='''class Codec:
    def serialize(self, root):
        out, stack = [], [root]
        while stack:                       # iterative preorder with null markers
            node = stack.pop()
            if node is None:
                out.append("#")
            else:
                out.append(str(node.val))
                stack.append(node.right)
                stack.append(node.left)
        return ",".join(out)

    def deserialize(self, data):
        tokens = iter(data.split(","))
        def build():
            t = next(tokens)
            if t == "#":
                return None
            node = TreeNode(int(t))
            node.left = build()
            node.right = build()
            return node
        return build()
''' + CODEC_ADAPTER,
    tests=[[[1, 2, 3, None, None, 4, 5]], [[]], [[1]], [[-1000, 1000]], [[1, None, 2]], [[12, 1, 2]], [[1, 12, None, 2]],
           [[5, 5, 5, None, 5, 5]], [[4, -7, -3, None, None, -9, -3, 9, -7, -4, None, 6, None, -6, -6, None, None, 0, 6, 5, None, 9, None, None, -1, -4, None, None, None, -2]],
           [SKEW_L], [SKEW_R], [BIG], [complete(range(-500, 500))]],
    examples=2,
    wrong_solutions=[
        '''class Codec:
    # level order WITHOUT null markers, rebuilt as a complete tree
    def serialize(self, root):
        out, q = [], collections.deque([root] if root else [])
        while q:
            n = q.popleft()
            out.append(str(n.val))
            for c in (n.left, n.right):
                if c:
                    q.append(c)
        return " ".join(out)

    def deserialize(self, data):
        vals = [int(x) for x in data.split()]
        if not vals:
            return None
        nodes = [TreeNode(v) for v in vals]
        for i, n in enumerate(nodes):
            if 2 * i + 1 < len(nodes):
                n.left = nodes[2 * i + 1]
            if 2 * i + 2 < len(nodes):
                n.right = nodes[2 * i + 2]
        return nodes[0]
''' + CODEC_ADAPTER,
        '''class Codec:
    # digits glued together without separators
    def serialize(self, root):
        def go(n):
            return "#" if not n else str(n.val) + go(n.left) + go(n.right)
        return go(root)

    def deserialize(self, data):
        pos = 0
        def build():
            nonlocal pos
            if data[pos] == "#":
                pos += 1
                return None
            start = pos
            while pos < len(data) and data[pos] != "#":
                pos += 1
            node = TreeNode(int(data[start:pos]))
            node.left = build()
            node.right = build()
            return node
        return build()
''' + CODEC_ADAPTER,
    ],
    guide=dict(
        prereqs="Preorder traversal; lesson *Binary search trees, construction and serialization*.",
        intuition="A single traversal is ambiguous *unless* you also write down where the empty children are. Preorder with a null marker (`#`) for every missing child determines the tree uniquely, and it can be parsed back with the same recursion that produced it.",
        hints=["Pick a delimiter (`,`) so multi-digit and negative numbers survive.",
               "Serialise with preorder, writing `#` for every `None`.",
               "Deserialise with an iterator over the tokens: read a token; `#` → None; otherwise make a node, build its left, then its right."],
        brute_force="Serialising both preorder and inorder and rebuilding with *Construct Binary Tree…* fails when values repeat. Level order with nulls (LeetCode's own format) is a fine alternative.",
        approach="""`[1,2,3,None,None,4,5]` serialises to `1,2,#,#,3,4,#,#,5,#,#`.

Deserialise: read 1 → build left: read 2 → left `#`, right `#` → back at 1, build right: read 3 → left 4 (`#`,`#`), right 5 (`#`,`#`). Done. Every node contributes one token and every null one token, so a tree with n nodes produces 2n + 1 tokens.

The reference serialises with an explicit stack; deserialising recursively is safe here because depth ≤ 500 in the tests (switch to an explicit stack or BFS for very deep trees).""",
        complexity="Time O(n) both ways, space O(n) for the string.",
        pitfalls="- No delimiter: `12` vs `1`,`2` become indistinguishable.\n- Leaving out null markers.\n- Using `self` to remember the tree (the judge uses separate Codec objects).",
        follow_up="Serialize and Deserialize BST (449): with the BST property, preorder alone (no nulls) suffices.",
    ),
),
]
