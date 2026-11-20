# Metadata and the data dictionary

When you create a table, the database has to remember more than its name: its columns and their types, default values, constraints, indexes, which user owns it, where it is stored. All of this is **metadata** — *data about data* — and the place it lives is the **data dictionary** or **system catalog**. Because relational databases store everything in tables, the catalog is itself a set of tables and views that you can query with ordinary SQL. This lesson shows how to read metadata in SQLite, MySQL and PostgreSQL, and what you can build with it: schema documentation, deployment verification, and SQL that writes SQL.

## Data about data

The book lists what the server records for a table:

- the table's name, storage information (tablespace, initial size, storage engine);
- column names, data types, default values and NOT NULL constraints;
- primary key columns, the primary key's name and its index;
- foreign key names, their columns and the tables they reference;
- index names, types (B-tree, bitmap…), columns, sort order and uniqueness.

Every tool that draws an ER diagram, autocompletes a column name or generates an ORM model gets its information from here. Each vendor exposes the catalog differently:

| Database | How metadata is published |
|---|---|
| Oracle | views such as `user_tables`, `all_constraints`, `dba_indexes` |
| SQL Server | `sys.*` catalog views, system stored procedures, and `INFORMATION_SCHEMA` |
| MySQL | the `information_schema` database, plus `SHOW` commands |
| PostgreSQL | `pg_catalog.*` tables and the standard `information_schema` |
| SQLite | the `sqlite_schema` table (alias `sqlite_master`) and `PRAGMA` functions |

`information_schema` is defined by the SQL standard, which is why the book builds its chapter around it: the queries are largely portable between MySQL, PostgreSQL and SQL Server. SQLite does not implement it, so this lesson shows both.

## SQLite: sqlite_schema and pragmas

Everything SQLite knows about a database's objects is in one small table:

```sql-run dataset=bank
SELECT type, name, tbl_name
FROM sqlite_master
ORDER BY type, name;
```

Its columns are `type` (`table`, `index`, `view`, `trigger`), `name`, `tbl_name` (the table an index or trigger belongs to), `rootpage` (where its B-tree starts in the file) and `sql` — the original `CREATE` statement text:

```sql-run dataset=bank
SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'employee';
```

SQLite does not parse that text into rows for you; instead it provides **pragma functions**, which can be used as tables:

| Pragma function | Returns |
|---|---|
| `pragma_table_info('t')` | columns: `cid, name, type, notnull, dflt_value, pk` |
| `pragma_table_xinfo('t')` | the same plus hidden/generated columns |
| `pragma_index_list('t')` | indexes on the table: `name, unique, origin, partial` |
| `pragma_index_info('idx')` | columns of an index, in order |
| `pragma_foreign_key_list('t')` | foreign keys: `table, from, to, on_update, on_delete` |
| `pragma_table_list` | all tables and views (3.37+) |

```sql-run dataset=bank
SELECT cid, name, type, "notnull", dflt_value, pk
FROM pragma_table_info('account');
```

Because a pragma function accepts a column from another table as its argument, you can join the list of tables to their columns and build a catalog-wide report in one query:

```sql-run dataset=shop
SELECT m.name AS table_name, p.name AS column_name, p.type, p."notnull", p.pk
FROM sqlite_master m
JOIN pragma_table_info(m.name) p
WHERE m.type = 'table'
ORDER BY m.name, p.cid
LIMIT 20;
```

Foreign keys across the whole schema — effectively the ER diagram as a table:

```sql-run dataset=bank
SELECT m.name AS child_table, fk."from" AS child_column,
       fk."table" AS parent_table, fk."to" AS parent_column
FROM sqlite_master m
JOIN pragma_foreign_key_list(m.name) fk
WHERE m.type = 'table'
ORDER BY parent_table, child_table;
```

## information_schema (MySQL, PostgreSQL, SQL Server)

In `information_schema` each kind of object has a view. The book explores these:

| View | Describes |
|---|---|
| `schemata` | databases/schemas |
| `tables` | tables **and** views (`table_type` = `BASE TABLE` or `VIEW`) |
| `columns` | columns of tables and views |
| `views` | views, including `view_definition` and `is_updatable` |
| `statistics` (MySQL) | indexes and their columns |
| `table_constraints` | primary key, unique, foreign key, check constraints |
| `key_column_usage` | the columns that make up each key constraint |
| `referential_constraints` | foreign keys and their update/delete rules |

The equivalents of the SQLite queries above:

```sql
-- All base tables in the bank schema (MySQL)
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

-- Indexes on account (MySQL)
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

In PostgreSQL the schema is usually `public`, and indexes are found in `pg_indexes`. MySQL's convenience commands `SHOW TABLES`, `DESCRIBE account` and `SHOW CREATE TABLE account` (and psql's `\dt`, `\d account`) are shortcuts over the same catalog. Beyond structure, MySQL and PostgreSQL also expose *runtime* metadata — table sizes, index usage statistics, running queries, locks — through `information_schema`, `performance_schema`, `pg_stat_*` views.

## Working with metadata

Why would you query the catalog yourself, when tools already show it? The book gives three scenarios.

### Schema generation scripts

Teams keep the scripts that build the database under version control, but when the scripts are missing or out of date, you can **regenerate DDL from the catalog**. The book assembles a `CREATE TABLE` statement for `customer` by selecting from `information_schema.columns` and concatenating the pieces. In SQLite the original text is stored, so a complete schema dump is one query:

```sql-run dataset=shop
SELECT sql || ';' AS ddl
FROM sqlite_master
WHERE sql IS NOT NULL AND type IN ('table', 'index', 'view')
ORDER BY CASE type WHEN 'table' THEN 1 WHEN 'index' THEN 2 ELSE 3 END, name
LIMIT 4;
```

(The `.schema` command of the `sqlite3` shell does exactly this; `pg_dump --schema-only` and `mysqldump --no-data` are the server equivalents.) To *build* DDL from column metadata, as the book does:

```sql-run dataset=bank
SELECT 'CREATE TABLE branch_copy (' || char(10)
       || group_concat('  ' || name || ' ' || type
                       || CASE WHEN "notnull" = 1 THEN ' NOT NULL' ELSE '' END
                       || CASE WHEN pk = 1 THEN ' PRIMARY KEY' ELSE '' END, ',' || char(10))
       || char(10) || ');' AS generated_ddl
