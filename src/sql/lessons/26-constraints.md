# Constraints and cascading

A **constraint** is a restriction placed on one or more columns of a table. Constraints are how you tell the database what *valid* data looks like, so that it can refuse everything else — no matter which application, script or person is doing the writing. You met them briefly when creating tables; this lesson treats them properly: the kinds of constraint, how to create and drop them, how they relate to indexes, and what **cascading** updates and deletes do.

## Kinds of constraint

The book lists four:

| Constraint | Restricts |
|---|---|
| **Primary key** | the column(s) that guarantee uniqueness within the table; never NULL |
| **Foreign key** | one or more columns to values that exist in another table's primary (or unique) key columns; may also govern what happens on update/delete |
| **Unique** | one or more columns to unique values within the table |
| **Check** | the allowable values for a column (or combination of columns) |

Plus the simplest of all, `NOT NULL`, and `DEFAULT`, which is not a restriction but usually discussed alongside.

Without constraints, consistency is a matter of hope. The book's illustration: if the server lets you change a customer's id in the `customer` table without changing the same id in `account`, you end up with accounts that point at a customer who no longer exists — **orphaned rows**. With primary and foreign key constraints in place, the server will either raise an error when you try, or **propagate** the change for you.

> [!WARNING]
> Remember the two enforcement caveats from the DML lesson: **SQLite** checks foreign keys only when `PRAGMA foreign_keys = ON` has been run on the connection (the sandbox datasets do this), and **MySQL** enforces them only for InnoDB tables.

## Constraint creation

Constraints are normally created with the table. Here are the bank's `product` and `account`, in the style of the book, with every kind represented:

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

Naming constraints (`CONSTRAINT pk_product …`) is optional but worthwhile: error messages mention the name, and you need it to drop the constraint later.

In most databases you can also add and remove constraints afterwards:

```sql
ALTER TABLE product
  ADD CONSTRAINT fk_product_type_cd FOREIGN KEY (product_type_cd)
      REFERENCES product_type (product_type_cd);

ALTER TABLE product DROP CONSTRAINT fk_product_type_cd;      -- MySQL: DROP FOREIGN KEY fk_product_type_cd
```

Adding a constraint to a populated table makes the server check every existing row first; if any violates it, the `ALTER` fails.

> [!NOTE]
> **SQLite's `ALTER TABLE` cannot add or drop constraints.** Constraints must be declared in `CREATE TABLE`. To change them you rebuild: create a new table with the desired definition, copy the data, drop the old table, rename the new one — all inside a transaction. (Unique constraints can be approximated afterwards with `CREATE UNIQUE INDEX`.)

Inspect the constraints of an existing table:

```sql-run dataset=bank
SELECT "table" AS references_table, "from" AS column, "to" AS referenced_column, on_update, on_delete
FROM pragma_foreign_key_list('account');
```

```sql-run dataset=bank
SELECT sql FROM sqlite_master WHERE name = 'account';
```

### Check constraints in action

```sql-run dataset=shop
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (1, 1, 0, 1199.0);
```

`CHECK constraint failed: quantity > 0`. A check constraint may reference several columns of the same row (`CHECK (date_retired >= date_offered)`), but not other rows or tables — for cross-row rules you need unique constraints, foreign keys, or triggers.

A subtle rule: a CHECK is violated only when its condition is **FALSE**. If it evaluates to UNKNOWN because a column is NULL, the row is accepted. `CHECK (price > 0)` therefore allows a NULL price; add `NOT NULL` if that is not intended.

> [!NOTE]
> MySQL accepted but **ignored** CHECK constraints before version 8.0.16 — the book, written earlier, notes that they are not enforced. Modern MySQL enforces them.

## Constraints and indexes

Constraints and indexes are closely linked, because checking a constraint efficiently requires fast lookups:

- **Primary key and unique constraints** need to find whether a value already exists → the server creates a **unique index** automatically.
- **Foreign key constraints** need two lookups: when a *child* row is inserted, find the parent (served by the parent's primary key index); when a *parent* row is deleted or its key updated, find any children (served by an index on the child's foreign key column — **if one exists**).

