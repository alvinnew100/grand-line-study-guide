"""SQL track problems, part 6: analytics interview set on the `saas` dataset."""

STARTER = "-- write your query\nSELECT "

ACCOUNTS = "- `accounts(account_id, company, industry, country, created_on, parent_account_id)` - `parent_account_id` is NULL for a top-level company, otherwise the account that owns it"
USERS = "- `app_users(user_id, account_id, email, role, created_on, last_login)` - `email` was typed by hand: mixed case and stray spaces occur"
SUBS = "- `subscriptions(subscription_id, account_id, plan, mrr, started_on, ended_on)` - `plan` is `free`, `starter`, `pro` or `enterprise`; `mrr` is monthly recurring revenue; `ended_on` is NULL while the subscription is active; an account has a sequence of subscriptions over time"
INVOICES = "- `invoices(invoice_id, account_id, issued_on, amount, paid_on, status)` - `status` is `paid`, `open` or `void`; `paid_on` is NULL unless paid"
FEATURES = "- `features(feature_name, is_core)` - the product's features; `is_core` is 1 or 0"
EVENTS = "- `events(event_id, account_id, user_id, event_name, occurred_at)` - product usage; `event_name` is `signup` or a feature name; `occurred_at` is text like `'2024-10-07 18:22:05'`"
TICKETS = "- `tickets(ticket_id, account_id, opened_at, closed_at, priority, category, csat)` - `closed_at` is NULL while open; `csat` (1-5) is NULL when the customer did not answer the survey"


def P(pid, title, difficulty, pattern, tables, task, columns, order, solution, guide, ordered=True):
    desc = task.strip() + "\n\n**Tables** (dataset `saas`):\n\n" + "\n".join(tables) + "\n\n**Columns, in this order:** " + columns
    desc += "\n\n**Order:** " + order if order else "\n\nAny row order is accepted."
    return dict(id=pid, title=title, difficulty=difficulty, pattern=pattern, kind="sql", dataset="saas",
                description=desc, starter=STARTER, solution=solution.strip(), ordered=ordered, guide=guide)


def G(prereqs, intuition, hints, approach, pitfalls, complexity, follow_up=None):
    g = dict(prereqs=prereqs, intuition=intuition, hints=hints, approach=approach, pitfalls=pitfalls,
             complexity=complexity)
    if follow_up:
        g["follow_up"] = follow_up
    return g


