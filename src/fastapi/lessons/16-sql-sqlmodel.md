# SQL with SQLAlchemy and SQLModel

> **Before this lesson:** you should know the session-per-request dependency written with `yield`
> ([lesson 11](#/lesson/fastapi/yield-deps)), model families such as Create / Public / Update
> ([lesson 5](#/lesson/fastapi/body-responses)) and the data layer's place in a project
> ([lesson 15](#/lesson/fastapi/layers)). No database experience is assumed: tables, SQL and
> transactions are introduced from the beginning.

## In plain words

A web server forgets everything when it restarts. Anything that must outlive a restart (users,
orders, messages) has to be kept in a **database**: a separate program whose whole job is to store
data safely and find it again quickly.

The most common kind is the **relational database**. Its data is organised in **tables**, which you
can picture as spreadsheets. Each **row** is one record (one user) and each **column** is one
property (the user's email). Programs talk to such a database in a language called **SQL**
(Structured Query Language, often pronounced "sequel").

An everyday picture: a library's card catalogue with a professional librarian. You do not rummage
through the drawers yourself. You hand the librarian a precisely worded slip ("all cards where the
author is Austen, sorted by year") and get the matching cards back. The slip is a SQL query, the
librarian is the database, and the catalogue's own rules (no two books with the same shelf mark) are
enforced by the librarian whoever asks.

Most APIs are, underneath, a careful interface to such a database. FastAPI itself does not care
which database or library you use. This lesson climbs the ladder of tools the way Lubanovic does,
from raw SQL to a library that maps tables to Python classes, and then concentrates on the pattern
you must get right in a web application: **one database session for each request**.

Why this matters for a job: nearly every backend role involves a database. "How do you manage
sessions in FastAPI?", "what is the N+1 problem?" and "how do you prevent SQL injection?" are
standard interview questions, and all three are answered below.

## Five words of database vocabulary

- A **primary key** is the column whose value identifies each row uniquely, usually `id`.
- A **foreign key** is a column that holds the primary key of a row in another table. An order's
  `user_id` says which user the order belongs to. This is how tables are related.
- A **constraint** is a rule the database enforces on every write, such as "emails are unique" or
  "balance is never negative".
- A **query** is a request for data. The four basic SQL statements are `SELECT` (read), `INSERT`
  (add), `UPDATE` (change) and `DELETE` (remove), which are the CRUD operations of lesson 2.
- A **driver** is the Python library that knows how to talk to one particular database product over
  its network protocol.

## The abstraction ladder

There are several levels at which Python code can work with a database. Each level hides more of
the SQL:

| Level | What you write | Example |
|---|---|---|
| DB-API driver | SQL strings + cursors | `sqlite3`, `psycopg` |
| SQLAlchemy **Core** | SQL built from Python expressions | `select(users).where(users.c.id == 1)` |
| SQLAlchemy **ORM** | classes mapped to tables, a `Session` tracking objects | `session.get(User, 1)` |
| **SQLModel** | one class that is both a Pydantic model and a SQLAlchemy table | `class Hero(SQLModel, table=True)` |

The book's data-layer chapter deliberately begins at the bottom, with the `sqlite3` module from the
standard library. SQLite is a small database that lives in a single file (or in memory) and needs no
server. The interface it follows, Python's **DB-API** (defined in PEP 249), is what every higher
tool is built on, and it has only a handful of steps: `connect()` gives a connection;
`conn.cursor()` gives a cursor; `cursor.execute(sql, params)` runs a statement; `fetchone()` or
`fetchall()` reads results; `commit()` saves.

```python-run
import sqlite3

conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
curs = conn.cursor()
curs.execute("create table creature(name text primary key, country text, area text)")

# Parameters are passed SEPARATELY from the SQL text (named style) - never format them into the string.
rows = [{"name": "yeti", "country": "CN", "area": "Himalayas"},
        {"name": "bigfoot", "country": "US", "area": "*"}]
curs.executemany("insert into creature values(:name, :country, :area)", rows)
conn.commit()

curs.execute("select * from creature where country = :c", {"c": "US"})
print([dict(r) for r in curs.fetchall()])

# Why parameters matter: a classic injection string is treated as plain data.
evil = "x' OR '1'='1"
curs.execute("select count(*) from creature where name = :n", {"n": evil})
print("safe, parameterised:", curs.fetchone()[0])
curs.execute(f"select count(*) from creature where name = '{evil}'")       # NEVER do this
print("string formatting  :", curs.fetchone()[0], "<- injection matched every row")

try:
    curs.execute("insert into creature values('yeti', 'XX', '')")
except sqlite3.IntegrityError as e:
    print("IntegrityError:", e)          # the data layer turns this into a Duplicate exception
```

Step by step:

- `sqlite3.connect(":memory:")` opens a database that exists only in memory. Setting `row_factory`
  makes rows behave like dictionaries.
- `create table creature(...)` makes a table with three text columns; `name` is the primary key.
- `executemany` runs one `insert` statement for each dictionary in `rows`. In the SQL, `:name`,
  `:country` and `:area` are **placeholders**; the values travel separately.
- `conn.commit()` makes the inserts permanent.
- The `select` asks for creatures whose country is `US`; the printed result is the bigfoot row.

The next four lines are the most important in the lesson. `evil` is the kind of text an attacker
types into a form. Passed as a parameter, it is treated as a plain (and odd) name, and the count is
`0`. Pasted into the SQL text with an f-string, the quote characters inside it end the intended
value and add `OR '1'='1'`, a condition that is always true, so the count is `2`: every row matched.
This is **SQL injection**. With a `delete` in place of a `select`, the attacker would have emptied
the table. The defence is always the same: never build SQL by inserting values into the text; pass
them as parameters.

The last block inserts a second `yeti`. The primary-key rule is broken, and the database raises
`IntegrityError: UNIQUE constraint failed: creature.name`. In a layered application the data layer
would turn this into the `Duplicate` exception of lesson 15.

## SQLAlchemy in one page

Writing SQL strings by hand for every operation is repetitive, and the strings are invisible to
your editor. **SQLAlchemy** is the standard Python library one level up. Its upper half is an
**ORM** (object-relational mapper): a tool that presents tables as Python classes and rows as
objects. The three objects to know in SQLAlchemy 2.0:

- The **engine** is created once for each process from a database address such as
  `postgresql+psycopg://user:pw@host/db`. It owns the **connection pool**: a set of open
  connections that are lent out and returned, because opening a new connection for every query
  would be slow.
- A **session** is a workspace for one piece of work. It keeps track of the objects you have loaded
  and the changes you have made, and it holds a transaction. Sessions are cheap to create and are
  **not safe to share between threads**. Use one for each request.
- **Declarative models** are the classes that describe tables.

```python
from sqlalchemy import ForeignKey, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

class Base(DeclarativeBase): ...

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str]
    orders: Mapped[list["Order"]] = relationship(back_populates="user")

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    total: Mapped[float]
    user: Mapped[User] = relationship(back_populates="orders")

engine = create_engine("postgresql+psycopg://app:app@localhost/app", pool_pre_ping=True)

with Session(engine) as session:
    user = session.scalars(select(User).where(User.email == "ann@example.com")).first()
    session.add(Order(user_id=user.id, total=19.9))
    session.commit()
```

- `class User(Base)` describes the table `users`. Each attribute is a column: `id` is the primary
  key, and `email` is text of at most 255 characters that must be unique and has an index (a lookup
  structure, explained below).
- `orders: Mapped[list["Order"]] = relationship(...)` is not a column. It is a convenience that lets
  you write `user.orders` and receive that user's `Order` objects.
- `class Order(Base)` has a foreign key `user_id` pointing at `users.id`.
- `create_engine(...)` builds the engine. `pool_pre_ping=True` tests a connection before it is used.
- Inside `with Session(engine) as session:` the code builds a query in Python
  (`select(User).where(User.email == ...)`), takes the first result, adds a new `Order` and commits.

With plain SQLAlchemy you maintain **two sets of classes**: ORM models for the tables, and Pydantic
models (commonly called *schemas* in this context) for the shapes of the API. You convert with
`Schema.model_validate(orm_obj)`, which needs `from_attributes=True` (lesson 7). Many teams prefer
the separation, because the API contract and the table design can then change independently.

## SQLModel: one class for both

**SQLModel**, written by FastAPI's author, is built on SQLAlchemy *and* Pydantic, so that one class
can be both a table and a validation model. The official FastAPI SQL tutorial uses it:

```python
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select

class HeroBase(SQLModel):
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)

class Hero(HeroBase, table=True):          # the only TABLE model
    id: int | None = Field(default=None, primary_key=True)
    secret_name: str

class HeroPublic(HeroBase):                # what clients receive (no secret_name)
    id: int

class HeroCreate(HeroBase):                # what clients send to create
    secret_name: str

class HeroUpdate(HeroBase):                # PATCH body: everything optional
    name: str | None = None
    age: int | None = None
    secret_name: str | None = None

sqlite_url = "sqlite:///database.db"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
```

This is the model-family pattern from lesson 5, with one addition:

- `HeroBase` holds the fields that every variant shares.
- `Hero(HeroBase, table=True)` is the only class that is a real table. `id` is `None` until the
  database assigns it; `secret_name` is stored but must stay private.
- `HeroPublic` is what clients receive: an `id` that is always present, and no `secret_name`.
- `HeroCreate` is what clients send to create a hero.
- `HeroUpdate` is the PATCH body, with every field optional.
- `create_engine` builds the engine for a SQLite file, and `create_db_and_tables` creates any
  missing tables.

`table=True` is the switch: with it, a class is a database table; without it, the class is a pure
data model used for validation and responses. The family matters for the reason given in lesson 5:
`secret_name` goes in and never comes out, and `id` is optional before the insert but guaranteed in
`HeroPublic`.

(`check_same_thread=False` is a setting specific to SQLite. FastAPI may run the parts of one request
on different threads of its pool, and SQLite objects otherwise refuse to be used from a thread other
than the one that created them. Each request still gets a session of its own.)

## A session per request

```python
def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
```

This is the standard pattern, and you met its shape in lesson 11. The **engine is global**: one
pool for the process. The **session belongs to one request**: a `yield` dependency creates it and
closes it afterwards, which returns its connection to the pool. Never share one session between
requests. A session carries the state of a transaction and a record of loaded objects, and
simultaneous use by two requests corrupts both.

CRUD endpoints then read naturally:

```python
@app.post("/heroes/", response_model=HeroPublic, status_code=201)
def create_hero(hero: HeroCreate, session: SessionDep):
    db_hero = Hero.model_validate(hero)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)          # reload DB-generated values (id)
    return db_hero

@app.get("/heroes/", response_model=list[HeroPublic])
def read_heroes(session: SessionDep, offset: int = 0,
                limit: Annotated[int, Query(le=100)] = 100):
    return session.exec(select(Hero).offset(offset).limit(limit)).all()

@app.get("/heroes/{hero_id}", response_model=HeroPublic)
def read_hero(hero_id: int, session: SessionDep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero

@app.patch("/heroes/{hero_id}", response_model=HeroPublic)
def update_hero(hero_id: int, hero: HeroUpdate, session: SessionDep):
    hero_db = session.get(Hero, hero_id)
    if not hero_db:
        raise HTTPException(status_code=404, detail="Hero not found")
    hero_db.sqlmodel_update(hero.model_dump(exclude_unset=True))   # only fields the client sent
    session.add(hero_db)
    session.commit()
    session.refresh(hero_db)
    return hero_db

@app.delete("/heroes/{hero_id}", status_code=204)
def delete_hero(hero_id: int, session: SessionDep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    session.delete(hero)
    session.commit()
```

- **Create.** `Hero.model_validate(hero)` turns the incoming `HeroCreate` into a table object.
  `session.add` registers it, `session.commit` writes it, and `session.refresh` re-reads the row so
  that the `id` generated by the database is filled in. The response model then filters out
  `secret_name`.
- **List.** `select(Hero).offset(offset).limit(limit)` is pagination done by the database (lesson
  2); `limit` is capped at 100.
- **Read one.** `session.get(Hero, hero_id)` fetches by primary key and returns `None` when no such
  row exists, which becomes a 404.
- **Update.** `hero.model_dump(exclude_unset=True)` yields only the fields the client sent (lesson
  8), and `sqlmodel_update` applies them to the stored object.
- **Delete.** Fetch, delete, commit, and answer 204.

These are plain `def` endpoints. The driver is synchronous, so FastAPI runs them in its thread pool
(lesson 12). In the layered design of the previous lesson, the query code would sit in a repository
or data module and the endpoint would call a service.

## Transactions

A **transaction** is a group of changes that the database treats as one: either all of them happen
or none do. A session starts a transaction automatically the first time it is used. `commit()` makes
the changes permanent; `rollback()` discards them; closing a session with a transaction still open
rolls it back. Guidelines:

- **One business operation = one transaction.** If creating an order also reduces the stock count,
  both changes come before a single `commit()`. With two commits, a crash between them would leave
  the data contradicting itself.
- Commit **explicitly** in the service or endpoint, or use `with session.begin():` for a block that
  commits on success and rolls back on an exception.
- Catch `IntegrityError` (a broken uniqueness or foreign-key rule), call `rollback()`, and translate
  it into a domain error, which becomes a 409. Do not enforce uniqueness by "checking first, then
  inserting". Two requests arriving together can both pass the check before either inserts. Such a
  timing-dependent bug is called a **race condition**, and only a constraint inside the database is
  free of it.

```python-run
import sqlite3

conn = sqlite3.connect(":memory:", isolation_level=None)      # manual transaction control
conn.execute("create table account(id integer primary key, balance integer check(balance >= 0))")
conn.execute("insert into account values (1, 100), (2, 0)")

def transfer(src, dst, amount):
    try:
        conn.execute("begin")
        conn.execute("update account set balance = balance + ? where id = ?", (amount, dst))
        conn.execute("update account set balance = balance - ? where id = ?", (amount, src))
        conn.execute("commit")
        return "ok"
    except sqlite3.IntegrityError as e:
        conn.execute("rollback")                               # undo the credit too
        return f"rolled back ({e})"

print(transfer(1, 2, 70), conn.execute("select * from account").fetchall())
print(transfer(1, 2, 70), conn.execute("select * from account").fetchall())
```

The table has a rule, `check(balance >= 0)`: no balance may go below zero. Account 1 starts with 100
and account 2 with 0. `transfer` begins a transaction, adds the amount to the destination, subtracts
it from the source, and commits.

The first transfer of 70 works: the output shows `ok` and balances of 30 and 70. The second transfer
of 70 first credits account 2 (which would make it 140) and then tries to debit account 1, which
would make it -40. The constraint refuses, and the `except` branch rolls back. The printed balances
are still 30 and 70. The credit that had already been made was undone together with the failed
debit. This all-or-nothing property is called **atomicity**.

## The N+1 query problem

An ORM normally loads related objects *lazily*: `user.orders` triggers a query at the moment you
first touch it. Listing 100 users and touching `user.orders` for each therefore sends 1 query for
the users plus 100 more, one per user. That is the **N+1 problem**. The cure is **eager loading**,
which asks for the related rows up front:

```python
from sqlalchemy.orm import selectinload
users = session.scalars(select(User).options(selectinload(User.orders)).limit(100)).all()
# 2 queries total: users, then orders WHERE user_id IN (...)
```

Pass `echo=True` when creating the engine during development to *see* the SQL your endpoint sends.
It is the most instructive debugging switch SQLAlchemy has.

> [!INTERVIEW]
> "How do you manage database sessions in FastAPI?" — Create one engine (with its connection pool)
> per process at start-up. Provide a session per request through a `yield` dependency that opens the
> session and closes it afterwards, returning the connection to the pool. Endpoints or services
> commit explicitly; errors roll back. Sessions are never shared between requests or threads. In
> tests, override the dependency with a session bound to a test database, or to a transaction that is
> rolled back after each test.

## Relationships and N+1, demonstrated

The N+1 problem is easier to believe once you have counted the queries. SQLite can report every
statement it runs:

```python-run
import sqlite3

conn = sqlite3.connect(":memory:")
conn.executescript("""
    create table users(id integer primary key, name text);
    create table orders(id integer primary key, user_id integer references users(id), total real);
    create index ix_orders_user on orders(user_id);
""")
conn.executemany("insert into users values (?, ?)", [(i, f"user{i}") for i in range(1, 51)])
conn.executemany("insert into orders(user_id, total) values (?, ?)",
                 [(u, 10.0 * k) for u in range(1, 51) for k in range(1, 4)])

statements = []
conn.set_trace_callback(statements.append)

# --- lazy loading: what an ORM does when you touch user.orders in a loop ---
statements.clear()
result = {}
for user_id, name in conn.execute("select id, name from users").fetchall():
    result[name] = [t for (t,) in conn.execute("select total from orders where user_id = ?", (user_id,))]
print("lazy          :", len(statements), "queries")

# --- 'selectin' eager loading: one extra query with IN (...) ---
statements.clear()
users = conn.execute("select id, name from users").fetchall()
ids = [u[0] for u in users]
orders = conn.execute(f"select user_id, total from orders where user_id in ({','.join('?' * len(ids))})", ids)
by_user = {}
for user_id, total in orders:
    by_user.setdefault(user_id, []).append(total)
result2 = {name: by_user.get(uid, []) for uid, name in users}
print("selectin      :", len(statements), "queries")

# --- 'joined' eager loading: a single JOIN ---
statements.clear()
rows = conn.execute("""select u.name, o.total from users u left join orders o on o.user_id = u.id""").fetchall()
print("joined        :", len(statements), "query,", len(rows), "rows for 50 users (parent data repeated)")
print("same data     :", result == result2)
```

The set-up creates 50 users with three orders each. `set_trace_callback` appends every executed
statement to a list, so `len(statements)` is the number of queries. Three strategies fetch the same
data:

- **Lazy**: one query for the users, then one per user for that user's orders. The output says
  `51 queries`.
- **Select-in**: one query for the users, then a single query for all their orders using
  `where user_id in (...)`. The output says `2 queries`.
- **Joined**: one query that combines the two tables with a `JOIN`. The output says 1 query and 150
  rows for 50 users, because each user's name is repeated on each of that user's order rows.

The last line confirms that the first two strategies produced identical data. Fifty-one queries
against two: over a network each query costs a round trip of perhaps a millisecond, so the lazy
version of a 100-item page spends a tenth of a second doing nothing but waiting. Note the trade-off
in the joined version: it returns one row per *child*, repeating the parent's columns. That is fine
for a single related object and wasteful for large collections, which is why `selectinload` is the
usual choice for collections and `joinedload` for a single parent.

In SQLModel and SQLAlchemy, the relationship and the eager load look like this:

```python
class Team(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    heroes: list["Hero"] = Relationship(back_populates="team")

class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    team_id: int | None = Field(default=None, foreign_key="team.id", index=True)
    team: Team | None = Relationship(back_populates="heroes")

class TeamPublicWithHeroes(TeamPublic):          # response model that includes the children
    heroes: list[HeroPublic] = []

@app.get("/teams", response_model=list[TeamPublicWithHeroes])
def read_teams(session: SessionDep, limit: Annotated[int, Query(le=100)] = 20):
    statement = select(Team).options(selectinload(Team.heroes)).limit(limit)
    return session.exec(statement).all()
```

Two details matter. A response model that includes related objects must be declared explicitly: the
plain `TeamPublic` has no `heroes`, so nothing is loaded or revealed by accident. And beware of
shapes that go round in circles (a team's heroes, each hero's team, that team's heroes, and so on).
Design nested public models to stop after one level.

## Indexes and reading a query plan

The second classic performance problem is a missing **index**. An index is an extra lookup structure
that the database keeps for a column, like the index at the back of a book: it lets the database
jump to the matching rows without reading the whole table. The command `EXPLAIN` asks the database
how it intends to run a query, and its answer is the **query plan**.

```python-run
import sqlite3

conn = sqlite3.connect(":memory:")
conn.execute("create table events(id integer primary key, user_id integer, kind text, created_at text)")
conn.executemany("insert into events(user_id, kind, created_at) values (?, ?, ?)",
                 [(i % 1000, "click", f"2025-01-{i % 28 + 1:02d}") for i in range(20000)])

def plan(sql):
    return " | ".join(row[3] for row in conn.execute("explain query plan " + sql))

q = "select * from events where user_id = 42 order by created_at desc limit 20"
print("no index      :", plan(q))
conn.execute("create index ix_events_user on events(user_id)")
print("single column :", plan(q))
conn.execute("create index ix_events_user_created on events(user_id, created_at)")
print("composite     :", plan(q))
```

The table holds 20,000 events, and the query wants the 20 most recent events of user 42. The three
printed plans:

- **No index:** `SCAN events` plus a temporary sort. `SCAN` means every row is read.
- **Index on `user_id`:** `SEARCH events USING INDEX ix_events_user` plus a temporary sort. The
  right rows are found directly, but they must still be sorted for the `ORDER BY`.
- **Composite index on `(user_id, created_at)`:** a `SEARCH` with no separate sorting step. A
  *composite* index covers two columns, and here it serves both the filter and the ordering, so the
  first twenty rows can be returned straight away.

Rules of thumb: index foreign keys, and index the columns that appear in your most frequent `WHERE`
and `ORDER BY` clauses; in a composite index put the columns compared for equality first and the
sorting or range column after them; and remember that every index makes writes a little slower. On
PostgreSQL, run `EXPLAIN (ANALYZE, BUFFERS)` on the real query with realistic amounts of data.

## Sessions: the mental model

A session is three things at once, and most confusion about ORMs comes from forgetting one of them:

| Aspect | What it does | Consequence |
|---|---|---|
| **Identity map** | one Python object per row per session | `session.get(User, 1) is session.get(User, 1)`; a second session has its own copy |
| **Unit of work** | tracks new, dirty and deleted objects; writes them at `flush` | changes are sent as SQL on flush (automatically before queries and at commit), not when you set attributes |
| **Transaction** | begun on first use, ended by `commit`/`rollback`/`close` | nothing is durable, and nothing is visible to other sessions, until commit |

Useful distinctions. `flush()` sends the pending SQL *inside* the transaction, so that you can read a
generated primary key before committing. `commit()` flushes and makes the result permanent.
`refresh(obj)` re-reads one row. The setting `expire_on_commit` (on by default) marks objects as
out of date after a commit, so the next time you read an attribute it is fetched again; this is the
cause of the notorious `DetachedInstanceError` when code touches an object after its session has been
closed. In an API, convert to response models (or let `response_model` do so) while the session is
still open.

## Debugging checklist

| Symptom | Likely cause |
|---|---|
| Changes vanish | no `commit()`, or an exception rolled back the transaction |
| `id` is `None` after `add` | not flushed/committed yet, or missing `refresh` |
| `DetachedInstanceError` / lazy-load error in serialisation | object used after its session closed; eager-load or serialise earlier |
| `QueuePool limit ... reached, connection timed out` | sessions not closed, long transactions, or pool too small for the concurrency |
| `SQLite objects created in a thread can only be used in that same thread` | missing `check_same_thread=False` for SQLite |
| Endpoint slow with many tiny queries in the log | N+1 — add `selectinload` |
| `IntegrityError` under concurrent requests only | check-then-insert race; rely on the constraint and handle the error |
| Deadlocks under load | transactions touching the same rows in different orders; lock in a consistent order, keep transactions short |

Setting `echo=True` on the engine (in development only) prints every statement with its parameters,
and is the quickest way to confirm any of the above.

## Pitfalls

- One global session shared by all requests.
- Building SQL with f-strings (injection). Always pass parameters.
- Forgetting `commit()` (nothing is saved) or `refresh()` (generated IDs are missing).
- Returning table models that contain secrets. Use `response_model=...Public`.
- Lazy loading while the response is being converted to JSON, which causes N+1 queries, or errors if
  the session is already closed.
- Synchronous database calls inside `async def` endpoints.

## Summary

- The DB-API (connections, cursors, parameters) is underneath everything; SQLAlchemy adds an engine
  with a pool, queries built in Python and an ORM; SQLModel merges ORM tables with Pydantic models.
- Engine: one per process. Session: one per request, through a `yield` dependency.
- Use Base / Create / Public / Update model families; PATCH with `exclude_unset=True`.
- One business operation per transaction; rely on database constraints and handle `IntegrityError`.
- Watch for N+1 queries; eager-load with `selectinload`.

## Glossary

- **Relational database** — a database that stores data in tables related through keys.
- **Table / row / column** — a set of records / one record / one property of every record.
- **SQL** — the language for reading and changing data in a relational database.
- **Primary key / foreign key** — a row's unique identifier / a column pointing at another table's
  primary key.
- **Constraint** — a rule the database enforces on every write.
- **Driver / DB-API** — the library for one database product / Python's standard interface for
  drivers.
- **Cursor** — the object used to run statements and fetch results.
- **SQL injection** — user input being executed as part of a SQL command.
- **Parameter (placeholder)** — a slot in SQL text whose value is sent separately.
- **ORM** — a library that maps tables to classes and rows to objects.
- **Engine / connection pool** — the per-process database gateway / its set of reusable connections.
- **Session** — a per-request workspace that tracks objects and holds a transaction.
- **Transaction / atomicity** — a group of changes treated as one / the all-or-nothing guarantee.
- **Race condition** — a bug that depends on the timing of simultaneous operations.
- **Lazy / eager loading** — fetching related rows when first touched / fetching them up front.
- **N+1 problem** — one query for a list plus one more for each item in it.
- **Index / query plan** — a lookup structure for fast searching / the database's chosen way to run a
  query.

```quiz
[
  {"q": "Which object should be created once per process and shared?", "options": ["Session", "Engine (with its connection pool)", "Cursor", "Transaction"], "answer": 1,
   "explain": "The engine owns the pool; sessions are short-lived, per-request units of work."},
  {"q": "Why pass values as bound parameters instead of formatting them into SQL strings?", "options": ["It is shorter", "It prevents SQL injection because values are never parsed as SQL", "It makes queries async", "SQLite requires it"], "answer": 1,
   "explain": "The driver sends parameters separately from the statement, so malicious text is treated as data."},
  {"q": "In SQLModel, what does table=True do?", "options": ["Enables validation", "Makes the class a mapped database table in addition to a model", "Creates an index", "Marks the model as public"], "answer": 1,
   "explain": "Only table=True classes are SQLAlchemy tables; the others are data-only Pydantic models."},
  {"q": "Why call session.refresh(obj) after commit when creating a row?", "options": ["To close the session", "To load database-generated values such as the primary key", "To validate the object", "To start a new transaction for speed"], "answer": 1,
   "explain": "After commit, attributes are expired; refresh reloads them, including autogenerated ids/defaults."},
  {"q": "What is the race-free way to guarantee unique emails?", "options": ["SELECT first, then INSERT if absent", "A unique constraint in the database and handling IntegrityError", "A Pydantic validator", "A Python lock"], "answer": 1,
   "explain": "Check-then-insert has a window between the two statements; only the DB constraint is atomic across processes."},
  {"q": "Listing 50 users and accessing user.orders on each triggers 51 queries. What is this called and one fix?", "options": ["Deadlock; add indexes", "N+1 problem; eager load with selectinload/joinedload", "Dirty read; raise isolation level", "Pool exhaustion; increase pool_size"], "answer": 1,
   "explain": "Lazy loading issues one query per parent. Eager loading fetches related rows in one or two queries."},
  {"q": "A sync SQLAlchemy session is used inside 'async def' endpoints. Effect under load?", "options": ["Faster queries", "Each query blocks the event loop, stalling all requests on that worker", "Automatic thread offloading", "Nothing"], "answer": 1,
   "explain": "Blocking DB I/O on the loop serialises the whole worker; use def endpoints or an async driver."}
]
```

> **Source:** Lubanovic, *FastAPI*, ch. 10 "Data Layer" (DB-API, SQLite, Making It Work) and ch. 14 "Databases, Data Science, and a Little AI" (Relational Databases and SQL, SQLAlchemy, SQLModel); https://fastapi.tiangolo.com/tutorial/sql-databases/; https://sqlmodel.tiangolo.com/; https://docs.sqlalchemy.org/en/20/orm/session_basics.html
