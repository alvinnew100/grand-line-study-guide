# Views

A well-designed application exposes a public interface and keeps its implementation private, so the implementation can change without breaking its users. Databases can do the same. Instead of letting every report and service query the base tables directly, you can publish **views** — named, stored queries that look and behave like tables. This lesson covers what views are, the four reasons the book gives for using them (data security, data aggregation, hiding complexity, joining partitioned data), when views can be updated, and their relatives: materialized views and temporary views.

## What are views?

A view is a query stored in the data dictionary under a name. It holds **no data of its own**. When you select from a view, the server combines your query with the view's definition and runs the result against the underlying tables.

The book's first example hides most of a customer's federal ID:

```sql-run dataset=bank
CREATE VIEW customer_vw (cust_id, fed_id, cust_type_cd, address, city, state, zipcode) AS
SELECT cust_id,
       'ends in ' || substr(fed_id, -4) AS fed_id,
       cust_type_cd, address, city, state, postal_code
FROM customer;

SELECT cust_id, fed_id, cust_type_cd, city FROM customer_vw LIMIT 6;
```

The first part of the statement names the view and (optionally) its columns; the second is an ordinary SELECT that supplies one expression per column. Creating the view runs nothing against the data — the server merely saves the definition. Afterwards you query it like a table, with any clauses you like:

```sql-run dataset=bank
CREATE VIEW customer_vw AS
SELECT cust_id, 'ends in ' || substr(fed_id, -4) AS fed_id,
       cust_type_cd, address, city, state, postal_code AS zipcode
FROM customer;

SELECT cust_type_cd, COUNT(*) AS n
FROM customer_vw
WHERE state = 'MA'
GROUP BY cust_type_cd;
```

Views can be joined to tables and to other views:

```sql-run dataset=bank
CREATE VIEW customer_vw AS
SELECT cust_id, 'ends in ' || substr(fed_id, -4) AS fed_id, cust_type_cd, city
FROM customer;

SELECT cv.cust_id, cv.fed_id, b.name AS business
FROM customer_vw cv
JOIN business b ON b.cust_id = cv.cust_id
LIMIT 5;
```

What the server actually executes is roughly your query with the view **expanded inline**, as if you had written the SELECT as a derived table. A view is, in effect, a named subquery that many queries can share.

Remove a view with `DROP VIEW customer_vw`. To change one, MySQL and PostgreSQL offer `CREATE OR REPLACE VIEW`; in SQLite you drop and recreate (`DROP VIEW IF EXISTS …`).

## Why use views?

### Data security

If you let users query `customer` directly, they can read full federal IDs. Instead, keep the table private and grant access only to a view that omits or obscures sensitive columns:

```sql
REVOKE ALL ON customer FROM analysts;
GRANT SELECT ON customer_vw TO analysts;
```

You can also restrict **rows** by adding a WHERE clause to the view. The book's example exposes only business customers:

```sql-run dataset=bank
CREATE VIEW business_customer_vw AS
SELECT cust_id, fed_id, cust_type_cd, address, city, state, postal_code
FROM customer
WHERE cust_type_cd = 'B';

SELECT cust_id, city, state FROM business_customer_vw;
```

Give the corporate-banking department this view and they cannot see individuals at all. (SQLite has no users or GRANT — it is an embedded library — but the pattern is universal in server databases. Oracle and PostgreSQL additionally offer row-level security policies for finer control.)

### Data aggregation

Reporting users usually want summaries, not raw rows. A view can make data **appear pre-aggregated**:

```sql-run dataset=bank
CREATE VIEW customer_totals_vw AS
SELECT cust_id, COUNT(*) AS num_accounts, ROUND(SUM(avail_balance), 2) AS tot_deposits
FROM account
WHERE product_cd IN ('CHK', 'SAV', 'MM', 'CD')
GROUP BY cust_id;

SELECT * FROM customer_totals_vw ORDER BY tot_deposits DESC LIMIT 5;
```

This buys design flexibility. Suppose the query becomes too slow as data grows and you decide to maintain a real summary table, refreshed nightly. You can create the table and **redefine the view** to read from it. Every report keeps querying `customer_totals_vw` and nothing downstream changes. The book demonstrates exactly this switch: `CREATE TABLE customer_totals AS SELECT * FROM customer_totals_vw`, then `CREATE OR REPLACE VIEW customer_totals_vw AS SELECT … FROM customer_totals`.

### Hiding complexity

One of the most common uses. A report needs, for each branch, the number of employees, accounts and transactions. Rather than asking every report writer to join four tables correctly, publish:

```sql-run dataset=bank
CREATE VIEW branch_activity_vw AS
SELECT b.name AS branch_name, b.city, b.state,
       (SELECT COUNT(*) FROM account a  WHERE a.open_branch_id = b.branch_id)       AS num_accounts,
       (SELECT COUNT(*) FROM txn t      WHERE t.execution_branch_id = b.branch_id)  AS num_txns,
       (SELECT COUNT(*) FROM employee e WHERE e.assigned_branch_id = b.branch_id)   AS num_emps
FROM branch b;

SELECT * FROM branch_activity_vw;
```

The book points out a nice property of writing the counts as scalar subqueries: if someone selects only `branch_name` and `city` from the view, a good optimizer need not execute the subqueries at all. (Had the view been written with joins and GROUP BY, the joins would always run.)

The ML equivalent is a "model health" view that hides the joins between models, deployments and predictions:

```sql-run dataset=mlops
CREATE VIEW model_health_vw AS
SELECT d.deployment_id,
       m.name || ':v' || m.version AS model,
       d.environment,
       COUNT(p.prediction_id) AS predictions,
       ROUND(AVG(p.latency_ms), 1) AS avg_latency_ms,
       ROUND(100.0 * SUM(p.predicted_label = p.actual_label) / NULLIF(COUNT(p.actual_label), 0), 1) AS accuracy_pct
FROM deployments d
JOIN models m ON m.model_id = d.model_id
LEFT JOIN predictions p ON p.deployment_id = d.deployment_id
GROUP BY d.deployment_id, m.name, m.version, d.environment;

SELECT * FROM model_health_vw
WHERE environment = 'production' AND predictions > 0
ORDER BY accuracy_pct
LIMIT 6;
```

Dashboards query one object; the definition of "accuracy" lives in one place.

### Joining partitioned data

Some designs split a large table into pieces for performance — say, `txn_current` holding the last six months and `txn_historic` holding everything older. Queries that need all transactions would have to know about both. A view with `UNION ALL` presents them as one:

```sql
CREATE VIEW transaction_vw AS
SELECT txn_id, txn_date, account_id, txn_type_cd, amount FROM txn_historic
UNION ALL
SELECT txn_id, txn_date, account_id, txn_type_cd, amount FROM txn_current;
```

