# Three or more tables, self joins and non-equi joins

Two-table joins are the building block; real queries chain several of them. This lesson covers joining three or more tables, using subqueries as tables inside a join, using the *same* table more than once, joining a table to *itself*, and joins whose condition is not a simple equality.

## Joining three or more tables

A three-table join has three tables in FROM, two join types and two ON clauses. The book's example lists each business account with the teller who opened it:

```sql-run dataset=bank
SELECT a.account_id, c.fed_id, e.fname, e.lname
FROM account a
JOIN customer c ON a.cust_id = c.cust_id
JOIN employee e ON a.open_emp_id = e.emp_id
WHERE c.cust_type_cd = 'B';
```

Think of it as a snowball: `account` joined to `customer` produces an intermediate result; that result is then joined to `employee`. Each `ON` clause may refer to any table already mentioned.

### Does the order matter?

Rearrange the tables and the result is the same:

```sql-run dataset=bank
SELECT a.account_id, c.fed_id, e.fname, e.lname
FROM employee e
JOIN account a  ON a.open_emp_id = e.emp_id
JOIN customer c ON a.cust_id = c.cust_id
WHERE c.cust_type_cd = 'B';
```

The server picks a **driving table** and a join order using statistics; your FROM clause is a description, not a recipe. The only thing the written order must respect is that an `ON` clause can only mention tables that have already appeared.

### Walking a chain of foreign keys

Many questions are just a walk along the schema's foreign keys. *Total value of delivered orders per top-level product, with the customer's country* touches four tables:

```sql-run dataset=shop
SELECT c.country,
       cat.name AS category,
       ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)), 2) AS revenue
FROM customers c
JOIN orders o       ON o.customer_id = c.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
JOIN products p     ON p.product_id = oi.product_id
JOIN categories cat ON cat.category_id = p.category_id
WHERE o.status = 'delivered'
GROUP BY c.country, cat.name
ORDER BY revenue DESC
LIMIT 10;
```

Before writing such a query, sketch the path on the ER diagram: customers → orders → order_items → products → categories. One `JOIN ... ON` per arrow.

## Using subqueries as tables

A join partner need not be a stored table. The book rewrites the earlier query so that the employee and branch filters are pushed into subqueries: find accounts opened by *experienced tellers* currently assigned to the *Woburn* branch.

```sql-run dataset=bank
SELECT a.account_id, a.cust_id, a.open_date, a.product_cd
FROM account a
JOIN (SELECT emp_id, assigned_branch_id
      FROM employee
      WHERE start_date < '2021-06-01'
        AND title IN ('Teller', 'Head Teller')) e
  ON a.open_emp_id = e.emp_id
JOIN (SELECT branch_id
      FROM branch
      WHERE name = 'Woburn Branch') b
  ON e.assigned_branch_id = b.branch_id;
```

Each subquery produces a small derived table (`e` holds experienced tellers, `b` holds one branch) and the outer query joins them. There is no WHERE clause in the outer query; all filtering has moved inside the derived tables. Whether this is *faster* than the flat version depends on the optimizer — most will produce the same plan — but it is a powerful way to **structure** a query: build small, obviously-correct pieces and join them.

The most important use of this technique is **pre-aggregation**, which solves the fan-out problem from the last lesson. To get each order's item total *and* keep `shipping_fee` unduplicated, aggregate the items first, then join:

```sql-run dataset=shop
SELECT o.order_id, o.shipping_fee, t.items, t.subtotal,
       ROUND(t.subtotal + o.shipping_fee, 2) AS total
FROM orders o
JOIN (SELECT order_id,
             SUM(quantity) AS items,
             ROUND(SUM(quantity * unit_price * (1 - discount)), 2) AS subtotal
      FROM order_items
      GROUP BY order_id) t ON t.order_id = o.order_id
ORDER BY total DESC
LIMIT 8;
```

The derived table `t` has one row per order, so the join is one-to-one and nothing is double counted.

## Using the same table twice

Sometimes a table plays two different roles in one query. An account has an *opening branch*; the employee who opened it has an *assigned branch*. To show both names, join `branch` twice with different aliases:

```sql-run dataset=bank
SELECT a.account_id,
       e.emp_id,
       b_a.name AS open_branch,
       b_e.name AS emp_branch
FROM account a
JOIN branch b_a   ON a.open_branch_id = b_a.branch_id
JOIN employee e   ON a.open_emp_id = e.emp_id
JOIN branch b_e   ON e.assigned_branch_id = b_e.branch_id
WHERE a.product_cd = 'CHK'
LIMIT 10;
```

Aliases are mandatory here: without them the server could not tell which `branch` you mean in each ON clause. Give role-based aliases (`b_a` for the account's branch, `b_e` for the employee's) rather than `b1`, `b2`.

## Self joins

A table can also be joined **to itself**. This is natural whenever a table has a **self-referencing foreign key** — a column pointing at the same table's primary key. `employee.superior_emp_id` points at the manager's `emp_id`:

```sql-run dataset=bank
SELECT e.fname || ' ' || e.lname AS employee,
       e.title,
       mgr.fname || ' ' || mgr.lname AS manager
FROM employee e
JOIN employee mgr ON e.superior_emp_id = mgr.emp_id
ORDER BY mgr.emp_id, e.emp_id;
```

Read the two aliases as two different tables: `e` is "the employee", `mgr` is "their manager". Notice the result has 21 rows, not 22: the president has no superior (`superior_emp_id` is NULL), so the inner join drops him. An outer join keeps him; that is the *Joins revisited* module.

Other self-referencing structures in our datasets: `categories.parent_id`, `customers.referred_by`, `runs.parent_run_id`.

```sql-run dataset=shop
SELECT child.name AS category, parent.name AS parent_category
FROM categories child
JOIN categories parent ON child.parent_id = parent.category_id
ORDER BY parent.name, child.name;
```

