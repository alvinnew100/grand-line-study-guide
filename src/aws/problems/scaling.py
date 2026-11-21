_STEP_CFG = {
    "high": 70, "low": 30, "breach": 2, "cooldown": 3, "min": 2, "max": 10, "start": 2,
    "steps_out": [[0, 15, 1], [15, None, 3]],
    "steps_in": [[0, 15, -1], [15, None, -2]],
}


def _cfg(**kw):
    c = dict(_STEP_CFG)
    c.update(kw)
    return c


PROBLEMS = [
dict(
    id="aws-health-check-state",
    title="Health-Check State Machine",
    difficulty="Easy",
    pattern="Load Balancing",
    entry="healthStates",
    description=r"""
A load balancer probes each target at a fixed interval. One failed probe does not remove a target and
one good probe does not bring it back: the state flips only after a run of **consecutive** results.

`healthStates(results, healthy_threshold, unhealthy_threshold, initial)`:

- `results`: list of booleans, one per probe (`True` = the probe succeeded).
- The target starts in state `initial` (`"healthy"` or `"unhealthy"`).
- An `unhealthy` target becomes `healthy` when the last `healthy_threshold` probes all succeeded.
- A `healthy` target becomes `unhealthy` when the last `unhealthy_threshold` probes all failed.
- Runs are counted across state changes only in the natural way: a counter of consecutive successes
  and a counter of consecutive failures, each reset to 0 by the opposite result.

Return the list of states after each probe.

**Example:** `results=[True, True, False, False, True]`, thresholds 2 and 2, initial `"unhealthy"`
→ `["unhealthy","healthy","healthy","unhealthy","unhealthy"]`
""",
    starter='''def healthStates(results, healthy_threshold, unhealthy_threshold, initial):
    pass
''',
    solution='''def healthStates(results, healthy_threshold, unhealthy_threshold, initial):
    state, ok, bad, out = initial, 0, 0, []
    for r in results:
        if r:
            ok, bad = ok + 1, 0
            if state == "unhealthy" and ok >= healthy_threshold:
                state = "healthy"
        else:
            bad, ok = bad + 1, 0
            if state == "healthy" and bad >= unhealthy_threshold:
                state = "unhealthy"
        out.append(state)
    return out
''',
    tests=[
        [[True, True, False, False, True], 2, 2, "unhealthy"],
        [[False, True, False, True, False, True], 2, 2, "healthy"],
        [[], 3, 2, "healthy"],
        [[True] * 6, 5, 2, "unhealthy"],
        [[False, False, False], 5, 3, "healthy"],
        [[True, True, True, False, True, True, True, True], 3, 1, "unhealthy"],
        [[False, False, True, False, False, False, True, True], 2, 3, "healthy"],
        [[True], 1, 1, "unhealthy"],
        [[False], 1, 1, "healthy"],
        [[True, False] * 10, 2, 2, "unhealthy"],
        [[False] * 4 + [True] * 9 + [False] * 2 + [True], 10, 2, "healthy"],
        [[i % 7 != 0 for i in range(60)], 3, 1, "unhealthy"],
    ],
    examples=2,
    wrong_solutions=[
        '''def healthStates(results, healthy_threshold, unhealthy_threshold, initial):
    return ["healthy" if r else "unhealthy" for r in results]
''',
        '''def healthStates(results, healthy_threshold, unhealthy_threshold, initial):
    state, ok, bad, out = initial, 0, 0, []
    for r in results:
        if r:
            ok += 1
            if ok >= healthy_threshold:
                state = "healthy"
        else:
            bad += 1
            if bad >= unhealthy_threshold:
                state = "unhealthy"
        out.append(state)
    return out
''',
    ],
    guide=dict(
        prereqs="The load balancing lesson: health checks and thresholds.",
        intuition="Two counters of consecutive results. A success resets the failure counter and the other way round; a threshold reached in the 'wrong' state changes nothing.",
        hints=["Keep `ok` and `bad`; exactly one of them is non-zero after each probe.",
               "Check the threshold only for the transition that makes sense from the current state.",
               "Append the state after processing each probe."],
        brute_force="For each index look back over the last k results with a slice: O(n × k). The counters make it O(n).",
        approach="Dry run thresholds 2/2 from unhealthy with `T T F F T`: T → ok 1 (unhealthy); T → ok 2 → healthy; F → bad 1 (healthy); F → bad 2 → unhealthy; T → ok 1 (unhealthy).",
        complexity="O(n) time, O(1) extra space.",
        pitfalls="Not resetting the opposite counter (flapping results would then accumulate); mapping each probe directly to a state; starting from the wrong initial state.",
    ),
),
dict(
    id="aws-alb-routing",
    title="Load Balancer Routing Algorithms",
    difficulty="Medium",
    pattern="Load Balancing",
    entry="routeRequests",
    description=r"""
Simulate two ways a load balancer can choose a target.

`routeRequests(algorithm, targets, events)` returns the list of target names chosen for the `"req"`
events, in order.

- `targets`: list of `[name, weight]` in registration order (weights are non-negative integers).
- `events`: list of `["req", id]` (a new request arrives) or `["done", id]` (that request finished).

**`"weighted"`** — smooth weighted round robin. Targets with weight 0 receive nothing. Each target has
a `current` value starting at 0. For every request: add each target's weight to its `current`; pick
the target with the largest `current` (ties → earliest registered); subtract the **sum of all
weights** from the picked target's `current`. `"done"` events are ignored. Over any window of
`sum(weights)` requests each target receives exactly its weight, without long bursts.

**`"least_outstanding"`** — send each request to the target with the fewest requests in flight (ties →
earliest registered). Weights are ignored (even 0). A `"done"` event decrements the in-flight count of
the target that received that request; a `"done"` for an unknown or already finished id is ignored.

If there is no eligible target, a request yields the string `"503"`.

**Example:** `"weighted"`, targets `[["blue",3],["green",1]]`, four requests
→ `["blue","blue","green","blue"]`
""",
    starter='''def routeRequests(algorithm, targets, events):
    pass
''',
    solution='''def routeRequests(algorithm, targets, events):
    out = []
    if algorithm == "weighted":
        live = [[n, w] for n, w in targets if w > 0]
        total = sum(w for _, w in live)
        cur = [0] * len(live)
        for kind, _ in events:
            if kind != "req":
                continue
            if not live:
                out.append("503")
                continue
            for i, (_, w) in enumerate(live):
                cur[i] += w
            best = max(range(len(live)), key=lambda i: (cur[i], -i))
            cur[best] -= total
            out.append(live[best][0])
        return out
    inflight = [0] * len(targets)
    owner = {}
    for kind, rid in events:
        if kind == "req":
            if not targets:
                out.append("503")
                continue
            i = min(range(len(targets)), key=lambda j: (inflight[j], j))
            inflight[i] += 1
            owner[rid] = i
            out.append(targets[i][0])
        elif rid in owner:
            inflight[owner.pop(rid)] -= 1
    return out
''',
    tests=[
        ["weighted", [["blue", 3], ["green", 1]], [["req", i] for i in range(4)]],
        ["least_outstanding", [["a", 1], ["b", 1]], [["req", 1], ["req", 2], ["done", 1], ["req", 3], ["req", 4]]],
        ["weighted", [["a", 5], ["b", 1], ["c", 1]], [["req", i] for i in range(14)]],
        ["weighted", [["a", 0], ["b", 2]], [["req", 1], ["req", 2], ["done", 1], ["req", 3]]],
        ["weighted", [["a", 0]], [["req", 1]]],
        ["weighted", [], [["req", 1], ["req", 2]]],
        ["least_outstanding", [], [["req", 1]]],
        ["least_outstanding", [["a", 0], ["b", 9]], [["req", 1], ["req", 2], ["req", 3]]],
        ["least_outstanding", [["a", 1], ["b", 1], ["c", 1]],
         [["req", 1], ["req", 2], ["req", 3], ["done", 2], ["done", 2], ["done", 99], ["req", 4], ["done", 3], ["done", 1], ["req", 5], ["req", 6], ["req", 7]]],
        ["weighted", [["a", 1], ["b", 1], ["c", 1]], [["req", i] for i in range(7)]],
        ["weighted", [["a", 2], ["b", 3], ["c", 0], ["d", 2]], [["req", i] for i in range(21)]],
        ["least_outstanding", [["slow", 1], ["fast", 1]],
         [["req", 1], ["req", 2], ["done", 2], ["req", 3], ["done", 3], ["req", 4], ["done", 4], ["req", 5], ["req", 6]]],
        ["weighted", [["a", 90], ["b", 10]], [["req", i] for i in range(30)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def routeRequests(algorithm, targets, events):
    out = []
    if algorithm == "weighted":
        seq = [n for n, w in targets for _ in range(w)]
        k = 0
        for kind, _ in events:
            if kind == "req":
                out.append(seq[k % len(seq)] if seq else "503")
                k += 1
        return out
    inflight = [0] * len(targets)
    owner = {}
    for kind, rid in events:
        if kind == "req":
            if not targets:
                out.append("503"); continue
            i = min(range(len(targets)), key=lambda j: (inflight[j], j))
            inflight[i] += 1; owner[rid] = i; out.append(targets[i][0])
        elif rid in owner:
            inflight[owner.pop(rid)] -= 1
    return out
''',
        '''def routeRequests(algorithm, targets, events):
    out = []
    if algorithm == "weighted":
        live = [[n, w] for n, w in targets if w > 0]
        total = sum(w for _, w in live)
        cur = [0] * len(live)
        for kind, _ in events:
            if kind != "req":
                continue
            if not live:
                out.append("503"); continue
            for i, (_, w) in enumerate(live):
                cur[i] += w
            best = max(range(len(live)), key=lambda i: (cur[i], -i))
            cur[best] -= total
            out.append(live[best][0])
        return out
    k = 0
    for kind, rid in events:
        if kind == "req":
            out.append(targets[k % len(targets)][0] if targets else "503")
            k += 1
    return out
''',
    ],
    guide=dict(
        prereqs="The load balancing lesson: routing algorithms and weighted target groups.",
        intuition="Weighted: every target earns credit equal to its weight on each request, and the winner pays back the total — so heavy targets win more often but never many times in a row. Least outstanding: a counter per target, incremented on assignment and decremented on completion.",
        hints=["Filter out weight-0 targets for the weighted algorithm before anything else.",
               "For ties use the key `(current, -index)` with `max`, or `(inflight, index)` with `min`.",
               "Remember which target owns each request id so that `done` can find it; delete the entry so a duplicate `done` does nothing."],
        brute_force="Expanding weights into a repeated list (`a,a,a,b`) and cycling gives the right proportions but in bursts, which is not the specified order.",
        approach="Dry run weighted blue 3, green 1 (total 4): request 1 → current (3,1) → blue → (-1,1). Request 2 → (2,2) → tie → blue (earlier) → (-2,2). Request 3 → (1,3) → green → (1,-1). Request 4 → (4,0) → blue → (0,0). Output blue, blue, green, blue.",
        complexity="O(E × T) for E events and T targets; O(T + in-flight requests) space.",
        pitfalls="Bursty expansion instead of smooth round robin; decrementing twice for a duplicate `done`; applying weights to least-outstanding; crashing on an empty target list.",
    ),
),
dict(
    id="aws-asg-target-tracking",
    title="Target-Tracking Scaling Simulation",
    difficulty="Medium",
    pattern="Auto Scaling",
    entry="targetTracking",
    description=r"""
A **target-tracking** policy keeps a metric near a target value by resizing the group, like a
thermostat. Simulate a simplified version minute by minute.

`targetTracking(loads, target, min_size, max_size, start, cooldown)`:

- `loads[t]`: total CPU demand during minute `t`, in "percent-instances" (150 means one and a half
  fully busy instances). With `capacity` instances the average utilisation is `loads[t] / capacity` %.
- `target`: the desired average utilisation in percent (integer ≥ 1).
- The capacity during minute 0 is `start`.
- At the end of each minute compute `desired = ceil(loads[t] / target)`, clamped to
  `[min_size, max_size]`.
  - If `desired > capacity`: **scale out immediately** — the capacity for minute `t + 1` is `desired`.
  - If `desired < capacity`: **scale in** to `desired` only if at least `cooldown` minutes have passed
    since the last capacity change of either kind (a change decided at the end of minute `c` allows a
    scale-in at the end of minute `t` when `t - c >= cooldown`). Before any change has happened,
    scale-in is allowed. Otherwise keep the capacity.
- Return the list of capacities in effect during each minute (same length as `loads`).

**Example:** `loads=[100, 300, 300, 50, 50, 50]`, target 50, min 1, max 10, start 2, cooldown 2
→ `[2, 2, 6, 6, 1, 1]`
""",
    starter='''def targetTracking(loads, target, min_size, max_size, start, cooldown):
    pass
''',
    solution='''def targetTracking(loads, target, min_size, max_size, start, cooldown):
    cap, last_change, out = start, None, []
    for t, load in enumerate(loads):
        out.append(cap)
        desired = -(-load // target)
        desired = max(min_size, min(max_size, desired))
        if desired > cap:
            cap, last_change = desired, t
        elif desired < cap and (last_change is None or t - last_change >= cooldown):
            cap, last_change = desired, t
    return out
''',
    tests=[
        [[100, 300, 300, 50, 50, 50], 50, 1, 10, 2, 2],
        [[100, 100, 100], 50, 1, 10, 2, 5],
        [[], 50, 1, 10, 2, 5],
        [[1000, 1000, 1000], 50, 1, 4, 1, 0],
        [[0, 0, 0, 0], 60, 2, 8, 6, 0],
        [[0, 0, 0, 0], 60, 2, 8, 6, 3],
        [[120, 480, 100, 100, 100, 100, 100], 60, 1, 20, 2, 3],
        [[300, 10, 300, 10, 300, 10], 50, 1, 10, 1, 4],
        [[301, 299, 300], 100, 1, 10, 1, 0],
        [[50] * 3 + [500] * 3 + [50] * 6, 50, 1, 6, 1, 5],
        [[100, 200, 300, 400, 300, 200, 100, 0, 0, 0], 40, 2, 9, 2, 2],
        [[(i * 37) % 400 for i in range(80)], 55, 1, 6, 3, 4],
    ],
    examples=2,
    wrong_solutions=[
        '''def targetTracking(loads, target, min_size, max_size, start, cooldown):
    cap, out = start, []
    for load in loads:
        out.append(cap)
        cap = max(min_size, min(max_size, -(-load // target)))
    return out
''',
        '''def targetTracking(loads, target, min_size, max_size, start, cooldown):
    cap, last_change, out = start, None, []
    for t, load in enumerate(loads):
        desired = max(min_size, min(max_size, load // target))
        if desired > cap:
            cap, last_change = desired, t
        elif desired < cap and (last_change is None or t - last_change >= cooldown):
            cap, last_change = desired, t
        out.append(cap)
    return out
''',
    ],
    guide=dict(
        prereqs="The auto scaling lesson: target tracking, cooldowns, why scale-in is conservative.",
        intuition="The right number of instances is 'total work divided by how much work each should carry'. Growing is urgent and unconditional; shrinking waits for a quiet period so that the group does not oscillate.",
        hints=["Record the capacity for the minute **before** deciding the change for the next minute.",
               "Ceiling division with integers: `-(-load // target)`.",
               "Keep `last_change` (minute index) and update it on scale-out as well as scale-in."],
        brute_force="Simulation is inherently linear; there is no slower sensible alternative.",
        approach="Dry run of the example (target 50, cooldown 2, start 2). Minute 0: capacity 2, load 100 → desired 2, no change. Minute 1: capacity 2, load 300 → desired 6 > 2 → scale out, last change = 1. Minute 2: capacity 6, desired 6. Minute 3: capacity 6, load 50 → desired 1 < 6 and 3 − 1 = 2 ≥ cooldown → scale in, last change = 3. Minutes 4 and 5 run with capacity 1. Output `[2, 2, 6, 6, 1, 1]`. With cooldown 3 the scale-in would wait until the end of minute 4.",
        complexity="O(n) time, O(1) extra space.",
        pitfalls="Floor instead of ceiling division; applying the cooldown to scale-out; appending the capacity after the decision (off by one minute); forgetting to clamp.",
    ),
),
dict(
    id="aws-asg-step-scaling",
    title="Step Scaling with Cooldown",
    difficulty="Hard",
    pattern="Auto Scaling",
    entry="stepScaling",
    description=r"""
A **step scaling** policy reacts to an alarm with an adjustment that depends on how far the metric is
past the threshold. Simulate it.

`stepScaling(metrics, cfg)` — `metrics[t]` is the metric value (integer) observed during minute `t`;
`cfg` is a dict:

- `start`, `min`, `max`: initial capacity and bounds.
- `high`, `low`: alarm thresholds. `breach`: number of consecutive minutes required.
- `steps_out`: list of `[lower, upper, adjustment]` with `upper = null` for "no upper bound".
  `steps_in`: the same shape with negative adjustments.
- `cooldown`: minutes.

Rules, applied at the end of every minute `t` (the capacity used during minute 0 is `start`):

1. The **scale-out alarm** is in ALARM when `metrics[t] >= high` for the last `breach` consecutive
   minutes including `t`. The **scale-in alarm** is in ALARM when `metrics[t] <= low` for the last
   `breach` consecutive minutes including `t`. (`high > low`, so they are never both in ALARM.)
2. If an alarm is in ALARM and the policy is **not cooling down**, take one action:
   - scale-out: `d = metrics[t] - high`; scale-in: `d = low - metrics[t]`;
   - find the step with `lower <= d < upper` and add its adjustment to the capacity (if no step
     contains `d`, do nothing and do not start a cooldown);
   - clamp the capacity to `[min, max]`.
   An action taken at the end of minute `t` starts a cooldown: no further action can be taken at the
   end of minutes `t+1 … t+cooldown-1`; the next possible action is at the end of minute
   `t + cooldown`. An action counts (and starts the cooldown) even if clamping left the capacity
   unchanged.
3. While the alarm stays in ALARM after the cooldown, the policy acts again.

Return the capacity in effect during each minute.

**Example:** `metrics=[50, 80, 80, 80, 80, 80]`, `high=70, low=30, breach=2, cooldown=3, start=2,
min=2, max=10`, `steps_out=[[0,15,1],[15,null,3]]` → alarm at t=2 (d=10 → +1), cooldown blocks t=3
and t=4, acts again at t=5 → `[2, 2, 2, 3, 3, 3]`
""",
    starter='''def stepScaling(metrics, cfg):
    pass
''',
    solution='''def stepScaling(metrics, cfg):
    cap, out = cfg["start"], []
    hi_run = lo_run = 0
    next_ok = 0
    for t, m in enumerate(metrics):
        out.append(cap)
        hi_run = hi_run + 1 if m >= cfg["high"] else 0
        lo_run = lo_run + 1 if m <= cfg["low"] else 0
        if t < next_ok:
            continue
        if hi_run >= cfg["breach"]:
            d, steps = m - cfg["high"], cfg["steps_out"]
        elif lo_run >= cfg["breach"]:
            d, steps = cfg["low"] - m, cfg["steps_in"]
        else:
            continue
        for lower, upper, adj in steps:
            if d >= lower and (upper is None or d < upper):
                cap = max(cfg["min"], min(cfg["max"], cap + adj))
                next_ok = t + cfg["cooldown"]
                break
    return out
''',
    tests=[
        [[50, 80, 80, 80, 80, 80], _STEP_CFG],
        [[50, 90, 90, 90, 90, 90, 90], _STEP_CFG],
        [[], _STEP_CFG],
        [[50, 50, 50, 50], _STEP_CFG],
        [[80, 50, 80, 50, 80, 50, 80], _STEP_CFG],
        [[20, 20, 20, 20, 20, 20, 20, 20], _cfg(start=8)],
        [[10, 10, 10, 10, 10, 10, 10, 10], _cfg(start=8)],
        [[95] * 12, _cfg(cooldown=1, breach=1)],
        [[95] * 12, _cfg(cooldown=0, breach=3)],
        [[75, 75, 99, 99, 99, 20, 20, 20, 20, 20, 20, 20], _cfg(cooldown=2)],
        [[70, 70, 30, 30, 70, 70, 30, 30], _cfg(start=5, cooldown=0)],
        [[80, 80, 80, 80, 80, 80], _cfg(steps_out=[[5, 8, 1], [20, None, 4]])],
        [[90, 90, 90, 90, 90, 90], _cfg(steps_out=[[5, 8, 1], [20, None, 4]], cooldown=2)],
        [[20, 20, 20, 20, 20, 80, 80, 80, 80], _cfg(start=2, cooldown=4)],
        [[80, 80, 20, 20, 20, 20, 20, 20], _STEP_CFG],
        [[(i * 53) % 100 for i in range(120)], _cfg(breach=1, cooldown=2, start=5)],
    ],
    examples=2,
    wrong_solutions=[
        '''def stepScaling(metrics, cfg):
    cap, out = cfg["start"], []
    hi = lo = 0
    for t, m in enumerate(metrics):
        out.append(cap)
        hi = hi + 1 if m >= cfg["high"] else 0
        lo = lo + 1 if m <= cfg["low"] else 0
        if hi >= cfg["breach"]:
            d, steps = m - cfg["high"], cfg["steps_out"]
        elif lo >= cfg["breach"]:
            d, steps = cfg["low"] - m, cfg["steps_in"]
        else:
            continue
        for lower, upper, adj in steps:
            if d >= lower and (upper is None or d < upper):
                cap = max(cfg["min"], min(cfg["max"], cap + adj))
                break
    return out
''',
        '''def stepScaling(metrics, cfg):
    cap, out = cfg["start"], []
    hi = lo = 0
    next_ok = 0
    for t, m in enumerate(metrics):
        out.append(cap)
        if t < next_ok:
            continue
        hi = hi + 1 if m >= cfg["high"] else 0
        lo = lo + 1 if m <= cfg["low"] else 0
        if hi >= cfg["breach"]:
            d, steps = m - cfg["high"], cfg["steps_out"]
        elif lo >= cfg["breach"]:
            d, steps = cfg["low"] - m, cfg["steps_in"]
        else:
            continue
        for lower, upper, adj in steps:
            if d >= lower and (upper is None or d < upper):
                cap = max(cfg["min"], min(cfg["max"], cap + adj))
                next_ok = t + cfg["cooldown"]
                break
    return out
''',
        '''def stepScaling(metrics, cfg):
    cap, out = cfg["start"], []
    hi = lo = 0
    next_ok = 0
    for t, m in enumerate(metrics):
        out.append(cap)
        hi = hi + 1 if m >= cfg["high"] else 0
        lo = lo + 1 if m <= cfg["low"] else 0
        if t < next_ok:
            continue
        if hi >= cfg["breach"]:
            d, steps = m - cfg["high"], cfg["steps_out"]
        elif lo >= cfg["breach"]:
            d, steps = cfg["low"] - m, cfg["steps_in"]
        else:
            continue
        next_ok = t + cfg["cooldown"]
        for lower, upper, adj in steps:
            if d >= lower and (upper is None or d <= upper):
                cap = max(cfg["min"], min(cfg["max"], cap + adj))
                break
    return out
''',
    ],
    guide=dict(
        prereqs="The auto scaling lesson (step policies, alarms, cooldown) and the CloudWatch alarm problem.",
        intuition="Three small state machines run side by side: a run counter for each alarm, and a `next_ok` minute for the cooldown. The alarm counters keep counting during the cooldown — only the action is suppressed.",
        hints=["Append the capacity at the top of the loop, decide at the bottom.",
               "Update both run counters on every minute, **before** checking the cooldown.",
               "Set `next_ok = t + cooldown` only when a step actually matched."],
        brute_force="Recomputing 'the last `breach` minutes all breach' with a slice each minute is O(n × breach); counters make it O(n).",
        approach="Dry run of the second test: metrics `50, 90×6`, breach 2, cooldown 3. t=1 run 1. t=2 run 2 → ALARM, d = 20 → step `[15, ∞)` → +3 → capacity 5, next_ok = 5. t=3, t=4 blocked. t=5: still in alarm → +3 → 8. Output `[2, 2, 2, 5, 5, 5, 8]`.",
        complexity="O(n × S) time for S steps, O(1) extra space.",
        pitfalls="Freezing the alarm counters during cooldown; treating `upper` as inclusive; starting a cooldown when no step matched; forgetting to clamp; letting cooldown 0 block the same minute.",
    ),
),
dict(
    id="aws-cloudwatch-alarm",
    title="CloudWatch Alarm State Evaluation",
    difficulty="Medium",
    pattern="Monitoring",
    entry="alarmStates",
    description=r"""
A CloudWatch alarm watches one metric. It is configured with a threshold, a comparison, an evaluation
window of **N** datapoints and a number **M** ("M out of N datapoints must breach"). Datapoints can be
missing, and the alarm has a setting for how to treat them.

`alarmStates(datapoints, threshold, comparison, n, m, missing)`:

- `datapoints`: list of numbers or `null` (missing), one per period.
- `comparison`: one of `">"`, `">="`, `"<"`, `"<="` — a datapoint **breaches** when
  `value <comparison> threshold` is true.
- For every index `i`, produce the alarm state after period `i`:
  - if `i < n - 1` (the window is not full yet) → `"INSUFFICIENT_DATA"`;
  - otherwise look at the window `datapoints[i-n+1 .. i]` and apply the `missing` treatment:
    - `"breaching"`: a missing datapoint counts as breaching;
    - `"notBreaching"`: a missing datapoint counts as not breaching;
    - `"missing"`: if **every** datapoint in the window is missing → `"INSUFFICIENT_DATA"`;
      otherwise missing datapoints count as not breaching;
    - `"ignore"`: if every datapoint in the window is missing, the state **stays what it was** after
      the previous period (`"INSUFFICIENT_DATA"` if there is none); otherwise missing datapoints
      count as not breaching;
  - then the state is `"ALARM"` if at least `m` datapoints breach, else `"OK"`.

Return the list of states.

**Example:** `datapoints=[50, 85, 90, 40]`, threshold 80, `">"`, n=2, m=2, `"missing"`
→ `["INSUFFICIENT_DATA", "OK", "ALARM", "OK"]`
""",
    starter='''def alarmStates(datapoints, threshold, comparison, n, m, missing):
    pass
''',
    solution='''def alarmStates(datapoints, threshold, comparison, n, m, missing):
    def breach(v):
        if comparison == ">":
            return v > threshold
        if comparison == ">=":
            return v >= threshold
        if comparison == "<":
            return v < threshold
        return v <= threshold
    out = []
    for i in range(len(datapoints)):
        if i < n - 1:
            out.append("INSUFFICIENT_DATA")
            continue
        window = datapoints[i - n + 1:i + 1]
        present = [v for v in window if v is not None]
        if not present and missing == "missing":
            out.append("INSUFFICIENT_DATA")
            continue
        if not present and missing == "ignore":
            out.append(out[-1] if out else "INSUFFICIENT_DATA")
            continue
        count = sum(1 for v in present if breach(v))
        if missing == "breaching":
            count += len(window) - len(present)
        out.append("ALARM" if count >= m else "OK")
    return out
''',
    tests=[
        [[50, 85, 90, 40], 80, ">", 2, 2, "missing"],
        [[90, None, 90, None, None, 90], 80, ">", 3, 2, "notBreaching"],
        [[90, None, 90, None, None, 90], 80, ">", 3, 2, "breaching"],
        [[], 80, ">", 1, 1, "missing"],
        [[80, 81, 79], 80, ">=", 1, 1, "missing"],
        [[80, 81, 79], 80, ">", 1, 1, "missing"],
        [[5, 3, 2, 1, 9], 3, "<", 3, 2, "missing"],
        [[5, 3, 2, 1, 9], 3, "<=", 3, 2, "missing"],
        [[90, 90, None, None, None, 10], 80, ">", 2, 1, "missing"],
        [[90, 90, None, None, None, 10], 80, ">", 2, 1, "ignore"],
        [[None, None, 95, None, None], 80, ">", 2, 1, "ignore"],
        [[None, None, None], 80, ">", 1, 1, "breaching"],
        [[None, None, None], 80, ">", 1, 1, "notBreaching"],
        [[10, 95, 10, 95, 10, 95, 95, 95], 80, ">", 5, 3, "missing"],
        [[(i * 17) % 100 if i % 6 else None for i in range(90)], 60, ">=", 4, 2, "ignore"],
    ],
    examples=2,
    wrong_solutions=[
        '''def alarmStates(datapoints, threshold, comparison, n, m, missing):
    ops = {">": lambda v: v > threshold, ">=": lambda v: v >= threshold, "<": lambda v: v < threshold, "<=": lambda v: v <= threshold}
    out = []
    for i in range(len(datapoints)):
        if i < n - 1:
            out.append("INSUFFICIENT_DATA"); continue
        window = datapoints[i - n + 1:i + 1]
        count = sum(1 for v in window if v is not None and ops[comparison](v))
        out.append("ALARM" if count >= m else "OK")
    return out
''',
        '''def alarmStates(datapoints, threshold, comparison, n, m, missing):
    ops = {">": lambda v: v > threshold, ">=": lambda v: v >= threshold, "<": lambda v: v < threshold, "<=": lambda v: v <= threshold}
    out = []
    for i in range(len(datapoints)):
        if i < n - 1:
            out.append("INSUFFICIENT_DATA"); continue
        window = datapoints[i - n + 1:i + 1]
        present = [v for v in window if v is not None]
        if not present and missing in ("missing", "ignore"):
            out.append("INSUFFICIENT_DATA"); continue
        count = sum(1 for v in present if ops[comparison](v))
        if missing == "breaching":
            count += len(window) - len(present)
        out.append("ALARM" if count == len(window) else "OK")
    return out
''',
    ],
    guide=dict(
        prereqs="The CloudWatch lesson: periods, evaluation periods, datapoints to alarm, missing-data treatment.",
        intuition="A sliding window of size N. Count breaches in it; what a hole in the data counts as depends on one setting. Two settings have a special case when the whole window is empty.",
        hints=["Slice the window `datapoints[i-n+1 : i+1]` and split it into present and missing values.",
               "Handle the 'all missing' cases for `missing` and `ignore` first, then fall through to the common M-of-N count.",
               "For `ignore`, the previous state is simply the last element already appended to the output."],
        brute_force="Re-slicing the window for each index is O(n × N); a running count would be O(n), but N is tiny in practice and the simple version is clearer.",
        approach="Dry run `[90, 90, None, None, None, 10]`, threshold 80, `>`, N=2, M=1, treatment `ignore`: i=0 → INSUFFICIENT; i=1 window (90, 90) → ALARM; i=2 window (90, None) → one breach → ALARM; i=3 window (None, None) → keep ALARM; i=4 → keep ALARM; i=5 window (None, 10) → 0 breaches → OK. With treatment `missing`, i=3 and i=4 become INSUFFICIENT_DATA instead.",
        complexity="O(len × N) time, O(N) extra space.",
        pitfalls="Requiring all N datapoints to breach instead of M; treating missing data as breaching by default; forgetting the comparison operator variants; reading `out[-1]` when the output is still empty.",
    ),
),
]
