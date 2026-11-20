# Generics, Protocol, TypedDict and Pydantic

The previous lesson covered everyday annotations. This one covers the tools that let you type *reusable* code precisely: **generics** (functions and classes that work for any type while keeping track of which one), **Protocols** (static duck typing), **TypedDict** (typed dictionaries for JSON-shaped data), and a preview of **Pydantic**, which turns type hints into runtime validation and powers FastAPI.

## Generics with TypeVar

Suppose `first` returns the first element of a list. Annotating it `list[Any] -> Any` throws away information: the checker no longer knows that `first([1, 2])` is an `int`. A **type variable** links the input and output types:

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

Each call *solves* `T`: for `first([1, 2, 3])`, `T = int`, so the return type is `int`.

Python 3.12 added a lighter syntax (PEP 695) that declares the type parameter inline. Both spellings mean the same; you'll see the `TypeVar` form in most existing code:

```python
def first[T](items: Sequence[T]) -> T:      # Python 3.12+
    return items[0]
```

### Bounds and constraints

- **Bound**: `TypeVar("T", bound=Base)` — `T` must be `Base` or a subclass. Lets you call `Base`'s methods while preserving the precise type.
- **Constraints**: `TypeVar("T", int, str)` — `T` must be exactly one of the listed types.

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

For "anything that supports `<`", the idiom is a Protocol bound (see below).

## Generic classes

A container class that works for any element type is generic in that type:

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

In 3.12+: `class Stack[T]:`. Built-in `list[int]`, `dict[str, int]` are generic classes of exactly this kind.

### Variance in one paragraph

Is a `list[int]` acceptable where a `list[float]` is expected? **No** — the function could append `1.5` to your list of ints. Mutable containers are **invariant**. Read-only types like `Sequence[int]` and `Iterable[int]` are **covariant** (fine where `Sequence[float]` is expected). `Callable` is **contravariant** in its arguments. If mypy complains that `list[Dog]` isn't `list[Animal]`, change the parameter to `Sequence[Animal]`.

## Protocol: static duck typing

Python code traditionally relies on duck typing: "if it has a `.read()` method, I can use it". `typing.Protocol` lets you write that expectation as a type. A class satisfies a protocol **structurally** — just by having the right methods and attributes — with no inheritance required.

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

Why it matters:

- You can describe types you don't own (third-party classes, built-ins) without subclassing them.
- It keeps code decoupled: the consumer defines the small interface it needs ("interface segregation").
- It's the natural type for dependency injection and test fakes.

`@runtime_checkable` permits `isinstance` checks, but they only verify that the members *exist*, not their signatures.

**ABC vs Protocol**: an ABC is *nominal* (you must inherit or register) and can enforce implementation at instantiation time and share code; a Protocol is *structural* and purely for static checking (plus the shallow runtime check above).

A common Protocol-bounded generic — "anything comparable":

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

## TypedDict: typed dictionaries

JSON arrives as dicts with known string keys and differently-typed values. `dict[str, Any]` tells the checker nothing; `TypedDict` describes the shape while the runtime value remains a plain `dict`.

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

No validation happens at runtime — `TypedDict` is purely static. Compare the three "record" options:

| | Runtime type | Validates at runtime | Use when |
|---|---|---|---|
| `TypedDict` | plain `dict` | no | typing existing dict/JSON-shaped data |
| `@dataclass` | your class | no (unless you add it) | internal domain objects |
| Pydantic `BaseModel` | your class | **yes**, with coercion | data crossing a trust boundary (HTTP, files, env) |

## A few more advanced tools

- **`ParamSpec`** — captures a callable's whole parameter list, so decorators can preserve signatures.
- **`@overload`** — declare several signatures for one function (e.g., `str` in → `str` out, `bytes` in → `bytes` out).
- **`TypeGuard` / `TypeIs`** — user-defined narrowing functions.
- **`Annotated[T, metadata]`** — attach extra information to a type; FastAPI and Pydantic use it heavily (`Annotated[int, Field(gt=0)]`).
- **`Self`** — "the type of the current class", for fluent methods and alternative constructors.

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

