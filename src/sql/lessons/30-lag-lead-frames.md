# LAG, LEAD, running totals and frames

> **Before this lesson:** you should understand the `OVER` clause, `PARTITION BY`, the `ORDER BY` inside a window, and the fact that window functions keep every row ([Window basics and ranking](#/lesson/sql/ranking)). Date arithmetic with `julianday` and `strftime` comes from [Dates, times and conversion](#/lesson/sql/dates-conversion).

## In plain words

The ranking functions of the last lesson compare a row with its whole group. A second family of window functions looks at a row's **neighbours**: the row before it, the row after it, all the rows up to it, or the last few rows.

An everyday picture: a bank statement. Every line shows one transaction, and beside it the balance *after* that transaction. Nobody stored that balance line by line; it is the sum of everything from the top of the page down to the current line. That is a **running total**. Now imagine sliding a card with a slot cut in it down the page, so that only three lines show at a time, and writing the average of the visible lines next to each one. That is a **moving average**, and the slot is what SQL calls a **frame**.

A simpler neighbour question is "what was the value on the previous line?" With it you can work out the change since last month, or the number of days since a customer's last order. SQL's functions for looking one row back and one row forward are called `LAG` and `LEAD`.

**Why it matters for a job.** Almost every report over time uses these: month-over-month growth, running balances, 7-day averages, time between events. In interviews they are a staple, together with two traps that this lesson explains in detail: what happens to a running total when two rows are tied, and why `LAST_VALUE` seems to return the wrong thing.

## LAG and LEAD

`LAG(expression, n, default)` returns the value of `expression` from the row `n` rows **before** the current one in its partition. `LEAD` looks `n` rows **after**. `n` is 1 if you leave it out. If there is no such row the result is NULL, or the `default` if you supply one.

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

The `WITH` part counts orders per month: one row per month. The main query then adds four columns:

- `LAG(orders) OVER (ORDER BY month)` — with the rows in month order, the order count of the row before.
- `LEAD(orders) OVER (ORDER BY month)` — the order count of the row after.
- `change` — this month minus the previous month.
- `pct_change` — that difference as a percentage of the previous month.

Read the second row: February 2024 had 30 orders, the previous month had 8, the next has 36; the change is 22, which is 275% of 8. The first row, January, has no predecessor, so `prev_month` is NULL, and every calculation that uses it is NULL too.

Comparing one period with the one before is called a **period-over-period** calculation. The recipe never changes: **first reduce the data to one row per period, then apply `LAG`.**

With `PARTITION BY`, each customer, account or device gets its own sequence. Days since each customer's previous order:

```sql-run dataset=shop
SELECT customer_id, order_id, order_date,
       LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS prev_order,
       CAST(julianday(order_date)
            - julianday(LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id)) AS INTEGER) AS days_since_prev
FROM orders
WHERE customer_id IN (5, 8)
ORDER BY customer_id, order_date;
```

Customer 5's first order has no previous one (NULL); the second came 1 day later, the third 3 days after that. Without `PARTITION BY customer_id`, the first order of customer 8 would be compared with the last order of customer 5, a classic mistake.

Typical uses of `LAG` and `LEAD`:

- **detecting change**: did the status, price or version differ from the previous row?
- **gaps**: the time since the previous event;
- **durations**: `LEAD(start_time)` gives the moment the current state ended;
- **removing consecutive repeats**: keep the rows whose value differs from `LAG(value)`.

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

Each version was live until the next one was deployed, so `LEAD(deployed_at)` is its end. Version 1 lasted 2.0 days, version 4 lasted 20.4. The last row has NULL: nothing has replaced it yet.

## Running totals

Give an aggregate function a window that has an `ORDER BY`, and it becomes **cumulative**: for each row, it aggregates from the start of the partition up to that row.

```sql-run dataset=bank
SELECT txn_id, txn_date, txn_type_cd, amount,
       CASE txn_type_cd WHEN 'CDT' THEN amount ELSE -amount END AS signed,
       ROUND(SUM(CASE txn_type_cd WHEN 'CDT' THEN amount ELSE -amount END)
             OVER (ORDER BY txn_date, txn_id), 2) AS running_net
FROM txn
WHERE account_id = 142
ORDER BY txn_date, txn_id;
```

The `signed` column makes a credit (`CDT`) positive and a debit negative. `SUM(...) OVER (ORDER BY txn_date, txn_id)` adds up `signed` from the first transaction to the current one. Follow it down: 3590.16, then 3590.16 + 48.66 = 3638.82, then + 176.49 = 3815.31, then a debit of 1323.16 brings it to 2492.15. This is the bank-statement column.

With a partition there is one running total per account, month or user:

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

`month_to_date` starts again from zero when a new month begins, because the month is the partition; `since_november` keeps climbing.

Other aggregates follow the same pattern. `MAX(x) OVER (ORDER BY t)` is the highest value so far, `COUNT(*) OVER (ORDER BY t)` a running count, `AVG` a cumulative average.

## The frame clause

How does the database know that `SUM(...) OVER (ORDER BY t)` means "from the start up to here"? Every aggregate used as a window function has a **frame**: the part of the partition, described relative to the current row, that the function is applied to. Written in full:

```
{ROWS | RANGE | GROUPS} BETWEEN frame_start AND frame_end
```

where each end is one of:

| Boundary | Meaning |
|---|---|
| `UNBOUNDED PRECEDING` | the first row of the partition |
| `n PRECEDING` | n rows (or units) before the current row |
| `CURRENT ROW` | the current row |
| `n FOLLOWING` | n rows after the current row |
| `UNBOUNDED FOLLOWING` | the last row of the partition |

The **defaults** are the part to memorise:

- A window with **no `ORDER BY`**: the frame is the **whole partition**.
- A window **with `ORDER BY`**: the frame is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`. That is the start of the partition up to the current row *and every row tied with it*.

That default explains running totals. It also hides a trap.

### ROWS versus RANGE: the tie trap

`ROWS` counts actual rows. `RANGE` works on the *values* of the `ORDER BY` expression and treats rows with equal values as one unit. Rows that are equal in the window's ordering are called **peers**. Under the default `RANGE` frame, all peers get the same cumulative value: the total *including all of them*.

```sql-run dataset=shop
SELECT order_id, order_date, shipping_fee,
       SUM(shipping_fee) OVER (ORDER BY order_date)                                AS range_default,
       SUM(shipping_fee) OVER (ORDER BY order_date
                               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS rows_frame
FROM orders
WHERE order_date BETWEEN '2024-02-05' AND '2024-02-12'
ORDER BY order_date, order_id;
```

Orders 13 and 14 share the date 6 February, with fees of 7.50 and 0. Both columns show 7.50 for both rows, which looks harmless. Now look at 8 February, where several orders share the date. `range_default` shows 30.00 on *every* one of them: the total after the whole day. `rows_frame` climbs one order at a time: 15.00, then 22.50, and so on. Neither is wrong. They answer different questions: "total up to and including this day" versus "total up to and including this row".

For a true row-by-row running total, write `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`, or make the ordering unique (`ORDER BY order_date, order_id`), or better, do both.

> [!TIP]
> Make it a habit: whenever you write a running or moving aggregate, **state the frame** with `ROWS`. You never have to recall the default, and `ROWS` frames are also faster to compute.

### Moving averages

A frame that slides along with the current row gives moving (also called rolling) calculations. A three-row moving average is the current row and the two before it:

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

For March, the frame of `ma3` holds January, February and March: (5303.21 + 20994.09 + 18801.77) ÷ 3 = 15033.02. The `rows_in_frame` column shows how many rows each frame really contained. January has 1 and February 2: at the edge of the partition there are no earlier rows, so the frame is cut short and the "three-month average" is an average of fewer months. If that is unacceptable, blank it out: `CASE WHEN COUNT(*) OVER w = 3 THEN AVG(revenue) OVER w END`. The last column uses a frame centred on the current row: one before, the row itself, one after.

**A `ROWS` frame counts rows, not time.** "The last 7 rows" equals "the last 7 days" only if every day has exactly one row. For data with gaps, either fill in the missing days first ([Cross joins, natural joins and densifying data](#/lesson/sql/cross-natural)) or use a `RANGE` frame over a numeric time value:

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

The window is ordered by `julianday(day)`, a plain day number. `RANGE BETWEEN 2 PRECEDING AND CURRENT ROW` then means "rows whose day number is within 2 of mine": a true window of three calendar days, however many of those days have data. The `days_with_data` column shows how many did. (PostgreSQL accepts `RANGE BETWEEN INTERVAL '2 days' PRECEDING AND CURRENT ROW` directly on a date column. The third mode, `GROUPS`, counts groups of peers.)

## FIRST_VALUE, LAST_VALUE and NTH_VALUE

These return the value of an expression from a particular row of the **frame**. The example follows a model being trained: `val_loss` is an error measure recorded at each step, where lower is better.

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

The window `w` is defined once at the bottom and used three times. For run 17, `first_loss` is 0.8057 on every row; by step 4 the loss is 0.4577, a change of −0.348 from the start, and `best_so_far` (the minimum up to this step) follows it down.

`LAST_VALUE` has a well-known trap. Under the default frame, which ends at the current row, the "last" row of the frame **is the current row**. So `LAST_VALUE(x) OVER (ORDER BY t)` returns `x` itself. To get the final value of the partition, extend the frame to the end:

```sql-run dataset=mlops
SELECT run_id, step, value,
       LAST_VALUE(value) OVER (PARTITION BY run_id ORDER BY step) AS last_value_default,
       LAST_VALUE(value) OVER (PARTITION BY run_id ORDER BY step
                               ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS final_loss
FROM metrics
WHERE metric_name = 'val_loss' AND run_id = 17
ORDER BY step;
```

`last_value_default` repeats the `value` column exactly, which is useless. `final_loss` shows 0.3435, the loss at the last step, on every row. (An easier way to the same result: `FIRST_VALUE(value) OVER (PARTITION BY run_id ORDER BY step DESC)`.)

## Putting windows together

Ranking, neighbours and frames combine freely. A compact report on training: for each step, the loss, the change from the previous step, the best loss so far, and a note when this step sets a new best.

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

Here the named window `w` supplies the partition and order, and a frame is added to it where one is needed. For run 18, step 2 improved by 0.1584 and is a new best; step 3 got *worse* by 0.0076, so its note is empty. A step where the loss rises is a sign that further training has stopped helping.

Share of a total and cumulative share need two windows. This is the "which few products bring in most of the revenue?" analysis, often called a Pareto analysis:

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

`SUM(revenue) OVER ()` is the grand total, repeated on every row. Dividing a product's revenue by it gives the share; dividing the running total by it gives the cumulative share. The top two products alone, at 30.0% and 20.5%, account for 50.5% of delivered revenue.

## The same functions on other databases

`LAG`, `LEAD`, `FIRST_VALUE`, `LAST_VALUE` and frames are written the same way in SQLite, PostgreSQL, MySQL 8, SQL Server and Oracle. A few differences:

| Feature | SQLite | PostgreSQL | MySQL 8 |
|---|---|---|---|
| `RANGE` with a number of units | yes, over a numeric expression | yes; also with `INTERVAL` over dates | yes; also with `INTERVAL` over dates |
| `GROUPS` frames | yes | yes | no |
| Named `WINDOW` clause | yes | yes | yes |
| Skipping NULLs in `LAG` (`IGNORE NULLS`) | no | no | no (Oracle, SQL Server 2022 and Snowflake have it) |

```sql
-- PostgreSQL and MySQL 8: a true 7-day window directly on a date column
SELECT day, AVG(revenue) OVER (ORDER BY day
                               RANGE BETWEEN INTERVAL '6' DAY PRECEDING AND CURRENT ROW) AS avg_7_days
FROM daily_revenue;
```

> [!INTERVIEW]
> "Compute month-over-month revenue growth" is the standard `LAG` question: reduce to one row per month, then `(revenue - LAG(revenue)) / LAG(revenue)`, and say what the first month shows (NULL). For "running total" or "7-day moving average", state the frame aloud: "`ROWS BETWEEN 6 PRECEDING AND CURRENT ROW`, which is seven rows, and it equals seven days only if there are no missing days." Naming the tie behaviour of the default frame is what distinguishes a strong answer.

## Pitfalls

- **The default `RANGE` frame with ties**: a running total jumps once per group of peers. Use `ROWS` and a unique `ORDER BY`.
- **`LAST_VALUE` with the default frame** returns the current row's own value.
- **`ROWS` is not calendar time** when the data has gaps.
- **A missing `PARTITION BY`** on `LAG` or `LEAD`: values leak from one customer to the next.
- **`LAG` on rows that are not yet one per period** when "the previous period" was meant.
- **Short frames at the edges** of a moving average.
- **Long `OVER` clauses repeated many times**: use a named `WINDOW`.

## Summary

- `LAG` and `LEAD` read the value of an earlier or later row: period-over-period change, gaps, durations.
- An aggregate whose window has an `ORDER BY` is cumulative: running total, highest so far.
- The **frame** selects rows relative to the current one. With `ORDER BY` the default is `RANGE` from the start to the current row, peers included; without `ORDER BY` it is the whole partition.
- Prefer explicit `ROWS BETWEEN ...` frames; use `n PRECEDING` for moving windows, and `RANGE` over a numeric time value for calendar windows.
- `FIRST_VALUE`, `LAST_VALUE` and `NTH_VALUE` pick values from the frame; extend the frame for `LAST_VALUE`.

## Glossary

- **`LAG` / `LEAD`** — window functions returning a value from an earlier / later row of the partition.
- **Offset** — how many rows back or forward `LAG` or `LEAD` looks; 1 unless stated.
- **Period-over-period** — comparing each period (day, month) with the one before.
- **Running total (cumulative sum)** — the sum of all rows from the start of the partition to the current row.
- **Frame** — the part of a partition, described relative to the current row, that an aggregate window function uses.
- **`ROWS` frame** — a frame measured in actual rows.
- **`RANGE` frame** — a frame measured in values of the ordering expression; tied rows are treated together.
- **Peers** — rows with equal values in the window's `ORDER BY`.
- **`UNBOUNDED PRECEDING` / `UNBOUNDED FOLLOWING`** — the first / last row of the partition.
- **Moving (rolling) average** — the average over a frame that slides along with the current row.
- **`FIRST_VALUE` / `LAST_VALUE` / `NTH_VALUE`** — the value from the first, last or nth row of the frame.
- **Pareto analysis** — ranking items by size and looking at their cumulative share of the total.

```quiz
[
  {"q": "What does LAG(revenue) OVER (ORDER BY month) return for the first month?", "options": ["0", "The same month's revenue", "NULL", "An error"], "answer": 2, "explain": "There is no previous row, so LAG gives NULL unless a default is supplied as the third argument."},
  {"q": "What is the default frame when a window has ORDER BY but no frame clause?", "options": ["The whole partition", "ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW", "RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW", "The current row only"], "answer": 2, "explain": "RANGE up to the current row, including all peers that share its ORDER BY value."},
  {"q": "Two rows share the same order_date. With SUM(x) OVER (ORDER BY order_date), their running totals are...", "options": ["Different, increasing row by row", "The same: both include both rows", "NULL", "Zero"], "answer": 1, "explain": "The default RANGE frame includes all peers of the current row."},
  {"q": "Which frame gives a 7-row moving average that includes the current row?", "options": ["ROWS BETWEEN 7 PRECEDING AND CURRENT ROW", "ROWS BETWEEN 6 PRECEDING AND CURRENT ROW", "ROWS BETWEEN 7 PRECEDING AND 7 FOLLOWING", "RANGE UNBOUNDED PRECEDING"], "answer": 1, "explain": "Six preceding rows plus the current row make seven rows."},
  {"q": "Why does LAST_VALUE(x) OVER (ORDER BY t) usually return x itself?", "options": ["It is a bug", "The default frame ends at the current row, which is therefore the last row of the frame", "LAST_VALUE ignores ORDER BY", "It needs PARTITION BY"], "answer": 1, "explain": "Extend the frame to UNBOUNDED FOLLOWING to get the final value of the partition."},
  {"q": "What goes wrong if PARTITION BY customer_id is omitted from a LAG over orders?", "options": ["Nothing", "A customer's first order is compared with another customer's order", "LAG returns zero", "The query fails"], "answer": 1, "explain": "Without partitions, all customers form one long sequence."},
  {"q": "Why might ROWS BETWEEN 6 PRECEDING AND CURRENT ROW not be a 7-day window?", "options": ["ROWS counts rows, and days with no data have no rows", "ROWS frames are approximate", "It includes peers", "It is always a 7-day window"], "answer": 0, "explain": "With gaps, seven rows span more than seven days; fill in the missing days or use a RANGE frame over time."},
  {"q": "In a 3-row moving average (ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), what does the first row of a partition show?", "options": ["NULL", "The average of that one row", "The average of three rows", "An error"], "answer": 1, "explain": "The frame is cut short at the edge of the partition, so it contains only the first row."}
]
```

> **Source:** Beaulieu, *Learning SQL*, 3rd ed., ch. 16 "Analytic Functions" (reporting functions, window frames, lag and lead), restated in original wording with this guide's own datasets. SQLite documentation, "Window Functions" (frame specifications).
