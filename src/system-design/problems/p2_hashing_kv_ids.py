"""System design problems 2: consistent hashing, quorums, vector clocks, Merkle trees, IDs and URL shortening."""


def _ops(cls, ctor_args, calls):
    return [[cls] + [c[0] for c in calls], [list(ctor_args)] + [list(c[1]) for c in calls]]


_KEYS = [f"user:{i}" for i in range(60)]

PROBLEMS = [
dict(
    id="sd-consistent-hash-ring",
    title="Consistent Hash Ring with Virtual Nodes",
    difficulty="Hard",
    pattern="Consistent Hashing",
    kind="class",
    entry="HashRing",
    description=r"""
Build a consistent hash ring with virtual nodes.

Use this hash everywhere (it is in the starter code): `h(s) = int(hashlib.md5(s.encode()).hexdigest(), 16) % 2**32`.

`HashRing(vnodes)`: each physical node `name` is placed on the ring at the `vnodes` positions `h(name + "#" + str(i))` for `i = 0 .. vnodes-1`. A key belongs to the node owning the first position **greater than or equal to** `h(key)`; if there is none, wrap around to the smallest position. (Assume no two virtual nodes share a position.)

- `add_node(name)` → `None`. Adding a node that is already present does nothing.
- `remove_node(name)` → `None`. Removing an absent node does nothing.
- `get_node(key)` → the owning node's name, or `None` if the ring is empty.
- `moved_if_added(name, keys)` → how many of the given keys would change owner if `name` were added. The ring is left unchanged. (If the ring is empty, every key moves from `None` to `name`.)
- `moved_if_removed(name, keys)` → how many of the given keys would change owner if `name` were removed. The ring is left unchanged.

**Example:** with `HashRing(3)` after `add_node("A")`, `get_node(k)` is `"A"` for every key; `moved_if_removed("A", ["x","y"])` → 2.
""",
    starter='''import bisect, hashlib

def h(s: str) -> int:
    return int(hashlib.md5(s.encode()).hexdigest(), 16) % 2**32

class HashRing:
    def __init__(self, vnodes: int):
        pass

    def add_node(self, name: str) -> None:
        pass

    def remove_node(self, name: str) -> None:
        pass

    def get_node(self, key: str):
        pass

    def moved_if_added(self, name: str, keys: List[str]) -> int:
        pass

    def moved_if_removed(self, name: str, keys: List[str]) -> int:
        pass
''',
    solution='''import bisect, hashlib

def h(s):
    return int(hashlib.md5(s.encode()).hexdigest(), 16) % 2**32

class HashRing:
    def __init__(self, vnodes):
        self.vnodes = vnodes
        self.nodes = set()
        self.positions = []
        self.owner = {}

    def _points(self, name):
        return [h(name + "#" + str(i)) for i in range(self.vnodes)]

    def add_node(self, name):
        if name in self.nodes:
            return
        self.nodes.add(name)
        for p in self._points(name):
            bisect.insort(self.positions, p)
            self.owner[p] = name

    def remove_node(self, name):
        if name not in self.nodes:
            return
        self.nodes.discard(name)
        for p in self._points(name):
            self.positions.pop(bisect.bisect_left(self.positions, p))
            del self.owner[p]

    def get_node(self, key):
        if not self.positions:
            return None
        i = bisect.bisect_left(self.positions, h(key))
        if i == len(self.positions):
            i = 0
        return self.owner[self.positions[i]]

    def moved_if_added(self, name, keys):
        if name in self.nodes:
            return 0
        before = [self.get_node(k) for k in keys]
        self.add_node(name)
        after = [self.get_node(k) for k in keys]
        self.remove_node(name)
        return sum(1 for a, b in zip(before, after) if a != b)

    def moved_if_removed(self, name, keys):
        if name not in self.nodes:
            return 0
        before = [self.get_node(k) for k in keys]
        self.remove_node(name)
        after = [self.get_node(k) for k in keys]
        self.add_node(name)
        return sum(1 for a, b in zip(before, after) if a != b)
''',
    tests=[
        _ops("HashRing", [3], [("get_node", ["x"]), ("add_node", ["A"]), ("get_node", ["x"]), ("get_node", ["y"]), ("moved_if_removed", ["A", ["x", "y"]]), ("get_node", ["x"])]),
        _ops("HashRing", [1], [("add_node", [n]) for n in ("A", "B", "C")] + [("get_node", [k]) for k in _KEYS[:12]]),
        _ops("HashRing", [50], [("add_node", [n]) for n in ("n1", "n2", "n3", "n4")] + [("get_node", [k]) for k in _KEYS[:20]]),
        _ops("HashRing", [20], [("add_node", [n]) for n in ("n1", "n2", "n3")] + [("moved_if_added", ["n4", _KEYS]), ("get_node", [_KEYS[0]]), ("add_node", ["n4"]), ("moved_if_added", ["n4", _KEYS]), ("moved_if_removed", ["n2", _KEYS]), ("get_node", [_KEYS[1]])]),
        _ops("HashRing", [10], [("moved_if_added", ["solo", _KEYS[:5]]), ("moved_if_removed", ["solo", _KEYS[:5]]), ("add_node", ["solo"]), ("moved_if_removed", ["solo", _KEYS[:5]]), ("moved_if_added", ["second", _KEYS])]),
        _ops("HashRing", [8], [("add_node", ["a"]), ("add_node", ["a"]), ("add_node", ["b"]), ("remove_node", ["zzz"]), ("remove_node", ["a"])] + [("get_node", [k]) for k in _KEYS[:6]] + [("remove_node", ["b"]), ("get_node", ["k"])]),
        _ops("HashRing", [100], [("add_node", [f"cache-{i}"]) for i in range(8)] + [("moved_if_removed", [f"cache-{i}", _KEYS]) for i in range(8)]),
        _ops("HashRing", [100], [("add_node", [f"cache-{i}"]) for i in range(5)] + [("get_node", [k]) for k in _KEYS] ),
        _ops("HashRing", [2], [("add_node", ["x"]), ("add_node", ["y"]), ("remove_node", ["x"]), ("add_node", ["x"])] + [("get_node", [k]) for k in _KEYS[:15]]),
        _ops("HashRing", [30], [("add_node", ["a"]), ("add_node", ["b"]), ("moved_if_added", ["c", _KEYS]), ("add_node", ["c"]), ("moved_if_removed", ["c", _KEYS]), ("remove_node", ["c"]), ("moved_if_added", ["c", _KEYS])]),
        _ops("HashRing", [1], [("add_node", ["only"]), ("moved_if_added", ["other", _KEYS]), ("add_node", ["other"]), ("moved_if_removed", ["only", _KEYS]), ("moved_if_removed", ["other", _KEYS])]),
    ],
    examples=1,
    wrong_solutions=[
        '''import bisect, hashlib
def h(s):
    return int(hashlib.md5(s.encode()).hexdigest(), 16) % 2**32
class HashRing:
    def __init__(self, vnodes):
        self.nodes = []
    def add_node(self, name):
        if name not in self.nodes:
            self.nodes.append(name)
    def remove_node(self, name):
        if name in self.nodes:
            self.nodes.remove(name)
    def get_node(self, key):
        return self.nodes[h(key) % len(self.nodes)] if self.nodes else None
    def moved_if_added(self, name, keys):
        if name in self.nodes:
            return 0
        b = [self.get_node(k) for k in keys]; self.nodes.append(name)
        a = [self.get_node(k) for k in keys]; self.nodes.pop()
        return sum(x != y for x, y in zip(a, b))
    def moved_if_removed(self, name, keys):
        if name not in self.nodes:
            return 0
        i = self.nodes.index(name)
        b = [self.get_node(k) for k in keys]; self.nodes.pop(i)
        a = [self.get_node(k) for k in keys]; self.nodes.insert(i, name)
        return sum(x != y for x, y in zip(a, b))
''',
        '''import bisect, hashlib
def h(s):
    return int(hashlib.md5(s.encode()).hexdigest(), 16) % 2**32
class HashRing:
    def __init__(self, vnodes):
        self.vnodes, self.nodes, self.positions, self.owner = vnodes, set(), [], {}
    def add_node(self, name):
        if name in self.nodes:
            return
        self.nodes.add(name)
        for i in range(self.vnodes):
            p = h(name + "#" + str(i)); bisect.insort(self.positions, p); self.owner[p] = name
    def remove_node(self, name):
        if name not in self.nodes:
            return
        self.nodes.discard(name)
        for i in range(self.vnodes):
            p = h(name + "#" + str(i)); self.positions.remove(p); del self.owner[p]
    def get_node(self, key):
        if not self.positions:
            return None
        i = bisect.bisect_left(self.positions, h(key))
        if i == len(self.positions):
            i = len(self.positions) - 1
        return self.owner[self.positions[i]]
    def moved_if_added(self, name, keys):
        if name in self.nodes:
            return 0
        b = [self.get_node(k) for k in keys]; self.add_node(name)
        a = [self.get_node(k) for k in keys]; self.remove_node(name)
        return sum(x != y for x, y in zip(a, b))
    def moved_if_removed(self, name, keys):
        if name not in self.nodes:
            return 0
        b = [self.get_node(k) for k in keys]; self.remove_node(name)
        a = [self.get_node(k) for k in keys]; self.add_node(name)
        return sum(x != y for x, y in zip(a, b))
''',
        '''import bisect, hashlib
def h(s):
    return int(hashlib.md5(s.encode()).hexdigest(), 16) % 2**32
class HashRing:
    def __init__(self, vnodes):
        self.vnodes, self.nodes, self.positions, self.owner = vnodes, set(), [], {}
    def add_node(self, name):
        if name in self.nodes:
            return
        self.nodes.add(name)
        p = h(name); bisect.insort(self.positions, p); self.owner[p] = name
    def remove_node(self, name):
        if name not in self.nodes:
            return
        self.nodes.discard(name)
        p = h(name); self.positions.remove(p); del self.owner[p]
    def get_node(self, key):
        if not self.positions:
            return None
        i = bisect.bisect_left(self.positions, h(key)) % len(self.positions)
        return self.owner[self.positions[i]]
    def moved_if_added(self, name, keys):
        if name in self.nodes:
            return 0
        b = [self.get_node(k) for k in keys]; self.add_node(name)
        a = [self.get_node(k) for k in keys]; self.remove_node(name)
        return sum(x != y for x, y in zip(a, b))
    def moved_if_removed(self, name, keys):
        if name not in self.nodes:
            return 0
        b = [self.get_node(k) for k in keys]; self.remove_node(name)
        a = [self.get_node(k) for k in keys]; self.add_node(name)
        return sum(x != y for x, y in zip(a, b))
''',
    ],
    guide=dict(
        prereqs="Both consistent hashing lessons: the ring, the clockwise rule, virtual nodes. Python's `bisect` module.",
        intuition="Keep every virtual node's position in one sorted list. Finding a key's owner is 'first position at or after the key's hash', a binary search, with a wrap to index 0 when you run off the end.",
        hints=[
            "Store `positions` (sorted list of ints) and `owner` (dict from position to node name).",
            "`i = bisect.bisect_left(positions, h(key))`; if `i == len(positions)`, use `i = 0`.",
            "For the 'moved if' methods, record the owners, apply the change, record again, undo the change, and count the differences.",
        ],
        brute_force="For each lookup, scan all positions for the smallest one that is >= the key's hash: O(n*v) per lookup. Sorting once and using binary search makes it O(log(n*v)).",
        approach="""1. `add_node`: compute the `vnodes` positions, insert each into the sorted list (`bisect.insort`), record the owner.
2. `remove_node`: locate each of its positions by binary search and delete it.
3. `get_node`: binary search with wrap-around.
4. `moved_if_added` / `moved_if_removed`: owners before, apply, owners after, undo, count mismatches. Guard the no-op cases (node already present, or absent).

**Dry run** with positions `[100 (A), 400 (B), 900 (A)]`: a key hashing to 250 → `bisect_left` gives index 1 → B. A key hashing to 950 → index 3, equal to the length → wrap to index 0 → A. A key hashing to exactly 400 → index 1 → B.""",
        complexity="Lookup O(log(n*v)). Add or remove O(v * n*v) with list insertion (fine here; a balanced tree would give O(v log(n*v))). Space O(n*v).",
        pitfalls="Forgetting to wrap around; using `bisect_right`, which sends a key sitting exactly on a position to the next node; placing a node once instead of `vnodes` times; leaving the ring modified after a 'moved if' query; using `hash()`, which differs between runs.",
        follow_up="Add `get_nodes(key, n)` returning the first n distinct physical nodes clockwise (a preference list). Add weights by giving a node `weight * vnodes` positions.",
    ),
),
dict(
    id="sd-rendezvous-hashing",
    title="Rendezvous (Highest Random Weight) Hashing",
    difficulty="Medium",
    pattern="Consistent Hashing",
    kind="function",
    entry="top_nodes",
    description=r"""
Rendezvous hashing picks a node for a key without any ring: score every node for the key and take the best.

Define the score of a node for a key as
`score = int(hashlib.md5((key + "|" + node).encode()).hexdigest(), 16)`.

Write `top_nodes(key, nodes, k)` returning the names of the `k` nodes with the **highest** scores, best first. If two nodes have the same score, the one with the smaller name comes first. If `k` is larger than the number of nodes, return all of them in that order. `nodes` contains distinct names and may be empty.

The first element is the key's owner; the next ones are natural places for its replicas.

**Example:** `top_nodes("user:1", ["a", "b", "c"], 1)` returns a one-element list with whichever of the three has the highest score for `"user:1"`; removing a *different* node from the list never changes that answer.
""",
    starter='''import hashlib

def top_nodes(key: str, nodes: List[str], k: int) -> List[str]:
    pass
''',
    solution='''import hashlib

def top_nodes(key, nodes, k):
    def score(node):
        return int(hashlib.md5((key + "|" + node).encode()).hexdigest(), 16)
    ranked = sorted(nodes, key=lambda n: (-score(n), n))
    return ranked[:max(0, k)]
''',
    tests=[
        ["user:1", ["a", "b", "c"], 1],
        ["user:1", ["a", "b", "c"], 3],
        ["user:1", [], 2],
        ["user:2", ["only"], 5],
        ["cart:99", [f"node-{i}" for i in range(8)], 3],
        ["cart:99", [f"node-{i}" for i in range(8) if i != 3], 3],
        ["cart:100", [f"node-{i}" for i in range(8)], 8],
        ["k", ["x", "y"], 0],
        ["", ["x", "y", "z"], 2],
        ["session:abc", [f"cache{i}" for i in range(50)], 5],
        ["session:abd", [f"cache{i}" for i in range(50)], 5],
        ["user:7", ["c", "b", "a"], 2],
        ["user:7", ["a", "b", "c"], 2],
    ],
    examples=2,
    wrong_solutions=[
        '''import hashlib
def top_nodes(key, nodes, k):
    s = lambda n: int(hashlib.md5((key + "|" + n).encode()).hexdigest(), 16)
    return sorted(nodes, key=s)[:k]
''',
        '''import hashlib
def top_nodes(key, nodes, k):
    if not nodes:
        return []
    i = int(hashlib.md5(key.encode()).hexdigest(), 16) % len(nodes)
    return (nodes[i:] + nodes[:i])[:k]
''',
        '''import hashlib
def top_nodes(key, nodes, k):
    s = lambda n: int(hashlib.md5((n + "|" + key).encode()).hexdigest(), 16)
    return sorted(nodes, key=lambda n: (-s(n), n))[:k]
''',
    ],
    guide=dict(
        prereqs="Lesson 'Design consistent hashing II', the section on rendezvous hashing. Sorting with a key function.",
        intuition="Every key holds a private, repeatable 'lottery' among the nodes. The winner owns the key. Removing a losing node cannot change the winner, so only the removed node's keys move.",
        hints=[
            "Write a helper that computes the score of one node for the given key, exactly as defined.",
            "Sort the nodes by descending score. A sort key of `(-score, name)` also handles ties.",
            "Slice the first k elements; slicing already copes with k larger than the list.",
        ],
        brute_force="Scoring every node is the algorithm: O(n) hashes per key. There is no cheaper exact method without extra structure, which is why rendezvous hashing suits small and medium clusters.",
        approach="""1. `score(node) = md5(key + "|" + node)` as an integer.
2. `ranked = sorted(nodes, key=lambda n: (-score(n), n))`.
3. Return `ranked[:k]`.

**Dry run** with made-up scores `a: 40, b: 90, c: 70` and `k = 2`: sorted by descending score gives `b, c, a`; the answer is `["b", "c"]`. Remove `a` and the answer is unchanged; remove `b` and the key moves to `c`, its previous runner-up.""",
        complexity="Time O(n log n) per call for the sort (O(n) hashes); O(n log k) with a heap. Space O(n).",
        pitfalls="Sorting ascending; concatenating in the wrong order (`node|key`), which gives different scores from the specification; depending on the input order of `nodes`; using `hash()` instead of a stable hash.",
        follow_up="Weighted rendezvous hashing: score = -weight / ln(hash scaled into (0,1)). Compare the per-lookup cost with a ring for 10 and for 10,000 nodes.",
    ),
),
dict(
    id="sd-quorum-decision",
    title="Quorum Settings: What Do N, W and R Guarantee?",
    difficulty="Easy",
    pattern="Replication",
    kind="function",
    entry="quorum",
    description=r"""
A Dynamo-style store keeps each key on `n` replicas, waits for `w` acknowledgements on a write and for `r` responses on a read.

Write `quorum(n, w, r)`. If the setting is invalid (`n < 1`, or `w` or `r` outside `1..n`), return the string `"invalid"`. Otherwise return a list of four values:

1. `strong_read` (bool): every read quorum overlaps every write quorum, i.e. `w + r > n`.
2. `no_split_writes` (bool): two writes cannot both reach a write quorum without sharing a replica, i.e. `2 * w > n`.
3. `write_tolerance` (int): how many replicas may be down while writes still succeed, `n - w`.
4. `read_tolerance` (int): how many replicas may be down while reads still succeed, `n - r`.

**Example:** `quorum(3, 2, 2)` → `[True, True, 1, 1]`

**Example:** `quorum(3, 1, 1)` → `[False, False, 2, 2]`
""",
    starter='''def quorum(n: int, w: int, r: int):
    pass
''',
    solution='''def quorum(n, w, r):
    if n < 1 or not (1 <= w <= n) or not (1 <= r <= n):
        return "invalid"
    return [w + r > n, 2 * w > n, n - w, n - r]
''',
    tests=[
        [3, 2, 2], [3, 1, 1], [3, 3, 1], [3, 1, 3], [5, 3, 3], [5, 2, 3], [5, 3, 2], [1, 1, 1],
        [3, 0, 2], [3, 4, 1], [0, 0, 0], [4, 2, 3], [4, 2, 2], [7, 4, 4], [2, 1, 2], [3, 2, 4],
    ],
    examples=2,
    wrong_solutions=[
        '''def quorum(n, w, r):
    if n < 1 or not (1 <= w <= n) or not (1 <= r <= n):
        return "invalid"
    return [w + r >= n, 2 * w > n, n - w, n - r]
''',
        '''def quorum(n, w, r):
    if n < 1 or not (1 <= w <= n) or not (1 <= r <= n):
        return "invalid"
    return [w + r > n, 2 * w >= n, n - w, n - r]
''',
        '''def quorum(n, w, r):
    if n < 1 or w < 1 or r < 1:
        return "invalid"
    return [w + r > n, 2 * w > n, n - w, n - r]
''',
    ],
    guide=dict(
        prereqs="Lesson 'Design a key-value store I', the section on quorum consensus.",
        intuition="Two groups chosen from n replicas must share a member when their sizes add up to more than n (the pigeonhole principle). Apply that once to a write group and a read group, and once to two write groups.",
        hints=[
            "Validate first: w and r must each be between 1 and n.",
            "Read/write overlap needs strictly more than n in total: `w + r > n`.",
            "Tolerance is how many replicas you can lose and still gather the required number: `n - w` and `n - r`.",
        ],
        brute_force="Enumerate all subsets of size w and r and test whether every pair intersects: exponential, and unnecessary once you see the counting argument.",
        approach="""1. Reject invalid input.
2. `strong_read = w + r > n`.
3. `no_split_writes = 2 * w > n`.
4. Tolerances `n - w` and `n - r`.

**Dry run** `quorum(5, 2, 3)`: 2 + 3 = 5 is not greater than 5 → reads may be stale (False); 2 x 2 = 4 is not greater than 5 → two writes can succeed on disjoint replicas (False); writes survive 3 failures, reads survive 2.""",
        complexity="O(1) time and space.",
        pitfalls="Using `>=` instead of `>` (with n = 4, w = 2, r = 2 the groups can be disjoint); forgetting the upper bound in validation (w = 4 with n = 3 is impossible).",
        follow_up="Which of these guarantees does a sloppy quorum weaken, and why?",
    ),
),
dict(
    id="sd-vector-clock-compare",
    title="Vector Clocks: Detect Conflicts and Merge",
    difficulty="Medium",
    pattern="Replication",
    kind="function",
    entry="reconcile",
    description=r"""
Each stored version of a value carries a vector clock: a dictionary from node name to a counter. A node that is missing from the dictionary has counter 0.

Clock `a` **dominates** `b` when `a[n] >= b[n]` for every node `n`.

Write `reconcile(versions)` where `versions` is a list of `[value, clock]` pairs. Return a list `[survivors, merged_clock]`:

- `survivors`: the **values** of the versions that are not obsolete, in their original order. A version is obsolete if some *other* version's clock dominates its clock and is not equal to it. If several versions have equal clocks, keep only the first of them.
- `merged_clock`: the clock a client should send when it writes a value that merges all survivors: for every node, the maximum counter over all given versions. Omit nodes whose maximum is 0.

If exactly one value survives there was no conflict; more than one means the versions are concurrent siblings.

**Example:** `reconcile([["A", {"x": 1}], ["B", {"x": 2}]])` → `[["B"], {"x": 2}]`

**Example:** `reconcile([["A", {"x": 2, "y": 1}], ["B", {"x": 2, "z": 1}]])` → `[["A", "B"], {"x": 2, "y": 1, "z": 1}]`
""",
    starter='''def reconcile(versions):
    pass
''',
    solution='''def reconcile(versions):
    def dominates(a, b):
        return all(a.get(n, 0) >= b.get(n, 0) for n in set(a) | set(b))

    def norm(c):
        return {n: v for n, v in c.items() if v > 0}

    survivors = []
    for i, (value, clock) in enumerate(versions):
        obsolete = False
        for j, (_, other) in enumerate(versions):
            if i == j:
                continue
            if dominates(other, clock):
                if not dominates(clock, other):
                    obsolete = True          # strictly older
                elif j < i:
                    obsolete = True          # equal clocks: keep only the first
            if obsolete:
                break
        if not obsolete:
            survivors.append(value)
    merged = {}
    for _, clock in versions:
        for n, v in norm(clock).items():
            merged[n] = max(merged.get(n, 0), v)
    return [survivors, merged]
''',
    tests=[
        [[["A", {"x": 1}], ["B", {"x": 2}]]],
        [[["A", {"x": 2, "y": 1}], ["B", {"x": 2, "z": 1}]]],
        [[]],
        [[["only", {"n1": 3}]]],
        [[["A", {"x": 1}], ["B", {"x": 1}]]],
        [[["A", {"x": 1}], ["B", {"y": 1}], ["C", {"x": 1, "y": 1}]]],
        [[["A", {"x": 3, "y": 1}], ["B", {"x": 2, "y": 2}], ["C", {"x": 1, "y": 1}]]],
        [[["A", {}], ["B", {"x": 1}]]],
        [[["A", {"x": 1, "y": 0}], ["B", {"x": 1}]]],
        [[["A", {"x": 1}], ["B", {"y": 1}], ["C", {"z": 1}]]],
        [[["v5", {"x": 3, "y": 1, "z": 1}], ["v3", {"x": 2, "y": 1}], ["v4", {"x": 2, "z": 1}]]],
        [[["A", {"a": 5}], ["B", {"a": 5, "b": 0}], ["C", {"a": 4, "b": 9}]]],
        [[["A", {"x": 2}], ["B", {"x": 1, "y": 1}], ["C", {"x": 2, "y": 1}], ["D", {"x": 2, "y": 1}]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def reconcile(versions):
    best = None
    for value, clock in versions:
        if best is None or sum(clock.values()) > sum(best[1].values()):
            best = (value, clock)
    merged = {}
    for _, c in versions:
        for n, v in c.items():
            if v > 0:
                merged[n] = max(merged.get(n, 0), v)
    return [[best[0]] if best else [], merged]
''',
        '''def reconcile(versions):
    def dom(a, b):
        return all(a.get(n, 0) >= b.get(n, 0) for n in a)
    out = []
    for i, (v, c) in enumerate(versions):
        if not any(i != j and dom(o, c) and (not dom(c, o) or j < i) for j, (_, o) in enumerate(versions)):
            out.append(v)
    merged = {}
    for _, c in versions:
        for n, x in c.items():
            if x > 0:
                merged[n] = max(merged.get(n, 0), x)
    return [out, merged]
''',
        '''def reconcile(versions):
    def dom(a, b):
        return all(a.get(n, 0) >= b.get(n, 0) for n in set(a) | set(b))
    out = []
    for i, (v, c) in enumerate(versions):
        if not any(i != j and dom(o, c) and not dom(c, o) for j, (_, o) in enumerate(versions)):
            out.append(v)
    merged = {}
    for _, c in versions:
        for n, x in c.items():
            if x > 0:
                merged[n] = max(merged.get(n, 0), x)
    return [out, merged]
''',
        '''def reconcile(versions):
    def dom(a, b):
        return all(a.get(n, 0) >= b.get(n, 0) for n in set(a) | set(b))
    out = []
    for i, (v, c) in enumerate(versions):
        if not any(i != j and dom(o, c) and (not dom(c, o) or j < i) for j, (_, o) in enumerate(versions)):
            out.append(v)
    merged = {}
    for _, c in versions:
        for n, x in c.items():
            merged[n] = merged.get(n, 0) + x
    return [out, {n: x for n, x in merged.items() if x > 0}]
''',
    ],
    guide=dict(
        prereqs="Lesson 'Design a key-value store II', the section on vector clocks: descends-from versus concurrent.",
        intuition="A version can be thrown away only if another version has seen everything it has seen, and more. If each of two versions has seen something the other has not, neither may be discarded: they are siblings.",
        hints=[
            "Write `dominates(a, b)`: for every node in either clock, `a.get(n, 0) >= b.get(n, 0)`.",
            "Version i is obsolete if some other version j dominates it and either i does not dominate j (strictly older) or the clocks are equal and j comes first.",
            "The merged clock is the per-node maximum. Treat counters of 0 as absent.",
        ],
        brute_force="Comparing every pair of versions is already the natural solution: O(v^2 * nodes). Version lists are tiny (usually 1 to 3 siblings), so nothing faster is needed.",
        approach="""1. For each version, compare it against all others with `dominates`.
2. Keep it unless it is strictly dominated, or it ties with an earlier version.
3. Merge clocks by taking maxima.

**Dry run** for `v5 {x:3,y:1,z:1}`, `v3 {x:2,y:1}`, `v4 {x:2,z:1}`: v5 dominates v3 and v4 and neither dominates v5, so v3 and v4 are obsolete; survivors `["v5"]`, merged clock `{x:3,y:1,z:1}`. Without v5, v3 and v4 each have a node the other lacks, so both survive as siblings.""",
        complexity="Time O(v^2 * k) for v versions and k nodes; space O(k).",
        pitfalls="Comparing only the nodes present in one clock (a missing node means 0, and the *other* clock may have it); picking a winner by the sum of counters or by a timestamp; dropping both of two equal versions, or keeping both; treating `{x:1, y:0}` as different from `{x:1}`.",
        follow_up="After merging, the coordinating node increments its own counter in the merged clock before storing. Implement that `put` step.",
    ),
),
dict(
    id="sd-merkle-diff",
    title="Merkle Tree Difference Between Two Replicas",
    difficulty="Medium",
    pattern="Replication",
    kind="function",
    entry="merkle_diff",
    description=r"""
Two replicas each hold a dictionary of string keys to string values. Find which **buckets** differ, comparing as few hashes as possible.

Definitions (use `hashlib.md5`):

- `H(text)` = `hashlib.md5(text.encode()).hexdigest()`.
- A key lives in bucket `int(H(key), 16) % buckets`. `buckets` is a power of two (1, 2, 4, 8, ...).
- The **leaf hash** of a bucket is `H` of the concatenation of `key + "=" + value + ";"` over the bucket's keys in ascending key order (so an empty bucket hashes the empty string).
- A **parent hash** is `H(left_child_hash + right_child_hash)`. Pair leaves 0-1, 2-3, ... and repeat upward until one root remains.

Compare the two trees top-down: compare the roots (1 comparison). If two hashes are equal, stop exploring that subtree. If they differ and the node is not a leaf, compare both pairs of children (1 comparison each) and continue.

Write `merkle_diff(a, b, buckets)` returning `[differing, comparisons]`: the ascending list of bucket numbers whose leaf hashes differ, and the total number of hash comparisons made.

**Example:** identical dictionaries with 8 buckets → `[[], 1]` (only the roots are compared).
""",
    starter='''import hashlib

def merkle_diff(a: dict, b: dict, buckets: int):
    pass
''',
    solution='''import hashlib

def merkle_diff(a, b, buckets):
    def H(text):
        return hashlib.md5(text.encode()).hexdigest()

    def build(d):
        groups = [[] for _ in range(buckets)]
        for k in d:
            groups[int(H(k), 16) % buckets].append(k)
        level = [H("".join(k + "=" + d[k] + ";" for k in sorted(g))) for g in groups]
        levels = [level]
        while len(level) > 1:
            level = [H(level[i] + level[i + 1]) for i in range(0, len(level), 2)]
            levels.append(level)
        return levels

    ta, tb = build(a), build(b)
    comparisons, differing = 0, []
    stack = [(len(ta) - 1, 0)]
    while stack:
        depth, i = stack.pop()
        comparisons += 1
        if ta[depth][i] != tb[depth][i]:
            if depth == 0:
                differing.append(i)
            else:
                stack.append((depth - 1, 2 * i))
                stack.append((depth - 1, 2 * i + 1))
    return [sorted(differing), comparisons]
''',
    tests=[
        [{f"k{i}": "v" for i in range(40)}, {f"k{i}": "v" for i in range(40)}, 8],
        [{f"k{i}": "v" for i in range(40)}, {**{f"k{i}": "v" for i in range(40)}, "k7": "changed"}, 8],
        [{}, {}, 1],
        [{"a": "1"}, {"a": "2"}, 1],
        [{"a": "1"}, {}, 4],
        [{f"k{i}": "v" for i in range(100)}, {f"k{i}": ("w" if i % 10 == 0 else "v") for i in range(100)}, 16],
        [{f"k{i}": "v" for i in range(100)}, {f"k{i}": "w" for i in range(100)}, 16],
        [{f"k{i}": str(i) for i in range(30)}, {f"k{i}": str(i) for i in range(31)}, 4],
        [{"x": "1", "y": "2"}, {"y": "2", "x": "1"}, 2],
        [{f"user:{i}": "a" for i in range(200)}, {**{f"user:{i}": "a" for i in range(200)}, "user:5": "b", "user:150": "b"}, 32],
        [{f"user:{i}": "a" for i in range(64)}, {f"user:{i}": "a" for i in range(64) if i != 20}, 64],
        [{"ab": "c"}, {"a": "bc"}, 2],
        [{f"k{i}": "v" for i in range(10)}, {f"k{i}": "v" for i in reversed(range(10))}, 1],
        [{f"k{i}": "v" for i in range(30)}, {f"k{i}": "v" for i in reversed(range(30))}, 4],
    ],
    examples=2,
    wrong_solutions=[
        '''import hashlib
def merkle_diff(a, b, buckets):
    H = lambda t: hashlib.md5(t.encode()).hexdigest()
    def leaves(d):
        g = [[] for _ in range(buckets)]
        for k in d:
            g[int(H(k), 16) % buckets].append(k)
        return [H("".join(k + "=" + d[k] + ";" for k in sorted(x))) for x in g]
    la, lb = leaves(a), leaves(b)
    return [[i for i in range(buckets) if la[i] != lb[i]], buckets]
''',
        '''import hashlib
def merkle_diff(a, b, buckets):
    H = lambda t: hashlib.md5(t.encode()).hexdigest()
    def build(d):
        g = [[] for _ in range(buckets)]
        for k in d:
            g[int(H(k), 16) % buckets].append(k)
        level = [H("".join(k + "=" + d[k] + ";" for k in x)) for x in g]
        levels = [level]
        while len(level) > 1:
            level = [H(level[i] + level[i + 1]) for i in range(0, len(level), 2)]
            levels.append(level)
        return levels
    ta, tb = build(a), build(b)
    c, diff, stack = 0, [], [(len(ta) - 1, 0)]
    while stack:
        dep, i = stack.pop()
        c += 1
        if ta[dep][i] != tb[dep][i]:
            if dep == 0:
                diff.append(i)
            else:
                stack += [(dep - 1, 2 * i), (dep - 1, 2 * i + 1)]
    return [sorted(diff), c]
''',
        '''import hashlib
def merkle_diff(a, b, buckets):
    H = lambda t: hashlib.md5(t.encode()).hexdigest()
    def build(d):
        g = [[] for _ in range(buckets)]
        for k in d:
            g[int(H(k), 16) % buckets].append(k)
        level = [H("".join(k + "=" + d[k] + ";" for k in sorted(x))) for x in g]
        levels = [level]
        while len(level) > 1:
            level = [H(level[i] + level[i + 1]) for i in range(0, len(level), 2)]
            levels.append(level)
        return levels
    ta, tb = build(a), build(b)
    c, diff, stack = 0, [], [(len(ta) - 1, 0)]
    while stack:
        dep, i = stack.pop()
        if ta[dep][i] != tb[dep][i]:
            c += 1
            if dep == 0:
                diff.append(i)
            else:
                stack += [(dep - 1, 2 * i), (dep - 1, 2 * i + 1)]
    return [sorted(diff), c]
''',
    ],
    guide=dict(
        prereqs="Lesson 'Design a key-value store II', the section on Merkle trees. Lists of lists; a stack or recursion.",
        intuition="A parent hash summarises everything beneath it. If two parents match, everything beneath them matches, so you never look there. You only walk down the branches that disagree.",
        hints=[
            "Build each tree as a list of levels: level 0 is the leaves, the last level is the single root.",
            "Leaf `i` at level `d` has children `2*i` and `2*i + 1` at level `d - 1`.",
            "Count one comparison every time you compare a pair of hashes, whether they turn out equal or different.",
        ],
        brute_force="Compare every leaf: always `buckets` comparisons. The tree walk needs 1 comparison when the replicas agree and about `2 * log2(buckets)` per differing bucket.",
        approach="""1. Group keys by bucket; hash each bucket's sorted `key=value;` string to get the leaves.
2. Hash pairs upward to the root, saving each level.
3. Walk from the root with a stack of `(level, index)`: count a comparison; if the hashes differ, record the bucket at level 0 or push the two children.

**Dry run**, 8 buckets, one differing key in bucket 5: root differs (1). Children: left half equal (2), right half differs (3). Its children: buckets 4-5 differ (4), buckets 6-7 equal (5). Leaves 4 (6, equal) and 5 (7, differs). Result `[[5], 7]`.""",
        complexity="Building: O(K log K) for K keys (sorting within buckets) plus O(buckets) hashes. Comparing: O(1) when equal, O(d log buckets) for d differing buckets.",
        pitfalls="Not sorting keys inside a bucket (two replicas with the same data in different insertion order would look different); counting only unequal comparisons; a separator-free leaf string, where `ab=c` and `a=bc` could collide; forgetting that with one bucket the root is the leaf.",
        follow_up="How would you choose the number of buckets? Too few and each difference forces a large bucket to be transferred; too many and the tree itself is large.",
    ),
),
dict(
    id="sd-snowflake-id",
    title="Snowflake ID Generator and Decoder",
    difficulty="Medium",
    pattern="Unique IDs",
    kind="class",
    entry="Snowflake",
    description=r"""
Implement a Snowflake-style 64-bit ID generator. The clock is passed in, so the behaviour is deterministic.

Layout from the most significant bit: 1 sign bit (always 0), **41 bits** of milliseconds since a custom epoch, **5 bits** data centre, **5 bits** machine, **12 bits** sequence.

`Snowflake(epoch_ms, datacenter, machine)` with `0 <= datacenter, machine <= 31`.

- `next_id(now_ms)`:
  - if `now_ms` is **less than** the time of the last ID issued, the clock went backwards: return `-1` and change nothing;
  - if `now_ms` equals the time of the last ID, use the next sequence number; if all 4096 sequence numbers (0..4095) for this millisecond are used up, return `-2` and change nothing (the caller must wait for the next millisecond);
  - if `now_ms` is later, the sequence restarts at 0;
  - the ID is `((now_ms - epoch_ms) << 22) | (datacenter << 17) | (machine << 12) | sequence`.
- `decode(id)` → `[timestamp_ms, datacenter, machine, sequence]` where `timestamp_ms` is the absolute time (`epoch_ms` added back).

**Example:** `Snowflake(1000, 1, 2)`: `next_id(1005)` → `(5 << 22) | (1 << 17) | (2 << 12) | 0 = 21110784`; `next_id(1005)` → `21110785`; `next_id(1004)` → `-1`; `decode(21110785)` → `[1005, 1, 2, 1]`.
""",
    starter='''class Snowflake:
    def __init__(self, epoch_ms: int, datacenter: int, machine: int):
        pass

    def next_id(self, now_ms: int) -> int:
        pass

    def decode(self, snowflake_id: int) -> List[int]:
        pass
''',
    solution='''class Snowflake:
    def __init__(self, epoch_ms, datacenter, machine):
        self.epoch, self.dc, self.machine = epoch_ms, datacenter, machine
        self.last, self.seq = None, 0

    def next_id(self, now_ms):
        if self.last is not None and now_ms < self.last:
            return -1
        if self.last is not None and now_ms == self.last:
            if self.seq == 4095:
                return -2
            self.seq += 1
        else:
            self.seq = 0
            self.last = now_ms
        return ((now_ms - self.epoch) << 22) | (self.dc << 17) | (self.machine << 12) | self.seq

    def decode(self, snowflake_id):
        return [(snowflake_id >> 22) + self.epoch, (snowflake_id >> 17) & 31,
                (snowflake_id >> 12) & 31, snowflake_id & 4095]
''',
    tests=[
        _ops("Snowflake", [1000, 1, 2], [("next_id", [1005]), ("next_id", [1005]), ("next_id", [1004]), ("decode", [21110785]), ("next_id", [1005]), ("next_id", [1006])]),
        _ops("Snowflake", [0, 0, 0], [("next_id", [0]), ("next_id", [0]), ("next_id", [1]), ("decode", [0]), ("decode", [4194304])]),
        _ops("Snowflake", [1_700_000_000_000, 31, 31], [("next_id", [1_700_000_000_000 + t]) for t in (1, 1, 2, 2, 2, 500, 499, 500, 1000)]),
        _ops("Snowflake", [500, 3, 17], [("next_id", [501])] * 4 + [("decode", [((1 << 22) | (3 << 17) | (17 << 12) | 3)])]),
        _ops("Snowflake", [0, 5, 6], [("next_id", [7])] * 4097 + [("next_id", [8]), ("next_id", [7])]),
        _ops("Snowflake", [100, 0, 1], [("next_id", [100]), ("next_id", [99]), ("next_id", [100]), ("next_id", [100]), ("next_id", [101]), ("next_id", [100])]),
        _ops("Snowflake", [10, 31, 0], [("decode", [(12345 << 22) | (31 << 17) | (0 << 12) | 4095]), ("decode", [(1 << 22)]), ("decode", [4095])]),
        _ops("Snowflake", [1_000_000, 9, 9], [("next_id", [1_000_000 + t // 3]) for t in range(30)]),
        _ops("Snowflake", [0, 1, 1], [("next_id", [2 ** 30 - 1]), ("next_id", [2 ** 30 - 1]), ("decode", [((2 ** 30 - 1) << 22) | (1 << 17) | (1 << 12) | 1])]),
        _ops("Snowflake", [50, 2, 3], [("next_id", [60]), ("next_id", [70]), ("next_id", [70]), ("next_id", [65]), ("next_id", [70]), ("next_id", [71]), ("next_id", [71])]),
        _ops("Snowflake", [0, 0, 31], [("next_id", [1])] * 3 + [("next_id", [3])] * 2 + [("next_id", [2])] + [("next_id", [3])]),
    ],
    examples=1,
    wrong_solutions=[
        '''class Snowflake:
    def __init__(self, epoch_ms, dc, machine):
        self.epoch, self.dc, self.machine, self.last, self.seq = epoch_ms, dc, machine, None, 0
    def next_id(self, now):
        if self.last is not None and now == self.last:
            self.seq = (self.seq + 1) & 4095
        else:
            self.seq, self.last = 0, now
        return ((now - self.epoch) << 22) | (self.dc << 17) | (self.machine << 12) | self.seq
    def decode(self, i):
        return [(i >> 22) + self.epoch, (i >> 17) & 31, (i >> 12) & 31, i & 4095]
''',
        '''class Snowflake:
    def __init__(self, epoch_ms, dc, machine):
        self.epoch, self.dc, self.machine, self.last, self.seq = epoch_ms, dc, machine, None, 0
    def next_id(self, now):
        if self.last is not None and now < self.last:
            return -1
        if self.last is not None and now == self.last:
            if self.seq == 4095:
                return -2
            self.seq += 1
        else:
            self.seq, self.last = 0, now
        return ((now - self.epoch) << 22) | (self.dc << 17) | (self.machine << 12) | self.seq
    def decode(self, i):
        return [(i >> 22), (i >> 17) & 31, (i >> 12) & 31, i & 4095]
''',
        '''class Snowflake:
    def __init__(self, epoch_ms, dc, machine):
        self.epoch, self.dc, self.machine, self.last, self.seq = epoch_ms, dc, machine, None, 0
    def next_id(self, now):
        if self.last is not None and now < self.last:
            return -1
        if self.last is not None and now == self.last:
            if self.seq == 4095:
                return -2
            self.seq += 1
        else:
            self.seq, self.last = 0, now
        return ((now - self.epoch) << 22) | (self.machine << 17) | (self.dc << 12) | self.seq
    def decode(self, i):
        return [(i >> 22) + self.epoch, (i >> 17) & 31, (i >> 12) & 31, i & 4095]
''',
        '''class Snowflake:
    def __init__(self, epoch_ms, dc, machine):
        self.epoch, self.dc, self.machine, self.last, self.seq = epoch_ms, dc, machine, None, 0
    def next_id(self, now):
        if self.last is not None and now < self.last:
            self.last = now
            return -1
        if self.last is not None and now == self.last:
            if self.seq == 4095:
                return -2
            self.seq += 1
        else:
            self.seq, self.last = 0, now
        return ((now - self.epoch) << 22) | (self.dc << 17) | (self.machine << 12) | self.seq
    def decode(self, i):
        return [(i >> 22) + self.epoch, (i >> 17) & 31, (i >> 12) & 31, i & 4095]
''',
    ],
    guide=dict(
        prereqs="Lesson 'Design a unique ID generator II': the bit layout, shifts, OR, masks, and clock handling.",
        intuition="The generator needs to remember only two things: the millisecond of the last ID and the sequence used in it. Same millisecond: count up. New millisecond: restart. Earlier millisecond: refuse.",
        hints=[
            "Shifts: timestamp by 22 (5 + 5 + 12), data centre by 17, machine by 12.",
            "Check the three cases in this order: clock went backwards, same millisecond, later millisecond.",
            "To decode, shift right and mask: `& 31` keeps 5 bits, `& 4095` keeps 12 bits. Add the epoch back to the timestamp.",
        ],
        brute_force="A global counter gives unique IDs trivially but needs coordination between machines and carries no time ordering, which is the whole point of this layout.",
        approach="""State: `last` (None at first) and `seq`.

1. `now < last` → return -1.
2. `now == last` → if `seq == 4095` return -2, else `seq += 1`.
3. otherwise → `seq = 0`, `last = now`.
4. Assemble with shifts and ORs.

**Dry run**, epoch 1000, dc 1, machine 2: `next_id(1005)`: new ms, seq 0 → `5<<22 = 20971520`, `1<<17 = 131072`, `2<<12 = 8192`, total 21110784. Again at 1005: seq 1 → 21110785. `next_id(1004)`: 1004 < 1005 → -1. Decode 21110785: `>> 22` = 5, +1000 = 1005; `(>> 17) & 31` = 1; `(>> 12) & 31` = 2; `& 4095` = 1.""",
        complexity="O(1) time and space per call.",
        pitfalls="Wrapping the sequence silently at 4096, which produces a duplicate ID; updating state when returning -1 or -2; swapping the data centre and machine fields; forgetting to add the epoch back when decoding.",
        follow_up="Make `next_id` thread-safe. Change the split to 16 machine bits and 6 sequence bits and compute the new limits.",
    ),
),
dict(
    id="sd-base62",
    title="Base-62 Encode and Decode",
    difficulty="Easy",
    pattern="URL Shortener",
    kind="class",
    entry="Base62",
    description=r"""
Convert between non-negative integers and base-62 strings using the alphabet

`0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ`

(digit values 0-9, then `a`=10 ... `z`=35, then `A`=36 ... `Z`=61).

`Base62()`:

- `encode(n)` → the base-62 representation of `n` with no leading zeros; `encode(0)` is `"0"`.
- `decode(s)` → the integer the string represents. Leading zeros are allowed in the input (`"007"` decodes to 7).
- `encode_padded(n, width)` → like `encode`, left-padded with `"0"` to at least `width` characters.

**Example:** `encode(61)` → `"Z"`, `encode(62)` → `"10"`, `encode(11157)` → `"2TX"`, `decode("2TX")` → `11157`, `encode_padded(61, 7)` → `"000000Z"`.
""",
    starter='''class Base62:
    def __init__(self):
        pass

    def encode(self, n: int) -> str:
        pass

    def decode(self, s: str) -> int:
        pass

    def encode_padded(self, n: int, width: int) -> str:
        pass
''',
    solution='''class Base62:
    ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def __init__(self):
        self.index = {ch: i for i, ch in enumerate(self.ALPHABET)}

    def encode(self, n):
        if n == 0:
            return "0"
        out = []
        while n > 0:
            n, r = divmod(n, 62)
            out.append(self.ALPHABET[r])
        return "".join(reversed(out))

    def decode(self, s):
        n = 0
        for ch in s:
            n = n * 62 + self.index[ch]
        return n

    def encode_padded(self, n, width):
        return self.encode(n).rjust(width, "0")
''',
    tests=[
        _ops("Base62", [], [("encode", [61]), ("encode", [62]), ("encode", [11157]), ("decode", ["2TX"]), ("encode_padded", [61, 7])]),
        _ops("Base62", [], [("encode", [0]), ("decode", ["0"]), ("decode", ["007"]), ("encode_padded", [0, 3]), ("encode_padded", [0, 0])]),
        _ops("Base62", [], [("encode", [n]) for n in range(0, 130, 7)]),
        _ops("Base62", [], [("encode", [62 ** 7 - 1]), ("encode", [62 ** 7]), ("decode", ["ZZZZZZZ"]), ("decode", ["10000000"])]),
        _ops("Base62", [], [("decode", [s]) for s in ("a", "z", "A", "Z", "10", "a0", "Aa", "zZ", "000", "abcXYZ")]),
        _ops("Base62", [], [("encode", [2_009_215_674_938]), ("decode", ["zn9edcu"]), ("encode", [3_521_614_606_207])]),
        _ops("Base62", [], [("encode_padded", [n, 4]) for n in (1, 62, 3843, 3844, 238327, 238328, 14776336)]),
        _ops("Base62", [], [("encode", [10]), ("encode", [35]), ("encode", [36]), ("encode", [9]), ("encode", [3843]), ("encode", [3844])]),
        _ops("Base62", [], [("decode", ["Z" * k]) for k in range(1, 8)]),
        _ops("Base62", [], [("encode", [2 ** 50]), ("decode", ["1bqqqqqqq"]), ("encode", [2 ** 32]), ("encode", [10 ** 12])]),
    ],
    examples=1,
    wrong_solutions=[
        '''class Base62:
    A = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    def __init__(self):
        self.index = {c: i for i, c in enumerate(self.A)}
    def encode(self, n):
        out = []
        while n > 0:
            n, r = divmod(n, 62)
            out.append(self.A[r])
        return "".join(out) or "0"
    def decode(self, s):
        n = 0
        for c in s:
            n = n * 62 + self.index[c]
        return n
    def encode_padded(self, n, width):
        return self.encode(n).rjust(width, "0")
''',
        '''class Base62:
    A = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    def __init__(self):
        self.index = {c: i for i, c in enumerate(self.A)}
    def encode(self, n):
        if n == 0:
            return "0"
        out = []
        while n > 0:
            n, r = divmod(n, 62)
            out.append(self.A[r])
        return "".join(reversed(out))
    def decode(self, s):
        n = 0
        for c in s:
            n = n * 62 + self.index[c]
        return n
    def encode_padded(self, n, width):
        return self.encode(n).rjust(width, "0")
''',
        '''class Base62:
    A = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    def __init__(self):
        self.index = {c: i for i, c in enumerate(self.A)}
    def encode(self, n):
        out = []
        while n > 0:
            n, r = divmod(n, 62)
            out.append(self.A[r])
        return "".join(reversed(out))
    def decode(self, s):
        n = 0
        for c in s:
            n = n * 62 + self.index[c]
        return n
    def encode_padded(self, n, width):
        return self.encode(n).rjust(width, "0")
''',
    ],
    guide=dict(
        prereqs="Lesson 'Design a URL shortener I', section 6 on base 62. `divmod`.",
        intuition="It is the same procedure as writing a number in base 10, with 62 symbols instead of 10: peel off the last digit with the remainder, shrink the number with the quotient, repeat.",
        hints=[
            "`divmod(n, 62)` gives the quotient and the remainder in one step.",
            "The remainders come out least-significant digit first, so reverse them at the end.",
            "To decode, go left to right: `n = n * 62 + value_of(character)`.",
        ],
        brute_force="Python's `int(s, base)` only goes up to base 36, so there is no built-in; the loop above is the standard approach and already optimal.",
        approach="""Encode: handle 0 specially; loop `n, r = divmod(n, 62)`, append `ALPHABET[r]`; reverse.
Decode: build a character-to-value dictionary once; fold from the left.

**Dry run** `encode(11157)`: 11157 = 179 x 62 + 59 → `X`; 179 = 2 x 62 + 55 → `T`; 2 = 0 x 62 + 2 → `2`. Reversed: `2TX`. `decode("2TX")`: 2 → 2 x 62 + 55 = 179 → 179 x 62 + 59 = 11157.""",
        complexity="O(log62 n) time and space: one step per output character.",
        pitfalls="Forgetting to reverse; returning an empty string for 0; using an alphabet in a different order (upper case before lower case gives different, incompatible codes); `list.index` lookups making decode quadratic.",
        follow_up="Remove look-alike characters (0, O, 1, l, I) to make a base-57 alphabet and compute how long a code must be for 365 billion links.",
    ),
),
dict(
    id="sd-url-shortener-store",
    title="URL Shortener Store with Collision Handling",
    difficulty="Medium",
    pattern="URL Shortener",
    kind="class",
    entry="Shortener",
    description=r"""
Implement the hash-and-resolve-collisions approach to short codes.

Let `B62(n)` be the base-62 encoding of `n` with alphabet `0-9a-zA-Z`, and define the **candidate code** of a text as the last `length` characters of `B62(int(hashlib.md5(text.encode()).hexdigest(), 16))`.

`Shortener(length)`:

- `shorten(long_url)` → a code. Start with `attempt = long_url` and `salt = 0`, then repeat:
  1. `code = candidate(attempt)`;
  2. if `code` is unused, store `code -> long_url` and return it;
  3. if `code` already maps to this same `long_url`, return it (no new entry);
  4. otherwise it is a collision: `salt += 1`, `attempt = long_url + "#" + str(salt)`, and try again.
- `shorten_custom(long_url, alias)` → `True` and store `alias -> long_url` if `alias` is not in use by anything; otherwise `False`.
- `resolve(code)` → the long URL, or `None`.
- `count()` → number of stored codes.

**Example:** with `length = 7`, `shorten("https://a.example/x")` twice returns the same code and `count()` is 1.
""",
    starter='''import hashlib

class Shortener:
    def __init__(self, length: int):
        pass

    def shorten(self, long_url: str) -> str:
        pass

    def shorten_custom(self, long_url: str, alias: str) -> bool:
        pass

    def resolve(self, code: str):
        pass

    def count(self) -> int:
        pass
''',
    solution='''import hashlib

class Shortener:
    ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def __init__(self, length):
        self.length = length
        self.store = {}

    def _candidate(self, text):
        n = int(hashlib.md5(text.encode()).hexdigest(), 16)
        out = []
        while n > 0:
            n, r = divmod(n, 62)
            out.append(self.ALPHABET[r])
        return ("".join(reversed(out)) or "0")[-self.length:]

    def shorten(self, long_url):
        attempt, salt = long_url, 0
        while True:
            code = self._candidate(attempt)
            existing = self.store.get(code)
            if existing is None:
                self.store[code] = long_url
                return code
            if existing == long_url:
                return code
            salt += 1
            attempt = long_url + "#" + str(salt)

    def shorten_custom(self, long_url, alias):
        if alias in self.store:
            return False
        self.store[alias] = long_url
        return True

    def resolve(self, code):
        return self.store.get(code)

    def count(self):
        return len(self.store)
''',
    tests=[
        _ops("Shortener", [7], [("shorten", ["https://a.example/x"]), ("shorten", ["https://a.example/x"]), ("count", []), ("resolve", ["nope"])]),
        _ops("Shortener", [1], [("shorten", [f"https://e.com/{i}"]) for i in range(40)] + [("count", [])]),
        _ops("Shortener", [1], [("shorten", [f"https://e.com/{i}"]) for i in range(20)] + [("shorten", [f"https://e.com/{i}"]) for i in range(20)] + [("count", [])]),
        _ops("Shortener", [2], [("shorten", [f"u{i}"]) for i in range(150)] + [("count", [])]),
        _ops("Shortener", [6], [("shorten_custom", ["https://sale.example", "summer"]), ("shorten_custom", ["https://other.example", "summer"]), ("resolve", ["summer"]), ("count", [])]),
        _ops("Shortener", [1], [("shorten_custom", ["https://x.example", c]) for c in "0123456789abcdef"] + [("shorten", [f"https://y.example/{i}"]) for i in range(12)] + [("count", [])]),
        _ops("Shortener", [3], [("shorten", ["a"]), ("shorten", ["b"]), ("shorten", ["a"]), ("shorten", [""]), ("count", [])]),
        _ops("Shortener", [1], [("shorten", ["only"]), ("resolve", ["?"]), ("count", [])]),
        _ops("Shortener", [1], [("shorten", [f"p{i}"]) for i in range(62)] + [("count", [])]),
        _ops("Shortener", [2], [("shorten", ["dup"])] * 5 + [("shorten_custom", ["dup", "zz"]), ("shorten", ["dup"]), ("count", [])]),
        _ops("Shortener", [5], [("shorten", [f"https://site.example/page?id={i}"]) for i in range(30)] + [("count", [])]),
    ],
    examples=1,
    wrong_solutions=[
        '''import hashlib
class Shortener:
    A = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    def __init__(self, length):
        self.length, self.store = length, {}
    def _c(self, t):
        n = int(hashlib.md5(t.encode()).hexdigest(), 16); out = []
        while n > 0:
            n, r = divmod(n, 62); out.append(self.A[r])
        return ("".join(reversed(out)) or "0")[-self.length:]
    def shorten(self, u):
        code = self._c(u)
        self.store[code] = u
        return code
    def shorten_custom(self, u, a):
        if a in self.store:
            return False
        self.store[a] = u
        return True
    def resolve(self, c):
        return self.store.get(c)
    def count(self):
        return len(self.store)
''',
        '''import hashlib
class Shortener:
    A = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    def __init__(self, length):
        self.length, self.store = length, {}
    def _c(self, t):
        n = int(hashlib.md5(t.encode()).hexdigest(), 16); out = []
        while n > 0:
            n, r = divmod(n, 62); out.append(self.A[r])
        return ("".join(reversed(out)) or "0")[-self.length:]
    def shorten(self, u):
        attempt, salt = u, 0
        while True:
            code = self._c(attempt)
            if code not in self.store:
                self.store[code] = u
                return code
            salt += 1
            attempt = u + "#" + str(salt)
    def shorten_custom(self, u, a):
        if a in self.store:
            return False
        self.store[a] = u
        return True
    def resolve(self, c):
        return self.store.get(c)
    def count(self):
        return len(self.store)
''',
        '''import hashlib
class Shortener:
    A = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    def __init__(self, length):
        self.length, self.store = length, {}
    def _c(self, t):
        n = int(hashlib.md5(t.encode()).hexdigest(), 16); out = []
        while n > 0:
            n, r = divmod(n, 62); out.append(self.A[r])
        return ("".join(reversed(out)) or "0")[-self.length:]
    def shorten(self, u):
        attempt, salt = u, 0
        while True:
            code = self._c(attempt)
            e = self.store.get(code)
            if e is None:
                self.store[code] = u
                return code
            if e == u:
                return code
            salt += 1
            attempt = attempt + "#" + str(salt)
    def shorten_custom(self, u, a):
        self.store[a] = u
        return True
    def resolve(self, c):
        return self.store.get(c)
    def count(self):
        return len(self.store)
''',
    ],
    guide=dict(
        prereqs="Lesson 'Design a URL shortener II', the hash-and-resolve approach. The Base-62 problem.",
        intuition="A truncated hash is a good first guess for a code, but two URLs can share it. When the slot is taken by a different URL, perturb the input in a repeatable way and try again; when it is taken by the same URL, you have found the answer you gave last time.",
        hints=[
            "Write `_candidate(text)`: md5 → big integer → base 62 → last `length` characters.",
            "Three outcomes when you look a code up: free, same URL, different URL.",
            "The salt is appended to the ORIGINAL url each time (`url#1`, `url#2`), not to the previous attempt.",
        ],
        brute_force="Ignore collisions and overwrite: every collision silently redirects an older link to a new destination, the worst possible bug for this product.",
        approach="""1. `candidate` as defined.
2. Loop: look the candidate up; store and return if free; return if it already holds this URL; otherwise increment the salt and retry.
3. `shorten_custom` is a conditional insert.

**Dry run** with `length = 1`: suppose `u1` and `u2` both hash to code `k`. `shorten(u1)` stores `k`. `shorten(u2)` finds `k` holding `u1`, tries `u2#1`, which gives (say) `4`, free: stored. Calling `shorten(u2)` again walks the same path: `k` (taken by u1), then `4` (holds u2): returned, nothing added.""",
        complexity="Expected O(1) attempts while the code space is sparsely used; attempts grow as it fills. Each attempt is one hash and one dictionary lookup.",
        pitfalls="Overwriting on collision; treating 'same URL' as a collision (creates a new code every time); salting the previous attempt instead of the original URL, which breaks repeatability; letting a custom alias overwrite an existing code.",
        follow_up="Add a Bloom filter in front of the store to skip the existence check for codes that are definitely new. Compare with the counter-plus-base-62 approach.",
    ),
),
]
