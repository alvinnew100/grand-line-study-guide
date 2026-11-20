# Gaps and islands, sessions and cohort retention

The second half of the pattern catalogue covers problems about **sequences in time**: streaks of consecutive days, missing values in a series, grouping events into sessions, funnels, and the cohort retention tables that every product team lives by. These are the "hard" tier of SQL interviews, but they rest on two small tricks — *difference of sequences* and *flag-and-running-sum* — plus careful date arithmetic. Learn the tricks and the problems stop being hard.

## Pattern 1: gaps and islands

Given a set of ordered values (dates, sequence numbers), an **island** is a maximal run of consecutive values, and a **gap** is the space between islands. "Longest login streak", "periods of continuous subscription", "consecutive failed runs", "missing invoice numbers" are all this problem.

### Islands: the difference-of-sequences trick

Take one customer's login dates and number them in order:

| login_date | row number | date − row number |
|---|---|---|
| Mar 04 | 1 | Mar 03 |
| Mar 05 | 2 | Mar 03 |
| Mar 06 | 3 | Mar 03 |
| Mar 10 | 4 | Mar 06 |
| Mar 11 | 5 | Mar 06 |

Within a run of consecutive days, the date goes up by one each row and so does the row number, so their **difference is constant**. When a day is skipped, the date jumps but the row number does not, and the difference changes. That constant is a label for the island.

```sql-run dataset=shop
SELECT customer_id, login_date,
       ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY login_date) AS rn,
       date(login_date, '-' || ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY login_date) || ' days') AS island_key
FROM logins
WHERE customer_id = 4
ORDER BY login_date;
```

Group by the label and each group is a streak:

```sql-run dataset=shop
WITH keyed AS (
  SELECT customer_id, login_date,
         julianday(login_date) - ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY login_date) AS grp
  FROM logins
)
SELECT customer_id,
       MIN(login_date) AS streak_start,
       MAX(login_date) AS streak_end,
       COUNT(*)        AS streak_days
FROM keyed
GROUP BY customer_id, grp
HAVING COUNT(*) >= 4
ORDER BY streak_days DESC, customer_id
LIMIT 8;
```

`julianday()` turns the date into a number so that subtraction works. From here, "longest streak per customer" is a top-1-per-group over these islands, and "customers with a streak of at least 7 days" is a HAVING.

Requirements for the trick: **one row per unit** (deduplicate first — two logins on the same day would break the arithmetic; here the primary key guarantees it), and a unit you can do arithmetic on (days, integers; for months use a month index such as `year * 12 + month`).

> [!NOTE]
> **Other dialects:** PostgreSQL `login_date - (ROW_NUMBER() OVER (...))::int` (date minus integer is a date); MySQL `DATE_SUB(login_date, INTERVAL ROW_NUMBER() OVER (...) DAY)`; SQL Server `DATEADD(day, -ROW_NUMBER() OVER (...), login_date)`.

### Islands defined by a condition

Sometimes the islands are runs of rows sharing a *status* rather than consecutive dates: "longest run of FINISHED runs in an experiment". Use two row numbers — one over all rows, one within the status — and subtract; the difference is constant inside each run of equal status:

```sql-run dataset=mlops
WITH seq AS (
  SELECT experiment_id, run_id, status,
         ROW_NUMBER() OVER (PARTITION BY experiment_id ORDER BY started_at)
       - ROW_NUMBER() OVER (PARTITION BY experiment_id, status ORDER BY started_at) AS grp
  FROM runs
)
SELECT experiment_id, status, COUNT(*) AS run_length, MIN(run_id) AS first_run, MAX(run_id) AS last_run
FROM seq
GROUP BY experiment_id, status, grp
HAVING status = 'FINISHED'
ORDER BY run_length DESC
LIMIT 5;
```

### Gaps

To list the gaps themselves, compare each row with the next using `LEAD`:

```sql-run dataset=shop
WITH nxt AS (
  SELECT customer_id, login_date,
         LEAD(login_date) OVER (PARTITION BY customer_id ORDER BY login_date) AS next_login
  FROM logins
)
SELECT customer_id,
       date(login_date, '+1 day') AS gap_start,
       date(next_login, '-1 day') AS gap_end,
       CAST(julianday(next_login) - julianday(login_date) - 1 AS INTEGER) AS days_missed
FROM nxt
WHERE julianday(next_login) - julianday(login_date) > 1
  AND customer_id = 4
ORDER BY gap_start;
```

To list every individual missing value, generate the full series (recursive CTE) and anti-join it against the data.

## Pattern 2: sessionization — flag and running sum

Clickstream data is a stream of timestamped events. A **session** is a burst of activity; the usual definition is "a new session starts when more than 30 minutes have passed since the user's previous event". No column says which session an event belongs to — you must derive it.

