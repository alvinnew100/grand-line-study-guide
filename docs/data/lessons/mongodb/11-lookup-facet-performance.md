# $lookup, $facet and pipeline performance

> **Before this lesson:** you should be able to build a pipeline from `$match`, `$project`, `$group`, `$sort` and `$unwind` - see [Pipelines: $match, $project, $group and $unwind](#/lesson/mongodb/pipeline-stages). The performance section relies on indexes and explain output from [Single-field and compound indexes: the ESR rule](#/lesson/mongodb/index-basics) and [Reading explain output and covered queries](#/lesson/mongodb/explain-covered).

## In plain words

The previous lesson worked on one collection at a time. Two needs go beyond that.

First, data sometimes lives in two collections that must be brought together: orders in one, customers in another. Bringing them together is called a **join**. Imagine two stacks of index cards, one stack of orders and one of customers. For each order card you look up the matching customer card and clip the two together. In a pipeline the stage that does the clipping is **`$lookup`**.

Second, a single screen often needs several different summaries of the same data. A shop's search page shows the matching products, a count per brand in the sidebar and a price histogram. That is three reports from one set of documents. Picture one conveyor belt that splits into three side belts, each making a different product from identical parts. That splitter is **`$facet`**.

The last part of the lesson is about making pipelines fast, because a pipeline that is correct on a hundred test documents can be painfully slow on a hundred million.

Why it matters for a job: "how do you do a join in MongoDB, and when should you avoid one?" is among the most frequent MongoDB interview questions, and slow reporting pipelines are a routine production problem.

## The data

A small plant nursery keeps three collections.

```javascript
// customers
{ _id: "c1", name: "Renata", city: "Porto" }
{ _id: "c2", name: "Jonas",  city: "Graz" }
{ _id: "c3", name: "Mei",    city: "Porto" }

// plants
{ _id: "p1", name: "fern",   price: 12, light: "shade" }
{ _id: "p2", name: "cactus", price: 8,  light: "sun" }
{ _id: "p3", name: "ficus",  price: 35, light: "sun" }

// orders
{ _id: 1, customer_id: "c1", plant_ids: ["p1", "p2"], total: 20 }
{ _id: 2, customer_id: "c2", plant_ids: ["p3"],       total: 35 }
{ _id: 3, customer_id: "c1", plant_ids: ["p2"],       total: 8  }
{ _id: 4, customer_id: "c9", plant_ids: [],           total: 0  }
```

An order does not contain the customer's name. It contains `customer_id`, the `_id` of a document in another collection. A field whose value is the identity of a document elsewhere is called a **reference** (relational databases call it a foreign key).

## $lookup: joining two collections

```javascript
nursery> db.orders.aggregate([
...   { $lookup: { from: "customers", localField: "customer_id", foreignField: "_id", as: "customer" } }
... ])
[
  { _id: 1, customer_id: 'c1', plant_ids: [ 'p1', 'p2' ], total: 20, customer: [ { _id: 'c1', name: 'Renata', city: 'Porto' } ] },
  { _id: 2, customer_id: 'c2', plant_ids: [ 'p3' ], total: 35, customer: [ { _id: 'c2', name: 'Jonas', city: 'Graz' } ] },
  { _id: 3, customer_id: 'c1', plant_ids: [ 'p2' ], total: 8, customer: [ { _id: 'c1', name: 'Renata', city: 'Porto' } ] },
  { _id: 4, customer_id: 'c9', plant_ids: [], total: 0, customer: [] }
]
```

The four settings read like a sentence:

- `from: "customers"` - the other collection to look in;
- `localField: "customer_id"` - the field of the *current* document (an order) to match with;
- `foreignField: "_id"` - the field in the *other* collection to compare against;
- `as: "customer"` - the name of the new field that receives the matches.

Three behaviours deserve attention.

**The result is always an array.** Even when exactly one customer matches, `customer` is a one-element array, because in general a lookup can find several matches.

**Unmatched documents are kept.** Order 4 refers to customer `c9`, who does not exist. The order still comes out, with an empty array. In SQL terms this is a **left outer join**: every document from the left-hand side (orders) survives, matched or not.

**Arrays in the local field match element by element.** If `localField` holds an array, a foreign document matches when its value equals *any* element:

```javascript
{ $lookup: { from: "plants", localField: "plant_ids", foreignField: "_id", as: "plants" } }
// order 1 gets plants: [ { _id: 'p1', name: 'fern', ... }, { _id: 'p2', name: 'cactus', ... } ]
```

### Flattening the result

A one-element array is awkward to work with. The usual follow-up is `$unwind`, which turns the array into a plain embedded document:

```javascript
nursery> db.orders.aggregate([
...   { $lookup: { from: "customers", localField: "customer_id", foreignField: "_id", as: "customer" } },
...   { $unwind: "$customer" },
...   { $group: { _id: "$customer.city", revenue: { $sum: "$total" } } }
... ])
[ { _id: 'Porto', revenue: 28 }, { _id: 'Graz', revenue: 35 } ]
```

After the unwind, `customer` is a document, so `"$customer.city"` reads the city. Notice what happened to order 4: its `customer` array was empty, `$unwind` drops documents with empty arrays, and so the order vanished. `$lookup` followed by a plain `$unwind` behaves like an **inner join**, which keeps only matched pairs. To keep the unmatched order, use `{ $unwind: { path: "$customer", preserveNullAndEmptyArrays: true } }`.

### Lookup with a sub-pipeline

Sometimes equality on one field is not enough: you want only some of the matching documents, or only some of their fields. `$lookup` accepts a `pipeline` that runs on the other collection for each incoming document:

```javascript
nursery> db.customers.aggregate([
...   { $lookup: {
...       from: "orders",
...       localField: "_id", foreignField: "customer_id",
...       pipeline: [ { $match: { total: { $gte: 10 } } }, { $project: { _id: 0, total: 1 } } ],
...       as: "big_orders"
...   } }
... ])
// Renata -> big_orders: [ { total: 20 } ]   (the 8-euro order is filtered out)
```

The inner pipeline filters and trims the matches before they are attached, so less data is carried along the belt.

### The cost of a join

For every document that reaches `$lookup`, the server performs a search in the other collection. If that collection has an index on `foreignField`, each search is a quick index lookup. If it does not, each search is a collection scan, and a thousand incoming documents mean a thousand scans. `_id` is always indexed. For any other `foreignField`, create an index.

> [!WARNING]
> `$lookup` exists for the occasional report, not as the default way to read data. If your application runs a `$lookup` on every page view to assemble something it always displays together, the data is modelled as tables and the join's cost is paid on every request. The usual cure is to embed the data that is read together, or to copy the few fields needed (say, the customer's name) into the order. Module 6 covers this decision.

