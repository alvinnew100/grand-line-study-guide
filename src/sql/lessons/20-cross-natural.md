# Cross joins, natural joins and densifying data

> **Before this lesson:** you should understand the Cartesian product, the all-pairs result of a join with no condition ([Inner joins](#/lesson/sql/inner-joins)), left joins, `COALESCE` and why `COUNT(column)` gives 0 for unmatched rows ([Outer joins](#/lesson/sql/outer-joins)), and grouping ([Aggregate functions and GROUP BY](#/lesson/sql/group-by)). The examples use `WITH` to name intermediate results; a one-line reminder is given where it first appears.

## In plain words

Two kinds of join are left to cover.

A **cross join** pairs every row of one table with every row of another. Earlier lessons treated that as an accident caused by a forgotten condition. Done on purpose, it is a tool for *making rows that are not stored anywhere*. Think of a blank timetable: write the five weekdays across the top and the eight lesson periods down the side, and you get a grid of 40 empty boxes before a single lesson has been entered. "Every weekday with every period" is a cross join.

That grid is the key to the most practical technique in this lesson. A report built only from stored rows shows only what happened. A day with no sales has no rows, so it is missing from the report, not shown as zero. If you first build the grid of every day you expect and then attach the data to it, the empty days appear with a zero. Filling in the missing rows this way is called **densifying** the data.

A **natural join** lets the database guess the join condition from the column names. It sounds convenient and is fragile; you need to recognise it mainly so that you can avoid it.

**Why it matters for a job.** "Daily sales for the last 30 days, including days with no sales" is a standard interview question and a real reporting need: charts, moving averages and week-over-week comparisons all go wrong when days are silently missing.

## Cross joins

To ask for every pairing deliberately, write `CROSS JOIN`:

```sql-run dataset=bank
SELECT pt.name AS product_type, d.name AS department
FROM product_type pt
CROSS JOIN department d;
```

There is no `ON`, because there is no matching rule. Three product types times three departments gives nine rows: "Customer Accounts" beside each of the three departments, then the next product type beside each, and so on. A comma between the tables (`FROM product_type pt, department d`) does the same; writing `CROSS JOIN` tells the reader that the all-pairs result is intended.

Pairing product types with departments has no business meaning. The useful cases come when the rows you need do not exist yet.

## Making rows from nothing: a table of numbers

Suppose a report needs one row for every day of 2024. No table holds "all days". An old and universal trick builds a run of numbers by cross-joining small lists of digits. Take three tiny one-column lists: the ones 0 to 9, the tens 0, 10, ... 90, and the hundreds 0, 100, 200, 300. Pair them all and add:

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

Each of the three parenthesised pieces is a small table built with `UNION ALL`. The cross joins produce every combination of one "ones" value, one "tens" value and one "hundreds" value: 10 × 10 × 4 = 400 combinations, whose sums are exactly the numbers 0 to 399. The query shows the first twelve.

A number becomes a date by adding it, as a count of days, to 1 January:

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

This is tidier. `WITH` names an intermediate result so later parts of the query can use it like a table. The first, `digits`, is a ten-row list written with `VALUES`. The second, `nums`, cross-joins `digits` with itself three times, giving every number from 0 to 999. The main query turns each number below 366 into a date: `'+' || n || ' days'` builds text such as `'+3 days'`, which `date()` understands as a modifier. 2024 is a leap year, hence 366 days.

> [!NOTE]
> **Shorter ways exist.** PostgreSQL has `generate_series(start, stop, step)`. Every modern database, including SQLite and MySQL 8, can count upward with a recursive query ([Recursive CTEs](#/lesson/sql/recursive-ctes)), used at the end of this lesson. Many companies keep a permanent **calendar table** with one row per day.

## Densifying: build the grid, then left join

Now the payoff. An ordinary grouped query reports only the days that *have* transactions:

```sql-run dataset=bank
SELECT date(txn_date) AS day, COUNT(*) AS txns
FROM txn
WHERE txn_date >= '2024-02-01' AND txn_date < '2024-02-15'
GROUP BY day
ORDER BY day;
```

Eight rows for a fourteen-day period. The list jumps from 1 February to 3 February; the 2nd is not there, because no transaction rows exist for it and a group is formed only from rows that exist. A chart drawn from this would join neighbouring points and hide the gaps. An "average of the last 7 rows" would cover more than 7 days.

To get a row for **every** day, generate the days and left-join the facts onto them:

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

Fourteen rows, and 2 February now appears with 0 transactions and an amount of 0. The recipe has three parts and is worth memorising:

1. **Scaffold**: generate every row that *should* exist. A scaffold is the complete framework of expected rows.
2. **`LEFT JOIN`** the real data onto the scaffold, so that scaffold rows without data are kept.
3. **`COUNT(column)` and `COALESCE`** turn the missing matches into zeros. `COUNT(t.txn_id)` skips the NULL of an unmatched day; `SUM` over no rows is NULL, which `COALESCE(..., 0)` replaces.

### A scaffold with two dimensions

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

Three named pieces. `months` is the list of months, `cats` a list of categories, and `sales` the units sold, already totalled to one row per month and category. Then `months CROSS JOIN cats` is the grid of every month with every category, and the left join attaches the sales that exist. Note that the facts were brought to the same grain as the grid before joining.

In machine-learning work this is how a complete *entity by time* table is built (one row per user per day) before rolling features are calculated.

### Other uses of a cross join

**Attaching a one-row result to every row**, for example a grand total needed for a percentage:

```sql-run dataset=bank
SELECT a.product_cd,
       ROUND(SUM(a.avail_balance), 2) AS balance,
       ROUND(100.0 * SUM(a.avail_balance) / t.total, 1) AS pct_of_total
FROM account a
CROSS JOIN (SELECT SUM(avail_balance) AS total FROM account) t
GROUP BY a.product_cd, t.total
ORDER BY pct_of_total DESC;
```

The subquery `t` has a single row, the total of all balances. Cross-joining a one-row table to `account` multiplies the row count by one: it only adds a `total` column to every account row. Checking accounts hold 44.8% of all balances.

**Generating test data**: cross-join a handful of names, cities and dates to get thousands of rows.

**All pairs for comparison**: add a filter such as `a.id < b.id`, as in the tournament example of [Three or more tables, self joins and non-equi joins](#/lesson/sql/multi-self-joins).

> [!WARNING]
> Row counts multiply. Cross-joining two tables of a million rows each asks for a million million rows. Keep at least one side tiny, and filter as early as you can.

## Natural joins

A **natural join** has no `ON`. The database joins on **every column that has the same name in both tables**.

```sql-run dataset=bank
SELECT a.account_id, a.cust_id, c.cust_type_cd, c.fed_id
FROM account a
NATURAL JOIN customer c
LIMIT 5;
```

`account` and `customer` share exactly one column name, `cust_id`, so this is the same as `JOIN customer c ON a.cust_id = c.cust_id`. Convenient, and fragile, in two opposite ways.

**No shared name: an accidental cross join.** Join `account` to `branch` naturally:

```sql-run dataset=bank
SELECT COUNT(*) AS rows_returned
FROM account a
NATURAL JOIN branch b;
```

336 rows. `account` calls its column `open_branch_id` and `branch` calls its column `branch_id`. No names match, so there is no condition at all, and the database quietly returns every pair: 84 × 4 = 336.

**Too many shared names: no rows.** `product` and `product_type` both have `product_type_cd`, the intended link. They also both have a column called `name`, holding unrelated descriptions.

```sql-run dataset=bank
SELECT COUNT(*) AS products_naturally_joined_to_types
FROM product NATURAL JOIN product_type;
```

Zero. The natural join requires *both* shared columns to be equal. A product's name never equals its type's name, so nothing matches.

There is a third danger. A natural join that works today can break tomorrow: add an `updated_at` column to both tables and every natural join between them silently begins to require equal timestamps.

> [!TIP]
> **Avoid `NATURAL JOIN`** and write the condition out. If you like the brevity, `USING (cust_id)` gives it to you while still naming the column, so a new same-named column cannot change the join.

## The whole join family

| Join | Keeps | Typical use |
|---|---|---|
| `INNER JOIN` | matching pairs only | following a link that always has a partner |
| `LEFT JOIN` | all left rows | optional links, counts that include zero, anti-joins |
| `RIGHT JOIN` | all right rows | rewrite as a `LEFT JOIN` |
| `FULL JOIN` | everything from both sides | reconciling two sources |
| `CROSS JOIN` | every combination | generating rows, scaffolds, attaching totals |
| `NATURAL JOIN` | pairs equal on all same-named columns | avoid |

## Worked example: a complete activity grid

The scaffold technique is easiest to appreciate on a table that is *mostly* gaps. The shop's `logins` table has one row per customer per day on which they logged in. A picture of activity needs one cell for **every** customer on **every** day, including days on which nobody logged in.

**Step 1: the two dimensions.** A handful of customers and a calendar of fourteen days:

```sql-run dataset=shop
WITH digits(d) AS (VALUES (0),(1),(2),(3),(4),(5),(6),(7),(8),(9)),
     days AS (SELECT date('2024-03-01', '+' || (a.d + 10 * b.d) || ' days') AS day
              FROM digits a CROSS JOIN digits b
              WHERE a.d + 10 * b.d < 14),
     people AS (SELECT DISTINCT customer_id FROM logins WHERE customer_id <= 21)
SELECT (SELECT COUNT(*) FROM days) AS days,
       (SELECT COUNT(*) FROM people) AS customers,
       (SELECT COUNT(*) FROM days CROSS JOIN people) AS grid_cells;
```

14 days, 4 customers, 56 cells. The size of the grid is known before any data is attached, which is the point.

**Step 2: attach the facts and summarise.** Left-join the logins onto the grid. A missing match means "did not log in".

```sql-run dataset=shop
WITH digits(d) AS (VALUES (0),(1),(2),(3),(4),(5),(6),(7),(8),(9)),
     days AS (SELECT date('2024-03-01', '+' || (a.d + 10 * b.d) || ' days') AS day
              FROM digits a CROSS JOIN digits b
              WHERE a.d + 10 * b.d < 14),
     people AS (SELECT DISTINCT customer_id FROM logins WHERE customer_id <= 21)
SELECT p.customer_id,
       group_concat(CASE WHEN l.customer_id IS NULL THEN '.' ELSE '#' END, '') AS first_two_weeks,
       COUNT(l.login_date) AS active_days,
       COUNT(*) - COUNT(l.login_date) AS inactive_days
FROM people p
CROSS JOIN days d
LEFT JOIN logins l ON l.customer_id = p.customer_id AND l.login_date = d.day
GROUP BY p.customer_id
ORDER BY p.customer_id;
```

Each customer gets a strip of 14 characters, `#` for a day with a login and `.` for a day without. Customer 4 shows `.#.#..#.######`: 9 active days and 5 inactive ones. Without the scaffold you could count active days, but **inactive days could not be counted at all**, because there are no rows for them. (The strip depends on rows reaching `group_concat` in day order, which holds here because the days are generated in order. SQLite 3.44 and later let you state it: `group_concat(... ORDER BY d.day)`.)

**Step 3: totals per day, empty days included.** This version makes the calendar with a recursive query: start at 1 March and keep adding one day until 10 March.

```sql-run dataset=shop
WITH RECURSIVE days(day) AS (
  SELECT '2024-03-01' UNION ALL SELECT date(day, '+1 day') FROM days WHERE day < '2024-03-10'
)
SELECT d.day, COUNT(l.customer_id) AS customers_logged_in
FROM days d
LEFT JOIN logins l ON l.login_date = d.day
GROUP BY d.day
ORDER BY d.day;
```

It is shorter than the digits trick and is the form you will usually write today. How the recursion works is explained in [Recursive CTEs](#/lesson/sql/recursive-ctes).

## Ways to generate rows, compared

| Technique | Works in | Notes |
|---|---|---|
| Cross-joined digit lists | every database, including old MySQL | wordy but universal |
| Recursive query | SQLite, PostgreSQL, MySQL 8+, SQL Server | compact; very long series may hit a recursion limit |
| `generate_series(a, b, step)` | PostgreSQL, DuckDB, some SQLite builds | shortest; also produces timestamps |
| Permanent calendar or numbers table | every database | fastest; can also record holidays, financial periods, week numbers |

For reports that run every day, a calendar table is the usual choice. It is generated once, and it can carry business facts (is this day a public holiday? which financial quarter?) that no function can work out.

> [!INTERVIEW]
> "Report daily sales for the last 30 days, including days with no sales" separates people who know `GROUP BY` from people who know its limits. The expected answer: generate the 30 dates, `LEFT JOIN` the sales onto them, and show `COALESCE(SUM(amount), 0)`.

## Pitfalls

- **An accidental cross join** from a forgotten condition, or from a `NATURAL JOIN` with no shared column names.
- **A natural join on accidental names** such as `name`, `id` or `created_at`.
- **A scaffold at the wrong grain.** The facts must be totalled to the scaffold's grain before, or while, joining.
- **Filtering the fact table in `WHERE`** after the left join removes the zero rows you worked to create. Put such filters in `ON`, or inside the subquery that totals the facts.
- **A function around the join column** (`date(t.txn_date) = days.day`) stops an index on that column from being used. On large tables join on a range instead: `t.txn_date >= day AND t.txn_date < next_day`.

## Summary

- `CROSS JOIN` returns every combination; use it on purpose to generate rows.
- Cross-joined digit lists, recursive queries, `generate_series` and calendar tables all produce runs of numbers and dates.
- **Densify** a report with scaffold, then `LEFT JOIN`, then `COALESCE`, so that gaps show as zeros.
- `NATURAL JOIN` joins on all same-named columns and is fragile; prefer `ON` or `USING`.

## Glossary

- **Cross join** — a join with no condition that returns every row of one table paired with every row of the other.
- **Cartesian product** — the mathematical name for that all-pairs result.
- **Row generator** — a query that produces rows, such as a run of numbers or dates, that are not stored in any table.
- **Numbers table** — a table (stored or generated) holding the whole numbers 0, 1, 2, ...
- **Calendar table (date dimension)** — a permanent table with one row per day, often with extra facts about each day.
- **Scaffold** — the complete set of rows a report should contain, built before any data is attached.
- **Densifying** — filling in rows for which no data exists, so that gaps show as zeros.
- **Sparse / dense data** — data with gaps where nothing happened / data with a row for every expected case.
- **Natural join** — a join whose condition is equality on every column that has the same name in both tables.
- **`USING`** — a join shorthand that names the shared column explicitly.
- **`generate_series`** — a function, in PostgreSQL and some other databases, that returns a run of numbers or timestamps.

```quiz
[
  {"q": "A table with 12 rows is cross-joined with a table of 5 rows. How many rows result?", "options": ["12", "17", "60", "5"], "answer": 2, "explain": "A cross join produces every combination: 12 x 5 = 60."},
  {"q": "What columns does NATURAL JOIN match on?", "options": ["Primary and foreign keys", "All columns with the same name in both tables", "The first column of each table", "Columns of the same type"], "answer": 1, "explain": "It ignores declared keys entirely and uses identical column names."},
  {"q": "account NATURAL JOIN branch, which have no column names in common, returns...", "options": ["An error", "No rows", "The cross join of the two tables", "A join on branch_id"], "answer": 2, "explain": "With no shared names there is no condition, so every pair is returned."},
  {"q": "Why does a report grouped by date omit days without transactions?", "options": ["GROUP BY skips zeros", "Groups are formed only from rows that exist", "Dates must be indexed", "A HAVING clause removes them"], "answer": 1, "explain": "No rows, no group. Generate the days and LEFT JOIN the data onto them."},
  {"q": "What are the three steps of densifying a report?", "options": ["Filter, sort, limit", "Scaffold, LEFT JOIN, COALESCE", "Group, having, order", "Union, intersect, except"], "answer": 1, "explain": "Generate every expected row, attach the facts with an outer join, and replace NULL with zero."},
  {"q": "How many rows do three cross-joined copies of a 10-row digits table give?", "options": ["30", "100", "1000", "10"], "answer": 2, "explain": "10 x 10 x 10 = 1000 combinations, giving the numbers 0 to 999."},
  {"q": "Which is the safer shorthand for a join on a same-named column?", "options": ["NATURAL JOIN", "USING (col)", "CROSS JOIN", "A comma join"], "answer": 1, "explain": "USING names the column, so a new same-named column added later cannot change the join."},
  {"q": "After days LEFT JOIN txn, which expression shows 0 for a day with no transactions?", "options": ["COUNT(*)", "COUNT(t.txn_id)", "SUM(t.amount)", "MAX(t.txn_id)"], "answer": 1, "explain": "COUNT of a column from the joined table skips the NULL of an unmatched day; COUNT(*) would count that row as 1, and SUM would be NULL."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 10 "Joins Revisited" (cross joins, including generating a year of dates, and natural joins), restated in original wording with this guide's own datasets.