The **flag-and-sum** technique, in three steps:

1. With `LAG`, compute the gap to the previous event of the same user.
2. **Flag** rows that start a new session (first event, or gap > 30 minutes) with 1, others 0.
3. A **running sum** of the flag is the session number: it increases by one at each session start and stays constant within a session.

```sql-run dataset=shop
WITH gaps AS (
  SELECT customer_id, event_id, event_time, event_type,
         ROUND((julianday(event_time)
                - julianday(LAG(event_time) OVER (PARTITION BY customer_id ORDER BY event_time))) * 1440, 1) AS mins_since_prev
  FROM web_events
),
flagged AS (
  SELECT *, CASE WHEN mins_since_prev IS NULL OR mins_since_prev > 30 THEN 1 ELSE 0 END AS new_session
  FROM gaps
)
SELECT customer_id, event_time, event_type, mins_since_prev, new_session,
       SUM(new_session) OVER (PARTITION BY customer_id ORDER BY event_time
                              ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS session_no
FROM flagged
WHERE customer_id = 35
ORDER BY event_time;
```

With a session number on every event, session-level metrics are a GROUP BY:

```sql-run dataset=shop
WITH flagged AS (
  SELECT customer_id, event_time, event_type,
         CASE WHEN LAG(event_time) OVER w IS NULL
                OR (julianday(event_time) - julianday(LAG(event_time) OVER w)) * 1440 > 30
              THEN 1 ELSE 0 END AS new_session
  FROM web_events
  WINDOW w AS (PARTITION BY customer_id ORDER BY event_time)
),
sessions AS (
  SELECT *, SUM(new_session) OVER (PARTITION BY customer_id ORDER BY event_time
                                   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS session_no
  FROM flagged
)
SELECT customer_id, session_no,
       MIN(event_time) AS started, COUNT(*) AS events,
       ROUND((julianday(MAX(event_time)) - julianday(MIN(event_time))) * 1440, 1) AS duration_min,
       MAX(event_type = 'purchase') AS converted
FROM sessions
GROUP BY customer_id, session_no
ORDER BY events DESC
LIMIT 8;
```

Flag-and-sum is more general than the difference trick: **any** rule that can decide "this row starts a new group" — a time gap, a change of value (`status <> LAG(status)`), a reset event — becomes a grouping key. It solves the islands problems above too.

## Pattern 3: funnels

A funnel counts how many users reach each step of a process: viewed → added to cart → checked out → purchased. The simplest version counts distinct users per step with conditional aggregation:

```sql-run dataset=shop
SELECT COUNT(DISTINCT customer_id) AS visitors,
       COUNT(DISTINCT CASE WHEN event_type = 'add_to_cart' THEN customer_id END) AS added_to_cart,
       COUNT(DISTINCT CASE WHEN event_type IN ('checkout', 'purchase') THEN customer_id END) AS reached_checkout,
       COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN customer_id END) AS purchased
FROM web_events;
```

A **strict** funnel also requires the steps to happen *in order*. Compute each user's first time at each step, then compare the timestamps:

```sql-run dataset=shop
WITH firsts AS (
  SELECT customer_id,
         MIN(CASE WHEN event_type = 'page_view'   THEN event_time END) AS t_view,
         MIN(CASE WHEN event_type = 'add_to_cart' THEN event_time END) AS t_cart,
         MIN(CASE WHEN event_type = 'purchase'    THEN event_time END) AS t_buy
  FROM web_events
  GROUP BY customer_id
)
SELECT COUNT(t_view) AS viewed,
       SUM(t_cart > t_view) AS then_carted,
       SUM(t_cart > t_view AND t_buy > t_cart) AS then_purchased,
       ROUND(100.0 * SUM(t_cart > t_view AND t_buy > t_cart) / COUNT(t_view), 1) AS conversion_pct
FROM firsts;
```

Comparisons involving a NULL timestamp are UNKNOWN and are not counted by SUM — exactly the behaviour wanted for users who never reached a step.

## Pattern 4: cohort retention

A **cohort** is a group of users who share a starting event in the same period — typically the month they signed up. **Retention** asks what fraction of each cohort is still active N periods later. It is the standard way to measure whether a product keeps its users, and its triangular table is instantly recognisable.

Build it in stages:

1. **Cohort assignment** — one row per user with their cohort period.
2. **Activity** — one row per user per active period (distinct!).
3. **Period offset** — how many periods after the cohort start each activity occurred.
4. **Aggregate** — distinct users per (cohort, offset), divided by cohort size.

For month arithmetic, convert a date to a **month index**: `year * 12 + month`. Differences of indexes are whole months.

