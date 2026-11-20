# Correlated subqueries, EXISTS and subqueries as data sources

Noncorrelated subqueries run once and hand a result to the containing statement. A **correlated subquery** is different: it refers to one or more columns of the containing statement, so it has no meaning on its own and is — conceptually — executed once for every candidate row. That makes it the natural way to ask "for each row, look something up about *this* row". This lesson covers correlated subqueries, the `EXISTS` operator, data manipulation with correlated subqueries, and then the three places the book says subqueries earn their keep: as **data sources**, in **filter conditions**, and as **expression generators**.

## Correlated subqueries

Count each customer's accounts, and keep customers with exactly two:

```sql-run dataset=bank
SELECT c.cust_id, c.cust_type_cd, c.city
FROM customer c
WHERE 2 = (SELECT COUNT(*)
           FROM account a
           WHERE a.cust_id = c.cust_id);
```

The reference to `c.cust_id` inside the subquery is the **correlation**. The outer query retrieves the 40 customer rows; for each one, the subquery is evaluated with that customer's id plugged in, and the row is kept if the count equals 2. You cannot run the subquery alone — `c` is not defined there.

Correlated subqueries can use any comparison. The book's next example uses a range: customers whose total available balance lies between \$5,000 and \$10,000.

```sql-run dataset=bank
SELECT c.cust_id, c.cust_type_cd, c.city
FROM customer c
WHERE (SELECT SUM(a.avail_balance)
       FROM account a
       WHERE a.cust_id = c.cust_id) BETWEEN 5000 AND 10000;
```

> [!NOTE]
> "Executed once per row" is the *logical* model. Optimizers frequently **decorrelate** such queries into joins or semi-joins, and with an index on the correlation column (`account(cust_id)`) even the naive strategy is cheap. Without that index, a correlated subquery over large tables is an O(n × m) trap.

A correlated subquery is also a classic way to get *the latest row per group*:

```sql-run dataset=shop
SELECT o.customer_id, o.order_id, o.order_date
FROM orders o
WHERE o.order_date = (SELECT MAX(o2.order_date)
                      FROM orders o2
                      WHERE o2.customer_id = o.customer_id)
ORDER BY o.customer_id
LIMIT 8;
```

"Keep this order if its date is the maximum date among orders of the same customer."

## The EXISTS operator

The most common operator used with correlated subqueries is `EXISTS`. It asks only whether the subquery returns **at least one row** — it does not care how many, or what they contain.

Accounts that had a transaction on a particular day:

```sql-run dataset=bank
SELECT a.account_id, a.product_cd, a.cust_id, a.avail_balance
FROM account a
WHERE EXISTS (SELECT 1
              FROM txn t
              WHERE t.account_id = a.account_id
                AND t.txn_date >= '2024-07-01' AND t.txn_date < '2024-07-04');
```

Because EXISTS ignores the subquery's select list, the convention is `SELECT 1` (the book notes that `SELECT *` or anything else works equally well). The engine can stop at the first matching row — a **semi-join**.

`NOT EXISTS` finds rows *without* a match — an **anti-join**. Customers who are not businesses (no row in `business`):

```sql-run dataset=bank
SELECT a.account_id, a.product_cd, a.cust_id
FROM account a
WHERE NOT EXISTS (SELECT 1 FROM business b WHERE b.cust_id = a.cust_id)
LIMIT 6;
```

Runs that logged no metrics at all:

```sql-run dataset=mlops
SELECT r.run_id, r.run_name, r.status
FROM runs r
WHERE NOT EXISTS (SELECT 1 FROM metrics m WHERE m.run_id = r.run_id);
```

(Unsurprisingly, those are the FAILED runs.)

### EXISTS versus IN

| | `IN (subquery)` | `EXISTS (correlated subquery)` |
|---|---|---|
| Compares | a value with a list | nothing — tests for any row |
| Conditions | one column (or a row value) | anything: ranges, several columns, inequalities |
| NULL in subquery | harmless for IN, **fatal for NOT IN** | no problem either way |
| Typical plan | semi-join | semi-join |

Positive forms perform the same on modern optimizers. For the negative form, prefer `NOT EXISTS`: it is NULL-safe and usually planned as an efficient anti-join.

## Data manipulation using correlated subqueries

Correlated subqueries appear constantly in UPDATE and DELETE. The book refreshes every account's `last_activity_date` from its latest transaction:

```sql-run dataset=bank
UPDATE account
SET last_activity_date = (SELECT MAX(date(t.txn_date))
                          FROM txn t
                          WHERE t.account_id = account.account_id)
WHERE EXISTS (SELECT 1 FROM txn t WHERE t.account_id = account.account_id);

SELECT account_id, last_activity_date FROM account LIMIT 5;
```

The `WHERE EXISTS` is not decoration. Without it, accounts with no transactions would have the subquery return NULL and their date would be **overwritten with NULL**. The second subquery protects them.

