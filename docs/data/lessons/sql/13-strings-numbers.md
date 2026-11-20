# Strings and numbers

Raw data is rarely in the shape you need. Names arrive in the wrong case, emails have stray spaces, amounts need rounding, identifiers need zero-padding. Every database ships a library of built-in functions for generating, converting and manipulating data — and, as the book warns, this is the area where vendors differ the most, because the SQL standard left much of it open. This lesson covers string and numeric functions using SQLite, with a translation table for MySQL and PostgreSQL. The next lesson handles dates and type conversion.

## Working with string data

### String generation

The simplest way to make a string is a literal in single quotes. Two details matter.

**Embedded quotes.** Double the quote character:

```sql-run dataset=bank
SELECT 'This string didn''t break' AS s, length('didn''t') AS len;
```

MySQL also accepts a backslash escape (`'didn\'t'`); the doubled quote is the standard, portable form. When values come from a program, **never build SQL by string concatenation** — use bound parameters (`WHERE lname = ?`), which is both safe from SQL injection and immune to quoting problems.

**Special characters.** `char(n, ...)` builds a string from character codes and `unicode(s)` returns the code of the first character (MySQL: `CHAR()` / `ASCII()`; PostgreSQL: `chr()` / `ascii()`):

```sql-run dataset=bank
SELECT char(97, 98, 99) AS abc, char(233) AS e_acute, unicode('é') AS code, hex('abc') AS bytes;
```

**What happens to over-long strings?** In MySQL (strict mode) and PostgreSQL, inserting 50 characters into a `VARCHAR(30)` column raises an error; in non-strict MySQL it truncates with a warning. SQLite stores the whole string regardless of the declared length.

### Concatenation

```sql-run dataset=bank
SELECT fname || ' ' || lname || ' has been a ' || title || ' since ' || start_date AS emp_narrative
FROM employee
WHERE title LIKE '%Teller'
LIMIT 5;
```

`||` is the standard operator (SQLite, PostgreSQL, Oracle). MySQL uses `CONCAT(a, b, ...)` and SQL Server uses `+` or `CONCAT`. Remember that `||` with a NULL operand yields NULL; wrap nullable pieces in `COALESCE(x, '')`. SQLite 3.44+ and the other engines also have `concat()` / `concat_ws(sep, ...)`, which skip NULLs.

### Functions that return numbers

```sql-run dataset=shop
SELECT name,
       length(name)        AS len,
       instr(name, ' ')    AS first_space,
       instr(name, 'Pro')  AS pos_of_pro
FROM products
LIMIT 6;
```

- `length(s)` — number of characters (MySQL: `CHAR_LENGTH`; its `LENGTH` counts bytes).
- `instr(s, sub)` — 1-based position of the first occurrence, or 0 if absent (MySQL: `LOCATE(sub, s)` / `POSITION(sub IN s)`; PostgreSQL: `strpos(s, sub)` / `position(sub in s)`).

Positions in SQL are **1-based**, unlike Python's 0-based indexing.

String comparison is done with the ordinary operators, plus `LIKE`/`GLOB` from the filtering module. For case-insensitive comparison in SQLite use `COLLATE NOCASE` or compare `lower()` values.

### Functions that return strings

| Task | SQLite | MySQL | PostgreSQL |
|---|---|---|---|
| Upper / lower case | `upper(s)`, `lower(s)` | same | same (+ `initcap`) |
| Substring | `substr(s, start, len)` | `SUBSTRING(s, start, len)` | `substring(s from start for len)`, `substr` |
| Trim | `trim(s)`, `ltrim`, `rtrim`, `trim(s, chars)` | `TRIM([chars FROM] s)` | `trim`, `btrim(s, chars)` |
| Replace | `replace(s, from, to)` | same | same |
| Position | `instr(s, sub)` | `LOCATE(sub, s)` | `strpos(s, sub)` |
| Pad | `printf('%05d', n)` / `format()` | `LPAD(s, n, pad)` | `lpad(s, n, pad)` |
| Split by delimiter | `substr` + `instr` | `SUBSTRING_INDEX(s, d, n)` | `split_part(s, d, n)` |
| Concatenate a group | `group_concat(x, sep)` | `GROUP_CONCAT(x SEPARATOR sep)` | `string_agg(x, sep)` |
| Reverse / repeat | — (not built in) | `REVERSE`, `REPEAT` | `reverse`, `repeat` |

