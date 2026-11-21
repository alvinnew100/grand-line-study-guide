# Gaps and islands, sessions and cohort retention

> **Before this lesson:** you should be able to number rows with `ROW_NUMBER`, look at neighbouring rows with `LAG` and `LEAD`, and compute a running total with a frame ([Window basics and ranking](#/lesson/sql/ranking), [LAG, LEAD, running totals and frames](#/lesson/sql/lag-lead-frames)); count conditionally with `CASE` ([CASE patterns](#/lesson/sql/case-patterns)); do date arithmetic with `julianday` and `strftime` ([Dates, times and conversion](#/lesson/sql/dates-conversion)); and chain CTEs ([Common table expressions](#/lesson/sql/ctes)). The first half of this catalogue is [Top-N, deduplication, pivoting and medians](#/lesson/sql/patterns-1).

## In plain words

This second half of the pattern catalogue is about **sequences in time**. The questions sound like these:

- "What is each user's longest run of consecutive days with a login?" Think of the streak counter in a language-learning app.
- "Which days are missing?"
- "A user clicked 40 times today. How many separate visits was that?"
- "Of the people who looked at a product, how many put it in the basket, and how many of those paid?"
- "Of the customers who signed up in March, how many were still buying two months later?"

None of these can be answered by looking at one row at a time. Each row has to be compared with the rows around it, and then rows have to be gathered into groups that no column names: "this streak", "this visit".

They are considered the hard tier of SQL interview questions. They rest, however, on two small tricks, plus careful date arithmetic:

1. **Difference of sequences.** Subtract a row number from a date. Rows of the same streak all give the same answer.
2. **Flag and running sum.** Mark each row that starts a new group with a 1, then keep a running total of the marks. The total is a group number.

Learn the two tricks and the problems stop being hard.

**Why it matters for a job.** Streaks, visits, funnels and retention are the daily vocabulary of teams that build products. Any analyst or data scientist working on a product is asked for a retention table sooner or later. In interviews, "longest streak of consecutive days" is one of the most common hard questions.

## Pattern 1: gaps and islands

Take a set of ordered values, such as the dates on which someone logged in. An **island** is a run of consecutive values with nothing missing. A **gap** is the empty stretch between two islands. "Longest login streak", "periods of unbroken subscription", "consecutive failures" and "missing invoice numbers" are all this problem.

### Islands: the difference-of-sequences trick

Take one customer's login dates and number them in order:

| login_date | row number | date minus row number |
|---|---|---|
| Mar 04 | 1 | Mar 03 |
| Mar 05 | 2 | Mar 03 |
| Mar 06 | 3 | Mar 03 |
| Mar 10 | 4 | Mar 06 |
| Mar 11 | 5 | Mar 06 |

Within a run of consecutive days the date goes up by one on each row, and so does the row number. Subtract one from the other and the **result stays the same**. When a day is skipped, the date jumps ahead but the row number does not, and the result changes. That constant result is a label for the island. Its actual value (3 March, 6 March) has no meaning; what matters is that rows of one streak share it.

See it on real data. The second column numbers customer 4's logins; the third subtracts that many days from the date.

```sql-run dataset=shop
SELECT customer_id, login_date,
       ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY login_date) AS rn,
       date(login_date, '-' || ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY login_date) || ' days') AS island_key
FROM logins
WHERE customer_id = 4
ORDER BY login_date;
```

The first rows, 4 March to 12 March, all show the island key `2024-03-03`. After a missed day the key changes, and it stays at its new value for the next streak.

Now group by that label, and each group is one streak:

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

- In `keyed`, `julianday(login_date)` turns the date into a day number so that an ordinary subtraction works. `grp` is the island label.
- The main query groups by customer and label. The earliest date in a group is the start of the streak, the latest is its end, and the row count is its length.

Customer 4 has a streak from 4 to 12 March: nine days. From here, "the longest streak per customer" is a top-1 per group over these islands, and "customers with a streak of at least 7 days" is a `HAVING`.

Two requirements for the trick. There must be **one row per unit** (per user per day). Two logins on the same day would advance the row number without advancing the date and break the arithmetic, so remove duplicates first; in this table the primary key guarantees it. And the unit must allow arithmetic: days and whole numbers do. For months, use a month number such as `year * 12 + month`.

> [!NOTE]
> **Other databases.** PostgreSQL: `login_date - (ROW_NUMBER() OVER (...))::int` (a date minus a whole number is a date). MySQL: `DATE_SUB(login_date, INTERVAL ROW_NUMBER() OVER (...) DAY)`. SQL Server: `DATEADD(day, -ROW_NUMBER() OVER (...), login_date)`.

### Islands defined by a status

Sometimes an island is a run of rows that share a *status*: "the longest run of finished training runs in an experiment". Use two row numbers and subtract them. One numbers all rows of the experiment in time order. The other numbers the rows *of the same status* in time order. While the status stays the same both go up by one, so their difference is constant; when a row of another status interrupts, the first number moves on and the second does not.

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

Experiment 1 has nine finished runs in a row, runs 1 to 9.

### Gaps

To list the gaps themselves, compare each row with the next one using `LEAD`:

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

Each row is paired with the date of the next login. If the two are more than one day apart, there is a gap, which begins the day after this login and ends the day before the next. Customer 4 missed two days (13 and 14 March) and later four days (21 to 24 March).

To list every single missing value, generate the complete series with a recursive CTE and keep the dates that have no matching row.

## Pattern 2: sessionization with flag and running sum

Websites record a stream of timestamped events: page views, clicks, purchases. A **session** is one visit, a burst of activity. The usual definition is: "a new session starts when more than 30 minutes have passed since the same user's previous event". No column says which session an event belongs to. It has to be worked out, and working it out is called **sessionization**.

The **flag-and-sum** technique has three steps:

1. With `LAG`, compute the time since the same user's previous event.
2. **Flag** each row that starts a new session (the user's first event, or a pause of more than 30 minutes) with 1, and every other row with 0.
3. Take a **running sum** of the flag. It goes up by one at each session start and stays level inside a session, so it is a session number.

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

Follow customer 35 down the result. The first event has no previous one (`mins_since_prev` is NULL), so its flag is 1 and its session number is 1. The next events come 7.0, 19.4 and 5.7 minutes apart, all within 30 minutes: flag 0, and the running sum stays at 1. Further down, where a pause exceeds 30 minutes, the flag is 1 again and the session number becomes 2. (The difference of two Julian day numbers is in days; multiplying by 1440 gives minutes.)

With a session number on every event, figures per session are an ordinary `GROUP BY`:

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

One row per session: when it started, how many events it had, how long it lasted, and whether it included a purchase. `MAX(event_type = 'purchase')` is 1 if any event of the session was a purchase. Customer 5's first session had 7 events over 71.4 minutes and ended in a purchase.

Flag-and-sum is more general than the difference trick. **Any** rule that can decide "this row starts a new group" becomes a grouping label: a pause in time, a change of value (`status <> LAG(status)`), a reset event. It solves the island problems above as well.

## Pattern 3: funnels

A **funnel** counts how many users reach each step of a process: viewed a page, added to the basket, reached the checkout, purchased. It is called a funnel because it narrows at every step. The simple version counts the different users at each step:

```sql-run dataset=shop
SELECT COUNT(DISTINCT customer_id) AS visitors,
       COUNT(DISTINCT CASE WHEN event_type = 'add_to_cart' THEN customer_id END) AS added_to_cart,
       COUNT(DISTINCT CASE WHEN event_type IN ('checkout', 'purchase') THEN customer_id END) AS reached_checkout,
       COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN customer_id END) AS purchased
FROM web_events;
```

Each `CASE` passes the customer id through only for events of one kind, and `COUNT(DISTINCT ...)` counts the different customers that remain. 24 visitors, 19 who added something to the basket, 17 who reached the checkout, 12 who purchased.

A **strict** funnel also demands that the steps happened *in order*. Find each user's first time at each step, then compare the times:

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

`firsts` holds one row per customer with three times; a step the customer never reached is NULL. The main query counts customers whose first basket event came after their first view, and those whose first purchase came after that. The strict numbers are smaller: 24 viewed, 16 then added to the basket, and only 3 then purchased, a conversion of 12.5%. A comparison with a NULL time gives NULL, which `SUM` skips. That is exactly what is wanted for users who never reached a step.

## Pattern 4: cohort retention

A **cohort** is a group of users who started in the same period, typically the month in which they signed up. **Retention** asks what fraction of each cohort is still active a given number of periods later. It is the standard measure of whether a product keeps its users.

Build it in stages:

1. **Cohort.** One row per user, with the period they started in.
2. **Activity.** One row per user per period in which they were active. Remove duplicates: someone who ordered three times in May was active in May once.
3. **Offset.** For each activity, how many periods after the user's start it occurred.
4. **Aggregate.** Count the different users per cohort and offset, and divide by the size of the cohort.

For arithmetic with months, turn a date into a **month index**: `year * 12 + month`. January 2024 is 2024 × 12 + 1 = 24289, and February 2024 is 24290. The difference of two month indexes is a whole number of months, however long the months are.

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

Each row is one cohort. `m0` is the number of its customers who ordered in the month they signed up, `m1` the number who ordered the month after, and so on. Read the February 2024 row: 17 customers signed up; 15 ordered in February, 8 in March, 1 in April, 3 in May. Month-1 retention is 8 ÷ 17 = 47.1%.

Points to get right:

- **`LEFT JOIN`** from the cohort to the activity, so that customers who never ordered still exist in the result. And take the divisor from the cohort table (`sizes`), not from the active users. An inner join, or a divisor of "users with activity", quietly inflates every rate.
- **Recent cohorts are incomplete.** A customer who signed up in November cannot have month-3 activity in data that ends in December. In a real report show such cells as blank, not as 0.
- **The definition matters.** "Active in the next calendar month" (used here), "active between day 30 and day 59", and "active at any time from day 30 onward" give different numbers. Say which one you mean.

The long format, one row per cohort and offset, is better for charts and avoids listing the columns by hand:

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

Here the cohort size is attached to every customer row by a window function, `COUNT(*) OVER (PARTITION BY ...)`, computed over all customers before the join. That is why an inner join is safe in this version: the divisor was fixed first. The February cohort shows 88.2% in month 0, 47.1% in month 1 and 5.9% in month 2.

## Pattern 5: active users over a rolling window

**DAU** (daily active users) and **MAU** (monthly active users) are counts of different users per period. A **rolling** count, "users active in the last 7 days", cannot be made with a window frame: window functions cannot count distinct values, and seven daily counts cannot be added because the same user may appear on several days. Instead, join each day to all the events of its preceding seven days and count the different users:

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

The join condition is a range: logins after "seven days before this day" up to and including this day. On 10 March, 11 customers logged in that day and 16 different customers logged in during the seven days ending then. A range join like this does a lot of work on large data; big systems count per day in advance and use approximate methods.

## Pattern 6: new, retained and reactivated

Several related questions use the same idea of comparing with the previous period:

- **New versus returning.** Find each user's first activity date, then compare each event's date with it.
- **Churn and reactivation.** A customer who stops being active has **churned**. With `LAG` on the month index per user, a gap of more than one month means the user went away and came back.
- **Year over year.** `LAG(value, 12)` over monthly rows, after filling in any missing months.

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

`monthly` has one row per customer per month with an order. `gap` is the number of months since that customer's previous active month. No previous month means a new customer; a gap of 1 means they were also active the month before (retained); a larger gap means they returned after a pause (reactivated). The result: 74 new, 55 retained, 30 reactivated.

> [!INTERVIEW]
> For "longest streak of consecutive days", say the trick in one sentence before writing: "within a streak, the date minus the row number is constant, so I group by that". Then state the precondition (one row per user per day) and remove duplicates if needed. For retention, say your definition and what the divisor is. Interviewers mark these problems on whether you control the edge cases, not on whether you remember syntax.

## Pitfalls

- **Several rows per period** break the island arithmetic. Reduce to one row per unit first.
- **A forgotten `PARTITION BY`**: streaks and sessions run on from one user into the next.
- **Inner joins in retention** shrink the divisor.
- **Recent, incomplete cohorts** reported as zero.
- **`COUNT(*)` where different users had to be counted.**
- **Off-by-one errors in gaps**: `> 30` or `>= 30` minutes; counting both end days or neither.
- **Dividing days by 30** to get months, instead of using a month index.
- **Time zones.** "A day" must be defined in one zone.

## Summary

| Problem | Technique |
|---|---|
| Streaks of consecutive days (islands) | date minus `ROW_NUMBER()` is constant within a streak; group by it |
| Runs of equal status | the difference of two row numbers |
| Gaps | `LEAD` or `LAG`, and compare neighbours |
| Sessionization | `LAG`, flag the start of each group, running `SUM` of the flags |
| Funnels | first time per step with `MIN(CASE ...)`, compared in order |
| Cohort retention | cohort per user, distinct activity per period, difference of month indexes, `LEFT JOIN`, divide by cohort size |
| Rolling active users | range join of days to the preceding events, `COUNT(DISTINCT)` |

## Glossary

- **Island** — a run of consecutive values with nothing missing, such as a streak of days.
- **Gap** — the missing stretch between two islands.
- **Difference of sequences** — the trick of subtracting a row number from a date or number to label islands.
- **Session** — one visit: a burst of events by one user with no long pause.
- **Sessionization** — working out which session each event belongs to.
- **Flag** — a column holding 1 for rows that meet a condition and 0 for the rest.
- **Flag and running sum** — marking the first row of each group with 1 and using the running total of the marks as a group number.
- **Funnel** — the number of users reaching each step of a process, in order.
- **Conversion** — the share of users who complete the final step.
- **Cohort** — users who started in the same period.
- **Retention** — the share of a cohort still active a given number of periods later.
- **Month index** — `year * 12 + month`, a whole number that makes month arithmetic exact.
- **DAU / MAU** — daily / monthly active users: different users active in a day / a month.
- **Rolling window** — a period of fixed length that moves forward with each row, such as "the last 7 days".
- **Churn** — a customer ceasing to be active.
- **Reactivation** — a churned customer becoming active again.

```quiz
[
  {"q": "Why is date minus ROW_NUMBER() constant within a streak of consecutive days?", "options": ["Dates are stored as text", "Both the date and the row number increase by exactly one per row", "ROW_NUMBER starts again every day", "It is not constant"], "answer": 1, "explain": "When a day is skipped the date jumps but the row number does not, so the difference changes and a new island begins."},
  {"q": "What must be true of the data before using the difference-of-sequences trick on daily logins?", "options": ["It must be indexed", "At most one row per user per day", "No NULL user ids", "Dates must be in UTC"], "answer": 1, "explain": "A repeated day advances the row number without advancing the date, which breaks the constant difference."},
  {"q": "In sessionization, what does the running SUM of the new_session flag produce?", "options": ["The number of events", "A session number that goes up by one at each session start", "The session's duration", "The pause in minutes"], "answer": 1, "explain": "The flag is 1 on the first event of each session, so the running total stays level inside a session and rises between sessions."},
  {"q": "Why must cohort retention use a LEFT JOIN from cohort members to activity, or a cohort size computed separately?", "options": ["LEFT JOIN is faster", "Users with no activity must still count in the divisor", "To remove duplicates", "Inner joins are not allowed with dates"], "answer": 1, "explain": "An inner join drops inactive users and so overstates retention."},
  {"q": "How do you compute the number of whole months between two dates reliably?", "options": ["Difference in days divided by 30", "(year * 12 + month) of one minus that of the other", "Subtract the date strings", "Count weeks and divide by 4"], "answer": 1, "explain": "A month index makes the difference exact whatever the length of the months."},
  {"q": "Why can't a rolling 7-day count of distinct users be made by adding seven daily distinct counts?", "options": ["SUM cannot be used in a window", "A user active on several days would be counted several times", "Days have different lengths", "It can"], "answer": 1, "explain": "Distinct counts of overlapping sets cannot be added."},
  {"q": "In a strict funnel, why does SUM(t_cart > t_view) ignore users who never added to the basket?", "options": ["They are removed by WHERE", "A comparison with a NULL time gives NULL, which SUM skips", "MIN returns zero", "They are counted as 1"], "answer": 1, "explain": "Comparisons with NULL give NULL, and aggregates ignore NULLs."},
  {"q": "With a 30-minute rule, a user has events at 10:00, 10:10, 10:50 and 10:55. How many sessions is that?", "options": ["1", "2", "3", "4"], "answer": 1, "explain": "The pause from 10:10 to 10:50 is 40 minutes, more than 30, so a second session starts at 10:50; the other pauses are short."}
]
```

> **Source:** Techniques build on Beaulieu, *Learning SQL*, 3rd ed., ch. 16 "Analytic Functions" and ch. 7 (temporal data). Gaps and islands, sessionization and cohort analysis follow standard industry practice and common SQL interview problem styles, written from scratch with this guide's own datasets.
