# Dates, times and conversion

> **Before this lesson:** you should know what a function and an argument are, how `substr` cuts a piece out of a string, and why dividing two whole numbers drops the decimals ([Strings and numbers](#/lesson/sql/strings-numbers)). Examples also use `COUNT(*)` with `GROUP BY` and `CASE`; each is explained briefly where it appears.

## In plain words

A date looks simple and is not. Months have different lengths, some years have an extra day, the same instant is Monday evening in one city and Tuesday morning in another, and people write the third of July as 03/07 or 07/03 depending on where they grew up. A database needs clear rules to store a moment in time and to calculate with it.

There are three things you do with dates, and this lesson takes them in turn:

1. **Make one**: from text, from the clock, or from a number.
2. **Work with it**: add a week, find the start of the month, pull out the year, measure the gap between two dates.
3. **Convert it**, and other values, from one data type to another.

An everyday picture: a wall calendar and a stopwatch. The calendar answers "which day, which week, which month does this belong to?" (useful for grouping). The stopwatch answers "how long between these two moments?" (useful for durations). Almost every date question in SQL is one of those two.

Be warned that date functions are the least standard part of SQL. Nearly every example here is spelled differently in MySQL and PostgreSQL. The ideas carry over unchanged, and tables give the translations.

**Why it matters for a job.** "Orders per month", "users active in the last 7 days", "average time to resolve a ticket": most business reports are organised by time. Interview tasks on dates test two things: whether you know the functions, and whether you get the boundaries right (does "March" include the last second of 31 March?).

## Time zones in one page

The world is divided into **time zones** so that noon is roughly when the sun is highest wherever you are. The common reference is **UTC** (Coordinated Universal Time), the time on the zero meridian with no seasonal clock change. Tokyo is UTC plus 9 hours; New York is UTC minus 5 in winter and minus 4 in summer, because of **daylight saving time**, the practice of moving clocks forward in summer.

Guidelines that prevent most trouble:

- Store moments in **UTC** and convert to local time only when showing them to a person.
- Know what your column type does. In PostgreSQL, `timestamptz` stores an exact instant and shows it in your session's zone, while plain `timestamp` stores clock digits with no zone. In MySQL, `TIMESTAMP` converts to UTC for storage and `DATETIME` does not.
- SQLite stores whatever text you give it. Its special value `'now'` is the current time in UTC; the extra word `'localtime'` converts to the computer's own zone.

```sql-run dataset=bank
SELECT datetime('now')              AS utc_now,
       datetime('now', 'localtime') AS local_now,
       date('now')                  AS utc_today;
```

The first two columns differ by your distance from UTC (they are equal if your clock is on UTC).

> [!WARNING]
> A query that uses `'now'` gives a different answer every day. That is right for a live dashboard and wrong for a test or a graded exercise. The practice datasets are frozen in 2024, so the examples use fixed dates.

## How SQLite stores dates and times

SQLite has no separate date type. Its date functions understand three ways of writing a moment:

| Form | Example | Stored as |
|---|---|---|
| ISO-8601 text | `'2024-03-07 14:22:00'` | text |
| Julian day number | `2460377.0986`, days counted from a fixed day far in the past | decimal number |
| Unix epoch | `1709821320`, seconds since 1 January 1970 UTC | whole number |

**ISO-8601** is an international standard for writing dates: year, month, day, from largest unit to smallest, with leading zeros. It has a valuable property: sorting the text alphabetically also sorts it by time. All the practice datasets use it.

The functions all take a time value followed by optional **modifiers**, short instructions that change it:

| Function | Returns |
|---|---|
| `date(...)` | `'YYYY-MM-DD'` |
| `time(...)` | `'HH:MM:SS'` |
| `datetime(...)` | `'YYYY-MM-DD HH:MM:SS'` |
| `julianday(...)` | a day number with decimals, for arithmetic |
| `unixepoch(...)` | seconds since 1970 |
| `strftime(format, ...)` | text in any layout you describe |

## Making a date

**From text.** ISO text already is a valid date. Any other layout must be rearranged first, because SQLite cannot read `'03/07/2024'`:

```sql-run dataset=bank
SELECT date('2024-03-07')              AS iso,
       date('03/07/2024')              AS us_style_fails,
       substr('03/07/2024', 7, 4) || '-' || substr('03/07/2024', 1, 2) || '-' || substr('03/07/2024', 4, 2) AS rebuilt;
```

The first column is the date. The second is empty (NULL): the function did not understand the text and, instead of raising an error, returned nothing. The third rebuilds an ISO date by cutting out the year (4 characters from position 7), the month and the day with `substr` and joining them with dashes.

> [!NOTE]
> **Reading other layouts elsewhere.** MySQL: `STR_TO_DATE('03/07/2024', '%m/%d/%Y')`. PostgreSQL and Oracle: `to_date('03/07/2024', 'MM/DD/YYYY')`. The standard also has typed literals: `DATE '2024-03-07'`.

**From the clock.** `CURRENT_DATE`, `CURRENT_TIME` and `CURRENT_TIMESTAMP` are standard and work everywhere (MySQL also has `NOW()`).

**From a number.** `datetime(1709821320, 'unixepoch')` turns epoch seconds into readable text. Event logs often store time this way.

## Working with dates

### Adding and subtracting: modifiers

Modifiers are applied from left to right.

```sql-run dataset=bank
SELECT date('2024-01-31', '+1 month')                  AS plus_month,
       date('2024-03-07', '-7 days')                   AS week_ago,
       date('2024-03-07', 'start of month')            AS month_start,
       date('2024-03-07', 'start of month', '+1 month', '-1 day') AS month_end,
       date('2024-03-07', 'start of year')             AS year_start,
       date('2024-03-07', 'weekday 0')                 AS next_sunday,
       datetime('2024-03-07 14:22:00', '+90 minutes')  AS later;
```

Column by column:

- `'+1 month'` on 31 January gives **2 March**. There is no 31 February, so SQLite counts the overflow into March. MySQL and PostgreSQL stop at the last day of February instead. Adding months near the end of a month is ambiguous by nature.
- `'-7 days'` gives 29 February (2024 is a leap year).
- `'start of month'` gives 1 March.
- Three modifiers in a row give the last day of the month: go to 1 March, add a month (1 April), go back a day (31 March). This is the reliable recipe; MySQL has `LAST_DAY(d)`.
- `'weekday 0'` moves forward to the next Sunday (0 is Sunday, 6 is Saturday), or stays put if the date is already a Sunday.
- `'+90 minutes'` works on a date with a time.

| Task | SQLite | MySQL | PostgreSQL |
|---|---|---|---|
| Add 5 days | `date(d, '+5 days')` | `DATE_ADD(d, INTERVAL 5 DAY)` | `d + INTERVAL '5 days'` |
| First day of the month | `date(d, 'start of month')` | `DATE_FORMAT(d, '%Y-%m-01')` | `date_trunc('month', d)` |
| Days between | `julianday(b) - julianday(a)` | `DATEDIFF(b, a)` | `b::date - a::date` |
| Year of a date | `strftime('%Y', d)` | `YEAR(d)` | `EXTRACT(YEAR FROM d)` |
| Custom layout | `strftime(fmt, d)` | `DATE_FORMAT(d, fmt)` | `to_char(d, fmt)` |

### Pulling out parts: strftime

`strftime` ("string format time") builds text from a date according to a pattern. Codes in the pattern stand for parts of the date: `%Y` year, `%m` month (01–12), `%d` day, `%H` hour, `%M` minute, `%S` second, `%w` day of the week (0 = Sunday), `%W` week of the year.

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

For the transaction at `2024-01-02 15:57:00` this gives `'2024'`, 1, `'2024-01'`, `'2'` (a Tuesday) and `'15'`.

`strftime` always returns **text**. That has a consequence: `strftime('%m', d) = 3` is false for a March date, because the text `'03'` is not the number 3. Compare with `'03'`, or convert with `CAST(... AS INTEGER)` as the third column does.

Cutting every date down to its period and counting is the basis of every report over time. Reducing a date to the start of its period is called **truncation**.

```sql-run dataset=shop
SELECT strftime('%Y-%m', order_date) AS month,
       COUNT(*) AS orders
FROM orders
GROUP BY month
ORDER BY month;
```

Every order date becomes a label such as `'2024-02'`; `GROUP BY month` gathers the orders sharing a label and `COUNT(*)` counts each group. Twelve rows, one per month.

The same idea by day of the week, with `CASE` turning the digit into a name:

```sql-run dataset=bank
SELECT CASE strftime('%w', txn_date)
         WHEN '0' THEN 'Sun' WHEN '1' THEN 'Mon' WHEN '2' THEN 'Tue' WHEN '3' THEN 'Wed'
         WHEN '4' THEN 'Thu' WHEN '5' THEN 'Fri' ELSE 'Sat' END AS weekday,
       COUNT(*) AS txns
FROM txn
GROUP BY strftime('%w', txn_date)
ORDER BY strftime('%w', txn_date);
```

### The gap between two dates

Convert both dates to Julian day numbers and subtract. The result is a number of days.

```sql-run dataset=bank
SELECT emp_id, fname, start_date,
       CAST(julianday('2024-12-31') - julianday(start_date) AS INTEGER) AS days_employed,
       CAST((julianday('2024-12-31') - julianday(start_date)) / 365.25 AS INTEGER) AS years_employed
FROM employee
ORDER BY start_date
LIMIT 6;
```

John, who started on 11 May 2018, had been employed 2,426 days at the end of 2024, which is 6 whole years (dividing by 365.25 allows for leap years).

For hours multiply the day difference by 24, for minutes by 1440. For seconds, subtract `unixepoch` values:

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
> Never subtract date text directly. `'2024-03-07' - '2023-01-01'` reads the leading number of each string and computes 2024 − 2023 = 1. There is no error, only a wrong answer.

A person's exact age needs care around the birthday. Subtract the years, then take one off if this year's birthday has not happened yet:

```sql-run dataset=bank
SELECT fname, lname, birth_date,
       CAST(strftime('%Y', '2024-12-31') AS INTEGER) - CAST(strftime('%Y', birth_date) AS INTEGER)
         - (strftime('%m-%d', '2024-12-31') < strftime('%m-%d', birth_date)) AS age
FROM individual
LIMIT 6;
```

The comparison in parentheses is 1 when the month-and-day of the reference date comes before the month-and-day of the birthday, and 0 otherwise. (PostgreSQL: `EXTRACT(YEAR FROM age(d))`; MySQL: `TIMESTAMPDIFF(YEAR, d, CURDATE())`.)

### Filtering on dates

Both conditions below select March 2024:

```sql
WHERE txn_date >= '2024-03-01' AND txn_date < '2024-04-01'   -- range on the column itself
WHERE strftime('%Y-%m', txn_date) = '2024-03'                 -- function wrapped around the column
```

Prefer the first. An **index** is a lookup structure that lets the database jump to the rows it needs, as the index of a book does ([Indexes and query plans](#/lesson/sql/indexes)). An index on `txn_date` can serve a range on the bare column, but not a condition where the column is hidden inside a function; then every row must be read. A condition that an index can serve is called **sargable**.

The first form is also a **half-open range**: the start is included (`>=`) and the end is excluded (`<`). It catches every moment of 31 March up to midnight, which `<= '2024-03-31'` would miss for any time after 00:00:00.

The rule: half-open ranges on the bare column for *filtering*; `strftime` for *labelling and grouping*.

## Conversion functions

`CAST(value AS type)` converts a value to another data type and works in every database.

```sql-run dataset=bank
SELECT CAST('1456328' AS INTEGER)  AS str_to_int,
       CAST('999ABC111' AS INTEGER) AS partial,
       CAST('abc' AS INTEGER)       AS not_a_number,
       CAST(3.99 AS INTEGER)        AS real_to_int,
       CAST(42 AS TEXT) || '!'      AS int_to_text,
       CAST('3.14' AS REAL) * 2     AS str_to_real;
```

- Text made of digits becomes the number 1456328.
- `'999ABC111'` becomes **999**: SQLite reads digits until the first character that is not one, and stops. MySQL does the same with a warning.
- `'abc'` becomes **0**. PostgreSQL refuses both of these with an error, which is the safer behaviour, since a silent 0 can hide bad data.
- `3.99` becomes 3: conversion to an integer cuts the decimals off. Call `round()` first if you want 4.
- A number converted to text can be joined to other text.

A database may also convert without being asked, which is called **implicit conversion**: `'5' + 3` is 8 in SQLite and MySQL and an error in PostgreSQL. Do not depend on it. Comparisons between text and numbers follow rules that surprise people, and a hidden conversion can stop an index from being used.

PostgreSQL has the shorthand `value::type`; MySQL also offers `CONVERT(value, type)`.

## Worked example: a weekly report from raw dates

Most date questions repeat three moves: **truncate** each date to a period, **aggregate** (count or average) per period, and **compare** periods. Here is one from start to finish: *for each week of the last quarter of 2024, how many orders were placed, how long on average after the customer's sign-up, and what share fell on a weekend?*

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

- **Truncating to the week.** SQLite has no "start of week" modifier, so two are combined: `'weekday 0'` moves forward to Sunday, then `'-6 days'` steps back to the Monday of that week. (PostgreSQL: `date_trunc('week', d)`.)
- **A duration**: the difference of two Julian day numbers, averaged per week.
- **A weekend test**: the weekday digit is compared with the *texts* `'0'` and `'6'`. The test is 1 when true, so `SUM` counts weekend orders, and `100.0 *` keeps the percentage in decimals.
- **The filter** is a half-open range on the bare column.

The first row is the week starting Monday 30 September: two orders, both on a weekend.

### Truncation at every level

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

The quarter expression uses integer division: months 1–3 give (m + 2) / 3 = 1, months 4–6 give 2, and so on. For grouping, prefer a truncated **date** (`'2024-03-01'`) to a name (`'March'`): it sorts correctly, can be compared, and does not confuse March 2024 with March 2025.

## Worked example: durations, deadlines and ages

**Elapsed time in readable units.** A duration in days is turned into hours and minutes with multiplication, integer conversion and the remainder operator `%`:

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

Run 45 started at 13:00:00 and ended at 23:18:44. Total minutes divided by 60 leaves a remainder of 18, so the duration reads `10h 18m`.

**Deadlines.** "Which deposits were held for at least two days before the money became available?" compares a stored time with a calculated one:

```sql-run dataset=bank
SELECT txn_id, txn_date, funds_avail_date,
       ROUND(julianday(funds_avail_date) - julianday(txn_date), 1) AS hold_days
FROM txn
WHERE funds_avail_date >= datetime(txn_date, '+2 days')
ORDER BY txn_date
LIMIT 6;
```

**Bands of age or length of membership.** How long someone has been a customer is called **tenure**:

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

`CASE` checks the conditions from top to bottom and stops at the first true one. Note the fixed reference date `'2024-12-31'`. With `'now'` the bands would shift every day. In data pipelines the reference date should be a stated input, often called the **as-of date**, so that a result can be reproduced later.

## Time zones, concretely

SQLite can shift a time by a fixed number of hours, but it holds no table of the world's time zones and their rules.

```sql-run dataset=bank
SELECT '2024-03-10 06:30:00'                          AS stored_utc,
       datetime('2024-03-10 06:30:00', '-5 hours')    AS new_york_standard_time,
       datetime('2024-03-10 06:30:00', '+9 hours')    AS tokyo,
       date('2024-03-10 06:30:00', '+9 hours')        AS tokyo_calendar_day,
       date('2024-03-10 01:30:00', '-5 hours')        AS new_york_calendar_day;
```

The last column shows why zones matter for reports: 01:30 UTC on 10 March is still **9 March** in New York. "Orders per day" therefore depends on whose day you mean. A fixed offset is also wrong for half the year wherever daylight saving applies. PostgreSQL handles this properly with `ts AT TIME ZONE 'America/New_York'`, MySQL with `CONVERT_TZ(ts, 'UTC', 'America/New_York')`.

## Worked example: how many predictions have been checked?

In the `mlops` data each prediction has a `predicted_label` and, once the truth is known, an `actual_label`. The truth often arrives late, so `actual_label` starts out NULL. This report shows, per week, what share of predictions has its true answer. `COUNT(column)` counts only the rows where the column is not NULL.

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

In week 9, 24 of 27 predictions (88.9%) have a known answer.

> [!INTERVIEW]
> Date questions are where knowledge of a specific database is tested. If you cannot recall a function name, say what it should do ("truncate to the month", "difference in days") and write the half-open range filter, which works everywhere. Interviewers accept `date_trunc`-style pseudocode far more readily than a wrong boundary.

## Pitfalls

- **Dates not in ISO form** cannot be read by SQLite and sort wrongly everywhere.
- **`strftime` returns text.** Compare with `'03'`, not `3`.
- **Subtracting date text.** Use `julianday` or `unixepoch`.
- **Adding months at the end of a month** behaves differently between databases.
- **An inclusive upper bound** (`<= '2024-03-31'`) misses most of the last day when the column holds times. Use a half-open range.
- **`'now'` in tests** gives results that change from day to day.
- **Mixing local time and UTC** in one calculation.

## Summary

- Store ISO-8601 text, ideally in UTC. SQLite's `date`, `time`, `datetime`, `julianday`, `unixepoch` and `strftime`, with modifiers, cover making and calculating.
- Truncate with `'start of month'` or `strftime('%Y-%m', ...)`; measure a gap with `julianday(b) - julianday(a)`.
- Filter with half-open ranges on the bare column; group and label with `strftime`.
- `CAST` converts between types; what happens to malformed input differs (SQLite and MySQL are lenient, PostgreSQL is strict).
- Date functions are the least portable part of SQL; translate with the tables above.

## Glossary

- **Time zone** — a region that keeps the same clock time.
- **UTC** — Coordinated Universal Time, the worldwide reference time.
- **Daylight saving time** — moving clocks forward in summer, which changes a zone's distance from UTC.
- **ISO-8601** — the standard year-month-day way of writing dates, which sorts correctly as text.
- **Julian day number** — a count of days from a fixed day in the distant past, used for date arithmetic.
- **Unix epoch** — the number of seconds since 1 January 1970 UTC.
- **Modifier** — in SQLite, a short instruction such as `'+1 month'` that changes a date.
- **`strftime`** — the function that formats a date as text using `%` codes.
- **Truncation (of a date)** — reducing a date to the start of its day, week, month or year.
- **Half-open range** — a range that includes its start and excludes its end.
- **Sargable** — describes a condition that an index can be used to answer.
- **`CAST`** — the standard function for converting a value to another type.
- **Implicit conversion** — a type conversion the database performs without being asked.
- **Tenure** — how long someone has been a customer or employee.
- **As-of date** — the fixed reference date used in a calculation instead of "now".

```quiz
[
  {"q": "What does date('2024-03-07', 'start of month', '+1 month', '-1 day') return?", "options": ["2024-03-01", "2024-03-31", "2024-04-01", "2024-04-06"], "answer": 1, "explain": "Modifiers apply left to right: 1 March, then 1 April, then back one day to 31 March, the last day of the month."},
  {"q": "Why is strftime('%m', txn_date) = 3 false for a March date?", "options": ["Months are counted from 0", "strftime returns the text '03', which does not equal the number 3", "It returns the month name", "It is true"], "answer": 1, "explain": "Compare with '03' or CAST the result to INTEGER."},
  {"q": "How do you compute the number of days between two ISO dates in SQLite?", "options": ["b - a", "julianday(b) - julianday(a)", "datediff(b, a)", "days(b, a)"], "answer": 1, "explain": "Julian day numbers subtract cleanly; subtracting the text itself only subtracts the leading years."},
  {"q": "Which filter can use an index on txn_date?", "options": ["strftime('%Y', txn_date) = '2024'", "txn_date >= '2024-01-01' AND txn_date < '2025-01-01'", "substr(txn_date, 1, 4) = '2024'", "CAST(txn_date AS INTEGER) = 2024"], "answer": 1, "explain": "A range on the bare column is sargable; wrapping the column in a function hides it from the index."},
  {"q": "What is CAST(3.99 AS INTEGER)?", "options": ["4", "3", "3.99", "An error"], "answer": 1, "explain": "Conversion to an integer cuts the decimals off; it does not round."},
  {"q": "Which is PostgreSQL's way to truncate a timestamp to the first of its month?", "options": ["date(d, 'start of month')", "DATE_FORMAT(d, '%Y-%m-01')", "date_trunc('month', d)", "trunc_month(d)"], "answer": 2, "explain": "date_trunc is PostgreSQL's truncation function; the first option is SQLite and the second MySQL."},
  {"q": "What is the safest way to store a moment in time?", "options": ["Local time as text", "UTC, in ISO-8601 text or a time-zone-aware type", "Epoch seconds as text", "Month/day/year strings"], "answer": 1, "explain": "UTC avoids daylight-saving ambiguity, and ISO text sorts in time order."},
  {"q": "A column holds dates with times. Why is txn_date <= '2024-03-31' a poor way to end a March filter?", "options": ["It is a syntax error", "It excludes every transaction on 31 March after midnight", "It includes April", "It cannot use an index"], "answer": 1, "explain": "'2024-03-31 09:00:00' sorts after '2024-03-31', so most of the last day is lost; use < '2024-04-01'."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 7 "Working with Temporal Data" (time zones, generating and manipulating temporal data) and "Conversion Functions", restated in original wording. SQLite documentation, "Date And Time Functions".
