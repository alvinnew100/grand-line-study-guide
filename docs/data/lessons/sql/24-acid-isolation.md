# Transactions, ACID and isolation levels

If database servers never crashed, never ran out of disk and never had two users, there would be little more to say about changing data. But hardware fails mid-statement and sessions collide. A **transaction** is the device that lets a group of SQL statements succeed or fail **as a unit**, no matter what happens. This lesson covers what a transaction is, how to start and end one, savepoints, the four ACID properties, and a preview of **isolation levels** — the dial that trades consistency against concurrency.

## What is a transaction?

The book's example is the canonical one: transferring \$500 from your savings account to your checking account. That is two changes — withdraw from one, deposit to the other — and it is essential that **either both happen or neither does**. If the server crashes after the withdrawal, \$500 has vanished. If the deposit runs twice, the bank has invented money.

Wrapping the statements in a transaction gives the guarantee:

```sql-run dataset=bank
BEGIN TRANSACTION;

UPDATE account SET avail_balance = avail_balance - 500 WHERE account_id = 105;   -- savings
UPDATE account SET avail_balance = avail_balance + 500 WHERE account_id = 103;   -- checking

INSERT INTO txn (txn_date, account_id, txn_type_cd, amount) VALUES ('2024-12-31 10:00:00', 105, 'DBT', 500);
INSERT INTO txn (txn_date, account_id, txn_type_cd, amount) VALUES ('2024-12-31 10:00:00', 103, 'CDT', 500);

COMMIT;

SELECT account_id, product_cd, avail_balance FROM account WHERE account_id IN (103, 105);
```

Until `COMMIT`, none of the four changes is visible to any other session, and if anything fails — a constraint violation, a crash, a lost network connection — the server undoes all of them.

Now watch a transaction being abandoned. The business rule "no overdrafts" is checked after the first update, and the whole unit is rolled back:

```sql-run dataset=bank
BEGIN;
UPDATE account SET avail_balance = avail_balance - 50000 WHERE account_id = 105;
UPDATE account SET avail_balance = avail_balance + 50000 WHERE account_id = 103;
SELECT 'inside txn' AS stage, account_id, avail_balance FROM account WHERE account_id IN (103, 105);
ROLLBACK;
SELECT 'after rollback' AS stage, account_id, avail_balance FROM account WHERE account_id IN (103, 105);
```

(The sandbox shows the result of the last statement; add or remove the ROLLBACK to compare.) After the rollback the balances are exactly what they were.

## ACID

The guarantees a transactional database makes are summarised by the acronym **ACID**:

| Property | Guarantee | Mechanism (typical) |
|---|---|---|
| **Atomicity** | All of the transaction's changes happen, or none do. | undo log / rollback journal |
| **Consistency** | A transaction takes the database from one valid state to another; all constraints hold at commit. | constraints, triggers — plus correct application logic |
| **Isolation** | Concurrent transactions do not interfere; each behaves (to a chosen degree) as if it ran alone. | locks and/or MVCC |
| **Durability** | Once committed, changes survive crashes and power loss. | write-ahead log flushed to disk before commit returns |

The book describes the durability mechanism concretely: when you commit, the server first writes the changes to a **transaction log** on durable storage, and only later updates the data files. If the server dies, on restart it replays the log: committed transactions are reapplied, and transactions that were in flight are rolled back.

"Consistency" is the odd one out: it is partly your job. The database enforces the rules you *declared* (keys, CHECKs, foreign keys); invariants you did not declare — "debits equal credits" — hold only if your transactions are written correctly.

## Starting a transaction

Servers differ in how a transaction begins. The book distinguishes two approaches:

1. **A transaction is always active** (Oracle, and the SQL standard). You never begin one explicitly; when the current transaction ends, the next statement starts a new one.
2. **Autocommit** (MySQL, SQL Server, PostgreSQL, SQLite by default). Unless you explicitly begin a transaction, each statement is committed automatically as soon as it finishes — a one-statement transaction. You cannot roll it back afterwards.

| Engine | Begin explicitly | Turn autocommit off |
|---|---|---|
| Standard / PostgreSQL | `START TRANSACTION` / `BEGIN` | (client setting) |
| MySQL | `START TRANSACTION` / `BEGIN` | `SET autocommit = 0` |
| SQL Server | `BEGIN TRANSACTION` | `SET IMPLICIT_TRANSACTIONS ON` |
| SQLite | `BEGIN [DEFERRED \| IMMEDIATE \| EXCLUSIVE]` | — |
| Oracle | implicit | — |

The book's practical advice: when you log in to do manual work, **start a transaction explicitly** (or disable autocommit), so that a mistaken UPDATE can be rolled back rather than apologised for.

> [!NOTE]
> Client libraries add their own layer. Python's `sqlite3` and `psycopg` open transactions implicitly before data-modifying statements and expect you to call `conn.commit()`; forgetting it is the classic "my insert disappeared" bug. Use `with conn:` blocks, which commit on success and roll back on exception.

