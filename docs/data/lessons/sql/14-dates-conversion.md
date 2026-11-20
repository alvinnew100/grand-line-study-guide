# Dates, times and conversion

The book calls temporal data the most involved of the three data families, and every practitioner agrees. Dates have formats, time zones, months of unequal length, leap years and daylight saving. On top of that, date functions are the least portable part of SQL: nearly every example in this lesson needs a different spelling in MySQL and PostgreSQL. The concepts, however, are the same everywhere: **generate** a temporal value, **manipulate** it (add, subtract, truncate, extract parts), and **convert** between types.

## Time zones in one page

People want noon to be when the sun is overhead, so the world runs on 24+ time zones, and many shift twice a year for daylight saving. The reference is **UTC** (Coordinated Universal Time). Guidelines:

- Store instants in **UTC**; convert to local time when displaying.
- Know what your column type does. PostgreSQL `timestamptz` stores an absolute instant and converts to the session time zone on output; plain `timestamp` stores wall-clock digits with no zone. MySQL `TIMESTAMP` converts to UTC for storage, `DATETIME` does not.
- SQLite stores whatever text you give it. `datetime('now')` is UTC; add the `'localtime'` modifier to convert.

```sql-run dataset=bank
SELECT datetime('now')              AS utc_now,
       datetime('now', 'localtime') AS local_now,
       date('now')                  AS utc_today;
```

> [!WARNING]
> Queries using `now` return different results on different days. That is fine in a dashboard, but never in a test or a judged problem — the datasets in this guide are frozen in 2024, so examples use explicit dates.

## How SQLite represents temporal values

SQLite has no date type. Its date functions understand three encodings:

| Encoding | Example | Storage |
|---|---|---|
| ISO-8601 text | `'2024-03-07 14:22:00'` | TEXT |
| Julian day number | `2460377.0986` (days since noon, 24 Nov 4714 BC) | REAL |
| Unix epoch | `1709821320` (seconds since 1970-01-01 UTC) | INTEGER |

All three datasets here use ISO text, which is human-readable and sorts correctly. Five core functions do the work, all with the signature `fn(timevalue, modifier, modifier, ...)`:

| Function | Returns |
|---|---|
| `date(...)` | `'YYYY-MM-DD'` |
| `time(...)` | `'HH:MM:SS'` |
| `datetime(...)` | `'YYYY-MM-DD HH:MM:SS'` |
| `julianday(...)` | fractional day number (for arithmetic) |
| `unixepoch(...)` / `strftime('%s', ...)` | seconds since 1970 |
| `strftime(format, ...)` | text in any format |

## Generating temporal data

**From strings.** If the text is ISO-formatted, it already *is* a valid date value. Any other format must be rearranged, because SQLite cannot parse `'03/07/2024'`:

```sql-run dataset=bank
SELECT date('2024-03-07')              AS iso,
       date('03/07/2024')              AS us_style_fails,
       substr('03/07/2024', 7, 4) || '-' || substr('03/07/2024', 1, 2) || '-' || substr('03/07/2024', 4, 2) AS rebuilt;
```

