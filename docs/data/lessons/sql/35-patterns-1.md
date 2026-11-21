# Top-N, deduplication, pivoting and medians

> **Before this lesson:** this is a lesson of recipes that combine earlier tools. You should be comfortable with `GROUP BY` and `HAVING` ([HAVING, multi-column groups and rollups](#/lesson/sql/having-rollup)), `CASE` inside aggregates ([CASE patterns](#/lesson/sql/case-patterns)), ranking functions and `OVER` ([Window basics and ranking](#/lesson/sql/ranking)), running totals with frames ([LAG, LEAD, running totals and frames](#/lesson/sql/lag-lead-frames)) and CTEs ([Common table expressions](#/lesson/sql/ctes)).

## In plain words

A cook does not invent a new technique for every dish. A small number of techniques (a white sauce, a dough, a stock) are learned once and reused everywhere. Analytical SQL is similar. Interview questions and real reporting tasks draw on a surprisingly small set of recurring **patterns**: shapes of problem, each with a standard solution. Once you recognise the shape, the query nearly writes itself.

This lesson and the next are a catalogue of those patterns. This one covers seven:

1. **Top-N per group**: the best few rows in each group.
2. **The Nth highest value**: "the second-highest salary".
3. **Deduplication**: finding and removing repeated records.
4. **Pivot and unpivot**: turning rows into columns and back.
5. **Median and percentiles**: the middle value, and the value below which 90% fall.
6. **Percent of total**: each item's share, and the running share.
7. **"Has all of"**: groups that contain every item on a list.

Each comes with the recipe, the variations interviewers ask for, and the traps.

**Why it matters for a job.** These seven shapes cover a large share of the SQL questions asked for analyst, data-engineer and data-scientist roles, and of the queries behind everyday dashboards. Knowing them turns "I have never seen this problem" into "this is a top-N per group".

## A method before the patterns

For any analytical question, settle three things before typing:

1. **Grain.** What does one row of the answer stand for? One customer? One customer per month?
2. **Inputs.** Which tables hold the facts, and what does one row of each stand for? Where could a join multiply rows?
3. **Ties and NULLs.** What if two rows tie for first place? What should happen to missing values?

Saying these aloud is also what interviewers want to hear.

## Pattern 1: top-N per group

*"For each X, return the N rows with the highest Y."* The latest order of each customer. The three best-selling products of each category.

**Recipe:** number the rows within each group in a CTE, then keep the low numbers in the query that follows.

```sql-run dataset=shop
WITH product_sales AS (
  SELECT p.category_id, p.name, SUM(oi.quantity) AS units
  FROM order_items oi
  JOIN products p ON p.product_id = oi.product_id
  JOIN orders o   ON o.order_id = oi.order_id
  WHERE o.status = 'delivered'
  GROUP BY p.category_id, p.product_id, p.name
),
ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY category_id ORDER BY units DESC, name) AS rn
  FROM product_sales
)
SELECT c.name AS category, r.name AS product, r.units
FROM ranked r
JOIN categories c ON c.category_id = r.category_id
WHERE r.rn <= 2
ORDER BY category, units DESC;
```

Three steps, each with its own grain:

- `product_sales`: one row per product, with the units sold in delivered orders.
- `ranked`: the same rows, each numbered within its category from the best seller down. `name` at the end of the window's `ORDER BY` is a **tie-breaker**: it decides the order when two products sold equally.
- The final query keeps numbers 1 and 2 and looks up the category name.

In Accessories the top two are the 27in Monitor (23 units) and the Wireless Mouse (19).

Choose the ranking function by the rule for ties:

| Requirement | Function |
|---|---|
| exactly N rows per group | `ROW_NUMBER()` with a tie-breaker |
| everyone tied within the first N positions | `RANK()` |
| the top N different values, with everyone who has them | `DENSE_RANK()` |

**Without window functions** (old MySQL), there are two classic alternatives. For N = 1, a correlated subquery that picks the one wanted row:

```sql-run dataset=shop
SELECT o.customer_id, o.order_id, o.order_date
FROM orders o
WHERE o.order_id = (SELECT o2.order_id FROM orders o2
                    WHERE o2.customer_id = o.customer_id
                    ORDER BY o2.order_date DESC, o2.order_id DESC
                    LIMIT 1)
ORDER BY o.customer_id
LIMIT 6;
```

For each order, the subquery finds the id of the same customer's most recent order. The order is kept if that id is its own.

For any N, "count how many beat me": keep a row when fewer than N rows of its group have a strictly greater value.

```sql-run dataset=shop
SELECT p.category_id, p.name, p.price
FROM products p
WHERE (SELECT COUNT(*) FROM products p2
       WHERE p2.category_id = p.category_id AND p2.price > p.price) < 2
ORDER BY p.category_id, p.price DESC
LIMIT 8;
```

A product is among the two dearest of its category if fewer than two products there cost more. This compares every row with every other row of its group, so it is slow on large tables. It is worth seeing because it shows what ranking *means*.

(PostgreSQL also offers `DISTINCT ON (customer_id) ... ORDER BY customer_id, order_date DESC` for N = 1.)

## Pattern 2: the Nth highest value

*"The second-highest salary." "The third-largest order."* Use `DENSE_RANK`, so that repeats of the top value do not occupy position 2:

```sql-run dataset=bank
WITH r AS (
  SELECT avail_balance, DENSE_RANK() OVER (ORDER BY avail_balance DESC) AS dr
  FROM account
)
SELECT DISTINCT avail_balance AS second_highest_balance
FROM r
WHERE dr = 2;
```

46764.47. If three accounts shared the highest balance, all three would have dense rank 1 and the next different balance would still be rank 2. `DISTINCT` returns the value once even if several accounts hold it.

The same answer with `LIMIT` and `OFFSET` over the distinct values, sorted from the top: skip one, take one.

```sql-run dataset=bank
SELECT (SELECT DISTINCT avail_balance
        FROM account
        ORDER BY avail_balance DESC
        LIMIT 1 OFFSET 1) AS second_highest_balance;
```

Wrapping the query in an outer `SELECT (...)` makes it return **NULL**, instead of no row at all, when there is no second value. Interview problems usually ask for exactly that behaviour.

## Pattern 3: deduplication

Duplicate records arrive through loads that were run twice, forms submitted twice, and sources that were merged. Removing them is called **deduplication**. There are three sub-problems.

**Find the duplicates.** Group by the **business key**, the value that identifies the real-world thing (here the email address), and keep the groups with more than one row:

```sql-run dataset=shop
SELECT lower(trim(email)) AS email_key, COUNT(*) AS copies,
       group_concat(import_id) AS import_ids
FROM customer_imports
GROUP BY email_key
HAVING COUNT(*) > 1
ORDER BY copies DESC, email_key
LIMIT 6;
```

`hana.muller@example.com` was imported three times, as rows 1, 18 and 38. Notice `lower(trim(email))`: `' A@X.COM'` and `'a@x.com'` are the same person. Bringing values to one standard form before comparing them is called **normalising** them. Deciding what "the same" means is the hard part; the SQL is the easy part.

**Choose one survivor per key.** Number the copies of each key, with an `ORDER BY` that says which copy wins (the earliest, the latest, the most complete), and keep number 1:

```sql-run dataset=shop
WITH ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY lower(trim(email))
                               ORDER BY imported_at, import_id) AS rn
  FROM customer_imports
)
SELECT import_id, lower(trim(email)) AS email, full_name, source, imported_at
FROM ranked
WHERE rn = 1
ORDER BY email
LIMIT 6;
```

Two tools that look as if they should work, and do not:

- `SELECT DISTINCT` removes only rows that are identical in *every* selected column. Copies that differ in their import time are all kept.
- `GROUP BY key` with `MIN(imported_at)` gives the earliest time, but not the other columns *of that same row*.

`ROW_NUMBER` is the right tool, because it selects whole rows.

**Delete the losers.** Reuse the same numbering. (Each Run starts from a fresh copy of the data.)

```sql-run dataset=shop
DELETE FROM customer_imports
WHERE import_id IN (
  SELECT import_id FROM (
    SELECT import_id, ROW_NUMBER() OVER (PARTITION BY lower(trim(email))
                                         ORDER BY imported_at, import_id) AS rn
    FROM customer_imports)
  WHERE rn > 1);

SELECT COUNT(*) AS rows_left FROM customer_imports;
```

30 rows remain of 50. To stop duplicates coming back, add a unique index on the normalised key: `CREATE UNIQUE INDEX ... ON customer_imports (lower(trim(email)))`.

A related pattern is **collapsing consecutive repeats**: keep a row only when its value differs from the previous row's (`value <> LAG(value)`). It is used to shorten histories of status changes.

## Pattern 4: pivot and unpivot

**Pivot (long to wide):** one output column per category value, using an aggregate around a `CASE`. Orders per month, by status:

```sql-run dataset=shop
SELECT strftime('%Y-%m', order_date) AS month,
       SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) AS delivered,
       SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled,
       SUM(CASE WHEN status = 'returned'  THEN 1 ELSE 0 END) AS returned,
       COUNT(*) AS total
FROM orders
GROUP BY month
ORDER BY month
LIMIT 6;
```

Each `CASE` gives 1 for the orders of "its" status and 0 for the rest, so each `SUM` counts one status. January 2024: 5 delivered, 1 cancelled, 1 returned, 8 in total.

For a value instead of a count, use `MAX(CASE WHEN key = 'x' THEN value END)`. This widens a table that stores one measurement per row:

```sql-run dataset=mlops
SELECT r.run_id, r.model_type,
       MAX(CASE WHEN m.metric_name = 'accuracy' THEN m.value END) AS accuracy,
       MAX(CASE WHEN m.metric_name = 'f1'       THEN m.value END) AS f1,
       MAX(CASE WHEN m.metric_name = 'auc'      THEN m.value END) AS auc
FROM runs r
JOIN metrics m ON m.run_id = r.run_id
WHERE r.experiment_id = 3
GROUP BY r.run_id, r.model_type
ORDER BY auc DESC;
```

One row per training run, with three measurements side by side.

**Unpivot (wide to long):** `UNION ALL`, one `SELECT` per column:

```sql-run dataset=mlops
SELECT run_id, 'learning_rate' AS param, CAST(learning_rate AS TEXT) AS value FROM runs WHERE run_id <= 2
UNION ALL
SELECT run_id, 'batch_size', CAST(batch_size AS TEXT) FROM runs WHERE run_id <= 2
UNION ALL
SELECT run_id, 'model_type', model_type FROM runs WHERE run_id <= 2
ORDER BY run_id, param;
```

Three columns of `runs` become three rows per run. `CAST(... AS TEXT)` is needed because a number and a piece of text must share the single `value` column.

The limitation is the same in both directions: the columns must be listed in the text of the query.

## Pattern 5: median and percentiles

An average is pulled about by extreme values: one laptop order among many book orders raises it sharply. The **median** is the middle value when the values are sorted, so half are below it and half above; one extreme value does not move it. Few databases have a `MEDIAN` function (Oracle, Snowflake and DuckDB do; PostgreSQL has `percentile_cont(0.5) WITHIN GROUP (ORDER BY x)`). In SQLite and MySQL it is built by hand.

**Recipe:** number the sorted rows and count them. With an odd count `n`, the median is the row at position (n + 1) ÷ 2. With an even count there are two middle rows, n ÷ 2 and n ÷ 2 + 1, and the median is their average. One expression covers both cases: take positions `(n + 1) / 2` and `(n + 2) / 2` using integer division. For n = 5 both are 3. For n = 6 they are 3 and 4.

```sql-run dataset=shop
WITH order_value AS (
  SELECT o.order_id, SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS v
  FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
  WHERE o.status = 'delivered'
  GROUP BY o.order_id
),
numbered AS (
  SELECT v, ROW_NUMBER() OVER (ORDER BY v) AS rn, COUNT(*) OVER () AS n
  FROM order_value
)
SELECT ROUND(AVG(v), 2) AS median_order_value,
       (SELECT ROUND(AVG(v), 2) FROM order_value) AS mean_order_value,
       MAX(n) AS orders
FROM numbered
WHERE rn IN ((n + 1) / 2, (n + 2) / 2);
```

- `order_value`: one row per delivered order with its value.
- `numbered`: each order's position when sorted by value (`rn`), and the total number of orders (`n`) on every row.
- The final query keeps the middle position or positions and averages them.

Over 171 delivered orders the median is 263.40 and the average 763.33. The average is almost three times the median: a few very large orders pull it up. Such a lopsided spread is called **skewed**, and it is the reason the median is often the more honest "typical value".

For a median per group, add `PARTITION BY` to both window functions and group the final query.

Other percentiles use the same numbering. The 90th percentile (p90) is the value at position 0.9 × n, rounded up. Written with whole-number arithmetic, because this page has no rounding-up function, that position is `(9 * n + 9) / 10`:

```sql-run dataset=mlops
WITH numbered AS (
  SELECT deployment_id, latency_ms,
         ROW_NUMBER() OVER (PARTITION BY deployment_id ORDER BY latency_ms) AS rn,
         COUNT(*)     OVER (PARTITION BY deployment_id) AS n
  FROM predictions
)
SELECT deployment_id, MAX(n) AS predictions,
       MAX(CASE WHEN rn = (n + 1) / 2 THEN latency_ms END)               AS p50_latency,
       MAX(CASE WHEN rn = (9 * n + 9) / 10 THEN latency_ms END)            AS p90_latency,
       MAX(latency_ms) AS max_latency
FROM numbered
GROUP BY deployment_id
HAVING MAX(n) >= 15
ORDER BY p90_latency DESC
LIMIT 6;
```

For deployment 3, half of the 22 predictions took 121 milliseconds or less, 90% took 214 or less, and the slowest took 262. Targets for response time are stated in percentiles for exactly this reason: an average hides the slow tail that annoys users.

A related figure, the **mode** (the most frequent value), is a top-1 over counts: `GROUP BY value`, then rank by `COUNT(*) DESC`.

## Pattern 6: percent of total and cumulative share

*"What fraction of revenue does each category bring in?"* Divide by a window total; no second query is needed.

```sql-run dataset=shop
WITH cat AS (
  SELECT c.name AS category, SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS revenue
  FROM order_items oi
  JOIN products p   ON p.product_id = oi.product_id
  JOIN categories c ON c.category_id = p.category_id
  JOIN orders o     ON o.order_id = oi.order_id
  WHERE o.status = 'delivered'
  GROUP BY c.name
)
SELECT category, ROUND(revenue, 2) AS revenue,
       ROUND(100.0 * revenue / SUM(revenue) OVER (), 1) AS pct_of_total,
       ROUND(100.0 * SUM(revenue) OVER (ORDER BY revenue DESC
                                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
             / SUM(revenue) OVER (), 1) AS cumulative_pct
FROM cat
ORDER BY revenue DESC;
```

`SUM(revenue) OVER ()` is the grand total, available on every row. The second window is a running total from the largest category down. Laptops alone are 58.5% of revenue; with Kitchen, Furniture and Audio the running share reaches 82.2%. Four categories of ten account for four fifths of the money.

With `PARTITION BY` in the divisor you get a share within a group, such as each product's share of its category.

## Pattern 7: "all of" and "both" conditions

*"Customers who bought both A and B." "Runs that recorded all three measurements."* A single row cannot equal two different values, so `WHERE x = 'A' AND x = 'B'` finds nothing. Instead: keep the candidate rows, group, and count the different matches.

```sql-run dataset=mlops
SELECT run_id
FROM metrics
WHERE metric_name IN ('accuracy', 'f1', 'auc')
GROUP BY run_id
HAVING COUNT(DISTINCT metric_name) = 3
LIMIT 5;
```

A run is kept when, among the three names asked for, it has three different ones: all of them.

Alternatives are `INTERSECT` of two queries, or two `EXISTS` conditions. For *"bought A but not B"*, use `HAVING SUM(product = 'A') > 0 AND SUM(product = 'B') = 0`, or `EXISTS ... AND NOT EXISTS ...`.

## A checklist for the interview

- State the **grain** of the result.
- **Aggregate before you rank; rank before you filter.**
- Decide the **tie** rule and add a tie-breaker.
- Watch for **multiplied rows** when joining to order items; total them first.
- Write `100.0` (or `1.0 *`) to avoid whole-number division.
- Handle **NULLs** (`COALESCE`, `COUNT(column)`), and say what you assumed.
- Test in your head on a small case: a group with a tie, an empty group, a NULL.

> [!INTERVIEW]
> Name the pattern before you write: "this is top-N per group, so I will number the rows per category in a CTE and filter on the number". Then state the tie rule you are assuming and ask whether it is the one wanted. Recognising the shape, and raising ties and NULLs unprompted, matters more to the interviewer than typing speed.

## Pitfalls

- **Filtering on a window function in `WHERE`.** It must be computed in a CTE or subquery first.
- **`ROW_NUMBER` with no tie-breaker.** Which of two tied rows survives can change from run to run.
- **`RANK` for "Nth highest".** A repeated top value leaves a gap, so rank 2 may not exist. Use `DENSE_RANK`.
- **`SELECT DISTINCT` as a deduplication tool** when the copies differ in some column.
- **Comparing keys without normalising them**: stray spaces and capital letters hide duplicates.
- **Reporting an average for skewed data** without the median beside it.
- **Hand-listed pivot columns** that go out of date when a new category appears.

## Summary

| Pattern | Core tool |
|---|---|
| Top-N per group | `ROW_NUMBER`, `RANK` or `DENSE_RANK` in a CTE; filter outside |
| Nth highest | `DENSE_RANK() = N`, or `DISTINCT ... LIMIT 1 OFFSET N-1` |
| Deduplicate | `ROW_NUMBER() OVER (PARTITION BY key ORDER BY preference)`; keep `rn = 1` |
| Pivot / unpivot | aggregate around `CASE` / `UNION ALL` |
| Median, percentiles | `ROW_NUMBER` with `COUNT(*) OVER`; pick the middle position or positions |
| Percent of total | `x / SUM(x) OVER ()`; running share with an ordered frame |
| "Has all of" | `GROUP BY ... HAVING COUNT(DISTINCT ...) = k` |

## Glossary

- **Pattern** — a recurring shape of problem with a standard solution.
- **Grain** — what one row of a table or result stands for.
- **Top-N per group** — keeping the first N rows of each group according to some order.
- **Tie-breaker** — an extra ordering column that makes the order certain when values are equal.
- **Deduplication** — finding and removing repeated records.
- **Business key** — the value that identifies a real-world thing, such as an email address.
- **Normalising (a value)** — bringing values to one standard form, for example trimmed and lower-case, before comparing them.
- **Survivor** — the one copy kept when duplicates are removed.
- **Pivot / unpivot** — turning row values into columns / columns into rows.
- **Median** — the middle value of a sorted list; half the values lie on each side.
- **Mean** — the ordinary average: the total divided by the count.
- **Percentile** — the value below which a given percentage of the values fall (p90: 90%).
- **Mode** — the most frequent value.
- **Skewed distribution** — a spread of values with a long tail on one side, which pulls the mean away from the median.
- **Cumulative share** — the running total expressed as a percentage of the grand total.

```quiz
[
  {"q": "You need exactly one row per customer: their most recent order. Which function?", "options": ["RANK()", "DENSE_RANK()", "ROW_NUMBER() with a tie-breaker", "NTILE(1)"], "answer": 2, "explain": "ROW_NUMBER gives different numbers even to tied rows, so rn = 1 selects exactly one row when dates tie."},
  {"q": "Why use DENSE_RANK for 'second-highest salary'?", "options": ["It is faster", "Repeats of the highest value share rank 1, so rank 2 is the next different value", "It skips NULLs", "RANK is not standard"], "answer": 1, "explain": "With ROW_NUMBER a repeated top value would occupy position 2, and with RANK position 2 would be skipped."},
  {"q": "Why can't SELECT DISTINCT deduplicate rows that differ in imported_at?", "options": ["DISTINCT ignores dates", "DISTINCT removes only rows identical in every selected column", "DISTINCT needs GROUP BY", "It can"], "answer": 1, "explain": "To keep one of several differing copies you must number them and choose."},
  {"q": "For n sorted rows, which positions hold the median value or values, using integer division?", "options": ["n/2 only", "(n+1)/2 and (n+2)/2", "n/2 and n", "1 and n"], "answer": 1, "explain": "They are the same position when n is odd and the two middle positions when n is even; average them."},
  {"q": "How do you compute each row's percentage of the grand total without a join?", "options": ["x / SUM(x)", "x / SUM(x) OVER ()", "x / COUNT(*)", "x / MAX(x)"], "answer": 1, "explain": "An empty OVER makes the total available on every row."},
  {"q": "Which query finds runs having all of accuracy, f1 and auc?", "options": ["WHERE metric_name = 'accuracy' AND metric_name = 'f1' AND metric_name = 'auc'", "WHERE metric_name IN (...) GROUP BY run_id HAVING COUNT(DISTINCT metric_name) = 3", "WHERE metric_name IN (...) only", "GROUP BY metric_name HAVING COUNT(*) = 3"], "answer": 1, "explain": "A single row has one metric name; count the different names per run."},
  {"q": "What is the first thing to settle before writing an analytical query?", "options": ["Which indexes exist", "The grain of the result: what one output row stands for", "The version of the SQL dialect", "The column aliases"], "answer": 1, "explain": "The grain decides the grouping, which joins are safe and what the aggregates mean."},
  {"q": "Delivered orders have a mean value of 763 and a median of 263. What does that tell you?", "options": ["The data contains errors", "A few very large orders pull the mean up; the typical order is much smaller", "Half the orders are worth exactly 763", "The median was computed wrongly"], "answer": 1, "explain": "A mean far above the median is the sign of a skewed distribution with a long tail of large values."}
]
```

> **Source:** Patterns built on Beaulieu, *Learning SQL*, ch. 8 (grouping), ch. 9 (subqueries), ch. 11 (result set transformations) and 3rd ed. ch. 16 (analytic functions); the problem styles follow common SQL interview categories and are written from scratch with this guide's own datasets.
