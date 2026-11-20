# Properties, dataclasses, ABCs and composition

This lesson finishes the OOP module with four tools that make classes safer and shorter. **Properties** let you add validation or computation behind plain attribute syntax. **Dataclasses** generate `__init__`, `__repr__`, `__eq__` and ordering from field declarations. **Abstract base classes** define interfaces that subclasses must implement. And **composition** patterns tie it together into maintainable designs.

## Properties

In Java you write `getX()`/`setX()` up front "in case" you need validation later. In Python you start with a plain attribute and, if needed later, turn it into a **property** without changing any caller code.

```python-run
class Account:
    def __init__(self, owner, balance=0):
        self.owner = owner
        self.balance = balance          # goes through the setter below!

    @property
    def balance(self):
        """Current balance (read via obj.balance)."""
        return self._balance

    @balance.setter
    def balance(self, value):
        if value < 0:
            raise ValueError("balance cannot be negative")
        self._balance = value

    @property
    def is_rich(self):                  # computed, read-only
        return self._balance > 1_000_000

a = Account("Nami", 500)
a.balance += 250
print(a.balance, a.is_rich)
try:
    a.balance = -1
except ValueError as e:
    print("ValueError:", e)
try:
    a.is_rich = True
except AttributeError as e:
    print("AttributeError:", e)
```

How it works: `property` is a **descriptor** — an object stored on the class that defines `__get__` (and optionally `__set__`/`__delete__`). When you access `a.balance`, Python finds the property on the class and calls its getter instead of looking in the instance dict. Store the real value under a different name (`_balance`), or the getter will call itself forever.

Uses:

- **Validation** on assignment (as above).
- **Computed attributes** (`area` from `width * height`), always up to date.
- **Read-only attributes** (no setter).
- **Backward compatibility**: change internal representation while keeping the public attribute.

`functools.cached_property` computes once per instance and stores the result — ideal for expensive, immutable derived values.

```python-run
class Rectangle:
    def __init__(self, w, h):
        self.w, self.h = w, h
    @property
    def area(self):
        return self.w * self.h

r = Rectangle(3, 4)
r.w = 10
print(r.area)             # recomputed from current fields
```

## Dataclasses

Most classes that mainly hold data need the same boilerplate: an `__init__` that copies arguments to attributes, a `__repr__`, an `__eq__`. The `@dataclass` decorator (3.7+) generates them from **annotated class attributes**:

```python-run
from dataclasses import dataclass, field, asdict, replace

@dataclass
class Pirate:
    name: str
    bounty: int = 0
    crew: list[str] = field(default_factory=list)    # NOT crew: list = []

p = Pirate("Brook", 383_000_000)
q = Pirate("Brook", 383_000_000)
print(p, p == q, p is q)
p.crew.append("Laboon")
print(asdict(p), replace(p, bounty=0))
```

What you get by default: `__init__` (fields in order, defaults honoured), `__repr__`, `__eq__` (compares fields as a tuple). Mutable defaults must use `field(default_factory=...)` — the decorator actually raises `ValueError` if you write `crew: list = []`, protecting you from the shared-default bug.

### Options worth knowing

| Option | Effect |
|---|---|
| `order=True` | generates `<`, `<=`, `>`, `>=` comparing fields as tuples in declaration order |
| `frozen=True` | instances are immutable (assignment raises `FrozenInstanceError`) and hashable |
| `slots=True` (3.10+) | uses `__slots__` for smaller, faster instances |
| `kw_only=True` (3.10+) | all fields keyword-only in `__init__` |
| `field(compare=False)` | exclude a field from `==` and ordering |
| `field(repr=False)` | hide from `__repr__` (e.g., passwords) |
| `field(init=False)` | not an `__init__` parameter (compute in `__post_init__`) |

```python-run
from dataclasses import dataclass, field

@dataclass(order=True, frozen=True)
class Employee:
    sort_key: tuple = field(init=False, repr=False)
    dept: str
    salary: int
    name: str = field(compare=False)

    def __post_init__(self):
        # frozen: must bypass __setattr__ to set derived fields
        object.__setattr__(self, "sort_key", (self.dept, -self.salary))

staff = [Employee("eng", 120, "ana"), Employee("art", 90, "ben"), Employee("eng", 150, "cy")]
for e in sorted(staff):
    print(e)
print(hash(staff[0]) is not None, {staff[0]: "hashable because frozen"}[staff[0]])
```

The first field `sort_key` controls ordering: department ascending, then salary descending. Field order matters for `order=True` because comparison uses fields in declaration order.

`__post_init__` runs after the generated `__init__` and is the place for validation and derived fields.

