# Pythonic idioms

Code can be correct and still not be *Pythonic*. Idiomatic Python uses the language's own constructs — iteration protocols, unpacking, comprehensions, context managers, the standard library — instead of transliterating habits from C or Java. The payoff isn't aesthetic: idiomatic code is shorter, usually faster (the work happens in C inside the interpreter), has fewer places for off-by-one bugs, and is what reviewers and interviewers expect. This lesson is a tour of before/after pairs, pulling together the whole track.

## The Zen of Python

`import this` prints Tim Peters' nineteen aphorisms. The ones that guide daily decisions:

- *Beautiful is better than ugly. Explicit is better than implicit. Simple is better than complex.*
- *Flat is better than nested. Readability counts.*
- *Errors should never pass silently.*
- *There should be one — and preferably only one — obvious way to do it.*
- *If the implementation is hard to explain, it's a bad idea.*

"Pythonic" means in the spirit of these — not "clever". A dense one-liner nobody can read is un-Pythonic.

## Iteration

**Loop over items, not indices.**

```python-run
names = ["luffy", "zoro", "nami"]
bounties = [3000, 1111, 366]

# un-Pythonic
for i in range(len(names)):
    print(i, names[i], bounties[i])

# Pythonic
for i, (name, bounty) in enumerate(zip(names, bounties)):
    print(i, name, bounty)

for name in reversed(names): print(name, end=" ")
print()
for name in sorted(names, key=len): print(name, end=" ")
print()
print(dict(zip(names, bounties)), list(zip(*[(1, "a"), (2, "b")])))    # build a dict; unzip
```

| Need | Idiom |
|---|---|
| index + item | `enumerate(xs, start=1)` |
| parallel sequences | `zip(a, b)` (`strict=True` to demand equal lengths) |
| backwards | `reversed(xs)` |
| sorted view | `sorted(xs, key=...)` |
| adjacent pairs | `zip(xs, xs[1:])` or `itertools.pairwise(xs)` |
| dict items | `for k, v in d.items():` |
| until sentinel | `for chunk in iter(lambda: f.read(4096), b""):` |
| search with fallback | `for ... else:` or `next((x for x in xs if p(x)), default)` |

## Unpacking and swapping

```python-run
a, b = 1, 2
a, b = b, a                                   # swap, no temp
first, *middle, last = [1, 2, 3, 4, 5]
(x, y), label = (3, 4), "pt"
head, *_ = "abc"
print(a, b, first, middle, last, x, y, label, head)

def min_max(xs):
    return min(xs), max(xs)                   # return several values as a tuple
lo, hi = min_max([4, 9, 2])
print(lo, hi, *[1, 2, 3], sep=" | ")
```

## Truthiness and comparisons

```python-run
items, name, result = [], "", None

if not items: print("empty list")             # not: if len(items) == 0
if not name: print("empty string")            # not: if name == ""
if result is None: print("no result")         # not: if result == None
x = 7
print(0 < x < 10, x in (2, 3, 5, 7))          # chained comparison; membership instead of or-chains
flag = x > 5                                  # not: flag = True if x > 5 else False
print(flag, bool(items))
```

Careful where `0`, `""` or empty containers are *valid* values: test `is None` explicitly.

## Building strings

```python-run
parts = ["2026", "01", "15"]
print("-".join(parts))                                   # not: a loop with +=
name, score = "Robin", 97.4567
print(f"{name!r:>10} scored {score:.1f} ({score / 100:.0%})")
print(", ".join(str(n) for n in range(5)))
print(f"{name=}, {score=:.2f}")
long_text = (
    "adjacent string literals "
    "are concatenated at compile time"
)
print(long_text)
```

## Comprehensions and generator expressions

```python-run
nums = [3, -1, 4, -1, 5, -9]

squares = [n * n for n in nums if n > 0]                 # map + filter
index = {n: i for i, n in enumerate(nums)}               # dict comprehension
unique_abs = {abs(n) for n in nums}                      # set comprehension
total = sum(n * n for n in nums)                         # generator: no temporary list
print(squares, index, unique_abs, total)
print(any(n < 0 for n in nums), all(isinstance(n, int) for n in nums))
print(max(nums, key=abs), sorted(nums, key=abs)[:2], sum(1 for n in nums if n < 0))
```

`any`/`all`/`sum`/`min`/`max` with generator expressions replace most flag-and-loop patterns. But: if a comprehension needs more than two clauses, or you're using one only for side effects, write the loop.

## Dictionaries

