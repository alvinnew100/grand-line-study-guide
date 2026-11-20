# Pydantic models, types and Field

FastAPI does not validate data itself — it delegates to **Pydantic**. Every 422 you see, every response
that gets filtered, every JSON Schema in `/docs` comes from Pydantic. Pydantic v2 (2023) rewrote the core
in Rust (`pydantic-core`), making validation 5–50× faster than v1, and changed several method names. This
module teaches Pydantic on its own terms; everything here runs without FastAPI, so the examples are live.

## Why type hints need a runtime library

Lubanovic's chapter 5 starts from the observation that Python's type hints are *ignored at runtime*:

```python-run
def double(n: int) -> int:
    return n * 2

print(double("ha"))      # no error: hints are documentation for tools, not runtime checks
```

Static checkers (mypy, pyright) catch some bugs in *your* code, but they cannot check data arriving from
the network at runtime. That is the gap Pydantic fills: it **reads the same type hints at runtime** and
enforces them on incoming data, converting where sensible.

The book walks through the alternatives for grouping data — tuples, dicts, `namedtuple`, dataclasses,
`attrs` — and lands on Pydantic because it combines a class-like definition with validation, conversion,
and JSON (de)serialisation.

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

Key behaviours:

- Fields without defaults are **required**; with defaults are optional.
- Values are **converted** where unambiguous (`"1951-11-08"` → `date`, `"5"` → `5` for `int`).
- Errors are collected for **all** fields, not just the first, in one `ValidationError`.
- Mutable defaults like `[]` are safe — Pydantic copies them per instance (unlike plain function defaults).

## Lax versus strict mode

By default Pydantic is **lax**: it coerces compatible inputs. Some coercions it accepts and rejects:

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

Note that `4.0` → `4` is allowed (no information lost) but `"4.5"` → `int` is not, and `123` is *not*
coerced to `"123"` for a `str` field. Strictness can be set per model (`ConfigDict(strict=True)`), per field
(`Field(strict=True)`), or per call (`model_validate(data, strict=True)`). In JSON mode, strict mode still
accepts JSON-native forms like ISO date strings.

## The type vocabulary

Pydantic understands standard and many special types:

| Category | Examples |
|---|---|
| Builtins | `int`, `float`, `str`, `bool`, `bytes`, `list[T]`, `dict[K, V]`, `set[T]`, `tuple[int, str]` |
| Optionals/unions | `str \| None`, `int \| str` (smart union: picks the best match) |
| Literals & enums | `Literal["asc", "desc"]`, `Enum` subclasses |
| Time | `datetime`, `date`, `time`, `timedelta` (ISO 8601 strings parsed) |
| IDs & numbers | `UUID`, `Decimal` |
| Pydantic types | `EmailStr` (needs `email-validator`), `HttpUrl`, `AnyUrl`, `SecretStr`, `PositiveInt`, `conint`, `constr`, `IPvAnyAddress`, `Json[T]` |
| Nested | other `BaseModel` classes, arbitrarily deep |
| Discriminated unions | `Annotated[Cat \| Dog, Field(discriminator="kind")]` |

`SecretStr` deserves a mention: it hides its value in `repr` and logs (`SecretStr('**********')`) — use it
for API keys and passwords in settings.

## `Field`: constraints and metadata

`Field` attaches validation constraints and documentation to a field:

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

Constraint vocabulary: numbers `gt`, `ge`, `lt`, `le`, `multiple_of`; strings `min_length`, `max_length`,
`pattern`; collections `min_length`, `max_length`; decimals `max_digits`, `decimal_places`. Metadata:
`title`, `description`, `examples`, `alias`, `exclude`, `deprecated`. Defaults: `default=` or
`default_factory=` (a callable, for lists/dicts/timestamps).

Lubanovic's "Validate Values" section does the same with the older `constr`/`conint` helpers and
`Field(..., min_length=2)`; in v2 the `Field` / `Annotated` style is preferred.

### `Annotated` constraints: reusable types

You can bake constraints into a reusable type alias with `Annotated`, which is exactly the same mechanism
FastAPI uses for `Query()` and `Depends()`:

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

## Aliases: Python names vs wire names

JSON from a JavaScript client may use `camelCase` or names that aren't valid identifiers:

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

FastAPI serialises response models **by alias** by default, so the client sees camelCase while your
Python code stays snake_case.

## Model configuration

`model_config = ConfigDict(...)` controls model-wide behaviour. The options you'll use most:

- `extra="ignore" | "forbid" | "allow"` — what to do with unknown fields.
- `str_strip_whitespace=True`, `str_to_lower=True` — normalise strings.
- `frozen=True` — immutable, hashable instances.
- `from_attributes=True` — validate from arbitrary objects' attributes (ORM rows) via
  `Model.model_validate(orm_obj)`. (v1 called this `orm_mode`.)
- `validate_assignment=True` — re-validate when attributes are set after creation.
- `strict=True`, `populate_by_name=True`, `alias_generator=...`.

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

## v1 → v2 cheat sheet

Old tutorials and Stack Overflow answers still show v1 names. The book's examples straddle both eras; here
is the mapping you'll need:

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
> validation, conversion, serialisation and JSON Schema, which gives FastAPI request validation, response
> filtering and OpenAPI for free. v2 moved the core into Rust (pydantic-core), making validation much
> faster, introduced strict mode, `model_*` method names, `field_validator`/`model_validator`, `ConfigDict`,
> `TypeAdapter`, and split settings into `pydantic-settings`.

## Pitfalls

- Assuming hints are checked at runtime in plain functions — only Pydantic (or similar) checks them.
- Optional vs nullable: `x: int | None` without a default is **required** but may be `null`. Optional
  means "has a default".
- Expecting `str` fields to coerce numbers (`123` → `"123"`): v2 rejects this.
- Using v1 methods (`.dict()`) — they still exist but are deprecated and emit warnings.
- Mutating a model and expecting validation, without `validate_assignment=True`.

## Summary

- Pydantic enforces type hints on data at runtime: it validates, converts, collects all errors.
- Lax mode coerces safe conversions; strict mode demands exact types.
- `Field` and `Annotated` add constraints (`ge`, `max_length`, `pattern`) and docs metadata.
- Aliases separate Python names from wire names; `ConfigDict` sets model-wide behaviour (`extra`,
  `from_attributes`, `frozen`).
- Know the v1 → v2 renames.

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
