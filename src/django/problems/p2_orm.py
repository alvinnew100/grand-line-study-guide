_ITEMS = [
    {"id": 1, "title": "Blue umbrella", "place": "Library", "days": 3, "claimed": False, "finder": {"name": "Ana", "team": {"name": "Porters", "floor": 1}}, "note": None},
    {"id": 2, "title": "blue scarf", "place": "Gym", "days": 10, "claimed": True, "finder": {"name": "Bo", "team": {"name": "Coaches", "floor": 2}}, "note": "wool"},
    {"id": 3, "title": "Calculator", "place": "library", "days": 0, "claimed": False, "finder": None, "note": "Casio fx"},
    {"id": 4, "title": "Water bottle", "place": "Canteen", "days": 7, "claimed": False, "finder": {"name": "ana", "team": None}, "note": ""},
    {"id": 5, "title": "Umbrella stand", "place": "Gym", "days": 21, "claimed": True, "finder": {"name": "Cy", "team": {"name": "Porters", "floor": 1}}, "note": None},
]

_SCORES = [
    {"name": "Ana", "team": "red", "score": 7, "city": {"name": "Lagos"}},
    {"name": "Bo", "team": "blue", "score": 9, "city": {"name": "Oslo"}},
    {"name": "Cy", "team": "red", "score": 9, "city": {"name": "Lima"}},
    {"name": "Di", "team": "blue", "score": 4, "city": {"name": "Oslo"}},
    {"name": "Ed", "team": "green", "score": 7, "city": {"name": "Lagos"}},
]

_STOCK = [
    {"sku": "A", "on_hand": 10, "reserved": 2, "price": 5, "sold": 0},
    {"sku": "B", "on_hand": 0, "reserved": 0, "price": 12, "sold": 40},
    {"sku": "C", "on_hand": 3, "reserved": 3, "price": 8, "sold": 7},
]

_SALES = [
    {"shop": "north", "amount": 10, "rating": 4},
    {"shop": "south", "amount": 5, "rating": None},
    {"shop": "north", "amount": None, "rating": 5},
    {"shop": "east", "amount": None, "rating": None},
    {"shop": "south", "amount": 7, "rating": 2},
    {"shop": "north", "amount": 2, "rating": 3},
]

_LOOKUP_ENGINE = r'''
_OPS = {"exact", "iexact", "contains", "icontains", "gt", "gte", "lt", "lte", "in", "isnull", "startswith", "range"}


def _split(key):
    parts = key.split("__")
    if len(parts) > 1 and parts[-1] in _OPS:
        return parts[:-1], parts[-1]
    return parts, "exact"


def _value(row, path):
    cur = row
    for part in path:
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def _test(value, op, arg):
    if op == "isnull":
        return (value is None) == arg
    if value is None:
        return op == "exact" and arg is None
    if op == "exact":
        return value == arg
    if op == "iexact":
        return str(value).lower() == str(arg).lower()
    if op == "contains":
        return str(arg) in str(value)
    if op == "icontains":
        return str(arg).lower() in str(value).lower()
    if op == "startswith":
        return str(value).startswith(str(arg))
    if op == "gt":
        return value > arg
    if op == "gte":
        return value >= arg
    if op == "lt":
        return value < arg
    if op == "lte":
        return value <= arg
    if op == "in":
        return value in arg
    if op == "range":
        return arg[0] <= value <= arg[1]
    return False


def _matches(row, conditions):
    for key, arg in conditions.items():
        path, op = _split(key)
        if not _test(_value(row, path), op, arg):
            return False
    return True
'''