### dataclass vs namedtuple vs dict vs Pydantic

| Tool | Mutable | Validation | Notes |
|---|---|---|---|
| `dict` | yes | none | flexible, no schema, typo-prone keys |
| `namedtuple` / `NamedTuple` | no | none | tuple-compatible, tiny, unpacks |
| `@dataclass` | optional | manual (`__post_init__`) | standard library, type hints, fast |
| Pydantic `BaseModel` | yes | automatic, coerces types | third-party; used by FastAPI (module 8) |

## Abstract base classes

An **abstract base class** (ABC) defines an interface: methods subclasses *must* implement. You can't instantiate a class that still has abstract methods. Goodrich (§2.4.3) uses this to build `Sequence`-like hierarchies; the `abc` module provides the machinery.

```python-run
from abc import ABC, abstractmethod
import math

class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...

    @abstractmethod
    def perimeter(self) -> float: ...

    def describe(self):                       # concrete method using the abstract ones
        return f"{type(self).__name__}: area={self.area():.2f}, perimeter={self.perimeter():.2f}"

class Circle(Shape):
    def __init__(self, r): self.r = r
    def area(self): return math.pi * self.r ** 2
    def perimeter(self): return 2 * math.pi * self.r

class Square(Shape):
    def __init__(self, s): self.s = s
    def area(self): return self.s ** 2
    # forgot perimeter!

print(Circle(1).describe())
for cls in (Shape, Square):
    try:
        cls(2)
    except TypeError as e:
        print("TypeError:", e)
```

The error arrives at **instantiation**, not at the first call — an early, clear failure.

### `collections.abc`: free methods

The standard library's ABCs (`Sequence`, `Mapping`, `MutableMapping`, `Set`, `Iterable`, `Iterator`, `Hashable`, `Callable`...) provide **mixin methods**: implement a few abstract methods and inherit the rest. Implement `__getitem__` and `__len__` on a `Sequence` subclass, and you get `__contains__`, `__iter__`, `__reversed__`, `index` and `count`:

```python-run
from collections.abc import Sequence, MutableMapping, Iterable

class Squares(Sequence):
    def __init__(self, n): self.n = n
    def __len__(self): return self.n
    def __getitem__(self, i):
        if isinstance(i, slice):
            return [self[j] for j in range(*i.indices(self.n))]
        if not 0 <= i < self.n: raise IndexError(i)
        return i * i

s = Squares(6)
print(list(s), 16 in s, s.index(9), s.count(4), list(reversed(s)), s[1:4])
print(isinstance(s, Iterable), isinstance([], Sequence), isinstance({}, MutableMapping))
```

`isinstance(x, collections.abc.Iterable)` is the right way to ask "is this iterable?" — ABCs can recognise classes that never inherited from them (via `__subclasshook__` or `register`).

### ABCs vs Protocols

ABCs are **nominal**: a class must inherit from (or be registered with) the ABC. `typing.Protocol` (module 8) is **structural**: any class with the right methods matches, checked statically by mypy. Use ABCs when you want runtime enforcement and shared implementation; Protocols when you just want to describe a shape.

## Composition patterns

Composition — building objects out of other objects — is usually preferable to deep inheritance (see lesson 13). A few patterns appear constantly:

**Delegation**: forward calls to a component.

```python-run
class Stack:
    """A stack that exposes only stack operations, built on a list."""
    def __init__(self):
        self._items = []                # has-a list, rather than is-a list
    def push(self, x): self._items.append(x)
    def pop(self): return self._items.pop()
    def peek(self): return self._items[-1]
    def __len__(self): return len(self._items)

s = Stack(); s.push(1); s.push(2)
print(s.pop(), len(s), hasattr(s, "insert"))     # list's insert isn't exposed
```

Subclassing `list` instead would expose `insert`, `sort`, slicing and everything else, breaking the stack's guarantees. Goodrich calls this the **adapter pattern**: adapt an existing class's interface to a new one.

**Strategy**: pass in a component that implements one varying behaviour.

```python-run
from dataclasses import dataclass
from typing import Callable

@dataclass
class Checkout:
    pricing: Callable[[float], float]          # the strategy
    def total(self, amounts):
        return round(self.pricing(sum(amounts)), 2)

regular = Checkout(lambda t: t)
sale = Checkout(lambda t: t * 0.8)
bulk = Checkout(lambda t: t - 10 if t > 100 else t)
items = [40, 35, 50]
print(regular.total(items), sale.total(items), bulk.total(items))
```

In Python a strategy can be just a function — first-class functions make many classical patterns one-liners.

