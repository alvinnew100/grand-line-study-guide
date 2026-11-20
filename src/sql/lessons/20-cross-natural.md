# Cross joins, natural joins and densifying data

Two more join types complete the picture. The **cross join** — the Cartesian product you were warned about — turns out to be genuinely useful for *generating* rows. The **natural join** lets the server guess the join condition, and is best understood so that you can avoid it. Along the way this lesson introduces one of the most practical reporting techniques: building a complete scaffold of rows (every day, every category, every combination) and attaching data to it, so that gaps show up as zeros instead of silently missing.

## Cross joins

A cross join pairs every row of one table with every row of another. You saw it happen by accident when a join condition was missing. To ask for it deliberately, say so:

```sql-run dataset=bank
SELECT pt.name AS product_type, d.name AS department
FROM product_type pt
CROSS JOIN department d;
```

3 product types × 3 departments = 9 rows. Writing `CROSS JOIN` documents that the Cartesian product is intentional; a comma (`FROM product_type pt, department d`) does the same thing with less clarity.

The book is frank that cross joins are used rarely. But it then gives the one family of problems where they are indispensable: **when you need to fabricate rows that are not stored anywhere**.

## Generating rows: a table of numbers

Suppose you want one row for every day of 2024, to report daily activity. No table holds "all days". The book's trick is to build a set of numbers by cross-joining small sets of digits. Three single-column sets — ones `{0..9}`, tens `{0,10,..,90}`, hundreds `{0,100,200,300}` — cross-joined produce every sum from 0 to 399:

```sql-run dataset=bank
SELECT ones.num + tens.num + hundreds.num AS n
FROM (SELECT 0 AS num UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
      UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) ones
CROSS JOIN
     (SELECT 0 AS num UNION ALL SELECT 10 UNION ALL SELECT 20 UNION ALL SELECT 30 UNION ALL SELECT 40
      UNION ALL SELECT 50 UNION ALL SELECT 60 UNION ALL SELECT 70 UNION ALL SELECT 80 UNION ALL SELECT 90) tens
CROSS JOIN
     (SELECT 0 AS num UNION ALL SELECT 100 UNION ALL SELECT 200 UNION ALL SELECT 300) hundreds
ORDER BY n
LIMIT 12;
```

10 × 10 × 4 = 400 rows from 24 literal values. Turn each number into a date by adding it, as days, to 1 January, and keep the ones that fall inside the year:

```sql-run dataset=bank
WITH digits(d) AS (VALUES (0),(1),(2),(3),(4),(5),(6),(7),(8),(9)),
     nums AS (SELECT a.d + 10 * b.d + 100 * c.d AS n
              FROM digits a CROSS JOIN digits b CROSS JOIN digits c)
SELECT date('2024-01-01', '+' || n || ' days') AS dt
FROM nums
WHERE n < 366
ORDER BY dt
LIMIT 5;
```

Here the same `digits` set is cross-joined with itself three times (0–999), which is tidier. 2024 is a leap year, so 366 days — and SQLite's date arithmetic takes care of February for us.

> [!NOTE]
> **Easier generators exist in modern engines.** PostgreSQL has `generate_series(start, stop, step)` for numbers and timestamps. SQLite has a `generate_series` table-valued function in some builds, and — everywhere, including MySQL 8 — you can use a **recursive CTE** (`WITH RECURSIVE days(d) AS (SELECT '2024-01-01' UNION ALL SELECT date(d, '+1 day') FROM days WHERE d < '2024-12-31')`), covered in the CTE module. Many warehouses simply keep a permanent **calendar (date dimension) table**.

## Densifying: scaffold, then left join

Now the payoff. A plain GROUP BY reports only days that *have* transactions:

```sql-run dataset=bank
SELECT date(txn_date) AS day, COUNT(*) AS txns
FROM txn
WHERE txn_date >= '2024-02-01' AND txn_date < '2024-02-15'
GROUP BY day
ORDER BY day;
```

Days without transactions are simply absent. A chart drawn from this would connect neighbouring points and hide the gaps; a moving average over "the last 7 rows" would cover more than 7 days. To get a row for **every** day, generate the days and outer-join the facts to them — the book's final example in this chapter:

