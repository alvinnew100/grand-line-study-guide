# APIRouter and bigger applications

A single `main.py` is perfect for learning and miserable for a real service. Once you have more than a
handful of endpoints you want to split them into modules by topic — users, items, auth, admin, health —
each with its own prefix, tags and dependencies. FastAPI's tool for this is **`APIRouter`**. Lubanovic
introduces it in his web-layer chapter under "Multiple Routers": a router is like a mini `FastAPI` app
that the top-level app plugs in.

## From one file to routers

```python
# app/routers/items.py
from fastapi import APIRouter, HTTPException, status
from app.schemas import Item, ItemCreate

router = APIRouter(
    prefix="/items",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
def list_items() -> list[Item]: ...

@router.get("/{item_id}")
def get_item(item_id: int) -> Item: ...

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate) -> Item: ...
```

```python
# app/main.py
from fastapi import Depends, FastAPI
from app.routers import items, users, admin
from app.deps import require_admin

app = FastAPI(title="Shop API")

app.include_router(users.router)
app.include_router(items.router)
app.include_router(
    admin.router,
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],        # applied to every admin route
)

@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}
```

A router supports the same decorators as the app (`@router.get`, `.post`, ..., `@router.websocket`).
`include_router` *copies* the router's routes into the app, combining settings:

| Setting | Where it can be set | How they combine |
|---|---|---|
| `prefix` | `APIRouter(...)`, `include_router(...)` | concatenated: include prefix + router prefix + route path |
| `tags` | router, include, route | merged |
| `dependencies` | app, include, router, route decorator | all run: app → include → router → route → parameters |
| `responses` | router, include, route | merged |
| `deprecated`, `include_in_schema` | include, router, route | inherited |

Because routes are copied at include time, there is **no runtime overhead** for nesting — the final app
has a flat route table.

> [!TIP]
> Prefixes must not end with `/`. With `prefix="/items"`, `@router.get("/")` serves `/items/` and
> `@router.get("")` serves `/items`. Pick one convention; Starlette redirects between the two by default
> (`redirect_slashes=True`), which costs clients a round trip.

## Nesting and versioning

Routers can include routers, which gives a clean way to version an API:

```python
# app/api/v1/__init__.py
from fastapi import APIRouter
from . import items, users, predict

api_v1 = APIRouter(prefix="/v1")
api_v1.include_router(users.router)
api_v1.include_router(items.router)
api_v1.include_router(predict.router)

# app/main.py
app.include_router(api_v1)        # /v1/users, /v1/items, /v1/predict
app.include_router(api_v2)        # /v2/...
```

You can even include the *same* router twice with different prefixes (e.g. `/v1/items` and a legacy
`/items` marked `deprecated=True`) — the routes are duplicated in the table and in the docs.

For hard isolation (separate docs, separate middleware) you can **mount** a whole sub-application:
`app.mount("/internal", internal_app)`. A mounted app is independent — its own OpenAPI, its own
dependency overrides — whereas an included router is part of the parent app.

## A project layout that scales

The official "Bigger Applications" tutorial suggests:

```text
app/
├── __init__.py
├── main.py              # creates FastAPI(), includes routers, lifespan, middleware
├── config.py            # Settings (pydantic-settings)
├── dependencies.py      # shared Depends: get_session, get_current_user, ...
├── routers/
│   ├── __init__.py
│   ├── items.py
│   └── users.py
├── schemas/             # Pydantic request/response models
├── models/              # ORM table models
├── services/            # business logic
├── db.py                # engine, session factory
└── internal/
    └── admin.py
tests/
```

Lubanovic's book uses an equivalent structure with different folder names, organised by **layer**
(next lesson): `src/web/` (routers), `src/service/`, `src/data/`, `src/model/`, `src/fake/`, and
`src/test/`. His `main.py` does very little beyond creating the app and including one router per
resource:

```python
# main.py in the book's style
from fastapi import FastAPI
from web import explorer, creature

app = FastAPI()
app.include_router(explorer.router)
app.include_router(creature.router)
```

For larger codebases a **feature-based** (a.k.a. domain-based) layout is popular: one package per feature,
each containing its own router, schemas, service and models:

```text
app/
├── users/      (router.py, schemas.py, service.py, models.py)
├── orders/     (router.py, schemas.py, service.py, models.py)
└── core/       (config.py, db.py, security.py)
```

Layer-based keeps similar code together and suits small/medium apps; feature-based keeps a feature's code
together and suits many teams. Both work with `APIRouter` identically.

