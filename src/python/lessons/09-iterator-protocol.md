# The iterator protocol

The `for` loop is the most-used statement in Python, and it works on lists, strings, dicts, files, sockets, database cursors, generators, `range`, `zip` and your own classes — all through one small protocol made of two methods. Knowing that protocol lets you write classes that plug into every iteration tool in the language, and it explains behaviours like "why can I only loop over this once?".

## Iterables versus iterators

These two words are not synonyms:

- An **iterable** is anything you can loop over. It has an `__iter__` method that returns a **fresh iterator** each time (or, as a fallback, a `__getitem__` that accepts 0, 1, 2, ... until `IndexError`). Lists, tuples, strings, dicts, sets, files and ranges are iterables.
- An **iterator** is the object that actually walks through the data. It has a `__next__` method that returns the next item or raises `StopIteration` when exhausted, and an `__iter__` method that returns **itself**.

Goodrich (§1.8) puts it neatly: an iterator manages one *pass* over a collection, while an iterable is the collection that can produce passes.

```python-run
nums = [10, 20, 30]           # iterable
it = iter(nums)               # calls nums.__iter__() -> a list_iterator
print(type(it).__name__)
print(next(it), next(it), next(it))   # next(it) calls it.__next__()
try:
    next(it)
except StopIteration:
    print("StopIteration: iterator exhausted")
print(iter(it) is it)         # an iterator's __iter__ returns itself
print(next(iter(nums)))       # a NEW iterator starts from the beginning
```

## What `for` actually does

```python
for x in iterable:
    body(x)
```

is roughly:

```python
_it = iter(iterable)
while True:
    try:
        x = next(_it)
    except StopIteration:
        break
    body(x)
```

```mermaid
sequenceDiagram
  participant Loop as for loop
  participant Able as iterable
  participant Tor as iterator
  Loop->>Able: iter()
  Able-->>Loop: new iterator
  loop until StopIteration
    Loop->>Tor: next()
    Tor-->>Loop: item
  end
  Tor-->>Loop: raises StopIteration
```

The same protocol drives `list(x)`, `tuple(x)`, `sum`, `max`, `sorted`, `zip`, `enumerate`, `map`, `filter`, `in` (for objects without `__contains__`), unpacking `a, b = x`, `"".join(x)`, comprehensions, `yield from`, and `dict(pairs)`.

## Single-pass iterators: the exhaustion trap

Because an iterator returns itself from `iter()`, looping over it twice gives nothing the second time. Many built-ins return iterators, not lists: `map`, `filter`, `zip`, `enumerate`, `reversed`, file objects, generators, `dict.items()`'s iterator, `itertools.*`.

```python-run
squares = map(lambda x: x * x, [1, 2, 3])
print(list(squares))
print(list(squares))     # [] — already consumed

pairs = zip("ab", [1, 2])
print(dict(pairs), dict(pairs))

z = zip([1, 2, 3], [4, 5, 6])
print(3 in z, list(z))   # 'in' consumed items up to the match
```

> [!WARNING]
> A function that iterates its argument twice (e.g., computes `sum(xs)` then loops again to normalise) silently misbehaves when given an iterator. Either document that you need a re-iterable collection, or materialise once with `xs = list(xs)`.

You can detect the difference: `iter(x) is x` is true for iterators and false for proper containers.

## Writing an iterator class

Let's reimplement a simplified `range`, following Goodrich's `Range` example (§2.3.5). We separate the **iterable** (the range object, which can be looped over many times) from the **iterator** (which tracks the position of one loop).

