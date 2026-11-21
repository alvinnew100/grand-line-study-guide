def _patch(src, old, new):
    if old not in src:
        raise ValueError("patch target not found: " + old[:60])
    return src.replace(old, new, 1)


_REPLAY = '''def _replay(initial, events, days):
    pts, sub, inside, done = {}, set(), set(), set()
    for key, p, is_sub in initial:
        pts[key] = p or 0
        inside.add(key)
        if is_sub:
            sub.add(key)
    by_day = {}
    for ev in events:
        by_day.setdefault(ev[0], []).append(ev)
    snapshots, scope_days = [], set()
    for d in range(days + 1):
        for ev in by_day.get(d, []):
            kind, key = ev[1], ev[2]
            if kind == "add":
                p, is_sub = ev[3]
                pts[key] = p or 0
                inside.add(key)
                done.discard(key)
                if is_sub:
                    sub.add(key)
                else:
                    scope_days.add(d)
            elif key not in inside or key in sub:
                continue
            elif kind == "remove":
                inside.discard(key)
                done.discard(key)
                scope_days.add(d)
            elif kind == "done":
                done.add(key)
            elif kind == "reopen":
                done.discard(key)
            elif kind == "estimate":
                new = ev[3] or 0
                if new != pts[key]:
                    pts[key] = new
                    scope_days.add(d)
        live = [k for k in inside if k not in sub]
        scope = sum(pts[k] for k in live)
        finished = sum(pts[k] for k in live if k in done)
        snapshots.append((round(scope, 2), round(finished, 2)))
    start = sum(p or 0 for k, p, s in initial if not s)
    return snapshots, sorted(scope_days), start
'''

_BURNDOWN = _REPLAY + '''
def burndown(days, initial, events):
    snaps, changes, start = _replay(initial, events, days)
    return {
        "remaining": [round(s - f, 2) for s, f in snaps],
        "guideline": [round(start * (1 - d / days), 2) if days else 0 for d in range(days + 1)],
        "scope_changes": changes,
    }
'''

_BURNUP = _REPLAY + '''
def burnup(days, initial, events):
    snaps, changes, start = _replay(initial, events, days)
    return {"scope": [s for s, f in snaps], "done": [f for s, f in snaps]}
'''

_SPRINT_INIT = [["S-1", 5, False], ["S-2", 3, False], ["S-3", 8, False], ["S-4", 2, False], ["S-5", 5, False]]
_SPRINT_EVENTS = [[2, "done", "S-4", None], [4, "done", "S-2", None], [5, "add", "S-9", [5, False]],
                  [6, "estimate", "S-3", 13], [7, "done", "S-1", None], [9, "done", "S-9", None], [9, "done", "S-5", None]]

_BURN_TESTS = [
    [10, _SPRINT_INIT, _SPRINT_EVENTS],
    [5, [["A-1", 3, False], ["A-2", 2, False]], [[1, "done", "A-1", None], [3, "done", "A-2", None]]],
    [4, [], []],
    [3, [["A-1", 3, False], ["A-1a", 5, True]], [[1, "done", "A-1a", None], [2, "estimate", "A-1a", 8], [3, "done", "A-1", None]]],
    [6, [["A-1", 5, False], ["A-2", None, False]], [[1, "done", "A-1", None], [2, "reopen", "A-1", None], [4, "estimate", "A-2", 3], [5, "done", "A-2", None]]],
    [5, [["A-1", 5, False], ["A-2", 3, False]], [[1, "done", "A-1", None], [2, "remove", "A-1", None], [3, "remove", "A-2", None]]],
    [5, [["A-1", 5, False]], [[0, "add", "A-2", [3, False]], [0, "add", "A-3", [2, True]], [2, "estimate", "A-1", 5], [3, "done", "ZZZ-1", None]]],
    [4, [["A-1", 2.5, False], ["A-2", 0.5, False]], [[2, "done", "A-2", None], [3, "estimate", "A-1", 1.5]]],
    [10, [["K-%d" % i, (i % 8) + 1, i % 5 == 0] for i in range(30)],
     [[d, "done", "K-%d" % (d * 3 + j), None] for d in range(1, 10) for j in range(3)]
     + [[4, "add", "K-90", [8, False]], [6, "reopen", "K-4", None], [7, "remove", "K-11", None]]],
]

_FLOW = '''def flow_times(items, log, active, done):
    active, done = set(active), set(done)
    by_key = {}
    for key, day, status in log:
        by_key.setdefault(key, []).append((day, status))
    out = []
    for key, created in items:
        entries = by_key.get(key, [])
        if not entries or entries[-1][1] not in done:
            continue
        finish = entries[-1][0]
        status, since, cycle = None, created, 0
        for day, new in entries:
            if status in active:
                cycle += day - since
            status, since = new, day
        out.append([key, cycle, finish - created])
    return out
'''

_CONTROL = '''import math

def control_chart(cycle_times):
    n = len(cycle_times)
    if n == 0:
        return {"window": 0, "rolling": [], "sle85": None}
    window = max(5, n * 20 // 100)
    if window % 2 == 0:
        window += 1
    half = window // 2
    rolling = []
    for i in range(n):
        part = cycle_times[max(0, i - half):min(n, i + half + 1)]
        rolling.append(round(sum(part) / len(part), 2))
    ranked = sorted(cycle_times)
    sle85 = ranked[math.ceil(0.85 * n) - 1]
    return {"window": window, "rolling": rolling, "sle85": sle85}
'''

_CFD = '''def cfd(columns, moves, days):
    index = {c: i for i, c in enumerate(columns)}
    where = {}
    by_day = {}
    for day, key, col in moves:
        by_day.setdefault(day, []).append((key, col))
    out = []
    for d in range(days):
        for key, col in by_day.get(d, []):
            if col in index:
                where[key] = index[col]
        out.append([sum(1 for p in where.values() if p >= c) for c in range(len(columns))])
    return out
'''

_HOW_MANY = '''import random

def how_many(history, days, trials):
    random.seed(42)
    totals = []
    for _ in range(trials):
        total = 0
        for _ in range(days):
            total += random.choice(history)
        totals.append(total)
    totals.sort()
    return [totals[int((100 - p) * trials / 100)] for p in (50, 85, 95)]
'''