## Avoiding circular imports

The classic mistake: `routers/items.py` does `from app.main import app`, and `main.py` imports
`routers.items` → circular import. Rules that prevent it:

- Routers never import `main`. `main` imports routers — one direction only.
- Shared things (`get_session`, `Settings`, security helpers) live in neutral modules (`dependencies.py`,
  `config.py`) that both can import.
- Need the app instance inside an endpoint? Use `request.app` (e.g. `request.app.state.model`).

## An application factory

Creating the app in a function makes configuration explicit and tests cleaner (each test can build an app
with different settings):

```python
def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan,
                  openapi_url="/openapi.json" if settings.docs_enabled else None)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                       allow_methods=["*"], allow_headers=["*"])
    app.include_router(api_v1)
    register_exception_handlers(app)
    return app

app = create_app()      # uvicorn app.main:app   (or: uvicorn --factory app.main:create_app)
```

## How routing works: a mini router

To make prefixes, tags and router-level dependencies concrete, here is a small model of
`APIRouter`/`include_router`. Note that inclusion *flattens* everything into one table:

```python-run
class MiniRouter:
    def __init__(self, prefix="", tags=None, dependencies=None):
        self.prefix, self.tags, self.dependencies = prefix, tags or [], dependencies or []
        self.routes = []          # (method, path, handler, tags, dependencies)

    def get(self, path, tags=None, dependencies=None):
        def deco(fn):
            self.routes.append(("GET", self.prefix + path, fn,
                                self.tags + (tags or []),
                                self.dependencies + (dependencies or [])))
            return fn
        return deco

    def include_router(self, router, prefix="", tags=None, dependencies=None):
        for method, path, fn, rtags, rdeps in router.routes:
            self.routes.append((method, self.prefix + prefix + path, fn,
                                self.tags + (tags or []) + rtags,
                                self.dependencies + (dependencies or []) + rdeps))

    def dispatch(self, method, path, ctx):
        for m, p, fn, tags, deps in self.routes:
            if (m, p) == (method, path):
                for dep in deps:               # outermost dependencies first
                    err = dep(ctx)
                    if err:
                        return err
                return 200, fn()
        return 404, "Not Found"

def require_key(ctx):
    return None if ctx.get("key") == "s3cret" else (401, "missing api key")

def require_admin(ctx):
    return None if ctx.get("role") == "admin" else (403, "admins only")

items = MiniRouter(prefix="/items", tags=["items"])
@items.get("/")
def list_items(): return ["hammer", "saw"]

admin = MiniRouter(tags=["admin"])
@admin.get("/stats")
def stats(): return {"users": 3}

v1 = MiniRouter(prefix="/v1", dependencies=[require_key])
v1.include_router(items)
v1.include_router(admin, prefix="/admin", dependencies=[require_admin])

app = MiniRouter()
app.include_router(v1)

for m, p, fn, tags, deps in app.routes:
    print(f"{m} {p:<18} tags={tags} deps={[d.__name__ for d in deps]}")
print(app.dispatch("GET", "/v1/items/", {"key": "s3cret"}))
print(app.dispatch("GET", "/v1/admin/stats", {"key": "s3cret"}))
print(app.dispatch("GET", "/v1/admin/stats", {"key": "s3cret", "role": "admin"}))
print(app.dispatch("GET", "/v1/items/", {}))
```

## Tags, docs and operation IDs at scale

With dozens of routes the docs need organisation:

- Give each router a tag; describe tags via `FastAPI(openapi_tags=[{"name": "items", "description": ...}])`.
  The order of that list is the order in Swagger UI.
- Generated clients use `operationId`s for method names. The default (`read_item_items__item_id__get`) is
  ugly; set a `generate_unique_id_function` on the app that returns e.g. `f"{route.tags[0]}-{route.name}"`.

> [!INTERVIEW]
> "How do you structure a large FastAPI project?" — Split endpoints into `APIRouter`s per resource/feature,
> each with prefix, tags and shared dependencies, and include them in a thin `main.py` (optionally under a
> versioned parent router). Keep routers thin: validation and HTTP concerns only; business logic in a
> service layer; persistence in a data layer; Pydantic schemas separate from ORM models. Shared
> dependencies and settings live in neutral modules to avoid circular imports. Use an app factory and
> lifespan for wiring.

## Worked example: refactoring a single file into routers

Start with the kind of `main.py` every project has at week two:

```python
# main.py - before
app = FastAPI()
engine = create_engine(DATABASE_URL)

def get_session(): ...
def get_current_user(...): ...

@app.post("/token") ...
@app.get("/users/me") ...
@app.get("/users/{user_id}") ...
@app.get("/items") ...
@app.post("/items") ...
@app.get("/items/{item_id}") ...
@app.get("/admin/stats") ...
@app.get("/health") ...
```

The refactoring is mechanical if you do it in this order, running the tests after each step:

**Step 1 — move shared things out first.** Anything two future modules will need goes into neutral
modules, so nothing later has to import `main`:

```python
# app/db.py            -> engine, get_session, SessionDep
# app/security.py      -> hashing, token helpers, get_current_user, CurrentUser
# app/schemas.py       -> Pydantic models
# app/config.py        -> Settings, get_settings
```

**Step 2 — one router per resource.** Replace `@app.` with `@router.`, hoist the common path into the
prefix, and delete it from each route:

```python
# app/routers/items.py - after
router = APIRouter(prefix="/items", tags=["items"])

@router.get("", response_model=list[ItemPublic])
def list_items(session: SessionDep, page: PageDep): ...

@router.post("", response_model=ItemPublic, status_code=201)
def create_item(item: ItemCreate, session: SessionDep, user: CurrentUser): ...

@router.get("/{item_id}", response_model=ItemPublic, responses={404: {"model": ErrorResponse}})
def read_item(item_id: int, session: SessionDep): ...
```

**Step 3 — make protection structural.** Instead of remembering `CurrentUser` on every admin route, put
the requirement on the router so a new route is protected by default:

```python
# app/routers/admin.py
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_role("admin"))])
```

**Step 4 — a thin `main.py` that only wires.**

```python
# app/main.py - after
from app.routers import admin, auth, health, items, users

api = APIRouter(prefix="/api/v1")
for r in (auth.router, users.router, items.router, admin.router):
    api.include_router(r)

app = FastAPI(title="Shop API", lifespan=lifespan)
app.include_router(health.router)          # unversioned, unauthenticated
app.include_router(api)
```

**Step 5 — verify nothing moved.** The public contract must be identical before and after. Snapshot the
route table (or `/openapi.json`) before you start and compare afterwards:

```python
def route_table(app):
    return sorted((m, r.path) for r in app.routes if hasattr(r, "methods") for m in r.methods)
```

A model of that check, showing how prefixes compose and how an accidental change is caught:

```python-run
def flatten(router, prefix=""):
    """Each router: {'prefix': str, 'routes': [(method, path)], 'children': [routers]}"""
    base = prefix + router.get("prefix", "")
    table = [(m, base + p) for m, p in router.get("routes", [])]
    for child in router.get("children", []):
        table += flatten(child, base)
    return sorted(table)

before = sorted([("POST", "/token"), ("GET", "/users/me"), ("GET", "/users/{user_id}"),
                 ("GET", "/items"), ("POST", "/items"), ("GET", "/items/{item_id}"),
                 ("GET", "/admin/stats"), ("GET", "/health")])

after_app = {"children": [
    {"prefix": "", "routes": [("GET", "/health")]},
    {"prefix": "", "routes": [("POST", "/token")]},
    {"prefix": "/users", "routes": [("GET", "/me"), ("GET", "/{user_id}")]},
    {"prefix": "/items", "routes": [("GET", ""), ("POST", ""), ("GET", "/{item_id}")]},
    {"prefix": "/admin", "routes": [("GET", "/stats")]},
]}
print("contract preserved:", flatten(after_app) == before)

# A common slip: writing "/" instead of "" in a prefixed router changes the public path
after_app["children"][3]["routes"][0] = ("GET", "/")
diff = set(flatten(after_app)) ^ set(before)
print("accidental change detected:", sorted(diff))
```

That last case — `/items` silently becoming `/items/` — is the most common regression in this kind of
refactor: clients start getting `307` redirects (and POST clients that don't follow redirects simply
fail).

## Route order still matters inside and across routers

Matching is first-come-first-served over the flattened table, in the order routes were *included*:

- Within a router, declare `/users/me` before `/users/{user_id}`.
- Across routers, a broad route included early can shadow a specific one included later. A catch-all such
  as `@router.get("/{full_path:path}")` (used to serve a single-page app) must be included **last**.
- If two routes have the same method and path, the first wins silently — FastAPI doesn't warn. A unit
  test asserting that `(method, path)` pairs are unique is cheap insurance in a large app.

