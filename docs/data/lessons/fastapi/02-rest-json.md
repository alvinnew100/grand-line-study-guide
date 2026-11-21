# REST design and JSON

> **Before this lesson:** you should know what a request, a response, a method, a status code and a
> header are. All of that is in lesson 1, [HTTP: methods, status codes and headers](#/lesson/fastapi/http-basics).
> Basic Python dictionaries and lists are enough for the code.

## In plain words

Lesson 1 gave you the vocabulary of HTTP: verbs such as `GET` and `POST`, addresses, and status codes.
Vocabulary alone does not tell you how to arrange an API. Two teams could build the same feature with
completely different addresses and verbs, and anyone using both would have to learn each from scratch.

**REST** is a set of habits for arranging an API so that other programmers can guess how it works
before reading the manual. **JSON** is the text format in which almost every such API sends its data.

An everyday picture: a library. Every book has a shelf mark, and the shelf marks follow one system.
Once you know the system you can find any book in any library that uses it, and the things you may do
with a book are the same few everywhere: look at it, add one, replace one, remove one. REST gives every
"thing" in your program a shelf mark (an address) and limits you to a small fixed set of actions (the
HTTP methods). JSON is the common language the catalogue cards are written in.

Why this matters for a job: the addresses, methods, field names and error shapes of your API form a
**contract**, a promise that other programs are written against. Phone apps and other teams' services
depend on it, and changing it later breaks them. "Design a REST API for X" is among the most common
interview exercises, and this lesson is the checklist for answering it.

## Where REST comes from

REST stands for *Representational State Transfer*. Roy Fielding introduced the term in his doctoral
thesis in 2000 to describe the way the web itself is organised. The formal definition lists six
constraints (client and server are separate programs, requests are stateless, answers can be cached,
every resource is handled through one uniform interface, intermediaries may sit in between, and
servers may optionally send code to the client). You rarely need to recite them. In everyday work,
calling an API "RESTful" means it is built from four ingredients, which Lubanovic summarises in his
chapter on the web layer:

- **Resources**: the nouns your application manages (users, items, models, predictions).
- **IDs**: an **identifier** is a value that picks out exactly one resource, such as the number `42`.
- **URLs**: addresses built from resource names and IDs.
- **Verbs**: the HTTP methods, which say what to do with the resource.

The whole pattern rests on two address shapes. `/items` is the **collection** (all items), and
`/items/42` is one member of it.

| Request | Meaning |
|---|---|
| `GET /items` | list items (with filtering/pagination via query) |
| `POST /items` | create a new item → `201 Created` + `Location: /items/42` |
| `GET /items/42` | read item 42 |
| `PUT /items/42` | replace item 42 |
| `PATCH /items/42` | partially update item 42 |
| `DELETE /items/42` | delete item 42 → `204 No Content` |

These rows are the four basic things you can do with stored data, known by the acronym **CRUD**:
Create (`POST`), Read (`GET`), Update (`PUT` or `PATCH`) and Delete (`DELETE`).

Notice that the address names a **thing**, never an action. `POST /createItem` or `GET /getItem?id=42`
put the verb in the address, as a function call would. That style (RPC, from lesson 1) works, but it
throws away what the shared rules give you for free: caches know a `GET` can be stored, tools know a
`DELETE` removes something, and a newcomer can predict your addresses.

> [!NOTE]
> Lubanovic deliberately uses *singular* resource names in his book (`/explorer`, `/creature`) because
> English plurals are irregular (series, fish, people). The more common industry convention is plural
> (`/explorers`). Either is fine; **consistency** is what matters. This track uses plurals.

### Nested resources and relationships

Sometimes one resource belongs to another: an order belongs to a user. A nested address expresses
that: `GET /users/7/orders` lists the orders of user 7. Keep nesting shallow. One level is usually
enough, and `GET /orders/99` should still work on its own. Deep addresses such as
`/a/1/b/2/c/3/d/4` are hard to change later, because every client has the whole chain written into it.

### Actions that don't fit CRUD

Some operations are not naturally a create, read, update or delete: "cancel an order", "retrain a
model", "send a password reset". There are three common ways to fit them in, in order of preference:

1. Treat the action as a **change of state**: `PATCH /orders/99` with the body `{"status": "cancelled"}`.
2. Treat it as **creating a new resource**: `POST /orders/99/cancellations`, or
   `POST /models/3/training-jobs`. For slow work the server answers `202 Accepted` ("I have taken the
   job, it is not finished") and returns a job the client can ask about later.
3. As a last resort, a verb at the end of the path: `POST /orders/99:cancel` (Google's API style guide
   uses this form).

For machine-learning services the second pattern is the usual one: `POST /predictions` creates a
prediction, and long jobs return `202` plus a `GET /jobs/{id}` address for checking progress. Asking
repeatedly "is it done yet?" in this way is called **polling**.

## Filtering, sorting and pagination

A collection can hold millions of resources, so clients need ways to narrow, order and slice it.
Those controls go in the query string (the `key=value` pairs after the `?`):

```text
GET /items?category=tools&min_price=5&sort=-price&limit=20&offset=40
```

Reading that address piece by piece: only items in the `tools` category, costing at least 5, sorted by
price from highest to lowest, 20 results at a time, skipping the first 40.

- **Filtering**: one parameter per field (`category=tools`).
- **Sorting**: `sort=price` for ascending, `sort=-price` for descending; several keys separated by commas.
- **Pagination** means returning a long list in pages. There are two styles. `limit`/`offset` says
  "give me 20, skipping the first 40"; it is easy to build but becomes slow and unreliable on huge
  tables that change often. A **cursor** (`?after=eyJpZCI6NDJ9`) is a bookmark: a token that records
  the last item the client saw. It is fast and stays correct while data changes. Both are demonstrated
  further down.

Always **cap** the page size on the server. A client that asks for `limit=1000000` should receive your
maximum, not a server that runs out of memory. The *Pagination Metadata* problem in the
project-structure module builds this helper.

A paginated answer normally wraps the list in an **envelope**: a JSON object that holds the list plus
information about it.

```json
{
  "items": [{"id": 41, "name": "hammer"}, {"id": 42, "name": "wrench"}],
  "total": 95,
  "limit": 20,
  "offset": 40,
  "next": "/items?limit=20&offset=60"
}
```

`items` is the page itself, `total` is how many exist altogether, `limit` and `offset` echo what was
asked, and `next` is the ready-made address of the following page so the client does not have to
compute it.

## Errors as part of the contract

A client program has to react to errors without a person reading them, so errors need a predictable
shape too. FastAPI's defaults are a good starting point. When your code deliberately reports a problem
(with `HTTPException`, lesson 5) the body is:

```json
{"detail": "Item not found"}
```

When the incoming data fails FastAPI's automatic checking, the status is `422` and the body lists
every failure:

```json
{
  "detail": [
    {"type": "int_parsing", "loc": ["path", "item_id"], "msg": "Input should be a valid integer, unable to parse string as an integer", "input": "abc"}
  ]
}
```

Three keys do the work. `loc` (location) says *where* the bad value was: here in the path, in the
part named `item_id`. `type` is a short stable code that programs can compare against. `msg` is a
sentence for people. `input` echoes what was received.

Many teams adopt a published standard for the error body. Internet standards are published as numbered
documents called **RFCs** (Request for Comments), and **RFC 9457 "Problem Details"** defines an error
object with the fields `type`, `title`, `status`, `detail` and `instance`, sent with the media type
`application/problem+json`. Whichever shape you choose, use it for every error in the API.

## Versioning

APIs change after release, and old clients keep running. **Versioning** is how you change the contract
without breaking them. The options:

- **URL versioning**: `/v1/items`, `/v2/items`. The most visible, the easiest to direct to different
  code (one `APIRouter` per version, lesson 14), and the most common choice.
- **Header versioning**: `Accept: application/vnd.example.v2+json` or `API-Version: 2`. The addresses
  stay clean, but it is harder to try out in a browser.
- **Additive evolution**: avoid breaking changes altogether. Add optional fields; never rename or
  remove a field; never change a field's type. This only works if clients ignore fields they do not
  recognise.

For machine-learning APIs there are two version numbers to track: the version of the **API shape** and
the version of the **model** behind it. `/v1/predict` may be answered by the model trained on
2024-11-03 today and the one from 2025-01-15 tomorrow. Return the model version in the response so
that any result can be traced back (see the final module).

> [!INTERVIEW]
> "How would you make a breaking change to a public API?" — Add the new behaviour under a new version
> (`/v2`) or as an additive optional field; keep the old version running; announce a deprecation window
> (*deprecated* means "still works, scheduled for removal"); mark the old endpoints `deprecated=True`
> in the generated docs (FastAPI supports this per route) and return `Deprecation`/`Sunset` headers;
> watch traffic on the old version until it reaches zero; then remove it.

## JSON in depth

JSON is defined in RFC 8259 and has exactly six kinds of value:

- an **object**: `{"name": "wrench", "price": 9.5}`, which Python calls a dictionary;
- an **array**: `[1, 2, 3]`, which Python calls a list;
- a **string** in double quotes: `"wrench"`;
- a **number**: `42` or `9.5`;
- `true` or `false`;
- `null`, meaning "no value" (Python's `None`).

That small list is why JSON replaced the older, heavier XML format. It is also the cause of most
conversion trouble, because Python has more kinds of value than JSON does. Turning a Python object
into JSON text is called **serialisation**; the reverse is **deserialisation** or parsing.

| Python | JSON | Gotcha |
|---|---|---|
| `dict` | object | keys must be strings |
| `list`, `tuple` | array | tuples come back as lists |
| `str` | string | must be valid Unicode |
| `int`, `float` | number | `NaN`/`Infinity` are **not** valid JSON; JavaScript loses precision above 2^53 |
| `True`/`False`/`None` | `true`/`false`/`null` | |
| `datetime` | — | must be converted (ISO 8601 string) |
| `Decimal`, `UUID`, `set`, `bytes` | — | must be converted |

Run the conversions and watch where they succeed and where they fail:

```python-run
import json, datetime, uuid, decimal

data = {"id": 1, "tags": ("a", "b"), "ok": True, "missing": None}
s = json.dumps(data)
print(s)
print(json.loads(s))          # tuple came back as a list

try:
    json.dumps({"when": datetime.datetime(2025, 1, 15, 9, 30)})
except TypeError as e:
    print("TypeError:", e)

# A default= hook converts unknown types - FastAPI's jsonable_encoder does this (and more).
def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    if isinstance(o, (uuid.UUID, decimal.Decimal)):
        return str(o)
    if isinstance(o, set):
        return sorted(o)
    raise TypeError(f"not serialisable: {type(o).__name__}")

print(json.dumps({"when": datetime.datetime(2025, 1, 15, 9, 30),
                  "id": uuid.UUID(int=7), "price": decimal.Decimal("9.99"),
                  "tags": {"b", "a"}}, default=default))

print("NaN is emitted by Python but is NOT valid JSON:", json.dumps(float("nan")))
print("big int precision in JS ends at", 2**53)
```

Walking through it:

- `json.dumps(data)` ("dump to string") serialises a dictionary. In the printed text the tuple
  `("a", "b")` has become `["a", "b"]`, `True` has become `true` and `None` has become `null`.
- `json.loads(s)` ("load from string") parses the text back. The tags are now a *list*: JSON has no
  tuple, so the difference is lost on the round trip.
- The `try` block attempts to serialise a `datetime`. JSON has no date type, so Python raises
  `TypeError: Object of type datetime is not JSON serializable`, and the `except` branch prints it.
- `default` is a function that `json.dumps` calls for any value it does not know how to write. This one
  turns dates into ISO text (ISO 8601 is the international standard layout `2025-01-15T09:30:00`),
  turns a **UUID** (a 128-bit random-looking identifier) and a `Decimal` (an exact decimal number, used
  for money) into strings, and turns a set into a sorted list.
- The last two lines show traps. Python will happily write `NaN` ("not a number"), which is not legal
  JSON, and `2**53` (9007199254740992) is the largest range in which JavaScript can count whole numbers
  exactly.

FastAPI handles most of this for you: when your function returns data containing datetimes, UUIDs or
Decimals, FastAPI converts them (through Pydantic, the library covered in lesson 7, or its helper
`jsonable_encoder`). You should still know *that* a conversion happens, so that it is no surprise when
a `datetime` reaches the client as the string `"2025-01-15T09:30:00"`, or a `Decimal` arrives as a
string or a float depending on settings.

> [!WARNING]
> IDs larger than 2^53 (for example the "snowflake" IDs used by some social networks, or large database
> integers) silently lose precision in JavaScript clients. Send such IDs as **strings**.

### Naming and shape conventions

- Pick one letter-case style for field names. Python code uses `snake_case`; many JavaScript clients
  prefer `camelCase`. Pydantic **aliases** (an alias is a second, external name for a field) let you
  keep snake_case in Python and send camelCase to clients.
- Return an object at the top level, not a bare array, so that you can add fields later without
  breaking anyone.
- Write timestamps in ISO 8601 with a time zone (`2025-01-15T09:30:00Z`; the `Z` means UTC).
- Use `null` deliberately: "field absent" and "field present and null" can mean different things in a
  `PATCH`.

## Alternatives you should be able to name

Lubanovic's first chapter surveys other API styles. An interviewer may ask when each beats REST with
JSON:

- **JSON:API**: a specification that standardises envelopes, relationships and pagination for REST
  APIs, so that teams do not each invent their own.
- **GraphQL**: the client sends a query listing exactly the fields (and related objects) it wants,
  to a single endpoint. This avoids fetching unneeded data and suits complicated screens; it is harder
  to cache and to protect against expensive queries.
- **gRPC**: a compact binary format (Protocol Buffers) over HTTP/2, with client code generated
  automatically. It is fast and strictly typed, and is common between a company's internal services
  and for high-volume model serving.
- **WebSockets / Server-Sent Events**: connections that stay open so the server can push data
  (lesson 24).

## A worked design: a model-registry API

Suppose you are asked to design an API for storing machine-learning models and getting predictions
from them. Applying the rules above gives:

```text
GET    /v1/models                       list models (?task=classification&limit=20)
POST   /v1/models                       register a model           -> 201 + Location
GET    /v1/models/{model_id}            model metadata
PATCH  /v1/models/{model_id}            update description/tags
DELETE /v1/models/{model_id}            archive                    -> 204
GET    /v1/models/{model_id}/versions   list versions
POST   /v1/models/{model_id}/predictions   run inference          -> 200 (sync)
POST   /v1/batch-jobs                   start batch scoring        -> 202 + job id
GET    /v1/batch-jobs/{job_id}          poll job status
```

Every address is a noun; the verbs come from HTTP; slow work (`batch-jobs`) is a resource the client
can poll; the version is in the path. The curly braces, as in `{model_id}`, mark a path parameter: a
slot that is filled with a real ID in an actual request.

## Worked trace: one resource through its whole life

Following a single item from creation to deletion shows how the conventions fit together. Each step
lists the request, the response and the rule it demonstrates.

```text
1. POST /v1/items                      {"name": "wrench", "price": 9.5}
   -> 201 Created   Location: /v1/items/42   ETag: "a1"      body: the new item
2. GET /v1/items/42
   -> 200 OK        ETag: "a1"   Cache-Control: private, max-age=30
3. GET /v1/items/42                    If-None-Match: "a1"
   -> 304 Not Modified (no body)                              conditional read
4. PATCH /v1/items/42                  If-Match: "a1"   {"price": 11.0}
   -> 200 OK        ETag: "b7"                                optimistic concurrency
5. PATCH /v1/items/42                  If-Match: "a1"   {"price": 12.0}
   -> 412 Precondition Failed                                 someone else changed it first
6. DELETE /v1/items/42
   -> 204 No Content
7. GET /v1/items/42
   -> 404 Not Found
8. DELETE /v1/items/42
   -> 404 Not Found (state is unchanged: DELETE is still idempotent)
```

Steps 1 to 3 are lesson 1 in action: `201` with a `Location` header, then a cached read confirmed with
the ETag fingerprint. Steps 4 and 5 add something new, **optimistic concurrency control**. The header
`If-Match: "a1"` means "apply this change only if the item still has fingerprint a1". In step 4 it
does, so the change is applied and the fingerprint becomes `b7`. In step 5 a client that still holds
the old fingerprint tries to write; the server sees the mismatch and answers
`412 Precondition Failed`. Without this check, two people editing the same record would silently
overwrite each other (the **lost update** problem). With it, the slower one is told to re-read first.
The method is called "optimistic" because it does not lock the record in advance; it assumes clashes
are rare and detects them when they happen. It costs one header comparison, and it is the answer
interviewers hope for when they ask how to handle simultaneous edits without locks.

Steps 6 to 8 show that a second `DELETE` gets `404`, yet the stored data is the same as after the
first: that is idempotency.

## Offset versus cursor pagination, concretely

The weakness of offset pagination is easiest to see by running it against data that changes between
two page requests:

```python-run
import base64, json

rows = [{"id": i, "name": f"item-{i}"} for i in range(1, 11)]      # ids 1..10, newest last

def page_offset(data, limit, offset):
    return data[offset: offset + limit]

def page_cursor(data, limit, cursor=None):
    after = json.loads(base64.urlsafe_b64decode(cursor))["id"] if cursor else 0
    chunk = [r for r in data if r["id"] > after][:limit]              # WHERE id > :after ORDER BY id LIMIT :n
    nxt = base64.urlsafe_b64encode(json.dumps({"id": chunk[-1]["id"]}).encode()).decode() if chunk else None
    return chunk, nxt

# --- offset: read page 1, then a row is deleted, then read page 2 ---
p1 = page_offset(rows, 3, 0)
rows_after_delete = [r for r in rows if r["id"] != 2]                # someone deletes id 2
p2 = page_offset(rows_after_delete, 3, 3)
print("offset pages:", [r["id"] for r in p1], [r["id"] for r in p2], "<- id 4 was skipped!")

# --- cursor: same scenario ---
c1, cur = page_cursor(rows, 3)
c2, _ = page_cursor(rows_after_delete, 3, cur)
print("cursor pages:", [r["id"] for r in c1], [r["id"] for r in c2], "<- nothing skipped")
print("opaque cursor the client sees:", cur)
```

How to read the demo:

- `rows` is ten small dictionaries with ids 1 to 10, standing in for a database table.
- `page_offset` slices the list: skip `offset` rows, take `limit` rows.
- `page_cursor` first decodes the cursor to learn the last id the client saw (0 when there is no
  cursor), keeps only rows with a larger id, and takes `limit` of them. It then builds the next
  cursor by writing `{"id": <last id>}` as JSON and encoding it in **base64**, a way of writing bytes
  using only letters, digits and a few symbols.
- In both scenarios the client reads page 1, somebody deletes row 2, and the client reads page 2.

The output is `offset pages: [1, 2, 3] [5, 6, 7]` and `cursor pages: [1, 2, 3] [4, 5, 6]`. With
offsets, deleting an earlier row shifts every later row up by one, so "skip 3" now skips item 4 and
the client never sees it (an insert would cause a duplicate instead). The cursor version asks "what
comes after the last thing I saw?", which stays correct however the table changes. A database can also
answer that question quickly, by jumping to the right place with an **index** (a lookup structure,
lesson 16) instead of reading and discarding `offset` rows.

The cursor is deliberately unreadable so that clients cannot depend on what is inside it, which leaves
you free to change the sort order later. The trade-offs: a cursor cannot jump straight to "page 17",
and it needs a sort key that is stable and unique (add `id` as a tie-breaker when sorting by a column
with repeated values).

## Design mistakes and how they show up

| Symptom reported by clients | Likely design mistake | Fix |
|---|---|---|
| "We got charged twice after a timeout" | non-idempotent `POST` retried | accept an `Idempotency-Key` header |
| "The mobile app broke after your release" | a field was renamed or its type changed | additive changes only; new version for breaking ones |
| "We can't tell a validation error from an outage" | every error is `400` or `500` with free text | precise codes plus a machine-readable error `type` |
| "The list endpoint times out" | unbounded collection | mandatory pagination with a capped `limit` |
| "Updates overwrite each other" | blind `PUT` | ETags with `If-Match` |
| "Dates are off by a few hours" | naive local timestamps | ISO 8601 in UTC with an explicit offset |

## Pitfalls

- Verbs in URLs (`/getUser`) and inconsistent pluralisation.
- Returning a bare JSON array from a list endpoint (no room for pagination metadata).
- Unbounded list endpoints.
- Leaking internal fields (password hashes, internal IDs) because you returned the database object
  directly — FastAPI's `response_model` exists to prevent this.
- Breaking changes without a version bump.

## Summary

- REST = resources identified by URLs, manipulated with HTTP methods, with stateless requests.
- Use the two URL shapes `/resources` and `/resources/{id}`; model awkward actions as state changes or new
  resources (jobs).
- Filtering, sorting and pagination go in the query string; cap page sizes.
- Errors are part of the contract: consistent shape, precise status codes.
- JSON has six types; datetimes, decimals, UUIDs and huge integers need deliberate conversion.

## Glossary

- **REST** — a style of API design: resources at URLs, acted on with HTTP methods, statelessly.
- **Contract** — the addresses, methods, fields and errors that clients rely on.
- **Resource / collection** — one thing the API exposes / the full set of things of one kind.
- **Identifier (ID)** — a value that picks out exactly one resource.
- **CRUD** — Create, Read, Update, Delete: the four basic operations on stored data.
- **Polling** — asking repeatedly whether a slow job has finished.
- **Pagination** — returning a long list one page at a time.
- **Offset / cursor** — "skip N rows" paging / a bookmark token that marks the last row seen.
- **Envelope** — a JSON object that wraps a list together with information about it.
- **RFC** — a numbered document that defines an internet standard.
- **Versioning / deprecated** — changing an API without breaking old clients / still working but
  scheduled for removal.
- **JSON object, array, null** — JSON's names for a dictionary, a list and "no value".
- **Serialisation** — converting an in-memory object to text or bytes (here, JSON).
- **ISO 8601** — the standard text layout for dates and times.
- **UUID** — a 128-bit identifier designed to be unique without central coordination.
- **Alias** — an alternative external name for a field.
- **Optimistic concurrency control** — detecting clashing edits with a version check (`If-Match`)
  instead of locking.
- **Lost update** — one writer silently overwriting another's change.
- **Base64** — a way to write arbitrary bytes using plain text characters.

```quiz
[
  {"q": "Which URL best follows REST conventions for cancelling order 99?", "options": ["GET /cancelOrder?id=99", "POST /orders/99/cancel-order-now", "PATCH /orders/99 with {\"status\": \"cancelled\"}", "DELETE /orders?cancel=99"], "answer": 2,
   "explain": "Modelling the action as a state change of the order resource keeps URLs as nouns and uses HTTP semantics. GET must never change state."},
  {"q": "What status and header should a successful POST /items return?", "options": ["200 with no headers", "201 Created with a Location header", "204 No Content", "202 Accepted with Retry-After"], "answer": 1,
   "explain": "201 indicates a new resource was created, and Location tells the client its URL."},
  {"q": "Why prefer returning {\"items\": [...]} instead of a bare JSON array from a list endpoint?", "options": ["Arrays are invalid JSON", "It allows adding pagination metadata later without breaking clients", "It is faster to parse", "FastAPI cannot return arrays"], "answer": 1,
   "explain": "An object envelope is extensible: total counts, next links and other metadata can be added without changing the top-level type."},
  {"q": "Which Python value has no valid JSON representation?", "options": ["None", "float('nan')", "a tuple", "an empty dict"], "answer": 1,
   "explain": "JSON has no NaN or Infinity. Python's json module emits NaN by default, but strict parsers will reject it. None maps to null; tuples become arrays."},
  {"q": "Why serialise very large integer IDs as strings?", "options": ["JSON forbids large numbers", "JavaScript numbers are doubles and lose integer precision above 2^53", "Strings compress better", "Pydantic requires it"], "answer": 1,
   "explain": "JSON allows big numbers, but JavaScript clients parse them into IEEE-754 doubles, silently rounding IDs beyond 2^53."},
  {"q": "What is the main weakness of limit/offset pagination on a huge, frequently updated table?", "options": ["It cannot be cached", "Large offsets are slow and inserts shift rows between pages", "It requires GraphQL", "It cannot be sorted"], "answer": 1,
   "explain": "The database must scan and skip offset rows, and concurrent inserts/deletes cause duplicates or gaps. Cursor (keyset) pagination avoids both."}
]
```

> **Source:** Lubanovic, *FastAPI*, ch. 1 "The Modern Web" (REST(ful), JSON and API Data Formats, JSON:API, GraphQL) and ch. 8 "Web Layer" (RESTful API Design, Pagination and Sorting); RFC 8259; RFC 9457; https://fastapi.tiangolo.com/tutorial/handling-errors/
