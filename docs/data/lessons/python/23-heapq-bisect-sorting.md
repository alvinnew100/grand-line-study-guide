# heapq, bisect, sorting and math

Three standard-library tools turn up in a large share of interview solutions: **sorting with key functions** (to arrange data by any criterion), **`heapq`** (a priority queue for "smallest/largest k" and scheduling), and **`bisect`** (binary search on sorted lists). Add a handful of `math` and string helpers and you have the complete everyday toolkit.

## Sorting

Python sorts with **Timsort**: O(n log n) worst case, O(n) on already-sorted or nearly-sorted input, and **stable** (equal elements keep their original relative order).

- `sorted(iterable, *, key=None, reverse=False)` → returns a **new list** from any iterable.
- `list.sort(*, key=None, reverse=False)` → sorts **in place**, returns `None`.

```python-run
nums = [5, 2, 9, 1]
print(sorted(nums), nums)            # new list; original untouched
print(nums.sort(), nums)             # None; now sorted in place
print(sorted("banana"), sorted({3, 1, 2}), sorted({"b": 1, "a": 2}))   # works on any iterable
print(sorted(nums, reverse=True))
```

### Key functions

`key` is a function applied **once per element**; elements are ordered by the returned values.

```python-run
words = ["Banana", "apple", "cherry", "fig"]
print(sorted(words))                              # uppercase sorts before lowercase
print(sorted(words, key=str.lower))
print(sorted(words, key=len))
print(sorted(words, key=lambda w: (-len(w), w)))  # length descending, then alphabetical

people = [("ana", 31), ("ben", 25), ("cy", 31), ("dee", 25)]
print(sorted(people, key=lambda p: (-p[1], p[0])))

from operator import itemgetter, attrgetter
print(sorted(people, key=itemgetter(1, 0)))
print(max(people, key=itemgetter(1)), min(words, key=len))
```

Multi-criteria sorting relies on **tuple comparison**: tuples compare element by element. Negate a numeric field for descending order. For descending order on a *non-numeric* field, exploit **stability** — sort by the secondary key first, then by the primary:

```python-run
people = [("ana", 31), ("ben", 25), ("cy", 31), ("dee", 25)]
people.sort(key=lambda p: p[0], reverse=True)   # secondary: name descending
people.sort(key=lambda p: p[1])                 # primary: age ascending (stable!)
print(people)
```

### Custom comparators

When ordering can't be expressed as a key (e.g. "arrange numbers to form the largest concatenation"), wrap an old-style comparison function with `functools.cmp_to_key`:

```python-run
from functools import cmp_to_key

def largest_number(nums):
    strs = list(map(str, nums))
    cmp = lambda a, b: (a + b < b + a) - (a + b > b + a)   # negative if a should come first
    return "".join(sorted(strs, key=cmp_to_key(cmp))).lstrip("0") or "0"

print(largest_number([3, 30, 34, 5, 9]), largest_number([0, 0]))
```

Sorting facts worth remembering: comparing mixed types (`[1, "a"]`) raises `TypeError`; `sorted` needs only `__lt__`; `reverse=True` preserves stability; and sorting is often the simplest route to an O(n log n) solution (intervals, two-pointer problems, grouping).

## heapq: the priority queue

A **binary heap** is a list arranged so that `heap[0]` is always the smallest element (a *min-heap*): for every index `i`, `heap[i] <= heap[2i+1]` and `heap[i] <= heap[2i+2]`. `heapq` provides functions that maintain this invariant on a plain list.

| Function | Effect | Cost |
|---|---|---|
| `heapify(lst)` | turn a list into a heap in place | O(n) |
| `heappush(h, x)` | add an item | O(log n) |
| `heappop(h)` | remove and return the smallest | O(log n) |
| `h[0]` | peek at the smallest | O(1) |
| `heappushpop(h, x)` | push then pop (faster than both) | O(log n) |
| `heapreplace(h, x)` | pop then push | O(log n) |
| `nlargest(k, it, key=)` / `nsmallest(k, it, key=)` | top-k | O(n log k) |
| `merge(*sorted_its)` | lazily merge sorted inputs | O(total · log k) |

```python-run
import heapq

h = [5, 3, 8, 1, 9, 2]
heapq.heapify(h)
print(h, h[0])                         # a heap is NOT fully sorted; only h[0] is guaranteed
heapq.heappush(h, 0)
print([heapq.heappop(h) for _ in range(3)], h)
print(heapq.nlargest(2, [5, 3, 8, 1]), heapq.nsmallest(2, ["pear", "fig", "apple"], key=len))
print(list(heapq.merge([1, 4, 7], [2, 5], [0, 9])))
```

### Max-heaps and tuples

`heapq` is min-only. For a max-heap, push **negated** values (or `(-priority, item)` tuples). Tuples are compared element by element, so `(priority, item)` works as a priority queue entry — but if priorities tie, Python compares the items, which fails for uncomparable objects. The standard fix is a unique tie-breaker counter:

```python-run
import heapq, itertools

scores = [5, 3, 8, 1]
max_heap = [-s for s in scores]
heapq.heapify(max_heap)
print(-heapq.heappop(max_heap), -max_heap[0])

counter = itertools.count()
tasks = []
for priority, task in [(2, {"name": "write"}), (1, {"name": "plan"}), (2, {"name": "test"})]:
    heapq.heappush(tasks, (priority, next(counter), task))    # dicts are never compared
while tasks:
    priority, _, task = heapq.heappop(tasks)
    print(priority, task["name"])
```

### Heap patterns

**Top-k with a size-k min-heap** — O(n log k) time, O(k) space, and it works on streams:

```python-run
import heapq

def k_largest(stream, k):
    heap = []
    for x in stream:
        if len(heap) < k:
            heapq.heappush(heap, x)
        elif x > heap[0]:
            heapq.heapreplace(heap, x)       # drop the smallest of the current top-k
    return sorted(heap, reverse=True)

print(k_largest(iter([3, 1, 4, 1, 5, 9, 2, 6, 5, 3]), 3))
```

**Dijkstra's shortest paths** — pop the closest unsettled node:

```python-run
import heapq

def dijkstra(graph, src):
    dist = {src: 0}
    heap = [(0, src)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, float("inf")):
            continue                         # stale entry: lazy deletion
        for v, w in graph.get(u, []):
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return dist

g = {"a": [("b", 4), ("c", 1)], "c": [("b", 2), ("d", 5)], "b": [("d", 1)]}
print(dijkstra(g, "a"))
```

Other heap classics: merge k sorted lists, meeting rooms (min-heap of end times), running median (two heaps), task scheduler.

Choosing: for one-off top-k, `sorted(xs)[:k]` is O(n log n) and fine for small inputs; `heapq.nlargest` is O(n log k); for k=1 use `min`/`max`.

## bisect: binary search on sorted lists

`bisect` finds insertion points in a **sorted** list in O(log n).

- `bisect_left(a, x)` → the leftmost index where `x` could be inserted keeping order: the first position `i` with `a[i] >= x`.
- `bisect_right(a, x)` (alias `bisect`) → the rightmost: the first `i` with `a[i] > x`.
- `insort(a, x)` → insert keeping order (O(log n) search **+ O(n) shift**).
- All accept `lo`, `hi`, and (3.10+) `key`.

```python-run
import bisect
a = [10, 20, 20, 20, 30, 40]
print(bisect.bisect_left(a, 20), bisect.bisect_right(a, 20))     # 1 4
print(bisect.bisect_right(a, 20) - bisect.bisect_left(a, 20))    # count of 20s
print(bisect.bisect_left(a, 25), bisect.bisect_left(a, 5), bisect.bisect_left(a, 99))

def index_of(a, x):                      # exact search
    i = bisect.bisect_left(a, x)
    return i if i < len(a) and a[i] == x else -1
print(index_of(a, 30), index_of(a, 31))

bisect.insort(a, 25); print(a)
```

Handy translations:

| Question | Expression |
|---|---|
| number of elements `< x` | `bisect_left(a, x)` |
| number of elements `<= x` | `bisect_right(a, x)` |
| first element `>= x` | `a[bisect_left(a, x)]` (if in range) |
| last element `<= x` | `a[bisect_right(a, x) - 1]` (if index ≥ 0) |

```python-run
import bisect

def grade(score, breakpoints=(60, 70, 80, 90), grades="FDCBA"):
    return grades[bisect.bisect_right(breakpoints, score)]
print([grade(s) for s in (33, 60, 77, 89, 90, 100)])

# longest increasing subsequence in O(n log n): tails[i] = smallest tail of an LIS of length i+1
def lis_length(nums):
    tails = []
    for x in nums:
        i = bisect.bisect_left(tails, x)
        if i == len(tails):
            tails.append(x)
        else:
            tails[i] = x
    return len(tails)
print(lis_length([10, 9, 2, 5, 3, 7, 101, 18]))
```

When an interviewer wants binary search written by hand, the `bisect_left` loop is the template to memorise:

```python-run
def lower_bound(a, x):
    lo, hi = 0, len(a)              # search in the half-open range [lo, hi)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo
print(lower_bound([10, 20, 20, 30], 20), lower_bound([10, 20, 20, 30], 35))
```

## math essentials

```python-run
import math
print(math.gcd(84, 36), math.lcm(4, 6), math.isqrt(17), math.sqrt(16))
print(math.comb(5, 2), math.perm(5, 2), math.factorial(5), math.prod([1, 2, 3, 4]))
print(math.ceil(7 / 2), math.floor(-3.5), -(-7 // 2), round(2.5), round(3.5))
print(math.inf > 10**100, -math.inf, math.isclose(0.1 + 0.2, 0.3), math.log2(1024), math.log(100, 10))
print(divmod(17, 5), pow(3, 200, 13), abs(-3), sum([0.1] * 10), math.fsum([0.1] * 10))
```

Notes for interviews:

- `float("inf")` / `math.inf` are the usual "infinity" initial values for minimum searches.
- `math.isqrt(n)` is an exact integer square root; `int(math.sqrt(n))` can be off by one for huge `n`.
- `-(-a // b)` is integer ceiling division without floats.
- `round()` uses **banker's rounding** (round half to even): `round(2.5) == 2`, `round(3.5) == 4`.
- Integers never overflow; modular answers use `% (10**9 + 7)` and `pow(a, b, m)`.

## String helpers

```python-run
import string
s = "Hello, World"
print(s.lower(), s[::-1], s.isalnum(), "".join(c for c in s if c.isalnum()).lower())
print(ord("a"), chr(97), chr(ord("a") + 3), string.ascii_lowercase[:5], string.digits)
print("a,b;c".replace(";", ",").split(","), " ".join(reversed("the sky is blue".split())))
print(f"{5:03d} {3.14159:.2f} {255:b} {255:x} {1234567:,}", "ab".zfill(5), "x".center(5, "*"))
print("".join(sorted("listen")) == "".join(sorted("silent")), "abc" < "abd", "Z" < "a")
print(int("101", 2), bin(5)[2:], str(123)[::-1], "racecar" == "racecar"[::-1])
```

> [!INTERVIEW]
> State costs as you code: "sorting is O(n log n) and stable", "heap push/pop are O(log n), heapify is O(n)", "`bisect` is O(log n) but `insort` is O(n) because of the shift". Know the max-heap trick (negate), the tuple tie-breaker trick, and the difference between `bisect_left` and `bisect_right` on duplicates.

## Pitfalls recap

- `x = lst.sort()` gives `None`.
- Treating a heap as sorted: only `heap[0]` is the minimum; iterate with repeated `heappop` (or `sorted(heap)`).
- Tuples with equal priorities and uncomparable payloads raise `TypeError` — add a counter.
- Using `bisect` on an unsorted list silently returns garbage.
- `insort` in a loop is O(n²) overall.
- `round(0.5) == 0` — banker's rounding.

## Summary

Sort with `key` functions and tuple keys, relying on stability; use `cmp_to_key` for exotic orders. `heapq` maintains a min-heap on a list for O(log n) priority-queue operations and top-k selection. `bisect` performs binary search on sorted lists. `math` covers gcd, combinatorics, integer roots and infinities.

```quiz
[
  {"q": "Which statement about Python's sort is true?", "options": ["It is unstable", "It is stable and O(n log n) worst case", "list.sort returns the sorted list", "It is quicksort"], "answer": 1,
   "explain": "Timsort is stable, O(n log n) worst case and O(n) on sorted data. list.sort returns None."},
  {"q": "How do you sort people by age descending then name ascending?", "options": ["sorted(p, key=lambda x: (x.age, x.name), reverse=True)", "sorted(p, key=lambda x: (-x.age, x.name))", "sorted(p, reverse=True)", "p.sort(key=age)"], "answer": 1,
   "explain": "Negating the numeric field flips its order while the name stays ascending. reverse=True would flip both."},
  {"q": "How do you get max-heap behaviour from heapq?", "options": ["heapq.heapify(lst, max=True)", "Push negated values (or tuples starting with a negated priority)", "Use heapq.maxpush", "Sort in reverse first"], "answer": 1,
   "explain": "heapq only implements a min-heap; negate keys to invert the order."},
  {"q": "Time complexity of heapq.heapify on n items?", "options": ["O(log n)", "O(n)", "O(n log n)", "O(n^2)"], "answer": 1,
   "explain": "Bottom-up heap construction is linear."},
  {"q": "For a = [1, 2, 2, 2, 3], what are bisect_left(a, 2) and bisect_right(a, 2)?", "options": ["1 and 4", "1 and 3", "2 and 4", "0 and 3"], "answer": 0,
   "explain": "bisect_left returns the first index with a[i] >= 2 (1); bisect_right the first index with a[i] > 2 (4)."},
  {"q": "Why push (priority, counter, task) instead of (priority, task)?", "options": ["Counters are faster", "When priorities tie, tuples would compare the tasks, which may not be comparable; the counter breaks ties first", "heapq requires 3-tuples", "To sort by task name"], "answer": 1,
   "explain": "A unique increasing counter guarantees comparison never reaches the payload and keeps FIFO order among equal priorities."},
  {"q": "`round(2.5)` in Python 3 is:", "options": ["3", "2", "2.5", "Error"], "answer": 1,
   "explain": "Python rounds half to even (banker's rounding): 2.5 -> 2, 3.5 -> 4."},
  {"q": "Cost of bisect.insort on a list of n items?", "options": ["O(log n)", "O(n)", "O(1)", "O(n log n)"], "answer": 1,
   "explain": "Finding the position is O(log n) but inserting into a list shifts elements, O(n)."}
]
```

> **Source:** Python docs, *Library Reference* `heapq`, `bisect`, `math`, built-in `sorted`, and the *Sorting Techniques* HOWTO; Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, ch. 9 (priority queues and heaps) and ch. 12 (sorting).