When a route "isn't being hit", print the table and look for an earlier pattern that matches the same
URL.

## Layer-based versus feature-based layout

Both organisations use exactly the same routers; they differ in what sits next to what.

| | Layer-based (`routers/`, `services/`, `models/`) | Feature-based (`users/`, `orders/`, `billing/`) |
|---|---|---|
| Finding "all the endpoints" | one folder | spread across features |
| Adding a feature | touch 4–5 folders | add one folder |
| Team ownership | by skill | by product area |
| Risk | features entangle through shared modules | duplication, cross-feature imports |
| Fits | small/medium services, one team | larger services, several teams, future extraction into microservices |

A common path is to start layer-based (as the book does with `web/`, `service/`, `data/`, `model/`) and
move to feature packages when the `services/` folder passes a dozen files. Whichever you choose, enforce
the import direction — routers import services, never the reverse; features talk to each other through
their service functions, not by reaching into each other's tables. Tools such as `import-linter` can
check these rules in CI.

## Per-router customisation worth knowing

- `APIRouter(route_class=TimedRoute)` — a custom `APIRoute` subclass that wraps every handler in the
  router (timing, request-body logging, gzip request decoding) without global middleware.
- `APIRouter(default_response_class=ORJSONResponse)` — a faster or different default serialiser for one
  area of the API.
- `APIRouter(include_in_schema=False)` — hide a whole internal router from the docs.
- `APIRouter(lifespan=...)` — a router can carry its own startup/shutdown logic, combined with the app's.
- `callbacks=` and `generate_unique_id_function=` — OpenAPI details for webhook documentation and client
  method naming.

## Pitfalls

- Importing `app` from routers (circular imports).
- Trailing-slash inconsistencies causing 307 redirects.
- Declaring a router's routes *after* `include_router` — they won't be copied (include after defining).
- Putting business logic in routers until they're impossible to test.
- Forgetting that router-level `dependencies` also apply to routes you didn't mean to protect (or missing
  one router when adding auth). Prefer secure-by-default: auth on the parent router, explicit opt-outs.

## Summary

- `APIRouter` groups related routes with shared prefix, tags, dependencies and responses.
- `app.include_router` copies routes into the app; prefixes concatenate, dependencies stack.
- Nest routers for versioning; `mount` sub-apps for full isolation.
- Lay out by layer (book style: web/service/data/model) or by feature; keep `main.py` thin.
- Avoid circular imports with one-directional imports and `request.app`.

```quiz
[
  {"q": "With APIRouter(prefix='/items') included via include_router(router, prefix='/v1'), where is @router.get('/{id}') served?", "options": ["/items/v1/{id}", "/v1/items/{id}", "/{id}", "/v1/{id}"], "answer": 1,
   "explain": "The include prefix comes first, then the router prefix, then the route path."},
  {"q": "What is the runtime cost of nesting routers three levels deep?", "options": ["Three extra lookups per request", "None - routes are copied into a flat table at include time", "One thread per router", "Extra middleware"], "answer": 1,
   "explain": "include_router copies each route with combined settings into the parent."},
  {"q": "How should an endpoint in a router access app-level state without importing main?", "options": ["from app.main import app", "request.app.state", "A global variable in the router", "os.environ"], "answer": 1,
   "explain": "request.app refers to the running application and avoids circular imports."},
  {"q": "Difference between app.mount('/x', sub_app) and include_router?", "options": ["None", "A mounted app is independent (own docs, middleware, overrides); an included router becomes part of the parent app", "mount is faster", "include_router only works for GET"], "answer": 1,
   "explain": "Mounting attaches a separate ASGI application; inclusion merges routes into the same app and OpenAPI schema."},
  {"q": "Dependencies are set on the app, on include_router, and on the route decorator. Which run?", "options": ["Only the route's", "Only the app's", "All of them, outermost first", "The last one declared"], "answer": 2,
   "explain": "Dependencies from every level are combined and all executed."},
  {"q": "Why use an application factory (create_app)?", "options": ["It is required by Uvicorn", "It makes configuration explicit and lets tests build apps with different settings", "It doubles performance", "It removes the need for routers"], "answer": 1,
   "explain": "A factory avoids import-time side effects and improves testability."}
]
```

> **Source:** Lubanovic, *FastAPI*, ch. 8 "Web Layer" (File and Directory Site Layout, The First Website Code, Multiple Routers); https://fastapi.tiangolo.com/tutorial/bigger-applications/, /advanced/sub-applications/, /advanced/generate-clients/
