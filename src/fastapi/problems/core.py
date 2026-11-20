PROBLEMS = [
dict(
    id="api-validate-schema",
    title="Validate a Request Body like a 422",
    difficulty="Medium",
    pattern="Validation",
    entry="validate",
    description=r"""
When a request body fails validation, FastAPI answers **422 Unprocessable Content** with a `detail` list —
one entry per problem, each with a `loc` (where) and a `type` (what). Reproduce that logic for a tiny schema
language.

`validate(data, schema)` where `data` is the parsed JSON body (a dict) and `schema` maps field names to
rule dicts with these optional keys:

| key | meaning |
|---|---|
| `type` | `"int"`, `"float"`, `"str"` or `"bool"` (always present) |
| `required` | default `True` |
| `min` / `max` | inclusive numeric bounds (int/float only) |
| `min_length` / `max_length` | inclusive string-length bounds (str only) |

Check each schema field **in schema order** and report at most **one** error per field — the first that applies:

1. Missing and required → `"missing"`. Missing and optional → no error.
2. Wrong type → `"int_type"`, `"float_type"`, `"string_type"` or `"bool_type"`. Strict rules:
   `bool` is **not** an int or float; an `int` **is** acceptable for `float`; `None` is never valid.
3. `value < min` → `"greater_than_equal"`; `value > max` → `"less_than_equal"`.
4. `len < min_length` → `"string_too_short"`; `len > max_length` → `"string_too_long"`.

Afterwards, every key in `data` not in the schema is an error `"extra_forbidden"`, in `data` order.

Each error is `[["body", field_name], type]`. Return the list (empty if valid).

**Example:** `validate({"name": "", "age": "x", "admin": True}, {"name": {"type": "str", "min_length": 1}, "age": {"type": "int"}})`
→ `[[["body","name"],"string_too_short"], [["body","age"],"int_type"], [["body","admin"],"extra_forbidden"]]`
""",
    starter='''def validate(data: dict, schema: dict) -> list:
    pass
''',
    solution='''def _type_ok(kind, v):
    if kind == "bool":
        return isinstance(v, bool)
    if isinstance(v, bool):
        return False
    if kind == "int":
        return isinstance(v, int)
    if kind == "float":
        return isinstance(v, (int, float))
    if kind == "str":
        return isinstance(v, str)
    return False

TYPE_ERR = {"int": "int_type", "float": "float_type", "str": "string_type", "bool": "bool_type"}

def validate(data, schema):
    errors = []
    for name, rule in schema.items():
        loc = ["body", name]
        if name not in data:
            if rule.get("required", True):
                errors.append([loc, "missing"])
            continue
        v, kind = data[name], rule["type"]
        if not _type_ok(kind, v):
            errors.append([loc, TYPE_ERR[kind]])
            continue
        if kind in ("int", "float"):
            if "min" in rule and v < rule["min"]:
                errors.append([loc, "greater_than_equal"]); continue
            if "max" in rule and v > rule["max"]:
                errors.append([loc, "less_than_equal"]); continue
        if kind == "str":
            if "min_length" in rule and len(v) < rule["min_length"]:
                errors.append([loc, "string_too_short"]); continue
            if "max_length" in rule and len(v) > rule["max_length"]:
                errors.append([loc, "string_too_long"]); continue
    for k in data:
        if k not in schema:
            errors.append([["body", k], "extra_forbidden"])
    return errors
''',
    tests=[
        [{"name": "", "age": "x", "admin": True}, {"name": {"type": "str", "min_length": 1}, "age": {"type": "int"}}],
        [{"name": "Ann", "age": 30}, {"name": {"type": "str"}, "age": {"type": "int", "min": 0, "max": 150}}],
        [{}, {"name": {"type": "str"}, "nick": {"type": "str", "required": False}}],
        [{"age": True}, {"age": {"type": "int"}}],
        [{"price": 3}, {"price": {"type": "float", "min": 0}}],
        [{"price": -0.5}, {"price": {"type": "float", "min": 0}}],
        [{"qty": 1000}, {"qty": {"type": "int", "min": 1, "max": 999}}],
        [{"ok": 1}, {"ok": {"type": "bool"}}],
        [{"ok": False}, {"ok": {"type": "bool"}}],
        [{"code": "ABCDEFG"}, {"code": {"type": "str", "min_length": 2, "max_length": 6}}],
        [{"x": None}, {"x": {"type": "str", "required": False}}],
        [{"b": 1, "a": 2, "z": 3}, {}],
        [{"n": 1.5}, {"n": {"type": "int"}}],
        [{"tags": "x", "name": 5, "extra1": 0}, {"name": {"type": "str"}, "age": {"type": "int"}, "tags": {"type": "str", "max_length": 0}}],
        [{"t": 37.0}, {"t": {"type": "float", "min": 35, "max": 42}}],
    ],
    wrong_solutions=[
        '''def validate(data, schema):
    T = {"int": int, "float": float, "str": str, "bool": bool}
    E = {"int": "int_type", "float": "float_type", "str": "string_type", "bool": "bool_type"}
    errs = []
    for n, r in schema.items():
        if n not in data:
            if r.get("required", True): errs.append([["body", n], "missing"])
            continue
        v = data[n]
        if not isinstance(v, T[r["type"]]): errs.append([["body", n], E[r["type"]]]); continue
        if "min" in r and v < r["min"]: errs.append([["body", n], "greater_than_equal"]); continue
        if "max" in r and v > r["max"]: errs.append([["body", n], "less_than_equal"]); continue
        if "min_length" in r and len(v) < r["min_length"]: errs.append([["body", n], "string_too_short"]); continue
        if "max_length" in r and len(v) > r["max_length"]: errs.append([["body", n], "string_too_long"]); continue
    for k in data:
        if k not in schema: errs.append([["body", k], "extra_forbidden"])
    return errs
''',
    ],
    guide=dict(
        prereqs="Pydantic validation and FastAPI's 422 response (lessons in module *Pydantic deep dive*).",
        intuition="Validation is a pipeline per field: presence → type → constraints. Stop at the first failure "
                  "for that field (a value of the wrong type has no meaningful length), but keep going to the next "
                  "field so the client sees **all** problems in one response.",
        hints=["`isinstance(True, int)` is `True` in Python — handle `bool` before `int`.",
               "Accept `int` for `float`, but still reject `bool`.",
               "After the schema loop, scan `data` for extra keys."],
        brute_force="There is no meaningfully slower approach; the work is getting the rule order right.",
        approach="For each field: if absent → `missing` if required. Else type check with a helper that rejects "
                 "`bool` unless the kind is `bool`. Then numeric bounds, then string lengths, each with `continue` "
                 "after reporting. Finally, extras in data order.",
        complexity="O(fields + keys).",
        pitfalls="- `True` passing as an `int`.\n- `None` for an optional field is still a type error (absent ≠ null).\n"
                 "- Reporting several errors for one field.",
        follow_up="Pydantic's *lax* mode would coerce `\"5\"` to `5`; its *strict* mode behaves like this exercise. "
                  "FastAPI uses lax mode for JSON bodies by default.",
    ),
),
dict(
    id="api-di-resolver",
    title="Dependency Injection Resolver",
    difficulty="Medium",
    pattern="Dependency Injection",
    entry="resolveOrder",
    description=r"""
FastAPI resolves `Depends(...)` declarations as a graph: before calling a function it resolves that
function's own dependencies, and within **one request** each dependency is called **at most once**
(the result is cached and shared). Tests can swap a dependency with `app.dependency_overrides`.

`resolveOrder(providers, target, overrides)`:

- `providers` maps a provider name to the **ordered** list of names it depends on.
- `overrides` maps a name to the name of the provider that should be used instead (an override's
  own dependencies come from `providers[override_name]`). Overrides are applied once (not chained).
- Resolve `target` depth-first: for a provider, first resolve each dependency **in listed order**, then
  "call" the provider itself. Record the **actual** provider name each time a provider is called. A
  provider already called in this request is not called again.

Return the list of called provider names in call order. If the graph has a cycle reachable from
`target`, return `["cycle"]`. All referenced names exist in `providers`.

**Example:** `providers = {"endpoint": ["user", "db"], "user": ["db", "token"], "db": ["settings"], "token": [], "settings": []}`,
`target="endpoint"`, no overrides → `["settings", "db", "token", "user", "endpoint"]`

With `overrides = {"db": "fake_db"}` and `"fake_db": []` → `["fake_db", "token", "user", "endpoint"]`.
""",
    starter='''def resolveOrder(providers: dict, target: str, overrides: dict) -> list:
    pass
''',
    solution='''def resolveOrder(providers, target, overrides):
    order, done, active = [], set(), set()

    def visit(name):
        actual = overrides.get(name, name)
        if actual in done:
            return True
        if actual in active:
            return False
        active.add(actual)
        for dep in providers[actual]:
            if not visit(dep):
                return False
        active.discard(actual)
        done.add(actual)
        order.append(actual)
        return True

    return order if visit(target) else ["cycle"]
''',
    tests=[
        [{"endpoint": ["user", "db"], "user": ["db", "token"], "db": ["settings"], "token": [], "settings": []}, "endpoint", {}],
        [{"endpoint": ["user", "db"], "user": ["db", "token"], "db": ["settings"], "token": [], "settings": [], "fake_db": []}, "endpoint", {"db": "fake_db"}],
        [{"a": []}, "a", {}],
        [{"a": ["b"], "b": ["a"]}, "a", {}],
        [{"a": ["b"], "b": ["c"], "c": ["a"]}, "a", {}],
        [{"a": ["b"], "b": ["c"], "c": ["a"], "c2": []}, "a", {"c": "c2"}],
        [{"e": ["x", "y", "z"], "x": ["s"], "y": ["s"], "z": ["s"], "s": []}, "e", {}],
        [{"e": ["a", "b"], "a": ["c"], "b": ["c"], "c": ["d"], "d": []}, "e", {}],
        [{"e": ["auth"], "auth": ["token", "db"], "token": [], "db": [], "test_auth": []}, "e", {"auth": "test_auth"}],
        [{"e": ["e"]}, "e", {}],
        [{"e": ["a"], "a": [], "unused1": ["unused2"], "unused2": ["unused1"]}, "e", {}],
        [{"e": ["a", "b"], "a": [], "b": [], "a2": ["b"]}, "e", {"a": "a2"}],
        [{"t": ["l1"], **{f"l{i}": [f"l{i+1}"] for i in range(1, 300)}, "l300": []}, "t", {}],
    ],
    wrong_solutions=[
        '''def resolveOrder(providers, target, overrides):
    order = []
    def visit(n):
        n = overrides.get(n, n)
        for d in providers[n]:
            visit(d)
        order.append(n)
    try:
        visit(target)
    except RecursionError:
        return ["cycle"]
    return order
''',
        '''def resolveOrder(providers, target, overrides):
    order, done, active = [], set(), set()
    def visit(n):
        if n in done: return True
        if n in active: return False
        active.add(n)
        for d in providers[n]:
            if not visit(d): return False
        active.discard(n); done.add(n); order.append(n)
        return True
    return order if visit(target) else ["cycle"]
''',
    ],
    guide=dict(
        prereqs="Dependencies, sub-dependencies and `dependency_overrides` (module *Dependencies*); DFS.",
        intuition="This is a post-order DFS (a topological sort) with memoisation. 'Called once per request' is the "
                  "`done` set; cycle detection is the classic three-colour trick: a node that is *in progress* "
                  "and is reached again means a back-edge.",
        hints=["Translate the name through `overrides` at the start of each visit.",
               "Keep two sets: `done` (finished) and `active` (on the current DFS path).",
               "Append a provider *after* its dependencies are resolved (post-order)."],
        brute_force="Calling every dependency each time it is mentioned gives exponential work on diamond-shaped "
                    "graphs and duplicates in the output.",
        approach="`visit(name)`: `actual = overrides.get(name, name)`; if done → return; if active → cycle; mark "
                 "active, visit deps in order, unmark, mark done, append. Dry run the first example: endpoint → user → "
                 "db → settings (append settings, db), token (append), append user, db already done, append endpoint.",
        complexity="O(V + E) for the reachable sub-graph.",
        pitfalls="- Caching by the *requested* name instead of the actual provider name.\n"
                 "- Reporting cycles in unreachable parts of the graph.\n"
                 "- Deep chains: recursion depth of a few hundred is fine in Python (limit 1000).",
        follow_up="FastAPI lets you disable sharing with `Depends(dep, use_cache=False)`. Yield-dependencies are "
                  "torn down in the reverse of this order.",
    ),
),
dict(
    id="api-concurrency-schedule",
    title="Simulate a Concurrency Limit",
    difficulty="Medium",
    pattern="Async & Concurrency",
    entry="simulate",
    description=r"""
A common async pattern is `asyncio.Semaphore(limit)`: at most `limit` coroutines run a slow section at
once, and the rest wait in **FIFO** order. Predict the timing.

`simulate(durations, limit)`: task `i` is submitted at time 0 and needs `durations[i]` time units of the
guarded section. Tasks acquire the semaphore in index order. Whenever a running task finishes at time `t`,
its slot is immediately given to the next waiting task, which starts at `t`. Several tasks may finish at
the same time; all their slots are freed at that time.

Return a list `finish` where `finish[i]` is the time task `i` completes.

**Example:** `simulate([3, 1, 2, 4], 2)` → `[3, 1, 3, 7]`
(t=0: tasks 0 and 1 start; t=1: task 1 ends, task 2 starts; t=3: tasks 0 and 2 end, task 3 starts, ends at 7.)

Constraints: `1 <= limit`, `0 <= len(durations) <= 20000`, durations are non-negative integers.
""",
    starter='''def simulate(durations: list[int], limit: int) -> list[int]:
    pass
''',
    solution='''import heapq

def simulate(durations, limit):
    finish = [0] * len(durations)
    running = []  # heap of finish times
    for i, d in enumerate(durations):
        start = 0
        if len(running) >= limit:
            start = heapq.heappop(running)
        finish[i] = start + d
        heapq.heappush(running, finish[i])
    return finish
''',
    tests=[
        [[3, 1, 2, 4], 2],
        [[], 3],
        [[5], 1],
        [[1, 1, 1, 1], 1],
        [[1, 1, 1, 1], 10],
        [[2, 2, 2, 2, 2], 2],
        [[0, 0, 3, 0], 1],
        [[10, 1, 1, 1, 1, 1], 2],
        [[4, 3, 2, 1], 3],
        [[(i * 7919) % 97 for i in range(20000)], 64],
        [[(i * 31) % 11 + 1 for i in range(1000)], 1],
    ],
    wrong_solutions=[
        '''def simulate(durations, limit):
    out = []
    for i, d in enumerate(durations):
        prev = out[i - limit] if i >= limit else 0
        out.append(prev + d)
    return out
''',
    ],
    guide=dict(
        prereqs="Semaphores and concurrency limits (lesson *Background tasks and concurrency limits*); heaps.",
        intuition="Because tasks acquire in FIFO order, task `i` starts exactly when the *earliest* currently "
                  "running task finishes. A min-heap of finish times answers 'when is the next free slot?' in O(log k).",
        hints=["While fewer than `limit` tasks are running, a task starts at time 0.",
               "Otherwise pop the smallest finish time — that is your start time.",
               "Push the new task's finish time back onto the heap."],
        brute_force="Simulate time step by step, or scan all slots for the earliest free one: O(n·limit).",
        approach="Keep a min-heap `running`. For each task: `start = heappop(running)` if the heap is full else 0; "
                 "`finish = start + d`; push it. Dry run `[3,1,2,4], 2`: push 3, push 1; task 2 pops 1 → finishes 3; "
                 "task 3 pops 3 → finishes 7.",
        complexity="O(n log limit) time, O(limit) extra space.",
        pitfalls="- Assuming task `i` waits for task `i - limit` (wrong when durations differ).\n"
                 "- Forgetting zero-duration tasks.",
        follow_up="Total makespan is `max(finish)`. This same model sizes thread pools: FastAPI runs sync `def` "
                  "endpoints in a thread pool whose default limit is 40 threads.",
    ),
),
dict(
    id="api-pagination",
    title="Pagination Metadata",
    difficulty="Easy",
    pattern="API Design",
    entry="paginate",
    description=r"""
List endpoints rarely return everything. A typical design accepts `limit` and `offset` query parameters
and returns metadata alongside the items. Compute that metadata.

`paginate(total, limit, offset)`:

1. Sanitise inputs: clamp `limit` into `1..100`; if `offset < 0`, use `0`.
2. Return a dict with keys:
   - `"total"`, `"limit"`, `"offset"` — the sanitised values (`total` as given, `total >= 0`).
   - `"page"` — 1-based page number: `offset // limit + 1`.
   - `"pages"` — `ceil(total / limit)` (so `0` when `total == 0`).
   - `"has_next"` — `offset + limit < total`; `"next_offset"` — `offset + limit` if `has_next` else `None`.
   - `"has_prev"` — `offset > 0`; `"prev_offset"` — `max(0, offset - limit)` if `has_prev` else `None`.

**Example:** `paginate(95, 20, 40)` → `{"total": 95, "limit": 20, "offset": 40, "page": 3, "pages": 5,
"has_next": True, "next_offset": 60, "has_prev": True, "prev_offset": 20}`
""",
    starter='''def paginate(total: int, limit: int, offset: int) -> dict:
    pass
''',
    solution='''def paginate(total, limit, offset):
    limit = max(1, min(100, limit))
    offset = max(0, offset)
    has_next = offset + limit < total
    has_prev = offset > 0
    return {
        "total": total, "limit": limit, "offset": offset,
        "page": offset // limit + 1,
        "pages": (total + limit - 1) // limit,
        "has_next": has_next, "next_offset": offset + limit if has_next else None,
        "has_prev": has_prev, "prev_offset": max(0, offset - limit) if has_prev else None,
    }
''',
    tests=[[95, 20, 40], [0, 10, 0], [10, 10, 0], [11, 10, 10], [100, 0, 0], [100, 500, 0], [100, 10, -5],
           [100, 10, 5], [5, 10, 50], [1, 1, 0], [1000000, 100, 999900], [7, 3, 6]],
    wrong_solutions=[
        '''def paginate(total, limit, offset):
    import math
    return {"total": total, "limit": limit, "offset": offset, "page": offset // max(limit,1) + 1,
            "pages": math.ceil(total / max(limit,1)), "has_next": offset + limit < total,
            "next_offset": offset + limit if offset + limit < total else None,
            "has_prev": offset > 0, "prev_offset": max(0, offset - limit) if offset > 0 else None}
''',
        '''def paginate(total, limit, offset):
    limit = max(1, min(100, limit)); offset = max(0, offset)
    return {"total": total, "limit": limit, "offset": offset, "page": offset // limit + 1,
            "pages": total // limit + 1, "has_next": offset + limit <= total,
            "next_offset": offset + limit, "has_prev": offset > 0, "prev_offset": offset - limit if offset else None}
''',
    ],
    guide=dict(
        prereqs="Query parameters with validation (`Query(ge=1, le=100)`), REST list design.",
        intuition="Never trust client paging input: cap `limit` so one request cannot ask for a million rows. "
                  "Everything else is arithmetic — the only subtle parts are ceiling division and the boundaries.",
        hints=["Ceiling division for non-negative ints: `(a + b - 1) // b`.",
               "`has_next` uses strict `<`: with 10 items and limit 10 at offset 0 there is no next page.",
               "A previous offset can never go below 0."],
        brute_force="Not applicable — O(1) arithmetic.",
        approach="Clamp, then compute each field directly as specified. Dry run `(11, 10, 10)`: page 2, pages 2, "
                 "has_next `20 < 11` false, prev_offset 0.",
        complexity="O(1).",
        pitfalls="- Using float `ceil` on huge totals (fine here, but integer arithmetic is exact).\n"
                 "- Off-by-one in `has_next`.\n- Not clamping `limit = 0` (division by zero).",
        follow_up="Offset pagination gets slow and inconsistent on large, changing tables; *cursor* (keyset) "
                  "pagination — `WHERE id > :last_id ORDER BY id LIMIT :n` — fixes both.",
    ),
),
dict(
    id="api-middleware-chain",
    title="Middleware Onion",
    difficulty="Medium",
    pattern="Middleware",
    entry="runChain",
    description=r"""
Middleware wraps the application like layers of an onion: the **first** middleware in the list is the
**outermost**. A request passes inward through each layer, reaches the handler, and the response passes
back outward. Simulate it with a tiny DSL.

`runChain(middlewares, path)` returns `[status, headers, trace]`. Middleware specs:

- `"trace:N"` — appends `"N>"` to `trace` on the way in and `"<N"` on the way out (the way out happens
  for every response that comes back through it, including ones produced by inner middleware).
- `"block:N:/prefix"` — if `path` starts with `/prefix`, appends `"N!"` and returns `403` immediately
  with empty headers (inner layers never run). Otherwise passes through.
- `"catch:N"` — passes through, but if an inner layer raises an error it appends `"N caught"` and
  returns `500` with empty headers instead.
- `"header:K:V"` — passes through and sets response header `K` to `V` on the way out.

The **handler** appends `"handler"`. If `path == "/boom"` it raises an error; otherwise it returns `200`
with empty headers. If an error escapes the outermost layer, the server appends `"server_error"` and the
result is status `500` with empty headers. Layers an error passes through **do not** run their
"way out" logic (no `<N`, no headers).

**Example:** `runChain(["trace:A", "header:X:1", "trace:B"], "/ok")` →
`[200, {"X": "1"}, ["A>", "B>", "handler", "<B", "<A"]]`
""",
    starter='''def runChain(middlewares: list[str], path: str) -> list:
    pass
''',
    solution='''class _Boom(Exception):
    pass

def runChain(middlewares, path):
    trace = []

    def handler():
        trace.append("handler")
        if path == "/boom":
            raise _Boom()
        return 200, {}

    def wrap(spec, inner):
        kind, _, rest = spec.partition(":")
        if kind == "trace":
            def mw():
                trace.append(rest + ">")
                st, h = inner()
                trace.append("<" + rest)
                return st, h
        elif kind == "block":
            name, _, prefix = rest.partition(":")
            def mw():
                if path.startswith(prefix):
                    trace.append(name + "!")
                    return 403, {}
                return inner()
        elif kind == "catch":
            def mw():
                try:
                    return inner()
                except _Boom:
                    trace.append(rest + " caught")
                    return 500, {}
        elif kind == "header":
            k, _, v = rest.partition(":")
            def mw():
                st, h = inner()
                h = dict(h)
                h[k] = v
                return st, h
        else:
            raise ValueError(spec)
        return mw

    app = handler
    for spec in reversed(middlewares):
        app = wrap(spec, app)
    try:
        st, h = app()
    except _Boom:
        trace.append("server_error")
        st, h = 500, {}
    return [st, h, trace]
''',
    tests=[
        [["trace:A", "header:X:1", "trace:B"], "/ok"],
        [[], "/ok"],
        [[], "/boom"],
        [["trace:A", "trace:B"], "/boom"],
        [["trace:A", "catch:C", "trace:B"], "/boom"],
        [["catch:C", "trace:A"], "/boom"],
        [["trace:A", "block:Auth:/admin", "trace:B"], "/admin/users"],
        [["trace:A", "block:Auth:/admin", "trace:B"], "/public"],
        [["header:X-Req:1", "block:Auth:/admin"], "/admin"],
        [["block:Auth:/admin", "header:X-Req:1"], "/admin"],
        [["header:A:1", "header:A:2"], "/x"],
        [["header:H:v", "catch:C", "header:I:w"], "/boom"],
        [["trace:Outer", "catch:C1", "catch:C2", "trace:Inner"], "/boom"],
        [["block:B:/", "trace:A"], "/anything"],
    ],
    wrong_solutions=[
        '''def runChain(middlewares, path):
    trace = []; headers = {}
    for m in middlewares:
        k, _, r = m.partition(":")
        if k == "trace": trace.append(r + ">")
        if k == "block":
            n, _, p = r.partition(":")
            if path.startswith(p): trace.append(n + "!"); return [403, {}, trace]
        if k == "header":
            a, _, b = r.partition(":"); headers[a] = b
    trace.append("handler")
    if path == "/boom": trace.append("server_error"); return [500, {}, trace]
    for m in reversed(middlewares):
        k, _, r = m.partition(":")
        if k == "trace": trace.append("<" + r)
    return [200, headers, trace]
''',
    ],
    guide=dict(
        prereqs="Middleware (lesson *Errors, exception handlers and middleware*); closures.",
        intuition="Middleware composition is function composition: `app = mw1(mw2(mw3(handler)))`. Build it by "
                  "wrapping from the inside out (iterate the list in reverse), then call the outermost function. "
                  "Everything about ordering then falls out of normal call/return and exception propagation.",
        hints=["Represent each layer as a zero-argument closure that calls `inner()`.",
               "Wrap in `reversed(middlewares)` so the first spec ends up outermost.",
               "Use a private exception class for the handler's error and let it propagate naturally.",
               "Header layers should copy the inner headers dict before modifying it."],
        brute_force="Trying to emulate the onion with two flat loops (in, then out) breaks as soon as a layer "
                    "short-circuits or an exception skips some layers.",
        approach="Define `handler`, then `wrap(spec, inner)` returning a closure per kind. Compose, call inside a "
                 "`try`. Dry run `['header:H:v','catch:C','header:I:w'], '/boom'`: handler raises → I layer is "
                 "skipped → C catches, returns 500 → H adds header → `[500, {'H':'v'}, ['handler','C caught']]`.",
        complexity="O(m) per request for m middleware layers.",
        pitfalls="- First-in-list must be outermost.\n- Exceptions skip the 'way out' of the layers they pass through.\n"
                 "- An outer header layer still decorates a 403 produced by an inner block.",
        follow_up="In Starlette, `app.add_middleware` *prepends*, so the **last** middleware added is the outermost — "
                  "the opposite of this list order. `ServerErrorMiddleware` is always outermost.",
    ),
),
dict(
    id="api-lru-ttl-cache",
    title="LRU Response Cache with TTL",
    difficulty="Medium",
    pattern="Caching",
    kind="class",
    entry="TTLCache",
    description=r"""
Cache expensive responses (say, model predictions for repeated inputs) with both a **capacity** (LRU
eviction) and a **time-to-live**. Time is passed in explicitly so tests are deterministic.

Implement `TTLCache(capacity, ttl)`:

- `get(key, now)` → the cached value, or `-1` if absent or expired. An entry stored at time `t` is
  expired when `now - t >= ttl`; expired entries found by `get` are removed. A successful `get` makes the
  key the **most recently used** (it does **not** extend its TTL).
- `put(key, value, now)` → stores the value with timestamp `now` and makes it most recently used. If
  the key already exists it is updated (value, timestamp, recency). If the key is new and the cache is
  full, first remove **all** expired entries; if it is still full, evict the least recently used entry.
- `size(now)` → number of non-expired entries at time `now` (does not change recency; may purge).

**Example:** `["TTLCache","put","put","get","put","get","get"]`, `[[2,10],[1,"a",0],[2,"b",1],[1,2],[3,"c",3],[2,4],[1,5]]`
→ `[None, None, None, "a", None, -1, "a"]` (key 2 was least recently used when 3 arrived).
""",
    starter='''class TTLCache:
    def __init__(self, capacity: int, ttl: int):
        pass

    def get(self, key, now: int):
        pass

    def put(self, key, value, now: int) -> None:
        pass

    def size(self, now: int) -> int:
        pass
''',
    solution='''from collections import OrderedDict

class TTLCache:
    def __init__(self, capacity, ttl):
        self.cap, self.ttl = capacity, ttl
        self.d = OrderedDict()  # key -> (value, stored_at)

    def _expired(self, key, now):
        return now - self.d[key][1] >= self.ttl

    def get(self, key, now):
        if key not in self.d:
            return -1
        if self._expired(key, now):
            del self.d[key]
            return -1
        self.d.move_to_end(key)
        return self.d[key][0]

    def _purge(self, now):
        for k in [k for k in self.d if self._expired(k, now)]:
            del self.d[k]

    def put(self, key, value, now):
        if key in self.d:
            self.d[key] = (value, now)
            self.d.move_to_end(key)
            return
        if len(self.d) >= self.cap:
            self._purge(now)
            if len(self.d) >= self.cap:
                self.d.popitem(last=False)
        self.d[key] = (value, now)

    def size(self, now):
        self._purge(now)
        return len(self.d)
''',
    tests=[
        [["TTLCache", "put", "put", "get", "put", "get", "get"], [[2, 10], [1, "a", 0], [2, "b", 1], [1, 2], [3, "c", 3], [2, 4], [1, 5]]],
        [["TTLCache", "put", "get", "get"], [[5, 10], ["k", 1, 0], ["k", 9], ["k", 10]]],
        [["TTLCache", "get", "size"], [[1, 5], ["nope", 0], [0]]],
        [["TTLCache", "put", "put", "put", "size", "get", "get"], [[2, 5], ["a", 1, 0], ["b", 2, 1], ["c", 3, 6], [6], ["a", 6], ["b", 6]]],
        [["TTLCache", "put", "put", "put", "get", "get", "get"], [[2, 100], ["a", 1, 0], ["b", 2, 0], ["a", 9, 1], ["a", 2], ["b", 2], ["c", 2]]],
        [["TTLCache", "put", "put", "put", "put", "get", "get"], [[2, 100], ["a", 1, 0], ["b", 2, 0], ["a", 9, 1], ["c", 3, 2], ["b", 3], ["a", 3]]],
        [["TTLCache", "put", "get", "put", "get"], [[1, 3], ["a", 1, 0], ["a", 2], ["a", 5, 2], ["a", 4]]],
        [["TTLCache", "put", "put", "get", "put", "get", "get", "size"], [[2, 100], [1, 1, 0], [2, 2, 0], [1, 1], [3, 3, 2], [1, 3], [2, 3], [3]]],
        [["TTLCache", "put", "put", "put", "size", "size"], [[3, 4], ["x", 0, 0], ["y", 0, 2], ["z", 0, 3], [4], [7]]],
        [["TTLCache", "put", "put", "get", "put", "get", "get"], [[1, 10], ["a", "A", 0], ["b", "B", 1], ["a", 2], ["c", "C", 3], ["b", 4], ["c", 4]]],
        [["TTLCache"] + ["put"] * 200 + ["size", "get", "get"], [[50, 1000]] + [[i, i * i, i] for i in range(200)] + [[200], [149, 201], [150, 201]]],
    ],
    wrong_solutions=[
        '''class TTLCache:
    def __init__(self, capacity, ttl):
        self.cap, self.ttl, self.d = capacity, ttl, {}
    def get(self, key, now):
        if key in self.d and now - self.d[key][1] < self.ttl:
            return self.d[key][0]
        return -1
    def put(self, key, value, now):
        if key not in self.d and len(self.d) >= self.cap:
            del self.d[next(iter(self.d))]
        self.d.pop(key, None)
        self.d[key] = (value, now)
    def size(self, now):
        return sum(1 for v in self.d.values() if now - v[1] < self.ttl)
''',
        '''from collections import OrderedDict
class TTLCache:
    def __init__(self, capacity, ttl):
        self.cap, self.ttl, self.d = capacity, ttl, OrderedDict()
    def get(self, key, now):
        if key not in self.d or now - self.d[key][1] > self.ttl:
            return -1
        self.d.move_to_end(key)
        return self.d[key][0]
    def put(self, key, value, now):
        if key in self.d:
            self.d[key] = (value, now); self.d.move_to_end(key); return
        if len(self.d) >= self.cap:
            self.d.popitem(last=False)
        self.d[key] = (value, now)
    def size(self, now):
        return sum(1 for v in self.d.values() if now - v[1] <= self.ttl)
''',
    ],
    guide=dict(
        prereqs="Caching (lesson *NoSQL and Redis caching*); `collections.OrderedDict`.",
        intuition="An `OrderedDict` is an LRU list for free: `move_to_end` on every hit, `popitem(last=False)` "
                  "to evict the oldest. Store `(value, stored_at)` so expiry is a single subtraction.",
        hints=["`get` must refresh recency but keep the original timestamp.",
               "Updating an existing key never evicts anything.",
               "Purge expired entries before falling back to LRU eviction — an expired entry is a free slot."],
        brute_force="A list of keys in recency order gives O(n) per operation.",
        approach="See solution. Dry run the example: put 1@0, put 2@1, get 1 (1 is now MRU), put 3 at capacity: "
                 "nothing expired, evict LRU = 2. get 2 → -1, get 1 → 'a'.",
        complexity="`get`/`put` amortised O(1), except the purge which is O(n) but only runs when full.",
        pitfalls="- `>=` vs `>` at the TTL boundary.\n- Evicting the most recent instead of the least.\n"
                 "- Forgetting to refresh recency on `get`.",
        follow_up="Redis implements this server-side: `SET key value EX 60` plus `maxmemory-policy allkeys-lru`.",
    ),
),
]
