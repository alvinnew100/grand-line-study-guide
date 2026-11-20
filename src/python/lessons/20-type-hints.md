# Type hints and mypy

Python is dynamically typed: names have no declared type and errors like `"3" + 4` surface only when that line runs. **Type hints** let you *optionally* annotate what types you expect; a **static type checker** (mypy, pyright) then finds mismatches without running the code, and your editor gains accurate autocompletion. Hints are also read at runtime by libraries such as dataclasses, Pydantic and FastAPI — which is why this module comes before the FastAPI track.

## The basics

```python-run
def greet(name: str, times: int = 1) -> str:
    return ", ".join([f"hello {name}"] * times)

age: int = 30
ratio: float = 0.5
names: list[str] = ["ana", "ben"]

print(greet("Robin", 2))
print(greet.__annotations__)
print(greet(42, "x") if False else "hints are NOT enforced at runtime")
```

- Parameter annotations follow the name (`name: str`); the return type follows `->`.
- Variable annotations are usually unnecessary when the value makes the type obvious (`age = 30`); checkers **infer** it.
- **Python itself ignores the hints.** They are stored in `__annotations__` and do nothing unless a tool reads them. Calling `greet(42, "x")` raises no error because of the hints (it fails later, for other reasons).

That last point is essential for interviews: type hints are documentation plus tooling, not runtime enforcement.

## Running a type checker

```bash
uv add --dev mypy        # or: pip install mypy
mypy src/                # check a package
mypy --strict app.py     # all the optional strictness flags
```

Given

```python
def total(prices: list[float]) -> float:
    return sum(prices)

total(["1.5", "2"])
```

mypy reports something like:

```
app.py:4: error: List item 0 has incompatible type "str"; expected "float"  [list-item]
```

