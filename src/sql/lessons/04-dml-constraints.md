# Inserting, updating, deleting — and when statements go bad

A schema without data is an empty shell. This lesson covers the three data-changing statements — `INSERT`, `UPDATE`, `DELETE` — plus the modern UPSERT, and then follows the book's tour of the ways such statements fail: duplicate keys, missing parents, invalid values and bad dates. Those failures are not nuisances; they are the database protecting your data. Understanding them is the difference between a schema that guards itself and one that silently collects garbage.

All examples run against throwaway copies of the datasets, so feel free to experiment.

## Before this lesson

You should be able to read a `CREATE TABLE` statement and know what a data type, a primary key, a foreign key and a constraint are ([Data types and CREATE TABLE](#/lesson/sql/data-types-tables)).

## In plain words

A table starts empty. Three statements change what it contains: **`INSERT`** adds new rows, **`UPDATE`** changes values in existing rows, and **`DELETE`** removes rows. Together with `SELECT` (which only reads) they are often called **CRUD** — create, read, update, delete — the four things any application does with its data.

An everyday picture: a paper address book. Writing in a new friend is an insert. Crossing out an old phone number and writing the new one is an update. Tearing out a page is a delete. The important difference is that a database has a strict librarian standing next to you: if you try to write a second entry with the same membership number, or refer to a person who is not in the book, the librarian refuses. Those refusals are the **constraints** from the previous lesson doing their job, and the second half of this lesson shows each kind of refusal.

**Why it matters for a job.** Every application that saves anything runs these statements, and data engineers write them all day to load and correct data. The most feared mistake in the profession — changing or deleting every row of a table by forgetting one line — is made with these statements, so learning the safe habits now is worth a great deal.

### One of each, line by line

```sql-run dataset=bank
INSERT INTO department (name) VALUES ('Compliance');

UPDATE department
SET name = 'Risk and Compliance'
WHERE name = 'Compliance';

SELECT * FROM department;
```

- `INSERT INTO department (name)` — add a row to the `department` table, supplying a value for the `name` column only.
- `VALUES ('Compliance')` — the value to store. The `dept_id` column is not mentioned, so the database generates it.
- `UPDATE department` — change rows of this table.
- `SET name = 'Risk and Compliance'` — the new value for the `name` column.
- `WHERE name = 'Compliance'` — **which rows** to change. Without this line, *every* department would be renamed.
- The final `SELECT` shows the table afterwards: the three original departments plus the new one, already renamed.

Every example in this lesson runs on a private copy of the data that is reloaded each time you press Run, so you can experiment freely — including with the statements that are meant to fail.

## INSERT

The full form names the target columns and then supplies values in the same order:

```sql
INSERT INTO table_name (col1, col2, col3)
VALUES (v1, v2, v3);
```

Columns you leave out receive their `DEFAULT` (or NULL if there is no default). The primary key can be left out when the database generates it.

```sql-run dataset=bank
INSERT INTO branch (name, address, city, state, zip)
VALUES ('Lowell Branch', '15 Merrimack St.', 'Lowell', 'MA', '01852');

SELECT * FROM branch;
```

The new branch received `branch_id = 5` automatically.

### Multi-row inserts and INSERT ... SELECT

Most engines accept several rows in one statement:

```sql
INSERT INTO department (name) VALUES ('Compliance'), ('Marketing');
```

And you can insert the result of a query — handy for copying, archiving or building summary tables:

```sql-run dataset=bank
CREATE TABLE closed_account_archive AS
SELECT * FROM account WHERE 0;          -- empty copy with the same columns

INSERT INTO closed_account_archive
SELECT * FROM account WHERE status = 'CLOSED';

SELECT account_id, cust_id, close_date FROM closed_account_archive;
```

> [!TIP]
> Always list the target columns explicitly in application code. `INSERT INTO t VALUES (...)` without a column list breaks the day someone adds a column.

## UPDATE

`UPDATE` changes column values in the rows that match a `WHERE` clause:

```sql-run dataset=bank
UPDATE account
SET status = 'FROZEN',
    pending_balance = avail_balance
WHERE account_id = 101;

SELECT account_id, status, avail_balance, pending_balance
FROM account WHERE account_id = 101;
```

The new value may be an expression referring to the old values — `SET avail_balance = avail_balance * 1.01` applies 1% interest — or a subquery:

```sql-run dataset=bank
UPDATE account
SET last_activity_date = (SELECT MAX(date(t.txn_date))
                          FROM txn t
                          WHERE t.account_id = account.account_id)
WHERE product_cd = 'CHK';

SELECT account_id, last_activity_date FROM account WHERE product_cd = 'CHK' LIMIT 5;
```

That correlated form is covered properly in the subqueries module.

> [!WARNING]
> **An UPDATE or DELETE without WHERE changes every row.** Before running one by hand, run the same WHERE as a `SELECT COUNT(*)` first, and do it inside a transaction so you can roll back. MySQL Workbench even has a "safe updates" mode that refuses WHERE-less updates.

## DELETE

```sql-run dataset=shop
DELETE FROM web_events
WHERE event_time < '2024-11-02';

SELECT COUNT(*) AS remaining, MIN(event_time) AS earliest FROM web_events;
```

`DELETE FROM t` with no WHERE empties the table row by row (and can be rolled back). `TRUNCATE TABLE t` (MySQL, PostgreSQL; not SQLite) removes all rows faster by deallocating storage, with less logging and — in some engines — no rollback.

## UPSERT: insert or update

A frequent need: "insert this row, but if the key already exists, update it". The SQL standard's `MERGE` statement does this (Oracle, SQL Server, PostgreSQL 15+). SQLite and PostgreSQL also have the more compact `ON CONFLICT`:

```sql-run dataset=shop
INSERT INTO logins (customer_id, login_date) VALUES (4, '2024-03-02')
ON CONFLICT (customer_id, login_date) DO NOTHING;

INSERT INTO products (product_id, name, category_id, price, cost, launched_on)
VALUES (5, 'Wireless Mouse', 4, 21.99, 11.0, '2022-01-01')
ON CONFLICT (product_id) DO UPDATE SET price = excluded.price;

SELECT product_id, name, price FROM products WHERE product_id = 5;
```

`excluded` refers to the row you tried to insert.

> [!NOTE]
> **MySQL** spells it `INSERT ... ON DUPLICATE KEY UPDATE price = VALUES(price)` (or a row alias in 8.0.19+). MySQL's `REPLACE INTO` deletes and re-inserts, which fires delete triggers and cascades — usually not what you want.

## When good statements go bad

The book devotes a section to statements that the server rejects. Each corresponds to a constraint doing its job.

### 1. Non-unique primary key

```sql-run dataset=bank
INSERT INTO department (dept_id, name) VALUES (1, 'Duplicate Ops');
```

You get `UNIQUE constraint failed: department.dept_id`. A primary key promises one row per key value, and the engine enforces it with a unique index.

### 2. Nonexistent foreign key

The bank dataset is created with `PRAGMA foreign_keys = ON`, so SQLite checks references:

```sql-run dataset=bank
PRAGMA foreign_keys = ON;
INSERT INTO account (product_cd, cust_id, open_date, status)
VALUES ('CHK', 999, '2024-05-01', 'ACTIVE');
```

`FOREIGN KEY constraint failed` — customer 999 doesn't exist, and an account cannot reference a missing parent. Without that check you would get an **orphan** row that every join silently drops.

> [!WARNING]
> SQLite enforces foreign keys only when `PRAGMA foreign_keys = ON` is set on the connection — it is off by default for backward compatibility. MySQL enforces them only with the InnoDB engine (the default since 5.5); the old MyISAM engine parsed and ignored them. PostgreSQL always enforces them.

### 3. Column value violations

A CHECK constraint rejects values outside its rule:

```sql-run dataset=bank
UPDATE account SET status = 'SLEEPING' WHERE account_id = 101;
```

The `status` column has `CHECK (status IN ('ACTIVE','CLOSED','FROZEN'))`. MySQL before 8.0.16 parsed CHECK constraints and ignored them; the book's example uses an `ENUM` column type instead, which MySQL does enforce in strict mode. PostgreSQL has enums too (`CREATE TYPE status AS ENUM (...)`), but a CHECK or a lookup table with a foreign key is the portable choice.

`NOT NULL` violations behave the same way:

```sql-run dataset=shop
INSERT INTO customers (first_name, last_name, country, signup_date)
VALUES ('Ana', NULL, 'Brazil', '2024-12-01');
```

### 4. Invalid date conversions

In MySQL, inserting `'DEC-21-2008'` into a DATE column fails because the server cannot parse that format; the fix is an explicit conversion such as `STR_TO_DATE('DEC-21-2008', '%b-%d-%Y')`. SQLite, with no real date type, would accept the text and your date functions would later return NULL:

```sql-run dataset=bank
SELECT date('2024-12-21')  AS iso_ok,
       date('12/21/2024')  AS us_format,
       date('DEC-21-2024') AS book_format;
```

The lesson is the same in every engine: **normalise dates to ISO-8601 on the way in.**

## Data integrity is a team sport

Constraints, defaults and types are declarative rules that hold no matter which program writes to the database — the web app, a nightly ETL job, or an analyst with a SQL console. Application-level validation is valuable for user-friendly error messages, but only the database sees *every* write. A good rule of thumb is: validate in the app for usability, constrain in the database for correctness.

| Constraint | Protects against |
|---|---|
| `PRIMARY KEY` | duplicate entities, NULL identifiers |
| `UNIQUE` | duplicate natural keys (emails, codes) |
| `NOT NULL` | missing required facts |
| `CHECK` | out-of-range or invalid values |
| `FOREIGN KEY` | orphans and references to nothing |
| `DEFAULT` | forgotten values (timestamps, statuses) |

The *Indexes and constraints* module covers how constraints interact with indexes and what `ON DELETE CASCADE` does.

## Worked example: a safe data fix

A data engineer learns that all `pending` orders older than 30 days should be marked `cancelled`. A careful workflow:

```sql-run dataset=shop
-- 1. Look before you leap
SELECT order_id, order_date, status
FROM orders
WHERE status = 'pending' AND order_date < '2024-11-15';
```

```sql-run dataset=shop
-- 2. Change inside a transaction, verify, then commit
BEGIN;
UPDATE orders SET status = 'cancelled'
WHERE status = 'pending' AND order_date < '2024-11-15';
SELECT changes() AS rows_updated;
SELECT status, COUNT(*) FROM orders GROUP BY status;
COMMIT;
```

`changes()` is SQLite's count of rows affected by the last statement (MySQL: `ROW_COUNT()`; most drivers expose it as `cursor.rowcount`). If the number had surprised you, `ROLLBACK` instead of `COMMIT` would undo everything.

## Pitfalls

- **Forgetting WHERE** on UPDATE/DELETE.
- **Assuming foreign keys are enforced** in SQLite (pragma) or legacy MySQL (MyISAM).
- **Relying on column order** in `INSERT ... VALUES` without a column list.
- **Updating a primary key.** Keys should be immutable; updating them breaks references (unless cascades are configured) and caches.
- **Loading dates in local formats.** Convert to ISO first.

## Worked example: loading and reconciling data

Real DML rarely means typing one row. A typical task is loading a batch from a staging table into a clean table, skipping what is already there, updating what changed, and then proving the load did what you expect. Walk through one with the shop's messy `customer_imports`.

**Step 1 — profile the source.** How many rows, how many distinct people?

```sql-run dataset=shop
SELECT COUNT(*) AS staged_rows,
       COUNT(DISTINCT lower(trim(email))) AS distinct_emails,
       SUM(email <> lower(trim(email))) AS rows_needing_cleanup
FROM customer_imports;
```

**Step 2 — build the target with the rules you want enforced.** The UNIQUE constraint is what makes the load safe to repeat.

**Step 3 — insert with a conflict rule.** `ON CONFLICT DO NOTHING` keeps the first copy of each email; a second run inserts nothing.

```sql-run dataset=shop
CREATE TABLE leads (
  lead_id    INTEGER PRIMARY KEY,
  email      TEXT NOT NULL UNIQUE CHECK (email = lower(trim(email))),
  full_name  TEXT NOT NULL,
  source     TEXT NOT NULL,
  first_seen DATETIME NOT NULL
);

INSERT INTO leads (email, full_name, source, first_seen)
SELECT lower(trim(email)), full_name, source, imported_at
FROM customer_imports
WHERE true
ORDER BY imported_at
ON CONFLICT (email) DO NOTHING;

SELECT COUNT(*) AS leads_loaded FROM leads;
```

The number loaded equals the distinct-email count from step 1 — the first reconciliation check. Because rows were inserted in `imported_at` order, each lead kept its earliest source. (The odd-looking `WHERE true` is a SQLite parsing requirement: in `INSERT … SELECT … ON CONFLICT`, the SELECT needs a WHERE clause so that `ON` is not mistaken for a join condition.)

**Step 4 — an update driven by another table.** Mark which leads are already customers. This is a correlated UPDATE; the `WHERE EXISTS` restricts it to rows that have a match.

```sql-run dataset=shop
CREATE TABLE leads AS
SELECT DISTINCT lower(trim(email)) AS email, 0 AS is_customer FROM customer_imports;

UPDATE leads
SET is_customer = 1
WHERE EXISTS (SELECT 1 FROM customers c WHERE lower(c.email) = leads.email);

SELECT is_customer, COUNT(*) AS leads FROM leads GROUP BY is_customer;
```

**Step 5 — reconcile.** After any load, compare counts and totals between source and target. Three cheap checks catch most problems:

| Check | Query shape |
|---|---|
| Row counts match expectation | `SELECT COUNT(*)` on source (distinct keys) and target |
| No keys lost | `SELECT key FROM source EXCEPT SELECT key FROM target` returns nothing |
| Totals agree | `SUM(amount)` on both sides |

> [!TIP]
> Design loads to be **idempotent** — safe to run twice. A unique key plus `ON CONFLICT`, or "delete the day's partition, then insert it", means a retry after a crash cannot create duplicates. This is the single most valuable habit in data engineering.

## RETURNING: see what you changed

SQLite (3.35+), PostgreSQL and MariaDB let a data-changing statement return the affected rows, which saves a second query and removes a race between "write" and "read back":

```sql-run dataset=bank
UPDATE account
SET status = 'FROZEN'
WHERE cust_id = 3 AND status = 'ACTIVE'
RETURNING account_id, product_cd, avail_balance, status;
```

`INSERT ... RETURNING id` is the portable-ish way to learn a generated key (MySQL uses `LAST_INSERT_ID()`, SQL Server `OUTPUT inserted.id`).

## Deleting safely

Deletes are the least reversible DML. Three patterns keep them under control.

**Delete in dependency order.** With foreign keys enforced, children go before parents:

```sql-run dataset=shop
PRAGMA foreign_keys = ON;
DELETE FROM order_items WHERE order_id IN (SELECT order_id FROM orders WHERE status = 'cancelled');
DELETE FROM orders WHERE status = 'cancelled';
SELECT status, COUNT(*) AS orders FROM orders GROUP BY status;
```

Try swapping the two DELETE statements: the parent delete fails with `FOREIGN KEY constraint failed`, because cancelled orders still have items.

**Soft delete.** Instead of removing the row, mark it — `discontinued = 1`, or a `deleted_at` timestamp — and filter in queries (ideally through a view). History and foreign keys stay intact, and "undelete" is an UPDATE. The cost is that every query must remember the filter.

**Archive, then delete,** inside one transaction, so the row is never in neither place:

```sql
BEGIN;
INSERT INTO orders_archive SELECT * FROM orders WHERE order_date < '2020-01-01';
DELETE FROM orders WHERE order_date < '2020-01-01';
COMMIT;
```

On very large tables, do this in batches of a few thousand rows, or — better — drop a whole partition (see *Partitioning*).

## Summary

- `INSERT` adds rows (single, multi-row, or from a SELECT); omitted columns get defaults.
- `UPDATE ... SET ... WHERE` modifies matching rows; values may be expressions or subqueries.
- `DELETE ... WHERE` removes rows; `TRUNCATE` empties a table quickly where supported.
- UPSERT: `ON CONFLICT` (SQLite/PostgreSQL), `ON DUPLICATE KEY UPDATE` (MySQL), `MERGE` (standard).
- Rejected statements are constraints at work: duplicate keys, missing parents, invalid values, unparsable dates.
- Check counts first, change inside a transaction, verify, then commit.

## Glossary

| Term | Meaning in one sentence |
|---|---|
| **`INSERT`** | The statement that adds new rows to a table. |
| **`UPDATE`** | The statement that changes values in existing rows. |
| **`DELETE`** | The statement that removes rows. |
| **CRUD** | Create, read, update, delete — the four basic operations on stored data. |
| **`WHERE` clause** | The part of a statement that says which rows it applies to. |
| **`TRUNCATE`** | A fast way, in some databases, to remove every row of a table at once. |
| **UPSERT** | "Update or insert": add a row, or update the existing one if its key is already present. |
| **`ON CONFLICT`** | The SQLite and PostgreSQL wording for an upsert. |
| **`RETURNING`** | A clause that makes a data-changing statement hand back the rows it affected. |
| **Constraint violation** | The error raised when a statement would break a rule such as uniqueness. |
| **Orphan row** | A row whose foreign key points to a parent row that does not exist. |
| **Referential integrity** | The guarantee that every foreign key points to an existing row. |
| **Staging table** | A temporary holding table where raw data lands before it is cleaned and loaded. |
| **Idempotent** | Safe to run more than once: the second run changes nothing. |
| **Reconciliation** | Checking, with counts and totals, that a load produced what was expected. |
| **Soft delete** | Marking a row as deleted with a flag or date instead of physically removing it. |
| **Transaction** | A group of statements that take effect together or not at all (covered in its own module). |
| **Rollback** | Undoing the changes of an unfinished transaction. |

```quiz
[
  {"q": "What happens to columns omitted from an INSERT column list?", "options": ["The INSERT fails", "They receive their DEFAULT, or NULL if none", "They copy the previous row", "They are set to 0"], "answer": 1, "explain": "Unless a NOT NULL column has no default, omitted columns get defaults."},
  {"q": "What does UPDATE account SET status = 'FROZEN'; (no WHERE) do?", "options": ["Nothing", "Updates the first row", "Updates every row", "Raises an error"], "answer": 2, "explain": "Without WHERE every row qualifies. Always check counts first."},
  {"q": "Why might SQLite accept an account for a non-existent customer?", "options": ["SQLite has no foreign keys", "PRAGMA foreign_keys is OFF by default on a connection", "Foreign keys only work on text columns", "It never would"], "answer": 1, "explain": "SQLite parses FOREIGN KEY clauses but enforces them only when the pragma is on."},
  {"q": "In SQLite's INSERT ... ON CONFLICT DO UPDATE, what does 'excluded' refer to?", "options": ["The existing row", "The row you attempted to insert", "Deleted rows", "A system table"], "answer": 1, "explain": "excluded.col gives the value from the proposed insert."},
  {"q": "The error 'UNIQUE constraint failed: department.dept_id' means...", "options": ["dept_id is NULL", "A row with that dept_id already exists", "The department table is missing", "dept_id is the wrong type"], "answer": 1, "explain": "Primary keys are unique; the engine refuses duplicates."},
  {"q": "What is the safest way to run a manual data fix?", "options": ["Run the UPDATE and hope", "Preview with SELECT, run inside a transaction, verify, then COMMIT", "Delete and re-insert all rows", "Disable constraints first"], "answer": 1, "explain": "Previewing and transactional verification let you roll back mistakes."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 2 "Populating and Modifying Tables" and "When Good Statements Go Bad". SQLite docs, "UPSERT" and "Foreign Key Support".