## Ending a transaction

A transaction ends in one of these ways:

- **`COMMIT`** — make all changes permanent and release locks.
- **`ROLLBACK`** — undo all changes since the transaction began and release locks.
- **The server shuts down or the connection drops** — the transaction is rolled back (when the server restarts, if necessary).
- **A schema statement is issued** — in MySQL and Oracle, DDL such as `ALTER TABLE` causes an **implicit commit** of the current transaction *before* it runs. The book warns about this: you cannot roll back past a `CREATE INDEX` there. PostgreSQL, SQL Server and SQLite are different — most DDL is itself transactional and can be rolled back, which makes schema migrations much safer.
- **Another `START TRANSACTION`** — in MySQL this implicitly commits the previous transaction.
- **Deadlock detection** — the server rolls back the victim's transaction and returns an error; the application should retry.

Try transactional DDL in SQLite:

```sql-run dataset=bank
BEGIN;
CREATE TABLE scratch (id INTEGER PRIMARY KEY, note TEXT);
INSERT INTO scratch (note) VALUES ('this will vanish');
ROLLBACK;
SELECT COUNT(*) AS scratch_tables FROM sqlite_master WHERE name = 'scratch';
```

Zero: the table creation itself was rolled back.

### What about errors in the middle?

An important subtlety: a failed statement does not necessarily end the transaction. In MySQL and SQLite, a statement that violates a constraint is undone *by itself*, the transaction stays open, and it is up to you to issue ROLLBACK (commit now, and the earlier statements persist!). PostgreSQL instead puts the transaction into an aborted state where every further statement fails until you roll back. Either way, application code should treat any error inside a transaction as "roll back the whole thing" unless it deliberately uses savepoints.

## Transaction savepoints

Sometimes you want to undo only *part* of a transaction. A **savepoint** marks a point to which you can roll back without discarding earlier work:

```sql-run dataset=shop
BEGIN;
UPDATE products SET price = ROUND(price * 0.9, 2) WHERE category_id = 5;       -- keep this
SAVEPOINT before_risky_change;
UPDATE products SET price = 0.01;                                             -- oops: no WHERE
ROLLBACK TO SAVEPOINT before_risky_change;
COMMIT;

SELECT category_id, MIN(price) AS min_price, COUNT(*) AS n
FROM products GROUP BY category_id ORDER BY category_id LIMIT 6;
```

The 10% discount on audio products survives; the catastrophic second update does not. The book stresses two points:

- Creating a savepoint **commits nothing**. You still need `COMMIT` at the end.
- `ROLLBACK` **without** naming a savepoint undoes the *entire* transaction, savepoints included.

`RELEASE SAVEPOINT name` discards a savepoint without undoing anything. Savepoints are how frameworks implement "nested transactions", and how a batch loader can skip one bad row without abandoning the batch.

## Isolation levels: a preview

Isolation is not all-or-nothing. Perfect isolation (transactions behave as if run one after another) costs concurrency, so the SQL standard defines four **isolation levels** in terms of which anomalies they permit:

- **Dirty read** — reading another transaction's *uncommitted* changes (which may be rolled back).
- **Non-repeatable read** — reading the same row twice in one transaction and getting different values, because someone committed in between.
- **Phantom read** — re-running a range query in one transaction and finding new rows that someone inserted and committed in between.

| Isolation level | Dirty read | Non-repeatable read | Phantom |
|---|---|---|---|
| READ UNCOMMITTED | possible | possible | possible |
| READ COMMITTED | prevented | possible | possible |
| REPEATABLE READ | prevented | prevented | possible (by the standard) |
| SERIALIZABLE | prevented | prevented | prevented |

Defaults differ, which matters when you move code between databases:

| Engine | Default level | Notes |
|---|---|---|
| PostgreSQL | READ COMMITTED | each *statement* sees a fresh snapshot; REPEATABLE READ is snapshot isolation; SERIALIZABLE uses SSI and may abort transactions |
| Oracle | READ COMMITTED | offers SERIALIZABLE (really snapshot isolation) |
| SQL Server | READ COMMITTED | lock-based by default; optional snapshot modes |
| MySQL InnoDB | REPEATABLE READ | snapshot per transaction; gap locks also block most phantoms |
| SQLite | SERIALIZABLE | trivially: one writer at a time, readers see a snapshot |

Set it with `SET TRANSACTION ISOLATION LEVEL REPEATABLE READ` (standard syntax) at the start of a transaction.

Why should you care? A report that runs **several queries** and expects them to agree with one another (totals matching details) needs at least a transaction-wide snapshot: REPEATABLE READ. A check-then-act sequence ("if no booking exists for this slot, insert one") is only safe under SERIALIZABLE, or with explicit locks or a unique constraint — snapshot isolation alone permits the **write skew** anomaly, where two transactions each read an overlapping set, make disjoint writes, and jointly break an invariant.