`substr` in action. A negative start counts from the end; omitting the length means "to the end":

```sql-run dataset=bank
SELECT fed_id,
       substr(fed_id, 1, 3)  AS first3,
       substr(fed_id, -4)    AS last4,
       '***-**-' || substr(fed_id, -4) AS masked
FROM customer
WHERE cust_type_cd = 'I'
LIMIT 5;
```

Cleaning text — the workhorse combination is `lower(trim(x))`:

```sql-run dataset=shop
SELECT email AS raw,
       lower(trim(email)) AS clean,
       substr(lower(trim(email)), 1, instr(lower(trim(email)), '@') - 1) AS local_part,
       substr(lower(trim(email)), instr(lower(trim(email)), '@') + 1)    AS domain
FROM customer_imports
ORDER BY import_id
LIMIT 8;
```

`replace` substitutes every occurrence:

```sql-run dataset=shop
SELECT name, replace(lower(name), ' ', '-') AS url_slug
FROM products
LIMIT 6;
```

Formatting with `printf` (alias `format` since SQLite 3.38) covers padding and number formatting:

```sql-run dataset=bank
SELECT account_id,
       printf('%08d', account_id)        AS padded_id,
       printf('$%,.2f', avail_balance)   AS pretty_balance,
       printf('%-6s|', product_cd)       AS left_aligned
FROM account
LIMIT 5;
```

Aggregating strings — one row per group with values joined:

```sql-run dataset=bank
SELECT cust_id, group_concat(product_cd, ', ') AS products
FROM account
GROUP BY cust_id
LIMIT 8;
```

> [!NOTE]
> The order of items inside `group_concat` is not guaranteed in SQLite unless you order them (3.44+: `group_concat(product_cd, ', ' ORDER BY product_cd)`). MySQL: `GROUP_CONCAT(product_cd ORDER BY product_cd SEPARATOR ', ')`; PostgreSQL: `string_agg(product_cd, ', ' ORDER BY product_cd)`.

## Working with numeric data

### Arithmetic and integer division

All the usual operators work: `+ - * /` and `%` (modulo). The one that bites is `/`:

```sql-run dataset=bank
SELECT 7 / 2      AS int_div,
       7 / 2.0    AS real_div,
       7 % 2      AS remainder,
       CAST(7 AS REAL) / 2 AS cast_div,
       -7 / 2     AS neg_int_div;
```

In SQLite, PostgreSQL and SQL Server, **integer / integer is integer division** (truncating toward zero). In MySQL and Oracle `/` always yields a decimal, and MySQL has a separate `DIV` operator for integer division. For portable percentages multiply by `100.0` or cast:

```sql-run dataset=mlops
SELECT COUNT(*) AS runs,
       SUM(status = 'FAILED') AS failed,
       100 * SUM(status = 'FAILED') / COUNT(*)   AS pct_wrong,
       ROUND(100.0 * SUM(status = 'FAILED') / COUNT(*), 1) AS pct_right
FROM runs;
```

(`SUM(status = 'FAILED')` works because SQLite and MySQL evaluate a comparison to 1 or 0. PostgreSQL has a real boolean type, so there you write `COUNT(*) FILTER (WHERE status = 'FAILED')` or `SUM(CASE WHEN ... THEN 1 ELSE 0 END)`.)

Division by zero returns NULL in SQLite and MySQL but raises an error in PostgreSQL and SQL Server; guard with `NULLIF(divisor, 0)`.

