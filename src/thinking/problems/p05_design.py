_SPOTS = [["A1", "motorcycle"], ["A2", "compact"], ["A3", "compact"], ["B1", "large"], ["B2", "large"]]
_ITEMS = [[i, 1000 + (i * 7) % 5] for i in range(1, 13)]
_ROWS = [["ada", "ada@x.org", "spring", "2025-03-14"], ["grace", "grace@x.org", "spring", "2025-03-14"],
         ["ada", "ada@old.org", "summer", "2025-07-06"], ["linus", "linus@x.org", "summer", "2025-07-07"]]

PROBLEMS = [
dict(
    id="think-parking-lot",
    title="Parking Lot from an Operations List",
    difficulty="Medium",
    pattern="Object-Oriented Design",
    entry="parking_lot",
    description=r"""
Model a parking lot and replay a list of operations against it.

`spots` is a list of `[spot_id, size]` with size one of `"motorcycle"`, `"compact"`, `"large"`.
A vehicle of size `motorcycle` fits any spot; `compact` fits `compact` or `large`; `large` fits only `large`.

`ops` is a list of operations; return one result per operation:

- `["park", plate, vehicle_size]` — choose a free spot the vehicle fits, preferring the **smallest
  size that fits**, and among those the one that appears **earliest in `spots`**. Return the spot id.
  If the plate is already parked return `"DUPLICATE"`. If nothing fits return `"FULL"`.
- `["leave", plate]` — free the vehicle's spot and return its spot id, or `"UNKNOWN"` if that plate
  is not parked.
- `["free", size]` — return how many free spots have exactly that size.

**Example:** `spots = [["A1","motorcycle"],["A2","compact"],["B1","large"]]`,
`ops = [["park","M1","motorcycle"],["park","C1","compact"],["park","C2","compact"],["park","C3","compact"],["leave","C1"],["free","compact"]]`
→ `["A1", "A2", "B1", "FULL", "A2", 1]`
""",
    starter='''def parking_lot(spots: List[List[str]], ops: List[list]) -> list:
    pass
''',
    solution='''def parking_lot(spots, ops):
    rank = {"motorcycle": 1, "compact": 2, "large": 3}
    occupied = {}          # spot id -> plate
    where = {}             # plate -> spot id
    out = []
    for op in ops:
        if op[0] == "park":
            plate, size = op[1], op[2]
            if plate in where:
                out.append("DUPLICATE")
                continue
            best = None
            for sid, ssize in spots:
                if sid in occupied or rank[ssize] < rank[size]:
                    continue
                if best is None or rank[ssize] < rank[best[1]]:
                    best = (sid, ssize)
            if best is None:
                out.append("FULL")
            else:
                occupied[best[0]] = plate
                where[plate] = best[0]
                out.append(best[0])
        elif op[0] == "leave":
            plate = op[1]
            if plate not in where:
                out.append("UNKNOWN")
            else:
                sid = where.pop(plate)
                del occupied[sid]
                out.append(sid)
        else:
            out.append(sum(1 for sid, ssize in spots if ssize == op[1] and sid not in occupied))
    return out
''',
    tests=[
        [[["A1", "motorcycle"], ["A2", "compact"], ["B1", "large"]], [["park", "M1", "motorcycle"], ["park", "C1", "compact"], ["park", "C2", "compact"], ["park", "C3", "compact"], ["leave", "C1"], ["free", "compact"]]],
        [_SPOTS, []],
        [[], [["park", "X", "compact"], ["free", "large"], ["leave", "X"]]],
        [_SPOTS, [["free", "motorcycle"], ["free", "compact"], ["free", "large"]]],
        [_SPOTS, [["park", "T1", "large"], ["park", "T2", "large"], ["park", "T3", "large"], ["free", "compact"]]],
        [_SPOTS, [["park", "M1", "motorcycle"], ["park", "M2", "motorcycle"], ["park", "M3", "motorcycle"], ["park", "M4", "motorcycle"], ["park", "M5", "motorcycle"], ["park", "M6", "motorcycle"]]],
        [_SPOTS, [["park", "C1", "compact"], ["park", "C1", "compact"], ["leave", "C1"], ["leave", "C1"], ["park", "C1", "large"]]],
        [_SPOTS, [["park", "C1", "compact"], ["park", "C2", "compact"], ["park", "C3", "compact"], ["leave", "C1"], ["park", "C4", "compact"], ["free", "large"]]],
        [[["L1", "large"], ["C1", "compact"], ["M1", "motorcycle"]], [["park", "a", "motorcycle"], ["park", "b", "motorcycle"], ["park", "c", "motorcycle"], ["leave", "b"], ["park", "d", "compact"]]],
        [[["L1", "large"], ["L2", "large"]], [["park", "a", "compact"], ["leave", "zzz"], ["park", "b", "large"], ["park", "c", "motorcycle"], ["leave", "a"], ["park", "c", "motorcycle"]]],
        [[["S%d" % i, ["motorcycle", "compact", "large"][i % 3]] for i in range(60)], [["park", "p%d" % i, ["large", "compact", "motorcycle"][i % 3]] for i in range(70)] + [["free", "large"], ["free", "compact"], ["free", "motorcycle"]]],
        [_SPOTS, [["park", "X", "compact"], ["leave", "X"], ["park", "Y", "compact"], ["free", "compact"], ["leave", "Y"], ["free", "compact"]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def parking_lot(spots, ops):
    rank = {"motorcycle": 1, "compact": 2, "large": 3}
    occupied, where, out = {}, {}, []
    for op in ops:
        if op[0] == "park":
            plate, size = op[1], op[2]
            if plate in where:
                out.append("DUPLICATE"); continue
            best = None
            for sid, ssize in spots:
                if sid not in occupied and rank[ssize] >= rank[size]:
                    best = sid; break
            if best is None:
                out.append("FULL")
            else:
                occupied[best] = plate; where[plate] = best; out.append(best)
        elif op[0] == "leave":
            if op[1] not in where:
                out.append("UNKNOWN")
            else:
                sid = where.pop(op[1]); del occupied[sid]; out.append(sid)
        else:
            out.append(sum(1 for sid, s in spots if s == op[1] and sid not in occupied))
    return out
''',
        '''def parking_lot(spots, ops):
    occupied, where, out = {}, {}, []
    for op in ops:
        if op[0] == "park":
            plate, size = op[1], op[2]
            if plate in where:
                out.append("DUPLICATE"); continue
            best = None
            for sid, ssize in spots:
                if sid not in occupied and ssize == size:
                    best = sid; break
            if best is None:
                out.append("FULL")
            else:
                occupied[best] = plate; where[plate] = best; out.append(best)
        elif op[0] == "leave":
            if op[1] not in where:
                out.append("UNKNOWN")
            else:
                sid = where.pop(op[1]); del occupied[sid]; out.append(sid)
        else:
            out.append(sum(1 for sid, s in spots if s == op[1] and sid not in occupied))
    return out
''',
        '''def parking_lot(spots, ops):
    rank = {"motorcycle": 1, "compact": 2, "large": 3}
    occupied, where, out = {}, {}, []
    for op in ops:
        if op[0] == "park":
            plate, size = op[1], op[2]
            best = None
            for sid, ssize in spots:
                if sid in occupied or rank[ssize] < rank[size]:
                    continue
                if best is None or rank[ssize] < rank[best[1]]:
                    best = (sid, ssize)
            if best is None:
                out.append("FULL")
            else:
                occupied[best[0]] = plate; where[plate] = best[0]; out.append(best[0])
        elif op[0] == "leave":
            if op[1] not in where:
                out.append("UNKNOWN")
            else:
                sid = where.pop(op[1]); occupied.pop(sid, None); out.append(sid)
        else:
            out.append(sum(1 for sid, s in spots if s == op[1] and sid not in occupied))
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Object-oriented design questions: a framework, a parking lot and a vending machine*. Dictionaries.",
        intuition="Two lookups describe the whole lot: which plate is in each spot, and which spot each plate is in. "
                  "Every operation reads or updates those two maps. The fitting rule is one comparison of size ranks.",
        hints=[
            "Give the sizes numbers — motorcycle 1, compact 2, large 3 — so that 'fits' becomes `spot_rank >= vehicle_rank`.",
            "Keep `occupied` (spot → plate) and `where` (plate → spot); update both together.",
            "To choose a spot, scan `spots` in order and keep a candidate only if it is strictly smaller than the best so far.",
        ],
        brute_force="Store only a list of (spot, plate) pairs and search it for every operation: O(spots) per lookup of a "
                    "plate. Fine for small lots; the two dictionaries make plate lookups constant time.",
        approach="For `park`: reject duplicates; scan for the smallest fitting free spot (first wins ties); record in both "
                 "maps. For `leave`: look up the plate, remove from both maps. For `free`: count unoccupied spots of that "
                 "exact size.\n\n**Dry run** of the example: M1 → A1 (smallest fit). C1 → A2. C2: A2 taken, B1 fits → B1. "
                 "C3: nothing free that fits → FULL. leave C1 → A2. free compact → 1.",
        complexity="Each park or free is O(S) for S spots; leave is O(1). Space O(S).",
        pitfalls="- Taking the first free spot that fits instead of the smallest, wasting large spots on motorcycles.\n"
                 "- Requiring an exact size match.\n- Forgetting the duplicate-plate check.\n"
                 "- Updating one map and not the other on `leave`.",
        follow_up="Keep a free list per size so that parking is O(1); add an hourly fee computed at `leave`.",
    ),
),
dict(
    id="think-pagination-cursor",
    title="Cursor Pagination",
    difficulty="Medium",
    pattern="API Design",
    entry="page",
    description=r"""
Implement the server side of cursor pagination for a list endpoint.

`items` is a list of `[id, created_at]` in arbitrary order (ids are unique integers; timestamps may
repeat). The endpoint returns items **newest first**: by `created_at` descending, ties broken by `id`
descending.

`page(items, limit, cursor)` returns `[ids, next_cursor]`:

- `cursor` is `None` for the first page, otherwise `[created_at, id]` of the **last item the client
  received**; the page starts with the first item strictly after that position in the ordering.
- `ids` holds at most `limit` item ids (`limit >= 1`).
- `next_cursor` is `[created_at, id]` of the last item returned if **more items remain** after this
  page, otherwise `None`. An empty page has `next_cursor = None`.

**Example:** `items = [[1,100],[2,100],[3,90],[4,110]]`, `limit = 2`, `cursor = None` →
`[[4, 2], [100, 2]]`. Calling again with `cursor = [100, 2]` → `[[1, 3], None]`.
""",
    starter='''def page(items: List[List[int]], limit: int, cursor) -> list:
    pass
''',
    solution='''def page(items, limit, cursor):
    ordered = sorted(items, key=lambda it: (-it[1], -it[0]))
    if cursor is not None:
        c_ts, c_id = cursor
        ordered = [it for it in ordered if (it[1], it[0]) < (c_ts, c_id)]
    chunk = ordered[:limit]
    if len(ordered) > limit:
        last = chunk[-1]
        return [[it[0] for it in chunk], [last[1], last[0]]]
    return [[it[0] for it in chunk], None]
''',
    tests=[
        [[[1, 100], [2, 100], [3, 90], [4, 110]], 2, None],
        [[[1, 100], [2, 100], [3, 90], [4, 110]], 2, [100, 2]],
        [[], 5, None],
        [[[1, 100]], 1, None],
        [[[1, 100]], 1, [100, 1]],
        [[[1, 100], [2, 100], [3, 100], [4, 100]], 3, None],
        [[[1, 100], [2, 100], [3, 100], [4, 100]], 3, [100, 2]],
        [_ITEMS, 5, None],
        [_ITEMS, 5, [1002, 7]],
        [_ITEMS, 12, None],
        [_ITEMS, 100, [1004, 11]],
        [_ITEMS, 3, [1000, 5]],
        [_ITEMS, 4, [1003, 9]],
        [[[i, i // 10] for i in range(1, 2001)], 50, [100, 1005]],
    ],
    examples=2,
    wrong_solutions=[
        '''def page(items, limit, cursor):
    ordered = sorted(items, key=lambda it: (-it[1], -it[0]))
    if cursor is not None:
        ordered = [it for it in ordered if it[1] < cursor[0]]
    chunk = ordered[:limit]
    if len(ordered) > limit:
        return [[it[0] for it in chunk], [chunk[-1][1], chunk[-1][0]]]
    return [[it[0] for it in chunk], None]
''',
        '''def page(items, limit, cursor):
    ordered = sorted(items, key=lambda it: (-it[1], -it[0]))
    if cursor is not None:
        ordered = [it for it in ordered if (it[1], it[0]) < (cursor[0], cursor[1])]
    chunk = ordered[:limit]
    if chunk:
        return [[it[0] for it in chunk], [chunk[-1][1], chunk[-1][0]]]
    return [[], None]
''',
        '''def page(items, limit, cursor):
    ordered = sorted(items, key=lambda it: -it[1])
    if cursor is not None:
        ordered = [it for it in ordered if (it[1], it[0]) < (cursor[0], cursor[1])]
    chunk = ordered[:limit]
    if len(ordered) > limit:
        return [[it[0] for it in chunk], [chunk[-1][1], chunk[-1][0]]]
    return [[it[0] for it in chunk], None]
''',
    ],
    guide=dict(
        prereqs="Lesson *API design questions: the building blocks* (pagination). Sorting with a tuple key.",
        intuition="A cursor is a bookmark: 'the last thing I saw was this'. Because timestamps repeat, the bookmark "
                  "must include the id as a tie-breaker, and the ordering must be total — otherwise items sharing a "
                  "timestamp are skipped or repeated.",
        hints=[
            "Sort once by `(created_at, id)` descending; every page is a slice of that order.",
            "An item comes after the cursor exactly when its `(created_at, id)` tuple is *smaller* than the cursor's.",
            "Return a next cursor only if items remain beyond this page: compare the remaining count with `limit`.",
        ],
        brute_force="Offset pagination: sort and return `ordered[offset:offset+limit]`. Simple, but pages shift when "
                    "items are inserted and deep offsets are slow; it also does not satisfy this interface.",
        approach="1. Sort newest first with id as tie-breaker.\n2. If a cursor is given, keep items whose key is "
                 "strictly less than it.\n3. Take `limit` items.\n4. If more remained, the next cursor is the key of the "
                 "last returned item; else `None`.\n\n**Dry run** example: order is 4(110), 2(100), 1(100), 3(90). First "
                 "page: [4, 2], two remain → cursor [100, 2]. Second: items after (100, 2) are 1 and 3 → [1, 3], none remain → None.",
        complexity="O(n log n) here because of the sort; a real database uses an index and seeks in O(log n + limit).",
        pitfalls="- Filtering on the timestamp alone, which drops items sharing the cursor's timestamp.\n"
                 "- Always returning a cursor, causing clients to request an empty extra page.\n"
                 "- Sorting without the id tie-breaker, so order among equal timestamps is not guaranteed.",
        follow_up="Encode the cursor as an opaque string; support paging backwards with a `prev_cursor`.",
    ),
),
dict(
    id="think-idempotency-keys",
    title="Idempotency-Key Handling",
    difficulty="Easy",
    pattern="API Design",
    entry="process_payments",
    description=r"""
A payment endpoint receives requests `[idempotency_key, amount]` one after another. Implement the
server's handling:

- A key seen for the **first time**: charge the amount. The response is `"paid:<n>"` where `n` counts
  successful charges starting at 1.
- A key seen **before with the same amount**: do **not** charge again; return the same response as
  the first time.
- A key seen **before with a different amount**: return `"conflict"` and charge nothing. The stored
  record for the key is unchanged.

Return `[responses, total_charged]` where `responses` has one entry per request.

**Example:** `[["k1", 50], ["k1", 50], ["k2", 20], ["k1", 99]]` →
`[["paid:1", "paid:1", "paid:2", "conflict"], 70]`
""",
    starter='''def process_payments(requests: List[list]) -> list:
    pass
''',
    solution='''def process_payments(requests):
    seen = {}
    responses = []
    total = 0
    count = 0
    for key, amount in requests:
        if key in seen:
            old_amount, old_response = seen[key]
            responses.append(old_response if old_amount == amount else "conflict")
            continue
        count += 1
        total += amount
        response = "paid:%d" % count
        seen[key] = (amount, response)
        responses.append(response)
    return [responses, total]
''',
    tests=[
        [[["k1", 50], ["k1", 50], ["k2", 20], ["k1", 99]]],
        [[]],
        [[["a", 10]]],
        [[["a", 10], ["a", 10], ["a", 10]]],
        [[["a", 10], ["b", 10], ["c", 10]]],
        [[["a", 10], ["a", 11], ["a", 10], ["a", 11]]],
        [[["a", 0], ["a", 0], ["b", 0]]],
        [[["x", 5], ["y", 7], ["x", 5], ["z", 1], ["y", 8], ["y", 7]]],
        [[["a", 10], ["a", 20], ["b", 20], ["a", 20]]],
        [[["k%d" % (i % 50), 3 + (i % 50)] for i in range(500)]],
        [[["k%d" % (i % 7), i % 3] for i in range(100)]],
        [[["same", 1], ["Same", 1], ["same ", 1]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def process_payments(requests):
    responses, total = [], 0
    for i, (key, amount) in enumerate(requests):
        total += amount
        responses.append("paid:%d" % (i + 1))
    return [responses, total]
''',
        '''def process_payments(requests):
    seen, responses, total, count = {}, [], 0, 0
    for key, amount in requests:
        if key in seen:
            responses.append(seen[key])
            continue
        count += 1; total += amount
        seen[key] = "paid:%d" % count
        responses.append(seen[key])
    return [responses, total]
''',
        '''def process_payments(requests):
    seen, responses, total, count = {}, [], 0, 0
    for key, amount in requests:
        if key in seen and seen[key][0] == amount:
            responses.append(seen[key][1])
            continue
        if key in seen:
            responses.append("conflict")
            seen[key] = (amount, "conflict")
            continue
        count += 1; total += amount
        seen[key] = (amount, "paid:%d" % count)
        responses.append(seen[key][1])
    return [responses, total]
''',
    ],
    guide=dict(
        prereqs="Lessons *API design questions: the building blocks* and *Concurrency questions told as stories*.",
        intuition="The key identifies one purchase, however many times it is sent. Remember, per key, what was asked "
                  "and what you answered; a repeat gets the remembered answer and no new work.",
        hints=[
            "Use a dictionary from key to `(amount, response)`.",
            "Three cases: unseen key; seen with the same amount; seen with a different amount.",
            "Only the unseen case touches the charge counter and the running total.",
        ],
        brute_force="Keep a list of past requests and scan it for each new one: O(n²) overall. A dictionary makes each "
                    "lookup constant time.",
        approach="One pass with a dictionary.\n\n**Dry run** example: k1/50 unseen → paid:1, total 50. k1/50 seen, same "
                 "amount → paid:1 again. k2/20 unseen → paid:2, total 70. k1/99 seen, different amount → conflict.",
        complexity="Time O(n), space O(distinct keys).",
        pitfalls="- Charging every request.\n- Returning the stored response even when the amount differs.\n"
                 "- Overwriting the stored record on a conflict, so that a later correct retry is no longer recognised.",
        follow_up="Add expiry: forget keys older than a given number of requests or seconds.",
    ),
),
dict(
    id="think-inventory-race",
    title="Inventory Race with Optimistic Locking",
    difficulty="Medium",
    pattern="Concurrency",
    entry="inventory",
    description=r"""
Simulate several clients buying from one stock row protected by a **version number**
(optimistic locking). The row starts with `stock` units and version `0`.

`ops` is a list of steps in the order they interleave:

- `["read", client]` — the client remembers the row's current `(stock, version)`. Result `"read"`.
- `["buy", client, qty]` — the client tries to buy using **the values it last read**:
  1. if it has never read → `"no_read"`;
  2. else if the row's version differs from the version it read → `"conflict"` (someone wrote first);
  3. else if the stock it read is less than `qty` → `"insufficient"`;
  4. else the row's stock decreases by `qty`, its version increases by 1 → `"ok"`.

A client's remembered values change only when it reads again.

Return `[results, final_stock]`.

**Example:** `stock = 1`, `ops = [["read","A"],["read","B"],["buy","A",1],["buy","B",1],["read","B"],["buy","B",1]]`
→ `[["read","read","ok","conflict","read","insufficient"], 0]`
""",
    starter='''def inventory(stock: int, ops: List[list]) -> list:
    pass
''',
    solution='''def inventory(stock, ops):
    version = 0
    seen = {}
    results = []
    for op in ops:
        if op[0] == "read":
            seen[op[1]] = (stock, version)
            results.append("read")
            continue
        client, qty = op[1], op[2]
        if client not in seen:
            results.append("no_read")
        elif seen[client][1] != version:
            results.append("conflict")
        elif seen[client][0] < qty:
            results.append("insufficient")
        else:
            stock -= qty
            version += 1
            results.append("ok")
    return [results, stock]
''',
    tests=[
        [1, [["read", "A"], ["read", "B"], ["buy", "A", 1], ["buy", "B", 1], ["read", "B"], ["buy", "B", 1]]],
        [5, []],
        [5, [["buy", "A", 1]]],
        [5, [["read", "A"], ["buy", "A", 5]]],
        [5, [["read", "A"], ["buy", "A", 6]]],
        [5, [["read", "A"], ["buy", "A", 2], ["buy", "A", 2]]],
        [5, [["read", "A"], ["buy", "A", 2], ["read", "A"], ["buy", "A", 2], ["read", "A"], ["buy", "A", 2]]],
        [10, [["read", "A"], ["read", "B"], ["read", "C"], ["buy", "C", 3], ["buy", "B", 3], ["buy", "A", 3]]],
        [3, [["read", "A"], ["buy", "A", 4], ["buy", "A", 3], ["buy", "A", 0]]],
        [0, [["read", "A"], ["buy", "A", 0], ["buy", "A", 0], ["read", "A"], ["buy", "A", 1]]],
        [100, [x for i in range(60) for x in (["read", "c%d" % (i % 4)], ["buy", "c%d" % ((i + 1) % 4), 2])]],
        [2, [["read", "A"], ["read", "B"], ["buy", "B", 3], ["buy", "A", 2], ["buy", "B", 1]]],
        [2, [["read", "A"], ["read", "B"], ["buy", "A", 1], ["buy", "B", 3], ["read", "B"], ["buy", "B", 3], ["buy", "B", 1]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def inventory(stock, ops):
    seen, results = {}, []
    for op in ops:
        if op[0] == "read":
            seen[op[1]] = stock; results.append("read"); continue
        client, qty = op[1], op[2]
        if client not in seen:
            results.append("no_read")
        elif seen[client] < qty:
            results.append("insufficient")
        else:
            stock = seen[client] - qty
            results.append("ok")
    return [results, stock]
''',
        '''def inventory(stock, ops):
    version, seen, results = 0, {}, []
    for op in ops:
        if op[0] == "read":
            seen[op[1]] = (stock, version); results.append("read"); continue
        client, qty = op[1], op[2]
        if client not in seen:
            results.append("no_read")
        elif seen[client][0] < qty:
            results.append("insufficient")
        elif seen[client][1] != version:
            results.append("conflict")
        else:
            stock -= qty; version += 1; results.append("ok")
    return [results, stock]
''',
        '''def inventory(stock, ops):
    version, seen, results = 0, {}, []
    for op in ops:
        if op[0] == "read":
            seen[op[1]] = (stock, version); results.append("read"); continue
        client, qty = op[1], op[2]
        if client not in seen:
            results.append("no_read")
        elif seen[client][1] != version:
            results.append("conflict")
        elif seen[client][0] < qty:
            results.append("insufficient")
        else:
            stock -= qty; version += 1; seen[client] = (stock, version); results.append("ok")
    return [results, stock]
''',
    ],
    guide=dict(
        prereqs="Lesson *Concurrency questions told as stories* (lost update, optimistic locking).",
        intuition="Each client acts on a photograph of the row. The version number tells the row whether that "
                  "photograph is still current; a write based on an old photograph is refused instead of silently "
                  "overwriting someone else's change.",
        hints=[
            "Keep the row's `stock` and `version`, and per client the pair it last read.",
            "Check in the stated order: never read → version mismatch → not enough → success.",
            "On success change the row only; the client's remembered pair stays as it was until it reads again.",
        ],
        brute_force="The broken version is the instructive one: store only the stock each client read and write "
                    "`read_stock - qty`. Two clients then both succeed on the last unit — the lost update.",
        approach="Loop over the steps, updating either a client's memory (read) or the row (successful buy).\n\n"
                 "**Dry run** example: A and B both read (1, v0). A buys → stock 0, v1. B's buy: its version 0 ≠ 1 → "
                 "conflict. B reads (0, v1). B buys 1: 0 < 1 → insufficient.",
        complexity="Time O(n), space O(clients).",
        pitfalls="- No version check, which oversells.\n- Testing stock before version, which reports 'insufficient' "
                 "where the true answer is 'conflict'.\n- Refreshing the client's memory after its own successful buy.",
        follow_up="Add automatic retry: on conflict, re-read and try once more; count how many units are sold.",
    ),
),
dict(
    id="think-ab-significance",
    title="A/B Test Significance",
    difficulty="Medium",
    pattern="Metrics and Experiments",
    entry="ab_test",
    compare="float",
    tolerance=1e-6,
    description=r"""
Compare two conversion rates with the standard two-proportion z-test.

Given visitors and conversions for control (A) and treatment (B), compute

- `pa = conversions_a / visitors_a`, `pb = conversions_b / visitors_b`
- pooled rate `p = (conversions_a + conversions_b) / (visitors_a + visitors_b)`
- standard error `se = sqrt(p * (1 - p) * (1/visitors_a + 1/visitors_b))`
- `z = (pb - pa) / se`, or `0.0` when `se` is 0 (nobody or everybody converted)

Return `[pa, pb, z, verdict]` where `verdict` is

- `"B better"` if `z >= 1.96`,
- `"B worse"` if `z <= -1.96`,
- `"no difference shown"` otherwise.

(1.96 is the threshold for the conventional 5 % significance level, two-sided.)

**Example:** `ab_test(10000, 500, 10000, 580)` → `[0.05, 0.058, 2.5028..., "B better"]`

Visitors are positive; conversions are between 0 and the visitors.
""",
    starter='''def ab_test(visitors_a: int, conversions_a: int, visitors_b: int, conversions_b: int) -> list:
    pass
''',
    solution='''def ab_test(visitors_a, conversions_a, visitors_b, conversions_b):
    pa = conversions_a / visitors_a
    pb = conversions_b / visitors_b
    pooled = (conversions_a + conversions_b) / (visitors_a + visitors_b)
    se = math.sqrt(pooled * (1 - pooled) * (1 / visitors_a + 1 / visitors_b))
    z = (pb - pa) / se if se > 0 else 0.0
    if z >= 1.96:
        verdict = "B better"
    elif z <= -1.96:
        verdict = "B worse"
    else:
        verdict = "no difference shown"
    return [pa, pb, z, verdict]
''',
    tests=[
        [10000, 500, 10000, 580],
        [1000, 50, 1000, 58],
        [100000, 5000, 100000, 5250],
        [10000, 580, 10000, 500],
        [500, 0, 500, 0],
        [500, 500, 500, 500],
        [1000, 100, 1000, 100],
        [2000, 100, 500, 40],
        [50, 5, 50, 15],
        [1, 0, 1, 1],
        [40000, 2000, 40000, 2125],
        [300, 30, 900, 60],
        [1000000, 10000, 1000000, 10300],
    ],
    examples=1,
    wrong_solutions=[
        '''def ab_test(visitors_a, conversions_a, visitors_b, conversions_b):
    pa = conversions_a / visitors_a
    pb = conversions_b / visitors_b
    verdict = "B better" if pb > pa else ("B worse" if pb < pa else "no difference shown")
    pooled = (conversions_a + conversions_b) / (visitors_a + visitors_b)
    se = math.sqrt(pooled * (1 - pooled) * (1 / visitors_a + 1 / visitors_b))
    return [pa, pb, (pb - pa) / se if se > 0 else 0.0, verdict]
''',
        '''def ab_test(visitors_a, conversions_a, visitors_b, conversions_b):
    pa = conversions_a / visitors_a
    pb = conversions_b / visitors_b
    pooled = (pa + pb) / 2
    se = math.sqrt(pooled * (1 - pooled) * (1 / visitors_a + 1 / visitors_b))
    z = (pb - pa) / se if se > 0 else 0.0
    verdict = "B better" if z >= 1.96 else ("B worse" if z <= -1.96 else "no difference shown")
    return [pa, pb, z, verdict]
''',
        '''def ab_test(visitors_a, conversions_a, visitors_b, conversions_b):
    pa = conversions_a / visitors_a
    pb = conversions_b / visitors_b
    pooled = (conversions_a + conversions_b) / (visitors_a + visitors_b)
    se = math.sqrt(pooled * (1 - pooled) / (visitors_a + visitors_b))
    z = (pb - pa) / se if se > 0 else 0.0
    verdict = "B better" if z >= 1.96 else ("B worse" if z <= -1.96 else "no difference shown")
    return [pa, pb, z, verdict]
''',
    ],
    guide=dict(
        prereqs="Lesson *Metrics, experiments and \"a number moved — why?\"*. Square roots; percentages.",
        intuition="Two random groups never match exactly. The standard error is the typical size of a gap produced "
                  "by chance alone; z says how many of those typical gaps the observed gap is worth. Beyond about two, "
                  "luck is an unlikely explanation.",
        hints=[
            "Compute the two rates first, then the pooled rate from the combined counts (not the average of the two rates).",
            "The standard error uses the pooled rate and both group sizes: `sqrt(p(1-p)(1/na + 1/nb))`.",
            "Guard against `se == 0`, then compare z with ±1.96.",
        ],
        brute_force="Declare the larger rate the winner. That ignores sample size — a 5.0 % versus 5.8 % gap is noise "
                    "with 1,000 visitors per group and solid with 10,000.",
        approach="Four formulas and a three-way comparison.\n\n**Dry run** example: pa = 0.05, pb = 0.058, pooled = "
                 "1080/20000 = 0.054; se = sqrt(0.054 × 0.946 × 0.0002) ≈ 0.003196; z ≈ 0.008 / 0.003196 ≈ 2.50 → B better.",
        complexity="O(1).",
        pitfalls="- Averaging the two rates instead of pooling counts (differs when group sizes differ).\n"
                 "- Dividing by zero when no one or everyone converted.\n"
                 "- Forgetting the negative side: B can be significantly worse.",
        follow_up="Return a 95 % confidence interval for the difference, and compute the sample size needed to detect a given lift.",
    ),
),
dict(
    id="think-metric-attribution",
    title="Attribute a Metric Drop by Segment",
    difficulty="Easy",
    pattern="Metrics and Experiments",
    entry="attribute_change",
    compare="float",
    tolerance=1e-6,
    description=r"""
A metric is the sum of its segments (for example, daily users by platform). Given the per-segment
values `before` and `after` as dictionaries, work out which segments explain the change.

A segment missing from one dictionary counts as 0 there. For every segment that appears in either,
compute

- `delta = after - before`
- `share = delta / total_delta`, where `total_delta` is the sum of all deltas; use `0.0` for every
  share when `total_delta` is 0.

Return a list of `[segment, delta, share]` sorted by `delta` ascending (largest drop first), ties
broken by segment name ascending.

**Example:** `before = {"ios": 400, "android": 500, "web": 100}`,
`after = {"ios": 398, "android": 404, "web": 98}` →
`[["android", -96, 0.96], ["ios", -2, 0.02], ["web", -2, 0.02]]`
""",
    starter='''def attribute_change(before: dict, after: dict) -> list:
    pass
''',
    solution='''def attribute_change(before, after):
    segments = sorted(set(before) | set(after))
    deltas = {s: after.get(s, 0) - before.get(s, 0) for s in segments}
    total = sum(deltas.values())
    rows = [[s, deltas[s], (deltas[s] / total) if total != 0 else 0.0] for s in segments]
    rows.sort(key=lambda r: (r[1], r[0]))
    return rows
''',
    tests=[
        [{"ios": 400, "android": 500, "web": 100}, {"ios": 398, "android": 404, "web": 98}],
        [{}, {}],
        [{"a": 10}, {"a": 10}],
        [{"a": 10}, {}],
        [{}, {"a": 10}],
        [{"a": 10, "b": 10}, {"a": 5, "b": 15}],
        [{"a": 100, "b": 100}, {"a": 150, "b": 80, "c": 20}],
        [{"x": 1, "y": 2, "z": 3}, {"x": 0, "y": 1, "z": 2}],
        [{"de": 5000, "fr": 3000, "br": 2000}, {"de": 5100, "fr": 2950, "br": 100}],
        [{"s%02d" % i: 1000 + i for i in range(40)}, {"s%02d" % i: 1000 + i - (i % 7) * 3 for i in range(40)}],
        [{"a": 1, "b": 1}, {"a": 0, "b": 2}],
        [{"new": 0, "old": 50}, {"new": 30, "old": 10}],
    ],
    examples=1,
    wrong_solutions=[
        '''def attribute_change(before, after):
    rows = []
    total = sum(after.values()) - sum(before.values())
    for s in before:
        d = after.get(s, 0) - before[s]
        rows.append([s, d, d / total if total else 0.0])
    rows.sort(key=lambda r: (r[1], r[0]))
    return rows
''',
        '''def attribute_change(before, after):
    segments = sorted(set(before) | set(after))
    rows = []
    for s in segments:
        d = after.get(s, 0) - before.get(s, 0)
        rows.append([s, d, d / before[s] if before.get(s) else 0.0])
    rows.sort(key=lambda r: (r[1], r[0]))
    return rows
''',
        '''def attribute_change(before, after):
    segments = sorted(set(before) | set(after))
    deltas = {s: after.get(s, 0) - before.get(s, 0) for s in segments}
    total = sum(deltas.values())
    rows = [[s, deltas[s], deltas[s] / total] for s in segments]
    rows.sort(key=lambda r: (r[1], r[0]))
    return rows
''',
    ],
    guide=dict(
        prereqs="Lesson *Metrics, experiments and \"a number moved — why?\"* (slicing a metric).",
        intuition="A total can only move because its parts moved. Listing each part's change, and its share of "
                  "the whole change, shows at a glance where to look.",
        hints=[
            "Collect the segment names from both dictionaries — a segment may be new or may have vanished.",
            "Compute every delta first, then their sum, then the shares.",
            "Sort by `(delta, name)`; guard the division when the total change is zero.",
        ],
        brute_force="Compare segments by their percentage change relative to their own previous size. That highlights "
                    "small segments with dramatic swings and can miss the large segment responsible for most of the movement.",
        approach="Union of keys → deltas → total → shares → sort.\n\n**Dry run** example: deltas ios −2, android −96, "
                 "web −2; total −100; shares 0.02, 0.96, 0.02; sorted ascending: android, ios, web.",
        complexity="O(k log k) for k segments.",
        pitfalls="- Iterating only over `before` and missing new segments.\n"
                 "- Dividing by the segment's own size instead of the total change.\n"
                 "- Division by zero when gains and losses cancel exactly.",
        follow_up="Break down by two dimensions at once (platform × country) and report the single worst cell.",
    ),
),
dict(
    id="think-fd-check",
    title="Check a Functional Dependency",
    difficulty="Easy",
    pattern="Data Modelling",
    entry="fd_violations",
    description=r"""
In a table, column `B` **functionally depends** on columns `A` when rows that agree on `A` always
agree on `B`. Violations indicate duplicated facts that have drifted apart — the update anomaly that
normalisation removes.

`rows` is a list of rows, each a list of strings. `lhs` is a list of column indexes (the determining
columns, possibly empty) and `rhs` is one column index.

Return the list of distinct `lhs` value combinations (each as a list, in `lhs` order) that are
associated with **more than one** different `rhs` value, sorted ascending. An empty result means the
dependency holds in this data.

**Example:** with rows

```
["ada",   "ada@x.org",   "spring", "2025-03-14"]
["grace", "grace@x.org", "spring", "2025-03-14"]
["ada",   "ada@old.org", "summer", "2025-07-06"]
```

`lhs = [0], rhs = 1` → `[["ada"]]` (ada has two emails); `lhs = [2], rhs = 3` → `[]`.
""",
    starter='''def fd_violations(rows: List[List[str]], lhs: List[int], rhs: int) -> List[List[str]]:
    pass
''',
    solution='''def fd_violations(rows, lhs, rhs):
    seen = {}
    for row in rows:
        key = tuple(row[i] for i in lhs)
        seen.setdefault(key, set()).add(row[rhs])
    return sorted(list(k) for k, values in seen.items() if len(values) > 1)
''',
    tests=[
        [_ROWS[:3], [0], 1],
        [_ROWS[:3], [2], 3],
        [[], [0], 1],
        [_ROWS, [2], 3],
        [_ROWS, [0, 2], 1],
        [_ROWS, [], 2],
        [_ROWS[:2], [], 2],
        [_ROWS, [1], 0],
        [[["a", "1"], ["a", "1"], ["a", "1"]], [0], 1],
        [[["a", "1"], ["b", "2"], ["a", "2"], ["b", "1"], ["c", "3"]], [0], 1],
        [[["k%d" % (i % 30), "v%d" % (i % 30 if i % 30 else i % 4)] for i in range(600)], [0], 1],
        [[["x", "y", "z"], ["x", "y", "w"], ["x", "q", "z"]], [0, 1], 2],
        [[["x", "y", "z"], ["x", "y", "w"], ["x", "q", "z"]], [1, 0], 2],
    ],
    examples=2,
    wrong_solutions=[
        '''def fd_violations(rows, lhs, rhs):
    seen, bad = {}, []
    for row in rows:
        key = tuple(row[i] for i in lhs)
        if key in seen and seen[key] != row[rhs]:
            bad.append(list(key))
        seen[key] = row[rhs]
    return sorted(bad)
''',
        '''def fd_violations(rows, lhs, rhs):
    seen = {}
    for row in rows:
        key = row[lhs[0]] if lhs else ""
        seen.setdefault(key, set()).add(row[rhs])
    return sorted([k] for k, v in seen.items() if len(v) > 1)
''',
        '''def fd_violations(rows, lhs, rhs):
    seen = {}
    for row in rows:
        key = tuple(row[i] for i in lhs)
        seen.setdefault(key, []).append(row[rhs])
    return sorted(list(k) for k, v in seen.items() if len(v) > 1)
''',
    ],
    guide=dict(
        prereqs="Lesson *Data modelling questions: entities, relationships and SQL versus NoSQL* (functional dependency).",
        intuition="'A determines B' means each value of A comes with a single value of B. So group the rows by A, "
                  "collect the distinct B values in each group, and report groups holding more than one.",
        hints=[
            "Build the grouping key as a tuple of the `lhs` columns — a tuple can be a dictionary key.",
            "Store a *set* of right-hand values per key so that repeats of the same value do not count.",
            "An empty `lhs` gives the empty tuple for every row: the question becomes 'is this column constant?'",
        ],
        brute_force="Compare every pair of rows: if they agree on `lhs` and differ on `rhs`, record the key. O(n²) "
                    "comparisons — 180,000 for 600 rows — against one pass with a dictionary.",
        approach="One pass building `key → set of values`, then filter and sort.\n\n**Dry run** `lhs=[0], rhs=1`: "
                 "ada → {ada@x.org, ada@old.org}, grace → {grace@x.org}. Only ada has two → `[['ada']]`.",
        complexity="Time O(n · |lhs|) plus sorting the violations; space O(n).",
        pitfalls="- Reporting the same key several times.\n- Counting rows instead of distinct values, which flags "
                 "harmless duplicates.\n- Using only the first `lhs` column.",
        follow_up="Given all columns, search for every single-column dependency that holds — a first step towards "
                  "suggesting how to split a table.",
    ),
),
]
