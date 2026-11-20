"""SQL track problems, part 1: SELECT, filtering, joins, set operations, functions."""

STARTER = "-- write your query\nSELECT "

BANK_ACCOUNT = """
`account(account_id, product_cd, cust_id, open_date, close_date, last_activity_date, status, open_branch_id, open_emp_id, avail_balance, pending_balance)`
"""

PROBLEMS = [
dict(
    id="sql-high-balance-checking",
    title="High-Balance Checking Accounts",
    difficulty="Easy",
    pattern="Filtering",
    kind="sql",
    dataset="bank",
    description=r"""
The bank's relationship managers want to phone every customer who keeps a lot of money in a
**checking** account, so they can pitch a money-market product.

**Table** (dataset `bank`):

- `account(account_id, product_cd, cust_id, open_date, close_date, last_activity_date, status, open_branch_id, open_emp_id, avail_balance, pending_balance)`

Return every account where

- `product_cd` is `'CHK'`,
- `status` is `'ACTIVE'`, and
- `avail_balance` is **strictly greater than 5000**.

**Columns, in this order:** `account_id`, `cust_id`, `avail_balance`

**Order:** by `avail_balance` from highest to lowest.
""",
    starter=STARTER,
    solution="""SELECT account_id, cust_id, avail_balance
FROM account
WHERE product_cd = 'CHK'
  AND status = 'ACTIVE'
  AND avail_balance > 5000
ORDER BY avail_balance DESC;""",
    ordered=True,
    guide=dict(
        prereqs="SELECT / FROM / WHERE / ORDER BY (modules *Query primer* and *Filtering*).",
        intuition="Three independent conditions must all hold, so they are joined with `AND`. Sorting is a separate, final step.",
        hints=["Start with `SELECT account_id, cust_id, avail_balance FROM account`.",
               "Each requirement becomes one predicate; combine them with AND.",
               "`ORDER BY avail_balance DESC` puts the biggest balances first."],
        brute_force="There is nothing slower to compare against: a single table scan with a filter is the whole job.",
        approach="""1. `FROM account` - one table, no joins.
2. `WHERE product_cd = 'CHK' AND status = 'ACTIVE' AND avail_balance > 5000` - every row must pass all three tests.
3. Project only the three requested columns.
4. `ORDER BY avail_balance DESC`.

Dry run: an account with `CHK / ACTIVE / 7893.71` passes; `CHK / FROZEN / 9000` fails the status test; `SAV / ACTIVE / 8000` fails the product test.""",
        complexity="One pass over `account` (O(n)). An index on `(product_cd, status)` would let the engine skip non-checking rows - try `EXPLAIN QUERY PLAN` after creating one.",
        pitfalls="""- `> 5000` versus `>= 5000`: the task says *strictly greater*.
- String literals use **single** quotes. In standard SQL `"CHK"` is an *identifier*; SQLite only falls back to treating it as a string, which hides bugs.
- Forgetting `DESC` returns the smallest balances first.""",
        follow_up="Add `LIMIT 5` to call only the top five, or filter on `pending_balance` too.",
    ),
),
dict(
    id="sql-incomplete-customer-profiles",
    title="Incomplete Customer Profiles",
    difficulty="Easy",
    pattern="NULL logic",
    kind="sql",
    dataset="shop",
    description=r"""
The CRM team is cleaning up the shop's customer list. A profile is *incomplete* when its
`email` **or** its `city` is missing (`NULL`).

**Table** (dataset `shop`):

- `customers(customer_id, first_name, last_name, email, city, country, signup_date, referred_by)`

**Columns, in this order:** `customer_id`, `first_name`, `last_name`, `country`

**Order:** by `customer_id` ascending.
""",
    starter=STARTER,
    solution="""SELECT customer_id, first_name, last_name, country
FROM customers
WHERE email IS NULL OR city IS NULL
ORDER BY customer_id;""",
    ordered=True,
    guide=dict(
        prereqs="NULL and three-valued logic (lesson *NULL: the four-letter word*).",
        intuition="A missing value is not equal to anything - not even to another missing value - so `= NULL` never matches. SQL gives you a dedicated test: `IS NULL`.",
        hints=["Try `WHERE email = NULL` and notice that it returns nothing. Why?",
               "Use `IS NULL` for each column.",
               "Either missing column qualifies, so combine with OR."],
        approach="""`WHERE email IS NULL OR city IS NULL` keeps a row if at least one of the two columns is missing.
Because `IS NULL` always returns TRUE or FALSE (never UNKNOWN), the OR behaves exactly as in ordinary logic.""",
        complexity="A full scan of `customers`; fine for any table that fits in a dashboard query.",
        pitfalls="""- `email = NULL` evaluates to UNKNOWN for every row, and WHERE drops UNKNOWN rows - you get an empty result and no error.
- An empty string `''` is **not** NULL (except in Oracle). If your data mixes both, test `COALESCE(email, '') = ''`.""",
        follow_up="Count incomplete profiles per country with GROUP BY.",
    ),
),
dict(
    id="sql-account-owners",
    title="Who Owns Each Account?",
    difficulty="Easy",
    pattern="Inner joins",
    kind="sql",
    dataset="bank",
    description=r"""
List every account that belongs to an **individual** (person) customer together with the owner's
name and the product's descriptive name.

**Tables** (dataset `bank`):

- `account(account_id, product_cd, cust_id, ..., status, avail_balance, ...)`
- `individual(cust_id, fname, lname, birth_date)` - one row per person customer
- `product(product_cd, name, product_type_cd, date_offered, date_retired)`

**Columns, in this order:** `account_id`, `fname`, `lname`, `product_name`
(the `product.name` column, aliased).

Any row order is accepted.
""",
    starter=STARTER,
    solution="""SELECT a.account_id, i.fname, i.lname, p.name AS product_name
FROM account a
JOIN individual i ON i.cust_id = a.cust_id
JOIN product p    ON p.product_cd = a.product_cd;""",
    guide=dict(
        prereqs="Inner joins and table aliases (module *Querying multiple tables*).",
        intuition="`account` holds foreign keys (`cust_id`, `product_cd`); each JOIN follows one key to the table that holds the descriptive data.",
        hints=["Join `account` to `individual` on `cust_id`.",
               "Join to `product` on `product_cd`.",
               "Business customers have no row in `individual`, so an INNER JOIN drops their accounts automatically."],
        approach="""Three-table inner join. The order you write the joins in does not matter to the result; the optimizer chooses its own join order.

Alias the tables (`a`, `i`, `p`) so the ON clauses stay readable, and alias `p.name` as `product_name` because the task asks for that column name.""",
        complexity="With primary keys on `individual.cust_id` and `product.product_cd`, each account row costs two index lookups: O(n log m).",
        pitfalls="""- Joining `customer` instead of `individual` gives no names - names live in the subtype tables.
- Omitting an ON condition (old comma syntax without a WHERE) produces a Cartesian product.
- `name` is ambiguous across tables; always qualify it.""",
    ),
),
dict(
    id="sql-employees-senior-to-boss",
    title="Employees Who Joined Before Their Boss",
    difficulty="Easy",
    pattern="Self joins",
    kind="sql",
    dataset="bank",
    description=r"""
Each employee row stores the id of its manager in `superior_emp_id`. Find the employees who were
hired **before** their own manager (an earlier `start_date`).

**Table** (dataset `bank`):

- `employee(emp_id, fname, lname, start_date, end_date, superior_emp_id, dept_id, title, assigned_branch_id)`

**Columns, in this order:**
`emp_id`, `employee` (first and last name separated by one space), `employee_start`,
`manager` (same format), `manager_start`

**Order:** by `emp_id`.
""",
    starter=STARTER,
    solution="""SELECT e.emp_id,
       e.fname || ' ' || e.lname AS employee,
       e.start_date              AS employee_start,
       m.fname || ' ' || m.lname AS manager,
       m.start_date              AS manager_start
FROM employee e
JOIN employee m ON m.emp_id = e.superior_emp_id
WHERE e.start_date < m.start_date
ORDER BY e.emp_id;""",
    ordered=True,
    guide=dict(
        prereqs="Self joins (lesson *Multi-table and self joins*), string concatenation with `||`.",
        intuition="Treat the one `employee` table as two copies: one playing *worker*, one playing *manager*. Aliases make that possible.",
        hints=["`FROM employee e JOIN employee m ON m.emp_id = e.superior_emp_id`.",
               "Compare `e.start_date` with `m.start_date`.",
               "Concatenate names with `||` (standard SQL; MySQL uses CONCAT)."],
        approach="Self-join on the manager key, filter on the date comparison, build the display names, sort.",
        complexity="Each employee looks up its manager by primary key: O(n log n) at worst.",
        pitfalls="""- Reversing the ON condition (`e.emp_id = m.superior_emp_id`) pairs managers with their *reports*, flipping the meaning.
- The president has `superior_emp_id = NULL`, so an inner join drops her - correct here, because she has no boss.
- In MySQL `||` is logical OR by default; use `CONCAT(e.fname, ' ', e.lname)`.""",
    ),
),
dict(
    id="sql-cross-branch-transactions",
    title="Transactions Away From Home",
    difficulty="Medium",
    pattern="Inner joins",
    kind="sql",
    dataset="bank",
    description=r"""
A transaction is *away from home* when it was executed at a branch different from the branch where
its account was opened. Report such transactions with both branch names.

**Tables** (dataset `bank`):

- `txn(txn_id, txn_date, account_id, txn_type_cd, amount, teller_emp_id, execution_branch_id, funds_avail_date)`
  (`execution_branch_id` is NULL for ATM/online transactions - ignore those)
- `account(account_id, ..., open_branch_id, ...)`
- `branch(branch_id, name, address, city, state, zip)`

**Columns, in this order:** `txn_id`, `account_id`, `home_branch`, `executed_at`
(the two branch **names**)

Any row order is accepted.
""",
    starter=STARTER,
    solution="""SELECT t.txn_id, t.account_id,
       hb.name AS home_branch,
       xb.name AS executed_at
FROM txn t
JOIN account a ON a.account_id = t.account_id
JOIN branch hb ON hb.branch_id = a.open_branch_id
JOIN branch xb ON xb.branch_id = t.execution_branch_id
WHERE t.execution_branch_id <> a.open_branch_id;""",
    guide=dict(
        prereqs="Joining the same table twice (lesson *Multi-table and self joins*).",
        intuition="You need two different branch rows per transaction, so `branch` appears twice under two aliases - one per role.",
        hints=["Join `txn` to `account` to learn the home branch id.",
               "Join `branch` once as `hb` (home) and once as `xb` (executed).",
               "Filter where the two ids differ."],
        approach="""1. `txn t JOIN account a` - get `open_branch_id`.
2. `JOIN branch hb ON hb.branch_id = a.open_branch_id`.
3. `JOIN branch xb ON xb.branch_id = t.execution_branch_id` - this inner join also discards ATM rows whose branch is NULL.
4. `WHERE t.execution_branch_id <> a.open_branch_id`.""",
        complexity="Three primary-key lookups per transaction: O(n log m).",
        pitfalls="""- Using one alias for `branch` forces both ids to match the same row, which returns nothing useful.
- `NULL <> 2` is UNKNOWN, not TRUE, so ATM rows vanish from the WHERE anyway - but be deliberate about it.""",
        follow_up="Count away-from-home transactions per executing branch.",
    ),
),
dict(
    id="sql-branch-cities-with-customers",
    title="Cities With Both Branches and Customers",
    difficulty="Easy",
    pattern="Set operations",
    kind="sql",
    dataset="bank",
    description=r"""
Which cities host at least one bank **branch** and are also home to at least one **customer**?

**Tables** (dataset `bank`):

- `branch(branch_id, name, address, city, state, zip)`
- `customer(cust_id, fed_id, cust_type_cd, address, city, state, postal_code)`

**Columns:** `city`

**Order:** alphabetical.

Solve it with a **set operator** rather than a join.
""",
    starter=STARTER,
    solution="""SELECT city FROM branch
INTERSECT
SELECT city FROM customer
ORDER BY city;""",
    ordered=True,
    guide=dict(
        prereqs="UNION / INTERSECT / EXCEPT (module *Working with sets*).",
        intuition="Build two sets of city names and keep the overlap. INTERSECT also removes duplicates for you.",
        hints=["Write each SELECT separately first.", "Both queries must return the same number of columns.", "ORDER BY goes once, at the very end of the compound query."],
        approach="`SELECT city FROM branch INTERSECT SELECT city FROM customer ORDER BY city`.",
        complexity="Both inputs are de-duplicated (sort or hash), then merged: O(n log n).",
        pitfalls="""- Placing ORDER BY inside the first SELECT is a syntax error in SQLite and PostgreSQL.
- MySQL only added INTERSECT and EXCEPT in 8.0.31; older versions need `WHERE city IN (SELECT ...)`.
- A join version needs DISTINCT, or a city with five customers appears five times.""",
    ),
),
dict(
    id="sql-import-email-domains",
    title="Email Domains in the Import File",
    difficulty="Easy",
    pattern="String functions",
    kind="sql",
    dataset="shop",
    description=r"""
The `customer_imports` table is a messy marketing upload: some emails are in UPPER case and some have
a leading space. Normalise each email with `lower(trim(email))`, extract the **domain** (everything
after the `@`), and count the imported rows per domain.

**Table** (dataset `shop`):

- `customer_imports(import_id, email, full_name, source, imported_at)`

**Columns, in this order:** `domain`, `imports`

**Order:** by `imports` descending, then `domain` ascending.
""",
    starter=STARTER,
    solution="""SELECT substr(lower(trim(email)), instr(lower(trim(email)), '@') + 1) AS domain,
       COUNT(*) AS imports
FROM customer_imports
GROUP BY domain
ORDER BY imports DESC, domain;""",
    ordered=True,
    guide=dict(
        prereqs="String functions (lesson *Strings and numbers*), GROUP BY.",
        intuition="Clean first, then cut: once the text is lower-case and trimmed, the domain starts one character after the position of `@`.",
        hints=["`instr(s, '@')` returns the 1-based position of `@`.",
               "`substr(s, start)` with no length returns the rest of the string.",
               "You may GROUP BY the alias in SQLite, MySQL and PostgreSQL."],
        approach="""`substr(clean, instr(clean, '@') + 1)` where `clean = lower(trim(email))`, then `GROUP BY domain` and `COUNT(*)`.

A CTE keeps it tidy:
```sql
WITH c AS (SELECT lower(trim(email)) AS e FROM customer_imports)
SELECT substr(e, instr(e,'@')+1) AS domain, COUNT(*) AS imports
FROM c GROUP BY domain ORDER BY imports DESC, domain;
```""",
        complexity="One scan plus a hash/sort aggregate.",
        pitfalls="""- Without `lower`, `EXAMPLE.COM` and `example.com` become two groups.
- MySQL: `SUBSTRING_INDEX(email, '@', -1)`; PostgreSQL: `split_part(email, '@', 2)`.
- `instr` returns 0 when the character is missing; guard with a WHERE if data might lack `@`.""",
    ),
),
dict(
    id="sql-monthly-credits-debits",
    title="Monthly Credits and Debits",
    difficulty="Medium",
    pattern="Date functions",
    kind="sql",
    dataset="bank",
    description=r"""
Finance wants a 2024 cash-flow summary by month.

**Table** (dataset `bank`):

- `txn(txn_id, txn_date, account_id, txn_type_cd, amount, teller_emp_id, execution_branch_id, funds_avail_date)`
  - `txn_type_cd` is `'CDT'` (credit / money in) or `'DBT'` (debit / money out)
  - `txn_date` is text like `'2024-03-07 14:22:00'`

For every month, return the month as `'YYYY-MM'`, the total credited amount and the total debited
amount, each **rounded to 2 decimals**.

**Columns, in this order:** `month`, `credits`, `debits`

**Order:** by `month`.
""",
    starter=STARTER,
    solution="""SELECT strftime('%Y-%m', txn_date) AS month,
       ROUND(SUM(CASE WHEN txn_type_cd = 'CDT' THEN amount ELSE 0 END), 2) AS credits,
       ROUND(SUM(CASE WHEN txn_type_cd = 'DBT' THEN amount ELSE 0 END), 2) AS debits
FROM txn
GROUP BY month
ORDER BY month;""",
    ordered=True,
    guide=dict(
        prereqs="Date functions (`strftime`), GROUP BY, CASE inside aggregates.",
        intuition="Bucket every transaction into its month, then add up amounts twice - once counting only credits and once only debits.",
        hints=["`strftime('%Y-%m', txn_date)` gives the month key.",
               "`SUM(CASE WHEN txn_type_cd='CDT' THEN amount ELSE 0 END)` is *selective aggregation*.",
               "Round after summing, not before."],
        approach="Group by the month expression; compute two conditional sums; round; sort by month (text `YYYY-MM` sorts chronologically).",
        complexity="One scan + aggregate over 12 groups.",
        pitfalls="""- Rounding each amount before summing introduces drift.
- MySQL: `DATE_FORMAT(txn_date, '%Y-%m')`; PostgreSQL: `to_char(txn_date, 'YYYY-MM')` or `date_trunc('month', txn_date)`.
- `ELSE 0` matters: without it the CASE yields NULL, which SUM ignores - fine here, but a month with no debits would show NULL instead of 0.""",
        follow_up="Add a `net` column and a running total of net cash flow with a window function.",
    ),
),
]
