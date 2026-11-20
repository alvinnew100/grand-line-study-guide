# INTERSECT, EXCEPT and set operation rules

`UNION` adds result sets together. Its siblings answer the other two classic set questions: **what do these results have in common?** (`INTERSECT`) and **what is in the first but not the second?** (`EXCEPT`). This lesson covers both, shows the join- and subquery-based alternatives you will need on engines that lack them, and then lays out the rules that govern all compound queries: where `ORDER BY` goes, and in what order multiple set operators are evaluated.

## INTERSECT

`A INTERSECT B` returns the rows that appear in **both** results, with duplicates removed.

Which employees are both assigned to the Woburn branch *and* have opened accounts there?

```sql-run dataset=bank
SELECT emp_id FROM employee
WHERE assigned_branch_id = 2 AND title LIKE '%Teller'
INTERSECT
SELECT open_emp_id FROM account
WHERE open_branch_id = 2;
```

If the two sets do not overlap, the intersection is empty — no error:

```sql-run dataset=bank
SELECT emp_id FROM employee WHERE title = 'President'
INTERSECT
SELECT open_emp_id FROM account;
```

A set-flavoured question on the shop data: customers who have both a **cancelled** and a **returned** order.

```sql-run dataset=shop
SELECT customer_id FROM orders WHERE status = 'cancelled'
INTERSECT
SELECT customer_id FROM orders WHERE status = 'returned'
ORDER BY customer_id;
```

Try writing that with a single WHERE clause: `status = 'cancelled' AND status = 'returned'` is always false, because one *row* cannot have two statuses. The condition is about *sets of rows per customer*, which is exactly what INTERSECT expresses.

## EXCEPT

`A EXCEPT B` returns the rows of A that do **not** appear in B, with duplicates removed. Order matters.

Tellers assigned to Woburn who have **not** opened an account there:

```sql-run dataset=bank
SELECT emp_id FROM employee
WHERE assigned_branch_id = 2
EXCEPT
SELECT open_emp_id FROM account
WHERE open_branch_id = 2;
```

Products that have never been sold in a delivered order:

```sql-run dataset=shop
SELECT product_id FROM products
EXCEPT
SELECT oi.product_id
FROM order_items oi JOIN orders o ON o.order_id = oi.order_id
WHERE o.status = 'delivered' AND o.order_date >= '2024-10-01';
```

(Products with no delivered sale in the last quarter.) And an ML housekeeping question — finished runs that were never registered as a model:

```sql-run dataset=mlops
SELECT run_id FROM runs WHERE status = 'FINISHED' AND experiment_id = 5
EXCEPT
SELECT run_id FROM models
ORDER BY run_id;
```

> [!NOTE]
> **Dialect support.** `INTERSECT` and `EXCEPT` are standard and available in SQLite, PostgreSQL and SQL Server. Oracle calls EXCEPT `MINUS`. **MySQL only added both in version 8.0.31** — the book (written for earlier MySQL) notes they are not implemented there, and on older servers you must use the join/subquery rewrites below.

### The ALL variants

The standard also defines `INTERSECT ALL` and `EXCEPT ALL`, which respect duplicate counts: if a row appears 3 times in A and once in B, `A EXCEPT ALL B` keeps 2 copies and `A INTERSECT ALL B` keeps 1. PostgreSQL and MySQL 8.0.31+ support them; SQLite does not. Plain `EXCEPT` removes the row entirely if B contains it even once.

## Rewriting without set operators

Every INTERSECT/EXCEPT can be expressed with subqueries. These rewrites are worth knowing — partly for old MySQL, mostly because they let you return *more columns* than the ones being compared.

**Intersection** → `IN` / `EXISTS` (a *semi-join*):

```sql-run dataset=shop
SELECT c.customer_id, c.first_name, c.last_name
FROM customers c
WHERE EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id AND o.status = 'cancelled')
  AND EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id AND o.status = 'returned')
ORDER BY c.customer_id;
```

The INTERSECT version could only return `customer_id`; this one returns names too.

