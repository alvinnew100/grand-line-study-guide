# Type hints and mypy

> **Before this lesson:** you need the idea that types belong to objects, not names ("dynamic typing"), from [Objects, names, types and mutability](#/lesson/python/py-objects-names); function definitions from [Functions and arguments](#/lesson/python/py-functions-args); and dataclasses from [Properties, dataclasses, ABCs and composition](#/lesson/python/py-properties-dataclasses). The commands in this lesson assume you can install a tool into a project, as shown in [Virtual environments, pip, uv and project layout](#/lesson/python/py-envs).

## In plain words

Python does not ask you to say what kind of value a variable holds or a function expects. That is convenient, and it has a cost: a mistake such as adding the text `"3"` to the number `4` is discovered only when that line runs, which may be in front of a customer.

A **type hint** is an optional note in the code saying what type you expect: "this parameter is a string", "this function returns a list of numbers". Python itself does not act on these notes. A separate program called a **type checker** (the best known are mypy and pyright) reads them and reports every place where the code contradicts its own notes, *without running the program*. Checking a program by reading it, as opposed to running it, is called **static** checking.

An everyday picture: labels on the drawers of a workshop. The drawer works the same with or without a label, and nothing physically stops you from putting screws in the drawer marked "nails". But a colleague, or an inspector walking round with a checklist, can now spot the mistake by looking, and you can find things without opening every drawer.

Hints pay for themselves in three ways. The checker finds whole classes of bugs before any test runs. Your editor can complete names and show documentation accurately, because it knows what each value is. And the hints are precise documentation for the next reader. Almost all professional Python code written today is type-hinted, some libraries (dataclasses, Pydantic, FastAPI) read the hints while the program runs, and interviewers regularly ask "are type hints enforced at runtime?" The answer is no, and this lesson shows it.

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

**Reading this code line by line**

- In `def greet(name: str, times: int = 1) -> str:`, each parameter's hint follows its name after a colon, a default value comes after the hint, and the type of the returned value follows the arrow `->`. A hint written in the code is called an **annotation**.
- The next three lines annotate variables. This is usually unnecessary when the value already makes the type clear (`age = 30`): checkers work the type out for themselves, which is called **inference**. `list[str]` means "a list whose items are strings".
- `greet.__annotations__` shows where the hints are kept: in a dictionary attached to the function.
- The last line makes the central point. It would call `greet(42, "x")`, with both arguments of the wrong type, and Python would not object *because of the hints*. (The call sits behind `if False` so that the demo does not run it; it would in fact fail a moment later for an unrelated reason, inside the function.)

**Python itself ignores the hints.** They are stored and otherwise do nothing unless a tool reads them.

Remember this for interviews: type hints are documentation and tooling. They are not checks performed while the program runs.

## Running a type checker

A type checker is installed like any other development tool and run from the terminal:

```bash
uv add --dev mypy        # or: pip install mypy
mypy src/                # check a package
mypy --strict app.py     # all the optional strictness flags
```

The first line installs mypy into the project, the second checks every file of a package, and the third checks one file with all the optional strict rules switched on. Suppose the file contains this:

```python
def total(prices: list[float]) -> float:
    return sum(prices)

total(["1.5", "2"])
```

The function promises to accept a list of floats, and the call passes a list of strings. Without running anything, mypy reports something like:

```
app.py:4: error: List item 0 has incompatible type "str"; expected "float"  [list-item]
```

The message gives the file, the line, what is wrong and a short code in square brackets naming the rule. Pyright, which powers the Python support of the editor VS Code, is a faster alternative that behaves much the same. Teams run a checker both in the editor, where mistakes are underlined as you type, and on the automated build server, so that nothing unchecked gets merged. It catches using a value that might be `None`, arguments in the wrong order, misspelled attribute names and many similar slips.

**Gradual typing** means you do not have to annotate everything at once. Code without annotations is given the special type `Any` and is not checked, so hints can be added one function at a time. The `--strict` option (or the setting `disallow_untyped_defs = true` in `pyproject.toml`) turns a missing annotation into an error, once a project is ready for that.

## Built-in collection types

A hint for a container usually says what is inside it too. Since Python 3.9 you write the item type in square brackets after the built-in name. A type that takes another type as a parameter in this way is called **generic**. (Older code imports capitalised versions, `List`, `Dict` and `Tuple`, from the `typing` module; they mean the same.)

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

`word_lengths` takes a list of strings and returns a dictionary from strings to integers. `Point = tuple[float, float]` gives a name to a type; such a name is a **type alias**, and it makes the signature of `midpoint` far easier to read than three repetitions of the tuple type would be.

## Optional and unions

A value that may be one of several types has a **union** type, written `X | Y` (Python 3.10 and later; before that, `Union[X, Y]`). The most important union is "an `X`, or nothing": `X | None`, which may also be written `Optional[X]`.

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

`find_user` returns a name or `None`, and its return type says so. In `shout`, the commented-out line shows what a checker rejects: `name` might be `None`, and `None` has no `upper` method. The `if name is None:` test deals with that case and returns. On every line after it, the checker knows that `name` can only be a `str`. Refining a type by following the program's tests in this way is called **type narrowing**. It also works with `isinstance`, `in`, truthiness tests, `match` and early returns.

Narrowing is how a checker turns the most common crash in programming, using a missing value as if it were present, into an error you see while writing the code.

Do not be misled by the word: `Optional[X]` does *not* mean "an argument you may leave out". It means "an `X` or `None`". Whether an argument can be left out depends on whether the parameter has a default value, whatever its type: `def f(n: int = 0)`.

## Any, object and friends

A handful of special types describe situations that no ordinary class covers:

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

In the demo, `Final` marks a constant; `Literal["r", "w", "a"]` allows exactly those three strings, so a checker rejects `open_mode("x")`; `object` accepts anything but lets the function do only what works on every object, such as `repr`; and `Any` lets `trust_me` do something absurd with no complaint from the checker. Use `Any` sparingly. It spreads: everything computed from an `Any` value is `Any` too, so checking is silently switched off along the whole path.

## Callables and abstract collection types

Annotate a parameter with *what the function needs*, not with the particular type you happen to pass today. A function that only loops over its argument should accept `Iterable[int]`; callers may then pass a list, a tuple, a set or a generator. These broad, role-based types live in `collections.abc` (in the tables, `T`, `K`, `V` and so on stand for "some type"):

| Type | Accepts |
|---|---|
| `Iterable[T]` | anything you can loop over once |
| `Iterator[T]` / `Generator[Y, S, R]` | iterators / generators |
| `Sequence[T]` | indexable, sized, read-only: list, tuple, str, range |
| `Mapping[K, V]` | read-only dict-like |
| `MutableSequence[T]`, `MutableMapping[K, V]` | when you mutate the argument |
| `Callable[[A, B], R]` | a callable taking `(A, B)` and returning `R` |

A good rule: be generous in what you accept and exact in what you return. Accept `Iterable[int]`; return `list[int]`.

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

- `apply_all` takes "anything loopable whose items are functions from an `int` to an `int`". `Callable[[int], int]` lists the argument types in the inner brackets and then the return type.
- `countdown` is a generator, so its return type is `Iterator[int]`: something that produces integers.
- `first` needs indexing, so it asks for a `Sequence[str]` and accepts a tuple as readily as a list. It returns `str | None`.

## Classes as types

Every class you define can be used as a type in a hint. The parameter `self` needs no annotation. For a method that returns an object of its own class, use `Self` (Python 3.11+).

One problem arises when a class mentions *itself* inside its own body, as a linked-list node does: at that moment the class name does not exist yet. Such a mention is a **forward reference**. Either put the name in quotes (`"Node"`), or add `from __future__ import annotations` as the first line of the file, which makes Python keep every annotation as text and not evaluate it.

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

`Node | None` describes the link to the next node, or the end of the chain. In `length`, the test `while node is not None` narrows the type inside the loop, so `node.next` is accepted. Three nodes are built and the program prints 3.

Notice that the fields of a dataclass *are* annotations: the decorator reads them while the program runs in order to generate `__init__`. Pydantic and FastAPI use the same trick and add real validation on top.

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

An alias is only another name for the same type. `NewType` goes further: it creates a type that the *checker* treats as different from `int`, although while the program runs a `UserId` is a plain integer (the print shows `int`). The benefit is that a checker rejects `load_user(42)`, and with it the classic mistake of passing an order number where a user number was expected. The second line shows that an alias may refer to itself: `Json` describes any value that can appear in JSON data.

Python 3.12 adds a dedicated statement for aliases: `type Point = tuple[float, float]`.

## Useful checker tools

- `reveal_type(x)` asks the checker what type it believes `x` has; mypy prints the answer. (From Python 3.11 it also exists in `typing`, so the line does not crash when run.)
- `cast(T, x)` tells the checker "trust me, this is a `T`". Nothing is checked or converted when the program runs.
- `# type: ignore[code]` silences one specific error on one line. Always include the code and a comment saying why.
- `assert isinstance(x, T)` narrows the type *and* really checks it at run time.
- `typing.get_type_hints(obj)` returns an object's annotations as real types while the program runs; frameworks use it.
- `TYPE_CHECKING` is a constant that is `False` when the program runs and `True` for checkers. An import placed under `if TYPE_CHECKING:` is seen only by the checker, which is useful for imports needed solely for hints.

```python-run
from typing import cast, get_type_hints, TYPE_CHECKING

def area(w: float, h: float) -> float:
    return w * h

print(get_type_hints(area), TYPE_CHECKING)
raw: object = "42"
n = int(cast(str, raw))        # cast does nothing at runtime
print(n)
```

The first print shows the hints of `area` as a dictionary of real types, and `False` for `TYPE_CHECKING`. In the last lines `raw` is declared as `object`, so a checker would refuse `int(raw)`; `cast(str, raw)` vouches for it. The program prints 42.

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

This small module reads lines of a log and counts errors per module:

- `Level` is an alias for "one of these three strings".
- `Event` is a frozen dataclass with three typed fields.
- `parse` returns an `Event`, or `None` for a line it cannot understand. The return type forces every caller to think about the `None` case.
- `count_by_module` accepts any iterable of events and a level that must be one of the three allowed strings.
- The comprehension on the second-to-last line parses each line, stores the result in `e` with the walrus operator, and keeps only the results that are not `None`; a checker understands that the resulting list contains only `Event` objects.

The output is `{'db': 2, 'api': 1}`.

The function headers alone now tell a reader what goes in and what comes out, and the checker confirms that the possible `None` from `parse` is dealt with before events are counted.

> [!INTERVIEW]
> "Are type hints enforced at runtime?" No. Python stores them in `__annotations__` and ignores them; static checkers (mypy, pyright) and some libraries (dataclasses, Pydantic, FastAPI) read them. "What is `Optional[int]`?" `int | None`. "`Any` versus `object`?" `Any` switches checking off; `object` accepts every value but allows only the operations every object supports. "Why annotate a parameter as `Iterable` or `Sequence` and not `list`?" To accept the most general type that supports what the function actually does.

## Pitfalls recap

- Believing that hints check input while the program runs.
- `def f(x: list = [])`: a hint does not cure the mutable-default bug.
- Reading `Optional[X]` as "optional parameter".
- Over-using `Any` and `# type: ignore`.
- Annotating parameters too narrowly (`list[int]` when `Iterable[int]` would do). A related surprise: a `list[int]` is not accepted where a `list[float]` is expected, because the function might append a float to your list of ints (lists are said to be *invariant*); a `Sequence[int]` is accepted where `Sequence[float]` is expected, because a read-only sequence cannot be damaged that way.
- Using new syntax (`X | Y`, `list[int]`) in code that must run on old Python versions.

## Summary

Type hints annotate parameters, return values and variables; a checker verifies them without running the code and infers the rest. Use the built-in generic types (`list[int]`), unions (`X | None`) together with narrowing, the role-based collection types for parameters, and `Literal`, `Final` and `NewType` for precision; keep `Any` rare. Hints cost nothing while the program runs and repay the effort in tooling and readability.

## Glossary

- **Type hint (annotation)** - an optional note in the code stating the expected type of a parameter, return value or variable.
- **Static type checker** - a tool, such as mypy or pyright, that finds type mistakes by reading code without running it.
- **Dynamic typing** - types belong to objects and are checked only while the program runs.
- **Inference** - the checker working out a type that was not written down.
- **Gradual typing** - adding hints piece by piece; unannotated code is treated as `Any`.
- **Generic type** - a type that takes another type as a parameter, such as `list[int]`.
- **Type alias** - a name given to a type expression.
- **Union** - "one of several types", written `X | Y`.
- **`Optional[X]`** - `X | None`.
- **Type narrowing** - the checker refining a type after a test such as `is None` or `isinstance`.
- **`Any`** - the type that switches checking off.
- **`object`** - the type of every value; allows only universal operations.
- **`Literal`** - a type limited to specific constant values.
- **`Final`** - marks a name that must not be reassigned.
- **`Callable`** - the type of things that can be called, with argument and return types.
- **`Iterable` / `Sequence` / `Mapping`** - role-based types for "loopable" / "indexable and sized" / "dictionary-like".
- **Forward reference** - a mention of a type before it has been defined.
- **`NewType`** - a distinct type for the checker that is a plain value at run time.
- **`cast`** - a statement to the checker that a value has a given type; no run-time effect.
- **Invariant** - said of a generic type whose `X[int]` is not accepted in place of `X[float]`.

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
