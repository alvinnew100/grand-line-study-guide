# Transactions, ACID and isolation levels

> **Before this lesson:** you should know what a session, a lock, a snapshot and a deadlock are, and why two sessions changing the same data can lose an update ([Multiuser databases and locking](#/lesson/sql/locking)). You should be able to read `INSERT` and `UPDATE` statements ([Inserting, updating, deleting - and when statements go bad](#/lesson/sql/dml-constraints)).

## In plain words

Some changes only make sense together. Moving 500 from a savings account to a checking account takes two steps: take 500 out of one, put 500 into the other. If the computer crashes between the two, 500 has disappeared. If the first step is repeated by accident, money has been invented.

A **transaction** is a group of statements that the database treats as a single unit: **either all of them take effect or none of them do**. You mark the start, do the work, and then either confirm everything (`COMMIT`) or cancel everything (`ROLLBACK`).

An everyday picture: an online shopping basket. You add items, change quantities, remove things. Nothing is charged and nothing is shipped while you do so. Pressing "Pay" confirms the whole basket at once; closing the tab abandons all of it. No one ever receives half of your basket.

The promises a database makes about transactions are summed up in four words whose initials spell **ACID**. The last part of the lesson looks at one of them, isolation, which comes in strengths called **isolation levels**.

**Why it matters for a job.** Any program that changes more than one row for one purpose needs a transaction: payments, orders, bookings, stock movements. "Explain ACID" and "what are the isolation levels?" are among the most common questions in backend and data-engineering interviews.

## What a transaction is

Here is the transfer, wrapped in a transaction. Four statements change data: two balance updates and two rows in the transaction history.

```sql-run dataset=bank
BEGIN TRANSACTION;

UPDATE account SET avail_balance = avail_balance - 500 WHERE account_id = 105;   -- savings
UPDATE account SET avail_balance = avail_balance + 500 WHERE account_id = 103;   -- checking

INSERT INTO txn (txn_date, account_id, txn_type_cd, amount) VALUES ('2024-12-31 10:00:00', 105, 'DBT', 500);
INSERT INTO txn (txn_date, account_id, txn_type_cd, amount) VALUES ('2024-12-31 10:00:00', 103, 'CDT', 500);

COMMIT;

SELECT account_id, product_cd, avail_balance FROM account WHERE account_id IN (103, 105);
```

- `BEGIN TRANSACTION` says "what follows is one unit".
- The two `UPDATE` statements move the money; the two `INSERT` statements record a debit and a credit in the history table.
- `COMMIT` says "make all of it permanent".
- The final `SELECT` shows the result: checking account 103 went up by 500 to 8393.71 and savings account 105 went down by 500 to 4656.82.

Until `COMMIT`, no other session can see any of the four changes. And if anything fails before it (a broken rule, a crash, a lost connection) the database undoes all of them.

Now watch a transaction being abandoned. The amounts are far too large, so after looking at the balances the transaction is cancelled with `ROLLBACK`:

```sql-run dataset=bank
BEGIN;
UPDATE account SET avail_balance = avail_balance - 50000 WHERE account_id = 105;
UPDATE account SET avail_balance = avail_balance + 50000 WHERE account_id = 103;
SELECT 'inside txn' AS stage, account_id, avail_balance FROM account WHERE account_id IN (103, 105);
ROLLBACK;
SELECT 'after rollback' AS stage, account_id, avail_balance FROM account WHERE account_id IN (103, 105);
```

Two result tables appear. The first, taken inside the transaction, shows the changed balances, including a large negative one for account 105. The second, taken after `ROLLBACK`, shows 7893.71 and 5156.82: exactly what the accounts held before. It is as if the two updates had never been issued.

## ACID

| Property | The promise | How it is usually achieved |
|---|---|---|
| **Atomicity** | All of a transaction's changes happen, or none do. | a record of how to undo each change |
| **Consistency** | A transaction takes the database from one valid state to another; every declared rule holds at commit. | constraints, plus correctly written application logic |
| **Isolation** | Transactions running at the same time do not interfere; each behaves, to a chosen degree, as if it ran alone. | locks, versioning, or both |
| **Durability** | Once committed, changes survive a crash or a power cut. | changes are written to a log on disk before `COMMIT` returns |

A few words on each.

**Atomicity** is the all-or-nothing rule shown above. "Atomic" means indivisible.

**Durability** works like this. When you commit, the database first appends a description of the changes to a file called the **transaction log** and makes sure it has reached the disk. Only later does it update the main data files. If the machine dies, on restart the database reads the log: committed transactions are applied again, and transactions that were still in progress are undone.

**Consistency** is the odd one out, because it is partly your job. The database enforces the rules you *declared*: primary keys, `CHECK` conditions, foreign keys. A rule you did not declare, such as "debits and credits always balance", holds only if your transactions are written correctly.

**Isolation** is the subject of the previous lesson and of the last section of this one.

## Starting a transaction

Databases differ in how a transaction begins. There are two approaches:

1. **A transaction is always open** (Oracle, and the SQL standard). You never begin one; when the current transaction ends, your next statement starts a new one.
2. **Autocommit** (MySQL, SQL Server, PostgreSQL and SQLite by default). Unless you begin a transaction yourself, every statement is committed automatically the moment it finishes. Each statement is a one-statement transaction, and it cannot be rolled back afterwards.

| Database | Begin explicitly | Switch autocommit off |
|---|---|---|
| Standard / PostgreSQL | `START TRANSACTION` or `BEGIN` | a setting in the client program |
| MySQL | `START TRANSACTION` or `BEGIN` | `SET autocommit = 0` |
| SQL Server | `BEGIN TRANSACTION` | `SET IMPLICIT_TRANSACTIONS ON` |
| SQLite | `BEGIN`, optionally `DEFERRED`, `IMMEDIATE` or `EXCLUSIVE` | not applicable |
| Oracle | always open | not applicable |

A practical habit: when you connect to a database to fix something by hand, **begin a transaction first**. A mistaken `UPDATE` can then be rolled back instead of apologised for.

> [!NOTE]
> The libraries that programs use to talk to a database add a layer of their own. Python's `sqlite3` and `psycopg` open a transaction for you before a statement that changes data and expect you to call `conn.commit()`. Forgetting it is the classic "my insert disappeared" bug. A `with conn:` block commits on success and rolls back if an error is raised.

## Ending a transaction

A transaction ends in one of these ways:

- **`COMMIT`**: all changes become permanent and locks are released.
- **`ROLLBACK`**: all changes since the start are undone and locks are released.
- **The server stops or the connection drops**: the transaction is rolled back.
- **A statement that changes the structure of the database is issued.** Statements such as `CREATE TABLE` and `ALTER TABLE` are known as **DDL** (data definition language). In MySQL and Oracle, a DDL statement causes an **implicit commit**: whatever transaction is open is committed *before* the statement runs, without being asked. You cannot roll back past a `CREATE INDEX` there. PostgreSQL, SQL Server and SQLite are different: most DDL takes part in the transaction and can be rolled back, which makes changes to a database's structure much safer.
- **Another `START TRANSACTION`**: in MySQL this silently commits the previous transaction.
- **The transaction is chosen as a deadlock victim**: the database rolls it back and reports an error; the program should retry.

Try rolling back DDL in SQLite:

```sql-run dataset=bank
BEGIN;
CREATE TABLE scratch (id INTEGER PRIMARY KEY, note TEXT);
INSERT INTO scratch (note) VALUES ('this will vanish');
ROLLBACK;
SELECT COUNT(*) AS scratch_tables FROM sqlite_master WHERE name = 'scratch';
```

Zero. `sqlite_master` is SQLite's own list of the tables that exist, and `scratch` is not in it: the creation of the table itself was rolled back.

### What if a statement fails in the middle?

A failed statement does not necessarily end the transaction. In MySQL and SQLite, a statement that breaks a rule is undone *by itself*; the transaction stays open, and it is up to you to issue `ROLLBACK`. If you commit at that point, the earlier statements become permanent: half a transfer. PostgreSQL instead puts the transaction into a failed state in which every further statement is refused until you roll back. On any database, program code should treat an error inside a transaction as "roll back everything", unless it deliberately uses savepoints.

## Savepoints

Sometimes you want to undo *part* of a transaction. A **savepoint** is a named marker inside a transaction that you can return to without throwing away the work done before it.

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

Step by step: the first update gives category 5 a 10% discount. `SAVEPOINT` plants a marker. The second update is a disaster: with no `WHERE`, it sets every price in the shop to 0.01. `ROLLBACK TO SAVEPOINT` undoes everything after the marker, and only that. `COMMIT` then makes the discount permanent. The final query shows normal prices everywhere, with category 5 at its discounted minimum of 26.10.

Two points are easy to get wrong:

- Creating a savepoint **commits nothing**. You still need `COMMIT` at the end.
- `ROLLBACK` **without** a savepoint name undoes the *whole* transaction, savepoints included.

`RELEASE SAVEPOINT name` removes a marker without undoing anything. Savepoints let a program that loads a thousand rows skip one bad row without abandoning the batch.

## Isolation levels

Isolation is not all or nothing. Perfect isolation means transactions behave as if they ran one after another. That is the safest, and it costs the most waiting. So the SQL standard defines four **isolation levels**, described by which unwanted effects each one still permits. Such an effect is called an **anomaly**. There are three classic ones.

- **Dirty read**: reading changes that another transaction has made but *not yet committed*. If that transaction rolls back, you have read something that never officially existed.
- **Non-repeatable read**: reading the same row twice within one transaction and getting two different values, because another transaction changed the row and committed in between.
- **Phantom read**: running the same range query twice within one transaction and finding extra rows the second time, because another transaction inserted them and committed in between.

Picture checking a shared spreadsheet while a colleague edits it. Seeing a figure they are still typing and may delete is a dirty read. Looking at a cell, looking again a minute later and finding it changed is a non-repeatable read. Counting the rows, counting again and finding more is a phantom.

| Isolation level | Dirty read | Non-repeatable read | Phantom read |
|---|---|---|---|
| READ UNCOMMITTED | possible | possible | possible |
| READ COMMITTED | prevented | possible | possible |
| REPEATABLE READ | prevented | prevented | possible (according to the standard) |
| SERIALIZABLE | prevented | prevented | prevented |

The names describe what you are allowed to see. Under READ COMMITTED you read only committed data, but each statement looks at the latest committed state, so two statements can disagree. Under REPEATABLE READ a row you have read stays the same for the rest of your transaction. SERIALIZABLE guarantees that the outcome equals *some* one-after-another ordering of the transactions.

Here is a non-repeatable read as it would happen on PostgreSQL at its default level:

```sql
-- PostgreSQL, READ COMMITTED, time runs downward
-- Session A                                   -- Session B
BEGIN;
SELECT avail_balance FROM account
WHERE account_id = 103;        -- 7893.71
                                               UPDATE account SET avail_balance = 100
                                               WHERE account_id = 103;   -- committed at once
SELECT avail_balance FROM account
WHERE account_id = 103;        -- 100.00: same query, different answer
COMMIT;
```

Under REPEATABLE READ, session A's second `SELECT` would still return 7893.71, because the whole transaction works from one snapshot.

The default level differs between products, which matters when code is moved from one to another:

| Database | Default level | Notes |
|---|---|---|
| PostgreSQL | READ COMMITTED | each *statement* sees a fresh snapshot; REPEATABLE READ gives one snapshot per transaction; SERIALIZABLE may cancel a transaction, which must then be retried |
| Oracle | READ COMMITTED | also offers SERIALIZABLE |
| SQL Server | READ COMMITTED | uses locks by default; snapshot modes are optional |
| MySQL InnoDB | REPEATABLE READ | one snapshot per transaction; extra locks stop most phantoms |
| SQLite | SERIALIZABLE | in effect: only one writer at a time, and readers see a snapshot |

The level is chosen with `SET TRANSACTION ISOLATION LEVEL REPEATABLE READ` (standard syntax) at the start of a transaction.

Why should you care? Two situations:

- A report that runs **several queries** and expects them to agree (a total that matches the detail lines) needs one snapshot for the whole transaction: REPEATABLE READ.
- A **check-then-act** sequence ("if nobody has booked this slot, insert my booking") is safe only under SERIALIZABLE, or with an explicit lock, or with a unique constraint that rejects the second booking. Snapshots alone do not help: two transactions can each check, each see an empty slot, and each insert. This anomaly, in which each transaction is fine by itself and together they break a rule, is called **write skew**.

> [!INTERVIEW]
> Expect "explain ACID" and "name the isolation levels and the anomalies each prevents" in any backend or data-engineering interview. Add one practical sentence: a higher level means fewer anomalies, and more waiting or more cancelled transactions that have to be retried.

## Writing good transactions

- **Keep them short.** Begin late, commit early. Never wait for a person, or call a slow outside service, with a transaction open: locks and old row versions pile up.
- **Group what belongs together.** A transfer is one transaction; ten unrelated updates are ten.
- **Always handle failure.** Commit on success, roll back on any error, and be ready to retry after a deadlock.
- **Make retries safe.** An operation that has the same effect whether it runs once or several times is called **idempotent**. An insert that says "do nothing if this row already exists" can be retried without creating a duplicate.
- **Batch large jobs.** Committing every few thousand rows keeps locks and logs manageable. And wrapping many inserts in one transaction, instead of letting each one autocommit, is much *faster*, because the log is forced to disk once and not once per row.

The block below registers version 4 of a model twice inside one transaction. `ON CONFLICT (name, version) DO NOTHING` tells the database to skip the insert when a row with that name and version already exists.

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

Four rows, versions 1 to 4. The second insert found version 4 already there and did nothing, so there is no duplicate and no error.

## Pitfalls

- **Relying on autocommit** for a change made of several statements: a crash between them leaves half a transfer.
- **Forgetting to commit** in a library that opens transactions for you.
- **DDL inside a transaction on MySQL or Oracle**: an implicit commit.
- **Committing after an error** in MySQL or SQLite: the statements that succeeded become permanent.
- **Assuming every database has the same default isolation level.**
- **Thinking a savepoint commits.** It does not.
- **Check-then-act without a lock or a unique constraint**: two sessions can both pass the check.

## Summary

- A transaction makes a group of statements all-or-nothing: `BEGIN`, then `COMMIT` or `ROLLBACK`.
- **ACID**: atomicity, consistency, isolation, durability.
- Databases either keep a transaction always open (Oracle) or commit each statement automatically unless you begin a transaction yourself.
- A transaction ends by commit, by rollback, by a crash or dropped connection, by an implicit commit on DDL (MySQL, Oracle), or as a deadlock victim.
- **Savepoints** allow part of a transaction to be undone.
- **Isolation levels**, from READ UNCOMMITTED to SERIALIZABLE, trade anomalies (dirty, non-repeatable and phantom reads) against waiting; the defaults differ between databases.

## Glossary

- **Transaction** — a group of statements that take effect together or not at all.
- **`COMMIT`** — make a transaction's changes permanent.
- **`ROLLBACK`** — undo a transaction's changes.
- **ACID** — atomicity, consistency, isolation, durability: the four guarantees of a transactional database.
- **Atomicity** — all of a transaction's changes happen, or none.
- **Consistency** — the declared rules hold before and after every transaction.
- **Isolation** — transactions running at the same time do not disturb one another.
- **Durability** — committed changes survive a crash.
- **Transaction log** — the file in which changes are recorded on disk before the data files are updated.
- **Autocommit** — the mode in which every statement is committed automatically when it finishes.
- **DDL (data definition language)** — statements that change structure, such as `CREATE TABLE` and `ALTER TABLE`.
- **Implicit commit** — a commit the database performs without being asked, for example before DDL in MySQL.
- **Savepoint** — a named marker inside a transaction to which you can roll back.
- **Isolation level** — a setting that decides which anomalies a transaction may experience.
- **Anomaly** — an unwanted effect caused by transactions running at the same time.
- **Dirty read** — reading another transaction's uncommitted changes.
- **Non-repeatable read** — reading the same row twice and getting different values.
- **Phantom read** — repeating a range query and finding rows that were not there before.
- **Write skew** — two transactions each make a change that is valid alone, and together break a rule.
- **Idempotent** — having the same effect whether carried out once or several times.

```quiz
[
  {"q": "Which ACID property guarantees that a committed transfer survives a power failure?", "options": ["Atomicity", "Consistency", "Isolation", "Durability"], "answer": 3, "explain": "Committed changes are written to the transaction log on disk before COMMIT returns."},
  {"q": "In autocommit mode, what happens after each individual statement?", "options": ["Nothing until COMMIT", "It is committed automatically", "It is rolled back", "A savepoint is created"], "answer": 1, "explain": "Each statement is its own transaction unless you begin one explicitly."},
  {"q": "In MySQL, what does running ALTER TABLE inside an open transaction do?", "options": ["Fails", "Commits the current transaction first, without being asked", "Is rolled back with the transaction", "Creates a savepoint"], "answer": 1, "explain": "DDL causes an implicit commit in MySQL and Oracle; in PostgreSQL and SQLite most DDL can be rolled back."},
  {"q": "After SAVEPOINT s; ... ROLLBACK TO SAVEPOINT s; what is the state?", "options": ["The whole transaction is rolled back", "Changes after s are undone; earlier changes still await COMMIT", "Everything is committed", "The transaction has ended"], "answer": 1, "explain": "Only the work after the savepoint is undone, and you still need COMMIT."},
  {"q": "Which anomaly does READ COMMITTED still allow?", "options": ["Dirty reads", "Non-repeatable reads", "Reading uncommitted data", "None"], "answer": 1, "explain": "Each statement sees the latest committed data, so reading a row again can return a different value."},
  {"q": "What is MySQL InnoDB's default isolation level?", "options": ["READ UNCOMMITTED", "READ COMMITTED", "REPEATABLE READ", "SERIALIZABLE"], "answer": 2, "explain": "InnoDB defaults to REPEATABLE READ; PostgreSQL, Oracle and SQL Server default to READ COMMITTED."},
  {"q": "Why should transactions be kept short?", "options": ["Long ones use more processor time", "They hold locks and old row versions, making others wait and using storage", "COMMIT has a time limit", "They cannot contain SELECT statements"], "answer": 1, "explain": "Locks and snapshots are held until the transaction ends."},
  {"q": "Two sessions each check that a meeting slot is free and then each insert a booking. Which protection is NOT enough to stop a double booking?", "options": ["A unique constraint on the slot", "SERIALIZABLE isolation", "A snapshot per transaction (REPEATABLE READ) alone", "An explicit lock taken before the check"], "answer": 2, "explain": "Each transaction's snapshot shows the slot as free, so both insert: this is write skew."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 12 "Transactions" (what a transaction is, starting a transaction, ending a transaction, transaction savepoints), restated in original wording. Isolation levels: ISO SQL standard; PostgreSQL and MySQL reference manuals, "Transaction Isolation".