```python-run
class MyRange:
    """Iterable over start, start+step, ... stopping before stop."""
    def __init__(self, start, stop=None, step=1):
        if step == 0:
            raise ValueError("step cannot be 0")
        if stop is None:
            start, stop = 0, start
        self.start, self.stop, self.step = start, stop, step

    def __len__(self):
        return max(0, (self.stop - self.start + self.step - (1 if self.step > 0 else -1)) // self.step)

    def __getitem__(self, k):
        if k < 0:
            k += len(self)
        if not 0 <= k < len(self):
            raise IndexError("index out of range")
        return self.start + k * self.step

    def __iter__(self):
        return MyRangeIterator(self)        # fresh iterator every time

class MyRangeIterator:
    def __init__(self, r):
        self._r = r
        self._k = 0
    def __iter__(self):
        return self
    def __next__(self):
        if self._k >= len(self._r):
            raise StopIteration
        value = self._r[self._k]
        self._k += 1
        return value

r = MyRange(2, 11, 3)
print(list(r), list(r), len(r), r[-1])
print(list(MyRange(5)), list(MyRange(10, 0, -4)), list(MyRange(3, 3)))
print(sum(r), 8 in r, [x * 2 for x in r])
```

Note that `8 in r` works even without `__contains__`: Python falls back to iterating. A real `range` implements `__contains__` in O(1) arithmetic; you could too.

## A class that is its own iterator

Sometimes the object *is* a one-shot stream — like a file or a countdown. Then `__iter__` returns `self`:

```python-run
class Countdown:
    def __init__(self, n):
        self.n = n
    def __iter__(self):
        return self
    def __next__(self):
        if self.n <= 0:
            raise StopIteration
        self.n -= 1
        return self.n + 1

c = Countdown(3)
print(list(c), list(c))    # second pass is empty: it's an iterator
```

In practice you'd write either of these as a **generator function** (next lesson), which builds the iterator object for you in three lines. But interviewers like to check that you know the protocol underneath.

## The `__getitem__` fallback (legacy sequence protocol)

If a class has no `__iter__` but has `__getitem__`, `iter()` creates an iterator that calls `obj[0]`, `obj[1]`, ... until `IndexError`. That's how Goodrich's early `Vector` and `Range` examples become iterable "for free".

```python-run
class Squares:
    def __getitem__(self, i):
        if i >= 5:
            raise IndexError
        return i * i

print(list(Squares()), 9 in Squares())
```

## Two-argument `iter(callable, sentinel)`

`iter(f, sentinel)` calls `f()` repeatedly until it returns `sentinel`. It's perfect for reading fixed-size chunks:

```python-run
import io
from functools import partial

stream = io.BytesIO(b"abcdefghij")
for chunk in iter(partial(stream.read, 4), b""):
    print(chunk)
```

## `next` with a default

`next(it, default)` returns `default` instead of raising when the iterator is exhausted. It's the idiom for "first match or None":

```python-run
users = [{"name": "ana", "admin": False}, {"name": "ben", "admin": True}]
first_admin = next((u for u in users if u["admin"]), None)
print(first_admin)
print(next(iter([]), "empty"))
```

## Iterating dicts and files

- Iterating a dict yields **keys**; use `.items()` for pairs and `.values()` for values.
- Iterating a text file yields **lines** (with `\n`), read lazily — so you can process a 50 GB log with constant memory.
- `enumerate(it, start)` and `zip(a, b)` wrap iterators lazily.

## Lazy versus eager

Iterators are **lazy**: they compute each item on demand. That gives three superpowers:

1. **Memory**: process streams bigger than RAM.
2. **Infinite sequences**: `itertools.count()` never ends; you take what you need.
3. **Early exit**: `any`, `next`, and `break` stop the pipeline without computing the rest.

The cost: single pass, no `len`, no indexing. Convert with `list(...)` when you need those.

```python-run
import itertools
evens = (n for n in itertools.count() if n % 2 == 0)     # infinite
print(list(itertools.islice(evens, 5)))
print(any(n > 10**6 for n in itertools.count()))         # stops at 1000001
```

## Worked example: peekable iterator

Parsers often need to look at the next token without consuming it. Here's a wrapper that adds `peek()` to any iterator:

