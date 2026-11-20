# LAG, LEAD, running totals and frames

Ranking functions compare a row with its whole partition. The second family of window functions looks at **neighbours**: the previous row, the next row, all rows so far, the last seven rows. They turn time-series questions — change since last month, running balance, moving average, time since the previous event — into one-line expressions. This lesson covers the offset functions `LAG`, `LEAD`, `FIRST_VALUE`, `LAST_VALUE` and `NTH_VALUE`, aggregate functions used as running and moving calculations, and the **frame clause** that controls exactly which rows an aggregate window sees.

## LAG and LEAD

`LAG(expr, n, default)` returns the value of `expr` from the row `n` rows **before** the current row within the partition (n defaults to 1); `LEAD` looks `n` rows **after**. If there is no such row the result is NULL, or `default` if you supply one.

```sql-run dataset=shop
WITH monthly AS (
  SELECT strftime('%Y-%m', order_date) AS month, COUNT(*) AS orders
  FROM orders
  GROUP BY month
)
SELECT month, orders,
       LAG(orders)  OVER (ORDER BY month) AS prev_month,
       LEAD(orders) OVER (ORDER BY month) AS next_month,
       orders - LAG(orders) OVER (ORDER BY month) AS change,
       ROUND(100.0 * (orders - LAG(orders) OVER (ORDER BY month)) / LAG(orders) OVER (ORDER BY month), 1) AS pct_change
FROM monthly
ORDER BY month;
```

The first month has no predecessor, so `prev_month` is NULL and the arithmetic that uses it is NULL too. This *period-over-period* calculation is a standard interview question; the pattern is always **aggregate to one row per period, then LAG**.

With `PARTITION BY`, each entity gets its own sequence. Days since each customer's previous order:

```sql-run dataset=shop
SELECT customer_id, order_id, order_date,
       LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS prev_order,
       CAST(julianday(order_date)
            - julianday(LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id)) AS INTEGER) AS days_since_prev
FROM orders
WHERE customer_id IN (5, 8)
ORDER BY customer_id, order_date;
```

Without the partition, the first order of customer 8 would be compared with the last order of customer 5 — a classic bug.

Typical uses of LAG/LEAD:

- **change detection** — did the status, price or model version change from the previous row?
- **gaps** — time since the previous event (sessionization, churn detection);
- **duration** — `LEAD(start_time)` gives the end of the current state;
- **deduplicating consecutive repeats** — keep rows where the value differs from `LAG(value)`.

```sql-run dataset=mlops
-- How long did each production deployment of the churn model stay live?
SELECT m.version, d.deployed_at,
       LEAD(d.deployed_at) OVER (ORDER BY d.deployed_at) AS replaced_at,
       ROUND(julianday(LEAD(d.deployed_at) OVER (ORDER BY d.deployed_at)) - julianday(d.deployed_at), 1) AS days_live
FROM deployments d
JOIN models m ON m.model_id = d.model_id
WHERE m.name = 'churn-model' AND d.environment = 'production'
ORDER BY d.deployed_at;
```

## Running totals

Give an aggregate function a window with `ORDER BY` and it becomes **cumulative**: for each row it aggregates from the start of the partition up to that row.

```sql-run dataset=bank
SELECT txn_id, txn_date, txn_type_cd, amount,
       CASE txn_type_cd WHEN 'CDT' THEN amount ELSE -amount END AS signed,
       ROUND(SUM(CASE txn_type_cd WHEN 'CDT' THEN amount ELSE -amount END)
             OVER (ORDER BY txn_date, txn_id), 2) AS running_net
FROM txn
WHERE account_id = 142
ORDER BY txn_date, txn_id;
```

Each row shows the net effect of all transactions so far. With a partition you get one running total per account, month, user…:

