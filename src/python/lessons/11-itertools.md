# itertools and lazy pipelines

The `itertools` module is a toolkit of fast, memory-efficient iterator building blocks, implemented in C. Combined with generators and built-ins like `zip`, `map`, `enumerate`, `sum` and `any`, it gives you an "iterator algebra" that replaces many hand-written loops — and in interviews it can turn a fiddly nested loop into one readable line. This lesson tours the module by category, explains each tool's laziness and cost, and shows how to build your own.

## Infinite iterators

| Tool | Produces |
|---|---|
| `count(start=0, step=1)` | `start, start+step, ...` forever |
| `cycle(iterable)` | the items repeated forever (it saves a copy) |
| `repeat(obj, times=None)` | `obj` forever, or `times` times |

Always pair infinite iterators with something that stops: `islice`, `zip` with a finite iterable, `takewhile`, or `break`.

```python-run
from itertools import count, cycle, repeat, islice
print(list(islice(count(10, 5), 4)))
print(list(zip("abcde", cycle([0, 1]))))
print(list(map(pow, range(5), repeat(2))))       # squares
print(list(repeat("x", 3)))
```

## Slicing and filtering

| Tool | Behaviour |
|---|---|
| `islice(it, stop)` / `islice(it, start, stop, step)` | lazy slicing of any iterator (no negative indices) |
| `takewhile(pred, it)` | items while `pred` is true, then stop |
| `dropwhile(pred, it)` | skip while `pred` is true, then yield everything |
| `filterfalse(pred, it)` | items where `pred` is false |
| `compress(data, selectors)` | items whose selector is truthy |

```python-run
from itertools import islice, takewhile, dropwhile, filterfalse, compress
data = [1, 3, 5, 6, 7, 9]
print(list(takewhile(lambda x: x % 2, data)))     # [1, 3, 5]
print(list(dropwhile(lambda x: x % 2, data)))     # [6, 7, 9]
print(list(filterfalse(lambda x: x % 3, data)))   # multiples of 3
print(list(compress("ABCDEF", [1, 0, 1, 0, 1, 1])))
print(list(islice("abcdefg", 1, None, 2)))
```

## Combining and grouping

| Tool | Behaviour |
|---|---|
| `chain(a, b, ...)`, `chain.from_iterable(its)` | concatenate iterables lazily |
| `zip_longest(a, b, fillvalue=None)` | like `zip` but runs to the longest |
| `groupby(it, key=None)` | consecutive runs of equal keys |
| `pairwise(it)` (3.10+) | overlapping pairs `(a,b), (b,c), ...` |
| `batched(it, n)` (3.12+) | tuples of length `n` (last may be shorter) |
| `tee(it, n)` | `n` independent iterators from one |
| `accumulate(it, func=add, initial=None)` | running totals (prefix sums) |
| `starmap(f, it)` | `f(*args)` for each tuple of args |

```python-run
from itertools import chain, zip_longest, accumulate, starmap, tee
import operator
print(list(chain([1, 2], "ab", range(2))))
print(list(chain.from_iterable([[1, 2], [3], []])))       # flatten one level
print(list(zip_longest("abc", [1], fillvalue="-")))
print(list(accumulate([3, 1, 4, 1, 5])))                   # prefix sums
print(list(accumulate([3, 1, 4, 1, 5], max)))              # running max
print(list(accumulate([1, 2, 3], operator.mul, initial=1)))
print(list(starmap(pow, [(2, 3), (3, 2)])))
a, b = tee(iter([1, 2, 3]))
print(list(a), list(b))
```

### `groupby` in detail

`groupby` groups **consecutive** items with the same key — it does not sort. To group all equal keys together, sort by the same key first. Each group is itself an iterator that shares the underlying source, so consume (or copy) it before advancing to the next group.

```python-run
from itertools import groupby
s = "aaabccdaa"
print([(k, len(list(g))) for k, g in groupby(s)])          # run-length encoding

words = ["apple", "bob", "avocado", "banana", "cherry"]
for first, group in groupby(sorted(words), key=lambda w: w[0]):
    print(first, list(group))

groups = list(groupby("aabb"))                              # pitfall: groups not consumed
print([(k, list(g)) for k, g in groups])                    # inner iterators already exhausted
```

The last line prints empty lists: by the time we call `list(g)`, `groupby` has advanced past those groups. Always materialise groups inside the loop.

### `pairwise` and `batched`

```python-run
import itertools, sys
temps = [20, 22, 21, 25]
if hasattr(itertools, "pairwise"):
    print([b - a for a, b in itertools.pairwise(temps)])
else:
    print([b - a for a, b in zip(temps, temps[1:])])

def batched(iterable, n):                 # fallback for Python < 3.12
    it = iter(iterable)
    while chunk := tuple(itertools.islice(it, n)):
        yield chunk
print(list(batched(range(7), 3)))
```

