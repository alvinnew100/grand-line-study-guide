# The CASE expression

Sometimes you want SQL to branch: show one thing for individual customers and another for businesses, label balances as low or high, treat credits and debits differently in the same sum. **Conditional logic** is the ability to take one of several paths depending on the values in a row, and in SQL it is provided by the `CASE` expression. CASE is part of the SQL-92 standard, works identically in every major database, and can be used in SELECT, INSERT, UPDATE and DELETE statements — almost anywhere an expression is allowed. This lesson covers its two forms and their rules; the next applies them to the classic patterns.

## What is conditional logic?

The bank has two kinds of customer, with names stored in different subtype tables. With outer joins you can fetch both names in separate columns:

```sql-run dataset=bank
SELECT c.cust_id, c.fed_id, c.cust_type_cd,
       i.fname || ' ' || i.lname AS indiv_name,
       b.name AS business_name
FROM customer c
LEFT JOIN individual i ON c.cust_id = i.cust_id
LEFT JOIN business b   ON c.cust_id = b.cust_id
WHERE c.cust_id BETWEEN 28 AND 33;
```

The caller must now look at two columns to find the name. With conditional logic the query decides which one to return:

```sql-run dataset=bank
SELECT c.cust_id, c.fed_id,
       CASE
         WHEN c.cust_type_cd = 'I' THEN i.fname || ' ' || i.lname
         WHEN c.cust_type_cd = 'B' THEN b.name
         ELSE 'Unknown'
       END AS name
FROM customer c
LEFT JOIN individual i ON c.cust_id = i.cust_id
LEFT JOIN business b   ON c.cust_id = b.cust_id
WHERE c.cust_id BETWEEN 28 AND 33;
```

One `name` column, filled from the right source for each row.

> [!NOTE]
> Many databases have their own conditional functions — Oracle's `DECODE`, MySQL's `IF()`, SQL Server's `IIF` and `COALESCE`'s cousins, SQLite's `iif()`. The book recommends CASE over all of them, because it is standard, runs everywhere, and reads clearly. `iif(cond, a, b)` in SQLite is simply shorthand for `CASE WHEN cond THEN a ELSE b END`.

## Searched CASE expressions

The form used above is the **searched** case expression:

```
CASE
  WHEN condition_1 THEN expression_1
  WHEN condition_2 THEN expression_2
  ...
  [ELSE default_expression]
END
```

Rules:

1. Conditions are evaluated **in order, top to bottom**.
2. As soon as one evaluates to TRUE, the corresponding expression is returned and **no further WHEN clauses are evaluated**.
3. If none is true, the `ELSE` expression is returned. If there is no ELSE, the result is **NULL**.
4. All result expressions should return the **same type** (strings, numbers, dates…). PostgreSQL enforces this; SQLite, being dynamically typed, will let you mix and leave you to deal with the consequences.

Each condition is a full boolean expression: comparisons, `AND`/`OR`, `IN`, `LIKE`, `IS NULL`, even subqueries.

Because the first true branch wins, order matters when conditions overlap. This lets you write thresholds compactly:

```sql-run dataset=shop
SELECT name, price,
       CASE
         WHEN price >= 1000 THEN 'premium'
         WHEN price >= 100  THEN 'mid-range'     -- implicitly: and price < 1000
         WHEN price >= 20   THEN 'budget'
         ELSE 'impulse'
       END AS tier
FROM products
ORDER BY price DESC
LIMIT 10;
```

Reverse the order — test `price >= 20` first — and nearly everything would be labelled "budget". When a CASE gives unexpected labels, check the order of its branches first.

### The missing ELSE

Without ELSE, unmatched rows get NULL. Sometimes that is a bug, and sometimes it is exactly what you want — it is the key to conditional aggregation, because aggregates ignore NULLs:

```sql-run dataset=bank
SELECT COUNT(*) AS accounts,
       COUNT(CASE WHEN status = 'ACTIVE' THEN 1 END) AS active,
       COUNT(CASE WHEN status = 'FROZEN' THEN 1 END) AS frozen,
       ROUND(AVG(CASE WHEN product_cd = 'CHK' THEN avail_balance END), 2) AS avg_checking
FROM account;
```

