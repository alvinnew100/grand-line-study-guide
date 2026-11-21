"""DSA in JavaScript: Tree and Trie problems.

Convention: trees are written as LeetCode level-order arrays with null for missing children
([3, 9, 20, null, null, 15, 7]). A provided buildTree/treeToArray pair converts them.
"""
import random


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


TREE_HELPERS = r'''
// --- provided: TreeNode and helpers (do not change) ---
class TreeNode {
  constructor(val = 0, left = null, right = null) {
    this.val = val;
    this.left = left;
    this.right = right;
  }
}
function buildTree(values) {            // level-order array with null gaps -> root
  if (!values.length || values[0] === null) return null;
  const root = new TreeNode(values[0]);
  const queue = [root];
  let head = 0, i = 1;
  while (i < values.length) {
    const node = queue[head++];
    if (values[i] !== null && values[i] !== undefined) { node.left = new TreeNode(values[i]); queue.push(node.left); }
    i++;
    if (i < values.length && values[i] !== null) { node.right = new TreeNode(values[i]); queue.push(node.right); }
    i++;
  }
  return root;
}
function treeToArray(root) {            // root -> level-order array, trailing nulls removed
  const out = [], queue = [root];
  let head = 0;
  while (head < queue.length) {
    const node = queue[head++];
    if (node) { out.push(node.val); queue.push(node.left, node.right); }
    else out.push(null);
  }
  while (out.length && out[out.length - 1] === null) out.pop();
  return out;
}
'''

CONVENTION = r"""

**How the tests talk to your code.** Trees are written in level order (row by row, left to right) with `null`
for a missing child, as on LeetCode: `[3, 9, 20, null, null, 15, 7]` is a root 3 with children 9 and 20, where 20
has children 15 and 7. The provided `TreeNode` class, `buildTree` and `treeToArray` helpers and the driver at the
bottom convert between arrays and real nodes. Do not edit the provided part.
"""


def level_order(root):
    """root is (val, left, right) tuples or None -> LeetCode list."""
    out, q, h = [], [root], 0
    while h < len(q):
        n = q[h]; h += 1
        if n is None:
            out.append(None)
        else:
            out.append(n[0]); q.append(n[1]); q.append(n[2])
    while out and out[-1] is None:
        out.pop()
    return out


def bst_from(values):
    root = None
    def ins(node, v):
        if node is None:
            return [v, None, None]
        if v < node[0]:
            node[1] = ins(node[1], v)
        else:
            node[2] = ins(node[2], v)
        return node
    for v in values:
        root = ins(root, v)
    return root


def random_tree(n, lo, hi, seed):
    r = random.Random(seed)
    nodes = [[r.randint(lo, hi), None, None] for _ in range(n)]
    for i in range(1, n):
        while True:
            p = nodes[r.randrange(i)]
            side = r.choice((1, 2))
            if p[side] is None:
                p[side] = nodes[i]
                break
    return nodes[0]


def skewed(n, right=True):
    vals = [1]
    for i in range(2, n + 1):
        vals += [None, i] if right else [i, None]
    return vals


rb = random.Random(41)
BST_VALS = rb.sample(range(1, 100000), 1500)
BIG_BST = level_order(bst_from(BST_VALS))


def break_bst(vals):
    """Return a copy where one deep LEFT leaf gets a value below its lower bound (still < its parent)."""
    vals = list(vals)
    n = len(vals)
    bounds = {0: (float("-inf"), float("inf"), 0)}
    child_of, q, h, i = {}, [0], 0, 1
    while h < len(q) and i < n:
        node = q[h]; h += 1
        for side in (0, 1):
            if i < n and vals[i] is not None:
                child_of[i] = (node, side); q.append(i)
            i += 1
    for idx in q[1:]:
        par, side = child_of[idx]
        lo, hi, d = bounds[par]
        v = vals[par]
        bounds[idx] = (lo, v, d + 1) if side == 0 else (v, hi, d + 1)
    for idx in q:
        lo, hi, d = bounds[idx]
        is_leaf = all(not (c in child_of and child_of[c][0] == idx) for c in (2 * 0,)) and idx not in [p for p, _ in child_of.values()]
        if d >= 5 and is_leaf and child_of.get(idx, (0, 1))[1] == 0 and lo != float("-inf"):
            vals[idx] = lo - 1
            return vals
    raise ValueError("no suitable leaf")


BAD_BST = break_bst(BIG_BST)
RAND_TREE = level_order(random_tree(1500, -1000, 1000, 3))
RAND_TREE_2 = level_order(random_tree(800, -50, 100, 4))

TRIE_DRIVER = r'''
// --- driver used by the tests (provided, do not change) ---
function runTrie(ops, args) {
  let trie = null;
  const out = [];
  for (let i = 0; i < ops.length; i++) {
    if (ops[i] === "Trie") { trie = new Trie(); out.push(null); }
    else { const r = trie[ops[i]](...args[i]); out.push(r === undefined ? null : r); }
  }
  return out;
}
'''

