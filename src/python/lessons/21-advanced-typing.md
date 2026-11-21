# Generics, Protocol, TypedDict and Pydantic

> **Before this lesson:** read [Type hints and mypy](#/lesson/python/py-type-hints) first. You need annotations, unions, `Any`, narrowing and the idea of a static type checker. Duck typing and abstract base classes come from [Properties, dataclasses, ABCs and composition](#/lesson/python/py-properties-dataclasses), and decorators from [Decorators and functools](#/lesson/python/py-decorators).

## In plain words

The previous lesson covered the hints you write every day. This one covers the tools for describing *reusable* code precisely. There are four, and each answers one question.

- **Generics**: "this function works for a list of anything, and what comes out is the same kind of thing that went in." A vending machine is generic: it does not care which drinks are loaded, but if you loaded cola, cola is what comes out. Writing that link down lets the checker keep track of the type.
- **Protocols**: "I accept any object that can do X; I do not care what class it is." A job advert that says "must be able to drive", not "must be a graduate of this particular driving school".
- **TypedDict**: "this dictionary has exactly these keys, with these value types." A paper form with named boxes, as opposed to a blank sheet.
- **Pydantic**: a popular library that takes the same kind of hints and *really checks the data while the program runs*. This is the guard at the door who inspects what arrives from outside.

Why this matters for a job: these appear in the headers of nearly every modern library, so you need to read them even if you seldom write them. FastAPI, one of the most used web frameworks, is built on Pydantic. Interviewers ask "what is a Protocol and how does it differ from an abstract base class?" and "what does a TypeVar do?". The lesson ends with a look at what these constructs are while the program runs, which is how frameworks make use of them.

## Generics with TypeVar

Suppose a function `first` returns the first item of a sequence. If you annotate it as taking `Sequence[Any]` and returning `Any`, information is thrown away: the checker no longer knows that `first([1, 2])` is an `int`, so it cannot catch `first([1, 2]).upper()`. A **type variable** is a placeholder that stands for "some type, to be worked out at each call". Using the same placeholder in the parameter and in the return type links the two:

```python-run
from typing import TypeVar
from collections.abc import Sequence

T = TypeVar("T")

def first(items: Sequence[T]) -> T:
    return items[0]

n = first([1, 2, 3])        # checker infers int
s = first("abc")            # checker infers str
print(n + 1, s.upper())
```

`T = TypeVar("T")` creates the placeholder (the name is passed as a string too, for technical reasons). In the header, `Sequence[T]` and `-> T` say: whatever the items are, that is what is returned. At each call the checker works out what `T` must be. For `first([1, 2, 3])` it is `int`, so `n + 1` is accepted; for `first("abc")` it is `str`, so `s.upper()` is accepted. A function or class written with type variables is called **generic**.

Python 3.12 added a lighter spelling that declares the placeholder in square brackets after the function name. Both mean the same; most existing code uses the `TypeVar` form.

```python
def first[T](items: Sequence[T]) -> T:      # Python 3.12+
    return items[0]
```

### Bounds and constraints

A plain `T` can stand for any type at all, so the function body may not assume anything about it. Two ways of restricting it:

- **Bound**: `TypeVar("T", bound=Base)` says `T` must be `Base` or a subclass of it. The body may then use `Base`'s methods, and the exact type is still preserved for the caller.
- **Constraints**: `TypeVar("T", int, str)` says `T` must be exactly one of the listed types.

```python-run
from typing import TypeVar
from collections.abc import Iterable, Hashable

H = TypeVar("H", bound=Hashable)

def dedupe(items: Iterable[H]) -> list[H]:
    seen: set[H] = set()
    out: list[H] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

print(dedupe([3, 1, 3, 2, 1]), dedupe("mississippi"))
```

`dedupe` removes repeated items while keeping the first of each. It puts items into a set, which works only for hashable items, so the type variable is bound to `Hashable`. A checker would reject `dedupe([[1], [1]])`, a list of unhashable lists, while still knowing that `dedupe([3, 1, 3])` returns a `list[int]`. The output is `[3, 1, 2] ['m', 'i', 's', 'p']`.

For "any type that supports `<`" the usual solution is to bind the variable to a Protocol, shown further down.

## Generic classes

A class can be generic too. A container that works for items of any type is generic in the type of its items:

```python-run
from typing import Generic, TypeVar

T = TypeVar("T")

class Stack(Generic[T]):
    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        if not self._items:
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def __len__(self) -> int:
        return len(self._items)

ints: Stack[int] = Stack()
ints.push(1); ints.push(2)
# ints.push("three")       # mypy: Argument 1 to "push" has incompatible type "str"; expected "int"
print(ints.pop() + 10, len(ints), Stack[str])
```

Inheriting from `Generic[T]` declares that `Stack` has one type parameter. Inside the class, `T` is used wherever "the item type" is meant. The variable `ints` is annotated `Stack[int]`, and from then on the checker knows that `push` takes an `int` and `pop` returns one; the commented line shows the error a string would cause. (While the program runs, nothing stops it. More on that under "What exists at runtime?".)

In Python 3.12 and later the header can be written `class Stack[T]:`. The built-in `list[int]` and `dict[str, int]` are generic classes of exactly this kind.

### Variance in one paragraph

**Variance** is the question of when a container of one type may stand in for a container of a related type. Is a `list[int]` acceptable where a `list[float]` is expected? **No**: the function receiving it could append `1.5` to your list of integers. Containers that can be changed are **invariant**: only the exact type will do. Read-only types such as `Sequence[int]` and `Iterable[int]` are **covariant**: they are accepted where `Sequence[float]` is expected, because nothing can be put into them. `Callable` is **contravariant** in its argument types, meaning the relationship runs the other way round. The practical rule: if mypy complains that `list[Dog]` is not a `list[Animal]`, change the parameter to `Sequence[Animal]`.

## Protocol: static duck typing

Python code has always relied on duck typing: "if it has a `.read()` method, I can use it". `typing.Protocol` lets you write that expectation down as a type. A class satisfies a protocol **structurally**, that is, by having the right methods and attributes. It does not inherit from the protocol and need not know that the protocol exists.

```python-run
from typing import Protocol, runtime_checkable

class Speaker(Protocol):
    name: str
    def speak(self) -> str: ...

class Dog:                              # does NOT inherit from Speaker
    def __init__(self, name: str) -> None:
        self.name = name
    def speak(self) -> str:
        return "woof"

class Robot:
    name = "R2"
    def speak(self) -> str:
        return "beep"

def introduce(s: Speaker) -> str:
    return f"{s.name} says {s.speak()}"

print(introduce(Dog("Chopper")), "|", introduce(Robot()))

@runtime_checkable
class SupportsClose(Protocol):
    def close(self) -> None: ...

import io
print(isinstance(io.StringIO(), SupportsClose), isinstance(3, SupportsClose))
```

- `Speaker` is the protocol: anything with a `name` that is a string and a `speak()` method returning a string. The bodies are `...`, because a protocol only describes.
- `Dog` and `Robot` do not mention `Speaker` anywhere. Both have the required members, so a checker accepts both as arguments of `introduce`.
- The second half shows an optional extra. Decorating a protocol with `@runtime_checkable` allows `isinstance` tests against it while the program runs: an in-memory file has a `close` method (`True`), the integer 3 does not (`False`).

Why protocols matter:

- You can describe types you do not own (classes from other libraries, built-ins) without subclassing them.
- The code stays loosely connected: the *user* of an object states the small interface it needs, and any class that fits may be supplied.
- It is the natural type for dependency injection and for the fakes used in tests (see the lesson on properties, dataclasses and composition).

A caution about `@runtime_checkable`: the `isinstance` test only verifies that members with those *names* exist. It does not look at their parameters or return types.

**ABC or Protocol?** An abstract base class is *nominal*: a class must name it as a base (or be registered). In return it can refuse to create incomplete objects and can share code. A Protocol is *structural* and exists for the static checker (plus the shallow run-time test above).

Protocols and type variables combine well. Here is the "anything that can be compared" case promised above:

```python-run
from typing import Protocol, TypeVar, Any
from collections.abc import Iterable

class SupportsLessThan(Protocol):
    def __lt__(self, other: Any) -> bool: ...

C = TypeVar("C", bound=SupportsLessThan)

def smallest(items: Iterable[C]) -> C:
    it = iter(items)
    best = next(it)
    for x in it:
        if x < best:
            best = x
    return best

print(smallest([3, 1, 2]), smallest(["pear", "apple"]), smallest([(2, "b"), (1, "z")]))
```

`SupportsLessThan` describes any type that has `__lt__`, the method behind `<`. The type variable `C` is bound to it, so `smallest` accepts numbers, strings and tuples alike, and the checker knows that the result has the same type as the items.

## TypedDict: typed dictionaries

Data from the outside world very often arrives as JSON (a text format for nested lists and dictionaries, covered in the files lesson), which Python turns into dictionaries with known string keys and values of various types. The hint `dict[str, Any]` tells a checker nothing about such data. `TypedDict` describes the exact keys and the type of each value, while the object itself remains a plain `dict`.

```python-run
from typing import TypedDict, NotRequired

class Address(TypedDict):
    city: str
    zip: str

class User(TypedDict):
    id: int
    name: str
    email: NotRequired[str]             # key may be absent
    address: Address

def label(u: User) -> str:
    # u["nmae"]  -> mypy: TypedDict "User" has no key "nmae"
    return f'{u["id"]}: {u["name"]} ({u["address"]["city"]})'

u: User = {"id": 1, "name": "Nami", "address": {"city": "Cocoyasi", "zip": "0001"}}
print(label(u), type(u).__name__, u.get("email"))
```

`User` requires `id`, `name` and `address`; `email` is marked `NotRequired`, so the key may be missing; and `address` is itself a typed dictionary. The comment inside `label` shows what a checker catches: a misspelled key. The printed type name is `dict`, and `u.get("email")` is `None`.

Nothing is validated while the program runs: `TypedDict` is purely for the static checker. Compare the three ways of describing a record:

| | Runtime type | Validates at runtime | Use when |
|---|---|---|---|
| `TypedDict` | plain `dict` | no | typing existing dict/JSON-shaped data |
| `@dataclass` | your class | no (unless you add it) | internal domain objects |
| Pydantic `BaseModel` | your class | **yes**, with coercion | data arriving from outside your program (web requests, files, settings) |

## A few more advanced tools

- **`ParamSpec`** stands for a function's *entire parameter list*, so that a decorator can state "my wrapper takes exactly what the original takes".
- **`@overload`** declares several signatures for one function (for example: `str` in gives `str` out, `bytes` in gives `bytes` out).
- **`TypeGuard` / `TypeIs`** let you write your own narrowing functions.
- **`Annotated[T, metadata]`** attaches extra information to a type without changing it. FastAPI and Pydantic rely on it: `Annotated[int, Field(gt=0)]` is "an int, with the rule that it must be greater than 0".
- **`Self`** means "the class this method belongs to", for methods that return their own object.

```python-run
import functools, time
from typing import Callable, ParamSpec, TypeVar, Annotated, get_type_hints

P = ParamSpec("P")
R = TypeVar("R")

def timed(func: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            wrapper.last_ms = (time.perf_counter() - start) * 1000   # type: ignore[attr-defined]
    return wrapper

@timed
def add(a: int, b: int = 0) -> int:
    return a + b

print(add(2, b=3))          # the checker still knows add(a: int, b: int = 0) -> int

Positive = Annotated[int, "must be > 0"]
def buy(qty: Positive) -> None: ...
print(get_type_hints(buy, include_extras=True))
```

The `timed` decorator from the decorators lesson, now with types. `Callable[P, R]` in, `Callable[P, R]` out says that the decorated function keeps its exact parameters `P` and return type `R`; inside, `*args: P.args, **kwargs: P.kwargs` ties the wrapper's arguments to the same parameter list. Without `ParamSpec`, every decorated function would look to the checker like "takes anything". The last lines show `Annotated`: the metadata string travels with the type and can be read back with `get_type_hints(..., include_extras=True)`.

## Pydantic preview

Pydantic is a third-party library (installed with `uv add pydantic` or `pip install pydantic`). It reads the annotations on a class and **enforces them while the program runs**. Given input data, it converts values that can sensibly be converted (the text `"1.50"` to the float 1.5; this is called **coercion**), checks any extra rules, and raises a detailed `ValidationError` if the data does not fit. FastAPI uses Pydantic models for the data it receives and sends. The library is not available on this page, so the next block is shown, not run:

```python
from pydantic import BaseModel, Field, ValidationError

class Item(BaseModel):
    name: str
    price: float = Field(gt=0)              # constraint: must be > 0
    tags: list[str] = []                    # safe: Pydantic copies defaults per instance
    in_stock: bool = True

item = Item(name="Cola", price="1.50")      # "1.50" is coerced to the float 1.5
print(item)                                 # name='Cola' price=1.5 tags=[] in_stock=True
print(item.model_dump())                    # -> plain dict
print(item.model_dump_json())               # -> JSON string

try:
    Item(name="Bad", price=-3, tags="oops")
except ValidationError as e:
    print(e.error_count(), "validation errors")
    # price: Input should be greater than 0
    # tags: Input should be a valid list

data = Item.model_validate({"name": "Meat", "price": 12})        # from a dict
data = Item.model_validate_json('{"name": "Meat", "price": 12}') # from JSON text
```

A class becomes a model by inheriting from `BaseModel`. Creating an `Item` validates the data: the price given as text is converted, and the bad second item is rejected with a list of everything wrong with it. `model_dump()` and `model_validate()` convert between models and plain dictionaries or JSON text.

The core idea, validation driven by annotations, fits in a few lines of standard-library Python. The toy version below does run here, and shows that nothing mysterious is involved:

```python-run
from typing import get_type_hints

class ValidationError(ValueError):
    pass

class MiniModel:
    """A 15-line caricature of pydantic.BaseModel (flat fields, simple types only)."""
    def __init__(self, **data):
        hints = get_type_hints(type(self))
        errors = []
        for field, expected in hints.items():
            if field not in data:
                if hasattr(type(self), field):
                    setattr(self, field, getattr(type(self), field))     # class-level default
                else:
                    errors.append(f"{field}: field required")
                continue
            value = data[field]
            try:
                setattr(self, field, value if isinstance(value, expected) else expected(value))
            except (TypeError, ValueError):
                errors.append(f"{field}: expected {expected.__name__}, got {value!r}")
        if errors:
            raise ValidationError("; ".join(errors))
    def __repr__(self):
        return f"{type(self).__name__}({vars(self)})"

class Item(MiniModel):
    name: str
    price: float
    qty: int = 1

print(Item(name="Cola", price="1.50"))
try:
    Item(price="cheap", qty="many")
except ValidationError as e:
    print("ValidationError:", e)
```

`MiniModel.__init__` reads the annotations of the class with `get_type_hints` and walks through them. A field that was not supplied takes the class-level default if there is one and is otherwise recorded as an error. A supplied value is kept if it already has the right type; if not, the type itself is called to convert it (`float("1.50")`), and a failed conversion is recorded as an error. At the end, all errors are reported together.

The first call prints `Item({'name': 'Cola', 'price': 1.5, 'qty': 1})`: the price was converted and the default quantity filled in. The second reports three problems at once: `name` missing, `price` not a float, `qty` not an int.

In FastAPI, writing `def create(item: Item)` for a web address is enough for the framework to read the incoming JSON, validate it against the model, answer with a 422 error and the details when it is invalid, and publish a description of the expected data, all driven by the type hints.

> [!INTERVIEW]
> "What is a Protocol and how does it differ from an ABC?" Structural (duck) typing checked statically, versus nominal inheritance enforced at run time. "What is a TypeVar for?" To relate types within one signature (the same `T` in and out), so that generic code keeps exact types. "TypedDict, dataclass or Pydantic?" A dictionary shape for the static checker only; a plain class; a model validated at run time. "How does FastAPI use type hints?" It inspects the annotations to read, validate (through Pydantic) and document the data of each request and response.

## What exists at runtime?

The typing constructs are ordinary Python objects, and it helps to know which of them leave a trace while the program runs. An expression such as `list[int]` or `Box[int]` is a real object that remembers its parameters. The *instances* created through it do not remember them. This loss is called **type erasure**:

```python-run
from typing import Generic, TypeVar, get_origin, get_args, get_type_hints, Optional, Protocol

T = TypeVar("T")
class Box(Generic[T]):
    def __init__(self, item: T) -> None:
        self.item = item

alias = Box[int]
print(alias, get_origin(alias) is Box, get_args(alias))
b = Box[int]("not an int")                 # no runtime check: parameters are erased
print(type(b) is Box, b.item)

print(get_origin(dict[str, list[int]]), get_args(dict[str, list[int]]))
print(get_args(Optional[int]), get_args(int | None) == get_args(Optional[int]))

def handler(user_id: int, tags: list[str] | None = None) -> dict[str, int]: ...
for name, hint in get_type_hints(handler).items():
    print(f"  {name}: {hint}")
try:
    isinstance([1, 2], list[int])
except TypeError as e:
    print("TypeError:", e)
```

- `Box[int]` prints as an object of its own; `get_origin` returns the class it was made from (`Box`) and `get_args` the parameters (`(int,)`).
- `Box[int]("not an int")` is accepted when run: the parameter is not checked, and the resulting object is a plain `Box`.
- The same two functions take apart `dict[str, list[int]]` and show that `Optional[int]` and `int | None` are the same union.
- `get_type_hints(handler)` returns each parameter's annotation as a real object.
- `isinstance([1, 2], list[int])` is refused with a `TypeError`.

`get_type_hints`, `get_origin` and `get_args` are what frameworks use to walk through annotations. FastAPI sees `user_id: int` and converts that part of the web address to an integer; Pydantic sees `list[str] | None` and builds a check for "a list of strings, or nothing". Python refuses `isinstance(x, list[int])` because checking the item types would mean examining every item; a library that wants that check has to go through the items itself.

Here is that idea in miniature: a function that follows an annotation recursively and checks a value against it. In spirit, this is what Pydantic builds from your model.

```python-run
from typing import get_origin, get_args, Union
import types

def conforms(value, hint) -> bool:
    origin, args = get_origin(hint), get_args(hint)
    if hint is None or hint is type(None):
        return value is None
    if origin in (Union, types.UnionType):
        return any(conforms(value, a) for a in args)
    if origin is list:
        return isinstance(value, list) and all(conforms(v, args[0]) for v in value)
    if origin is dict:
        return isinstance(value, dict) and all(conforms(k, args[0]) and conforms(v, args[1]) for k, v in value.items())
    if origin is tuple:
        return isinstance(value, tuple) and len(value) == len(args) and all(map(conforms, value, args))
    return isinstance(value, hint)

checks = [
    ([1, 2, 3], list[int]), ([1, "2"], list[int]), ({"a": [1.5]}, dict[str, list[float]]),
    (None, int | None), ("x", int | None), ((1, "a"), tuple[int, str]),
]
for value, hint in checks:
    print(f"{value!r:<16} {str(hint):<24} {conforms(value, hint)}")
```

`conforms` takes the hint apart with `get_origin` and `get_args`. For a union it tries each alternative; for a list it checks the container and then every item against the item type; likewise for dictionaries and fixed-length tuples; for a plain class it falls back to `isinstance`. The printed table shows `True` for `[1, 2, 3]` as `list[int]`, `False` for `[1, "2"]`, `True` for the nested dictionary, and so on.

## Reading checker errors on generics

Three messages account for most of the confusion with advanced typing:

- **`Argument 1 has incompatible type "list[Dog]"; expected "list[Animal]"`** is invariance. Mypy adds a note suggesting `Sequence`. Change the *parameter's* annotation (accept `Sequence[Animal]` or `Iterable[Animal]`), not the call.
- **`Value of type variable "T" cannot be "str"`**: the argument breaks the type variable's bound or constraints. Look at what `bound=` requires.
- **`"Robot" is missing following "Speaker" protocol member: name`** (or "incompatible signature"): the class does not fit the protocol, and the note says exactly which member differs. Attribute *types* and method signatures must match, not only the names.

When it is unclear what the checker has worked out, insert `reveal_type(expr)`. It prints the type it deduced, and you can see where precision was lost, which is usually at an `Any` or at a function without annotations.

## Choosing among the tools

| You want to express | Use |
|---|---|
| "same type in, same type out" | `TypeVar` |
| "any type with method `m`" | `Protocol` (optionally as a TypeVar bound) |
| "one of these exact values" | `Literal[...]` or an `Enum` |
| "a dict with these keys" | `TypedDict` |
| "an int that is a user id, not an order id" | `NewType` |
| "a type plus validation metadata" | `Annotated[T, ...]` |
| "must inherit from my base and share code" | ABC |
| "validate untrusted input at runtime" | Pydantic model |

How far should you go? Precise types pay off most at the **edges of a module**, in functions other code calls, and in **library code** with many users. Inside a short private function, inference already does the work. If an annotation takes longer to write than the function it describes, make it simpler: a readable `Callable[..., Any]` with a comment is better than a wall of nested generics that nobody maintains.

## Pitfalls recap

- Using `Any` where a `TypeVar` would keep the type.
- Expecting `TypedDict` or dataclasses to validate data while the program runs.
- Passing `list[Child]` where `list[Parent]` is expected (invariance); accept `Sequence[Parent]`.
- `isinstance` against a `@runtime_checkable` protocol tests only that the members *exist*.
- Reusing one `TypeVar` for unrelated things: within one signature, the same variable must stand for one type.

## Summary

`TypeVar` and `Generic` (or the bracket syntax of Python 3.12) describe functions and classes that work in the same way for many types. `Protocol` gives duck-typed interfaces a structural type. `TypedDict` describes dictionaries shaped like JSON. `ParamSpec`, `Annotated` and `Self` cover decorators, metadata and methods returning their own object. Pydantic turns the same annotations into reading and validation at run time, which is the foundation of FastAPI.

## Glossary

- **Generic** - written to work with many types while keeping track of which one is in use.
- **Type variable (`TypeVar`)** - a placeholder for a type, worked out by the checker at each use.
- **Bound / constraints** - a rule that a type variable must be a subtype of a given type / exactly one of several types.
- **`Generic[T]`** - the base class that makes a class generic in `T`.
- **Variance** - the rules for when `X[A]` may be used where `X[B]` is expected.
- **Invariant / covariant / contravariant** - only the exact type fits / subtypes fit / supertypes fit.
- **Protocol** - a type defined by required methods and attributes, satisfied without inheritance.
- **Structural / nominal typing** - matching by shape / matching by declared base class.
- **`@runtime_checkable`** - allows `isinstance` tests against a protocol (names only).
- **`TypedDict`** - a description of a dictionary's keys and value types, for the static checker only.
- **`ParamSpec`** - a placeholder for a whole parameter list, used to type decorators.
- **`Annotated`** - a type with extra metadata attached.
- **Pydantic** - a third-party library that validates and converts data at run time from annotations.
- **Coercion** - converting a value to the expected type, such as `"1.50"` to `1.5`.
- **Validation** - checking that data fits the declared types and rules.
- **Type erasure** - instances not remembering the type parameters they were created with.
- **`get_origin` / `get_args`** - functions that take a generic type apart at run time.

```quiz
[
  {"q": "For `def first(items: Sequence[T]) -> T`, what does a checker infer for `first(['a', 'b'])`?", "options": ["Any", "str", "list[str]", "object"], "answer": 1,
   "explain": "T is solved as str from the argument, so the return type is str."},
  {"q": "A class satisfies a Protocol when:", "options": ["It inherits from the protocol", "It has the required methods/attributes with compatible types, no inheritance needed", "It is registered with abc", "It is decorated with @protocol"], "answer": 1,
   "explain": "Protocols use structural subtyping: matching shape is enough."},
  {"q": "Why isn't `list[int]` accepted where `list[float]` is expected?", "options": ["int is not a float", "Lists are mutable and therefore invariant: the callee could insert a float", "It is accepted", "Because of TypedDict"], "answer": 1,
   "explain": "Mutable containers are invariant. Read-only Sequence[int] is acceptable as Sequence[float]."},
  {"q": "What is a TypedDict instance at runtime?", "options": ["A special validated object", "A plain dict", "A dataclass", "A namedtuple"], "answer": 1,
   "explain": "TypedDict only informs the type checker; no runtime validation or new type exists."},
  {"q": "What does Pydantic add on top of type hints?", "options": ["Faster execution", "Runtime parsing, coercion and validation driven by the annotations", "Static checking", "Nothing"], "answer": 1,
   "explain": "Pydantic reads annotations when a model is instantiated and validates/coerces the input, raising ValidationError on failure."},
  {"q": "`TypeVar('T', bound=Hashable)` means:", "options": ["T is exactly Hashable", "T may be any type that is a subtype of Hashable", "T is int or str", "T is Any"], "answer": 1,
   "explain": "A bound restricts the variable to subtypes while preserving the specific type."},
  {"q": "Which tool lets a decorator preserve the wrapped function's parameter types?", "options": ["TypedDict", "ParamSpec", "Literal", "NewType"], "answer": 1,
   "explain": "ParamSpec captures the full parameter list so Callable[P, R] -> Callable[P, R] keeps the signature."}
]
```

> **Source:** Python docs, *Library Reference* `typing` (Generics, Protocols, TypedDict, ParamSpec, Annotated); PEPs 544, 589, 612, 695; mypy documentation ("Generics", "Protocols and structural subtyping"); Pydantic documentation ("Models", "Fields").
