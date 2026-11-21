# Performance, profiling and memory

> **Before this lesson:** you should be comfortable with lists, tuples and strings ([Lists, tuples and strings](#/lesson/python/py-sequences)), dictionaries and sets ([Dictionaries and sets](#/lesson/python/py-dicts-sets)), `deque` and `Counter` ([collections](#/lesson/python/py-collections)), heaps ([heapq, bisect, sorting and math](#/lesson/python/py-heapq-bisect-sorting)), generators ([Generators and yield from](#/lesson/python/py-generators)), `lru_cache` ([Decorators and functools](#/lesson/python/py-decorators)) and basic classes ([Classes and instances](#/lesson/python/py-classes)). The idioms in [Pythonic idioms](#/lesson/python/py-idioms) come up again here with their costs attached. Big-O notation is explained from scratch below.

## In plain words

**Performance** is how much time and memory a program needs to do its job. **Profiling** is measuring where that time and memory actually go, instead of guessing.

Think about a slow morning commute. You could buy a faster car, but first it is worth timing each part of the trip. If you lose twenty minutes waiting at one junction, a faster car saves almost nothing; a different route saves those twenty minutes. Programs behave the same way. Usually a few lines account for most of the running time, and the biggest win comes from changing the *route* (the method, or algorithm) rather than making each step a little quicker.

This lesson teaches a working method that professionals use:

1. Know roughly what the common built-in operations cost.
2. **Measure before optimising**, to find the slow part.
3. Fix the method first, then use Python-specific techniques.
4. Understand where memory goes.

Why this matters for a job: every coding interview asks "what is the complexity of your solution?" and often "how would you make it faster?". At work, a slow endpoint costs users and money, and a program that runs out of memory crashes. Knowing how to measure, and which fixes pay off, separates a guess from an engineering decision.

## Why Python is "slow", and why it often does not matter

Your Python source code is first translated into **bytecode**, a compact list of simple instructions, and then an **interpreter** (a program that reads and carries out those instructions one at a time) runs it. The standard interpreter is called **CPython** because it is written in the C programming language. Running instructions one by one has an overhead, so a loop written in pure Python is often 10 to 100 times slower than the same loop compiled from C.

"Python is slow" is still only half true, for two reasons:

- **Built-in functions and many libraries are written in C.** When you call `sum(data)`, `sorted(data)` or a NumPy function, the loop happens inside fast C code, not in the Python interpreter. Idiomatic Python leans on these.
- **The algorithm matters far more than the language.** A smart method in Python easily beats a clumsy method in C once the input is large.

## Rule zero: measure

Intuition about performance is wrong surprisingly often. A **bottleneck** is the part of a program that limits its overall speed, like the narrow neck of a bottle that limits how fast it pours. The discipline is:

1. Make it correct, with tests.
2. Decide whether it is actually too slow, using a realistic input.
3. **Profile** to find the bottleneck. Typically a few lines account for most of the time.
4. Fix that, with the biggest lever first: algorithm, then data structure, then library, then micro-optimisation.
5. Measure again, and keep the tests passing.

A **micro-optimisation** is a small local change, such as rewriting one expression, that saves a little time per operation. The computer scientist Donald Knuth famously warned that "premature optimization is the root of all evil": tweaking code before you know it matters wastes effort and makes code harder to read. The other half of the lesson is equally true, though: ignoring a loop that does `n × n` work is a disaster once it meets a million rows.

## Big-O notation in five minutes

**Big-O notation** describes how the work an operation does *grows* as its input grows. The letter `n` stands for the size of the input, such as the number of items in a list. Big-O ignores constant factors and small details and keeps only the growth pattern.

| Big-O | Name | Everyday example | Steps for n = 1,000 | Steps for n = 1,000,000 |
|---|---|---|---|---|
| O(1) | constant | opening a book at a bookmark | 1 | 1 |
| O(log n) | logarithmic | finding a word in a dictionary by halving | about 10 | about 20 |
| O(n) | linear | reading every page once | 1,000 | 1,000,000 |
| O(n log n) | "n log n" | sorting a deck of cards efficiently | about 10,000 | about 20,000,000 |
| O(n²) | quadratic | comparing every page with every other page | 1,000,000 | 1,000,000,000,000 |

The last column is the point. A quadratic method that feels instant on a thousand items needs a million times longer on a million items. That is why, in interviews and at work, the first question about any loop is "what does each step cost, and how many steps are there?"

Two more words you will meet in the table below:

- **Amortised** cost is the average cost per operation over a long sequence of operations. Appending to a Python list is usually instant, but now and then the list runs out of room and must move into a bigger block of memory, copying everything. Because the list grows by a proportion each time, those occasional copies average out to a constant cost per append: amortised O(1).
- **Average case** means "what you can expect for typical data". Dictionary and set lookups are O(1) on average; in rare unlucky cases (many keys colliding in the same slot of the hash table) they can be slower.

## Big-O of the built-ins

Here are the costs collected in one place for CPython. `n` is the size of the container and `k` the size of the other operand. A **deque** (double-ended queue, from `collections`) is a sequence that is fast to add to and remove from at both ends.

| Operation | list | deque | dict / set | str |
|---|---|---|---|---|
| index `x[i]` | O(1) | O(n) middle, O(1) ends | — | O(1) |
| append / add at end | O(1)* | O(1) | O(1)* | O(n) (new string) |
| insert / pop at front | **O(n)** | O(1) | — | O(n) |
| pop at end | O(1) | O(1) | — | — |
| membership `in` | **O(n)** | O(n) | **O(1)** avg | O(n) substring |
| lookup / store by key | — | — | O(1) avg | — |
| delete by value / key | O(n) | O(n) | O(1) avg | — |
| slice `x[a:b]` | O(b−a) | — | — | O(b−a) |
| concatenate `+` | O(n+k) | — | — | O(n+k) |
| copy | O(n) | O(n) | O(n) | O(1)** |
| `len` | O(1) | O(1) | O(1) | O(1) |
| `min`/`max`/`sum` | O(n) | O(n) | O(n) | O(n) |
| sort | O(n log n) | — | — | — |

\* amortised. \*\* strings are immutable, so a "copy" shares the same object.

How to read the bold entries, which cause most real slowdowns:

- **Inserting or popping at the front of a list is O(n).** A list stores its items side by side in memory. Removing the first one means sliding every other item one place to the left. A deque avoids this.
- **`in` on a list is O(n).** Python has to check items one by one. A set or dict jumps straight to the right slot using a **hash**, a number computed from the value, so membership is O(1) on average.

Other useful costs: `heapq.heappush` and `heappop` are O(log n) and `heapify` is O(n); `bisect` searches in O(log n) but `insort` is O(n) because it must shift items to insert; `"".join` is O(total length); `x in range(...)` is O(1), since Python can answer with arithmetic; set union is O(n+k) and intersection O(min(n, k)); `collections.Counter(xs)` is O(n); and `sorted(xs)[:k]` is O(n log n) while `heapq.nsmallest(k, xs)` is O(n log k).

Explore the growth rates interactively and notice how quickly the curves separate as the input grows:

<div class="widget" data-widget="bigo"></div>

### Hidden quadratic behaviour

The classic performance bugs are linear operations hidden inside loops. A loop that runs `n` times, doing O(n) work each time, does O(n²) work in total. This demo times several such pairs. A small helper, `timed`, runs a function and prints how long it took.

```python-run
import time

def timed(label, fn):
    t = time.perf_counter()
    fn()
    print(f"{label:<34}{(time.perf_counter() - t) * 1000:8.1f} ms")

n = 4000
data = list(range(n))
lookup_list, lookup_set = list(range(n)), set(range(n))

timed("x in list, n times   O(n^2)", lambda: [x in lookup_list for x in data])
timed("x in set, n times    O(n)", lambda: [x in lookup_set for x in data])

def front_insert():
    out = []
    for x in data:
        out.insert(0, x)                       # shifts everything each time

def append_reverse():
    out = []
    for x in data:
        out.append(x)
    out.reverse()

timed("insert(0, x) loop    O(n^2)", front_insert)
timed("append + reverse     O(n)", append_reverse)

def concat():
    out = []
    for x in data:
        out = out + [x]                        # builds a new list every iteration

timed("out = out + [x]      O(n^2)", concat)
timed("list.count in a loop O(n^2)", lambda: [data.count(x) for x in data[:400]] * 1)
```

**Reading this code line by line**

- `time.perf_counter()` reads a precise clock. Taking it before and after a call and subtracting gives the elapsed seconds; multiplying by 1000 gives milliseconds. `{label:<34}` pads the label to 34 characters so the numbers line up.
- `lambda: [...]` wraps an expression in a tiny function so `timed` can call it.
- The first pair asks "is `x` in the collection?" 4,000 times. With a list each question scans up to 4,000 items; with a set each question is one hash lookup.
- `out.insert(0, x)` puts each new item at the front, which shifts every existing item. `append` followed by one `reverse` at the end gives the same list with far less work.
- `out = out + [x]` builds a brand-new list on every step, copying all the old items. `out.append(x)` would add in place.
- `data.count(x)` scans the whole list to count one value; doing that inside a loop multiplies the cost.

Your exact numbers depend on the machine (and the browser), but the pattern is reliable: each O(n²) line takes tens to hundreds of times longer than its O(n) partner, and the gap widens as `n` grows.

Other disguises of the same bug: `s += piece` over many pieces, loops of `del lst[0]` or `pop(0)`, slicing inside recursion (`f(xs[1:])` copies the list at every level), `lst.index(x)` or `lst.remove(x)` in loops, calling `sorted()` inside a loop, and `if key in d.values()` (the values of a dict are not hashed, so that test scans them).

## Timing code: `timeit` and `perf_counter`

`time.perf_counter()` is a **monotonic** clock (it never jumps backwards, even if the computer's date is adjusted) with high resolution. It is right for coarse timing of a whole operation. For a **micro-benchmark**, a measurement of a tiny piece of code, use the `timeit` module. It runs the snippet many times so that the total is long enough to measure accurately, and it switches off **garbage collection** (Python's periodic search for unused memory, explained in the next lesson) during timing so that a collection does not land in one run by chance.

```python-run
import timeit

setup = "data = list(range(1000))"
candidates = {
    "for loop + append": "out = []\nfor x in data:\n    out.append(x * 2)",
    "list comprehension": "[x * 2 for x in data]",
    "map + lambda": "list(map(lambda x: x * 2, data))",
}
for name, stmt in candidates.items():
    best = min(timeit.repeat(stmt, setup, number=300, repeat=3))
    print(f"{name:<20}{best / 300 * 1e6:8.1f} µs per run")
```

**Reading this code line by line**

- `setup` is code that runs once before timing; it builds the test data and is not counted.
- `candidates` maps a description to the code being timed, written as a string. `\n` inside the string is a line break, so the first entry is a three-line loop.
- `timeit.repeat(stmt, setup, number=300, repeat=3)` runs the statement 300 times in a row, measures the total, and does that three separate times, returning three totals.
- `min(...)` keeps the fastest of the three totals. The fastest run is the one least disturbed by other activity on the computer, so it is the best estimate of the code's own cost.
- Dividing by 300 gives seconds per run; multiplying by one million gives microseconds (µs, millionths of a second).

Typically the comprehension is a little faster than the explicit loop, because it avoids looking up and calling `out.append` on each step, and `map` with a `lambda` is the slowest of the three, because it calls a Python function for every item. The differences are modest; this is micro-optimisation territory.

From the shell, the same tool runs as a command: `python -m timeit -s "data = list(range(1000))" "[x * 2 for x in data]"`. Three habits make benchmarks trustworthy: report the **minimum** of several repeats, use realistic input sizes, and remember that results vary between machines and Python versions. Python 3.11 and later are substantially faster than 3.10 because of the *specialising adaptive interpreter*, which notices the types an instruction keeps seeing and swaps in a faster version of that instruction.

## Profiling: where does the time go?

A **profiler** watches a program run and reports where the time went. `cProfile`, in the standard library, records every function call: how many times each function was called (`ncalls`), the time spent in the function's own code (`tottime`), and the time including everything it called (`cumtime`, cumulative time).

```python-run
import cProfile, pstats, io

def is_prime(n):
    if n < 2:
        return False
    for d in range(2, int(n ** 0.5) + 1):
        if n % d == 0:
            return False
    return True

def count_primes(limit):
    return sum(1 for n in range(limit) if is_prime(n))

def report():
    return {"small": count_primes(2_000), "large": count_primes(20_000)}

profiler = cProfile.Profile()
profiler.enable()
report()
profiler.disable()

out = io.StringIO()
pstats.Stats(profiler, stream=out).strip_dirs().sort_stats("cumulative").print_stats(5)
print(out.getvalue()[:900])
```

**Reading this code line by line**

- `is_prime(n)` tests whether `n` is prime by trying every divisor up to its square root. `count_primes` counts primes below a limit, and `report` does that twice.
- `cProfile.Profile()` creates a profiler; `enable()` starts recording, `disable()` stops it. Only the call to `report()` between them is measured.
- `pstats.Stats(...)` turns the recording into a table. `strip_dirs()` shortens file names, `sort_stats("cumulative")` puts the functions with the largest cumulative time first, and `print_stats(5)` prints the top five rows into the `StringIO` text buffer `out`.

In the output, `report` is at the top with the whole cumulative time, because everything happens inside it. Further down, `is_prime` shows `ncalls` of 22000 (once for every number below 2,000 and below 20,000) and the largest `tottime`: almost all the time is spent in its own loop. That is the bottleneck. You now know that speeding up `count_primes` means making `is_prime` cheaper or calling it less often (a sieve that marks multiples would do both).

Read the table from the top. Sort by `cumulative` to see which high-level call dominates; sort by `tottime` to find the function whose own code burns the time. From the command line:

```bash
python -m cProfile -s cumulative script.py | head -30
python -m cProfile -o out.prof script.py     # then inspect with pstats or 'snakeviz out.prof'
```

Other tools worth knowing: **py-spy**, a *sampling* profiler that peeks at a running program many times per second instead of recording every call, so it adds almost no overhead and can be attached to a live server; **line_profiler**, which times individual lines; **scalene**, which reports CPU time and memory together; and **pytest-benchmark**, which turns benchmarks into tests that fail if code gets slower.

## Speeding things up, biggest lever first

### 1. A better algorithm or data structure

An **algorithm** is a step-by-step method for solving a problem; a **data structure** is a way of organising data, such as a list, a set or a heap. Changing either one beats every other technique. Replacing an O(n²) scan with a dictionary or set lookup turns minutes into milliseconds.

The demo counts pairs of numbers that add up to exactly one million, first by checking every pair, then with a set.

```python-run
import time, random
random.seed(1)
nums = random.sample(range(10**6), 3000)
target_pairs = 0

t = time.perf_counter()
brute = sum(1 for i in range(len(nums)) for j in range(i + 1, len(nums)) if nums[i] + nums[j] == 1_000_000)
t_brute = time.perf_counter() - t

t = time.perf_counter()
seen, fast = set(), 0
for x in nums:
    if 1_000_000 - x in seen:
        fast += 1
    seen.add(x)
t_fast = time.perf_counter() - t
print(brute == fast, f"brute {t_brute * 1000:.0f} ms vs set {t_fast * 1000:.2f} ms")
```

**Reading this code line by line**

- `random.seed(1)` makes the "random" numbers the same on every run, so results are repeatable. `random.sample(range(10**6), 3000)` picks 3,000 different numbers below one million.
- The **brute-force** version (trying every possibility) checks each pair `(i, j)` with `j` after `i`: about 4.5 million pairs, O(n²).
- The fast version walks the list once. For each `x` it asks "have I already seen the partner `1_000_000 - x`?" That question is a set lookup, O(1) on average, so the whole loop is O(n).
- The output starts with `True`, confirming both methods give the same count, followed by the two times. The set version is typically hundreds of times faster, and the ratio grows with the input size.

This is the famous "two sum" interview pattern: trade a little memory (the set) for a huge saving in time.

### 2. Push loops into C

Built-ins and standard-library functions run their loops in C. Prefer `sum`, `min`, `max`, `any`, `all`, `sorted`, `str.join`, `map`, comprehensions, `collections.Counter`, `itertools`, slicing, and `in` on sets over hand-written Python loops. For arrays of numbers, **NumPy** is a library whose arrays store raw numbers side by side and whose operations loop in C over the whole array at once, a style called **vectorisation**. It is typically 10 to 100 times faster than a Python loop:

```python-run
import timeit
setup = "data = list(range(100_000))"
print("manual loop:", round(min(timeit.repeat("t = 0\nfor x in data:\n    t += x", setup, number=20, repeat=3)) / 20 * 1000, 2), "ms")
print("sum(data):  ", round(min(timeit.repeat("sum(data)", setup, number=20, repeat=3)) / 20 * 1000, 2), "ms")
try:
    import numpy as np
    setup_np = "import numpy as np; arr = np.arange(100_000)"
    print("numpy sum:  ", round(min(timeit.repeat("arr.sum()", setup_np, number=20, repeat=3)) / 20 * 1000, 3), "ms")
except ImportError:
    print("numpy not installed here")
```

All three lines add up the same 100,000 numbers. The hand-written loop executes several bytecode instructions per item; `sum(data)` runs one C loop over the list, typically several times faster; `arr.sum()` runs a C loop over raw numbers with no Python objects involved, typically faster again by a large factor. The `try`/`except ImportError` keeps the demo working on a machine without NumPy.

### 3. Do not repeat work

- **Cache.** Store results so they are computed once. `functools.lru_cache` or `cache` does this for **pure functions** (functions whose result depends only on their arguments and that change nothing else). Precompute lookup tables; **hoist** computations that give the same answer on every pass out of a loop, which means moving them above it; compile regular expressions once instead of on every call.
- **Be lazy.** Generators produce items on demand and avoid building intermediate lists; `any` and `next` stop at the first answer.
- **Batch input and output.** **I/O** (input/output: reading files, talking to a database or the network) is slow per request. One database query for 1,000 rows beats 1,000 queries for one row each; build text with `"".join` and write it once instead of writing many small pieces.

### 4. Concurrency and parallelism

A program is **I/O-bound** when it spends most of its time waiting for files, databases or the network, and **CPU-bound** when it spends most of its time computing. Waiting can overlap: use threads or `asyncio` for I/O-bound work. Computing needs more processors: use several processes, or native code that releases Python's global lock. See [The GIL, threading and multiprocessing](#/lesson/python/py-threads-processes) and [asyncio](#/lesson/python/py-asyncio).

### 5. Micro-optimisations: last and least

Reading a local variable is faster than reading a global variable or an attribute, so very hot loops sometimes store `append = out.append` before the loop. `x * x` is a little faster than `x ** 2`. `if x in {"a", "b", "c"}` with a constant set is a fast lookup. These give tens of percent at best and cost readability, so use them only inside hot spots that profiling has found.

When that is still not enough, there are heavier tools: **PyPy** (an alternative Python interpreter that compiles hot code to machine code while it runs), **Cython** (Python-like code compiled to C), **Numba** (compiles numeric functions on the fly) and extensions written in Rust or C.

## Memory

### How big are objects?

In Python every value is an **object**, a block of memory that holds the value plus some bookkeeping. Every object carries a **header**: a **reference count** (how many names and containers currently point at it, explained in the next lesson) and a pointer to its type. A container such as a list does not hold its items directly; it holds **references** (memory addresses) to item objects stored elsewhere. So small values take far more memory than in C, where an integer is often 4 or 8 bytes.

`sys.getsizeof` reports the size in bytes of the object **itself**, not of the objects it refers to. That is called a **shallow** size; the **deep** size would include everything reachable from the object.

```python-run
import sys
for obj in [0, 2**100, 3.14, "", "abc", "é" * 3, (), (1, 2, 3), [], [1, 2, 3], {}, set(), None, True]:
    print(f"{obj!r:<28} {sys.getsizeof(obj):>4} bytes")

nested = [[0] * 1000 for _ in range(10)]
print("outer list only:", sys.getsizeof(nested), "| including inner lists:",
      sys.getsizeof(nested) + sum(sys.getsizeof(row) for row in nested))
```

**Reading the output**

- The loop prints each object's `repr` padded to 28 characters, then its size. Exact numbers depend on the platform: on a typical 64-bit computer the integer `0` takes 28 bytes and an empty list 56. The browser runs a 32-bit build of Python, so the numbers you see there are smaller, but the pattern is the same.
- Even an empty string or empty tuple has a size, because of the header. A huge integer such as `2**100` is bigger than a small one, since Python integers grow to hold any number of digits. A string of three `é` characters takes more than `"abc"`: CPython gives a string containing any character outside ASCII (the American Standard Code for Information Interchange, the basic English character set) a larger internal header.
- The last line shows the shallow-versus-deep trap. The outer list `nested` is small, because it holds only 10 references. Adding the 10 inner lists, each holding 1,000 references, gives a far larger total. Even that is not the full deep size, since it does not count the integer objects themselves.

On a 64-bit machine, a list of a million distinct integers costs about 8 MB for the references **plus** about 28 bytes for each integer object. When memory matters, these techniques help:

| Technique | Saving |
|---|---|
| generators / iterating files lazily | O(1) instead of O(n) |
| `__slots__` on classes with many instances | no per-instance `__dict__` (often 2–3× smaller) |
| `array.array` / NumPy arrays | raw 4–8 bytes per number, no per-item objects |
| tuples instead of lists for fixed records | smaller, no over-allocation |
| `range`, `itertools`, `dict` views | computed on demand |
| interning / sharing equal immutable objects | fewer duplicates |
| chunked processing, memory-mapped files (`mmap`) | bounded working set |

Some terms from the table: by default each object of a class keeps its attributes in its own dictionary, `__dict__`; declaring **`__slots__`** lists the attribute names in advance so Python stores them in fixed positions instead, with no dictionary. **Over-allocation** is the spare room a list keeps for future appends. **Interning** means keeping one shared copy of equal immutable values. A **memory-mapped file** lets the operating system load parts of a large file on demand, as if it were in memory. The **working set** is the memory a program is actively using.

```python-run
import sys, array

class PlainPoint:
    def __init__(self, x, y): self.x, self.y = x, y
class SlotPoint:
    __slots__ = ("x", "y")
    def __init__(self, x, y): self.x, self.y = x, y

p, s = PlainPoint(1, 2), SlotPoint(1, 2)
print("plain:", sys.getsizeof(p) + sys.getsizeof(p.__dict__), "bytes | slots:", sys.getsizeof(s), "bytes")

n = 100_000
as_list = list(range(n))
as_array = array.array("i", range(n))
print("list :", sys.getsizeof(as_list) + n * 28, "bytes (approx, incl. int objects)")
print("array:", sys.getsizeof(as_array), "bytes")
print("gen  :", sys.getsizeof(x for x in range(n)), "bytes")
```

**Reading this code line by line**

- `PlainPoint` stores `x` and `y` in a per-object dictionary; `SlotPoint` declares `__slots__` and has no dictionary. The first print adds the object and its dictionary for the plain version and shows that the slotted point is several times smaller. With millions of points, that difference is the difference between fitting in memory and not.
- `array.array("i", range(n))` stores 100,000 numbers as raw machine integers (`"i"` means a C `int`, usually 4 bytes each) instead of as separate Python objects. Its size is a fraction of the list's estimated total, which adds 28 bytes per integer object to the list's own size.
- A generator expression has a small, fixed size however many items it will produce, because it produces them one at a time.

### Finding memory hogs: `tracemalloc`

`tracemalloc` (trace memory allocations) records which line of code allocated each block of memory. Taking a **snapshot** before and after a piece of code and comparing them shows which lines grew.

```python-run
import tracemalloc

tracemalloc.start()
before = tracemalloc.take_snapshot()

cache = {i: str(i) * 20 for i in range(20_000)}          # the "leak"
squares = [i * i for i in range(50_000)]

after = tracemalloc.take_snapshot()
current, peak = tracemalloc.get_traced_memory()
print(f"current {current / 1e6:.1f} MB, peak {peak / 1e6:.1f} MB")
for stat in after.compare_to(before, "lineno")[:2]:
    print(f"  line {stat.traceback[0].lineno}: +{stat.size_diff / 1e6:.2f} MB in {stat.count_diff} blocks")
tracemalloc.stop()
```

**Reading this code line by line**

- `tracemalloc.start()` begins recording; `take_snapshot()` captures the current allocations.
- Two lines allocate memory: a dictionary of 20,000 strings and a list of 50,000 squares.
- `get_traced_memory()` returns the memory currently allocated and the peak since tracing started, in bytes; dividing by one million gives megabytes.
- `after.compare_to(before, "lineno")` lists the differences grouped by line number, biggest first. The two rows printed point straight at the dictionary line and the list line, with how much each added. In a real program, this is how you find the line responsible for growth.

A **memory leak** is memory that a program keeps holding although it no longer needs it. Python frees an object automatically once nothing refers to it, so leaks in Python are almost always **unintended references**: a module-level dict or list that only ever grows, an unbounded cache (`lru_cache(maxsize=None)` on arguments that take many different values), closures or callbacks that hold on to big objects, or long-lived objects referring to short-lived data. The fixes are bounded caches, **weak references** (`weakref`, references that do not keep an object alive), explicit cleanup, and narrower scopes.

## Worked example: optimising step by step

Task: for each query word, count how many words in a word list are **anagrams** of it, that is, made of exactly the same letters in a different order. Two words are anagrams if their sorted letters are equal: `sorted("abc") == sorted("cab")`.

```python-run
import random, string, time
from collections import Counter

random.seed(7)
words = ["".join(random.choices("abcde", k=5)) for _ in range(3000)]
queries = ["".join(random.choices("abcde", k=5)) for _ in range(300)]

def v1(words, queries):                       # O(q * n * k log k): re-sorts every word for every query
    return [sum(1 for w in words if sorted(w) == sorted(q)) for q in queries]

def v2(words, queries):                       # precompute signatures once: O((n + q) * k log k)
    table = Counter("".join(sorted(w)) for w in words)
    return [table["".join(sorted(q))] for q in queries]

t = time.perf_counter(); r1 = v1(words, queries); t1 = time.perf_counter() - t
t = time.perf_counter(); r2 = v2(words, queries); t2 = time.perf_counter() - t
print(r1 == r2, f"v1 {t1 * 1000:.0f} ms -> v2 {t2 * 1000:.1f} ms ({t1 / t2:.0f}x faster)")
```

**Reading this code line by line**

- The setup builds 3,000 random five-letter words and 300 random queries from the letters a to e.
- `v1` compares every query with every word, sorting both each time. With `q` queries, `n` words and words of length `k`, that is `q × n` comparisons, each paying for two sorts.
- `v2` first computes each word's **signature**, its letters in sorted order joined into a string, and counts the signatures with a `Counter`. Each query then needs one sort and one dictionary lookup. The cost becomes "sort every word once, plus sort every query once".
- The output shows `True` (both versions agree) and a speed-up in the hundreds.

The speed-up comes entirely from *not repeating work* and from a hash lookup replacing a scan. No tricks were needed, and the code got shorter.

> [!INTERVIEW]
> When asked "how would you make this faster?", answer in order: (1) measure/profile to find the hotspot; (2) improve the algorithm or data structure (set/dict lookups, sorting once, heaps, avoiding repeated work); (3) use built-ins/vectorised libraries so loops run in C; (4) cache; (5) parallelise according to I/O- vs CPU-bound. Quote the complexities of the built-ins you use — especially `in` on a list (O(n)) vs a set (O(1)), `pop(0)` vs `popleft()`, and string concatenation vs `join`.

## Pitfalls recap

- Optimising without profiling, or optimising code that is not the bottleneck.
- Hidden O(n) operations inside loops: `in` on lists, `pop(0)`, slicing, concatenation.
- Benchmarking with tiny inputs or a single run; timing with `time.time()` (a wall clock that can jump) instead of `perf_counter` or `timeit`.
- Reading `sys.getsizeof` as the *deep* size.
- Unbounded caches and global containers that only grow.
- Sacrificing readability for gains of a few percent.

## Summary

Know what built-in operations cost, measure with `timeit` and `cProfile`, and fix the algorithm first. Let C-implemented built-ins and libraries run your loops, avoid repeated work with caching and laziness, choose threads, `asyncio` or processes according to whether the work waits or computes, and keep micro-optimisations for proven hot spots. For memory, think in object counts: generators, `__slots__`, arrays and bounded caches, with `tracemalloc` to find where memory goes.

## Glossary

- **Performance** - how much time and memory a program needs.
- **Profiling / profiler** - measuring where a program spends its time or memory / the tool that does it.
- **Bytecode** - the compact instructions Python compiles your source into before running it.
- **Interpreter** - the program that executes bytecode instruction by instruction; CPython is the standard one.
- **Bottleneck** - the part of a program that limits its overall speed.
- **Micro-optimisation** - a small local change that saves a little time per operation.
- **Big-O notation** - a description of how work grows with input size, ignoring constant factors.
- **Amortised cost** - the average cost per operation over a long sequence of operations.
- **Deque** - a double-ended queue, fast to add to and remove from at both ends.
- **Hash** - a number computed from a value that lets sets and dicts find it directly.
- **Monotonic clock** - a clock that never goes backwards, suitable for measuring durations.
- **Micro-benchmark** - a timing of a very small piece of code, repeated many times.
- **Brute force** - solving a problem by trying every possibility.
- **Vectorisation** - running one operation over a whole array in compiled code instead of a Python loop.
- **Pure function** - a function whose result depends only on its arguments and that has no side effects.
- **I/O-bound / CPU-bound** - spending most time waiting for input and output / spending most time computing.
- **Reference count** - the number of references currently pointing at an object.
- **Shallow / deep size** - the memory of an object alone / of the object plus everything it refers to.
- **`__slots__`** - a class declaration that stores attributes in fixed positions instead of a per-object dictionary.
- **Memory leak** - memory a program keeps holding although it no longer needs it; in Python, usually a forgotten reference.
- **Weak reference** - a reference that does not keep its target object alive.

```quiz
[
  {"q": "What should you do first when a program is too slow?", "options": ["Rewrite it in C", "Profile it to find where the time actually goes", "Replace all lists with tuples", "Add threads"], "answer": 1,
   "explain": "Measure before optimising: usually a small part of the code dominates the runtime."},
  {"q": "Complexity of `for x in a: if x in b:` when a and b are lists of size n?", "options": ["O(n)", "O(n log n)", "O(n^2)", "O(1)"], "answer": 2,
   "explain": "Each `in` on a list is a linear scan; converting b to a set makes the whole loop O(n)."},
  {"q": "Which tool reports per-function call counts and cumulative time?", "options": ["timeit", "cProfile", "tracemalloc", "sys.getsizeof"], "answer": 1,
   "explain": "cProfile is the deterministic function-level profiler; timeit benchmarks snippets; tracemalloc tracks memory."},
  {"q": "What does sys.getsizeof([[0]*1000]*3) measure?", "options": ["The total memory of all nested data", "Only the outer list object (header + 3 pointers)", "The number of elements", "Disk size"], "answer": 1,
   "explain": "getsizeof is shallow: it does not follow references to contained objects."},
  {"q": "Why is `sum(data)` faster than an explicit Python for loop adding the items?", "options": ["It uses multiple cores", "The loop runs in C inside the interpreter rather than as Python bytecode", "It skips some items", "It caches results"], "answer": 1,
   "explain": "Built-ins avoid per-iteration bytecode dispatch and name lookups."},
  {"q": "What does __slots__ save?", "options": ["CPU time for method calls only", "The per-instance __dict__, reducing memory for classes with many instances", "Disk space", "Import time"], "answer": 1,
   "explain": "Attributes are stored in fixed slots instead of a dictionary per object."},
  {"q": "The most common cause of a 'memory leak' in Python is:", "options": ["Forgetting to call free()", "Unintended lingering references, e.g. a global dict or unbounded cache that keeps growing", "Integers overflowing", "Using generators"], "answer": 1,
   "explain": "Objects stay alive as long as something references them; growing global containers and caches are the usual culprits."},
  {"q": "For top-10 of a million numbers, which is asymptotically best?", "options": ["sorted(xs)[:10]", "heapq.nsmallest(10, xs)", "Repeated min() and remove()", "Bubble sort"], "answer": 1,
   "explain": "A size-k heap gives O(n log k) versus O(n log n) for a full sort."}
]
```

> **Source:** Python docs, *Library Reference* `timeit`, "The Python Profilers" (`cProfile`, `pstats`), `tracemalloc`, `sys.getsizeof`; Python wiki "TimeComplexity" and "PythonSpeed/PerformanceTips"; Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, ch. 3 (Algorithm Analysis) and ch. 5 (efficiency of Python's sequence types).