```python-run
from collections import Counter, defaultdict

d = {"a": 1}
print(d.get("b", 0))                                     # default instead of if-in-else
d.setdefault("list", []).append(1)                       # init-and-use
counts = Counter("mississippi")                          # counting
groups = defaultdict(list)                               # grouping
for w in ["apple", "avocado", "banana"]:
    groups[w[0]].append(w)
merged = {"x": 1, "y": 2} | {"y": 20}                    # merge (3.9+)
inverted = {v: k for k, v in merged.items()}
print(d, counts.most_common(2), dict(groups), merged, inverted)

# EAFP instead of check-then-act
try:
    value = d["missing"]
except KeyError:
    value = None

# dispatch table instead of a long if/elif chain
ops = {"+": lambda a, b: a + b, "-": lambda a, b: a - b, "*": lambda a, b: a * b}
print(ops["*"](6, 7))
```

## Functions

- Small functions that do one thing, named with verbs; return values rather than mutating arguments.
- Keyword arguments for clarity (`connect(timeout=5, retries=3)`), keyword-only for flags.
- `None` as the default for mutable parameters.
- Return early with **guard clauses** to avoid deep nesting:

```python-run
def shipping_cost_nested(order):
    if order is not None:
        if order["items"]:
            if order["country"] == "PT":
                return 0
            else:
                return 10
        else:
            raise ValueError("empty order")
    else:
        raise ValueError("no order")

def shipping_cost(order):
    if order is None:
        raise ValueError("no order")
    if not order["items"]:
        raise ValueError("empty order")
    return 0 if order["country"] == "PT" else 10         # flat is better than nested

print(shipping_cost({"items": [1], "country": "PT"}), shipping_cost_nested({"items": [1], "country": "BR"}))
```

## Resources, errors and constants

```python-run
import contextlib, io
from enum import Enum, auto
from pathlib import Path

with contextlib.redirect_stdout(io.StringIO()) as buf:   # with: guaranteed cleanup
    print("captured")
print(buf.getvalue().strip())

class Color(Enum):                                       # enums instead of magic strings/ints
    RED = auto()
    GREEN = auto()
print(Color.RED, Color.RED.name, Color["GREEN"], list(Color), Color.RED is Color.RED)

MAX_RETRIES = 3                                          # named constants, UPPER_CASE
p = Path("data") / "raw" / "file.csv"                    # pathlib instead of string paths
print(p.suffix, p.stem, p.parent.as_posix())

_MISSING = object()                                      # sentinel when None is a valid value
def get(d, key, default=_MISSING):
    if key in d:
        return d[key]
    if default is _MISSING:
        raise KeyError(key)
    return default
print(get({"a": None}, "a"), get({}, "b", None))
```

## Classes

- Give data holders `@dataclass` instead of hand-written `__init__`/`__repr__`/`__eq__`.
- Start with plain attributes; add `@property` only when you need validation or computation.
- Implement dunder methods so objects work with `len`, `in`, `for`, `sorted`, `==`.
- Prefer composition and small `Protocol`s over deep inheritance.
- Don't write a class when a function (or a dict, or a namedtuple) will do.

```python-run
from dataclasses import dataclass, field

@dataclass(order=True, frozen=True)
class Card:
    rank: int
    suit: str = field(compare=False)

hand = [Card(12, "hearts"), Card(3, "spades"), Card(12, "clubs")]
print(max(hand), sorted(hand)[0], Card(3, "x") == Card(3, "y"), len({Card(1, "a"), Card(1, "b")}))
```

## PEP 8 in two minutes

| Thing | Convention |
|---|---|
| Indentation | 4 spaces, no tabs |
| Line length | 79 in PEP 8; most teams use 88–100 |
| Functions, variables, modules | `snake_case` |
| Classes, exceptions | `PascalCase` |
| Constants | `UPPER_SNAKE_CASE` |
| "Internal" names | `_leading_underscore` |
| Imports | top of file; stdlib, third-party, local — separated by blank lines; one module per line |
| Blank lines | two around top-level definitions, one between methods |
| Whitespace | `x = f(a, b)`, `d["k"]`, `a[1:3]`; no spaces around `=` in keyword args |
| Comparisons | `is None`, `is not`, `not in`; never `== True` |
| Docstrings | triple double quotes, imperative one-line summary (PEP 257) |

Don't argue about style — automate it. **ruff** (linter + formatter) or **black** + **isort** format on save and in CI; **mypy**/**pyright** type-check. Configure them in `pyproject.toml`.

## A worked refactoring

A function written "C-style", then idiomatically:

```python-run
def top_customers_v1(orders, n):
    totals = {}
    for i in range(len(orders)):
        order = orders[i]
        if order["status"] == "paid":
            if order["customer"] in totals.keys():
                totals[order["customer"]] = totals[order["customer"]] + order["amount"]
            else:
                totals[order["customer"]] = order["amount"]
    pairs = []
    for key in totals.keys():
        pairs.append([totals[key], key])
    pairs.sort()
    pairs.reverse()
    result = []
    i = 0
    while i < n and i < len(pairs):
        result.append(pairs[i][1])
        i = i + 1
    return result

from collections import Counter

def top_customers(orders, n):
    """Return the n customers with the highest total of paid orders."""
    totals = Counter()
    for order in orders:
        if order["status"] == "paid":
            totals[order["customer"]] += order["amount"]
    return [customer for customer, _ in totals.most_common(n)]

orders = [
    {"customer": "ana", "amount": 50, "status": "paid"},
    {"customer": "ben", "amount": 70, "status": "paid"},
    {"customer": "ana", "amount": 40, "status": "paid"},
    {"customer": "cy", "amount": 500, "status": "refunded"},
]
print(top_customers_v1(orders, 2), top_customers(orders, 2))
```

