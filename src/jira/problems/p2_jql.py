def _patch(src, old, new):
    if old not in src:
        raise ValueError("patch target not found: " + old[:60])
    return src.replace(old, new, 1)


_TOKENIZE = r'''import re

KEYWORDS = {"AND", "OR", "NOT", "IN", "IS", "EMPTY", "NULL", "ORDER", "BY", "ASC", "DESC"}
WORD_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-+")

def tokenize(q):
    toks, i, n = [], 0, len(q)
    while i < n:
        c = q[i]
        if c in " \t\n\r":
            i += 1
        elif c in "\"'":
            j, buf = i + 1, []
            while j < n and q[j] != c:
                if q[j] == "\\" and j + 1 < n:
                    j += 1
                buf.append(q[j])
                j += 1
            if j >= n:
                return [["ERROR", i]]
            toks.append(["STRING", "".join(buf)])
            i = j + 1
        elif c == "(":
            toks.append(["LPAREN", "("])
            i += 1
        elif c == ")":
            toks.append(["RPAREN", ")"])
            i += 1
        elif c == ",":
            toks.append(["COMMA", ","])
            i += 1
        elif q[i:i + 2] in ("!=", ">=", "<=", "!~"):
            toks.append(["OP", q[i:i + 2]])
            i += 2
        elif c in "=<>~":
            toks.append(["OP", c])
            i += 1
        elif c in WORD_CHARS:
            j = i
            while j < n and q[j] in WORD_CHARS:
                j += 1
            w = q[i:j]
            if w.upper() in KEYWORDS:
                toks.append(["KEYWORD", w.upper()])
            else:
                toks.append(["WORD", w])
            i = j
        else:
            return [["ERROR", i]]
    return toks
'''

_CORE = _TOKENIZE + r'''
ALIAS = {"issuetype": "type", "issuekey": "key"}
DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
PRIORITY = {"lowest": 1, "low": 2, "medium": 3, "high": 4, "highest": 5}

def parse_query(q):
    toks = tokenize(q)
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else None

    def take():
        t = toks[pos[0]]
        pos[0] += 1
        return t

    def is_kw(k):
        t = peek()
        return t is not None and t[0] == "KEYWORD" and t[1] == k

    def field_name():
        f = take()[1].lower()
        return ALIAS.get(f, f)

    def clause():
        field = field_name()
        if is_kw("IS"):
            take()
            neg = False
            if is_kw("NOT"):
                take()
                neg = True
            take()
            return ("notempty" if neg else "empty", field)
        neg = False
        if is_kw("NOT"):
            take()
            neg = True
        if is_kw("IN"):
            take()
            take()
            vals = [take()[1]]
            while peek() is not None and peek()[0] == "COMMA":
                take()
                vals.append(take()[1])
            take()
            return ("notin" if neg else "in", field, vals)
        op = take()[1]
        return ("cmp", field, op, take()[1])

    def atom():
        if is_kw("NOT"):
            take()
            return ("not", atom())
        if peek() is not None and peek()[0] == "LPAREN":
            take()
            node = or_expr()
            take()
            return node
        return clause()

    def and_expr():
        node = atom()
        while is_kw("AND"):
            take()
            node = ("and", node, atom())
        return node

    def or_expr():
        node = and_expr()
        while is_kw("OR"):
            take()
            node = ("or", node, and_expr())
        return node

    where = None
    if toks and not is_kw("ORDER"):
        where = or_expr()
    order = []
    if is_kw("ORDER"):
        take()
        take()
        while True:
            f = field_name()
            d = "ASC"
            if is_kw("ASC") or is_kw("DESC"):
                d = take()[1]
            order.append((f, d))
            if peek() is not None and peek()[0] == "COMMA":
                take()
                continue
            break
    return where, order

def _empty(v):
    return v is None or v == [] or v == ""

def _vals(v):
    if _empty(v):
        return []
    return list(v) if isinstance(v, list) else [v]

def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)

def _eq(x, s):
    if _num(x):
        try:
            return float(s) == float(x)
        except ValueError:
            return False
    return str(x).lower() == s.lower()

def _order_cmp(x, s):
    if _num(x):
        try:
            y = float(s)
        except ValueError:
            return None
        return (x > y) - (x < y)
    if isinstance(x, str) and DATE.match(x) and DATE.match(s):
        return (x > s) - (x < s)
    return None

def _words(t):
    return [w for w in re.split(r"[^a-z0-9]+", t.lower()) if w]

def matches(issue, node):
    kind = node[0]
    if kind == "and":
        return matches(issue, node[1]) and matches(issue, node[2])
    if kind == "or":
        return matches(issue, node[1]) or matches(issue, node[2])
    if kind == "not":
        return not matches(issue, node[1])
    vals = _vals(issue.get(node[1]))
    if kind == "empty":
        return not vals
    if kind == "notempty":
        return bool(vals)
    if kind == "in":
        return any(_eq(x, s) for x in vals for s in node[2])
    if kind == "notin":
        return bool(vals) and not any(_eq(x, s) for x in vals for s in node[2])
    op, s = node[2], node[3]
    if op == "=":
        return any(_eq(x, s) for x in vals)
    if op == "!=":
        return bool(vals) and not any(_eq(x, s) for x in vals)
    if op in ("~", "!~"):
        have = set(w for x in vals for w in _words(str(x)))
        hit = bool(vals) and all(w in have for w in _words(s))
        return hit if op == "~" else (bool(vals) and not hit)
    for x in vals:
        c = _order_cmp(x, s)
        if c is None:
            continue
        if (op == ">" and c > 0) or (op == ">=" and c >= 0) or (op == "<" and c < 0) or (op == "<=" and c <= 0):
            return True
    return False

def _sort_key(issue, f):
    v = issue.get(f)
    if _empty(v):
        return None
    if f == "priority":
        return PRIORITY.get(str(v).lower(), 0)
    if f == "key":
        p, num = str(v).rsplit("-", 1)
        return (p.lower(), int(num))
    if isinstance(v, list):
        return ",".join(str(x).lower() for x in v)
    if _num(v):
        return v
    return str(v).lower()

def _sorted(issues, order):
    import functools
    idx = list(range(len(issues)))

    def cmp(a, b):
        for f, d in order:
            ka, kb = _sort_key(issues[a], f), _sort_key(issues[b], f)
            if ka == kb:
                continue
            if ka is None:
                return 1
            if kb is None:
                return -1
            r = -1 if ka < kb else 1
            return -r if d == "DESC" else r
        return a - b

    return [issues[i] for i in sorted(idx, key=functools.cmp_to_key(cmp))]
'''


