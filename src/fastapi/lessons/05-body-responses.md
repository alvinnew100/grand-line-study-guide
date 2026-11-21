# Request bodies, responses and status codes

> **Before this lesson:** you should be able to write a FastAPI endpoint with path and query
> parameters ([lesson 4](#/lesson/fastapi/first-app)) and know the common status codes and what JSON
> looks like ([lesson 1](#/lesson/fastapi/http-basics), [lesson 2](#/lesson/fastapi/rest-json)). In
> Python you need to have seen a `class` once; classes are used here only as a way to list fields.

## In plain words

Path and query parameters are fine for small single values such as an id or a page number. Anything
with structure (a new user with a name, an email and a password; an order with ten lines) will not fit
comfortably in an address. It travels in the **request body**: the block of content after the headers
in an HTTP message, almost always written as JSON.

The other half of the lesson is the reply. You decide which fields the client gets to see, which
status code is sent, and which headers.

An everyday picture: a parcel counter. A customer hands over a parcel with a customs form. The clerk
checks the form against the rules (is every required box filled? is the weight a number?) and refuses
it on the spot if something is wrong. Later, when a parcel is handed *out*, the clerk removes the
internal routing stickers so the customer sees only what is meant for them. In FastAPI the "customs
form" is a small class called a **model**, and one model describes what may come in while another
describes what may go out.

Why this matters for a job: nearly every real endpoint accepts or returns structured data, and the
most common security mistake in API code is sending out a field that should have stayed private, such
as a password hash. Interviewers ask about exactly this.

## Declaring a body with a Pydantic model

**Pydantic** is the Python library FastAPI uses for describing and checking data. You describe a
shape by writing a class that inherits from `BaseModel` and listing the fields with type hints. Such a
class is called a **model**.

```fastapi-run method=POST path=/items/
from fastapi import FastAPI
from fastapi.testclient import TestClient
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

client = TestClient(app)
print(client.post("/items/", json={"name": "Hammer", "price": 9.5, "tax": 0.5}).json())
r = client.post("/items/", json={"name": "Hammer", "price": "abc"})
print(r.status_code, r.json())
```

Reading it from the top:

- `class Item(BaseModel):` defines a model named `Item`.
- `name: str` is a required text field. `price: float` is a required number.
- `description: str | None = None` and `tax: float | None = None` are optional: they may be text (or a
  number) or absent, and default to `None`.
- `@app.post("/items/")` registers the function for `POST` requests, the method used for creating.
- `def create_item(item: Item):` has one parameter whose type hint is the model. That hint is the
  whole trick: because `Item` is a model, FastAPI knows the value must come from the body.
- `item.model_dump()` converts the model object into an ordinary dictionary. The function then adds a
  computed field when a tax was given, and returns the dictionary.
- The last four lines use the test client from lesson 4. `client.post(url, json=...)` sends a `POST`
  request whose body is the given dictionary, written out as JSON. The first request is valid and
  prints the stored item with `price_with_tax` added; the second sends text where a number belongs
  and prints `422` followed by the error explained below.

Press **Run**, then use the request panel under the code: its body box starts with an example built
from the `Item` model. Press **Send** once as it is, then delete the `"name"` line or give `price` the
value `"abc"`, send again, and read the 422.

Because of that single hint, FastAPI will:

1. Read the body and parse it as JSON. Text that is not legal JSON gives a 422 with
   `"type": "json_invalid"`.
2. Check the result against `Item`: `name` and `price` must be present, the others may be missing.
   Values are converted where that is sensible (`"9.5"` becomes `9.5`; Pydantic calls this tolerant
   default *lax mode*).
3. Hand your function a real `Item` object, an **instance** of the class, so you write `item.price`
   and your editor can complete the field names.
4. Add a description of `Item` to the automatic documentation, so `/docs` shows an example body.

A body such as `{"name": "Hammer", "price": "abc"}` never reaches your code. The client receives:

```json
{"detail": [{"type": "float_parsing", "loc": ["body", "price"],
             "msg": "Input should be a valid number, unable to parse string as a number", "input": "abc"}]}
```

The `loc` value `["body", "price"]` says the problem is in the body, in the field `price`.

Here is the same mechanism without a web server, using Pydantic directly. Run it:

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

Step by step:

- `Item.model_validate({...})` checks a dictionary against the model and returns an `Item`. The first
  call succeeds and prints `name='Hammer' description=None price=9.5 tax=None`: the text `"9.5"` was
  converted to a number.
- The second call has no `name`, a `price` that is not a number, and an unknown field `colour`.
  Pydantic raises `ValidationError`. The `except` block loops over `e.errors()` and prints each one
  the way FastAPI would report it. Two lines appear: `name` is `missing` and `price` is
  `float_parsing`. Both problems are reported at once.
- `model_validate_json` does the same starting from JSON text, and `.model_dump()` turns the result
  into a dictionary.

Notice what did *not* produce an error: the unknown field `colour` was dropped without comment.
Pydantic's default setting is `extra="ignore"`. Add `model_config = ConfigDict(extra="forbid")` to a
model to reject unknown fields, which is useful for catching spelling mistakes made by clients.

### Mixing body, path and query

One function can take all three kinds of input. FastAPI sorts them by the rule from lesson 4: a model
means body, a name in the path template means path, any other basic type means query.

```python
@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item, q: str | None = None):
    return {"item_id": item_id, **item.model_dump(), "q": q}
```

Here `item_id` comes from the path, `item` from the JSON body and `q` from the query string. The
`**item.model_dump()` in the return line unpacks the item's fields into the surrounding dictionary.

### Multiple bodies and singular body values

A request has only one body, so what happens when a function asks for two models? FastAPI then
expects a JSON object with one key per parameter:

```python
class User(BaseModel):
    username: str
    full_name: str | None = None

@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item, user: User, importance: Annotated[int, Body(gt=0)]):
    ...
# expects: {"item": {...}, "user": {...}, "importance": 5}
```

`Body()` is a marker like `Query()` and `Path()`. It says "this basic value lives in the body", which
is how `importance` (a plain integer that would otherwise be read from the query) joins the other
two. With a *single* model, `Annotated[Item, Body(embed=True)]` makes FastAPI expect
`{"item": {...}}` in place of the bare object.

### Nested models

Models can contain other models, and lists of them. When validation fails deep inside, the error
gives the full route to the bad value, such as `["body", "items", 2, "price"]` (the `price` of the
third item, since counting starts at 0):

```python
class Image(BaseModel):
    url: HttpUrl
    name: str

class Offer(BaseModel):
    name: str
    items: list[Item]
    images: list[Image] | None = None
```

`Offer` has a list of `Item` objects and an optional list of `Image` objects. `HttpUrl` is a Pydantic
type that accepts only well-formed web addresses.

Lubanovic's chapter 3 points out the practical result: once your data shapes are models, FastAPI
parses, checks and documents them for you, and the same models can be handed between the different
parts of a larger program (lesson 15).

## Response models: controlling the output

Whatever your function returns is converted to JSON. *Which fields* end up in that JSON is something
you must control on purpose. The classic bug is returning the stored record of a user and thereby
sending the client its `hashed_password` (a scrambled form of the password, lesson 19). FastAPI offers
two ways to declare the shape of the output. A model used this way is a **response model**.

### Return type annotation

```python
class ItemOut(BaseModel):
    name: str
    price: float

@app.get("/items/{item_id}")
def read_item(item_id: int) -> ItemOut:
    return ItemOut(name="Hammer", price=9.5)
```

The `-> ItemOut` after the parameter list is a return type hint. FastAPI uses it to **validate** the
value you return, **filter** it down to the declared fields, **serialise** it to JSON and **document**
it.

### `response_model` parameter

Sometimes the function returns something other than the declared shape, for example a dictionary or
an object from the database. In that case put `response_model` in the decorator. It takes priority
over the return hint:

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

`UserIn` describes what a client sends: it includes `password`. `UserOut` describes what a client
receives: it does not. (`EmailStr` is a Pydantic type that accepts only valid email addresses.) Even
though `saved` carries more attributes, the client receives only `username` and `email`. This
**filtering** is a security feature, not a convenience.

A widely used pattern is a small *family* of models built by inheritance: a base model with the shared
fields, plus one subclass for each situation.

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

`UserBase` holds what all variants share. `UserCreate` adds `password` (what the client sends).
`UserInDB` adds `id` and `hashed_password` (what is stored). `UserPublic` adds only `id` (what the
client may see). The last three lines do by hand what `response_model=UserPublic` does: take the
stored object's data, validate it as `UserPublic`, and print the JSON. The output is
`{"username":"ann","email":"ann@example.com","id":1}`, with no trace of the hash.

### Trimming defaults and unset fields

Decorator options shape the JSON further:

- `response_model_exclude_unset=True` leaves out fields that were never explicitly given a value,
  which keeps sparse records small.
- `response_model_exclude_none=True` leaves out fields whose value is `None`.
- `response_model_include={"name"}` and `response_model_exclude={"tax"}` are quick one-off filters.
  For anything permanent, prefer a separate model.

## Status codes

A successful endpoint answers `200` unless told otherwise. Set a different success code in the
decorator:

```python
from fastapi import status

@app.post("/items/", status_code=status.HTTP_201_CREATED)
def create_item(item: Item) -> Item: ...

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int) -> None: ...
```

`status.HTTP_201_CREATED` is the number 201 under a readable name. The `...` in the function bodies
is a Python placeholder meaning "code omitted here".

For **errors**, raise `HTTPException`. An **exception** is Python's mechanism for abandoning the
current work and reporting a problem; `raise` triggers one.

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

The function looks the item up in a dictionary. If nothing is found, it raises an `HTTPException`
with the status, a `detail` message (which becomes `{"detail": "Item not found"}` in the body) and
optional extra headers.

Raising, as opposed to returning, matters. A raised exception stops the endpoint immediately *and*
stops every helper function that was in the middle of being called, so code several calls deep can
report "not found" without passing special return values back up. (The book argues for keeping HTTP
details at the edge of the program, so its inner code raises its own exception types such as
`Missing`, which the outer layer translates into `HTTPException`. Lesson 15 develops this.)

To choose the status *while the function runs* (for example 200 when something was updated and 201
when it was created), declare a parameter of type `Response` and set its `status_code`:

```python
from fastapi import Response

@app.put("/items/{item_id}")
def upsert(item_id: int, item: Item, response: Response) -> Item:
    if item_id not in items:
        response.status_code = status.HTTP_201_CREATED
    items[item_id] = item
    return item
```

FastAPI notices the `Response` type and passes in an object that represents the response being
built. This endpoint is an *upsert* (update or insert): a `PUT` that creates the item when it does
not exist yet, in which case the status is changed to 201.

## Response headers and cookies

The same `Response` parameter lets you add headers and cookies while still returning data in the
normal way:

```python
@app.get("/report")
def report(response: Response):
    response.headers["Cache-Control"] = "max-age=60"
    response.set_cookie(key="seen_report", value="yes", httponly=True, secure=True, samesite="lax")
    return {"ok": True}
```

The first line sets a caching header. The second asks the browser to store a cookie. Its three flags
are safety settings: `httponly` hides the cookie from JavaScript running in the page, `secure` sends
it only over encrypted connections, and `samesite` limits when it is sent along with requests coming
from other websites.

## Returning a Response directly

You can skip FastAPI's conversion entirely by returning a `Response` object (or one of its
subclasses). FastAPI sends it exactly as it is, with no response-model checking or filtering:

```python
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse, RedirectResponse

@app.get("/legacy")
def legacy():
    return JSONResponse(status_code=200, content={"old": True}, headers={"Deprecation": "true"})

@app.get("/go")
def go():
    return RedirectResponse("/docs")
```

`JSONResponse` lets you set the status, content and headers yourself. `RedirectResponse` tells the
client to go to another address. Use direct responses for content that is not JSON (HTML, CSV text,
images), for redirects, or when you need full control. Streaming and files are covered in the
files/streaming module. Writing `response_class=HTMLResponse` (or `ORJSONResponse`, a faster JSON
encoder) in the decorator changes the default response type and the media type shown in the docs.

> [!INTERVIEW]
> "How do you prevent an API from leaking sensitive fields like password hashes?" — Never return
> internal objects unfiltered. Declare an output shape (`response_model=UserPublic` or a return
> annotation); FastAPI validates the return value against it and drops any field not declared. Keep
> separate input, storage and output models so that a sensitive field can only exist where it belongs.
> Add a test asserting the field is absent from the JSON.

## What really happens to your return value

1. If you returned a `Response`, it is sent unchanged.
2. Otherwise, if there is a response model, FastAPI validates the value against it. A mismatch is a
   bug in the **server**, so the result is a 500 (`ResponseValidationError`), not a 422.
3. The validated data is converted with Pydantic into JSON-compatible values: datetimes become ISO
   strings, UUIDs become strings, and so on. With no model, a helper named `jsonable_encoder` does it.
4. The bytes are wrapped in a `JSONResponse` with your status code and headers.

Step 3 is easy to see directly:

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

The first `print` shows Python objects: a `UUID(...)` and a `datetime.datetime(...)`. The second,
with `mode="json"`, shows what goes on the wire: the id as the string
`'00000000-0000-0000-0000-00000000002a'` and the time as `'2025-01-15T09:30:00Z'`.

## Worked example: a complete resource with model families

Now everything together for one resource: a separate model for each direction, correct status codes,
and a partial update. `Field(...)` attaches rules to a field (`min_length`, `gt` for "greater than");
lesson 7 covers it fully. `repo` is a small stand-in for a database: an object that keeps the items
in a dictionary and offers `insert`, `get`, `save` and `delete` methods, so that the whole example
runs here. Press **Run**:

```fastapi-run method=POST path=/items
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Response, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

class ItemBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0)
    description: str | None = None

class ItemCreate(ItemBase):                 # what a client may send when creating
    pass

class ItemUpdate(BaseModel):                # PATCH: everything optional
    name: str | None = Field(default=None, min_length=1, max_length=100)
    price: float | None = Field(default=None, gt=0)
    description: str | None = None

class ItemPublic(ItemBase):                 # what a client receives
    id: int
    created_at: datetime

class ItemInDB(ItemPublic):                 # what we store: extra internal fields
    cost_price: float
    supplier_id: int

class Repo:                                 # stand-in for a database table
    def __init__(self):
        self.rows, self.next_id = {}, 1
    def insert(self, item: ItemCreate) -> ItemInDB:
        stored = ItemInDB(**item.model_dump(), id=self.next_id, created_at=datetime.now(timezone.utc),
                          cost_price=round(item.price * 0.4, 2), supplier_id=7)
        self.rows[stored.id] = stored
        self.next_id += 1
        return stored
    def get(self, item_id: int) -> ItemInDB | None:
        return self.rows.get(item_id)
    def save(self, item: ItemInDB) -> ItemInDB:
        self.rows[item.id] = item
        return item
    def delete(self, item_id: int) -> bool:
        return self.rows.pop(item_id, None) is not None

repo = Repo()
app = FastAPI()

@app.post("/items", response_model=ItemPublic, status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate, response: Response):
    stored = repo.insert(item)                               # -> ItemInDB
    response.headers["Location"] = f"/items/{stored.id}"
    return stored                                            # cost_price, supplier_id filtered out

@app.patch("/items/{item_id}", response_model=ItemPublic)
def patch_item(item_id: int, patch: ItemUpdate):
    stored = repo.get(item_id)
    if stored is None:
        raise HTTPException(status_code=404, detail="Item not found")
    updated = stored.model_copy(update=patch.model_dump(exclude_unset=True))
    return repo.save(updated)

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int) -> None:
    if not repo.delete(item_id):
        raise HTTPException(status_code=404, detail="Item not found")

client = TestClient(app)
r = client.post("/items", json={"name": "Hammer", "price": 9.5, "cost_price": 1})
print(r.status_code, r.headers["location"], r.json())
print(client.patch("/items/1", json={"price": 11.0}).json())
print(client.delete("/items/1").status_code)
print(client.delete("/items/1").json())
```

The four printed lines are the story of one item. The `POST` answers `201`, a `Location` header
pointing at `/items/1`, and the public fields only. The `PATCH` changes the price and keeps the
name. The first `DELETE` answers `204` (deleted, nothing to send back) and the second answers
`{'detail': 'Item not found'}`, because the item is already gone. In the request panel, try
`PATCH /items/1` with the body `{"price": -1}` to watch `Field(gt=0)` refuse it.

Trace `POST /items` with the body `{"name": "Hammer", "price": 9.5, "cost_price": 1}`:

1. The body is parsed as JSON and validated against `ItemCreate`. `cost_price` is not a field of
   `ItemCreate`, so it is dropped (the default `extra="ignore"`). The client cannot set an internal
   field. With `extra="forbid"` the request would be refused with 422, which is stricter and often
   better.
2. `repo.insert` returns an `ItemInDB` with `id`, `created_at`, `cost_price` and `supplier_id`.
3. The response model `ItemPublic` validates and filters: the client receives `id`, `name`, `price`,
   `description` and `created_at`, and nothing else.
4. Status `201` comes from the decorator and the `Location` header from the injected `Response`.

The `PATCH` endpoint deserves a second look. `patch.model_dump(exclude_unset=True)` produces a
dictionary of *only the fields the client actually sent*. `stored.model_copy(update=...)` makes a copy
of the stored item with those fields replaced. A client that sends `{"price": 11.0}` changes the
price and leaves the name alone, which is the meaning of PATCH from lesson 1.

The whole filtering mechanism can be reproduced, and tested, with Pydantic alone:

```python-run
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class ItemBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0)
    description: str | None = None

class ItemUpdate(BaseModel):
    name: str | None = None
    price: float | None = Field(default=None, gt=0)
    description: str | None = None

class ItemPublic(ItemBase):
    id: int
    created_at: datetime

class ItemInDB(ItemPublic):
    cost_price: float
    supplier_id: int

stored = ItemInDB(id=42, name="Hammer", price=9.5, cost_price=4.1, supplier_id=7,
                  created_at=datetime(2025, 1, 15, tzinfo=timezone.utc))

def to_response(obj, model):
    """What response_model does: validate against the public model, keep only its fields, JSON-encode."""
    return model.model_validate(obj.model_dump()).model_dump(mode="json")

print("client sees :", to_response(stored, ItemPublic))

patch = ItemUpdate.model_validate({"price": 11.0})
updated = stored.model_copy(update=patch.model_dump(exclude_unset=True))
print("after PATCH :", to_response(updated, ItemPublic))
print("internal kept:", updated.cost_price, updated.supplier_id)

leaked = set(ItemInDB.model_fields) - set(ItemPublic.model_fields)
print("fields that must never appear in responses:", sorted(leaked))
```

The first line of output shows the client's view: no `cost_price`, no `supplier_id`. The second shows
the price changed to 11.0 after the patch while the name stayed. The third confirms the internal
fields are still on the stored object. The fourth computes, with a set difference, the fields that
exist in storage but not in the public model: `['cost_price', 'supplier_id']`.

That last line makes a useful automated test in a real project: assert that the difference between
the storage model and the public model is exactly the set of fields you intend to keep private.

## Choosing the response style

| You want | Use |
|---|---|
| typed, filtered JSON (the normal case) | return annotation or `response_model` |
| different success codes per branch | inject `Response`, set `status_code` |
| extra headers/cookies with normal JSON | inject `Response` |
| an error anywhere in the call stack | `raise HTTPException` |
| HTML, text, redirect, file, stream | return the specific `Response` subclass |
| full manual control, no validation | return `JSONResponse(...)` |
| document extra outcomes in OpenAPI | `responses={404: {"model": ErrorModel}}` on the decorator |

A subtle interaction: when both a return annotation and `response_model` are present,
`response_model` wins for validation, filtering and documentation, while the annotation still serves
your type checker. Setting `response_model=None` switches FastAPI's handling off when the annotation
is not something Pydantic can use (for example a union that includes `Response`).

## Pitfalls

- Returning database objects without a response model: fields leak, or the conversion to JSON fails.
- Writing `return HTTPException(...)` instead of `raise`. The exception object is then treated as
  ordinary data and sent with status 200.
- Forgetting that a response-model mismatch produces a 500, which is *your* bug and not the client's.
- Declaring `status_code=204` and then returning a body.
- Reusing one model for input and output, then adding a sensitive field to it later.

## Summary

- A `BaseModel` parameter is the JSON body: parsed, validated, documented, and handed to you as an
  object.
- `Body()` handles single values and embedding; models nest freely.
- Declare outputs with a return annotation or `response_model`; it validates, **filters** and documents.
- Use input / stored / public model families to keep secrets out of responses.
- `status_code=` for defaults, `HTTPException` for errors, an injected `Response` for a status chosen
  at run time and for headers and cookies, or return a `Response` subclass for full control.

## Glossary

- **Request body** — the content after the headers of a request, usually JSON.
- **Pydantic** — the library FastAPI uses to describe, check and convert data.
- **Model** — a class inheriting from `BaseModel` that lists fields and their types.
- **Instance** — one object created from a class.
- **Field** — one named, typed entry in a model.
- **Lax mode** — Pydantic's default willingness to convert sensible inputs (`"9.5"` to `9.5`).
- **`extra="ignore"` / `"forbid"`** — drop unknown fields without comment / reject them.
- **Nested model** — a model used as the type of a field in another model.
- **Response model** — the model that defines, checks and filters what an endpoint sends back.
- **Filtering** — removing every field not declared in the response model.
- **Model family** — related models (create, stored, public) built from one base by inheritance.
- **Exception / raise** — Python's way to abandon the current work and report a problem.
- **`HTTPException`** — the exception FastAPI turns into an error response with a chosen status.
- **Upsert** — update the record if it exists, insert it if it does not.
- **Redirect** — a response telling the client to request a different address.

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
   "explain": "A returned exception object would be serialised as data with status 200. Raising unwinds the stack to FastAPI's handler."},
  {"q": "What is Pydantic's default behaviour for unknown fields in the body?", "options": ["Reject with 422", "Ignore them", "Keep them as attributes", "Raise a 500"], "answer": 1,
   "explain": "The default extra='ignore' drops unknown fields; use extra='forbid' to reject them."},
  {"q": "If you return a JSONResponse object directly, which is true?", "options": ["response_model filtering still applies", "It is sent as-is without response_model validation", "FastAPI converts it to a dict first", "It must be wrapped in HTTPException"], "answer": 1,
   "explain": "Returning a Response bypasses FastAPI's serialisation and response-model handling entirely."}
]
```

> **Source:** Lubanovic, *FastAPI*, ch. 3 "FastAPI Tour" (Body, HTTP Responses, Status Code, Headers, Response Types, Model Types and response_model); https://fastapi.tiangolo.com/tutorial/body/, /tutorial/response-model/, /tutorial/extra-models/, /tutorial/response-status-code/, /tutorial/handling-errors/, /advanced/response-directly/
