# NULL: the four-letter word

The book titles its NULL section "Null: That Four-Letter Word", and with good reason: NULL causes more silent wrong answers than any other feature of SQL. NULL is not zero, not an empty string, not false. It is the *absence of a value*, and SQL handles it with a three-valued logic that surprises almost everyone the first time. This lesson explains what NULL means, how it behaves in comparisons, arithmetic, aggregates, sorting and joins, and the tools — `IS NULL`, `COALESCE`, `NULLIF` — that tame it.

## What NULL means

The book lists three situations in which a value is NULL:

- **Not applicable** — an ATM transaction has no teller, so `txn.teller_emp_id` is NULL.
- **Value not yet known** — a prediction's true label hasn't arrived yet (`predictions.actual_label`), a run hasn't finished (`runs.ended_at`).
- **Value undefined** — an account opened for a product that has no meaningful value for some column.

All three are represented by the same marker, which is part of the trouble: the database cannot tell you *why* a value is missing. If the distinction matters, model it explicitly (a status column, a separate table).

## Rule 1: NULL is never equal to anything

An expression can *be* null, but it can never *equal* null. Comparing anything to NULL — even NULL itself — yields neither TRUE nor FALSE but a third truth value, **UNKNOWN**.

```sql-run dataset=bank
SELECT NULL = NULL      AS null_eq_null,
       NULL <> NULL     AS null_ne_null,
       1 = NULL         AS one_eq_null,
       NULL IS NULL     AS is_null_test;
```

SQLite shows UNKNOWN as an empty (NULL) cell. Only `IS NULL` gives a definite answer.

Because WHERE keeps only rows whose condition is TRUE, a test like `= NULL` silently matches nothing:

```sql-run dataset=bank
SELECT COUNT(*) AS wrong FROM txn WHERE teller_emp_id = NULL;
```

```sql-run dataset=bank
SELECT COUNT(*) AS atm_or_online FROM txn WHERE teller_emp_id IS NULL;
```

The first query is a bug that produces no error. Use `IS NULL` and `IS NOT NULL`.

> [!NOTE]
> Standard SQL also has `IS DISTINCT FROM` / `IS NOT DISTINCT FROM`, a null-safe comparison where NULL equals NULL (PostgreSQL, SQLite 3.39+). SQLite also accepts `a IS b`; MySQL spells it `a <=> b`.

## Rule 2: three-valued logic

With UNKNOWN in play, AND, OR and NOT follow these truth tables:

| AND | TRUE | FALSE | UNKNOWN |
|---|---|---|---|
| **TRUE** | TRUE | FALSE | UNKNOWN |
| **FALSE** | FALSE | FALSE | FALSE |
| **UNKNOWN** | UNKNOWN | FALSE | UNKNOWN |

| OR | TRUE | FALSE | UNKNOWN |
|---|---|---|---|
| **TRUE** | TRUE | TRUE | TRUE |
| **FALSE** | TRUE | FALSE | UNKNOWN |
| **UNKNOWN** | TRUE | UNKNOWN | UNKNOWN |

`NOT UNKNOWN` is UNKNOWN. A useful intuition: treat UNKNOWN as "could be either". `FALSE AND anything` is FALSE regardless; `TRUE OR anything` is TRUE regardless; otherwise the answer is unknown.

The consequence for queries: a row whose condition evaluates to UNKNOWN is **dropped by WHERE** just like a FALSE one — and *also* dropped by the negated condition. Rows with NULLs can fall out of both a filter and its opposite.

## The classic trap: forgetting NULLs in a negative filter

The book's example: find every transaction *not* handled by teller 7. The obvious query:

```sql-run dataset=bank
SELECT COUNT(*) AS not_teller_7 FROM txn WHERE teller_emp_id <> 7;
```

…misses all the ATM/online transactions, because `NULL <> 7` is UNKNOWN. Count them all to see the gap:

```sql-run dataset=bank
SELECT COUNT(*)                                        AS total,
       SUM(CASE WHEN teller_emp_id = 7 THEN 1 ELSE 0 END) AS teller_7,
       SUM(CASE WHEN teller_emp_id <> 7 THEN 1 ELSE 0 END) AS not_7,
       SUM(CASE WHEN teller_emp_id IS NULL THEN 1 ELSE 0 END) AS no_teller
FROM txn;
```

`teller_7 + not_7` does not add up to `total`; the difference is exactly `no_teller`. The correct query is:

```sql-run dataset=bank
SELECT COUNT(*) FROM txn WHERE teller_emp_id <> 7 OR teller_emp_id IS NULL;
```

