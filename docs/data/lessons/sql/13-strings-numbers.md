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
SELECT abs(-25.76)        AS abs_val,
       sign(-25.76)       AS sgn,
       power(2, 10)       AS two_to_10,
       sqrt(144)          AS root,
       mod(22, 5)         AS modulo,
       round(exp(1), 4)   AS e,
       round(ln(10), 4)   AS ln10,
       round(log10(1000), 1) AS log_1000;
```

The book lists the same families for MySQL: `ACOS/ASIN/ATAN/COS/SIN/TAN`, `EXP`, `LN`, `SQRT`, `MOD`, `POW`. (SQLite's maths functions exist only when the library is compiled with them — it is in this sandbox and in recent Python builds. `sign` requires 3.35+.)

### Controlling number precision

Four functions limit precision: `ceil` (always up), `floor` (always down), `round` (to nearest), `trunc` (toward zero).

```sql-run dataset=bank
SELECT ceil(72.445)     AS ceil_v,
       floor(72.445)    AS floor_v,
       round(72.445)    AS round_0,
       round(72.445, 1) AS round_1,
       round(72.445, 2) AS round_2,
       trunc(72.999)    AS trunc_v,
       floor(-72.5)     AS floor_neg,
       trunc(-72.5)     AS trunc_neg;
```

`round(72.445, 2)` may surprise you by returning 72.44 or 72.45 depending on the engine: 72.445 cannot be represented exactly in binary floating point. `DECIMAL` columns in MySQL/PostgreSQL round exactly (half away from zero). MySQL's `TRUNCATE(x, d)` and PostgreSQL's `trunc(x, d)` take a digits argument; MySQL and PostgreSQL's `ROUND` also accept a **negative** precision to round to tens or hundreds (`ROUND(17456, -3)` = 17000) — in SQLite compute `round(x / 1000.0) * 1000`.

### Handling signed data

The bank's `txn.amount` is always positive and `txn_type_cd` says whether it is a credit or a debit. `sign()` and `abs()` help when data is stored signed instead:

```sql-run dataset=bank
SELECT account_id, avail_balance, pending_balance,
       pending_balance - avail_balance        AS diff,
       sign(pending_balance - avail_balance)  AS direction,
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
  {"q": "floor(-72.5) and trunc(-72.5) return...", "options": ["-73 and -72", "-72 and -73", "-72 and -72", "-73 and -73"], "answer": 0, "explain": "floor goes toward negative infinity; trunc goes toward zero."},
  {"q": "Which is the PostgreSQL equivalent of SQLite's group_concat(x, ', ')?", "options": ["GROUP_CONCAT(x SEPARATOR ', ')", "string_agg(x, ', ')", "concat_all(x)", "array_join(x)"], "answer": 1, "explain": "string_agg is PostgreSQL's (and standard-ish LISTAGG's cousin) string aggregate."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 7 "Data Generation, Conversion, and Manipulation" (working with string data; working with numeric data). SQLite documentation, "Built-in Scalar SQL Functions" and "Built-In Mathematical SQL Functions".