_WHEN = '''import math
import random
from datetime import date, timedelta

def when_done(history, target, trials, start_date):
    if sum(history) == 0:
        return []
    random.seed(42)
    needed = []
    for _ in range(trials):
        done = days = 0
        while done < target:
            done += random.choice(history)
            days += 1
        needed.append(days)
    needed.sort()
    start = date.fromisoformat(start_date)
    out = []
    for p in (50, 85, 95):
        d = needed[math.ceil(p * trials / 100) - 1]
        day, count = start, 0
        while True:
            if day.weekday() < 5:
                count += 1
                if count == d:
                    break
            day += timedelta(days=1)
        out.append([p, d, day.isoformat()])
    return out
'''

_HIST = [0, 2, 1, 3, 0, 2, 4, 1, 2, 0, 3, 2, 1, 2, 3]

PROBLEMS = [
dict(
    id="jira-velocity",
    title="Velocity from Sprint Records",
    difficulty="Easy",
    pattern="Aggregation",
    entry="velocity",
    description=r"""
**Mirrors:** Jira's velocity chart. **Commitment** is the total estimate of the sprint's work when the sprint
**started**: items added later and later estimate changes are excluded. **Completed** is the total estimate of work
done by the end, and **includes** items added mid-sprint. Velocity is the average of completed work over recent
sprints.

`sprints` is a list of `[name, items]` in time order. Each item is `[key, start_points, final_points, added,
completed]`: the estimate at sprint start (`None` for items added later), the estimate at the end, whether it was
added after the start, and whether it was completed. Treat `None` points as 0.

Return a dict:

- `"sprints"`: `[name, commitment, completed]` per sprint, each total rounded to 2 decimals;
- `"velocity"`: the average `completed` of the **last** `last_n` sprints (all of them if there are fewer), rounded
  to 2 decimals; `0` if there are no sprints.

**Example:**
```
sprints = [["S12", [["A-1", 5, 5, False, True], ["A-2", 3, 5, False, False]]],
           ["S13", [["A-2", 5, 5, False, True], ["A-3", None, 2, True, True]]]]
last_n = 3
```
→ `{"sprints": [["S12", 8, 5], ["S13", 5, 7]], "velocity": 6.0}`
""",
    starter='''def velocity(sprints: list, last_n: int) -> dict:
    pass
''',
    solution='''def velocity(sprints, last_n):
    rows = []
    for name, items in sprints:
        commit = sum((start or 0) for key, start, final, added, completed in items if not added)
        done = sum((final or 0) for key, start, final, added, completed in items if completed)
        rows.append([name, round(commit, 2), round(done, 2)])
    recent = [r[2] for r in rows[-last_n:]] if rows else []
    v = round(sum(recent) / len(recent), 2) if recent else 0
    return {"sprints": rows, "velocity": v}
''',
    tests=[
        [[["S12", [["A-1", 5, 5, False, True], ["A-2", 3, 5, False, False]]],
          ["S13", [["A-2", 5, 5, False, True], ["A-3", None, 2, True, True]]]], 3],
        [[], 3],
        [[["S1", []]], 3],
        [[["S1", [["A-1", 3, 8, False, True]]]], 1],
        [[["S1", [["A-1", None, None, False, True], ["A-2", 2, 2, False, False]]]], 2],
        [[["S1", [["A-1", 5, 5, False, True]]], ["S2", [["A-2", 8, 8, False, True]]], ["S3", [["A-3", 2, 2, False, True]]]], 2],
        [[["S1", [["A-1", 0.5, 0.5, False, True], ["A-2", 0.2, 0.1, False, True]]]], 3],
        [[["S1", [["A-9", None, 13, True, False]]]], 3],
        [[["S%d" % s, [["K-%d" % i, (i % 5) + 1, (i % 7) + 1, i % 4 == 0, (i + s) % 3 != 0] for i in range(s, s + 12)]] for s in range(1, 9)], 6],
        [[["S1", [["A-1", 5, 5, False, True]]], ["S2", [["A-2", 3, 3, False, True]]], ["S3", [["A-3", 4, 4, False, True]]]], 0],
    ],
    examples=1,
    wrong_solutions=[
        '''def velocity(sprints, last_n):
    rows = []
    for name, items in sprints:
        commit = sum((final or 0) for key, start, final, added, completed in items)
        done = sum((final or 0) for key, start, final, added, completed in items if completed)
        rows.append([name, round(commit, 2), round(done, 2)])
    recent = [r[2] for r in rows[-last_n:]] if rows else []
    v = round(sum(recent) / len(recent), 2) if recent else 0
    return {"sprints": rows, "velocity": v}
''',
        '''def velocity(sprints, last_n):
    rows = []
    for name, items in sprints:
        commit = sum((start or 0) for key, start, final, added, completed in items if not added)
        done = sum((final or 0) for key, start, final, added, completed in items if completed and not added)
        rows.append([name, round(commit, 2), round(done, 2)])
    recent = [r[2] for r in rows[-last_n:]] if rows else []
    v = round(sum(recent) / len(recent), 2) if recent else 0
    return {"sprints": rows, "velocity": v}
''',
        '''def velocity(sprints, last_n):
    rows = []
    for name, items in sprints:
        commit = sum((start or 0) for key, start, final, added, completed in items if not added)
        done = sum((final or 0) for key, start, final, added, completed in items if completed)
        rows.append([name, round(commit, 2), round(done, 2)])
    recent = [r[2] for r in rows[:last_n]] if rows else []
    v = round(sum(recent) / len(recent), 2) if recent else 0
    return {"sprints": rows, "velocity": v}
''',
    ],
    guide=dict(
        prereqs="Sums over filtered lists and slicing. See the lesson *Scrum reports and how they are misused*.",
        intuition="Commitment is a photo taken at the start, so use the start estimate of items that were there at the start. Completed is a photo "
                  "at the end, so use the final estimate of everything completed, wherever it came from.",
        hints=[
            "Commitment: `sum(start or 0)` over items with `added == False`.",
            "Completed: `sum(final or 0)` over items with `completed == True`.",
            "`rows[-last_n:]` takes the last n; watch out for `last_n = 0` (Python's `[-0:]` is the whole list).",
        ],
        brute_force="This is already a single pass per sprint.",
        approach="Loop over sprints, compute the two sums, round them, then average the last `last_n` completed values.\n\n"
                 "**Dry run:** S12 commitment 5 + 3 = 8, completed 5 (A-1). S13 commitment 5 (A-2 at its new start estimate), completed 5 + 2 = 7. Velocity (5 + 7) / 2 = 6.0.",
        complexity="Time O(total items); space O(number of sprints).",
        pitfalls="- Re-estimated items: commitment uses the start estimate, completed uses the final one.\n- Added items never count in commitment.\n"
                 "- `None` points are 0.\n- Round sums so 0.1 + 0.2 style float noise does not appear.",
        follow_up="Velocity is for the team's own planning. How would you also report the range (minimum and maximum of the last n sprints) so a forecast shows its uncertainty?",
    ),
),
dict(
    id="jira-sprint-report",
    title="Sprint Report",
    difficulty="Medium",
    pattern="Classification / Formatting",
    entry="sprint_report",
    description=r"""
**Mirrors:** Jira's sprint report, which lists the sprint's work, marks items **added after the sprint started with
an asterisk**, shows an estimate changed during the sprint as **old value, arrow, new value** (such as `3 -> 3.5`),
and treats an item as complete only when it is in the board's **rightmost column**.

`items` is a list of dicts with `key`, `start_points` (estimate at sprint start, `None` if added later or not
estimated), `final_points`, `added` (bool), `removed` (bool, taken out of the sprint) and `column` (0-based board
column index). `done_column` is the index of the rightmost column.

Return a dict, keeping input order in every list:

- `"completed"`: labels of items not removed and in `done_column`;
- `"not_completed"`: labels of items not removed and not in `done_column`;
- `"removed"`: labels of removed items;
- `"changes"`: `[key, "old -> new"]` for items **not** added whose `start_points` differs from `final_points`.
  Numbers are written with Python's `format(x, "g")` (so `3.0` becomes `3`, `3.5` stays `3.5`) and `None` as `-`;
- `"completed_points"`: the sum of `final_points` (`None` = 0) of completed items, rounded to 2 decimals.

A **label** is the key, followed by `*` if the item was added after the start.

**Example:**
```
items = [{"key": "S-1", "start_points": 3, "final_points": 3.5, "added": False, "removed": False, "column": 3},
         {"key": "S-2", "start_points": None, "final_points": 2, "added": True, "removed": False, "column": 1},
         {"key": "S-3", "start_points": 5, "final_points": 5, "added": False, "removed": True, "column": 0}]
done_column = 3
```
→ `{"completed": ["S-1"], "not_completed": ["S-2*"], "removed": ["S-3"], "changes": [["S-1", "3 -> 3.5"]], "completed_points": 3.5}`
""",
    starter='''def sprint_report(items: list, done_column: int) -> dict:
    pass
''',
    solution='''def sprint_report(items, done_column):
    def fmt(x):
        return "-" if x is None else format(x, "g")
    out = {"completed": [], "not_completed": [], "removed": [], "changes": [], "completed_points": 0}
    total = 0
    for it in items:
        label = it["key"] + ("*" if it["added"] else "")
        if it["removed"]:
            out["removed"].append(label)
        elif it["column"] == done_column:
            out["completed"].append(label)
            total += it["final_points"] or 0
        else:
            out["not_completed"].append(label)
        if not it["added"] and it["start_points"] != it["final_points"]:
            out["changes"].append([it["key"], fmt(it["start_points"]) + " -> " + fmt(it["final_points"])])
    out["completed_points"] = round(total, 2)
    return out
''',
    tests=[
        [[{"key": "S-1", "start_points": 3, "final_points": 3.5, "added": False, "removed": False, "column": 3},
          {"key": "S-2", "start_points": None, "final_points": 2, "added": True, "removed": False, "column": 1},
          {"key": "S-3", "start_points": 5, "final_points": 5, "added": False, "removed": True, "column": 0}], 3],
        [[], 3],
        [[{"key": "A-1", "start_points": 2, "final_points": 2, "added": False, "removed": False, "column": 2}], 2],
        [[{"key": "A-1", "start_points": None, "final_points": 5, "added": False, "removed": False, "column": 0}], 2],
        [[{"key": "A-1", "start_points": 8, "final_points": None, "added": False, "removed": False, "column": 4}], 4],
        [[{"key": "A-1", "start_points": None, "final_points": 3, "added": True, "removed": True, "column": 4},
          {"key": "A-2", "start_points": None, "final_points": 1, "added": True, "removed": False, "column": 4}], 4],
        [[{"key": "A-1", "start_points": 3.0, "final_points": 3, "added": False, "removed": False, "column": 1}], 1],
        [[{"key": "A-1", "start_points": 1, "final_points": 2, "added": False, "removed": False, "column": 5},
          {"key": "A-2", "start_points": 1, "final_points": 2, "added": False, "removed": False, "column": 3}], 3],
        [[{"key": "K-%d" % i, "start_points": (None if i % 6 == 0 else i % 5 + 1), "final_points": (i % 4 + 1) / 2,
           "added": i % 6 == 0, "removed": i % 11 == 0, "column": i % 4} for i in range(1, 40)], 3],
    ],
    examples=1,
    wrong_solutions=[
        '''def sprint_report(items, done_column):
    def fmt(x):
        return "-" if x is None else str(x)
    out = {"completed": [], "not_completed": [], "removed": [], "changes": [], "completed_points": 0}
    total = 0
    for it in items:
        label = it["key"] + ("*" if it["added"] else "")
        if it["removed"]:
            out["removed"].append(label)
        elif it["column"] == done_column:
            out["completed"].append(label)
            total += it["final_points"] or 0
        else:
            out["not_completed"].append(label)
        if not it["added"] and it["start_points"] != it["final_points"]:
            out["changes"].append([it["key"], fmt(it["start_points"]) + " -> " + fmt(it["final_points"])])
    out["completed_points"] = round(total, 2)
    return out
''',
        '''def sprint_report(items, done_column):
    def fmt(x):
        return "-" if x is None else format(x, "g")
    out = {"completed": [], "not_completed": [], "removed": [], "changes": [], "completed_points": 0}
    total = 0
    for it in items:
        label = it["key"] + ("*" if it["added"] else "")
        if it["column"] >= done_column:
            out["completed"].append(label)
            total += it["final_points"] or 0
        elif it["removed"]:
            out["removed"].append(label)
        else:
            out["not_completed"].append(label)
        if not it["added"] and it["start_points"] != it["final_points"]:
            out["changes"].append([it["key"], fmt(it["start_points"]) + " -> " + fmt(it["final_points"])])
    out["completed_points"] = round(total, 2)
    return out
''',
    ],
    guide=dict(
        prereqs="Dict access, string formatting with `format(x, \"g\")`. See the lessons *Scrum reports and how they are misused* and *Backlog refinement and sprint planning in Jira*.",
        intuition="Each item lands in exactly one of three lists (removed first, then done or not done) and may additionally appear in the changes list. "
                  "The asterisk is part of the label, not of the key used in `changes`.",
        hints=[
            "Check `removed` before the column: a removed item is never completed, whatever its column.",
            "Only `column == done_column` counts as complete.",
            "`format(3.0, \"g\")` gives `'3'`; `format(3.5, \"g\")` gives `'3.5'`.",
        ],
        brute_force="Already one pass.",
        approach="For each item: build the label; classify; add final points if completed; if not added and the estimate moved, record `old -> new`.\n\n"
                 "**Dry run:** S-1 in column 3 = done; estimate 3 → 3.5 recorded. S-2 added (asterisk) in column 1 = not completed. S-3 removed.",
        complexity="Time O(n); space O(n).",
        pitfalls="- `3.0` and `3` are equal, so no change is reported.\n- Items in a column to the right of `done_column` do not exist on a real board; here they are not equal to it.\n"
                 "- Added items never appear in `changes`.",
        follow_up="Jira's report also shows work completed outside the sprint and lets you view any past sprint. How would you add an `\"outside\"` list for items done before the sprint started?",
    ),
),
dict(
    id="jira-burndown",
    title="Sprint Burndown",
    difficulty="Medium",
    pattern="Event Replay",
    entry="burndown",
    description=r"""
**Mirrors:** Jira's sprint burndown chart: remaining work in the board's estimation statistic for each day, a
straight **guideline** from the starting total to zero, story points on **sub-tasks excluded**, work counted as done
only when it reaches the rightmost column, and remaining work rising when scope is added or estimates increase.

- `days`: the sprint length; report days `0..days` inclusive.
- `initial`: `[key, points, is_subtask]` for items in the sprint at the start (`None` points = 0).
- `events`: `[day, kind, key, value]` in time order, applied at the start of their day before measuring:
  - `"add"`: `value = [points, is_subtask]`, the item joins the sprint (not done);
  - `"remove"`: the item leaves the sprint;
  - `"done"`: the item reaches the rightmost column;
  - `"reopen"`: the item leaves the rightmost column;
  - `"estimate"`: `value` is the new points.
  Events for keys not in the sprint, and every event for a sub-task, are ignored.

Return a dict:

- `"remaining"`: for each day, total points of non-sub-task items in the sprint that are not done (rounded to 2);
- `"guideline"`: `round(start * (1 - d / days), 2)` for each day, where `start` is the total points of
  non-sub-task items in `initial` (all zeros if `days == 0`);
- `"scope_changes"`: sorted distinct days with an `add` or `remove` of a non-sub-task item, or an `estimate`
  that changed a non-sub-task item's points.

**Example:** the lesson's sprint, `days = 10`, five items totalling 23 points, an item of 5 added on day 5 and
an estimate raised from 8 to 13 on day 6 → remaining
`[23, 23, 21, 21, 18, 23, 28, 23, 23, 13, 13]`, scope changes `[5, 6]`.
""",
    starter='''def burndown(days: int, initial: list, events: list) -> dict:
    pass
''',
    solution=_BURNDOWN,
    tests=_BURN_TESTS,
    examples=1,
    wrong_solutions=[
        _patch(_BURNDOWN, "            elif key not in inside or key in sub:\n                continue\n", "            elif key not in inside:\n                continue\n")
        .replace("        live = [k for k in inside if k not in sub]", "        live = list(inside)"),
        _patch(_BURNDOWN, '            elif kind == "reopen":\n                done.discard(key)\n', ""),
        _patch(_BURNDOWN, '                if new != pts[key]:\n                    pts[key] = new\n                    scope_days.add(d)\n',
               '                pts[key] = new\n                scope_days.add(d)\n'),
    ],
    guide=dict(
        prereqs="Sets and dicts to track state while replaying events day by day. See the lesson *Scrum reports and how they are misused*.",
        intuition="Keep the state of the sprint (which items are in it, their points, which are done, which are sub-tasks). For each day, apply that "
                  "day's events, then take a measurement. Remaining work is scope minus done.",
        hints=[
            "Group events by day; apply them before measuring that day.",
            "Mark sub-tasks once and skip them everywhere, including their later events.",
            "An estimate that does not change the value is not a scope change.",
            "The guideline uses only the initial total, never later scope.",
        ],
        brute_force="Recomputing from scratch for each day by replaying all earlier events is O(days * events); fine for small inputs, but one pass is simpler.",
        approach="1. Initialise points, membership and sub-task sets.\n2. For each day apply events in order.\n3. Measure scope and done over non-sub-task members.\n"
                 "4. Build remaining, guideline and the sorted scope-change days.\n\n**Dry run (example):** day 2: 23 - 2 = 21; day 5: +5 → 23; day 6: +5 → 28; day 9: two items done → 13.",
        complexity="Time O(days * n + e) for n items and e events; space O(n).",
        pitfalls="- Reopened items count as remaining again.\n- Removing a done item reduces scope but not remaining.\n- Sub-task points never count, even if the sub-task is re-estimated.\n- Float points: round outputs.",
        follow_up="Jira lets a board's estimation statistic be the item count instead of points. How would you change the function so every non-sub-task item counts as 1?",
    ),
),
dict(
    id="jira-burnup",
    title="Sprint Burnup",
    difficulty="Medium",
    pattern="Event Replay",
    entry="burnup",
    description=r"""
**Mirrors:** Jira's burnup chart, which draws **work scope** and **completed work** as two separate lines so that
scope creep (the scope line rising) is not confused with progress. As in the other Scrum reports, sub-task story
points are excluded and done means the rightmost column.

The input is exactly the same as in *Sprint Burndown*: `days`, `initial` (`[key, points, is_subtask]`) and
`events` (`[day, kind, key, value]` with kinds `add`, `remove`, `done`, `reopen`, `estimate`, applied at the start of
their day; events for unknown keys and for sub-tasks are ignored).

Return `{"scope": [...], "done": [...]}` with one value per day `0..days`:

- `scope`: total points of non-sub-task items in the sprint (done or not);
- `done`: total points of those items that are currently done.

Round every value to 2 decimals. An estimate change on a done item changes both lines.

**Example:** the lesson's sprint → scope `[23, 23, 23, 23, 23, 28, 33, 33, 33, 33, 33]`,
done `[0, 0, 2, 2, 5, 5, 5, 10, 10, 20, 20]`.
""",
    starter='''def burnup(days: int, initial: list, events: list) -> dict:
    pass
''',
    solution=_BURNUP,
    tests=_BURN_TESTS,
    examples=1,
    wrong_solutions=[
        _patch(_BURNUP, '            elif kind == "reopen":\n                done.discard(key)\n', ""),
        _patch(_BURNUP, "        live = [k for k in inside if k not in sub]", "        live = list(inside)"),
        _patch(_BURNUP, 'snaps, changes, start = _replay(initial, events, days)\n    return {"scope": [s for s, f in snaps]',
               'snaps, changes, start = _replay(initial, events, days)\n    return {"scope": [start for s, f in snaps]'),
    ],
    guide=dict(
        prereqs="The same event replay as *Sprint Burndown*. See the lesson *Scrum reports and how they are misused*.",
        intuition="Burnup and burndown come from the same state; burnup reports two numbers per day (scope and done) instead of their difference.",
        hints=[
            "Reuse the replay idea: membership, points, done set, sub-task set.",
            "Scope includes done items; done includes only done items.",
            "Removing a done item lowers both lines.",
        ],
        brute_force="Replaying all events from scratch per day works but repeats work.",
        approach="Replay events day by day; after each day's events, sum points of non-sub-task members (scope) and of those also done (done).\n\n"
                 "**Dry run (example):** scope rises on day 5 (+5) and day 6 (+5); done steps up on days 2, 4, 7 and 9.",
        complexity="Time O(days * n + e); space O(n).",
        pitfalls="- Scope is not fixed at the start; that is the point of the chart.\n- Sub-tasks are excluded from both lines.\n- A reopened item leaves `done` but stays in scope.",
        follow_up="Extend the result with the first day on which done reached scope, or `None` if it never did: the day the lines meet.",
    ),
),
dict(
    id="jira-cycle-lead-time",
    title="Cycle and Lead Time",
    difficulty="Medium",
    pattern="Interval Sums",
    entry="flow_times",
    description=r"""
**Mirrors:** Jira's control chart, where **cycle time** is the time an item spends in the statuses you select as
active work, and time spent after a **reopen** is added; and the common definition of **lead time** as time from
creation to finish.

- `items`: `[key, created_day]` in output order.
- `log`: `[key, day, status]` status changes, sorted by day (entries for the same key are in order).
  Before its first entry, an item is in no active status.
- `active`: the statuses that count as active work (for example `["In Progress", "In Review"]`).
- `done`: the statuses that count as finished.

Consider only items whose **last** status in the log is in `done`. For each, return `[key, cycle, lead]`:

- `cycle`: total days spent in `active` statuses up to the last log entry (each stay in an active status from day
  `a` until the next change on day `b` adds `b - a`; several stays add up);
- `lead`: the day of the last log entry minus `created_day`.

**Example:**
```
items = [["A-1", 0], ["A-2", 1]]
log = [["A-1", 2, "In Progress"], ["A-2", 2, "In Progress"], ["A-1", 4, "In Review"], ["A-1", 5, "Done"],
       ["A-1", 7, "In Progress"], ["A-1", 8, "Done"]]
active = ["In Progress", "In Review"]; done = ["Done"]
```
→ `[["A-1", 4, 8]]` (2-4 and 4-5 and 7-8 are active; A-2 is not finished)
""",
    starter='''def flow_times(items: list, log: list, active: list, done: list) -> list:
    pass
''',
    solution=_FLOW,
    tests=[
        [[["A-1", 0], ["A-2", 1]],
         [["A-1", 2, "In Progress"], ["A-2", 2, "In Progress"], ["A-1", 4, "In Review"], ["A-1", 5, "Done"], ["A-1", 7, "In Progress"], ["A-1", 8, "Done"]],
         ["In Progress", "In Review"], ["Done"]],
        [[], [], ["In Progress"], ["Done"]],
        [[["A-1", 3]], [], ["In Progress"], ["Done"]],
        [[["A-1", 3]], [["A-1", 3, "Done"]], ["In Progress"], ["Done"]],
        [[["A-1", 0]], [["A-1", 1, "In Progress"], ["A-1", 4, "Blocked"], ["A-1", 9, "In Progress"], ["A-1", 10, "Won't Do"]], ["In Progress"], ["Done", "Won't Do"]],
        [[["B-1", 0], ["A-1", 0]], [["A-1", 1, "In Progress"], ["B-1", 2, "In Progress"], ["A-1", 3, "Done"], ["B-1", 6, "Done"]], ["In Progress"], ["Done"]],
        [[["A-1", 0]], [["A-1", 1, "In Progress"], ["A-1", 2, "Done"], ["A-1", 5, "To Do"]], ["In Progress"], ["Done"]],
        [[["A-1", 2]], [["A-1", 2, "In Progress"], ["A-1", 2, "In Review"], ["A-1", 2, "Done"]], ["In Progress", "In Review"], ["Done"]],
        [[["K-%d" % i, i] for i in range(60)],
         [e for i in range(60) for e in ([["K-%d" % i, i + 1, "In Progress"], ["K-%d" % i, i + 3 + i % 4, "QA"]]
                                         + ([["K-%d" % i, i + 6 + i % 4, "Done"]] if i % 5 else [])
                                         + ([["K-%d" % i, i + 8 + i % 4, "In Progress"], ["K-%d" % i, i + 9 + i % 4, "Done"]] if i % 7 == 0 and i % 5 else []))],
         ["In Progress", "QA"], ["Done"]],
    ],
    examples=1,
    wrong_solutions=[
        '''def flow_times(items, log, active, done):
    out = []
    for key, created in items:
        entries = [(d, s) for k, d, s in log if k == key]
        if not entries or entries[-1][1] not in done:
            continue
        first_active = next((d for d, s in entries if s in active), entries[-1][0])
        first_done = next(d for d, s in entries if s in done)
        out.append([key, first_done - first_active, entries[-1][0] - created])
    return out
''',
        '''def flow_times(items, log, active, done):
    active, done = set(active), set(done)
    out = []
    for key, created in items:
        entries = [(d, s) for k, d, s in log if k == key]
        if not entries or entries[-1][1] not in done:
            continue
        finish = entries[-1][0]
        status, since, cycle = None, created, 0
        for day, new in entries:
            if status in active:
                cycle += day - since
            status, since = new, day
        out.append([key, cycle, finish - entries[0][0]])
    return out
''',
    ],
    guide=dict(
        prereqs="Grouping a log by key and summing intervals. See the lessons *Flow reports, forecasting and DORA* and *Kanban*.",
        intuition="Walk each item's history like a stopwatch: whenever the item leaves an active status, add the time since it entered. "
                  "Because you add every active stay, reopened work is counted automatically.",
        hints=[
            "Group log entries by key first so each item's history is in order.",
            "Skip items whose final status is not a done status.",
            "Track `(status, since)`; on each entry, if the old status was active, add `day - since`.",
        ],
        brute_force="Taking 'first time active' to 'first time done' ignores rework after a reopen and time spent blocked outside active statuses.",
        approach="1. Build `by_key`.\n2. For each item with a done final status: replay entries, summing active intervals; lead = last day - created.\n\n"
                 "**Dry run (example):** A-1 active 2-4 (2), 4-5 (1), Done 5-7, active 7-8 (1) → cycle 4; lead 8 - 0 = 8.",
        complexity="Time O(n + L) for n items and L log entries; space O(L).",
        pitfalls="- Time in non-active statuses such as Blocked does not count towards cycle time here.\n- An item that was done and then moved back to To Do is not finished.\n"
                 "- Several entries on the same day add zero days.",
        follow_up="Kanban's work item age is the same stopwatch for unfinished items. Add an `ages` output for items not yet done, measured up to a given `today`.",
    ),
),
dict(
    id="jira-control-chart",
    title="Control Chart Rolling Average",
    difficulty="Medium",
    pattern="Sliding Window",
    entry="control_chart",
    description=r"""
**Mirrors:** Jira's control chart. Atlassian describes its rolling average as **work-based**: each item's cycle time
is averaged with the same number of items before and after it, using a window of **20% of the items displayed,
always odd, and at least 5**. Atlassian does not say how 20% is rounded, so this problem fixes a rule. It also
computes an 85th-percentile value, the usual basis for a Kanban **Service Level Expectation**.

`cycle_times` lists cycle times (in days) in the order the items finished. Let `n` be its length.

- `window = max(5, floor(n * 20 / 100))`, plus 1 if that is even.
- `half = window // 2`. Item `i`'s rolling average is the mean of the items from `i - half` to `i + half`, clipped to
  the list (so the first and last items average fewer values). Round to 2 decimals.
- `sle85` is the **nearest-rank** 85th percentile: sort the values and take the element at position
  `ceil(0.85 * n)` counting from 1.

Return `{"window": window, "rolling": [...], "sle85": value}`, or `{"window": 0, "rolling": [], "sle85": None}`
when the list is empty.

**Example:** `[2, 3, 1, 8, 2, 4]` → window 5 (20% of 6 is 1, so 5), half 2 →
rolling `[2.0, 3.5, 3.2, 3.6, 3.75, 4.67]`, `sle85` = 6th of the sorted values `[1, 2, 2, 3, 4, 8]`... the position
is `ceil(5.1) = 6`, so `8`.
""",
    starter='''def control_chart(cycle_times: list) -> dict:
    pass
''',
    solution=_CONTROL,
    tests=[
        [[2, 3, 1, 8, 2, 4]],
        [[]],
        [[7]],
        [[1, 2]],
        [[3, 3, 3, 3, 3]],
        [[2, 3, 1, 8, 2, 4, 3, 15, 2, 3, 4, 2, 6, 3, 2, 5, 3, 2, 4, 3, 2, 3, 7, 2, 3]],
        [[(i * 7) % 11 + 1 for i in range(30)]],
        [[(i * 13) % 17 + 0.5 for i in range(40)]],
        [[(i * 31) % 23 + 1 for i in range(57)]],
        [[(i * 5) % 9 + 1 for i in range(100)]],
        [[1.5, 2.25, 0.75, 4.0, 3.5, 2.0, 1.0]],
        [list(range(20, 0, -1))],
        [[(i * 3) % 40 + 1 for i in range(40)]],
    ],
    examples=1,
    wrong_solutions=[
        _patch(_CONTROL, "    if window % 2 == 0:\n        window += 1\n", ""),
        _patch(_CONTROL, "    window = max(5, n * 20 // 100)", "    window = n * 20 // 100\n    window = window if window > 0 else 1"),
        _patch(_CONTROL, "    sle85 = ranked[math.ceil(0.85 * n) - 1]", "    sle85 = ranked[int(0.85 * n)]"),
    ],
    guide=dict(
        prereqs="Slicing, integer division, `math.ceil`. See the lesson *Flow reports, forecasting and DORA*.",
        intuition="The rolling average is a centred window that slides along the list one item at a time. Near the ends the window is cut short, "
                  "so average whatever is there. The SLE value is a position in the sorted list.",
        hints=[
            "Compute `window` first, then `half = window // 2`.",
            "Use `cycle_times[max(0, i - half):min(n, i + half + 1)]` for item `i`.",
            "Nearest rank: index `ceil(0.85 * n) - 1` in the sorted list.",
        ],
        brute_force="Summing each window afresh is O(n * w); a running sum makes it O(n), but n is small enough that the direct way is fine.",
        approach="1. Handle the empty list.\n2. Window rule.\n3. For each i, average the clipped window and round.\n4. Sort and pick the nearest-rank 85th percentile.\n\n"
                 "**Dry run (example):** i = 0 averages [2, 3, 1] = 2.0; i = 3 averages [3, 1, 8, 2, 4] = 3.6; i = 5 averages [8, 2, 4] = 4.67.",
        complexity="Time O(n * w + n log n); space O(n).",
        pitfalls="- The minimum of 5 dominates until n reaches 25.\n- An even result must become odd (20 → 21 for n = 100).\n- Use nearest rank, not interpolation, for `sle85`.",
        follow_up="Jira also shades one standard deviation around the rolling average. Add a `band` list giving the population standard deviation of each window.",
    ),
),
dict(
    id="jira-cfd",
    title="Cumulative Flow Counts",
    difficulty="Medium",
    pattern="Simulation / Counting",
    entry="cfd",
    description=r"""
**Mirrors:** Jira's cumulative flow diagram. Each band is a board column; the leftmost column is To Do and the
rightmost is Done. Atlassian's worked example (5 items in To Do, 2 moved to In Progress, 1 to Done, then that one
moved back to To Do, after which it no longer counts in Done or In Progress while To Do stays at 5) is reproduced
exactly by counting, for each column, the items currently **in that column or any column to its right**.

- `columns`: board columns, left to right.
- `moves`: `[day, key, column]`, sorted by day: the item is in `column` from that day on. An item's first move puts it
  on the board. Moves to unknown columns are ignored.
- `days`: report days `0..days-1`, applying each day's moves (in order) before counting.

Return a list with one row per day; row `d` lists, for each column `c`, the number of items whose current column is
`c` or further right.

**Example:** columns `["To Do", "In Progress", "Done"]`; moves
`[[0,"A","To Do"],[0,"B","To Do"],[1,"A","In Progress"],[2,"A","Done"],[3,"A","To Do"]]`; `days = 4` →
`[[2,0,0],[2,1,0],[2,1,1],[2,0,0]]`
""",
    starter='''def cfd(columns: list, moves: list, days: int) -> list:
    pass
''',
    solution=_CFD,
    tests=[
        [["To Do", "In Progress", "Done"], [[0, "A", "To Do"], [0, "B", "To Do"], [1, "A", "In Progress"], [2, "A", "Done"], [3, "A", "To Do"]], 4],
        [["To Do", "In Progress", "Done"],
         [[0, k, "To Do"] for k in "ABCDE"] + [[1, "A", "In Progress"], [1, "B", "In Progress"], [2, "A", "Done"], [3, "A", "To Do"]], 4],
        [["To Do", "Done"], [], 3],
        [["To Do", "Done"], [[0, "A", "To Do"]], 0],
        [["To Do", "Doing", "Done"], [[0, "A", "Doing"], [1, "A", "Nowhere"], [2, "B", "Done"]], 3],
        [["To Do", "In Progress", "Review", "Done"],
         [[0, "A", "To Do"], [0, "B", "To Do"], [0, "C", "To Do"], [1, "D", "To Do"], [1, "A", "In Progress"], [2, "B", "In Progress"],
          [3, "A", "Review"], [4, "B", "Review"], [4, "C", "In Progress"], [5, "E", "To Do"], [6, "A", "Done"], [7, "C", "Review"],
          [8, "D", "In Progress"], [9, "B", "Done"]], 10],
        [["A", "B"], [[0, "x", "B"], [0, "x", "A"], [0, "y", "B"]], 2],
        [["To Do", "Dev", "QA", "Done"],
         [[d, "K-%d" % ((d * 7 + j) % 25), ["To Do", "Dev", "QA", "Done"][(d + j) % 4]] for d in range(30) for j in range(3)], 30],
    ],
    examples=1,
    wrong_solutions=[
        '''def cfd(columns, moves, days):
    index = {c: i for i, c in enumerate(columns)}
    where = {}
    out = []
    for d in range(days):
        for day, key, col in moves:
            if day == d and col in index:
                where[key] = index[col]
        out.append([sum(1 for p in where.values() if p == c) for c in range(len(columns))])
    return out
''',
        '''def cfd(columns, moves, days):
    index = {c: i for i, c in enumerate(columns)}
    best = {}
    out = []
    for d in range(days):
        for day, key, col in moves:
            if day == d and col in index:
                best[key] = max(best.get(key, 0), index[col])
        out.append([sum(1 for p in best.values() if p >= c) for c in range(len(columns))])
    return out
''',
    ],
    guide=dict(
        prereqs="Dicts for current positions and counting with a condition. See the lesson *Flow reports, forecasting and DORA*.",
        intuition="Track only where each item is now. A band's top edge counts items that have reached that column or gone beyond, so the first "
                  "column counts every item on the board and the last counts finished items.",
        hints=[
            "Keep `where[key] = column index`.",
            "Apply all moves of day `d` before counting day `d`.",
            "Count `p >= c`, not `p == c`; the band thickness is the difference between neighbouring counts.",
        ],
        brute_force="Remembering the furthest column an item ever reached would make a moved-back item still count in Done, which contradicts Atlassian's example.",
        approach="Group moves by day; for each day update positions, then for each column count positions at or to its right.\n\n"
                 "**Dry run (example):** day 2 A is in Done → [2, 1, 1]; day 3 A moves back to To Do → [2, 0, 0].",
        complexity="Time O(days * (items * columns) + moves); space O(items).",
        pitfalls="- Unknown columns: ignore the move, keep the previous position.\n- Several moves of one item on the same day: the last wins.\n- Report days start at 0 and stop before `days`.",
        follow_up="Turn the counts into band thicknesses (items currently in each column) and flag any column whose thickness grew on five consecutive days: a candidate bottleneck.",
    ),
),
dict(
    id="jira-monte-carlo-how-many",
    title="Monte Carlo: How Many Items",
    difficulty="Medium",
    pattern="Simulation / Percentiles",
    entry="how_many",
    description=r"""
**Mirrors:** probabilistic forecasting with Monte Carlo simulation as described by Scrum.org (2020): sample the team's
historical throughput thousands of times and report results at confidence levels such as 50%, 85% and 95%, answering
"how many items can we finish by a date?".

`history` is a non-empty list of items finished per working day. Simulate `trials` futures of `days` working days.
To make results reproducible and gradable, follow this exact procedure:

1. Call `random.seed(42)` once.
2. For each trial in order, and for each of the `days` days in order, add `random.choice(history)` to that trial's total.
3. Sort the totals ascending.
4. For each confidence `p` in `(50, 85, 95)`, the answer is `totals[int((100 - p) * trials / 100)]`: the number of
   items that at least `p`% of trials reached.

Return the three answers as a list `[at_50, at_85, at_95]` (so they never increase).

**Example:** `history = [0, 2, 1, 3, 0, 2, 4, 1, 2, 0, 3, 2, 1, 2, 3], days = 10, trials = 10000` →
`[17, 13, 11]` (the lesson's simulation).
""",
    starter='''def how_many(history: list, days: int, trials: int) -> list:
    pass
''',
    solution=_HOW_MANY,
    tests=[
        [_HIST, 10, 10000],
        [[1], 10, 50],
        [[0, 5], 1, 1000],
        [_HIST, 0, 100],
        [[3, 0, 0, 1, 7, 2], 15, 2000],
        [[2, 2, 3], 5, 1],
        [list(range(10)), 20, 3000],
        [[0, 0, 0, 1], 30, 500],
    ],
    examples=1,
    wrong_solutions=[
        _patch(_HOW_MANY, "    return [totals[int((100 - p) * trials / 100)] for p in (50, 85, 95)]",
               "    return [totals[min(trials - 1, int(p * trials / 100))] for p in (50, 85, 95)]"),
        _patch(_HOW_MANY, "    random.seed(42)\n", ""),
        _patch(_HOW_MANY, "            total += random.choice(history)", "            total += history[int(random.random() * len(history))]"),
    ],
    guide=dict(
        prereqs="The `random` module, sorting, and percentiles. See the lesson *Flow reports, forecasting and DORA*.",
        intuition="Each trial invents one plausible future by replaying random past days. After thousands of trials, the sorted totals show "
                  "how likely each outcome is. For 'how many', being more confident means promising fewer items, so read from the low end.",
        hints=[
            "Seed once, before any trial; calling `random.seed(42)` inside the loop would repeat the same trial.",
            "Use `random.choice(history)` exactly as described; other random calls consume the random stream differently.",
            "Index `int((100 - p) * trials / 100)` in the ascending list.",
        ],
        brute_force="Enumerating every possible sequence of days is exponential; sampling is the whole point.",
        approach="Seed, run trials (outer loop) over days (inner loop), sort, read three indexes.\n\n**Check:** with `history = [1]` every trial totals `days`, so all three answers equal `days`.",
        complexity="Time O(trials * days + trials log trials); space O(trials).",
        pitfalls="- Reading the 85% value from the top of the list answers a different question (an optimistic outcome).\n- Loop order matters for reproducibility.\n"
                 "- With `days = 0` every total is 0.",
        follow_up="Teams often forecast by week rather than by day. Change the input to weekly throughput and compare the spread of results; why is daily sampling usually smoother?",
    ),
),
dict(
    id="jira-monte-carlo-when",
    title="Monte Carlo: When Will It Be Done",
    difficulty="Hard",
    pattern="Simulation / Dates",
    entry="when_done",
    description=r"""
**Mirrors:** the "when will N items be done?" Monte Carlo forecast described by Scrum.org (2020), where results are
stated as a range with a probability (for example "85% chance within 27 working days") and turned into a delivery
date by adding a start date.

`history` lists items finished per working day; `target` (at least 1) is the number of items to finish; `trials`
is the number of simulations; `start_date` is an ISO date `"YYYY-MM-DD"`.

1. If `sum(history) == 0`, return `[]` (the work would never finish).
2. Call `random.seed(42)` once. For each trial: start with `done = 0, days = 0`; while `done < target`, add
   `random.choice(history)` to `done` and add 1 to `days`. Record `days`.
3. Sort the recorded days ascending. For each `p` in `(50, 85, 95)`, take `d = days[ceil(p * trials / 100) - 1]`:
   the number of working days within which `p`% of trials finished.
4. Convert `d` to a date: count working days (Monday to Friday) starting **at** `start_date` if it is a weekday
   (otherwise at the next Monday); the `d`-th working day is the finish date.

Return `[[50, d50, date50], [85, d85, date85], [95, d95, date95]]`.

**Example:** `history = [0, 2, 1, 3, 0, 2, 4, 1, 2, 0, 3, 2, 1, 2, 3], target = 40, trials = 10000,
start_date = "2026-04-06"` (a Monday) →
`[[50, 23, "2026-05-06"], [85, 27, "2026-05-12"], [95, 29, "2026-05-14"]]`
""",
    starter='''def when_done(history: list, target: int, trials: int, start_date: str) -> list:
    pass
''',
    solution=_WHEN,
    tests=[
        [_HIST, 40, 10000, "2026-04-06"],
        [[0, 0], 5, 100, "2026-04-06"],
        [[1], 3, 10, "2026-04-06"],
        [[1], 1, 10, "2026-04-11"],
        [[1], 5, 10, "2026-04-10"],
        [[0, 1, 2], 12, 2000, "2026-12-24"],
        [[5, 0, 0, 0], 20, 3000, "2026-02-27"],
        [[2, 3, 1, 0, 4], 60, 1500, "2026-06-01"],
        [[1, 1, 2], 7, 7, "2026-03-03"],
    ],
    examples=1,
    wrong_solutions=[
        _patch(_WHEN, "        d = needed[math.ceil(p * trials / 100) - 1]", "        d = needed[int(p * trials / 100) - 1]"),
        _patch(_WHEN, "            if day.weekday() < 5:\n                count += 1\n                if count == d:\n                    break\n",
               "            count += 1\n            if count == d:\n                break\n"),
        _patch(_WHEN, "        while done < target:", "        while done <= target:"),
    ],
    guide=dict(
        prereqs="`random`, sorting, `math.ceil`, and `datetime.date` with `timedelta` and `weekday()`. See the lesson *Flow reports, forecasting and DORA*.",
        intuition="Each trial asks 'how many working days would it take if the future looked like randomly chosen past days?'. Sorting the answers "
                  "gives a distribution; for 'when', higher confidence means a later date, so read further up the list.",
        hints=[
            "Guard against a history of all zeros before simulating, or the loop never ends.",
            "Use nearest rank with `ceil(p * trials / 100) - 1` as the index.",
            "Walk forward one calendar day at a time, counting only weekdays, until you have counted `d` of them.",
            "If the start date is a Saturday or Sunday, the walk naturally skips to Monday.",
        ],
        brute_force="Adding `d` calendar days ignores weekends and gives dates that are too early.",
        approach="1. Zero-history guard.\n2. Seed; simulate trials; sort.\n3. For each p: index, then convert working days to a date by walking the calendar.\n\n"
                 "**Check:** with `history = [1]` and `target = 3`, every trial takes 3 days; from Monday 6 April 2026 the 3rd working day is Wednesday 8 April.",
        complexity="Time O(trials * days_per_trial + trials log trials); space O(trials).",
        pitfalls="- `int(85 * 7 / 100)` is 5 but `ceil` gives 6: the floor version under-states the confidence.\n- Count the start date itself if it is a weekday.\n"
                 "- `done < target`, not `<=`: reaching the target exactly finishes the work.",
        follow_up="Public holidays (for example Singapore's) also stop work. Add a `holidays` list of ISO dates that the calendar walk skips.",
    ),
),
]
