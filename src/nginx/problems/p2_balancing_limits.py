PROBLEMS = [
dict(
    id="nginx-smooth-wrr",
    title="Smooth Weighted Round Robin",
    difficulty="Medium",
    pattern="Load Balancing",
    entry="smooth_wrr",
    description=r"""
NGINX's default balancing method is **smooth weighted round robin**. With weights 5, 1, 1 a naive scheme would send
five requests in a row to the first server. The smooth version spreads them: `a a b a c a a`.

Write `smooth_wrr(weights, n)` returning the list of server indices chosen for `n` consecutive requests.

Algorithm, per request:

1. Every server keeps a number `current`, starting at 0. Add each server's `weight` to its `current`.
2. Choose the server with the largest `current` (the lowest index wins ties).
3. Subtract the **sum of all weights** from the chosen server's `current`.

Weights are positive integers. If `weights` is empty, return an empty list.

**Example:** `[5, 1, 1]`, `7` → `[0, 0, 1, 0, 2, 0, 0]`
""",
    starter='''def smooth_wrr(weights, n):
    # return the indices chosen for n requests
    pass
''',
    solution='''def smooth_wrr(weights, n):
    if not weights:
        return []
    total = sum(weights)
    current = [0] * len(weights)
    out = []
    for _ in range(n):
        best = 0
        for i, w in enumerate(weights):
            current[i] += w
            if current[i] > current[best]:
                best = i
        current[best] -= total
        out.append(best)
    return out
''',
    tests=[
        [[5, 1, 1], 7],
        [[1, 1, 1], 6],
        [[3, 1], 8],
        [[1], 3],
        [[2, 2, 1], 10],
        [[10, 1], 11],
        [[], 5],
        [[1, 2, 3], 12],
        [[4, 2, 1], 0],
        [[1, 1, 5], 9],
        [[7, 5, 3, 1], 1600],
        [[2, 1], 1],
    ],
    examples=1,
    wrong_solutions=[
        '''def smooth_wrr(weights, n):
    cycle = [i for i, w in enumerate(weights) for _ in range(w)]
    return [cycle[k % len(cycle)] for k in range(n)] if cycle else []
''',
        '''def smooth_wrr(weights, n):
    if not weights:
        return []
    current = [0] * len(weights)
    out = []
    for _ in range(n):
        for i, w in enumerate(weights):
            current[i] += w
        best = current.index(max(current))
        current[best] -= weights[best] * len(weights)
        out.append(best)
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson: *HTTP load balancing and the balancing methods*. Lists and loops.",
        intuition="Each server earns credit at a rate equal to its weight. Whoever holds the most credit serves the next request and pays the price of one full round. Heavy servers earn quickly and are picked often, but paying the full round each time stops them from being picked many times in a row.",
        hints=[
            "Keep one integer per server and update all of them on every request.",
            "The amount subtracted is the same for every server: the sum of all weights.",
            "On ties, keep the earlier server. Compare with a strict `>` while scanning from index 0.",
        ],
        brute_force="Expand the weights into a list such as `[0,0,0,0,0,1,2]` and cycle through it. The proportions are right over a full cycle, but the heavy server receives bursts, which is exactly what the smooth algorithm was introduced to avoid.",
        approach="1. `total = sum(weights)`, `current = [0] * k`.\n2. For each request add the weights, find the arg-max, subtract `total` from it, record it.\n\nDry run with `[5,1,1]` (total 7): currents become `[5,1,1]` → pick 0 → `[-2,1,1]`. Add → `[3,2,2]` → pick 0 → `[-4,2,2]`. Add → `[1,3,3]` → pick 1 (tie with 2, lower index) → `[1,-4,3]`. Add → `[6,-3,4]` → 0. Add → `[4,-2,5]` → 2. Then 0, 0, and the currents are back to all zeros: the pattern repeats every 7 requests.",
        complexity="Time O(n × k) for k servers; space O(k) besides the output.",
        pitfalls="Subtracting the chosen server's own weight instead of the total; breaking ties towards the later server; dividing by zero or indexing an empty list.",
        follow_up="NGINX lowers a server's *effective* weight after failures and lets it recover gradually. Add an `effective` array that is used in place of `weights` and adjusted on failure.",
    ),
),
dict(
    id="nginx-least-conn",
    title="Least Connections with Weights",
    difficulty="Medium",
    pattern="Load Balancing",
    entry="least_conn",
    description=r"""
The `least_conn` method sends each new request to the server with the fewest requests in progress, taking weights into
account. Write `least_conn(weights, events)` and return the server index chosen for each request, in order.

`events` is a list in time order:

- `["req", id]`: a new request arrives and must be assigned.
- `["done", id]`: that request has finished and no longer counts. An unknown id is ignored.

A server's load is `active / weight`, where `active` is its number of requests in progress. Choose the server with the
**smallest load**; on a tie choose the lowest index. Compare loads without floating point: server `i` is strictly less
loaded than server `j` when `active[i] * weight[j] < active[j] * weight[i]`.

**Example:** weights `[1, 1]`, events `[["req","a"], ["req","b"], ["done","a"], ["req","c"]]` → `[0, 1, 0]`

**Example:** weights `[2, 1]`, three requests and no completions → `[0, 1, 0]`
""",
    starter='''def least_conn(weights, events):
    # return the server index chosen for each "req" event
    pass
''',
    solution='''def least_conn(weights, events):
    active = [0] * len(weights)
    placed = {}
    out = []
    for kind, rid in events:
        if kind == "req":
            best = 0
            for i in range(1, len(weights)):
                if active[i] * weights[best] < active[best] * weights[i]:
                    best = i
            active[best] += 1
            placed[rid] = best
            out.append(best)
        else:
            server = placed.pop(rid, None)
            if server is not None:
                active[server] -= 1
    return out
''',
    tests=[
        [[1, 1], [["req", "a"], ["req", "b"], ["done", "a"], ["req", "c"]]],
        [[2, 1], [["req", "a"], ["req", "b"], ["req", "c"]]],
        [[1, 1, 1], [["req", i] for i in range(7)]],
        [[1, 1, 1], [["req", 1], ["req", 2], ["req", 3], ["done", 2], ["done", 3], ["req", 4], ["req", 5], ["req", 6]]],
        [[3, 1], [["req", i] for i in range(8)]],
        [[1], [["req", "x"], ["done", "x"], ["req", "y"]]],
        [[1, 1], []],
        [[1, 1], [["done", "ghost"], ["req", "a"], ["done", "a"], ["done", "a"], ["req", "b"], ["req", "c"]]],
        [[1, 4, 2], [["req", i] for i in range(14)]],
        [[1, 1], [["req", "slow"], ["req", "f1"], ["done", "f1"], ["req", "f2"], ["done", "f2"], ["req", "f3"], ["req", "f4"]]],
        [[2, 2, 1], [["req", "a"], ["req", "b"], ["req", "c"], ["done", "a"], ["req", "d"], ["req", "e"], ["done", "c"], ["req", "f"]]],
        [[5, 3], [["req", i] for i in range(300)] + [["done", i] for i in range(0, 300, 2)] + [["req", 1000 + i] for i in range(50)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def least_conn(weights, events):
    active = [0] * len(weights)
    placed = {}
    out = []
    for kind, rid in events:
        if kind == "req":
            best = active.index(min(active))
            active[best] += 1
            placed[rid] = best
            out.append(best)
        else:
            server = placed.pop(rid, None)
            if server is not None:
                active[server] -= 1
    return out
''',
        '''def least_conn(weights, events):
    active = [0] * len(weights)
    out = []
    for kind, rid in events:
        if kind == "req":
            best = 0
            for i in range(1, len(weights)):
                if active[i] * weights[best] < active[best] * weights[i]:
                    best = i
            active[best] += 1
            out.append(best)
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson: *HTTP load balancing and the balancing methods*. Dictionaries.",
        intuition="Round robin counts requests handed out. Least connections counts requests still running, so a server stuck on slow requests stops receiving new ones until it catches up. Weights scale the comparison: a server with weight 2 is allowed twice as many before it looks equally busy.",
        hints=[
            "You need two pieces of state: how many requests each server has in progress, and which server each request id went to.",
            "Cross-multiply to compare `a/b` with `c/d` using integers only.",
            "Use a strict `<` while scanning upward so that the lowest index wins ties.",
        ],
        brute_force="Compute `active[i] / weights[i]` as floats and take the minimum. It works for small numbers; cross-multiplication avoids any rounding doubt and is no harder.",
        approach="1. `active = [0]*k`, `placed = {}`.\n2. On `req`: scan for the least loaded server, increment it, remember `placed[id]`, record the index.\n3. On `done`: look up the id, decrement that server, forget the id.\n\nDry run with weights `[2,1]`: first request, loads 0 and 0, tie → 0. Second: loads 1/2 and 0 → 1. Third: 1/2 against 1/1 → 0. Result `[0,1,0]`.",
        complexity="Time O(events × servers); space O(servers + requests in progress).",
        pitfalls="Ignoring weights; never decrementing; decrementing twice for a repeated `done`; breaking ties towards the last server.",
        follow_up="Real NGINX breaks ties with weighted round robin instead of the lowest index. Combine this with `smooth_wrr` over the tied servers.",
    ),
),
dict(
    id="nginx-hash-select",
    title="ip_hash: Choose a Server from the Client Address",
    difficulty="Medium",
    pattern="Load Balancing",
    entry="ip_hash",
    description=r"""
With `ip_hash`, NGINX sends all requests from one client network to the same server. Reproduce its calculation.

`ip_hash(ips, weights, down)` returns, for each IPv4 address in `ips`, the index of the chosen server. `weights` are
the servers' weights and `down` is a list of indices that are currently unavailable.

For one address:

1. Take only the **first three octets** (so a whole /24 network maps to one server).
2. Start with `hash = 89`. For each of the three octets in order: `hash = (hash * 113 + octet) % 6271`.
3. `w = hash % total_weight`. Walk the servers from index 0: while `w >= weight` of the current server, subtract that
   weight from `w` and move to the next server. The server you stop on is the candidate.
4. If the candidate is not in `down`, it is the answer. If it is, **repeat steps 2 and 3 without resetting `hash`**
   (feed the same three octets in again) and test the new candidate. After 20 unsuccessful attempts the answer is `-1`.

**Example:** `["203.0.113.5", "203.0.113.200"]`, weights `[1, 1, 1]`, no servers down → both get the same index.
""",
    starter='''def ip_hash(ips, weights, down):
    # return the chosen server index for each address
    pass
''',
    solution='''def ip_hash(ips, weights, down):
    total = sum(weights)
    unavailable = set(down)
    out = []
    for ip in ips:
        octets = [int(x) for x in ip.split(".")[:3]]
        h = 89
        chosen = -1
        for _ in range(20):
            for o in octets:
                h = (h * 113 + o) % 6271
            w = h % total
            idx = 0
            while w >= weights[idx]:
                w -= weights[idx]
                idx += 1
            if idx not in unavailable:
                chosen = idx
                break
        out.append(chosen)
    return out
''',
    tests=[
        [["203.0.113.5", "203.0.113.200"], [1, 1, 1], []],
        [["10.0.0.1", "10.0.1.1", "10.0.2.1", "10.0.3.1", "10.0.4.1", "10.0.5.1"], [1, 1, 1], []],
        [["192.168.1.7"], [1], []],
        [["192.168.1.7", "172.16.5.9", "8.8.8.8", "1.1.1.1"], [5, 1], []],
        [["192.168.1.7", "172.16.5.9", "8.8.8.8", "1.1.1.1"], [1, 5], []],
        [["10.0.0.1", "10.0.1.1", "10.0.2.1", "10.0.3.1", "10.0.4.1", "10.0.5.1"], [1, 1, 1], [0]],
        [["10.0.0.1", "10.0.1.1", "10.0.2.1", "10.0.3.1"], [1, 1, 1], [0, 1]],
        [["10.0.0.1", "10.0.1.1"], [1, 1], [0, 1]],
        [[], [1, 1], []],
        [["198.51.%d.%d" % (i, (i * 7) % 256) for i in range(60)], [2, 1, 3, 1], []],
        [["198.51.%d.%d" % (i, (i * 7) % 256) for i in range(60)], [2, 1, 3, 1], [2]],
        [["100.64.%d.1" % i for i in range(40)] + ["100.64.%d.250" % i for i in range(40)], [1, 1, 1, 1, 1], [4]],
    ],
    examples=1,
    wrong_solutions=[
        '''def ip_hash(ips, weights, down):
    total = sum(weights)
    unavailable = set(down)
    out = []
    for ip in ips:
        octets = [int(x) for x in ip.split(".")]
        h = 89
        chosen = -1
        for _ in range(20):
            for o in octets:
                h = (h * 113 + o) % 6271
            w = h % total
            idx = 0
            while w >= weights[idx]:
                w -= weights[idx]
                idx += 1
            if idx not in unavailable:
                chosen = idx
                break
        out.append(chosen)
    return out
''',
        '''def ip_hash(ips, weights, down):
    total = sum(weights)
    out = []
    for ip in ips:
        h = 89
        for o in [int(x) for x in ip.split(".")[:3]]:
            h = (h * 113 + o) % 6271
        w = h % total
        idx = 0
        while w >= weights[idx]:
            w -= weights[idx]
            idx += 1
        out.append(idx)
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson: *HTTP load balancing and the balancing methods* (ip_hash). The `%` operator.",
        intuition="A hash turns the address into a number that looks random but is always the same for the same input. Reducing that number modulo the total weight and walking the weights converts it into a server, with heavier servers covering more of the range.",
        hints=[
            "Split on dots and keep three numbers. The fourth octet must not influence the result.",
            "The walk in step 3 is the standard way to pick from weighted items: subtract weights until the remainder fits.",
            "For the retry, do not start again from 89. Continue from the current hash value, which is why the next candidate differs.",
        ],
        brute_force="A simpler but different scheme is `sum(octets) % number_of_servers`. It ignores weights and clusters badly; it is not what NGINX does, so its answers do not match.",
        approach="1. Precompute `total` and a set of down servers.\n2. For each address: three octets, `h = 89`.\n3. Up to 20 times: fold the octets into `h`, compute `w`, walk the weights, accept if available.\n\nDry run for `10.0.0.1` with weights `[1,1,1]`: h = (89·113+10) % 6271 = 3796; then (3796·113+0) % 6271 = 2520; then (2520·113+0) % 6271 = 2565. `w = 2565 % 3 = 0` → server 0.",
        complexity="Time O(addresses × (tries × servers)); space O(servers).",
        pitfalls="Using all four octets; resetting the hash on retry (which would pick the same down server twenty times); an off-by-one in the weight walk; returning a server that is down.",
        follow_up="`hash $key consistent;` uses a ring so that removing a server remaps only that server's keys. Implement a consistent-hash ring with 160 points per unit of weight and measure how many keys move when one server leaves.",
    ),
),
dict(
    id="nginx-passive-health",
    title="Passive Health Checks: max_fails and fail_timeout",
    difficulty="Medium",
    pattern="Load Balancing",
    entry="passive_health",
    description=r"""
Open-source NGINX judges an upstream server by the requests it sends there. Simulate one server with the parameters
`max_fails` and `fail_timeout` (seconds).

`passive_health(max_fails, fail_timeout, events)` receives `events`, a list of `[time, would_succeed]` in increasing
time order. Each is a moment at which NGINX would like to use the server, and whether the server would answer
correctly at that moment. Return one string per event:

- `"skipped"` if the server is currently marked unavailable. No request is sent, so nothing is learned.
- `"ok"` if a request is sent and succeeds.
- `"fail"` if a request is sent and fails.

Rules for this model:

- A failure at time `t` is remembered while `now - t < fail_timeout`.
- When a new failure brings the number of remembered failures to `max_fails`, the server is marked unavailable from
  that moment until `now + fail_timeout` (exclusive), and the remembered failures are cleared.
- At or after that time the server is tried again as normal.
- `max_fails = 0` switches the mechanism off: the server is never skipped.
- A success does not erase remembered failures; they expire with time.

**Example:** `max_fails=2`, `fail_timeout=10`, events `[[0,False],[1,False],[5,True],[11,True]]`
→ `["fail", "fail", "skipped", "ok"]`
""",
    starter='''def passive_health(max_fails, fail_timeout, events):
    # return "ok", "fail" or "skipped" for each event
    pass
''',
    solution='''def passive_health(max_fails, fail_timeout, events):
    fails = []
    unavailable_until = None
    out = []
    for t, would_succeed in events:
        if unavailable_until is not None and t < unavailable_until:
            out.append("skipped")
            continue
        if would_succeed:
            out.append("ok")
            continue
        out.append("fail")
        fails = [f for f in fails if t - f < fail_timeout]
        fails.append(t)
        if max_fails > 0 and len(fails) >= max_fails:
            unavailable_until = t + fail_timeout
            fails = []
    return out
''',
    tests=[
        [2, 10, [[0, False], [1, False], [5, True], [11, True]]],
        [1, 10, [[0, False], [3, True], [9, True], [10, True]]],
        [3, 10, [[0, False], [4, False], [8, True], [12, False], [13, False], [14, True]]],
        [3, 10, [[0, False], [4, False], [9, False], [10, True], [18, True], [19, False]]],
        [0, 10, [[0, False], [1, False], [2, False], [3, True]]],
        [2, 5, [[0, False], [5, False], [6, False], [7, True], [11, True]]],
        [2, 10, []],
        [2, 10, [[0, True], [1, True], [2, True]]],
        [1, 30, [[0, False], [10, False], [29, False], [30, False], [31, True], [60, True]]],
        [2, 10, [[0, False], [1, True], [2, False], [3, True], [12, False], [13, True], [25, False], [30, False]]],
        [5, 60, [[i, False] for i in range(12)] + [[70, True], [71, False]]],
        [2, 1, [[0, False], [1, False], [2, False], [2, False], [2, True], [3, True]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def passive_health(max_fails, fail_timeout, events):
    count = 0
    unavailable_until = None
    out = []
    for t, would_succeed in events:
        if unavailable_until is not None and t < unavailable_until:
            out.append("skipped")
            continue
        if would_succeed:
            out.append("ok")
            continue
        out.append("fail")
        count += 1
        if max_fails > 0 and count >= max_fails:
            unavailable_until = t + fail_timeout
            count = 0
    return out
''',
        '''def passive_health(max_fails, fail_timeout, events):
    return ["ok" if ok else "fail" for _, ok in events]
''',
    ],
    guide=dict(
        prereqs="Lesson: *Health checks, retries, draining and slow start*. Lists and conditionals.",
        intuition="`fail_timeout` plays two roles: it is the window in which failures are counted and the length of the time-out once the count is reached. While a server is in time-out NGINX sends it nothing, so it cannot learn whether the server recovered until the time-out ends and a real request is risked.",
        hints=[
            "Check the unavailable period first. A skipped event must not change any state.",
            "Before adding a failure, drop the ones that are `fail_timeout` or more seconds old.",
            "Handle `max_fails = 0` explicitly, or zero failures would satisfy `>= 0` at once.",
        ],
        brute_force="Count failures for ever with a single integer. It gives the same answer only when failures arrive close together; two failures an hour apart would wrongly disable a server configured with `max_fails=2 fail_timeout=10s`.",
        approach="1. State: a list of recent failure times and `unavailable_until`.\n2. For each event: skipped if inside the unavailable period; `ok` if it would succeed; otherwise `fail`, prune old failures, append, and if the count reaches `max_fails` set `unavailable_until = t + fail_timeout` and clear the list.\n\nDry run of the example: t=0 fail (1 remembered), t=1 fail (2 → unavailable until 11), t=5 skipped even though the server has recovered, t=11 tried again → ok.",
        complexity="Time O(events × max_fails) because the remembered list never exceeds `max_fails` entries; space O(max_fails).",
        pitfalls="Counting failures outside the window; changing state on skipped events; forgetting that the boundary `t == unavailable_until` is available again; letting `max_fails = 0` disable the server.",
        follow_up="Extend to several servers with round robin and `proxy_next_upstream`: a failed attempt is retried on the next available server, and when all are unavailable the client receives 502.",
    ),
),
dict(
    id="nginx-map-eval",
    title="Evaluate a map Block",
    difficulty="Medium",
    pattern="Traffic Management",
    entry="map_eval",
    description=r"""
A `map` block computes one variable from another by looking it up in a table. Write `map_eval(entries, source)` that
returns the resulting value.

`entries` is a list of `[pattern, value]` in configuration order. A pattern is one of:

- the word `default`: the value used when nothing else matches (if there is no `default` entry, the result is `""`);
- a **regular expression**: starts with `~` (case-sensitive) or `~*` (case-insensitive); test the rest with
  `re.search`;
- anything else: a **plain string**, compared with the source **ignoring letter case**. The empty string `""` is a
  valid plain pattern and matches an empty source.

Order of evaluation, whatever the order in the file:

1. plain strings (an exact match wins immediately),
2. regular expressions, in the order they are written; the first that matches wins,
3. the default.

**Example:** `[["default", "0"], ["~^5", "1"], ["503", "skip"]]`: source `"503"` → `"skip"`; `"502"` → `"1"`;
`"200"` → `"0"`
""",
    starter='''def map_eval(entries, source):
    # return the mapped value
    pass
''',
    solution=r'''import re

def map_eval(entries, source):
    default = ""
    for pattern, value in entries:
        if pattern == "default":
            default = value
    lowered = source.lower()
    for pattern, value in entries:
        if pattern != "default" and not pattern.startswith("~") and pattern.lower() == lowered:
            return value
    for pattern, value in entries:
        if pattern.startswith("~*"):
            if re.search(pattern[2:], source, re.I):
                return value
        elif pattern.startswith("~"):
            if re.search(pattern[1:], source):
                return value
    return default
''',
    tests=[
        [[["default", "0"], ["~^5", "1"], ["503", "skip"]], "503"],
        [[["default", "0"], ["~^5", "1"], ["503", "skip"]], "502"],
        [[["default", "0"], ["~^5", "1"], ["503", "skip"]], "200"],
        [[["~^[23]", "0"], ["default", "1"]], "404"],
        [[["default", "upgrade"], ["", "close"]], ""],
        [[["default", "upgrade"], ["", "close"]], "websocket"],
        [[["GET", "read"], ["post", "write"]], "POST"],
        [[["GET", "read"], ["post", "write"]], "DELETE"],
        [[["~Googlebot", "bot"], ["~*curl", "tool"], ["default", "human"]], "CURL/8.5"],
        [[["~Googlebot", "bot"], ["~*curl", "tool"], ["default", "human"]], "googlebot/2.1"],
        [[["~^/api/", "api"], ["~\\.json$", "json"], ["default", "page"]], "/api/data.json"],
        [[["~\\.json$", "json"], ["~^/api/", "api"], ["default", "page"]], "/api/data.json"],
        [[], "anything"],
        [[["~.", "nonempty"], ["default", "empty"]], ""],
    ],
    examples=3,
    wrong_solutions=[
        r'''import re

def map_eval(entries, source):
    default = ""
    for pattern, value in entries:
        if pattern == "default":
            default = value
        elif pattern.startswith("~*"):
            if re.search(pattern[2:], source, re.I):
                return value
        elif pattern.startswith("~"):
            if re.search(pattern[1:], source):
                return value
        elif pattern.lower() == source.lower():
            return value
    return default
''',
        r'''import re

def map_eval(entries, source):
    default = ""
    for pattern, value in entries:
        if pattern == "default":
            default = value
    for pattern, value in entries:
        if pattern != "default" and not pattern.startswith("~") and pattern == source:
            return value
    for pattern, value in entries:
        if pattern.startswith("~") and re.search(pattern.lstrip("~*"), source, re.I):
            return value
    return default
''',
    ],
    guide=dict(
        prereqs="Lesson: *A/B testing, map, geo and finding the real client*. `re.search` and the `re.I` flag.",
        intuition="A `map` is a lookup table with three tiers of authority. An exact string is the most specific statement and always wins. Regular expressions are tried next in the order written. The default catches the rest. Position in the file matters only among the regexes.",
        hints=[
            "Make three passes over the entries instead of one.",
            "Plain strings are compared without regard to case; regexes follow their own `~` or `~*` marker.",
            "Find the default in advance, because it may be written anywhere in the block.",
        ],
        brute_force="One pass that returns the first entry that matches in any way. It breaks as soon as a regex is written above an exact string that it also matches, as in the first example.",
        approach="1. Scan for `default`.\n2. Scan plain strings for a case-insensitive equal.\n3. Scan regexes in order.\n4. Return the default.\n\nDry run of `[default→0, ~^5→1, 503→skip]` with `503`: pass 1 finds the default `0`. Pass 2 finds the plain string `503` → `skip`. The regex `^5`, written earlier in the file, is never consulted.",
        complexity="Time O(entries × cost of a regex search); space O(1). NGINX stores the plain strings in a hash table, making pass 2 constant time.",
        pitfalls="Using file order for everything; case-sensitive comparison of plain strings; applying `re.I` to `~` patterns; returning `None` instead of the empty string when there is no default.",
        follow_up="Add the `hostnames` parameter, which enables wildcard patterns such as `*.example.com` evaluated between the plain strings and the regexes.",
    ),
),
dict(
    id="nginx-split-clients",
    title="split_clients: Percentage Buckets",
    difficulty="Medium",
    pattern="Traffic Management",
    entry="split_clients",
    description=r"""
`split_clients` assigns each request to a variant for A/B testing. It hashes a key to a 32-bit number and compares the
number with cumulative percentage thresholds. Write the comparison part.

`split_clients(buckets, hash_value)`:

- `buckets` is a list of `[percent, value]` in order. `percent` is a string such as `"10%"` or `"0.5%"` with at most
  two decimal places, or `"*"` meaning "everything that is left".
- `hash_value` is an integer from 0 to 4294967295 (`0xffffffff`).

Go through the buckets in order, keeping a running total of the percentages in **hundredths of a percent** (so `10%`
is 1000 and `0.5%` is 50). For each bucket:

- if its percent is `"*"`, return its value;
- otherwise add it to the total and compute `threshold = total * 4294967295 // 10000` with integer arithmetic; if
  `hash_value < threshold`, return its value.

If no bucket is chosen, return `""`.

**Example:** `[["10%", "a"], ["0.5%", "b"], ["*", "c"]]`: hash `0` → `"a"`; hash `440000000` → `"b"`;
hash `4000000000` → `"c"`
""",
    starter='''def split_clients(buckets, hash_value):
    # return the value of the chosen bucket, or ""
    pass
''',
    solution='''def split_clients(buckets, hash_value):
    total = 0
    for percent, value in buckets:
        if percent == "*":
            return value
        total += round(float(percent.rstrip("%")) * 100)
        if hash_value < total * 4294967295 // 10000:
            return value
    return ""
''',
    tests=[
        [[["10%", "a"], ["0.5%", "b"], ["*", "c"]], 0],
        [[["10%", "a"], ["0.5%", "b"], ["*", "c"]], 440000000],
        [[["10%", "a"], ["0.5%", "b"], ["*", "c"]], 4000000000],
        [[["10%", "a"], ["0.5%", "b"], ["*", "c"]], 429496728],
        [[["10%", "a"], ["0.5%", "b"], ["*", "c"]], 429496729],
        [[["10%", "a"], ["0.5%", "b"], ["*", "c"]], 450971564],
        [[["10%", "a"], ["0.5%", "b"], ["*", "c"]], 450971565],
        [[["50%", "x"], ["50%", "y"]], 2147483646],
        [[["50%", "x"], ["50%", "y"]], 2147483647],
        [[["50%", "x"], ["50%", "y"]], 4294967295],
        [[["20%", "new"]], 3000000000],
        [[["33.33%", "a"], ["33.33%", "b"], ["*", "c"]], 2863025798],
        [[["*", "only"]], 123456],
        [[], 5],
        [[["1%", "canary"], ["*", "stable"]], 42949672],
    ],
    examples=3,
    wrong_solutions=[
        '''def split_clients(buckets, hash_value):
    slot = hash_value % 100
    total = 0
    for percent, value in buckets:
        if percent == "*":
            return value
        total += int(float(percent.rstrip("%")))
        if slot < total:
            return value
    return ""
''',
        '''def split_clients(buckets, hash_value):
    for percent, value in buckets:
        if percent == "*":
            return value
        if hash_value < round(float(percent.rstrip("%")) * 100) * 4294967295 // 10000:
            return value
    return ""
''',
    ],
    guide=dict(
        prereqs="Lesson: *A/B testing, map, geo and finding the real client*. Integer division.",
        intuition="Lay the whole range of 32-bit numbers out as a ruler. Each bucket claims the next stretch of it, as long as its percentage. A request's hash is a point on the ruler, and the bucket whose stretch contains the point wins. Because the hash of a given key never changes, a user stays in the same bucket.",
        hints=[
            "Thresholds are cumulative: the second bucket's threshold uses the sum of the first two percentages.",
            "Work in hundredths of a percent so that `0.5%` is the integer 50 and no fractions are compared.",
            "Use `round(...)` when converting, since `33.33 * 100` is not exactly 3333 in floating point.",
        ],
        brute_force="Reduce the hash with `% 100` and compare with whole percentages. It cannot represent `0.5%`, and it uses only the low digits of the hash. NGINX compares against the full 32-bit range.",
        approach="1. `total = 0`.\n2. For each bucket: `*` returns at once; otherwise add its hundredths, compute the threshold, compare.\n3. Fall through to `\"\"`.\n\nDry run with `10%`, `0.5%`, `*` and hash 440000000: threshold 1 = 1000 × 4294967295 // 10000 = 429496729, and the hash is not below it. Threshold 2 = 1050 × 4294967295 // 10000 = 450971565, and the hash is below it → `b`.",
        complexity="Time O(number of buckets); space O(1).",
        pitfalls="Comparing against each bucket's own percentage instead of the running total; using `<=`; float rounding when parsing; assuming percentages that sum to 100 cover every hash (the largest hash value, 4294967295, is not below the final threshold, a real quirk of the integer arithmetic).",
        follow_up="NGINX hashes the key with MurmurHash2. Implement that hash and verify that about 10% of 100,000 random keys fall in a `10%` bucket.",
    ),
),
dict(
    id="nginx-limit-conn",
    title="limit_conn: Cap Simultaneous Connections per Key",
    difficulty="Easy",
    pattern="Traffic Management",
    entry="limit_conn",
    description=r"""
`limit_conn zone N;` allows at most `N` requests in progress at the same moment for each key (usually the client
address). Write `limit_conn(limit, events)`.

`events` is a list in time order:

- `["open", conn_id, key]`: a request starts. Decide `"pass"` or `"reject"`.
- `["close", conn_id]`: that request ends.

Rules:

- A request is rejected when its key already has `limit` requests in progress. A rejected request is **not counted**
  and its later `close` event changes nothing.
- A request whose key is the empty string is always passed and never counted.
- A `close` for an unknown `conn_id` is ignored.

Return the list of verdicts for the `open` events, in order.

**Example:** `limit=2`, events `[["open",1,"a"], ["open",2,"a"], ["open",3,"a"], ["close",1], ["open",4,"a"]]`
→ `["pass", "pass", "reject", "pass"]`
""",
    starter='''def limit_conn(limit, events):
    # return "pass" or "reject" for each open event
    pass
''',
    solution='''def limit_conn(limit, events):
    counts = {}
    owner = {}
    out = []
    for event in events:
        if event[0] == "open":
            conn_id, key = event[1], event[2]
            if key == "":
                out.append("pass")
            elif counts.get(key, 0) >= limit:
                out.append("reject")
            else:
                counts[key] = counts.get(key, 0) + 1
                owner[conn_id] = key
                out.append("pass")
        else:
            key = owner.pop(event[1], None)
            if key is not None:
                counts[key] -= 1
    return out
''',
    tests=[
        [2, [["open", 1, "a"], ["open", 2, "a"], ["open", 3, "a"], ["close", 1], ["open", 4, "a"]]],
        [1, [["open", 1, "a"], ["open", 2, "b"], ["open", 3, "a"], ["open", 4, "b"]]],
        [1, [["open", 1, "a"], ["open", 2, "a"], ["close", 2], ["open", 3, "a"], ["close", 1], ["open", 4, "a"]]],
        [2, [["open", 1, ""], ["open", 2, ""], ["open", 3, ""], ["close", 1]]],
        [0, [["open", 1, "a"], ["open", 2, ""]]],
        [3, []],
        [1, [["close", 99], ["open", 1, "a"], ["close", 1], ["close", 1], ["open", 2, "a"], ["open", 3, "a"]]],
        [2, [["open", 1, "a"], ["open", 2, "a"], ["open", 3, "a"], ["open", 4, "a"], ["close", 3], ["close", 4], ["open", 5, "a"], ["close", 1], ["open", 6, "a"]]],
        [3, [["open", i, "k%d" % (i % 2)] for i in range(10)]],
        [2, [["open", 1, "x"], ["close", 1], ["open", 2, "x"], ["close", 2], ["open", 3, "x"], ["open", 4, "x"], ["open", 5, "x"]]],
        [5, [["open", i, "ip"] for i in range(200)] + [["close", i] for i in range(200)] + [["open", 1000, "ip"]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def limit_conn(limit, events):
    counts = {}
    owner = {}
    out = []
    for event in events:
        if event[0] == "open":
            conn_id, key = event[1], event[2]
            owner[conn_id] = key
            counts[key] = counts.get(key, 0) + 1
            out.append("pass" if key == "" or counts[key] <= limit else "reject")
        else:
            key = owner.pop(event[1], None)
            if key is not None:
                counts[key] -= 1
    return out
''',
        '''def limit_conn(limit, events):
    counts = {}
    out = []
    for event in events:
        if event[0] == "open":
            key = event[2]
            if counts.get(key, 0) >= limit:
                out.append("reject")
            else:
                counts[key] = counts.get(key, 0) + 1
                out.append("pass")
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson: *Limiting request rate, connections and bandwidth*. Dictionaries.",
        intuition="This is a counter per key that goes up when a request starts and down when it ends. The only subtlety is bookkeeping: a rejected request never entered, so it must not be counted on the way in or on the way out.",
        hints=[
            "Keep two dictionaries: key → current count, and connection id → key (for accepted requests only).",
            "Decide before incrementing: reject when the count is already at the limit.",
            "On close, look the connection up; if it is not there it was rejected, exempt or unknown, so do nothing.",
        ],
        brute_force="Keep a list of open connections and count those with the same key on every `open`: O(n) per event. The dictionary of counts makes it O(1).",
        approach="1. `counts = {}`, `owner = {}`.\n2. `open`: empty key → pass. Count at limit → reject. Otherwise count up, remember the owner, pass.\n3. `close`: pop the owner; if found, count down.\n\nDry run of the example with limit 2: opens 1 and 2 pass (count 2). Open 3 is rejected and not recorded. Close 1 brings the count to 1. Open 4 passes.",
        complexity="Time O(number of events); space O(open connections + distinct keys).",
        pitfalls="Counting rejected requests, which makes the key stay over the limit for ever; decrementing on the close of a rejected request; counting the empty key; forgetting that `limit=0` rejects everything with a non-empty key.",
        follow_up="Apply two zones at once, per address and per virtual server, and reject if either is full, as in `limit_conn perip 10; limit_conn perserver 500;`.",
    ),
),
dict(
    id="nginx-limit-req",
    title="limit_req: the Leaky Bucket with burst and nodelay",
    difficulty="Medium",
    pattern="Traffic Management",
    entry="limit_req",
    description=r"""
Implement NGINX's request rate limiter for one zone. `limit_req(rate, burst, nodelay, requests)`:

- `rate`: allowed requests per second (a positive integer).
- `burst`: how many requests above the rate may be accepted (0 or more).
- `nodelay`: `True` to forward accepted requests at once, `False` to delay them so that they leave at the rate.
- `requests`: a list of `[key, time_ms]` in increasing time order.

Return one `[verdict, delay_ms]` per request, where the verdict is `"pass"` or `"reject"`.

NGINX keeps, per key, an integer `excess` in **thousandths of a request** and the time of the last accepted request:

- A key seen for the first time: store `excess = 0`, answer `["pass", 0]`.
- Otherwise compute `excess = max(0, stored_excess - rate * (now - last) + 1000)`, with times in milliseconds.
  - If `excess > burst * 1000`: answer `["reject", 0]` and **leave the stored state unchanged**.
  - Else store the new `excess` and `now`, and answer `["pass", delay]` where `delay` is `0` with `nodelay` and
    `excess // rate` milliseconds without it.
- A request with the empty string as key is not limited: `["pass", 0]`, and nothing is stored.

**Example:** `rate=5, burst=0`, one key at times `0, 1, 200` → `pass, reject, pass` (5 r/s means one per 200 ms)

**Example:** `rate=5, burst=3, nodelay=False`, one key at `0, 0, 0` → delays `0, 200, 400`
""",
    starter='''def limit_req(rate, burst, nodelay, requests):
    # return [verdict, delay_ms] for each request
    pass
''',
    solution='''def limit_req(rate, burst, nodelay, requests):
    state = {}
    out = []
    for key, now in requests:
        if key == "":
            out.append(["pass", 0])
            continue
        if key not in state:
            state[key] = (0, now)
            out.append(["pass", 0])
            continue
        excess, last = state[key]
        excess = max(0, excess - rate * (now - last) + 1000)
        if excess > burst * 1000:
            out.append(["reject", 0])
            continue
        state[key] = (excess, now)
        out.append(["pass", 0 if nodelay else excess // rate])
    return out
''',
    tests=[
        [5, 0, False, [["a", 0], ["a", 1], ["a", 200]]],
        [5, 3, False, [["a", 0], ["a", 0], ["a", 0]]],
        [5, 3, True, [["a", 0], ["a", 1], ["a", 2], ["a", 3], ["a", 4], ["a", 5], ["a", 400], ["a", 401], ["a", 402]]],
        [5, 3, False, [["a", 0], ["a", 1], ["a", 2], ["a", 3], ["a", 4], ["a", 5]]],
        [1, 5, True, [["a", 0]] * 8],
        [10, 0, True, [["a", i * 100] for i in range(6)]],
        [10, 0, True, [["a", i * 99] for i in range(6)]],
        [2, 5, True, [["a", 0]] * 10 + [["a", 1000]] * 4],
        [5, 2, True, [["a", 0], ["b", 0], ["a", 1], ["b", 1], ["a", 2], ["b", 2], ["a", 3], ["b", 3]]],
        [5, 0, True, [["", 0], ["", 0], ["", 1], ["x", 1], ["x", 2]]],
        [3, 4, False, []],
        [100, 20, False, [["k", t] for t in range(0, 60, 2)]],
        [1, 1, True, [["a", 0], ["a", 10], ["a", 20], ["a", 1010], ["a", 1020], ["a", 5000], ["a", 5001], ["a", 5002]]],
        [20, 40, True, [["ip", i] for i in range(300)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def limit_req(rate, burst, nodelay, requests):
    state = {}
    out = []
    for key, now in requests:
        if key == "":
            out.append(["pass", 0])
            continue
        if key not in state:
            state[key] = (0, now)
            out.append(["pass", 0])
            continue
        excess, last = state[key]
        excess = max(0, excess - rate * (now - last) + 1000)
        state[key] = (excess, now)
        if excess > burst * 1000:
            out.append(["reject", 0])
            continue
        out.append(["pass", 0 if nodelay else excess // rate])
    return out
''',
        '''def limit_req(rate, burst, nodelay, requests):
    windows = {}
    out = []
    for key, now in requests:
        if key == "":
            out.append(["pass", 0])
            continue
        slot = (key, now // 1000)
        windows[slot] = windows.get(slot, 0) + 1
        if windows[slot] > rate + burst:
            out.append(["reject", 0])
        else:
            out.append(["pass", 0])
    return out
''',
        '''def limit_req(rate, burst, nodelay, requests):
    state = {}
    out = []
    for key, now in requests:
        if key == "":
            out.append(["pass", 0])
            continue
        if key not in state:
            state[key] = (0, now)
            out.append(["pass", 0])
            continue
        excess, last = state[key]
        excess = max(0, excess - rate * (now - last)) + 1000
        if excess > burst * 1000:
            out.append(["reject", 0])
            continue
        state[key] = (excess, now)
        out.append(["pass", 0 if nodelay else excess // rate])
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson: *Limiting request rate, connections and bandwidth*. Integer arithmetic and dictionaries.",
        intuition="Picture a bucket per client. Each request adds one unit; the bucket leaks `rate` units per second. `excess` is the level after adding the new request. If the level would rise above `burst`, the request is refused and the bucket is left as it was. Working in thousandths keeps everything in integers, as NGINX does.",
        hints=[
            "With times in milliseconds and excess in thousandths, the leak since the last accepted request is `rate * (now - last)` with no division.",
            "Add the new request (1000) before clamping at zero, not after.",
            "A rejected request must not update the stored excess or the stored time, or a client that keeps hammering would never be let back in.",
        ],
        brute_force="Count requests per key in fixed one-second windows and reject above `rate + burst`. It is simple and behaves differently: it allows a double burst across a window boundary and cannot express \"one per 200 ms\".",
        approach="1. `state[key] = (excess, last_ms)`.\n2. Empty key → pass, untouched state.\n3. New key → store `(0, now)`, pass.\n4. Else compute the new excess; compare with `burst * 1000`; reject without storing, or store and compute the delay.\n\nDry run, `rate=5, burst=0`, times 0, 1, 200: first request stores excess 0. At 1 ms: `0 - 5·1 + 1000 = 995 > 0` → reject, state unchanged. At 200 ms: `0 - 5·200 + 1000 = 0`, not above 0 → pass.",
        complexity="Time O(number of requests); space O(number of distinct keys).",
        pitfalls="Updating state on rejection; clamping before adding the request, which makes `burst=0` reject every request after the first; using `>=` for the comparison; forgetting the exempt empty key; floating-point drift.",
        follow_up="Add the `delay=N` parameter: the first N excess requests pass without delay and later ones are delayed by `(excess - N*1000) // rate` milliseconds.",
    ),
),
]