```python-run
class Peekable:
    _EMPTY = object()                # sentinel distinct from any real value (including None)

    def __init__(self, iterable):
        self._it = iter(iterable)
        self._buf = self._EMPTY

    def __iter__(self):
        return self

    def __next__(self):
        if self._buf is not self._EMPTY:
            v, self._buf = self._buf, self._EMPTY
            return v
        return next(self._it)

    def peek(self, default=None):
        if self._buf is self._EMPTY:
            try:
                self._buf = next(self._it)
            except StopIteration:
                return default
        return self._buf

p = Peekable([1, None, 3])
print(p.peek(), next(p), p.peek(), next(p), list(p), p.peek("done"))
```

The private `_EMPTY = object()` sentinel is a pattern worth stealing: it lets `None` be a legitimate value.

> [!INTERVIEW]
> "What's the difference between an iterable and an iterator?" — An iterable has `__iter__` returning a new iterator; an iterator has `__next__` (raising `StopIteration` at the end) and an `__iter__` that returns itself. Containers are iterables; iterators are single-pass cursors. Then show `m = map(...); list(m); list(m)` to demonstrate exhaustion.

## Under the hood: what the built-in iterators store

An iterator is a small object holding a reference to its source plus a cursor. For a list, the cursor is just an index — which explains precisely what goes wrong when you mutate a list during iteration:

```python-run
nums = [10, 20, 30, 40]
it = iter(nums)
print(next(it), next(it))            # cursor is now at index 2
nums.insert(0, 5)                    # everything shifts right by one
print(next(it))                      # index 2 now holds 20 again: an item is repeated
nums.clear()
print(list(it))                      # index is past the end: iteration just stops

it = iter([1, 2, 3])
print(it.__length_hint__())          # iterators may offer a size *hint* (used by list() to pre-allocate)
```

Removing an element while looping has the mirror effect: the items shift left, the index still advances, and one element is **skipped** — silently. Dicts and sets, whose internal layout can be rebuilt on insertion, detect the situation instead and raise `RuntimeError: ... changed size during iteration`.

`for` compiles to two bytecode instructions around your loop body — `GET_ITER` (call `iter()`) and `FOR_ITER` (call `next()` and jump out on `StopIteration`):

```python-run
import dis
def total(xs):
    t = 0
    for x in xs:
        t += x
    return t
print([i.opname for i in dis.get_instructions(total) if "ITER" in i.opname])
```

Because the `StopIteration` is consumed inside the interpreter's loop, exhausting an iterator in a `for` loop is cheap; you only see the exception when you call `next()` yourself.

## Sharing one iterator on purpose

Since `iter(iterator)` returns the same object, several consumers can pull from one stream. This is a feature you can exploit:

```python-run
from itertools import islice

lines = iter(["# header", "# units: m", "1.5", "2.5", "3.0"])

header = []
for line in lines:                   # consume the comment block...
    if not line.startswith("#"):
        first_value = line
        break
    header.append(line)
rest = [float(x) for x in lines]     # ...and continue where the first loop stopped
print(header, first_value, rest)

it = iter(range(10))
pairs = list(zip(it, it))            # the same iterator twice: consecutive pairs
print(pairs)

it = iter("abcdefg")
print([a + b + c for a, b, c in zip(it, it, it)], list(it))   # leftover 'g' was consumed by zip!
```

The last line shows a subtle cost: `zip` pulled `g` from the first argument before discovering that the second was exhausted, so `g` is lost. When leftovers matter, use `itertools.zip_longest` or `islice`.

## Iterable, iterator, sequence, generator: a comparison

| | `__iter__` | `__next__` | `len()` / indexing | re-iterable | lazy |
|---|---|---|---|---|---|
| **Sequence** (`list`, `tuple`, `str`, `range`) | new iterator | no | yes | yes | no (`range`: yes) |
| **Other containers** (`dict`, `set`) | new iterator | no | `len` only | yes | no |
| **Iterator** (`map`, `zip`, `enumerate`, file) | returns self | yes | no | **no** | yes |
| **Generator** (next lesson) | returns self | yes | no | **no** | yes |

`collections.abc` lets you test for these roles structurally:

```python-run
from collections.abc import Iterable, Iterator, Sequence, Sized
for obj in ([1, 2], (x for x in [1]), map(str, [1]), range(3), {1: 2}, "text", 42):
    print(f"{type(obj).__name__:<10} iterable={isinstance(obj, Iterable)!s:<5} "
          f"iterator={isinstance(obj, Iterator)!s:<5} sized={isinstance(obj, Sized)!s:<5} "
          f"sequence={isinstance(obj, Sequence)}")
```

## Debugging iterator problems

- **A loop body never runs, or a result is unexpectedly empty**: something upstream already consumed the iterator (a debugging `print(list(it))` is a classic way to *cause* this). Materialise once — `items = list(it)` — and use the list for both.
- **`TypeError: 'X' object is not iterable`**: the value isn't what you think (often `None` or an `int`); print its type. **`'list' object is not an iterator`**: you called `next()` on a list — wrap it with `iter()` first.
- **`TypeError: object of type 'generator' has no len()`** or "not subscriptable": convert with `list()`, or use `itertools.islice` to take a slice lazily.
- **Infinite loop in your own iterator class**: `__next__` never raises `StopIteration`.
- **Nested loops over your own container misbehave**: its `__iter__` returns `self`, so both loops share one cursor.

## Pitfalls recap

- Reusing an exhausted iterator (map/zip/filter/generators/files).
- Making a container's `__iter__` return `self` — it can then only be looped over once and nested loops over it break.
- Forgetting to raise `StopIteration` (infinite loop) or raising it from a generator (converted to `RuntimeError` since 3.7).
- Calling `len()` on an iterator — `TypeError`.
- Mutating a collection while iterating over it.

## Summary

`iter()` turns an iterable into an iterator; `next()` advances it; `StopIteration` ends it. `for` loops and almost every consuming built-in speak this protocol. Containers should return a fresh iterator from `__iter__`; iterators return themselves. Iterators are lazy and single-pass, which saves memory and enables infinite streams, at the cost of re-iteration.

```quiz
[
  {"q": "Which method must an iterator define to produce items?", "options": ["__iter__ only", "__next__", "__getitem__", "__len__"], "answer": 1,
   "explain": "__next__ returns the next item or raises StopIteration; iterators also define __iter__ returning self."},
  {"q": "`m = map(str, [1, 2]); list(m); list(m)` — what is the second list?", "options": ["['1', '2']", "[]", "None", "Error"], "answer": 1,
   "explain": "map returns an iterator; the first list() consumed it."},
  {"q": "For a container class, what should __iter__ return?", "options": ["self", "A new iterator object each call", "A list copy", "None"], "answer": 1,
   "explain": "Returning a fresh iterator lets the container be iterated many times and in nested loops."},
  {"q": "How does a for loop know to stop?", "options": ["It checks len()", "The iterator raises StopIteration", "It gets None", "It catches IndexError always"], "answer": 1,
   "explain": "The loop calls next() until StopIteration is raised, then exits quietly."},
  {"q": "`next((x for x in [] ), 'none')` returns:", "options": ["StopIteration", "'none'", "None", "[]"], "answer": 1,
   "explain": "The default argument of next() is returned when the iterator is exhausted."},
  {"q": "A class with only `__getitem__` (raising IndexError at the end):", "options": ["Can't be iterated", "Can be iterated via the legacy sequence protocol", "Needs __len__ too", "Is an iterator"], "answer": 1,
   "explain": "iter() falls back to calling __getitem__ with 0, 1, 2, ... until IndexError."},
  {"q": "Why is reading a file line by line with `for line in f` memory-efficient?", "options": ["Files are compressed", "The file object is a lazy iterator yielding one line at a time", "Python reads it into a list first", "It isn't"], "answer": 1,
   "explain": "File objects are iterators; only a buffer and the current line are in memory."}
]
```

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, §1.8 (Iterators and Generators), §2.3.4 (Iterators) and §2.3.5 (Example: Range Class); Python docs, *Library Reference* "Iterator Types" and *Tutorial* §9.8 "Iterators".
