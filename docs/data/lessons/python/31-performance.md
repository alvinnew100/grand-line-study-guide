# Performance, profiling and memory

"Python is slow" is half true: pure-Python bytecode runs roughly 10–100× slower than equivalent C. Yet Python programs are routinely fast enough — because the heavy lifting happens inside built-ins and libraries written in C, and because the *algorithm* matters far more than the language. This lesson teaches the working method: know the cost of built-in operations, **measure before optimising**, fix the algorithm first, then apply Python-specific techniques, and understand where memory goes.

## Rule zero: measure

Intuition about performance is wrong surprisingly often. The discipline is:

1. Make it correct (with tests).
2. Decide whether it is actually too slow, with a realistic input.
3. **Profile** to find the bottleneck — typically a few lines account for most of the time.
4. Fix that, with the biggest lever first: algorithm → data structure → library → micro-optimisation.
5. Measure again; keep the tests green.

Knuth's line applies: premature optimisation is the root of all evil — but so is ignoring an O(n²) loop that's about to meet a million rows.

## Big-O of the built-ins

Collected in one place, for CPython (`n` = container size, `k` = other operand size):

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

\* amortised. \*\* strings are immutable, so "copying" just shares.

Also: `heapq.heappush/heappop` O(log n), `heapify` O(n); `bisect` O(log n) search but `insort` O(n); `"".join` O(total length); `x in range(...)` O(1); set union O(n+k), intersection O(min(n, k)); `collections.Counter(xs)` O(n); `sorted(xs)[:k]` O(n log n) vs `heapq.nsmallest(k, xs)` O(n log k).

Explore growth rates interactively:

<div class="widget" data-widget="bigo"></div>

### Hidden quadratic behaviour

The classic performance bugs are linear operations inside loops:

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

Other disguises: `s += piece` over many pieces, `del lst[0]`/`pop(0)` loops, slicing inside recursion (`f(xs[1:])`), `lst.index(x)` or `lst.remove(x)` in loops, `sorted()` inside a loop, and `if key in d.values()`.

## Timing code: `timeit` and `perf_counter`

Use `time.perf_counter()` (a monotonic, high-resolution clock) for coarse timing, and `timeit` for micro-benchmarks — it runs the snippet many times, disables garbage collection during timing, and avoids common pitfalls.

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

From the shell: `python -m timeit -s "data = list(range(1000))" "[x * 2 for x in data]"`. Report the **minimum** of several repeats (the least disturbed run), benchmark with realistic sizes, and remember that results vary across machines and Python versions (3.11+ is substantially faster than 3.10 thanks to the specialising adaptive interpreter).

## Profiling: where does the time go?

`cProfile` records every function call: how many times it was called (`ncalls`), time spent in the function itself (`tottime`), and time including callees (`cumtime`).

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

Read the table from the top: sort by `cumulative` to see which high-level call dominates, by `tottime` to find the function whose own code burns the time. Command-line forms:

```bash
python -m cProfile -s cumulative script.py | head -30
python -m cProfile -o out.prof script.py     # then inspect with pstats or 'snakeviz out.prof'
```

Other tools: **py-spy** (sampling profiler that attaches to a running process with almost no overhead — great in production), **line_profiler** (per-line timings), **scalene** (CPU + memory), **pytest-benchmark** (benchmarks as tests).

## Speeding things up, biggest lever first

### 1. A better algorithm or data structure

Nothing else comes close. Replacing an O(n²) scan with a dict lookup turns minutes into milliseconds.

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

### 2. Push loops into C

Built-ins and standard-library functions run their loops in C. Prefer `sum`, `min`, `max`, `any`, `all`, `sorted`, `str.join`, `map`, comprehensions, `collections.Counter`, `itertools`, slicing, and `in` on sets over hand-written Python loops. For numeric arrays, **NumPy** vectorisation is typically 10–100× faster than a Python loop:

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

### 3. Don't repeat work

