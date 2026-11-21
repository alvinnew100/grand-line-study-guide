PROBLEMS = [
dict(
    id="msvc-timeout-budget",
    title="Timeout Budget Propagation",
    difficulty="Easy",
    pattern="Stability Patterns",
    entry="propagate_budget",
    description=r"""
A request enters the system with a total time budget of `total_ms` milliseconds and travels down a chain of services. Each service passes the **remaining** budget to the next one, so nobody keeps working for a caller that has already given up.

`hops` is a list of `[service, network_ms, work_ms]`: the time to reach the service over the network, and the time the service spends on its own work before calling the next hop.

Start with `remaining = total_ms` and process hops in order:

1. Subtract `network_ms`. If `remaining <= 0`, the deadline passed in transit: stop with outcome `"deadline exceeded before <service>"`. The service is not listed.
2. Record `[service, remaining]` (the budget the service sees on arrival).
3. Subtract `work_ms`. If `remaining < 0`, stop with outcome `"deadline exceeded in <service>"`.

If every hop finishes, the outcome is `"ok"`.

Return `{"budgets": [[service, budget_on_arrival], ...], "outcome": str, "slack": int}` where `slack` is the remaining budget when the outcome is `"ok"` and `0` otherwise.

**Example:** `total_ms = 1000`, hops `[["gateway", 10, 40], ["booking", 20, 300], ["billing", 30, 500]]` → budgets `[["gateway", 990], ["booking", 930], ["billing", 600]]`, outcome `"ok"`, slack `100`.
""",
    starter='''def propagate_budget(total_ms: int, hops: List[list]) -> dict:
    pass
''',
    solution='''def propagate_budget(total_ms, hops):
    remaining = total_ms
    budgets = []
    for service, network_ms, work_ms in hops:
        remaining -= network_ms
        if remaining <= 0:
            return {"budgets": budgets, "outcome": "deadline exceeded before " + service, "slack": 0}
        budgets.append([service, remaining])
        remaining -= work_ms
        if remaining < 0:
            return {"budgets": budgets, "outcome": "deadline exceeded in " + service, "slack": 0}
    return {"budgets": budgets, "outcome": "ok", "slack": remaining}
''',
    tests=[
        [1000, [["gateway", 10, 40], ["booking", 20, 300], ["billing", 30, 500]]],
        [100, [["gateway", 10, 40], ["booking", 20, 300]]],
        [500, []],
        [50, [["a", 50, 0]]],
        [50, [["a", 10, 40]]],
        [50, [["a", 10, 41]]],
        [0, [["a", 0, 0]]],
        [300, [["a", 100, 100], ["b", 100, 0]]],
        [301, [["a", 100, 100], ["b", 100, 1]]],
        [301, [["a", 100, 100], ["b", 100, 2], ["c", 1, 1]]],
        [10 ** 6, [["s%d" % i, 3, 7] for i in range(200)]],
        [1999, [["s%d" % i, 3, 7] for i in range(200)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def propagate_budget(total_ms, hops):
    remaining = total_ms
    budgets = []
    for service, network_ms, work_ms in hops:
        remaining -= network_ms
        if remaining < 0:
            return {"budgets": budgets, "outcome": "deadline exceeded before " + service, "slack": 0}
        budgets.append([service, remaining])
        remaining -= work_ms
        if remaining <= 0:
            return {"budgets": budgets, "outcome": "deadline exceeded in " + service, "slack": 0}
    return {"budgets": budgets, "outcome": "ok", "slack": remaining}
''',
        '''def propagate_budget(total_ms, hops):
    budgets = []
    for service, network_ms, work_ms in hops:
        if network_ms + work_ms > total_ms:
            return {"budgets": budgets, "outcome": "deadline exceeded in " + service, "slack": 0}
        budgets.append([service, total_ms - network_ms])
    return {"budgets": budgets, "outcome": "ok", "slack": total_ms}
''',
    ],
    guide=dict(
        prereqs="Timeouts from the lesson *Stability patterns*. A running total in a loop.",
        intuition="A deadline is a budget that only shrinks. Each hop spends some of it on the wire and some on work, and hands the rest down. Giving every hop the full original timeout is how a slow chain ends up working long after the user left.",
        hints=[
            "Keep one variable `remaining` and subtract from it; never restart from `total_ms`.",
            "Check after the network subtraction with `<= 0`, and after the work subtraction with `< 0`.",
            "Record the budget between those two checks.",
        ],
        brute_force="Recompute the sum of all earlier costs for every hop: O(n²). The running total gives O(n).",
        approach="Loop: subtract network; fail `before` on `<= 0`; record; subtract work; fail `in` on `< 0`. After the loop return ok with the slack.\n\n**Dry run** on the example: 1000 − 10 = 990 (gateway) − 40 = 950; − 20 = 930 (booking) − 300 = 630; − 30 = 600 (billing) − 500 = 100. Outcome ok, slack 100.",
        complexity="Time O(n); space O(n) for the list of budgets.",
        pitfalls="The two comparisons are different on purpose: arriving with exactly 0 ms left is too late, finishing with exactly 0 ms left is in time. A failed run has slack 0, not a negative number.",
        follow_up="Real systems carry the deadline in a request header (gRPC does this for you). Each service should also cancel its own downstream calls when the deadline passes.",
    ),
),
dict(
    id="msvc-retry-backoff",
    title="Retry Schedule with Exponential Backoff and Jitter",
    difficulty="Easy",
    pattern="Stability Patterns",
    entry="retry_schedule",
    description=r"""
Compute what a retrying client does.

- The client makes at most `max_attempts` attempts (at least 1). Attempt 1 happens immediately.
- `outcomes[i]` is `True` if attempt `i + 1` succeeds. Attempts beyond the end of the list fail.
- After a **failed** attempt number `n` (1-based), if `n < max_attempts`, the client waits before the next attempt. The upper bound of the wait is `min(cap_ms, base_ms * factor ** (n - 1))`. With **full jitter** the real wait is `int(jitter[n - 1] * bound)` where `jitter` holds numbers between 0 and 1 (in a real client they are random; here they are given). If `jitter` is too short, use `1.0`.
- The client stops at the first success, or when attempts run out.

Return `{"attempts": int, "delays": [int, ...], "succeeded": bool, "total_wait_ms": int}`.

**Example:** `base_ms = 100`, `factor = 2`, `cap_ms = 1000`, `max_attempts = 4`, `jitter = [0.5, 1.0, 0.25]`, `outcomes = [False, False, True]` → `{"attempts": 3, "delays": [50, 200], "succeeded": True, "total_wait_ms": 250}`
""",
    starter='''def retry_schedule(base_ms: int, factor: int, cap_ms: int, max_attempts: int, jitter: List[float], outcomes: List[bool]) -> dict:
    pass
''',
    solution='''def retry_schedule(base_ms, factor, cap_ms, max_attempts, jitter, outcomes):
    delays = []
    attempts = 0
    succeeded = False
    for n in range(1, max_attempts + 1):
        attempts = n
        if n - 1 < len(outcomes) and outcomes[n - 1]:
            succeeded = True
            break
        if n < max_attempts:
            bound = min(cap_ms, base_ms * factor ** (n - 1))
            j = jitter[n - 1] if n - 1 < len(jitter) else 1.0
            delays.append(int(j * bound))
    return {"attempts": attempts, "delays": delays, "succeeded": succeeded, "total_wait_ms": sum(delays)}
''',
    tests=[
        [100, 2, 1000, 4, [0.5, 1.0, 0.25], [False, False, True]],
        [100, 2, 1000, 3, [1.0, 1.0, 1.0], [False, False, False]],
        [100, 2, 1000, 1, [], [False]],
        [100, 2, 1000, 5, [], [True]],
        [100, 2, 1000, 5, [], []],
        [100, 2, 300, 6, [1.0] * 6, []],
        [100, 3, 10 ** 9, 5, [0.0, 0.5, 0.999, 1.0], [False, False, False, False, True]],
        [250, 1, 1000, 4, [0.3, 0.3, 0.3], []],
        [7, 2, 1000, 4, [0.5, 0.5, 0.5], []],
        [100, 2, 1000, 3, [0.5], [False, False, True, True]],
        [100, 2, 1000, 2, [0.5, 0.5], [False, True]],
        [1, 2, 10 ** 6, 25, [0.75] * 30, []],
    ],
    examples=2,
    wrong_solutions=[
        '''def retry_schedule(base_ms, factor, cap_ms, max_attempts, jitter, outcomes):
    delays = []
    attempts = 0
    succeeded = False
    for n in range(1, max_attempts + 1):
        attempts = n
        if n - 1 < len(outcomes) and outcomes[n - 1]:
            succeeded = True
            break
        bound = min(cap_ms, base_ms * factor ** (n - 1))
        j = jitter[n - 1] if n - 1 < len(jitter) else 1.0
        delays.append(int(j * bound))
    return {"attempts": attempts, "delays": delays, "succeeded": succeeded, "total_wait_ms": sum(delays)}
''',
        '''def retry_schedule(base_ms, factor, cap_ms, max_attempts, jitter, outcomes):
    delays = []
    attempts = 0
    succeeded = False
    for n in range(1, max_attempts + 1):
        attempts = n
        if n - 1 < len(outcomes) and outcomes[n - 1]:
            succeeded = True
            break
        if n < max_attempts:
            bound = base_ms * factor ** n
            j = jitter[n - 1] if n - 1 < len(jitter) else 1.0
            delays.append(int(j * bound))
    return {"attempts": attempts, "delays": delays, "succeeded": succeeded, "total_wait_ms": sum(delays)}
''',
    ],
    guide=dict(
        prereqs="Retries from the lesson *Stability patterns*. Exponents; `int()` truncation.",
        intuition="Each failure doubles (or multiplies) the patience of the client, up to a ceiling. Jitter then picks a point somewhere below that ceiling so that a thousand clients that failed together do not all come back at the same instant.",
        hints=[
            "Loop over attempt numbers from 1 to `max_attempts`.",
            "Check success first. Only a failed attempt that is not the last one produces a wait.",
            "The exponent for the wait after attempt n is `n - 1`, so the first wait is bounded by `base_ms`.",
        ],
        brute_force="Not applicable: the direct simulation is linear and there is nothing slower that is natural.",
        approach="For each attempt: success → stop. Otherwise, if another attempt is allowed, compute `bound = min(cap, base × factor^(n−1))`, multiply by the jitter value, truncate, record.\n\n**Dry run** on the example: attempt 1 fails → bound 100, jitter 0.5 → 50. Attempt 2 fails → bound 200, jitter 1.0 → 200. Attempt 3 succeeds. Delays [50, 200], total 250.",
        complexity="Time O(max_attempts); space O(max_attempts).",
        pitfalls="Waiting after the final attempt. Using exponent n instead of n − 1. Applying the cap after the jitter instead of before. Indexing past the end of `jitter` or `outcomes`.",
        follow_up="Retries multiply load: three layers that each retry three times can turn one request into 27. Give retries a budget and retry at one layer only.",
    ),
),
dict(
    id="msvc-circuit-breaker",
    title="Circuit Breaker State Machine",
    difficulty="Medium",
    pattern="Stability Patterns",
    kind="class",
    entry="CircuitBreaker",
    description=r"""
Implement a circuit breaker with explicit timestamps (integers that never decrease).

`CircuitBreaker(failure_threshold, reset_timeout, success_threshold)` starts **closed**.

- `state(ts)` → `"closed"`, `"open"` or `"half_open"`. If the breaker is open and `ts - opened_at >= reset_timeout`, it becomes half-open first.
- `allow(ts)` → whether a call may be made now.
  - closed: `True`.
  - open (after applying the time rule above): `False`.
  - half-open: only one trial call may be in flight. If none is, mark one as in flight and return `True`; otherwise `False`.
- `record(success, ts)` → `None`. Reports the result of a call that was allowed.
  - closed: a success sets the consecutive-failure count to 0; a failure adds 1, and when the count reaches `failure_threshold` the breaker opens with `opened_at = ts`.
  - half-open: the trial is no longer in flight. A failure reopens the breaker with `opened_at = ts`. A success adds 1 to a success count; when it reaches `success_threshold` the breaker closes and all counts reset.
  - open: ignored.

Entering half-open resets the success count and clears the in-flight flag. `record` applies the time rule first, like the other methods.

**Example:** `CircuitBreaker(2, 10, 1)`: `record(False,0)`, `record(False,1)` → open. `allow(5)` → `False`. `allow(11)` → `True` (trial). `allow(11)` → `False`. `record(True,12)` → closed. `state(12)` → `"closed"`.
""",
    starter='''class CircuitBreaker:
    def __init__(self, failure_threshold: int, reset_timeout: int, success_threshold: int):
        pass

    def state(self, ts: int) -> str:
        pass

    def allow(self, ts: int) -> bool:
        pass

    def record(self, success: bool, ts: int) -> None:
        pass
''',
    solution='''class CircuitBreaker:
    def __init__(self, failure_threshold, reset_timeout, success_threshold):
        self.ft, self.rt, self.st = failure_threshold, reset_timeout, success_threshold
        self.s = "closed"
        self.failures = 0
        self.successes = 0
        self.opened_at = 0
        self.trial = False

    def _tick(self, ts):
        if self.s == "open" and ts - self.opened_at >= self.rt:
            self.s = "half_open"
            self.successes = 0
            self.trial = False

    def state(self, ts):
        self._tick(ts)
        return self.s

    def allow(self, ts):
        self._tick(ts)
        if self.s == "closed":
            return True
        if self.s == "open":
            return False
        if self.trial:
            return False
        self.trial = True
        return True

    def record(self, success, ts):
        self._tick(ts)
        if self.s == "closed":
            if success:
                self.failures = 0
            else:
                self.failures += 1
                if self.failures >= self.ft:
                    self.s, self.opened_at = "open", ts
        elif self.s == "half_open":
            self.trial = False
            if success:
                self.successes += 1
                if self.successes >= self.st:
                    self.s, self.failures, self.successes = "closed", 0, 0
            else:
                self.s, self.opened_at = "open", ts
''',
    tests=[
        [["CircuitBreaker", "record", "record", "allow", "allow", "allow", "record", "state"],
         [[2, 10, 1], [False, 0], [False, 1], [5], [11], [11], [True, 12], [12]]],
        [["CircuitBreaker", "state", "allow", "record", "state"], [[1, 5, 1], [0], [0], [True, 0], [0]]],
        [["CircuitBreaker", "record", "record", "record", "state", "record", "state"],
         [[3, 10, 1], [False, 0], [False, 1], [True, 2], [2], [False, 3], [3]]],
        [["CircuitBreaker", "record", "state", "state", "state"], [[1, 10, 1], [False, 0], [9], [10], [10]]],
        [["CircuitBreaker", "record", "allow", "record", "state", "allow", "allow"],
         [[1, 10, 1], [False, 0], [10], [False, 12], [12], [21], [22]]],
        [["CircuitBreaker", "record", "allow", "record", "state", "allow", "record", "state", "allow"],
         [[1, 10, 2], [False, 0], [10], [True, 11], [11], [11], [True, 12], [12], [12]]],
        [["CircuitBreaker", "record", "record", "state", "record", "state"],
         [[1, 10, 1], [False, 0], [True, 1], [1], [False, 2], [12]]],
        [["CircuitBreaker", "record", "allow", "allow", "record", "allow", "record", "record", "state"],
         [[1, 5, 2], [False, 0], [5], [5], [True, 6], [6], [False, 7], [True, 8], [8]]],
        [["CircuitBreaker", "record", "record", "record", "record", "state", "allow"],
         [[2, 10, 1], [False, 0], [True, 1], [False, 2], [False, 3], [3], [12]]],
        [["CircuitBreaker", "record", "allow", "record", "record", "record", "state", "allow"],
         [[1, 10, 1], [False, 0], [10], [True, 10], [False, 11], [False, 30], [30], [41]]],
        [["CircuitBreaker", "record", "state", "allow", "record", "state", "state"],
         [[1, 10, 3], [False, 0], [100], [100], [False, 100], [109], [110]]],
    ],
    examples=1,
    wrong_solutions=[
        '''class CircuitBreaker:
    def __init__(self, failure_threshold, reset_timeout, success_threshold):
        self.ft, self.rt, self.st = failure_threshold, reset_timeout, success_threshold
        self.s, self.failures, self.successes, self.opened_at = "closed", 0, 0, 0
    def _tick(self, ts):
        if self.s == "open" and ts - self.opened_at >= self.rt:
            self.s, self.successes = "half_open", 0
    def state(self, ts):
        self._tick(ts)
        return self.s
    def allow(self, ts):
        self._tick(ts)
        return self.s != "open"
    def record(self, success, ts):
        self._tick(ts)
        if self.s == "closed":
            if success:
                self.failures = 0
            else:
                self.failures += 1
                if self.failures >= self.ft:
                    self.s, self.opened_at = "open", ts
        elif self.s == "half_open":
            if success:
                self.successes += 1
                if self.successes >= self.st:
                    self.s, self.failures, self.successes = "closed", 0, 0
            else:
                self.s, self.opened_at = "open", ts
''',
        '''class CircuitBreaker:
    def __init__(self, failure_threshold, reset_timeout, success_threshold):
        self.ft, self.rt, self.st = failure_threshold, reset_timeout, success_threshold
        self.s, self.failures, self.successes, self.opened_at, self.trial = "closed", 0, 0, 0, False
    def _tick(self, ts):
        if self.s == "open" and ts - self.opened_at >= self.rt:
            self.s, self.successes, self.trial = "half_open", 0, False
    def state(self, ts):
        self._tick(ts)
        return self.s
    def allow(self, ts):
        self._tick(ts)
        if self.s == "closed":
            return True
        if self.s == "open" or self.trial:
            return False
        self.trial = True
        return True
    def record(self, success, ts):
        self._tick(ts)
        if self.s == "closed":
            if not success:
                self.failures += 1
                if self.failures >= self.ft:
                    self.s, self.opened_at = "open", ts
        elif self.s == "half_open":
            self.trial = False
            if success:
                self.s, self.failures, self.successes = "closed", 0, 0
            else:
                self.s, self.opened_at = "open", ts
''',
    ],
    guide=dict(
        prereqs="Circuit breakers from the lesson *Stability patterns*. A class with a few fields; state machines.",
        intuition="The breaker is a three-position switch. Closed counts consecutive failures. Open refuses everything until a timer runs out. Half-open lets one probe through to learn whether it is safe to close again.",
        hints=[
            "Write a private method that applies the open → half-open time rule, and call it at the top of every public method.",
            "In the closed state a success must reset the failure count, so only *consecutive* failures trip the breaker.",
            "In half-open track two things: whether a trial is in flight, and how many trials have succeeded.",
        ],
        brute_force="A version without the half-open state closes fully as soon as the timer expires. It is simpler, and it sends the whole traffic at a service that may still be down. The probe exists to avoid that.",
        approach="Fields: state, failures, successes, opened_at, trial. `_tick` moves open to half-open when due. `allow` answers by state. `record` updates counts and transitions.\n\n**Dry run** of the example (2, 10, 1): two failures at 0 and 1 open the breaker at 1. `allow(5)`: 5 − 1 < 10, open → False. `allow(11)`: 11 − 1 ≥ 10 → half-open, trial granted → True. Second `allow(11)` → False. `record(True, 12)`: one success meets the threshold → closed.",
        complexity="O(1) time and space per call.",
        pitfalls="Counting total failures instead of consecutive ones. Allowing unlimited calls in half-open. Forgetting to restart the timer when a trial fails. Not resetting the failure count on closing.",
        follow_up="Production breakers usually trip on an error *rate* over a sliding window, and expose their state as a metric so that people can see them open.",
    ),
),
dict(
    id="msvc-bulkhead",
    title="Bulkhead Concurrency Limiter",
    difficulty="Medium",
    pattern="Stability Patterns",
    entry="bulkhead",
    description=r"""
A bulkhead gives each downstream dependency its own small pool of concurrent calls, so one slow dependency cannot use up every worker.

- `limits`: a dict from pool name to `[max_running, max_queued]`.
- `events`: a list of `["start", pool, request_id]` or `["end", pool, request_id]`, in time order. Request ids are unique within a pool.

Handle each event and collect one result string per event:

**start**
- if the pool has fewer than `max_running` running requests → the request runs: `"run"`
- else if fewer than `max_queued` requests wait → it joins the back of the queue: `"queued"`
- else → `"rejected"`
- an unknown pool → `"rejected"`

**end**
- if the request is running: it finishes. If the queue is not empty, the request at the front starts running and the result is `"promoted:<that id>"`; otherwise the result is `"done"`.
- if the request is waiting in the queue: it is removed (the caller gave up): `"cancelled"`
- otherwise (unknown, rejected or already ended): `"noop"`

Return the list of results.

**Example:** `limits = {"billing": [1, 1]}`, events `start r1`, `start r2`, `start r3`, `end r1`, `end r2` (all on `billing`) → `["run", "queued", "rejected", "promoted:r2", "done"]`
""",
    starter='''def bulkhead(limits: Dict[str, List[int]], events: List[List[str]]) -> List[str]:
    pass
''',
    solution='''def bulkhead(limits, events):
    running = {p: set() for p in limits}
    queue = {p: [] for p in limits}
    out = []
    for kind, pool, rid in events:
        if pool not in limits:
            out.append("rejected" if kind == "start" else "noop")
            continue
        max_running, max_queued = limits[pool]
        if kind == "start":
            if len(running[pool]) < max_running:
                running[pool].add(rid)
                out.append("run")
            elif len(queue[pool]) < max_queued:
                queue[pool].append(rid)
                out.append("queued")
            else:
                out.append("rejected")
        else:
            if rid in running[pool]:
                running[pool].remove(rid)
                if queue[pool]:
                    nxt = queue[pool].pop(0)
                    running[pool].add(nxt)
                    out.append("promoted:" + nxt)
                else:
                    out.append("done")
            elif rid in queue[pool]:
                queue[pool].remove(rid)
                out.append("cancelled")
            else:
                out.append("noop")
    return out
''',
    tests=[
        [{"billing": [1, 1]}, [["start", "billing", "r1"], ["start", "billing", "r2"], ["start", "billing", "r3"], ["end", "billing", "r1"], ["end", "billing", "r2"]]],
        [{"a": [2, 0]}, [["start", "a", "1"], ["start", "a", "2"], ["start", "a", "3"], ["end", "a", "3"], ["end", "a", "1"], ["start", "a", "4"]]],
        [{}, []],
        [{}, [["start", "x", "1"], ["end", "x", "1"]]],
        [{"a": [1, 2]}, [["start", "a", "1"], ["start", "a", "2"], ["start", "a", "3"], ["end", "a", "2"], ["end", "a", "1"], ["end", "a", "3"], ["end", "a", "3"]]],
        [{"a": [1, 1], "b": [1, 1]}, [["start", "a", "1"], ["start", "a", "2"], ["start", "b", "1"], ["start", "a", "3"], ["start", "b", "2"], ["end", "b", "1"], ["end", "a", "1"]]],
        [{"a": [0, 2]}, [["start", "a", "1"], ["start", "a", "2"], ["start", "a", "3"], ["end", "a", "1"], ["start", "a", "4"]]],
        [{"a": [1, 3]}, [["start", "a", "1"], ["start", "a", "2"], ["start", "a", "3"], ["start", "a", "4"], ["end", "a", "1"], ["end", "a", "2"], ["end", "a", "3"], ["end", "a", "4"], ["end", "a", "4"]]],
        [{"a": [2, 2]}, [["end", "a", "ghost"], ["start", "a", "1"], ["end", "a", "1"], ["end", "a", "1"]]],
        [{"a": [3, 1]}, [["start", "a", "%d" % i] for i in range(6)] + [["end", "a", "%d" % i] for i in (1, 4, 0, 3, 5, 2)]],
        [{"slow": [2, 2], "fast": [5, 0]}, [["start", "slow", "s%d" % i] for i in range(6)] + [["start", "fast", "f%d" % i] for i in range(6)] + [["end", "slow", "s0"], ["end", "fast", "f5"], ["end", "fast", "f0"]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def bulkhead(limits, events):
    running, queue, out = {}, {}, []
    for kind, pool, rid in events:
        if pool not in limits:
            out.append("rejected" if kind == "start" else "noop")
            continue
        r, q = running.setdefault(pool, set()), queue.setdefault(pool, [])
        if kind == "start":
            if len(r) < limits[pool][0]:
                r.add(rid); out.append("run")
            elif len(q) < limits[pool][1]:
                q.append(rid); out.append("queued")
            else:
                out.append("rejected")
        else:
            if rid in r:
                r.remove(rid)
                if q:
                    nxt = q.pop()
                    r.add(nxt); out.append("promoted:" + nxt)
                else:
                    out.append("done")
            elif rid in q:
                q.remove(rid); out.append("cancelled")
            else:
                out.append("noop")
    return out
''',
        '''def bulkhead(limits, events):
    running, queue, out = set(), [], []
    total_run = sum(v[0] for v in limits.values())
    total_q = sum(v[1] for v in limits.values())
    for kind, pool, rid in events:
        key = (pool, rid)
        if pool not in limits:
            out.append("rejected" if kind == "start" else "noop")
        elif kind == "start":
            if len(running) < total_run:
                running.add(key); out.append("run")
            elif len(queue) < total_q:
                queue.append(key); out.append("queued")
            else:
                out.append("rejected")
        elif key in running:
            running.remove(key)
            if queue:
                nxt = queue.pop(0)
                running.add(nxt); out.append("promoted:" + nxt[1])
            else:
                out.append("done")
        elif key in queue:
            queue.remove(key); out.append("cancelled")
        else:
            out.append("noop")
    return out
''',
    ],
    guide=dict(
        prereqs="Bulkheads from the lesson *Stability patterns*. Sets and lists used as a queue.",
        intuition="Each pool is a small waiting room with a fixed number of desks and a fixed number of chairs. When both are full, new arrivals are turned away at once. Turning away quickly is the point: it keeps the trouble inside one pool.",
        hints=[
            "Keep, per pool, a set of running ids and a list of waiting ids.",
            "On `start`, try the running set, then the queue, then reject.",
            "On `end`, a running request frees a desk and the front of the queue takes it.",
        ],
        brute_force="One shared pool for all dependencies needs less code and is exactly the design that lets a slow billing service starve calls to every other service. The second wrong solution in the tests is that design.",
        approach="Dictionaries `running` and `queue` keyed by pool. Process events in order with the rules above.\n\n**Dry run** on the example with limits [1, 1]: r1 runs. r2 queues. r3 finds both full → rejected. End r1 → r2 promoted. End r2 → queue empty → done.",
        complexity="Time O(events × queue length) because of list removal; O(events) with a deque plus a set of cancelled ids. Space O(running + queued).",
        pitfalls="Promoting the newest waiter instead of the oldest. Sharing counts between pools. Treating the end of a rejected request as a real end.",
        follow_up="Thread-pool bulkheads and semaphore bulkheads behave the same from the outside. Combine a bulkhead with a timeout so that a queued request does not wait forever.",
    ),
),
dict(
    id="msvc-tenant-rate-limiter",
    title="Per-tenant Rate Limiter with a Global Cap",
    difficulty="Medium",
    pattern="Stability Patterns",
    kind="class",
    entry="TenantLimiter",
    description=r"""
Implement a sliding-window rate limiter for a shared service used by several tenants (customers). Timestamps are integers that never decrease.

`TenantLimiter(window, default_limit, global_limit)`

- A request at time `ts` looks at the accepted requests with timestamps in the range `(ts - window, ts]`.
- `allow(tenant, ts)` → `True` if the tenant has fewer than its limit of accepted requests in that range **and** all tenants together have fewer than `global_limit`. An accepted request is recorded for both counts. A refused request is not recorded.
- `set_limit(tenant, limit)` → `None`. Overrides the limit for one tenant from now on.
- `usage(tenant, ts)` → the number of accepted requests of that tenant in the range.

**Example:** `TenantLimiter(10, 2, 3)`: `allow("a",0)` → True, `allow("a",1)` → True, `allow("a",2)` → False (tenant limit), `allow("b",3)` → True, `allow("c",4)` → False (global cap of 3), `allow("c",10)` → True (the request at 0 has left the window).
""",
    starter='''class TenantLimiter:
    def __init__(self, window: int, default_limit: int, global_limit: int):
        pass

    def allow(self, tenant: str, ts: int) -> bool:
        pass

    def set_limit(self, tenant: str, limit: int) -> None:
        pass

    def usage(self, tenant: str, ts: int) -> int:
        pass
''',
    solution='''import collections


class TenantLimiter:
    def __init__(self, window, default_limit, global_limit):
        self.window, self.default, self.global_limit = window, default_limit, global_limit
        self.limits = {}
        self.logs = {}
        self.all = collections.deque()

    def _trim(self, dq, ts):
        while dq and dq[0] <= ts - self.window:
            dq.popleft()

    def allow(self, tenant, ts):
        log = self.logs.setdefault(tenant, collections.deque())
        self._trim(log, ts)
        self._trim(self.all, ts)
        if len(log) >= self.limits.get(tenant, self.default) or len(self.all) >= self.global_limit:
            return False
        log.append(ts)
        self.all.append(ts)
        return True

    def set_limit(self, tenant, limit):
        self.limits[tenant] = limit

    def usage(self, tenant, ts):
        log = self.logs.get(tenant)
        if not log:
            return 0
        self._trim(log, ts)
        return len(log)
''',
    tests=[
        [["TenantLimiter", "allow", "allow", "allow", "allow", "allow", "allow"],
         [[10, 2, 3], ["a", 0], ["a", 1], ["a", 2], ["b", 3], ["c", 4], ["c", 10]]],
        [["TenantLimiter", "usage", "allow", "usage", "usage", "usage"], [[5, 1, 9], ["a", 0], ["a", 0], ["a", 0], ["a", 4], ["a", 5]]],
        [["TenantLimiter", "allow", "allow", "set_limit", "allow", "allow", "allow"],
         [[10, 1, 99], ["a", 0], ["a", 1], ["a", 3], ["a", 2], ["a", 3], ["a", 4]]],
        [["TenantLimiter", "set_limit", "allow", "allow"], [[10, 5, 5], ["a", 0], ["a", 0], ["b", 0]]],
        [["TenantLimiter", "allow", "allow", "allow", "allow", "usage", "usage"],
         [[3, 2, 2], ["a", 0], ["b", 0], ["c", 1], ["c", 3], ["c", 3], ["a", 3]]],
        [["TenantLimiter", "allow", "allow", "allow", "allow", "allow", "allow"],
         [[1, 1, 5], ["a", 0], ["a", 0], ["a", 1], ["a", 1], ["a", 2], ["b", 2]]],
        [["TenantLimiter", "allow", "allow", "allow", "allow", "allow", "usage", "allow"],
         [[10, 3, 4], ["a", 0], ["a", 0], ["a", 0], ["a", 0], ["a", 5], ["a", 9], ["a", 10]]],
        [["TenantLimiter", "allow", "allow", "set_limit", "allow", "usage"],
         [[10, 3, 9], ["a", 0], ["a", 1], ["a", 1], ["a", 2], ["a", 2]]],
        [["TenantLimiter", "allow", "allow", "allow", "allow", "allow", "allow", "allow"],
         [[4, 2, 3], ["a", 0], ["b", 1], ["a", 2], ["b", 3], ["b", 4], ["b", 5], ["a", 5]]],
        [["TenantLimiter"] + ["allow"] * 30 + ["usage", "usage"],
         [[7, 3, 5]] + [["t%d" % (i % 4), i] for i in range(30)] + [["t0", 30], ["t1", 30]]],
        [["TenantLimiter", "allow", "allow", "allow"], [[10, 0, 5], ["a", 0], ["a", 50], ["b", 50]]],
    ],
    examples=1,
    wrong_solutions=[
        '''class TenantLimiter:
    def __init__(self, window, default_limit, global_limit):
        self.window, self.default, self.global_limit = window, default_limit, global_limit
        self.limits, self.logs = {}, {}
    def _count(self, tenant, ts):
        return sum(1 for t in self.logs.get(tenant, []) if ts - self.window < t <= ts)
    def allow(self, tenant, ts):
        if self._count(tenant, ts) >= self.limits.get(tenant, self.default):
            return False
        self.logs.setdefault(tenant, []).append(ts)
        return True
    def set_limit(self, tenant, limit):
        self.limits[tenant] = limit
    def usage(self, tenant, ts):
        return self._count(tenant, ts)
''',
        '''class TenantLimiter:
    def __init__(self, window, default_limit, global_limit):
        self.window, self.default, self.global_limit = window, default_limit, global_limit
        self.limits, self.logs = {}, {}
    def _count(self, tenant, ts):
        return sum(1 for t in self.logs.get(tenant, []) if ts - self.window <= t <= ts)
    def allow(self, tenant, ts):
        total = sum(self._count(t, ts) for t in self.logs)
        if self._count(tenant, ts) >= self.limits.get(tenant, self.default) or total >= self.global_limit:
            return False
        self.logs.setdefault(tenant, []).append(ts)
        return True
    def set_limit(self, tenant, limit):
        self.limits[tenant] = limit
    def usage(self, tenant, ts):
        return self._count(tenant, ts)
''',
    ],
    guide=dict(
        prereqs="Rate limiting (see the System Design track) and shared services from the organisation lessons. `collections.deque`.",
        intuition="A sliding-window log keeps the timestamps of accepted requests and forgets the ones that have slid out of the window. Two logs are consulted: the tenant's own, and one for everybody, so one tenant cannot exhaust a shared service.",
        hints=[
            "Keep a deque of accepted timestamps per tenant, and one more for all tenants.",
            "Before counting, pop from the left while the oldest timestamp is `<= ts - window`.",
            "Record the request only when both checks pass.",
        ],
        brute_force="Store every accepted timestamp forever and count the ones in range on each call: O(n) per call and unbounded memory. Trimming from the left keeps each timestamp's total cost constant.",
        approach="`allow`: trim both deques, compare lengths with the tenant limit and the global limit, append to both on success. `usage`: trim and return the length.\n\n**Dry run** of the example (window 10, tenant 2, global 3): a@0 ok, a@1 ok, a@2 refused (a has 2). b@3 ok (global now 3). c@4 refused (global 3). c@10: the range is (0, 10], so the request at 0 is gone; global is 2 → accepted.",
        complexity="Amortised O(1) per call; space O(accepted requests inside one window).",
        pitfalls="The window is open on the left: a request exactly `window` old no longer counts. Do not record refused requests. A limit of 0 refuses everything for that tenant. A changed limit applies to later calls only.",
        follow_up="See the rate limiter lessons of the System Design track for token buckets and for the distributed version with a shared store.",
    ),
),
dict(
    id="msvc-cascading-failure",
    title="Cascading Failure on a Dependency Graph",
    difficulty="Hard",
    pattern="Resilience",
    entry="cascade",
    description=r"""
Work out how one hung service affects everything that depends on it.

- `work`: a dict from service name to the milliseconds of its own work per request.
- `calls`: a dict from service name to a list of `[dependency, timeout_ms, critical]`. The service calls its dependencies one after another, in list order. The graph has no cycles. A service missing from `calls` calls nobody.
- `down`: a list of services that hang: they never answer.

For each service compute a **status** and a **response time**.

A call from S to dependency D with timeout T:

- if D is down, the call fails after `T` ms;
- otherwise, if D's response time is greater than `T`, the call fails after `T` ms;
- otherwise the call takes D's response time, and it fails if D's status is `"failed"`, else it succeeds.

For a service that is not down:

- response time = own work + the time of each of its calls;
- status `"failed"` if any call marked critical failed; otherwise `"degraded"` if any call failed; otherwise `"ok"`.

A down service has status `"failed"` and response time `-1`.

Return a dict from every service in `work` to `[status, response_time]`.

**Example:** `work = {"web": 10, "booking": 20, "billing": 30}`, `calls = {"web": [["booking", 500, True]], "booking": [["billing", 200, True]]}`, `down = ["billing"]` → `{"billing": ["failed", -1], "booking": ["failed", 220], "web": ["failed", 230]}`
""",
    starter='''def cascade(work: Dict[str, int], calls: Dict[str, List[list]], down: List[str]) -> Dict[str, list]:
    pass
''',
    solution='''def cascade(work, calls, down):
    import sys
    sys.setrecursionlimit(10000)
    dead = set(down)
    memo = {}

    def solve(s):
        if s in memo:
            return memo[s]
        if s in dead:
            memo[s] = ["failed", -1]
            return memo[s]
        total = work[s]
        critical_failed = any_failed = False
        for dep, timeout, critical in calls.get(s, []):
            status, t = solve(dep)
            if dep in dead or t > timeout:
                total += timeout
                failed = True
            else:
                total += t
                failed = status == "failed"
            if failed:
                any_failed = True
                if critical:
                    critical_failed = True
        memo[s] = ["failed" if critical_failed else "degraded" if any_failed else "ok", total]
        return memo[s]

    return {s: solve(s) for s in work}
''',
    tests=[
        [{"web": 10, "booking": 20, "billing": 30}, {"web": [["booking", 500, True]], "booking": [["billing", 200, True]]}, ["billing"]],
        [{"web": 10, "booking": 20, "billing": 30}, {"web": [["booking", 500, True]], "booking": [["billing", 200, True]]}, []],
        [{}, {}, []],
        [{"a": 5}, {}, ["a"]],
        [{"web": 10, "booking": 20, "reminders": 30}, {"web": [["booking", 500, True], ["reminders", 100, False]]}, ["reminders"]],
        [{"web": 10, "slow": 300}, {"web": [["slow", 100, True]]}, []],
        [{"web": 10, "slow": 300}, {"web": [["slow", 300, True]]}, []],
        [{"web": 10, "mid": 10, "leaf": 10}, {"web": [["mid", 15, True]], "mid": [["leaf", 1000, True]]}, ["leaf"]],
        [{"web": 10, "mid": 10, "leaf": 10}, {"web": [["mid", 5000, False]], "mid": [["leaf", 1000, True]]}, ["leaf"]],
        [{"web": 1, "a": 1, "b": 1, "shared": 1}, {"web": [["a", 50, True], ["b", 50, False]], "a": [["shared", 20, False]], "b": [["shared", 20, True]]}, ["shared"]],
        [{"web": 1, "a": 1, "b": 1}, {"web": [["a", 50, False], ["b", 50, False], ["a", 50, False]]}, ["a"]],
        [{"s%d" % i: 1 for i in range(60)}, {"s%d" % i: [["s%d" % (i + 1), 1000, i % 2 == 0]] for i in range(59)}, ["s59"]],
        [{"top": 5, "l": 5, "r": 5, "base": 5}, {"top": [["l", 100, True], ["r", 100, True]], "l": [["base", 100, True]], "r": [["base", 100, True]]}, []],
    ],
    examples=2,
    wrong_solutions=[
        '''def cascade(work, calls, down):
    dead = set(down)
    memo = {}
    def solve(s):
        if s in memo:
            return memo[s]
        if s in dead:
            memo[s] = ["failed", -1]
            return memo[s]
        total = work[s]
        failed = False
        for dep, timeout, critical in calls.get(s, []):
            status, t = solve(dep)
            if dep in dead:
                total += timeout
                failed = True
            else:
                total += t
                if status == "failed":
                    failed = True
        memo[s] = ["failed" if failed else "ok", total]
        return memo[s]
    return {s: solve(s) for s in work}
''',
        '''def cascade(work, calls, down):
    dead = set(down)
    memo = {}
    def solve(s):
        if s in memo:
            return memo[s]
        if s in dead:
            memo[s] = ["failed", -1]
            return memo[s]
        total = work[s]
        crit = anyf = False
        for dep, timeout, critical in calls.get(s, []):
            status, t = solve(dep)
            if t > timeout or t == -1:
                total += timeout
                failed = True
            else:
                total += t
                failed = False
            if failed:
                anyf = True
                crit = crit or critical
        memo[s] = ["failed" if crit else "degraded" if anyf else "ok", total]
        return memo[s]
    return {s: solve(s) for s in work}
''',
    ],
    guide=dict(
        prereqs="Cascading failure, timeouts and degraded functionality from the resiliency lessons. Recursion with memoisation on a directed acyclic graph.",
        intuition="A hung dependency does two kinds of damage. It makes its callers fail, and it makes them slow, because each caller waits for its whole timeout. That slowness can in turn exceed the timeout of the caller's caller. Timeouts and the critical flag decide how far the damage travels.",
        hints=[
            "Solve a service only after its dependencies: a recursive function with a memo dictionary does this for you.",
            "A call costs `timeout` when it times out and the dependency's response time otherwise.",
            "Track two flags per service: did any call fail, and did a critical call fail.",
        ],
        brute_force="Recompute each dependency from scratch every time it is called. On a graph with shared dependencies (a diamond) the work grows exponentially with depth. The memo makes each service cost one visit.",
        approach="`solve(s)`: down → `[failed, -1]`. Else start with own work; for each call get the dependency's result; decide timed out, failed fast or succeeded; add the time; update flags. Store and return.\n\n**Dry run** on the example: billing is down. Booking: 20 + timeout 200 = 220, critical failure → failed. Web: booking answers in 220 ≤ 500, so the call takes 220 and fails because booking failed: 10 + 220 = 230, failed.",
        complexity="Time O(V + E) thanks to memoisation; space O(V).",
        pitfalls="A failed dependency that answers within the timeout fails *fast*: charge its response time, not the timeout. A response time exactly equal to the timeout is in time. Non-critical failures give `degraded`, not `failed`. Never compare the `-1` of a down service with a timeout.",
        follow_up="Lower the timeouts in the example and watch the response time of `web` fall. Then mark the billing call non-critical to see graceful degradation.",
    ),
),
dict(
    id="msvc-chain-availability",
    title="Availability of a Call Chain, with and without Fallbacks",
    difficulty="Easy",
    pattern="Resilience",
    entry="chain_availability",
    compare="float",
    description=r"""
A request needs every step of a chain to succeed. `chain` is a list of steps. Each step is `[availability]` or `[availability, fallback_availability]`, with values between 0 and 1. Failures are independent.

- Without fallbacks, a step succeeds with probability `availability`.
- With a fallback (for example a cache or a default answer), the step also succeeds when the primary fails and the fallback works: `availability + (1 - availability) * fallback_availability`.

Return `[without_fallbacks, with_fallbacks]`: the probability that the whole chain succeeds in each case. An empty chain succeeds with probability `1.0`.

**Example:** `[[0.99], [0.99, 0.9], [0.95, 1.0]]` → `[0.931095, 0.98901]`
""",
    starter='''def chain_availability(chain: List[List[float]]) -> List[float]:
    pass
''',
    solution='''def chain_availability(chain):
    plain = better = 1.0
    for step in chain:
        a = step[0]
        plain *= a
        f = step[1] if len(step) > 1 else 0.0
        better *= a + (1 - a) * f
    return [plain, better]
''',
    tests=[
        [[[0.99], [0.99, 0.9], [0.95, 1.0]]],
        [[[0.999], [0.999], [0.999]]],
        [[]],
        [[[1.0]]],
        [[[0.0, 1.0]]],
        [[[0.5, 0.5], [0.5, 0.5]]],
        [[[0.9, 0.0], [0.9]]],
        [[[0.999]] * 30],
        [[[0.99, 0.99]] * 10],
        [[[0.0]]],
        [[[0.9], [0.8, 0.5], [0.7, 0.25], [1.0, 0.0]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def chain_availability(chain):
    plain = better = 1.0
    for step in chain:
        a = step[0]
        plain *= a
        better *= max(a, step[1]) if len(step) > 1 else a
    return [plain, better]
''',
        '''def chain_availability(chain):
    if not chain:
        return [1.0, 1.0]
    plain = min(s[0] for s in chain)
    better = min(s[0] + (1 - s[0]) * (s[1] if len(s) > 1 else 0.0) for s in chain)
    return [plain, better]
''',
    ],
    guide=dict(
        prereqs="Availability arithmetic from *Architecture from zero* and degraded functionality from the resiliency lessons. Multiplying probabilities.",
        intuition="Steps in series multiply, so a long chain is less available than its weakest link. A fallback is a second chance for one step, and it only matters in the fraction of cases where the primary failed.",
        hints=[
            "Start two running products at 1.0.",
            "For a step without a fallback, treat the fallback availability as 0.",
            "The improved step availability is `a + (1 - a) * f`.",
        ],
        brute_force="Enumerate every combination of up and down for all components and add the probabilities of the working combinations: O(2^n). Independence lets you multiply instead.",
        approach="One loop, two products.\n\n**Dry run** on the example: plain 0.99 × 0.99 × 0.95 = 0.931095. With fallbacks: 0.99, then 0.99 + 0.01 × 0.9 = 0.999, then 0.95 + 0.05 × 1.0 = 1.0; product 0.98901.",
        complexity="Time O(n); space O(1).",
        pitfalls="Taking the minimum instead of the product. Using `max(a, f)` for a fallback. Forgetting the empty chain.",
        follow_up="Thirty services at 99.9% each give about 97% for the chain. That one line is a strong argument against deep synchronous call chains.",
    ),
),
dict(
    id="msvc-ttl-cache",
    title="Cache with TTL and Invalidation Events",
    difficulty="Medium",
    pattern="Caching",
    kind="class",
    entry="TagCache",
    description=r"""
Implement a cache that combines the two common invalidation mechanisms: a time to live (TTL) and explicit invalidation by events. Timestamps are integers that never decrease.

`TagCache(ttl)`

- `put(key, value, tags, ts)` → `None`. Stores the value with a list of tag strings (for example `"pet:7"`). Replaces any earlier entry for the key, including its tags.
- `get(key, ts)` → the value if the key is stored and `ts < stored_at + ttl`; otherwise `None`. An expired entry is removed. Each call counts as one hit or one miss.
- `invalidate(tag, ts)` → the number of entries removed. Removes every entry carrying the tag that is still live at `ts`; expired entries carrying the tag are removed too but are not counted.
- `stats()` → `[hits, misses]`.

**Example:** `TagCache(10)`: `put("pet:7:summary", "Miso", ["pet:7"], 0)`, `get("pet:7:summary", 5)` → `"Miso"`, `invalidate("pet:7", 6)` → `1`, `get("pet:7:summary", 7)` → `None`, `stats()` → `[1, 1]`.
""",
    starter='''class TagCache:
    def __init__(self, ttl: int):
        pass

    def put(self, key: str, value, tags: List[str], ts: int) -> None:
        pass

    def get(self, key: str, ts: int):
        pass

    def invalidate(self, tag: str, ts: int) -> int:
        pass

    def stats(self) -> List[int]:
        pass
''',
    solution='''class TagCache:
    def __init__(self, ttl):
        self.ttl = ttl
        self.data = {}      # key -> (value, tags, stored_at)
        self.by_tag = {}    # tag -> set of keys
        self.hits = self.misses = 0

    def _drop(self, key):
        _, tags, _ = self.data.pop(key)
        for t in tags:
            self.by_tag[t].discard(key)

    def put(self, key, value, tags, ts):
        if key in self.data:
            self._drop(key)
        self.data[key] = (value, list(tags), ts)
        for t in tags:
            self.by_tag.setdefault(t, set()).add(key)

    def get(self, key, ts):
        entry = self.data.get(key)
        if entry is not None and ts < entry[2] + self.ttl:
            self.hits += 1
            return entry[0]
        if entry is not None:
            self._drop(key)
        self.misses += 1
        return None

    def invalidate(self, tag, ts):
        removed = 0
        for key in list(self.by_tag.get(tag, ())):
            if ts < self.data[key][2] + self.ttl:
                removed += 1
            self._drop(key)
        return removed

    def stats(self):
        return [self.hits, self.misses]
''',
    tests=[
        [["TagCache", "put", "get", "invalidate", "get", "stats"],
         [[10], ["pet:7:summary", "Miso", ["pet:7"], 0], ["pet:7:summary", 5], ["pet:7", 6], ["pet:7:summary", 7], []]],
        [["TagCache", "get", "invalidate", "stats"], [[10], ["x", 0], ["t", 0], []]],
        [["TagCache", "put", "get", "get", "get", "stats"], [[10], ["k", 1, [], 0], ["k", 9], ["k", 10], ["k", 11], []]],
        [["TagCache", "put", "put", "put", "invalidate", "get", "get", "get"],
         [[100], ["a", 1, ["pet:1", "owner:9"], 0], ["b", 2, ["pet:2", "owner:9"], 0], ["c", 3, ["pet:3"], 0], ["owner:9", 1], ["a", 2], ["b", 2], ["c", 2]]],
        [["TagCache", "put", "put", "invalidate", "invalidate", "get"],
         [[100], ["a", 1, ["old"], 0], ["a", 2, ["new"], 1], ["old", 2], ["new", 2], ["a", 3]]],
        [["TagCache", "put", "put", "invalidate", "invalidate"],
         [[10], ["a", 1, ["t"], 0], ["b", 2, ["t"], 5], ["t", 12], ["t", 12]]],
        [["TagCache", "put", "get", "put", "get", "get", "stats"],
         [[10], ["a", 1, ["t"], 0], ["a", 10], ["a", 2, ["t"], 10], ["a", 19], ["a", 20], []]],
        [["TagCache", "put", "put", "get", "get", "stats"], [[5], ["a", None, [], 0], ["b", 0, [], 0], ["a", 1], ["b", 1], []]],
        [["TagCache", "put", "invalidate", "put", "get", "invalidate", "stats"],
         [[10], ["a", "x", ["t", "t"], 0], ["t", 1], ["a", "y", ["t"], 2], ["a", 3], ["u", 3], []]],
        [["TagCache"] + ["put"] * 20 + ["invalidate", "invalidate", "get", "get", "stats"],
         [[50]] + [["k%d" % i, i, ["even" if i % 2 == 0 else "odd", "all"], i] for i in range(20)] + [["even", 20], ["all", 60], ["k1", 60], ["k19", 68], []]],
        [["TagCache", "put", "get", "invalidate", "get", "stats"], [[0], ["a", 1, ["t"], 0], ["a", 0], ["t", 0], ["a", 0], []]],
    ],
    examples=1,
    wrong_solutions=[
        '''class TagCache:
    def __init__(self, ttl):
        self.ttl, self.data, self.hits, self.misses = ttl, {}, 0, 0
    def put(self, key, value, tags, ts):
        self.data[key] = (value, list(tags), ts)
    def get(self, key, ts):
        entry = self.data.get(key)
        if entry is not None and ts <= entry[2] + self.ttl:
            self.hits += 1
            return entry[0]
        self.data.pop(key, None)
        self.misses += 1
        return None
    def invalidate(self, tag, ts):
        keys = [k for k, e in self.data.items() if tag in e[1]]
        for k in keys:
            del self.data[k]
        return len(keys)
    def stats(self):
        return [self.hits, self.misses]
''',
        '''class TagCache:
    def __init__(self, ttl):
        self.ttl, self.data, self.by_tag, self.hits, self.misses = ttl, {}, {}, 0, 0
    def put(self, key, value, tags, ts):
        self.data[key] = (value, ts)
        for t in tags:
            self.by_tag.setdefault(t, set()).add(key)
    def get(self, key, ts):
        entry = self.data.get(key)
        if entry is not None and ts < entry[1] + self.ttl:
            self.hits += 1
            return entry[0]
        self.data.pop(key, None)
        self.misses += 1
        return None
    def invalidate(self, tag, ts):
        removed = 0
        for key in self.by_tag.pop(tag, set()):
            if key in self.data:
                if ts < self.data[key][1] + self.ttl:
                    removed += 1
                del self.data[key]
        return removed
    def stats(self):
        return [self.hits, self.misses]
''',
    ],
    guide=dict(
        prereqs="Cache invalidation from the lesson *Caching and autoscaling*. Dictionaries of sets.",
        intuition="TTL is the safety net: nothing stays wrong for longer than the TTL. Tags are the fast path: when the source of truth announces a change, every cached answer derived from it is thrown away at once.",
        hints=[
            "Store value, tags and the time of storage per key, plus a reverse index from tag to keys.",
            "Write one helper that removes a key and cleans the reverse index, and use it for replacement, expiry and invalidation.",
            "In `invalidate`, copy the set of keys before removing from it, and count only entries that are still live.",
        ],
        brute_force="Without the reverse index, `invalidate` scans every entry for the tag: O(n) per event. With many events per second that scan dominates. The index makes it proportional to the number of affected entries.",
        approach="`data[key] = (value, tags, stored_at)`, `by_tag[tag] = {keys}`. `put` drops the old entry first. `get` checks `ts < stored_at + ttl`. `invalidate` walks the tag's keys.\n\n**Dry run** of the example: put at 0. `get` at 5: 5 < 10 → hit. `invalidate(pet:7)` at 6 removes one live entry → 1. `get` at 7 → miss. Stats [1, 1].",
        complexity="`put` and `get` O(number of tags on the entry); `invalidate` O(entries with that tag). Space O(entries + tags).",
        pitfalls="Leaving the old tags of a replaced key in the index, so that a later event wrongly removes the new entry. Using `<=` for expiry. Confusing a stored value of `None` with a miss when counting. Counting expired entries as removed.",
        follow_up="Invalidation events can be lost or arrive late, which is why real caches keep the TTL as well. See the lesson's golden rule: cache in as few places as possible.",
    ),
),
]
