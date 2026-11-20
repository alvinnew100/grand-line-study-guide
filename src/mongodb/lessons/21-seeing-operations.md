# Seeing what the application is doing: currentOp and the profiler

> **Before this lesson:** you should be able to read explain output and know the terms collection scan, keys examined and documents examined ([Reading explain output and covered queries](#/lesson/mongodb/explain-covered)). Familiarity with replica sets ([Replica sets, members and elections](#/lesson/mongodb/replica-sets-elections)) helps but is not essential.

## In plain words

`explain` tells you how *one query you already suspect* behaves. In real life the question usually arrives the other way round: "the site is slow - which query is to blame?" You do not know yet. You need to look at what the database is doing as a whole.

Think of an air-traffic control room. One screen shows every aircraft in the air **right now**. A logbook records every flight that took **unusually long**. And a wall of dials shows the airport's **overall figures**: runways in use, fuel stocks, aircraft waiting. Controllers glance at the screen to deal with an emergency, read the logbook to find repeat offenders, and watch the dials for trends.

MongoDB offers the same three views. `currentOp` is the live screen. The **profiler** and the slow-query log are the logbook. `serverStatus` and the statistics commands are the dials.

Why it matters for a job: when a production system misbehaves, the person who can find the responsible operation in two minutes is worth a great deal. Interviewers ask "a MongoDB-backed service is suddenly slow - walk me through your investigation", and this lesson is the answer.

## The live view: currentOp

An **operation** is one piece of work the server performs for a client: a query, an insert, an index build. At any moment a busy server has many in progress. `db.currentOp()` lists them.

```javascript
shop> db.currentOp({ active: true, secs_running: { $gte: 3 } })
{
  inprog: [
    {
      opid: 48211,
      active: true,
      secs_running: 41,
      op: 'query',
      ns: 'shop.orders',
      command: { find: 'orders', filter: { note: /gift/i } },
      planSummary: 'COLLSCAN',
      client: '10.4.7.19:53122',
      appName: 'reporting-service',
      waitingForLock: false
    }
  ]
}
```

- The argument is a filter, in the usual query language, applied to the list of operations. Here: operations that are actively running and have been running for at least three seconds. Without a filter you get everything, including the server's own idle background threads.
- `opid` is the operation's identifier, needed to stop it.
- `secs_running` is how long it has been going: 41 seconds.
- `op` and `ns` say what kind of operation it is and on which namespace.
- `command` shows the operation itself. This one searches `orders` for notes containing "gift" in any letter case.
- `planSummary: 'COLLSCAN'` is the short form of the plan: a collection scan. Combined with the 41 seconds, that is the diagnosis.
- `client` and `appName` say who sent it. `appName` is a label the application supplies in its connection string; setting it in every service makes this output far more useful.
- `waitingForLock` says whether the operation is stuck waiting for something else to finish.

### Stopping an operation

```javascript
shop> db.killOp(48211)
{ info: 'attempting to kill op', ok: 1 }
```

`killOp` asks the server to stop the operation with that id. The operation ends at its next safe point and the client receives an error.

> [!WARNING]
> Kill only operations that a client sent, and only when you know what they are. The list also contains the server's internal work, such as replication threads; stopping those can harm the replica set. Killing a long write does not undo the part already applied. And killing the query does not stop the application from sending it again a second later, so find the source.

A better defence than killing operations afterwards is to stop them outliving their usefulness in the first place: give queries a `maxTimeMS`, so the server abandons them once the time is up.

### Locks, briefly

A **lock** is a marker that gives one operation temporary control of a resource so that concurrent operations do not corrupt it. MongoDB's storage engine, **WiredTiger** (the component that manages how data is held in memory and written to disk), locks at the level of individual documents for ordinary reads and writes, so they rarely block one another. A few administrative operations need a lock on a whole collection or database, such as dropping a collection or some forms of index build. If `currentOp` shows many operations with `waitingForLock: true`, look for the one long-running operation they are all queued behind.

## The logbook: the profiler

`currentOp` shows only this instant. A query that takes 800 milliseconds and runs a hundred times a minute is a serious problem that you will almost never catch on the live screen. The **database profiler** records operations as they finish, into a collection called `system.profile` in the same database.

The profiler has three levels:

| level | records |
|---|---|
| 0 | nothing (the default) |
| 1 | operations slower than a threshold, `slowms` |
| 2 | every operation |

```javascript
shop> db.setProfilingLevel(1, { slowms: 100 })
{ was: 0, slowms: 100, sampleRate: 1, ok: 1 }

shop> db.system.profile.find().sort({ ts: -1 }).limit(1)
[ {
    op: 'query',
    ns: 'shop.orders',
    command: { find: 'orders', filter: { customer_email: 'li@example.org' } },
    keysExamined: 0,
    docsExamined: 1840000,
    nreturned: 3,
    millis: 912,
    planSummary: 'COLLSCAN',
    ts: ISODate("2026-06-02T10:14:09.120Z"),
    appName: 'web-frontend'
} ]
```

- `setProfilingLevel(1, { slowms: 100 })` records operations that take longer than 100 milliseconds. The reply shows the previous settings.
- `system.profile` is an ordinary collection that you query like any other. Sorting by `ts` descending shows the most recent entry.
- The entry contains the same figures as explain's `executionStats`: here 1,840,000 documents were examined to return 3, taking 912 milliseconds, with a collection scan. An index on `customer_email` is missing.

Because the entries are documents, the aggregation framework can summarise them. This finds which query shapes consume the most time in total:

```javascript
shop> db.system.profile.aggregate([
...   { $group: { _id: { ns: "$ns", plan: "$planSummary" }, count: { $sum: 1 },
...               total_ms: { $sum: "$millis" }, worst_ms: { $max: "$millis" } } },
...   { $sort: { total_ms: -1 } },
...   { $limit: 5 }
... ])
```

Group by namespace and plan, count the occurrences, add up the time, and list the five most expensive groups. Sorting by **total** time, not by the worst single run, is deliberate: a query taking 200 milliseconds that runs 50,000 times an hour costs far more than one taking 20 seconds that runs once a day.

### The cost of profiling

The profiler writes a document for every operation it records. At level 2 on a busy server that roughly doubles the write work and can itself cause the slowness you are investigating. Three rules keep it safe:

- use level 1 with a sensible threshold in production; reserve level 2 for short diagnostic sessions or test systems;
- on very busy systems add `sampleRate`, for example `0.1`, to record a random tenth of the slow operations;
- `system.profile` is a small capped collection (1 megabyte by default), so old entries are overwritten quickly - read it soon, or enlarge it.

Profiling is set per database and per `mongod`. On a replica set, switch it on for the member you are investigating.

### The slow-query log

Even with the profiler off, MongoDB writes any operation slower than `slowms` (100 milliseconds by default) to its log file, with the same key figures. This costs almost nothing and is always on, so the log file is frequently the first place to look after an incident. Hosted services present the same information as charts and as index suggestions.

## The dials: statistics commands

Several commands report sizes and counters.

```javascript
shop> db.orders.stats({ scale: 1048576 })
{ ns: 'shop.orders', count: 1840000, size: 1420, avgObjSize: 809, storageSize: 512,
  nindexes: 4, totalIndexSize: 268, indexSizes: { _id_: 41, customer_id_1: 38, created_1: 22, note_text: 167 } }
```

- `scale: 1048576` reports sizes in megabytes (that number is the count of bytes in a megabyte).
- `count` is the number of documents; `size` the uncompressed data size; `avgObjSize` the average document size in bytes; `storageSize` the space used on disk after compression.
- `indexSizes` lists each index. Here a text index takes 167 megabytes - more than all the others together, and a candidate for review.

`db.stats()` gives the same kind of totals for a whole database.

To learn whether indexes are used at all:

```javascript
shop> db.orders.aggregate([ { $indexStats: {} } ])
[ { name: 'customer_id_1', accesses: { ops: 5120338, since: ISODate("2026-05-01T00:00:00Z") } },
  { name: 'created_1',     accesses: { ops: 0,       since: ISODate("2026-05-01T00:00:00Z") } }, ... ]
```

`$indexStats` reports, per index, how many operations have used it since the server last started. `created_1` has been used zero times in a month: it slows every write and helps nothing, so it is a candidate to drop (after checking it is not needed for some rare but important job, such as a month-end report).

`db.serverStatus()` returns hundreds of server-wide counters. A few are worth knowing by name:

| section | what it tells you |
|---|---|
| `connections` | current and available connections |
| `opcounters` | inserts, queries, updates, deletes since start |
| `wiredTiger.cache` | how full the in-memory cache is |
| `globalLock.currentQueue` | operations waiting for locks |
| `metrics.queryExecutor.scannedObjects` | documents examined in total |

Two command-line tools show the same counters as a moving table: `mongostat` (operations, connections and memory, once per second) and `mongotop` (which collections the server is spending its read and write time on).

## An investigation, start to finish

"The checkout page became slow at about ten o'clock."

1. **Is something stuck right now?** `db.currentOp({ active: true, secs_running: { $gte: 2 } })`. Look for long-running operations, collection scans and lock waits.
2. **What has been slow recently?** Read the slow-query log, or switch the profiler to level 1 and aggregate `system.profile` by total time.
3. **Why is that query slow?** Take the worst offender and run it with `explain("executionStats")`. Compare keys examined, documents examined and documents returned.
4. **Fix the cause.** Usually an index, sometimes a rewritten query or a schema change.
5. **Verify.** Run explain again; watch the entry disappear from the slow log.
6. **Prevent a repeat.** Add `maxTimeMS` to the application's queries and set an alert on the relevant dial.

> [!TIP]
> Set `appName` in every service's connection string (`...?appName=checkout-api`). It appears in `currentOp`, in the profiler and in the logs, and turns "some client at 10.4.7.19" into "the nightly export job".

> [!INTERVIEW]
> **"Production is slow. How do you find out why?"** Work from live to historical to specific. First `currentOp` filtered to active operations running longer than a few seconds, looking for collection scans, lock waits and their source via `appName` and `client`. Then the slow-query log or the profiler at level 1, aggregated by total time per query shape, to find repeat offenders. Then `explain("executionStats")` on the worst one, comparing keys examined, documents examined and documents returned. Fix with an index or query change, confirm with explain, and add `maxTimeMS` and monitoring. Mention that profiling level 2 is too expensive for a busy production server.

## The same from Python

```python
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/?appName=ops-notebook")           # 1
db = client["shop"]

running = client.admin.aggregate([                                               # 2
    {"$currentOp": {"allUsers": True, "idleConnections": False}},
    {"$match": {"active": True, "secs_running": {"$gte": 3}}},
    {"$project": {"opid": 1, "secs_running": 1, "ns": 1, "planSummary": 1, "appName": 1}},
])
for op in running:
    print(op)                                                                    # 3

db.command("profile", 1, slowms=100, sampleRate=1.0)                             # 4
worst = db["system.profile"].aggregate([
    {"$group": {"_id": {"ns": "$ns", "plan": "$planSummary"},
                "count": {"$sum": 1}, "total_ms": {"$sum": "$millis"}}},
    {"$sort": {"total_ms": -1}}, {"$limit": 5},
])
print(list(worst))                                                               # 5

unused = [ix["name"] for ix in db.orders.aggregate([{"$indexStats": {}}])
          if ix["accesses"]["ops"] == 0 and ix["name"] != "_id_"]                 # 6
print("never used since restart:", unused)
db.command("profile", 0)                                                         # 7
```

1. The `appName` labels everything this script does.
2. `$currentOp` is the aggregation-stage form of `currentOp`. It must be run on the `admin` database and can be followed by ordinary stages.
3. Prints one compact document per long-running operation.
4. The `profile` command is what `db.setProfilingLevel` calls.
5. The five most time-consuming groups of slow operations.
6. Index names with zero recorded uses, leaving out the mandatory `_id_` index.
7. Switches profiling off again. Always leave the server as you found it.

## Simulate it yourself

The simulation generates a morning of operations for a small server, then answers the three questions of this lesson: what is running now, what was slow, and where the total time goes.

```python-run
import random

random.seed(31)
SHAPES = {                                  # query shape -> (plan, typical ms, runs)
    "orders by customer_id":   ("IXSCAN",   4,    9000),
    "orders by email":         ("COLLSCAN", 900,  140),
    "product by sku":          ("IXSCAN",   2,    20000),
    "search notes /gift/i":    ("COLLSCAN", 21000, 2),
    "cart update":             ("IXSCAN",   6,    7000),
    "dashboard recent orders": ("IXSCAN",   180,  2600),
}
log = []
for shape, (plan, ms, runs) in SHAPES.items():
    for _ in range(runs):
        log.append({"shape": shape, "plan": plan, "millis": max(1, int(random.gauss(ms, ms * 0.2))),
                    "start": random.uniform(0, 3600)})

# 1. currentOp: what is running at t = 1800 s and has been running for at least 3 s?
NOW = 1800
live = [op for op in log if op["start"] <= NOW <= op["start"] + op["millis"] / 1000]
print("operations in progress at t=%d: %d" % (NOW, len(live)))
for op in live:
    running = NOW - op["start"]
    if running >= 3:
        print("  LONG-RUNNING %-26s %-9s running %.0f s" % (op["shape"], op["plan"], running))

# 2. The profiler at level 1 with slowms = 100 records only slow operations.
SLOWMS = 100
profile = [op for op in log if op["millis"] > SLOWMS]
print("\noperations total: %d | recorded by the profiler (> %d ms): %d (%.1f%%)" %
      (len(log), SLOWMS, len(profile), 100 * len(profile) / len(log)))

# 3. Aggregate the profile: group by shape, sum the time.
groups = {}
for op in profile:
    g = groups.setdefault(op["shape"], {"plan": op["plan"], "count": 0, "total": 0, "worst": 0})
    g["count"] += 1
    g["total"] += op["millis"]
    g["worst"] = max(g["worst"], op["millis"])

print("\n%-26s %-9s %6s %10s %9s" % ("shape", "plan", "count", "total s", "worst ms"))
for shape, g in sorted(groups.items(), key=lambda kv: -kv[1]["total"]):
    print("%-26s %-9s %6d %10.1f %9d" % (shape, g["plan"], g["count"], g["total"] / 1000, g["worst"]))

by_worst = max(groups.items(), key=lambda kv: kv[1]["worst"])[0]
by_total = max(groups.items(), key=lambda kv: kv[1]["total"])[0]
print("\nworst single run :", by_worst)
print("most total time  :", by_total, "<- fix this one first")
```

Reading the output:

- At the chosen moment the live view shows nothing in progress, even though thousands of slow operations ran during the hour. `currentOp` is a snapshot and can miss problems entirely, which is why the logbook exists. Change `NOW` to other values and see how rarely you catch something.
- Out of roughly 38,700 operations the profiler records only the slow ones, about 7 per cent. That is the saving that makes level 1 affordable.
- Sorted by total time, the dashboard query comes first with hundreds of seconds, although each run takes under a fifth of a second. It uses an index, so it would never appear in a hunt for collection scans. The email lookup, a collection scan run 140 times, comes next.
- The note search has by far the worst single run, at over twenty seconds, but it ran twice. Ranking by the worst run would send you after the least important of the three.

## Pitfalls

- **Profiling level 2 on a busy production server.**
- **Leaving the profiler on** after an investigation.
- **Ranking by the slowest single run** instead of by total time.
- **Killing internal operations**, or killing a query without finding the application that keeps sending it.
- **Judging index usage shortly after a restart**, when the `$indexStats` counters have been reset, or dropping an index needed by a rare job.
- **Reading `system.profile` too late**, after the small capped collection has wrapped around.
- **No `appName`**, making it hard to trace operations back to a service.
- **Looking at one member of a replica set** when the slow reads are being served by another.

## Cheat sheet

| question | tool |
|---|---|
| what is running now? | `db.currentOp({ active: true, secs_running: { $gte: 3 } })` |
| stop one operation | `db.killOp(opid)` |
| what has been slow? | slow-query log; `db.setProfilingLevel(1, { slowms: 100 })` then `db.system.profile` |
| why is this query slow? | `explain("executionStats")` |
| how big is this collection and its indexes? | `db.coll.stats({ scale: 1048576 })` |
| which indexes are unused? | `db.coll.aggregate([ { $indexStats: {} } ])` |
| server-wide counters | `db.serverStatus()`, `mongostat`, `mongotop` |
| bound a query's run time | `.maxTimeMS(ms)` |

| profiler level | records | use |
|---|---|---|
| 0 | nothing | normal default |
| 1 | operations slower than `slowms` | production diagnosis |
| 2 | everything | brief sessions, test systems |

## Summary

- `currentOp` lists operations in progress with their duration, plan summary and origin; `killOp` stops one.
- The profiler records finished operations into `system.profile`; level 1 with a `slowms` threshold is the production-safe setting, and the slow-query log is always available.
- Profile entries carry the same counts as explain and can be aggregated; rank query shapes by total time, not by worst case.
- `stats`, `$indexStats` and `serverStatus` report sizes, index usage and server-wide counters.
- A sound investigation goes: live operations, recent slow operations, explain on the worst, fix, verify, prevent.
- Label connections with `appName` and bound queries with `maxTimeMS`.

## Glossary

- **Operation** - one unit of work the server performs for a client.
- **`currentOp`** - the command listing operations in progress.
- **`opid`** - the identifier of a running operation.
- **`killOp`** - the command that asks the server to stop an operation.
- **Lock** - a marker granting an operation temporary control of a resource.
- **WiredTiger** - MongoDB's storage engine, which manages data in memory and on disk.
- **Profiler** - a facility that records finished operations into `system.profile`.
- **`slowms`** - the duration above which an operation counts as slow.
- **Slow-query log** - log-file entries for operations slower than `slowms`.
- **`planSummary`** - the one-line form of a query plan, such as `COLLSCAN` or `IXSCAN { a: 1 }`.
- **`$indexStats`** - an aggregation stage reporting how often each index has been used.
- **`serverStatus`** - a command returning server-wide counters and gauges.
- **`appName`** - a label an application sets on its connections for identification.

## Check yourself

```quiz
[
  {"q": "Which tool shows operations that are in progress at this moment?",
   "options": ["The profiler", "db.currentOp()", "explain()", "db.stats()"],
   "answer": 1,
   "explain": "currentOp is a live snapshot; the profiler records operations after they finish."},
  {"q": "What does profiling level 1 with slowms: 100 record?",
   "options": ["Every operation", "Nothing", "Operations that take longer than 100 milliseconds", "Only write operations"],
   "answer": 2,
   "explain": "Level 1 records slow operations only, as defined by the slowms threshold."},
  {"q": "Why is profiling level 2 risky on a busy production server?",
   "options": ["It deletes old data", "It writes a profile document for every operation, adding substantial load", "It disables indexes", "It stops replication"],
   "answer": 1,
   "explain": "Recording everything roughly doubles write activity and can cause the slowness being investigated."},
  {"q": "Query A takes 20 s and runs once a day. Query B takes 200 ms and runs 50,000 times an hour. Which should usually be fixed first?",
   "options": ["A, because it is slowest", "B, because its total time is far greater", "Neither", "Both are equal"],
   "answer": 1,
   "explain": "B consumes 10,000 seconds of server time per hour; rank by total time, not by the worst single run."},
  {"q": "A profile entry shows docsExamined: 1840000, nreturned: 3, planSummary: COLLSCAN. What is the likely fix?",
   "options": ["Increase slowms", "Create an index on the filtered field", "Raise the profiling level", "Kill the operation"],
   "answer": 1,
   "explain": "Examining 1.8 million documents to return 3 with a collection scan is a missing-index symptom."},
  {"q": "What does $indexStats report?",
   "options": ["The size of each index", "How many operations have used each index since the server started", "Which queries are slow", "The fields of each document"],
   "answer": 1,
   "explain": "It shows usage counts per index, which reveals indexes that cost writes but serve no queries."},
  {"q": "Why is killing a slow query often only a temporary fix?",
   "options": ["killOp never works", "The application that sent it is likely to send it again", "It corrupts the collection", "It drops the index"],
   "answer": 1,
   "explain": "The cause is in the application or the missing index; maxTimeMS and a proper fix prevent recurrence."},
  {"q": "What is the purpose of setting appName in a connection string?",
   "options": ["It encrypts the connection", "It labels operations so that currentOp, the profiler and logs show which service sent them", "It selects the database", "It raises the connection limit"],
   "answer": 1,
   "explain": "The label makes it straightforward to trace an operation back to its source."}
]
```

> **Source:** MongoDB: The Definitive Guide 3e, ch. 18 (topics only; wording and examples are original). MongoDB Manual: https://www.mongodb.com/docs/manual/reference/method/db.currentOp/ , https://www.mongodb.com/docs/manual/tutorial/manage-the-database-profiler/ , https://www.mongodb.com/docs/manual/reference/operator/aggregation/indexStats/ , https://www.mongodb.com/docs/manual/reference/command/serverStatus/
