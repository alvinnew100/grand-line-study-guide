# Update operators, arrays and upserts

> **Before this lesson:** you should be able to insert and delete documents and know what a filter is ([Inserting, deleting and write concern](#/lesson/mongodb/insert-delete)), and know the BSON value types including arrays and embedded documents ([BSON types, ObjectId and the shell](#/lesson/mongodb/bson-shell)).

## In plain words

Changing stored data can be done in two ways. Imagine a paper form in a filing cabinet with one wrong phone number on it. You could throw the whole form away and write a fresh one, or you could cross out the one number and write the new one above it. The second way is quicker, and it is safer when a colleague might be correcting a different box on the same form at the same moment.

MongoDB offers both. **Replacing** swaps the whole document for a new one. **Updating with operators** sends a small instruction such as "add 1 to `visits`" or "append this to the list", and the server applies that change to the stored document. An **operator** here is a keyword starting with a dollar sign, such as `$set` or `$inc`, that names the kind of change.

There is also a third behaviour, the **upsert**: "update the document if it exists, otherwise create it". The name is a blend of *update* and *insert*.

Why it matters for a job: almost every feature of an application ends in an update - a like counter, a shopping basket, a profile edit. Using the right operator avoids a whole family of bugs in which two users' changes overwrite each other, and interviewers like to probe exactly that.

## The shape of an update

Every update method takes at least two arguments:

```javascript
db.collection.updateOne( <filter>, <update>, <options> )
```

- The **filter** selects which document to change, exactly like the filter of a delete.
- The **update** document says what to change.
- The optional third argument holds options such as `upsert`.

There are three methods. `updateOne` changes the first matching document, `updateMany` changes all matching documents, and `replaceOne` swaps the first matching document for a new one.

Start with the smallest example. A gym keeps one document per member:

```javascript
gym> db.members.insertOne({ _id: 7, name: "Dara", plan: "basic", visits: 3 })

gym> db.members.updateOne({ _id: 7 }, { $set: { plan: "premium" } })
{ acknowledged: true, matchedCount: 1, modifiedCount: 1, upsertedId: null, upsertedCount: 0 }

gym> db.members.findOne({ _id: 7 })
{ _id: 7, name: 'Dara', plan: 'premium', visits: 3 }
```

- The filter `{ _id: 7 }` picks Dara's document.
- `{ $set: { plan: "premium" } }` reads "set the field `plan` to `"premium"`". Fields that are not mentioned (`name`, `visits`) are left untouched.
- `matchedCount: 1` says the filter found one document. `modifiedCount: 1` says it was actually changed. Run the same command again and you get `matchedCount: 1, modifiedCount: 0`, because the value is already `"premium"`.

> [!WARNING]
> An update document must consist of operators. Writing `db.members.updateOne({ _id: 7 }, { plan: "premium" })` - forgetting `$set` - is rejected by modern shells and drivers, precisely because in the past it silently replaced the whole document with `{ plan: "premium" }` and destroyed the other fields. If you do want a wholesale swap, say so explicitly with `replaceOne`.

## Field operators

| operator | what it does | example |
|---|---|---|
| `$set` | assigns a value; creates the field if absent | `{ $set: { plan: "premium" } }` |
| `$unset` | removes the field | `{ $unset: { trial_ends: "" } }` |
| `$inc` | adds a number (negative to subtract); a missing field starts at 0 | `{ $inc: { visits: 1 } }` |
| `$mul` | multiplies | `{ $mul: { price: 1.1 } }` |
| `$min` / `$max` | assigns only if the new value is smaller / larger than the current one | `{ $max: { best_lift_kg: 95 } }` |
| `$rename` | changes a field's name | `{ $rename: { plan: "tier" } }` |
| `$currentDate` | assigns the server's current time | `{ $currentDate: { updated_at: true } }` |

Several operators can be combined in one update, and one operator can touch several fields:

```javascript
gym> db.members.updateOne(
...   { _id: 7 },
...   { $inc: { visits: 1 }, $set: { last_visit: new Date(), "locker.number": 42 }, $unset: { trial_ends: "" } }
... )
```

Three things happen to the one document in a single step: `visits` goes up by one, two fields are set, and `trial_ends` is removed. The value after `$unset` is ignored; an empty string is the usual placeholder.

Notice `"locker.number"`. This is **dot notation**: it reaches the field `number` inside the embedded document `locker`. If `locker` does not exist yet, MongoDB creates it. The quotes are needed because of the dot.

One rule to remember: within one update, the same field may not be changed by two operators. `{ $set: { visits: 0 }, $inc: { visits: 1 } }` is refused as a conflict.

### Why `$inc` beats read-then-write

A newcomer often writes a counter like this in application code: read the document, add one to the number, write the new number back. That works when one user is active. With two users acting at the same moment, both may read 3, both compute 4, and both write 4. One visit has vanished. This is called a **lost update**.

`$inc` does not have the problem. The client never sees the old value; it sends "add one", and the server applies each such instruction one after the other. An update to a single document is **atomic**: it happens completely or not at all, and no other operation can observe it half-done or squeeze in between its read and its write.

## Array operators

Arrays have their own vocabulary. Suppose each member has a list of booked classes:

```javascript
{ _id: 7, name: "Dara", classes: ["yoga", "spin"] }
```

| operator | what it does |
|---|---|
| `$push` | appends a value to the array (creating the array if absent) |
| `$addToSet` | appends only if an equal value is not already present |
| `$pull` | removes every element matching a value or condition |
| `$pop` | removes the last element (`1`) or the first (`-1`) |
| `$each` | modifier: apply `$push` / `$addToSet` to several values |
| `$slice` | modifier for `$push`: keep only the first or last N elements afterwards |
| `$sort` | modifier for `$push`: sort the array after pushing |

```javascript
gym> db.members.updateOne({ _id: 7 }, { $push: { classes: "boxing" } })
// classes: ["yoga", "spin", "boxing"]

gym> db.members.updateOne({ _id: 7 }, { $addToSet: { classes: "yoga" } })
// classes unchanged: "yoga" is already there; modifiedCount is 0

gym> db.members.updateOne({ _id: 7 }, { $pull: { classes: "spin" } })
// classes: ["yoga", "boxing"]

gym> db.members.updateOne({ _id: 7 }, { $push: { classes: { $each: ["pilates", "hiit"] } } })
// classes: ["yoga", "boxing", "pilates", "hiit"]
```

Without `$each`, pushing `["pilates", "hiit"]` would append one element that is itself an array. That surprise catches almost everybody once.

A powerful combination keeps a list at a fixed length, for instance "the five most recent check-ins":

```javascript
gym> db.members.updateOne(
...   { _id: 7 },
...   { $push: { recent: { $each: [ { at: new Date(), door: "north" } ], $sort: { at: -1 }, $slice: 5 } } }
... )
```

Read it inside out: push one check-in, sort the array by `at` descending (`-1` means newest first), then keep the first five. The array can never grow without bound, which protects the 16 MB document limit.

### Changing one element inside an array

Now suppose the array holds documents:

```javascript
{ _id: 7, name: "Dara",
  bookings: [ { class: "yoga", day: "Mon", paid: false },
              { class: "spin", day: "Wed", paid: false } ] }
```

How do you mark the spin booking as paid? There are three tools.

**By position.** Array positions count from zero, and a position can be used in dot notation: `{ $set: { "bookings.1.paid": true } }` changes the second element. This is fragile, because you must already know the position.

**The positional operator `$`.** Put the condition in the filter and write `$` where the position would go. It stands for "the first element that matched the filter":

```javascript
gym> db.members.updateOne(
...   { _id: 7, "bookings.class": "spin" },
...   { $set: { "bookings.$.paid": true } }
... )
```

**Array filters.** To change *every* element meeting a condition, name a placeholder in square brackets and define it in the options:

```javascript
gym> db.members.updateOne(
...   { _id: 7 },
...   { $set: { "bookings.$[b].paid": true } },
...   { arrayFilters: [ { "b.day": "Mon" } ] }
... )
```

`$[b]` means "each element, call it `b`, for which the array filter holds"; here, every Monday booking. The form `$[]` with empty brackets means "every element".

## Upserts

A page-view counter illustrates the need. For each visit you want to add one to the counter for that page, but for a page never seen before no document exists yet. Checking first and then inserting takes two round trips and has a gap between them in which another visitor can do the same, leaving two documents for one page.

An **upsert** closes the gap. Add `{ upsert: true }` as the third argument:

```javascript
web> db.pageviews.updateOne({ path: "/pricing" }, { $inc: { views: 1 } }, { upsert: true })
{ acknowledged: true, matchedCount: 0, modifiedCount: 0, upsertedId: ObjectId("6803c1..."), upsertedCount: 1 }

web> db.pageviews.updateOne({ path: "/pricing" }, { $inc: { views: 1 } }, { upsert: true })
{ acknowledged: true, matchedCount: 1, modifiedCount: 1, upsertedId: null, upsertedCount: 0 }

web> db.pageviews.findOne({ path: "/pricing" })
{ _id: ObjectId("6803c1..."), path: '/pricing', views: 2 }
```

The first call found nothing, so it created a document. Look at how that document was built: MongoDB started from the **equality fields of the filter** (`path: "/pricing"`) and then applied the update (`$inc` on a missing field starts from 0, giving `views: 1`). The second call found the document and incremented it.

Sometimes a field should be written only at creation. `$setOnInsert` does that:

```javascript
web> db.pageviews.updateOne(
...   { path: "/docs" },
...   { $inc: { views: 1 }, $setOnInsert: { first_seen: new Date() } },
...   { upsert: true }
... )
```

`first_seen` is set when the document is created and ignored on every later update.

> [!TIP]
> Two upserts for the same new key arriving at the same instant can still both insert, unless a **unique index** (a rule that forbids two documents with the same value in a field, see module 4) exists on the filter field. With a unique index on `path`, one insert wins, and the other fails with a duplicate key error and is retried by the driver as an ordinary update. Always pair upserts with a unique index on the fields in the filter.

## Getting the document back: findOneAndUpdate

`updateOne` tells you counts, not contents. When you need the document itself, for example to claim the next job in a queue, use `findOneAndUpdate`. It finds, changes and returns one document as a single atomic step:

```javascript
queue> db.jobs.findOneAndUpdate(
...   { status: "waiting" },
...   { $set: { status: "running", worker: "w-3" } },
...   { sort: { priority: -1 }, returnDocument: "after" }
... )
{ _id: 12, task: 'resize images', priority: 9, status: 'running', worker: 'w-3' }
```

The `sort` option picks the highest-priority waiting job; `returnDocument: "after"` returns the document as it looks after the change (the default is the version *before* the change). Because the step is atomic, two workers can never be handed the same job. `findOneAndDelete` and `findOneAndReplace` work the same way.

> [!INTERVIEW]
> **"Two requests decrement the stock of the same product at the same time. How do you prevent overselling?"** Put the condition and the change in one atomic update: `updateOne({ _id: sku, stock: { $gte: 1 } }, { $inc: { stock: -1 } })`. The filter only matches while stock remains, and the server applies the updates one after the other. If `modifiedCount` comes back 0, the item was sold out. No transaction and no application-level lock is needed, because a single-document update is atomic. Reading the stock, checking it in code and writing it back is the wrong answer: it has a race between the read and the write.

## The same from Python

```python
from pymongo import MongoClient, ReturnDocument

db = MongoClient()["gym"]

r = db.members.update_one({"_id": 7}, {"$inc": {"visits": 1}, "$set": {"locker.number": 42}})   # 1
print(r.matched_count, r.modified_count)                                                       # 2

db.members.update_many({"plan": "basic"}, {"$mul": {"fee": 1.05}})                             # 3

r = db.pageviews.update_one({"path": "/pricing"}, {"$inc": {"views": 1}}, upsert=True)         # 4
print(r.upserted_id)                                                                           # 5

job = db.jobs.find_one_and_update(                                                             # 6
    {"status": "waiting"},
    {"$set": {"status": "running"}},
    sort=[("priority", -1)],
    return_document=ReturnDocument.AFTER,
)
print(job["status"] if job else "queue empty")                                                 # 7
```

1. Operator names are ordinary dictionary keys in Python and must be quoted.
2. Prints `1 1` when the member exists.
3. `update_many` raises the fee of every basic-plan member by five per cent.
4. `upsert=True` is a keyword argument.
5. Prints the new `_id` if a document was created, or `None` if an existing one was updated.
6. The sort is given as a list of `(field, direction)` pairs.
7. `find_one_and_update` returns `None` when nothing matched, so the code checks before using the result.

## Simulate it yourself

The first part implements a handful of operators on plain dictionaries so you can watch each one work. The second part stages a lost update and shows why sending an instruction is safer than sending a value.

```python-run
import copy

def apply_update(doc, update):
    """Apply a small subset of MongoDB update operators to one dict (top-level fields only)."""
    doc = copy.deepcopy(doc)
    for op, changes in update.items():
        for field, value in changes.items():
            if op == "$set":
                doc[field] = value
            elif op == "$unset":
                doc.pop(field, None)
            elif op == "$inc":
                doc[field] = doc.get(field, 0) + value
            elif op == "$push":
                doc.setdefault(field, []).append(value)
            elif op == "$addToSet":
                if value not in doc.setdefault(field, []):
                    doc[field].append(value)
            elif op == "$pull":
                doc[field] = [x for x in doc.get(field, []) if x != value]
            else:
                raise ValueError("unsupported operator " + op)
    return doc

member = {"_id": 7, "name": "Dara", "plan": "basic", "visits": 3, "classes": ["yoga", "spin"]}
steps = [
    {"$set": {"plan": "premium"}},
    {"$inc": {"visits": 1, "guest_passes": 2}},
    {"$push": {"classes": "boxing"}},
    {"$addToSet": {"classes": "yoga"}},
    {"$pull": {"classes": "spin"}},
    {"$unset": {"guest_passes": ""}},
]
for step in steps:
    after = apply_update(member, step)
    print(step, "->", "changed" if after != member else "no change")
    member = after
print("final:", member)

print()
# --- lost update ----------------------------------------------------------
store = {"visits": 3}

# Two clients read at the same moment, each computes a new value, each writes it back.
seen_by_a = store["visits"]
seen_by_b = store["visits"]
store["visits"] = seen_by_a + 1        # client A writes 4
store["visits"] = seen_by_b + 1        # client B writes 4 as well, overwriting A
print("read-modify-write, two clients:", store["visits"], "(one visit lost)")

store = {"visits": 3}
for client in ("A", "B"):              # each client sends the instruction, not the value
    store = apply_update(store, {"$inc": {"visits": 1}})
print("$inc sent by two clients     :", store["visits"])

# --- upsert ---------------------------------------------------------------
pageviews = []
def upsert_inc(path):
    for d in pageviews:
        if d["path"] == path:
            d["views"] += 1
            return "updated"
    pageviews.append({"path": path, "views": 1, "first_seen": len(pageviews) + 1})
    return "inserted"

print([upsert_inc(p) for p in ["/pricing", "/docs", "/pricing", "/pricing"]], pageviews)
```

Reading the output:

- Each step prints whether the document changed. The `$addToSet` of `"yoga"` reports "no change" because the value was already present: that is the situation in which the real server returns `modifiedCount: 0`.
- In the lost-update part, both clients read 3, so the counter ends at 4 although two visits happened. With `$inc` it ends at 5.
- The upsert part prints `inserted, inserted, updated, updated`, and `first_seen` keeps the value from the moment of creation, as `$setOnInsert` would.

## Pitfalls

- **Forgetting the operator** and replacing a document by accident. Use `replaceOne` only on purpose.
- **Pushing an array without `$each`**, which nests it as one element.
- **Unbounded `$push`.** An array that grows forever slows every update and eventually hits 16 MB. Cap it with `$slice` or move the items to their own collection.
- **`updateOne` when you meant `updateMany`.** Only the first match is changed; check `matchedCount`.
- **`$` updating only the first matching element.** Use `$[]` or array filters for all of them.
- **Read-modify-write counters.** Use `$inc`, or put the expected old value in the filter.
- **Upserts without a unique index**, which can create duplicates under concurrency.
- **Upsert with a range filter.** A condition such as `{ score: { $gt: 50 } }` contributes no field to the new document, only equality conditions do.

## Cheat sheet

| goal | update document |
|---|---|
| change or add a field | `{ $set: { f: v } }` |
| remove a field | `{ $unset: { f: "" } }` |
| counter | `{ $inc: { n: 1 } }` |
| keep the highest value seen | `{ $max: { best: v } }` |
| append to a list | `{ $push: { arr: v } }` |
| append several | `{ $push: { arr: { $each: [a, b] } } }` |
| append unless present | `{ $addToSet: { arr: v } }` |
| remove from a list | `{ $pull: { arr: v } }` |
| keep the newest N | `{ $push: { arr: { $each: [v], $sort: { at: -1 }, $slice: N } } }` |
| first matching element | filter on the element, then `"arr.$.field"` |
| all matching elements | `"arr.$[x].field"` with `arrayFilters: [ { "x.k": v } ]` |
| create if missing | third argument `{ upsert: true }`, plus `$setOnInsert` for creation-only fields |

## Summary

- Updates take a filter and an update document made of operators; `replaceOne` swaps the whole document.
- `$set`, `$unset`, `$inc`, `$mul`, `$min`, `$max` and `$rename` change fields; dot notation reaches into embedded documents.
- `$push`, `$addToSet`, `$pull` and `$pop` change arrays; `$each`, `$sort` and `$slice` refine `$push`; `$`, `$[]` and `$[name]` address elements.
- A single-document update is atomic, so operators such as `$inc` avoid lost updates that read-modify-write code suffers from.
- An upsert creates the document from the filter's equality fields plus the update when nothing matches; pair it with a unique index.
- `findOneAndUpdate` changes a document and returns it in one atomic step.

## Glossary

- **Operator** - a keyword starting with `$` that names a kind of change or comparison.
- **Replace** - swap an entire document for a new one, keeping only `_id`.
- **Atomic** - happening completely or not at all, with no visible intermediate state.
- **Lost update** - a change that disappears because another client overwrote it using stale data.
- **Dot notation** - a path such as `"locker.number"` or `"bookings.1.paid"` that reaches inside embedded documents and arrays.
- **Positional operator (`$`)** - a placeholder for the position of the first array element matched by the filter.
- **Array filter** - a condition, named in `arrayFilters`, selecting which array elements an update touches.
- **Upsert** - an update that inserts a new document when no document matches the filter.
- **`$setOnInsert`** - an operator whose fields are written only when an upsert creates a document.
- **Unique index** - a rule that prevents two documents from holding the same value in the indexed field.

## Check yourself

```quiz
[
  {"q": "What does db.members.updateOne({_id: 7}, {$set: {plan: \"premium\"}}) do to the other fields of the document?",
   "options": ["Deletes them", "Leaves them unchanged", "Sets them to null", "Copies them into a new document"],
   "answer": 1,
   "explain": "$set changes only the fields it names; everything else stays as it was."},
  {"q": "The array classes is [\"yoga\"]. What is it after {$push: {classes: [\"spin\", \"hiit\"]}}?",
   "options": ["[\"yoga\", \"spin\", \"hiit\"]", "[\"yoga\", [\"spin\", \"hiit\"]]", "[[\"spin\", \"hiit\"]]", "An error is raised"],
   "answer": 1,
   "explain": "Without $each the whole array is appended as a single element."},
  {"q": "Why is {$inc: {visits: 1}} safer than reading visits, adding one in the application and writing it back?",
   "options": ["$inc is faster to type", "The server applies each $inc atomically, so concurrent increments cannot overwrite each other", "$inc bypasses the write concern", "Reading a document locks it for the reader"],
   "answer": 1,
   "explain": "Two clients doing read-modify-write can both read the same old value; $inc sends the change itself."},
  {"q": "An upsert with filter {path: \"/docs\"} and update {$inc: {views: 1}} finds no document. What is inserted?",
   "options": ["{views: 1}", "{path: \"/docs\"}", "{path: \"/docs\", views: 1} plus a generated _id", "Nothing"],
   "answer": 2,
   "explain": "The new document starts from the filter's equality fields, then the update is applied; $inc on a missing field starts from 0."},
  {"q": "Which operator writes a field only when an upsert creates the document?",
   "options": ["$set", "$setOnInsert", "$addToSet", "$currentDate"],
   "answer": 1,
   "explain": "$setOnInsert is ignored when an existing document is updated."},
  {"q": "In {\\$set: {\"bookings.\\$.paid\": true}}, what does \\$ refer to?",
   "options": ["Every element of bookings", "The last element of bookings", "The first element of bookings matched by the filter", "The document's _id"],
   "answer": 2,
   "explain": "The positional operator stands for the position of the first array element that satisfied the filter."},
  {"q": "updateOne returns matchedCount: 1 and modifiedCount: 0. What happened?",
   "options": ["The update failed", "The document was found but already had the requested values", "The document was deleted", "The filter matched nothing"],
   "answer": 1,
   "explain": "A document matched, but applying the update produced no change, so nothing was written."},
  {"q": "Why should an upsert be backed by a unique index on the filter field?",
   "options": ["Upserts do not work without one", "Otherwise two simultaneous upserts for the same new key can each insert a document", "It makes $inc atomic", "It removes the 16 MB limit"],
   "answer": 1,
   "explain": "Both may find nothing and both insert; a unique index makes one of them fail and retry as an update."}
]
```

> **Source:** MongoDB: The Definitive Guide 3e, ch. 3 (topics only; wording and examples are original). MongoDB Manual: https://www.mongodb.com/docs/manual/reference/operator/update/ , https://www.mongodb.com/docs/manual/reference/method/db.collection.updateOne/ , https://www.mongodb.com/docs/manual/reference/method/db.collection.findOneAndUpdate/
