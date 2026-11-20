"""Problems for the CRUD and index modules."""

_GARAGE = [
    {"_id": 1, "plate": "KX-101", "status": "queued", "visits": 2, "jobs": ["oil"], "owner": {"name": "Noor", "city": "Leeds"}},
    {"_id": 2, "plate": "BD-552", "status": "queued", "visits": 0, "jobs": [], "owner": {"name": "Pavel"}},
    {"_id": 3, "plate": "ZR-900", "status": "done", "jobs": ["tyres", "oil", "tyres"], "owner": {"name": "Sade", "city": "Hull"}},
    {"_id": 4, "plate": "MM-314", "status": "queued", "visits": 7},
]

_PLAYERS = [
    {"_id": 1, "handle": "quill", "score": 40, "region": "eu"},
    {"_id": 2, "handle": "ember", "score": 75, "region": "na"},
    {"_id": 3, "handle": "sable", "score": 75, "region": "eu"},
]

_TRIPS = [
    {"_id": i, "city": c, "km": k, "driver": d}
    for i, (c, k, d) in enumerate([
        ("oslo", 4, "d1"), ("oslo", 12, "d2"), ("oslo", 12, "d1"), ("oslo", 30, "d3"), ("lima", 2, "d1"),
        ("lima", 9, "d2"), ("lima", 18, "d2"), ("kyiv", 12, "d1"), ("kyiv", 25, "d3"), ("kyiv", 31, "d3"),
        ("oslo", 7, "d2"), ("lima", 12, "d3"),
    ], start=1)
] + [{"_id": 13, "city": "oslo", "driver": "d1"}, {"_id": 14, "km": 12, "driver": "d2"}]

_SESSIONS = [
    {"_id": "a", "seen": 100},
    {"_id": "b", "seen": 160},
    {"_id": "c", "seen": "100"},
    {"_id": "d"},
    {"_id": "e", "seen": [400, 130, "x"]},
    {"_id": "f", "seen": True},
    {"_id": "g", "seen": 219.5},
    {"_id": "h", "seen": []},
    {"_id": "i", "seen": None},
    {"_id": "j", "seen": 100},
]

_ESR_CHECKER = '''def check(args, got, expected):
    equality, sort, ranges = args
    if not isinstance(got, list):
        return False
    try:
        fields = [g[0] for g in got]
        dirs = [g[1] for g in got]
    except Exception:
        return False
    if any(d not in (1, -1) for d in dirs):
        return False
    sort_fields = [s[0] for s in sort]
    tail = [r for r in ranges if r not in sort_fields]
    e, s = len(equality), len(sort)
    if len(fields) != e + s + len(tail):
        return False
    if sorted(fields[:e]) != sorted(equality):
        return False
    if fields[e:e + s] != sort_fields:
        return False
    want = [x[1] for x in sort]
    mid = dirs[e:e + s]
    if mid != want and mid != [-d for d in want]:
        return False
    return sorted(fields[e + s:]) == sorted(tail)
'''

