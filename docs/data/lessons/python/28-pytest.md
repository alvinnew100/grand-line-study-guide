# Testing with pytest

Code without tests works only by coincidence and stays working only by luck. Automated tests let you change code confidently, document intended behaviour with executable examples, and catch regressions in seconds instead of in production. **pytest** is the de-facto standard test framework for Python: tests are plain functions, checks are plain `assert` statements, and a small set of powerful features — fixtures, parametrisation, markers — covers nearly everything.

> [!NOTE]
> pytest is a command-line tool, so most examples here are shown as files plus terminal output. Install it in your project with `uv add --dev pytest` (or `pip install pytest`) and try them. A few runnable snippets below show the underlying ideas in the browser.

## Why test, and what

Goodrich (§2.2.4) distinguishes **testing** — experimentally checking correctness on a representative set of inputs — from **debugging** — tracking down the cause once a test fails. Good test inputs cover the **special cases** where code tends to break: empty collections, a single element, all-equal elements, already-sorted and reverse-sorted input, boundaries (0, −1, maximum sizes), and invalid input. The classic levels:

| Level | Tests | Speed | Share of a healthy suite |
|---|---|---|---|
| **Unit** | one function/class in isolation | milliseconds | most |
| **Integration** | several components together (DB, HTTP layer) | slower | some |
| **End-to-end** | the whole system as a user would | slowest | few |

## Your first test

```python
# src/shop/pricing.py
def apply_discount(price: float, percent: float) -> float:
    if not 0 <= percent <= 100:
        raise ValueError("percent must be between 0 and 100")
    return round(price * (1 - percent / 100), 2)
```

```python
# tests/test_pricing.py
import pytest
from shop.pricing import apply_discount

def test_apply_discount_reduces_price():
    assert apply_discount(200, 25) == 150

def test_zero_discount_keeps_price():
    assert apply_discount(99.99, 0) == 99.99

def test_invalid_percent_raises():
    with pytest.raises(ValueError, match="between 0 and 100"):
        apply_discount(100, 150)
```

```
$ pytest
========================= test session starts =========================
collected 3 items

tests/test_pricing.py ...                                        [100%]
========================== 3 passed in 0.02s ==========================
```

**Discovery rules**: pytest collects files named `test_*.py` or `*_test.py`, functions named `test_*`, and methods named `test_*` inside classes named `Test*` (no `__init__`). No base class, no boilerplate.

### Plain `assert`, rich failure output

pytest rewrites `assert` statements so that failures show the values involved:

```
    def test_apply_discount_reduces_price():
>       assert apply_discount(200, 25) == 140
E       assert 150.0 == 140
E        +  where 150.0 = apply_discount(200, 25)
```

For containers and long strings you get a diff. Compare floats with `pytest.approx`:

```python
assert 0.1 + 0.2 == pytest.approx(0.3)
assert [0.1 + 0.2, 1 / 3] == pytest.approx([0.3, 0.3333], abs=1e-3)
```

The essence of a test runner is tiny — find functions named `test_*`, call them, report which raised. This toy version runs here:

```python-run
import math

def apply_discount(price, percent):
    if not 0 <= percent <= 100:
        raise ValueError("percent must be between 0 and 100")
    return round(price * (1 - percent / 100), 2)

def test_discount():
    assert apply_discount(200, 25) == 150

def test_floats():
    assert math.isclose(0.1 + 0.2, 0.3)

def test_wrong_expectation():
    assert apply_discount(100, 10) == 80, "10% off 100 should be 90"

def test_invalid_percent():
    try:
        apply_discount(100, 150)
    except ValueError:
        return
    raise AssertionError("expected ValueError")

def run_tests(namespace):
    passed = failed = 0
    for name, fn in sorted(namespace.items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                passed += 1
                print(f"PASS {name}")
            except AssertionError as e:
                failed += 1
                print(f"FAIL {name}: {e}")
    print(f"{passed} passed, {failed} failed")

run_tests(dict(globals()))
```

## Anatomy of a good test: Arrange, Act, Assert

```python
def test_cart_total_includes_tax():
    # Arrange: build the world
    cart = Cart(tax_rate=0.2)
    cart.add("cola", price=10, qty=2)
    # Act: do the one thing under test
    total = cart.total()
    # Assert: check the outcome
    assert total == 24
```

