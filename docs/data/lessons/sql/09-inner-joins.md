# Inner joins

Normalization spreads facts across tables: an employee row holds a `dept_id`, not the department's name. To answer almost any real question you must bring the pieces back together. The mechanism is the **join**, and the most common kind is the **inner join**. This lesson builds the idea from the ground up — starting, as the book does, with what happens when you *don't* say how tables relate.

## What is a join?

Look at two tables:

```sql-run dataset=bank
SELECT emp_id, fname, lname, dept_id FROM employee LIMIT 5;
```

```sql-run dataset=bank
SELECT * FROM department;
```

`employee.dept_id` is a foreign key that points at `department.dept_id`. A join tells the server to use that column as the *transportation* between the tables, so that columns from both can appear in one result row.

## The Cartesian product

Start naively: name both tables and specify nothing else.

```sql-run dataset=bank
SELECT e.fname, e.lname, d.name
FROM employee e JOIN department d;
```

66 rows: 22 employees × 3 departments. Every employee is paired with every department. This is the **Cartesian product** (or **cross join**) — every permutation of the two tables. It is rarely what you want (the *Joins revisited* module shows the cases where it is), and on real tables it is catastrophic: a million rows × a million rows is 10¹² rows.

> [!NOTE]
> SQLite and MySQL accept `JOIN` without `ON` and produce a cross join. PostgreSQL and standard SQL require `ON` (or `USING`) for `JOIN`, and want you to write `CROSS JOIN` when you really mean a Cartesian product — a helpful safety net.

## Inner joins

To get one row per employee with the right department, add a **join condition** in an `ON` subclause:

```sql-run dataset=bank
SELECT e.fname, e.lname, d.name AS department
FROM employee e
JOIN department d ON e.dept_id = d.dept_id;
```

22 rows. Conceptually the server builds the Cartesian product and keeps only the pairs where `e.dept_id = d.dept_id`. (Physically it does something much smarter — a nested loop with an index lookup, a hash join, or a merge join.)

What if a value exists in one table but not the other? If an employee's `dept_id` were NULL, or pointed to a department that didn't exist, that employee would simply **not appear** in the result. That is the defining property of an inner join: **rows without a match on both sides are dropped**. If you want to keep them, you need an outer join (later module).

Check this with a real case. Not every customer is an individual:

```sql-run dataset=bank
SELECT (SELECT COUNT(*) FROM customer) AS all_customers,
       (SELECT COUNT(*) FROM customer c JOIN individual i ON i.cust_id = c.cust_id) AS joined_to_individual;
```

The 10 business customers have no row in `individual`, so the inner join drops them.

`JOIN` on its own means `INNER JOIN`; the book recommends writing `INNER JOIN` explicitly for clarity. This guide uses plain `JOIN` in most places, as most codebases do — know that they are identical.

### USING

When the join columns have the same name in both tables, `USING` is a shorthand:

```sql-run dataset=bank
SELECT e.fname, e.lname, d.name AS department
FROM employee e
JOIN department d USING (dept_id);
```

The book notes it and then sticks to `ON` to avoid confusion, since `USING` only works when the names match and hides which tables are involved.

## The ANSI join syntax

The `JOIN ... ON` notation was introduced by the SQL-92 standard. Before it — and still in a lot of legacy code — joins were written by listing tables with commas and putting join conditions in the WHERE clause:

```sql-run dataset=bank
-- Older syntax: join condition mixed in with filters
SELECT e.fname, e.lname, d.name AS department
FROM employee e, department d
WHERE e.dept_id = d.dept_id
  AND e.title = 'Teller';
```

It returns the same rows. The book gives three reasons to prefer the SQL-92 syntax:

1. **Join conditions and filter conditions are separated** (`ON` vs `WHERE`), making queries easier to read.
2. **The join condition for each pair of tables sits in its own `ON` clause**, so it is much harder to forget one — and a forgotten condition in the old syntax silently produces a Cartesian product.
3. **It is portable**; the old vendors' outer-join notations (`*=`, Oracle's `(+)`) were not.

```sql-run dataset=bank
-- SQL-92 syntax: structure visible at a glance
SELECT e.fname, e.lname, d.name AS department
FROM employee e
JOIN department d ON e.dept_id = d.dept_id
WHERE e.title = 'Teller';
```

## Join conditions versus filter conditions

For *inner* joins, the server treats conditions in `ON` and `WHERE` identically — these two queries return the same rows:

```sql-run dataset=bank
SELECT a.account_id, a.product_cd, c.fed_id
FROM account a
JOIN customer c ON a.cust_id = c.cust_id
WHERE c.cust_type_cd = 'B';
```

```sql-run dataset=bank
SELECT a.account_id, a.product_cd, c.fed_id
FROM account a
JOIN customer c ON a.cust_id = c.cust_id AND c.cust_type_cd = 'B';
```

The convention is still worth keeping: **how tables relate goes in ON; which rows you want goes in WHERE.** Besides readability there is a practical reason: with *outer* joins the placement changes the result, so building the right habit now pays off later.

## How many rows will a join return?

Before running a join, predict its row count — it is the best single habit for catching join bugs.

- **Many-to-one** (child → parent): joining `account` to `customer` on the customer's primary key returns exactly one row per account (provided every account has a customer). The row count stays at the "many" side.
- **One-to-many** (parent → child): joining `customer` to `account` returns one row per account, so customer columns are **repeated** — and any aggregate over customer columns is inflated.
- **Many-to-many through a duplicate key:** if neither side is unique on the join column, rows multiply — the **fan-out** trap.

