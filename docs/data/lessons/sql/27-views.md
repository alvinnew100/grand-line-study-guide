# Views

> **Before this lesson:** you should be able to write queries with joins, `GROUP BY` and subqueries ([Inner joins](#/lesson/sql/inner-joins), [Aggregate functions and GROUP BY](#/lesson/sql/group-by), [Correlated subqueries, EXISTS and subqueries as data sources](#/lesson/sql/correlated-exists)), stack results with `UNION ALL` ([Set theory and UNION](#/lesson/sql/union)), and know what `CREATE TABLE` does ([Data types and CREATE TABLE](#/lesson/sql/data-types-tables)).

## In plain words

Suppose you have written a useful query: it joins four tables, hides a sensitive column and calculates a total. Ten colleagues need the same thing. They could each copy your query into their own work, and then there are eleven copies to correct when the rules change.

A **view** is a query that has been given a name and saved in the database. From then on, people use the name as if it were a table: `SELECT * FROM my_view`. The view holds **no data of its own**. Each time someone reads from it, the database runs the saved query against the real tables and shows the result.

An everyday picture: a window in a wall. The window lets you see part of the room behind it, from one angle. It contains nothing itself; what you see is the real room, as it is at this moment. And whoever built the wall decided how large the window is and what it faces, so some things in the room cannot be seen through it.

A second picture, for programmers: a view is to a query what a named function is to a block of code. Write it once, use it everywhere, change it in one place.

**Why it matters for a job.** Views are how teams share one agreed definition of things such as "revenue" or "active customer", and how sensitive columns are kept from people who should not see them. Interviewers ask for the difference between a view and a table, between a view and a materialized view, and whether a view makes a query faster (it does not).

## Creating and using a view

The bank's `customer` table holds each customer's tax identification number in `fed_id`. The view below shows only its last four characters.

```sql-run dataset=bank
CREATE VIEW customer_vw (cust_id, fed_id, cust_type_cd, address, city, state, zipcode) AS
SELECT cust_id,
       'ends in ' || substr(fed_id, -4) AS fed_id,
       cust_type_cd, address, city, state, postal_code
FROM customer;

SELECT cust_id, fed_id, cust_type_cd, city FROM customer_vw LIMIT 6;
```

There are two statements. The first is the view's definition:

- `CREATE VIEW customer_vw` gives the view its name.
- The list in parentheses names the view's columns. It is optional; without it the columns take their names from the query.
- After `AS` comes an ordinary `SELECT` that supplies one value per column. The second value replaces the real `fed_id` with the text `ends in` followed by its last four characters.

Creating the view reads no data. The database only saves the definition. The second statement then queries the view exactly like a table. Customer 1 shows `ends in 2186`; the full number cannot be seen through this view.

Any clause can be used on a view. (Each Run starts from a fresh copy of the data, so the examples create their view again.)

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

What the database actually runs is your query with the view's definition slotted in where its name stood, as if you had written the `SELECT` in parentheses as a derived table. A view is, in effect, a named subquery that many queries can share.

`DROP VIEW customer_vw` removes a view; the underlying table is not affected. To change one, MySQL and PostgreSQL offer `CREATE OR REPLACE VIEW`; in SQLite you drop it and create it again.

## Four reasons to use views

### 1. Data security

If people query `customer` directly, they can read full tax numbers. On a server database you keep the table private and give access only to the view. `GRANT` gives a permission and `REVOKE` takes one away:

```sql
-- PostgreSQL, MySQL, SQL Server, Oracle
REVOKE ALL ON customer FROM analysts;
GRANT SELECT ON customer_vw TO analysts;
```

A view can hide **rows** as well as columns, with a `WHERE` in its definition. This one shows only business customers:

```sql-run dataset=bank
CREATE VIEW business_customer_vw AS
SELECT cust_id, fed_id, cust_type_cd, address, city, state, postal_code
FROM customer
WHERE cust_type_cd = 'B';

SELECT cust_id, city, state FROM business_customer_vw;
```

Ten rows. Give a department this view and they cannot see individual customers at all. (SQLite is a library inside one program and has no user accounts or `GRANT`. The pattern applies to server databases.)

### 2. Presenting summaries

People who write reports usually want totals, not raw rows. A view can make data **look as if it were already summarised**:

```sql-run dataset=bank
CREATE VIEW customer_totals_vw AS
SELECT cust_id, COUNT(*) AS num_accounts, ROUND(SUM(avail_balance), 2) AS tot_deposits
FROM account
WHERE product_cd IN ('CHK', 'SAV', 'MM', 'CD')
GROUP BY cust_id;

SELECT * FROM customer_totals_vw ORDER BY tot_deposits DESC LIMIT 5;
```

One row per customer: customer 33 has two deposit accounts holding 29863.36 in total.

This also buys freedom to change your mind. Suppose the summarising query becomes too slow as the data grows, and you decide to keep a real summary table, refreshed every night. You create the table and **redefine the view** to read from it. Every report still queries `customer_totals_vw`, and nothing that uses it has to change.

### 3. Hiding complexity

The most common reason. A report needs, for each branch, the number of accounts, transactions and employees. Instead of asking every report writer to combine four tables correctly, publish one view:

```sql-run dataset=bank
CREATE VIEW branch_activity_vw AS
SELECT b.name AS branch_name, b.city, b.state,
       (SELECT COUNT(*) FROM account a  WHERE a.open_branch_id = b.branch_id)       AS num_accounts,
       (SELECT COUNT(*) FROM txn t      WHERE t.execution_branch_id = b.branch_id)  AS num_txns,
       (SELECT COUNT(*) FROM employee e WHERE e.assigned_branch_id = b.branch_id)   AS num_emps
FROM branch b;

SELECT * FROM branch_activity_vw;
```

Four rows, one per branch: Headquarters has 12 accounts, 44 transactions and 10 employees. The three counts are correlated subqueries. Writing them that way has a pleasant side effect: if someone selects only the branch name and city from the view, a good optimizer does not need to run the counting subqueries at all.

The same idea in machine-learning operations: a "model health" view that hides the joins between models, deployments and predictions.

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

A dashboard queries one object, and the definition of "accuracy" (correct predictions divided by predictions whose true answer is known) lives in one place.

### 4. Joining split data

Some designs split a large table into pieces for speed: say, `txn_current` for the last six months and `txn_historic` for everything older. A query that needs all transactions would have to know about both. A view with `UNION ALL` presents them as one:

```sql
CREATE VIEW transaction_vw AS
SELECT txn_id, txn_date, account_id, txn_type_cd, amount FROM txn_historic
UNION ALL
SELECT txn_id, txn_date, account_id, txn_type_cd, amount FROM txn_current;
```

The designers can later change how the data is split, or switch to the database's built-in way of splitting tables ([Partitioning](#/lesson/sql/partitioning)), without touching any query that uses the view.

## Can you write through a view?

If people read through views, can they also `INSERT`, `UPDATE` and `DELETE` through them? Sometimes. A view that allows it is called an **updatable view**. Each database has its own rules; MySQL's are typical. A view is updatable if:

- it uses no aggregate functions;
- it has no `GROUP BY` or `HAVING`;
- it has no subquery in its `SELECT` list or `FROM` clause;
- it does not use `UNION`, `UNION ALL` or `DISTINCT`;
- its `FROM` clause has at least one table or updatable view, and uses only inner joins if it has several.

The reasoning behind all of these: the database must be able to trace every row of the view back to exactly one row of a real table. A row that stands for a whole group has no single row behind it.

### Simple views

`customer_vw` meets the rules, so in MySQL or PostgreSQL this works, and the change lands in `customer`:

```sql
-- MySQL, PostgreSQL
UPDATE customer_vw SET city = 'Woooburn' WHERE city = 'Woburn';
```

A column **computed from an expression** cannot be updated. `UPDATE customer_vw SET fed_id = '...'` fails, because the database cannot work backwards from `'ends in 2186'` to a full number. For the same reason nothing can be inserted through a view that has computed columns.

### Views over joins

For a view that joins tables, the usual rule is that one statement may change columns of **only one** of the underlying tables.

Two refinements:

- `WITH CHECK OPTION` (MySQL, PostgreSQL) rejects a write through a view if the resulting row would not be visible through that view, such as inserting an individual through `business_customer_vw`.
- An **`INSTEAD OF` trigger** lets you spell out what an insert, update or delete on a view should do. A **trigger** is a small piece of SQL that the database runs automatically when a stated event happens.

> [!NOTE]
> **SQLite views are read-only.** `UPDATE customer_vw ...` fails with "cannot modify customer_vw because it is a view". An `INSTEAD OF` trigger is the only way to write through a view there.

```sql-run dataset=bank
CREATE VIEW customer_city_vw AS SELECT cust_id, city FROM customer;

CREATE TRIGGER customer_city_upd INSTEAD OF UPDATE OF city ON customer_city_vw
BEGIN
  UPDATE customer SET city = NEW.city WHERE cust_id = OLD.cust_id;
END;

UPDATE customer_city_vw SET city = 'Woooburn' WHERE city = 'Woburn';
SELECT city, COUNT(*) AS customers FROM customer GROUP BY city ORDER BY city;
```

The trigger says: whenever someone updates `city` on the view, run this `UPDATE` on the real table instead. `NEW.city` is the value being written and `OLD.cust_id` identifies the row. The final query shows a city called "Woooburn" in the real `customer` table and no "Woburn": the write went through.

## Materialized views

An ordinary view is worked out afresh every time it is queried. A **materialized view** stores the *result* of its query on disk, like a table. Reading it is fast because nothing is recalculated. The price is that the stored result goes out of date and must be **refreshed**, on request or on a schedule.

```sql
-- PostgreSQL
CREATE MATERIALIZED VIEW monthly_revenue_mv AS SELECT ...;
REFRESH MATERIALIZED VIEW monthly_revenue_mv;
```

Oracle, SQL Server (under the name "indexed views"), Snowflake and BigQuery have them too. MySQL and SQLite do not. There you imitate one with a summary table built by `CREATE TABLE ... AS SELECT`, plus a job that rebuilds it:

```sql-run dataset=shop
CREATE TABLE monthly_revenue_mv AS
SELECT strftime('%Y-%m', o.order_date) AS month,
       ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)), 2) AS revenue
FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.status = 'delivered'
GROUP BY month;

SELECT * FROM monthly_revenue_mv ORDER BY month LIMIT 4;
```

`monthly_revenue_mv` is now a real table holding one row per month. It will not notice new orders until it is rebuilt.

## Worked example: a small stack of views for a dashboard

Views are most valuable in layers, each adding one idea.

```sql-run dataset=shop
-- Layer 1: one row per order line, with the money worked out once
CREATE VIEW v_order_lines AS
SELECT o.order_id, o.order_date, o.status, o.customer_id,
       oi.product_id, oi.quantity,
       oi.quantity * oi.unit_price * (1 - oi.discount) AS net_revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id;

-- Layer 2: delivered revenue per customer, built on layer 1
CREATE VIEW v_customer_value AS
SELECT customer_id, COUNT(DISTINCT order_id) AS delivered_orders, ROUND(SUM(net_revenue), 2) AS revenue
FROM v_order_lines
WHERE status = 'delivered'
GROUP BY customer_id;

-- The dashboard query is now short
SELECT c.country, COUNT(*) AS buyers, ROUND(SUM(v.revenue), 2) AS revenue, ROUND(AVG(v.revenue), 2) AS avg_per_buyer
FROM v_customer_value v
JOIN customers c ON c.customer_id = v.customer_id
GROUP BY c.country
ORDER BY revenue DESC;
```

The first view defines "net revenue" (quantity times price, less discount). The second is built on the first and adds "per customer, delivered orders only". The final query reads like the question it answers: Germany has 8 buyers who spent 39768.74 in total, an average of 4971.09 each.

The definition of net revenue lives in exactly one place. If the finance team later decides that returned orders must be subtracted, one view changes and every report follows.

Tools used by analytics teams, such as **dbt**, are in essence systems for managing layers like these: each "model" is a `SELECT` that is deployed as a view or a table, and models build on one another.

## Performance and pitfalls

- **A view is not a stored result.** Reading from a complicated view runs the complicated query. A view built on a view built on a view can hide an enormous join behind a harmless-looking `SELECT *`.
- **Filters may or may not be applied early.** For a simple view, the optimizer merges your `WHERE` into the view's query, so only the needed rows are read; this is called **predicate pushdown**. It often cannot do so through `GROUP BY`, `DISTINCT` or window functions, and then a filter on a summarising view summarises everything first.
- **`SELECT *` inside a view** is fixed at creation time on some databases and re-read on others. List the columns.
- **Dropping or changing an underlying column** breaks the view: when it is next queried in SQLite and MySQL, or at once in PostgreSQL, which refuses the change.
- **`ORDER BY` inside a view** is not guaranteed to apply to queries on the view. Sort in the outer query.
- **Unclear grain.** Record what one row of the view stands for.

> [!INTERVIEW]
> Common questions. *View versus table*: a stored query versus stored data. *View versus materialized view*: worked out on every read versus stored and refreshed. *Can you update a view?* Only simple ones; the rules differ between databases. *Do views make queries faster?* Not in themselves; they make queries easier to maintain and data easier to protect.

## Summary

- A view is a named, saved query; it holds no data and is expanded into the queries that use it.
- Use views for **security** (hide columns and rows), for **summaries** (and the freedom to swap in a summary table later), to **hide complexity** (one definition of joins and measures) and to **unify split data** (`UNION ALL`).
- Simple views can be written through in MySQL and PostgreSQL, subject to rules: no aggregates, grouping, `DISTINCT` or unions; computed columns are read-only; one underlying table per statement. SQLite views are read-only without `INSTEAD OF` triggers.
- A **materialized view** stores its result for speed and must be refreshed.

## Glossary

- **View** — a query saved under a name and used like a table; it stores no data.
- **Base table (underlying table)** — a real table that a view reads from.
- **`GRANT` / `REVOKE`** — statements that give and take away permissions on a server database.
- **Updatable view** — a view through which rows can be inserted, updated or deleted.
- **Computed (derived) column** — a view column produced by an expression instead of copied from a table.
- **`WITH CHECK OPTION`** — a setting that rejects writes through a view when the resulting row would not be visible in it.
- **Trigger** — SQL that the database runs automatically when a stated event occurs.
- **`INSTEAD OF` trigger** — a trigger that replaces a write on a view with statements you supply.
- **Materialized view** — a view whose result is stored on disk and refreshed from time to time.
- **Refresh** — recalculating the stored result of a materialized view.
- **Predicate pushdown** — the optimizer applying your filter inside a view's query, so fewer rows are read.
- **Layered views** — views built on other views, each adding one idea.

```quiz
[
  {"q": "What does an ordinary (non-materialized) view store?", "options": ["A copy of the data", "The query definition only", "An index of the result", "A snapshot refreshed nightly"], "answer": 1, "explain": "The database saves the SELECT and runs it against the underlying tables whenever the view is queried."},
  {"q": "Which is NOT a reason to use an ordinary view?", "options": ["Data security", "Hiding complexity", "Making queries run faster automatically", "Presenting split tables as one"], "answer": 2, "explain": "An ordinary view speeds nothing up; it is a saved query that is run every time."},
  {"q": "Why can't you update the fed_id column of customer_vw?", "options": ["Views are always read-only", "It is computed from an expression the database cannot work backwards from", "fed_id is a primary key", "It needs an index"], "answer": 1, "explain": "Computed columns cannot be updated; columns passed straight through can be, outside SQLite."},
  {"q": "Which view is updatable under MySQL's rules?", "options": ["One with GROUP BY", "One with UNION ALL", "A single-table view selecting some of the columns and rows", "One with DISTINCT"], "answer": 2, "explain": "Aggregates, grouping, set operators and DISTINCT make a view non-updatable, because a view row no longer maps to one table row."},
  {"q": "How can a view be made writable in SQLite?", "options": ["WITH CHECK OPTION", "INSTEAD OF triggers", "CREATE OR REPLACE VIEW", "It cannot"], "answer": 1, "explain": "SQLite views are read-only unless INSTEAD OF triggers define what a write should do."},
  {"q": "What is the main difference between a view and a materialized view?", "options": ["A materialized view cannot be queried", "A materialized view stores the result and must be refreshed", "Views are faster", "Only views can join tables"], "answer": 1, "explain": "Storing the result trades freshness and disk space for speed."},
  {"q": "What does a view let you change without breaking the queries that use it?", "options": ["The view's column names", "What lies behind it, such as swapping a query for a summary table", "The SQL dialect of its users", "Nothing"], "answer": 1, "explain": "The view is a stable front over an implementation that can change."},
  {"q": "A dashboard reads SELECT * FROM v3, where v3 is built on v2, which is built on v1. What is run each time?", "options": ["Only v3's stored rows are read", "The full query formed by expanding all three definitions against the real tables", "Nothing until the views are refreshed", "Only v1"], "answer": 1, "explain": "Ordinary views hold no data; every read expands the whole stack down to the underlying tables."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 14 "Views" (what views are; why use views: data security, data aggregation, hiding complexity, joining partitioned data; updatable views), restated in original wording with this guide's own datasets.
