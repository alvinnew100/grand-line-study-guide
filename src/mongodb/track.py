TRACK = dict(
    id="mongodb",
    title="MongoDB",
    icon="🍃",
    color="#13aa52",
    group="Data & Databases",
    blurb="Documents, CRUD, querying, indexes, aggregation, transactions, schema design, replication, sharding and "
          "operations - a chapter-by-chapter companion to MongoDB: The Definitive Guide, plus PyMongo, change streams, "
          "Atlas Vector Search for RAG and interview-style data-modelling exercises.",
    sources=[
        "Bradshaw, Brazil & Chodorow, MongoDB: The Definitive Guide, 3rd ed. (O'Reilly, 2019), ch. 1-24",
        "MongoDB Manual (mongodb.com/docs/manual)",
        "PyMongo and Motor documentation (pymongo.readthedocs.io, motor.readthedocs.io)",
        "MongoDB Atlas Vector Search documentation (mongodb.com/docs/atlas/atlas-vector-search)",
    ],
    modules=[
        dict(
            id="getting-started",
            title="1. Introduction & Getting Started",
            summary="The document model, collections and databases, BSON types, ObjectId, and working in mongosh.",
            lessons=[
                dict(id="document-model", title="Documents, collections and why a document database", file="01-document-model.md"),
                dict(id="bson-shell", title="BSON types, ObjectId and the shell", file="02-bson-shell.md"),
            ],
            problems=["mongo-objectid-timestamp"],
        ),
        dict(
            id="crud",
            title="2. Creating, Updating & Deleting",
            summary="Inserts and deletes, update operators, array and embedded-document updates, upserts and write concern.",
            lessons=[
                dict(id="insert-delete", title="Inserting, deleting and write concern", file="03-insert-delete.md"),
                dict(id="update-operators", title="Update operators, arrays and upserts", file="04-update-operators.md"),
            ],
            problems=["mongo-update-operators", "mongo-upsert"],
        ),
        dict(
            id="querying",
            title="3. Querying",
            summary="Query operators, type-specific matching, arrays and embedded documents, $where, cursors and pagination.",
            lessons=[
                dict(id="query-operators", title="Query operators and how documents match", file="05-query-operators.md"),
                dict(id="cursors-pagination", title="Cursors, sorting and pagination done right", file="06-cursors-pagination.md"),
            ],
            problems=["mongo-find-query", "mongo-projection", "mongo-sort-multi-key", "mongo-skip-limit", "mongo-keyset-pagination"],
        ),
        dict(
            id="indexes",
            title="4. Indexes",
            summary="B-tree indexes, compound indexes and the ESR rule, explain output, covered queries, and special index types.",
            lessons=[
                dict(id="index-basics", title="Single-field and compound indexes: the ESR rule", file="07-index-basics.md"),
                dict(id="explain-covered", title="Reading explain output and covered queries", file="08-explain-covered.md"),
                dict(id="special-indexes", title="Unique, partial, sparse, TTL, text, geospatial and hashed indexes", file="09-special-indexes.md"),
            ],
            problems=["mongo-index-prefix-covered", "mongo-esr-index-order", "mongo-explain-scan-count",
                      "mongo-ttl-sweep", "mongo-unique-violations"],
        ),
        dict(
            id="aggregation",
            title="5. The Aggregation Framework",
            summary="Pipelines, $match, $project, $group and accumulators, $unwind, $lookup, $facet, and pipeline performance.",
            lessons=[
                dict(id="pipeline-stages", title="Pipelines: $match, $project, $group and $unwind", file="10-pipeline-stages.md"),
                dict(id="lookup-facet-performance", title="$lookup, $facet and pipeline performance", file="11-lookup-facet-performance.md"),
            ],
            problems=["mongo-aggregate-pipeline", "mongo-facet"],
        ),
        dict(
            id="transactions-design",
            title="6. Transactions & Application Design",
            summary="ACID transactions and their limits, embedding vs referencing, cardinality, schema design patterns and anti-patterns.",
            lessons=[
                dict(id="transactions", title="Transactions: ACID in MongoDB and its limits", file="12-transactions.md"),
                dict(id="embed-vs-reference", title="Embedding vs referencing, cardinality and normalisation trade-offs", file="13-embed-vs-reference.md"),
                dict(id="schema-patterns", title="Schema design patterns and anti-patterns", file="14-schema-patterns.md"),
            ],
            problems=["mongo-embed-reference", "mongo-bucket-pattern", "mongo-schema-validation"],
        ),
        dict(
            id="replication",
            title="7. Replication",
            summary="Replica sets, elections, the oplog, read preference, write and read concern, and replica-set administration.",
            lessons=[
                dict(id="replica-sets-elections", title="Replica sets, members and elections", file="15-replica-sets-elections.md"),
                dict(id="oplog-concerns", title="The oplog, write concern, read concern and read preference", file="16-oplog-concerns.md"),
                dict(id="replica-admin", title="Connecting from applications and administering a replica set", file="17-replica-admin.md"),
            ],
            problems=["mongo-election-winner", "mongo-majority-ack", "mongo-read-preference", "mongo-oplog-replay"],
        ),
        dict(
            id="sharding",
            title="8. Sharding",
            summary="Shards, mongos and config servers, shard keys, chunks and the balancer, targeted vs scatter-gather queries.",
            lessons=[
                dict(id="sharding-components", title="Sharded cluster components and query routing", file="18-sharding-components.md"),
                dict(id="shard-keys", title="Choosing a shard key: ranged, hashed and zoned", file="19-shard-keys.md"),
                dict(id="chunks-balancer", title="Chunks, the balancer and sharding administration", file="20-chunks-balancer.md"),
            ],
            problems=["mongo-shard-routing", "mongo-chunk-balancer"],
        ),
        dict(
            id="app-admin",
            title="9. Application Administration",
            summary="currentOp, the profiler and slow-query logs, collection and index statistics, durability and journaling.",
            lessons=[
                dict(id="seeing-operations", title="Seeing what the application is doing: currentOp and the profiler", file="21-seeing-operations.md"),
                dict(id="durability", title="Data administration, durability and journaling", file="22-durability.md"),
            ],
            problems=[],
        ),
        dict(
            id="server-admin",
            title="10. Server Administration",
            summary="Starting and stopping mongod, configuration, monitoring, backups, security and production deployment.",
            lessons=[
                dict(id="running-monitoring", title="Starting, stopping and monitoring MongoDB", file="23-running-monitoring.md"),
                dict(id="backups-security", title="Backups, security and production deployment", file="24-backups-security.md"),
            ],
            problems=[],
        ),
        dict(
            id="python-ml",
            title="11. MongoDB with Python and for ML",
            summary="PyMongo and Motor, Pydantic models, change streams, and Atlas Vector Search as the retrieval layer of a RAG system.",
            lessons=[
                dict(id="pymongo-motor", title="PyMongo, Motor and Pydantic models", file="25-pymongo-motor.md"),
                dict(id="change-streams-vector", title="Change streams and Atlas Vector Search for RAG", file="26-change-streams-vector.md"),
            ],
            problems=["mongo-change-stream-resume"],
        ),
        dict(
            id="interview",
            title="12. SQL vs NoSQL and MongoDB Interview Essentials",
            summary="When to choose a document store, CAP and PACELC positioning, worked data-modelling exercises and common pitfalls.",
            lessons=[
                dict(id="sql-vs-nosql", title="SQL vs NoSQL: choosing a document store and CAP positioning", file="27-sql-vs-nosql.md"),
                dict(id="modelling-exercises", title="Data-modelling interview exercises, worked end to end", file="28-modelling-exercises.md"),
            ],
            problems=[],
        ),
    ],
)
