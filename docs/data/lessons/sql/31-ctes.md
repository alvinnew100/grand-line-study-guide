# Common table expressions

> **Before this lesson:** you should be able to use a subquery in `FROM` as a derived table ([Correlated subqueries, EXISTS and subqueries as data sources](#/lesson/sql/correlated-exists)), group and aggregate ([Aggregate functions and GROUP BY](#/lesson/sql/group-by)), write a `CASE` expression ([The CASE expression](#/lesson/sql/case-expressions)) and read a window function with `OVER` ([Window basics and ranking](#/lesson/sql/ranking)). Earlier lessons already used `WITH` in passing; this one explains it properly.

## In plain words

As a query grows, subqueries end up nested inside subqueries. To understand such a query you must find the innermost parentheses and read outward, holding every level in your head. A month later even the author struggles.

A **common table expression**, almost always shortened to **CTE**, fixes that. It is a query whose result you give a name at the top of a statement, using the keyword `WITH`. The rest of the statement then uses that name as if it were a table. The result is temporary: it exists only while that one statement runs.

An everyday picture: a recipe. A badly written recipe is one enormous sentence: "fold the mixture made from whipping the eggs you separated into the chocolate you melted with the butter...". A well-written one has numbered steps, and later steps refer to the results of earlier ones by name: "1. Make the meringue. 2. Make the chocolate base. 3. Fold the meringue into the base." The ingredients and the dish are the same. Only the way it is written down has changed, and that makes all the difference to the cook.

For ordinary queries a CTE adds no new power: anything it does, a derived table can do. What it changes is how you *write* SQL: as a sequence of small named steps, each building on the ones before. (There is one thing only a CTE can do, which is to refer to itself. That is the subject of the next lesson.)

**Why it matters for a job.** In most analytics teams, CTEs are the standard way to write any query longer than a few lines. In a live interview, writing your answer as named steps lets the interviewer follow your thinking and correct you early. The follow-up question "is a CTE faster than a subquery?" is also common, and is answered below.

> [!NOTE]
> CTEs are standard SQL and are supported by PostgreSQL, SQL Server, Oracle, SQLite and MySQL **8.0 and later** (not MySQL 5.7).

## Syntax

```
WITH name [(column, ...)] AS (
    SELECT ...
)
SELECT ... FROM name ...;
```

Compare the two styles on one question: *put each customer in a tier according to their total deposits, then count the customers in each tier.* First with nested derived tables:

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

It works: 8 large, 16 medium and 16 small customers. But to read it you must start at the innermost `SELECT` (the balances), move out to the middle one (the tiers) and finish at the top (the count). Now the same logic with CTEs:

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

The same three rows, and now it reads from top to bottom:

- `WITH balances AS (...)` — step one: total the deposit balances per customer and call the result `balances`.
- `tiers AS (...)` — step two: read from `balances` and label each customer; call that `tiers`.
- The final `SELECT` — step three: count the rows of `tiers` per label.

Each step has a name that says what it holds.

The rules of the `WITH` clause:

- Several CTEs are separated by **commas**. The word `WITH` appears once.
- A CTE can refer to CTEs defined **before** it, not to ones defined later.
- A CTE is visible only in the **one statement** it belongs to. Nothing is stored.
- Its column names come from its `SELECT` list, or from an optional list after the name: `WITH t(a, b) AS (...)`.
- `WITH` can come before `SELECT` and, on most databases, before `INSERT`, `UPDATE` and `DELETE` too.

## CTEs as a pipeline

Think of each CTE as a stage through which the data flows, a **pipeline**. A realistic question: *for each month, what share of delivered revenue came from repeat customers, meaning customers whose first order was in an earlier month?*

```sql-run dataset=shop
WITH order_revenue AS (               -- 1. one row per delivered order, with its value
  SELECT o.order_id, o.customer_id, o.order_date,
         SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS revenue
  FROM orders o
  JOIN order_items oi ON oi.order_id = o.order_id
  WHERE o.status = 'delivered'
  GROUP BY o.order_id, o.customer_id, o.order_date
),
first_order AS (                      -- 2. one row per customer: the month of their first order
  SELECT customer_id, MIN(strftime('%Y-%m', order_date)) AS first_month
  FROM orders
  GROUP BY customer_id
),
labelled AS (                         -- 3. one row per delivered order, tagged new or repeat
  SELECT strftime('%Y-%m', r.order_date) AS month, r.revenue,
         CASE WHEN strftime('%Y-%m', r.order_date) = f.first_month THEN 'new' ELSE 'repeat' END AS kind
  FROM order_revenue r
  JOIN first_order f ON f.customer_id = r.customer_id
)
SELECT month,                         -- 4. one row per month
       ROUND(SUM(revenue), 2) AS revenue,
       ROUND(100.0 * SUM(CASE WHEN kind = 'repeat' THEN revenue ELSE 0 END) / SUM(revenue), 1) AS repeat_pct
FROM labelled
GROUP BY month
ORDER BY month;
```

Four small steps. The comment beside each one states its **grain**, what one row of that step stands for; that single habit prevents most mistakes in long queries. In January 2024, the shop's first month, the repeat share is 0.0: nobody can be a repeat customer yet. By March it is 18.6%.

> [!TIP]
> **Debugging a chain of CTEs.** Temporarily replace the final `SELECT` with `SELECT * FROM some_cte LIMIT 20` to look at any intermediate step. Compare the row counts between steps. A jump usually means a join multiplied rows; a drop means an inner join or a filter removed rows you expected to keep.

## Using a CTE more than once

Unlike a derived table, a CTE can be referred to **several times** in the same statement. Without it you would have to paste the same subquery twice.

Here each product's revenue is compared with the average product revenue of its category:

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

`product_rev` is used once to compute the category averages and once more to compare each product with its category's average. Seven products earn more than twice their category's average; the first is the UltraBook 15 Pro, with 39128.25 against a category average of 19103.05.

CTEs and window functions are natural partners. A window function cannot be used in `WHERE`, so you compute it in a CTE and filter on it in the next step:

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

The CTE numbers the runs of each experiment from most to least accurate and attaches the experiment's average accuracy to every row. The main query keeps number 1, the best run of each experiment, and shows how far it is above that average.

## CTEs with statements that change data

`WITH` can feed an `INSERT`, `UPDATE` or `DELETE`. A clean-up: delete all but the earliest copy of each imported email. (Each Run starts from a fresh copy of the data.)

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

The CTE numbers the copies of each email from oldest to newest. The `DELETE` removes every copy numbered 2 or higher. The check afterwards shows 30 rows left and 30 different emails: no duplicates remain.

PostgreSQL goes further and lets a CTE itself change data: `WITH moved AS (DELETE FROM t WHERE ... RETURNING *) INSERT INTO archive SELECT * FROM moved` moves rows from one table to another in a single statement.

## CTE, subquery, view or temporary table?

| | Where it is visible | Stored? | Can be used twice in one statement | Can be used by later statements |
|---|---|---|---|---|
| Derived table (subquery in `FROM`) | one place in one statement | no | no | no |
| **CTE** | one statement | no | yes | no |
| View | everywhere, permanently | the definition only | yes | yes |
| Temporary table | one session | the data, until the session ends | yes | yes, in the same session |

A **temporary table** is a real table that the database deletes automatically when your session ends.

Guidelines:

- Logic used by **one query**: a CTE.
- Logic shared by **many queries or people**: a view ([Views](#/lesson/sql/views)).
- A costly intermediate result needed by **several statements**, or one that would benefit from an index: a temporary table.
- A tiny one-off filter: an ordinary subquery is fine. Not everything needs to be a CTE.

## Performance: inlining versus materialization

A CTE describes logic; it does not dictate how the work is done. The optimizer can treat it in two ways:

- **Inline** it: substitute its definition into the main query, as with a view. A filter in the main query can then be applied inside the CTE, and unused columns can be dropped.
- **Materialize** it: compute it once into a temporary result and read that result wherever the CTE is mentioned.

Which is better depends on the query. With inlining, a `WHERE customer_id = 42` in the main query can reduce the CTE's work to a single customer; with materialization all customers are computed first. On the other hand, a costly CTE mentioned three times is computed three times when inlined and once when materialized.

Databases differ:

- **PostgreSQL** before version 12 *always* materialized CTEs, which blocked the optimizer from pushing filters in and was a common cause of slow queries. Since version 12 it inlines a CTE that is used once and has no side effects, and you can choose with `AS MATERIALIZED` or `AS NOT MATERIALIZED`.
- **SQLite** (3.35 and later) accepts the same two hints and otherwise decides for itself, typically materializing a CTE that is used more than once.
- **MySQL 8** and **SQL Server** usually inline. SQL Server recomputes a CTE each time it is mentioned.

```sql-run dataset=shop
EXPLAIN QUERY PLAN
WITH per_customer AS (
  SELECT customer_id, COUNT(*) AS orders FROM orders GROUP BY customer_id
)
SELECT a.customer_id, a.orders
FROM per_customer a
JOIN per_customer b ON b.orders = a.orders AND b.customer_id < a.customer_id;
```

The first line of the plan reads `MATERIALIZE per_customer`. The CTE is used twice (as `a` and as `b`), so SQLite computes it once and reads the stored result twice.

Practical advice: write CTEs for clarity first. If a query is slow, read its plan. If a materialized CTE is doing far more work than the final result needs, filter early *inside* it, or apply a hint.

## Style conventions

- Name a CTE for **what it holds** (`monthly_revenue`, `first_order`), not `cte1`, `tmp` or `t2`.
- One logical step per CTE; keep the final `SELECT` short.
- State the **grain** in a comment: `-- one row per customer per month`.
- Filter early, in the first CTE that touches a large table.
- Do not chain CTEs that only rename columns; fold trivial steps together.

## Worked example: refactoring a query into CTEs

Rewriting code to make it clearer without changing what it does is called **refactoring**. A good way to learn CTEs is to refactor a query that works but resists reading. This one answers *which products are bought mostly by repeat customers?* in one nested statement:

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

The recipe: find the innermost subquery, give it a name that says what it holds, and move it to the top. Repeat, working outward.

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

The same five rows. The innermost subquery, the number of orders per customer, became the first CTE. The middle one, buyers and repeat buyers per product, became the second and now reads from the first by name. Each step states its grain and can be run alone.

To confirm that a refactoring changed nothing, compare the two versions with `EXCEPT` in both directions ([INTERSECT, EXCEPT and set operation rules](#/lesson/sql/intersect-except)). Two empty results mean the outputs are identical.

> [!INTERVIEW]
> In a live SQL interview, writing CTEs from the top down *is* your thinking aloud: name a step, say its grain, move on. Be ready for "is a CTE faster than a subquery?" In general, no. It is a tool for readability, and whether it is inlined or materialized depends on the database and version.

## Pitfalls

- **Assuming a CTE is computed once.** It may be recomputed for each mention. Or the reverse: assuming outside filters reach inside when it is materialized.
- **Referring to a CTE defined later** in the `WITH` list.
- **Writing `WITH` twice.** Only the first CTE takes the keyword; the rest follow after commas.
- **Expecting a CTE to survive** into the next statement.
- **MySQL 5.7** has no CTEs.
- **Long chains that hide multiplied rows.** Check the row count at each stage.

## Summary

- A CTE is a named result defined with `WITH name AS (SELECT ...)` and visible to one statement.
- CTEs make a query read from top to bottom as a pipeline, can be used several times, and pair naturally with window functions: compute, then filter.
- Use a CTE for logic inside one statement, a view for shared logic, a temporary table for results needed by several statements or needing an index.
- An optimizer either inlines or materializes a CTE; `MATERIALIZED` and `NOT MATERIALIZED` hints exist in PostgreSQL 12+ and SQLite 3.35+.

## Glossary

- **Common table expression (CTE)** — a named, temporary query result defined with `WITH` and usable in the statement that follows.
- **`WITH` clause** — the part of a statement that defines one or more CTEs.
- **Derived table** — a subquery written in `FROM`, usable only at that one place.
- **Pipeline** — a sequence of steps in which each step's output is the next step's input.
- **Grain** — what one row of a table or result stands for.
- **Temporary table** — a real table that exists only for the current session.
- **Inlining** — substituting a CTE's definition into the query that uses it.
- **Materialization** — computing a CTE once and storing the result for the duration of the statement.
- **Optimization fence** — a boundary the optimizer cannot move filters across, such as a materialized CTE.
- **Hint** — a keyword that tells the optimizer which strategy to use.
- **Refactoring** — rewriting a query to make it clearer without changing its result.

```quiz
[
  {"q": "How long does a CTE exist?", "options": ["Until the session ends", "For the single statement it is defined in", "Until it is dropped", "Until the transaction commits"], "answer": 1, "explain": "A CTE is visible only in its own statement; nothing is stored."},
  {"q": "How are several CTEs written?", "options": ["WITH a AS (...) WITH b AS (...)", "WITH a AS (...), b AS (...)", "WITH a AS (...); b AS (...)", "DEFINE a, b"], "answer": 1, "explain": "WITH appears once and the definitions are separated by commas."},
  {"q": "Which can a CTE do that a derived table cannot?", "options": ["Contain GROUP BY", "Be referred to more than once in the same statement", "Use joins", "Return several columns"], "answer": 1, "explain": "A derived table exists only where it is written; a CTE's name can be reused, and a CTE can also refer to itself."},
  {"q": "A CTE b can refer to CTE a when...", "options": ["a is defined before b in the WITH list", "a is defined after b", "Never", "Only if both are recursive"], "answer": 0, "explain": "Each CTE sees the ones defined earlier in the list."},
  {"q": "What did PostgreSQL versions before 12 always do with CTEs?", "options": ["Inline them", "Materialize them, which stopped filters from being pushed inside", "Reject them", "Keep them for later queries"], "answer": 1, "explain": "They acted as an optimization fence; since version 12, simple CTEs used once are inlined, and hints control the choice."},
  {"q": "Which construct is the best fit for logic shared by many different queries?", "options": ["CTE", "Derived table", "View", "Scalar subquery"], "answer": 2, "explain": "A view is stored in the database and can be used by any query."},
  {"q": "What is a good way to debug a long chain of CTEs?", "options": ["Rewrite it as nested subqueries", "Select from each intermediate CTE and check its rows and row count", "Add DISTINCT everywhere", "Remove the WITH clause"], "answer": 1, "explain": "Looking at each stage shows where rows were multiplied or lost."},
  {"q": "Is a query written with CTEs faster than the same logic written with nested subqueries?", "options": ["Always", "Never", "Not in general; it is a readability tool, and speed depends on whether the database inlines or materializes it", "Only in SQLite"], "answer": 2, "explain": "The optimizer often produces the same plan for both; differences come from inlining versus materialization."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 9 "Subqueries" (subqueries as data sources; common table expressions in the 3rd edition), restated in original wording with this guide's own datasets. SQLite documentation, "The WITH Clause"; PostgreSQL documentation, "WITH Queries (Common Table Expressions)".
