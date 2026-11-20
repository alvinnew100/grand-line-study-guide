import bisect as _b
import random as _r

_r.seed(79)


def _build(keys, t):
    """Build a B-tree of minimum degree t as nested [keys, children] lists."""
    root = [[], []]

    def split(parent, i):
        full = parent[1][i]
        right = [full[0][t:], full[1][t:]]
        median = full[0][t - 1]
        full[0], full[1] = full[0][:t - 1], full[1][:t]
        parent[0].insert(i, median)
        parent[1].insert(i + 1, right)

    for k in keys:
        if len(root[0]) == 2 * t - 1:
            root = [[], [root]]
            split(root, 0)
        node = root
        dup = False
        while node[1]:
            i = _b.bisect_left(node[0], k)
            if i < len(node[0]) and node[0][i] == k:
                dup = True
                break
            if len(node[1][i][0]) == 2 * t - 1:
                split(node, i)
                if k == node[0][i]:
                    dup = True
                    break
                if k > node[0][i]:
                    i += 1
            node = node[1][i]
        if not dup:
            i = _b.bisect_left(node[0], k)
            if i == len(node[0]) or node[0][i] != k:
                node[0].insert(i, k)
    return root


_small = [[42, 65], [
    [[22, 37], [[[11, 12], []], [[24, 29], []], [[38, 40, 41], []]]],
    [[46, 58], [[[43, 45], []], [[48, 50, 51, 53, 56], []], [[59, 63], []]]],
    [[72, 80, 93], [[[66, 70], []], [[74, 75], []], [[83, 85, 86], []], [[95, 98], []]]],
]]
_k1 = _r.sample(range(1000), 120)
_t1 = _build(_k1, 2)
_k2 = _r.sample(range(100000), 3000)
_t2 = _build(_k2, 8)
_t3 = _build(list(range(0, 4000, 2)), 3)

PROBLEMS = [
dict(
    id="dsaf-btree-search",
    title="B-Tree Search and Page Count",
    difficulty="Medium",
    pattern="Memory Management and B-Trees",
    entry="btree_search",
    description=r"""
A B-tree (Goodrich ch. 15.3) is given as nested lists: every node is `[keys, children]` where

- `keys` is a sorted list of the node's keys (distinct integers), and
- `children` is a list of `len(keys) + 1` child nodes — or the **empty list** for a leaf.

All keys in `children[i]` lie strictly between `keys[i-1]` and `keys[i]` (multiway search-tree
order). Each node stands for one disk page.

Implement `btree_search(root, key)` returning `[found, pages]`:

- `found` — whether `key` is stored in the tree;
- `pages` — the number of nodes (pages) **read** by the standard top-down search: read the root; if
  the key is in this node, stop; otherwise descend into the unique child whose range contains the
  key; if the node is a leaf, stop (not found).

Use **binary search inside each node** (`bisect` is available). The root may be `[[], []]` (an empty
tree): that is still one page read, and nothing is found.

**Example:** in the tree `[[20], [ [[5, 10], []], [[30, 40], []] ]]`:
`key = 30` → `[true, 2]`; `key = 20` → `[true, 1]`; `key = 7` → `[false, 2]`
""",
    starter='''import bisect


def btree_search(root, key):
    pass
''',
    solution='''import bisect


def btree_search(root, key):
    node, pages = root, 0
    while True:
        pages += 1
        keys, children = node
        i = bisect.bisect_left(keys, key)
        if i < len(keys) and keys[i] == key:
            return [True, pages]
        if not children:
            return [False, pages]
        node = children[i]
''',
    tests=[
        [[[20], [[[5, 10], []], [[30, 40], []]]], 30],
        [[[20], [[[5, 10], []], [[30, 40], []]]], 20],
        [[[20], [[[5, 10], []], [[30, 40], []]]], 7],
        [[[], []], 5],
        [[[1, 2, 3], []], 3],
        [[[1, 2, 3], []], 0],
        [[[20], [[[5, 10], []], [[30, 40], []]]], 50],
        [_small, 53],
        [_small, 65],
        [_small, 39],
        [_small, 98],
        [_small, 99],
        [_small, 11],
        [_t1, _k1[7]],
        [_t1, _k1[63]],
        [_t1, 1001],
        [_t1, -5],
        [_t2, _k2[1234]],
        [_t2, _k2[2999]],
        [_t2, 100001],
        [_t3, 2001],
        [_t3, 3998],
    ],
    examples=3,
    wrong_solutions=[
        '''def btree_search(root, key):
    pages = 0
    def walk(node):
        nonlocal pages
        pages += 1
        if key in node[0]:
            return True
        return any(walk(c) for c in node[1])
    return [walk(root), pages]
''',
        '''import bisect
def btree_search(root, key):
    node, pages = root, 0
    while True:
        pages += 1
        keys, children = node
        i = bisect.bisect_right(keys, key)
        if not children:
            return [key in keys, pages]
        node = children[i]
''',
        '''import bisect
def btree_search(root, key):
    node, pages = root, 1
    while True:
        keys, children = node
        i = bisect.bisect_left(keys, key)
        if i < len(keys) and keys[i] == key:
            return [True, pages]
        if not children:
            return [False, pages]
        node = children[min(i, len(children) - 1) if i else 0]
        pages += 1 if i else 2
''',
    ],
    guide=dict(
        prereqs="Lesson *External searching: (a,b) trees and B-trees*; multiway search from the (2,4)-tree lesson; `bisect`.",
        intuition="A B-tree node is a sorted array of separators. Binary search tells you either that the key is right here, or which gap it falls into — and the i-th gap leads to the i-th child. One node per level means one page read per level.",
        hints=["i = bisect.bisect_left(keys, key) is the number of keys smaller than `key`.",
               "If i < len(keys) and keys[i] == key: found in this node.",
               "Otherwise, if the node is a leaf: not found; else continue with children[i]. Count a page each time you look at a node."],
        brute_force="Traverse the whole tree (first wrong solution): finds the key but reads up to every page — O(n/B) transfers instead of O(log_B n).",
        approach="""
Loop: pages += 1; binary-search the node; found → return; leaf → return not found; else descend.

Trace in the lesson's order-6 tree for key 53: root [42 65] → 53 falls in gap 1 → node [46 58] → gap 1 → leaf [48 50 51 53 56] → found: `[True, 3]`. For key 65: found in the root: `[True, 1]`.
""",
        complexity="O(log_B n) page reads (the height), and O(log B) comparisons inside each page: O(log n) comparisons in total. O(1) extra space.",
        pitfalls="Descending past a node that already contains the key (second wrong solution only looks in leaves — a B+-tree habit — so it misses internal keys and over-counts pages); visiting several children; forgetting that an empty root still counts as one page read; linear scans inside big nodes waste CPU (not transfers).",
        follow_up="Implement insertion with node splitting; convert to a B+ tree (all keys in leaves, leaves linked) and support range queries.",
    ),
),
]