One behaviour per test; a descriptive name (`test_<what>_<condition>_<expected>`); no logic (loops/ifs) in tests; independent of other tests and of execution order.

## Parametrisation

When the same check applies to many inputs, don't copy-paste — parametrise. Each case becomes its own test with its own pass/fail line.

```python
import pytest
from shop.pricing import apply_discount

@pytest.mark.parametrize(
    ("price", "percent", "expected"),
    [
        (100, 0, 100),
        (100, 100, 0),
        (200, 25, 150),
        (19.99, 10, 17.99),
        pytest.param(0, 50, 0, id="free-item"),
    ],
)
def test_apply_discount(price, percent, expected):
    assert apply_discount(price, percent) == expected

@pytest.mark.parametrize("bad", [-1, 100.01, 1000])
def test_rejects_out_of_range(bad):
    with pytest.raises(ValueError):
        apply_discount(100, bad)
```

This is table-driven testing: the test logic is written once, and edge cases are one line each.

## Fixtures

A **fixture** is a function that provides something a test needs — an object, a database connection, a temp directory, a configured client. A test requests a fixture simply by **naming it as a parameter**; pytest calls the fixture and injects the result (dependency injection).

```python
import pytest
from shop.cart import Cart

@pytest.fixture
def cart():
    c = Cart(tax_rate=0.2)
    c.add("cola", price=10, qty=2)
    return c

def test_total(cart):
    assert cart.total() == 24

def test_remove(cart):
    cart.remove("cola")
    assert cart.total() == 0          # each test gets a FRESH cart
```

### Setup and teardown with `yield`

Code after `yield` runs after the test — even if the test fails:

```python
@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users (name TEXT)")
    yield conn                         # the test runs here
    conn.close()                       # teardown
```

It's the same shape as `@contextmanager`. The idea in runnable form:

```python-run
from contextlib import contextmanager

@contextmanager
def fake_db():
    print("  setup: connect")
    conn = {"users": []}
    try:
        yield conn
    finally:
        print("  teardown: close")

def test_insert():
    with fake_db() as db:
        db["users"].append("robin")
        assert db["users"] == ["robin"]
        print("  test body ran")

test_insert()
```

### Scope, sharing and built-ins

- `@pytest.fixture(scope="function")` (default) — fresh per test. Other scopes: `"class"`, `"module"`, `"session"` — create once and share, for expensive resources. Shared fixtures must not be mutated by tests.
- Fixtures can request other fixtures, forming a dependency graph.
- Put shared fixtures in **`tests/conftest.py`**; pytest finds them automatically, no import needed.
- `autouse=True` applies a fixture to every test in scope.

Built-in fixtures you'll use constantly:

| Fixture | Gives you |
|---|---|
| `tmp_path` | a unique temporary directory (`pathlib.Path`) per test |
| `monkeypatch` | temporarily set attributes, dict items, environment variables |
| `capsys` | captured stdout/stderr |
| `caplog` | captured log records |
| `request` | information about the requesting test (advanced) |

```python
def test_writes_report(tmp_path):
    out = tmp_path / "report.txt"
    write_report(out, ["a", "b"])
    assert out.read_text(encoding="utf-8") == "a\nb\n"

def test_reads_api_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    assert load_settings().api_key == "test-key"

def test_greets(capsys):
    greet("Brook")
    assert capsys.readouterr().out == "Hello, Brook!\n"
```

## Testing exceptions and warnings

```python
def test_parse_rejects_garbage():
    with pytest.raises(ValueError) as excinfo:
        parse_age("forty")
    assert "forty" in str(excinfo.value)

def test_deprecated_call_warns():
    with pytest.warns(DeprecationWarning):
        old_api()
```

If the block doesn't raise, the test fails — the mistake a hand-written `try/except` test often makes (forgetting the "should have raised" branch).

## Test doubles: mocks, fakes and monkeypatching

Unit tests shouldn't hit the network, real clocks, or production databases. Replace such dependencies with stand-ins:

- **Fake**: a simple working implementation (in-memory repository).
- **Stub**: returns canned answers.
- **Mock**: records how it was called so you can assert on interactions.

The easiest route is designing for it — pass dependencies in (dependency injection), then hand the test a fake:

```python-run
from unittest.mock import Mock

class Signup:
    def __init__(self, mailer, clock):
        self.mailer, self.clock = mailer, clock
    def register(self, email):
        if "@" not in email:
            raise ValueError("invalid email")
        self.mailer.send(to=email, subject="Welcome!")
        return {"email": email, "at": self.clock()}

def test_register_sends_welcome_mail():
    mailer = Mock()
    service = Signup(mailer, clock=lambda: "2026-01-01T00:00:00")
    result = service.register("nami@sea.org")
    mailer.send.assert_called_once_with(to="nami@sea.org", subject="Welcome!")
    assert result["at"] == "2026-01-01T00:00:00"

def test_register_rejects_bad_email():
    mailer = Mock()
    try:
        Signup(mailer, clock=lambda: 0).register("nope")
        raise AssertionError("should have raised")
    except ValueError:
        pass
    mailer.send.assert_not_called()

test_register_sends_welcome_mail(); test_register_rejects_bad_email()
print("both tests passed")

m = Mock(return_value=3)
m.side_effect = [1, ValueError("boom")]
print(m(), m.call_count)
```

When you can't inject, patch the name **where it is looked up**:

```python
# shop/weather.py does:  import requests ... requests.get(url)
def test_forecast(monkeypatch):
    class FakeResponse:
        def json(self): return {"temp": 21}
    monkeypatch.setattr("shop.weather.requests.get", lambda url, timeout=5: FakeResponse())
    assert forecast("Lisbon") == 21
```

`unittest.mock.patch("shop.weather.requests.get")` does the same as a context manager/decorator. Over-mocking is a smell: tests that mirror the implementation line by line break on every refactor and prove little. Prefer fakes and real objects where cheap.

## Markers, selection and useful flags

```python
@pytest.mark.slow
def test_full_reindex(): ...

@pytest.mark.skip(reason="waiting for API v2")
def test_new_endpoint(): ...

@pytest.mark.skipif(sys.platform == "win32", reason="POSIX only")
def test_fork(): ...

@pytest.mark.xfail(reason="known bug #123")
def test_rounding_edge(): ...
```

| Command | Effect |
|---|---|
| `pytest -q` / `-v` | quieter / one line per test |
| `pytest tests/test_pricing.py::test_zero_discount_keeps_price` | run one test |
| `pytest -k "discount and not invalid"` | select by name expression |
| `pytest -m "not slow"` | select by marker |
| `pytest -x` / `--maxfail=3` | stop at first / third failure |
| `pytest --lf` / `--ff` | rerun last failures / failures first |
| `pytest -s` | don't capture output (see your prints) |
| `pytest --pdb` | drop into the debugger on failure |
| `pytest -n auto` | run in parallel (plugin `pytest-xdist`) |
| `pytest --cov=shop --cov-report=term-missing` | coverage (plugin `pytest-cov`) |

Register custom markers and defaults in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q --strict-markers"
markers = ["slow: long-running tests"]
```

**Coverage** measures which lines ran during tests. It finds untested code; it does not prove tested code is correct. 100% coverage with weak assertions is worthless; ~80–90% with meaningful assertions is a common, sensible target.

## Testing async code and FastAPI (preview)

With the `pytest-asyncio` (or `anyio`) plugin, tests can be coroutines:

```python
import pytest

@pytest.mark.asyncio
async def test_fetch_user():
    user = await fetch_user(1)
    assert user.name == "Luffy"
```

FastAPI ships a `TestClient` that calls your app in-process — no server needed:

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_item():
    response = client.get("/items/42")
    assert response.status_code == 200
    assert response.json()["id"] == 42
```

## Test-driven development in one paragraph

**Red → Green → Refactor**: write a small failing test that states the next behaviour; write the simplest code that makes it pass; clean up with the tests as a safety net. Whether or not you practise strict TDD, writing the test *while the design is still soft* yields code that is easier to test — smaller functions, injected dependencies, fewer hidden globals. And whenever you fix a bug, first write a test that reproduces it: it proves the fix and prevents the regression.

## unittest and doctest

The standard library has `unittest` (xUnit style: classes deriving from `TestCase`, `self.assertEqual(...)`, `setUp`/`tearDown`) and `doctest` (runs examples embedded in docstrings). pytest runs both kinds, so legacy suites migrate gradually.