### Mathematical functions

```sql-run dataset=bank
SELECT abs(-25.76)                         AS abs_val,
       (-25.76 > 0) - (-25.76 < 0)         AS sign_of_value,
       22 % 5                              AS modulo,
       2 * 2 * 2 * 2 * 2 * 2 * 2 * 2 * 2 * 2 AS two_to_10,
       1 << 10                             AS two_to_10_by_shift,
       max(3, 7, 5)                        AS largest_of_three,
       min(3, 7, 5)                        AS smallest_of_three,
       round(22 / 7.0, 4)                  AS approx_pi;
```

Everything in that query is **core** SQLite: `abs`, `round`, the `%` modulo operator, the bit-shift operator `<<`, and the multi-argument forms of `max` / `min` (which pick the largest or smallest of their arguments on one row — MySQL and PostgreSQL call these `GREATEST` / `LEAST`). The expression `(x > 0) - (x < 0)` yields −1, 0 or 1: the sign of `x`.

The book lists a much larger family for MySQL: `ACOS/ASIN/ATAN/COS/SIN/TAN`, `EXP`, `LN`, `SQRT`, `MOD`, `POW`, `CEIL`, `FLOOR`, `SIGN`, `TRUNCATE`.

> [!NOTE]
> **Math functions and this sandbox.** `ceil`, `floor`, `trunc`, `power`, `sqrt`, `exp`, `ln`, `log10`, `mod`, `pi` and the trigonometric functions exist in MySQL and PostgreSQL, and in SQLite builds compiled with math functions enabled (`SQLITE_ENABLE_MATH_FUNCTIONS` — the `sqlite3` shell and recent Python builds). The in-browser SQLite used by this guide is built **without** them, so calling them here gives *no such function*. The examples in this track therefore use core operators only, and name the function you would use elsewhere.

| You want | MySQL / PostgreSQL | Core SQLite equivalent |
|---|---|---|
| Modulo | `MOD(a, b)` | `a % b` |
| Truncate toward zero | `TRUNCATE(x, 0)` / `trunc(x)` | `CAST(x AS INTEGER)` |
| Floor | `FLOOR(x)` | `CAST(x AS INTEGER) - (x < CAST(x AS INTEGER))` |
| Ceiling | `CEIL(x)` | `CAST(x AS INTEGER) + (x > CAST(x AS INTEGER))` |
| Sign | `SIGN(x)` | `(x > 0) - (x < 0)` |
| Square, cube | `POWER(x, 2)` | `x * x`, `x * x * x` |
| Power of two | `POWER(2, n)` | `1 << n` |
| Square root, logarithms | `SQRT(x)`, `LN(x)` | not available — compute in the application, or use a full build |

### Controlling number precision

Four operations limit precision: **ceiling** (always up), **floor** (always down), **round** (to nearest) and **truncate** (toward zero). MySQL and PostgreSQL have a function for each (`CEIL`, `FLOOR`, `ROUND`, `TRUNCATE`/`trunc`). Here `round` is built in and the other three are written with `CAST` and a comparison, as in the table above:

```sql-run dataset=bank
SELECT CAST(72.445 AS INTEGER) + (72.445 > CAST(72.445 AS INTEGER)) AS ceil_v,
       CAST(72.445 AS INTEGER) - (72.445 < CAST(72.445 AS INTEGER)) AS floor_v,
       round(72.445)             AS round_0,
       round(72.445, 1)          AS round_1,
       round(72.445, 2)          AS round_2,
       CAST(72.999 AS INTEGER)   AS trunc_v,
       CAST(-72.5 AS INTEGER) - (-72.5 < CAST(-72.5 AS INTEGER)) AS floor_neg,
       CAST(-72.5 AS INTEGER)    AS trunc_neg;
```

The last two columns show the difference that matters for negative numbers: floor goes toward negative infinity (−73), truncation toward zero (−72). `CAST(x AS INTEGER)` truncates; the `(x < CAST(...))` term is 1 exactly when truncation moved the value upward, so subtracting it produces the floor.