And a correlated DELETE — remove departments that have no employees:

```sql-run dataset=bank
INSERT INTO department (name) VALUES ('Compliance');
DELETE FROM department
WHERE NOT EXISTS (SELECT 1 FROM employee e WHERE e.dept_id = department.dept_id);
SELECT * FROM department;
```

> [!NOTE]
> MySQL does not allow a table alias on the target of a `DELETE` when using a correlated subquery in the form shown in the book, and historically forbade selecting from the table being modified in a subquery. PostgreSQL and SQL Server offer `UPDATE ... FROM` / `DELETE ... USING` join syntax as an alternative.

## When to use subqueries

### Subqueries as data sources

Since a subquery returns a table, it can sit in the FROM clause as a **derived table**. The key restriction: a subquery in FROM must be **noncorrelated** — it is executed first and stays in memory for the duration of the query. (The exception is `LATERAL` in PostgreSQL/MySQL 8 and `CROSS APPLY` in SQL Server, which allow correlation in FROM.)

**Summarise, then join.** Pre-aggregate one table and join the summary to others:

```sql-run dataset=bank
SELECT d.dept_id, d.name, e_cnt.how_many AS num_employees
FROM department d
JOIN (SELECT dept_id, COUNT(*) AS how_many
      FROM employee
      GROUP BY dept_id) e_cnt
  ON d.dept_id = e_cnt.dept_id;
```

**Data fabrication.** Sometimes the grouping you want does not exist in the database. The book defines customer groups by balance range *inside the query* and joins to them with a range condition:

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

Two derived tables: one computes each customer's deposit balance; the other fabricates the three tiers. Whether tiers *should* live in a real table is a design question — if several queries need them, yes.

**Task-oriented subqueries.** A report needs total deposit balances by product, branch and teller, with readable names. You could join five tables and group by all the name columns. The book's cleaner approach: do the grouping on the *ids* in a subquery, then join the small result to the lookup tables just for the names:

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

The grouping now involves three compact columns instead of long strings, and the query reads as two clear steps. Today most people would write the inner step as a CTE (`WITH g AS (...)`), covered in its own module.

### Subqueries in filter conditions

Subqueries are not limited to WHERE; they are just as useful in **HAVING**. Which teller opened the most accounts?

```sql-run dataset=bank
SELECT open_emp_id, COUNT(*) AS how_many
FROM account
GROUP BY open_emp_id
HAVING COUNT(*) = (SELECT MAX(cnt)
                   FROM (SELECT COUNT(*) AS cnt FROM account GROUP BY open_emp_id));
```

The innermost query counts accounts per employee, the middle one takes the maximum count, and HAVING keeps the group(s) matching it. (Standard SQL writes this as `>= ALL (SELECT COUNT(*) ...)`.)

### Subqueries as expression generators

Scalar subqueries can go anywhere an expression can: the select list, ORDER BY, even the VALUES of an INSERT.

In the **select list**, a correlated scalar subquery performs a lookup per row — an alternative to a join:

```sql-run dataset=bank
SELECT a.account_id,
       (SELECT p.name FROM product p WHERE p.product_cd = a.product_cd)   AS product,
       (SELECT b.name FROM branch b WHERE b.branch_id = a.open_branch_id) AS branch,
       (SELECT COUNT(*) FROM txn t WHERE t.account_id = a.account_id)     AS txn_count
FROM account a
WHERE a.cust_id IN (1, 2);
```

The `txn_count` column shows the real advantage: it counts child rows **without changing the grain** of the outer query, so there is no fan-out and no GROUP BY. An account with no transactions shows 0, where an inner join would have dropped it.

In **ORDER BY**, a subquery can sort by something not selected — employees ordered by their boss's last name:

```sql-run dataset=bank
SELECT e.emp_id, e.fname || ' ' || e.lname AS name
FROM employee e
ORDER BY (SELECT boss.lname FROM employee boss WHERE boss.emp_id = e.superior_emp_id), e.lname
LIMIT 8;
```

In an **INSERT**, subqueries look up foreign keys from natural keys, so the statement needs no hard-coded ids:

```sql
INSERT INTO account (product_cd, cust_id, open_date, status, open_branch_id, open_emp_id)
VALUES ('SAV',
        (SELECT cust_id FROM customer WHERE fed_id = '555-55-5555'),
        '2024-09-25', 'ACTIVE',
        (SELECT branch_id FROM branch WHERE name = 'Quincy Branch'),
        (SELECT emp_id FROM employee WHERE lname = 'Portman' AND fname = 'Frank'));
```

Beware: if a lookup finds nothing, NULL is inserted — which is why such columns should be `NOT NULL`.

## Subquery wrap-up

The book closes the chapter with a summary worth repeating. Subqueries:

- return a single value, a single column of rows, or multiple columns and rows;
- are independent of the containing statement (noncorrelated) or reference its columns (correlated);
- are used in conditions with comparison operators and with `IN`, `NOT IN`, `EXISTS`, `NOT EXISTS` (and `ANY`/`ALL`);
- can be found in SELECT, UPDATE, DELETE and INSERT statements;
- can serve as tables in FROM, as conditions in WHERE and HAVING, and as expressions in SELECT, ORDER BY and VALUES.

## Pitfalls

- **Correlated subquery without an index** on the correlation column — quadratic work.
- **UPDATE … SET col = (correlated subquery)** without a guarding WHERE — overwrites non-matching rows with NULL.
- **Scalar subquery in SELECT returning several rows** — error (or silent first row in SQLite).
- **Trying to correlate a derived table** in FROM — not allowed without LATERAL.
- **`MAX(date)` per group returning ties** — add a tie-breaker or use ROW_NUMBER.

## Correlated subquery, join or window? Choosing a form

The same question can usually be written three ways. Take *each account's balance compared with the average balance of its product*.

```sql-run dataset=bank
-- 1. Correlated scalar subquery: the average is looked up per row
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
-- 3. Window function: no second reference to the table at all
SELECT account_id, product_cd, avail_balance, product_avg
FROM (SELECT account_id, cust_id, product_cd, avail_balance,
             ROUND(AVG(avail_balance) OVER (PARTITION BY product_cd), 2) AS product_avg
      FROM account)
WHERE cust_id <= 3;
```

All three return the same rows. Rules of thumb for choosing:

| Situation | Prefer |
|---|---|
| A yes/no test against another table | `EXISTS` / `NOT EXISTS` |
| One looked-up value for a handful of outer rows, with an index on the correlation column | correlated scalar subquery |
| The same per-group statistic needed for many rows | derived table join, or a window function |
| Statistic over the *same* table as the outer query | window function |
| Need to keep outer rows that have no match | correlated subquery in SELECT, or LEFT JOIN |

Note the subtle point in version 3: the filter `cust_id <= 3` had to move to an **outer** query. Had it been inside, the average would have been computed over those three customers' accounts only — windows see the rows that survive WHERE.

## Summary

- Correlated subqueries reference the outer row and are logically evaluated per row.
- `EXISTS` / `NOT EXISTS` test for the presence or absence of matching rows — semi-join and anti-join — and are NULL-safe.
- Correlated subqueries drive UPDATEs and DELETEs; guard UPDATEs with `WHERE EXISTS`.
- Subqueries serve as data sources (derived tables: pre-aggregation, fabricated lookup data), filters (WHERE and HAVING) and expression generators (SELECT, ORDER BY, INSERT values).

```quiz
[
  {"q": "What makes a subquery correlated?", "options": ["It contains a join", "It references a column from the containing statement", "It returns several rows", "It appears in FROM"], "answer": 1, "explain": "The reference to the outer row means it cannot run on its own."},
  {"q": "What does EXISTS (subquery) evaluate?", "options": ["Whether the subquery's first column is non-NULL", "Whether the subquery returns at least one row", "The number of rows returned", "Whether all rows match"], "answer": 1, "explain": "EXISTS only tests for the presence of any row; the select list is irrelevant."},
  {"q": "Why add WHERE EXISTS (...) to an UPDATE that sets a column from a correlated subquery?", "options": ["For speed only", "To avoid setting the column to NULL for rows with no match", "It is required syntax", "To lock fewer tables"], "answer": 1, "explain": "A subquery with no rows yields NULL, which would overwrite existing values."},
  {"q": "Which statement about subqueries in the FROM clause is true (without LATERAL)?", "options": ["They must be correlated", "They must be noncorrelated", "They can only return one row", "They cannot contain GROUP BY"], "answer": 1, "explain": "Derived tables are evaluated before the outer query, so they cannot reference its rows."},
  {"q": "A correlated scalar subquery (SELECT COUNT(*) FROM txn t WHERE t.account_id = a.account_id) in the select list returns what for an account with no transactions?", "options": ["NULL", "0", "The row is dropped", "An error"], "answer": 1, "explain": "COUNT over zero rows is 0, and the outer row is kept - unlike an inner join."},
  {"q": "Which is the NULL-safe way to find rows without a match?", "options": ["NOT IN (subquery)", "NOT EXISTS (correlated subquery)", "<> ALL (subquery)", "!= (subquery)"], "answer": 1, "explain": "NOT EXISTS is unaffected by NULLs in the subquery's data."},
  {"q": "Which index most helps WHERE 2 = (SELECT COUNT(*) FROM account a WHERE a.cust_id = c.cust_id)?", "options": ["customer(city)", "account(cust_id)", "account(avail_balance)", "customer(cust_type_cd)"], "answer": 1, "explain": "The subquery is probed once per customer on a.cust_id."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 9 "Subqueries" (correlated subqueries, the exists operator, data manipulation using correlated subqueries, subqueries as data sources, in filter conditions and as expression generators, subquery wrap-up).