## Combinatorics

| Tool | Produces | Count for n items |
|---|---|---|
| `product(a, b, repeat=1)` | Cartesian product (nested loops) | `len(a)·len(b)` |
| `permutations(it, r=None)` | ordered arrangements of length r | `n!/(n−r)!` |
| `combinations(it, r)` | unordered selections, no repeats | `C(n, r)` |
| `combinations_with_replacement(it, r)` | unordered, repeats allowed | `C(n+r−1, r)` |

Results come in lexicographic order of input positions and are tuples.

```python-run
from itertools import product, permutations, combinations, combinations_with_replacement
import math
print(list(product("ab", [0, 1])))
print(list(product([0, 1], repeat=3))[:4], "...")      # all 3-bit strings
print(list(permutations("abc", 2)))
print(list(combinations(range(4), 2)))
print(list(combinations_with_replacement("ab", 2)))
print(math.comb(52, 5), math.perm(5, 2), math.factorial(5))
```

`product` flattens nested loops — handy for grid neighbours and breaking out of "nested" loops with one `break`:

```python-run
from itertools import product
target = 12
for a, b in product(range(1, 10), repeat=2):
    if a * b == target and a < b:
        print("found", a, b)
        break

directions = [(dr, dc) for dr, dc in product((-1, 0, 1), repeat=2) if (dr, dc) != (0, 0)]
print(len(directions), directions[:3])
```

> [!TIP]
> In interviews it's usually fine to use `combinations`/`permutations` for brute force or to generate test cases, but if the question is "generate all subsets/permutations", the interviewer wants to see backtracking. Offer both: "In production I'd use `itertools.permutations`; here's the recursive version."

## Built-ins that pair with itertools

- `enumerate(it, start=0)`, `zip(*its, strict=False)`, `map(f, *its)`, `filter(pred, it)`, `reversed(seq)` — all lazy.
- `sum`, `min`, `max`, `any`, `all`, `sorted`, `list`, `set`, `dict`, `"".join` — consumers.
- `functools.reduce` — custom folding.

## Building your own tools

The itertools documentation includes "recipes" — short functions built from the primitives. Writing them is excellent practice. A few classics:

```python-run
from itertools import islice, chain, groupby, tee, zip_longest
from collections import deque

def take(n, it):
    return list(islice(it, n))

def nth(it, n, default=None):
    return next(islice(it, n, None), default)

def flatten(list_of_lists):
    return chain.from_iterable(list_of_lists)

def unique_everseen(it, key=None):
    seen = set()
    for x in it:
        k = x if key is None else key(x)
        if k not in seen:
            seen.add(k)
            yield x

def sliding_window(it, n):
    it = iter(it)
    window = deque(islice(it, n - 1), maxlen=n)
    for x in it:
        window.append(x)
        yield tuple(window)

def grouper(it, n, fillvalue=None):
    args = [iter(it)] * n                 # n references to the SAME iterator
    return zip_longest(*args, fillvalue=fillvalue)

def all_equal(it):
    g = groupby(it)
    return next(g, True) and not next(g, False)

def consume(it, n=None):
    if n is None:
        deque(it, maxlen=0)               # exhaust at C speed
    else:
        next(islice(it, n, n), None)

print(take(3, "abcdef"), nth(range(10), 4), list(flatten([[1], [2, 3]])))
print(list(unique_everseen("AAAaBBcA", key=str.lower)))
print(list(sliding_window(range(5), 3)))
print(list(grouper("ABCDEFG", 3, "x")))
print(all_equal("aaa"), all_equal("aab"), all_equal(""))
```

`grouper` uses a beautiful trick: `[iter(it)] * n` creates a list with `n` references to the *same* iterator, so `zip` pulls consecutive items into each tuple. This is the one place where the list-multiplication aliasing "bug" is a feature.

### Implementing `groupby` yourself

A good exercise in understanding laziness: here's a simplified `groupby` returning materialised lists (the real one returns lazy sub-iterators):

```python-run
def my_groupby(iterable, key=None):
    key = key or (lambda x: x)
    it = iter(iterable)
    _end = object()
    cur = next(it, _end)
    while cur is not _end:
        k = key(cur)
        group = [cur]
        cur = next(it, _end)
        while cur is not _end and key(cur) == k:
            group.append(cur)
            cur = next(it, _end)
        yield k, group

print(list(my_groupby([1, 1, 2, 3, 3, 3, 1])))
print(list(my_groupby(["ant", "ape", "bee", "cat", "cow"], key=lambda w: w[0])))
```

