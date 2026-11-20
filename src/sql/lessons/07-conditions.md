# Building conditions

Most queries are not interested in every row. The `WHERE` clause (and later `HAVING` and join `ON` clauses) uses **conditions** to decide which rows survive. This lesson covers how conditions are evaluated and combined with `AND`, `OR` and `NOT`, then works through the four condition types the book identifies: equality, range, membership and matching. The next lesson tackles the special case of NULL.

## How conditions are evaluated

A WHERE clause contains one or more conditions joined by `AND` and `OR`. For each row the server evaluates the whole expression and keeps the row only if the result is **TRUE**.

- With only `AND`s, every condition must be true.
- With only `OR`s, at least one must be true.

```sql-run dataset=bank
SELECT emp_id, fname, lname, title, start_date
FROM employee
WHERE title = 'Teller' AND start_date < '2021-01-01';
```

```sql-run dataset=bank
SELECT emp_id, fname, lname, title, start_date
FROM employee
WHERE title = 'Teller' OR start_date < '2020-01-01';
```

The second query returns tellers *plus* anyone hired before 2020, whatever their title.

### Using parentheses

When you mix AND and OR, **AND binds tighter** — just as multiplication binds tighter than addition. `a OR b AND c` means `a OR (b AND c)`. The book's advice: always use parentheses when mixing them, so that neither the server nor the next reader has to guess.

```sql-run dataset=bank
-- Tellers or head tellers who started before 2021
SELECT emp_id, fname, title, start_date
FROM employee
WHERE (title = 'Teller' OR title = 'Head Teller')
  AND start_date < '2021-01-01';
```

Remove the parentheses and you get every Teller (any start date) plus Head Tellers who started before 2021 — a different, wrong answer that runs without error.

### Using NOT

`NOT` inverts a condition:

```sql-run dataset=bank
SELECT emp_id, fname, title
FROM employee
WHERE NOT (title = 'Teller' OR title = 'Head Teller');
```

Expressions with several NOTs are hard to read; De Morgan's laws let you push NOT inward: `NOT (a OR b)` is `NOT a AND NOT b`. Most people find `title <> 'Teller' AND title <> 'Head Teller'` (or `title NOT IN (...)`) clearer.

### What a condition is made of

A condition is one or more **expressions** combined with **operators**. Expressions can be numbers, columns, string literals, built-in functions, subqueries, or lists of expressions. Operators include comparison (`=`, `<>`/`!=`, `<`, `>`, `<=`, `>=`, `LIKE`, `IN`, `BETWEEN`) and arithmetic (`+ - * /`).

## Equality conditions

`column = expression` is the most common condition. Its inverse is inequality, written `<>` (standard) or `!=` (accepted everywhere).

```sql-run dataset=bank
SELECT p.name AS product, pt.name AS product_type
FROM product p
JOIN product_type pt ON p.product_type_cd = pt.product_type_cd
WHERE pt.name <> 'Customer Accounts';
```

Equality also powers data modification — `DELETE FROM account WHERE status = 'CLOSED' AND close_date < '2022-01-01'` removes old closed accounts.

## Range conditions

Range conditions check whether an expression falls within a range, using `<`, `<=`, `>`, `>=`:

```sql-run dataset=bank
SELECT emp_id, fname, lname, start_date
FROM employee
WHERE start_date >= '2020-01-01' AND start_date < '2021-01-01';
```

This **half-open** form — inclusive lower bound, exclusive upper bound — is the safest way to express a period, because it works for dates *and* timestamps. Compare with the inclusive version on a timestamp column:

```sql-run dataset=bank
SELECT COUNT(*) AS inclusive_end, 
       (SELECT COUNT(*) FROM txn WHERE txn_date >= '2024-03-01' AND txn_date < '2024-04-01') AS half_open
FROM txn
WHERE txn_date >= '2024-03-01' AND txn_date <= '2024-03-31';
```

The inclusive version misses every transaction made *during* March 31, because `'2024-03-31 10:15:00'` is greater than `'2024-03-31'`.

### BETWEEN

`BETWEEN low AND high` is shorthand for `>= low AND <= high` — inclusive on both ends:

```sql-run dataset=bank
SELECT account_id, product_cd, avail_balance
FROM account
WHERE avail_balance BETWEEN 3000 AND 5000
ORDER BY avail_balance;
```

Always put the **lower bound first**. `BETWEEN 5000 AND 3000` is not an error; it simply means `>= 5000 AND <= 3000`, which matches nothing.

### String ranges