> [!TIP]
> Whenever you write `<>`, `NOT IN` or `NOT LIKE` on a nullable column, ask: *"what should happen to NULL rows?"* — and write the answer into the query.

## The NOT IN trap

`x NOT IN (a, b, NULL)` expands to `x <> a AND x <> b AND x <> NULL`. The last term is UNKNOWN, so the whole condition can never be TRUE: **NOT IN against a list containing NULL returns no rows at all.**

```sql-run dataset=bank
SELECT COUNT(*) AS employees_not_handling_txns
FROM employee
WHERE emp_id NOT IN (SELECT teller_emp_id FROM txn);
```

Zero — even though many employees (the president, loan officers) never act as tellers — because the subquery returns NULLs. Fixes:

```sql-run dataset=bank
SELECT COUNT(*) AS fixed_with_filter
FROM employee
WHERE emp_id NOT IN (SELECT teller_emp_id FROM txn WHERE teller_emp_id IS NOT NULL);
```

```sql-run dataset=bank
SELECT COUNT(*) AS fixed_with_not_exists
FROM employee e
WHERE NOT EXISTS (SELECT 1 FROM txn t WHERE t.teller_emp_id = e.emp_id);
```

`NOT EXISTS` is immune to the problem and is the idiom to prefer. (Plain `IN` is safe: `x IN (a, NULL)` is TRUE when `x = a`.)

## NULL in expressions

Almost any operation involving NULL produces NULL:

```sql-run dataset=mlops
SELECT run_id, status, started_at, ended_at,
       round((julianday(ended_at) - julianday(started_at)) * 24, 2) AS hours,
       'run-' || ended_at AS label
FROM runs
WHERE status IN ('RUNNING', 'FINISHED')
LIMIT 6;
```

