import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))


def _L(id, title, file):
    return dict(id=id, title=title, file=file)


_MODULES = [
    dict(
        id="from-zero",
        title="1. System design from zero",
        summary="Clients, servers and requests; the database, cache, load balancer, queue and CDN; scaling, latency, throughput, availability and consistency in plain words.",
        lessons=[
            _L("clients-servers-requests", "Clients, servers and requests: what a \"system\" is", "01-clients-servers-requests.md"),
            _L("core-components", "The five building blocks: database, cache, load balancer, queue and CDN", "02-databases-caches-balancers-queues.md"),
            _L("core-vocabulary", "The vocabulary of scale: scaling, latency, throughput, availability and consistency", "03-scaling-latency-availability-consistency.md"),
        ],
        problems=["sd-availability", "sd-lru-ttl-cache", "sd-load-balancer"],
    ),
    dict(
        id="scale-zero-to-millions",
        title="2. Scaling from zero to millions of users",
        summary="From one machine to a replicated, cached, multi-data-centre, sharded architecture, one justified step at a time.",
        lessons=[
            _L("scale-single-to-replicated", "Scaling from zero I: from one server to a replicated, cached system", "04-single-server-to-replicated.md"),
            _L("scale-stateless-to-sharded", "Scaling from zero II: stateless servers, data centres, queues, observability and sharding", "05-stateless-datacentres-queues-sharding.md"),
        ],
        problems=["sd-cache-aside-stampede", "sd-shard-router"],
    ),
    dict(
        id="estimation",
        title="3. Back-of-the-envelope estimation",
        summary="Powers of two, latency and availability numbers, and QPS, storage, bandwidth and server-count estimates worked step by step.",
        lessons=[
            _L("estimation-numbers", "Estimation I: the numbers worth memorising", "06-estimation-numbers.md"),
            _L("estimation-worked", "Estimation II: QPS, storage and bandwidth worked step by step", "07-estimation-worked.md"),
        ],
        problems=["sd-capacity-estimate"],
    ),
    dict(
        id="framework",
        title="4. A framework for the system design interview",
        summary="The four steps (scope, high-level design, deep dive, wrap-up), the time budget, dos and don'ts and a complete worked session.",
        lessons=[
            _L("framework-four-steps", "A framework for the interview I: the four steps", "08-framework-four-steps.md"),
            _L("framework-dos-donts", "A framework for the interview II: dos, don'ts and a complete worked session", "09-framework-dos-donts.md"),
        ],
        problems=[],
    ),
    dict(
        id="rate-limiter",
        title="5. Design a rate limiter",
        summary="Token bucket, leaky bucket, fixed window, sliding window log and sliding window counter; then the distributed design with shared counters, atomicity and failure policy.",
        lessons=[
            _L("rate-limiter-algorithms", "Design a rate limiter I: requirements and the five algorithms", "10-rate-limiter-algorithms.md"),
            _L("rate-limiter-distributed", "Design a rate limiter II: the distributed design", "11-rate-limiter-distributed.md"),
        ],
        problems=["sd-fixed-window", "sd-token-bucket", "sd-leaky-bucket", "sd-sliding-window-log", "sd-sliding-window-counter"],
    ),
    dict(
        id="consistent-hashing",
        title="6. Design consistent hashing",
        summary="The rehashing problem, the hash ring, virtual nodes, replication on the ring, and the alternatives: rendezvous hashing, jump hash and slot directories.",
        lessons=[
            _L("consistent-hashing-ring", "Design consistent hashing I: the rehashing problem and the ring", "12-consistent-hashing-ring.md"),
            _L("consistent-hashing-virtual-nodes", "Design consistent hashing II: virtual nodes, replication and alternatives", "13-consistent-hashing-virtual-nodes.md"),
        ],
        problems=["sd-consistent-hash-ring", "sd-rendezvous-hashing"],
    ),
    dict(
        id="key-value-store",
        title="7. Design a key-value store",
        summary="CAP, partitioning, replication, tunable quorums, vector clocks, gossip, hinted handoff, Merkle trees and the LSM storage engine.",
        lessons=[
            _L("kv-store-cap-replication", "Design a key-value store I: CAP, partitioning, replication and quorums", "14-kv-store-cap-replication.md"),
            _L("kv-store-versioning-failures", "Design a key-value store II: versioning, failure handling and the storage engine", "15-kv-store-versioning-failures.md"),
        ],
        problems=["sd-quorum-decision", "sd-vector-clock-compare", "sd-merkle-diff"],
    ),
    dict(
        id="unique-id",
        title="8. Design a unique ID generator",
        summary="Multi-master auto-increment, UUIDs, ticket servers and Snowflake-style IDs: bit layout, clocks, sequence overflow and machine-ID assignment.",
        lessons=[
            _L("unique-id-options", "Design a unique ID generator I: requirements and the four approaches", "16-unique-id-options.md"),
            _L("unique-id-snowflake", "Design a unique ID generator II: the Snowflake design in depth", "17-unique-id-snowflake.md"),
        ],
        problems=["sd-snowflake-id"],
    ),
    dict(
        id="url-shortener",
        title="9. Design a URL shortener",
        summary="Estimates, 301 vs 302, the data model, base-62 encoding, hashing with collision resolution, caching and abuse handling.",
        lessons=[
            _L("url-shortener-design", "Design a URL shortener I: requirements, API, data model and base 62", "18-url-shortener-design.md"),
            _L("url-shortener-deep-dive", "Design a URL shortener II: code generation, collisions, caching and failure handling", "19-url-shortener-deep-dive.md"),
        ],
        problems=["sd-base62", "sd-url-shortener-store"],
    ),
    dict(
        id="web-crawler",
        title="10. Design a web crawler",
        summary="The crawl loop, the URL frontier with politeness and priority, robots.txt, duplicate detection with Bloom filters, freshness and spider traps.",
        lessons=[
            _L("web-crawler-design", "Design a web crawler I: requirements, the crawl loop and the high-level design", "20-web-crawler-design.md"),
            _L("web-crawler-deep-dive", "Design a web crawler II: the URL frontier, deduplication, freshness and robustness", "21-web-crawler-deep-dive.md"),
        ],
        problems=["sd-crawler-frontier", "sd-bloom-filter"],
    ),
    dict(
        id="notification-system",
        title="11. Design a notification system",
        summary="Push, SMS and email channels, third-party providers, queues per channel, deduplication, retries, rate limits, templates and user preferences.",
        lessons=[
            _L("notification-design", "Design a notification system I: channels, requirements and the high-level design", "22-notification-design.md"),
            _L("notification-reliability", "Design a notification system II: reliability, deduplication, retries and limits", "23-notification-reliability.md"),
        ],
        problems=["sd-notification-dedup-retry"],
    ),
    dict(
        id="news-feed",
        title="12. Design a news feed system",
        summary="Feed publishing and retrieval, fan-out on write vs fan-out on read, the hybrid for celebrity accounts, the cache layers and ranking.",
        lessons=[
            _L("news-feed-design", "Design a news feed I: requirements, API, data model and the two flows", "24-news-feed-design.md"),
            _L("news-feed-deep-dive", "Design a news feed II: fan-out strategies, caching and failure handling", "25-news-feed-deep-dive.md"),
        ],
        problems=["sd-feed-fanout"],
    ),
    dict(
        id="chat-system",
        title="13. Design a chat system",
        summary="Polling, long polling and WebSocket; stateful connection servers, message storage, ordering with per-channel sequence numbers, multi-device sync and presence.",
        lessons=[
            _L("chat-design", "Design a chat system I: connections, requirements and the high-level design", "26-chat-design.md"),
            _L("chat-deep-dive", "Design a chat system II: message flow, ordering, sync and presence", "27-chat-deep-dive.md"),
        ],
        problems=["sd-chat-sequencer"],
    ),
    dict(
        id="search-autocomplete",
        title="14. Design a search autocomplete system",
        summary="Tries with cached top-k, the data-gathering pipeline, the query service, sharding the trie, freshness and filtering.",
        lessons=[
            _L("autocomplete-design", "Design search autocomplete I: requirements and the trie", "28-autocomplete-design.md"),
            _L("autocomplete-deep-dive", "Design search autocomplete II: building, serving, sharding and updating", "29-autocomplete-deep-dive.md"),
        ],
        problems=["sd-autocomplete-trie"],
    ),
    dict(
        id="video-platform",
        title="15. Design a video platform",
        summary="Upload, transcoding as a DAG, the bitrate ladder and adaptive streaming, CDN delivery and cost control, resumable uploads and safety.",
        lessons=[
            _L("video-design", "Design a video platform I: requirements, upload and streaming flows", "30-video-design.md"),
            _L("video-deep-dive", "Design a video platform II: transcoding, adaptive bitrate, CDN cost and failures", "31-video-deep-dive.md"),
        ],
        problems=["sd-bitrate-ladder"],
    ),
    dict(
        id="file-storage-sync",
        title="16. Design a file storage and sync service",
        summary="Block-level storage, delta sync, deduplication, metadata consistency, notifications, conflicts and storage cost.",
        lessons=[
            _L("file-sync-design", "Design file storage and sync I: requirements, blocks and the high-level design", "32-file-sync-design.md"),
            _L("file-sync-deep-dive", "Design file storage and sync II: delta sync, consistency, conflicts and failures", "33-file-sync-deep-dive.md"),
        ],
        problems=["sd-block-delta"],
    ),
    dict(
        id="building-blocks",
        title="17. Building blocks in depth",
        summary="Load-balancing algorithms, caching strategies and invalidation, database choice and indexing, replication and partitioning, CAP and PACELC, queues vs streams, idempotency, API styles and observability.",
        lessons=[
            _L("bb-load-balancing-caching", "Building blocks I: load balancing algorithms and caching strategies", "34-bb-load-balancing-caching.md"),
            _L("bb-databases-replication-partitioning", "Building blocks II: database choice, indexing, replication and partitioning", "35-bb-databases-replication-partitioning.md"),
            _L("bb-cap-queues-idempotency", "Building blocks III: CAP and PACELC, queues vs streams, and idempotency", "36-bb-cap-queues-idempotency.md"),
            _L("bb-apis-observability", "Building blocks IV: API styles, resilience patterns and observability", "37-bb-apis-observability.md"),
        ],
        problems=["sd-lease-leader-election", "sd-circuit-breaker", "sd-backpressure-queue"],
    ),
    dict(
        id="more-designs",
        title="18. More designs",
        summary="Ride-hailing dispatch, a payment system with idempotency and ledgers, ticket booking with seat locking, metrics and monitoring, a distributed job scheduler, ML model serving and a RAG application.",
        lessons=[
            _L("ride-hailing", "Design ride-hailing dispatch", "38-ride-hailing.md"),
            _L("payment-system", "Design a payment system: idempotency and ledgers", "39-payment-system.md"),
            _L("ticket-booking", "Design a ticket-booking system: seat holds and overselling", "40-ticket-booking.md"),
            _L("metrics-and-job-scheduler", "Design a metrics and monitoring system, and a distributed job scheduler", "41-metrics-and-job-scheduler.md"),
            _L("model-serving-and-rag", "Design an ML model-serving platform and a RAG/LLM application", "42-model-serving-and-rag.md"),
        ],
        problems=["sd-idempotent-payments", "sd-seat-booking"],
    ),
    dict(
        id="interview-essentials",
        title="19. System design interview essentials",
        summary="A one-page checklist, level expectations from junior to senior, how to practise, and 60 practice prompts with outline answers.",
        lessons=[
            _L("essentials-checklist-levels", "Checklist, level expectations and how to practise", "43-checklist-levels-practice.md"),
            _L("practice-prompts-1", "Practice prompts 1 to 30 with outline answers", "44-practice-prompts-1.md"),
            _L("practice-prompts-2", "Practice prompts 31 to 60 with outline answers", "45-practice-prompts-2.md"),
        ],
        problems=[],
    ),
]