## $facet: several reports in one pass

`$facet` takes a document in which each key names a sub-pipeline. Every sub-pipeline receives the same input documents, and the stage outputs **one** document holding each sub-pipeline's result as an array.

```javascript
nursery> db.plants.aggregate([
...   { $match: { price: { $gt: 0 } } },
...   { $facet: {
...       by_light: [ { $sortByCount: "$light" } ],
...       price_bands: [ { $bucket: { groupBy: "$price", boundaries: [0, 10, 20, 50], default: "other",
...                                   output: { count: { $sum: 1 } } } } ],
...       stats: [ { $group: { _id: null, avg: { $avg: "$price" }, max: { $max: "$price" } } } ]
...   } }
... ])
[ {
    by_light: [ { _id: 'sun', count: 2 }, { _id: 'shade', count: 1 } ],
    price_bands: [ { _id: 0, count: 1 }, { _id: 10, count: 1 }, { _id: 20, count: 1 } ],
    stats: [ { _id: null, avg: 18.333333333333332, max: 35 } ]
} ]
```

Read each branch in turn.

- `by_light` counts plants per light requirement. `$sortByCount` is the shorthand for group, count, sort descending.
- `price_bands` uses **`$bucket`**, which sorts documents into ranges. With boundaries `[0, 10, 20, 50]` the buckets are 0 up to (not including) 10, 10 up to 20, and 20 up to 50; each bucket is named by its lower boundary. A value outside all ranges goes into the `default` bucket. A relative, `$bucketAuto`, chooses boundaries for you so that buckets hold similar numbers of documents.
- `stats` computes overall figures by grouping everything under `_id: null`.

The benefit is consistency and economy: the three results come from one snapshot of the matching documents, in one round trip.

Two limitations follow from how it works. The whole output of `$facet` is a single document, so the combined results must fit in 16 megabytes. And the sub-pipelines cannot use indexes, because their input is the stream coming from the previous stage, not a collection. So place the selective `$match` **before** `$facet`, where it can use an index.

## Saving results: $out and $merge

A pipeline normally returns its results to the client. Two stages write them to a collection instead, and either must be the final stage.

- `{ $out: "daily_totals" }` replaces the named collection with the results.
- `{ $merge: { into: "daily_totals", on: "_id", whenMatched: "replace", whenNotMatched: "insert" } }` folds the results into an existing collection, updating documents that already exist and inserting new ones.

