# Common table expressions

As queries grow, subqueries nest inside subqueries until the logic reads inside-out and nobody — including the author a month later — can follow it. A **common table expression (CTE)** fixes that. It is a named, temporary result set defined at the top of a statement with the `WITH` keyword and then used like a table in the query that follows. CTEs don't add new computational power for ordinary queries (anything they do, a derived table can do), but they change how you *write* SQL: as a sequence of small, named steps, each building on the previous ones. This lesson covers CTE syntax, chaining, reuse, how they differ from subqueries, views and temp tables, and how optimizers treat them. The next lesson covers the one thing only CTEs can do: recursion.

> [!NOTE]
> CTEs are standard SQL:1999. Supported by PostgreSQL, SQL Server, Oracle, SQLite (3.8.3+) and MySQL **8.0+**. The second edition of the book (MySQL 5) uses derived tables throughout for this reason; its third edition introduces CTEs alongside subqueries in chapter 9.

## Syntax

```
WITH cte_name [(column, ...)] AS (
    SELECT ...
)
SELECT ... FROM cte_name ...;
```

Compare the two styles on a question from the subqueries module — classify customers by total deposit balance, then count customers per class. With nested derived tables:

```sql-run dataset=bank
SELECT tier, COUNT(*) AS customers
FROM (SELECT cust_id,
             CASE WHEN bal < 5000 THEN 'small' WHEN bal < 15000 THEN 'medium' ELSE 'large' END AS tier
      FROM (SELECT cust_id, SUM(avail_balance) AS bal
            FROM account
            WHERE product_cd IN ('CHK', 'SAV', 'MM', 'CD')
            GROUP BY cust_id) balances) tiers
GROUP BY tier;
```

You have to read from the innermost parentheses outward. The same logic with CTEs:

```sql-run dataset=bank
WITH balances AS (
  SELECT cust_id, SUM(avail_balance) AS bal
  FROM account
  WHERE product_cd IN ('CHK', 'SAV', 'MM', 'CD')
  GROUP BY cust_id
),
tiers AS (
  SELECT cust_id,
         CASE WHEN bal < 5000 THEN 'small' WHEN bal < 15000 THEN 'medium' ELSE 'large' END AS tier
  FROM balances
)
SELECT tier, COUNT(*) AS customers
FROM tiers
GROUP BY tier;
```

Identical result, but now it reads top to bottom: *compute balances; assign tiers; count*. Each step has a name that documents its purpose.

Rules of the WITH clause:

- Several CTEs are separated by **commas**; `WITH` appears once.
- A CTE can reference CTEs defined **before** it (and itself, if recursive), not ones defined later.
- A CTE's scope is the **single statement** it is attached to. It is not stored anywhere.
- Column names come from the CTE's SELECT list, or from an optional list after the name: `WITH t(a, b) AS (...)`.
- `WITH` can precede `SELECT`, and in most engines also `INSERT`, `UPDATE` and `DELETE`.

## CTEs as a pipeline

Think of each CTE as a stage in a data pipeline — exactly how you would write a pandas or dbt transformation. A realistic analytics question: *for each month, what share of delivered revenue came from repeat customers (customers who had ordered in an earlier month)?*

```sql-run dataset=shop
WITH order_revenue AS (               -- 1. one row per delivered order with its value
  SELECT o.order_id, o.customer_id, o.order_date,
         SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS revenue
  FROM orders o
  JOIN order_items oi ON oi.order_id = o.order_id
  WHERE o.status = 'delivered'
  GROUP BY o.order_id, o.customer_id, o.order_date
),
first_order AS (                      -- 2. each customer's first order month
  SELECT customer_id, MIN(strftime('%Y-%m', order_date)) AS first_month
  FROM orders
  GROUP BY customer_id
),
labelled AS (                         -- 3. tag each order as new or repeat
  SELECT strftime('%Y-%m', r.order_date) AS month, r.revenue,
         CASE WHEN strftime('%Y-%m', r.order_date) = f.first_month THEN 'new' ELSE 'repeat' END AS kind
  FROM order_revenue r
  JOIN first_order f ON f.customer_id = r.customer_id
)
SELECT month,                         -- 4. aggregate
       ROUND(SUM(revenue), 2) AS revenue,
       ROUND(100.0 * SUM(CASE WHEN kind = 'repeat' THEN revenue ELSE 0 END) / SUM(revenue), 1) AS repeat_pct
FROM labelled
GROUP BY month
ORDER BY month;
```