Ranges work on text too, using the collation's order. The book finds customers whose fed IDs fall within a range of social-security-style numbers:

```sql-run dataset=bank
SELECT cust_id, fed_id
FROM customer
WHERE cust_type_cd = 'I'
  AND fed_id BETWEEN '500-00-0000' AND '999-99-9999';
```

Text ranges are a sharp tool: `'10' < '9'` is true for text, so never use them on numbers stored as text.

## Membership conditions

Testing against a finite set of values with chained ORs is verbose:

```sql
WHERE product_cd = 'CHK' OR product_cd = 'SAV' OR product_cd = 'CD' OR product_cd = 'MM'
```

`IN` says the same thing:

```sql-run dataset=bank
SELECT account_id, product_cd, cust_id, avail_balance
FROM account
WHERE product_cd IN ('CHK', 'SAV', 'CD', 'MM')
  AND avail_balance > 15000;
```

The list can also come from a subquery, which saves you from hard-coding:

```sql-run dataset=bank
SELECT account_id, product_cd, avail_balance
FROM account
WHERE product_cd IN (SELECT product_cd FROM product WHERE product_type_cd = 'LOAN');
```

`NOT IN` excludes a set. It has one dangerous trap with NULLs, covered in the next lesson.

## Matching conditions

Sometimes you need partial string matches: every employee whose last name begins with T, every email at a certain domain.

### String functions

You can match with functions — `substr(lname, 1, 1) = 'T'` — but the book recommends wildcards.

### Wildcards with LIKE

| Wildcard | Matches |
|---|---|
| `_` | exactly one character |
| `%` | any number of characters, including zero |

```sql-run dataset=bank
SELECT lname FROM employee WHERE lname LIKE '_a%e%';   -- 'a' in 2nd position, an 'e' somewhere after
```

Common patterns:

| Pattern | Meaning |
|---|---|
| `'F%'` | starts with F |
| `'%t'` | ends with t |
| `'%bas%'` | contains "bas" |
| `'___-__-____'` | exactly 11 characters with dashes in positions 4 and 7 (an SSN shape) |

```sql-run dataset=bank
SELECT cust_id, fed_id
FROM customer
WHERE fed_id LIKE '___-__-____';
```

To match a literal `%` or `_`, declare an escape character: `LIKE '50\%%' ESCAPE '\'`.

> [!NOTE]
> **Case sensitivity varies.** SQLite's LIKE is case-insensitive for ASCII letters by default; MySQL's depends on the collation (usually insensitive); PostgreSQL's LIKE is case-sensitive and offers `ILIKE` for insensitive matching. For portable case-insensitive matching write `lower(col) LIKE 'abc%'`.

### Regular expressions