```sql-run dataset=shop
WITH cohort AS (
  SELECT customer_id,
         strftime('%Y-%m', signup_date) AS cohort_month,
         CAST(strftime('%Y', signup_date) AS INTEGER) * 12 + CAST(strftime('%m', signup_date) AS INTEGER) AS cohort_idx
  FROM customers
),
activity AS (
  SELECT DISTINCT customer_id,
         CAST(strftime('%Y', order_date) AS INTEGER) * 12 + CAST(strftime('%m', order_date) AS INTEGER) AS month_idx
  FROM orders
),
sizes AS (SELECT cohort_month, COUNT(*) AS cohort_size FROM cohort GROUP BY cohort_month)
SELECT c.cohort_month, s.cohort_size,
       COUNT(DISTINCT CASE WHEN a.month_idx - c.cohort_idx = 0 THEN c.customer_id END) AS m0,
       COUNT(DISTINCT CASE WHEN a.month_idx - c.cohort_idx = 1 THEN c.customer_id END) AS m1,
       COUNT(DISTINCT CASE WHEN a.month_idx - c.cohort_idx = 2 THEN c.customer_id END) AS m2,
       COUNT(DISTINCT CASE WHEN a.month_idx - c.cohort_idx = 3 THEN c.customer_id END) AS m3,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN a.month_idx - c.cohort_idx = 1 THEN c.customer_id END)
             / s.cohort_size, 1) AS m1_retention_pct
FROM cohort c
JOIN sizes s ON s.cohort_month = c.cohort_month
LEFT JOIN activity a ON a.customer_id = c.customer_id
GROUP BY c.cohort_month, s.cohort_size
ORDER BY c.cohort_month;
```

Each row is a cohort; each `m` column is the number of its customers who ordered that many months after signing up. Points to get right:

- **LEFT JOIN** from cohort to activity, so customers who never ordered still count in the cohort size (the denominator). An inner join silently inflates every rate.
- **Denominator = cohort size**, computed from the cohort table, not from active users.
- **Recent cohorts are incomplete**: November signups cannot have month-3 activity yet in data that ends in December. Show such cells as NULL or blank rather than 0 in a real report.
- **Definition matters**: "active in calendar month +1" (used here), "active between day 30 and 59", and "active at any time on or after day 30" (unbounded or *rolling* retention) give different numbers. State yours.

The long format — one row per (cohort, offset) — is better for charting, and avoids hand-listing columns:

```sql-run dataset=shop
WITH cohort AS (
  SELECT customer_id, strftime('%Y-%m', signup_date) AS cohort_month,
         CAST(strftime('%Y', signup_date) AS INTEGER) * 12 + CAST(strftime('%m', signup_date) AS INTEGER) AS cohort_idx,
         COUNT(*) OVER (PARTITION BY strftime('%Y-%m', signup_date)) AS cohort_size
  FROM customers
),
activity AS (
  SELECT DISTINCT customer_id,
         CAST(strftime('%Y', order_date) AS INTEGER) * 12 + CAST(strftime('%m', order_date) AS INTEGER) AS month_idx
  FROM orders
)
SELECT c.cohort_month, a.month_idx - c.cohort_idx AS months_since_signup,
       COUNT(*) AS active_customers,
       ROUND(100.0 * COUNT(*) / MAX(c.cohort_size), 1) AS retention_pct
FROM cohort c
JOIN activity a ON a.customer_id = c.customer_id
WHERE c.cohort_month IN ('2024-02', '2024-03')
GROUP BY c.cohort_month, months_since_signup
ORDER BY c.cohort_month, months_since_signup;
```

## Pattern 5: active users and rolling windows

**DAU / MAU** are distinct counts per period. A **rolling** 7-day active count cannot be computed with a window frame (window functions cannot `COUNT(DISTINCT)` and distinct counts are not additive), so join each day to the events of the trailing window:

```sql-run dataset=shop
WITH days AS (SELECT DISTINCT login_date AS day FROM logins WHERE login_date BETWEEN '2024-03-10' AND '2024-03-16')
SELECT d.day,
       COUNT(DISTINCT CASE WHEN l.login_date = d.day THEN l.customer_id END) AS dau,
       COUNT(DISTINCT l.customer_id) AS rolling_7d_active
FROM days d
JOIN logins l ON l.login_date > date(d.day, '-7 days') AND l.login_date <= d.day
GROUP BY d.day
ORDER BY d.day;
```

A range join like this is O(days × window); on large data, warehouses pre-aggregate daily and use approximate distinct sketches.

## Pattern 6: comparing with the previous period, and "first time" events

