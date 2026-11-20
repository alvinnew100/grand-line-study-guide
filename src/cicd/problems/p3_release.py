PROBLEMS = [
dict(
    id="cicd-rolling-update",
    title="Rolling Update Schedule",
    difficulty="Medium",
    pattern="Simulation",
    entry="rolling_schedule",
    description=r"""
A rolling update replaces the old copies ("pods") of an application with new ones a few at a time, controlled by
two limits:

- `max_surge`: how many pods **above** `replicas` may exist during the update;
- `max_unavailable`: how many pods **below** `replicas` may be running during the update.

Simulate the update in steps. The state is `[old, new]`, the numbers of running old and new pods, starting at
`[replicas, 0]`. In each step do the following, in this order:

1. **Remove old pods**, as many as possible while keeping `old + new >= replicas - max_unavailable`
   (never more than the old pods that exist).
2. **Add new pods**, as many as possible while keeping `old + new <= replicas + max_surge`
   (never more than are still needed to reach `replicas` new pods). The added pods are running by the end of the step.

Record the state after each step. Stop when the state is `[0, replicas]`.

Return the list of states, beginning with the starting state. If both limits are `0` and `replicas > 0`, no
progress is possible: return `[]`.

**Example 1:** `replicas = 4`, `max_surge = 1`, `max_unavailable = 0` → `[[4,0],[4,1],[3,2],[2,3],[1,4],[0,4]]`

**Example 2:** `replicas = 4`, `max_surge = 0`, `max_unavailable = 2` → `[[4,0],[2,2],[0,4]]`
""",
    starter='''def rolling_schedule(replicas: int, max_surge: int, max_unavailable: int) -> List[List[int]]:
    pass
''',
    solution='''def rolling_schedule(replicas, max_surge, max_unavailable):
    if replicas > 0 and max_surge == 0 and max_unavailable == 0:
        return []
    old, new = replicas, 0
    states = [[old, new]]
    while old > 0 or new < replicas:
        removable = min(old, old + new - (replicas - max_unavailable))
        old -= max(0, removable)
        addable = min(replicas - new, replicas + max_surge - (old + new))
        new += max(0, addable)
        states.append([old, new])
    return states
''',
    tests=[
        [4, 1, 0],
        [4, 0, 2],
        [10, 2, 1],
        [10, 1, 0],
        [10, 0, 3],
        [10, 10, 0],
        [3, 0, 0],
        [0, 0, 0],
        [0, 2, 1],
        [1, 1, 0],
        [1, 0, 1],
        [5, 0, 5],
        [5, 100, 100],
        [7, 3, 2],
        [1000, 1, 0],
    ],
    examples=2,
    wrong_solutions=[
        '''def rolling_schedule(replicas, max_surge, max_unavailable):
    if replicas > 0 and max_surge == 0 and max_unavailable == 0:
        return []
    old, new = replicas, 0
    states = [[old, new]]
    while old > 0 or new < replicas:
        addable = min(replicas - new, replicas + max_surge - (old + new))
        new += max(0, addable)
        removable = min(old, old + new - (replicas - max_unavailable))
        old -= max(0, removable)
        states.append([old, new])
    return states
''',
        '''def rolling_schedule(replicas, max_surge, max_unavailable):
    step = max_surge + max_unavailable
    if replicas > 0 and step == 0:
        return []
    old, new = replicas, 0
    states = [[old, new]]
    while new < replicas:
        k = min(step, replicas - new)
        old, new = old - k, new + k
        states.append([old, new])
    return states
''',
    ],
    guide=dict(
        prereqs="Loops, `min` and `max`. See the lesson *Blue-green, canary and rolling deployments*.",
        intuition="Two fences bound the total number of pods: a floor (`replicas - max_unavailable`) and a ceiling (`replicas + max_surge`). "
                  "Each step lowers the total to the floor by removing old pods, then raises it to the ceiling by adding new ones. "
                  "The gap between the fences is the amount of work one step can do.",
        hints=[
            "Write down the floor and the ceiling as two numbers before simulating.",
            "The number of old pods you may remove is the current total minus the floor, limited by how many old pods are left.",
            "After removing, the number of new pods you may add is the ceiling minus the current total, limited by how many new pods are still missing.",
        ],
        brute_force="Remove and add one pod at a time, checking both limits after each single change. It reaches the same states with more loop "
                    "iterations; grouping the changes of one step into two formulas is tidier.",
        approach="1. If nothing can move (both limits 0 with replicas > 0), return `[]`.\n"
                 "2. Start at `[replicas, 0]`.\n"
                 "3. Loop until `[0, replicas]`: `old -= max(0, min(old, old + new - floor))`, then `new += max(0, min(replicas - new, ceiling - (old + new)))`; record the state.\n\n"
                 "**Dry run** on Example 1 (floor 4, ceiling 5): [4,0] -> remove 0, add 1 -> [4,1] -> remove 1 (total 5 down to 4), add 1 -> [3,2] -> "
                 "[2,3] -> [1,4] -> remove 1, add 0 -> [0,4].",
        complexity="Time O(replicas / (max_surge + max_unavailable)) steps. Space the same, for the recorded states.",
        pitfalls="- The order inside a step matters: removing first frees room below the ceiling for the additions.\n"
                 "- Clamp at zero: in the first step with `max_unavailable = 0` nothing may be removed.\n"
                 "- With both limits zero the loop would never end; handle that case first.\n"
                 "- `replicas = 0` is already finished: the answer is `[[0, 0]]`.\n"
                 "- The final step may only remove old pods and add nothing.",
        follow_up="Kubernetes also accepts percentages for both limits: surge rounds up and unavailable rounds down. Extend the function to accept `'25%'`.",
    ),
),
dict(
    id="cicd-blue-green-fsm",
    title="Blue-Green Switch State Machine",
    difficulty="Medium",
    pattern="Simulation / State Machine",
    entry="blue_green",
    description=r"""
A blue-green deployment keeps two environments ("slots"), `blue` and `green`. One is **live** (serving users) and
the other is **idle**. Process a list of commands and report the final state.

Initially `blue` is live with version `"v0"`, and `green` is idle and empty.

Commands (each is a list):

- `["deploy", version]` — install `version` in the idle slot. The idle slot becomes **unverified**.
  Always accepted.
- `["verify", "pass"]` or `["verify", "fail"]` — record the result of testing the idle slot. Rejected if nothing
  has ever been deployed to the idle slot. A pass marks the idle slot verified; a fail marks it unverified.
- `["switch"]` — make the idle slot live. Accepted only if the idle slot is **verified**. After a switch, the slot
  that was live becomes idle, keeps its version and counts as verified (it was serving users a moment ago).
  A rollback becomes possible.
- `["rollback"]` — switch back to the previous live slot. Accepted only if a rollback is possible: the most recent
  accepted `switch` has not been followed by an accepted `deploy` or an accepted `rollback`.

Rejected commands change nothing.

Return `[live_slot, live_version, rejected]`, where `rejected` is the number of rejected commands.

**Example 1:** `[["deploy","v1"],["verify","pass"],["switch"]]` → `["green", "v1", 0]`

**Example 2:** `[["deploy","v1"],["switch"],["verify","pass"],["switch"],["rollback"],["rollback"]]` → `["blue", "v0", 2]`
(the first switch is rejected because nothing was verified; the second rollback is rejected)
""",
    starter='''def blue_green(commands: List[List[str]]) -> list:
    pass
''',
    solution='''def blue_green(commands):
    version = {"blue": "v0", "green": None}
    verified = {"blue": True, "green": False}
    live, can_rollback, rejected = "blue", False, 0
    for command in commands:
        idle = "green" if live == "blue" else "blue"
        kind = command[0]
        if kind == "deploy":
            version[idle] = command[1]
            verified[idle] = False
            can_rollback = False
        elif kind == "verify":
            if version[idle] is None:
                rejected += 1
            else:
                verified[idle] = command[1] == "pass"
        elif kind == "switch":
            if verified[idle]:
                verified[live] = True
                live = idle
                can_rollback = True
            else:
                rejected += 1
        elif kind == "rollback":
            if can_rollback:
                live = idle
                can_rollback = False
            else:
                rejected += 1
    return [live, version[live], rejected]
''',
    tests=[
        [[["deploy", "v1"], ["verify", "pass"], ["switch"]]],
        [[["deploy", "v1"], ["switch"], ["verify", "pass"], ["switch"], ["rollback"], ["rollback"]]],
        [[]],
        [[["switch"]]],
        [[["rollback"]]],
        [[["verify", "pass"], ["switch"]]],
        [[["deploy", "v1"], ["verify", "fail"], ["switch"]]],
        [[["deploy", "v1"], ["verify", "pass"], ["verify", "fail"], ["switch"]]],
        [[["deploy", "v1"], ["verify", "pass"], ["deploy", "v2"], ["switch"]]],
        [[["deploy", "v1"], ["verify", "pass"], ["switch"], ["deploy", "v2"], ["rollback"]]],
        [[["deploy", "v1"], ["verify", "pass"], ["switch"], ["switch"]]],
        [[["deploy", "v1"], ["verify", "pass"], ["switch"], ["rollback"], ["switch"]]],
        [[["deploy", "v1"], ["verify", "pass"], ["switch"], ["deploy", "v2"], ["verify", "pass"], ["switch"], ["rollback"]]],
        [[["deploy", "v1"], ["verify", "pass"], ["switch"], ["verify", "fail"], ["rollback"], ["switch"]]],
        [sum(([["deploy", f"v{i}"], ["verify", "pass" if i % 3 else "fail"], ["switch"]] for i in range(1, 200)), [])],
    ],
    examples=2,
    wrong_solutions=[
        '''def blue_green(commands):
    version = {"blue": "v0", "green": None}
    live, rejected = "blue", 0
    for c in commands:
        idle = "green" if live == "blue" else "blue"
        if c[0] == "deploy":
            version[idle] = c[1]
        elif c[0] in ("switch", "rollback"):
            if version[idle] is None:
                rejected += 1
            else:
                live = idle
    return [live, version[live], rejected]
''',
        '''def blue_green(commands):
    version = {"blue": "v0", "green": None}
    verified = {"blue": True, "green": False}
    live, rejected = "blue", 0
    for c in commands:
        idle = "green" if live == "blue" else "blue"
        if c[0] == "deploy":
            version[idle] = c[1]; verified[idle] = False
        elif c[0] == "verify":
            if version[idle] is None:
                rejected += 1
            else:
                verified[idle] = c[1] == "pass"
        else:
            if verified[idle]:
                verified[live] = True
                live = idle
            else:
                rejected += 1
    return [live, version[live], rejected]
''',
    ],
    guide=dict(
        prereqs="Dictionaries, loops and `if`/`elif` chains. See the lesson *Blue-green, canary and rolling deployments*.",
        intuition="A state machine is a small set of facts plus rules for how each command changes them. Here the facts are: which slot is live, "
                  "what version each slot holds, whether each slot is verified, and whether a rollback is currently possible. Every command "
                  "either updates some of those facts or is rejected.",
        hints=[
            "Compute the idle slot at the start of each command from the live slot.",
            "Keep one boolean, `can_rollback`: set it on an accepted switch, clear it on a deploy and on an accepted rollback.",
            "When a switch succeeds, mark the slot that was live as verified before swapping, because it becomes the new idle slot.",
        ],
        brute_force="There is no slower meaningful approach; each command is handled in constant time. The work is in getting the rules exactly right.",
        approach="Keep `version`, `verified`, `live`, `can_rollback`, `rejected`. For each command, with `idle` = the other slot:\n\n"
                 "- deploy: set the idle version, mark idle unverified, clear `can_rollback`.\n"
                 "- verify: reject if the idle slot is empty; otherwise set its verified flag from pass/fail.\n"
                 "- switch: if idle is verified, mark the live slot verified, swap, set `can_rollback`; otherwise reject.\n"
                 "- rollback: if `can_rollback`, swap and clear it; otherwise reject.\n\n"
                 "**Dry run** on Example 2: deploy v1 (green unverified). switch -> rejected (1). verify pass. switch -> live green, can roll back. "
                 "rollback -> live blue. rollback -> rejected (2). Result: blue, v0, 2.",
        complexity="Time O(n) for n commands. Space O(1).",
        pitfalls="- A switch must be refused when the idle slot is unverified, including when it was verified and then redeployed.\n"
                 "- A later `verify fail` cancels an earlier pass.\n"
                 "- Deploying to the idle slot after a switch overwrites the previous version, so rollback is no longer possible.\n"
                 "- After a rollback, a second rollback is rejected, but a `switch` is accepted because the other slot is still verified.\n"
                 "- Verifying an empty slot is rejected.",
        follow_up="Add a `drain` period: after a switch, the old slot keeps serving existing connections for a number of ticks before it may be redeployed.",
    ),
),
dict(
    id="cicd-canary-decision",
    title="Canary Analysis Decision",
    difficulty="Medium",
    pattern="Arithmetic / Decision Rules",
    entry="canary_decision",
    description=r"""
During a canary release a small share of traffic goes to the new version (the **canary**) while the rest goes to
the current version (the **baseline**). Decide what to do next from their error rates.

`baseline` and `canary` are lists of samples, one per time interval; each sample is `[requests, errors]`.
Add up the samples of each list to get its total requests and total errors. A list's **error rate** is
`errors / requests`, or `0` if it has no requests.

`config` is a dictionary:

- `"min_requests"`: the minimum total canary requests needed before any judgement;
- `"abs_ceiling"`: an error rate the canary must never exceed;
- `"max_ratio"` and `"margin"`: the canary may not be worse than `baseline_rate * max_ratio + margin`.

Return one of three strings, applying the rules in this order:

1. `"wait"` if the canary has fewer than `min_requests` requests in total;
2. `"rollback"` if the canary's error rate is **greater than** `abs_ceiling`;
3. `"rollback"` if the canary's error rate is **greater than** `baseline_rate * max_ratio + margin`;
4. otherwise `"promote"`.

**Example 1:** `baseline = [[5000, 10], [4500, 9]]`, `canary = [[250, 0], [250, 1]]`,
`config = {"min_requests": 500, "abs_ceiling": 0.02, "max_ratio": 1.5, "margin": 0.002}` → `"promote"`

**Example 2:** the same, but `canary = [[250, 3], [250, 4]]` → `"rollback"` (1.4% against a limit of 0.5%)
""",
    starter='''def canary_decision(baseline: List[List[int]], canary: List[List[int]], config: dict) -> str:
    pass
''',
    solution='''def canary_decision(baseline, canary, config):
    def totals(samples):
        return sum(s[0] for s in samples), sum(s[1] for s in samples)
    b_req, b_err = totals(baseline)
    c_req, c_err = totals(canary)
    if c_req < config["min_requests"]:
        return "wait"
    b_rate = b_err / b_req if b_req else 0.0
    c_rate = c_err / c_req if c_req else 0.0
    if c_rate > config["abs_ceiling"]:
        return "rollback"
    if c_rate > b_rate * config["max_ratio"] + config["margin"]:
        return "rollback"
    return "promote"
''',
    tests=[
        [[[5000, 10], [4500, 9]], [[250, 0], [250, 1]], {"min_requests": 500, "abs_ceiling": 0.02, "max_ratio": 1.5, "margin": 0.002}],
        [[[5000, 10], [4500, 9]], [[250, 3], [250, 4]], {"min_requests": 500, "abs_ceiling": 0.02, "max_ratio": 1.5, "margin": 0.002}],
        [[[5000, 10], [4500, 9]], [[100, 30]], {"min_requests": 500, "abs_ceiling": 0.02, "max_ratio": 1.5, "margin": 0.002}],
        [[[9500, 760]], [[500, 41]], {"min_requests": 500, "abs_ceiling": 0.02, "max_ratio": 1.5, "margin": 0.002}],
        [[[9500, 150]], [[500, 8]], {"min_requests": 500, "abs_ceiling": 0.02, "max_ratio": 1.5, "margin": 0.002}],
        [[], [[1000, 0]], {"min_requests": 500, "abs_ceiling": 0.02, "max_ratio": 1.5, "margin": 0.002}],
        [[], [[1000, 5]], {"min_requests": 500, "abs_ceiling": 0.02, "max_ratio": 1.5, "margin": 0.002}],
        [[[1000, 10]], [], {"min_requests": 0, "abs_ceiling": 0.02, "max_ratio": 1.5, "margin": 0.0}],
        [[[1000, 10]], [], {"min_requests": 1, "abs_ceiling": 0.02, "max_ratio": 1.5, "margin": 0.0}],
        [[[1000, 0]], [[400, 0], [99, 0]], {"min_requests": 500, "abs_ceiling": 0.02, "max_ratio": 1.5, "margin": 0.002}],
        [[[1000, 0]], [[400, 0], [100, 0]], {"min_requests": 500, "abs_ceiling": 0.02, "max_ratio": 1.5, "margin": 0.002}],
        [[[1000, 100]], [[1000, 100]], {"min_requests": 500, "abs_ceiling": 0.5, "max_ratio": 1.0, "margin": 0.0}],
        [[[1000, 100]], [[1000, 101]], {"min_requests": 500, "abs_ceiling": 0.5, "max_ratio": 1.0, "margin": 0.0}],
        [[[1000, 0]], [[10, 1], [990, 0]], {"min_requests": 500, "abs_ceiling": 0.02, "max_ratio": 1.5, "margin": 0.002}],
        [[[2000, 20], [0, 0]], [[0, 0], [800, 16]], {"min_requests": 500, "abs_ceiling": 0.05, "max_ratio": 2.0, "margin": 0.001}],
        [[[100, 1]] * 500, [[10, 0]] * 499 + [[10, 3]], {"min_requests": 5000, "abs_ceiling": 0.02, "max_ratio": 1.2, "margin": 0.0005}],
    ],
    examples=2,
    wrong_solutions=[
        '''def canary_decision(baseline, canary, config):
    c_req = sum(s[0] for s in canary)
    c_err = sum(s[1] for s in canary)
    if c_req < config["min_requests"]:
        return "wait"
    rate = c_err / c_req if c_req else 0.0
    return "rollback" if rate > config["abs_ceiling"] else "promote"
''',
        '''def canary_decision(baseline, canary, config):
    def mean_rate(samples):
        rates = [s[1] / s[0] for s in samples if s[0]]
        return sum(rates) / len(rates) if rates else 0.0
    if sum(s[0] for s in canary) < config["min_requests"]:
        return "wait"
    b, c = mean_rate(baseline), mean_rate(canary)
    if c > config["abs_ceiling"] or c > b * config["max_ratio"] + config["margin"]:
        return "rollback"
    return "promote"
''',
    ],
    guide=dict(
        prereqs="Summing over lists, division with a guard for zero, and comparisons. See the lesson *Blue-green, canary and rolling deployments*.",
        intuition="Three questions in order: do we have enough data to say anything; is the canary bad in absolute terms; is it clearly worse than "
                  "the version it would replace? Comparing with a baseline that runs at the same moment stops the canary from being blamed for a "
                  "problem that is hitting everything.",
        hints=[
            "Add up all the requests and all the errors first; do not average the per-interval rates.",
            "Check the sample size before computing any rate, and guard the divisions against zero requests.",
            "Use strictly greater-than for both rollback tests, so that a canary exactly at the limit is promoted.",
        ],
        brute_force="There is no slower sensible algorithm: the totals need one pass. A common wrong shortcut is to average the interval rates, "
                    "which lets a tiny interval count as much as a huge one.",
        approach="1. `c_req, c_err` and `b_req, b_err` = column sums.\n"
                 "2. If `c_req < min_requests`: `wait`.\n"
                 "3. Rates = errors / requests (0 when there are no requests).\n"
                 "4. `rollback` if canary rate > `abs_ceiling`; `rollback` if canary rate > baseline rate * `max_ratio` + `margin`; else `promote`.\n\n"
                 "**Dry run** on Example 2: baseline 19 / 9500 = 0.002; canary 7 / 500 = 0.014. Enough requests. 0.014 is not above 0.02. "
                 "Relative limit = 0.002 * 1.5 + 0.002 = 0.005; 0.014 > 0.005, so `rollback`.",
        complexity="Time O(n) for n samples in total. Space O(1).",
        pitfalls="- A canary with few requests must give `wait`, even if its error rate looks terrible.\n"
                 "- Averaging interval rates weights a 10-request interval like a 5,000-request one.\n"
                 "- With no baseline traffic the baseline rate is 0, so only the margin protects the canary.\n"
                 "- Without the absolute ceiling, a canary would be promoted during an outage that affects both versions equally.\n"
                 "- `margin` keeps a canary from being rolled back for one error when the baseline has none.",
        follow_up="Make the decision statistically: with a few hundred requests, is a difference of five errors significant? Look up the two-proportion z-test.",
    ),
),
dict(
    id="cicd-rollback-target",
    title="Choose the Rollback Target",
    difficulty="Easy",
    pattern="Arrays / Scan",
    entry="rollback_target",
    description=r"""
A release is misbehaving, and you need the version to roll back to.

`releases` is the release history, **oldest first**. Each entry is `[version, status, schema]`:

- `status` is `"succeeded"`, `"failed"` (never became healthy) or `"rolled_back"` (was live, then withdrawn
  for cause);
- `schema` is the database schema number that release was built for.

The **last** entry is the release now live. Its `schema` is the schema the database has today.

`compat` says how far behind an application may be: a release built for schema `s` can run against today's
schema `S` only if `S - s <= compat`.

Return the version of the **most recent earlier** release that:

- has status `"succeeded"`, and
- has a different version string from the current release, and
- is compatible with today's schema.

If no earlier release qualifies, return `None`.

**Example 1:** `[["v41","succeeded",17],["v42","succeeded",18],["v43","rolled_back",18],["v44","succeeded",19]]`, `compat = 1` → `"v42"`

**Example 2:** `[["v41","succeeded",17],["v42","rolled_back",18],["v43","succeeded",19]]`, `compat = 1` → `None`
(v41 is healthy but two schema versions behind)
""",
    starter='''def rollback_target(releases: List[list], compat: int) -> Optional[str]:
    pass
''',
    solution='''def rollback_target(releases, compat):
    if not releases:
        return None
    current_version, _, current_schema = releases[-1]
    for version, status, schema in reversed(releases[:-1]):
        if status == "succeeded" and version != current_version and current_schema - schema <= compat:
            return version
    return None
''',
    tests=[
        [[["v41", "succeeded", 17], ["v42", "succeeded", 18], ["v43", "rolled_back", 18], ["v44", "succeeded", 19]], 1],
        [[["v41", "succeeded", 17], ["v42", "rolled_back", 18], ["v43", "succeeded", 19]], 1],
        [[], 1],
        [[["v1", "succeeded", 1]], 5],
        [[["v1", "succeeded", 1], ["v2", "succeeded", 1]], 0],
        [[["v1", "succeeded", 1], ["v2", "succeeded", 2]], 0],
        [[["v1", "failed", 3], ["v2", "failed", 3], ["v3", "succeeded", 3]], 2],
        [[["v1", "succeeded", 3], ["v2", "failed", 3], ["v3", "rolled_back", 3], ["v4", "failed", 3]], 0],
        [[["v1", "succeeded", 5], ["v2", "succeeded", 5], ["v2", "succeeded", 5]], 0],
        [[["v2", "succeeded", 5], ["v2", "succeeded", 5], ["v2", "succeeded", 5]], 3],
        [[["v1", "succeeded", 10], ["v2", "succeeded", 12], ["v3", "rolled_back", 12], ["v4", "succeeded", 13]], 2],
        [[["v1", "succeeded", 10], ["v2", "succeeded", 9], ["v3", "succeeded", 13]], 3],
        [[[f"v{i}", "succeeded" if i % 4 == 0 else "failed", i // 50] for i in range(1, 400)], 1],
    ],
    examples=2,
    wrong_solutions=[
        '''def rollback_target(releases, compat):
    return releases[-2][0] if len(releases) >= 2 else None
''',
        '''def rollback_target(releases, compat):
    if not releases:
        return None
    for version, status, schema in reversed(releases[:-1]):
        if status == "succeeded":
            return version
    return None
''',
    ],
    guide=dict(
        prereqs="Lists, `reversed`, slicing and unpacking. See the lesson *Rollback, roll-forward, zero downtime and emergency fixes*.",
        intuition="'The previous release' is not always safe to return to. Walk backwards through history and take the first release that was "
                  "healthy, is not the same build as the one that is failing, and can still run against today's database.",
        hints=[
            "Split the history into the current release (the last entry) and everything before it.",
            "Scan the earlier releases from newest to oldest and return at the first one that passes all three tests.",
            "The compatibility test is `current_schema - schema <= compat`.",
        ],
        brute_force="Filter the whole history down to qualifying releases and take the last one. It is also linear, but it examines every entry "
                    "even when the answer is the previous release.",
        approach="1. Empty history -> `None`.\n"
                 "2. Read `current_version` and `current_schema` from the last entry.\n"
                 "3. For each earlier entry, newest first: return its version if it succeeded, differs from the current version and is compatible.\n"
                 "4. If the loop ends, return `None`.\n\n"
                 "**Dry run** on Example 1: current = v44, schema 19. v43 was rolled back: skip. v42 succeeded, and 19 - 18 = 1 <= 1: return v42.",
        complexity="Time O(n) in the worst case. Space O(1) apart from the slice.",
        pitfalls="- The release just before the current one may itself have failed or been withdrawn.\n"
                 "- A healthy release that is too old for today's schema is not a valid target; then the answer may be to fix forward.\n"
                 "- A redeploy of the same version is not a rollback.\n"
                 "- An empty history, or a history with one entry, has no target.",
        follow_up="If no target exists, return the list of schema steps that would need to be made backward-compatible for the newest healthy release to work.",
    ),
),
dict(
    id="cicd-migration-plan",
    title="Validate an Expand/Contract Migration Plan",
    difficulty="Medium",
    pattern="Simulation / Sets",
    entry="first_unsafe_step",
    description=r"""
A zero-downtime release changes the database and the application in small steps. A plan is safe only if **after
every step** both of these still work against the database:

- the application version that is **running**, and
- the version that was running **before it** (the one you would roll back to).

A version "works" when every column it uses exists.

Input:

- `columns`: the columns that exist at the start;
- `app`: the columns used by the version running at the start (at the start, the previous version is the same);
- `steps`: a list of steps, each one of
  - `["add", column]` — add a column. Invalid if the column already exists;
  - `["drop", column]` — remove a column. Invalid if the column does not exist;
  - `["deploy", used_columns]` — release a new application version that uses the listed columns. The version
    that was running becomes the previous version.

Return the **1-based index of the first step that is invalid or leaves either version broken**, or `0` if the
whole plan is safe.

**Example 1 (direct rename):** `columns = ["name"]`, `app = ["name"]`,
`steps = [["add","full_name"],["drop","name"],["deploy",["full_name"]]]` → `2`

**Example 2 (expand/contract):** `columns = ["name"]`, `app = ["name"]`,
`steps = [["add","full_name"],["deploy",["name","full_name"]],["deploy",["full_name"]],["deploy",["full_name"]],["drop","name"]]` → `0`
""",
    starter='''def first_unsafe_step(columns: List[str], app: List[str], steps: List[list]) -> int:
    pass
''',
    solution='''def first_unsafe_step(columns, app, steps):
    existing = set(columns)
    running = set(app)
    previous = set(app)
    for index, step in enumerate(steps, 1):
        kind = step[0]
        if kind == "add":
            if step[1] in existing:
                return index
            existing.add(step[1])
        elif kind == "drop":
            if step[1] not in existing:
                return index
            existing.discard(step[1])
        else:
            previous = running
            running = set(step[1])
        if not running <= existing or not previous <= existing:
            return index
    return 0
''',
    tests=[
        [["name"], ["name"], [["add", "full_name"], ["drop", "name"], ["deploy", ["full_name"]]]],
        [["name"], ["name"], [["add", "full_name"], ["deploy", ["name", "full_name"]], ["deploy", ["full_name"]], ["deploy", ["full_name"]], ["drop", "name"]]],
        [["name"], ["name"], []],
        [["name"], ["name"], [["add", "full_name"], ["deploy", ["name", "full_name"]], ["deploy", ["full_name"]], ["drop", "name"]]],
        [["name"], ["name"], [["deploy", ["name", "full_name"]], ["add", "full_name"]]],
        [["name"], ["name"], [["add", "name"]]],
        [["name"], ["name"], [["drop", "email"]]],
        [["a", "b"], ["a"], [["drop", "b"]]],
        [["a", "b"], ["a", "b"], [["deploy", ["a"]], ["drop", "b"]]],
        [["a", "b"], ["a", "b"], [["deploy", ["a"]], ["deploy", ["a"]], ["drop", "b"]]],
        [["a"], ["a"], [["add", "b"], ["deploy", ["a", "b"]], ["drop", "b"]]],
        [["a"], ["a"], [["add", "b"], ["add", "c"], ["deploy", ["a", "b", "c"]], ["deploy", ["b", "c"]], ["deploy", []], ["drop", "a"], ["drop", "b"]]],
        [["a"], ["a"], [["add", "b"], ["add", "c"], ["deploy", ["a", "b", "c"]], ["deploy", ["b", "c"]], ["deploy", []], ["deploy", []], ["drop", "a"], ["drop", "b"], ["drop", "c"]]],
        [[], [], [["add", "x"], ["drop", "x"], ["add", "x"], ["deploy", ["x"]]]],
        [["c0"], ["c0"], sum(([["add", f"c{i}"], ["deploy", [f"c{i - 1}", f"c{i}"]], ["deploy", [f"c{i}"]], ["deploy", [f"c{i}"]], ["drop", f"c{i - 1}"]] for i in range(1, 120)), [])],
    ],
    examples=2,
    wrong_solutions=[
        '''def first_unsafe_step(columns, app, steps):
    existing, running = set(columns), set(app)
    for index, step in enumerate(steps, 1):
        if step[0] == "add":
            if step[1] in existing:
                return index
            existing.add(step[1])
        elif step[0] == "drop":
            if step[1] not in existing:
                return index
            existing.discard(step[1])
        else:
            running = set(step[1])
        if not running <= existing:
            return index
    return 0
''',
        '''def first_unsafe_step(columns, app, steps):
    existing, running, previous = set(columns), set(app), set(app)
    for index, step in enumerate(steps, 1):
        if step[0] == "add":
            existing.add(step[1])
        elif step[0] == "drop":
            existing.discard(step[1])
        else:
            previous, running = running, set(step[1])
        if not running <= existing or not previous <= existing:
            return index
    return 0
''',
    ],
    guide=dict(
        prereqs="Sets and the subset test `a <= b`. See the lessons *Schema migrations and expand/contract* and "
                "*Scenario: zero-downtime migration, and CI/CD for ML models*.",
        intuition="Keep three sets: the columns that exist, the columns the running version uses, and the columns the previous version uses. "
                  "After each step, both versions' sets must be contained in the set of existing columns. A column may be dropped only when "
                  "neither the running version nor the rollback version still uses it.",
        hints=[
            "A deploy does not change the database; it shifts 'running' to 'previous' and installs a new 'running'.",
            "Check validity of add and drop (does the column already exist / is it missing?) before applying them.",
            "After applying the step, test `running <= existing and previous <= existing`.",
        ],
        brute_force="After each step, rebuild the state by replaying the plan from the start. That is O(n^2) for n steps; carrying the three sets "
                    "forward makes it one pass.",
        approach="1. `existing = set(columns)`, `running = previous = set(app)`.\n"
                 "2. For each step (index from 1): apply add (invalid if present), drop (invalid if absent) or deploy (previous <- running, running <- new).\n"
                 "3. If either version uses a column not in `existing`, return the index.\n"
                 "4. Return 0 after the last step.\n\n"
                 "**Dry run** on Example 1: add full_name -> fine. drop name -> the running version uses `name`, which no longer exists: return 2.\n\n"
                 "Example 2 passes because `name` is dropped only after *two* releases that do not use it, so the rollback version does not need it either.",
        complexity="Time O(total number of columns mentioned in the plan). Space O(number of distinct columns).",
        pitfalls="- Checking only the running version misses the rollback requirement: dropping a column one release after the last version that "
                 "used it is unsafe.\n"
                 "- Deploying a version before its column has been added is unsafe.\n"
                 "- Adding an existing column or dropping a missing one is an invalid step.\n"
                 "- A deploy can itself be unsafe, if the new version uses a column that does not exist.",
        follow_up="Distinguish reads from writes: a version that only writes a column can tolerate that column being nullable and unread. "
                  "Also model data: after a drop, can the old column's values be recovered?",
    ),
),
dict(
    id="cicd-dora-metrics",
    title="Compute the DORA Metrics",
    difficulty="Medium",
    pattern="Arrays / Statistics",
    entry="dora_metrics",
    compare="float",
    description=r"""
Compute the four DORA delivery metrics from an event log. All times are whole minutes since the start of the
observation period.

- `deployments` is a list of `[deployment_id, finished_at, commit_times]`: a production deployment that finished
  at minute `finished_at` and contained one change for each entry of `commit_times` (the minute each change
  was committed).
- `incidents` is a list of `[deployment_id, started_at, resolved_at]`: a failure caused by that deployment.
  One deployment may have several incidents.
- `days` is the length of the observation period in days (at least 1).

Return `[frequency, lead_time, failure_rate, restore_time]`:

1. **Deployment frequency**: number of deployments divided by `days`.
2. **Lead time for changes**: the **median** of `finished_at - commit_time` over every change in every
   deployment. (With an even count, the median is the average of the two middle values.) `0` if there are no changes.
3. **Change failure rate**: the number of **distinct** deployments that have at least one incident, divided by
   the number of deployments. `0` if there are no deployments.
4. **Time to restore**: the mean of `resolved_at - started_at` over all incidents. `0` if there are none.

**Example 1:** `deployments = [["d1", 600, [240]], ["d2", 1500, [900, 1440]], ["d3", 4000, [2500]]]`,
`incidents = [["d2", 1505, 1535]]`, `days = 7`
→ `[0.428571..., 480.0, 0.333333..., 30.0]`
(lead times are 360, 600, 60 and 1500; sorted: 60, 360, 600, 1500; median (360 + 600) / 2 = 480)

Answers are compared with a small tolerance.
""",
    starter='''def dora_metrics(deployments: List[list], incidents: List[list], days: int) -> List[float]:
    pass
''',
    solution='''def dora_metrics(deployments, incidents, days):
    frequency = len(deployments) / days
    leads = sorted(finished - c for _, finished, commits in deployments for c in commits)
    if leads:
        mid = len(leads) // 2
        lead = float(leads[mid]) if len(leads) % 2 else (leads[mid - 1] + leads[mid]) / 2
    else:
        lead = 0.0
    failed = {i[0] for i in incidents}
    failure_rate = len(failed) / len(deployments) if deployments else 0.0
    restores = [resolved - started for _, started, resolved in incidents]
    restore = sum(restores) / len(restores) if restores else 0.0
    return [frequency, lead, failure_rate, restore]
''',
    tests=[
        [[["d1", 600, [240]], ["d2", 1500, [900, 1440]], ["d3", 4000, [2500]]], [["d2", 1505, 1535]], 7],
        [[], [], 7],
        [[["d1", 100, [40]]], [], 1],
        [[["d1", 100, [40]]], [["d1", 100, 160]], 1],
        [[["d1", 100, [10, 20, 30]]], [], 2],
        [[["d1", 100, [10, 20, 30, 40]]], [], 2],
        [[["d1", 100, [90]], ["d2", 200, [190]]], [["d1", 100, 110], ["d1", 150, 190]], 1],
        [[["d1", 100, []], ["d2", 200, []]], [], 4],
        [[["d1", 5000, [10]], ["d2", 5001, [5000]], ["d3", 5002, [5001]]], [], 30],
        [[["a", 10, [0]], ["b", 20, [0]], ["c", 30, [0]], ["d", 40, [0]]], [["a", 10, 20], ["b", 20, 50], ["c", 30, 90], ["d", 40, 41]], 2],
        [[["a", 1000, [0, 0, 0, 999]], ["b", 2000, [1999]]], [["b", 2000, 2000]], 28],
        [[[f"d{i}", 100 * i + 50, [100 * i + (i % 5), 100 * i + 20]] for i in range(300)],
         [[f"d{i}", 100 * i + 50, 100 * i + 50 + i % 30] for i in range(0, 300, 7)] + [["d0", 60, 90]], 28],
    ],
    examples=1,
    wrong_solutions=[
        '''def dora_metrics(deployments, incidents, days):
    leads = [f - c for _, f, cs in deployments for c in cs]
    lead = sum(leads) / len(leads) if leads else 0.0
    failed = {i[0] for i in incidents}
    rate = len(failed) / len(deployments) if deployments else 0.0
    rs = [e - s for _, s, e in incidents]
    return [len(deployments) / days, lead, rate, sum(rs) / len(rs) if rs else 0.0]
''',
        '''def dora_metrics(deployments, incidents, days):
    leads = sorted(f - c for _, f, cs in deployments for c in cs)
    if leads:
        m = len(leads) // 2
        lead = float(leads[m]) if len(leads) % 2 else (leads[m - 1] + leads[m]) / 2
    else:
        lead = 0.0
    rate = len(incidents) / len(deployments) if deployments else 0.0
    rs = [e - s for _, s, e in incidents]
    return [len(deployments) / days, lead, rate, sum(rs) / len(rs) if rs else 0.0]
''',
    ],
    guide=dict(
        prereqs="List comprehensions, sorting, sets, and the difference between a mean and a median. See the lesson *DORA metrics: measuring delivery performance*.",
        intuition="Four small computations over the same log. Two are counts divided by something, one is a middle value and one is an average. "
                  "The traps are in the definitions: lead time is per change, the failure rate counts deployments and not incidents, and the "
                  "median is not the mean.",
        hints=[
            "Collect one lead time for every commit time in every deployment, then sort the list.",
            "For the median, look at whether the count is odd or even.",
            "Use a set of deployment ids to count failed deployments once each; guard every division against an empty list.",
        ],
        brute_force="Find the median by repeatedly removing the smallest and largest values until one or two remain: O(n^2). Sorting once gives O(n log n).",
        approach="1. `frequency = len(deployments) / days`.\n"
                 "2. `leads` = sorted list of `finished - commit` for every change. Median = middle element, or the average of the two middle elements. 0 if empty.\n"
                 "3. `failure_rate` = size of the set of incident deployment ids / number of deployments (0 if there are none).\n"
                 "4. `restore` = mean of `resolved - started` (0 if there are no incidents).\n\n"
                 "**Dry run** on Example 1: 3 deployments / 7 days = 0.4286. Leads sorted [60, 360, 600, 1500] -> median 480. "
                 "One failed deployment of three -> 0.3333. One incident of 30 minutes -> 30.",
        complexity="Time O(c log c) for c changes, plus O(d + i) for d deployments and i incidents. Space O(c).",
        pitfalls="- A deployment with three commits contributes three lead times, not one.\n"
                 "- The mean of the lead times is pulled far off by one very old change; the task asks for the median.\n"
                 "- Two incidents caused by the same deployment count as one failed deployment.\n"
                 "- Empty inputs must give zeros, not a division error.\n"
                 "- A deployment may contain no commits; it still counts for frequency.",
        follow_up="Break lead time into stages (commit to merge, merge to deploy) from extra timestamps, and report which stage contributes most.",
    ),
),
]