def _issue(key, type_, summary, status, cat, assignee, priority, labels, points, created, parent):
    return {"key": key, "type": type_, "summary": summary, "status": status, "statuscategory": cat,
            "assignee": assignee, "priority": priority, "labels": labels, "points": points,
            "created": created, "parent": parent, "project": key.split("-")[0]}


ISSUES = [
    _issue("SHOP-1", "Story", "Apply promo code at checkout", "Done", "Done", "farah", "High", ["checkout", "cny"], 5, "2026-02-20", "SHOP-10"),
    _issue("SHOP-2", "Bug", "Promo code accepted on empty cart", "In Progress", "In Progress", "farah", "Highest", ["checkout"], 2, "2026-03-04", "SHOP-10"),
    _issue("SHOP-3", "Story", "Show promo code on receipt", "To Do", "To Do", None, "Medium", ["cny"], 3, "2026-03-02", "SHOP-10"),
    _issue("SHOP-4", "Task", "Rotate payment API key", "In Review", "In Progress", "wei", "High", [], None, "2026-03-06", None),
    _issue("SHOP-5", "Bug", "Receipt email missing logo", "To Do", "To Do", "aisha", "Low", ["email"], 1, "2026-02-11", None),
    _issue("SHOP-6", "Story", "Saved cards list", "In Progress", "In Progress", "aisha", "Medium", ["cards"], 8, "2026-02-25", None),
    _issue("SHOP-10", "Epic", "Promo codes", "In Progress", "In Progress", "siti", "Medium", ["cny"], None, "2026-02-01", None),
    _issue("PAY-7", "Bug", "Refund fails for e-wallet payments", "In Progress", "In Progress", "wei", "Highest", ["refunds"], 3, "2026-03-09", None),
    _issue("PAY-8", "Story", "Partial refunds for card payments", "To Do", "To Do", None, "High", ["refunds"], 13, "2026-02-27", None),
    _issue("PAY-9", "Task", "Upgrade payment SDK", "Done", "Done", "farah", "Low", [], 2, "2026-01-15", None),
]

_BIG = [
    _issue("BIG-%d" % i, ["Story", "Bug", "Task"][i % 3], "Item %d %s" % (i, ["refund flow", "login page", "promo code"][i % 3]),
           ["To Do", "In Progress", "Done"][i % 3 if i % 5 else 0], ["To Do", "In Progress", "Done"][i % 3 if i % 5 else 0],
           [None, "farah", "wei", "aisha"][i % 4], ["Lowest", "Low", "Medium", "High", "Highest"][i % 5],
           [["a"], ["b", "c"], []][i % 3], (i % 13) or None, "2026-%02d-%02d" % (1 + i % 3, 1 + i % 28), None)
    for i in range(1, 301)
]

_ENTRY_CLAUSE = '''
def run_clause(issues, clause):
    where, _ = parse_query(clause)
    return [it["key"] for it in issues if matches(it, where)]
'''
_ENTRY_WHERE = '''
def run_where(issues, query):
    where, _ = parse_query(query)
    return [it["key"] for it in issues if matches(it, where)]
'''
_ENTRY_QUERY = '''
def run_query(issues, query):
    where, order = parse_query(query)
    hits = [it for it in issues if where is None or matches(it, where)]
    return [it["key"] for it in _sorted(hits, order)]
'''

_DATA_NOTE = r"""
Each work item is a dict with lower-case field names, for example
`{"key": "SHOP-4", "type": "Task", "summary": "Rotate payment API key", "status": "In Review",
"statuscategory": "In Progress", "assignee": "wei", "priority": "High", "labels": [], "points": None,
"created": "2026-03-06", "parent": None, "project": "SHOP"}`. A value is a string, a number, `None`, or a list
of strings (multi-valued fields such as `labels`). `None`, `""` and `[]` count as **empty**.
The sample tests use the ten items from the lesson *JQL basics*.
"""