Who creates that second index varies, as the book tabulates:

| Constraint type | MySQL (InnoDB) | SQL Server | Oracle | PostgreSQL | SQLite |
|---|---|---|---|---|---|
| Primary key | unique index | unique index | uses existing or creates | unique index | rowid or automatic index |
| Unique | unique index | unique index | uses existing or creates | unique index | automatic index |
| Foreign key | **creates an index** | no | no | no | no |

So everywhere except MySQL, **you** should index foreign key columns. Otherwise deleting one customer forces a full scan of `account` to check for children, and every join on the key is slow.

```sql-run dataset=bank
SELECT m.name AS tbl, il.name AS index_name, il."unique", il.origin
FROM sqlite_master m
JOIN pragma_index_list(m.name) il
WHERE m.type = 'table'
ORDER BY m.name;
```

Only the automatically created indexes exist (origin `u` for UNIQUE, `pk` for non-integer primary keys). No foreign key in this database is indexed; in a real deployment you would add `CREATE INDEX account_cust_idx ON account (cust_id)` and friends.

## What a foreign key does on violation

With the constraint in place, what happens when a statement would break referential integrity? By default, the statement **fails**.

Inserting a child with no parent:

```sql-run dataset=bank
INSERT INTO product (product_cd, name, product_type_cd, date_offered)
VALUES ('CRY', 'crypto wallet', 'CRYPTO', '2024-06-01');
```

Deleting a parent that still has children:

```sql-run dataset=bank
DELETE FROM product_type WHERE product_type_cd = 'LOAN';
```

Updating a parent key that children refer to:

```sql-run dataset=bank
UPDATE product_type SET product_type_cd = 'LENDING' WHERE product_type_cd = 'LOAN';
```

All three raise `FOREIGN KEY constraint failed`. The data stays consistent, and you are forced to say what you really mean: move or delete the children first, or tell the server to do it.

## Cascading constraints

The foreign key definition can instruct the server to **propagate** changes instead of rejecting them:

```sql
CONSTRAINT fk_product_type_cd FOREIGN KEY (product_type_cd)
    REFERENCES product_type (product_type_cd)
    ON UPDATE CASCADE
    ON DELETE CASCADE
```

- **`ON UPDATE CASCADE`** — when the parent's key value changes, the server updates the matching child rows to the new value. The book calls this a *cascading update*: rename `LOAN` to `LENDING` in `product_type` and every loan product follows.
- **`ON DELETE CASCADE`** — when a parent row is deleted, the server deletes its child rows as well.

The full menu of referential actions:

| Action | On delete/update of the parent… |
|---|---|
| `NO ACTION` / `RESTRICT` (default) | reject the statement if children exist |
| `CASCADE` | delete the children / update their key |
| `SET NULL` | set the children's foreign key to NULL (column must be nullable) |
| `SET DEFAULT` | set it to the column's default |

Try it with a small parent/child pair:

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

Deleting wishlist 1 removed its two items automatically; the others are untouched.

### When to cascade

Cascades are convenient and dangerous in equal measure.

- **Good fit:** true *ownership* relationships, where the child has no meaning without the parent — order → order items, wishlist → items, a run → its metrics.
- **Bad fit:** *reference* relationships — product → order items, customer → orders, product type → products. Deleting a product should not silently erase sales history. Use the default `RESTRICT`, or avoid deletes altogether with a **soft delete** (`discontinued = 1`, `deleted_at` timestamp), as the shop's `products.discontinued` column does.
- `ON UPDATE CASCADE` is rarely needed if you use surrogate keys, which never change. It matters with natural keys such as product codes.
- `SET NULL` suits optional references: if an employee leaves, `account.open_emp_id` could become NULL rather than block the deletion.

> [!WARNING]
> One `DELETE` on a root table with cascades can remove millions of rows across many tables, hold locks for a long time, and cannot be undone after commit. In production, large cascading deletes are usually done explicitly, in batches, children first.

## Deferred checking

