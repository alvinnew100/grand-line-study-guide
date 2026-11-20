# NoSQL and Redis caching

Relational databases are the default for good reasons — transactions, constraints, flexible queries. But
Lubanovic's chapter 14 surveys the alternatives because real systems mix stores: a relational source of
truth, a key-value cache in front, a search engine beside it, maybe a document or vector store. This
lesson gives you the map, then goes deep on the one you'll use in nearly every FastAPI service:
**Redis**, for caching, rate limiting, idempotency and queues.

## The NoSQL landscape

| Family | Examples | Data model | Typical use |
|---|---|---|---|
| Key-value | **Redis**, Memcached, DynamoDB | key → value (Redis: rich structures) | caches, sessions, counters, queues |
| Document | **MongoDB**, Couchbase | JSON-like documents in collections | flexible/nested records, catalogs |
| Wide-column | **Cassandra**, ScyllaDB | partitioned rows, tunable consistency | huge write volumes, time series |
| Search | **Elasticsearch**, OpenSearch | inverted indexes over documents | full-text search, log analytics |
| Graph | Neo4j | nodes and edges | relationships, recommendations |
| Vector | pgvector, Qdrant, Milvus | embeddings + ANN index | semantic search, RAG |

The book also points out a trend that simplifies architecture: SQL databases have absorbed NoSQL features.
PostgreSQL's **JSONB** columns store and index documents; full-text search and `pgvector` cover many
search and embedding needs. Reaching for PostgreSQL first and adding a specialised store when a measured
need appears is a sound default.

Trade-offs to be able to articulate: NoSQL stores typically give up joins, multi-row transactions or
strong consistency in exchange for horizontal scale, schema flexibility or raw speed. The **CAP theorem**
frames the distributed part: under a network partition a system must choose between consistency and
availability.

Async Python clients exist for all of them (`redis.asyncio`, `motor`/PyMongo async, `elasticsearch[async]`),
and they slot into FastAPI the same way as a SQL engine: create the client in the **lifespan**, expose it
through a **dependency**.

## Redis in five minutes

Redis is an in-memory data-structure server: single-threaded command execution (so each command is
atomic), sub-millisecond latency, optional persistence. Core types:

| Type | Commands | Use |
|---|---|---|
| String | `GET`, `SET key val EX 60 NX`, `INCR` | cache entries, counters, locks |
| Hash | `HSET`, `HGETALL` | objects, per-user fields |
| List | `LPUSH`, `BRPOP` | simple queues |
| Set / Sorted set | `SADD`, `ZADD`, `ZRANGEBYSCORE` | membership, leaderboards, sliding-window rate limits |
| Stream | `XADD`, `XREADGROUP` | durable event logs, job queues |
| Pub/Sub | `PUBLISH`, `SUBSCRIBE` | fan-out notifications (e.g. WebSocket broadcast across workers) |

Wiring into FastAPI:

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

## Caching patterns

Caching trades **freshness** for **speed and load reduction**. Lubanovic lists caches first among the
performance tools in his production chapter — with the standing caveat that cache invalidation is one of
the famously hard problems.

### Cache-aside (lazy loading)

The application owns the logic: look in the cache; on a miss, load from the source and store it.

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

A runnable model of cache-aside with TTL and hit-rate accounting:

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

### Other strategies

- **Write-through**: every write updates cache and DB together — fresh reads, slower writes.
- **Write-behind**: write to cache, flush to DB asynchronously — fast, risk of loss.
- **Read-through**: a library/proxy loads on miss transparently.
- **HTTP caching**: let *clients and CDNs* cache with `Cache-Control` and `ETag` — the cheapest request is
  the one that never reaches you.
- **In-process caches** (`functools.lru_cache`, `cachetools.TTLCache`): zero network hops, but per-worker
  (each process has its own copy and they drift) — fine for small, slowly changing reference data.
  The problem *LRU Response Cache with TTL* builds one.

### Cache keys

