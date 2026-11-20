# Top-N, deduplication, pivoting and medians

SQL interviews — and real analytics work — draw on a surprisingly small set of recurring problem shapes. Once you can recognise the shape, the query almost writes itself. This lesson and the next are a pattern catalogue built on everything in the track. Here: **top-N per group**, **Nth highest value**, **deduplication**, **pivot and unpivot**, **median and percentiles**, and **percent of total / running share**. Each comes with the canonical solution, the variations interviewers ask for, and the traps.

A general method first. For any analytics question, pin down three things before typing:

1. **Grain** — what does one row of the answer represent? (One customer? One customer per month?)
2. **Inputs** — which tables hold the facts, and at what grain? Where could a join fan out?
3. **Tie and NULL rules** — what if two rows tie for first? What about missing values?

Saying these out loud is also what interviewers want to hear.

## Pattern 1: top-N per group

*"For each X, return the N rows with the highest Y."* The latest order per customer, the three best-selling products per category, the best run per experiment.

**Recipe:** rank within the group in a CTE, filter on the rank outside.

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

Choose the ranking function by the tie rule:

| Requirement | Function |
|---|---|
| exactly N rows per group | `ROW_NUMBER()` + deterministic tie-breaker |
| everyone tied within the top N positions | `RANK()` |
| the top N distinct values, with everyone who has them | `DENSE_RANK()` |

**Without window functions** (older MySQL), two classic alternatives. A correlated subquery for N = 1:

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

And a "count how many beat me" self join for general N: keep a row when fewer than N rows in its group have a strictly greater value. It is O(n²) and is mostly of historical interest, but it shows what ranking *means*:

```sql-run dataset=shop
SELECT p.category_id, p.name, p.price
FROM products p
WHERE (SELECT COUNT(*) FROM products p2
       WHERE p2.category_id = p.category_id AND p2.price > p.price) < 2
ORDER BY p.category_id, p.price DESC
LIMIT 8;
```

(PostgreSQL also has `DISTINCT ON (customer_id) … ORDER BY customer_id, order_date DESC` for N = 1, and `LATERAL` joins for general N.)

## Pattern 2: Nth highest value

*"Second-highest salary", "third-largest order".* Use `DENSE_RANK` so that duplicates of the top value don't occupy position 2:

```sql-run dataset=bank
WITH r AS (
  SELECT avail_balance, DENSE_RANK() OVER (ORDER BY avail_balance DESC) AS dr
  FROM account
)
SELECT DISTINCT avail_balance AS second_highest_balance
FROM r
WHERE dr = 2;
```

The equivalent with `LIMIT/OFFSET` over distinct values:

```sql-run dataset=bank
SELECT (SELECT DISTINCT avail_balance
        FROM account
        ORDER BY avail_balance DESC
        LIMIT 1 OFFSET 1) AS second_highest_balance;
```

Wrapping the query as a scalar subquery makes it return **NULL** (rather than no rows) when there is no second value — the behaviour LeetCode-style problems usually specify.

## Pattern 3: deduplication

Duplicates arrive through retried loads, double form submissions, merged sources. Three sub-problems.

**Find the duplicates** — group by the *business key* and keep groups with more than one row:

```sql-run dataset=shop
SELECT lower(trim(email)) AS email_key, COUNT(*) AS copies,
       group_concat(import_id) AS import_ids
FROM customer_imports
GROUP BY email_key
HAVING COUNT(*) > 1
ORDER BY copies DESC, email_key
LIMIT 6;
```

Notice the normalisation: `' A@X.COM'` and `'a@x.com'` are the same person. Deciding what "the same" means is the hard part; the SQL is easy.

**Select one survivor per key** — `ROW_NUMBER` with an ORDER BY expressing which copy wins (earliest, latest, most complete):

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

`SELECT DISTINCT` only removes rows that are identical in *every* selected column, so it cannot pick one of several differing copies. And `GROUP BY key` with `MIN(imported_at)` gives the earliest timestamp but not the other columns *of that same row* — the bare-column trap. `ROW_NUMBER` is the right tool.

**Delete the losers** — reuse the same ranking:

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

