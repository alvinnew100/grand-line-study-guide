# SELECT and FROM

`SELECT` is the statement you will write a thousand times more often than any other. It looks simple — pick some columns from a table — but each of its clauses has more power than first appears. This lesson covers the two mandatory-ish clauses, `SELECT` and `FROM`: what you can put in the select list, column aliases, removing duplicates, the kinds of "tables" a FROM clause accepts, and table aliases.

## The clauses of a query

A `SELECT` statement is made of up to six main clauses. The book summarises them in a table that is worth memorising:

| Clause | Purpose |
|---|---|
| `SELECT` | which columns (or expressions) to include in the result |
| `FROM` | which tables to draw data from, and how to join them |
| `WHERE` | which rows to keep |
| `GROUP BY` | how to group rows that share values |
| `HAVING` | which groups to keep |
| `ORDER BY` | how to sort the final result |

Only `SELECT` is strictly required in SQLite, MySQL and PostgreSQL — `SELECT 1 + 1;` is a valid query with no FROM. (Oracle requires `FROM dual`.)

```sql-run dataset=bank
SELECT 1 + 1 AS two, 'hello' || ' ' || 'world' AS greeting, date('2024-02-28', '+1 day') AS leap_day;
```

## The SELECT clause

Although it is written first, the select list is evaluated *late*: the server first works out which rows qualify (FROM, WHERE, GROUP BY, HAVING) and only then computes the columns you asked for. The next lesson returns to this evaluation order because it explains several error messages.

### Selecting all columns

`*` means "every column, in table order":

```sql-run dataset=bank
SELECT * FROM department;
```

`*` is fine for exploration but avoid it in application code and saved queries: it returns columns you don't need (wasting I/O and network), and its meaning changes silently when someone adds or reorders columns.

### Selecting specific columns and expressions

The select list can hold any mix of:

- **column names** — `fname`
- **literals** — numbers or strings such as `'ACTIVE'`
- **expressions** — `avail_balance * 1.05`, `fname || ' ' || lname`
- **function calls** — `upper(lname)`, `round(x, 2)`
- **scalar subqueries** (later module)

```sql-run dataset=bank
SELECT emp_id,
       'ACTIVE'                 AS status,
       emp_id * 3.14159         AS empid_x_pi,
       upper(lname)             AS last_name_upper,
       julianday('2024-12-31') - julianday(start_date) AS days_employed
FROM employee
LIMIT 8;
```

The literal `'ACTIVE'` appears on every row; `empid_x_pi` is arithmetic; `upper` is a built-in function.

### Column aliases

Without an alias, an expression column gets an awkward generated name — try removing `AS days_employed` above and see the header become the whole expression. An **alias** names a result column:

```sql
SELECT upper(lname) AS last_name_upper ...
```

The keyword `AS` is optional (`upper(lname) last_name_upper`), but writing it makes queries easier to read and avoids a classic bug: a missing comma between two columns turns the second into an alias of the first.

```sql-run dataset=bank
SELECT fname lname      -- oops: missing comma; "lname" is now an alias for fname!
FROM employee
LIMIT 3;
```

An alias that contains spaces or is a reserved word must be quoted — `AS "Days Employed"`. Aliases matter beyond cosmetics: client code reads columns by name, and the judge in this guide checks your column names.

### Removing duplicates with DISTINCT

Ask which customers have accounts and you get one row per account — so customers with three accounts appear three times:

```sql-run dataset=bank
SELECT cust_id FROM account ORDER BY cust_id LIMIT 12;
```

`DISTINCT` removes duplicate rows from the result:

```sql-run dataset=bank
SELECT DISTINCT cust_id FROM account ORDER BY cust_id LIMIT 12;
```

`DISTINCT` applies to the **whole row**, not to the first column: `SELECT DISTINCT cust_id, product_cd` returns each distinct *pair*.

