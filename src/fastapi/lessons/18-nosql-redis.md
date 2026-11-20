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
