# NoSQL and Redis caching

> **Before this lesson:** you should know what a relational database, a transaction and a commit are
> ([lesson 16](#/lesson/fastapi/sql-sqlmodel)), how the lifespan and dependencies supply shared
> resources ([lesson 11](#/lesson/fastapi/yield-deps)) and the HTTP caching headers from
> [lesson 1](#/lesson/fastapi/http-basics). No knowledge of Redis is assumed. For a full course on
> it, see [What Redis is](#/lesson/redis/what-is-redis) in the Redis track.

## In plain words

A relational database is careful and general, and that care costs time. Many things a web service
does again and again do not need it: "what did this slow query return ten seconds ago?", "how many
requests has this client made in the last minute?" For those, the answer should come back in well
under a millisecond.

A **cache** is a small, fast store that keeps copies of answers which are slow to produce, so that
the same question does not have to be answered from scratch each time.

An everyday picture: a cook's worktop. The pantry (the database) holds everything, properly
labelled, a walk away. The cook keeps the salt, the oil and today's chopped onions within arm's
reach. The worktop is small, things on it go off and must be replaced, and nobody would keep the
restaurant's only copy of anything there. But it is why dinner arrives in ten minutes and not an
hour. The technical questions in this lesson are the worktop questions: what to keep there, for how
long, and what to do when the pantry's contents change.

This lesson first gives a map of the databases that are *not* relational, then goes deep on the one
you will use in nearly every FastAPI service: **Redis**, for caching, rate limiting and
coordination between workers.

Why this matters for a job: "design caching for a slow endpoint" is a standard interview exercise,
and the failure modes named here (stale data, stampede, wrong cache key) are real production
incidents.

## The NoSQL landscape

Relational databases are the default for good reasons: transactions, constraints, flexible queries.
Lubanovic's chapter 14 surveys the alternatives because real systems combine several stores. The
alternatives are grouped under the loose name **NoSQL**, which means "not built around tables and
SQL".

| Family | Examples | Data model | Typical use |
|---|---|---|---|
| Key-value | **Redis**, Memcached, DynamoDB | key → value (Redis: rich structures) | caches, sessions, counters, queues |
| Document | **MongoDB**, Couchbase | JSON-like documents in collections | flexible/nested records, catalogs |
| Wide-column | **Cassandra**, ScyllaDB | partitioned rows, tunable consistency | huge write volumes, time series |
| Search | **Elasticsearch**, OpenSearch | inverted indexes over documents | full-text search, log analytics |
| Graph | Neo4j | nodes and edges | relationships, recommendations |
| Vector | pgvector, Qdrant, Milvus | embeddings + ANN index | semantic search, RAG |

Some terms in the table: a *document* is a JSON-like record whose fields can vary from one record to
the next; an *inverted index* maps each word to the documents containing it, which is what makes text
search fast; an *embedding* is a list of numbers that represents the meaning of a text or image, and
*ANN* (approximate nearest neighbour) is the technique for finding similar ones quickly.

The book also points to a trend that simplifies matters: SQL databases have absorbed many NoSQL
features. PostgreSQL's **JSONB** column type stores and indexes JSON documents, and its full-text
search and the `pgvector` extension cover many search and embedding needs. Starting with PostgreSQL
and adding a specialised store only when measurement shows a need is a sound default.

The trade-offs you should be able to state: NoSQL stores typically give up joins (combining tables
in one query), transactions spanning several records, or strict consistency, in return for the
ability to spread over many machines, freedom in the shape of records, or raw speed. The **CAP
theorem** describes the multi-machine part: when the network between a system's machines fails, the
system must choose between *consistency* (every reader sees the latest write) and *availability*
(every request gets an answer).

Async Python clients exist for all of these (`redis.asyncio`, async PyMongo, the async Elasticsearch
client), and they fit into FastAPI in the same way as a SQL engine: create the client in the
**lifespan**, and hand it out through a **dependency**.

## Redis in five minutes

**Redis** is a server that keeps data in memory, organised as ready-made structures, each stored
under a name called a **key**. It executes commands one at a time on a single thread. A command
therefore runs from start to finish with nothing else in between; it is **atomic**. Typical response
times are below a millisecond, and saving to disk is optional. The main types:

| Type | Commands | Use |
|---|---|---|
| String | `GET`, `SET key val EX 60 NX`, `INCR` | cache entries, counters, locks |
| Hash | `HSET`, `HGETALL` | objects, per-user fields |
| List | `LPUSH`, `BRPOP` | simple queues |
| Set / Sorted set | `SADD`, `ZADD`, `ZRANGEBYSCORE` | membership, leaderboards, sliding-window rate limits |
| Stream | `XADD`, `XREADGROUP` | durable event logs, job queues |
| Pub/Sub | `PUBLISH`, `SUBSCRIBE` | fan-out notifications (e.g. WebSocket broadcast across workers) |

In the first row, `SET key val EX 60 NX` means "store this value, let it expire after 60 seconds
(`EX`), and only if the key does not exist yet (`NX`)". A time limit on a key is called a **TTL**
(time to live).

Connecting Redis to FastAPI follows the pattern of lesson 11:

```python
import redis.asyncio as redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = redis.from_url(settings.redis_url, decode_responses=True)
    yield
    await app.state.redis.aclose()

def get_redis(request: Request) -> redis.Redis:
    return request.app.state.redis

RedisDep = Annotated[redis.Redis, Depends(get_redis)]
```

One client is created at start-up, stored on `app.state` and closed at shut-down. The dependency
`get_redis` hands it to endpoints, and `RedisDep` is the usual short alias.

## Caching patterns

Caching exchanges **freshness** for **speed and reduced load**. Lubanovic lists caches first among
the performance tools in his production chapter, with the standing warning that deciding when a
cached copy is out of date is famously hard. Removing or replacing an out-of-date copy is called
**invalidation**.

### Cache-aside (lazy loading)

In the **cache-aside** pattern the application does the work itself: look in the cache; if the
answer is there (a **hit**), return it; if not (a **miss**), load it from the database and store a
copy.

```python
@app.get("/items/{item_id}", response_model=ItemPublic)
async def read_item(item_id: int, r: RedisDep, session: SessionDep):
    key = f"item:v1:{item_id}"
    if (cached := await r.get(key)) is not None:
        return ItemPublic.model_validate_json(cached)             # hit
    item = await session.get(Item, item_id)                       # miss -> database
    if item is None:
        raise HTTPException(404, "Item not found")
    public = ItemPublic.model_validate(item)
    await r.set(key, public.model_dump_json(), ex=300)            # TTL 5 minutes
    return public

@app.patch("/items/{item_id}")
async def update_item(item_id: int, patch: ItemUpdate, r: RedisDep, session: SessionDep):
    ...                                    # update DB, commit
    await r.delete(f"item:v1:{item_id}")   # invalidate AFTER the commit
```

Reading the first endpoint:

- `key = f"item:v1:{item_id}"` builds the cache key: the kind of thing, a version, and the id.
- `await r.get(key)` asks Redis. If something comes back, it is parsed into the response model and
  returned. The database is never touched. (The `:=` operator assigns and tests in one step.)
- On a miss the item is read from the database, or a 404 is raised.
- `r.set(key, ..., ex=300)` stores the JSON for 300 seconds.

The second endpoint shows the write path: update the database, commit, and *then* delete the cache
key, so that the next read fetches fresh data. Why the order matters is shown later in the lesson.

A runnable model of cache-aside with expiry, counting hits and database queries:

```python-run
import json, time

class FakeRedis:
    def __init__(self): self.d = {}
    def get(self, k, now):
        v = self.d.get(k)
        if v and v[1] > now: return v[0]
        self.d.pop(k, None)
    def set(self, k, v, ex, now): self.d[k] = (v, now + ex)
    def delete(self, k): self.d.pop(k, None)

DB = {1: {"id": 1, "name": "hammer", "price": 9.5}}
db_queries = hits = 0
cache = FakeRedis()

def slow_db_get(item_id):
    global db_queries
    db_queries += 1
    return DB.get(item_id)

def read_item(item_id, now):
    global hits
    key = f"item:v1:{item_id}"
    cached = cache.get(key, now)
    if cached is not None:
        hits += 1
        return json.loads(cached)
    item = slow_db_get(item_id)
    if item is not None:
        cache.set(key, json.dumps(item), ex=300, now=now)
    return item

for t in range(0, 1000, 10):            # one read every 10 seconds
    read_item(1, now=t)
print(f"100 reads -> {db_queries} DB queries, {hits} cache hits")

DB[1]["price"] = 11.0                   # write path: update DB, then invalidate
print("stale without invalidation:", read_item(1, now=1001)["price"])
cache.delete("item:v1:1")
print("fresh after invalidation  :", read_item(1, now=1002)["price"])
```

`FakeRedis` stores each value together with its expiry time; `get` returns nothing once that time
has passed. `read_item` is the cache-aside logic, with the current time passed in as `now` so that
the demo does not have to wait in real time. The loop performs one read every 10 simulated seconds
for 1,000 seconds.

The first line of output is `100 reads -> 4 DB queries, 96 cache hits`: the database was asked only
at seconds 0, 300, 600 and 900, each time the 300-second entry had expired. Then the price is
changed in the database. The next read prints `9.5`, the old price: the cached copy is **stale**.
After `cache.delete(...)` the following read prints `11.0`.

### Other strategies

- **Write-through**: every write updates the cache and the database together. Reads are always
  fresh; writes are slower.
- **Write-behind**: write to the cache now and to the database a little later. Fast, with a risk of
  losing data.
- **Read-through**: a library or proxy performs the load-on-miss for you.
- **HTTP caching**: let *clients and CDNs* keep copies, using `Cache-Control` and `ETag` (lesson 1).
  A CDN (content delivery network) is a fleet of servers near users that stores copies of responses.
  The cheapest request is the one that never reaches you.
- **In-process caches** (`functools.lru_cache`, `cachetools.TTLCache`): no network hop at all, but
  each worker process has its own copy, and the copies drift apart. Fine for small reference data
  that changes slowly. The problem *LRU Response Cache with TTL* builds one.

### Cache keys

A key must include **everything that changes the answer**: the resource id, the relevant query
parameters, the caller's identity or customer account if the response is personal, and a
**version** segment, so that a release which changes the shape of the data does not read old
entries. Leaving the user out of the key is a data leak: user B is shown user A's cached response.

For machine-learning predictions:
`key = f"pred:{model_version}:{sha256(canonical_json(features))}"`. Include the model version, and
hash a canonical form of the input (the same input always written the same way).

### What goes wrong

| Problem | What it is | Mitigation |
|---|---|---|
| Stale data | cache outlives the truth | TTLs; invalidate on write; versioned keys |
| **Stampede** (thundering herd) | a hot key expires; 1,000 requests all recompute it | per-key lock/single-flight; stale-while-revalidate; jittered TTLs |
| Penetration | repeated lookups for keys that don't exist always hit the DB | cache negative results briefly; Bloom filter |
| Avalanche | many keys expire at once | add random jitter to TTLs |
| Hot key / big value | one key dominates load or is MBs large | local cache tier; split value |
| Memory exhaustion | cache grows without bound | `maxmemory` + eviction policy (`allkeys-lru`/`lfu`) |
| Cache as source of truth | data only in cache gets evicted | cache must be rebuildable |

The stampede deserves a demonstration. The cure is **single-flight**: when many requests miss the
same key at the same moment, only one recomputes the value and the rest wait for its result.

```python-run
import asyncio

cache, inflight, computations = {}, {}, 0

async def expensive(key):
    global computations
    computations += 1
    await asyncio.sleep(0.05)             # slow DB query / model call
    return f"value-of-{key}"

async def get(key):
    if key in cache:
        return cache[key]
    if key not in inflight:               # first caller starts the computation
        inflight[key] = asyncio.ensure_future(expensive(key))
    try:
        value = await inflight[key]       # everyone awaits the same future
    finally:
        inflight.pop(key, None)
    cache[key] = value
    return value

results = await asyncio.gather(*(get("hot") for _ in range(100)))
print(f"100 concurrent requests -> {computations} computation(s)")
```

`get` first checks the cache. If the key is absent and nobody is computing it, the caller starts the
computation and records it in `inflight`. Every caller, the first included, then awaits that same
in-progress computation. One hundred requests arrive together, and the output is
`100 concurrent requests -> 1 computation(s)`. Without the `inflight` dictionary, all hundred would
have run the slow query.

## Redis beyond caching

- **Rate limiting**: `INCR` plus `EXPIRE` for each client and time window, or a token bucket in a
  small script. The count is shared by all workers and replicas, which a limiter inside one process
  is not.
- **Idempotency keys**: `SET idem:{key} in_progress NX EX 86400` is an atomic "claim" (see the
  problem *Idempotency-Key Store*).
- **Distributed locks**: `SET lock:x token NX PX 30000`, released by a script that deletes the key
  only if it still holds your token.
- **Sessions and token deny-lists**: IDs of cancelled login tokens, each with a TTL equal to the
  token's remaining life.
- **Task queues**: Celery, RQ and Arq use Redis to hold their jobs.
- **Pub/Sub** (publish/subscribe): pass WebSocket messages on to clients connected to other workers.

The atomicity of `SET ... NX` is what makes these safe. Two workers racing for the same key cannot
both win, because Redis runs one command at a time.

> [!INTERVIEW]
> "Design caching for a slow endpoint." — First ask how stale the data may be and whether responses
> are per-user. Use cache-aside in Redis with a key that includes everything affecting the result
> (ids, parameters, user or customer, version) and a TTL with some random variation. Invalidate on
> writes, after the commit. Protect against stampedes with single-flight or by serving the old value
> while refreshing, cache "not found" results briefly, limit memory with an eviction policy, and
> record hit and miss counts. Add HTTP caching headers (`Cache-Control`, `ETag`) so that clients and
> CDNs can skip the request entirely. Treat the cache as disposable.

## Why invalidate *after* commit: the race, replayed

"Delete the cache key after the database commit" sounds fussy until you interleave two requests by
hand. The simulation runs the same writer and the same reader in the two possible orders:

```python-run
def run(order):
    db, cache, log = {"price": 10}, {"price": 10}, []
    pending = {}

    def writer_invalidate():  cache.pop("price", None); log.append("W: delete cache key")
    def writer_begin():       pending["price"] = 12;    log.append("W: UPDATE price=12 (not committed)")
    def writer_commit():      db.update(pending);       log.append("W: COMMIT")
    def reader():
        if "price" in cache:
            log.append(f"R: cache hit {cache['price']}")
        else:
            cache["price"] = db["price"]                 # reads COMMITTED data only
            log.append(f"R: cache miss -> read db ({db['price']}) -> repopulate cache")

    steps = {"invalidate-then-commit": [writer_begin, writer_invalidate, reader, writer_commit],
             "commit-then-invalidate": [writer_begin, reader, writer_commit, writer_invalidate]}[order]
    for step in steps:
        step()
    print(f"[{order}]")
    print("   " + "\n   ".join(log))
    print(f"   final: db={db['price']} cache={cache.get('price', '(empty)')}",
          "<- STALE until TTL expires" if cache.get("price") not in (None, db["price"]) else "<- consistent")

run("invalidate-then-commit")
run("commit-then-invalidate")
```

The writer has three steps (change the price without committing, commit, delete the cache key) and
the reader has one (use the cache, or on a miss read the *committed* value from the database and
store it). `run` executes the steps in a given order and prints a log.

In the first ordering, **invalidate-then-commit**, the log shows the reader arriving between the
delete and the commit. It finds the cache empty, reads the *old* committed price of 10 and writes it
back into the cache. Then the writer commits 12. The final line reads `db=12 cache=10`, marked
`STALE until TTL expires`, even though the writer "did invalidate".

In the second ordering, **commit-then-invalidate**, the reader gets a cache hit of 10 for a moment
before the delete, and the final state is `db=12 cache=(empty)`, marked `consistent`. The next read
will load the fresh value.

A narrower race remains even with the correct order: a reader that fetched the old row a moment
before the commit may write it into the cache a moment after the delete. That is why invalidation is
always paired with a **TTL as a safety net**, and why systems that cannot tolerate any staleness
either skip the cache for that data or use versioned keys.

## Reading cached data safely with Pydantic

Whatever comes out of a cache is, strictly speaking, untrusted input. It may have been written by an
older release with a different shape. Validate when reading, and treat a failure as a miss:

```python-run
from pydantic import BaseModel, ValidationError

class ItemV2(BaseModel):
    id: int
    name: str
    price_cents: int                         # v1 stored a float 'price' instead

cache = {
    "item:v2:1": '{"id": 1, "name": "hammer", "price_cents": 950}',
    "item:v2:2": '{"id": 2, "name": "saw", "price": 12.0}',     # written by the previous release
    "item:v2:3": '{"id": 3, "name": "drill", "price_cen',       # truncated / corrupt
}

def cached_item(item_id, load_from_db):
    raw = cache.get(f"item:v2:{item_id}")
    if raw is not None:
        try:
            return ItemV2.model_validate_json(raw), "hit"
        except ValidationError:
            cache.pop(f"item:v2:{item_id}")              # poisoned entry: drop it and fall through
    item = load_from_db(item_id)
    cache[f"item:v2:{item_id}"] = item.model_dump_json()
    return item, "miss -> reloaded"

db = lambda i: ItemV2(id=i, name=f"item{i}", price_cents=100 * i)
for i in (1, 2, 3, 4):
    item, how = cached_item(i, db)
    print(i, how, item.price_cents)
```

The cache holds three entries: one valid, one written by a previous release (it has `price` where
the current model wants `price_cents`), and one cut off in the middle. `cached_item` tries to
validate what it finds; on a `ValidationError` it deletes the entry and falls through to the
database.

The output: item 1 is a `hit` with 950; items 2 and 3 are `miss -> reloaded` with 200 and 300,
because their entries failed validation; item 4 was never cached and is loaded with 400. No
exception reached the caller.

Changing the version segment of the key (`item:v2:` to `item:v3:`) at every change of shape is
cleaner still: the new release never sees the old entries, and those are left to expire.

## A fixed-window limiter and its edge problem

A **rate limiter** restricts how many requests a client may make in a period. Redis's `INCR` and
`EXPIRE` give the easiest limiter that is shared between workers: count the requests in the current
minute. Its well-known weakness lies at the boundary between two minutes. A sliding window removes
the weakness at the cost of remembering more:

```python-run
from collections import defaultdict, deque

class FixedWindow:
    def __init__(self, limit, window): self.limit, self.window, self.counts = limit, window, defaultdict(int)
    def allow(self, now):
        bucket = int(now // self.window)                 # INCR rl:{client}:{bucket}; EXPIRE window
        self.counts[bucket] += 1
        return self.counts[bucket] <= self.limit

class SlidingWindowLog:
    def __init__(self, limit, window): self.limit, self.window, self.log = limit, window, deque()
    def allow(self, now):
        while self.log and self.log[0] <= now - self.window:      # ZREMRANGEBYSCORE
            self.log.popleft()
        if len(self.log) < self.limit:                            # ZCARD
            self.log.append(now)                                  # ZADD
            return True
        return False

# 10 requests just before the minute boundary and 10 just after
burst = [59.0 + i * 0.09 for i in range(10)] + [60.0 + i * 0.09 for i in range(10)]
for limiter in (FixedWindow(10, 60), SlidingWindowLog(10, 60)):
    allowed = sum(limiter.allow(t) for t in burst)
    print(f"{type(limiter).__name__:17} limit 10/min -> allowed {allowed} requests within 2 seconds")
```

`FixedWindow` counts requests per numbered minute (`int(now // 60)`). `SlidingWindowLog` keeps the
times of recent requests, discards those older than 60 seconds, and allows a request only if fewer
than the limit remain. The test sends 10 requests in the last second of one minute and 10 in the
first second of the next.

The output: `FixedWindow` allowed **20** requests within two seconds, twice the limit, because the
counter started again at the boundary. `SlidingWindowLog` allowed **10**.

In Redis, the sliding log is one sorted set per client, with timestamps as the scores. A token
bucket (lesson 20) kept in a hash and updated by a small script gives the same smoothness with a
fixed, small amount of memory. Whichever you choose, reading the count, deciding and writing it back
must be **atomic**: done in a server-side script (Redis runs scripts written in the Lua language) or
a `MULTI`/`EXEC` block. Otherwise two workers can both read "9 used" and both allow the tenth
request.

## Choosing a store: a decision guide

| Need | Reach for | Because |
|---|---|---|
| Transactions, joins, constraints, ad-hoc queries | PostgreSQL | the relational default |
| Semi-structured attributes on relational rows | PostgreSQL `JSONB` | no second system to operate |
| Sub-millisecond lookups, counters, TTLs, locks | Redis | in-memory, atomic commands |
| Full-text relevance search, faceting, log search | Elasticsearch / OpenSearch (or Postgres FTS at small scale) | inverted indexes and scoring |
| Similarity search over embeddings | pgvector first; a dedicated vector DB at larger scale | approximate nearest-neighbour indexes |
| Enormous write throughput across regions | Cassandra / DynamoDB | partitioned, tunable consistency |
| Large binary objects | object storage (S3-compatible) | cheap, durable; keep only metadata in the DB |
| Durable event stream between services | Kafka / Redis Streams | ordered, replayable log |

Every additional store is one more thing to back up, monitor, secure and keep in agreement with the
others, and **no transaction spans two stores**. If you write to PostgreSQL and then to
Elasticsearch, the first can succeed and the second fail. The standard remedy is the *outbox
pattern*: write the change and an "event to publish" row in the same database transaction, and let
a background process deliver those events to the other systems, retrying until they arrive.

## Pitfalls

- Caching personal responses under a shared key.
- Invalidating before the database commit (a reader arriving in between stores the old value again).
- `lru_cache` on a function that takes a database session or a request object. Every call has
  different arguments, so nothing is ever reused, or worse, stale objects are kept for ever.
- No TTL at all, on the theory that invalidation will be perfect. It will not be.
- Creating a Redis connection for each request instead of one pooled client in the lifespan.
- The blocking `redis` client inside `async def` endpoints. Use `redis.asyncio`.

## Summary

- NoSQL families give up relational guarantees for scale, flexibility or speed; PostgreSQL covers
  many of their uses with JSONB, full-text search and pgvector.
- Redis offers in-memory structures with atomic commands: caches, counters, locks, queues, pub/sub.
- Cache-aside with a TTL, invalidating after the commit, is the workhorse pattern; design keys with
  care.
- Guard against stampedes, lookups for missing keys, mass expiry and unlimited memory growth.

## Glossary

- **NoSQL** — the family of databases not built around tables and SQL.
- **Key-value store** — a database that keeps each value under a name (the key).
- **Redis** — an in-memory data-structure server used for caches, counters, locks and queues.
- **Cache** — a fast store of copies of answers that are slow to produce.
- **Hit / miss** — the answer was in the cache / it was not.
- **TTL (time to live)** — how long an entry is kept before it expires.
- **Stale** — a cached copy that no longer matches the source.
- **Invalidation** — removing or replacing a cached copy when the source changes.
- **Cache-aside** — the application checks the cache, loads on a miss, and stores the result.
- **Stampede** — many requests recomputing the same expired entry at once.
- **Single-flight** — letting one request compute a value while the others wait for it.
- **Atomic** — executed completely, with nothing else able to run in the middle.
- **Eviction** — the cache discarding entries to stay within its memory limit.
- **CAP theorem** — during a network failure a distributed system must choose consistency or
  availability.
- **JSONB** — PostgreSQL's indexed column type for JSON documents.
- **Rate limiter** — a mechanism that caps requests per client per period.
- **Fixed / sliding window** — counting per calendar interval / counting over the most recent
  interval.
- **Outbox pattern** — recording events in the same transaction as the data, for reliable delivery
  to other systems.

```quiz
[
  {"q": "In the cache-aside pattern, what happens on a cache miss?", "options": ["Return 404", "The application loads from the database and stores the result in the cache", "Redis queries the database itself", "The request is retried"], "answer": 1,
   "explain": "The application code owns both the lookup and the population of the cache."},
  {"q": "A cached response differs per user but the key is 'profile'. What bug results?", "options": ["Lower hit rate", "Users can receive another user's data", "Redis runs out of memory", "TTL is ignored"], "answer": 1,
   "explain": "Keys must include everything that changes the response, including the user or tenant."},
  {"q": "What is a cache stampede?", "options": ["Too many keys", "Many requests simultaneously recomputing the same expired hot key", "A Redis crash", "Keys with no TTL"], "answer": 1,
   "explain": "When a popular entry expires, concurrent misses all hit the backend; single-flight locks or stale-while-revalidate prevent it."},
  {"q": "Why does 'SET key value NX EX 60' work as a distributed claim/lock?", "options": ["NX encrypts the value", "Redis executes commands atomically, so only one client can set a key that doesn't exist", "EX makes it permanent", "It uses transactions across databases"], "answer": 1,
   "explain": "NX sets only if absent; single-threaded command execution guarantees exactly one winner. EX prevents a crashed holder from locking forever."},
  {"q": "Why is functools.lru_cache a poor fit for shared response caching in a 4-worker deployment?", "options": ["It is slow", "Each worker process has its own independent cache, so entries and invalidations are not shared", "It cannot cache strings", "It requires Redis"], "answer": 1,
   "explain": "In-process caches are per process; workers drift apart and invalidation reaches only one of them."},
  {"q": "When should a cache entry be invalidated on update?", "options": ["Before writing to the DB", "After the database commit succeeds", "Never", "Only at midnight"], "answer": 1,
   "explain": "Invalidating before commit lets a concurrent reader re-cache the old value; delete after commit."},
  {"q": "Which PostgreSQL feature lets it cover many document-store use cases?", "options": ["VACUUM", "JSONB columns with indexing", "WAL", "Foreign keys"], "answer": 1,
   "explain": "JSONB stores schemaless documents with GIN indexes, giving document-database features inside SQL."}
]
```

> **Source:** Lubanovic, *FastAPI*, ch. 14 "Databases, Data Science, and a Little AI" (Data Storage Alternatives, Nonrelational (NoSQL) Databases, Redis, MongoDB, Cassandra, Elasticsearch, NoSQL Features in SQL Databases) and ch. 13 "Production" (Caches); https://redis.io/docs/latest/develop/; https://fastapi.tiangolo.com/advanced/events/
