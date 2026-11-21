# Pydantic models, types and Field

> **Before this lesson:** you should have seen a Pydantic model used as a request body and as a
> response model in [lesson 5](#/lesson/fastapi/body-responses), and know what a type hint is
> ([lesson 4](#/lesson/fastapi/first-app)). In Python you need classes at the level of "a class lists
> some fields", dictionaries and `try` / `except`.

## In plain words

Data that arrives from outside your program cannot be trusted to have the right shape. A client may
send text where a number belongs, leave a field out, or misspell a name. **Pydantic** is the Python
library that stands at the door and checks. You describe the shape you expect by writing a small
class with type hints, and Pydantic compares every incoming piece of data against that description,
converts what can sensibly be converted, and reports everything that is wrong.

An everyday picture: the security check at an airport. Every bag goes through the same scanner
before it is allowed into the building. Bags that pass are known to be safe from then on, so nobody
inside has to check again. Pydantic is that scanner for data, and a value that has passed through it
is known to have the right types everywhere after.

FastAPI does not check data itself; it hands the job to Pydantic. Every `422` response you have seen,
every field filtered out of a response and every description on the `/docs` page was produced by
Pydantic. This module studies Pydantic by itself. Nothing here needs a web server, so every example
runs live in your browser.

Why this matters for a job: models are where most of the daily work in a FastAPI codebase happens,
and "why does FastAPI use Pydantic?" and "what changed in version 2?" are common interview questions.
Version 2 (2023) rewrote the checking engine in the fast compiled language Rust (the engine is called
`pydantic-core`), which made validation roughly 5 to 50 times faster than version 1, and it renamed
several methods. Old tutorials still show the old names; a table below translates them.

## Why type hints need a runtime library

Lubanovic's chapter 5 begins with an observation that surprises many newcomers. Python *ignores* type
hints while a program runs:

```python-run
def double(n: int) -> int:
    return n * 2

print(double("ha"))      # no error: hints are documentation for tools, not runtime checks
```

The hint says `n` should be an `int`, yet calling `double("ha")` raises no error. Python multiplies
the text by two and prints `haha`. **Runtime** means "while the program is running", and at runtime a
hint is only a comment with nicer syntax.

Tools called static checkers (mypy, pyright) read hints *before* the program runs and catch some
mistakes in your own code. They cannot inspect data that arrives from the network later. That is the
gap Pydantic fills: it **reads the same hints while the program runs** and enforces them on incoming
data.

The book walks through the other ways Python can group related values (tuples, dictionaries,
`namedtuple`, dataclasses, the `attrs` library) and settles on Pydantic because it alone combines a
class-style definition with checking, conversion, and translation to and from JSON.

## A first model

```python-run
from datetime import date
from pydantic import BaseModel, ValidationError

class Creature(BaseModel):          # the book's running example: cryptids!
    name: str
    country: str
    area: str | None = None
    description: str = ""
    aka: list[str] = []
    first_seen: date | None = None

thing = Creature(name="yeti", country="CN", aka=["Abominable Snowman"], first_seen="1951-11-08")
print(thing)
print(thing.first_seen, type(thing.first_seen).__name__)   # string was parsed into a date
print(thing.model_dump())

try:
    Creature(name="bigfoot")               # country missing
except ValidationError as e:
    print(e)
```

Reading the code:

- `class Creature(BaseModel):` defines a model. (The book's running example is a catalogue of
  legendary creatures.) Each line below it declares one **field**: a name, a type and possibly a
  default.
- `name: str` and `country: str` have no default, so they are required.
- `area: str | None = None` may be text or nothing, and is nothing unless given.
- `description: str = ""` and `aka: list[str] = []` default to empty text and an empty list.
- `first_seen: date | None = None` is an optional calendar date.
- `Creature(name="yeti", ...)` creates an instance. Note that `first_seen` is given as the *text*
  `"1951-11-08"`.

The output shows four things. The printed object lists every field, with `first_seen` now a real
`datetime.date(1951, 11, 8)`. The second line confirms it: the text was parsed into a `date`.
`model_dump()` gives the same data as a plain dictionary. Finally, creating a creature without a
`country` raises `ValidationError`, whose message says `country` and `Field required`.

The behaviours to remember:

- A field without a default is **required**; a field with one is optional.
- Values are **converted** when the meaning is unambiguous (`"1951-11-08"` to a date, `"5"` to `5`).
- Errors are collected for **all** fields in one `ValidationError`; checking does not stop at the
  first problem.
- A mutable default such as `[]` is safe. Pydantic makes a fresh copy for each instance, which plain
  Python function defaults do not.

## Lax versus strict mode

By default Pydantic is **lax**: it converts inputs that are compatible with the declared type. The
technical word for such conversion is **coercion**. It is worth seeing exactly where the line is
drawn:

```python-run
from pydantic import BaseModel, ValidationError, ConfigDict

class Lax(BaseModel):
    i: int
    f: float
    b: bool
    s: str

print(Lax(i="42", f="3.5", b="yes", s="hello"))
for bad in [{"i": "4.5", "f": 1, "b": True, "s": "x"},       # "4.5" is not an integer string
            {"i": 4.0, "f": 1, "b": "maybe", "s": "x"},      # "maybe" is not a bool
            {"i": 1, "f": 1, "b": True, "s": 123}]:          # ints are NOT coerced to str
    try:
        Lax(**bad)
    except ValidationError as e:
        print([(err["loc"], err["type"]) for err in e.errors()])

class Strict(BaseModel):
    model_config = ConfigDict(strict=True)
    i: int

try:
    Strict(i="42")
except ValidationError as e:
    print("strict:", e.errors()[0]["type"])
```

The first `print` shows `i=42 f=3.5 b=True s='hello'`: text became an integer, a float and a boolean.
Then three bad inputs are tried, and for each the code prints the field and the error type:

- `"4.5"` for an `int` fails with `int_parsing`. Turning 4.5 into a whole number would lose
  information, so Pydantic refuses.
- `"maybe"` for a `bool` fails with `bool_parsing`. In the same input, `4.0` for the `int` was
  accepted without complaint, because 4.0 is exactly 4.
- `123` for a `str` fails with `string_type`. Numbers are *not* silently turned into text.

The last part defines a model in **strict** mode, where no conversion is done at all: the text `"42"`
is rejected for an `int` field with the error type `int_type`.

Strictness can be chosen for a whole model (`ConfigDict(strict=True)`), for one field
(`Field(strict=True)`) or for one call (`model_validate(data, strict=True)`). When the input is JSON
text, strict mode still accepts the forms JSON has no alternative for, such as a date written as an
ISO string.

## The type vocabulary

Pydantic understands Python's standard types and adds many of its own:

| Category | Examples |
|---|---|
| Built-in | `int`, `float`, `str`, `bool`, `bytes`, `list[T]`, `dict[K, V]`, `set[T]`, `tuple[int, str]` |
| "Or" types (unions) | `str \| None`, `int \| str` |
| Fixed choices | `Literal["asc", "desc"]`, `Enum` subclasses |
| Time | `datetime`, `date`, `time`, `timedelta` (ISO 8601 text is parsed) |
| IDs and exact numbers | `UUID`, `Decimal` |
| Pydantic's own | `EmailStr` (needs the `email-validator` package), `HttpUrl`, `AnyUrl`, `SecretStr`, `PositiveInt`, `IPvAnyAddress`, `Json[T]` |
| Nested | other `BaseModel` classes, to any depth |
| Tagged unions | `Annotated[Cat \| Dog, Field(discriminator="kind")]` (next lesson) |

In the table `T`, `K` and `V` stand for "any type you choose": `list[int]` is a list of integers.
A **union**, written with `|`, means "one of these types".

`SecretStr` deserves a mention. It hides its value whenever it is printed or logged (it shows as
`SecretStr('**********')`), so use it for passwords and API keys.

## `Field`: constraints and metadata

A type says what *kind* of value is allowed. A **constraint** narrows it further: "a number, and at
least 18". `Field` attaches constraints and documentation to a field:

```python-run
from pydantic import BaseModel, Field, ValidationError

class Explorer(BaseModel):
    name: str = Field(min_length=2, max_length=50, description="Full name")
    country: str = Field(pattern=r"^[A-Z]{2}$", examples=["US", "FR"])
    age: int = Field(ge=18, le=120)
    rating: float = Field(default=0.0, ge=0, le=5)
    tags: list[str] = Field(default_factory=list, max_length=10)

print(Explorer(name="Claude Hande", country="FR", age=40))
try:
    Explorer(name="X", country="france", age=12, rating=7)
except ValidationError as e:
    for err in e.errors():
        print(err["loc"], err["type"], "-", err["msg"])
```

- `name` must be 2 to 50 characters long.
- `country` must match the regular expression `^[A-Z]{2}$`, which means "exactly two capital letters".
- `age` must be from 18 to 120 (`ge` is "greater than or equal", `le` is "less than or equal").
- `rating` defaults to 0.0 and must be from 0 to 5.
- `tags` defaults to a new empty list (`default_factory=list` means "call `list()` to make the
  default") and may hold at most 10 entries.

The valid explorer prints normally. The invalid one produces four errors, one per broken rule:
`string_too_short` for the name, `string_pattern_mismatch` for the country,
`greater_than_equal` for the age and `less_than_equal` for the rating, each with a readable message.

The constraint vocabulary: for numbers `gt`, `ge`, `lt`, `le`, `multiple_of`; for text `min_length`,
`max_length`, `pattern`; for lists and other collections `min_length`, `max_length`; for decimals
`max_digits`, `decimal_places`. Documentation options: `title`, `description`, `examples`, `alias`,
`exclude`, `deprecated`. Defaults: `default=` for a fixed value, or `default_factory=` for a function
that produces one (needed for lists, dictionaries and timestamps).

Lubanovic's "Validate Values" section does the same with older helper functions (`constr`, `conint`)
and `Field(..., min_length=2)`. In version 2 the `Field` and `Annotated` style shown here is preferred.

### `Annotated` constraints: reusable types

With `Annotated` you can attach constraints to a type once, give the result a name, and reuse it. It
is the same mechanism FastAPI uses for `Query()` and `Path()`:

```python-run
from typing import Annotated
from pydantic import BaseModel, Field, TypeAdapter, ValidationError

CountryCode = Annotated[str, Field(pattern=r"^[A-Z]{2}$")]
Probability = Annotated[float, Field(ge=0.0, le=1.0)]

class Detection(BaseModel):
    origin: CountryCode
    confidence: Probability
    class_scores: dict[str, Probability]

print(Detection(origin="US", confidence=0.93, class_scores={"cat": 0.93, "dog": 0.07}))

# TypeAdapter validates any type, not just models - handy for lists of models, unions, etc.
ta = TypeAdapter(list[Probability])
print(ta.validate_python(["0.5", 1]))
try:
    ta.validate_python([0.2, 1.5])
except ValidationError as e:
    print(e.errors()[0]["loc"], e.errors()[0]["type"])
```

`CountryCode` is now a name for "text made of two capital letters", and `Probability` for "a float
from 0 to 1". The model `Detection` uses them like any other type, including inside a dictionary:
every value of `class_scores` must be a probability.

The second half introduces `TypeAdapter`. A model checks a group of named fields; a `TypeAdapter`
checks *any* type without a model class. Here it validates "a list of probabilities".
`["0.5", 1]` is accepted and comes back as `[0.5, 1.0]`. `[0.2, 1.5]` is rejected, and the printed
location `(1,)` points at the element at position 1 (the second one), with the type `less_than_equal`.

## Aliases: Python names vs wire names

Python style writes field names as `customer_name`. JSON produced by JavaScript programs usually
writes `customerName`, and sometimes a name is not a legal Python name at all. An **alias** is a
second name for a field, used "on the wire", meaning in the JSON that travels over the network:

```python-run
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

class Order(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    order_id: int
    customer_name: str
    total_usd: float = Field(alias="totalUSD")

o = Order.model_validate({"orderId": 7, "customerName": "Ann", "totalUSD": 19.9})
print(o.order_id, o.customer_name)
print(o.model_dump())                 # Python names
print(o.model_dump(by_alias=True))    # wire names
```

- `alias_generator=to_camel` gives every field a camelCase alias automatically.
- `populate_by_name=True` allows the Python name to be used as well when creating the model.
- `total_usd` gets a hand-written alias because the automatic one would be `totalUsd`.

`model_validate` reads the camelCase keys, and the code then uses the Python names
(`o.order_id`). `model_dump()` prints the Python names; `model_dump(by_alias=True)` prints the wire
names. FastAPI sends response models **by alias** by default, so the client sees camelCase while your
Python code keeps snake_case.

## Model configuration

`model_config = ConfigDict(...)` sets behaviour for the whole model. The options used most often:

- `extra="ignore" | "forbid" | "allow"`: what to do with fields that were not declared.
- `str_strip_whitespace=True`, `str_to_lower=True`: tidy up text automatically.
- `frozen=True`: instances cannot be changed after creation (and can be used as dictionary keys).
- `from_attributes=True`: allow `Model.model_validate(obj)` to read the *attributes* of any object,
  not only the keys of a dictionary. This is how database rows become models; an **ORM**
  (object-relational mapper, lesson 16) is a library that presents database rows as Python objects.
  Version 1 called this option `orm_mode`.
- `validate_assignment=True`: check again whenever a field is assigned after creation.
- `strict=True`, `populate_by_name=True`, `alias_generator=...`, all seen above.

```python-run
from pydantic import BaseModel, ConfigDict, ValidationError

class Row:                                   # pretend this is a SQLAlchemy object
    def __init__(self):
        self.id, self.email, self.hashed_password = 1, "  Ann@Example.com ", "xyz"

class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True,
                              str_to_lower=True, extra="forbid", frozen=True)
    id: int
    email: str

u = UserPublic.model_validate(Row())
print(u)
try:
    u.email = "x"
except ValidationError as e:
    print("frozen:", e.errors()[0]["type"])
```

`Row` imitates a database row object: it has attributes, including a `hashed_password` that must not
leak and an email with stray spaces and capitals. `UserPublic.model_validate(Row())` reads the
attributes it has fields for, strips and lower-cases the text, and prints
`id=1 email='ann@example.com'`. The password attribute is not a declared field, so it is not copied.
Because the model is frozen, the assignment `u.email = "x"` raises an error of type
`frozen_instance`.

## v1 → v2 cheat sheet

Old tutorials and forum answers still show version 1 names, and the book's examples sit across both
eras. This is the translation table:

| Pydantic v1 | Pydantic v2 |
|---|---|
| `.dict()` | `.model_dump()` |
| `.json()` | `.model_dump_json()` |
| `parse_obj(d)` | `model_validate(d)` |
| `parse_raw(s)` | `model_validate_json(s)` |
| `.copy(update=...)` | `.model_copy(update=...)` |
| `schema()` | `model_json_schema()` |
| `class Config: orm_mode = True` | `model_config = ConfigDict(from_attributes=True)` |
| `@validator` / `@root_validator` | `@field_validator` / `@model_validator` |
| `BaseSettings` in `pydantic` | `BaseSettings` in the separate `pydantic-settings` package |

> [!INTERVIEW]
> "Why does FastAPI use Pydantic, and what changed in v2?" — Pydantic turns type hints into runtime
> validation, conversion, serialisation and JSON Schema, which gives FastAPI request validation,
> response filtering and OpenAPI documentation at no extra effort. Version 2 moved the core into Rust
> (pydantic-core), making validation much faster, and introduced strict mode, the `model_*` method
> names, `field_validator` / `model_validator`, `ConfigDict` and `TypeAdapter`, and moved settings
> into the separate `pydantic-settings` package.

## Nested models and reading error locations

Real request bodies are trees: an order contains an address and a list of items. Pydantic checks the
whole tree in one pass and reports each problem with a **path** (`loc`) leading to it. It is the same
path FastAPI returns to clients, with `"body"` added at the front:

```python-run
from pydantic import BaseModel, Field, ValidationError

class Address(BaseModel):
    street: str
    city: str
    postcode: str = Field(pattern=r"^\d{5}$")

class LineItem(BaseModel):
    sku: str = Field(min_length=3)
    quantity: int = Field(ge=1)
    unit_price: float = Field(gt=0)

class Order(BaseModel):
    customer_email: str
    shipping: Address
    items: list[LineItem] = Field(min_length=1)
    notes: dict[str, str] = {}

payload = {
    "customer_email": "ann@example.com",
    "shipping": {"street": "1 Main St", "city": "Austin", "postcode": "ABCDE"},
    "items": [
        {"sku": "HAM-1", "quantity": 2, "unit_price": 9.5},
        {"sku": "x", "quantity": 0, "unit_price": "free"},
    ],
    "notes": {"gift": 1},
}
try:
    Order.model_validate(payload)
except ValidationError as e:
    for err in e.errors():
        print(".".join(str(p) for p in err["loc"]).ljust(22), err["type"])
```

The payload contains five mistakes on purpose, and the output lists all five:

- `shipping.postcode` (`string_pattern_mismatch`): `ABCDE` is not five digits.
- `items.1.sku` (`string_too_short`), `items.1.quantity` (`greater_than_equal`) and
  `items.1.unit_price` (`float_parsing`): three faults in the second item.
- `notes.gift` (`string_type`): the value `1` is a number where text is required.

Read `items.1.quantity` as "in `items`, the element at index 1, the field `quantity`" (indexes start
at 0, so that is the second item). Finding and locating every problem in one pass is what allows a
web form to highlight all the bad boxes at once.

A valid payload becomes nested objects with real types, and going back to dictionaries is one call:

```python-run
from pydantic import BaseModel

class Address(BaseModel):
    city: str

class User(BaseModel):
    name: str
    addresses: list[Address]

u = User.model_validate({"name": "Ann", "addresses": [{"city": "Austin"}, {"city": "Boston"}]})
print(type(u.addresses[0]).__name__, u.addresses[1].city)        # real Address objects, not dicts
print(u.model_dump())                                            # recursively back to plain dicts
copy = u.model_copy(deep=True)
copy.addresses[0].city = "Denver"
print(u.addresses[0].city, "|", copy.addresses[0].city)          # deep copy is independent
```

The first line prints `Address Boston`: the entries of `addresses` are real `Address` objects, not
dictionaries. `model_dump()` converts the whole tree back to plain dictionaries and lists. The last
three lines make a *deep copy* (a copy that also copies everything nested inside) and change the
copy; the original still says `Austin`.

## Unions: how Pydantic chooses

For a field declared `int | str`, which type wins when the input is `"5"`? Version 1 tried the types
from left to right, so the *order you wrote them in* silently changed the result. Version 2 uses a
**smart mode**: it first looks for a member type that the input already matches exactly, and only if
there is none does it try conversion.

```python-run
from pydantic import BaseModel

class M(BaseModel):
    a: int | str
    b: str | int
    c: float | int
    d: list[int] | str

print(M(a="5", b=5, c=3, d="12"))
# a stays '5' (already a str), b stays 5 (already an int), c stays int 3, d stays '12'
print(M(a=5, b="x", c=3.5, d=["1", 2]))
```

In the first line every input already matches one member, so nothing is converted:
`a='5' b=5 c=3 d='12'`. In the second, `a=5` stays an integer, `b="x"` stays text, `c=3.5` stays a
float, and `d=["1", 2]` becomes `[1, 2]` because a list was given and its elements could be converted.

When the members of a union are models, prefer a **discriminated union** (next lesson), where a
field in the data states outright which model is meant.

## Validating things that aren't model fields

Four tools cover data that does not arrive as a ready-made model instance:

- `Model.model_validate(obj)`: from a dictionary, or from any object when `from_attributes=True`.
- `Model.model_validate_json(text)`: parse and check JSON text in one step inside the Rust engine. It
  is faster than `json.loads` followed by `model_validate`.
- `TypeAdapter(T)`: the same engine for any type, such as `TypeAdapter(list[Order])` or
  `TypeAdapter(dict[str, float])`.
- `@validate_call`: a decorator that checks an ordinary function's arguments (and optionally its
  return value) against its hints. It gives runtime checking to internal functions that receive
  untrusted data.

```python-run
from pydantic import ValidationError, validate_call, Field
from typing import Annotated

@validate_call
def resize(width: Annotated[int, Field(gt=0, le=4096)], height: Annotated[int, Field(gt=0, le=4096)],
           keep_ratio: bool = True) -> str:
    return f"{width}x{height} keep_ratio={keep_ratio}"

print(resize("640", 480, keep_ratio="no"))        # coerced like model fields
try:
    resize(0, 99999)
except ValidationError as e:
    print([(err["loc"], err["type"]) for err in e.errors()])
```

`resize` is a normal function whose parameters carry constraints. Thanks to `@validate_call`, the
first call converts its arguments as a model would (`"640"` to `640`, `"no"` to `False`) and prints
`640x480 keep_ratio=False`. The second call breaks two rules, a width of 0 and a height above 4096,
and both are reported in one `ValidationError`. This is the fix for the `double("ha")` problem at the
top of the lesson.

## Cost model: where validation time goes

Validation is fast, since it runs as compiled Rust, but it is not free:

- **Creating the class** builds a validator and a serialiser for it. This happens once, when the
  module is imported.
- **Each call** costs time in proportion to the amount of data. Ten thousand nested objects in a
  request means ten thousand validations. For bulk numeric input (tables of features, embedding
  vectors) prefer a flat `list[list[float]]` with length limits, or a binary format, over a list of
  tiny models.
- `model_construct()` builds an instance **without any checking**. Use it only for data you have
  already validated, such as rows you wrote yourself. Using it on client input removes the safety
  net.
- In FastAPI a response model is validated *again* on the way out. For very large responses that you
  trust, returning a `Response` directly avoids that cost, at the price of losing the filtering.

## Dataclasses, TypedDict or BaseModel?

Python has two lighter ways to describe a record. A `dataclass` is a standard-library shortcut for
writing a class that mostly holds fields. A `TypedDict` is a hint describing which keys a dictionary
should have.

| | `dataclass` | `TypedDict` | Pydantic `BaseModel` |
|---|---|---|---|
| Runtime validation | no | no | **yes** |
| Coercion from JSON-ish input | no | no | yes |
| JSON serialisation | manual | manual | built in |
| JSON Schema | no | no | built in |
| Overhead | lowest | none (a dict) | small |
| Use for | internal value objects | typing existing dicts | **data crossing a trust boundary** |

The last row is the rule of thumb the book arrives at. A **trust boundary** is any point where data
enters or leaves your program: requests, responses, configuration, messages from queues, rows read
from files. Use Pydantic there, and feel free to use lighter structures deep inside.

## Pitfalls

- Assuming hints are checked at runtime in plain functions. Only Pydantic (or a similar library)
  checks them.
- Confusing optional with nullable. `x: int | None` with no default is **required**; the client must
  send it, though the value may be `null`. "Optional" means "has a default".
- Expecting a `str` field to accept a number (`123` to `"123"`). Version 2 rejects this.
- Using version 1 methods such as `.dict()`. They still exist but are deprecated and print warnings.
- Changing a field after creation and expecting it to be checked, without `validate_assignment=True`.

## Summary

- Pydantic enforces type hints on data at runtime: it validates, converts, and collects all errors.
- Lax mode performs safe conversions; strict mode demands exact types.
- `Field` and `Annotated` add constraints (`ge`, `max_length`, `pattern`) and documentation.
- Aliases separate Python names from wire names; `ConfigDict` sets model-wide behaviour (`extra`,
  `from_attributes`, `frozen`).
- Know the v1 → v2 renames.

## Glossary

- **Runtime** — the time during which a program is running.
- **Static checker** — a tool (mypy, pyright) that inspects hints before the program runs.
- **Model** — a class inheriting from `BaseModel`; a description of a data shape.
- **Field** — one named, typed entry in a model.
- **`ValidationError`** — the exception Pydantic raises, listing every problem found.
- **Coercion** — converting an input to the declared type (`"42"` to `42`).
- **Lax / strict mode** — allow safe conversions / demand exactly the declared type.
- **Union** — a type meaning "one of these", written `int | str`.
- **Constraint** — an extra rule on a value, such as `ge=18` or `max_length=50`.
- **`Field`** — the function that attaches constraints, defaults and documentation to a field.
- **`default_factory`** — a function called to produce a fresh default value.
- **`Annotated`** — a hint that carries extra information, used to build reusable constrained types.
- **`TypeAdapter`** — validates any type without defining a model class.
- **Alias** — a field's external name in JSON, as opposed to its Python name.
- **`ConfigDict` / `model_config`** — settings that apply to a whole model.
- **`from_attributes`** — the setting that lets a model be built from an object's attributes.
- **ORM** — a library that presents database rows as Python objects.
- **`loc`** — the path to the location of an error inside nested data.
- **Trust boundary** — a point where data enters or leaves your program.

```quiz
[
  {"q": "What does Python itself do with the hint in 'def f(n: int)' when called with f('x')?", "options": ["Raises TypeError", "Converts 'x' to int", "Nothing - hints are not enforced at runtime", "Logs a warning"], "answer": 2,
   "explain": "Type hints are metadata for tools. Runtime enforcement requires a library like Pydantic."},
  {"q": "In Pydantic v2 lax mode, which input is REJECTED for an int field?", "options": ["'42'", "42.0", "'4.5'", "True"], "answer": 2,
   "explain": "'4.5' would lose information, so it fails with int_parsing. 42.0 is an exact integer float; True is accepted as 1 in lax mode."},
  {"q": "A field declared 'nickname: str | None' with NO default is:", "options": ["Optional and defaults to None", "Required, but null is an allowed value", "Ignored", "Always None"], "answer": 1,
   "explain": "Requiredness comes from having a default, not from allowing None."},
  {"q": "Which config lets you build a model from an ORM object's attributes?", "options": ["extra='allow'", "from_attributes=True", "frozen=True", "strict=True"], "answer": 1,
   "explain": "from_attributes (v1: orm_mode) makes model_validate read attributes instead of dict keys."},
  {"q": "What is the v2 equivalent of model.dict()?", "options": ["model.to_dict()", "model.model_dump()", "dict(model)", "model.serialize()"], "answer": 1,
   "explain": "v2 prefixes model methods with model_: model_dump, model_dump_json, model_validate, model_copy."},
  {"q": "Why use Field(default_factory=list) or a [] default safely in Pydantic?", "options": ["Lists are immutable in Pydantic", "Pydantic copies mutable defaults per instance, and default_factory creates a fresh object each time", "It is required syntax", "To enable strict mode"], "answer": 1,
   "explain": "Unlike plain Python function defaults, model defaults are not shared mutably between instances."},
  {"q": "What does TypeAdapter let you do?", "options": ["Convert models to SQL", "Validate and serialise arbitrary types (e.g. list[Model]) without defining a BaseModel", "Define database adapters", "Generate API clients"], "answer": 1,
   "explain": "TypeAdapter wraps any type with Pydantic's validation, serialisation and JSON Schema machinery."}
]
```

> **Source:** Lubanovic, *FastAPI*, ch. 5 "Pydantic, Type Hints, and Models Tour" (Type Hinting, Data Grouping, Alternatives, Validate Types, Validate Values); https://docs.pydantic.dev/latest/concepts/models/, /concepts/fields/, /concepts/strict_mode/, /concepts/config/; https://fastapi.tiangolo.com/python-types/
