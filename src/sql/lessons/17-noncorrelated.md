# Noncorrelated subqueries

A **subquery** is a query contained inside another SQL statement (the *containing statement*). It is always enclosed in parentheses and is usually executed before the containing statement. Like any query, it returns a result set, which may be a single value, a single column of many rows, or a full table — and the shape of that result decides how the containing statement is allowed to use it. Subqueries are one of SQL's most powerful tools, because they let you use the answer to one question as an ingredient in another.

This lesson defines the types of subquery and covers **noncorrelated** subqueries — those that can be run on their own. The next lesson covers correlated subqueries, `EXISTS`, and subqueries used as data sources.

## What is a subquery?

A simple example: find the most recently opened account.

```sql-run dataset=bank
SELECT account_id, product_cd, cust_id, open_date
FROM account
WHERE open_date = (SELECT MAX(open_date) FROM account);
```

The subquery returns one value — the latest `open_date`. The containing query then finds the account(s) with that date. You can always check what a noncorrelated subquery contributes by running it alone:

```sql-run dataset=bank
SELECT MAX(open_date) FROM account;
```

Think of the subquery's result as a temporary table with *statement scope*: the server frees it when the statement finishes.

Couldn't you do this in two steps — run the inner query, copy the answer, paste it into the outer one? Yes, and the subquery does precisely that for you, atomically, and stays correct when the data changes.

## Subquery types

Subqueries are classified along two axes.

**By shape of the result:**

| Shape | Returns | Usable with |
|---|---|---|
| **Scalar** | one row, one column | `=`, `<>`, `<`, `>`, arithmetic, select list — anywhere a value is allowed |
| **Multiple-row, single-column** | a list of values | `IN`, `NOT IN`, `ANY`, `ALL` |
| **Multicolumn** | rows of several columns | row comparison `(a, b) IN (...)`, or as a table in FROM |

**By dependence on the containing statement:**

- **Noncorrelated** — completely self-contained; executed once, before the containing statement.
- **Correlated** — references columns of the containing statement; conceptually executed once per candidate row.

## Scalar subqueries

A scalar subquery can appear on either side of a comparison. Accounts *not* opened by the head teller of the Woburn branch:

```sql-run dataset=bank
SELECT account_id, product_cd, cust_id, avail_balance
FROM account
WHERE open_emp_id <> (SELECT e.emp_id
                      FROM employee e
                      JOIN branch b ON e.assigned_branch_id = b.branch_id
                      WHERE e.title = 'Head Teller' AND b.city = 'Woburn')
LIMIT 8;
```

The subquery can be as complex as it needs to be — joins, filters, aggregates — as long as it yields one row and one column.

What if it returns **more than one row**? The book shows the error by dropping the title filter so that several Woburn employees come back. PostgreSQL, MySQL and SQL Server refuse: *"subquery returns more than 1 row"*. That makes sense — a single `open_emp_id` cannot be equated to a *set* of ids.

> [!WARNING]
> **SQLite does not raise this error.** If a subquery used as a scalar returns several rows, SQLite silently uses the **first** row. That makes a logic bug invisible here and a crash in production on another engine. When you intend a scalar subquery, guarantee one row: aggregate (`MAX`, `MIN`), filter on a unique key, or add `LIMIT 1` with a deterministic `ORDER BY`.

```sql-run dataset=bank
-- Legal in SQLite, an error in PostgreSQL/MySQL: the subquery returns 4 rows
SELECT COUNT(*) AS misleading
FROM account
WHERE open_emp_id <> (SELECT e.emp_id
                      FROM employee e
                      JOIN branch b ON e.assigned_branch_id = b.branch_id
                      WHERE b.city = 'Woburn');
```

A scalar subquery that returns **zero rows** evaluates to NULL in every engine, and any comparison with it is UNKNOWN — so the outer query returns nothing.

Scalar subqueries shine for "compare with an overall statistic" questions:

```sql-run dataset=shop
SELECT name, price,
       ROUND(price - (SELECT AVG(price) FROM products), 2) AS diff_from_avg
FROM products
WHERE price > 2 * (SELECT AVG(price) FROM products)
ORDER BY price DESC;
```

## Multiple-row, single-column subqueries

When a subquery returns several rows you cannot equate to it, but four operators accept a set.

### IN and NOT IN

`IN` tests membership in the set the subquery returns. Which employees supervise other employees?

```sql-run dataset=bank
SELECT emp_id, fname, lname, title
FROM employee
WHERE emp_id IN (SELECT superior_emp_id FROM employee);
```

