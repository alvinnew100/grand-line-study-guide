TRACK = dict(
    id="redis",
    title="Redis in Action",
    icon="🟥",
    color="#d82c20",
    group="Data & Databases",
    blurb="Redis from zero to production: data structures, caching, persistence and replication, queues, locks, "
          "search, a social feed, memory tuning, scaling, Lua scripting, streams, Cluster, vector search and "
          "the caching and rate-limiting patterns interviews ask about - every idea with a runnable simulation.",
    sources=[
        "Josiah L. Carlson, Redis in Action (Manning, 2013), ch. 1-11",
        "Redis documentation (redis.io/docs): data types, persistence, replication, Sentinel, Cluster specification, "
        "streams, ACLs, client-side caching, eviction, programmability, vector search",
    ],
    modules=[
        dict(
            id="getting-started",
            title="1. Getting to Know Redis",
            summary="What Redis is, the five core data structures, and a first vote-ranked application.",
            lessons=[
                dict(id="what-is-redis", title="What Redis is and the five core data structures", file="01-what-is-redis.md"),
                dict(id="first-app-voting", title="A first application: a proposal board with backing and ranking", file="02-first-app-voting.md"),
            ],
            problems=[],
        ),
        dict(
            id="web-application",
            title="2. Anatomy of a Redis Web Application",
            summary="Login sessions and cookies, shopping carts, page and row caching, lightweight analytics.",
            lessons=[
                dict(id="sessions-carts", title="Sessions, login cookies and shopping carts", file="03-sessions-carts.md"),
                dict(id="caching-analytics", title="Page caching, row caching and lightweight analytics", file="04-caching-analytics.md"),
            ],
            problems=["redis-expiring-store"],
        ),
        dict(
            id="commands",
            title="3. Commands in Depth",
            summary="Strings, lists, sets, hashes, sorted sets, publish/subscribe, SORT, MULTI/EXEC and key expiry.",
            lessons=[
                dict(id="strings-lists-sets", title="Commands in depth: strings, lists and sets", file="05-strings-lists-sets.md"),
                dict(id="hashes-sorted-sets", title="Commands in depth: hashes and sorted sets", file="06-hashes-sorted-sets.md"),
                dict(id="pubsub-transactions-expiry", title="Commands in depth: pub/sub, sorting, transactions and expiry", file="07-pubsub-transactions-expiry.md"),
            ],
            problems=["redis-list-commands", "redis-set-algebra", "redis-hash-commands", "redis-sorted-set", "redis-pubsub"],
        ),
        dict(
            id="safety-performance",
            title="4. Keeping Data Safe and Ensuring Performance",
            summary="RDB snapshots, the append-only file, replication, failure handling, WATCH, pipelining and measurement.",
            lessons=[
                dict(id="persistence", title="Keeping data safe: snapshots and the append-only file", file="08-persistence.md"),
                dict(id="replication-failures", title="Replication and handling failures", file="09-replication-failures.md"),
                dict(id="watch-pipelining-performance", title="Check-and-set with WATCH, pipelining, and measuring performance", file="10-watch-pipelining-performance.md"),
            ],
            problems=["redis-multi-exec-watch"],
        ),
        dict(
            id="application-support",
            title="5. Using Redis for Application Support",
            summary="Recent and common logs, time-bucket counters, running statistics, range lookups, service discovery, configuration.",
            lessons=[
                dict(id="logging-counters-stats", title="Application support: logging, counters and statistics", file="11-logging-counters-stats.md"),
                dict(id="ip-lookup-config", title="Application support: range lookups, service discovery and configuration", file="12-ip-lookup-config.md"),
            ],
            problems=["redis-unique-visitors"],
        ),
        dict(
            id="application-components",
            title="6. Application Components",
            summary="Autocomplete, distributed locks, counting semaphores, task queues, pull messaging, file distribution.",
            lessons=[
                dict(id="autocomplete-locks-semaphores", title="Autocomplete, distributed locks and counting semaphores", file="13-autocomplete-locks-semaphores.md"),
                dict(id="queues-messaging-files", title="Task queues, pull messaging and file distribution", file="14-queues-messaging-files.md"),
            ],
            problems=["redis-autocomplete", "redis-lock-fencing", "redis-counting-semaphore", "redis-delayed-queue", "redis-reliable-queue"],
        ),
        dict(
            id="search",
            title="7. Search-Based Applications",
            summary="Inverted indexes, AND/OR/NOT queries, sorted results, ad targeting by eCPM, skill matching.",
            lessons=[
                dict(id="inverted-index-search", title="Search with Redis: inverted indexes and sorted results", file="15-inverted-index-search.md"),
                dict(id="ad-targeting-job-search", title="Search with Redis: ad targeting and skill matching", file="16-ad-targeting-job-search.md"),
            ],
            problems=["redis-inverted-index"],
        ),
        dict(
            id="social-network",
            title="8. Building a Simple Social Network",
            summary="Users, posts, profile and home timelines, followers, fan-out on write, deletion, a streaming API.",
            lessons=[
                dict(id="users-timelines", title="Building a social network: users, posts and timelines", file="17-users-timelines.md"),
                dict(id="followers-streaming", title="Building a social network: following, fan-out, deletion and live streams", file="18-followers-streaming.md"),
            ],
            problems=["redis-timeline-fanout"],
        ),
        dict(
            id="memory",
            title="9. Reducing Memory Use",
            summary="Listpack and intset encodings, their thresholds, sharded hashes and sets, packing bits and bytes.",
            lessons=[
                dict(id="compact-encodings", title="Reducing memory use: compact encodings", file="19-compact-encodings.md"),
                dict(id="sharded-structures-bits", title="Reducing memory use: sharded structures and packing bits and bytes", file="20-sharded-structures-bits.md"),
            ],
            problems=["redis-bitmap-dau"],
        ),
        dict(
            id="scaling",
            title="10. Scaling Redis",
            summary="Read scaling with replicas, sharding for writes and memory, consistent hashing, queries across shards.",
            lessons=[
                dict(id="scaling-reads-writes", title="Scaling Redis: more reads, more writes, more memory", file="21-scaling-reads-writes.md"),
                dict(id="queries-on-shards", title="Scaling Redis: complex queries across shards", file="22-queries-on-shards.md"),
            ],
            problems=["redis-consistent-hash"],
        ),
        dict(
            id="lua",
            title="11. Scripting Redis with Lua",
            summary="EVAL, KEYS and ARGV, atomic scripts, script caching, and locks, semaphores and transactions rewritten in Lua.",
            lessons=[
                dict(id="lua-basics", title="Lua scripting: running your own logic inside Redis", file="23-lua-basics.md"),
                dict(id="lua-locks-semaphores", title="Lua scripting: rewriting locks, semaphores and transactions", file="24-lua-locks-semaphores.md"),
            ],
            problems=["redis-token-bucket"],
        ),
        dict(
            id="modern-redis",
            title="12. Modern Redis",
            summary="Streams and consumer groups, HyperLogLog, bitmaps, geospatial, Sentinel, Cluster and hash slots, ACLs, "
                    "client-side caching, Redis 6-8 changes, Redis as a vector store for RAG.",
            lessons=[
                dict(id="streams", title="Modern Redis: streams and consumer groups", file="25-streams.md"),
                dict(id="hll-bitmaps-geo", title="Modern Redis: HyperLogLog, bitmaps and geospatial indexes", file="26-hll-bitmaps-geo.md"),
                dict(id="cluster-sentinel", title="Modern Redis: Sentinel and Redis Cluster", file="27-cluster-sentinel.md"),
                dict(id="acl-csc-vector", title="Modern Redis: access control, client-side caching, modules and vector search", file="28-acl-csc-vector.md"),
            ],
            problems=["redis-stream-groups", "redis-hyperloglog", "redis-cluster-slot"],
        ),
        dict(
            id="caching-interview",
            title="13. Caching Patterns and Redis Interview Essentials",
            summary="Cache-aside, write-through, write-behind, TTL design, stampedes, eviction, hot keys, consistency, "
                    "rate limiters, leaderboards, lock limits, and when not to use Redis.",
            lessons=[
                dict(id="caching-patterns", title="Caching patterns: cache-aside, write-through, stampedes and eviction", file="29-caching-patterns.md"),
                dict(id="interview-essentials", title="Redis interview essentials: rate limiters, leaderboards, locks and limits", file="30-interview-essentials.md"),
            ],
            problems=["redis-cache-aside-stampede", "redis-lru-cache", "redis-lfu-cache", "redis-fixed-window-limiter",
                      "redis-sliding-log-limiter", "redis-leaderboard"],
        ),
    ],
)
