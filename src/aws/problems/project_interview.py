PROBLEMS = [
dict(
    id="aws-az-failure-capacity",
    title="Capacity That Survives an AZ Failure",
    difficulty="Easy",
    pattern="High Availability",
    entry="azCapacity",
    description=r"""
An Auto Scaling group spreads identical instances evenly over `zones` Availability Zones (the same
number in each). You want **static stability**: if any one zone disappears, the instances that are
left must carry the peak load straight away, without waiting for new ones.

`azCapacity(peak_rps, rps_per_instance, zones, max_util_pct)`:

- `peak_rps`: requests per second at peak (integer, 0 or more).
- `rps_per_instance`: requests per second one instance handles when fully busy (integer, 1 or more).
- `zones`: number of Availability Zones in use (2 or more).
- `max_util_pct`: instances should run at no more than this percentage of full capacity
  (integer 1 to 100), so one instance may be given at most `rps_per_instance * max_util_pct / 100`
  requests per second.

Return `[per_zone, total]`: the smallest number of instances per zone, and the fleet total, such that
the instances in any `zones - 1` zones can serve `peak_rps` within the utilisation limit. There is
always at least one instance per zone.

**Example:** `azCapacity(900, 150, 2, 100)` → `[6, 12]` (six instances serve the peak, and each zone
must hold all six).

**Example:** `azCapacity(900, 150, 3, 100)` → `[3, 9]` (two surviving zones hold six between them).
""",
    starter='''def azCapacity(peak_rps, rps_per_instance, zones, max_util_pct):
    pass
''',
    solution='''def azCapacity(peak_rps, rps_per_instance, zones, max_util_pct):
    usable = rps_per_instance * max_util_pct            # capacity of one instance, in hundredths
    needed = -(-peak_rps * 100 // usable)                # ceiling division, integers only
    per_zone = max(1, -(-needed // (zones - 1)))
    return [per_zone, per_zone * zones]
''',
    tests=[
        [900, 150, 2, 100],
        [900, 150, 3, 100],
        [900, 150, 3, 60],
        [0, 100, 2, 50],
        [1, 100, 4, 100],
        [1000, 100, 2, 70],
        [1000, 100, 3, 70],
        [50, 50, 2, 100],
        [51, 50, 2, 100],
        [700, 100, 4, 100],
        [12345, 37, 5, 65],
        [10 ** 6, 250, 3, 50],
        [29, 10, 3, 100],
    ],
    examples=2,
    wrong_solutions=[
        '''def azCapacity(peak_rps, rps_per_instance, zones, max_util_pct):
    usable = rps_per_instance * max_util_pct
    needed = -(-peak_rps * 100 // usable)
    per_zone = max(1, -(-needed // zones))
    return [per_zone, per_zone * zones]
''',
        '''def azCapacity(peak_rps, rps_per_instance, zones, max_util_pct):
    needed = -(-peak_rps // rps_per_instance)
    per_zone = max(1, -(-needed // (zones - 1)))
    return [per_zone, per_zone * zones]
''',
        '''def azCapacity(peak_rps, rps_per_instance, zones, max_util_pct):
    usable = rps_per_instance * max_util_pct
    needed = peak_rps * 100 // usable
    per_zone = max(1, needed // (zones - 1))
    return [per_zone, per_zone * zones]
''',
    ],
    guide=dict(
        prereqs="Project part 2 (static stability) and the Auto Scaling lesson. Ceiling division.",
        intuition="Work out how many instances the peak needs at the allowed utilisation. Those instances must all fit in the zones that remain after one is lost, so divide by `zones - 1`, not by `zones`.",
        hints=["How many instances serve the peak if each may only be loaded to `max_util_pct`?",
               "After a zone fails, `zones - 1` zones are left. They must hold that many instances between them.",
               "Round up twice: once for instances needed, once for instances per zone. `-(-a // b)` is ceiling division with integers."],
        brute_force="Try per_zone = 1, 2, 3, ... and stop at the first value where `per_zone * (zones - 1) * usable capacity >= peak`. Correct but linear in the answer.",
        approach="Dry run `azCapacity(900, 150, 3, 60)`: one instance may take 150 x 0.60 = 90 requests/s, so the peak needs ceil(900 / 90) = 10 instances. Two zones survive, so each zone needs ceil(10 / 2) = 5, and the fleet is 15. Check: lose a zone, 10 instances x 90 = 900. Keep the arithmetic in integers (multiply the peak by 100 instead of dividing the capacity) to avoid floating-point surprises.",
        complexity="O(1) time and space.",
        pitfalls="Dividing by `zones` (sizes for normal running only); forgetting the utilisation limit; rounding down; returning 0 per zone when the peak is 0; using floats, where 0.7 x 100 is not exactly 70.",
        follow_up="With two zones the fleet is 100 % over-provisioned, with three zones 50 %, with four 33 %. That is the cost argument for using three zones.",
    ),
),
dict(
    id="aws-rolling-deploy-plan",
    title="Instance Refresh Plan",
    difficulty="Medium",
    pattern="Deployment",
    entry="rollingDeploy",
    description=r"""
An Auto Scaling group of `fleet` instances must be replaced with a new version by an **instance
refresh**. Two settings bound what may happen while it runs:

- `min_healthy_pct` (0 to 100): at least `ceil(fleet * min_healthy_pct / 100)` instances must be
  healthy and in service at every moment.
- `max_healthy_pct` (100 to 200): the group may temporarily grow to at most
  `floor(fleet * max_healthy_pct / 100)` instances.

So in one round the group may launch up to `surge = ceiling - fleet` extra new instances first, and
take up to `dip = fleet - floor_healthy` old instances out of service straight away.

Each round replaces `batch = min(old instances remaining, surge + dip)` instances like this:

1. Launch `min(batch, surge)` new instances; the total rises by that amount.
2. At the same time terminate the other `batch - min(batch, surge)` old instances; the healthy count
   dips by that amount until their replacements are ready.
3. When all new instances are healthy, terminate the old ones that step 1 kept; the group is back at
   `fleet`.

Return a list with one entry per round: `[batch, lowest_healthy, highest_total]`, where
`lowest_healthy` is the smallest number of healthy instances during the round and `highest_total`
the largest group size. If no instance can ever be replaced (`surge + dip == 0`), return `[]`.

**Example:** `rollingDeploy(4, 50, 100)` → `[[2, 2, 4], [2, 2, 4]]`

**Example:** `rollingDeploy(4, 100, 150)` → `[[2, 4, 6], [2, 4, 6]]` (launch before terminate: capacity never dips)
""",
    starter='''def rollingDeploy(fleet, min_healthy_pct, max_healthy_pct):
    pass
''',
    solution='''def rollingDeploy(fleet, min_healthy_pct, max_healthy_pct):
    floor_healthy = -(-fleet * min_healthy_pct // 100)     # ceiling
    ceiling = fleet * max_healthy_pct // 100               # floor
    surge = ceiling - fleet
    dip = fleet - floor_healthy
    if surge + dip == 0:
        return []
    rounds, remaining = [], fleet
    while remaining > 0:
        batch = min(remaining, surge + dip)
        launched_first = min(batch, surge)
        rounds.append([batch, fleet - (batch - launched_first), fleet + launched_first])
        remaining -= batch
    return rounds
''',
    tests=[
        [4, 50, 100],
        [4, 100, 150],
        [4, 100, 100],
        [10, 90, 100],
        [10, 90, 110],
        [5, 50, 100],
        [3, 100, 200],
        [7, 0, 100],
        [1, 100, 200],
        [1, 50, 100],
        [9, 67, 133],
        [100, 95, 105],
        [6, 34, 100],
    ],
    examples=2,
    wrong_solutions=[
        '''def rollingDeploy(fleet, min_healthy_pct, max_healthy_pct):
    floor_healthy = fleet * min_healthy_pct // 100
    ceiling = fleet * max_healthy_pct // 100
    surge = ceiling - fleet
    dip = fleet - floor_healthy
    if surge + dip == 0:
        return []
    rounds, remaining = [], fleet
    while remaining > 0:
        batch = min(remaining, surge + dip)
        launched_first = min(batch, surge)
        rounds.append([batch, fleet - (batch - launched_first), fleet + launched_first])
        remaining -= batch
    return rounds
''',
        '''def rollingDeploy(fleet, min_healthy_pct, max_healthy_pct):
    floor_healthy = -(-fleet * min_healthy_pct // 100)
    dip = fleet - floor_healthy
    if dip == 0:
        return []
    rounds, remaining = [], fleet
    while remaining > 0:
        batch = min(remaining, dip)
        rounds.append([batch, fleet - batch, fleet])
        remaining -= batch
    return rounds
''',
        '''def rollingDeploy(fleet, min_healthy_pct, max_healthy_pct):
    floor_healthy = -(-fleet * min_healthy_pct // 100)
    ceiling = fleet * max_healthy_pct // 100
    surge = ceiling - fleet
    dip = fleet - floor_healthy
    if surge + dip == 0:
        return []
    rounds, remaining = [], fleet
    while remaining > 0:
        batch = min(remaining, surge + dip)
        rounds.append([batch, fleet - dip, fleet + surge])
        remaining -= batch
    return rounds
''',
    ],
    guide=dict(
        prereqs="Project part 2 (shipping changes safely) and the Auto Scaling lesson on instance refresh.",
        intuition="Two budgets exist per round: how far the group may grow (surge) and how far healthy capacity may fall (dip). A round replaces as many instances as the two budgets together allow, spending the surge budget first because it costs no capacity.",
        hints=["Compute the healthy floor with a ceiling and the size limit with a floor; both must be integers.",
               "`surge = ceiling - fleet`, `dip = fleet - floor_healthy`, and a round handles at most `surge + dip` instances.",
               "In the last round the batch may be smaller than the budgets. Launch-first covers `min(batch, surge)` of it; only the rest causes a dip."],
        brute_force="Simulate instance by instance with explicit lists of old and new servers and their states. It gives the same numbers with far more code.",
        approach="Dry run `rollingDeploy(9, 67, 133)`: floor_healthy = ceil(6.03) = 7, ceiling = floor(11.97) = 11, so surge = 2 and dip = 2. Round 1: batch 4, launch 2 first (total 11), terminate 2 at once (healthy 7). Round 2: the same. Round 3: one instance left, launched first, so healthy stays 9 and total peaks at 10. Result `[[4,7,11],[4,7,11],[1,9,10]]`.",
        complexity="O(fleet / batch) rounds, O(1) work per round.",
        pitfalls="Rounding the healthy floor down (it would allow dipping below the minimum); ignoring the surge budget; reporting the full dip and surge in a final, smaller round; looping for ever when both budgets are zero.",
        follow_up="Setting the minimum to 100 % and the maximum above 100 % gives a deployment with no loss of capacity, at the price of briefly paying for extra instances.",
    ),
),
dict(
    id="aws-composite-availability",
    title="Availability of a Design",
    difficulty="Medium",
    pattern="System Design",
    entry="compositeAvailability",
    compare="float",
    description=r"""
In a design review you are asked how available the whole system is, given the availability of its parts.

A design is described recursively:

- a number such as `99.9` is one component that is available that percentage of the time;
- `["serial", [parts...]]` is a chain in which **every** part must work (a load balancer, then a
  server, then a database);
- `["parallel", [parts...]]` is a redundant group that works if **at least one** part works
  (two servers behind a load balancer). Failures are assumed independent.

`compositeAvailability(design)` returns `[availability_pct, downtime_minutes_per_year]` for the whole
design, where a year has 365 days (525,600 minutes). An empty serial group is 100 % available.

**Example:** `["serial", [99.9, 99.9]]` → `[99.8001, 1050.6744]`

**Example:** `["parallel", [99.0, 99.0]]` → `[99.99, 52.56]`

Answers are compared with a small tolerance.
""",
    starter='''def compositeAvailability(design):
    pass
''',
    solution='''def compositeAvailability(design):
    def avail(node):
        if isinstance(node, (int, float)):
            return node / 100.0
        kind, parts = node
        if kind == "serial":
            a = 1.0
            for p in parts:
                a *= avail(p)
            return a
        fail = 1.0
        for p in parts:
            fail *= 1.0 - avail(p)
        return 1.0 - fail
    a = avail(design)
    return [a * 100.0, (1.0 - a) * 525600.0]
''',
    tests=[
        [["serial", [99.9, 99.9]]],
        [["parallel", [99.0, 99.0]]],
        [99.95],
        [["serial", [99.99, ["parallel", [99.5, 99.5]], 99.95]]],
        [["serial", []]],
        [["parallel", [90]]],
        [["serial", [99.99, ["parallel", [["serial", [99.9, 99.5]], ["serial", [99.9, 99.5]]]], ["parallel", [99.95, 99.95]]]]],
        [100],
        [["serial", [99.9] * 10]],
        [["parallel", [95.0, 95.0, 95.0]]],
        [["serial", [["parallel", [99.0, 99.0]], ["parallel", [99.0, 99.0]], 99.99]]],
        [["parallel", [["serial", [99.0, 98.0]], 97.0]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def compositeAvailability(design):
    def avail(node):
        if isinstance(node, (int, float)):
            return node / 100.0
        kind, parts = node
        a = 1.0
        for p in parts:
            a *= avail(p)
        return a
    a = avail(design)
    return [a * 100.0, (1.0 - a) * 525600.0]
''',
        '''def compositeAvailability(design):
    def avail(node):
        if isinstance(node, (int, float)):
            return node / 100.0
        kind, parts = node
        vals = [avail(p) for p in parts] or [1.0]
        return min(vals) if kind == "serial" else max(vals)
    a = avail(design)
    return [a * 100.0, (1.0 - a) * 525600.0]
''',
    ],
    guide=dict(
        prereqs="The reliability lesson (availability in numbers) and the design-answers lesson. Recursion over nested lists.",
        intuition="A chain works only if every link works, so multiply availabilities. A redundant group fails only if every member fails, so multiply the failure probabilities and subtract from one.",
        hints=["Convert percentages to fractions first: 99.9 becomes 0.999.",
               "Serial: product of the parts. Parallel: one minus the product of (1 - part).",
               "A part may itself be a serial or parallel group, so write a helper that calls itself."],
        brute_force="Enumerate every combination of up/down for all leaf components and add the probabilities of the combinations in which the system works: O(2^n). The recursive formula is O(n).",
        approach="Dry run `['serial', [99.99, ['parallel', [99.5, 99.5]], 99.95]]`: the parallel pair fails with probability 0.005 x 0.005 = 0.000025, so it is 0.999975 available. The chain is 0.9999 x 0.999975 x 0.9995 = 0.999375..., about 99.9375 %, or roughly 328 minutes of downtime a year. Notice that the redundant pair is now better than either single component beside it.",
        complexity="O(n) time for n leaf components; recursion depth equals the nesting depth.",
        pitfalls="Multiplying availabilities for a parallel group (that describes a chain); taking min or max instead of combining probabilities; forgetting to convert between percent and fraction; treating an empty chain as 0 %.",
        follow_up="Real failures are not independent: two servers in the same Availability Zone share its fate. That is why redundancy must span zones, and why the result of this formula is an upper bound.",
    ),
),
dict(
    id="aws-spot-training-steps",
    title="Spot Training With Checkpoints",
    difficulty="Medium",
    pattern="Simulation",
    entry="spotTrainingSteps",
    description=r"""
A training job runs on Spot capacity, which can be taken away. Time is counted in equal **steps**
(say, quarter hours), and every step the job runs is billed.

`spotTrainingSteps(work_units, checkpoint_every, interruptions)`:

- The job is finished when its progress reaches `work_units`. Each billed step adds 1 to progress.
- If `checkpoint_every` is greater than 0, the job saves a checkpoint whenever its progress is
  `checkpoint_every` units beyond the last saved point. If it is 0, nothing is ever saved.
- `interruptions` is a list of distinct billed-step numbers (counting from 1). An interruption
  happens at the **end** of that step: progress falls back to the last saved point (0 if none).
  The job then continues with the next step.
- Within one step the order is: add progress; if the job is now finished, stop; save a checkpoint
  if one is due; then apply an interruption if there is one.

Return the total number of billed steps.

**Example:** `spotTrainingSteps(8, 0, [5])` → `13` (five steps lost, then eight more)

**Example:** `spotTrainingSteps(8, 2, [5])` → `9` (only the step since the checkpoint at 4 is lost)
""",
    starter='''def spotTrainingSteps(work_units, checkpoint_every, interruptions):
    pass
''',
    solution='''def spotTrainingSteps(work_units, checkpoint_every, interruptions):
    cut = set(interruptions)
    progress = saved = billed = 0
    while progress < work_units:
        billed += 1
        progress += 1
        if progress == work_units:
            break
        if checkpoint_every and progress - saved == checkpoint_every:
            saved = progress
        if billed in cut:
            progress = saved
    return billed
''',
    tests=[
        [8, 0, [5]],
        [8, 2, [5]],
        [8, 0, []],
        [8, 2, [4]],
        [8, 0, [8]],
        [8, 0, [7, 14, 21]],
        [10, 3, [2, 5, 9]],
        [0, 1, [1]],
        [1, 1, [1]],
        [500, 0, [100, 300, 600]],
        [1000, 10, list(range(7, 2000, 37))],
        [1000, 0, list(range(400, 4000, 400))],
        [12, 5, [3, 6, 9, 12, 15]],
    ],
    examples=2,
    wrong_solutions=[
        '''def spotTrainingSteps(work_units, checkpoint_every, interruptions):
    cut = set(interruptions)
    progress = billed = 0
    while progress < work_units:
        billed += 1
        progress += 1
        if progress == work_units:
            break
        if billed in cut:
            progress = 0
    return billed
''',
        '''def spotTrainingSteps(work_units, checkpoint_every, interruptions):
    cut = set(interruptions)
    progress = saved = billed = 0
    while progress < work_units:
        billed += 1
        progress += 1
        if progress == work_units:
            break
        if billed in cut:
            progress = saved
        if checkpoint_every and progress - saved == checkpoint_every:
            saved = progress
    return billed
''',
        '''def spotTrainingSteps(work_units, checkpoint_every, interruptions):
    return work_units + len(interruptions)
''',
    ],
    guide=dict(
        prereqs="The SageMaker lesson (managed Spot training and checkpoints). A simple loop with state.",
        intuition="Keep three counters: progress, the last saved progress, and billed steps. An interruption does not cost a fixed amount; it costs whatever was done since the last save, which is why frequent checkpoints matter.",
        hints=["Put the interruption steps in a set for constant-time lookup.",
               "Follow the stated order inside a step exactly: progress, finished?, checkpoint, interruption.",
               "After an interruption the distance to the next checkpoint is measured from the saved point, which is where progress now stands."],
        brute_force="The step-by-step simulation is already the direct method and is fast enough: the loop runs once per billed step.",
        approach="Dry run `spotTrainingSteps(10, 3, [2, 5, 9])`: step 1 p=1; step 2 p=2, interrupted, back to 0; steps 3-5 p=3, checkpoint at 3, the interruption at step 5 loses nothing; steps 6-8 p=6, checkpoint; step 9 p=7, interrupted, back to 6; steps 10-12 p=9, checkpoint; step 13 p=10, finished. Answer 13.",
        complexity="O(B) time where B is the number of billed steps, O(k) space for k interruptions.",
        pitfalls="Resetting to zero although a checkpoint exists; applying the interruption before the checkpoint due in the same step; charging an interruption that falls on the finishing step; assuming each interruption costs exactly one step.",
        follow_up="Without checkpoints a job longer than the typical gap between interruptions may never finish. Estimate the expected loss per interruption as half the checkpoint interval to choose that interval.",
    ),
),
]
