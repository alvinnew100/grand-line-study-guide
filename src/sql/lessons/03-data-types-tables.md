# Data types and CREATE TABLE

Every column in a table has a data type, and choosing types well is the first design decision you make. Types decide what values are legal, how much space they take, how they sort and compare, and which functions work on them. This lesson follows the book's tour of character, numeric and temporal types, shows how SQLite's very different type system works, and then designs and creates a table step by step.

## Character data

Text comes in two classic flavours:

- **`CHAR(n)`** — fixed length. Shorter values are padded with spaces to `n` characters. Good for values that are always the same length: two-letter state codes, ISO country codes, single-letter flags such as `cust_type_cd CHAR(1)`.
- **`VARCHAR(n)`** — variable length, up to `n` characters, stores only what you give it. The default choice for names, emails, addresses.

For long text (documents, JSON blobs, log messages) databases offer large-object types: `TEXT`, `MEDIUMTEXT`, `LONGTEXT` in MySQL; `TEXT` (unlimited) in PostgreSQL; `CLOB` in Oracle.

Two related concepts matter as soon as you leave ASCII:

- **Character set (encoding)** — which characters can be stored and how they are encoded in bytes. Use UTF-8 everywhere. (In MySQL that means `utf8mb4`; the older `utf8` cannot store emoji.)
- **Collation** — the rules for comparing and sorting text: is `'a' = 'A'`? does `'é'` sort next to `'e'`? MySQL's default collations are case-insensitive; PostgreSQL's comparisons are case-sensitive by default.

> [!NOTE]
> In PostgreSQL there is no performance difference between `VARCHAR(n)` and `TEXT`; the length limit is just a constraint. In MySQL the declared length affects index limits and memory use for temporary tables, so it is worth keeping it realistic.

## Numeric data

| Kind | Typical types | Use for |
|---|---|---|
| Integers | `SMALLINT` (2 bytes), `INT`/`INTEGER` (4), `BIGINT` (8) | ids, counts, quantities |
| Exact decimals | `DECIMAL(p, s)` / `NUMERIC(p, s)` | **money**, anything where 0.1 + 0.2 must equal 0.3 |
| Floating point | `REAL`/`FLOAT`, `DOUBLE PRECISION` | measurements, scores, ML metrics |
| Booleans | `BOOLEAN` (PostgreSQL), `TINYINT(1)` (MySQL), `INTEGER` 0/1 (SQLite) | flags |

`DECIMAL(10, 2)` means 10 significant digits of which 2 are after the decimal point: values up to 99,999,999.99. The book's bank stores balances as `float(10,2)`, which MySQL has since deprecated; modern practice is `DECIMAL` (or integer cents) for money, because binary floating point cannot represent most decimal fractions exactly.

```sql-run dataset=bank
SELECT 0.1 + 0.2         AS float_sum,
       0.1 + 0.2 = 0.3   AS equals_point_three,
       ROUND(0.1 + 0.2, 2) = 0.3 AS after_round;
```

The second column comes back `0` (false). That is not a SQLite bug; it is IEEE-754 arithmetic, the same in Python.