Four small steps, each of which you can test on its own.

> [!TIP]
> **Debugging a CTE chain:** temporarily replace the final SELECT with `SELECT * FROM some_cte LIMIT 20` to inspect any intermediate step. Check row counts between steps — a jump usually means a join fan-out; a drop means an inner join or filter removed rows you expected to keep.

## Reusing a CTE

Unlike a derived table, a CTE can be referenced **more than once** in the same statement. Without it you would have to paste the same subquery twice.

Compare each product's revenue with the average product revenue of its category:

```sql-run dataset=shop
WITH product_rev AS (
  SELECT p.product_id, p.name, p.category_id,
         SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS revenue
  FROM products p
  JOIN order_items oi ON oi.product_id = p.product_id
  JOIN orders o ON o.order_id = oi.order_id
  WHERE o.status = 'delivered'
  GROUP BY p.product_id, p.name, p.category_id
),
category_avg AS (
  SELECT category_id, AVG(revenue) AS avg_rev
  FROM product_rev                     -- first use
  GROUP BY category_id
)
SELECT pr.name, ROUND(pr.revenue, 2) AS revenue, ROUND(ca.avg_rev, 2) AS category_avg
FROM product_rev pr                    -- second use
JOIN category_avg ca ON ca.category_id = pr.category_id
WHERE pr.revenue > 2 * ca.avg_rev
ORDER BY pr.revenue DESC;
```

A CTE joined to itself is the tidy way to write self joins over a derived result — for example, comparing each month with the same month's neighbour, or pairs of users with the same attribute.

(This particular query could also use `AVG(revenue) OVER (PARTITION BY category_id)`. CTEs and window functions are natural partners: compute a window function in a CTE, filter on it in the next step.)

```sql-run dataset=mlops
WITH scored AS (
  SELECT r.experiment_id, r.run_id, r.model_type, m.value AS accuracy,
         ROW_NUMBER() OVER (PARTITION BY r.experiment_id ORDER BY m.value DESC, r.run_id) AS rn,
         AVG(m.value) OVER (PARTITION BY r.experiment_id) AS exp_avg
  FROM runs r
  JOIN metrics m ON m.run_id = r.run_id AND m.metric_name = 'accuracy'
)
SELECT e.name AS experiment, s.run_id, s.model_type, s.accuracy,
       ROUND(s.accuracy - s.exp_avg, 4) AS lift_over_avg
FROM scored s
JOIN experiments e ON e.experiment_id = s.experiment_id
WHERE s.rn = 1
ORDER BY lift_over_avg DESC;
```

## CTEs with data-modifying statements

`WITH` can feed an INSERT, UPDATE or DELETE. A cleanup — delete all but the earliest copy of each imported email:

```sql-run dataset=shop
WITH ranked AS (
  SELECT import_id,
         ROW_NUMBER() OVER (PARTITION BY lower(trim(email)) ORDER BY imported_at, import_id) AS rn
  FROM customer_imports
)
DELETE FROM customer_imports
WHERE import_id IN (SELECT import_id FROM ranked WHERE rn > 1);

SELECT COUNT(*) AS rows_left, COUNT(DISTINCT lower(trim(email))) AS distinct_emails FROM customer_imports;
```

PostgreSQL goes further with *data-modifying CTEs*: `WITH moved AS (DELETE FROM t WHERE … RETURNING *) INSERT INTO archive SELECT * FROM moved` — an atomic move in one statement.

## CTE, subquery, view or temporary table?

| | Scope | Stored? | Reusable within a statement | Reusable across statements |
|---|---|---|---|---|
| Derived table (subquery in FROM) | one place in one statement | no | no | no |
| **CTE** | one statement | no | yes | no |
| View | permanent, shared | definition only | yes | yes |
| Temporary table | session | data, until the session ends | yes | yes (same session) |