When wildcards are not enough, most engines support regular expressions: MySQL `col REGEXP '^[FG]'`, PostgreSQL `col ~ '^[FG]'`, Oracle `REGEXP_LIKE(col, '^[FG]')`. SQLite has the `REGEXP` operator syntax but ships no implementation — the host application must register one (Python's `sqlite3` can, via `create_function`). Another SQLite option is `GLOB`, which uses Unix shell wildcards (`*`, `?`, `[A-F]`) and is case-sensitive:

```sql-run dataset=bank
SELECT lname FROM employee WHERE lname GLOB '[FG]*';
```

### Performance note

A pattern with a fixed prefix (`LIKE 'Sm%'`) can, under the right collation, use an index on the column — it is effectively a range `>= 'Sm' AND < 'Sn'`. A pattern starting with a wildcard (`'%son'`) cannot; the engine must examine every row. For "contains" search over large text, use full-text indexes (SQLite FTS5, PostgreSQL `tsvector`, MySQL FULLTEXT).

## Putting it together

A realistic filter from the `mlops` world: finished deep-learning runs (BERT variants or vision models) trained in March 2024 with a small learning rate.

```sql-run dataset=mlops
SELECT run_id, run_name, model_type, learning_rate, started_at
FROM runs
WHERE status = 'FINISHED'
  AND (model_type LIKE '%bert%' OR model_type IN ('resnet50', 'efficientnet-b0'))
  AND started_at >= '2024-03-01' AND started_at < '2024-04-01'
  AND learning_rate <= 0.001
ORDER BY started_at;
```

Read it clause by clause: an equality, a parenthesised OR of a match and a membership test, a half-open range, and a comparison.

## Pitfalls

- **Mixing AND/OR without parentheses.**
- **Inclusive end dates on timestamp columns.**
- **`BETWEEN high AND low`** silently returns nothing.
- **Leading wildcards** on large tables are full scans.
- **Text comparisons on numeric data** (`'10' < '9'`).
- **Assuming LIKE's case behaviour** is the same everywhere.

## Worked example: translating a requirement into a WHERE clause

Requirements arrive in English, with all its ambiguity. Practise turning one into precise conditions. The request: *"Find active deposit accounts — checking, savings or money market — opened at the Woburn or Quincy branch before 2023, with at least \$2,000 available, excluding accounts opened by head tellers."*

Break it into atomic conditions, classify each, and decide how they combine:

| English | Condition | Type |
|---|---|---|
| active | `status = 'ACTIVE'` | equality |
| checking, savings or money market | `product_cd IN ('CHK', 'SAV', 'MM')` | membership |
| Woburn or Quincy branch | `open_branch_id IN (2, 3)` | membership |
| opened before 2023 | `open_date < '2023-01-01'` | range |
| at least 2,000 available | `avail_balance >= 2000` | range |
| not opened by a head teller | `open_emp_id NOT IN (…head tellers…)` | membership (negated, subquery) |

All six must hold, so they are joined by AND — the ORs are hidden inside the IN lists, which is exactly why IN is safer than writing the ORs yourself.

```sql-run dataset=bank
SELECT account_id, product_cd, open_branch_id, open_date, open_emp_id, avail_balance
FROM account
WHERE status = 'ACTIVE'
  AND product_cd IN ('CHK', 'SAV', 'MM')
  AND open_branch_id IN (2, 3)
  AND open_date < '2023-01-01'
  AND avail_balance >= 2000
  AND open_emp_id NOT IN (SELECT emp_id FROM employee WHERE title = 'Head Teller')
ORDER BY avail_balance DESC;
```

Check the boundary words. "Before 2023" is `< '2023-01-01'` (strict). "At least 2,000" is `>=` (inclusive). "Between 1 and 5" in everyday English is usually inclusive — the same as SQL's BETWEEN — but "between January and March" might or might not include March 31st at 3 pm; ask, or use an explicit half-open range and state your assumption.

### A debugging technique: count as you add

When a filter returns fewer rows than expected, do not stare at it — measure it. Add the conditions one at a time and watch the count fall:

```sql-run dataset=bank
SELECT COUNT(*) AS all_accounts,
       SUM(status = 'ACTIVE') AS active,
       SUM(status = 'ACTIVE' AND product_cd IN ('CHK','SAV','MM')) AS and_deposit,
       SUM(status = 'ACTIVE' AND product_cd IN ('CHK','SAV','MM') AND open_branch_id IN (2,3)) AS and_branch,
       SUM(status = 'ACTIVE' AND product_cd IN ('CHK','SAV','MM') AND open_branch_id IN (2,3)
           AND open_date < '2023-01-01') AS and_date,
       SUM(status = 'ACTIVE' AND product_cd IN ('CHK','SAV','MM') AND open_branch_id IN (2,3)
           AND open_date < '2023-01-01' AND avail_balance >= 2000) AS and_balance
FROM account;
```

The condition where the number drops unexpectedly is the one to inspect. (This relies on SQLite/MySQL treating a boolean as 1/0; elsewhere wrap each in `CASE WHEN … THEN 1 ELSE 0 END`.)

## Precedence and De Morgan, with data

The operator precedence in a WHERE clause, highest first: comparison operators (`=`, `<`, `LIKE`, `IN`, `BETWEEN`, `IS NULL`) → `NOT` → `AND` → `OR`. Three versions of a filter show how much the parentheses matter:

```sql-run dataset=shop
SELECT
  SUM(country = 'Canada' OR country = 'Japan' AND city = 'Tokyo')    AS no_parens,
  SUM((country = 'Canada' OR country = 'Japan') AND city = 'Tokyo')  AS or_grouped,
  SUM(country = 'Canada' OR (country = 'Japan' AND city = 'Tokyo'))  AS and_grouped
FROM customers;
```

`no_parens` equals `and_grouped`: every Canadian customer plus Tokyo customers. `or_grouped` is a different (and here much smaller) set — customers in Canada or Japan whose city is Tokyo.

Negating a compound condition follows **De Morgan's laws**:

- `NOT (a AND b)` ≡ `NOT a OR NOT b`
- `NOT (a OR b)` ≡ `NOT a AND NOT b`

So "not (cancelled or returned)" is "not cancelled **and** not returned":

```sql-run dataset=shop
SELECT SUM(NOT (status = 'cancelled' OR status = 'returned'))   AS negated_group,
       SUM(status <> 'cancelled' AND status <> 'returned')      AS de_morgan,
       SUM(status NOT IN ('cancelled', 'returned'))             AS not_in,
       SUM(status <> 'cancelled' OR status <> 'returned')       AS common_mistake
FROM orders;
```

The first three agree. The last — written with OR — is true for *every* row, since no status equals both values at once. It is one of the most frequent logic bugs in hand-written filters.

## LIKE in practice

A few more patterns worth having at your fingertips, and what each really matches:

```sql-run dataset=shop
SELECT name,
       name LIKE 'The %'      AS starts_with_the,
       name LIKE '% % %'      AS three_or_more_words,
       name LIKE '%book%'     AS contains_book,
       name LIKE '____'       AS exactly_four_chars,
       name LIKE '%-%'        AS has_hyphen
FROM products
WHERE product_id IN (3, 8, 10, 15, 23, 26, 30);
```

Notice `'%book%'` matches *Chromebook Go* — LIKE has no notion of word boundaries. For "the word book", you would need `' ' || name || ' ' LIKE '% book %'` or a regular expression / full-text search.

Searching for the wildcard characters themselves requires an escape:

```sql-run dataset=shop
SELECT '25% off' LIKE '%\%%' ESCAPE '\'  AS contains_percent,
       'file_name' LIKE '%\_%' ESCAPE '\' AS contains_underscore,
       'filename' LIKE '%\_%' ESCAPE '\'  AS no_underscore;
```

Case behaviour in SQLite, concretely — LIKE ignores ASCII case, `=` and GLOB do not:

```sql-run dataset=shop
SELECT 'Tokyo' LIKE 'tokyo' AS like_ci,
       'Tokyo' = 'tokyo'    AS equals_cs,
       'Tokyo' GLOB 't*'    AS glob_cs,
       'Tokyo' = 'tokyo' COLLATE NOCASE AS equals_nocase;
```

> [!INTERVIEW]
> Filtering questions often hide a trap in the wording: "customers **not** in the USA" (what about NULL country?), "orders in March" (timestamps on the 31st?), "names starting with A" (case?). State your interpretation, then write the condition — interviewers value the clarification as much as the query.

## Summary

- Rows are kept when the WHERE expression is TRUE; AND binds tighter than OR, so parenthesise mixtures.
- Condition types: **equality** (`=`, `<>`), **range** (`<`, `>=`, `BETWEEN`), **membership** (`IN`, `NOT IN`, lists or subqueries), **matching** (`LIKE` with `_` and `%`, regular expressions, SQLite `GLOB`).
- Use half-open ranges for periods.
- Prefix patterns can use indexes; leading-wildcard patterns cannot.

```quiz
[
  {"q": "How is a OR b AND c evaluated?", "options": ["(a OR b) AND c", "a OR (b AND c)", "Left to right", "It is a syntax error"], "answer": 1, "explain": "AND has higher precedence than OR; use parentheses to be explicit."},
  {"q": "Which condition includes every transaction on 31 March 2024 when txn_date holds timestamps?", "options": ["txn_date <= '2024-03-31'", "txn_date < '2024-04-01'", "txn_date BETWEEN '2024-03-01' AND '2024-03-31'", "txn_date = '2024-03-31'"], "answer": 1, "explain": "A half-open upper bound on the next day captures all times on the 31st."},
  {"q": "What does LIKE '_a%' match?", "options": ["Strings starting with 'a'", "Strings whose second character is 'a'", "Strings containing 'a'", "Exactly two characters"], "answer": 1, "explain": "_ is exactly one character, so 'a' must be in position 2."},
  {"q": "What does BETWEEN 100 AND 50 return?", "options": ["Values from 50 to 100", "An error", "No rows", "Values outside the range"], "answer": 2, "explain": "It means >= 100 AND <= 50, which nothing satisfies."},
  {"q": "Which pattern can generally use a B-tree index on lname?", "options": ["LIKE '%son'", "LIKE '%mit%'", "LIKE 'Smi%'", "None of them"], "answer": 2, "explain": "A fixed prefix turns into a range scan; leading wildcards force a full scan."},
  {"q": "In PostgreSQL, how do you do a case-insensitive LIKE?", "options": ["LIKE is already insensitive", "ILIKE", "LIKE ... NOCASE", "REGEXP"], "answer": 1, "explain": "ILIKE is PostgreSQL's case-insensitive LIKE; lower(col) LIKE ... is portable."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 4 "Filtering" (condition evaluation, parentheses, NOT, building a condition, equality, range, membership and matching conditions).