WD_DRIVER = r'''
// --- driver used by the tests (provided, do not change) ---
function runWordDictionary(ops, args) {
  let wd = null;
  const out = [];
  for (let i = 0; i < ops.length; i++) {
    if (ops[i] === "WordDictionary") { wd = new WordDictionary(); out.push(null); }
    else { const r = wd[ops[i]](...args[i]); out.push(r === undefined ? null : r); }
  }
  return out;
}
'''


def trie_random(n, seed):
    r = random.Random(seed)
    words = ["".join(r.choice("abc") for _ in range(r.randint(1, 6))) for _ in range(60)]
    ops, args = ["Trie"], [[]]
    for _ in range(n):
        w = r.choice(words); c = r.random()
        if c < 0.4:
            ops.append("insert"); args.append([w])
        elif c < 0.7:
            ops.append("search"); args.append([w])
        else:
            ops.append("startsWith"); args.append([w[: r.randint(1, len(w))]])
    return [ops, args]


def wd_random(n, seed):
    r = random.Random(seed)
    words = ["".join(r.choice("abcd") for _ in range(r.randint(1, 5))) for _ in range(50)]
    ops, args = ["WordDictionary"], [[]]
    for _ in range(n):
        w = r.choice(words)
        if r.random() < 0.4:
            ops.append("addWord"); args.append([w])
        else:
            pat = "".join("." if r.random() < 0.3 else ch for ch in w)
            ops.append("search"); args.append([pat])
    return [ops, args]


