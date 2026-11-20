# Reading explain output and covered queries

> **Before this lesson:** you should know what an index, a collection scan, a compound index, a prefix and the ESR rule are - all from [Single-field and compound indexes: the ESR rule](#/lesson/mongodb/index-basics). Projection is explained in [Cursors, sorting and pagination done right](#/lesson/mongodb/cursors-pagination).

## In plain words

When a query is slow, guessing at the cause wastes hours. MongoDB will tell you exactly what it did if you ask. The tool is called **explain**: you attach it to a query and, instead of the results, you receive a report describing the route the server took and how much work each step cost.

Think of the itemised receipt from a garage. "Car fixed: 480" tells you nothing. "Diagnosis 40, new belt 60, labour 6 hours at 60, sundries 20" tells you where the money went and which line to question. Explain is the itemised receipt for a query.

The second topic, the **covered query**, is the cheapest kind of query there is: one that the index can answer entirely by itself, so that not a single document has to be opened. In the cookbook picture from the last lesson, it is a question such as "on which pages is saffron used?" - the index at the back answers it and you never turn to the recipes.

Why it matters for a job: reading explain output is the core skill of performance work. In an interview, being able to say "I would run explain with executionStats and compare keys examined, documents examined and documents returned" separates people who have tuned a database from people who have only read about it.

## Asking for an explanation

Add `.explain(...)` to a query. The argument selects how much detail you get, called the **verbosity mode**:

| mode | what the server does | what you learn |
|---|---|---|
| `"queryPlanner"` (default) | chooses a plan but does not run it | which plan would be used |
| `"executionStats"` | runs the chosen plan | the plan plus real counts and timings |
| `"allPlansExecution"` | runs the chosen plan and reports the trial of the rejected ones | why the winner won |

`"executionStats"` is the one you will use most. Note that it really executes the query, so explaining a slow query is itself slow.

```javascript
ship> db.parcels.find({ depot: "leeds" }).explain("executionStats")
```

The report is long. The parts worth reading first are shown below, trimmed, for a collection of 200,000 parcels **without** an index on `depot`:

```javascript
{
  queryPlanner: {
    winningPlan: { stage: 'COLLSCAN', filter: { depot: { '$eq': 'leeds' } }, direction: 'forward' },
    rejectedPlans: []
  },
  executionStats: {
    nReturned: 16480,
    executionTimeMillis: 142,
    totalKeysExamined: 0,
    totalDocsExamined: 200000
  }
}
```

Two sections matter.

**`queryPlanner.winningPlan`** describes the chosen **plan**: the sequence of steps the server will perform. Each step is called a **stage**. Here there is a single stage, `COLLSCAN`, the collection scan.

**`executionStats`** holds the measurements. Four numbers carry most of the story:

| field | meaning |
|---|---|
| `nReturned` | documents the query returned |
| `totalKeysExamined` | index entries read |
| `totalDocsExamined` | documents fetched and inspected |
| `executionTimeMillis` | elapsed time in milliseconds |

In the report above, 200,000 documents were examined to return 16,480. More than eleven documents were read for every one returned. That ratio is the diagnosis.

## The same query with an index

```javascript
ship> db.parcels.createIndex({ depot: 1 })
ship> db.parcels.find({ depot: "leeds" }).explain("executionStats")
{
  queryPlanner: {
    winningPlan: {
      stage: 'FETCH',
      inputStage: { stage: 'IXSCAN', keyPattern: { depot: 1 }, indexName: 'depot_1',
                    indexBounds: { depot: [ '["leeds", "leeds"]' ] } }
    }
  },
  executionStats: { nReturned: 16480, executionTimeMillis: 19, totalKeysExamined: 16480, totalDocsExamined: 16480 }
}
```

The plan is now a small tree, and it is read **from the inside out**: the innermost `inputStage` runs first and feeds the stage that wraps it.

1. `IXSCAN` (index scan) walks the index `depot_1`. The `indexBounds` line says which part of the index was read: from `"leeds"` to `"leeds"`, both ends included. **Index bounds** are the start and end points of the stretch of the index the server reads.
2. `FETCH` takes each index entry, follows its pointer and loads the document.

The numbers are now 16,480 keys, 16,480 documents, 16,480 returned. One to one to one. That is the signature of a well-indexed query.

### The stages you will meet

| stage | meaning | good or bad? |
|---|---|---|
| `COLLSCAN` | read every document | bad on a large collection |
| `IXSCAN` | read a stretch of an index | good |
| `FETCH` | load documents the index pointed to | normal; costs one lookup per document |
| `SORT` | sort in memory (a blocking sort) | a warning sign on large inputs |
| `LIMIT` / `SKIP` | stop early / discard entries | fine |
| `PROJECTION_COVERED` | build results from index keys alone | the best case |
| `PROJECTION_SIMPLE` / `PROJECTION_DEFAULT` | build results from fetched documents | normal |
| `COUNT_SCAN` | count index entries without fetching | very good |

### Reading the three numbers together

A practical way to judge any query is to compare the funnel **keys examined → documents examined → documents returned**.

| pattern | what it means | typical fix |
|---|---|---|
| keys = docs = returned | ideal: every entry read was a result | nothing |
| keys = 0, docs much larger than returned | collection scan | create an index |
| keys = docs, both much larger than returned | the index narrows poorly; the rest is filtered after fetching | add the filtered field to the index |
| keys much larger than docs | many index entries read and rejected on the key | reorder index fields (ESR) |
| docs = 0, returned > 0 | covered query | celebrate |
| a `SORT` stage is present | results were sorted in memory | put the sort field in the index, after the equality fields |

> [!TIP]
> Do not judge by `executionTimeMillis` alone. On a laptop with a small test collection held in memory, a collection scan can take 2 ms. The counts tell you how the query will behave with production-sized data; the time tells you how it behaved once, here.

## How the planner chooses

When several indexes could serve a query, the planner does not reason about which is best from first principles. It holds a short race. Each candidate plan is run for a brief trial period, and the one that produces the first batch of results with the least work wins. The winner is stored in the **plan cache**, a memory of which plan to use for each **query shape** (the structure of a query: which fields, operators and sort it uses, ignoring the particular values). The next query with the same shape reuses the cached plan without another race.

`queryPlanner.rejectedPlans` lists the losers, and `allPlansExecution` shows the figures from the race.

Occasionally the planner picks badly, for example when the data is very uneven. You can then force an index with `hint`:

```javascript
ship> db.parcels.find({ depot: "leeds", status: "returned" }).hint({ depot: 1, status: 1 })
```

`hint` takes the index's key pattern or its name. Use it to compare plans while investigating. Leaving hints in application code is risky: if someone later drops that index, the query fails instead of falling back to another plan.

## A realistic investigation

A support screen shows "the 20 newest returned parcels at a depot". The only index is `{ depot: 1 }`.

```javascript
ship> db.parcels.find({ depot: "leeds", status: "returned" }).sort({ created: -1 }).limit(20)
...             .explain("executionStats")
// winningPlan (inside out): IXSCAN depot_1 -> FETCH with filter status = returned -> SORT by created, limit 20
// nReturned: 20, totalKeysExamined: 16480, totalDocsExamined: 16480
```

Reading the funnel: the index found all 16,480 Leeds parcels; every one was fetched so that its `status` could be checked; about 800 survived; those were sorted in memory; 20 were returned. 16,480 documents read to deliver 20.

Apply ESR. Equality fields: `depot`, `status`. Sort field: `created`.

```javascript
ship> db.parcels.createIndex({ depot: 1, status: 1, created: -1 })
ship> db.parcels.find({ depot: "leeds", status: "returned" }).sort({ created: -1 }).limit(20)
...             .explain("executionStats")
// winningPlan (inside out): IXSCAN depot_1_status_1_created_-1 -> FETCH -> LIMIT 20
// nReturned: 20, totalKeysExamined: 20, totalDocsExamined: 20
```

The `SORT` stage is gone and all three numbers are 20. The query is about 800 times cheaper, and it will stay that cheap however many parcels Leeds accumulates.

## Covered queries

Look again at the well-indexed plan: `IXSCAN` then `FETCH`. The fetch is the expensive half. An index is compact and usually in memory; documents are large and scattered across the disk. Each fetch may be a separate disk read.

Now suppose the screen only needs the creation times, not whole parcels:

```javascript
ship> db.parcels.find({ depot: "leeds", status: "returned" }, { created: 1, _id: 0 })
...             .explain("executionStats")
{
  queryPlanner: { winningPlan: { stage: 'PROJECTION_COVERED',
                                 inputStage: { stage: 'IXSCAN', indexName: 'depot_1_status_1_created_-1' } } },
  executionStats: { nReturned: 812, totalKeysExamined: 812, totalDocsExamined: 0 }
}
```

`totalDocsExamined: 0`. There is no `FETCH` stage at all. Every field the query needs - `depot` and `status` to filter, `created` to return - is stored in the index entry itself, so the server builds the answer from the index and never opens a document. The index **covers** the query.

A query is covered when all of these hold:

1. every field in the **filter** is part of the index;
2. every field in the **projection** (the fields returned) is part of the index;
3. `_id` is excluded with `_id: 0`, unless `_id` is itself in the index - forgetting this is the most common reason a query that "should" be covered is not;
4. none of the indexed fields involved holds an **array** in any document (see multikey indexes below);
5. the query does not test for `null` or for a missing field in a way that requires seeing the document.

Sometimes it is worth adding a field to the end of an index purely so that a very frequent query becomes covered. The index grows a little; the query stops touching documents entirely.

> [!INTERVIEW]
> **"What is a covered query and how do you recognise one?"** A covered query is satisfied entirely from an index: the filter fields and the returned fields are all in the index, so no document is fetched. In explain output you see `totalDocsExamined: 0` and a `PROJECTION_COVERED` stage over an `IXSCAN`, with no `FETCH`. Mention the two classic reasons it fails to be covered: `_id` was not excluded from the projection, or an indexed field contains arrays (a multikey index cannot cover).

## Multikey indexes

When you index a field that holds an array, MongoDB creates one index entry **per array element**. A document with `tags: ["fragile", "express", "insured"]` contributes three entries. Such an index is called a **multikey index**, and it is what makes `find({ tags: "fragile" })` fast.

Three consequences are worth knowing.

- **Size.** The index has as many entries as there are array elements in total, which can be many times the number of documents.
- **No covering.** An index entry holds one element, not the array, so the server cannot rebuild the field from the index and must fetch the document.
- **One array per compound index.** A compound index may include at most one field that is an array in any given document. An attempt to insert a document in which two fields of the same compound index are both arrays is rejected, because the index would need an entry for every combination of elements.

Explain reports `isMultiKey: true` on the `IXSCAN` stage when the index is multikey.

## When an index does not help

An index is a detour: read the index, then jump to each document. That pays off when few documents are wanted. If a query matches a large part of the collection - a rough rule of thumb is more than a third - jumping around to fetch them one by one can be slower than reading the collection straight through. Reports that touch most of the data are often better served by a collection scan, by a covered query, or by pre-computed summaries.

> [!WARNING]
> `explain("executionStats")` on a write is safe for `update` and `delete` - the server reports what it *would* do without changing data. But explaining an aggregation pipeline that ends in `$out` or `$merge`, or calling explain through a helper that does not support it, deserves care. When investigating writes on production data, read the manual page for that command first.

## The same from Python

```python
from pymongo import MongoClient

parcels = MongoClient()["ship"]["parcels"]

query = {"depot": "leeds", "status": "returned"}
plan = parcels.find(query).sort("created", -1).limit(20).explain()        # 1
stats = plan["executionStats"]                                           # 2
print(stats["nReturned"], stats["totalKeysExamined"], stats["totalDocsExamined"])

def stages(node):                                                        # 3
    names = [node["stage"]]
    if "inputStage" in node:
        names += stages(node["inputStage"])
    return names

print(" <- ".join(stages(plan["queryPlanner"]["winningPlan"])))          # 4

covered = parcels.find(query, {"created": 1, "_id": 0}).explain()        # 5
print(covered["executionStats"]["totalDocsExamined"])                    # 6
```

1. In PyMongo, `explain()` on a cursor returns the report as a dictionary. It uses a verbosity that includes execution statistics.
2. `executionStats` holds the counts. With the compound index in place this prints `20 20 20`.
3. A small helper walks the nested `inputStage` chain and collects the stage names. Plans with several branches use `inputStages` (a list); this helper handles the common single-chain case.
4. Prints something like `LIMIT <- FETCH <- IXSCAN`. Reading right to left gives the order of execution.
5. The same filter with a projection restricted to an indexed field and `_id` switched off.
6. Prints `0`: the query is covered.

## Simulate it yourself

This simulation is a miniature planner. It decides between a collection scan and an index scan, reports the four explain numbers and says whether the query was covered. Run it and compare the plans.

```python-run
import random

random.seed(11)
DEPOTS = ["leeds", "york", "hull", "bath", "ayr", "ely", "wick", "oban", "rye", "deal", "bude", "looe"]
parcels = [{"_id": i,
            "depot": random.choice(DEPOTS),
            "status": random.choices(["in_transit", "delivered", "returned"], weights=[20, 75, 5])[0],
            "created": random.randint(0, 10**6),
            "tags": random.sample(["fragile", "express", "insured", "bulky"], k=random.randint(0, 2))}
           for i in range(60_000)]

def explain(docs, index, query, projection=None, sort=None, limit=None):
    """index: list of fields or None. query: field -> exact value. Returns explain-style numbers."""
    index = index or []
    prefix = []
    for field in index:                       # equality fields at the front of the index form the bounds
        if field not in query:
            break
        prefix.append(field)
    all_match = [d for d in docs if all(d.get(f) == v for f, v in query.items())]
    if not prefix:
        plan, keys, fetched = ["COLLSCAN"], 0, len(docs)
        sorted_by_index = False
    else:
        in_bounds = [d for d in docs if all(d[f] == query[f] for f in prefix)]
        sorted_by_index = sort is not None and len(index) > len(prefix) and index[len(prefix)] == sort
        if sorted_by_index and limit:         # walk in order and stop once `limit` results are found
            in_bounds = sorted(in_bounds, key=lambda d: -d[sort])
            keys, found = 0, 0
            for d in in_bounds:
                keys += 1
                found += all(d.get(f) == v for f, v in query.items())
                if found == limit:
                    break
        else:
            keys = len(in_bounds)
        multikey = any(isinstance(d.get(f), list) for d in docs[:500] for f in index)
        needed = set(query) | set(projection or ["<whole document>"])
        covered = projection is not None and needed <= set(index) and not multikey
        fetched = 0 if covered else keys
        plan = ["IXSCAN(" + ",".join(index) + ")"] + (["PROJECTION_COVERED"] if covered else ["FETCH"])
    if sort is not None and not sorted_by_index:
        plan.append("SORT")
    if limit:
        plan.append("LIMIT")
    returned = min(len(all_match), limit) if limit else len(all_match)
    return {"plan": " -> ".join(plan), "keys": keys, "docs": fetched, "returned": returned}

q = {"depot": "leeds", "status": "returned"}
cases = [
    ("no index",                         None,                           dict(sort="created", limit=20)),
    ("index (depot)",                    ["depot"],                      dict(sort="created", limit=20)),
    ("index (depot,status)",             ["depot", "status"],            dict(sort="created", limit=20)),
    ("index (depot,status,created)",     ["depot", "status", "created"], dict(sort="created", limit=20)),
    ("same, projection {created}",       ["depot", "status", "created"], dict(projection=["created"])),
    ("same, projection {created,_id}",   ["depot", "status", "created"], dict(projection=["created", "_id"])),
    ("index (depot,status,tags)",        ["depot", "status", "tags"],    dict(projection=["tags"])),
]
for label, index, options in cases:
    r = explain(parcels, index, q, **options)
    print(label.ljust(32), "keys %6d  docs %6d  returned %4d   %s" % (r["keys"], r["docs"], r["returned"], r["plan"]))
```

Reading the output, row by row:

- **No index**: 60,000 documents examined for 20 results, with a `SORT` stage.
- **Index on `depot`**: about 5,000 keys and 5,000 documents - a twelfth of the collection - and still a `SORT`, because status is checked only after fetching.
- **Index on `depot, status`**: roughly 250 keys and documents. Much better, but the `SORT` remains.
- **Index on `depot, status, created`**: 20 keys, 20 documents, 20 returned, no `SORT`. The scan stops as soon as 20 entries have been read.
- **Projection of `created` only**: `docs` drops to 0 and the plan ends in `PROJECTION_COVERED`.
- **Projection including `_id`**: the fetch returns, because `_id` is not in the index.
- **Index containing the array field `tags`**: not covered, even though every needed field is in the index. A multikey index cannot cover.

## Pitfalls

- **Reading only the time.** Small test data hides bad plans; read the counts.
- **Reading the plan top-down.** Execution starts at the innermost stage.
- **Forgetting `_id: 0`** and wondering why a query is not covered.
- **Expecting a multikey index to cover.**
- **Leaving `hint` in application code.**
- **Testing explain on an empty or tiny development collection**, where the planner may legitimately choose a different plan than it would on production data.
- **Indexing for queries that return most of the collection.** The index adds cost without benefit.

## Cheat sheet

| goal | command |
|---|---|
| see the chosen plan | `db.c.find(q).explain()` |
| see real counts | `db.c.find(q).explain("executionStats")` |
| compare candidate plans | `db.c.find(q).explain("allPlansExecution")` |
| force an index | `db.c.find(q).hint({ a: 1, b: 1 })` |
| explain an update | `db.c.explain("executionStats").updateOne(q, u)` |

| symptom in explain | meaning |
|---|---|
| `stage: COLLSCAN` | no usable index |
| `SORT` stage | in-memory sort |
| `totalDocsExamined` far above `nReturned` | index not selective enough for this filter |
| `totalKeysExamined` far above `nReturned` | wrong field order in the index |
| `totalDocsExamined: 0` | covered query |
| `isMultiKey: true` | an indexed field holds arrays |

## Summary

- `explain("executionStats")` runs a query and reports its plan and the work done.
- Read the plan from the innermost stage outward; learn `COLLSCAN`, `IXSCAN`, `FETCH`, `SORT` and `PROJECTION_COVERED`.
- Compare keys examined, documents examined and documents returned; the closer they are, the better the query.
- The planner trials candidate plans, caches the winner per query shape, and can be overridden with `hint` for experiments.
- A covered query takes all filter and projected fields from the index and examines zero documents; remember `_id: 0`.
- Indexes on array fields are multikey: one entry per element, no covering, one array field per compound index.

## Glossary

- **Explain** - a command that reports how a query is, or would be, executed.
- **Verbosity mode** - the level of detail requested from explain.
- **Plan** - the sequence of steps chosen to execute a query.
- **Stage** - one step of a plan, such as `IXSCAN` or `FETCH`.
- **`IXSCAN` / `COLLSCAN`** - index scan / collection scan.
- **`FETCH`** - loading full documents that index entries point to.
- **Index bounds** - the start and end of the stretch of an index that is read.
- **`nReturned`, `totalKeysExamined`, `totalDocsExamined`** - documents returned, index entries read, documents inspected.
- **Plan cache** - the server's memory of the winning plan for each query shape.
- **Query shape** - the structure of a query without its specific values.
- **Hint** - an instruction forcing the use of a particular index.
- **Covered query** - a query answered entirely from an index, with no documents examined.
- **Multikey index** - an index on an array field, holding one entry per element.

## Check yourself

```quiz
[
  {"q": "Which explain mode actually runs the query and reports counts such as totalDocsExamined?",
   "options": ["queryPlanner", "executionStats", "planCache", "verbose"],
   "answer": 1,
   "explain": "queryPlanner only chooses a plan; executionStats executes it and adds the measurements."},
  {"q": "Explain shows nReturned: 20, totalKeysExamined: 16480, totalDocsExamined: 16480 and a SORT stage. What is the most likely fix?",
   "options": ["Increase the server's memory", "Extend the index with the other equality field and the sort field", "Add a hint", "Remove the limit"],
   "answer": 1,
   "explain": "The index narrows too little and does not supply the order; an Equality-Sort index lets the scan stop after 20 keys."},
  {"q": "A plan is FETCH with inputStage IXSCAN. Which stage runs first?",
   "options": ["FETCH", "IXSCAN", "They run at the same time", "It depends on the limit"],
   "answer": 1,
   "explain": "Plans are read from the innermost stage outward: the index scan feeds the fetch."},
  {"q": "The index is {depot: 1, status: 1, created: -1}. Which query is covered?",
   "options": ["find({depot: \"leeds\"}, {created: 1})", "find({depot: \"leeds\"}, {created: 1, _id: 0})", "find({depot: \"leeds\"}, {weight_kg: 1, _id: 0})", "find({depot: \"leeds\"})"],
   "answer": 1,
   "explain": "All filter and projected fields must be in the index and _id must be excluded; the first option returns _id, which is not in the index."},
  {"q": "What does totalDocsExamined: 0 with nReturned: 812 indicate?",
   "options": ["The query failed", "A covered query answered from the index alone", "A collection scan", "The plan cache was empty"],
   "answer": 1,
   "explain": "No documents were fetched, yet results were returned: they were built from index keys."},
  {"q": "Why can a multikey index not cover a query on its array field?",
   "options": ["Arrays cannot be indexed", "Each index entry holds one element, so the full array cannot be rebuilt from the index", "Multikey indexes are stored on disk only", "The planner refuses to use them"],
   "answer": 1,
   "explain": "The index stores an entry per element, not the array as a whole, so the document must be fetched."},
  {"q": "How does the planner pick among several candidate indexes?",
   "options": ["Alphabetically by index name", "It always takes the newest index", "It runs the candidates for a short trial and caches the plan that did the least work", "It asks the client"],
   "answer": 2,
   "explain": "Candidate plans race briefly; the winner is cached per query shape."},
  {"q": "Why is hint() risky in application code?",
   "options": ["It makes queries return wrong results", "If the hinted index is dropped later, the query fails instead of using another plan", "It disables the journal", "It only works in mongosh"],
   "answer": 1,
   "explain": "A hint names a specific index; without that index the query errors out."}
]
```

> **Source:** MongoDB: The Definitive Guide 3e, ch. 5 (topics only; wording and examples are original). MongoDB Manual: https://www.mongodb.com/docs/manual/reference/explain-results/ , https://www.mongodb.com/docs/manual/core/query-optimization/ , https://www.mongodb.com/docs/manual/core/indexes/index-types/index-multikey/
