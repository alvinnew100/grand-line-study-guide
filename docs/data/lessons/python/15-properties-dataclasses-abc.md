# Properties, dataclasses, ABCs and composition

> **Before this lesson:** you need classes and attribute lookup from [Classes and instances](#/lesson/python/py-classes), inheritance and the "is-a versus has-a" discussion from [Inheritance, MRO and super](#/lesson/python/py-inheritance), special methods from [The data model: dunder methods](#/lesson/python/py-data-model), and decorators from [Decorators and functools](#/lesson/python/py-decorators).

## In plain words

This lesson finishes the object-oriented module with four tools that make classes safer to use and shorter to write.

- A **property** is an attribute with a guard at the door. From the outside it looks like ordinary data (`account.balance`), but reading or changing it quietly runs a small function of yours, which can check the new value or work the answer out on the spot. Think of a thermostat dial: you turn a dial, and behind the panel something checks that you did not ask for 90 degrees.
- A **dataclass** is a class that mainly holds data, for which Python writes the repetitive methods for you. You list the fields, as on a blank form, and Python produces the code that fills the form in, prints it and compares two forms.
- An **abstract base class** is a contract. It lists methods that every class of a family must provide, in the way a job advert lists required skills. A class that leaves one out cannot be used to create objects.
- **Composition** means building an object out of other objects, as a car is built from an engine and wheels, as an alternative to inheriting from them.

Why this matters for a job: properties and dataclasses are in nearly every modern Python codebase, so you must be able to read them. Interviewers ask "when would you use a property?", "what does `@dataclass` generate?" and "composition or inheritance?". And the last section's patterns, especially handing an object its helpers from outside, are what make code testable.

## Properties

In languages such as Java it is customary to hide every piece of data behind a pair of methods, `getX()` and `setX()`, from the first day, in case a check is needed later. Python does it the other way round. You begin with a plain attribute, and if a check or calculation becomes necessary later, you turn the attribute into a **property**. Code that uses the class does not change at all: it still writes `a.balance`.

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

**Reading this code line by line**

- `@property` above a method named `balance` turns it into the **getter**: reading `a.balance` now calls this method. There are no parentheses at the place of use.
- `@balance.setter` above a second method of the same name registers the **setter**: an assignment `a.balance = value` calls it with the new value. Here it rejects negative numbers.
- The real number is kept in a different attribute, `_balance`. That name must differ from the property's name; a getter that returned `self.balance` would call itself for ever.
- Inside `__init__`, the line `self.balance = balance` already goes through the setter, so even the starting value is checked.
- `is_rich` has a getter and no setter. It is computed from other data and is **read-only**.

`a.balance += 250` reads through the getter, adds, and writes through the setter; the first print shows `750 False`. Assigning −1 raises the setter's `ValueError`. Assigning to `is_rich` raises `AttributeError`, because there is no setter.

How it works: `property` is a **descriptor**, an object stored on the class that defines `__get__` (and optionally `__set__` and `__delete__`). When you read `a.balance`, Python finds the property on the class and calls its getter; it does not look in the instance's own dictionary first. The end of this lesson shows how to write a descriptor yourself.

What properties are used for:

- **Validation**: checking a value when it is assigned, as above.
- **Computed attributes**, such as an `area` worked out from `width * height`, which are always up to date.
- **Read-only attributes**: a getter without a setter.
- **Backward compatibility**: changing how the data is stored inside while the public attribute stays the same.

The second demo shows a computed attribute: after `r.w = 10`, `r.area` is 40, because the getter multiplies the current values each time it is read. For a result that is expensive to compute and never changes, `functools.cached_property` computes it once per instance and stores it.

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

Most classes that mainly hold data need the same repetitive code (**boilerplate**): an `__init__` that copies each argument into an attribute, a `__repr__`, an `__eq__`. The `@dataclass` decorator (Python 3.7+) writes these for you. You declare each field as a class-level name followed by a colon and a type, for example `name: str`. That colon-and-type note is an **annotation**; Python does not enforce the type (the typing lessons come later), but the dataclass decorator reads the annotations to learn what the fields are.

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

- The three annotated lines declare three fields. `bounty` has a default of 0.
- `crew` should default to an empty list. Writing `crew: list = []` would share one list among all instances, the mutable-default bug again, so dataclasses require `field(default_factory=list)`: "call `list()` to make a fresh default for each new instance".
- `Pirate("Brook", 383_000_000)` works although no `__init__` was written. Printing shows a generated `__repr__`, and `p == q` is `True` because the generated `__eq__` compares field by field. `p is q` is `False`: they are two objects.
- `asdict(p)` converts an instance to a dictionary, and `replace(p, bounty=0)` returns a copy with one field changed.

What you get without asking: `__init__` (parameters in field order, with the defaults), `__repr__`, and `__eq__` (compares the fields as a tuple). If you do write `crew: list = []`, the decorator raises `ValueError` when the class is defined, so the shared-default bug cannot slip in.

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

This class asks for ordering and immutability and customises three fields:

- `frozen=True` makes instances immutable, and therefore hashable. The last line uses an employee as a dictionary key.
- `order=True` generates `<` and friends, which compare the fields in the order they are declared.
- `sort_key` is declared first so that it decides the order. `init=False` keeps it out of the generated `__init__`, and `repr=False` out of the printed form.
- `__post_init__` runs right after the generated `__init__` and computes `sort_key` as (department, minus the salary). Because the instance is frozen, a normal assignment is forbidden there, so it calls `object.__setattr__` directly.
- `name` has `compare=False`: it plays no part in equality or ordering.

The sorted output lists `art` before `eng`, and within `eng` the higher salary first (minus 150 is smaller than minus 120). Field order matters with `order=True`, because the comparison goes through the fields in declaration order.

`__post_init__` is the place for validation and for fields derived from other fields.

### dataclass vs namedtuple vs dict vs Pydantic

| Tool | Mutable | Validation | Notes |
|---|---|---|---|
| `dict` | yes | none | flexible, no schema, typo-prone keys |
| `namedtuple` / `NamedTuple` | no | none | tuple-compatible, tiny, unpacks |
| `@dataclass` | optional | manual (`__post_init__`) | standard library, type hints, fast |
| Pydantic `BaseModel` | yes | automatic, coerces types | a third-party library (not part of Python itself); used by the web framework FastAPI and introduced in the typing module |

## Abstract base classes

An **abstract base class** (ABC) defines an interface: a list of methods that subclasses *must* provide. A method marked `@abstractmethod` has a name and no real body. A class that still has abstract methods cannot be instantiated. The standard `abc` module supplies the machinery.

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

`Shape` declares two abstract methods (the body `...` is a placeholder) and one ordinary method, `describe`, which is written in terms of the abstract ones. An ordinary, fully written method is called a **concrete** method. `Circle` provides both abstract methods, so it can be created, and `describe` works for it. `Shape` itself cannot be created, and neither can `Square`, whose author forgot `perimeter`: both attempts raise `TypeError`, and for `Square` the message names the missing method.

Notice *when* the error comes: at the moment an object is created, not weeks later when some rarely used code path finally calls the missing method. An early, clear failure is the whole point.

### `collections.abc`: free methods

The standard library ships ABCs for the common kinds of container: `Sequence`, `Mapping`, `MutableMapping`, `Set`, `Iterable`, `Iterator`, `Hashable`, `Callable` and more. They do more than check. Each one also contains ready-made methods written in terms of a few abstract ones (these are called **mixin methods**). Subclass `Sequence`, provide `__getitem__` and `__len__`, and you inherit `__contains__`, `__iter__`, `__reversed__`, `index` and `count`:

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

`Squares(6)` behaves as the sequence 0, 1, 4, 9, 16, 25 without storing it. Only two methods were written, yet `in`, `index`, `count` and `reversed` all work.

`isinstance(x, collections.abc.Iterable)` is the proper way to ask "can this be looped over?". An ABC can recognise classes that never inherited from it, either by checking for the right methods or because the class was registered with it; that is why a plain list counts as a `Sequence` on the last line.

### ABCs vs Protocols

ABCs are **nominal**: a class belongs because it *names* the ABC as a base (or is registered with it). `typing.Protocol`, covered in the typing module, is **structural**: any class with the right methods matches, and the match is checked by a type-checking tool before the program runs. Use an ABC when you want the check enforced at run time and want to share code; use a Protocol when you only want to describe what an object must be able to do.

## Composition patterns

Composition, building objects out of other objects, is usually preferable to a deep family tree of classes (see the inheritance lesson). Three patterns come up constantly.

**Delegation**: keep a component and pass calls on to it.

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

This `Stack` *has* a list; it is not one. Each method passes its work to the inner list. The last value printed is `False`: the stack has no `insert`. Had the class inherited from `list`, it would also offer `insert`, `sort`, slicing and everything else, and nothing would protect the rule that a stack is only touched at the top. Wrapping an existing class to give it a different interface is known as the **adapter pattern**.

**Strategy**: hand the object a component that carries out the one part of its behaviour that varies.

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

`Checkout` knows how to add up amounts; how the total is priced is supplied from outside as a function. The annotation `Callable[[float], float]` says "something callable that takes a float and returns a float". The three checkouts print `125 100.0 115`: no discount, 20% off, and 10 off above 100. In many languages the strategy would have to be an object of a special class; in Python a plain function is enough, because functions are first-class values.

**Dependency injection**: give an object the helpers it depends on from outside; do not let it create them itself. This is how FastAPI's `Depends` works, and it makes testing easy, because a test can hand in a harmless stand-in (a **fake**).

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

`SignupService` needs something that can send email, and receives it as a constructor argument. In production that would be a real mail sender. The test passes a `FakeSender` that only records what it was asked to send, so the behaviour can be checked without any email leaving the machine: the list shows one welcome message.

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

This example combines the tools. `order=True` with `price` as the first (and only compared) field makes items sort by price. `__post_init__` validates the price and tidies the name. `value` is a computed property. The output shows the cheapest item, the name of the dearest, and the total stock value, followed by the error message for a negative price.

> [!INTERVIEW]
> Expect: "When would you use a property?" (validation, computed or read-only attributes, without changing the public interface). "What does `@dataclass` generate?" (`__init__`, `__repr__`, `__eq__`; optionally ordering, hashing, slots). "Why `field(default_factory=list)`?" (to avoid a shared mutable default). "ABC or Protocol?" (nominal with run-time enforcement, versus structural with static checking). "Composition or inheritance?" (has-a versus is-a; prefer composition).

## Under the hood: descriptors, the machinery behind properties

A **descriptor** is any object stored on a class that defines `__get__`, `__set__` or `__delete__`. When attribute access finds such an object on the class, Python calls those methods; it does not read or write the instance's dictionary directly. `property`, ordinary methods, `classmethod`, `staticmethod`, `functools.cached_property` and the field objects of database and validation libraries are all descriptors. Writing one yourself turns a rule into a reusable part, where a property would have to be written out again for every attribute:

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

- `Positive` is the descriptor class. One instance of it is created for each attribute that should be positive (`price = Positive()`, `qty = Positive()`).
- `__set_name__` is called once for each of those, when the `Product` class is created, and tells the descriptor which name it was given. It remembers the name and chooses a private storage name with an underscore.
- `__get__` runs when the attribute is read. Reached through the class (`Product.price`), it returns the descriptor itself; reached through an instance, it returns the stored value.
- `__set__` runs on every assignment, checks the value and stores it.

`Product(9.5, 3)` assigns both attributes through `__set__`. The printed dictionary shows the real storage names, `_price` and `_qty`. Both bad attempts are rejected with a message that names the attribute.

`property` is a ready-made descriptor whose `__get__` and `__set__` call the functions you decorated. Because it defines `__set__` it is a **data descriptor**, and data descriptors take priority over the instance's dictionary. That is why a property cannot be bypassed by assigning to the same name.

## What `@dataclass` actually generates

Nothing mysterious happens at run time. The decorator reads the class's annotations, writes the source code of the methods as text, runs that text to create the functions, and attaches them to your class. You can inspect the outcome:

```python-run
from dataclasses import dataclass, fields, field, asdict, astuple
import inspect

@dataclass
class Item:
    name: str
    price: float = 0.0
    tags: list = field(default_factory=list, repr=False)

print(inspect.signature(Item.__init__))
print([(f.name, f.type.__name__, f.compare, f.repr) for f in fields(Item)])   # name, type, in ==?, in repr?
print(sorted(n for n in vars(Item) if n.startswith("__") and n in
             ("__init__", "__repr__", "__eq__", "__hash__", "__match_args__")))
i = Item("cola", 1.5)
print(i, asdict(i), astuple(i), Item.__hash__)
```

The first line shows the generated signature of `__init__`; the second lists each field with its type and whether it takes part in `==` and in the printed form; the third lists the special methods the decorator added.

Note the last value printed, `None`: an ordinary dataclass (with `__eq__`, and mutable) has its `__hash__` set to `None`. This is the "defining `__eq__` makes you unhashable" rule from the data model lesson. `frozen=True` brings hashing back; `unsafe_hash=True` forces it at your own risk.

Two more behaviours that surprise people:

- **A field without a default cannot follow a field with one**, because the generated `__init__` would be invalid. This also strikes with inheritance, when a subclass adds a required field after a parent's optional one; `kw_only=True` solves it.
- **Only annotated names are fields.** `count = 0` without an annotation is an ordinary class attribute, silently missing from `__init__`, `__repr__` and `__eq__`.

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

`port = 8000` has no annotation, so `Settings` has a single field. The printed form shows only `host`, and passing a second argument fails with `TypeError: ... takes from 1 to 2 positional arguments but 3 were given`. In the second half, `kw_only=True` allows `Service` to add a required field after the parent's optional one.

## Debugging checklist

- `RecursionError` on attribute access: the property reads or writes its own public name where it should use the underscore storage name.
- `AttributeError: can't set attribute` or `property ... has no setter`: an assignment to a read-only property, perhaps inside `__init__`.
- `ValueError: mutable default <class 'list'> for field x is not allowed`: use `field(default_factory=list)`.
- `FrozenInstanceError` in `__post_init__`: use `object.__setattr__(self, name, value)`.
- `TypeError: Can't instantiate abstract class X without an implementation for abstract method 'y'`: implement `y`, or check its spelling. `X.__abstractmethods__` lists what is still missing.
- Sorting dataclasses raises `TypeError: '<' not supported`: `order=True` is missing, or a compared field holds values that cannot be compared with each other.

## Pitfalls recap

- A property getter that reads `self.balance` where it should read `self._balance`, causing endless recursion.
- Mutable dataclass defaults without `default_factory`.
- In a `frozen=True` dataclass, derived fields must be set in `__post_init__` with `object.__setattr__`.
- `order=True` compares in field declaration order; put the sort key first or mark other fields `compare=False`.
- A forgotten abstract method gives `TypeError` when an object is created.
- Subclassing a concrete container to "reuse" it when only part of its behaviour is wanted; compose instead.

## Summary

Properties put logic behind attribute syntax. Dataclasses generate the boilerplate of data-holding classes, with options for ordering, immutability and slots. ABCs define interfaces that are enforced and, through `collections.abc`, supply ready-made mixin methods. Composition, delegation, strategies and dependency injection keep a design flexible and testable.

## Glossary

- **Property** - an attribute whose reading and writing run methods of the class.
- **Getter / setter** - the method that runs when a property is read / assigned.
- **Read-only attribute** - a property with no setter.
- **Validation** - checking that a value is acceptable before storing it.
- **Boilerplate** - repetitive code that has to be written but says nothing new.
- **Dataclass** - a class decorated with `@dataclass`, whose `__init__`, `__repr__` and `__eq__` are generated from its fields.
- **Field / annotation** - one declared piece of data of a dataclass / the `name: type` note that declares it.
- **`default_factory`** - a function called to produce a fresh default value for each instance.
- **`__post_init__`** - a method run right after a dataclass's generated `__init__`.
- **Frozen** - immutable after creation; a frozen dataclass is hashable.
- **Abstract base class (ABC)** - a class that declares methods its subclasses must implement and cannot itself be instantiated.
- **Abstract / concrete method** - declared without an implementation / fully implemented.
- **Mixin method** - a ready-made method an ABC provides on top of the abstract ones.
- **Nominal / structural typing** - matching by declared inheritance / by having the right methods.
- **Delegation** - passing a call on to a component object.
- **Adapter pattern** - wrapping a class to present a different interface.
- **Strategy pattern** - supplying a varying piece of behaviour as a component, often a function.
- **Dependency injection** - handing an object its helpers from outside.
- **Fake** - a simple stand-in used in tests in place of a real component.
- **Descriptor / data descriptor** - an object on a class with `__get__` / one that also has `__set__`.

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