```python-run
import doctest

def slugify(title):
    """Turn a title into a URL slug.

    >>> slugify("Hello, World!")
    'hello-world'
    >>> slugify("  Many   spaces ")
    'many-spaces'
    """
    import re
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")

print(doctest.testmod())
```

> [!INTERVIEW]
> Expect: "How do you test code that calls an external API?" (inject the client and use a fake, or patch where the name is looked up; test the real integration separately). "What's a fixture?" (reusable setup/teardown injected by parameter name, with scopes). "How do you test that an exception is raised?" (`with pytest.raises(E, match=...)`). "What does parametrize do?" And when live-coding, proactively listing edge cases — empty input, one element, duplicates, negatives, large input — is what interviewers want to hear.

## Pitfalls recap

- Tests that depend on each other or on execution order (shared mutable state, module-scoped fixtures mutated by tests).
- Asserting nothing (a test that can't fail), or asserting implementation details instead of behaviour.
- `assert a == b` with floats; use `pytest.approx`.
- Patching the wrong target — patch the name in the module that *uses* it.
- Real network/time/randomness in unit tests → flaky tests. Inject clocks, seed RNGs.
- Naming a file `utils_tests.py` or a function `check_x` — pytest won't collect it.

## Summary

pytest discovers `test_*` functions and gives detailed failure reports for plain `assert`s. Use `parametrize` for tables of cases, fixtures (with `yield` teardown, scopes and `conftest.py`) for setup, `pytest.raises` for errors, `monkeypatch`/mocks/fakes to isolate dependencies, and markers plus CLI flags to select what runs. Cover the edge cases, keep tests fast and independent, and write a failing test before fixing any bug.

```quiz
[
  {"q": "Which function will pytest collect as a test by default?", "options": ["def check_total():", "def test_total():", "def total_test():", "def Test():"], "answer": 1,
   "explain": "By default pytest collects functions prefixed with test_ in files named test_*.py or *_test.py."},
  {"q": "How does a test receive a fixture?", "options": ["By importing it", "By naming the fixture as a parameter of the test function", "By calling setup()", "Via a global variable"], "answer": 1,
   "explain": "pytest matches parameter names to fixture names and injects the fixture's return (or yielded) value."},
  {"q": "In a fixture that uses `yield`, when does the code after yield run?", "options": ["Before the test", "After the test finishes, even if it failed", "Only if the test passed", "Never"], "answer": 1,
   "explain": "The part after yield is teardown, executed when the fixture goes out of scope."},
  {"q": "What does @pytest.mark.parametrize do?", "options": ["Runs tests in parallel", "Runs the same test function once per set of arguments, as separate test cases", "Skips tests", "Creates fixtures"], "answer": 1,
   "explain": "Each parameter set is reported individually, making table-driven tests easy."},
  {"q": "Correct way to assert that parse('x') raises ValueError?", "options": ["assert parse('x') == ValueError", "with pytest.raises(ValueError): parse('x')", "try: parse('x') except: pass", "pytest.fail(ValueError)"], "answer": 1,
   "explain": "pytest.raises fails the test if the block does not raise the expected exception."},
  {"q": "Where should fixtures shared by many test files live?", "options": ["In each test file", "tests/conftest.py", "setup.py", "__init__.py of the package"], "answer": 1,
   "explain": "pytest automatically loads conftest.py files and makes their fixtures available to tests in that directory tree."},
  {"q": "What does high line coverage guarantee?", "options": ["The code is correct", "Only that those lines executed during tests", "No bugs remain", "Good performance"], "answer": 1,
   "explain": "Coverage reveals untested code; it says nothing about the quality of assertions."},
  {"q": "When patching `requests.get` used inside `shop/weather.py` (which does `import requests`), a reliable target is:", "options": ["'requests.post'", "'shop.weather.requests.get'", "'builtins.get'", "'weather.get'"], "answer": 1,
   "explain": "Patch the attribute as looked up by the module under test."}
]
```

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, §2.2.4 (Testing and Debugging); pytest documentation ("Get Started", "How to use fixtures", "How to parametrize", "How to monkeypatch"); Python docs, *Library Reference* `unittest.mock` and `doctest`.