## Cost model

All itertools functions are lazy and O(1) per item produced, with small memory, except: `cycle` and `tee` may store items (O(n) memory), `groupby` stores nothing beyond the current key, and the combinatoric iterators first store the input pool (O(n)) but produce exponentially many outputs. `list(permutations(range(12)))` has 479,001,600 tuples — don't.

## Worked example: top-3 consecutive streaks

"Given daily step counts, report the longest streak of days above 10,000 steps." With `groupby` it's one pass:

```python-run
from itertools import groupby
steps = [12000, 15000, 8000, 11000, 13000, 14000, 9000, 10500]
streaks = [len(list(g)) for above, g in groupby(steps, key=lambda s: s > 10_000) if above]
print(streaks, max(streaks, default=0))
```

And prefix sums with `accumulate` answer "sum of any range" in O(1) after O(n) preprocessing:

```python-run
from itertools import accumulate
nums = [3, -1, 4, 1, 5, -9, 2]
prefix = [0, *accumulate(nums)]
range_sum = lambda i, j: prefix[j + 1] - prefix[i]       # inclusive i..j
print(prefix, range_sum(2, 4), range_sum(0, 6) == sum(nums))
```

> [!INTERVIEW]
> Mentioning the right tool earns points: `groupby` for run-length encoding (remember it only groups consecutive items), `accumulate` for prefix sums, `product` for grid directions or brute force, `combinations` for "choose k", `chain.from_iterable` to flatten one level, `islice` to take from a generator, `zip(a, a[1:])` / `pairwise` for adjacent pairs.

## How the tools work: pure-Python equivalents

The documentation specifies each itertools function by an equivalent generator. Writing a few yourself is the best way to internalise their behaviour — and interviewers sometimes ask for exactly this.

```python-run
def my_chain(*iterables):
    for it in iterables:
        yield from it

def my_islice(iterable, stop):
    it = iter(iterable)
    for _ in range(stop):
        try:
            yield next(it)
        except StopIteration:
            return

def my_accumulate(iterable, func=lambda a, b: a + b):
    it = iter(iterable)
    try:
        total = next(it)
    except StopIteration:
        return
    yield total
    for x in it:
        total = func(total, x)
        yield total

def my_product(*pools):
    result = [[]]
    for pool in pools:                               # grow partial tuples one pool at a time
        result = [prefix + [x] for prefix in result for x in pool]
    for combo in result:
        yield tuple(combo)

def my_combinations(items, r):
    items = tuple(items)
    def build(start, chosen):
        if len(chosen) == r:
            yield tuple(chosen)
            return
        for i in range(start, len(items)):           # only move forward: no repeats, no reorderings
            yield from build(i + 1, chosen + [items[i]])
    yield from build(0, [])

import itertools
print(list(my_chain("ab", [1])), list(my_islice(itertools.count(), 3)), list(my_accumulate([1, 2, 3, 4])))
print(list(my_product("ab", [0, 1])) == list(itertools.product("ab", [0, 1])))
print(list(my_combinations("abcd", 2)) == list(itertools.combinations("abcd", 2)))
```

`my_combinations` is the backtracking template behind "generate all subsets of size k"; changing `i + 1` to `i` gives combinations with replacement, and iterating over all unused positions instead of `range(start, ...)` gives permutations.

Two facts follow from these definitions. First, the combinatoric tools work on **positions**, not values: if the input contains duplicates, so does the output (`combinations("aab", 2)` yields `('a','a')`, `('a','b')`, `('a','b')`). De-duplicate with a `set` or sort and skip equal neighbours. Second, `product` needs to replay its inputs, so it materialises each one — never pass it an infinite iterator.

## The cost of `tee`

`tee` buffers every item that one branch has seen and another has not. If you exhaust one branch before touching the other, the buffer holds the *entire* stream — at which point a plain `list` would be simpler and faster:

```python-run
from itertools import tee

def source():
    for i in range(5):
        print(f"  produce {i}")
        yield i

a, b = tee(source())
print("a:", next(a), next(a))        # two items produced and buffered for b
print("b:", next(b))                 # served from the buffer: nothing new is produced
print("a:", next(a))
```

Use `tee` only when the branches advance roughly in step (as in the classic `pairwise` recipe: `a, b = tee(it); next(b, None); zip(a, b)`).

## Lazy pipeline versus building lists: a comparison

