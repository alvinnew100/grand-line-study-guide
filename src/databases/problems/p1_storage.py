"""Problems for modules 1 and 3: percentiles, log-structured storage, Bloom filters, B-tree splits."""
import random as _r

_rng = _r.Random(7)

PROBLEMS = [
dict(
    id="db-percentiles",
    title="Response-Time Percentiles",
    difficulty="Easy",
    pattern="Sorting & Statistics",
    kind="function",
    entry="percentile_report",
    description=r"""
A latency dashboard needs percentiles, not averages. Given a list of response times `latencies`
(numbers, in any order) and a list of percentiles `ps` (integers from 0 to 100), return the list of
percentile values in the same order as `ps`, using the **nearest-rank** definition:

- sort the samples ascending;
- the p-th percentile is the sample at 1-based rank `ceil(p / 100 * n)`;
- rank 0 (only possible for `p = 0`) is treated as rank 1, i.e. the minimum.

If `latencies` is empty, return an empty list.

**Example:** `latencies = [30, 10, 20, 40]`, `ps = [50, 75, 100]` → `[20, 30, 40]`

**Example:** `latencies = [5]`, `ps = [0, 99]` → `[5, 5]`
""",
    starter='''def percentile_report(latencies: List[float], ps: List[int]) -> List[float]:
    pass
''',
    solution='''def percentile_report(latencies, ps):
    if not latencies:
        return []
    xs = sorted(latencies)
    n = len(xs)
    out = []
    for p in ps:
        rank = -(-p * n // 100)          # ceil(p*n/100) using integer maths
        out.append(xs[max(rank, 1) - 1])
    return out
''',
    tests=[
        [[30, 10, 20, 40], [50, 75, 100]],
        [[5], [0, 99]],
        [[], [50, 99]],
        [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [0, 10, 50, 90, 95, 99, 100]],
        [[100, 1, 1, 1, 1, 1, 1, 1, 1, 1], [50, 90, 91, 99]],
        [[3, 3, 3], [1, 50, 100]],
        [[2.5, 0.5, 1.5], [33, 34, 67]],
        [list(range(1, 101)), [1, 50, 95, 99, 100]],
        [list(range(1000, 0, -1)), [50, 99, 100]],
        [[_rng.randint(1, 5000) for _ in range(5000)], [50, 90, 95, 99, 100]],
        [[7, 9], []],
    ],
    examples=2,
    wrong_solutions=[
        '''def percentile_report(latencies, ps):
    if not latencies:
        return []
    xs = sorted(latencies)
    return [xs[min(len(xs) - 1, p * len(xs) // 100)] for p in ps]
''',
        '''def percentile_report(latencies, ps):
    if not latencies:
        return []
    n = len(latencies)
    return [latencies[max(-(-p * n // 100), 1) - 1] for p in ps]
''',
    ],
    guide=dict(
        prereqs="Sorting, integer ceiling division. See the lesson *Scalability: load parameters, percentiles and SLOs*.",
        intuition="A percentile answers: *what value is at least as large as p percent of my samples?* Once the samples are sorted, that is just an index computation.",
        hints=[
            "Sort a copy of the data once, then answer every percentile from it.",
            "The rank is `ceil(p/100 * n)`. Avoid floats: `-(-p*n // 100)` is an exact integer ceiling.",
            "Ranks are 1-based, lists are 0-based, and p = 0 would give rank 0 - clamp it to 1.",
        ],
        brute_force="For every percentile, count for each sample how many samples are <= it and pick the smallest sample covering p percent: O(n^2) per query.",
        approach="Sort once. For each `p`: `rank = ceil(p*n/100)`, clamp to at least 1, return `xs[rank-1]`. Dry run on `[10,20,30,40]`, p=75: rank = ceil(3.0) = 3 → `xs[2] = 30`.",
        complexity="Time O(n log n + q) for q percentiles, space O(n) for the sorted copy.",
        pitfalls="Floating-point `math.ceil(0.07*100)` style errors (0.07*100 is 7.000000000000001); off-by-one between rank and index; forgetting to sort; mutating the caller's list.",
        follow_up="Real monitoring systems cannot keep every sample. Look at t-digest and HdrHistogram, which approximate percentiles in bounded memory and - unlike averages of percentiles - can be merged across machines.",
    ),
),
dict(
    id="db-append-log-kv",
    title="Append-Only Log KV Store with Hash Index",
    difficulty="Medium",
    pattern="Storage Engines",
    kind="class",
    entry="LogKV",
    description=r"""
Build the simplest useful storage engine: an **append-only log** plus an in-memory **hash index**
that maps each key to the position of its latest record (the Bitcask design).

Implement class `LogKV`:

- `set(key, value)` - append a record to the log and return its **offset** (0-based position in the log).
- `get(key)` - return the latest value, or `None` if the key is missing or deleted. Must use the index, not scan the log.
- `delete(key)` - if the key is currently live, append a **tombstone** record and return `True`; otherwise return `False` and append nothing.
- `log_size()` - number of records currently in the log (values and tombstones).
- `compact()` - rewrite the log so it contains only the latest record of each live key, in the order
  those latest records appeared in the old log; drop tombstones and overwritten records; rebuild the index.
  Return the number of records removed.

**Example:**
`set("a",1)`→0, `set("b",2)`→1, `set("a",3)`→2, `delete("b")`→True, `log_size()`→4,
`compact()`→3, `log_size()`→1, `get("a")`→3, `set("c",9)`→1
""",
    starter='''class LogKV:
    def __init__(self):
        pass

    def set(self, key: str, value) -> int:
        pass

    def get(self, key: str):
        pass

    def delete(self, key: str) -> bool:
        pass

    def log_size(self) -> int:
        pass

    def compact(self) -> int:
        pass
''',
    solution='''class LogKV:
    _TOMB = object()

    def __init__(self):
        self.log = []          # list of (key, value-or-tombstone)
        self.index = {}        # key -> offset of latest live record

    def set(self, key, value):
        self.log.append((key, value))
        self.index[key] = len(self.log) - 1
        return len(self.log) - 1

    def get(self, key):
        off = self.index.get(key)
        return None if off is None else self.log[off][1]

    def delete(self, key):
        if key not in self.index:
            return False
        self.log.append((key, LogKV._TOMB))
        del self.index[key]
        return True

    def log_size(self):
        return len(self.log)

    def compact(self):
        old = len(self.log)
        live = sorted(self.index.values())
        new_log = [self.log[off] for off in live]
        self.log = new_log
        self.index = {k: i for i, (k, _) in enumerate(new_log)}
        return old - len(new_log)
''',
    tests=[
        [["LogKV", "set", "set", "set", "delete", "log_size", "compact", "log_size", "get", "set"],
         [[], ["a", 1], ["b", 2], ["a", 3], ["b"], [], [], [], ["a"], ["c", 9]]],
        [["LogKV", "get", "delete", "log_size", "compact"], [[], ["x"], ["x"], [], []]],
        [["LogKV", "set", "get", "set", "get", "log_size"], [[], ["k", "v1"], ["k"], ["k", "v2"], ["k"], []]],
        [["LogKV", "set", "delete", "delete", "get", "log_size", "set", "get", "log_size"],
         [[], ["k", 1], ["k"], ["k"], ["k"], [], ["k", 2], ["k"], []]],
        [["LogKV", "set", "set", "set", "set", "compact", "set", "get", "get", "get", "log_size"],
         [[], ["b", 1], ["a", 2], ["b", 3], ["c", 4], [], ["d", 5], ["a"], ["b"], ["c"], []]],
        [["LogKV", "set", "set", "set", "compact", "delete", "compact", "log_size", "get", "get"],
         [[], ["x", 1], ["y", 2], ["x", 3], [], ["y"], [], [], ["x"], ["y"]]],
        [["LogKV", "set", "delete", "compact", "log_size", "get", "set", "get"],
         [[], ["only", 1], ["only"], [], [], ["only"], ["only", 2], ["only"]]],
        [["LogKV", "set", "set", "get", "get"], [[], ["zero", 0], ["empty", ""], ["zero"], ["empty"]]],
        [["LogKV"] + ["set"] * 300 + ["log_size", "compact", "log_size", "get", "get", "set"],
         [[]] + [["k%d" % (i % 7), i] for i in range(300)] + [[], [], [], ["k0"], ["k6"], ["new", 1]]],
        [["LogKV", "set", "set", "set", "delete", "set", "compact", "get", "get", "get", "set", "delete", "log_size"],
         [[], ["a", 1], ["b", 2], ["c", 3], ["a"], ["a", 4], [], ["a"], ["b"], ["c"], ["b", 5], ["c"], []]],
    ],
    examples=1,
    wrong_solutions=[
        '''class LogKV:
    def __init__(self):
        self.d = {}
        self.n = 0
    def set(self, key, value):
        self.d[key] = value
        self.n += 1
        return self.n - 1
    def get(self, key):
        return self.d.get(key)
    def delete(self, key):
        return self.d.pop(key, None) is not None
    def log_size(self):
        return self.n
    def compact(self):
        removed = self.n - len(self.d)
        self.n = len(self.d)
        return removed
''',
        '''class LogKV:
    def __init__(self):
        self.log = []
        self.index = {}
    def set(self, key, value):
        self.log.append((key, value))
        self.index[key] = len(self.log) - 1
        return len(self.log) - 1
    def get(self, key):
        off = self.index.get(key)
        return None if off is None else self.log[off][1]
    def delete(self, key):
        if key not in self.index:
            return False
        self.log.append((key, None))
        del self.index[key]
        return True
    def log_size(self):
        return len(self.log)
    def compact(self):
        old = len(self.log)
        self.log = [(k, self.log[o][1]) for k, o in self.index.items()]
        return old - len(self.log)
''',
    ],
    guide=dict(
        prereqs="Python lists and dicts. Lesson *Log-structured storage: hash indexes, SSTables, LSM-trees*.",
        intuition="Writes are cheap if you only ever append. Reads are cheap if you remember, per key, where its newest record sits. Deletes are just a special record, and compaction is the garbage collector that throws away everything the index no longer points at.",
        hints=[
            "Keep `self.log` as a list of `(key, value)` records and `self.index` as `key -> offset`.",
            "A delete must be *recorded* (tombstone) so that a crash-recovery scan of the log would not resurrect the key. Remove the key from the index too.",
            "For compaction, the live offsets are exactly `self.index.values()`. Sort them, copy those records to a new log, and rebuild the index from the new positions.",
        ],
        brute_force="No index: `get` scans the log backwards for the key - O(n) per read. Correct but unusable once the log is large.",
        approach="1. `set`: append, store offset in index, return it.\n2. `get`: one dict lookup, one list access.\n3. `delete`: only when live; append tombstone; drop from index.\n4. `compact`: `live = sorted(index.values())`; new log = those records; index = positions in the new log.\n\nDry run from the example: log = [a1, b2, a3, b-tombstone]; index = {a: 2}. Compaction keeps offset 2 only → log = [a3], removed 3.",
        complexity="`set`/`get`/`delete` O(1) average. `compact` O(L log L) in live keys (the sort) plus O(L) copying. Space: the log plus one index entry per live key - the index must fit in memory, which is the real-world limit of this design.",
        pitfalls="Storing `None` as the tombstone and then confusing it with a legitimately stored `None`/`0`/`\"\"`; forgetting to rebuild offsets after compaction (stale offsets then point at the wrong records); deleting a missing key and still appending a record.",
        follow_up="Real engines split the log into segments, compact segments in the background while serving reads from the old ones, and add checksums per record so that a half-written tail can be detected after a crash. How would you rebuild the index after a restart?",
    ),
),
dict(
    id="db-sstable-merge",
    title="SSTable Merge and Compaction",
    difficulty="Medium",
    pattern="Storage Engines",
    kind="function",
    entry="merge_sstables",
    description=r"""
An LSM-tree periodically merges several sorted segment files (SSTables) into one.

`tables` is a list of SSTables ordered **from oldest to newest**. Each SSTable is a list of
`[key, value]` pairs sorted by key, with unique keys inside one table. A value of `None` is a
**tombstone** (the key was deleted).

Return one merged SSTable (list of `[key, value]`, sorted by key) such that:

- when a key occurs in several tables, the entry from the **newest** table wins;
- because this is a full compaction of all segments, keys whose winning entry is a tombstone are dropped.

**Example:**
`tables = [[["a",1],["c",3]], [["b",2],["c",30]], [["a",None]]]` → `[["b",2],["c",30]]`
""",
    starter='''def merge_sstables(tables: List[List[list]]) -> List[list]:
    pass
''',
    solution='''def merge_sstables(tables):
    import heapq
    heap = []
    for age, t in enumerate(tables):
        if t:
            # newer tables get a smaller tiebreak so they pop first for equal keys
            heapq.heappush(heap, (t[0][0], -age, 0))
    out = []
    last = object()
    while heap:
        key, neg_age, i = heapq.heappop(heap)
        t = tables[-neg_age]
        if key != last:
            last = key
            if t[i][1] is not None:
                out.append([key, t[i][1]])
        if i + 1 < len(t):
            heapq.heappush(heap, (t[i + 1][0], neg_age, i + 1))
    return out
''',
    tests=[
        [[[["a", 1], ["c", 3]], [["b", 2], ["c", 30]], [["a", None]]]],
        [[]],
        [[[]]],
        [[[["k", 1]]]],
        [[[["k", None]]]],
        [[[["a", 1], ["b", 2]], [["c", 3], ["d", 4]]]],
        [[[["a", None]], [["a", 5]]]],
        [[[["a", 5]], [["a", None]], [["b", 1]]]],
        [[[["a", 1], ["b", 1], ["c", 1]], [["a", 2], ["b", 2]], [["a", 3]]]],
        [[[], [["x", 1], ["z", 2]], [], [["y", 0], ["z", None]]]],
        [[[[1, "one"], [5, "five"], [9, "nine"]], [[2, "two"], [5, None]], [[5, "FIVE"], [10, "ten"]]]],
        [[[[i, i] for i in range(0, 3000, 2)], [[i, -i] for i in range(0, 3000, 3)], [[i, None] for i in range(0, 3000, 5)]]],
        [[[["a", 0], ["b", ""]], [["c", False]]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def merge_sstables(tables):
    d = {}
    for t in tables:
        for k, v in t:
            d.setdefault(k, v)
    return [[k, d[k]] for k in sorted(d) if d[k] is not None]
''',
        '''def merge_sstables(tables):
    d = {}
    for t in tables:
        for k, v in t:
            d[k] = v
    return [[k, d[k]] for k in sorted(d)]
''',
        '''def merge_sstables(tables):
    d = {}
    for t in tables:
        for k, v in t:
            if v is not None:
                d[k] = v
    return [[k, d[k]] for k in sorted(d)]
''',
    ],
    guide=dict(
        prereqs="Merge step of mergesort, heaps (`heapq`). Lesson *Log-structured storage*.",
        intuition="Every input is already sorted, so you never need to look further than the head of each table. Repeatedly take the smallest head; if several tables share that key, trust the newest and skip the rest.",
        hints=[
            "A dict-then-sort solution is accepted, but try the streaming version: it is what lets real engines merge files far larger than RAM.",
            "Push `(key, -table_age, position)` on a heap. With that tiebreak the newest copy of a key is popped first.",
            "Remember the last key you emitted (or skipped as a tombstone) and ignore further pops with the same key.",
        ],
        brute_force="Load everything into a dict from oldest to newest so later writes overwrite earlier ones, drop `None`s, sort the keys: O(N log N) time and O(N) memory - fine for a toy, impossible for 100 GB of segments.",
        approach="K-way merge. Heap holds one cursor per table. Pop the smallest `(key, -age)`. If the key differs from the previous key, this is the winning version: emit it unless it is a tombstone. Either way advance that table's cursor. Dry run on the example: pops are a (newest, tombstone → skip), a (old → same key, ignore), b → emit, c (age 1 → emit 30), c (age 0 → ignore).",
        complexity="Time O(N log k) for N total entries in k tables; extra space O(k) besides the output.",
        pitfalls="Letting the oldest value win; emitting the older value after skipping a tombstone (track the last key even when you emit nothing); using truthiness (`if v:`) and thereby deleting legitimate values such as `0` or `\"\"`.",
        follow_up="Tombstones may only be dropped when the merge includes the *oldest* segment that could hold the key. Why would a partial compaction that discards tombstones bring deleted data back to life?",
    ),
),
dict(
    id="db-bloom-filter",
    title="Bloom Filter",
    difficulty="Medium",
    pattern="Probabilistic Data Structures",
    kind="class",
    entry="BloomFilter",
    description=r"""
LSM-tree engines keep a Bloom filter per SSTable so that lookups for keys that do not exist can skip the file.

Implement `BloomFilter(m, k)` with `m` bits and `k` hash functions. To keep results deterministic,
derive the hash functions from two string hashes (double hashing):

```
h1 = 7;  for each character c of key: h1 = (h1 * 31  + ord(c)) % 1000000007
h2 = 0;  for each character c of key: h2 = (h2 * 131 + ord(c)) % 998244353
position_i = (h1 + i * (h2 + 1)) % m      for i = 0 .. k-1
```

Methods:

- `add(key)` - set the `k` bits for `key` (returns nothing).
- `might_contain(key)` - `True` if all `k` bits are set (possibly a false positive), `False` if the key was definitely never added.
- `bits_set()` - how many of the `m` bits are currently 1.

**Example:** `BloomFilter(64, 3)`, `add("cat")`, `might_contain("cat")` → `True`, `might_contain("dog")` → `False`, `bits_set()` → `3`
""",
    starter='''class BloomFilter:
    def __init__(self, m: int, k: int):
        pass

    def add(self, key: str) -> None:
        pass

    def might_contain(self, key: str) -> bool:
        pass

    def bits_set(self) -> int:
        pass
''',
    solution='''class BloomFilter:
    def __init__(self, m, k):
        self.m, self.k = m, k
        self.bits = [0] * m

    def _positions(self, key):
        h1, h2 = 7, 0
        for c in key:
            h1 = (h1 * 31 + ord(c)) % 1000000007
            h2 = (h2 * 131 + ord(c)) % 998244353
        return [(h1 + i * (h2 + 1)) % self.m for i in range(self.k)]

    def add(self, key):
        for p in self._positions(key):
            self.bits[p] = 1

    def might_contain(self, key):
        return all(self.bits[p] for p in self._positions(key))

    def bits_set(self):
        return sum(self.bits)
''',
    tests=[
        [["BloomFilter", "add", "might_contain", "might_contain", "bits_set"], [[64, 3], ["cat"], ["cat"], ["dog"], []]],
        [["BloomFilter", "might_contain", "bits_set"], [[16, 2], ["anything"], []]],
        [["BloomFilter", "add", "add", "bits_set", "might_contain"], [[32, 4], ["x"], ["x"], [], ["x"]]],
        [["BloomFilter", "add", "might_contain", "bits_set"], [[1, 5], ["a"], ["zzz"], []]],
        [["BloomFilter", "add", "might_contain", "might_contain", "bits_set"], [[1000, 1], [""], [""], ["a"], []]],
        [["BloomFilter"] + ["add"] * 6 + ["might_contain"] * 10 + ["bits_set"],
         [[20, 3]] + [[w] for w in ["apple", "pear", "plum", "fig", "kiwi", "lime"]]
         + [[w] for w in ["apple", "lime", "grape", "melon", "peach", "mango", "date", "yuzu", "nut", "bean"]] + [[]]],
        [["BloomFilter"] + ["add"] * 50 + ["bits_set"] + ["might_contain"] * 60,
         [[256, 4]] + [["user:%d" % i] for i in range(50)] + [[]] + [["user:%d" % i] for i in range(20, 80)]],
        [["BloomFilter"] + ["add"] * 200 + ["bits_set"] + ["might_contain"] * 100,
         [[4096, 7]] + [["key-%d" % (i * 37)] for i in range(200)] + [[]] + [["probe-%d" % i] for i in range(100)]],
        [["BloomFilter"] + ["add"] * 30 + ["bits_set"] + ["might_contain"] * 40,
         [[40, 2]] + [["w%d" % i] for i in range(30)] + [[]] + [["q%d" % i] for i in range(40)]],
        [["BloomFilter", "add", "add", "might_contain", "might_contain", "might_contain", "bits_set"],
         [[97, 5], ["ab"], ["ba"], ["ab"], ["ba"], ["aa"], []]],
    ],
    examples=1,
    wrong_solutions=[
        '''class BloomFilter:
    def __init__(self, m, k):
        self.m, self.k, self.bits = m, k, [0] * m
    def _h(self, key):
        h1 = 7
        for c in key:
            h1 = (h1 * 31 + ord(c)) % 1000000007
        return h1 % self.m
    def add(self, key):
        self.bits[self._h(key)] = 1
    def might_contain(self, key):
        return self.bits[self._h(key)] == 1
    def bits_set(self):
        return sum(self.bits)
''',
        '''class BloomFilter:
    def __init__(self, m, k):
        self.m, self.k, self.bits = m, k, [0] * m
    def _positions(self, key):
        h1, h2 = 7, 0
        for c in key:
            h1 = (h1 * 31 + ord(c)) % 1000000007
            h2 = (h2 * 131 + ord(c)) % 998244353
        return [(h1 + i * (h2 + 1)) % self.m for i in range(self.k)]
    def add(self, key):
        for p in self._positions(key):
            self.bits[p] = 1
    def might_contain(self, key):
        return any(self.bits[p] for p in self._positions(key))
    def bits_set(self):
        return sum(self.bits)
''',
        '''class BloomFilter:
    def __init__(self, m, k):
        self.s = set()
        self.k = k
    def add(self, key):
        self.s.add(key)
    def might_contain(self, key):
        return key in self.s
    def bits_set(self):
        return len(self.s) * self.k
''',
    ],
    guide=dict(
        prereqs="Bit arrays, modular hashing. Lesson *Log-structured storage* (Bloom filters section).",
        intuition="Each key leaves `k` fingerprints in a shared bit array. If any fingerprint of a queried key is missing, the key cannot have been added. If all are present, they may have been left by other keys - hence *might* contain.",
        hints=[
            "Write one helper that returns the `k` positions for a key; `add` and `might_contain` both use it.",
            "Compute `h1` and `h2` in a single pass over the characters, exactly as specified (Python's built-in `hash` is randomised per process for strings).",
            "`might_contain` needs **all** positions set - `any` gives a filter that says yes far too often.",
        ],
        brute_force="Store every key in a set: exact answers, but memory grows with the total key bytes. The entire point of the filter is roughly 10 bits per key regardless of key length.",
        approach="1. Allocate `m` zero bits.\n2. `_positions(key)`: fold the characters into `h1`, `h2`; return `(h1 + i*(h2+1)) % m` for `i < k`.\n3. `add`: set those bits. `might_contain`: check them all. `bits_set`: sum.\n\nThe `+1` on `h2` guarantees a non-zero step so the `k` probes do not all collapse onto one bit when `h2 = 0`.",
        complexity="`add` and `might_contain`: O(len(key) + k). `bits_set`: O(m) (or O(1) if you keep a counter). Space: m bits.",
        pitfalls="Using `hash()`; treating a positive answer as certain; expecting to delete (clearing bits would create false negatives for other keys - you need a counting Bloom filter).",
        follow_up="With n keys the false-positive rate is about $(1-e^{-kn/m})^k$, minimised at $k = (m/n)\\ln 2$. Compute the rate for the 30-keys-in-40-bits test and see why that test produces many false positives.",
    ),
),
dict(
    id="db-btree-split",
    title="B+-Tree Leaf Insert and Split",
    difficulty="Easy",
    pattern="Storage Engines",
    kind="function",
    entry="split_leaf",
    description=r"""
A B+-tree leaf page holds at most `capacity` sorted keys. Insert `new_key` into the sorted list `keys`
and report what the tree must do.

Return `[left, right, separator]`:

- If `new_key` is already present, nothing changes: return `[keys, [], None]`.
- If the page still fits after the insert (`len <= capacity`): return `[keys_with_new_key, [], None]`.
- Otherwise the page **splits**: with `n` keys after the insert, the left page keeps the first `n // 2` keys,
  the right page gets the rest, and `separator` is the smallest key of the right page (it is *copied* up to the parent).

Do not mutate the input list.

**Example:** `keys = [10, 20, 30, 40], new_key = 25, capacity = 4` → `[[10, 20], [25, 30, 40], 25]`

**Example:** `keys = [10, 20], new_key = 5, capacity = 4` → `[[5, 10, 20], [], None]`
""",
    starter='''def split_leaf(keys: List[int], new_key: int, capacity: int) -> list:
    pass
''',
    solution='''def split_leaf(keys, new_key, capacity):
    import bisect
    i = bisect.bisect_left(keys, new_key)
    if i < len(keys) and keys[i] == new_key:
        return [list(keys), [], None]
    merged = keys[:i] + [new_key] + keys[i:]
    if len(merged) <= capacity:
        return [merged, [], None]
    mid = len(merged) // 2
    return [merged[:mid], merged[mid:], merged[mid]]
''',
    tests=[
        [[10, 20, 30, 40], 25, 4],
        [[10, 20], 5, 4],
        [[], 7, 4],
        [[10, 20, 30, 40], 30, 4],
        [[10, 20, 30, 40], 50, 4],
        [[10, 20, 30, 40], 1, 4],
        [[1, 2, 3], 4, 3],
        [[5], 3, 1],
        [[5], 9, 1],
        [[2, 4, 6, 8, 10], 7, 5],
        [[2, 4, 6, 8, 10], 7, 6],
        [list(range(0, 2000, 2)), 999, 1000],
        [[-5, -3, 0], -4, 3],
    ],
    examples=2,
    wrong_solutions=[
        '''def split_leaf(keys, new_key, capacity):
    merged = sorted(set(keys + [new_key]))
    if len(merged) <= capacity:
        return [merged, [], None]
    mid = len(merged) // 2
    return [merged[:mid], merged[mid:], merged[mid - 1]]
''',
        '''def split_leaf(keys, new_key, capacity):
    merged = sorted(set(keys + [new_key]))
    if len(merged) <= capacity:
        return [merged, [], None]
    mid = (len(merged) + 1) // 2
    return [merged[:mid], merged[mid:], merged[mid]]
''',
        '''def split_leaf(keys, new_key, capacity):
    merged = sorted(keys + [new_key])
    if len(merged) <= capacity:
        return [merged, [], None]
    mid = len(merged) // 2
    return [merged[:mid], merged[mid:], merged[mid]]
''',
    ],
    guide=dict(
        prereqs="Binary search (`bisect`). Lesson *B-trees, write-ahead logs and the LSM vs B-tree trade-off*.",
        intuition="A B-tree grows by splitting full pages in half and telling the parent where the boundary now lies. In a B+-tree all data stays in the leaves, so the boundary key is copied upward, not moved.",
        hints=[
            "Find the insertion point with `bisect_left`; if the key at that position equals `new_key`, it is a duplicate.",
            "Build a new list rather than calling `keys.insert` - the caller's page must not change.",
            "After an overflow there are `capacity + 1` keys. Left gets `n // 2`, right the remainder, separator is `right[0]`.",
        ],
        brute_force="Append, sort, deduplicate: O(n log n). Works, but a real page is already sorted and a binary search plus one shift is all that is needed.",
        approach="1. `i = bisect_left(keys, new_key)`; duplicate check.\n2. `merged = keys[:i] + [new_key] + keys[i:]`.\n3. Fits → `[merged, [], None]`.\n4. Else `mid = len(merged)//2` → `[merged[:mid], merged[mid:], merged[mid]]`.\n\nDry run: `[10,20,30,40] + 25`, capacity 4 → merged has 5 keys, mid = 2 → left `[10,20]`, right `[25,30,40]`, separator 25.",
        complexity="O(log n) to locate plus O(n) to copy the page; space O(n).",
        pitfalls="Returning `left[-1]` as separator (lookups for the separator key would then be routed to the wrong page under the usual `key >= separator goes right` rule); inserting duplicates; mutating the argument.",
        follow_up="Splits can cascade: the parent receives the separator and may overflow too, all the way to the root - which is the only way a B-tree gets taller. A split touches several pages, which is why a write-ahead log is needed to survive a crash mid-split.",
    ),
),
]
