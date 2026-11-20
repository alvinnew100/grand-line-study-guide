# Unique, partial, sparse, TTL, text, geospatial and hashed indexes

> **Before this lesson:** you should understand ordinary and compound indexes ([Single-field and compound indexes: the ESR rule](#/lesson/mongodb/index-basics)) and be able to read basic explain output ([Reading explain output and covered queries](#/lesson/mongodb/explain-covered)).

## In plain words

The indexes met so far do one job: make lookups and sorts fast. MongoDB also has indexes with extra abilities, a bit like the specialised tools on a multi-tool pocket knife. Each solves one particular problem.

- A **unique** index is a bouncer with a guest list: nobody gets in under a name that is already inside.
- A **partial** index is an index of only the interesting chapters of a book.
- A **TTL** index is a "best before" date: documents past it are thrown away automatically.
- A **text** index is a search engine for words inside sentences.
- A **geospatial** index is a map that can answer "what is near here?".
- A **hashed** index is a shuffling machine that spreads values evenly.

Why it matters for a job: these features replace code you would otherwise have to write and run yourself - duplicate checks, nightly clean-up scripts, a location search service. Interviewers regularly ask "how would you make email addresses unique?", "how do you expire sessions?" and "how do you find the nearest drivers?".

## Unique indexes

An ordinary index allows any number of documents to share a value. A **unique index** refuses a write that would create a second document with the same value.

```javascript
club> db.members.createIndex({ email: 1 }, { unique: true })
email_1

club> db.members.insertOne({ name: "Pia", email: "pia@example.org" })
{ acknowledged: true, insertedId: ObjectId("...") }

club> db.members.insertOne({ name: "Another Pia", email: "pia@example.org" })
MongoServerError: E11000 duplicate key error collection: club.members index: email_1 dup key: { email: "pia@example.org" }
```

- The second argument of `createIndex` is an options document; `unique: true` switches on the guarantee.
- The first insert succeeds.
- The second is rejected with the **duplicate key error** (code 11000), and the message names the index and the offending value.

The index on `_id` that every collection has is a unique index of exactly this kind.

Why do this in the database and not in the application ("look first, insert if absent")? Because two requests can both look at the same instant, both see nothing and both insert. Only the database, which processes the two writes one after the other, can guarantee the rule.

**Compound unique indexes** make a *combination* unique. `createIndex({ club_id: 1, member_no: 1 }, { unique: true })` allows member number 12 in many clubs, but only once per club.

There is one surprise. A document that lacks the indexed field is indexed as if the field were `null`. So a unique index on `email` allows **one** document without an email, and rejects the second, because both would have the key `null`. The cure is a partial index, coming up next.

Creating a unique index on a collection that already contains duplicates fails. You must clean the data first.

## Partial indexes

A **partial index** contains entries only for documents that satisfy a filter you give when creating it.

```javascript
club> db.members.createIndex(
...   { email: 1 },
...   { unique: true, partialFilterExpression: { email: { $exists: true } } }
... )
```

`partialFilterExpression` is an ordinary query filter. Only documents that have an `email` field are indexed; those without are left out, so they cannot collide with each other. This is the standard recipe for "unique, but optional".

Partial indexes are also a way to save space and write cost. Imagine a `tasks` collection in which 98 per cent of tasks are finished and the application only ever searches the open ones:

```javascript
work> db.tasks.createIndex({ assignee: 1, due: 1 }, { partialFilterExpression: { status: "open" } })
```

The index is fifty times smaller than a full one, and completing a task removes its entry.

The price is a rule you must remember: the planner uses a partial index only when the query is **guaranteed** to stay within the indexed subset. `find({ assignee: "kim", status: "open" })` can use it. `find({ assignee: "kim" })` cannot, because the answer might include finished tasks that the index knows nothing about.

### Sparse indexes

A **sparse** index (`{ sparse: true }`) is the older, simpler relative: it skips documents that do not have the indexed field at all. A partial index with `{ field: { $exists: true } }` does the same and can express much more, so prefer partial indexes in new work. You will still meet sparse indexes in existing systems.

## TTL indexes

Some data is only useful for a while: login sessions, one-time codes, temporary caches, logs. A **TTL index** (TTL stands for *time to live*) deletes documents automatically once they reach a certain age.

```javascript
web> db.sessions.createIndex({ last_seen: 1 }, { expireAfterSeconds: 1800 })
```

Read it as: "a session document may be deleted once `last_seen` is more than 1,800 seconds (30 minutes) in the past". The field must hold a real BSON **date**. A document where the field is missing, or is a string or a number, is never deleted. If the field holds an array of dates, the earliest one decides.

A second style stores the exact moment of expiry in the document and sets the delay to zero:

```javascript
web> db.codes.createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 })
web> db.codes.insertOne({ code: "481516", expires_at: new Date(Date.now() + 10 * 60 * 1000) })
```

`Date.now()` is the current time in milliseconds; the expression adds ten minutes. Each document can now have its own lifetime.

Three properties matter in practice.

1. **Deletion is not instant.** A background task wakes up about once every 60 seconds and removes what has expired. A document can outlive its expiry by a minute, or longer on a heavily loaded server. Never rely on a TTL index for exact timing; if the application must not accept an expired code, compare the date in the query as well.
2. **Single field only.** A TTL index cannot be a compound index.
3. **Deletes are real deletes.** They cost write work like any other delete and are copied to the other members of a replica set. In a replica set only the primary runs the clean-up task.

> [!TIP]
> Updating the date field restarts the clock. A session system that sets `last_seen` to the current time on every request gets "expire 30 minutes after the last activity" with no extra code.

## Text indexes

A regular index on a string field finds exact values and prefixes. It cannot find a word in the middle of a sentence. A **text index** can. When it is built, each string is split into words, common filler words such as "the" and "and" (called **stop words**) are dropped, and each remaining word is reduced to its **stem**, a base form shared by related words: "running", "runs" and "run" all become "run". The index stores one entry per stem.

```javascript
blog> db.posts.createIndex({ title: "text", body: "text" }, { weights: { title: 5, body: 1 } })

blog> db.posts.find(
...   { $text: { $search: "sourdough starter" } },
...   { title: 1, score: { $meta: "textScore" } }
... ).sort({ score: { $meta: "textScore" } })
```

- The index type is given as the string `"text"` in place of `1`. A collection may have only one text index, but it can span several fields.
- `weights` says a match in the title counts five times as much as one in the body.
- `$text` with `$search` finds documents containing *any* of the words. Wrap a phrase in escaped quotes (`"\"sourdough starter\""`) to demand the exact phrase, and put a minus sign before a word to exclude it (`"sourdough -rye"`).
- `{ $meta: "textScore" }` asks for the relevance score, and sorting by it puts the best matches first.

Text indexes are large and slow down writes noticeably, because one document yields many entries. They have no typo tolerance and only basic ranking. For serious search - misspellings, synonyms, highlighting - MongoDB's hosted service offers Atlas Search, which is built on the Lucene search library; the built-in text index is suitable for modest needs.

## Geospatial indexes

To answer "which cafés are within 500 metres of me?" the database must understand positions on the Earth. Positions are stored in **GeoJSON**, a standard format in which a point looks like this:

```javascript
{ name: "Bean There", location: { type: "Point", coordinates: [ 24.1052, 56.9496 ] } }
```

> [!WARNING]
> GeoJSON coordinates are written **longitude first, then latitude**: `[ east-west, north-south ]`. Everyday usage and most map applications say "latitude, longitude". Swapping them is the single most common geospatial bug, and it usually fails silently by placing your point on another continent.

The index type for positions on a sphere is `2dsphere`:

```javascript
city> db.cafes.createIndex({ location: "2dsphere" })

city> db.cafes.find({
...   location: { $near: { $geometry: { type: "Point", coordinates: [ 24.1060, 56.9500 ] }, $maxDistance: 500 } }
... })
```

`$near` returns documents ordered from nearest to farthest, and `$maxDistance` (in metres) cuts the list off. Two other operators are common: `$geoWithin` finds everything inside a shape such as a polygon or a circle, without ordering, and `$geoIntersects` finds shapes that overlap a given shape, for example "which delivery zones contain this address?".

A 2dsphere index can be part of a compound index, so "open cafés near me" can use `{ location: "2dsphere", open: 1 }`. An older type, `2d`, works on a flat plane and is meant for game maps and floor plans, not for the Earth.

## Hashed indexes

A **hash function** turns any value into a number that looks random, in such a way that the same input always gives the same number and similar inputs give unrelated numbers. A **hashed index** stores the hash of the field value in place of the value.

```javascript
app> db.events.createIndex({ user_id: "hashed" })
```

Because similar values land far apart, a hashed index is useless for ranges and sorting. It supports equality lookups only. Its purpose is **sharding** (splitting a collection across machines, module 8): values that increase steadily, such as timestamps or ObjectIds, would otherwise all be written to the same machine, and hashing spreads them evenly. You will rarely create one for any other reason.

## Two more worth knowing

**Wildcard indexes.** `createIndex({ "attributes.$**": 1 })` indexes every field found under `attributes`, whatever their names. This suits documents whose keys are not known in advance, such as product specifications that differ per category. It is not a substitute for designing indexes around known queries: it supports one field per query and is larger than a targeted index.

**Capped collections.** These are not an index but appear in the same chapter of most references. A capped collection has a fixed maximum size; when it is full, the oldest documents are overwritten by new ones, like a security camera recording over old tape. It is created with `db.createCollection("log", { capped: true, size: 1048576 })`, where `size` is in bytes. For most "keep recent data" needs a TTL index is more flexible, because it expires by age, not by volume.

> [!INTERVIEW]
> **"How do you enforce uniqueness on an optional field?"** A plain unique index treats a missing field as `null`, so the second document without the field is rejected. Use a partial unique index: `{ unique: true, partialFilterExpression: { email: { $exists: true } } }` (or `{ $type: "string" }` to exclude explicit nulls as well). Then add the follow-up they are waiting for: queries must include the same condition for the planner to use a partial index, and in a sharded collection a unique index must contain the shard key.

## The same from Python

```python
import datetime
from pymongo import MongoClient, ASCENDING, GEOSPHERE, TEXT
from pymongo.errors import DuplicateKeyError

db = MongoClient()["club"]

db.members.create_index([("email", ASCENDING)], unique=True,
                        partialFilterExpression={"email": {"$exists": True}})          # 1
db.members.insert_many([{"name": "guest one"}, {"name": "guest two"}])                 # 2
try:
    db.members.insert_many([{"email": "pia@example.org"}, {"email": "pia@example.org"}])
except Exception as err:                                                               # 3
    print(type(err).__name__)

db.sessions.create_index("last_seen", expireAfterSeconds=1800)                         # 4
db.sessions.insert_one({"user": "pia", "last_seen": datetime.datetime.now(datetime.timezone.utc)})

db.cafes.create_index([("location", GEOSPHERE)])                                       # 5
here = {"type": "Point", "coordinates": [24.1060, 56.9500]}
for cafe in db.cafes.find({"location": {"$near": {"$geometry": here, "$maxDistance": 500}}}):
    print(cafe["name"])

db.posts.create_index([("title", TEXT), ("body", TEXT)], weights={"title": 5})         # 6
hits = db.posts.find({"$text": {"$search": "sourdough"}}, {"score": {"$meta": "textScore"}})
print([p["title"] for p in hits.sort([("score", {"$meta": "textScore"})])])
```

1. Options are keyword arguments. This is the "unique but optional" recipe.
2. Two members without an email are both accepted, thanks to the partial filter.
3. The second identical email is rejected. Because this was a bulk insert the exception type printed is `BulkWriteError`; with `insert_one` it would be `DuplicateKeyError`.
4. A TTL index. The date is created with an explicit UTC time zone.
5. `GEOSPHERE` is PyMongo's constant for `"2dsphere"`. The loop prints cafés within 500 metres, nearest first.
6. `TEXT` is the constant for `"text"`. The final line prints titles ordered by relevance.

## Simulate it yourself

Each block imitates one special index with a few lines of plain Python, so that the behaviour behind the option becomes visible.

```python-run
import math, hashlib

# ---- unique, with and without a partial filter ---------------------------------------
def try_inserts(docs, partial):
    keys, log = set(), []
    for d in docs:
        if partial and "email" not in d:
            log.append("stored (not indexed)")            # left out of the partial index
            continue
        key = d.get("email")                               # a missing field is indexed as None
        if key in keys:
            log.append("DUPLICATE KEY %r" % (key,))
        else:
            keys.add(key)
            log.append("stored")
    return log

people = [{"email": "pia@example.org"}, {"name": "guest one"}, {"name": "guest two"}, {"email": "pia@example.org"}]
print("plain unique  :", try_inserts(people, partial=False))
print("partial unique:", try_inserts(people, partial=True))

# ---- TTL: a sweep every 60 seconds ---------------------------------------------------
sessions = [{"user": "a", "last_seen": 0}, {"user": "b", "last_seen": 95}, {"user": "c", "last_seen": "yesterday"}]
EXPIRE_AFTER = 120
for now in range(60, 301, 60):
    expired = [s["user"] for s in sessions
               if isinstance(s["last_seen"], (int, float)) and s["last_seen"] + EXPIRE_AFTER <= now]
    sessions = [s for s in sessions if s["user"] not in expired]
    print("sweep at t=%3d deletes %s" % (now, expired))
print("never deleted:", [s["user"] for s in sessions], "(its date field is not a date)")

# ---- geospatial: nearest first, within a radius --------------------------------------
def metres(a, b):
    """Great-circle distance between two [longitude, latitude] points (haversine formula)."""
    lon1, lat1, lon2, lat2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6_371_000 * math.asin(math.sqrt(h))

cafes = {"Bean There": [24.1052, 56.9496], "Steam Room": [24.1100, 56.9520], "Far Roast": [24.1500, 56.9700]}
here = [24.1060, 56.9500]
near = sorted((round(metres(here, pos)), name) for name, pos in cafes.items())
print("within 500 m, nearest first:", [(n, d) for d, n in near if d <= 500])
swapped = [here[1], here[0]]                                   # latitude and longitude the wrong way round
print("with swapped coordinates the nearest cafe appears to be %d km away" % (min(metres(swapped, p) for p in cafes.values()) / 1000))

# ---- hashed: neighbouring values are scattered ---------------------------------------
def bucket(value, buckets=4):
    return int(hashlib.md5(str(value).encode()).hexdigest(), 16) % buckets

ids = list(range(1000, 1012))
print("ids in order      :", ids)
print("bucket by range   :", [min(3, (i - 1000) // 3) for i in ids])
print("bucket by hash    :", [bucket(i) for i in ids])
```

Reading the output:

- With a plain unique index the second guest is rejected with `DUPLICATE KEY None`: two missing emails collide. With the partial index both guests are stored and only the repeated real address is rejected.
- The TTL sweeps delete session `a` (expiry 120) at the sweep at t=120 and session `b` (expiry 215) at t=240, a full 25 seconds after it expired. Session `c`, whose "date" is a string, is never removed.
- The geospatial block lists the two cafés within 500 metres with their distances, nearest first. Swapping longitude and latitude moves the search point thousands of kilometres away.
- Consecutive ids fall into range buckets in neat blocks of three, but into hash buckets in no visible pattern. That scattering is exactly what a hashed index is for, and exactly why it cannot answer range queries.

## Pitfalls

- **Unique index on an optional field** without a partial filter: the second document lacking the field is rejected.
- **Creating a unique index over existing duplicates.** The build fails; deduplicate first.
- **Queries that do not include the partial filter condition** cannot use the partial index.
- **TTL on a non-date field**, or expecting deletion at the exact second.
- **Longitude and latitude swapped** in GeoJSON.
- **Using a text index for prefix or substring search.** It matches whole stemmed words.
- **Range queries on a hashed index.** Equality only.
- **One text index per collection**: plan which fields it covers.

## Cheat sheet

| need | index | key option |
|---|---|---|
| no two documents with the same value | unique | `{ unique: true }` |
| unique per parent | compound unique | `{ a: 1, b: 1 }, { unique: true }` |
| unique but optional | partial unique | `partialFilterExpression: { f: { $exists: true } }` |
| index only a subset | partial | `partialFilterExpression: { status: "open" }` |
| delete after N seconds | TTL | `{ expireAfterSeconds: N }` on a date field |
| delete at a stored moment | TTL | `{ expireAfterSeconds: 0 }` on an `expires_at` field |
| word search | text | `{ field: "text" }`, query with `$text` |
| nearby / inside a shape | 2dsphere | `{ location: "2dsphere" }`, query with `$near`, `$geoWithin` |
| even spread for sharding | hashed | `{ field: "hashed" }` |
| unknown field names | wildcard | `{ "path.$**": 1 }` |

## Summary

- A unique index enforces uniqueness inside the database, the only place where it can be done safely under concurrency; missing fields count as `null`.
- A partial index covers only documents matching a filter: smaller, cheaper, and the tool for unique-but-optional fields. Sparse is its older, limited form.
- A TTL index deletes documents some seconds after a date field, by a sweep that runs about once a minute.
- A text index supports word search with stemming and relevance scores, one per collection.
- A 2dsphere index answers nearness and containment questions on GeoJSON data, with longitude first.
- A hashed index scatters values for even distribution and supports equality only.

## Glossary

- **Unique index** - an index that rejects writes creating a duplicate value.
- **Duplicate key error** - error 11000, raised on a uniqueness violation.
- **Partial index** - an index containing only documents that match a filter expression.
- **Sparse index** - an index that skips documents lacking the indexed field.
- **TTL (time to live) index** - an index that causes documents to be deleted after a set age.
- **Text index** - an index of stemmed words for searching inside strings.
- **Stop word** - a very common word ignored by text search.
- **Stem** - the base form to which related words are reduced.
- **GeoJSON** - a standard format for geographic shapes; a point is `[longitude, latitude]`.
- **2dsphere index** - an index for geometry on the Earth's surface.
- **Hash function** - a function mapping values to seemingly random numbers in a repeatable way.
- **Hashed index** - an index on the hash of a field, used mainly for sharding.
- **Wildcard index** - an index over all fields beneath a path.
- **Capped collection** - a fixed-size collection that overwrites its oldest documents.

## Check yourself

```quiz
[
  {"q": "A collection has a plain unique index on email. Two documents are inserted, neither with an email field. What happens?",
   "options": ["Both are stored", "The first is stored; the second fails with a duplicate key error", "Both fail", "The index is dropped"],
   "answer": 1,
   "explain": "A missing field is indexed as null, so the second document duplicates the key null."},
  {"q": "Which index makes email unique while allowing many documents without an email?",
   "options": ["{unique: true}", "{unique: true, partialFilterExpression: {email: {$exists: true}}}", "{expireAfterSeconds: 0}", "{email: \"hashed\"}"],
   "answer": 1,
   "explain": "The partial filter leaves documents without the field out of the index, so they cannot collide."},
  {"q": "A partial index was created with partialFilterExpression: {status: \"open\"} on {assignee: 1}. Which query can use it?",
   "options": ["find({assignee: \"kim\"})", "find({assignee: \"kim\", status: \"open\"})", "find({status: \"done\"})", "find({})"],
   "answer": 1,
   "explain": "The planner uses a partial index only when the query is guaranteed to stay inside the indexed subset."},
  {"q": "A TTL index has expireAfterSeconds: 1800 on last_seen. When is a document removed?",
   "options": ["Exactly 1800 seconds after last_seen", "At the next background sweep after last_seen is more than 1800 seconds old", "When the collection is next queried", "Never, unless deleteMany is called"],
   "answer": 1,
   "explain": "A background task runs roughly every 60 seconds, so deletion can lag the expiry time."},
  {"q": "In GeoJSON, how is a point written?",
   "options": ["[latitude, longitude]", "[longitude, latitude]", "{lat: .., lng: ..}", "A string such as \"56.9N 24.1E\""],
   "answer": 1,
   "explain": "GeoJSON order is longitude first, then latitude - the reverse of everyday usage."},
  {"q": "Which query can a hashed index on user_id support?",
   "options": ["user_id greater than 500", "sort by user_id", "user_id equal to 500", "user_id starting with a prefix"],
   "answer": 2,
   "explain": "Hashing destroys ordering, so only equality lookups are possible."},
  {"q": "Why enforce uniqueness with an index instead of checking in application code first?",
   "options": ["Application code cannot read the database", "Two concurrent requests can both check, both find nothing and both insert; only the database can serialise them", "Indexes are faster to type", "Checks in code are not allowed"],
   "answer": 1,
   "explain": "Check-then-insert has a race condition; a unique index closes it."},
  {"q": "What does a text index store for the sentence \"The runners were running\"?",
   "options": ["The whole sentence as one key", "Entries for stemmed, non-stop words such as runner and run", "Every character separately", "Only the first word"],
   "answer": 1,
   "explain": "Text indexing drops stop words like 'the' and 'were' and reduces the rest to stems."}
]
```

> **Source:** MongoDB: The Definitive Guide 3e, ch. 5-6 (topics only; wording and examples are original). MongoDB Manual: https://www.mongodb.com/docs/manual/core/index-unique/ , https://www.mongodb.com/docs/manual/core/index-partial/ , https://www.mongodb.com/docs/manual/core/index-ttl/ , https://www.mongodb.com/docs/manual/core/indexes/index-types/index-text/ , https://www.mongodb.com/docs/manual/geospatial-queries/ , https://www.mongodb.com/docs/manual/core/indexes/index-types/index-hashed/
