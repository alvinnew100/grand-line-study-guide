# REST design and JSON

HTTP gives you verbs, paths and status codes. **REST** is a set of conventions for combining them into an
API that other developers can guess. **JSON** is the format almost every such API speaks. Together they
are the "contract" your FastAPI service exposes — and changing a contract after clients depend on it is
expensive, so it pays to design it deliberately.

## Where REST comes from

REST (*Representational State Transfer*) was described by Roy Fielding in his 2000 dissertation as the
architectural style of the web itself. Its formal constraints are: client–server separation,
statelessness, cacheability, a uniform interface, a layered system, and (optionally) code on demand. In
everyday API work, "RESTful" has come to mean something simpler, which Lubanovic summarises in his
chapter on the web layer:

- **Resources** — the nouns your application manages (users, items, models, predictions).
- **IDs** — unique identifiers for individual resources.
- **URLs** — structured strings combining resource names and IDs.
- **Verbs** — HTTP methods that say what to do with them.

The core pattern is two URL shapes:

| Request | Meaning |
|---|---|
| `GET /items` | list items (with filtering/pagination via query) |
| `POST /items` | create a new item → `201 Created` + `Location: /items/42` |
| `GET /items/42` | read item 42 |
| `PUT /items/42` | replace item 42 |
| `PATCH /items/42` | partially update item 42 |
| `DELETE /items/42` | delete item 42 → `204 No Content` |

Notice the URL names **things**, never actions. `POST /createItem` or `GET /getItem?id=42` are RPC-style
and lose the benefits of the uniform interface (caches, tooling, predictability).

> [!NOTE]
> Lubanovic deliberately uses *singular* resource names in his book (`/explorer`, `/creature`) because
> English plurals are irregular (series, fish, people). The more common industry convention is plural
> (`/explorers`). Either is fine — **consistency** is what matters. This track uses plurals.

### Nested resources and relationships

Sub-resources express ownership: `GET /users/7/orders` lists orders belonging to user 7. Keep nesting
shallow (one level is usually enough); `GET /orders/99` should still work directly. Deep URLs like
`/a/1/b/2/c/3/d/4` are hard to evolve.

### Actions that don't fit CRUD

Some operations are not naturally create/read/update/delete: "cancel an order", "retrain a model",
"send a password reset". Common patterns:

1. Model the action as a **state change**: `PATCH /orders/99` with `{"status": "cancelled"}`.
2. Model it as creating a **resource**: `POST /orders/99/cancellations`, `POST /models/3/training-jobs`
   (which returns `202 Accepted` and a job you can poll).
