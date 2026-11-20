import random as _r

_r.seed(11)
_lat = [int(_r.lognormvariate(3.5, 0.6)) for _ in range(20000)]
_arrivals = []
_t = 0
for _i in range(3000):
    _t += int(_r.expovariate(1 / 4.0))
    _arrivals.append([_t, "r%d" % _i])
_ref = [_r.gauss(0, 1) for _ in range(3000)]
_shift = [_r.gauss(0.3, 1.2) for _ in range(3000)]
_ks_a = [_r.randint(0, 50) for _ in range(4000)]
_ks_b = [_r.randint(5, 55) for _ in range(3500)]
_scores = [round(abs(_r.gauss(0.08, 0.08)), 3) for _ in range(1000)]

PROBLEMS = [
dict(
    id="mlops-dynamic-batching",
    title="Dynamic Batching Scheduler",
    difficulty="Medium",
    pattern="Model Serving",
    entry="dynamicBatches",
    description=r"""
Model servers (Triton, TorchServe, BentoML, Ray Serve) improve GPU throughput with **dynamic batching**:
requests are queued and dispatched together either when the batch is full or when the oldest request has
waited long enough — "a bus that leaves when full or on schedule" (Huyen, *AI Engineering*, ch. 9).

`dynamicBatches(requests, max_batch_size, max_wait_ms)`:

- `requests`: list of `[arrival_ms, request_id]` sorted by arrival (ties keep list order).
- A batch **opens** when a request arrives and no batch is open; let its arrival time be `t0`.
- Subsequent requests with `arrival <= t0 + max_wait_ms` join the open batch.
- The batch is **dispatched**:
  - at the arrival time of the request that makes it reach `max_batch_size`, or
  - otherwise at `t0 + max_wait_ms` (the timeout).
- Assume dispatch is instantaneous and the server is always free.

Return `[[dispatch_ms, [ids...]], ...]` in dispatch order.

**Example:** `requests = [[0,"a"],[3,"b"],[4,"c"],[20,"d"]]`, `max_batch_size = 2`, `max_wait_ms = 10`
→ `[[3, ["a","b"]], [14, ["c"]], [30, ["d"]]]`
""",
    starter='''def dynamicBatches(requests, max_batch_size, max_wait_ms):
    pass
''',
    solution='''def dynamicBatches(requests, max_batch_size, max_wait_ms):
    out = []
    batch, t0 = [], None
    for t, rid in requests:
        if batch and t > t0 + max_wait_ms:
            out.append([t0 + max_wait_ms, batch])
            batch, t0 = [], None
        if not batch:
            t0 = t
        batch.append(rid)
        if len(batch) == max_batch_size:
            out.append([t, batch])
            batch, t0 = [], None
    if batch:
        out.append([t0 + max_wait_ms, batch])
    return out
''',
    tests=[
        [[[0, "a"], [3, "b"], [4, "c"], [20, "d"]], 2, 10],
        [[], 4, 10],
        [[[5, "x"]], 8, 50],
        [[[0, "a"], [0, "b"], [0, "c"]], 1, 10],
        [[[0, "a"], [10, "b"], [11, "c"]], 4, 10],
        [[[0, "a"], [1, "b"], [2, "c"], [3, "d"], [4, "e"]], 3, 100],
        [[[0, "a"], [5, "b"], [5, "c"], [5, "d"]], 2, 0],
        [[[0, "a"], [100, "b"], [200, "c"]], 32, 50],
        [[[i, "q%d" % i] for i in range(0, 64)], 8, 1000],
        [_arrivals, 16, 20],
        [_arrivals, 4, 5],
    ],
    examples=2,
    wrong_solutions=[
        '''def dynamicBatches(requests, max_batch_size, max_wait_ms):
    out = []
    for i in range(0, len(requests), max_batch_size):
        chunk = requests[i:i + max_batch_size]
        out.append([chunk[-1][0], [r for _, r in chunk]])
    return out
''',
        '''def dynamicBatches(requests, max_batch_size, max_wait_ms):
    out = []
    batch, t0 = [], None
    for t, rid in requests:
        if batch and t >= t0 + max_wait_ms:
            out.append([t0 + max_wait_ms, batch]); batch = []
        if not batch: t0 = t
        batch.append(rid)
        if len(batch) == max_batch_size:
            out.append([t, batch]); batch = []
    if batch: out.append([t0 + max_wait_ms, batch])
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Model servers, batching, autoscaling and caching*.",
        intuition="Keep one open batch with a deadline `t0 + max_wait`. Each new arrival either misses the deadline (flush the old batch first, at its deadline) or joins it; joining may fill the batch, which flushes it immediately.",
        hints=["Before adding a request, check whether the open batch's deadline has already passed (`t > t0 + max_wait`).",
               "A request arriving *exactly* at the deadline still joins (`<=`).", "Don't forget to flush the last open batch at its deadline."],
        brute_force="Chunking every `max_batch_size` requests ignores time and can make the first request wait arbitrarily long — that's *static* batching.",
        approach="Single pass, state = (batch list, t0).\n\nDry run of the example: a opens at 0 (deadline 10); b at 3 joins → full → dispatch at 3. c opens at 4 (deadline 14); d at 20 > 14 → flush [c] at 14; d opens at 20 → flushed at end at 30.",
        complexity="O(n) time, O(max_batch_size) extra space.",
        pitfalls="- `>=` vs `>` at the deadline boundary.\n- Recording dispatch time as the *next* arrival instead of the deadline.\n- `max_wait_ms = 0` means only simultaneous arrivals share a batch.",
        follow_up="Continuous (in-flight) batching for LLMs lets finished sequences leave and new ones join mid-batch; Triton exposes `max_queue_delay_microseconds` and `preferred_batch_size`.",
    ),
),
dict(
    id="mlops-rolling-p95",
    title="Rolling p95 Latency",
    difficulty="Medium",
    pattern="Monitoring & Drift",
    entry="rollingP95",
    description=r"""
Averages hide tail latency — one 3-second request among ten 100 ms requests makes the mean 390 ms while
p50 stays at 100 ms (Huyen, ch. 9). SLOs are therefore written on **percentiles**. Compute a sliding-window p95.

`rollingP95(latencies, window)`: for every index `i >= window - 1`, take the last `window` values
`latencies[i-window+1 .. i]` and return their p95 using the **nearest-rank** method:

- sort the window ascending, `rank = ceil(95 * window / 100)` computed with integers as `(95 * window + 99) // 100`,
- p95 = `sorted_window[rank - 1]`.

Return the list of p95 values (length `len(latencies) - window + 1`, or `[]` if there are fewer values than `window`).

Inputs can be large (20,000 values, window 500), so re-sorting every window is too slow.

**Example:** `rollingP95([10, 20, 30, 40], 2)` → `[20, 30, 40]`
""",
    starter='''import bisect

def rollingP95(latencies, window):
    pass
''',
    solution='''import bisect

def rollingP95(latencies, window):
    if window <= 0 or len(latencies) < window:
        return []
    rank = (95 * window + 99) // 100
    win = sorted(latencies[:window])
    out = [win[rank - 1]]
    for i in range(window, len(latencies)):
        old = latencies[i - window]
        del win[bisect.bisect_left(win, old)]
        bisect.insort(win, latencies[i])
        out.append(win[rank - 1])
    return out
''',
    tests=[
        [[10, 20, 30, 40], 2],
        [[5, 1, 4], 5],
        [[7], 1],
        [list(range(1, 21)), 20],
        [list(range(20, 0, -1)) + [1000], 20],
        [[100, 102, 100, 100, 99, 104, 110, 90, 3000, 95], 10],
        [[5, 5, 5, 5, 9, 5, 5], 3],
        [[3, 1, 2] * 40, 7],
        [_lat[:2000], 100],
        [_lat, 500],
    ],
    examples=2,
    wrong_solutions=[
        '''def rollingP95(latencies, window):
    out = []
    for i in range(window - 1, len(latencies)):
        w = sorted(latencies[i - window + 1:i + 1])
        out.append(w[int(0.95 * window)] if int(0.95 * window) < window else w[-1])
    return out
''',
        '''def rollingP95(latencies, window):
    out = []
    for i in range(window - 1, len(latencies)):
        w = latencies[i - window + 1:i + 1]
        out.append(sum(w) / len(w))
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Metrics, logs, traces and Prometheus*; `bisect`.",
        intuition="Maintain the window as a sorted list. Sliding by one means deleting one known value and inserting one new value — both O(log w) to locate, O(w) to shift, far cheaper than an O(w log w) sort.",
        hints=["Compute `rank` once with integer arithmetic.", "`bisect_left` finds an occurrence of the outgoing value even with duplicates.", "`bisect.insort` inserts the incoming value."],
        brute_force="Sort each window: O(n · w log w) ≈ 20,000 × 500 × 9 operations — seconds in the browser.",
        approach="Seed with sorted first window; for each new value remove `latencies[i-window]` and insort `latencies[i]`, then read index `rank-1`.",
        complexity="O(n · w) worst case due to list shifting (memmove is very fast), O(w) space. A two-heap or order-statistic tree gives O(n log w).",
        pitfalls="- `int(0.95*w)` is an off-by-one versus nearest-rank (for w=20 it picks the max).\n- Float rounding in `ceil(0.95*w)` — use integers.\n- Prometheus `histogram_quantile` interpolates within buckets, so its p95 will differ from an exact one.",
        follow_up="Streaming sketches (t-digest, HDRHistogram, DDSketch) estimate quantiles in constant memory and can be merged across pods.",
    ),
),
dict(
    id="mlops-canary-decision",
    title="Canary Rollout Controller",
    difficulty="Medium",
    pattern="Deployment Strategies",
    entry="canaryDecision",
    description=r"""
A **canary** release sends a growing slice of traffic to the new model (e.g. 5% → 25% → 50% → 100%),
comparing it to the baseline at every step (this is what Argo Rollouts / Flagger automate).

`canaryDecision(schedule, observations, max_err_increase, max_p95_ratio, min_requests)`:

- `schedule`: increasing list of traffic weights in percent, ending in 100.
- `observations[i]`: stats collected while the canary held weight `schedule[i]`:
  `{"base_req", "base_err", "can_req", "can_err", "base_p95", "can_p95"}` (counts and ms).
  There may be **fewer** observations than steps (rollout in progress).
- Process steps in order. At step `i`:
  1. If `can_req < min_requests` → return `["HOLD", schedule[i]]` (not enough evidence yet).
  2. Error rate = `err / req` (0 if `req == 0`). If `can_rate - base_rate > max_err_increase`
     **or** `can_p95 > base_p95 * max_p95_ratio` → return `["ROLLBACK", 0]`.
  3. Otherwise the step passes.
- If every step in `schedule` passed → `["PROMOTE", 100]`.
- If all given observations passed but steps remain → `["CONTINUE", schedule[len(observations)]]`.

**Example:** schedule `[10, 50, 100]`, one healthy observation → `["CONTINUE", 50]`.
""",
    starter='''def canaryDecision(schedule, observations, max_err_increase, max_p95_ratio, min_requests):
    pass
''',
    solution='''def canaryDecision(schedule, observations, max_err_increase, max_p95_ratio, min_requests):
    def rate(e, n):
        return e / n if n else 0.0
    for i, w in enumerate(schedule):
        if i >= len(observations):
            return ["CONTINUE", w]
        o = observations[i]
        if o["can_req"] < min_requests:
            return ["HOLD", w]
        if rate(o["can_err"], o["can_req"]) - rate(o["base_err"], o["base_req"]) > max_err_increase:
            return ["ROLLBACK", 0]
        if o["can_p95"] > o["base_p95"] * max_p95_ratio:
            return ["ROLLBACK", 0]
    return ["PROMOTE", 100]
''',
    tests=[
        [[10, 50, 100], [{"base_req": 9000, "base_err": 9, "can_req": 1000, "can_err": 1, "base_p95": 120, "can_p95": 125}], 0.005, 1.2, 500],
        [[10, 50, 100], [], 0.005, 1.2, 500],
        [[10, 50, 100], [{"base_req": 9000, "base_err": 9, "can_req": 300, "can_err": 0, "base_p95": 120, "can_p95": 100}], 0.005, 1.2, 500],
        [[10, 50, 100], [{"base_req": 9000, "base_err": 9, "can_req": 1000, "can_err": 30, "base_p95": 120, "can_p95": 100}], 0.005, 1.2, 500],
        [[10, 50, 100], [{"base_req": 9000, "base_err": 9, "can_req": 1000, "can_err": 1, "base_p95": 100, "can_p95": 121}], 0.005, 1.2, 500],
        [[10, 50, 100], [{"base_req": 9000, "base_err": 9, "can_req": 1000, "can_err": 1, "base_p95": 100, "can_p95": 120}], 0.005, 1.2, 500],
        [[10, 100], [{"base_req": 900, "base_err": 0, "can_req": 100, "can_err": 0, "base_p95": 50, "can_p95": 50},
                     {"base_req": 0, "base_err": 0, "can_req": 1000, "can_err": 2, "base_p95": 50, "can_p95": 55}], 0.005, 1.2, 100],
        [[10, 100], [{"base_req": 900, "base_err": 0, "can_req": 100, "can_err": 0, "base_p95": 50, "can_p95": 50},
                     {"base_req": 0, "base_err": 0, "can_req": 1000, "can_err": 6, "base_p95": 50, "can_p95": 55}], 0.005, 1.2, 100],
        [[5, 25, 50, 100], [{"base_req": 9500, "base_err": 95, "can_req": 500, "can_err": 7, "base_p95": 80, "can_p95": 82},
                            {"base_req": 7500, "base_err": 75, "can_req": 2500, "can_err": 20, "base_p95": 80, "can_p95": 85},
                            {"base_req": 5000, "base_err": 50, "can_req": 5000, "can_err": 40, "base_p95": 80, "can_p95": 90},
                            {"base_req": 0, "base_err": 0, "can_req": 10000, "can_err": 90, "base_p95": 80, "can_p95": 92}], 0.002, 1.25, 400],
        [[5, 25, 50, 100], [{"base_req": 9500, "base_err": 95, "can_req": 500, "can_err": 7, "base_p95": 80, "can_p95": 82},
                            {"base_req": 7500, "base_err": 75, "can_req": 100, "can_err": 0, "base_p95": 80, "can_p95": 85}], 0.002, 1.25, 400],
        [[100], [{"base_req": 0, "base_err": 0, "can_req": 0, "can_err": 0, "base_p95": 0, "can_p95": 0}], 0.01, 1.1, 0],
    ],
    examples=2,
    wrong_solutions=[
        '''def canaryDecision(schedule, observations, max_err_increase, max_p95_ratio, min_requests):
    for i, o in enumerate(observations):
        if o["can_err"] / max(o["can_req"], 1) > max_err_increase:
            return ["ROLLBACK", 0]
    if len(observations) >= len(schedule):
        return ["PROMOTE", 100]
    return ["CONTINUE", schedule[len(observations)]]
''',
    ],
    guide=dict(
        prereqs="Lesson *Deployment strategies: canary, shadow, blue-green and A/B*.",
        intuition="A canary is a sequence of guarded gates. Each gate asks: do we have enough evidence? Is the canary *relatively* worse than the baseline running at the same time? Only then advance.",
        hints=["Compare the canary to the **baseline** (relative), not to an absolute threshold — both see the same traffic mix.",
               "Check the sample-size gate first, otherwise noise from 20 requests can trigger a rollback.",
               "If you run out of observations, report the weight of the next un-observed step."],
        brute_force="N/A — direct simulation.",
        approach="Loop over schedule; missing observation → CONTINUE at that weight; then HOLD gate; then error-rate and latency gates; after the loop PROMOTE.",
        complexity="O(len(schedule)).",
        pitfalls="- Division by zero when the baseline has 0 requests at 100%.\n- Using `>=` for the latency ratio (equal is allowed).\n- Comparing absolute error rates: a 1% canary error rate is fine if the baseline is also 1%.",
        follow_up="Replace the fixed thresholds with a statistical test (see `mlops-ab-ztest`) and add a bake time per step. Flagger and Argo Rollouts express these as `analysis` templates querying Prometheus.",
    ),
),
dict(
    id="mlops-ab-ztest",
    title="A/B Test: Two-Proportion z-Test",
    difficulty="Medium",
    pattern="Deployment Strategies",
    entry="abTest",
    compare="float",
    tolerance=1e-6,
    description=r"""
You ran an online A/B test of two recommendation models and measured conversions. Decide whether the
difference is statistically significant with a **pooled two-proportion z-test** (two-sided).

`abTest(conv_a, n_a, conv_b, n_b, alpha)`:

$$\hat p_a = \frac{conv_a}{n_a},\quad \hat p_b = \frac{conv_b}{n_b},\quad
\hat p = \frac{conv_a + conv_b}{n_a + n_b},\quad
SE = \sqrt{\hat p (1-\hat p)\left(\frac1{n_a}+\frac1{n_b}\right)},\quad z = \frac{\hat p_b - \hat p_a}{SE}$$

Two-sided p-value: `p = 2 * (1 - Phi(|z|))` with `Phi(x) = 0.5 * (1 + erf(x / sqrt(2)))`.

Return `[z, p, winner]` where `winner` is `"B"` if `p < alpha` and `z > 0`, `"A"` if `p < alpha` and
`z < 0`, else `"none"`.

Degenerate cases: if `n_a == 0`, `n_b == 0`, or `SE == 0`, return `[0.0, 1.0, "none"]`.

**Example:** `abTest(200, 10000, 260, 10000, 0.05)` → `z ≈ 2.8284`, `p ≈ 0.00468`, `"B"`.
""",
    starter='''import math

def abTest(conv_a, n_a, conv_b, n_b, alpha):
    pass
''',
    solution='''import math

def abTest(conv_a, n_a, conv_b, n_b, alpha):
    if n_a == 0 or n_b == 0:
        return [0.0, 1.0, "none"]
    pa, pb = conv_a / n_a, conv_b / n_b
    p = (conv_a + conv_b) / (n_a + n_b)
    se = math.sqrt(p * (1 - p) * (1 / n_a + 1 / n_b))
    if se == 0:
        return [0.0, 1.0, "none"]
    z = (pb - pa) / se
    pv = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    w = "none"
    if pv < alpha:
        w = "B" if z > 0 else "A"
    return [z, pv, w]
''',
    tests=[
        [200, 10000, 260, 10000, 0.05],
        [200, 10000, 210, 10000, 0.05],
        [300, 10000, 200, 10000, 0.05],
        [0, 0, 5, 100, 0.05],
        [0, 100, 0, 100, 0.05],
        [100, 100, 100, 100, 0.05],
        [50, 1000, 70, 1000, 0.05],
        [50, 1000, 70, 1000, 0.10],
        [1200, 50000, 1300, 50000, 0.01],
        [12, 400, 30, 600, 0.05],
        [5000, 100000, 5150, 100000, 0.05],
    ],
    examples=2,
    wrong_solutions=[
        '''import math
def abTest(conv_a, n_a, conv_b, n_b, alpha):
    if n_a == 0 or n_b == 0: return [0.0, 1.0, "none"]
    pa, pb = conv_a / n_a, conv_b / n_b
    se = math.sqrt(pa * (1 - pa) / n_a + pb * (1 - pb) / n_b)
    if se == 0: return [0.0, 1.0, "none"]
    z = (pb - pa) / se
    pv = 1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2)))
    w = "none"
    if pv < alpha: w = "B" if z > 0 else "A"
    return [z, pv, w]
''',
    ],
    guide=dict(
        prereqs="Lesson *Deployment strategies*; basic hypothesis testing.",
        intuition="Under the null hypothesis both variants share one conversion rate, so estimate it from the pooled data; z measures how many standard errors apart the two observed rates are.",
        hints=["Pool the conversions for the standard error.", "Two-sided: double the upper-tail probability.", "`math.erf` gives you the normal CDF without scipy."],
        brute_force="Eyeballing '2.6% beats 2.0%' — without a test you can't tell signal from noise at small n.",
        approach="Compute rates → pooled rate → SE → z → p-value → decision. Example: pa=0.02, pb=0.026, p̂=0.023, SE≈0.00212, z≈2.83, p≈0.0047 < 0.05 → B.",
        complexity="O(1).",
        pitfalls="- Unpooled SE (valid for confidence intervals, but the classic test pools).\n- One-sided p-value.\n- **Peeking**: checking every hour and stopping at the first p<0.05 inflates false positives — fix the sample size up front or use sequential tests.",
        follow_up="Compute the sample size needed to detect a 0.3-point lift with 80% power; consider CUPED variance reduction or Bayesian A/B testing.",
    ),
),
dict(
    id="mlops-psi",
    title="Population Stability Index",
    difficulty="Easy",
    pattern="Monitoring & Drift",
    entry="psi",
    compare="float",
    tolerance=1e-6,
    description=r"""
The **Population Stability Index** compares the distribution of a feature (or of model scores) in production
to a reference sample, typically training data:

$$\mathrm{PSI} = \sum_{i=1}^{B} (a_i - e_i)\,\ln\frac{a_i}{e_i}$$

where $e_i$ and $a_i$ are the fractions of the expected (reference) and actual (production) samples in bin $i$.
Rule of thumb: < 0.1 stable, 0.1–0.25 moderate shift, > 0.25 major shift.

`psi(expected, actual, bins)`:

- Bin edges are **equal-width** over the expected sample: `lo = min(expected)`, `hi = max(expected)`
  (guaranteed `hi > lo`).
- Bin index of a value `x`: `floor((x - lo) / (hi - lo) * bins)`, clipped to `[0, bins - 1]`
  (so values outside the reference range fall in the first/last bin, and `x == hi` lands in the last bin).
- Fractions = count / sample size; replace any fraction of 0 by `1e-4` (avoids `log(0)`).
- Return the PSI as a float.

**Example:** `psi([1,2,3,4], [1,2,3,4], 2)` → `0.0`
""",
    starter='''import math

def psi(expected, actual, bins):
    pass
''',
    solution='''import math

def psi(expected, actual, bins):
    lo, hi = min(expected), max(expected)
    def frac(xs):
        c = [0] * bins
        for x in xs:
            k = math.floor((x - lo) / (hi - lo) * bins)
            c[min(bins - 1, max(0, k))] += 1
        return [max(v / len(xs), 1e-4) for v in c]
    e, a = frac(expected), frac(actual)
    return sum((ai - ei) * math.log(ai / ei) for ai, ei in zip(a, e))
''',
    tests=[
        [[1, 2, 3, 4], [1, 2, 3, 4], 2],
        [[1, 2, 3, 4], [4, 4, 4, 4], 2],
        [[0, 10], [5, 5, 5, 5], 4],
        [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [-5, 20, 3, 3], 5],
        [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 10],
        [[0.1, 0.2, 0.3, 0.9], [0.15, 0.25, 0.85, 0.95], 3],
        [_ref, _ref[:1500], 10],
        [_ref, _shift, 10],
        [_ref, [x + 1 for x in _ref], 20],
        [list(range(100)), list(range(50, 150)), 10],
    ],
    examples=2,
    wrong_solutions=[
        '''import math
def psi(expected, actual, bins):
    lo, hi = min(expected), max(expected)
    def frac(xs):
        c = [0] * bins
        for x in xs:
            k = math.floor((x - lo) / (hi - lo) * bins)
            if 0 <= k < bins: c[k] += 1
        return [max(v / len(xs), 1e-4) for v in c]
    e, a = frac(expected), frac(actual)
    return sum((ai - ei) * math.log(ai / ei) for ai, ei in zip(a, e))
''',
        '''import math
def psi(expected, actual, bins):
    lo, hi = min(expected), max(expected)
    def frac(xs):
        c = [0] * bins
        for x in xs:
            c[min(bins - 1, max(0, math.floor((x - lo) / (hi - lo) * bins)))] += 1
        return [max(v / len(xs), 1e-4) for v in c]
    e, a = frac(expected), frac(actual)
    return sum(ai * math.log(ai / ei) for ai, ei in zip(a, e))
''',
    ],
    guide=dict(
        prereqs="Lesson *Data drift, concept drift and statistical tests*.",
        intuition="PSI is a symmetrised KL divergence over binned distributions: each bin contributes (difference in share) × (log ratio of shares), both of which have the same sign, so every term is ≥ 0.",
        hints=["Bin both samples with the **same** edges (from the reference).", "Clip out-of-range values into the edge bins — dropping them hides exactly the drift you want to see.", "Floor zero fractions at 1e-4 before taking logs."],
        brute_force="Already linear. The common bug is conceptual (different bins per sample, or dropping outliers).",
        approach="Compute lo/hi → histogram helper with clipping → fractions with epsilon → sum the PSI terms.",
        complexity="O(N + M + B).",
        pitfalls="- `x == hi` must go to the last bin (clip handles it).\n- Using quantile bins vs equal-width bins changes the number — always document which.\n- Writing `a·ln(a/e)` (that's KL, not PSI).",
        follow_up="Evidently and NannyML compute PSI, KS, Wasserstein and Jensen–Shannon per feature and pick defaults by data type and sample size.",
    ),
),
dict(
    id="mlops-ks-statistic",
    title="Two-Sample Kolmogorov–Smirnov Statistic",
    difficulty="Medium",
    pattern="Monitoring & Drift",
    entry="ksStatistic",
    compare="float",
    tolerance=1e-9,
    description=r"""
The two-sample **KS statistic** is the largest vertical gap between two empirical CDFs:

$$D = \sup_x \left| F_a(x) - F_b(x) \right|, \qquad F_a(x) = \frac{\#\{a_i \le x\}}{|a|}$$

It is the default drift test for numeric features in tools like Evidently when samples are small.

`ksStatistic(a, b)` takes two non-empty lists of numbers (they may contain **ties** and shared values) and
returns `D`. Aim for O((n + m) log(n + m)).

**Example:** `ksStatistic([1, 2, 3], [4, 5, 6])` → `1.0`; `ksStatistic([1, 2], [1, 2])` → `0.0`
""",
    starter='''def ksStatistic(a, b):
    pass
''',
    solution='''def ksStatistic(a, b):
    a, b = sorted(a), sorted(b)
    n, m = len(a), len(b)
    i = j = 0
    d = 0.0
    while i < n or j < m:
        if j >= m or (i < n and a[i] <= b[j]):
            x = a[i]
        else:
            x = b[j]
        while i < n and a[i] == x:
            i += 1
        while j < m and b[j] == x:
            j += 1
        d = max(d, abs(i / n - j / m))
    return d
''',
    tests=[
        [[1, 2, 3], [4, 5, 6]],
        [[1, 2], [1, 2]],
        [[1, 1, 1, 2], [1, 2, 2, 2]],
        [[5], [5]],
        [[5], [6]],
        [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [3, 4, 5]],
        [[0.5, 0.5, 0.5], [0.1, 0.5, 0.9]],
        [[-3, -1, 0, 2], [-2, -1, 1, 2, 3, 4]],
        [_ref[:1000], _shift[:1000]],
        [_ks_a, _ks_b],
        [_ref, _ref[::-1]],
    ],
    examples=2,
    wrong_solutions=[
        '''def ksStatistic(a, b):
    a, b = sorted(a), sorted(b)
    n, m = len(a), len(b)
    i = j = 0; d = 0.0
    while i < n and j < m:
        if a[i] <= b[j]: i += 1
        else: j += 1
        d = max(d, abs(i / n - j / m))
    return d
''',
    ],
    guide=dict(
        prereqs="Lesson *Data drift, concept drift and statistical tests*; merging sorted lists.",
        intuition="Both ECDFs are step functions that only change at sample values. Sweep the merged sorted values left to right; at each distinct value, advance *both* pointers past all copies of it, then measure the gap.",
        hints=["Sort both samples.", "Process one **distinct** value at a time, consuming ties in both lists before measuring.",
               "The gap only needs checking right after each distinct value."],
        brute_force="For every candidate x in a ∪ b, count ≤ x in both lists: O((n+m)²).",
        approach="Two pointers over sorted arrays. Ties matter: for a=[1,2], b=[1,2], advancing only `i` past 1 would momentarily report a gap of 0.5 that does not exist in the true ECDFs.",
        complexity="O((n+m) log(n+m)) for sorting, O(n+m) sweep.",
        pitfalls="- Tie handling (the wrong solution reports phantom gaps).\n- Stopping when one list is exhausted — the gap can still grow? (It can't exceed values already seen once one side is at 1, but finishing the loop is simplest).\n- Large samples make *any* tiny shift 'significant' — with 1M rows, look at D itself (effect size), not just the p-value.",
        follow_up="Compute the asymptotic p-value: with $n_e = nm/(n+m)$, $p \\approx Q_{KS}(\\sqrt{n_e} D)$. `scipy.stats.ks_2samp` does this for you.",
    ),
),
dict(
    id="mlops-drift-alerts",
    title="Drift Alerts with Patience",
    difficulty="Easy",
    pattern="Monitoring & Drift",
    entry="driftAlerts",
    description=r"""
Paging an on-call engineer because a single noisy window crossed a threshold is the fastest way to get alerts
ignored. Like Prometheus' `for:` clause, require the condition to hold for several consecutive windows.

`driftAlerts(scores, threshold, patience)`:

- `scores[t]` is the drift score (e.g. PSI) for window `t`.
- A window **breaches** if `scores[t] >= threshold`.
- Fire an alert at window `t` when it completes a run of exactly `patience` consecutive breaches.
- After firing, the alert stays active (no new alerts) until a window **does not** breach; then it re-arms.

Return the list of window indices at which alerts fire.

**Example:** `driftAlerts([0.3, 0.3, 0.3, 0.3, 0.0, 0.3, 0.3], 0.25, 2)` → `[1, 6]`
""",
    starter='''def driftAlerts(scores, threshold, patience):
    pass
''',
    solution='''def driftAlerts(scores, threshold, patience):
    out, run = [], 0
    for t, s in enumerate(scores):
        if s >= threshold:
            run += 1
            if run == patience:
                out.append(t)
        else:
            run = 0
    return out
''',
    tests=[
        [[0.3, 0.3, 0.3, 0.3, 0.0, 0.3, 0.3], 0.25, 2],
        [[], 0.25, 3],
        [[0.1, 0.2, 0.24], 0.25, 1],
        [[0.25], 0.25, 1],
        [[0.3, 0.3, 0.1, 0.3, 0.3, 0.3], 0.25, 3],
        [[0.5, 0.5, 0.5, 0.5, 0.5, 0.5], 0.25, 2],
        [[0.5, 0.1, 0.5, 0.1, 0.5], 0.25, 1],
        [[0.5, 0.1, 0.5, 0.1, 0.5], 0.25, 2],
        [_scores, 0.15, 2],
        [_scores, 0.2, 1],
    ],
    examples=2,
    wrong_solutions=[
        '''def driftAlerts(scores, threshold, patience):
    out, run = [], 0
    for t, s in enumerate(scores):
        run = run + 1 if s >= threshold else 0
        if run >= patience: out.append(t)
    return out
''',
        '''def driftAlerts(scores, threshold, patience):
    out, run = [], 0
    for t, s in enumerate(scores):
        run = run + 1 if s > threshold else 0
        if run == patience: out.append(t)
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Alerting, feedback loops and retraining triggers*.",
        intuition="Track the length of the current breach streak. Fire exactly when it *reaches* `patience`; longer streaks don't re-fire, and any non-breach resets the streak (re-arming the alert).",
        hints=["One counter is enough.", "`==` (not `>=`) prevents duplicate alerts during a long incident.", "Breach uses `>=`."],
        brute_force="Check every window of length `patience` — O(n·k) and easy to double-fire.",
        approach="Single pass with a run counter.",
        complexity="O(n) time, O(1) space.",
        pitfalls="- Re-firing every window during a long breach.\n- Strict `>` at the threshold.\n- Choosing `patience` too high: detection delay = patience × window length (that's your MTTD).",
        follow_up="Add hysteresis: require the score to fall below a lower *clear* threshold before re-arming, like Prometheus `keep_firing_for` or Grafana recovery thresholds.",
    ),
),
]