Then prevent recurrence with a unique index on the normalised key (`CREATE UNIQUE INDEX … ON customer_imports (lower(trim(email)))`).

A related pattern is **collapsing consecutive duplicates** — keep a row only when its value differs from the previous row's (`value <> LAG(value)`), used to compress status histories.

## Pattern 4: pivot and unpivot

**Pivot (long → wide):** one output column per category value, via an aggregate around CASE (conditional-logic module). Monthly orders by status:

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

For values rather than counts, `MAX(CASE WHEN key = 'x' THEN value END)` — the standard way to widen an entity–attribute–value table such as ML metrics:

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

**Unpivot (wide → long):** `UNION ALL`, one branch per column (or a cross join with a list of column names plus CASE):

```sql-run dataset=mlops
SELECT run_id, 'learning_rate' AS param, CAST(learning_rate AS TEXT) AS value FROM runs WHERE run_id <= 2
UNION ALL
SELECT run_id, 'batch_size', CAST(batch_size AS TEXT) FROM runs WHERE run_id <= 2
UNION ALL
SELECT run_id, 'model_type', model_type FROM runs WHERE run_id <= 2
ORDER BY run_id, param;
```

The limitation is the same in both directions: columns must be enumerated in the query text.

## Pattern 5: median and percentiles

The mean is distorted by outliers (one laptop order among many book orders); the **median** is the middle value. Few engines have a `MEDIAN` function (Oracle, Snowflake, DuckDB do; PostgreSQL has `percentile_cont(0.5) WITHIN GROUP (ORDER BY x)`); SQLite and MySQL need it built by hand.

**Recipe:** number the sorted rows and count them; the median is the row at position `(n+1)/2` for odd n, or the average of rows `n/2` and `n/2 + 1` for even n. With integer division, `(n+1)/2` and `(n+2)/2` cover both cases — they are equal when n is odd and the two middle positions when n is even.

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

The mean is far above the median — the distribution is right-skewed. Add `PARTITION BY` to both window functions (and group the final query) for a median per group; that is the *Median Order Value by Country* problem.

Other percentiles use the same numbering. The p90 by the nearest-rank method is the row at position `ceil(0.9 × n)`:

```sql-run dataset=mlops
WITH numbered AS (
  SELECT deployment_id, latency_ms,
         ROW_NUMBER() OVER (PARTITION BY deployment_id ORDER BY latency_ms) AS rn,
         COUNT(*)     OVER (PARTITION BY deployment_id) AS n
  FROM predictions
)
SELECT deployment_id, MAX(n) AS predictions,
       MAX(CASE WHEN rn = (n + 1) / 2 THEN latency_ms END)               AS p50_latency,
       MAX(CASE WHEN rn = CAST(ceil(0.9 * n) AS INTEGER) THEN latency_ms END) AS p90_latency,
       MAX(latency_ms) AS max_latency
FROM numbered
GROUP BY deployment_id
HAVING MAX(n) >= 15
ORDER BY p90_latency DESC
LIMIT 6;
```

Latency SLOs are stated in percentiles precisely because averages hide the slow tail.

A related statistic, the **mode** (most frequent value), is a top-1-per-group over counts: `GROUP BY value`, then rank by `COUNT(*) DESC`.

## Pattern 6: percent of total and cumulative share

*"What fraction of revenue does each category contribute?"* Divide by a window total — no self join needed:

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

