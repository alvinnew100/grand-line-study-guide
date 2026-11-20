"""SQL track problems, part 2: grouping, subqueries, outer joins, CASE, metadata, transactions, indexes."""

STARTER = "-- write your query\nSELECT "

PROBLEMS = [
dict(
    id="sql-branch-balance-summary",
    title="Branch Balance Summary",
    difficulty="Easy",
    pattern="Grouping & aggregates",
    kind="sql",
    dataset="bank",
    description=r"""
For each branch, summarise the **active** accounts that were opened there.

**Tables** (dataset `bank`):

- `account(account_id, product_cd, cust_id, open_date, close_date, last_activity_date, status, open_branch_id, open_emp_id, avail_balance, pending_balance)`
- `branch(branch_id, name, address, city, state, zip)`

**Columns, in this order:**
`branch_name`, `num_accounts`, `total_balance` (sum of `avail_balance`, rounded to 2),
`avg_balance` (rounded to 2)

**Order:** by `total_balance` descending.
""",
    starter=STARTER,
    solution="""SELECT b.name AS branch_name,
       COUNT(*) AS num_accounts,
       ROUND(SUM(a.avail_balance), 2) AS total_balance,
       ROUND(AVG(a.avail_balance), 2) AS avg_balance
FROM account a
JOIN branch b ON b.branch_id = a.open_branch_id
WHERE a.status = 'ACTIVE'
GROUP BY b.branch_id, b.name
ORDER BY total_balance DESC;""",
    ordered=True,
    guide=dict(
        prereqs="GROUP BY and aggregate functions (module *Grouping and aggregates*).",
        intuition="Filter rows first (WHERE), then collapse each branch's rows into one summary row (GROUP BY), then sort the summaries.",
        hints=["Join account to branch to get the name.", "WHERE status = 'ACTIVE' runs before grouping.",
               "COUNT(*), SUM, AVG all work per group."],
        approach="Join, filter, `GROUP BY b.branch_id, b.name`, compute three aggregates, round, sort.",
        complexity="One scan + hash aggregate over 4 groups.",
        pitfalls="""- Grouping by `name` only is fine here, but grouping by the key (`branch_id`) is safer when names can repeat.
- Selecting a column that is neither grouped nor aggregated is an error in PostgreSQL and in MySQL with ONLY_FULL_GROUP_BY; SQLite silently picks a value from an arbitrary row.
- Filtering on status in HAVING instead of WHERE would fail - status is not a group-level value.""",
    ),
),
dict(
    id="sql-multi-account-customers",
    title="Customers With Three or More Accounts",
    difficulty="Easy",
    pattern="HAVING",
    kind="sql",
    dataset="bank",
    description=r"""
Find customers who hold **at least three accounts** (any status).

**Table** (dataset `bank`):

- `account(account_id, product_cd, cust_id, ..., status, ..., avail_balance, pending_balance)`

**Columns, in this order:** `cust_id`, `num_accounts`, `total_balance` (sum of `avail_balance`, rounded to 2)

**Order:** by `num_accounts` descending, then `cust_id` ascending.
""",
    starter=STARTER,
    solution="""SELECT cust_id,
       COUNT(*) AS num_accounts,
       ROUND(SUM(avail_balance), 2) AS total_balance
FROM account
GROUP BY cust_id
HAVING COUNT(*) >= 3
ORDER BY num_accounts DESC, cust_id;""",
    ordered=True,
    guide=dict(
        prereqs="HAVING vs WHERE.",
        intuition="The condition is about a *group* (how many rows a customer has), so it can only be checked after grouping - that is HAVING's job.",
        hints=["GROUP BY cust_id.", "`HAVING COUNT(*) >= 3`.", "Two sort keys."],
        approach="Group by customer, count, keep groups with count >= 3, sort.",
        complexity="One scan + aggregate.",
        pitfalls="""- `WHERE COUNT(*) >= 3` is an error: aggregates are not allowed in WHERE.
- PostgreSQL does not allow a SELECT alias inside HAVING (`HAVING num_accounts >= 3`); SQLite and MySQL do. Repeating the aggregate is portable.""",
    ),
),
dict(
    id="sql-category-revenue",
    title="Revenue by Category",
    difficulty="Medium",
    pattern="Grouping & aggregates",
    kind="sql",
    dataset="shop",
    description=r"""
Compute net revenue per product category, counting only **delivered** orders.
Line revenue is `quantity * unit_price * (1 - discount)`.

**Tables** (dataset `shop`):

- `orders(order_id, customer_id, order_date, status, shipping_fee)`
- `order_items(order_item_id, order_id, product_id, quantity, unit_price, discount)`
- `products(product_id, name, category_id, price, cost, launched_on, discontinued)`
- `categories(category_id, name, parent_id)`

Return only categories whose revenue exceeds **1000**.

**Columns, in this order:** `category`, `orders` (number of *distinct* delivered orders containing the category), `revenue` (rounded to 2)

**Order:** by `revenue` descending.
""",
    starter=STARTER,
    solution="""SELECT c.name AS category,
       COUNT(DISTINCT o.order_id) AS orders,
       ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)), 2) AS revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN products p     ON p.product_id = oi.product_id
JOIN categories c   ON c.category_id = p.category_id
WHERE o.status = 'delivered'
GROUP BY c.category_id, c.name
HAVING SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) > 1000
ORDER BY revenue DESC;""",
    ordered=True,
    guide=dict(
        prereqs="Multi-table joins, COUNT(DISTINCT), HAVING.",
        intuition="Join down to the line-item grain, filter delivered orders, then roll lines up to categories.",
        hints=["The grain after the joins is one row per order line.",
               "An order with two laptop lines would be counted twice by COUNT(*) - use COUNT(DISTINCT order_id).",
               "The > 1000 filter is on an aggregate: HAVING."],
        approach="Four-table join, WHERE on status, GROUP BY category, aggregate, HAVING, sort.",
        complexity="Linear in order lines with hash joins; the planner will use the primary keys of the dimension tables.",
        pitfalls="""- Filtering `status` in HAVING is wrong (and an error in strict engines).
- Forgetting `(1 - discount)` overstates revenue.
- Products sit in leaf categories here (e.g. *Laptops*), not in the top-level *Electronics*; rolling up the hierarchy needs a recursive CTE (see problem *Revenue Rolled Up the Category Tree*).""",
    ),
),
dict(
    id="sql-above-average-checking",
    title="Accounts Above the Checking Average",
    difficulty="Easy",
    pattern="Scalar subqueries",
    kind="sql",
    dataset="bank",
    description=r"""
Return all accounts (any product) whose `avail_balance` is greater than the **average balance of
all checking accounts** (`product_cd = 'CHK'`).

**Table** (dataset `bank`):

- `account(account_id, product_cd, cust_id, ..., avail_balance, pending_balance)`

**Columns, in this order:** `account_id`, `product_cd`, `avail_balance`

**Order:** by `avail_balance` descending.
""",
    starter=STARTER,
    solution="""SELECT account_id, product_cd, avail_balance
FROM account
WHERE avail_balance > (SELECT AVG(avail_balance)
                       FROM account
                       WHERE product_cd = 'CHK')
ORDER BY avail_balance DESC;""",
    ordered=True,
    guide=dict(
        prereqs="Noncorrelated scalar subqueries (module *Subqueries*).",
        intuition="Compute one number (the checking average) in an inner query, then compare every row with it.",
        hints=["The inner query returns one row and one column.", "Put it in parentheses on the right of `>`.", "It runs once, independent of the outer row."],
        approach="`WHERE avail_balance > (SELECT AVG(avail_balance) FROM account WHERE product_cd = 'CHK')`.",
        complexity="Two scans of `account`: one for the average, one for the filter.",
        pitfalls="- `WHERE avail_balance > AVG(avail_balance)` is illegal - aggregates cannot appear in WHERE.\n- If the subquery could return several rows you would need ANY/ALL/IN instead of `>`.",
    ),
),
dict(
    id="sql-customers-never-ordered",
    title="Customers Who Never Ordered",
    difficulty="Easy",
    pattern="EXISTS",
    kind="sql",
    dataset="shop",
    description=r"""
List customers who have **no orders at all**.

**Tables** (dataset `shop`):

- `customers(customer_id, first_name, last_name, email, city, country, signup_date, referred_by)`
- `orders(order_id, customer_id, order_date, status, shipping_fee)`

**Columns, in this order:** `customer_id`, `first_name`, `last_name`, `signup_date`

**Order:** by `customer_id`.
""",
    starter=STARTER,
    solution="""SELECT c.customer_id, c.first_name, c.last_name, c.signup_date
FROM customers c
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id)
ORDER BY c.customer_id;""",
    ordered=True,
    guide=dict(
        prereqs="Correlated subqueries and EXISTS.",
        intuition="For each customer ask a yes/no question: *is there any order for this customer?* Keep the ones answered no.",
        hints=["The subquery refers to `c.customer_id` from the outer query - that makes it correlated.",
               "EXISTS ignores the select list; `SELECT 1` is the convention.",
               "Alternative: LEFT JOIN orders and keep rows where `o.order_id IS NULL`."],
        approach="`WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id)` - an *anti-join*.",
        complexity="Engines turn NOT EXISTS into an anti-join; with an index on `orders(customer_id)` each probe is O(log n).",
        pitfalls="- `NOT IN (SELECT customer_id FROM orders)` breaks if that column ever contains NULL.\n- With LEFT JOIN, test a NOT NULL column of the right table (its primary key), not a nullable one.",
    ),
),
dict(
    id="sql-latest-order-per-customer",
    title="Each Customer's Latest Order",
    difficulty="Medium",
    pattern="Correlated subqueries",
    kind="sql",
    dataset="shop",
    description=r"""
For every customer who has ordered, return their **most recent** order. If a customer placed several
orders on that same latest date, return the one with the **highest `order_id`**.

**Table** (dataset `shop`):

- `orders(order_id, customer_id, order_date, status, shipping_fee)`

**Columns, in this order:** `customer_id`, `order_id`, `order_date`, `status`

Any row order is accepted.
""",
    starter=STARTER,
    solution="""SELECT o.customer_id, o.order_id, o.order_date, o.status
FROM orders o
WHERE o.order_id = (SELECT o2.order_id
                    FROM orders o2
                    WHERE o2.customer_id = o.customer_id
                    ORDER BY o2.order_date DESC, o2.order_id DESC
                    LIMIT 1);""",
    guide=dict(
        prereqs="Correlated subqueries; later, window functions.",
        intuition="For each order ask: *is this the newest order of its own customer?* The inner query finds that newest order id per outer row.",
        hints=["Correlate on customer_id.", "Order the inner query by date then id, both descending, LIMIT 1.",
               "Equivalent window-function version: ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC, order_id DESC) = 1."],
        brute_force="`WHERE order_date = (SELECT MAX(order_date) ...)` is simpler but returns ties - two rows for a customer with two orders on the same day.",
        approach="Correlated scalar subquery returning one order_id per customer; keep the outer row whose id matches.",
        complexity="Naively O(n^2); with an index on `orders(customer_id, order_date)` each probe is a short index range. ROW_NUMBER needs a single sort: O(n log n).",
        pitfalls="- The tie rule matters: always add a deterministic tie-breaker.\n- LIMIT inside a subquery is fine in SQLite/PostgreSQL/MySQL; SQL Server uses TOP 1.",
        follow_up="Rewrite with ROW_NUMBER and compare the query plans with EXPLAIN QUERY PLAN.",
    ),
),
dict(
    id="sql-pricier-than-category-average",
    title="Pricier Than Their Category",
    difficulty="Medium",
    pattern="Correlated subqueries",
    kind="sql",
    dataset="shop",
    description=r"""
Find products whose price is **above the average price of products in the same category**.

**Tables** (dataset `shop`):

- `products(product_id, name, category_id, price, cost, launched_on, discontinued)`
- `categories(category_id, name, parent_id)`

**Columns, in this order:** `product_id`, `product`, `category`, `price`, `category_avg` (rounded to 2)

**Order:** by `category`, then `price` descending.
""",
    starter=STARTER,
    solution="""SELECT p.product_id, p.name AS product, c.name AS category, p.price,
       ROUND((SELECT AVG(p2.price) FROM products p2 WHERE p2.category_id = p.category_id), 2) AS category_avg
FROM products p
JOIN categories c ON c.category_id = p.category_id
WHERE p.price > (SELECT AVG(p2.price) FROM products p2 WHERE p2.category_id = p.category_id)
ORDER BY category, p.price DESC;""",
    ordered=True,
    guide=dict(
        prereqs="Correlated subqueries; derived tables.",
        intuition="Each product needs *its own* category's average - the subquery is re-evaluated per outer row with that row's category.",
        hints=["Inner: `SELECT AVG(price) FROM products p2 WHERE p2.category_id = p.category_id`.",
               "Use it in WHERE for the filter and in SELECT for display.",
               "Alternative: join to a derived table `(SELECT category_id, AVG(price) avg_p FROM products GROUP BY category_id)`."],
        approach="""Derived-table version (often faster, computes each average once):
```sql
SELECT p.product_id, p.name AS product, c.name AS category, p.price, ROUND(a.avg_p,2) AS category_avg
FROM products p
JOIN (SELECT category_id, AVG(price) AS avg_p FROM products GROUP BY category_id) a USING (category_id)
JOIN categories c USING (category_id)
WHERE p.price > a.avg_p
ORDER BY category, p.price DESC;
```""",
        complexity="Correlated: O(n x group size) without an index; derived table: O(n).",
        pitfalls="- A category with one product never qualifies (price = its own average).\n- Ambiguous `name`: alias both name columns.",
    ),
),
dict(
    id="sql-employee-transaction-counts",
    title="Transactions Handled per Employee",
    difficulty="Medium",
    pattern="Outer joins",
    kind="sql",
    dataset="bank",
    description=r"""
List **every** employee with the number of transactions they handled as teller
(`txn.teller_emp_id`). Employees who handled none must appear with **0**.

**Tables** (dataset `bank`):

- `employee(emp_id, fname, lname, start_date, end_date, superior_emp_id, dept_id, title, assigned_branch_id)`
- `txn(txn_id, txn_date, account_id, txn_type_cd, amount, teller_emp_id, execution_branch_id, funds_avail_date)`

**Columns, in this order:** `emp_id`, `fname`, `lname`, `title`, `txn_count`

**Order:** by `txn_count` descending, then `emp_id`.
""",
    starter=STARTER,
    solution="""SELECT e.emp_id, e.fname, e.lname, e.title,
       COUNT(t.txn_id) AS txn_count
FROM employee e
LEFT JOIN txn t ON t.teller_emp_id = e.emp_id
GROUP BY e.emp_id, e.fname, e.lname, e.title
ORDER BY txn_count DESC, e.emp_id;""",
    ordered=True,
    guide=dict(
        prereqs="LEFT OUTER JOIN (module *Joins revisited*).",
        intuition="An inner join would silently drop employees with no transactions. A left join keeps every employee and pads the txn columns with NULL.",
        hints=["`employee e LEFT JOIN txn t ON t.teller_emp_id = e.emp_id`.",
               "`COUNT(t.txn_id)` counts non-NULL values, so padded rows count as 0.",
               "`COUNT(*)` would count the padded row as 1 - wrong."],
        approach="Left join, group by employee, count a column from the optional side.",
        complexity="Hash or index-nested-loop join; linear in txn rows.",
        pitfalls="""- Putting a filter on `t` in the WHERE clause (e.g. `WHERE t.amount > 100`) turns the left join back into an inner join - move it into the ON clause instead.
- COUNT(*) vs COUNT(column) is the classic bug here.""",
    ),
),
dict(
    id="sql-country-status-matrix",
    title="Country x Status Order Matrix",
    difficulty="Medium",
    pattern="Cross joins",
    kind="sql",
    dataset="shop",
    description=r"""
Build a complete matrix of **every customer country x every order status that appears in `orders`**,
with the number of orders for each combination - including combinations with **zero** orders.

**Tables** (dataset `shop`):

- `customers(customer_id, first_name, last_name, email, city, country, signup_date, referred_by)`
- `orders(order_id, customer_id, order_date, status, shipping_fee)`

**Columns, in this order:** `country`, `status`, `orders`

**Order:** by `country`, then `status`.
""",
    starter=STARTER,
    solution="""WITH countries AS (SELECT DISTINCT country FROM customers),
     statuses  AS (SELECT DISTINCT status FROM orders),
     counts    AS (SELECT c.country, o.status, COUNT(*) AS n
                   FROM orders o JOIN customers c ON c.customer_id = o.customer_id
                   GROUP BY c.country, o.status)
SELECT k.country, s.status, COALESCE(n.n, 0) AS orders
FROM countries k
CROSS JOIN statuses s
LEFT JOIN counts n ON n.country = k.country AND n.status = s.status
ORDER BY k.country, s.status;""",
    ordered=True,
    guide=dict(
        prereqs="CROSS JOIN, LEFT JOIN, COALESCE.",
        intuition="A plain GROUP BY only produces combinations that exist. To show zeros, first *generate* all combinations (Cartesian product), then attach counts with a left join.",
        hints=["Distinct countries x distinct statuses = the scaffold.", "Aggregate the real counts separately.",
               "LEFT JOIN the counts to the scaffold and COALESCE NULL to 0."],
        approach="Scaffold with CROSS JOIN, fill with LEFT JOIN, default with COALESCE. This *densification* pattern also fills missing dates in time series.",
        complexity="7 countries x 5 statuses = 35 scaffold rows; trivial.",
        pitfalls="- Joining customers to orders with a LEFT JOIN and grouping still misses statuses that a country never had.\n- `COUNT(*)` after a left join would report 1 instead of 0.",
    ),
),
dict(
    id="sql-experiment-run-outcomes",
    title="Experiment Run Outcomes",
    difficulty="Easy",
    pattern="CASE",
    kind="sql",
    dataset="mlops",
    description=r"""
For each experiment, pivot its runs by status and compute a success rate.

**Tables** (dataset `mlops`):

- `experiments(experiment_id, name, team, owner, task, created_at)`
- `runs(run_id, experiment_id, ..., status, ...)` with status in `RUNNING`, `FINISHED`, `FAILED`, `KILLED`

**Columns, in this order:**
`experiment`, `total_runs`, `finished`, `failed`, `success_pct`
(`100.0 * finished / total_runs`, rounded to 1)

**Order:** by `success_pct` descending, then `experiment`.
""",
    starter=STARTER,
    solution="""SELECT e.name AS experiment,
       COUNT(*) AS total_runs,
       SUM(CASE WHEN r.status = 'FINISHED' THEN 1 ELSE 0 END) AS finished,
       SUM(CASE WHEN r.status = 'FAILED' THEN 1 ELSE 0 END) AS failed,
       ROUND(100.0 * SUM(CASE WHEN r.status = 'FINISHED' THEN 1 ELSE 0 END) / COUNT(*), 1) AS success_pct
FROM experiments e
JOIN runs r ON r.experiment_id = e.experiment_id
GROUP BY e.experiment_id, e.name
ORDER BY success_pct DESC, experiment;""",
    ordered=True,
    guide=dict(
        prereqs="CASE expressions, selective aggregation (module *Conditional logic*).",
        intuition="`SUM(CASE WHEN cond THEN 1 ELSE 0 END)` counts the rows meeting `cond` inside each group - it turns row values into columns.",
        hints=["Group by experiment.", "One CASE-in-SUM per status column.", "Multiply by 100.0 (not 100) to avoid integer division."],
        approach="Join, group, conditional sums, percentage with a REAL multiplier, round, sort.",
        complexity="One pass.",
        pitfalls="- `100 * finished / total` in SQLite or PostgreSQL is integer division (67/100 -> 0).\n- PostgreSQL also offers `COUNT(*) FILTER (WHERE status = 'FINISHED')`.",
    ),
),
dict(
    id="sql-balance-tiers",
    title="Balance Tiers",
    difficulty="Easy",
    pattern="CASE",
    kind="sql",
    dataset="bank",
    description=r"""
Classify **deposit** accounts (`product_cd IN ('CHK','SAV','MM','CD')`) into tiers by `avail_balance`:

| tier | rule |
|---|---|
| `low` | balance < 1000 |
| `medium` | 1000 <= balance < 10000 |
| `high` | balance >= 10000 |

Count the accounts in each tier.

**Table** (dataset `bank`): `account(account_id, product_cd, ..., avail_balance, ...)`

**Columns, in this order:** `tier`, `accounts`

**Order:** `low`, `medium`, `high` (a business order, not alphabetical).
""",
    starter=STARTER,
    solution="""SELECT CASE WHEN avail_balance < 1000 THEN 'low'
            WHEN avail_balance < 10000 THEN 'medium'
            ELSE 'high' END AS tier,
       COUNT(*) AS accounts
FROM account
WHERE product_cd IN ('CHK', 'SAV', 'MM', 'CD')
GROUP BY tier
ORDER BY CASE tier WHEN 'low' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END;""",
    ordered=True,
    guide=dict(
        prereqs="Searched and simple CASE.",
        intuition="A searched CASE evaluates its WHEN branches top to bottom and stops at the first true one, so later branches can assume earlier ones failed.",
        hints=["Order the WHENs from smallest threshold up.", "GROUP BY the tier.", "A simple CASE in ORDER BY maps labels to sort positions."],
        approach="CASE to label, GROUP BY label, ORDER BY a CASE that returns 1/2/3.",
        complexity="One pass.",
        pitfalls="- Overlapping ranges are harmless because the first match wins, but gaps (e.g. `< 1000` then `> 1000`) lose rows at exactly 1000 into ELSE.\n- Alphabetical order would be high, low, medium.",
    ),
),
dict(
    id="sql-pending-balance-mismatch",
    title="Accounts With Uncommitted Funds",
    difficulty="Easy",
    pattern="Transactions",
    kind="sql",
    dataset="bank",
    description=r"""
`pending_balance` includes transactions that are still clearing; `avail_balance` only includes
settled funds. Find accounts where the two differ, and show the difference.

**Table** (dataset `bank`): `account(account_id, product_cd, cust_id, ..., status, ..., avail_balance, pending_balance)`

**Columns, in this order:** `account_id`, `cust_id`, `avail_balance`, `pending_balance`, `diff`
(`pending_balance - avail_balance`, rounded to 2)

**Order:** by the absolute difference descending, then `account_id`.
""",
    starter=STARTER,
    solution="""SELECT account_id, cust_id, avail_balance, pending_balance,
       ROUND(pending_balance - avail_balance, 2) AS diff
FROM account
WHERE pending_balance <> avail_balance
ORDER BY ABS(pending_balance - avail_balance) DESC, account_id;""",
    ordered=True,
    guide=dict(
        prereqs="Arithmetic expressions, ABS, ordering by an expression not in the SELECT list.",
        intuition="These are accounts with work *in flight* - the state a transaction moves between. A real bank updates both balances inside one transaction so readers never see half an update.",
        hints=["`WHERE pending_balance <> avail_balance`.", "ORDER BY may use any expression.", "ABS gives the magnitude."],
        approach="Filter on inequality, compute the difference, sort by its magnitude.",
        complexity="One scan + sort.",
        pitfalls="- Comparing floating-point money for exact equality can mislead; real systems use DECIMAL/NUMERIC or integer cents.\n- `<>` and `!=` are both accepted; `<>` is the standard spelling.",
    ),
),
dict(
    id="sql-q1-large-transactions",
    title="Large Q1 Transactions (Index-Friendly)",
    difficulty="Easy",
    pattern="Indexes & sargability",
    kind="sql",
    dataset="bank",
    description=r"""
Return transactions from the **first quarter of 2024** (1 Jan - 31 Mar, any time of day) whose amount
is at least **3000**. Write the date condition so that an index on `txn_date` could be used
(no functions wrapped around the column).

**Table** (dataset `bank`):
`txn(txn_id, txn_date, account_id, txn_type_cd, amount, teller_emp_id, execution_branch_id, funds_avail_date)`

**Columns, in this order:** `txn_id`, `txn_date`, `account_id`, `txn_type_cd`, `amount`

**Order:** by `txn_date`.
""",
    starter=STARTER,
    solution="""SELECT txn_id, txn_date, account_id, txn_type_cd, amount
FROM txn
WHERE txn_date >= '2024-01-01' AND txn_date < '2024-04-01'
  AND amount >= 3000
ORDER BY txn_date;""",
    ordered=True,
    guide=dict(
        prereqs="B-tree indexes and EXPLAIN QUERY PLAN (module *Indexes and constraints*).",
        intuition="An index is sorted by the raw column value. A half-open range on the raw column maps to one contiguous slice of the index; `strftime('%m', txn_date)` does not.",
        hints=["Use `>=` on the first day and `<` on the first day *after* the range.",
               "Timestamps carry times, so `<= '2024-03-31'` would miss 31 March afternoons.",
               "Try `CREATE INDEX ix_txn_date ON txn(txn_date);` then `EXPLAIN QUERY PLAN` your query."],
        approach="Half-open date range plus the amount filter, then sort. With the index, SQLite reports `SEARCH txn USING INDEX ix_txn_date (txn_date>? AND txn_date<?)` and can even skip the sort.",
        complexity="With an index: O(log n + k). Without: full scan O(n).",
        pitfalls="- `'2024-03-31 15:00:00' <= '2024-03-31'` is FALSE in text comparison - a classic off-by-a-day bug.\n- `BETWEEN '2024-01-01' AND '2024-03-31 23:59:59'` works but is fragile with fractional seconds.",
    ),
),
dict(
    id="sql-schema-column-counts",
    title="Schema Inventory",
    difficulty="Medium",
    pattern="Metadata",
    kind="sql",
    dataset="bank",
    description=r"""
Use the database's **metadata** to produce an inventory of the bank schema: for every table, its
number of columns and how many of those columns are declared `NOT NULL`.

In SQLite the catalog is `sqlite_master` (alias `sqlite_schema`) and column details come from the
table-valued function `pragma_table_info(table_name)`, which returns
`(cid, name, type, "notnull", dflt_value, pk)`.

**Columns, in this order:** `table_name`, `columns`, `not_null_columns`

**Order:** by `table_name`.
""",
    starter=STARTER,
    solution="""SELECT m.name AS table_name,
       COUNT(*) AS columns,
       SUM(p."notnull") AS not_null_columns
FROM sqlite_master m
JOIN pragma_table_info(m.name) p
WHERE m.type = 'table'
GROUP BY m.name
ORDER BY m.name;""",
    ordered=True,
    guide=dict(
        prereqs="Lesson *Metadata and the data dictionary*.",
        intuition="The catalog is itself queryable as tables. Joining the list of tables to a per-table column function gives one row per (table, column) - then it is an ordinary GROUP BY.",
        hints=["`SELECT name FROM sqlite_master WHERE type = 'table'` lists tables.",
               "`pragma_table_info(m.name)` can be joined like a table (a lateral call).",
               "`notnull` is 1 or 0, so SUM counts the NOT NULL columns."],
        approach="Join sqlite_master to pragma_table_info, group by table, count and sum.",
        complexity="Reads only the catalog - instant.",
        pitfalls="""- An `INTEGER PRIMARY KEY` column is reported with notnull = 0 even though SQLite never stores NULL in it.
- MySQL/PostgreSQL equivalent: `SELECT table_name, COUNT(*), SUM(CASE WHEN is_nullable='NO' THEN 1 ELSE 0 END) FROM information_schema.columns WHERE table_schema = ... GROUP BY table_name`.""",
    ),
),
]