MySQL also offers `UNSIGNED` integer variants (the book's `smallint unsigned` ids), doubling the positive range. Standard SQL and PostgreSQL have no unsigned types; use a CHECK constraint (`CHECK (qty >= 0)`) to forbid negatives.

## Temporal data

| Type | Holds | Example literal |
|---|---|---|
| `DATE` | calendar date | `'2024-03-07'` |
| `TIME` | time of day | `'14:22:00'` |
| `TIMESTAMP` / `DATETIME` | date + time | `'2024-03-07 14:22:00'` |
| `INTERVAL` (PostgreSQL, standard) | a duration | `INTERVAL '3 days'` |
| `YEAR` (MySQL) | a year | `2024` |

The ISO-8601 format `YYYY-MM-DD HH:MM:SS` is accepted by every engine and, importantly, **sorts correctly as text**. Time zones are a perennial source of bugs: PostgreSQL's `TIMESTAMP WITH TIME ZONE` stores an absolute instant, MySQL's `TIMESTAMP` converts to UTC for storage while `DATETIME` stores the wall-clock value as given. A robust rule: store UTC, convert at the edges.

## SQLite's type system: affinity

SQLite is different. It uses **dynamic typing**: a *value* has a type, a *column* only has a preferred type called its **affinity**. There are five storage classes — `NULL`, `INTEGER`, `REAL`, `TEXT`, `BLOB` — and the declared column type is mapped to an affinity by a few substring rules:

| Declared type contains... | Affinity |
|---|---|
| `INT` | INTEGER |
| `CHAR`, `CLOB`, `TEXT` | TEXT |
| `BLOB` or nothing | BLOB (none) |
| `REAL`, `FLOA`, `DOUB` | REAL |
| anything else (`NUMERIC`, `DECIMAL`, `DATE`, `BOOLEAN`) | NUMERIC |

So `VARCHAR(20)` means TEXT affinity, and the `(20)` is **ignored** — SQLite will happily store 500 characters. `DATE` gets NUMERIC affinity, and dates are stored as text because `'2024-03-07'` doesn't look like a number. There is no separate date type; SQLite's date functions work on ISO text, Julian day numbers, or Unix epoch numbers.

```sql-run dataset=bank
SELECT typeof(account_id), typeof(product_cd), typeof(open_date),
       typeof(avail_balance), typeof(close_date)
FROM account
LIMIT 3;
```

Affinity converts when it can: insert `'42'` into an INTEGER-affinity column and it is stored as the integer 42; insert `'abc'` and it is stored as text, without error. Since version 3.37 you can opt in to rigid typing with `CREATE TABLE ... (...) STRICT`, which rejects values of the wrong type.

> [!WARNING]
> Because SQLite tolerates sloppy values, a query can work perfectly here and fail in PostgreSQL (or the reverse). Write portable SQL: compare numbers with numbers and text with text, and use `CAST` when you mean a conversion.

## Designing a table: the book's three steps

The book designs a small `person` table in three steps; we will follow the same method for a new table that tracks **feature flags** in the `mlops` world.

### Step 1: design — list the facts

What do we need to know about a feature flag? Its name, a description, which team owns it, whether it's on, the percentage of traffic it applies to, when it was created, and which environments it is enabled in.

### Step 2: refinement — apply the relational rules

- Give each row a **primary key**: a surrogate `flag_id`.
- `name` must be unique: a **UNIQUE** constraint (a natural key kept as an alternate key).
- "Which environments" is **multi-valued** (staging *and* production). Storing `'staging,production'` in one column breaks first normal form; it belongs in a child table `flag_environment(flag_id, environment)`, exactly as the book moves a person's favourite foods into a separate `favorite_food` table.
- `owner_team` repeats team names; in a full design that would be a foreign key to a `team` table.
- `rollout_pct` must be between 0 and 100: a **CHECK** constraint.

### Step 3: build the schema statements

```sql
CREATE TABLE feature_flag (
  flag_id      INTEGER PRIMARY KEY,
  name         VARCHAR(60)  NOT NULL UNIQUE,
  description  TEXT,
  owner_team   VARCHAR(30)  NOT NULL,
  enabled      INTEGER      NOT NULL DEFAULT 0 CHECK (enabled IN (0, 1)),
  rollout_pct  NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (rollout_pct BETWEEN 0 AND 100),
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE flag_environment (
  flag_id      INTEGER NOT NULL REFERENCES feature_flag(flag_id),
  environment  VARCHAR(20) NOT NULL CHECK (environment IN ('staging','production','shadow')),
  PRIMARY KEY (flag_id, environment)
);
```

Run it — the sandbox lets you create tables in the loaded database:

```sql-run dataset=mlops
CREATE TABLE feature_flag (
  flag_id      INTEGER PRIMARY KEY,
  name         VARCHAR(60)  NOT NULL UNIQUE,
  owner_team   VARCHAR(30)  NOT NULL,
  enabled      INTEGER      NOT NULL DEFAULT 0 CHECK (enabled IN (0, 1)),
  rollout_pct  NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (rollout_pct BETWEEN 0 AND 100),
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO feature_flag (name, owner_team, enabled, rollout_pct)
VALUES ('new-ranker', 'search', 1, 10), ('bert-intents', 'nlp', 0, 0);
SELECT * FROM feature_flag;
```

Notice that we did not supply `flag_id` or `created_at`. `flag_id` is an `INTEGER PRIMARY KEY`, which in SQLite is an alias of the internal rowid and is assigned automatically; `created_at` came from its `DEFAULT`.

> [!NOTE]
> **Auto-generated keys by dialect.** MySQL: `flag_id INT AUTO_INCREMENT PRIMARY KEY`. PostgreSQL: `flag_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY` (or the older `SERIAL`). SQL Server: `IDENTITY(1,1)`. Oracle 12c+: identity columns, previously sequences. SQLite: `INTEGER PRIMARY KEY` (add `AUTOINCREMENT` only if ids must never be reused).

### Anatomy of a column definition

```
column_name  TYPE  [NOT NULL]  [DEFAULT expr]  [PRIMARY KEY | UNIQUE]  [CHECK (cond)]  [REFERENCES t(col)]
```

Table-level constraints go after the columns and are needed when a constraint spans several columns, as with the compound key `PRIMARY KEY (flag_id, environment)`.

## Inspecting a table

The book uses MySQL's `DESC customer`. SQLite's equivalent is a pragma:

```sql-run dataset=bank
SELECT name, type, "notnull", dflt_value, pk
FROM pragma_table_info('account');
```

PostgreSQL's `psql` has `\d account`; any engine that supports the standard `information_schema` answers `SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'account'`.

## Changing and dropping tables

- `ALTER TABLE t ADD COLUMN c TYPE` — supported everywhere.
- `ALTER TABLE t RENAME COLUMN a TO b` — SQLite 3.25+, PostgreSQL, MySQL 8.
- `ALTER TABLE t DROP COLUMN c` — SQLite 3.35+, with restrictions.
- Changing a column's type: PostgreSQL `ALTER COLUMN ... TYPE`, MySQL `MODIFY`; SQLite requires rebuilding the table (create new, copy, drop, rename).
- `DROP TABLE t` removes the table and its data. `DROP TABLE IF EXISTS t` avoids an error if it is missing.

In production, schema changes are managed as versioned **migrations** (Alembic, Flyway, Django migrations) so that every environment's schema can be reproduced.

## Choosing types: a checklist

1. **Identifiers:** `INTEGER`/`BIGINT` surrogates. Use BIGINT for anything that may exceed 2.1 billion rows (event tables, predictions).
2. **Money:** `DECIMAL(p,2)` or integer cents — never FLOAT.
3. **Codes with fixed length:** `CHAR(n)` plus a CHECK or a foreign key to a lookup table.
4. **Free text:** `VARCHAR(n)` with a realistic limit, or `TEXT`.
5. **Timestamps:** a timezone-aware type, stored in UTC.
6. **Flags:** BOOLEAN where available; otherwise 0/1 with a CHECK.
7. **ML metrics, scores:** `REAL`/`DOUBLE` is fine — they are approximate by nature.

## Pitfalls

- **Trusting SQLite's length limits.** `VARCHAR(2)` stores `'Massachusetts'` without complaint. Validate in the application, use CHECK (`length(state) = 2`), or STRICT tables.
- **Floating-point money.** Sums drift by fractions of a cent and equality tests fail.
- **Storing dates in non-ISO text** like `'03/07/2024'`: they sort wrongly and date functions can't parse them.
- **Multi-valued columns** (`'staging,production'`): use a child table.

## Worked example: reading a schema like a reviewer

Type and constraint choices are easiest to judge on a real table. Here is the DDL of the `mlops.runs` table; read it the way a reviewer would.

```sql-run dataset=mlops
SELECT sql FROM sqlite_master WHERE name = 'runs';
```

What the definition tells you — and what it guarantees:

- `run_id INTEGER PRIMARY KEY` — a surrogate key, auto-assigned.
- `experiment_id INTEGER NOT NULL REFERENCES experiments(...)` — every run belongs to exactly one experiment; an orphan run is impossible.
- `parent_run_id INTEGER REFERENCES runs(run_id)` — **nullable** and self-referencing: a run *may* have a parent (hyper-parameter sweeps), and most do not.
- `learning_rate REAL`, `batch_size INTEGER` — nullable on purpose: tree models have no batch size. NULL here means "not applicable".
- `status TEXT NOT NULL CHECK (status IN (...))` — a closed vocabulary. A typo such as `'FINSHED'` is rejected at write time instead of corrupting every dashboard that groups by status.
- `ended_at DATETIME` — nullable: a running job has not ended. The pair (`status`, `ended_at`) carries an implicit rule — finished runs should have an end time — that the schema does *not* enforce. You can check it:

```sql-run dataset=mlops
SELECT status,
       COUNT(*) AS runs,
       SUM(ended_at IS NULL) AS without_end_time,
       SUM(gpu_hours IS NULL) AS without_gpu_hours
FROM runs
GROUP BY status;
```

Only `RUNNING` jobs lack an end time, so the data obeys the rule today. To make the database guarantee it, add a table-level check: `CHECK (status = 'RUNNING' OR ended_at IS NOT NULL)`.

Now see the type system react to input. Affinity quietly converts a numeric string:

```sql-run dataset=mlops
INSERT INTO runs (experiment_id, run_name, model_type, learning_rate, status, started_at, triggered_by)
VALUES (1, 'typed-demo', 'xgboost', '0.05', 'RUNNING', '2024-12-01 08:00:00', 'priya');

SELECT run_name, learning_rate, typeof(learning_rate) AS stored_as
FROM runs WHERE run_name = 'typed-demo';
```

The text `'0.05'` was stored as a REAL because the column has REAL affinity. PostgreSQL would also accept this literal (untyped string literals are coerced to the column type), but would reject `'abc'` — which SQLite stores as text without complaint. That silent acceptance is the reason to add CHECKs such as `CHECK (typeof(learning_rate) IN ('real', 'null'))` or to use STRICT tables for anything important.

> [!INTERVIEW]
> A common design prompt is "create a table for X". Interviewers look for: a primary key; sensible types (no floats for money, a real timestamp type); NOT NULL on required columns; a UNIQUE constraint on the natural key; foreign keys; and a sentence on which columns are nullable *and why*.

### Generated columns and defaults

Two more column features are worth knowing. A **default** supplies a value when an INSERT omits the column (`DEFAULT CURRENT_TIMESTAMP`, `DEFAULT 0`). A **generated column** is computed from other columns of the same row and can never disagree with them:

```sql-run dataset=shop
CREATE TABLE line_demo (
  quantity   INTEGER NOT NULL CHECK (quantity > 0),
  unit_price REAL    NOT NULL,
  discount   REAL    NOT NULL DEFAULT 0 CHECK (discount BETWEEN 0 AND 1),
  line_total REAL GENERATED ALWAYS AS (ROUND(quantity * unit_price * (1 - discount), 2)) VIRTUAL
);
INSERT INTO line_demo (quantity, unit_price) VALUES (3, 19.99), (1, 249.0);
INSERT INTO line_demo (quantity, unit_price, discount) VALUES (2, 89.0, 0.15);
SELECT * FROM line_demo;
```

`line_total` is derived on read (`VIRTUAL`) or stored on write (`STORED`). Generated columns exist in SQLite 3.31+, MySQL 5.7+ and PostgreSQL 12+ (stored only), and are a clean way to keep a derived value without the risk of it drifting.

## Summary

- Character types: `CHAR` (fixed), `VARCHAR` (variable), large text types; mind character sets and collations.
- Numeric types: integers, exact `DECIMAL` for money, floating point for measurements.
- Temporal types: `DATE`, `TIME`, `TIMESTAMP`, intervals; use ISO-8601 and UTC.
- SQLite uses dynamic typing with column **affinity**; declared lengths are ignored unless you use STRICT tables.
- Design in three steps: list facts, refine (keys, single-valued columns, constraints), write DDL.

```quiz
[
  {"q": "Which type is the best fit for an account balance?", "options": ["FLOAT", "DOUBLE", "DECIMAL(12,2)", "VARCHAR(12)"], "answer": 2, "explain": "Exact decimal arithmetic avoids the rounding drift of binary floating point."},
  {"q": "In SQLite, what happens when you insert a 50-character string into a VARCHAR(10) column of an ordinary table?", "options": ["Error", "Truncated to 10 characters", "Stored in full", "Converted to NULL"], "answer": 2, "explain": "SQLite ignores declared lengths; only STRICT tables or CHECK constraints enforce limits."},
  {"q": "What affinity does SQLite give a column declared DATE?", "options": ["TEXT", "INTEGER", "NUMERIC", "BLOB"], "answer": 2, "explain": "DATE matches none of the INT/CHAR/TEXT/BLOB/REAL rules, so it falls through to NUMERIC; ISO date strings are then stored as TEXT values."},
  {"q": "Where should a flag's list of enabled environments be stored?", "options": ["A comma-separated column", "A child table with one row per (flag, environment)", "Three boolean columns always", "A JSON string"], "answer": 1, "explain": "Multi-valued attributes go in a separate table; that is the first normal form rule."},
  {"q": "Which declaration auto-generates keys in PostgreSQL in the modern standard way?", "options": ["AUTO_INCREMENT", "GENERATED ALWAYS AS IDENTITY", "IDENTITY(1,1)", "ROWID"], "answer": 1, "explain": "Identity columns are standard SQL; AUTO_INCREMENT is MySQL and IDENTITY(1,1) is SQL Server."},
  {"q": "Why does ISO-8601 text work for dates in SQLite?", "options": ["SQLite parses all date formats", "YYYY-MM-DD sorts and compares correctly as plain text", "It is stored as an integer", "It doesn't"], "answer": 1, "explain": "Most-significant parts come first, so lexical order equals chronological order."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 2 "Creating and Populating a Database" (MySQL data types; table creation steps 1-3). SQLite documentation, "Datatypes In SQLite".