The cumulative column is a Pareto analysis: how many categories make up 80% of revenue. With `PARTITION BY` in the denominator you get share-within-group (each product's share of its category).

## Pattern 7: "all of" and "both" conditions

*"Customers who bought both A and B"*, *"runs that logged all three metrics"*. One row cannot satisfy two different equalities, so filter to the candidates, group, and count distinct matches:

```sql-run dataset=mlops
SELECT run_id
FROM metrics
WHERE metric_name IN ('accuracy', 'f1', 'auc')
GROUP BY run_id
HAVING COUNT(DISTINCT metric_name) = 3
LIMIT 5;
```

Alternatives: `INTERSECT` of two queries, or two `EXISTS` conditions. For *"bought A but not B"* use `HAVING SUM(product = 'A') > 0 AND SUM(product = 'B') = 0`, or `EXISTS … AND NOT EXISTS …`.

## A checklist for the interview

- State the **grain** of the result.
- **Aggregate before you rank**; rank before you filter.
- Decide **ties** explicitly and add a tie-breaker.
- Watch **fan-out** when joining to line items; pre-aggregate.
- Use `100.0` (or `1.0 *`) to avoid integer division.
- Handle **NULLs** (`COALESCE`, `COUNT(col)`), and say what you assumed.
- Test on a small example: one group with a tie, one empty group, one NULL.

## Summary

| Pattern | Core tool |
|---|---|
| Top-N per group | `ROW_NUMBER / RANK / DENSE_RANK` in a CTE, filter outside |
| Nth highest | `DENSE_RANK() = N`, or `DISTINCT … LIMIT 1 OFFSET N-1` |
| Deduplicate | `ROW_NUMBER() OVER (PARTITION BY key ORDER BY preference)`, keep `rn = 1` |
| Pivot / unpivot | aggregate around `CASE` / `UNION ALL` |
| Median, percentiles | `ROW_NUMBER` + `COUNT(*) OVER`, pick middle position(s) |
| Percent of total | `x / SUM(x) OVER ()`; cumulative with an ordered frame |
| "Has all of" | `GROUP BY … HAVING COUNT(DISTINCT …) = k` |

```quiz
[
  {"q": "You need exactly one row per customer: their most recent order. Which function?", "options": ["RANK()", "DENSE_RANK()", "ROW_NUMBER() with a tie-breaker", "NTILE(1)"], "answer": 2, "explain": "ROW_NUMBER assigns distinct numbers, so rn = 1 selects exactly one row even when dates tie."},
  {"q": "Why use DENSE_RANK for 'second-highest salary'?", "options": ["It is faster", "Duplicates of the highest value share rank 1, so rank 2 is the next distinct value", "It skips NULLs", "RANK is not standard"], "answer": 1, "explain": "With ROW_NUMBER or RANK, a duplicated top value could occupy or skip position 2."},
  {"q": "Why can't SELECT DISTINCT deduplicate rows that differ in imported_at?", "options": ["DISTINCT ignores dates", "DISTINCT only removes rows identical in every selected column", "DISTINCT needs GROUP BY", "It can"], "answer": 1, "explain": "To keep one of several differing copies you must rank them and choose."},
  {"q": "For n rows, which positions hold the median value(s) using integer division?", "options": ["n/2 only", "(n+1)/2 and (n+2)/2", "n/2 and n", "1 and n"], "answer": 1, "explain": "They coincide for odd n and are the two middle rows for even n; average them."},
  {"q": "How do you compute each row's percent of the grand total without a join?", "options": ["x / SUM(x)", "x / SUM(x) OVER ()", "x / COUNT(*)", "x / MAX(x)"], "answer": 1, "explain": "An empty OVER makes the total available on every row."},
  {"q": "Which query finds runs having all of accuracy, f1 and auc?", "options": ["WHERE metric_name = 'accuracy' AND metric_name = 'f1' AND metric_name = 'auc'", "WHERE metric_name IN (...) GROUP BY run_id HAVING COUNT(DISTINCT metric_name) = 3", "WHERE metric_name IN (...) only", "GROUP BY metric_name HAVING COUNT(*) = 3"], "answer": 1, "explain": "A single row has one metric name; count distinct names per run."},
  {"q": "What is the first thing to establish before writing an analytics query?", "options": ["The indexes available", "The grain of the result - what one output row represents", "The SQL dialect version", "The column aliases"], "answer": 1, "explain": "Grain determines the grouping, the joins that are safe and what the aggregates mean."}
]
```

> **Source:** Patterns built on Beaulieu, *Learning SQL*, ch. 8 (grouping), ch. 9 (subqueries), ch. 11 (result set transformations) and 3rd ed. ch. 16 (analytic functions); problem styles follow common LeetCode / DataLemur SQL interview categories, written from scratch.