```sql-run dataset=shop
WITH daily AS (
  SELECT strftime('%Y-%m', order_date) AS month, order_date, COUNT(*) AS orders
  FROM orders
  WHERE order_date >= '2024-11-01'
  GROUP BY order_date
)
SELECT month, order_date, orders,
       SUM(orders) OVER (PARTITION BY month ORDER BY order_date) AS month_to_date,
       SUM(orders) OVER (ORDER BY order_date)                    AS since_november
FROM daily
ORDER BY order_date
LIMIT 12;
```

Other cumulative aggregates follow the same pattern: `MAX(x) OVER (ORDER BY t)` is the running maximum ("best validation score so far"), `COUNT(*) OVER (ORDER BY t)` a running count, `AVG` a cumulative average.

## The frame clause

How does the engine know that `SUM(...) OVER (ORDER BY t)` means "from the start up to here"? Every aggregate window has a **frame** — the subset of the partition, relative to the current row, that the function is applied to. The full syntax:

```
{ROWS | RANGE | GROUPS} BETWEEN frame_start AND frame_end
```

where the boundaries are:

| Boundary | Meaning |
|---|---|
| `UNBOUNDED PRECEDING` | first row of the partition |
| `n PRECEDING` | n rows (or units) before the current row |
| `CURRENT ROW` | the current row (or its peer group for RANGE) |
| `n FOLLOWING` | n rows after |
| `UNBOUNDED FOLLOWING` | last row of the partition |

The **defaults** are the part everyone must memorise:

- With **no ORDER BY** in the window: the frame is the **whole partition**.
- With **ORDER BY**: the frame is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` — the start of the partition through the current row *and all its peers* (rows with the same ORDER BY value).

That default explains running totals — and hides a trap.

### ROWS versus RANGE: the tie trap

`ROWS` counts physical rows. `RANGE` works on *values* of the ORDER BY expression, treating rows with equal values (**peers**) as one unit. With the default RANGE frame, tied rows all receive the same cumulative value — the total *including all of their peers*:

```sql-run dataset=shop
SELECT order_id, order_date, shipping_fee,
       SUM(shipping_fee) OVER (ORDER BY order_date)                                AS range_default,
       SUM(shipping_fee) OVER (ORDER BY order_date
                               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS rows_frame
FROM orders
WHERE order_date BETWEEN '2024-02-05' AND '2024-02-12'
ORDER BY order_date, order_id;
```

Wherever several orders share a date, `range_default` jumps once for the whole day and repeats, while `rows_frame` increases row by row. Neither is wrong; they answer different questions. To get a true row-by-row running total, either write `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` explicitly or make the ORDER BY unique (`ORDER BY order_date, order_id`) — ideally both.

> [!TIP]
> Make it a habit: when you write a running or moving aggregate, **state the frame explicitly** with `ROWS`. You never have to remember the default, and `ROWS` frames are also faster.

### Moving averages

A sliding frame gives moving (rolling) calculations. A 3-row moving average — the current row and the two before it:

```sql-run dataset=shop
WITH monthly AS (
  SELECT strftime('%Y-%m', o.order_date) AS month,
         ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)), 2) AS revenue
  FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
  WHERE o.status = 'delivered'
  GROUP BY month
)
SELECT month, revenue,
       ROUND(AVG(revenue) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS ma3,
       COUNT(*)           OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)     AS rows_in_frame,
       ROUND(AVG(revenue) OVER (ORDER BY month ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING), 2) AS centered_ma3