- **New vs returning** — find each user's first activity date with `MIN(...) OVER (PARTITION BY user)` or a grouped CTE, then label each event by comparing its date with it.
- **Churn / reactivation** — `LAG(activity_month)` per user; a gap of more than one period means the user churned and came back.
- **Year-over-year** — `LAG(value, 12)` over monthly rows (after densifying), or a self join on month − 12.

```sql-run dataset=shop
WITH monthly AS (
  SELECT DISTINCT customer_id,
         CAST(strftime('%Y', order_date) AS INTEGER) * 12 + CAST(strftime('%m', order_date) AS INTEGER) AS m
  FROM orders
),
labelled AS (
  SELECT customer_id, m, m - LAG(m) OVER (PARTITION BY customer_id ORDER BY m) AS gap
  FROM monthly
)
SELECT CASE WHEN gap IS NULL THEN 'new' WHEN gap = 1 THEN 'retained' ELSE 'reactivated' END AS customer_state,
       COUNT(*) AS customer_months
FROM labelled
GROUP BY customer_state;
```

## Pitfalls

- **Duplicates per period** break the islands arithmetic — deduplicate to one row per unit first.
- **Forgetting PARTITION BY** — streaks and sessions leak across users.
- **Inner joins in retention** — shrink the denominator.
- **Incomplete recent cohorts** reported as zero.
- **`COUNT(*)` where distinct users are required.**
- **Off-by-one in gaps** (`> 30` vs `>= 30` minutes; inclusive vs exclusive day counts).
- **Month arithmetic with day counts** (`/ 30`) instead of a month index.
- **Time zones** — "a day" must be defined in one zone.

## Summary

| Problem | Technique |
|---|---|
| Consecutive streaks (islands) | `date − ROW_NUMBER()` is constant within a streak; group by it |
| Runs of equal status | difference of two row numbers |
| Gaps | `LEAD`/`LAG` and compare neighbours |
| Sessionization | `LAG` → flag new group → running `SUM` of flags |
| Funnels | first timestamp per step (`MIN(CASE …)`), compare in order |
| Cohort retention | cohort per user, distinct activity per period, month index difference, LEFT JOIN, divide by cohort size |
| Rolling active users | range join of days to trailing events, `COUNT(DISTINCT)` |

```quiz
[
  {"q": "Why is date - ROW_NUMBER() constant within a streak of consecutive days?", "options": ["Dates are stored as text", "Both the date and the row number increase by exactly one per row", "ROW_NUMBER resets every day", "It is not constant"], "answer": 1, "explain": "When a day is skipped the date jumps but the row number does not, changing the difference and starting a new island."},
  {"q": "What must be true of the data before using the difference-of-sequences trick on daily logins?", "options": ["It must be indexed", "At most one row per user per day", "No NULL user ids", "Dates must be in UTC"], "answer": 1, "explain": "Duplicate days advance the row number without advancing the date, breaking the constant difference."},
  {"q": "In sessionization, what does the running SUM of the new_session flag produce?", "options": ["The number of events", "A session number that increases at each session start", "The session duration", "The gap in minutes"], "answer": 1, "explain": "The flag is 1 at each session's first event, so the cumulative sum is constant within a session and increments between sessions."},
  {"q": "Why must cohort retention use a LEFT JOIN from cohort members to activity (or a separately computed cohort size)?", "options": ["LEFT JOIN is faster", "Users with no activity must still count in the denominator", "To remove duplicates", "Inner joins are not allowed with dates"], "answer": 1, "explain": "An inner join drops inactive users and overstates retention."},
  {"q": "How do you compute the number of whole months between two dates robustly?", "options": ["Days difference / 30", "(year*12 + month) of one minus the other", "Subtract the date strings", "Count weeks / 4"], "answer": 1, "explain": "A month index makes month differences exact regardless of month length."},
  {"q": "Why can't a rolling 7-day distinct-user count be computed by summing seven daily distinct counts?", "options": ["SUM cannot be windowed", "A user active on several days would be counted several times", "Days have different lengths", "It can"], "answer": 1, "explain": "Distinct counts are not additive across overlapping sets."},
  {"q": "In a strict funnel, why does SUM(t_cart > t_view) ignore users who never added to cart?", "options": ["They are filtered by WHERE", "Comparison with a NULL timestamp is UNKNOWN (NULL), which SUM skips", "MIN returns zero", "They are counted as 1"], "answer": 1, "explain": "NULL comparisons yield NULL and aggregates ignore NULLs."}
]
```

> **Source:** Techniques build on Beaulieu, *Learning SQL*, 3rd ed., ch. 16 "Analytic Functions" and ch. 7 (temporal data); gaps-and-islands, sessionization and cohort analysis follow standard industry practice and common DataLemur / LeetCode problem styles, written from scratch.
