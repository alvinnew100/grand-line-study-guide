PROBLEMS = [
dict(
    id="think-revert-set",
    title="Pick the Revert Set from a Failing-Test Matrix",
    difficulty="Medium",
    pattern="CI/CD Process",
    entry="revert_set",
    description=r"""
Main is red. Culprit-finding has re-run the failing tests with individual commits reverted and
produced a matrix: `fixes[commit]` is the list of failing tests that pass again when that commit alone
is reverted. Assume the effects combine: reverting several commits fixes the union of their lists.

Given `failing` (the tests that are red) and `fixes`, return the **smallest set of commits** to revert
so that every failing test is fixed, as a list of commit ids sorted ascending.

- If several smallest sets exist return the one whose sorted list is lexicographically smallest.
- If `failing` is empty return `[]`.
- If no set of commits fixes everything return `None`.

**Example:** `failing = ["t1","t2","t3"]`,
`fixes = {"c1": ["t1"], "c2": ["t1","t2"], "c3": ["t3"]}` → `["c2", "c3"]`

Constraints: at most 14 commits and 40 tests. Lists in `fixes` may mention tests that are not failing.
""",
    starter='''def revert_set(failing: List[str], fixes: dict):
    pass
''',
    solution='''def revert_set(failing, fixes):
    need = set(failing)
    commits = sorted(fixes)
    cover = {c: set(fixes[c]) & need for c in commits}
    for k in range(len(commits) + 1):
        for combo in itertools.combinations(commits, k):
            got = set()
            for c in combo:
                got |= cover[c]
            if got == need:
                return list(combo)
    return None
''',
    tests=[
        [["t1", "t2", "t3"], {"c1": ["t1"], "c2": ["t1", "t2"], "c3": ["t3"]}],
        [[], {"c1": ["t1"]}],
        [["t1"], {}],
        [[], {}],
        [["t1", "t2"], {"c1": ["t1"]}],
        [["t1", "t2", "t3", "t4", "t5", "t6"], {"a": ["t1", "t2", "t3", "t4"], "b": ["t1", "t2", "t5"], "c": ["t3", "t4", "t6"]}],
        [["t1", "t2"], {"z": ["t1", "t2"], "a": ["t1"], "b": ["t2"]}],
        [["t1", "t2"], {"b": ["t1", "t2"], "a": ["t1", "t2"]}],
        [["t1", "t2"], {"c9": ["t1"], "c1": ["t2"], "c5": ["t1"], "c3": ["t2"]}],
        [["x"], {"c1": ["y", "z"], "c2": ["x", "y"]}],
        [["t%d" % i for i in range(12)], {"c%02d" % j: ["t%d" % i for i in range(12) if (i + j) % 3 == 0 or i == j] for j in range(12)}],
        [["t%d" % i for i in range(30)], {"c%02d" % j: ["t%d" % i for i in range(30) if (i * j) % 7 < 2] for j in range(14)}],
        [["t%d" % i for i in range(8)], {"c%d" % j: ["t%d" % j] for j in range(8)}],
        [["a", "b", "c", "d"], {"k1": ["a", "b"], "k2": ["c", "d"], "k3": ["a", "c"], "k4": ["b", "d"], "k0": ["a", "d", "noise"]}],
    ],
    examples=1,
    wrong_solutions=[
        '''def revert_set(failing, fixes):
    need = set(failing)
    out = []
    while need:
        best = max(sorted(fixes), key=lambda c: len(set(fixes[c]) & need), default=None)
        if best is None or not (set(fixes[best]) & need):
            return None
        out.append(best)
        need -= set(fixes[best])
    return sorted(out)
''',
        '''def revert_set(failing, fixes):
    need = set(failing)
    out = sorted(c for c in fixes if set(fixes[c]) & need)
    got = set()
    for c in out:
        got |= set(fixes[c])
    return out if need <= got else None
''',
        '''def revert_set(failing, fixes):
    need = set(failing)
    commits = sorted(fixes, reverse=True)
    for k in range(len(commits) + 1):
        for combo in itertools.combinations(commits, k):
            got = set()
            for c in combo:
                got |= set(fixes[c])
            if need <= got:
                return sorted(combo)
    return None
''',
    ],
    guide=dict(
        prereqs="Lesson *Buggy code on main* (revert-first, culprit finding). `itertools.combinations`; set cover.",
        intuition="Each commit 'covers' some failing tests; you want the fewest commits whose coverage adds up to "
                  "everything. That is the set-cover problem, and with at most 14 commits you can simply try sets "
                  "in increasing size.",
        hints=[
            "Reverting less is safer, so search sizes 0, 1, 2, … and stop at the first size that works.",
            "`itertools.combinations(sorted(commits), k)` yields candidates in lexicographic order — the first hit "
            "at a given size is automatically the required tie-break winner.",
            "A candidate works when the union of its fix lists contains every failing test.",
        ],
        brute_force="Test all 2^14 = 16,384 subsets and keep the best by (size, sorted list). Fine here; the "
                    "size-ordered search is the same idea but stops early.",
        approach="Sort the commit ids, loop k from 0, loop combinations, union, compare.\n\n**Dry run** example: "
                 "k=0: empty set fixes nothing. k=1: c1 {t1}, c2 {t1,t2}, c3 {t3} — none covers all. k=2: (c1,c2) → "
                 "{t1,t2}; (c1,c3) → {t1,t3}; (c2,c3) → {t1,t2,t3} ✓ → `['c2','c3']`.",
        complexity="Worst case O(2^C · C · T) for C commits and T tests; space O(C · T).",
        pitfalls="- Greedy 'revert the commit that fixes the most' is not optimal (a big commit can be redundant "
                 "once two smaller ones are chosen).\n- Reverting every commit that touches a failing test.\n"
                 "- Confusing the empty answer (`[]`, nothing to do) with the impossible answer (`None`).",
        follow_up="Weight commits by revert risk (lines changed, dependents) and minimise total weight instead of count.",
    ),
),
dict(
    id="think-canary-decision",
    title="Rollout Decision from Canary Metrics",
    difficulty="Medium",
    pattern="CI/CD Process",
    entry="canary_decision",
    description=r"""
An automated canary analysis compares the new version (canary) with the current one (baseline).

- `baseline = [requests, errors, p95_ms]` and `canary = [requests, errors, p95_ms]`
  (`baseline` requests > 0).
- `policy = [min_requests, max_delta_bp, max_latency_pct]`:
  the canary needs at least `min_requests` requests before any judgement; its error **rate** may
  exceed the baseline's by at most `max_delta_bp` basis points (1 bp = 0.01 percentage points =
  1/10000); its p95 latency may be at most `max_latency_pct` percent of the baseline's (e.g. `120`
  allows up to 20 % slower).

Decide, checking **in this order**:

1. `canary requests < min_requests` → `"HOLD"` (not enough data).
2. error-rate difference `canary_rate - baseline_rate` **strictly greater** than `max_delta_bp / 10000` → `"ROLLBACK"`.
3. `canary_p95 * 100 > baseline_p95 * max_latency_pct` → `"ROLLBACK"`.
4. Warning zone → `"HOLD"`: the error-rate difference is strictly greater than **half** the allowed
   delta, **or** `canary_p95 * 200 > baseline_p95 * (100 + max_latency_pct)` (more than half the
   allowed slowdown).
5. Otherwise → `"PROMOTE"`.

Use exact integer arithmetic (cross-multiply) so that values exactly on a threshold are handled
correctly.

**Example:** `baseline = [100000, 100, 200]`, `canary = [5000, 30, 210]`, `policy = [1000, 40, 120]` →
`"ROLLBACK"` (0.60 % vs 0.10 % is a 50 bp difference, above 40)

**Example:** `baseline = [100000, 100, 200]`, `canary = [5000, 6, 205]`, `policy = [1000, 40, 120]` → `"PROMOTE"`
""",
    starter='''def canary_decision(baseline: List[int], canary: List[int], policy: List[int]) -> str:
    pass
''',
    solution='''def canary_decision(baseline, canary, policy):
    b_req, b_err, b_p95 = baseline
    c_req, c_err, c_p95 = canary
    min_req, max_bp, max_pct = policy
    if c_req < min_req:
        return "HOLD"
    diff = (c_err * b_req - b_err * c_req) * 10000
    allowed = max_bp * b_req * c_req
    if diff > allowed:
        return "ROLLBACK"
    if c_p95 * 100 > b_p95 * max_pct:
        return "ROLLBACK"
    if 2 * diff > allowed or c_p95 * 200 > b_p95 * (100 + max_pct):
        return "HOLD"
    return "PROMOTE"
''',
    tests=[
        [[100000, 100, 200], [5000, 30, 210], [1000, 40, 120]],
        [[100000, 100, 200], [5000, 6, 205], [1000, 40, 120]],
        [[100000, 100, 200], [999, 500, 900], [1000, 40, 120]],
        [[100000, 100, 200], [1000, 5, 200], [1000, 40, 120]],
        [[100000, 100, 200], [10000, 50, 200], [1000, 40, 120]],
        [[100000, 100, 200], [10000, 51, 200], [1000, 40, 120]],
        [[100000, 100, 200], [10000, 30, 200], [1000, 40, 120]],
        [[100000, 100, 200], [10000, 31, 200], [1000, 40, 120]],
        [[100000, 100, 200], [10000, 10, 240], [1000, 40, 120]],
        [[100000, 100, 200], [10000, 10, 241], [1000, 40, 120]],
        [[100000, 100, 200], [10000, 10, 220], [1000, 40, 120]],
        [[100000, 100, 200], [10000, 10, 221], [1000, 40, 120]],
        [[100000, 0, 150], [2000, 0, 100], [1000, 0, 100]],
        [[100000, 0, 150], [2000, 1, 100], [1000, 0, 100]],
        [[3, 1, 100], [7, 2, 100], [5, 1000, 300]],
    ],
    examples=2,
    wrong_solutions=[
        '''def canary_decision(baseline, canary, policy):
    b_req, b_err, b_p95 = baseline
    c_req, c_err, c_p95 = canary
    min_req, max_bp, max_pct = policy
    if c_req < min_req:
        return "HOLD"
    diff = (c_err * b_req - b_err * c_req) * 10000
    allowed = max_bp * b_req * c_req
    if diff >= allowed:
        return "ROLLBACK"
    if c_p95 * 100 >= b_p95 * max_pct:
        return "ROLLBACK"
    if 2 * diff >= allowed or c_p95 * 200 >= b_p95 * (100 + max_pct):
        return "HOLD"
    return "PROMOTE"
''',
        '''def canary_decision(baseline, canary, policy):
    b_req, b_err, b_p95 = baseline
    c_req, c_err, c_p95 = canary
    min_req, max_bp, max_pct = policy
    diff = (c_err * b_req - b_err * c_req) * 10000
    allowed = max_bp * b_req * c_req
    if diff > allowed or c_p95 * 100 > b_p95 * max_pct:
        return "ROLLBACK"
    if c_req < min_req:
        return "HOLD"
    if 2 * diff > allowed or c_p95 * 200 > b_p95 * (100 + max_pct):
        return "HOLD"
    return "PROMOTE"
''',
        '''def canary_decision(baseline, canary, policy):
    b_req, b_err, b_p95 = baseline
    c_req, c_err, c_p95 = canary
    min_req, max_bp, max_pct = policy
    if c_req < min_req:
        return "HOLD"
    if (c_err - b_err) * 10000 > max_bp * c_req:
        return "ROLLBACK"
    if c_p95 * 100 > b_p95 * max_pct:
        return "ROLLBACK"
    if 2 * (c_err - b_err) * 10000 > max_bp * c_req or c_p95 * 200 > b_p95 * (100 + max_pct):
        return "HOLD"
    return "PROMOTE"
''',
        '''def canary_decision(baseline, canary, policy):
    b_req, b_err, b_p95 = baseline
    c_req, c_err, c_p95 = canary
    min_req, max_bp, max_pct = policy
    if c_req < min_req:
        return "HOLD"
    diff = (c_err * b_req - b_err * c_req) * 10000
    allowed = max_bp * b_req * c_req
    if diff > allowed or c_p95 * 100 > b_p95 * max_pct:
        return "ROLLBACK"
    return "PROMOTE"
''',
    ],
    guide=dict(
        prereqs="Lesson *A bad deploy, a risky migration and the hotfix flow* (canary analysis). Rates vs counts.",
        intuition="A canary sees far less traffic than the baseline, so compare *rates*, never raw counts — and "
                  "refuse to judge until the canary has enough requests for its rate to mean anything.",
        hints=[
            "Rate = errors / requests. The difference of two fractions can be compared without floats by "
            "multiplying through by both denominators.",
            "`c_err/c_req - b_err/b_req > bp/10000` ⇔ `(c_err·b_req − b_err·c_req)·10000 > bp·b_req·c_req`.",
            "The warning zone uses the same quantities with a factor of two; write the five checks in order.",
        ],
        brute_force="Compute the rates as floats and compare. It is correct almost always, but values exactly on a "
                    "threshold (0.5 % − 0.1 % vs 0.4 %) can land on either side because of binary rounding.",
        approach="Unpack, guard on sample size, then two rollback checks, one warning check, default promote.\n\n"
                 "**Dry run** example 1: diff = (30·100000 − 100·5000)·10000 = 2.5·10¹⁰; allowed = 40·100000·5000 = "
                 "2·10¹⁰; diff > allowed → `ROLLBACK`.",
        complexity="O(1) time and space.",
        pitfalls="- Comparing error counts instead of rates.\n- Judging a canary with too few requests.\n"
                 "- `>=` where the spec says strictly greater.\n- Forgetting the warning zone entirely.",
        follow_up="Replace the fixed threshold with a statistical test (e.g. a one-sided test on two proportions) and "
                  "discuss how the required sample size grows as the baseline error rate shrinks.",
    ),
),
dict(
    id="think-retry-outcome",
    title="Outcome of a Retry Policy with Backoff",
    difficulty="Medium",
    pattern="Reliability Policies",
    entry="retry_outcome",
    description=r"""
A client calls a flaky dependency under a retry policy with exponential backoff. Simulate it.

- `attempts`: list of `[duration_ms, result]` describing what each successive attempt *would* do;
  `result` is `"ok"`, `"retryable"` (e.g. timeout, HTTP 503) or `"fatal"` (e.g. HTTP 400).
  It has at least `max_attempts` entries.
- `max_attempts >= 1`, `base_delay`, `multiplier` (integer ≥ 1), `max_delay`, `deadline` — all in ms.

Start with `time = 0`. For attempt number `k = 1, 2, ...`:

1. `time += duration` of attempt `k`.
2. `"ok"` → return `["SUCCESS", k, time]` (even if `time` is past the deadline — the work is done).
3. `"fatal"` → return `["FAILED", k, time]` (never retry a non-retryable error).
4. `"retryable"`: if `k == max_attempts` → `["EXHAUSTED", k, time]`.
   Otherwise `delay = min(base_delay * multiplier^(k-1), max_delay)`; if `time + delay >= deadline`
   → `["DEADLINE", k, time]` (there is no point waiting); else `time += delay` and try again.

**Example:** `attempts = [[100,"retryable"],[100,"retryable"],[50,"ok"]]`, `max_attempts = 5`,
`base_delay = 200`, `multiplier = 2`, `max_delay = 1000`, `deadline = 5000` → `["SUCCESS", 3, 850]`
(100 + wait 200 + 100 + wait 400 + 50)
""",
    starter='''def retry_outcome(attempts: List[list], max_attempts: int, base_delay: int,
                  multiplier: int, max_delay: int, deadline: int) -> list:
    pass
''',
    solution='''def retry_outcome(attempts, max_attempts, base_delay, multiplier, max_delay, deadline):
    time = 0
    for k in range(1, max_attempts + 1):
        duration, result = attempts[k - 1]
        time += duration
        if result == "ok":
            return ["SUCCESS", k, time]
        if result == "fatal":
            return ["FAILED", k, time]
        if k == max_attempts:
            return ["EXHAUSTED", k, time]
        delay = min(base_delay * multiplier ** (k - 1), max_delay)
        if time + delay >= deadline:
            return ["DEADLINE", k, time]
        time += delay
''',
    tests=[
        [[[100, "retryable"], [100, "retryable"], [50, "ok"]], 5, 200, 2, 1000, 5000],
        [[[30, "ok"]], 1, 100, 2, 1000, 1000],
        [[[30, "retryable"]], 1, 100, 2, 1000, 1000],
        [[[30, "fatal"], [10, "ok"]], 3, 100, 2, 1000, 1000],
        [[[10, "retryable"], [10, "fatal"], [10, "ok"]], 3, 100, 2, 1000, 1000],
        [[[10, "retryable"]] * 6, 6, 100, 2, 1000, 100000],
        [[[10, "retryable"]] * 6, 6, 100, 2, 300, 100000],
        [[[10, "retryable"]] * 6 + [[10, "ok"]], 4, 100, 3, 5000, 100000],
        [[[100, "retryable"], [100, "ok"]], 3, 400, 2, 1000, 500],
        [[[100, "retryable"], [100, "ok"]], 3, 400, 2, 1000, 501],
        [[[2000, "ok"]], 3, 100, 2, 1000, 500],
        [[[100, "retryable"], [100, "retryable"], [100, "retryable"], [5, "ok"]], 4, 50, 1, 1000, 10000],
        [[[0, "retryable"]] * 20 + [[0, "ok"]], 30, 1, 2, 60000, 10 ** 9],
        [[[500, "retryable"], [500, "retryable"], [500, "ok"]], 3, 100, 10, 800, 2500],
    ],
    examples=1,
    wrong_solutions=[
        '''def retry_outcome(attempts, max_attempts, base_delay, multiplier, max_delay, deadline):
    time = 0
    for k in range(1, max_attempts + 1):
        duration, result = attempts[k - 1]
        time += duration
        if result == "ok":
            return ["SUCCESS", k, time]
        if k == max_attempts:
            return ["EXHAUSTED", k, time]
        delay = min(base_delay * multiplier ** (k - 1), max_delay)
        if time + delay >= deadline:
            return ["DEADLINE", k, time]
        time += delay
''',
        '''def retry_outcome(attempts, max_attempts, base_delay, multiplier, max_delay, deadline):
    time = 0
    for k in range(1, max_attempts + 1):
        duration, result = attempts[k - 1]
        time += duration
        if result == "ok":
            return ["SUCCESS", k, time]
        if result == "fatal":
            return ["FAILED", k, time]
        if k == max_attempts:
            return ["EXHAUSTED", k, time]
        delay = base_delay * multiplier ** (k - 1)
        if time + delay >= deadline:
            return ["DEADLINE", k, time]
        time += delay
''',
        '''def retry_outcome(attempts, max_attempts, base_delay, multiplier, max_delay, deadline):
    time = 0
    for k in range(1, max_attempts + 1):
        duration, result = attempts[k - 1]
        time += duration
        if result == "ok":
            return ["SUCCESS", k, time]
        if result == "fatal":
            return ["FAILED", k, time]
        if k == max_attempts:
            return ["EXHAUSTED", k, time]
        delay = min(base_delay * multiplier ** k, max_delay)
        if time + delay > deadline:
            return ["DEADLINE", k, time]
        time += delay
''',
    ],
    guide=dict(
        prereqs="Lesson *Debugging and incident questions* (retries, timeouts) and the payments-API worked answer.",
        intuition="A retry policy is a loop with four exits: success, a non-retryable error, running out of "
                  "attempts, and running out of time. Simulate the clock and take the first exit that applies.",
        hints=[
            "Track a single `time` variable; add the attempt duration first, then decide.",
            "The delay before attempt k+1 is `base * multiplier**(k-1)`, capped at `max_delay`.",
            "Check the exits in the order given: ok, fatal, attempts exhausted, deadline — then sleep.",
        ],
        brute_force="There is nothing cheaper than the direct simulation; the 'brute force' mistake is to "
                    "precompute all delays without the cap or the deadline and add them up.",
        approach="One loop over attempt numbers.\n\n**Dry run** of the example: k=1: time 100, retryable, delay "
                 "min(200,1000)=200, 300 < 5000 → time 300. k=2: time 400, retryable, delay 400 → time 800. "
                 "k=3: time 850, ok → `['SUCCESS', 3, 850]`.",
        complexity="O(max_attempts) time, O(1) space.",
        pitfalls="- Retrying fatal errors (a 400 will fail identically every time).\n- Forgetting the delay cap.\n"
                 "- Off-by-one in the exponent: the first wait is `base_delay`, not `base_delay * multiplier`.\n"
                 "- Using `>` instead of `>=` for the deadline check.",
        follow_up="Add jitter (randomised delay) and explain why synchronised retries cause a thundering herd.",
    ),
),
dict(
    id="think-rate-limiter",
    title="Token-Bucket Rate Limiter Outcome",
    difficulty="Easy",
    pattern="Reliability Policies",
    entry="rate_limit",
    description=r"""
A token bucket holds at most `capacity` tokens and starts **full**. `refill` tokens are added for
every whole second that passes (never exceeding `capacity`). Each request arrives at an integer
timestamp (seconds, non-decreasing) and is **allowed** if at least one token is available — it then
consumes one — otherwise it is **rejected** and consumes nothing.

Refill is applied before each request, based on the seconds elapsed since the previous request
(the first request sees the full bucket).

Return a list of booleans, one per request.

**Example:** `capacity = 2, refill = 1, times = [0, 0, 0, 1, 1, 5, 5, 5]` →
`[True, True, False, True, False, True, True, False]`

Constraints: `1 <= capacity <= 10^6`, `0 <= refill <= 10^6`, up to `10^5` requests.
""",
    starter='''def rate_limit(capacity: int, refill: int, times: List[int]) -> List[bool]:
    pass
''',
    solution='''def rate_limit(capacity, refill, times):
    tokens = capacity
    last = None
    out = []
    for t in times:
        if last is not None:
            tokens = min(capacity, tokens + (t - last) * refill)
        last = t
        if tokens > 0:
            tokens -= 1
            out.append(True)
        else:
            out.append(False)
    return out
''',
    tests=[
        [2, 1, [0, 0, 0, 1, 1, 5, 5, 5]],
        [1, 1, []],
        [1, 0, [0, 1, 2, 3]],
        [3, 0, [5, 5, 5, 5, 9]],
        [1, 1, [0, 1, 2, 3]],
        [1, 1, [0, 0, 1, 1, 2, 2]],
        [5, 2, [0, 0, 0, 0, 0, 0, 1, 1, 1, 100, 100, 100, 100, 100, 100]],
        [2, 5, [10, 10, 10, 11, 11, 11]],
        [3, 1, [0, 0, 0, 2, 2, 2, 3]],
        [10, 3, [7] * 12 + [8] * 5 + [9] * 2 + [20] * 11],
        [100, 10, [i // 30 for i in range(3000)]],
        [1, 1000000, [0, 0, 1, 1]],
        [4, 1, [0, 0, 3, 3, 3, 3, 3]],
    ],
    examples=1,
    wrong_solutions=[
        '''def rate_limit(capacity, refill, times):
    tokens = capacity; last = None; out = []
    for t in times:
        if last is not None:
            tokens = tokens + (t - last) * refill
        last = t
        if tokens > 0:
            tokens -= 1; out.append(True)
        else:
            out.append(False)
    return out
''',
        '''def rate_limit(capacity, refill, times):
    out = []; window = None; used = 0
    for t in times:
        if t != window:
            window = t; used = 0
        if used < capacity:
            used += 1; out.append(True)
        else:
            out.append(False)
    return out
''',
        '''def rate_limit(capacity, refill, times):
    tokens = capacity; last = None; out = []
    for t in times:
        if last is not None and t > last:
            tokens = min(capacity, tokens + refill)
        last = t
        if tokens > 0:
            tokens -= 1; out.append(True)
        else:
            out.append(False)
    return out
''',
    ],
    guide=dict(
        prereqs="The payments-API worked answer (rate limits) and lesson *Estimation*. Simple simulation.",
        intuition="You never need a timer thread. Lazily top the bucket up when a request arrives: tokens earned = "
                  "seconds elapsed × refill rate, clipped to the capacity.",
        hints=[
            "Remember the timestamp of the previous request.",
            "Before serving, add `(t - last) * refill` tokens and clamp with `min(capacity, …)`.",
            "Allowed iff `tokens > 0`; only then subtract one.",
        ],
        brute_force="Advance a clock one second at a time, adding tokens each tick. O(time span) instead of "
                    "O(requests) — hopeless when timestamps are far apart.",
        approach="Lazy refill in one pass.\n\n**Dry run** capacity 2, refill 1: t=0 → 2 tokens: allow, allow, "
                 "reject. t=1 → +1 = 1: allow, reject. t=5 → +4 capped at 2: allow, allow, reject.",
        complexity="Time O(n), space O(1) besides the output.",
        pitfalls="- No cap: a quiet hour would bank thousands of tokens and permit a huge burst.\n"
                 "- Fixed-window counting, which is a different algorithm.\n"
                 "- Refilling by `refill` once regardless of how many seconds passed.",
        follow_up="Compare with a sliding-window log limiter; discuss per-user versus global buckets.",
    ),
),
dict(
    id="think-triage-order",
    title="Order Incident Hypotheses by Probability and Cost",
    difficulty="Medium",
    pattern="Incident Triage",
    entry="triage_order",
    compare="float",
    description=r"""
During an incident you hold several hypotheses about the cause. Each is `[name, probability, cost]`:
your estimated probability (an integer percentage) that it is the cause, and the minutes needed to
check it (`cost >= 1`). Exactly one hypothesis is the true cause and you stop as soon as you check it.

The order that minimises the **expected time to find the cause** is: highest
`probability / cost` first. Break ties by lower `cost`, then by `name` ascending.

Return `[order, expected_minutes]` where `order` is the list of names in checking order and

$$\text{expected\_minutes} = \sum_i \frac{p_i}{100} \cdot (c_1 + c_2 + \dots + c_i)$$

with hypotheses numbered in checking order.

**Example:** `[["bad deploy", 50, 2], ["db overload", 30, 10], ["dns", 20, 1]]` →
`[["bad deploy", "dns", "db overload"], 5.5]`

Ratios are 25, 3 and 20. Expected = 0.5·2 + 0.2·3 + 0.3·13 = 5.5 minutes.

Constraints: up to `10^4` hypotheses; compare ratios exactly (cross-multiply), not with floats.
""",
    starter='''def triage_order(hypotheses: List[list]) -> list:
    pass
''',
    solution='''def triage_order(hypotheses):
    def cmp(a, b):
        left, right = a[1] * b[2], b[1] * a[2]
        if left != right:
            return -1 if left > right else 1
        if a[2] != b[2]:
            return -1 if a[2] < b[2] else 1
        return -1 if a[0] < b[0] else (1 if a[0] > b[0] else 0)
    ordered = sorted(hypotheses, key=functools.cmp_to_key(cmp))
    elapsed, expected = 0, 0.0
    for name, p, c in ordered:
        elapsed += c
        expected += p / 100 * elapsed
    return [[h[0] for h in ordered], expected]
''',
    tests=[
        [[["bad deploy", 50, 2], ["db overload", 30, 10], ["dns", 20, 1]]],
        [[["only", 100, 7]]],
        [[]],
        [[["a", 50, 10], ["b", 50, 1]]],
        [[["b", 40, 4], ["a", 40, 4], ["c", 20, 2]]],
        [[["x", 30, 3], ["y", 10, 1], ["z", 60, 6]]],
        [[["cheap-unlikely", 1, 1], ["costly-likely", 99, 60]]],
        [[["zero", 0, 1], ["sure", 100, 100]]],
        [[["h1", 25, 5], ["h2", 25, 4], ["h3", 25, 3], ["h4", 25, 2]]],
        [[["p", 33, 7], ["q", 33, 7], ["r", 34, 7]]],
        [[["m", 10, 3], ["n", 20, 6], ["o", 30, 9], ["k", 40, 12]]],
        [[["h%04d" % i, (i * 37) % 101, (i * 53) % 29 + 1] for i in range(2000)]],
        [[["third", 1, 3], ["seventh", 1, 7], ["rest", 98, 300]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def triage_order(hypotheses):
    ordered = sorted(hypotheses, key=lambda h: (-h[1], h[2], h[0]))
    elapsed, expected = 0, 0.0
    for name, p, c in ordered:
        elapsed += c; expected += p / 100 * elapsed
    return [[h[0] for h in ordered], expected]
''',
        '''def triage_order(hypotheses):
    ordered = sorted(hypotheses, key=lambda h: (h[2], -h[1], h[0]))
    elapsed, expected = 0, 0.0
    for name, p, c in ordered:
        elapsed += c; expected += p / 100 * elapsed
    return [[h[0] for h in ordered], expected]
''',
        '''def triage_order(hypotheses):
    ordered = sorted(hypotheses, key=lambda h: (-h[1] / h[2], h[2], h[0]))
    expected = sum(p / 100 * c for _, p, c in ordered)
    return [[h[0] for h in ordered], expected]
''',
        '''def triage_order(hypotheses):
    ordered = sorted(hypotheses, key=lambda h: (-(h[1] / h[2]), h[0]))
    elapsed, expected = 0, 0.0
    for name, p, c in ordered:
        elapsed += c; expected += p / 100 * elapsed
    return [[h[0] for h in ordered], expected]
''',
    ],
    guide=dict(
        prereqs="Lesson *Hypothesis-driven triage*. Sorting with a comparator (`functools.cmp_to_key`).",
        intuition="Checking a hypothesis delays every later one by its cost. Swapping two neighbours A then B to B "
                  "then A changes the expected time by p_B·c_A − p_A·c_B, so A should come first exactly when "
                  "p_A/c_A ≥ p_B/c_B. That exchange argument gives the ratio rule.",
        hints=[
            "A likely-but-slow check and an unlikely-but-instant check: which first? Compute both orders by hand.",
            "Compare two hypotheses with `a.p * b.c` versus `b.p * a.c` to avoid dividing.",
            "After sorting, walk the list keeping a running total of cost; add `p/100 * running_total` each step.",
        ],
        brute_force="Try every permutation and compute the expected time: O(n!) — unusable past ten hypotheses, but "
                    "a good way to convince yourself the ratio rule is optimal on small cases.",
        approach="Comparator sort then one accumulation pass.\n\n**Dry run** example: ratios 50/2 = 25, 30/10 = 3, "
                 "20/1 = 20 → order deploy, dns, db. Running cost 2, 3, 13 → 0.5·2 + 0.2·3 + 0.3·13 = 5.5.",
        complexity="Time O(n log n), space O(n).",
        pitfalls="- Sorting by probability alone (ignores cheap checks) or by cost alone.\n"
                 "- Summing p·c without the cumulative cost.\n- Dropping the cost tie-break.",
        follow_up="Add a mitigation that is cheap and safe regardless of cause (e.g. roll back): when should you "
                  "do it before any diagnosis at all?",
    ),
),
dict(
    id="think-estimate-capacity",
    title="Back-of-Envelope Capacity Estimator",
    difficulty="Easy",
    pattern="Estimation",
    entry="estimate",
    compare="float",
    tolerance=1e-6,
    description=r"""
Turn a list of assumptions into the three numbers every sizing answer needs.

Inputs: `dau` (daily active users), `actions` (average actions per user per day), `bytes_per_action`
(bytes stored per action), `peak_factor` (peak traffic ÷ average traffic), `replication` (number of
copies kept), `retention_days` (how long data is kept).

Return `[avg_qps, peak_qps, storage_gb]` where

- `avg_qps = dau * actions / 86400` (a day has 86,400 seconds),
- `peak_qps = avg_qps * peak_factor`,
- `storage_gb = dau * actions * bytes_per_action * replication * retention_days / 10^9`
  (decimal gigabytes).

Answers are compared with a relative tolerance of `1e-6`.

**Example:** `dau = 10_000_000, actions = 20, bytes_per_action = 500, peak_factor = 3, replication = 3,
retention_days = 365` → `[2314.814814..., 6944.444444..., 109500.0]`
""",
    starter='''def estimate(dau: int, actions: float, bytes_per_action: int, peak_factor: float,
             replication: int, retention_days: int) -> List[float]:
    pass
''',
    solution='''def estimate(dau, actions, bytes_per_action, peak_factor, replication, retention_days):
    per_day = dau * actions
    avg_qps = per_day / 86400
    storage_gb = per_day * bytes_per_action * replication * retention_days / 1e9
    return [avg_qps, avg_qps * peak_factor, storage_gb]
''',
    tests=[
        [10000000, 20, 500, 3, 3, 365],
        [0, 20, 500, 3, 3, 365],
        [86400, 1, 1000, 1, 1, 1],
        [1000000, 0.5, 2000000, 10, 2, 30],
        [500000000, 5, 300, 2, 3, 1825],
        [1, 1, 1, 1, 1, 1],
        [2500, 40, 1024, 4, 1, 90],
        [50000000, 2, 150, 2.5, 3, 7],
        [3000000, 100, 80, 5, 2, 0],
        [1200000, 15, 4096, 6, 3, 400],
        [750, 3.2, 250000, 1.5, 2, 365],
    ],
    examples=1,
    wrong_solutions=[
        '''def estimate(dau, actions, bytes_per_action, peak_factor, replication, retention_days):
    per_day = dau * actions
    avg_qps = per_day / 86400
    return [avg_qps, avg_qps * peak_factor, per_day * bytes_per_action * replication * retention_days / 1024 ** 3]
''',
        '''def estimate(dau, actions, bytes_per_action, peak_factor, replication, retention_days):
    per_day = dau * actions
    avg_qps = per_day / 86400
    return [avg_qps, avg_qps * peak_factor, per_day * bytes_per_action * retention_days / 1e9]
''',
        '''def estimate(dau, actions, bytes_per_action, peak_factor, replication, retention_days):
    per_day = dau * actions
    avg_qps = per_day / 100000
    return [avg_qps, avg_qps * peak_factor, per_day * bytes_per_action * replication * retention_days / 1e9]
''',
        '''def estimate(dau, actions, bytes_per_action, peak_factor, replication, retention_days):
    per_day = dau * actions
    avg_qps = per_day / 86400
    return [avg_qps, avg_qps + peak_factor, per_day * bytes_per_action * replication * retention_days / 1e9]
''',
    ],
    guide=dict(
        prereqs="Lesson *Back-of-envelope estimation*. Units: seconds per day, bytes per gigabyte.",
        intuition="Every sizing estimate is the same chain: users × actions = events per day; ÷ seconds per day = "
                  "rate; × bytes × copies × days = storage. Keeping the units on every factor prevents mistakes.",
        hints=[
            "Compute events per day once and reuse it.",
            "Rate is events per day divided by 86,400.",
            "Storage multiplies events per day by size, copies and days, then converts bytes to GB with 10⁹.",
        ],
        brute_force="There is no asymptotic concern; the 'brute force' is doing each formula separately and "
                    "re-deriving events per day three times, which is where arithmetic slips come from.",
        approach="Three lines of arithmetic.\n\n**Dry run** example: per day = 10⁷ × 20 = 2×10⁸; ÷ 86,400 ≈ 2,315 QPS; "
                 "× 3 ≈ 6,944 peak; storage = 2×10⁸ × 500 × 3 × 365 = 1.095×10¹⁴ bytes = 109,500 GB ≈ 110 TB.",
        complexity="O(1).",
        pitfalls="- In conversation, rounding 86,400 to 10⁵ is fine; the judge here wants the exact figure.\n"
                 "- Mixing GiB (2³⁰) with GB (10⁹).\n- Forgetting replication, which triples the bill.\n"
                 "- Adding the peak factor instead of multiplying.",
        follow_up="Add index overhead and compression ratio, and express the result in the largest sensible unit.",
    ),
),
]