`round(72.445, 2)` may surprise you by returning 72.44 or 72.45 depending on the engine: 72.445 cannot be represented exactly in binary floating point. `DECIMAL` columns in MySQL/PostgreSQL round exactly (half away from zero). MySQL's `TRUNCATE(x, d)` and PostgreSQL's `trunc(x, d)` take a digits argument; MySQL and PostgreSQL's `ROUND` also accept a **negative** precision to round to tens or hundreds (`ROUND(17456, -3)` = 17000) — in SQLite compute `round(x / 1000.0) * 1000`.

### Handling signed data

The bank's `txn.amount` is always positive and `txn_type_cd` says whether it is a credit or a debit. A sign expression and `abs()` help when data is stored signed instead (elsewhere: `SIGN(x)`):

```sql-run dataset=bank
SELECT account_id, avail_balance, pending_balance,
       pending_balance - avail_balance        AS diff,
       (pending_balance > avail_balance) - (pending_balance < avail_balance) AS direction,
       abs(pending_balance - avail_balance)   AS magnitude
FROM account
WHERE pending_balance <> avail_balance
LIMIT 6;
```

### Bucketing numbers

A staple of analytics and feature engineering is turning a continuous value into a bucket. Integer division does it in one expression:

```sql-run dataset=mlops
SELECT (latency_ms / 50) * 50 AS bucket_start,
       COUNT(*) AS predictions,
       printf('%.*c', COUNT(*) / 4, '#') AS histogram
FROM predictions
GROUP BY bucket_start
ORDER BY bucket_start;
```

`latency_ms / 50` is integer division, so 0–49 → 0, 50–99 → 50, and so on. The last column abuses `printf` to draw a text histogram.

### Random numbers

`random()` returns a random 64-bit integer in SQLite (MySQL `RAND()` and PostgreSQL `random()` return a float in [0, 1)). Typical uses are sampling and shuffling:

```sql-run dataset=shop
SELECT customer_id, first_name, country
FROM customers
ORDER BY random()
LIMIT 5;
```

Run it twice — different rows each time. (This sorts the whole table, fine for small data; big systems use `TABLESAMPLE` or hash-based sampling such as `WHERE abs(customer_id * 2654435761) % 100 < 10`, which is also *repeatable* — important for reproducible ML train/test splits.)

## Pitfalls

- **Integer division** — `1 / 2 = 0` in SQLite/PostgreSQL/SQL Server.
- **1-based string positions** and `instr` returning 0 (not −1, not NULL) when nothing is found.
- **`||` and NULL** — the whole string becomes NULL.
- **Functions on columns in WHERE** (`WHERE lower(email) = ...`) defeat ordinary indexes; use an expression index or store the normalised value.
- **Dialect drift** — check the function table before porting a query.
- **Concatenating user input into SQL** — use bound parameters.

## Worked example: cleaning a messy text column

String functions are most often used in combination, to repair data. The `customer_imports` table has names and emails typed by hand. Suppose the CRM wants, for every import: a clean email, the email's user name and domain, the person's first and last name in separate columns, initials, and a display name in "LAST, First" form.

Build it incrementally. First isolate the cleaning step in a CTE, so later expressions can use tidy inputs instead of repeating `lower(trim(...))`:

```sql-run dataset=shop
WITH clean AS (
  SELECT import_id,
         lower(trim(email)) AS email,
         trim(full_name)    AS full_name
  FROM customer_imports
)
SELECT import_id,
       email,
       substr(email, 1, instr(email, '@') - 1)  AS user_name,
       substr(email, instr(email, '@') + 1)     AS domain,
       substr(full_name, 1, instr(full_name, ' ') - 1) AS first_name,
       substr(full_name, instr(full_name, ' ') + 1)    AS last_name,
       upper(substr(full_name, 1, 1)) || upper(substr(full_name, instr(full_name, ' ') + 1, 1)) AS initials,
       upper(substr(full_name, instr(full_name, ' ') + 1)) || ', ' || substr(full_name, 1, instr(full_name, ' ') - 1) AS display_name
FROM clean
ORDER BY import_id
LIMIT 8;
```

