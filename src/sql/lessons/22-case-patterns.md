# CASE patterns

Knowing the syntax of CASE is the easy part. Its real value shows in a handful of recurring patterns that the book walks through and that appear in nearly every analytics query and interview: **result set transformations** (pivoting rows into columns), **selective aggregation**, **checking for existence**, **avoiding division-by-zero errors**, **conditional updates**, and **handling NULL values**.

## Result set transformations (pivoting)

A grouped query returns one **row** per group. Suppose you count accounts opened per year:

```sql-run dataset=bank
SELECT strftime('%Y', open_date) AS year, COUNT(*) AS how_many
FROM account
WHERE open_date >= '2020-01-01' AND open_date < '2024-01-01'
GROUP BY year;
```

Four rows. But the report wants **one row with four columns** — a year per column. The transformation: for each desired column, write an aggregate around a CASE that picks out only the rows belonging to that column.

```sql-run dataset=bank
SELECT SUM(CASE WHEN strftime('%Y', open_date) = '2020' THEN 1 ELSE 0 END) AS year_2020,
       SUM(CASE WHEN strftime('%Y', open_date) = '2021' THEN 1 ELSE 0 END) AS year_2021,
       SUM(CASE WHEN strftime('%Y', open_date) = '2022' THEN 1 ELSE 0 END) AS year_2022,
       SUM(CASE WHEN strftime('%Y', open_date) = '2023' THEN 1 ELSE 0 END) AS year_2023
FROM account
WHERE open_date >= '2020-01-01' AND open_date < '2024-01-01';
```

Each CASE returns 1 for rows of "its" year and 0 otherwise; summing counts them. Every row passes through all four columns but contributes to exactly one.

Add a GROUP BY and you get a cross-tab: rows for one dimension, columns for another.

```sql-run dataset=shop
SELECT c.country,
       SUM(CASE WHEN o.status = 'delivered' THEN 1 ELSE 0 END) AS delivered,
       SUM(CASE WHEN o.status = 'shipped'   THEN 1 ELSE 0 END) AS shipped,
       SUM(CASE WHEN o.status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled,
       SUM(CASE WHEN o.status = 'returned'  THEN 1 ELSE 0 END) AS returned,
       COUNT(*) AS total
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
GROUP BY c.country
ORDER BY total DESC;
```

The limitation: SQL needs to know the output **columns** when the query is written, so the pivoted values must be listed by hand. Truly dynamic pivots require generating the SQL in application code (or a tool like dbt/pandas `pivot_table`).

> [!NOTE]
> SQL Server and Oracle have a dedicated `PIVOT` clause, and PostgreSQL offers `crosstab()` (tablefunc extension) and the `FILTER` clause: `COUNT(*) FILTER (WHERE status = 'delivered')`. SQLite also supports `FILTER` (3.30+). CASE-in-aggregate works in **all** of them.

### Pivoting values, not counts: MAX(CASE …)

When each cell should hold a *value* from the single matching row rather than a count, wrap the CASE in `MAX` (or `MIN`) and drop the ELSE. This is how you turn *long* (entity–attribute–value) data into *wide* data — a daily task with ML metric tables:

```sql-run dataset=mlops
SELECT run_id,
       MAX(CASE WHEN metric_name = 'accuracy' THEN value END) AS accuracy,
       MAX(CASE WHEN metric_name = 'f1'       THEN value END) AS f1,
       MAX(CASE WHEN metric_name = 'auc'      THEN value END) AS auc
FROM metrics
WHERE run_id BETWEEN 23 AND 30
GROUP BY run_id
HAVING accuracy IS NOT NULL;
```

Inside each group, the CASE yields the metric's value on one row and NULL on all the others; MAX ignores the NULLs and returns the one value.

The reverse (**unpivot**, wide → long) is done with `UNION ALL`, one SELECT per column (see the sets module).

## Selective aggregation

The pivot is one use of a more general idea: **an aggregate that only considers some of the rows**. The book's example deals with a real data-modelling wrinkle. In `txn`, the `amount` column is always positive; whether it adds to or subtracts from the balance depends on `txn_type_cd`. To check that each account's stored balance agrees with its transaction history you need a *signed* sum:

```sql-run dataset=bank
SELECT t.account_id,
       ROUND(SUM(CASE WHEN t.txn_type_cd = 'DBT' THEN -t.amount ELSE t.amount END), 2) AS net_2024,
       ROUND(SUM(CASE WHEN t.txn_type_cd = 'CDT' THEN t.amount ELSE 0 END), 2) AS credits,
       ROUND(SUM(CASE WHEN t.txn_type_cd = 'DBT' THEN t.amount ELSE 0 END), 2) AS debits,
       COUNT(*) AS txns
FROM txn t
GROUP BY t.account_id
ORDER BY net_2024
LIMIT 8;
```

The first aggregate flips the sign of debits *inside* the SUM. One pass over the table produces all the conditional totals — far cheaper than running a separate filtered query for each and joining the results.

The book goes one step further with funds that are not yet available: a transaction counts toward the *available* balance only if its `funds_avail_date` has passed. That is just one more condition in the CASE:

```sql-run dataset=bank
SELECT account_id,
       ROUND(SUM(CASE WHEN txn_type_cd = 'DBT' THEN -amount ELSE amount END), 2) AS pending_net,
       ROUND(SUM(CASE
                   WHEN funds_avail_date > '2024-12-30 12:00:00' THEN 0
                   WHEN txn_type_cd = 'DBT' THEN -amount
                   ELSE amount
                 END), 2) AS available_net
FROM txn
WHERE txn_date >= '2024-12-20'
GROUP BY account_id
HAVING pending_net <> available_net;
```

Selective aggregation is also how ratios and rates are computed in one query:

```sql-run dataset=mlops
SELECT d.deployment_id,
       COUNT(*) AS predictions,
       SUM(CASE WHEN p.latency_ms > 100 THEN 1 ELSE 0 END) AS slow,
       ROUND(100.0 * SUM(CASE WHEN p.latency_ms > 100 THEN 1 ELSE 0 END) / COUNT(*), 1) AS slow_pct,
       ROUND(100.0 * SUM(CASE WHEN p.predicted_label = p.actual_label THEN 1 ELSE 0 END)
             / COUNT(p.actual_label), 1) AS accuracy_pct
FROM predictions p
JOIN deployments d ON d.deployment_id = p.deployment_id
GROUP BY d.deployment_id
HAVING COUNT(*) >= 15
ORDER BY slow_pct DESC;
```

> [!TIP]
> A neat equivalent for rates: `AVG(CASE WHEN cond THEN 1.0 ELSE 0 END)` is the fraction of rows meeting `cond`. Multiply by 100 for a percentage.

## Checking for existence

Sometimes you only need to know **whether** a relationship exists, not how many times. The book flags, for each customer, whether they have any checking account and any savings account — using CASE around correlated EXISTS subqueries:

```sql-run dataset=bank
SELECT c.cust_id, c.cust_type_cd,
       CASE WHEN EXISTS (SELECT 1 FROM account a
                         WHERE a.cust_id = c.cust_id AND a.product_cd = 'CHK')
            THEN 'Y' ELSE 'N' END AS has_checking,
       CASE WHEN EXISTS (SELECT 1 FROM account a
                         WHERE a.cust_id = c.cust_id AND a.product_cd = 'SAV')
            THEN 'Y' ELSE 'N' END AS has_savings
FROM customer c
ORDER BY c.cust_id
LIMIT 10;
```

No join, so no row multiplication; each flag is evaluated independently and can stop at the first match.

When a rough size matters — none, one, a couple, many — use a scalar count subquery inside a simple CASE, as the book does:

```sql-run dataset=bank
SELECT c.cust_id,
       CASE (SELECT COUNT(*) FROM account a WHERE a.cust_id = c.cust_id)
         WHEN 0 THEN 'None'
         WHEN 1 THEN '1'
         WHEN 2 THEN '2'
         ELSE '3+'
       END AS num_accounts
FROM customer c
ORDER BY c.cust_id
LIMIT 10;
```

## Division-by-zero errors

Calculations with division must consider a zero denominator. Engines disagree on what happens: PostgreSQL, SQL Server and Oracle raise an error and abort the query; MySQL and SQLite return NULL. Either way, the book's advice is to guard the denominator explicitly, so your query has the same, intended behaviour everywhere:

