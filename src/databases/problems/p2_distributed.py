"""Problems for modules 5-8: replication, partitioning, transactions, fencing."""
import random as _r

_rng = _r.Random(11)


def _rand_clock(nodes):
    return {n: _rng.randint(0, 3) for n in nodes if _rng.random() < 0.8}


def _rand_txns(n):
    keys = ["a", "b", "c", "d"]
    out = []
    for i in range(1, n + 1):
        s = _rng.randint(0, 30)
        out.append([i, s, s + _rng.randint(1, 8),
                    _rng.sample(keys, _rng.randint(0, 3)), _rng.sample(keys, _rng.randint(0, 2))])
    return out


PROBLEMS = [
dict(
    id="db-quorum-read",
    title="Quorum Read with Versions and Read Repair",
    difficulty="Easy",
    pattern="Replication",
    kind="function",
    entry="quorum_read",
    description=r"""
In a leaderless (Dynamo-style) database a client reads from several replicas in parallel and keeps the
freshest answer.

`responses[i]` is the reply of replica `i`: either `[value, version]` (version is an integer; higher is newer)
or `None` if that replica did not answer in time. `r` is the read quorum.

- If fewer than `r` replicas answered, the read fails: return `None`.
- Otherwise return `[value, stale]`, where `value` is the value carrying the highest version among **all**
  replies received, and `stale` is the ascending list of indices of replicas that answered with a lower
  version (these are the targets for **read repair**). Replicas that did not answer are not listed.

**Example:** `responses = [["blue", 3], None, ["red", 4]], r = 2` → `["red", [0]]`

**Example:** `responses = [["blue", 3], None, None], r = 2` → `None`
""",
    starter='''def quorum_read(responses: List[Optional[list]], r: int):
    pass
''',
    solution='''def quorum_read(responses, r):
    live = [(i, resp) for i, resp in enumerate(responses) if resp is not None]
    if len(live) < r:
        return None
    best_version = max(resp[1] for _, resp in live)
    value = next(resp[0] for _, resp in live if resp[1] == best_version)
    stale = [i for i, resp in live if resp[1] < best_version]
    return [value, stale]
''',
    tests=[
        [[["blue", 3], None, ["red", 4]], 2],
        [[["blue", 3], None, None], 2],
        [[["x", 1], ["x", 1], ["x", 1]], 2],
        [[None, None, None], 1],
        [[["a", 7]], 1],
        [[["old", 1], ["older", 0], ["new", 2], None, ["new", 2]], 3],
        [[["old", 1], None, None, None, ["new", 2]], 3],
        [[["v9", 9], ["v2", 2], ["v5", 5]], 3],
        [[["v9", 9], ["v2", 2], ["v5", 5]], 4],
        [[None, [None, 5], ["ghost", 4]], 2],
        [[["a", 10], ["b", 9]] * 50, 60],
        [[], 0],
    ],
    examples=2,
    wrong_solutions=[
        '''def quorum_read(responses, r):
    live = [x for x in responses if x is not None]
    if len(live) < r:
        return None
    return [live[0][0], []]
''',
        '''def quorum_read(responses, r):
    if len(responses) < r:
        return None
    live = [(i, x) for i, x in enumerate(responses) if x is not None]
    if not live:
        return None
    best = max(x[1] for _, x in live)
    return [next(x[0] for _, x in live if x[1] == best), [i for i, x in live if x[1] < best]]
''',
        '''def quorum_read(responses, r):
    live = [(i, x) for i, x in enumerate(responses) if x is not None][:r]
    if len(live) < r:
        return None
    best = max(x[1] for _, x in live)
    return [next(x[0] for _, x in live if x[1] == best), [i for i, x in live if x[1] < best]]
''',
    ],
    guide=dict(
        prereqs="Lesson *Multi-leader and leaderless replication, quorums*.",
        intuition="If a write reached `w` replicas and you hear from `r` replicas with `w + r > n`, at least one reply must come from a replica that saw the write. Version numbers tell you which reply that is.",
        hints=[
            "First filter out the `None`s but remember each reply's original index.",
            "Count the replies before doing anything else - below `r` you must refuse to answer.",
            "Find the maximum version, then make a second pass to collect the replicas that are behind it.",
        ],
        brute_force="Compare every reply with every other reply to decide whether it is stale: O(n^2). One pass for the maximum makes that unnecessary.",
        approach="1. `live = [(i, resp)]` for non-`None` replies.\n2. `len(live) < r` → `None`.\n3. `best = max(version)`; value = any reply with that version.\n4. `stale = [i for (i, resp) in live if version < best]`.\n\nDry run: replies `blue@3`, timeout, `red@4`, r=2 → two replies, best = 4 → `red`; replica 0 is behind → `[\"red\", [0]]`.",
        complexity="O(n) time and space for n replicas.",
        pitfalls="Counting timeouts towards the quorum; returning the first reply instead of the newest; listing unreachable replicas as stale (read repair can only be sent to nodes you can talk to - the rest is the job of anti-entropy); a stored value may itself be `None`, so test `resp is None`, not the value.",
        follow_up="A single integer version only works when writes to a key are totally ordered. With concurrent writers you need version vectors and may have to return several sibling values - see `db-vector-clock-compare`.",
    ),
),
dict(
    id="db-lww-merge",
    title="Last-Write-Wins Merge",
    difficulty="Easy",
    pattern="Replication",
    kind="function",
    entry="lww_merge",
    description=r"""
Two replicas have diverged and must converge. Each replica is a dict mapping
`key -> [value, timestamp, node_id]`, where `timestamp` is an integer, `node_id` is the string id of the
node that accepted the write, and `value = None` marks a deletion (tombstone).

Merge them with **last write wins**:

- a key present on only one side is copied;
- otherwise the entry with the larger `timestamp` wins;
- equal timestamps are broken by the larger `node_id` (string comparison).

Tombstones take part in the comparison like any other write and are **kept** in the result (otherwise a
deleted key could reappear at the next merge). Return the merged dict; do not modify the inputs.

**Example:**
`a = {"x": [1, 10, "n1"], "y": [2, 5, "n1"]}`, `b = {"x": [9, 12, "n2"], "z": [None, 3, "n2"]}`
→ `{"x": [9, 12, "n2"], "y": [2, 5, "n1"], "z": [None, 3, "n2"]}`
""",
    starter='''def lww_merge(a: dict, b: dict) -> dict:
    pass
''',
    solution='''def lww_merge(a, b):
    out = {k: list(v) for k, v in a.items()}
    for k, v in b.items():
        cur = out.get(k)
        if cur is None or (v[1], v[2]) > (cur[1], cur[2]):
            out[k] = list(v)
    return out
''',
    tests=[
        [{"x": [1, 10, "n1"], "y": [2, 5, "n1"]}, {"x": [9, 12, "n2"], "z": [None, 3, "n2"]}],
        [{}, {}],
        [{"k": [1, 1, "a"]}, {}],
        [{}, {"k": [1, 1, "a"]}],
        [{"k": ["left", 7, "n1"]}, {"k": ["right", 7, "n2"]}],
        [{"k": ["left", 7, "n2"]}, {"k": ["right", 7, "n1"]}],
        [{"k": ["alive", 5, "n1"]}, {"k": [None, 6, "n2"]}],
        [{"k": [None, 6, "n1"]}, {"k": ["revived", 9, "n2"]}],
        [{"k": [None, 9, "n1"]}, {"k": ["late", 4, "n2"]}],
        [{"k": ["same", 3, "n1"]}, {"k": ["same", 3, "n1"]}],
        [{"a": [100, 1, "n9"], "b": [0, 50, "n1"]}, {"a": [5, 2, "n1"], "b": [1, 49, "n9"]}],
        [{"k%d" % i: [i, i % 13, "n1"] for i in range(400)}, {"k%d" % i: [-i, i % 11, "n2"] for i in range(200, 600)}],
    ],
    examples=1,
    wrong_solutions=[
        '''def lww_merge(a, b):
    out = dict(a)
    out.update(b)
    return out
''',
        '''def lww_merge(a, b):
    out = {k: list(v) for k, v in a.items()}
    for k, v in b.items():
        if k not in out or v[1] > out[k][1]:
            out[k] = list(v)
    return out
''',
        '''def lww_merge(a, b):
    out = {k: list(v) for k, v in a.items()}
    for k, v in b.items():
        cur = out.get(k)
        if cur is None or (v[1], v[2]) > (cur[1], cur[2]):
            out[k] = list(v)
    return {k: v for k, v in out.items() if v[0] is not None}
''',
    ],
    guide=dict(
        prereqs="Tuple comparison in Python. Lesson *Detecting concurrent writes: LWW, version vectors, CRDTs*.",
        intuition="Give every write a tag that is totally ordered - (timestamp, node id) - and let the biggest tag win everywhere. Because *max* is commutative, associative and idempotent, replicas converge no matter in which order they exchange data.",
        hints=[
            "Start from a copy of `a`, then fold `b` in key by key.",
            "Compare `(timestamp, node_id)` tuples; Python compares them lexicographically.",
            "Do not special-case `None` values - a tombstone is just a write whose value happens to be `None`.",
        ],
        brute_force="Iterate over the union of keys and write out four cases (only in a, only in b, a newer, b newer) by hand. Same complexity, more room for mistakes.",
        approach="1. `out = copy(a)`.\n2. For each `(k, v)` in `b`: if `k` is absent from `out` or `(v.ts, v.node) > (out[k].ts, out[k].node)`, replace.\n3. Return `out`.\n\nDry run: `x` exists on both sides, `(12, \"n2\") > (10, \"n1\")` → b's value 9 wins. `y` only in a, `z` only in b (a tombstone, kept).",
        complexity="O(|a| + |b|) time and space.",
        pitfalls="`dict.update` (makes b win regardless of time); ignoring the tie-break, so two replicas merging in opposite directions keep different values and never converge; dropping tombstones during merge.",
        follow_up="LWW converges but silently discards one of two concurrent writes, and the 'last' write is decided by clocks that may be skewed. When losing data is unacceptable use version vectors with siblings or a CRDT.",
    ),
),
dict(
    id="db-vector-clock-compare",
    title="Compare Version Vectors",
    difficulty="Easy",
    pattern="Replication",
    kind="function",
    entry="compare_clocks",
    description=r"""
A version vector (vector clock) maps a node id to the number of events from that node which a version has
seen. A node missing from the dict counts as `0`.

Given two vectors `a` and `b`, return:

- `"equal"` - every counter is the same;
- `"before"` - `a` happened before `b`: every counter of `a` is `<=` the one in `b`, and at least one is smaller;
- `"after"` - the mirror case, `b` happened before `a`;
- `"concurrent"` - each has seen something the other has not.

**Example:** `a = {"n1": 2, "n2": 1}`, `b = {"n1": 3, "n2": 1}` → `"before"`

**Example:** `a = {"n1": 2}`, `b = {"n2": 1}` → `"concurrent"`
""",
    starter='''def compare_clocks(a: Dict[str, int], b: Dict[str, int]) -> str:
    pass
''',
    solution='''def compare_clocks(a, b):
    a_less = b_less = False
    for node in set(a) | set(b):
        x, y = a.get(node, 0), b.get(node, 0)
        if x < y:
            a_less = True
        elif x > y:
            b_less = True
    if a_less and b_less:
        return "concurrent"
    if a_less:
        return "before"
    if b_less:
        return "after"
    return "equal"
''',
    tests=[
        [{"n1": 2, "n2": 1}, {"n1": 3, "n2": 1}],
        [{"n1": 2}, {"n2": 1}],
        [{}, {}],
        [{"n1": 1}, {"n1": 1}],
        [{}, {"n1": 1}],
        [{"n1": 1}, {}],
        [{"n1": 0}, {}],
        [{"n1": 3, "n2": 0}, {"n1": 3}],
        [{"n1": 1, "n2": 2}, {"n1": 2, "n2": 1}],
        [{"n1": 5, "n2": 5, "n3": 5}, {"n1": 5, "n2": 5, "n3": 4}],
        [{"a": 1, "b": 1}, {"a": 1, "b": 1, "c": 1}],
        [{"a": 2, "b": 1}, {"a": 1, "b": 1, "c": 1}],
    ] + [[_rand_clock("abcd"), _rand_clock("abcd")] for _ in range(3)],
    examples=2,
    wrong_solutions=[
        '''def compare_clocks(a, b):
    sa, sb = sum(a.values()), sum(b.values())
    if a == b:
        return "equal"
    return "before" if sa < sb else "after" if sa > sb else "concurrent"
''',
        '''def compare_clocks(a, b):
    a_less = b_less = False
    for node in a:
        if node in b:
            if a[node] < b[node]:
                a_less = True
            elif a[node] > b[node]:
                b_less = True
    if a_less and b_less:
        return "concurrent"
    return "before" if a_less else "after" if b_less else "equal"
''',
        '''def compare_clocks(a, b):
    if a == b:
        return "equal"
    if all(a.get(n, 0) <= b.get(n, 0) for n in set(a) | set(b)):
        return "before"
    return "after"
''',
    ],
    guide=dict(
        prereqs="Partial orders. Lessons *Detecting concurrent writes* and *Ordering, causality, Lamport clocks*.",
        intuition="A vector summarises *what a version knows*. If b knows everything a knows and more, b descends from a and may safely overwrite it. If each knows something the other does not, nobody saw the other's write: they are concurrent and a merge is needed.",
        hints=[
            "Iterate over the **union** of node ids, reading missing entries as 0.",
            "Track two booleans: 'a is smaller somewhere' and 'b is smaller somewhere'.",
            "Both true → concurrent; only the first → before; only the second → after; neither → equal.",
        ],
        brute_force="Two separate dominance checks (`all(a<=b)` and `all(b<=a)`) each scanning the union: same O(n), just two passes.",
        approach="One pass over the union setting the two flags, then a four-way decision. Dry run: `{n1:2}` vs `{n2:1}` → on n1, b is smaller; on n2, a is smaller → both flags → concurrent.",
        complexity="O(n) time for n distinct node ids, O(n) space for the union set.",
        pitfalls="Looping only over the keys of `a`; comparing sums (a Lamport-style scalar cannot detect concurrency); treating `{n1: 0}` and `{}` as different.",
        follow_up="To merge two concurrent siblings, the new version's vector is the element-wise maximum of both, with the writing node's own counter incremented.",
    ),
),
dict(
    id="db-range-router",
    title="Range Partition Router",
    difficulty="Medium",
    pattern="Partitioning",
    kind="class",
    entry="RangeRouter",
    description=r"""
A key-range partitioned database keeps a sorted list of **split points**. With split points
`[b0, b1, ..., b(k-1)]` there are `k + 1` partitions:

- partition `0` holds keys `< b0`,
- partition `i` holds keys with `b(i-1) <= key < b(i)`,
- partition `k` holds keys `>= b(k-1)`.

Implement `RangeRouter(boundaries)` (`boundaries` is sorted, without duplicates, possibly empty). Keys are strings.

- `route(key)` - index of the partition that owns `key`.
- `route_range(lo, hi)` - ascending list of partition indices that may contain keys in the half-open range `[lo, hi)`; empty list if `lo >= hi`.
- `split(key)` - add `key` as a new split point (splitting the partition that owns it). Return `True`, or `False` if it is already a split point.
- `num_partitions()` - current number of partitions.

**Example:** `RangeRouter(["g", "p"])`: `route("apple")` → 0, `route("g")` → 1, `route("zebra")` → 2,
`route_range("f", "h")` → `[0, 1]`, `route_range("g", "p")` → `[1]`, `split("k")` → True, `route("m")` → 2
""",
    starter='''class RangeRouter:
    def __init__(self, boundaries: List[str]):
        pass

    def route(self, key: str) -> int:
        pass

    def route_range(self, lo: str, hi: str) -> List[int]:
        pass

    def split(self, key: str) -> bool:
        pass

    def num_partitions(self) -> int:
        pass
''',
    solution='''class RangeRouter:
    def __init__(self, boundaries):
        self.b = list(boundaries)

    def route(self, key):
        import bisect
        return bisect.bisect_right(self.b, key)

    def route_range(self, lo, hi):
        import bisect
        if lo >= hi:
            return []
        first = bisect.bisect_right(self.b, lo)
        last = bisect.bisect_left(self.b, hi)      # partition of the largest key strictly below hi
        return list(range(first, last + 1))

    def split(self, key):
        import bisect
        i = bisect.bisect_left(self.b, key)
        if i < len(self.b) and self.b[i] == key:
            return False
        self.b.insert(i, key)
        return True

    def num_partitions(self):
        return len(self.b) + 1
''',
    tests=[
        [["RangeRouter", "route", "route", "route", "route_range", "route_range", "split", "route"],
         [[["g", "p"]], ["apple"], ["g"], ["zebra"], ["f", "h"], ["g", "p"], ["k"], ["m"]]],
        [["RangeRouter", "route", "route_range", "num_partitions"], [[[]], ["anything"], ["a", "z"], []]],
        [["RangeRouter", "split", "split", "num_partitions", "route", "route"], [[[]], ["m"], ["m"], [], ["m"], ["l"]]],
        [["RangeRouter", "route_range", "route_range", "route_range", "route_range"],
         [[["d", "h", "m"]], ["a", "z"], ["h", "h"], ["z", "a"], ["d", "da"]]],
        [["RangeRouter", "route_range", "route_range", "route_range"],
         [[["d", "h", "m"]], ["a", "d"], ["a", "da"], ["m", "zzz"]]],
        [["RangeRouter", "route", "route", "route", "route"], [[["b"]], [""], ["a"], ["b"], ["ba"]]],
        [["RangeRouter", "split", "split", "split", "route", "route", "route", "route", "num_partitions"],
         [[["m"]], ["t"], ["c"], ["h"], ["a"], ["c"], ["j"], ["x"], []]],
        [["RangeRouter"] + ["route"] * 26 + ["route_range", "num_partitions"],
         [[["e", "j", "o", "t", "y"]]] + [[chr(97 + i)] for i in range(26)] + [["i", "u"], []]],
        [["RangeRouter"] + ["split"] * 40 + ["num_partitions"] + ["route"] * 20 + ["route_range"],
         [[[]]] + [["key%03d" % ((i * 37) % 100)] for i in range(40)] + [[]]
         + [["key%03d" % (i * 5)] for i in range(20)] + [["key010", "key050"]]],
        [["RangeRouter", "route_range", "split", "route_range", "route_range"],
         [[["k"]], ["a", "k"], ["f"], ["a", "k"], ["f", "g"]]],
    ],
    examples=1,
    wrong_solutions=[
        '''class RangeRouter:
    def __init__(self, boundaries):
        self.b = list(boundaries)
    def route(self, key):
        import bisect
        return bisect.bisect_left(self.b, key)
    def route_range(self, lo, hi):
        import bisect
        if lo >= hi:
            return []
        return list(range(bisect.bisect_left(self.b, lo), bisect.bisect_left(self.b, hi) + 1))
    def split(self, key):
        if key in self.b:
            return False
        self.b.append(key); self.b.sort()
        return True
    def num_partitions(self):
        return len(self.b) + 1
''',
        '''class RangeRouter:
    def __init__(self, boundaries):
        self.b = list(boundaries)
    def route(self, key):
        import bisect
        return bisect.bisect_right(self.b, key)
    def route_range(self, lo, hi):
        if lo >= hi:
            return []
        return list(range(self.route(lo), self.route(hi) + 1))
    def split(self, key):
        if key in self.b:
            return False
        self.b.append(key); self.b.sort()
        return True
    def num_partitions(self):
        return len(self.b) + 1
''',
        '''class RangeRouter:
    def __init__(self, boundaries):
        self.b = list(boundaries)
    def route(self, key):
        import bisect
        return bisect.bisect_right(self.b, key)
    def route_range(self, lo, hi):
        import bisect
        if lo >= hi:
            return []
        return list(range(bisect.bisect_right(self.b, lo), bisect.bisect_left(self.b, hi) + 1))
    def split(self, key):
        self.b.append(key); self.b.sort()
        return True
    def num_partitions(self):
        return len(self.b) + 1
''',
    ],
    guide=dict(
        prereqs="`bisect_left` vs `bisect_right`. Lessons *Partitioning key-value data and hot spots* and *Secondary indexes, rebalancing and request routing*.",
        intuition="The routing table of a range-partitioned store is nothing but a sorted array of boundaries. Finding the owner of a key is 'how many boundaries are <= key', which is exactly what `bisect_right` computes.",
        hints=[
            "A key equal to a boundary belongs to the partition on the **right** of it.",
            "For a range `[lo, hi)`, the first partition is `route(lo)`. The last one is the partition of the largest key strictly below `hi` - think about what happens when `hi` is itself a boundary.",
            "`bisect_left(boundaries, hi)` counts the boundaries strictly below `hi`, which is the index of that last partition.",
        ],
        brute_force="Scan the boundaries linearly for every lookup: O(k) per route. Acceptable for ten partitions, not for the tens of thousands of tablets a large cluster has.",
        approach="`route`: `bisect_right(b, key)`.\n`route_range`: empty if `lo >= hi`; else `range(bisect_right(b, lo), bisect_left(b, hi) + 1)`.\n`split`: binary-search the position; reject duplicates; insert.\n\nDry run with `[g, p]`: `route_range(\"g\", \"p\")` → first = bisect_right(g) = 1, last = bisect_left(p) = 1 → `[1]`. The exclusive upper bound `p` does not drag in partition 2.",
        complexity="`route` and `route_range` O(log k) (+ output size); `split` O(k) because of the list insert.",
        pitfalls="Using `bisect_left` for point routing (keys equal to a boundary go one partition too far left); including an extra partition when `hi` equals a boundary; accepting duplicate split points, which creates an empty phantom partition.",
        follow_up="Range partitioning makes scans cheap but invites hot spots when keys are sequential (timestamps). How does prefixing the key with a sensor id or hashing the key change `route_range`?",
    ),
),
dict(
    id="db-consistent-hashing",
    title="Consistent Hashing Ring with Virtual Nodes",
    difficulty="Medium",
    pattern="Partitioning",
    kind="class",
    entry="HashRing",
    description=r"""
Implement a consistent-hashing ring. Use the 32-bit **FNV-1a** hash so results are deterministic:

```
h = 2166136261
for each byte c of the UTF-8 encoding of s:
    h = h XOR c
    h = (h * 16777619) mod 2^32
```

`HashRing(vnodes)` creates an empty ring in which every physical node owns `vnodes` tokens.

- `add_node(name)` - place tokens `fnv1a(name + "#" + str(i))` for `i = 0 .. vnodes-1` on the ring. Returns nothing. (Adding an existing node does nothing.)
- `remove_node(name)` - remove all tokens of that node (no-op if unknown). Returns nothing.
- `get_node(key)` - hash the key, walk clockwise to the first token whose position is `>=` the key's hash
  (wrapping around to the smallest token), and return the owning node's name; `None` if the ring is empty.
  If two tokens share a position, the one whose node name is alphabetically smaller comes first.

**Example:** `HashRing(3)`, `add_node("A")`, `add_node("B")`, then `get_node("user42")` returns `"A"` or `"B"`
depending on the hashes; after `remove_node` of that node the same key moves to the other one, while keys
owned by the surviving node stay where they were.
""",
    starter='''class HashRing:
    def __init__(self, vnodes: int):
        pass

    def add_node(self, name: str) -> None:
        pass

    def remove_node(self, name: str) -> None:
        pass

    def get_node(self, key: str) -> Optional[str]:
        pass
''',
    solution='''class HashRing:
    def __init__(self, vnodes):
        self.vnodes = vnodes
        self.ring = []            # sorted list of (token, node)
        self.nodes = set()

    @staticmethod
    def _h(s):
        h = 2166136261
        for c in s.encode("utf-8"):
            h ^= c
            h = (h * 16777619) % (1 << 32)
        return h

    def add_node(self, name):
        import bisect
        if name in self.nodes:
            return
        self.nodes.add(name)
        for i in range(self.vnodes):
            bisect.insort(self.ring, (self._h(name + "#" + str(i)), name))

    def remove_node(self, name):
        if name in self.nodes:
            self.nodes.discard(name)
            self.ring = [t for t in self.ring if t[1] != name]

    def get_node(self, key):
        import bisect
        if not self.ring:
            return None
        i = bisect.bisect_left(self.ring, (self._h(key), ""))
        return self.ring[i % len(self.ring)][1]
''',
    tests=[
        [["HashRing", "add_node", "add_node"] + ["get_node"] * 8,
         [[3], ["A"], ["B"]] + [["user%d" % i] for i in range(8)]],
        [["HashRing", "get_node", "remove_node", "get_node"], [[4], ["k"], ["ghost"], ["k"]]],
        [["HashRing", "add_node", "get_node", "get_node", "remove_node", "get_node"],
         [[1], ["solo"], ["a"], ["zzzz"], ["solo"], ["a"]]],
        [["HashRing", "add_node", "add_node", "add_node"] + ["get_node"] * 30,
         [[1], ["n1"], ["n2"], ["n3"]] + [["key-%d" % i] for i in range(30)]],
        [["HashRing", "add_node", "add_node", "add_node"] + ["get_node"] * 30 + ["remove_node"] + ["get_node"] * 30,
         [[8], ["n1"], ["n2"], ["n3"]] + [["key-%d" % i] for i in range(30)] + [["n2"]] + [["key-%d" % i] for i in range(30)]],
        [["HashRing", "add_node", "add_node"] + ["get_node"] * 20 + ["add_node"] + ["get_node"] * 20,
         [[16], ["alpha"], ["beta"]] + [["obj%d" % i] for i in range(20)] + [["gamma"]] + [["obj%d" % i] for i in range(20)]],
        [["HashRing", "add_node", "add_node", "add_node"] + ["get_node"] * 10,
         [[5], ["x"], ["x"], ["y"]] + [["dup%d" % i] for i in range(10)]],
        [["HashRing"] + ["add_node"] * 10 + ["get_node"] * 100,
         [[50]] + [["server-%d" % i] for i in range(10)] + [["item:%d" % i] for i in range(100)]],
        [["HashRing", "add_node", "add_node", "remove_node", "remove_node", "get_node", "add_node", "get_node"],
         [[3], ["a"], ["b"], ["a"], ["b"], ["k"], ["c"], ["k"]]],
        [["HashRing", "add_node", "add_node"] + ["get_node"] * 12,
         [[2], ["东京"], ["ñandú"]] + [["clé-%d" % i] for i in range(12)]],
    ],
    examples=1,
    wrong_solutions=[
        '''class HashRing:
    def __init__(self, vnodes):
        self.nodes = []
    @staticmethod
    def _h(s):
        h = 2166136261
        for c in s.encode("utf-8"):
            h ^= c
            h = (h * 16777619) % (1 << 32)
        return h
    def add_node(self, name):
        if name not in self.nodes:
            self.nodes.append(name)
    def remove_node(self, name):
        if name in self.nodes:
            self.nodes.remove(name)
    def get_node(self, key):
        if not self.nodes:
            return None
        return self.nodes[self._h(key) % len(self.nodes)]
''',
        '''class HashRing:
    def __init__(self, vnodes):
        self.vnodes, self.ring, self.nodes = vnodes, [], set()
    @staticmethod
    def _h(s):
        h = 2166136261
        for c in s.encode("utf-8"):
            h ^= c
            h = (h * 16777619) % (1 << 32)
        return h
    def add_node(self, name):
        if name in self.nodes:
            return
        self.nodes.add(name)
        for i in range(self.vnodes):
            self.ring.append((self._h(name + "#" + str(i)), name))
        self.ring.sort()
    def remove_node(self, name):
        self.nodes.discard(name)
        self.ring = [t for t in self.ring if t[1] != name]
    def get_node(self, key):
        import bisect
        if not self.ring:
            return None
        i = bisect.bisect_left(self.ring, (self._h(key), ""))
        return self.ring[min(i, len(self.ring) - 1)][1]
''',
        '''class HashRing:
    def __init__(self, vnodes):
        self.vnodes, self.ring, self.nodes = vnodes, [], set()
    @staticmethod
    def _h(s):
        h = 2166136261
        for c in s.encode("utf-8"):
            h ^= c
            h = (h * 16777619) % (1 << 32)
        return h
    def add_node(self, name):
        if name in self.nodes:
            return
        self.nodes.add(name)
        self.ring.append((self._h(name + "#0"), name))
        self.ring.sort()
    def remove_node(self, name):
        self.nodes.discard(name)
        self.ring = [t for t in self.ring if t[1] != name]
    def get_node(self, key):
        import bisect
        if not self.ring:
            return None
        i = bisect.bisect_left(self.ring, (self._h(key), ""))
        return self.ring[i % len(self.ring)][1]
''',
    ],
    guide=dict(
        prereqs="Hash functions, binary search on a sorted list. Lesson *Secondary indexes, rebalancing and request routing* (why `hash mod N` is a bad idea).",
        intuition="With `hash(key) % N`, changing N reshuffles nearly every key. Put nodes and keys on the same circle instead: a key belongs to the next node clockwise. Adding or removing a node then only affects the arcs next to its tokens. Virtual nodes give each machine many small arcs so load evens out.",
        hints=[
            "Keep one sorted list of `(token, node_name)` tuples.",
            "`bisect_left(ring, (hash, \"\"))` finds the first token at or after the key's position - the empty string sorts before every node name.",
            "If the index runs off the end, wrap to index 0 with `% len(ring)`.",
        ],
        brute_force="For each lookup scan all tokens for the smallest one that is >= the key's hash: O(T) per lookup for T tokens.",
        approach="1. FNV-1a helper over UTF-8 bytes.\n2. `add_node`: skip known names; insert `vnodes` tokens in sorted position.\n3. `remove_node`: filter the ring.\n4. `get_node`: empty → `None`; otherwise bisect and wrap.\n\nWhy the wrap matters: a key hashing above the largest token belongs to the node with the *smallest* token - the ring has no end.",
        complexity="`get_node` O(log T); `add_node` O(V * T) with list insertion (O(V log T) with a balanced tree); `remove_node` O(T). T = nodes * vnodes.",
        pitfalls="Using Python's `hash()` (salted per process - two servers would disagree on ownership); forgetting the wrap-around; hashing characters instead of bytes for non-ASCII names; adding a node twice and doubling its share.",
        follow_up="For replication, continue clockwise and collect the next N *distinct physical* nodes. Compare with the fixed-number-of-partitions approach, where the hash space is pre-cut into e.g. 1024 partitions and only whole partitions move between nodes.",
    ),
),
dict(
    id="db-mvcc-visibility",
    title="MVCC Snapshot Visibility",
    difficulty="Medium",
    pattern="Transactions",
    kind="function",
    entry="visible_rows",
    description=r"""
Under snapshot isolation implemented with multi-version concurrency control, every row version records
which transaction created it and which (if any) deleted it. An update is a delete plus a create.

`versions` is a list of `[row_id, value, created_by, deleted_by]`, where `deleted_by` is a transaction id or `None`.
A reading transaction has id `txid` and took its snapshot when the transactions in `active` were still in
progress. `aborted` lists transactions that rolled back. Transaction ids increase over time.

A transaction `t`'s effects are **visible** to the reader iff

- `t == txid` (a transaction sees its own writes), or
- `t < txid` and `t` is in neither `active` nor `aborted`.

A row version is visible iff its creator is visible **and** it has no deleter or its deleter is not visible.

Return `[row_id, value]` for every visible version, in input order.

**Example:** `versions = [[1, "old", 5, 8], [1, "new", 8, None]]`, `txid = 10`, `active = [8]`, `aborted = []`
→ `[[1, "old"]]` (transaction 8 had not committed when the snapshot was taken, so its delete and its insert are both ignored)
""",
    starter='''def visible_rows(versions: List[list], txid: int, active: List[int], aborted: List[int]) -> List[list]:
    pass
''',
    solution='''def visible_rows(versions, txid, active, aborted):
    hidden = set(active) | set(aborted)

    def sees(t):
        return t == txid or (t < txid and t not in hidden)

    out = []
    for row_id, value, created_by, deleted_by in versions:
        if sees(created_by) and (deleted_by is None or not sees(deleted_by)):
            out.append([row_id, value])
    return out
''',
    tests=[
        [[[1, "old", 5, 8], [1, "new", 8, None]], 10, [8], []],
        [[[1, "old", 5, 8], [1, "new", 8, None]], 10, [], []],
        [[[1, "old", 5, 8], [1, "new", 8, None]], 10, [], [8]],
        [[], 5, [], []],
        [[[1, "a", 3, None], [2, "b", 12, None]], 10, [], []],
        [[[1, "mine", 10, None], [2, "gone", 4, 10]], 10, [], []],
        [[[1, "a", 3, 12]], 10, [], []],
        [[[1, "a", 3, None]], 10, [3], []],
        [[[1, "a", 3, None]], 3, [], []],
        [[[1, "v1", 2, 4], [1, "v2", 4, 6], [1, "v3", 6, 9], [1, "v4", 9, None]], 7, [6], []],
        [[[1, "v1", 2, 4], [1, "v2", 4, 6], [1, "v3", 6, 9], [1, "v4", 9, None]], 20, [], [4, 9]],
        [[[7, "x", 1, 2], [8, "y", 2, None], [9, "z", 1, 5]], 6, [2], [5]],
        [[[i, i * i, i, (i + 7 if i % 3 == 0 else None)] for i in range(1, 400)], 300, list(range(250, 300, 4)), list(range(1, 250, 9))],
    ],
    examples=1,
    wrong_solutions=[
        '''def visible_rows(versions, txid, active, aborted):
    def sees(t):
        return t <= txid and t not in aborted
    return [[r, v] for r, v, c, d in versions if sees(c) and (d is None or not sees(d))]
''',
        '''def visible_rows(versions, txid, active, aborted):
    hidden = set(active) | set(aborted)
    def sees(t):
        return t == txid or (t < txid and t not in hidden)
    return [[r, v] for r, v, c, d in versions if sees(c) and d is None]
''',
        '''def visible_rows(versions, txid, active, aborted):
    hidden = set(active) | set(aborted)
    def sees(t):
        return t < txid and t not in hidden
    return [[r, v] for r, v, c, d in versions if sees(c) and (d is None or not sees(d))]
''',
        '''def visible_rows(versions, txid, active, aborted):
    hidden = set(active)
    def sees(t):
        return t == txid or (t < txid and t not in hidden)
    return [[r, v] for r, v, c, d in versions if sees(c) and (d is None or not sees(d))]
''',
    ],
    guide=dict(
        prereqs="Lesson *ACID, read committed and snapshot isolation* (the MVCC visibility rules).",
        intuition="A snapshot is not a copy of the data; it is a *rule* for deciding which versions to ignore. Reduce everything to one question - 'had transaction t committed when I started, or is it me?' - and ask it twice per version: once about the creator, once about the deleter.",
        hints=[
            "Write a helper `sees(t)`.",
            "A version whose creator you cannot see does not exist for you, whatever its deleter says.",
            "A version whose deleter you cannot see is still alive for you - this is how you keep reading the old value while someone else's update is in flight.",
        ],
        brute_force="There is no asymptotically worse sensible approach, but the common first attempt hard-codes cases (active creator, later creator, aborted deleter, ...) and misses one. The helper function collapses them.",
        approach="1. `hidden = set(active) | set(aborted)`.\n2. `sees(t) = (t == txid) or (t < txid and t not in hidden)`.\n3. Keep versions with `sees(created_by) and (deleted_by is None or not sees(deleted_by))`.\n\nDry run of the example: `old` was created by 5 (visible) and deleted by 8 (active → invisible) → still visible. `new` was created by 8 → invisible. The reader sees exactly one version of row 1.",
        complexity="O(n + |active| + |aborted|) time, O(|active| + |aborted|) extra space.",
        pitfalls="Forgetting that a transaction sees its own uncommitted writes and deletes; treating any non-null `deleted_by` as deleted; ignoring transactions with a larger id (they started after the snapshot even if they have already committed); forgetting aborted transactions.",
        follow_up="Old versions can be garbage-collected once no running snapshot can see them. Which single number does the vacuum process need to know? What does one long-running analytics transaction do to that number?",
    ),
),
dict(
    id="db-write-skew-detect",
    title="Detect Write Skew in a Schedule",
    difficulty="Medium",
    pattern="Transactions",
    kind="function",
    entry="find_write_skew",
    description=r"""
Snapshot isolation prevents lost updates on the *same* object but allows **write skew**: two concurrent
transactions each read something, then each update a *different* object, and the combination breaks an
invariant neither could have broken alone.

Each committed transaction is `[id, start, commit, reads, writes]` with integer times `start < commit` and
lists of keys read and written.

Report every pair of transactions `(A, B)` that forms a potential write skew:

1. they are **concurrent**: `A.start < B.commit` and `B.start < A.commit`;
2. their write sets are **disjoint** (otherwise first-committer-wins would have aborted one of them);
3. each one wrote a key that the other one read: `A.writes ∩ B.reads` and `B.writes ∩ A.reads` are both non-empty.

Return the pairs as `[smaller_id, larger_id]`, sorted ascending.

**Example (two doctors going off call):**
`[[1, 0, 10, ["alice", "bob"], ["alice"]], [2, 1, 11, ["alice", "bob"], ["bob"]]]` → `[[1, 2]]`
""",
    starter='''def find_write_skew(txns: List[list]) -> List[List[int]]:
    pass
''',
    solution='''def find_write_skew(txns):
    out = []
    n = len(txns)
    for i in range(n):
        ia, sa, ca, ra, wa = txns[i]
        ra, wa = set(ra), set(wa)
        for j in range(i + 1, n):
            ib, sb, cb, rb, wb = txns[j]
            rb, wb = set(rb), set(wb)
            if not (sa < cb and sb < ca):
                continue
            if wa & wb:
                continue
            if (wa & rb) and (wb & ra):
                out.append([min(ia, ib), max(ia, ib)])
    out.sort()
    return out
''',
    tests=[
        [[[1, 0, 10, ["alice", "bob"], ["alice"]], [2, 1, 11, ["alice", "bob"], ["bob"]]]],
        [[[1, 0, 5, ["alice", "bob"], ["alice"]], [2, 5, 9, ["alice", "bob"], ["bob"]]]],
        [[]],
        [[[1, 0, 10, ["x"], ["x"]]]],
        [[[1, 0, 10, ["x", "y"], ["x"]], [2, 1, 11, ["x", "y"], ["x"]]]],
        [[[1, 0, 10, ["x", "y"], ["x"]], [2, 1, 11, ["z"], ["y"]]]],
        [[[2, 0, 10, ["a", "b"], ["a"]], [1, 3, 4, ["a", "b"], ["b"]]]],
        [[[1, 0, 10, ["a", "b"], ["a"]], [2, 2, 12, ["a", "b"], ["b"]], [3, 4, 14, ["a", "b", "c"], ["c"]]]],
        [[[1, 0, 10, ["a", "b", "c"], ["a"]], [2, 2, 12, ["a", "b", "c"], ["b"]], [3, 4, 14, ["a", "b", "c"], ["c"]]]],
        [[[1, 0, 3, ["a", "b"], ["a"]], [2, 3, 6, ["a", "b"], ["b"]], [3, 2, 4, ["a", "b"], ["b"]]]],
        [[[1, 0, 10, [], ["a"]], [2, 1, 9, [], ["b"]]]],
        [[[1, 0, 10, ["a", "b"], ["a", "c"]], [2, 1, 9, ["a", "b"], ["b", "c"]]]],
        [_rand_txns(40)],
        [_rand_txns(60)],
    ],
    examples=2,
    wrong_solutions=[
        '''def find_write_skew(txns):
    out = []
    for i in range(len(txns)):
        for j in range(i + 1, len(txns)):
            a, b = txns[i], txns[j]
            if set(a[4]) & set(b[4]):
                continue
            if set(a[4]) & set(b[3]) and set(b[4]) & set(a[3]):
                out.append(sorted([a[0], b[0]]))
    return sorted(out)
''',
        '''def find_write_skew(txns):
    out = []
    for i in range(len(txns)):
        for j in range(i + 1, len(txns)):
            a, b = txns[i], txns[j]
            if not (a[1] < b[2] and b[1] < a[2]):
                continue
            if set(a[4]) & set(b[3]) and set(b[4]) & set(a[3]):
                out.append(sorted([a[0], b[0]]))
    return sorted(out)
''',
        '''def find_write_skew(txns):
    out = []
    for i in range(len(txns)):
        for j in range(i + 1, len(txns)):
            a, b = txns[i], txns[j]
            if not (a[1] < b[2] and b[1] < a[2]):
                continue
            if set(a[4]) & set(b[4]):
                continue
            if set(a[4]) & set(b[3]) or set(b[4]) & set(a[3]):
                out.append(sorted([a[0], b[0]]))
    return sorted(out)
''',
        '''def find_write_skew(txns):
    out = []
    for i in range(len(txns)):
        for j in range(i + 1, len(txns)):
            a, b = txns[i], txns[j]
            if not (a[1] < b[2] and b[1] < a[2]):
                continue
            if set(a[4]) & set(b[4]):
                continue
            if set(a[4]) & set(b[3]) and set(b[4]) & set(a[3]):
                out.append([a[0], b[0]])
    return sorted(out)
''',
    ],
    guide=dict(
        prereqs="Interval overlap, set intersection. Lessons *Lost updates, write skew and phantoms* and *Serializability* (SSI).",
        intuition="Each transaction made a decision based on a premise (what it read). Write skew is two concurrent transactions invalidating each other's premise: A wrote into what B read and B wrote into what A read, and neither could see it because both worked from snapshots.",
        hints=[
            "Two intervals overlap iff each starts before the other ends.",
            "Convert the read and write lists to sets once per transaction.",
            "You need the dependency in **both** directions. One direction only means the pair can still be ordered serially.",
        ],
        brute_force="Checking all pairs is already the straightforward solution, O(n^2) pairs. A production detector would index writes by key so it only examines transactions that touched related keys.",
        approach="For every pair i < j: overlap test → disjoint-writes test → mutual read/write intersection test → record `[min id, max id]`; sort at the end.\n\nDry run (doctors): both read `{alice, bob}`; T1 writes `alice`, T2 writes `bob`. Concurrent; writes disjoint; T1's write hits T2's read and vice versa → skew. In the second test T2 starts exactly when T1 commits, so T2's snapshot already contains T1's write: no anomaly.",
        complexity="O(n^2 * k) for n transactions with at most k keys each; O(k) extra space.",
        pitfalls="Treating `start == commit` of the other transaction as overlapping; forgetting to order the ids inside a pair; reporting write-write conflicts (those are lost-update candidates, which snapshot isolation already blocks).",
        follow_up="This pairwise rw-rw pattern is the simplest dangerous structure. Serializable snapshot isolation generalises it: it aborts a transaction that has both an incoming and an outgoing read-write dependency to concurrent transactions. Why can that abort transactions that were actually harmless?",
    ),
),
dict(
    id="db-fencing-token",
    title="Lock Service with Fencing Tokens",
    difficulty="Easy",
    pattern="Distributed Systems",
    kind="class",
    entry="FencedStore",
    description=r"""
A client that holds a lease may be paused (GC, VM migration) past the lease expiry and wake up still
believing it holds the lock. The cure is a **fencing token**: every time the lock is granted the lock
service hands out a strictly larger number, and the storage service refuses writes carrying a token older
than one it has already seen.

Implement `FencedStore`, which plays both roles:

- `acquire(client)` - grant the lock to `client` (taking it from whoever had it - assume the previous lease expired) and return a new token: 1, 2, 3, ...
- `write(token, key, value)` - accept the write and return `True` iff `token` was actually issued **and** is `>=` the highest token the store has accepted so far. Otherwise return `False` and change nothing.
- `read(key)` - current value or `None`.
- `holder()` - the client that most recently acquired the lock, or `None`.

Note that the store only learns about a token when a write carrying it arrives.

**Example:** `acquire("A")`→1, `acquire("B")`→2, `write(2,"f","b")`→True, `write(1,"f","a")`→False, `read("f")`→`"b"`
""",
    starter='''class FencedStore:
    def __init__(self):
        pass

    def acquire(self, client: str) -> int:
        pass

    def write(self, token: int, key: str, value) -> bool:
        pass

    def read(self, key: str):
        pass

    def holder(self) -> Optional[str]:
        pass
''',
    solution='''class FencedStore:
    def __init__(self):
        self.issued = 0
        self.max_seen = 0
        self.data = {}
        self.owner = None

    def acquire(self, client):
        self.issued += 1
        self.owner = client
        return self.issued

    def write(self, token, key, value):
        if token < 1 or token > self.issued or token < self.max_seen:
            return False
        self.max_seen = token
        self.data[key] = value
        return True

    def read(self, key):
        return self.data.get(key)

    def holder(self):
        return self.owner
''',
    tests=[
        [["FencedStore", "acquire", "acquire", "write", "write", "read"], [[], ["A"], ["B"], [2, "f", "b"], [1, "f", "a"], ["f"]]],
        [["FencedStore", "holder", "read", "write", "read"], [[], [], ["k"], [1, "k", "v"], ["k"]]],
        [["FencedStore", "acquire", "write", "write", "read", "holder"], [[], ["A"], [1, "k", 1], [1, "k", 2], ["k"], []]],
        [["FencedStore", "acquire", "acquire", "write", "write", "read", "holder"],
         [[], ["A"], ["B"], [1, "k", "from-A"], [2, "k", "from-B"], ["k"], []]],
        [["FencedStore", "acquire", "acquire", "write", "write", "write", "read", "read"],
         [[], ["A"], ["B"], [1, "x", "a1"], [2, "y", "b1"], [1, "x", "a2"], ["x"], ["y"]]],
        [["FencedStore", "acquire", "write", "write", "write", "read"], [[], ["A"], [0, "k", "zero"], [5, "k", "forged"], [-1, "k", "neg"], ["k"]]],
        [["FencedStore", "acquire", "acquire", "acquire", "write", "write", "write", "read", "holder"],
         [[], ["A"], ["B"], ["A"], [3, "k", "A-new"], [2, "k", "B"], [1, "k", "A-old"], ["k"], []]],
        [["FencedStore", "acquire", "write", "acquire", "write", "write", "read"],
         [[], ["A"], [1, "k", "v1"], ["B"], [1, "k", "v2"], [2, "k", "v3"], ["k"]]],
        [["FencedStore"] + ["acquire"] * 50 + ["write"] * 50 + ["read"],
         [[]] + [["c%d" % i] for i in range(50)] + [[(i * 7) % 50 + 1, "k", i] for i in range(50)] + [["k"]]],
        [["FencedStore", "acquire", "write", "read", "read"], [[], ["A"], [1, "zero", 0], ["zero"], ["missing"]]],
    ],
    examples=1,
    wrong_solutions=[
        '''class FencedStore:
    def __init__(self):
        self.n, self.data, self.owner = 0, {}, None
    def acquire(self, client):
        self.n += 1; self.owner = client
        return self.n
    def write(self, token, key, value):
        self.data[key] = value
        return True
    def read(self, key):
        return self.data.get(key)
    def holder(self):
        return self.owner
''',
        '''class FencedStore:
    def __init__(self):
        self.n, self.data, self.owner = 0, {}, None
    def acquire(self, client):
        self.n += 1; self.owner = client
        return self.n
    def write(self, token, key, value):
        if token != self.n:
            return False
        self.data[key] = value
        return True
    def read(self, key):
        return self.data.get(key)
    def holder(self):
        return self.owner
''',
        '''class FencedStore:
    def __init__(self):
        self.n, self.mx, self.data, self.owner = 0, 0, {}, None
    def acquire(self, client):
        self.n += 1; self.owner = client
        return self.n
    def write(self, token, key, value):
        if token <= self.mx:
            return False
        self.mx = token
        self.data[key] = value
        return True
    def read(self, key):
        return self.data.get(key)
    def holder(self):
        return self.owner
''',
        '''class FencedStore:
    def __init__(self):
        self.n, self.mx, self.data, self.owner = 0, 0, {}, None
    def acquire(self, client):
        self.n += 1; self.owner = client
        return self.n
    def write(self, token, key, value):
        if token < self.mx:
            return False
        self.mx = token
        self.data[key] = value
        return True
    def read(self, key):
        return self.data.get(key)
    def holder(self):
        return self.owner
''',
    ],
    guide=dict(
        prereqs="Lesson *Truth, majorities, fencing tokens and Byzantine faults*.",
        intuition="A node cannot trust its own belief that it still holds a lock, because it cannot notice that it was frozen. So the check must be made by the resource being protected: it remembers the newest token it has honoured and turns older ones away.",
        hints=[
            "Two counters: tokens issued so far, and the highest token the store has accepted.",
            "The same token may write repeatedly - the comparison is `>=`, not `>`.",
            "The store does not consult the lock service about who the current holder is; a stale token is only rejected after a newer one has *written*.",
        ],
        brute_force="Asking the lock service 'is this client still the holder?' before each write looks simpler but is racy: the answer can go stale between the check and the write. The token comparison at the storage layer has no such gap.",
        approach="`acquire`: increment, remember owner, return the counter.\n`write`: reject forged (`token > issued` or `< 1`) and stale (`token < max_seen`) tokens; otherwise raise `max_seen` and store.\n\nDry run: A gets 1, pauses. B gets 2 and writes → `max_seen = 2`. A wakes and writes with 1 → `1 < 2` → rejected. The zombie is fenced off.",
        complexity="O(1) per operation; O(keys) space.",
        pitfalls="Rejecting equal tokens (the legitimate holder could then write only once); comparing against the latest *issued* token instead of the highest *seen* (a legitimate design choice in some systems, but not the mechanism described here, and impossible when the lock service and the store are different machines); accepting tokens that were never issued.",
        follow_up="Where do monotonically increasing tokens come from in practice? ZooKeeper's `zxid` or a znode version, an etcd revision, or the term number of a consensus leader. What breaks if the client *lies* about its token?",
    ),
),
]
