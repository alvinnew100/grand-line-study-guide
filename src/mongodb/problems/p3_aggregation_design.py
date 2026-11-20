"""Problems for the aggregation, application-design and getting-started modules."""

_SHOP = {
    "orders": [
        {"_id": 1, "customer": "c1", "status": "paid", "total": 40, "items": ["tea", "cup"]},
        {"_id": 2, "customer": "c2", "status": "paid", "total": 15, "items": ["tea"]},
        {"_id": 3, "customer": "c1", "status": "refunded", "total": 25, "items": []},
        {"_id": 4, "customer": "c3", "status": "paid", "total": 60, "items": ["pot", "tea", "tray"]},
        {"_id": 5, "customer": "c2", "status": "pending", "items": ["cup"]},
        {"_id": 6, "customer": "c9", "status": "paid", "total": 5},
        {"_id": 7, "status": "paid", "total": 11, "items": "sampler"},
    ],
    "customers": [
        {"_id": "c1", "name": "Wren", "tier": "gold"},
        {"_id": "c2", "name": "Idris", "tier": "basic"},
        {"_id": "c3", "name": "Luz", "tier": "gold"},
        {"_id": "c4", "name": "Tove"},
    ],
    "products": [
        {"_id": "p1", "sku": "tea", "price": 5},
        {"_id": "p2", "sku": "cup", "price": 10},
        {"_id": "p3", "sku": "pot", "price": 30},
        {"_id": "p4", "sku": "tea", "price": 6},
    ],
}

_FLATS = [
    {"_id": 1, "area": "north", "rent": 950, "rooms": 2, "pets": True},
    {"_id": 2, "area": "north", "rent": 1400, "rooms": 3, "pets": False},
    {"_id": 3, "area": "docks", "rent": 700, "rooms": 1, "pets": True},
    {"_id": 4, "area": "docks", "rent": 2100, "rooms": 4, "pets": True},
    {"_id": 5, "area": "old town", "rent": 1000, "rooms": 2, "pets": False},
    {"_id": 6, "area": "docks", "rent": 1999.5, "rooms": 3},
    {"_id": 7, "area": "north", "rooms": 1, "pets": True},
    {"_id": 8, "rent": "ask", "rooms": 2, "pets": False},
    {"_id": 9, "area": "old town", "rent": 3000, "rooms": 5, "pets": True},
]

_AUTHORS = [{"_id": "a1", "name": "Kiri"}, {"_id": "a2", "name": "Bram"}, {"_id": "a3", "name": "Sol"}]
_COMMENTS = [
    {"_id": 10, "author": "a1", "text": "first"},
    {"_id": 11, "author": "a2", "text": "nice"},
    {"_id": 12, "author": "a1", "text": "second", "likes": 3},
    {"_id": 13, "author": "a1", "text": "third"},
    {"_id": 14, "author": "zz", "text": "orphan"},
    {"_id": 15, "text": "no author"},
    {"_id": 16, "author": "a1", "text": "fourth"},
]

_READINGS = [
    {"sensor": "s2", "ts": 125, "value": 7.5},
    {"sensor": "s1", "ts": 61, "value": 20},
    {"sensor": "s1", "ts": 5, "value": 18},
    {"sensor": "s1", "ts": 59, "value": 22},
    {"sensor": "s2", "ts": 0, "value": 9},
    {"sensor": "s1", "ts": 60, "value": 19},
    {"sensor": "s1", "ts": 5, "value": 17},
    {"sensor": "s1", "ts": 185, "value": 30},
]

_USER_SCHEMA = {
    "bsonType": "object",
    "required": ["email", "age"],
    "properties": {
        "email": {"bsonType": "string", "minLength": 5},
        "age": {"bsonType": "int", "minimum": 13, "maximum": 120},
        "plan": {"enum": ["free", "pro", None]},
        "score": {"bsonType": ["double", "null"]},
        "tags": {"bsonType": "array", "items": {"bsonType": "string", "maxLength": 8}, "minItems": 1},
        "address": {"bsonType": "object", "required": ["city"], "additionalProperties": False,
                    "properties": {"city": {"bsonType": "string"}, "zip": {"bsonType": ["string", "int"]}}},
    },
}