Running jobs have NULL `ended_at`, so `hours` and `label` are NULL too. (Oracle is an exception for strings: it treats `''` as NULL and `'a' || NULL` as `'a'`. MySQL's `CONCAT('a', NULL)` returns NULL; `CONCAT_WS` skips NULLs.)

## COALESCE, IFNULL and NULLIF

`COALESCE(a, b, c, ...)` returns the first non-NULL argument — the standard way to supply a default:

```sql-run dataset=bank
SELECT txn_id, amount,
       COALESCE(teller_emp_id, 0)               AS teller_or_zero,
       COALESCE(CAST(teller_emp_id AS TEXT), 'ATM/online') AS channel
FROM txn
LIMIT 8;
```

`IFNULL(a, b)` (SQLite, MySQL) and `NVL(a, b)` (Oracle) and `ISNULL(a, b)` (SQL Server) are two-argument vendor versions; prefer COALESCE.

`NULLIF(a, b)` does the reverse: it returns NULL when `a = b`, else `a`. Its killer use is avoiding division by zero:

```sql-run dataset=bank
SELECT product_cd,
       SUM(avail_balance) / NULLIF(COUNT(CASE WHEN avail_balance > 0 THEN 1 END), 0) AS avg_positive
FROM account
GROUP BY product_cd;
```

For a product whose positive count is zero, the divisor becomes NULL and the result is NULL instead of an error (PostgreSQL raises "division by zero"; SQLite and MySQL quietly return NULL).

## NULL in aggregates, sorting, grouping and uniqueness

A quick tour — each is covered again in its own module:

- **Aggregates ignore NULLs.** `COUNT(col)`, `SUM`, `AVG`, `MIN`, `MAX` skip NULL values; `COUNT(*)` counts rows.

```sql-run dataset=mlops
SELECT COUNT(*) AS predictions,
       COUNT(actual_label) AS labeled,
       COUNT(*) - COUNT(actual_label) AS awaiting_label
FROM predictions;
```

- **AVG of a column with NULLs** averages only the non-NULL values — not the same as treating NULL as zero. `AVG(COALESCE(x, 0))` is the other interpretation; choose deliberately.
- **Sorting:** NULLs sort first (SQLite, MySQL) or last (PostgreSQL, Oracle) — see the previous lesson.
- **GROUP BY** puts all NULLs into *one* group, even though NULL ≠ NULL.
- **DISTINCT** treats NULLs as duplicates of each other.
- **UNIQUE constraints** generally allow *many* NULLs (SQLite, PostgreSQL, MySQL), since NULLs are not equal. SQL Server allows only one.
- **Joins:** `ON a.x = b.x` never matches NULL to NULL, so rows with NULL keys silently disappear from inner joins.

## Designing to reduce NULL pain

- Declare columns `NOT NULL` whenever a value must exist.
- Use `DEFAULT` for values that have a natural starting point (`status DEFAULT 'pending'`).
- Distinguish *unknown* from *not applicable* with explicit columns when it matters (the `mlops` dataset uses `status = 'RUNNING'` to explain a NULL `ended_at`).
- Never use magic values (`-1`, `'1900-01-01'`) as a NULL substitute; they poison averages and comparisons.

## Pitfalls checklist

| Mistake | Fix |
|---|---|
| `col = NULL` | `col IS NULL` |
| `col <> x` dropping NULL rows | `col <> x OR col IS NULL` |
| `NOT IN (subquery)` with NULLs | `NOT EXISTS`, or filter NULLs in the subquery |
| `COUNT(*)` after a left join | `COUNT(right_table.key)` |
| NULL arithmetic surprises | `COALESCE` with a sensible default |
| Division by zero | `NULLIF(divisor, 0)` |

## Worked example: an audit of NULLs in a table

Before trusting any analysis, find out where the NULLs are. A profile of the `runs` table shows how to do it systematically:

```sql-run dataset=mlops
SELECT COUNT(*)                              AS total_rows,
       COUNT(*) - COUNT(parent_run_id)       AS null_parent,
       COUNT(*) - COUNT(learning_rate)       AS null_learning_rate,
       COUNT(*) - COUNT(batch_size)          AS null_batch_size,
       COUNT(*) - COUNT(ended_at)            AS null_ended_at,
       COUNT(*) - COUNT(gpu_hours)           AS null_gpu_hours
FROM runs;
```

`COUNT(*) - COUNT(col)` is the number of NULLs in `col`, because `COUNT(col)` skips them. Each NULL count has a *meaning* you should be able to state: no parent (not part of a sweep), no batch size (tree models — "not applicable"), no end time (still running — "not yet known"). When you cannot explain a NULL, you have found a data-quality problem.

Next, see how those NULLs would distort a naive analysis. Average batch size by model type:

```sql-run dataset=mlops
SELECT model_type,
       COUNT(*) AS runs,
       COUNT(batch_size) AS runs_with_batch_size,
       AVG(batch_size) AS avg_batch_size
FROM runs
GROUP BY model_type
ORDER BY runs DESC;
```

Model types with no batch sizes show a NULL average — correct, and far better than a misleading 0. If a dashboard insisted on a number, `COALESCE(AVG(batch_size), 0)` would turn "undefined" into "zero", a lie that looks like data.

## Three-valued logic, traced row by row

Abstract truth tables stick better with real rows. Take five transactions and evaluate one condition and its negation:

```sql-run dataset=bank
SELECT txn_id, teller_emp_id,
       teller_emp_id = 9          AS is_9,
       NOT (teller_emp_id = 9)    AS not_9,
       teller_emp_id = 9 OR teller_emp_id IS NULL AS is_9_or_missing,
       COALESCE(teller_emp_id, -1) <> 9           AS not_9_incl_missing
FROM txn
WHERE txn_id IN (1, 2, 3, 4, 5)
ORDER BY txn_id;
```

For the row whose teller is NULL, both `is_9` and `not_9` are NULL (UNKNOWN): the row belongs to *neither* the filter nor its negation. The last two columns show the two standard repairs — an explicit `OR … IS NULL`, or mapping NULL to a sentinel with COALESCE before comparing.

The same thing happens inside `CASE`, joins, and CHECK constraints, with one important twist in each:

| Context | What UNKNOWN does |
|---|---|
| `WHERE`, `HAVING`, join `ON` | row is **rejected** (treated like FALSE) |
| `CASE WHEN cond` | branch is **not taken**; falls through to the next WHEN / ELSE |
| `CHECK (cond)` | row is **accepted** (only FALSE violates a check) |
| `UNIQUE` | NULLs do not collide with each other |

That asymmetry between WHERE and CHECK surprises people: `CHECK (price > 0)` happily admits a NULL price.

## NULL and joins

A NULL foreign key never matches anything in an equality join, so the row silently disappears from an inner join:

```sql-run dataset=bank
SELECT (SELECT COUNT(*) FROM txn) AS all_txns,
       (SELECT COUNT(*) FROM txn t JOIN employee e ON e.emp_id = t.teller_emp_id) AS joined_to_teller,
       (SELECT COUNT(*) FROM txn t LEFT JOIN employee e ON e.emp_id = t.teller_emp_id) AS left_joined;
```

The inner join loses every ATM/online transaction. A total computed from that join would understate the bank's activity with no error and no warning. A LEFT JOIN keeps them (with NULL employee columns); the *Joins revisited* module covers it.

To deliberately match NULL with NULL — for example when comparing two versions of a table column by column — use the null-safe comparison:

```sql-run dataset=bank
SELECT NULL = NULL                  AS plain_equals,
       NULL IS NULL                 AS is_null,
       NULL IS NOT DISTINCT FROM NULL AS null_safe_equals,
       1 IS DISTINCT FROM NULL      AS one_differs_from_null;
```

## Choosing a NULL policy for a report

There is no universally right treatment; there is only an explicit one. For any metric touching nullable columns, decide and document:

1. **Exclude** rows with NULL (the default behaviour of aggregates) — "average latency of *labelled* predictions".
2. **Impute** a value with COALESCE — "treat missing discount as 0".
3. **Report NULL as its own category** — often the most honest:

```sql-run dataset=bank
SELECT COALESCE(b.name, '(ATM / online)') AS channel,
       COUNT(*) AS txns,
       ROUND(SUM(t.amount), 2) AS amount
FROM txn t
LEFT JOIN branch b ON b.branch_id = t.execution_branch_id
GROUP BY channel
ORDER BY txns DESC;
```

GROUP BY places all NULLs in one group, and COALESCE gives that group a readable label instead of a blank cell.

> [!INTERVIEW]
> Two NULL questions come up constantly. (1) *"What's the difference between COUNT(\*) and COUNT(column)?"* — rows versus non-NULL values. (2) *"Why does my NOT IN query return nothing?"* — a NULL in the subquery; fix with NOT EXISTS. Being able to explain *why* (UNKNOWN is not TRUE) is what distinguishes an understanding of three-valued logic from a memorised rule.

## Summary

- NULL marks a missing value; it is never equal (or unequal) to anything, including NULL.
- Comparisons with NULL yield UNKNOWN; WHERE keeps only TRUE rows, so UNKNOWN rows vanish from both a filter and its negation.
- Test with `IS NULL` / `IS NOT NULL`; null-safe comparison with `IS [NOT] DISTINCT FROM`.
- `NOT IN` with a NULL in the list returns nothing — prefer `NOT EXISTS`.
- Expressions with NULL yield NULL; use `COALESCE` for defaults and `NULLIF` to avoid division by zero.
- Aggregates skip NULLs; `COUNT(*)` counts rows.

```quiz
[
  {"q": "What does NULL = NULL evaluate to?", "options": ["TRUE", "FALSE", "UNKNOWN", "An error"], "answer": 2, "explain": "Any comparison involving NULL yields UNKNOWN."},
  {"q": "What is FALSE AND UNKNOWN?", "options": ["TRUE", "FALSE", "UNKNOWN", "NULL error"], "answer": 1, "explain": "FALSE AND anything is FALSE."},
  {"q": "What is TRUE OR UNKNOWN?", "options": ["TRUE", "FALSE", "UNKNOWN", "Depends on the engine"], "answer": 0, "explain": "TRUE OR anything is TRUE."},
  {"q": "WHERE emp_id NOT IN (SELECT teller_emp_id FROM txn) returns zero rows because...", "options": ["All employees are tellers", "The subquery contains NULL, making every comparison UNKNOWN", "NOT IN is not supported", "emp_id is the primary key"], "answer": 1, "explain": "x <> NULL is UNKNOWN, so the AND-chain can never be TRUE."},
  {"q": "COUNT(actual_label) counts...", "options": ["all rows", "rows where actual_label is not NULL", "distinct labels", "NULL rows"], "answer": 1, "explain": "COUNT(column) skips NULLs; COUNT(*) counts rows."},
  {"q": "Which expression returns NULL instead of dividing by zero?", "options": ["x / COALESCE(y, 0)", "x / NULLIF(y, 0)", "x / IFNULL(y, 1)", "x / y"], "answer": 1, "explain": "NULLIF(y, 0) turns a zero divisor into NULL, and x / NULL is NULL."},
  {"q": "How many NULLs can a UNIQUE column hold in SQLite and PostgreSQL?", "options": ["None", "One", "Many", "Only if indexed"], "answer": 2, "explain": "NULLs are not equal to each other, so they don't violate uniqueness (SQL Server differs)."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 4 "Filtering" — "Null: That Four-Letter Word"; ch. 8 "How Nulls Are Handled"; ch. 11 "Handling Null Values".
