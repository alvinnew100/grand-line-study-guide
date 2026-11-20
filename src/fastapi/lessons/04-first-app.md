# Your first FastAPI app

FastAPI's pitch, in its creator Sebastián Ramírez's words, is building APIs "based on standard Python type
hints". You declare *what* your endpoint needs using ordinary function parameters with types, and the
framework works out *where* each value comes from, converts it, validates it, documents it, and rejects
bad requests before your code runs. This lesson builds the smallest app, then explores path and query
parameters — the two inputs that live in the URL.

## Installing and running

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install "fastapi[standard]"                         # FastAPI + Uvicorn + CLI + httpx + extras
```

`fastapi[standard]` pulls in Uvicorn, the `fastapi` CLI, `python-multipart` (forms), `email-validator`,
`httpx` (for tests) and more. A minimal application, `main.py`:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World"}
```

```bash
fastapi dev main.py
# INFO  Uvicorn running on http://127.0.0.1:8000
```

Visit `http://127.0.0.1:8000/` and you get `{"message":"Hello, World"}`. Visit `/docs` and you get a full
interactive Swagger UI; `/redoc` gives ReDoc; `/openapi.json` is the machine-readable schema. You wrote
four lines.

Let's dissect them:

- `app = FastAPI()` creates the ASGI application object (a Starlette subclass).
- `@app.get("/")` is a **path operation decorator**: *path* `/`, *operation* `GET`. There are matching
  decorators `@app.post`, `@app.put`, `@app.patch`, `@app.delete`, `@app.options`, `@app.head`, and
  `@app.api_route(..., methods=[...])` for several at once.
- `read_root` is the **path operation function**. Its return value (a dict, list, Pydantic model, string…)
  is serialised to JSON automatically.

Lubanovic's first example in chapter 3 is a `/hi` endpoint returning a greeting, which he then extends step
by step to accept a name through every input channel. We'll follow a similar route.

> [!TIP]
> You can also start the server from code — handy in a debugger:
> ```python
> if __name__ == "__main__":
>     import uvicorn
>     uvicorn.run("main:app", reload=True)
> ```

## Path parameters

Variables in the path template become function parameters with the same name:

```python
@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}
```

- `GET /items/5` → `{"item_id": 5}` — note **5 the integer**, not `"5"`. FastAPI converted it because of
  the `int` annotation.
- `GET /items/foo` → **422** with a detail like
  `{"type": "int_parsing", "loc": ["path", "item_id"], "msg": "Input should be a valid integer, ...", "input": "foo"}`.

The type hint is doing three jobs: **conversion** (string → int), **validation** (reject non-integers),
and **documentation** (OpenAPI says `item_id` is an integer). Your editor also gets autocompletion
because `item_id` really is an `int` inside the function.

### Order matters

Routes are matched in declaration order. If you have both `/users/me` and `/users/{user_id}`, declare the
fixed one **first**:

```python
@app.get("/users/me")
def read_current_user():
    return {"user_id": "the current user"}

@app.get("/users/{user_id}")
def read_user(user_id: str):
    return {"user_id": user_id}
```

Otherwise `/users/me` would match `{user_id}` with `user_id="me"`.

### Restricting values with Enum

```python
from enum import Enum

class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"

@app.get("/models/{model_name}")
def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}
    return {"model_name": model_name}
```

Any value outside the enum gets a 422, and the docs show a dropdown of allowed values. Inheriting from
`str` makes the members serialise as plain strings.

### Paths inside paths

To capture a file path including slashes, use Starlette's `path` converter in the template:

```python
@app.get("/files/{file_path:path}")
def read_file(file_path: str):
    return {"file_path": file_path}
```

`GET /files/home/johndoe/myfile.txt` → `file_path="home/johndoe/myfile.txt"`.

### Extra validation with `Path`

```python
from typing import Annotated
from fastapi import Path

@app.get("/items/{item_id}")
def read_item(item_id: Annotated[int, Path(title="The item ID", ge=1, le=1_000_000)]):
    return {"item_id": item_id}
```

`ge`, `gt`, `le`, `lt` constrain numbers; the `title`/`description` show up in docs.

## Query parameters

Any function parameter that is **not** in the path template (and is a simple type) is a **query
parameter**:

```python
fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]

@app.get("/items/")
def read_items(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]
```

`GET /items/?skip=1&limit=1` → `[{"item_name": "Bar"}]`. The rules:

- A parameter **with a default** is optional. With no default it is **required** (missing → 422 with
  `"type": "missing"`).
