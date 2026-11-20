# Request bodies, responses and status codes

Path and query parameters carry small, flat values. Anything structured — a new user, an order with line
items, a batch of feature vectors for a model — travels in the **request body**, almost always as JSON.
On the way out, you want just as much control: which fields the client sees, which status code, which
headers. This lesson covers both directions.

## Declaring a body with a Pydantic model

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

app = FastAPI()

@app.post("/items/")
def create_item(item: Item):
    data = item.model_dump()
    if item.tax is not None:
        data["price_with_tax"] = item.price + item.tax
    return data
```

Because `item` is annotated with a `BaseModel` subclass, FastAPI will:

1. Read the body and parse it as JSON (invalid JSON → 422 with `"type": "json_invalid"`).
2. Validate it against `Item`: `name` and `price` required, the others optional, types coerced
   (`"9.5"` → `9.5` in Pydantic's default *lax* mode).
3. Give your function a real `Item` instance — attribute access, editor completion, type checking.
4. Add a JSON Schema for `Item` to OpenAPI, so `/docs` shows an example body.

A body like `{"name": "Hammer", "price": "abc"}` never reaches your code; the client gets:

```json
{"detail": [{"type": "float_parsing", "loc": ["body", "price"],
             "msg": "Input should be a valid number, unable to parse string as a number", "input": "abc"}]}
```

Here is the same mechanism, run directly with Pydantic:

```python-run
from pydantic import BaseModel, ValidationError

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

print(Item.model_validate({"name": "Hammer", "price": "9.5"}))       # lax: "9.5" -> 9.5

try:
    Item.model_validate({"price": "abc", "colour": "red"})
except ValidationError as e:
    # FastAPI wraps exactly these errors, prefixing loc with "body"
    for err in e.errors():
        print({"loc": ["body", *err["loc"]], "type": err["type"]})

print(Item.model_validate_json('{"name": "Saw", "price": 12}').model_dump())
```

Notice the unknown field `colour` was silently ignored — Pydantic's default is `extra="ignore"`. Set
`model_config = ConfigDict(extra="forbid")` to reject unknown fields (useful to catch client typos).

### Mixing body, path and query

FastAPI decides by type: Pydantic model → body, name in path → path, simple type → query.

```python
@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item, q: str | None = None):
    return {"item_id": item_id, **item.model_dump(), "q": q}
```

### Multiple bodies and singular body values

Two model parameters make FastAPI expect a JSON object keyed by parameter name:

```python
class User(BaseModel):
    username: str
    full_name: str | None = None

@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item, user: User, importance: Annotated[int, Body(gt=0)]):
    ...
# expects: {"item": {...}, "user": {...}, "importance": 5}
```

`Body()` turns a simple type into a body key instead of a query parameter. With a *single* model,
`Annotated[Item, Body(embed=True)]` makes FastAPI expect `{"item": {...}}` rather than the bare object.

### Nested models

Models compose. Lists, dicts, sets and other models nest arbitrarily, and validation errors report the
full path (`["body", "items", 2, "price"]`):

```python
class Image(BaseModel):
    url: HttpUrl
    name: str

class Offer(BaseModel):
    name: str
    items: list[Item]
    images: list[Image] | None = None
```

Lubanovic's chapter 3 notes the practical upshot: once your data shapes are models, FastAPI handles
parsing, checking and documenting them for you, and the same models can be passed between the book's
web, service and data layers.

## Response models: controlling the output

The return value of an endpoint is serialised to JSON. What fields end up in that JSON is something you
must control explicitly — the classic bug is returning a database user object and leaking its
`hashed_password`. FastAPI offers two ways to declare the output shape.

### Return type annotation

```python
class ItemOut(BaseModel):
    name: str
    price: float

@app.get("/items/{item_id}")
def read_item(item_id: int) -> ItemOut:
    return ItemOut(name="Hammer", price=9.5)
```

FastAPI uses the annotation to **validate** the return value, **filter** it to the declared fields,
**serialise** it and **document** it in OpenAPI.

### `response_model` parameter

When the function returns something different from what you want to declare (e.g. a dict or a database
object), use `response_model` in the decorator — it takes priority over the annotation:

```python
class UserIn(BaseModel):
    username: str
    password: str
    email: EmailStr