By default each statement must leave the constraints satisfied. Occasionally you need a temporary violation — for example, inserting two rows that reference each other, or loading tables in an awkward order. The standard allows constraints to be `DEFERRABLE INITIALLY DEFERRED`, meaning they are checked at **COMMIT** instead of per statement (PostgreSQL, Oracle, SQLite for foreign keys). Bulk-loading tools often go further and disable constraint checking during the load, then re-validate.

## Constraints as documentation — and as optimizer hints

Beyond protection, constraints tell humans and tools how the data fits together: ER diagrams are drawn from foreign keys, ORMs generate relationships from them, and query optimizers exploit them (a join to a parent table on a NOT NULL foreign key can be eliminated if no parent columns are used; a unique constraint tells the planner a lookup returns at most one row). In analytical warehouses (Snowflake, BigQuery, Redshift) primary and foreign keys are often *informational only* — declared, not enforced — exactly for these documentation and optimisation benefits, with integrity checked by pipeline tests (dbt's `unique`, `not_null`, `relationships` tests) instead.

## Pitfalls

- **Foreign keys not enforced** (SQLite pragma off, MyISAM, informational constraints in warehouses).
- **Unindexed foreign key columns** outside MySQL.
- **CHECK passes on NULL** — combine with NOT NULL.
- **Cascading deletes on reference relationships** — silent loss of history.
- **Trying `ALTER TABLE … ADD CONSTRAINT` in SQLite.**
- **Unnamed constraints** — hard to drop, cryptic errors.

## Summary

- Constraints — primary key, foreign key, unique, check, not null — define valid data and are enforced for every writer.
- Primary key and unique constraints are backed by automatic unique indexes; foreign key columns usually need an index you create yourself (MySQL InnoDB creates it).
- By default a foreign key **rejects** orphan-creating statements; `ON DELETE/UPDATE CASCADE`, `SET NULL` and `SET DEFAULT` propagate instead.
- Cascade for ownership, restrict (or soft-delete) for references.

```quiz
[
  {"q": "What is an orphaned row?", "options": ["A row with a NULL primary key", "A child row whose foreign key refers to a parent that does not exist", "A row not covered by an index", "A row in a temporary table"], "answer": 1, "explain": "Foreign key constraints exist to prevent exactly this."},
  {"q": "With a default (no action) foreign key, what happens when you delete a parent row that has children?", "options": ["Children are deleted", "Children's keys become NULL", "The statement fails", "Nothing is checked"], "answer": 2, "explain": "The default action rejects the delete; cascading must be requested explicitly."},
  {"q": "What does ON DELETE CASCADE do?", "options": ["Prevents deletes", "Deletes child rows when the parent is deleted", "Sets child keys to NULL", "Deletes the parent when a child is deleted"], "answer": 1, "explain": "The delete propagates from parent to children."},
  {"q": "Which database automatically creates an index on foreign key columns?", "options": ["PostgreSQL", "SQLite", "MySQL (InnoDB)", "SQL Server"], "answer": 2, "explain": "InnoDB requires and creates one; elsewhere you should create it yourself."},
  {"q": "A column has CHECK (price > 0). Is a NULL price accepted?", "options": ["No", "Yes - the check is UNKNOWN, not FALSE", "Only in MySQL", "Only with a default"], "answer": 1, "explain": "A CHECK rejects only when the condition is FALSE; add NOT NULL to forbid NULLs."},
  {"q": "For which relationship is ON DELETE CASCADE most appropriate?", "options": ["product -> order_items", "customer -> orders", "order -> order_items", "product_type -> product"], "answer": 2, "explain": "Line items have no meaning without their order (ownership); the others are references whose history should be kept."},
  {"q": "How do you add a foreign key to an existing SQLite table?", "options": ["ALTER TABLE ... ADD CONSTRAINT", "Rebuild the table with the new definition and copy the data", "PRAGMA add_fk", "CREATE FOREIGN KEY"], "answer": 1, "explain": "SQLite's ALTER TABLE cannot add constraints."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 13 "Indexes and Constraints" (constraints, constraint creation, constraints and indexes, cascading constraints). SQLite documentation, "SQLite Foreign Key Support".
