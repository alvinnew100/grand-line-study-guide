def _pet_spec():
    return [
        ["pet", "patients", ["name", "species"], True],
        ["visit", "appointments", ["next"], True],
        ["balance", "billing", ["balance_cents"], False],
        ["points", "loyalty", ["points"], False],
    ]


def _pet_responses(**overrides):
    base = {
        "patients": ["ok", 20, {"name": "Miso", "species": "cat", "weight_kg": 4.1, "notes": "nervous"}],
        "appointments": ["ok", 35, {"next": "Tue 10:00", "vet": "Dr Lim", "room": 3}],
        "billing": ["ok", 60, {"balance_cents": 4500, "currency": "SGD"}],
        "loyalty": ["ok", 25, {"points": 120}],
    }
    base.update(overrides)
    return base


def _svc(team, db):
    return {"team": team, "db": db}


PROBLEMS = [
dict(
    id="msvc-bff-aggregate",
    title="Backend for Frontend: Aggregate with Fallbacks",
    difficulty="Medium",
    pattern="User Interfaces",
    entry="compose_screen",
    description=r"""
A backend for frontend (BFF) builds one screen from several services. It calls them **in parallel**, waits at most `budget_ms` for each, keeps only the fields the screen shows, and copes when an optional part is unavailable.

`spec` is a list of screen parts, in display order. Each part is `[name, service, fields, required]`:

- `name`: the key of this part in the output;
- `service`: the service that supplies it;
- `fields`: the list of field names to copy from that service's response body;
- `required`: `True` if the screen is useless without this part.

`responses` maps a service name to `[status, latency_ms, body]`, where `status` is `"ok"` or `"error"` and `body` is a dict.

Rules:

1. Each distinct service named in `spec` is called once, even if several parts use it.
2. A call **succeeds** only if the service is in `responses`, its status is `"ok"` and `latency_ms <= budget_ms`. A slower call is abandoned at `budget_ms` (a timeout). A service missing from `responses` fails immediately (0 ms).
3. For a part whose call succeeded, the output holds `{field: body.get(field) for each field}` (a field absent from the body becomes `None`).
4. For a part whose call failed, the output holds `None` and the part's name is added to `missing` (in `spec` order).
5. `elapsed_ms` is the longest time the BFF waited for any one call: the maximum of `min(latency_ms, budget_ms)` over the services called, or `0` if nothing was called.
6. `status` is `"error"` if any **required** part failed, otherwise `"degraded"` if any part failed, otherwise `"ok"`. When the status is `"error"`, `data` is `{}`.

Return `{"status": ..., "elapsed_ms": ..., "data": {...}, "missing": [...]}`.

**Example:** with the four-part pet screen, all services healthy and `budget_ms = 200`, the result is status `"ok"`, `elapsed_ms = 60` (the slowest call, not the sum), and `data` holding only the requested fields.

**Example:** if `loyalty` answers `"error"` after 25 ms, the status is `"degraded"`, `data["points"]` is `None` and `missing` is `["points"]`.
""",
    starter='''def compose_screen(spec: List[list], responses: dict, budget_ms: int) -> dict:
    pass
''',
    solution='''def compose_screen(spec, responses, budget_ms):
    called = []
    for part in spec:
        if part[1] not in called:
            called.append(part[1])

    def succeeded(service):
        r = responses.get(service)
        return r is not None and r[0] == "ok" and r[1] <= budget_ms

    elapsed = 0
    for service in called:
        r = responses.get(service)
        if r is not None:
            elapsed = max(elapsed, min(r[1], budget_ms))

    data, missing, fatal = {}, [], False
    for name, service, fields, required in spec:
        if succeeded(service):
            body = responses[service][2]
            data[name] = {f: body.get(f) for f in fields}
        else:
            data[name] = None
            missing.append(name)
            if required:
                fatal = True
    if fatal:
        return {"status": "error", "elapsed_ms": elapsed, "data": {}, "missing": missing}
    return {"status": "degraded" if missing else "ok", "elapsed_ms": elapsed, "data": data, "missing": missing}
''',
    tests=[
        [_pet_spec(), _pet_responses(), 200],
        [_pet_spec(), _pet_responses(loyalty=["error", 25, {}]), 200],
        [_pet_spec(), _pet_responses(billing=["ok", 900, {"balance_cents": 4500}]), 200],
        [_pet_spec(), _pet_responses(patients=["error", 5, {}]), 200],
        [[], {}, 100],
        [_pet_spec(), {"patients": ["ok", 20, {"name": "Miso", "species": "cat"}],
                       "appointments": ["ok", 35, {"next": "Tue 10:00"}]}, 200],
        [[["summary", "patients", ["name"], True], ["clinical", "patients", ["weight_kg", "allergies"], False]],
         {"patients": ["ok", 40, {"name": "Miso", "weight_kg": 4.1}]}, 100],
        [[["visit", "appointments", ["next"], True]], {"appointments": ["ok", 100, {"next": "Wed 09:00"}]}, 100],
        [[["visit", "appointments", ["next"], True]], {"appointments": ["ok", 101, {"next": "Wed 09:00"}]}, 100],
        [_pet_spec(), _pet_responses(billing=["error", 500, {}], loyalty=["ok", 300, {"points": 1}]), 250],
        [[["a", "s1", [], False], ["b", "s2", ["x"], False], ["c", "s1", ["y"], False]],
         {"s1": ["error", 10, {"y": 1}], "s2": ["ok", 15, {"x": None}]}, 50],
        [[["p%d" % i, "svc%d" % (i % 7), ["v"], i % 5 == 0] for i in range(40)],
         {"svc%d" % j: ["ok" if j != 3 else "error", 10 * (j + 1), {"v": j}] for j in range(7)}, 55],
        [[["p%d" % i, "svc%d" % (i % 7), ["v"], False] for i in range(40)],
         {"svc%d" % j: ["ok", 10 * (j + 1), {"v": j}] for j in range(7)}, 45],
    ],
    examples=2,
    wrong_solutions=[
        '''def compose_screen(spec, responses, budget_ms):
    called = []
    for part in spec:
        if part[1] not in called:
            called.append(part[1])
    def succeeded(service):
        r = responses.get(service)
        return r is not None and r[0] == "ok" and r[1] <= budget_ms
    elapsed = sum(min(responses[s][1], budget_ms) for s in called if s in responses)
    data, missing, fatal = {}, [], False
    for name, service, fields, required in spec:
        if succeeded(service):
            data[name] = {f: responses[service][2].get(f) for f in fields}
        else:
            data[name] = None
            missing.append(name)
            fatal = fatal or required
    if fatal:
        return {"status": "error", "elapsed_ms": elapsed, "data": {}, "missing": missing}
    return {"status": "degraded" if missing else "ok", "elapsed_ms": elapsed, "data": data, "missing": missing}
''',
        '''def compose_screen(spec, responses, budget_ms):
    called = {part[1] for part in spec}
    elapsed = max([responses[s][1] for s in called if s in responses] or [0])
    data, missing, fatal = {}, [], False
    for name, service, fields, required in spec:
        r = responses.get(service)
        if r is not None and r[0] == "ok":
            data[name] = {f: r[2].get(f) for f in fields}
        else:
            data[name] = None
            missing.append(name)
            fatal = fatal or required
    if fatal:
        return {"status": "error", "elapsed_ms": elapsed, "data": {}, "missing": missing}
    return {"status": "degraded" if missing else "ok", "elapsed_ms": elapsed, "data": data, "missing": missing}
''',
        '''def compose_screen(spec, responses, budget_ms):
    called = {part[1] for part in spec}
    elapsed = max([min(responses[s][1], budget_ms) for s in called if s in responses] or [0])
    data, missing = {}, []
    for name, service, fields, required in spec:
        r = responses.get(service)
        if r is not None and r[0] == "ok" and r[1] <= budget_ms:
            data[name] = {f: r[2].get(f) for f in fields}
        else:
            data[name] = None
            missing.append(name)
    if missing:
        return {"status": "error", "elapsed_ms": elapsed, "data": {}, "missing": missing}
    return {"status": "ok", "elapsed_ms": elapsed, "data": data, "missing": missing}
''',
    ],
    guide=dict(
        prereqs="The lesson *Aggregating gateways, backends for frontends and GraphQL*, and degraded functionality from *What resiliency is*. Python dicts and `dict.get`.",
        intuition="A BFF is a waiter with a tray: it visits several counters at the same time, waits only so long at each, and brings back what the table asked for. Because the calls run in parallel, the waiting time is the slowest single call, capped by the timeout. Whether a missing item spoils the meal depends on whether it was essential.",
        hints=[
            "Work out first which calls succeed: present, status `ok`, and not slower than the budget.",
            "Elapsed time uses `min(latency, budget)` per service and then the maximum, because calls overlap in time.",
            "Build `data` and `missing` in one pass over `spec`, and remember whether any failed part was required.",
        ],
        brute_force="There is nothing to search here; the naive mistake is to model the calls one after another and add the latencies, which gives the wrong elapsed time and describes a much slower design.",
        approach="1. Collect the distinct services in `spec`.\n2. `elapsed` = max of `min(latency, budget)` over those present in `responses`.\n3. For each part: on success copy the requested fields with `body.get`; on failure store `None`, add the name to `missing`, and note if it was required.\n4. If a required part failed return status `error` with empty `data`; else `degraded` if anything is missing; else `ok`.\n\n**Dry run** (loyalty returns an error after 25 ms, budget 200): calls succeed for patients (20), appointments (35), billing (60). Elapsed = max(20, 35, 60, 25) = 60. Parts `pet`, `visit`, `balance` are filled; `points` is `None` and optional, so the status is `degraded` and `missing = ['points']`.",
        complexity="Time O(P x F) for P parts with up to F fields each; space proportional to the output.",
        pitfalls="Adding latencies instead of taking the maximum. Forgetting that a timed-out call still cost `budget_ms` of waiting. Treating a latency exactly equal to the budget as a timeout. Calling a service twice when two parts share it. Returning partial `data` when a required part failed.",
        follow_up="Add a cached fallback value per optional part and mark it as stale in the output. Then add a circuit breaker per service so that a service known to be failing is not called at all.",
    ),
),
dict(
    id="msvc-fitness-functions",
    title="Architecture Fitness Functions on a Dependency Graph",
    difficulty="Medium",
    pattern="Architecture Governance",
    entry="architecture_fitness",
    description=r"""
A fitness function is an automated check that an architectural rule still holds. Implement three checks over a system's call graph and report every violation.

- `calls` is a list of `[caller, callee]` pairs (service names). The same pair may appear several times.
- `layers` maps every service that appears in `calls` to an integer layer. Layer 0 is the edge (closest to the user); larger numbers are deeper. **Rule:** a service may call only services in the same layer or a deeper one.
- `max_fan_out` is the largest number of **distinct** services one service may call (a call to itself counts as one).

Return a dict with four keys:

- `"cycles"`: the sorted list of services that lie on at least one dependency cycle, that is, services that can reach themselves by following one or more calls (a service that calls itself is on a cycle);
- `"fan_out"`: the sorted list of services that call more than `max_fan_out` distinct services;
- `"layer_violations"`: the sorted list of distinct `[caller, callee]` pairs where the callee's layer is smaller than the caller's;
- `"passed"`: `True` if the three lists are all empty.

**Example:** `calls = [["bff","appointments"],["appointments","billing"],["billing","appointments"]]`, `layers = {"bff":0,"appointments":1,"billing":1}`, `max_fan_out = 3` → `{"cycles": ["appointments","billing"], "fan_out": [], "layer_violations": [], "passed": False}`

**Example:** `calls = [["bff","patients"],["patients","bff"]]`, `layers = {"bff":0,"patients":1}`, `max_fan_out = 1` → cycles `["bff","patients"]`, layer violations `[["patients","bff"]]`.
""",
    starter='''def architecture_fitness(calls: List[List[str]], layers: dict, max_fan_out: int) -> dict:
    pass
''',
    solution='''def architecture_fitness(calls, layers, max_fan_out):
    graph = {}
    for a, b in calls:
        graph.setdefault(a, set()).add(b)
        graph.setdefault(b, set())

    def reaches_itself(start):
        stack, seen = list(graph[start]), set()
        while stack:
            node = stack.pop()
            if node == start:
                return True
            if node in seen:
                continue
            seen.add(node)
            stack.extend(graph[node])
        return False

    cycles = sorted(s for s in graph if reaches_itself(s))
    fan_out = sorted(s for s, callees in graph.items() if len(callees) > max_fan_out)
    violations = [list(pair) for pair in sorted({(a, b) for a, b in calls if layers[b] < layers[a]})]
    return {"cycles": cycles, "fan_out": fan_out, "layer_violations": violations,
            "passed": not (cycles or fan_out or violations)}
''',
    tests=[
        [[["bff", "appointments"], ["appointments", "billing"], ["billing", "appointments"]],
         {"bff": 0, "appointments": 1, "billing": 1}, 3],
        [[["bff", "patients"], ["patients", "bff"]], {"bff": 0, "patients": 1}, 1],
        [[], {}, 2],
        [[["a", "b"], ["b", "c"], ["c", "d"]], {"a": 0, "b": 1, "c": 2, "d": 3}, 1],
        [[["a", "a"]], {"a": 0}, 1],
        [[["a", "b"], ["b", "c"], ["c", "a"], ["c", "d"], ["e", "a"]],
         {"a": 1, "b": 1, "c": 1, "d": 2, "e": 0}, 2],
        [[["a", "b"], ["a", "b"], ["a", "b"], ["a", "c"]], {"a": 0, "b": 1, "c": 1}, 2],
        [[["a", "b"], ["a", "c"], ["a", "d"]], {"a": 0, "b": 1, "c": 1, "d": 1}, 2],
        [[["core", "edge"], ["core", "edge"], ["edge", "data"], ["data", "core"]],
         {"edge": 0, "core": 1, "data": 2}, 5],
        [[["a", "b"], ["b", "a"], ["c", "d"], ["d", "c"], ["b", "c"]], {"a": 0, "b": 0, "c": 0, "d": 0}, 1],
        [[["s%d" % i, "s%d" % (i + 1)] for i in range(300)], {"s%d" % i: i for i in range(301)}, 1],
        [[["r%d" % i, "r%d" % ((i + 1) % 200)] for i in range(200)], {"r%d" % i: 0 for i in range(200)}, 1],
        [[["hub", "leaf%d" % i] for i in range(30)] + [["leaf7", "hub"]],
         dict({"hub": 1}, **{"leaf%d" % i: 2 for i in range(30)}), 10],
    ],
    examples=2,
    wrong_solutions=[
        '''def architecture_fitness(calls, layers, max_fan_out):
    pairs = {(a, b) for a, b in calls}
    cycles = sorted({a for a, b in pairs if (b, a) in pairs})
    graph = {}
    for a, b in pairs:
        graph.setdefault(a, set()).add(b)
    fan_out = sorted(s for s, c in graph.items() if len(c) > max_fan_out)
    violations = [list(p) for p in sorted(p for p in pairs if layers[p[1]] < layers[p[0]])]
    return {"cycles": cycles, "fan_out": fan_out, "layer_violations": violations,
            "passed": not (cycles or fan_out or violations)}
''',
        '''def architecture_fitness(calls, layers, max_fan_out):
    graph, count = {}, {}
    for a, b in calls:
        graph.setdefault(a, set()).add(b)
        graph.setdefault(b, set())
        count[a] = count.get(a, 0) + 1
    def reaches_itself(start):
        stack, seen = list(graph[start]), set()
        while stack:
            node = stack.pop()
            if node == start:
                return True
            if node not in seen:
                seen.add(node)
                stack.extend(graph[node])
        return False
    cycles = sorted(s for s in graph if reaches_itself(s))
    fan_out = sorted(s for s, n in count.items() if n > max_fan_out)
    violations = [list(p) for p in sorted({(a, b) for a, b in calls if layers[b] < layers[a]})]
    return {"cycles": cycles, "fan_out": fan_out, "layer_violations": violations,
            "passed": not (cycles or fan_out or violations)}
''',
        '''def architecture_fitness(calls, layers, max_fan_out):
    graph = {}
    for a, b in calls:
        graph.setdefault(a, set()).add(b)
        graph.setdefault(b, set())
    def reaches_itself(start):
        stack, seen = list(graph[start]), set()
        while stack:
            node = stack.pop()
            if node == start:
                return True
            if node not in seen:
                seen.add(node)
                stack.extend(graph[node])
        return False
    cycles = sorted(s for s in graph if reaches_itself(s))
    fan_out = sorted(s for s, c in graph.items() if len(c) > max_fan_out)
    violations = [list(p) for p in sorted({(a, b) for a, b in calls if layers[b] <= layers[a] and a != b})]
    return {"cycles": cycles, "fan_out": fan_out, "layer_violations": violations,
            "passed": not (cycles or fan_out or violations)}
''',
    ],
    guide=dict(
        prereqs="The lesson *Guiding an evolutionary architecture* (fitness functions) and the required standard from *The architect's role*. Sets, dicts and a depth-first search over a graph.",
        intuition="Each rule in a principles document can be turned into a question a program answers. 'No circular dependencies' becomes: can any service reach itself by following calls? 'Do not depend on too many others' becomes a count of distinct callees. 'Depend inwards only' becomes a comparison of two numbers on each edge.",
        hints=[
            "Build an adjacency map from caller to a **set** of callees so that repeated pairs collapse.",
            "A service is on a cycle exactly when a search that starts from its callees can come back to it.",
            "Use an explicit stack instead of recursion: one of the tests is a chain of 300 services.",
        ],
        brute_force="For cycles, enumerate every path from every service and look for one that returns to its start. The number of paths can grow exponentially; a search with a `seen` set visits each service once per starting point.",
        approach="1. Build `graph[caller] = set of callees`, adding an empty set for services that only receive calls.\n2. For each service, run an iterative depth-first search from its callees; if the start is reached, it is on a cycle.\n3. Fan-out violators are services whose callee set is larger than the limit.\n4. Layer violations are the distinct pairs with `layers[callee] < layers[caller]`, sorted.\n5. `passed` is true when all three lists are empty.\n\n**Dry run** on the first example: from `appointments` the search visits `billing`, whose callee is `appointments`: a cycle. From `billing` it visits `appointments` and then `billing`: a cycle. From `bff` it visits both and never returns to `bff`. Result: `['appointments', 'billing']`.",
        complexity="Time O(V x (V + E)) for the cycle check with V services and E distinct calls, which is ample for a few hundred services; O(E) for the other two checks. Space O(V + E). Tarjan's strongly connected components algorithm gives O(V + E) overall.",
        pitfalls="Detecting only two-service loops and missing longer ones. Counting repeated calls towards fan-out. Reporting a service that merely calls into a cycle as being on it. Flagging same-layer calls as layer violations. Deep recursion on a long chain.",
        follow_up="Return the cycles themselves as groups (strongly connected components), and add a fourth check: no service may be reachable from the edge by more than a given number of synchronous hops.",
    ),
),
dict(
    id="msvc-design-review",
    title="Design Review: Spot the Anti-patterns",
    difficulty="Medium",
    pattern="Architecture Review",
    entry="review_design",
    description=r"""
In a design interview you are shown a set of services and the calls between them, and asked what worries you. Write the reviewer.

- `services` maps a service name to `{"team": <owner or None>, "db": <database name or None>}`.
- `calls` is a list of `[caller, callee, mode, timeout_ms, retries, idempotent]`:
  - `mode` is `"sync"` (the caller waits) or `"async"` (a message through a broker);
  - `timeout_ms` is an integer or `None`;
  - `retries` is the number of retry attempts (for `"async"`, the number of redeliveries the broker may make);
  - `idempotent` says whether the receiving operation is safe to repeat.
- `max_sync_depth` is the longest acceptable chain of synchronous calls, counted in hops.

Return the list of findings, each `[code, subject]`, sorted by code and then subject, without duplicates:

| code | subject | when |
|---|---|---|
| `"long-sync-chain"` | the length as a string, e.g. `"5"` | the longest path of consecutive `sync` calls has more than `max_sync_depth` hops (reported once; skipped if there is a sync cycle) |
| `"no-timeout"` | `"caller->callee"` | a `sync` call has `timeout_ms` of `None` |
| `"orphan-service"` | service name | its `team` is `None` or empty |
| `"shared-database"` | database name | two or more services use the same `db` |
| `"sync-cycle"` | service name | the service can reach itself through one or more `sync` calls |
| `"unsafe-retry"` | `"caller->callee"` | `retries > 0` and the operation is not idempotent (either mode) |

**Example:** two services sharing database `"clinic"`, and one call `["appointments","billing","sync",None,2,False]` → `[["no-timeout","appointments->billing"],["shared-database","clinic"],["unsafe-retry","appointments->billing"]]`
""",
    starter='''def review_design(services: dict, calls: List[list], max_sync_depth: int) -> List[List[str]]:
    pass
''',
    solution='''def review_design(services, calls, max_sync_depth):
    findings = set()
    by_db = {}
    for name, info in services.items():
        if not info.get("team"):
            findings.add(("orphan-service", name))
        if info.get("db"):
            by_db.setdefault(info["db"], []).append(name)
    for db, users in by_db.items():
        if len(users) > 1:
            findings.add(("shared-database", db))

    sync = {}
    for caller, callee, mode, timeout_ms, retries, idempotent in calls:
        edge = caller + "->" + callee
        if mode == "sync":
            sync.setdefault(caller, set()).add(callee)
            sync.setdefault(callee, set())
            if timeout_ms is None:
                findings.add(("no-timeout", edge))
        if retries > 0 and not idempotent:
            findings.add(("unsafe-retry", edge))

    def reaches_itself(start):
        stack, seen = list(sync[start]), set()
        while stack:
            node = stack.pop()
            if node == start:
                return True
            if node in seen:
                continue
            seen.add(node)
            stack.extend(sync[node])
        return False

    on_cycle = [s for s in sync if reaches_itself(s)]
    if on_cycle:
        for s in on_cycle:
            findings.add(("sync-cycle", s))
    else:
        depth = {}

        def longest(node):
            if node not in depth:
                depth[node] = max((1 + longest(c) for c in sync[node]), default=0)
            return depth[node]

        deepest = max((longest(s) for s in sync), default=0)
        if deepest > max_sync_depth:
            findings.add(("long-sync-chain", str(deepest)))
    return [list(f) for f in sorted(findings)]
''',
    tests=[
        [{"appointments": _svc("booking", "clinic"), "billing": _svc("billing", "clinic")},
         [["appointments", "billing", "sync", None, 2, False]], 3],
        [{"appointments": _svc("booking", "appts"), "billing": _svc("billing", "bills")},
         [["appointments", "billing", "sync", 250, 2, True]], 3],
        [{}, [], 3],
        [{"a": _svc("t", None), "b": _svc("t", None), "c": _svc("t", None), "d": _svc("t", None), "e": _svc("t", None)},
         [["a", "b", "sync", 100, 0, True], ["b", "c", "sync", 100, 0, True],
          ["c", "d", "sync", 100, 0, True], ["d", "e", "sync", 100, 0, True]], 3],
        [{"a": _svc("t", None), "b": _svc("t", None), "c": _svc("t", None), "d": _svc("t", None), "e": _svc("t", None)},
         [["a", "b", "sync", 100, 0, True], ["b", "c", "sync", 100, 0, True],
          ["c", "d", "async", None, 0, True], ["d", "e", "sync", 100, 0, True]], 3],
        [{"a": _svc("t", "da"), "b": _svc("t", "db"), "c": _svc("t", "dc")},
         [["a", "b", "sync", 100, 0, True], ["b", "c", "sync", 100, 0, True], ["c", "a", "sync", 100, 0, True]], 1],
        [{"orders": _svc("x", "o"), "mailer": _svc(None, None), "audit": _svc("", "o2")},
         [["orders", "mailer", "async", None, 5, False], ["orders", "audit", "async", None, 5, True]], 3],
        [{"a": _svc("t", "shared"), "b": _svc("u", "shared"), "c": _svc("v", "shared"), "d": _svc("w", "own")}, [], 3],
        [{"a": _svc("t", None), "b": _svc("t", None)},
         [["a", "b", "sync", None, 1, False], ["a", "b", "sync", None, 3, False], ["a", "b", "sync", 50, 0, False]], 3],
        [{"a": _svc("t", None), "b": _svc("t", None), "c": _svc("t", None)},
         [["a", "b", "sync", 100, 0, True], ["a", "c", "sync", 100, 0, True], ["b", "c", "sync", 100, 0, True]], 1],
        [{"a": _svc("t", None)}, [["a", "a", "sync", 100, 1, True]], 5],
        [{"s%d" % i: _svc("team%d" % (i % 3), "db%d" % (i % 10)) for i in range(25)},
         [["s%d" % i, "s%d" % (i + 1), "sync", None if i % 6 == 0 else 200, i % 2, i % 4 != 1] for i in range(24)], 10],
        [{"s%d" % i: _svc("team", "db%d" % i) for i in range(12)},
         [["s%d" % i, "s%d" % (i + 1), "sync" if i % 4 else "async", 200, 0, True] for i in range(11)], 3],
    ],
    examples=1,
    wrong_solutions=[
        '''def review_design(services, calls, max_sync_depth):
    findings = set()
    by_db = {}
    for name, info in services.items():
        if not info.get("team"):
            findings.add(("orphan-service", name))
        if info.get("db"):
            by_db.setdefault(info["db"], []).append(name)
    for db, users in by_db.items():
        if len(users) > 1:
            findings.add(("shared-database", db))
    sync = {}
    for caller, callee, mode, timeout_ms, retries, idempotent in calls:
        edge = caller + "->" + callee
        if mode == "sync":
            sync.setdefault(caller, set()).add(callee)
            sync.setdefault(callee, set())
            if timeout_ms is None:
                findings.add(("no-timeout", edge))
            if retries > 0 and not idempotent:
                findings.add(("unsafe-retry", edge))
    def reaches_itself(start):
        stack, seen = list(sync[start]), set()
        while stack:
            node = stack.pop()
            if node == start:
                return True
            if node not in seen:
                seen.add(node)
                stack.extend(sync[node])
        return False
    on_cycle = [s for s in sync if reaches_itself(s)]
    if on_cycle:
        for s in on_cycle:
            findings.add(("sync-cycle", s))
    else:
        depth = {}
        def longest(node):
            if node not in depth:
                depth[node] = max((1 + longest(c) for c in sync[node]), default=0)
            return depth[node]
        deepest = max((longest(s) for s in sync), default=0)
        if deepest > max_sync_depth:
            findings.add(("long-sync-chain", str(deepest)))
    return [list(f) for f in sorted(findings)]
''',
        '''def review_design(services, calls, max_sync_depth):
    findings = set()
    by_db = {}
    for name, info in services.items():
        if not info.get("team"):
            findings.add(("orphan-service", name))
        if info.get("db"):
            by_db.setdefault(info["db"], []).append(name)
    for db, users in by_db.items():
        if len(users) > 1:
            findings.add(("shared-database", db))
    graph = {}
    for caller, callee, mode, timeout_ms, retries, idempotent in calls:
        edge = caller + "->" + callee
        graph.setdefault(caller, set()).add(callee)
        graph.setdefault(callee, set())
        if mode == "sync" and timeout_ms is None:
            findings.add(("no-timeout", edge))
        if retries > 0 and not idempotent:
            findings.add(("unsafe-retry", edge))
    def reaches_itself(start):
        stack, seen = list(graph[start]), set()
        while stack:
            node = stack.pop()
            if node == start:
                return True
            if node not in seen:
                seen.add(node)
                stack.extend(graph[node])
        return False
    on_cycle = [s for s in graph if reaches_itself(s)]
    if on_cycle:
        for s in on_cycle:
            findings.add(("sync-cycle", s))
    else:
        depth = {}
        def longest(node):
            if node not in depth:
                depth[node] = max((1 + longest(c) for c in graph[node]), default=0)
            return depth[node]
        deepest = max((longest(s) for s in graph), default=0)
        if deepest > max_sync_depth:
            findings.add(("long-sync-chain", str(deepest)))
    return [list(f) for f in sorted(findings)]
''',
        '''def review_design(services, calls, max_sync_depth):
    findings = []
    dbs = [info["db"] for info in services.values() if info.get("db")]
    for db in dbs:
        if dbs.count(db) > 1:
            findings.append(["shared-database", db])
    for name, info in services.items():
        if info.get("team") is None:
            findings.append(["orphan-service", name])
    for caller, callee, mode, timeout_ms, retries, idempotent in calls:
        if mode == "sync" and timeout_ms is None:
            findings.append(["no-timeout", caller + "->" + callee])
        if retries > 0 and not idempotent:
            findings.append(["unsafe-retry", caller + "->" + callee])
    return sorted(findings)
''',
    ],
    guide=dict(
        prereqs="The lesson *Interview essentials I*, plus data ownership (*The key concepts*), stability patterns and idempotency (*Stability patterns*), and ownership (*Conway's law and team structure*). Sets, dicts and a graph search.",
        intuition="Each finding is one of the track's warnings turned into a rule. Shared tables couple services. A blocking call with no timeout lets a slow dependency hold your workers. Retrying or redelivering a non-idempotent operation repeats its effect. Long synchronous chains multiply unavailability and add latency. A cycle of blocking calls means the services cannot fail or deploy separately. A service with no owner will not be patched.",
        hints=[
            "Collect findings in a set of tuples so duplicates disappear, then sort at the end.",
            "Only `sync` calls belong in the graph used for cycles and chain length; `unsafe-retry` applies to both modes.",
            "If there is no sync cycle, the longest chain is a longest-path problem on an acyclic graph: memoise `1 + longest(child)`.",
        ],
        brute_force="Enumerate every path of synchronous calls to find the longest and to look for repeats. Paths can be exponentially many; memoising the longest chain from each service visits each edge once.",
        approach="1. Scan `services`: flag missing owners; group services by database and flag any database with two or more users.\n2. Scan `calls`: for `sync` calls record the edge and flag a missing timeout; for any call flag retries on a non-idempotent operation.\n3. On the sync graph, a service is on a cycle if a search from its callees returns to it. Report each such service.\n4. If there is no cycle, compute the longest chain in hops with memoised recursion and report it once if it exceeds the limit.\n5. Return the sorted findings as lists.\n\n**Dry run** on the example: both services use `clinic` → `shared-database`. The call is `sync` with no timeout → `no-timeout`. It retries twice and is not idempotent → `unsafe-retry`. The sync graph has one hop, within the limit of 3, and no cycle.",
        complexity="Time O(S + C + V x (V + E)) for S services, C calls and the sync graph's V nodes and E edges; space O(V + E).",
        pitfalls="Counting services instead of hops for the chain length. Including asynchronous calls in the chain. Ignoring redelivery on asynchronous calls. Reporting the same database or edge twice. Treating an empty team name as an owner. Computing a longest path on a graph that contains a cycle.",
        follow_up="Add a severity to each finding and a rule for retries at more than one layer of the same chain (a retry storm). Then estimate the chain's availability from a per-service figure.",
    ),
),
]
