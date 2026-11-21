# Strings and numbers

> **Before this lesson:** you should be able to write `SELECT ... FROM ... WHERE` queries with column aliases ([SELECT and FROM](#/lesson/sql/select-from)) and know the basic data types: text, whole numbers and decimal numbers ([Data types and CREATE TABLE](#/lesson/sql/data-types-tables)). A few examples use `GROUP BY` and `CASE`, which later lessons teach; each is explained in a sentence where it appears.

## In plain words

Data rarely arrives in the form you need. A name is typed in capitals, an email has a stray space in front, a price has too many decimals, an id must be shown with leading zeros. A database can fix these on the way out, using **functions**.

A function is a named operation that takes one or more inputs and gives back one result. You write the name, then the inputs in parentheses: `upper('abc')` gives `'ABC'`. The inputs are called **arguments**. If you have used a spreadsheet, you already know the idea: `=UPPER(A1)` and `=ROUND(B2, 1)` are the same kind of thing, and SQL functions are applied to every row the way a spreadsheet formula is filled down a column.

Two kinds of data get most of this treatment. A **string** is a piece of text, a "string of characters". A **number** is a number. This lesson covers the functions for both; the next lesson covers dates and converting between types.

One warning before starting. This is the part of SQL where database products disagree most. The standard left many functions undefined, so each vendor invented its own names. The live examples use SQLite (the database running in this page), and tables throughout give the MySQL and PostgreSQL names.

**Why it matters for a job.** Cleaning text and getting arithmetic right is a large part of real data work. Interviewers like the numeric traps in particular: a percentage that comes out as 0 because of whole-number division is one of the most common mistakes in SQL tests.

## Working with text

### Writing a string

A string is written between single quotes: `'hello'`. A value typed directly into a query like this is called a **literal**. What if the text itself contains a single quote, as in *didn't*? Write the quote twice:

```sql-run dataset=bank
SELECT 'This string didn''t break' AS s, length('didn''t') AS len;
```

The first column shows the text with one apostrophe. The second uses the function `length`, which counts characters: `didn't` has six, so the doubled quote was stored as one character.

> [!WARNING]
> When values come from a program (a web form, say), never build the query by gluing the user's text into the SQL. A user who types a quote can change the meaning of your query, an attack called **SQL injection**. Programs should send the query with placeholders (`WHERE lname = ?`) and pass the values separately; these are called **bound parameters**.

Characters you cannot type can be produced from their numeric codes. Every character has a number in the Unicode standard; `char(...)` turns numbers into characters and `unicode(...)` does the reverse.

```sql-run dataset=bank
SELECT char(97, 98, 99) AS abc, char(233) AS e_acute, unicode('é') AS code, hex('abc') AS bytes;
```

Codes 97, 98 and 99 are `a`, `b` and `c`; code 233 is `é`. (MySQL: `CHAR()` and `ASCII()`; PostgreSQL: `chr()` and `ascii()`.)

**What if a string is too long for its column?** MySQL in strict mode and PostgreSQL reject 50 characters going into a `VARCHAR(30)` column. SQLite stores the whole string regardless of the declared length.

### Joining strings together

Gluing strings end to end is called **concatenation**. The standard operator is `||` (two vertical bars).

```sql-run dataset=bank
SELECT fname || ' ' || lname || ' has been a ' || title || ' since ' || start_date AS emp_narrative
FROM employee
WHERE title LIKE '%Teller'
LIMIT 5;
```

Each row becomes a sentence such as "Helen Fleming has been a Head Teller since 2022-03-17". The pieces in quotes are literals (note the spaces inside them); the others are columns.

`||` works in SQLite, PostgreSQL and Oracle. MySQL uses the function `CONCAT(a, b, ...)`; SQL Server uses `+` or `CONCAT`. One trap: if any piece is NULL (empty), the whole result of `||` is NULL. Wrap a column that may be empty in `COALESCE(x, '')`, which replaces NULL with an empty string.

### Functions that measure a string

```sql-run dataset=shop
SELECT name,
       length(name)        AS len,
       instr(name, ' ')    AS first_space,
       instr(name, 'Pro')  AS pos_of_pro
FROM products
LIMIT 6;
```

- `length(s)` returns the number of characters. "UltraBook 13" has 12. (MySQL: `CHAR_LENGTH`; its `LENGTH` counts bytes.)
- `instr(s, sub)` returns the position at which `sub` first appears inside `s`. A piece of a string is called a **substring**. The first space in "UltraBook 13" is at position 10. When the substring is not there, the answer is 0: "UltraBook 13" has no "Pro", while in "UltraBook 15 Pro" it starts at position 14. (MySQL: `LOCATE(sub, s)`; PostgreSQL: `strpos(s, sub)`.)

Positions in SQL start at **1**, not at 0 as in Python and many other programming languages.

### Functions that return a changed string

| Task | SQLite | MySQL | PostgreSQL |
|---|---|---|---|
| Upper / lower case | `upper(s)`, `lower(s)` | same | same (plus `initcap`) |
| Cut out a piece | `substr(s, start, len)` | `SUBSTRING(s, start, len)` | `substring(s from start for len)`, `substr` |
| Remove outer spaces | `trim(s)`, `ltrim`, `rtrim` | `TRIM(s)` | `trim`, `btrim` |
| Replace text | `replace(s, from, to)` | same | same |
| Find a position | `instr(s, sub)` | `LOCATE(sub, s)` | `strpos(s, sub)` |
| Pad to a width | `printf('%05d', n)` | `LPAD(s, n, pad)` | `lpad(s, n, pad)` |
| Split at a separator | `substr` with `instr` | `SUBSTRING_INDEX(s, d, n)` | `split_part(s, d, n)` |
| Join a group's values | `group_concat(x, sep)` | `GROUP_CONCAT(x SEPARATOR sep)` | `string_agg(x, sep)` |

**`substr(s, start, len)`** returns `len` characters of `s` beginning at position `start`. Leave out the length to get everything up to the end. A negative start counts from the end.

```sql-run dataset=bank
SELECT fed_id,
       substr(fed_id, 1, 3)  AS first3,
       substr(fed_id, -4)    AS last4,
       '***-**-' || substr(fed_id, -4) AS masked
FROM customer
WHERE cust_type_cd = 'I'
LIMIT 5;
```

For the id `766-16-2186`: `substr(fed_id, 1, 3)` starts at character 1 and takes three, giving `766`. `substr(fed_id, -4)` starts four characters from the end, giving `2186`. The last column hides all but the final four digits, the way a receipt hides a card number.

**Cleaning text.** The pair used most is `lower(trim(x))`: remove spaces at both ends, then convert to lower case, so that two spellings of one address compare as equal. Functions can be **nested**: the result of the inner one becomes the input of the outer one.

```sql-run dataset=shop
SELECT email AS raw,
       lower(trim(email)) AS clean,
       substr(lower(trim(email)), 1, instr(lower(trim(email)), '@') - 1) AS local_part,
       substr(lower(trim(email)), instr(lower(trim(email)), '@') + 1)    AS domain
FROM customer_imports
ORDER BY import_id
LIMIT 8;
```

The first raw email begins with a space; the `clean` column has removed it. The last two columns are a "find a position, then cut" pattern: `instr(..., '@')` finds where the `@` is; everything before it (from position 1, for `position − 1` characters) is the part in front of the `@`, and everything from `position + 1` onward is the domain.

**`replace(s, from, to)`** swaps every occurrence of one piece of text for another:

```sql-run dataset=shop
SELECT name, replace(lower(name), ' ', '-') AS url_slug
FROM products
LIMIT 6;
```

"UltraBook 15 Pro" becomes `ultrabook-15-pro`, a form fit for a web address.

**Formatting with `printf`.** `printf` builds a string from a pattern in which codes starting with `%` are replaced by values:

```sql-run dataset=bank
SELECT account_id,
       printf('%08d', account_id)        AS padded_id,
       printf('$%,.2f', avail_balance)   AS pretty_balance,
       printf('%-6s|', product_cd)       AS left_aligned
FROM account
LIMIT 5;
```

`%08d` means "a whole number, at least 8 characters wide, padded with zeros", so 101 becomes `00000101`. `%,.2f` means "a decimal number with thousands separators and two decimals", so 3820.42 becomes `3,820.42`. `%-6s` means "text, left-aligned in six characters".

**Joining the values of a group.** `group_concat` collects many rows into one string. It needs `GROUP BY`, which gathers rows sharing a value into a group ([Aggregate functions and GROUP BY](#/lesson/sql/group-by)):

```sql-run dataset=bank
SELECT cust_id, group_concat(product_cd, ', ') AS products
FROM account
GROUP BY cust_id
LIMIT 8;
```

One row per customer, listing all their products: customer 1 has `CHK, MM`.

> [!NOTE]
> The order of items inside `group_concat` is not guaranteed unless you ask for one. SQLite 3.44+: `group_concat(product_cd, ', ' ORDER BY product_cd)`. MySQL: `GROUP_CONCAT(product_cd ORDER BY product_cd SEPARATOR ', ')`. PostgreSQL: `string_agg(product_cd, ', ' ORDER BY product_cd)`.

## Working with numbers

### Arithmetic and the whole-number division trap

The usual operators work: `+`, `-`, `*`, `/`, and `%`, which gives the remainder after division (called **modulo**). The one that catches people is `/`.

```sql-run dataset=bank
SELECT 7 / 2      AS int_div,
       7 / 2.0    AS real_div,
       7 % 2      AS remainder,
       CAST(7 AS REAL) / 2 AS cast_div,
       -7 / 2     AS neg_int_div;
```

`7 / 2` gives **3**, not 3.5. A whole number is called an **integer**, and when both sides of `/` are integers, SQLite, PostgreSQL and SQL Server perform **integer division**: they drop the fractional part. Write one side as a decimal (`2.0`) or convert it with `CAST(7 AS REAL)` and you get 3.5. (`CAST` converts a value to another type; `REAL` is a number with a fractional part.) MySQL and Oracle always give a decimal from `/`.

This matters most in percentages:

```sql-run dataset=mlops
SELECT COUNT(*) AS runs,
       SUM(status = 'FAILED') AS failed,
       100 * SUM(status = 'FAILED') / COUNT(*)   AS pct_wrong,
       ROUND(100.0 * SUM(status = 'FAILED') / COUNT(*), 1) AS pct_right
FROM runs;
```

11 of 86 training runs failed. The true share is 12.8%; the version without a decimal point reports 12. Had the query divided first (`11 / 86`), the result would have been 0. The habit to form: **start a percentage with `100.0 *`.**

Two side notes. `SUM(status = 'FAILED')` counts the failed rows because SQLite and MySQL turn a true comparison into 1 and a false one into 0; PostgreSQL requires `COUNT(*) FILTER (WHERE status = 'FAILED')`. And dividing by zero gives NULL in SQLite and MySQL but an error in PostgreSQL and SQL Server; write `x / NULLIF(divisor, 0)` to be safe everywhere, since `NULLIF(a, b)` returns NULL when `a` equals `b`.

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

- `abs(x)` removes the sign: 25.76.
- `(x > 0) - (x < 0)` gives −1, 0 or 1, the **sign** of `x`. Each comparison is 1 when true and 0 when false, so for a negative number this is 0 − 1.
- `22 % 5` is 2, the remainder when 22 is divided by 5.
- `1 << 10` shifts the number 1 ten places to the left in binary, which multiplies it by 2 ten times: 1024.
- `max` and `min` with several arguments pick the largest or smallest value on one row (MySQL and PostgreSQL call these `GREATEST` and `LEAST`).
- `round(x, 4)` rounds to four decimals.

> [!NOTE]
> **Math functions and this page.** MySQL and PostgreSQL offer `CEIL`, `FLOOR`, `POWER`, `SQRT`, `EXP`, `LN`, `MOD`, `SIGN` and the trigonometric functions. Full SQLite installations have them too, but the SQLite that runs in this page was built without them, so calling them here gives *no such function*. The examples use basic operators and name the function you would use elsewhere.

| You want | MySQL / PostgreSQL | Basic SQLite equivalent |
|---|---|---|
| Remainder | `MOD(a, b)` | `a % b` |
| Cut off decimals | `TRUNCATE(x, 0)` / `trunc(x)` | `CAST(x AS INTEGER)` |
| Round down | `FLOOR(x)` | `CAST(x AS INTEGER) - (x < CAST(x AS INTEGER))` |
| Round up | `CEIL(x)` | `CAST(x AS INTEGER) + (x > CAST(x AS INTEGER))` |
| Sign | `SIGN(x)` | `(x > 0) - (x < 0)` |
| Square | `POWER(x, 2)` | `x * x` |
| Power of two | `POWER(2, n)` | `1 << n` |
| Square root, logarithm | `SQRT(x)`, `LN(x)` | not available here; calculate in the application |

### Controlling precision: four ways to drop decimals

- **Ceiling**: up to the next whole number.
- **Floor**: down to the previous whole number.
- **Round**: to the nearest.
- **Truncate**: cut the decimals off.

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

For 72.445 the ceiling is 73 and the floor 72. `CAST(72.999 AS INTEGER)` is 72: converting to an integer truncates, however close the value is to 73. The last two columns show where floor and truncate differ. For −72.5, floor goes *down* to −73, while truncation cuts toward zero and gives −72.

`round(72.445, 2)` returns 72.44 here, not the 72.45 you might expect. Computers store most decimal numbers in a binary format called **floating point**, which cannot hold 72.445 exactly; the stored value is a hair below it. Columns declared `DECIMAL` in MySQL and PostgreSQL store exact decimals and round as people expect, which is why money belongs in `DECIMAL`.

### Signed values

When a positive and a negative direction are stored in one column, `abs` and the sign expression pull them apart. Here they compare two balances:

```sql-run dataset=bank
SELECT account_id, avail_balance, pending_balance,
       pending_balance - avail_balance        AS diff,
       (pending_balance > avail_balance) - (pending_balance < avail_balance) AS direction,
       abs(pending_balance - avail_balance)   AS magnitude
FROM account
WHERE pending_balance <> avail_balance
LIMIT 6;
```

`direction` is 1 when the pending balance is higher and −1 when it is lower; `magnitude` is the size of the gap. The first row shows `105.57999999999993` where you expect 105.58: floating point again. Round for display.

### Sorting numbers into buckets

Reports often group a continuous measurement into ranges, called **buckets** or bins. Integer division does it in one expression:

```sql-run dataset=mlops
SELECT (latency_ms / 50) * 50 AS bucket_start,
       COUNT(*) AS predictions,
       printf('%.*c', COUNT(*) / 4, '#') AS histogram
FROM predictions
GROUP BY bucket_start
ORDER BY bucket_start;
```

`latency_ms` is how long a prediction took, in milliseconds. Dividing by 50 with integer division and multiplying back by 50 turns 0–49 into 0, 50–99 into 50, and so on. The last column uses `printf` to repeat `#` once per four predictions, drawing a bar chart in text.

### Random numbers

`random()` returns a random whole number in SQLite (MySQL's `RAND()` and PostgreSQL's `random()` return a decimal between 0 and 1). Sorting by it shuffles the rows:

```sql-run dataset=shop
SELECT customer_id, first_name, country
FROM customers
ORDER BY random()
LIMIT 5;
```

Run it twice and different customers appear. This sorts the whole table, which is fine for small data. Large systems sample with an expression on the id, such as `WHERE customer_id % 100 < 10`, which is also *repeatable*: the same rows are chosen every time, which matters when a machine-learning experiment must be reproduced.

## Worked example: cleaning a messy text column

The `customer_imports` table holds names and emails typed by hand. Suppose another system wants, for every row: a clean email, its user name and domain, first and last name in separate columns, initials, and a display name in the form "LAST, First".

The cleaning step is done once, in a `WITH` clause, which gives a query result a name (here `clean`) so the main query can use it like a table ([Common table expressions](#/lesson/sql/ctes)). That avoids repeating `lower(trim(...))` in every expression.

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

Read each expression as "find a position, then cut". The email splits at the `@`; the name splits at the first space; the initials are the character at position 1 and the character right after the space. The first row gives `hana.muller`, `example.com`, `Hana`, `Muller`, `HM` and `MULLER, Hana`.

This works for "First Last". Real names are harder (several given names, a single name, a suffix) and no arrangement of `substr` handles them all. The sound engineering answer is to **store first and last names in separate columns from the start** and treat splitting as a best effort.

A careful version handles a name with no space. There `instr` returns 0, and `substr(s, 1, -1)` would quietly return an empty string. `CASE WHEN ... THEN ... ELSE ... END` is SQL's "if ... then ... else" ([The CASE expression](#/lesson/sql/case-expressions)):

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

"Cher" keeps the whole name as first name and gets an empty last name instead of a wrong one.

### The same tasks in other databases

| Task | SQLite | MySQL | PostgreSQL |
|---|---|---|---|
| Domain of an email | `substr(e, instr(e,'@')+1)` | `SUBSTRING_INDEX(e, '@', -1)` | `split_part(e, '@', 2)` |
| First word | `substr(s, 1, instr(s,' ')-1)` | `SUBSTRING_INDEX(s, ' ', 1)` | `split_part(s, ' ', 1)` |
| Pad to 8 digits | `printf('%08d', n)` | `LPAD(n, 8, '0')` | `lpad(n::text, 8, '0')` |
| Capitalise words | not built in | not built in | `initcap(s)` |
| Replace by pattern | needs an extension | `REGEXP_REPLACE(s, pat, rep)` | `regexp_replace(s, pat, rep)` |

## Worked example: numbers in a pricing report

A pricing analyst asks, for each product: the margin (price minus cost), the margin as a percentage, the price rounded to the nearest 5 for a shelf sticker, a price band, and the price compared with the average of its category.

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

The Smart Watch costs 199.00 with a margin of 108.80, which is 54.7% of the price. Points to notice:

- **`100.0 *` comes first**, so the whole calculation is done in decimals.
- **Rounding to a multiple**: divide, round, multiply back. `ROUND(199.0 / 5.0) * 5` is 200. The same pattern rounds to the nearest 0.25 or the nearest 1,000.
- **Banding**: `CAST(x / 100 AS INTEGER) * 100` gives the hundred below, so 199 falls in band 100.
- **The category average** comes from a subquery joined in as a table, the derived-table technique from [Three or more tables, self joins and non-equi joins](#/lesson/sql/multi-self-joins).
- **Powers** are written as repeated multiplication here; elsewhere use `POWER(x, 2)`.

### Floating point: round last, compare with a tolerance

Round for *display*, as the final step. Rounding in the middle of a calculation piles up small errors:

```sql-run dataset=shop
SELECT ROUND(SUM(quantity * unit_price * (1 - discount)), 2)          AS sum_then_round,
       ROUND(SUM(ROUND(quantity * unit_price * (1 - discount), 2)), 2) AS round_then_sum,
       ROUND(SUM(ROUND(quantity * unit_price * (1 - discount), 0)), 2) AS round_to_units_then_sum
FROM order_items;
```

Summing first gives 184225.88. Rounding each line to cents first gives 184225.85, three cents off. Rounding each line to whole units is 88 cents off.

And never test floating-point values for exact equality:

```sql-run dataset=shop
SELECT 0.1 + 0.2 = 0.3                    AS exact_equal,
       ABS((0.1 + 0.2) - 0.3) < 1e-9      AS equal_within_tolerance;
```

`0.1 + 0.2 = 0.3` is 0, meaning false: in floating point the sum is 0.30000000000000004. The second test asks whether the two values differ by less than a billionth (`1e-9`), and that is true. An allowed difference like this is called a **tolerance**.

> [!INTERVIEW]
> Three numeric traps appear in almost every SQL test: **integer division** (`COUNT(x) / COUNT(*)` giving 0), **division by zero** (guard with `NULLIF`), and **percentages that do not add up to 100** because each was rounded separately. Mention them without being asked whenever you calculate a rate.

## Pitfalls

- **Integer division.** `1 / 2` is 0 in SQLite, PostgreSQL and SQL Server.
- **Positions start at 1**, and `instr` returns 0 (not −1, not NULL) when nothing is found.
- **`||` with NULL** makes the whole string NULL.
- **A function around a column in `WHERE`** (`WHERE lower(email) = ...`) stops the database from using an ordinary index on that column, so the search reads every row. Store the cleaned value, or index the expression ([Indexes and query plans](#/lesson/sql/indexes)).
- **Different names on different databases.** Check a translation table before moving a query.
- **Gluing user input into SQL.** Use bound parameters.

## Summary

- Strings: quote with `'` and double any quote inside; join with `||` (MySQL: `CONCAT`); measure with `length` and `instr`; change with `substr`, `trim`, `upper`, `lower`, `replace`, `printf`; collect a group with `group_concat`.
- Numbers: watch integer division; know ceiling, floor, round and truncate; use `abs` and the sign expression; make buckets with integer division.
- Floating point is approximate: round at the end and compare with a tolerance.
- Function names vary between databases more than any other part of SQL.

## Glossary

- **Function** — a named operation that takes inputs and returns one value, written `name(inputs)`.
- **Argument** — an input given to a function.
- **String** — a piece of text.
- **Literal** — a value typed directly into a query, such as `'abc'` or `42`.
- **Concatenation** — joining strings end to end.
- **Substring** — a piece cut from inside a string.
- **Nested functions** — functions placed inside one another, the inner result feeding the outer.
- **SQL injection** — an attack in which user-typed text changes the meaning of a query.
- **Bound parameter** — a placeholder in a query whose value is supplied separately and safely.
- **Integer** — a whole number.
- **Integer division** — division of two integers that drops the fractional part.
- **Modulo** — the remainder left after division.
- **Ceiling / floor** — rounding up / down to a whole number.
- **Truncate** — cutting off the decimals, which moves a number toward zero.
- **Floating point** — the approximate binary format in which computers store most decimal numbers.
- **Bucket (bin)** — a range into which values are grouped.
- **Tolerance** — the small difference allowed when comparing approximate numbers.

```quiz
[
  {"q": "What is 7 / 2 in SQLite or PostgreSQL?", "options": ["3.5", "3", "4", "An error"], "answer": 1, "explain": "Both sides are integers, so the fractional part is dropped. Write 7 / 2.0 or use CAST to get 3.5."},
  {"q": "What does 'abc' || NULL return in SQLite and PostgreSQL?", "options": ["'abc'", "'abcNULL'", "NULL", "''"], "answer": 2, "explain": "Concatenation with NULL gives NULL; wrap the nullable part in COALESCE(x, '')."},
  {"q": "What does instr('hello', 'z') return?", "options": ["-1", "0", "NULL", "5"], "answer": 1, "explain": "instr returns 0 when the substring is not found; real positions start at 1."},
  {"q": "How do you write a string literal containing an apostrophe so that it works on every database?", "options": ["`'didn\\'t'`", "`\"didn't\"`", "`'didn''t'`", "`` `didn't` ``"], "answer": 2, "explain": "Doubling the single quote is the standard form."},
  {"q": "Which expression extracts the last four characters of fed_id in SQLite?", "options": ["substr(fed_id, 4)", "substr(fed_id, -4)", "right4(fed_id)", "fed_id[-4:]"], "answer": 1, "explain": "A negative start position counts from the end of the string."},
  {"q": "The floor of -72.5 and the truncation of -72.5 (CAST AS INTEGER) are...", "options": ["-73 and -72", "-72 and -73", "-72 and -72", "-73 and -73"], "answer": 0, "explain": "Floor goes down, toward negative infinity; truncation cuts toward zero."},
  {"q": "Which is the PostgreSQL equivalent of SQLite's group_concat(x, ', ')?", "options": ["GROUP_CONCAT(x SEPARATOR ', ')", "string_agg(x, ', ')", "concat_all(x)", "array_join(x)"], "answer": 1, "explain": "string_agg is PostgreSQL's function for joining a group's values; GROUP_CONCAT with SEPARATOR is MySQL's."},
  {"q": "Why does SELECT 0.1 + 0.2 = 0.3 return 0 (false)?", "options": ["SQLite cannot add decimals", "Floating-point numbers are stored approximately, so the sum is not exactly 0.3", "The = operator only works on integers", "0.3 is treated as text"], "answer": 1, "explain": "The sum is 0.30000000000000004 in binary floating point; compare within a tolerance instead."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 7 "Data Generation, Conversion, and Manipulation" (working with string data; working with numeric data), restated in original wording. SQLite documentation, "Built-in Scalar SQL Functions" and "Built-In Mathematical SQL Functions".
