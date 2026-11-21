# Correlated subqueries, EXISTS and subqueries as data sources

> **Before this lesson:** you should know what a subquery is, the difference between a subquery that returns one value and one that returns a list, and why `NOT IN` fails when the list contains a NULL ([Noncorrelated subqueries](#/lesson/sql/noncorrelated)). Grouping with `GROUP BY` and `HAVING` is used throughout ([Aggregate functions and GROUP BY](#/lesson/sql/group-by)).

## In plain words

The subqueries in the last lesson were self-contained: the database could run each one once, on its own, and hand the answer to the outer query. Some questions do not work that way. "For each customer, how many accounts do *they* have?" needs a fresh answer for every customer. A subquery that mentions the row currently being examined by the outer query is called a **correlated subquery**. It cannot be run alone, because part of it is a blank that the outer query fills in, row by row.

An everyday picture: a teacher going down the class register. For each pupil she opens the homework folder and counts *that pupil's* submissions. The folder check is the same small task each time, but it depends on whose name she is on. That is a correlated subquery. (The earlier kind was like looking up one fact, such as today's date, before starting on the register at all.)

Often the teacher does not need a count, only a yes or no: "has this pupil handed in anything at all?" SQL has a keyword for exactly that question, `EXISTS`.

The second half of the lesson looks at where subqueries are useful in general: as a stand-in for a table, as a filter, and as a way to compute one extra column.

**Why it matters for a job.** `EXISTS` and `NOT EXISTS` are the safest way to ask "has a match" and "has no match", which are everyday questions (customers with no orders, products never sold). Correlated subqueries are also behind the classic "latest row per group" interview task. And interviewers like to ask how the same question can be written as a subquery, a join and a window function, which the last section answers.

## Correlated subqueries

Which customers have exactly two accounts?

```sql-run dataset=bank
SELECT c.cust_id, c.cust_type_cd, c.city
FROM customer c
WHERE 2 = (SELECT COUNT(*)
           FROM account a
           WHERE a.cust_id = c.cust_id);
```

Look inside the parentheses. The subquery counts rows of `account`, but its `WHERE` mentions `c.cust_id`, and `c` is the customer table of the *outer* query. That reference is the **correlation**.

Here is how to think about what happens:

1. The outer query takes the first customer, say customer 1.
2. The subquery is evaluated with `c.cust_id` replaced by 1: "count the accounts whose `cust_id` is 1". The answer is 2.
3. The outer `WHERE` checks `2 = 2`. True, so customer 1 is kept.
4. The same is repeated for customer 2, customer 3, and so on through all 40.

Twelve customers pass. If you copy the subquery out and try to run it by itself, you get an error: `c` is not defined there.

Any comparison can be used. Customers whose accounts hold between 5,000 and 10,000 in total:

```sql-run dataset=bank
SELECT c.cust_id, c.cust_type_cd, c.city
FROM customer c
WHERE (SELECT SUM(a.avail_balance)
       FROM account a
       WHERE a.cust_id = c.cust_id) BETWEEN 5000 AND 10000;
```

For each customer the subquery adds up that customer's balances, and the outer query keeps the customer if the sum lies in the range.

> [!NOTE]
> "Evaluated once per outer row" is the way to *reason* about a correlated subquery. The database is free to get the same answer more cleverly, and optimizers often turn such queries into joins. What you should take care of is an **index** (a lookup structure) on the column used for the correlation, here `account(cust_id)`. With it, each small lookup is fast. Without it, the database may read the whole inner table once for every outer row: a million customers times a million accounts.

A correlated subquery is the classic way to get **the latest row per group**:

```sql-run dataset=shop
SELECT o.customer_id, o.order_id, o.order_date
FROM orders o
WHERE o.order_date = (SELECT MAX(o2.order_date)
                      FROM orders o2
                      WHERE o2.customer_id = o.customer_id)
ORDER BY o.customer_id
LIMIT 8;
```

The same table appears twice with different aliases. Read it as: "keep this order (`o`) if its date equals the latest date among all orders (`o2`) of the same customer." Customer 1's most recent order is number 171, placed on 2024-07-26.

## The EXISTS operator

`EXISTS (subquery)` is true when the subquery returns **at least one row**. It does not care how many rows, or what is in them.

Which accounts had a transaction in the first three days of July 2024?

```sql-run dataset=bank
SELECT a.account_id, a.product_cd, a.cust_id, a.avail_balance
FROM account a
WHERE EXISTS (SELECT 1
              FROM txn t
              WHERE t.account_id = a.account_id
                AND t.txn_date >= '2024-07-01' AND t.txn_date < '2024-07-04');
```

For each account, the subquery looks for transactions of *that account* in the date range. If it finds any, `EXISTS` is true and the account is kept. Five accounts qualify.

Why `SELECT 1`? Because `EXISTS` only checks whether a row comes back, the contents of the `SELECT` list are irrelevant. Writing the constant `1` is the convention that signals "I only care that a row exists". The database can stop searching as soon as it finds the first match. Keeping the rows of one table that have a match in another, without adding columns or copies, is called a **semi-join**.

`NOT EXISTS` is true when the subquery returns **no rows**: it finds rows *without* a match. That is an **anti-join**. Accounts whose owner is not a business (no row for that customer in `business`):

```sql-run dataset=bank
SELECT a.account_id, a.product_cd, a.cust_id
FROM account a
WHERE NOT EXISTS (SELECT 1 FROM business b WHERE b.cust_id = a.cust_id)
LIMIT 6;
```

Training runs that recorded no measurements at all:

```sql-run dataset=mlops
SELECT r.run_id, r.run_name, r.status
FROM runs r
WHERE NOT EXISTS (SELECT 1 FROM metrics m WHERE m.run_id = r.run_id);
```

Eleven runs, every one with status `FAILED`, which makes sense: a run that crashed at the start measured nothing.

### EXISTS versus IN

| | `IN (subquery)` | `EXISTS (correlated subquery)` |
|---|---|---|
| What it does | compares a value with a list | tests whether any row comes back |
| Conditions it can express | equality on one column, or on a group of columns | anything: ranges, several columns, inequalities |
| NULL in the subquery's data | harmless for `IN`, **fatal for `NOT IN`** | no effect either way |

For the positive form, modern databases run both equally fast. For the negative form, prefer `NOT EXISTS`: a NULL cannot break it.

## Changing data with correlated subqueries

Correlated subqueries are common in `UPDATE` and `DELETE`. This block sets each account's `last_activity_date` to the date of its latest transaction, then shows a few rows. (Every Run starts from a fresh copy of the data.)

```sql-run dataset=bank
UPDATE account
SET last_activity_date = (SELECT MAX(date(t.txn_date))
                          FROM txn t
                          WHERE t.account_id = account.account_id)
WHERE EXISTS (SELECT 1 FROM txn t WHERE t.account_id = account.account_id);

SELECT account_id, last_activity_date FROM account LIMIT 5;
```

There are two correlated subqueries, and each refers to `account.account_id`, the row being updated. The first calculates the new value. The second, in `WHERE EXISTS`, limits the update to accounts that have transactions. It is not decoration. Without it, for an account with no transactions the first subquery would find nothing and return NULL, and the account's existing date would be **overwritten with NULL**.

A correlated `DELETE`: add a department with no employees, then remove every department that has none.

```sql-run dataset=bank
INSERT INTO department (name) VALUES ('Compliance');
DELETE FROM department
WHERE NOT EXISTS (SELECT 1 FROM employee e WHERE e.dept_id = department.dept_id);
SELECT * FROM department;
```

The three original departments remain; "Compliance" was created and deleted again.

> [!NOTE]
> Databases differ in the details here. MySQL restricts aliases on the table being deleted from, and for a long time did not allow a subquery to read the table being changed. PostgreSQL and SQL Server offer join forms (`UPDATE ... FROM`, `DELETE ... USING`) as alternatives.

## Where subqueries earn their place

### 1. As a data source

A subquery returns a table, so it can stand where a table stands, in `FROM` or after `JOIN`. There it is called a **derived table**. One restriction: a derived table must be **noncorrelated**. It is computed first and cannot look at the outer rows. (PostgreSQL and MySQL 8 lift this with the keyword `LATERAL`; SQL Server has `CROSS APPLY`.)

**Summarise, then join.**

```sql-run dataset=bank
SELECT d.dept_id, d.name, e_cnt.how_many AS num_employees
FROM department d
JOIN (SELECT dept_id, COUNT(*) AS how_many
      FROM employee
      GROUP BY dept_id) e_cnt
  ON d.dept_id = e_cnt.dept_id;
```

The derived table `e_cnt` holds one row per department with its head count; joining it to `department` adds the name. Operations has 15 employees, Loans 3.

**Making up data inside the query.** Sometimes the groups you want are not stored anywhere. Here three customer tiers, defined by balance range, are built on the spot and joined with a range condition:

```sql-run dataset=bank
SELECT grp.name AS tier, COUNT(*) AS num_customers
FROM (SELECT cust_id, SUM(avail_balance) AS cust_balance
      FROM account
      WHERE product_cd IN ('CHK', 'SAV', 'MM', 'CD')
      GROUP BY cust_id) cb
JOIN (SELECT 'Small Fry' AS name, 0 AS low_limit, 4999.99 AS high_limit
      UNION ALL SELECT 'Average Joes', 5000, 9999.99
      UNION ALL SELECT 'Heavy Hitters', 10000, 9999999.99) grp
  ON cb.cust_balance BETWEEN grp.low_limit AND grp.high_limit
GROUP BY grp.name;
```

Two derived tables. `cb` computes each customer's total deposits. `grp` is a three-row table of tiers made with `UNION ALL`. The join places each customer in the tier whose range contains their balance, and the outer query counts customers per tier: 13 "Average Joes", 11 "Heavy Hitters". If several queries need the tiers, they belong in a real table.

**Group on ids, look up names afterwards.** A report needs total deposits per product, branch and employee, with readable names. One way joins four tables and groups by three long name columns. A tidier way groups by the three short id columns in a subquery, then joins the small result to the other tables only to fetch names:

```sql-run dataset=bank
SELECT p.name AS product, b.name AS branch,
       e.fname || ' ' || e.lname AS teller,
       g.tot_deposits
FROM (SELECT product_cd, open_branch_id AS branch_id, open_emp_id AS emp_id,
             ROUND(SUM(avail_balance), 2) AS tot_deposits
      FROM account
      GROUP BY product_cd, open_branch_id, open_emp_id) g
JOIN employee e ON e.emp_id = g.emp_id
JOIN branch b   ON b.branch_id = g.branch_id
JOIN product p  ON p.product_cd = g.product_cd
WHERE p.product_type_cd = 'ACCOUNT'
ORDER BY g.tot_deposits DESC
LIMIT 8;
```

The query reads as two clear steps. Today the inner step is often written with `WITH g AS (...)` ([Common table expressions](#/lesson/sql/ctes)).

### 2. As a filter

Subqueries work in `HAVING` as well as in `WHERE`. Which employee opened the most accounts?

```sql-run dataset=bank
SELECT open_emp_id, COUNT(*) AS how_many
FROM account
GROUP BY open_emp_id
HAVING COUNT(*) = (SELECT MAX(cnt)
                   FROM (SELECT COUNT(*) AS cnt FROM account GROUP BY open_emp_id));
```

Read from the innermost part outward: count accounts per employee; take the largest of those counts; keep the group whose own count equals it. Employee 11, with 11 accounts.

### 3. As a calculated value

A subquery that returns one value can go anywhere a value can: the `SELECT` list, `ORDER BY`, the `VALUES` of an `INSERT`.

In the **`SELECT` list**, a correlated subquery looks something up for each row, as an alternative to a join:

```sql-run dataset=bank
SELECT a.account_id,
       (SELECT p.name FROM product p WHERE p.product_cd = a.product_cd)   AS product,
       (SELECT b.name FROM branch b WHERE b.branch_id = a.open_branch_id) AS branch,
       (SELECT COUNT(*) FROM txn t WHERE t.account_id = a.account_id)     AS txn_count
FROM account a
WHERE a.cust_id IN (1, 2);
```

The `txn_count` column shows the real advantage. It counts related rows **without changing the grain** of the outer query: still one row per account, no multiplied rows, no `GROUP BY`. An account with no transactions shows 0, where an inner join to `txn` would have left it out.

In **`ORDER BY`**, a subquery can sort by something that is not shown. Employees ordered by their manager's last name:

```sql-run dataset=bank
SELECT e.emp_id, e.fname || ' ' || e.lname AS name
FROM employee e
ORDER BY (SELECT boss.lname FROM employee boss WHERE boss.emp_id = e.superior_emp_id), e.lname
LIMIT 8;
```

The president comes first: he has no manager, the subquery returns NULL for him, and SQLite sorts NULL before everything else.

In an **`INSERT`**, subqueries find ids from human-readable values, so no id is typed by hand:

```sql
INSERT INTO account (product_cd, cust_id, open_date, status, open_branch_id, open_emp_id)
VALUES ('SAV',
        (SELECT cust_id FROM customer WHERE fed_id = '555-55-5555'),
        '2024-09-25', 'ACTIVE',
        (SELECT branch_id FROM branch WHERE name = 'Quincy Branch'),
        (SELECT emp_id FROM employee WHERE lname = 'Portman' AND fname = 'Frank'));
```

Take care: if a lookup finds nothing, NULL is inserted. Declaring such columns `NOT NULL` turns that silent mistake into an error.

## Subquery, join or window function? Choosing a form

One question can usually be written three ways. Take *each account's balance next to the average balance of its product*.

```sql-run dataset=bank
-- 1. Correlated subquery: the average is looked up for each row
SELECT a.account_id, a.product_cd, a.avail_balance,
       ROUND((SELECT AVG(a2.avail_balance) FROM account a2 WHERE a2.product_cd = a.product_cd), 2) AS product_avg
FROM account a
WHERE a.cust_id <= 3;
```

```sql-run dataset=bank
-- 2. Join to a derived table: every average is computed once
SELECT a.account_id, a.product_cd, a.avail_balance, ROUND(p.avg_bal, 2) AS product_avg
FROM account a
JOIN (SELECT product_cd, AVG(avail_balance) AS avg_bal FROM account GROUP BY product_cd) p
  ON p.product_cd = a.product_cd
WHERE a.cust_id <= 3;
```

```sql-run dataset=bank
-- 3. Window function: the table is mentioned only once
SELECT account_id, product_cd, avail_balance, product_avg
FROM (SELECT account_id, cust_id, product_cd, avail_balance,
             ROUND(AVG(avail_balance) OVER (PARTITION BY product_cd), 2) AS product_avg
      FROM account)
WHERE cust_id <= 3;
```

All three return the same nine rows; account 101, a checking account holding 3820.42, sits beside the checking average of 5645.34. The third uses a **window function**, which computes a value over a set of related rows while keeping every row ([Window basics and ranking](#/lesson/sql/ranking)).

| Situation | Prefer |
|---|---|
| A yes-or-no test against another table | `EXISTS` / `NOT EXISTS` |
| One looked-up value for a few outer rows, with an index on the correlation column | correlated subquery |
| The same per-group figure needed for many rows | join to a derived table, or a window function |
| A figure over the *same* table as the outer query | window function |
| Outer rows without a match must be kept | correlated subquery in `SELECT`, or `LEFT JOIN` |

A fine point in version 3: the filter `cust_id <= 3` had to move to an **outer** query. Inside, it would have been applied first, and the average would have been taken over those three customers' accounts only.

> [!INTERVIEW]
> "Find customers who have never placed an order." Write `NOT EXISTS` with a correlated subquery and say why you did not use `NOT IN`: a single NULL in the subquery's column would make `NOT IN` return nothing. Then mention the `LEFT JOIN ... WHERE right.key IS NULL` form as an equivalent. Offering two correct forms and one trap is a complete answer.

## Pitfalls

- **No index on the correlation column**: the inner table may be read once per outer row.
- **`UPDATE ... SET col = (correlated subquery)` without a guarding `WHERE`**: rows with no match are overwritten with NULL.
- **A subquery in the `SELECT` list that returns several rows**: an error on most databases, a silent first row in SQLite.
- **Trying to correlate a derived table** in `FROM`: not allowed without `LATERAL`.
- **Ties for the latest date**: `= (SELECT MAX(date) ...)` returns every tied row. Add a tie-breaker or use `ROW_NUMBER`.

## Summary

- A correlated subquery mentions the outer row and is, in effect, evaluated for each outer row.
- `EXISTS` and `NOT EXISTS` test whether matching rows are present or absent (semi-join and anti-join) and are unaffected by NULLs.
- Correlated subqueries drive `UPDATE` and `DELETE`; guard an `UPDATE` with `WHERE EXISTS`.
- Subqueries serve as data sources (derived tables for totals and made-up lookup data), as filters (in `WHERE` and `HAVING`) and as calculated values (in `SELECT`, `ORDER BY` and `INSERT`).
- The same question can often be a correlated subquery, a join to a derived table, or a window function; choose by clarity and by how many rows are involved.

## Glossary

- **Correlated subquery** — a subquery that refers to a column of the outer query and so depends on the current outer row.
- **Correlation** — the reference inside a subquery to the outer query's row.
- **`EXISTS`** — true when a subquery returns at least one row.
- **`NOT EXISTS`** — true when a subquery returns no rows.
- **Semi-join** — keeping rows of one table that have a match in another, without adding columns or copies.
- **Anti-join** — keeping rows of one table that have no match in another.
- **Derived table** — a subquery used in `FROM` in place of a table.
- **`LATERAL`** — a keyword (PostgreSQL, MySQL 8) that lets a subquery in `FROM` refer to earlier tables in the same `FROM`.
- **Latest row per group** — the task of picking, for each group, the row with the greatest date or value.
- **Window function** — a function that computes over a set of related rows while keeping each row.
- **Index** — a lookup structure that lets the database find rows by a column's value without reading the whole table.

```quiz
[
  {"q": "What makes a subquery correlated?", "options": ["It contains a join", "It refers to a column from the containing statement", "It returns several rows", "It appears in FROM"], "answer": 1, "explain": "The reference to the outer row means it cannot be run on its own."},
  {"q": "What does EXISTS (subquery) evaluate?", "options": ["Whether the subquery's first column is non-NULL", "Whether the subquery returns at least one row", "The number of rows returned", "Whether all rows match"], "answer": 1, "explain": "EXISTS only tests whether any row comes back; the SELECT list is irrelevant."},
  {"q": "Why add WHERE EXISTS (...) to an UPDATE that sets a column from a correlated subquery?", "options": ["For speed only", "To avoid setting the column to NULL for rows with no match", "The syntax requires it", "To lock fewer tables"], "answer": 1, "explain": "A subquery that finds no rows yields NULL, which would overwrite existing values."},
  {"q": "Which statement about subqueries in the FROM clause is true (without LATERAL)?", "options": ["They must be correlated", "They must be noncorrelated", "They can only return one row", "They cannot contain GROUP BY"], "answer": 1, "explain": "A derived table is computed before the outer query, so it cannot refer to the outer rows."},
  {"q": "A correlated subquery (SELECT COUNT(*) FROM txn t WHERE t.account_id = a.account_id) in the SELECT list returns what for an account with no transactions?", "options": ["NULL", "0", "The row is dropped", "An error"], "answer": 1, "explain": "COUNT over no rows is 0, and the outer row is kept, unlike with an inner join."},
  {"q": "Which is the NULL-safe way to find rows without a match?", "options": ["NOT IN (subquery)", "NOT EXISTS (correlated subquery)", "<> ALL (subquery)", "!= (subquery)"], "answer": 1, "explain": "NOT EXISTS is unaffected by NULLs in the subquery's data; NOT IN returns nothing if the list contains one."},
  {"q": "Which index most helps WHERE 2 = (SELECT COUNT(*) FROM account a WHERE a.cust_id = c.cust_id)?", "options": ["customer(city)", "account(cust_id)", "account(avail_balance)", "customer(cust_type_cd)"], "answer": 1, "explain": "The subquery looks up accounts by a.cust_id once per customer, so that is the column to index."},
  {"q": "WHERE o.order_date = (SELECT MAX(o2.order_date) FROM orders o2 WHERE o2.customer_id = o.customer_id) returns, for a customer with two orders on their latest date...", "options": ["One of them, chosen at random", "Both orders", "Neither order", "An error"], "answer": 1, "explain": "Every row whose date equals the maximum qualifies, so ties all come back."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 9 "Subqueries" (correlated subqueries, the exists operator, data manipulation using correlated subqueries, subqueries as data sources, in filter conditions and as expression generators), restated in original wording with this guide's own datasets.