> [!WARNING]
> DISTINCT is not free. To remove duplicates the server must sort or hash the entire result. Use it when duplicates are genuinely possible and unwanted, not as a reflex to "clean up" output — reflexive DISTINCT often hides a join that is producing more rows than you think (a *fan-out*). Fix the join instead.

`ALL` is the opposite (keep duplicates) and the default, so you will rarely write it.

## The FROM clause

The book defines FROM as naming the tables used by the query, *along with the means of linking them together*. That second half matters: joins are part of FROM.

### Kinds of tables

A FROM clause can draw from four kinds of table:

1. **Permanent tables** — created with `CREATE TABLE`.
2. **Derived tables** — rows returned by a **subquery** in parentheses, held in memory for the query.
3. **Temporary tables** — `CREATE TEMPORARY TABLE`, volatile data visible to your session only.
4. **Virtual tables** — **views**, stored queries that act like tables.

You have already used permanent tables. Here is a derived table: the inner query builds a three-column table on the fly and the outer query selects from it as if it were stored:

```sql-run dataset=bank
SELECT e.emp_id, e.full_name
FROM (SELECT emp_id, fname || ' ' || lname AS full_name, start_date
      FROM employee
      WHERE title = 'Teller') AS e
WHERE e.start_date >= '2020-06-01';
```

A derived table must be given an alias (`AS e`) in MySQL and PostgreSQL (≤15); SQLite does not insist but it is good practice.

A temporary table persists for your session and disappears when you disconnect:

```sql-run dataset=shop
CREATE TEMP TABLE big_spenders AS
SELECT customer_id, COUNT(*) AS orders
FROM orders GROUP BY customer_id HAVING COUNT(*) >= 6;

SELECT * FROM big_spenders ORDER BY orders DESC;
```

And a view is a saved query:

```sql-run dataset=shop
CREATE VIEW delivered_orders AS
SELECT order_id, customer_id, order_date FROM orders WHERE status = 'delivered';

SELECT COUNT(*) FROM delivered_orders;
```

Views get their own module later; for now, note that the FROM clause doesn't care which kind of table it is reading.

### Table links

When FROM names more than one table, it must also say how they relate — the **join condition**:

```sql-run dataset=bank
SELECT employee.emp_id, employee.fname, employee.lname, department.name AS dept_name
FROM employee
JOIN department ON employee.dept_id = department.dept_id
LIMIT 8;
```

The joins modules cover this in depth.

### Table aliases

Writing `employee.` and `department.` everywhere is tedious. A **table alias** gives a short name to use throughout the query:

```sql-run dataset=bank
SELECT e.emp_id, e.fname, e.lname, d.name AS dept_name
FROM employee e
JOIN department d ON e.dept_id = d.dept_id
LIMIT 8;
```

`AS` is optional for table aliases (and Oracle forbids it there). Once you alias a table, use the alias consistently: in most engines, referring to `employee.fname` after aliasing it as `e` is an error.

Table aliases are essential when the same table appears twice (self joins) and when a column name is ambiguous across tables — both `branch` and `department` have a `name` column, so you must say which one.

> [!TIP]
> Use short but meaningful aliases: `a` for account, `c` for customer, `t` for txn. Avoid `t1, t2, t3` in long queries; they make reviews painful.

## Selecting from the other datasets

The same clauses work everywhere. A quick look at the ML runs table, computing a derived column:

```sql-run dataset=mlops
SELECT run_id,
       run_name,
       model_type,
       status,
       round((julianday(ended_at) - julianday(started_at)) * 24, 2) AS hours
FROM runs
WHERE experiment_id = 6;
```

Note that `hours` is NULL for runs still `RUNNING` — `ended_at` is NULL and arithmetic with NULL yields NULL. The filtering module explains NULL in depth.

## Pitfalls

- **Missing commas** silently create aliases.
- **SELECT \*** in production code.
- **DISTINCT as a band-aid** for a bad join.
- **Ambiguous column names** after joins — qualify them.
- **Forgetting that a derived table needs an alias** in MySQL/PostgreSQL.