FROM monthly
ORDER BY month;
```

`rows_in_frame` shows that the first two rows average fewer than three values — the frame is clipped at the partition edge. If a partial window is unacceptable, null it out: `CASE WHEN COUNT(*) OVER w = 3 THEN AVG(revenue) OVER w END`.

**ROWS frames count rows, not time.** "The last 7 rows" equals "the last 7 days" only if every day has exactly one row. For gappy data, either densify first (scaffold + left join, as in the cross-join lesson) or use a `RANGE` frame over a numeric time value:

```sql-run dataset=mlops
WITH daily AS (
  SELECT date(predicted_at) AS day, COUNT(*) AS preds, AVG(latency_ms) AS avg_latency
  FROM predictions
  WHERE predicted_at >= '2024-03-01' AND predicted_at < '2024-03-20'
  GROUP BY day
)
SELECT day, preds,
       ROUND(AVG(avg_latency) OVER (ORDER BY julianday(day)
                                    RANGE BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS avg_last_3_calendar_days,
       COUNT(*) OVER (ORDER BY julianday(day)
                      RANGE BETWEEN 2 PRECEDING AND CURRENT ROW) AS days_with_data
FROM daily
ORDER BY day;
```

`RANGE BETWEEN 2 PRECEDING AND CURRENT ROW` here means "rows whose Julian day is within 2 of mine" — a true three-calendar-day window regardless of missing days. (PostgreSQL accepts `RANGE BETWEEN INTERVAL '2 days' PRECEDING AND CURRENT ROW` directly on a date column.) `GROUPS` frames, the third mode, count peer groups rather than rows or values.

## FIRST_VALUE, LAST_VALUE and NTH_VALUE

These return the value of an expression from a particular row of the **frame**:

```sql-run dataset=mlops
SELECT run_id, step, value AS val_loss,
       FIRST_VALUE(value) OVER w AS first_loss,
       ROUND(value - FIRST_VALUE(value) OVER w, 4) AS change_from_start,
       MIN(value) OVER w AS best_so_far
FROM metrics
WHERE metric_name = 'val_loss' AND run_id IN (17, 18)
WINDOW w AS (PARTITION BY run_id ORDER BY step ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
ORDER BY run_id, step;
```

`LAST_VALUE` has a famous gotcha: with the default frame, the "last" row of the frame **is the current row**, so `LAST_VALUE(x) OVER (ORDER BY t)` just returns `x`. To get the final value of the partition, extend the frame to the end:

```sql-run dataset=mlops
SELECT run_id, step, value,
       LAST_VALUE(value) OVER (PARTITION BY run_id ORDER BY step) AS last_value_default,
       LAST_VALUE(value) OVER (PARTITION BY run_id ORDER BY step
                               ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS final_loss
FROM metrics
WHERE metric_name = 'val_loss' AND run_id = 17
ORDER BY step;
```

(An easier alternative: `FIRST_VALUE(value) OVER (PARTITION BY run_id ORDER BY step DESC)`.)

## Putting windows together

Ranking, offsets and frames combine freely. A compact training-curve report: per run and step, the loss, the improvement over the previous step, the best loss so far, and whether this step is a new best:

```sql-run dataset=mlops
SELECT run_id, step, value AS val_loss,
       ROUND(value - LAG(value) OVER w, 4) AS delta,
       MIN(value) OVER (w ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS best_so_far,
       CASE WHEN value = MIN(value) OVER (w ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
            THEN 'new best' ELSE '' END AS note
FROM metrics
WHERE metric_name = 'val_loss' AND run_id IN (18, 31)
WINDOW w AS (PARTITION BY run_id ORDER BY step)
ORDER BY run_id, step;
```

A step where `delta` is positive and the note is empty is a sign of overfitting — the basis of early stopping.

Percent-of-total and cumulative share (Pareto analysis) need two windows:

```sql-run dataset=shop
WITH rev AS (
  SELECT p.name, SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS revenue
  FROM order_items oi
  JOIN products p ON p.product_id = oi.product_id
  JOIN orders o ON o.order_id = oi.order_id
  WHERE o.status = 'delivered'
  GROUP BY p.product_id, p.name
)
SELECT name, ROUND(revenue, 2) AS revenue,
       ROUND(100.0 * revenue / SUM(revenue) OVER (), 1) AS pct_of_total,
       ROUND(100.0 * SUM(revenue) OVER (ORDER BY revenue DESC
                                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
             / SUM(revenue) OVER (), 1) AS cumulative_pct
FROM rev
ORDER BY revenue DESC
LIMIT 8;
```

## Pitfalls

- **Default RANGE frame with ties** — running totals jump per peer group. Use `ROWS` and a unique ORDER BY.
- **`LAST_VALUE` with the default frame** returns the current row.
- **ROWS ≠ calendar time** when the data has gaps.
- **Missing PARTITION BY** on LAG/LEAD — values leak across entities.
- **LAG on un-aggregated rows** when you meant "previous period".
- **Partial frames at the edges** of a moving average.
- **Repeating long OVER clauses** — use a named `WINDOW`.

## Summary

- `LAG`/`LEAD` read a previous/next row's value: period-over-period change, gaps, durations.
- An aggregate with `ORDER BY` in its window is cumulative (running total, running max).
- The **frame** selects rows relative to the current row; default with ORDER BY is `RANGE UNBOUNDED PRECEDING … CURRENT ROW` (peers included), without ORDER BY the whole partition.
- Prefer explicit `ROWS BETWEEN …` frames; use `n PRECEDING` for moving windows and `RANGE` over a numeric time value for calendar windows.
- `FIRST_VALUE` / `LAST_VALUE` / `NTH_VALUE` pick values from the frame — extend the frame for `LAST_VALUE`.

```quiz
[
  {"q": "What does LAG(revenue) OVER (ORDER BY month) return for the first month?", "options": ["0", "The same month's revenue", "NULL", "An error"], "answer": 2, "explain": "There is no previous row, so LAG yields NULL unless a default is given as the third argument."},
  {"q": "What is the default frame when a window has ORDER BY but no frame clause?", "options": ["The whole partition", "ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW", "RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW", "The current row only"], "answer": 2, "explain": "RANGE up to the current row, including all peers with the same ORDER BY value."},
  {"q": "Two rows share the same order_date. With SUM(x) OVER (ORDER BY order_date), their running totals are...", "options": ["Different, increasing row by row", "The same - both include both rows", "NULL", "Zero"], "answer": 1, "explain": "The default RANGE frame includes all peers of the current row."},
  {"q": "Which frame gives a 7-row moving average including the current row?", "options": ["ROWS BETWEEN 7 PRECEDING AND CURRENT ROW", "ROWS BETWEEN 6 PRECEDING AND CURRENT ROW", "ROWS BETWEEN 7 PRECEDING AND 7 FOLLOWING", "RANGE UNBOUNDED PRECEDING"], "answer": 1, "explain": "Six preceding rows plus the current row is seven rows."},
  {"q": "Why does LAST_VALUE(x) OVER (ORDER BY t) usually return x itself?", "options": ["It is a bug", "The default frame ends at the current row, which is therefore the last row of the frame", "LAST_VALUE ignores ORDER BY", "It needs PARTITION BY"], "answer": 1, "explain": "Extend the frame to UNBOUNDED FOLLOWING to get the partition's final value."},
  {"q": "What goes wrong if PARTITION BY customer_id is omitted from a LAG over orders?", "options": ["Nothing", "A customer's first order is compared with another customer's order", "LAG returns zero", "The query fails"], "answer": 1, "explain": "Without partitions all customers form one sequence."},
  {"q": "Why might ROWS BETWEEN 6 PRECEDING AND CURRENT ROW not be a 7-day window?", "options": ["ROWS counts rows, and days with no data have no rows", "ROWS frames are approximate", "It includes peers", "It is always a 7-day window"], "answer": 0, "explain": "With gaps, seven rows span more than seven days; densify the data or use a RANGE frame over time."}
]
```

> **Source:** Beaulieu, *Learning SQL*, 3rd ed., ch. 16 "Analytic Functions" (reporting functions, window frames, lag and lead, column value concatenation). SQLite documentation, "Window Functions" (frame specifications).