PROBLEMS = [
dict(
    id="js-invert-binary-tree", title="Invert Binary Tree", difficulty="Easy", pattern="Trees",
    leetcode="https://leetcode.com/problems/invert-binary-tree/",
    neetcode="https://neetcode.io/problems/invert-a-binary-tree",
    kind="js", entry="runInvert",
    description=r"""
Given the `root` of a binary tree, swap the left and right child of **every** node (the tree's mirror image) and
return the root.

**Example 1:** `[4, 2, 7, 1, 3, 6, 9]` → `[4, 7, 2, 9, 6, 3, 1]`

**Example 2:** `[]` → `[]`
""" + CONVENTION,
    starter="function invertTree(root) {\n  // your code\n}\n" + TREE_HELPERS + "\nfunction runInvert(values) {\n  return treeToArray(invertTree(buildTree(values)));\n}\n",
    solution=r'''function invertTree(root) {
  if (root === null) return null;
  const left = invertTree(root.left);
  root.left = invertTree(root.right);
  root.right = left;
  return root;
}
''' + TREE_HELPERS + "\nfunction runInvert(values) {\n  return treeToArray(invertTree(buildTree(values)));\n}\n",
    tests=[[[4, 2, 7, 1, 3, 6, 9]], [[]], [[1]], [[2, 1, 3]], [[1, 2]], [[1, None, 2]], [[1, 2, 3, 4, None, None, 5]],
           [[5, 3, 8, 1, 4, 7, 9, 0, 2]], [RAND_TREE_2], [skewed(500)]],
    examples=2,
    wrong_solutions=[
        "function invertTree(root) {\n  if (root) { const t = root.left; root.left = root.right; root.right = t; }\n  return root;\n}\n" + TREE_HELPERS + "\nfunction runInvert(values) {\n  return treeToArray(invertTree(buildTree(values)));\n}\n",
        "function invertTree(root) {\n  if (!root) return null;\n  [root.left, root.right] = [root.right, root.left];\n  invertTree(root.left);\n  return root;\n}\n" + TREE_HELPERS + "\nfunction runInvert(values) {\n  return treeToArray(invertTree(buildTree(values)));\n}\n",
    ],
    guide=G(
        prereqs="The lesson *Linked lists and trees with classes*: `TreeNode`, recursion on `root.left` and `root.right`, `null` as an empty tree.",
        intuition="A mirrored tree is: the root, with the mirrored right subtree on the left and the mirrored left subtree on the right. That sentence is the recursion.",
        hints=[
            "What is the mirror of an empty tree?",
            "Invert both subtrees, then swap them.",
            "Save one subtree in a variable before overwriting `root.left`.",
        ],
        brute_force="This problem has no slower alternative worth mentioning; the iterative version uses a queue (BFS) and swaps children of every dequeued node.",
        approach="1. Base case: `null` → `null`.\n2. `left = invertTree(root.left)`.\n3. `root.left = invertTree(root.right)`; `root.right = left`.\n4. Return `root`.",
        complexity="Time O(n), space O(h) for the call stack (h = height).",
        pitfalls="- Assigning `root.left = invertTree(root.right)` and then `root.right = invertTree(root.left)` uses the **already replaced** left child.\n- Swapping only at the root is not enough: every node must be swapped.\n- Destructuring swap `[root.left, root.right] = [root.right, root.left]` is a neat JS idiom; then recurse on both.",
        follow_up="Symmetric Tree asks whether a tree equals its own mirror: compare left with right recursively.",
    ),
),
dict(
    id="js-maximum-depth-of-binary-tree", title="Maximum Depth of Binary Tree", difficulty="Easy", pattern="Trees",
    leetcode="https://leetcode.com/problems/maximum-depth-of-binary-tree/",
    neetcode="https://neetcode.io/problems/depth-of-binary-tree",
    kind="js", entry="runMaxDepth",
    description=r"""
Return the **depth** of a binary tree: the number of nodes on the longest path from the root down to a leaf.
An empty tree has depth 0. Some tests contain a very tall, thin tree (thousands of levels), so think about
whether recursion is safe (an iterative BFS always is).

**Example 1:** `[1, 2, 3, null, null, 4]` → `3`

**Example 2:** `[]` → `0`
""" + CONVENTION,
    starter="function maxDepth(root) {\n  // your code\n}\n" + TREE_HELPERS + "\nfunction runMaxDepth(values) {\n  return maxDepth(buildTree(values));\n}\n",
    solution=r'''function maxDepth(root) {
  if (!root) return 0;
  let level = [root], depth = 0;       // BFS one level at a time: no recursion
  while (level.length) {
    depth++;
    const next = [];
    for (const node of level) {
      if (node.left) next.push(node.left);
      if (node.right) next.push(node.right);
    }
    level = next;
  }
  return depth;
}
''' + TREE_HELPERS + "\nfunction runMaxDepth(values) {\n  return maxDepth(buildTree(values));\n}\n",
    tests=[[[1, 2, 3, None, None, 4]], [[]], [[1]], [[1, None, 2]], [[3, 9, 20, None, None, 15, 7]], [[1, 2, 3, 4, 5, 6, 7]],
           [[1, 2, None, 3, None, 4, None, 5]], [RAND_TREE], [skewed(6000, right=False)]],
    examples=2,
    wrong_solutions=[
        "function maxDepth(root) {\n  let d = 0;\n  for (let n = root; n; n = n.left) d++;\n  return d;\n}\n" + TREE_HELPERS + "\nfunction runMaxDepth(values) {\n  return maxDepth(buildTree(values));\n}\n",
        "function maxDepth(root) {\n  if (!root) return 0;\n  return 1 + Math.min(maxDepth(root.left), maxDepth(root.right));\n}\n" + TREE_HELPERS + "\nfunction runMaxDepth(values) {\n  return maxDepth(buildTree(values));\n}\n",
    ],
    guide=G(
        prereqs="Tree recursion and level-by-level BFS (lesson *Pattern map II*).",
        intuition="The depth of a tree is 1 plus the deeper of its two subtrees. Iteratively: count how many levels a breadth-first search visits.",
        hints=[
            "Recursive one-liner: `root ? 1 + Math.max(maxDepth(root.left), maxDepth(root.right)) : 0`.",
            "A 6000-level chain can be close to an engine's recursion limit. How would you avoid recursion?",
            "Process the tree one level at a time and count the levels.",
        ],
        brute_force="The recursive solution is already O(n); the concern here is not speed but call-stack depth on degenerate trees.",
        approach="1. Empty tree → 0.\n2. `level = [root]`; while it is non-empty: `depth++` and build the next level from the children.\n3. Return `depth`.",
        complexity="Time O(n), space O(w) where w is the widest level.",
        pitfalls="- Recursion depth equals tree height. Node's default stack holds roughly ten thousand simple frames, browsers vary; a skewed tree with 10^5 nodes throws `RangeError: Maximum call stack size exceeded`.\n- `Math.min` gives the depth of the shallowest branch, not the deepest.\n- Following only `left` pointers measures one path.",
        follow_up="Minimum Depth needs care: a node with one child is not a leaf. BFS can stop at the first leaf.",
    ),
),
dict(
    id="js-binary-tree-level-order-traversal", title="Binary Tree Level Order Traversal", difficulty="Medium", pattern="Trees",
    leetcode="https://leetcode.com/problems/binary-tree-level-order-traversal/",
    neetcode="https://neetcode.io/problems/level-order-traversal-of-binary-tree",
    kind="js", entry="runLevelOrder",
    description=r"""
Return the values of a binary tree level by level: an array of rows, top row first, each row left to right.

**Example 1:** `[1, 2, 3, 4, 5, 6, 7]` → `[[1], [2, 3], [4, 5, 6, 7]]`

**Example 2:** `[]` → `[]`
""" + CONVENTION,
    starter="function levelOrder(root) {\n  // your code\n}\n" + TREE_HELPERS + "\nfunction runLevelOrder(values) {\n  return levelOrder(buildTree(values));\n}\n",
    solution=r'''function levelOrder(root) {
  const res = [];
  if (!root) return res;
  const queue = [root];
  let head = 0;                        // index of the next node to dequeue
  while (head < queue.length) {
    const size = queue.length - head;  // nodes in the current level
    const row = [];
    for (let i = 0; i < size; i++) {
      const node = queue[head++];
      row.push(node.val);
      if (node.left) queue.push(node.left);
      if (node.right) queue.push(node.right);
    }
    res.push(row);
  }
  return res;
}
''' + TREE_HELPERS + "\nfunction runLevelOrder(values) {\n  return levelOrder(buildTree(values));\n}\n",
    tests=[[[1, 2, 3, 4, 5, 6, 7]], [[]], [[1]], [[3, 9, 20, None, None, 15, 7]], [[1, 2, None, 3, None, 4]],
           [[1, None, 2, None, 3]], [[0, -1, 1, None, -2, 2]], [RAND_TREE_2], [BIG_BST]],
    examples=2,
    wrong_solutions=[
        "function levelOrder(root) {\n  const res = [];\n  const q = root ? [root] : [];\n  while (q.length) { const n = q.shift(); res.push([n.val]); if (n.left) q.push(n.left); if (n.right) q.push(n.right); }\n  return res;\n}\n" + TREE_HELPERS + "\nfunction runLevelOrder(values) {\n  return levelOrder(buildTree(values));\n}\n",
        "function levelOrder(root) {\n  const res = [];\n  function dfs(n, d) { if (!n) return; (res[d] = res[d] || []).push(n.val); dfs(n.right, d + 1); dfs(n.left, d + 1); }\n  dfs(root, 0);\n  return res;\n}\n" + TREE_HELPERS + "\nfunction runLevelOrder(values) {\n  return levelOrder(buildTree(values));\n}\n",
    ],
    guide=G(
        prereqs="Queues without `shift` (lesson *Stacks, queues and deques in JavaScript*) and BFS.",
        intuition="Breadth-first search naturally visits nodes level by level. Before processing a level, note how many nodes are in the queue: exactly those form the current row.",
        hints=[
            "Use an array as a queue with a `head` index instead of `shift()`.",
            "At the start of each round, `size = queue.length - head` is the number of nodes on this level.",
            "Pop `size` nodes, record their values, and enqueue their children.",
        ],
        brute_force="A DFS that passes the depth and pushes into `res[depth]` also works in O(n), as long as it visits left before right.",
        approach="1. Empty → `[]`.\n2. `queue = [root]`, `head = 0`.\n3. While `head < queue.length`: `size = queue.length - head`; dequeue `size` nodes into `row`, enqueue children; push `row`.",
        complexity="Time O(n), space O(n) for the queue (the array keeps processed nodes too; reset it per level if memory matters).",
        pitfalls="- `queue.shift()` is O(n) per call in the worst case: on a wide tree the traversal becomes quadratic.\n- Reading `queue.length` inside the loop condition instead of saving `size` mixes levels.\n- In the DFS version, recursing right before left reverses each row.",
        follow_up="Zigzag order, right side view and level averages are the same loop with a different row action.",
    ),
),
dict(
    id="js-validate-binary-search-tree", title="Validate Binary Search Tree", difficulty="Medium", pattern="Trees",
    leetcode="https://leetcode.com/problems/validate-binary-search-tree/",
    neetcode="https://neetcode.io/problems/valid-binary-search-tree",
    kind="js", entry="runIsValidBST",
    description=r"""
Return `true` if the binary tree is a valid **binary search tree (BST)**: for every node, all values in its left
subtree are strictly smaller than the node's value, and all values in its right subtree are strictly larger.

**Example 1:** `[2, 1, 3]` → `true`

**Example 2:** `[5, 1, 7, null, null, 4, 8]` → `false` (4 sits in the right subtree of 5)
""" + CONVENTION,
    starter="function isValidBST(root) {\n  // your code\n}\n" + TREE_HELPERS + "\nfunction runIsValidBST(values) {\n  return isValidBST(buildTree(values));\n}\n",
    solution=r'''function isValidBST(root) {
  // iterative DFS carrying the open interval (lo, hi) each node must fall in
  const stack = [[root, -Infinity, Infinity]];
  while (stack.length) {
    const [node, lo, hi] = stack.pop();
    if (!node) continue;
    if (node.val <= lo || node.val >= hi) return false;
    stack.push([node.left, lo, node.val], [node.right, node.val, hi]);
  }
  return true;
}
''' + TREE_HELPERS + "\nfunction runIsValidBST(values) {\n  return isValidBST(buildTree(values));\n}\n",
    tests=[[[2, 1, 3]], [[5, 1, 7, None, None, 4, 8]], [[]], [[1]], [[1, 1]], [[2, 2, 2]], [[5, 4, 6, None, None, 3, 7]],
           [[3, 1, 5, 0, 2, 4, 6]], [[-2147483648, None, 2147483647]], [[10, 5, 15, None, 12]], [BIG_BST], [BAD_BST]],
    examples=2,
    wrong_solutions=[
        "function isValidBST(root) {\n  if (!root) return true;\n  if (root.left && root.left.val >= root.val) return false;\n  if (root.right && root.right.val <= root.val) return false;\n  return isValidBST(root.left) && isValidBST(root.right);\n}\n" + TREE_HELPERS + "\nfunction runIsValidBST(values) {\n  return isValidBST(buildTree(values));\n}\n",
        "function isValidBST(root) {\n  function ok(n, lo, hi) { if (!n) return true; if (n.val < lo || n.val > hi) return false; return ok(n.left, lo, n.val) && ok(n.right, n.val, hi); }\n  return ok(root, -Infinity, Infinity);\n}\n" + TREE_HELPERS + "\nfunction runIsValidBST(values) {\n  return isValidBST(buildTree(values));\n}\n",
    ],
    guide=G(
        prereqs="BST definition, tree DFS, and `-Infinity` / `Infinity` as open bounds.",
        intuition="Checking each node only against its children is not enough: a node deep in the right subtree must still be larger than the root. Pass down the allowed open interval `(lo, hi)`; going left tightens `hi`, going right tightens `lo`.",
        hints=[
            "Why is `[5, 1, 7, null, null, 4, 8]` invalid even though 4 < 7?",
            "Give every node a lower and an upper bound.",
            "Start with `(-Infinity, Infinity)`; equal values are not allowed.",
        ],
        brute_force="For every node, scan its whole left and right subtrees for violations: O(n^2) on a skewed tree. An in-order traversal that checks strictly increasing order is a clean O(n) alternative.",
        approach="1. Stack of `[node, lo, hi]` starting with `[root, -Infinity, Infinity]`.\n2. Pop; skip `null`; fail if `val <= lo` or `val >= hi`.\n3. Push left child with `(lo, val)` and right child with `(val, hi)`.\n4. Empty stack → `true`.",
        complexity="Time O(n), space O(h) to O(n) for the stack.",
        pitfalls="- Parent-child comparisons alone accept invalid trees.\n- Using `<`/`>` instead of `<=`/`>=` accepts duplicates.\n- Starting bounds at `Number.MIN_SAFE_INTEGER` works for these inputs but `-Infinity` is clearer and never wrong.",
        follow_up="Kth Smallest Element in a BST uses the same in-order walk; Recover BST finds the two swapped nodes during it.",
    ),
),
dict(
    id="js-lowest-common-ancestor-of-a-bst", title="Lowest Common Ancestor of a Binary Search Tree", difficulty="Medium", pattern="Trees",
    leetcode="https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-search-tree/",
    neetcode="https://neetcode.io/problems/lowest-common-ancestor-in-binary-search-tree",
    kind="js", entry="runLCA",
    description=r"""
In a binary search tree with distinct values, the **lowest common ancestor (LCA)** of two nodes `p` and `q` is the
deepest node that has both of them in its subtree (a node counts as its own descendant). Given the root and the
two nodes, return the LCA node.

**How the tests call your code.** Each test is `[tree, pValue, qValue]`. The driver finds the nodes holding
those values, calls `lowestCommonAncestor(root, p, q)`, and reports the **value** of the node you return.

**Example 1:** `[6, 2, 8, 0, 4, 7, 9, null, null, 3, 5]`, p = 2, q = 8 → `6`

**Example 2:** same tree, p = 2, q = 4 → `2`
""" + CONVENTION,
    starter="function lowestCommonAncestor(root, p, q) {\n  // your code\n}\n" + TREE_HELPERS + r'''
function runLCA(values, pv, qv) {
  const root = buildTree(values);
  const find = (v) => { let n = root; while (n && n.val !== v) n = v < n.val ? n.left : n.right; return n; };
  const ans = lowestCommonAncestor(root, find(pv), find(qv));
  return ans ? ans.val : null;
}
''',
    solution=r'''function lowestCommonAncestor(root, p, q) {
  let node = root;
  while (node) {
    if (p.val < node.val && q.val < node.val) node = node.left;        // both on the left
    else if (p.val > node.val && q.val > node.val) node = node.right;  // both on the right
    else return node;                                                  // they split here
  }
  return null;
}
''' + TREE_HELPERS + r'''
function runLCA(values, pv, qv) {
  const root = buildTree(values);
  const find = (v) => { let n = root; while (n && n.val !== v) n = v < n.val ? n.left : n.right; return n; };
  const ans = lowestCommonAncestor(root, find(pv), find(qv));
  return ans ? ans.val : null;
}
''',
    tests=[[[6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 2, 8], [[6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 2, 4],
           [[6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 3, 5], [[6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 7, 9],
           [[6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 0, 5], [[2, 1], 2, 1], [[2, 1], 1, 2], [[5, 3, 6, 2, 4, None, None, 1], 1, 4],
           [[5, 3, 6, 2, 4, None, None, 1], 6, 6], [BIG_BST, BST_VALS[700], BST_VALS[1400]], [BIG_BST, BST_VALS[3], BST_VALS[1499]]],
    examples=2,
    wrong_solutions=[
        "function lowestCommonAncestor(root, p, q) {\n  return root;\n}\n" + TREE_HELPERS + r'''
function runLCA(values, pv, qv) {
  const root = buildTree(values);
  const find = (v) => { let n = root; while (n && n.val !== v) n = v < n.val ? n.left : n.right; return n; };
  const ans = lowestCommonAncestor(root, find(pv), find(qv));
  return ans ? ans.val : null;
}
''',
        "function lowestCommonAncestor(root, p, q) {\n  return p.val < q.val ? p : q;\n}\n" + TREE_HELPERS + r'''
function runLCA(values, pv, qv) {
  const root = buildTree(values);
  const find = (v) => { let n = root; while (n && n.val !== v) n = v < n.val ? n.left : n.right; return n; };
  const ans = lowestCommonAncestor(root, find(pv), find(qv));
  return ans ? ans.val : null;
}
''',
    ],
    guide=G(
        prereqs="The BST ordering property and walking down a tree with a loop.",
        intuition="Walk down from the root. While both values are smaller than the current node, the LCA is in the left subtree; while both are larger, it is in the right subtree. The first node where they split (or that equals one of them) is the answer.",
        hints=[
            "Use the BST ordering instead of searching both subtrees.",
            "If `p` and `q` are on different sides of `node`, what does that mean?",
            "A loop is enough; no recursion or extra memory.",
        ],
        brute_force="Record the root-to-node path for `p` and for `q` and take the last common node: O(h) time but O(h) extra space. For a general binary tree you would need the recursive \"return up\" method.",
        approach="1. `node = root`.\n2. Both smaller → go left; both larger → go right; otherwise return `node`.\n\n**Dry run** p 3, q 5 in the example: 6 → both smaller → 2 → both larger → 4 → split → 4.",
        complexity="Time O(h), space O(1).",
        pitfalls="- Comparing node objects with `<` compares... nothing useful: compare `p.val` and `q.val`.\n- When `p` is an ancestor of `q`, the answer is `p` itself; the `else` branch covers it.",
        follow_up="LCA of a general binary tree: recurse and return the node if found in both subtrees.",
    ),
),
dict(
    id="js-binary-tree-maximum-path-sum", title="Binary Tree Maximum Path Sum", difficulty="Hard", pattern="Trees",
    leetcode="https://leetcode.com/problems/binary-tree-maximum-path-sum/",
    neetcode="https://neetcode.io/problems/binary-tree-maximum-path-sum",
    kind="js", entry="runMaxPathSum",
    description=r"""
A **path** in a binary tree is a sequence of nodes where each consecutive pair is joined by an edge, and no node
appears twice. It does not have to pass through the root, but it must contain at least one node. Return the
largest possible sum of node values along a path.

- `1 <=` number of nodes `<= 3 * 10^4`, `-1000 <= val <= 1000`

**Example 1:** `[1, 2, 3]` → `6` (2 → 1 → 3)

**Example 2:** `[-15, 10, 20, null, null, 15, 5, -5]` → `40` (15 → 20 → 5)
""" + CONVENTION,
    starter="function maxPathSum(root) {\n  // your code\n}\n" + TREE_HELPERS + "\nfunction runMaxPathSum(values) {\n  return maxPathSum(buildTree(values));\n}\n",
    solution=r'''function maxPathSum(root) {
  let best = -Infinity;
  // gain(node) = best sum of a path that starts at node and goes DOWN one side
  function gain(node) {
    if (!node) return 0;
    const left = Math.max(0, gain(node.left));    // drop negative branches
    const right = Math.max(0, gain(node.right));
    best = Math.max(best, node.val + left + right); // path that bends at node
    return node.val + Math.max(left, right);        // only one side can continue up
  }
  gain(root);
  return best;
}
''' + TREE_HELPERS + "\nfunction runMaxPathSum(values) {\n  return maxPathSum(buildTree(values));\n}\n",
    tests=[[[1, 2, 3]], [[-15, 10, 20, None, None, 15, 5, -5]], [[-3]], [[-2, -1]], [[2, -1]], [[-10, 9, 20, None, None, 15, 7]],
           [[5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, 1]], [[1, -2, 3]], [[-1, 5, None, 4, None, None, 2, -4]],
           [[10, 2, 10, 20, 1, None, -25, None, None, None, None, 3, 4]], [RAND_TREE], [RAND_TREE_2]],
    examples=2,
    wrong_solutions=[
        "function maxPathSum(root) {\n  let best = 0;\n  function g(n) { if (!n) return 0; const l = Math.max(0, g(n.left)), r = Math.max(0, g(n.right)); best = Math.max(best, n.val + l + r); return n.val + Math.max(l, r); }\n  g(root);\n  return best;\n}\n" + TREE_HELPERS + "\nfunction runMaxPathSum(values) {\n  return maxPathSum(buildTree(values));\n}\n",
        "function maxPathSum(root) {\n  let best = -Infinity;\n  function g(n) { if (!n) return 0; const l = Math.max(0, g(n.left)), r = Math.max(0, g(n.right)); best = Math.max(best, n.val + l + r); return n.val + l + r; }\n  g(root);\n  return best;\n}\n" + TREE_HELPERS + "\nfunction runMaxPathSum(values) {\n  return maxPathSum(buildTree(values));\n}\n",
    ],
    guide=G(
        prereqs="Post-order recursion that returns a value up while updating an outer variable (closures; lesson *Pattern map II*).",
        intuition="Every path has one highest node where it bends. At that node the sum is `val + bestDown(left) + bestDown(right)`. But what a node can hand **up** to its parent is only a one-sided path: `val + max(bestDown(left), bestDown(right))`. Negative branches are better dropped (count them as 0).",
        hints=[
            "Separate \"best path through this node\" from \"best downward path starting here\".",
            "Use `Math.max(0, ...)` to ignore negative subtrees.",
            "Keep the global answer in a variable captured by an inner function; start it at `-Infinity`.",
        ],
        brute_force="Try every node as the bend point and compute the best downward sums from scratch: O(n^2).",
        approach="1. `best = -Infinity`.\n2. `gain(node)`: 0 for `null`; `left`/`right` = `Math.max(0, gain(child))`; update `best` with `val + left + right`; return `val + Math.max(left, right)`.\n3. Call `gain(root)`, return `best`.\n\n**Dry run** `[-10,9,20,null,null,15,7]`: gain(15)=15, gain(7)=7, at 20: best 42, returns 35; at -10: best stays 42.",
        complexity="Time O(n), space O(h).",
        pitfalls="- Starting `best` at 0 is wrong when every value is negative (`[-3]` must return -3).\n- Returning `val + left + right` upward builds an illegal forked path.\n- Recursion depth equals tree height; for adversarial deep trees convert to an iterative post-order.",
        follow_up="Diameter of Binary Tree is the same pattern counting edges instead of summing values.",
    ),
),
dict(
    id="js-implement-trie-prefix-tree", title="Implement Trie (Prefix Tree)", difficulty="Medium", pattern="Tries",
    leetcode="https://leetcode.com/problems/implement-trie-prefix-tree/",
    neetcode="https://neetcode.io/problems/implement-prefix-tree",
    kind="js", entry="runTrie",
    description=r"""
A **trie** (prefix tree) stores strings character by character along paths from a root. Implement class `Trie`:

- `insert(word)` stores the word
- `search(word)` returns `true` if exactly this word was inserted
- `startsWith(prefix)` returns `true` if some inserted word begins with `prefix`

Words use lowercase letters `a`-`z`, lengths 1..2000.

**How the tests call your class.** Each test is `[ops, args]`, for example
`[["Trie","insert","search","search","startsWith"], [[],["dog"],["dog"],["do"],["do"]]]` →
`[null,null,true,false,true]`. The provided `runTrie` driver makes the calls.
""",
    starter="class Trie {\n  constructor() {\n    // your fields\n  }\n  insert(word) {}\n  search(word) {}\n  startsWith(prefix) {}\n}\n" + TRIE_DRIVER,
    solution=r'''class TrieNode {
  constructor() {
    this.children = new Map();   // character -> TrieNode
    this.end = false;            // does a word end here?
  }
}
class Trie {
  constructor() { this.root = new TrieNode(); }
  insert(word) {
    let node = this.root;
    for (const c of word) {
      if (!node.children.has(c)) node.children.set(c, new TrieNode());
      node = node.children.get(c);
    }
    node.end = true;
  }
  walk(s) {                      // node reached by following s, or null
    let node = this.root;
    for (const c of s) {
      node = node.children.get(c);
      if (!node) return null;
    }
    return node;
  }
  search(word) { const n = this.walk(word); return n !== null && n.end; }
  startsWith(prefix) { return this.walk(prefix) !== null; }
}
''' + TRIE_DRIVER,
    tests=[
        [["Trie", "insert", "search", "search", "startsWith"], [[], ["dog"], ["dog"], ["do"], ["do"]]],
        [["Trie", "insert", "search", "search", "startsWith", "insert", "search"], [[], ["apple"], ["apple"], ["app"], ["app"], ["app"], ["app"]]],
        [["Trie", "search", "startsWith"], [[], ["a"], ["a"]]],
        [["Trie", "insert", "insert", "search", "search", "startsWith", "startsWith"], [[], ["ab"], ["abc"], ["ab"], ["abcd"], ["abc"], ["b"]]],
        [["Trie", "insert", "startsWith", "search"], [[], ["constructor"], ["constr"], ["constructor"]]],
        [["Trie", "insert", "search", "startsWith"], [[], ["toString"], ["valueOf"], ["hasOwnProperty"]]],
        trie_random(300, 7),
        trie_random(2000, 8),
    ],
    examples=2,
    wrong_solutions=[
        "class Trie {\n  constructor() { this.words = []; }\n  insert(w) { this.words.push(w); }\n  search(w) { return this.words.some(x => x.startsWith(w)); }\n  startsWith(p) { return this.words.some(x => x.startsWith(p)); }\n}\n" + TRIE_DRIVER,
        r'''class Trie {
  constructor() { this.root = new Map(); }
  insert(w) { let n = this.root; for (const c of w) { if (!n.has(c)) n.set(c, new Map()); n = n.get(c); } }
  search(w) { let n = this.root; for (const c of w) { n = n.get(c); if (!n) return false; } return true; }
  startsWith(p) { return this.search(p); }
}
''' + TRIE_DRIVER,
    ],
    guide=G(
        prereqs="Classes, `Map`, and the trie idea (lesson *Pattern map II*).",
        intuition="Each node represents a prefix. Its children map the next character to the node for the longer prefix. A boolean `end` marks nodes where a whole inserted word stops, which is what separates `search` from `startsWith`.",
        hints=[
            "A node needs a `children` map and an `end` flag.",
            "`insert` creates missing children while walking; `search` and `startsWith` only walk.",
            "Write one helper that walks a string and returns the final node or `null`.",
        ],
        brute_force="Keep an array of words and scan it for each query: O(total length) per query instead of O(word length).",
        approach="1. `TrieNode { children: Map, end: false }`.\n2. `insert`: walk, creating nodes; set `end = true` at the last one.\n3. `walk(s)`: follow characters, return `null` on a missing child.\n4. `search` = node exists and `end`; `startsWith` = node exists.",
        complexity="Each operation O(L) for a string of length L. Space O(total characters inserted).",
        pitfalls="- Plain objects `{}` work as child maps while keys are single letters, but if you ever key by whole strings, names such as `\"constructor\"` and `\"toString\"` already exist on every object through `Object.prototype`. `Map` (or `Object.create(null)`) avoids the trap.\n- Forgetting the `end` flag makes `search(\"app\")` true after inserting only `\"apple\"`.",
        follow_up="Replace the `Map` with a 26-slot array for speed, or store a count per node to answer \"how many words have this prefix\".",
    ),
),
dict(
    id="js-design-add-and-search-words", title="Design Add and Search Words Data Structure", difficulty="Medium", pattern="Tries",
    leetcode="https://leetcode.com/problems/design-add-and-search-words-data-structure/",
    neetcode="https://neetcode.io/problems/design-word-search-data-structure",
    kind="js", entry="runWordDictionary",
    description=r"""
Implement class `WordDictionary`:

- `addWord(word)` stores a lowercase word
- `search(pattern)` returns `true` if some stored word matches `pattern`, where each `.` matches **any one**
  letter and other characters must match exactly (same length required)

Patterns have at most 2 dots in the original problem; your solution should still be correct with more.

**How the tests call your class.** Each test is `[ops, args]`, e.g.
`[["WordDictionary","addWord","addWord","search","search","search"], [[],["day"],["bay"],["say"],[".ay"],["b.."]]]`
→ `[null,null,null,false,true,true]`. The provided driver makes the calls.
""",
    starter="class WordDictionary {\n  constructor() {\n    // your fields\n  }\n  addWord(word) {}\n  search(pattern) {}\n}\n" + WD_DRIVER,
    solution=r'''class WordDictionary {
  constructor() { this.root = { children: new Map(), end: false }; }
  addWord(word) {
    let node = this.root;
    for (const c of word) {
      if (!node.children.has(c)) node.children.set(c, { children: new Map(), end: false });
      node = node.children.get(c);
    }
    node.end = true;
  }
  search(pattern) {
    const dfs = (node, i) => {
      if (i === pattern.length) return node.end;
      const c = pattern[i];
      if (c === ".") {
        for (const child of node.children.values()) if (dfs(child, i + 1)) return true;
        return false;
      }
      const next = node.children.get(c);
      return next !== undefined && dfs(next, i + 1);
    };
    return dfs(this.root, 0);
  }
}
''' + WD_DRIVER,
    tests=[
        [["WordDictionary", "addWord", "addWord", "search", "search", "search"], [[], ["day"], ["bay"], ["say"], [".ay"], ["b.."]]],
        [["WordDictionary", "addWord", "addWord", "addWord", "search", "search", "search", "search"], [[], ["bad"], ["dad"], ["mad"], ["pad"], ["bad"], [".ad"], ["b.."]]],
        [["WordDictionary", "search"], [[], ["."]]],
        [["WordDictionary", "addWord", "search", "search", "search"], [[], ["a"], ["."], ["a."], [".."]]],
        [["WordDictionary", "addWord", "addWord", "search", "search"], [[], ["ab"], ["abc"], ["ab."], ["a.c."]]],
        [["WordDictionary", "addWord", "search", "search"], [[], ["abc"], ["..."], ["ab"]]],
        wd_random(300, 9),
        wd_random(1500, 10),
    ],
    examples=2,
    wrong_solutions=[
        "class WordDictionary {\n  constructor() { this.w = new Set(); }\n  addWord(x) { this.w.add(x); }\n  search(p) { return this.w.has(p); }\n}\n" + WD_DRIVER,
        "class WordDictionary {\n  constructor() { this.w = []; }\n  addWord(x) { this.w.push(x); }\n  search(p) { const re = new RegExp(p); return this.w.some(x => re.test(x)); }\n}\n" + WD_DRIVER,
    ],
    guide=G(
        prereqs="The trie from *Implement Trie*, plus depth-first search with recursion.",
        intuition="A normal character follows exactly one child. A dot could be any letter, so try **every** child and succeed if any branch matches the rest of the pattern. That branching is a small DFS over the trie.",
        hints=[
            "Reuse your trie insert for `addWord`.",
            "Write `dfs(node, i)` meaning: can the pattern from index `i` be matched starting at `node`?",
            "On `.`, loop over `node.children.values()` and return `true` as soon as one branch works.",
        ],
        brute_force="Store words in an array and test each with an anchored regular expression `new RegExp(\"^\" + pattern + \"$\")`: O(words * length) per search.",
        approach="1. Trie with `children` `Map` and `end` flag.\n2. `dfs(node, i)`: at the end, return `node.end`; for `.` try all children; otherwise follow the one child.\n3. `search` returns `dfs(root, 0)`.",
        complexity="`addWord` O(L). `search` O(L) without dots; with d dots, up to O(26^d * L).",
        pitfalls="- A regex without `^` and `$` matches substrings: `\"ab\"` would match stored `\"abc\"`.\n- Forgetting to check `end` at the last character accepts prefixes.\n- Inner arrow functions see `pattern` through the closure, so you do not have to pass it down.",
        follow_up="Word Search II walks a grid and a trie together, pruning trie nodes once their words are found.",
    ),
),
]
