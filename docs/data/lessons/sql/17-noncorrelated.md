# Noncorrelated subqueries

> **Before this lesson:** you should be able to filter with `WHERE`, including `IN` with a list of values ([Building conditions](#/lesson/sql/conditions)), know why `NOT IN` and NULL do not mix ([NULL: the four-letter word](#/lesson/sql/null-logic)), join tables ([Inner joins](#/lesson/sql/inner-joins)) and use aggregates such as `MAX` and `AVG` with `GROUP BY` ([Aggregate functions and GROUP BY](#/lesson/sql/group-by)).

## In plain words

Some questions cannot be answered in one step. "Which account was opened most recently?" really contains two questions: *what is the latest opening date?* and then *which account has that date?* You could run the first query, read the date off the screen, and type it into the second. A **subquery** does that for you: it is a query written inside another query, in parentheses, whose answer is used by the query around it.

An everyday picture: a recipe that says "add the sauce (see page 40)". Page 40 is a small recipe of its own. You make the sauce first, then carry on with the main dish using the result. The main recipe does not care how the sauce was made, only what comes out of it.

What matters most about a subquery is the **shape** of what it returns: a single value, a list of values, or a table of several columns. The shape decides where you may use it. A single value can be compared with `=`; a list needs `IN`. Much of this lesson is about matching shape to operator.

This lesson covers subqueries that stand on their own: you could run them separately and get the same answer. They are called **noncorrelated**. The next lesson covers the other kind, which refer back to the query around them.

**Why it matters for a job.** "Find employees who earn more than the average", "customers who ordered this year", "the most expensive product in each category": these are staple interview tasks and each one is a subquery. In daily work, subqueries let a query stay correct as the data changes, because nothing is typed in by hand.

## A first subquery, read step by step

Find the most recently opened account.

```sql-run dataset=bank
SELECT account_id, product_cd, cust_id, open_date
FROM account
WHERE open_date = (SELECT MAX(open_date) FROM account);
```

Read it from the inside out:

- The part in parentheses, `SELECT MAX(open_date) FROM account`, is the subquery. It returns one value: the latest opening date in the table.
- The outer query, called the **containing statement**, then reads `WHERE open_date = <that value>` and returns the account or accounts opened on that date.

One row comes back: account 140, opened on 2023-12-16. To see what the subquery contributes, run it alone:

```sql-run dataset=bank
SELECT MAX(open_date) FROM account;
```

It returns `2023-12-16`. Being able to run it separately is exactly what makes a subquery *noncorrelated*. The database treats its result as a small temporary table that exists only while the whole statement runs.

Why not run two queries by hand and paste the date? Because the pasted date is wrong as soon as a newer account is opened. The subquery is recalculated every time.

## The kinds of subquery

Subqueries are classified in two ways.

**By the shape of the result:**

| Shape | Returns | Can be used with |
|---|---|---|
| **Scalar** | one row with one column, that is, a single value | `=`, `<>`, `<`, `>`, arithmetic, the `SELECT` list: anywhere a value is allowed |
| **Multiple-row, single-column** | a list of values | `IN`, `NOT IN`, `ANY`, `ALL` |
| **Multicolumn** | rows with several columns | a comparison of several columns at once, or as a table in `FROM` |

"Scalar" is the mathematical word for a single value, as opposed to a list.

**By whether it depends on the containing statement:**

- **Noncorrelated**: complete in itself; run once, before the outer query.
- **Correlated**: mentions columns of the outer query, so it must be worked out again for each outer row (next lesson).

## Scalar subqueries

A scalar subquery can be as elaborate as needed (joins, filters, aggregates) provided it yields one row and one column. Here it finds the head teller of the Woburn branch, and the outer query lists accounts *not* opened by that person:

```sql-run dataset=bank
SELECT account_id, product_cd, cust_id, avail_balance
FROM account
WHERE open_emp_id <> (SELECT e.emp_id
                      FROM employee e
                      JOIN branch b ON e.assigned_branch_id = b.branch_id
                      WHERE e.title = 'Head Teller' AND b.city = 'Woburn')
LIMIT 8;
```

The subquery joins `employee` to `branch` and returns a single employee id. The outer `<>` ("not equal") then compares each account's opener with that one id.

**What if the subquery returns more than one row?** A single value cannot be compared with a list using `<>` or `=`. PostgreSQL, MySQL and SQL Server stop with an error such as "subquery returns more than 1 row".

> [!WARNING]
> **SQLite does not raise this error.** If a subquery used as a single value returns several rows, SQLite quietly uses the **first** one. A logic mistake is therefore invisible in this page and a crash on another database. When you mean a single value, guarantee one row: use an aggregate (`MAX`, `MIN`), filter on a unique key, or add `ORDER BY ... LIMIT 1`.

```sql-run dataset=bank
-- Runs in SQLite, fails in PostgreSQL/MySQL: the subquery returns 4 rows
SELECT COUNT(*) AS misleading
FROM account
WHERE open_emp_id <> (SELECT e.emp_id
                      FROM employee e
                      JOIN branch b ON e.assigned_branch_id = b.branch_id
                      WHERE b.city = 'Woburn');
```

Without the title filter the subquery returns four Woburn employees. SQLite compares with the first only and reports 76, a number that answers no sensible question.

**What if it returns no row at all?** Then its value is NULL on every database. A comparison with NULL is never true, so the outer query returns nothing.

Scalar subqueries are ideal for "compare with an overall figure":

```sql-run dataset=shop
SELECT name, price,
       ROUND(price - (SELECT AVG(price) FROM products), 2) AS diff_from_avg
FROM products
WHERE price > 2 * (SELECT AVG(price) FROM products)
ORDER BY price DESC;
```

The same subquery appears twice: once in the `SELECT` list, to show how far each price is from the average, and once in `WHERE`, to keep only products costing more than double the average. Four products qualify; the dearest, at 1799.00, is 1583.05 above the average.

## Subqueries that return a list

When a subquery returns several rows of one column, four operators accept it.

### IN and NOT IN

`IN` asks "is this value on the list?". Which employees supervise someone?

```sql-run dataset=bank
SELECT emp_id, fname, lname, title
FROM employee
WHERE emp_id IN (SELECT superior_emp_id FROM employee);
```

The subquery lists the `superior_emp_id` of every employee, which is the id of everybody's boss. An employee whose own id is on that list is a supervisor. Nine rows come back, starting with the president.

The opposite question, "who supervises nobody?", suggests `NOT IN`. But the list contains a NULL: the president has no superior. As the NULL lesson showed, `x NOT IN (list containing NULL)` is never true, so the query would return nothing at all. The NULL must be removed from the list:

```sql-run dataset=bank
SELECT emp_id, fname, lname, title
FROM employee
WHERE emp_id NOT IN (SELECT superior_emp_id
                     FROM employee
                     WHERE superior_emp_id IS NOT NULL);
```

Thirteen employees, and 9 + 13 = 22, the whole staff. Delete the `WHERE superior_emp_id IS NOT NULL` line and run it again to watch the result vanish.

`IN` with a subquery replaces a hand-typed list with one that maintains itself:

```sql-run dataset=mlops
-- Runs belonging to experiments owned by the risk team
SELECT run_id, run_name, status
FROM runs
WHERE experiment_id IN (SELECT experiment_id FROM experiments WHERE team = 'risk')
LIMIT 8;
```

When the risk team starts a new experiment, its runs appear without anyone editing the query.

### ALL

`ALL` compares a value with **every** value on a list and is true only if the comparison holds for all of them. In standard SQL, "accounts with a balance smaller than all of customer 31's accounts" is:

```sql
-- MySQL, PostgreSQL, Oracle, SQL Server
... WHERE avail_balance < ALL (SELECT avail_balance FROM account WHERE cust_id = 31)
```

Smaller than every one of them is the same as smaller than the smallest, so the query can be written with `MIN`, which also works in SQLite:

```sql-run dataset=bank
SELECT account_id, cust_id, product_cd, avail_balance
FROM account
WHERE status = 'ACTIVE'
  AND avail_balance < (SELECT MIN(avail_balance) FROM account WHERE cust_id = 31)
ORDER BY avail_balance DESC
LIMIT 6;
```

Likewise `> ALL (list)` means "greater than the largest". `<> ALL (list)` is the same as `NOT IN`, with the same NULL problem.

### ANY

`ANY` (also spelled `SOME`) is true if the comparison holds for **at least one** value on the list. `> ANY (list)` means "greater than the smallest"; `= ANY (list)` is exactly `IN`.

> [!NOTE]
> **SQLite does not have `ANY`, `ALL` or `SOME`.** MySQL, PostgreSQL, Oracle and SQL Server do. The rewrites work everywhere and are arguably clearer:
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
> One fine point: when the list is **empty**, `x > ALL (S)` is true (there is nothing to fail against), while `x > (SELECT MAX ...)` compares with NULL and is not true.

Accounts of other customers whose balance is greater than *at least one* of customer 31's accounts, using the rewrite:

```sql-run dataset=bank
SELECT account_id, cust_id, product_cd, avail_balance
FROM account
WHERE avail_balance > (SELECT MIN(avail_balance) FROM account WHERE cust_id = 31)
  AND cust_id <> 31
ORDER BY avail_balance
LIMIT 6;
```

## Subqueries that return several columns

Sometimes a match involves two columns at once. Accounts opened at the Woburn branch by a teller can be written with two single-column subqueries:

```sql-run dataset=bank
SELECT account_id, product_cd, cust_id
FROM account
WHERE open_branch_id = (SELECT branch_id FROM branch WHERE name = 'Woburn Branch')
  AND open_emp_id IN (SELECT emp_id FROM employee WHERE title IN ('Teller', 'Head Teller'))
LIMIT 6;
```

Or with one subquery that returns (branch, employee) **pairs**, compared against a pair of columns written in parentheses:

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

`(open_branch_id, open_emp_id) IN (...)` is true when the account's pair of values equals one of the pairs the subquery returns. The two versions ask slightly different questions: the second also requires the opening employee to be *assigned to* the opening branch. Comparisons of several columns at once work in SQLite, MySQL, PostgreSQL and Oracle, but not in SQL Server.

A very common use is **"the row that holds the maximum of its group"**:

```sql-run dataset=shop
-- The most expensive product(s) in each category
SELECT category_id, name, price
FROM products
WHERE (category_id, price) IN (SELECT category_id, MAX(price)
                               FROM products
                               GROUP BY category_id)
ORDER BY category_id;
```

The subquery returns one (category, highest price) pair per category. A product is kept when its own category and price equal one of those pairs. If two products tie for the top price in a category, both are returned. Window functions give finer control over ties ([Window basics and ranking](#/lesson/sql/ranking)).

## Subqueries in statements that change data

Subqueries are not limited to `SELECT`. They work in `INSERT ... SELECT`, in the `SET` and `WHERE` parts of `UPDATE`, and in the `WHERE` of `DELETE`. This block deletes imported sign-ups whose email already belongs to a customer, then counts what is left. (Each Run starts from a fresh copy of the data, so nothing is lost.)

```sql-run dataset=shop
DELETE FROM customer_imports
WHERE lower(trim(email)) IN (SELECT lower(email) FROM customers WHERE email IS NOT NULL);

SELECT COUNT(*) AS imports_not_already_customers FROM customer_imports;
```

Of the 50 imported rows, 2 are left.

## Subquery or join?

Many `IN` subqueries can be rewritten as joins, and optimizers often do so internally. The difference that matters to you: a join returns one row **per match**, so it can multiply rows; `IN` only keeps or drops each outer row. If you need columns from one table and are only *testing* against another, a subquery says what you mean and cannot create duplicates.

```sql-run dataset=shop
SELECT (SELECT COUNT(*) FROM customers
        WHERE customer_id IN (SELECT customer_id FROM orders)) AS with_in,
       (SELECT COUNT(*) FROM customers c
        JOIN orders o ON o.customer_id = c.customer_id) AS with_join;
```

74 with `IN`: the number of customers who have ordered. 249 with the join: the number of *orders*, because a customer with five orders appears five times.

## Worked example: four shapes on one dataset

The `mlops` dataset records training runs and the models registered from them. Four related questions, one for each shape.

**A single value.** *Which finished runs took longer than the average finished run?* The duration is the difference of two Julian day numbers ([Dates, times and conversion](#/lesson/sql/dates-conversion)).

```sql-run dataset=mlops
SELECT run_id, run_name,
       ROUND((julianday(ended_at) - julianday(started_at)) * 24, 2) AS hours
FROM runs
WHERE status = 'FINISHED'
  AND (julianday(ended_at) - julianday(started_at)) >
      (SELECT AVG(julianday(ended_at) - julianday(started_at)) FROM runs WHERE status = 'FINISHED')
ORDER BY hours DESC
LIMIT 5;
```

**A list.** *Which runs produced a model now in Production?*

```sql-run dataset=mlops
SELECT run_id, run_name, model_type
FROM runs
WHERE run_id IN (SELECT run_id FROM models WHERE stage = 'Production');
```

**A list with a negation.** *How many finished runs were never registered as a model?* `NOT IN` is safe here only because `models.run_id` is declared `NOT NULL`, so the list cannot contain a NULL. Say so when you write it.

```sql-run dataset=mlops
SELECT COUNT(*) AS finished_but_unregistered
FROM runs
WHERE status = 'FINISHED'
  AND run_id NOT IN (SELECT run_id FROM models);
```

**Several columns.** *For each experiment, the finished run that took longest.* The pair (experiment, duration) is matched against the longest duration per experiment:

```sql-run dataset=mlops
SELECT experiment_id, run_id, run_name,
       ROUND((julianday(ended_at) - julianday(started_at)) * 24, 2) AS hours
FROM runs
WHERE status = 'FINISHED'
  AND (experiment_id, julianday(ended_at) - julianday(started_at)) IN
      (SELECT experiment_id, MAX(julianday(ended_at) - julianday(started_at))
       FROM runs WHERE status = 'FINISHED'
       GROUP BY experiment_id)
ORDER BY experiment_id;
```

Eight rows, one per experiment.

A useful way to debug any of these: **run the inner query by itself first.** If it returns the number or list you expect, the mistake is in the outer comparison. If not, you have found it without reading the whole statement.

> [!INTERVIEW]
> "Employees earning more than the company average" (single value), "customers who placed an order in 2024" (`IN` or `EXISTS`), "the highest-paid employee in each department" (several columns with a grouped subquery, or a window function): these three cover most subquery questions at screening level. For each, name the shape of the subquery before you write it.

## Pitfalls

- **A subquery meant as one value that returns several rows**: an error elsewhere, a silent first row in SQLite.
- **`NOT IN` with a NULL on the list**: returns nothing. Filter NULLs out or use `NOT EXISTS`.
- **`ANY` and `ALL` in SQLite**: not available; use the `MIN` and `MAX` rewrites.
- **A single-value subquery that finds no row**: gives NULL, and the outer query returns nothing.
- **A join where a membership test was meant**: outer rows are repeated once per match.

## Summary

- A subquery is a query in parentheses inside another statement; a noncorrelated one runs once, independently.
- A scalar subquery (one value) works with ordinary comparisons and inside calculations.
- A subquery returning a list needs `IN`, `NOT IN`, `ANY` or `ALL` (the last two rewritten with `MIN` and `MAX` in SQLite).
- A multicolumn subquery is compared with a pair of columns: `(a, b) IN (SELECT x, y ...)`.
- Prefer a subquery for membership tests and a join when you need columns from both tables.

## Glossary

- **Subquery** — a query written in parentheses inside another SQL statement.
- **Containing statement (outer query)** — the statement that holds a subquery and uses its result.
- **Scalar subquery** — a subquery that returns a single value: one row, one column.
- **Multiple-row subquery** — a subquery that returns a list of values in one column.
- **Multicolumn subquery** — a subquery that returns rows of several columns.
- **Noncorrelated subquery** — a subquery that does not refer to the outer query and can be run alone.
- **Correlated subquery** — a subquery that refers to columns of the outer query.
- **`IN` / `NOT IN`** — tests whether a value is, or is not, on a list.
- **`ALL`** — makes a comparison that must hold for every value on a list.
- **`ANY` (`SOME`)** — makes a comparison that must hold for at least one value on a list.
- **Row-value comparison** — comparing several columns at once, as in `(a, b) IN (...)`.
- **Membership test** — checking whether a matching row exists elsewhere without fetching its columns.

```quiz
[
  {"q": "What kind of subquery can be used with the = operator?", "options": ["Any subquery", "A scalar subquery (one row, one column)", "A multi-row subquery", "A multicolumn subquery"], "answer": 1, "explain": "A single value can only be set equal to a single value."},
  {"q": "What does SQLite do when a subquery used with = returns three rows?", "options": ["Raises an error", "Uses the first row silently", "Compares with all three", "Returns NULL"], "answer": 1, "explain": "SQLite takes the first row; PostgreSQL and MySQL raise an error. Guarantee one row yourself."},
  {"q": "x > ALL (S) is equivalent, for a non-empty S without NULLs, to...", "options": ["x > (SELECT MIN(v) FROM S)", "x > (SELECT MAX(v) FROM S)", "x IN (S)", "x NOT IN (S)"], "answer": 1, "explain": "Greater than every element means greater than the largest."},
  {"q": "= ANY (subquery) means the same as...", "options": ["NOT IN", "IN", "= ALL", "EXISTS in every case"], "answer": 1, "explain": "Equal to at least one element is membership of the list."},
  {"q": "Why does emp_id NOT IN (SELECT superior_emp_id FROM employee) return no rows?", "options": ["Everyone is a manager", "The president's NULL superior makes every NOT IN test unknown", "superior_emp_id is not indexed", "NOT IN needs a join"], "answer": 1, "explain": "A NULL on the list means NOT IN can never be true; filter it out or use NOT EXISTS."},
  {"q": "What does WHERE (category_id, price) IN (SELECT category_id, MAX(price) FROM products GROUP BY category_id) return?", "options": ["One product overall", "The most expensive product(s) of each category", "All products", "An error in SQLite"], "answer": 1, "explain": "Each product's pair is matched against the (category, highest price) pairs; ties return several rows."},
  {"q": "Why might IN (subquery) be safer than a JOIN for a membership test?", "options": ["IN is always faster", "IN never repeats outer rows", "JOIN cannot use indexes", "IN ignores NULLs in the outer table"], "answer": 1, "explain": "A join returns one row per match; IN only keeps or drops each outer row."},
  {"q": "What makes a subquery noncorrelated?", "options": ["It returns one value", "It does not refer to the outer query, so it can be run on its own", "It is written in the FROM clause", "It uses no aggregate"], "answer": 1, "explain": "A noncorrelated subquery is self-contained and is run once, before the outer query."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 9 "Subqueries" (what a subquery is, subquery types, noncorrelated subqueries, multiple-row single-column subqueries with IN, ALL and ANY, multicolumn subqueries), restated in original wording with this guide's own datasets.
