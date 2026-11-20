# HAVING, multi-column groups and rollups

The previous lesson grouped by a single column. Real reports group by several columns, by computed expressions, and often need subtotals and grand totals as well. This lesson covers the ways of **generating groups** (single column, multicolumn, expressions), **rollups** and their modern relatives `GROUPING SETS` and `CUBE`, and **group filter conditions** with `HAVING` — including the important question of what belongs in WHERE versus HAVING.

## Generating groups

### Single-column grouping

The simplest case: one group per distinct value of one column.

```sql-run dataset=bank
SELECT product_cd, ROUND(SUM(avail_balance), 2) AS prod_balance
FROM account
GROUP BY product_cd;
```

### Multicolumn grouping

Groups can span more than one column. To see balances not just per product but per product *and* branch, list both columns:

```sql-run dataset=bank
SELECT product_cd, open_branch_id,
       COUNT(*) AS accounts,
       ROUND(SUM(avail_balance), 2) AS tot_balance
FROM account
GROUP BY product_cd, open_branch_id
ORDER BY product_cd, open_branch_id;
```

A group now exists for every distinct **combination** that occurs in the data. Combinations that never occur (a product nobody opened at some branch) simply do not appear — there is no row with a zero. To show those, build the full grid with a cross join and left-join the counts (see *Joins revisited*).

The order of columns in GROUP BY does not change which groups are formed; `GROUP BY open_branch_id, product_cd` gives the same rows. (It does matter for ROLLUP, below.)

### Grouping via expressions

You can group by any expression. The book groups employees by the year they were hired:

```sql-run dataset=bank
SELECT strftime('%Y', start_date) AS year, COUNT(*) AS how_many
FROM employee
GROUP BY strftime('%Y', start_date)
ORDER BY year;
```

SQLite, MySQL and PostgreSQL also let you group by the select-list **alias** (`GROUP BY year`) or by position (`GROUP BY 1`). Standard SQL, Oracle and SQL Server do not — there you must repeat the expression. Repeating it is the portable choice; `GROUP BY 1` is common in analytics code but carries the same fragility as `ORDER BY 1`.

Expression grouping is how you bucket continuous values:

```sql-run dataset=shop
SELECT CASE WHEN price < 25   THEN '1: under 25'
            WHEN price < 100  THEN '2: 25-99'
            WHEN price < 500  THEN '3: 100-499'
            ELSE                   '4: 500+' END AS price_band,
       COUNT(*) AS products,
       ROUND(AVG(price - cost), 2) AS avg_margin
FROM products
GROUP BY price_band
ORDER BY price_band;
```

The numeric prefix in the labels is a small trick to make the bands sort in a sensible order.

## Generating rollups

Suppose that along with the totals per product and branch, the manager also wants **subtotals per product** and a **grand total**. You could run three queries. In MySQL — the book's database — you can append `WITH ROLLUP`:

```sql
-- MySQL
SELECT product_cd, open_branch_id, SUM(avail_balance) AS tot_balance
FROM account
GROUP BY product_cd, open_branch_id WITH ROLLUP;
```

The result contains the normal rows, plus one extra row per `product_cd` with `open_branch_id` shown as NULL (the product subtotal), plus one final row with both columns NULL (the grand total). Rollup works **right to left** through the GROUP BY list, so column order now matters: `GROUP BY open_branch_id, product_cd WITH ROLLUP` would subtotal by branch instead.

The standard syntax (PostgreSQL, Oracle, SQL Server, and MySQL 8) is `GROUP BY ROLLUP (product_cd, open_branch_id)`.

> [!NOTE]
> **SQLite has no ROLLUP, CUBE or GROUPING SETS.** You get the same result by stacking one grouped query per level with `UNION ALL`. It is worth understanding this form anyway — it is exactly what ROLLUP *means*.

```sql-run dataset=bank
SELECT product_cd, open_branch_id, tot_balance
FROM (
  SELECT product_cd, open_branch_id, ROUND(SUM(avail_balance), 2) AS tot_balance
  FROM account
  GROUP BY product_cd, open_branch_id

  UNION ALL
  SELECT product_cd, NULL, ROUND(SUM(avail_balance), 2)      -- subtotal per product
  FROM account
  GROUP BY product_cd

  UNION ALL
  SELECT NULL, NULL, ROUND(SUM(avail_balance), 2)             -- grand total
  FROM account
)
ORDER BY product_cd IS NULL, product_cd, open_branch_id IS NULL, open_branch_id;
```