Twenty lines became six, the intent is in the docstring and names, and the counting/top-k logic is delegated to a tested library class.

## Idioms that are *anti*-patterns

| Smell | Prefer |
|---|---|
| `except:` / `except Exception: pass` | catch specific exceptions; log |
| `from module import *` | explicit imports |
| `if x == True:` / `if len(xs) > 0:` | `if x:` / `if xs:` |
| `type(x) == list` | `isinstance(x, list)` |
| `lst = lst + [x]` in a loop | `lst.append(x)` |
| `s += piece` in a big loop | `"".join(pieces)` |
| `x in list` inside a loop | convert to a `set` once |
| `list.pop(0)` in a loop | `collections.deque` |
| `[print(x) for x in xs]` | a `for` loop |
| mutable default `def f(a=[])` | `a=None` |
| `d.keys()` just to iterate or test membership | `for k in d`, `k in d` |
| getters/setters everywhere | attributes, then `@property` if needed |
| `lambda` bound to a name | `def` |
| deep nesting | guard clauses, helper functions |
| reinventing `Counter`, `groupby`, `bisect`, `heapq` | use the standard library |

> [!INTERVIEW]
> Interviewers notice idiom fluency within the first few lines: `enumerate`/`zip` instead of index loops, a `set` for membership, `Counter`/`defaultdict` for tallies, `"".join`, tuple-key sorting, slicing for reversal, `with` for files, and early returns. It signals real experience and leaves you more time for the algorithm. When you use a concise idiom, say what it does and its cost ("`Counter` builds frequencies in O(n)").

## Summary

Pythonic code iterates directly, unpacks, uses comprehensions and built-in reducers, leans on dict/set/`collections`, manages resources with `with`, prefers EAFP and guard clauses, models data with dataclasses and enums, follows PEP 8 via automated tools — and stays readable above all.

```quiz
[
  {"q": "Most Pythonic way to loop over a list with indices?", "options": ["for i in range(len(xs)): x = xs[i]", "for i, x in enumerate(xs):", "i = 0; while i < len(xs):", "for i in xs.index():"], "answer": 1,
   "explain": "enumerate yields (index, item) pairs without manual indexing."},
  {"q": "Idiomatic test for an empty list `xs`?", "options": ["if len(xs) == 0:", "if xs == []:", "if not xs:", "if xs is None:"], "answer": 2,
   "explain": "Empty containers are falsy. (Use `is None` only to distinguish a missing value.)"},
  {"q": "Best way to concatenate 10,000 strings?", "options": ["s += piece in a loop", "''.join(pieces)", "reduce with +", "str(pieces)"], "answer": 1,
   "explain": "join computes the total size once; repeated += may copy the growing string each time."},
  {"q": "How do you swap a and b idiomatically?", "options": ["tmp = a; a = b; b = tmp", "a, b = b, a", "swap(a, b)", "a = b = a"], "answer": 1,
   "explain": "Tuple packing and unpacking evaluates the right side first, then assigns."},
  {"q": "Which is preferred for checking the type of x?", "options": ["type(x) == list", "isinstance(x, list)", "x.__class__ == list", "str(type(x)) == 'list'"], "answer": 1,
   "explain": "isinstance respects subclasses and accepts tuples of types."},
  {"q": "What does `any(n < 0 for n in nums)` do efficiently?", "options": ["Builds a full list first", "Stops at the first negative number (short-circuits)", "Sorts nums", "Counts negatives"], "answer": 1,
   "explain": "The generator is consumed lazily and any() returns as soon as it sees a truthy value."},
  {"q": "According to PEP 8, how are class names and function names written?", "options": ["snake_case and PascalCase", "PascalCase and snake_case", "camelCase for both", "UPPER_CASE for both"], "answer": 1,
   "explain": "Classes use PascalCase (CapWords); functions and variables use snake_case; constants UPPER_SNAKE_CASE."},
  {"q": "Why prefer guard clauses (early returns)?", "options": ["They run faster", "They reduce nesting, keeping the main path flat and readable", "They are required by PEP 8", "They avoid exceptions"], "answer": 1,
   "explain": "'Flat is better than nested': handle special cases first and return, leaving the main logic unindented."}
]
```

> **Source:** PEP 8 (Style Guide for Python Code), PEP 20 (The Zen of Python), PEP 257; Python docs, *Tutorial* ch. 4–5 and *Programming FAQ*; Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, §1.9 (Additional Python Conveniences) and §2.2.3 (Coding Style and Documentation).
