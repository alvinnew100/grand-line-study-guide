# Choosing a shard key: ranged, hashed and zoned

> **Before this lesson:** you should know the components of a sharded cluster, what chunks are, and the difference between targeted and scatter-gather queries - see [Sharded cluster components and query routing](#/lesson/mongodb/sharding-components). Hashed indexes were introduced in [Unique, partial, sparse, TTL, text, geospatial and hashed indexes](#/lesson/mongodb/special-indexes).

## In plain words

The shard key is the rule that decides which machine each document lives on. Choosing it is the most consequential decision in a sharded cluster, because it affects every write and every read from then on.

Go back to the library with four branches. Suppose the books are divided by **date of purchase**: oldest purchases in the north branch, newest in the west. Every new book goes to the west branch. Its staff are overwhelmed while the other three branches sit idle. Now suppose the books are divided by **colour of cover**: there are only six colours, so one branch ends up with all the blue books, far more than its shelves hold, and that pile cannot be subdivided. Dividing by **author's surname** works better: purchases are spread across branches, a reader wanting one author goes to one branch, and there are enough distinct surnames to subdivide the shelves finely.

Those three stories are the three properties of a shard key that this lesson is about.

Why it matters for a job: a poor shard key produces a cluster in which one shard does all the work, and until recent versions the key could not be changed without rebuilding the collection. "How would you choose a shard key for this collection?" is the standard sharding interview question.

## What a good shard key must do

Two goals pull in different directions.

1. **Spread writes and data evenly** across the shards, so that capacity added is capacity used.
2. **Keep related documents together**, so that the common queries can be targeted at one shard.

Perfectly random placement achieves the first and destroys the second. Placing everything related in one spot achieves the second and risks the first. A good key balances them for the workload at hand.

Three measurable properties predict how a candidate key will behave.

### Cardinality: how many distinct values

**Cardinality** is the number of distinct values the key can take. A chunk is a range of key values, and the smallest possible chunk holds all documents sharing one value. Documents with the same shard key value can never be separated.

So if the key is `status` with five possible values, there can be at most five chunks, however large the collection. A chunk that has grown too big but cannot be divided, because all its documents share one key value, is called a **jumbo chunk**. Jumbo chunks cannot be moved easily, and data stops being balanced.

High cardinality is necessary. It is not sufficient, as the next two properties show.

### Frequency: how evenly values occur

**Frequency** is how often each value appears. A key can have millions of distinct values and still be badly skewed. Shard a collection of orders by `customer_id` when one enormous customer places 40 per cent of all orders, and 40 per cent of the data and the writes land in one chunk on one shard. A shard receiving a disproportionate share of the load is called a **hot shard**.

### Monotonic change: do new values always increase?

A value is **monotonically increasing** if each new one is larger than all before it. Timestamps, auto-incrementing numbers and ObjectIds (whose first bytes are a timestamp) behave this way.

With ranged sharding, the chunk covering the highest values - the one ending at `MaxKey` - receives *every* insert, because every new value is larger than the last. All insert traffic therefore goes to a single shard. The cluster has many shards and the write capacity of one. This is the most common shard key mistake, and it is tempting because `_id` and `created_at` look like such natural keys.

| property | good | bad | what goes wrong |
|---|---|---|---|
| cardinality | high (many distinct values) | low | few chunks; jumbo chunks |
| frequency | even | skewed | hot shard for the popular value |
| change over time | not monotonic | always increasing | all inserts hit the last chunk |

## Ranged and hashed sharding

There are two ways to turn key values into chunks.

**Ranged sharding** divides the key's natural ordering into ranges, as in the table of the previous lesson. Documents with nearby key values sit in the same or neighbouring chunks.

```javascript
mongos> sh.shardCollection("desk.tickets", { customer_id: 1 })
```

- Strength: queries for a **range** of key values touch only the shards owning that range.
- Weakness: a monotonically increasing key creates a hot shard.

**Hashed sharding** first passes the key through a hash function, which maps each value to a number that looks random, and divides the range of *hash values* into chunks.

```javascript
mongos> sh.shardCollection("iot.events", { device_id: "hashed" })
```

- Strength: even a monotonically increasing key is spread evenly, because consecutive values hash to unrelated places.
- Weakness: neighbouring key values are scattered, so a **range** query on the key cannot be targeted and becomes scatter-gather. Equality on the key is still targeted, since the router can hash the value and look it up.

| | ranged | hashed |
|---|---|---|
| equality on the key | targeted | targeted |
| range on the key | targeted | scatter-gather |
| monotonically increasing key | hot shard | evenly spread |
| skewed frequency (one giant value) | hot shard | still a hot shard: equal values hash equally |
| low cardinality | jumbo chunks | still jumbo chunks |

The last two rows deserve emphasis: hashing fixes monotonic keys and nothing else. One customer with 40 per cent of the data is as hot under hashing as under ranges, because all of that customer's documents have the same key and so the same hash.

## Compound shard keys

Often no single field has every property. A **compound shard key** combines fields, in the same way a compound index does, and its prefix rule applies to routing: a query that supplies the *leading* field or fields of the key can be targeted.

Take events from devices, each with a `device_id` and a `ts` timestamp.

- `{ ts: 1 }` alone: monotonic, so a hot shard.
- `{ device_id: 1 }` alone: every event of a device shares one key value, so a busy device's data forms a chunk that can never be split.
- `{ device_id: 1, ts: 1 }`: the leading field spreads inserts across devices and therefore across shards; the second field gives every document a different key, so a busy device's data can be split into many chunks; and the common query "this device, last 24 hours" supplies the prefix and is targeted.

```javascript
mongos> sh.shardCollection("iot.events", { device_id: 1, ts: 1 })
mongos> db.events.find({ device_id: "d-881", ts: { $gte: ISODate("2026-06-01") } })   // targeted
mongos> db.events.find({ ts: { $gte: ISODate("2026-06-01") } })                       // scatter-gather: no prefix
```

The pattern "a well-distributed field that the queries filter on, followed by a field that adds cardinality" covers a large share of real designs. A hashed field may also be one component of a compound key (from version 4.4).

## Designing from the queries

A procedure that works in practice and in interviews:

1. **List the most frequent operations**, with rough proportions. Which fields do they filter on?
2. **Pick candidates** from the fields that appear in most of them, so those operations are targeted.
3. **Test each candidate** against the three properties: cardinality, frequency, monotonic change.
4. **Repair weaknesses**: add a second field for cardinality; hash a monotonic field if range queries on it are not needed.
5. **Accept the remaining scatter-gather queries** consciously, and confirm they are infrequent.

A multi-tenant application (one system serving many customer organisations) is the classic example. Almost every query carries `tenant_id`. A key of `{ tenant_id: 1, _id: 1 }` targets those queries, keeps each tenant's data together, and lets a large tenant be split across chunks. The risk to check is frequency: one tenant far larger than the rest.

## Zoned sharding

Sometimes you want control over where particular ranges live. **Zones** let you label shards and pin ranges of the shard key to labels.

```javascript
mongos> sh.addShardToZone("shardEU1", "EU")
mongos> sh.addShardToZone("shardUS1", "US")
mongos> sh.updateZoneKeyRange("app.users", { country: "DE", _id: MinKey }, { country: "DE", _id: MaxKey }, "EU")
```

The first two lines label shards. The third says: for the collection `app.users`, sharded on `{ country: 1, _id: 1 }`, every key from `(DE, lowest)` up to `(DE, highest)` must live on a shard in zone EU. The cluster then keeps German users' documents there.

Typical uses: **data residency** (laws requiring that certain people's data stay within a region), **locality** (keeping data near its users for speed), and **tiering** (recent data on fast, expensive hardware and old data on cheap hardware).

## Can the key be changed later?

For years the answer was no, which is why older material treats the choice as irreversible. Modern versions are more forgiving:

- **4.2** - a document's shard key *value* can be updated (the document moves to another shard if necessary).
- **4.4** - `refineCollectionShardKey` adds fields to the end of an existing key, which is the cure for jumbo chunks caused by low cardinality.
- **5.0** - `reshardCollection` changes the key entirely, rewriting the collection in the background.

Resharding a large collection takes time, extra disk space and I/O, so the choice still deserves care. But it is no longer a trap without an exit.

> [!WARNING]
> Do not shard on a field merely because it is unique or convenient. `{ _id: 1 }` with default ObjectIds and `{ created_at: 1 }` are both monotonically increasing and send every insert to one shard. If you need to shard on such a field, use `{ _id: "hashed" }` and accept that range queries on it will be scatter-gather.

> [!TIP]
> Before sharding a production collection, test the candidate key against real data. The `analyzeShardKey` command (version 7.0) reports cardinality, frequency and monotonicity for a candidate, and how many of your recent queries would have been targeted. On older versions, an aggregation with `$group` on the candidate field and a sort by count shows the frequency skew.

> [!INTERVIEW]
> **"How do you choose a shard key?"** Start from the workload: the key should appear in the most frequent queries so they are targeted. Then check three properties - high cardinality so chunks can split, even frequency so no single value creates a hot shard, and no monotonic growth so inserts do not all land on the last chunk. State the trade-off between ranged (range queries targeted, but monotonic keys are hot) and hashed (even distribution, but range queries scatter). Offer a compound key such as `{ tenant_id: 1, _id: 1 }` or `{ device_id: 1, ts: 1 }` as the usual answer, and mention that since 5.0 the key can be changed with `reshardCollection`, at a cost.

## The same from Python

```python
from pymongo import MongoClient

client = MongoClient("mongodb://router1.example.net:27017/")
admin = client["admin"]

admin.command("enableSharding", "iot")                                           # 1
client["iot"]["events"].create_index([("device_id", 1), ("ts", 1)])              # 2
admin.command("shardCollection", "iot.events", key={"device_id": 1, "ts": 1})    # 3

skew = client["iot"]["events"].aggregate([                                       # 4
    {"$group": {"_id": "$device_id", "n": {"$sum": 1}}},
    {"$sort": {"n": -1}}, {"$limit": 3},
])
print([(row["_id"], row["n"]) for row in skew])

stats = client["iot"].command("collStats", "events")                             # 5
print({name: s["count"] for name, s in stats.get("shards", {}).items()})

admin.command("refineCollectionShardKey", "iot.events",                          # 6
              key={"device_id": 1, "ts": 1, "_id": 1})
```

1. Sharding is enabled for a database through a command sent to the `admin` database.
2. The index that supports the shard key. It must exist before a non-empty collection is sharded.
3. The command behind `sh.shardCollection`.
4. A frequency check: the three devices with the most events. If the first dwarfs the others, the key has a hot value.
5. `collStats` on a sharded collection includes per-shard figures; this prints how many documents each shard holds.
6. Adds `_id` to the end of the key, increasing cardinality without rewriting the data.

## Simulate it yourself

The simulation inserts the same 20,000 events under five candidate shard keys and reports how inserts and data are distributed over four shards, how many distinct key values exist, and how a typical query is routed.

```python-run
import hashlib, random

random.seed(12)
SHARDS = 4
events = []
for i in range(20_000):
    device = "d-%03d" % (0 if random.random() < 0.35 else random.randrange(1, 200))   # one very busy device
    events.append({"_id": i, "ts": 1_000_000 + i, "device": device,
                   "level": random.choice(["info", "info", "info", "warn", "error"])})

def h(value):
    return int(hashlib.md5(str(value).encode()).hexdigest(), 16)

def split_points(keys):
    """Chunk boundaries that would give 4 equal ranges for the keys seen SO FAR."""
    ordered = sorted(set(keys))
    return [ordered[len(ordered) * q // SHARDS] for q in range(1, SHARDS)] if len(ordered) >= SHARDS else ordered[1:]

def simulate(name, key_of, hashed=False):
    first = [key_of(e) for e in events[:2000]]                 # boundaries are set from early data ...
    transform = h if hashed else (lambda v: v)
    bounds = split_points([transform(k) for k in first])
    counts = [0] * SHARDS
    for e in events[2000:]:                                    # ... then 18,000 more inserts arrive
        position = transform(key_of(e))
        counts[sum(position >= b for b in bounds)] += 1
    distinct = len({key_of(e) for e in events})
    hottest = max(counts) * 100 // sum(counts)
    print("%-26s inserts per shard %-28s hottest %3d%%   distinct key values %5d" % (name, counts, hottest, distinct))

simulate("ts (ranged)",            lambda e: e["ts"])
simulate("ts (hashed)",            lambda e: e["ts"], hashed=True)
simulate("level (ranged)",         lambda e: e["level"])
simulate("device (ranged)",        lambda e: e["device"])
simulate("device (hashed)",        lambda e: e["device"], hashed=True)
simulate("device + ts (ranged)",   lambda e: (e["device"], e["ts"]))

print()
print("largest group of documents that can never be split apart (same shard key value):")
for name, key_of in [("level", lambda e: e["level"]), ("device", lambda e: e["device"]),
                     ("device + ts", lambda e: (e["device"], e["ts"]))]:
    groups = {}
    for e in events:
        groups[key_of(e)] = groups.get(key_of(e), 0) + 1
    print("  %-12s %5d documents" % (name, max(groups.values())))

print()
print("routing of the query 'events of device d-042 in a time range':")
for key, verdict in [("ts (ranged)", "targeted by time, but that key has a hot shard"),
                     ("ts (hashed)", "scatter-gather: a hash destroys the time order"),
                     ("device (hashed)", "targeted: equality on the hashed field"),
                     ("device + ts (ranged)", "targeted: the query supplies the key's prefix, and the range narrows it further")]:
    print("  %-22s %s" % (key, verdict))
```

Reading the output:

- **`ts` ranged** sends 100 per cent of new inserts to the last shard: every new timestamp is larger than all the boundaries. This is the monotonic-key hot shard.
- **`ts` hashed** spreads the inserts almost perfectly evenly.
- **`level`** has only three distinct values, so there are at most three chunks, one shard gets nothing, and the largest unsplittable group is about 12,000 documents - a jumbo chunk in the making.
- **`device`**, ranged or hashed, is dominated by the busy device: the shard owning `d-000` receives roughly half of all inserts. Hashing does not help, because equal keys have equal hashes.
- **`device + ts`** still shows the busy device's shard as the hottest in this snapshot, but look at the second table: the largest unsplittable group is now a single document. The busy device's range can be split into many chunks and spread over several shards, which no single-field key on `device` allows.
- The routing table shows that the compound key also keeps the most common query targeted.

## Pitfalls

- **A monotonically increasing ranged key** (`_id`, timestamps): all inserts on one shard.
- **A low-cardinality key**: few chunks, jumbo chunks.
- **Ignoring frequency skew**: one giant tenant or device makes a hot shard under any scheme.
- **Hashing a key you need range queries on.**
- **Choosing the key before knowing the queries.**
- **A key that is absent from the most frequent queries**, so that they all scatter.
- **Assuming hashing cures every distribution problem.** It cures monotonic growth only.
- **Believing the key can never be changed** - or believing that changing it is free.

## Cheat sheet

| candidate key | verdict |
|---|---|
| `{ _id: 1 }` with ObjectIds | monotonic: hot shard |
| `{ _id: "hashed" }` | even writes; lookups by `_id` targeted; everything else scatters |
| `{ created_at: 1 }` | monotonic: hot shard |
| `{ status: 1 }` | low cardinality: jumbo chunks |
| `{ tenant_id: 1 }` | good routing; watch for one giant tenant; cannot split within a tenant |
| `{ tenant_id: 1, _id: 1 }` | good routing, splittable within a tenant |
| `{ device_id: 1, ts: 1 }` | good for time-series per device |
| `{ country: 1, _id: 1 }` with zones | data residency |

| command | purpose |
|---|---|
| `sh.shardCollection(ns, { f: 1 })` | ranged sharding |
| `sh.shardCollection(ns, { f: "hashed" })` | hashed sharding |
| `sh.addShardToZone(shard, zone)` / `sh.updateZoneKeyRange(...)` | zoned sharding |
| `refineCollectionShardKey` | add suffix fields to the key (4.4) |
| `reshardCollection` | change the key (5.0) |
| `analyzeShardKey` | evaluate a candidate key (7.0) |

## Summary

- The shard key must both spread load evenly and keep the data of common queries together.
- Judge candidates by cardinality (enough distinct values to split chunks), frequency (no dominant value) and monotonic change (no ever-increasing values with ranged sharding).
- Ranged sharding keeps range queries targeted but suffers hot shards with monotonic keys; hashed sharding spreads writes evenly but turns range queries into scatter-gather.
- Hashing does not fix low cardinality or skewed frequency.
- Compound keys such as `{ tenant_id: 1, _id: 1 }` combine good routing with enough cardinality to split.
- Zones pin key ranges to chosen shards for residency, locality or tiering; modern versions allow the key to be refined or the collection resharded.

## Glossary

- **Shard key** - the field or fields that decide where a document is stored.
- **Cardinality** - the number of distinct values a key takes.
- **Frequency** - how often each value of the key occurs.
- **Monotonically increasing** - each new value being larger than all previous ones.
- **Hot shard** - a shard receiving a disproportionate share of the load.
- **Jumbo chunk** - a chunk too large to move that cannot be split because its documents share one key value.
- **Ranged sharding** - chunks are ranges of the key's own values.
- **Hashed sharding** - chunks are ranges of the hash of the key.
- **Compound shard key** - a shard key made of several fields.
- **Multi-tenant** - one system serving many separate customer organisations.
- **Zone** - a label on shards to which ranges of the key can be pinned.
- **Data residency** - a requirement that data be stored within a particular region.
- **Resharding** - changing a collection's shard key by redistributing its data.

## Check yourself

```quiz
[
  {"q": "A collection is ranged-sharded on a timestamp field. Where do new inserts go?",
   "options": ["Evenly across all shards", "All to the shard owning the highest range", "To the config servers", "To a random shard"],
   "answer": 1,
   "explain": "Each new timestamp exceeds every existing boundary, so every insert lands in the last chunk: a hot shard."},
  {"q": "Which problem does hashed sharding solve?",
   "options": ["Low cardinality", "One value occurring far more often than others", "Monotonically increasing key values", "Scatter-gather range queries"],
   "answer": 2,
   "explain": "Hashing scatters consecutive values. Equal values still hash equally, and range queries become scatter-gather."},
  {"q": "A collection is sharded on status, which has five possible values. What is the consequence?",
   "options": ["At most five chunks can exist, and they may become jumbo", "Inserts fail", "Queries on status become scatter-gather", "Nothing; any field works"],
   "answer": 0,
   "explain": "Documents sharing a key value cannot be separated, so cardinality caps the number of chunks."},
  {"q": "With shard key {device_id: 1, ts: 1}, which query is targeted?",
   "options": ["find({ts: {$gte: X}})", "find({device_id: \"d-1\", ts: {$gte: X}})", "find({level: \"error\"})", "find({})"],
   "answer": 1,
   "explain": "Routing follows the prefix rule: the leading field of the compound key must be supplied."},
  {"q": "A collection is hashed on device_id and the query asks for device_id between \"d-100\" and \"d-200\". How is it routed?",
   "options": ["Targeted to one shard", "Targeted to two shards", "Scatter-gather to all shards", "It is rejected"],
   "answer": 2,
   "explain": "Hashing destroys the ordering of key values, so a range of keys maps to scattered hash values."},
  {"q": "One tenant produces 40% of all documents and the key is {tenant_id: \"hashed\"}. What happens?",
   "options": ["The data is spread evenly", "The shard holding that tenant's hash is hot, because identical keys hash identically", "The tenant's documents are split across all shards", "Hashing rejects duplicates"],
   "answer": 1,
   "explain": "Hashing cannot separate documents that share a key value; frequency skew remains."},
  {"q": "What are zones used for?",
   "options": ["Speeding up hashing", "Pinning ranges of the shard key to particular shards, for example to keep data in a region", "Replacing config servers", "Disabling the balancer"],
   "answer": 1,
   "explain": "Zones associate key ranges with labelled shards for data residency, locality or hardware tiering."},
  {"q": "Which command lets a modern cluster change a collection's shard key entirely?",
   "options": ["rs.reconfig", "reshardCollection", "sh.addShard", "compact"],
   "answer": 1,
   "explain": "reshardCollection (5.0) rewrites the collection with a new key; refineCollectionShardKey (4.4) only adds suffix fields."}
]
```

> **Source:** MongoDB: The Definitive Guide 3e, ch. 16 (topics only; wording and examples are original). MongoDB Manual: https://www.mongodb.com/docs/manual/core/sharding-choose-a-shard-key/ , https://www.mongodb.com/docs/manual/core/hashed-sharding/ , https://www.mongodb.com/docs/manual/core/zone-sharding/ , https://www.mongodb.com/docs/manual/core/sharding-reshard-a-collection/
