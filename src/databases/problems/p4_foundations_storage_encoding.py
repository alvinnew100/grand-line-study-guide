"""Beginner-friendly simulations for modules 1-5: error budgets, graph traversal, WAL replay,
bitmap run-length encoding, varints, schema resolution and sibling versions."""
import random as _r

_rng = _r.Random(11)


def _intervals(n, span):
    out = []
    for _ in range(n):
        a = _rng.randint(0, span - 50)
        out.append([a, a + _rng.randint(0, 40)])
    return out


def _wal(n_tx, n_keys):
    log, open_tx = [], []
    for t in range(n_tx):
        tx = "t%d" % t
        log.append(["begin", tx])
        open_tx.append(tx)
        for _ in range(_rng.randint(1, 4)):
            key = "k%d" % _rng.randrange(n_keys)
            if _rng.random() < 0.2:
                log.append(["delete", tx, key])
            else:
                log.append(["set", tx, key, _rng.randint(0, 999)])
        if len(open_tx) > 2 or _rng.random() < 0.5:
            done = open_tx.pop(_rng.randrange(len(open_tx)))
            log.append([_rng.choice(["commit", "commit", "abort"]), done])
    return log


PROBLEMS = [
dict(
    id="db-error-budget",
    title="Error Budget Remaining",
    difficulty="Easy",
    pattern="Intervals",
    kind="function",
    entry="error_budget_left",
    compare="float",
    description=r"""
A service promises an availability target (an **SLO**), for example 99.9% over a 30-day period.
The time it is *allowed* to be down is its **error budget**:

`budget = (100 - slo_percent) / 100 * period_minutes`

You are given the outages recorded in the period as a list of `[start, end]` pairs, in minutes
from the start of the period (`start <= end`). The list is in no particular order, and two
monitoring tools may have recorded the same incident, so outages **can overlap or repeat**.
A minute during which the service was down counts once, however many records cover it.

Return the budget that is left: `budget - total_downtime`. A negative result means the SLO was
broken. Answers are compared with a small tolerance.

**Example:** `slo_percent = 99.9, period_minutes = 43200, outages = [[100, 110]]` → `33.2`
(the budget is 43.2 minutes and 10 were used)

**Example:** `slo_percent = 99.9, period_minutes = 43200, outages = [[100, 130], [120, 150]]` → `-6.8`
(the two records overlap; together they cover minutes 100 to 150, which is 50 minutes)
""",
    starter='''def error_budget_left(slo_percent: float, period_minutes: float, outages: List[List[float]]) -> float:
    pass
''',
    solution='''def error_budget_left(slo_percent, period_minutes, outages):
    budget = (100 - slo_percent) / 100 * period_minutes
    down = 0
    cur_start = cur_end = None
    for start, end in sorted(outages):
        if cur_end is None or start > cur_end:      # a separate outage begins
            if cur_end is not None:
                down += cur_end - cur_start
            cur_start, cur_end = start, end
        else:                                       # overlaps or touches the current one
            cur_end = max(cur_end, end)
    if cur_end is not None:
        down += cur_end - cur_start
    return budget - down
''',
    tests=[
        [99.9, 43200, [[100, 110]]],
        [99.9, 43200, [[100, 130], [120, 150]]],
        [99.9, 43200, []],
        [99.0, 10000, [[0, 10], [10, 20]]],
        [99.99, 525600, [[5, 6], [5, 6]]],
        [100, 1000, []],
        [100, 1000, [[1, 2]]],
        [95, 1440, [[300, 320], [10, 40], [35, 50], [600, 600]]],
        [99.5, 10080, [[0, 100], [10, 20], [30, 40]]],
        [99.0, 20000, [[50, 60], [10, 20], [55, 58], [15, 52]]],
        [90, 100000, _intervals(400, 100000)],
        [99.9, 43200, [[7, 7]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def error_budget_left(slo_percent, period_minutes, outages):
    budget = (100 - slo_percent) / 100 * period_minutes
    return budget - sum(e - s for s, e in outages)
''',
        '''def error_budget_left(slo_percent, period_minutes, outages):
    budget = (100 - slo_percent) / 100 * period_minutes
    down, last_end = 0, None
    for s, e in outages:                 # forgot to sort first
        if last_end is not None and s < last_end:
            s = last_end
        down += max(0, e - s)
        last_end = e if last_end is None else max(last_end, e)
    return budget - down
''',
    ],
    guide=dict(
        prereqs="Lists, sorting, a `for` loop. See the lesson *Reliability and maintainability* (availability and error budgets).",
        intuition="The budget is one multiplication. The work is in measuring downtime without counting any minute twice, which means **merging overlapping intervals** before adding up their lengths.",
        hints=[
            "Compute the budget first and set it aside. Then think only about the total length covered by the intervals.",
            "Sort the outages by start time. After sorting, an outage either begins after the current merged outage has ended, or it overlaps it.",
            "Keep one `current` interval. If the next outage starts after `current` ends, add `current`'s length to the total and start a new one. Otherwise extend `current`'s end to the larger of the two ends. Do not forget to add the last interval after the loop.",
        ],
        brute_force="Mark every minute that is down in a set and count the set. It works for whole minutes but uses memory proportional to the total downtime and fails for fractional times.",
        approach="1. `budget = (100 - slo) / 100 * period`.\n2. Sort outages.\n3. Sweep left to right, merging any outage that starts at or before the current end.\n4. Return `budget - downtime`.\n\nDry run on `[[100,130],[120,150]]`: current = [100,130]; next starts at 120 <= 130, so current becomes [100,150]; downtime = 50; budget 43.2 - 50 = -6.8.",
        complexity="Time O(n log n) for the sort, then one pass. Space O(n) for the sorted copy.",
        pitfalls="Adding raw lengths counts overlapping minutes twice. Merging without sorting misses overlaps between records that are far apart in the list. Forgetting the final interval after the loop. A zero-length outage `[7, 7]` must not break the code.",
        follow_up="Real SLOs are usually measured over a *rolling* window, such as the last 30 days at every moment. How would you report the budget left as a function of time?",
    ),
),
dict(
    id="db-graph-traverse",
    title="Follow an Edge Any Number of Times",
    difficulty="Easy",
    pattern="Graph Traversal",
    kind="function",
    entry="reachable",
    description=r"""
A graph is stored as a list of **triples** `[subject, predicate, object]`, for example
`["idaho", "within", "usa"]`. Each triple is an edge from the subject to the object, labelled with
the predicate.

Graph query languages can follow one kind of edge *any number of times*: Cypher writes
`-[:WITHIN*1..]->` and SQL needs `WITH RECURSIVE`. Implement that operation.

Write `reachable(triples, start, predicate)` returning the **sorted list** of every vertex that can
be reached from `start` by following **one or more** edges whose label is `predicate`, always in
the subject-to-object direction.

- Edges with any other label are ignored.
- The graph may contain cycles. Your function must still finish.
- `start` itself is included only if a path of one or more edges leads back to it.
- If `start` has no outgoing edge of that kind, return `[]`.

**Example:** triples `[["idaho","within","usa"], ["usa","within","namerica"], ["lucy","born_in","idaho"]]`,
`start = "idaho"`, `predicate = "within"` → `["namerica", "usa"]`

**Example:** same triples, `start = "lucy"`, `predicate = "within"` → `[]`
""",
    starter='''def reachable(triples: List[List[str]], start: str, predicate: str) -> List[str]:
    pass
''',
    solution='''def reachable(triples, start, predicate):
    out_edges = {}
    for s, p, o in triples:
        if p == predicate:
            out_edges.setdefault(s, []).append(o)
    seen = set()
    todo = list(out_edges.get(start, []))
    while todo:
        v = todo.pop()
        if v in seen:
            continue
        seen.add(v)
        todo.extend(out_edges.get(v, []))
    return sorted(seen)
''',
    tests=[
        [[["idaho", "within", "usa"], ["usa", "within", "namerica"], ["lucy", "born_in", "idaho"]], "idaho", "within"],
        [[["idaho", "within", "usa"], ["usa", "within", "namerica"], ["lucy", "born_in", "idaho"]], "lucy", "within"],
        [[], "a", "within"],
        [[["a", "next", "b"], ["b", "next", "a"]], "a", "next"],
        [[["a", "next", "a"]], "a", "next"],
        [[["a", "x", "b"], ["a", "x", "c"], ["b", "x", "d"], ["c", "x", "d"], ["d", "x", "e"]], "a", "x"],
        [[["a", "x", "b"], ["b", "y", "c"], ["c", "x", "d"]], "a", "x"],
        [[["a", "x", "b"], ["c", "x", "a"]], "a", "x"],
        [[["a", "x", "b"], ["b", "x", "c"], ["c", "x", "b"]], "a", "x"],
        [[["n%d" % i, "next", "n%d" % (i + 1)] for i in range(3000)], "n0", "next"],
        [[["n%d" % i, "next", "n%d" % (i + 1)] for i in range(50)] + [["n50", "next", "n10"]], "n25", "next"],
        [[["a", "x", "b"]], "zzz", "x"],
    ],
    examples=2,
    wrong_solutions=[
        '''def reachable(triples, start, predicate):
    return sorted({o for s, p, o in triples if s == start and p == predicate})
''',
        '''def reachable(triples, start, predicate):
    out_edges = {}
    for s, p, o in triples:
        if p == predicate:
            out_edges.setdefault(s, []).append(o)
    seen = {start}
    todo = [start]
    while todo:
        v = todo.pop()
        for n in out_edges.get(v, []):
            if n not in seen:
                seen.add(n)
                todo.append(n)
    return sorted(seen)
''',
    ],
    guide=dict(
        prereqs="Dictionaries, sets, a `while` loop. See the lesson *Graph models and query languages* (triples, variable-length paths).",
        intuition="Keep a to-do list of vertices to visit and a set of vertices already visited. Each visit adds that vertex's neighbours to the to-do list. The visited set is what stops a cycle from running for ever.",
        hints=[
            "First build a dictionary from each subject to the list of objects it points to, using only the triples with the right predicate.",
            "Start the to-do list with the *neighbours* of `start`, not with `start` itself. That way `start` ends up in the answer only if some path really leads back to it.",
            "Loop: take a vertex off the to-do list; if it has been seen, skip it; otherwise record it and add its neighbours. Sort the visited set at the end.",
        ],
        brute_force="Repeat `for every triple: if its subject is reachable, mark its object reachable` until a full pass changes nothing. Correct, but each pass reads all triples, so a chain of n edges costs O(n^2).",
        approach="1. Index the edges: `out_edges[subject] -> [objects]`.\n2. `todo = out_edges[start]`, `seen = empty set`.\n3. Pop a vertex; skip if seen; else add to `seen` and push its neighbours.\n4. Return `sorted(seen)`.\n\nDry run for `a -> b -> a`, start `a`: todo = [b]; visit b, push a; visit a, push b; b is seen, skip; done. Answer `[a, b]`.",
        complexity="Time O(V + E) plus the final sort. Space O(V + E) for the index and the visited set.",
        pitfalls="Recursion fails on a chain of thousands of vertices because Python limits recursion depth; use an explicit list. Without a visited set a cycle loops for ever. Seeding the visited set with `start` wrongly puts `start` in every answer.",
        follow_up="Return, for each reachable vertex, the smallest number of edges needed to reach it (swap the stack for a queue: breadth-first search).",
    ),
),
dict(
    id="db-wal-replay",
    title="Replay a Write-Ahead Log",
    difficulty="Medium",
    pattern="Storage Engines",
    kind="function",
    entry="replay",
    description=r"""
After a crash, a database rebuilds its state by reading its **write-ahead log** from the start.
Each log record is a list:

- `["begin", tx]` - transaction `tx` starts
- `["set", tx, key, value]` - `tx` wants to store `value` under `key`
- `["delete", tx, key]` - `tx` wants to remove `key` (removing a missing key is not an error)
- `["commit", tx]` - `tx` is committed
- `["abort", tx]` - `tx` is cancelled

Rules of recovery:

1. A transaction's writes take effect **at the moment of its commit record**, in the order the
   transaction made them. If two transactions wrote the same key, the one that **commits later** wins.
2. Writes of an aborted transaction are discarded.
3. The log may stop anywhere, because the machine crashed. A transaction with **no commit record**
   is discarded, as if it had aborted.

Write `replay(log)` returning the recovered key-value state as a list of `[key, value]` pairs
**sorted by key**. Keys are strings.

**Example:**
`[["begin","t1"], ["set","t1","a",1], ["commit","t1"], ["begin","t2"], ["set","t2","a",2]]` → `[["a", 1]]`
(`t2` never committed: the log ends before its commit record)

**Example:**
`[["begin","t1"], ["set","t1","a",1], ["set","t1","b",2], ["delete","t1","a"], ["commit","t1"]]` → `[["b", 2]]`
""",
    starter='''def replay(log: List[list]) -> List[list]:
    pass
''',
    solution='''def replay(log):
    state = {}
    pending = {}                       # tx -> list of buffered operations
    for rec in log:
        kind, tx = rec[0], rec[1]
        if kind == "begin":
            pending[tx] = []
        elif kind == "set":
            pending.setdefault(tx, []).append((rec[2], rec[3], False))
        elif kind == "delete":
            pending.setdefault(tx, []).append((rec[2], None, True))
        elif kind == "commit":
            for key, value, is_delete in pending.pop(tx, []):
                if is_delete:
                    state.pop(key, None)
                else:
                    state[key] = value
        elif kind == "abort":
            pending.pop(tx, None)
    return [[k, state[k]] for k in sorted(state)]
''',
    tests=[
        [[["begin", "t1"], ["set", "t1", "a", 1], ["commit", "t1"], ["begin", "t2"], ["set", "t2", "a", 2]]],
        [[["begin", "t1"], ["set", "t1", "a", 1], ["set", "t1", "b", 2], ["delete", "t1", "a"], ["commit", "t1"]]],
        [[]],
        [[["begin", "t1"], ["set", "t1", "x", 5], ["abort", "t1"]]],
        [[["begin", "t1"], ["begin", "t2"], ["set", "t1", "x", 1], ["set", "t2", "x", 2], ["commit", "t2"], ["commit", "t1"]]],
        [[["begin", "t1"], ["begin", "t2"], ["set", "t1", "x", 1], ["set", "t2", "y", 2], ["commit", "t1"], ["abort", "t2"]]],
        [[["begin", "t1"], ["delete", "t1", "ghost"], ["commit", "t1"]]],
        [[["begin", "t1"], ["set", "t1", "k", "v1"], ["commit", "t1"], ["begin", "t2"], ["delete", "t2", "k"], ["commit", "t2"],
          ["begin", "t3"], ["set", "t3", "k", "v3"]]],
        [[["begin", "t1"], ["set", "t1", "b", 0], ["set", "t1", "a", ""], ["set", "t1", "c", None], ["commit", "t1"]]],
        [[["begin", "t1"], ["set", "t1", "x", 1], ["set", "t1", "x", 2], ["set", "t1", "x", 3], ["commit", "t1"],
          ["begin", "t2"], ["set", "t2", "x", 4], ["abort", "t2"]]],
        [[["begin", "t1"], ["set", "t1", "x", 1], ["begin", "t2"], ["set", "t2", "x", 9], ["delete", "t1", "x"],
          ["commit", "t1"], ["commit", "t2"]]],
        [_wal(300, 12)],
        [_wal(60, 3)],
    ],
    examples=2,
    wrong_solutions=[
        '''def replay(log):
    state = {}
    for rec in log:                    # applies every write at once, ignoring commit and abort
        if rec[0] == "set":
            state[rec[2]] = rec[3]
        elif rec[0] == "delete":
            state.pop(rec[2], None)
    return [[k, state[k]] for k in sorted(state)]
''',
        '''def replay(log):
    committed = {rec[1] for rec in log if rec[0] == "commit"}
    state = {}
    for rec in log:                    # right transactions, but applied in write order, not commit order
        if rec[1] not in committed:
            continue
        if rec[0] == "set":
            state[rec[2]] = rec[3]
        elif rec[0] == "delete":
            state.pop(rec[2], None)
    return [[k, state[k]] for k in sorted(state)]
''',
    ],
    guide=dict(
        prereqs="Dictionaries and lists. See the lessons *B-trees, write-ahead logs and the LSM vs B-tree trade-off* and *ACID, read committed and snapshot isolation* (atomicity).",
        intuition="Atomicity means all of a transaction's writes count or none do, and the commit record is the single fact that decides. So do not touch the real state while reading a transaction's writes. Hold them in a waiting area, and move them into the state only when the commit record appears.",
        hints=[
            "Keep two dictionaries: `state` for the recovered data and `pending` mapping each open transaction to the list of writes it has made so far.",
            "On `set` or `delete`, append to that transaction's pending list. Do not change `state` yet.",
            "On `commit`, apply the transaction's pending writes to `state` in order and forget the list. On `abort`, forget the list. Anything still pending when the log ends is dropped.",
        ],
        brute_force="Scan the log once to collect the committed transaction ids, then for each commit record, in order, scan the whole log again for that transaction's writes. Correct, but O(n * number of transactions).",
        approach="One pass with a buffer per transaction.\n\nDry run on `begin t1, begin t2, set t1 x=1, set t2 x=2, commit t2, commit t1`:\n- pending: t1 -> [x=1], t2 -> [x=2]\n- commit t2: state x=2\n- commit t1: state x=1\n- answer `[[\"x\", 1]]`, because t1 committed later.",
        complexity="Time O(n) for the pass plus O(k log k) to sort k keys. Space O(n) for the buffers.",
        pitfalls="Applying writes immediately makes uncommitted and aborted data visible. Applying committed transactions' writes in *write* order gets interleaved transactions wrong. Deleting a missing key must not raise. A stored value of `None`, `0` or an empty string is still a value.",
        follow_up="Real logs are huge, so databases periodically write a **checkpoint**: a snapshot of the state plus the log position it corresponds to. Extend `replay` to start from a checkpoint.",
    ),
),
dict(
    id="db-bitmap-rle",
    title="Bitmap Index with Run-Length Encoding",
    difficulty="Easy",
    pattern="Column Storage",
    kind="function",
    entry="bitmap_rle",
    description=r"""
A column store can describe "which rows have this value?" with a **bitmap**: one bit per row,
1 where the row has the value and 0 where it does not. Bitmaps with long stretches of equal bits
are stored compactly with **run-length encoding**: the lengths of the runs, alternating between
runs of 0s and runs of 1s.

Write `bitmap_rle(column, value)` returning the run lengths for the bitmap of `value` in `column`.

- The list **always starts with the length of a run of 0s**. If the first row matches, that
  first length is `0`.
- After that, lengths alternate: 1s, 0s, 1s, ...
- For an empty column return `[]`.

**Example:** `column = [69, 69, 74, 31, 31, 31, 69]`, `value = 31` → `[3, 3, 1]`
(bitmap `0001110`: three 0s, three 1s, one 0)

**Example:** `column = [69, 69, 74]`, `value = 69` → `[0, 2, 1]`
(bitmap `110`: zero 0s, two 1s, one 0)
""",
    starter='''def bitmap_rle(column: list, value) -> List[int]:
    pass
''',
    solution='''def bitmap_rle(column, value):
    if not column:
        return []
    runs = []
    current_bit, count = 0, 0
    for x in column:
        bit = 1 if x == value else 0
        if bit == current_bit:
            count += 1
        else:
            runs.append(count)
            current_bit, count = bit, 1
    runs.append(count)
    return runs
''',
    tests=[
        [[69, 69, 74, 31, 31, 31, 69], 31],
        [[69, 69, 74], 69],
        [[], 5],
        [[1, 2, 3], 9],
        [[7, 7, 7, 7], 7],
        [[7], 7],
        [[8], 7],
        [[1, 0, 1, 0, 1], 1],
        [[0, 1, 0, 1, 0], 1],
        [["de", "fr", "fr", "de", "de", "us"], "de"],
        [[i // 1000 for i in range(5000)], 2],
        [[69, 69, 69, 74, 31, 31, 31, 31, 29, 30, 30, 31, 31, 31, 68, 69, 69], 69],
    ],
    examples=2,
    wrong_solutions=[
        '''def bitmap_rle(column, value):
    runs, prev, count = [], None, 0
    for x in column:                   # no leading zero-length run when the first row matches
        bit = 1 if x == value else 0
        if bit == prev:
            count += 1
        else:
            if prev is not None:
                runs.append(count)
            prev, count = bit, 1
    if prev is not None:
        runs.append(count)
    return runs
''',
        '''def bitmap_rle(column, value):
    if not column:
        return []
    runs, prev, count = [], column[0], 0
    for x in column:                   # encodes runs of equal column values, not runs of the bitmap
        if x == prev:
            count += 1
        else:
            runs.append(count)
            prev, count = x, 1
    runs.append(count)
    return runs
''',
    ],
    guide=dict(
        prereqs="Loops and lists. See the lesson *OLTP vs OLAP, warehouses and column-oriented storage* (bitmap encoding, run-length encoding).",
        intuition="Walk down the column turning each row into a bit, and count how long the current bit keeps repeating. Every time the bit flips, write down the count and start a new one. Pretending the bitmap begins with a run of 0s (possibly of length zero) is what makes the output unambiguous.",
        hints=[
            "Convert each row to a bit: `1 if x == value else 0`.",
            "Keep `current_bit` (start it at 0) and `count` (start at 0). When the row's bit equals `current_bit`, add one to `count`.",
            "When the bit differs, append `count` to the result, switch `current_bit`, and reset `count` to 1. After the loop, append the final `count`.",
        ],
        brute_force="Build the whole bitmap as a string of 0s and 1s, then split it into runs. It gives the same answer and uses memory for the full bitmap, which is what the encoding is meant to avoid.",
        approach="Dry run on `[69, 69, 74]` with value 69: start bit 0, count 0. Row 1 is a 1, which differs: append 0, now bit 1, count 1. Row 2 is a 1: count 2. Row 3 is a 0: append 2, bit 0, count 1. End: append 1. Result `[0, 2, 1]`.",
        complexity="Time O(n), space O(number of runs).",
        pitfalls="Leaving out the leading 0 when the first row matches makes `[2, 1]` ambiguous: is it `001` or `110`? Encoding runs of raw column values is a different thing. Returning `[0]` for an empty column when the specification asks for `[]`.",
        follow_up="Write `rle_or(a, b)` that combines two encoded bitmaps with OR without expanding them. That is how a column store answers `WHERE x IN (v1, v2)` on compressed data.",
    ),
),
dict(
    id="db-varint-encode",
    title="Variable-Length Integer Encoding",
    difficulty="Easy",
    pattern="Bit Manipulation",
    kind="function",
    entry="encode_varint",
    description=r"""
Protocol Buffers and many storage formats save space by writing small numbers in fewer bytes.
A **varint** stores a non-negative whole number as a sequence of bytes:

- Split the number into groups of 7 bits, starting with the **lowest** 7 bits.
- Each group becomes one byte. The byte's top bit (value 128) is set to 1 if **more bytes follow**,
  and 0 on the last byte.

Write `encode_varint(n)` returning the bytes as a list of integers from 0 to 255.

**Example:** `n = 1` → `[1]`

**Example:** `n = 300` → `[172, 2]`
(300 is `10 0101100` in binary; the low 7 bits `0101100` are 44, plus 128 because more follows,
gives 172; the remaining bits `10` are 2)

**Example:** `n = 0` → `[0]`
""",
    starter='''def encode_varint(n: int) -> List[int]:
    pass
''',
    solution='''def encode_varint(n):
    out = []
    while True:
        group = n & 0x7F          # lowest 7 bits
        n >>= 7                   # drop them
        if n:
            out.append(group | 0x80)
        else:
            out.append(group)
            return out
''',
    tests=[
        [1],
        [300],
        [0],
        [127],
        [128],
        [1337],
        [16383],
        [16384],
        [255],
        [2 ** 32],
        [2 ** 63 - 1],
        [2097151],
        [150],
    ],
    examples=3,
    wrong_solutions=[
        '''def encode_varint(n):
    out = []
    while n:                       # returns [] for zero
        group = n & 0x7F
        n >>= 7
        out.append(group | 0x80 if n else group)
    return out
''',
        '''def encode_varint(n):
    groups = []
    while True:
        groups.append(n & 0x7F)
        n >>= 7
        if not n:
            break
    groups.reverse()               # highest group first: wrong byte order
    return [g | 0x80 for g in groups[:-1]] + [groups[-1]]
''',
    ],
    guide=dict(
        prereqs="The bit operators `&`, `|` and `>>`. See the lesson *Encoding formats and schema evolution* (Protocol Buffers, varints).",
        intuition="Peel off the lowest seven bits again and again. Each peel is one byte. If anything is left after a peel, switch on the byte's top bit as a signal that the number continues.",
        hints=[
            "`n & 0x7F` keeps the lowest 7 bits of `n`. `n >> 7` throws those 7 bits away.",
            "After shifting, check whether `n` is now zero. If it is not, more bytes will follow, so add 128 (`| 0x80`) to the byte you are about to write.",
            "Use a loop that always runs at least once, so that `n = 0` produces `[0]` and not an empty list.",
        ],
        brute_force="Convert to a binary string with `bin(n)`, pad it to a multiple of 7 characters, cut it into chunks, reverse the chunks and convert each back. It works and is slower and easier to get wrong at the edges.",
        approach="Dry run for 300 (binary `100101100`): low 7 bits `0101100` = 44; shift leaves 2, which is non-zero, so write 44 + 128 = 172. Next: low 7 bits of 2 = 2; shift leaves 0, so write 2 and stop. Result `[172, 2]`.",
        complexity="Time and space O(number of bytes), which is the bit length of `n` divided by 7, rounded up.",
        pitfalls="Returning an empty list for zero. Writing the highest group first. Setting the continuation bit on the last byte. Using 8 bits per group and leaving no room for the continuation bit.",
        follow_up="Write `decode_varint(bytes)`. Then look up *zig-zag encoding*, which Protocol Buffers and Avro use so that small negative numbers also take few bytes.",
    ),
),
dict(
    id="db-schema-resolve",
    title="Resolve Writer and Reader Schemas",
    difficulty="Easy",
    pattern="Schema Evolution",
    kind="function",
    entry="resolve",
    description=r"""
In Avro, data written with one version of a schema can be read by a program that expects another
version. The library matches fields **by name**:

- A field the reader wants and the writer provided: take the writer's value.
- A field the reader wants and the writer did **not** provide: use the reader's **default** for it.
- A field the writer provided and the reader does not want: ignore it.
- A field the reader wants, the writer did not provide, and for which the reader has **no default**:
  the schemas are incompatible.

`record` is a dictionary of the fields the writer provided. `reader_schema` is a list describing
the reader's fields, each either `[name]` (no default) or `[name, default]` (the default may be
`None`).

Write `resolve(record, reader_schema)` returning a dictionary with exactly the reader's fields,
or the string `"incompatible"` if any reader field cannot be filled.

**Example:** `record = {"userName": "Martin", "favoriteNumber": 1337}`,
`reader_schema = [["userName"], ["photoUrl", None]]` → `{"userName": "Martin", "photoUrl": None}`

**Example:** `record = {"userName": "Martin"}`, `reader_schema = [["userName"], ["email"]]` → `"incompatible"`
""",
    starter='''def resolve(record: dict, reader_schema: List[list]):
    pass
''',
    solution='''def resolve(record, reader_schema):
    out = {}
    for field in reader_schema:
        name = field[0]
        if name in record:
            out[name] = record[name]
        elif len(field) == 2:
            out[name] = field[1]
        else:
            return "incompatible"
    return out
''',
    tests=[
        [{"userName": "Martin", "favoriteNumber": 1337}, [["userName"], ["photoUrl", None]]],
        [{"userName": "Martin"}, [["userName"], ["email"]]],
        [{}, []],
        [{"a": 1, "b": 2}, []],
        [{}, [["a", 0], ["b", "x"]]],
        [{"a": 5}, [["a", 0]]],
        [{"a": None}, [["a", 7]]],
        [{"count": 0, "name": ""}, [["count", 99], ["name", "unknown"]]],
        [{"a": 1}, [["b", 2], ["c"]]],
        [{"tags": ["x", "y"], "meta": {"k": 1}}, [["meta"], ["tags", []], ["extra", {"z": 0}]]],
        [{"a": 1, "b": 2, "c": 3}, [["c"], ["a"]]],
        [{"active": False}, [["active", True]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def resolve(record, reader_schema):
    out = dict(record)                 # keeps fields the reader does not know
    for field in reader_schema:
        if field[0] not in out:
            if len(field) == 2:
                out[field[0]] = field[1]
            else:
                return "incompatible"
    return out
''',
        '''def resolve(record, reader_schema):
    out = {}
    for field in reader_schema:
        name = field[0]
        value = record.get(name)
        if value:                      # treats 0, "", False and None as missing
            out[name] = value
        elif len(field) == 2:
            out[name] = field[1]
        else:
            return "incompatible"
    return out
''',
    ],
    guide=dict(
        prereqs="Dictionaries and the `in` operator. See the lesson *Encoding formats and schema evolution* (writer's schema and reader's schema).",
        intuition="The reader's schema drives everything. Walk through the fields the reader wants, and for each one ask two questions in order: did the writer supply it, and if not, is there a default?",
        hints=[
            "Loop over `reader_schema`, not over `record`. Fields that only the writer knows are then ignored without any extra code.",
            "Test presence with `name in record`. Do not test the value itself, because a stored `0`, `\"\"`, `False` or `None` is a real value.",
            "A field description of length 2 has a default, even when that default is `None`. A description of length 1 has none: if the record lacks the field, return `\"incompatible\"` at once.",
        ],
        brute_force="There is nothing slower that is also simpler here: one pass over the reader's fields is the direct method.",
        approach="For each reader field: present in the record, copy the value; absent with a default, use the default; absent without one, return `\"incompatible\"`.\n\nDry run: record `{userName: Martin, favoriteNumber: 1337}`, reader `[[userName], [photoUrl, None]]`. `userName` is present, copy. `photoUrl` is absent and has a default, use `None`. `favoriteNumber` is never looked at.",
        complexity="Time O(number of reader fields), space the same for the result.",
        pitfalls="Using `record.get(name) or default` replaces legitimate falsy values with the default. Starting from a copy of the record leaves unknown fields in the result. Confusing 'default is None' with 'no default'.",
        follow_up="Avro also lets a reader rename a field by listing *aliases*. Extend the schema entries to carry a list of old names to try when the main name is missing.",
    ),
),
dict(
    id="db-sibling-versions",
    title="Sibling Values with Version Numbers",
    difficulty="Medium",
    pattern="Replication",
    kind="function",
    entry="final_siblings",
    description=r"""
A single server stores one key. To avoid silently losing concurrent writes, it follows the
version-number algorithm from the lesson on detecting concurrent writes:

- The server keeps a counter `version`, starting at 0, and a collection of stored values, each
  remembered together with the version at which it was written. Values stored side by side are
  called **siblings**.
- A client that writes sends `[value, seen_version]`, where `seen_version` is the version number
  it got from its last read (`0` if it has never read).
- For each write the server: adds 1 to `version`; **removes every stored value whose version is
  less than or equal to `seen_version`** (the client had seen those and has merged them into its
  new value); then stores the new value with the new `version`. Values with a higher version stay,
  because the client did not know about them: they are concurrent with this write.

Write `final_siblings(writes)` that processes the writes in order and returns the remaining
siblings as a list of `[version, value]` pairs in increasing order of version.

**Example:** `[["milk", 0], ["eggs", 0]]` → `[[1, "milk"], [2, "eggs"]]`
(the second client had seen nothing, so nothing was overwritten)

**Example:** `[["milk", 0], ["eggs", 0], ["milk+flour", 1]]` → `[[2, "eggs"], [3, "milk+flour"]]`
(the third write had seen version 1, so "milk" is replaced; "eggs" at version 2 is kept)
""",
    starter='''def final_siblings(writes: List[list]) -> List[list]:
    pass
''',
    solution='''def final_siblings(writes):
    version = 0
    stored = []                        # list of [version, value]
    for value, seen_version in writes:
        version += 1
        stored = [[ver, val] for ver, val in stored if ver > seen_version]
        stored.append([version, value])
    return stored
''',
    tests=[
        [[["milk", 0], ["eggs", 0]]],
        [[["milk", 0], ["eggs", 0], ["milk+flour", 1]]],
        [[]],
        [[["a", 0]]],
        [[["a", 0], ["b", 1], ["c", 2], ["d", 3]]],
        [[["a", 0], ["b", 0], ["c", 0], ["d", 0]]],
        [[[["milk"], 0], [["eggs"], 0], [["milk", "flour"], 1], [["eggs", "milk", "ham"], 2],
          [["milk", "flour", "eggs", "bacon"], 3]]],
        [[["a", 0], ["b", 0], ["merged", 2]]],
        [[["a", 0], ["b", 0], ["c", 0], ["x", 1], ["y", 4]]],
        [[["a", 0], ["b", 1], ["stale", 0], ["c", 2]]],
        [[["v%d" % i, max(0, i - 2)] for i in range(200)]],
        [[["a", 0], ["b", 0], ["c", 1], ["d", 1], ["e", 5]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def final_siblings(writes):
    version, stored = 0, []
    for value, seen_version in writes:     # last write wins: discards concurrent values
        version += 1
        stored = [[version, value]]
    return stored
''',
        '''def final_siblings(writes):
    version, stored = 0, []
    for value, seen_version in writes:
        version += 1
        stored = [[ver, val] for ver, val in stored if ver >= seen_version]   # keeps the value the client had seen
        stored.append([version, value])
    return stored
''',
    ],
    guide=dict(
        prereqs="Lists and list comprehensions. See the lesson *Detecting concurrent writes: LWW, version vectors, CRDTs* (capturing happens-before with version numbers).",
        intuition="The number a client sends back says how much of the past it knows. Everything at or below that number has been folded into the client's new value, so it can go. Everything above it was written behind the client's back, so it must stay.",
        hints=[
            "Keep a counter and a list of `[version, value]` pairs.",
            "For each write, first increase the counter. Then rebuild the list keeping only pairs whose version is **greater than** `seen_version`.",
            "Append the new `[version, value]` last. Because versions only grow, the list stays in increasing order without sorting.",
        ],
        brute_force="The direct simulation is already linear per write. A slower but equivalent approach keeps every value ever written and marks them as overwritten, filtering at the end.",
        approach="Dry run on `[milk,0], [eggs,0], [milk+flour,1]`:\n- write 1: version 1, nothing to remove, store [1, milk]\n- write 2: version 2, seen 0 removes nothing, store [2, eggs]\n- write 3: version 3, seen 1 removes [1, milk], store [3, milk+flour]\n- result `[[2, eggs], [3, milk+flour]]`.",
        complexity="Time O(n * s) where s is the number of siblings alive at once (at most n). Space O(s).",
        pitfalls="Using `>=` keeps the very value the client said it had seen. Replacing the whole list on each write is last-write-wins and loses concurrent data. Forgetting to raise the version before storing.",
        follow_up="With several replicas, one counter is not enough. Each replica needs its own, and the collection of counters is a **version vector**. Try the problem `db-vector-clock-compare` next.",
    ),
),
]