**Dependency injection**: give an object its collaborators instead of letting it create them. This is how FastAPI's `Depends` works, and it makes testing easy — inject a fake.

```python-run
class EmailSender:
    def send(self, to, msg): raise NotImplementedError

class FakeSender(EmailSender):
    def __init__(self): self.sent = []
    def send(self, to, msg): self.sent.append((to, msg))

class SignupService:
    def __init__(self, sender: EmailSender):
        self.sender = sender
    def register(self, email):
        self.sender.send(email, "welcome aboard!")

fake = FakeSender()
SignupService(fake).register("sanji@baratie.sea")
print(fake.sent)
```

## Worked example: a validated, ordered inventory item

```python-run
from dataclasses import dataclass, field

@dataclass(order=True)
class Item:
    price: float
    name: str = field(compare=False)
    qty: int = field(default=0, compare=False)

    def __post_init__(self):
        if self.price < 0:
            raise ValueError(f"price must be >= 0, got {self.price}")
        self.name = self.name.strip().title()

    @property
    def value(self):
        return self.price * self.qty

stock = [Item(3.5, " meat ", 10), Item(1.25, "cola", 40), Item(9.0, "sake ", 2)]
print(sorted(stock)[0], max(stock).name, sum(i.value for i in stock))
try:
    Item(-1, "bad")
except ValueError as e:
    print(e)
```

> [!INTERVIEW]
> Expect: "When would you use a property?" (validation/computed/read-only attributes without changing the public API), "What does @dataclass generate?" (`__init__`, `__repr__`, `__eq__`, optionally ordering, hashing, slots), "Why `field(default_factory=list)`?" (avoid a shared mutable default), "ABC vs Protocol?" (nominal + runtime enforcement vs structural + static checking), "Composition vs inheritance?" (has-a vs is-a; prefer composition).

## Under the hood: descriptors, the machinery behind properties

A **descriptor** is any object stored on a class that defines `__get__`, `__set__` or `__delete__`. When attribute access finds one on the class, Python calls those methods instead of reading or writing the instance dict. `property`, methods, `classmethod`, `staticmethod`, `functools.cached_property` and ORM/Pydantic fields are all descriptors. Writing one yourself turns a validation rule into a reusable component — where a property would have to be repeated for every attribute:

```python-run
class Positive:
    """Reusable validated attribute (a data descriptor)."""
    def __set_name__(self, owner, name):       # called once, when the class is created
        self.name = name
        self.storage = "_" + name
    def __get__(self, instance, owner=None):
        if instance is None:
            return self                         # accessed on the class itself
        return getattr(instance, self.storage)
    def __set__(self, instance, value):
        if value <= 0:
            raise ValueError(f"{self.name} must be positive, got {value}")
        setattr(instance, self.storage, value)

class Product:
    price = Positive()
    qty = Positive()
    def __init__(self, price, qty):
        self.price, self.qty = price, qty       # both assignments run Positive.__set__

p = Product(9.5, 3)
p.qty = 10
print(p.price * p.qty, vars(p))
for bad in (lambda: Product(-1, 1), lambda: setattr(p, "qty", 0)):
    try:
        bad()
    except ValueError as e:
        print("ValueError:", e)
print(type(Product.price).__name__)
```

`property` is simply a ready-made descriptor whose `__get__`/`__set__` call the functions you decorated. Because it defines `__set__`, it is a **data descriptor** and takes priority over the instance dict — which is why a property cannot be bypassed by assigning to the same name.

## What `@dataclass` actually generates

There is no runtime magic: the decorator reads `__annotations__`, writes the source code of the methods, `exec`s it, and attaches the results to your class. You can inspect the outcome:

```python-run
from dataclasses import dataclass, fields, field, asdict, astuple
import inspect

@dataclass
class Item:
    name: str
    price: float = 0.0
    tags: list = field(default_factory=list, repr=False)

print(inspect.signature(Item.__init__))
print([(f.name, f.type.__name__, f.default is not f.default_factory) for f in fields(Item)])
print(sorted(n for n in vars(Item) if n.startswith("__") and n in
             ("__init__", "__repr__", "__eq__", "__hash__", "__match_args__")))
i = Item("cola", 1.5)
print(i, asdict(i), astuple(i), Item.__hash__)
```

Note the last value: a plain (`eq=True`, mutable) dataclass sets `__hash__` to `None` — the "defining `__eq__` makes you unhashable" rule from the data-model lesson. `frozen=True` restores hashing; `unsafe_hash=True` forces it at your own risk.

Two more behaviours that surprise people:

- **Fields without defaults cannot follow fields with defaults** (the generated `__init__` would be invalid). This also bites in inheritance, when a subclass adds a required field after a parent's optional one; `kw_only=True` solves it.
- **Only annotated names are fields.** `count = 0` without an annotation is an ordinary class attribute, silently absent from `__init__`, `__repr__` and `__eq__`.

```python-run
from dataclasses import dataclass

@dataclass
class Settings:
    host: str = "localhost"
    port = 8000                      # no annotation: NOT a field

s = Settings()
print(s, Settings("h") == Settings("h"), s.port)
try:
    Settings("h", 9000)
except TypeError as e:
    print("TypeError:", e)

@dataclass(kw_only=True)
class Base:
    debug: bool = False
@dataclass(kw_only=True)
class Service(Base):
    name: str                        # required field after an optional one: fine with kw_only
print(Service(name="api"))
```

## Debugging checklist

- `RecursionError` on attribute access: the property reads or writes its own public name instead of the underscore-prefixed storage.
- `AttributeError: can't set attribute` / `property ... has no setter`: you assigned to a read-only property, perhaps in `__init__`.
- `ValueError: mutable default <class 'list'> for field x is not allowed`: use `field(default_factory=list)`.
- `FrozenInstanceError` in `__post_init__`: use `object.__setattr__(self, name, value)`.
- `TypeError: Can't instantiate abstract class X without an implementation for abstract method 'y'`: implement `y` — or you misspelled it. `X.__abstractmethods__` lists what is still missing.
- Sorting dataclasses raises `TypeError: '<' not supported`: you forgot `order=True`, or a compared field holds mixed/uncomparable values.

## Pitfalls recap

- A property getter that reads `self.balance` instead of `self._balance` → infinite recursion.
- Mutable dataclass defaults without `default_factory`.
- `frozen=True` dataclasses: set derived fields in `__post_init__` with `object.__setattr__`.
- `order=True` compares in field declaration order — put the sort key first or use `compare=False`.
- Forgetting an abstract method → `TypeError` at instantiation.
- Subclassing a concrete container to "reuse" it when you only need some of its behaviour — compose instead.

## Summary

Properties put logic behind attribute syntax. Dataclasses generate the boilerplate of data-holding classes, with options for ordering, immutability and slots. ABCs define enforceable interfaces and, via `collections.abc`, give you free mixin methods. Composition, delegation, strategies and dependency injection keep designs flexible and testable.

```quiz
[
  {"q": "What does a @property let you do?", "options": ["Make attributes private", "Run code on attribute access/assignment while keeping obj.attr syntax", "Create class attributes", "Speed up attribute access"], "answer": 1,
   "explain": "A property is a descriptor whose getter/setter run when the attribute is read or written."},
  {"q": "Why is `tags: list = []` rejected in a dataclass?", "options": ["Lists can't be annotated", "It would be a shared mutable default; dataclasses require field(default_factory=list)", "Dataclasses can't have lists", "It's allowed"], "answer": 1,
   "explain": "The decorator raises ValueError for list/dict/set defaults to prevent the shared-default bug."},
  {"q": "With @dataclass(order=True), how are instances compared?", "options": ["By id", "As tuples of fields in declaration order (excluding compare=False fields)", "By the first field only", "Alphabetically by repr"], "answer": 1,
   "explain": "Generated comparison methods compare field tuples in declaration order."},
  {"q": "When does instantiating a subclass that misses an @abstractmethod fail?", "options": ["Never", "When the missing method is called", "At instantiation, with TypeError", "At import"], "answer": 2,
   "explain": "ABCMeta refuses to create instances of classes with unimplemented abstract methods."},
  {"q": "Which makes a dataclass hashable and immutable?", "options": ["order=True", "frozen=True", "slots=True", "eq=False"], "answer": 1,
   "explain": "frozen=True blocks assignment and, with eq=True, generates __hash__ from the fields."},
  {"q": "Subclassing collections.abc.Sequence and implementing __getitem__ and __len__ gives you:", "options": ["Nothing else", "__contains__, __iter__, __reversed__, index and count", "append and pop", "Sorting"], "answer": 1,
   "explain": "Sequence provides those mixin methods built on the two abstract ones."},
  {"q": "A Stack class that stores a list in self._items rather than subclassing list is using:", "options": ["Multiple inheritance", "Composition (adapter pattern)", "A metaclass", "A mixin"], "answer": 1,
   "explain": "It wraps a list and exposes only stack operations."}
]
```

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, §2.1.3 (Design Patterns), §2.4.3 (Abstract Base Classes); Python docs, *Library Reference* `dataclasses`, `abc`, `collections.abc` and built-in `property`, and the *Descriptor HowTo Guide*.
