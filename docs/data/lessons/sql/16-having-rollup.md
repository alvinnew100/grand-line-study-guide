# HAVING, multi-column groups and rollups

> **Before this lesson:** you should be able to write a grouped query with `GROUP BY` and the aggregate functions `COUNT`, `SUM`, `AVG`, `MIN` and `MAX`, and state the golden rule that every selected item must be grouped or aggregated ([Aggregate functions and GROUP BY](#/lesson/sql/group-by)). `UNION ALL` is used to stack results ([Set theory and UNION](#/lesson/sql/union)).

## In plain words

The last lesson sorted rows into piles by one column and summarised each pile. Real reports ask for a little more, in three directions:

- **Finer piles.** Not "balance per product" but "balance per product *and* branch". That is grouping by several columns.
- **Totals on top of the piles.** A subtotal for each product and a grand total at the bottom, as on a printed report. That is a **rollup**.
- **Throwing piles away.** "Show only the products whose total is above 40,000." That is filtering groups, and it has its own keyword, `HAVING`.

An everyday picture: a teacher sorts exam papers into piles by class, then within each class by subject. She writes the average on each pile, adds a slip with the class average on top of each class, and a final slip with the school average. Then the head asks, "Show me only the piles with an average below 50." Sorting into piles is `GROUP BY`; the slips are the rollup; the head's request is `HAVING`.

**Why it matters for a job.** "What is the difference between `WHERE` and `HAVING`?" may be the single most common SQL interview question. Beyond the interview, `HAVING` is the tool for a family of questions that are hard to answer any other way: customers who have *never* returned an order, products that were *always* sold at full price, emails that appear *more than once*.

## Making groups

### One column

The form from the previous lesson: one group for each different value.

```sql-run dataset=bank
SELECT product_cd, ROUND(SUM(avail_balance), 2) AS prod_balance
FROM account
GROUP BY product_cd;
```

Seven rows, one per product, each with the total available balance of its accounts.

### Several columns

List two columns after `GROUP BY` and a group is formed for every different **pair** of values:

```sql-run dataset=bank
SELECT product_cd, open_branch_id,
       COUNT(*) AS accounts,
       ROUND(SUM(avail_balance), 2) AS tot_balance
FROM account
GROUP BY product_cd, open_branch_id
ORDER BY product_cd, open_branch_id;
```

25 rows. The first two say that one `BUS` account was opened at branch 3 and one at branch 4. Each row is a product-and-branch combination that occurs in the data.

Two things to notice. First, a combination that never occurs produces **no row at all**, not a row with zero: no `BUS` account was opened at branch 1, so there is no `BUS, 1` line. Showing the zeros takes an extra technique ([Cross joins, natural joins and densifying data](#/lesson/sql/cross-natural)). Second, the order in which you list the grouping columns does not change which groups are made; `GROUP BY open_branch_id, product_cd` gives the same 25 rows.

### A calculation

You can group by the result of a calculation. Here employees are grouped by the year they started, cut out of the date with `strftime`:

```sql-run dataset=bank
SELECT strftime('%Y', start_date) AS year, COUNT(*) AS how_many
FROM employee
GROUP BY strftime('%Y', start_date)
ORDER BY year;
```

Two employees started in 2018, four in 2019, and so on.

SQLite, MySQL and PostgreSQL also let you write the alias (`GROUP BY year`) or the column's position (`GROUP BY 1`). Oracle and SQL Server do not, so repeating the calculation is the form that works everywhere.

Grouping by a calculation is how continuous values are put into bands:

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

`CASE` gives each product a label according to its price; the query then groups by that label. Twelve products cost under 25 and have an average margin (price minus cost) of 5.95. The digits at the front of the labels are a small trick: they make the bands sort in a sensible order.

## Rollups: subtotals and grand totals

Suppose the manager wants, in addition to the product-and-branch figures, a **subtotal for each product** and a **grand total**. That is three levels of grouping in one result. MySQL can add them with two words:

```sql
-- MySQL
SELECT product_cd, open_branch_id, SUM(avail_balance) AS tot_balance
FROM account
GROUP BY product_cd, open_branch_id WITH ROLLUP;
```

The result has the normal rows, plus one extra row per product in which the branch column is NULL (the product subtotal), plus a last row with both columns NULL (the grand total). A rollup removes grouping columns from **right to left**, so here the column order does matter: listing the branch first would give subtotals per branch instead.

The standard spelling, used by PostgreSQL, Oracle, SQL Server and MySQL 8, is `GROUP BY ROLLUP (product_cd, open_branch_id)`.

> [!NOTE]
> **SQLite has no `ROLLUP`.** You get the same result by writing one grouped query per level and stacking them with `UNION ALL`. This form is worth understanding in any case, because it is exactly what a rollup *means*.

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

Three queries, three levels: 25 detail rows, 7 product subtotals, 1 grand total, 33 rows in all. NULL stands in for "all branches" or "all products". The `ORDER BY` uses `IS NULL` tests (0 for false, 1 for true) to push each subtotal below its detail rows and the grand total to the very bottom.

### CUBE and GROUPING SETS

Two related features exist on other databases:

- `GROUP BY CUBE (a, b)` gives subtotals for **every** combination: per (a, b), per a, per b, and overall.
- `GROUP BY GROUPING SETS ((a, b), (a), ())` lets you list exactly the levels you want. `ROLLUP (a, b)` is shorthand for those three.

All of them share one problem: a NULL in the output might mark a subtotal, or might be a real NULL from the data. The function `GROUPING(col)` returns 1 on a subtotal row for that column, so the row can be labelled reliably. In the `UNION ALL` form you write the label you want directly:

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

Canada has 13 orders in all, 9 of them delivered. The label `(all statuses)` sorts first within each country because a parenthesis comes before letters.

## Filtering groups: WHERE versus HAVING

A grouped query can filter at two different moments:

- **`WHERE`** tests single rows **before** they are grouped.
- **`HAVING`** tests whole groups **after** they are formed.

```sql-run dataset=bank
SELECT product_cd, ROUND(SUM(avail_balance), 2) AS prod_balance
FROM account
WHERE status = 'ACTIVE'                 -- row filter: only active accounts are grouped
GROUP BY product_cd
HAVING SUM(avail_balance) >= 40000;     -- group filter: only big products are reported
```

Follow the order of events. First `WHERE` discards accounts that are not active. Then `GROUP BY` forms a group per product from what remains. Then `SUM` is calculated for each group. Only then does `HAVING` discard groups whose total is under 40,000. Five products remain.

```mermaid
flowchart LR
    A[all rows] --> B[WHERE keeps rows]
    B --> C[GROUP BY forms groups]
    C --> D[aggregates are calculated]
    D --> E[HAVING keeps groups]
    E --> F[SELECT and ORDER BY]
```

A common mistake is to put the group test in `WHERE`. This block fails on purpose; run it to see the message:

```sql-run dataset=bank
SELECT product_cd, SUM(avail_balance) AS prod_balance
FROM account
WHERE status = 'ACTIVE' AND SUM(avail_balance) > 40000
GROUP BY product_cd;
```

The error, `misuse of aggregate: SUM()`, follows from the order above: when `WHERE` runs, no groups exist yet, so there is nothing to add up.

### HAVING may test aggregates that are not shown

The condition in `HAVING` can use any aggregate, whether or not it is in the `SELECT` list:

```sql-run dataset=bank
SELECT product_cd, ROUND(SUM(avail_balance), 2) AS prod_balance
FROM account
WHERE status = 'ACTIVE'
GROUP BY product_cd
HAVING MIN(avail_balance) >= 1000
   AND MAX(avail_balance) <= 30000;
```

A product is kept only if its smallest active balance is at least 1,000 and its largest is at most 30,000. In other words, *every* active account of the product lies in that range. Two products qualify, `CD` and `SAV`.

### Row tests belong in WHERE

A test on a *grouping column* is accepted in either clause:

```sql
... GROUP BY product_cd HAVING product_cd <> 'CD'    -- works
... WHERE product_cd <> 'CD' GROUP BY product_cd     -- better
```

Prefer `WHERE`. Removing rows early leaves less to group, and a `WHERE` test can use an index, while a `HAVING` test is applied after all the grouping work is done. Good optimizers move such tests for you, but writing them in the right place also tells the reader what you mean: **`WHERE` for rows, `HAVING` for aggregates.**

### HAVING for "has all of these"

`HAVING` is the natural answer to "which groups contain all of, or at least *n* of, something":

```sql-run dataset=shop
-- Customers who have had orders both cancelled and returned
SELECT customer_id
FROM orders
WHERE status IN ('cancelled', 'returned')
GROUP BY customer_id
HAVING COUNT(DISTINCT status) = 2;
```

Step by step: `WHERE` keeps only cancelled and returned orders. `GROUP BY` makes one group per customer. `COUNT(DISTINCT status)` counts how many *different* statuses each customer's remaining orders have. That can only be 1 or 2, and 2 means both are present. The same four customers come back as from the `INTERSECT` query in [INTERSECT, EXCEPT and set operation rules](#/lesson/sql/intersect-except).

The pattern extends: "customers who bought all three of these products" is `WHERE product_id IN (...) GROUP BY customer_id HAVING COUNT(DISTINCT product_id) = 3`.

Counts of rows meeting a condition work inside `HAVING` too:

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

`r.status = 'FAILED'` is 1 for a failed run and 0 otherwise, so its `SUM` is the number of failures. Multiplying by `1.0` keeps the division in decimals. The `churn-gbm` experiment has 10 runs, 2 of them failed: 20%, so it is listed.

## Worked example: a monthly report with a total line

Orders and revenue per month for delivered orders, only for months with at least 15 orders, with a total line at the end. The monthly figures are computed once in a `WITH` clause, which names a query result so that it can be used twice ([Common table expressions](#/lesson/sql/ctes)).

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

`COUNT(DISTINCT o.order_id)` is needed because the join to `order_items` repeats each order once per item. The text `'TOTAL'` sorts after `'2024-...'` because letters come after digits. Adding up `orders` for the total line is valid here because each order belongs to exactly one month; it would *not* be valid for a count of different customers, who can buy in several months.

## Worked example: a two-level report, step by step

*For the bank's deposit products, show the number of accounts and the total balance per branch and product, only for combinations with at least three accounts, with a subtotal per branch and each line's share of its branch.*

**Step 1: the detail level.**

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

Check which test went where. "Active" and "deposit product" are facts about a *single account*, so they sit in `WHERE`. "At least three accounts" is a fact about a *group*, so it sits in `HAVING`. Seven combinations qualify.

**Step 2: add the subtotal level and the share.** The detail is kept in one named result, a second named result totals it per branch, and the final query stacks the two:

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

The helper column `is_total` (0 for detail, 1 for subtotal) exists only to sort each subtotal after its detail lines. One subtle point: the subtotal adds up the *listed* combinations, those that passed `HAVING`, not every account at the branch, which is why it is labelled "(all listed)". Whether a subtotal should include groups that were filtered out is a business decision to make on purpose. `ROLLUP` on other databases computes its subtotals *before* `HAVING` is applied, so there they include the hidden groups.

For comparison, PostgreSQL and MySQL 8 express the two levels in one clause:

```sql
-- PostgreSQL / MySQL 8
SELECT b.name AS branch, a.product_cd, COUNT(*) AS accounts, SUM(a.avail_balance) AS balance,
       GROUPING(a.product_cd) AS is_total
FROM account a JOIN branch b ON b.branch_id = a.open_branch_id
WHERE a.status = 'ACTIVE' AND a.product_cd IN ('CHK', 'SAV', 'MM', 'CD')
GROUP BY ROLLUP (b.name, a.product_cd)
ORDER BY b.name, is_total, balance DESC;
```

## Five HAVING patterns worth memorising

```sql-run dataset=shop
-- 1. A threshold on a count: customers with 6 or more orders
SELECT customer_id, COUNT(*) AS orders
FROM orders GROUP BY customer_id
HAVING COUNT(*) >= 6
ORDER BY orders DESC LIMIT 5;
```

```sql-run dataset=shop
-- 2. "Never": customers with 5+ orders, none of them cancelled or returned
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
-- 5. Comparison with an overall figure: categories larger than the average category
SELECT category_id, COUNT(*) AS products
FROM products GROUP BY category_id
HAVING COUNT(*) > (SELECT AVG(n) FROM (SELECT COUNT(*) AS n FROM products GROUP BY category_id));
```

Patterns 2 and 3 are the grouped way to say "no row in the group has property X" and "every row has property Y". For "never", count the offending rows and require zero. For "always", take the `MAX` (or `MIN`) and test it: if even the deepest discount is at most 10%, all of them are. Pattern 5 compares each group with a number computed by a subquery in parentheses ([Noncorrelated subqueries](#/lesson/sql/noncorrelated)).

> [!NOTE]
> **Differences between databases.** SQLite and MySQL accept a `SELECT` alias in `HAVING` (`HAVING orders >= 6`); PostgreSQL, SQL Server and Oracle do not, so repeat the aggregate. `HAVING` without `GROUP BY` is allowed everywhere and treats the whole table as one group: `SELECT COUNT(*) FROM t HAVING COUNT(*) > 100` returns one row or none.

> [!INTERVIEW]
> "What is the difference between `WHERE` and `HAVING`?" `WHERE` filters rows before grouping and cannot contain aggregates; `HAVING` filters groups after the aggregates are calculated. Add the performance point: tests on plain columns belong in `WHERE`, so that fewer rows are grouped and indexes can be used.

## Pitfalls

- **An aggregate in `WHERE`** is an error. Use `HAVING`.
- **A row test in `HAVING`** is allowed for grouping columns but wasteful. For other columns it is an error, or in SQLite an arbitrary value.
- **Expecting zero-count groups.** `GROUP BY` produces only groups that have rows.
- **Aliases in `HAVING` or `GROUP BY`** work in SQLite and MySQL but not everywhere.
- **NULL in a rollup** may be a subtotal marker or real data. Use `GROUPING()` or explicit labels.
- **Column order in `ROLLUP`** decides which subtotals you get.
- **Subtotals and `HAVING`.** Decide whether hidden groups should count toward the subtotal.

## Summary

- Group by one column, by several (one group per combination that exists) or by a calculation.
- Subtotals: `WITH ROLLUP` in MySQL, `ROLLUP`, `CUBE` and `GROUPING SETS` in the standard; in SQLite stack one grouped query per level with `UNION ALL`.
- `WHERE` filters rows before grouping; `HAVING` filters groups afterwards and may use any aggregate.
- `HAVING COUNT(DISTINCT x) = n` answers "has all of these"; a zero count of offenders answers "never"; a `MIN` or `MAX` test answers "always".

## Glossary

- **Multi-column grouping** — forming one group for each combination of values in several columns.
- **Rollup** — a result that contains detail groups together with subtotals and a grand total.
- **Subtotal / grand total** — a total over part of the groups / over all rows.
- **`ROLLUP`** — a `GROUP BY` option that adds subtotals by removing grouping columns from right to left.
- **`CUBE`** — a `GROUP BY` option that adds subtotals for every combination of the grouping columns.
- **`GROUPING SETS`** — a `GROUP BY` option listing exactly which grouping levels to produce.
- **`GROUPING(col)`** — a function that returns 1 on a row where `col` was rolled up into a subtotal.
- **`HAVING`** — the clause that keeps or discards whole groups, using aggregates.
- **Row filter / group filter** — a test on single rows (`WHERE`) / on groups (`HAVING`).
- **Band (bucket)** — a range of values treated as one group, such as a price band.

```quiz
[
  {"q": "GROUP BY product_cd, open_branch_id creates one group for each...", "options": ["product", "branch", "combination of product and branch present in the data", "possible combination, including empty ones"], "answer": 2, "explain": "Only combinations that actually occur produce groups; missing combinations give no row."},
  {"q": "Why is WHERE SUM(avail_balance) > 40000 an error?", "options": ["SUM needs DISTINCT", "WHERE is applied before groups exist", "40000 is too large", "SUM is only allowed in ORDER BY"], "answer": 1, "explain": "Aggregates are calculated after grouping, and grouping happens after WHERE."},
  {"q": "In ROLLUP (product_cd, open_branch_id), which subtotals are produced?", "options": ["Per branch and grand total", "Per product and grand total", "Per product, per branch and grand total", "Grand total only"], "answer": 1, "explain": "ROLLUP removes columns right to left: (product, branch), then (product), then the grand total."},
  {"q": "How do you get rollup-style subtotals in SQLite?", "options": ["WITH ROLLUP", "GROUP BY ROLLUP", "UNION ALL of queries grouped at each level", "It is impossible"], "answer": 2, "explain": "SQLite lacks ROLLUP, CUBE and GROUPING SETS; write one grouped query per level and stack them."},
  {"q": "Where should the condition status = 'ACTIVE' go in a grouped query?", "options": ["HAVING", "WHERE", "ORDER BY", "Either, at the same cost"], "answer": 1, "explain": "It is a test on single rows: applying it before grouping reduces the work and can use an index."},
  {"q": "What does HAVING COUNT(DISTINCT status) = 2 select, after WHERE status IN ('cancelled','returned')?", "options": ["Customers with exactly two orders", "Customers with both a cancelled and a returned order", "Customers with either status", "Orders with two statuses"], "answer": 1, "explain": "Two different statuses out of the two allowed means both are present."},
  {"q": "What does GROUPING(col) tell you in a rollup result?", "options": ["The size of the group", "Whether col was rolled up into a subtotal, as opposed to being a real NULL", "The sort order", "How many grouping columns there are"], "answer": 1, "explain": "It separates subtotal markers from genuine NULL data."},
  {"q": "Which HAVING test finds products whose every sale had a discount of at most 10%?", "options": ["HAVING AVG(discount) <= 0.10", "HAVING MAX(discount) <= 0.10", "HAVING MIN(discount) <= 0.10", "HAVING COUNT(discount) <= 10"], "answer": 1, "explain": "If the largest discount in the group is at most 10%, then all of them are."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 8 "Grouping and Aggregates" (generating groups: single-column, multicolumn, via expressions; generating rollups; group filter conditions), restated in original wording with this guide's own datasets.
