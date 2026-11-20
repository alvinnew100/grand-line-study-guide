import random as _r

_r.seed(11)


def _rand_tree(n):
    """Level-order list (with None holes) of a random binary tree with n nodes labelled 1..n."""
    if n == 0:
        return []
    vals = list(range(1, n + 1))
    _r.shuffle(vals)
    out, frontier, k = [vals[0]], 1, 1
    while k < n:
        slots = []
        for _ in range(frontier):
            for _ in range(2):
                if k < n and _r.random() < 0.7:
                    slots.append(vals[k]); k += 1
                else:
                    slots.append(None)
        if all(s is None for s in slots):
            slots[0] = vals[k]; k += 1
        out.extend(slots)
        frontier = sum(s is not None for s in slots)
    while out and out[-1] is None:
        out.pop()
    return out


PROBLEMS = [
dict(
    id="dsaf-tree-traversals",
    title="All Four Binary-Tree Traversals",
    difficulty="Easy",
    pattern="Trees",
    entry="traversals",
    arg_types=["tree"],
    description=r"""
Given the root of a binary tree (`TreeNode` with `val`, `left`, `right`), return
`[preorder, inorder, postorder, levelorder]` — four lists of node values (Goodrich ch. 8.4).

Write preorder, inorder and postorder recursively (or iteratively), and level order with a queue.
An empty tree returns `[[], [], [], []]`.

**Example:** tree `[1, 2, 3, 4, 5, null, 6]` →
`[[1,2,4,5,3,6], [4,2,5,1,3,6], [4,5,2,6,3,1], [1,2,3,4,5,6]]`
""",
    starter='''class Solution:
    def traversals(self, root):
        pass
''',
    solution='''from collections import deque

class Solution:
    def traversals(self, root):
        pre, ino, post, lvl = [], [], [], []
        def dfs(p):
            if p is None:
                return
            pre.append(p.val)
            dfs(p.left)
            ino.append(p.val)
            dfs(p.right)
            post.append(p.val)
        dfs(root)
        Q = deque([root] if root else [])
        while Q:
            p = Q.popleft()
            lvl.append(p.val)
            if p.left: Q.append(p.left)
            if p.right: Q.append(p.right)
        return [pre, ino, post, lvl]
''',
    tests=[
        [[1, 2, 3, 4, 5, None, 6]],
        [[]],
        [[7]],
        [[1, 2, None, 3, None, 4]],
        [[1, None, 2, None, 3]],
        [[5, 3, 8, 1, 4, 7, 9]],
        [[1, 2, 3, None, 4, 5]],
        [_rand_tree(15)],
        [_rand_tree(40)],
        [_rand_tree(300)],
    ],
    examples=1,
    wrong_solutions=[
        '''class Solution:
    def traversals(self, root):
        pre, ino, post, lvl = [], [], [], []
        def dfs(p):
            if p is None:
                return
            pre.append(p.val); ino.append(p.val)
            dfs(p.left); dfs(p.right)
            post.append(p.val)
        dfs(root)
        st = [root] if root else []
        while st:
            p = st.pop(); lvl.append(p.val)
            if p.left: st.append(p.left)
            if p.right: st.append(p.right)
        return [pre, ino, post, lvl]
''',
        '''class Solution:
    def traversals(self, root):
        pre, ino, post, lvl = [], [], [], []
        def dfs(p):
            if p is None:
                return
            pre.append(p.val); dfs(p.left); ino.append(p.val); dfs(p.right); post.append(p.val)
        dfs(root)
        st = [root] if root else []
        while st:
            p = st.pop(); lvl.append(p.val)
            if p.right: st.append(p.right)
            if p.left: st.append(p.left)
        return [pre, ino, post, lvl]
''',
    ],
    guide=dict(
        prereqs="Lesson *Traversals, Euler tours and expression trees*.",
        intuition="One recursive walk can produce all three depth-first orders: record the node before the left call (pre), between the calls (in), and after the right call (post) — exactly the three Euler-tour visits. Level order needs a FIFO queue.",
        hints=["Pre = visit before children; in = between; post = after.",
               "Use collections.deque and popleft() for level order.",
               "A stack instead of a queue gives a depth-first order, not level order."],
        brute_force="Four separate traversals are also O(n) each — fine, just more code.",
        approach="""
Define `dfs(p)` that returns on None and otherwise appends to `pre`, recurses left, appends to `ino`, recurses right, appends to `post`. Then BFS from the root with a deque, enqueuing left before right.
""",
        complexity="Time O(n): each node is visited a constant number of times. Space O(h) recursion + O(w) queue (w = max level width), O(n) for the outputs.",
        pitfalls="Using a stack for level order; forgetting the empty tree; enqueuing None children.",
        follow_up="Iterative inorder with an explicit stack; Morris traversal in O(1) extra space; rebuild a tree from preorder + inorder.",
    ),
),
dict(
    id="dsaf-expression-tree",
    title="Build and Evaluate an Expression Tree",
    difficulty="Medium",
    pattern="Trees",
    entry="expression_tree",
    description=r"""
`tokens` is a valid **postfix** expression over integers and the binary operators `+`, `-`, `*`
(Goodrich ch. 8.5). Build the expression tree (leaves = operands, internal nodes = operators) and
return `[value, infix]` where:

- `value` is the integer value of the expression (evaluate by a **postorder** traversal);
- `infix` is the **fully parenthesised** infix string produced by an Euler tour: a leaf prints its
  token; an internal node prints `"(" + left + " " + op + " " + right + ")"`.

Operands may be negative (e.g. `"-3"` is a number, `"-"` alone is the operator).

**Example:** `["3","1","+","4","*"]` → `[16, "((3 + 1) * 4)"]`

**Example:** `["7"]` → `[7, "7"]`
""",
    starter='''class Node:
    def __init__(self, token, left=None, right=None):
        self.token, self.left, self.right = token, left, right


def expression_tree(tokens):
    pass
''',
    solution='''class Node:
    def __init__(self, token, left=None, right=None):
        self.token, self.left, self.right = token, left, right


def expression_tree(tokens):
    S = []
    for t in tokens:
        if t in ("+", "-", "*"):
            right = S.pop()
            left = S.pop()
            S.append(Node(t, left, right))
        else:
            S.append(Node(t))
    root = S.pop()

    def value(p):
        if p.left is None:
            return int(p.token)
        a, b = value(p.left), value(p.right)
        return a + b if p.token == "+" else a - b if p.token == "-" else a * b

    def infix(p):
        if p.left is None:
            return p.token
        return "(" + infix(p.left) + " " + p.token + " " + infix(p.right) + ")"

    return [value(root), infix(root)]
''',
    tests=[
        [["3", "1", "+", "4", "*"]],
        [["7"]],
        [["5", "2", "-"]],
        [["2", "5", "-", "3", "-"]],
        [["2", "5", "3", "-", "-"]],
        [["-3", "4", "*"]],
        [["1", "2", "+", "3", "4", "+", "*"]],
        [["3", "1", "+", "3", "*", "9", "5", "-", "2", "+", "-", "3", "7", "4", "-", "*", "6", "+", "-"]],
        [["10", "-2", "-", "0", "*", "8", "+"]],
        [["1"] + ["1", "+"] * 200],
        [["2", "3", "4", "5", "*", "*", "*", "6", "-"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def expression_tree(tokens):
    S = []
    for t in tokens:
        if t in ("+", "-", "*"):
            a = S.pop(); b = S.pop()
            S.append(("(" + a[1] + " " + t + " " + b[1] + ")",
                      a[0] + b[0] if t == "+" else a[0] - b[0] if t == "-" else a[0] * b[0]))
            S[-1] = (S[-1][1], S[-1][0])
        else:
            S.append((int(t), t))
    v, s = S.pop()
    return [v, s]
''',
        '''def expression_tree(tokens):
    S = []
    for t in tokens:
        if t in "+-*":
            b = S.pop(); a = S.pop()
            S.append((a[0] + b[0] if t == "+" else a[0] - b[0] if t == "-" else a[0] * b[0],
                      a[1] + " " + t + " " + b[1]))
        else:
            S.append((int(t), t))
    return list(S.pop())
''',
    ],
    guide=dict(
        prereqs="Lessons *Stacks* (postfix evaluation) and *Traversals, Euler tours and expression trees*.",
        intuition="Postfix lists each operator right after its two operands, so a stack of subtrees assembles the tree bottom-up. Evaluation is postorder; parenthesised printing is an Euler tour.",
        hints=["Operand → push a leaf. Operator → pop right, pop left, push Node(op, left, right).",
               "Check membership with a tuple of operators so '-3' is treated as a number.",
               "value(leaf) = int(token); value(op) = op(value(left), value(right))."],
        brute_force="You can evaluate postfix directly with a stack of numbers (no tree), and build the string in parallel with a stack of strings — equally O(n). Building the tree makes the traversal structure explicit.",
        approach="""
1. Build: scan tokens with a stack of nodes.
2. Evaluate recursively (postorder).
3. Print recursively: leaf → token; internal → "(" + left + " op " + right + ")".

Dry run `3 1 + 4 *`: push 3, push 1, '+' → (3 + 1); push 4; '*' → ((3 + 1) * 4) = 16.
""",
        complexity="Time O(n) for building, evaluating and printing (each node handled once). Space O(n) for the tree and O(h) recursion.",
        pitfalls="Popping operands in the wrong order breaks '-'; `t in '+-*'` is true for the empty string and treats '-' prefix numbers wrongly only if you test characters — compare whole tokens. Long left-deep chains are deep: 200 levels is fine, 10^5 would need iteration.",
        follow_up="Support '/' with exact fractions (fractions.Fraction); simplify the infix output by omitting parentheses implied by precedence.",
    ),
),
]
