# APIRouter and bigger applications

> **Before this lesson:** you should be able to write endpoints with `@app.get` and friends
> ([lesson 4](#/lesson/fastapi/first-app)), attach dependencies at different levels
> ([lesson 10](#/lesson/fastapi/depends-basics)) and know what tags do in the docs
> ([lesson 6](#/lesson/fastapi/openapi-docs)). In Python you need `import` between your own files.

## In plain words

Every example so far has lived in one file. That is ideal for learning and miserable for a real
project. A service with eighty endpoints in a single `main.py` is hard to read, and five people
editing the same file get in each other's way all day.

The cure is the same as for any long piece of writing: chapters. FastAPI's chapter is the
**`APIRouter`**. A router is a group of related endpoints (everything about users, say) that lives
in its own file and is later plugged into the main application. The group can share a common start
of the address (`/users`), a common heading in the documentation, and common requirements such as
"must be logged in".

An everyday picture: a department store. The building has one entrance and one address, but inside
it is divided into departments, each with its own sign, its own staff and its own rules (the
jewellery counter checks more carefully than the sock aisle). The store directory at the entrance
lists every department. The `FastAPI` app is the building, each `APIRouter` is a department, and the
route table is the directory.

Why this matters for a job: any codebase you join will be organised this way, and "how do you
structure a large FastAPI project?" is a standard interview question whose answer starts with
routers.

Two Python words are used throughout. A **module** is one `.py` file. A **package** is a folder of
modules (traditionally marked by a file named `__init__.py`). `from app.routers import items` means
"from the package `app.routers`, load the module `items.py`".

## From one file to routers

Lubanovic introduces routers in his web-layer chapter under "Multiple Routers": a router behaves
like a small `FastAPI` app that the top-level app plugs in. Here is one router in its own file:

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

- `router = APIRouter(...)` creates the group. `prefix="/items"` is placed in front of every path
  declared on it. `tags=["items"]` puts all of its endpoints under one heading in `/docs`.
  `responses={404: ...}` documents a 404 outcome for all of them.
- `@router.get("/")` works exactly like `@app.get`, but registers the endpoint on the router. With
  the prefix, this endpoint answers at `/items/`.
- `@router.get("/{item_id}")` answers at `/items/{item_id}`, and the `post` at `/items/`.

The main file then plugs the routers in:

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

- `from app.routers import items, users, admin` loads three router modules.
- `app.include_router(users.router)` adds every route of that router to the app.
- The third `include_router` call adds settings at the moment of inclusion: an extra prefix, an extra
  tag, and a dependency that will run before every route of the admin router.
- A small `/health` endpoint is declared directly on the app, hidden from the docs.

A router supports the same decorators as the app (`@router.get`, `.post`, `@router.websocket` and so
on). `include_router` *copies* the router's routes into the app and combines the settings from each
level:

| Setting | Where it can be set | How they combine |
|---|---|---|
| `prefix` | `APIRouter(...)`, `include_router(...)` | concatenated: include prefix + router prefix + route path |
| `tags` | router, include, route | merged |
| `dependencies` | app, include, router, route decorator | all run: app → include → router → route → parameters |
| `responses` | router, include, route | merged |
| `deprecated`, `include_in_schema` | include, router, route | inherited |

Because routes are copied when `include_router` is called, nesting costs **nothing while the server
is running**. The finished app holds one flat list of routes, however many levels of routers
produced it.

> [!TIP]
> A prefix must not end with `/`. With `prefix="/items"`, `@router.get("/")` answers at `/items/`
> and `@router.get("")` answers at `/items`. Pick one convention. By default Starlette redirects from
> one form to the other (`redirect_slashes=True`), which costs clients an extra round trip.

## Nesting and versioning

A router can include other routers. That gives a clean way to put a version number in front of a
whole API (lesson 2):

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

`api_v1` is an empty router with the prefix `/v1`. Three resource routers are included into it, and
it in turn is included into the app. The users router's `/users` routes are now served under
`/v1/users`. A second parent router, `api_v2`, can sit beside it with different contents.

The *same* router can even be included twice with different prefixes, for example at `/v1/items` and
at an old `/items` address marked `deprecated=True`. Its routes then appear twice in the table and in
the docs.

For complete separation (separate documentation, separate middleware) you can **mount** an entire
second application: `app.mount("/internal", internal_app)`. A mounted app is independent, with its
own OpenAPI document and its own dependency overrides, whereas an included router becomes part of
the parent app.

## A project layout that scales

The official "Bigger Applications" tutorial suggests a folder structure like this:

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

Each name has one job: `main.py` assembles the app; `config.py` holds the settings class of lesson
9; `dependencies.py` holds shared dependencies; `routers/` holds one module per resource; `schemas/`
holds the Pydantic models for requests and responses; `models/` holds the classes that describe
database tables; `services/` holds the application's own rules; `db.py` sets up the database
connection.

Lubanovic's book uses an equivalent structure with other folder names, organised by **layer** (the
subject of the next lesson): `src/web/` for routers, `src/service/`, `src/data/`, `src/model/`,
`src/fake/` and `src/test/`. His `main.py` does little more than create the app and include one
router per resource:

```python
# main.py in the book's style
from fastapi import FastAPI
from web import explorer, creature

app = FastAPI()
app.include_router(explorer.router)
app.include_router(creature.router)
```

Larger codebases often prefer a **feature-based** layout (also called domain-based): one package per
feature, each holding its own router, schemas, service and models:

```text
app/
├── users/      (router.py, schemas.py, service.py, models.py)
├── orders/     (router.py, schemas.py, service.py, models.py)
└── core/       (config.py, db.py, security.py)
```

A layer-based layout keeps code of the same kind together and suits small and medium applications.
A feature-based layout keeps everything about one feature together and suits projects with several
teams. `APIRouter` works identically in both; a comparison table follows later in the lesson.

## Avoiding circular imports

A **circular import** happens when file A imports file B while B imports A. Python cannot finish
loading either, and the program fails at start-up. The classic way to cause one: `routers/items.py`
contains `from app.main import app`, while `main.py` imports `routers.items`. Three rules prevent it:

- Routers never import `main`. `main` imports routers. Imports flow in one direction only.
- Things that several files need (`get_session`, `Settings`, security helpers) live in neutral
  modules (`dependencies.py`, `config.py`) that both sides may import.
- If an endpoint needs the app object, it uses `request.app` (for example
  `request.app.state.model`) and imports nothing.

## An application factory

A **factory** is a function whose job is to build and return an object. Creating the app inside a
function makes its configuration explicit and makes tests cleaner, since each test can build an app
with different settings:

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

`create_app` takes optional settings, creates the `FastAPI` object, adds middleware, includes the
routers, registers error handlers and returns the finished app. The last line builds the app that
Uvicorn runs. Uvicorn can also call the factory itself: `uvicorn --factory app.main:create_app`.

## How routing works: a mini router

To make prefixes, tags and router-level dependencies concrete, here is a small model of `APIRouter`
and `include_router`. Watch how inclusion *flattens* everything into one table:

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

Reading the model:

- A `MiniRouter` stores its own prefix, tags and dependencies, plus a list of routes. Each route is
  a tuple of method, full path, handler function, tags and dependencies.
- `get(path)` is the decorator. It stores the route with the router's prefix already joined to the
  path, and the router's tags and dependencies already attached.
- `include_router` copies every route of the child into the parent, adding the parent's prefix in
  front and the parent's tags and dependencies ahead of the child's.
- `dispatch` searches the flat list for a match on method and path, runs the dependencies in order
  (stopping at the first that reports an error), and calls the handler.
- Below that, an `items` router and an `admin` router are included into a `v1` router that requires
  an API key, and `v1` is included into the app.

The first two printed lines are the flattened table: `GET /v1/items/` with the dependency
`require_key`, and `GET /v1/admin/stats` with `require_key` followed by `require_admin`. The four
requests then give `(200, ['hammer', 'saw'])` with a valid key; `(403, 'admins only')` for the stats
route with a key but no admin role; `(200, {'users': 3})` with both; and
`(401, 'missing api key')` with no key. The outermost dependency ran first each time.

## Tags, docs and operation IDs at scale

With dozens of routes, the documentation page needs organising:

- Give each router a tag, and describe the tags with
  `FastAPI(openapi_tags=[{"name": "items", "description": ...}])`. The order of that list is the
  order of the sections in Swagger UI.
- Client code generated from the schema names its functions after each route's `operationId`. The
  default (`read_item_items__item_id__get`) is ugly. Set a `generate_unique_id_function` on the app
  that returns something like `f"{route.tags[0]}-{route.name}"`.

> [!INTERVIEW]
> "How do you structure a large FastAPI project?" — Split endpoints into `APIRouter`s, one per
> resource or feature, each with a prefix, tags and shared dependencies, and include them in a thin
> `main.py` (optionally under a versioned parent router). Keep routers thin: validation and HTTP
> matters only; the application's rules go in a service layer; storage in a data layer; Pydantic
> schemas are kept apart from database models. Shared dependencies and settings live in neutral
> modules to avoid circular imports. Use an app factory and the lifespan to wire things together.

## Worked example: refactoring a single file into routers

**Refactoring** means changing how code is organised without changing what it does. Start with the
kind of `main.py` that every project has in its second week:

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

The work is mechanical if you do it in this order, running the tests after each step.

**Step 1: move shared things out first.** Whatever two of the future modules will both need goes
into neutral modules, so that nothing later has to import `main`:

```python
# app/db.py            -> engine, get_session, SessionDep
# app/security.py      -> hashing, token helpers, get_current_user, CurrentUser
# app/schemas.py       -> Pydantic models
# app/config.py        -> Settings, get_settings
```

**Step 2: one router per resource.** Replace `@app.` with `@router.`, lift the common start of the
path into the prefix, and delete it from each route:

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

**Step 3: make protection part of the structure.** Instead of remembering to add `CurrentUser` to
every admin route, put the requirement on the router, so that a route added next month is protected
without anyone thinking about it:

```python
# app/routers/admin.py
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_role("admin"))])
```

**Step 4: a thin `main.py` that only assembles.**

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

A parent router `api` with the prefix `/api/v1` collects the four resource routers in a loop. The
health router is included directly on the app, outside the version prefix and outside any login
requirement.

**Step 5: check that nothing moved.** The public contract must be identical before and after. Record
the route table (or `/openapi.json`) before you start, and compare afterwards:

```python
def route_table(app):
    return sorted((m, r.path) for r in app.routes if hasattr(r, "methods") for m in r.methods)
```

This helper lists every (method, path) pair the app serves, sorted. Here is a model of the check,
showing how prefixes combine and how an accidental change is caught:

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

`flatten` walks a nested description of routers and returns the sorted list of (method, path)
pairs, joining prefixes as it goes. `before` is the list from the original single file, and
`after_app` describes the refactored layout. The first print says `contract preserved: True`: the
two lists are equal. Then one route path is changed from `""` to `"/"`, and the second print shows
the difference: `('GET', '/items')` has disappeared and `('GET', '/items/')` has appeared.

That case, `/items` quietly becoming `/items/`, is the most common mistake in this kind of
refactoring. Clients start receiving `307` redirects, and clients that do not follow redirects for
POST requests fail outright.

## Route order still matters inside and across routers

Matching goes through the flattened table from the top and takes the first fit, in the order in
which routes were *included*:

- Within a router, declare `/users/me` before `/users/{user_id}` (lesson 4).
- Across routers, a broad route included early can hide a specific one included later. A catch-all
  such as `@router.get("/{full_path:path}")`, used to serve a single-page web app, must be included
  **last**.
- If two routes have the same method and path, the first wins and FastAPI gives no warning. In a
  large app, a unit test asserting that the (method, path) pairs are unique is cheap insurance.

When a route "is not being hit", print the table and look for an earlier pattern that fits the same
address.

## Layer-based versus feature-based layout

Both organisations use exactly the same routers. They differ in what sits next to what.

| | Layer-based (`routers/`, `services/`, `models/`) | Feature-based (`users/`, `orders/`, `billing/`) |
|---|---|---|
| Finding "all the endpoints" | one folder | spread across features |
| Adding a feature | touch 4–5 folders | add one folder |
| Team ownership | by skill | by product area |
| Risk | features entangle through shared modules | duplication, cross-feature imports |
| Fits | small/medium services, one team | larger services, several teams, future extraction into microservices |

A common path is to begin layer-based (as the book does with `web/`, `service/`, `data/`, `model/`)
and to move to feature packages when the `services/` folder has grown past a dozen files. Whichever
you choose, enforce the direction of imports: routers import services and never the reverse, and
features talk to each other through their service functions instead of reaching into each other's
tables. A tool such as `import-linter` can check these rules automatically on every change, as part
of **CI** (continuous integration: the automated checks run whenever code is submitted).

## Per-router customisation worth knowing

- `APIRouter(route_class=TimedRoute)`: a custom `APIRoute` subclass that wraps every handler in the
  router (timing, logging request bodies) without middleware for the whole app.
- `APIRouter(default_response_class=ORJSONResponse)`: a faster or different default JSON encoder for
  one area of the API.
- `APIRouter(include_in_schema=False)`: hide an entire internal router from the docs.
- `APIRouter(lifespan=...)`: a router can carry start-up and shut-down code of its own, which is
  combined with the app's.
- `callbacks=` and `generate_unique_id_function=`: OpenAPI details for documenting webhooks and for
  naming generated client functions.

## Pitfalls

- Importing `app` from routers (circular imports).
- Inconsistent trailing slashes, causing 307 redirects.
- Declaring routes on a router *after* it has been included. They are not copied; include a router
  only once all its routes are defined.
- Putting the application's rules in routers until they can no longer be tested.
- Forgetting that router-level `dependencies` also apply to routes you did not mean to protect, or
  missing one router when adding login checks. Prefer secure-by-default: the login requirement on the
  parent router, with explicit exceptions.

## Summary

- `APIRouter` groups related routes with a shared prefix, tags, dependencies and responses.
- `app.include_router` copies routes into the app; prefixes are joined and dependencies stack.
- Nest routers for versioning; `mount` sub-applications for complete separation.
- Lay the project out by layer (the book's style: web / service / data / model) or by feature; keep
  `main.py` thin.
- Avoid circular imports with one-directional imports and `request.app`.

## Glossary

- **Module / package** — one `.py` file / a folder of modules.
- **`APIRouter`** — a group of related routes that is later plugged into the app.
- **Prefix** — a path fragment placed in front of every route of a router.
- **`include_router`** — copies a router's routes into an app or another router.
- **Route table** — the app's flat, ordered list of all (method, path, handler) entries.
- **Mount** — attach a complete, independent application under a path.
- **Layout** — how a project's files and folders are organised.
- **Layer-based / feature-based** — folders by kind of code / folders by product feature.
- **Circular import** — two modules importing each other, which fails at start-up.
- **Application factory** — a function that builds and returns the app.
- **Refactoring** — reorganising code without changing what it does.
- **Operation ID** — the machine name of an endpoint in the OpenAPI document.
- **CI (continuous integration)** — automated checks run on every code change.

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