PROBLEMS = [
dict(
    id="mongo-aggregate-pipeline",
    title="Aggregation Pipeline Runner",
    difficulty="Hard",
    pattern="Aggregation",
    kind="function",
    entry="aggregate",
    description=r"""
Build a small aggregation engine. `aggregate(collections, name, pipeline)` runs `pipeline` (a list of
single-key stage dicts) over `collections[name]` and returns the resulting list of documents.
`collections` maps collection names to lists of flat documents; the input must not be mutated. A field
reference is a string starting with `$`, e.g. `"$total"`.

| stage | behaviour |
|---|---|
| `{"$match": q}` | keep documents where every `field: cond` of `q` holds. `cond` is a literal (field present and equal) or a dict of `$gt`, `$gte`, `$lt`, `$lte`, `$in` (field present and satisfying it) or `$ne` (true when the field is missing or different). |
| `{"$project": spec}` | build a new document. `_id` is kept unless `"_id": 0`. Every other entry is `name: 1` (copy the field of that name) or `name: "$other"` (copy field `other` under the new name). Missing source fields are omitted. |
| `{"$group": {"_id": key, out: {acc: expr}, ...}}` | `key` is `None` (one group) or a field reference (a missing field groups under `None`). Emit one document per group, **in order of first appearance**, with `_id` and one field per accumulator. |
| `{"$sort": {field: 1 or -1, ...}}` | stable sort, earlier keys more significant. Missing / `None` sorts before every value when ascending. Present values are mutually comparable. |
| `{"$limit": n}` | keep the first `n` documents. |
| `{"$unwind": "$field"}` | a list becomes one output document per element (an empty list yields none); a missing or `None` field drops the document; any other value passes through unchanged. |
| `{"$lookup": {"from", "localField", "foreignField", "as"}}` | add an array field `as` holding every document of collection `from` whose `foreignField` equals the local value. If the local value is a list, a foreign document matches when its value equals **any** element. A missing field counts as `None` on both sides. An unknown `from` collection is empty. |

**Accumulators** take a field reference, or (for `$sum`) a number constant:

- `$sum`: sum of the numeric values (missing / non-numeric ignored); `{"$sum": 1}` counts documents;
- `$avg`: mean of the numeric values, `None` if there are none;
- `$min`, `$max`: smallest / largest numeric value, `None` if there are none;
- `$push`: list of the values in input order, skipping documents where the field is missing.

Booleans are not numeric.

**Example:** orders `[{"c": "x", "t": 5}, {"c": "y", "t": 1}, {"c": "x", "t": 2}]`, pipeline
`[{"$group": {"_id": "$c", "spent": {"$sum": "$t"}, "n": {"$sum": 1}}}]`
→ `[{"_id": "x", "spent": 7, "n": 2}, {"_id": "y", "spent": 1, "n": 1}]`
""",
    starter='''def aggregate(collections: dict, name: str, pipeline: List[dict]) -> List[dict]:
    pass
''',
    solution='''def aggregate(collections, name, pipeline):
    cmp = {"$gt": lambda a, b: a > b, "$gte": lambda a, b: a >= b,
           "$lt": lambda a, b: a < b, "$lte": lambda a, b: a <= b}

    def is_num(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool)

    def match(doc, q):
        for field, cond in q.items():
            present = field in doc
            if not isinstance(cond, dict):
                if not present or doc[field] != cond:
                    return False
                continue
            for op, x in cond.items():
                if op == "$ne":
                    if present and doc[field] == x:
                        return False
                elif op == "$in":
                    if not present or doc[field] not in x:
                        return False
                elif not present or not cmp[op](doc[field], x):
                    return False
        return True

    def group(docs, spec):
        ref = spec["_id"]
        groups, order = {}, []
        for d in docs:
            key = d.get(ref[1:]) if isinstance(ref, str) else None
            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append(d)
        out = []
        for key in order:
            row = {"_id": key}
            for field, acc in spec.items():
                if field == "_id":
                    continue
                (fn, expr), = acc.items()
                if isinstance(expr, str):
                    vals = [d[expr[1:]] for d in groups[key] if expr[1:] in d]
                else:
                    vals = [expr] * len(groups[key])
                if fn == "$push":
                    row[field] = vals
                    continue
                nums = [v for v in vals if is_num(v)]
                if fn == "$sum":
                    row[field] = sum(nums)
                elif fn == "$avg":
                    row[field] = sum(nums) / len(nums) if nums else None
                elif fn == "$min":
                    row[field] = min(nums) if nums else None
                elif fn == "$max":
                    row[field] = max(nums) if nums else None
            out.append(row)
        return out

    docs = [dict(d) for d in collections.get(name, [])]
    for stage in pipeline:
        (op, arg), = stage.items()
        if op == "$match":
            docs = [d for d in docs if match(d, arg)]
        elif op == "$project":
            out = []
            for d in docs:
                new = {}
                if arg.get("_id", 1) != 0 and "_id" in d:
                    new["_id"] = d["_id"]
                for k, v in arg.items():
                    if k == "_id":
                        continue
                    src = v[1:] if isinstance(v, str) else k
                    if src in d:
                        new[k] = d[src]
                out.append(new)
            docs = out
        elif op == "$group":
            docs = group(docs, arg)
        elif op == "$sort":
            for field, direction in reversed(list(arg.items())):
                docs.sort(key=lambda d: (d.get(field) is not None, 0 if d.get(field) is None else d[field]),
                          reverse=(direction == -1))
        elif op == "$limit":
            docs = docs[:arg]
        elif op == "$unwind":
            field = arg[1:]
            out = []
            for d in docs:
                v = d.get(field)
                if v is None:
                    continue
                if isinstance(v, list):
                    for item in v:
                        new = dict(d)
                        new[field] = item
                        out.append(new)
                else:
                    out.append(d)
            docs = out
        elif op == "$lookup":
            foreign = collections.get(arg["from"], [])
            out = []
            for d in docs:
                local = d.get(arg["localField"])
                wanted = local if isinstance(local, list) else [local]
                new = dict(d)
                new[arg["as"]] = [dict(f) for f in foreign if f.get(arg["foreignField"]) in wanted]
                out.append(new)
            docs = out
        else:
            raise ValueError("unsupported stage " + op)
    return docs
''',
    tests=[
        [{"orders": [{"c": "x", "t": 5}, {"c": "y", "t": 1}, {"c": "x", "t": 2}]}, "orders",
         [{"$group": {"_id": "$c", "spent": {"$sum": "$t"}, "n": {"$sum": 1}}}]],
        [_SHOP, "orders", []],
        [_SHOP, "orders", [{"$match": {"status": "paid", "total": {"$gte": 11, "$lt": 60}}}]],
        [_SHOP, "orders", [{"$match": {"total": {"$ne": 40}, "customer": {"$in": ["c1", "c2"]}}},
                           {"$project": {"_id": 0, "who": "$customer", "status": 1, "total": 1}}]],
        [_SHOP, "orders", [{"$group": {"_id": "$customer", "orders": {"$sum": 1}, "spent": {"$sum": "$total"},
                                       "avg": {"$avg": "$total"}, "ids": {"$push": "$_id"}}}]],
        [_SHOP, "orders", [{"$group": {"_id": None, "lo": {"$min": "$total"}, "hi": {"$max": "$total"},
                                       "mean": {"$avg": "$total"}, "twice": {"$sum": 2}}}]],
        [_SHOP, "orders", [{"$match": {"status": "pending"}},
                           {"$group": {"_id": "$status", "avg": {"$avg": "$total"}, "lo": {"$min": "$total"},
                                       "sum": {"$sum": "$total"}, "all": {"$push": "$total"}}}]],
        [_SHOP, "orders", [{"$unwind": "$items"}, {"$group": {"_id": "$items", "n": {"$sum": 1}}},
                           {"$sort": {"n": -1, "_id": 1}}, {"$limit": 3}]],
        [_SHOP, "orders", [{"$unwind": "$items"}, {"$project": {"items": 1}}]],
        [_SHOP, "orders", [{"$sort": {"customer": 1, "total": -1}}, {"$project": {"customer": 1, "total": 1}}]],
        [_SHOP, "orders", [{"$sort": {"total": -1}}, {"$limit": 2}, {"$project": {"_id": 1}}]],
        [_SHOP, "orders", [{"$lookup": {"from": "customers", "localField": "customer", "foreignField": "_id", "as": "buyer"}},
                           {"$project": {"buyer": 1}}]],
        [_SHOP, "orders", [{"$match": {"_id": {"$in": [1, 4, 7]}}},
                           {"$lookup": {"from": "products", "localField": "items", "foreignField": "sku", "as": "lines"}},
                           {"$project": {"_id": 1, "lines": 1}}]],
        [_SHOP, "customers", [{"$lookup": {"from": "orders", "localField": "_id", "foreignField": "customer", "as": "orders"}},
                              {"$unwind": "$orders"}, {"$group": {"_id": "$tier", "names": {"$push": "$name"}}}]],
        [_SHOP, "customers", [{"$lookup": {"from": "nowhere", "localField": "tier", "foreignField": "tier", "as": "x"}},
                              {"$limit": 0}]],
        [_SHOP, "missing", [{"$group": {"_id": None, "n": {"$sum": 1}}}]],
        [_SHOP, "customers", [{"$lookup": {"from": "orders", "localField": "tier", "foreignField": "tier", "as": "same"}},
                              {"$match": {"_id": "c4"}}, {"$unwind": "$same"}, {"$group": {"_id": None, "n": {"$sum": 1}}}]],
    ],
    examples=1,
    wrong_solutions=[
        # $unwind keeps documents with missing fields and mishandles empty arrays; $avg divides by group size
        '''def aggregate(collections, name, pipeline):
    cmp = {"$gt": lambda a, b: a > b, "$gte": lambda a, b: a >= b, "$lt": lambda a, b: a < b, "$lte": lambda a, b: a <= b}
    def match(doc, q):
        for f, c in q.items():
            present = f in doc
            if not isinstance(c, dict):
                if not present or doc[f] != c:
                    return False
                continue
            for op, x in c.items():
                if op == "$ne":
                    if present and doc[f] == x:
                        return False
                elif op == "$in":
                    if not present or doc[f] not in x:
                        return False
                elif not present or not cmp[op](doc[f], x):
                    return False
        return True
    docs = [dict(d) for d in collections.get(name, [])]
    for stage in pipeline:
        (op, arg), = stage.items()
        if op == "$match":
            docs = [d for d in docs if match(d, arg)]
        elif op == "$project":
            out = []
            for d in docs:
                new = {}
                if arg.get("_id", 1) != 0 and "_id" in d:
                    new["_id"] = d["_id"]
                for k, v in arg.items():
                    if k != "_id":
                        src = v[1:] if isinstance(v, str) else k
                        if src in d:
                            new[k] = d[src]
                out.append(new)
            docs = out
        elif op == "$group":
            groups, order = {}, []
            for d in docs:
                key = d.get(arg["_id"][1:]) if isinstance(arg["_id"], str) else None
                if key not in groups:
                    groups[key] = []
                    order.append(key)
                groups[key].append(d)
            out = []
            for key in order:
                row = {"_id": key}
                for field, acc in arg.items():
                    if field == "_id":
                        continue
                    (fn, expr), = acc.items()
                    vals = [d.get(expr[1:], 0) for d in groups[key]] if isinstance(expr, str) else [expr] * len(groups[key])
                    if fn == "$push":
                        row[field] = vals
                    elif fn == "$sum":
                        row[field] = sum(vals)
                    elif fn == "$avg":
                        row[field] = sum(vals) / len(vals)
                    elif fn == "$min":
                        row[field] = min(vals)
                    else:
                        row[field] = max(vals)
                out.append(row)
            docs = out
        elif op == "$sort":
            for field, direction in reversed(list(arg.items())):
                docs.sort(key=lambda d: (d.get(field) is not None, 0 if d.get(field) is None else d[field]), reverse=(direction == -1))
        elif op == "$limit":
            docs = docs[:arg]
        elif op == "$unwind":
            out = []
            for d in docs:
                v = d.get(arg[1:])
                if isinstance(v, list):
                    for item in v:
                        new = dict(d)
                        new[arg[1:]] = item
                        out.append(new)
                else:
                    out.append(d)
            docs = out
        elif op == "$lookup":
            foreign = collections.get(arg["from"], [])
            out = []
            for d in docs:
                local = d.get(arg["localField"])
                wanted = local if isinstance(local, list) else [local]
                new = dict(d)
                new[arg["as"]] = [dict(f) for f in foreign if f.get(arg["foreignField"]) in wanted]
                out.append(new)
            docs = out
    return docs
''',
        # groups emitted in sorted order and $lookup does not expand local arrays
        '''def aggregate(collections, name, pipeline):
    cmp = {"$gt": lambda a, b: a > b, "$gte": lambda a, b: a >= b, "$lt": lambda a, b: a < b, "$lte": lambda a, b: a <= b}
    def num(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool)
    def match(doc, q):
        for f, c in q.items():
            present = f in doc
            if not isinstance(c, dict):
                if not present or doc[f] != c:
                    return False
                continue
            for op, x in c.items():
                if op == "$ne":
                    if present and doc[f] == x:
                        return False
                elif op == "$in":
                    if not present or doc[f] not in x:
                        return False
                elif not present or not cmp[op](doc[f], x):
                    return False
        return True
    docs = [dict(d) for d in collections.get(name, [])]
    for stage in pipeline:
        (op, arg), = stage.items()
        if op == "$match":
            docs = [d for d in docs if match(d, arg)]
        elif op == "$project":
            out = []
            for d in docs:
                new = {}
                if arg.get("_id", 1) != 0 and "_id" in d:
                    new["_id"] = d["_id"]
                for k, v in arg.items():
                    if k != "_id":
                        src = v[1:] if isinstance(v, str) else k
                        if src in d:
                            new[k] = d[src]
                out.append(new)
            docs = out
        elif op == "$group":
            groups = {}
            for d in docs:
                key = d.get(arg["_id"][1:]) if isinstance(arg["_id"], str) else None
                groups.setdefault(key, []).append(d)
            out = []
            for key in sorted(groups, key=lambda k: (k is not None, str(k))):
                row = {"_id": key}
                for field, acc in arg.items():
                    if field == "_id":
                        continue
                    (fn, expr), = acc.items()
                    vals = [d[expr[1:]] for d in groups[key] if expr[1:] in d] if isinstance(expr, str) else [expr] * len(groups[key])
                    nums = [v for v in vals if num(v)]
                    if fn == "$push":
                        row[field] = vals
                    elif fn == "$sum":
                        row[field] = sum(nums)
                    elif fn == "$avg":
                        row[field] = sum(nums) / len(nums) if nums else None
                    elif fn == "$min":
                        row[field] = min(nums) if nums else None
                    else:
                        row[field] = max(nums) if nums else None
                out.append(row)
            docs = out
        elif op == "$sort":
            for field, direction in reversed(list(arg.items())):
                docs.sort(key=lambda d: (d.get(field) is not None, 0 if d.get(field) is None else d[field]), reverse=(direction == -1))
        elif op == "$limit":
            docs = docs[:arg]
        elif op == "$unwind":
            out = []
            for d in docs:
                v = d.get(arg[1:])
                if v is None:
                    continue
                if isinstance(v, list):
                    for item in v:
                        new = dict(d)
                        new[arg[1:]] = item
                        out.append(new)
                else:
                    out.append(d)
            docs = out
        elif op == "$lookup":
            foreign = collections.get(arg["from"], [])
            out = []
            for d in docs:
                new = dict(d)
                new[arg["as"]] = [dict(f) for f in foreign if f.get(arg["foreignField"]) == d.get(arg["localField"])]
                out.append(new)
            docs = out
    return docs
''',
    ],
    guide=dict(
        prereqs="Both aggregation lessons. Dict-of-lists grouping; stable sorting.",
        intuition="A pipeline is function composition over a list: each stage takes the list produced by the previous "
                  "one and returns a new list. Write each stage as a small list-to-list transformation and the "
                  "runner is a `for` loop. The care goes into the edge rules - what a missing field means to "
                  "`$match`, `$group`, `$unwind` and `$lookup` - because each stage answers that differently.",
        hints=[
            "Unpack a stage with `(op, arg), = stage.items()` and dispatch on `op`.",
            "For `$group`, keep a dict of lists plus a separate list recording the order in which keys first appear; compute accumulators afterwards from each group's documents.",
            "For `$lookup`, normalise the local value to a list of wanted values (`local if isinstance(local, list) else [local]`) and test membership.",
        ],
        brute_force="Computing each accumulator with a fresh pass over all documents per group is O(groups × documents). "
                    "Bucketing documents by key first makes it one pass. A nested-loop `$lookup` is O(local × foreign); "
                    "building a dict from foreign value to documents brings that to O(local + foreign), which is what an index on `foreignField` does for the real server.",
        approach="""1. Copy the input documents (`dict(d)`) so stages can build new dicts freely.
2. `$match`: one predicate; `$ne` is the only operator that is true for a missing field.
3. `$project`: start from `_id` (unless excluded) and copy each requested or renamed field that exists.
4. `$group`: bucket by key, then fold each bucket with the requested accumulators.
5. `$sort`: stable sorts from the last key to the first, with `(is present, value)` as the key.
6. `$unwind`, `$lookup`, `$limit`: direct list rebuilds.

**Dry run** - orders with `items` `["tea", "cup"]`, `["tea"]`, `[]`, `["pot", "tea", "tray"]`, `["cup"]`, missing,
`"sampler"` through `$unwind` → 2 + 1 + 0 + 3 + 1 + 0 + 1 = 8 documents. `$group` by `$items` with `{"$sum": 1}`
→ tea 3, cup 2, pot 1, tray 1, sampler 1 (first-appearance order). `$sort {n: -1, _id: 1}` then `$limit 3`
→ tea, cup, pot.""",
        complexity="Each stage is O(n) except `$sort` (O(n log n)) and the nested-loop `$lookup` (O(n · m)). Space O(n) per stage.",
        pitfalls="- Dividing `$avg` by the group size instead of by the number of numeric values.\n"
                 "- Letting `$unwind` keep documents whose array is empty or missing (that is the `preserveNullAndEmptyArrays` option, off by default).\n"
                 "- Emitting groups in sorted order: `$group` promises no order, and the tests fix first appearance.\n"
                 "- Capturing the loop variable `field` in a lambda that is used after the loop moves on (here it is used immediately, which is safe).",
        follow_up="Add `$skip`, `$count`, `$addFields`, `$sortByCount`, and expression operators such as `$multiply` inside `$project`. "
                  "Then reorder a `$match` in front of a `$lookup` automatically when it only touches local fields, as the real optimiser does.",
    ),
),
dict(
    id="mongo-facet",
    title="$facet: Several Aggregations in One Pass",
    difficulty="Medium",
    pattern="Aggregation",
    kind="function",
    entry="facet",
    description=r"""
A search page needs a category sidebar, a price histogram and summary statistics for the same result set.
`$facet` computes them together. Implement `facet(docs, facets)`, returning a dict with one entry per facet
name. Each facet spec is a dict that may contain `"match"` (a flat `field: value` equality filter applied
first; a missing field never matches) and exactly one of the following:

**`"sortByCount": field`** - count documents per value of `field` (missing counts as `None`). Result: a list of
`{"_id": value, "count": n}` sorted by count descending; ties stay in order of first appearance.

**`"bucket": field, "boundaries": [b0, b1, ..., bk]`** (ascending numbers) - a document whose numeric value `v`
satisfies `b[i] <= v < b[i+1]` falls in bucket `b[i]`. Missing, non-numeric (booleans are not numbers) or
out-of-range values fall in the bucket `"other"`. Result: a list of `{"_id": b[i], "count": n}` for the
**non-empty** buckets in boundary order, followed by `{"_id": "other", "count": n}` if it is non-empty.

**`"stats": field`** - over the numeric values of `field`: `{"count": n, "min": .., "max": .., "avg": ..}`
with `None` for min, max and avg when `n == 0`.

**Example:** docs with rents `[950, 1400, 700]` in areas `["north", "north", "docks"]`,
`facets = {"areas": {"sortByCount": "area"}, "rent": {"stats": "rent"}}`
→ `{"areas": [{"_id": "north", "count": 2}, {"_id": "docks", "count": 1}], "rent": {"count": 3, "min": 700, "max": 1400, "avg": 1016.6666666666666}}`
""",
    starter='''def facet(docs: List[dict], facets: dict) -> dict:
    pass
''',
    compare="float",
    solution='''def facet(docs, facets):
    def is_num(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool)

    result = {}
    for name, spec in facets.items():
        cond = spec.get("match", {})
        rows = [d for d in docs if all(k in d and d[k] == v for k, v in cond.items())]
        if "sortByCount" in spec:
            field = spec["sortByCount"]
            counts = {}
            for d in rows:
                key = d.get(field)
                counts[key] = counts.get(key, 0) + 1
            out = [{"_id": k, "count": c} for k, c in counts.items()]
            out.sort(key=lambda r: -r["count"])
            result[name] = out
        elif "bucket" in spec:
            field, bounds = spec["bucket"], spec["boundaries"]
            counts = {}
            for d in rows:
                v = d.get(field)
                key = "other"
                if is_num(v):
                    for lo, hi in zip(bounds, bounds[1:]):
                        if lo <= v < hi:
                            key = lo
                            break
                counts[key] = counts.get(key, 0) + 1
            out = [{"_id": lo, "count": counts[lo]} for lo in bounds[:-1] if lo in counts]
            if "other" in counts:
                out.append({"_id": "other", "count": counts["other"]})
            result[name] = out
        else:
            nums = [d[spec["stats"]] for d in rows if is_num(d.get(spec["stats"]))]
            if nums:
                result[name] = {"count": len(nums), "min": min(nums), "max": max(nums), "avg": sum(nums) / len(nums)}
            else:
                result[name] = {"count": 0, "min": None, "max": None, "avg": None}
    return result
''',
    tests=[
        [[{"area": "north", "rent": 950}, {"area": "north", "rent": 1400}, {"area": "docks", "rent": 700}],
         {"areas": {"sortByCount": "area"}, "rent": {"stats": "rent"}}],
        [_FLATS, {"areas": {"sortByCount": "area"}}],
        [_FLATS, {"pets": {"sortByCount": "pets"}, "rooms": {"sortByCount": "rooms"}}],
        [_FLATS, {"bands": {"bucket": "rent", "boundaries": [0, 1000, 2000, 3000]}}],
        [_FLATS, {"bands": {"bucket": "rent", "boundaries": [500, 800]}}],
        [_FLATS, {"bands": {"bucket": "rooms", "boundaries": [1, 2, 3, 6]}, "rent": {"stats": "rent"}}],
        [_FLATS, {"rent": {"stats": "rent"}, "rooms": {"stats": "rooms"}, "none": {"stats": "area"}}],
        [_FLATS, {"dock_rent": {"match": {"area": "docks"}, "stats": "rent"},
                  "dock_bands": {"match": {"area": "docks"}, "bucket": "rent", "boundaries": [0, 1000, 2000, 2100]},
                  "pet_areas": {"match": {"pets": True}, "sortByCount": "area"}}],
        [_FLATS, {"x": {"match": {"area": "moon"}, "sortByCount": "rooms"}, "y": {"match": {"area": "moon"}, "stats": "rent"},
                  "z": {"match": {"area": "moon"}, "bucket": "rent", "boundaries": [0, 10]}}],
        [_FLATS, {}],
        [[], {"a": {"sortByCount": "k"}, "b": {"stats": "k"}, "c": {"bucket": "k", "boundaries": [0, 1]}}],
        [[{"v": True}, {"v": 1}, {"v": 1.0}, {"v": "1"}, {"v": 0.999}, {}], {"b": {"bucket": "v", "boundaries": [1, 2]}, "s": {"stats": "v"}}],
        [[{"k": i % 7, "w": i} for i in range(200)], {"k": {"sortByCount": "k"}, "w": {"bucket": "w", "boundaries": [0, 50, 150, 199]},
                                                       "s": {"match": {"k": 3}, "stats": "w"}}],
    ],
    examples=1,
    wrong_solutions=[
        '''def facet(docs, facets):
    result = {}
    for name, spec in facets.items():
        cond = spec.get("match", {})
        rows = [d for d in docs if all(d.get(k) == v for k, v in cond.items())]
        if "sortByCount" in spec:
            counts = {}
            for d in rows:
                counts[d.get(spec["sortByCount"])] = counts.get(d.get(spec["sortByCount"]), 0) + 1
            result[name] = sorted(({"_id": k, "count": c} for k, c in counts.items()), key=lambda r: -r["count"])
        elif "bucket" in spec:
            bounds = spec["boundaries"]
            counts = {}
            for d in rows:
                v = d.get(spec["bucket"])
                key = "other"
                if isinstance(v, (int, float)):
                    for lo, hi in zip(bounds, bounds[1:]):
                        if lo <= v <= hi:
                            key = lo
                            break
                counts[key] = counts.get(key, 0) + 1
            out = [{"_id": lo, "count": counts.get(lo, 0)} for lo in bounds[:-1]]
            if "other" in counts:
                out.append({"_id": "other", "count": counts["other"]})
            result[name] = out
        else:
            nums = [d[spec["stats"]] for d in rows if isinstance(d.get(spec["stats"]), (int, float))]
            result[name] = {"count": len(nums), "min": min(nums) if nums else None, "max": max(nums) if nums else None,
                            "avg": sum(nums) / len(nums) if nums else None}
    return result
''',
        '''def facet(docs, facets):
    def is_num(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool)
    result = {}
    rows = docs
    for name, spec in facets.items():
        cond = spec.get("match", {})
        rows = [d for d in rows if all(k in d and d[k] == v for k, v in cond.items())]
        if "sortByCount" in spec:
            counts = {}
            for d in rows:
                counts[d.get(spec["sortByCount"])] = counts.get(d.get(spec["sortByCount"]), 0) + 1
            result[name] = sorted(({"_id": k, "count": c} for k, c in counts.items()), key=lambda r: -r["count"])
        elif "bucket" in spec:
            bounds = spec["boundaries"]
            counts = {}
            for d in rows:
                v = d.get(spec["bucket"])
                key = "other"
                if is_num(v):
                    for lo, hi in zip(bounds, bounds[1:]):
                        if lo <= v < hi:
                            key = lo
                            break
                counts[key] = counts.get(key, 0) + 1
            out = [{"_id": lo, "count": counts[lo]} for lo in bounds[:-1] if lo in counts]
            if "other" in counts:
                out.append({"_id": "other", "count": counts["other"]})
            result[name] = out
        else:
            nums = [d[spec["stats"]] for d in rows if is_num(d.get(spec["stats"]))]
            result[name] = {"count": len(nums), "min": min(nums) if nums else None, "max": max(nums) if nums else None,
                            "avg": sum(nums) / len(nums) if nums else None}
    return result
''',
    ],
    guide=dict(
        prereqs="Lesson *$lookup, $facet and pipeline performance*; the pipeline-runner problem.",
        intuition="`$facet` fans one input out to several independent sub-pipelines and gathers their answers into a "
                  "single document. *Independent* is the key word: every facet starts again from the same input, so "
                  "a filter inside one facet must not leak into the next. Each of the three facet kinds is a "
                  "dictionary-counting exercise with a specific output shape.",
        hints=[
            "Compute `rows` freshly from `docs` for every facet.",
            "For `sortByCount`, a plain dict preserves first-appearance order and `list.sort` is stable, so sorting by `-count` alone gives the required tie order.",
            "For `bucket`, pair each boundary with its successor using `zip(bounds, bounds[1:])`; the interval is closed on the left and open on the right.",
        ],
        brute_force="Run each facet as a separate query. That is what applications do without `$facet`; it costs one "
                    "round trip and one scan per facet and, on a live collection, the facets can disagree with each "
                    "other because the data changed between queries.",
        approach="""1. Loop over facets; apply the optional `match` to the original documents.
2. `sortByCount`: count with a dict, emit rows, stable-sort by count descending.
3. `bucket`: find the half-open interval for each numeric value, count, emit non-empty buckets in boundary order, then `other`.
4. `stats`: collect numeric values and reduce.

**Dry run** - rents `950, 1400, 700, 2100, 1000, 1999.5, missing, "ask", 3000` with boundaries `[0, 1000, 2000, 3000]`:
bucket 0 gets 950 and 700; bucket 1000 gets 1400, 1000 and 1999.5; bucket 2000 gets 2100; 3000 equals the last
boundary, which is exclusive, so it joins the missing and string values in `other` (3).""",
        complexity="Time O(f · n · b) for f facets, n documents and b boundaries (binary search would make the bucket lookup O(log b)); space O(distinct values).",
        pitfalls="- Carrying one facet's filtered rows into the next facet.\n"
                 "- Treating the last boundary as inclusive.\n"
                 "- Emitting empty buckets with a zero count: `$bucket` only outputs buckets that received documents.\n"
                 "- Counting `True` as the number 1.",
        follow_up="In MongoDB the whole `$facet` output is one document and so must fit in 16 MB, and sub-pipelines cannot use indexes because their input is the stream from the previous stage. Put the selective `$match` *before* `$facet`.",
    ),
),
dict(
    id="mongo-embed-reference",
    title="From References to Embedded Documents",
    difficulty="Medium",
    pattern="Schema Design",
    kind="function",
    entry="embed_children",
    description=r"""
Convert a normalised, two-collection model into an embedded one - with a cap, because unbounded arrays are
an anti-pattern.

`embed_children(parents, children, fk, as_field, limit)`:

- every parent has a unique `_id`; every child has a unique, sortable `_id` and (usually) a field `fk` holding
  its parent's `_id`;
- return a new list with one document per parent, in the original order, equal to the parent plus two fields:
  - `as_field`: that parent's children **most recent first** (descending child `_id`), each **without** its `fk`
    field, truncated to the first `limit` entries when `limit` is not `None`;
  - `as_field + "_count"`: the total number of children of that parent, before truncation.
- children whose `fk` is missing or matches no parent are ignored. Inputs must not be mutated.

This is the *subset pattern* (keep the newest few inline, the rest in their own collection) combined with the
*computed pattern* (store the count instead of recounting).

**Example:** parents `[{"_id": "a1", "name": "Kiri"}]`, children
`[{"_id": 10, "author": "a1", "text": "first"}, {"_id": 12, "author": "a1", "text": "second"}]`, `fk = "author"`,
`as_field = "recent"`, `limit = 1`
→ `[{"_id": "a1", "name": "Kiri", "recent": [{"_id": 12, "text": "second"}], "recent_count": 2}]`
""",
    starter='''def embed_children(parents: List[dict], children: List[dict], fk: str, as_field: str, limit: Optional[int]) -> List[dict]:
    pass
''',
    solution='''def embed_children(parents, children, fk, as_field, limit):
    by_parent = {}
    for child in children:
        if fk in child:
            by_parent.setdefault(child[fk], []).append(child)
    out = []
    for parent in parents:
        kids = sorted(by_parent.get(parent["_id"], []), key=lambda c: c["_id"], reverse=True)
        total = len(kids)
        if limit is not None:
            kids = kids[:limit]
        new = dict(parent)
        new[as_field] = [{k: v for k, v in c.items() if k != fk} for c in kids]
        new[as_field + "_count"] = total
        out.append(new)
    return out
''',
    tests=[
        [[{"_id": "a1", "name": "Kiri"}], [{"_id": 10, "author": "a1", "text": "first"}, {"_id": 12, "author": "a1", "text": "second"}], "author", "recent", 1],
        [_AUTHORS, _COMMENTS, "author", "comments", None],
        [_AUTHORS, _COMMENTS, "author", "recent", 2],
        [_AUTHORS, _COMMENTS, "author", "recent", 0],
        [_AUTHORS, _COMMENTS, "author", "recent", 50],
        [_AUTHORS[::-1], _COMMENTS[::-1], "author", "c", 3],
        [_AUTHORS, [], "author", "comments", None],
        [[], _COMMENTS, "author", "comments", 2],
        [_AUTHORS, _COMMENTS, "writer", "comments", None],
        [[{"_id": 1, "title": "t"}, {"_id": 2, "title": "u"}], [{"_id": "b", "post": 1}, {"_id": "a", "post": 1}, {"_id": "c", "post": 2, "post_title": "u"}], "post", "replies", 1],
        [[{"_id": 7, "tags": ["x"]}], [{"_id": i, "p": 7, "n": i * i} for i in range(40)], "p", "last", 5],
        [[{"_id": None, "name": "root"}], [{"_id": 1, "parent": None}, {"_id": 2}], "parent", "kids", None],
    ],
    examples=1,
    wrong_solutions=[
        '''def embed_children(parents, children, fk, as_field, limit):
    out = []
    for p in parents:
        kids = [c for c in children if c.get(fk) == p["_id"]]
        kids = kids[:limit] if limit is not None else kids
        new = dict(p)
        new[as_field] = [{k: v for k, v in c.items() if k != fk} for c in kids]
        new[as_field + "_count"] = len(kids)
        out.append(new)
    return out
''',
        '''def embed_children(parents, children, fk, as_field, limit):
    out = []
    for p in parents:
        kids = sorted([c for c in children if fk in c and c[fk] == p["_id"]], key=lambda c: c["_id"], reverse=True)
        new = dict(p)
        new[as_field] = kids[:limit] if limit else kids
        new[as_field + "_count"] = len(kids)
        out.append(new)
    return out
''',
    ],
    guide=dict(
        prereqs="Lessons *Embedding vs referencing* and *Schema design patterns and anti-patterns* (subset and computed patterns).",
        intuition="Embedding is a join performed once, at write time, so that reads need no join at all. The transformation "
                  "is a group-by on the foreign key followed by attaching each group to its parent. The cap and the "
                  "stored count are what keep the embedded array bounded while still letting the UI say *showing 3 of 1,204 comments*.",
        hints=[
            "Group the children by `child[fk]` in a dict of lists with one pass.",
            "Record the count before slicing.",
            "`limit = 0` is a real cap (an empty array), so test `limit is not None`, not truthiness.",
        ],
        brute_force="For each parent, scan all children: O(P · C). Grouping first is O(P + C log C).",
        approach="""1. `by_parent[fk value] → [children]`, skipping children without the key.
2. For each parent: sort its children by `_id` descending, remember the total, slice to `limit`.
3. Strip `fk` from each embedded child and attach the list and the count to a copy of the parent.

**Dry run** - author `a1` has comments 10, 12, 13, 16; `limit = 2`. Sorted descending: 16, 13, 12, 10; total 4;
keep 16 and 13 without their `author` field. Author `a3` has none → `[]` and count 0. Comment 14 (unknown
author) and 15 (no author) are ignored.""",
        complexity="Time O(P + C log C), space O(P + C).",
        pitfalls="- Using `c.get(fk) == parent_id`, which wrongly attaches children with no `fk` to a parent whose `_id` is `None`.\n"
                 "- Counting after truncation.\n"
                 "- Leaving the redundant foreign key inside each embedded child.\n"
                 "- `if limit:` treating 0 as *no limit*.",
        follow_up="Write the inverse: split embedded arrays back into a child collection with a foreign key. Then describe "
                  "the write path that keeps the subset fresh: `$push` with `$each`, `$sort` and `$slice`, plus `$inc` on the counter.",
    ),
),
dict(
    id="mongo-bucket-pattern",
    title="Bucket Pattern for Time-Series Readings",
    difficulty="Medium",
    pattern="Schema Design",
    kind="function",
    entry="bucket_readings",
    description=r"""
One document per sensor reading means billions of tiny documents and index entries. The **bucket pattern**
stores one document per sensor per time window, with the readings inside and summary values precomputed.

`bucket_readings(readings, bucket_seconds)`: each reading is `{"sensor": str, "ts": int >= 0, "value": number}`.
Group readings by sensor and by window, where a reading belongs to the window starting at
`ts - ts % bucket_seconds`. Return the bucket documents sorted by `sensor`, then by `bucket_start`:

```
{"sensor": "s1", "bucket_start": 0, "count": 3, "sum": 57, "min": 17, "max": 22,
 "readings": [{"ts": 5, "value": 18}, {"ts": 5, "value": 17}, {"ts": 59, "value": 22}]}
```

Inside a bucket, `readings` are ordered by `ts` ascending, ties keeping their input order. Only buckets that
contain at least one reading are produced.

**Example:** readings for `s1` at ts `5, 59, 60` with values `18, 22, 19` and `bucket_seconds = 60` → two
buckets: start 0 (count 2, sum 40, min 18, max 22) and start 60 (count 1, sum 19, min 19, max 19).
""",
    starter='''def bucket_readings(readings: List[dict], bucket_seconds: int) -> List[dict]:
    pass
''',
    compare="float",
    solution='''def bucket_readings(readings, bucket_seconds):
    buckets = {}
    for r in readings:
        start = r["ts"] - r["ts"] % bucket_seconds
        buckets.setdefault((r["sensor"], start), []).append(r)
    out = []
    for (sensor, start) in sorted(buckets):
        rows = sorted(buckets[(sensor, start)], key=lambda r: r["ts"])
        values = [r["value"] for r in rows]
        out.append({
            "sensor": sensor,
            "bucket_start": start,
            "count": len(rows),
            "sum": sum(values),
            "min": min(values),
            "max": max(values),
            "readings": [{"ts": r["ts"], "value": r["value"]} for r in rows],
        })
    return out
''',
    tests=[
        [[{"sensor": "s1", "ts": 5, "value": 18}, {"sensor": "s1", "ts": 59, "value": 22}, {"sensor": "s1", "ts": 60, "value": 19}], 60],
        [_READINGS, 60],
        [_READINGS, 1],
        [_READINGS, 3600],
        [_READINGS, 7],
        [_READINGS[::-1], 60],
        [[], 60],
        [[{"sensor": "x", "ts": 0, "value": -4}], 10],
        [[{"sensor": "b", "ts": 119, "value": 1}, {"sensor": "a", "ts": 120, "value": 2}, {"sensor": "b", "ts": 120, "value": 3}, {"sensor": "a", "ts": 0, "value": 4}], 120],
        [[{"sensor": "s10", "ts": 3, "value": 1}, {"sensor": "s9", "ts": 3, "value": 2}, {"sensor": "s10", "ts": 2, "value": 5}], 5],
        [[{"sensor": "t" + str(i % 3), "ts": (i * 37) % 600, "value": (i * 13) % 50} for i in range(150)], 100],
        [[{"sensor": "z", "ts": t, "value": v} for t, v in [(30, 1), (30, 2), (30, 3), (29, 4), (31, 0)]], 30],
    ],
    examples=1,
    wrong_solutions=[
        '''def bucket_readings(readings, bucket_seconds):
    buckets = {}
    for r in readings:
        start = r["ts"] // bucket_seconds
        buckets.setdefault((r["sensor"], start), []).append(r)
    out = []
    for (sensor, start) in sorted(buckets):
        rows = sorted(buckets[(sensor, start)], key=lambda r: r["ts"])
        vals = [r["value"] for r in rows]
        out.append({"sensor": sensor, "bucket_start": start, "count": len(rows), "sum": sum(vals), "min": min(vals),
                    "max": max(vals), "readings": [{"ts": r["ts"], "value": r["value"]} for r in rows]})
    return out
''',
        '''def bucket_readings(readings, bucket_seconds):
    buckets = {}
    for r in readings:
        start = r["ts"] - r["ts"] % bucket_seconds
        buckets.setdefault((r["sensor"], start), []).append(r)
    out = []
    for (sensor, start) in sorted(buckets):
        rows = sorted(buckets[(sensor, start)], key=lambda r: (r["ts"], r["value"]))
        vals = [r["value"] for r in rows]
        out.append({"sensor": sensor, "bucket_start": start, "count": len(rows), "sum": sum(vals), "min": min(vals),
                    "max": max(vals), "readings": [{"ts": r["ts"], "value": r["value"]} for r in rows]})
    return out
''',
        '''def bucket_readings(readings, bucket_seconds):
    buckets = {}
    for r in readings:
        start = r["ts"] - r["ts"] % bucket_seconds
        buckets.setdefault(start, []).append(r)
    out = []
    for start in sorted(buckets):
        rows = sorted(buckets[start], key=lambda r: r["ts"])
        vals = [r["value"] for r in rows]
        out.append({"sensor": rows[0]["sensor"], "bucket_start": start, "count": len(rows), "sum": sum(vals), "min": min(vals),
                    "max": max(vals), "readings": [{"ts": r["ts"], "value": r["value"]} for r in rows]})
    return sorted(out, key=lambda b: (b["sensor"], b["bucket_start"]))
''',
    ],
    guide=dict(
        prereqs="Lesson *Schema design patterns and anti-patterns* (bucket and computed patterns).",
        intuition="Round each timestamp down to the start of its window and use `(sensor, window start)` as a grouping "
                  "key. Everything else is bookkeeping: order the readings inside the bucket and fold them into "
                  "count, sum, min and max so that a dashboard can draw an hourly chart from the summaries without "
                  "opening the arrays.",
        hints=[
            "`start = ts - ts % bucket_seconds` (equivalently `ts // size * size`).",
            "Use a dict keyed by the tuple `(sensor, start)`; sorting the keys gives the required output order.",
            "Sort a bucket's readings by `ts` only - Python's sort is stable, so equal timestamps keep input order.",
        ],
        brute_force="Sort all readings by sensor and time and sweep once, closing a bucket whenever the sensor or window changes. "
                    "It is the same O(n log n) and matches how a streaming writer does it, but the dictionary version is shorter.",
        approach="""1. One pass: append each reading to `buckets[(sensor, start)]`.
2. For each key in sorted order: stable-sort by `ts`, compute the four summaries, strip `sensor` from the embedded readings.

**Dry run** - `s1` readings at ts 61, 5, 59, 60, 5, 185 with 60-second windows: starts 60, 0, 0, 60, 0, 180.
Bucket `(s1, 0)`: input order 5 (18), 59 (22), 5 (17) → sorted by ts: 5 (18), 5 (17), 59 (22); count 3, sum 57,
min 17, max 22. Bucket `(s1, 60)`: 60 (19), 61 (20). Bucket `(s1, 180)`: 185 (30).""",
        complexity="Time O(n log n), space O(n).",
        pitfalls="- Storing the bucket *index* (`ts // size`) instead of the bucket's start time.\n"
                 "- Grouping by window only and mixing sensors together.\n"
                 "- Breaking the tie order by sorting on `(ts, value)`.\n"
                 "- Sorting sensors numerically: the specification says plain string order, so `s10` precedes `s9`.",
        follow_up="Cap buckets at a maximum count (start a new bucket when full) so documents stay well under 16 MB. "
                  "Compare with MongoDB's native time-series collections, which apply bucketing automatically.",
    ),
),
dict(
    id="mongo-schema-validation",
    title="Validate a Document Against a $jsonSchema Subset",
    difficulty="Medium",
    pattern="Schema Design",
    kind="function",
    entry="validate",
    description=r"""
MongoDB collections are schemaless by default, but a `$jsonSchema` validator can reject malformed writes.
Implement `validate(doc, schema) -> bool` for this subset. A schema is a dict; every keyword present must
be satisfied, and a keyword that does not apply to the value's type is ignored.

| keyword | applies to | rule |
|---|---|---|
| `bsonType` | any value | a type name or a list of names; the value must be of at least one. `"object"` = dict, `"array"` = list, `"string"` = str, `"bool"` = bool, `"null"` = `None`, `"int"` = int, `"double"` = float, `"number"` = int or float. A bool is **never** an int, double or number. |
| `enum` | any value | the value must equal one of the listed values |
| `minimum`, `maximum` | numbers (not bools) | inclusive bounds |
| `minLength`, `maxLength` | strings | inclusive bounds on `len` |
| `minItems` | arrays | minimum number of elements |
| `items` | arrays | a schema every element must satisfy |
| `required` | objects | list of keys that must be present |
| `properties` | objects | map of key → schema; checked only for keys that are present |
| `additionalProperties` | objects | when `False`, every key must appear in `properties` |

An empty schema accepts everything.

**Example:** schema `{"bsonType": "object", "required": ["age"], "properties": {"age": {"bsonType": "int", "minimum": 13}}}`
accepts `{"age": 20, "nick": "z"}` and rejects `{"age": 12}`, `{"age": "20"}` and `{"nick": "z"}`.
""",
    starter='''def validate(doc, schema: dict) -> bool:
    pass
''',
    solution='''def validate(doc, schema):
    def is_num(v):
        return isinstance(v, (int, float)) and not isinstance(v, bool)

    def type_ok(v, t):
        if t == "object":
            return isinstance(v, dict)
        if t == "array":
            return isinstance(v, list)
        if t == "string":
            return isinstance(v, str)
        if t == "bool":
            return isinstance(v, bool)
        if t == "null":
            return v is None
        if isinstance(v, bool):
            return False
        if t == "int":
            return isinstance(v, int)
        if t == "double":
            return isinstance(v, float)
        if t == "number":
            return isinstance(v, (int, float))
        return False

    def ok(v, s):
        if "bsonType" in s:
            types = s["bsonType"] if isinstance(s["bsonType"], list) else [s["bsonType"]]
            if not any(type_ok(v, t) for t in types):
                return False
        if "enum" in s and not any(v == e and type(v) == type(e) for e in s["enum"]):
            return False
        if is_num(v):
            if "minimum" in s and v < s["minimum"]:
                return False
            if "maximum" in s and v > s["maximum"]:
                return False
        if isinstance(v, str):
            if "minLength" in s and len(v) < s["minLength"]:
                return False
            if "maxLength" in s and len(v) > s["maxLength"]:
                return False
        if isinstance(v, list):
            if "minItems" in s and len(v) < s["minItems"]:
                return False
            if "items" in s and not all(ok(x, s["items"]) for x in v):
                return False
        if isinstance(v, dict):
            props = s.get("properties", {})
            if any(k not in v for k in s.get("required", [])):
                return False
            if any(k in v and not ok(v[k], sub) for k, sub in props.items()):
                return False
            if s.get("additionalProperties") is False and any(k not in props for k in v):
                return False
        return True

    return ok(doc, schema)
''',
    tests=[
        [{"age": 20, "nick": "z"}, {"bsonType": "object", "required": ["age"], "properties": {"age": {"bsonType": "int", "minimum": 13}}}],
        [{"age": 12}, {"bsonType": "object", "required": ["age"], "properties": {"age": {"bsonType": "int", "minimum": 13}}}],
        [{"nick": "z"}, {"bsonType": "object", "required": ["age"], "properties": {"age": {"bsonType": "int", "minimum": 13}}}],
        [{"email": "ada@x.io", "age": 36}, _USER_SCHEMA],
        [{"email": "ada@x.io", "age": 36.0}, _USER_SCHEMA],
        [{"email": "ada@x.io", "age": True}, _USER_SCHEMA],
        [{"email": "a@x", "age": 36}, _USER_SCHEMA],
        [{"email": "ada@x.io", "age": 121}, _USER_SCHEMA],
        [{"email": "ada@x.io", "age": 13, "plan": None, "score": None, "tags": ["a", "bb"]}, _USER_SCHEMA],
        [{"email": "ada@x.io", "age": 13, "plan": "gold"}, _USER_SCHEMA],
        [{"email": "ada@x.io", "age": 13, "score": 3}, _USER_SCHEMA],
        [{"email": "ada@x.io", "age": 13, "tags": []}, _USER_SCHEMA],
        [{"email": "ada@x.io", "age": 13, "tags": ["ok", "waytoolong"]}, _USER_SCHEMA],
        [{"email": "ada@x.io", "age": 13, "tags": ["ok", 5]}, _USER_SCHEMA],
        [{"email": "ada@x.io", "age": 13, "address": {"city": "Riga", "zip": 1050}}, _USER_SCHEMA],
        [{"email": "ada@x.io", "age": 13, "address": {"city": "Riga", "street": "Elm"}}, _USER_SCHEMA],
        [{"email": "ada@x.io", "age": 13, "address": {"zip": "LV-1050"}}, _USER_SCHEMA],
        [{"email": "ada@x.io", "age": 13, "address": "Riga"}, _USER_SCHEMA],
        [[1, 2, 3], {"bsonType": "array", "items": {"bsonType": "number", "maximum": 2.5}}],
        ["anything", {}],
        [7, {"minLength": 3, "required": ["x"], "minItems": 2}],
        [False, {"enum": [0, 1]}],
        [None, {"bsonType": ["int", "string"]}],
    ],
    examples=3,
    wrong_solutions=[
        '''def validate(doc, schema):
    names = {"object": dict, "array": list, "string": str, "bool": bool, "null": type(None), "int": int, "double": float, "number": (int, float)}
    def ok(v, s):
        if "bsonType" in s:
            ts = s["bsonType"] if isinstance(s["bsonType"], list) else [s["bsonType"]]
            if not any(isinstance(v, names[t]) for t in ts):
                return False
        if "enum" in s and v not in s["enum"]:
            return False
        if isinstance(v, (int, float)):
            if "minimum" in s and v < s["minimum"]:
                return False
            if "maximum" in s and v > s["maximum"]:
                return False
        if isinstance(v, str):
            if "minLength" in s and len(v) < s["minLength"]:
                return False
            if "maxLength" in s and len(v) > s["maxLength"]:
                return False
        if isinstance(v, list):
            if "minItems" in s and len(v) < s["minItems"]:
                return False
            if "items" in s and not all(ok(x, s["items"]) for x in v):
                return False
        if isinstance(v, dict):
            props = s.get("properties", {})
            if any(k not in v for k in s.get("required", [])):
                return False
            if any(k in v and not ok(v[k], sub) for k, sub in props.items()):
                return False
            if s.get("additionalProperties") is False and any(k not in props for k in v):
                return False
        return True
    return ok(doc, schema)
''',
        '''def validate(doc, schema):
    def ok(v, s):
        t = s.get("bsonType")
        if t == "object":
            if not isinstance(v, dict):
                return False
            for k in s.get("required", []):
                if k not in v:
                    return False
            for k, sub in s.get("properties", {}).items():
                if not ok(v.get(k), sub):
                    return False
        if t == "int" and not (isinstance(v, int) and not isinstance(v, bool)):
            return False
        if t == "string" and not isinstance(v, str):
            return False
        if "minimum" in s and isinstance(v, (int, float)) and v < s["minimum"]:
            return False
        if "maximum" in s and isinstance(v, (int, float)) and v > s["maximum"]:
            return False
        return True
    return ok(doc, schema)
''',
    ],
    guide=dict(
        prereqs="Lesson *Schema design patterns and anti-patterns* (schema validation section). Recursion.",
        intuition="A schema and a value are two trees of the same shape. Validation walks them together: check the "
                  "keywords that apply to this node, then recurse into `properties` and `items`. Each keyword is "
                  "guarded by a type test so that, for example, `minLength` on a number is irrelevant rather than an error.",
        hints=[
            "Write `type_ok(value, type_name)` first and reject booleans before testing for int, double or number.",
            "Group the remaining keywords by the kind of value they apply to: numbers, strings, lists, dicts.",
            "`properties` constrains only keys that are present; presence itself is the job of `required`.",
        ],
        brute_force="Hard-coding the checks for one particular schema (`if 'age' not in doc ...`) is what application code "
                    "often does. It cannot be reused, and it drifts from the validator installed on the collection.",
        approach="""1. `bsonType`: normalise to a list of names; at least one must match.
2. `enum`: equality with one listed value (taking care that `False` is not accepted for `0`).
3. Numeric, string, array and object keywords, each behind an `isinstance` guard.
4. Recurse: `items` for each element, `properties[key]` for each present key.

**Dry run** - `{"email": "ada@x.io", "age": 13, "address": {"city": "Riga", "street": "Elm"}}` against the user
schema: top level is an object with both required keys; `email` is a string of length 8 ≥ 5; `age` 13 is an int
within [13, 120]; `address` is an object with `city`, but `street` is not listed and `additionalProperties` is
`False` → invalid.""",
        complexity="Time O(size of the document + size of the schema reached), space O(depth) for the recursion.",
        pitfalls="- `isinstance(True, int)` is true: without a guard, `True` passes as an int and `False == 0` passes an enum.\n"
                 "- Validating absent optional properties as if they were `None`.\n"
                 "- Raising an error when a keyword does not apply to the value's type instead of ignoring it.\n"
                 "- Forgetting that `additionalProperties: False` at the top level of a real collection must list `_id`.",
        follow_up="Return the list of failing paths instead of a bool, as the server does in the `errInfo` of a failed write (MongoDB 5.0+). "
                  "Add `pattern`, `uniqueItems`, `anyOf` and `dependencies`.",
    ),
),
dict(
    id="mongo-objectid-timestamp",
    title="Decode an ObjectId",
    difficulty="Easy",
    pattern="BSON Types",
    kind="function",
    entry="objectid_info",
    description=r"""
An ObjectId is 12 bytes, usually shown as 24 hexadecimal characters:

| bytes | hex chars | content |
|---|---|---|
| 0-3 | 0-7 | creation time: seconds since the Unix epoch, big-endian unsigned |
| 4-8 | 8-17 | a random value unique to the machine and process |
| 9-11 | 18-23 | an incrementing counter, big-endian unsigned |

`objectid_info(oid)` returns `None` unless `oid` is a string of exactly 24 hexadecimal characters (either
case). Otherwise return

```
{"timestamp": <int seconds>, "iso": "YYYY-MM-DDTHH:MM:SSZ" (UTC), "random": <10 lowercase hex chars>, "counter": <int>}
```

**Example:** `"5f43a1b2c3d4e5f6a7b8c9d0"` →
`{"timestamp": 1598267826, "iso": "2020-08-24T11:17:06Z", "random": "c3d4e5f6a7", "counter": 12110288}`

**Example:** `"xyz"` → `None`
""",
    starter='''def objectid_info(oid: str) -> Optional[dict]:
    pass
''',
    solution='''def objectid_info(oid):
    import datetime
    if not isinstance(oid, str) or len(oid) != 24:
        return None
    if any(c not in "0123456789abcdefABCDEF" for c in oid):
        return None
    ts = int(oid[:8], 16)
    when = datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=ts)
    return {
        "timestamp": ts,
        "iso": when.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "random": oid[8:18].lower(),
        "counter": int(oid[18:], 16),
    }
''',
    tests=[
        ["5f43a1b2c3d4e5f6a7b8c9d0"],
        ["xyz"],
        ["000000000000000000000000"],
        ["ffffffffffffffffffffffff"],
        ["65A1B2C3DEADBEEF00112233"],
        ["65a1b2c3deadbeef0011223"],
        ["65a1b2c3deadbeef001122334"],
        ["65a1b2c3deadbeef0011223g"],
        ["65a1b2c3 eadbeef00112233"],
        [""],
        ["0000003c0000000000000001"],
        ["386d4380aaaaaaaaaa000100"],
        ["7fffffff0102030405ffffff"],
        ["+5a1b2c3deadbeef00112233"],
    ],
    examples=2,
    wrong_solutions=[
        '''def objectid_info(oid):
    import datetime
    if len(oid) != 24:
        return None
    try:
        ts = int(oid[:8], 16)
        counter = int(oid[18:], 16)
    except ValueError:
        return None
    when = datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=ts)
    return {"timestamp": ts, "iso": when.strftime("%Y-%m-%dT%H:%M:%SZ"), "random": oid[8:18].lower(), "counter": counter}
''',
        '''def objectid_info(oid):
    import datetime
    if not isinstance(oid, str) or len(oid) != 24 or any(c not in "0123456789abcdefABCDEF" for c in oid):
        return None
    ts = int(oid[:8], 16)
    when = datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=ts)
    return {"timestamp": ts, "iso": when.strftime("%Y-%m-%dT%H:%M:%SZ"), "random": oid[8:18], "counter": int(oid[20:], 16)}
''',
    ],
    guide=dict(
        prereqs="Lesson *BSON types, ObjectId and the shell*. Hexadecimal: two hex characters per byte.",
        intuition="An ObjectId is not an opaque random string: its first four bytes are a clock reading. That is why "
                  "ObjectIds sort roughly by creation time and why `_id` can stand in for a `created_at` field. "
                  "Decoding is slicing a hex string at fixed offsets and converting two of the slices to integers.",
        hints=[
            "Validate first: a string, length 24, every character a hex digit.",
            "`int(text, 16)` converts hex to an integer; the first 8 characters are the timestamp.",
            "Build the UTC time as `datetime(1970, 1, 1) + timedelta(seconds=ts)` and format it with `strftime`.",
        ],
        brute_force="Converting digit by digit with a manual base-16 loop works and is worth doing once; `int(s, 16)` does the same thing.",
        approach="""1. Reject anything that is not exactly 24 hex characters.
2. `ts = int(oid[:8], 16)`; `counter = int(oid[18:], 16)`; `random = oid[8:18].lower()`.
3. Format `ts` as an ISO-8601 UTC string.

**Dry run** - `5f43a1b2 c3d4e5f6a7 b8c9d0`: `0x5f43a1b2` = 1,598,267,826 seconds → 24 August 2020, 11:17:06 UTC;
random part `c3d4e5f6a7`; counter `0xb8c9d0` = 12,110,288.""",
        complexity="O(1): the input has a fixed size.",
        pitfalls="- Relying on `int(s, 16)` for validation: it accepts a leading `+`, surrounding spaces and underscores.\n"
                 "- Slicing by bytes instead of hex characters (offsets 4 and 9 instead of 8 and 18).\n"
                 "- Formatting in local time instead of UTC.\n"
                 "- The timestamp has one-second resolution, so ObjectIds created in the same second by different processes are not ordered by creation time.",
        follow_up="Go the other way: build the smallest ObjectId for a given date to query `_id` by time range, e.g. everything inserted yesterday, using only the default `_id` index.",
    ),
),
]
