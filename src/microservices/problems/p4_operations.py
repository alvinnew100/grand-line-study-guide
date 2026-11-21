PROBLEMS = [
dict(
    id="msvc-trace-slowest-path",
    title="Rebuild a Distributed Trace and Find the Slowest Path",
    difficulty="Hard",
    pattern="Observability",
    entry="analyse_trace",
    description=r"""
A distributed trace arrives as an unordered list of spans. Each span is `[span_id, parent_id, service, start, end]` with integer times in milliseconds and `start <= end`. Exactly one span has `parent_id` equal to `None` (the root); every other parent id exists in the list. A child's interval lies inside its parent's interval. Children of the same parent may overlap each other (parallel calls).

Compute:

1. **Self time** of every span: its duration minus the total time covered by its children. Overlapping children must not be counted twice: take the length of the union of the child intervals.
2. **Slowest path**: start at the root and repeatedly move to the child with the longest duration (`end - start`); break ties by the earlier `start`, then by the smaller `span_id` (string comparison). Stop at a span with no children. The path is the list of span ids visited.
3. **Bottleneck**: the span with the largest self time in the whole trace; break ties by the smaller `span_id`.

Return `{"path": [...], "bottleneck": span_id, "self_time": {span_id: ms}}`.

**Example:** spans `["a", None, "web", 0, 100]`, `["b", "a", "booking", 10, 60]`, `["c", "a", "billing", 40, 90]`, `["d", "b", "db", 20, 50]` → path `["a", "b", "d"]`; self times a: 100 − 80 = 20, b: 50 − 30 = 20, c: 50, d: 30; bottleneck `"c"`.
""",
    starter='''def analyse_trace(spans: List[list]) -> dict:
    pass
''',
    solution='''def analyse_trace(spans):
    info = {s[0]: s for s in spans}
    children = {s[0]: [] for s in spans}
    root = None
    for sid, parent, _, _, _ in spans:
        if parent is None:
            root = sid
        else:
            children[parent].append(sid)
    self_time = {}
    for sid, _, _, start, end in spans:
        covered = 0
        cur_s = cur_e = None
        for s, e in sorted((info[c][3], info[c][4]) for c in children[sid]):
            if cur_e is None or s > cur_e:
                if cur_e is not None:
                    covered += cur_e - cur_s
                cur_s, cur_e = s, e
            else:
                cur_e = max(cur_e, e)
        if cur_e is not None:
            covered += cur_e - cur_s
        self_time[sid] = (end - start) - covered
    path = [root]
    while children[path[-1]]:
        kids = children[path[-1]]
        path.append(min(kids, key=lambda c: (-(info[c][4] - info[c][3]), info[c][3], c)))
    bottleneck = min(self_time, key=lambda k: (-self_time[k], k))
    return {"path": path, "bottleneck": bottleneck, "self_time": self_time}
''',
    tests=[
        [[["a", None, "web", 0, 100], ["b", "a", "booking", 10, 60], ["c", "a", "billing", 40, 90], ["d", "b", "db", 20, 50]]],
        [[["root", None, "web", 0, 10]]],
        [[["b", "a", "x", 0, 5], ["a", None, "web", 0, 10], ["c", "a", "y", 5, 10]]],
        [[["a", None, "web", 0, 100], ["b", "a", "x", 10, 30], ["c", "a", "y", 50, 70]]],
        [[["a", None, "web", 0, 100], ["b", "a", "x", 10, 30], ["c", "a", "y", 10, 30], ["d", "a", "z", 10, 30]]],
        [[["a", None, "web", 0, 100], ["b", "a", "x", 0, 100], ["c", "b", "y", 0, 100], ["d", "c", "z", 0, 100]]],
        [[["a", None, "web", 0, 50], ["z", "a", "x", 0, 20], ["y", "a", "x", 5, 25], ["x", "a", "x", 24, 40], ["w", "a", "x", 45, 50]]],
        [[["d", "b", "db", 12, 18], ["c", "a", "cache", 40, 41], ["b", "a", "booking", 10, 30], ["a", None, "gateway", 0, 45], ["e", "b", "db", 20, 29], ["f", "e", "disk", 21, 28]]],
        [[["a", None, "web", 5, 5]]],
        [[["a", None, "web", 0, 30], ["b", "a", "x", 0, 10], ["c", "a", "x", 10, 20], ["d", "a", "x", 20, 30]]],
        [[["s0", None, "svc", 0, 1000]] + [["s%d" % i, "s%d" % (i - 1), "svc", i, 1000 - i] for i in range(1, 120)]],
        [[["r", None, "web", 0, 200]] + [["k%02d" % i, "r", "w", i * 3, i * 3 + 10] for i in range(40)] + [["leaf", "k07", "db", 22, 30]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def analyse_trace(spans):
    info = {s[0]: s for s in spans}
    children = {s[0]: [] for s in spans}
    root = None
    for sid, parent, _, _, _ in spans:
        if parent is None:
            root = sid
        else:
            children[parent].append(sid)
    self_time = {sid: (e - s) - sum(info[c][4] - info[c][3] for c in children[sid]) for sid, _, _, s, e in spans}
    path = [root]
    while children[path[-1]]:
        path.append(min(children[path[-1]], key=lambda c: (-(info[c][4] - info[c][3]), info[c][3], c)))
    bottleneck = min(self_time, key=lambda k: (-self_time[k], k))
    return {"path": path, "bottleneck": bottleneck, "self_time": self_time}
''',
        '''def analyse_trace(spans):
    info = {s[0]: s for s in spans}
    children = {s[0]: [] for s in spans}
    root = spans[0][0]
    for sid, parent, _, _, _ in spans:
        if parent is not None:
            children[parent].append(sid)
    self_time = {}
    for sid, _, _, start, end in spans:
        covered, cur_s, cur_e = 0, None, None
        for s, e in sorted((info[c][3], info[c][4]) for c in children[sid]):
            if cur_e is None or s > cur_e:
                if cur_e is not None:
                    covered += cur_e - cur_s
                cur_s, cur_e = s, e
            else:
                cur_e = max(cur_e, e)
        if cur_e is not None:
            covered += cur_e - cur_s
        self_time[sid] = (end - start) - covered
    path = [root]
    while children[path[-1]]:
        path.append(max(children[path[-1]], key=lambda c: info[c][4] - info[c][3]))
    bottleneck = max(self_time, key=lambda k: self_time[k])
    return {"path": path, "bottleneck": bottleneck, "self_time": self_time}
''',
    ],
    guide=dict(
        prereqs="Distributed tracing from the lesson *Logs, metrics and traces*. Trees stored as parent pointers; merging intervals.",
        intuition="A trace is a tree of timed boxes. The time a service spends itself is its box minus whatever its children cover. If children ran in parallel their boxes overlap, so you must measure the covered ground once, like the shadow they cast together.",
        hints=[
            "Build `children[parent]` lists from the parent ids; the span with parent `None` is the root.",
            "For self time, sort the child intervals by start and merge overlapping ones before adding their lengths.",
            "For the path, pick the next child with `min` and a key tuple `(-duration, start, span_id)`.",
        ],
        brute_force="Mark every millisecond of the parent that some child covers in a boolean array and count the unmarked ones: O(duration) per span. Interval merging does the same in O(k log k) for k children, regardless of how long the spans are.",
        approach="1. Index spans by id and build child lists. 2. For each span merge its children's intervals and subtract the union from its duration. 3. Walk from the root choosing the longest child. 4. Take the maximum self time with the id tie-break.\n\n**Dry run** on the example: children of `a` are b [10, 60] and c [40, 90]; the union is [10, 90] = 80, so self(a) = 20. Children of `b`: d [20, 50] = 30, self(b) = 20. Path: from a, b and c both last 50; b starts earlier → b, then d. The largest self time is c with 50.",
        complexity="Time O(n log n) for the sorting of child intervals; space O(n).",
        pitfalls="Adding child durations without merging gives negative self times for parallel calls. The input is unordered, so the root is not necessarily first. Touching intervals such as [0, 10] and [10, 20] cover 20 in total, with or without merging.",
        follow_up="In a real tracing tool the slowest path is drawn as the critical path of a waterfall chart. Self time is what you sort by when you look for the service to optimise.",
    ),
),
dict(
    id="msvc-slo-burn-rate",
    title="SLO Burn-rate Alert Evaluation",
    difficulty="Medium",
    pattern="Observability",
    entry="burn_alerts",
    description=r"""
A service level objective (SLO) allows a small share of requests to fail: the **error budget**. The **burn rate** over a time window says how fast the budget is being used: `(errors / total in the window) / allowed error ratio`. A burn rate of 1 uses the budget exactly over the SLO period; 10 uses it ten times too fast.

- `budget_ppm`: the allowed error ratio in parts per million (an SLO of 99.9% gives 1000).
- `samples`: a list of `[minute, total, errors]`, one entry per minute that had traffic, in increasing minute order. "Now" is the minute of the last sample. With no samples, nothing fires.
- `rules`: a list of `[severity, long_window, short_window, threshold]`. Windows are in minutes. A window of `w` minutes covers the samples with `minute > now - w`.

A rule **fires** when the burn rate over the long window **and** over the short window are both at least `threshold`. A window with zero requests has burn rate 0.

To avoid rounding problems, test `burn >= threshold` as `errors * 1_000_000 >= threshold * budget_ppm * total` (with `total > 0`).

Return a list of `[severity, fired]` in rule order.

**Example:** `budget_ppm = 1000`, samples `[[1, 1000, 0], [2, 1000, 0], [3, 1000, 30], [4, 1000, 30]]`, rules `[["page", 4, 2, 14], ["ticket", 4, 4, 3]]` → `[["page", True], ["ticket", True]]` (4-minute burn 15, 2-minute burn 30).
""",
    starter='''def burn_alerts(budget_ppm: int, samples: List[List[int]], rules: List[list]) -> List[list]:
    pass
''',
    solution='''def burn_alerts(budget_ppm, samples, rules):
    if not samples:
        return [[r[0], False] for r in rules]
    now = samples[-1][0]

    def hot(window, threshold):
        total = errors = 0
        for minute, t, e in samples:
            if minute > now - window:
                total += t
                errors += e
        return total > 0 and errors * 1000000 >= threshold * budget_ppm * total

    return [[sev, hot(long_w, thr) and hot(short_w, thr)] for sev, long_w, short_w, thr in rules]
''',
    tests=[
        [1000, [[1, 1000, 0], [2, 1000, 0], [3, 1000, 30], [4, 1000, 30]], [["page", 4, 2, 14], ["ticket", 4, 4, 3]]],
        [1000, [[1, 1000, 100], [2, 1000, 100], [3, 1000, 0], [4, 1000, 0]], [["page", 4, 2, 14]]],
        [1000, [], [["page", 60, 5, 14]]],
        [1000, [[5, 0, 0]], [["page", 60, 5, 1]]],
        [1000, [[1, 1000, 1]], [["exact", 1, 1, 1], ["above", 1, 1, 2]]],
        [1000, [[1, 1000, 500], [100, 1000, 0]], [["page", 60, 5, 1], ["old", 100, 100, 1], ["long", 100, 1, 1]]],
        [10000, [[i, 100, 3] for i in range(1, 61)], [["page", 60, 5, 14], ["ticket", 60, 30, 3], ["tight", 60, 30, 4]]],
        [1000, [[10, 200, 0], [11, 200, 50], [12, 200, 0]], [["a", 3, 1, 5], ["b", 3, 2, 5], ["c", 2, 2, 100]]],
        [500, [[1, 10, 10]], []],
        [1000, [[1, 1000, 0], [2, 1000, 0], [3, 1000, 0], [4, 1000, 60]], [["page", 4, 1, 14], ["page2", 4, 1, 15], ["page3", 4, 1, 16]]],
        [100, [[i, 5000, 1 if i % 10 == 0 else 0] for i in range(1, 361)] + [[361, 5000, 400]], [["fast", 60, 5, 14], ["slow", 360, 30, 6], ["never", 360, 30, 50]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def burn_alerts(budget_ppm, samples, rules):
    if not samples:
        return [[r[0], False] for r in rules]
    now = samples[-1][0]
    def hot(window, threshold):
        total = sum(t for m, t, e in samples if m > now - window)
        errors = sum(e for m, t, e in samples if m > now - window)
        return total > 0 and errors * 1000000 >= threshold * budget_ppm * total
    return [[sev, hot(long_w, thr)] for sev, long_w, short_w, thr in rules]
''',
        '''def burn_alerts(budget_ppm, samples, rules):
    if not samples:
        return [[r[0], False] for r in rules]
    now = samples[-1][0]
    def hot(window, threshold):
        total = sum(t for m, t, e in samples if m >= now - window)
        errors = sum(e for m, t, e in samples if m >= now - window)
        return total > 0 and errors * 1000000 > threshold * budget_ppm * total
    return [[sev, hot(long_w, thr) and hot(short_w, thr)] for sev, long_w, short_w, thr in rules]
''',
    ],
    guide=dict(
        prereqs="SLOs, error budgets and alerting from the lesson *Are we doing OK*. Ratios; summing over a filtered list.",
        intuition="The long window proves the problem is significant; the short window proves it is still happening. Requiring both stops the alert from firing on a brief blip and from staying on long after a fix.",
        hints=[
            "`now` is the minute of the last sample; a window of w minutes keeps samples with `minute > now - w`.",
            "Write a helper that, for a window and a threshold, sums totals and errors and applies the integer inequality.",
            "A rule fires only if the helper is true for both of its windows.",
        ],
        brute_force="Recomputing the sums for each rule is O(rules × samples), which is what the reference does and is fine here. For long histories, prefix sums over the minutes make each window O(log n) with a binary search.",
        approach="Guard the empty case. For each rule call `hot(long)` and `hot(short)`.\n\n**Dry run** on the example, page rule (4, 2, 14): long window covers minutes 1–4: 60 errors of 4000 → 15000 ppm → burn 15 ≥ 14. Short window covers minutes 3–4: 60 of 2000 → burn 30 ≥ 14. Fires. Ticket rule (4, 4, 3): burn 15 ≥ 3 → fires.",
        complexity="Time O(R × S); space O(1) beyond the output.",
        pitfalls="Using only the long window. An off-by-one on the window edge (`>=` would include one minute too many). Dividing by a zero total. Comparing floats at the boundary instead of cross-multiplying.",
        follow_up="The classic pairing is a fast rule (1 hour and 5 minutes at burn 14.4) that pages a person and a slow rule (6 hours and 30 minutes at burn 6) that opens a ticket.",
    ),
),
dict(
    id="msvc-canary-decision",
    title="Canary Analysis Decision",
    difficulty="Easy",
    pattern="Progressive Delivery",
    entry="canary_rollout",
    description=r"""
A canary release sends a growing share of traffic to the new version and compares it with the old one (the baseline) at every step.

- `weights`: the planned traffic percentages for the canary, in increasing order, for example `[5, 25, 50, 100]`.
- `observations`: one dict per step with keys `"base_requests"`, `"base_errors"`, `"canary_requests"`, `"canary_errors"`, `"base_p99"`, `"canary_p99"` (latencies in ms). If there are fewer observations than weights, the missing steps were never reached.
- `rules`: `{"min_requests": int, "max_error_delta_bp": int, "max_latency_pct": int}`.

At each step, in order, decide:

1. `"hold"` if `canary_requests < min_requests` (not enough data). The rollout stays at this weight and evaluation stops.
2. `"rollback"` if the canary's error rate exceeds the baseline's by more than `max_error_delta_bp` basis points (1 basis point = 0.01%), **or** `canary_p99 * 100 > base_p99 * max_latency_pct`. The final weight is 0 and evaluation stops. Compare error rates without division: `canary_errors * base_requests * 10000 > base_errors * canary_requests * 10000 + max_error_delta_bp * base_requests * canary_requests`. If `base_requests` is 0, treat the baseline error rate as 0, that is: `canary_errors * 10000 > max_error_delta_bp * canary_requests`.
3. Otherwise `"promote"` and move to the next weight.

If a step has no observation, evaluation stops with the rollout at that weight. If every step is promoted, the final weight is the last weight.

Return `{"decisions": [[weight, decision], ...], "final_weight": int}`.

**Example:** weights `[10, 50, 100]`, rules `{min_requests: 100, max_error_delta_bp: 50, max_latency_pct: 120}`, observations: step 1 healthy, step 2 with canary errors 30 of 1000 against baseline 1 of 1000 → `{"decisions": [[10, "promote"], [50, "rollback"]], "final_weight": 0}`
""",
    starter='''def canary_rollout(weights: List[int], observations: List[dict], rules: dict) -> dict:
    pass
''',
    solution='''def canary_rollout(weights, observations, rules):
    decisions = []
    for i, w in enumerate(weights):
        if i >= len(observations):
            return {"decisions": decisions, "final_weight": w}
        o = observations[i]
        if o["canary_requests"] < rules["min_requests"]:
            decisions.append([w, "hold"])
            return {"decisions": decisions, "final_weight": w}
        br, be, cr, ce = o["base_requests"], o["base_errors"], o["canary_requests"], o["canary_errors"]
        if br == 0:
            bad_errors = ce * 10000 > rules["max_error_delta_bp"] * cr
        else:
            bad_errors = ce * br * 10000 > be * cr * 10000 + rules["max_error_delta_bp"] * br * cr
        bad_latency = o["canary_p99"] * 100 > o["base_p99"] * rules["max_latency_pct"]
        if bad_errors or bad_latency:
            decisions.append([w, "rollback"])
            return {"decisions": decisions, "final_weight": 0}
        decisions.append([w, "promote"])
    return {"decisions": decisions, "final_weight": weights[-1] if weights else 0}
''',
    tests=[
        [[10, 50, 100], [{"base_requests": 900, "base_errors": 1, "canary_requests": 100, "canary_errors": 0, "base_p99": 200, "canary_p99": 210},
                         {"base_requests": 1000, "base_errors": 1, "canary_requests": 1000, "canary_errors": 30, "base_p99": 200, "canary_p99": 205}],
         {"min_requests": 100, "max_error_delta_bp": 50, "max_latency_pct": 120}],
        [[10, 100], [{"base_requests": 900, "base_errors": 1, "canary_requests": 100, "canary_errors": 0, "base_p99": 200, "canary_p99": 210},
                     {"base_requests": 10, "base_errors": 0, "canary_requests": 990, "canary_errors": 1, "base_p99": 200, "canary_p99": 239}],
         {"min_requests": 100, "max_error_delta_bp": 50, "max_latency_pct": 120}],
        [[], [], {"min_requests": 1, "max_error_delta_bp": 0, "max_latency_pct": 100}],
        [[5, 25], [], {"min_requests": 1, "max_error_delta_bp": 0, "max_latency_pct": 100}],
        [[5, 25], [{"base_requests": 900, "base_errors": 0, "canary_requests": 99, "canary_errors": 99, "base_p99": 100, "canary_p99": 900}],
         {"min_requests": 100, "max_error_delta_bp": 50, "max_latency_pct": 120}],
        [[5, 25], [{"base_requests": 1000, "base_errors": 10, "canary_requests": 1000, "canary_errors": 15, "base_p99": 100, "canary_p99": 100}],
         {"min_requests": 100, "max_error_delta_bp": 50, "max_latency_pct": 120}],
        [[5, 25], [{"base_requests": 1000, "base_errors": 10, "canary_requests": 1000, "canary_errors": 16, "base_p99": 100, "canary_p99": 100}],
         {"min_requests": 100, "max_error_delta_bp": 50, "max_latency_pct": 120}],
        [[5, 25], [{"base_requests": 1000, "base_errors": 10, "canary_requests": 1000, "canary_errors": 0, "base_p99": 100, "canary_p99": 120}],
         {"min_requests": 100, "max_error_delta_bp": 50, "max_latency_pct": 120}],
        [[5, 25], [{"base_requests": 1000, "base_errors": 10, "canary_requests": 1000, "canary_errors": 0, "base_p99": 100, "canary_p99": 121}],
         {"min_requests": 100, "max_error_delta_bp": 50, "max_latency_pct": 120}],
        [[100], [{"base_requests": 0, "base_errors": 0, "canary_requests": 2000, "canary_errors": 10, "base_p99": 0, "canary_p99": 0}],
         {"min_requests": 100, "max_error_delta_bp": 50, "max_latency_pct": 120}],
        [[100], [{"base_requests": 0, "base_errors": 0, "canary_requests": 2000, "canary_errors": 11, "base_p99": 50, "canary_p99": 50}],
         {"min_requests": 100, "max_error_delta_bp": 50, "max_latency_pct": 120}],
        [[1, 5, 25, 50, 100], [{"base_requests": 5000, "base_errors": 5, "canary_requests": 500 * (i + 1), "canary_errors": i, "base_p99": 300, "canary_p99": 300 + 10 * i} for i in range(5)],
         {"min_requests": 500, "max_error_delta_bp": 10, "max_latency_pct": 110}],
    ],
    examples=2,
    wrong_solutions=[
        '''def canary_rollout(weights, observations, rules):
    decisions = []
    for i, w in enumerate(weights):
        if i >= len(observations):
            return {"decisions": decisions, "final_weight": w}
        o = observations[i]
        bad_errors = o["canary_errors"] > o["base_errors"]
        bad_latency = o["canary_p99"] * 100 > o["base_p99"] * rules["max_latency_pct"]
        if bad_errors or bad_latency:
            decisions.append([w, "rollback"])
            return {"decisions": decisions, "final_weight": 0}
        if o["canary_requests"] < rules["min_requests"]:
            decisions.append([w, "hold"])
            return {"decisions": decisions, "final_weight": w}
        decisions.append([w, "promote"])
    return {"decisions": decisions, "final_weight": weights[-1] if weights else 0}
''',
        '''def canary_rollout(weights, observations, rules):
    decisions = []
    for i, w in enumerate(weights):
        if i >= len(observations):
            break
        o = observations[i]
        if o["canary_requests"] < rules["min_requests"]:
            decisions.append([w, "hold"])
            return {"decisions": decisions, "final_weight": w}
        br, be, cr, ce = o["base_requests"], o["base_errors"], o["canary_requests"], o["canary_errors"]
        bad_errors = ce * max(br, 1) * 10000 >= be * cr * 10000 + rules["max_error_delta_bp"] * max(br, 1) * cr
        bad_latency = o["canary_p99"] * 100 >= o["base_p99"] * rules["max_latency_pct"]
        if bad_errors or bad_latency:
            decisions.append([w, "rollback"])
            return {"decisions": decisions, "final_weight": 0}
        decisions.append([w, "promote"])
    return {"decisions": decisions, "final_weight": weights[-1] if weights else 0}
''',
    ],
    guide=dict(
        prereqs="Canary releases from the lesson *Deployment options and progressive delivery*. Comparing ratios by cross-multiplying.",
        intuition="A canary step answers three questions in order: do I have enough data, is the new version worse than the old one by more than I tolerate, and if neither, may I widen the exposure? Comparing against a live baseline, instead of a fixed number, cancels out whatever else is happening to traffic right now.",
        hints=[
            "Walk the weights with their index; stop when the observations run out.",
            "Check the sample size before anything else: too little data means hold, even if the numbers look terrible.",
            "Use the integer inequalities given in the statement; do not divide.",
        ],
        brute_force="Not a performance problem. The naive version compares raw error counts, which is wrong whenever the canary and the baseline receive different amounts of traffic.",
        approach="For each step: no observation → return current weight. Too few requests → hold. Compute `bad_errors` and `bad_latency` → rollback with weight 0. Else promote.\n\n**Dry run** on the example, step 2: canary 30/1000 = 300 bp, baseline 1/1000 = 10 bp, allowed delta 50 bp. 300 > 60 → rollback, final weight 0.",
        complexity="Time O(steps); space O(steps).",
        pitfalls="Comparing error counts instead of rates. Rolling back on a tiny sample. Using `>=` where the rule says more than. Returning the last weight when observations run out early.",
        follow_up="Real canary analysis uses statistical tests over many metrics, and runs automatically inside the deployment tool. The shape of the decision stays the same.",
    ),
),
dict(
    id="msvc-blue-green",
    title="Blue-green Switch and Rollback",
    difficulty="Medium",
    pattern="Progressive Delivery",
    entry="blue_green",
    description=r"""
Two identical environments, **blue** and **green**, exist side by side. One is live (receives users); the other is idle. Simulate a sequence of operations.

Start: blue is live and runs `initial_version`; green is idle and empty (`None`).

Operations (each appends one string to a log):

- `["deploy", version]`: install `version` on the idle environment. It becomes **unverified**. Log `"deployed <version> to <colour>"`.
- `["smoke", passed]`: record the smoke-test result (`True`/`False`) for the idle environment. If the idle environment is empty log `"nothing to test"`; otherwise it becomes **verified** or **failed** and the log is `"smoke passed"` or `"smoke failed"`.
- `["switch"]`: only allowed when the idle environment holds a verified version. Live and idle swap; log `"switched to <new live colour>"`. The environment that was live keeps its version and counts as verified (it was serving users), which makes a rollback possible. Otherwise log `"switch refused"`.
- `["rollback"]`: allowed when the most recent successful `switch` or `rollback` was a switch, and no `deploy` has happened since. Live and idle swap back; log `"rolled back to <new live colour>"`. Otherwise log `"rollback refused"`.

Return `{"log": [...], "live": colour, "live_version": version, "idle_version": version or None}`.

**Example:** `initial_version = "v1"`, ops `[["deploy","v2"], ["switch"], ["smoke",True], ["switch"], ["rollback"]]` → log `["deployed v2 to green", "switch refused", "smoke passed", "switched to green", "rolled back to blue"]`, live `"blue"`, live_version `"v1"`, idle_version `"v2"`.
""",
    starter='''def blue_green(initial_version: str, ops: List[list]) -> dict:
    pass
''',
    solution='''def blue_green(initial_version, ops):
    version = {"blue": initial_version, "green": None}
    status = {"blue": "verified", "green": "empty"}
    live, idle = "blue", "green"
    can_rollback = False
    log = []
    for op in ops:
        kind = op[0]
        if kind == "deploy":
            version[idle] = op[1]
            status[idle] = "unverified"
            can_rollback = False
            log.append("deployed %s to %s" % (op[1], idle))
        elif kind == "smoke":
            if status[idle] == "empty":
                log.append("nothing to test")
            else:
                status[idle] = "verified" if op[1] else "failed"
                log.append("smoke passed" if op[1] else "smoke failed")
        elif kind == "switch":
            if status[idle] == "verified":
                live, idle = idle, live
                can_rollback = True
                log.append("switched to " + live)
            else:
                log.append("switch refused")
        elif kind == "rollback":
            if can_rollback:
                live, idle = idle, live
                can_rollback = False
                log.append("rolled back to " + live)
            else:
                log.append("rollback refused")
    return {"log": log, "live": live, "live_version": version[live], "idle_version": version[idle]}
''',
    tests=[
        ["v1", [["deploy", "v2"], ["switch"], ["smoke", True], ["switch"], ["rollback"]]],
        ["v1", []],
        ["v1", [["switch"], ["rollback"], ["smoke", True]]],
        ["v1", [["deploy", "v2"], ["smoke", False], ["switch"], ["smoke", True], ["switch"]]],
        ["v1", [["deploy", "v2"], ["smoke", True], ["switch"], ["rollback"], ["rollback"]]],
        ["v1", [["deploy", "v2"], ["smoke", True], ["switch"], ["deploy", "v3"], ["rollback"], ["smoke", True], ["switch"]]],
        ["v1", [["deploy", "v2"], ["smoke", True], ["switch"], ["switch"]]],
        ["v1", [["deploy", "v2"], ["smoke", True], ["switch"], ["rollback"], ["switch"], ["rollback"]]],
        ["v1", [["deploy", "v2"], ["deploy", "v3"], ["smoke", True], ["switch"]]],
        ["v1", [["deploy", "v2"], ["smoke", True], ["deploy", "v3"], ["switch"]]],
        ["v1", [["deploy", "v2"], ["smoke", True], ["switch"], ["deploy", "v3"], ["smoke", True], ["switch"], ["deploy", "v4"], ["smoke", False], ["switch"], ["rollback"]]],
        ["v7", [["deploy", "v8"], ["smoke", True], ["smoke", False], ["switch"], ["smoke", True], ["switch"], ["rollback"], ["smoke", False], ["switch"]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def blue_green(initial_version, ops):
    version = {"blue": initial_version, "green": None}
    live, idle = "blue", "green"
    log = []
    for op in ops:
        if op[0] == "deploy":
            version[idle] = op[1]
            log.append("deployed %s to %s" % (op[1], idle))
        elif op[0] == "smoke":
            log.append("nothing to test" if version[idle] is None else "smoke passed" if op[1] else "smoke failed")
        elif op[0] == "switch":
            if version[idle] is not None:
                live, idle = idle, live
                log.append("switched to " + live)
            else:
                log.append("switch refused")
        else:
            live, idle = idle, live
            log.append("rolled back to " + live)
    return {"log": log, "live": live, "live_version": version[live], "idle_version": version[idle]}
''',
        '''def blue_green(initial_version, ops):
    version = {"blue": initial_version, "green": None}
    status = {"blue": "verified", "green": "empty"}
    live, idle = "blue", "green"
    can_rollback = False
    log = []
    for op in ops:
        kind = op[0]
        if kind == "deploy":
            version[idle] = op[1]
            status[idle] = "unverified"
            log.append("deployed %s to %s" % (op[1], idle))
        elif kind == "smoke":
            if status[idle] == "empty":
                log.append("nothing to test")
            else:
                status[idle] = "verified" if op[1] else "failed"
                log.append("smoke passed" if op[1] else "smoke failed")
        elif kind == "switch":
            if status[idle] == "verified":
                live, idle = idle, live
                can_rollback = True
                log.append("switched to " + live)
            else:
                log.append("switch refused")
        elif kind == "rollback":
            if can_rollback:
                live, idle = idle, live
                log.append("rolled back to " + live)
            else:
                log.append("rollback refused")
    return {"log": log, "live": live, "live_version": version[live], "idle_version": version[idle]}
''',
    ],
    guide=dict(
        prereqs="Blue-green deployment from the lesson *Deployment options and progressive delivery*. A small state machine with dictionaries.",
        intuition="Deployment (putting software on machines) and release (sending users to it) are separate acts. Blue-green makes the release a pointer flip, and the old environment stays warm so that undoing the release is the same flip in reverse.",
        hints=[
            "Track a version and a status per colour, plus which colour is live.",
            "Swapping is `live, idle = idle, live`.",
            "Keep one boolean `can_rollback`: set by a switch, cleared by a rollback and by a deploy.",
        ],
        brute_force="Not a performance problem; a single pass is the only sensible design. The naive version forgets the verification gate and the rollback window.",
        approach="Process operations in order, updating `version`, `status`, `live`, `idle`, `can_rollback` and the log.\n\n**Dry run** on the example: deploy v2 to green (unverified). Switch refused. Smoke passes → verified. Switch → green live, rollback possible. Rollback → blue live again with v1; green keeps v2.",
        complexity="Time O(number of operations); space O(1) beyond the log.",
        pitfalls="Allowing a switch to an unverified or failed environment. Allowing a rollback after a new deploy overwrote the old version. Allowing two rollbacks in a row. A switch right after a switch is legal, because the old live environment is verified.",
        follow_up="A database shared by blue and green must accept both versions at once, which is why schema changes are made in backward-compatible steps (expand, then contract).",
    ),
),
dict(
    id="msvc-feature-toggle",
    title="Feature Toggle Evaluation with Targeting Rules",
    difficulty="Medium",
    pattern="Progressive Delivery",
    entry="is_enabled",
    description=r"""
Decide whether a feature is on for a user.

`toggle` is a dict:

- `"enabled"`: the kill switch. If `False`, the answer is `False` whatever else is set.
- `"rules"`: a list of `{"attr": str, "op": str, "value": ..., "result": bool}` evaluated in order. The **first** rule that matches decides, and its `result` is returned. A rule whose attribute is missing from `user` does not match.
  - `"eq"`: `user[attr] == value`
  - `"neq"`: `user[attr] != value`
  - `"in"`: `user[attr]` is an element of the list `value`
  - `"gte"`: `user[attr] >= value`
  - `"lt"`: `user[attr] < value`
- `"percentage"`: an integer 0–100 used when no rule matches. Compute a bucket from the string `key = toggle["salt"] + ":" + user["id"]` as `sum((i + 1) * ord(ch) for i, ch in enumerate(key)) % 100`. The feature is on if `bucket < percentage`.

`user` is a dict of attributes and always has a string `"id"`.

**Example:** toggle `{"enabled": True, "salt": "new-booking", "percentage": 0, "rules": [{"attr": "clinic", "op": "in", "value": ["north", "east"], "result": True}]}`, user `{"id": "u1", "clinic": "east"}` → `True`
""",
    starter='''def is_enabled(toggle: dict, user: dict) -> bool:
    pass
''',
    solution='''def is_enabled(toggle, user):
    if not toggle["enabled"]:
        return False
    for rule in toggle.get("rules", []):
        attr = rule["attr"]
        if attr not in user:
            continue
        have, want, op = user[attr], rule["value"], rule["op"]
        if op == "eq":
            hit = have == want
        elif op == "neq":
            hit = have != want
        elif op == "in":
            hit = have in want
        elif op == "gte":
            hit = have >= want
        elif op == "lt":
            hit = have < want
        else:
            hit = False
        if hit:
            return rule["result"]
    key = toggle["salt"] + ":" + user["id"]
    bucket = sum((i + 1) * ord(ch) for i, ch in enumerate(key)) % 100
    return bucket < toggle["percentage"]
''',
    tests=[
        [{"enabled": True, "salt": "new-booking", "percentage": 0, "rules": [{"attr": "clinic", "op": "in", "value": ["north", "east"], "result": True}]}, {"id": "u1", "clinic": "east"}],
        [{"enabled": False, "salt": "new-booking", "percentage": 100, "rules": [{"attr": "clinic", "op": "in", "value": ["north", "east"], "result": True}]}, {"id": "u1", "clinic": "east"}],
        [{"enabled": True, "salt": "s", "percentage": 100, "rules": []}, {"id": "anyone"}],
        [{"enabled": True, "salt": "s", "percentage": 0, "rules": []}, {"id": "anyone"}],
        [{"enabled": True, "salt": "s", "percentage": 100, "rules": [{"attr": "role", "op": "eq", "value": "intern", "result": False}]}, {"id": "u2", "role": "intern"}],
        [{"enabled": True, "salt": "s", "percentage": 100, "rules": [{"attr": "role", "op": "eq", "value": "intern", "result": False}]}, {"id": "u2"}],
        [{"enabled": True, "salt": "s", "percentage": 0, "rules": [{"attr": "role", "op": "neq", "value": "vet", "result": False}, {"attr": "years", "op": "gte", "value": 5, "result": True}]}, {"id": "u3", "role": "vet", "years": 5}],
        [{"enabled": True, "salt": "s", "percentage": 0, "rules": [{"attr": "years", "op": "lt", "value": 5, "result": True}, {"attr": "years", "op": "gte", "value": 5, "result": False}]}, {"id": "u3", "years": 4}],
        [{"enabled": True, "salt": "s", "percentage": 0, "rules": [{"attr": "role", "op": "eq", "value": "vet", "result": False}, {"attr": "role", "op": "eq", "value": "vet", "result": True}]}, {"id": "u3", "role": "vet"}],
        [{"enabled": True, "salt": "exp", "percentage": 50, "rules": []}, {"id": "a"}],
        [{"enabled": True, "salt": "exp", "percentage": 50, "rules": []}, {"id": "b"}],
        [{"enabled": True, "salt": "exp", "percentage": 50, "rules": []}, {"id": "user-1042"}],
        [{"enabled": True, "salt": "other", "percentage": 50, "rules": []}, {"id": "user-1042"}],
        [{"enabled": True, "salt": "exp", "percentage": 37, "rules": [{"attr": "beta", "op": "eq", "value": True, "result": True}]}, {"id": "user-77", "beta": False}],
        [{"enabled": True, "salt": "exp", "percentage": 13, "rules": [{"attr": "plan", "op": "zz", "value": 1, "result": True}]}, {"id": "ab", "plan": 1}],
    ],
    examples=2,
    wrong_solutions=[
        '''def is_enabled(toggle, user):
    result = False
    for rule in toggle.get("rules", []):
        attr = rule["attr"]
        if attr not in user:
            continue
        have, want, op = user[attr], rule["value"], rule["op"]
        hit = (op == "eq" and have == want) or (op == "neq" and have != want) or (op == "in" and have in want) or (op == "gte" and have >= want) or (op == "lt" and have < want)
        if hit:
            result = rule["result"]
    if result:
        return toggle["enabled"]
    key = toggle["salt"] + ":" + user["id"]
    return toggle["enabled"] and sum((i + 1) * ord(ch) for i, ch in enumerate(key)) % 100 < toggle["percentage"]
''',
        '''def is_enabled(toggle, user):
    if not toggle["enabled"]:
        return False
    for rule in toggle.get("rules", []):
        have, want, op = user.get(rule["attr"]), rule["value"], rule["op"]
        hit = (op == "eq" and have == want) or (op == "neq" and have != want) or (op == "in" and have in want)
        if op == "gte":
            hit = have is not None and have >= want
        if op == "lt":
            hit = have is not None and have < want
        if hit:
            return rule["result"]
    key = user["id"]
    return sum((i + 1) * ord(ch) for i, ch in enumerate(key)) % 100 < toggle["percentage"]
''',
    ],
    guide=dict(
        prereqs="Feature toggles from the lessons on migration patterns and progressive delivery. Dictionaries; `enumerate`; `ord`.",
        intuition="A toggle is a small decision list: kill switch first, then explicit targeting, then a stable percentage. The percentage must be computed from the user, not drawn at random, so the same person sees the same behaviour on every request.",
        hints=[
            "Return `False` immediately when the kill switch is off.",
            "Loop over the rules; skip a rule if the attribute is not in the user; return the result of the first match.",
            "Build the key from the salt and the user id, and compute the bucket exactly as given.",
        ],
        brute_force="Not a performance problem. The usual wrong shortcut is a random number per request, which makes the feature flicker on and off for the same user.",
        approach="Kill switch → rules in order → bucket.\n\n**Dry run** on the example: enabled. The first rule looks at `clinic`; the user has `east`, which is in the list → the rule matches and returns `True`. The percentage of 0 is never consulted.",
        complexity="Time O(rules + length of the key); space O(1).",
        pitfalls="Letting the last matching rule win. Treating a missing attribute as `None` and matching `neq`. Leaving the salt out of the key, which puts the same users in the early bucket of every experiment. A rule may force the feature *off* (`result: False`).",
        follow_up="Toggles are debt: release toggles should be removed once the feature is fully on. Long-lived toggles (permissions, kill switches) deserve tests for both positions.",
    ),
),
dict(
    id="msvc-jwt-confused-deputy",
    title="Token Scopes Across a Call Chain and the Confused Deputy",
    difficulty="Hard",
    pattern="Security",
    entry="authorise_chain",
    description=r"""
A user's request passes through several services. Each hop either forwards the user's token (so the callee can check it) or relies on the calling service's own identity.

- `token`: `{"sub": user id, "scopes": [str], "aud": [service names], "exp": int}`.
- `now`: the current time (an integer).
- `trust`: a dict from service name to the list of services it accepts calls from when no user token is forwarded.
- `hops`: a list of dicts `{"caller": str, "callee": str, "scope": str, "owner": str, "forward": bool}`. The callee performs an action that needs `scope` on a resource belonging to user `owner`.

**User check** for a hop, in this order; the first failing check gives the reason:

1. `exp > now`, else `"expired"`
2. `callee` is in `aud`, else `"audience"`
3. `scope` is in `scopes`, else `"scope"`
4. `owner == sub` or `"admin"` is in `scopes`, else `"owner"`

Evaluate hops in order:

- If `forward` is true, the callee runs the user check: pass → `"allow"`, fail → `"deny:<reason>"`.
- If `forward` is false, the callee sees only the caller. If the caller is not in `trust[callee]` → `"deny:untrusted"`. Otherwise the action **is performed** without any user check: the result is `"allow"` if the user check would have passed, and `"confused-deputy"` if it would have failed (a trusted service was used to do what the user may not do).
- After any `deny`, the chain stops and every remaining hop is `"skipped"`. A `confused-deputy` hop does not stop the chain.

Return the list of results.

**Example:** token `{"sub": "u1", "scopes": ["records:read"], "aud": ["gateway", "patients"], "exp": 100}`, now `50`, trust `{"patients": ["gateway"]}`, hops `[gateway→patients, scope records:read, owner u2, forward false]` → `["confused-deputy"]` (u1 read u2's record through the gateway).
""",
    starter='''def authorise_chain(token: dict, now: int, trust: Dict[str, List[str]], hops: List[dict]) -> List[str]:
    pass
''',
    solution='''def authorise_chain(token, now, trust, hops):
    def user_check(hop):
        if not token["exp"] > now:
            return "expired"
        if hop["callee"] not in token["aud"]:
            return "audience"
        if hop["scope"] not in token["scopes"]:
            return "scope"
        if hop["owner"] != token["sub"] and "admin" not in token["scopes"]:
            return "owner"
        return None

    out = []
    stopped = False
    for hop in hops:
        if stopped:
            out.append("skipped")
            continue
        reason = user_check(hop)
        if hop["forward"]:
            if reason is None:
                out.append("allow")
            else:
                out.append("deny:" + reason)
                stopped = True
        elif hop["caller"] not in trust.get(hop["callee"], []):
            out.append("deny:untrusted")
            stopped = True
        else:
            out.append("allow" if reason is None else "confused-deputy")
    return out
''',
    tests=[
        [{"sub": "u1", "scopes": ["records:read"], "aud": ["gateway", "patients"], "exp": 100}, 50, {"patients": ["gateway"]},
         [{"caller": "gateway", "callee": "patients", "scope": "records:read", "owner": "u2", "forward": False}]],
        [{"sub": "u1", "scopes": ["records:read"], "aud": ["gateway", "patients"], "exp": 100}, 50, {"patients": ["gateway"]},
         [{"caller": "gateway", "callee": "patients", "scope": "records:read", "owner": "u2", "forward": True}]],
        [{"sub": "u1", "scopes": [], "aud": [], "exp": 100}, 50, {}, []],
        [{"sub": "u1", "scopes": ["records:read"], "aud": ["patients"], "exp": 100}, 100, {},
         [{"caller": "gateway", "callee": "patients", "scope": "records:read", "owner": "u1", "forward": True},
          {"caller": "patients", "callee": "lab", "scope": "lab:read", "owner": "u1", "forward": True}]],
        [{"sub": "u1", "scopes": ["records:read", "lab:read"], "aud": ["patients"], "exp": 100}, 99, {},
         [{"caller": "gateway", "callee": "patients", "scope": "records:read", "owner": "u1", "forward": True},
          {"caller": "patients", "callee": "lab", "scope": "lab:read", "owner": "u1", "forward": True},
          {"caller": "lab", "callee": "billing", "scope": "x", "owner": "u1", "forward": True}]],
        [{"sub": "u1", "scopes": ["records:read"], "aud": ["patients", "lab"], "exp": 100}, 1, {},
         [{"caller": "gateway", "callee": "patients", "scope": "records:read", "owner": "u1", "forward": True},
          {"caller": "patients", "callee": "lab", "scope": "lab:read", "owner": "u1", "forward": True}]],
        [{"sub": "u1", "scopes": ["records:read", "admin"], "aud": ["patients"], "exp": 100}, 1, {},
         [{"caller": "gateway", "callee": "patients", "scope": "records:read", "owner": "u9", "forward": True}]],
        [{"sub": "u1", "scopes": ["records:read"], "aud": ["patients"], "exp": 100}, 1, {"patients": ["reminders"]},
         [{"caller": "gateway", "callee": "patients", "scope": "records:read", "owner": "u1", "forward": False},
          {"caller": "gateway", "callee": "patients", "scope": "records:read", "owner": "u1", "forward": True}]],
        [{"sub": "u1", "scopes": ["records:read"], "aud": ["patients"], "exp": 100}, 1, {"patients": ["gateway"], "billing": ["patients"]},
         [{"caller": "gateway", "callee": "patients", "scope": "records:read", "owner": "u1", "forward": False},
          {"caller": "patients", "callee": "billing", "scope": "invoices:write", "owner": "u1", "forward": False},
          {"caller": "billing", "callee": "patients", "scope": "records:read", "owner": "u1", "forward": True}]],
        [{"sub": "u1", "scopes": ["a"], "aud": ["s"], "exp": 5}, 9, {"s": ["g"]},
         [{"caller": "g", "callee": "s", "scope": "a", "owner": "u1", "forward": False},
          {"caller": "g", "callee": "s", "scope": "a", "owner": "u1", "forward": True},
          {"caller": "g", "callee": "s", "scope": "a", "owner": "u1", "forward": True}]],
        [{"sub": "u1", "scopes": ["a"], "aud": [], "exp": 50}, 9, {"s": ["g"]},
         [{"caller": "g", "callee": "s", "scope": "zzz", "owner": "u2", "forward": True}]],
        [{"sub": "u1", "scopes": ["a"], "aud": ["s"], "exp": 50}, 9, {"s": ["g"]},
         [{"caller": "g", "callee": "s", "scope": "zzz", "owner": "u2", "forward": True}]],
    ],
    examples=2,
    wrong_solutions=[
        '''def authorise_chain(token, now, trust, hops):
    out, stopped = [], False
    for hop in hops:
        if stopped:
            out.append("skipped")
            continue
        if not hop["forward"]:
            if hop["caller"] in trust.get(hop["callee"], []):
                out.append("allow")
            else:
                out.append("deny:untrusted")
                stopped = True
            continue
        reason = None
        if not token["exp"] > now:
            reason = "expired"
        elif hop["callee"] not in token["aud"]:
            reason = "audience"
        elif hop["scope"] not in token["scopes"]:
            reason = "scope"
        elif hop["owner"] != token["sub"] and "admin" not in token["scopes"]:
            reason = "owner"
        if reason:
            out.append("deny:" + reason)
            stopped = True
        else:
            out.append("allow")
    return out
''',
        '''def authorise_chain(token, now, trust, hops):
    def user_check(hop):
        if hop["scope"] not in token["scopes"]:
            return "scope"
        if hop["owner"] != token["sub"]:
            return "owner"
        if token["exp"] < now:
            return "expired"
        if hop["callee"] not in token["aud"]:
            return "audience"
        return None
    out = []
    for hop in hops:
        reason = user_check(hop)
        if hop["forward"]:
            out.append("allow" if reason is None else "deny:" + reason)
        elif hop["caller"] not in trust.get(hop["callee"], []):
            out.append("deny:untrusted")
        else:
            out.append("allow" if reason is None else "confused-deputy")
    return out
''',
    ],
    guide=dict(
        prereqs="JWTs, scopes and the confused deputy problem from the lesson *Trust, encryption and identity*. Ordered checks with early return.",
        intuition="Two questions get mixed up easily: *is this caller a service I trust?* and *is this user allowed to do this?* A confused deputy appears when a service answers only the first question and then acts on the user's behalf anyway.",
        hints=[
            "Write the user check as a function that returns the first failing reason or `None`.",
            "For a non-forwarding hop, test trust first; if trusted, use the user check only to decide between `allow` and `confused-deputy`.",
            "Keep a flag that turns every later hop into `skipped` after a deny.",
        ],
        brute_force="Not a performance problem. The simplest wrong version treats any trusted caller as fully authorised, which is the vulnerability the problem asks you to detect.",
        approach="Loop over hops with a `stopped` flag. Compute `reason = user_check(hop)`. Forwarding: allow or deny. Not forwarding: untrusted → deny; trusted → allow or confused-deputy.\n\n**Dry run** on the example: the hop does not forward. Gateway is trusted by patients. The user check: not expired, patients in the audience, scope present, but owner u2 ≠ sub u1 and no admin scope → `owner`. A trusted hop with a failing user check → `confused-deputy`.",
        complexity="Time O(hops × size of the scope and audience lists); space O(1) beyond the output.",
        pitfalls="Checking in the wrong order changes the reported reason. A token whose `exp` equals `now` is expired. A confused-deputy hop does not stop the chain, because nothing refused it; that is why it is dangerous.",
        follow_up="The fix is to pass the user's identity downstream in a verifiable form and to re-check ownership in the service that owns the data. Token exchange narrows scopes and audience at each hop.",
    ),
),
dict(
    id="msvc-conway-mismatch",
    title="Conway's Law: Team and Architecture Mismatch",
    difficulty="Medium",
    pattern="Organisation",
    entry="conway_report",
    description=r"""
Conway's law says a system's structure mirrors the communication structure of the organisation that builds it. Find the places where the architecture asks teams to coordinate that do not talk to each other.

- `ownership`: a dict from service name to the owning team.
- `calls`: a list of `[caller, callee]` service dependencies. The same pair may appear more than once and counts once.
- `team_links`: a list of `[team_a, team_b]` pairs of teams with a regular communication channel. Links work in both directions.

Classify each distinct dependency:

- If the caller or the callee has no owner, it is **unowned**: do not count it anywhere else.
- If both belong to the same team: **same team**.
- If they belong to different teams: **cross team**. It is additionally a **mismatch** if the two teams have no link.

Return:

```
{"same_team": int, "cross_team": int,
 "mismatches": [[caller, callee], ...]   # sorted
 "unowned": [service names with no owner that appear in calls, sorted, no repeats],
 "busiest_pair": [team_x, team_y] or None}
```

`busiest_pair` is the pair of different teams with the most cross-team dependencies between them (direction ignored), written with the two names sorted; ties go to the alphabetically smallest pair; `None` if there are no cross-team dependencies.

**Example:** `ownership = {"web": "front", "booking": "care", "billing": "money"}`, `calls = [["web", "booking"], ["booking", "billing"]]`, `team_links = [["front", "care"]]` → `{"same_team": 0, "cross_team": 2, "mismatches": [["booking", "billing"]], "unowned": [], "busiest_pair": ["care", "front"]}`
""",
    starter='''def conway_report(ownership: Dict[str, str], calls: List[List[str]], team_links: List[List[str]]) -> dict:
    pass
''',
    solution='''def conway_report(ownership, calls, team_links):
    links = set()
    for a, b in team_links:
        links.add((a, b))
        links.add((b, a))
    same = cross = 0
    mismatches, unowned, pairs = [], set(), {}
    for caller, callee in sorted(set((c[0], c[1]) for c in calls)):
        missing = [s for s in (caller, callee) if s not in ownership]
        if missing:
            unowned.update(missing)
            continue
        ta, tb = ownership[caller], ownership[callee]
        if ta == tb:
            same += 1
            continue
        cross += 1
        key = tuple(sorted((ta, tb)))
        pairs[key] = pairs.get(key, 0) + 1
        if (ta, tb) not in links:
            mismatches.append([caller, callee])
    busiest = None
    if pairs:
        busiest = list(min(pairs, key=lambda k: (-pairs[k], k)))
    return {"same_team": same, "cross_team": cross, "mismatches": mismatches, "unowned": sorted(unowned), "busiest_pair": busiest}
''',
    tests=[
        [{"web": "front", "booking": "care", "billing": "money"}, [["web", "booking"], ["booking", "billing"]], [["front", "care"]]],
        [{"a": "t1", "b": "t1"}, [["a", "b"], ["b", "a"]], []],
        [{}, [], []],
        [{"a": "t1"}, [["a", "ghost"], ["ghost", "a"], ["phantom", "ghost"]], []],
        [{"a": "t1", "b": "t2"}, [["a", "b"], ["a", "b"], ["a", "b"]], [["t2", "t1"]]],
        [{"a": "t1", "b": "t2", "c": "t3"}, [["a", "b"], ["b", "a"], ["a", "c"]], []],
        [{"a": "t1", "b": "t2", "c": "t3", "d": "t3"}, [["a", "c"], ["a", "d"], ["a", "b"], ["b", "a"], ["c", "d"]], [["t1", "t3"]]],
        [{"a": "t1", "b": "t2", "c": "t3"}, [["a", "b"], ["a", "c"]], [["t1", "t2"], ["t1", "t3"]]],
        [{"z": "t9", "y": "t8", "x": "t7"}, [["z", "y"], ["y", "x"], ["x", "z"]], [["t9", "t9"]]],
        [{"a": "t1", "b": "t2"}, [["a", "a"], ["b", "b"]], []],
        [{"s%d" % i: "team%d" % (i // 3) for i in range(30)}, [["s%d" % i, "s%d" % ((i * 7 + 1) % 30)] for i in range(30)], [["team%d" % i, "team%d" % (i + 1)] for i in range(0, 9, 2)]],
    ],
    examples=1,
    wrong_solutions=[
        '''def conway_report(ownership, calls, team_links):
    links = set((a, b) for a, b in team_links)
    same = cross = 0
    mismatches, unowned, pairs = [], set(), {}
    for caller, callee in calls:
        missing = [s for s in (caller, callee) if s not in ownership]
        if missing:
            unowned.update(missing)
            continue
        ta, tb = ownership[caller], ownership[callee]
        if ta == tb:
            same += 1
            continue
        cross += 1
        key = tuple(sorted((ta, tb)))
        pairs[key] = pairs.get(key, 0) + 1
        if (ta, tb) not in links:
            mismatches.append([caller, callee])
    busiest = list(min(pairs, key=lambda k: (-pairs[k], k))) if pairs else None
    return {"same_team": same, "cross_team": cross, "mismatches": sorted(mismatches), "unowned": sorted(unowned), "busiest_pair": busiest}
''',
        '''def conway_report(ownership, calls, team_links):
    links = set()
    for a, b in team_links:
        links.add((a, b)); links.add((b, a))
    same = cross = 0
    mismatches, unowned, pairs = [], set(), {}
    for caller, callee in sorted(set((c[0], c[1]) for c in calls)):
        ta, tb = ownership.get(caller), ownership.get(callee)
        if ta is None:
            unowned.add(caller)
        if tb is None:
            unowned.add(callee)
        if ta == tb:
            same += 1
            continue
        cross += 1
        key = (ta or "", tb or "")
        pairs[key] = pairs.get(key, 0) + 1
        if (ta, tb) not in links:
            mismatches.append([caller, callee])
    busiest = list(max(pairs, key=lambda k: pairs[k])) if pairs else None
    return {"same_team": same, "cross_team": cross, "mismatches": mismatches, "unowned": sorted(unowned), "busiest_pair": busiest}
''',
    ],
    guide=dict(
        prereqs="Conway's law from the lesson *Conway's law and team structure*. Sets of pairs; counting with a dictionary.",
        intuition="Every arrow between services owned by different teams is a standing request for those teams to coordinate. If no channel exists between them, the arrow is a place where work will queue, or where the design will quietly drift.",
        hints=[
            "Remove duplicate dependencies with a set of tuples, and sort them so the output order is fixed.",
            "Store team links in both directions so a lookup does not depend on order.",
            "Count cross-team dependencies per unordered team pair with a sorted tuple as the key.",
        ],
        brute_force="For each dependency, scan the whole list of team links: O(D × L). A set of pairs makes each lookup O(1).",
        approach="Build `links` symmetric. For each distinct dependency: unowned → record names and skip; same team → count; else count as cross, bump the pair counter, and add to mismatches if the teams are not linked. Choose the busiest pair with the key `(-count, pair)`.\n\n**Dry run** on the example: web→booking is front→care, linked: cross, no mismatch. booking→billing is care→money, not linked: cross and mismatch. Pair counts: (care, front) 1, (care, money) 1; the tie goes to (care, front).",
        complexity="Time O(D log D + L); space O(D + L).",
        pitfalls="Counting a repeated dependency several times. Treating team links as one-directional. Counting dependencies with an unowned end as cross-team. Forgetting the tie rule for the busiest pair.",
        follow_up="A long list of mismatches suggests either changing the architecture (merge or move services) or changing the organisation (the inverse Conway manoeuvre).",
    ),
),
dict(
    id="msvc-monorepo-affected",
    title="Monorepo: Which Services Does This Change Affect?",
    difficulty="Medium",
    pattern="Build",
    entry="affected_projects",
    description=r"""
In a monorepo, one repository holds many projects (services and shared libraries). A build system should rebuild only what a change can affect.

- `roots`: a dict from project name to its directory, for example `{"billing": "services/billing", "money": "libs/money"}`. Directories have no leading or trailing slash.
- `deps`: a dict from project name to the list of projects it depends on. Projects missing from `deps` depend on nothing. There are no cycles.
- `changed`: a list of changed file paths.
- `global_paths`: a list of file paths or directories whose change affects **every** project (for example the root build configuration).

Rules:

1. A path is **inside** a directory if it equals the directory or starts with the directory followed by `/`.
2. If any changed path is inside any entry of `global_paths`, every project is affected.
3. Otherwise each changed file belongs to the project with the **longest** root it is inside (projects may be nested). A file inside no root is ignored.
4. A project is affected if it owns a changed file, or depends (directly or indirectly) on an affected project.

Return the sorted list of affected project names.

**Example:** `roots = {"billing": "services/billing", "booking": "services/booking", "money": "libs/money"}`, `deps = {"billing": ["money"], "booking": []}`, `changed = ["libs/money/round.py"]`, `global_paths = ["build.yml"]` → `["billing", "money"]`
""",
    starter='''def affected_projects(roots: Dict[str, str], deps: Dict[str, List[str]], changed: List[str], global_paths: List[str]) -> List[str]:
    pass
''',
    solution='''def affected_projects(roots, deps, changed, global_paths):
    def inside(path, directory):
        return path == directory or path.startswith(directory + "/")

    for path in changed:
        if any(inside(path, g) for g in global_paths):
            return sorted(roots)
    direct = set()
    for path in changed:
        best, owner = -1, None
        for name, root in roots.items():
            if inside(path, root) and len(root) > best:
                best, owner = len(root), name
        if owner is not None:
            direct.add(owner)
    users = {}
    for name, ds in deps.items():
        for d in ds:
            users.setdefault(d, []).append(name)
    affected = set(direct)
    stack = list(direct)
    while stack:
        p = stack.pop()
        for u in users.get(p, []):
            if u not in affected and u in roots:
                affected.add(u)
                stack.append(u)
    return sorted(affected)
''',
    tests=[
        [{"billing": "services/billing", "booking": "services/booking", "money": "libs/money"}, {"billing": ["money"], "booking": []}, ["libs/money/round.py"], ["build.yml"]],
        [{"billing": "services/billing", "booking": "services/booking", "money": "libs/money"}, {"billing": ["money"], "booking": []}, ["build.yml"], ["build.yml"]],
        [{}, {}, ["a.py"], []],
        [{"a": "svc/a"}, {}, [], ["ci"]],
        [{"a": "svc/a", "ab": "svc/ab"}, {}, ["svc/ab/main.py"], []],
        [{"a": "svc/a", "inner": "svc/a/plugins/inner"}, {"a": ["inner"]}, ["svc/a/plugins/inner/x.py"], []],
        [{"a": "svc/a", "inner": "svc/a/plugins/inner"}, {}, ["svc/a/plugins/inner/x.py", "README.md"], []],
        [{"a": "svc/a", "inner": "svc/a/plugins/inner"}, {}, ["svc/a/plugins/x.py"], []],
        [{"web": "apps/web", "api": "apps/api", "auth": "libs/auth", "log": "libs/log"}, {"web": ["api"], "api": ["auth"], "auth": ["log"]}, ["libs/log/fmt.py"], []],
        [{"web": "apps/web", "api": "apps/api", "auth": "libs/auth", "log": "libs/log"}, {"web": ["api"], "api": ["auth"], "auth": ["log"]}, ["apps/api/routes.py", "docs/readme.md"], ["ci"]],
        [{"web": "apps/web", "api": "apps/api"}, {"web": ["api"]}, ["ci/deploy/prod.yml"], ["ci"]],
        [{"web": "apps/web", "api": "apps/api"}, {"web": ["api"]}, ["cinema/readme.md"], ["ci"]],
        [{"p%d" % i: "pkg/p%d" % i for i in range(40)}, {"p%d" % i: ["p%d" % (i - 1)] for i in range(1, 40) if i != 20}, ["pkg/p5/x.py", "pkg/p30/y.py"], []],
    ],
    examples=2,
    wrong_solutions=[
        '''def affected_projects(roots, deps, changed, global_paths):
    for path in changed:
        if any(path.startswith(g) for g in global_paths):
            return sorted(roots)
    direct = set()
    for path in changed:
        for name, root in roots.items():
            if path.startswith(root):
                direct.add(name)
    users = {}
    for name, ds in deps.items():
        for d in ds:
            users.setdefault(d, []).append(name)
    affected, stack = set(direct), list(direct)
    while stack:
        p = stack.pop()
        for u in users.get(p, []):
            if u not in affected:
                affected.add(u)
                stack.append(u)
    return sorted(affected)
''',
        '''def affected_projects(roots, deps, changed, global_paths):
    def inside(path, directory):
        return path == directory or path.startswith(directory + "/")
    for path in changed:
        if any(inside(path, g) for g in global_paths):
            return sorted(roots)
    direct = set()
    for path in changed:
        best, owner = -1, None
        for name, root in roots.items():
            if inside(path, root) and len(root) > best:
                best, owner = len(root), name
        if owner is not None:
            direct.add(owner)
    affected = set(direct)
    for name, ds in deps.items():
        if any(d in direct for d in ds):
            affected.add(name)
    return sorted(affected)
''',
    ],
    guide=dict(
        prereqs="Monorepos and build mapping from the lesson *Monorepo or multirepo*. Reverse dependency graphs; depth-first search.",
        intuition="A change flows *against* the dependency arrows: if billing depends on the money library, a change to money reaches billing. So invert the graph, find the projects that own the changed files, and spread outwards to everyone who uses them.",
        hints=[
            "Write `inside(path, directory)` with the slash-boundary rule and use it for both global paths and roots.",
            "Assign each file to the longest matching root so nested projects work.",
            "Build a map from a project to the projects that depend on it, and traverse from the directly changed set.",
        ],
        brute_force="Repeat until nothing changes: scan all projects and mark any that depends on a marked one. O(P × E) in the worst case, against O(P + E) for a single traversal of the reversed graph.",
        approach="1. Global check. 2. Owners of changed files by longest root. 3. Reverse the dependency map. 4. Depth-first search from the owners.\n\n**Dry run** on the example: no global path changed. `libs/money/round.py` is inside `libs/money` → money. Users of money: billing. Users of billing: none. Result `[billing, money]`.",
        complexity="Time O(C × P + P + E) for C changed files, P projects and E dependency edges; space O(P + E).",
        pitfalls="Plain `startswith` makes `svc/ab` belong to project `svc/a`, and `cinema/` look like `ci`. Stopping after direct dependents misses transitive ones. With nested projects a file in the inner one does not belong to the outer one.",
        follow_up="Tools such as Bazel, Nx and Pants compute this from declared dependencies. The same calculation selects which tests to run and which images to rebuild.",
    ),
),
]
