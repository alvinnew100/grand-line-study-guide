# Connecting from applications and administering a replica set

> **Before this lesson:** you should understand primaries, secondaries, elections and failover ([Replica sets, members and elections](#/lesson/mongodb/replica-sets-elections)) and the oplog, replication lag and write concern ([The oplog, write concern, read concern and read preference](#/lesson/mongodb/oplog-concerns)).

## In plain words

A replica set can change its primary at any moment. How does your program, running on some other machine, keep talking to the right server? And how do the people who look after the set replace hardware, upgrade software and change settings without the application noticing?

For the first question, think of phoning a company through its switchboard. You do not memorise which desk your contact sits at this week. You dial the main number and the switchboard connects you, wherever the person has moved. A MongoDB **driver** (the library your program uses to talk to the database) plays the switchboard: you give it the set's addresses once, and it keeps track of which member is primary.

For the second, think of changing the tyres on a lorry convoy one lorry at a time, while the convoy keeps moving. Each lorry pulls over briefly, the others carry the load, and the convoy never stops. Maintaining a replica set member by member is called **rolling maintenance**.

Why it matters for a job: a replica set only delivers high availability if the application is written to survive a failover. Many outages blamed on "the database" are really applications that crashed during a ten-second election. And being able to describe a rolling upgrade is expected of anyone who will operate MongoDB.

## The connection string

A program connects by giving the driver a **connection string**, a single line of text in URI form (the same general shape as a web address):

```
mongodb://app_user:secret@db1.example.net:27017,db2.example.net:27017,db3.example.net:27017/shop?replicaSet=rs0&w=majority&retryWrites=true
```

Read it part by part.

| part | meaning |
|---|---|
| `mongodb://` | the protocol |
| `app_user:secret@` | user name and password (optional here; often supplied separately) |
| `db1...,db2...,db3...` | the **seed list**: members the driver may contact first |
| `/shop` | the default database |
| `?replicaSet=rs0` | the name of the set; tells the driver to discover the whole set |
| `&w=majority&retryWrites=true` | further options, joined by `&` |

The seed list does not need to name every member, and the members named do not need to include the primary. The driver contacts whichever seed answers, asks it for the full membership and each member's role, and then monitors every member in the background, re-checking about every ten seconds and immediately after any error. This background process is called **server discovery and monitoring**. Listing several seeds matters only for the first contact: with a single seed, the application cannot start if that one member happens to be down.

A second form, `mongodb+srv://cluster0.example.net/shop`, replaces the host list with one name. The driver looks that name up in **DNS** (the internet's directory that turns names into addresses) and receives the member list from there. Hosted services use this form, because members can then be replaced without anyone editing connection strings.

## What happens during a failover

Suppose the primary dies while the application is busy. From the application's side:

1. Operations in flight on the dead connection fail with a network error.
2. The driver marks that member as unknown and starts checking the others more frequently.
3. For about ten to twelve seconds there is no primary. During this time a write cannot be sent anywhere. The driver does not fail at once; it waits for a suitable member to appear, for up to the **server selection timeout** (30 seconds by default).
4. A secondary wins the election. The driver notices and sends waiting operations to the new primary.

So an application with sensible timeouts experiences a failover as a pause of a few seconds, not as a wall of errors. What about the operation that was in flight at the moment of failure?

### Retryable writes

When a write fails with a network error, the application cannot tell which of two things happened: the write never reached the server, or the write was applied and only the reply was lost. Sending it again is safe in the first case and harmful in the second - a second order, a counter incremented twice.

**Retryable writes** solve this. The driver attaches a unique identifier to each write. If the write fails with a network error or a "not primary" error, the driver sends it once more, to the new primary if there is one. The server remembers recent identifiers; if it has already applied that write, it returns the original result and does not apply it again. The effect is a write that is applied **exactly once** even when a retry occurs.

Retryable writes are switched on by default in current drivers and cover single-document operations: `insertOne`, `updateOne`, `replaceOne`, `deleteOne`, `findOneAndUpdate` and their relatives, plus bulk writes made of these. Multi-document operations such as `updateMany` and `deleteMany` are **not** retried automatically, because they cannot be given this guarantee. **Retryable reads** do the same for queries, which are naturally safe to repeat.

One retry covers the common case, a brief hiccup or a quick election. It does not cover a long outage.

### Designing for the cases the driver cannot fix

Three habits make an application robust beyond what automatic retries provide.

**Make operations idempotent.** An operation is idempotent when repeating it changes nothing further. `$set: { status: "paid" }` is idempotent. `$inc: { balance: -50 }` is not. Where a non-idempotent change is unavoidable, give it an identity: include a unique `payment_id` and let a unique index reject a second attempt.

**Set time limits deliberately.** Without them, a problem turns into threads that wait forever.

| setting | what it limits | default |
|---|---|---|
| `serverSelectionTimeoutMS` | waiting for a usable member (for example during an election) | 30,000 |
| `connectTimeoutMS` | opening a new network connection | 20,000 in PyMongo |
| `socketTimeoutMS` | waiting for a reply on a connection | none |
| `maxTimeMS` (per operation) | how long the **server** may work on the operation | none |
| `wtimeout` (write concern) | waiting for replication of a write | none |

`maxTimeMS` is the most useful of these day to day: it makes the server abandon a runaway query, which also stops it consuming resources.

**Use one client for the whole process.** A `MongoClient` object owns a **connection pool**: a set of open connections that are reused, because opening a connection is expensive (it involves a network handshake and authentication). The default maximum is 100 connections per member. Create the client once when the program starts and share it. Creating a new client per request is a classic mistake that floods the server with connections.

> [!WARNING]
> Do not write your own blanket retry loop around all database calls. Retrying a non-idempotent write that actually succeeded duplicates it, and retrying everything during a real outage multiplies load on a system that is already struggling. Rely on the driver's retryable writes for single operations and on the transaction helper for transactions, and reserve hand-written retries for operations you have made idempotent.

## Administering a replica set

### Member states

`rs.status()` shows a state for each member. The ones you will see:

| state | meaning |
|---|---|
| `PRIMARY` | accepting writes |
| `SECONDARY` | replicating and able to serve reads |
| `STARTUP2` | performing its initial sync |
| `RECOVERING` | temporarily not ready for reads, for example too far behind |
| `ROLLBACK` | discarding writes that did not replicate before a failover |
| `ARBITER` | voting only |
| `DOWN` / `(not reachable/healthy)` | cannot be contacted by the member reporting |

### Changing the configuration

The set's configuration is a document. To change it, fetch it, edit it and submit it:

```javascript
rs0 [direct: primary] admin> cfg = rs.conf()
rs0 [direct: primary] admin> cfg.members[2].priority = 0
rs0 [direct: primary] admin> cfg.members[2].hidden = true
rs0 [direct: primary] admin> rs.reconfig(cfg)
{ ok: 1 }
```

- `rs.conf()` returns the current configuration, stored here in the variable `cfg`.
- The next two lines edit the third member (positions count from zero) so that it can never be primary and is hidden from applications.
- `rs.reconfig(cfg)` submits the new configuration. It must be run on the primary and takes effect across the set.

Change one voting member at a time, so that a majority always agrees on what the configuration is. `rs.add(...)` and `rs.remove(...)` are shortcuts that do the fetch-edit-submit for you.

### Rolling maintenance

The procedure for upgrading software, changing a setting that needs a restart, or replacing a disk is always the same shape.

```mermaid
graph LR
  A["1. Pick one secondary"] --> B["2. Shut it down, do the work, restart"]
  B --> C["3. Wait until it is SECONDARY and caught up"]
  C --> D{"More secondaries?"}
  D -->|yes| A
  D -->|no| E["4. rs.stepDown on the primary"]
  E --> F["5. Maintain the old primary as a secondary"]
```

1. Take **one secondary** out of service, do the work, and restart it.
2. Wait until it reports `SECONDARY` and its replication lag has returned to near zero. Never start on the next member before this.
3. Repeat for each remaining secondary.
4. Finally run `rs.stepDown()` on the primary. It hands over to an up-to-date secondary in a controlled election that takes a few seconds, shorter than a crash because no timeout has to expire.
5. The former primary is now a secondary; maintain it like the others.

At every moment a majority of members is up, so the application keeps running. The step-down causes one short pause, which retryable writes absorb.

For work that should not be seen by the set at all, a member can be restarted as a **standalone**: without the `--replSet` option and on a different port, so that neither the set nor the application talks to it. When restarted normally, it catches up from the oplog - provided the work took less time than the oplog window.

### Watching lag and the oplog

Two numbers deserve regular attention.

- **Replication lag** per secondary, from `rs.printSecondaryReplicationInfo()`. Persistent lag means a secondary cannot keep up, and it limits how quickly a majority write can be acknowledged.
- **Oplog window**, from `rs.printReplicationInfo()`. It must comfortably exceed your longest planned maintenance, or a member under maintenance will need a full resync. The oplog can be resized on a running member with the `replSetResizeOplog` command.

A member that has fallen too far behind is rebuilt by emptying its data folder and restarting it, which triggers an initial sync, or by restoring a recent backup and letting it catch up from there.

> [!TIP]
> Before any planned maintenance, check three things: every member is healthy (`rs.status()`), lag is near zero, and the oplog window is several times longer than the work will take. Most maintenance mishaps come from skipping one of these.

> [!INTERVIEW]
> **"How do you upgrade a replica set with no downtime?"** A rolling upgrade: upgrade the secondaries one at a time, waiting for each to return to `SECONDARY` and catch up; then `rs.stepDown()` the primary, let a secondary take over, and upgrade the old primary. A majority is available throughout. Add the application side: the step-down causes a brief election that retryable writes and the driver's server selection ride through. For a major version, mention the final step of raising the feature compatibility version only after every member runs the new binaries, because that step is what makes the upgrade hard to reverse.

## Replication chaining and running on a budget

### Where do secondaries copy from?

So far the picture was simple: the primary writes, every secondary copies the primary's oplog. In practice a secondary may choose to copy from **another secondary** instead. This is called **replication chaining**, like a line of people passing buckets of water: the primary hands to one, who hands to the next.

```mermaid
graph LR
  P["Primary"] --> S1["Secondary 1"]
  S1 --> S2["Secondary 2"]
  P --> S3["Secondary 3"]
```

By default each secondary picks its source automatically, preferring a member that is close (low network delay) and ahead of it. Chaining has real advantages: it spares the primary from serving every copier, and it saves bandwidth when a data centre holds several secondaries, because only one of them needs to cross the expensive link to the primary and the rest copy from their neighbour.

The disadvantage is delay. A change reaches the second secondary only after the first has applied it, so lag adds up along the chain, and a majority-acknowledged write may wait longer. If the middle member is slow, everything behind it is slow too.

### Replication loops

A **replication loop** is a cycle of members each copying from the next: A copies from B, B from C, C from A. None of them copies from the primary, so none receives new writes, and all fall behind together. Automatic source selection avoids loops by only choosing a source that is ahead. Loops can appear only when sources are forced by hand with the `replSetSyncFrom` command (the shell helper is `rs.syncFrom("host:port")`). Before using it, read `rs.status()` and make sure the chosen source is ahead and does not itself copy from you.

### Disabling chaining

If you prefer predictable, short lag over saving the primary's bandwidth, switch chaining off. The setting lives in the replica set configuration, under `settings`:

```javascript
rs0:PRIMARY> cfg = rs.conf()
rs0:PRIMARY> cfg.settings = cfg.settings || {}
rs0:PRIMARY> cfg.settings.chainingAllowed = false
rs0:PRIMARY> rs.reconfig(cfg)
```

- `rs.conf()` fetches the current configuration, as in the earlier "Changing the configuration" steps.
- The `settings` sub-document may not exist yet, so it is created if missing.
- `chainingAllowed` defaults to `true`; setting it to `false` makes every secondary copy straight from the primary.
- `rs.reconfig` submits the change from the primary.

If the primary becomes unavailable, secondaries fall back to copying from each other so that they can keep up. The cost of turning chaining off is that the primary serves more copiers; with a handful of members, that is rarely a problem.

### Replication on a budget

A full replica set normally means several equally strong machines, which is expensive. If you can afford only one excellent server, you can still gain a safety copy by adding a cheaper machine used purely for disaster recovery: less memory, a slower disk, and no client traffic. The good server is always the primary. The cheap one is configured with these member options:

```javascript
{ _id: 1, host: "cheap.example.org:27017",
  priority: 0,          // never becomes primary
  hidden: true,         // invisible to drivers, so no client reads reach it
  buildIndexes: false,  // optional: skips building secondary indexes
  votes: 0 }            // only if the set has just two members
```

- `priority: 0` means the member can never stand for election, so the weak machine never takes over from the strong one.
- `hidden: true` removes it from the list drivers see, so reads cannot be sent to it. (A hidden member must also have priority 0.)
- `buildIndexes: false` saves a lot of work, because the member then keeps no indexes except `_id`. The cost: restoring from this member means rebuilding every index. This option can only be set when the member is added.
- `votes: 0` addresses a two-member set. With two voting members, losing either leaves no majority, so the primary would step down. Taking the vote away from the cheap member lets the primary keep working if the cheap one fails. If a third machine exists, even the application server, a lightweight arbiter running there is better than `votes: 0`.

You get a continuous, up-to-date copy for backup and recovery, without paying for two high-end machines. You do not get automatic failover to equal performance: if the primary dies, the cheap member cannot step in as an equal.

> [!WARNING]
> A budget secondary protects data, not availability. Plan for a manual recovery, and test it before you need it.

## The same from Python

```python
from pymongo import MongoClient
from pymongo.errors import AutoReconnect, DuplicateKeyError, ServerSelectionTimeoutError

client = MongoClient(                                                    # 1
    "mongodb://db1.example.net,db2.example.net,db3.example.net/?replicaSet=rs0",
    w="majority", retryWrites=True,
    serverSelectionTimeoutMS=15000, maxPoolSize=50,
)
payments = client["shop"]["payments"]
payments.create_index("payment_id", unique=True)                         # 2

def record_payment(payment_id, amount):
    try:
        payments.insert_one({"payment_id": payment_id, "amount": amount})   # 3
        return "recorded"
    except DuplicateKeyError:
        return "already recorded"                                        # 4
    except ServerSelectionTimeoutError:
        return "database unavailable, try again later"                   # 5
    except AutoReconnect:
        return "connection lost, safe to call again with the same id"    # 6

print(record_payment("pay-7731", 49.0))
print(record_payment("pay-7731", 49.0))                                  # 7
slow = payments.find({"amount": {"$gt": 10}}).max_time_ms(2000)          # 8
```

1. One client for the whole program. The options are also valid inside the connection string.
2. A unique index turns the business identifier into a guard against duplicates.
3. A single-document insert: retried once by the driver if a failover interrupts it.
4. A repeat of the same payment is harmless; the unique index reports it.
5. Raised when no primary appeared within the selection timeout.
6. Raised when the connection failed and the driver's own retry also failed. Because the operation is idempotent thanks to the unique index, the caller may repeat it.
7. Prints `recorded`, then `already recorded`.
8. `max_time_ms` tells the server to give up on this query after two seconds.

## Simulate it yourself

The first part replays a failover three ways: a naive client that retries blindly, a client that does not retry, and a client using retryable writes. The second part checks a rolling-maintenance plan and a careless one against the majority rule.

```python-run
class Server:
    """A primary that applies increments and remembers the ids of writes it has applied."""
    def __init__(self):
        self.balance, self.seen = 100, {}

    def inc(self, amount, txn_id=None):
        if txn_id is not None and txn_id in self.seen:
            return self.seen[txn_id]                # already applied: return the original result
        self.balance += amount
        if txn_id is not None:
            self.seen[txn_id] = self.balance
        return self.balance

def send(server, amount, reply_lost, txn_id=None):
    result = server.inc(amount, txn_id)             # the server always applies the write here ...
    if reply_lost:
        raise ConnectionError("network error")      # ... but the reply may not arrive
    return result

def run(strategy):
    server = Server()
    for i, reply_lost in enumerate([False, True, False]):      # the 2nd request loses its reply (failover)
        try:
            if strategy == "retryable":
                try:
                    send(server, -10, reply_lost, txn_id=i)
                except ConnectionError:
                    send(server, -10, False, txn_id=i)         # the driver retries with the SAME id
            else:
                send(server, -10, reply_lost)
        except ConnectionError:
            if strategy == "blind retry":
                send(server, -10, False)                       # the application re-sends without an id
    return server.balance

print("three payments of 10 from a balance of 100; the reply to the second one is lost")
for strategy in ("no retry", "blind retry", "retryable"):
    print("  %-12s -> final balance %d" % (strategy, run(strategy)))
print("  correct answer is 70. 'no retry' is right here only because the write DID arrive;")
print("  had the request been lost instead, 'no retry' would give 80 and never know.")

print()
def check_plan(name, members, steps):
    """Each step is the set of members that are down at the same time."""
    majority = len(members) // 2 + 1
    worst = min(len(members) - len(down) for down in steps)
    verdict = "OK, a primary exists throughout" if worst >= majority else "OUTAGE: no majority at some step"
    print("  %-28s members up at worst step: %d of %d (need %d) -> %s" % (name, worst, len(members), majority, verdict))

members = ["a", "b", "c"]
print("maintenance plans for a 3-member set")
check_plan("rolling, one at a time", members, [{"b"}, {"c"}, {"a"}])
check_plan("both secondaries at once", members, [{"b", "c"}, {"a"}])
five = ["a", "b", "c", "d", "e"]
check_plan("5 members, two at a time", five, [{"b", "c"}, {"d", "e"}, {"a"}])
check_plan("5 members, three at a time", five, [{"b", "c", "d"}, {"e", "a"}])

print()
oplog_window_hours = 26
for work_hours in (2, 20, 30):
    ok = work_hours < oplog_window_hours
    print("  member offline %2d h with a %d h oplog window -> %s" %
          (work_hours, oplog_window_hours, "catches up from the oplog" if ok else "needs a full initial sync"))
```

Reading the output:

- With a blind retry the second payment is applied twice and the balance ends at 60: ten too low. With retryable writes the retry carries the same identifier, the server recognises it, and the balance is the correct 70.
- "No retry" gives 70 in this run only by luck: the lost message was the reply. When the *request* is the one that is lost, not retrying loses a payment. The application cannot distinguish the two cases, which is exactly why the identifier is needed.
- Taking one member of three down at a time always leaves two, a majority. Taking both secondaries down together leaves one member and no primary.
- A five-member set can afford two members down at once, but not three.
- A member offline for longer than the oplog window cannot catch up and must be resynchronised from scratch.

## Pitfalls

- **A single host in the seed list**, so the application cannot start when that member is down.
- **Omitting `replicaSet=`**, which can make the driver treat the address as a lone server and never follow a failover.
- **Creating a `MongoClient` per request**, exhausting connections.
- **No time limits**, so that requests pile up behind a slow or missing server.
- **Blind application-level retries of non-idempotent writes.**
- **Assuming `updateMany` and `deleteMany` are retried.** They are not.
- **Starting maintenance on the next member before the previous one has caught up.**
- **Maintenance longer than the oplog window.**
- **Reconfiguring several voting members in one step.**

## Cheat sheet

| task | how |
|---|---|
| connect to a set | `mongodb://h1,h2,h3/db?replicaSet=rs0` |
| connect through DNS | `mongodb+srv://cluster.example.net/db` |
| limit server work on a query | `.maxTimeMS(2000)` / `.max_time_ms(2000)` |
| see member states | `rs.status()` |
| change settings | `cfg = rs.conf()`; edit; `rs.reconfig(cfg)` |
| hand over the primary role | `rs.stepDown()` |
| check lag / window | `rs.printSecondaryReplicationInfo()` / `rs.printReplicationInfo()` |
| resize the oplog | `db.adminCommand({ replSetResizeOplog: 1, size: <MB> })` |

| default | value |
|---|---|
| server selection timeout | 30 seconds |
| connection pool size | 100 per member |
| retryable writes / reads | on |
| driver heartbeat to each member | every 10 seconds |

## Summary

- A connection string gives the driver a seed list and the set's name; the driver discovers all members and tracks the primary by itself.
- During a failover the driver waits for a new primary instead of failing at once, up to the server selection timeout.
- Retryable writes attach an identifier so that a single-document write retried after a network error is applied exactly once; multi-document writes are not covered.
- Robust applications make operations idempotent, set time limits, and share one client with its connection pool.
- Configuration changes go through `rs.reconfig`, one voting member at a time.
- Rolling maintenance works through the secondaries one by one and steps the primary down last, keeping a majority up throughout, within the oplog window.

## Glossary

- **Driver** - the library an application uses to talk to MongoDB.
- **Connection string** - a URI holding hosts, options and credentials for connecting.
- **Seed list** - the hosts a driver contacts first to discover the set.
- **Server discovery and monitoring** - the driver's background tracking of members and their roles.
- **DNS** - the directory service that maps names to network addresses.
- **Server selection timeout** - how long the driver waits for a suitable member before raising an error.
- **Retryable write** - a write carrying an identifier so that one automatic retry cannot apply it twice.
- **Idempotent** - having the same effect whether performed once or several times.
- **Connection pool** - a set of open, reusable connections held by a client.
- **`maxTimeMS`** - a per-operation limit on how long the server may work on it.
- **Rolling maintenance** - servicing members one at a time so that the set stays available.
- **Step down** - a primary voluntarily giving up its role.
- **Standalone** - a `mongod` running outside any replica set.
- **Resync** - rebuilding a member's data with a full initial sync.
- **Replication chaining** - a secondary copying from another secondary instead of from the primary.
- **Replication loop** - a cycle of members each copying from the next, so that none receives new writes.
- **`chainingAllowed`** - a replica set setting (default true) controlling whether chaining is permitted.
- **Hidden member** - a member that drivers do not see and so receives no client reads.
- **`priority: 0`** - a member option making a member ineligible to become primary.
- **`buildIndexes: false`** - a member option that skips building secondary indexes on that member.

## Check yourself

```quiz
[
  {"q": "A connection string lists two of a set's five members and includes replicaSet=rs0. Can the driver reach the primary if it is one of the three unlisted members?",
   "options": ["No, only listed members can be used", "Yes, the driver discovers the full membership from any seed and finds the primary", "Only after a restart", "Only with read preference secondary"],
   "answer": 1,
   "explain": "The seed list is for first contact; discovery then reveals every member and its role."},
  {"q": "What do retryable writes guarantee for an insertOne interrupted by a failover?",
   "options": ["It is applied at least twice", "It is retried once and applied exactly once, because the server recognises the write's identifier", "It is silently dropped", "It is converted into an upsert"],
   "answer": 1,
   "explain": "The identifier lets the server return the original result if the write had already been applied."},
  {"q": "Which operation is NOT automatically retried by retryable writes?",
   "options": ["insertOne", "updateOne", "findOneAndUpdate", "updateMany"],
   "answer": 3,
   "explain": "Multi-document writes such as updateMany and deleteMany are not covered."},
  {"q": "Why should a program create a single MongoClient and share it?",
   "options": ["Only one client is allowed per server", "A client owns a connection pool; creating many clients opens many connections and wastes handshakes", "Clients cannot be closed", "It disables elections"],
   "answer": 1,
   "explain": "Connections are costly to open and are reused through the pool that one client manages."},
  {"q": "In a rolling upgrade of a three-member set, what is the correct order?",
   "options": ["Primary first, then secondaries", "All three at once", "Secondaries one at a time, waiting for each to catch up, then step down and upgrade the primary", "Any order, without waiting"],
   "answer": 2,
   "explain": "This keeps a majority available at every step and limits the disruption to one short step-down."},
  {"q": "Which update is idempotent?",
   "options": ["{$inc: {balance: -50}}", "{$push: {log: \"paid\"}}", "{$set: {status: \"paid\"}}", "{$mul: {price: 2}}"],
   "answer": 2,
   "explain": "Setting a field to a fixed value gives the same result however many times it is applied."},
  {"q": "A member is taken offline for 30 hours and the oplog window is 26 hours. What happens when it returns?",
   "options": ["It catches up normally", "It cannot catch up from the oplog and needs a full resync", "It becomes primary", "Nothing; it never rejoins"],
   "answer": 1,
   "explain": "The entries it needs have been overwritten, so it must copy all data again."},
  {"q": "What does maxTimeMS do?",
   "options": ["Limits how long the driver waits to find a primary", "Tells the server to abandon the operation after the given time", "Sets the heartbeat interval", "Delays replication"],
   "answer": 1,
   "explain": "It is a server-side limit on processing time for one operation, which also frees server resources."},
  {"q": "What is replication chaining?",
   "options": ["A secondary copying from another secondary instead of the primary", "Linking two replica sets together", "Running two writes in sequence", "Encrypting the oplog"],
   "answer": 0,
   "explain": "Chaining spares the primary some work but adds delay along the chain."},
  {"q": "Which setting forces every secondary to copy directly from the primary?",
   "options": ["settings.chainingAllowed = false", "priority = 0", "hidden = true", "votes = 0"],
   "answer": 0,
   "explain": "chainingAllowed defaults to true; setting it to false disables chaining. If the primary is unreachable, members still fall back to each other."},
  {"q": "How can a replication loop arise?",
   "options": ["Only by forcing sync sources manually in a circle", "Automatically on every failover", "By enabling hidden members", "By lowering the oplog size"],
   "answer": 0,
   "explain": "Automatic selection picks sources that are ahead, so loops need a hand-forced replSetSyncFrom."},
  {"q": "A cheap disaster-recovery secondary should never become primary and never get client reads. Which options achieve this?",
   "options": ["priority: 0 and hidden: true", "votes: 5", "buildIndexes: true only", "arbiterOnly: true"],
   "answer": 0,
   "explain": "priority 0 blocks elections and hidden hides it from drivers."},
  {"q": "Why set votes: 0 on the cheap member of a two-member set?",
   "options": ["So the primary can keep its majority if the cheap member fails", "To make it faster", "To make it the primary", "To disable the oplog"],
   "answer": 0,
   "explain": "With two voters, losing either member loses the majority and the primary would step down."}
]
```

> **Source:** MongoDB: The Definitive Guide 3e, ch. 12-13 (topics only; wording and examples are original). MongoDB Manual: https://www.mongodb.com/docs/manual/reference/connection-string/ , https://www.mongodb.com/docs/manual/core/retryable-writes/ , https://www.mongodb.com/docs/manual/tutorial/perform-maintence-on-replica-set-members/ , https://www.mongodb.com/docs/manual/reference/replica-states/
