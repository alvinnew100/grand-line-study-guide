_PRICING = {"per_million_requests": 0.20, "per_gb_second": 0.0000166667, "free_requests": 1000000, "free_gb_seconds": 400000}
_NO_FREE = {"per_million_requests": 0.20, "per_gb_second": 0.0000166667, "free_requests": 0, "free_gb_seconds": 0}
_ITEMS = (
    [{"pk": "user#1", "sk": "order#%03d" % i, "size": 1500, "status": "paid" if i % 2 else "open"} for i in range(10)]
    + [{"pk": "user#2", "sk": "order#%03d" % i, "size": 5000, "status": "paid"} for i in range(3)]
    + [{"pk": "user#3", "sk": "profile", "size": 300, "status": "open"}]
)
_STRATS = [["backup-restore", 1440, 1440, 100], ["pilot-light", 60, 15, 600],
           ["warm-standby", 10, 1, 2500], ["multi-site", 0, 0, 9000]]


def _q(op, **kw):
    r = {"op": op, "pk": None, "sk_lo": None, "sk_hi": None, "filter": None, "consistent": True}
    r.update(kw)
    return r


PROBLEMS = [
dict(
    id="aws-lambda-cost",
    title="Lambda Monthly Cost",
    difficulty="Easy",
    pattern="Serverless",
    entry="lambdaCost",
    compare="float",
    description=r"""
Lambda bills two things: the **number of requests** and the **compute time**, measured in
*GB-seconds* (memory configured in GB × seconds of execution).

`lambdaCost(invocations, avg_ms, memory_mb, pricing)`:

- `invocations`: number of invocations in the month; `avg_ms`: average billed duration in
  milliseconds (integer); `memory_mb`: configured memory.
- `gb_seconds = invocations × (avg_ms / 1000) × (memory_mb / 1024)`.
- `pricing` has `per_million_requests`, `per_gb_second`, `free_requests` and `free_gb_seconds`.
  The free amounts are subtracted first and can never make a part negative.
- `cost = max(0, invocations − free_requests) / 1,000,000 × per_million_requests
          + max(0, gb_seconds − free_gb_seconds) × per_gb_second`.

Return the cost in USD (float, not rounded).

**Example:** 5,000,000 invocations of 200 ms at 512 MB with `0.20` per million, `0.0000166667` per
GB-second, 1,000,000 free requests and 400,000 free GB-seconds → GB-seconds = 500,000 →
`4 × 0.20 + 100000 × 0.0000166667 = 2.4667`.
""",
    starter='''def lambdaCost(invocations, avg_ms, memory_mb, pricing):
    pass
''',
    solution='''def lambdaCost(invocations, avg_ms, memory_mb, pricing):
    gb_seconds = invocations * (avg_ms / 1000) * (memory_mb / 1024)
    req = max(0, invocations - pricing["free_requests"]) / 1e6 * pricing["per_million_requests"]
    compute = max(0, gb_seconds - pricing["free_gb_seconds"]) * pricing["per_gb_second"]
    return req + compute
''',
    tests=[
        [5000000, 200, 512, _PRICING],
        [100000, 100, 128, _PRICING],
        [0, 100, 128, _PRICING],
        [1000000, 3200, 128, _PRICING],
        [1000001, 3200, 128, _PRICING],
        [500000, 1000, 1024, _PRICING],
        [30000000, 50, 256, _NO_FREE],
        [30000000, 50, 1024, _NO_FREE],
        [2000000, 120, 10240, _PRICING],
        [100, 900000, 3008, _NO_FREE],
        [10 ** 9, 1, 128, _PRICING],
    ],
    examples=2,
    tolerance=1e-6,
    wrong_solutions=[
        '''def lambdaCost(invocations, avg_ms, memory_mb, pricing):
    gb_seconds = invocations * (avg_ms / 1000) * (memory_mb / 1024)
    return (invocations - pricing["free_requests"]) / 1e6 * pricing["per_million_requests"] + \\
           (gb_seconds - pricing["free_gb_seconds"]) * pricing["per_gb_second"]
''',
        '''def lambdaCost(invocations, avg_ms, memory_mb, pricing):
    gb_seconds = invocations * (avg_ms / 1000) * (memory_mb / 1000)
    req = max(0, invocations - pricing["free_requests"]) / 1e6 * pricing["per_million_requests"]
    return req + max(0, gb_seconds - pricing["free_gb_seconds"]) * pricing["per_gb_second"]
''',
    ],
    guide=dict(
        prereqs="The Lambda lesson: the pricing model (requests plus GB-seconds).",
        intuition="Two meters, each with its own free allowance. Compute each meter, subtract the allowance with a floor at zero, multiply by its price, add.",
        hints=["Convert milliseconds to seconds and megabytes to gigabytes (÷ 1024) before multiplying.",
               "Use `max(0, …)` on each part separately — unused free requests do not offset compute.",
               "The request price is per million."],
        brute_force="Not applicable.",
        approach="Dry run: 1,000,000 invocations × 3.2 s × 0.125 GB = 400,000 GB-seconds — exactly the free allowance, and exactly the free request count → cost 0. One more invocation costs 0.0000002 for the request plus 0.4 GB-seconds of compute.",
        complexity="O(1).",
        pitfalls="Negative parts when usage is below the free tier; dividing memory by 1000; forgetting that doubling memory doubles the GB-seconds for the same duration.",
    ),
),
dict(
    id="aws-lambda-concurrency",
    title="Lambda Concurrency and Cold Starts",
    difficulty="Medium",
    pattern="Serverless",
    entry="lambdaStats",
    description=r"""
Lambda runs each concurrent request in its own **execution environment**. A new environment needs a
**cold start**; a finished environment stays warm for a while and can serve the next request without
one. An account-level **concurrency limit** caps the number of busy environments.

`lambdaStats(invocations, idle_timeout, limit)`:

- `invocations`: list of `[start_ms, duration_ms]`, sorted by `start_ms` (ties keep list order).
  An invocation that runs occupies its environment during `[start, start + duration)`.
- For each invocation, in order:
  1. A **warm** environment is one that is free (`free_at <= start`) and has not been idle for more
     than `idle_timeout` (`start - free_at <= idle_timeout`). Environments idle for longer are gone.
     If warm environments exist, reuse the one that became free **most recently** (largest
     `free_at`).
  2. Otherwise, if the number of busy environments (`free_at > start`) is below `limit`, create a new
     environment: one cold start.
  3. Otherwise the invocation is **throttled**: it does not run at all.
- Return `[cold_starts, peak_concurrency, throttled]`, where peak concurrency is the largest number
  of invocations running at the same instant.

**Example:** `[[0,100],[50,100],[120,10],[5000,10]]`, idle timeout 1000, limit 10 → the first two
overlap (2 cold starts, peak 2), the third reuses a warm environment, the fourth arrives after every
environment has expired (cold) → `[3, 2, 0]`.
""",
    starter='''def lambdaStats(invocations, idle_timeout, limit):
    pass
''',
    solution='''def lambdaStats(invocations, idle_timeout, limit):
    envs = []            # free_at time of each live environment
    cold = peak = throttled = 0
    for start, dur in invocations:
        envs = [f for f in envs if f > start or start - f <= idle_timeout]
        warm = [f for f in envs if f <= start]
        busy = len(envs) - len(warm)
        if warm:
            envs.remove(max(warm))
        elif busy < limit:
            cold += 1
        else:
            throttled += 1
            continue
        envs.append(start + dur)
        peak = max(peak, sum(1 for f in envs if f > start))
    return [cold, peak, throttled]
''',
    tests=[
        [[[0, 100], [50, 100], [120, 10], [5000, 10]], 1000, 10],
        [[[0, 100], [100, 100], [200, 100]], 0, 10],
        [[], 1000, 10],
        [[[0, 1000], [1, 1000], [2, 1000], [3, 1000]], 1000, 2],
        [[[0, 10], [10, 10], [20, 10], [1021, 10]], 1000, 5],
        [[[0, 10], [10, 10], [20, 10], [1030, 10]], 1000, 5],
        [[[0, 100], [0, 100], [0, 100], [100, 100], [100, 100], [100, 100]], 50, 3],
        [[[0, 100], [10, 10], [30, 10], [100, 10], [2000, 5]], 1905, 100],
        [[[0, 100], [10, 10], [30, 10], [100, 10], [2000, 5]], 1890, 100],
        [[[0, 0], [0, 0], [0, 0]], 100, 1],
        [[[i * 10, 95] for i in range(200)], 500, 1000],
        [[[i * 10, 95] for i in range(200)], 500, 4],
        [[[0, 500], [100, 50], [200, 50], [300, 50], [400, 50], [10000, 500], [10000, 500]], 60000, 3],
    ],
    examples=2,
    wrong_solutions=[
        '''def lambdaStats(invocations, idle_timeout, limit):
    envs, cold, peak = [], 0, 0
    for start, dur in invocations:
        warm = [f for f in envs if f <= start]
        if warm:
            envs.remove(max(warm))
        else:
            cold += 1
        envs.append(start + dur)
        peak = max(peak, sum(1 for f in envs if f > start))
    return [cold, peak, 0]
''',
        '''def lambdaStats(invocations, idle_timeout, limit):
    envs = []
    cold = peak = throttled = 0
    for start, dur in invocations:
        envs = [f for f in envs if f > start or start - f < idle_timeout]
        warm = [f for f in envs if f < start]
        busy = len(envs) - len(warm)
        if warm:
            envs.remove(max(warm))
        elif busy < limit:
            cold += 1
        else:
            throttled += 1
            continue
        envs.append(start + dur)
        peak = max(peak, sum(1 for f in envs if f > start))
    return [cold, peak, throttled]
''',
    ],
    guide=dict(
        prereqs="The Lambda lesson: execution environments, cold starts, concurrency limits and throttling.",
        intuition="Keep one number per live environment: the time it becomes free. Each arrival first forgets expired environments, then prefers a warm one, then a new one if the limit allows.",
        hints=["An environment is busy at `start` when `free_at > start`, warm when `free_at <= start` and `start - free_at <= idle_timeout`.",
               "Drop expired environments before counting anything.",
               "Peak concurrency can be measured right after each successful start: count the environments with `free_at > start`."],
        brute_force="Checking every millisecond of the timeline for the number of running invocations works but is O(time range). Event-based accounting is O(n × environments).",
        approach="Dry run with limit 2 and four 1000 ms invocations at 0, 1, 2, 3: first → cold (busy 0 < 2); second → cold (busy 1 < 2); third → no warm, busy 2 = limit → throttled; fourth → throttled. Result `[2, 2, 2]`.",
        complexity="O(n × e) time for n invocations and e live environments (a heap would give O(n log e)); O(e) space.",
        pitfalls="Reusing an environment that is still busy; using `<` instead of `<=` at the exact boundary (an environment that frees at t can serve a request at t, and one idle for exactly `idle_timeout` is still warm); counting throttled invocations as running; reusing the oldest warm environment instead of the most recently freed.",
    ),
),
dict(
    id="aws-dynamodb-capacity",
    title="DynamoDB Capacity Units",
    difficulty="Easy",
    pattern="DynamoDB",
    entry="capacityUnits",
    description=r"""
In provisioned mode you tell DynamoDB how many **read capacity units** (RCU) and **write capacity
units** (WCU) a table needs.

- One RCU = one **strongly consistent** read per second of an item up to **4 KB**. Larger items need
  one unit per started 4 KB. An **eventually consistent** read costs half; a **transactional** read
  costs double.
- One WCU = one write per second of an item up to **1 KB**; one unit per started 1 KB. A
  **transactional** write costs double.

`capacityUnits(item_bytes, reads_per_s, writes_per_s, mode)` with `mode` in `"eventual"`, `"strong"`,
`"transactional"` (the mode applies to reads; writes are doubled only in transactional mode).
1 KB = 1024 bytes. An item of 0 bytes still counts as one unit per operation.

Return `[rcu, wcu]` as integers; when the eventual-consistency halving gives a fraction, round the
**total** up.

**Example:** 6,000-byte items, 100 reads/s, 20 writes/s, `"eventual"` → each read needs 2 units,
halved → 100 RCU; each write needs 6 units → 120 WCU → `[100, 120]`.
""",
    starter='''def capacityUnits(item_bytes, reads_per_s, writes_per_s, mode):
    pass
''',
    solution='''def capacityUnits(item_bytes, reads_per_s, writes_per_s, mode):
    read_units = max(1, -(-item_bytes // 4096))
    write_units = max(1, -(-item_bytes // 1024))
    rcu = reads_per_s * read_units
    wcu = writes_per_s * write_units
    if mode == "eventual":
        rcu = -(-rcu // 2)
    elif mode == "transactional":
        rcu *= 2
        wcu *= 2
    return [rcu, wcu]
''',
    tests=[
        [6000, 100, 20, "eventual"],
        [6000, 100, 20, "strong"],
        [6000, 100, 20, "transactional"],
        [4096, 10, 10, "strong"],
        [4097, 10, 10, "strong"],
        [1024, 7, 7, "eventual"],
        [1025, 7, 7, "eventual"],
        [0, 5, 5, "strong"],
        [100, 0, 0, "transactional"],
        [100, 1, 1, "eventual"],
        [400000, 3, 3, "eventual"],
        [12288, 33, 1, "eventual"],
    ],
    examples=2,
    wrong_solutions=[
        '''def capacityUnits(item_bytes, reads_per_s, writes_per_s, mode):
    rcu = reads_per_s * item_bytes / 4096
    wcu = writes_per_s * item_bytes / 1024
    if mode == "eventual":
        rcu /= 2
    elif mode == "transactional":
        rcu *= 2; wcu *= 2
    return [int(-(-rcu // 1)), int(-(-wcu // 1))]
''',
        '''def capacityUnits(item_bytes, reads_per_s, writes_per_s, mode):
    read_units = max(1, -(-item_bytes // 4096))
    write_units = max(1, -(-item_bytes // 1024))
    if mode == "eventual":
        read_units = max(1, read_units // 2)
    elif mode == "transactional":
        read_units *= 2; write_units *= 2
    return [reads_per_s * read_units, writes_per_s * write_units]
''',
    ],
    guide=dict(
        prereqs="The DynamoDB lesson: capacity modes, RCU and WCU.",
        intuition="Round **each item** up to its block size first (4 KB for reads, 1 KB for writes), multiply by the rate, then apply the mode's factor to the total.",
        hints=["`-(-n // block)` is integer ceiling division; force a minimum of 1.",
               "Halve the total RCU for eventual reads and round that total up.",
               "Transactional doubles both reads and writes."],
        brute_force="Not applicable.",
        approach="Dry run: 1,025-byte items, 7 reads and 7 writes per second, eventual. Read block: 1 unit each → 7 → halved 3.5 → 4 RCU. Write: 1,025 bytes spans 2 KB → 14 WCU. Result `[4, 14]`.",
        complexity="O(1).",
        pitfalls="Multiplying the rate by the fractional size before rounding (10 reads of 4,097 bytes is 20 units, not 11); halving per item instead of in total; forgetting writes use 1 KB blocks.",
    ),
),
dict(
    id="aws-gsi-projection",
    title="GSI Projection Check",
    difficulty="Easy",
    pattern="DynamoDB",
    entry="missingAttributes",
    description=r"""
A **global secondary index** (GSI) is a copy of part of a table, organised under a different key. The
copy contains only the attributes that were **projected** into it — and a query on a GSI can never
fetch the rest from the base table.

`missingAttributes(table_keys, index, requested)`:

- `table_keys`: list with the table's partition key and, optionally, sort key attribute names.
- `index`: `{"keys": [index partition key, optional index sort key], "projection": "KEYS_ONLY" |
  "INCLUDE" | "ALL", "include": [names]}` (`include` is only meaningful for `"INCLUDE"`).
- `requested`: attribute names the query wants back.

Attributes available in the index: the index keys and the table keys (always), plus the `include`
list for `INCLUDE`, or everything for `ALL`.

Return the sorted list of requested attributes that the index **cannot** return (duplicates removed).
An empty list means the index covers the query.

**Example:** table keys `["order_id"]`, index keys `["customer_id","created_at"]`, `KEYS_ONLY`,
requested `["order_id","total","status"]` → `["status","total"]`
""",
    starter='''def missingAttributes(table_keys, index, requested):
    pass
''',
    solution='''def missingAttributes(table_keys, index, requested):
    if index["projection"] == "ALL":
        return []
    available = set(table_keys) | set(index["keys"])
    if index["projection"] == "INCLUDE":
        available |= set(index.get("include") or [])
    return sorted(set(requested) - available)
''',
    tests=[
        [["order_id"], {"keys": ["customer_id", "created_at"], "projection": "KEYS_ONLY", "include": []}, ["order_id", "total", "status"]],
        [["order_id"], {"keys": ["customer_id", "created_at"], "projection": "INCLUDE", "include": ["total"]}, ["order_id", "total", "status"]],
        [["order_id"], {"keys": ["customer_id", "created_at"], "projection": "ALL", "include": []}, ["order_id", "total", "status", "anything"]],
        [["pk", "sk"], {"keys": ["gsi1pk"], "projection": "KEYS_ONLY", "include": ["ignored"]}, ["sk", "pk", "gsi1pk"]],
        [["pk", "sk"], {"keys": ["gsi1pk"], "projection": "KEYS_ONLY", "include": ["ignored"]}, ["ignored"]],
        [["pk"], {"keys": ["email"], "projection": "INCLUDE", "include": ["name", "plan"]}, []],
        [["pk"], {"keys": ["email"], "projection": "INCLUDE", "include": ["name", "plan"]}, ["z", "a", "z", "name", "a"]],
        [["pk"], {"keys": ["email"], "projection": "INCLUDE", "include": ["name", "plan"]}, ["Email", "Name"]],
        [["id", "ts"], {"keys": ["status", "ts"], "projection": "INCLUDE", "include": []}, ["id", "ts", "status", "payload"]],
        [["id"], {"keys": ["a", "b"], "projection": "KEYS_ONLY"}, ["b", "c", "a", "id"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def missingAttributes(table_keys, index, requested):
    if index["projection"] == "ALL":
        return []
    available = set(index["keys"]) | set(index.get("include") or [])
    return sorted(set(requested) - available)
''',
        '''def missingAttributes(table_keys, index, requested):
    available = set(table_keys) | set(index["keys"])
    if index["projection"] == "INCLUDE":
        available |= set(index.get("include") or [])
    return [r for r in requested if r not in available]
''',
    ],
    guide=dict(
        prereqs="The DynamoDB lesson: global secondary indexes and projections. Python sets.",
        intuition="Build the set of attributes that physically live in the index, subtract it from the requested set.",
        hints=["`ALL` short-circuits to an empty answer.", "Table keys are always projected, even with `KEYS_ONLY`.",
               "Only honour `include` when the projection type is `INCLUDE`."],
        brute_force="A nested loop comparing each requested name with each available name is O(r × a); sets make it O(r + a).",
        approach="Dry run: table keys `[pk, sk]`, index keys `[gsi1pk]`, KEYS_ONLY with a stray include list `[ignored]`. Available = {pk, sk, gsi1pk}. Requesting `[ignored]` → missing `[ignored]`, because the include list does not apply to KEYS_ONLY.",
        complexity="O(r + a) time and space, plus O(m log m) to sort the m missing names.",
        pitfalls="Forgetting that table keys are always in the index; honouring `include` for `KEYS_ONLY`; returning duplicates or unsorted output; case-insensitive comparison (attribute names are case-sensitive).",
    ),
),
dict(
    id="aws-dynamodb-hot-partition",
    title="Hot Partition Key Detector",
    difficulty="Medium",
    pattern="DynamoDB",
    entry="hotKeys",
    description=r"""
DynamoDB spreads items over partitions by hashing the **partition key**. If a few key values receive
most of the traffic, their partitions are throttled while the rest of the table sits idle — a **hot
partition**. Given a sample of requests, find the hot keys and suggest whether write sharding helps.

`hotKeys(accesses, threshold_pct, shards)`:

- `accesses`: list of partition-key values (strings), one per sampled request.
- A key is **hot** when its share of all requests is **strictly greater** than `threshold_pct`
  percent (use integer arithmetic: `count × 100 > threshold_pct × total`).
- Write sharding appends a suffix `#0 … #(shards-1)` to a key, splitting its traffic evenly over
  `shards` new keys. For each hot key compute `after = ceil(count / shards)`, the traffic of its
  busiest shard; sharding **fixes** the key when `after × 100 <= threshold_pct × total`.

Return a list of `[key, count, fixed]` for the hot keys, sorted by `count` descending and then by key
ascending; `fixed` is a boolean. Return `[]` when `accesses` is empty.

**Example:** `["a","a","a","b","c","a","d","a"]`, threshold 25, shards 2 → `a` has 5 of 8 (62.5 %);
after sharding its busiest shard gets 3 of 8 (37.5 %) → `[["a", 5, False]]`.
""",
    starter='''def hotKeys(accesses, threshold_pct, shards):
    pass
''',
    solution='''def hotKeys(accesses, threshold_pct, shards):
    total = len(accesses)
    counts = {}
    for k in accesses:
        counts[k] = counts.get(k, 0) + 1
    out = []
    for k, c in counts.items():
        if c * 100 > threshold_pct * total:
            after = -(-c // shards)
            out.append([k, c, after * 100 <= threshold_pct * total])
    out.sort(key=lambda x: (-x[1], x[0]))
    return out
''',
    tests=[
        [["a", "a", "a", "b", "c", "a", "d", "a"], 25, 2],
        [["a", "a", "a", "b", "c", "a", "d", "a"], 25, 4],
        [[], 10, 4],
        [["x"], 50, 10],
        [["a", "b", "c", "d"], 25, 2],
        [["a", "b", "c", "d"], 24, 2],
        [["b"] * 30 + ["a"] * 30 + ["c"] * 40, 29, 2],
        [["tenant-1"] * 900 + ["tenant-%d" % i for i in range(2, 102)], 10, 10],
        [["tenant-1"] * 900 + ["tenant-%d" % i for i in range(2, 102)], 10, 9],
        [["k%d" % (i % 50) for i in range(5000)], 2, 1],
        [["k%d" % (i % 50) for i in range(5000)], 1, 2],
        [["2026-11-21"] * 70 + ["2026-11-20"] * 20 + ["2026-11-19"] * 10, 15, 5],
    ],
    examples=2,
    wrong_solutions=[
        '''def hotKeys(accesses, threshold_pct, shards):
    total = len(accesses)
    counts = {}
    for k in accesses:
        counts[k] = counts.get(k, 0) + 1
    out = []
    for k, c in counts.items():
        if c * 100 >= threshold_pct * total:
            out.append([k, c, (c // shards) * 100 <= threshold_pct * total])
    out.sort(key=lambda x: (-x[1], x[0]))
    return out
''',
        '''def hotKeys(accesses, threshold_pct, shards):
    total = len(accesses)
    counts = {}
    for k in accesses:
        counts[k] = counts.get(k, 0) + 1
    out = [[k, c, -(-c // shards) * 100 <= threshold_pct * total] for k, c in counts.items() if c * 100 > threshold_pct * total]
    return sorted(out)
''',
    ],
    guide=dict(
        prereqs="The DynamoDB lesson: partition keys, hot partitions and write sharding. Counting with a dictionary.",
        intuition="Count, compare each share with the threshold without floating point, then ask whether dividing the count by the shard number brings the busiest piece under the same threshold.",
        hints=["Cross-multiply instead of dividing: `count × 100 > threshold × total`.",
               "The busiest shard after an even split has `ceil(count / shards)` requests.",
               "Sort with the key `(-count, key)`."],
        brute_force="Calling `accesses.count(k)` for every distinct key is O(n × distinct); a dictionary pass is O(n).",
        approach="Dry run: 900 requests for tenant-1 and 100 other tenants once each (total 1000), threshold 10 %, 10 shards. tenant-1: 90 % > 10 % → hot. After sharding: ceil(900 / 10) = 90 → 9 % ≤ 10 % → fixed. With 9 shards: 100 → 10 % ≤ 10 % → still fixed (the fix test is not strict).",
        complexity="O(n + h log h) time for n accesses and h hot keys; O(distinct keys) space.",
        pitfalls="Using `>=` for the hot test; floor instead of ceiling for the shard split; floating-point percentages at the boundary; sorting by key only.",
    ),
),
dict(
    id="aws-dynamodb-query-scan",
    title="Query vs Scan Read Cost",
    difficulty="Medium",
    pattern="DynamoDB",
    entry="readCost",
    description=r"""
A DynamoDB **Query** reads only the items of one partition key (optionally a range of sort keys). A
**Scan** reads the whole table. In both cases a **filter** is applied *after* the items are read, so
it reduces what is returned but not what is paid for.

`readCost(items, request)`:

- `items`: list of dicts with `"pk"`, `"sk"` (strings), `"size"` (bytes) and other attributes.
- `request`: `{"op": "query"|"scan", "pk": str or null, "sk_lo": str or null, "sk_hi": str or null,
  "filter": [attribute, value] or null, "consistent": bool}`.
- Items **read**:
  - `scan`: every item;
  - `query`: items with `pk == request["pk"]`, and if `sk_lo`/`sk_hi` are given, with
    `sk_lo <= sk <= sk_hi` (string comparison; either bound may be `null` = open).
- Items **returned**: the items read that also satisfy the filter (`item.get(attribute) == value`),
  or all the items read if there is no filter.
- **Consumed read capacity**: add the sizes of all items read, divide by 4096 and round up (the
  rounding is on the total of the operation, not per item); 0 items read → 0. If `consistent` is
  `False`, halve the result (this can give `x.5`).

Return `[consumed_rcu, returned_count]`.

**Example:** a table of 14 items; `query` on `pk="user#1"` reads 10 items of 1,500 bytes → 15,000
bytes → 4 RCU strongly consistent, 2.0 eventually consistent.
""",
    starter='''def readCost(items, request):
    pass
''',
    solution='''def readCost(items, request):
    read = []
    for it in items:
        if request["op"] == "query":
            if it["pk"] != request["pk"]:
                continue
            if request.get("sk_lo") is not None and it["sk"] < request["sk_lo"]:
                continue
            if request.get("sk_hi") is not None and it["sk"] > request["sk_hi"]:
                continue
        read.append(it)
    f = request.get("filter")
    returned = [it for it in read if f is None or it.get(f[0]) == f[1]]
    total = sum(it["size"] for it in read)
    rcu = -(-total // 4096)
    if not request["consistent"]:
        rcu = rcu / 2
    return [rcu, len(returned)]
''',
    tests=[
        [_ITEMS, _q("query", pk="user#1")],
        [_ITEMS, _q("query", pk="user#1", consistent=False)],
        [_ITEMS, _q("scan")],
        [_ITEMS, _q("scan", filter=["pk", "user#3"])],
        [_ITEMS, _q("query", pk="user#3")],
        [_ITEMS, _q("query", pk="user#9")],
        [_ITEMS, _q("query", pk="user#1", sk_lo="order#003", sk_hi="order#005")],
        [_ITEMS, _q("query", pk="user#1", sk_lo="order#008")],
        [_ITEMS, _q("query", pk="user#1", sk_hi="order#000", consistent=False)],
        [_ITEMS, _q("query", pk="user#1", filter=["status", "paid"])],
        [_ITEMS, _q("query", pk="user#2", filter=["status", "open"], consistent=False)],
        [_ITEMS, _q("scan", filter=["missing", "x"], consistent=False)],
        [[], _q("scan")],
        [[{"pk": "a", "sk": "1", "size": 4096}, {"pk": "a", "sk": "2", "size": 1}], _q("query", pk="a")],
        [[{"pk": "a", "sk": "%04d" % i, "size": 400, "t": i % 5} for i in range(3000)], _q("scan", filter=["t", 0], consistent=False)],
    ],
    examples=3,
    wrong_solutions=[
        '''def readCost(items, request):
    read = []
    for it in items:
        if request["op"] == "query":
            if it["pk"] != request["pk"]:
                continue
            if request.get("sk_lo") is not None and it["sk"] < request["sk_lo"]:
                continue
            if request.get("sk_hi") is not None and it["sk"] > request["sk_hi"]:
                continue
        f = request.get("filter")
        if f is None or it.get(f[0]) == f[1]:
            read.append(it)
    rcu = -(-sum(it["size"] for it in read) // 4096)
    if not request["consistent"]:
        rcu = rcu / 2
    return [rcu, len(read)]
''',
        '''def readCost(items, request):
    read = [it for it in items if request["op"] == "scan" or (it["pk"] == request["pk"]
            and (request.get("sk_lo") is None or it["sk"] >= request["sk_lo"])
            and (request.get("sk_hi") is None or it["sk"] <= request["sk_hi"]))]
    f = request.get("filter")
    returned = [it for it in read if f is None or it.get(f[0]) == f[1]]
    rcu = sum(-(-it["size"] // 4096) for it in read)
    if not request["consistent"]:
        rcu = rcu / 2
    return [rcu, len(returned)]
''',
    ],
    guide=dict(
        prereqs="The DynamoDB lesson: Query, Scan, filter expressions and read capacity.",
        intuition="Separate two sets: what the operation touches (decided by the key condition only) and what it returns (after the filter). Capacity is charged on the first set.",
        hints=["Build `read` from the key condition alone; never look at the filter in that step.",
               "Sum the sizes of `read`, then one ceiling division by 4096.",
               "For eventually consistent reads divide by two with `/` — a half unit is a valid answer."],
        brute_force="Both operations are linear passes here. The lesson of the problem is that, in the real service, a Scan is linear in the size of the **table**, while a Query is linear in the size of the **partition**.",
        approach="Dry run: scan with filter `pk = user#3` over the sample table: reads 10 × 1,500 + 3 × 5,000 + 300 = 30,300 bytes → ceil(30,300 / 4096) = 8 RCU and returns 1 item. The equivalent query on `pk = user#3` reads 300 bytes → 1 RCU for the same single item.",
        complexity="O(n) time over the items; O(n) space for the lists (O(1) with counters).",
        pitfalls="Applying the filter before computing the cost; rounding each item up separately (that is the GetItem rule, not the Query/Scan rule); integer-dividing the eventually consistent result; treating `None` bounds as strings.",
    ),
),
dict(
    id="aws-rds-failover-lag",
    title="Multi-AZ Failover vs Read-Replica Promotion",
    difficulty="Medium",
    pattern="RDS",
    entry="recoveryOutcome",
    description=r"""
A primary database fails at time `failure`. What it costs depends on how it was protected:

- **`"multi-az"`** — a standby in another Availability Zone is updated **synchronously**: every
  committed write is on the standby. Recovery is an automatic failover.
- **`"read-replica"`** — a replica is updated **asynchronously** and lags behind by `lag` seconds:
  writes committed during the last `lag` seconds before the failure never reached it. Recovery is a
  promotion of the replica.
- **`"backup"`** — only automated backups: the database can be restored to the latest restorable
  time, which is `backup_interval` seconds granular. Writes after the last backup point are lost.

`recoveryOutcome(setup, failure, writes, cfg)`:

- `writes`: list of commit times (integers, any order). Writes with a time `> failure` were rejected
  by the application and are ignored. Writes at or before `failure` were committed on the primary.
- `cfg` has `failover_s`, `promote_s`, `restore_s`, `lag`, `backup_interval`.
- Lost writes:
  - `multi-az`: none;
  - `read-replica`: committed writes with `time > failure - lag`;
  - `backup`: backup points are at `0, backup_interval, 2 × backup_interval, …`; the last one at or
    before `failure` is `last = (failure // backup_interval) × backup_interval`; committed writes with
    `time > last` are lost.
- Downtime: `failover_s`, `promote_s` or `restore_s` respectively.

Return `[downtime_seconds, lost_writes, achieved_rpo_seconds]`, where the achieved RPO is how far back
in time the data went: `0` for multi-az, `lag` for read-replica, `failure - last` for backup.

**Example:** failure at 1000, writes `[100, 990, 996, 1000, 1003]`, lag 5 → read-replica loses the
writes at 996 and 1000 → `[promote_s, 2, 5]`.
""",
    starter='''def recoveryOutcome(setup, failure, writes, cfg):
    pass
''',
    solution='''def recoveryOutcome(setup, failure, writes, cfg):
    committed = [w for w in writes if w <= failure]
    if setup == "multi-az":
        return [cfg["failover_s"], 0, 0]
    if setup == "read-replica":
        cutoff = failure - cfg["lag"]
        return [cfg["promote_s"], sum(1 for w in committed if w > cutoff), cfg["lag"]]
    last = (failure // cfg["backup_interval"]) * cfg["backup_interval"]
    return [cfg["restore_s"], sum(1 for w in committed if w > last), failure - last]
''',
    tests=[
        ["read-replica", 1000, [100, 990, 996, 1000, 1003], {"failover_s": 90, "promote_s": 600, "restore_s": 3600, "lag": 5, "backup_interval": 300}],
        ["multi-az", 1000, [100, 990, 996, 1000, 1003], {"failover_s": 90, "promote_s": 600, "restore_s": 3600, "lag": 5, "backup_interval": 300}],
        ["backup", 1000, [100, 990, 996, 1000, 1003], {"failover_s": 90, "promote_s": 600, "restore_s": 3600, "lag": 5, "backup_interval": 300}],
        ["backup", 900, [900, 899, 901, 600, 601], {"failover_s": 90, "promote_s": 600, "restore_s": 3600, "lag": 5, "backup_interval": 300}],
        ["read-replica", 1000, [995, 994, 1000], {"failover_s": 90, "promote_s": 600, "restore_s": 3600, "lag": 5, "backup_interval": 300}],
        ["read-replica", 1000, [995, 994, 1000], {"failover_s": 90, "promote_s": 600, "restore_s": 3600, "lag": 0, "backup_interval": 300}],
        ["read-replica", 50, [], {"failover_s": 60, "promote_s": 300, "restore_s": 1800, "lag": 3600, "backup_interval": 86400}],
        ["read-replica", 50, [0, 1, 49, 50, 51], {"failover_s": 60, "promote_s": 300, "restore_s": 1800, "lag": 3600, "backup_interval": 86400}],
        ["backup", 86399, list(range(0, 86400, 3600)) + [90000], {"failover_s": 60, "promote_s": 300, "restore_s": 1800, "lag": 30, "backup_interval": 86400}],
        ["backup", 86400, list(range(0, 86401, 3600)), {"failover_s": 60, "promote_s": 300, "restore_s": 1800, "lag": 30, "backup_interval": 86400}],
        ["multi-az", 0, [0], {"failover_s": 35, "promote_s": 300, "restore_s": 1800, "lag": 30, "backup_interval": 300}],
        ["backup", 299, [0, 1, 298, 299, 300], {"failover_s": 35, "promote_s": 300, "restore_s": 1800, "lag": 30, "backup_interval": 300}],
    ],
    examples=3,
    wrong_solutions=[
        '''def recoveryOutcome(setup, failure, writes, cfg):
    if setup == "multi-az":
        return [cfg["failover_s"], 0, 0]
    if setup == "read-replica":
        return [cfg["promote_s"], sum(1 for w in writes if w > failure - cfg["lag"]), cfg["lag"]]
    last = (failure // cfg["backup_interval"]) * cfg["backup_interval"]
    return [cfg["restore_s"], sum(1 for w in writes if w > last), failure - last]
''',
        '''def recoveryOutcome(setup, failure, writes, cfg):
    committed = [w for w in writes if w <= failure]
    if setup == "multi-az":
        return [cfg["failover_s"], 0, 0]
    if setup == "read-replica":
        return [cfg["promote_s"], sum(1 for w in committed if w >= failure - cfg["lag"]), cfg["lag"]]
    last = (failure // cfg["backup_interval"]) * cfg["backup_interval"]
    return [cfg["restore_s"], sum(1 for w in committed if w >= last), failure - last]
''',
    ],
    guide=dict(
        prereqs="The RDS and Aurora lesson: Multi-AZ (synchronous standby), read replicas (asynchronous), automated backups; RTO and RPO from the reliability lesson.",
        intuition="Each protection scheme defines a cut-off time: everything committed after it is gone. Synchronous replication puts the cut-off at the failure itself; asynchronous replication puts it `lag` seconds earlier; backups put it at the last backup point.",
        hints=["Discard writes after the failure first — they were never committed.",
               "Count the committed writes strictly later than the cut-off.",
               "Integer division gives the last backup point: `(failure // interval) × interval`."],
        brute_force="Not applicable; one pass over the writes.",
        approach="Dry run of the third test (backup every 300 s, failure at 1000): last backup point = 900. Committed writes `[100, 990, 996, 1000]`; later than 900: three → lost 3; achieved RPO = 100 s; downtime = restore time 3600 s. Multi-AZ on the same data: downtime 90 s, nothing lost.",
        complexity="O(n) time, O(1) extra space.",
        pitfalls="Counting rejected writes (after the failure) as lost; off-by-one at the cut-off (a write exactly at the cut-off time is safe); confusing a read replica with a standby — a replica is for read scaling and loses recent writes when promoted.",
    ),
),
dict(
    id="aws-dr-strategy",
    title="Disaster-Recovery Strategy Selector",
    difficulty="Medium",
    pattern="Reliability",
    entry="chooseStrategy",
    description=r"""
The four classic disaster-recovery strategies trade money for speed: **backup and restore**, **pilot
light**, **warm standby** and **multi-site active/active**. Each offers a recovery time objective
(**RTO**: how long the service may be down) and a recovery point objective (**RPO**: how much recent
data may be lost), at a monthly cost.

`chooseStrategy(rto_min, rpo_min, budget, strategies)`:

- `strategies`: list of `[name, rto_minutes, rpo_minutes, monthly_cost]`.
- A strategy **qualifies** when its RTO ≤ `rto_min` and its RPO ≤ `rpo_min`.
- Among the qualifying strategies that also cost ≤ `budget`, return the name of the cheapest. Break
  ties by lower RTO, then lower RPO, then name.
- If some strategies qualify but all of them are over budget, return
  `"OVER_BUDGET:<name>"` with the cheapest qualifying one (same tie-breaks) — the business must either
  pay or relax the objectives.
- If nothing qualifies, return `"IMPOSSIBLE"`.

**Example:** strategies backup-restore (1440, 1440, 100), pilot-light (60, 15, 600), warm-standby
(10, 1, 2500), multi-site (0, 0, 9000). Requirement RTO 30 min, RPO 5 min, budget 3000 →
`"warm-standby"`. With budget 1000 → `"OVER_BUDGET:warm-standby"`.
""",
    starter='''def chooseStrategy(rto_min, rpo_min, budget, strategies):
    pass
''',
    solution='''def chooseStrategy(rto_min, rpo_min, budget, strategies):
    ok = [(cost, rto, rpo, name) for name, rto, rpo, cost in strategies if rto <= rto_min and rpo <= rpo_min]
    if not ok:
        return "IMPOSSIBLE"
    affordable = [s for s in ok if s[0] <= budget]
    if affordable:
        return min(affordable)[3]
    return "OVER_BUDGET:" + min(ok)[3]
''',
    tests=[
        [30, 5, 3000, _STRATS],
        [30, 5, 1000, _STRATS],
        [2000, 2000, 50, _STRATS],
        [2000, 2000, 100, _STRATS],
        [60, 15, 600, _STRATS],
        [59, 15, 10000, _STRATS],
        [0, 0, 10000, _STRATS],
        [5, 0, 8999, _STRATS],
        [30, 5, 3000, []],
        [9, 5, 99999, [["a", 10, 1, 5]]],
        [10, 10, 100, [["b", 5, 5, 50], ["a", 5, 5, 50], ["c", 4, 9, 50], ["d", 1, 1, 60]]],
        [10, 10, 10, [["b", 5, 5, 50], ["a", 5, 5, 50], ["c", 5, 4, 50], ["d", 1, 1, 60]]],
        [1440, 60, 500, _STRATS],
    ],
    examples=2,
    wrong_solutions=[
        '''def chooseStrategy(rto_min, rpo_min, budget, strategies):
    ok = [(cost, name) for name, rto, rpo, cost in strategies if rto <= rto_min and rpo <= rpo_min and cost <= budget]
    return min(ok)[1] if ok else "IMPOSSIBLE"
''',
        '''def chooseStrategy(rto_min, rpo_min, budget, strategies):
    ok = [(rto, rpo, cost, name) for name, rto, rpo, cost in strategies if rto <= rto_min and rpo <= rpo_min]
    if not ok:
        return "IMPOSSIBLE"
    affordable = [s for s in ok if s[2] <= budget]
    if affordable:
        return min(affordable)[3]
    return "OVER_BUDGET:" + min(ok)[3]
''',
    ],
    guide=dict(
        prereqs="The reliability lesson: RTO, RPO and the four disaster-recovery strategies.",
        intuition="Objectives are hard constraints, cost is what you minimise. Filter on the objectives first; the budget only decides between a clean answer and an 'over budget' warning.",
        hints=["Build tuples `(cost, rto, rpo, name)` so that `min` applies every tie-break at once.",
               "Distinguish three cases: nothing qualifies, something qualifies within budget, something qualifies but only above budget.",
               "The over-budget answer uses the cheapest qualifying strategy, not the fastest."],
        brute_force="Sorting all strategies is O(n log n); a single `min` is O(n). Either is fine for four strategies.",
        approach="Dry run: RTO ≤ 30, RPO ≤ 5. backup-restore fails both; pilot-light fails both (60, 15); warm-standby (10, 1) and multi-site (0, 0) qualify. Budget 3000 → warm-standby (2500). Budget 1000 → neither is affordable → `OVER_BUDGET:warm-standby`.",
        complexity="O(n) time, O(n) space.",
        pitfalls="Choosing the most resilient option instead of the cheapest sufficient one; returning IMPOSSIBLE when the real problem is budget; wrong tie-break order.",
    ),
),
]
