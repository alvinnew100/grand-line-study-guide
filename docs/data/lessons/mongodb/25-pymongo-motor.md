# PyMongo, Motor and Pydantic models

> **Before this lesson:** you should be comfortable with CRUD, filters and update operators ([Update operators, arrays and upserts](#/lesson/mongodb/update-operators), [Query operators and how documents match](#/lesson/mongodb/query-operators)), with BSON types such as ObjectId and dates ([BSON types, ObjectId and the shell](#/lesson/mongodb/bson-shell)), and with why one client object is shared ([Connecting from applications and administering a replica set](#/lesson/mongodb/replica-admin)). Basic Python - functions, dictionaries, classes - is assumed; `async` and type hints are explained here.

## In plain words

Earlier lessons showed short Python snippets next to each shell example. This lesson is about writing a real Python program against MongoDB: how to organise the code, how to keep bad data out, and how to serve many users at once.

Three tools do the work.

- **PyMongo** is the official Python **driver**: the library that turns Python calls into messages the database understands. It is the telephone line between your program and MongoDB.
- **Pydantic** is a library for describing what your data should look like and checking that it does. Think of the receptionist who checks that a form is filled in properly before passing it on: date in the date box, a number in the age box, nothing essential left blank.
- **Motor** and PyMongo's newer **async API** let one program wait on many database requests at once. Picture one waiter looking after ten tables: while table 3's food is cooking, the waiter takes table 7's order, instead of standing at the kitchen door doing nothing.

Why it matters for a job: Python is the main language of data and machine-learning work, and services built with frameworks such as FastAPI on top of MongoDB are common. Interviewers look for the habits in this lesson: one shared client, validated models at the boundary, and a correct understanding of what `async` does and does not buy.

## PyMongo essentials

Install with `pip install pymongo`. The object model has three levels, mirroring the database's own structure:

```python
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/?appName=library-api")   # 1
db = client["library"]                                                   # 2
books = db["books"]                                                      # 3
```

1. `MongoClient` represents the connection to a deployment. It owns a **connection pool**, a set of open connections that are reused. Create it **once** when the program starts and share it everywhere. It is safe to use from many threads at the same time.
2. A database handle. Nothing is sent to the server yet.
3. A collection handle. Handles are cheap; create as many as you like.

The CRUD methods have the same names as in the shell, written with underscores:

```python
from datetime import datetime, timezone

result = books.insert_one({"title": "Salt Harbour", "year": 2019, "tags": ["sea"],
                           "added": datetime.now(timezone.utc)})          # 1
print(result.inserted_id)                                                # 2

book = books.find_one({"title": "Salt Harbour"})                         # 3
print(book["year"], type(book["_id"]).__name__)                          # 4

books.update_one({"_id": book["_id"]}, {"$push": {"tags": "prize-winner"}})   # 5

for b in books.find({"year": {"$gte": 2015}}, {"title": 1, "year": 1}).sort("year", -1).limit(5):   # 6
    print(b["title"], b["year"])

print(books.delete_one({"_id": book["_id"]}).deleted_count)              # 7
```

1. A Python `dict` becomes a document. The `datetime` carries an explicit UTC time zone and is stored as a BSON date.
2. The generated `_id`, an `ObjectId`.
3. `find_one` returns one document as a dictionary, or `None` if nothing matches. Always handle the `None` case.
4. Prints `2019 ObjectId`.
5. Operators such as `$push` are quoted keys.
6. `find` returns a cursor. Filter, projection, sort and limit are combined before the query is sent, as in the shell.
7. Prints `1`.

### Type mapping to remember

| Python | BSON | note |
|---|---|---|
| `dict` | document | keys must be strings |
| `list` | array | |
| `str` | string | |
| `int` | 32-bit or 64-bit integer | chosen by size |
| `float` | double | |
| `bool` | boolean | |
| `None` | null | |
| `datetime.datetime` | date | milliseconds precision; returned without time zone unless `tz_aware=True` is set on the client |
| `bson.ObjectId` | ObjectId | not a string |
| `decimal.Decimal` | *not accepted directly* | convert with `bson.Decimal128` |

Two of these cause most first-week bugs. An `ObjectId` is not a string: an id received from a web request must be converted with `ObjectId(text)` before querying, and converted back with `str(oid)` before being returned as JSON. And dates come back from PyMongo as "naive" datetimes with no time zone attached, although they are UTC; pass `tz_aware=True` to `MongoClient` to receive them with UTC attached.

### Many writes in one round trip

Sending a thousand operations one by one means a thousand network round trips. `bulk_write` sends a mixed batch at once:

```python
from pymongo import InsertOne, UpdateOne, DeleteOne

outcome = books.bulk_write([
    InsertOne({"title": "The Quiet Tide", "year": 2023}),
    UpdateOne({"title": "Salt Harbour"}, {"$inc": {"loans": 1}}, upsert=True),
    DeleteOne({"withdrawn": True}),
], ordered=False)
print(outcome.inserted_count, outcome.modified_count, outcome.upserted_count, outcome.deleted_count)
```

Each element describes one operation. `ordered=False` lets the server continue past individual failures and execute in any order. The result reports how many documents each kind of operation affected.

### Errors worth catching

| exception | when | sensible reaction |
|---|---|---|
| `DuplicateKeyError` | a unique index rejected the write | report "already exists"; often not an error at all |
| `ServerSelectionTimeoutError` | no suitable server could be reached in time | report "service unavailable" |
| `OperationFailure` | the server refused: not authorised, invalid query, failed validation | inspect `.code` and `.details` |
| `BulkWriteError` | some operations of a bulk write failed | read `.details` to see which succeeded |

Catch the specific exception you can handle. A bare `except Exception` around database calls hides real problems.

## Pydantic: giving documents a shape

MongoDB will store whatever dictionary you hand it. That freedom is the source of the classic slow-motion failure: one code path writes `"year": "2019"` as a string, another writes `"yr": 2019`, and six months later a report crashes on data nobody remembers creating.

The defence is to make one place in the program responsible for the shape of each kind of document. **Pydantic** (install with `pip install pydantic`) does this with **models**: classes whose attributes carry **type hints**, the annotations after a colon such as `year: int` that state what type a value should have.

```python
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class Book(BaseModel):                                                    # 1
    title: str = Field(min_length=1)                                      # 2
    year: int = Field(ge=1400, le=2100)                                   # 3
    tags: list[str] = []                                                  # 4
    added: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))   # 5

book = Book(title="Salt Harbour", year="2019")                            # 6
print(book.year + 1)                                                      # 7
print(book.model_dump())                                                  # 8
```

1. A model is a class inheriting from `BaseModel`.
2. `title` must be a string of at least one character. `Field` adds constraints beyond the type.
3. `year` must be an integer between 1400 and 2100 (`ge` means greater than or equal, `le` less than or equal).
4. `tags` is a list of strings and defaults to empty.
5. `default_factory` calls a function to produce the default, so each book receives the current time, not the time the class was defined.
6. Creating an instance **validates** the input. The string `"2019"` is converted to the integer 2019, because that conversion is unambiguous.
7. Prints `2020`: `year` is a real integer.
8. `model_dump()` converts the model to a plain dictionary, ready for `insert_one`.

Invalid input raises `ValidationError` with a precise description:

```python
from pydantic import ValidationError

try:
    Book(title="", year=3000)
except ValidationError as err:
    print(err.error_count(), [e["loc"][0] for e in err.errors()])        # prints: 2 ['title', 'year']
```

Both problems are reported at once, each with the field it concerns.

### Handling `_id`

Two details need care. Pydantic treats attribute names starting with an underscore as private, so the field is declared as `id` with the **alias** `_id` (an alias is an alternative name used when reading and writing data). And `ObjectId` is not a type Pydantic knows, so the simplest approach is to hold the id as a string in the model and convert at the database boundary.

```python
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field

class BookInDB(Book):
    model_config = ConfigDict(populate_by_name=True)                     # 1
    id: Optional[str] = Field(default=None, alias="_id")                 # 2

def from_mongo(doc: dict) -> BookInDB:                                   # 3
    return BookInDB.model_validate({**doc, "_id": str(doc["_id"])})

def to_mongo(book: Book) -> dict:                                        # 4
    return book.model_dump(exclude={"id"})
```

1. Allows the field to be set as either `id` or `_id`.
2. An optional string that is read from and written to the key `_id`.
3. Reading: convert the `ObjectId` to a string, then validate the whole document. Every document leaving the database passes this check, so the rest of the program can trust its shape.
4. Writing: produce a dictionary without the id, and let MongoDB generate one.

### A repository: one place for database code

A **repository** is a class that hides the database behind a few meaningful methods. The rest of the program asks for "the book with this id" and never sees a filter document.

```python
class BookRepository:
    def __init__(self, collection):
        self.c = collection

    def add(self, book: Book) -> str:
        return str(self.c.insert_one(to_mongo(book)).inserted_id)

    def get(self, book_id: str) -> Optional[BookInDB]:
        if not ObjectId.is_valid(book_id):                               # 1
            return None
        doc = self.c.find_one({"_id": ObjectId(book_id)})
        return from_mongo(doc) if doc else None                          # 2

    def recent(self, limit: int = 10) -> list[BookInDB]:
        return [from_mongo(d) for d in self.c.find().sort("added", -1).limit(min(limit, 100))]   # 3
```

1. A malformed id from a URL is rejected before it reaches the database.
2. `None` is passed through when nothing is found.
3. The limit is capped, so a caller cannot request a million documents by accident.

Benefits: queries live in one file, where they can be reviewed against the indexes; tests can substitute a fake repository; and a change of schema touches one class.

> [!WARNING]
> Application-level validation and database-level validation solve different problems, and serious systems use both. Pydantic protects your own code paths. A `$jsonSchema` validator on the collection (see the schema patterns lesson) protects against everything else: another service, a migration script, someone working in the shell at midnight.

## Asynchronous access

### What "async" means

A web server handles many requests at once. Most of each request's time is spent **waiting** - for the database, for another service - not computing. There are two ways to handle many waiting requests.

With **synchronous** code, each call blocks: the line `books.find_one(...)` does not return until the answer arrives, and the thread running it can do nothing else meanwhile. To serve many users you need many threads.

With **asynchronous** code, a function that reaches a slow operation says, in effect, "I am waiting; let someone else run". A single thread, coordinated by an **event loop**, switches between many functions, each paused at a point where it is waiting. In Python such a function is declared with `async def`, and the word `await` marks each point where it may pause.

Async does not make a single query faster. It lets one process make progress on many requests while each of them waits.

### Motor and PyMongo's async API

For years the async driver for MongoDB was **Motor**, a separate package with the same method names as PyMongo. PyMongo itself now includes an async API (`AsyncMongoClient`, from version 4.9), and MongoDB has announced that Motor is deprecated in its favour. You will meet Motor in existing code; new projects should use PyMongo's own async client. The two look almost identical:

```python
import asyncio
from pymongo import AsyncMongoClient          # with Motor: from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncMongoClient("mongodb://localhost:27017")                   # 1
books = client["library"]["books"]

async def main():
    await books.insert_one({"title": "Salt Harbour", "year": 2019})      # 2
    book = await books.find_one({"title": "Salt Harbour"})               # 3
    print(book["year"])

    async for b in books.find({"year": {"$gte": 2015}}).sort("year", -1):   # 4
        print(b["title"])

    recent, total = await asyncio.gather(                                # 5
        books.find().sort("added", -1).limit(5).to_list(),
        books.count_documents({}),
    )
    print(len(recent), total)

asyncio.run(main())                                                      # 6
```

1. One client for the whole application, as before.
2. Every method that talks to the server must be awaited. Forgetting `await` is the most common mistake: you get an unfinished "coroutine" object in place of a result.
3. `find_one` awaited returns the document.
4. `find` returns an async cursor, iterated with `async for`.
5. `asyncio.gather` runs both operations **concurrently** - both are in flight at once - and waits for both. The total time is that of the slower one, not the sum.
6. `asyncio.run` starts the event loop and runs `main` to completion.

### In a web framework

FastAPI is a Python web framework built around async functions and Pydantic models, which makes the three tools of this lesson fit together naturally:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pymongo import AsyncMongoClient

@asynccontextmanager
async def lifespan(app: FastAPI):                                        # 1
    app.state.client = AsyncMongoClient("mongodb://localhost:27017")
    app.state.books = app.state.client["library"]["books"]
    yield
    await app.state.client.close()

app = FastAPI(lifespan=lifespan)

@app.post("/books", status_code=201)
async def create_book(book: Book):                                       # 2
    result = await app.state.books.insert_one(to_mongo(book))
    return {"id": str(result.inserted_id)}

@app.get("/books/{book_id}", response_model=BookInDB)
async def read_book(book_id: str):
    if not ObjectId.is_valid(book_id):
        raise HTTPException(status_code=404, detail="no such book")      # 3
    doc = await app.state.books.find_one({"_id": ObjectId(book_id)})
    if doc is None:
        raise HTTPException(status_code=404, detail="no such book")
    return from_mongo(doc)                                               # 4
```

1. The client is created once when the application starts and closed when it stops.
2. Declaring the parameter as `Book` makes FastAPI validate the request body with Pydantic; invalid input never reaches this function.
3. A malformed or unknown id produces a "not found" response, not a crash.
4. The validated model is returned, and FastAPI converts it to JSON with the id as a string.

> [!TIP]
> Never call the synchronous `MongoClient` inside an `async def` function. A blocking call freezes the event loop, so every other request in the process waits for that one query. Inside async code use the async client; inside ordinary functions use the synchronous one.

> [!INTERVIEW]
> **"How would you structure a Python service that uses MongoDB?"** One client created at start-up and shared, since it holds the connection pool. Pydantic models at the boundaries: request bodies are validated on the way in, and documents are validated on the way out of the database, with `_id` handled through an alias and converted between `ObjectId` and string. Database access in a repository layer, so queries are in one place and can be matched to indexes. An async driver if the framework is async, remembering that async improves concurrency of waiting, not the speed of a single query. Plus a `$jsonSchema` validator and unique indexes in the database, because application checks do not cover other writers.

## Simulate it yourself

The first part implements a miniature model with validation, standing in for Pydantic, and passes messy input through it. The second part uses real `asyncio` to compare handling five simulated queries one after another with handling them concurrently.

```python-run
import asyncio, time
from dataclasses import dataclass, field, asdict

# ---- a tiny validating model (the idea behind Pydantic) -------------------------------
class ValidationError(Exception):
    pass

@dataclass
class Book:
    title: str
    year: int
    tags: list = field(default_factory=list)

    def __post_init__(self):                      # runs automatically after the object is created
        errors = []
        if isinstance(self.year, str) and self.year.strip().isdigit():
            self.year = int(self.year)            # safe, unambiguous conversion
        if not isinstance(self.title, str) or not self.title.strip():
            errors.append("title: must be a non-empty string")
        if not isinstance(self.year, int) or isinstance(self.year, bool) or not 1400 <= self.year <= 2100:
            errors.append("year: must be an integer between 1400 and 2100")
        if not all(isinstance(t, str) for t in self.tags):
            errors.append("tags: every tag must be a string")
        if errors:
            raise ValidationError("; ".join(errors))

incoming = [
    {"title": "Salt Harbour", "year": 2019, "tags": ["sea"]},
    {"title": "The Quiet Tide", "year": "2023"},
    {"title": "", "year": 3000},
    {"title": "Old Maps", "year": "last year"},
    {"title": "Field Notes", "yr": 2001},
]
collection, next_id = [], 1
for raw in incoming:
    try:
        book = Book(**raw)
        collection.append({"_id": next_id, **asdict(book)})    # only validated data is stored
        next_id += 1
        print("stored  ", collection[-1])
    except (ValidationError, TypeError) as err:
        print("rejected", raw, "->", err)

types = {type(d["year"]).__name__ for d in collection}
print("types of 'year' in the collection:", types)

# ---- synchronous versus concurrent waiting --------------------------------------------
DELAYS = [0.05, 0.08, 0.03, 0.06, 0.04]           # five queries, each waiting on the "database"

async def fake_query(n, delay):
    await asyncio.sleep(delay)                    # the function pauses here; others may run
    return "result %d" % n

async def one_after_another():
    return [await fake_query(n, d) for n, d in enumerate(DELAYS)]

async def all_at_once():
    return await asyncio.gather(*(fake_query(n, d) for n, d in enumerate(DELAYS)))

for name, job in (("one after another", one_after_another), ("concurrently     ", all_at_once)):
    start = time.perf_counter()
    results = asyncio.run(job())
    print("%s: %d results in %.2f s" % (name, len(results), time.perf_counter() - start))
print("sum of delays %.2f s, longest delay %.2f s" % (sum(DELAYS), max(DELAYS)))
```

Reading the output:

- The first two books are stored; the year `"2023"` arrives as text and is stored as the integer 2023.
- The third is rejected with two messages at once. The fourth is rejected because `"last year"` cannot be read as a year. The fifth is rejected because of the misspelt key `yr` - the kind of typo MongoDB alone would have accepted.
- The collection ends up with exactly one type in `year`. That uniformity is what validation at the boundary buys.
- Run one after another, the five queries take at least the sum of their delays, 0.26 seconds (a little more, because timers are not exact). Run concurrently they take about as long as the slowest one, 0.08 seconds. Nothing was computed faster; the waiting overlapped.

## Pitfalls

- **Creating a `MongoClient` per request or per function call.**
- **Querying `_id` with a string** when it is an `ObjectId`, or returning a raw `ObjectId` in a JSON response.
- **Naive datetimes**: storing local times without a zone, or forgetting that returned datetimes are UTC.
- **Forgetting `await`** on an async driver call.
- **Calling the synchronous driver inside async code**, blocking the event loop.
- **Trusting application validation alone** when other writers exist.
- **`list(collection.find())` on a large collection**, loading everything into memory. Iterate, or limit.
- **`except Exception: pass`** around database calls.
- **Passing a `Decimal`** directly: convert to `Decimal128`.

## Cheat sheet

| task | PyMongo (sync) | async client |
|---|---|---|
| connect | `MongoClient(uri)` | `AsyncMongoClient(uri)` |
| insert | `c.insert_one(d)` | `await c.insert_one(d)` |
| find one | `c.find_one(f)` | `await c.find_one(f)` |
| iterate | `for d in c.find(f):` | `async for d in c.find(f):` |
| all results | `list(c.find(f).limit(n))` | `await c.find(f).limit(n).to_list()` |
| update | `c.update_one(f, u)` | `await c.update_one(f, u)` |
| many operations | `c.bulk_write([...])` | `await c.bulk_write([...])` |
| run together | threads | `await asyncio.gather(a, b)` |

| Pydantic | purpose |
|---|---|
| `class M(BaseModel)` | declare a model |
| `Field(ge=0, min_length=1)` | constraints |
| `Field(alias="_id")` | read and write under another key |
| `M.model_validate(doc)` | validate a dictionary |
| `m.model_dump()` | convert to a dictionary |
| `ValidationError` | raised with every problem listed |

## Summary

- PyMongo is the official driver; create one `MongoClient` and share it, since it owns the connection pool.
- CRUD methods mirror the shell with underscore names; `bulk_write` batches operations; catch specific exceptions.
- `ObjectId` and string are different types, and dates are UTC: convert deliberately at the boundaries.
- Pydantic models declare and validate the shape of documents; an alias maps `id` to `_id`; a repository keeps database code in one place.
- Async drivers (Motor historically, PyMongo's `AsyncMongoClient` now) let one process overlap the waiting of many requests; every server call must be awaited.
- Combine application validation with database validators and unique indexes.

## Glossary

- **Driver** - a library that lets a programming language communicate with the database.
- **PyMongo** - the official MongoDB driver for Python.
- **Connection pool** - reusable open connections held by a client.
- **Type hint** - an annotation such as `year: int` stating the expected type of a value.
- **Pydantic** - a Python library for declaring and validating data models.
- **Model** - a class describing the fields and types of a kind of data.
- **Validation** - checking, and where safe converting, data against a declared shape.
- **Alias** - an alternative key name used when reading and writing a model's field.
- **Repository** - a class that encapsulates data access behind domain-level methods.
- **Synchronous / asynchronous** - blocking until a result arrives / pausing so other work can proceed.
- **Event loop** - the scheduler that runs asynchronous functions and switches between them while they wait.
- **`await`** - the keyword marking a point where an async function may pause.
- **Concurrency** - several tasks in progress during the same period.
- **Motor** - the older, separate async MongoDB driver for Python, now deprecated in favour of PyMongo's async API.

## Check yourself

```quiz
[
  {"q": "How many MongoClient objects should a typical web application create?",
   "options": ["One per request", "One per function", "One for the whole process, shared", "One per collection"],
   "answer": 2,
   "explain": "The client owns the connection pool; creating many wastes connections and handshakes."},
  {"q": "A URL contains the id 66f0a1c2e4b0a1b2c3d4e5f6. Which query finds the document?",
   "options": ["find_one({\"_id\": \"66f0a1c2e4b0a1b2c3d4e5f6\"})", "find_one({\"_id\": ObjectId(\"66f0a1c2e4b0a1b2c3d4e5f6\")})", "find_one({\"id\": 66})", "find_one(\"66f0a1c2e4b0a1b2c3d4e5f6\")"],
   "answer": 1,
   "explain": "The stored _id is an ObjectId, and a string never equals an ObjectId; convert first."},
  {"q": "What does Book(title=\"X\", year=\"2019\") do for a Pydantic field declared year: int?",
   "options": ["Raises an error", "Stores the string \"2019\"", "Converts the value to the integer 2019", "Sets year to None"],
   "answer": 2,
   "explain": "Pydantic performs unambiguous conversions such as a numeric string to an integer during validation."},
  {"q": "Why is the id field declared with alias=\"_id\" in a Pydantic model?",
   "options": ["MongoDB requires aliases", "Names beginning with an underscore are treated as private by Pydantic, so the model uses id and maps it to _id", "It makes queries faster", "Aliases encrypt the field"],
   "answer": 1,
   "explain": "The alias lets the model read and write the MongoDB key _id while exposing a normal attribute."},
  {"q": "What does using an async driver improve?",
   "options": ["The speed of each individual query", "How many requests one process can make progress on while each waits for the database", "The size of documents", "The durability of writes"],
   "answer": 1,
   "explain": "Async overlaps waiting time; it does not make the database answer any single query sooner."},
  {"q": "What happens if you write book = books.find_one({...}) without await when using an async client?",
   "options": ["It works normally", "book is a coroutine object, not the document", "The query runs twice", "The collection is locked"],
   "answer": 1,
   "explain": "Async methods return coroutines that must be awaited to obtain the result."},
  {"q": "Why is application-level validation alone not enough?",
   "options": ["Pydantic is unreliable", "Other writers such as scripts, other services or the shell bypass the application's checks", "MongoDB ignores validated data", "It slows down reads"],
   "answer": 1,
   "explain": "A $jsonSchema validator and unique indexes in the database cover every writer."},
  {"q": "Why should the synchronous MongoClient not be used inside an async def request handler?",
   "options": ["It is not installed", "Its blocking calls freeze the event loop, stalling every other request in the process", "It cannot connect to replica sets", "It returns wrong results"],
   "answer": 1,
   "explain": "A blocked event loop cannot switch to other tasks, so all concurrency is lost for the duration."}
]
```

> **Source:** beyond the book; original material. PyMongo documentation: https://pymongo.readthedocs.io/en/stable/ , PyMongo async API: https://www.mongodb.com/docs/languages/python/pymongo-driver/current/ , Motor documentation: https://motor.readthedocs.io/en/stable/ , Pydantic documentation: https://docs.pydantic.dev/latest/