**Difference** → `NOT EXISTS` (an *anti-join*) or `LEFT JOIN ... IS NULL`:

```sql-run dataset=mlops
SELECT r.run_id, r.run_name, r.model_type
FROM runs r
WHERE r.status = 'FINISHED' AND r.experiment_id = 5
  AND NOT EXISTS (SELECT 1 FROM models m WHERE m.run_id = r.run_id)
ORDER BY r.run_id;
```

One subtle difference: set operators treat NULLs as equal to each other (two NULL rows are "the same row" for de-duplication and matching), whereas `=` in a join or `IN` does not match NULLs. When the compared columns can be NULL, `INTERSECT`/`EXCEPT` are the null-safe choice.

## Set operation rules

### Sorting compound query results

A compound query produces **one** result, so it gets **one** `ORDER BY`, written after the last query. The sort keys must be column names (or positions) from the **first** query's select list:

```sql-run dataset=bank
SELECT emp_id, assigned_branch_id AS branch
FROM employee
WHERE title = 'Teller'
UNION
SELECT open_emp_id, open_branch_id
FROM account
WHERE product_cd = 'SAV'
ORDER BY emp_id;
```

`ORDER BY open_emp_id` would fail — that name belongs to the second query and does not exist in the result. The book's advice: give the columns of all queries the same aliases, so there is nothing to remember.

`LIMIT` likewise applies to the whole compound query. To sort or limit an individual branch, wrap it in a subquery:

```sql-run dataset=shop
SELECT * FROM (SELECT name, price, 'cheapest' AS tag FROM products ORDER BY price LIMIT 3)
UNION ALL
SELECT * FROM (SELECT name, price, 'priciest' FROM products ORDER BY price DESC LIMIT 3);
```

### Set operation precedence

With three or more queries, the order of evaluation matters when the operators differ. Compare:

```sql-run dataset=bank
SELECT cust_id FROM account WHERE product_cd = 'SAV'
UNION ALL
SELECT cust_id FROM account WHERE product_cd = 'MM'
EXCEPT
SELECT cust_id FROM account WHERE product_cd = 'MRT'
ORDER BY cust_id;
```

How this is evaluated depends on the engine:

- **Standard SQL, PostgreSQL, SQL Server, MySQL:** `INTERSECT` binds tighter than `UNION` and `EXCEPT`; operators of equal precedence are evaluated top to bottom.
- **SQLite and Oracle:** *all* set operators have equal precedence and are evaluated strictly top to bottom (left-associative).

In the query above both rules agree (UNION ALL first, then EXCEPT — which also de-duplicates the whole result, because EXCEPT is a distinct operation). They disagree for something like `A UNION B INTERSECT C`: standard SQL computes `A UNION (B INTERSECT C)`, SQLite computes `(A UNION B) INTERSECT C`.

Most engines let you add parentheses around the queries to control grouping. SQLite does **not** allow parenthesised SELECTs in a compound query, so there you group with subqueries or CTEs:

```sql-run dataset=bank
-- Customers with a savings account, or with (money market but no mortgage)
WITH mm_no_mortgage AS (
  SELECT cust_id FROM account WHERE product_cd = 'MM'
  EXCEPT
  SELECT cust_id FROM account WHERE product_cd = 'MRT'
)
SELECT cust_id FROM account WHERE product_cd = 'SAV'
UNION
SELECT cust_id FROM mm_no_mortgage
ORDER BY cust_id;
```

> [!TIP]
> Never rely on precedence in a compound query that mixes operators. Name each intermediate set with a CTE; the query becomes portable *and* readable.

## Worked example: symmetric difference

*Which cities have a branch or a customer, but not both?* — `(A − B) ∪ (B − A)`:

```sql-run dataset=bank
WITH branch_cities AS (SELECT city FROM branch),
     customer_cities AS (SELECT city FROM customer),
     only_branch AS (SELECT city FROM branch_cities EXCEPT SELECT city FROM customer_cities),
     only_customer AS (SELECT city FROM customer_cities EXCEPT SELECT city FROM branch_cities)
SELECT city, 'branch only' AS note FROM only_branch
UNION ALL
SELECT city, 'customers only' FROM only_customer
ORDER BY note, city;
```

