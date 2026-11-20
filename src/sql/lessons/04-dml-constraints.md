# Inserting, updating, deleting — and when statements go bad

A schema without data is an empty shell. This lesson covers the three data-changing statements — `INSERT`, `UPDATE`, `DELETE` — plus the modern UPSERT, and then follows the book's tour of the ways such statements fail: duplicate keys, missing parents, invalid values and bad dates. Those failures are not nuisances; they are the database protecting your data. Understanding them is the difference between a schema that guards itself and one that silently collects garbage.

All examples run against throwaway copies of the datasets, so feel free to experiment.

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

## Summary

- `INSERT` adds rows (single, multi-row, or from a SELECT); omitted columns get defaults.
- `UPDATE ... SET ... WHERE` modifies matching rows; values may be expressions or subqueries.
- `DELETE ... WHERE` removes rows; `TRUNCATE` empties a table quickly where supported.
- UPSERT: `ON CONFLICT` (SQLite/PostgreSQL), `ON DUPLICATE KEY UPDATE` (MySQL), `MERGE` (standard).
- Rejected statements are constraints at work: duplicate keys, missing parents, invalid values, unparsable dates.
- Check counts first, change inside a transaction, verify, then commit.

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