- **Cache**: `functools.lru_cache`/`cache` for pure functions; precompute lookup tables; hoist invariant computations out of loops; compile regexes once.
- **Be lazy**: generators avoid building intermediate lists; `any`/`next` stop early.
- **Batch I/O**: one query for 1,000 rows instead of 1,000 queries; buffered writes; `"".join` then a single `write`.

### 4. Concurrency and parallelism

I/O-bound → threads or asyncio. CPU-bound → processes or native code. (Module 10.)

### 5. Micro-optimisations — last and least

Local variable access is faster than global or attribute access, so hot loops sometimes bind `append = out.append` first; `x * x` beats `x ** 2`; `if x in {…}` with a constant set is a fast lookup. These yield tens of percent at best and cost readability — only inside profiled hot spots. If you need more, reach for PyPy, Cython, Numba, or a Rust/C extension.

## Memory

### How big are objects?

Every Python object carries a header (reference count + type pointer), so small values are much bigger than in C. `sys.getsizeof` reports the size of the object **itself**, not the things it references:

```python-run
import sys
for obj in [0, 2**100, 3.14, "", "abc", "é" * 3, (), (1, 2, 3), [], [1, 2, 3], {}, set(), None, True]:
    print(f"{obj!r:<28} {sys.getsizeof(obj):>4} bytes")

nested = [[0] * 1000 for _ in range(10)]
print("outer list only:", sys.getsizeof(nested), "| including inner lists:",
      sys.getsizeof(nested) + sum(sys.getsizeof(row) for row in nested))
```

A list of a million ints is about 8 MB of pointers **plus** ~28 bytes per distinct int object. Options when memory matters:

| Technique | Saving |
|---|---|
| generators / iterating files lazily | O(1) instead of O(n) |
| `__slots__` on classes with many instances | no per-instance `__dict__` (often 2–3× smaller) |
| `array.array` / NumPy arrays | raw 4–8 bytes per number, no per-item objects |
| tuples instead of lists for fixed records | smaller, no over-allocation |
| `range`, `itertools`, `dict` views | computed on demand |
| interning / sharing equal immutable objects | fewer duplicates |
| chunked processing, memory-mapped files (`mmap`) | bounded working set |

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

### Finding memory hogs: `tracemalloc`

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

"Memory leaks" in Python are almost always **unintended references**: an ever-growing module-level dict or list, an unbounded cache (`lru_cache(maxsize=None)` on high-cardinality arguments), closures or callbacks holding big objects, or long-lived objects referencing short-lived data. Fix with bounded caches, `weakref`, explicit cleanup, or narrower scopes.

## Worked example: optimising step by step

Task: for each query word, count how many dictionary words are anagrams of it.

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

The speed-up comes entirely from *not repeating work* and from a hash lookup replacing a scan — no tricks, and the code became shorter.

> [!INTERVIEW]
> When asked "how would you make this faster?", answer in order: (1) measure/profile to find the hotspot; (2) improve the algorithm or data structure (set/dict lookups, sorting once, heaps, avoiding repeated work); (3) use built-ins/vectorised libraries so loops run in C; (4) cache; (5) parallelise according to I/O- vs CPU-bound. Quote the complexities of the built-ins you use — especially `in` on a list (O(n)) vs a set (O(1)), `pop(0)` vs `popleft()`, and string concatenation vs `join`.

## Pitfalls recap

- Optimising without profiling; optimising code that isn't the bottleneck.
- Hidden O(n) operations inside loops (`in` on lists, `pop(0)`, slicing, concatenation).
- Benchmarking with tiny inputs or a single run; timing with `time.time()` instead of `perf_counter`/`timeit`.
- Reading `sys.getsizeof` as the *deep* size.
- Unbounded caches and global containers that only grow.
- Sacrificing readability for single-digit-percent gains.

## Summary

Know what built-in operations cost, measure with `timeit` and `cProfile`, and fix the algorithm first. Let C-implemented built-ins and libraries run your loops, avoid repeated work with caching and laziness, and reserve micro-optimisations for proven hot spots. For memory, think in object counts: generators, `__slots__`, arrays and bounded caches, diagnosed with `tracemalloc`.

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