3. As a last resort, a verb sub-path: `POST /orders/99:cancel` (Google's API style guide uses this).

For ML services the second pattern is common: `POST /predictions` creates a prediction resource; long
jobs return `202` with `GET /jobs/{id}` for status.

## Filtering, sorting and pagination

Collections need query parameters:

```text
GET /items?category=tools&min_price=5&sort=-price&limit=20&offset=40
```

- **Filtering**: one parameter per field, or a small query language for complex needs.
- **Sorting**: `sort=price` ascending, `sort=-price` descending, comma-separated for multiple keys.
- **Pagination**: either `limit`/`offset` (simple, but slow and unstable on huge, changing tables) or a
  **cursor** (`?after=eyJpZCI6NDJ9` — an opaque token encoding the last seen key; fast and stable).

Always **cap** the page size server-side. A client asking for `limit=1000000` should get your maximum,
not a memory spike. The *Pagination Metadata* problem in the project-structure module builds this helper.

A typical paginated response envelope:

```json
{
  "items": [{"id": 41, "name": "hammer"}, {"id": 42, "name": "wrench"}],
  "total": 95,
  "limit": 20,
  "offset": 40,
  "next": "/items?limit=20&offset=60"
}
```

## Errors as part of the contract

Clients need errors they can parse. FastAPI's defaults are a good baseline:

```json
{"detail": "Item not found"}
```

for an `HTTPException`, and for validation failures (422):

```json
{
  "detail": [
    {"type": "int_parsing", "loc": ["path", "item_id"], "msg": "Input should be a valid integer, unable to parse string as an integer", "input": "abc"}
  ]
}
```

`loc` tells the client *where* (path/query/header/body plus field path), `type` is a stable
machine-readable code, `msg` is for humans. Many teams adopt **RFC 9457 "Problem Details"**
(`application/problem+json` with `type`, `title`, `status`, `detail`, `instance`) for a standard error shape.
Whatever you pick, use it everywhere.

## Versioning

APIs change. Options:

- **URL versioning**: `/v1/items`, `/v2/items`. Most visible and the easiest to route (an `APIRouter`
  per version). The most common choice.
- **Header versioning**: `Accept: application/vnd.example.v2+json` or `API-Version: 2`. Cleaner URLs,
  harder to test in a browser.
- **Additive evolution**: avoid breaking changes altogether — add optional fields, never rename or remove,
  never change types. Clients must ignore unknown fields.

For ML APIs, versioning has two axes: the **API schema** version and the **model** version. A
`/v1/predict` endpoint may serve model 2024-11-03 today and 2025-01-15 tomorrow; return the model
version in the response so results are traceable (see the final module).

> [!INTERVIEW]
> "How would you make a breaking change to a public API?" — Add the new behaviour under a new version
> (`/v2`) or as an additive optional field; keep the old version running; announce a deprecation window;
> mark the old endpoints `deprecated=True` in OpenAPI (FastAPI supports this per route) and return
> `Deprecation`/`Sunset` headers; monitor traffic on the old version until it reaches zero; then remove.

## JSON in depth

JSON (RFC 8259) has exactly six value types: **object**, **array**, **string**, **number**, `true`/`false`,
and `null`. That simplicity is why it won over XML — and it is also the source of every serialisation
headache, because your Python objects are richer:

| Python | JSON | Gotcha |
|---|---|---|
| `dict` | object | keys must be strings |
| `list`, `tuple` | array | tuples come back as lists |
| `str` | string | must be valid Unicode |
| `int`, `float` | number | `NaN`/`Infinity` are **not** valid JSON; JavaScript loses precision above 2^53 |
| `True`/`False`/`None` | `true`/`false`/`null` | |
| `datetime` | — | must be converted (ISO 8601 string) |
| `Decimal`, `UUID`, `set`, `bytes` | — | must be converted |

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

FastAPI handles most of this for you: when you return a Pydantic model or a dict containing datetimes,
UUIDs or Decimals, it serialises them through Pydantic (or `jsonable_encoder`). But you should know
*that* a conversion happens, so you are not surprised that a `datetime` arrives at the client as
`"2025-01-15T09:30:00"` and a `Decimal` might become a string or float depending on settings.

> [!WARNING]
> IDs larger than 2^53 (e.g. Twitter/X snowflake IDs, some database bigints) silently lose precision in
> JavaScript clients. Serialise such IDs as **strings**.

### Naming and shape conventions

- Pick one casing for field names. Python code uses `snake_case`; many JavaScript clients prefer
  `camelCase`. Pydantic **aliases** (`alias_generator=to_camel`) let you keep snake_case in Python and
  emit camelCase on the wire.
- Return objects at the top level, not bare arrays, so you can add metadata later without a breaking change.
- Use ISO 8601 with time zone for timestamps (`2025-01-15T09:30:00Z`).
- Use `null` deliberately: "absent" and "explicitly null" can mean different things for `PATCH`.

## Alternatives you should be able to name

Lubanovic's first chapter surveys other API styles; know when they beat REST+JSON:

- **JSON:API** — a specification standardising REST response envelopes, relationships and pagination.
- **GraphQL** — the client sends a query describing exactly which fields (and nested relations) it wants;
  one endpoint, no over-fetching. Great for complex UIs; harder to cache and to protect from expensive
  queries.
- **gRPC** — binary Protocol Buffers over HTTP/2 with generated clients; fast and strongly typed; common
  between internal microservices and for high-throughput model serving.
- **WebSockets / Server-Sent Events** — long-lived connections for push and streaming (covered later).

## A worked design: a model-registry API

Suppose you must design an API for managing ML models and getting predictions:

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

Every URL is a noun; the verbs come from HTTP; long-running work is a resource you can poll; versions are
in the path.

## Worked trace: one resource through its whole life

Following a single item from creation to deletion shows how the conventions fit together. Each step lists
the request, the response and the rule it demonstrates.

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

Steps 4 and 5 are **optimistic concurrency control**: the client proves it has seen the latest version by
sending the ETag back in `If-Match`. Two users editing the same record can no longer silently overwrite
each other (the "lost update" problem); the loser receives `412` and must re-read. It costs nothing but a
header comparison, and it's the answer interviewers want when they ask how to handle concurrent edits
without locks.

## Offset versus cursor pagination, concretely

The weakness of offset pagination is easiest to see by running it against data that changes between page
requests:

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

With offsets, deleting one earlier row shifts everything up, so the client never sees item 4 (an insert
would cause a duplicate instead). The cursor version asks "what comes after the last thing I saw?", which
stays correct however the table changes — and the database answers it with an index seek instead of
scanning and discarding `offset` rows. The cursor is opaque (base64) so clients can't depend on its
contents, leaving you free to change the sort key later. The trade-off: cursors can't jump to "page 17",
and they need a stable, unique sort key (add `id` as a tie-breaker when sorting by a non-unique column).

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
