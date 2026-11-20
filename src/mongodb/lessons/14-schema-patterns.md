# Schema design patterns and anti-patterns

> **Before this lesson:** you should be able to reason about embedding versus referencing, cardinality and denormalisation - see [Embedding vs referencing, cardinality and normalisation trade-offs](#/lesson/mongodb/embed-vs-reference). The examples use update operators ([Update operators, arrays and upserts](#/lesson/mongodb/update-operators)) and indexes ([Single-field and compound indexes: the ESR rule](#/lesson/mongodb/index-basics)).

## In plain words

Builders do not invent a new way to make a staircase for every house. They use known solutions - a spiral stair where space is tight, a straight flight where it is not - and they know the mistakes to avoid, such as steps of uneven height. A **design pattern** is a named, proven solution to a problem that keeps coming up. An **anti-pattern** is a named, common mistake.

MongoDB schema design has its own collection of both. Each pattern in this lesson answers one recurring question: "too many tiny documents?", "one giant exception ruining a sensible design?", "the same sum computed on every page view?", "need a field from another collection on every row?", "the document shape must change but the old data is still there?".

Why it matters for a job: these names are shared vocabulary. Saying "I would use the bucket pattern with a computed total" in a design review or interview communicates a whole design in a sentence, and recognising an unbounded array in someone's schema can prevent an outage.

## The bucket pattern

**Problem.** A weather station reports the temperature every minute. One document per reading means 1,440 documents per station per day; ten thousand stations produce over five billion documents a year. Each document is tiny, yet each carries its own `_id`, its own copy of the station id and its own index entries. The indexes end up larger than the data.

**Pattern.** Group readings that belong together - same station, same hour - into one document, a **bucket**:

```javascript
{
  _id: "st-042:2026-06-01T14",
  station: "st-042",
  hour: ISODate("2026-06-01T14:00:00Z"),
  count: 3,
  sum: 62.1,
  min: 20.4, max: 21.0,
  readings: [ { m: 0, t: 20.4 }, { m: 1, t: 20.7 }, { m: 2, t: 21.0 } ]
}
```

Each new reading is one upsert that appends to the right bucket and adjusts the summaries:

```javascript
weather> db.buckets.updateOne(
...   { station: "st-042", hour: ISODate("2026-06-01T14:00:00Z"), count: { $lt: 60 } },
...   { $push: { readings: { m: 3, t: 21.3 } },
...     $inc: { count: 1, sum: 21.3 }, $min: { min: 21.3 }, $max: { max: 21.3 } },
...   { upsert: true }
... )
```

Line by line: the filter finds this station's bucket for this hour, provided it holds fewer than 60 readings. `$push` appends the reading. `$inc` raises the count and the running sum. `$min` and `$max` adjust the extremes only when the new value beats them. `upsert: true` creates the bucket when the hour's first reading arrives.

**What you gain.** Sixty times fewer documents and index entries. An hourly chart reads `sum / count` from each bucket and never opens the arrays. The array is bounded by design, at 60 entries.

**What it costs.** Changing or deleting one individual reading is clumsier, and queries for single readings must look inside arrays.

> [!TIP]
> Since version 5.0, MongoDB has **time-series collections**, created with `db.createCollection("readings", { timeseries: { timeField: "ts", metaField: "station" } })`. You insert one document per reading and the server applies bucketing internally. For plain time-series data, prefer them. The hand-made bucket pattern is still worth understanding: it explains what the server is doing, and it applies to non-time data too, such as grouping an invoice's thousands of line items into pages.

## The computed pattern

**Problem.** A cinema's page for each film shows "tickets sold" and "total revenue". Computing these by summing the screenings on every page view repeats the same arithmetic thousands of times between changes.

**Pattern.** Compute the value when the data **changes**, not when it is **read**, and store the result in the document:

```javascript
cinema> db.films.updateOne({ _id: "f17" }, { $inc: { tickets_sold: 2, revenue: 26 } })
```

This is done as part of recording the sale. The film page then reads two stored numbers.

Use it when reads greatly outnumber writes. The opposite extreme - a value changed a thousand times a second and read once a day - is better computed on demand. For expensive figures that need not be exact to the second, recompute them on a schedule with an aggregation ending in `$merge`.

The bucket above already used this pattern: `count`, `sum`, `min` and `max` are computed values.

## The subset pattern

**Problem.** A product has 4,000 reviews. The product page shows five. Embedding all 4,000 makes the product document enormous, and that large document is loaded into memory every time anyone views the product, pushing other, useful data out of RAM.

**Pattern.** Keep the frequently used **subset** in the main document and the complete set in its own collection:

```javascript
{ _id: "sku-9", name: "Trail shoe", price: 89,
  review_count: 4000, rating_avg: 4.3,
  recent_reviews: [ { user: "Ines", stars: 5, text: "Light and grippy" } /* ... 4 more */ ] }
```

Writing a review inserts into `reviews` and also updates the product, keeping only the newest five:

```javascript
shop> db.products.updateOne({ _id: "sku-9" },
...   { $push: { recent_reviews: { $each: [ newReview ], $sort: { at: -1 }, $slice: 5 } },
...     $inc: { review_count: 1 } })
```

`$each` supplies the item, `$sort` orders the array newest first, and `$slice: 5` cuts it to five. The page loads from one small document; the "all reviews" page queries the `reviews` collection.

## The extended reference pattern

**Problem.** An order references a customer by id. The order list shows the customer's name and city on every row, so every row needs a join.

**Pattern.** Next to the reference, copy the few fields that are read with it:

```javascript
{ _id: 7001, total: 48,
  customer: { _id: "c1", name: "Renata", city: "Porto" } }
```

The reference is still there for navigating to the full record; the extended part removes the join for the common read. Copy only fields that rarely change, and decide who refreshes the copies when they do. As the last lesson noted, some copies are deliberately never refreshed: an order's shipping address is a historical fact.

## The outlier pattern

**Problem.** A design that embeds a book's buyers works for 99.9 per cent of books, which sell a few hundred copies. Then one bestseller sells two million, and its document passes 16 MB. Redesigning everything around the one exception would make all the ordinary cases slower.

**Pattern.** Keep the simple design for the typical documents, and mark the rare exceptions - the **outliers** - so the application handles them differently:

```javascript
{ _id: "book-1", title: "A Quiet Almanac", buyers: ["u1", "u7", "u9"] }

{ _id: "book-2", title: "The Runaway Hit", buyers: [ /* first 1,000 */ ], has_overflow: true }
{ _id: "book-2:overflow:1", book: "book-2", buyers: [ /* next 1,000 */ ] }
```

The flag `has_overflow` tells the code to fetch the extra documents. Ordinary books need one read; only the outlier pays for more.

The cost is extra code paths that are exercised rarely and therefore need deliberate testing.

## The attribute pattern

**Problem.** Products have wildly different characteristics: shoes have sizes, laptops have RAM, paint has a finish. Users filter on any of them. An index per possible field would mean hundreds of indexes.

**Pattern.** Turn the varying fields into an array of key-value pairs and index that array once:

```javascript
{ _id: "sku-9", name: "Trail shoe",
  attrs: [ { k: "size", v: 43 }, { k: "colour", v: "moss" }, { k: "waterproof", v: true } ] }

shop> db.products.createIndex({ "attrs.k": 1, "attrs.v": 1 })
shop> db.products.find({ attrs: { $elemMatch: { k: "colour", v: "moss" } } })
```

One compound index serves a search on any attribute. `$elemMatch` makes sure key and value come from the same array element. (A wildcard index, from the special-indexes lesson, is a newer alternative for the same need.)

## The schema versioning pattern

**Problem.** Requirements change. Version 1 of a user document stored one phone number as a string; now users can have several, each with a label. A relational database would be altered in one disruptive step. A collection holding 80 million documents cannot be rewritten in an instant, and the application must keep running throughout.

**Pattern.** Add a field recording which shape the document has, and let the application understand every shape still in existence:

```javascript
{ _id: 1, name: "Aiko", phone: "555-0101" }                                    // no version field: version 1
{ _id: 2, schema_version: 2, name: "Bram", phones: [ { label: "mobile", number: "555-0188" } ] }
```

Reading code inspects `schema_version` and converts old documents to the new shape in memory. Migration then proceeds in whichever way suits the system:

- **lazily** - whenever a document is saved, it is written back in the newest shape;
- **in the background** - a script walks the collection and upgrades documents in small batches at a gentle pace;
- **both** - lazy upgrades for active documents, a background job for the rest.

No downtime is needed, because old and new shapes coexist. The price is that the reading code must handle every version until the last old document is gone.

## Validation: keeping documents honest

A flexible schema does not have to mean an unchecked one. A collection can carry a **validator**: rules the server applies to every insert and update. The usual language for the rules is **JSON Schema**, a standard vocabulary for describing the allowed shape of a document.

```javascript
shop> db.createCollection("customers", {
...   validator: { $jsonSchema: {
...     bsonType: "object",
...     required: ["email", "created"],
...     properties: {
...       email:   { bsonType: "string", pattern: "^.+@.+$" },
...       created: { bsonType: "date" },
...       tier:    { enum: ["free", "pro"] },
...       age:     { bsonType: "int", minimum: 13 }
...     }
...   } },
...   validationAction: "error"
... })
```

- `required` lists fields every document must have.
- `properties` describes individual fields: `bsonType` fixes the type, `pattern` is a regular expression the string must match, `enum` lists the permitted values, `minimum` sets a lower bound.
- Fields not mentioned are still allowed, so the schema stays open to additions.
- `validationAction: "error"` rejects violating writes. The alternative `"warn"` lets them through and records a log entry, which is useful for trying out a new rule on a live system before enforcing it.

A write that breaks a rule fails with "Document failed validation", and from version 5.0 the error explains which rule was broken. Existing documents are not checked when a validator is added; `validationLevel: "moderate"` additionally exempts already-invalid documents from being checked on update.

## Anti-patterns

These are the mistakes that performance reviews find most often.

| anti-pattern | why it hurts | remedy |
|---|---|---|
| **Unbounded arrays** | documents grow until writes slow down and the 16 MB limit is reached | reference from the child; subset or bucket pattern |
| **Bloated documents** | rarely used large fields are loaded with every read, crowding RAM | move cold fields to another collection; subset pattern |
| **Massive number of collections** | each collection and index has overhead; thousands (one per customer, one per day) strain the server | one collection with a discriminating field and an index |
| **Unnecessary indexes** | every write maintains every index | review usage with `$indexStats`, drop the unused |
| **Separating data that is read together** | `$lookup` or several queries on the hottest path | embed, or extended reference |
| **Case-insensitive regex for lookups** | `/^ada$/i` cannot use an index efficiently | store a lower-cased copy, or use a case-insensitive collation index |
| **Storing related numbers as strings, dates as text** | wrong sorting, no range queries, no TTL | use proper BSON types, enforce with a validator |

> [!WARNING]
> The unbounded array is the anti-pattern most likely to cause a real incident, because it works perfectly in testing and for months in production, and fails only when one particular document grows large - typically your most active user or most popular item, at your busiest moment. For every array in a design, write down its maximum realistic length. If the answer is "it depends on usage", give it a cap.

> [!INTERVIEW]
> **"Name some MongoDB schema design patterns."** A solid answer names four or five with a one-line use each: **bucket** (group time-series readings per device per hour to cut document and index counts), **computed** (store totals at write time when reads dominate), **subset** (embed the newest few, keep the rest in another collection), **extended reference** (copy a few display fields beside an id to avoid a join), **outlier** (flag and overflow the rare huge document), **schema versioning** (a version field so old and new shapes coexist during migration). Then name the top anti-pattern, unbounded arrays, and its link to the 16 MB limit.

## The same from Python

```python
import datetime
from pymongo import MongoClient
from pymongo.errors import WriteError

db = MongoClient()["weather"]

def record(station, when, temp):                                              # 1
    hour = when.replace(minute=0, second=0, microsecond=0)
    db.buckets.update_one(
        {"station": station, "hour": hour, "count": {"$lt": 60}},
        {"$push": {"readings": {"m": when.minute, "t": temp}},
         "$inc": {"count": 1, "sum": temp},
         "$min": {"min": temp}, "$max": {"max": temp}},
        upsert=True)

record("st-042", datetime.datetime(2026, 6, 1, 14, 3, tzinfo=datetime.timezone.utc), 21.3)

def load_user(doc):                                                           # 2
    if doc.get("schema_version", 1) == 1:
        doc = {**doc, "schema_version": 2,
               "phones": [{"label": "main", "number": doc["phone"]}] if doc.get("phone") else []}
        doc.pop("phone", None)
    return doc

user = load_user(db.users.find_one({"_id": 1}))
db.users.replace_one({"_id": user["_id"]}, user)                              # 3

db.command("collMod", "users", validator={"$jsonSchema": {                    # 4
    "bsonType": "object", "required": ["name"],
    "properties": {"name": {"bsonType": "string", "minLength": 1}}}})
try:
    db.users.insert_one({"name": ""})
except WriteError as err:
    print(err.details["errmsg"])                                              # 5
```

1. The bucket pattern as a function: truncate the time to the hour, then upsert into that hour's bucket.
2. Schema versioning: documents with no version field are version 1 and are converted in memory to version 2.
3. Lazy migration: the upgraded document is written back, so it will not need converting again.
4. `collMod` adds a validator to an existing collection.
5. Prints `Document failed validation`: the empty name is shorter than `minLength`.

## Simulate it yourself

The simulation applies four patterns to plain Python data and measures their effect: bucket (document counts), computed (work per read), outlier (reads per item) and schema versioning (lazy migration progress).

```python-run
import random

random.seed(21)

# ---- bucket pattern -------------------------------------------------------------------
readings = [{"station": "st-%02d" % s, "ts": minute * 60, "temp": round(15 + random.random() * 10, 1)}
            for s in range(5) for minute in range(24 * 60)]            # 5 stations, one reading a minute, one day

buckets = {}
for r in readings:
    key = (r["station"], r["ts"] // 3600 * 3600)                       # station + start of the hour
    b = buckets.setdefault(key, {"count": 0, "sum": 0.0, "min": r["temp"], "max": r["temp"], "readings": []})
    b["readings"].append({"m": r["ts"] % 3600 // 60, "t": r["temp"]})
    b["count"] += 1
    b["sum"] += r["temp"]
    b["min"], b["max"] = min(b["min"], r["temp"]), max(b["max"], r["temp"])

print("one document per reading:", len(readings), "documents (and as many index entries)")
print("bucketed per station-hour:", len(buckets), "documents, largest array", max(b["count"] for b in buckets.values()))
b = buckets[("st-02", 14 * 3600)]
print("st-02 at 14:00 -> average %.2f from stored sum/count, without opening the array" % (b["sum"] / b["count"]))

# ---- computed pattern -----------------------------------------------------------------
sales = [{"film": "f%d" % random.randrange(8), "tickets": random.randint(1, 4)} for _ in range(20_000)]
totals = {}
for s in sales:                                                        # maintained at write time: one $inc per sale
    totals[s["film"]] = totals.get(s["film"], 0) + s["tickets"]
on_read = sum(s["tickets"] for s in sales if s["film"] == "f3")        # recomputed on every page view
print("film f3: computed-at-write value %d equals summed-at-read value %d;" % (totals["f3"], on_read),
      "documents touched per page view: 1 vs %d" % sum(s["film"] == "f3" for s in sales))

# ---- outlier pattern ------------------------------------------------------------------
LIMIT = 1000
buyers = {"book-%d" % i: random.randint(5, 400) for i in range(999)}
buyers["bestseller"] = 2_300_000
docs_needed = {b: 1 + (0 if n <= LIMIT else -(-(n - LIMIT) // LIMIT)) for b, n in buyers.items()}
outliers = [b for b, n in buyers.items() if n > LIMIT]
print("books needing overflow documents:", outliers, "| reads for an ordinary book: 1 | for the outlier:", docs_needed["bestseller"])

# ---- schema versioning: lazy migration ------------------------------------------------
users = [{"_id": i, "phone": "555-%04d" % i} for i in range(1000)]     # all version 1

def upgrade(doc):
    if doc.get("schema_version", 1) == 1:
        return {"_id": doc["_id"], "schema_version": 2, "phones": [{"label": "main", "number": doc["phone"]}]}
    return doc

for day in range(1, 6):
    for _ in range(300):                                               # 300 user visits a day, favouring low ids
        i = min(int(random.expovariate(1 / 150)), 999)
        users[i] = upgrade(users[i])                                   # read, convert, save back
    done = sum(u.get("schema_version", 1) == 2 for u in users)
    print("day %d: %4d of 1000 documents on version 2" % (day, done))
print("a background job upgrades the rest; meanwhile the code reads both versions")
```

Reading the output:

- **Bucket**: 7,200 reading documents become 120 bucket documents, none with more than 60 entries. The hourly average comes from two stored numbers.
- **Computed**: the stored total and the freshly summed total agree. The stored one costs reading one document; the summed one touches around 2,500.
- **Outlier**: 999 ordinary books need a single read each. Only the bestseller is flagged and spread over 2,300 documents.
- **Schema versioning**: lazy migration upgrades the active users quickly, then slows down, because rarely visiting users are rarely saved. After five days fewer than half are converted, and each day adds less than the one before. That long tail is why a background job is usually added.

## Pitfalls

- **Applying a pattern without the problem.** Patterns add complexity; use one when its problem is present.
- **Buckets without a cap**, which recreate the unbounded array.
- **Computed values updated outside the write that changes the source**, so that they drift.
- **Extended references to volatile fields.**
- **Outlier handling that is never tested**, because outliers are rare in development data.
- **Removing support for an old schema version** before confirming that no documents of that version remain.
- **Validators added late**, after bad data is already stored. They do not clean existing documents.

## Cheat sheet

| problem | pattern |
|---|---|
| billions of tiny time-stamped documents | bucket (or a time-series collection) |
| the same total recomputed on every read | computed |
| large array, only the newest few shown | subset |
| a join needed for a few display fields | extended reference |
| one in a thousand documents is huge | outlier |
| many optional, searchable fields | attribute (or a wildcard index) |
| the document shape must evolve without downtime | schema versioning |
| malformed documents creeping in | `$jsonSchema` validator |

## Summary

- Patterns are named solutions; anti-patterns are named mistakes. Both give a team a shared vocabulary.
- Bucket groups many small readings into bounded documents with precomputed summaries.
- Computed stores results at write time; subset embeds the frequently read few; extended reference copies a few fields beside an id.
- Outlier keeps the common case simple by flagging exceptions; attribute makes varied fields searchable with one index.
- Schema versioning lets old and new document shapes coexist while data is migrated lazily or in the background.
- A `$jsonSchema` validator enforces types and required fields on writes.
- The anti-patterns to hunt for first are unbounded arrays, bloated documents, too many collections and unused indexes.

## Glossary

- **Design pattern** - a named, reusable solution to a recurring problem.
- **Anti-pattern** - a named, common practice that causes problems.
- **Bucket** - a document holding a bounded group of related items, such as one hour of readings.
- **Time-series collection** - a collection type in which the server buckets time-stamped data automatically.
- **Computed pattern** - storing a derived value when its inputs change.
- **Subset pattern** - embedding a frequently used part of a large set and keeping the whole set elsewhere.
- **Extended reference** - an id accompanied by copies of a few fields from the referenced document.
- **Outlier** - a rare document far outside the typical size, handled by special-case logic.
- **Attribute pattern** - storing varied fields as an array of key-value pairs.
- **Schema versioning** - recording a document's shape version so several shapes can coexist.
- **Lazy migration** - upgrading a document to the new shape when it is next saved.
- **Validator** - rules a collection applies to every write.
- **JSON Schema** - a standard vocabulary for describing the permitted structure of a document.

## Check yourself

```quiz
[
  {"q": "Ten thousand sensors report once a minute. Which pattern reduces the number of documents and index entries?",
   "options": ["Outlier", "Bucket", "Extended reference", "Attribute"],
   "answer": 1,
   "explain": "The bucket pattern stores, for example, one document per sensor per hour with the readings inside."},
  {"q": "A film page shows total tickets sold, viewed thousands of times between sales. Which pattern fits?",
   "options": ["Computed: increment a stored total when a sale is recorded", "Subset", "Schema versioning", "Sum all sales on every page view"],
   "answer": 0,
   "explain": "When reads dominate, compute at write time and store the result."},
  {"q": "A product has 4,000 reviews but its page shows five. What does the subset pattern store in the product document?",
   "options": ["All 4,000 reviews", "The five newest reviews and a count, with all reviews in a separate collection", "Only the review ids", "Nothing about reviews"],
   "answer": 1,
   "explain": "The frequently read subset is embedded; the full set lives elsewhere."},
  {"q": "What does the outlier pattern do?",
   "options": ["Deletes unusually large documents", "Keeps the simple design for typical documents and flags rare huge ones for special handling", "Indexes every field", "Stores all documents in buckets"],
   "answer": 1,
   "explain": "A flag such as has_overflow tells the application to fetch extra documents for the exceptions only."},
  {"q": "How does schema versioning avoid downtime during a change of document shape?",
   "options": ["By locking the collection during migration", "By letting old and new shapes coexist, with a version field telling the code how to read each", "By creating a new database", "By disabling validation"],
   "answer": 1,
   "explain": "The application handles every live version, and documents are upgraded lazily or by a background job."},
  {"q": "Which is the most dangerous schema anti-pattern in practice?",
   "options": ["Using ObjectId for _id", "An array that grows without bound inside one document", "Embedding a one-to-one relationship", "Having two indexes"],
   "answer": 1,
   "explain": "Unbounded arrays slow writes as they grow and eventually exceed the 16 MB document limit."},
  {"q": "A $jsonSchema validator is added to a collection that already holds invalid documents. What happens to them?",
   "options": ["They are deleted", "They are fixed automatically", "They stay as they are; validation applies to subsequent inserts and updates", "The validator is rejected"],
   "answer": 2,
   "explain": "Validators check writes from then on and do not clean existing data."},
  {"q": "When is the computed pattern a poor choice?",
   "options": ["When the value is read far more often than it changes", "When the value changes thousands of times a second and is read once a day", "When the document is small", "When an index exists"],
   "answer": 1,
   "explain": "With writes dominating, maintaining the stored value costs more than computing it on the rare read."}
]
```

> **Source:** MongoDB: The Definitive Guide 3e, ch. 9 (topics only; wording and examples are original). MongoDB Manual: https://www.mongodb.com/docs/manual/data-modeling/design-patterns/ , https://www.mongodb.com/docs/manual/data-modeling/design-antipatterns/ , https://www.mongodb.com/docs/manual/core/schema-validation/ , https://www.mongodb.com/docs/manual/core/timeseries-collections/
