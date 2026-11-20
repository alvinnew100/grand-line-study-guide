# Errors, exception handlers and middleware

A production API is judged less by its happy path than by how it fails: are errors consistent and
informative for clients, invisible to attackers, and loud for operators? This lesson covers FastAPI's
error machinery (`HTTPException`, validation errors, custom handlers), **middleware** for cross-cutting
behaviour, and **structured logging** with request IDs that ties it all together.

## HTTPException recap

```python
from fastapi import HTTPException, status

raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Item not found",                       # str, dict or list - anything JSON-serialisable
    headers={"X-Error-Code": "item_missing"},
)
```

FastAPI catches it and returns `{"detail": ...}` with that status. It's the right tool **in the web
layer**. Deeper layers should raise *domain* exceptions (the book's `Missing`, `Duplicate`) that know
nothing about HTTP.

## Custom exception handlers

Instead of `try/except` in every endpoint, register a translation once:

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

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
```

Now any endpoint can simply call `service.get_one(name)`; a `Missing` raised three layers down becomes a
clean 404. Handlers are matched by class, most specific first (a handler for a base class catches its
subclasses).

### Overriding the built-in handlers

FastAPI installs default handlers for `HTTPException`, `RequestValidationError` (→ 422) and
`ResponseValidationError`. Override them to enforce a house error format, e.g. RFC 9457 problem details:

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

Don't echo `exc.body` back in production (it may contain secrets the client mistyped into the wrong
field), and never include stack traces.

### The catch-all

Unhandled exceptions become a plain `500 Internal Server Error`, with the traceback logged by the server.
You can register `@app.exception_handler(Exception)` to shape the 500 body (e.g. include a request ID),
but keep the message generic — details go to logs, not clients.

A model of the dispatch logic:

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

## Middleware

**Middleware** wraps *every* request: code runs before the route is matched and after the response is
produced. Lubanovic introduces it in the security chapter, with CORS as the first example; other uses are
logging, timing, request IDs, compression, security headers and authentication gateways.

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

Built-in middleware you'll actually add:

```python
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["api.example.com", "*.example.com"])
app.add_middleware(CORSMiddleware, allow_origins=[...])
```

### Order: the onion

Each `add_middleware` wraps the existing stack, so **the last one added is the outermost** — it sees the
request first and the response last:

```mermaid
graph LR
    R[Request] --> M3[CORS - added last, outermost]
    M3 --> M2[TrustedHost]
    M2 --> M1[GZip - added first, innermost]
    M1 --> E[ExceptionMiddleware and router]
    E --> EP[Endpoint]
```

That's why CORS is usually added last (outermost): its headers must be on *every* response, including
errors generated by inner layers. Starlette also always wraps everything in `ServerErrorMiddleware`
(outermost; turns unhandled exceptions into 500) and puts `ExceptionMiddleware` (which runs your exception
handlers) innermost, just outside the router.

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

The problem *Middleware Onion* extends this with short-circuiting and error handling.

### Middleware vs dependencies

| | Middleware | Dependency |
|---|---|---|
| Runs for | every request (incl. 404s, static files, docs) | routes that declare it |
| Sees | raw request/response | validated, typed parameters |
| Can inject values into endpoints | only via `request.state` | yes, as arguments |
| In OpenAPI docs | no | yes (parameters, security) |
| Good for | logging, timing, IDs, headers, compression, CORS | auth, DB sessions, per-route limits |

Rule of thumb: **truly global, HTTP-level concerns → middleware; anything about business inputs or
selectively applied → dependencies.**

> [!WARNING]
> `@app.middleware("http")` (Starlette's `BaseHTTPMiddleware`) is convenient but has costs: it adds
> overhead per request and has historically interfered with streaming responses, background tasks and
> `contextvars` propagation. For hot paths or streaming-heavy apps, write **pure ASGI middleware** (a
> class with `async def __call__(self, scope, receive, send)`) — which is also how the built-ins are
> written. And never read the request body in middleware unless you must: it consumes the stream.

## Logging with request IDs

When a user reports "error at 14:32", you need to find *that request's* log lines among thousands. Give
every request an ID, put it in every log line, and return it in a header:

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

`contextvars` are the async-safe replacement for thread-locals: each request's task sees its own value,
even though all share one thread. Emit logs as **JSON, one object per line, to stdout** so the platform's
log collector can index fields:

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

Logging hygiene: never log passwords, tokens, full request bodies or personal data; use levels
consistently (INFO for requests, WARNING for handled anomalies, ERROR with traceback for bugs); and avoid
logging inside tight loops. Lubanovic's service-layer chapter groups logging with metrics and tracing as
the three ways you'll understand a running system — the deployment module returns to these.

> [!INTERVIEW]
> "Middleware or dependency for authentication?" — Usually a dependency: it's typed, composable
> (`CurrentUser`), documented in OpenAPI (the Authorize button), overridable in tests, and can be applied
> per route or router, leaving health/docs/login open. Middleware suits blanket HTTP-level concerns —
> request IDs, logging, timing, CORS, compression, security headers — or a coarse gate in front of
> everything (e.g. a shared-secret check for an internal service). The two also differ in ordering:
> middleware runs before routing; dependencies after.

## Pitfalls

- `try/except Exception: return {"error": ...}` with status 200 — hides failures from monitoring.
- Leaking tracebacks or SQL errors in responses.
- Adding CORS middleware first (innermost) so error responses from outer layers lack CORS headers.
- Heavy work or body reads in middleware — it taxes every request.
- Registering a handler for FastAPI's `HTTPException` but missing Starlette's (router 404s keep the old
  format).
- Logging secrets; no request ID.

## Summary

- Raise domain exceptions below the web layer; map them to HTTP once with `@app.exception_handler`.
- Override `RequestValidationError`/`HTTPException` handlers for a uniform error format; keep 500s generic.
- Middleware wraps all requests like an onion — last added is outermost.
- Global HTTP concerns → middleware; typed, per-route concerns → dependencies.
- Structured JSON logs with a per-request ID (via `contextvars`) make production debuggable.

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