`AVG(CASE WHEN product_cd = 'CHK' THEN avail_balance END)` averages only checking balances: the other rows yield NULL and are skipped. With `ELSE 0` the average would be dragged down by all the zeros — a subtle and common mistake.

### Subqueries inside CASE

The branches can contain scalar subqueries. The book rewrites the name query without any outer joins, fetching the name with a correlated subquery chosen by customer type:

```sql-run dataset=bank
SELECT c.cust_id, c.fed_id,
       CASE
         WHEN c.cust_type_cd = 'I' THEN
           (SELECT i.fname || ' ' || i.lname FROM individual i WHERE i.cust_id = c.cust_id)
         WHEN c.cust_type_cd = 'B' THEN
           (SELECT b.name FROM business b WHERE b.cust_id = c.cust_id)
         ELSE 'Unknown'
       END AS name
FROM customer c
WHERE c.cust_id BETWEEN 28 AND 33;
```

Only the subquery of the branch that fires is executed for each row, so only the relevant table is touched.

## Simple CASE expressions

The **simple** case expression compares one expression with a list of values:

```
CASE expression
  WHEN value_1 THEN result_1
  WHEN value_2 THEN result_2
  ...
  [ELSE default_result]
END
```

```sql-run dataset=bank
SELECT c.cust_id,
       CASE c.cust_type_cd
         WHEN 'I' THEN 'Individual'
         WHEN 'B' THEN 'Business'
         ELSE 'Unknown Customer Type'
       END AS customer_type
FROM customer c
WHERE c.cust_id BETWEEN 28 AND 33;
```

It is less flexible than the searched form — it can only test **equality** against the one expression — and therefore, the book notes, less useful: no ranges, no multiple columns. Use it for straightforward code-to-label translation; reach for the searched form for everything else.

One trap: a simple CASE can never match NULL, because it uses `=`.

```sql-run dataset=bank
SELECT txn_id,
       CASE teller_emp_id WHEN NULL THEN 'ATM/online' ELSE 'branch' END AS wrong,
       CASE WHEN teller_emp_id IS NULL THEN 'ATM/online' ELSE 'branch' END AS right
FROM txn
LIMIT 6;
```

`WHEN NULL` compares `teller_emp_id = NULL`, which is never TRUE.

## CASE is an expression, not a statement

In procedural languages `if` controls which statements run. SQL's CASE is an **expression**: it produces a value. So it can appear anywhere a value can.

**In the select list** — every example so far.

**In ORDER BY** — custom sort orders:

```sql-run dataset=bank
SELECT emp_id, fname, lname, title
FROM employee
ORDER BY CASE title
           WHEN 'President' THEN 1
           WHEN 'Vice President' THEN 2
           WHEN 'Treasurer' THEN 3
           ELSE 4
         END, lname
LIMIT 8;
```

**In GROUP BY** — group by a derived category:

```sql-run dataset=mlops
SELECT CASE
         WHEN model_type IN ('bert-base', 'distilbert', 'resnet50', 'efficientnet-b0') THEN 'deep learning'
         WHEN model_type IN ('xgboost', 'lightgbm', 'random_forest', 'lambdamart') THEN 'tree ensemble'
         ELSE 'classical'
       END AS family,
       COUNT(*) AS runs,
       ROUND(SUM(gpu_hours), 1) AS gpu_hours
FROM runs
GROUP BY family
ORDER BY runs DESC;
```

**In WHERE** — possible, but usually a plain boolean expression is clearer and more index-friendly. `WHERE CASE WHEN type = 'I' THEN a ELSE b END > 10` is better written as `WHERE (type = 'I' AND a > 10) OR (type <> 'I' AND b > 10)`.

**Inside aggregate functions** — the most important placement, covered in the next lesson.

**In UPDATE … SET** — conditional updates in a single pass:

```sql-run dataset=shop
UPDATE products
SET price = CASE
              WHEN discontinued = 1 THEN ROUND(price * 0.70, 2)   -- clearance
              WHEN price >= 1000    THEN ROUND(price * 0.95, 2)   -- premium promo
              ELSE price
            END;
SELECT name, price, discontinued FROM products ORDER BY product_id LIMIT 6;
```

Note the `ELSE price`. Without it, every product matching neither branch would have its price set to NULL.

## Nesting and readability