- `None` as default (`q: str | None = None`) makes it optional and lets you detect absence.
- `bool` parameters accept `1`, `true`, `True`, `on`, `yes` (and their negatives) — FastAPI converts them.

Path and query parameters mix freely; FastAPI tells them apart by name:

```python
@app.get("/users/{user_id}/items/{item_id}")
def read_user_item(user_id: int, item_id: str, q: str | None = None, short: bool = False):
    item = {"item_id": item_id, "owner_id": user_id}
    if q:
        item["q"] = q
    if not short:
        item["description"] = "A long description"
    return item
```

### Validation and metadata with `Query`

The modern style uses `Annotated` to attach extra information while keeping the default as a normal
Python default:

```python
from typing import Annotated
from fastapi import Query

@app.get("/search/")
def search(
    q: Annotated[str | None, Query(min_length=3, max_length=50, pattern="^[a-z ]+$")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return {"q": q, "page": page, "size": size}
```

Other `Query` options: `alias="item-query"` (when the URL name isn't a valid Python identifier),
`deprecated=True`, `include_in_schema=False`, `title`, `description`, `examples`.

### Lists from repeated keys

```python
@app.get("/items/")
def read_items(tag: Annotated[list[str], Query()] = []):
    return {"tags": tag}
```

`GET /items/?tag=a&tag=b` → `{"tags": ["a", "b"]}`. You *must* use `Query()` explicitly for a list,
otherwise FastAPI would assume a list parameter is a request **body**.

### Query parameter models

Since FastAPI 0.115 you can group related query parameters into a Pydantic model:

```python
from typing import Literal
from pydantic import BaseModel, Field

class FilterParams(BaseModel):
    model_config = {"extra": "forbid"}          # reject unknown query params
    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = []

@app.get("/items/")
def read_items(filter_query: Annotated[FilterParams, Query()]):
    return filter_query
```

## How FastAPI decides where a parameter comes from

This decision table is worth memorising:

| Declaration | Source |
|---|---|
| name appears in the path template | **path** |
| simple type (`int`, `str`, `float`, `bool`, `Enum`, `UUID`, `datetime`…) not in path | **query** |
| Pydantic model (no marker) | **body** (JSON) |
| `Annotated[..., Query()/Header()/Cookie()/Body()/Form()/File()]` | as marked |
| `Annotated[..., Depends(...)]` | a **dependency** |
| type `Request`, `Response`, `BackgroundTasks`, `WebSocket` | injected by the framework |

## A mini FastAPI in 40 lines

To demystify the "magic", here is a toy that uses `inspect` and type hints to route, extract path/query
parameters and coerce types — the same idea FastAPI implements (far more completely) with Pydantic:

```python-run
import inspect, re
from urllib.parse import parse_qsl

class MiniAPI:
    def __init__(self):
        self.routes = []

    def get(self, template):
        def deco(fn):
            names = re.findall(r"{(\w+)}", template)
            regex = "^" + re.sub(r"{(\w+)}", r"(?P<\1>[^/]+)", template) + "$"
            self.routes.append((re.compile(regex), names, fn))
            return fn
        return deco

    def handle(self, url):
        path, _, query = url.partition("?")
        qs = dict(parse_qsl(query))
        for regex, names, fn in self.routes:
            m = regex.match(path)
            if not m:
                continue
            kwargs, errors = {}, []
            for name, p in inspect.signature(fn).parameters.items():
                raw = m.group(name) if name in names else qs.get(name)
                if raw is None:
                    if p.default is inspect.Parameter.empty:
                        errors.append({"loc": ["query", name], "type": "missing"})
                    else:
                        kwargs[name] = p.default
                    continue
                try:
                    kwargs[name] = p.annotation(raw) if p.annotation is not inspect.Parameter.empty else raw
                except ValueError:
                    where = "path" if name in names else "query"
                    errors.append({"loc": [where, name], "type": f"{p.annotation.__name__}_parsing"})
            if errors:
                return 422, {"detail": errors}
            return 200, fn(**kwargs)
        return 404, {"detail": "Not Found"}

app = MiniAPI()

@app.get("/users/me")
def me():
    return {"user": "current"}

@app.get("/users/{user_id}/items/{item_id}")
def user_item(user_id: int, item_id: str, limit: int = 10, q: str = None):
    return {"user_id": user_id, "item_id": item_id, "limit": limit, "q": q}

@app.get("/search")
def search(term: str, page: int = 1):
    return {"term": term, "page": page}

for url in ["/users/me", "/users/7/items/abc?limit=3", "/users/x/items/abc",
            "/search?term=fastapi", "/search", "/nope"]:
    print(url, "->", *app.handle(url))
```

Notice how the declaration order (`/users/me` first) and the type hints drive everything. Real FastAPI
does this analysis **once at startup** (when the decorator runs), building a validation model per
endpoint, so the per-request cost is low.

> [!INTERVIEW]
> "How does FastAPI know that `item_id` is a path parameter and `q` is a query parameter?" — At
> decoration time it inspects the function signature: names that appear in the path template are path
> parameters; remaining parameters of singular types are query parameters; Pydantic-model parameters are
> body; anything wrapped in `Annotated[..., Query()/Header()/Body()/Depends()...]` follows the explicit
> marker. It then builds Pydantic validators for each, which run before the function is called and
> produce a 422 on failure.

## `def` or `async def`?

Both work. FastAPI runs `async def` endpoints directly on the event loop and plain `def` endpoints in a
thread pool. Rule of thumb (covered in depth in the async module): use `async def` when everything you
call inside is awaitable (async DB driver, `httpx.AsyncClient`); use `def` when you call blocking
libraries (classic `requests`, most ML `model.predict` calls, synchronous DB drivers).

## Tracing one request step by step

Take this endpoint:

```python
@app.get("/users/{user_id}/items")
def list_user_items(
    user_id: Annotated[int, Path(ge=1)],
    status: Literal["open", "closed"] = "open",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    tag: Annotated[list[str], Query()] = [],
):
    ...
```

and the request `GET /users/7/items?limit=5&tag=red&tag=blue&debug=1`:

1. **Routing.** Starlette tries routes in declaration order. The template compiles to a regular
   expression roughly like `^/users/(?P<user_id>[^/]+)/items$`; it matches, capturing `user_id="7"` — a
   string at this point.
2. **Path parameters.** FastAPI validates `"7"` against `int` with `ge=1` → `7`.
3. **Query parameters.** The query string parses to a multi-dict
   `{"limit": ["5"], "tag": ["red", "blue"], "debug": ["1"]}`.
   - `status` is absent → default `"open"`.
   - `limit`: `"5"` → `5`, within `1..100`.
   - `tag`: declared as a list → all occurrences → `["red", "blue"]`.
   - `debug` is not declared → **silently ignored** (unless you use a query-parameter model with
     `extra="forbid"`).
4. **Call.** `list_user_items(user_id=7, status="open", limit=5, tag=["red", "blue"])`.
5. **Response.** The return value is serialised to JSON with status 200.

Now the failing variant `GET /users/0/items?limit=500&status=archived`. Validation does **not** stop at
the first problem — all three are reported together, so a client can fix everything in one round trip:

```json
{"detail": [
  {"type": "greater_than_equal", "loc": ["path", "user_id"], "msg": "Input should be greater than or equal to 1", "input": "0", "ctx": {"ge": 1}},
  {"type": "literal_error", "loc": ["query", "status"], "msg": "Input should be 'open' or 'closed'", "input": "archived", "ctx": {"expected": "'open' or 'closed'"}},
  {"type": "less_than_equal", "loc": ["query", "limit"], "msg": "Input should be less than or equal to 100", "input": "500", "ctx": {"le": 100}}
]}
```

Reading a 422: `loc[0]` says which part of the request (`path`, `query`, `header`, `cookie`, `body`),
the rest of `loc` is the field path, `type` is a stable code, `input` echoes what was received, and `ctx`
carries the constraint that failed.

## Debugging the classics

| What you see | Cause | Fix |
|---|---|---|
| `422` with `"loc": ["query", "item"], "type": "missing"` on a POST with a JSON body | parameter annotated with a plain type or `dict`, so FastAPI looks in the query | annotate with a Pydantic model or `Body()` |
| `422` with `"loc": ["body"], "type": "missing"` on a GET | a list/model parameter without `Query()` is treated as a body | add `Query()` |
| `/users/me` returns a 422 about `user_id` | the parameterised route was declared first | declare fixed paths before `{param}` paths |
| `307 Temporary Redirect` then failure in a client | trailing-slash mismatch (`/items` vs `/items/`) | call the declared form, or declare both / set `redirect_slashes=False` |
| `405 Method Not Allowed` | the path exists, but not for this method | check the decorator (`@app.post` vs `@app.get`) |
| `404` although the function exists | router never included, or prefix differs | inspect `app.routes` |
| Parameter is always the default | name mismatch between URL and function (`item-id` vs `item_id`) | rename, or use `alias="item-id"` |

A quick way to see exactly what FastAPI registered:

```python
for route in app.routes:
    print(getattr(route, "methods", None), route.path, route.name)
```

## Path or query? A decision guide

- Is the value part of the resource's **identity**, and is the request meaningless without it? → path
  (`/users/7`).
- Is it **optional**, a filter, a sort order, a page, a flag? → query (`?status=open&limit=20`).
- Can there be **several** values? → repeated query keys (`?tag=a&tag=b`).
- Is it **hierarchical** (belongs-to)? → nested path, one level (`/users/7/items`).
- Is it large, structured or sensitive? → not in the URL at all; use the body or a header.

## Pitfalls

- Declaring `/users/{user_id}` before `/users/me`.
- Forgetting `Query()` for list parameters (FastAPI then expects a JSON body).
- Using mutable defaults carelessly — FastAPI copies defaults per request, but your own helper functions
  won't.
- Expecting `bool("false")` semantics — FastAPI's bool conversion is correct, but if you parse query
  strings manually remember that `bool("false")` is `True`.
- Missing trailing slash: by default FastAPI redirects `/items` → `/items/` (307) if only the latter is
  declared; clients that don't follow redirects for POST will be confused. Pick one style.

## Summary

- `app = FastAPI()` + `@app.get(path)` decorators define path operations; return values become JSON.
- Path parameters come from `{names}` in the template; type hints convert and validate them.
- Other simple parameters are query parameters; defaults make them optional.
- `Annotated[T, Path()/Query()]` adds validation (`ge`, `le`, `min_length`, `pattern`) and docs metadata.
- `/docs`, `/redoc` and `/openapi.json` are generated automatically.

```quiz
[
  {"q": "GET /items/abc is sent to 'def read_item(item_id: int)' on '/items/{item_id}'. What happens?", "options": ["item_id is 'abc'", "item_id is None", "FastAPI returns 422 before calling the function", "500 Internal Server Error"], "answer": 2,
   "explain": "The int annotation is enforced during request validation; the failure becomes a 422 with loc ['path', 'item_id']."},
  {"q": "In 'def f(user_id: int, q: str | None = None)' on path '/users/{user_id}', what is q?", "options": ["A required path parameter", "An optional query parameter", "A request body field", "A header"], "answer": 1,
   "explain": "q is not in the path template and is a simple type, so it is a query parameter; the None default makes it optional."},
  {"q": "Why must /users/me be declared before /users/{user_id}?", "options": ["Alphabetical order", "Routes are matched in declaration order, so the parameterised route would capture 'me'", "FastAPI forbids it otherwise", "For OpenAPI ordering only"], "answer": 1,
   "explain": "The first matching route wins; '{user_id}' matches any segment including 'me'."},
  {"q": "How do you accept ?tag=a&tag=b as a list?", "options": ["tag: list[str] = []", "tag: Annotated[list[str], Query()] = []", "tag: str = Query(multiple=True)", "tag: set = Body()"], "answer": 1,
   "explain": "Without Query(), a list-typed parameter is interpreted as part of the JSON body. Query() marks it as a repeated query parameter."},
  {"q": "Which URL serves the interactive Swagger UI by default?", "options": ["/swagger", "/docs", "/api", "/openapi"], "answer": 1,
   "explain": "/docs serves Swagger UI, /redoc serves ReDoc and /openapi.json the raw schema."},
  {"q": "What does Annotated[int, Query(ge=1, le=100)] = 20 express?", "options": ["A required int between 1 and 100", "An optional int query parameter, default 20, that must be between 1 and 100 if provided", "A path parameter", "A list of ints"], "answer": 1,
   "explain": "The default makes it optional; Query adds validation constraints ge/le and documentation."},
  {"q": "When does FastAPI analyse your endpoint's signature?", "options": ["On every request", "Once, when the route is registered at import time", "Only when /docs is opened", "When the first request fails"], "answer": 1,
   "explain": "The decorator inspects the signature and builds the parameter/validation model once; per-request work is just running the validators."}
]
```

> **Source:** Lubanovic, *FastAPI*, ch. 3 "FastAPI Tour" (A FastAPI Application, URL Path, Query Parameters, Type Conversion); https://fastapi.tiangolo.com/tutorial/first-steps/, /tutorial/path-params/, /tutorial/query-params/, /tutorial/query-params-str-validations/, /tutorial/query-param-models/