The `IS NULL` sort keys push each subtotal below its detail rows and the grand total to the bottom. (The compound query is wrapped in a subquery because a compound query's own ORDER BY may only name result columns, not expressions.)

### CUBE and GROUPING SETS

Two relatives generalise the idea:

- `GROUP BY CUBE (a, b)` produces subtotals for **every combination**: (a, b), (a), (b) and (). The book mentions Oracle's and SQL Server's `WITH CUBE`.
- `GROUP BY GROUPING SETS ((a, b), (a), ())` lets you list exactly the grouping levels you want. `ROLLUP (a, b)` is shorthand for those three sets; `CUBE (a, b)` adds `(b)`.

One problem with all of them: a NULL in the output could be a "subtotal marker" or a genuine NULL in the data. The `GROUPING(col)` function returns 1 when the column was rolled up, so you can label rows reliably: `CASE WHEN GROUPING(open_branch_id) = 1 THEN 'All branches' ELSE ... END`. In the UNION ALL form you simply write the label you want:

```sql-run dataset=shop
SELECT c.country, o.status, COUNT(*) AS orders
FROM orders o JOIN customers c ON c.customer_id = o.customer_id
WHERE c.country IN ('Canada', 'Japan')
GROUP BY c.country, o.status
UNION ALL
SELECT c.country, '(all statuses)', COUNT(*)
FROM orders o JOIN customers c ON c.customer_id = o.customer_id
WHERE c.country IN ('Canada', 'Japan')
GROUP BY c.country
ORDER BY 1, 2;
```

## Group filter conditions

When a query groups data you can apply filters at two points:

- **WHERE** acts on rows **before** they are grouped.
- **HAVING** acts on groups **after** they are formed.

```sql-run dataset=bank
SELECT product_cd, ROUND(SUM(avail_balance), 2) AS prod_balance
FROM account
WHERE status = 'ACTIVE'                 -- row filter: only active accounts are grouped
GROUP BY product_cd
HAVING SUM(avail_balance) >= 40000;     -- group filter: only big products are reported
```

The book highlights a common mistake: putting a group-level condition in WHERE.

```sql-run dataset=bank
SELECT product_cd, SUM(avail_balance) AS prod_balance
FROM account
WHERE status = 'ACTIVE' AND SUM(avail_balance) > 40000
GROUP BY product_cd;
```

The error (`misuse of aggregate: SUM()`) follows directly from the logical order of evaluation: when WHERE runs, groups do not yet exist, so there is nothing to sum.

### HAVING may use aggregates that are not selected

A HAVING condition can reference any aggregate, whether or not it appears in the select list:

```sql-run dataset=bank
SELECT product_cd, ROUND(SUM(avail_balance), 2) AS prod_balance
FROM account
WHERE status = 'ACTIVE'
GROUP BY product_cd
HAVING MIN(avail_balance) >= 1000
   AND MAX(avail_balance) <= 30000;
```

Only products whose every active account lies between 1,000 and 30,000 survive.

### WHERE or HAVING? Put row filters in WHERE

A condition on a *grouping column* could legally go in either clause:

```sql
... GROUP BY product_cd HAVING product_cd <> 'CD'    -- works
... WHERE product_cd <> 'CD' GROUP BY product_cd     -- better
```

Prefer WHERE. Filtering early means fewer rows to group, and WHERE conditions can use indexes; a HAVING condition is applied after all the grouping work is done. Good optimizers push such predicates down automatically, but writing it correctly also documents your intent: **WHERE for rows, HAVING for aggregates.**

### HAVING as a set-membership test

HAVING is the natural way to answer "which groups contain *all of* / *at least n of* something":

```sql-run dataset=shop
-- Customers who have had orders both cancelled and returned
SELECT customer_id
FROM orders
WHERE status IN ('cancelled', 'returned')
GROUP BY customer_id
HAVING COUNT(DISTINCT status) = 2;
```

This is the GROUP BY version of the INTERSECT query from the sets module. The pattern generalises: "customers who bought all three of these products" is `WHERE product_id IN (...) GROUP BY customer_id HAVING COUNT(DISTINCT product_id) = 3` — a simple form of *relational division*.

Conditional counts inside HAVING are equally useful:

```sql-run dataset=mlops
-- Experiments with at least 10 runs and a failure rate above 10%
SELECT e.name,
       COUNT(*) AS runs,
       SUM(r.status = 'FAILED') AS failed
FROM experiments e JOIN runs r ON r.experiment_id = e.experiment_id
GROUP BY e.experiment_id, e.name
HAVING COUNT(*) >= 10
   AND 1.0 * SUM(r.status = 'FAILED') / COUNT(*) > 0.10;
```

## Worked example: a monthly report with a total line

Putting it together — orders and revenue per month for delivered orders, only months with at least 15 orders, with a grand-total line:

```sql-run dataset=shop
WITH monthly AS (
  SELECT strftime('%Y-%m', o.order_date) AS month,
         COUNT(DISTINCT o.order_id) AS orders,
         SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS revenue
  FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
  WHERE o.status = 'delivered'
  GROUP BY month
  HAVING COUNT(DISTINCT o.order_id) >= 15
)
SELECT month, orders, ROUND(revenue, 2) AS revenue FROM monthly
UNION ALL
SELECT 'TOTAL', SUM(orders), ROUND(SUM(revenue), 2) FROM monthly
ORDER BY month;
```

(`'TOTAL'` sorts after `'2024-..'` because letters follow digits.) Summing `orders` in the total line is valid here because each order belongs to exactly one month; it would *not* be valid for a distinct count of customers.

## Pitfalls

- **Aggregates in WHERE** — use HAVING.
- **Row filters in HAVING** — legal for grouping columns but wasteful; non-grouped columns there are an error (or arbitrary, in SQLite).
- **Expecting zero-count groups** — GROUP BY only produces groups that have rows.
- **Alias use in HAVING/GROUP BY** — fine in SQLite/MySQL, not portable (PostgreSQL rejects aliases in HAVING).
- **NULL ambiguity in rollups** — use `GROUPING()` or explicit labels.
- **ROLLUP column order** determines which subtotals you get.

## Worked example: a multi-level report, step by step

Reports with several grouping levels are where GROUP BY, HAVING and rollups come together. Build one deliberately: *for the bank's deposit products, show the number of accounts and total balance per branch and product, only for combinations with at least three accounts, with a subtotal per branch and each line's share of its branch.*

**Step 1 — the detail level.** Join for the branch name, filter rows in WHERE, group by both dimensions, and filter groups in HAVING:

```sql-run dataset=bank
SELECT b.name AS branch, a.product_cd,
       COUNT(*) AS accounts,
       ROUND(SUM(a.avail_balance), 2) AS balance
FROM account a
JOIN branch b ON b.branch_id = a.open_branch_id
WHERE a.status = 'ACTIVE' AND a.product_cd IN ('CHK', 'SAV', 'MM', 'CD')
GROUP BY b.branch_id, b.name, a.product_cd
HAVING COUNT(*) >= 3
ORDER BY branch, balance DESC;
```

Check which filter went where. "Active" and "deposit product" are facts about *individual accounts* → WHERE. "At least three accounts" is a fact about *a group* → HAVING.

**Step 2 — add the subtotal level and the share.** Keep the detail in a CTE, then stack a second level grouped by branch only, and divide each line by its branch total:

```sql-run dataset=bank
WITH detail AS (
  SELECT b.name AS branch, a.product_cd,
         COUNT(*) AS accounts,
         SUM(a.avail_balance) AS balance
  FROM account a
  JOIN branch b ON b.branch_id = a.open_branch_id
  WHERE a.status = 'ACTIVE' AND a.product_cd IN ('CHK', 'SAV', 'MM', 'CD')
  GROUP BY b.branch_id, b.name, a.product_cd
  HAVING COUNT(*) >= 3
),
branch_total AS (
  SELECT branch, SUM(accounts) AS accounts, SUM(balance) AS balance
  FROM detail
  GROUP BY branch
)
SELECT branch, product_cd, accounts, balance, pct_of_branch
FROM (
  SELECT d.branch, d.product_cd, d.accounts, ROUND(d.balance, 2) AS balance,
         ROUND(100.0 * d.balance / t.balance, 1) AS pct_of_branch, 0 AS is_total
  FROM detail d JOIN branch_total t ON t.branch = d.branch
  UNION ALL
  SELECT branch, '(all listed)', accounts, ROUND(balance, 2), 100.0, 1
  FROM branch_total
)
ORDER BY branch, is_total, balance DESC;
```

The `is_total` column exists only to sort each subtotal after its detail lines. Note a subtle point about the subtotal: it sums the *listed* combinations (those that passed HAVING), not every account at the branch — which is why it is labelled "(all listed)". Whether a subtotal should include groups that were filtered out is a business decision you must make explicitly; `ROLLUP` in other engines has the same ambiguity (it computes subtotals *before* HAVING is applied, so they include the hidden groups).

For comparison, the PostgreSQL / MySQL 8 version of the two-level grouping is a single clause:

```sql
SELECT b.name AS branch, a.product_cd, COUNT(*) AS accounts, SUM(a.avail_balance) AS balance,
       GROUPING(a.product_cd) AS is_total
FROM account a JOIN branch b ON b.branch_id = a.open_branch_id
WHERE a.status = 'ACTIVE' AND a.product_cd IN ('CHK', 'SAV', 'MM', 'CD')
GROUP BY ROLLUP (b.name, a.product_cd)
ORDER BY b.name, is_total, balance DESC;
```

## HAVING patterns worth memorising

HAVING expresses conditions about a whole group. Five shapes cover most uses.

```sql-run dataset=shop
-- 1. Threshold on a count: customers with 6+ orders
SELECT customer_id, COUNT(*) AS orders
FROM orders GROUP BY customer_id
HAVING COUNT(*) >= 6
ORDER BY orders DESC LIMIT 5;
```

```sql-run dataset=shop
-- 2. "Never": customers with orders but no cancelled or returned ones
SELECT customer_id, COUNT(*) AS orders
FROM orders GROUP BY customer_id
HAVING SUM(status IN ('cancelled', 'returned')) = 0 AND COUNT(*) >= 5;
```

```sql-run dataset=shop
-- 3. "Always": products whose every sale had a discount of at most 10%
SELECT product_id, COUNT(*) AS sales, MAX(discount) AS deepest_discount
FROM order_items GROUP BY product_id
HAVING MAX(discount) <= 0.10;
```

```sql-run dataset=shop
-- 4. Duplicates: emails imported more than once
SELECT lower(trim(email)) AS email, COUNT(*) AS copies
FROM customer_imports GROUP BY 1
HAVING COUNT(*) > 1
ORDER BY copies DESC, email LIMIT 5;
```

```sql-run dataset=shop
-- 5. Comparison with an overall statistic: categories above the average category size
SELECT category_id, COUNT(*) AS products
FROM products GROUP BY category_id
HAVING COUNT(*) > (SELECT AVG(n) FROM (SELECT COUNT(*) AS n FROM products GROUP BY category_id));
```

Patterns 2 and 3 are the grouped way to say "no row in the group has property X" and "every row has property Y": count the violators and require zero, or take a MIN/MAX and test it. They avoid a correlated NOT EXISTS and are a common interview solution.

> [!NOTE]
> **Dialect notes on HAVING.** SQLite and MySQL let you reference a SELECT alias in HAVING (`HAVING orders >= 6`); PostgreSQL, SQL Server and Oracle do not — repeat the aggregate. A HAVING clause without GROUP BY is legal everywhere and treats the whole table as one group: `SELECT COUNT(*) FROM t HAVING COUNT(*) > 100` returns one row or none.

> [!INTERVIEW]
> "Difference between WHERE and HAVING?" — WHERE filters rows before grouping and cannot contain aggregates; HAVING filters groups after aggregation. Add the performance angle: conditions on plain columns belong in WHERE so that fewer rows are grouped and indexes can be used.

## Summary

- Group by one column, several columns (one group per existing combination) or expressions.
- Subtotals: `WITH ROLLUP` (MySQL), `ROLLUP / CUBE / GROUPING SETS` (standard); in SQLite stack grouped queries with `UNION ALL`.
- WHERE filters rows before grouping; HAVING filters groups afterwards and may use any aggregate.
- `HAVING COUNT(DISTINCT x) = n` answers "has all of these" questions.

```quiz
[
  {"q": "GROUP BY product_cd, open_branch_id creates one group for each...", "options": ["product", "branch", "combination of product and branch present in the data", "possible combination, including empty ones"], "answer": 2, "explain": "Only combinations that actually occur produce groups."},
  {"q": "Why is WHERE SUM(avail_balance) > 40000 an error?", "options": ["SUM needs DISTINCT", "WHERE is evaluated before groups exist", "40000 is too large", "SUM is only allowed in ORDER BY"], "answer": 1, "explain": "Aggregates are computed after grouping, which happens after WHERE."},
  {"q": "In ROLLUP (product_cd, open_branch_id), which subtotals are produced?", "options": ["Per branch and grand total", "Per product and grand total", "Per product, per branch and grand total", "Grand total only"], "answer": 1, "explain": "ROLLUP removes columns right to left: (product, branch), (product), ()."},
  {"q": "How do you get rollup-style subtotals in SQLite?", "options": ["WITH ROLLUP", "GROUP BY ROLLUP", "UNION ALL of queries grouped at each level", "It is impossible"], "answer": 2, "explain": "SQLite lacks ROLLUP/CUBE/GROUPING SETS; stack the levels."},
  {"q": "Where should the condition status = 'ACTIVE' go in a grouped query?", "options": ["HAVING", "WHERE", "ORDER BY", "Either, with identical cost"], "answer": 1, "explain": "It is a row filter: applying it before grouping reduces work and can use indexes."},
  {"q": "What does HAVING COUNT(DISTINCT status) = 2 select, after WHERE status IN ('cancelled','returned')?", "options": ["Customers with exactly two orders", "Customers with both a cancelled and a returned order", "Customers with either status", "Orders with two statuses"], "answer": 1, "explain": "Two distinct statuses out of the two allowed means both are present."},
  {"q": "What does GROUPING(col) tell you in a rollup result?", "options": ["The group's size", "Whether col was rolled up (subtotal row) rather than genuinely NULL", "The sort order", "The grouping depth of the table"], "answer": 1, "explain": "It distinguishes subtotal markers from real NULL data."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 8 "Grouping and Aggregates" (generating groups: single-column, multicolumn, via expressions; generating rollups; group filter conditions).
