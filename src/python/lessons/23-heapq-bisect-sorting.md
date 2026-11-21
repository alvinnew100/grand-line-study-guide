# heapq, bisect, sorting and math

> **Before this lesson:** you need lists, tuples, tuple comparison and the O-notation from [Lists, tuples and strings](#/lesson/python/py-sequences), `key` functions and lambdas from [Functions and arguments](#/lesson/python/py-functions-args) and [Scope, closures and lambdas](#/lesson/python/py-scope-closures), and the containers of [collections](#/lesson/python/py-collections).

## In plain words

This lesson is about three ways of dealing with *order*, each suited to a different situation.

- **Sorting** puts everything in order once, like arranging a whole bookshelf alphabetically. You can say *by what* to order, with a small function called a key.
- A **heap** is for when you never need the whole collection in order, but again and again need "the smallest one right now" while new items keep arriving. Think of a hospital emergency room: patients arrive at any time, and the next one treated is always the most urgent, not the one who has waited longest. A collection that hands out items by priority is called a **priority queue**, and a heap is the standard way to build one. In Python the module is `heapq`.
- **Binary search** finds a position in a collection that is *already sorted*, by halving: open the dictionary in the middle, decide whether your word is in the first or the second half, and repeat. A thousand pages need about ten steps, a million pages about twenty. In Python the module is `bisect`.

The lesson ends with the few `math` and string helpers that complete the everyday toolkit.

Why this matters for a job: a large share of interview solutions use one of these three, and you are expected to state the cost as you write ("sorting is O(n log n)", "each heap operation is O(log n)"). Choosing a full sort where a heap would do, or searching item by item in sorted data, is exactly the kind of inefficiency interviewers look for.

## Sorting

Python sorts with an algorithm called **Timsort**. Three facts about it are worth knowing by heart: it takes O(n log n) time at worst; it takes only O(n) on input that is already sorted or nearly so; and it is **stable**, meaning that items which compare as equal keep the order they had before the sort.

There are two ways to sort:

- `sorted(iterable, *, key=None, reverse=False)` accepts any iterable and returns a **new list**.
- `list.sort(*, key=None, reverse=False)` sorts an existing list **in place** and returns `None`.

```python-run
nums = [5, 2, 9, 1]
print(sorted(nums), nums)            # new list; original untouched
print(nums.sort(), nums)             # None; now sorted in place
print(sorted("banana"), sorted({3, 1, 2}), sorted({"b": 1, "a": 2}))   # works on any iterable
print(sorted(nums, reverse=True))
```

The first line prints `[1, 2, 5, 9] [5, 2, 9, 1]`: a new sorted list, and the original unchanged. The second prints `None [1, 2, 5, 9]`: `sort()` returned nothing and changed the list itself. The third shows that `sorted` accepts a string (giving a list of letters), a set, and a dictionary (giving its keys). `reverse=True` sorts from largest to smallest.

### Key functions

The `key` argument is a function that Python calls **once for each item**. The items are then arranged according to the values that function returned, not according to the items themselves.

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

- Without a key, `Banana` comes first, because capital letters have smaller character numbers than lowercase ones.
- `key=str.lower` compares lowercase versions: `apple, Banana, cherry, fig`.
- `key=len` orders by length: `fig`, `apple`, then the two six-letter words in their original order (stability).
- `key=lambda w: (-len(w), w)` returns a *tuple* for each word. Tuples compare item by item, so this sorts by the first item, and by the second where the first is equal. The minus sign turns "longest first" into an ordinary ascending sort.
- The `people` list is sorted by age from high to low and then by name.
- `itemgetter(1, 0)` is a ready-made key function meaning "item 1, then item 0". `max` and `min` accept `key` too.

Sorting by several criteria therefore rests on **tuple comparison**. To reverse the direction of a numeric field, negate it. A text field cannot be negated. For that case use **stability**: sort by the less important key first, and then by the more important one. The second sort keeps ties in the order the first sort left them.

```python-run
people = [("ana", 31), ("ben", 25), ("cy", 31), ("dee", 25)]
people.sort(key=lambda p: p[0], reverse=True)   # secondary: name descending
people.sort(key=lambda p: p[1])                 # primary: age ascending (stable!)
print(people)
```

The result is ordered by age ascending, and within each age by name descending: `dee, ben` (both 25), then `cy, ana` (both 31).

### Custom comparators

Occasionally the order cannot be expressed as a key computed from one item, because it depends on comparing two items with each other. The classic example: arrange numbers so that writing them side by side gives the largest possible number. Should 3 come before 30? Compare `"330"` with `"303"`. A function that takes two items and returns a negative number, zero or a positive number (for "first comes first", "equal", "second comes first") is called a **comparator**; `functools.cmp_to_key` converts one into a key.

```python-run
from functools import cmp_to_key

def largest_number(nums):
    strs = list(map(str, nums))
    cmp = lambda a, b: (a + b < b + a) - (a + b > b + a)   # negative if a should come first
    return "".join(sorted(strs, key=cmp_to_key(cmp))).lstrip("0") or "0"

print(largest_number([3, 30, 34, 5, 9]), largest_number([0, 0]))
```

The lambda returns −1 when `a + b` is the larger combination (so `a` should come first) and 1 in the opposite case, using the fact that `True` and `False` count as 1 and 0. The answers are `9534330` and, for two zeros, `0` (the `lstrip("0") or "0"` deals with a result made only of zeros).

More facts worth remembering: sorting values of different types (`[1, "a"]`) raises `TypeError`; `sorted` needs only the `<` operation (`__lt__`) from its items; `reverse=True` keeps stability; and sorting first is often the easiest route to an O(n log n) solution (problems about intervals, two pointers, or grouping).

## heapq: the priority queue

A **binary heap** is an ordinary list whose items are arranged by one rule: the item at position `i` is never larger than the items at positions `2i + 1` and `2i + 2`. One consequence follows at once: `heap[0]` is always the smallest item. (A heap with the smallest on top is a *min-heap*.) The rest of the list is only loosely ordered, which is what makes a heap cheap to maintain. The `heapq` module does not provide a heap class; it provides functions that keep this rule true on a plain list.

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

- `heapify(h)` rearranges the list into a heap. The printed list is not sorted; only `h[0]`, which is 1, is guaranteed.
- `heappush` adds 0, and three `heappop` calls return `[0, 1, 2]`: always the smallest remaining item.
- `nlargest` and `nsmallest` return the top or bottom `k` items, optionally by a key.
- `merge` combines several inputs that are *already sorted* into one sorted stream, lazily.

### Max-heaps and tuples

`heapq` provides only a min-heap. For a **max-heap**, where the largest comes out first, store the *negative* of each value (or tuples starting with a negated priority), and negate again when reading.

Entries in a priority queue are usually tuples, `(priority, item)`, and tuples compare item by item. That hides a trap: when two priorities are equal, Python goes on to compare the items themselves, and if they are, say, dictionaries, that raises `TypeError`. The standard fix is to put a unique, ever-increasing counter between the priority and the item:

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

The first part pops 8 (stored as −8) and then looks at the new top, 5. In the second part the tasks come out as `1 plan`, `2 write`, `2 test`: by priority, and among equal priorities in the order they were added, because the counter decides before the dictionaries are ever looked at.

### Heap patterns

**The k largest items, with a min-heap of size k.** The heap holds the best `k` items seen so far, with the *smallest of them* on top, the one that would be dropped first. A new item replaces the top only if it is larger. This takes O(n log k) time and O(k) memory, and it works on a stream that is too long to store:

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

**Dijkstra's algorithm** finds the shortest route from one point to every other point in a network whose connections have lengths. The idea: always continue from the nearest point not yet finished. "The nearest one, repeatedly, while new candidates keep arriving" is precisely what a heap is for.

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

The graph is a dictionary from each node to a list of (neighbour, length) pairs. `dist` holds the best known distance to each node, and the heap holds (distance, node) candidates. Each turn pops the nearest candidate. If a shorter route to that node has been found since the entry was pushed, the entry is out of date and is skipped. Otherwise each neighbour is examined, and whenever going through the current node gives a shorter distance, the distance is updated and a new candidate pushed. The output is `{'a': 0, 'b': 3, 'c': 1, 'd': 4}`: the best way to `b` is through `c`.

Other classic heap problems: merging k sorted lists, counting the meeting rooms needed (a min-heap of ending times), the running median (two heaps), and the task scheduler.

How to choose: for a single top-k on a small input, `sorted(xs)[:k]` at O(n log n) is perfectly fine; `heapq.nlargest` is O(n log k); and for k = 1, use `min` or `max`.

## bisect: binary search on sorted lists

**Binary search** looks for a position in a sorted list by repeatedly halving the range in which it can lie, which takes O(log n) steps. The `bisect` module (to bisect is to cut in two) does it for you. Its functions answer "at which position would `x` have to be inserted to keep the list sorted?":

- `bisect_left(a, x)` gives the leftmost such position: the first index `i` with `a[i] >= x`. If `x` is already present, this is the position of its first occurrence.
- `bisect_right(a, x)` (also available under the name `bisect`) gives the rightmost: the first `i` with `a[i] > x`, the position after the last occurrence.
- `insort(a, x)` inserts `x` at the right place. The search is O(log n), **but the insertion shifts items and is O(n)**.
- All of them accept `lo` and `hi` to limit the range and, from Python 3.10, a `key`.

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

For the three 20s at positions 1 to 3, `bisect_left` gives 1 and `bisect_right` gives 4; their difference, 3, is the number of 20s. A value that is absent gets the position where it would go: 25 belongs at 4, 5 at 0, and 99 at 6, the end. `index_of` turns this into an exact search by checking that the item found really equals `x`. `insort` puts 25 between 20 and 30.

Common questions and the expressions that answer them:

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

- `grade` converts a score into a letter. `bisect_right` counts how many breakpoints are less than or equal to the score, and that count is the position of the letter: 33 gives `F`, 60 gives `D`, 90 and 100 give `A`.
- `lis_length` solves a well-known interview problem: the length of the longest subsequence of strictly increasing numbers (a subsequence keeps the original order but may skip items). `tails[i]` holds the smallest possible last number of an increasing subsequence of length `i + 1`. Each new number either extends the longest subsequence so far or replaces the first tail that is not smaller than it, found by binary search. For the sample list the answer is 4 (for example 2, 3, 7, 18).

When an interviewer wants binary search written by hand, this loop, which is `bisect_left`, is the version to memorise:

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

`lo` and `hi` mark a range in which the answer must lie, `hi` not included. Each turn looks at the middle item. If it is smaller than `x`, the answer lies to the right, so `lo` moves past the middle. Otherwise the middle itself might be the answer, so `hi` moves to the middle. When the two meet, that position is the answer: 1 for the first 20, and 4 (the end) for 35.

## math essentials

```python-run
import math
print(math.gcd(84, 36), math.lcm(4, 6), math.isqrt(17), math.sqrt(16))
print(math.comb(5, 2), math.perm(5, 2), math.factorial(5), math.prod([1, 2, 3, 4]))
print(math.ceil(7 / 2), math.floor(-3.5), -(-7 // 2), round(2.5), round(3.5))
print(math.inf > 10**100, -math.inf, math.isclose(0.1 + 0.2, 0.3), math.log2(1024), math.log(100, 10))
print(divmod(17, 5), pow(3, 200, 13), abs(-3), sum([0.1] * 10), math.fsum([0.1] * 10))
```

Line by line: the greatest common divisor (12), least common multiple (12), whole-number square root (4) and ordinary square root (4.0); the number of combinations and permutations, a factorial and a product; rounding up (`ceil`), down (`floor`), ceiling division with integers only, and two calls of `round`; infinity, a tolerant comparison of floats and two logarithms; and finally `divmod`, modular power, absolute value, and a comparison of `sum` with the exact `math.fsum`, which gives 1.0 (Python versions before 3.12 print 0.9999999999999999 for the plain `sum`, a rounding error; newer versions add floats more carefully).

Notes for interviews:

- `float("inf")` or `math.inf` is the usual starting value when searching for a minimum: anything is smaller than it.
- `math.isqrt(n)` is an exact whole-number square root; `int(math.sqrt(n))` can be off by one for very large `n`.
- `-(-a // b)` divides and rounds *up* using integers only.
- `round()` rounds a value exactly halfway between two integers to the *even* one, a rule known as **banker's rounding**: `round(2.5) == 2`, `round(3.5) == 4`.
- Integers never overflow. Problems that ask for an answer "modulo 10⁹ + 7" use `% (10**9 + 7)` and `pow(a, b, m)`.

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

A reference list of the string moves that interview problems use most: changing case, reversing with `[::-1]`, keeping only letters and digits, converting between characters and their numbers, splitting and joining, formatting numbers, testing for anagrams by sorting the letters, comparing strings, and converting between number bases.

> [!INTERVIEW]
> State the costs as you write: "sorting is O(n log n) and stable", "heap push and pop are O(log n), heapify is O(n)", "`bisect` is O(log n) but `insort` is O(n) because of the shift". Know the max-heap trick (negate), the tie-breaker counter in tuples, and how `bisect_left` and `bisect_right` differ when the list contains duplicates.

## Under the hood

### How a heap keeps its shape

Picture a heap as a tree: one item at the top, two below it, four below those, each level filled from the left. Written out level by level, that tree is the list. The two items below position `i` (its *children*) sit at positions `2i + 1` and `2i + 2`, and the item above it (its *parent*) at `(i - 1) // 2`. The heap rule says every parent is no larger than its children.

Only two repair operations are needed. **Sift up**, after a new item has been appended at the end: while the item is smaller than its parent, swap the two. **Sift down**, after a pop has moved the last item to the top: while the item is larger than its smaller child, swap the two. Each follows a single path between top and bottom, and the tree has about log n levels, so both cost O(log n).

```python-run
import heapq

def push(heap, x):
    heap.append(x)
    i = len(heap) - 1
    while i > 0 and heap[i] < heap[(i - 1) // 2]:          # sift up
        parent = (i - 1) // 2
        heap[i], heap[parent] = heap[parent], heap[i]
        i = parent

def pop(heap):
    heap[0], heap[-1] = heap[-1], heap[0]
    smallest = heap.pop()
    i, n = 0, len(heap)
    while True:                                            # sift down
        left, right, least = 2 * i + 1, 2 * i + 2, i
        if left < n and heap[left] < heap[least]: least = left
        if right < n and heap[right] < heap[least]: least = right
        if least == i:
            return smallest
        heap[i], heap[least] = heap[least], heap[i]
        i = least

mine, ref = [], []
for x in [7, 2, 9, 4, 1, 8, 3]:
    push(mine, x); heapq.heappush(ref, x)
print(mine, mine == ref)
print([pop(mine) for _ in range(len(mine))])
```

These home-made `push` and `pop` follow that description line by line. The first print shows that the list built by `push` is identical to the one `heapq` builds (`True`). The second pops everything and gets the numbers in sorted order.

`heapify` applies sift-down to every parent, from the last one back to the top. Most items sit near the bottom of the tree and can move only a step or two, so the total cost is O(n), not O(n log n).

A heap cannot efficiently search for an item, remove one from the middle, or change a priority. The standard way round this is **lazy deletion**: push a new entry and, when popping, skip the entries that have gone out of date, as the Dijkstra example did.

### Why Timsort is fast on real data

Timsort begins by looking for stretches that are already in order, called **runs** (ascending, or strictly descending, which it reverses). It lengthens short runs with a simple insertion sort and then merges runs in a carefully balanced order. Real data is rarely completely random, so it often needs far fewer comparisons than n log n. The demo counts them:

```python-run
import random

class Counted:
    comparisons = 0
    def __init__(self, v): self.v = v
    def __lt__(self, other):
        Counted.comparisons += 1
        return self.v < other.v

def count(values):
    Counted.comparisons = 0
    sorted(Counted(v) for v in values)
    return Counted.comparisons

n = 2000
random.seed(0)
shuffled = random.sample(range(n), n)
print("already sorted :", count(range(n)))
print("reversed       :", count(range(n, 0, -1)))
print("two sorted runs:", count(list(range(0, n, 2)) + list(range(1, n, 2))))
print("random         :", count(shuffled), f"(n log2 n is about {int(n * 11)})")
```

`Counted` wraps a number and counts every `<` comparison performed on it. Already-sorted and reversed inputs need about `n` comparisons, two interleaved sorted runs need a few thousand, and random data needs close to the n log n figure.

The same experiment explains why a key function is efficient. The key is computed once per item, `n` calls in total, and the comparisons that follow are cheap comparisons of the stored keys. A `cmp_to_key` comparator, by contrast, runs your Python function for every one of the roughly n log n comparisons.

### The decorate-sort-undecorate idea

`key=` automates an old technique known as decorate-sort-undecorate: pair each item with its sort key, sort the pairs, then throw the keys away. Doing it by hand exposes the same trap that heaps have. When two keys are equal, tuple comparison moves on to the items themselves:

```python-run
people = [{"name": "ana", "age": 31}, {"name": "ben", "age": 31}]
try:
    sorted((p["age"], p) for p in people)              # tie on age -> compares the dicts
except TypeError as e:
    print("TypeError:", e)
decorated = sorted((p["age"], i, p) for i, p in enumerate(people))   # index breaks ties, keeps stability
print([p["name"] for _, _, p in decorated], [p["name"] for p in sorted(people, key=lambda p: p["age"])])
```

Both people are 31, so sorting the `(age, person)` pairs tries to compare two dictionaries and fails. Putting the original position between the key and the item breaks every tie and also preserves stability. The `key=` form on the last line does all of this for you.

## Sort, heap or bisect? Choosing by workload

| Workload | Best tool | Cost |
|---|---|---|
| order everything once | `sorted` / `list.sort` | O(n log n) |
| the k smallest/largest of n, once | `heapq.nsmallest/nlargest` | O(n log k) |
| only the min or max | `min` / `max` | O(n) |
| repeatedly take the smallest while adding items | heap | O(log n) per operation |
| many lookups in data that never changes | sort once + `bisect` | O(log n) per lookup |
| lookups **and** many insertions, kept sorted | `bisect.insort` if n is small; otherwise a heap (if only the min matters) or the third-party `sortedcontainers.SortedList` | O(n) per insort |
| membership only | `set` | O(1) avg |

## Debugging these tools

- **`TypeError: '<' not supported between instances of 'dict' and 'dict'`** (or of your own class): equal leading fields in a tuple forced the items to be compared. Add a tie-breaking index or use `key=`.
- **A "heap" gives items in the wrong order**: the list was changed without `heappush` / `heappop` (an `append`, a `sort(reverse=True)`, an item changed in place), which broke the heap rule; or it was looped over with `for` in the expectation of sorted order.
- **`bisect` returns nonsense**: the list is not sorted in the order you are searching by, for example sorted descending, or sorted by a key that was not passed to `bisect`.
- **Sorting numbers gives `[1, 10, 2]`**: they are strings. Convert them, or use `key=int`.
- **Off by one with `bisect`**: decide whether equal items should fall to the left or to the right of the insertion point, then test on a list that contains duplicates.

## Pitfalls recap

- `x = lst.sort()` gives `None`.
- Treating a heap as sorted: only `heap[0]` is the minimum. To get everything in order, pop repeatedly or use `sorted(heap)`.
- Tuples with equal priorities and items that cannot be compared raise `TypeError`; add a counter.
- `bisect` on an unsorted list returns garbage without any error.
- `insort` inside a loop is O(n²) overall.
- `round(0.5) == 0`, because of banker's rounding.

## Summary

Sort with `key` functions and tuple keys, relying on stability; use `cmp_to_key` for unusual orders. `heapq` maintains a min-heap on a list, giving O(log n) priority-queue operations and top-k selection. `bisect` performs binary search on sorted lists. `math` covers greatest common divisors, combinatorics, whole-number roots and infinity.

## Glossary

- **Timsort** - Python's sorting algorithm: O(n log n) at worst, O(n) on nearly sorted input, stable.
- **Stable sort** - a sort in which equal items keep their original relative order.
- **Key function** - a function called once per item whose results decide the order.
- **Comparator** - a function that compares two items and returns a negative, zero or positive number.
- **Priority queue** - a collection that always hands out its most urgent item next.
- **Heap (binary heap)** - a list arranged so that each parent is no larger than its children; `heap[0]` is the smallest.
- **Min-heap / max-heap** - a heap with the smallest / the largest item on top.
- **Sift up / sift down** - moving an item towards the top / the bottom until the heap rule holds again.
- **Heapify** - turning an arbitrary list into a heap, in O(n).
- **Lazy deletion** - leaving outdated entries in a heap and skipping them when they are popped.
- **Dijkstra's algorithm** - a shortest-route method that repeatedly continues from the nearest unfinished node.
- **Binary search** - finding a position in sorted data by repeatedly halving the range.
- **Insertion point** - the index at which a value would have to be inserted to keep a list sorted.
- **Run** - a stretch of input that is already in order.
- **Subsequence** - items taken from a sequence in their original order, possibly skipping some.
- **Banker's rounding** - rounding exact halves to the nearest even number.

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
