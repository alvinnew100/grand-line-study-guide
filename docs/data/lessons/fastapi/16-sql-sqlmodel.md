# SQL with SQLAlchemy and SQLModel

Most APIs are, at heart, a careful interface to a relational database. FastAPI is database-agnostic — you
can use raw drivers, SQLAlchemy, SQLModel, or anything else. This lesson walks up the abstraction ladder
the way Lubanovic does (DB-API → SQLAlchemy → SQLModel) and then focuses on the pattern you must get
right: **one session per request**.

## The abstraction ladder

| Level | What you write | Example |
|---|---|---|
| DB-API driver | SQL strings + cursors | `sqlite3`, `psycopg` |
| SQLAlchemy **Core** | SQL built from Python expressions | `select(users).where(users.c.id == 1)` |
| SQLAlchemy **ORM** | classes mapped to tables, a `Session` tracking objects | `session.get(User, 1)` |
| **SQLModel** | one class that is both a Pydantic model and a SQLAlchemy table | `class Hero(SQLModel, table=True)` |

The book's data-layer chapter deliberately starts at the bottom with the standard-library `sqlite3`
module, because Python's **DB-API** (PEP 249) is what every other tool is built on: `connect()` → a
connection; `conn.cursor()` → a cursor; `cursor.execute(sql, params)`; `fetchone()/fetchall()`; `commit()`.

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

## SQLAlchemy in one page

SQLAlchemy 2.0's key objects:

- **Engine** — created once per process from a URL (`postgresql+psycopg://user:pw@host/db`). Owns the
  **connection pool**.
- **Session** — a unit of work: a workspace that tracks loaded objects, pending changes, and a
  transaction. Cheap to create; **not thread-safe**; one per request.
- **Declarative models** — classes with `Mapped[...]` columns.

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

With plain SQLAlchemy you keep **two sets of classes**: ORM models (tables) and Pydantic schemas (API
shapes), converting with `Schema.model_validate(orm_obj)` (`from_attributes=True`). Many teams prefer that
separation: the API contract and the storage schema evolve independently.

## SQLModel: one class for both

SQLModel (by FastAPI's author) builds on SQLAlchemy *and* Pydantic. The current official FastAPI
SQL tutorial uses it:

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

`table=True` makes a class a real table; the others are pure data models (Pydantic) used for validation
and responses. The **multiple-models pattern** matters for the same reason as in the response-model
lesson: `secret_name` goes in but never comes out, and `id` is optional before insert but guaranteed in
`HeroPublic`.

(`check_same_thread=False` is a SQLite-specific flag: FastAPI may run one request's code on different
threads of its pool, and SQLite objects otherwise refuse to cross threads. Each request still gets its own
session.)

## A session per request

```python
def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
```

This is the canonical pattern. The **engine is global** (one pool per process); the **session is
per-request**, created by a `yield` dependency and closed afterwards (which returns its connection to the
pool). Never share one session across requests: sessions hold transaction state and an identity map, and
concurrent use corrupts both.

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

These are plain `def` endpoints: the driver is synchronous, so FastAPI runs them in the thread pool.
(In the layered design from the previous lesson, the query code would live in a repository/data module and
the endpoint would call a service.)

## Transactions

A session begins a transaction implicitly on first use; `commit()` makes changes durable; `rollback()`
discards them; closing a session with an open transaction rolls back. Guidelines:

- **One business operation = one transaction.** If creating an order also decrements stock, both happen
  before a single `commit()` — otherwise a crash between two commits leaves inconsistent data.
- Commit **explicitly** in the service/endpoint, or use `with session.begin():` for a block that commits
  on success and rolls back on exception.
- Catch `IntegrityError` (unique/foreign-key violations), `rollback()`, and translate it to a domain error
  → 409. Don't "check then insert" to enforce uniqueness — two concurrent requests both pass the check;
  only a database constraint is race-free.

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

The second transfer credits account 2, then fails the debit; the rollback undoes *both* statements —
atomicity.

## The N+1 query problem

ORMs load relationships lazily by default. Listing 100 users and touching `user.orders` for each issues
1 + 100 queries. Fix with eager loading:

```python
from sqlalchemy.orm import selectinload
users = session.scalars(select(User).options(selectinload(User.orders)).limit(100)).all()
# 2 queries total: users, then orders WHERE user_id IN (...)
```

Turn on `echo=True` on the engine in development to *see* the SQL your endpoint emits — the most
educational debugging switch SQLAlchemy has.

> [!INTERVIEW]
> "How do you manage database sessions in FastAPI?" — Create one engine (connection pool) per process at
> startup. Provide a session per request through a `yield` dependency that opens the session and closes it
> afterwards, returning the connection to the pool. Endpoints/services commit explicitly; errors roll back.
> Sessions are never shared between requests or threads. In tests, override the dependency with a session
> bound to a test database or a transaction that rolls back after each test.

## Pitfalls

- A global session shared by all requests.
- Building SQL with f-strings (injection). Always bind parameters.
- Forgetting `commit()` (nothing saved) or `refresh()` (missing generated IDs).
- Returning table models with secrets — use `response_model=...Public`.
- Lazy-loading relationships during response serialisation → N+1 queries, or errors if the session is
  already closed.
- Sync DB calls in `async def` endpoints.

## Summary

- DB-API (connections, cursors, bound parameters) underlies everything; SQLAlchemy adds an engine/pool,
  expression language and ORM; SQLModel merges ORM tables with Pydantic models.
- Engine: one per process. Session: one per request via a `yield` dependency.
- Use Base/Create/Public/Update model families; PATCH with `exclude_unset=True`.
- One business operation per transaction; rely on DB constraints and handle `IntegrityError`.
- Watch for N+1 queries; eager-load with `selectinload`.

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