> [!INTERVIEW]
> Expect "explain ACID" and "what are the isolation levels and which anomalies do they prevent?" in any backend or data-engineering interview. Add one practical sentence: higher isolation means fewer anomalies but more blocking or more aborted transactions that must be retried.

## Writing good transactions

- **Keep them short.** Open late, commit early. Never wait for user input or call a slow external API with a transaction open — locks and old row versions pile up.
- **Group what belongs together.** A transfer is one transaction; ten unrelated updates are ten.
- **Always handle failure.** `try: ... commit` / `except: rollback`. Be ready to retry on deadlock or serialization errors.
- **Make retries safe (idempotent).** Use natural or client-generated keys with `ON CONFLICT DO NOTHING`, so that a retried insert does not duplicate.
- **Batch big jobs.** Committing every few thousand rows keeps locks, logs and replication lag manageable — and wrapping many inserts in one transaction (rather than autocommitting each) is also much *faster*, because the log is flushed once.

```sql-run dataset=mlops
-- Idempotent registration of a model version: safe to run twice
BEGIN;
INSERT INTO models (name, version, run_id, stage, registered_at)
VALUES ('intent-model', 4, 55, 'None', '2024-12-01 09:00:00')
ON CONFLICT (name, version) DO NOTHING;
INSERT INTO models (name, version, run_id, stage, registered_at)
VALUES ('intent-model', 4, 55, 'None', '2024-12-01 09:00:00')
ON CONFLICT (name, version) DO NOTHING;
COMMIT;
SELECT name, version, stage FROM models WHERE name = 'intent-model';
```

## Pitfalls

- **Relying on autocommit** for multi-statement changes — a crash between statements leaves half a transfer.
- **Forgetting to commit** in a driver that opens transactions implicitly.
- **DDL inside a transaction on MySQL/Oracle** — implicit commit.
- **Committing after an error** in MySQL/SQLite — the successful statements persist.
- **Assuming the same default isolation level** across engines.
- **Thinking savepoints commit** — they don't.

## Summary

- A transaction groups statements into an all-or-nothing unit: `BEGIN … COMMIT` or `ROLLBACK`.
- **ACID**: atomicity, consistency, isolation, durability.
- Engines either keep a transaction always active (Oracle) or autocommit each statement unless you begin one explicitly.
- Transactions end by commit, rollback, disconnect/crash, implicit commit on DDL (MySQL/Oracle), or as a deadlock victim.
- **Savepoints** allow partial rollback inside a transaction.
- **Isolation levels** (READ UNCOMMITTED → SERIALIZABLE) trade anomalies (dirty, non-repeatable, phantom reads) against concurrency; defaults differ by engine.

```quiz
[
  {"q": "Which ACID property guarantees that a committed transfer survives a power failure?", "options": ["Atomicity", "Consistency", "Isolation", "Durability"], "answer": 3, "explain": "Committed changes are written to the transaction log on durable storage before commit returns."},
  {"q": "In autocommit mode, what happens after each individual statement?", "options": ["Nothing until COMMIT", "It is committed automatically", "It is rolled back", "A savepoint is created"], "answer": 1, "explain": "Each statement is its own transaction unless you BEGIN explicitly."},
  {"q": "In MySQL, what does running ALTER TABLE inside an open transaction do?", "options": ["Fails", "Implicitly commits the current transaction first", "Is rolled back with the transaction", "Creates a savepoint"], "answer": 1, "explain": "DDL causes an implicit commit in MySQL and Oracle; PostgreSQL and SQLite have transactional DDL."},
  {"q": "After SAVEPOINT s; ... ROLLBACK TO SAVEPOINT s; what is the state?", "options": ["Whole transaction rolled back", "Changes after s undone; earlier changes still pending commit", "Everything committed", "Transaction ended"], "answer": 1, "explain": "Only work after the savepoint is undone; you still need COMMIT."},
  {"q": "Which anomaly does READ COMMITTED still allow?", "options": ["Dirty reads", "Non-repeatable reads", "Reading uncommitted data", "None"], "answer": 1, "explain": "Each statement sees newly committed data, so re-reading a row can return a different value."},
  {"q": "What is MySQL InnoDB's default isolation level?", "options": ["READ UNCOMMITTED", "READ COMMITTED", "REPEATABLE READ", "SERIALIZABLE"], "answer": 2, "explain": "InnoDB defaults to REPEATABLE READ; PostgreSQL, Oracle and SQL Server default to READ COMMITTED."},
  {"q": "Why should transactions be kept short?", "options": ["Long ones use more CPU", "They hold locks and old row versions, blocking others and bloating storage", "COMMIT has a time limit", "They cannot contain SELECTs"], "answer": 1, "explain": "Locks and snapshots are held until the transaction ends."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 12 "Transactions" (what is a transaction, starting a transaction, ending a transaction, transaction savepoints). Isolation levels: ISO SQL standard; PostgreSQL and MySQL reference manuals, "Transaction Isolation".
