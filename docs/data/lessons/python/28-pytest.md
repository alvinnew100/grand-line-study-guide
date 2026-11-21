# Testing with pytest

> **Before this lesson:** you should have written a first `assert` and a first test as in [Files, errors and tests: programs you can rely on](#/lesson/python/py-start-files-tests). You need exceptions ([Exceptions](#/lesson/python/py-exceptions)), decorators ([Decorators and functools](#/lesson/python/py-decorators)), context managers and generators with `yield` ([Context managers and contextlib](#/lesson/python/py-context-managers)), and how to install a tool into a project ([Virtual environments, pip, uv and project layout](#/lesson/python/py-envs)).

## In plain words

A **test** is a small piece of code that runs another piece of code and checks that the result is what it should be. "Call the discount function with 200 and 25, and check that the answer is 150." A collection of such checks that the computer can run by itself, in seconds, as often as you like, is an **automated test suite**.

Think of the pre-flight checklist that pilots go through. No pilot trusts memory or a feeling that "it worked yesterday". The same list of concrete checks is carried out before every flight, and the plane leaves only if every item passes. A test suite is that checklist for a program, run before every change is accepted.

Tests buy three things. You can change code without fear, because a broken behaviour shows up at once (a bug that reappears in something that used to work is called a **regression**). Each test is a precise, executable example of how the code is meant to behave. And mistakes are found in seconds at your desk, not days later by a customer.

**pytest** is the standard testing tool of the Python world. With it a test is a plain function, a check is a plain `assert` statement, and a few powerful features cover almost everything else.

Why this matters for a job: every professional team expects changes to arrive with tests, and testing is a standard interview topic ("how would you test this?", "what is a fixture?", "how do you test code that calls an external service?"). During live coding, listing the unusual inputs you would test is one of the easiest ways to make a good impression.

> [!NOTE]
> pytest is a program you run in a terminal, so most examples here are shown as files together with the output you would see. Install it into a project with `uv add --dev pytest` (or `pip install pytest`) and try them. A few boxes with a Run button demonstrate the ideas underneath, here in the page.

## Why test, and what

Two activities are worth keeping apart. **Testing** is checking, by running the code on chosen inputs, that it behaves correctly. **Debugging**, the subject of the next lesson, is finding the cause once a test has failed.

The skill in testing lies in choosing the inputs. Typical inputs are not enough; code tends to break on the unusual ones, called **edge cases**: an empty collection, a single item, all items equal, input already sorted or sorted backwards, values at a limit (0, −1, the maximum size), and invalid input.

Tests also differ in how much of the system they exercise. The usual three levels:

| Level | Tests | Speed | Share of a healthy suite |
|---|---|---|---|
| **Unit** | one function/class in isolation | milliseconds | most |
| **Integration** | several components together (DB, HTTP layer) | slower | some |
| **End-to-end** | the whole system as a user would | slowest | few |

## Your first test

Here is a small function, kept in its own module:

```python
# src/shop/pricing.py
def apply_discount(price: float, percent: float) -> float:
    if not 0 <= percent <= 100:
        raise ValueError("percent must be between 0 and 100")
    return round(price * (1 - percent / 100), 2)
```

And here is a file of tests for it. By convention tests live in a separate `tests` folder:

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

**Reading the test file**

- Each test is an ordinary function whose name starts with `test_`.
- Each contains an `assert`: a statement that does nothing if its condition is true and raises `AssertionError` if it is false. A test **passes** if the function finishes without raising an error and **fails** otherwise.
- The third test checks that a wrong call is *rejected*. `with pytest.raises(ValueError, match="...")` passes only if the block raises a `ValueError` whose message contains the given text.

Typing `pytest` in the project folder finds and runs them:

```
$ pytest
========================= test session starts =========================
collected 3 items

tests/test_pricing.py ...                                        [100%]
========================== 3 passed in 0.02s ==========================
```

Each dot is a passed test. How did pytest know what to run? By its **discovery rules**: it collects files named `test_*.py` or `*_test.py`, functions in them named `test_*`, and methods named `test_*` inside classes named `Test*`. There is nothing to register and no special class to inherit from.

### Plain `assert`, rich failure output

When an `assert` fails, plain Python would only say "AssertionError". pytest rewrites your `assert` statements behind the scenes, so that a failure shows the values involved:

```
    def test_apply_discount_reduces_price():
>       assert apply_discount(200, 25) == 140
E       assert 150.0 == 140
E        +  where 150.0 = apply_discount(200, 25)
```

The report says that the call returned 150.0 while the test expected 140. For lists, dictionaries and long strings pytest shows exactly where the two sides differ. Floats should not be compared with `==` (recall `0.1 + 0.2`); use `pytest.approx`:

```python
assert 0.1 + 0.2 == pytest.approx(0.3)
assert [0.1 + 0.2, 1 / 3] == pytest.approx([0.3, 0.3333], abs=1e-3)
```

A **test runner** is the program that finds tests, runs them and reports. Its core idea is small: find the functions named `test_*`, call each one, and note which raised an error. This toy version runs here:

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

`run_tests` goes through a dictionary of names, calls every function whose name starts with `test_`, and counts a pass when nothing was raised and a failure when an `AssertionError` was. The output shows three `PASS` lines and one `FAIL`, for the test whose expectation is deliberately wrong, with its message. pytest does the same job with far better reports.

## Anatomy of a good test: Arrange, Act, Assert

A readable test has three parts, often remembered as **Arrange, Act, Assert**:

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

Guidelines: test one behaviour per test; give it a descriptive name (`test_<what>_<condition>_<expected>`); keep logic such as loops and `if`s out of tests; and make every test independent of the others and of the order in which they run.

## Parametrisation

When the same check applies to many inputs, do not copy the test; **parametrise** it. The decorator `@pytest.mark.parametrize` takes the names of the test's parameters and a list of value sets, and runs the test once for each set. Each run is reported as a separate test with its own pass or fail.

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

The first test runs five times, once per row; `pytest.param(..., id="free-item")` gives one row a readable name in the report. The second runs three times with three invalid percentages. This style is called table-driven testing: the logic is written once, and each further edge case costs one line.

## Fixtures

Most tests need something prepared before they can start: an object in a known state, a database connection, a temporary folder. A **fixture** is a function that provides such a thing. A test asks for a fixture by **naming it as a parameter**. pytest sees the parameter name, calls the fixture function of that name, and passes the result in. Being handed what you need from outside is the dependency injection of the earlier OOP lesson.

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

Both tests have a parameter called `cart`, so pytest calls the `cart` fixture for each of them. Each test receives a *new* cart, which is why the second test can remove an item without affecting the first.

### Setup and teardown with `yield`

Preparing what a test needs is called **setup**; cleaning up afterwards is **teardown**. A fixture that must clean up uses `yield` in place of `return`:

The code before `yield` is the setup, the yielded value is what the test receives, and the code after `yield` runs when the test has finished, whether it passed or failed.

```python
@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users (name TEXT)")
    yield conn                         # the test runs here
    conn.close()                       # teardown
```

This is the same shape as a `@contextmanager` generator. The idea in a form that runs here:

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

The output shows the order: setup, the body of the test, teardown.

### Scope, sharing and built-ins

- A fixture's **scope** says how often it is created. The default, `scope="function"`, makes a new one for every test. The other scopes, `"class"`, `"module"` and `"session"`, create it once and share it, which suits things that are expensive to set up. A shared fixture must not be changed by the tests that use it.
- A fixture can itself ask for other fixtures in its parameters.
- Put fixtures that several test files share into **`tests/conftest.py`**. pytest finds that file automatically; no import is needed.
- `autouse=True` applies a fixture to every test in its scope without it being asked for.

pytest comes with fixtures of its own. The ones you will use constantly:

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

The first test writes into a temporary folder that pytest creates and later removes. The second sets an environment variable for the duration of one test; `monkeypatch` undoes the change afterwards. The third checks what a function printed.

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

`excinfo.value` is the exception that was caught, so its message can be checked too. If the block does *not* raise, the test fails. A hand-written `try` / `except` test easily gets that wrong, by forgetting the "it should have raised" branch.

## Test doubles: mocks, fakes and monkeypatching

A unit test should not send requests over the network, depend on the real time of day, or touch a real database: such tests are slow and fail for reasons that have nothing to do with your code. The remedy is to replace those dependencies with stand-ins, known collectively as **test doubles**:

- **Fake**: a simple but working replacement, such as a "database" that is a dictionary in memory.
- **Stub**: an object that returns fixed, prepared answers.
- **Mock**: an object that records how it was called, so the test can check the calls afterwards.

The easiest way is to design for it: let a class receive its helpers as arguments, and hand the test a stand-in.

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

- `Signup` receives a `mailer` and a `clock` from outside.
- `Mock()` creates an object that accepts any method call and records it. After `service.register(...)`, the test asks `mailer.send.assert_called_once_with(...)`: was `send` called exactly once, with exactly these arguments? No email is sent anywhere.
- The clock is replaced by a lambda returning a fixed time, which makes the result predictable.
- The second test checks that a bad address raises an error *and* that no mail was sent.
- The last lines show two more features of `Mock`: `side_effect` set to a list makes successive calls return (or raise) the listed items; `call_count` counts the calls.

When the code does not accept its helper as an argument, the test can swap a name temporarily, which is called **patching** (or monkeypatching). The rule is to patch the name **in the module that uses it**:

```python
# shop/weather.py does:  import requests ... requests.get(url)
def test_forecast(monkeypatch):
    class FakeResponse:
        def json(self): return {"temp": 21}
    monkeypatch.setattr("shop.weather.requests.get", lambda url, timeout=5: FakeResponse())
    assert forecast("Lisbon") == 21
```

Here `forecast` would normally call a real weather service through `requests.get`. For the duration of the test, that function is replaced by a lambda returning a prepared answer. `unittest.mock.patch("shop.weather.requests.get")` does the same as a context manager or decorator.

A warning: mocking too much is a sign of trouble. A test that mirrors the implementation line by line breaks at every reorganisation of the code and proves little. Prefer fakes and real objects where they are cheap.

## Markers, selection and useful flags

A **marker** is a label attached to a test with a decorator. Some markers are built in, and you can invent your own:

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

`slow` is a home-made label; `skip` and `skipif` leave a test out (always, or under a condition); `xfail` says "this is expected to fail for now". The command line then selects what to run:

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

Home-made markers and default options are declared in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q --strict-markers"
markers = ["slow: long-running tests"]
```

**Coverage** measures which lines of your code were executed while the tests ran. It finds code that no test touches. It does not prove that the tested code is correct: 100% coverage with weak checks is worthless. Around 80 to 90% with meaningful assertions is a common and sensible target.

## Testing async code and FastAPI (preview)

A **plugin** is an add-on package that extends pytest. With the `pytest-asyncio` (or `anyio`) plugin, a test can be a coroutine and use `await`:

```python
import pytest

@pytest.mark.asyncio
async def test_fetch_user():
    user = await fetch_user(1)
    assert user.name == "Luffy"
```

The web framework FastAPI provides a `TestClient` that sends pretend requests straight to your application inside the test process, so no server has to be started:

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

**Test-driven development** (TDD) reverses the usual order, in a three-step cycle called **red, green, refactor**: write a small test for the next piece of behaviour and watch it fail; write the simplest code that makes it pass; then tidy the code, with the tests as a safety net. Whether or not you follow it strictly, writing tests *while the design can still change* leads to code that is easier to test: smaller functions, helpers passed in as arguments, fewer hidden global variables. And whenever you fix a bug, first write a test that reproduces it. That test proves the fix and keeps the bug from coming back.

## unittest and doctest

Python's standard library has two older testing tools. `unittest` follows the style of Java's JUnit: tests are methods of a class that inherits from `TestCase`, checks are method calls such as `self.assertEqual(a, b)`, and `setUp` / `tearDown` methods prepare and clean up. `doctest` runs the examples written in docstrings and checks that the output shown there is what really comes out. pytest can run both kinds, so an old test suite can be moved over gradually.

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

The docstring contains two examples in the form of an interactive session: a line starting with `>>>` and the expected result below it. `doctest.testmod()` runs them and reports `TestResults(failed=0, attempted=2)`.

> [!INTERVIEW]
> Expect: "How do you test code that calls an external service?" (pass the client in and use a fake, or patch the name where it is looked up; test the real connection separately). "What is a fixture?" (reusable setup and teardown, injected by parameter name, with scopes). "How do you test that an exception is raised?" (`with pytest.raises(E, match=...)`). "What does parametrize do?" And in live coding, listing the edge cases unprompted (empty input, one item, duplicates, negatives, large input) is what interviewers hope to hear.

## Pitfalls recap

- Tests that depend on each other or on the order they run in (shared mutable data, or widely scoped fixtures that tests modify).
- Asserting nothing, so the test cannot fail; or asserting how the code works inside when its behaviour is what matters.
- `assert a == b` with floats; use `pytest.approx`.
- Patching the wrong target; patch the name in the module that *uses* it.
- Real network access, time or randomness in unit tests, which gives tests that sometimes pass and sometimes fail (**flaky** tests). Pass clocks in, and fix the seeds of random generators.
- Naming a file `utils_tests.py` or a function `check_x`: pytest will not collect it.

## Summary

pytest discovers `test_*` functions and gives detailed failure reports for plain `assert` statements. Use `parametrize` for tables of cases; fixtures (with `yield` teardown, scopes and `conftest.py`) for setup; `pytest.raises` for errors; `monkeypatch`, mocks and fakes to isolate dependencies; and markers with command-line options to select what runs. Cover the edge cases, keep tests fast and independent, and write a failing test before fixing any bug.

## Glossary

- **Test** - code that runs other code and checks the result.
- **Test suite** - the full collection of a project's tests.
- **`assert`** - a statement that raises `AssertionError` when its condition is false.
- **Pass / fail** - a test finishing without an error / raising one.
- **Regression** - a bug in something that used to work.
- **Edge case** - an unusual input at the limits of what the code must handle.
- **Unit / integration / end-to-end test** - testing one piece alone / several pieces together / the whole system.
- **Test runner** - the program that finds tests, runs them and reports; here, pytest.
- **Test discovery** - finding tests by naming convention (`test_*.py`, `test_*`).
- **Arrange, Act, Assert** - the three parts of a test: prepare, do, check.
- **Parametrise** - run one test function with many sets of inputs.
- **Fixture** - a function providing something a test needs, requested by parameter name.
- **Setup / teardown** - preparation before a test / cleanup after it.
- **Scope** - how long a fixture lives: per test, class, module or session.
- **`conftest.py`** - the file where shared fixtures are placed.
- **Test double** - a stand-in for a real dependency: a fake, a stub or a mock.
- **Mock** - a stand-in that records how it was called.
- **Patching (monkeypatching)** - temporarily replacing a name or attribute during a test.
- **Marker** - a label attached to a test with `@pytest.mark...`.
- **Coverage** - the share of code lines executed by the tests.
- **TDD** - test-driven development: write the failing test first.
- **Flaky test** - a test that passes or fails unpredictably.

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

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, §2.2.4 (Testing and Debugging), restated in original wording with new examples; pytest documentation ("Get Started", "How to use fixtures", "How to parametrize", "How to monkeypatch"); Python docs, *Library Reference* `unittest.mock` and `doctest`.