PROBLEMS = [
dict(
    id="django-queryset-filter",
    title="filter() with field lookups over dictionaries",
    difficulty="Medium",
    pattern="ORM",
    entry="qs_filter",
    description=r"""
`Item.objects.filter(place__iexact="gym", finder__team__floor__gte=2)` reads almost like a sentence. Implement
that mini-language over plain data.

`qs_filter(rows, conditions)`:

- `rows` is a list of dicts; a value may itself be a dict (a related object) or `None`.
- `conditions` maps a **lookup key** to an argument. All conditions must hold (AND). Return the matching rows in
  their original order (the same dict objects, unchanged).

A key is split on `__`. If the **last** piece is one of the lookup names below it is the lookup, otherwise the
lookup is `exact`. The remaining pieces are a path followed through nested dicts. If any step of the path is
missing, or passes through `None`, the value is `None`.

| lookup | true when |
|---|---|
| `exact` | `value == arg`; with `arg` equal to `None` it means "value is None" |
| `iexact` | `str(value).lower() == str(arg).lower()` |
| `contains` / `icontains` | `str(arg)` is a substring of `str(value)` (case-sensitive / case-insensitive) |
| `startswith` | `str(value)` starts with `str(arg)` (case-sensitive) |
| `gt`, `gte`, `lt`, `lte` | the usual comparisons `value > arg`, ... |
| `in` | `value` is an element of the list `arg` |
| `range` | `arg[0] <= value <= arg[1]` (both ends inclusive) |
| `isnull` | `arg` is `True` and the value is `None`, or `arg` is `False` and it is not |

**NULL rule:** when the value is `None`, every lookup is false except `isnull=True` and `exact` with `None`.
An empty `conditions` dict matches everything.

**Example:** `qs_filter(items, {"finder__name__iexact": "ANA", "days__lt": 5})` keeps the items whose finder is
named ana (any case) and whose `days` is below 5.
""",
    starter='''def qs_filter(rows: list, conditions: dict) -> list:
    pass
''',
    solution=_LOOKUP_ENGINE + '''

def qs_filter(rows, conditions):
    return [row for row in rows if _matches(row, conditions)]
''',
    tests=[
        [_ITEMS, {"finder__name__iexact": "ANA", "days__lt": 5}],
        [_ITEMS, {"place": "Gym"}],
        [_ITEMS, {}],
        [_ITEMS, {"place__iexact": "LIBRARY"}],
        [_ITEMS, {"title__contains": "mbrella"}],
        [_ITEMS, {"title__icontains": "BLUE", "claimed": False}],
        [_ITEMS, {"title__startswith": "blue"}],
        [_ITEMS, {"days__gte": 7, "days__lte": 10}],
        [_ITEMS, {"days__range": [3, 10]}],
        [_ITEMS, {"id__in": [5, 1, 99]}],
        [_ITEMS, {"note__isnull": True}],
        [_ITEMS, {"note__isnull": False, "note__contains": ""}],
        [_ITEMS, {"finder__team__name": "Porters"}],
        [_ITEMS, {"finder__team__floor__gt": 0}],
        [_ITEMS, {"finder__team__isnull": True}],
        [_ITEMS, {"note": None}],
        [_ITEMS, {"finder__team__floor__lt": 5, "finder__name__in": ["Bo", "Cy"]}],
        [[], {"x": 1}],
        [[{"in": 3, "a": {"range": 5}}], {"in": 3, "a__range__gte": 5}],
    ],
    examples=3,
    wrong_solutions=[
        '''def qs_filter(rows, conditions):
    out = []
    for row in rows:
        ok = True
        for key, arg in conditions.items():
            parts = key.split("__")
            op = parts.pop() if len(parts) > 1 else "exact"
            cur = row
            for p in parts:
                cur = cur.get(p) if isinstance(cur, dict) else None
            if op == "exact": ok &= cur == arg
            elif op == "iexact": ok &= str(cur).lower() == str(arg).lower()
            elif op in ("contains",): ok &= str(arg) in str(cur)
            elif op == "icontains": ok &= str(arg).lower() in str(cur).lower()
            elif op == "startswith": ok &= str(cur).startswith(str(arg))
            elif op == "in": ok &= cur in arg
            elif op == "isnull": ok &= (cur is None) == arg
            elif op == "range": ok &= cur is not None and arg[0] <= cur <= arg[1]
            elif cur is None: ok = False
            elif op == "gt": ok &= cur > arg
            elif op == "gte": ok &= cur >= arg
            elif op == "lt": ok &= cur < arg
            elif op == "lte": ok &= cur <= arg
        if ok:
            out.append(row)
    return out
''',
        _LOOKUP_ENGINE + '''

def qs_filter(rows, conditions):
    return [row for row in rows if any(_test(_value(row, _split(k)[0]), _split(k)[1], a) for k, a in conditions.items())]
''',
    ],
    guide=dict(
        prereqs="Lesson *ListView, querysets and tests with a database* (filter and lookups); dictionaries and string methods.",
        intuition="A lookup key is a little program: *path* then *operator*. Parse it once (`a__b__gte` → path `[a, b]`, "
                  "operator `gte`), fetch the value by walking the path, and dispatch on the operator. `None` plays the "
                  "role of SQL `NULL`: unknown, so comparisons with it are never true.",
        hints=[
            "Split on `__`; only treat the last piece as an operator when it is in the known set **and** there is more than one piece.",
            "Write `value(row, path)` that returns `None` as soon as a step is not a dict or lacks the key.",
            "Handle `isnull` first, then bail out for `None` values, then the ordinary comparisons.",
        ],
        brute_force="Hard-code an `if` per field/lookup combination you see in the tests. It cannot generalise and grows "
                    "with fields × lookups; the parsed approach is the same O(rows × conditions) with no special cases.",
        approach="""1. For each row, for each `(key, arg)`: split the key into path and operator.
2. Walk the path to get the value (`None` if broken).
3. Evaluate the operator with the NULL rule applied first.
4. Keep the row only when every condition is true.

**Dry run** `{"finder__team__floor__gt": 0}` on item 4 (`finder.team` is `None`): path `[finder, team, floor]`
→ `finder` is a dict, `team` is `None`, the next step fails → value `None` → `gt` on `None` is false → row dropped.""",
        complexity="O(R · C · D) for R rows, C conditions and path depth D. The database does the same job with indexes instead of a scan.",
        pitfalls="""- Comparing `None > 0` raises `TypeError` in Python; apply the NULL rule before comparing.
- `str(None)` is `"None"`, so a naive `contains="on"` would wrongly match missing values.
- A field can legally be called `in` or `range`: a single-piece key is always a field name.
- Conditions are ANDed, never ORed (that is what `Q` objects are for).""",
        follow_up="Django also has `endswith`, `regex`, date parts such as `created__year`, and `istartswith`; add two of them.",
    ),
),
dict(
    id="django-queryset-shape",
    title="Chain exclude, order_by, values and values_list",
    difficulty="Medium",
    pattern="ORM",
    entry="run_query",
    description=r"""
A queryset is built by chaining methods; each returns a new queryset. Evaluate such a chain over a list of dicts.

`run_query(rows, ops)` applies `ops` in order, starting from `rows`, and returns the final result. Each op is a
list whose first element is the method name:

| op | effect |
|---|---|
| `["filter", cond]` | keep rows where **all** conditions in the dict hold |
| `["exclude", cond]` | drop rows where **all** conditions hold (rows failing at least one condition stay) |
| `["order_by", keys]` | sort by the listed keys; a key starting with `-` sorts descending; later keys break ties; rows equal on every key keep their current relative order |
| `["reverse"]` | reverse the current order |
| `["values", fields]` | turn each row into a dict containing only `fields` (keys written exactly as given) |
| `["values_list", fields]` | turn each row into a list of the field values, in the order given |
| `["values_list_flat", field]` | turn each row into the bare value of one field |
| `["distinct"]` | remove duplicates, keeping the first occurrence |

Conditions use `field` (exact), or `field__gt`, `__gte`, `__lt`, `__lte`, `__in`, `__contains` (substring of a
string value). Field names in conditions, sort keys and `values*` may traverse nested dicts with `__`
(`city__name`). All sort values are present and mutually comparable; no value is `None`.

`values`, `values_list` and `values_list_flat` are applied to rows that are still full dicts; only `distinct`
and `reverse` may follow them.

**Example:** `run_query(players, [["exclude", {"team": "blue"}], ["order_by", ["-score", "name"]], ["values_list_flat", "name"]])`
→ names of the non-blue players, best score first, ties by name.
""",
    starter='''def run_query(rows: list, ops: list):
    pass
''',
    solution='''_OPS = {"gt", "gte", "lt", "lte", "in", "contains"}


def _get(row, key):
    cur = row
    for part in key.split("__"):
        cur = cur[part]
    return cur


def _holds(row, key, arg):
    parts = key.split("__")
    op = "exact"
    if len(parts) > 1 and parts[-1] in _OPS:
        op = parts.pop()
    value = _get(row, "__".join(parts))
    if op == "exact":
        return value == arg
    if op == "gt":
        return value > arg
    if op == "gte":
        return value >= arg
    if op == "lt":
        return value < arg
    if op == "lte":
        return value <= arg
    if op == "in":
        return value in arg
    return arg in value


def _all(row, cond):
    return all(_holds(row, k, a) for k, a in cond.items())


def run_query(rows, ops):
    cur = list(rows)
    for op in ops:
        name = op[0]
        if name == "filter":
            cur = [r for r in cur if _all(r, op[1])]
        elif name == "exclude":
            cur = [r for r in cur if not _all(r, op[1])]
        elif name == "order_by":
            for key in reversed(op[1]):
                desc = key.startswith("-")
                field = key[1:] if desc else key
                cur = sorted(cur, key=lambda r: _get(r, field), reverse=desc)
                if desc:
                    # sorted(reverse=True) keeps equal items in original order, which is what we need
                    pass
        elif name == "reverse":
            cur = cur[::-1]
        elif name == "values":
            cur = [{f: _get(r, f) for f in op[1]} for r in cur]
        elif name == "values_list":
            cur = [[_get(r, f) for f in op[1]] for r in cur]
        elif name == "values_list_flat":
            cur = [_get(r, op[1]) for r in cur]
        elif name == "distinct":
            seen, out = [], []
            for r in cur:
                if r not in seen:
                    seen.append(r)
                    out.append(r)
            cur = out
    return cur
''',
    tests=[
        [_SCORES, [["exclude", {"team": "blue"}], ["order_by", ["-score", "name"]], ["values_list_flat", "name"]]],
        [_SCORES, [["order_by", ["team", "-score"]], ["values_list", ["team", "score", "name"]]]],
        [_SCORES, []],
        [_SCORES, [["exclude", {"team": "red", "score": 9}], ["values_list_flat", "name"]]],
        [_SCORES, [["exclude", {"team": "red"}], ["exclude", {"score": 9}], ["values_list_flat", "name"]]],
        [_SCORES, [["order_by", ["-score"]], ["values_list_flat", "name"]]],
        [_SCORES, [["order_by", ["score"]], ["reverse"], ["values_list_flat", "name"]]],
        [_SCORES, [["values", ["name", "city__name"]]]],
        [_SCORES, [["order_by", ["city__name", "-name"]], ["values_list", ["city__name", "name"]]]],
        [_SCORES, [["values_list_flat", "team"], ["distinct"]]],
        [_SCORES, [["values", ["team", "score"]], ["distinct"]]],
        [_SCORES, [["filter", {"score__gte": 7, "name__in": ["Ana", "Bo", "Di"]}], ["exclude", {"city__name__contains": "s"}], ["values_list_flat", "name"]]],
        [_SCORES, [["filter", {"score__gt": 100}], ["order_by", ["name"]], ["values", ["name"]]]],
        [_SCORES, [["exclude", {}], ["values_list_flat", "name"]]],
        [_SCORES, [["order_by", ["-team", "-score", "-name"]], ["values_list_flat", "name"]]],
        [_SCORES, [["filter", {"score__lt": 9, "score__lte": 7}], ["order_by", ["score", "team"]], ["values_list", ["name"]]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def _get(row, key):
    cur = row
    for part in key.split("__"):
        cur = cur[part]
    return cur
def run_query(rows, ops):
    cur = list(rows)
    for op in ops:
        name = op[0]
        if name in ("filter", "exclude"):
            def ok(r):
                for k, a in op[1].items():
                    parts = k.split("__"); o = "exact"
                    if len(parts) > 1 and parts[-1] in ("gt", "gte", "lt", "lte", "in", "contains"):
                        o = parts.pop()
                    v = _get(r, "__".join(parts))
                    good = {"exact": lambda: v == a, "gt": lambda: v > a, "gte": lambda: v >= a, "lt": lambda: v < a,
                            "lte": lambda: v <= a, "in": lambda: v in a, "contains": lambda: a in v}[o]()
                    if name == "filter" and not good: return False
                    if name == "exclude" and good: return False
                return True
            cur = [r for r in cur if ok(r)]
        elif name == "order_by":
            for key in reversed(op[1]):
                desc = key.startswith("-")
                cur = sorted(cur, key=lambda r: _get(r, key.lstrip("-")), reverse=desc)
        elif name == "reverse": cur = cur[::-1]
        elif name == "values": cur = [{f: _get(r, f) for f in op[1]} for r in cur]
        elif name == "values_list": cur = [[_get(r, f) for f in op[1]] for r in cur]
        elif name == "values_list_flat": cur = [_get(r, op[1]) for r in cur]
        elif name == "distinct":
            out = []
            for r in cur:
                if r not in out: out.append(r)
            cur = out
    return cur
''',
        '''def _get(row, key):
    cur = row
    for part in key.split("__"):
        cur = cur[part]
    return cur
def _all(r, cond):
    for k, a in cond.items():
        parts = k.split("__"); o = "exact"
        if len(parts) > 1 and parts[-1] in ("gt", "gte", "lt", "lte", "in", "contains"):
            o = parts.pop()
        v = _get(r, "__".join(parts))
        if not {"exact": lambda: v == a, "gt": lambda: v > a, "gte": lambda: v >= a, "lt": lambda: v < a,
                "lte": lambda: v <= a, "in": lambda: v in a, "contains": lambda: a in v}[o]():
            return False
    return True
def run_query(rows, ops):
    cur = list(rows)
    for op in ops:
        name = op[0]
        if name == "filter": cur = [r for r in cur if _all(r, op[1])]
        elif name == "exclude": cur = [r for r in cur if not _all(r, op[1])]
        elif name == "order_by":
            key = op[1][0]
            cur = sorted(cur, key=lambda r: _get(r, key.lstrip("-")), reverse=key.startswith("-"))
        elif name == "reverse": cur = cur[::-1]
        elif name == "values": cur = [{f: _get(r, f) for f in op[1]} for r in cur]
        elif name == "values_list": cur = [[_get(r, f) for f in op[1]] for r in cur]
        elif name == "values_list_flat": cur = [_get(r, op[1]) for r in cur]
        elif name == "distinct": cur = sorted(set(cur)) if cur and not isinstance(cur[0], (dict, list)) else cur
    return cur
''',
    ],
    guide=dict(
        prereqs="Problem *filter() with field lookups*; stable sorting with `sorted(key=..., reverse=...)`.",
        intuition="Each queryset method is a pure function from a list of rows to a new list, so a chain is a fold over "
                  "the ops. The two subtle ones are `exclude`, which negates the *conjunction* of its conditions, and a "
                  "multi-key `order_by` with mixed directions, which is easiest as several stable sorts applied from the "
                  "least significant key to the most significant.",
        hints=[
            "`exclude(a=1, b=2)` is `NOT (a=1 AND b=2)`. It is not the same as two separate excludes.",
            "Python's sort is stable, even with `reverse=True`: sort by the last key first, the first key last.",
            "For `distinct`, dicts and lists are unhashable; compare against a list of already-seen values.",
        ],
        brute_force="For ordering, generate a composite key by negating numbers for descending fields. That fails for "
                    "strings (you cannot negate text), which is why repeated stable sorts are the general tool.",
        approach="""1. Start with a copy of the rows and loop over ops.
2. `filter`/`exclude`: evaluate all conditions per row; keep when true / when not all true.
3. `order_by`: for each key from last to first, `sorted` by that field with `reverse` for a `-` prefix.
4. `values*`: project each row; `distinct`: first-occurrence dedupe; `reverse`: slice `[::-1]`.

**Dry run** `order_by(["-score", "name"])` on Ana 7, Cy 9, Ed 7: sort by name → Ana, Cy, Ed; then stable sort by
score descending → Cy 9, Ana 7, Ed 7 (Ana stays ahead of Ed).""",
        complexity="Filtering and projection are O(n); ordering is O(k · n log n) for k keys; `distinct` here is O(n²) in the worst case (fine for small result sets; hash the rows to do better).",
        pitfalls="""- Treating `exclude(a, b)` as 'drop rows matching a or b'.
- Sorting only by the first key, or sorting keys in the wrong significance order.
- `key.lstrip("-")` inside a lambda defined in a loop is fine, but capturing the loop variable late is a classic bug; bind it first.
- `distinct` must preserve first-seen order; `set()` does not and cannot hold dicts.""",
        follow_up="In real Django, `distinct()` after `values()` becomes `SELECT DISTINCT` over those columns, and `order_by` fields silently join the DISTINCT list. Read the docs note on that interaction.",
    ),
),
dict(
    id="django-q-objects",
    title="Evaluate Q-object boolean trees",
    difficulty="Medium",
    pattern="ORM",
    entry="q_filter",
    description=r"""
Keyword arguments to `filter()` can only be ANDed. For OR and NOT Django provides `Q` objects:
`Q(place="Gym") | ~Q(claimed=True)`. Evaluate such expressions written as nested lists.

`q_filter(rows, q)` returns the rows (original order) for which `q` is true. A `q` is one of:

- a **dict** of lookups, all of which must hold (an empty dict is true for every row);
- `["AND", q1, q2, ...]`: true when every child is true (one or more children);
- `["OR", q1, q2, ...]`: true when at least one child is true (one or more children);
- `["NOT", q1]`: true when the child is false.

Lookups inside dicts: `field` (exact), `field__gt`, `__gte`, `__lt`, `__lte`, `__in`, `__icontains`
(case-insensitive substring of `str(value)`), `__isnull` (argument `True`/`False`). Paths may traverse nested
dicts with `__`; a broken path gives `None`. When the value is `None` every lookup is false except
`isnull=True` and exact comparison with `None`. `NOT` is plain boolean negation of its child.

**Example:** `q_filter(items, ["OR", {"place": "Gym"}, ["NOT", {"claimed": True}]])` keeps items that are in the
gym or not yet claimed.
""",
    starter='''def q_filter(rows: list, q) -> list:
    pass
''',
    solution='''_OPS = {"gt", "gte", "lt", "lte", "in", "icontains", "isnull"}


def _leaf(row, key, arg):
    parts = key.split("__")
    op = "exact"
    if len(parts) > 1 and parts[-1] in _OPS:
        op = parts.pop()
    value = row
    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            value = None
            break
    if op == "isnull":
        return (value is None) == arg
    if value is None:
        return op == "exact" and arg is None
    if op == "exact":
        return value == arg
    if op == "gt":
        return value > arg
    if op == "gte":
        return value >= arg
    if op == "lt":
        return value < arg
    if op == "lte":
        return value <= arg
    if op == "in":
        return value in arg
    return str(arg).lower() in str(value).lower()


def _eval(row, q):
    if isinstance(q, dict):
        return all(_leaf(row, k, a) for k, a in q.items())
    if q[0] == "AND":
        return all(_eval(row, child) for child in q[1:])
    if q[0] == "OR":
        return any(_eval(row, child) for child in q[1:])
    return not _eval(row, q[1])


def q_filter(rows, q):
    return [row for row in rows if _eval(row, q)]
''',
    tests=[
        [_ITEMS, ["OR", {"place": "Gym"}, ["NOT", {"claimed": True}]]],
        [_ITEMS, {"place": "Gym", "claimed": True}],
        [_ITEMS, {}],
        [_ITEMS, ["NOT", {}]],
        [_ITEMS, ["AND", {"days__gte": 3}, {"days__lt": 20}]],
        [_ITEMS, ["OR", {"title__icontains": "UMBRELLA"}, {"note__icontains": "casio"}]],
        [_ITEMS, ["NOT", ["OR", {"place": "Gym"}, {"place": "Library"}]]],
        [_ITEMS, ["AND", ["OR", {"days__lt": 1}, {"days__gt": 9}], ["NOT", {"claimed": True}]]],
        [_ITEMS, ["NOT", {"finder__team__floor__gt": 1}]],
        [_ITEMS, ["OR", {"finder__isnull": True}, {"finder__team__isnull": True}]],
        [_ITEMS, ["NOT", ["NOT", {"id__in": [2, 4]}]]],
        [_ITEMS, ["OR", {"id": 1}]],
        [_ITEMS, ["AND", {"id": 1}, {"id": 2}]],
        [_ITEMS, ["OR", ["AND", {"place": "Gym"}, {"days__gt": 15}], ["AND", {"place": "Library"}, ["NOT", {"note__isnull": False}]]]],
        [[], ["OR", {"a": 1}, {"b": 2}]],
        [_ITEMS, ["OR", {"id": 1}, {"id": 2}, {"id": 3}]],
        [_ITEMS, ["AND", {"days__gt": 0}, {"days__lt": 30}, {"claimed": True}, {"place": "Library"}]],
        [_ITEMS, ["NOT", {"place": "Gym", "claimed": False}]],
    ],
    examples=3,
    wrong_solutions=[
        '''def _leaf(row, key, arg):
    parts = key.split("__"); op = "exact"
    if len(parts) > 1 and parts[-1] in {"gt", "gte", "lt", "lte", "in", "icontains", "isnull"}:
        op = parts.pop()
    value = row
    for part in parts:
        if isinstance(value, dict) and part in value: value = value[part]
        else:
            value = None; break
    if op == "isnull": return (value is None) == arg
    if value is None: return op == "exact" and arg is None
    if op == "exact": return value == arg
    if op == "gt": return value > arg
    if op == "gte": return value >= arg
    if op == "lt": return value < arg
    if op == "lte": return value <= arg
    if op == "in": return value in arg
    return str(arg).lower() in str(value).lower()
def _eval(row, q):
    if isinstance(q, dict):
        return any(_leaf(row, k, a) for k, a in q.items()) if q else True
    if q[0] == "AND": return all(_eval(row, c) for c in q[1:])
    if q[0] == "OR": return any(_eval(row, c) for c in q[1:])
    return not _eval(row, q[1])
def q_filter(rows, q):
    return [r for r in rows if _eval(r, q)]
''',
        '''def _leaf(row, key, arg):
    parts = key.split("__"); op = "exact"
    if len(parts) > 1 and parts[-1] in {"gt", "gte", "lt", "lte", "in", "icontains", "isnull"}:
        op = parts.pop()
    value = row
    for part in parts:
        if isinstance(value, dict) and part in value: value = value[part]
        else:
            value = None; break
    if op == "isnull": return (value is None) == arg
    if value is None: return op == "exact" and arg is None
    if op == "exact": return value == arg
    if op == "gt": return value > arg
    if op == "gte": return value >= arg
    if op == "lt": return value < arg
    if op == "lte": return value <= arg
    if op == "in": return value in arg
    return str(arg).lower() in str(value).lower()
def _eval(row, q):
    if isinstance(q, dict):
        return all(_leaf(row, k, a) for k, a in q.items())
    if q[0] == "NOT": return not _eval(row, q[1])
    return _eval(row, q[1]) and (len(q) < 3 or _eval(row, q[2])) if q[0] == "AND" else _eval(row, q[1]) or (len(q) > 2 and _eval(row, q[2]))
def q_filter(rows, q):
    return [r for r in rows if _eval(r, q)]
''',
    ],
    guide=dict(
        prereqs="Lesson *Querysets in depth: laziness, lookups, Q and F*; recursion over a tree; `all()` and `any()`.",
        intuition="A Q expression is a tree: leaves are lookup dicts, inner nodes are AND, OR and NOT. Trees are "
                  "evaluated by recursion, each node asking its children and combining the answers. This is the same "
                  "structure Django keeps internally (`Q.children`, `Q.connector`, `Q.negated`) before compiling it to a `WHERE` clause.",
        hints=[
            "Distinguish leaf from operator node with `isinstance(q, dict)`.",
            "`all(...)` over the children is AND, `any(...)` is OR; both take any number of children.",
            "A dict with several keys is itself an AND; do not confuse it with OR.",
        ],
        brute_force="Convert the tree to disjunctive normal form and test each conjunction. Exponential blow-up in the "
                    "worst case, and completely unnecessary: direct recursion visits each node once.",
        approach="""1. `eval(row, q)`: dict → all lookups hold; `AND` → all children; `OR` → any child; `NOT` → negate.
2. Leaf lookup = split key, walk path, apply the NULL rule, compare.
3. Filter the rows with `eval`.

**Dry run** `["NOT", {"finder__team__floor__gt": 1}]` on item 3 (`finder` is `None`): the leaf's value is `None`,
so `gt` is false; NOT makes it true → the row is kept.""",
        complexity="O(R · N) for R rows and N nodes in the Q tree (times path depth).",
        pitfalls="""- Supporting only two children for AND/OR.
- Reading a multi-key dict as OR.
- In real SQL, `NOT (NULL > 1)` is still *unknown* and the row would be dropped; Django adds `IS NOT NULL` checks to
  make `exclude()` behave intuitively. This exercise uses plain boolean negation, so know the difference in interviews.""",
        follow_up="Implement operator overloading: a `Q` class with `__or__`, `__and__` and `__invert__` that builds this list structure.",
    ),
),
dict(
    id="django-f-update",
    title="update() with F expressions",
    difficulty="Medium",
    pattern="ORM",
    entry="apply_update",
    description=r"""
`Stock.objects.filter(on_hand__gt=0).update(on_hand=F("on_hand") - F("reserved"), reserved=0)` runs as a single
SQL `UPDATE`. Every `F("x")` on the right-hand side refers to the row's value **before** the statement, no matter
in which order the assignments are written. Simulate it.

`apply_update(rows, where, assignments)`:

- `rows`: list of flat dicts. **Do not mutate the input.**
- `where`: dict of conditions, all required: `field` (exact) or `field__gt`, `__gte`, `__lt`, `__lte`.
  An empty dict selects every row.
- `assignments`: dict mapping a field name to an **expression**:
  - a number or string literal;
  - `["F", "field"]`: the row's old value of that field;
  - `[op, left, right]` with `op` one of `"+"`, `"-"`, `"*"` and both operands expressions (nesting allowed).

Return `[count, new_rows]`: the number of rows matched by `where` (matched rows count even if their values do
not change) and a new list with the rows in the same order, matched ones updated.

**Example:** on `{"a": 1, "b": 5}`, assignments `{"a": ["F", "b"], "b": ["F", "a"]}` swap the values →
`{"a": 5, "b": 1}`.
""",
    starter='''def apply_update(rows: list, where: dict, assignments: dict) -> list:
    pass
''',
    solution='''def _match(row, where):
    for key, arg in where.items():
        field, _, op = key.partition("__")
        value = row[field]
        if op == "" and value != arg:
            return False
        if op == "gt" and not value > arg:
            return False
        if op == "gte" and not value >= arg:
            return False
        if op == "lt" and not value < arg:
            return False
        if op == "lte" and not value <= arg:
            return False
    return True


def _calc(expr, old):
    if not isinstance(expr, list):
        return expr
    if expr[0] == "F":
        return old[expr[1]]
    left, right = _calc(expr[1], old), _calc(expr[2], old)
    if expr[0] == "+":
        return left + right
    if expr[0] == "-":
        return left - right
    return left * right


def apply_update(rows, where, assignments):
    count, out = 0, []
    for row in rows:
        if _match(row, where):
            count += 1
            new = dict(row)
            for field, expr in assignments.items():
                new[field] = _calc(expr, row)
            out.append(new)
        else:
            out.append(dict(row))
    return [count, out]
''',
    tests=[
        [[{"a": 1, "b": 5}], {}, {"a": ["F", "b"], "b": ["F", "a"]}],
        [_STOCK, {"on_hand__gt": 0}, {"on_hand": ["-", ["F", "on_hand"], ["F", "reserved"]], "reserved": 0}],
        [_STOCK, {}, {"sold": ["+", ["F", "sold"], 1]}],
        [_STOCK, {"sku": "B"}, {"price": ["*", ["F", "price"], 2]}],
        [_STOCK, {"sku": "Z"}, {"price": 0}],
        [_STOCK, {"price__gte": 8, "price__lt": 12}, {"sku": "sale"}],
        [_STOCK, {"on_hand__lte": 3}, {"on_hand": ["+", ["*", ["F", "reserved"], 2], ["-", ["F", "price"], ["F", "sold"]]]}],
        [_STOCK, {}, {"price": ["+", ["F", "price"], 1], "sold": ["*", ["F", "price"], 10]}],
        [_STOCK, {}, {"reserved": 0, "on_hand": ["-", ["F", "on_hand"], ["F", "reserved"]]}],
        [[], {}, {"a": 1}],
        [_STOCK, {"sold": 0}, {"sold": 0}],
        [[{"n": 2, "m": 3}, {"n": 4, "m": 0}], {"m__gt": 0}, {"n": ["*", ["F", "n"], ["F", "n"]], "m": ["F", "n"]}],
        [[{"tag": "a", "n": 1}], {"n__gte": 1}, {"tag": ["+", ["F", "tag"], "-old"], "n": ["-", 10, ["F", "n"]]}],
    ],
    examples=2,
    wrong_solutions=[
        '''def _calc(expr, row):
    if not isinstance(expr, list): return expr
    if expr[0] == "F": return row[expr[1]]
    l, r = _calc(expr[1], row), _calc(expr[2], row)
    return l + r if expr[0] == "+" else l - r if expr[0] == "-" else l * r
def apply_update(rows, where, assignments):
    count, out = 0, []
    for row in rows:
        new = dict(row)
        ok = True
        for key, arg in where.items():
            f, _, op = key.partition("__"); v = row[f]
            ok &= {"": v == arg, "gt": v > arg, "gte": v >= arg, "lt": v < arg, "lte": v <= arg}[op]
        if ok:
            count += 1
            for field, expr in assignments.items():
                new[field] = _calc(expr, new)
        out.append(new)
    return [count, out]
''',
        '''def _calc(expr, row):
    if not isinstance(expr, list): return expr
    if expr[0] == "F": return row[expr[1]]
    l, r = _calc(expr[1], row), _calc(expr[2], row)
    return l + r if expr[0] == "+" else l - r if expr[0] == "-" else l * r
def apply_update(rows, where, assignments):
    count, out = 0, []
    for row in rows:
        new = dict(row)
        ok = True
        for key, arg in where.items():
            f, _, op = key.partition("__"); v = row[f]
            ok &= {"": v == arg, "gt": v > arg, "gte": v >= arg, "lt": v < arg, "lte": v <= arg}[op]
        if ok:
            for field, expr in assignments.items():
                new[field] = _calc(expr, row)
            if new != row:
                count += 1
        out.append(new)
    return [count, out]
''',
    ],
    guide=dict(
        prereqs="Lesson *Querysets in depth: laziness, lookups, Q and F*; recursion over expression trees.",
        intuition="An `F` expression is a *description* of a computation that the database performs per row, not a "
                  "Python value. SQL evaluates the whole `SET` list against a snapshot of the old row, so the result "
                  "never depends on the order of the assignments. Keep the old row read-only and write into a copy.",
        hints=[
            "Write a recursive `calc(expr, old_row)`; non-list → literal, `[\"F\", name]` → `old_row[name]`.",
            "Build `new = dict(row)` and always read from `row`, never from `new`.",
            "`update()` returns the number of rows *matched*, not the number that changed.",
        ],
        brute_force="Fetch each object, compute in Python and call `save()`. That is N queries instead of one and it is "
                    "subject to race conditions: two workers both read 10, both write 9. `F` pushes the arithmetic into one atomic statement.",
        approach="""1. For each row test the `where` conditions.
2. Not matched → append a copy. Matched → increment the count, copy the row, and for each assignment evaluate the
   expression against the **original** row, storing into the copy.
3. Return `[count, new_rows]`.

**Dry run** swap: old `{a:1, b:5}`. `a = F(b)` → 5 (reads old b). `b = F(a)` → 1 (reads old a, not the freshly
written 5). Result `{a:5, b:1}`.""",
        complexity="O(R · (W + E)) for R rows, W conditions and total expression size E; O(R) extra space for the copies.",
        pitfalls="""- Evaluating assignments sequentially against the partly updated row (the swap test catches it).
- Mutating the caller's rows.
- Counting changed rows instead of matched rows.
- After a real `update()` with `F`, in-memory model instances are stale; call `refresh_from_db()`.""",
        follow_up="Add `Greatest`/`Least` functions and a `Case/When` expression.",
    ),
),
dict(
    id="django-annotate",
    title="values().annotate(): group and aggregate",
    difficulty="Medium",
    pattern="ORM",
    entry="annotate",
    description=r"""
`Sale.objects.values("shop").annotate(total=Sum("amount"), n=Count("id"))` is Django's way to write
`GROUP BY shop`. Implement the grouping with SQL's NULL rules.

`annotate(rows, group_key, aggregates)`:

- `rows`: list of flat dicts; every row has `group_key`. Other values may be numbers or `None`.
- `aggregates`: dict mapping an output name to `[function, field]`. Functions:

| function | result for one group |
|---|---|
| `Count` | with field `"*"`: number of rows; otherwise number of rows whose field is not `None` |
| `Sum` | sum of the non-`None` values; `None` if there are none |
| `Avg` | mean of the non-`None` values rounded with `round(x, 4)`; `None` if there are none |
| `Min`, `Max` | smallest / largest non-`None` value; `None` if there are none |

Return one dict per distinct group value, in order of **first appearance**, containing `group_key` and then one
entry per aggregate.

**Example:** rows `[{"shop": "n", "amount": 10}, {"shop": "s", "amount": 5}, {"shop": "n", "amount": None}]`
with `{"total": ["Sum", "amount"], "n": ["Count", "*"], "paid": ["Count", "amount"]}` →
`[{"shop": "n", "total": 10, "n": 2, "paid": 1}, {"shop": "s", "total": 5, "n": 1, "paid": 1}]`.
""",
    starter='''def annotate(rows: list, group_key: str, aggregates: dict) -> list:
    pass
''',
    solution='''def annotate(rows, group_key, aggregates):
    groups = {}
    for row in rows:
        groups.setdefault(row[group_key], []).append(row)
    out = []
    for key, members in groups.items():
        result = {group_key: key}
        for alias, (func, field) in aggregates.items():
            if func == "Count" and field == "*":
                result[alias] = len(members)
                continue
            values = [m[field] for m in members if m.get(field) is not None]
            if func == "Count":
                result[alias] = len(values)
            elif not values:
                result[alias] = None
            elif func == "Sum":
                result[alias] = sum(values)
            elif func == "Avg":
                result[alias] = round(sum(values) / len(values), 4)
            elif func == "Min":
                result[alias] = min(values)
            else:
                result[alias] = max(values)
        out.append(result)
    return out
''',
    tests=[
        [[{"shop": "n", "amount": 10}, {"shop": "s", "amount": 5}, {"shop": "n", "amount": None}], "shop",
         {"total": ["Sum", "amount"], "n": ["Count", "*"], "paid": ["Count", "amount"]}],
        [_SALES, "shop", {"total": ["Sum", "amount"]}],
        [_SALES, "shop", {"avg": ["Avg", "rating"], "n": ["Count", "rating"]}],
        [_SALES, "shop", {"lo": ["Min", "amount"], "hi": ["Max", "amount"], "rows": ["Count", "*"]}],
        [_SALES, "shop", {}],
        [[], "shop", {"n": ["Count", "*"]}],
        [_SCORES, "team", {"best": ["Max", "score"], "avg": ["Avg", "score"], "players": ["Count", "name"]}],
        [[{"k": 1, "v": 1}, {"k": 1, "v": 2}, {"k": 1, "v": 2}], "k", {"avg": ["Avg", "v"], "sum": ["Sum", "v"]}],
        [[{"k": "a", "v": 0}, {"k": "b", "v": None}], "k", {"s": ["Sum", "v"], "a": ["Avg", "v"], "c": ["Count", "v"], "m": ["Min", "v"]}],
        [[{"k": None, "v": 3}, {"k": "x", "v": 4}, {"k": None, "v": 5}], "k", {"s": ["Sum", "v"]}],
        [[{"k": i % 7, "v": i} for i in range(700)], "k", {"s": ["Sum", "v"], "a": ["Avg", "v"], "n": ["Count", "*"]}],
        [[{"k": "z", "v": 2.5}, {"k": "a", "v": 1}, {"k": "z", "v": 0.25}], "k", {"a": ["Avg", "v"], "mx": ["Max", "v"]}],
    ],
    examples=2,
    wrong_solutions=[
        '''def annotate(rows, group_key, aggregates):
    groups = {}
    for row in rows:
        groups.setdefault(row[group_key], []).append(row)
    out = []
    for key, members in groups.items():
        result = {group_key: key}
        for alias, (func, field) in aggregates.items():
            values = [m.get(field) or 0 for m in members]
            if func == "Count": result[alias] = len(members)
            elif func == "Sum": result[alias] = sum(values)
            elif func == "Avg": result[alias] = round(sum(values) / len(values), 4)
            elif func == "Min": result[alias] = min(values)
            else: result[alias] = max(values)
        out.append(result)
    return out
''',
        '''def annotate(rows, group_key, aggregates):
    out = []
    for key in sorted({r[group_key] for r in rows}, key=str):
        members = [r for r in rows if r[group_key] == key]
        result = {group_key: key}
        for alias, (func, field) in aggregates.items():
            if func == "Count" and field == "*":
                result[alias] = len(members); continue
            values = [m[field] for m in members if m.get(field) is not None]
            if func == "Count": result[alias] = len(values)
            elif not values: result[alias] = None
            elif func == "Sum": result[alias] = sum(values)
            elif func == "Avg": result[alias] = round(sum(values) / len(values), 4)
            elif func == "Min": result[alias] = min(values)
            else: result[alias] = max(values)
        out.append(result)
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Aggregation, joins and the N+1 problem*; dictionaries that preserve insertion order.",
        intuition="Grouping is bucketing: one pass puts each row into the bucket for its key, a second pass reduces each "
                  "bucket to one summary row. The only delicate part is NULL: aggregates skip missing values instead of "
                  "treating them as zero, and an aggregate over nothing is NULL (except `Count`, which is 0).",
        hints=[
            "A plain `dict` with `setdefault(key, [])` keeps groups in first-appearance order.",
            "Filter out `None` before `Sum`/`Avg`/`Min`/`Max`; return `None` when nothing is left.",
            "`Count(\"*\")` counts rows; `Count(\"field\")` counts non-NULL values.",
        ],
        brute_force="For each distinct key, rescan all rows to collect its members: O(G · R). One bucketing pass makes it O(R).",
        approach="""1. Bucket rows by `row[group_key]`.
2. For each bucket build `{group_key: key}` and add every aggregate using the table in the statement.
3. Return the list of summaries.

**Dry run** shop `north` in the sample data: amounts `[10, None, 2]` → Sum 12; ratings `[4, 5, 3]` → Avg 4.0;
shop `east`: amounts `[None]` → Sum `None`, `Count("amount")` 0, `Count("*")` 1.""",
        complexity="O(R · A) time for R rows and A aggregates, O(R) space for the buckets.",
        pitfalls="""- Treating `None` as 0 changes `Avg` and `Min`.
- Returning 0 instead of `None` for an empty `Sum` (in Django, wrap with `Coalesce(Sum(...), 0)` when you want 0).
- Sorting the groups; the spec asks for first-appearance order. A real database gives no order without `order_by`.
- Dividing by the group size instead of the count of non-NULL values in `Avg`.""",
        follow_up="Add a `distinct` flag for `Count`, and a `filter` argument (conditional aggregation: `Count('id', filter=Q(...))`).",
    ),
),
]
