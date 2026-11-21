# Testing FastAPI apps

> **Before this lesson:** you should know `app.dependency_overrides` and pytest-style `yield`
> fixtures from [lesson 11](#/lesson/fastapi/yield-deps), the layers and fakes of
> [lesson 15](#/lesson/fastapi/layers), and the ASGI call `app(scope, receive, send)` from
> [lesson 3](#/lesson/fastapi/asgi-stack). No testing experience is assumed.

## In plain words

A **test** is a small program that runs your program and checks that the result is what you expect.
You write it once and run it thousands of times. It is how you find out, seconds after making a
change, that the change broke something elsewhere, instead of hearing it from a customer a week
later.

An everyday picture: the checks a pilot performs before every flight. Each item is small, the list
is the same every time, and working through it takes minutes. No pilot skips it on the grounds that
the aircraft flew fine yesterday. A test suite is that checklist for your code, with the advantage
that a machine performs it.

The core statement in a Python test is `assert`. `assert x == 3` does nothing when the condition is
true and stops the test with an error when it is false. The standard tool for finding and running
tests is **pytest**: it collects every function whose name starts with `test_`, runs each one, and
reports which passed.

Lubanovic gives testing a whole chapter and also places "Test!" sections throughout the chapters
that build his site, because web services fail in ways that a quick try on the `/docs` page does not
reveal. FastAPI is unusually pleasant to test: the app is an ordinary object that a test can call
directly, dependencies can be swapped, and Pydantic models give typed test data.

Why this matters for a job: every professional codebase has tests, and writing them is part of every
task. "How do you test an endpoint that needs a database and a logged-in user?" is a standard
interview question, answered step by step below.

## The test pyramid for a layered app

The book defines three kinds of test and maps them onto its layers:

| Kind | Scope | Speed | In the book |
|---|---|---|---|
| **Unit** | one function/layer, neighbours replaced by fakes/mocks | ms | `test/unit/{web,service,data}` |
| **Integration** | several layers together (e.g. service + real DB) | 10s of ms | "Automated Integration Tests" |
| **Full / end-to-end** | the running server over real HTTP | slow | `test/full` with an HTTP client |

The usual advice is a **pyramid**: many fast unit tests at the bottom, fewer integration tests, and
a handful of end-to-end tests at the top. With FastAPI, "API tests" written with `TestClient` sit in
a very productive middle: they exercise routing, validation, dependencies, conversion to JSON and
your own code, all inside one process and in milliseconds.

## TestClient

First, a small application to test:

```python
# app/main.py
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI()
fake_db = {"foo": {"id": "foo", "title": "Foo", "description": "There goes my hero"}}

class Item(BaseModel):
    id: str
    title: str
    description: str | None = None

@app.get("/items/{item_id}", response_model=Item)
async def read_item(item_id: str, x_token: Annotated[str, Header()]):
    if x_token != "coneofsilence":
        raise HTTPException(status_code=400, detail="Invalid X-Token header")
    if item_id not in fake_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return fake_db[item_id]
```

One endpoint: it requires an `X-Token` header, returns 400 when the token is wrong and 404 when the
item does not exist, and otherwise returns the item.

Now the tests:

```python
# tests/test_main.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_item():
    response = client.get("/items/foo", headers={"X-Token": "coneofsilence"})
    assert response.status_code == 200
    assert response.json() == {"id": "foo", "title": "Foo", "description": "There goes my hero"}

def test_read_item_bad_token():
    response = client.get("/items/foo", headers={"X-Token": "hailhydra"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid X-Token header"}

def test_read_nonexistent_item():
    response = client.get("/items/baz", headers={"X-Token": "coneofsilence"})
    assert response.status_code == 404

def test_missing_header_is_422():
    response = client.get("/items/foo")
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["header", "x-token"]
```

- `TestClient(app)` creates a client attached to the app object. No server is started.
- Each `test_...` function sends one request and makes assertions about the response.
- `client.get("/items/foo", headers={...})` returns a response with `.status_code` and `.json()`.
- The first test checks the success case: status 200 and the exact body.
- The second sends a wrong token and expects 400 with the error message.
- The third asks for an item that does not exist and expects 404.
- The fourth sends no header at all. FastAPI's own validation answers 422, and the test checks that
  the error location is `["header", "x-token"]`.

Notice that three of the four tests are about failures. That proportion is normal and healthy.

Key facts:

- `TestClient` is built on **httpx**, a Python HTTP client library, and talks to the ASGI app
  directly: no server and no network port.
- Test functions are plain `def`, and the client calls are not awaited, even though the endpoint is
  `async`. The client runs the app on an event loop behind the scenes.
- Its methods follow `requests` and `httpx`:
  `client.post(url, json=..., data=..., files=..., headers=..., cookies=..., params=...)`.
- Run the tests with the command `pytest` (install with `pip install pytest httpx`).
- By default an exception that the server did not handle is **raised inside your test**, which
  shows you the real error. Pass `TestClient(app, raise_server_exceptions=False)` when you want to
  make assertions about the 500 response instead.

### Lifespan in tests

Start-up and shut-down code (lesson 11) runs only if the client is used in a `with` block:

```python
def test_predict_uses_loaded_model():
    with TestClient(app) as client:          # lifespan startup runs here
        r = client.post("/predict", json={"x": [1.0, 2.0]})
        assert r.status_code == 200
    # lifespan shutdown has run
```

## pytest essentials

Two pytest features carry most of the load.

A **fixture** is a function that prepares something a test needs and cleans up afterwards. A test
asks for a fixture by naming it as a parameter, which is dependency injection for tests. Fixtures
placed in a file named `conftest.py` are available to every test file in that folder.

**Parametrize** runs one test function over a list of cases, which is ideal for validation rules:

```python
import pytest

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.mark.parametrize("payload, bad_field", [
    ({"name": "", "price": 1}, "name"),
    ({"name": "ok", "price": -1}, "price"),
    ({"name": "ok"}, "price"),
])
def test_create_item_validation(client, payload, bad_field):
    r = client.post("/items", json=payload)
    assert r.status_code == 422
    assert any(err["loc"][-1] == bad_field for err in r.json()["detail"])
```

The `client` fixture creates a `TestClient` inside a `with` block and yields it; everything after
the `yield` is clean-up. `@pytest.mark.parametrize` supplies three (payload, bad_field) pairs, so
pytest runs the test three times. Each run posts an invalid body and checks for a 422 whose errors
mention the expected field.

## Replacing dependencies

The place where tests cut the app off from real infrastructure is `app.dependency_overrides`,
introduced in lesson 11:

```python
from app.deps import get_current_user, get_session, get_settings

@pytest.fixture
def client(session):
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_current_user] = lambda: User(id=1, username="tester", roles=["admin"])
    app.dependency_overrides[get_settings] = lambda: Settings(secret_key="test", database_url="sqlite://")
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

This fixture replaces three dependencies: the database session, the current user and the settings.
After the test it clears the overrides so that nothing leaks into the next test.

Test login **both ways**: with the override, to check what the application does for a given user;
and without it, to prove that protected endpoints really answer 401 or 403 when the token is
missing, invalid or lacks a scope.

### Mocks, fakes, stubs

The book distinguishes several kinds of **test double**, the general name for an object that stands
in for a real one during a test:

- A **stub** returns fixed, prepared answers.
- A **fake** is a working but lightweight implementation, such as a repository that keeps its data
  in a dictionary (the book's `fake/` modules).
- A **mock** also records how it was called, so that a test can assert "this method was called once
  with these arguments". Python provides mocks in `unittest.mock`.

Prefer fakes to mocks where you can. A test that asserts "function X was called with Y" breaks
whenever the code is reorganised, even if the behaviour is unchanged. A test that asserts on
*results* does not. And replace only the outer boundaries (a payment service, email, the
machine-learning model, the clock), not the insides of your own code.

```python
from unittest.mock import patch

def test_service_uses_data_layer():
    with patch("service.creature.data.get_one", return_value=Creature(name="yeti", country="CN")):
        assert service.get_one("yeti").country == "CN"
```

`patch(...)` temporarily replaces the function named by the string for the duration of the `with`
block. Here the data layer's `get_one` is replaced by something that returns a fixed creature, and
the test checks that the service passes it through.

The whole idea in a runnable miniature: a service tested against a fake repository, with a mock to
verify an outgoing call.

```python-run
from unittest.mock import Mock

class Missing(Exception): ...

class FakeRepo:                                    # a fake: real behaviour, in memory
    def __init__(self): self.rows = {}
    def get(self, name):
        if name not in self.rows: raise Missing(name)
        return self.rows[name]
    def add(self, name, data): self.rows[name] = data

class CreatureService:
    def __init__(self, repo, notifier): self.repo, self.notifier = repo, notifier
    def register(self, name, country):
        name = name.strip().lower()
        self.repo.add(name, {"name": name, "country": country.upper()})
        self.notifier.send(f"new creature: {name}")
        return self.repo.get(name)

def test_register_normalises_and_notifies():
    notifier = Mock()                              # a mock: records interactions
    svc = CreatureService(FakeRepo(), notifier)
    assert svc.register("  Yeti ", "cn") == {"name": "yeti", "country": "CN"}
    notifier.send.assert_called_once_with("new creature: yeti")

def test_missing_raises():
    svc = CreatureService(FakeRepo(), Mock())
    try:
        svc.repo.get("bigfoot")
        assert False, "expected Missing"
    except Missing:
        pass

for t in (test_register_normalises_and_notifies, test_missing_raises):
    t(); print("PASS", t.__name__)
```

- `FakeRepo` is a fake: it really stores and returns data, in a dictionary.
- `CreatureService.register` tidies the name, stores the creature, sends a notification and returns
  the stored record.
- The first test creates the service with a fake repository and a `Mock()` as the notifier. It
  asserts on the *result* (`{"name": "yeti", "country": "CN"}`), and then on the one interaction that
  matters: `notifier.send.assert_called_once_with("new creature: yeti")`.
- The second test checks that asking for an unknown creature raises `Missing`.

The loop at the bottom plays pytest: it calls each test and prints `PASS` with its name. Both lines
appear. Change `country.upper()` to `country.lower()` in the service and run it again to see what a
failing test looks like.

## Testing with a database

The options, from fastest to most faithful:

1. **A fake repository.** No database at all. Good for unit tests of services.
2. **SQLite in memory.** Quick, but SQLite differs from PostgreSQL in its types, its JSON support
   and its constraints, and those differences can hide bugs.
3. **The real database engine in a container** (a throwaway packaged copy of PostgreSQL started for
   the test run, with a tool such as Testcontainers or docker compose). The most faithful; use it for
   the data layer and for migrations.

The set-up SQLModel recommends for option 2:

```python
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)       # one shared in-memory connection
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
```

`"sqlite://"` with no file name means "in memory". `StaticPool` makes every use share one
connection, which is necessary because an in-memory SQLite database exists only inside its
connection. `create_all` builds the tables, and the fixture yields a session.

With a real database, keep tests from affecting each other by running every test inside a
**transaction that is rolled back** at the end (fast, and no clean-up code; lesson 11 showed the
fixtures), or by emptying the tables between tests. Each test must be independent and able to run in
any order.

## Async tests with httpx.AsyncClient

`TestClient` cannot be used inside an `async def` test. When the test itself has to `await`
something (an async database session, or a check on an asynchronous side effect), use
`httpx.AsyncClient` with `ASGITransport`:

```python
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

@pytest.mark.anyio                       # anyio's pytest plugin (bundled with Starlette's deps)
async def test_root():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Tomato"}
```

`@pytest.mark.anyio` tells pytest to run the coroutine test on an event loop. `ASGITransport(app=app)`
makes the HTTP client call the app directly instead of using the network, and the request itself is
awaited.

Two notes. `AsyncClient` does **not** run lifespan events; wrap the app in `LifespanManager` from the
`asgi-lifespan` package if you need them. And use the same event loop for the app and for async
fixtures, since using two is the classic cause of "attached to a different loop" errors with async
database engines.

## Other things worth testing

- **WebSockets**: `with client.websocket_connect("/ws") as ws: ws.send_text("hi")`, then assert on
  `ws.receive_text()`.
- **Streaming and server-sent events**:
  `with client.stream("GET", "/stream") as r: lines = list(r.iter_lines())`.
- **File uploads**: `client.post("/upload", files={"file": ("a.txt", b"hello", "text/plain")})`.
- **The OpenAPI contract**: save a copy of `client.get("/openapi.json").json()` and compare against
  it, to catch accidental breaking changes. **Schemathesis** generates tests from the schema.
- **Security**: the book lists security testing as a category of its own. Test authorization for
  every role, and test that sensitive fields never appear in responses.
- **Load**: the book mentions Locust for load testing; k6 and `hey` are alternatives. A load test
  sends many requests at once and measures how the service copes. Record the response time that
  50%, 95% and 99% of requests stay under (written p50, p95, p99) and the error rate at your target
  number of requests per second, *before* production does it for you.

## What makes a good API test

- Three steps, **Arrange, Act, Assert**: set up the situation, perform one action, check the
  outcome. One behaviour per test, and a name that states it
  (`test_create_duplicate_returns_409`).
- Assert on the status code **and** on the shape of the body. For errors, assert on the
  machine-readable parts (`type`, `loc`), not on the wording of messages.
- Cover the unhappy paths: validation failures, 401 and 403, 404, 409, timeouts of outside services.
- No sleeping, no network, no state shared between tests, and no dependence on the real time or on
  random numbers (pass the clock in; fix the random seed). A test that sometimes passes and
  sometimes fails without any change to the code is called **flaky**, and these are its usual
  causes.
- **Coverage** (the percentage of code lines that the tests execute) is a torch for finding untested
  corners, not a goal. One hundred percent coverage with weak assertions proves little.

> [!INTERVIEW]
> "How do you test a FastAPI endpoint that needs a database and an authenticated user?" — Use
> `TestClient(app)` in a pytest fixture; override `get_session` with a session bound to a test
> database (in-memory SQLite with `StaticPool`, or a PostgreSQL container with a transaction rolled
> back after each test) and override `get_current_user` to return a known user. Assert on status
> codes and JSON. Add separate tests without the login override to verify the 401 and 403 behaviour,
> clear the overrides after each test, and use the client in a `with` block if lifespan resources are
> needed.

## How TestClient works: a miniature you can run

`TestClient` looks like magic until you recall from lesson 3 that an ASGI app is a coroutine taking
`scope`, `receive` and `send`. A test client builds a scope from your call, supplies the body
through `receive`, collects what the app passes to `send`, and hands you a response object. Here is
one in thirty lines, used to test a tiny app that has a dependency override. It is the whole testing
story with no network and no framework:

```python-run
import json

# ---------------- a tiny ASGI "framework" with overridable dependencies ----------------
def get_db():
    raise RuntimeError("real database is not available in tests!")

class App:
    def __init__(self):
        self.dependency_overrides = {}
    def resolve(self, dep):
        return self.dependency_overrides.get(dep, dep)()

    async def __call__(self, scope, receive, send):
        body = (await receive())["body"]
        status, payload = 404, {"detail": "Not Found"}
        if (scope["method"], scope["path"]) == ("POST", "/items"):
            data = json.loads(body or b"{}")
            if not isinstance(data.get("name"), str) or not data["name"]:
                status, payload = 422, {"detail": [{"loc": ["body", "name"], "type": "missing"}]}
            else:
                db = self.resolve(get_db)
                db.append(data["name"])
                status, payload = 201, {"id": len(db), "name": data["name"]}
        elif (scope["method"], scope["path"]) == ("GET", "/items"):
            status, payload = 200, {"items": list(self.resolve(get_db))}
        raw = json.dumps(payload).encode()
        await send({"type": "http.response.start", "status": status,
                    "headers": [(b"content-type", b"application/json")]})
        await send({"type": "http.response.body", "body": raw})

app = App()

# ---------------- the test client ----------------
class Response:
    def __init__(self, status_code, body): self.status_code, self._body = status_code, body
    def json(self): return json.loads(self._body)

class MiniTestClient:
    def __init__(self, app): self.app = app
    async def request(self, method, path, json_body=None):
        sent = []
        async def receive():
            return {"type": "http.request", "body": json.dumps(json_body).encode() if json_body else b""}
        async def send(message):
            sent.append(message)
        scope = {"type": "http", "method": method, "path": path, "headers": []}
        await self.app(scope, receive, send)                 # call the app directly: no server, no socket
        return Response(sent[0]["status"], sent[1]["body"])
    async def get(self, path): return await self.request("GET", path)
    async def post(self, path, json=None): return await self.request("POST", path, json)

# ---------------- tests ----------------
def make_client():
    fake_db = []
    app.dependency_overrides[get_db] = lambda: fake_db        # swap the dependency
    return MiniTestClient(app), fake_db

async def test_create_and_list():
    client, db = make_client()
    r = await client.post("/items", json={"name": "hammer"})
    assert r.status_code == 201 and r.json() == {"id": 1, "name": "hammer"}
    assert (await client.get("/items")).json() == {"items": ["hammer"]}
    assert db == ["hammer"]                                   # the test can inspect the fake directly

async def test_validation_error():
    client, _ = make_client()
    r = await client.post("/items", json={"nome": "typo"})
    assert r.status_code == 422 and r.json()["detail"][0]["loc"] == ["body", "name"]

async def test_unknown_route():
    client, _ = make_client()
    assert (await client.get("/nope")).status_code == 404

async def test_tests_are_isolated():
    client, _ = make_client()
    assert (await client.get("/items")).json() == {"items": []}   # nothing leaked from earlier tests

async def test_without_override_hits_real_dependency():
    app.dependency_overrides.clear()
    try:
        await MiniTestClient(app).get("/items")
        assert False, "expected the real dependency to fail"
    except RuntimeError as e:
        assert "not available" in str(e)

for test in (test_create_and_list, test_validation_error, test_unknown_route, test_tests_are_isolated,
             test_without_override_hits_real_dependency):
    await test()
    print("PASS", test.__name__)
app.dependency_overrides.clear()
```

The code has three sections.

**The app.** `get_db` is the "real" dependency, and it raises an error, as a real database would
when none is available. `App.resolve` looks a dependency up in `dependency_overrides` before calling
it (the mechanism of lesson 11). `__call__` is a small ASGI app with two routes, `POST /items` and
`GET /items`, including a 422 for a missing name.

**The client.** `MiniTestClient.request` builds the `scope`, defines `receive` (which hands over the
body) and `send` (which collects the messages), calls the app directly, and wraps the collected
status and body in a `Response`.

**The tests.** `make_client` installs a brand-new list as the fake database for each test. The five
tests check: create then list; a validation error for a misspelled field name; a 404 for an unknown
route; that nothing leaks between tests (the list is empty again); and that without the override the
real dependency fails.

The output is five `PASS` lines. Everything the real tools do is here in outline. The client turns
a call into ASGI messages and collects the reply. A fresh fake for each test keeps tests independent.
The override replaces a dependency that would otherwise need infrastructure. This miniature is the
*async* variety: it awaits the app directly, like `httpx.AsyncClient` with `ASGITransport`. The real
`TestClient` adds a synchronous front: it runs the app on an event loop in a background thread and
waits until the response is complete, which is why ordinary tests are plain `def` functions with no
`await`.

## A full test module, annotated

This module uses the fixtures `session`, `user`, `client` and `anonymous_client` defined in lesson
11. Tests are grouped into classes whose names begin with `Test`, which pytest also collects.

```python
# tests/test_orders.py
import pytest

@pytest.fixture
def order(session, user):                              # arrange shared state through the same session
    order = Order(owner_id=user.id, total=19.9, status="open")
    session.add(order); session.commit(); session.refresh(order)
    return order

class TestReadOrder:
    def test_owner_can_read(self, client, order):
        r = client.get(f"/orders/{order.id}")
        assert r.status_code == 200
        assert r.json() == {"id": order.id, "total": 19.9, "status": "open"}      # exact public shape

    def test_internal_fields_are_not_exposed(self, client, order):
        assert "owner_id" not in client.get(f"/orders/{order.id}").json()

    def test_other_users_order_is_404(self, client, session):
        other = Order(owner_id=999, total=5, status="open")
        session.add(other); session.commit()
        assert client.get(f"/orders/{other.id}").status_code == 404           # object-level authorization

    def test_requires_authentication(self, anonymous_client, order):
        r = anonymous_client.get(f"/orders/{order.id}")
        assert r.status_code == 401
        assert r.headers["www-authenticate"] == "Bearer"

class TestCancelOrder:
    def test_cancel_open_order(self, client, order, session):
        r = client.post(f"/orders/{order.id}/cancellations")
        assert r.status_code == 201
        session.refresh(order)
        assert order.status == "cancelled"                                     # assert on stored state too

    def test_cancel_twice_conflicts(self, client, order):
        client.post(f"/orders/{order.id}/cancellations")
        assert client.post(f"/orders/{order.id}/cancellations").status_code == 409

    def test_notification_sent(self, client, order, monkeypatch):
        sent = []
        monkeypatch.setattr("app.services.orders.send_email", lambda to, subject: sent.append((to, subject)))
        client.post(f"/orders/{order.id}/cancellations")
        assert sent == [("tester@example.com", "Your order was cancelled")]
```

What this module gets right:

- All four outcomes of a protected read are covered: success, not logged in, somebody else's object,
  and internal fields staying hidden.
- Changes are asserted twice, through the API *and* in the database (`session.refresh(order)`
  re-reads the row).
- The behaviour of a repeated request is fixed: cancelling twice gives 409.
- The only thing replaced is an outside boundary, the email sender.

One detail deserves attention. `monkeypatch.setattr` must target the name **where it is looked up**
(`app.services.orders.send_email`), not where the function is defined. Getting this wrong is the
most common reason a patch "does not work".

## Controlling time and randomness

A test that depends on `datetime.now()`, `uuid4()` or `random` is flaky by construction. Make such
things something that can be passed in. Dependencies are the natural place:

```python
def get_clock() -> Callable[[], datetime]:
    return lambda: datetime.now(UTC)

ClockDep = Annotated[Callable[[], datetime], Depends(get_clock)]

@router.post("/coupons/{code}/redeem")
def redeem(code: str, now: ClockDep, session: SessionDep): ...

# test
app.dependency_overrides[get_clock] = lambda: (lambda: datetime(2025, 6, 1, tzinfo=UTC))
```

`get_clock` returns a function that gives the current time. The endpoint receives it as `now` and
calls `now()` whenever it needs the time. The test overrides `get_clock` with a clock that always
answers 1 June 2025.

Token expiry, rate-limit windows, cache lifetimes and "valid until" rules can then all be tested at
their exact boundaries (one second before, exactly at, one second after) with no `sleep`.

## Debugging failing tests

| Symptom | Likely cause |
|---|---|
| Passes alone, fails in the suite | state leaking between tests: uncleared overrides, shared in-memory dicts, module-level caches (`lru_cache` on settings) |
| `404` in a test for a route that exists | the test imports a different app instance, or the router isn't included in the app under test |
| `401` everywhere after adding auth | the override key isn't the function the routes actually use |
| "attached to a different loop" | async engine/client created on one event loop and used on another; create them inside the async fixture |
| Lifespan resources missing | client not used as a context manager |
| Test hangs | an awaited call without timeout, or a streaming response never closed |
| Works locally, fails in CI | reliance on test order, wall-clock time, local files or an already-populated database |

To run a single test with full detail and stop inside the debugger at the first failure:
`pytest tests/test_orders.py::TestCancelOrder::test_cancel_twice_conflicts -vv -x --pdb`.

## Pitfalls

- Forgetting `with TestClient(app)` and then wondering why the model or the connection pool is
  `None`.
- Overrides leaking from one test into the next.
- Testing against SQLite only while deploying on PostgreSQL.
- `async def` tests that use the synchronous `TestClient`.
- Over-mocking: the tests pass while the real integration is broken.
- Asserting on the exact wording of error messages.

## Summary

- Unit-test layers with fakes; test the API through `TestClient`; keep a few end-to-end and load
  tests.
- `TestClient` runs the ASGI app inside the test process; use it in a `with` block for lifespan.
- `app.dependency_overrides` swaps database sessions, users and settings.
- Async tests: `httpx.AsyncClient(transport=ASGITransport(app=app))` with `pytest.mark.anyio`.
- Test the unhappy paths, the login rules and the OpenAPI contract.

## Glossary

- **Test** — a small program that runs your code and checks the result.
- **`assert`** — a statement that fails the test when its condition is false.
- **pytest** — the standard Python tool that finds and runs tests.
- **Unit / integration / end-to-end test** — one piece alone / several pieces together / the whole
  running system.
- **Test pyramid** — many unit tests, fewer integration tests, few end-to-end tests.
- **`TestClient`** — FastAPI's client that calls the app directly, without a network.
- **Fixture** — a function that prepares something for a test and cleans up afterwards.
- **Parametrize** — run one test function over a list of cases.
- **Test double** — any stand-in for a real object in a test.
- **Stub / fake / mock** — fixed answers / a lightweight working implementation / a stand-in that
  records its calls.
- **Patch (monkeypatch)** — temporarily replacing a function or attribute during a test.
- **Arrange, Act, Assert** — the three steps of a well-shaped test.
- **Flaky test** — a test whose result changes without any change to the code.
- **Coverage** — the share of code lines executed by the tests.
- **Load test** — sending many simultaneous requests to measure behaviour under pressure.

```quiz
[
  {"q": "How does TestClient talk to your app?", "options": ["Over a real TCP port", "It calls the ASGI app in-process via httpx", "Through Uvicorn in a subprocess", "Via WebSockets only"], "answer": 1,
   "explain": "No server or network is involved; requests are translated directly into ASGI calls."},
  {"q": "Your lifespan loads a model, but in tests app.state.model is missing. Why?", "options": ["pytest disables lifespan", "The TestClient wasn't used as a context manager, so startup never ran", "Models can't load in tests", "dependency_overrides cleared it"], "answer": 1,
   "explain": "Lifespan startup/shutdown run on entering/exiting 'with TestClient(app) as client'."},
  {"q": "Which tool lets you replace get_session with a test session without patching?", "options": ["unittest.mock.patch", "app.dependency_overrides", "pytest.mark.skip", "TestClient(base_url=...)"], "answer": 1,
   "explain": "FastAPI looks up overrides for each dependency callable at request time."},
  {"q": "What is the difference between a fake and a mock?", "options": ["None", "A fake is a working lightweight implementation; a mock records calls for interaction assertions", "A mock uses a real database", "A fake only works with pytest"], "answer": 1,
   "explain": "Fakes support behaviour-based tests; mocks verify interactions and are best kept to external boundaries."},
  {"q": "When do you need httpx.AsyncClient instead of TestClient?", "options": ["Always for async endpoints", "When the test function itself is async and must await other things", "Only for WebSockets", "Never"], "answer": 1,
   "explain": "Sync TestClient works fine for async endpoints; async tests need an async client on the same event loop."},
  {"q": "Why can relying only on in-memory SQLite tests be risky?", "options": ["SQLite is slower", "Dialect and behaviour differences from the production database can hide bugs", "SQLite can't create tables", "FastAPI doesn't support it"], "answer": 1,
   "explain": "Types, constraints, JSON operators and locking differ; run data-layer tests against the real engine too."},
  {"q": "For a 422 response, what should a robust test assert on?", "options": ["The exact human-readable msg string", "Status code plus machine-readable fields like loc and type", "Response time", "Header order"], "answer": 1,
   "explain": "Messages change between library versions; loc/type are the stable contract."}
]
```

> **Source:** Lubanovic, *FastAPI*, ch. 12 "Testing" (Web API Testing, Where to Test, What to Test, Pytest, Mocking, Test Doubles and Fakes, Automated Integration Tests, The Repository Pattern, Automated Full Tests, Security Testing, Load Testing); https://fastapi.tiangolo.com/tutorial/testing/, /advanced/async-tests/, /advanced/testing-dependencies/, /advanced/testing-events/
