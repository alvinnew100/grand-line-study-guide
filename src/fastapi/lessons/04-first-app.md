# Your first FastAPI app

> **Before this lesson:** you should know the parts of an HTTP request and of a URL
> ([lesson 1](#/lesson/fastapi/http-basics)), the REST address shapes `/items` and `/items/42`
> ([lesson 2](#/lesson/fastapi/rest-json)), and that Uvicorn is the server that runs a FastAPI app
> ([lesson 3](#/lesson/fastapi/asgi-stack)). In Python you need functions with parameters and default
> values. Decorators and type hints are explained here.

## In plain words

In the last lesson you saw a web application written by hand: a function that inspected the path,
decoded the body and assembled the response message itself. **FastAPI** removes that hand work. You
write an ordinary Python function, say which address it answers, and describe what it needs by giving
its parameters names and types. FastAPI does the rest: it finds each value in the request, converts
it, checks it, refuses bad requests with a clear error, and writes documentation for the whole API.

An everyday picture: a form with labelled boxes. "Age: [whole number]". Whoever designed the form
decided once what each box means. A clerk then checks every submitted form against the labels and
sends back any form with a word in the age box, before it ever reaches the person who does the real
work. In FastAPI your function's parameter list *is* the form, and FastAPI is the clerk.

Why this matters for a job: these few ideas (path operations, path parameters, query parameters,
automatic checking) are the daily bread of FastAPI work, and "how does FastAPI know where a parameter
comes from?" is a classic interview question. Everything later in the track builds on them.

## Two bits of Python you need first

**Type hints.** Python lets you note the expected type of a parameter after a colon:

```python
def double(n: int) -> int:
    return n * 2
```

`n: int` says "n should be a whole number" and `-> int` says the function returns one. Python itself
does not enforce these notes; they are hints for people and tools. FastAPI is unusual in that it
*reads* the hints while your program starts and acts on them. Other hints you will meet: `str` (text),
`float` (a number with a decimal point), `bool` (`True`/`False`), `list[str]` (a list of strings) and
`str | None` ("a string, or nothing").

**Decorators.** A line beginning with `@` directly above a function is a decorator. It hands the
function to some other code at the moment the function is defined. `@app.get("/")` means "register
the function below as the handler for `GET /`". The function itself is unchanged.

## Installing and running

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install "fastapi[standard]"                         # FastAPI + Uvicorn + CLI + httpx + extras
```

The first line creates and switches on a **virtual environment**: a private folder of installed
packages for this project, so that different projects do not disturb each other. The second line uses
`pip`, Python's package installer, to fetch FastAPI. The `[standard]` suffix asks for the usual
companions too: Uvicorn, the `fastapi` command, `python-multipart` (for HTML forms), `email-validator`,
`httpx` (for tests) and more.

Now the smallest possible application. Save it as `main.py`:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World"}
```

Start it:

```bash
fastapi dev main.py
# INFO  Uvicorn running on http://127.0.0.1:8000
```

Open `http://127.0.0.1:8000/` in a browser and you see `{"message":"Hello, World"}`. Open
`http://127.0.0.1:8000/docs` and you find an interactive page listing your endpoint with a "Try it
out" button. That page is called Swagger UI. `/redoc` shows the same information in another layout,
and `/openapi.json` is a machine-readable description of the API (lesson 6 explains all three). You
wrote four lines of code.

What each line does:

- `from fastapi import FastAPI` loads the main class.
- `app = FastAPI()` creates the application object. This is the ASGI app from lesson 3, the thing
  Uvicorn calls.
- `@app.get("/")` is a **path operation decorator**. *Path* is the address `/`; *operation* is the
  HTTP method `GET`. There is a matching decorator for each method: `@app.post`, `@app.put`,
  `@app.patch`, `@app.delete`, `@app.options`, `@app.head`, and `@app.api_route(..., methods=[...])`
  for several at once.
- `def read_root():` is the **path operation function**, also called the endpoint function or
  handler. FastAPI calls it for each matching request.
- `return {"message": "Hello, World"}` returns a Python dictionary. FastAPI converts whatever you
  return (a dictionary, a list, a string, a Pydantic model) to JSON and sends it with status `200`.

Lubanovic's first example in chapter 3 is a `/hi` endpoint that returns a greeting, which he then
extends one step at a time so that a name can arrive through every part of the request. This lesson
takes a similar route for the two inputs that live in the URL.

> [!TIP]
> You can also start the server from code, which is handy when using a debugger:
> ```python
> if __name__ == "__main__":
>     import uvicorn
>     uvicorn.run("main:app", reload=True)
> ```

## Path parameters

A **path parameter** is a variable part of the path, such as the `5` in `/items/5`. Write the variable
part in curly braces in the path, and add a function parameter with the same name:

```python
@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}
```

- `"/items/{item_id}"` is a **path template**: `/items/` followed by one slot named `item_id`.
- `def read_item(item_id: int):` declares a parameter with the same name, with the hint `int`.
- The function returns the value it was given, so we can see what arrived.

Two requests show what the hint does:

- `GET /items/5` returns `{"item_id": 5}`. Look closely: `5` the number, not `"5"` the text. Everything
  in a URL is text, so FastAPI converted it because the hint says `int`.
- `GET /items/foo` returns status **422**, with a body like
  `{"type": "int_parsing", "loc": ["path", "item_id"], "msg": "Input should be a valid integer, ...", "input": "foo"}`.
  Your function was never called.

That one hint is doing three jobs: **conversion** (text to number), **validation** (checking that the
data obeys the rules, here "must be a whole number") and **documentation** (the docs page now says
`item_id` is an integer). Your code editor benefits too: inside the function it knows `item_id` is an
`int` and can suggest completions.

### Order matters

FastAPI tries your routes in the order they appear in the file and uses the first that fits. If you
have both a fixed path `/users/me` and a template `/users/{user_id}`, write the fixed one **first**:

```python
@app.get("/users/me")
def read_current_user():
    return {"user_id": "the current user"}

@app.get("/users/{user_id}")
def read_user(user_id: str):
    return {"user_id": user_id}
```

In the other order, a request for `/users/me` would fit the template with `user_id="me"`, and the
"current user" function would never run.

### Restricting values with Enum

Sometimes only a few values are allowed. Python's `Enum` (short for enumeration) is a class that
lists a fixed set of named values:

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

`ModelName` has three members. Using it as the hint for `model_name` tells FastAPI that only
`alexnet`, `resnet` or `lenet` may appear in that slot. Anything else gets a 422, and the docs page
shows a dropdown with the three choices. Inside the function you compare against the members
(`model_name is ModelName.alexnet`). Inheriting from `str` as well as `Enum` makes the members
behave as plain strings when converted to JSON.

### Paths inside paths

A slot normally matches one segment, meaning the text between two slashes. To capture a file path
that itself contains slashes, add `:path` inside the braces:

```python
@app.get("/files/{file_path:path}")
def read_file(file_path: str):
    return {"file_path": file_path}
```

`GET /files/home/johndoe/myfile.txt` gives `file_path="home/johndoe/myfile.txt"`.

### Extra validation with `Path`

"Must be an integer" is often not strict enough. `Annotated` is a standard Python tool for attaching
extra information to a type hint. Its first item is the real type; the rest are notes for whoever
reads the hint, here FastAPI:

```python
from typing import Annotated
from fastapi import Path

@app.get("/items/{item_id}")
def read_item(item_id: Annotated[int, Path(title="The item ID", ge=1, le=1_000_000)]):
    return {"item_id": item_id}
```

`Annotated[int, Path(...)]` reads "an `int`, taken from the path, with these extra rules". `ge=1`
means *greater than or equal to* 1 and `le=1_000_000` means *less than or equal to* a million (the
underscores are only there to make the number readable). The complete set is `ge`, `gt` (greater
than), `le` and `lt` (less than). `title` and `description` appear in the docs.

## Query parameters

A **query parameter** is a `key=value` pair after the `?` in a URL. The rule is short: any function
parameter that is **not** named in the path template, and has a basic type, is read from the query
string.

```python
fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]

@app.get("/items/")
def read_items(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]
```

Here `skip` and `limit` are not in the path `/items/`, so they are query parameters. The body
`fake_items_db[skip : skip + limit]` is a list slice: start at position `skip` and take `limit`
entries. `GET /items/?skip=1&limit=1` therefore returns `[{"item_name": "Bar"}]`.

Whether a query parameter is required depends on its default value:

- A parameter **with a default** (`skip: int = 0`) is optional.
- A parameter with **no default** is required. Leaving it out gives a 422 with `"type": "missing"`.
- A default of `None` (`q: str | None = None`) makes it optional and lets your code tell "not sent"
  apart from any real value.
- A `bool` parameter accepts `1`, `true`, `True`, `on` and `yes` (and their opposites); FastAPI
  converts them to `True` or `False`.

Path and query parameters can be mixed in one function. FastAPI tells them apart by name:

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

`user_id` and `item_id` appear in the template, so they come from the path. `q` and `short` do not,
so they come from the query. `GET /users/3/items/pen?short=true` yields
`{"item_id": "pen", "owner_id": 3}`: no `q` was sent, and `short` suppressed the description.

### Validation and metadata with `Query`

`Query` plays the same role for query parameters as `Path` does for path parameters:

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

- `q` is optional text. If present it must be 3 to 50 characters long and match the `pattern`, a
  **regular expression** (a compact notation for describing text shapes); `^[a-z ]+$` means "only
  lower-case letters and spaces".
- `page` must be at least 1 and defaults to 1.
- `size` must be between 1 and 100 and defaults to 20.

Notice that the default value stays where Python normally puts it, after `=`. This `Annotated` style is
the one current FastAPI documentation recommends.

Other `Query` options: `alias="item-query"` (for when the name in the URL is not a legal Python name),
`deprecated=True`, `include_in_schema=False`, `title`, `description` and `examples`.

### Lists from repeated keys

```python
@app.get("/items/")
def read_items(tag: Annotated[list[str], Query()] = []):
    return {"tags": tag}
```

`GET /items/?tag=a&tag=b` returns `{"tags": ["a", "b"]}`. For a list you *must* write `Query()`
explicitly. Without it, FastAPI assumes a list-typed parameter belongs in the request **body**
(lesson 5).

### Query parameter models

Since FastAPI 0.115, related query parameters can be grouped into one class. The class below is a
Pydantic model, a kind of class studied in lesson 7; for now read it as "a named bundle of fields
with types and rules":

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

`limit` defaults to 100 and must be between 1 and 100; `offset` defaults to 0 and cannot be negative;
`order_by` uses `Literal`, a hint meaning "exactly one of these written values"; `tags` is a list.
The line `model_config = {"extra": "forbid"}` makes unknown query parameters an error instead of
being ignored.

## How FastAPI decides where a parameter comes from

This decision table is worth memorising. Rows three to six mention features from later lessons; they
are listed here so that you have the whole rule in one place.

| Declaration | Source |
|---|---|
| name appears in the path template | **path** |
| simple type (`int`, `str`, `float`, `bool`, `Enum`, `UUID`, `datetime`…) not in path | **query** |
| Pydantic model (no marker) | **body** (JSON) |
| `Annotated[..., Query()/Header()/Cookie()/Body()/Form()/File()]` | as marked |
| `Annotated[..., Depends(...)]` | a **dependency** |
| type `Request`, `Response`, `BackgroundTasks`, `WebSocket` | injected by the framework |

## A mini FastAPI in 40 lines

None of this is magic. Here is a toy framework that uses Python's `inspect` module and type hints to
route requests, pull out path and query parameters and convert their types. It is the same idea
FastAPI implements, far more completely, with Pydantic:

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

How the toy works:

- `get(template)` is the decorator. It turns `/users/{user_id}` into a regular expression in which
  each slot matches "one or more characters that are not a slash", and stores the compiled
  expression, the slot names and the function in `self.routes`.
- `handle(url)` plays the server. It splits the URL at `?`, parses the query string into a dictionary,
  and tries each route in order.
- For the first route that matches, `inspect.signature(fn).parameters` lists the function's
  parameters with their hints and defaults. Each value is looked up in the path if the name is a
  slot, otherwise in the query.
- A missing value falls back to the default, or is recorded as a `missing` error when there is none.
  A present value is converted by *calling the hint*: `p.annotation(raw)` is `int("7")` when the hint
  is `int`. If that raises `ValueError`, an `int_parsing` error is recorded.
- Any errors produce `422`; otherwise the function is called with the collected arguments. If no
  route matched at all the answer is `404`.

The six printed lines show: the fixed route winning for `/users/me`; `user_id` arriving as the number
`7` and `limit` as `3`; a 422 for `/users/x/...` because `x` is not an integer; a successful search;
a 422 because `term` is required; and a 404 for an unknown path.

The declaration order (`/users/me` first) and the type hints drive everything. Real FastAPI performs
this analysis **once at start-up**, when the decorator runs, and builds a set of checks for each
endpoint, so the cost per request stays low.

> [!INTERVIEW]
> "How does FastAPI know that `item_id` is a path parameter and `q` is a query parameter?" — At
> decoration time it inspects the function signature: names that appear in the path template are path
> parameters; remaining parameters of basic types are query parameters; Pydantic-model parameters are
> the body; anything wrapped in `Annotated[..., Query()/Header()/Body()/Depends()...]` follows the
> explicit marker. It then builds Pydantic validators for each, which run before the function is
> called and produce a 422 on failure.

## `def` or `async def`?

Both work. FastAPI runs `async def` endpoints directly on the event loop (lesson 3) and plain `def`
endpoints in a thread pool. A rule of thumb until the async module covers it in depth: use
`async def` when everything you call inside can be awaited (an async database driver,
`httpx.AsyncClient`); use `def` when you call libraries that block while they work (the classic
`requests` library, most machine-learning `model.predict` calls, synchronous database drivers).

## Tracing one request step by step

Take this endpoint, which combines everything above. Unlike the toy, this block is real FastAPI,
running inside your browser, so press **Run**:

```fastapi-run path=/users/7/items?limit=5&tag=red&tag=blue&debug=1
from typing import Annotated, Literal
from fastapi import FastAPI, Path, Query
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/users/{user_id}/items")
def list_user_items(
    user_id: Annotated[int, Path(ge=1)],
    status: Literal["open", "closed"] = "open",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    tag: Annotated[list[str], Query()] = [],
):
    return {"user_id": user_id, "status": status, "limit": limit, "tag": tag}

client = TestClient(app)
for url in ["/users/7/items?limit=5&tag=red&tag=blue&debug=1",
            "/users/0/items?limit=500&status=archived"]:
    r = client.get(url)
    print(r.status_code, r.json())
```

The endpoint returns its four arguments so that you can see what FastAPI handed it. The last five
lines send two requests without starting a server:

- `TestClient(app)` creates a **test client**: an object that plays the part of a browser and
  delivers requests straight to the app object, with no network in between. Lesson 22 covers it in
  depth.
- `client.get(url)` sends a `GET` request for that address and returns the response.
- `r.status_code` is the response's status number, and `r.json()` decodes the JSON body into Python
  dictionaries and lists.

The first printed line is the successful request, the second the failing one; both are explained
below. Under the code there is also a **request panel**. Choose a method, edit the path (for example
`/users/7/items?status=closed`) and press **Send** to see the status, the headers and the JSON body
the app returns. If you change the code, Send runs it again first.

Now follow the request `GET /users/7/items?limit=5&tag=red&tag=blue&debug=1` step by step:

1. **Routing.** Routes are tried in declaration order. The template becomes a regular expression
   roughly like `^/users/(?P<user_id>[^/]+)/items$`; it matches and captures `user_id="7"`, still text
   at this point.
2. **Path parameters.** FastAPI checks `"7"` against `int` with `ge=1` and gets `7`.
3. **Query parameters.** The query string is parsed into a structure that keeps repeated keys:
   `{"limit": ["5"], "tag": ["red", "blue"], "debug": ["1"]}`.
   - `status` is absent, so the default `"open"` is used.
   - `limit`: `"5"` becomes `5`, which is within 1 to 100.
   - `tag` is declared as a list, so every occurrence is collected: `["red", "blue"]`.
   - `debug` is not declared and is **silently ignored** (unless you use a query-parameter model with
     `extra="forbid"`).
4. **Call.** `list_user_items(user_id=7, status="open", limit=5, tag=["red", "blue"])`.
5. **Response.** The return value is converted to JSON and sent with status 200.

Now the failing variant, `GET /users/0/items?limit=500&status=archived`. Validation does **not** stop
at the first problem. All three are reported together, so the client can fix everything in one go:

```json
{"detail": [
  {"type": "greater_than_equal", "loc": ["path", "user_id"], "msg": "Input should be greater than or equal to 1", "input": "0", "ctx": {"ge": 1}},
  {"type": "literal_error", "loc": ["query", "status"], "msg": "Input should be 'open' or 'closed'", "input": "archived", "ctx": {"expected": "'open' or 'closed'"}},
  {"type": "less_than_equal", "loc": ["query", "limit"], "msg": "Input should be less than or equal to 100", "input": "500", "ctx": {"le": 100}}
]}
```

To read a 422: the first entry of `loc` names the part of the request (`path`, `query`, `header`,
`cookie` or `body`), the remainder of `loc` is the field's name, `type` is a stable code, `input`
echoes what was received, and `ctx` carries the rule that was broken.

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

A quick way to see exactly what FastAPI has registered:

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
- Using a mutable default such as `[]` carelessly. FastAPI copies defaults for each request, but your
  own helper functions will not; in plain Python one default list is shared by every call.
- Parsing booleans by hand. FastAPI's `bool` conversion is correct, but in plain Python
  `bool("false")` is `True`, because any non-empty string counts as true.
- A missing trailing slash. If only `/items/` is declared, FastAPI answers a request for `/items`
  with a `307` redirect to `/items/`. Clients that do not follow redirects for POST will be confused.
  Pick one style and keep to it.

## Summary

- `app = FastAPI()` plus `@app.get(path)` decorators define path operations; return values become JSON.
- Path parameters come from `{names}` in the template; type hints convert and check them.
- Other basic-typed parameters are query parameters; a default makes them optional.
- `Annotated[T, Path()/Query()]` adds rules (`ge`, `le`, `min_length`, `pattern`) and documentation.
- `/docs`, `/redoc` and `/openapi.json` are generated automatically.

## Glossary

- **Type hint (annotation)** — a note after a colon stating the expected type of a parameter.
- **Decorator** — an `@name` line that passes the function below it to other code for registration.
- **Virtual environment** — a per-project folder of installed Python packages.
- **Path operation** — one combination of a path and an HTTP method.
- **Path operation function (handler)** — the function FastAPI calls for a path operation.
- **Path template** — a path containing `{slots}`, such as `/items/{item_id}`.
- **Path parameter** — a value taken from a slot in the path.
- **Query parameter** — a value taken from the `key=value` pairs after `?`.
- **Conversion (coercion)** — turning the text from a URL into the declared Python type.
- **Validation** — checking that data obeys the declared rules; failures give `422`.
- **Enum** — a class that lists a fixed set of allowed values.
- **Annotated** — a hint that carries extra information: `Annotated[int, Path(ge=1)]`.
- **Literal** — a hint allowing only the listed values.
- **Regular expression** — a compact notation for describing the shape of text.
- **Swagger UI** — the interactive documentation page served at `/docs`.

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
   "explain": "The decorator inspects the signature and builds the parameter/validation model once; per-request work is only running the validators."}
]
```

> **Source:** Lubanovic, *FastAPI*, ch. 3 "FastAPI Tour" (A FastAPI Application, URL Path, Query Parameters, Type Conversion); https://fastapi.tiangolo.com/tutorial/first-steps/, /tutorial/path-params/, /tutorial/query-params/, /tutorial/query-params-str-validations/, /tutorial/query-param-models/