class UserOut(BaseModel):
    username: str
    email: EmailStr

@app.post("/users/", response_model=UserOut, status_code=201)
def create_user(user: UserIn) -> Any:
    saved = save_user(user)       # returns an object that also has hashed_password
    return saved                  # filtered down to username + email
```

Even though `saved` has more attributes, the client receives only `username` and `email`. This
**filtering** is a security feature. A common pattern (used by the SQLModel tutorial as well) is a family
of models: `UserBase` with shared fields, `UserCreate(UserBase)` adding `password`, `UserPublic(UserBase)`
adding `id`, `UserInDB(UserBase)` adding `hashed_password`.

```python-run
from pydantic import BaseModel

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: int
    hashed_password: str

class UserPublic(UserBase):
    id: int

stored = UserInDB(id=1, username="ann", email="ann@example.com", hashed_password="$argon2id$...")
# What FastAPI does with response_model=UserPublic: validate from the object's attributes, drop extras
public = UserPublic.model_validate(stored.model_dump())
print(public.model_dump_json())
```

### Trimming defaults and unset fields

Decorator options shape the JSON further:

- `response_model_exclude_unset=True` — omit fields that were never explicitly set (great for sparse
  documents).
- `response_model_exclude_none=True` — omit `None` values.
- `response_model_include={"name"}` / `response_model_exclude={"tax"}` — quick ad-hoc filters (prefer
  separate models for anything permanent).

## Status codes

Set the default success status in the decorator:

```python
from fastapi import status

@app.post("/items/", status_code=status.HTTP_201_CREATED)
def create_item(item: Item) -> Item: ...

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int) -> None: ...
```

For **errors**, raise `HTTPException`:

```python
from fastapi import HTTPException

@app.get("/items/{item_id}")
def read_item(item_id: int) -> Item:
    item = items.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found",
                            headers={"X-Error": "missing-item"})
    return item
```

Raising (not returning) matters: it immediately aborts the endpoint *and* any calling helper functions,
so deep service code can signal "not found" without threading return values back up. (The book argues
for keeping HTTP details in the web layer, so its service layer raises domain exceptions like
`Missing`, which the web layer translates into `HTTPException` — more in the layers lesson.)

To choose the status *dynamically* (e.g. 200 if updated, 201 if created), declare a `Response`
parameter and set `response.status_code`:

```python
from fastapi import Response

@app.put("/items/{item_id}")
def upsert(item_id: int, item: Item, response: Response) -> Item:
    if item_id not in items:
        response.status_code = status.HTTP_201_CREATED
    items[item_id] = item
    return item
```

## Response headers and cookies

The same injected `Response` lets you add headers and cookies while still returning data normally:

```python
@app.get("/report")
def report(response: Response):
    response.headers["Cache-Control"] = "max-age=60"
    response.set_cookie(key="seen_report", value="yes", httponly=True, secure=True, samesite="lax")
    return {"ok": True}
```

## Returning a Response directly

You can bypass serialisation entirely by returning a `Response` (or subclass). FastAPI sends it as-is —
no `response_model` validation or filtering:

```python
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse, RedirectResponse

@app.get("/legacy")
def legacy():
    return JSONResponse(status_code=200, content={"old": True}, headers={"Deprecation": "true"})

@app.get("/go")
def go():
    return RedirectResponse("/docs")
```

Use this for non-JSON responses (HTML, CSV, images), redirects, or fine-grained control. For streaming
and files see the files/streaming module. `response_class=ORJSONResponse` or `HTMLResponse` on the
decorator changes the default response type and its documented media type.

> [!INTERVIEW]
> "How do you prevent an API from leaking sensitive fields like password hashes?" — Never return internal
> objects unfiltered. Declare an output schema (`response_model=UserPublic` or a return annotation); FastAPI
> validates the return value against it and drops any field not declared. Keep separate input, storage and
> output models so a sensitive field can only exist where it belongs. Add a test asserting the field is
> absent from the JSON.

## What really happens to your return value

1. If you returned a `Response`, it is sent unchanged.
2. Otherwise, if there is a response model, FastAPI validates the value against it (a mismatch is a
   **server** bug → 500 `ResponseValidationError`, not a 422).
3. The validated data is serialised with Pydantic (`model_dump(mode="json")` semantics: datetimes to ISO
   strings, UUIDs to strings, etc.), or with `jsonable_encoder` when there is no model.
4. The bytes are wrapped in a `JSONResponse` with your status code and headers.

```python-run
from datetime import datetime, timezone
from uuid import UUID
from pydantic import BaseModel

