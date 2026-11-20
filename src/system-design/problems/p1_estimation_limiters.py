"""System design problems 1: estimation, availability and the five rate limiters."""


def _ops(cls, ctor_args, calls):
    """Build a class-problem test: calls is a list of (method, args)."""
    return [[cls] + [c[0] for c in calls], [list(ctor_args)] + [list(c[1]) for c in calls]]


PROBLEMS = [
dict(
    id="sd-capacity-estimate",
    title="Capacity Estimator: QPS, Storage and Bandwidth",
    difficulty="Easy",
    pattern="Estimation",
    kind="function",
    entry="capacity_estimate",
    compare="float",
    description=r"""
Turn a list of stated assumptions into the five numbers every back-of-the-envelope estimate needs.

Write `capacity_estimate(dau, writes_per_user, reads_per_user, bytes_per_write, bytes_per_read, peak_factor, replication, years)` and return a list of five numbers, in this order:

1. **average write QPS** = `dau * writes_per_user / 86400`
2. **average read QPS** = `dau * reads_per_user / 86400`
3. **peak QPS** = `(write QPS + read QPS) * peak_factor`
4. **storage in bytes** for the whole retention period = writes per day `* bytes_per_write * 365 * years * replication`
5. **egress in bits per second** = `read QPS * bytes_per_read * 8`

A day has 86,400 seconds and a year has 365 days. Results are compared with a relative tolerance of 1e-6.

**Example:** `capacity_estimate(1_000_000, 2, 10, 500, 2000, 2, 3, 1)` →
`[23.148148..., 115.740740..., 277.777777..., 1095000000000, 1851851.85...]`
""",
    starter='''def capacity_estimate(dau, writes_per_user, reads_per_user, bytes_per_write,
                      bytes_per_read, peak_factor, replication, years):
    pass
''',
    solution='''def capacity_estimate(dau, writes_per_user, reads_per_user, bytes_per_write,
                      bytes_per_read, peak_factor, replication, years):
    day = 86400
    writes_day = dau * writes_per_user
    write_qps = writes_day / day
    read_qps = dau * reads_per_user / day
    peak = (write_qps + read_qps) * peak_factor
    storage = writes_day * bytes_per_write * 365 * years * replication
    egress_bits = read_qps * bytes_per_read * 8
    return [write_qps, read_qps, peak, storage, egress_bits]
''',
    tests=[
        [1_000_000, 2, 10, 500, 2000, 2, 3, 1],
        [20_000_000, 1, 50, 300, 20_000, 2, 3, 5],
        [100_000_000, 0.2, 100, 2_050_000, 245_000, 2, 3, 1],
        [86_400, 1, 1, 1, 1, 1, 1, 1],
        [0, 5, 5, 100, 100, 3, 3, 10],
        [50_000_000, 40, 40, 200, 200, 2, 3, 1],
        [10, 1, 0, 1000, 0, 5, 1, 1],
        [300_000_000, 0.01, 3, 1_000_000, 50_000, 10, 2, 7],
        [1, 1, 1, 1, 1, 1, 1, 1],
        [5_000_000, 3, 30, 1024, 4096, 1.5, 3, 2],
        [123_456_789, 2.5, 17.5, 777, 3333, 2.2, 3, 4],
    ],
    examples=2,
    wrong_solutions=[
        '''def capacity_estimate(dau, w, r, bw, br, peak_factor, replication, years):
    wq, rq = dau * w / 86400, dau * r / 86400
    return [wq, rq, (wq + rq) * peak_factor, dau * w * bw * 365 * years, rq * br * 8]
''',
        '''def capacity_estimate(dau, w, r, bw, br, peak_factor, replication, years):
    wq, rq = dau * w / 86400, dau * r / 86400
    return [wq, rq, (wq + rq) * peak_factor, dau * w * bw * 365 * years * replication, rq * br]
''',
        '''def capacity_estimate(dau, w, r, bw, br, peak_factor, replication, years):
    wq, rq = dau * w / 86400, dau * r / 86400
    return [wq, rq, rq * peak_factor, dau * w * bw * 365 * years * replication, rq * br * 8]
''',
    ],
    guide=dict(
        prereqs="The estimation lessons: a day is 86,400 seconds; storage = writes x size x days x copies; network speeds are in bits.",
        intuition="Every estimate is the same chain: users x actions gives events per day; divide by seconds per day for a rate; multiply by bytes for storage and bandwidth.",
        hints=[
            "Compute writes per day once and reuse it for both the write QPS and the storage.",
            "Peak applies to the sum of reads and writes, not to reads alone.",
            "Egress is asked for in bits per second: multiply bytes by 8.",
        ],
        brute_force="There is no search here; the naive approach of writing each formula separately is already O(1). The risk is unit mistakes, not speed.",
        approach="""1. `writes_day = dau * writes_per_user`.
2. `write_qps = writes_day / 86400`, `read_qps = dau * reads_per_user / 86400`.
3. `peak = (write_qps + read_qps) * peak_factor`.
4. `storage = writes_day * bytes_per_write * 365 * years * replication`.
5. `egress = read_qps * bytes_per_read * 8`.

**Dry run** with `(1_000_000, 2, 10, 500, 2000, 2, 3, 1)`: writes/day = 2,000,000 so write QPS = 23.15; read QPS = 10,000,000 / 86,400 = 115.74; peak = 138.89 x 2 = 277.78; storage = 2,000,000 x 500 x 365 x 1 x 3 = 1.095e12 bytes (about 1 TB); egress = 115.74 x 2000 x 8 = 1.85 Mbit/s.""",
        complexity="Time O(1), space O(1): a fixed number of multiplications.",
        pitfalls="Forgetting the replication factor; reporting egress in bytes; applying the peak factor only to reads; using 24 x 60 = 1,440 (minutes) instead of 86,400 seconds.",
        follow_up="Add a server count: ceil(peak / (per_server_qps x utilisation)). Add a cache size from the 80/20 rule.",
    ),
),
dict(
    id="sd-availability",
    title="Availability of Series and Parallel Components",
    difficulty="Easy",
    pattern="Estimation",
    kind="function",
    entry="availability",
    compare="float",
    description=r"""
A system is described as a nested structure:

- a **number** between 0 and 1 is one component's availability (0.999 means 99.9%);
- `["series", part, part, ...]` means **all** parts are needed: availabilities multiply;
- `["parallel", part, part, ...]` means **any one** part is enough: the system is down only when every part is down, so availability is `1 - product of (1 - part)`.

Parts can themselves be nested lists. An empty series has availability 1; an empty parallel group has availability 0.

Write `availability(spec)` returning a list `[a, downtime]` where `a` is the availability of the whole system as a fraction and `downtime` is the expected **downtime in minutes per year**, `(1 - a) * 365 * 24 * 60`.

**Example:** `availability(["series", 0.999, 0.999])` → `[0.998001, 1050.67...]`

**Example:** `availability(["parallel", 0.99, 0.99])` → `[0.9999, 52.56]`
""",
    starter='''def availability(spec):
    pass
''',
    solution='''def availability(spec):
    def a(node):
        if isinstance(node, (int, float)):
            return float(node)
        kind, parts = node[0], node[1:]
        if kind == "series":
            out = 1.0
            for p in parts:
                out *= a(p)
            return out
        down = 1.0
        for p in parts:
            down *= 1.0 - a(p)
        return 1.0 - down
    value = a(spec)
    return [value, (1.0 - value) * 365 * 24 * 60]
''',
    tests=[
        [["series", 0.999, 0.999]],
        [["parallel", 0.99, 0.99]],
        [0.999],
        [["series", 0.9999, ["parallel", 0.99, 0.99, 0.99], 0.9995]],
        [["series"]],
        [["parallel"]],
        [["parallel", ["series", 0.99, 0.99], ["series", 0.99, 0.99]]],
        [["series", ["parallel", 0.9, 0.9], ["parallel", 0.9, 0.9], ["parallel", 0.9, 0.9]]],
        [1],
        [0],
        [["series", 0.99999, 0.99999, 0.99999, 0.99999, 0.99999, 0.99999, 0.99999, 0.99999, 0.99999, 0.99999]],
        [["parallel", 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]],
        [["series", ["parallel", ["series", 0.95, 0.99], 0.9], 0.999, ["parallel", 0.8]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def availability(spec):
    def a(n):
        if isinstance(n, (int, float)):
            return float(n)
        out = 1.0
        for p in n[1:]:
            out *= a(p)
        return out
    v = a(spec)
    return [v, (1 - v) * 365 * 24 * 60]
''',
        '''def availability(spec):
    def a(n):
        if isinstance(n, (int, float)):
            return float(n)
        if n[0] == "series":
            out = 1.0
            for p in n[1:]:
                out *= a(p)
            return out
        return max([a(p) for p in n[1:]] or [0.0])
    v = a(spec)
    return [v, (1 - v) * 365 * 24 * 60]
''',
        '''def availability(spec):
    def a(n):
        if isinstance(n, (int, float)):
            return float(n)
        if n[0] == "series":
            out = 1.0
            for p in n[1:]:
                out *= a(p)
            return out
        d = 1.0
        for p in n[1:]:
            d *= 1 - a(p)
        return 1 - d
    v = a(spec)
    return [v, (1 - v) * 365 * 24]
''',
    ],
    guide=dict(
        prereqs="The lesson 'The vocabulary of scale': availability, series and parallel combination, the nines. Recursion on nested lists.",
        intuition="A chain is only up when every link is up, so multiply. A redundant group is only down when every copy is down, so multiply the *down* probabilities and subtract from 1. Nesting means: evaluate the inner groups first.",
        hints=[
            "Write a helper that returns the availability of one node: a number returns itself.",
            "For a list, look at the first element to know the rule, and call the helper on each remaining element.",
            "Parallel: start `down = 1.0`, multiply by `(1 - a(part))` for each part, return `1 - down`. An empty group then gives 0, which is what the statement asks.",
        ],
        brute_force="You could simulate millions of random up/down states and count, which is slow and inexact. The closed-form recursion is exact.",
        approach="""Recursive evaluation of the tree:

1. Base case: a number is its own availability.
2. `series`: product of the children's availabilities (empty product is 1).
3. `parallel`: `1 - product of (1 - child)` (empty product is 1, so the result is 0).
4. Downtime = `(1 - a) * 525600` minutes.

**Dry run** for `["series", 0.9999, ["parallel", 0.99, 0.99, 0.99], 0.9995]`: the parallel group is `1 - 0.01^3 = 0.999999`; the series is `0.9999 x 0.999999 x 0.9995 = 0.999399...`; downtime = `0.000601 x 525600`, about 316 minutes a year.""",
        complexity="Time O(n) for n numbers and brackets in the spec; space O(depth) for the recursion.",
        pitfalls="Multiplying availabilities in a parallel group (that is the series rule); taking the maximum for a parallel group; returning downtime in hours; mishandling the empty groups.",
        follow_up="The formula assumes independent failures. How would you model two copies that share a power supply? (Put the shared part in series with the parallel group.)",
    ),
),
dict(
    id="sd-fixed-window",
    title="Fixed Window Rate Limiter",
    difficulty="Easy",
    pattern="Rate Limiting",
    kind="class",
    entry="FixedWindowLimiter",
    description=r"""
Implement the fixed window counter algorithm with explicit timestamps.

`FixedWindowLimiter(limit, window)` allows at most `limit` requests per caller in each window of `window` seconds. Windows are aligned to time zero: a timestamp `ts` (a non-negative integer, in seconds) belongs to window number `ts // window`.

- `allow(key, ts)` → `True` if the caller `key` has made fewer than `limit` allowed requests in the window containing `ts`; the request is then counted. Otherwise `False`, and the request is **not** counted.

Each key has its own counter. Timestamps never decrease.

**Example:** `FixedWindowLimiter(2, 10)`: `allow("a",0)`→True, `allow("a",5)`→True, `allow("a",9)`→False, `allow("a",10)`→True (new window), `allow("b",9)`→True (different key).
""",
    starter='''class FixedWindowLimiter:
    def __init__(self, limit: int, window: int):
        pass

    def allow(self, key: str, ts: int) -> bool:
        pass
''',
    solution='''class FixedWindowLimiter:
    def __init__(self, limit, window):
        self.limit, self.window = limit, window
        self.state = {}                      # key -> [window_id, count]

    def allow(self, key, ts):
        wid = ts // self.window
        s = self.state.get(key)
        if s is None or s[0] != wid:
            s = self.state[key] = [wid, 0]
        if s[1] < self.limit:
            s[1] += 1
            return True
        return False
''',
    tests=[
        _ops("FixedWindowLimiter", [2, 10], [("allow", ["a", 0]), ("allow", ["a", 5]), ("allow", ["a", 9]), ("allow", ["a", 10]), ("allow", ["b", 9])]),
        _ops("FixedWindowLimiter", [1, 1], [("allow", ["k", t]) for t in (0, 0, 1, 1, 2, 5, 5)]),
        _ops("FixedWindowLimiter", [5, 60], [("allow", ["u", t]) for t in (58, 58, 59, 59, 59, 60, 60, 60, 61, 61, 62)]),
        _ops("FixedWindowLimiter", [3, 10], [("allow", [k, t]) for t in (0, 1, 2, 3) for k in ("x", "y")]),
        _ops("FixedWindowLimiter", [0, 10], [("allow", ["a", 0]), ("allow", ["a", 10])]),
        _ops("FixedWindowLimiter", [2, 5], [("allow", ["a", t]) for t in (4, 4, 4, 5, 9, 9, 10, 100, 100, 100, 104, 105)]),
        _ops("FixedWindowLimiter", [3, 7], [("allow", ["a", t]) for t in range(0, 30)]),
        _ops("FixedWindowLimiter", [2, 10], [("allow", ["a", 0]), ("allow", ["a", 1]), ("allow", ["a", 2]), ("allow", ["a", 3]), ("allow", ["a", 30]), ("allow", ["a", 31]), ("allow", ["a", 32])]),
        _ops("FixedWindowLimiter", [1, 1000], [("allow", [f"user{i % 3}", i]) for i in range(12)]),
        _ops("FixedWindowLimiter", [100, 60], [("allow", ["a", 59]) for _ in range(101)] + [("allow", ["a", 60]) for _ in range(101)]),
        _ops("FixedWindowLimiter", [4, 3], [("allow", ["a", t // 2]) for t in range(40)]),
    ],
    examples=1,
    wrong_solutions=[
        '''class FixedWindowLimiter:
    def __init__(self, limit, window):
        self.limit, self.window, self.state = limit, window, {}
    def allow(self, key, ts):
        s = self.state.setdefault(key, [ts, 0])
        if ts - s[0] >= self.window:
            s[0], s[1] = ts, 0
        if s[1] < self.limit:
            s[1] += 1
            return True
        return False
''',
        '''class FixedWindowLimiter:
    def __init__(self, limit, window):
        self.limit, self.window, self.wid, self.count = limit, window, None, 0
    def allow(self, key, ts):
        wid = ts // self.window
        if wid != self.wid:
            self.wid, self.count = wid, 0
        if self.count < self.limit:
            self.count += 1
            return True
        return False
''',
        '''class FixedWindowLimiter:
    def __init__(self, limit, window):
        self.limit, self.window, self.state = limit, window, {}
    def allow(self, key, ts):
        wid = ts // self.window
        s = self.state.get(key)
        if s is None or s[0] != wid:
            s = self.state[key] = [wid, 0]
        s[1] += 1
        return s[1] <= self.limit + 1
''',
    ],
    guide=dict(
        prereqs="Lesson 'Design a rate limiter I', section on the fixed window counter. Integer division and dictionaries.",
        intuition="Time is cut into numbered boxes. Each caller has one counter that belongs to one box; when a request arrives in a later box, the counter starts again from zero.",
        hints=[
            "The window number of a timestamp is `ts // window`.",
            "Store, for each key, the window number its counter belongs to and the count.",
            "If the stored window number differs from the current one, reset the count before testing it. Only count requests you allow.",
        ],
        brute_force="Keep every timestamp per key and count those with the same window number on each call: O(n) per call and unbounded memory.",
        approach="""Per key keep `[window_id, count]`.

1. `wid = ts // window`.
2. If the key is new or its stored `window_id != wid`, set it to `[wid, 0]`.
3. If `count < limit`: increment and return True; else return False.

**Dry run**, `limit=2, window=10`: `allow(a,0)` wid 0, count 0→1 True. `allow(a,5)` count 1→2 True. `allow(a,9)` count 2 is not < 2: False. `allow(a,10)` wid 1 differs: reset, count 0→1 True.""",
        complexity="Time O(1) per call; space O(number of keys).",
        pitfalls="Starting the window at the first request instead of aligning to `ts // window` (a different algorithm); sharing one counter between all keys; an off-by-one that lets `limit + 1` through; `limit = 0` must reject everything.",
        follow_up="Show a sequence that lets 2 x limit requests through in a short span (the boundary problem). Then solve 'Sliding Window Counter'.",
    ),
),
dict(
    id="sd-token-bucket",
    title="Token Bucket Rate Limiter",
    difficulty="Medium",
    pattern="Rate Limiting",
    kind="class",
    entry="TokenBucket",
    description=r"""
Implement a token bucket with lazy refill and explicit timestamps.

`TokenBucket(capacity, refill_per_second)`: every caller has their own bucket, which **starts full** with `capacity` tokens the first time the caller is seen. Tokens are added continuously at `refill_per_second` (fractions of a token accumulate), and the bucket never holds more than `capacity`.

- `allow(key, ts, cost)` → `True` if, after adding the tokens earned since the caller's previous call, the bucket holds at least `cost` tokens; `cost` tokens are then removed. Otherwise `False` and nothing is removed (all or nothing). In both cases the refill is applied and the caller's last-update time becomes `ts`.

`ts` is in seconds (an integer), and never decreases for a given key.

**Example:** `TokenBucket(4, 1)`: `allow("a",0,1)` four times → True x4; a fifth at `ts=0` → False; `allow("a",2,1)` → True (2 tokens refilled); `allow("a",2,2)` → False (only 1 left); `allow("a",100,4)` → True (refilled to the capacity of 4, not more); `allow("a",100,1)` → False.
""",
    starter='''class TokenBucket:
    def __init__(self, capacity: int, refill_per_second: float):
        pass

    def allow(self, key: str, ts: int, cost: int) -> bool:
        pass
''',
    solution='''class TokenBucket:
    def __init__(self, capacity, refill_per_second):
        self.capacity, self.rate = capacity, refill_per_second
        self.state = {}                          # key -> [tokens, last_ts]

    def allow(self, key, ts, cost):
        s = self.state.get(key)
        if s is None:
            s = self.state[key] = [float(self.capacity), ts]
        s[0] = min(self.capacity, s[0] + (ts - s[1]) * self.rate)
        s[1] = ts
        if s[0] >= cost:
            s[0] -= cost
            return True
        return False
''',
    tests=[
        _ops("TokenBucket", [4, 1], [("allow", ["a", 0, 1])] * 5 + [("allow", ["a", 2, 1]), ("allow", ["a", 2, 2]), ("allow", ["a", 100, 4]), ("allow", ["a", 100, 1])]),
        _ops("TokenBucket", [1, 1], [("allow", ["a", t, 1]) for t in (0, 0, 1, 1, 2, 10, 10)]),
        _ops("TokenBucket", [10, 2], [("allow", ["a", 0, 10]), ("allow", ["a", 1, 3]), ("allow", ["a", 1, 2]), ("allow", ["a", 2, 2]), ("allow", ["a", 3, 5]), ("allow", ["a", 6, 6])]),
        _ops("TokenBucket", [3, 0.5], [("allow", ["a", t, 1]) for t in (0, 0, 0, 0, 1, 2, 3, 4, 4, 6, 6)]),
        _ops("TokenBucket", [2, 1], [("allow", [k, t, 1]) for t in (0, 0, 0) for k in ("a", "b")] + [("allow", ["c", 50, 2]), ("allow", ["c", 50, 1])]),
        _ops("TokenBucket", [5, 1], [("allow", ["a", 0, 6]), ("allow", ["a", 0, 5]), ("allow", ["a", 3, 4]), ("allow", ["a", 3, 3]), ("allow", ["a", 3, 1])]),
        _ops("TokenBucket", [4, 2], [("allow", ["late", 1000, 4]), ("allow", ["late", 1000, 1]), ("allow", ["late", 1001, 2]), ("allow", ["late", 1001, 1])]),
        _ops("TokenBucket", [3, 1], [("allow", ["a", 0, 3]), ("allow", ["a", 1, 2]), ("allow", ["a", 2, 2]), ("allow", ["a", 3, 2])]),
        _ops("TokenBucket", [100, 10], [("allow", ["a", 0, 1])] * 101 + [("allow", ["a", 1, 10]), ("allow", ["a", 1, 1])]),
        _ops("TokenBucket", [2, 0.25], [("allow", ["a", t, 1]) for t in (0, 0, 2, 4, 4, 8, 12, 12, 13)]),
        _ops("TokenBucket", [5, 3], [("allow", ["a", t, 4]) for t in range(0, 12)]),
    ],
    examples=1,
    wrong_solutions=[
        '''class TokenBucket:
    def __init__(self, capacity, rate):
        self.capacity, self.rate, self.state = capacity, rate, {}
    def allow(self, key, ts, cost):
        s = self.state.get(key)
        if s is None:
            s = self.state[key] = [float(self.capacity), ts]
        s[0] = s[0] + (ts - s[1]) * self.rate
        s[1] = ts
        if s[0] >= cost:
            s[0] -= cost
            return True
        return False
''',
        '''class TokenBucket:
    def __init__(self, capacity, rate):
        self.capacity, self.rate, self.state = capacity, rate, {}
    def allow(self, key, ts, cost):
        s = self.state.get(key)
        if s is None:
            s = self.state[key] = [float(self.capacity), ts]
        if s[0] >= cost:
            s[0] -= cost
            ok = True
        else:
            ok = False
        s[0] = min(self.capacity, s[0] + (ts - s[1]) * self.rate)
        s[1] = ts
        return ok
''',
        '''class TokenBucket:
    def __init__(self, capacity, rate):
        self.capacity, self.rate, self.state = capacity, rate, {}
    def allow(self, key, ts, cost):
        s = self.state.get(key)
        if s is None:
            s = self.state[key] = [float(self.capacity), ts]
        s[0] = min(self.capacity, s[0] + int((ts - s[1]) * self.rate))
        s[1] = ts
        if s[0] >= cost:
            s[0] -= cost
            return True
        return False
''',
        '''class TokenBucket:
    def __init__(self, capacity, rate):
        self.capacity, self.rate, self.state = capacity, rate, {}
    def allow(self, key, ts, cost):
        s = self.state.get(key)
        if s is None:
            s = self.state[key] = [float(self.capacity), ts]
        s[0] = min(self.capacity, s[0] + (ts - s[1]) * self.rate)
        s[1] = ts
        s[0] -= cost
        return s[0] >= 0
''',
    ],
    guide=dict(
        prereqs="Lesson 'Design a rate limiter I', section on the token bucket and lazy refill.",
        intuition="You do not need a timer dripping tokens in. Remember how many tokens there were and when; on the next request, add `elapsed x rate`, cap at capacity, then try to spend.",
        hints=[
            "Per key store two values: tokens (a float) and the time of the last update.",
            "Refill first: `tokens = min(capacity, tokens + (ts - last) * rate)`, and always set `last = ts`.",
            "Only subtract `cost` if `tokens >= cost`. A rejected request must not take partial tokens.",
        ],
        brute_force="Simulate every second between calls adding `rate` tokens each time: O(elapsed seconds) per call, and wrong for fractional rates unless you keep fractions.",
        approach="""1. First sight of a key: `tokens = capacity`, `last = ts`.
2. `tokens = min(capacity, tokens + (ts - last) * rate)`; `last = ts`.
3. If `tokens >= cost`: subtract and return True, else return False.

**Dry run**, capacity 4, rate 1: four calls at t=0 leave 0 tokens; the fifth is rejected. At t=2: 0 + 2x1 = 2 tokens; cost 1 → True, 1 left; cost 2 → False (1 < 2). At t=100: 1 + 98 = 99, capped at 4; cost 4 → True, 0 left; cost 1 → False.""",
        complexity="Time O(1) per call; space O(number of keys).",
        pitfalls="Forgetting the cap (an idle caller would bank unlimited tokens); spending before refilling; truncating fractional tokens to integers (a rate of 0.5 would never refill on 1-second steps); deducting tokens from a rejected request.",
        follow_up="Return the seconds until the request would be allowed (for a Retry-After header): `(cost - tokens) / rate`.",
    ),
),
dict(
    id="sd-leaky-bucket",
    title="Leaky Bucket (Meter Form)",
    difficulty="Medium",
    pattern="Rate Limiting",
    kind="class",
    entry="LeakyBucket",
    description=r"""
Implement the leaky bucket as a meter.

`LeakyBucket(capacity, leak_per_second)`: the bucket has a water **level** that starts at 0. Water leaks out continuously at `leak_per_second` and the level never goes below 0. Each accepted request adds 1 unit.

- `offer(ts)` → first apply the leak for the time since the previous call, then: if `level + 1 <= capacity`, add 1 and return `True`; otherwise return `False` and add nothing.
- `queued(ts)` → apply the leak, then return how many **whole** requests are still in the bucket, that is the level rounded **up** to an integer (`math.ceil`). A request counts as present until it has fully drained.

`ts` is an integer number of seconds and never decreases.

**Example:** `LeakyBucket(3, 1)`: `offer(0)`→True, `offer(0)`→True, `offer(0)`→True, `offer(0)`→False, `queued(0)`→3, `offer(1)`→True (one unit leaked), `queued(3)`→1, `queued(10)`→0.
""",
    starter='''class LeakyBucket:
    def __init__(self, capacity: int, leak_per_second: float):
        pass

    def offer(self, ts: int) -> bool:
        pass

    def queued(self, ts: int) -> int:
        pass
''',
    solution='''import math

class LeakyBucket:
    def __init__(self, capacity, leak_per_second):
        self.capacity, self.rate = capacity, leak_per_second
        self.level, self.last = 0.0, 0

    def _leak(self, ts):
        self.level = max(0.0, self.level - (ts - self.last) * self.rate)
        self.last = ts

    def offer(self, ts):
        self._leak(ts)
        if self.level + 1 <= self.capacity:
            self.level += 1
            return True
        return False

    def queued(self, ts):
        self._leak(ts)
        return math.ceil(self.level)
''',
    tests=[
        _ops("LeakyBucket", [3, 1], [("offer", [0])] * 4 + [("queued", [0]), ("offer", [1]), ("queued", [3]), ("queued", [10])]),
        _ops("LeakyBucket", [1, 1], [("offer", [t]) for t in (0, 0, 1, 1, 2, 2)]),
        _ops("LeakyBucket", [2, 0.5], [("offer", [0]), ("offer", [0]), ("offer", [1]), ("queued", [1]), ("offer", [2]), ("offer", [2]), ("queued", [5]), ("queued", [6])]),
        _ops("LeakyBucket", [5, 2], [("offer", [0])] * 6 + [("queued", [1]), ("offer", [1]), ("offer", [1]), ("offer", [1]), ("queued", [2])]),
        _ops("LeakyBucket", [0, 1], [("offer", [0]), ("offer", [100]), ("queued", [100])]),
        _ops("LeakyBucket", [3, 1], [("queued", [0]), ("offer", [50]), ("queued", [50]), ("queued", [51]), ("offer", [51]), ("offer", [51]), ("offer", [51]), ("offer", [51])]),
        _ops("LeakyBucket", [4, 0.25], [("offer", [t]) for t in (0, 0, 0, 0, 0, 2, 4, 4, 8, 8, 8)] + [("queued", [8]), ("queued", [9])]),
        _ops("LeakyBucket", [2, 1], [("offer", [t]) for t in range(0, 10)] + [("queued", [9])]),
        _ops("LeakyBucket", [2, 1], [("offer", [t // 3]) for t in range(0, 30)]),
        _ops("LeakyBucket", [10, 5], [("offer", [0])] * 12 + [("queued", [0]), ("queued", [1]), ("queued", [2]), ("offer", [2])]),
        _ops("LeakyBucket", [3, 0.5], [("offer", [0]), ("queued", [1]), ("queued", [2]), ("offer", [3]), ("offer", [3]), ("offer", [3]), ("offer", [3]), ("queued", [4])]),
    ],
    examples=1,
    wrong_solutions=[
        '''import math
class LeakyBucket:
    def __init__(self, capacity, rate):
        self.capacity, self.rate, self.level, self.last = capacity, rate, 0.0, 0
    def _leak(self, ts):
        self.level = self.level - (ts - self.last) * self.rate
        self.last = ts
    def offer(self, ts):
        self._leak(ts)
        if self.level + 1 <= self.capacity:
            self.level += 1
            return True
        return False
    def queued(self, ts):
        self._leak(ts)
        return math.ceil(self.level)
''',
        '''import math
class LeakyBucket:
    def __init__(self, capacity, rate):
        self.capacity, self.rate, self.level, self.last = capacity, rate, 0.0, 0
    def _leak(self, ts):
        self.level = max(0.0, self.level - (ts - self.last) * self.rate)
        self.last = ts
    def offer(self, ts):
        self._leak(ts)
        if self.level < self.capacity:
            self.level += 1
            return True
        return False
    def queued(self, ts):
        self._leak(ts)
        return math.ceil(self.level)
''',
        '''import math
class LeakyBucket:
    def __init__(self, capacity, rate):
        self.capacity, self.rate, self.level, self.last = capacity, rate, 0.0, 0
    def _leak(self, ts):
        self.level = max(0.0, self.level - (ts - self.last) * self.rate)
        self.last = ts
    def offer(self, ts):
        self._leak(ts)
        if self.level + 1 <= self.capacity:
            self.level += 1
            return True
        return False
    def queued(self, ts):
        self._leak(ts)
        return int(self.level)
''',
    ],
    guide=dict(
        prereqs="Lesson 'Design a rate limiter I', section on the leaky bucket. `math.ceil`.",
        intuition="It is the token bucket upside down. Instead of tokens that refill and are spent, there is a level that drains and is added to. A request fits only if adding one unit does not overflow.",
        hints=[
            "Keep `level` (float) and `last` (time of the last update).",
            "Write one helper that applies the leak: `level = max(0, level - (ts - last) * rate)`.",
            "`offer` must test `level + 1 <= capacity`, not `level < capacity`: with a fractional level such as 2.5 and capacity 3, there is no room for a whole request.",
        ],
        brute_force="Keep a list of accepted requests and remove them one at a time as simulated seconds pass. That works for integer rates and is O(elapsed) per call.",
        approach="""1. `_leak(ts)`: subtract `(ts - last) * rate`, clamp at 0, set `last = ts`.
2. `offer`: leak, then accept if `level + 1 <= capacity`.
3. `queued`: leak, then `ceil(level)`.

**Dry run**, capacity 3, rate 1: three offers at t=0 raise the level to 3; the fourth sees 3 + 1 > 3: False. `offer(1)`: level 3 - 1 = 2, 2 + 1 <= 3: True, level 3. `queued(3)`: 3 - 2 = 1 → 1. `queued(10)`: clamped at 0 → 0.""",
        complexity="Time O(1) per call; space O(1).",
        pitfalls="Letting the level go negative after a long idle period (the bucket would then accept more than its capacity); testing `level < capacity` with fractional levels; rounding the level down in `queued`; capacity 0 must reject every request.",
        follow_up="Implement the queue form, where accepted requests are held and released at the leak rate, and return the time at which each request will be processed.",
    ),
),
dict(
    id="sd-sliding-window-log",
    title="Sliding Window Log Rate Limiter",
    difficulty="Medium",
    pattern="Rate Limiting",
    kind="class",
    entry="SlidingWindowLog",
    description=r"""
Implement the sliding window log algorithm.

`SlidingWindowLog(limit, window)` allows at most `limit` requests per caller in any window of `window` seconds ending at the current request. The window for a request at time `ts` is the half-open interval `(ts - window, ts]`: a logged request at exactly `ts - window` is **outside** it.

- `allow(key, ts)` → drop the caller's logged timestamps that are outside the window, then return `True` and log `ts` if fewer than `limit` timestamps remain; otherwise return `False`. **Rejected requests are not logged.**
- `count(key, ts)` → the number of logged requests of `key` inside the window `(ts - window, ts]`.

`ts` is an integer and never decreases for a key.

**Example:** `SlidingWindowLog(2, 10)`: `allow("a",1)`→True, `allow("a",5)`→True, `allow("a",10)`→False, `count("a",10)`→2, `allow("a",11)`→True (the request at 1 is now outside), `allow("a",12)`→False, `allow("a",15)`→True.
""",
    starter='''class SlidingWindowLog:
    def __init__(self, limit: int, window: int):
        pass

    def allow(self, key: str, ts: int) -> bool:
        pass

    def count(self, key: str, ts: int) -> int:
        pass
''',
    solution='''from collections import deque

class SlidingWindowLog:
    def __init__(self, limit, window):
        self.limit, self.window = limit, window
        self.logs = {}

    def _trim(self, key, ts):
        log = self.logs.setdefault(key, deque())
        while log and log[0] <= ts - self.window:
            log.popleft()
        return log

    def allow(self, key, ts):
        log = self._trim(key, ts)
        if len(log) < self.limit:
            log.append(ts)
            return True
        return False

    def count(self, key, ts):
        return len(self._trim(key, ts))
''',
    tests=[
        _ops("SlidingWindowLog", [2, 10], [("allow", ["a", 1]), ("allow", ["a", 5]), ("allow", ["a", 10]), ("count", ["a", 10]), ("allow", ["a", 11]), ("allow", ["a", 12]), ("allow", ["a", 15])]),
        _ops("SlidingWindowLog", [5, 60], [("allow", ["u", t]) for t in (58, 58, 59, 59, 59, 60, 60, 61, 117, 118, 118, 119, 119, 119, 120)]),
        _ops("SlidingWindowLog", [1, 1], [("allow", ["a", t]) for t in (0, 0, 1, 1, 2)]),
        _ops("SlidingWindowLog", [3, 5], [("allow", [k, t]) for t in (0, 1, 2, 3) for k in ("x", "y")] + [("count", ["x", 5]), ("count", ["y", 6]), ("count", ["z", 6])]),
        _ops("SlidingWindowLog", [0, 5], [("allow", ["a", 0]), ("allow", ["a", 100]), ("count", ["a", 100])]),
        _ops("SlidingWindowLog", [2, 3], [("allow", ["a", t]) for t in range(0, 15)]),
        _ops("SlidingWindowLog", [3, 10], [("allow", ["a", 0])] * 10 + [("count", ["a", 9]), ("allow", ["a", 9]), ("allow", ["a", 10]), ("allow", ["a", 10]), ("allow", ["a", 10]), ("allow", ["a", 10])]),
        _ops("SlidingWindowLog", [2, 10], [("count", ["a", 0]), ("allow", ["a", 0]), ("count", ["a", 9]), ("count", ["a", 10]), ("allow", ["a", 10]), ("allow", ["a", 10]), ("allow", ["a", 10])]),
        _ops("SlidingWindowLog", [4, 7], [("allow", ["a", t // 2]) for t in range(0, 40)]),
        _ops("SlidingWindowLog", [50, 100], [("allow", ["a", t]) for t in range(0, 60)] + [("count", ["a", 99]), ("count", ["a", 100]), ("count", ["a", 120]), ("allow", ["a", 120])]),
        _ops("SlidingWindowLog", [2, 5], [("allow", ["a", 0]), ("allow", ["a", 0]), ("allow", ["a", 4]), ("allow", ["a", 4]), ("allow", ["a", 5]), ("allow", ["a", 5]), ("allow", ["a", 5])]),
    ],
    examples=1,
    wrong_solutions=[
        '''from collections import deque
class SlidingWindowLog:
    def __init__(self, limit, window):
        self.limit, self.window, self.logs = limit, window, {}
    def _trim(self, key, ts):
        log = self.logs.setdefault(key, deque())
        while log and log[0] < ts - self.window:
            log.popleft()
        return log
    def allow(self, key, ts):
        log = self._trim(key, ts)
        if len(log) < self.limit:
            log.append(ts)
            return True
        return False
    def count(self, key, ts):
        return len(self._trim(key, ts))
''',
        '''from collections import deque
class SlidingWindowLog:
    def __init__(self, limit, window):
        self.limit, self.window, self.logs = limit, window, {}
    def _trim(self, key, ts):
        log = self.logs.setdefault(key, deque())
        while log and log[0] <= ts - self.window:
            log.popleft()
        return log
    def allow(self, key, ts):
        log = self._trim(key, ts)
        log.append(ts)
        return len(log) <= self.limit
    def count(self, key, ts):
        return len(self._trim(key, ts))
''',
        '''class SlidingWindowLog:
    def __init__(self, limit, window):
        self.limit, self.window, self.state = limit, window, {}
    def allow(self, key, ts):
        wid = ts // self.window
        s = self.state.get(key)
        if s is None or s[0] != wid:
            s = self.state[key] = [wid, 0]
        if s[1] < self.limit:
            s[1] += 1
            return True
        return False
    def count(self, key, ts):
        s = self.state.get(key)
        return s[1] if s and s[0] == ts // self.window else 0
''',
    ],
    guide=dict(
        prereqs="Lesson 'Design a rate limiter I', section on the sliding window log. `collections.deque`.",
        intuition="Remember when each allowed request happened. Before deciding, forget the ones that have slid out of the last `window` seconds; what is left is exactly the number of requests in the window.",
        hints=[
            "Use one deque of timestamps per key; timestamps arrive in order, so the oldest is always at the left.",
            "A timestamp `t` is outside the window when `t <= ts - window`.",
            "Append `ts` only when you return True.",
        ],
        brute_force="Keep a plain list and count with a comprehension on each call: O(n) per call and the list never shrinks. The deque with trimming is amortised O(1).",
        approach="""1. `_trim`: pop from the left while `log[0] <= ts - window`.
2. `allow`: trim; if `len(log) < limit`, append and return True, else False.
3. `count`: trim and return the length.

**Dry run**, limit 2, window 10: at 1 and 5 → log [1,5]. At 10: `10 - 10 = 0`, nothing to drop, 2 entries: False. At 11: `11 - 10 = 1`, drop 1 → [5], allow → [5,11]. At 12: False. At 15: drop 5 → [11], allow.""",
        complexity="Amortised O(1) per call (each timestamp is appended once and removed once); space O(limit) per key.",
        pitfalls="Using `<` instead of `<=` when trimming (keeps a request at exactly `ts - window`); logging rejected requests, which locks out a retrying caller; using fixed-window logic and calling it sliding.",
        follow_up="Memory is O(limit) per key. For a limit of 10,000 per hour and a million callers that is prohibitive: see 'Sliding Window Counter'.",
    ),
),
dict(
    id="sd-sliding-window-counter",
    title="Sliding Window Counter Rate Limiter",
    difficulty="Medium",
    pattern="Rate Limiting",
    kind="class",
    entry="SlidingWindowCounter",
    description=r"""
Implement the sliding window counter, which approximates a sliding window using two fixed-window counters per caller.

`SlidingWindowCounter(limit, window)`. Windows are aligned to zero: window number `w = ts // window`, and `elapsed = ts - w * window` is how far `ts` is into the current window.

For a caller, let `current` be the number of allowed requests in window `w` and `previous` the number allowed in window `w - 1` (0 if there were none, or if the caller's last activity was in an older window). The estimated number of requests in the sliding window is

`estimate = current + previous * (window - elapsed) / window`

- `allow(key, ts)` → `True` if `estimate + 1 <= limit`, and the request is counted in `current`; otherwise `False` and nothing is counted.

To avoid floating-point surprises use the equivalent integer test:
`current * window + previous * (window - elapsed) + window <= limit * window`.

`ts` is an integer and never decreases for a key.

**Example:** `SlidingWindowCounter(5, 60)`: five calls at `ts=58` → all True. `allow("a",60)` → False (`0 + 5 * 60/60 + 1 > 5`). `allow("a",75)` → True (`0 + 5 * 0.75 + 1 = 4.75`). `allow("a",80)` → False (`1 + 5 * 40/60 + 1 = 5.33`). `allow("a",90)` → True (`1 + 2.5 + 1 = 4.5`).
""",
    starter='''class SlidingWindowCounter:
    def __init__(self, limit: int, window: int):
        pass

    def allow(self, key: str, ts: int) -> bool:
        pass
''',
    solution='''class SlidingWindowCounter:
    def __init__(self, limit, window):
        self.limit, self.window = limit, window
        self.state = {}                         # key -> [window_id, current, previous]

    def allow(self, key, ts):
        wid = ts // self.window
        s = self.state.get(key)
        if s is None:
            s = self.state[key] = [wid, 0, 0]
        elif s[0] != wid:
            s[2] = s[1] if wid == s[0] + 1 else 0
            s[1] = 0
            s[0] = wid
        elapsed = ts - wid * self.window
        if s[1] * self.window + s[2] * (self.window - elapsed) + self.window <= self.limit * self.window:
            s[1] += 1
            return True
        return False
''',
    tests=[
        _ops("SlidingWindowCounter", [5, 60], [("allow", ["a", 58])] * 5 + [("allow", ["a", t]) for t in (60, 75, 80, 90)]),
        _ops("SlidingWindowCounter", [5, 60], [("allow", ["a", t]) for t in (58, 58, 59, 59, 59, 60, 60, 75, 90, 105, 119, 119, 120, 121)]),
        _ops("SlidingWindowCounter", [1, 10], [("allow", ["a", t]) for t in (0, 5, 10, 15, 19, 20, 29, 30)]),
        _ops("SlidingWindowCounter", [10, 100], [("allow", ["a", 99])] * 11 + [("allow", ["a", t]) for t in (100, 110, 110, 120, 150, 150, 150, 150, 150, 150)]),
        _ops("SlidingWindowCounter", [3, 10], [("allow", ["a", 0])] * 4 + [("allow", ["a", 25])] * 4),
        _ops("SlidingWindowCounter", [3, 10], [("allow", [k, t]) for t in (9, 9, 10, 12) for k in ("x", "y")]),
        _ops("SlidingWindowCounter", [0, 10], [("allow", ["a", 0]), ("allow", ["a", 100])]),
        _ops("SlidingWindowCounter", [4, 4], [("allow", ["a", t]) for t in range(0, 24)]),
        _ops("SlidingWindowCounter", [2, 10], [("allow", ["a", t]) for t in (9, 9, 10, 14, 15, 19, 20, 20, 24, 25)]),
        _ops("SlidingWindowCounter", [100, 60], [("allow", ["a", 59])] * 100 + [("allow", ["a", 60 + t]) for t in range(0, 60, 3)]),
        _ops("SlidingWindowCounter", [6, 30], [("allow", ["a", t // 2]) for t in range(0, 140)]),
        _ops("SlidingWindowCounter", [2, 5], [("allow", ["a", 4]), ("allow", ["a", 4]), ("allow", ["a", 5]), ("allow", ["a", 7]), ("allow", ["a", 8]), ("allow", ["a", 14]), ("allow", ["a", 14]), ("allow", ["a", 14])]),
    ],
    examples=1,
    wrong_solutions=[
        '''class SlidingWindowCounter:
    def __init__(self, limit, window):
        self.limit, self.window, self.state = limit, window, {}
    def allow(self, key, ts):
        wid = ts // self.window
        s = self.state.get(key)
        if s is None or s[0] != wid:
            s = self.state[key] = [wid, 0]
        if s[1] < self.limit:
            s[1] += 1
            return True
        return False
''',
        '''class SlidingWindowCounter:
    def __init__(self, limit, window):
        self.limit, self.window, self.state = limit, window, {}
    def allow(self, key, ts):
        wid = ts // self.window
        s = self.state.get(key)
        if s is None:
            s = self.state[key] = [wid, 0, 0]
        elif s[0] != wid:
            s[2], s[1], s[0] = s[1], 0, wid
        elapsed = ts - wid * self.window
        if s[1] * self.window + s[2] * (self.window - elapsed) + self.window <= self.limit * self.window:
            s[1] += 1
            return True
        return False
''',
        '''class SlidingWindowCounter:
    def __init__(self, limit, window):
        self.limit, self.window, self.state = limit, window, {}
    def allow(self, key, ts):
        wid = ts // self.window
        s = self.state.get(key)
        if s is None:
            s = self.state[key] = [wid, 0, 0]
        elif s[0] != wid:
            s[2] = s[1] if wid == s[0] + 1 else 0
            s[1], s[0] = 0, wid
        elapsed = ts - wid * self.window
        if s[1] * self.window + s[2] * elapsed + self.window <= self.limit * self.window:
            s[1] += 1
            return True
        return False
''',
        '''class SlidingWindowCounter:
    def __init__(self, limit, window):
        self.limit, self.window, self.state = limit, window, {}
    def allow(self, key, ts):
        wid = ts // self.window
        s = self.state.get(key)
        if s is None:
            s = self.state[key] = [wid, 0, 0]
        elif s[0] != wid:
            s[2] = s[1] if wid == s[0] + 1 else 0
            s[1], s[0] = 0, wid
        elapsed = ts - wid * self.window
        s[1] += 1
        return (s[1] - 1) * self.window + s[2] * (self.window - elapsed) + self.window <= self.limit * self.window
''',
    ],
    guide=dict(
        prereqs="Lesson 'Design a rate limiter I', section on the sliding window counter; the Fixed Window problem.",
        intuition="The sliding window covers all of the current fixed window so far and the tail end of the previous one. Assume the previous window's requests were spread evenly, so the share still inside the sliding window is the fraction of that window not yet slid past.",
        hints=[
            "Per key keep the window number, the current count and the previous count.",
            "When the window number advances by exactly one, the current count becomes the previous count. When it advances by more, both are zero.",
            "The weight of the previous window is `(window - elapsed) / window`. Multiply the whole inequality by `window` to stay in integers.",
        ],
        brute_force="The sliding window log gives the exact answer with O(limit) memory per key. This algorithm trades a small error for O(1) memory.",
        approach="""1. `wid = ts // window`. Roll the counters if `wid` changed (by one: `previous = current`; by more: `previous = 0`), then `current = 0`.
2. `elapsed = ts - wid * window`.
3. Allow iff `current*window + previous*(window - elapsed) + window <= limit*window`; if allowed, `current += 1`.

**Dry run**, limit 5, window 60: five requests at 58 → current 5. At 60: wid 1, previous 5, current 0, elapsed 0: `0 + 5*60 + 60 = 360 > 300`: False. At 75: elapsed 15: `0 + 5*45 + 60 = 285 <= 300`: True, current 1. At 80: `60 + 5*40 + 60 = 320 > 300`: False. At 90: `60 + 150 + 60 = 270`: True.""",
        complexity="Time O(1) per call; space O(1) per key.",
        pitfalls="Carrying `previous` forward after skipping more than one window; weighting by `elapsed` instead of `window - elapsed`; counting rejected requests; float comparisons at exact boundaries.",
        follow_up="Construct a request pattern where this estimate differs from the exact sliding window log, and state which way the error goes.",
    ),
),
]