Read each expression as "find a position, then cut":

- `instr(email, '@')` locates the separator; everything before it (`substr(…, 1, pos - 1)`) is the user name and everything after (`substr(…, pos + 1)`) the domain.
- Names split the same way on the first space.
- Initials take one character at position 1 and one at the position just after the space.

This works for "First Last". Real names are harder — "Mary Ann Van Der Berg", single names, trailing suffixes — and no amount of `substr` solves that reliably. The honest engineering answer is to **store names in separate columns at the source** and treat splitting as best-effort.

A defensive version guards against a missing separator, where `instr` returns 0 and `substr(s, 1, -1)` would silently return an empty string:

```sql-run dataset=shop
SELECT full_name,
       CASE WHEN instr(full_name, ' ') > 0
            THEN substr(full_name, 1, instr(full_name, ' ') - 1)
            ELSE full_name END AS first_name,
       CASE WHEN instr(full_name, ' ') > 0
            THEN substr(full_name, instr(full_name, ' ') + 1)
            ELSE NULL END AS last_name
FROM (SELECT 'Hana Muller' AS full_name UNION ALL SELECT 'Cher' UNION ALL SELECT 'Liam Rossi');
```

### The same task in other dialects

| Task | SQLite | MySQL | PostgreSQL |
|---|---|---|---|
| Domain of an email | `substr(e, instr(e,'@')+1)` | `SUBSTRING_INDEX(e, '@', -1)` | `split_part(e, '@', 2)` |
| First word | `substr(s, 1, instr(s,' ')-1)` | `SUBSTRING_INDEX(s, ' ', 1)` | `split_part(s, ' ', 1)` |
| Pad to 8 digits | `printf('%08d', n)` | `LPAD(n, 8, '0')` | `lpad(n::text, 8, '0')` |
| Capitalise words | — (do it in the application) | — | `initcap(s)` |
| Regex replace | — (needs an extension) | `REGEXP_REPLACE(s, pat, rep)` | `regexp_replace(s, pat, rep)` |

## Worked example: numeric functions in a pricing report

Numbers deserve the same care. A pricing analyst asks for, per product: margin, margin percentage rounded to one decimal, the price rounded to the nearest \$5 for a promotional sticker, a price band, and how the price compares with its category average.

```sql-run dataset=shop
SELECT p.name,
       p.price,
       ROUND(p.price - p.cost, 2)                         AS margin,
       ROUND(100.0 * (p.price - p.cost) / p.price, 1)     AS margin_pct,
       ROUND(p.price / 5.0) * 5                           AS sticker_price,
       CAST(p.price / 100 AS INTEGER) * 100               AS band_floor,
       ROUND(p.price / a.avg_price, 2)                    AS ratio_to_category_avg,
       ROUND(p.price * p.price, 2)                        AS price_squared
FROM products p
JOIN (SELECT category_id, AVG(price) AS avg_price FROM products GROUP BY category_id) a
  ON a.category_id = p.category_id
ORDER BY margin_pct DESC
LIMIT 8;
```

Points worth noticing:

- **`100.0 *` first.** Writing the real constant at the front makes the whole expression real-valued. With integer columns, `(price - cost) / price * 100` would truncate to 0 before multiplying.
- **Rounding to a multiple:** divide, round, multiply back — `ROUND(x / 5.0) * 5`. The same idiom gives nearest 0.25, nearest 1,000 and so on.
- **Bucketing:** `CAST(x / 100 AS INTEGER) * 100` floors to the hundred below; for negative numbers use a true floor (the `CAST … - (x < CAST …)` expression, or `FLOOR()` elsewhere), since CAST truncates toward zero.
- **Powers** are written as repeated multiplication (`x * x`) in this sandbox; elsewhere use `POWER(x, 2)`. **Log transforms** (`LN(price)`), a standard feature-engineering step for skewed quantities, need MySQL/PostgreSQL or a SQLite build with math functions.