```sql-run dataset=bank
WITH digits(d) AS (VALUES (0),(1),(2),(3),(4),(5),(6),(7),(8),(9)),
     days AS (SELECT date('2024-02-01', '+' || (a.d + 10 * b.d) || ' days') AS day
              FROM digits a CROSS JOIN digits b
              WHERE a.d + 10 * b.d < 14)
SELECT days.day, COUNT(t.txn_id) AS txns, COALESCE(ROUND(SUM(t.amount), 2), 0) AS amount
FROM days
LEFT JOIN txn t ON date(t.txn_date) = days.day
GROUP BY days.day
ORDER BY days.day;
```

Fourteen rows, zeros included. The recipe has three parts and is worth memorising:

1. **Scaffold** — generate every row that *should* exist (cross join, series, or calendar table).
2. **LEFT JOIN** the facts onto the scaffold.
3. **COALESCE / COUNT(col)** to turn missing matches into zeros.

### Scaffolds with two dimensions

The same recipe fills in missing *combinations*. Every category for every month, including months in which a category sold nothing:

```sql-run dataset=shop
WITH months AS (SELECT DISTINCT strftime('%Y-%m', order_date) AS month FROM orders
                WHERE order_date < '2024-04-01'),
     cats AS (SELECT category_id, name FROM categories WHERE parent_id = 1 OR parent_id = 2),
     sales AS (SELECT strftime('%Y-%m', o.order_date) AS month, p.category_id,
                      SUM(oi.quantity) AS units
               FROM orders o
               JOIN order_items oi ON oi.order_id = o.order_id
               JOIN products p ON p.product_id = oi.product_id
               GROUP BY month, p.category_id)
SELECT m.month, c.name AS category, COALESCE(s.units, 0) AS units
FROM months m
CROSS JOIN cats c
LEFT JOIN sales s ON s.month = m.month AND s.category_id = c.category_id
ORDER BY m.month, c.name;
```

`months CROSS JOIN cats` is the grid; `sales` is pre-aggregated to the same grain; the left join attaches what exists. In ML feature engineering this is how you build a dense *entity × time* table (one row per user per day) before computing rolling features.

### Other uses of cross joins

- **Attaching a single-row result to every row** — a grand total for percentage-of-total calculations:

```sql-run dataset=bank
SELECT a.product_cd,
       ROUND(SUM(a.avail_balance), 2) AS balance,
       ROUND(100.0 * SUM(a.avail_balance) / t.total, 1) AS pct_of_total
FROM account a
CROSS JOIN (SELECT SUM(avail_balance) AS total FROM account) t
GROUP BY a.product_cd, t.total
ORDER BY pct_of_total DESC;
```

- **Generating test data** — cross join a handful of names, cities and dates to get thousands of rows.
- **All pairs for comparison** — combine with a filter such as `a.id < b.id` (the tournament example in the joins module is a filtered self cross join).

> [!WARNING]
> Row counts multiply. Cross-joining two million-row tables asks for 10¹² rows. Keep at least one side tiny, and filter as early as possible.

## Natural joins

A **natural join** lets the server work out the join condition: it joins on **all columns that have the same name** in both tables.

```sql-run dataset=bank
SELECT a.account_id, a.cust_id, c.cust_type_cd, c.fed_id
FROM account a
NATURAL JOIN customer c
LIMIT 5;
```

`account` and `customer` share exactly one column name, `cust_id`, so this is equivalent to `JOIN customer c ON a.cust_id = c.cust_id`. Convenient — and fragile. The book immediately shows how it goes wrong: join `account` to `branch` naturally.

```sql-run dataset=bank
SELECT COUNT(*) AS rows_returned
FROM account a
NATURAL JOIN branch b;
```

`account` has `open_branch_id`; `branch` has `branch_id`. No column names match, so there is no join condition at all and the server quietly produces the **cross join**: 84 × 4 = 336 rows.

The opposite failure is worse. `employee` and `individual` both have `fname` and `lname`; `branch`, `department`, `product` and `business` all have a column called `name`. A natural join between such tables matches on those *accidental* names:

```sql-run dataset=bank
SELECT COUNT(*) AS products_naturally_joined_to_types
FROM product NATURAL JOIN product_type;
```

Both tables have `product_type_cd` (the intended key) **and** `name` (unrelated descriptions). The natural join requires both to be equal, which never happens, so the result is zero rows.

And a natural join that works today can break tomorrow: add an `updated_at` column to both tables and every natural join between them silently starts requiring the timestamps to match.

> [!TIP]
> The book's verdict, and the industry's: **avoid NATURAL JOIN** and write the condition explicitly. If you like the brevity, `USING (cust_id)` gives it to you while still naming the column.

## Choosing a join type: a summary of the family

| Join | Keeps | Typical use |
|---|---|---|
| `INNER JOIN` | matching pairs only | follow a mandatory foreign key |
| `LEFT JOIN` | all left rows | optional relationships, counts including zero, anti-joins |
| `RIGHT JOIN` | all right rows | rewrite as LEFT |
| `FULL JOIN` | everything from both | reconciliation between two sources |
| `CROSS JOIN` | every combination | generating rows, scaffolds, attaching totals |
| `NATURAL JOIN` | matches on same-named columns | avoid |

## Pitfalls

- **Accidental cross join** from a forgotten condition (or a NATURAL JOIN with no common names).
- **Natural join on accidental column names** (`name`, `id`, `created_at`).
- **Scaffold at the wrong grain** — the facts must be aggregated to the scaffold's grain before (or while) joining.
- **Filtering the fact table in WHERE** after the left join — removes the zero rows you just created; put fact filters in ON or in the pre-aggregation.
- **Function on the join column** (`date(t.txn_date) = days.day`) prevents index use; for large tables join on a range (`t.txn_date >= day AND t.txn_date < next_day`).

## Summary

- `CROSS JOIN` returns every combination; use it deliberately to generate rows.
- Cross-joined digit sets (or `generate_series`, recursive CTEs, calendar tables) fabricate sequences of numbers and dates.
- **Densify** reports with scaffold → LEFT JOIN → COALESCE so that gaps appear as zeros.
- `NATURAL JOIN` joins on all same-named columns — fragile; prefer `ON` or `USING`.

```quiz
[
  {"q": "A table with 12 rows is cross-joined with a table of 5 rows. How many rows result?", "options": ["12", "17", "60", "5"], "answer": 2, "explain": "A cross join produces every combination: 12 x 5."},
  {"q": "What columns does NATURAL JOIN match on?", "options": ["Primary and foreign keys", "All columns with the same name in both tables", "The first column of each table", "Columns of the same type"], "answer": 1, "explain": "It ignores declared keys entirely and uses identical column names."},
  {"q": "account NATURAL JOIN branch (no common column names) returns...", "options": ["An error", "No rows", "The cross join of the two tables", "A join on branch_id"], "answer": 2, "explain": "With no shared names there is no condition, so every pair is returned."},
  {"q": "Why does a GROUP BY date report omit days without transactions?", "options": ["GROUP BY skips zeros", "Groups are only formed from rows that exist", "Dates must be indexed", "A HAVING clause removes them"], "answer": 1, "explain": "No rows, no group. Generate the days and LEFT JOIN the data to them."},
  {"q": "What are the three steps of densifying a report?", "options": ["Filter, sort, limit", "Scaffold, LEFT JOIN, COALESCE", "Group, having, order", "Union, intersect, except"], "answer": 1, "explain": "Generate every expected row, attach facts with an outer join, replace NULL with zero."},
  {"q": "How many rows do three cross-joined copies of a 10-row digits table give?", "options": ["30", "100", "1000", "10"], "answer": 2, "explain": "10 x 10 x 10 = 1000, the numbers 0 to 999."},
  {"q": "Which is the safer shorthand for a join on a same-named column?", "options": ["NATURAL JOIN", "USING (col)", "CROSS JOIN", "A comma join"], "answer": 1, "explain": "USING names the column explicitly, so new same-named columns cannot change the join."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 10 "Joins Revisited" (cross joins — including generating a year of dates — and natural joins).