A report that takes a minute to compute can be run once an hour with `$merge`, and the dashboard then reads the small result collection instantly. A result stored in advance like this is called a **materialised view**.

## Making pipelines fast

The server runs stages in the order you wrote them, with a few safe rearrangements of its own. Six habits cover most of the performance problems you will meet.

**1. Filter first.** A `$match` at the very start of the pipeline is executed like a `find`, so it can use an index. A `$match` further down operates on the stream and cannot. The same holds for a leading `$sort`: it can read documents in index order, while a later one sorts in memory.

**2. Limit early.** `$sort` immediately followed by `$limit` is handled specially: the server keeps only the top N documents in memory while scanning, never the whole sorted set. Put the `$limit` directly after the `$sort`.

**3. Join late and little.** Every document that enters a `$lookup` triggers a search. Filter, group and limit *before* the lookup whenever the logic allows, so that it runs for 20 documents and not for 2 million.

**4. Index the foreign field.** As described above.

**5. Carry less.** Wide documents moving through many stages cost memory. If later stages need three fields, a `$project` trimming to those three after the initial `$match` can help. The server works out which fields a pipeline uses and fetches only those when it can, so do this where measurement shows a gain, not as a ritual.

**6. Mind the memory limit.** Each blocking stage - `$group`, a `$sort` that cannot use an index, `$bucket` - may use up to 100 megabytes of RAM. Beyond that the stage writes temporary files to disk, which is slower (and on versions before 6.0 the pipeline fails unless you pass `allowDiskUse: true`).

How do you see what the server actually does? The same way as for queries:

```javascript
nursery> db.orders.explain("executionStats").aggregate([
...   { $match: { total: { $gte: 10 } } },
...   { $lookup: { from: "customers", localField: "customer_id", foreignField: "_id", as: "customer" } }
... ])
```

The report shows whether the first stage used an index (`IXSCAN`) or scanned the collection (`COLLSCAN`), how many documents each stage passed on, and, for `$lookup`, how many documents and index keys were examined in the other collection.

> [!TIP]
> The server's optimiser moves stages when that cannot change the result. For example, a `$match` on a field of the original documents that you wrote after a `$project` or after a `$lookup` on unrelated fields is pushed in front of it. Do not rely on this silently: write the pipeline in the efficient order yourself, and confirm with explain.

> [!INTERVIEW]
> **"How do you join in MongoDB and what are the caveats?"** Use the `$lookup` aggregation stage with `from`, `localField`, `foreignField` and `as`. It is a left outer join that returns the matches as an array; follow it with `$unwind` for a flat, inner-join shape. Caveats: the foreign field must be indexed or every input document causes a collection scan; do the filtering before the lookup; arrays that grow large after a lookup can hit the 16 MB document limit; and a schema that needs a lookup on its hottest read path is usually better served by embedding or by duplicating a few fields.

## The same from Python

```python
from pymongo import MongoClient

db = MongoClient()["nursery"]
db.orders.create_index("customer_id")                                         # 1

revenue_by_city = db.orders.aggregate([
    {"$match": {"total": {"$gt": 0}}},                                        # 2
    {"$lookup": {"from": "customers", "localField": "customer_id",
                 "foreignField": "_id", "as": "customer"}},
    {"$unwind": "$customer"},                                                 # 3
    {"$group": {"_id": "$customer.city", "revenue": {"$sum": "$total"}}},
    {"$sort": {"revenue": -1}},
])
print({row["_id"]: row["revenue"] for row in revenue_by_city})                # 4

page = db.plants.aggregate([
    {"$facet": {"by_light": [{"$sortByCount": "$light"}],
                "stats": [{"$group": {"_id": None, "avg": {"$avg": "$price"}}}]}}
]).next()                                                                     # 5
print(page["by_light"], round(page["stats"][0]["avg"], 2))

db.orders.aggregate([{"$group": {"_id": "$customer_id", "spent": {"$sum": "$total"}}},
                     {"$merge": {"into": "customer_totals", "whenMatched": "replace"}}])   # 6
```

1. An index for lookups that go from customers to their orders.
2. Filtering happens before the join.
3. Flattens the one-element array and drops orders without a known customer.
4. Prints `{'Graz': 35, 'Porto': 28}`.
5. `$facet` yields exactly one document, so `.next()` fetches it from the cursor.
6. Writes one summary document per customer into `customer_totals`; nothing is returned to the client.

## Simulate it yourself

The simulation implements `$lookup` twice - once by scanning the other collection for every input document and once with a dictionary acting as an index - and counts the comparisons. It then runs a small `$facet`.

