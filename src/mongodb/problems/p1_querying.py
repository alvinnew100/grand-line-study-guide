"""Problems for the querying module: find, projection, sorting and two styles of pagination."""

_KITCHEN = [
    {"_id": 1, "dish": "ramen", "price": 12, "tags": ["soup", "noodles"], "chef": {"name": "Aiko", "years": 9},
     "ratings": [4, 5, 3]},
    {"_id": 2, "dish": "paella", "price": 19, "tags": ["rice", "seafood"], "chef": {"name": "Mateo", "years": 4},
     "ratings": [5, 5]},
    {"_id": 3, "dish": "borscht", "price": 8, "tags": ["soup"], "chef": {"name": "Olena"}, "ratings": []},
    {"_id": 4, "dish": "dosa", "price": 7, "tags": [], "chef": {"name": "Ravi", "years": 15}, "seasonal": None},
    {"_id": 5, "dish": "tagine", "price": 16, "chef": {"name": "Yasmin", "years": 4}, "ratings": [2, 9],
     "sides": [{"name": "couscous", "kcal": 180}, {"name": "flatbread", "kcal": 260}]},
    {"_id": 6, "dish": "pho", "price": "market", "tags": ["soup", "noodles", "beef"], "ratings": [4],
     "sides": [{"name": "herbs", "kcal": 10}]},
]

_STAFF = [
    {"_id": 1, "name": "Imani", "team": "search", "level": 3, "remote": True},
    {"_id": 2, "name": "Bjorn", "team": "infra", "level": 5},
    {"_id": 3, "name": "Chen", "team": "search", "level": 5, "remote": False},
    {"_id": 4, "name": "Dalia", "team": None, "level": 2},
    {"_id": 5, "name": "Emre", "team": "infra", "level": "contractor"},
    {"_id": 6, "name": "Farah", "level": 3, "remote": True},
    {"_id": 7, "name": "Goran", "team": "data", "level": 4.5},
    {"_id": 8, "name": "Hana", "team": 7, "level": None},
]

_POSTS = [{"_id": i, "created": c, "title": "post-%d" % i}
          for i, c in enumerate([500, 480, 480, 480, 455, 455, 430, 400, 400, 390, 350, 350, 350, 349], start=1)]

