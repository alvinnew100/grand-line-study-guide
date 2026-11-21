"""Extra practice for the priority-queue, hashing/skip-list and memory/B-tree modules."""
import random as _r


def _mutate(src, old, new):
    """Derive a wrong solution from a reference one by replacing one exact snippet."""
    assert old in src, old
    return src.replace(old, new, 1)


# ---------------------------------------------------------------- generators

def _apq_ops(n, seed, keyrange):
    """Random AdaptablePQ workload; a small model tracks which locators are alive."""
    rnd = _r.Random(seed)
    ops, args = ["AdaptablePQ"], [[]]
    alive, issued, nxt = {}, [], 1           # loc -> key
    for i in range(n):
        x = rnd.random()
        if x < 0.33 or not alive:
            k = rnd.randint(0, keyrange)
            ops.append("add"); args.append([k, "v%d" % i])
            alive[nxt] = k; issued.append(nxt); nxt += 1
        elif x < 0.53:
            loc = rnd.choice(list(alive)) if rnd.random() < 0.9 else rnd.choice(issued + [0, nxt + 3])
            k = rnd.randint(0, keyrange)
            ops.append("update"); args.append([loc, k, "u%d" % i])
            if loc in alive:
                alive[loc] = k
        elif x < 0.68:
            loc = rnd.choice(list(alive)) if rnd.random() < 0.85 else rnd.choice(issued + [0])
            ops.append("remove"); args.append([loc])
            alive.pop(loc, None)
        elif x < 0.85:
            ops.append("remove_min"); args.append([])
            loc = min(alive, key=lambda q: (alive[q], q))
            del alive[loc]
        else:
            ops.append(rnd.choice(["min", "size"])); args.append([])
    ops += ["remove_min"] * (len(alive) + 1)
    args += [[]] * (len(alive) + 1)
    return [ops, args]


def _probe_ops(n, seed, N, keygen, cells_every=0):
    rnd = _r.Random(seed)
    ops, args = ["ProbingMap"], [[N]]
    keys = []
    for i in range(n):
        x = rnd.random()
        if x < 0.45:
            k = keygen(rnd)
            ops.append("put"); args.append([k, rnd.randint(0, 999)]); keys.append(k)
        elif x < 0.70:
            k = rnd.choice(keys) if keys and rnd.random() < 0.7 else keygen(rnd)
            ops.append("get"); args.append([k])
        elif x < 0.90:
            k = rnd.choice(keys) if keys and rnd.random() < 0.8 else keygen(rnd)
            ops.append("remove"); args.append([k])
        else:
            ops.append("size"); args.append([])
        if cells_every and i % cells_every == cells_every - 1:
            ops.append("cells"); args.append([])
    ops.append("cells"); args.append([])
    return [ops, args]


def _skip_ops(n, seed, span):
    rnd = _r.Random(seed)
    ops, args = ["SkipListMap"], [[]]
    keys = []
    for i in range(n):
        x = rnd.random()
        if x < 0.40:
            k, h = rnd.randint(-span, span), 1
            while rnd.random() < 0.5 and h < 16:
                h += 1
            ops.append("put"); args.append([k, "v%d" % i, h]); keys.append(k)
        elif x < 0.55:
            k = rnd.choice(keys) if keys and rnd.random() < 0.8 else rnd.randint(-span, span)
            ops.append("remove"); args.append([k])
        elif x < 0.72:
            ops.append("steps"); args.append([rnd.randint(-span - 3, span + 3)])
        elif x < 0.82:
            k = rnd.choice(keys) if keys and rnd.random() < 0.6 else rnd.randint(-span, span)
            ops.append("get"); args.append([k])
        elif x < 0.95:
            ops.append(rnd.choice(["find_ge", "find_lt"])); args.append([rnd.randint(-span - 3, span + 3)])
        else:
            ops.append("size"); args.append([])
    ops.append("keys"); args.append([])
    return [ops, args]


def _rand_heap(n, m, roots, seed):
    rnd = _r.Random(seed)
    refs = [[] for _ in range(n)]
    for _ in range(m):
        refs[rnd.randrange(n)].append(rnd.randrange(n))
    return [refs, [rnd.randrange(n) for _ in range(roots)]]


def _rand_keys(n, span, seed):
    rnd = _r.Random(seed)
    return [rnd.randint(0, span) for _ in range(n)]


# ---------------------------------------------------------------- reference solutions used for mutations

_APQ_SOL = '''class AdaptablePQ:
    def __init__(self):
        self._heap = []          # entries [key, loc, value, index], in heap order
        self._where = {}         # loc -> entry, for entries still in the queue
        self._next = 1

    def _less(self, i, j):
        a, b = self._heap[i], self._heap[j]
        return (a[0], a[1]) < (b[0], b[1])       # key first, then locator

    def _swap(self, i, j):
        h = self._heap
        h[i], h[j] = h[j], h[i]
        h[i][3], h[j][3] = i, j                  # entries always know their index

    def _upheap(self, j):
        while j > 0 and self._less(j, (j - 1) // 2):
            self._swap(j, (j - 1) // 2)
            j = (j - 1) // 2

    def _downheap(self, j):
        n = len(self._heap)
        while 2 * j + 1 < n:
            c = 2 * j + 1
            if c + 1 < n and self._less(c + 1, c):
                c += 1
            if self._less(c, j):
                self._swap(j, c)
                j = c
            else:
                break

    def _bubble(self, j):
        if j > 0 and self._less(j, (j - 1) // 2):
            self._upheap(j)
        else:
            self._downheap(j)

    def add(self, k, v):
        loc = self._next
        self._next += 1
        entry = [k, loc, v, len(self._heap)]
        self._heap.append(entry)
        self._where[loc] = entry
        self._upheap(len(self._heap) - 1)
        return loc

    def min(self):
        if not self._heap:
            return None
        e = self._heap[0]
        return [e[0], e[2]]

    def remove_min(self):
        if not self._heap:
            return None
        return self.remove(self._heap[0][1])

    def update(self, loc, k, v):
        e = self._where.get(loc)
        if e is None:
            return False
        e[0], e[2] = k, v
        self._bubble(e[3])
        return True

    def remove(self, loc):
        e = self._where.pop(loc, None)
        if e is None:
            return None
        j, last = e[3], len(self._heap) - 1
        if j != last:
            self._swap(j, last)
        self._heap.pop()
        if j < len(self._heap):
            self._bubble(j)
        return [e[0], e[2]]

    def size(self):
        return len(self._heap)
'''