_SEMANTICS = r"""
**Rules for a clause** (a simplified model of Jira's documented behaviour):

| Clause | Matches when |
|---|---|
| `f = v` | some value of `f` equals `v` |
| `f != v` | `f` is **not empty** and no value equals `v` (Jira: `!=` does not match empty fields) |
| `f IN (v1, v2)` | some value equals one of the list |
| `f NOT IN (v1, v2)` | `f` is not empty and no value equals any of the list |
| `f > v`, `>=`, `<`, `<=` | some value compares that way; only for numbers, and for `YYYY-MM-DD` date strings; otherwise no match (so `priority > Medium` matches nothing here, although real Jira orders priorities) |
| `f ~ v` | `f` is not empty and every word of `v` appears as a whole word in `f` (no stemming or wildcards) |
| `f !~ v` | `f` is not empty and `f ~ v` is false |
| `f IS EMPTY` / `f IS NOT EMPTY` | `f` is empty / not empty (`NULL` is a synonym of `EMPTY`) |

- Field names and keywords are case-insensitive; `issuetype` means `type` and `issuekey` means `key`.
- String comparison is case-insensitive. If the item's value is a number, `v` is compared as a number (a
  non-numeric `v` never matches).
- Words for `~` are runs of letters and digits, compared in lower case.
- Values are a bare word (letters, digits and `_ . - +`) or a quoted string (`"..."` or `'...'`).
"""

_TOKEN_TESTS = [
    ['project = SHOP AND status = "In Progress"'],
    ["labels in (cny, refunds) order by created desc"],
    [""],
    ["assignee != farah OR assignee IS EMPTY"],
    ["created >= -7d AND points<=5"],
    ['summary ~ "say \\"hi\\" now"'],
    ["summary ~ 'single quoted'"],
    ['status = "In Progress'],
    ["priority ! High"],
    ["fixVersion !~ 2026.04 AND key = SHOP-10"],
    ["NOT (type = Bug)"],
    ["status = Done @ x"],
    ['summary ~ "ends with backslash \\"'],
    ["Order By Rank Asc, created DESC"],
    [" ".join("f%d = v%d AND" % (i, i) for i in range(200)) + " last = x"],
]

_CLAUSE_TESTS = [
    [ISSUES, "assignee != farah"],
    [ISSUES, 'summary ~ "promo code"'],
    [ISSUES, "project = SHOP"],
    [ISSUES, "labels = cny"],
    [ISSUES, "assignee IS EMPTY"],
    [ISSUES, "assignee is not null"],
    [ISSUES, "priority IN (High, Highest)"],
    [ISSUES, "assignee NOT IN (farah, wei)"],
    [ISSUES, "points >= 5"],
    [ISSUES, "points < 3"],
    [ISSUES, 'created >= "2026-03-01"'],
    [ISSUES, "priority > Medium"],
    [ISSUES, "summary ~ promo"],
    [ISSUES, "summary !~ refund"],
    [ISSUES, "labels != cny"],
    [ISSUES, 'STATUS = "in progress"'],
    [ISSUES, "issuetype = bug"],
    [ISSUES, "points = 13"],
    [ISSUES, "points = abc"],
    [ISSUES, "labels IS EMPTY"],
    [ISSUES, "parent = SHOP-10"],
    [ISSUES, "summary ~ codes"],
    [_BIG, "assignee != wei"],
    [_BIG, "labels NOT IN (a, c)"],
]

_WHERE_TESTS = [
    [ISSUES, "project = SHOP AND type = Bug"],
    [ISSUES, "type = Bug OR priority = Highest"],
    [ISSUES, "project = SHOP AND (type = Bug OR priority = Highest)"],
    [ISSUES, "project = SHOP AND type = Bug OR priority = Highest"],
    [ISSUES, "type = Bug OR priority = Highest AND project = SHOP"],
    [ISSUES, "NOT type = Story"],
    [ISSUES, "NOT type = Story AND assignee = farah"],
    [ISSUES, "NOT (type = Story AND assignee = farah)"],
    [ISSUES, "assignee != farah OR assignee IS EMPTY"],
    [ISSUES, "project IN (SHOP, PAY) AND type IN (Bug, Task) AND statuscategory != Done AND priority IN (High, Highest) AND (assignee != farah OR assignee IS EMPTY)"],
    [ISSUES, "((labels = cny))"],
    [ISSUES, "labels != cny AND type != Epic"],
    [ISSUES, "assignee != farah AND priority != Low"],
    [ISSUES, "NOT NOT project = PAY"],
    [ISSUES, "a = 1 OR b = 2 OR labels = refunds"],
    [ISSUES, "summary ~ promo and not status = done or points > 10"],
    [_BIG, "(type = Bug OR type = Task) AND NOT assignee IS EMPTY AND points >= 7"],
    [_BIG, "priority = Highest OR priority = Lowest AND labels = a"],
]

_QUERY_TESTS = [
    [ISSUES, "statuscategory != Done ORDER BY priority DESC, created ASC"],
    [ISSUES, "project = SHOP AND statuscategory != Done ORDER BY priority DESC, created ASC"],
    [ISSUES, "ORDER BY key"],
    [ISSUES, "ORDER BY key DESC"],
    [ISSUES, "ORDER BY points DESC"],
    [ISSUES, "ORDER BY points"],
    [ISSUES, "ORDER BY assignee, key DESC"],
    [ISSUES, "labels IN (cny, refunds) ORDER BY created DESC"],
    [ISSUES, "type = Bug"],
    [ISSUES, "ORDER BY priority, summary"],
    [ISSUES, "order by labels desc"],
    [ISSUES, "project = NONE ORDER BY key"],
    [_BIG, "points >= 3 ORDER BY priority DESC, points ASC, key DESC"],
    [_BIG, "ORDER BY assignee DESC, created"],
]