A key must include **everything that changes the answer**: resource id, relevant query parameters, the
caller's identity or tenant if the response is personalised, and a schema/model **version** prefix so a
deploy that changes the shape doesn't read old entries. Forgetting the user in the key is a data-leak bug
(user B sees user A's cached response).

For ML inference: `key = f"pred:{model_version}:{sha256(canonical_json(features))}"` — include the model
version, hash a canonical serialisation of the input.

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

Single-flight in asyncio — only one coroutine recomputes, the others await its result:

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

## Redis beyond caching

- **Rate limiting**: `INCR` + `EXPIRE` per client per window, or a token bucket in a Lua script — shared
  across all workers and replicas (an in-process limiter isn't).
- **Idempotency keys**: `SET idem:{key} in_progress NX EX 86400` is an atomic "claim" (see the problem
  *Idempotency-Key Store*).
- **Distributed locks**: `SET lock:x token NX PX 30000`, release with a compare-and-delete script.
- **Sessions / token deny-lists**: revoked JWT IDs with TTL equal to remaining token lifetime.
- **Task queues**: Celery, RQ and Arq use Redis as a broker.
- **Pub/Sub**: broadcast WebSocket messages to clients connected to different workers.

The atomicity of `SET ... NX` (set only if not exists) is what makes these safe: two workers racing for
the same key can't both win, because Redis executes commands one at a time.

> [!INTERVIEW]
> "Design caching for a slow endpoint." — Clarify freshness tolerance and whether responses are
> per-user. Use cache-aside in Redis with a key that includes everything affecting the result (ids, params,
> user/tenant, version) and a TTL with jitter. Invalidate on writes after commit. Protect against
> stampedes with single-flight or stale-while-revalidate, cache negative results briefly, bound memory
> with an eviction policy, and emit hit/miss metrics. Add HTTP caching headers (`Cache-Control`, `ETag`)
> so clients and CDNs can avoid the request entirely. Treat the cache as disposable.

## Why invalidate *after* commit: the race, replayed

"Delete the cache key after the database commit" sounds like pedantry until you interleave two requests
by hand. The simulation runs the same writer and reader with the two possible orderings:

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

In the first ordering a reader slips in between the delete and the commit, finds the cache empty, reads
the *old* committed value and writes it back — and the cache now holds stale data for a full TTL even
though the writer "did invalidate". In the second, the worst case is that a reader sees the old value for
the instant before the delete, after which the next read repopulates from fresh data.

A narrower race remains even with the correct order (a reader that fetched the old row just before the
commit may write it to the cache just after the delete). That is why invalidation is always paired with
a **TTL as a safety net**, and why systems that can't tolerate any staleness either skip the cache for
that data or use versioned keys.

## Reading cached data safely with Pydantic

Whatever comes out of a cache is, strictly speaking, untrusted input: it may have been written by an
older release with a different schema. Validate on read and treat failure as a miss:

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

Bumping the version segment of the key (`item:v2:` → `item:v3:`) on every schema change is cleaner still:
the new release never sees old entries, and the old ones simply expire.

## A fixed-window limiter and its edge problem

Redis's `INCR` + `EXPIRE` gives the simplest shared rate limiter. Its well-known weakness is the window
boundary; a sliding window fixes it at the cost of more state:

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

The fixed window lets through twice the limit across the boundary. In Redis the sliding log is a sorted
set per client (timestamps as scores); a token bucket stored in a hash and updated by a small Lua script
gives the same smoothness with O(1) memory. Whichever you choose, the read-modify-write must be **atomic**
— a Lua script or `MULTI/EXEC` — otherwise two workers can both read "9 used" and both allow the tenth
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

Every additional store is another thing to back up, monitor, secure and keep consistent with the others,
and **there are no transactions across stores**: if you write to PostgreSQL and then to Elasticsearch, one
can succeed and the other fail. The standard remedy is the *outbox pattern* — write the change and an
"event to publish" row in the same database transaction, and let a background process deliver events to
the other systems with retries.

## Pitfalls

- Caching personalised responses under a shared key.
- Invalidating before the DB commit (a concurrent reader repopulates the old value).
- `lru_cache` on a function taking a DB session or request object (unhashable/every call differs — or
  worse, it caches per-session garbage forever).
- No TTL at all ("we'll invalidate perfectly") — you won't.
- Creating a Redis connection per request instead of a pooled client in lifespan.
- Blocking `redis` (sync) client inside `async def` endpoints — use `redis.asyncio`.

## Summary

- NoSQL families trade relational guarantees for scale/flexibility/speed; PostgreSQL covers many cases
  with JSONB, full-text search and pgvector.
- Redis: in-memory structures with atomic commands — caches, counters, locks, queues, pub/sub.
- Cache-aside with TTL + invalidate-after-commit is the workhorse pattern; design keys carefully.
- Guard against stampedes, penetration, avalanches and unbounded memory.

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