PROBLEMS = [
dict(
    id="mongo-find-query",
    title="Implement find() with Query Operators",
    difficulty="Hard",
    pattern="Query Matching",
    kind="function",
    entry="find",
    description=r"""
Write `find(docs, query)`: return the documents of `docs` (a list of dicts) that match `query`, in their
original order. This is a faithful miniature of the matcher inside `db.collection.find()`.

**Query shape.** `query` is a dict and every entry must hold (implicit AND). An entry is one of:

- `"$and": [q1, q2, ...]` - all sub-queries match; `"$or": [q1, ...]` - at least one matches;
- `"<path>": condition` - a field path (dots descend into embedded documents) with a condition. If the
  condition is a non-empty dict whose keys **all** start with `$`, it is an operator document and every
  operator in it must hold; any other value is shorthand for `{"$eq": value}`.

**Resolving a path** gives a list of *found values* (empty list = field missing). Walk the path parts:

- on a dict, follow the key (absent key: nothing found);
- on a list, a part made only of digits is a position (`"sides.0.name"`); any other part is applied to
  every element that is a dict, and all results are collected (`"sides.name"` finds every side's name).

**Candidates.** For each found value `v`, the candidates are `v` itself plus, when `v` is a list, each of
its elements. Operators:

| operator | true when |
|---|---|
| `$eq: x` | some candidate `== x`; additionally `x is None` matches a missing field |
| `$ne: x` | `$eq: x` is false |
| `$gt, $gte, $lt, $lte: x` | some candidate is of the same kind as `x` (both numbers, or both strings) and compares true; booleans are not numbers |
| `$in: [..]` | `$eq` holds for at least one listed value |
| `$nin: [..]` | `$in` is false |
| `$exists: b` | (field found) equals `b` |
| `$not: {ops}` | the operator document `ops` does **not** match |

Note the consequence for arrays: `{"ratings": {"$gt": 8, "$lt": 3}}` matches `ratings = [2, 9]` because
each operator may be satisfied by a different element.

**Example:** docs `[{"_id": 1, "tags": ["a", "b"]}, {"_id": 2, "tags": ["c"]}]`, query `{"tags": "b"}` → the first document.

**Example:** query `{"qty": {"$ne": 5}}` matches documents where `qty` is missing as well as those where it differs from 5.
""",
    starter='''def find(docs: List[dict], query: dict) -> List[dict]:
    pass
''',
    solution='''def find(docs, query):
    def resolve(value, parts):
        if not parts:
            return [value]
        head, rest = parts[0], parts[1:]
        if isinstance(value, dict):
            return resolve(value[head], rest) if head in value else []
        if isinstance(value, list):
            if head.isdigit():
                i = int(head)
                return resolve(value[i], rest) if i < len(value) else []
            out = []
            for item in value:
                if isinstance(item, dict):
                    out.extend(resolve(item, parts))
            return out
        return []

    def is_num(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool)

    def same_kind(a, b):
        return (is_num(a) and is_num(b)) or (isinstance(a, str) and isinstance(b, str))

    compare = {"$gt": lambda a, b: a > b, "$gte": lambda a, b: a >= b,
               "$lt": lambda a, b: a < b, "$lte": lambda a, b: a <= b}

    def test(op, arg, found):
        cands = []
        for v in found:
            cands.append(v)
            if isinstance(v, list):
                cands.extend(v)
        if op == "$eq":
            return any(c == arg for c in cands) or (arg is None and not found)
        if op == "$ne":
            return not test("$eq", arg, found)
        if op == "$in":
            return any(test("$eq", a, found) for a in arg)
        if op == "$nin":
            return not test("$in", arg, found)
        if op == "$exists":
            return bool(found) == bool(arg)
        if op == "$not":
            return not all(test(k, v, found) for k, v in arg.items())
        return any(same_kind(c, arg) and compare[op](c, arg) for c in cands)

    def matches(doc, q):
        for key, cond in q.items():
            if key == "$and":
                ok = all(matches(doc, sub) for sub in cond)
            elif key == "$or":
                ok = any(matches(doc, sub) for sub in cond)
            else:
                found = resolve(doc, key.split("."))
                if isinstance(cond, dict) and cond and all(k.startswith("$") for k in cond):
                    ok = all(test(k, v, found) for k, v in cond.items())
                else:
                    ok = test("$eq", cond, found)
            if not ok:
                return False
        return True

    return [d for d in docs if matches(d, query)]
''',
    tests=[
        [[{"_id": 1, "tags": ["a", "b"]}, {"_id": 2, "tags": ["c"]}], {"tags": "b"}],
        [[{"_id": 1, "qty": 5}, {"_id": 2, "qty": 6}, {"_id": 3}], {"qty": {"$ne": 5}}],
        [_KITCHEN, {}],
        [_KITCHEN, {"price": {"$gte": 8, "$lt": 16}}],
        [_KITCHEN, {"chef.years": 4}],
        [_KITCHEN, {"tags": "soup", "price": {"$lte": 10}}],
        [_KITCHEN, {"ratings": {"$gt": 8, "$lt": 3}}],
        [_KITCHEN, {"sides.kcal": {"$gte": 200}}],
        [_KITCHEN, {"sides.0.name": "herbs"}],
        [_KITCHEN, {"$or": [{"price": {"$lt": 8}}, {"chef.name": {"$in": ["Aiko", "Zed"]}}]}],
        [_KITCHEN, {"seasonal": None}],
        [_KITCHEN, {"seasonal": {"$exists": True}}],
        [_KITCHEN, {"tags": {"$nin": ["soup", "rice"]}}],
        [_KITCHEN, {"price": {"$not": {"$gt": 10}}}],
        [_KITCHEN, {"$and": [{"tags": ["soup"]}, {"ratings": {"$exists": True}}]}],
        [_KITCHEN, {"chef": {"name": "Olena"}, "price": {"$gt": "a"}}],
        [_KITCHEN, {"price": {"$gt": "a"}}],
        [[], {"x": 1}],
    ],
    examples=2,
    wrong_solutions=[
        # no array semantics: compares the field value only
        '''def find(docs, query):
    def get(doc, path):
        cur = doc
        for part in path.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return []
        return [cur]
    def test(op, arg, found):
        if op == "$eq":
            return any(c == arg for c in found) or (arg is None and not found)
        if op == "$ne":
            return not test("$eq", arg, found)
        if op == "$in":
            return any(test("$eq", a, found) for a in arg)
        if op == "$nin":
            return not test("$in", arg, found)
        if op == "$exists":
            return bool(found) == bool(arg)
        if op == "$not":
            return not all(test(k, v, found) for k, v in arg.items())
        f = {"$gt": lambda a, b: a > b, "$gte": lambda a, b: a >= b, "$lt": lambda a, b: a < b, "$lte": lambda a, b: a <= b}[op]
        return any(type(c) == type(arg) and f(c, arg) for c in found)
    def matches(doc, q):
        for key, cond in q.items():
            if key == "$and":
                ok = all(matches(doc, s) for s in cond)
            elif key == "$or":
                ok = any(matches(doc, s) for s in cond)
            else:
                found = get(doc, key)
                if isinstance(cond, dict) and cond and all(k.startswith("$") for k in cond):
                    ok = all(test(k, v, found) for k, v in cond.items())
                else:
                    ok = test("$eq", cond, found)
            if not ok:
                return False
        return True
    return [d for d in docs if matches(d, query)]
''',
        # $ne / $nin / $not ignore missing fields (treat "missing" as no match)
        '''def find(docs, query):
    def resolve(value, parts):
        if not parts:
            return [value]
        head, rest = parts[0], parts[1:]
        if isinstance(value, dict):
            return resolve(value[head], rest) if head in value else []
        if isinstance(value, list):
            if head.isdigit():
                return resolve(value[int(head)], rest) if int(head) < len(value) else []
            out = []
            for item in value:
                if isinstance(item, dict):
                    out.extend(resolve(item, parts))
            return out
        return []
    def num(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool)
    def test(op, arg, found):
        cands = []
        for v in found:
            cands.append(v)
            if isinstance(v, list):
                cands.extend(v)
        if op == "$eq":
            return any(c == arg for c in cands) or (arg is None and not found)
        if op == "$ne":
            return any(c != arg for c in cands)
        if op == "$in":
            return any(test("$eq", a, found) for a in arg)
        if op == "$nin":
            return bool(cands) and not test("$in", arg, found)
        if op == "$exists":
            return bool(found) == bool(arg)
        if op == "$not":
            return bool(cands) and not all(test(k, v, found) for k, v in arg.items())
        f = {"$gt": lambda a, b: a > b, "$gte": lambda a, b: a >= b, "$lt": lambda a, b: a < b, "$lte": lambda a, b: a <= b}[op]
        return any(((num(c) and num(arg)) or (isinstance(c, str) and isinstance(arg, str))) and f(c, arg) for c in cands)
    def matches(doc, q):
        for key, cond in q.items():
            if key == "$and":
                ok = all(matches(doc, s) for s in cond)
            elif key == "$or":
                ok = any(matches(doc, s) for s in cond)
            else:
                found = resolve(doc, key.split("."))
                if isinstance(cond, dict) and cond and all(k.startswith("$") for k in cond):
                    ok = all(test(k, v, found) for k, v in cond.items())
                else:
                    ok = test("$eq", cond, found)
            if not ok:
                return False
        return True
    return [d for d in docs if matches(d, query)]
''',
    ],
    guide=dict(
        prereqs="The lessons *Query operators and how documents match* and *Arrays and embedded documents*. "
                "Comfort with recursion over nested dicts and lists.",
        intuition="A query is a tree of small yes/no tests. Split the work in two: **(1)** turn a dotted path into "
                  "the list of values it can reach inside one document, fanning out across arrays; **(2)** ask each "
                  "operator a question about that list. Almost every surprising MongoDB matching rule (equality "
                  "against an array element, `$ne` matching missing fields, two range operators satisfied by two "
                  "different elements) falls out of treating the field as a *set of candidates* rather than one value.",
        hints=[
            "Write `resolve(value, parts)` recursively first and test it on `sides.kcal` and `sides.0.name` before touching operators.",
            "Build the candidate list once per operator: every found value, plus the elements of any found value that is a list.",
            "Define the negative operators purely as negations: `$ne = not $eq`, `$nin = not $in`, `$not = not (all inner operators)`. Missing fields then behave correctly for free.",
        ],
        brute_force="Special-casing each query shape (`if field has a dot ... elif value is a list ...`) grows into a "
                    "tangle that mishandles combinations such as a dotted path through an array with a range operator. "
                    "The general evaluator below is no slower: it is one pass over the documents either way.",
        approach="""1. `matches(doc, q)` loops over the entries of `q`; `$and` / `$or` recurse on sub-queries.
2. For a field entry, `resolve` returns the found values. On a dict it follows the key; on a list it either
   indexes (digit part) or recurses into each dict element **with the same remaining parts**.
3. Decide whether the condition is an operator document (non-empty dict, all keys start with `$`) or a literal.
4. Evaluate each operator against the candidates; all operators in the document must be true.

**Dry run** - document 5 (`ratings: [2, 9]`) against `{"ratings": {"$gt": 8, "$lt": 3}}`:
found = `[[2, 9]]`, candidates = `[[2, 9], 2, 9]`. `$gt 8`: the list is not a number (skipped), 2 fails, 9
passes → true. `$lt 3`: 2 passes → true. Both hold, so the document matches even though no single rating is
both above 8 and below 3.""",
        complexity="Time O(D · Q · F) for D documents, Q conditions and F candidate values reached per path; space O(F) "
                   "for the candidate list. A real server avoids the D factor with an index.",
        pitfalls="- Treating `{\"chef\": {\"name\": \"Olena\"}}` as an operator document: its key does not start with `$`, so it is an exact-equality test on the whole embedded document.\n"
                 "- Forgetting that `$eq: None` matches a missing field while `$exists: True` does not.\n"
                 "- Comparing a string price with a number: MongoDB range operators only compare within a type bracket, so `\"market\" > 10` must be false, not a `TypeError`.\n"
                 "- Writing `$ne` as *some element differs* instead of *no element equals*.",
        follow_up="Add `$elemMatch` (one element must satisfy all operators), `$size`, `$all` and `$regex`. "
                  "Then add an index: a sorted list of `(value, position)` pairs that lets range operators skip most documents.",
    ),
),
dict(
    id="mongo-projection",
    title="Projection: Include or Exclude Fields",
    difficulty="Medium",
    pattern="Document Shaping",
    kind="function",
    entry="project",
    description=r"""
Implement the second argument of `find()`. `project(docs, spec)` returns a new list with one reshaped
document per input document, in the same order.

`spec` maps field paths to `1` (include) or `0` (exclude).

- If **any** value in `spec` is `1` the projection is in **inclusion mode**: the result holds only the listed
  fields, plus `_id` unless the spec says `"_id": 0`.
- Otherwise it is in **exclusion mode**: the result holds everything except the listed fields. An empty spec
  returns the documents unchanged.
- Apart from `_id`, a spec never mixes `1` and `0` (MongoDB rejects that; the tests do not try it).

**Dotted paths** reach into embedded documents:

- when the parent is a dict, the rule is applied to that dict (inclusion of `a.b` yields `{"a": {"b": ...}}`;
  if `a` is a dict without `b`, the result has `"a": {}`);
- when the parent is a list, the rule is applied to each element that is a dict; in inclusion mode the
  non-dict elements are dropped, in exclusion mode they are kept as they are;
- in inclusion mode, if the parent is a scalar the field is omitted altogether.

Fields missing from a document are absent from its result. Do not modify the input.

**Example:** `[{"_id": 1, "name": "Ada", "age": 36}]`, spec `{"name": 1}` → `[{"_id": 1, "name": "Ada"}]`

**Example:** `[{"_id": 1, "name": "Ada", "geo": {"lat": 1, "lon": 2}}]`, spec `{"_id": 0, "geo.lat": 1}` → `[{"geo": {"lat": 1}}]`
""",
    starter='''def project(docs: List[dict], spec: dict) -> List[dict]:
    pass
''',
    solution='''def project(docs, spec):
    include = any(v == 1 for v in spec.values())
    keep_id = spec.get("_id", 1) == 1
    paths = [k.split(".") for k in spec if k != "_id"]

    def keep(value, group):
        if isinstance(value, list):
            return [keep(x, group) for x in value if isinstance(x, dict)]
        out = {}
        for key, val in value.items():
            subs = [p[1:] for p in group if p[0] == key]
            if not subs:
                continue
            if any(len(s) == 0 for s in subs):
                out[key] = val
            elif isinstance(val, (dict, list)):
                out[key] = keep(val, subs)
        return out

    def drop(value, group):
        if isinstance(value, list):
            return [drop(x, group) if isinstance(x, dict) else x for x in value]
        out = {}
        for key, val in value.items():
            subs = [p[1:] for p in group if p[0] == key]
            if any(len(s) == 0 for s in subs):
                continue
            out[key] = drop(val, subs) if subs and isinstance(val, (dict, list)) else val
        return out

    result = []
    for doc in docs:
        if include:
            new = keep({k: v for k, v in doc.items() if k != "_id"}, paths)
            if keep_id and "_id" in doc:
                new = {"_id": doc["_id"], **new}
        else:
            new = drop(doc, paths)
            if not keep_id:
                new.pop("_id", None)
        result.append(new)
    return result
''',
    tests=[
        [[{"_id": 1, "name": "Ada", "age": 36}], {"name": 1}],
        [[{"_id": 1, "name": "Ada", "geo": {"lat": 1, "lon": 2}}], {"_id": 0, "geo.lat": 1}],
        [_KITCHEN, {}],
        [_KITCHEN, {"_id": 0}],
        [_KITCHEN, {"_id": 1}],
        [_KITCHEN, {"dish": 1, "price": 1, "_id": 0}],
        [_KITCHEN, {"tags": 0, "ratings": 0, "sides": 0}],
        [_KITCHEN, {"chef.name": 1}],
        [_KITCHEN, {"chef.years": 1, "dish": 1}],
        [_KITCHEN, {"chef.years": 0, "_id": 0}],
        [_KITCHEN, {"sides.kcal": 1, "_id": 0}],
        [_KITCHEN, {"sides.kcal": 0, "chef": 0, "tags": 0, "ratings": 0}],
        [[{"_id": 7, "a": 5, "b": [1, {"c": 2, "d": 3}, "x"]}], {"a.z": 1, "b.c": 1}],
        [[{"_id": 7, "a": 5, "b": [1, {"c": 2, "d": 3}, "x"]}], {"a.z": 0, "b.c": 0}],
        [[{"_id": 9, "a": {"b": {"c": 1, "d": 2}, "e": 3}}], {"a.b.c": 1, "a.e": 1}],
        [[], {"x": 1}],
    ],
    examples=2,
    wrong_solutions=[
        '''def project(docs, spec):
    include = any(v == 1 for k, v in spec.items() if k != "_id")
    out = []
    for d in docs:
        if include:
            new = {k: d[k] for k in spec if spec[k] == 1 and k in d}
            if spec.get("_id", 1) == 1 and "_id" in d:
                new["_id"] = d["_id"]
        else:
            new = {k: v for k, v in d.items() if spec.get(k, 1) != 0}
        out.append(new)
    return out
''',
        '''def project(docs, spec):
    include = any(v == 1 for v in spec.values())
    out = []
    for d in docs:
        if include:
            new = {}
            for path in spec:
                if spec[path] != 1:
                    continue
                parts = path.split(".")
                if len(parts) == 1:
                    if path in d:
                        new[path] = d[path]
                elif isinstance(d.get(parts[0]), dict) and parts[1] in d[parts[0]]:
                    new.setdefault(parts[0], {})[parts[1]] = d[parts[0]][parts[1]]
            if "_id" in d:
                new["_id"] = d["_id"]
        else:
            new = {k: v for k, v in d.items() if spec.get(k, 1) != 0}
        out.append(new)
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Cursors, sorting and pagination done right* (projection section). Recursion over nested structures.",
        intuition="A projection is a tree of paths laid over the document tree. Walk both trees together. In inclusion "
                  "mode you copy a field only where the path tree says so; in exclusion mode you copy everything "
                  "*except* where the path tree ends. Arrays are transparent: the rule passes straight through to "
                  "every embedded document inside them.",
        hints=[
            "Decide the mode first: any `1` in the spec (including `_id: 1` on its own) means inclusion.",
            "Split each path on dots. At each level, collect the paths that start with the current key and strip that first part before recursing.",
            "Handle `_id` separately at the top level so the recursive helpers never have to think about it.",
        ],
        brute_force="Deep-copy every document and delete or re-add fields one path at a time. It works for exclusion but "
                    "becomes awkward for inclusion through arrays, and deep-copying everything wastes work when only "
                    "one small field is wanted.",
        approach="""1. `include = any(v == 1 ...)`, `keep_id = spec.get("_id", 1) == 1`, `paths` = split paths except `_id`.
2. `keep(value, group)`: for a list, recurse into dict elements only. For a dict, for each key find the
   sub-paths under it. No sub-paths → skip the key. A sub-path that is now empty → copy the whole value.
   Otherwise recurse if the value is a container (a scalar parent is dropped).
3. `drop(value, group)` mirrors it: an empty sub-path removes the key; a non-empty one recurses; everything else is copied.
4. Add or remove `_id` at the end.

**Dry run** - `{"_id": 7, "a": 5, "b": [1, {"c": 2, "d": 3}, "x"]}` with `{"a.z": 1, "b.c": 1}`:
key `a` has sub-path `["z"]` but `5` is a scalar → omitted. Key `b` has sub-path `["c"]` and is a list → keep
only dict elements, each reduced to `{"c": 2}`. Result `{"_id": 7, "b": [{"c": 2}]}`.""",
        complexity="Time O(total size of the documents × number of paths), space O(size of the output).",
        pitfalls="- `{\"_id\": 1}` alone is inclusion mode and returns only `_id`.\n"
                 "- `{\"_id\": 0}` alone is exclusion mode: every other field survives.\n"
                 "- Including `a.b` where `a` is a dict lacking `b` yields an empty `a`, not a missing `a`.\n"
                 "- Mutating the caller's documents while deleting fields.",
        follow_up="Add `$slice` for arrays and the positional `$` projection. Explain why a covered query needs `_id: 0` "
                  "unless `_id` is part of the index.",
    ),
),
dict(
    id="mongo-sort-multi-key",
    title="Sort by Several Keys with BSON Type Order",
    difficulty="Medium",
    pattern="Sorting",
    kind="function",
    entry="sort_docs",
    description=r"""
Implement `cursor.sort()`. `sort_docs(docs, spec)` returns the documents ordered by `spec`, a list of
`[field, direction]` pairs where direction is `1` (ascending) or `-1` (descending). Earlier pairs are more
significant.

Values of different types are compared by a fixed **type order** first (a simplified version of the BSON
comparison order), and only values of the same type are compared with each other:

1. missing field or `None` (these two are equal to each other)
2. numbers (`int` and `float` compare numerically with each other)
3. strings (ordinary Python string comparison)
4. booleans (`False` before `True`)

Direction `-1` reverses the entire order for that key, type order included. Documents that tie on every
key keep their relative input order (the sort is stable). Fields are top-level and never hold lists or dicts.
Do not modify the input list.

**Example:** docs with `level` values `[3, "x", None, 5]`, spec `[["level", 1]]` → order `None, 3, 5, "x"`.

**Example:** spec `[["team", 1], ["level", -1]]` sorts by team, and inside one team by level descending.
""",
    starter='''def sort_docs(docs: List[dict], spec: List[list]) -> List[dict]:
    pass
''',
    solution='''def sort_docs(docs, spec):
    def keyer(field):
        def key(doc):
            v = doc.get(field)
            if v is None:
                return (0, 0)
            if isinstance(v, bool):
                return (3, v)
            if isinstance(v, (int, float)):
                return (1, v)
            return (2, v)
        return key

    out = list(docs)
    for field, direction in reversed(spec):
        out.sort(key=keyer(field), reverse=(direction == -1))
    return out
''',
    tests=[
        [[{"_id": 1, "level": 3}, {"_id": 2, "level": "x"}, {"_id": 3, "level": None}, {"_id": 4, "level": 5}], [["level", 1]]],
        [_STAFF, [["team", 1], ["level", -1]]],
        [_STAFF, [["level", 1]]],
        [_STAFF, [["level", -1]]],
        [_STAFF, [["remote", 1], ["name", -1]]],
        [_STAFF, [["remote", -1], ["level", 1], ["_id", -1]]],
        [_STAFF, [["team", -1]]],
        [_STAFF, []],
        [_STAFF, [["missing", 1]]],
        [_STAFF, [["missing", -1], ["name", 1]]],
        [[{"_id": 1, "v": 2.5}, {"_id": 2, "v": 2}, {"_id": 3, "v": 10}, {"_id": 4, "v": 2}], [["v", -1]]],
        [[{"_id": 1, "v": True}, {"_id": 2, "v": 0}, {"_id": 3, "v": False}, {"_id": 4, "v": "0"}, {"_id": 5}], [["v", 1]]],
        [[], [["a", 1]]],
        [[{"_id": i, "g": i % 3, "h": (i * 7) % 5} for i in range(60)], [["g", -1], ["h", 1]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def sort_docs(docs, spec):
    def keyer(field):
        def key(doc):
            v = doc.get(field)
            if v is None:
                return (0, 0)
            if isinstance(v, bool):
                return (3, v)
            if isinstance(v, (int, float)):
                return (1, v)
            return (2, v)
        return key
    out = list(docs)
    for field, direction in reversed(spec):
        out = sorted(out, key=keyer(field))
        if direction == -1:
            out = out[::-1]
    return out
''',
        '''def sort_docs(docs, spec):
    def keyer(field):
        def key(doc):
            v = doc.get(field)
            if v is None:
                return (0, 0)
            if isinstance(v, (int, float)):
                return (1, v)
            return (2, v)
        return key
    out = list(docs)
    for field, direction in spec:
        out.sort(key=keyer(field), reverse=(direction == -1))
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Cursors, sorting and pagination done right*. Python's `list.sort(key=...)` and the idea of a stable sort.",
        intuition="Two ideas do all the work. First, map every value to a pair `(type rank, value)` so that Python never "
                  "has to compare a string with a number: tuples compare the rank first. Second, a multi-key sort is "
                  "a sequence of **stable** single-key sorts applied from the *least* significant key to the most "
                  "significant one, exactly like sorting a spreadsheet column by column.",
        hints=[
            "Check `bool` before `int`: in Python `isinstance(True, int)` is true.",
            "Missing and `None` must produce the same key, for example `(0, 0)`.",
            "Sort by the last pair first. Use `reverse=True` rather than reversing the list afterwards, because reversing a list destroys stability.",
        ],
        brute_force="Build one composite key per document and negate numbers for descending order. That breaks down for "
                    "strings (you cannot negate a string) and forces a custom comparator with `functools.cmp_to_key`. "
                    "It is still O(n log n) but harder to get right.",
        approach="""1. `keyer(field)` returns a function mapping a document to `(rank, value)`.
2. Copy the list. For each `[field, direction]` **from last to first**, call `out.sort(key=..., reverse=direction == -1)`.
3. Python guarantees stability even with `reverse=True`, so ties from later (less significant) keys survive.

**Dry run** - spec `[["team", 1], ["level", -1]]` on three docs `A(team=s, level=3)`, `B(team=i, level=5)`,
`C(team=s, level=5)`: sort by level descending → `B, C, A`; then stable sort by team ascending → `B` (i),
`C` (s, 5), `A` (s, 3). Inside team `s` the level order from the first pass is preserved.""",
        complexity="Time O(k · n log n) for k sort keys, space O(n) for the copy.",
        pitfalls="- `sorted(...)[::-1]` reverses ties too, so it is not a stable descending sort.\n"
                 "- Iterating the spec in forward order makes the *last* key the most significant.\n"
                 "- Letting `True` fall into the number bracket, which would sort it next to `1`.",
        follow_up="Real BSON order has more brackets (objects, arrays, ObjectId, dates, regular expressions) and sorts an "
                  "array by its smallest element ascending and its largest descending. Extend the key function to cover them.",
    ),
),
dict(
    id="mongo-skip-limit",
    title="skip() and limit() and What They Cost",
    difficulty="Easy",
    pattern="Pagination",
    kind="function",
    entry="find_page",
    description=r"""
Offset pagination is easy to write and expensive to run: the server has to walk past every skipped entry.
Implement it and report the cost.

`find_page(docs, sort_field, direction, skip, limit)`:

1. Order the documents by `sort_field` (present in every document, all values of one comparable type);
   `direction` is `1` or `-1`. Ties are broken by `_id` **ascending** whatever the direction.
2. Discard the first `skip` documents (`skip >= 0`).
3. Keep at most `limit` documents. As in MongoDB, `limit = 0` means *no limit*.

Return `{"docs": [...], "examined": n}` where `examined` is the number of ordered entries the server had to
walk: `min(len(docs), skip + limit)` when `limit > 0`, and `len(docs)` when `limit == 0`.

**Example:** five docs with scores `[50, 90, 70, 90, 10]` and `_id` 1..5, `find_page(docs, "score", -1, 1, 2)`
→ docs with `_id` 4 and 3, `examined = 3`.
""",
    starter='''def find_page(docs: List[dict], sort_field: str, direction: int, skip: int, limit: int) -> dict:
    pass
''',
    solution='''def find_page(docs, sort_field, direction, skip, limit):
    ordered = sorted(docs, key=lambda d: d["_id"])
    ordered.sort(key=lambda d: d[sort_field], reverse=(direction == -1))
    n = len(ordered)
    if limit > 0:
        page = ordered[skip:skip + limit]
        examined = min(n, skip + limit)
    else:
        page = ordered[skip:]
        examined = n
    return {"docs": page, "examined": examined}
''',
    tests=[
        [[{"_id": i + 1, "score": s} for i, s in enumerate([50, 90, 70, 90, 10])], "score", -1, 1, 2],
        [[{"_id": i + 1, "score": s} for i, s in enumerate([50, 90, 70, 90, 10])], "score", 1, 0, 3],
        [_POSTS, "created", -1, 0, 5],
        [_POSTS, "created", -1, 5, 5],
        [_POSTS, "created", -1, 10, 5],
        [_POSTS, "created", -1, 15, 5],
        [_POSTS, "created", 1, 2, 0],
        [_POSTS, "created", 1, 0, 0],
        [_POSTS, "title", 1, 3, 4],
        [_POSTS[::-1], "created", -1, 1, 3],
        [_POSTS[::-1], "created", 1, 0, 4],
        [[], "created", 1, 0, 10],
        [[{"_id": i, "k": i % 4} for i in range(200, 0, -1)], "k", -1, 49, 3],
    ],
    examples=2,
    wrong_solutions=[
        '''def find_page(docs, sort_field, direction, skip, limit):
    ordered = sorted(docs, key=lambda d: (d[sort_field], d["_id"]), reverse=(direction == -1))
    n = len(ordered)
    if limit > 0:
        return {"docs": ordered[skip:skip + limit], "examined": min(n, skip + limit)}
    return {"docs": ordered[skip:], "examined": n}
''',
        '''def find_page(docs, sort_field, direction, skip, limit):
    ordered = sorted(docs, key=lambda d: d["_id"])
    ordered.sort(key=lambda d: d[sort_field], reverse=(direction == -1))
    page = ordered[skip:skip + limit]
    return {"docs": page, "examined": min(len(ordered), skip + limit)}
''',
    ],
    guide=dict(
        prereqs="Lesson *Cursors, sorting and pagination done right*. Python slicing and stable sorting.",
        intuition="`skip` does not jump; it counts. Even with a perfect index the server walks `skip + limit` index "
                  "entries and throws the first `skip` away, which is why page 5,000 of a feed is slow. The function "
                  "is three slices of a sorted list plus one honest piece of accounting.",
        hints=[
            "Sort by `_id` first, then stable-sort by the sort field; the tie-break then holds in both directions.",
            "Slicing past the end of a list is safe in Python and returns an empty list.",
            "Treat `limit == 0` as a separate branch: the page is everything after `skip` and the whole collection is examined.",
        ],
        brute_force="Repeatedly pop the smallest remaining document `skip + limit` times: O(n · (skip + limit)). Sorting once is simpler and faster.",
        approach="""1. `ordered = sorted(docs, key=_id)`, then `ordered.sort(key=sort_field, reverse=direction == -1)`.
2. `limit > 0`: `page = ordered[skip:skip + limit]`, `examined = min(n, skip + limit)`.
3. `limit == 0`: `page = ordered[skip:]`, `examined = n`.

**Dry run** - scores `[50, 90, 70, 90, 10]`, descending, skip 1, limit 2. Order by score desc with `_id`
ascending ties: `_id` 2 (90), 4 (90), 3 (70), 1 (50), 5 (10). Skip one → start at `_id` 4; take two → `[4, 3]`.
Entries walked: 1 skipped + 2 returned = 3.""",
        complexity="Time O(n log n) for the sort here. On a server with an index on the sort field the cost is O(skip + limit) index entries, which is the number the function reports.",
        pitfalls="- Sorting by the tuple `(field, _id)` with `reverse=True` reverses the `_id` tie-break as well.\n"
                 "- `ordered[skip:skip + 0]` is empty: `limit = 0` needs its own branch.\n"
                 "- Reporting `examined` larger than the collection when the page runs off the end.",
        follow_up="Solve *Range-Based (Keyset) Pagination* next and compare the `examined` figure for page 1,000.",
    ),
),
dict(
    id="mongo-keyset-pagination",
    title="Range-Based (Keyset) Pagination",
    difficulty="Medium",
    pattern="Pagination",
    kind="function",
    entry="next_page",
    description=r"""
Replace `skip` with a bookmark. Every document has an integer `created` timestamp and a unique integer
`_id`. The feed is ordered by `created` **descending**, ties broken by `_id` **descending**.

`next_page(docs, page_size, after)`:

- `after` is `None` for the first page, otherwise `[created, _id]` of the last document the client saw.
- Return the first `page_size` documents that come **strictly after** that position in the feed order
  (`page_size >= 1`). The bookmark document itself may have been deleted since; the function must still work.
- Return `{"items": [...], "next": bookmark}` where `bookmark` is `[created, _id]` of the last returned item
  if at least one more document exists after it, and `None` otherwise (including when `items` is empty).

The equivalent MongoDB filter is
`{$or: [{created: {$lt: c}}, {created: c, _id: {$lt: i}}]}` with `sort({created: -1, _id: -1}).limit(n)`.

**Example:** docs `(created, _id)` = `(480, 2), (480, 3), (500, 1), (455, 5)`, `page_size = 2`, `after = None`
→ items with `_id` 1 then 3, `next = [480, 3]`.

**Example:** same docs, `after = [480, 3]` → items with `_id` 2 then 5, `next = None`.
""",
    starter='''def next_page(docs: List[dict], page_size: int, after: Optional[list]) -> dict:
    pass
''',
    solution='''def next_page(docs, page_size, after):
    ordered = sorted(docs, key=lambda d: (d["created"], d["_id"]), reverse=True)
    if after is not None:
        c, i = after
        ordered = [d for d in ordered if d["created"] < c or (d["created"] == c and d["_id"] < i)]
    items = ordered[:page_size]
    more = len(ordered) > page_size
    nxt = [items[-1]["created"], items[-1]["_id"]] if items and more else None
    return {"items": items, "next": nxt}
''',
    tests=[
        [[{"_id": 2, "created": 480}, {"_id": 3, "created": 480}, {"_id": 1, "created": 500}, {"_id": 5, "created": 455}], 2, None],
        [[{"_id": 2, "created": 480}, {"_id": 3, "created": 480}, {"_id": 1, "created": 500}, {"_id": 5, "created": 455}], 2, [480, 3]],
        [_POSTS, 3, None],
        [_POSTS, 3, [480, 3]],
        [_POSTS, 3, [480, 4]],
        [_POSTS, 5, [455, 5]],
        [_POSTS, 4, [350, 13]],
        [_POSTS, 4, [350, 11]],
        [_POSTS, 14, None],
        [_POSTS, 20, None],
        [_POSTS, 2, [349, 14]],
        [_POSTS, 2, [460, 99]],
        [_POSTS[::-1], 1, [400, 9]],
        [[], 5, None],
        [[{"_id": i, "created": 1000 - i // 6} for i in range(1, 121)], 7, [990, 62]],
    ],
    examples=2,
    wrong_solutions=[
        '''def next_page(docs, page_size, after):
    ordered = sorted(docs, key=lambda d: (d["created"], d["_id"]), reverse=True)
    if after is not None:
        ordered = [d for d in ordered if d["created"] < after[0]]
    items = ordered[:page_size]
    nxt = [items[-1]["created"], items[-1]["_id"]] if items and len(ordered) > page_size else None
    return {"items": items, "next": nxt}
''',
        '''def next_page(docs, page_size, after):
    ordered = sorted(docs, key=lambda d: (d["created"], d["_id"]), reverse=True)
    if after is not None:
        c, i = after
        ordered = [d for d in ordered if d["created"] < c or (d["created"] == c and d["_id"] < i)]
    items = ordered[:page_size]
    nxt = [items[-1]["created"], items[-1]["_id"]] if len(items) == page_size else None
    return {"items": items, "next": nxt}
''',
        '''def next_page(docs, page_size, after):
    ordered = sorted(docs, key=lambda d: (d["created"], d["_id"]), reverse=True)
    start = 0
    if after is not None:
        keys = [[d["created"], d["_id"]] for d in ordered]
        start = keys.index(after) + 1 if after in keys else 0
    items = ordered[start:start + page_size]
    nxt = [items[-1]["created"], items[-1]["_id"]] if items and len(ordered) > start + page_size else None
    return {"items": items, "next": nxt}
''',
    ],
    guide=dict(
        prereqs="Lesson *Cursors, sorting and pagination done right*; the previous problem on `skip` and `limit`.",
        intuition="Instead of telling the server *how many* rows to throw away, tell it *where you stopped*. With a "
                  "compound index on `(created, _id)` the server seeks straight to the bookmark and reads one page. "
                  "The sort key must be unique, otherwise documents sharing a timestamp are skipped or repeated; "
                  "adding `_id` as a tie-breaker makes every position in the feed distinct.",
        hints=[
            "Sort by the tuple `(created, _id)` descending; here reversing the tuple is exactly what the feed order asks for.",
            "\"Strictly after `[c, i]`\" in a descending feed means `created < c`, or `created == c` and `_id < i`.",
            "To know whether more pages exist, compare the number of remaining documents with `page_size` (fetching `page_size + 1` is the production trick).",
        ],
        brute_force="Find the bookmark by scanning the sorted list and slice after it. That is O(n) per page and, worse, "
                    "fails when the bookmark document has been deleted between requests.",
        approach="""1. Sort descending by `(created, _id)`.
2. If `after = [c, i]`, keep documents with `created < c or (created == c and _id < i)`.
3. `items` = first `page_size` of what remains; `next` = last item's key if more remain, else `None`.

**Dry run** - feed order `(500,1) (480,3) (480,2) (455,5)`, `page_size = 2`. First call: items `(500,1) (480,3)`,
two remain beyond the page → `next = [480, 3]`. Second call with `after = [480, 3]`: `(480,2)` qualifies through
the tie-break branch and `(455,5)` through `created < 480`; nothing remains → `next = None`.""",
        complexity="Time O(n log n) here because the list is sorted on each call. With an index on `{created: -1, _id: -1}` a database does O(log n + page_size) work per page regardless of depth.",
        pitfalls="- Filtering on `created < c` alone loses documents that share the bookmark's timestamp.\n"
                 "- Returning a bookmark when the page is exactly full but nothing follows it sends the client to an empty page.\n"
                 "- Looking the bookmark up by identity breaks when it was deleted; compare positions instead.",
        follow_up="Support a caller-chosen sort direction and a `before` bookmark for backwards paging. Encode the bookmark as an opaque base64 string so clients cannot tamper with it casually.",
    ),
),
]
