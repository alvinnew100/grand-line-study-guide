# Constraints and cascading

> **Before this lesson:** you should know what a primary key and a foreign key are and how `CREATE TABLE` declares columns ([Data types and CREATE TABLE](#/lesson/sql/data-types-tables)), have seen statements rejected for breaking a rule ([Inserting, updating, deleting - and when statements go bad](#/lesson/sql/dml-constraints)), and know what an index is ([Indexes and query plans](#/lesson/sql/indexes)).

## In plain words

A database is written to by many hands: the website, a mobile app, a nightly import script, a developer fixing something late at night. Each of them can make mistakes. A **constraint** is a rule about what valid data looks like, stored in the database itself, so that the database refuses anything that breaks it, whoever is writing.

An everyday picture: an online form that will not let you submit until the required boxes are filled in, the email looks like an email, and the date of birth is not in the future. The form does not trust you to be careful; it checks. Constraints are those checks, placed at the last possible gate: the table.

This lesson covers the kinds of constraint, how they are created, how they relate to indexes, and one more ability. When a row that other rows depend on is deleted or changed, the database can either refuse or carry the change through to the dependent rows automatically. The second behaviour is called **cascading**, as when one falling domino knocks over the next.

**Why it matters for a job.** Bad data is far more expensive to clean up than to prevent. Constraints are also a regular interview topic: "primary key versus unique key", "what does `ON DELETE CASCADE` do, and when is it dangerous?", "how would you guarantee that every order belongs to a real customer?".

## The kinds of constraint

| Constraint | What it restricts |
|---|---|
| **Primary key** | the column or columns whose value identifies each row; must be unique and never NULL |
| **Foreign key** | a column's values to those that exist in the key of another table; can also say what happens when that other row changes |
| **Unique** | a column or combination of columns to values that do not repeat within the table |
| **Check** | the values a column may hold, by a condition such as `quantity > 0` |
| **Not null** | a column from being left empty |

`DEFAULT` is usually discussed alongside them. It is not a restriction: it supplies a value when an `INSERT` does not give one.

In a foreign-key relationship, the table that is pointed at is called the **parent** and the table holding the pointer is the **child**. `customer` is a parent of `account`, because each account row stores the id of its customer.

Without constraints, consistency is a matter of hope. Suppose the database let you change a customer's id in `customer` without changing it in `account`. The accounts would now point at a customer who does not exist. Such child rows are called **orphaned rows**, and keeping every pointer valid is called **referential integrity**. With primary and foreign keys declared, the database either rejects the change or carries it through to the children for you.

> [!WARNING]
> Two reminders about enforcement. **SQLite** checks foreign keys only after `PRAGMA foreign_keys = ON` has been run on the connection (the practice datasets do this). **MySQL** enforces them only on tables that use the InnoDB engine.

## Creating constraints

Constraints are normally written in `CREATE TABLE`. Here is a product table with every kind:

```sql
CREATE TABLE product (
  product_cd      VARCHAR(10) NOT NULL,
  name            VARCHAR(50) NOT NULL,
  product_type_cd VARCHAR(10) NOT NULL,
  date_offered    DATE,
  date_retired    DATE,
  CONSTRAINT pk_product PRIMARY KEY (product_cd),
  CONSTRAINT fk_product_type_cd FOREIGN KEY (product_type_cd)
      REFERENCES product_type (product_type_cd),
  CONSTRAINT uq_product_name UNIQUE (name),
  CONSTRAINT ck_product_dates CHECK (date_retired IS NULL OR date_retired >= date_offered)
);
```

Line by line, for the four `CONSTRAINT` lines:

- `pk_product`: `product_cd` identifies each product.
- `fk_product_type_cd`: the `product_type_cd` of every product must exist in the table `product_type`.
- `uq_product_name`: no two products may share a name.
- `ck_product_dates`: a product cannot be withdrawn before it was first offered.

The names after the word `CONSTRAINT` are optional and worth giving: error messages mention the name, and you need it to remove the constraint later.

On most databases a constraint can also be added or removed afterwards:

```sql
-- MySQL, PostgreSQL, SQL Server, Oracle
ALTER TABLE product
  ADD CONSTRAINT fk_product_type_cd FOREIGN KEY (product_type_cd)
      REFERENCES product_type (product_type_cd);

ALTER TABLE product DROP CONSTRAINT fk_product_type_cd;      -- MySQL: DROP FOREIGN KEY fk_product_type_cd
```

When a constraint is added to a table that already holds rows, the database checks every existing row first. If any row breaks the rule, the `ALTER` fails.

> [!NOTE]
> **SQLite's `ALTER TABLE` cannot add or drop constraints.** They must be declared in `CREATE TABLE`. To change them you rebuild: create a new table with the definition you want, copy the data across, drop the old table and rename the new one, all inside a transaction.

You can inspect the constraints of an existing table. The first query lists the foreign keys of `account`:

```sql-run dataset=bank
SELECT "table" AS references_table, "from" AS column, "to" AS referenced_column, on_update, on_delete
FROM pragma_foreign_key_list('account');
```

Four rows: `account` points at `employee`, `branch`, `customer` and `product`. The last two columns say `NO ACTION`, the default behaviour, explained below. The second query shows the full `CREATE TABLE` text that SQLite stored:

```sql-run dataset=bank
SELECT sql FROM sqlite_master WHERE name = 'account';
```

Reading it, you can spot `NOT NULL` on several columns, four `REFERENCES` clauses (a short way of writing a foreign key next to its column) and a `CHECK` on `status`.

### A check constraint at work

This block fails on purpose:

```sql-run dataset=shop
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (1, 1, 0, 1199.0);
```

`CHECK constraint failed: quantity > 0`. An order line with a quantity of zero is refused.

A check may compare several columns of the same row, as `ck_product_dates` does. It cannot look at other rows or other tables; rules of that kind need a unique constraint, a foreign key, or a trigger (a small program the database runs automatically when data changes).

A subtle point: a check is broken only when its condition is **false**. If a column is NULL, the comparison is neither true nor false, and the row is **accepted**. `CHECK (price > 0)` therefore allows a NULL price. Add `NOT NULL` if that is not what you want.

> [!NOTE]
> MySQL accepted `CHECK` constraints but **ignored** them before version 8.0.16. Current versions enforce them.

## Constraints and indexes

The two are closely linked, because checking a rule quickly needs fast lookups.

- **Primary key and unique constraints** must discover whether a value is already present. The database creates a **unique index** for this automatically.
- **Foreign key constraints** need two lookups. When a *child* row is inserted, find its parent; the parent's primary-key index serves that. When a *parent* row is deleted or its key changed, find any children; that needs an index on the child's foreign-key column, **if one exists**.

Who creates that second index differs between products:

| Constraint | MySQL (InnoDB) | SQL Server | Oracle | PostgreSQL | SQLite |
|---|---|---|---|---|---|
| Primary key | unique index | unique index | uses an existing index or creates one | unique index | the table's own order, or an automatic index |
| Unique | unique index | unique index | uses an existing index or creates one | unique index | automatic index |
| Foreign key | **creates an index** | no | no | no | no |

So everywhere except MySQL, **you** should index foreign-key columns. Otherwise deleting one customer forces a scan of the whole `account` table to check for children, and every join on that column is slow.

```sql-run dataset=bank
SELECT m.name AS tbl, il.name AS index_name, il."unique", il.origin
FROM sqlite_master m
JOIN pragma_index_list(m.name) il
WHERE m.type = 'table'
ORDER BY m.name;
```

Only three indexes exist in the whole bank database, all created automatically (`u` for a unique constraint, `pk` for a primary key that is not a whole number). No foreign key is indexed. In a real system you would add `CREATE INDEX account_cust_idx ON account (cust_id)` and its relatives.

## What a foreign key does when a statement would break it

By default, the statement **fails**. Three cases, each of which fails on purpose here.

Inserting a child with no parent (there is no product type `CRYPTO`):

```sql-run dataset=bank
INSERT INTO product (product_cd, name, product_type_cd, date_offered)
VALUES ('CRY', 'crypto wallet', 'CRYPTO', '2024-06-01');
```

Deleting a parent that still has children (loan products exist):

```sql-run dataset=bank
DELETE FROM product_type WHERE product_type_cd = 'LOAN';
```

Changing a parent's key while children still refer to the old value:

```sql-run dataset=bank
UPDATE product_type SET product_type_cd = 'LENDING' WHERE product_type_cd = 'LOAN';
```

All three report `FOREIGN KEY constraint failed`. The data stays consistent, and you are made to say what you mean: move or delete the children first, or instruct the database to do it.

## Cascading

The foreign-key definition can tell the database to **carry the change through** instead of rejecting it:

```sql
CONSTRAINT fk_product_type_cd FOREIGN KEY (product_type_cd)
    REFERENCES product_type (product_type_cd)
    ON UPDATE CASCADE
    ON DELETE CASCADE
```

- **`ON UPDATE CASCADE`**: when the parent's key value changes, the matching child rows are updated to the new value. Rename `LOAN` to `LENDING` in `product_type` and every loan product follows.
- **`ON DELETE CASCADE`**: when a parent row is deleted, its child rows are deleted too.

The full list of choices, called **referential actions**:

| Action | When the parent is deleted or its key is updated... |
|---|---|
| `NO ACTION` / `RESTRICT` (the default) | reject the statement if children exist |
| `CASCADE` | delete the children / update their key |
| `SET NULL` | set the children's foreign key to NULL (the column must allow NULL) |
| `SET DEFAULT` | set it to the column's default value |

Try it with a small parent and child. The block creates wish lists (owned by customers) and wish-list items (owned by wish lists), fills them, deletes one wish list and shows what is left of the items.

```sql-run dataset=shop
PRAGMA foreign_keys = ON;
CREATE TABLE wishlists (
  wishlist_id INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
  name TEXT NOT NULL
);
CREATE TABLE wishlist_items (
  wishlist_id INTEGER NOT NULL REFERENCES wishlists(wishlist_id) ON DELETE CASCADE,
  product_id  INTEGER REFERENCES products(product_id) ON DELETE SET NULL,
  note TEXT
);
INSERT INTO wishlists VALUES (1, 13, 'birthday'), (2, 13, 'kitchen'), (3, 26, 'gym');
INSERT INTO wishlist_items VALUES (1, 10, 'headphones'), (1, 38, 'watch'), (2, 16, 'espresso'), (3, 31, 'dumbbells');

DELETE FROM wishlists WHERE wishlist_id = 1;       -- cascades to its two items
SELECT * FROM wishlist_items;
```

Four items were inserted and two remain: "espresso" and "dumbbells". The `DELETE` named only the wish list; its two items ("headphones" and "watch") were removed by the cascade. The other lists were not touched.

### When to cascade

Cascades are convenient and dangerous in equal measure.

- **A good fit: ownership.** The child has no meaning without the parent: an order and its items, a wish list and its items, a training run and its measurements.
- **A bad fit: reference.** The child merely mentions the parent: a product in old order items, a customer on old orders. Deleting a product should not silently erase sales history. Keep the default, or avoid deleting at all with a **soft delete**: mark the row as inactive instead of removing it, as the shop's `products.discontinued` column does.
- `ON UPDATE CASCADE` is rarely needed when keys are meaningless numbers that never change. It matters when keys are meaningful codes that might be renamed.
- `SET NULL` suits optional pointers. If an employee leaves, `account.open_emp_id` could become NULL instead of blocking the deletion.

> [!WARNING]
> One `DELETE` on a table at the top of a chain of cascades can remove millions of rows across many tables, hold locks for a long time, and cannot be undone once committed. In production, large deletions are usually done explicitly, in batches, children first.

## Checking at commit instead of at each statement

By default every statement must leave all constraints satisfied. Now and then a temporary violation is needed, for example when inserting two rows that point at each other. The standard lets a constraint be declared `DEFERRABLE INITIALLY DEFERRED`, which means it is checked at **`COMMIT`** instead of after each statement (PostgreSQL, Oracle, and SQLite for foreign keys). This is called **deferred checking**.

## Constraints as documentation and as hints

Beyond protection, constraints tell people and tools how the data fits together. Diagrams of a database are drawn from its foreign keys. Optimizers use them too: a unique constraint tells the optimizer that a lookup returns at most one row.

In large analytics databases (Snowflake, BigQuery, Redshift), primary and foreign keys are often **informational only**: declared, and not enforced. They are kept for their value as documentation and hints, while the actual checking is done by tests in the data pipeline. Never assume a declared key is enforced there.

## Worked example: testing a table's constraints

A table's constraints are claims about its data, and a short test proves them. Each of the next three blocks *should* fail, and each error names the rule that stopped it.

```sql-run dataset=shop
PRAGMA foreign_keys = ON;
-- 1. status outside the allowed list (CHECK)
INSERT INTO orders (customer_id, order_date, status) VALUES (1, '2024-12-20', 'lost');
```

```sql-run dataset=shop
PRAGMA foreign_keys = ON;
-- 2. order for a customer that does not exist (FOREIGN KEY)
INSERT INTO orders (customer_id, order_date, status) VALUES (9999, '2024-12-20', 'pending');
```

```sql-run dataset=shop
-- 3. two customers with the same email (UNIQUE)
INSERT INTO customers (first_name, last_name, email, country, signup_date)
SELECT 'Copy', 'Cat', email, 'USA', '2024-12-20' FROM customers WHERE email IS NOT NULL LIMIT 1;
```

The first reports a failed `CHECK`, the second a failed `FOREIGN KEY`, the third `UNIQUE constraint failed: customers.email`.

A fourth statement should succeed, to show that the rules do not reject everything. `RETURNING` hands back the row that was inserted:

```sql-run dataset=shop
PRAGMA foreign_keys = ON;
INSERT INTO orders (customer_id, order_date, status) VALUES (1, '2024-12-20', 'pending')
RETURNING order_id, customer_id, status, shipping_fee;
```

Order 250 is created. Its `shipping_fee` is 0.0 although the statement gave none: the column's `DEFAULT` filled it in.

Writing such failing-on-purpose tests when you design a table costs little, and it records the intended rules better than any comment.

> [!INTERVIEW]
> Typical questions. *Primary key versus unique key*: a table has one primary key and it can never be NULL; a table can have several unique constraints, and they usually allow NULLs. *What does `ON DELETE CASCADE` do and when is it dangerous?* *How would you enforce "an order must have at least one item"?* That rule cannot be written as a plain constraint: it needs a deferred check, a trigger or application logic, and saying so is a good answer.

## Pitfalls

- **Foreign keys that are not enforced**: the SQLite pragma is off, the MySQL table is MyISAM, or the keys are informational only.
- **No index on foreign-key columns** outside MySQL.
- **A `CHECK` passes on NULL.** Combine it with `NOT NULL`.
- **Cascading deletes on reference relationships**: history disappears without a trace.
- **`ALTER TABLE ... ADD CONSTRAINT` in SQLite**: not supported.
- **Unnamed constraints**: hard to remove, and their error messages are cryptic.

## Summary

- Constraints (primary key, foreign key, unique, check, not null) define valid data and are enforced for every writer.
- Primary key and unique constraints are backed by automatic unique indexes; foreign-key columns usually need an index you create yourself (MySQL's InnoDB creates it).
- By default a foreign key **rejects** a statement that would leave orphaned rows; `CASCADE`, `SET NULL` and `SET DEFAULT` carry the change through instead.
- Cascade for ownership; restrict, or soft-delete, for references.
- Test constraints with statements that should fail.

## Glossary

- **Constraint** — a rule about valid data that the database enforces.
- **Primary key** — the column or columns that uniquely identify each row; never NULL.
- **Foreign key** — a column whose values must exist in the key of another table.
- **Unique constraint** — a rule that values in a column or combination of columns may not repeat.
- **Check constraint** — a rule that a row must satisfy a stated condition.
- **Parent / child table** — the table being pointed at / the table holding the foreign key.
- **Orphaned row** — a child row whose foreign key points at a parent that does not exist.
- **Referential integrity** — the property that every foreign key points at an existing row.
- **Referential action** — what the database does to children when a parent is deleted or its key changes.
- **Cascade** — to carry a delete or key change from a parent through to its children.
- **`RESTRICT` / `NO ACTION`** — refuse the change while children exist.
- **`SET NULL`** — empty the children's foreign key when the parent goes.
- **Soft delete** — marking a row as inactive instead of removing it.
- **Deferred checking** — checking a constraint at `COMMIT` instead of after each statement.
- **Informational constraint** — a declared constraint that the database does not enforce.
- **Trigger** — a small program the database runs automatically when data changes.

```quiz
[
  {"q": "What is an orphaned row?", "options": ["A row with a NULL primary key", "A child row whose foreign key refers to a parent that does not exist", "A row not covered by an index", "A row in a temporary table"], "answer": 1, "explain": "Foreign key constraints exist to prevent exactly this."},
  {"q": "With a default (no action) foreign key, what happens when you delete a parent row that has children?", "options": ["The children are deleted", "The children's keys become NULL", "The statement fails", "Nothing is checked"], "answer": 2, "explain": "The default is to reject the delete; cascading must be asked for explicitly."},
  {"q": "What does ON DELETE CASCADE do?", "options": ["Prevents deletes", "Deletes child rows when the parent is deleted", "Sets child keys to NULL", "Deletes the parent when a child is deleted"], "answer": 1, "explain": "The delete is carried from the parent through to its children."},
  {"q": "Which database automatically creates an index on foreign key columns?", "options": ["PostgreSQL", "SQLite", "MySQL (InnoDB)", "SQL Server"], "answer": 2, "explain": "InnoDB requires one and creates it; elsewhere you should create it yourself."},
  {"q": "A column has CHECK (price > 0). Is a NULL price accepted?", "options": ["No", "Yes: the condition is unknown, not false", "Only in MySQL", "Only with a default"], "answer": 1, "explain": "A CHECK rejects a row only when its condition is false; add NOT NULL to forbid NULLs."},
  {"q": "For which relationship is ON DELETE CASCADE most appropriate?", "options": ["product -> order_items", "customer -> orders", "order -> order_items", "product_type -> product"], "answer": 2, "explain": "Order items have no meaning without their order (ownership); the others are references whose history should be kept."},
  {"q": "How do you add a foreign key to an existing SQLite table?", "options": ["ALTER TABLE ... ADD CONSTRAINT", "Rebuild the table with the new definition and copy the data", "PRAGMA add_fk", "CREATE FOREIGN KEY"], "answer": 1, "explain": "SQLite's ALTER TABLE cannot add constraints; the table must be rebuilt."},
  {"q": "Which statement about a table's keys is correct?", "options": ["A table may have several primary keys", "A table has one primary key, which is never NULL, and may have several unique constraints", "Unique constraints can never contain NULL", "A primary key may contain duplicates if it is indexed"], "answer": 1, "explain": "There is exactly one primary key per table; unique constraints can be many and usually allow NULLs."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 13 "Indexes and Constraints" (constraints, constraint creation, constraints and indexes, cascading constraints), restated in original wording with this guide's own datasets. SQLite documentation, "SQLite Foreign Key Support".