The designers can later change the split (or use the database's native partitioning, covered in *Working with large databases*) without touching any query that uses the view.

## Updatable views

If users read through views, can they also write through them? Sometimes. Each server has its own rules; the book lists MySQL's, which are typical. A view is updatable if:

- it uses no aggregate functions;
- it has no `GROUP BY` or `HAVING`;
- it has no subquery in the SELECT or FROM clause (and none in WHERE that refers to the view's tables);
- it does not use `UNION`, `UNION ALL` or `DISTINCT`;
- its FROM clause includes at least one table or updatable view, and uses only inner joins if there are several.

### Updating simple views

`customer_vw` above meets the rules, so in MySQL or PostgreSQL you could run:

```sql
UPDATE customer_vw SET city = 'Woooburn' WHERE city = 'Woburn';
```

and the change lands in `customer`. But a column **derived from an expression** cannot be updated: `UPDATE customer_vw SET fed_id = '…'` fails, because the server cannot invert `'ends in ' || substr(fed_id, -4)`. For the same reason you cannot INSERT through a view with derived columns.

### Updating complex views

With views over joins, the usual rule is that a single statement may modify columns of **only one** of the underlying tables. The book's `business_customer_vw` joins `customer` and `business`; you can update the customer's postal code through it, or the business's incorporation date, but not both in one statement — and inserts are more restricted still.

Two refinements worth knowing:

- `WITH CHECK OPTION` (MySQL, PostgreSQL) rejects writes through a view that would produce rows the view itself cannot see — e.g. inserting an individual through `business_customer_vw`.
- **`INSTEAD OF` triggers** let you define what an insert/update/delete on a view should do. This is how you make arbitrary views writable — and it is the *only* way in SQLite.

> [!NOTE]
> **SQLite views are read-only.** `UPDATE customer_vw …` fails with "cannot modify customer_vw because it is a view". Define an `INSTEAD OF` trigger if you need write-through.

```sql-run dataset=bank
CREATE VIEW customer_city_vw AS SELECT cust_id, city FROM customer;

CREATE TRIGGER customer_city_upd INSTEAD OF UPDATE OF city ON customer_city_vw
BEGIN
  UPDATE customer SET city = NEW.city WHERE cust_id = OLD.cust_id;
END;

UPDATE customer_city_vw SET city = 'Woooburn' WHERE city = 'Woburn';
SELECT city, COUNT(*) AS customers FROM customer GROUP BY city ORDER BY city;
```

## Materialized views

An ordinary view is recomputed every time it is queried. A **materialized view** stores the query's *result* on disk, like a table, and is refreshed on demand or on a schedule (PostgreSQL `CREATE MATERIALIZED VIEW … ; REFRESH MATERIALIZED VIEW …`; Oracle; SQL Server "indexed views"; Snowflake and BigQuery materialized views). You trade freshness and storage for speed. MySQL and SQLite have none; you emulate one with a summary table plus a refresh job (`CREATE TABLE … AS SELECT …`), exposing it through a regular view if you want to keep the option of changing strategy.

```sql-run dataset=shop
CREATE TABLE monthly_revenue_mv AS
SELECT strftime('%Y-%m', o.order_date) AS month,
       ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)), 2) AS revenue
FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.status = 'delivered'
GROUP BY month;

SELECT * FROM monthly_revenue_mv ORDER BY month LIMIT 4;
```

## Views in the modern analytics stack

Tools such as **dbt** are essentially view management systems: each "model" is a SELECT statement that is deployed as a view, a table, or an incrementally maintained table, and models build on each other in layers (staging → intermediate → marts). The principles in this lesson — a stable interface, one definition of each metric, the freedom to materialise later — are the same ones.

## Performance considerations and pitfalls

- **A view is not a cache.** Selecting from a complex view runs the complex query. A view over a view over a view can hide an enormous join behind an innocent-looking `SELECT *`.
- **Predicate pushdown** usually works for simple views (the optimizer merges your WHERE into the view's query). It often cannot push filters through GROUP BY, DISTINCT or window functions, so a filter on an aggregated view may aggregate everything first.
- **`SELECT *` inside a view** is frozen at creation time in some engines and re-evaluated in others; list the columns explicitly.
- **Dropping or altering an underlying column** breaks the view — at query time in SQLite and MySQL, at DDL time in PostgreSQL (which refuses the change).
- **ORDER BY in a view** is not guaranteed to apply to queries on the view; sort in the outer query.
- **Grain confusion:** document what one row of the view represents.

## Summary

- A view is a named, stored query; it holds no data and is expanded into queries that use it.
- Use views for **security** (hide columns and rows), **aggregation** (present summaries, swap in summary tables later), **hiding complexity** (one definition of joins and metrics) and **unifying partitioned data** (UNION ALL).
- Simple views are updatable in MySQL/PostgreSQL subject to rules (no aggregates, GROUP BY, DISTINCT, unions; derived columns are read-only; one base table per statement). SQLite views are read-only without `INSTEAD OF` triggers.
- **Materialized views** store results for speed and must be refreshed.

```quiz
[
  {"q": "What does a (non-materialized) view store?", "options": ["A copy of the data", "The query definition only", "An index of the result", "A snapshot refreshed nightly"], "answer": 1, "explain": "The server saves the SELECT and runs it against the base tables whenever the view is queried."},
  {"q": "Which is NOT one of the book's reasons to use views?", "options": ["Data security", "Hiding complexity", "Making queries run faster automatically", "Joining partitioned data"], "answer": 2, "explain": "An ordinary view does not speed anything up; it is just a stored query."},
  {"q": "Why can't you update the fed_id column of customer_vw?", "options": ["Views are always read-only", "It is derived from an expression the server cannot invert", "fed_id is a primary key", "It needs an index"], "answer": 1, "explain": "Derived columns are not updatable; plain pass-through columns can be (outside SQLite)."},
  {"q": "Which view is updatable under MySQL's rules?", "options": ["One with GROUP BY", "One with UNION ALL", "A single-table view selecting a subset of columns and rows", "One with DISTINCT"], "answer": 2, "explain": "Aggregates, grouping, set operators and DISTINCT make a view non-updatable."},
  {"q": "How can a view be made writable in SQLite?", "options": ["WITH CHECK OPTION", "INSTEAD OF triggers", "CREATE OR REPLACE VIEW", "It cannot"], "answer": 1, "explain": "SQLite views are read-only unless INSTEAD OF triggers define the write behaviour."},
  {"q": "What is the main difference between a view and a materialized view?", "options": ["Materialized views cannot be queried", "A materialized view stores the result and must be refreshed", "Views are faster", "Only views can join tables"], "answer": 1, "explain": "Materialization trades freshness and storage for query speed."},
  {"q": "What does a view let you change without breaking its consumers?", "options": ["The view's column names", "The underlying implementation, e.g. swapping a query for a summary table", "The consumers' SQL dialect", "Nothing"], "answer": 1, "explain": "The view is a stable interface over a changeable implementation."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 14 "Views" (what are views, why use views: data security, data aggregation, hiding complexity, joining partitioned data; updatable views).
