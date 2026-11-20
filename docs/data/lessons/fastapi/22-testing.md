# Testing FastAPI apps

Lubanovic devotes a full chapter to testing and salts "Test!" sections through the chapters that build
his site, because web services fail in ways a quick manual poke at `/docs` won't reveal. FastAPI makes
testing unusually pleasant: the app is a plain object you can call in-process, dependencies are
swappable, and Pydantic models give you typed fixtures. This lesson covers the test pyramid, `TestClient`,
dependency overrides, database strategies, async tests with `httpx.AsyncClient`, and what to test.

## The test pyramid for a layered app

The book defines three kinds, mapped onto its layers:

| Kind | Scope | Speed | In the book |
|---|---|---|---|
| **Unit** | one function/layer, neighbours replaced by fakes/mocks | ms | `test/unit/{web,service,data}` |
| **Integration** | several layers together (e.g. service + real DB) | 10s of ms | "Automated Integration Tests" |
| **Full / end-to-end** | the running server over real HTTP | slow | `test/full` with an HTTP client |

Many fast unit tests at the base, fewer integration tests, a handful of end-to-end checks. With FastAPI,
"API tests" via `TestClient` sit in the sweet spot: they exercise routing, validation, dependencies,
serialisation and your code — in-process, in milliseconds.

## TestClient

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

Key facts:

- `TestClient` is built on **httpx** and speaks to the ASGI app directly — no server, no network port.
- Test functions are plain `def` (not `async def`) and the client calls are not awaited, even though the
  endpoints are async; the client runs the app in an event loop behind the scenes.
- The API mirrors `requests`/`httpx`: `client.post(url, json=..., data=..., files=..., headers=...,
  cookies=..., params=...)`.
- Run with `pytest` (`pip install pytest httpx`).
- By default, unhandled server exceptions are **re-raised in your test** (helpful). Pass
  `TestClient(app, raise_server_exceptions=False)` to assert on the 500 response instead.

### Lifespan in tests

Startup/shutdown code only runs if you use the client as a context manager:

```python
def test_predict_uses_loaded_model():
    with TestClient(app) as client:          # lifespan startup runs here
        r = client.post("/predict", json={"x": [1.0, 2.0]})
        assert r.status_code == 200
    # lifespan shutdown has run
```

## pytest essentials

**Fixtures** provide setup/teardown and dependency injection for tests; `conftest.py` shares them.
**Parametrize** runs one test over many cases — ideal for validation rules:

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

## Replacing dependencies

The seam for isolation is `app.dependency_overrides` (see the dependencies module):

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

Test auth **both ways**: with the override (to test business behaviour as a given user) and without it (to
prove protected endpoints return 401/403 with missing/invalid/under-scoped tokens).

### Mocks, fakes, stubs

The book distinguishes *test doubles*:

- A **stub** returns canned answers. A **fake** is a working lightweight implementation (in-memory
  repository; the book's `fake/` modules). A **mock** additionally records calls so you can assert on
  interactions (`unittest.mock`).
- Prefer fakes over mocks where practical: tests that assert "function X was called with Y" break on
  every refactor; tests that assert on *behaviour* don't.
- Patch external boundaries only (payment API, email, the ML model, the clock), not your own internals.

```python
from unittest.mock import patch

def test_service_uses_data_layer():
    with patch("service.creature.data.get_one", return_value=Creature(name="yeti", country="CN")):
        assert service.get_one("yeti").country == "CN"
```

The whole idea in runnable miniature — a service tested against a fake repository, plus a mock to verify
an outbound call:

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

## Testing with a database

Options, from fastest to most faithful:

1. **Fake repository** — no DB at all (unit tests of services).
2. **SQLite in memory** — quick, but dialect differences from PostgreSQL (types, JSON, constraints) can
   hide bugs.
3. **The real engine in a container** (Testcontainers, docker compose in CI) — highest fidelity; use for
   the data layer and migrations.

The SQLModel-recommended setup for option 2:

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

For a real database, isolate tests by running each inside a **transaction that is rolled back** at the end
(fast, no cleanup) or by truncating tables between tests. Each test must be independent and runnable in
any order.

## Async tests with httpx.AsyncClient

`TestClient` can't be used inside `async def` tests. When the test itself must `await` things — an async
DB session, verifying async side effects — use `httpx.AsyncClient` with `ASGITransport`:

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

Notes: `AsyncClient` does **not** trigger lifespan events — wrap the app with `asgi-lifespan`'s
`LifespanManager` if you need them. Use the same event loop for app and async fixtures (a classic source
of "attached to a different loop" errors with async DB engines).

## Other things worth testing

- **WebSockets**: `with client.websocket_connect("/ws") as ws: ws.send_text("hi"); assert
  ws.receive_text() == ...`.
- **Streaming/SSE**: `with client.stream("GET", "/stream") as r: lines = list(r.iter_lines())`.
- **File uploads**: `client.post("/upload", files={"file": ("a.txt", b"hello", "text/plain")})`.
- **OpenAPI contract**: snapshot `client.get("/openapi.json").json()` to catch accidental breaking changes;
  **Schemathesis** generates property-based tests from the schema.
- **Security**: the book lists security testing as its own category — test authorization for every role,
  and that sensitive fields never appear in responses.
- **Load**: the book mentions Locust for load testing; also k6 or `hey`. Measure p50/p95/p99 latency and
  error rate at target RPS *before* production does it for you.

## What makes a good API test

- Arrange–Act–Assert, one behaviour per test, named for the behaviour
  (`test_create_duplicate_returns_409`).
- Assert on status code **and** body shape; for errors, on the machine-readable parts (`type`, `loc`),
  not message wording.
- Cover the unhappy paths: validation failures, 401/403, 404, 409, upstream timeouts.
- No sleeps, no network, no shared mutable state, deterministic time and randomness (inject the clock,
  seed RNGs).
- Coverage is a flashlight, not a goal: 100% line coverage with weak assertions proves little.

> [!INTERVIEW]
> "How do you test a FastAPI endpoint that needs a database and an authenticated user?" — Use
> `TestClient(app)` in a pytest fixture; override `get_session` with a session bound to a test database
> (in-memory SQLite with `StaticPool`, or a PostgreSQL container with per-test transaction rollback) and
> override `get_current_user` to return a known user. Assert status codes and JSON. Add separate tests
> without the auth override to verify 401/403 behaviour, clear overrides after each test, and use the
> client as a context manager if lifespan resources are needed.

## Pitfalls

- Forgetting `with TestClient(app)` and wondering why the model/pool is `None`.
- Overrides leaking between tests.
- Testing against SQLite only, deploying on PostgreSQL.
- `async def` tests using the sync `TestClient`.
- Over-mocking: tests pass while the real integration is broken.
- Asserting on exact error message strings.

## Summary

- Unit-test layers with fakes; API-test through `TestClient`; keep a few end-to-end and load tests.
- `TestClient` runs the ASGI app in-process; use it as a context manager for lifespan.
- `app.dependency_overrides` swaps DB sessions, users and settings.
- Async tests: `httpx.AsyncClient(transport=ASGITransport(app=app))` with `pytest.mark.anyio`.
- Test unhappy paths, auth, and the OpenAPI contract.

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