## Pydantic preview

Pydantic is a third-party library (`uv add pydantic`) that reads the annotations on a class and **enforces them at runtime**: it parses input data, coerces compatible values, validates constraints, and raises a detailed `ValidationError` otherwise. FastAPI uses Pydantic models for request bodies, responses and settings — so this is a preview of what's coming.

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

The essence — validation driven by annotations — fits in a few lines of standard-library Python. This toy version runs here and shows there is no magic involved:

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

In FastAPI, declaring `def create(item: Item)` on a route is enough for the framework to parse the JSON body, validate it against the model, return a 422 with error details when it's invalid, and document the schema in OpenAPI — all from the type hints.

> [!INTERVIEW]
> "What's a Protocol and how does it differ from an ABC?" — structural (duck) typing checked statically vs nominal inheritance enforced at runtime. "What is a TypeVar for?" — to relate types within a signature (same `T` in and out) so generic code keeps precise types. "TypedDict vs dataclass vs Pydantic?" — static-only dict shape vs plain class vs runtime-validated model. "How does FastAPI use type hints?" — it inspects annotations to parse, validate (via Pydantic) and document request/response data.

## What exists at runtime?

Typing constructs are ordinary objects, and it helps to know which of them leave a trace when the program runs. Generic aliases such as `list[int]` are real objects that remember their parameters; the *instances* you create from them do not — this is called **type erasure**:

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

`get_type_hints`, `get_origin` and `get_args` are the tools frameworks use to walk annotations: FastAPI sees `user_id: int` and converts the path segment; Pydantic sees `list[str] | None` and builds a validator for "list of strings or null". You cannot ask `isinstance(x, list[int])`, because checking element types would mean scanning the whole container — libraries that want that check do the scan themselves.

Here is that idea in miniature: a validator that recursively follows an annotation, which is conceptually what Pydantic compiles from your model:

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

## Reading checker errors on generics

Three messages account for most of the confusion with advanced typing:

- **`Argument 1 has incompatible type "list[Dog]"; expected "list[Animal]"`** — invariance. Mypy even adds a note suggesting `Sequence`. Fix the *parameter* annotation (accept `Sequence[Animal]` or `Iterable[Animal]`), not the call site.
- **`Value of type variable "T" cannot be "str"`** — the argument violates the TypeVar's bound or constraints; check what `bound=` demands.
- **`"Robot" is missing following "Speaker" protocol member: name`** (or "incompatible signature") — structural mismatch; the note lists exactly which member differs. Remember that attribute *types* and method signatures must match, not just names.

When inference is unclear, insert `reveal_type(expr)`; the checker prints what it deduced and you can see where precision was lost (usually at an `Any` or an unannotated function).

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

How far to go? Precise types pay off most at **module boundaries** and in **library code** that many callers use; inside a short private function, inference already does the work. If an annotation takes longer to write than the function, simplify it — a readable `Callable[..., Any]` with a comment beats a wall of nested generics nobody maintains.

## Pitfalls recap

- Using `Any` where a `TypeVar` would preserve the type.
- Expecting `TypedDict` or dataclasses to validate data at runtime.
- `list[Child]` passed where `list[Parent]` is expected (invariance) — accept `Sequence[Parent]`.
- `@runtime_checkable` isinstance checks only test member *presence*.
- Reusing one `TypeVar` for unrelated things: within a signature, the same variable must resolve to one type.

## Summary

`TypeVar` and `Generic` (or 3.12's bracket syntax) describe functions and classes that work uniformly over types. `Protocol` types duck-typed interfaces structurally. `TypedDict` types JSON-shaped dicts. `ParamSpec`, `Annotated` and `Self` cover decorators, metadata and fluent APIs. Pydantic turns the same annotations into runtime parsing and validation — the foundation of FastAPI.

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
