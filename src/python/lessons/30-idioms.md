# Pythonic idioms

> **Before this lesson:** this lesson gathers ideas from the whole track, so it helps to have worked through most of it. In particular you should know loops and `enumerate` from [Lists, tuples and strings](#/lesson/python/py-sequences), comprehensions and unpacking from [Comprehensions, unpacking and copying](#/lesson/python/py-comprehensions-copying), dictionaries from [Dictionaries and sets](#/lesson/python/py-dicts-sets), `Counter` and `defaultdict` from [collections](#/lesson/python/py-collections), the `with` statement from [Context managers and contextlib](#/lesson/python/py-context-managers) and `@dataclass` from [Properties, dataclasses, ABCs and composition](#/lesson/python/py-properties-dataclasses). Every idiom is explained again briefly where it appears, so a gap or two will not stop you.

## In plain words

An **idiom** is the usual, natural way that fluent speakers say something. "It's raining cats and dogs" is an English idiom; a word-for-word translation from another language might be grammatically correct and still sound odd to a native speaker. Programming languages have idioms too. **Pythonic** code is code written the way experienced Python programmers would naturally write it, using the tools the language was designed around instead of habits carried over from another language such as C or Java.

Here is the difference in one picture. Someone who learnt programming in C tends to loop over a list by counting positions: "for each number from 0 up to the length, look up the item at that position". A Python programmer loops over the items themselves: "for each item in the list". Both are correct. The second is shorter, has no position counter that can be off by one, and says what it means.

Why this matters for a job:

- **Code review.** Teams expect idiomatic code. A pull request full of index loops and hand-built counting dictionaries will collect comments asking you to use `enumerate`, `zip` or `Counter`.
- **Interviews.** Interviewers notice in the first few lines whether you write Python fluently. Idiomatic code also takes less time to type, which leaves more time for the algorithm.
- **Speed and correctness.** Many idioms hand the work to functions written in C inside the interpreter, so they often run faster. Fewer hand-written counters and flags also mean fewer places for bugs.

This lesson is a tour of "before and after" pairs: a clumsy version, the idiomatic version, and why the second is better.

## The Zen of Python

A **PEP** (Python Enhancement Proposal) is a numbered design document that proposes or records a decision about the language. PEP 20, *The Zen of Python*, is a short poem of nineteen sayings by the long-time core developer Tim Peters. It is built into every Python installation as a hidden joke module; importing it prints the poem:

```python-run
import this
```

The sayings that guide everyday decisions most often are these:

- *Beautiful is better than ugly. Explicit is better than implicit. Simple is better than complex.*
- *Flat is better than nested. Readability counts.*
- *Errors should never pass silently.*
- *There should be one — and preferably only one — obvious way to do it.*
- *If the implementation is hard to explain, it's a bad idea.*

"Explicit is better than implicit" means the code should say what it does, not rely on the reader guessing a hidden rule. "Flat is better than nested" means fewer levels of indentation. "Errors should never pass silently" means you should not hide failures.

"Pythonic" means written in the spirit of these sayings. It does not mean "clever". A dense one-liner that nobody can read is *un*-Pythonic, however short it is.

## Iteration

To **iterate** means to go through a collection one item at a time. An **iterable** is anything you can iterate over with `for`: a list, a tuple, a string, a dictionary, a file, a `range`, and many more.

### Loop over items, not positions

The simplest possible example first. Both loops below print every name:

```python-run
names = ["luffy", "zoro", "nami"]

# counting positions, a habit from C
for i in range(len(names)):
    print(names[i])

# looping over the items directly: the Pythonic way
for name in names:
    print(name)
```

The first loop asks for `len(names)` (3), builds the numbers 0, 1, 2 with `range`, and uses each number to look up an item with `names[i]`. The second loop asks the list for its items directly. It has no number to get wrong and reads like the English sentence "for each name in names".

### When you also need the position: `enumerate`

Sometimes you really do need the position, for example to print a numbered list. `enumerate(xs)` hands you pairs of (position, item), and `for i, name in ...` splits each pair into two names. That splitting is called **unpacking**, and it gets its own section below.

The next demo goes further. It has two lists that belong together: `names[0]` goes with `bounties[0]`, and so on. Lists that line up like this are called **parallel sequences**.

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

**Reading this code line by line**

- The first loop is the index style: it prints `0 luffy 3000`, `1 zoro 1111`, `2 nami 366`.
- `zip(names, bounties)` walks both lists side by side and produces pairs: `("luffy", 3000)`, `("zoro", 1111)`, `("nami", 366)`. The name comes from a zip fastener, which joins two rows of teeth.
- `enumerate(...)` numbers those pairs, so each step receives `(0, ("luffy", 3000))`. The target `i, (name, bounty)` mirrors that shape: `i` gets the number and the inner parentheses unpack the pair. The output is identical to the first loop.
- `reversed(names)` goes through the list backwards without copying it. `end=" "` tells `print` to end with a space instead of a new line, so the names appear on one line: `nami zoro luffy`.
- `sorted(names, key=len)` returns a new list ordered by length. A **key function** is a function applied to each item to get the value that is compared; here the items are compared by their length. The output is `zoro nami luffy`: "zoro" and "nami" both have four letters, and Python's sort is **stable**, meaning items that compare equal keep their original order, so "zoro" stays ahead of "nami".
- `dict(zip(names, bounties))` turns the pairs straight into a dictionary: `{'luffy': 3000, 'zoro': 1111, 'nami': 366}`.
- `zip(*[(1, "a"), (2, "b")])` is the "unzip" trick. The `*` spreads the list out so `zip` receives two arguments, `(1, "a")` and `(2, "b")`; zipping them pairs first items with first items and second with second, giving `[(1, 2), ('a', 'b')]`.

A table of the most useful iteration idioms. You do not need to memorise it; come back to it when you write a loop.

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

Three rows need a word of explanation.

- `zip` stops quietly at the end of the *shorter* input. If unequal lengths would mean a bug, pass `strict=True` (Python 3.10 and later) and `zip` raises an error instead.
- A **sentinel** is a special value that means "stop". `iter(function, sentinel)` keeps calling the function and yields its results until one equals the sentinel. Reading a file in blocks of 4,096 bytes until `read` returns the empty bytes `b""` is the classic use.
- "Search with fallback" means "find the first item that passes a test, or use a default if none does". The demo below shows both spellings.

```python-run
crew = ["usopp", "sanji", "chopper"]

# for ... else: the else block runs only if the loop did NOT break
for member in crew:
    if member.startswith("s"):
        print("first s-name:", member)
        break
else:
    print("no s-name")

# next() with a default: the same search as one expression
print(next((m for m in crew if m.startswith("z")), "nobody"))
print(list(zip(crew, crew[1:])))
```

The `for` loop finds "sanji", prints it and leaves with `break`, so the `else` block is skipped. (`else` on a loop is easy to misread: think of it as "no break happened".) In the second search, `(m for m in crew if ...)` is a **generator expression**, a lazy recipe that produces matching items one at a time; `next` takes the first one, and because no name starts with "z" it returns the default, `nobody`. The last line pairs each item with its neighbour: `[('usopp', 'sanji'), ('sanji', 'chopper')]`.

## Unpacking and swapping

**Unpacking** means assigning the items of a sequence to several names in one statement. The number of names on the left must match the number of items on the right, unless one name has a star.

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

**Reading this code line by line**

- `a, b = 1, 2` builds the tuple `(1, 2)` on the right and unpacks it: `a` is 1, `b` is 2.
- `a, b = b, a` swaps the two values. Python evaluates the whole right-hand side first, making the tuple `(2, 1)`, and only then assigns. No temporary variable is needed, unlike in C.
- `first, *middle, last = [1, 2, 3, 4, 5]`: the starred name collects "everything left over" as a list, so `middle` is `[2, 3, 4]`.
- `(x, y), label = (3, 4), "pt"`: the left side has the same nested shape as the right, so `x` is 3, `y` is 4 and `label` is `"pt"`.
- `head, *_ = "abc"` keeps the first letter and throws away the rest. By convention the name `_` means "a value I do not care about".
- `min_max` returns two values. Strictly, it returns one tuple, `(2, 9)`, which the caller unpacks into `lo` and `hi`.
- In the last `print`, `*[1, 2, 3]` spreads the list into three separate arguments, and `sep=" | "` puts a bar between all of them.

The output is `2 1 1 [2, 3, 4] 5 3 4 pt a` and then `2 | 9 | 1 | 2 | 3`.

## Truthiness and comparisons

Every Python value can be used where a yes/no answer is expected, such as after `if`. A value that counts as true is called **truthy**; one that counts as false is **falsy**. The falsy values are `False`, `None`, zero of any number type, and every *empty* container: `""`, `[]`, `()`, `{}`, `set()`. Everything else is truthy. This rule is called **truthiness**, and it lets you write tests the way you would say them aloud.

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

**Reading this code line by line**

- `if not items:` reads "if there are no items". An empty list is falsy, so `not items` is `True` and `empty list` is printed.
- `if not name:` does the same for an empty string.
- `if result is None:` uses `is`, which asks "is this the very same object?" There is only one `None` object in a running program, so `is` is the precise test. `== None` usually works too, but a class can redefine `==` to do something surprising, while `is` cannot be redefined.
- `0 < x < 10` is a **chained comparison**: Python reads it as `0 < x and x < 10`, as a mathematician would.
- `x in (2, 3, 5, 7)` replaces the long chain `x == 2 or x == 3 or x == 5 or x == 7`.
- `flag = x > 5`: a comparison already produces `True` or `False`, so wrapping it in `True if ... else False` adds nothing.
- `bool(items)` converts a value to its truthiness explicitly: `False` for the empty list.

The output is the three messages, then `True True`, then `True False`.

> [!WARNING]
> Be careful where `0`, `""` or an empty container is a *valid* value. If a function returns a count, a count of 0 is a real answer, but `if not count:` treats it the same as "no answer". When "missing" and "zero" must be told apart, return `None` for missing and test `if count is None:`.

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

**Reading this code line by line**

- `"-".join(parts)` glues the strings in `parts` together with `"-"` between them: `2026-01-15`. The string you call `join` on is the separator.
- An **f-string** is a string literal with `f` in front; anything inside `{}` is evaluated and inserted. After a colon comes a **format specification**, a tiny language for layout. `{name!r:>10}` takes the `repr` of the name (with quotes, `'Robin'`, seven characters) and right-aligns it in a field 10 characters wide, so three spaces appear in front. `{score:.1f}` shows one digit after the decimal point, `97.5`. `{score / 100:.0%}` shows 0.974567 as a percentage with no decimals, `97%`.
- `", ".join(str(n) for n in range(5))` turns each number into text and joins them: `0, 1, 2, 3, 4`. `join` only accepts strings, which is why `str(n)` is needed.
- `f"{name=}"` (Python 3.8 and later) prints the expression *and* its value, `name='Robin'`, which is very handy when debugging. A format can follow, as in `score=97.46`.
- Two string literals written next to each other, with nothing between them, are joined into one string when the code is compiled. Wrapping them in parentheses lets a long string span several lines without any `+`.

Why prefer `join` over adding with `+=` in a loop? Strings are **immutable**, meaning they can never be changed after creation, so `s += piece` builds a brand-new string each time and may copy everything collected so far. Over many pieces that copying adds up. `join` measures all the pieces first and builds the result once.

## Comprehensions and generator expressions

A **comprehension** builds a list, set or dictionary from a loop written inside the brackets. A **generator expression** has the same syntax in round brackets and produces items lazily, one at a time, without building a list.

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

**Reading this code line by line**

- `[n * n for n in nums if n > 0]` reads "n squared, for each n in nums, keeping only positive n". It **maps** (transforms each item) and **filters** (keeps some items) in one line: `[9, 16, 25]`.
- `{n: i for i, n in enumerate(nums)}` builds a dictionary from each number to its position. `-1` appears twice; the second assignment overwrites the first, so `-1` maps to 3. The key keeps its original place in the dictionary's order, which is why the result is `{3: 0, -1: 3, 4: 2, 5: 4, -9: 5}`.
- `{abs(n) for n in nums}` is a set of absolute values; duplicates vanish, leaving `{1, 3, 4, 5, 9}`.
- `sum(n * n for n in nums)` adds the squares, 133, without ever storing them in a list. When a generator expression is the only argument of a call, its own parentheses can be dropped.
- `any(...)` is `True` if at least one item is truthy, and it stops at the first one it finds. `all(...)` is `True` if every item is truthy and stops at the first failure. Stopping early like this is called **short-circuiting**.
- `max(nums, key=abs)` is the number with the largest absolute value, `-9`. `sorted(nums, key=abs)[:2]` gives the two closest to zero, `[-1, -1]`. `sum(1 for n in nums if n < 0)` counts the negatives: 3.

`any`, `all`, `sum`, `min` and `max` fed by a generator expression replace most "set a flag, loop, update the flag" patterns. Two limits: if a comprehension needs more than two `for` or `if` clauses, a plain loop is easier to read; and if you are writing a comprehension only for its side effects, such as printing, write the loop instead.

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

**Reading this code line by line**

- `d.get("b", 0)` returns the value for `"b"` if it exists and `0` otherwise, replacing a four-line `if "b" in d: ... else: ...`. It prints `0`.
- `d.setdefault("list", [])` returns the value for `"list"`, first storing `[]` there if the key was missing. Chaining `.append(1)` therefore works whether or not the key existed.
- `Counter("mississippi")` counts each letter. `most_common(2)` gives the two most frequent: `[('i', 4), ('s', 4)]`. On a tie, the letter seen first comes first.
- `defaultdict(list)` is a dictionary that creates an empty list the first time a missing key is used. That makes grouping a one-liner: `groups[w[0]].append(w)` files each word under its first letter, giving `{'a': ['apple', 'avocado'], 'b': ['banana']}`.
- `|` merges two dictionaries (Python 3.9 and later); where both have a key, the right-hand value wins, so `y` becomes 20.
- `{v: k for k, v in merged.items()}` swaps keys and values: `{1: 'x', 20: 'y'}`.

Then two named idioms.

**EAFP and LBYL.** *Look Before You Leap* (LBYL) checks first and acts second: `if "missing" in d: value = d["missing"]`. *Easier to Ask Forgiveness than Permission* (EAFP) tries the action and handles the failure: the `try`/`except KeyError` block. Python culture favours EAFP. It avoids looking the key up twice, and in programs where another thread or process could change the data between the check and the action, it avoids a gap in which the check is no longer true. For a plain dictionary lookup with a default, `d.get` is shorter still; EAFP shines when the failure is rare or the check would be expensive.

**Dispatch table.** A long `if op == "+": ... elif op == "-": ...` chain can become a dictionary from each choice to the function that handles it. `ops["*"]` looks up the multiplying function and `(6, 7)` calls it: `42`. Adding a new operation means adding one entry, not another branch.

## Functions

- Write small functions that do one thing, named with verbs (`load_orders`, `send_invoice`). Prefer returning a new value to changing an argument in place.
- Use keyword arguments where a bare value would be unclear: `connect(timeout=5, retries=3)` says far more than `connect(5, 3)`. For on/off flags, make the parameter **keyword-only** (placed after a `*` in the parameter list) so callers have to write the name.
- Use `None` as the default for a parameter that should start as an empty list or dictionary. A default value is created once, when the function is defined, so `def f(a=[])` would share one list between every call.
- Return early with **guard clauses**: checks at the top of a function that deal with the special cases and leave immediately, so the main logic is not buried in nested `if` blocks.

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

Both functions give the same answers; the demo prints `0 10`. In the nested version, the reader has to keep three open conditions in mind, and each error message sits far from the test that triggers it. In the guard-clause version each problem is handled and dismissed on its own two lines, and the real rule ("free shipping to Portugal, 10 elsewhere") sits at the bottom with no indentation. The last line uses a **conditional expression**, `A if condition else B`, which picks one of two values.

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

**Reading this code block by block**

- **`with` for anything that must be cleaned up.** A **context manager** is an object that sets something up at the start of a `with` block and undoes it at the end, even if an error happens inside. Here `redirect_stdout` sends everything printed inside the block into an in-memory text buffer, then restores normal printing. So `captured` does not appear during the block; the next line prints it from the buffer. Files, locks and database connections follow the same pattern: `with open(path) as f:` closes the file for you.
- **Enums instead of magic values.** A **magic value** is a bare string or number whose meaning is not written down, such as `status = 2`. An **enumeration** (`Enum`) gives each allowed value a name. `auto()` numbers them for you. `Color.RED` prints as `Color.RED`, `.name` is `RED`, `Color["GREEN"]` looks a member up by name, `list(Color)` lists the members, and each member is a single object, so `is` works. A typo such as `Color.REED` fails at once with an error, while a typo in a magic string fails silently.
- **Named constants.** A value that never changes gets an `UPPER_CASE` name at the top of the module. Python does not enforce it; the capitals are a signal to readers.
- **`pathlib` instead of string paths.** `Path("data") / "raw" / "file.csv"` joins path parts with `/` and uses the correct separator on every operating system. Parts of the path are attributes: `.suffix` is `.csv`, `.stem` is `file`, `.parent` is `data/raw`.
- **A private sentinel.** Sometimes `None` is a perfectly valid value, so it cannot also mean "the caller passed nothing". `object()` creates a brand-new object that nothing else can be equal to, and testing `default is _MISSING` tells "no default given" apart from "the default is `None`". The demo returns the stored `None` for `"a"` and the explicit default `None` for `"b"`, printing `None None`; with no default at all, the function raises `KeyError`.

## Classes

- Give classes that mainly hold data the `@dataclass` decorator instead of hand-written `__init__`, `__repr__` and `__eq__` methods.
- Start with plain attributes. Add `@property` only when you need to validate or compute a value; callers' code does not have to change when you do.
- Implement the special "dunder" (double-underscore) methods so your objects work with `len`, `in`, `for`, `sorted` and `==`, as built-in types do.
- Prefer **composition** (an object holding other objects) and small `Protocol`s over deep inheritance trees.
- Do not write a class when a function, a dictionary or a named tuple will do. A class with one method and an `__init__` is usually a function in disguise.

```python-run
from dataclasses import dataclass, field

@dataclass(order=True, frozen=True)
class Card:
    rank: int
    suit: str = field(compare=False)

hand = [Card(12, "hearts"), Card(3, "spades"), Card(12, "clubs")]
print(max(hand), sorted(hand)[0], Card(3, "x") == Card(3, "y"), len({Card(1, "a"), Card(1, "b")}))
```

**Reading this code line by line**

- `@dataclass` writes `__init__`, `__repr__` and `__eq__` from the annotated fields. `order=True` also writes `<`, `<=`, `>` and `>=`, comparing fields in order. `frozen=True` makes instances read-only, which also makes them **hashable** (usable as dictionary keys and set members).
- `field(compare=False)` leaves `suit` out of all comparisons and out of the hash, so cards are compared by rank alone.
- `max(hand)` is `Card(rank=12, suit='hearts')`: two cards tie on rank 12, and `max` keeps the first one it saw.
- `sorted(hand)[0]` is the lowest card, `Card(rank=3, suit='spades')`.
- `Card(3, "x") == Card(3, "y")` is `True` because suit is ignored, and the set of two rank-1 cards has length 1 for the same reason.

## PEP 8 in two minutes

**PEP 8** is the official style guide for Python code: how to name things, indent, space and lay out a file. Following it means any Python programmer can read your code without adjusting to a personal style.

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

`snake_case` is lower-case words joined by underscores; `PascalCase` capitalises each word with no separator. The "stdlib" is the **standard library**, the modules that ship with Python. A **docstring** is the string literal on the first line of a function, class or module that describes it; PEP 257 is the companion guide for writing them.

Do not argue about style: let tools apply it. A **linter** reads code and reports likely mistakes and style breaches; a **formatter** rewrites code into a standard layout. **ruff** does both, very quickly; the older combination is **black** (formatter) plus **isort** (sorts imports). **mypy** and **pyright** are **type checkers** that read your type hints and report mismatches. Teams run these tools when a file is saved and again in **CI** (continuous integration, the automatic checks that run on every proposed change), and configure them in the project's `pyproject.toml` file.

## A worked refactoring

To **refactor** is to restructure code without changing what it does. Here is a function written "C-style", followed by an idiomatic version. Both return the `n` customers who spent the most on paid orders.

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

Both print `['ana', 'ben']`: ana paid 90 in total, ben 70, and cy's refunded order does not count. Walk through what changed:

1. `for i in range(len(orders)): order = orders[i]` became `for order in orders:`.
2. The "is the key there yet?" branch disappeared. A `Counter` treats a missing key as 0, so `totals[customer] += amount` works the first time too.
3. Building `[total, name]` pairs, sorting, reversing and slicing with a `while` loop became `most_common(n)`, a library method that is already tested.
4. A list comprehension pulls the names out of the `(name, total)` pairs, using `_` for the total that is not needed.
5. A docstring states the purpose, so a reader does not have to reverse-engineer it.

Twenty lines became six, and each of the six says something about the problem rather than about bookkeeping. The original also has a hidden quirk: on equal totals, `pairs.sort()` falls back to comparing names, then `reverse()` puts them in reverse alphabetical order, which is probably not what anyone intended.

## Idioms that are *anti*-patterns

An **anti-pattern** is a habit that looks reasonable but causes trouble. Each row names one and its idiomatic replacement.

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
| `d.keys()` only to iterate or test membership | `for k in d`, `k in d` |
| getters/setters everywhere | attributes, then `@property` if needed |
| `lambda` bound to a name | `def` |
| deep nesting | guard clauses, helper functions |
| reinventing `Counter`, `groupby`, `bisect`, `heapq` | use the standard library |

The reasons behind the less self-explanatory rows:

- A bare `except:` catches *everything*, including the `KeyboardInterrupt` raised when you press Ctrl+C, and `pass` then hides it: "errors should never pass silently".
- `from module import *` dumps unknown names into your file, so a reader cannot tell where a name came from and a later import can silently replace an earlier one.
- `type(x) == list` rejects subclasses of `list`; `isinstance` accepts them, and also accepts a tuple of types: `isinstance(x, (list, tuple))`.
- `lst = lst + [x]` builds a whole new list every time; `append` adds in place.
- `x in some_list` checks items one by one, so inside a loop it can turn a quick job into a slow one. A set answers membership questions in roughly constant time, however big it is.
- `list.pop(0)` shifts every remaining item one place to the left; a `deque` (double-ended queue) removes from the front without shifting.
- `f = lambda x: x * 2` gives the function the useless name `<lambda>` in error messages; `def f(x): return x * 2` is no longer and names it properly.

> [!INTERVIEW]
> Interviewers notice idiom fluency within the first few lines: `enumerate`/`zip` instead of index loops, a `set` for membership, `Counter`/`defaultdict` for tallies, `"".join`, tuple-key sorting, slicing for reversal, `with` for files, and early returns. It signals real experience and leaves you more time for the algorithm. When you use a concise idiom, say what it does and its cost ("`Counter` builds frequencies in O(n)").

"O(n)" in that last sentence is **Big-O notation**: it describes how the running time grows with the size of the input, here in proportion to the number of items, `n`. The performance lesson that follows explains it in detail.

## When an idiom goes too far

Idioms serve readability; they are not a contest to use as many as possible. Three warning signs:

- **The one-liner needs a comment to explain it.** If `{k: [v for v in vs if p(v)] for k, vs in d.items() if any(vs)}` takes a minute to decode, a short loop with a good variable name is more Pythonic, not less.
- **The idiom hides a cost.** `sorted(xs)[0]` is short but sorts the whole list to find one item; `min(xs)` does the same job in one pass.
- **The idiom changes behaviour.** Replacing `if count is None:` with `if not count:` looks tidier but starts treating 0 as missing.

## Pitfalls recap

- Testing `if not value:` when 0 or an empty string is a legitimate value; use `is None`.
- Forgetting that `zip` stops at the shortest input; pass `strict=True` when lengths must match.
- Reading `for ... else` as "if the loop was empty"; it means "if the loop did not `break`".
- Using a comprehension for side effects, or nesting so many clauses that nobody can read it.
- Catching every exception and moving on, which hides real bugs.
- A mutable default argument shared between calls.
- Hand-writing counting, grouping or top-k logic that `Counter`, `defaultdict` and `heapq` already provide.

## Summary

Pythonic code loops over items directly (with `enumerate` and `zip` when positions or parallel lists are needed), unpacks instead of indexing, tests truthiness and `is None` sensibly, builds strings with `join` and f-strings, uses comprehensions and the reducers `sum`, `any`, `all`, `min` and `max`, leans on `dict`, `set` and `collections`, manages resources with `with`, prefers EAFP and guard clauses, models data with dataclasses and enums, and leaves style to PEP 8 tools. Above all it stays readable: an idiom that obscures meaning is not Pythonic.

## Glossary

- **Idiom** - the natural, conventional way that fluent users of a language express something.
- **Pythonic** - written the way experienced Python programmers would write it, in the spirit of the Zen of Python.
- **PEP** - Python Enhancement Proposal, a numbered design document; PEP 8 is the style guide, PEP 20 the Zen.
- **Iterable** - anything a `for` loop can go through: lists, strings, dictionaries, files, ranges.
- **Parallel sequences** - several lists whose items line up by position.
- **Key function** - a function applied to each item to decide how items are compared, as in `sorted(xs, key=len)`.
- **Stable sort** - a sort that keeps equal items in their original order.
- **Sentinel** - a special value that signals "stop" or "nothing given".
- **Unpacking** - assigning the items of a sequence to several names at once.
- **Truthy / falsy** - counting as true / false in a condition; empty containers, 0 and `None` are falsy.
- **Chained comparison** - `a < b < c`, read as `a < b and b < c`.
- **f-string** - a string literal prefixed with `f` whose `{}` fields are evaluated and inserted.
- **Format specification** - the part after the colon in an f-string field, controlling width, alignment and decimals.
- **Immutable** - impossible to change after creation, like strings and tuples.
- **Comprehension** - a list, set or dict built from a loop written inside brackets.
- **Generator expression** - comprehension syntax in round brackets that produces items lazily.
- **Short-circuiting** - stopping evaluation as soon as the answer is known, as `any` and `all` do.
- **EAFP / LBYL** - "Easier to Ask Forgiveness than Permission" (try, then handle the error) versus "Look Before You Leap" (check, then act).
- **Dispatch table** - a dictionary mapping choices to the functions that handle them.
- **Guard clause** - an early check-and-return at the top of a function that handles a special case.
- **Conditional expression** - `A if condition else B`, choosing between two values.
- **Context manager** - an object used with `with` that guarantees setup and cleanup.
- **Magic value** - an unexplained literal string or number in code; replace it with a named constant or enum.
- **Enum** - a class whose members are a fixed set of named values.
- **Linter / formatter** - a tool that reports likely mistakes / a tool that rewrites code into a standard layout.
- **Refactor** - restructure code without changing its behaviour.
- **Anti-pattern** - a common habit that looks reasonable but causes problems.

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