```sql-run dataset=shop
SELECT (SELECT COUNT(*) FROM orders)       AS orders,
       (SELECT COUNT(*) FROM order_items)  AS order_items,
       (SELECT COUNT(*) FROM orders o JOIN order_items oi ON oi.order_id = o.order_id) AS joined;
```

The joined count equals the number of order items: the grain of the result is now *one row per line item*, and each order's `shipping_fee` appears once per item. Summing it would overcount:

```sql-run dataset=shop
SELECT (SELECT ROUND(SUM(shipping_fee), 2) FROM orders) AS true_shipping,
       ROUND(SUM(o.shipping_fee), 2) AS inflated_shipping
FROM orders o JOIN order_items oi ON oi.order_id = o.order_id;
```

> [!WARNING]
> **Know the grain.** After every join, be able to complete the sentence "each row of this result represents one ___". Aggregating a column from the "one" side after joining to the "many" side double-counts.

## How the engine executes a join

You don't choose the algorithm, but recognising them helps you read query plans:

| Algorithm | Idea | Good when |
|---|---|---|
| **Nested loop** | for each row of the outer table, look up matches in the inner (ideally by index) | small outer side, indexed inner side — OLTP lookups |
| **Hash join** | build a hash table on the smaller input, probe with the larger | large unsorted inputs, equality joins — analytics |
| **Merge join** | sort both inputs on the key (or read from indexes) and zip them | inputs already sorted |

SQLite only implements nested loops (with automatic temporary indexes when useful); PostgreSQL and MySQL 8 choose among all three.

```sql-run dataset=bank
EXPLAIN QUERY PLAN
SELECT a.account_id, c.city
FROM account a
JOIN customer c ON c.cust_id = a.cust_id;
```

`SCAN a` then `SEARCH c USING INTEGER PRIMARY KEY (rowid=?)`: for each account, one primary-key lookup.

## Does join order matter?

For inner joins, **no** — not to the result. `A JOIN B JOIN C` returns the same rows in any order, and the optimizer picks the order it estimates to be cheapest, using table statistics. The book stresses this: SQL is nonprocedural, so the order of tables in your FROM clause is not an instruction. (Hints such as MySQL's `STRAIGHT_JOIN` or SQL Server's `FORCE ORDER` exist for the rare cases where the optimizer gets it wrong.)

## Worked example: an ML question

*Which registered model versions came from which experiment, and with what model type?* That needs three hops — models → runs → experiments — but each hop is the same idea:

```sql-run dataset=mlops
SELECT m.name || ':v' || m.version AS model,
       m.stage,
       r.model_type,
       e.name AS experiment
FROM models m
JOIN runs r        ON r.run_id = m.run_id
JOIN experiments e ON e.experiment_id = r.experiment_id
WHERE m.stage IN ('Production', 'Staging')
ORDER BY m.name, m.version;
```

The next lesson looks at multi-table joins like this in detail.

## Pitfalls

- **Missing join condition** → Cartesian product. In the old comma syntax this is one forgotten line.
- **Ambiguous columns** — qualify every column once a query has two tables.
- **Unexpected row loss** — inner joins drop unmatched rows (NULL foreign keys, business customers without `individual` rows).
- **Fan-out double counting** — aggregate at the right grain or pre-aggregate before joining.
- **Joining on non-key columns** with duplicates multiplies rows.

## Summary

- A join combines rows from two tables using a condition, typically foreign key = primary key.
- With no condition you get the Cartesian product: every pair.
- An **inner join** keeps only pairs that satisfy the condition; unmatched rows vanish.
- Prefer SQL-92 `JOIN ... ON` over comma joins: conditions are separated, harder to forget, and portable.
- Predict row counts and know the grain of the result.
- Join order doesn't affect inner-join results; the optimizer chooses the physical order and algorithm.

```quiz
[
  {"q": "employee has 22 rows and department has 3. How many rows does FROM employee e JOIN department d (no ON) return in SQLite?", "options": ["22", "3", "25", "66"], "answer": 3, "explain": "Without a condition every employee pairs with every department: 22 x 3."},
  {"q": "What happens to an employee whose dept_id is NULL in an inner join to department?", "options": ["Appears with NULL department", "Is dropped from the result", "Causes an error", "Matches every department"], "answer": 1, "explain": "NULL = anything is UNKNOWN, so no pair qualifies and the row disappears."},
  {"q": "Which is NOT an advantage of the SQL-92 join syntax?", "options": ["Join and filter conditions are separated", "It makes joins execute in the written order", "It is portable across servers", "It is harder to forget a join condition"], "answer": 1, "explain": "The optimizer still chooses the join order."},
  {"q": "After joining orders to order_items, what does each row represent?", "options": ["One order", "One customer", "One order line item", "One product"], "answer": 2, "explain": "The grain becomes the 'many' side: line items."},
  {"q": "Why is SUM(o.shipping_fee) wrong after joining orders to order_items?", "options": ["shipping_fee is NULL", "Each order's fee is repeated once per item", "SUM cannot be used with joins", "It isn't wrong"], "answer": 1, "explain": "Fan-out repeats parent columns; aggregate before joining or use a subquery."},
  {"q": "JOIN without a qualifier means...", "options": ["LEFT JOIN", "INNER JOIN", "CROSS JOIN", "NATURAL JOIN"], "answer": 1, "explain": "INNER is the default join type."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 5 "Querying Multiple Tables" (what is a join, Cartesian product, inner joins, the ANSI join syntax, join conditions versus filter conditions).