Guidelines:

- Logic used by **one query** → CTE.
- Logic shared by **many queries or people** → view (or a dbt model).
- An expensive intermediate result needed by **several statements**, or that would benefit from an index → temporary table.
- A tiny one-off filter → an inline subquery is fine; don't wrap everything in a CTE.

## Performance: inlining versus materialization

A CTE is a *logical* construct. The optimizer may treat it in two ways:

- **Inline** it into the outer query, like a view or derived table, so filters from outside can be pushed inside and unused columns dropped.
- **Materialize** it: compute it once into a temporary result and scan that wherever it is referenced.

Which is better depends. Inlining lets `WHERE customer_id = 42` on the outside reduce the CTE's work to one customer; materializing computes all customers first. On the other hand, a costly CTE referenced three times is computed three times if inlined and once if materialized.

Engines differ:

- **PostgreSQL** before version 12 *always* materialized CTEs — they were an "optimization fence", and a common cause of slow queries. Since 12 it inlines a CTE that is non-recursive, side-effect-free and referenced once; you can force either behaviour with `AS MATERIALIZED` / `AS NOT MATERIALIZED`.
- **SQLite** (3.35+) accepts the same `MATERIALIZED` / `NOT MATERIALIZED` hints and otherwise decides by itself — typically materializing CTEs that are used more than once.
- **MySQL 8** and **SQL Server** usually merge CTEs into the outer query; SQL Server re-evaluates a multiply-referenced CTE each time.

```sql-run dataset=shop
EXPLAIN QUERY PLAN
WITH per_customer AS (
  SELECT customer_id, COUNT(*) AS orders FROM orders GROUP BY customer_id
)
SELECT a.customer_id, a.orders
FROM per_customer a
JOIN per_customer b ON b.orders = a.orders AND b.customer_id < a.customer_id;
```

Look for `MATERIALIZE per_customer` in the plan: because the CTE is used twice, SQLite computes it once and reuses it.

The practical advice: write CTEs for clarity first; if a query is slow, read the plan, and if a CTE is acting as a fence, filter early *inside* it or apply a hint.

## Style conventions

- Name CTEs for **what they contain** (`monthly_revenue`, `first_order`), not `cte1`, `tmp`, `t2`.
- One logical step per CTE; keep the final SELECT simple.
- State the **grain** in a comment: `-- one row per customer per month`.
- Filter early, in the first CTE that touches a large table.
- Don't chain CTEs that merely rename columns; fold trivial steps together.

## Pitfalls

- **Assuming a CTE is cached** — it may be recomputed per reference (or the reverse: assuming filters get pushed in when it is materialized).
- **Referencing a CTE defined later** in the WITH list.
- **Repeating `WITH`** — only the first CTE takes the keyword; the rest are comma-separated.
- **Expecting a CTE to persist** to the next statement.
- **MySQL 5.7** — no CTE support.
- **Deep chains hiding fan-outs** — check row counts at each stage.

## Worked example: refactoring a query into CTEs

A good way to learn CTEs is to refactor a query that works but resists reading. This one answers *which products are bought mostly by repeat customers?* in a single nested statement:

```sql-run dataset=shop
SELECT p.name, t.buyers, t.repeat_buyers, ROUND(100.0 * t.repeat_buyers / t.buyers, 1) AS repeat_pct
FROM (SELECT oi.product_id,
             COUNT(DISTINCT o.customer_id) AS buyers,
             COUNT(DISTINCT CASE WHEN c.n_orders > 1 THEN o.customer_id END) AS repeat_buyers
      FROM order_items oi
      JOIN orders o ON o.order_id = oi.order_id
      JOIN (SELECT customer_id, COUNT(*) AS n_orders FROM orders GROUP BY customer_id) c
        ON c.customer_id = o.customer_id
      GROUP BY oi.product_id) t
JOIN products p ON p.product_id = t.product_id
WHERE t.buyers >= 8
ORDER BY repeat_pct DESC
LIMIT 5;
```

The refactoring recipe: find the innermost subquery, give it a name that says what it contains, move it to the top; repeat outward.

