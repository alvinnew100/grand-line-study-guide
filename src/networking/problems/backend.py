_FNV_DOC = r"""
```
h = 2166136261
for each byte b of the UTF-8 encoding of the string:
    h = h XOR b
    h = (h * 16777619) mod 2^32
```
"""

_CH_SOL = '''def consistent_hash(servers, replicas, keys):
    def fnv(s):
        h = 2166136261
        for b in s.encode("utf-8"):
            h ^= b
            h = (h * 16777619) & 0xFFFFFFFF
        return h

    ring = sorted((fnv(s + "#" + str(i)), s) for s in servers for i in range(replicas))
    out = []
    for k in keys:
        if not ring:
            out.append("")
            continue
        idx = bisect.bisect_left(ring, (fnv(k), ""))
        if idx == len(ring):
            idx = 0
        out.append(ring[idx][1])
    return out
'''

_SERVERS = ["cache-a", "cache-b", "cache-c", "cache-d"]
_KEYS = ["user:%d" % i for i in range(60)]


PROBLEMS = [
dict(
    id="net-lb-weighted-round-robin",
    title="Smooth Weighted Round-Robin Load Balancer",
    difficulty="Medium",
    pattern="Load Balancing",
    entry="weighted_round_robin",
    description=r"""
A load balancer spreads requests over backends in proportion to integer `weights` (backend `i` has weight
`weights[i] >= 0`; at least one weight is positive unless the list is empty). Plain weighted round-robin
would send bursts (`A A A A A B`); the *smooth* variant used by nginx interleaves them.

Every backend has a running value `current`, initially 0. For each request:

1. add each backend's weight to its `current`;
2. pick the backend with the largest `current` (ties → the lowest index);
3. subtract the **sum of all weights** from the chosen backend's `current`.

Return the list of chosen backend indices for `n` requests. With an empty `weights` list return `[]`.
With all weights equal this is ordinary round-robin.

**Example:** `weights = [5, 1, 1]`, `n = 7` → `[0, 0, 1, 0, 2, 0, 0]`
""",
    starter='''def weighted_round_robin(weights: list, n: int) -> list:
    pass
''',
    solution='''def weighted_round_robin(weights, n):
    if not weights:
        return []
    total = sum(weights)
    cur = [0] * len(weights)
    out = []
    for _ in range(n):
        best = 0
        for i, w in enumerate(weights):
            cur[i] += w
            if cur[i] > cur[best]:
                best = i
        cur[best] -= total
        out.append(best)
    return out
''',
    tests=[
        [[5, 1, 1], 7],
        [[], 5],
        [[1, 1, 1], 7],
        [[3], 4],
        [[1, 1, 1], 0],
        [[2, 1], 6],
        [[0, 1, 0, 2], 9],
        [[4, 2, 1], 14],
        [[1, 2, 3, 4], 20],
        [[7, 7], 5],
        [[10, 1], 22],
        [[3, 5, 2, 8, 1], 190],
        [[1, 100], 30],
    ],
    examples=1,
    wrong_solutions=[
        '''def weighted_round_robin(weights, n):
    order = [i for i, w in enumerate(weights) for _ in range(w)]
    return [order[k % len(order)] for k in range(n)] if order else []
''',
        '''def weighted_round_robin(weights, n):
    if not weights:
        return []
    total = sum(weights)
    cur = [0] * len(weights)
    out = []
    for _ in range(n):
        best = 0
        for i, w in enumerate(weights):
            cur[i] += w
            if cur[i] >= cur[best]:
                best = i
        cur[best] -= total
        out.append(best)
    return out
''',
    ],
    guide=dict(
        prereqs="The lesson *Load balancers, reverse proxies and health checks*.",
        intuition="Think of `current` as accumulated credit. Everyone earns credit at their own rate each turn; whoever has the most gets served and pays the whole pot back. Heavy backends earn fast so they are served often, but paying the pot stops them being served many times in a row.",
        hints=[
            "You need one integer of state per backend plus the total weight.",
            "Do the 'add weight' step for **all** backends before choosing.",
            "Break ties towards the lowest index by using a strict `>` while scanning left to right.",
        ],
        brute_force="Expand the weights into a repeating list (`[0,0,0,0,0,1,2]`) and cycle through it. The proportions are right but the order is bursty and does not match the specification; memory also grows with the weights.",
        approach="""1. `total = sum(weights)`, `current = [0]*k`.
2. Per request: add weights, find the arg-max, subtract `total`, record.

**Dry run** `[5,1,1]`, total 7:

| request | current after adding | chosen | current after subtracting |
|---|---|---|---|
| 1 | 5, 1, 1 | 0 | -2, 1, 1 |
| 2 | 3, 2, 2 | 0 | -4, 2, 2 |
| 3 | 1, 3, 3 | 1 | 1, -4, 3 |
| 4 | 6, -3, 4 | 0 | -1, -3, 4 |
| 5 | 4, -2, 5 | 2 | 4, -2, -2 |
| 6 | 9, -1, -1 | 0 | 2, -1, -1 |
| 7 | 7, 0, 0 | 0 | 0, 0, 0 |

After `total` requests every `current` is back to 0 and the pattern repeats.""",
        complexity="Time O(n·k) for k backends; space O(k).",
        pitfalls="Subtracting the backend's own weight rather than the total. Choosing before all credits are added. Using `>=`, which sends ties to the highest index. A zero-weight backend must never be chosen.",
        follow_up="Combine with health checks (skip unhealthy backends and exclude their weight from the total) or with slow-start, where a newly added backend's effective weight ramps up.",
    ),
),
dict(
    id="net-lb-least-connections",
    title="Least-Connections Load Balancer with Health State",
    difficulty="Medium",
    pattern="Load Balancing",
    entry="least_connections",
    description=r"""
Simulate a least-connections balancer over servers `0 .. num_servers - 1`, all initially healthy with zero
active connections. `events` are processed in order:

- `["req", id]`: a new request with a unique `id`. Assign it to the **healthy** server with the fewest active
  connections (ties → lowest index); that server's count rises by one. If no server is healthy the request is
  rejected with `-1` and occupies nothing.
- `["done", id]`: the request finishes; its server's count drops by one. Ignore ids that were rejected,
  already finished, or never seen.
- `["down", s]` / `["up", s]`: server `s` fails or passes its health check. A down server receives no new
  requests, but its existing connections stay counted until they finish.

Return the list of results for the `"req"` events only (server index or `-1`), in order.

**Example:** `num_servers = 2`, `events = [["req",1],["req",2],["req",3],["done",1],["req",4]]` → `[0, 1, 0, 0]`
""",
    starter='''def least_connections(num_servers: int, events: list) -> list:
    pass
''',
    solution='''def least_connections(num_servers, events):
    active = [0] * num_servers
    healthy = [True] * num_servers
    where = {}
    out = []
    for kind, x in events:
        if kind == "req":
            best = -1
            for s in range(num_servers):
                if healthy[s] and (best == -1 or active[s] < active[best]):
                    best = s
            if best != -1:
                active[best] += 1
                where[x] = best
            out.append(best)
        elif kind == "done":
            if x in where:
                active[where.pop(x)] -= 1
        elif kind == "down":
            healthy[x] = False
        else:
            healthy[x] = True
    return out
''',
    tests=[
        [2, [["req", 1], ["req", 2], ["req", 3], ["done", 1], ["req", 4]]],
        [3, []],
        [0, [["req", 1], ["done", 1]]],
        [1, [["req", 1], ["req", 2], ["done", 1], ["req", 3]]],
        [3, [["req", 1], ["req", 2], ["req", 3], ["req", 4], ["done", 2], ["req", 5], ["done", 3], ["done", 4], ["req", 6]]],
        [3, [["down", 0], ["req", 1], ["req", 2], ["up", 0], ["req", 3], ["req", 4]]],
        [2, [["down", 0], ["down", 1], ["req", 1], ["done", 1], ["up", 1], ["req", 2], ["done", 1], ["req", 3]]],
        [2, [["req", 1], ["req", 2], ["down", 0], ["req", 3], ["req", 4], ["up", 0], ["req", 5], ["req", 6], ["req", 7]]],
        [2, [["req", 1], ["done", 1], ["done", 1], ["done", 99], ["req", 2], ["req", 3]]],
        [3, [["req", 1], ["req", 2], ["req", 3], ["done", 3], ["done", 1], ["req", 4], ["req", 5], ["req", 6]]],
        [4, [["req", i] for i in range(10)] + [["done", i] for i in (0, 4, 8, 1)] + [["req", i] for i in range(10, 16)]],
        [5, [(["down", i % 5] if i % 11 == 3 else ["up", (i * 3) % 5] if i % 13 == 5 else ["done", i - 7] if i % 3 == 0 else ["req", i]) for i in range(150)]],
    ],
    examples=1,
    wrong_solutions=[
        '''def least_connections(num_servers, events):
    active = [0] * num_servers
    healthy = [True] * num_servers
    where, out = {}, []
    for kind, x in events:
        if kind == "req":
            cands = [s for s in range(num_servers) if healthy[s]]
            if not cands:
                out.append(-1)
                continue
            best = min(cands, key=lambda s: active[s])
            active[best] += 1
            where[x] = best
            out.append(best)
        elif kind == "done":
            if x in where:
                active[where[x]] -= 1
        elif kind == "down":
            healthy[x] = False
            active[x] = 0
        else:
            healthy[x] = True
    return out
''',
        '''def least_connections(num_servers, events):
    out, k = [], 0
    healthy = [True] * num_servers
    for kind, x in events:
        if kind == "req":
            cands = [s for s in range(num_servers) if healthy[s]]
            if not cands:
                out.append(-1)
            else:
                out.append(cands[k % len(cands)])
                k += 1
        elif kind == "down":
            healthy[x] = False
        elif kind == "up":
            healthy[x] = True
    return out
''',
    ],
    guide=dict(
        prereqs="The lesson *Load balancers, reverse proxies and health checks*; dictionaries.",
        intuition="Round-robin assumes every request costs the same. When some requests are slow, the fair thing is to look at who is busiest right now. So the balancer tracks open connections per server and a map from request to server so it knows whose count to decrement.",
        hints=[
            "Three pieces of state: `active[s]`, `healthy[s]`, and `request id -> server`.",
            "Remove the id from the map when it completes so a duplicate `done` is harmless.",
            "A server going down does not reset its count: those connections are still draining.",
        ],
        brute_force="On every request recount each server's active connections by scanning the list of all open requests: O(R) per request. Keeping the counters up to date makes each event O(k) for k servers.",
        approach="""1. `req`: scan the healthy servers for the minimum count (strict `<` keeps the lowest index on ties); record and increment.
2. `done`: pop the id from the map and decrement that server.
3. `down` / `up`: flip the flag only.

**Dry run** (example): req 1 → server 0 (0,0 → 1,0). req 2 → server 1 (1,1). req 3 → tie → server 0 (2,1). done 1 → (1,1). req 4 → tie → server 0.""",
        complexity="Time O(E·k) with a linear scan (a heap keyed by `(active, index)` gives O(log k) per event); space O(k + open requests).",
        pitfalls="Decrementing twice for a repeated `done`. Zeroing the count of a failed server (it then looks idle the moment it recovers and gets flooded). Counting rejected requests. Forgetting the lowest-index tie-break.",
        follow_up="Power of two choices: pick two random servers and use the less loaded one. It achieves nearly the same balance with O(1) work and no global scan, and avoids the herd effect when many balancers share stale load data.",
    ),
),
dict(
    id="net-consistent-hash",
    title="Consistent-Hash Ring Lookup",
    difficulty="Medium",
    pattern="Load Balancing",
    entry="consistent_hash",
    description=(r"""
Map keys to servers with a consistent-hash ring so that adding or removing one server only moves a small
share of the keys.

Use the 32-bit **FNV-1a** hash, defined as
""" + _FNV_DOC + r"""
**Ring.** Every server `s` is placed on the ring `replicas` times, at positions
`fnv(s + "#" + str(i))` for `i = 0 .. replicas - 1` (virtual nodes).

**Lookup.** A key `k` belongs to the virtual node with the smallest position that is `>= fnv(k)`; if there
is none, wrap around to the virtual node with the smallest position overall. If two virtual nodes share a
position, the one whose server name is alphabetically smaller comes first.

Return the server name for each key in `keys`. If `servers` is empty return `""` for every key.

**Example:** `servers = ["a", "b"]`, `replicas = 1`, `keys = ["x"]`:
`fnv("a#0") = 4037809751`, `fnv("b#0") = 559601318`, `fnv("x") = 4245442695`. No position is `>=` the key's
hash, so wrap to the smallest position → `["b"]`.
"""),
    starter='''def consistent_hash(servers: list, replicas: int, keys: list) -> list:
    pass
''',
    solution=_CH_SOL,
    tests=[
        [["a", "b"], 1, ["x"]],
        [[], 3, ["k1", "k2"]],
        [["only"], 1, ["k1", "k2", "k3"]],
        [["a", "b"], 1, []],
        [_SERVERS, 1, _KEYS],
        [_SERVERS, 8, _KEYS],
        [_SERVERS[:3], 8, _KEYS],
        [_SERVERS + ["cache-e"], 8, _KEYS],
        [_SERVERS, 50, ["session-%04d" % i for i in range(300)]],
        [["n%d" % i for i in range(30)], 3, ["object/%d.png" % i for i in range(200)]],
        [["x", "y", "z"], 2, ["", "a", "ab", "abc", "ü", "日本"]],
        [["a", "b"], 1, ["a#0", "b#0"]],
    ],
    examples=1,
    wrong_solutions=[
        '''def consistent_hash(servers, replicas, keys):
    def fnv(s):
        h = 2166136261
        for b in s.encode("utf-8"):
            h ^= b
            h = (h * 16777619) & 0xFFFFFFFF
        return h
    if not servers:
        return [""] * len(keys)
    return [servers[fnv(k) % len(servers)] for k in keys]
''',
        '''def consistent_hash(servers, replicas, keys):
    def fnv(s):
        h = 2166136261
        for b in s.encode("utf-8"):
            h ^= b
            h = (h * 16777619) & 0xFFFFFFFF
        return h
    ring = sorted((fnv(s + "#" + str(i)), s) for s in servers for i in range(replicas))
    out = []
    for k in keys:
        if not ring:
            out.append("")
            continue
        idx = bisect.bisect_left(ring, (fnv(k), ""))
        out.append(ring[min(idx, len(ring) - 1)][1])
    return out
''',
        '''def consistent_hash(servers, replicas, keys):
    def fnv(s):
        h = 2166136261
        for b in s.encode("utf-8"):
            h = (h * 16777619) & 0xFFFFFFFF
            h ^= b
        return h
    ring = sorted((fnv(s + "#" + str(i)), s) for s in servers for i in range(replicas))
    out = []
    for k in keys:
        if not ring:
            out.append("")
            continue
        idx = bisect.bisect_left(ring, (fnv(k), ""))
        out.append(ring[idx % len(ring)][1])
    return out
''',
    ],
    guide=dict(
        prereqs="Hashing, binary search (`bisect`); the lesson *Load balancers, reverse proxies and health checks*.",
        intuition="With `hash(key) % N`, changing N reshuffles almost every key. Instead, hash servers and keys onto the same circle and give each key to the next server clockwise. Removing a server only hands its arc to its neighbour. Virtual nodes cut each server's territory into many small arcs so the load evens out.",
        hints=[
            "Build a sorted list of `(position, server)` tuples once.",
            "`bisect_left(ring, (h, \"\"))` finds the first tuple whose position is at least `h`, because the empty string sorts before every name.",
            "If the index equals `len(ring)`, wrap to index 0.",
        ],
        brute_force="For each key scan every virtual node to find the smallest position ≥ the hash: O(K·S·R). Sorting once and binary searching gives O(log(S·R)) per key.",
        approach="""1. Implement FNV-1a exactly (XOR first, then multiply, masking to 32 bits).
2. `ring = sorted((fnv(f"{s}#{i}"), s) ...)`.
3. For each key: `idx = bisect_left(ring, (fnv(key), ""))`, wrap, answer `ring[idx][1]`.

**Dry run** (example): ring = `[(559601318, "b"), (4037809751, "a")]`. `fnv("x") = 4245442695` is beyond both, `idx = 2 = len(ring)` → wrap to 0 → `"b"`.""",
        complexity="Build O(S·R·log(S·R)); each lookup O(L + log(S·R)) for a key of length L; space O(S·R).",
        pitfalls="Forgetting the wrap-around (index error or wrong owner for high hashes). Multiplying before XOR-ing gives FNV-1, a different function. Forgetting the 32-bit mask. Falling back to modulo hashing, which defeats the purpose.",
        follow_up="Measure how many keys move when a server is added (compare the 4-server and 5-server tests). Look at bounded-load consistent hashing, rendezvous hashing and Maglev hashing as alternatives.",
    ),
),
dict(
    id="net-token-bucket",
    title="Token-Bucket Rate Limiter",
    difficulty="Medium",
    pattern="Rate Limiting",
    entry="token_bucket",
    description=r"""
Implement a token-bucket limiter with explicit timestamps.

The bucket holds at most `capacity` tokens and starts **full** at time 0. Tokens are added continuously at
`rate` tokens per second, i.e. `rate * dt / 1000` tokens over `dt` milliseconds (fractions count), never
exceeding `capacity`.

`requests` is a list of `[t_ms, cost]` with non-decreasing integer timestamps. For each request:

1. refill for the time elapsed since the previous request (or since time 0);
2. if the bucket holds at least `cost` tokens, remove them and allow the request (`True`);
3. otherwise deny it (`False`) and remove nothing.

Return the list of booleans. `capacity`, `rate` and `cost` are non-negative integers.

**Hint on precision:** count in thousandths of a token (`rate * dt` milli-tokens per `dt` ms) so that all
arithmetic stays in integers.

**Example:** `capacity = 3`, `rate = 1`, `requests = [[0,1],[0,1],[0,1],[0,1],[500,1],[1000,1]]`
→ `[True, True, True, False, False, True]`
""",
    starter='''def token_bucket(capacity: int, rate: int, requests: list) -> list:
    pass
''',
    solution='''def token_bucket(capacity, rate, requests):
    cap = capacity * 1000
    tokens = cap
    last = 0
    out = []
    for t, cost in requests:
        tokens = min(cap, tokens + (t - last) * rate)
        last = t
        need = cost * 1000
        if tokens >= need:
            tokens -= need
            out.append(True)
        else:
            out.append(False)
    return out
''',
    tests=[
        [3, 1, [[0, 1], [0, 1], [0, 1], [0, 1], [500, 1], [1000, 1]]],
        [5, 2, []],
        [0, 10, [[0, 1], [1000, 1], [5000, 0]]],
        [1, 0, [[0, 1], [10000, 1]]],
        [10, 5, [[0, 10], [1000, 5], [1000, 1], [1200, 1], [3000, 10], [3001, 1]]],
        [2, 3, [[0, 2], [333, 1], [334, 1], [667, 1]]],
        [4, 1, [[0, 5], [0, 4], [3999, 4], [4000, 4]]],
        [5, 1, [[100000, 5], [100000, 1], [101000, 1]]],
        [3, 1, [[0, 3], [900, 1], [1100, 1], [1900, 1], [2100, 1]]],
        [1, 7, [[i * 143, 1] for i in range(40)]],
        [20, 10, [[i * 37, 1 + i % 3] for i in range(200)]],
        [6, 2, [[0, 6], [500, 1], [500, 1], [1500, 2], [1500, 1], [4500, 6], [4500, 1]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def token_bucket(capacity, rate, requests):
    cap = capacity * 1000
    tokens, last, out = cap, 0, []
    for t, cost in requests:
        tokens = tokens + (t - last) * rate
        last = t
        need = cost * 1000
        if tokens >= need:
            tokens -= need
            out.append(True)
        else:
            out.append(False)
    return out
''',
        '''def token_bucket(capacity, rate, requests):
    tokens, last, out = capacity, 0, []
    for t, cost in requests:
        tokens = min(capacity, tokens + (t - last) * rate // 1000)
        last = t
        if tokens >= cost:
            tokens -= cost
            out.append(True)
        else:
            out.append(False)
    return out
''',
    ],
    guide=dict(
        prereqs="The lesson *Timeouts, retries, pools, rate limits and idempotency*.",
        intuition="Tokens are permission slips that drip into a bucket at the sustained rate. A full bucket lets a client burst; an empty one makes it wait for the drip. You never need a timer: when a request arrives, work out how many tokens *would* have dripped in since last time.",
        hints=[
            "Lazy refill: `tokens += elapsed * rate`, then clamp to `capacity`.",
            "Update `last` on **every** request, allowed or denied, since the refill has been applied either way.",
            "Work in milli-tokens (multiply capacity and cost by 1000) to avoid floating-point comparisons.",
        ],
        brute_force="Advance a simulated clock one millisecond at a time, adding `rate/1000` tokens per tick. Time proportional to the timestamp range rather than the number of requests, and floating-point drift creeps in.",
        approach="""1. `tokens = capacity·1000`, `last = 0`.
2. Per request: `tokens = min(cap, tokens + (t − last)·rate)`, `last = t`; compare with `cost·1000`.

**Dry run** `capacity 3, rate 1`: three requests at t=0 drain 3000 → 0. Fourth at t=0: 0 < 1000 → deny. t=500: +500 → 500 < 1000 → deny (the 500 stays). t=1000: +500 → 1000 → allow.""",
        complexity="Time O(n), space O(1) besides the output.",
        pitfalls="Not capping at capacity (a quiet period then permits an unbounded burst). Integer-dividing the refill each time, which throws away fractions of a token and under-serves steady clients. Charging tokens for denied requests. Starting the bucket empty.",
        follow_up="Per-client buckets in a dict with idle eviction; a distributed version in Redis with an atomic script; returning a `Retry-After` value computed from the token deficit.",
    ),
),
dict(
    id="net-leaky-bucket",
    title="Leaky-Bucket Traffic Shaper",
    difficulty="Medium",
    pattern="Rate Limiting",
    entry="leaky_bucket",
    description=r"""
A leaky-bucket shaper smooths bursts: packets wait in a bounded queue and leave at a steady pace, at most one
every `interval` milliseconds.

`arrivals` is a non-decreasing list of arrival times (ms). Process packets in order. For a packet arriving
at time `t`:

- its earliest possible departure is `d = t` if no packet has been accepted yet, otherwise
  `d = max(t, last_departure + interval)` where `last_departure` is the departure time of the most recently
  accepted packet;
- let `waiting` be the number of accepted packets whose departure time is **greater than** `t` (still queued);
- if `d > t` (the packet must wait) and `waiting >= queue_size`, the packet is **dropped**: record `-1`;
- otherwise it is accepted and departs at `d`: record `d`.

Return the list of recorded values.

**Example:** `queue_size = 2`, `interval = 100`, `arrivals = [0, 0, 0, 0, 250]` → `[0, 100, 200, -1, 300]`
""",
    starter='''def leaky_bucket(queue_size: int, interval: int, arrivals: list) -> list:
    pass
''',
    solution='''def leaky_bucket(queue_size, interval, arrivals):
    queued = collections.deque()
    last = None
    out = []
    for t in arrivals:
        while queued and queued[0] <= t:
            queued.popleft()
        d = t if last is None else max(t, last + interval)
        if d > t and len(queued) >= queue_size:
            out.append(-1)
            continue
        last = d
        queued.append(d)
        out.append(d)
    return out
''',
    tests=[
        [2, 100, [0, 0, 0, 0, 250]],
        [5, 100, []],
        [0, 100, [0, 50, 100, 150, 200]],
        [1, 100, [0, 0, 0, 100, 100]],
        [3, 10, [0, 100, 200, 300]],
        [3, 0, [5, 5, 5, 5, 5, 5]],
        [2, 100, [50, 60, 70, 80, 149, 150, 151]],
        [10, 1000, [7] * 15],
        [1, 100, [0, 99, 100, 199, 200, 201]],
        [4, 25, [i * 10 for i in range(60)]],
        [2, 100, [0, 0, 0, 0, 0, 1000, 1000, 1000, 1000]],
        [6, 40, [(i * i * 7) % 500 + i * 20 for i in range(120)] and sorted((i * i * 7) % 500 + i * 20 for i in range(120))],
    ],
    examples=1,
    wrong_solutions=[
        '''def leaky_bucket(queue_size, interval, arrivals):
    last, out, pending = None, [], []
    for t in arrivals:
        pending = [d for d in pending if d > t]
        d = t if last is None else max(t, last + interval)
        if len(pending) >= queue_size:
            out.append(-1)
            continue
        last = d
        pending.append(d)
        out.append(d)
    return out
''',
        '''def leaky_bucket(queue_size, interval, arrivals):
    last, out, pending = None, [], []
    for t in arrivals:
        pending = [d for d in pending if d > t]
        d = t if last is None else max(t, last + interval)
        if d > t and len(pending) >= queue_size:
            out.append(-1)
            last = d
            continue
        last = d
        pending.append(d)
        out.append(d)
    return out
''',
    ],
    guide=dict(
        prereqs="Problem *Token-Bucket Rate Limiter*; queues (`collections.deque`).",
        intuition="Where a token bucket lets bursts through, a leaky bucket irons them flat: output is a metronome. Each accepted packet reserves the next free tick; the queue bound limits how far into the future reservations may stretch.",
        hints=[
            "The departure time of a packet depends only on the previous accepted packet's departure time.",
            "Before judging a new packet, discard queued departures that are `<= t`: those packets have left.",
            "A packet that can leave immediately (`d == t`) never needs a queue slot, even when `queue_size` is 0.",
        ],
        brute_force="Keep a list of all accepted departure times and count those greater than `t` for every arrival: O(n²). Because departures are increasing, a deque that drops expired entries from the front gives amortised O(1).",
        approach="""1. Pop departures `<= t` from the front of the deque.
2. Compute `d`.
3. If the packet must wait and the queue is full, drop; otherwise record `d`, append it, and update `last`.

**Dry run** `queue 2, interval 100, arrivals 0,0,0,0,250`: first leaves at 0. Second: d=100, waiting 0 → accept. Third: d=200, waiting 1 → accept. Fourth: d=300, waiting 2 ≥ 2 → drop. At 250 the departures at 0, 100, 200 are gone; d = max(250, 300) = 300, waiting 0 → accept.""",
        complexity="Time O(n) amortised, space O(queue_size).",
        pitfalls="Advancing `last` for a dropped packet (it reserved nothing). Counting the packet currently departing as waiting. Dropping a packet that could leave at once because the queue size is zero. Confusing this with the token bucket: the leaky bucket never emits two packets closer than `interval`.",
        follow_up="Implement the leaky bucket *as a meter* (a counter that drains at a constant rate and rejects when it would overflow) and show it is equivalent to a token bucket with the same capacity.",
    ),
),
dict(
    id="net-backoff-jitter",
    title="Exponential Backoff Schedule with Jitter",
    difficulty="Easy",
    pattern="Resilience",
    entry="backoff_schedule",
    description=r"""
Compute the delays (in milliseconds) a client waits before each of `attempts` retries.

For retry `i` (0-based) the exponential ceiling is `c = min(cap, base * 2^i)`. Randomness is supplied as
`rand`, a list of integers in `[0, 99]` (percentages) with at least `attempts` entries; retry `i` uses `r = rand[i]`.
All divisions are integer (floor) divisions.

`mode` selects the strategy:

- `"none"`: `delay = c`
- `"full"`: `delay = c * r // 100`
- `"equal"`: `half = c // 2`, `delay = half + (c - half) * r // 100`
- `"decorrelated"`: ignores `c`. With `prev = base` before the first retry,
  `delay = min(cap, base + (3 * prev - base) * r // 100)`, then `prev = delay`.

Return the list of delays.

**Example:** `base = 100`, `cap = 1000`, `attempts = 5`, `mode = "none"`, `rand = [0,0,0,0,0]` → `[100, 200, 400, 800, 1000]`

**Example:** same with `mode = "full"`, `rand = [50, 10, 99, 0, 75]` → `[50, 20, 396, 0, 750]`
""",
    starter='''def backoff_schedule(base: int, cap: int, attempts: int, mode: str, rand: list) -> list:
    pass
''',
    solution='''def backoff_schedule(base, cap, attempts, mode, rand):
    out = []
    prev = base
    for i in range(attempts):
        r = rand[i]
        c = min(cap, base * (2 ** i))
        if mode == "none":
            d = c
        elif mode == "full":
            d = c * r // 100
        elif mode == "equal":
            half = c // 2
            d = half + (c - half) * r // 100
        else:
            d = min(cap, base + (3 * prev - base) * r // 100)
            prev = d
        out.append(d)
    return out
''',
    tests=[
        [100, 1000, 5, "none", [0, 0, 0, 0, 0]],
        [100, 1000, 5, "full", [50, 10, 99, 0, 75]],
        [100, 1000, 0, "full", []],
        [100, 1000, 5, "equal", [50, 10, 99, 0, 75]],
        [100, 1000, 6, "decorrelated", [50, 10, 99, 0, 75, 99]],
        [100, 50, 4, "none", [1, 2, 3, 4]],
        [1, 10 ** 9, 40, "none", [0] * 40],
        [250, 30000, 12, "full", [(i * 37 + 11) % 100 for i in range(12)]],
        [250, 30000, 12, "equal", [(i * 37 + 11) % 100 for i in range(12)]],
        [250, 30000, 12, "decorrelated", [(i * 37 + 11) % 100 for i in range(12)]],
        [7, 100, 8, "equal", [99] * 8],
        [7, 100, 8, "equal", [0] * 8],
        [50, 2000, 10, "decorrelated", [99] * 10],
        [50, 2000, 10, "decorrelated", [0] * 10],
        [3, 1000, 9, "full", [33, 66, 99, 1, 50, 50, 50, 99, 99, 12, 13]],
    ],
    examples=2,
    wrong_solutions=[
        '''def backoff_schedule(base, cap, attempts, mode, rand):
    out, prev = [], base
    for i in range(attempts):
        r = rand[i]
        c = base * (2 ** i)
        if mode == "none":
            d = c
        elif mode == "full":
            d = c * r // 100
        elif mode == "equal":
            half = c // 2
            d = half + (c - half) * r // 100
        else:
            d = min(cap, base + (3 * prev - base) * r // 100)
            prev = d
        out.append(d)
    return out
''',
        '''def backoff_schedule(base, cap, attempts, mode, rand):
    out, prev = [], base
    for i in range(attempts):
        r = rand[i]
        c = min(cap, base * (2 ** i))
        if mode == "none":
            d = c
        elif mode == "full":
            d = c * r // 100
        elif mode == "equal":
            d = c // 2 + c * r // 100
        else:
            d = min(cap, base + (3 * base - base) * r // 100)
        out.append(d)
    return out
''',
    ],
    guide=dict(
        prereqs="The lesson *Timeouts, retries, pools, rate limits and idempotency*.",
        intuition="Doubling the wait gives an overloaded service room to recover. But if a thousand clients failed at the same instant and all double in lockstep, they come back as synchronised waves. Jitter spreads each wave across the interval; the modes differ only in how much of the interval is randomised.",
        hints=[
            "Compute the capped ceiling first; three of the four modes are one-liners on top of it.",
            "`equal` keeps half the ceiling as a guaranteed minimum and randomises only the other half.",
            "`decorrelated` carries state from one retry to the next: the previous delay.",
        ],
        brute_force="There is nothing slower to write; the brute-force mistake is conceptual: retrying immediately in a tight loop, or with a fixed delay, which is what turns a brief outage into a retry storm.",
        approach="""1. Loop `i` from 0 to `attempts − 1`, `c = min(cap, base·2^i)`.
2. Apply the formula for the mode with `r = rand[i]`.

**Dry run** `base 100, cap 1000`, full jitter, `rand = [50,10,99,0,75]`: ceilings 100, 200, 400, 800, 1000 → `100·50//100 = 50`, `200·10//100 = 20`, `400·99//100 = 396`, `0`, `750`.""",
        complexity="Time O(attempts), space O(attempts).",
        pitfalls="Forgetting the cap (after 30 doublings a 100 ms base exceeds a day). Adding jitter on top of the full ceiling in `equal` mode, exceeding the cap. Using the base instead of the previous delay in `decorrelated`. In production also bound the *number* of retries and retry only idempotent operations.",
        follow_up="Add a retry budget (retries may be at most 10% of requests) and honour a server-supplied `Retry-After`. Compare the total work done by clients under no jitter and full jitter in a simulation.",
    ),
),
]