_PROBE_SOL = '''_DELETED = object()        # deletion marker (tombstone)


class ProbingMap:
    def __init__(self, N):
        self._table = [None] * N      # None, _DELETED, or [key, value]
        self._n = 0

    def _find(self, k):
        """(True, j) if k is in cell j; else (False, first reusable cell or -1)."""
        N = len(self._table)
        j = k % N
        free = -1
        for _ in range(N):            # never examine more than N cells
            cell = self._table[j]
            if cell is None:
                return False, (j if free == -1 else free)
            if cell is _DELETED:
                if free == -1:
                    free = j
            elif cell[0] == k:
                return True, j
            j = (j + 1) % N
        return False, free

    def put(self, k, v):
        found, j = self._find(k)
        if found:
            self._table[j][1] = v
        elif j != -1:
            self._table[j] = [k, v]
            self._n += 1
        return j

    def get(self, k):
        found, j = self._find(k)
        return self._table[j][1] if found else -1

    def remove(self, k):
        found, j = self._find(k)
        if found:
            self._table[j] = _DELETED
            self._n -= 1
        return found

    def size(self):
        return self._n

    def cells(self):
        return [None if c is None else "X" if c is _DELETED else c[0] for c in self._table]
'''

_SKIP_SOL = '''class _SNode:
    __slots__ = "key", "value", "next"

    def __init__(self, key, value, h):
        self.key, self.value, self.next = key, value, [None] * h


class SkipListMap:
    MAX = 16

    def __init__(self):
        self._head = _SNode(None, None, self.MAX)    # the minus-infinity tower
        self._n = 0

    def _walk(self, k):
        """Predecessor of k on every level, and the number of forward moves made."""
        preds, x, steps = [None] * self.MAX, self._head, 0
        for i in range(self.MAX - 1, -1, -1):        # top level down
            while x.next[i] is not None and x.next[i].key < k:
                x = x.next[i]                        # scan forward
                steps += 1
            preds[i] = x                             # then drop down
        return preds, steps

    def put(self, k, v, h):
        preds, _ = self._walk(k)
        x = preds[0].next[0]
        if x is not None and x.key == k:
            x.value = v
            return None
        node = _SNode(k, v, h)
        for i in range(h):                           # splice the tower in, level by level
            node.next[i] = preds[i].next[i]
            preds[i].next[i] = node
        self._n += 1
        return None

    def get(self, k):
        x = self._walk(k)[0][0].next[0]
        return x.value if x is not None and x.key == k else None

    def remove(self, k):
        preds, _ = self._walk(k)
        x = preds[0].next[0]
        if x is None or x.key != k:
            return False
        for i in range(len(x.next)):
            preds[i].next[i] = x.next[i]
        self._n -= 1
        return True

    def find_ge(self, k):
        x = self._walk(k)[0][0].next[0]
        return None if x is None else [x.key, x.value]

    def find_lt(self, k):
        p = self._walk(k)[0][0]
        return None if p is self._head else [p.key, p.value]

    def steps(self, k):
        return self._walk(k)[1]

    def keys(self):
        out, x = [], self._head.next[0]
        while x is not None:
            out.append(x.key)
            x = x.next[0]
        return out

    def size(self):
        return self._n
'''

_GC_SOL = '''from collections import deque


def collect(refs, roots):
    n = len(refs)
    # mark: iterative depth-first search from the roots
    marked = [False] * n
    stack = list(roots)
    while stack:
        v = stack.pop()
        if not marked[v]:
            marked[v] = True
            stack.extend(refs[v])
    garbage = [v for v in range(n) if not marked[v]]
    # reference counting: count every incoming reference, then cascade the frees
    count = [0] * n
    for v in range(n):
        for w in refs[v]:
            count[w] += 1
    for r in roots:
        count[r] += 1
    freed = [False] * n
    queue = deque(v for v in range(n) if count[v] == 0)
    while queue:
        v = queue.popleft()
        freed[v] = True
        for w in refs[v]:
            count[w] -= 1
            if count[w] == 0:
                queue.append(w)
    stuck = [v for v in garbage if not freed[v]]
    return [garbage, stuck]
'''

_BT_SOL = '''import bisect


def btree_insert(d, keys):
    root = [[], []]

    def insert(node, k):
        """Insert k below node; return (median, right_node) if node split, else None."""
        ks, ch = node
        i = bisect.bisect_left(ks, k)
        if i < len(ks) and ks[i] == k:
            return None                          # duplicate: ignore
        if ch:                                   # internal node: go down first
            res = insert(ch[i], k)
            if res is None:
                return None
            median, right = res
            ks.insert(i, median)
            ch.insert(i + 1, right)
        else:
            ks.insert(i, k)
        if len(ks) < d:
            return None
        m = d // 2                               # overflow: split around keys[m]
        median = ks[m]
        right = [ks[m + 1:], ch[m + 1:]]
        node[0], node[1] = ks[:m], ch[:m + 1]
        return median, right

    for k in keys:
        res = insert(root, k)
        if res is not None:                      # the root split: grow a new root
            median, right = res
            root = [[median], [root, right]]
    return root
'''