class Prediction(BaseModel):
    id: UUID
    label: str
    score: float
    created_at: datetime

p = Prediction(id=UUID(int=42), label="cat", score=0.97,
               created_at=datetime(2025, 1, 15, 9, 30, tzinfo=timezone.utc))
print(p.model_dump())               # Python objects
print(p.model_dump(mode="json"))    # JSON-compatible types: what goes on the wire
```

## Pitfalls

- Returning ORM/DB objects without a response model → leaks fields, or fails serialisation.
- Using `return HTTPException(...)` instead of `raise` — you just return an exception object as JSON.
- Forgetting that a response model mismatch produces a 500, which is *your* bug.
- Declaring `status_code=204` but returning a body.
- Reusing one model for input and output, then adding a sensitive field to it later.

## Summary

- A `BaseModel` parameter is the JSON body: parsed, validated, documented, given to you as an object.
- `Body()` handles singular values and embedding; models nest freely.
- Declare outputs with a return annotation or `response_model` — it validates, **filters** and documents.
- Use input/stored/public model families to keep secrets out of responses.
- `status_code=` for defaults, `HTTPException` for errors, an injected `Response` for dynamic status,
  headers and cookies, or return a `Response` subclass for full control.

```quiz
[
  {"q": "A parameter annotated with a Pydantic BaseModel (no marker) is read from:", "options": ["The query string", "The JSON request body", "Headers", "Path"], "answer": 1,
   "explain": "FastAPI treats model-typed parameters as the request body by default."},
  {"q": "Your endpoint returns a DB object containing hashed_password with response_model=UserPublic (no such field). What does the client get?", "options": ["All fields including the hash", "A 422 error", "Only fields declared in UserPublic", "A 500 error"], "answer": 2,
   "explain": "The response model filters output to declared fields, which is why separate public models prevent leaks."},
  {"q": "What status code does a failed response-model validation produce?", "options": ["422", "400", "500", "200 with warnings"], "answer": 2,
   "explain": "The client's request was fine; the server produced invalid output, so it is a server error (ResponseValidationError → 500)."},
  {"q": "How do you make a single model expect {\"item\": {...}} instead of the bare object?", "options": ["item: Item = Query()", "item: Annotated[Item, Body(embed=True)]", "response_model_exclude_unset=True", "item: dict"], "answer": 1,
   "explain": "Body(embed=True) wraps the body under a key named after the parameter."},
  {"q": "Why raise HTTPException rather than return it?", "options": ["Returning is slower", "Raising aborts execution immediately, even from nested helper functions, and FastAPI converts it into an error response", "Returned exceptions become 404s", "There is no difference"], "answer": 1,
   "explain": "A returned exception object would simply be serialised as data with status 200. Raising unwinds the stack to FastAPI's handler."},
  {"q": "What is Pydantic's default behaviour for unknown fields in the body?", "options": ["Reject with 422", "Ignore them", "Keep them as attributes", "Raise a 500"], "answer": 1,
   "explain": "The default extra='ignore' drops unknown fields; use extra='forbid' to reject them."},
  {"q": "If you return a JSONResponse object directly, which is true?", "options": ["response_model filtering still applies", "It is sent as-is without response_model validation", "FastAPI converts it to a dict first", "It must be wrapped in HTTPException"], "answer": 1,
   "explain": "Returning a Response bypasses FastAPI's serialisation and response-model handling entirely."}
]
```

> **Source:** Lubanovic, *FastAPI*, ch. 3 "FastAPI Tour" (Body, HTTP Responses, Status Code, Headers, Response Types, Model Types and response_model); https://fastapi.tiangolo.com/tutorial/body/, /tutorial/response-model/, /tutorial/extra-models/, /tutorial/response-status-code/, /tutorial/handling-errors/, /advanced/response-directly/