```python-run
import random

random.seed(3)
customers = [{"_id": "c%d" % i, "city": random.choice(["Porto", "Graz", "Turku", "Cork"])} for i in range(1000)]
orders = [{"_id": i, "customer_id": "c%d" % random.randrange(1050), "total": random.randint(0, 60)}
          for i in range(2000)]

def lookup_scan(local_docs, foreign_docs, local_field, foreign_field, as_field):
    """No index on the foreign field: scan the whole foreign collection for every local document."""
    comparisons, out = 0, []
    for d in local_docs:
        matches = []
        for f in foreign_docs:
            comparisons += 1
            if f[foreign_field] == d[local_field]:
                matches.append(f)
        out.append({**d, as_field: matches})
    return out, comparisons

def lookup_indexed(local_docs, foreign_docs, local_field, foreign_field, as_field):
    """With an index: build it once, then each lookup is a single probe."""
    index = {}
    for f in foreign_docs:
        index.setdefault(f[foreign_field], []).append(f)
    out = [{**d, as_field: index.get(d[local_field], [])} for d in local_docs]
    return out, len(local_docs)

joined_a, cost_a = lookup_scan(orders, customers, "customer_id", "_id", "customer")
joined_b, cost_b = lookup_indexed(orders, customers, "customer_id", "_id", "customer")
print("same result either way:", joined_a == joined_b)
print("lookup without index:", f"{cost_a:,}", "comparisons")
print("lookup with index   :", f"{cost_b:,}", "probes")

big = [o for o in orders if o["total"] >= 58]                    # $match first ...
_, cost_c = lookup_scan(big, customers, "customer_id", "_id", "customer")
print("filter first, then scan-lookup:", f"{cost_c:,}", "comparisons for", len(big), "orders")

unmatched = sum(1 for d in joined_b if not d["customer"])
print("orders kept with an empty customer array (left outer join):", unmatched)
inner = [{**d, "customer": d["customer"][0]} for d in joined_b if d["customer"]]     # $unwind
print("orders left after $unwind (inner join):", len(inner))

revenue = {}
for d in inner:                                                  # $group by customer.city
    revenue[d["customer"]["city"]] = revenue.get(d["customer"]["city"], 0) + d["total"]
print("revenue by city:", dict(sorted(revenue.items(), key=lambda kv: -kv[1])))

def facet(docs, branches):
    return {name: branch(docs) for name, branch in branches.items()}     # every branch sees the same input

def bands(docs, bounds=(0, 20, 40, 61)):
    return [{"_id": lo, "count": sum(lo <= d["total"] < hi for d in docs)} for lo, hi in zip(bounds, bounds[1:])]

print(facet(inner, {
    "orders": lambda docs: len(docs),
    "price_bands": bands,
    "stats": lambda docs: {"avg": round(sum(d["total"] for d in docs) / len(docs), 2), "max": max(d["total"] for d in docs)},
}))
```

Reading the output:

- Both join implementations return identical results. The scanning version needs two million comparisons (2,000 orders times 1,000 customers); the indexed version needs 2,000 probes. That factor of 1,000 is the difference an index on `foreignField` makes.
- Filtering to the large orders first cuts the scanning join to well under a hundred thousand comparisons, even without an index. Fewer documents entering the `$lookup` means fewer searches.
- About a hundred orders refer to customers that do not exist. The left outer join keeps them with an empty array; after the unwind they are gone.
- The facet output holds three results computed from the same input: a count, three price bands and summary statistics.

## Pitfalls

- **`$lookup` without an index on the foreign field**: one collection scan per input document.
- **Forgetting the result is an array**, then reading `"$customer.city"` and getting an array of cities.
- **`$unwind` after `$lookup` silently dropping unmatched documents.**
- **Joining first and filtering afterwards.**
- **Putting the selective `$match` inside `$facet`** where no index can serve it.
- **A `$facet` or `$lookup` result exceeding 16 MB.**
- **Using `$lookup` on every request** in place of a schema that stores related data together.
- **`$out` overwriting a collection** you meant to add to; use `$merge` for that.

## Cheat sheet

| goal | stage |
|---|---|
| attach matching documents from another collection | `{ $lookup: { from, localField, foreignField, as } }` |
| filter or trim the joined documents | add `pipeline: [...]` inside `$lookup` |
| inner-join shape | `$lookup` then `{ $unwind: "$as" }` |
| keep unmatched after unwind | `{ $unwind: { path: "$as", preserveNullAndEmptyArrays: true } }` |
| several summaries at once | `{ $facet: { name: [stages], ... } }` |
| counts per value, sorted | `{ $sortByCount: "$field" }` |
| histogram | `{ $bucket: { groupBy, boundaries, default, output } }` |
| store results, replacing | `{ $out: "coll" }` |
| store results, upserting | `{ $merge: { into: "coll", whenMatched: "replace" } }` |
| inspect the plan | `db.c.explain("executionStats").aggregate([...])` |