### Floating point: round at the end, compare with a tolerance

Round only for *presentation*, as the last step. Rounding intermediate values accumulates error:

```sql-run dataset=shop
SELECT ROUND(SUM(quantity * unit_price * (1 - discount)), 2)          AS sum_then_round,
       ROUND(SUM(ROUND(quantity * unit_price * (1 - discount), 2)), 2) AS round_then_sum,
       ROUND(SUM(ROUND(quantity * unit_price * (1 - discount), 0)), 2) AS round_to_units_then_sum
FROM order_items;
```

And never test floating-point values for exact equality; compare within a tolerance:

```sql-run dataset=shop
SELECT 0.1 + 0.2 = 0.3                    AS exact_equal,
       ABS((0.1 + 0.2) - 0.3) < 1e-9      AS equal_within_tolerance;
```

> [!INTERVIEW]
> Three numeric traps appear in almost every SQL screen: **integer division** (`COUNT(x) / COUNT(*)` giving 0), **division by zero** (guard with `NULLIF`), and **percentages that do not sum to 100** because each was rounded separately. Mention them unprompted when you compute a rate.

## Summary

- Strings: quote with `'`, double embedded quotes; concatenate with `||` (MySQL `CONCAT`); `length`, `instr`, `substr`, `trim`, `upper/lower`, `replace`, `printf`, `group_concat`.
- Numbers: watch integer division; `round/ceil/floor/trunc`, `abs/sign`, `mod`, `power`, logs; bucket with integer division.
- Function names differ by engine more than any other part of SQL — keep a translation table handy.

```quiz
[
  {"q": "What is 7 / 2 in SQLite or PostgreSQL?", "options": ["3.5", "3", "4", "An error"], "answer": 1, "explain": "Both operands are integers, so the division truncates. Use 7 / 2.0 or a CAST."},
  {"q": "What does 'abc' || NULL return in SQLite and PostgreSQL?", "options": ["'abc'", "'abcNULL'", "NULL", "''"], "answer": 2, "explain": "Concatenation with NULL yields NULL; use COALESCE or concat_ws."},
  {"q": "What does instr('hello', 'z') return?", "options": ["-1", "0", "NULL", "5"], "answer": 1, "explain": "instr returns 0 when the substring is not found; positions are 1-based."},
  {"q": "How do you write a string literal containing an apostrophe portably?", "options": ["'didn\\'t'", "\"didn't\"", "'didn''t'", "`didn't`"], "answer": 2, "explain": "Doubling the single quote is standard SQL."},
  {"q": "Which expression extracts the last four characters of fed_id in SQLite?", "options": ["substr(fed_id, 4)", "substr(fed_id, -4)", "right4(fed_id)", "fed_id[-4:]"], "answer": 1, "explain": "A negative start position counts from the end."},
  {"q": "The floor of -72.5 and the truncation of -72.5 (CAST AS INTEGER) are...", "options": ["-73 and -72", "-72 and -73", "-72 and -72", "-73 and -73"], "answer": 0, "explain": "floor goes toward negative infinity; trunc goes toward zero."},
  {"q": "Which is the PostgreSQL equivalent of SQLite's group_concat(x, ', ')?", "options": ["GROUP_CONCAT(x SEPARATOR ', ')", "string_agg(x, ', ')", "concat_all(x)", "array_join(x)"], "answer": 1, "explain": "string_agg is PostgreSQL's (and standard-ish LISTAGG's cousin) string aggregate."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 7 "Data Generation, Conversion, and Manipulation" (working with string data; working with numeric data). SQLite documentation, "Built-in Scalar SQL Functions" and "Built-In Mathematical SQL Functions".
