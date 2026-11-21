# INTERSECT, EXCEPT and set operation rules

> **Before this lesson:** you should know what a compound query is, how `UNION` and `UNION ALL` stack two results, and that columns are matched by position ([Set theory and UNION](#/lesson/sql/union)). You should also remember that a comparison with NULL is never true ([NULL: the four-letter word](#/lesson/sql/null-logic)).

## In plain words

`UNION` answers "give me everything from both lists". Two other questions come up as often:

- **What do the two lists have in common?** That is `INTERSECT`.
- **What is on the first list and missing from the second?** That is `EXCEPT`.

An everyday picture: you have the list of people invited to a party and the list of people who replied. *Invited intersect replied* is the people who were invited and answered. *Invited except replied* is the people you still need to chase. *Replied except invited* is a different question altogether: people who answered without being asked, which probably means a mistake somewhere. Notice that swapping the two lists around `EXCEPT` changes the answer, while for `INTERSECT` it does not.

**Why it matters for a job.** "What is missing?" and "what overlaps?" are the two questions behind most data-quality checks: orders that point at a product that does not exist, customers who were loaded twice, a new report that should match the old one row for row. In interviews, "customers who bought A and B" and "customers who bought A but never B" are standard exercises, and set operators are the shortest correct answers.

## INTERSECT: rows found in both results

`A INTERSECT B` returns each row that appears in the result of query A **and** in the result of query B. Repeated rows are listed once.

Start small. Which tellers assigned to branch 2 have also opened accounts at branch 2?

```sql-run dataset=bank
SELECT emp_id FROM employee
WHERE assigned_branch_id = 2 AND title LIKE '%Teller'
INTERSECT
SELECT open_emp_id FROM account
WHERE open_branch_id = 2;
```

- The first query lists the ids of employees whose title ends in "Teller" and who are assigned to branch 2.
- The second lists the id of the opening employee for every account opened at branch 2. Many accounts were opened by the same person, so this list contains repeats.
- `INTERSECT` keeps an id only if it is on both lists, and shows it once.

Three ids come back: 10, 11 and 12. Each is a branch-2 teller who opened at least one account there.

If the two lists share nothing, the result is empty. That is a valid answer, not an error:

```sql-run dataset=bank
SELECT emp_id FROM employee WHERE title = 'President'
INTERSECT
SELECT open_emp_id FROM account;
```

No rows: the president has never opened an account.

Now a question that is hard to ask any other way. Which shop customers have both a **cancelled** order and a **returned** order?

```sql-run dataset=shop
SELECT customer_id FROM orders WHERE status = 'cancelled'
INTERSECT
SELECT customer_id FROM orders WHERE status = 'returned'
ORDER BY customer_id;
```

Four customers. A newcomer's first attempt is often `WHERE status = 'cancelled' AND status = 'returned'`. That returns nothing, ever, because `WHERE` tests one row at a time and a single order has a single status. The question is about *the collection of orders a customer has*, and `INTERSECT` compares collections.

## EXCEPT: rows in the first result and not in the second

`A EXCEPT B` returns each row of A that does **not** appear in B, listed once. The order of the two queries matters.

Which employees at headquarters (branch 1) have never opened an account?

```sql-run dataset=bank
SELECT emp_id FROM employee
WHERE assigned_branch_id = 1
EXCEPT
SELECT open_emp_id FROM account;
```

Six ids: start with everyone at branch 1, then strike out anyone whose id appears as an account opener. Swap the two queries and you ask the opposite question, account openers who do *not* work at headquarters, and get a different list.

Products with no delivered sale since October 2024:

```sql-run dataset=shop
SELECT product_id FROM products
EXCEPT
SELECT oi.product_id
FROM order_items oi JOIN orders o ON o.order_id = oi.order_id
WHERE o.status = 'delivered' AND o.order_date >= '2024-10-01';
```

The top query is "all products"; the bottom is "products that appear in a recent delivered order". What remains is the eight products that did not sell.

And a housekeeping question from the machine-learning data: training runs of experiment 5 that finished but were never saved as a registered model.

```sql-run dataset=mlops
SELECT run_id FROM runs WHERE status = 'FINISHED' AND experiment_id = 5
EXCEPT
SELECT run_id FROM models
ORDER BY run_id;
```

> [!NOTE]
> **Other databases.** `INTERSECT` and `EXCEPT` are part of the SQL standard and work in SQLite, PostgreSQL and SQL Server. Oracle spells `EXCEPT` as `MINUS`. **MySQL added both only in version 8.0.31**; on older MySQL servers you must use the rewrites in the next section.

### The ALL variants

Plain `INTERSECT` and `EXCEPT` ignore how many times a row is repeated. The standard also defines `INTERSECT ALL` and `EXCEPT ALL`, which count copies. If a row appears three times in A and once in B, `A EXCEPT ALL B` keeps two copies and `A INTERSECT ALL B` keeps one, while plain `A EXCEPT B` removes the row completely. PostgreSQL and MySQL 8.0.31+ support the `ALL` forms; SQLite does not.

## The same questions without set operators

Both operators can be rewritten with a **subquery**, a query nested inside another. The rewrites matter for two reasons: old MySQL lacks the operators, and, more importantly, a set operator can return only the columns being compared, whereas a rewrite can return any column you like.

The tool is `EXISTS`. `EXISTS (subquery)` is true when the subquery returns at least one row, and `NOT EXISTS` is true when it returns none. Subqueries and `EXISTS` get a full lesson later ([Correlated subqueries, EXISTS and subqueries as data sources](#/lesson/sql/correlated-exists)); here, read each `EXISTS` as "there is at least one such order for this customer".

**Intersection becomes two `EXISTS` tests.** Keeping the rows of one table that have a match elsewhere is called a **semi-join**.

```sql-run dataset=shop
SELECT c.customer_id, c.first_name, c.last_name
FROM customers c
WHERE EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id AND o.status = 'cancelled')
  AND EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id AND o.status = 'returned')
ORDER BY c.customer_id;
```

The same four customers as before, this time with their names, which the `INTERSECT` version could not show because both of its queries had to return the same single column.

**Difference becomes `NOT EXISTS`.** Keeping the rows that have *no* match is called an **anti-join**.

```sql-run dataset=mlops
SELECT r.run_id, r.run_name, r.model_type
FROM runs r
WHERE r.status = 'FINISHED' AND r.experiment_id = 5
  AND NOT EXISTS (SELECT 1 FROM models m WHERE m.run_id = r.run_id)
ORDER BY r.run_id;
```

There is one subtle difference between the two styles. Set operators treat two NULLs as the same value, while `=` inside a join or subquery never matches a NULL. When the compared columns can be empty, `INTERSECT` and `EXCEPT` are the safe choice. A demonstration follows later in the lesson.

## Rules for compound queries

### One ORDER BY, at the end

A compound query produces **one** result, so it takes **one** `ORDER BY`, written after the last query. The sort columns must be named as they appear in the **first** query.

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

`ORDER BY open_emp_id` would fail: that name belongs to the second query and does not exist in the combined result, whose columns are called `emp_id` and `branch`. A safe habit is to give matching columns the same alias in every query.

`LIMIT` also applies to the whole compound query. To sort or limit one half only, wrap that half in a subquery:

```sql-run dataset=shop
SELECT * FROM (SELECT name, price, 'cheapest' AS tag FROM products ORDER BY price LIMIT 3)
UNION ALL
SELECT * FROM (SELECT name, price, 'priciest' FROM products ORDER BY price DESC LIMIT 3);
```

Six rows: the three cheapest products followed by the three dearest.

### Precedence: which operator is applied first?

With three or more queries and different operators, the order in which they are applied changes the answer, in the same way that 2 + 3 × 4 depends on whether you add or multiply first. The rule that decides is called **precedence**.

```sql-run dataset=bank
SELECT cust_id FROM account WHERE product_cd = 'SAV'
UNION ALL
SELECT cust_id FROM account WHERE product_cd = 'MM'
EXCEPT
SELECT cust_id FROM account WHERE product_cd = 'MRT'
ORDER BY cust_id;
```

Databases do not agree on the rule:

- **Standard SQL, PostgreSQL, SQL Server, MySQL:** `INTERSECT` is applied before `UNION` and `EXCEPT`; operators of equal rank are applied top to bottom.
- **SQLite and Oracle:** all set operators have equal rank and are applied strictly top to bottom.

For the query above both rules give the same answer: stack savings and money-market customers, then remove anyone with a mortgage. (The final `EXCEPT` also removes repeats from the whole result.) The rules disagree for `A UNION B INTERSECT C`. The standard computes `A UNION (B INTERSECT C)`; SQLite computes `(A UNION B) INTERSECT C`.

Most databases let you put parentheses around queries to force the grouping. SQLite does not. There you name the intermediate result with a `WITH` clause, which defines a named temporary result called a **common table expression** or **CTE** ([Common table expressions](#/lesson/sql/ctes)):

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

The part inside `WITH ... AS (...)` runs first and is given the name `mm_no_mortgage`; the main query then uses it like a table.

> [!TIP]
> Never rely on precedence in a compound query that mixes operators. Give each intermediate set a name with a CTE. The query then works the same on every database and is easier to read.

## Worked example: in one or the other, but not both

*Which cities have a branch or a customer, but not both?* In set terms that is (A except B) union (B except A), known as the **symmetric difference**.

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

Four named steps, then a final stack. Every branch city has customers, so the result contains only "customers only" cities: four places where the bank has customers and no branch.

## Worked example: checking data with set operators

Set operators suit **data validation**, because the question is literally about sets: what is missing, what is extra, what overlaps. In each check below, an empty result means the data passed.

**Values used but not defined.** Every `product_cd` on an account should exist in the `product` table.

```sql-run dataset=bank
SELECT product_cd FROM account
EXCEPT
SELECT product_cd FROM product;
```

Empty, as it should be. In this database a foreign key already guarantees it. In many analytics databases such rules are not enforced, and a query like this *is* the check.

**Values defined but never used.** The opposite direction finds products that no account uses.

```sql-run dataset=bank
SELECT product_cd FROM product
EXCEPT
SELECT product_cd FROM account;
```

Two products, `AUT` and `TRM`. This is information, not an error.

**Groups that must not overlap.** A customer is a person or a company, never both.

```sql-run dataset=bank
SELECT cust_id FROM individual
INTERSECT
SELECT cust_id FROM business;
```

**Nothing left over.** Every customer must be one or the other.

```sql-run dataset=bank
SELECT cust_id FROM customer
EXCEPT
SELECT cust_id FROM individual
EXCEPT
SELECT cust_id FROM business;
```

Two `EXCEPT`s in a row: begin with all customers, remove the individuals, then remove the businesses. Anything left would be a customer with no detail row. Both operators are the same, so every database applies them top to bottom. Together, the last two checks confirm that `individual` and `business` split `customer` cleanly, with no overlap and no gap. Such a split is called a **partition**.

## A habit worth forming: comparing two results

`EXCEPT` is the quickest test of whether two queries return the same rows, for example after you rewrite a query to make it faster. If both of these come back empty, the two results contain the same rows:

```sql
SELECT * FROM (old_query) EXCEPT SELECT * FROM (new_query);
SELECT * FROM (new_query) EXCEPT SELECT * FROM (old_query);
```

Here the comma-style join from the inner-joins lesson is compared with the `JOIN ... ON` form:

```sql-run dataset=bank
-- Is the comma-join version equivalent to the JOIN ... ON version?
SELECT e.emp_id, d.name FROM employee e JOIN department d ON d.dept_id = e.dept_id
EXCEPT
SELECT e.emp_id, d.name FROM employee e, department d WHERE d.dept_id = e.dept_id;
```

Empty, as expected. This test ignores how many times a row is repeated; to compare that too, compare `COUNT(*)` of both results as well.

## Counting what the sets contain

Set operators return rows, not counts. Wrap them in a counting query to summarise. Here is an overlap report between customers who have a login on record and customers who ordered in March 2024:

```sql-run dataset=shop
WITH logged AS (SELECT DISTINCT customer_id FROM logins),
     ordered AS (SELECT DISTINCT customer_id FROM orders
                 WHERE order_date >= '2024-03-01' AND order_date < '2024-04-01')
SELECT 'logged in' AS segment, COUNT(*) AS customers FROM logged
UNION ALL SELECT 'ordered', COUNT(*) FROM ordered
UNION ALL SELECT 'both', COUNT(*) FROM (SELECT customer_id FROM logged INTERSECT SELECT customer_id FROM ordered)
UNION ALL SELECT 'logged in only', COUNT(*) FROM (SELECT customer_id FROM logged EXCEPT SELECT customer_id FROM ordered)
UNION ALL SELECT 'ordered only', COUNT(*) FROM (SELECT customer_id FROM ordered EXCEPT SELECT customer_id FROM logged);
```

16 logged in, 22 ordered, 5 did both. Set theory supplies a built-in check: *both* plus *logged in only* must equal *logged in* (5 + 11 = 16), and *both* plus *ordered only* must equal *ordered* (5 + 17 = 22). If the numbers do not add up, one of the definitions is wrong.

## NULLs and duplicates in set operators

**Two NULLs count as the same value.** For `INTERSECT`, `EXCEPT` and the duplicate removal in `UNION`, an empty cell matches another empty cell. An ordinary comparison does not behave that way:

```sql-run dataset=bank
SELECT 'INTERSECT finds NULL' AS test, COUNT(*) AS rows_returned
FROM (SELECT NULL AS v INTERSECT SELECT NULL)
UNION ALL
SELECT 'IN finds NULL', COUNT(*)
FROM (SELECT NULL AS v) t WHERE v IN (SELECT NULL);
```

`INTERSECT` returns the NULL row (count 1). `IN` does not (count 0), because `IN` uses `=` and `NULL = NULL` is unknown. This makes `EXCEPT` the safest way to compare two tables column by column when some columns can be empty.

**The result is a set.** `INTERSECT` and `EXCEPT` remove repeats, so a count of their output is a count of *distinct* rows.

```sql-run dataset=bank
SELECT COUNT(*) AS cust_ids_with_txn_free_accounts
FROM (SELECT cust_id FROM account
      EXCEPT
      SELECT a.cust_id FROM account a JOIN txn t ON t.account_id = a.account_id);
```

Read this result with care. It counts customers for whom **no** account has any transaction, not customers who have *some* account without transactions. A customer with one busy account and one idle account appears in the bottom query and is removed. A set difference works on the values you select, so select the values that match the question; choosing `account_id` instead would answer the per-account version.

## Which tool for which question?

| Question | Clearest tool | Why |
|---|---|---|
| Which key values are in A and not in B? | `EXCEPT` | reads like the question; safe with NULLs |
| Which *rows of A*, with all their columns, have no match in B? | `NOT EXISTS` (anti-join) | can return columns that B lacks |
| Which key values are in both? | `INTERSECT` | removes repeats for you |
| Which rows of A have a match in B? | `EXISTS` or `IN` (semi-join) | keeps A's columns, no multiplication of rows |
| Are two query results identical? | `EXCEPT` in both directions | compares whole rows, NULLs included |
| Combine rows from two sources | `UNION ALL` | stacks without extra work |

> [!INTERVIEW]
> A common prompt: "Find customers who bought product A but never product B." Offer two solutions and compare them. `SELECT customer_id ... WHERE product = 'A' EXCEPT SELECT customer_id ... WHERE product = 'B'` is short and returns ids only. `EXISTS ... AND NOT EXISTS ...` returns any customer columns you like. Add that MySQL before 8.0.31 has no `EXCEPT`; awareness of such differences is what interviewers listen for.

## Pitfalls

- **`EXCEPT` depends on order.** Check which query is on top.
- **Both operators remove repeats.** A count of the result is a count of distinct rows.
- **Mixed operators without explicit grouping** behave differently on different databases.
- **`ORDER BY` using a name from a later query** fails; only the first query's names exist.
- **Old MySQL** has neither operator; use `EXISTS` and `NOT EXISTS`.
- **A one-row test for a many-row question.** `WHERE x = 'a' AND x = 'b'` is never true.

## Summary

- `INTERSECT` keeps rows found in both results; `EXCEPT` (Oracle: `MINUS`) keeps rows of the first that are missing from the second. Both remove repeats and treat NULLs as equal.
- Rewrites exist: the semi-join (`EXISTS`, `IN`) and the anti-join (`NOT EXISTS`), which can also return extra columns.
- A compound query takes one `ORDER BY` and one `LIMIT`, at the end, using the first query's column names.
- Precedence differs between databases: the standard applies `INTERSECT` first; SQLite works top to bottom. Use CTEs or parentheses to say what you mean.
- Empty results from `EXCEPT` and `INTERSECT` make compact data-quality checks.

## Glossary

- **`INTERSECT`** — set operator returning the rows present in both query results.
- **`EXCEPT`** — set operator returning the rows of the first result that are absent from the second (`MINUS` in Oracle).
- **`INTERSECT ALL` / `EXCEPT ALL`** — variants that take the number of copies of each row into account.
- **Subquery** — a query written inside another query.
- **`EXISTS`** — a test that is true when a subquery returns at least one row.
- **Semi-join** — keeping the rows of one table that have at least one match in another, without adding columns or copies.
- **Anti-join** — keeping the rows of one table that have no match in another.
- **Precedence** — the rule that decides which operator is applied first when several are mixed.
- **Common table expression (CTE)** — a named temporary result defined with `WITH` and used later in the same query.
- **Symmetric difference** — the items that are in exactly one of two sets.
- **Partition (of a set)** — a split into groups that do not overlap and leave nothing out.
- **Data validation** — checking that stored data obeys the rules it is supposed to obey.

```quiz
[
  {"q": "A = {1,2,3}, B = {2,3,4}. What is A EXCEPT B?", "options": ["{1}", "{4}", "{1,4}", "{2,3}"], "answer": 0, "explain": "EXCEPT keeps the elements of A that are not in B; only 1 qualifies."},
  {"q": "Why can't WHERE status = 'cancelled' AND status = 'returned' find customers with both kinds of order?", "options": ["AND is not allowed on text", "WHERE tests one row at a time and a single row has only one status", "It needs DISTINCT", "It can"], "answer": 1, "explain": "The question is about the collection of rows per customer; use INTERSECT or two EXISTS tests."},
  {"q": "What does Oracle call EXCEPT?", "options": ["DIFFERENCE", "MINUS", "WITHOUT", "SUBTRACT"], "answer": 1, "explain": "Oracle uses MINUS for set difference."},
  {"q": "In SQLite, how is A UNION B INTERSECT C evaluated?", "options": ["A UNION (B INTERSECT C)", "(A UNION B) INTERSECT C", "It is an error", "In an undefined order"], "answer": 1, "explain": "SQLite gives all set operators equal rank and applies them top to bottom; the standard applies INTERSECT first."},
  {"q": "Where must ORDER BY go in a compound query?", "options": ["After each SELECT", "After the first SELECT", "Once, after the last SELECT", "Before the first SELECT"], "answer": 2, "explain": "It sorts the combined result and uses the first query's column names."},
  {"q": "An advantage of NOT EXISTS over EXCEPT is...", "options": ["It removes duplicates", "It can return columns that are not part of the comparison", "It is always faster", "It treats NULLs as equal"], "answer": 1, "explain": "EXCEPT compares whole rows, so both sides must return the same columns; NOT EXISTS filters the outer query, which can select anything."},
  {"q": "SELECT NULL INTERSECT SELECT NULL returns how many rows?", "options": ["0, because NULL = NULL is unknown", "1, because set operators treat NULLs as the same value", "2", "An error"], "answer": 1, "explain": "For set operators two NULLs match each other, unlike the = comparison used by joins and IN."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 6 "Working with Sets" (the intersect and except operators, set operation rules, sorting compound query results, set operation precedence), restated in original wording. SQLite documentation, "Compound Select Statements".