def _defined_problem_ids():
    ids = set()
    pdir = os.path.join(_HERE, "problems")
    if os.path.isdir(pdir):
        for name in os.listdir(pdir):
            if name.endswith(".py"):
                with open(os.path.join(pdir, name), encoding="utf-8") as fh:
                    ids.update(re.findall(r'^\s*id="(sd-[a-z0-9-]+)"', fh.read(), re.M))
    return ids


def _available(modules):
    """Keep the manifest buildable while the track is being written: list only
    lesson files and problem ids that exist. When everything is present this is a no-op."""
    have = _defined_problem_ids()
    out = []
    for m in modules:
        lessons = [l for l in m["lessons"] if os.path.exists(os.path.join(_HERE, "lessons", l["file"]))]
        problems = [p for p in m["problems"] if p in have]
        if lessons or problems:
            out.append(dict(m, lessons=lessons, problems=problems))
    return out


TRACK = dict(
    id="system-design",
    title="System Design Interview",
    icon="🏗️",
    color="#0f766e",
    group="Engineering Practice",
    blurb="System design from zero to interview-ready: the building blocks, estimation, a four-step framework, "
          "every classic design from rate limiter to file sync, more modern designs, and 60 practice prompts.",
    sources=[
        "Alex Xu, System Design Interview: An Insider's Guide (2nd ed.), ch. 1-16 (topic guide; all wording original)",
        "System Design Primer (github.com/donnemartin/system-design-primer)",
        "DeCandia et al., Dynamo: Amazon's Highly Available Key-value Store (SOSP 2007)",
        "Stripe engineering blog: rate limiters and idempotency (stripe.com/blog)",
        "RFC 9309 (robots.txt), RFC 9562 (UUIDs)",
    ],
    modules=_available(_MODULES),
)