## Expressions in depth: what you can compute in the select list

The select list is where raw columns become the answer to a question, so it is worth seeing the main families of expression side by side. Every one of them is evaluated **once per row** of the result.

```sql-run dataset=shop
SELECT product_id,
       name,
       price,
       cost,
       price - cost                               AS margin,
       ROUND(100.0 * (price - cost) / price, 1)   AS margin_pct,
       upper(substr(name, 1, 3)) || '-' || product_id AS sku,
       CASE WHEN discontinued = 1 THEN 'retired' ELSE 'active' END AS lifecycle,
       launched_on < '2023-01-01'                 AS launched_before_2023,
       (SELECT name FROM categories c WHERE c.category_id = p.category_id) AS category
FROM products p
WHERE product_id <= 6;
```

Walk through the result. `margin` and `margin_pct` are plain arithmetic; note `100.0` rather than `100`, which forces real-number division. `sku` chains three string operations. `lifecycle` uses CASE (module *Conditional logic*). `launched_before_2023` shows that a comparison is itself an expression — SQLite and MySQL return 1 or 0, PostgreSQL returns a true boolean. The last column is a *scalar subquery*: a query in parentheses that returns one value, evaluated for each product.

Two rules of thumb:

- **An alias defined in the select list cannot be used elsewhere in the same select list** in standard SQL. `SELECT price - cost AS margin, margin / price` fails in PostgreSQL and MySQL (SQLite permits it). Repeat the expression, or compute it in a subquery/CTE and refer to it from the outer query.
- **Column order is yours to choose** — and matters, because clients and the judge in this guide read columns by position and name. Put identifying columns first and measures last.

### Qualified stars

`*` can be restricted to one table, which is handy when exploring a join without typing every column:

```sql-run dataset=bank
SELECT a.*, p.name AS product_name
FROM account a
JOIN product p ON p.product_cd = a.product_cd
WHERE a.cust_id = 2;
```

All of `account`'s columns, plus one named column from `product`. The same caution applies as for a bare `*`: fine at the prompt, fragile in saved code.

## DISTINCT, in detail

Three clarifications that prevent most DISTINCT mistakes.

**1. DISTINCT sees the whole output row.** Adding a column can only keep or increase the number of rows:

```sql-run dataset=shop
SELECT (SELECT COUNT(*) FROM (SELECT DISTINCT country FROM customers))            AS countries,
       (SELECT COUNT(*) FROM (SELECT DISTINCT country, city FROM customers))      AS country_city_pairs,
       (SELECT COUNT(*) FROM customers)                                           AS all_rows;
```

**2. NULLs count as equal to each other for DISTINCT** (unlike `=`). A column with several NULLs contributes a single NULL row:

```sql-run dataset=shop
SELECT DISTINCT city FROM customers WHERE country = 'Japan' ORDER BY city;
```

**3. `COUNT(DISTINCT x)` is not the same as `SELECT DISTINCT`.** The first is an aggregate that returns one number and ignores NULLs; the second removes duplicate rows and keeps a NULL row.

```sql-run dataset=shop
SELECT COUNT(city) AS non_null_cities,
       COUNT(DISTINCT city) AS distinct_cities,
       (SELECT COUNT(*) FROM (SELECT DISTINCT city FROM customers)) AS distinct_rows_incl_null
FROM customers;
```

When someone reaches for DISTINCT, ask which question they are answering: "what are the different values?" (legitimate) or "why am I getting duplicates?" (a join problem to fix at its source).

## FROM in practice: a small investigation

A realistic use of the kinds of table. Suppose the support team asks: *which customers have placed five or more orders, and when did each last order?* Build it in layers.

A **derived table** computes the per-customer summary; the outer query joins it to a **permanent table** for names:

```sql-run dataset=shop
SELECT c.customer_id, c.first_name || ' ' || c.last_name AS customer, s.orders, s.last_order
FROM (SELECT customer_id, COUNT(*) AS orders, MAX(order_date) AS last_order
      FROM orders
      GROUP BY customer_id
      HAVING COUNT(*) >= 5) AS s
JOIN customers c ON c.customer_id = s.customer_id
ORDER BY s.orders DESC, c.customer_id;
```

If several follow-up questions need the same summary, promote it to a **temporary table** (lives for your session) or a **view** (stored definition, always current):

```sql-run dataset=shop
CREATE VIEW customer_order_summary AS
SELECT customer_id, COUNT(*) AS orders, MIN(order_date) AS first_order, MAX(order_date) AS last_order
FROM orders
GROUP BY customer_id;

SELECT c.country, COUNT(*) AS customers_with_orders, ROUND(AVG(s.orders), 2) AS avg_orders
FROM customer_order_summary s
JOIN customers c ON c.customer_id = s.customer_id
GROUP BY c.country
ORDER BY customers_with_orders DESC;
```

The choice between them is about **lifetime and reuse**, not about what they can express: a derived table lives for one query, a temp table for one session, a view until it is dropped.

> [!NOTE]
> **Naming and case.** Unquoted identifiers are case-insensitive in SQLite and MySQL (on most platforms), folded to lower case in PostgreSQL and to upper case in Oracle. A table created as `"Customers"` (quoted, mixed case) must then always be written with quotes in PostgreSQL. The simplest policy — and the one this guide follows — is `lower_snake_case` names, never quoted.

> [!INTERVIEW]
> When asked to "write a query that returns X", say the output columns aloud before writing: their names, order, and what one row represents. Many interview answers lose points not for logic but for returning an extra column, an unnamed expression, or duplicate rows.

## Summary

- A query has up to six clauses: SELECT, FROM, WHERE, GROUP BY, HAVING, ORDER BY.
- The select list can contain columns, literals, expressions, functions and subqueries; alias computed columns with `AS`.
- `DISTINCT` removes duplicate *rows* at the cost of a sort or hash.
- FROM reads permanent tables, derived tables (subqueries), temporary tables and views, and contains the join conditions.
- Table aliases shorten queries and are required to use a table twice.

```quiz
[
  {"q": "Which clause is the only one SQLite strictly requires?", "options": ["FROM", "SELECT", "WHERE", "ORDER BY"], "answer": 1, "explain": "SELECT 1+1; is legal with no FROM in SQLite, MySQL and PostgreSQL."},
  {"q": "What does SELECT fname lname FROM employee return?", "options": ["Two columns", "One column named lname containing first names", "A syntax error", "Last names only"], "answer": 1, "explain": "Without a comma, lname becomes the alias of fname."},
  {"q": "SELECT DISTINCT cust_id, product_cd removes duplicates of...", "options": ["cust_id only", "product_cd only", "each (cust_id, product_cd) pair", "nothing"], "answer": 2, "explain": "DISTINCT applies to entire result rows."},
  {"q": "Which of these is a derived table?", "options": ["A view", "A subquery in the FROM clause", "A temporary table", "An index"], "answer": 1, "explain": "A derived table is produced by a subquery inside FROM and lives only for that query."},
  {"q": "Why might a reflexive DISTINCT be a code smell?", "options": ["It is not standard SQL", "It can hide a join that multiplies rows", "It sorts by primary key", "It removes NULLs"], "answer": 1, "explain": "Unexpected duplicates usually mean a join fan-out; DISTINCT masks the bug and costs a sort."},
  {"q": "Why must you use table aliases in a self join?", "options": ["For speed", "To refer to the same table in two roles", "Because SQLite requires it everywhere", "To avoid DISTINCT"], "answer": 1, "explain": "Two copies of one table need two names to distinguish their columns."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 3 "Query Primer" (query clauses, the select clause, column aliases, removing duplicates, the from clause, tables, table links, table aliases).
