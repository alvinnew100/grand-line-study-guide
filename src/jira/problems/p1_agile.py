PROBLEMS = [
dict(
    id="jira-sprint-capacity",
    title="Sprint Capacity Planning",
    difficulty="Easy",
    pattern="Simulation / Arithmetic",
    entry="plan_capacity",
    description=r"""
**Mirrors:** Sprint Planning in the Scrum Guide, where the Developers' forecast is informed by *past performance*
and *upcoming capacity*. Teams commonly scale last Sprint's result by how much time is available this Sprint.

You are given:

- `sprint_days`: the number of working days in the Sprint (for example 10 for two weeks).
- `holidays`: public holidays inside the Sprint. They remove a day from **everyone**.
- `members`: a list of `[name, days_off, allocation_pct]`. `days_off` is personal leave inside the Sprint;
  `allocation_pct` is the percentage of the person's time given to this team (0 to 100).
- `past_points`: story points completed in a reference Sprint.
- `past_days`: the team's capacity in person-days during that reference Sprint.

For each member, available person-days are `max(0, sprint_days - holidays - days_off) * allocation_pct / 100`.

Return `[capacity, forecast]` where

- `capacity` is the total available person-days, **rounded to 2 decimals**;
- `forecast` is `floor(past_points * capacity / past_days)` using the *unrounded* capacity, or `0` if
  `past_days` is `0`.

**Example:** `sprint_days = 10, holidays = 1, members = [["Ann", 0, 100], ["Bo", 2, 100], ["Cy", 0, 50]],
past_points = 30, past_days = 25` → Ann 9, Bo 7, Cy 4.5 → capacity `20.5`, forecast `floor(30 * 20.5 / 25) = 24`
→ `[20.5, 24]`.
""",
    starter='''def plan_capacity(sprint_days: int, holidays: int, members: list, past_points: float, past_days: float) -> list:
    pass
''',
    solution='''import math

def plan_capacity(sprint_days, holidays, members, past_points, past_days):
    capacity = 0.0
    for name, days_off, pct in members:
        days = max(0, sprint_days - holidays - days_off)
        capacity += days * pct / 100
    forecast = 0 if past_days == 0 else math.floor(past_points * capacity / past_days + 1e-9)
    return [round(capacity, 2), forecast]
''',
    tests=[
        [10, 1, [["Ann", 0, 100], ["Bo", 2, 100], ["Cy", 0, 50]], 30, 25],
        [10, 0, [["Ann", 0, 100], ["Bo", 0, 100]], 20, 20],
        [10, 0, [], 30, 25],
        [10, 2, [["Ann", 12, 100], ["Bo", 0, 100]], 16, 8],
        [5, 0, [["Ann", 0, 0], ["Bo", 0, 100]], 10, 5],
        [10, 10, [["Ann", 0, 100]], 30, 25],
        [10, 1, [["Ann", 0, 100]], 30, 0],
        [10, 0, [["Ann", 3, 80], ["Bo", 1, 60], ["Cy", 0, 100], ["Di", 5, 100]], 42, 31],
        [15, 1, [["P" + str(i), i % 4, 50 + (i * 7) % 51] for i in range(12)], 55, 90],
        [10, 0, [["Ann", 0, 100], ["Bo", 0, 100], ["Cy", 0, 100]], 29.5, 30],
        [10, 3, [["Ann", 9, 100], ["Bo", 7, 100]], 12, 10],
    ],
    examples=2,
    wrong_solutions=[
        '''import math

def plan_capacity(sprint_days, holidays, members, past_points, past_days):
    capacity = 0.0
    for name, days_off, pct in members:
        capacity += (sprint_days - holidays - days_off) * pct / 100
    forecast = 0 if past_days == 0 else math.floor(past_points * capacity / past_days + 1e-9)
    return [round(capacity, 2), forecast]
''',
        '''import math

def plan_capacity(sprint_days, holidays, members, past_points, past_days):
    capacity = 0.0
    for name, days_off, pct in members:
        capacity += max(0, sprint_days - days_off) * pct / 100
    forecast = 0 if past_days == 0 else math.floor(past_points * capacity / past_days + 1e-9)
    return [round(capacity, 2), forecast]
''',
        '''def plan_capacity(sprint_days, holidays, members, past_points, past_days):
    capacity = 0.0
    for name, days_off, pct in members:
        capacity += max(0, sprint_days - holidays - days_off) * pct / 100
    forecast = 0 if past_days == 0 else round(past_points * capacity / past_days)
    return [round(capacity, 2), forecast]
''',
    ],
    guide=dict(
        prereqs="Loops, `max`, and `math.floor`. See the lessons *The Scrum events and their timeboxes* and *Backlog refinement and sprint planning in Jira*.",
        intuition="Capacity is the number of available person-days. Last Sprint tells you how many points the team finished per person-day; "
                  "multiply that rate by this Sprint's person-days to get a forecast. Round down: a forecast should not promise a fraction it may not reach.",
        hints=[
            "Compute each member's days first, clamp at zero, then scale by the allocation percentage.",
            "A public holiday removes a day from every member; personal leave only from that member.",
            "Guard the division when `past_days` is 0, and floor the forecast.",
        ],
        brute_force="There is nothing slower to compare with: one pass over the members is already optimal.",
        approach="1. `capacity = sum(max(0, sprint_days - holidays - off) * pct / 100)`.\n"
                 "2. `forecast = floor(past_points * capacity / past_days)` or 0.\n"
                 "3. Return `[round(capacity, 2), forecast]`.\n\n"
                 "**Dry run** on the example: Ann `(10-1-0)*1 = 9`, Bo `(10-1-2)*1 = 7`, Cy `(10-1-0)*0.5 = 4.5`; total 20.5; "
                 "`30 * 20.5 / 25 = 24.6` → 24.",
        complexity="Time O(m) for m members, space O(1).",
        pitfalls="- Leave longer than the Sprint must not produce negative days (clamp at 0).\n"
                 "- Forgetting that holidays affect everyone.\n"
                 "- Using `round` instead of `floor` for the forecast.\n"
                 "- Floating-point noise: `29.5 * 30 / 30` may come out as 29.499999...; a tiny epsilon before flooring avoids an off-by-one.",
        follow_up="Real teams also subtract time for Scrum events, on-call duty and support. How would you add a per-member `overhead_days`? "
                  "Why is a forecast from a single past Sprint fragile, and how would averaging the last three Sprints help?",
    ),
),
dict(
    id="jira-dod-check",
    title="Definition of Done Checker",
    difficulty="Easy",
    pattern="Hash Map",
    entry="check_done",
    description=r"""
**Mirrors:** the Scrum Guide's Definition of Done. An item that meets the Definition of Done becomes part of the
Increment; an item that does not cannot be released or presented at the Sprint Review and returns to the Product
Backlog.

`dod` is the ordered list of check names in the team's Definition of Done. `items` is a list of
`[key, checks]`, where `checks` is a dict from check name to `True`/`False`. A check that is **missing** from an
item's dict counts as **not met**. Checks that are not part of the DoD are ignored.

Return a dict:

- `"increment"`: the keys of items meeting every DoD check, in input order;
- `"backlog"`: a list of `[key, missing]` for every other item, in input order, where `missing` lists the unmet
  checks **in DoD order**.

An empty `dod` means every item is done.

**Example:**
```
dod   = ["reviewed", "tests", "staging"]
items = [["SHOP-1", {"reviewed": True, "tests": True, "staging": True}],
         ["SHOP-2", {"reviewed": True, "tests": False}]]
```
→ `{"increment": ["SHOP-1"], "backlog": [["SHOP-2", ["tests", "staging"]]]}`
""",
    starter='''def check_done(dod: list, items: list) -> dict:
    pass
''',
    solution='''def check_done(dod, items):
    increment, backlog = [], []
    for key, checks in items:
        missing = [c for c in dod if not checks.get(c, False)]
        if missing:
            backlog.append([key, missing])
        else:
            increment.append(key)
    return {"increment": increment, "backlog": backlog}
''',
    tests=[
        [["reviewed", "tests", "staging"],
         [["SHOP-1", {"reviewed": True, "tests": True, "staging": True}], ["SHOP-2", {"reviewed": True, "tests": False}]]],
        [[], [["A-1", {}], ["A-2", {"x": False}]]],
        [["reviewed"], []],
        [["reviewed", "tests"], [["A-1", {"tests": True, "reviewed": True, "extra": False}]]],
        [["reviewed", "tests"], [["A-1", {"tests": True}], ["A-2", {}]]],
        [["a", "b", "c", "d"], [["K-9", {"d": False, "c": False, "b": True, "a": False}]]],
        [["security", "docs"], [["X-1", {"security": True, "docs": True}], ["X-2", {"security": True, "docs": True}]]],
        [["ci"], [["X-" + str(i), {"ci": i % 3 != 0}] for i in range(1, 31)]],
        [["reviewed", "tests", "staging", "a11y", "monitoring"],
         [["P-" + str(i), {c: (i >> j) & 1 == 1 for j, c in enumerate(["reviewed", "tests", "staging", "a11y", "monitoring"])}] for i in range(32)]],
        [["tests"], [["Z-1", {"Tests": True}]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def check_done(dod, items):
    increment, backlog = [], []
    for key, checks in items:
        missing = [c for c, ok in checks.items() if not ok]
        if missing:
            backlog.append([key, missing])
        else:
            increment.append(key)
    return {"increment": increment, "backlog": backlog}
''',
        '''def check_done(dod, items):
    increment, backlog = [], []
    for key, checks in items:
        missing = sorted(c for c in dod if not checks.get(c, False))
        if missing:
            backlog.append([key, missing])
        else:
            increment.append(key)
    return {"increment": increment, "backlog": backlog}
''',
    ],
    guide=dict(
        prereqs="Dicts and `dict.get` with a default. See the lesson *Artifacts and commitments*.",
        intuition="Walk the DoD list, not the item's dict. That way missing checks are caught, unrelated checks are ignored, and the order of "
                  "the missing list follows the DoD automatically.",
        hints=[
            "`checks.get(name, False)` treats a missing check as not met.",
            "Build `missing` by iterating over `dod`.",
            "An item goes to the increment only if `missing` is empty.",
        ],
        brute_force="Iterating over the item's own checks misses checks that were never recorded, which is the most common real failure: nobody ran the step at all.",
        approach="For each item: `missing = [c for c in dod if not checks.get(c, False)]`; append to `increment` or `backlog`.\n\n"
                 "**Dry run:** SHOP-2 has reviewed True, tests False, staging absent → missing `['tests', 'staging']`.",
        complexity="Time O(n * d) for n items and d DoD checks; space O(n * d) for the output.",
        pitfalls="- Missing keys mean 'not met', not 'not applicable'.\n"
                 "- Keys are case-sensitive: `Tests` is not `tests`.\n"
                 "- Keep the DoD order in `missing`, not alphabetical order.",
        follow_up="In Jira, a team can enforce parts of a DoD with workflow conditions or validators so that an item cannot move to Done "
                  "until, for example, a field is filled in. Which DoD checks can be automated and which need a human?",
    ),
),
dict(
    id="jira-wip-check",
    title="WIP-Limit Checker",
    difficulty="Easy",
    pattern="Counting",
    entry="wip_status",
    description=r"""
**Mirrors:** Jira board column constraints. A column header turns **red** when its maximum is exceeded and
**yellow** when its minimum is not met. Constraints can count work items with or without sub-tasks.

`columns` is the ordered list of `[name, min, max]`; `min` or `max` may be `None` (no constraint).
`cards` is a list of `[key, column_name, is_subtask]`. Cards whose column is not in `columns` are ignored
(like unmapped statuses, which do not appear on the board). If `count_subtasks` is `False`, sub-task cards are
not counted.

Return a list of `[name, count, colour]` in column order, where `colour` is

- `"red"` if `max` is not `None` and `count > max`;
- otherwise `"yellow"` if `min` is not `None` and `count < min`;
- otherwise `"ok"`.

**Example:**
```
columns = [["To Do", 2, None], ["In Progress", None, 2], ["Done", None, None]]
cards   = [["S-1", "In Progress", False], ["S-2", "In Progress", False],
           ["S-3", "In Progress", True], ["S-4", "To Do", False]]
count_subtasks = True
```
→ `[["To Do", 1, "yellow"], ["In Progress", 3, "red"], ["Done", 0, "ok"]]`
""",
    starter='''def wip_status(columns: list, cards: list, count_subtasks: bool) -> list:
    pass
''',
    solution='''def wip_status(columns, cards, count_subtasks):
    counts = {name: 0 for name, _, _ in columns}
    for key, col, is_sub in cards:
        if col in counts and (count_subtasks or not is_sub):
            counts[col] += 1
    out = []
    for name, lo, hi in columns:
        n = counts[name]
        if hi is not None and n > hi:
            colour = "red"
        elif lo is not None and n < lo:
            colour = "yellow"
        else:
            colour = "ok"
        out.append([name, n, colour])
    return out
''',
    tests=[
        [[["To Do", 2, None], ["In Progress", None, 2], ["Done", None, None]],
         [["S-1", "In Progress", False], ["S-2", "In Progress", False], ["S-3", "In Progress", True], ["S-4", "To Do", False]], True],
        [[["To Do", 2, None], ["In Progress", None, 2], ["Done", None, None]],
         [["S-1", "In Progress", False], ["S-2", "In Progress", False], ["S-3", "In Progress", True], ["S-4", "To Do", False]], False],
        [[["Only", None, None]], [], True],
        [[["A", 1, 3]], [], True],
        [[["A", 1, 3]], [["X-1", "A", False], ["X-2", "A", False], ["X-3", "A", False]], True],
        [[["A", 1, 3]], [["X-1", "A", False], ["X-2", "A", False], ["X-3", "A", False], ["X-4", "A", False]], True],
        [[["A", 0, 0]], [["X-1", "A", False]], True],
        [[["A", 5, 2]], [["X-1", "A", False], ["X-2", "A", False], ["X-3", "A", False]], True],
        [[["A", 5, 2]], [["X-1", "A", False]], True],
        [[["Review", None, 1]], [["X-1", "Blocked", False], ["X-2", "Review", True], ["X-3", "Review", True]], False],
        [[["Backlog", 3, None], ["Dev", 1, 4], ["QA", None, 2], ["Done", None, None]],
         [["K-%d" % i, ["Backlog", "Dev", "QA", "Done", "Unmapped"][i % 5], i % 3 == 0] for i in range(40)], True],
        [[["Backlog", 3, None], ["Dev", 1, 4], ["QA", None, 2], ["Done", None, None]],
         [["K-%d" % i, ["Backlog", "Dev", "QA", "Done", "Unmapped"][i % 5], i % 3 == 0] for i in range(40)], False],
    ],
    examples=2,
    wrong_solutions=[
        '''def wip_status(columns, cards, count_subtasks):
    out = []
    for name, lo, hi in columns:
        n = sum(1 for k, c, s in cards if c == name)
        colour = "red" if hi is not None and n > hi else "yellow" if lo is not None and n < lo else "ok"
        out.append([name, n, colour])
    return out
''',
        '''def wip_status(columns, cards, count_subtasks):
    out = []
    for name, lo, hi in columns:
        n = sum(1 for k, c, s in cards if c == name and (count_subtasks or not s))
        colour = "red" if hi is not None and n >= hi else "yellow" if lo is not None and n < lo else "ok"
        out.append([name, n, colour])
    return out
''',
        '''def wip_status(columns, cards, count_subtasks):
    out = []
    for name, lo, hi in columns:
        n = sum(1 for k, c, s in cards if c == name and (count_subtasks or not s))
        colour = "yellow" if lo is not None and n < lo else "red" if hi is not None and n > hi else "ok"
        out.append([name, n, colour])
    return out
''',
    ],
    guide=dict(
        prereqs="Dicts for counting and `None` checks. See the lessons *Kanban: workflow, WIP limits, pull and service level expectations* and *Boards*.",
        intuition="Count the cards per column (skipping sub-tasks when asked), then compare each count with its limits. Reaching the maximum "
                  "is fine; only exceeding it is red.",
        hints=[
            "Initialise a count of 0 for every configured column so empty columns still appear.",
            "Skip cards whose column is unknown.",
            "Check `max` first, then `min`; use `>` for max and `<` for min.",
        ],
        brute_force="Counting by scanning all cards once per column is O(columns * cards); fine for a board, but a single pass with a dict is cleaner.",
        approach="1. `counts = {name: 0}` for each column.\n2. One pass over cards, incrementing when the column is known and the sub-task rule allows.\n"
                 "3. Build the result in column order with the red/yellow/ok rule.\n\n"
                 "**Dry run:** with sub-tasks counted, In Progress has 3 > 2 → red; To Do has 1 < 2 → yellow.",
        complexity="Time O(c + n) for c columns and n cards; space O(c).",
        pitfalls="- `count == max` is not a breach.\n- A column with a contradictory config (min above max) is red if over max, so check max first.\n"
                 "- Sub-task exclusion applies only when `count_subtasks` is False.",
        follow_up="Jira constraints count cards hidden by quick filters too. How would you add a `hidden` flag to cards and prove your function still counts them?",
    ),
),
dict(
    id="jira-throughput-age",
    title="Throughput and Work Item Age",
    difficulty="Easy",
    pattern="Counting / Sorting",
    entry="flow_snapshot",
    description=r"""
**Mirrors:** the Kanban Guide's flow measures: **WIP** (items started but not finished), **throughput** (items
finished per period, counted exactly) and **work item age** (time since an unfinished item started).

`items` is a list of `[key, start, finish]` where `start` and `finish` are day numbers or `None`
(`None` start means not started; `None` finish means not finished). Every given `finish` is `>= start` and
`<= today`. `period` is `[first_day, last_day]`, inclusive.

Return a dict:

- `"wip"`: the number of items with a start and no finish;
- `"throughput"`: the number of items whose finish day lies inside `period`;
- `"ages"`: `[key, age]` for every WIP item, with `age = today - start + 1` (an item started today has age 1),
  sorted by age **descending**, ties by key ascending.

**Example:** `items = [["K-1", 1, 4], ["K-2", 3, None], ["K-3", None, None], ["K-4", 6, None]]`,
`today = 8`, `period = [1, 7]` → `{"wip": 2, "throughput": 1, "ages": [["K-2", 6], ["K-4", 3]]}`
""",
    starter='''def flow_snapshot(items: list, today: int, period: list) -> dict:
    pass
''',
    solution='''def flow_snapshot(items, today, period):
    lo, hi = period
    ages = [[k, today - s + 1] for k, s, f in items if s is not None and f is None]
    ages.sort(key=lambda a: (-a[1], a[0]))
    thr = sum(1 for k, s, f in items if f is not None and lo <= f <= hi)
    return {"wip": len(ages), "throughput": thr, "ages": ages}
''',
    tests=[
        [[["K-1", 1, 4], ["K-2", 3, None], ["K-3", None, None], ["K-4", 6, None]], 8, [1, 7]],
        [[], 5, [1, 5]],
        [[["A-1", 5, None]], 5, [1, 5]],
        [[["A-1", 1, 1], ["A-2", 2, 5], ["A-3", 3, 6]], 6, [2, 5]],
        [[["A-2", 2, None], ["A-1", 2, None], ["A-3", 1, None]], 10, [1, 10]],
        [[["A-1", None, None], ["A-2", None, None]], 3, [1, 3]],
        [[["A-1", 1, 10], ["A-2", 4, 7]], 10, [7, 7]],
        [[["A-1", 1, 3]], 9, [4, 9]],
        [[["T-%02d" % i, i, (i + 4 if i % 3 else None)] for i in range(1, 40)], 45, [10, 30]],
        [[["T-%03d" % i, i % 50 + 1, None] for i in range(200)], 60, [1, 60]],
    ],
    examples=2,
    wrong_solutions=[
        '''def flow_snapshot(items, today, period):
    lo, hi = period
    ages = [[k, today - s] for k, s, f in items if s is not None and f is None]
    ages.sort(key=lambda a: (-a[1], a[0]))
    thr = sum(1 for k, s, f in items if f is not None and lo <= f <= hi)
    return {"wip": len(ages), "throughput": thr, "ages": ages}
''',
        '''def flow_snapshot(items, today, period):
    lo, hi = period
    ages = [[k, today - s + 1] for k, s, f in items if s is not None and f is None]
    ages.sort(key=lambda a: (-a[1], a[0]))
    thr = sum(1 for k, s, f in items if f is not None and lo < f <= hi)
    return {"wip": len(ages), "throughput": thr, "ages": ages}
''',
        '''def flow_snapshot(items, today, period):
    lo, hi = period
    ages = [[k, today - s + 1] for k, s, f in items if s is not None and f is None]
    ages.sort(key=lambda a: a[1], reverse=True)
    thr = sum(1 for k, s, f in items if f is not None and lo <= f <= hi)
    return {"wip": len(ages), "throughput": thr, "ages": ages}
''',
    ],
    guide=dict(
        prereqs="List comprehensions and sorting with a key. See the lesson *Kanban: workflow, WIP limits, pull and service level expectations*.",
        intuition="Three small counts over the same list. The only judgement calls are the inclusive period, the +1 in the age convention, "
                  "and the tie-break in the sort.",
        hints=[
            "WIP items are exactly those with a start and no finish; build their ages directly.",
            "Sort with `key=lambda a: (-a[1], a[0])` to get descending age and ascending key.",
            "Throughput checks `first_day <= finish <= last_day`.",
        ],
        brute_force="Already linear apart from the sort; nothing slower is worth considering.",
        approach="1. `ages` = `[key, today - start + 1]` for started, unfinished items.\n2. Sort by `(-age, key)`.\n"
                 "3. Count finishes in the period.\n\n**Dry run:** K-2 started day 3, today 8 → age 6; K-4 → 3; only K-1 finished, on day 4, inside [1, 7].",
        complexity="Time O(n log n) for the sort; space O(n).",
        pitfalls="- Items that never started are not WIP.\n- The period is inclusive on both ends.\n"
                 "- Without the key tie-break, equal ages keep input order and can mismatch.",
        follow_up="Age becomes powerful when compared with a Service Level Expectation: flag every WIP item whose age already exceeds the SLE's day count.",
    ),
),
dict(
    id="jira-planning-poker",
    title="Planning Poker Consensus",
    difficulty="Easy",
    pattern="Arrays",
    entry="poker_round",
    description=r"""
**Mirrors:** planning poker as described in Atlassian's estimation guidance: everyone votes privately on a
Fibonacci-like scale, cards are revealed together, and when estimates differ the highest and lowest voters explain.
The "within one step" agreement rule below is a common team convention, not an official rule.

The scale is `[0, 1, 2, 3, 5, 8, 13, 20, 40, 100]`. `votes` is a non-empty list of `[name, value]`. Off-scale
values are first **snapped up** to the smallest scale value `>=` them (values above 100 become 100).

- If the snapped values span at most **one step** of the scale (the positions of the largest and smallest snapped
  values differ by 0 or 1), return `["agree", largest_snapped_value]`.
- Otherwise return `["discuss", low_names, high_names]`: the names (in input order) whose snapped value equals the
  smallest, and those whose snapped value equals the largest.

**Example 1:** `[["Ann", 5], ["Bo", 8], ["Cy", 5]]` → `["agree", 8]`

**Example 2:** `[["Ann", 2], ["Bo", 3], ["Cy", 13], ["Di", 2]]` → `["discuss", ["Ann", "Di"], ["Cy"]]`
""",
    starter='''def poker_round(votes: list) -> list:
    pass
''',
    solution='''SCALE = [0, 1, 2, 3, 5, 8, 13, 20, 40, 100]

def poker_round(votes):
    def snap(v):
        for i, s in enumerate(SCALE):
            if s >= v:
                return i
        return len(SCALE) - 1
    idx = [(name, snap(v)) for name, v in votes]
    lo = min(i for _, i in idx)
    hi = max(i for _, i in idx)
    if hi - lo <= 1:
        return ["agree", SCALE[hi]]
    return ["discuss", [n for n, i in idx if i == lo], [n for n, i in idx if i == hi]]
''',
    tests=[
        [[["Ann", 5], ["Bo", 8], ["Cy", 5]]],
        [[["Ann", 2], ["Bo", 3], ["Cy", 13], ["Di", 2]]],
        [[["Solo", 3]]],
        [[["A", 4], ["B", 5]]],
        [[["A", 4], ["B", 8]]],
        [[["A", 0], ["B", 1]]],
        [[["A", 0], ["B", 2]]],
        [[["A", 150], ["B", 100], ["C", 40]]],
        [[["A", 21], ["B", 13]]],
        [[["A", 21], ["B", 12]]],
        [[["A", 1], ["B", 100], ["C", 1], ["D", 100], ["E", 8]]],
        [[["P%d" % i, [1, 2, 3, 5, 8][i % 5]] for i in range(20)]],
        [[["A", 0.5], ["B", 1]]],
    ],
    examples=2,
    wrong_solutions=[
        '''SCALE = [0, 1, 2, 3, 5, 8, 13, 20, 40, 100]

def poker_round(votes):
    vals = [v for _, v in votes]
    lo, hi = min(vals), max(vals)
    if hi - lo <= 3:
        return ["agree", hi]
    return ["discuss", [n for n, v in votes if v == lo], [n for n, v in votes if v == hi]]
''',
        '''SCALE = [0, 1, 2, 3, 5, 8, 13, 20, 40, 100]

def poker_round(votes):
    def snap(v):
        best = 0
        for i, s in enumerate(SCALE):
            if s <= v:
                best = i
        return best
    idx = [(name, snap(v)) for name, v in votes]
    lo = min(i for _, i in idx)
    hi = max(i for _, i in idx)
    if hi - lo <= 1:
        return ["agree", SCALE[hi]]
    return ["discuss", [n for n, i in idx if i == lo], [n for n, i in idx if i == hi]]
''',
    ],
    guide=dict(
        prereqs="Lists, `min`/`max` and indexing. See the lesson *Estimation: story points, planning poker and their limits*.",
        intuition="Work with positions on the scale, not raw numbers. 13 and 20 are one step apart even though the gap is 7; 2 and 5 are two steps apart "
                  "even though the gap is 3. Snapping off-scale votes up first means everyone is compared on the same scale.",
        hints=[
            "Write `snap(v)` returning the index of the first scale value `>= v`, or the last index.",
            "Compare `max_index - min_index` with 1.",
            "Collect the names at the min and max index in input order.",
        ],
        brute_force="Comparing raw differences (for example 'within 3 points') is wrong on a non-linear scale.",
        approach="1. Snap every vote to an index.\n2. If the index spread is at most 1, agree on the larger value.\n"
                 "3. Otherwise list the low and high voters.\n\n**Dry run (Example 2):** indices 2, 3, 6, 2 → spread 4 → discuss; low Ann and Di, high Cy.",
        complexity="Time O(n * s) with s = 10 scale values; space O(n).",
        pitfalls="- Snap **up**, not down: a 4 is closer in spirit to 5 than to 3 for planning safety.\n- Values above 100 still snap to 100.\n"
                 "- A single voter always agrees.",
        follow_up="Many teams include a '?' card (no idea) and a coffee-cup card (break). How would you extend the input and the rules to handle them?",
    ),
),
dict(
    id="jira-hierarchy-rollup",
    title="Hierarchy Roll-up",
    difficulty="Medium",
    pattern="Hash Map / Tree",
    entry="rollup",
    description=r"""
**Mirrors:** Jira's default work type hierarchy (level 1 Epic; level 0 Story, Task and Bug; level -1 Sub-task),
where an item's `parent` must sit on the level directly above it, and the fact that Jira's burndown and velocity
reports ignore story points on sub-tasks.

`items` is a list of dicts with keys `key`, `type` (one of `"Epic"`, `"Story"`, `"Task"`, `"Bug"`, `"Sub-task"`),
`parent` (a key or `None`) and `points` (a number or `None`).

An item is **invalid** if:

- it is an Epic with a parent (there is no level 2 in the default hierarchy); or
- it is a Sub-task with no parent; or
- it has a parent that does not exist, or whose level is not exactly one above its own.

Stories, Tasks and Bugs without a parent are valid (not every item belongs to an epic).

Return a dict:

- `"invalid"`: the sorted keys of invalid items;
- `"epics"`: for every **valid** Epic, the sum of `points` of its **valid** level-0 children (`None` counts as 0).
  Sub-task points are never added anywhere. Epics with no children map to 0.

**Example:**
```
[{"key": "E-1", "type": "Epic", "parent": None, "points": None},
 {"key": "S-1", "type": "Story", "parent": "E-1", "points": 5},
 {"key": "B-1", "type": "Bug", "parent": "E-1", "points": 2},
 {"key": "T-1", "type": "Sub-task", "parent": "S-1", "points": 3},
 {"key": "T-2", "type": "Sub-task", "parent": "E-1", "points": 1}]
```
→ `{"invalid": ["T-2"], "epics": {"E-1": 7}}` (T-2 skips a level; T-1's points are ignored)
""",
    starter='''def rollup(items: list) -> dict:
    pass
''',
    solution='''LEVEL = {"Epic": 1, "Story": 0, "Task": 0, "Bug": 0, "Sub-task": -1}

def rollup(items):
    by_key = {it["key"]: it for it in items}
    invalid = set()
    for it in items:
        lvl = LEVEL[it["type"]]
        p = it["parent"]
        if p is None:
            if lvl == -1:
                invalid.add(it["key"])
            continue
        if lvl == 1 or p not in by_key or LEVEL[by_key[p]["type"]] != lvl + 1:
            invalid.add(it["key"])
    epics = {it["key"]: 0 for it in items if it["type"] == "Epic" and it["key"] not in invalid}
    for it in items:
        if LEVEL[it["type"]] == 0 and it["key"] not in invalid and it["parent"] in epics:
            epics[it["parent"]] += it["points"] or 0
    return {"invalid": sorted(invalid), "epics": epics}
''',
    tests=[
        [[{"key": "E-1", "type": "Epic", "parent": None, "points": None},
          {"key": "S-1", "type": "Story", "parent": "E-1", "points": 5},
          {"key": "B-1", "type": "Bug", "parent": "E-1", "points": 2},
          {"key": "T-1", "type": "Sub-task", "parent": "S-1", "points": 3},
          {"key": "T-2", "type": "Sub-task", "parent": "E-1", "points": 1}]],
        [[]],
        [[{"key": "E-1", "type": "Epic", "parent": None, "points": 8}]],
        [[{"key": "S-1", "type": "Story", "parent": None, "points": 3}, {"key": "T-1", "type": "Sub-task", "parent": None, "points": 1}]],
        [[{"key": "E-1", "type": "Epic", "parent": None, "points": None}, {"key": "E-2", "type": "Epic", "parent": "E-1", "points": None},
          {"key": "S-1", "type": "Story", "parent": "E-2", "points": 5}]],
        [[{"key": "S-1", "type": "Story", "parent": "NOPE-1", "points": 5}]],
        [[{"key": "S-1", "type": "Story", "parent": None, "points": 5}, {"key": "S-2", "type": "Story", "parent": "S-1", "points": 2}]],
        [[{"key": "E-1", "type": "Epic", "parent": None, "points": None}, {"key": "S-1", "type": "Story", "parent": "E-1", "points": None},
          {"key": "K-1", "type": "Task", "parent": "E-1", "points": 1.5}]],
        [[{"key": "E-1", "type": "Epic", "parent": None, "points": None}, {"key": "T-1", "type": "Sub-task", "parent": "T-0", "points": 2},
          {"key": "T-0", "type": "Sub-task", "parent": "E-1", "points": 2}]],
        [[{"key": "E-%d" % e, "type": "Epic", "parent": None, "points": None} for e in range(5)]
         + [{"key": "S-%d" % i, "type": ["Story", "Task", "Bug"][i % 3], "parent": ("E-%d" % (i % 6) if i % 7 else None), "points": i % 9 or None} for i in range(60)]
         + [{"key": "U-%d" % i, "type": "Sub-task", "parent": "S-%d" % (i * 2), "points": 5} for i in range(25)]],
    ],
    examples=1,
    wrong_solutions=[
        '''LEVEL = {"Epic": 1, "Story": 0, "Task": 0, "Bug": 0, "Sub-task": -1}

def rollup(items):
    by_key = {it["key"]: it for it in items}
    invalid = set()
    for it in items:
        p = it["parent"]
        if p is not None and p not in by_key:
            invalid.add(it["key"])
    epics = {it["key"]: 0 for it in items if it["type"] == "Epic" and it["key"] not in invalid}
    for it in items:
        if LEVEL[it["type"]] == 0 and it["key"] not in invalid and it["parent"] in epics:
            epics[it["parent"]] += it["points"] or 0
    return {"invalid": sorted(invalid), "epics": epics}
''',
        '''LEVEL = {"Epic": 1, "Story": 0, "Task": 0, "Bug": 0, "Sub-task": -1}

def rollup(items):
    by_key = {it["key"]: it for it in items}
    invalid = set()
    for it in items:
        lvl = LEVEL[it["type"]]
        p = it["parent"]
        if p is None:
            if lvl == -1:
                invalid.add(it["key"])
            continue
        if lvl == 1 or p not in by_key or LEVEL[by_key[p]["type"]] != lvl + 1:
            invalid.add(it["key"])
    epics = {it["key"]: 0 for it in items if it["type"] == "Epic" and it["key"] not in invalid}
    for it in items:
        if it["key"] in invalid:
            continue
        p = it["parent"]
        if LEVEL[it["type"]] == -1 and p in by_key:
            p = by_key[p]["parent"]
        if p in epics:
            epics[p] += it["points"] or 0
    return {"invalid": sorted(invalid), "epics": epics}
''',
    ],
    guide=dict(
        prereqs="Dicts keyed by id and a level table. See the lessons *Epics, stories, initiatives and splitting work* and *The Jira data model*.",
        intuition="Give every type a number. A valid parent link always goes up exactly one number. Once you know which items are valid, the roll-up "
                  "only needs level-0 items whose parent is a valid epic.",
        hints=[
            "Index items by key first so parent lookups are O(1).",
            "Handle `parent is None` separately: only sub-tasks require a parent.",
            "Build the epic totals after validation, starting every valid epic at 0.",
        ],
        brute_force="Looking up each parent by scanning the list is O(n^2). A dict makes it O(n).",
        approach="1. `LEVEL` table; `by_key` dict.\n2. Mark invalid: epics with parents, orphan sub-tasks, missing parents, wrong level gap.\n"
                 "3. `epics = {valid epic: 0}`; add `points or 0` of valid level-0 children.\n\n"
                 "**Dry run:** T-2 (level -1) points at E-1 (level 1): gap 2 → invalid. S-1 5 + B-1 2 = 7 for E-1.",
        complexity="Time O(n), space O(n).",
        pitfalls="- Bugs and Tasks are level 0, exactly like Stories.\n- Do not add sub-task points to the epic (reports ignore them).\n"
                 "- A child of an invalid epic contributes nothing, even if the child itself is valid.\n- `None` points count as 0.",
        follow_up="Premium plans can add levels above Epic, such as Initiative at level 2. How would you generalise `LEVEL` and roll points up several levels?",
    ),
),
dict(
    id="jira-issue-keys",
    title="Extract Work Item Keys",
    difficulty="Easy",
    pattern="String / Regex",
    entry="extract_keys",
    description=r"""
**Mirrors:** how Jira's development integrations find work item keys in branch names, commit messages and
pull-request titles. Atlassian asks for **uppercase** keys; smart commits support the default key format of two or
more uppercase letters, a hyphen and a number.

For each string in `texts`, return the list of keys it contains, in order of first appearance, without duplicates.

A key is:

- two or more uppercase ASCII letters `A-Z`, then `-`, then a number with no leading zero (`1`, `42`, `1042`, not `0` or `07`);
- not immediately preceded by an ASCII letter or digit;
- not immediately followed by an ASCII letter or digit.

If `spaces` is non-empty, keep only keys whose letter part is in `spaces` (Jira only links keys of spaces that exist).

**Example:** `texts = ["feature/SHOP-1042-promo", "SHOP-7 fix and PAY-3, see SHOP-7", "shop-9 lower", "XSHOP-1"]`,
`spaces = []` → `[["SHOP-1042"], ["SHOP-7", "PAY-3"], [], ["XSHOP-1"]]`
""",
    starter='''def extract_keys(texts: List[str], spaces: List[str]) -> List[List[str]]:
    pass
''',
    solution='''import re

KEY = re.compile(r"(?<![A-Za-z0-9])([A-Z]{2,})-([1-9][0-9]*)(?![A-Za-z0-9])")

def extract_keys(texts, spaces):
    allowed = set(spaces)
    out = []
    for t in texts:
        seen, keys = set(), []
        for m in KEY.finditer(t):
            key = m.group(0)
            if allowed and m.group(1) not in allowed:
                continue
            if key not in seen:
                seen.add(key)
                keys.append(key)
        out.append(keys)
    return out
''',
    tests=[
        [["feature/SHOP-1042-promo", "SHOP-7 fix and PAY-3, see SHOP-7", "shop-9 lower", "XSHOP-1"], []],
        [["SHOP-1 PAY-2 OPS-3"], ["SHOP", "OPS"]],
        [[""], []],
        [["S-1 single letter", "AB-0 zero", "AB-07 leading zero", "AB-10 ok"], []],
        [["SHOP-12a", "SHOP-12_fix", "aSHOP-12", "1SHOP-12", "(SHOP-12)"], []],
        [["Shop-1 mixed case", "SHOP-1.SHOP-2", "SHOP-1SHOP-2"], []],
        [["ABC-DEF-12", "SHOP--3", "SHOP-", "-SHOP-4-"], []],
        [["Merge PR #12: SHOP-88 SHOP-88 SHOP-89 PAY-1"], ["SHOP"]],
        [["ÄSHOP-5 unicode before", "SHOP-5é after"], []],
        [["KEY-%d" % i for i in range(1, 30)] + [" ".join("AB-%d" % i for i in range(1, 200))], []],
    ],
    examples=1,
    wrong_solutions=[
        '''import re

def extract_keys(texts, spaces):
    out = []
    for t in texts:
        keys = []
        for k in re.findall(r"[A-Z]+-[0-9]+", t):
            if (not spaces or k.split("-")[0] in spaces) and k not in keys:
                keys.append(k)
        out.append(keys)
    return out
''',
        '''import re

def extract_keys(texts, spaces):
    out = []
    for t in texts:
        keys = []
        for k in re.findall(r"(?<![A-Za-z0-9])[A-Z]{2,}-[1-9][0-9]*(?![A-Za-z0-9])", t, re.IGNORECASE):
            k = k.upper()
            if (not spaces or k.split("-")[0] in spaces) and k not in keys:
                keys.append(k)
        out.append(keys)
    return out
''',
    ],
    guide=dict(
        prereqs="Python `re`: character classes, quantifiers and lookarounds. See the lessons *What Jira is* and *Jira and your code*.",
        intuition="Describe the key exactly with a regular expression, then add guards on both sides so a key is not cut out of the middle of a longer word.",
        hints=[
            "`[A-Z]{2,}-[1-9][0-9]*` describes the key itself.",
            "A negative lookbehind `(?<![A-Za-z0-9])` and lookahead `(?![A-Za-z0-9])` enforce the boundaries.",
            "Keep a `seen` set per text to remove duplicates while preserving order.",
        ],
        brute_force="Splitting on spaces misses keys inside branch names like `feature/SHOP-1-x` and inside punctuation like `(SHOP-1)`.",
        approach="Compile the pattern once; for each text, iterate `finditer`, filter by `spaces`, de-duplicate in order.\n\n"
                 "**Dry run:** `SHOP-12a` → digits followed by `a` → the lookahead fails, and backtracking to `SHOP-1` fails because `2` follows → no key.",
        complexity="Time O(total length of the texts); space O(number of keys).",
        pitfalls="- Lowercase or mixed-case keys are not keys.\n- `\\b` is not enough: it treats `_` as a word character and would reject `x_SHOP-1` style text differently.\n"
                 "- Python's `[A-Za-z]` is ASCII; non-ASCII letters like `Ä` are not in it, so `ÄSHOP-5` still yields `SHOP-5` here.\n"
                 "- Leading zeros are not valid key numbers.",
        follow_up="Jira also links keys that appear in pull-request titles from forks and in squashed merge commits. If two repositories use different key spaces, how would you route each key to the right Jira site?",
    ),
),
]