CASE expressions can be nested, and a long chain of WHENs is fine. When they grow, consider whether the logic is really *data*: a mapping from codes to labels or thresholds to tiers belongs in a **lookup table** that you join to, so that changing a threshold is an UPDATE rather than a code change in twenty queries.

```sql-run dataset=bank
WITH tier(name, low, high) AS (
  VALUES ('low', 0, 999.99), ('medium', 1000, 9999.99), ('high', 10000, 1e12)
)
SELECT t.name AS tier, COUNT(*) AS accounts
FROM account a
JOIN tier t ON a.avail_balance BETWEEN t.low AND t.high
GROUP BY t.name;
```

## Related shorthand functions

Three standard functions are special cases of CASE:

| Function | Equivalent CASE |
|---|---|
| `COALESCE(a, b, c)` | `CASE WHEN a IS NOT NULL THEN a WHEN b IS NOT NULL THEN b ELSE c END` |
| `NULLIF(a, b)` | `CASE WHEN a = b THEN NULL ELSE a END` |
| `iif(c, x, y)` (SQLite, SQL Server) / `IF(c, x, y)` (MySQL) | `CASE WHEN c THEN x ELSE y END` |

Use them when they fit; they are shorter and express intent.

## Pitfalls

- **Branch order** — first true WHEN wins.
- **Missing ELSE** — NULL results; fatal in UPDATE, useful in aggregates.
- **`ELSE 0` inside AVG / COUNT** — changes the meaning.
- **Simple CASE with NULL** — never matches; use the searched form with `IS NULL`.
- **Mixed result types** — errors in strict engines, surprising sorts in SQLite.
- **CASE in WHERE on big tables** — hides columns from the optimizer.

## Summary

- CASE is SQL's standard conditional expression; it returns a value and can be used almost anywhere.
- **Searched CASE** evaluates arbitrary conditions top-down and returns the first match; **simple CASE** tests one expression for equality.
- No match and no ELSE yields NULL.
- Use CASE in SELECT for labels, in ORDER BY for custom sorts, in GROUP BY for derived categories, in UPDATE for conditional changes, and inside aggregates for conditional totals.

```quiz
[
  {"q": "What does a CASE expression return when no WHEN matches and there is no ELSE?", "options": ["0", "An empty string", "NULL", "An error"], "answer": 2, "explain": "The implicit ELSE is NULL."},
  {"q": "For price = 1500, what does CASE WHEN price >= 20 THEN 'budget' WHEN price >= 1000 THEN 'premium' END return?", "options": ["premium", "budget", "NULL", "Both"], "answer": 1, "explain": "Branches are tested in order and the first true one wins."},
  {"q": "Why does CASE x WHEN NULL THEN 'missing' END never return 'missing'?", "options": ["NULL is not allowed in CASE", "Simple CASE compares with =, and x = NULL is never TRUE", "ELSE is required", "It does return it"], "answer": 1, "explain": "Use the searched form: CASE WHEN x IS NULL THEN ..."},
  {"q": "AVG(CASE WHEN product_cd = 'CHK' THEN avail_balance END) computes...", "options": ["The average of all balances", "The average checking balance", "Zero", "The count of checking accounts"], "answer": 1, "explain": "Non-checking rows yield NULL, which AVG ignores."},
  {"q": "What is the danger of omitting ELSE in UPDATE t SET price = CASE WHEN ... THEN ... END?", "options": ["Nothing", "Rows matching no branch get price = NULL", "The update is skipped", "A syntax error"], "answer": 1, "explain": "Add ELSE price to leave other rows unchanged."},
  {"q": "Which form can test ranges such as balance < 1000?", "options": ["Simple CASE", "Searched CASE", "Both", "Neither"], "answer": 1, "explain": "Simple CASE only tests equality against one expression."},
  {"q": "NULLIF(a, b) is shorthand for...", "options": ["CASE WHEN a IS NULL THEN b ELSE a END", "CASE WHEN a = b THEN NULL ELSE a END", "CASE WHEN b IS NULL THEN a END", "COALESCE(a, b)"], "answer": 1, "explain": "It returns NULL when the two arguments are equal."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 11 "Conditional Logic" (what is conditional logic, the case expression, searched and simple case expressions).
