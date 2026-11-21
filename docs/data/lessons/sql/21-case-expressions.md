# The CASE expression

> **Before this lesson:** you should be able to write conditions with comparisons, `AND`, `OR`, `IN` and `IS NULL` ([Building conditions](#/lesson/sql/conditions), [NULL: the four-letter word](#/lesson/sql/null-logic)), use aggregates with `GROUP BY` ([Aggregate functions and GROUP BY](#/lesson/sql/group-by)) and read a `LEFT JOIN` ([Outer joins](#/lesson/sql/outer-joins)).

## In plain words

So far every column in a result was either copied from a table or calculated the same way for every row. Often the calculation should *depend on the row*: show a person's name for one kind of customer and a company's name for another; call a balance "low" or "high"; count a deposit as plus and a withdrawal as minus. Choosing between alternatives according to a test is called **conditional logic**, and in SQL it is written with the `CASE` expression.

`CASE` is SQL's "if ... then ... otherwise". An everyday picture: the sorting rule at a post office. *If* the parcel weighs under one kilo, it goes in the small bin; *otherwise, if* it weighs under ten kilos, the medium bin; *otherwise* the large bin. The clerk checks the rules from the top and stops at the first one that fits. `CASE` works in exactly that way, once for each row.

If you have used a spreadsheet, `CASE` does the job of the `IF` function.

**Why it matters for a job.** Business rules ("customers with over 10,000 are Premier") reach the data through `CASE`. It is part of the SQL standard and is written the same way on every major database. In interviews it often arrives in disguise: "put customers into tiers", "count the passes and the fails in separate columns", "swap two values in one statement". This lesson covers the two forms of `CASE` and their rules; the next applies them to the classic patterns.

## A first example: one name column from two tables

The bank has two kinds of customer. A person's name is stored in the `individual` table and a company's name in `business`. With two left joins both can be fetched, each in its own column:

```sql-run dataset=bank
SELECT c.cust_id, c.fed_id, c.cust_type_cd,
       i.fname || ' ' || i.lname AS indiv_name,
       b.name AS business_name
FROM customer c
LEFT JOIN individual i ON c.cust_id = i.cust_id
LEFT JOIN business b   ON c.cust_id = b.cust_id
WHERE c.cust_id BETWEEN 28 AND 33;
```

Customers 28 to 30 are people (type `I`): they have an `indiv_name` and NULL as `business_name`. Customers 31 to 33 are companies (type `B`) and it is the other way round. Whoever reads the result has to look in two places. `CASE` lets the query choose:

```sql-run dataset=bank
SELECT c.cust_id, c.fed_id,
       CASE
         WHEN c.cust_type_cd = 'I' THEN i.fname || ' ' || i.lname
         WHEN c.cust_type_cd = 'B' THEN b.name
         ELSE 'Unknown'
       END AS name
FROM customer c
LEFT JOIN individual i ON c.cust_id = i.cust_id
LEFT JOIN business b   ON c.cust_id = b.cust_id
WHERE c.cust_id BETWEEN 28 AND 33;
```

Read the `CASE` part word by word:

- `CASE` opens the expression.
- `WHEN c.cust_type_cd = 'I' THEN i.fname || ' ' || i.lname` — if this customer is a person, the result is the first and last name joined with a space.
- `WHEN c.cust_type_cd = 'B' THEN b.name` — otherwise, if the customer is a company, the result is the company name.
- `ELSE 'Unknown'` — if neither test was true, the result is the text `Unknown`.
- `END` closes the expression, and `AS name` names the resulting column.

One `name` column, filled from the right source on each row.

> [!NOTE]
> Several databases have their own shortcuts: `DECODE` in Oracle, `IF()` in MySQL, `IIF` in SQL Server, `iif()` in SQLite. `iif(test, a, b)` is short for `CASE WHEN test THEN a ELSE b END`. Prefer `CASE`: it is standard, works everywhere and reads clearly.

## The searched CASE

The form above is called the **searched** `CASE`. Each `WHEN` carries a complete condition of its own:

```
CASE
  WHEN condition_1 THEN result_1
  WHEN condition_2 THEN result_2
  ...
  [ELSE default_result]
END
```

The rules:

1. The conditions are checked **in order, from top to bottom**.
2. At the first condition that is true, its result is returned and **the remaining `WHEN` lines are not looked at**.
3. If none is true, the `ELSE` result is returned. If there is no `ELSE`, the result is **NULL**.
4. All the results should be of the **same type** (all text, or all numbers). PostgreSQL insists; SQLite lets you mix and leaves you with the consequences.

A condition can be anything you could write in `WHERE`: comparisons, `AND` and `OR`, `IN`, `LIKE`, `IS NULL`, even a subquery.

Because the first true line wins, order matters when conditions overlap. That allows compact thresholds:

```sql-run dataset=shop
SELECT name, price,
       CASE
         WHEN price >= 1000 THEN 'premium'
         WHEN price >= 100  THEN 'mid-range'     -- reached only if price < 1000
         WHEN price >= 20   THEN 'budget'
         ELSE 'impulse'
       END AS tier
FROM products
ORDER BY price DESC
LIMIT 10;
```

A product priced 1799.00 passes the first test and is labelled `premium`; the other lines are never checked for it. A product at 349.00 fails the first test and passes the second: `mid-range`. The second line does not need to say "and below 1000", because any row that reaches it has already failed `price >= 1000`.

Put `price >= 20` first, and nearly every product would be labelled "budget", since almost every price is at least 20. When a `CASE` gives unexpected labels, check the order of its lines before anything else.

### What a missing ELSE does

Without `ELSE`, a row that matches no line gets NULL. Sometimes that is a mistake. Sometimes it is exactly what you want, because aggregate functions ignore NULLs:

```sql-run dataset=bank
SELECT COUNT(*) AS accounts,
       COUNT(CASE WHEN status = 'ACTIVE' THEN 1 END) AS active,
       COUNT(CASE WHEN status = 'FROZEN' THEN 1 END) AS frozen,
       ROUND(AVG(CASE WHEN product_cd = 'CHK' THEN avail_balance END), 2) AS avg_checking
FROM account;
```

Take the second column. For an active account the `CASE` gives 1; for any other it gives NULL (no `ELSE`). `COUNT` counts only values that are not NULL, so it counts the active accounts: 70 of 84. The same trick counts the 5 frozen ones.

The last column averages checking balances only: rows of other products give NULL and are skipped, leaving 5645.34. Had the `CASE` said `ELSE 0`, every non-checking account would have entered the average as a zero and dragged it down. That is a subtle and common mistake.

### A subquery inside a CASE

A result can be a subquery that returns one value. The name query again, this time without joins; the name is fetched by a correlated subquery ([Correlated subqueries, EXISTS and subqueries as data sources](#/lesson/sql/correlated-exists)) chosen by customer type:

```sql-run dataset=bank
SELECT c.cust_id, c.fed_id,
       CASE
         WHEN c.cust_type_cd = 'I' THEN
           (SELECT i.fname || ' ' || i.lname FROM individual i WHERE i.cust_id = c.cust_id)
         WHEN c.cust_type_cd = 'B' THEN
           (SELECT b.name FROM business b WHERE b.cust_id = c.cust_id)
         ELSE 'Unknown'
       END AS name
FROM customer c
WHERE c.cust_id BETWEEN 28 AND 33;
```

For each row only the subquery of the line that matched is run, so only the relevant table is read.

## The simple CASE

The **simple** `CASE` names one expression after the word `CASE` and compares it with a list of values:

```
CASE expression
  WHEN value_1 THEN result_1
  WHEN value_2 THEN result_2
  ...
  [ELSE default_result]
END
```

```sql-run dataset=bank
SELECT c.cust_id,
       CASE c.cust_type_cd
         WHEN 'I' THEN 'Individual'
         WHEN 'B' THEN 'Business'
         ELSE 'Unknown Customer Type'
       END AS customer_type
FROM customer c
WHERE c.cust_id BETWEEN 28 AND 33;
```

It reads "take `cust_type_cd`; when it equals `'I'` give 'Individual'; when it equals `'B'` give 'Business'". It is shorter, and less flexible: it can only test whether the one expression **equals** each value. No ranges, no second column. Use it to translate codes into labels, and the searched form for everything else.

One trap. A simple `CASE` can never match NULL, because it compares with `=` and nothing equals NULL:

```sql-run dataset=bank
SELECT txn_id,
       CASE teller_emp_id WHEN NULL THEN 'ATM/online' ELSE 'branch' END AS wrong,
       CASE WHEN teller_emp_id IS NULL THEN 'ATM/online' ELSE 'branch' END AS right
FROM txn
LIMIT 6;
```

The `wrong` column says "branch" on every row, including transactions with no teller. `WHEN NULL` means `teller_emp_id = NULL`, which is never true. The `right` column uses the searched form with `IS NULL`.

## CASE produces a value, so it can go anywhere a value can

In many programming languages `if` decides which instructions are carried out. SQL's `CASE` is different: it is an **expression**, something that produces a value. It can therefore appear wherever a value is allowed.

**In the `SELECT` list**: every example so far.

**In `ORDER BY`**, for a custom sort order. Titles sorted by rank instead of alphabetically:

```sql-run dataset=bank
SELECT emp_id, fname, lname, title
FROM employee
ORDER BY CASE title
           WHEN 'President' THEN 1
           WHEN 'Vice President' THEN 2
           WHEN 'Treasurer' THEN 3
           ELSE 4
         END, lname
LIMIT 8;
```

The `CASE` turns each title into a number; the rows are sorted by that number and then by last name.

**In `GROUP BY`**, to group by a category that is worked out on the spot:

```sql-run dataset=mlops
SELECT CASE
         WHEN model_type IN ('bert-base', 'distilbert', 'resnet50', 'efficientnet-b0') THEN 'deep learning'
         WHEN model_type IN ('xgboost', 'lightgbm', 'random_forest', 'lambdamart') THEN 'tree ensemble'
         ELSE 'classical'
       END AS family,
       COUNT(*) AS runs,
       ROUND(SUM(gpu_hours), 1) AS gpu_hours
FROM runs
GROUP BY family
ORDER BY runs DESC;
```

Each training run is assigned to one of three families by its model type, and the runs are then counted per family: 50 tree-ensemble runs, 21 deep-learning runs.

**In `WHERE`**: allowed, but a plain condition is usually clearer and lets the database use an index. `WHERE CASE WHEN type = 'I' THEN a ELSE b END > 10` is better written `WHERE (type = 'I' AND a > 10) OR (type <> 'I' AND b > 10)`.

**Inside an aggregate function**: the most important place of all, and the subject of the next lesson.

**In `UPDATE ... SET`**, to change different rows in different ways in one pass. (Each Run starts from a fresh copy of the data.)

```sql-run dataset=shop
UPDATE products
SET price = CASE
              WHEN discontinued = 1 THEN ROUND(price * 0.70, 2)   -- clearance
              WHEN price >= 1000    THEN ROUND(price * 0.95, 2)   -- premium promotion
              ELSE price
            END;
SELECT name, price, discontinued FROM products ORDER BY product_id LIMIT 6;
```

Discontinued products are cut by 30%, products at 1000 or more by 5%, and the rest keep their price. Note `ELSE price`. Without it, every product matching neither line would have its price set to NULL.

## When the rules are really data

`CASE` expressions can be nested, and a long list of `WHEN` lines is fine. When one grows large, ask whether the logic is really *data*. A mapping from thresholds to tiers can live in a small **lookup table** that you join to, so that changing a threshold means changing one row instead of editing twenty queries:

```sql-run dataset=bank
WITH tier(name, low, high) AS (
  VALUES ('low', 0, 999.99), ('medium', 1000, 9999.99), ('high', 10000, 1e12)
)
SELECT t.name AS tier, COUNT(*) AS accounts
FROM account a
JOIN tier t ON a.avail_balance BETWEEN t.low AND t.high
GROUP BY t.name;
```

Here the three tiers are written as a temporary three-row table with `WITH ... VALUES`, and each account is joined to the tier whose range contains its balance.

## Shorthand functions that are CASE in disguise

| Function | The same thing as a CASE |
|---|---|
| `COALESCE(a, b, c)` | `CASE WHEN a IS NOT NULL THEN a WHEN b IS NOT NULL THEN b ELSE c END` |
| `NULLIF(a, b)` | `CASE WHEN a = b THEN NULL ELSE a END` |
| `iif(c, x, y)` (SQLite, SQL Server), `IF(c, x, y)` (MySQL) | `CASE WHEN c THEN x ELSE y END` |

Use them when they fit; they are shorter and say what you mean.

## Worked example: a written policy turned into a CASE

Practise turning a policy into SQL. The bank's rule for the label shown to customers:

> Closed accounts show "Closed". Frozen accounts show "Contact branch". Otherwise, loans show "Loan"; deposit accounts show "Premier" at 10,000 or more, "Standard" from 1,000, and "Basic" below that. An account with no balance on file shows "Pending".

Arrange the lines from the most specific override down to the general case, and decide where NULL goes:

```sql-run dataset=bank
SELECT account_id, product_cd, status, avail_balance,
       CASE
         WHEN status = 'CLOSED'                THEN 'Closed'
         WHEN status = 'FROZEN'                THEN 'Contact branch'
         WHEN product_cd IN ('MRT', 'AUT', 'BUS', 'SBL') THEN 'Loan'
         WHEN avail_balance IS NULL            THEN 'Pending'
         WHEN avail_balance >= 10000           THEN 'Premier'
         WHEN avail_balance >= 1000            THEN 'Standard'
         ELSE 'Basic'
       END AS label
FROM account
WHERE account_id IN (101, 104, 107, 108, 120, 131, 142, 171)
ORDER BY account_id;
```

Account 101, an active checking account with 3820.42, is "Standard"; account 104, with 10000, is "Premier". Three decisions are visible in the order of the lines:

1. **Status overrides everything**, so those tests come first. A closed loan is "Closed", not "Loan".
2. **The NULL test comes before the numeric tests.** Without it, a NULL balance would fail both `>=` comparisons (a comparison with NULL is never true) and drop through to `ELSE`, quietly labelled "Basic". An explicit `IS NULL` line makes missing data visible.
3. **The thresholds go downward**, so each line may assume the earlier ones failed: `>= 1000` here means "from 1,000 up to 9,999.99".

A `CASE` is a piece of logic and deserves a test. Group by its result and look at the smallest and largest balance under each label:

```sql-run dataset=bank
SELECT CASE
         WHEN status = 'CLOSED'                THEN 'Closed'
         WHEN status = 'FROZEN'                THEN 'Contact branch'
         WHEN product_cd IN ('MRT', 'AUT', 'BUS', 'SBL') THEN 'Loan'
         WHEN avail_balance IS NULL            THEN 'Pending'
         WHEN avail_balance >= 10000           THEN 'Premier'
         WHEN avail_balance >= 1000            THEN 'Standard'
         ELSE 'Basic'
       END AS label,
       COUNT(*) AS accounts,
       MIN(avail_balance) AS min_balance,
       MAX(avail_balance) AS max_balance
FROM account
GROUP BY label
ORDER BY accounts DESC;
```

The 42 "Standard" accounts range from 1290.22 to 8989.19: none below 1,000 and none at 10,000 or above, so the boundaries hold. Grouping by a `CASE` is the quickest way to check it.

## CASE and data types

A `CASE` expression has *one* type, so every line should produce the same kind of value. Mixing is an error in PostgreSQL and a source of odd behaviour in SQLite:

```sql-run dataset=bank
SELECT account_id,
       CASE WHEN avail_balance > 0 THEN avail_balance ELSE 'n/a' END AS mixed_types,
       typeof(CASE WHEN avail_balance > 0 THEN avail_balance ELSE 'n/a' END) AS type_of_result,
       CASE WHEN avail_balance > 0 THEN printf('%.2f', avail_balance) ELSE 'n/a' END AS consistent_text
FROM account
WHERE account_id IN (107, 108, 110, 112);
```

`typeof` reports the type of a value. The `mixed_types` column is a number (`real`) on one row and text on the next. Sort or add up such a column and the result is unpredictable. Make all lines agree: convert numbers to text when the column is for display (third column), or use NULL instead of a placeholder when the column will be used in further arithmetic, since NULL fits any type.

## Stopping at the first match is a guarantee

`CASE` promises that its lines are tested in order and that checking **stops at the first match**. This is called **short-circuit evaluation**, and you can rely on it to protect a calculation that would otherwise fail:

```sql-run dataset=bank
SELECT account_id, avail_balance, pending_balance,
       CASE
         WHEN avail_balance = 0 THEN NULL
         ELSE ROUND(100.0 * (pending_balance - avail_balance) / avail_balance, 2)
       END AS pending_change_pct
FROM account
WHERE pending_balance <> avail_balance
ORDER BY account_id
LIMIT 8;
```

The division is reached only when the balance is not zero. By contrast, the order in which the parts of an `AND` or `OR` in `WHERE` are tested is **not** guaranteed, because the optimizer may rearrange them. `WHERE x <> 0 AND y / x > 2` is therefore not a safe guard on every database. `CASE` is.

## CASE on different databases

| Feature | SQLite | MySQL | PostgreSQL |
|---|---|---|---|
| Searched and simple `CASE` | yes | yes | yes |
| Shorthand | `iif(c, a, b)` | `IF(c, a, b)` | none; use `CASE` |
| Counting rows that meet a condition | `SUM(CASE ...)`, `FILTER (WHERE ...)` | `SUM(CASE ...)`, `SUM(condition)` | `SUM(CASE ...)`, `FILTER (WHERE ...)` |
| Checking that all results share a type | lenient | lenient | strict |

> [!INTERVIEW]
> `CASE` questions usually arrive in disguise: "put customers into tiers", "swap the values M and F in one `UPDATE`" (`SET sex = CASE sex WHEN 'M' THEN 'F' ELSE 'M' END`), "count X and Y in separate columns". The follow-up is nearly always about a boundary value or a NULL, so say which line catches each.

## Pitfalls

- **The order of the lines.** The first true `WHEN` wins.
- **A missing `ELSE`** gives NULL: fatal in an `UPDATE`, useful inside an aggregate.
- **`ELSE 0` inside `AVG` or `COUNT`** changes the meaning.
- **A simple `CASE` with NULL** never matches; use the searched form with `IS NULL`.
- **Results of mixed types**: an error on strict databases, strange sorting in SQLite.
- **`CASE` in `WHERE` on a large table** hides the columns from the optimizer.

## Summary

- `CASE` is SQL's standard conditional expression; it returns a value and can be used almost anywhere.
- The **searched** form checks any conditions from top to bottom and returns the first match; the **simple** form tests one expression for equality.
- No match and no `ELSE` gives NULL.
- Use `CASE` in `SELECT` for labels, in `ORDER BY` for custom sorting, in `GROUP BY` for categories worked out on the spot, in `UPDATE` for conditional changes, and inside aggregates for conditional totals.

## Glossary

- **Conditional logic** — choosing between alternatives according to a test.
- **Expression** — any piece of SQL that produces a value: a column, a calculation, a function call, a `CASE`.
- **`CASE` expression** — SQL's "if ... then ... else": it returns one of several values depending on conditions.
- **Searched `CASE`** — the form in which each `WHEN` has its own full condition.
- **Simple `CASE`** — the form that compares one expression for equality with a list of values.
- **`WHEN` / `THEN` / `ELSE` / `END`** — a test / the result if the test is true / the result if no test is true / the end of the expression.
- **Branch** — one `WHEN ... THEN ...` line, or the `ELSE`.
- **Short-circuit evaluation** — stopping at the first branch that matches without evaluating the rest.
- **Lookup table** — a small table that maps codes or ranges to labels, used by joining.
- **`iif` / `IF`** — two-way shorthand for `CASE` in SQLite and SQL Server / MySQL.
- **`typeof`** — an SQLite function that reports the data type of a value.

```quiz
[
  {"q": "What does a CASE expression return when no WHEN matches and there is no ELSE?", "options": ["0", "An empty string", "NULL", "An error"], "answer": 2, "explain": "A missing ELSE behaves as ELSE NULL."},
  {"q": "For price = 1500, what does CASE WHEN price >= 20 THEN 'budget' WHEN price >= 1000 THEN 'premium' END return?", "options": ["premium", "budget", "NULL", "Both"], "answer": 1, "explain": "Branches are tested in order and the first true one wins; 1500 >= 20 is true."},
  {"q": "Why does CASE x WHEN NULL THEN 'missing' END never return 'missing'?", "options": ["NULL is not allowed in CASE", "A simple CASE compares with =, and x = NULL is never true", "ELSE is required", "It does return it"], "answer": 1, "explain": "Use the searched form: CASE WHEN x IS NULL THEN ..."},
  {"q": "AVG(CASE WHEN product_cd = 'CHK' THEN avail_balance END) computes...", "options": ["The average of all balances", "The average checking balance", "Zero", "The number of checking accounts"], "answer": 1, "explain": "Rows of other products give NULL, which AVG ignores."},
  {"q": "What is the danger of omitting ELSE in UPDATE t SET price = CASE WHEN ... THEN ... END?", "options": ["Nothing", "Rows matching no branch get price = NULL", "The update is skipped", "A syntax error"], "answer": 1, "explain": "Add ELSE price so that other rows keep their value."},
  {"q": "Which form can test ranges such as balance < 1000?", "options": ["Simple CASE", "Searched CASE", "Both", "Neither"], "answer": 1, "explain": "A simple CASE only tests equality against one expression."},
  {"q": "NULLIF(a, b) is shorthand for...", "options": ["CASE WHEN a IS NULL THEN b ELSE a END", "CASE WHEN a = b THEN NULL ELSE a END", "CASE WHEN b IS NULL THEN a END", "COALESCE(a, b)"], "answer": 1, "explain": "It returns NULL when the two arguments are equal, and a otherwise."},
  {"q": "In a CASE that labels balances, why put WHEN avail_balance IS NULL before WHEN avail_balance >= 10000?", "options": ["IS NULL is faster", "Otherwise a NULL balance fails every comparison and falls through to ELSE unnoticed", "SQL requires NULL tests first", "It makes no difference"], "answer": 1, "explain": "Comparisons with NULL are never true, so without an explicit branch the missing value would get the ELSE label."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 11 "Conditional Logic" (what conditional logic is, the case expression, searched and simple case expressions), restated in original wording with this guide's own datasets.