PROBLEMS = [
dict(
    id="jira-workflow-transitions",
    title="Workflow Transitions",
    difficulty="Medium",
    pattern="State Machine",
    entry="simulate",
    description=r"""
**Mirrors:** a Jira workflow, a set of statuses joined by named one-way transitions where a transition that does
not exist from the current status is not available; and the control chart's rule that time spent after an
item is **reopened** still counts towards its cycle time.

- `workflow`: dict `status -> {transition_name: target_status}`.
- `category`: dict `status -> "To Do" | "In Progress" | "Done"` (the status category).
- `start`: the status the item is created in, on day `created`.
- `events`: a list of `[day, transition_name]` in time order (days never decrease). Transition names are
  case-sensitive.
- `end`: the day you stop measuring (`end >=` every event day).

Apply each event. If the current status has no transition with that name, the event is **rejected** and nothing
changes. Return a dict:

- `"final"`: the final status;
- `"rejected"`: the 0-based indexes of rejected events;
- `"reopens"`: how many accepted transitions went from a status in category `Done` to a status **not** in `Done`;
- `"in_progress_days"`: total days spent in statuses of category `In Progress`, from `created` to `end`
  (a status entered on day `a` and left on day `b` contributes `b - a`).

**Example:**
```
workflow = {"To Do": {"Start": "In Progress"}, "In Progress": {"Finish": "Done"}, "Done": {"Reopen": "In Progress"}}
category = {"To Do": "To Do", "In Progress": "In Progress", "Done": "Done"}
simulate(workflow, category, "To Do", 0, [[1, "Start"], [4, "Finish"], [5, "Finish"], [6, "Reopen"], [8, "Finish"]], 10)
```
→ `{"final": "Done", "rejected": [2], "reopens": 1, "in_progress_days": 5}` (days 1-4 and 6-8)
""",
    starter='''def simulate(workflow: dict, category: dict, start: str, created: int, events: list, end: int) -> dict:
    pass
''',
    solution='''def simulate(workflow, category, start, created, events, end):
    status, since = start, created
    rejected, reopens, spent = [], 0, {}
    for i, (day, name) in enumerate(events):
        target = workflow.get(status, {}).get(name)
        if target is None:
            rejected.append(i)
            continue
        cat = category[status]
        spent[cat] = spent.get(cat, 0) + (day - since)
        if cat == "Done" and category[target] != "Done":
            reopens += 1
        status, since = target, day
    cat = category[status]
    spent[cat] = spent.get(cat, 0) + (end - since)
    return {"final": status, "rejected": rejected, "reopens": reopens, "in_progress_days": spent.get("In Progress", 0)}
''',
    tests=[
        [{"To Do": {"Start": "In Progress"}, "In Progress": {"Finish": "Done"}, "Done": {"Reopen": "In Progress"}},
         {"To Do": "To Do", "In Progress": "In Progress", "Done": "Done"}, "To Do", 0,
         [[1, "Start"], [4, "Finish"], [5, "Finish"], [6, "Reopen"], [8, "Finish"]], 10],
        [{"To Do": {"Start": "In Progress"}}, {"To Do": "To Do", "In Progress": "In Progress"}, "To Do", 3, [], 9],
        [{"To Do": {"Start": "In Progress"}}, {"To Do": "To Do", "In Progress": "In Progress"}, "To Do", 3, [[5, "Start"]], 9],
        [{"To Do": {"Start": "In Progress"}}, {"To Do": "To Do", "In Progress": "In Progress"}, "To Do", 0, [[1, "start"], [2, "Begin"]], 4],
        [{"To Do": {"Start work": "In Progress", "Decline": "Won't Do"},
          "In Progress": {"Submit for review": "In Review", "Decline": "Won't Do"},
          "In Review": {"Request changes": "In Progress", "Approve": "QA"},
          "QA": {"Fail QA": "In Progress", "Pass QA": "Done"},
          "Done": {"Reopen": "In Progress"}, "Won't Do": {}},
         {"To Do": "To Do", "In Progress": "In Progress", "In Review": "In Progress", "QA": "In Progress", "Done": "Done", "Won't Do": "Done"},
         "To Do", 0,
         [[2, "Start work"], [4, "Submit for review"], [5, "Request changes"], [6, "Submit for review"], [7, "Approve"],
          [8, "Fail QA"], [9, "Submit for review"], [10, "Approve"], [11, "Pass QA"], [15, "Reopen"], [16, "Decline"], [20, "Reopen"]], 25],
        [{"Open": {"Close": "Closed", "Drop": "Dropped"}, "Closed": {"Drop": "Dropped"}, "Dropped": {"Revive": "Open"}},
         {"Open": "In Progress", "Closed": "Done", "Dropped": "Done"}, "Open", 0,
         [[2, "Close"], [3, "Drop"], [7, "Revive"], [9, "Close"]], 12],
        [{"A": {"go": "B"}, "B": {"go": "A"}}, {"A": "In Progress", "B": "Done"}, "A", 0,
         [[d, "go"] for d in range(1, 41)], 45],
        [{"A": {"x": "B"}, "B": {}}, {"A": "To Do", "B": "In Progress"}, "A", 10, [[10, "x"], [10, "x"]], 10],
        [{"To Do": {"Start": "Doing"}, "Doing": {"Done": "Done"}, "Done": {}},
         {"To Do": "To Do", "Doing": "In Progress", "Done": "Done"}, "To Do", 0,
         [[i, ["Done", "Start", "Start", "Done", "Done"][i % 5]] for i in range(1, 30)], 30],
    ],
    examples=1,
    wrong_solutions=[
        '''def simulate(workflow, category, start, created, events, end):
    status, since = start, created
    rejected, reopens, spent, finished = [], 0, 0, False
    for i, (day, name) in enumerate(events):
        target = workflow.get(status, {}).get(name)
        if target is None:
            rejected.append(i)
            continue
        if category[status] == "In Progress" and not finished:
            spent += day - since
        if category[status] == "Done" and category[target] != "Done":
            reopens += 1
        if category[target] == "Done":
            finished = True
        status, since = target, day
    if category[status] == "In Progress" and not finished:
        spent += end - since
    return {"final": status, "rejected": rejected, "reopens": reopens, "in_progress_days": spent}
''',
        '''def simulate(workflow, category, start, created, events, end):
    status, since = start, created
    rejected, reopens, spent = [], 0, {}
    for i, (day, name) in enumerate(events):
        target = workflow.get(status, {}).get(name)
        if target is None:
            rejected.append(i)
            continue
        cat = category[status]
        spent[cat] = spent.get(cat, 0) + (day - since)
        if cat == "Done":
            reopens += 1
        status, since = target, day
    cat = category[status]
    spent[cat] = spent.get(cat, 0) + (end - since)
    return {"final": status, "rejected": rejected, "reopens": reopens, "in_progress_days": spent.get("In Progress", 0)}
''',
        '''def simulate(workflow, category, start, created, events, end):
    status, since = start, created
    rejected, reopens, spent = [], 0, {}
    for i, (day, name) in enumerate(events):
        target = workflow.get(status, {}).get(name)
        if target is None:
            rejected.append(i)
            continue
        cat = category[status]
        spent[cat] = spent.get(cat, 0) + (day - since)
        if cat == "Done" and category[target] != "Done":
            reopens += 1
        status, since = target, day
    return {"final": status, "rejected": rejected, "reopens": reopens, "in_progress_days": spent.get("In Progress", 0)}
''',
    ],
    guide=dict(
        prereqs="Dicts of dicts and a running 'current state'. See the lesson *Workflows: statuses, transitions and status categories*.",
        intuition="Keep two pieces of state: the current status and the day you entered it. Each accepted transition closes the current "
                  "interval (add its length to the category's total) and opens a new one. Rejected events change nothing. Close the last "
                  "interval at `end`.",
        hints=[
            "`workflow.get(status, {}).get(name)` is `None` exactly when the transition does not exist.",
            "Before switching status, add `day - since` to the total of the **current** status's category.",
            "A reopen is a Done-category status moving to a non-Done one; Done to Won't Do is not a reopen.",
            "Do not forget the time from the last accepted event to `end`.",
        ],
        brute_force="You could expand every day into a list of statuses and count, but that is O(total days) and awkward; interval sums are simpler.",
        approach="1. `status, since = start, created`.\n2. For each event: look up the target; reject or close the interval, count reopens, move.\n"
                 "3. Add the final interval up to `end`.\n\n**Dry run (example):** To Do 0-1, In Progress 1-4 (3 days), Done 4-6 (the event on "
                 "day 5 is rejected), In Progress 6-8 (2 days), Done 8-10. In-progress total 5, one reopen.",
        complexity="Time O(e) for e events; space O(e) for the rejected list.",
        pitfalls="- Transition names are case-sensitive: `start` is not `Start`.\n- Several statuses can share a category (In Review and QA are both In Progress).\n"
                 "- Time after a reopen counts, as in Jira's control chart.\n- Events on the same day add zero days but still change the status.",
        follow_up="Jira's control chart lets you choose which columns count as cycle time. Change the function to take a set of statuses to measure instead of a category.",
    ),
),
dict(
    id="jira-jql-tokenize",
    title="Mini-JQL: Tokenizer",
    difficulty="Medium",
    pattern="String Parsing",
    entry="tokenize",
    description=r"""
**Mirrors:** the structure of a JQL query: fields, operators, values (bare or quoted with single or double quotes),
parentheses and commas for lists, and keywords such as `AND`, `OR`, `NOT`, `IN`, `IS`, `EMPTY`, `NULL`,
`ORDER BY`, `ASC` and `DESC`, which Jira accepts in any letter case. This is the first step of the mini-JQL series;
the next problems evaluate the tokens.

Split `query` into tokens, returning a list of `[type, text]`:

| Input | Token |
|---|---|
| space, tab, newline, carriage return | skipped |
| `(` `)` `,` | `["LPAREN", "("]`, `["RPAREN", ")"]`, `["COMMA", ","]` |
| `!=` `>=` `<=` `!~` (checked first), then `=` `<` `>` `~` | `["OP", op]` |
| a quoted string `"..."` or `'...'` | `["STRING", content]` without the quotes. Inside, a backslash makes the next character literal (`\"` gives `"`, `\\` gives `\`). It ends at the next unescaped quote of the **same** kind. |
| a maximal run of letters, digits and `_ . - +` | `["KEYWORD", WORD_IN_UPPER_CASE]` if, ignoring case, it is one of `AND OR NOT IN IS EMPTY NULL ORDER BY ASC DESC`; otherwise `["WORD", text]` |

Errors: if a quoted string is never closed, or any other character appears (for example a lone `!` or `@`),
return **only** `[["ERROR", i]]` where `i` is the 0-based index of the opening quote or of the bad character.

**Example:** `'project = SHOP and status = "In Progress"'` →
`[["WORD","project"],["OP","="],["WORD","SHOP"],["KEYWORD","AND"],["WORD","status"],["OP","="],["STRING","In Progress"]]`
""",
    starter='''def tokenize(query: str) -> list:
    pass
''',
    solution=_TOKENIZE,
    tests=_TOKEN_TESTS,
    examples=2,
    wrong_solutions=[
        _patch(_TOKENIZE, "if w.upper() in KEYWORDS:", "if w in KEYWORDS:"),
        _patch(_TOKENIZE, 'elif q[i:i + 2] in ("!=", ">=", "<=", "!~"):\n            toks.append(["OP", q[i:i + 2]])\n            i += 2\n        elif c in "=<>~":',
               'elif c in "=<>~!":'),
        _patch(_TOKENIZE, '                if q[j] == "\\\\" and j + 1 < n:\n                    j += 1\n', ""),
        _patch(_TOKENIZE, "            if j >= n:\n                return [[\"ERROR\", i]]\n", ""),
    ],
    guide=dict(
        prereqs="Walking through a string with an index and `while` loops. See the lesson *JQL basics: field, operator, value*.",
        intuition="Look at one character and decide which kind of token starts there; then consume the whole token and continue after it. "
                  "Two-character operators must be checked before one-character ones, or `!=` would be read as `!` then `=`.",
        hints=[
            "Use an index `i` and a `while i < len(query)` loop; each branch advances `i`.",
            "For strings, remember which quote opened it and stop only at the same quote; handle `\\` by skipping to the next character and keeping it.",
            "Words: extend `j` while the character is in the allowed set, then compare `word.upper()` with the keyword set.",
            "On any error, return `[[\"ERROR\", i]]` immediately, discarding tokens found so far.",
        ],
        brute_force="Splitting on spaces fails for `points<=5`, quoted values with spaces, and `(a,b)` lists.",
        approach="One left-to-right pass with branches for whitespace, quotes, punctuation, two-character operators, one-character operators, "
                 "words and errors.\n\n**Dry run:** `status = \"In Progress\"` → `status` is a word; `=` an operator; `\"` opens a string "
                 "that ends at the next `\"`, giving `In Progress`.",
        complexity="Time O(n) for a query of length n; space O(n) for the tokens.",
        pitfalls="- Keywords are case-insensitive, but only whole words: `ORDERS` is a word, not `ORDER`.\n- `-7d` and `SHOP-10` are single words because `-` is a word character.\n"
                 "- A backslash before the closing quote escapes it, so the string may become unterminated.\n- `!` alone is an error; `!=` and `!~` are operators.",
        follow_up="Real JQL also has functions such as `currentUser()`: a word followed by parentheses. The tokenizer already produces `WORD`, `LPAREN`, `RPAREN` for them; how would a parser recognise a function call?",
    ),
),
dict(
    id="jira-jql-clause",
    title="Mini-JQL: Single Clause",
    difficulty="Medium",
    pattern="Parsing / Filtering",
    entry="run_clause",
    description=r"""
**Mirrors:** JQL clause evaluation as documented by Atlassian, including the rules that `!=` and `NOT IN` do
**not** match items whose field is empty, that `=` matches any value of a multi-valued field such as labels,
and that `~` is a text search. This is a simplified model: no functions, no history operators, and `~` matches
whole words only.

Write `run_clause(issues, clause)` that evaluates **one** clause and returns the keys of matching items in input
order. The clause has one of these shapes: `field OP value`, `field IN (v1, v2, ...)`, `field NOT IN (...)`,
`field IS EMPTY`, `field IS NOT EMPTY` (with `NULL` allowed instead of `EMPTY`).
""" + _DATA_NOTE + _SEMANTICS + r"""
**Example 1:** `run_clause(ISSUES, "assignee != farah")` → `["SHOP-4", "SHOP-5", "SHOP-6", "SHOP-10", "PAY-7"]`
(SHOP-3 and PAY-8 are unassigned, so they do not match.)

**Example 2:** `run_clause(ISSUES, 'summary ~ "promo code"')` → `["SHOP-1", "SHOP-2", "SHOP-3"]`
""",
    starter='''def run_clause(issues: list, clause: str) -> list:
    pass
''',
    solution=_CORE + _ENTRY_CLAUSE,
    tests=_CLAUSE_TESTS,
    examples=2,
    wrong_solutions=[
        _patch(_CORE, 'if op == "!=":\n        return bool(vals) and not', 'if op == "!=":\n        return not') + _ENTRY_CLAUSE,
        _patch(_CORE, 'if kind == "notin":\n        return bool(vals) and not', 'if kind == "notin":\n        return not') + _ENTRY_CLAUSE,
        _patch(_CORE, "return str(x).lower() == s.lower()", "return str(x) == s") + _ENTRY_CLAUSE,
        _patch(_CORE, "hit = bool(vals) and all(w in have for w in _words(s))",
               "hit = bool(vals) and s.lower() in \" \".join(str(x) for x in vals).lower()") + _ENTRY_CLAUSE,
    ],
    guide=dict(
        prereqs="The tokenizer from *Mini-JQL: Tokenizer*, list handling and `any`/`all`. See the lessons *JQL basics* and *JQL operators in depth*.",
        intuition="Normalise every field value into a list (empty becomes `[]`, a scalar becomes `[x]`). Then every operator is an `any` or a "
                  "`not any` over that list, with an extra 'must not be empty' guard on the negative operators.",
        hints=[
            "Tokenize, then read: field word, then either `IS [NOT] EMPTY`, `[NOT] IN ( ... )`, or an operator and a value.",
            "Write `_vals(v)` returning `[]`, `[v]` or `list(v)`.",
            "`!=`, `NOT IN` and `!~` all require a non-empty field.",
            "For ordering operators, compare numbers numerically and `YYYY-MM-DD` strings as text; anything else does not match.",
        ],
        brute_force="Comparing raw values with Python `==` gets multi-valued fields, case and empties wrong.",
        approach="1. Parse the clause into `(kind, field, op/values)`.\n2. `vals = _vals(issue.get(field))`.\n3. Apply the table rule.\n4. Collect keys in order.\n\n"
                 "**Dry run:** `labels != cny` on SHOP-4 (`[]`) → empty → no match; on SHOP-2 (`['checkout']`) → non-empty, no `cny` → match.",
        complexity="Time O(n * v) for n items with up to v values each; space O(n).",
        pitfalls="- The empty-field rule for `!=`, `NOT IN` and `!~`.\n- Case-insensitive comparisons (`in progress` equals `In Progress`).\n"
                 "- `summary ~ codes` does **not** match `code` here (no stemming); real Jira's text search is fuzzier.\n- `points = abc` never matches a numeric field.",
        follow_up="Add support for the function `currentUser()` as a value: what extra input would the function need?",
    ),
),
dict(
    id="jira-jql-boolean",
    title="Mini-JQL: Boolean Queries",
    difficulty="Hard",
    pattern="Recursive Descent Parsing",
    entry="run_where",
    description=r"""
**Mirrors:** JQL's `AND`, `OR`, `NOT` and parentheses. Atlassian's documentation says parentheses control the order
in which clauses are evaluated and recommends using them; this problem fixes a precedence so that every query has
one meaning: **`NOT` binds tightest, then `AND`, then `OR`**, and operators of equal precedence group from the left.
`NOT` here is plain logical negation.

Write `run_where(issues, query)` returning the keys of matching items in input order. `query` contains clauses
(exactly as in *Mini-JQL: Single Clause*) combined with `AND`, `OR`, `NOT` and parentheses. Keywords are
case-insensitive. Queries are always valid and never contain `ORDER BY`.
""" + _DATA_NOTE + _SEMANTICS + r"""
**Grammar** (with the precedence above):
```
or_expr  := and_expr { OR and_expr }
and_expr := atom { AND atom }
atom     := NOT atom | "(" or_expr ")" | clause
```

**Example 1:** `"project = SHOP AND (type = Bug OR priority = Highest)"` → `["SHOP-2", "SHOP-5"]`

**Example 2:** `"project = SHOP AND type = Bug OR priority = Highest"` → `["SHOP-2", "SHOP-5", "PAY-7"]`
(read as `(project = SHOP AND type = Bug) OR priority = Highest`)
""",
    starter='''def run_where(issues: list, query: str) -> list:
    pass
''',
    solution=_CORE + _ENTRY_WHERE,
    tests=_WHERE_TESTS,
    examples=2,
    wrong_solutions=[
        _patch(_CORE,
            "    def and_expr():\n        node = atom()\n        while is_kw(\"AND\"):\n            take()\n            node = (\"and\", node, atom())\n        return node\n",
            "    def and_expr():\n        node = atom()\n        while is_kw(\"AND\") or is_kw(\"OR\"):\n            k = take()[1]\n            node = (k.lower(), node, atom())\n        return node\n") + _ENTRY_WHERE,
        _patch(_CORE, "            return (\"not\", atom())", "            return (\"not\", or_expr())") + _ENTRY_WHERE,
        _patch(_CORE, 'if op == "!=":\n        return bool(vals) and not', 'if op == "!=":\n        return not') + _ENTRY_WHERE,
    ],
    guide=dict(
        prereqs="Recursion and the single-clause evaluator. See the lessons *JQL basics* and *JQL operators in depth*.",
        intuition="Write one small function per precedence level. The lowest level (`or_expr`) calls the next (`and_expr`), which calls `atom`; "
                  "`atom` handles `NOT`, parentheses (by calling back up to `or_expr`) and plain clauses. The call structure *is* the precedence.",
        hints=[
            "Keep a shared position into the token list; each function consumes the tokens it understands.",
            "`and_expr` loops while the next token is `AND`; `or_expr` loops while it is `OR`.",
            "`NOT` applies to one atom: `NOT a AND b` is `(NOT a) AND b`.",
            "Build a small tree of tuples such as `(\"and\", left, right)` and evaluate it per item.",
        ],
        brute_force="Evaluating strictly left to right ignores precedence: `a OR b AND c` would become `(a OR b) AND c`, which is a different question.",
        approach="Parse once into a tree; then for each item evaluate the tree recursively: `and` / `or` / `not` nodes combine children; leaf "
                 "clauses use the single-clause rules.\n\n**Dry run:** `type = Bug OR priority = Highest AND project = SHOP` parses as "
                 "`Bug OR (Highest AND SHOP)` → SHOP-2, SHOP-5 (bugs), PAY-7 (a bug too).",
        complexity="Parsing is O(t) for t tokens; evaluation is O(n * t) for n items.",
        pitfalls="- `NOT` must bind to a single atom, not the rest of the query.\n- Parentheses must restart at the lowest precedence (`or_expr`).\n"
                 "- Keywords in lower case (`and`, `not`) are still keywords.\n- Fields that do not exist are treated as empty.",
        follow_up="In real Jira, `field != value` behaves like `NOT field = value` according to Atlassian, so both skip empty fields. How would you change `NOT` so that it does the same for a single clause, and what problems would that cause for `NOT (a OR b)`?",
    ),
),
dict(
    id="jira-jql-order-by",
    title="Mini-JQL: ORDER BY",
    difficulty="Hard",
    pattern="Parsing / Custom Sort",
    entry="run_query",
    description=r"""
**Mirrors:** JQL's `ORDER BY`, which must come last, accepts several comma-separated fields, each optionally
`ASC` or `DESC`, and sorts priorities by their configured order (Lowest < Low < Medium < High < Highest) rather
than alphabetically. Jira uses each field's own default direction when none is given; this problem simplifies that
to **ASC**.

Write `run_query(issues, query)` returning matching keys in sorted order. `query` is an optional condition (as in
*Mini-JQL: Boolean Queries*) followed by an optional `ORDER BY f1 [ASC|DESC], f2 [ASC|DESC], ...`. A query may be
only an `ORDER BY` (then every item matches). Without `ORDER BY`, keep input order.
""" + _DATA_NOTE + _SEMANTICS + r"""
**Sorting rules for this problem:**

- Compare by the first field; use later fields only to break ties; remaining ties keep **input order**.
- **Empty values always sort last**, for both `ASC` and `DESC`.
- `priority` uses Lowest=1 ... Highest=5. `key` sorts by space key (case-insensitive) and then by the **number**
  (`SHOP-2` before `SHOP-10`). Numbers sort numerically. Lists sort by their values joined with `,` in lower case.
  Other strings sort case-insensitively (so `YYYY-MM-DD` dates sort correctly).

**Example:** `"statuscategory != Done ORDER BY priority DESC, created ASC"` →
`["SHOP-2", "PAY-7", "PAY-8", "SHOP-4", "SHOP-10", "SHOP-6", "SHOP-3", "SHOP-5"]`
""",
    starter='''def run_query(issues: list, query: str) -> list:
    pass
''',
    solution=_CORE + _ENTRY_QUERY,
    tests=_QUERY_TESTS,
    examples=1,
    wrong_solutions=[
        _patch(_CORE, "            if ka is None:\n                return 1\n            if kb is None:\n                return -1\n            r = -1 if ka < kb else 1\n            return -r if d == \"DESC\" else r",
               "            if ka is None:\n                r = 1\n            elif kb is None:\n                r = -1\n            else:\n                r = -1 if ka < kb else 1\n            return -r if d == \"DESC\" else r") + _ENTRY_QUERY,
        _patch(_CORE, "        return PRIORITY.get(str(v).lower(), 0)", "        return str(v).lower()") + _ENTRY_QUERY,
        _patch(_CORE, "        return (p.lower(), int(num))", "        return str(v).lower()") + _ENTRY_QUERY,
    ],
    guide=dict(
        prereqs="The boolean evaluator, `functools.cmp_to_key`, and tuple comparison. See the lesson *JQL functions, dates and ordering*.",
        intuition="Filter first, then sort with a comparison function that walks the ORDER BY fields in turn. Handle empties before looking at "
                  "the direction, so that reversing for DESC never moves them to the front.",
        hints=[
            "Parse `ORDER BY` after the condition: field, optional direction, then a comma or the end.",
            "Write `sort_key(item, field)` returning `None` for empty values and a comparable value otherwise.",
            "In the comparator: equal keys → next field; `None` → after; otherwise compare and flip for DESC.",
            "Finish ties with the original index so the sort is stable by input order.",
        ],
        brute_force="`sorted(..., reverse=True)` for DESC moves empty values to the front and reverses tie order, both wrong here.",
        approach="1. Parse into `(where, order)`.\n2. Keep items matching `where` (or all if none).\n3. Sort indexes with a comparator over `order`, breaking final ties by index.\n\n"
                 "**Dry run (example):** Highest items SHOP-2 (4 Mar) and PAY-7 (9 Mar) come first, oldest first; then High: PAY-8 (27 Feb), SHOP-4; "
                 "then the three Mediums by date; then SHOP-5 (Low).",
        complexity="O(n log n * f) for n matching items and f sort fields.",
        pitfalls="- Empty last in both directions.\n- `SHOP-10` after `SHOP-2` needs numeric key sorting.\n- Alphabetical priority would put High before Highest before Low.\n"
                 "- Without ORDER BY, return input order.",
        follow_up="Real JQL sorts components and versions by space first, then by their configured order. How would you extend `sort_key` with a per-field ordering table supplied by the caller?",
    ),
),
]
