"""SQL track problems, part 3: window functions, CTEs, recursion, analytics/interview patterns, design."""

STARTER = "-- write your query\nSELECT "

REVENUE_TABLES = """
- `orders(order_id, customer_id, order_date, status, shipping_fee)`
- `order_items(order_item_id, order_id, product_id, quantity, unit_price, discount)`
- `products(product_id, name, category_id, price, cost, launched_on, discontinued)`
- `categories(category_id, name, parent_id)`
"""

PROBLEMS = [
dict(
    id="sql-top2-products-per-category",
    title="Top Two Products per Category",
    difficulty="Medium",
    pattern="Top-N per group",
    kind="sql",
    dataset="shop",
    description=r"""
For every category, find the **two products with the highest net revenue** from **delivered** orders.
Line revenue is `quantity * unit_price * (1 - discount)`. Use `DENSE_RANK`, so products tied on
revenue share a rank (and both are returned).

**Tables** (dataset `shop`):
""" + REVENUE_TABLES + r"""
**Columns, in this order:** `category`, `product`, `revenue` (rounded to 2), `rnk`

**Order:** by `category`, then `rnk`, then `product`.
""",
    starter=STARTER,
    solution="""WITH rev AS (
  SELECT c.name AS category, p.name AS product,
         SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS revenue
  FROM orders o
  JOIN order_items oi ON oi.order_id = o.order_id
  JOIN products p     ON p.product_id = oi.product_id
  JOIN categories c   ON c.category_id = p.category_id
  WHERE o.status = 'delivered'
  GROUP BY c.category_id, c.name, p.product_id, p.name
), ranked AS (
  SELECT category, product, revenue,
         DENSE_RANK() OVER (PARTITION BY category ORDER BY revenue DESC) AS rnk
  FROM rev
)
SELECT category, product, ROUND(revenue, 2) AS revenue, rnk
FROM ranked
WHERE rnk <= 2
ORDER BY category, rnk, product;""",
    ordered=True,
    guide=dict(
        prereqs="Window functions: ranking (module *Analytic functions*), CTEs.",
        intuition="Aggregate to one row per product, rank products *within* each category with a window, then keep ranks 1-2. The window does not collapse rows, so you need an outer query to filter on it.",
        hints=["Step 1 (CTE): revenue per (category, product).",
               "Step 2: `DENSE_RANK() OVER (PARTITION BY category ORDER BY revenue DESC)`.",
               "Step 3: `WHERE rnk <= 2` in an outer query - window results cannot be referenced in the WHERE of the same SELECT."],
        brute_force="Correlated count: keep a product when fewer than 2 products in its category have strictly higher revenue. Correct but O(n^2).",
        approach="Aggregate -> rank -> filter, the canonical top-N-per-group recipe. ROW_NUMBER would return exactly two rows per category (breaking ties arbitrarily); RANK would leave gaps (1,1,3).",
        complexity="One sort per partition: O(n log n).",
        pitfalls="""- Filtering `WHERE DENSE_RANK() OVER (...) <= 2` is a syntax error; wrap in a CTE or subquery (some engines offer QUALIFY).
- Rank *after* rounding can create artificial ties; rank the raw value.
- Ranking line items instead of per-product totals ranks the wrong thing.""",
    ),
),
dict(
    id="sql-account-running-balance",
    title="Running Balance of an Account",
    difficulty="Medium",
    pattern="Running totals",
    kind="sql",
    dataset="bank",
    description=r"""
Show the transaction history of account **157** with a running net total. Credits (`'CDT'`) add,
debits (`'DBT'`) subtract.

**Table** (dataset `bank`):
`txn(txn_id, txn_date, account_id, txn_type_cd, amount, teller_emp_id, execution_branch_id, funds_avail_date)`

**Columns, in this order:**
`txn_id`, `txn_date`, `signed_amount` (positive for credits, negative for debits),
`running_total` (cumulative sum of `signed_amount` in date order, rounded to 2)

**Order:** by `txn_date`, then `txn_id`.
""",
    starter=STARTER,
    solution="""SELECT txn_id, txn_date,
       CASE txn_type_cd WHEN 'CDT' THEN amount ELSE -amount END AS signed_amount,
       ROUND(SUM(CASE txn_type_cd WHEN 'CDT' THEN amount ELSE -amount END)
             OVER (ORDER BY txn_date, txn_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS running_total
FROM txn
WHERE account_id = 157
ORDER BY txn_date, txn_id;""",
    ordered=True,
    guide=dict(
        prereqs="Aggregate window functions and frames.",
        intuition="`SUM(x) OVER (ORDER BY t)` adds up x from the first row up to the current row - a running total - while keeping every row.",
        hints=["Sign the amount with a simple CASE.", "Wrap the same expression in `SUM(...) OVER (ORDER BY txn_date, txn_id ...)`.",
               "Spell out `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`."],
        approach="Filter one account, compute the signed amount, cumulative SUM over an ordered window.",
        complexity="Single sort + single pass: O(n log n).",
        pitfalls="""- With ORDER BY but no frame, the default frame is `RANGE ... CURRENT ROW`, which includes *all peers* with the same sort value - two transactions at the same timestamp would jump together. Adding `txn_id` to the ORDER BY and using ROWS avoids that.
- A self-join running total (`SUM over t2.txn_date <= t1.txn_date`) is O(n^2).""",
    ),
),
dict(
    id="sql-monthly-revenue-growth",
    title="Month-over-Month Revenue Growth",
    difficulty="Medium",
    pattern="LAG / LEAD",
    kind="sql",
    dataset="shop",
    description=r"""
Compute delivered-order revenue per month in 2024 and its growth versus the previous month.
Revenue = `SUM(quantity * unit_price * (1 - discount))` over delivered orders.

**Tables** (dataset `shop`): `orders(order_id, customer_id, order_date, status, shipping_fee)`,
`order_items(order_item_id, order_id, product_id, quantity, unit_price, discount)`

**Columns, in this order:**
`month` (`'YYYY-MM'`), `revenue` (rounded to 2), `prev_revenue` (rounded to 2; NULL for the first month),
`growth_pct` (`100 * (revenue - prev) / prev`, rounded to 1; NULL for the first month)

**Order:** by `month`.
""",
    starter=STARTER,
    solution="""WITH m AS (
  SELECT strftime('%Y-%m', o.order_date) AS month,
         SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS revenue
  FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
  WHERE o.status = 'delivered'
  GROUP BY month
)
SELECT month,
       ROUND(revenue, 2) AS revenue,
       ROUND(LAG(revenue) OVER (ORDER BY month), 2) AS prev_revenue,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month)) / LAG(revenue) OVER (ORDER BY month), 1) AS growth_pct
FROM m
ORDER BY month;""",
    ordered=True,
    guide=dict(
        prereqs="LAG/LEAD (lesson *Offsets: LAG, LEAD and friends*).",
        intuition="LAG lets a row peek at the previous row's value in a chosen order - exactly *last month* once rows are monthly.",
        hints=["First aggregate to one row per month in a CTE.", "`LAG(revenue) OVER (ORDER BY month)`.", "Use a named WINDOW clause to avoid repeating the OVER."],
        approach="Aggregate, then LAG over months, then compute the percentage. The first month has no predecessor so LAG returns NULL and the arithmetic propagates NULL.",
        complexity="Tiny: 12 rows after aggregation.",
        pitfalls="- Applying LAG before aggregating looks at the previous *order line*, not month.\n- Months with zero revenue would be missing entirely; densify with a calendar if that matters.\n- Integer division: use 100.0.",
    ),
),
dict(
    id="sql-best-run-per-experiment",
    title="Best Run per Experiment",
    difficulty="Medium",
    pattern="Top-N per group",
    kind="sql",
    dataset="mlops",
    description=r"""
For each experiment, find the finished run with the **highest `accuracy`** metric. Break ties by the
smaller `run_id`. Experiments with no accuracy metric (e.g. regression tasks) do not appear.

**Tables** (dataset `mlops`):

- `experiments(experiment_id, name, team, owner, task, created_at)`
- `runs(run_id, experiment_id, parent_run_id, run_name, model_type, learning_rate, batch_size, status, started_at, ended_at, gpu_hours, triggered_by)`
- `metrics(run_id, metric_name, step, value)` - long format; accuracy rows have `metric_name = 'accuracy'`

**Columns, in this order:** `experiment`, `run_id`, `model_type`, `accuracy`

**Order:** by `accuracy` descending.
""",
    starter=STARTER,
    solution="""WITH acc AS (
  SELECT e.name AS experiment, r.run_id, r.model_type, m.value AS accuracy,
         ROW_NUMBER() OVER (PARTITION BY e.experiment_id ORDER BY m.value DESC, r.run_id) AS rn
  FROM experiments e
  JOIN runs r    ON r.experiment_id = e.experiment_id
  JOIN metrics m ON m.run_id = r.run_id AND m.metric_name = 'accuracy'
  WHERE r.status = 'FINISHED'
)
SELECT experiment, run_id, model_type, accuracy
FROM acc
WHERE rn = 1
ORDER BY accuracy DESC;""",
    ordered=True,
    guide=dict(
        prereqs="ROW_NUMBER and PARTITION BY.",
        intuition="Number runs within each experiment from best to worst; the run numbered 1 is the winner.",
        hints=["Join runs to metrics with `metric_name = 'accuracy'` in the ON clause.",
               "`ROW_NUMBER() OVER (PARTITION BY experiment_id ORDER BY value DESC, run_id)`.",
               "Keep `rn = 1` in an outer query."],
        approach="Join, number, filter. ROW_NUMBER guarantees exactly one row per experiment because the tie-breaker makes the ordering total.",
        complexity="Sort within partitions: O(n log n).",
        pitfalls="- `SELECT experiment_id, MAX(value), run_id ... GROUP BY experiment_id` returns an arbitrary run_id in SQLite (and is rejected elsewhere) - the *bare column* trap.\n- Forgetting the status filter could pick a killed run that logged a partial metric.",
    ),
),
dict(
    id="sql-latency-moving-average",
    title="Prediction Latency Moving Average",
    difficulty="Medium",
    pattern="Window frames",
    kind="sql",
    dataset="mlops",
    description=r"""
SRE wants a smoothed view of serving latency during **March 2024**. For each day that has predictions,
compute the number of predictions, the day's average `latency_ms`, and a **3-day moving average**
of the daily averages (the current day and the two previous *days that have data*).

**Table** (dataset `mlops`):
`predictions(prediction_id, deployment_id, predicted_at, predicted_label, actual_label, score, latency_ms)`

**Columns, in this order:** `day` (`'YYYY-MM-DD'`), `predictions`, `avg_latency` (rounded to 1),
`ma3_latency` (rounded to 1)

**Order:** by `day`.
""",
    starter=STARTER,
    solution="""WITH d AS (
  SELECT date(predicted_at) AS day, COUNT(*) AS predictions, AVG(latency_ms) AS avg_latency
  FROM predictions
  WHERE predicted_at >= '2024-03-01' AND predicted_at < '2024-04-01'
  GROUP BY day
)
SELECT day, predictions,
       ROUND(avg_latency, 1) AS avg_latency,
       ROUND(AVG(avg_latency) OVER (ORDER BY day ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS ma3_latency
FROM d
ORDER BY day;""",
    ordered=True,
    guide=dict(
        prereqs="Window frames (lesson *Aggregate windows and frames*).",
        intuition="A frame is a sliding sub-window. `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` averages at most three consecutive rows.",
        hints=["Aggregate to one row per day first.", "`AVG(avg_latency) OVER (ORDER BY day ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)`.",
               "The first day's average uses one row, the second day's two."],
        approach="Daily aggregate in a CTE, then a framed AVG window.",
        complexity="Linear after the aggregate sort.",
        pitfalls="""- ROWS counts rows, not calendar days: if a day is missing, the window reaches further back. For a true calendar window use `RANGE` over a numeric day (e.g. `julianday(day)`) - `RANGE BETWEEN 2 PRECEDING AND CURRENT ROW`.
- Averaging all raw predictions over three days (weighted by volume) is a different metric from averaging daily averages - be explicit about which one the dashboard wants.""",
    ),
),
dict(
    id="sql-overfitting-alerts",
    title="Overfitting Alerts",
    difficulty="Hard",
    pattern="LAG / LEAD",
    kind="sql",
    dataset="mlops",
    description=r"""
A training run shows a warning sign when its **validation loss goes up** from one step to the next.
For every run where that happens at least once, report the **first step** at which `val_loss`
increased, the previous and new values, and the run's model type.

**Tables** (dataset `mlops`):

- `metrics(run_id, metric_name, step, value)` - `metric_name = 'val_loss'` rows, steps 1, 2, 3, ...
- `runs(run_id, experiment_id, parent_run_id, run_name, model_type, ..., status, ...)`

**Columns, in this order:** `run_id`, `model_type`, `step`, `prev_val_loss`, `val_loss`

**Order:** by `run_id`.
""",
    starter=STARTER,
    solution="""WITH v AS (
  SELECT run_id, step, value AS val_loss,
         LAG(value) OVER (PARTITION BY run_id ORDER BY step) AS prev_val_loss
  FROM metrics
  WHERE metric_name = 'val_loss'
), ups AS (
  SELECT run_id, step, prev_val_loss, val_loss,
         ROW_NUMBER() OVER (PARTITION BY run_id ORDER BY step) AS k
  FROM v
  WHERE val_loss > prev_val_loss
)
SELECT u.run_id, r.model_type, u.step, u.prev_val_loss, u.val_loss
FROM ups u JOIN runs r ON r.run_id = u.run_id
WHERE u.k = 1
ORDER BY u.run_id;""",
    ordered=True,
    guide=dict(
        prereqs="LAG with PARTITION BY; ROW_NUMBER for first-occurrence.",
        intuition="Compare each step with the previous step *of the same run*; among the increases keep the earliest.",
        hints=["`LAG(value) OVER (PARTITION BY run_id ORDER BY step)`.",
               "Filter `val_loss > prev_val_loss` in a second step (window results need an outer query).",
               "ROW_NUMBER over the remaining rows picks the first one per run (or use MIN(step) and join back)."],
        approach="Three layers: (1) LAG per run, (2) keep increases and number them, (3) keep number 1 and join to runs for the model type.",
        complexity="One sort of the val_loss rows by (run_id, step).",
        pitfalls="- Without PARTITION BY, step 1 of a run would be compared with the last step of the previous run.\n- `prev_val_loss` is NULL at step 1, and `x > NULL` is UNKNOWN - so step 1 is excluded automatically.",
    ),
),
dict(
    id="sql-org-chart-levels",
    title="Org Chart Levels",
    difficulty="Medium",
    pattern="Recursive CTE",
    kind="sql",
    dataset="bank",
    description=r"""
Walk the management hierarchy from the president (the employee with no `superior_emp_id`) downward.
For each employee report their **level** (president = 1, direct reports = 2, ...) and the chain of
last names from the top, joined by `' > '` (for example `'Smith > Tyler > Hawthorne'`).

**Table** (dataset `bank`):
`employee(emp_id, fname, lname, start_date, end_date, superior_emp_id, dept_id, title, assigned_branch_id)`

**Columns, in this order:** `emp_id`, `name` (`fname || ' ' || lname`), `title`, `level`, `chain`

**Order:** by `level`, then `emp_id`.
""",
    starter=STARTER,
    solution="""WITH RECURSIVE org(emp_id, name, title, level, chain) AS (
  SELECT emp_id, fname || ' ' || lname, title, 1, lname
  FROM employee
  WHERE superior_emp_id IS NULL
  UNION ALL
  SELECT e.emp_id, e.fname || ' ' || e.lname, e.title, o.level + 1, o.chain || ' > ' || e.lname
  FROM employee e
  JOIN org o ON e.superior_emp_id = o.emp_id
)
SELECT emp_id, name, title, level, chain
FROM org
ORDER BY level, emp_id;""",
    ordered=True,
    guide=dict(
        prereqs="Recursive CTEs (lesson *Recursive CTEs*).",
        intuition="A recursive CTE is a loop: the *anchor* produces the first generation (the president); the *recursive member* joins the previous generation to its children, until no new rows appear.",
        hints=["Anchor: `WHERE superior_emp_id IS NULL`, level 1, chain = lname.",
               "Recursive step: `JOIN org o ON e.superior_emp_id = o.emp_id`, level + 1, chain extended.",
               "UNION ALL between the two parts."],
        approach="Standard top-down tree traversal. Each iteration adds one level; the hierarchy here is 5 levels deep.",
        complexity="Each employee is visited once: O(n) iterations of index lookups.",
        pitfalls="- A cycle in the data (A manages B manages A) loops forever with UNION ALL; guard with a depth limit or by checking the chain.\n- MySQL requires 8.0+; PostgreSQL and SQLite need the RECURSIVE keyword, SQL Server does not use it.",
    ),
),
dict(
    id="sql-category-tree-revenue",
    title="Revenue Rolled Up the Category Tree",
    difficulty="Hard",
    pattern="Recursive CTE",
    kind="sql",
    dataset="shop",
    description=r"""
Categories form a tree through `parent_id` (e.g. *Electronics > Computers > Laptops*). Products are
attached to any level. Report delivered-order revenue rolled up to each **top-level** category
(categories with `parent_id IS NULL`). Line revenue is `quantity * unit_price * (1 - discount)`.

**Tables** (dataset `shop`):
""" + REVENUE_TABLES + r"""
**Columns, in this order:** `top_category`, `revenue` (rounded to 2)

**Order:** by `revenue` descending.
""",
    starter=STARTER,
    solution="""WITH RECURSIVE tree(category_id, root_id) AS (
  SELECT category_id, category_id FROM categories WHERE parent_id IS NULL
  UNION ALL
  SELECT c.category_id, t.root_id
  FROM categories c JOIN tree t ON c.parent_id = t.category_id
)
SELECT root.name AS top_category,
       ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)), 2) AS revenue
FROM tree t
JOIN categories root ON root.category_id = t.root_id
JOIN products p      ON p.category_id = t.category_id
JOIN order_items oi  ON oi.product_id = p.product_id
JOIN orders o        ON o.order_id = oi.order_id
WHERE o.status = 'delivered'
GROUP BY root.category_id, root.name
ORDER BY revenue DESC;""",
    ordered=True,
    guide=dict(
        prereqs="Recursive CTEs; multi-table aggregation.",
        intuition="First build a lookup *category -> its root*, carrying the root id unchanged down the recursion. Then the problem is an ordinary join + GROUP BY root.",
        hints=["Anchor: each root maps to itself.", "Recursive step: a child inherits its parent's root_id.",
               "Join products on the mapped category, then aggregate by root."],
        approach="Recursive mapping (14 rows), then the usual revenue join, grouped by the root category.",
        complexity="Recursion is O(categories); the aggregate is linear in order lines.",
        pitfalls="- A non-recursive join on `parent_id` handles only one level and misses *Laptops* (two levels below *Electronics*).\n- Products attached directly to a root (e.g. *Smart Watch* under *Electronics*) must map to themselves - the anchor handles that.",
    ),
),
dict(
    id="sql-referral-network-size",
    title="Referral Network Size",
    difficulty="Hard",
    pattern="Recursive CTE",
    kind="sql",
    dataset="shop",
    description=r"""
`customers.referred_by` stores who referred each customer. A customer's **referral network** is
everyone they referred directly, plus everyone those people referred, and so on.

For every customer with a non-empty network, report the number of direct referrals and the total
network size.

**Table** (dataset `shop`):
`customers(customer_id, first_name, last_name, email, city, country, signup_date, referred_by)`

**Columns, in this order:** `customer_id`, `direct_referrals`, `network_size`

**Order:** by `network_size` descending, then `customer_id`.
""",
    starter=STARTER,
    solution="""WITH RECURSIVE net(ancestor, member, depth) AS (
  SELECT referred_by, customer_id, 1
  FROM customers
  WHERE referred_by IS NOT NULL
  UNION ALL
  SELECT n.ancestor, c.customer_id, n.depth + 1
  FROM net n
  JOIN customers c ON c.referred_by = n.member
)
SELECT ancestor AS customer_id,
       SUM(CASE WHEN depth = 1 THEN 1 ELSE 0 END) AS direct_referrals,
       COUNT(*) AS network_size
FROM net
GROUP BY ancestor
ORDER BY network_size DESC, customer_id;""",
    ordered=True,
    guide=dict(
        prereqs="Recursive CTEs; transitive closure.",
        intuition="Compute the *transitive closure* of the referral relation: every (ancestor, descendant) pair. Then counting descendants per ancestor is a GROUP BY.",
        hints=["Anchor: every direct pair (referred_by, customer_id) at depth 1.",
               "Recursive step: extend a pair (a, m) with m's own referrals.",
               "Direct referrals are the depth-1 pairs."],
        approach="Generate all ancestor-descendant pairs with depth, then aggregate. Because each customer has at most one referrer, the graph is a forest and each pair appears once.",
        complexity="O(total pairs) = O(n x depth).",
        pitfalls="- Recursing only from roots and carrying the root id would credit only the top of each chain, not intermediate referrers.\n- If the data could contain a cycle, add `WHERE depth < 50` or track visited ids.",
    ),
),
dict(
    id="sql-longest-login-streak",
    title="Longest Login Streak",
    difficulty="Hard",
    pattern="Gaps & islands",
    kind="sql",
    dataset="shop",
    description=r"""
The `logins` table has one row per customer per day they logged in (March 2024). A **streak** is a
run of consecutive calendar days. For each customer find the **length of their longest streak** and
the date it started (if several streaks tie for longest, report the earliest one).

**Table** (dataset `shop`): `logins(customer_id, login_date)` - primary key `(customer_id, login_date)`

**Columns, in this order:** `customer_id`, `longest_streak`, `streak_start`

**Order:** by `longest_streak` descending, then `customer_id`.
""",
    starter=STARTER,
    solution="""WITH g AS (
  SELECT customer_id, login_date,
         julianday(login_date) - ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY login_date) AS grp
  FROM logins
), islands AS (
  SELECT customer_id, MIN(login_date) AS streak_start, COUNT(*) AS len
  FROM g
  GROUP BY customer_id, grp
), ranked AS (
  SELECT customer_id, streak_start, len,
         ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY len DESC, streak_start) AS rn
  FROM islands
)
SELECT customer_id, len AS longest_streak, streak_start
FROM ranked
WHERE rn = 1
ORDER BY longest_streak DESC, customer_id;""",
    ordered=True,
    guide=dict(
        prereqs="ROW_NUMBER; date arithmetic; the gaps-and-islands lesson.",
        intuition="Inside a run of consecutive days, the date and the row number both go up by 1 each row, so **date minus row number is constant**. That constant labels the island.",
        hints=["`julianday(login_date) - ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY login_date)`.",
               "GROUP BY (customer_id, grp): each group is one streak.",
               "Pick the longest streak per customer with another ROW_NUMBER."],
        brute_force="Self-join each login to the next day and walk chains - messy and O(n^2).",
        approach="""Dry run for dates 1, 2, 3, 6, 7 March:
row numbers 1..5, day numbers 1,2,3,6,7 -> differences 0,0,0,1,1 -> two islands of lengths 3 and 2.""",
        complexity="Two sorts per customer: O(n log n).",
        pitfalls="- Duplicate dates break the trick; DISTINCT first (the primary key prevents them here).\n- In PostgreSQL use `login_date - ROW_NUMBER() ... * INTERVAL '1 day'` or `login_date - rn::int`; in MySQL `DATE_SUB(login_date, INTERVAL rn DAY)`.",
    ),
),
dict(
    id="sql-dedupe-imports",
    title="Deduplicate the Import File",
    difficulty="Medium",
    pattern="Deduplication",
    kind="sql",
    dataset="shop",
    description=r"""
The `customer_imports` table contains the same person several times with differently formatted
emails (upper case, leading spaces). Treat two rows as duplicates when `lower(trim(email))` matches,
and keep only the **earliest** import (`imported_at`) of each person.

**Table** (dataset `shop`): `customer_imports(import_id, email, full_name, source, imported_at)`

**Columns, in this order:** `email` (normalised), `full_name`, `source`, `imported_at`, `copies`
(how many rows shared that normalised email)

**Order:** by `email`.
""",
    starter=STARTER,
    solution="""WITH n AS (
  SELECT lower(trim(email)) AS email, full_name, source, imported_at, import_id,
         ROW_NUMBER() OVER (PARTITION BY lower(trim(email)) ORDER BY imported_at, import_id) AS rn,
         COUNT(*) OVER (PARTITION BY lower(trim(email))) AS copies
  FROM customer_imports
)
SELECT email, full_name, source, imported_at, copies
FROM n
WHERE rn = 1
ORDER BY email;""",
    ordered=True,
    guide=dict(
        prereqs="ROW_NUMBER, COUNT(*) OVER, string normalisation.",
        intuition="Normalise the key, number rows inside each key group by time, keep number 1. A windowed COUNT gives the group size without collapsing rows.",
        hints=["Partition by the *normalised* email.", "Order by imported_at, with import_id as tie-breaker.", "`COUNT(*) OVER (PARTITION BY ...)` for copies."],
        approach="One CTE with two window functions; filter rn = 1. To physically delete duplicates: `DELETE FROM customer_imports WHERE import_id IN (SELECT import_id FROM n WHERE rn > 1)`.",
        complexity="One sort by (key, time): O(n log n).",
        pitfalls="- Partitioning by the raw email leaves ' a@x.com' and 'A@X.COM' as distinct people.\n- `GROUP BY email` with `MIN(imported_at)` gives the time but not the matching `source` - the bare-column trap again.",
    ),
),
dict(
    id="sql-cohort-retention",
    title="Month-1 Cohort Retention",
    difficulty="Hard",
    pattern="Cohort analysis",
    kind="sql",
    dataset="shop",
    description=r"""
Group customers into **cohorts by signup month**. A customer is *retained in month 1* if they placed
at least one order (any status) during the **calendar month right after** their signup month
(for a January signup: any day in February).

**Tables** (dataset `shop`):

- `customers(customer_id, first_name, last_name, email, city, country, signup_date, referred_by)`
- `orders(order_id, customer_id, order_date, status, shipping_fee)`

**Columns, in this order:** `cohort_month` (`'YYYY-MM'`), `cohort_size`, `retained_m1`,
`retention_pct` (`100.0 * retained / size`, rounded to 1)

**Order:** by `cohort_month`.
""",
    starter=STARTER,
    solution="""WITH cohort AS (
  SELECT customer_id,
         strftime('%Y-%m', signup_date) AS cohort_month,
         date(signup_date, 'start of month') AS cohort_start
  FROM customers
), retained AS (
  SELECT DISTINCT c.customer_id
  FROM cohort c
  JOIN orders o ON o.customer_id = c.customer_id
  WHERE o.order_date >= date(c.cohort_start, '+1 month')
    AND o.order_date <  date(c.cohort_start, '+2 months')
)
SELECT c.cohort_month,
       COUNT(*) AS cohort_size,
       COUNT(r.customer_id) AS retained_m1,
       ROUND(100.0 * COUNT(r.customer_id) / COUNT(*), 1) AS retention_pct
FROM cohort c
LEFT JOIN retained r ON r.customer_id = c.customer_id
GROUP BY c.cohort_month
ORDER BY c.cohort_month;""",
    ordered=True,
    guide=dict(
        prereqs="Date functions, DISTINCT, LEFT JOIN, COUNT(column).",
        intuition="Two facts per customer: which cohort they belong to, and whether they were active in the following month. Then a grouped ratio.",
        hints=["`date(signup_date, 'start of month')` gives the first day of the signup month.",
               "Month 1 is the half-open range [start + 1 month, start + 2 months).",
               "DISTINCT so a customer with three orders in month 1 counts once; LEFT JOIN so cohorts keep everyone."],
        approach="Cohort CTE, retained-customer CTE, left join, conditional count. Extending to months 2, 3, ... gives the classic retention triangle (one column per month offset via CASE).",
        complexity="Linear in orders with an index on `orders(customer_id, order_date)`.",
        pitfalls="""- Inner join drops cohorts' non-retained customers and inflates the rate to 100%.
- *30 days after signup* and *the next calendar month* are different definitions; state which one you use in an interview.
- PostgreSQL: `date_trunc('month', signup_date) + interval '1 month'`; MySQL: `DATE_ADD(..., INTERVAL 1 MONTH)`.""",
    ),
),
dict(
    id="sql-sessionize-events",
    title="Sessionize Clickstream Events",
    difficulty="Hard",
    pattern="Sessionization",
    kind="sql",
    dataset="shop",
    description=r"""
Split each customer's `web_events` into **sessions**: a new session starts at a customer's first
event, and whenever more than **30 minutes** have passed since that customer's previous event.

**Table** (dataset `shop`): `web_events(event_id, customer_id, event_time, event_type, page)`

**Columns, in this order:** `customer_id`, `sessions`, `events`, `avg_events_per_session` (rounded to 2)

**Order:** by `sessions` descending, then `customer_id`.
""",
    starter=STARTER,
    solution="""WITH flagged AS (
  SELECT customer_id, event_time,
         CASE WHEN LAG(event_time) OVER w IS NULL
                OR (julianday(event_time) - julianday(LAG(event_time) OVER w)) * 1440 > 30
              THEN 1 ELSE 0 END AS new_session
  FROM web_events
  WINDOW w AS (PARTITION BY customer_id ORDER BY event_time)
), numbered AS (
  SELECT customer_id,
         SUM(new_session) OVER (PARTITION BY customer_id ORDER BY event_time
                                ROWS UNBOUNDED PRECEDING) AS session_no
  FROM flagged
)
SELECT customer_id,
       COUNT(DISTINCT session_no) AS sessions,
       COUNT(*) AS events,
       ROUND(1.0 * COUNT(*) / COUNT(DISTINCT session_no), 2) AS avg_events_per_session
FROM numbered
GROUP BY customer_id
ORDER BY sessions DESC, customer_id;""",
    ordered=True,
    guide=dict(
        prereqs="LAG, running SUM, named WINDOW clause.",
        intuition="Flag the *start* of each session with a 1 (the gap is large), then a running sum of the flags numbers the sessions 1, 2, 3, ...",
        hints=["Gap in minutes: `(julianday(t) - julianday(LAG(t) OVER w)) * 1440`.",
               "First event of a customer has LAG = NULL - treat it as a new session.",
               "`SUM(flag) OVER (... ROWS UNBOUNDED PRECEDING)` assigns session numbers."],
        approach="Flag -> cumulative sum -> aggregate. This *flag-and-sum* trick is the general tool for grouping consecutive rows by any rule.",
        complexity="One sort by (customer, time); linear afterwards.",
        pitfalls="- `> 30` vs `>= 30` changes the result at exactly 30 minutes; follow the spec.\n- Forgetting PARTITION BY lets one customer's events continue another customer's session.",
    ),
),
dict(
    id="sql-median-order-value",
    title="Median Order Value by Country",
    difficulty="Hard",
    pattern="Median",
    kind="sql",
    dataset="shop",
    description=r"""
SQLite has no `MEDIAN` function. Compute the **median delivered-order value** per customer country,
where an order's value is `SUM(quantity * unit_price * (1 - discount))` over its items. For an even
number of orders, the median is the average of the two middle values.

**Tables** (dataset `shop`): `customers(customer_id, ..., country, ...)`, `orders(order_id, customer_id, order_date, status, shipping_fee)`,
`order_items(order_item_id, order_id, product_id, quantity, unit_price, discount)`

**Columns, in this order:** `country`, `orders`, `median_value` (rounded to 2)

**Order:** by `country`.
""",
    starter=STARTER,
    solution="""WITH ov AS (
  SELECT o.order_id, c.country,
         SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS v
  FROM orders o
  JOIN customers c    ON c.customer_id = o.customer_id
  JOIN order_items oi ON oi.order_id = o.order_id
  WHERE o.status = 'delivered'
  GROUP BY o.order_id, c.country
), r AS (
  SELECT country, v,
         ROW_NUMBER() OVER (PARTITION BY country ORDER BY v) AS rn,
         COUNT(*)     OVER (PARTITION BY country) AS n
  FROM ov
)
SELECT country, n AS orders, ROUND(AVG(v), 2) AS median_value
FROM r
WHERE rn IN ((n + 1) / 2, (n + 2) / 2)
GROUP BY country, n
ORDER BY country;""",
    ordered=True,
    guide=dict(
        prereqs="ROW_NUMBER, COUNT(*) OVER, integer division.",
        intuition="Sort each country's values, number them, and pick the middle position(s). With integer division, `(n+1)/2` and `(n+2)/2` are the same row when n is odd and the two middle rows when n is even.",
        hints=["Aggregate to one row per order first.", "Number rows within each country and count the partition.",
               "Average the one or two middle rows."],
        approach="Dry run, n = 4: (5/2, 6/2) = (2, 3) -> average rows 2 and 3. n = 5: (3, 3) -> row 3.",
        complexity="One sort per country: O(n log n).",
        pitfalls="- PostgreSQL has `percentile_cont(0.5) WITHIN GROUP (ORDER BY v)`; MySQL has neither - use this pattern.\n- `AVG` is the mean, not the median; order values are skewed by laptops.",
    ),
),
dict(
    id="sql-fraud-metric-pivot",
    title="Pivot Run Metrics",
    difficulty="Medium",
    pattern="Pivoting",
    kind="sql",
    dataset="mlops",
    description=r"""
`metrics` is stored in **long** format (one row per run x metric x step). Produce a **wide** table for
the experiment named `'fraud-detector'`: one row per finished run with its final `accuracy`, `f1`
and `auc` as columns.

**Tables** (dataset `mlops`):

- `experiments(experiment_id, name, ...)`
- `runs(run_id, experiment_id, ..., model_type, ..., status, ...)`
- `metrics(run_id, metric_name, step, value)`

**Columns, in this order:** `run_id`, `model_type`, `accuracy`, `f1`, `auc`

**Order:** by `auc` descending, then `run_id`.
""",
    starter=STARTER,
    solution="""SELECT r.run_id, r.model_type,
       MAX(CASE WHEN m.metric_name = 'accuracy' THEN m.value END) AS accuracy,
       MAX(CASE WHEN m.metric_name = 'f1'       THEN m.value END) AS f1,
       MAX(CASE WHEN m.metric_name = 'auc'      THEN m.value END) AS auc
FROM experiments e
JOIN runs r    ON r.experiment_id = e.experiment_id
JOIN metrics m ON m.run_id = r.run_id
WHERE e.name = 'fraud-detector' AND r.status = 'FINISHED'
GROUP BY r.run_id, r.model_type
ORDER BY auc DESC, r.run_id;""",
    ordered=True,
    guide=dict(
        prereqs="CASE inside aggregates (selective aggregation).",
        intuition="Group to one row per run; each output column picks out *its* metric with a CASE that is NULL for every other metric, and MAX ignores the NULLs.",
        hints=["GROUP BY run.", "`MAX(CASE WHEN metric_name = 'auc' THEN value END)`.", "Filter the experiment by name through a join."],
        approach="Join, filter, group, three CASE-in-MAX columns. The same pattern works in every SQL dialect; SQL Server and Oracle also offer a PIVOT clause.",
        complexity="Linear in the experiment's metric rows.",
        pitfalls="- SUM instead of MAX would add values if a metric were logged at several steps.\n- Leaving out GROUP BY gives a single row.",
    ),
),
dict(
    id="sql-quarterly-partition-summary",
    title="Quarterly Partition Summary",
    difficulty="Easy",
    pattern="Partitioning",
    kind="sql",
    dataset="bank",
    description=r"""
The bank plans to **range-partition** the `txn` table by quarter. Before choosing boundaries, the DBA
wants to see how many rows and how much money each quarterly partition would hold.

**Table** (dataset `bank`): `txn(txn_id, txn_date, account_id, txn_type_cd, amount, ...)`

**Columns, in this order:** `partition_key` (text like `'2024Q1'`), `row_count`, `total_amount` (rounded to 2),
`first_txn`, `last_txn` (min and max `txn_date` in the partition)

**Order:** by `partition_key`.
""",
    starter=STARTER,
    solution="""SELECT strftime('%Y', txn_date) || 'Q' || ((CAST(strftime('%m', txn_date) AS INTEGER) + 2) / 3) AS partition_key,
       COUNT(*) AS row_count,
       ROUND(SUM(amount), 2) AS total_amount,
       MIN(txn_date) AS first_txn,
       MAX(txn_date) AS last_txn
FROM txn
GROUP BY partition_key
ORDER BY partition_key;""",
    ordered=True,
    guide=dict(
        prereqs="Lesson *Partitioning and sharding*; date functions; CAST.",
        intuition="A partition key is just an expression that maps each row to a bucket. Grouping by that expression previews the partitions.",
        hints=["Month number: `CAST(strftime('%m', txn_date) AS INTEGER)`.", "Quarter = (month + 2) / 3 with integer division.",
               "Concatenate year, 'Q', quarter."],
        approach="Build the key expression, group by it, aggregate.",
        complexity="One scan.",
        pitfalls="- Without CAST, `'03' + 2` works in SQLite by coercion but `/ 3` on text is risky elsewhere.\n- Very uneven partitions (data skew) defeat the purpose of partitioning; that is what this check reveals.",
    ),
),
dict(
    id="sql-production-model-accuracy",
    title="Live Accuracy of Production Models",
    difficulty="Medium",
    pattern="Views & reporting",
    kind="sql",
    dataset="mlops",
    description=r"""
Build the query behind a *model health* view: for each **production** deployment, compare predictions
with ground truth. Only predictions whose `actual_label` is known (not NULL) count toward accuracy.

**Tables** (dataset `mlops`):

- `models(model_id, name, version, run_id, stage, registered_at)`
- `deployments(deployment_id, model_id, environment, deployed_at, retired_at, replicas)`
- `predictions(prediction_id, deployment_id, predicted_at, predicted_label, actual_label, score, latency_ms)`

**Columns, in this order:** `deployment_id`, `model` (`name || ':v' || version`, e.g. `'fraud-model:v9'`),
`predictions` (all), `labeled` (with known actual), `accuracy_pct`
(`100.0 * correct / labeled`, rounded to 1), `p_label_coverage` (`100.0 * labeled / predictions`, rounded to 1)

**Order:** by `deployment_id`.
""",
    starter=STARTER,
    solution="""SELECT d.deployment_id,
       m.name || ':v' || m.version AS model,
       COUNT(*) AS predictions,
       COUNT(p.actual_label) AS labeled,
       ROUND(100.0 * SUM(CASE WHEN p.actual_label = p.predicted_label THEN 1 ELSE 0 END)
             / COUNT(p.actual_label), 1) AS accuracy_pct,
       ROUND(100.0 * COUNT(p.actual_label) / COUNT(*), 1) AS p_label_coverage
FROM deployments d
JOIN models m      ON m.model_id = d.model_id
JOIN predictions p ON p.deployment_id = d.deployment_id
WHERE d.environment = 'production'
GROUP BY d.deployment_id, m.name, m.version
ORDER BY d.deployment_id;""",
    ordered=True,
    guide=dict(
        prereqs="Views (module *Views and metadata*), COUNT(column) vs COUNT(*), NULL comparisons.",
        intuition="NULL-aware counting does the heavy lifting: `COUNT(actual_label)` counts labeled rows, and `actual = predicted` is UNKNOWN (so not counted) when the label is missing.",
        hints=["Join deployments -> models and deployments -> predictions.",
               "`COUNT(p.actual_label)` = labeled rows.",
               "Wrap the final query in `CREATE VIEW model_health AS ...` in your own sandbox."],
        approach="Three-table join, filter production, group per deployment, NULL-aware counts and ratios.",
        complexity="Linear in predictions.",
        pitfalls="- Dividing by COUNT(*) instead of COUNT(actual_label) understates accuracy by treating unlabeled rows as wrong.\n- A deployment with zero labeled predictions would divide by zero - SQLite returns NULL; PostgreSQL raises an error, so guard with NULLIF(COUNT(...), 0).",
    ),
),
dict(
    id="sql-denormalized-order-summary",
    title="Denormalized Order Summary",
    difficulty="Medium",
    pattern="Normalization & denormalization",
    kind="sql",
    dataset="shop",
    description=r"""
The analytics team wants a wide, **denormalized** reporting table with one row per order, so that
dashboards do not need joins. Produce its contents for orders placed in **December 2024**.

**Tables** (dataset `shop`): `customers`, `orders`, `order_items` (see schema browser)

**Columns, in this order:**
`order_id`, `order_date`, `customer` (`first_name || ' ' || last_name`), `country`, `status`,
`items` (sum of quantities), `subtotal` (sum of `quantity * unit_price * (1 - discount)`, rounded to 2),
`total` (subtotal + `shipping_fee`, rounded to 2)

**Order:** by `order_date`, then `order_id`.
""",
    starter=STARTER,
    solution="""SELECT o.order_id, o.order_date,
       c.first_name || ' ' || c.last_name AS customer,
       c.country, o.status,
       SUM(oi.quantity) AS items,
       ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)), 2) AS subtotal,
       ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) + o.shipping_fee, 2) AS total
FROM orders o
JOIN customers c    ON c.customer_id = o.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.order_date >= '2024-12-01' AND o.order_date < '2025-01-01'
GROUP BY o.order_id, o.order_date, c.first_name, c.last_name, c.country, o.status, o.shipping_fee
ORDER BY o.order_date, o.order_id;""",
    ordered=True,
    guide=dict(
        prereqs="Normalization (lesson *Normal forms*), joins, grouping.",
        intuition="The normalized schema stores each fact once; a reporting table deliberately repeats customer facts on every order row. Build it by joining back and aggregating lines to the order grain.",
        hints=["Join customers and order_items to orders.", "GROUP BY every order-level column.",
               "Add `shipping_fee` once per order - *outside* the SUM."],
        approach="Join, filter the month with a half-open range, aggregate lines per order, compute totals.",
        complexity="Linear in the month's order lines.",
        pitfalls="- `SUM(... + o.shipping_fee)` adds shipping once per *line* - a fan-out bug.\n- Denormalized copies go stale when a customer moves country; refresh or accept point-in-time semantics.",
    ),
),
]