PROBLEMS = [
P("sql-mrr-by-plan", "Current MRR by Plan", "Easy", "Percent of total",
  [SUBS],
  "Report the company's current monthly recurring revenue by plan. A subscription is *current* when `ended_on` is NULL.",
  "`plan`, `subscriptions`, `mrr` (rounded to 2), `pct_of_mrr` (rounded to 1)",
  "by `mrr` descending, then `plan`.",
  """
SELECT plan,
       COUNT(*) AS subscriptions,
       ROUND(SUM(mrr), 2) AS mrr,
       ROUND(100.0 * SUM(mrr) / (SELECT SUM(mrr) FROM subscriptions WHERE ended_on IS NULL), 1) AS pct_of_mrr
FROM subscriptions
WHERE ended_on IS NULL
GROUP BY plan
ORDER BY mrr DESC, plan;""",
  G("IS NULL, GROUP BY, scalar subqueries.",
    "Filter to current subscriptions, total per plan, and divide each total by the grand total.",
    ["`WHERE ended_on IS NULL` - not `= NULL`.", "The denominator must use the same filter as the numerator.", "A window total `SUM(SUM(mrr)) OVER ()` is an alternative to the subquery."],
    "Filter, group, divide by a total computed over the same filtered rows.",
    "- `ended_on = NULL` matches nothing.\n- A denominator over *all* subscriptions (including ended ones) makes the percentages sum to less than 100.\n- Free plans contribute 0 MRR but still count as subscriptions.",
    "Two scans of a small table.")),

P("sql-csat-by-category", "Survey Scores by Ticket Category", "Easy", "NULL handling traps",
  [TICKETS],
  "After a ticket is closed the customer may answer a satisfaction survey (`csat`, 1-5). For closed tickets, report per category how many were closed, how many surveys were answered, the response rate and the average score of the answered surveys.",
  "`category`, `closed_tickets`, `responses`, `response_rate_pct` (rounded to 1), `avg_csat` (rounded to 2)",
  "by `avg_csat` descending, then `category`.",
  """
SELECT category,
       COUNT(*) AS closed_tickets,
       COUNT(csat) AS responses,
       ROUND(100.0 * COUNT(csat) / COUNT(*), 1) AS response_rate_pct,
       ROUND(AVG(csat), 2) AS avg_csat
FROM tickets
WHERE closed_at IS NOT NULL
GROUP BY category
ORDER BY avg_csat DESC, category;""",
  G("COUNT(*) vs COUNT(column), AVG and NULL.",
    "A missing survey is 'unknown', not 'zero'. `COUNT(csat)` counts answers, and `AVG(csat)` averages answers only - exactly the behaviour wanted.",
    ["Closed tickets: `closed_at IS NOT NULL`.", "`COUNT(csat)` skips NULLs; `COUNT(*)` does not.", "`AVG(csat)` already ignores unanswered surveys."],
    "One grouped pass; NULL-aware aggregates do the work.",
    "- `AVG(COALESCE(csat, 0))` treats silence as the worst score and drags every average down.\n- `SUM(csat) / COUNT(*)` makes the same mistake, and is integer division.\n- A low response rate means the average rests on few answers - report both.",
    "Single pass.")),

P("sql-user-email-types", "Company versus Personal Emails", "Easy", "String cleaning",
  [USERS],
  "User emails were entered by hand, so they contain upper-case letters and leading or trailing spaces. Clean each email with `lower(trim(email))`, take the part after the `@` as the domain, and classify the user as `'personal'` if the domain is `gmail.com`, `yahoo.com` or `outlook.com`, otherwise `'company'`.",
  "`email_type`, `users`, `accounts` (distinct accounts with at least one such user), `pct_of_users` (rounded to 1)",
  "by `users` descending.",
  """
WITH c AS (
  SELECT account_id, lower(trim(email)) AS email FROM app_users
), d AS (
  SELECT account_id, substr(email, instr(email, '@') + 1) AS domain FROM c
)
SELECT CASE WHEN domain IN ('gmail.com', 'yahoo.com', 'outlook.com') THEN 'personal' ELSE 'company' END AS email_type,
       COUNT(*) AS users,
       COUNT(DISTINCT account_id) AS accounts,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM app_users), 1) AS pct_of_users
FROM d
GROUP BY email_type
ORDER BY users DESC;""",
  G("String functions: `lower`, `trim`, `instr`, `substr`.",
    "Clean first, then cut: once the text is trimmed and lower-cased, the domain is everything after the position of `@`.",
    ["`lower(trim(email))` in a first CTE so later steps use clean text.", "`substr(email, instr(email, '@') + 1)` is the domain.", "Classify with `IN (...)` inside a CASE, then group."],
    "Two tiny CTEs (clean, extract) and a grouped classification.",
    "- Without `lower`, `GMAIL.COM` is not recognised as personal.\n- Without `trim`, a trailing space makes the domain `'gmail.com '`.\n- MySQL: `SUBSTRING_INDEX(email, '@', -1)`; PostgreSQL: `split_part(email, '@', 2)`.",
    "Single pass.")),

P("sql-churned-accounts", "Churned Accounts", "Medium", "Anti-join",
  [ACCOUNTS, SUBS],
  "An account has *churned* if it has no current subscription (no row with `ended_on` NULL). List churned accounts with the date their last subscription ended, the plan they were on at that point, and how many days they were a customer (from their first `started_on` to the churn date).",
  "`account_id`, `company`, `churned_on`, `last_plan`, `lifetime_days`",
  "by `churned_on` descending, then `account_id`.",
  """
WITH last_sub AS (
  SELECT account_id, plan, ended_on,
         ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY ended_on DESC, subscription_id DESC) AS rn,
         MIN(started_on) OVER (PARTITION BY account_id) AS first_start
  FROM subscriptions
)
SELECT a.account_id, a.company, l.ended_on AS churned_on, l.plan AS last_plan,
       CAST(julianday(l.ended_on) - julianday(l.first_start) AS INTEGER) AS lifetime_days
FROM accounts a
JOIN last_sub l ON l.account_id = a.account_id AND l.rn = 1
WHERE NOT EXISTS (SELECT 1 FROM subscriptions s
                  WHERE s.account_id = a.account_id AND s.ended_on IS NULL)
ORDER BY churned_on DESC, a.account_id;""",
  G("NOT EXISTS, ROW_NUMBER for the latest row, date differences.",
    "Churn is defined by an absence - no active subscription - so start with an anti-join. The details of the final subscription are a top-1-per-group lookup.",
    ["`NOT EXISTS (... ended_on IS NULL)` identifies churned accounts.", "Latest subscription per account: ROW_NUMBER ordered by `ended_on DESC`.", "Lifetime: `julianday(churned) - julianday(first start)`."],
    "Rank subscriptions per account, keep the last one, restrict to accounts with no active subscription.",
    "- `MAX(ended_on)` alone is not enough: an account with an active (NULL) subscription also has ended ones, because MAX ignores NULL.\n- `GROUP BY account_id` with `MAX(ended_on), plan` returns an arbitrary plan.\n- Reactivated accounts (a gap, then a new active subscription) are not churned.",
    "One sort per account.")),

P("sql-plan-transitions", "Plan Upgrade and Downgrade Paths", "Medium", "LAG / LEAD",
  [SUBS],
  "Each account moves through a sequence of subscriptions. Count how often each transition `from_plan -> to_plan` occurred between consecutive subscriptions of the same account (ordered by `started_on`), and label it `'upgrade'`, `'downgrade'` or `'same'` using the order free < starter < pro < enterprise.",
  "`from_plan`, `to_plan`, `transitions`, `direction`",
  "by `transitions` descending, then `from_plan`, then `to_plan`.",
  """
WITH seq AS (
  SELECT account_id, plan AS to_plan,
         LAG(plan) OVER (PARTITION BY account_id ORDER BY started_on, subscription_id) AS from_plan
  FROM subscriptions
), ranked AS (
  SELECT from_plan, to_plan,
         CASE from_plan WHEN 'free' THEN 1 WHEN 'starter' THEN 2 WHEN 'pro' THEN 3 ELSE 4 END AS from_level,
         CASE to_plan   WHEN 'free' THEN 1 WHEN 'starter' THEN 2 WHEN 'pro' THEN 3 ELSE 4 END AS to_level
  FROM seq
  WHERE from_plan IS NOT NULL
)
SELECT from_plan, to_plan, COUNT(*) AS transitions,
       CASE WHEN to_level > from_level THEN 'upgrade'
            WHEN to_level < from_level THEN 'downgrade'
            ELSE 'same' END AS direction
FROM ranked
GROUP BY from_plan, to_plan
ORDER BY transitions DESC, from_plan, to_plan;""",
  G("LAG with PARTITION BY, simple CASE for ordering labels.",
    "A transition is a pair (previous row's plan, this row's plan) within one account. LAG produces the pair; the first subscription of each account has no predecessor and is dropped.",
    ["`LAG(plan) OVER (PARTITION BY account_id ORDER BY started_on)`.", "Remove rows where the previous plan is NULL.", "Map plan names to numbers to compare them."],
    "Pair up consecutive rows, translate plans to levels, group by the pair.",
    "- Without PARTITION BY the last plan of one account pairs with the first plan of the next.\n- Comparing plan names as text (`'pro' > 'free'`) is alphabetical, not commercial, order.\n- 'same' transitions are renewals or reactivations on the same plan.",
    "One sort by (account, start date).")),

P("sql-open-invoice-aging", "Open Invoice Aging", "Medium", "Histograms and bucketing",
  [INVOICES],
  "Finance tracks unpaid invoices by age. For invoices with status `open`, compute the age in days as of **2024-12-31** and bucket into `'0-30'`, `'31-60'`, `'61-90'` and `'90+'`.",
  "`age_bucket`, `invoices`, `amount_due` (rounded to 2), `pct_of_amount` (rounded to 1)",
  "`'0-30'`, `'31-60'`, `'61-90'`, `'90+'` (only buckets that contain invoices appear).",
  """
WITH o AS (
  SELECT amount, CAST(julianday('2024-12-31') - julianday(issued_on) AS INTEGER) AS age_days
  FROM invoices
  WHERE status = 'open'
)
SELECT CASE WHEN age_days <= 30 THEN '0-30'
            WHEN age_days <= 60 THEN '31-60'
            WHEN age_days <= 90 THEN '61-90'
            ELSE '90+' END AS age_bucket,
       COUNT(*) AS invoices,
       ROUND(SUM(amount), 2) AS amount_due,
       ROUND(100.0 * SUM(amount) / (SELECT SUM(amount) FROM o), 1) AS pct_of_amount
FROM o
GROUP BY age_bucket
ORDER BY MIN(age_days);""",
  G("Date differences, CASE bucketing, percent of total.",
    "Compute an age per invoice against a fixed reference date, label it, and summarise by label.",
    ["Age: `julianday('2024-12-31') - julianday(issued_on)`.", "Use the fixed date, not `'now'`, so the answer is reproducible.", "Order buckets by `MIN(age_days)`."],
    "CTE with ages, CASE labels, grouped totals and shares.",
    "- `'now'` makes the result change every day.\n- Void invoices are not owed; paid invoices are not open - filter on status.\n- Sorting labels as text puts '90+' in the wrong place in general; use a numeric key.",
    "Single pass.")),

P("sql-slow-paying-accounts", "Slow-Paying Accounts", "Medium", "Date arithmetic",
  [INVOICES, ACCOUNTS],
  "Among paid invoices, *days to pay* is the number of days from `issued_on` to `paid_on`. Find accounts with at least 4 paid invoices whose average days to pay exceeds 25, and show how many of their invoices took more than 30 days.",
  "`account_id`, `company`, `paid_invoices`, `avg_days_to_pay` (rounded to 1), `late_invoices`",
  "by `avg_days_to_pay` descending, then `account_id`.",
  """
SELECT a.account_id, a.company,
       COUNT(*) AS paid_invoices,
       ROUND(AVG(julianday(i.paid_on) - julianday(i.issued_on)), 1) AS avg_days_to_pay,
       SUM(CASE WHEN julianday(i.paid_on) - julianday(i.issued_on) > 30 THEN 1 ELSE 0 END) AS late_invoices
FROM invoices i
JOIN accounts a ON a.account_id = i.account_id
WHERE i.status = 'paid'
GROUP BY a.account_id, a.company
HAVING COUNT(*) >= 4
   AND AVG(julianday(i.paid_on) - julianday(i.issued_on)) > 25
ORDER BY avg_days_to_pay DESC, a.account_id;""",
  G("`julianday` differences, HAVING with two aggregate conditions.",
    "Days to pay is a per-invoice difference; the question is about per-account averages and counts of that difference.",
    ["`julianday(paid_on) - julianday(issued_on)` per invoice.", "Row filter (`status = 'paid'`) in WHERE; both group conditions in HAVING.", "Late count: a conditional SUM."],
    "Filter, group by account, average the difference, filter groups.",
    "- Subtracting the date strings directly yields 0 (year minus year).\n- Open invoices have NULL `paid_on`; they must not enter the average.\n- Filtering on the rounded alias in HAVING is not portable - repeat the expression.",
    "Single pass over invoices.")),

P("sql-ticket-resolution-by-priority", "Ticket Resolution by Priority", "Medium", "NULL handling traps",
  [TICKETS],
  "For each priority, report the number of tickets, how many are still open, the average hours to close (closed tickets only) and the percentage of closed tickets that were closed within 24 hours.",
  "`priority`, `tickets`, `still_open`, `avg_hours_to_close` (rounded to 1), `closed_within_24h_pct` (rounded to 1)",
  "`urgent`, `high`, `normal`, `low`.",
  """
SELECT priority,
       COUNT(*) AS tickets,
       COUNT(*) - COUNT(closed_at) AS still_open,
       ROUND(AVG((julianday(closed_at) - julianday(opened_at)) * 24), 1) AS avg_hours_to_close,
       ROUND(100.0 * SUM(CASE WHEN (julianday(closed_at) - julianday(opened_at)) * 24 <= 24 THEN 1 ELSE 0 END)
             / COUNT(closed_at), 1) AS closed_within_24h_pct
FROM tickets
GROUP BY priority
ORDER BY CASE priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 WHEN 'normal' THEN 3 ELSE 4 END;""",
  G("NULL propagation in arithmetic, COUNT(column), CASE in ORDER BY.",
    "For an open ticket the duration is NULL (arithmetic with NULL), so AVG skips it automatically and the `<= 24` test is UNKNOWN - counted as 0. Only the denominator needs care.",
    ["Open tickets: `COUNT(*) - COUNT(closed_at)`.", "Hours: `(julianday(closed_at) - julianday(opened_at)) * 24`.", "Divide the within-24h count by `COUNT(closed_at)`, not `COUNT(*)`."],
    "One grouped pass that relies on NULL propagation, with a custom sort order.",
    "- Dividing by `COUNT(*)` treats open tickets as 'not closed within 24h' and understates the rate.\n- Replacing NULL `closed_at` with today's date mixes open and closed tickets in the average.\n- Alphabetical order (high, low, normal, urgent) is not the business order.",
    "Single pass.")),

P("sql-weekly-active-accounts", "Weekly Active Accounts", "Medium", "Active-user metrics",
  [EVENTS],
  "For each week (Monday to Sunday) that starts between 2024-10-07 and 2024-11-25 inclusive, report the number of distinct accounts and distinct users with at least one event, and the number of events.",
  "`week_start` (the Monday, `'YYYY-MM-DD'`), `active_accounts`, `active_users`, `events`",
  "by `week_start`.",
  """
SELECT date(occurred_at, 'weekday 0', '-6 days') AS week_start,
       COUNT(DISTINCT account_id) AS active_accounts,
       COUNT(DISTINCT user_id) AS active_users,
       COUNT(*) AS events
FROM events
WHERE occurred_at >= '2024-10-07' AND occurred_at < '2024-12-02'
GROUP BY week_start
ORDER BY week_start;""",
  G("Truncating dates to the week, COUNT(DISTINCT).",
    "Map every timestamp to the Monday of its week, then count distinct entities per Monday.",
    ["In SQLite, `date(ts, 'weekday 0', '-6 days')` is the Monday of the week (move to Sunday, step back six days).", "Half-open range: the last wanted week starts 25 November and ends before 2 December.", "`COUNT(DISTINCT ...)` for accounts and users, `COUNT(*)` for events."],
    "Filter the range on the raw column, truncate to week start, aggregate.",
    "- `strftime('%W', ...)` week numbers reset at new year and do not give a date to plot.\n- PostgreSQL: `date_trunc('week', occurred_at)`; MySQL: `DATE_SUB(DATE(ts), INTERVAL WEEKDAY(ts) DAY)`.\n- The dataset contains duplicate event rows, so `events` counts those too - fine for this problem, see *Duplicate Events*.",
    "One pass plus a sort for the distinct counts.")),

P("sql-duplicate-events", "Duplicate Events", "Medium", "Duplicates and deduplication",
  [EVENTS],
  "A tracking bug sent some events twice: rows that are identical in `account_id`, `user_id`, `event_name` and `occurred_at` but have different `event_id`. For each event name report the number of rows, the number of distinct real events, and the number of surplus duplicate rows. Only list event names that have duplicates.",
  "`event_name`, `total_rows`, `distinct_events`, `duplicate_rows`",
  "by `duplicate_rows` descending, then `event_name`.",
  """
WITH g AS (
  SELECT event_name, COUNT(*) AS copies
  FROM events
  GROUP BY account_id, user_id, event_name, occurred_at
)
SELECT event_name,
       SUM(copies) AS total_rows,
       COUNT(*) AS distinct_events,
       SUM(copies) - COUNT(*) AS duplicate_rows
FROM g
GROUP BY event_name
HAVING SUM(copies) > COUNT(*)
ORDER BY duplicate_rows DESC, event_name;""",
  G("Grouping by a business key, two-level aggregation.",
    "Group by the columns that define 'the same event'; each group is one real event and its size is the number of copies. A second grouping summarises per event name.",
    ["Inner GROUP BY on the four identifying columns with `COUNT(*) AS copies`.", "Outer: rows = `SUM(copies)`, real events = `COUNT(*)`.", "Surplus = the difference; keep names where it is positive."],
    "Two aggregations. To delete the surplus rows you would keep `MIN(event_id)` per group, or use `ROW_NUMBER() ... > 1`.",
    "- `SELECT DISTINCT *` removes nothing because `event_id` differs.\n- `COUNT(*) - COUNT(DISTINCT occurred_at)` is wrong: different users can act in the same second.\n- Deciding which columns define identity is the real work.",
    "One hash aggregate on four columns.")),

P("sql-revenue-concentration", "Revenue Concentration", "Medium", "Running totals",
  [INVOICES, ACCOUNTS],
  "How concentrated is revenue? Total the **paid** invoices per account, rank accounts from largest to smallest, and compute each account's cumulative share of all paid revenue. Return the top accounts up to and including the first one whose cumulative share reaches 50%.",
  "`rnk`, `account_id`, `company`, `revenue` (rounded to 2), `cumulative_pct` (rounded to 1)",
  "by `rnk`.",
  """
WITH rev AS (
  SELECT account_id, SUM(amount) AS revenue
  FROM invoices
  WHERE status = 'paid'
  GROUP BY account_id
), cum AS (
  SELECT account_id, revenue,
         ROW_NUMBER() OVER (ORDER BY revenue DESC, account_id) AS rnk,
         SUM(revenue) OVER (ORDER BY revenue DESC, account_id
                            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running,
         SUM(revenue) OVER () AS total
  FROM rev
)
SELECT c.rnk, c.account_id, a.company,
       ROUND(c.revenue, 2) AS revenue,
       ROUND(100.0 * c.running / c.total, 1) AS cumulative_pct
FROM cum c JOIN accounts a ON a.account_id = c.account_id
WHERE c.running - c.revenue < 0.5 * c.total
ORDER BY c.rnk;""",
  G("Running totals with an explicit frame, percent of total with `OVER ()`.",
    "A Pareto analysis: sort descending, accumulate, divide by the grand total. 'Up to and including the account that crosses 50%' means: keep a row while the cumulative total *before* it is still under half.",
    ["Per-account totals in a CTE.", "`SUM(revenue) OVER (ORDER BY revenue DESC, account_id ROWS UNBOUNDED PRECEDING)` and `SUM(revenue) OVER ()`.", "The running total before the current row is `running - revenue`."],
    "Aggregate, accumulate, compare the previous cumulative value with half the total.",
    "- `WHERE cumulative_pct <= 50` drops the account that crosses the line.\n- With the default RANGE frame, accounts with equal revenue would jump together; a tie-breaker and a ROWS frame avoid it.\n- Filtering on rounded percentages can misplace the boundary.",
    "One aggregate and one sort.")),

P("sql-paying-but-inactive", "Paying Customers Who Stopped Using the Product", "Medium", "Anti-join",
  [SUBS, ACCOUNTS, EVENTS],
  "Customer success wants an early-warning list: accounts with a current **paid** subscription (`ended_on` NULL and `mrr > 0`) that have recorded **no events on or after 2024-12-01**. Include the date of their last event (NULL if they never had one).",
  "`account_id`, `company`, `plan`, `mrr`, `last_event_date`",
  "by `mrr` descending, then `account_id`.",
  """
SELECT a.account_id, a.company, s.plan, s.mrr,
       (SELECT date(MAX(e.occurred_at)) FROM events e WHERE e.account_id = a.account_id) AS last_event_date
FROM subscriptions s
JOIN accounts a ON a.account_id = s.account_id
WHERE s.ended_on IS NULL
  AND s.mrr > 0
  AND NOT EXISTS (SELECT 1 FROM events e
                  WHERE e.account_id = a.account_id AND e.occurred_at >= '2024-12-01')
ORDER BY s.mrr DESC, a.account_id;""",
  G("NOT EXISTS with a date condition, scalar subqueries.",
    "Two conditions of opposite kinds: a *presence* (a current paid subscription - a join) and an *absence* (no recent events - an anti-join).",
    ["Start from current paid subscriptions.", "`NOT EXISTS` with the date condition inside the subquery.", "A separate correlated `MAX(occurred_at)` reports the last activity."],
    "Join for what must exist, NOT EXISTS for what must not, scalar subquery for the extra column.",
    "- `LEFT JOIN events ... WHERE e.occurred_at < '2024-12-01'` keeps accounts that have old events even if they also have new ones.\n- Putting the date condition outside the NOT EXISTS changes the question.\n- Free accounts are not 'paying' - check `mrr > 0`.",
    "With an index on `events(account_id, occurred_at)` each probe is a short range scan.")),

P("sql-accounts-using-every-core-feature", "Accounts That Use Every Core Feature", "Hard", "Relational division",
  [FEATURES, EVENTS, ACCOUNTS],
  "Find the accounts that have used **every** core feature (`features.is_core = 1`) at least once. The query must keep working if the list of core features changes - do not hard-code the feature names or their number.",
  "`account_id`, `company`, `core_features_used`, `core_events`",
  "by `core_events` descending, then `account_id`.",
  """
SELECT a.account_id, a.company,
       COUNT(DISTINCT e.event_name) AS core_features_used,
       COUNT(*) AS core_events
FROM events e
JOIN features f ON f.feature_name = e.event_name AND f.is_core = 1
JOIN accounts a ON a.account_id = e.account_id
GROUP BY a.account_id, a.company
HAVING COUNT(DISTINCT e.event_name) = (SELECT COUNT(*) FROM features WHERE is_core = 1)
ORDER BY core_events DESC, a.account_id;""",
  G("Joins, COUNT(DISTINCT), HAVING with a subquery.",
    "'Has all of them' = 'the number of distinct required items it has equals the number of required items'. This is *relational division* by counting.",
    ["Join events to the core features so only core usage remains.", "Per account, `COUNT(DISTINCT e.event_name)`.", "Compare with `(SELECT COUNT(*) FROM features WHERE is_core = 1)` in HAVING."],
    "Restrict to the required set, count distinct matches per account, compare with the size of the required set.",
    "- `COUNT(*) = 4` counts events, not distinct features, and hard-codes the list size.\n- Forgetting the `is_core` filter in either place breaks the equality.\n- The alternative is a double negation: accounts for which there is NO core feature that they have NOT used (`NOT EXISTS ... NOT EXISTS`).",
    "One join and aggregate over events.")),

P("sql-onboarding-funnel", "Onboarding Funnel", "Hard", "Funnels and conversion rates",
  [EVENTS],
  "Measure the onboarding funnel `signup -> create_project -> invite_teammate -> run_report`. An account reaches a step only if it reached the previous step first: the first `create_project` must be at or after the first `signup`, the first `invite_teammate` at or after that first `create_project`, and the first `run_report` at or after that first `invite_teammate`. Return one row per step.",
  "`step_no`, `step`, `accounts`, `pct_of_signups` (rounded to 1), `pct_of_previous_step` (rounded to 1; 100.0 for the first step)",
  "by `step_no`.",
  """
WITH firsts AS (
  SELECT account_id,
         MIN(CASE WHEN event_name = 'signup' THEN occurred_at END) AS t1,
         MIN(CASE WHEN event_name = 'create_project' THEN occurred_at END) AS t2,
         MIN(CASE WHEN event_name = 'invite_teammate' THEN occurred_at END) AS t3,
         MIN(CASE WHEN event_name = 'run_report' THEN occurred_at END) AS t4
  FROM events
  GROUP BY account_id
), reached AS (
  SELECT COUNT(t1) AS s1,
         SUM(CASE WHEN t2 >= t1 THEN 1 ELSE 0 END) AS s2,
         SUM(CASE WHEN t2 >= t1 AND t3 >= t2 THEN 1 ELSE 0 END) AS s3,
         SUM(CASE WHEN t2 >= t1 AND t3 >= t2 AND t4 >= t3 THEN 1 ELSE 0 END) AS s4
  FROM firsts
), steps AS (
  SELECT 1 AS step_no, 'signup' AS step, s1 AS accounts, s1 AS first_step, s1 AS prev FROM reached
  UNION ALL SELECT 2, 'create_project', s2, s1, s1 FROM reached
  UNION ALL SELECT 3, 'invite_teammate', s3, s1, s2 FROM reached
  UNION ALL SELECT 4, 'run_report', s4, s1, s3 FROM reached
)
SELECT step_no, step, accounts,
       ROUND(100.0 * accounts / first_step, 1) AS pct_of_signups,
       ROUND(100.0 * accounts / prev, 1) AS pct_of_previous_step
FROM steps
ORDER BY step_no;""",
  G("MIN(CASE) to pivot first timestamps, NULL comparisons, UNION ALL to unpivot.",
    "Reduce each account to four timestamps - the first time it did each step. Reaching step k means all the comparisons up to k hold. A comparison with a NULL timestamp is UNKNOWN, so accounts that never did a step drop out of the count automatically.",
    ["`MIN(CASE WHEN event_name = '...' THEN occurred_at END)` per account, one column per step.", "Count with chained conditions `t2 >= t1 AND t3 >= t2 ...`.", "Turn the one-row result into four rows with UNION ALL to compute the percentages."],
    "Pivot to first-times, count cumulative conditions, unpivot to one row per step.",
    "- Counting accounts with each event independently ignores order and can make a later step larger than an earlier one.\n- ISO timestamps compare correctly as text.\n- Using `>` instead of `>=` drops accounts whose steps share a timestamp; follow the stated rule.",
    "One aggregate over events.")),

P("sql-account-retention-cohorts", "Account Retention by Signup Cohort", "Hard", "Retention and cohorts",
  [ACCOUNTS, EVENTS],
  "Group accounts into cohorts by the month of `created_on`, for cohorts from 2024-01 to 2024-06. An account is *active* in a month if it has at least one event in that month. For each cohort report its size and how many accounts were active 1, 2 and 3 calendar months after the creation month, plus the month-1 retention rate.",
  "`cohort_month` (`'YYYY-MM'`), `cohort_size`, `active_m1`, `active_m2`, `active_m3`, `m1_retention_pct` (rounded to 1)",
  "by `cohort_month`.",
  """
WITH cohort AS (
  SELECT account_id, strftime('%Y-%m', created_on) AS cohort_month,
         CAST(strftime('%Y', created_on) AS INTEGER) * 12 + CAST(strftime('%m', created_on) AS INTEGER) AS c_idx
  FROM accounts
  WHERE created_on >= '2024-01-01' AND created_on < '2024-07-01'
), activity AS (
  SELECT DISTINCT account_id,
         CAST(strftime('%Y', occurred_at) AS INTEGER) * 12 + CAST(strftime('%m', occurred_at) AS INTEGER) AS m_idx
  FROM events
)
SELECT c.cohort_month,
       COUNT(DISTINCT c.account_id) AS cohort_size,
       COUNT(DISTINCT CASE WHEN a.m_idx - c.c_idx = 1 THEN c.account_id END) AS active_m1,
       COUNT(DISTINCT CASE WHEN a.m_idx - c.c_idx = 2 THEN c.account_id END) AS active_m2,
       COUNT(DISTINCT CASE WHEN a.m_idx - c.c_idx = 3 THEN c.account_id END) AS active_m3,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN a.m_idx - c.c_idx = 1 THEN c.account_id END)
             / COUNT(DISTINCT c.account_id), 1) AS m1_retention_pct
FROM cohort c
LEFT JOIN activity a ON a.account_id = c.account_id
GROUP BY c.cohort_month
ORDER BY c.cohort_month;""",
  G("Month index arithmetic, LEFT JOIN, COUNT(DISTINCT CASE ...).",
    "Give every account a cohort month and every activity row a month, both as a month index (year x 12 + month). The difference is 'months since signup'; counting distinct accounts at each difference fills one column of the retention table.",
    ["Cohort CTE: account, label, month index.", "Activity CTE: distinct (account, month index).", "LEFT JOIN so inactive accounts stay in the cohort size; one `COUNT(DISTINCT CASE WHEN diff = k ...)` per column."],
    "Cohort assignment, de-duplicated activity, outer join, conditional distinct counts.",
    "- An inner join shrinks the cohort size to accounts with events and inflates retention.\n- `COUNT(*)` counts activity rows; the join fans out, so distinct accounts are required.\n- Day differences divided by 30 are not calendar months.",
    "Linear in events after de-duplication.")),

P("sql-month-end-mrr", "Month-End MRR and Growth", "Hard", "Month-over-month growth",
  [SUBS],
  "Compute MRR at the end of each month of 2024. A subscription counts toward a month-end if it started on or before that day and had not ended by then (`ended_on` is NULL or later than that day). Also report the number of paying subscriptions (`mrr > 0`) and the month-over-month growth of MRR.",
  "`month_end` (`'YYYY-MM-DD'`), `paying_subscriptions`, `mrr` (rounded to 2), `mom_growth_pct` (rounded to 1; NULL for January)",
  "by `month_end`.",
  """
WITH RECURSIVE months(month_start) AS (
  SELECT '2024-01-01'
  UNION ALL
  SELECT date(month_start, '+1 month') FROM months WHERE month_start < '2024-12-01'
), ends AS (
  SELECT date(month_start, '+1 month', '-1 day') AS month_end FROM months
), snap AS (
  SELECT e.month_end,
         SUM(CASE WHEN s.mrr > 0 THEN 1 ELSE 0 END) AS paying_subscriptions,
         COALESCE(SUM(s.mrr), 0) AS mrr
  FROM ends e
  LEFT JOIN subscriptions s
    ON s.started_on <= e.month_end
   AND (s.ended_on IS NULL OR s.ended_on > e.month_end)
  GROUP BY e.month_end
)
SELECT month_end, paying_subscriptions,
       ROUND(mrr, 2) AS mrr,
       ROUND(100.0 * (mrr - LAG(mrr) OVER (ORDER BY month_end)) / LAG(mrr) OVER (ORDER BY month_end), 1) AS mom_growth_pct
FROM snap
ORDER BY month_end;""",
  G("Recursive CTE calendars, range joins, LAG.",
    "MRR at a date is a *snapshot*: the sum over subscriptions whose validity interval contains that date. Generate the twelve month-ends, range-join the subscriptions to each, then compare consecutive snapshots.",
    ["Generate month starts recursively; month end = start `+1 month -1 day`.", "Join condition: `started_on <= month_end AND (ended_on IS NULL OR ended_on > month_end)`.", "`LAG(mrr) OVER (ORDER BY month_end)` for growth."],
    "Calendar scaffold, point-in-time range join, aggregate, period-over-period comparison.",
    "- Summing MRR by `started_on` month counts new business, not the standing total.\n- `ended_on > month_end` fails for active rows (NULL) unless the `IS NULL` branch is present.\n- Day arithmetic like `+30 days` drifts; use month modifiers.",
    "12 x subscriptions comparisons - trivial here; on large data use an index on the dates.")),

P("sql-family-mrr-rollup", "MRR Rolled Up to Parent Companies", "Hard", "Recursive hierarchies",
  [ACCOUNTS, SUBS],
  "Accounts form a hierarchy through `parent_account_id` (a subsidiary points to its owner, possibly several levels deep). For each top-level account (no parent) that has at least one descendant, compute the number of accounts in its family (itself included) and the family's total **current** MRR (subscriptions with `ended_on` NULL).",
  "`root_account_id`, `company`, `family_accounts`, `family_mrr` (rounded to 2)",
  "by `family_mrr` descending, then `root_account_id`.",
  """
WITH RECURSIVE fam(root_id, account_id) AS (
  SELECT account_id, account_id FROM accounts WHERE parent_account_id IS NULL
  UNION ALL
  SELECT f.root_id, a.account_id
  FROM accounts a
  JOIN fam f ON a.parent_account_id = f.account_id
), mrr AS (
  SELECT account_id, SUM(mrr) AS mrr
  FROM subscriptions
  WHERE ended_on IS NULL
  GROUP BY account_id
)
SELECT f.root_id AS root_account_id, r.company,
       COUNT(*) AS family_accounts,
       ROUND(COALESCE(SUM(m.mrr), 0), 2) AS family_mrr
FROM fam f
JOIN accounts r ON r.account_id = f.root_id
LEFT JOIN mrr m ON m.account_id = f.account_id
GROUP BY f.root_id, r.company
HAVING COUNT(*) > 1
ORDER BY family_mrr DESC, root_account_id;""",
  G("Recursive CTEs, pre-aggregation, LEFT JOIN.",
    "First build a map *account -> its top-level ancestor* by walking down from the roots and carrying the root id along. After that the problem is a plain join and GROUP BY.",
    ["Anchor: each root maps to itself.", "Recursive step: a child inherits its parent's root id.", "Pre-aggregate current MRR per account, LEFT JOIN it (churned members have none), group by root."],
    "Recursive mapping, per-account MRR, outer join, aggregate, keep families larger than one.",
    "- One self join only reaches direct children; grandchildren would be missed.\n- An inner join to MRR drops churned subsidiaries and undercounts family size.\n- Joining raw subscriptions instead of a per-account total would be wrong if an account had two current subscriptions and you counted rows for the family size.",
    "Each account is visited once by the recursion.")),

P("sql-ticket-backlog-by-week", "Support Backlog by Week", "Hard", "Window frames",
  [TICKETS],
  "Track the support backlog. For each week (Monday start) from 2024-10-07 to 2024-12-23, report tickets opened that week, tickets closed that week, and the backlog at the end of the week: all tickets opened up to then minus all tickets closed up to then, counting from the beginning of the data.",
  "`week_start` (`'YYYY-MM-DD'`), `opened`, `closed`, `backlog_end_of_week`",
  "by `week_start`.",
  """
WITH changes AS (
  SELECT date(opened_at, 'weekday 0', '-6 days') AS week_start, 1 AS opened, 0 AS closed FROM tickets
  UNION ALL
  SELECT date(closed_at, 'weekday 0', '-6 days'), 0, 1 FROM tickets WHERE closed_at IS NOT NULL
), weekly AS (
  SELECT week_start, SUM(opened) AS opened, SUM(closed) AS closed
  FROM changes
  GROUP BY week_start
), running AS (
  SELECT week_start, opened, closed,
         SUM(opened - closed) OVER (ORDER BY week_start
                                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS backlog_end_of_week
  FROM weekly
)
SELECT week_start, opened, closed, backlog_end_of_week
FROM running
WHERE week_start BETWEEN '2024-10-07' AND '2024-12-23'
ORDER BY week_start;""",
  G("UNION ALL of events, running totals with an explicit frame, filter after the window.",
    "A ticket contributes +1 to the backlog in the week it opens and -1 in the week it closes - two different weeks, so turn each ticket into two 'change' rows. The backlog is the running sum of the net change.",
    ["Stack open events and close events with UNION ALL, each tagged with its own week.", "Aggregate per week, then `SUM(opened - closed) OVER (ORDER BY week_start ROWS UNBOUNDED PRECEDING)`.", "Apply the reporting date range *after* computing the running total."],
    "Event stacking, weekly aggregate, cumulative window, late filter.",
    "- Grouping tickets by opening week and counting how many are closed mixes two different weeks.\n- Filtering the date range before the window resets the backlog to zero at the start of the report.\n- A week with neither opens nor closes would be missing; scaffold with a calendar if that can happen.",
    "One sort of weekly rows.")),
]
