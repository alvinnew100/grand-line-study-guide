# Metadata and the data dictionary

> **Before this lesson:** you should know what tables, columns, data types, constraints, indexes and views are ([Data types and CREATE TABLE](#/lesson/sql/data-types-tables), [Indexes and query plans](#/lesson/sql/indexes), [Constraints and cascading](#/lesson/sql/constraints), [Views](#/lesson/sql/views)), and be able to join tables and use `group_concat` to glue a group's values into one string ([Strings and numbers](#/lesson/sql/strings-numbers)).

## In plain words

A database stores your data: customers, orders, payments. To do that it must also remember facts about the *containers*: which tables exist, what columns each has, the type of every column, which columns are keys, which indexes have been built. This information about the structure of the data is called **metadata**, which means "data about data".

An everyday picture: a library holds books, and it also keeps a catalogue. The catalogue contains no stories. It records, for every book, the title, the author, the shelf and the subject. You consult the catalogue to find out what the library has and where.

A database's catalogue is called the **data dictionary** or **system catalog**. The pleasant surprise is how it is stored: as tables. So the tool you already know, a `SELECT` statement, works on it. You can ask the database "which tables do you have?" and "which columns does this table have?" in SQL.

This lesson shows how to read metadata in SQLite and in the larger databases, and three practical things to do with it: produce documentation of a database, check that a release changed what it was supposed to change, and write queries that write other queries.

**Why it matters for a job.** On your first day with an unfamiliar database nobody hands you a manual. You explore it through its catalog. Interviewers ask practical versions of this: "how would you find every table that has a column called `customer_id`?", "how do you list the indexes on a table?".

## What the database records about itself

For each table, the database keeps at least:

- the table's name and how it is stored;
- each column's name, data type, default value and whether it may be NULL;
- which columns form the primary key;
- each foreign key: its columns and the table it points at;
- each index: its name, its columns and whether it forbids duplicates.

Every tool that draws a diagram of a database, or completes a column name as you type, gets its information from here. Each product publishes the catalog in its own way:

| Database | How metadata is published |
|---|---|
| Oracle | views such as `user_tables`, `all_constraints` |
| SQL Server | the `sys.*` catalog views, and `INFORMATION_SCHEMA` |
| MySQL | the `information_schema` database, plus `SHOW` commands |
| PostgreSQL | the `pg_catalog.*` tables, and the standard `information_schema` |
| SQLite | the table `sqlite_schema` (also called `sqlite_master`) and `PRAGMA` functions |

`information_schema` is defined by the SQL standard, so queries on it carry over largely unchanged between MySQL, PostgreSQL and SQL Server. SQLite does not have it. This lesson shows the SQLite way with live queries and the standard way beside it.

## SQLite: sqlite_master and pragmas

Everything SQLite knows about the objects in a database sits in one small table. An **object** here means anything that was created with a `CREATE` statement: a table, an index, a view, a trigger.

```sql-run dataset=bank
SELECT type, name, tbl_name
FROM sqlite_master
ORDER BY type, name;
```

Fourteen rows: three indexes first, then the eleven tables of the bank database. The columns of `sqlite_master` are:

- `type`: what kind of object it is (`table`, `index`, `view` or `trigger`);
- `name`: the object's name;
- `tbl_name`: for an index or trigger, the table it belongs to;
- `sql`: the text of the `CREATE` statement that made it.

That last column lets you read the definition of any table:

```sql-run dataset=bank
SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'employee';
```

The result is one long piece of text: the complete `CREATE TABLE employee (...)` statement. It is handy for a person and awkward for a program, because the columns are buried inside the text. For rows instead of text, SQLite provides **pragma functions**. A `PRAGMA` is an SQLite-specific command for settings and internal information; the functions whose names start with `pragma_` return such information as a table that you can select from.

| Pragma function | Returns |
|---|---|
| `pragma_table_info('t')` | one row per column: `cid, name, type, notnull, dflt_value, pk` |
| `pragma_index_list('t')` | the indexes on the table: `name, unique, origin` |
| `pragma_index_info('idx')` | the columns of an index, in order |
| `pragma_foreign_key_list('t')` | the foreign keys: `table, from, to, on_update, on_delete` |

```sql-run dataset=bank
SELECT cid, name, type, "notnull", dflt_value, pk
FROM pragma_table_info('account');
```

Eleven rows, one for each column of `account`. Read the second row: column number 1 is `product_cd`, of type `VARCHAR(10)`; `notnull` is 1, meaning it may not be left empty; `pk` is 0, meaning it is not part of the primary key. The first row, `account_id`, has `pk` equal to 1.

Notice the double quotes around `"notnull"`. `NOTNULL` is a word with a meaning in SQL (a **reserved word**), so a column that has that name must be quoted to be read as a name. The same goes for `"unique"`, `"table"`, `"from"` and `"to"` below.

A pragma function accepts a column of another table as its argument. That lets you join the list of tables to the columns of each one and describe a whole database in a single query:

```sql-run dataset=shop
SELECT m.name AS table_name, p.name AS column_name, p.type, p."notnull", p.pk
FROM sqlite_master m
JOIN pragma_table_info(m.name) p
WHERE m.type = 'table'
ORDER BY m.name, p.cid
LIMIT 20;
```

For each table `m` in the catalog, `pragma_table_info(m.name)` supplies that table's columns. The result begins with the three columns of `categories`.

All the foreign keys of a database, which amounts to its relationship diagram written as a table:

```sql-run dataset=bank
SELECT m.name AS child_table, fk."from" AS child_column,
       fk."table" AS parent_table, fk."to" AS parent_column
FROM sqlite_master m
JOIN pragma_foreign_key_list(m.name) fk
WHERE m.type = 'table'
ORDER BY parent_table, child_table;
```

Fourteen pointers. The first row says that `txn.account_id` points at `account.account_id`.

## information_schema (MySQL, PostgreSQL, SQL Server)

In `information_schema` each kind of object has a view of its own. On these systems a **schema** is a named collection of tables inside a database server, much like a folder.

| View | Describes |
|---|---|
| `schemata` | the schemas on the server |
| `tables` | tables **and** views; the column `table_type` is `BASE TABLE` or `VIEW` |
| `columns` | the columns of tables and views |
| `views` | views, with their definitions |
| `statistics` (MySQL) | indexes and their columns |
| `table_constraints` | primary key, unique, foreign key and check constraints |
| `key_column_usage` | the columns that make up each key |
| `referential_constraints` | foreign keys and their update and delete rules |

The counterparts of the SQLite queries above:

```sql
-- MySQL (PostgreSQL is the same apart from the schema name, usually 'public')

-- All real tables in the bank schema
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'bank' AND table_type = 'BASE TABLE'
ORDER BY 1;

-- Columns of the account table
SELECT column_name, data_type, character_maximum_length AS char_max_len,
       numeric_precision AS num_prcsn, numeric_scale AS num_scale, is_nullable
FROM information_schema.columns
WHERE table_schema = 'bank' AND table_name = 'account'
ORDER BY ordinal_position;

-- Indexes on account (MySQL only)
SELECT index_name, non_unique, seq_in_index, column_name
FROM information_schema.statistics
WHERE table_schema = 'bank' AND table_name = 'account'
ORDER BY 1, 3;

-- Constraints
SELECT constraint_name, table_name, constraint_type
FROM information_schema.table_constraints
WHERE table_schema = 'bank'
ORDER BY 3, 1;
```

In PostgreSQL, indexes are listed in `pg_indexes`. MySQL's convenience commands `SHOW TABLES`, `DESCRIBE account` and `SHOW CREATE TABLE account`, and PostgreSQL's `\dt` and `\d account`, are shortcuts over the same catalog. These systems also publish metadata about what is happening *now* (table sizes, which indexes are used, running queries, locks) in further catalog views.

## Three things to do with metadata

### 1. Regenerate the scripts that build the database

Teams keep the statements that create their database in files under version control. When those files are lost or out of date, the definitions can be **read back from the catalog**. Statements that define structure (`CREATE TABLE`, `CREATE INDEX` and so on) are called **DDL**, for data definition language. In SQLite the original text is stored, so a complete listing is one query:

```sql-run dataset=shop
SELECT sql || ';' AS ddl
FROM sqlite_master
WHERE sql IS NOT NULL AND type IN ('table', 'index', 'view')
ORDER BY CASE type WHEN 'table' THEN 1 WHEN 'index' THEN 2 ELSE 3 END, name
LIMIT 4;
```

The `CASE` in `ORDER BY` puts tables before indexes and views, because a table must exist before an index on it can be created. (Command-line tools do the same job: `.schema` in the `sqlite3` shell, `pg_dump --schema-only` for PostgreSQL, `mysqldump --no-data` for MySQL.)

Where the original text is not stored, the statement can be *built* from the column metadata:

```sql-run dataset=bank
SELECT 'CREATE TABLE branch_copy (' || char(10)
       || group_concat('  ' || name || ' ' || type
                       || CASE WHEN "notnull" = 1 THEN ' NOT NULL' ELSE '' END
                       || CASE WHEN pk = 1 THEN ' PRIMARY KEY' ELSE '' END, ',' || char(10))
       || char(10) || ');' AS generated_ddl
FROM pragma_table_info('branch');
```

Take it apart from the inside. For each column of `branch`, the expression inside `group_concat` builds a line such as `  name VARCHAR(20) NOT NULL`: two spaces, the column name, its type, and the words `NOT NULL` or `PRIMARY KEY` where the metadata says so. `group_concat` joins those lines with a comma and a line break (`char(10)` is the line-break character). The pieces before and after add the opening `CREATE TABLE branch_copy (` and the closing `);`. The result is a complete, valid statement that would create a copy of the table's structure.

### 2. Check a release

After a release that adds tables, columns and indexes, how do you confirm that the live database matches the one that was tested? Run the same metadata query in both and compare the output. This one returns, per table, the number of columns, indexes, primary-key columns and foreign keys:

```sql-run dataset=bank
SELECT m.name AS tbl_name,
       (SELECT COUNT(*) FROM pragma_table_info(m.name))                AS num_columns,
       (SELECT COUNT(*) FROM pragma_index_list(m.name))                AS num_indexes,
       (SELECT COUNT(*) FROM pragma_table_info(m.name) WHERE pk > 0)   AS num_pk_columns,
       (SELECT COUNT(*) FROM pragma_foreign_key_list(m.name))          AS num_foreign_keys
FROM sqlite_master m
WHERE m.type = 'table'
ORDER BY m.name;
```

`account` has 11 columns, no separate index, one primary-key column and four foreign keys. Save this output before and after a release; any difference that is not in the release notes is a problem. Tools for managing database changes (Alembic, Flyway, Liquibase) automate the idea by recording each applied change in a table of their own.

A related everyday check is the number of rows in every table. The catalog knows the table names, but counting needs a separate query per table. That leads to the third technique.

### 3. Queries that write queries

An SQL statement is a piece of text, so a query can produce one. Building SQL as text and then running it is called **dynamic SQL**. The larger databases can run such text on the server (MySQL: `PREPARE` and `EXECUTE`; Oracle: `EXECUTE IMMEDIATE`; SQL Server: `sp_executesql`). SQLite cannot, so the text is generated in SQL and run from the program that uses the database, which is how it is mostly done in practice anyway.

Generate a row-count query covering every table:

```sql-run dataset=mlops
SELECT group_concat('SELECT ''' || name || ''' AS table_name, COUNT(*) AS row_count FROM ' || name,
                    char(10) || 'UNION ALL ') AS generated_sql
FROM sqlite_master
WHERE type = 'table';
```

For each table name, the inner expression builds the text `SELECT 'runs' AS table_name, COUNT(*) AS row_count FROM runs` (two single quotes in a row stand for one quote inside a string). `group_concat` then joins the six pieces with a line break and the words `UNION ALL`. The single cell of the result is itself a query. Here it is, tidied and pasted into a box of its own:

```sql-run dataset=mlops
SELECT 'experiments' AS table_name, COUNT(*) AS row_count FROM experiments
UNION ALL SELECT 'runs', COUNT(*) FROM runs
UNION ALL SELECT 'metrics', COUNT(*) FROM metrics
UNION ALL SELECT 'models', COUNT(*) FROM models
UNION ALL SELECT 'deployments', COUNT(*) FROM deployments
UNION ALL SELECT 'predictions', COUNT(*) FROM predictions;
```

Six rows: 8 experiments, 86 runs, 940 metrics, and so on. From a program the same job is a short loop:

```python
tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
for t in tables:
    print(t, con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0])
```

> [!WARNING]
> A placeholder (`?`) in a query can stand for a **value**, never for the name of a table or column. So when SQL text is built from names, take the names from the catalog, as above, never from something a user typed, and put them in quotes. SQL text assembled from untrusted input is exactly how **SQL injection** attacks work.

Generated SQL powers a great deal of data tooling. One more example: a check for missing values in every column of a table.

```sql-run dataset=shop
-- Generate a NULL-count check for every column of customers
SELECT 'SELECT ''' || name || ''' AS col, COUNT(*) - COUNT(' || name || ') AS nulls FROM customers' AS check_sql
FROM pragma_table_info('customers');
```

Eight rows, each a ready-made query. `COUNT(*) - COUNT(column)` is the number of rows minus the number of non-NULL values, which is the number of NULLs.

## Metadata beyond one database

The same idea scales up. Analytics databases publish table sizes and query history in their own `INFORMATION_SCHEMA`. A **data catalog** is a metadata database describing datasets across a whole company. And a machine-learning experiment tracker, like the `mlops` dataset in this guide, is metadata about models: which training run produced which version, with which settings, deployed where. Tracing where something came from is called **lineage**, and a lineage question is a metadata query:

```sql-run dataset=mlops
-- Lineage of the current production models: model <- run <- experiment
SELECT m.name, m.version, r.run_name, r.model_type, r.learning_rate, e.name AS experiment, e.owner
FROM models m
JOIN runs r        ON r.run_id = m.run_id
JOIN experiments e ON e.experiment_id = r.experiment_id
WHERE m.stage = 'Production';
```

Version 9 of `churn-model` came from the run `lightgbm-09` of the experiment `churn-gbm`, owned by priya.

## Worked example: a data dictionary generated from the catalog

Documentation typed by hand goes out of date. Documentation that is *queried* cannot. This query produces a compact description of the `mlops` database: table, column, type, and the part each column plays.

```sql-run dataset=mlops
SELECT m.name AS table_name,
       p.name AS column_name,
       p.type AS declared_type,
       CASE WHEN p.pk > 0 THEN 'PK' ELSE '' END
         || CASE WHEN fk."from" IS NOT NULL THEN ' FK -> ' || fk."table" || '.' || fk."to" ELSE '' END
         || CASE WHEN p."notnull" = 1 THEN ' NOT NULL' ELSE '' END AS role
FROM sqlite_master m
JOIN pragma_table_info(m.name) p
LEFT JOIN pragma_foreign_key_list(m.name) fk ON fk."from" = p.name
WHERE m.type = 'table'
ORDER BY m.name, p.cid
LIMIT 24;
```

Three sources are combined with ordinary joins: the list of tables, each table's columns, and the targets of its foreign keys. The last is a `LEFT JOIN`, because most columns are not foreign keys and must be kept anyway. The `role` column is assembled from three small `CASE` expressions. For `deployments.model_id` it reads `FK -> models.model_id NOT NULL`.

Nothing in the query names a particular table. Point it at another SQLite database and it documents that database. The principle to keep: **the structure of a database is itself data, so describe it with a query.**

> [!INTERVIEW]
> Metadata questions are practical. "How would you find all tables containing a column named `customer_id`?" (`SELECT table_name FROM information_schema.columns WHERE column_name = 'customer_id'`.) "How do you list the indexes on a table?" "How do you find tables without a primary key?" What is being tested is whether you know the catalog can be queried, and roughly where to look.

## Pitfalls

- **Catalog queries do not carry over** between SQLite and the `information_schema` databases. Keep them in one place in your code.
- **An `INTEGER PRIMARY KEY` shows `notnull = 0`** in SQLite's `pragma_table_info`, although it can never be NULL.
- **Reserved-word column names** (`"notnull"`, `"unique"`, `"table"`, `"from"`) must be quoted when selected from pragma functions.
- **Generated SQL built from unquoted or untrusted names**: injection, and breakage on unusual names.
- **Row counts taken from the catalog are estimates** on some systems (`information_schema.tables.table_rows` in MySQL). Use `COUNT(*)` when you need the true figure.

## Summary

- Metadata describes tables, columns, constraints, indexes and views, and lives in a catalog that can be queried.
- SQLite: `sqlite_master` (or `sqlite_schema`) plus `pragma_table_info`, `pragma_index_list` and `pragma_foreign_key_list`.
- MySQL, PostgreSQL, SQL Server: the standard `information_schema` views (`tables`, `columns`, `table_constraints`, `key_column_usage` and others) and each product's own catalog.
- Practical uses: regenerating creation scripts, checking releases, profiling data, and generating SQL, with names taken from the catalog and never from users.

## Glossary

- **Metadata** — data that describes other data; here, the structure of a database.
- **Data dictionary (system catalog)** — the place where a database stores its metadata, as tables and views.
- **Object** — anything made with a `CREATE` statement: a table, index, view or trigger.
- **`sqlite_master` / `sqlite_schema`** — SQLite's catalog table, one row per object.
- **`PRAGMA`** — an SQLite-specific command for settings and internal information.
- **Pragma function** — a `pragma_...()` function that returns catalog information as a table.
- **`information_schema`** — the standard set of catalog views in MySQL, PostgreSQL and SQL Server.
- **Schema** — a named collection of tables in a database server; also, loosely, the structure of a database.
- **Reserved word** — a word with a fixed meaning in SQL, which must be quoted to be used as a name.
- **DDL (data definition language)** — statements that define structure, such as `CREATE TABLE`.
- **Dynamic SQL** — SQL text that is built by a program or a query and then run.
- **SQL injection** — an attack in which untrusted text becomes part of an SQL statement.
- **Data profile** — summary facts about data, such as row counts and the number of NULLs per column.
- **Data catalog** — a metadata system describing datasets across many databases.
- **Lineage** — the record of where a piece of data or a model came from.

```quiz
[
  {"q": "What is metadata in a database?", "options": ["Backup copies of data", "Data describing the database's objects: tables, columns, constraints, indexes", "Encrypted user data", "Temporary query results"], "answer": 1, "explain": "The data dictionary records the structure of the database itself."},
  {"q": "Where does SQLite keep its catalog?", "options": ["information_schema.tables", "sqlite_master (sqlite_schema)", "pg_catalog", "sys.tables"], "answer": 1, "explain": "One table holding the type, name, owning table and CREATE statement text of every object."},
  {"q": "Which information_schema view lists a table's columns and data types?", "options": ["tables", "columns", "statistics", "schemata"], "answer": 1, "explain": "information_schema.columns has one row per column, with its position, data type and whether it may be NULL."},
  {"q": "In information_schema.tables, how are views distinguished from tables?", "options": ["They are not listed", "table_type is 'VIEW' instead of 'BASE TABLE'", "Their names start with v_", "By the engine column"], "answer": 1, "explain": "Both appear in the tables view; table_type tells them apart."},
  {"q": "Why is comparing the output of a metadata query useful after a release?", "options": ["It speeds up the database", "It confirms that the expected tables, columns, indexes and constraints exist in the live database", "It refreshes statistics", "It rebuilds indexes"], "answer": 1, "explain": "A difference between the tested and the live database reveals a change that was missed or failed."},
  {"q": "Why can't a table name be supplied as a placeholder (?) in a prepared statement?", "options": ["It can", "Placeholders stand for values only; names must be part of the SQL text", "Table names are case-sensitive", "Only integers can be supplied"], "answer": 1, "explain": "So generated SQL must take names from a trusted source such as the catalog."},
  {"q": "Which SQLite function returns the foreign keys of a table?", "options": ["pragma_table_info", "pragma_index_list", "pragma_foreign_key_list", "sqlite_fk()"], "answer": 2, "explain": "It returns the parent table and the from and to columns, with the update and delete actions."},
  {"q": "What does COUNT(*) - COUNT(email) compute for a table?", "options": ["The number of different emails", "The number of rows where email is NULL", "Always zero", "The number of duplicate emails"], "answer": 1, "explain": "COUNT(*) counts all rows and COUNT(email) only the non-NULL ones, so the difference is the number of NULLs."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 15 "Metadata" (data about data, information_schema, working with metadata: schema generation scripts, deployment verification, dynamic SQL generation), restated in original wording with this guide's own datasets. SQLite documentation, "The Schema Table" and "PRAGMA Statements".