PROBLEMS = [
# ---------------------------------------------------------------- priority queues
dict(
    id="dsaf-adaptable-pq",
    title="Adaptable Priority Queue with Locators",
    difficulty="Medium",
    pattern="Priority Queues",
    kind="class",
    entry="AdaptablePQ",
    description=r"""
Extend the binary-heap priority queue with **locators** (Goodrich ch. 9.5) so that an entry can be
changed or removed after it was added. Locators are integer tickets: the first `add` returns `1`,
the second `2`, and so on.

| Operation | Returns |
|---|---|
| `add(k, v)` | the locator of the new entry |
| `min()` | `[k, v]` of the smallest entry, or `None` if the queue is empty |
| `remove_min()` | removes the smallest entry and returns its `[k, v]`, or `None` |
| `update(loc, k, v)` | `True` after giving that entry key `k` and value `v`; `False` if `loc` is invalid |
| `remove(loc)` | removes that entry and returns its `[k, v]`; `None` if `loc` is invalid |
| `size()` | the number of entries |

Entries are ordered by key, and **equal keys are ordered by locator** (smaller locator first). A
locator is invalid if it was never issued or its entry has already left the queue (through `remove`
or `remove_min`). `update` keeps the entry's locator.

Use an array-based heap whose entries remember their own index, so that `add`, `remove_min`,
`update` and `remove` all run in $O(\log n)$. Never search the array for an entry.

**Example:** `["AdaptablePQ","add","add","add","add","update","remove","min","remove_min","remove_min","size"]`,
`[[],[6,"cat"],[2,"owl"],[8,"elk"],[4,"bee"],[3,1,"elk"],[2],[],[],[],[]]` →
`[null,1,2,3,4,true,[2,"owl"],[1,"elk"],[1,"elk"],[4,"bee"],1]`

**Example:** `["AdaptablePQ","min","remove_min","add","remove_min","remove","update","size"]`,
`[[],[],[],[5,"x"],[],[1],[1,2,"y"],[]]` → `[null,null,null,1,[5,"x"],null,false,0]`
""",
    starter='''class AdaptablePQ:
    def __init__(self):
        self._heap = []      # suggestion: entries [key, loc, value, index]
        self._where = {}     # loc -> entry
        self._next = 1

    def add(self, k, v):
        pass

    def min(self):
        pass

    def remove_min(self):
        pass

    def update(self, loc, k, v):
        pass

    def remove(self, loc):
        pass

    def size(self):
        pass
''',
    solution=_APQ_SOL,
    tests=[
        [["AdaptablePQ", "add", "add", "add", "add", "update", "remove", "min", "remove_min", "remove_min", "size"],
         [[], [6, "cat"], [2, "owl"], [8, "elk"], [4, "bee"], [3, 1, "elk"], [2], [], [], [], []]],
        [["AdaptablePQ", "min", "remove_min", "add", "remove_min", "remove", "update", "size"],
         [[], [], [], [5, "x"], [], [1], [1, 2, "y"], []]],
        [["AdaptablePQ", "add", "add", "add", "update", "remove_min", "remove_min", "add", "remove_min", "remove_min", "remove_min"],
         [[], [5, "z"], [5, "a"], [5, "m"], [1, 5, "z2"], [], [], [5, "b"], [], [], []]],
        [["AdaptablePQ"] + ["add"] * 7 + ["update", "min"] + ["remove_min"] * 8,
         [[]] + [[k, "e%d" % k] for k in [1, 2, 3, 4, 5, 6, 7]] + [[1, 100, "big"], []] + [[]] * 8],
        [["AdaptablePQ"] + ["add"] * 8 + ["update", "min", "update", "update", "min", "size"],
         [[]] + [[k, k] for k in range(10, 90, 10)] + [[8, 5, "five"], [], [8, 85, 85], [4, 45, "mid"], [], []]],
        [["AdaptablePQ"] + ["add"] * 7 + ["remove", "remove_min", "remove_min", "min", "remove_min", "remove_min", "remove_min", "remove_min", "remove_min"],
         [[]] + [[k, "k%d" % k] for k in [1, 50, 10, 60, 70, 40, 20]] + [[4]] + [[]] * 8],
        [["AdaptablePQ"] + ["add"] * 6 + ["remove", "remove", "remove", "update", "remove", "remove", "remove", "remove", "min", "size", "add", "min"],
         [[]] + [[k, k] for k in [9, 3, 7, 1, 8, 2]] + [[6], [4], [1], [4, 0, 0], [2], [3], [5], [5], [], [], [4, "back"], []]],
        [["AdaptablePQ", "add", "add", "remove_min", "update", "remove", "update", "min", "add", "update", "remove_min", "remove_min"],
         [[], [3, "p"], [3, "q"], [], [1, 0, "p"], [1], [2, 9, "q"], [], [4, "r"], [3, 1, "r"], [], []]],
        _apq_ops(300, 71, 50),
        _apq_ops(1500, 72, 200),
        _apq_ops(4000, 73, 10 ** 6),
    ],
    examples=2,
    wrong_solutions=[
        _mutate(_APQ_SOL, "        e[0], e[2] = k, v\n        self._bubble(e[3])", "        e[0], e[2] = k, v\n        self._upheap(e[3])"),
        _mutate(_APQ_SOL, "        if j < len(self._heap):\n            self._bubble(j)", "        if j < len(self._heap):\n            self._downheap(j)"),
        _mutate(_APQ_SOL, "return (a[0], a[1]) < (b[0], b[1])", "return (a[0], str(a[2])) < (b[0], str(b[2]))"),
    ],
    guide=dict(
        prereqs="Lessons *Priority queues and binary heaps* (up-heap, down-heap, the array layout) and *PQ sorting, heap-sort and adaptable priority queues* (sections 3 and 4: locators and how they stay valid).",
        intuition="A heap can find its minimum instantly but any other entry only by searching. Give every entry a ticket and let the entry carry its current array index; then the ticket leads straight to the cell. The one rule that makes it work: every swap rewrites the index of both entries it moves.",
        hints=["Store each entry as a small mutable record `[key, loc, value, index]`, keep `loc -> entry` in a dictionary, and compare entries by `(key, loc)`.",
               "update: change key and value in place, then bubble at the entry's index: up if it is now smaller than its parent, otherwise down.",
               "remove: swap the entry with the last cell, pop it off, and bubble the entry that moved into the hole. That entry may need to go UP, not only down."],
        brute_force="Keep the entries in an unsorted list and scan for the minimum or for a locator: add is O(1) but min, remove_min, update and remove are O(n). Rebuilding a heap after every change is O(n) too.",
        approach="""
- `add`: append `[k, loc, v, n]`, register it, up-heap from the last index.
- `remove_min`: `remove(loc of the root)`.
- `remove(loc)`: look the entry up (absent → `None`), swap it with the last cell, pop, then `_bubble(j)` if `j` is still inside the array.
- `update(loc, k, v)`: look up, assign, `_bubble(index)`.

Dry run of the first example. Adds give `2:owl 4:bee 8:elk 6:cat` (owl rose to the root, bee rose above cat). `update(3, 1, "elk")`: elk sits at index 2, its key 1 beats its parent owl, so it moves up to the root: `1:elk 4:bee 2:owl 6:cat`. `remove(2)`: owl is at index 2; swap with the last cell (cat), pop, bubble cat: no parent issue, no children, so it stays: `1:elk 4:bee 6:cat`. Then min and remove_min give `[1, "elk"]`, the next remove_min gives `[4, "bee"]`, and one entry remains.

Why remove may need an up-heap: the last cell comes from a different subtree, so it can be smaller than the parent of the hole it fills. Adding keys 1, 50, 10, 60, 70, 40, 20 and removing the 60 moves 20 under 50.
""",
        complexity="add, remove_min, update and remove each do O(1) work plus one bubble along a root-to-leaf path: O(log n). min and size are O(1). Space O(n) for the heap and the locator dictionary.",
        pitfalls="Forgetting to update the stored index on every swap (locators then point at the wrong cell); only up-heaping in update (a key that grows must sink); only down-heaping after remove; letting a removed locator still answer; breaking ties by value instead of by locator.",
        follow_up="Use the queue for Dijkstra's algorithm: keep one locator per vertex and call update when a shorter distance is found, instead of pushing duplicate entries (lazy deletion).",
    ),
),
# ---------------------------------------------------------------- hashing
dict(
    id="dsaf-linear-probing",
    title="Linear Probing with Deletion Markers",
    difficulty="Medium",
    pattern="Maps and Hash Tables",
    kind="class",
    entry="ProbingMap",
    description=r"""
Implement a map from integer keys to non-negative integer values using **open addressing with
linear probing** (Goodrich ch. 10.2.2) in a table of fixed capacity `N` that never grows. Do not use
`dict` or `set`.

- The home cell of key `k` is `k % N` (Python's `%`, so negative keys work). A probe examines cells
  `home, home + 1, ...`, wrapping round from `N - 1` to `0`, and looks at **at most `N` cells**.
- `remove(k)` must not empty the cell: it leaves a **deletion marker**. Searches walk past markers
  and stop only at a never-used cell, at the key itself, or after `N` cells.
- `put(k, v)`: if `k` is present, overwrite its value. Otherwise store `k` in the **first** marker
  or never-used cell met during the probe, but keep probing past markers first, to be sure `k` is not
  stored further on. Return the index of the cell that holds `k`, or `-1` if `k` is absent and no
  cell is free.
- `get(k)` → the value, or `-1` if absent. `remove(k)` → `True` if a key was removed, else `False`.
- `size()` → the number of keys stored.
- `cells()` → the table as a list of length `N`: the key of an occupied cell, `None` for a
  never-used cell, `"X"` for a deletion marker.

`1 <= N <= 2003`.

**Example:** `["ProbingMap","put","put","put","put","put","cells","get","remove","cells","get","put"]`,
`[[7],[10,1],[17,2],[3,3],[6,4],[13,5],[],[13],[17],[],[3],[24,6]]` →
`[null,3,4,5,6,0,[13,null,null,10,17,3,6],5,true,[13,null,null,10,"X",3,6],3,4]`

(10, 17, 3 and later 24 all have home cell 3; 13 has home cell 6 and wraps round to cell 0. The search
for 24 passes the marker in cell 4, checks cells 5, 6, 0, stops at the never-used cell 1, and then
reuses cell 4.)
""",
    starter='''_DELETED = object()        # use this as the deletion marker


class ProbingMap:
    def __init__(self, N):
        self._table = [None] * N
        self._n = 0

    def put(self, k, v):
        pass

    def get(self, k):
        pass

    def remove(self, k):
        pass

    def size(self):
        pass

    def cells(self):
        pass
''',
    solution=_PROBE_SOL,
    tests=[
        [["ProbingMap", "put", "put", "put", "put", "put", "cells", "get", "remove", "cells", "get", "put"],
         [[7], [10, 1], [17, 2], [3, 3], [6, 4], [13, 5], [], [13], [17], [], [3], [24, 6]]],
        [["ProbingMap", "put", "put", "put", "remove", "put", "size", "cells", "get"],
         [[5], [1, 10], [6, 20], [11, 30], [6], [11, 31], [], [], [11]]],
        [["ProbingMap", "put", "put", "put", "put", "get", "remove", "size", "remove", "get", "put", "cells"],
         [[3], [0, 1], [1, 1], [2, 1], [5, 9], [5], [4], [], [1], [7], [7, 2], []]],
        [["ProbingMap", "put", "put", "get", "put", "remove", "get", "put", "cells", "size"],
         [[1], [5, 1], [5, 2], [5], [6, 1], [5], [5], [6, 3], [], []]],
        [["ProbingMap", "put", "put", "put", "get", "remove", "get", "cells", "put", "cells"],
         [[10], [-1, 1], [9, 2], [-11, 3], [-11], [9], [-11], [], [19, 4], []]],
        [["ProbingMap", "put", "put", "put", "put", "put", "remove", "remove", "remove", "remove", "remove", "size", "get", "put", "cells"],
         [[5], [0, 0], [1, 1], [2, 2], [3, 3], [4, 4], [0], [1], [2], [3], [4], [], [3], [8, 1], []]],
        [["ProbingMap", "get", "remove", "size", "cells"], [[4], [2], [2], [], []]],
        _probe_ops(1500, 81, 101, lambda rnd: rnd.randint(-300, 300), 100),
        _probe_ops(1200, 82, 211, lambda rnd: rnd.randint(0, 20) * 211 + rnd.randint(0, 10), 400),
        _probe_ops(3000, 83, 2003, lambda rnd: rnd.randint(-5000, 5000)),
        _probe_ops(400, 84, 17, lambda rnd: rnd.randint(0, 60), 20),
    ],
    examples=2,
    wrong_solutions=[
        _mutate(_PROBE_SOL, "            self._table[j] = _DELETED", "            self._table[j] = None"),
        _mutate(_PROBE_SOL, "                if free == -1:\n                    free = j", "                return False, j"),
        '''_DELETED = object()
class ProbingMap:
    def __init__(self, N):
        self._table = [None] * N
        self._n = 0
    def put(self, k, v):
        N = len(self._table)
        j = k % N
        for _ in range(N):
            cell = self._table[j]
            if cell is None or cell is _DELETED:
                self._table[j] = [k, v]
                self._n += 1
                return j
            if cell[0] == k:
                cell[1] = v
                return j
            j = (j + 1) % N
        return -1
    def get(self, k):
        N = len(self._table)
        j = k % N
        for _ in range(N):
            cell = self._table[j]
            if cell is None:
                return -1
            if cell is not _DELETED and cell[0] == k:
                return cell[1]
            j = (j + 1) % N
        return -1
    def remove(self, k):
        N = len(self._table)
        j = k % N
        for _ in range(N):
            cell = self._table[j]
            if cell is None:
                return False
            if cell is not _DELETED and cell[0] == k:
                self._table[j] = _DELETED
                self._n -= 1
                return True
            j = (j + 1) % N
        return False
    def size(self):
        return self._n
    def cells(self):
        return [None if c is None else "X" if c is _DELETED else c[0] for c in self._table]
''',
    ],
    guide=dict(
        prereqs="Lesson *Collision handling, load factors and rehashing*, section 2 (open addressing, linear probing, the deletion marker). The hash-map-with-chaining problem of this module is a good warm-up.",
        intuition="Every key lives somewhere along a run of occupied cells that starts at its home cell. A search may stop only where an insertion of that key would have stopped: at a cell that was never used. A deleted cell must therefore stay 'in the way' (a marker), or the keys stored beyond it become unreachable.",
        hints=["Write one helper `_find(k)` returning either `(True, j)` (k is in cell j) or `(False, j)` (j is where k should go, or -1 if the table is full). Build put, get and remove on it.",
               "While probing, remember the FIRST marker you pass, but keep going until you hit the key, a never-used cell, or N cells.",
               "Bound the loop with `for _ in range(N)`: once every cell holds a key or a marker, no never-used cell exists and an unbounded `while` would spin for ever."],
        brute_force="A plain list of `[key, value]` pairs scanned from the start: O(n) per operation, and it ignores hashing entirely. Within open addressing, rebuilding the whole table after each removal (instead of leaving a marker) also works but costs O(N) per removal.",
        approach="""
`_find(k)`: `j = k % N`, `free = -1`; repeat N times: never-used cell → return `(False, j if free == -1 else free)`; marker → record it in `free` if it is the first; matching key → `(True, j)`; advance `j = (j + 1) % N`. After N cells, return `(False, free)`.

- put: found → overwrite the value; else if `j != -1` store `[k, v]` there and count it; return `j`.
- get: the value if found, else -1.
- remove: if found, put the marker in the cell and decrement the count.

Dry run of the example (N = 7): 10 → cell 3; 17 → 3 taken → 4; 3 → 3, 4 taken → 5; 6 → 6; 13 → home 6 taken → wraps to 0. Removing 17 leaves `X` in cell 4. get(3) walks 3 (holds 10), 4 (marker, keep going), 5 (found). put(24): cells 3, 4 (first marker, remembered), 5, 6, 0, then 1 is never used, so 24 is absent: store it in cell 4.
""",
        complexity="Expected O(1) per operation while the load factor (counting markers) stays well below 1; worst case O(N) when long clusters form, and an unsuccessful search in a table without never-used cells examines all N cells. cells() is O(N). Space O(N).",
        pitfalls="Emptying the cell on remove (keys further along disappear); treating a marker as the end of a search; stopping put at the first marker without checking whether the key is stored further along (creates a duplicate); looping for ever on a table full of keys and markers; forgetting that `size` counts keys, not markers.",
        follow_up="Add rehashing: when keys plus markers exceed N/2, rebuild a table of about 2N cells (markers are dropped in the process). Try quadratic probing or double hashing and measure the average cluster length.",
    ),
),
# ---------------------------------------------------------------- skip lists
dict(
    id="dsaf-skip-list",
    title="Skip-List Sorted Map with Fixed Tower Heights",
    difficulty="Hard",
    pattern="Maps and Hash Tables",
    kind="class",
    entry="SkipListMap",
    description=r"""
Implement a sorted map as a **skip list** (Goodrich ch. 10.4). To make the structure reproducible, the
coin tosses are replaced by an explicit tower height: `put(k, v, h)` inserts a new key with a tower
of `h` levels (`1 <= h <= 16`), so the key appears in the lists $S_0, \ldots, S_{h-1}$.

- `put(k, v, h)` — insert `k`; if `k` is already present, only replace its value (the tower stays as
  it is and `h` is ignored). Returns `None`.
- `get(k)` → the value, or `None`.
- `remove(k)` → `True` if `k` was present (unlink its whole tower), else `False`.
- `find_ge(k)` → `[key, value]` for the smallest key `>= k`, or `None`; `find_lt(k)` →
  `[key, value]` for the largest key `< k`, or `None`.
- `keys()` → all keys in increasing order; `size()` → how many keys.
- `steps(k)` → the number of **forward moves** of the search for `k`: start at the head of the top
  level; on each level move forward while the next key on that level is **smaller than** `k`,
  counting one step per move; then drop to the level below; finish after level 0.

Keys are integers. Each operation except `keys` must cost time proportional to the steps of its
search plus the number of levels, never a scan of the whole bottom list.

**Example:** `["SkipListMap","put","put","put","put","put","steps","steps","steps","find_ge","find_lt","get"]`,
`[[],[30,"c",1],[10,"a",2],[50,"e",3],[20,"b",1],[40,"d",2],[45],[30],[60],[35],[10],[20]]` →
`[null,null,null,null,null,null,2,2,1,[40,"d"],null,"b"]`

Level 2 holds `50`, level 1 holds `10 40 50`, level 0 holds all five keys. The search for `45` moves
to `10` and then `40` on level 1 (2 steps) and finds nothing smaller than 45 to move to on levels 2 and 0.
""",
    starter='''class _SNode:
    __slots__ = "key", "value", "next"

    def __init__(self, key, value, h):
        self.key, self.value, self.next = key, value, [None] * h   # next[i] = successor on level i


class SkipListMap:
    MAX = 16

    def __init__(self):
        self._head = _SNode(None, None, self.MAX)
        self._n = 0

    def put(self, k, v, h):
        pass

    def get(self, k):
        pass

    def remove(self, k):
        pass

    def find_ge(self, k):
        pass

    def find_lt(self, k):
        pass

    def steps(self, k):
        pass

    def keys(self):
        pass

    def size(self):
        pass
''',
    solution=_SKIP_SOL,
    tests=[
        [["SkipListMap", "put", "put", "put", "put", "put", "steps", "steps", "steps", "find_ge", "find_lt", "get"],
         [[], [30, "c", 1], [10, "a", 2], [50, "e", 3], [20, "b", 1], [40, "d", 2], [45], [30], [60], [35], [10], [20]]],
        [["SkipListMap", "put", "put", "get", "steps", "put", "remove", "steps", "keys", "remove", "size"],
         [[], [5, "x", 2], [5, "y", 4], [5], [6], [7, "z", 1], [5], [8], [], [5], []]],
        [["SkipListMap", "get", "steps", "find_ge", "find_lt", "keys", "size", "remove"],
         [[], [1], [1], [0], [0], [], [], [3]]],
        [["SkipListMap"] + ["put"] * 6 + ["steps", "steps", "steps", "steps"],
         [[]] + [[k, k, 1] for k in [6, 2, 9, 4, 1, 7]] + [[0], [5], [7], [100]]],
        [["SkipListMap"] + ["put"] * 7 + ["steps", "steps", "steps", "find_ge", "find_lt"],
         [[]] + [[100, "t", 10]] + [[k, "s", 1] for k in [10, 20, 30, 110, 120, 130]] + [[1000], [100], [105], [100], [100]]],
        [["SkipListMap", "put", "put", "put", "put", "find_ge", "find_lt", "find_ge", "find_lt", "find_ge", "find_lt"],
         [[], [-5, "m5", 3], [0, "z", 1], [5, "p5", 2], [-10, "m10", 1], [-5], [-5], [6], [6], [-11], [-11]]],
        [["SkipListMap", "put", "put", "put", "put", "put", "remove", "steps", "steps", "remove", "steps", "keys"],
         [[], [10, "a", 1], [20, "b", 5], [30, "c", 1], [40, "d", 3], [50, "e", 1], [20], [45], [35], [40], [55], []]],
        [["SkipListMap", "put", "put", "put", "put", "get", "size", "steps", "put", "steps", "find_ge"],
         [[], [3, "a", 16], [1, "b", 16], [2, "c", 16], [3, "d", 1], [3], [], [3], [4, "e", 1], [5], [4]]],
        _skip_ops(600, 91, 200),
        _skip_ops(3000, 92, 10 ** 6),
        _skip_ops(2000, 93, 60),
    ],
    examples=2,
    wrong_solutions=[
        '''import bisect
class SkipListMap:
    def __init__(self):
        self._k, self._v = [], []
    def put(self, k, v, h):
        i = bisect.bisect_left(self._k, k)
        if i < len(self._k) and self._k[i] == k:
            self._v[i] = v
        else:
            self._k.insert(i, k)
            self._v.insert(i, v)
    def get(self, k):
        i = bisect.bisect_left(self._k, k)
        return self._v[i] if i < len(self._k) and self._k[i] == k else None
    def remove(self, k):
        i = bisect.bisect_left(self._k, k)
        if i < len(self._k) and self._k[i] == k:
            del self._k[i]
            del self._v[i]
            return True
        return False
    def find_ge(self, k):
        i = bisect.bisect_left(self._k, k)
        return [self._k[i], self._v[i]] if i < len(self._k) else None
    def find_lt(self, k):
        i = bisect.bisect_left(self._k, k)
        return [self._k[i - 1], self._v[i - 1]] if i else None
    def steps(self, k):
        return bisect.bisect_left(self._k, k)
    def keys(self):
        return list(self._k)
    def size(self):
        return len(self._k)
''',
        _mutate(_SKIP_SOL, "    def steps(self, k):\n        return self._walk(k)[1]",
                "    def steps(self, k):\n        x, steps = self._head, 0\n        for i in range(self.MAX - 1, -1, -1):\n"
                "            while x.next[i] is not None and x.next[i].key <= k:\n                x = x.next[i]\n                steps += 1\n"
                "        return steps"),
        _mutate(_SKIP_SOL, "        for i in range(len(x.next)):\n            preds[i].next[i] = x.next[i]",
                "        for i in range(1):\n            preds[i].next[i] = x.next[i]"),
    ],
    guide=dict(
        prereqs="Lesson *Sorted maps, skip lists, sets and multimaps* (section 1: the sorted map ADT; section 3: skip-list structure, search, insertion and deletion).",
        intuition="Each level is an express lane over the one below. A search rides the highest lane as far as it can without overshooting, then changes down. The last node visited on each level is exactly where a new tower must be spliced in, or an old one unlinked, so a single walk serves every operation.",
        hints=["Represent each key by ONE node whose list `next[i]` holds its successor on level i; the head is a node with all 16 levels.",
               "Write `_walk(k)` returning, for every level, the last node whose key is < k (the predecessor), plus the number of forward moves. `steps`, `get`, `find_ge` and `find_lt` read it directly.",
               "put splices the new node after the predecessor on levels 0..h-1; remove unlinks the node on EVERY level of its tower, not only level 0."],
        brute_force="A sorted Python list with `bisect` answers get, find_ge and find_lt in O(log n), but insertions and deletions shift the array (O(n)), and it has no levels, so `steps` cannot be reproduced. A single sorted linked list costs O(n) per search.",
        approach="""
`_walk(k)`: `x = head`; for `i` from 15 down to 0: while `x.next[i]` exists and its key is < k, move `x` forward and count a step; record `preds[i] = x`.

- get / find_ge: look at `preds[0].next[0]`.
- find_lt: `preds[0]` itself, unless it is the head.
- put: if `preds[0].next[0]` holds k, replace the value; else create a node of height h and, for i < h, set `node.next[i] = preds[i].next[i]` and `preds[i].next[i] = node`.
- remove: if found, for every level i of the node set `preds[i].next[i] = node.next[i]`.

Dry run of `steps(30)` in the example: level 2 starts at the head and its next key, 50, is not < 30, so no move. Level 1: 10 < 30, move (1); next is 40, stop. Level 0 from 10: 20 < 30, move (2); next is 30, not smaller, stop. Answer 2.
""",
        complexity="With random coin-toss heights a skip list has O(log n) levels and about two forward moves per level, so search, put and remove are expected O(log n). Here the heights come from the tests, so the cost is O(levels + steps); with the geometric heights used in the hidden tests that is again about log n. keys() is O(n). Space O(n) expected (about 2n links).",
        pitfalls="Scanning with `<=` instead of `<` (the walk then overshoots a present key, and steps counts one move too many); unlinking only the bottom level on remove (the tower still sits in the express lanes); creating a second tower when putting an existing key; returning the head sentinel from find_lt.",
        follow_up="Replace the explicit heights with coin tosses and measure the average `steps` for 10,000 random keys. Add `find_range(start, stop)` that walks level 0 from find_ge(start).",
    ),
),
# ---------------------------------------------------------------- memory
dict(
    id="dsaf-gc-reclaim",
    title="Mark-Sweep versus Reference Counting",
    difficulty="Medium",
    pattern="Memory Management and B-Trees",
    entry="collect",
    description=r"""
A toy memory heap holds objects `0 .. n-1`. `refs[i]` lists the objects that object `i` refers to (a
list may name the same object twice, and an object may refer to itself). `roots` lists the objects
that program variables refer to directly (it may contain repeats).

Return `[garbage, stuck]`, both sorted in increasing order:

- `garbage` — the objects that **mark-sweep** reclaims (Goodrich ch. 15.1.2): those that cannot be
  reached from any root by following references.
- `stuck` — the garbage objects that **reference counting alone** never reclaims. An object's count
  starts as the number of references pointing at it: every entry of every `refs` list plus every
  entry of `roots`, repeats included. Any object whose count is `0` is reclaimed, and reclaiming it
  discards its own outgoing references, lowering each target's count by one per reference, which may
  bring further counts to `0`. The garbage objects that this process never reclaims are `stuck`.

`0 <= n <= 6000`, at most 12,000 references in total. Chains of references can be thousands of
objects long, so use explicit stacks or queues rather than recursion.

**Example:** `refs = [[2], [], [3, 3], [2], [5], [4, 6], [7], []]`, `roots = [0]` →
`[[1, 4, 5, 6, 7], [4, 5, 6, 7]]`

Objects 0, 2 and 3 are reachable. Object 1 has no incoming reference, so counting reclaims it at once.
Objects 4 and 5 refer to each other, so neither count ever reaches 0, and together they keep 6 and 7
alive too.

**Example:** `refs = [[0]]`, `roots = []` → `[[0], [0]]`
""",
    starter='''def collect(refs, roots):
    pass
''',
    solution=_GC_SOL,
    tests=[
        [[[2], [], [3, 3], [2], [5], [4, 6], [7], []], [0]],
        [[[0]], []],
        [[], []],
        [[[1], [2], [3], []], []],
        [[[1, 1], []], []],
        [[[1], [0], []], [0, 0, 1]],
        [[[], [0], [1]], [0]],
        [[[1], [0, 2], [3], [2], [0]], []],
        [[[1], [2], [0], [4], [3], [6], []], [2, 2, 2]],
        [[[i + 1] for i in range(5999)] + [[]], [0]],
        [[[1], [0, 2]] + [[i + 1] for i in range(2, 5999)] + [[]], []],
        _rand_heap(4000, 6000, 8, 101),
        _rand_heap(3000, 2600, 20, 102),
    ],
    examples=2,
    wrong_solutions=[
        '''def collect(refs, roots):
    n = len(refs)
    marked = [False] * n
    stack = list(roots)
    while stack:
        v = stack.pop()
        if not marked[v]:
            marked[v] = True
            stack.extend(refs[v])
    garbage = [v for v in range(n) if not marked[v]]
    count = [0] * n
    for v in range(n):
        for w in refs[v]:
            count[w] += 1
    for r in roots:
        count[r] += 1
    return [garbage, [v for v in garbage if count[v] > 0]]
''',
        _mutate(_GC_SOL, "        for w in refs[v]:\n            count[w] -= 1", "        for w in set(refs[v]):\n            count[w] -= 1"),
        '''from collections import deque
def collect(refs, roots):
    n = len(refs)
    marked = [False] * n
    def mark(v):
        if not marked[v]:
            marked[v] = True
            for w in refs[v]:
                mark(w)
    for r in roots:
        mark(r)
    garbage = [v for v in range(n) if not marked[v]]
    count = [0] * n
    for v in range(n):
        for w in refs[v]:
            count[w] += 1
    for r in roots:
        count[r] += 1
    freed = [False] * n
    queue = deque(v for v in range(n) if count[v] == 0)
    while queue:
        v = queue.popleft()
        freed[v] = True
        for w in refs[v]:
            count[w] -= 1
            if count[w] == 0:
                queue.append(w)
    return [garbage, [v for v in garbage if not freed[v]]]
''',
    ],
    guide=dict(
        prereqs="Lesson *Memory allocation, garbage collection and caching*, section 2 (roots and live objects, reference counting, mark-sweep). Depth-first search from the graphs module helps.",
        intuition="Two different questions. Mark-sweep asks 'can a root reach you?', which is graph reachability. Reference counting asks 'does anyone still point at you?' and frees in a chain reaction from objects nobody points at. A cycle of garbage keeps every count in it above zero, and so does anything that cycle points to: that is exactly the set reference counting leaves behind.",
        hints=["Mark phase: an explicit stack seeded with the roots; pop, skip if already marked, mark, push its references.",
               "Counts: add 1 for every entry of every refs list and every entry of roots. Put every object with count 0 into a queue.",
               "Pop an object, record it as reclaimed, and lower the count of each object it refers to, once PER reference; enqueue any count that hits 0. Stuck = garbage that was never reclaimed."],
        brute_force="For each object, run a fresh search from the roots to see whether it is reachable: O(n * (n + m)). For the counting part, rescanning all objects for a zero count after every reclamation is O(n^2).",
        approach="""
1. Mark: iterative DFS from the roots; `garbage` = unmarked objects in increasing order.
2. Count incoming references (with repeats) plus root references.
3. Cascade with a queue, as in the hints.
4. `stuck` = garbage objects not reclaimed.

Dry run of the first example. Marking from 0 reaches 2 and 3, so garbage = [1, 4, 5, 6, 7]. Counts: 0:1 (root), 1:0, 2:2, 3:2, 4:1, 5:1, 6:1, 7:1. Only object 1 starts at 0; reclaiming it changes nothing else (it refers to nobody). The queue empties, so stuck = [4, 5, 6, 7].

Note that a live object can never reach count 0: something live points at it, or it is a root.
""",
        complexity="Each object is marked once and each reference pushed once: O(n + m). Counting and the cascade also touch each reference a constant number of times: O(n + m). Space O(n + m) in the worst case for the stack.",
        pitfalls="Recursive marking (RecursionError on a long chain); counting a reference that appears twice only once, or decrementing it only once; forgetting the root references in the counts; reporting objects on a cycle but not the objects that a garbage cycle keeps alive; returning unsorted lists.",
        follow_up="CPython combines both methods: counting frees most objects at once, and a cycle detector handles the rest. Extend the function to return the order in which the counting cascade reclaims objects, or implement Tarjan's strongly connected components to list the garbage cycles themselves.",
    ),
),
dict(
    id="dsaf-btree-insert",
    title="B-Tree Insertion with Overflow Splits",
    difficulty="Hard",
    pattern="Memory Management and B-Trees",
    entry="btree_insert",
    description=r"""
Build a B-tree of **order `d`** (Goodrich ch. 15.3) by inserting `keys` one at a time into an
initially empty tree, and return the final tree. A node of a B-tree of order `d` holds at most
`d - 1` keys, so at most `d` children. Use the **overflow-then-split** rule of the lesson:

1. Search for the key from the root. If it is already in the tree, ignore it. Otherwise insert it,
   in sorted position, into the leaf where the search ended.
2. If a node now holds `d` keys (an overflow), let `m = d // 2`. The node keeps `keys[:m]` and its
   first `m + 1` children; a new right node takes `keys[m + 1:]` and the remaining children; the
   median `keys[m]` is inserted in sorted position into the parent, with the new right node as the
   child just after it. The parent may then overflow in turn.
3. If the root overflows, a new root holding only the median is created above the two halves.

Return the tree in the format of the problem *B-Tree Search and Page Count*: each node is
`[keys, children]`, with `children == []` for a leaf. An empty tree is `[[], []]`.

`3 <= d <= 64`; up to 5000 integer keys, possibly repeated.

**Example:** `d = 3, keys = [5, 1, 9, 3, 7]` → `[[5], [[[1, 3], []], [[7, 9], []]]]`

**Example:** `d = 4, keys = [8, 2, 6, 4, 10, 12, 1]` → `[[6], [[[1, 2, 4], []], [[8, 10, 12], []]]]`
""",
    starter='''import bisect


def btree_insert(d, keys):
    root = [[], []]          # every node is [keys, children]; children == [] for a leaf
    pass
''',
    solution=_BT_SOL,
    tests=[
        [3, [5, 1, 9, 3, 7]],
        [4, [8, 2, 6, 4, 10, 12, 1]],
        [3, []],
        [5, [42]],
        [4, [7, 7, 3, 7, 3]],
        [3, list(range(1, 21))],
        [5, list(range(60, 0, -1))],
        [4, [50, 10, 90, 30, 70, 20, 80, 40, 60, 25, 35, 45, 55, 65]],
        [4, _rand_keys(300, 10 ** 4, 111)],
        [6, _rand_keys(1000, 10 ** 5, 112)],
        [7, _rand_keys(3000, 10 ** 6, 113)],
        [64, _rand_keys(5000, 10 ** 6, 114)],
        [3, _rand_keys(1000, 400, 115)],
    ],
    examples=2,
    wrong_solutions=[
        _mutate(_BT_SOL, "        m = d // 2 ", "        m = (d - 1) // 2 "),
        _mutate(_BT_SOL, "        right = [ks[m + 1:], ch[m + 1:]]", "        right = [ks[m + 1:], ch[m:]]"),
        _mutate(_BT_SOL, "        if i < len(ks) and ks[i] == k:\n            return None ", "        if False:\n            return None "),
    ],
    guide=dict(
        prereqs="Lesson *External searching: (a,b) trees and B-trees* (section 2.2: overflow and split; section 3: B-trees of order d; section 3.3: a dry run). The (2,4)-tree lesson of the search-trees module shows the same splits with d = 4.",
        intuition="A B-tree never grows downward. New keys always land in a leaf; when a node gets one key too many it splits in two and pushes its middle key up to the parent, like a full shelf that is divided while its middle book goes up a level. Only when the root itself splits does the tree become one level taller, so every leaf stays at the same depth.",
        hints=["Write a recursive `insert(node, k)` that returns `None` when nothing overflowed, or `(median, right_node)` when `node` had to split. The recursion depth is only the height of the tree.",
               "In an internal node, find the child index with `bisect_left`, recurse, and if the child split, insert the median at that index and the right node just after it, then check this node for overflow.",
               "Split with `m = d // 2`: left keeps `keys[:m]` and `children[:m+1]`, right gets `keys[m+1:]` and `children[m+1:]`; leaves have no children, and slicing an empty list keeps them empty."],
        brute_force="Collect all keys, sort them and pack them into leaves directly: you get A B-tree, but not the one this insertion order produces, so the structure would not match. Re-inserting everything after each key is O(n^2 log n) and still has to implement splits.",
        approach="""
For each key: `res = insert(root, k)`; if the root split, `root = [[median], [root, right]]`.

`insert(node, k)`: `i = bisect_left(keys, k)`; duplicate → `None`. Leaf → insert k at i. Internal → recurse into `children[i]` and absorb a returned split at position i. Then, if `len(keys) == d`, split around `keys[d // 2]` and return the pieces.

Dry run of the second example (d = 4, at most 3 keys per node): 8 → `[8]`; 2 → `[2 8]`; 6 → `[2 6 8]`; 4 → `[2 4 6 8]` overflows, m = 2, so 6 goes up into a new root: `[6]` over `[2 4]` and `[8]`. 10 and 12 join the right leaf `[8 10 12]`; 1 joins the left leaf `[1 2 4]`. Nothing else overflows.
""",
        complexity="Each insertion walks one root-to-leaf path of height O(log_d n) and may split one node per level; inserting into or splitting a node costs O(d). Total O(n d log_d n) time for n keys, O(n) space. Counting disk transfers, each insertion reads and writes O(log_d n) nodes.",
        pitfalls="Choosing the median as `keys[(d - 1) // 2]` (different for even d); giving the right node `children[m:]`, which duplicates a child; splitting at d - 1 keys instead of d (that is the top-down preemptive variant, which builds different trees); inserting duplicates; forgetting that a split of the root must create a new root.",
        follow_up="Implement deletion with transfer and fusion. Insert the same keys with the top-down preemptive-split method from the lesson's code (minimum degree t, order 2t) and compare the trees: when do they differ?",
    ),
),
]
