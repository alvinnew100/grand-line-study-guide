# Errors, exception handlers and middleware

> **Before this lesson:** you should know how to raise `HTTPException`
> ([lesson 5](#/lesson/fastapi/body-responses)), what domain exceptions such as `Missing` are and
> why lower layers raise them ([lesson 15](#/lesson/fastapi/layers)), and how ASGI middleware wraps
> an app ([lesson 3](#/lesson/fastapi/asgi-stack)). In Python you need `try` / `except` and class
> inheritance.

## In plain words

Things go wrong in every program: a record is missing, the input is malformed, a bug divides by
zero. An API is judged less by what it does when all is well than by how it fails. A good failure
has three properties. The client gets a clear and *consistent* message it can act on. An attacker
learns nothing useful from it. And the people who run the service are told loudly, with enough
detail to find the cause.

This lesson has three parts, and each maps onto a familiar picture, a hospital.

- **Exception handlers** are the triage desk. However a patient arrives and whatever is wrong, one
  desk classifies the case and sends it the right way. You write the rule "this kind of error
  becomes that kind of response" once, not in every endpoint.
- **Middleware** is the reception everyone walks through on the way in and again on the way out:
  sign the visitor book, get a wristband. It is the place for things that must happen for *every*
  request, such as timing it and labelling it.
- **Structured logging with request IDs** is the wristband number written on every form and test
  result, so that all the paperwork for one visit can be pulled together later.

Why this matters for a job: debugging in production means finding the handful of log lines that
belong to one failed request among millions. Interviewers ask "middleware or dependency?" and "what
should a 500 response contain?", and both are answered here.

## HTTPException recap

```python
from fastapi import HTTPException, status

raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Item not found",                       # str, dict or list - anything JSON-serialisable
    headers={"X-Error-Code": "item_missing"},
)
```

FastAPI catches the exception and sends `{"detail": ...}` with the given status and headers. This is
the right tool **in the web layer**. Deeper layers should raise *domain* exceptions (the book's
`Missing` and `Duplicate`, lesson 15), which know nothing about HTTP. The question is how those
become responses without a `try` / `except` in every endpoint.

## Custom exception handlers

An **exception handler** is a function you register with the app for one exception class. Whenever
that exception escapes from any endpoint, FastAPI calls the handler and sends what it returns:

```fastapi-run path=/explorers/Nobody
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

class Missing(Exception):
    def __init__(self, msg: str): self.msg = msg

class Duplicate(Exception):
    def __init__(self, msg: str): self.msg = msg

app = FastAPI()

@app.exception_handler(Missing)
async def missing_handler(request: Request, exc: Missing):
    return JSONResponse(status_code=404, content={"detail": exc.msg})

@app.exception_handler(Duplicate)
async def duplicate_handler(request: Request, exc: Duplicate):
    return JSONResponse(status_code=409, content={"detail": exc.msg})

# --- a tiny service layer that knows nothing about HTTP --------------------
explorers = {"Claude Hande": "France"}

def get_one(name: str) -> dict:
    if name not in explorers:
        raise Missing(f"Explorer {name} not found")
    return {"name": name, "country": explorers[name]}

def create(name: str, country: str) -> dict:
    if name in explorers:
        raise Duplicate(f"Explorer {name} already exists")
    explorers[name] = country
    return {"name": name, "country": country}

# --- the web layer: no try / except anywhere --------------------------------
@app.get("/explorers/{name}")
def read_explorer(name: str):
    return get_one(name)

@app.post("/explorers", status_code=201)
def add_explorer(name: str, country: str):
    return create(name, country)

client = TestClient(app)
for method, url in [("GET", "/explorers/Claude Hande"), ("GET", "/explorers/Nobody"),
                    ("POST", "/explorers?name=Noah Weiser&country=Germany"),
                    ("POST", "/explorers?name=Noah Weiser&country=Germany")]:
    r = client.request(method, url)
    print(method, url, "->", r.status_code, r.json())
```

- `Missing` and `Duplicate` are the domain exceptions, each carrying a message.
- `@app.exception_handler(Missing)` registers the function below it for that class.
- The handler receives the request and the exception object, and returns a `JSONResponse` with
  status 404 and the message.
- The second handler does the same for `Duplicate`, with 409.
- `get_one` and `create` play the service layer (lesson 15). They raise the domain exceptions and
  never mention a status code.
- The two endpoints call the service with no error handling of their own.
- The loop at the bottom sends four requests with the test client from lesson 4;
  `client.request(method, url)` is the general form of `client.get` and `client.post`.

Press **Run**. The first request finds the explorer (`200`), the second becomes a `404` through
`missing_handler`, the third creates Noah Weiser (`201`) and the fourth, a repeat of the third, becomes
a `409` through `duplicate_handler`. Then try other names in the request panel.

Now an endpoint can call `service.get_one(name)` with no `try` / `except` at all. A `Missing` raised
three layers down becomes a clean 404. Handlers are chosen by class, the most specific first, and a
handler registered for a base class also catches its subclasses.

### Overriding the built-in handlers

FastAPI installs handlers of its own for `HTTPException`, for `RequestValidationError` (the 422
case) and for `ResponseValidationError`. You can replace them to impose a single error format for
your whole API, for example the RFC 9457 "problem details" format from lesson 2:

```python
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        media_type="application/problem+json",
        content={"type": "https://example.com/problems/validation", "title": "Invalid request",
                 "status": 422, "errors": jsonable_encoder(exc.errors()),
                 "instance": request.url.path},
    )

@app.exception_handler(StarletteHTTPException)       # register for Starlette's class to also catch
async def http_handler(request, exc):                # router-generated 404/405s
    return JSONResponse(status_code=exc.status_code,
                        content={"title": exc.detail, "status": exc.status_code},
                        headers=exc.headers)
```

The first handler replaces the default 422 body. `exc.errors()` is Pydantic's list of problems, and
`jsonable_encoder` makes sure it can be written as JSON. The second is registered for *Starlette's*
`HTTPException` class. That detail matters: the 404 for an unknown address and the 405 for a wrong
method are raised by Starlette's router with Starlette's class. FastAPI's `HTTPException` is a
subclass of it, so a handler for the Starlette class catches both.

Do not send `exc.body` back to the client in production, since it may contain a password that was
typed into the wrong field. And never include a **stack trace** (also called a traceback): the list
of function calls that led to an error. It is exactly what you want in a log and exactly what an
attacker wants in a response.

### The catch-all

An exception that no handler claims becomes a plain `500 Internal Server Error`, and the server
writes the traceback to its log. You may register `@app.exception_handler(Exception)` to shape the
body of that 500, for example to include a request ID. Keep the message general: details belong in
logs, not in responses.

A model of how the right handler is found:

```python-run
class HTTPException(Exception):
    def __init__(self, status_code, detail): self.status_code, self.detail = status_code, detail
class Missing(Exception): ...
class Duplicate(Exception): ...
class ValidationError(Exception):
    def __init__(self, errors): self.errors = errors

handlers = {
    HTTPException:   lambda e: (e.status_code, {"detail": e.detail}),
    ValidationError: lambda e: (422, {"detail": e.errors}),
    Missing:         lambda e: (404, {"detail": str(e)}),
    Duplicate:       lambda e: (409, {"detail": str(e)}),
}

def call(endpoint):
    try:
        return 200, endpoint()
    except Exception as exc:
        for cls in type(exc).__mro__:                 # most specific class first
            if cls in handlers:
                return handlers[cls](exc)
        print("  [log] unhandled:", repr(exc))        # traceback goes to logs...
        return 500, {"detail": "Internal Server Error"}   # ...not to the client

def ok(): return {"name": "yeti"}
def missing(): raise Missing("Creature bigfoot not found")
def dup(): raise Duplicate("Creature yeti already exists")
def forbidden(): raise HTTPException(403, "Not enough permissions")
def invalid(): raise ValidationError([{"loc": ["body", "name"], "type": "missing"}])
def bug(): return 1 / 0

for ep in (ok, missing, dup, forbidden, invalid, bug):
    print(ep.__name__, "->", call(ep))
```

- The four exception classes at the top stand in for the real ones.
- `handlers` maps each class to a small function returning a (status, body) pair.
- `call(endpoint)` runs the endpoint. If an exception escapes, it walks through
  `type(exc).__mro__`, which is the exception's class followed by its parent classes in order, and
  uses the first class that has a handler. That is the "most specific first" rule.
- If no class matches, it prints a log line and returns a general 500.

The output shows each case: `ok` gives 200; `missing` gives 404 with its message; `dup` gives 409;
`forbidden` gives 403; `invalid` gives 422 with the list of errors. The last endpoint has a real bug
(`1 / 0`). A log line reports `ZeroDivisionError('division by zero')`, and the client sees only
`(500, {'detail': 'Internal Server Error'})`.

## Middleware

**Middleware** is code that wraps *every* request: part of it runs before the route is even chosen,
and part after the response has been produced. Lubanovic introduces it in his security chapter with
CORS as the first example. Other uses are logging, timing, request IDs, compression, security
headers and blanket checks. Tasks like these, which cut across all endpoints instead of belonging to
one, are called **cross-cutting concerns**.

```python
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)            # run the rest of the app
    response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.4f}"
    return response
```

- `@app.middleware("http")` registers the function as middleware for HTTP requests.
- The function receives the request and `call_next`, a function that runs "everything further in":
  other middleware, the routing and the endpoint.
- The lines before `await call_next(request)` run on the way in; here they note the start time.
- The lines after it run on the way out; here they add an `X-Process-Time` header.

Ready-made middleware you will really add:

```python
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["api.example.com", "*.example.com"])
app.add_middleware(CORSMiddleware, allow_origins=[...])
```

`GZipMiddleware` compresses large responses. `TrustedHostMiddleware` rejects requests whose `Host`
header is not one of yours. `CORSMiddleware` is the subject of lesson 20.

### Order: the onion

Each `add_middleware` call wraps everything added so far. Therefore **the one added last is the
outermost**: it sees the request first and the response last.

```mermaid
graph LR
    R[Request] --> M3[CORS - added last, outermost]
    M3 --> M2[TrustedHost]
    M2 --> M1[GZip - added first, innermost]
    M1 --> E[ExceptionMiddleware and router]
    E --> EP[Endpoint]
```

This is why CORS is usually added last, making it outermost: its headers must be on *every*
response, including errors produced by inner layers. Starlette also always wraps everything in a
`ServerErrorMiddleware`, at the very outside, which turns exceptions nobody handled into 500
responses. And it places an `ExceptionMiddleware`, which runs your exception handlers, at the very
inside, directly around the router.

```python-run
def make_app(order_log):
    def endpoint(request):
        order_log.append("endpoint")
        return {"status": 200, "headers": {}}

    def middleware(name, inner):
        def handler(request):
            order_log.append(f"{name}: before")
            response = inner(request)
            order_log.append(f"{name}: after")
            response["headers"][f"x-{name}"] = "1"
            return response
        return handler

    app = endpoint
    for name in ["gzip", "trustedhost", "cors"]:      # add_middleware order
        app = middleware(name, app)                   # each wraps the previous stack
    return app

log = []
resp = make_app(log)({"path": "/"})
print("\n".join(log))
print(resp)
```

`make_app` builds the onion from plain functions. `middleware(name, inner)` returns a handler that
logs "before", calls the inner handler, logs "after" and adds a header. The loop wraps the endpoint
in `gzip`, then `trustedhost`, then `cors`, in the same order as three `add_middleware` calls.

The printed log reads `cors: before`, `trustedhost: before`, `gzip: before`, `endpoint`,
`gzip: after`, `trustedhost: after`, `cors: after`. The middleware added last ran first on the way
in and last on the way out. The response carries all three headers.

The problem *Middleware Onion* extends this with short-circuiting and error handling.

### Middleware vs dependencies

Both run code around your endpoint, so which should you use?

| | Middleware | Dependency |
|---|---|---|
| Runs for | every request (incl. 404s, static files, docs) | routes that declare it |
| Sees | raw request/response | validated, typed parameters |
| Can inject values into endpoints | only via `request.state` | yes, as arguments |
| In OpenAPI docs | no | yes (parameters, security) |
| Good for | logging, timing, IDs, headers, compression, CORS | auth, DB sessions, per-route limits |

A rule of thumb: **concerns that are truly global and belong to HTTP itself go in middleware;
anything to do with the application's inputs, or applied only to some routes, goes in
dependencies.**

> [!WARNING]
> `@app.middleware("http")` (Starlette's `BaseHTTPMiddleware`) is convenient but has costs. It adds
> overhead to every request, and it has a history of interfering with streaming responses,
> background tasks and context variables. For heavily used paths, or apps that stream a lot, write
> **pure ASGI middleware**: a class with `async def __call__(self, scope, receive, send)`, as in
> lesson 3. The built-in middleware is written that way. And never read the request body in
> middleware unless you must, because reading it uses it up.

## Logging with request IDs

A **log** is the running record a program writes of what it is doing. When a user reports "I got an
error at 14:32", you need to find the lines for *that request* among thousands. The method: give
every request an identifier, put it in every log line, and return it in a response header so the
user can quote it.

```python
import contextvars, logging, uuid

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True

@app.middleware("http")
async def request_context(request: Request, call_next):
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex
    token = request_id_var.set(rid)
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("unhandled error")           # includes traceback + request_id
        raise
    finally:
        request_id_var.reset(token)
    response.headers["X-Request-ID"] = rid
    logger.info("request", extra={"method": request.method, "path": request.url.path,
                                  "status": response.status_code,
                                  "duration_ms": round((time.perf_counter() - start) * 1000, 1)})
    return response
```

- `request_id_var` is a **context variable**. A plain global variable would not work here, because
  many requests are in progress at the same time on one thread and would overwrite each other's
  value. A `ContextVar` holds a separate value for each task, so each request sees its own ID.
- `RequestIdFilter` copies the current ID onto every log record.
- The middleware takes the ID from an incoming `X-Request-ID` header if there is one (so that an ID
  can follow a request across several services), and otherwise invents one. It stores the ID, calls
  the rest of the app, logs any exception together with its traceback, and finally restores the
  variable.
- On the way out it adds the header and writes one log line with the method, path, status and
  duration.

Write logs as **JSON, one object per line, to standard output**. Logging in a format that machines
can parse is called **structured logging**, and it lets the platform's log collector search by
field, for example "all lines where `status` is 500".

```python-run
import contextvars, io, json, logging

request_id = contextvars.ContextVar("request_id", default="-")

class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {"level": record.levelname, "logger": record.name, "msg": record.getMessage(),
                   "request_id": request_id.get()}
        for key in ("method", "path", "status", "duration_ms"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info).splitlines()[-1]
        return json.dumps(payload)

stream = io.StringIO()
handler = logging.StreamHandler(stream)
handler.setFormatter(JsonFormatter())
log = logging.getLogger("app"); log.handlers = [handler]; log.setLevel(logging.INFO); log.propagate = False

request_id.set("3f2a9c")
log.info("request", extra={"method": "GET", "path": "/items/42", "status": 200, "duration_ms": 12.3})
try:
    1 / 0
except ZeroDivisionError:
    log.exception("unhandled error")
print(stream.getvalue())
```

`JsonFormatter` turns each log record into a dictionary (level, logger name, message, request ID and
any extra fields) and writes it as JSON. If the record carries an exception, the last line of the
traceback is included. The demo sets the request ID to `3f2a9c` and logs two events.

The output is two JSON lines. The first is an `INFO` line with `"request_id": "3f2a9c"`,
`"method": "GET"`, `"path": "/items/42"`, `"status": 200` and `"duration_ms": 12.3`. The second is
an `ERROR` line with the same request ID and `"exc": "ZeroDivisionError: division by zero"`. Because
they share an ID, a search for it finds both.

Logging hygiene: never log passwords, tokens, complete request bodies or personal data. Use the
**levels** consistently: INFO for ordinary requests, WARNING for oddities that were handled, ERROR
with a traceback for bugs. Avoid logging inside tight loops. Lubanovic's service-layer chapter
groups logging with metrics and tracing as the three ways of understanding a running system; the
deployment module returns to them.

> [!INTERVIEW]
> "Middleware or dependency for authentication?" — Usually a dependency: it is typed, it composes
> (`CurrentUser`), it is documented in OpenAPI (the Authorize button), it can be overridden in
> tests, and it can be applied per route or router, leaving health, docs and login endpoints open.
> Middleware suits blanket concerns at the HTTP level (request IDs, logging, timing, CORS,
> compression, security headers) or a coarse gate in front of everything, such as a shared-secret
> check for an internal service. The two also differ in order: middleware runs before routing, and
> dependencies after it.

## Worked example: one error contract for the whole API

Here is a complete setup of the kind used in production: a small family of domain errors, one
handler that renders all of them, and replacements for the validation handler and the catch-all, so
that **every** error response has the same shape and carries the request ID.

```python
# app/errors.py
class AppError(Exception):
    """Base class for expected, client-visible failures."""
    status_code = 400
    code = "bad_request"
    def __init__(self, message: str, **extra):
        self.message, self.extra = message, extra

class NotFound(AppError):          status_code, code = 404, "not_found"
class Conflict(AppError):          status_code, code = 409, "conflict"
class PermissionDenied(AppError):  status_code, code = 403, "permission_denied"
class RateLimited(AppError):       status_code, code = 429, "rate_limited"

def error_body(request: Request, status: int, code: str, message: str, **extra) -> dict:
    return {"error": {"code": code, "message": message, "status": status,
                      "request_id": request_id_var.get(), **extra}}

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)                       # one handler covers every subclass
    async def app_error(request: Request, exc: AppError):
        headers = {"Retry-After": str(exc.extra["retry_after"])} if "retry_after" in exc.extra else None
        return JSONResponse(error_body(request, exc.status_code, exc.code, exc.message, **exc.extra),
                            status_code=exc.status_code, headers=headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        fields = [{"field": ".".join(map(str, e["loc"][1:])), "in": e["loc"][0], "type": e["type"]}
                  for e in exc.errors()]
        return JSONResponse(error_body(request, 422, "validation_failed", "Invalid request", fields=fields),
                            status_code=422)

    @app.exception_handler(StarletteHTTPException)         # router 404/405 and explicit HTTPExceptions
    async def http_error(request: Request, exc: StarletteHTTPException):
        return JSONResponse(error_body(request, exc.status_code, "http_error", str(exc.detail)),
                            status_code=exc.status_code, headers=exc.headers)

    @app.exception_handler(Exception)                      # the unexpected
    async def unhandled(request: Request, exc: Exception):
        logger.exception("unhandled error")                # full traceback, server-side only
        return JSONResponse(error_body(request, 500, "internal_error", "Internal server error"),
                            status_code=500)
```

- `AppError` is the base class for failures a client is meant to see. Each subclass sets two class
  attributes: an HTTP status and a short machine-readable `code`.
- `error_body` builds the one shape used everywhere:
  `{"error": {"code", "message", "status", "request_id", ...}}`.
- `register_exception_handlers` installs four handlers: one for `AppError`, which covers every
  subclass; one that flattens validation errors into a list of fields; one for HTTP exceptions,
  including the router's 404 and 405; and one for everything unexpected, which logs the full
  traceback and answers with a general 500.

A service can now write `raise NotFound("Order 9 not found")` or
`raise RateLimited("Slow down", retry_after=30)` and nothing more. Here is the same logic in
runnable form, showing the responses a client would receive:

```python-run
import json

class AppError(Exception):
    status_code, code = 400, "bad_request"
    def __init__(self, message, **extra): self.message, self.extra = message, extra
class NotFound(AppError):    status_code, code = 404, "not_found"
class Conflict(AppError):    status_code, code = 409, "conflict"
class RateLimited(AppError): status_code, code = 429, "rate_limited"
class ValidationFailed(Exception):
    def __init__(self, errors): self.errors = errors

def body(status, code, message, request_id, **extra):
    return {"error": {"code": code, "message": message, "status": status, "request_id": request_id, **extra}}

def handle(endpoint, request_id="req-7f3a"):
    try:
        return 200, endpoint()
    except AppError as e:                                   # catches every subclass
        return e.status_code, body(e.status_code, e.code, e.message, request_id, **e.extra)
    except ValidationFailed as e:
        fields = [{"field": ".".join(map(str, loc[1:])), "in": loc[0], "type": t} for loc, t in e.errors]
        return 422, body(422, "validation_failed", "Invalid request", request_id, fields=fields)
    except Exception as e:
        print(f"   [server log] request_id={request_id} unhandled {type(e).__name__}: {e}")
        return 500, body(500, "internal_error", "Internal server error", request_id)

def missing():  raise NotFound("Order 9 not found")
def dup():      raise Conflict("Email already registered", field="email")
def limited():  raise RateLimited("Too many requests", retry_after=30)
def invalid():  raise ValidationFailed([(("body", "items", 1, "quantity"), "greater_than_equal"),
                                        (("query", "limit"), "int_parsing")])
def bug():      return {}["missing-key"]

for ep in (missing, dup, limited, invalid, bug):
    status, payload = handle(ep)
    print(status, json.dumps(payload))
```

The five lines of output:

- `404` with code `not_found`.
- `409` with code `conflict` and the extra key `"field": "email"`.
- `429` with code `rate_limited` and `"retry_after": 30`.
- `422` with code `validation_failed` and a `fields` list. The location
  `("body", "items", 1, "quantity")` has become `{"field": "items.1.quantity", "in": "body", ...}`.
- A server log line naming the `KeyError`, followed by `500` with code `internal_error`. Nothing
  about the key appears in the response.

Every body has the same outer shape and the same `request_id`. Points worth copying: a stable `code`
for programs, kept apart from the `message` for people; the request ID in every error, so that a
user can quote it to support staff; validation errors flattened into a predictable list; and exactly
one place where an unexpected exception is logged in full while the client sees nothing internal.

> [!NOTE]
> A handler registered for `Exception` runs inside Starlette's outermost `ServerErrorMiddleware`, so
> the response it returns does **not** travel back through your other middleware. If CORS headers or
> a request-ID header must appear on 500 responses too, add them in that handler, or catch
> exceptions inside your own middleware.

## Where does an exception get caught?

The layering inside Starlette decides who sees what, from the outside inwards:

```text
ServerErrorMiddleware          <- catches anything that escapes: logs it, returns 500
  your middleware (last added = outermost)
    ...
      ExceptionMiddleware      <- runs @app.exception_handler functions (HTTPException, your classes)
        router -> dependencies -> endpoint
```

Consequences:

1. An exception *with* a registered handler is converted into a response inside your middleware. A
   middleware written as `response = await call_next(request)` receives an ordinary 404 or 409
   response and never sees the exception.
2. An exception *without* a handler travels outwards through `call_next`. A `try` / `except` in
   middleware can observe it, which is useful for logging and metrics, and should re-raise it.
3. Exceptions raised **by middleware itself** are outside `ExceptionMiddleware`. Your
   `@app.exception_handler(NotFound)` will *not* handle a `NotFound` raised in middleware. Return a
   response from the middleware directly.
4. Errors in the clean-up part of a `yield` dependency that runs after the response has been sent
   (lesson 11) can only be logged.

## Debugging error-handling problems

| Symptom | Cause |
|---|---|
| Custom handler never runs for 404s on unknown URLs | registered for `fastapi.HTTPException`; the router raises Starlette's — register for `starlette.exceptions.HTTPException` |
| Handler for `Exception` seems ignored in tests | `TestClient` re-raises server exceptions by default; use `raise_server_exceptions=False` |
| Browser shows a CORS error on failures only | the 500 response was produced outside `CORSMiddleware` and has no CORS headers |
| Response is `200` with an exception's text in it | `return HTTPException(...)` instead of `raise` |
| `RuntimeError: No response returned` from middleware | an exception or client disconnect inside `BaseHTTPMiddleware`'s `call_next`; check the first traceback above it |
| Streaming or background tasks behave oddly behind `@app.middleware("http")` | `BaseHTTPMiddleware` limitations; rewrite as pure ASGI middleware |
| Request body is empty in the endpoint | middleware consumed the body stream |

## Pitfalls

- `try: ... except Exception: return {"error": ...}` with status 200. Monitoring tools never see the
  failure.
- Tracebacks or SQL errors leaking into responses.
- Adding the CORS middleware first, which makes it innermost, so that error responses from outer
  layers lack CORS headers.
- Heavy work, or reading the body, in middleware. Every request pays for it.
- Registering a handler for FastAPI's `HTTPException` and missing Starlette's, so that the router's
  404s keep the old format.
- Logging secrets; having no request ID.

## Summary

- Raise domain exceptions below the web layer; map them to HTTP once with `@app.exception_handler`.
- Override the `RequestValidationError` and `HTTPException` handlers for one error format
  everywhere; keep 500s general.
- Middleware wraps all requests like an onion, and the one added last is outermost.
- Global HTTP concerns go in middleware; typed, per-route concerns go in dependencies.
- Structured JSON logs with an ID per request (through `contextvars`) make production debuggable.

## Glossary

- **Exception handler** — a function registered for an exception class that turns it into a response.
- **Domain exception** — an error class in the application's own vocabulary, free of HTTP details.
- **Stack trace (traceback)** — the chain of function calls that led to an error.
- **Catch-all** — a handler for `Exception`, covering whatever nothing else handled.
- **MRO** — a class followed by its parent classes, in the order Python searches them.
- **Middleware** — code that wraps every request and response.
- **Cross-cutting concern** — a task that applies to all endpoints, such as logging.
- **`call_next`** — in middleware, the function that runs the rest of the app.
- **Onion model** — middleware as nested layers; the one added last is outermost.
- **Log / log level** — the running record a program writes / the severity label on each entry.
- **Structured logging** — logging in a machine-readable format, usually one JSON object per line.
- **Request ID** — an identifier given to one request and written on all its log lines.
- **Context variable** — a variable with a separate value for each concurrent task.
- **Error contract** — the one agreed shape for every error response of an API.

```quiz
[
  {"q": "You add middleware A, then B, then C with app.add_middleware. Which sees the incoming request first?", "options": ["A", "B", "C", "They run in parallel"], "answer": 2,
   "explain": "Each add wraps the existing stack, so the last added (C) is outermost."},
  {"q": "What does FastAPI return by default when the body fails Pydantic validation?", "options": ["400 with a string", "422 with a detail list of errors (loc, type, msg)", "500", "200 with warnings"], "answer": 1,
   "explain": "RequestValidationError is handled by a built-in handler producing 422 and structured details."},
  {"q": "Best way to convert a domain exception like Missing (raised in the data layer) into a 404?", "options": ["Raise HTTPException in the data layer", "Register @app.exception_handler(Missing) in the web layer", "Return None everywhere", "Use a Pydantic validator"], "answer": 1,
   "explain": "A single handler keeps HTTP knowledge in the web layer and removes repetitive try/except."},
  {"q": "Why use contextvars rather than a global variable for the request ID?", "options": ["Globals are slower", "Many requests interleave on one thread; a ContextVar holds a separate value per task", "ContextVars persist to disk", "Globals can't hold strings"], "answer": 1,
   "explain": "A global would be overwritten by concurrent requests; context variables are task-local."},
  {"q": "Which concern is best implemented as a dependency rather than middleware?", "options": ["Adding X-Request-ID to every response", "GZip compression", "Loading the current user and enforcing scopes on selected routes", "CORS"], "answer": 2,
   "explain": "Auth needs typed values injected into endpoints, per-route application and OpenAPI documentation."},
  {"q": "What should a 500 response body contain in production?", "options": ["The full stack trace", "The SQL that failed", "A generic message, ideally with a request ID; details go to server logs", "Environment variables"], "answer": 2,
   "explain": "Internal details help attackers; operators find the traceback in logs via the request ID."},
  {"q": "An unhandled exception occurs in an endpoint. Which Starlette component produces the 500?", "options": ["CORSMiddleware", "ServerErrorMiddleware (outermost)", "GZipMiddleware", "The router"], "answer": 1,
   "explain": "ServerErrorMiddleware wraps the whole stack and converts uncaught exceptions to 500 responses."}
]
```

> **Source:** Lubanovic, *FastAPI*, ch. 9 "Service Layer" (Logging; Metrics, Monitoring, Observability; Tracing), ch. 10 "Data Layer" (Missing/Duplicate exceptions), ch. 11 "Authentication and Authorization" (Middleware, CORS); https://fastapi.tiangolo.com/tutorial/handling-errors/, /tutorial/middleware/, /advanced/middleware/
