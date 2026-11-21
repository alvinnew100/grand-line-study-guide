TRACK = dict(
    id="databases",
    title="Databases & Data-Intensive Systems",
    icon="🏛️",
    color="#3d5a80",
    group="Data & Databases",
    blurb="Storage engines, replication, partitioning, transactions, consensus, batch and stream processing - "
          "a chapter-by-chapter companion to Designing Data-Intensive Applications, plus practical databases for ML engineers.",
    sources=[
        "Martin Kleppmann, Designing Data-Intensive Applications (O'Reilly, 2017), ch. 1-12",
        "PostgreSQL documentation (postgresql.org/docs)",
        "Redis documentation (redis.io/docs)",
        "Apache Kafka documentation (kafka.apache.org/documentation)",
        "Malkov & Yashunin, Efficient and robust approximate nearest neighbor search using HNSW graphs (2016)",
    ],
    modules=[
        dict(
            id="foundations",
            title="1. Reliable, Scalable, Maintainable Applications",
            summary="Faults vs failures, describing load with load parameters, response-time percentiles, SLOs, and maintainability.",
            lessons=[
                dict(id="reliability-maintainability", title="Reliability and maintainability", file="01-reliability-maintainability.md"),
                dict(id="scalability-percentiles", title="Scalability: load parameters, percentiles and SLOs", file="02-scalability-percentiles.md"),
            ],
            problems=["db-percentiles", "db-error-budget"],
        ),
        dict(
            id="data-models",
            title="2. Data Models & Query Languages",
            summary="Relational vs document vs graph, schema-on-read vs schema-on-write, declarative queries, Cypher, SPARQL, Datalog.",
            lessons=[
                dict(id="relational-vs-document", title="Relational vs document models", file="03-relational-vs-document.md"),
                dict(id="graph-models", title="Graph models and query languages", file="04-graph-models.md"),
            ],
            problems=["db-graph-traverse"],
        ),
        dict(
            id="storage",
            title="3. Storage & Retrieval",
            summary="Hash indexes, SSTables and LSM-trees, Bloom filters, B-trees and WAL, OLTP vs OLAP, column stores, star schemas.",
            lessons=[
                dict(id="log-structured", title="Log-structured storage: hash indexes, SSTables, LSM-trees", file="05-log-structured.md"),
                dict(id="btrees", title="B-trees, write-ahead logs and the LSM vs B-tree trade-off", file="06-btrees.md"),
                dict(id="olap-column-stores", title="OLTP vs OLAP, warehouses and column-oriented storage", file="07-olap-column-stores.md"),
            ],
            problems=["db-append-log-kv", "db-sstable-merge", "db-bloom-filter", "db-btree-split", "db-wal-replay", "db-bitmap-rle"],
        ),
        dict(
            id="encoding",
            title="4. Encoding & Evolution",
            summary="JSON, Protocol Buffers, Avro, backward/forward compatibility, and data flow through databases, RPC and messages.",
            lessons=[
                dict(id="encoding-formats", title="Encoding formats and schema evolution", file="08-encoding-formats.md"),
                dict(id="dataflow-modes", title="Modes of data flow: databases, REST/RPC, message passing", file="09-dataflow-modes.md"),
            ],
            problems=["db-varint-encode", "db-schema-resolve"],
        ),
        dict(
            id="replication",
            title="5. Replication",
            summary="Leader/follower, sync vs async, replication-lag anomalies, multi-leader, leaderless quorums, conflicts and CRDTs.",
            lessons=[
                dict(id="leader-follower", title="Single-leader replication and replication lag", file="10-leader-follower.md"),
                dict(id="multi-leader-leaderless", title="Multi-leader and leaderless replication, quorums", file="11-multi-leader-leaderless.md"),
                dict(id="concurrent-writes", title="Detecting concurrent writes: LWW, version vectors, CRDTs", file="12-concurrent-writes.md"),
            ],
            problems=["db-quorum-read", "db-lww-merge", "db-sibling-versions", "db-vector-clock-compare"],
        ),
        dict(
            id="partitioning",
            title="6. Partitioning",
            summary="Key-range vs hash partitioning, hot spots, secondary indexes, rebalancing strategies and request routing.",
            lessons=[
                dict(id="partitioning-keys", title="Partitioning key-value data and hot spots", file="13-partitioning-keys.md"),
                dict(id="partitioning-ops", title="Secondary indexes, rebalancing and request routing", file="14-partitioning-ops.md"),
            ],
            problems=["db-range-router", "db-consistent-hashing", "db-rebalance-partitions"],
        ),
        dict(
            id="transactions",
            title="7. Transactions",
            summary="ACID, read committed, snapshot isolation and MVCC, lost updates, write skew, phantoms, serial execution, 2PL, SSI.",
            lessons=[
                dict(id="acid-weak-isolation", title="ACID, read committed and snapshot isolation", file="15-acid-weak-isolation.md"),
                dict(id="lost-updates-write-skew", title="Lost updates, write skew and phantoms", file="16-lost-updates-write-skew.md"),
                dict(id="serializability", title="Serializability: serial execution, 2PL and SSI", file="17-serializability.md"),
            ],
            problems=["db-mvcc-visibility", "db-lost-update-detect", "db-write-skew-detect"],
        ),
        dict(
            id="distributed-trouble",
            title="8. The Trouble with Distributed Systems",
            summary="Partial failures, unreliable networks, timeouts, unreliable clocks, process pauses, fencing tokens, Byzantine faults.",
            lessons=[
                dict(id="networks-faults", title="Partial failures and unreliable networks", file="18-networks-faults.md"),
                dict(id="clocks-pauses", title="Unreliable clocks and process pauses", file="19-clocks-pauses.md"),
                dict(id="truth-fencing", title="Truth, majorities, fencing tokens and Byzantine faults", file="20-truth-fencing.md"),
            ],
            problems=["db-fencing-token"],
        ),
        dict(
            id="consistency-consensus",
            title="9. Consistency & Consensus",
            summary="Linearizability, CAP, causality, Lamport clocks, total order broadcast, 2PC, Raft/Paxos and ZooKeeper.",
            lessons=[
                dict(id="linearizability", title="Linearizability and the CAP theorem", file="21-linearizability.md"),
                dict(id="ordering", title="Ordering, causality, Lamport clocks and total order broadcast", file="22-ordering.md"),
                dict(id="consensus", title="Distributed transactions, 2PC and consensus", file="23-consensus.md"),
            ],
            problems=["db-lamport-order", "db-2pc-outcome", "db-raft-commit-index"],
        ),
        dict(
            id="batch",
            title="10. Batch Processing",
            summary="The Unix philosophy, MapReduce and HDFS, reduce-side and map-side joins, dataflow engines and Spark.",
            lessons=[
                dict(id="unix-mapreduce", title="From Unix pipes to MapReduce", file="24-unix-mapreduce.md"),
                dict(id="joins-dataflow", title="Batch joins and dataflow engines", file="25-joins-dataflow.md"),
            ],
            problems=["db-mapreduce-wordcount", "db-sort-merge-join"],
        ),
        dict(
            id="stream",
            title="11. Stream Processing",
            summary="Message brokers vs logs, Kafka, change data capture, event sourcing, windows, stream joins and exactly-once.",
            lessons=[
                dict(id="brokers-logs", title="Message brokers and partitioned logs", file="26-brokers-logs.md"),
                dict(id="cdc-event-sourcing", title="Databases and streams: CDC and event sourcing", file="27-cdc-event-sourcing.md"),
                dict(id="processing-streams", title="Processing streams: time, windows, joins, fault tolerance", file="28-processing-streams.md"),
            ],
            problems=["db-tumbling-window", "db-session-windows"],
        ),
        dict(
            id="future",
            title="12. The Future of Data Systems",
            summary="Data integration, derived data, unbundling the database, end-to-end correctness and doing the right thing.",
            lessons=[
                dict(id="unbundling", title="Data integration and unbundling databases", file="29-unbundling.md"),
                dict(id="correctness", title="Aiming for correctness and doing the right thing", file="30-correctness.md"),
            ],
            problems=[],
        ),
        dict(
            id="practical",
            title="13. Practical Databases for ML Engineers",
            summary="PostgreSQL essentials, indexes in practice, Redis, vector databases (HNSW/IVF), choosing a database, interview playbook.",
            lessons=[
                dict(id="postgres-indexes", title="PostgreSQL essentials and indexes in practice", file="31-postgres-indexes.md"),
                dict(id="redis-vector-dbs", title="Redis and vector databases", file="32-redis-vector-dbs.md"),
                dict(id="choosing-system-design", title="Choosing a database and the system-design playbook", file="33-choosing-system-design.md"),
            ],
            problems=["db-sliding-window-limiter", "db-ivf-search"],
        ),
    ],
)
