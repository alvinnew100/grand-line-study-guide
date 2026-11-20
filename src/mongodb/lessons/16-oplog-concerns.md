# The oplog, write concern, read concern and read preference

> **Before this lesson:** you should know what a replica set, a primary, a secondary, a majority, an election and a rollback are - all from [Replica sets, members and elections](#/lesson/mongodb/replica-sets-elections). Write concern was first introduced in [Inserting, deleting and write concern](#/lesson/mongodb/insert-delete).

## In plain words

The last lesson said that secondaries "copy every write from the primary". This lesson opens the lid on how, and then covers the three dials an application can turn to trade speed against safety.

The copying works through a logbook. Imagine a ship's captain who writes every action into a log: "09:02 turned to heading 140", "09:07 raised the mainsail". An officer on a second ship, wanting to end up in exactly the same state, reads the captain's log and repeats each entry in order. MongoDB's logbook is called the **oplog** (operations log). The primary writes each change into it, and the secondaries read it and repeat the changes.

Because copying takes a moment, the copies are always a little behind. That raises three questions, and each has a setting:

- **Write concern** - when I write, how many copies must have it before I am told "done"?
- **Read concern** - when I read, how *settled* must the data be?
- **Read preference** - when I read, *which member* should answer?

Why it matters for a job: these three settings decide whether your application can lose a confirmed write or show a user data that later disappears. "Explain write concern, read concern and read preference" is asked in most interviews that touch MongoDB, usually as one question to see whether you can keep the three apart.

## The oplog

The oplog is a special collection, `oplog.rs`, in the `local` database of every member. Each document in it describes one change. Trimmed to the essentials, entries look like this:

```javascript
{ ts: Timestamp(1767430000, 1), op: "i", ns: "shop.carts", o: { _id: 7, items: 1 } }
{ ts: Timestamp(1767430004, 1), op: "u", ns: "shop.carts", o2: { _id: 7 }, o: { $set: { items: 2 } } }
{ ts: Timestamp(1767430009, 1), op: "d", ns: "shop.carts", o: { _id: 7 } }
```

- `ts` is the entry's timestamp, which also serves as its position in the log. A member's most recent `ts` is called its **optime**.
- `op` is the kind of change: `i` insert, `u` update, `d` delete (and `n` for a no-op, `c` for a command such as creating a collection).
- `ns` is the namespace: database and collection.
- `o` holds the inserted document or the modification; `o2` identifies the document an update applies to.

Replication then works like this:

1. The primary applies a write to its data and adds an entry to its oplog.
2. Each secondary keeps a query open on the oplog of the member it syncs from and receives new entries as they appear.
3. The secondary applies each entry to its own data and records it in its own oplog.

A brand-new member has nothing to repeat from, so it first performs an **initial sync**: it copies all the data from another member, then applies the oplog entries written during the copy, and from then on follows along normally.

### Entries are idempotent

Look closely at the update entry. The application may have sent `{ $inc: { items: 1 } }`, "add one". The oplog does not record "add one". It records the outcome: "set items to 2".

The reason is safety under repetition. A secondary can crash after applying an entry but before noting that it did, and on restart it will apply that entry a second time. "Add one" applied twice gives the wrong answer. "Set to 2" applied twice gives 2. An operation that gives the same result whether applied once or several times is called **idempotent**, and every oplog entry is written in an idempotent form.

### The oplog has a fixed size

The oplog is a **capped collection**: it has a maximum size, and when it is full the oldest entries are overwritten. By default it takes about 5 per cent of free disk space.

The span of time between the oldest and newest entries is the **oplog window**. It tells you how long a secondary can be offline and still catch up. If a secondary is down for three hours and the window is two hours, the entries it needs have been overwritten; it has "fallen off the oplog" and must be rebuilt with a full initial sync, which on a large data set takes hours and loads the member it copies from.

`rs.printReplicationInfo()` shows the window. A busy, write-heavy system needs a larger oplog than the default to keep a comfortable window; a day or more is a common target.

### Replication lag

**Replication lag** is how far a secondary's optime trails the primary's, measured in seconds. On a healthy set it is well under a second. It grows when a secondary has slower hardware, the network is slow, or the primary is writing faster than a secondary can apply. `rs.printSecondaryReplicationInfo()` reports it per member.

Lag is the reason the next three sections exist: at any instant, different members can hold slightly different versions of the data.

## Write concern, revisited

With the oplog in view, write concern has a precise meaning: **how far the write's oplog entry must have travelled before the client is told it succeeded**.

| write concern | acknowledged when |
|---|---|
| `{ w: 1 }` | the primary has applied the write |
| `{ w: 2 }` | the primary and one secondary have it |
| `{ w: "majority" }` | a majority of voting, data-bearing members have it in their on-disk journals |
| add `wtimeout: ms` | stop waiting after that long and report an error (the write is not undone) |

The position in the oplog up to which a majority of members have replicated is called the **majority commit point**. Everything at or before it is **majority-committed**: it exists on enough members that it will survive any election and can never be rolled back. Entries after it exist on a minority only and could still vanish.

## Read concern

**Read concern** answers: of the data this member has, how settled must it be before I am shown it?

| level | what you are shown | can it be rolled back later? |
|---|---|---|
| `"local"` (default) | the member's most recent data | yes |
| `"available"` | like local, with a looser guarantee on sharded clusters | yes |
| `"majority"` | only data acknowledged by a majority - up to the commit point | no |
| `"linearizable"` | majority data, after first confirming this member is still the true primary | no, and never stale; slowest |
| `"snapshot"` | a consistent majority-committed view at one moment, used in transactions | no |

Why would `"local"` ever be a problem? Consider this sequence. A user saves a change with `w: 1`. The primary applies it. A report reading with `"local"` sees it. The primary then crashes before any secondary copied the change, and the change is rolled back. The report displayed something that, as far as the database is now concerned, never happened. A read of uncommitted data that later disappears is called a **dirty read**. Read concern `"majority"` cannot return such data, because it only shows what a majority already holds.

The cost is recency: the majority commit point is a little behind the primary's latest write, so a `"majority"` read may not include a write made a moment ago with `w: 1`.

## Read preference

**Read preference** answers a different question: *which member* serves the read?

| mode | reads go to | if that is unavailable |
|---|---|---|
| `primary` (default) | the primary | the read fails |
| `primaryPreferred` | the primary | a secondary |
| `secondary` | a secondary | the read fails |
| `secondaryPreferred` | a secondary | the primary |
| `nearest` | whichever member has the lowest network latency, primary or secondary | - |

Two refinements narrow the choice of secondary. `maxStalenessSeconds` excludes secondaries lagging by more than the given number of seconds (the minimum allowed value is 90). **Tag sets** restrict reads to members labelled in the configuration, for example `{ use: "reporting" }` or `{ region: "eu" }`.

Reading from secondaries has genuine uses: running heavy analytical queries without slowing the primary, serving users from a member in their own region, and continuing to serve reads during an election.

It also has a catch that surprises newcomers. A secondary is behind the primary by the replication lag. So a user can save a form, be redirected to a page that reads from a secondary, and see the **old** value. The data is not lost; that copy has not caught up yet. Data that is behind the latest state is called **stale**.

> [!WARNING]
> Reading from secondaries is not a way to gain capacity for a struggling system. Every secondary must apply every write the primary does, so its spare capacity is smaller than it looks, and when one member fails the remaining ones inherit its read load at the worst possible moment. Use secondary reads for isolation or locality, with stale data explicitly accepted. To scale beyond one primary, the tool is sharding.

## How the three fit together

The three settings are independent, and the trio is best remembered by the question each one answers.

| setting | question | applies to | values |
|---|---|---|---|
| write concern | how many members must **have my write** before I am told "done"? | writes | `w: 1`, `w: "majority"`, ... |
| read concern | how **settled** must the data I read be? | reads | `local`, `majority`, `linearizable`, `snapshot` |
| read preference | **which member** answers my read? | reads | `primary`, `secondary`, `nearest`, ... |

Common combinations:

| goal | write concern | read concern | read preference |
|---|---|---|---|
| defaults (5.0 and later): durable writes, freshest reads | `majority` | `local` | `primary` |
| never see data that could be rolled back | `majority` | `majority` | `primary` |
| analytics on a dedicated member, stale data accepted | (any) | `local` | `secondary` with a tag set |
| fastest logging, loss tolerated | `1` | `local` | `primary` |

### Reading your own writes

To guarantee that a user sees their own change even when reads go to a secondary, MongoDB offers **causal consistency**. Operations are run in a session; after each write the server returns the write's position in the oplog, and the driver sends that position along with the next read. A secondary receiving such a read waits until it has replicated at least that far before answering. Combined with majority write and read concern, this gives "read your own writes" across members.

> [!TIP]
> Start with the defaults: write concern `majority`, read concern `local`, read preference `primary`. They give durable writes and reads that always reflect the latest state. Change a setting only for a named reason, and make the change on the specific operation that needs it, not globally.

> [!INTERVIEW]
> **"What is the difference between write concern, read concern and read preference?"** Write concern is the acknowledgement level for a write: how many members must have it before success is reported. Read concern is the consistency level of a read: whether it may return data not yet replicated to a majority. Read preference is routing: which member serves the read. Then show you can combine them: `w: majority` with read concern `majority` means a client never observes data that can be rolled back; adding a causally consistent session gives read-your-own-writes even from secondaries. Close with the caution that secondary reads are eventually consistent and do not add write capacity.

## Worked example in the shell

```javascript
rs0 [direct: primary] shop> db.carts.insertOne({ _id: 7, items: 1 }, { writeConcern: { w: "majority", wtimeout: 5000 } })
{ acknowledged: true, insertedId: 7 }

rs0 [direct: primary] shop> db.carts.find({ _id: 7 }).readConcern("majority")
[ { _id: 7, items: 1 } ]

rs0 [direct: primary] shop> db.carts.find({ _id: 7 }).readPref("secondary", [ { use: "reporting" } ])
[ { _id: 7, items: 1 } ]

rs0 [direct: primary] shop> use local
rs0 [direct: primary] local> db.oplog.rs.find({ ns: "shop.carts" }).sort({ $natural: -1 }).limit(1)
[ { op: 'i', ns: 'shop.carts', o: { _id: 7, items: 1 }, ts: Timestamp({ t: 1767430000, i: 1 }), ... } ]

rs0 [direct: primary] local> rs.printReplicationInfo()
configured oplog size:   990 MB
log length start to end: 93204 secs (25.89 hrs)
```

1. The insert returns once a majority has the write, or fails with a timeout after five seconds.
2. `.readConcern("majority")` asks for majority-committed data only. Because the write was acknowledged by a majority, it is visible.
3. `.readPref("secondary", [...])` routes this one read to a secondary tagged for reporting.
4. The oplog is an ordinary collection that can be queried. `$natural: -1` sorts by storage order, newest first, so this shows the latest entry for the namespace: the insert made a moment ago.
5. The oplog window here is about 26 hours: a secondary could be offline that long and still catch up.

## The same from Python

```python
from pymongo import MongoClient, ReadPreference, WriteConcern
from pymongo.read_concern import ReadConcern

client = MongoClient("mongodb://h1,h2,h3/?replicaSet=rs0")
db = client["shop"]

orders = db.get_collection("orders",                                         # 1
                           write_concern=WriteConcern("majority", wtimeout=5000),
                           read_concern=ReadConcern("majority"))
orders.insert_one({"_id": 501, "total": 48})
print(orders.find_one({"_id": 501})["total"])                                # 2

reports = db.get_collection("orders",                                        # 3
                            read_preference=ReadPreference.SECONDARY_PREFERRED)
print(reports.count_documents({}))

with client.start_session(causal_consistency=True) as s:                     # 4
    orders.update_one({"_id": 501}, {"$set": {"total": 50}}, session=s)
    fresh = reports.find_one({"_id": 501}, session=s)                        # 5
    print(fresh["total"])
```

1. In PyMongo the three settings are attached to a collection (or database, or client) object. This handle writes and reads with `majority`.
2. Prints `48`.
3. A second handle onto the same collection, with a different read preference, for reporting. Different parts of an application can use different handles.
4. A causally consistent session.
5. This read goes to a secondary, but because it is in the same session as the update, the secondary waits until it has replicated the update. Prints `50`, never the stale `48`.

## Simulate it yourself

The simulation runs a three-member set with one slow secondary. It shows the oplog in idempotent form, the majority commit point, the difference between `local` and `majority` reads, stale secondary reads, and a rollback after failover.

```python-run
class Member:
    def __init__(self, name):
        self.name, self.data, self.oplog = name, {}, []

    @property
    def optime(self):
        return len(self.oplog)                      # position of the last applied entry

    def apply(self, entry):
        kind, key, value = entry
        if kind == "set":
            self.data[key] = value                  # "set to value": safe to repeat
        elif kind == "del":
            self.data.pop(key, None)
        self.oplog.append(entry)

primary, fast, slow = Member("primary"), Member("fast-secondary"), Member("slow-secondary")
members = [primary, fast, slow]

def write(kind, key, value=None):
    """The client says $inc; the primary logs the RESULT, which is idempotent."""
    if kind == "inc":
        kind, value = "set", primary.data.get(key, 0) + value
    primary.apply((kind, key, value))

def replicate(member, up_to=None):
    for entry in primary.oplog[member.optime:up_to]:
        member.apply(entry)

def commit_point():
    optimes = sorted((m.optime for m in members), reverse=True)
    return optimes[len(members) // 2]               # the position a majority has reached

def read(member, key, concern="local"):
    if concern == "local":
        return member.data.get(key)
    state = {}                                      # "majority": replay only up to the commit point
    for kind, k, v in member.oplog[:commit_point()]:
        if kind == "set": state[k] = v
        else: state.pop(k, None)
    return state.get(key)

write("inc", "stock", 10); write("inc", "stock", -1); write("inc", "stock", -1)
print("oplog on the primary:", primary.oplog)
replicate(fast); replicate(slow, up_to=1)
print("optimes:", {m.name: m.optime for m in members}, "| majority commit point:", commit_point())

write("inc", "stock", -1)                           # a 4th write, acknowledged with w:1, not yet replicated
print()
print("after one more w:1 write (optime %d on the primary only):" % primary.optime)
print("  read primary, concern local   ->", read(primary, "stock"))
print("  read primary, concern majority->", read(primary, "stock", "majority"), "(commit point is %d)" % commit_point())
print("  read fast secondary           ->", read(fast, "stock"), "(stale by one write)")
print("  read slow secondary           ->", read(slow, "stock"), "(stale by three writes)")
print("  would w:majority be acknowledged for the 4th write?", sum(m.optime >= 4 for m in members) >= 2)

# The primary crashes before replicating write 4. The fast secondary is elected.
lost = primary.oplog[fast.optime:]
print()
print("primary fails; fast-secondary becomes primary at optime", fast.optime)
print("  rolled back on the old primary:", lost, "-> the client was told this w:1 write succeeded")
print("  the 'majority' read had shown", read(fast, "stock"), "all along, so it never exposed the lost write")

# Idempotency: the slow secondary restarts and re-applies entries it had already applied.
replay = Member("replayed")
for entry in fast.oplog + fast.oplog[1:]:           # entries 2 and 3 applied twice
    replay.apply(entry)
print("  re-applying oplog entries twice still gives stock =", replay.data["stock"])
```

Reading the output:

- The three `$inc` operations appear in the oplog as `set` entries with the resulting values 10, 9 and 8.
- The primary and the fast secondary are at position 3, the slow one at 1. Two of three members have reached 3, so the commit point is 3.
- After the fourth write, a `local` read on the primary returns 7, while a `majority` read returns 8: the fourth write exists on one member only. The secondaries return 8 and 10 - stale by one and by three writes.
- A `w: majority` wait for the fourth write would not yet be satisfied.
- When the primary fails, the fourth write is rolled back. The `local` reader saw a value (7) that no longer exists; the `majority` reader never did.
- Re-applying entries a second time leaves the stock at 8, because every entry states an outcome, not a change.

## Pitfalls

- **Confusing the three settings.** Write concern is about acknowledgement, read concern about how settled data is, read preference about which member.
- **Reading from secondaries and expecting your own latest write.** Use a causally consistent session or read from the primary.
- **An oplog window that is too short**, forcing a full resync after ordinary maintenance.
- **`w: 1` plus `local` reads for data users rely on**, exposing them to rollbacks and dirty reads.
- **`w` set to the full member count**, so one member's downtime blocks every write.
- **Treating secondary reads as a scaling strategy.**
- **`linearizable` reads without a time limit**: they wait for a majority and can hang if one is unreachable; always set `maxTimeMS`.

## Cheat sheet

| task | shell |
|---|---|
| oplog size and window | `rs.printReplicationInfo()` |
| lag per secondary | `rs.printSecondaryReplicationInfo()` |
| write with majority | `{ writeConcern: { w: "majority", wtimeout: 5000 } }` |
| read majority-committed data | `cursor.readConcern("majority")` |
| route a read | `cursor.readPref("secondaryPreferred")` |
| inspect the oplog | `use local; db.oplog.rs.find().sort({ $natural: -1 }).limit(5)` |

| term | one-line meaning |
|---|---|
| optime | a member's position in the oplog |
| replication lag | how far a secondary's optime trails the primary's |
| oplog window | time span the oplog currently covers |
| majority commit point | the position a majority has replicated; everything before it is permanent |

## Summary

- The oplog is a capped collection in which the primary records every change in idempotent form; secondaries follow it and apply the entries in order.
- The oplog window bounds how long a secondary may be offline; replication lag is how far behind a secondary is.
- Write concern sets how far a write must have replicated before it is acknowledged; `majority` writes cannot be rolled back.
- Read concern sets how settled returned data must be; `majority` returns only data up to the majority commit point and so avoids dirty reads.
- Read preference picks the member that answers; secondary reads can be stale and do not add write capacity.
- Causally consistent sessions let a client read its own writes from any member.

## Glossary

- **Oplog** - the operations log, a capped collection recording every change on a member.
- **Optime** - the timestamp of a member's most recent oplog entry; its position in the log.
- **Initial sync** - the full copy a new or too-far-behind member performs before following the oplog.
- **Idempotent** - giving the same result whether applied once or several times.
- **Capped collection** - a fixed-size collection that overwrites its oldest documents.
- **Oplog window** - the time span between the oldest and newest oplog entries.
- **Replication lag** - the delay by which a secondary trails the primary.
- **Write concern** - the acknowledgement level required for a write.
- **Majority commit point** - the oplog position replicated to a majority of members.
- **Read concern** - the consistency level required of data returned by a read.
- **Dirty read** - reading data that is later rolled back.
- **Read preference** - the rule selecting which member serves a read.
- **Stale data** - data that is behind the most recent state.
- **Tag set** - labels on members used to direct reads.
- **Causal consistency** - a session guarantee that reads reflect the session's earlier writes.

## Check yourself

```quiz
[
  {"q": "A client sends {$inc: {stock: -1}} and the stock goes from 9 to 8. What does the oplog record?",
   "options": ["{$inc: {stock: -1}}", "A set of stock to 8", "Nothing; only inserts are logged", "The whole collection"],
   "answer": 1,
   "explain": "Oplog entries are idempotent: they record the resulting value so that re-applying them is harmless."},
  {"q": "A secondary was offline for 30 hours and the oplog window is 26 hours. What must happen?",
   "options": ["It catches up normally", "It needs a full initial sync because the entries it requires have been overwritten", "It becomes primary", "It is removed from the set automatically"],
   "answer": 1,
   "explain": "Once the oplog no longer contains the entries a member needs, it cannot catch up incrementally."},
  {"q": "Which setting determines WHICH member answers a read?",
   "options": ["Write concern", "Read concern", "Read preference", "wtimeout"],
   "answer": 2,
   "explain": "Read preference is routing. Read concern is about how settled the data is, not about which member."},
  {"q": "What does read concern \"majority\" guarantee?",
   "options": ["The read goes to a majority of members", "Returned data has been replicated to a majority and cannot be rolled back", "The read is the fastest possible", "The data is the very latest on the primary"],
   "answer": 1,
   "explain": "It returns data up to the majority commit point, which may be slightly behind the primary's newest writes."},
  {"q": "A user saves a profile and the next page, read with read preference secondary, shows the old value. Why?",
   "options": ["The write was lost", "The secondary has not yet replicated the write; it is stale", "Secondaries never receive updates", "The index is corrupt"],
   "answer": 1,
   "explain": "Replication lag means a secondary can trail the primary; a causally consistent session or a primary read avoids this."},
  {"q": "What is the majority commit point?",
   "options": ["The newest entry on the primary", "The oplog position that a majority of members have replicated", "The oldest entry in the oplog", "The time of the last election"],
   "answer": 1,
   "explain": "Everything at or before it is on a majority of members and is safe from rollback."},
  {"q": "Why does reading from secondaries not help a system limited by write throughput?",
   "options": ["Secondaries cannot be read", "Every secondary must still apply every write the primary applies", "Secondaries are always offline", "Reads from secondaries are converted to writes"],
   "answer": 1,
   "explain": "Replication copies all writes to all members, so write load is not reduced; sharding is the tool for that."},
  {"q": "Which combination ensures a client never observes data that might be rolled back?",
   "options": ["w: 1 with read concern local", "w: \"majority\" with read concern \"majority\"", "w: 0 with read preference nearest", "w: 1 with read preference secondary"],
   "answer": 1,
   "explain": "Majority-acknowledged writes are permanent, and majority reads only return such data."}
]
```

> **Source:** MongoDB: The Definitive Guide 3e, ch. 11-12 (topics only; wording and examples are original). MongoDB Manual: https://www.mongodb.com/docs/manual/core/replica-set-oplog/ , https://www.mongodb.com/docs/manual/reference/read-concern/ , https://www.mongodb.com/docs/manual/core/read-preference/ , https://www.mongodb.com/docs/manual/core/causal-consistency-read-write-concerns/
