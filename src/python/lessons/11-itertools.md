# itertools and lazy pipelines

> **Before this lesson:** you need iterators and laziness from [The iterator protocol](#/lesson/python/py-iterator-protocol) and generator functions with `yield` and `yield from` from [Generators and yield from](#/lesson/python/py-generators). Lambdas and `key` functions come from [Scope, closures and lambdas](#/lesson/python/py-scope-closures).

## In plain words

`itertools` is a module in Python's standard library (the collection of modules that is installed together with Python) full of small, ready-made tools for working with streams of items. Each tool takes one or more iterables and returns a new iterator. One counts upwards for ever, one glues several streams end to end, one cuts a piece out of a stream, one groups neighbours that belong together, one produces every possible pairing.

A good picture is a box of plumbing parts: straight pipes, T-pieces, taps, filters. No single part does much. Screwed together they carry water from anywhere to anywhere, and the water only flows when somebody opens the tap at the end. The `itertools` parts are the same: they are **lazy**, meaning no item is produced until something at the end of the chain asks for it, so a chain uses almost no memory however long the stream is.

Why this matters for a job: these tools replace many hand-written loops with one readable line, and they are written in C, so they are fast. In interviews, naming the right one ("that is a job for `groupby`", "use `accumulate` for running totals") shows fluency. It matters as much to know their costs and traps, because some of them (permutations, for example) can produce astronomically many results.

Throughout the examples you will see `list(...)` wrapped around a tool. That is only there to force the lazy iterator to produce everything so it can be printed.

## Infinite iterators

| Tool | Produces |
|---|---|
| `count(start=0, step=1)` | `start, start+step, ...` forever |
| `cycle(iterable)` | the items repeated forever (it saves a copy) |
| `repeat(obj, times=None)` | `obj` forever, or `times` times |

An iterator that never runs out must always be combined with something that stops: `islice`, a `zip` with a finite partner, `takewhile`, or a `break` in the loop. Otherwise the program hangs.

```python-run
from itertools import count, cycle, repeat, islice
print(list(islice(count(10, 5), 4)))
print(list(zip("abcde", cycle([0, 1]))))
print(list(map(pow, range(5), repeat(2))))       # squares
print(list(repeat("x", 3)))
```

**Reading this code line by line**

- `count(10, 5)` would give 10, 15, 20, ... without end; `islice(..., 4)` takes the first four: `[10, 15, 20, 25]`.
- `cycle([0, 1])` repeats 0, 1, 0, 1, ... for ever. `zip` stops when its shorter partner, the five letters, runs out, so the letters are labelled alternately with 0 and 1.
- `map(pow, range(5), repeat(2))` calls `pow(0, 2)`, `pow(1, 2)`, ...: `map` with two iterables takes one argument from each, and `repeat(2)` supplies a 2 every time. The result is the squares `[0, 1, 4, 9, 16]`.
- `repeat("x", 3)` with a count gives the item three times.

## Slicing and filtering

| Tool | Behaviour |
|---|---|
| `islice(it, stop)` / `islice(it, start, stop, step)` | a lazy slice of any iterator (negative positions are not allowed, because an iterator has no known end) |
| `takewhile(pred, it)` | items for as long as `pred(item)` is true, then stop for good |
| `dropwhile(pred, it)` | skip items while `pred(item)` is true, then let everything through |
| `filterfalse(pred, it)` | the items for which `pred(item)` is false |
| `compress(data, selectors)` | the items of `data` whose matching selector is truthy |

A **predicate** (`pred` in the table) is a function that answers yes or no about one item.

```python-run
from itertools import islice, takewhile, dropwhile, filterfalse, compress
data = [1, 3, 5, 6, 7, 9]
print(list(takewhile(lambda x: x % 2, data)))     # [1, 3, 5]
print(list(dropwhile(lambda x: x % 2, data)))     # [6, 7, 9]
print(list(filterfalse(lambda x: x % 3, data)))   # multiples of 3
print(list(compress("ABCDEF", [1, 0, 1, 0, 1, 1])))
print(list(islice("abcdefg", 1, None, 2)))
```

The predicate `lambda x: x % 2` returns 1 (truthy) for odd numbers and 0 (falsy) for even ones. `takewhile` passes 1, 3, 5 and stops at the first even number, 6; it does not resume for the later odd numbers. `dropwhile` is its mirror: it skips the leading odd numbers and then passes everything, `[6, 7, 9]`, odd ones included. `filterfalse(lambda x: x % 3, data)` keeps the items whose remainder is 0, the multiples of 3: `[3, 6, 9]`. `compress` keeps the letters that sit above a 1: `['A', 'C', 'E', 'F']`. `islice("abcdefg", 1, None, 2)` starts at position 1 and takes every second letter: `['b', 'd', 'f']`.

## Combining and grouping

| Tool | Behaviour |
|---|---|
| `chain(a, b, ...)`, `chain.from_iterable(its)` | the iterables one after another, as a single stream |
| `zip_longest(a, b, fillvalue=None)` | like `zip`, but continues to the end of the longest input, padding the others |
| `groupby(it, key=None)` | runs of neighbouring items that share a key |
| `pairwise(it)` (3.10+) | overlapping neighbours `(a,b), (b,c), ...` |
| `batched(it, n)` (3.12+) | tuples of `n` items (the last one may be shorter) |
| `tee(it, n)` | `n` independent iterators over one source |
| `accumulate(it, func=add, initial=None)` | running results, by default running totals |
| `starmap(f, it)` | `f(*args)` for each tuple of arguments |

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

**Reading this code line by line**

- `chain` joins a list, a string and a range into one stream: `[1, 2, 'a', 'b', 0, 1]`.
- `chain.from_iterable` takes one iterable *of* iterables and joins the inner ones, which removes one level of nesting: `[1, 2, 3]`.
- `zip_longest` pads the short input with the fill value: `[('a', 1), ('b', '-'), ('c', '-')]`.
- `accumulate` yields the total so far after each item: `[3, 4, 8, 9, 14]`. Such running totals are called **prefix sums**. Given `max` as the combining function it yields the largest value so far, and given multiplication with `initial=1` it yields `[1, 1, 2, 6]`.
- `starmap(pow, [(2, 3), (3, 2)])` unpacks each tuple into arguments: `pow(2, 3)` and `pow(3, 2)`, giving `[8, 9]`.
- `tee` splits one iterator into two that can be consumed separately; both print `[1, 2, 3]`.

### `groupby` in detail

`groupby` walks through its input once and bundles **neighbouring** items that have the same key. It does not sort and it does not look ahead, so equal items that are not next to each other end up in separate groups. To gather all equal keys together, sort by the same key first. Each step gives a pair: the key, and a group. The group is itself a lazy iterator that reads from the same underlying source, so use it (or copy it into a list) before moving on to the next group.

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

The first print counts the length of each run of equal letters: `[('a', 3), ('b', 1), ('c', 2), ('d', 1), ('a', 2)]`. Note that `a` appears twice, because its two runs are not adjacent. Storing each character with the length of its run in this way is called **run-length encoding**, a simple form of compression. The loop then sorts the words so that equal first letters become neighbours, and prints one group per letter.

The last two lines are the trap. `list(groupby("aabb"))` advances through all the groups without reading any of them; by the time `list(g)` is called, each group's items have already been passed by, and the lists come out empty. Always turn a group into a list inside the loop, while it is the current group.

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

`pairwise` gives each item together with its right-hand neighbour, so the differences between consecutive temperatures are `[2, -1, 4]`. The `hasattr` test lets the demo also run on Python versions older than 3.10, using `zip(temps, temps[1:])`. The `batched` function below it is a home-made version for Pythons older than 3.12: `islice(it, n)` takes the next `n` items from the shared iterator, the walrus `:=` stores them in `chunk`, and the loop ends when an empty tuple comes back. The output is `[(0, 1, 2), (3, 4, 5), (6,)]`.

## Combinatorics

**Combinatorics** is the branch of mathematics that counts and lists arrangements and selections. Four tools cover the standard cases:

| Tool | Produces | Count for n items |
|---|---|---|
| `product(a, b, repeat=1)` | Cartesian product (nested loops) | `len(a)·len(b)` |
| `permutations(it, r=None)` | ordered arrangements of length r | `n!/(n−r)!` |
| `combinations(it, r)` | unordered selections, no repeats | `C(n, r)` |
| `combinations_with_replacement(it, r)` | unordered, repeats allowed | `C(n+r−1, r)` |

In the last column `n!` is the factorial (1 × 2 × ... × n) and `C(n, r)` is the number of ways to choose `r` items out of `n`. Every result is a tuple, and the results come out in an order based on the *positions* of the inputs.

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

- `product("ab", [0, 1])` pairs every letter with every number: `('a', 0), ('a', 1), ('b', 0), ('b', 1)`. It is what two nested `for` loops would produce, and it is called the **Cartesian product**.
- `product([0, 1], repeat=3)` is the product of the list with itself three times: all eight three-digit patterns of 0 and 1.
- `permutations("abc", 2)` lists arrangements of two different letters where order matters, so both `('a', 'b')` and `('b', 'a')` appear: six in all.
- `combinations(range(4), 2)` lists selections where order does not matter: six pairs, each once.
- `combinations_with_replacement("ab", 2)` also allows an item to be picked twice: `aa`, `ab`, `bb`.
- The `math` functions count without listing: there are 2,598,960 five-card hands from 52 cards, 20 ordered pairs from 5 items, and 5! = 120.

`product` turns nested loops into a single loop. That is handy for the neighbours of a cell in a grid, and it means one `break` is enough to leave what would otherwise be a loop inside a loop:

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

The first loop tries every pair of numbers from 1 to 9 and stops at the first with product 12 and `a < b`: `found 2 6`. The second builds the eight directions to the neighbours of a grid cell, as (row change, column change) pairs, by taking every combination of −1, 0 and 1 and leaving out `(0, 0)`, which is the cell itself.

> [!TIP]
> In interviews it is usually fine to use `combinations` or `permutations` for a brute-force solution or to generate test cases. But if the question *is* "generate all subsets" or "all permutations", the interviewer wants to see you write the backtracking yourself. Offer both: "In real code I would use `itertools.permutations`; here is the recursive version."

## Built-ins that pair with itertools

- `enumerate(it, start=0)`, `zip(*its, strict=False)`, `map(f, *its)`, `filter(pred, it)` and `reversed(seq)` are all lazy, like the `itertools` tools.
- `sum`, `min`, `max`, `any`, `all`, `sorted`, `list`, `set`, `dict` and `"".join` are **consumers**: they pull the items through and produce a final result.
- `functools.reduce` is the consumer for a custom way of combining.

## Building your own tools

The `itertools` documentation ends with a list of "recipes": short functions built out of the basic tools. Writing them yourself is excellent practice. Some classics:

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

What each recipe does:

- `take(n, it)` returns the first `n` items as a list; `nth(it, n)` skips `n` items and returns the next one (4 for `range(10)`).
- `flatten` removes one level of nesting.
- `unique_everseen` yields each item the first time it appears and remembers what it has seen in a set; with `key=str.lower`, `A` and `a` count as the same, so the output is `['A', 'B', 'c']`.
- `sliding_window` yields overlapping windows of `n` items using a `deque` with `maxlen`, as in the generators lesson.
- `grouper` cuts the input into chunks of `n`, padding the last one: `('A','B','C'), ('D','E','F'), ('G','x','x')`.
- `all_equal` asks `groupby` for a first group and checks that there is no second one; an empty input counts as all equal.
- `consume` runs an iterator to its end (or forward by `n` items) and throws the items away, using a `deque` that keeps nothing.

`grouper` uses a neat trick: `[iter(it)] * n` makes a list holding `n` references to the *same* iterator. `zip_longest` takes one item from each of its arguments per tuple, and since all its arguments are one iterator, each tuple receives `n` consecutive items. This is the one place where the aliasing produced by multiplying a list, the cause of the grid bug in the first lesson, is exactly what is wanted.

### Implementing `groupby` yourself

A good exercise in understanding these tools is to write a simplified `groupby`. This version returns each group as a finished list (the real one returns lazy group iterators):

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

`cur` holds the item being looked at, and `_end` is a private sentinel object meaning "the input is finished". The outer loop starts a new group with the current item and its key. The inner loop keeps taking items while their key equals the group's key. When a different key (or the end) arrives, the group is yielded and the outer loop starts the next one with the item that did not fit. The first test prints `[(1, [1, 1]), (2, [2]), (3, [3, 3, 3]), (1, [1])]`.

## Cost model

Every `itertools` function is lazy, takes O(1) time per item it produces, and uses little memory, with these exceptions. `cycle` and `tee` may have to store items, up to O(n) memory. The combinatoric tools first store their whole input (O(n)) and can then produce exponentially many outputs. `groupby` stores only the current key. To get a feeling for the numbers: `list(permutations(range(12)))` would hold 479,001,600 tuples. Do not do that.

## Worked example: top-3 consecutive streaks

The task: "given daily step counts, report the longest unbroken run of days above 10,000 steps." With `groupby` it is a single pass:

```python-run
from itertools import groupby
steps = [12000, 15000, 8000, 11000, 13000, 14000, 9000, 10500]
streaks = [len(list(g)) for above, g in groupby(steps, key=lambda s: s > 10_000) if above]
print(streaks, max(streaks, default=0))
```

The key function turns each day into `True` (above the mark) or `False`. `groupby` then bundles neighbouring days with the same answer. The comprehension keeps only the `True` groups and measures each one: `[2, 3, 1]`, so the longest run is 3. `max(..., default=0)` avoids an error if there is no such day at all.

Prefix sums built with `accumulate` answer "what is the sum of items `i` to `j`?" in O(1), after one O(n) pass to prepare:

```python-run
from itertools import accumulate
nums = [3, -1, 4, 1, 5, -9, 2]
prefix = [0, *accumulate(nums)]
range_sum = lambda i, j: prefix[j + 1] - prefix[i]       # inclusive i..j
print(prefix, range_sum(2, 4), range_sum(0, 6) == sum(nums))
```

`prefix[k]` holds the sum of the first `k` numbers, with a 0 in front for "the sum of none". The sum of positions `i` to `j` inclusive is then the total up to `j` minus the total before `i`: `prefix[j + 1] - prefix[i]`. For positions 2 to 4 (the values 4, 1, 5) this gives 10.

> [!INTERVIEW]
> Naming the right tool earns points: `groupby` for run-length encoding (remember it groups neighbours only), `accumulate` for prefix sums, `product` for grid directions or brute force, `combinations` for "choose k", `chain.from_iterable` to flatten one level, `islice` to take from a generator, `zip(a, a[1:])` or `pairwise` for adjacent pairs.

## How the tools work: pure-Python equivalents

The official documentation defines each `itertools` function by showing an equivalent generator written in plain Python. Writing a few yourself is the best way to make their behaviour stick, and interviewers sometimes ask for exactly this.

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

- `my_chain` delegates to each input in turn with `yield from`.
- `my_islice` takes up to `stop` items, ending quietly if the input runs out sooner.
- `my_accumulate` yields the first item, then keeps combining the running value with each new item.
- `my_product` grows partial results one input at a time: every partial list so far is extended by every item of the next input.
- `my_combinations` builds each selection step by step. The inner generator `build` knows the position it may choose from (`start`) and what has been chosen so far. It only ever moves forward through the positions, which is what prevents both repeats and reorderings.

The two comparison lines print `True`: the home-made versions agree with the library.

`my_combinations` is the backtracking pattern behind "generate all subsets of size k". Changing `i + 1` to `i` gives combinations with replacement, and looping over all unused positions in place of `range(start, ...)` gives permutations.

Two facts follow from these definitions. First, the combinatoric tools work on **positions**, not values: if the input contains duplicates, so does the output (`combinations("aab", 2)` yields `('a','a')`, `('a','b')`, `('a','b')`). Remove duplicates with a `set`, or sort and skip equal neighbours. Second, `product` has to go through its inputs repeatedly, so it stores each one in full; never give it an endless iterator.

## The cost of `tee`

`tee` gives several branches over one source. To do that it has to store (**buffer**) every item that one branch has already taken and another has not yet seen. If you run one branch to its end before touching the other, the buffer holds the *entire* stream, and a plain `list` would have been simpler and faster.

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

The `produce` lines show when the source is really asked for an item. Branch `a` takes two items, so 0 and 1 are produced. Branch `b` then asks for its first item and no `produce` line appears: it was served from the buffer. Only when `a` asks for a third item is something new produced.

Use `tee` only when the branches move forward more or less together, as in the classic recipe for `pairwise`: `a, b = tee(it); next(b, None); zip(a, b)`.

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

Both functions return the squares of the first three even numbers below `n`. `tracemalloc` is a standard module that measures how much memory Python code allocates. The lazy version looks at a handful of numbers and stops; the eager one builds three large lists in order to return three items, and its peak memory is thousands of times higher.

Laziness wins whenever you might stop early or the data does not fit in memory. Eager lists win when you need the data more than once, need its length, or need to sort it; at that point laziness has to end anyway, since `sorted` consumes everything.

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

Note the grouping row. Sorting only in order to feed `groupby` costs O(n log n), while a `defaultdict(list)` groups in O(n) and keeps the order of first appearance. Use `groupby` when the data is already sorted, or when *consecutive* runs are what you really mean.

## Pitfalls recap

- `groupby` without sorting first groups only adjacent equal keys.
- Moving `groupby` forward before consuming a group empties that group.
- An endless iterator without a stopping condition hangs the program.
- After calling `tee`, do not keep using the original iterator; the branches would miss the items it takes.
- `islice` does not accept negative positions.
- Combinatoric explosion: count the results (with `math.comb` or `math.perm`) before you build them.

## Summary

`itertools` provides lazy building blocks: endless producers (`count`, `cycle`, `repeat`), slicing and filtering (`islice`, `takewhile`, `dropwhile`, `compress`), combining (`chain`, `zip_longest`, `groupby`, `pairwise`, `batched`, `accumulate`, `tee`) and combinatorics (`product`, `permutations`, `combinations`). Connect them with generators and the built-in consumers for clear code that uses little memory.

## Glossary

- **Standard library** - the modules that are installed together with Python.
- **Lazy** - producing each item only when it is requested.
- **Predicate** - a function that answers true or false about one item.
- **Consumer** - a function such as `sum` or `list` that pulls items through and returns a final result.
- **`islice`** - a lazy slice of any iterator.
- **`chain`** - several iterables joined into one stream.
- **`groupby`** - bundles neighbouring items with equal keys.
- **Run-length encoding** - storing each run of equal items as (item, length).
- **Prefix sum** - the total of all items up to a position; produced by `accumulate`.
- **`tee` / buffer** - a tool that splits one iterator into several / the store of items some branch has not yet seen.
- **Combinatorics** - counting and listing arrangements and selections.
- **Cartesian product** - every pairing of items from several inputs; what nested loops produce.
- **Permutation** - an arrangement in which order matters.
- **Combination** - a selection in which order does not matter.
- **Factorial (`n!`)** - the product 1 × 2 × ... × n.
- **Recipe** - a short helper function built from `itertools` primitives.

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