FROM pragma_table_info('branch');
```

### Deployment verification

After a release that adds tables, columns and indexes, how do you confirm that the production schema matches what was tested? Run a metadata query in both environments and compare. The book's verification query returns, per table, the number of columns, indexes and primary keys:

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

Save the output before and after a deployment; any difference that isn't in the release notes is a problem. Migration tools (Alembic, Flyway, Liquibase) automate this idea by recording applied migrations in a metadata table of their own.

A related everyday check is a **data profile** — row counts for every table. The catalog knows the table names but counting needs a query per table, which leads to the third technique.

### Dynamic SQL generation

Because SQL statements are just strings, a query can produce SQL. Most languages then let you submit that string for execution; the book demonstrates MySQL's `PREPARE` / `EXECUTE` / `DEALLOCATE PREPARE` statements (Oracle: `EXECUTE IMMEDIATE`, SQL Server: `sp_executesql`, PostgreSQL: `EXECUTE` inside PL/pgSQL). SQLite has no server-side dynamic SQL, so you generate the text in SQL and run it from the host language — which is how it is done in practice anyway.

Generate a row-count query for every table:

```sql-run dataset=mlops
SELECT group_concat('SELECT ''' || name || ''' AS table_name, COUNT(*) AS row_count FROM ' || name,
                    char(10) || 'UNION ALL ') AS generated_sql
FROM sqlite_master
WHERE type = 'table';
```

Copy the generated statement into the next box (it is already pasted) and run it:

```sql-run dataset=mlops
SELECT 'experiments' AS table_name, COUNT(*) AS row_count FROM experiments
UNION ALL SELECT 'runs', COUNT(*) FROM runs
UNION ALL SELECT 'metrics', COUNT(*) FROM metrics
UNION ALL SELECT 'models', COUNT(*) FROM models
UNION ALL SELECT 'deployments', COUNT(*) FROM deployments
UNION ALL SELECT 'predictions', COUNT(*) FROM predictions;
```

From Python the loop is three lines:

```python
tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
for t in tables:
    print(t, con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0])
```

> [!WARNING]
> **Identifiers cannot be bound as parameters** — only values can. When you build SQL text from names, take the names from the catalog (as above), never from user input, and quote them. String-built SQL fed by untrusted input is the definition of **SQL injection**.

Dynamic SQL from metadata powers a great deal of data tooling: generating a NULL-rate check for every column, a `SELECT` with columns pivoted from data, GRANT statements for every table in a schema, or a nightly statistics refresh.

```sql-run dataset=shop
-- Generate a NULL-count check for every column of customers
SELECT 'SELECT ''' || name || ''' AS col, COUNT(*) - COUNT(' || name || ') AS nulls FROM customers' AS check_sql
FROM pragma_table_info('customers');
```

## Metadata in data and ML platforms

The same idea scales up. Data warehouses expose `INFORMATION_SCHEMA` with table sizes, query history and access logs. **Data catalogs** (Hive Metastore, AWS Glue, Unity Catalog, DataHub) are metadata databases describing datasets across systems. And an ML **experiment tracker / model registry** — the `mlops` dataset in this guide — is metadata about models: which run produced which version, with what parameters and metrics, deployed where. Lineage questions are metadata queries:

```sql-run dataset=mlops
-- Lineage of the current production models: model <- run <- experiment
SELECT m.name, m.version, r.run_name, r.model_type, r.learning_rate, e.name AS experiment, e.owner
FROM models m
JOIN runs r        ON r.run_id = m.run_id
JOIN experiments e ON e.experiment_id = r.experiment_id
WHERE m.stage = 'Production';
```

## Pitfalls

- **Catalog queries are not portable** between SQLite and `information_schema` databases; isolate them.
- **`INTEGER PRIMARY KEY` shows `notnull = 0`** in SQLite's table_info although it can never be NULL.
- **Quoted reserved-word columns** (`"notnull"`, `"unique"`, `"table"`, `"from"`) must be quoted when selected from pragma functions.
- **Generated SQL with unquoted or untrusted names** — injection and breakage on odd names.
- **Stale statistics** in catalog row-count estimates (`information_schema.tables.table_rows` is approximate for InnoDB) — use `COUNT(*)` when you need the truth.

## Worked example: a data dictionary generated from the catalog

Documentation that is typed by hand goes stale; documentation that is *queried* cannot. Generate a compact data dictionary for the `mlops` schema straight from metadata — table, column, type, and the role each column plays.

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

Three catalog sources combined with ordinary joins: the list of tables, each table's columns, and — through a LEFT JOIN, since most columns are not foreign keys — the foreign-key targets. The same query pointed at a different database documents that database; nothing is hard-coded.

The equivalent in an `information_schema` database joins `columns` to `key_column_usage` and `referential_constraints`. The idea is identical: **the schema is data, so describe it with a query.**

> [!INTERVIEW]
> Metadata questions are usually practical: "How would you find all tables containing a column named `customer_id`?" (`information_schema.columns WHERE column_name = 'customer_id'`), "How do you list the indexes on a table?", "How do you find tables without a primary key?" Knowing that the catalog is queryable — and roughly which view to look in — is what is being tested.

## Summary

- Metadata describes tables, columns, constraints, indexes and views, and lives in a queryable catalog.
- SQLite: `sqlite_master` / `sqlite_schema` plus `pragma_table_info`, `pragma_index_list`, `pragma_foreign_key_list`.
- MySQL / PostgreSQL / SQL Server: the standard `information_schema` views (`tables`, `columns`, `table_constraints`, `key_column_usage`, …) and vendor catalogs.
- Practical uses: generating schema scripts, verifying deployments, profiling data, and generating dynamic SQL — with identifiers taken from the catalog, not from users.

```quiz
[
  {"q": "What is metadata in a database?", "options": ["Backup copies of data", "Data describing the database's objects: tables, columns, constraints, indexes", "Encrypted user data", "Temporary query results"], "answer": 1, "explain": "The data dictionary records the structure of the database itself."},
  {"q": "Where does SQLite keep its catalog?", "options": ["information_schema.tables", "sqlite_master (sqlite_schema)", "pg_catalog", "sys.tables"], "answer": 1, "explain": "One table with type, name, tbl_name, rootpage and the CREATE statement text."},
  {"q": "Which information_schema view lists a table's columns and data types?", "options": ["tables", "columns", "statistics", "schemata"], "answer": 1, "explain": "information_schema.columns has one row per column, with ordinal_position, data_type, is_nullable, etc."},
  {"q": "In information_schema.tables, how are views distinguished from tables?", "options": ["They are not listed", "table_type = 'VIEW' versus 'BASE TABLE'", "Their names start with v_", "By the engine column"], "answer": 1, "explain": "Both appear in tables; table_type tells them apart."},
  {"q": "Why is comparing metadata query output useful after a deployment?", "options": ["It speeds up the database", "It verifies that the expected tables, columns, indexes and constraints exist in the target environment", "It refreshes statistics", "It rebuilds indexes"], "answer": 1, "explain": "Differences between environments reveal missed or failed schema changes."},
  {"q": "Why can't table names be supplied as bound parameters in a prepared statement?", "options": ["They can", "Parameters stand for values only; identifiers must be part of the SQL text", "Table names are case-sensitive", "Only integers can be bound"], "answer": 1, "explain": "So dynamic SQL must take identifiers from a trusted source such as the catalog."},
  {"q": "Which SQLite function returns the foreign keys of a table?", "options": ["pragma_table_info", "pragma_index_list", "pragma_foreign_key_list", "sqlite_fk()"], "answer": 2, "explain": "It returns the parent table and the from/to columns with their update/delete actions."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 15 "Metadata" (data about data, information_schema, working with metadata: schema generation scripts, deployment verification, dynamic SQL generation). SQLite documentation, "The Schema Table" and "PRAGMA Statements".