Every branch city has customers, so only "customers only" cities show up — places where the bank might open its next branch.

## A data-quality habit: comparing two results

`EXCEPT` is the quickest way to test whether two queries return the same rows — for example after refactoring a query. If both of these return nothing, the results are equal as sets:

```sql
SELECT * FROM (old_query) EXCEPT SELECT * FROM (new_query);
SELECT * FROM (new_query) EXCEPT SELECT * FROM (old_query);
```

```sql-run dataset=bank
-- Is the comma-join version equivalent to the ANSI version?
SELECT e.emp_id, d.name FROM employee e JOIN department d ON d.dept_id = e.dept_id
EXCEPT
SELECT e.emp_id, d.name FROM employee e, department d WHERE d.dept_id = e.dept_id;
```

Empty — as expected. (This checks set equality; to compare duplicate counts as well, compare `COUNT(*)` too or use `EXCEPT ALL` where available.)

## Pitfalls

- **EXCEPT is not symmetric** — check which side is which.
- **Both operators de-duplicate** — a count of the result is a count of distinct rows.
- **Mixed operators without explicit grouping** behave differently across engines.
- **ORDER BY names from a later query** don't exist in the result.
- **Old MySQL** lacks INTERSECT/EXCEPT; use EXISTS / NOT EXISTS.

## Summary

- `INTERSECT` keeps rows present in both results; `EXCEPT` (Oracle `MINUS`) keeps rows of the first not present in the second; both remove duplicates and treat NULLs as equal.
- Equivalent rewrites: semi-join (`EXISTS`/`IN`) and anti-join (`NOT EXISTS`), which can also return extra columns.
- One `ORDER BY`/`LIMIT` per compound query, at the end, using the first query's column names.
- Precedence differs: standard SQL gives INTERSECT priority; SQLite evaluates top to bottom. Use CTEs or parentheses to be explicit.

```quiz
[
  {"q": "A = {1,2,3}, B = {2,3,4}. What is A EXCEPT B?", "options": ["{1}", "{4}", "{1,4}", "{2,3}"], "answer": 0, "explain": "Elements of A that are not in B."},
  {"q": "Why can't WHERE status = 'cancelled' AND status = 'returned' find customers with both kinds of order?", "options": ["AND is not allowed on text", "A single row has only one status, so the condition is never true", "It needs DISTINCT", "It can"], "answer": 1, "explain": "The question is about sets of rows per customer; use INTERSECT, EXISTS twice, or GROUP BY/HAVING."},
  {"q": "What does Oracle call EXCEPT?", "options": ["DIFFERENCE", "MINUS", "WITHOUT", "SUBTRACT"], "answer": 1, "explain": "Oracle uses MINUS for set difference."},
  {"q": "In SQLite, how is A UNION B INTERSECT C evaluated?", "options": ["A UNION (B INTERSECT C)", "(A UNION B) INTERSECT C", "It is an error", "Randomly"], "answer": 1, "explain": "SQLite gives all set operators equal precedence, evaluated top to bottom; the standard gives INTERSECT priority."},
  {"q": "Where must ORDER BY go in a compound query?", "options": ["After each SELECT", "After the first SELECT", "Once, after the last SELECT", "Before the first SELECT"], "answer": 2, "explain": "It sorts the combined result and uses the first query's column names."},
  {"q": "An advantage of NOT EXISTS over EXCEPT is...", "options": ["It removes duplicates", "It can return columns that are not part of the comparison", "It is always faster", "It treats NULLs as equal"], "answer": 1, "explain": "EXCEPT compares whole rows, so both sides must have the same columns; NOT EXISTS filters the outer query, which can select anything."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 6 "Working with Sets" (the intersect and except operators, set operation rules, sorting compound query results, set operation precedence). SQLite documentation, "Compound Select Statements".