| limit | value |
|---|---|
| memory per blocking stage | 100 MB, then temporary files |
| size of any single result document | 16 MB |

## Summary

- `$lookup` joins the current documents with another collection, attaching matches as an array; it is a left outer join, and `$unwind` afterwards gives an inner join.
- The foreign field must be indexed, and filtering should happen before the join.
- `$facet` runs several sub-pipelines over the same input and returns one document; its branches cannot use indexes, so filter before it.
- `$bucket` and `$sortByCount` are convenient grouping shortcuts; `$out` and `$merge` store results for later, giving materialised views.
- For speed: `$match` and `$sort` first so they use indexes, `$limit` right after `$sort`, joins late, and watch the 100 MB per-stage memory limit. Verify with explain.

## Glossary

- **Join** - combining documents from two collections by matching values.
- **Reference** - a field holding the identity of a document in another collection.
- **`$lookup`** - the pipeline stage that performs a join.
- **Left outer join** - a join that keeps every left-hand document, matched or not.
- **Inner join** - a join that keeps only matched pairs.
- **`$facet`** - a stage running several sub-pipelines on the same input.
- **`$bucket`** - a stage grouping documents into ranges defined by boundaries.
- **`$out` / `$merge`** - final stages that write pipeline results to a collection.
- **Materialised view** - a stored, precomputed query result.
- **Blocking stage** - a stage that must receive all its input before emitting output, such as `$group`.
- **Optimiser** - the part of the server that rearranges stages when that cannot change the result.

## Check yourself

```quiz
[
  {"q": "What does the field named by as contain after a $lookup?",
   "options": ["A single document, or null", "An array of the matching documents, possibly empty", "The number of matches", "The _id of the first match"],
   "answer": 1,
   "explain": "$lookup always produces an array, because several foreign documents may match."},
  {"q": "An order refers to a customer that does not exist. What does $lookup output for it?",
   "options": ["Nothing; the order is dropped", "The order with an empty array", "An error", "The order with a null field"],
   "answer": 1,
   "explain": "$lookup is a left outer join: unmatched left-hand documents are kept with an empty array."},
  {"q": "Which combination behaves like an inner join?",
   "options": ["$lookup alone", "$lookup followed by $unwind on the joined array", "$facet followed by $lookup", "$match followed by $limit"],
   "answer": 1,
   "explain": "A plain $unwind drops documents whose array is empty, removing the unmatched rows."},
  {"q": "A pipeline runs $lookup into a collection of 2 million documents with no index on the foreign field. What happens for each input document?",
   "options": ["One index probe", "A full scan of the 2 million documents", "Nothing; results are cached", "The pipeline is rejected"],
   "answer": 1,
   "explain": "Without an index every lookup is a collection scan, so the cost multiplies."},
  {"q": "Where should a selective $match go relative to $facet?",
   "options": ["Inside each facet branch", "Before the $facet stage", "After the $facet stage", "It does not matter"],
   "answer": 1,
   "explain": "Facet branches read a stream and cannot use indexes; a leading $match can."},
  {"q": "Why is $sort immediately followed by $limit efficient?",
   "options": ["The server keeps only the top N documents in memory while scanning", "The limit is ignored", "Sorting is skipped", "It forces an index build"],
   "answer": 0,
   "explain": "The two stages are combined into a top-N sort, avoiding a full sort of all input."},
  {"q": "Which stage would you use to refresh a summary collection every hour, updating existing rows and adding new ones?",
   "options": ["$out", "$merge", "$facet", "$unwind"],
   "answer": 1,
   "explain": "$merge upserts into an existing collection; $out replaces the whole collection."},
  {"q": "What is a sign that a schema relies too heavily on $lookup?",
   "options": ["A report that runs once a night uses it", "The most frequent read in the application needs a $lookup on every request", "The collection has an _id index", "Documents contain arrays"],
   "answer": 1,
   "explain": "Data that is always read together is usually better embedded or partly duplicated than joined on every request."}
]
```

> **Source:** MongoDB: The Definitive Guide 3e, ch. 7 (topics only; wording and examples are original). MongoDB Manual: https://www.mongodb.com/docs/manual/reference/operator/aggregation/lookup/ , https://www.mongodb.com/docs/manual/reference/operator/aggregation/facet/ , https://www.mongodb.com/docs/manual/core/aggregation-pipeline-optimization/ , https://www.mongodb.com/docs/manual/core/aggregation-pipeline-limits/