```sql-run dataset=shop
WITH orders_per_customer AS (          -- one row per customer
  SELECT customer_id, COUNT(*) AS n_orders
  FROM orders
  GROUP BY customer_id
),
product_buyers AS (                    -- one row per product
  SELECT oi.product_id,
         COUNT(DISTINCT o.customer_id) AS buyers,
         COUNT(DISTINCT CASE WHEN c.n_orders > 1 THEN o.customer_id END) AS repeat_buyers
  FROM order_items oi
  JOIN orders o              ON o.order_id = oi.order_id
  JOIN orders_per_customer c ON c.customer_id = o.customer_id
  GROUP BY oi.product_id
)
SELECT p.name, b.buyers, b.repeat_buyers,
       ROUND(100.0 * b.repeat_buyers / b.buyers, 1) AS repeat_pct
FROM product_buyers b
JOIN products p ON p.product_id = b.product_id
WHERE b.buyers >= 8
ORDER BY repeat_pct DESC
LIMIT 5;
```

Same rows, same plan in most engines — but each step now states its **grain** in a comment and can be checked alone. Verify that a refactoring changed nothing by comparing the two versions with `EXCEPT` in both directions; an empty result both ways means the outputs are identical.

> [!INTERVIEW]
> In a live SQL interview, writing CTEs top-down *is* your thinking aloud: name a step, say its grain, move on. Interviewers can follow and correct you early. Be ready for the follow-up "is a CTE faster than a subquery?" — generally no; it is a readability tool, and whether it is inlined or materialized depends on the engine.

## Summary

- A CTE is a named result set defined with `WITH name AS (SELECT …)` and visible to one statement.
- CTEs make queries read top-down as a pipeline, can be referenced several times, and combine naturally with window functions (compute, then filter).
- Use a CTE for single-statement logic, a view for shared logic, a temp table for multi-statement or indexed intermediates.
- Optimizers either inline or materialize CTEs; `MATERIALIZED` / `NOT MATERIALIZED` hints exist in PostgreSQL 12+ and SQLite 3.35+.

```quiz
[
  {"q": "How long does a CTE exist?", "options": ["Until the session ends", "For the single statement it is defined in", "Until it is dropped", "Until the transaction commits"], "answer": 1, "explain": "A CTE's scope is its statement; nothing is stored."},
  {"q": "How are multiple CTEs written?", "options": ["WITH a AS (...) WITH b AS (...)", "WITH a AS (...), b AS (...)", "WITH a AS (...); b AS (...)", "DEFINE a, b"], "answer": 1, "explain": "WITH appears once and the definitions are comma-separated."},
  {"q": "Which can a CTE do that a derived table cannot?", "options": ["Contain GROUP BY", "Be referenced more than once in the same statement", "Use joins", "Return multiple columns"], "answer": 1, "explain": "A derived table exists only where it is written; a CTE's name can be reused (and can be recursive)."},
  {"q": "A CTE b can reference CTE a when...", "options": ["a is defined before b in the WITH list", "a is defined after b", "Never", "Only if both are recursive"], "answer": 0, "explain": "Each CTE sees the ones defined earlier."},
  {"q": "What did PostgreSQL versions before 12 always do with CTEs?", "options": ["Inline them", "Materialize them, acting as an optimization fence", "Reject them", "Cache them across queries"], "answer": 1, "explain": "That prevented predicate pushdown; since 12, simple single-use CTEs are inlined and hints control the choice."},
  {"q": "Which construct is the best fit for logic shared by many different queries?", "options": ["CTE", "Derived table", "View", "Scalar subquery"], "answer": 2, "explain": "A view is stored in the catalog and usable by any query."},
  {"q": "What is a good way to debug a long CTE chain?", "options": ["Rewrite as nested subqueries", "Select from each intermediate CTE and check its rows and counts", "Add DISTINCT everywhere", "Remove the WITH clause"], "answer": 1, "explain": "Inspecting each stage localises fan-outs and unexpected row loss."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 9 "Subqueries" — subqueries as data sources (2nd ed.) and "Common table expressions" (3rd ed.). SQLite documentation, "The WITH Clause"; PostgreSQL documentation, "WITH Queries (Common Table Expressions)".