Pyright (the engine behind VS Code's Pylance) is a faster alternative with similar semantics. Either way, the checker runs in your editor and in CI, catching whole classes of bugs — `None` dereferences, wrong argument order, misspelled attributes — before any test executes.

**Gradual typing**: code without annotations is treated as `Any` and not checked, so you can add hints one function at a time. `--strict` (or `disallow_untyped_defs = true` in `pyproject.toml`) makes missing annotations an error.

## Built-in collection types

Since Python 3.9 you parameterise the built-in classes directly (older code imports `List`, `Dict`, `Tuple` from `typing`):

| Annotation | Meaning |
|---|---|
| `list[int]` | list of ints |
| `dict[str, float]` | str keys, float values |
| `set[str]`, `frozenset[str]` | sets of strings |
| `tuple[int, str]` | exactly two items: an int and a str |
| `tuple[int, ...]` | any number of ints |
| `list[dict[str, list[int]]]` | nesting works |

```python-run
def word_lengths(words: list[str]) -> dict[str, int]:
    return {w: len(w) for w in words}

Point = tuple[float, float]              # a type alias

def midpoint(a: Point, b: Point) -> Point:
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)

print(word_lengths(["sun", "moon"]), midpoint((0, 0), (2, 4)))
```

## Optional and unions

A value that may be one of several types is a **union**, written `X | Y` (3.10+; `Union[X, Y]` before). The most important union is "maybe `None`": `X | None`, also spelled `Optional[X]`.

```python-run
def find_user(user_id: int) -> str | None:
    users = {1: "luffy", 2: "zoro"}
    return users.get(user_id)

def shout(user_id: int) -> str:
    name = find_user(user_id)
    # return name.upper()      # mypy: Item "None" of "str | None" has no attribute "upper"
    if name is None:
        return "NOBODY"
    return name.upper()        # here the checker knows name is str

print(shout(1), shout(9))
```

This is **type narrowing**: after `if name is None: return`, the checker knows `name` is a `str`. Narrowing also works with `isinstance`, `in`, truthiness, `match`, and early returns. It's how a checker turns "billion-dollar mistake" `None` bugs into compile-time errors.

Note `Optional[X]` does *not* mean "optional argument"; it means "X or None". A parameter with a default is optional to pass regardless of its type: `def f(n: int = 0)`.

## Any, object and friends

| Type | Meaning |
|---|---|
| `Any` | opt out of checking: every operation is allowed, compatible with everything |
| `object` | any value, but you may only use operations all objects support — the *safe* "anything" |
| `None` | the type of `None` (as a return type: the function returns nothing) |
| `NoReturn` / `Never` | the function never returns normally (always raises / loops forever) |
| `Literal["r", "w"]` | only these exact values |
| `Final` | a name that must not be reassigned |
| `type[Animal]` | the class itself (or a subclass), not an instance |

```python-run
from typing import Any, Literal, Final

MAX_RETRIES: Final = 3

def open_mode(mode: Literal["r", "w", "a"]) -> str:
    return {"r": "read", "w": "write", "a": "append"}[mode]

def log(value: object) -> str:
    return repr(value)             # fine: every object has repr

def trust_me(value: Any) -> int:
    return value.anything.goes()   # type checker stays silent — and so the bug survives

print(open_mode("w"), log([1, 2]))
```

Use `Any` sparingly: it's contagious and silently switches checking off.

## Callables and abstract collection types

Annotate *what you need*, not the concrete type you happen to pass. A function that only loops over its argument should accept `Iterable[int]`, so callers can pass a list, tuple, set, or generator. These live in `collections.abc`:

| Type | Accepts |
|---|---|
| `Iterable[T]` | anything you can loop over once |
| `Iterator[T]` / `Generator[Y, S, R]` | iterators / generators |
| `Sequence[T]` | indexable, sized, read-only: list, tuple, str, range |
| `Mapping[K, V]` | read-only dict-like |
| `MutableSequence[T]`, `MutableMapping[K, V]` | when you mutate the argument |
| `Callable[[A, B], R]` | a callable taking `(A, B)` and returning `R` |

"Be liberal in what you accept, specific in what you return": accept `Iterable[int]`, return `list[int]`.

```python-run
from collections.abc import Callable, Iterable, Iterator, Sequence

def apply_all(funcs: Iterable[Callable[[int], int]], x: int) -> list[int]:
    return [f(x) for f in funcs]

def countdown(n: int) -> Iterator[int]:
    while n > 0:
        yield n
        n -= 1

def first(items: Sequence[str]) -> str | None:
    return items[0] if items else None

print(apply_all([abs, lambda v: v * 2], -3), list(countdown(3)), first(("a", "b")), first([]))
```

## Classes as types

Every class is a type. Methods annotate `self` implicitly; use `Self` (3.11+) for methods returning their own type and for fluent APIs. For forward references (a class mentioned before it's defined), either quote the name or add `from __future__ import annotations`, which makes all annotations lazy strings.

```python-run
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Node:
    value: int
    next: Node | None = None          # refers to the class being defined

    def push(self, value: int) -> Node:
        return Node(value, self)

def length(node: Node | None) -> int:
    n = 0
    while node is not None:           # narrowing in a loop
        n += 1
        node = node.next
    return n

print(length(Node(1).push(2).push(3)))
```

Dataclass fields *are* annotations — the decorator reads them at runtime to generate `__init__`. That's the same trick Pydantic and FastAPI use, with validation added.

## Type aliases and NewType

```python-run
from typing import NewType

UserId = NewType("UserId", int)          # distinct type for the checker; zero runtime cost
Json = dict[str, "Json"] | list["Json"] | str | int | float | bool | None   # recursive alias

def load_user(uid: UserId) -> str:
    return f"user#{uid}"

uid = UserId(42)
print(load_user(uid), type(uid).__name__)
# load_user(42)   # mypy error: expected UserId, got int — prevents mixing up ids
```

Python 3.12 adds the `type` statement for aliases: `type Point = tuple[float, float]`.

## Useful checker tools

- `reveal_type(x)` — ask the checker what it thinks `x` is (mypy prints it; also exists in `typing` at runtime from 3.11).
- `cast(T, x)` — tell the checker "trust me, it's a T" (no runtime check).
- `# type: ignore[code]` — silence one specific error on a line; always include the code and a reason.
- `assert isinstance(x, T)` — narrows *and* checks at runtime.
- `typing.get_type_hints(obj)` — resolve annotations at runtime (what frameworks use).
- `TYPE_CHECKING` — a constant that's `False` at runtime, `True` for checkers; guard imports needed only for hints.

```python-run
from typing import cast, get_type_hints, TYPE_CHECKING

def area(w: float, h: float) -> float:
    return w * h

print(get_type_hints(area), TYPE_CHECKING)
raw: object = "42"
n = int(cast(str, raw))        # cast does nothing at runtime
print(n)
```

## Worked example: typing a small module

```python-run
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

Level = Literal["INFO", "WARN", "ERROR"]

@dataclass(frozen=True)
class Event:
    level: Level
    module: str
    message: str

def parse(line: str) -> Event | None:
    parts = line.split(" ", 2)
    if len(parts) != 3 or parts[0] not in ("INFO", "WARN", "ERROR"):
        return None
    level, module, message = parts
    return Event(level, module, message)        # a strict checker wants a cast/narrow for Level

def count_by_module(events: Iterable[Event], level: Level = "ERROR") -> dict[str, int]:
    counts: defaultdict[str, int] = defaultdict(int)
    for e in events:
        if e.level == level:
            counts[e.module] += 1
    return dict(counts)

lines = ["ERROR db timeout", "INFO api started", "ERROR db reset", "garbage", "ERROR api 500"]
events = [e for line in lines if (e := parse(line)) is not None]     # narrowing inside a comprehension
print(count_by_module(events))
```

The signatures alone now tell a reader what flows where — and the checker verifies that `parse`'s possible `None` is handled before events are counted.

> [!INTERVIEW]
> "Are type hints enforced at runtime?" — No. The interpreter stores them in `__annotations__` and ignores them; static checkers (mypy/pyright) and libraries (dataclasses, Pydantic, FastAPI) read them. "What's `Optional[int]`?" — `int | None`. "Difference between `Any` and `object`?" — `Any` disables checking; `object` is the top type and only permits universal operations. "Why annotate parameters with `Iterable`/`Sequence` instead of `list`?" — accept the most general type that supports what you actually do.

## Pitfalls recap

- Believing hints validate input at runtime.
- `def f(x: list = [])` — hints don't fix the mutable-default bug.
- `Optional[X]` ≠ "optional parameter".
- Over-using `Any` and `# type: ignore`.
- Annotating parameters too concretely (`list[int]` when `Iterable[int]` would do) — note `list[int]` is not accepted where `list[float]` is expected (lists are *invariant*), while `Sequence[int]` is fine for `Sequence[float]`.
- Using new syntax (`X | Y`, `list[int]`) at runtime on old Python versions.

## Summary

Type hints annotate parameters, returns and variables; checkers verify them statically and infer the rest. Use built-in generics (`list[int]`), unions (`X | None`) with narrowing, abstract collection types for parameters, `Literal`/`Final`/`NewType` for precision, and keep `Any` rare. They cost nothing at runtime and pay for themselves in tooling and readability.

```quiz
[
  {"q": "What happens at runtime when you call `def f(x: int)` as `f('hello')`?", "options": ["TypeError from the annotation", "Nothing special: annotations are not enforced by the interpreter", "A warning is printed", "The string is converted to int"], "answer": 1,
   "explain": "Hints are metadata. Only tools like mypy, or libraries that read annotations, act on them."},
  {"q": "`Optional[str]` is the same as:", "options": ["str with a default value", "str | None", "Any", "list[str]"], "answer": 1,
   "explain": "Optional[X] is shorthand for Union[X, None]; it says nothing about default arguments."},
  {"q": "After `if name is None: return`, a checker treats `name: str | None` as:", "options": ["str | None", "str", "None", "Any"], "answer": 1,
   "explain": "Type narrowing removes None from the union on the path where the check failed."},
  {"q": "Which parameter annotation is best for a function that only iterates once over numbers?", "options": ["list[int]", "Iterable[int]", "dict[int, int]", "Any"], "answer": 1,
   "explain": "Iterable is the least demanding type that supports a for loop, so lists, tuples, sets and generators all qualify."},
  {"q": "Difference between Any and object?", "options": ["None", "Any turns checking off; object accepts everything but only allows operations valid for all objects", "object is deprecated", "Any is only for functions"], "answer": 1,
   "explain": "object is the safe top type; Any is an escape hatch."},
  {"q": "What does `tuple[int, ...]` mean?", "options": ["A 2-tuple of int and Ellipsis", "A tuple of any length whose items are all ints", "A list of ints", "Invalid syntax"], "answer": 1,
   "explain": "The ellipsis form describes a homogeneous variable-length tuple."},
  {"q": "What does `NewType('UserId', int)` give you?", "options": ["A runtime subclass with validation", "A distinct static type for checkers that is just an int at runtime", "A dataclass", "An alias identical to int for checkers"], "answer": 1,
   "explain": "Checkers treat UserId as different from int, preventing mix-ups; at runtime UserId(x) returns x."}
]
```

> **Source:** Python docs, *Library Reference* `typing` and "Static Typing with Python" (typing.python.org); PEPs 484, 526, 585, 604; mypy documentation ("Getting started", "Type narrowing").