PROBLEMS = [
dict(
    id="mongo-update-operators",
    title="Apply Update Operators",
    difficulty="Medium",
    pattern="Document Updates",
    kind="function",
    entry="apply_update",
    description=r"""
Implement `updateMany` for six operators. `apply_update(docs, filter, update)` returns
`{"matched": m, "modified": k, "docs": [...]}` where `docs` is the whole collection after the update, in the
original order. The input must not be mutated.

**Filter.** A flat dict of top-level `field: value` pairs. A document matches when every listed field is
present and equal. `{}` matches every document.

**Update.** A dict of operators, applied in the order they appear; inside an operator the fields are
applied in order. Field paths may be dotted and descend through embedded documents (never arrays).

| operator | effect on each `path: value` |
|---|---|
| `$set` | assign `value` (creating missing parent documents) |
| `$unset` | remove the field if it exists (the value is ignored; nothing is created) |
| `$inc` | add `value`; a missing field starts from 0 (parents are created) |
| `$push` | append `value` to the array; a missing field becomes `[value]` |
| `$addToSet` | append `value` only if no equal element is present; a missing field becomes `[value]` |
| `$pull` | remove every element equal to `value`; a missing field is left alone |

`matched` counts documents selected by the filter. `modified` counts matched documents whose content
actually changed (setting a field to the value it already has does not count), mirroring
`matchedCount` / `modifiedCount`.

**Example:** `[{"_id": 1, "n": 1}]`, filter `{"_id": 1}`, update `{"$inc": {"n": 2}, "$set": {"tag.new": True}}`
→ docs `[{"_id": 1, "n": 3, "tag": {"new": True}}]`, matched 1, modified 1.

**Example:** `[{"_id": 1, "n": 1}]`, filter `{}`, update `{"$set": {"n": 1}}` → matched 1, modified 0.
""",
    starter='''def apply_update(docs: List[dict], filter: dict, update: dict) -> dict:
    pass
''',
    solution='''def apply_update(docs, filter, update):
    import copy

    def locate(doc, path, create):
        parts = path.split(".")
        cur = doc
        for p in parts[:-1]:
            if not isinstance(cur.get(p), dict):
                if not create:
                    return None, parts[-1]
                cur[p] = {}
            cur = cur[p]
        return cur, parts[-1]

    out, matched, modified = [], 0, 0
    for doc in docs:
        if not all(k in doc and doc[k] == v for k, v in filter.items()):
            out.append(copy.deepcopy(doc))
            continue
        matched += 1
        new = copy.deepcopy(doc)
        for op, fields in update.items():
            for path, val in fields.items():
                target, key = locate(new, path, op not in ("$unset", "$pull"))
                if target is None:
                    continue
                if op == "$set":
                    target[key] = val
                elif op == "$unset":
                    target.pop(key, None)
                elif op == "$inc":
                    target[key] = target.get(key, 0) + val
                elif op == "$push":
                    target.setdefault(key, []).append(val)
                elif op == "$addToSet":
                    arr = target.setdefault(key, [])
                    if val not in arr:
                        arr.append(val)
                elif op == "$pull":
                    if key in target:
                        target[key] = [x for x in target[key] if x != val]
        if new != doc:
            modified += 1
        out.append(new)
    return {"matched": matched, "modified": modified, "docs": out}
''',
    tests=[
        [[{"_id": 1, "n": 1}], {"_id": 1}, {"$inc": {"n": 2}, "$set": {"tag.new": True}}],
        [[{"_id": 1, "n": 1}], {}, {"$set": {"n": 1}}],
        [_GARAGE, {"status": "queued"}, {"$set": {"status": "active"}, "$inc": {"visits": 1}}],
        [_GARAGE, {"status": "queued"}, {"$set": {"status": "queued"}}],
        [_GARAGE, {}, {"$push": {"jobs": "wash"}}],
        [_GARAGE, {}, {"$addToSet": {"jobs": "oil"}}],
        [_GARAGE, {}, {"$pull": {"jobs": "tyres"}}],
        [_GARAGE, {"_id": 3}, {"$pull": {"jobs": "brakes"}, "$unset": {"owner.zip": ""}}],
        [_GARAGE, {}, {"$unset": {"owner.city": "", "visits": ""}}],
        [_GARAGE, {"status": "done", "plate": "ZR-900"}, {"$set": {"owner.contact.phone": "555"}, "$inc": {"owner.loyalty": 10}}],
        [_GARAGE, {"status": "scrapped"}, {"$set": {"x": 1}}],
        [_GARAGE, {"visits": 0}, {"$inc": {"visits": -3}, "$push": {"log.events": "reset"}}],
        [_GARAGE, {"owner": {"name": "Pavel"}}, {"$addToSet": {"jobs": "oil"}, "$push": {"jobs": "oil"}}],
        [[], {}, {"$set": {"a": 1}}],
        [[{"_id": 1, "a": {"b": 1}}, {"_id": 2}], {}, {"$unset": {"a.b": ""}, "$pull": {"c.d": 1}}],
    ],
    examples=2,
    wrong_solutions=[
        '''def apply_update(docs, filter, update):
    import copy
    out, matched, modified = [], 0, 0
    for doc in docs:
        new = copy.deepcopy(doc)
        if all(k in doc and doc[k] == v for k, v in filter.items()):
            matched += 1
            modified += 1
            for op, fields in update.items():
                for key, val in fields.items():
                    if op == "$set":
                        new[key] = val
                    elif op == "$unset":
                        new.pop(key, None)
                    elif op == "$inc":
                        new[key] = new.get(key, 0) + val
                    elif op == "$push":
                        new.setdefault(key, []).append(val)
                    elif op == "$addToSet":
                        if val not in new.setdefault(key, []):
                            new[key].append(val)
                    elif op == "$pull" and key in new:
                        new[key] = [x for x in new[key] if x != val]
        out.append(new)
    return {"matched": matched, "modified": modified, "docs": out}
''',
        '''def apply_update(docs, filter, update):
    import copy
    def locate(doc, path):
        parts = path.split(".")
        cur = doc
        for p in parts[:-1]:
            if not isinstance(cur.get(p), dict):
                cur[p] = {}
            cur = cur[p]
        return cur, parts[-1]
    out, matched, modified = [], 0, 0
    for doc in docs:
        if not all(k in doc and doc[k] == v for k, v in filter.items()):
            out.append(copy.deepcopy(doc))
            continue
        matched += 1
        new = copy.deepcopy(doc)
        for op, fields in update.items():
            for path, val in fields.items():
                target, key = locate(new, path)
                if op == "$set":
                    target[key] = val
                elif op == "$unset":
                    target.pop(key, None)
                elif op == "$inc":
                    target[key] = target.get(key, 0) + val
                elif op in ("$push", "$addToSet"):
                    target.setdefault(key, []).append(val)
                elif op == "$pull":
                    target[key] = [x for x in target.get(key, []) if x != val][:-1]
        if new != doc:
            modified += 1
        out.append(new)
    return {"matched": matched, "modified": modified, "docs": out}
''',
    ],
    guide=dict(
        prereqs="Lesson *Update operators, arrays and upserts*. `copy.deepcopy`, `dict.setdefault`.",
        intuition="Every operator is a tiny function of *(parent document, last key, value)*. Write one helper that "
                  "walks a dotted path to the parent and optionally creates what is missing, and each operator "
                  "becomes a one-liner. `modified` needs no bookkeeping at all: compare the copy with the original.",
        hints=[
            "Split the path, walk all parts but the last, and return the dict that should hold the final key.",
            "Creating operators (`$set`, `$inc`, `$push`, `$addToSet`) build missing parents; removing operators (`$unset`, `$pull`) must not.",
            "Deep-copy each matched document before editing it, then test `new != doc` to decide whether it was modified.",
        ],
        brute_force="Handle only top-level keys with `doc[key] = value`. It passes the simple cases and silently writes a "
                    "literal key called `\"owner.city\"` for dotted paths, which is exactly the bug a dotted-path helper prevents.",
        approach="""1. For each document test the filter (`k in doc and doc[k] == v`). Non-matching documents are copied through.
2. Deep-copy the match and loop over operators in order, then over their fields.
3. `locate(new, path, create)` returns `(parent, key)` or `(None, key)` when a parent is missing and may not be created.
4. Apply the operator on `parent[key]`; finally `modified += new != doc`.

**Dry run** - `{"_id": 3, "jobs": ["tyres", "oil", "tyres"]}` with `{"$pull": {"jobs": "tyres"}}`: parent is the
document itself, key `jobs`; the filtered list is `["oil"]`; the copy differs from the original → modified.
The same update on `{"_id": 2, "jobs": []}` produces `[]` again → matched but not modified.""",
        complexity="Time O(n · u · d) for n documents, u field updates and path depth d (plus the deep copy); space O(size of the collection) for the result.",
        pitfalls="- Counting every matched document as modified.\n"
                 "- Letting `$unset` or `$pull` create empty parent documents as a side effect.\n"
                 "- `$addToSet` appending duplicates, or `$push` refusing them: the two differ only in that check.\n"
                 "- Mutating the caller's list, which makes the modified check always false.",
        follow_up="Add `$each` for `$push` / `$addToSet`, `$pop`, `$rename`, `$min` / `$max`, and array positions such as `jobs.0`. "
                  "Reject updates where two operators touch the same path, as the server does.",
    ),
),
dict(
    id="mongo-upsert",
    title="updateOne with Upsert Semantics",
    difficulty="Medium",
    pattern="Document Updates",
    kind="function",
    entry="update_one",
    description=r"""
An upsert means *update the matching document, or insert one if nothing matches*. Implement
`update_one(docs, filter, update, upsert)` and return `{"docs": [...], "matched": 0 or 1, "upserted_id": id or None}`.
The input must not be mutated.

**Filter.** Top-level fields only. A condition is either a literal (the field must be present and equal) or
an operator dict using `$gt`, `$gte`, `$lt`, `$lte` on numbers (the field must be present and satisfy all of them).

**Update.** May contain `$set`, `$inc` and `$setOnInsert`, each a dict of top-level `field: value` pairs.

**Behaviour.**

1. If at least one document matches, update the **first** match in list order: apply `$set`, then `$inc`
   (a missing field starts from 0). `$setOnInsert` is ignored. Result: `matched = 1`, `upserted_id = None`.
2. If nothing matches and `upsert` is false, nothing changes: `matched = 0`, `upserted_id = None`.
3. If nothing matches and `upsert` is true, build a new document:
   - start with the **literal equality** conditions of the filter (operator conditions contribute nothing);
   - apply `$set`, then `$inc`, then `$setOnInsert`;
   - if it still has no `_id`, assign `max(existing integer _ids) + 1` (or `1` for an empty collection) and
     put it first;
   - append it to the collection. Result: `matched = 0`, `upserted_id` = the new `_id`.

**Example:** docs `[{"_id": 1, "sku": "a", "qty": 2}]`, filter `{"sku": "b"}`, update `{"$inc": {"qty": 5}, "$setOnInsert": {"new": True}}`,
upsert true → a second document `{"_id": 2, "sku": "b", "qty": 5, "new": True}`, `upserted_id = 2`.

**Example:** same call with filter `{"sku": "a"}` → `qty` becomes 7, no `new` field, `matched = 1`.
""",
    starter='''def update_one(docs: List[dict], filter: dict, update: dict, upsert: bool) -> dict:
    pass
''',
    solution='''def update_one(docs, filter, update, upsert):
    import copy
    ops = {"$gt": lambda a, b: a > b, "$gte": lambda a, b: a >= b,
           "$lt": lambda a, b: a < b, "$lte": lambda a, b: a <= b}

    def matches(doc):
        for field, cond in filter.items():
            if field not in doc:
                return False
            if isinstance(cond, dict):
                if not all(ops[op](doc[field], x) for op, x in cond.items()):
                    return False
            elif doc[field] != cond:
                return False
        return True

    def apply(doc, inserting):
        for k, v in update.get("$set", {}).items():
            doc[k] = v
        for k, v in update.get("$inc", {}).items():
            doc[k] = doc.get(k, 0) + v
        if inserting:
            for k, v in update.get("$setOnInsert", {}).items():
                doc[k] = v

    out = copy.deepcopy(docs)
    for doc in out:
        if matches(doc):
            apply(doc, False)
            return {"docs": out, "matched": 1, "upserted_id": None}
    if not upsert:
        return {"docs": out, "matched": 0, "upserted_id": None}
    new = {k: v for k, v in filter.items() if not isinstance(v, dict)}
    apply(new, True)
    if "_id" not in new:
        ids = [d["_id"] for d in out if isinstance(d.get("_id"), int)]
        new = {"_id": max(ids, default=0) + 1, **new}
    out.append(new)
    return {"docs": out, "matched": 0, "upserted_id": new["_id"]}
''',
    tests=[
        [[{"_id": 1, "sku": "a", "qty": 2}], {"sku": "b"}, {"$inc": {"qty": 5}, "$setOnInsert": {"new": True}}, True],
        [[{"_id": 1, "sku": "a", "qty": 2}], {"sku": "a"}, {"$inc": {"qty": 5}, "$setOnInsert": {"new": True}}, True],
        [_PLAYERS, {"score": 75}, {"$set": {"badge": "gold"}}, False],
        [_PLAYERS, {"handle": "onyx"}, {"$set": {"badge": "gold"}}, False],
        [_PLAYERS, {"handle": "onyx", "region": "ap"}, {"$inc": {"score": 10}}, True],
        [_PLAYERS, {"handle": "onyx", "score": {"$gte": 50}}, {"$set": {"region": "sa"}, "$setOnInsert": {"score": 0}}, True],
        [_PLAYERS, {"score": {"$gt": 40, "$lt": 80}, "region": "eu"}, {"$inc": {"score": 1}, "$setOnInsert": {"fresh": True}}, True],
        [_PLAYERS, {"_id": 9}, {"$set": {"handle": "nine"}}, True],
        [_PLAYERS, {"score": {"$gt": 100}}, {"$set": {"handle": "top"}}, True],
        [[], {"k": "v"}, {"$inc": {"n": 1}}, True],
        [[], {"k": "v"}, {"$inc": {"n": 1}}, False],
        [[{"_id": 5, "k": "v"}, {"_id": 2, "k": "w"}], {"k": "z"}, {"$set": {"k": "y"}, "$setOnInsert": {"_id": 77}}, True],
        [[{"_id": 5, "k": "v"}, {"_id": 2, "k": "w"}], {"missing": {"$lt": 3}}, {"$set": {"seen": 1}}, True],
        [_PLAYERS, {}, {"$inc": {"score": -40, "strikes": 1}}, True],
    ],
    examples=2,
    wrong_solutions=[
        '''def update_one(docs, filter, update, upsert):
    import copy
    out = copy.deepcopy(docs)
    def apply(doc):
        for k, v in update.get("$set", {}).items():
            doc[k] = v
        for k, v in update.get("$inc", {}).items():
            doc[k] = doc.get(k, 0) + v
        for k, v in update.get("$setOnInsert", {}).items():
            doc[k] = v
    for doc in out:
        if all(k in doc and doc[k] == v for k, v in filter.items()):
            apply(doc)
            return {"docs": out, "matched": 1, "upserted_id": None}
    if not upsert:
        return {"docs": out, "matched": 0, "upserted_id": None}
    new = dict(filter)
    apply(new)
    if "_id" not in new:
        new["_id"] = max([d["_id"] for d in out], default=0) + 1
    out.append(new)
    return {"docs": out, "matched": 0, "upserted_id": new["_id"]}
''',
        '''def update_one(docs, filter, update, upsert):
    import copy
    ops = {"$gt": lambda a, b: a > b, "$gte": lambda a, b: a >= b, "$lt": lambda a, b: a < b, "$lte": lambda a, b: a <= b}
    def matches(doc):
        for f, c in filter.items():
            if f not in doc:
                return False
            if isinstance(c, dict):
                if not all(ops[o](doc[f], x) for o, x in c.items()):
                    return False
            elif doc[f] != c:
                return False
        return True
    out = copy.deepcopy(docs)
    hit = False
    for doc in out:
        if matches(doc):
            hit = True
            for k, v in update.get("$set", {}).items():
                doc[k] = v
            for k, v in update.get("$inc", {}).items():
                doc[k] = doc.get(k, 0) + v
    if hit:
        return {"docs": out, "matched": 1, "upserted_id": None}
    if not upsert:
        return {"docs": out, "matched": 0, "upserted_id": None}
    new = {k: v for k, v in filter.items() if not isinstance(v, dict)}
    for k, v in update.get("$set", {}).items():
        new[k] = v
    for k, v in update.get("$inc", {}).items():
        new[k] = new.get(k, 0) + v
    if "_id" not in new:
        new["_id"] = max([d["_id"] for d in out], default=0) + 1
    out.append(new)
    return {"docs": out, "matched": 0, "upserted_id": new["_id"]}
''',
    ],
    guide=dict(
        prereqs="Lesson *Update operators, arrays and upserts* and the previous problem.",
        intuition="An upsert is one decision made atomically on the server: *found* → ordinary update; *not found* → "
                  "the filter itself becomes the seed of a new document. Only the parts of the filter that pin a "
                  "field to one exact value can seed anything; a range such as `score >= 50` does not say what the "
                  "score should be. `$setOnInsert` exists for fields that should be written once, at creation, and "
                  "never overwritten by later updates.",
        hints=[
            "Write `matches(doc)` and `apply(doc, inserting)` as two helpers; the three outcomes are then a few lines each.",
            "Seed the new document with `{k: v for k, v in filter.items() if not isinstance(v, dict)}`.",
            "Apply `$setOnInsert` last and only on the insert path; generate `_id` only if none of the previous steps supplied one.",
        ],
        brute_force="A read followed by a separate insert-or-update (`if find_one(...): update else: insert`). In a real "
                    "system two clients can both see *not found* and both insert; the single-operation upsert backed "
                    "by a unique index is what removes that race.",
        approach="""1. Deep-copy the collection.
2. Scan for the first match. If found: `$set`, `$inc`, return `matched = 1`.
3. Otherwise, if `upsert` is false return unchanged.
4. Otherwise seed from literal filter fields, apply `$set`, `$inc`, `$setOnInsert`, assign `_id` if absent, append.

**Dry run** - players with handles quill/ember/sable, filter `{"handle": "onyx", "score": {"$gte": 50}}`,
update `{"$set": {"region": "sa"}, "$setOnInsert": {"score": 0}}`: nobody is called onyx → seed `{"handle": "onyx"}`
(the range on `score` contributes nothing) → `$set` adds `region` → `$setOnInsert` adds `score: 0` → `_id = 4`.""",
        complexity="Time O(n) to find the first match plus O(size) for the copy; space O(size of the collection).",
        pitfalls="- Copying operator conditions into the new document (`\"score\": {\"$gte\": 50}` stored as a value).\n"
                 "- Applying `$setOnInsert` on the update path.\n"
                 "- Updating every match: `updateOne` touches only the first.\n"
                 "- Overwriting an `_id` that the filter or `$setOnInsert` already provided.",
        follow_up="Explain why concurrent upserts on the same key can still create duplicates unless a unique index backs "
                  "the filter fields, and how the driver retries the losing write as an update.",
    ),
),
dict(
    id="mongo-index-prefix-covered",
    title="Can This Compound Index Serve the Query?",
    difficulty="Easy",
    pattern="Index Selection",
    kind="function",
    entry="analyze_index",
    description=r"""
A compound index can only be entered through its **leading fields**. Given

- `index`: the ordered list of field names in a compound index,
- `query_fields`: the list of fields the query filters on with equality,
- `projection`: the list of fields the query returns (`_id` is returned only if it is listed; an **empty**
  list means "no projection - return whole documents"),

return a dict with four keys:

- `"prefix_len"`: how many fields at the **start** of the index, counted consecutively, appear in `query_fields`;
- `"usable"`: `True` when `prefix_len >= 1`;
- `"residual"`: the sorted list of query fields that are *not* among those first `prefix_len` index fields
  (these must be checked after the index bounds have been applied);
- `"covered"`: `True` when the index is usable, the projection is non-empty, and every query field and every
  projected field is a field of the index (anywhere in it), so no document needs to be fetched.

**Example:** index `["city", "km", "driver"]`, query fields `["city", "driver"]`, projection `["city", "driver"]`
→ `{"prefix_len": 1, "usable": True, "residual": ["driver"], "covered": True}`

**Example:** same index, query fields `["km"]`, projection `["km"]` → `prefix_len 0`, not usable, residual `["km"]`, not covered.
""",
    starter='''def analyze_index(index: List[str], query_fields: List[str], projection: List[str]) -> dict:
    pass
''',
    solution='''def analyze_index(index, query_fields, projection):
    wanted = set(query_fields)
    prefix_len = 0
    for field in index:
        if field not in wanted:
            break
        prefix_len += 1
    usable = prefix_len >= 1
    used = set(index[:prefix_len])
    residual = sorted(f for f in wanted if f not in used)
    in_index = set(index)
    covered = (usable and len(projection) > 0
               and all(f in in_index for f in wanted)
               and all(f in in_index for f in projection))
    return {"prefix_len": prefix_len, "usable": usable, "residual": residual, "covered": covered}
''',
    tests=[
        [["city", "km", "driver"], ["city", "driver"], ["city", "driver"]],
        [["city", "km", "driver"], ["km"], ["km"]],
        [["city", "km", "driver"], ["driver", "km", "city"], ["km"]],
        [["city", "km", "driver"], ["city", "km"], []],
        [["city", "km", "driver"], ["city", "km"], ["_id", "km"]],
        [["city", "km", "driver"], ["city", "fare"], ["city"]],
        [["city", "km", "driver"], ["city"], ["city", "fare"]],
        [["city", "km", "driver"], [], ["city"]],
        [["_id"], ["_id"], ["_id"]],
        [["email"], ["email", "active"], ["email"]],
        [["a", "b", "c", "d"], ["a", "b", "d"], ["c"]],
        [["a", "b", "c", "d"], ["b", "c", "d"], ["b"]],
        [["a", "b", "c", "d"], ["d", "c", "b", "a"], ["a", "b", "c", "d"]],
        [["tenant", "created"], ["tenant"], ["created", "tenant"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def analyze_index(index, query_fields, projection):
    wanted = set(query_fields)
    prefix_len = sum(1 for f in index if f in wanted)
    used = set(index[:prefix_len])
    covered = prefix_len >= 1 and len(projection) > 0 and all(f in index for f in wanted) and all(f in index for f in projection)
    return {"prefix_len": prefix_len, "usable": prefix_len >= 1, "residual": sorted(f for f in wanted if f not in used), "covered": covered}
''',
        '''def analyze_index(index, query_fields, projection):
    wanted = set(query_fields)
    prefix_len = 0
    for f in index:
        if f not in wanted:
            break
        prefix_len += 1
    used = set(index[:prefix_len])
    covered = prefix_len >= 1 and all(f in index for f in projection)
    return {"prefix_len": prefix_len, "usable": prefix_len >= 1, "residual": sorted(f for f in wanted if f not in used), "covered": covered}
''',
    ],
    guide=dict(
        prereqs="Lessons *Single-field and compound indexes: the ESR rule* and *Reading explain output and covered queries*.",
        intuition="A compound index is a phone book sorted by surname, then first name, then street. You can look up a "
                  "surname, or a surname plus first name, but you cannot jump to everybody called *Ada* without "
                  "knowing the surname. So walk the index fields from the left and stop at the first one the query "
                  "does not constrain. Coverage is a separate question: is every field the query touches or returns "
                  "physically present in the index entries?",
        hints=[
            "Loop over `index` in order and `break` at the first field not in the query.",
            "The residual is computed against the prefix actually used, not against the whole index.",
            "For `covered`, an empty projection means whole documents are wanted, which an index can never supply.",
        ],
        brute_force="Counting how many index fields appear anywhere in the query overstates the prefix: for index "
                    "`[a, b, c, d]` and query `{a, b, d}` only `a, b` narrow the scan; `d` sits after a gap.",
        approach="""1. `prefix_len`: leading run of index fields found in the query.
2. `usable = prefix_len >= 1`.
3. `residual = sorted(query fields - index[:prefix_len])`.
4. `covered = usable and projection and (query fields ∪ projection) ⊆ index fields`.

**Dry run** - index `[city, km, driver]`, query `{city, driver}`, projection `[city, driver]`. `city` is in the
query (1), `km` is not → stop: prefix 1. Residual `[driver]`: it is filtered from the index keys after the
`city` bounds. All of `city, driver` live in the index → covered: the server answers from index keys alone.""",
        complexity="Time O(i + q + p) with sets, space O(i + q).",
        pitfalls="- Counting index fields after a gap as part of the prefix.\n"
                 "- Calling a query covered when the default `_id` is returned but `_id` is not in the index.\n"
                 "- Forgetting that the *query* fields must be in the index too, not only the projected ones.",
        follow_up="Extend the analysis to a sort specification: an index can also provide the sort when the sort fields follow the equality prefix in index order.",
    ),
),
dict(
    id="mongo-esr-index-order",
    title="Order a Compound Index by Equality, Sort, Range",
    difficulty="Medium",
    pattern="Index Selection",
    kind="function",
    entry="best_index",
    checker=_ESR_CHECKER,
    description=r"""
Given the shape of a query, design the compound index for it using the **ESR rule**: fields tested for
**E**quality first, then the **S**ort fields, then fields filtered by a **R**ange.

`best_index(equality, sort, ranges)`:

- `equality`: list of field names compared with an exact value;
- `sort`: list of `[field, direction]` pairs (direction `1` or `-1`), in sort order;
- `ranges`: list of field names filtered with `$gt` / `$lt` / `$in`-style ranges.

Return the index as a list of `[field, direction]` pairs such that

1. all equality fields come first (any order among themselves, any direction);
2. then the sort fields in exactly the given order, with either exactly the given directions or **all** of
   them flipped (an index can be walked backwards);
3. then the range fields (any order, any direction). A range field that is also a sort field appears only
   once, in its sort position.

Equality fields never overlap with the other two lists. Any index satisfying the rules is accepted.

**Example:** `equality = ["status"]`, `sort = [["created", -1]]`, `ranges = ["total"]`
→ `[["status", 1], ["created", -1], ["total", 1]]`

**Example:** `equality = []`, `sort = [["price", 1]]`, `ranges = ["price"]` → `[["price", 1]]`
""",
    starter='''def best_index(equality: List[str], sort: List[list], ranges: List[str]) -> List[list]:
    pass
''',
    solution='''def best_index(equality, sort, ranges):
    index = [[f, 1] for f in equality]
    index += [[f, d] for f, d in sort]
    sort_fields = {f for f, _ in sort}
    index += [[f, 1] for f in ranges if f not in sort_fields]
    return index
''',
    tests=[
        [["status"], [["created", -1]], ["total"]],
        [[], [["price", 1]], ["price"]],
        [["tenant", "kind"], [["score", -1], ["name", 1]], ["age", "height"]],
        [["tenant"], [], ["age"]],
        [["tenant"], [["created", 1]], []],
        [[], [], ["age"]],
        [["a"], [], []],
        [[], [["x", -1], ["y", -1], ["z", 1]], []],
        [["u"], [["t", -1]], ["t", "v"]],
        [["u", "w"], [["t", 1], ["s", -1]], ["s", "t"]],
        [[], [], []],
        [["region", "plan", "active"], [["last_seen", -1]], ["spend"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def best_index(equality, sort, ranges):
    return [[f, 1] for f in equality] + [[f, 1] for f in ranges] + [[f, d] for f, d in sort]
''',
        '''def best_index(equality, sort, ranges):
    return [[f, 1] for f in equality] + [[f, 1] for f, d in sort] + [[f, 1] for f in ranges if f not in [s[0] for s in sort]]
''',
        '''def best_index(equality, sort, ranges):
    return [[f, 1] for f in equality] + [[f, d] for f, d in sort] + [[f, 1] for f in ranges]
''',
    ],
    guide=dict(
        prereqs="Lesson *Single-field and compound indexes: the ESR rule*.",
        intuition="Equality fields pin the scan to one contiguous slice of the index. Inside that slice the entries "
                  "are ordered by the *next* index field, so if that next field is the sort field the results come "
                  "out already sorted and no in-memory sort is needed. A range field placed before the sort field "
                  "would fan the scan out across many sub-slices, each sorted on its own, and the server would have "
                  "to merge or re-sort them. Hence: equality, then sort, then range.",
        hints=[
            "The answer is three list concatenations.",
            "Keep the sort directions exactly as given; mixed directions such as `score: -1, name: 1` cannot be replaced by all-ascending.",
            "Filter the range list so a field already used for sorting is not repeated.",
        ],
        brute_force="Trying every permutation of the fields and scoring each one against the three rules works for a "
                    "handful of fields but is O(k!) and unnecessary: the rule is constructive.",
        approach="""1. `[f, 1]` for each equality field.
2. `[f, d]` for each sort pair, unchanged.
3. `[f, 1]` for each range field not already present as a sort field.

**Dry run** - `equality = ["u"]`, `sort = [["t", -1]]`, `ranges = ["t", "v"]`: step 1 gives `[u, 1]`; step 2
adds `[t, -1]`; step 3 skips `t` (already a sort key) and adds `[v, 1]` → `[[u, 1], [t, -1], [v, 1]]`.""",
        complexity="Time and space O(e + s + r).",
        pitfalls="- Putting range before sort (the common ERS mistake) forces a blocking in-memory sort.\n"
                 "- Normalising all directions to ascending: only a full flip of every sort direction is equivalent.\n"
                 "- Repeating a field that is both sorted and range-filtered.",
        follow_up="ESR is a guideline, not a law: when the range is extremely selective and the sort is over a few rows, "
                  "ERS can examine fewer keys. Use `explain(\"executionStats\")` to compare `totalKeysExamined` and the presence of a `SORT` stage.",
    ),
),
dict(
    id="mongo-explain-scan-count",
    title="Explain: Keys and Documents Examined",
    difficulty="Medium",
    pattern="Index Selection",
    kind="function",
    entry="explain",
    description=r"""
Reproduce the three numbers at the heart of `explain("executionStats")`.

`explain(docs, index, query)`:

- `index` is `None` or a list of field names (a compound index).
- `query` maps top-level fields to a condition: a literal (equality) or a dict of `$gt` / `$gte` / `$lt` / `$lte`
  bounds (a range). A document missing the field never satisfies a condition on it.

**Planning rule.** Walk the index fields from the left to build the *bounds prefix*:

- field not in the query → stop;
- equality condition → add it to the prefix and continue;
- range condition → add it to the prefix and stop.

If the prefix is empty (or `index` is `None`) the plan is a collection scan.

Return `{"stage", "keysExamined", "docsExamined", "nReturned"}`:

| plan | `stage` | `keysExamined` | `docsExamined` |
|---|---|---|---|
| collection scan | `"COLLSCAN"` | 0 | `len(docs)` |
| index scan | `"IXSCAN"` | documents satisfying every **prefix** condition | of those keys, the ones that also satisfy the conditions on any **other index fields** in the query (checked on the key, without fetching) |

`nReturned` is always the number of documents satisfying the whole query.

**Example:** 6 docs, index `["city", "km"]`, query `{"city": "oslo", "km": {"$gte": 10}}` where 4 docs are in
oslo and 3 of those have `km >= 10` → `IXSCAN`, keys 3, docs 3, returned 3.

**Example:** same docs, index `["km"]`, query `{"city": "oslo"}` → `COLLSCAN`, keys 0, docs 6.
""",
    starter='''def explain(docs: List[dict], index: Optional[List[str]], query: dict) -> dict:
    pass
''',
    solution='''def explain(docs, index, query):
    ops = {"$gt": lambda a, b: a > b, "$gte": lambda a, b: a >= b,
           "$lt": lambda a, b: a < b, "$lte": lambda a, b: a <= b}

    def holds(doc, field):
        if field not in doc:
            return False
        cond = query[field]
        if isinstance(cond, dict):
            return all(ops[op](doc[field], x) for op, x in cond.items())
        return doc[field] == cond

    prefix = []
    for field in index or []:
        if field not in query:
            break
        prefix.append(field)
        if isinstance(query[field], dict):
            break
    n_returned = sum(1 for d in docs if all(holds(d, f) for f in query))
    if not prefix:
        return {"stage": "COLLSCAN", "keysExamined": 0, "docsExamined": len(docs), "nReturned": n_returned}
    keys = [d for d in docs if all(holds(d, f) for f in prefix)]
    others = [f for f in index if f in query and f not in prefix]
    fetched = [d for d in keys if all(holds(d, f) for f in others)]
    return {"stage": "IXSCAN", "keysExamined": len(keys), "docsExamined": len(fetched), "nReturned": n_returned}
''',
    tests=[
        [_TRIPS[:6], ["city", "km"], {"city": "oslo", "km": {"$gte": 10}}],
        [_TRIPS[:6], ["km"], {"city": "oslo"}],
        [_TRIPS, None, {"city": "lima"}],
        [_TRIPS, ["city"], {"city": "lima"}],
        [_TRIPS, ["city"], {"city": "lima", "driver": "d2"}],
        [_TRIPS, ["city", "driver"], {"city": "lima", "driver": "d2"}],
        [_TRIPS, ["km", "city"], {"city": "kyiv", "km": {"$gt": 10, "$lte": 25}}],
        [_TRIPS, ["city", "km"], {"city": "kyiv", "km": {"$gt": 10, "$lte": 25}}],
        [_TRIPS, ["km", "driver", "city"], {"km": 12, "city": "oslo"}],
        [_TRIPS, ["km", "driver", "city"], {"km": {"$lt": 13}, "driver": "d1", "city": "oslo"}],
        [_TRIPS, ["driver", "km"], {"km": 12}],
        [_TRIPS, ["city", "km"], {}],
        [_TRIPS, ["city"], {"city": "rome"}],
        [[], ["city"], {"city": "oslo"}],
        [_TRIPS, ["driver", "city", "km"], {"driver": "d3", "city": "kyiv", "km": {"$gte": 26}, "fare": {"$gt": 0}}],
    ],
    examples=2,
    wrong_solutions=[
        '''def explain(docs, index, query):
    ops = {"$gt": lambda a, b: a > b, "$gte": lambda a, b: a >= b, "$lt": lambda a, b: a < b, "$lte": lambda a, b: a <= b}
    def holds(doc, field):
        if field not in doc:
            return False
        c = query[field]
        if isinstance(c, dict):
            return all(ops[o](doc[field], x) for o, x in c.items())
        return doc[field] == c
    n = sum(1 for d in docs if all(holds(d, f) for f in query))
    used = [f for f in (index or []) if f in query]
    if not used:
        return {"stage": "COLLSCAN", "keysExamined": 0, "docsExamined": len(docs), "nReturned": n}
    keys = [d for d in docs if all(holds(d, f) for f in used)]
    return {"stage": "IXSCAN", "keysExamined": len(keys), "docsExamined": len(keys), "nReturned": n}
''',
        '''def explain(docs, index, query):
    ops = {"$gt": lambda a, b: a > b, "$gte": lambda a, b: a >= b, "$lt": lambda a, b: a < b, "$lte": lambda a, b: a <= b}
    def holds(doc, field):
        if field not in doc:
            return False
        c = query[field]
        if isinstance(c, dict):
            return all(ops[o](doc[field], x) for o, x in c.items())
        return doc[field] == c
    n = sum(1 for d in docs if all(holds(d, f) for f in query))
    prefix = []
    for f in index or []:
        if f not in query:
            break
        prefix.append(f)
    if not prefix:
        return {"stage": "COLLSCAN", "keysExamined": 0, "docsExamined": len(docs), "nReturned": n}
    keys = [d for d in docs if all(holds(d, f) for f in prefix)]
    return {"stage": "IXSCAN", "keysExamined": len(keys), "docsExamined": len(keys), "nReturned": n}
''',
    ],
    guide=dict(
        prereqs="Lesson *Reading explain output and covered queries*; the two previous index problems.",
        intuition="Explain output is a funnel: index keys walked → documents fetched → documents returned. A healthy "
                  "query keeps the three numbers close together. The index bounds can only be as tight as the "
                  "leading equality fields plus at most one range; anything after that is checked key by key, and "
                  "anything not in the index at all costs a document fetch.",
        hints=[
            "Write one predicate `holds(doc, field)` that understands both a literal and a bounds dict, and returns False for a missing field.",
            "Build the prefix with a loop that breaks in two places: the field is absent from the query, or it was a range.",
            "`docsExamined` filters the scanned keys by conditions on index fields outside the prefix; `nReturned` filters by everything.",
        ],
        brute_force="There is nothing cheaper than one pass per number here; the interesting part is modelling the plan, not speeding it up.",
        approach="""1. Compute `nReturned` with the full query.
2. Build the bounds prefix. Empty → `COLLSCAN` with `docsExamined = len(docs)`.
3. `keysExamined` = docs satisfying the prefix conditions.
4. `docsExamined` = those also satisfying conditions on the remaining index fields.

**Dry run** - index `[km, city]`, query `{city: kyiv, km: (10, 25]}`. `km` is a range → prefix `[km]`, stop.
Keys in `(10, 25]`: seven trips. `city` is an index field outside the prefix, so it is tested on the keys:
two are in kyiv → 2 documents fetched and 2 returned. With index `[city, km]` the prefix is both fields and only
2 keys are examined: the equality-first order wins.""",
        complexity="Time O(n · q) for n documents and q conditions; space O(n) for the intermediate lists.",
        pitfalls="- Using every index field found in the query as bounds, ignoring gaps and the one-range limit.\n"
                 "- Continuing the prefix after a range field.\n"
                 "- Reporting `docsExamined` equal to `nReturned`: conditions on non-indexed fields are only checked *after* the fetch.",
        follow_up="Add a `projection` argument and report `docsExamined = 0` for covered queries. Add a sort and report whether a blocking `SORT` stage is needed.",
    ),
),
dict(
    id="mongo-ttl-sweep",
    title="TTL Index Expiry Sweeps",
    difficulty="Easy",
    pattern="Index Behaviour",
    kind="function",
    entry="ttl_timeline",
    description=r"""
A TTL index makes documents disappear some time after a timestamp stored in them. Deletion is not instant:
a background task wakes up periodically (every 60 seconds by default) and removes whatever has expired.

`ttl_timeline(docs, field, expire_after, sweep_times)` simulates that task with explicit integer clocks.
Every document has a unique `_id`. `sweep_times` is an ascending list of times at which the task runs.
Return a list with one entry per sweep: the list of `_id`s deleted by that sweep, in collection order.

A document's **expiry time** is `t + expire_after` where `t` is taken from `doc[field]`:

- a number (int or float, **not** a bool) → `t` is that number;
- a list → `t` is the smallest number in it (ignore non-numbers; no numbers → never expires);
- missing, `None`, a string, a bool, anything else → the document never expires.

A sweep at time `now` deletes every still-present document with `expiry time <= now`.

**Example:** docs `[{"_id": "a", "seen": 100}, {"_id": "b", "seen": 160}, {"_id": "d"}]`, `field = "seen"`,
`expire_after = 60`, `sweep_times = [150, 210, 270]` → `[[], ["a"], ["b"]]`
""",
    starter='''def ttl_timeline(docs: List[dict], field: str, expire_after: int, sweep_times: List[int]) -> List[list]:
    pass
''',
    solution='''def ttl_timeline(docs, field, expire_after, sweep_times):
    def is_num(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool)

    def expiry(doc):
        v = doc.get(field)
        if isinstance(v, list):
            nums = [x for x in v if is_num(x)]
            v = min(nums) if nums else None
        return v + expire_after if is_num(v) else None

    alive = [(d["_id"], expiry(d)) for d in docs]
    out = []
    for now in sweep_times:
        gone = [i for i, e in alive if e is not None and e <= now]
        alive = [(i, e) for i, e in alive if e is None or e > now]
        out.append(gone)
    return out
''',
    tests=[
        [[{"_id": "a", "seen": 100}, {"_id": "b", "seen": 160}, {"_id": "d"}], "seen", 60, [150, 210, 270]],
        [_SESSIONS, "seen", 60, [159, 160, 220, 280, 500]],
        [_SESSIONS, "seen", 0, [0, 1, 100, 130, 1000]],
        [_SESSIONS, "seen", 3600, [100, 3700, 3819, 3820]],
        [_SESSIONS, "seen", 60, []],
        [_SESSIONS, "seen", 60, [10 ** 9]],
        [_SESSIONS, "other", 60, [10 ** 9]],
        [[], "seen", 60, [1, 2]],
        [[{"_id": 1, "expireAt": 500}, {"_id": 2, "expireAt": 499}, {"_id": 3, "expireAt": 501}], "expireAt", 0, [499, 500, 500, 501]],
        [[{"_id": 1, "ts": [9, 3, 7]}, {"_id": 2, "ts": [8]}, {"_id": 3, "ts": ["3", None]}, {"_id": 4, "ts": [False, 20]}], "ts", 10, [12, 13, 18, 30]],
        [[{"_id": i, "t": i * 10} for i in range(30)], "t", 25, [60, 120, 121, 400]],
        [[{"_id": 1, "t": -50}, {"_id": 2, "t": 0}, {"_id": 3, "t": 0.5}], "t", 10, [-40, 10, 10.5]],
    ],
    examples=1,
    wrong_solutions=[
        '''def ttl_timeline(docs, field, expire_after, sweep_times):
    out = []
    for now in sweep_times:
        out.append([d["_id"] for d in docs if isinstance(d.get(field), (int, float)) and d[field] + expire_after <= now])
    return out
''',
        '''def ttl_timeline(docs, field, expire_after, sweep_times):
    def is_num(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool)
    def expiry(doc):
        v = doc.get(field)
        if isinstance(v, list):
            nums = [x for x in v if is_num(x)]
            v = max(nums) if nums else None
        return v + expire_after if is_num(v) else None
    alive = [(d["_id"], expiry(d)) for d in docs]
    out = []
    for now in sweep_times:
        out.append([i for i, e in alive if e is not None and e < now])
        alive = [(i, e) for i, e in alive if e is None or e >= now]
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Unique, partial, sparse, TTL, text, geospatial and hashed indexes* (TTL section).",
        intuition="TTL is a scheduled `deleteMany({field: {$lte: now - expireAfter}})`. Documents therefore outlive "
                  "their nominal expiry by up to one sweep interval, and a document without a usable date "
                  "never qualifies. Precompute each document's expiry once, then each sweep is a filter over what is still alive.",
        hints=[
            "Compute `(id, expiry or None)` for every document before looping over the sweeps.",
            "Exclude booleans explicitly: `isinstance(True, int)` is true in Python.",
            "After each sweep, drop the deleted ids from the alive list so they are not reported twice.",
        ],
        brute_force="Re-scan the full original collection at every sweep and subtract everything already deleted: O(s · n) "
                    "with extra set bookkeeping. Keeping an `alive` list does the same work without the bookkeeping.",
        approach="""1. `expiry(doc)`: resolve the field, reduce a list to its smallest number, return `t + expire_after` or `None`.
2. `alive = [(id, expiry)]` in collection order.
3. For each `now`: `gone` = alive entries with `expiry <= now`; remove them; record `gone`.

**Dry run** - `seen` values a=100, b=160, d=missing; `expire_after = 60`; sweeps 150, 210, 270. Expiries: a=160,
b=220, d=None. Sweep 150: nothing (160 > 150). Sweep 210: a goes. Sweep 270: b goes. d stays forever.
Note that a expired at 160 but survived until the 210 sweep: TTL deletion is eventual, not exact.""",
        complexity="Time O(n + s · n) in the worst case (sorting the expiries would give O(n log n + s)), space O(n).",
        pitfalls="- Reporting the same document in two sweeps.\n"
                 "- Treating `True` or a numeric string as a timestamp.\n"
                 "- Using the largest array element: MongoDB uses the earliest date in an array.\n"
                 "- Using `<` instead of `<=` at the boundary.",
        follow_up="Model the *expire at a specific clock time* idiom: store `expireAt` and create the index with `expireAfterSeconds: 0`. "
                  "Then think about why a TTL index cannot be compound and why replica-set secondaries never run the sweep themselves.",
    ),
),
dict(
    id="mongo-unique-violations",
    title="Unique Index: Detect Duplicate-Key Errors",
    difficulty="Medium",
    pattern="Index Behaviour",
    kind="function",
    entry="insert_many",
    description=r"""
Simulate `insertMany` into a collection that has a (possibly compound) **unique index**.

`insert_many(existing, new_docs, fields, ordered, sparse)`:

- `existing`: documents already stored (they never violate the index among themselves);
- `new_docs`: documents to insert, in order;
- `fields`: the list of indexed field names;
- `ordered`: `True` → stop at the first error (later documents are not attempted); `False` → skip the
  failing document and carry on;
- `sparse`: whether the index is sparse.

**Index key.** A document's key is the tuple of its values for `fields`, where a **missing field counts as
`None`** - so two documents that both lack a uniquely indexed field collide. With `sparse = True`, a document
that has **none** of the indexed fields is not in the index at all: it can always be inserted and never
blocks anything. (A document with at least one of the fields is indexed as usual.)

A new document is rejected with a duplicate-key error when its key equals the key of an existing document or
of a new document inserted earlier in the same call. Rejected documents do not occupy their key.

Return `{"inserted": [...], "errors": [...]}`: positions (0-based indexes into `new_docs`) of the inserted
documents and of the documents that raised duplicate-key errors.

**Example:** existing `[{"email": "a@x.io"}]`, new `[{"email": "b@x.io"}, {"email": "a@x.io"}, {"email": "c@x.io"}]`,
fields `["email"]`, ordered → `{"inserted": [0], "errors": [1]}`; unordered → `{"inserted": [0, 2], "errors": [1]}`.
""",
    starter='''def insert_many(existing: List[dict], new_docs: List[dict], fields: List[str], ordered: bool, sparse: bool) -> dict:
    pass
''',
    solution='''def insert_many(existing, new_docs, fields, ordered, sparse):
    def key(doc):
        if sparse and not any(f in doc for f in fields):
            return None
        return tuple(doc.get(f) for f in fields)

    seen = set()
    for doc in existing:
        k = key(doc)
        if k is not None:
            seen.add(k)
    inserted, errors = [], []
    for i, doc in enumerate(new_docs):
        k = key(doc)
        if k is not None and k in seen:
            errors.append(i)
            if ordered:
                break
            continue
        if k is not None:
            seen.add(k)
        inserted.append(i)
    return {"inserted": inserted, "errors": errors}
''',
    tests=[
        [[{"email": "a@x.io"}], [{"email": "b@x.io"}, {"email": "a@x.io"}, {"email": "c@x.io"}], ["email"], True, False],
        [[{"email": "a@x.io"}], [{"email": "b@x.io"}, {"email": "a@x.io"}, {"email": "c@x.io"}], ["email"], False, False],
        [[], [{"n": "x"}, {"n": "y"}, {"n": "x"}, {"n": "x"}, {"n": "z"}], ["n"], False, False],
        [[], [{"n": "x"}, {"n": "y"}, {"n": "x"}, {"n": "x"}, {"n": "z"}], ["n"], True, False],
        [[], [{"a": 1}, {"b": 2}, {"c": 3}], ["nick"], False, False],
        [[], [{"a": 1}, {"b": 2}, {"c": 3}], ["nick"], False, True],
        [[{"nick": None}], [{"a": 1}, {"nick": None}, {"nick": "q"}], ["nick"], False, True],
        [[{"t": "acme", "sku": "p1"}], [{"t": "acme", "sku": "p2"}, {"t": "zeta", "sku": "p1"}, {"t": "acme", "sku": "p1"}, {"t": "acme"}, {"t": "acme"}], ["t", "sku"], False, False],
        [[{"t": "acme", "sku": "p1"}], [{"t": "acme"}, {"sku": "p1"}, {"x": 1}, {"x": 2}, {"t": "acme"}, {"sku": "p1"}], ["t", "sku"], False, True],
        [[{"t": "acme", "sku": "p1"}], [{"x": 1}, {"x": 2}, {"t": "acme", "sku": "p1"}, {"t": "new", "sku": "p1"}], ["t", "sku"], True, False],
        [[{"k": "dup"}], [{"k": "dup"}, {"k": "fresh"}, {"k": "dup"}, {"k": "fresh"}], ["k"], False, False],
        [[{"k": "a"}, {"k": "b"}], [], ["k"], True, False],
        [[], [{"k": str(i % 37)} for i in range(120)], ["k"], False, False],
    ],
    examples=2,
    wrong_solutions=[
        '''def insert_many(existing, new_docs, fields, ordered, sparse):
    seen = set()
    for d in existing:
        if all(f in d for f in fields):
            seen.add(tuple(d[f] for f in fields))
    inserted, errors = [], []
    for i, d in enumerate(new_docs):
        if all(f in d for f in fields):
            k = tuple(d[f] for f in fields)
            if k in seen:
                errors.append(i)
                if ordered:
                    break
                continue
            seen.add(k)
        inserted.append(i)
    return {"inserted": inserted, "errors": errors}
''',
        '''def insert_many(existing, new_docs, fields, ordered, sparse):
    def key(doc):
        if sparse and not any(f in doc for f in fields):
            return None
        return tuple(doc.get(f) for f in fields)
    seen = {key(d) for d in existing if key(d) is not None}
    inserted, errors = [], []
    for i, doc in enumerate(new_docs):
        k = key(doc)
        if k is not None and k in seen:
            errors.append(i)
            continue
        if k is not None:
            seen.add(k)
        inserted.append(i)
    return {"inserted": inserted, "errors": errors}
''',
    ],
    guide=dict(
        prereqs="Lessons *Inserting, deleting and write concern* (ordered vs unordered bulk writes) and *Unique, partial, sparse, TTL...* (unique and sparse sections).",
        intuition="A unique index is a set of keys. Inserting is `if key in set: error else: add`. The two subtleties "
                  "are what the key *is* when a field is absent (it is null, so absent values collide with each "
                  "other) and what happens after an error (ordered stops, unordered continues). A sparse index "
                  "leaves documents without the field out of the set entirely.",
        hints=[
            "Use `tuple(doc.get(f) for f in fields)` as the key so missing fields become `None`.",
            "Return `None` as the key for documents the sparse index would skip, and treat `None` as *not indexed*.",
            "Only add a key to the set when the document was actually inserted.",
        ],
        brute_force="Compare each new document against every stored document field by field: O(n · m). A set of tuple keys gives O(1) checks.",
        approach="""1. Seed `seen` with the keys of the existing documents.
2. For each new document compute its key. Indexed and already seen → record the error, and `break` if ordered.
3. Otherwise add the key (if indexed) and record the insert.

**Dry run** - existing `{"t": "acme", "sku": "p1"}`, fields `[t, sku]`, unordered, not sparse; new docs
`{t: acme, sku: p2}` → key `(acme, p2)` new → inserted; `{t: zeta, sku: p1}` → inserted; `{t: acme, sku: p1}` →
duplicate; `{t: acme}` → key `(acme, None)` new → inserted; `{t: acme}` again → duplicate of the previous one.
Result `inserted = [0, 1, 3]`, `errors = [2, 4]`.""",
        complexity="Time O(n + m) with hashing, space O(n + m) for the key set.",
        pitfalls="- Skipping documents that lack the field in a **non-sparse** index: they are indexed under null and collide.\n"
                 "- For a compound sparse index, skipping a document that has *some* of the fields.\n"
                 "- Ignoring `ordered`: with `ordered = True` nothing after the first failure is attempted.\n"
                 "- Reserving the key of a rejected document.",
        follow_up="A partial unique index (`partialFilterExpression: {email: {$exists: true}}`) is the modern replacement for sparse. "
                  "Extend the function to accept a predicate deciding which documents are indexed.",
    ),
),
]