```python-run
import itertools, tracemalloc

def squares_of_evens_eager(n, k):
    nums = list(range(n))
    evens = [x for x in nums if x % 2 == 0]
    squares = [x * x for x in evens]
    return squares[:k]

def squares_of_evens_lazy(n, k):
    evens = (x for x in range(n) if x % 2 == 0)
    squares = (x * x for x in evens)
    return list(itertools.islice(squares, k))

for fn in (squares_of_evens_eager, squares_of_evens_lazy):
    tracemalloc.start()
    result = fn(200_000, 3)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"{fn.__name__:<26} {result}  peak ~{peak / 1024:,.0f} KiB")
```

The lazy version touches six numbers and stops; the eager one builds three large lists to return three items. Laziness wins whenever you might stop early, or the data doesn't fit in memory. Eager lists win when you need the data more than once, need its length, or need to sort it — at which point laziness must end anyway (`sorted` consumes everything).

## Choosing the right tool

| You want | Use |
|---|---|
| all pairs `(i, j)` with `i < j` | `combinations(xs, 2)` |
| every ordering | `permutations(xs)` |
| nested loops over several ranges | `product(a, b, c)` |
| all subsets (power set) | `chain.from_iterable(combinations(xs, r) for r in range(len(xs) + 1))` |
| running totals / running max | `accumulate(xs)` / `accumulate(xs, max)` |
| runs of equal neighbours | `groupby(xs)` |
| group *all* equal keys | `defaultdict(list)` (no sort needed), or sort then `groupby` |
| first n / skip n | `islice(it, n)` / `islice(it, n, None)` |
| round-robin labels | `zip(items, cycle(labels))` |
| pad the shorter input | `zip_longest(a, b, fillvalue=...)` |

Note the grouping row: sorting just to feed `groupby` costs O(n log n), while a `defaultdict(list)` groups in O(n) and keeps first-seen order. Reach for `groupby` when the data is already sorted or when *consecutive* runs are what you actually mean.

## Pitfalls recap

- `groupby` without sorting first only groups adjacent equal keys.
- Advancing `groupby` before consuming a group empties that group.
- Infinite iterators without a stop condition hang your program.
- `tee` after you've started using the original iterator gives inconsistent results; don't touch the original.
- `islice` doesn't support negative indices.
- Combinatoric explosion: count before you materialise.

## Summary

`itertools` provides lazy building blocks: infinite generators (`count`, `cycle`, `repeat`), slicing/filtering (`islice`, `takewhile`, `dropwhile`, `compress`), combining (`chain`, `zip_longest`, `groupby`, `pairwise`, `batched`, `accumulate`, `tee`) and combinatorics (`product`, `permutations`, `combinations`). Compose them with generators and built-in consumers for clear, memory-efficient code.

```quiz
[
  {"q": "`[(k, len(list(g))) for k, g in groupby('aabaa')]` gives:", "options": ["[('a', 4), ('b', 1)]", "[('a', 2), ('b', 1), ('a', 2)]", "[('a', 2), ('b', 1)]", "Error"], "answer": 1,
   "explain": "groupby groups consecutive equal items only; the second run of a's is a separate group."},
  {"q": "Which tool computes prefix sums lazily?", "options": ["itertools.chain", "itertools.accumulate", "functools.reduce", "itertools.tee"], "answer": 1,
   "explain": "accumulate yields running totals (or running results of any binary function)."},
  {"q": "How many tuples does `combinations(range(5), 2)` produce?", "options": ["10", "20", "25", "5"], "answer": 0,
   "explain": "C(5, 2) = 10 unordered pairs."},
  {"q": "How do you take the first 5 items of an infinite generator g?", "options": ["g[:5]", "list(g)[:5]", "list(islice(g, 5))", "g.take(5)"], "answer": 2,
   "explain": "Generators don't support slicing; list(g) never ends. islice slices lazily."},
  {"q": "`list(chain.from_iterable([[1], [2, 3], []]))` is:", "options": ["[[1], [2, 3], []]", "[1, 2, 3]", "[1, [2, 3]]", "[1, 2, 3, None]"], "answer": 1,
   "explain": "chain.from_iterable concatenates the inner iterables, flattening one level."},
  {"q": "Why does `zip(*[iter(xs)] * 3)` chunk xs into triples?", "options": ["zip has a chunk mode", "All three arguments are the same iterator, so each tuple pulls 3 consecutive items", "It copies xs three times", "It doesn't"], "answer": 1,
   "explain": "List multiplication creates three references to one iterator; zip advances it three times per tuple."},
  {"q": "`product('ab', repeat=2)` yields how many tuples?", "options": ["2", "3", "4", "6"], "answer": 2,
   "explain": "It's the Cartesian product of 'ab' with itself: aa, ab, ba, bb."}
]
```

> **Source:** Python docs, *Library Reference* `itertools` — "Functions creating iterators for efficient looping" and "Itertools Recipes"; Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, §1.8–1.9.