The subquery returns the ids of everyone who is somebody's boss. With `NOT IN` we would ask for the employees who supervise nobody — but the subquery's result contains a NULL (the president has no superior), and as the NULL lesson explained, `NOT IN` against a set containing NULL returns no rows. The book's version of the query adds the essential filter:

```sql-run dataset=bank
SELECT emp_id, fname, lname, title
FROM employee
WHERE emp_id NOT IN (SELECT superior_emp_id
                     FROM employee
                     WHERE superior_emp_id IS NOT NULL);
```

Delete the `WHERE superior_emp_id IS NOT NULL` line and run it again to see the trap for yourself.

`IN` with a subquery replaces hard-coded lists with *self-maintaining* ones:

```sql-run dataset=mlops
-- Runs belonging to experiments owned by the risk team
SELECT run_id, run_name, status
FROM runs
WHERE experiment_id IN (SELECT experiment_id FROM experiments WHERE team = 'risk')
LIMIT 8;
```

### ALL

`ALL` compares a value with **every** value in the set; the condition is true only if the comparison holds for all of them. Accounts with a balance smaller than *all* of customer 31's accounts:

```sql-run dataset=bank
SELECT account_id, cust_id, product_cd, avail_balance
FROM account
WHERE status = 'ACTIVE'
  AND avail_balance < (SELECT MIN(avail_balance) FROM account WHERE cust_id = 31)
ORDER BY avail_balance DESC
LIMIT 6;
```

In standard SQL you would write `avail_balance < ALL (SELECT avail_balance FROM account WHERE cust_id = 31)`. `< ALL (set)` means "less than the minimum"; `> ALL (set)` means "greater than the maximum"; `<> ALL (set)` is the same as `NOT IN` — with the same NULL problem: if the set contains a NULL, every `ALL` comparison becomes UNKNOWN.

### ANY

`ANY` (synonym `SOME`) is true if the comparison holds for **at least one** value. `> ANY (set)` means "greater than the minimum"; `= ANY (set)` is exactly `IN`.

> [!NOTE]
> **SQLite does not implement `ANY`, `ALL` or `SOME`.** MySQL, PostgreSQL, Oracle and SQL Server do. The portable rewrites are simple and arguably clearer:
>
> | Standard | Rewrite |
> |---|---|
> | `x > ALL (S)` | `x > (SELECT MAX(v) FROM S)` |
> | `x < ALL (S)` | `x < (SELECT MIN(v) FROM S)` |
> | `x > ANY (S)` | `x > (SELECT MIN(v) FROM S)` |
> | `x < ANY (S)` | `x < (SELECT MAX(v) FROM S)` |
> | `x = ANY (S)` | `x IN (S)` |
> | `x <> ALL (S)` | `x NOT IN (S)` |
>
> One subtle difference: on an **empty** set, `x > ALL (S)` is TRUE (vacuously) while `x > (SELECT MAX …)` compares with NULL and is UNKNOWN.

The book's ANY example finds accounts whose balance exceeds the balance of *any* of one customer's accounts — with the rewrite:

```sql-run dataset=bank
SELECT account_id, cust_id, product_cd, avail_balance
FROM account
WHERE avail_balance > (SELECT MIN(avail_balance) FROM account WHERE cust_id = 31)
  AND cust_id <> 31
ORDER BY avail_balance
LIMIT 6;
```

## Multicolumn subqueries

So far each subquery returned a single column. Sometimes the match involves two or more columns at once. The book's example: accounts opened at the Woburn branch *by a teller* could be written with two single-column subqueries…

```sql-run dataset=bank
SELECT account_id, product_cd, cust_id
FROM account
WHERE open_branch_id = (SELECT branch_id FROM branch WHERE name = 'Woburn Branch')
  AND open_emp_id IN (SELECT emp_id FROM employee WHERE title IN ('Teller', 'Head Teller'))
LIMIT 6;
```

…or with one subquery returning (branch, employee) **pairs**, compared against a parenthesised pair of columns:

```sql-run dataset=bank
SELECT account_id, product_cd, cust_id
FROM account
WHERE (open_branch_id, open_emp_id) IN
      (SELECT b.branch_id, e.emp_id
       FROM branch b
       JOIN employee e ON e.assigned_branch_id = b.branch_id
       WHERE b.name = 'Woburn Branch'
         AND e.title IN ('Teller', 'Head Teller'))
LIMIT 6;
```

The two are not quite the same question: the second requires the opening employee to be *assigned to* the opening branch. Row-value comparisons like `(a, b) IN (subquery)` are supported by SQLite (3.15+), MySQL, PostgreSQL and Oracle, but not SQL Server (use EXISTS there).

A very common use is **"the row holding the group maximum"**:

```sql-run dataset=shop
-- The most expensive product(s) in each category
SELECT category_id, name, price
FROM products
WHERE (category_id, price) IN (SELECT category_id, MAX(price)
                               FROM products
                               GROUP BY category_id)
ORDER BY category_id;
```

Ties return several rows per group; window functions (later) give finer control.

## Subqueries in other statements

Subqueries are not limited to SELECT. They work in `INSERT ... SELECT`, in `UPDATE`'s SET and WHERE, and in `DELETE`'s WHERE:

```sql-run dataset=shop
DELETE FROM customer_imports
WHERE lower(trim(email)) IN (SELECT lower(email) FROM customers WHERE email IS NOT NULL);

SELECT COUNT(*) AS imports_not_already_customers FROM customer_imports;
```

## Subquery or join?

Many `IN` subqueries can be rewritten as joins, and optimizers often do exactly that (a *semi-join*). The difference that matters to you: a join can **multiply** rows if the joined table has several matches, whereas `IN` only ever keeps or drops the outer row. If you only need columns from one table and are merely *testing* against another, a subquery (`IN` / `EXISTS`) states your intent and avoids accidental duplicates.

```sql-run dataset=shop
SELECT (SELECT COUNT(*) FROM customers
        WHERE customer_id IN (SELECT customer_id FROM orders)) AS with_in,
       (SELECT COUNT(*) FROM customers c
        JOIN orders o ON o.customer_id = c.customer_id) AS with_join;
```

The join version counts order rows, not customers.

## Pitfalls

- **Scalar subquery returning several rows** — error elsewhere, silent first-row in SQLite.
- **`NOT IN` with NULLs** — returns nothing; filter NULLs or use `NOT EXISTS`.
- **`ANY`/`ALL` in SQLite** — not supported; use MIN/MAX rewrites.
- **Empty scalar subquery** — yields NULL and an empty outer result.
- **Join instead of IN** — can duplicate outer rows.

## Summary

- A subquery is a parenthesised query inside another statement; noncorrelated subqueries run once, independently.
- Scalar subqueries work with ordinary comparison operators and in expressions.
- Multi-row subqueries need `IN`, `NOT IN`, `ANY` or `ALL` (the last two rewritten with MIN/MAX in SQLite).
- Multicolumn subqueries compare row values: `(a, b) IN (SELECT x, y ...)`.
- Prefer subqueries for membership tests, joins when you need columns from both tables.

```quiz
[
  {"q": "What kind of subquery can be used with the = operator?", "options": ["Any subquery", "A scalar subquery (one row, one column)", "A multi-row subquery", "A multicolumn subquery"], "answer": 1, "explain": "A single value can only be equated to a single value."},
  {"q": "What does SQLite do when a subquery used with = returns three rows?", "options": ["Raises an error", "Uses the first row silently", "Compares with all three", "Returns NULL"], "answer": 1, "explain": "SQLite takes the first row; PostgreSQL and MySQL raise an error. Guarantee one row yourself."},
  {"q": "x > ALL (S) is equivalent (for non-empty S without NULLs) to...", "options": ["x > (SELECT MIN(v) FROM S)", "x > (SELECT MAX(v) FROM S)", "x IN (S)", "x NOT IN (S)"], "answer": 1, "explain": "Greater than every element means greater than the largest."},
  {"q": "= ANY (subquery) means the same as...", "options": ["NOT IN", "IN", "= ALL", "EXISTS always"], "answer": 1, "explain": "Equal to at least one element is membership."},
  {"q": "Why does emp_id NOT IN (SELECT superior_emp_id FROM employee) return no rows?", "options": ["Everyone is a manager", "The president's NULL superior makes every comparison UNKNOWN", "superior_emp_id is not indexed", "NOT IN needs a join"], "answer": 1, "explain": "A NULL in the list poisons NOT IN; filter it out or use NOT EXISTS."},
  {"q": "What does WHERE (category_id, price) IN (SELECT category_id, MAX(price) FROM products GROUP BY category_id) return?", "options": ["One product overall", "The most expensive product(s) of each category", "All products", "An error in SQLite"], "answer": 1, "explain": "Each row is matched against (category, max price) pairs; ties return several rows."},
  {"q": "Why might IN (subquery) be safer than a JOIN for a membership test?", "options": ["IN is always faster", "IN never duplicates outer rows", "JOIN cannot use indexes", "IN ignores NULLs in the outer table"], "answer": 1, "explain": "A join returns one row per match; IN only keeps or drops each outer row."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 9 "Subqueries" (what is a subquery, subquery types, noncorrelated subqueries, multiple-row single-column subqueries with IN/ALL/ANY, multicolumn subqueries).