```sql-run dataset=bank
SELECT 100 / 0 AS sqlite_gives_null,
       100 / NULLIF(0, 0) AS guarded,
       COALESCE(100 / NULLIF(0, 0), 0) AS guarded_with_default;
```

A realistic case: each account's share of its product's total balance. Loan products have a total of zero.

```sql-run dataset=bank
SELECT a.account_id, a.product_cd, a.avail_balance,
       ROUND(a.avail_balance /
             CASE WHEN p.tot = 0 THEN 1 ELSE p.tot END, 4) AS share_book_style,
       ROUND(a.avail_balance / NULLIF(p.tot, 0), 4)        AS share_nullif
FROM account a
JOIN (SELECT product_cd, SUM(avail_balance) AS tot
      FROM account GROUP BY product_cd) p ON p.product_cd = a.product_cd
WHERE a.product_cd IN ('MRT', 'SAV')
ORDER BY a.product_cd, a.account_id
LIMIT 8;
```

The book replaces a zero denominator with 1 (so the result is 0 because the numerator is also 0). `NULLIF(tot, 0)` returns NULL instead — usually the more honest answer: "undefined", not "zero percent". Choose deliberately; do not let the engine choose for you.

## Conditional updates

When the new value depends on the row, CASE lets a single UPDATE apply different rules to different rows. The book updates `last_activity_date` after a transaction posts: use the current time, except where the transaction's funds become available in the future. A similar business rule here — apply monthly fees or interest by tier:

```sql-run dataset=bank
UPDATE account
SET avail_balance = ROUND(
      CASE
        WHEN status <> 'ACTIVE'      THEN avail_balance              -- untouched
        WHEN product_cd = 'SAV'      THEN avail_balance * 1.002      -- interest
        WHEN product_cd = 'CHK' AND avail_balance < 500
                                     THEN avail_balance - 5          -- low-balance fee
        ELSE avail_balance
      END, 2)
WHERE product_cd IN ('CHK', 'SAV');

SELECT account_id, product_cd, status, avail_balance
FROM account WHERE product_cd IN ('CHK','SAV') ORDER BY avail_balance LIMIT 6;
```

Doing this as three separate UPDATE statements risks a row being changed twice (a savings account that crosses a threshold after the first statement) and scans the table three times. One statement, one pass, each row evaluated once against its *original* values.

## Handling NULL values

NULL is the right way to store "unknown", but it is rarely the right thing to *display*, and it propagates through arithmetic. CASE (or its shorthand COALESCE) substitutes something meaningful at query time:

```sql-run dataset=mlops
SELECT run_id, status,
       CASE WHEN ended_at IS NULL THEN '(still running)' ELSE ended_at END AS ended,
       COALESCE(gpu_hours, 0) AS gpu_hours,
       CASE
         WHEN learning_rate IS NULL THEN 'n/a'
         WHEN learning_rate < 0.001 THEN 'tiny'
         WHEN learning_rate < 0.05  THEN 'small'
         ELSE 'large'
       END AS lr_band
FROM runs
WHERE status IN ('RUNNING', 'KILLED')
LIMIT 8;
```

In calculations, one NULL operand makes the whole result NULL. The book's example multiplies three numbers, any of which may be missing; wrapping each in a CASE (or `COALESCE(x, 0)` / `COALESCE(x, 1)`) keeps the arithmetic alive:

```sql-run dataset=shop
SELECT order_id,
       shipping_fee,
       (SELECT SUM(quantity * unit_price) FROM order_items oi WHERE oi.order_id = o.order_id) AS items_total,
       COALESCE((SELECT SUM(quantity * unit_price) FROM order_items oi WHERE oi.order_id = o.order_id), 0)
         + shipping_fee AS order_total
FROM orders o
ORDER BY order_id
LIMIT 5;
```

Be thoughtful about the substitute: 0 is the identity for addition, 1 for multiplication, and neither is right for an average.

## Putting it together: a one-query health report