> [!NOTE]
> **Parsing strings elsewhere.** MySQL: `STR_TO_DATE('03/07/2024', '%m/%d/%Y')` (the book's example builds a date from `'September 17, 2008'` with `'%M %d, %Y'`). PostgreSQL / Oracle: `to_date('03/07/2024', 'MM/DD/YYYY')`. Standard typed literals: `DATE '2024-03-07'`, `TIMESTAMP '2024-03-07 14:22:00'`.

**From the clock.** `CURRENT_DATE`, `CURRENT_TIME` and `CURRENT_TIMESTAMP` are standard and work everywhere (MySQL also `NOW()`, `CURDATE()`).

**From numbers.** `datetime(1709821320, 'unixepoch')` converts epoch seconds — common in event logs.

## Manipulating temporal data

### Adding and subtracting intervals: modifiers

SQLite's **modifiers** are applied left to right:

```sql-run dataset=bank
SELECT date('2024-01-31', '+1 month')                  AS plus_month,
       date('2024-03-07', '-7 days')                   AS week_ago,
       date('2024-03-07', 'start of month')            AS month_start,
       date('2024-03-07', 'start of month', '+1 month', '-1 day') AS month_end,
       date('2024-03-07', 'start of year')             AS year_start,
       date('2024-03-07', 'weekday 0')                 AS next_sunday,
       datetime('2024-03-07 14:22:00', '+90 minutes')  AS later;
```

Note `'2024-01-31' + 1 month`: there is no 31 February, so SQLite normalises to 2 March. MySQL and PostgreSQL clamp to the end of the month (29 February) instead. Month arithmetic is inherently ambiguous; "start of month, +1 month, −1 day" is the reliable way to get a month's last day (MySQL has `LAST_DAY(d)`).

| Task | SQLite | MySQL | PostgreSQL |
|---|---|---|---|
| Add 5 days | `date(d, '+5 days')` | `DATE_ADD(d, INTERVAL 5 DAY)` | `d + INTERVAL '5 days'` |
| Truncate to month | `date(d, 'start of month')` | `DATE_FORMAT(d, '%Y-%m-01')` | `date_trunc('month', d)` |
| Days between | `julianday(b) - julianday(a)` | `DATEDIFF(b, a)` | `b::date - a::date` |
| Extract year | `strftime('%Y', d)` | `YEAR(d)` / `EXTRACT(YEAR FROM d)` | `EXTRACT(YEAR FROM d)` |
| Format | `strftime(fmt, d)` | `DATE_FORMAT(d, fmt)` | `to_char(d, fmt)` |
| Day name | `strftime('%w', d)` (0 = Sunday) | `DAYNAME(d)` | `to_char(d, 'Day')` |

### Extracting parts: strftime

`strftime` returns **text**. The most used format codes: `%Y` year, `%m` month (01–12), `%d` day, `%H` hour, `%M` minute, `%S` second, `%w` weekday (0 = Sunday), `%j` day of year, `%W` week of year, `%s` epoch seconds.

```sql-run dataset=bank
SELECT txn_date,
       strftime('%Y', txn_date)                  AS yr,
       CAST(strftime('%m', txn_date) AS INTEGER) AS month_num,
       strftime('%Y-%m', txn_date)               AS year_month,
       strftime('%w', txn_date)                  AS weekday_num,
       strftime('%H', txn_date)                  AS hour
FROM txn
LIMIT 5;
```

Because the result is text, `strftime('%m', d) = 3` is **false** (`'03'` vs `3`); compare with `'03'` or CAST to INTEGER.

Grouping by a truncated date is the foundation of every time-series report:

```sql-run dataset=shop
SELECT strftime('%Y-%m', order_date) AS month,
       COUNT(*) AS orders
FROM orders
GROUP BY month
ORDER BY month;
```

And by weekday, with a readable label:

```sql-run dataset=bank
SELECT CASE strftime('%w', txn_date)
         WHEN '0' THEN 'Sun' WHEN '1' THEN 'Mon' WHEN '2' THEN 'Tue' WHEN '3' THEN 'Wed'
         WHEN '4' THEN 'Thu' WHEN '5' THEN 'Fri' ELSE 'Sat' END AS weekday,
       COUNT(*) AS txns
FROM txn
GROUP BY strftime('%w', txn_date)
ORDER BY strftime('%w', txn_date);
```

### Differences between dates

Subtract Julian day numbers to get days (with a fractional part for times):

```sql-run dataset=bank
SELECT emp_id, fname, start_date,
       CAST(julianday('2024-12-31') - julianday(start_date) AS INTEGER) AS days_employed,
       CAST((julianday('2024-12-31') - julianday(start_date)) / 365.25 AS INTEGER) AS years_employed
FROM employee
ORDER BY start_date
LIMIT 6;
```

For hours or minutes multiply by 24 or 1440; for seconds, subtracting `unixepoch()` values is exact:

```sql-run dataset=mlops
SELECT run_id, model_type,
       ROUND((julianday(ended_at) - julianday(started_at)) * 24, 2) AS hours,
       unixepoch(ended_at) - unixepoch(started_at) AS seconds
FROM runs
WHERE status = 'FINISHED'
ORDER BY hours DESC
LIMIT 5;
```

> [!WARNING]
> Never subtract ISO strings directly: `'2024-03-07' - '2023-01-01'` coerces each string to its leading number (2024 − 2023 = 1). No error, wrong answer.

Exact age in years needs care around birthdays. A reliable formula compares month-day strings:

```sql-run dataset=bank
SELECT fname, lname, birth_date,
       CAST(strftime('%Y', '2024-12-31') AS INTEGER) - CAST(strftime('%Y', birth_date) AS INTEGER)
         - (strftime('%m-%d', '2024-12-31') < strftime('%m-%d', birth_date)) AS age
FROM individual
LIMIT 6;
```

(PostgreSQL: `EXTRACT(YEAR FROM age(d))`; MySQL: `TIMESTAMPDIFF(YEAR, d, CURDATE())`.)

### Filtering on dates: stay sargable

Both of these select March 2024, but only the first can use an index on `txn_date`:

```sql
WHERE txn_date >= '2024-03-01' AND txn_date < '2024-04-01'   -- range on the raw column
WHERE strftime('%Y-%m', txn_date) = '2024-03'                 -- function hides the column
```

Prefer half-open ranges on the bare column for filtering; use `strftime` for *labelling and grouping*.

## Conversion functions

`CAST(expr AS type)` is the standard conversion and works in every engine:

```sql-run dataset=bank
SELECT CAST('1456328' AS INTEGER)  AS str_to_int,
       CAST('999ABC111' AS INTEGER) AS partial,
       CAST('abc' AS INTEGER)       AS not_a_number,
       CAST(3.99 AS INTEGER)        AS real_to_int,
       CAST(42 AS TEXT) || '!'      AS int_to_text,
       CAST('3.14' AS REAL) * 2     AS str_to_real;
```

The book shows the same partial-conversion behaviour in MySQL: `'999ABC111'` converts to 999, stopping at the first non-digit (MySQL adds a warning). SQLite returns 0 for `'abc'`; PostgreSQL is strict and raises an error for both — arguably the safest behaviour. Note that `CAST(3.99 AS INTEGER)` truncates; use `round()` first if you want rounding.

Implicit conversion also happens — `'5' + 3` is 8 in SQLite and MySQL, an error in PostgreSQL. Don't rely on it: comparisons between text and numbers follow confusing rules (in SQLite a number is always "less than" a text value unless column affinity converts it), and implicit casts can disable indexes.

PostgreSQL has a shorthand `expr::type`; MySQL also offers `CONVERT(expr, type)`. For formatted conversions use `printf`/`strftime` (SQLite), `FORMAT`/`DATE_FORMAT` (MySQL), `to_char` (PostgreSQL/Oracle).

## Worked example: label delay

In online ML the true label for a prediction often arrives later. Here we don't have a label timestamp, but we can report how many predictions per week still lack a label — a simple *label coverage* monitor:

```sql-run dataset=mlops
SELECT strftime('%Y-W%W', predicted_at) AS week,
       COUNT(*) AS predictions,
       COUNT(actual_label) AS labeled,
       ROUND(100.0 * COUNT(actual_label) / COUNT(*), 1) AS coverage_pct
FROM predictions
WHERE predicted_at >= '2024-03-01' AND predicted_at < '2024-05-01'
GROUP BY week
ORDER BY week;
```

## Pitfalls

- **Non-ISO date strings** — unparsable in SQLite, mis-sorted everywhere.
- **`strftime` returns text** — compare with `'03'`, not `3`.
- **Subtracting date strings** — use `julianday` or `unixepoch`.
- **Month arithmetic at month ends** differs between engines.
- **Inclusive upper bounds on timestamps** miss the last day; use half-open ranges.
- **`now` in tests** — non-deterministic.
- **Mixing local time and UTC.**

## Worked example: a time-series report from raw timestamps

Almost every date question follows the same three moves: **truncate** timestamps to a period, **aggregate** per period, and **compare** periods. Work through one end to end: *for each week of Q4 2024, how many orders were placed, what was the average gap between a customer's signup and the order, and what share of orders arrived on a weekend?*

```sql-run dataset=shop
SELECT date(o.order_date, 'weekday 0', '-6 days') AS week_start,
       COUNT(*) AS orders,
       ROUND(AVG(julianday(o.order_date) - julianday(c.signup_date)), 1) AS avg_days_since_signup,
       ROUND(100.0 * SUM(strftime('%w', o.order_date) IN ('0', '6')) / COUNT(*), 1) AS weekend_pct
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
WHERE o.order_date >= '2024-10-01' AND o.order_date < '2025-01-01'
GROUP BY week_start
ORDER BY week_start;
```

Three date techniques in four lines:

- **Truncating to the week.** SQLite has no "start of week" modifier, so combine two: `'weekday 0'` moves forward to the next Sunday (or stays, if the date is a Sunday), and `'-6 days'` steps back to the Monday of that week. PostgreSQL: `date_trunc('week', d)`; MySQL: `DATE_SUB(d, INTERVAL WEEKDAY(d) DAY)`.
- **A duration** as a difference of Julian days.
- **A weekday test** on `strftime('%w', …)`, comparing with *strings* `'0'` (Sunday) and `'6'` (Saturday).

The filter is a half-open range on the bare column, so it stays index-friendly even though the SELECT list wraps `order_date` in functions.

### Truncation cheat sheet

Truncating to a period is the single most common date operation, so here it is for every grain you are likely to need:

```sql-run dataset=bank
SELECT txn_date,
       date(txn_date)                                   AS day,
       date(txn_date, 'weekday 0', '-6 days')           AS week_start_monday,
       date(txn_date, 'start of month')                 AS month_start,
       strftime('%Y', txn_date) || '-Q' || ((CAST(strftime('%m', txn_date) AS INTEGER) + 2) / 3) AS quarter,
       date(txn_date, 'start of year')                  AS year_start,
       strftime('%Y-%m-%d %H:00:00', txn_date)          AS hour_start
FROM txn
WHERE txn_id IN (1, 150, 300, 450);
```

Prefer a truncated **date value** (`'2024-03-01'`) over a label (`'March'`) for grouping: it sorts correctly, can be compared and joined, and is unambiguous across years.

## Worked example: durations, deadlines and ages

**Elapsed time in sensible units.** A duration is a number of days with a fraction; convert by multiplying. Format it for humans with integer arithmetic:

```sql-run dataset=mlops
SELECT run_id, started_at, ended_at,
       CAST((julianday(ended_at) - julianday(started_at)) * 24 AS INTEGER) AS whole_hours,
       CAST((julianday(ended_at) - julianday(started_at)) * 1440 AS INTEGER) % 60 AS extra_minutes,
       printf('%dh %02dm',
              CAST((julianday(ended_at) - julianday(started_at)) * 24 AS INTEGER),
              CAST((julianday(ended_at) - julianday(started_at)) * 1440 AS INTEGER) % 60) AS duration
FROM runs
WHERE status = 'FINISHED' AND experiment_id = 5
ORDER BY run_id
LIMIT 6;
```

**Deadlines.** "Which funds are still unavailable two days after the transaction?" compares a stored timestamp with a computed one:

```sql-run dataset=bank
SELECT txn_id, txn_date, funds_avail_date,
       ROUND(julianday(funds_avail_date) - julianday(txn_date), 1) AS hold_days
FROM txn
WHERE funds_avail_date >= datetime(txn_date, '+2 days')
ORDER BY txn_date
LIMIT 6;
```

**Bucketing by age or tenure** — a typical feature for a churn model:

```sql-run dataset=shop
SELECT CASE
         WHEN julianday('2024-12-31') - julianday(signup_date) < 90  THEN '1: under 3 months'
         WHEN julianday('2024-12-31') - julianday(signup_date) < 180 THEN '2: 3-6 months'
         WHEN julianday('2024-12-31') - julianday(signup_date) < 365 THEN '3: 6-12 months'
         ELSE '4: over a year' END AS tenure,
       COUNT(*) AS customers
FROM customers
GROUP BY tenure
ORDER BY tenure;
```

Note the fixed reference date `'2024-12-31'`. Using `'now'` would make the buckets drift every day — fine for a live dashboard, wrong for a reproducible training set. In ML pipelines the reference date should be an explicit parameter (the *as-of* date).

## Time zones, concretely

SQLite can shift a UTC timestamp by a fixed offset or to the machine's local zone, but it has no time-zone database:

```sql-run dataset=bank
SELECT '2024-03-10 06:30:00'                          AS stored_utc,
       datetime('2024-03-10 06:30:00', '-5 hours')    AS new_york_standard_time,
       datetime('2024-03-10 06:30:00', '+9 hours')    AS tokyo,
       date('2024-03-10 06:30:00', '+9 hours')        AS tokyo_calendar_day,
       date('2024-03-10 01:30:00', '-5 hours')        AS new_york_calendar_day;
```

The last column shows why zones matter for reporting: 01:30 UTC on 10 March is still **9 March** in New York. "Daily orders" therefore depends on whose day you mean, and a fixed offset is wrong for half the year wherever daylight saving applies. PostgreSQL handles this properly with `ts AT TIME ZONE 'America/New_York'`, MySQL with `CONVERT_TZ(ts, 'UTC', 'America/New_York')`.

> [!INTERVIEW]
> Date questions are where dialect knowledge is tested. If you cannot recall a function name, say what it should do — "truncate to month", "difference in days" — and write the portable half-open range filter. Interviewers accept `date_trunc`-style pseudocode far more readily than a wrong boundary condition.

## Summary

- Store ISO-8601 (ideally UTC). SQLite's `date/time/datetime/julianday/unixepoch/strftime` plus modifiers cover generation and arithmetic.
- Truncate with `'start of month'` / `strftime('%Y-%m', …)`; difference with `julianday(b) - julianday(a)`.
- Filter with half-open ranges on the raw column; group and label with `strftime`.
- `CAST` converts between types; behaviour on malformed input differs (SQLite/MySQL lenient, PostgreSQL strict).
- Date functions are the least portable part of SQL — translate using the tables above.

```quiz
[
  {"q": "What does date('2024-03-07', 'start of month', '+1 month', '-1 day') return?", "options": ["2024-03-01", "2024-03-31", "2024-04-01", "2024-04-06"], "answer": 1, "explain": "Modifiers apply left to right: 1 March, then 1 April, then 31 March - the last day of the month."},
  {"q": "Why is strftime('%m', txn_date) = 3 false for a March date?", "options": ["Months are 0-based", "strftime returns text '03', which does not equal the integer 3", "It returns the month name", "It is true"], "answer": 1, "explain": "Compare with '03' or CAST the result to INTEGER."},
  {"q": "How do you compute the number of days between two ISO dates in SQLite?", "options": ["b - a", "julianday(b) - julianday(a)", "datediff(b, a)", "days(b, a)"], "answer": 1, "explain": "Julian day numbers are numeric and subtract cleanly; subtracting strings coerces to the year only."},
  {"q": "Which filter can use an index on txn_date?", "options": ["strftime('%Y', txn_date) = '2024'", "txn_date >= '2024-01-01' AND txn_date < '2025-01-01'", "substr(txn_date, 1, 4) = '2024'", "CAST(txn_date AS INTEGER) = 2024"], "answer": 1, "explain": "A range on the bare column is sargable; wrapping the column in a function is not."},
  {"q": "What is CAST(3.99 AS INTEGER)?", "options": ["4", "3", "3.99", "Error"], "answer": 1, "explain": "CAST to integer truncates toward zero."},
  {"q": "Which is PostgreSQL's way to truncate a timestamp to the first of its month?", "options": ["date(d, 'start of month')", "DATE_FORMAT(d, '%Y-%m-01')", "date_trunc('month', d)", "trunc_month(d)"], "answer": 2, "explain": "date_trunc is PostgreSQL's truncation function."},
  {"q": "What is the safest storage convention for instants?", "options": ["Local time as text", "UTC in ISO-8601 or a timezone-aware type", "Epoch as text", "Month/day/year strings"], "answer": 1, "explain": "UTC avoids daylight-saving ambiguity and ISO sorts correctly."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 7 "Working with Temporal Data" (time zones, generating and manipulating temporal data) and "Conversion Functions". SQLite documentation, "Date And Time Functions".