A self join climbs exactly **one level**. Walking a hierarchy of unknown depth needs a recursive CTE (see the CTE module).

Self joins don't require a self-referencing key. Any time you compare rows of a table with other rows of the same table — pairs of employees in the same branch, a customer's consecutive orders — you are self-joining.

## Equi-joins versus non-equi-joins

All joins so far were **equi-joins**: the condition was an equality. A **non-equi-join** uses ranges or inequalities.

### Range joins

Which products were on offer when each account was opened? The condition is "open date between the product's offer and retirement dates" — and here there is no foreign key involved at all:

```sql-run dataset=bank
SELECT e.emp_id, e.fname, e.lname, e.start_date, p.name AS product_offered
FROM employee e
JOIN product p
  ON e.start_date >= p.date_offered
 AND (p.date_retired IS NULL OR e.start_date <= p.date_retired)
WHERE p.product_type_cd = 'INSURANCE';
```

Range joins appear constantly in analytics: matching an event to the price list in force at the time, a transaction to its fiscal period, a prediction to the model deployment that was live when it was made:

```sql-run dataset=mlops
SELECT d.deployment_id, m.name, m.version, d.deployed_at, d.retired_at
FROM deployments d
JOIN models m ON m.model_id = d.model_id
WHERE d.environment = 'production'
  AND d.deployed_at <= '2024-03-02 12:00:00'
  AND (d.retired_at IS NULL OR d.retired_at > '2024-03-02 12:00:00');
```

That is a **point-in-time** lookup: which production deployments were live at noon on 2 March.

### Self non-equi-joins: generating pairs

The book's chess-tournament example: pair every teller with every other teller. A first attempt with `e1.emp_id <> e2.emp_id` produces each pairing twice (A–B and B–A). Using `<` keeps exactly one of each:

```sql-run dataset=bank
SELECT e1.fname || ' ' || e1.lname AS player_1,
       'VS' AS vs,
       e2.fname || ' ' || e2.lname AS player_2
FROM employee e1
JOIN employee e2 ON e1.emp_id < e2.emp_id
WHERE e1.title = 'Head Teller' AND e2.title = 'Head Teller';
```

Four head tellers give 4 × 3 / 2 = 6 matches. The `a.id < b.id` trick is the standard way to list unordered pairs — and to find duplicates (`a.email = b.email AND a.id < b.id`).

> [!WARNING]
> Non-equi-joins can be expensive. Hash and merge joins need an equality; a pure range condition often forces a nested loop over every pair of rows. On big tables add an equality where you can (same customer, same day bucket), or use window functions instead of self joins.

## Join conditions versus filter conditions, revisited

With several tables and subqueries, it is tempting to scatter conditions anywhere. Keep the discipline from the last lesson:

- **ON**: how this table relates to the tables already joined.
- **WHERE**: which rows of the final combination you want.

For inner joins the placement doesn't change the result, but it changes how quickly a reader can verify the query — and for outer joins it will change the result.

## Pitfalls

- **Forgetting an ON clause** in a five-table join multiplies rows silently (SQLite/MySQL). Count your joins: *n* tables need *n − 1* conditions.
- **Reusing an alias** or not using aliases when a table appears twice.
- **Symmetric duplicates** in pair generation — use `<`, not `<>`.
- **Self join for deep hierarchies** — only one level per join.
- **Joining an aggregated and a non-aggregated grain** without pre-aggregation.

## Summary

- Multi-table joins chain two-table joins; written order doesn't dictate execution order.
- Derived tables (subqueries in FROM) can be join partners; pre-aggregate in them to avoid fan-out.
- A table may appear several times under different aliases to play different roles.
- **Self joins** relate rows of one table to other rows of the same table, typically through a self-referencing foreign key.
- **Non-equi-joins** use ranges or inequalities: point-in-time lookups, pair generation.

```quiz
[
  {"q": "How many ON conditions does a join of five tables need at minimum to avoid a Cartesian product?", "options": ["3", "4", "5", "10"], "answer": 1, "explain": "n tables need n-1 join conditions to connect them all."},
  {"q": "Why does the employee-manager self join return 21 rows from 22 employees?", "options": ["A duplicate is removed", "The president has a NULL superior and the inner join drops him", "One employee left the bank", "LIMIT 21 is implied"], "answer": 1, "explain": "No manager row matches NULL, so the president's row vanishes."},
  {"q": "Which condition lists each unordered pair of employees exactly once?", "options": ["e1.emp_id = e2.emp_id", "e1.emp_id <> e2.emp_id", "e1.emp_id < e2.emp_id", "No condition"], "answer": 2, "explain": "< keeps one of (A,B)/(B,A) and excludes (A,A)."},
  {"q": "What is the main reason to join orders to a pre-aggregated subquery of order_items?", "options": ["It is required by SQLite", "To keep one row per order and avoid double-counting order-level columns", "Subqueries are always faster", "To avoid aliases"], "answer": 1, "explain": "Pre-aggregating restores a one-to-one grain."},
  {"q": "Joining branch twice in one query requires...", "options": ["A view", "Two different table aliases", "A UNION", "A temporary table"], "answer": 1, "explain": "Each role needs its own alias so columns can be told apart."},
  {"q": "A join with the condition e.start_date BETWEEN p.date_offered AND p.date_retired is a...", "options": ["Equi-join", "Non-equi-join", "Natural join", "Cross join"], "answer": 1, "explain": "The condition is a range, not an equality."}
]
```

> **Source:** Beaulieu, *Learning SQL*, ch. 5 "Querying Multiple Tables" (joining three or more tables, using subqueries as tables, using the same table twice, self-joins, equi-joins versus non-equi-joins).