```sql-run dataset=shop
SELECT strftime('%Y-%m', o.order_date) AS month,
       COUNT(*) AS orders,
       SUM(CASE WHEN o.status = 'delivered' THEN 1 ELSE 0 END) AS delivered,
       ROUND(100.0 * SUM(CASE WHEN o.status IN ('cancelled','returned') THEN 1 ELSE 0 END)
             / NULLIF(COUNT(*), 0), 1) AS problem_pct,
       CASE
         WHEN 1.0 * SUM(CASE WHEN o.status IN ('cancelled','returned') THEN 1 ELSE 0 END) / COUNT(*) > 0.2 THEN 'investigate'
         WHEN 1.0 * SUM(CASE WHEN o.status IN ('cancelled','returned') THEN 1 ELSE 0 END) / COUNT(*) > 0.1 THEN 'watch'
         ELSE 'ok'
       END AS flag
FROM orders o
GROUP BY month
ORDER BY month;
```

Selective aggregation, a guarded division, and a CASE *over* aggregates for the final label — all in one pass.

## Pitfalls

- **`ELSE 0` with COUNT** — `COUNT(CASE WHEN c THEN 1 ELSE 0 END)` counts every row, because 0 is not NULL. Use SUM with `ELSE 0`, or COUNT with no ELSE.
- **`ELSE 0` with AVG/MIN/MAX** — zeros enter the statistic.
- **Integer division in rates** — multiply by `100.0`.
- **Hand-listed pivot columns** go stale when new categories appear; add an "other" column or generate the SQL.
- **Unqualified division** — decide what a zero denominator should mean.

## Summary

- **Pivot**: one aggregate-around-CASE per output column; `SUM(CASE … THEN 1 ELSE 0 END)` for counts, `MAX(CASE … THEN value END)` for values.
- **Selective aggregation** computes several conditional totals and rates in one scan.
- **Existence flags**: `CASE WHEN EXISTS (…) THEN 'Y' ELSE 'N' END`.
- **Safe division**: `NULLIF(denominator, 0)` (or CASE), plus COALESCE if a default is wanted.
- **Conditional updates** apply per-row rules atomically in one statement.
- **NULL handling**: translate missing values at query time with CASE / COALESCE.

```quiz
[
  {"q": "Which expression counts delivered orders within each group?", "options": ["COUNT(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END)", "SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END)", "COUNT(status = 'delivered')", "MAX(CASE WHEN status = 'delivered' THEN 1 END)"], "answer": 1, "explain": "SUM of 1/0 counts matches. COUNT with ELSE 0 counts every row because 0 is not NULL."},
  {"q": "To pivot a long metrics table into one column per metric value, wrap the CASE in...", "options": ["SUM with ELSE 0", "MAX (or MIN) with no ELSE", "COUNT", "DISTINCT"], "answer": 1, "explain": "MAX ignores the NULLs from non-matching rows and returns the single value."},
  {"q": "What does 100 / 0 do in PostgreSQL versus SQLite?", "options": ["NULL in both", "Error in PostgreSQL, NULL in SQLite", "Error in both", "0 in both"], "answer": 1, "explain": "Engines differ, which is why you should guard the denominator explicitly."},
  {"q": "x / NULLIF(y, 0) returns what when y = 0?", "options": ["0", "x", "NULL", "An error"], "answer": 2, "explain": "NULLIF turns the zero into NULL and division by NULL is NULL."},
  {"q": "Why use one UPDATE with CASE instead of several UPDATE statements?", "options": ["CASE is required in UPDATE", "Each row is evaluated once against its original values, in a single scan", "Multiple UPDATEs are not allowed in a transaction", "It avoids locks entirely"], "answer": 1, "explain": "Sequential updates can change the same row twice as it crosses thresholds."},
  {"q": "AVG(CASE WHEN latency_ms > 100 THEN 1.0 ELSE 0 END) gives...", "options": ["The average latency", "The fraction of rows with latency above 100", "The count of slow rows", "NULL"], "answer": 1, "explain": "The mean of a 0/1 indicator is the proportion of ones."},
  {"q": "What is the main limitation of pivoting with CASE?", "options": ["It is slow", "The output columns must be listed when the query is written", "It only works for counts", "It needs a self join"], "answer": 1, "explain": "SQL result shapes are fixed at parse time; dynamic pivots need generated SQL."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 11 "Conditional Logic" — case expression examples: result set transformations, selective aggregation, checking for existence, division-by-zero errors, conditional updates, handling null values.
