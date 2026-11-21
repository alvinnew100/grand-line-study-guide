# collections: deque, Counter, defaultdict, OrderedDict

> **Before this lesson:** you need lists and their costs (including why `list.pop(0)` is slow) from [Lists, tuples and strings](#/lesson/python/py-sequences), dictionaries, sets and hashing from [Dictionaries and sets](#/lesson/python/py-dicts-sets), and classes from [Classes and instances](#/lesson/python/py-classes). The O-notation for costs is introduced in the sequences lesson.

## In plain words

Lists, dictionaries, sets and tuples cover most needs. For some very common jobs they are awkward or slow, and Python's standard `collections` module provides a specialised container for each of those jobs.

Think of a kitchen. A chef's knife can do almost everything, but a bread knife, a peeler and a whisk each do one task far better. Nobody is impressed by a cook who peels potatoes with a cleaver. The containers in this lesson are those extra tools:

- a **deque**: a line of items that is quick to add to and take from at *both* ends, like a queue of people where someone can join or leave at the front or the back;
- a **Counter**: a tally sheet that counts how many times each thing occurs;
- a **defaultdict**: a dictionary that creates an empty starting value by itself the first time a key is used;
- an **OrderedDict**: a dictionary whose entries can be moved to the front or back;
- a **namedtuple**: a tuple whose positions have names;
- a **ChainMap**: several dictionaries stacked so that a lookup tries each in turn.

In coding interviews these are the difference between a clumsy twenty-line solution and a clean six-line one, and choosing the right one, and saying why, is itself part of what is assessed. Several of them also remove real performance traps.

| Container | What it is | Reach for it when |
|---|---|---|
| `deque` | double-ended queue | queues, BFS, sliding windows, "last N items" |
| `Counter` | dict that counts hashables | frequencies, multisets, top-k, anagrams |
| `defaultdict` | dict with a default factory | grouping, adjacency lists, nested counters |
| `OrderedDict` | dict with reordering operations | LRU caches, order-sensitive equality |
| `namedtuple` | tuple with field names | lightweight immutable records |
| `ChainMap` | view over several dicts | layered configuration, scopes |

## deque

A `deque` (pronounced "deck", short for double-ended queue) supports **O(1) appends and removals at both ends**. A list is quick only at its right end: `list.pop(0)` and `list.insert(0, x)` are O(n), because every remaining item has to shift along by one place. A deque is built differently, as a chain of fixed-size blocks linked in both directions, so nothing ever has to shift.

```python-run
from collections import deque

d = deque([1, 2, 3])
d.append(4); d.appendleft(0)
print(d, d.pop(), d.popleft(), d)
d.extend([7, 8]); d.extendleft([-1, -2])      # note: extendleft reverses the order
print(d)
d.rotate(2); print(d)                         # rotate right by 2
d.rotate(-2); print(d, d[0], d[-1], len(d))
```

**Reading this code line by line**

- `append` adds at the right, `appendleft` at the left: the deque is now `0, 1, 2, 3, 4`.
- The `print` evaluates `d.pop()` (removes and returns the right-hand item, 4) and `d.popleft()` (removes and returns the left-hand item, 0). The first and last arguments are the same deque object, so both show its final state, `deque([1, 2, 3])`.
- `extend` adds several items at the right. `extendleft([-1, -2])` adds them at the left *one at a time*, so they end up in reverse order: `-2, -1, 1, 2, 3, 7, 8`.
- `rotate(2)` moves two items from the right end round to the left; `rotate(-2)` moves them back.
- `d[0]` and `d[-1]` read the two ends; `len(d)` is 7.

| Operation | Cost |
|---|---|
| `append`, `appendleft`, `pop`, `popleft` | O(1) |
| `d[0]`, `d[-1]` | O(1) |
| `d[i]` in the middle, `insert`, `remove`, `in` | O(n) |
| `rotate(k)` | O(k) |

So use a deque when the work happens at the ends, and a list when you need to reach items in the middle by position.

### A queue for breadth-first search

A **queue** is a waiting line: items leave in the order they arrived (first in, first out, or FIFO). The best-known algorithm that needs one is **breadth-first search** (BFS), which explores a grid or network outwards from a starting point, first everything one step away, then everything two steps away, and so on. Because it proceeds in order of distance, the first time it reaches the goal it has found a shortest route.

```python-run
from collections import deque

def shortest_path_length(grid, start, goal):
    rows, cols = len(grid), len(grid[0])
    queue = deque([(start, 0)])
    seen = {start}
    while queue:
        (r, c), dist = queue.popleft()            # O(1)
        if (r, c) == goal:
            return dist
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == "." and (nr, nc) not in seen:
                seen.add((nr, nc))
                queue.append(((nr, nc), dist + 1))
    return -1

grid = ["..#.",
        "..#.",
        "...."]
print(shortest_path_length(grid, (0, 0), (0, 3)))
```

The grid is a list of strings in which `.` is open floor and `#` is a wall; positions are `(row, column)` pairs. The queue holds pairs of (position, distance from the start), and the set `seen` remembers every position already queued, so that none is visited twice. Each turn of the loop takes the oldest entry from the left of the queue. If it is the goal, its distance is the answer. Otherwise the four neighbouring positions are examined, and each one that is inside the grid, open and new is added at the right with a distance one greater. For this grid the wall forces a detour along the bottom row, and the answer is 7.

The line to notice is `queue.popleft()`. With a list and `pop(0)` the whole search would slow down from linear to quadratic time.

### Bounded deques: `maxlen`

`deque(maxlen=n)` is a deque with a fixed capacity. When it is full, adding an item at one end automatically drops one from the other end. A fixed-size store that overwrites its oldest contents is known as a **ring buffer**, and here it takes one line:

```python-run
from collections import deque
last3 = deque(maxlen=3)
for event in "abcdef":
    last3.append(event)
print(last3)

def tail(lines, n=2):               # like the Unix tail command
    return list(deque(lines, maxlen=n))
print(tail(["l1", "l2", "l3", "l4"]))
```

After six letters have been appended, only the last three remain: `deque(['d', 'e', 'f'], maxlen=3)`. The `tail` function uses the same idea to return the last `n` items of any iterable, however long, while holding only `n` items in memory.

### Monotonic deque: sliding-window maximum

A classic, fairly hard interview problem: for every window of `k` neighbouring numbers, report the largest. Recomputing `max` for each window costs O(n·k). The faster method keeps a deque of *positions* whose values are in decreasing order (a **monotonic** deque, monotonic meaning "always going one way"). The front of the deque is then always the position of the current window's maximum.

```python-run
from collections import deque

def sliding_max(nums, k):
    dq, out = deque(), []
    for i, x in enumerate(nums):
        while dq and nums[dq[-1]] <= x:     # smaller values can never be the max again
            dq.pop()
        dq.append(i)
        if dq[0] <= i - k:                  # front fell out of the window
            dq.popleft()
        if i >= k - 1:
            out.append(nums[dq[0]])
    return out

print(sliding_max([1, 3, -1, -3, 5, 3, 6, 7], 3))
```

For each new number `x` at position `i`:

1. Remove positions from the *right* of the deque while their values are less than or equal to `x`. Those numbers are older and smaller than `x`, so they can never again be a window's maximum.
2. Append `i`.
3. If the position at the *front* has slid out of the window (`dq[0] <= i - k`), remove it.
4. Once the first full window has been seen (`i >= k - 1`), the value at the front position is that window's maximum.

Every position is appended once and removed at most once, so the total work is O(n), whatever `k` is. The output is `[3, 3, 5, 5, 6, 7]`.

## Counter

A `Counter` is a dictionary (strictly, a subclass of `dict`) that maps items to how many times they have been seen. Hand it any iterable and it counts the items. Asking for an item it has never seen gives `0`; no `KeyError` is raised.

```python-run
from collections import Counter

c = Counter("mississippi")
print(c, c["s"], c["z"])                    # missing key -> 0, no KeyError
print(c.most_common(2))
c.update("sip")                             # add counts
c.subtract("mmm")                           # subtract (may go negative)
print(c, sum(c.values()), list(c.elements())[:5])
print(Counter(["a", "b", "a"]), Counter({"x": 3}), Counter(a=2))
```

- `Counter("mississippi")` counts the letters: four `i`, four `s`, two `p`, one `m`. `c["z"]` is 0.
- `most_common(2)` returns the two most frequent items with their counts.
- `update("sip")` adds one to the counts of `s`, `i` and `p`. `subtract("mmm")` takes three from `m`, which drops to −2: counts are allowed to go negative.
- `sum(c.values())` is the total of all counts; `elements()` produces each item repeated as many times as its (positive) count.
- The last line shows three other ways to create a Counter: from a list, from a dictionary and from keyword arguments.

### Multiset arithmetic

A **multiset** is like a set, except that an item may be present several times. A Counter is a multiset, and the usual operators work on it:

```python-run
from collections import Counter
a, b = Counter("aabbbc"), Counter("abbd")
print(a + b)      # add counts
print(a - b)      # subtract, dropping zero/negative results
print(a & b)      # intersection: min of counts
print(a | b)      # union: max of counts
print(Counter("listen") == Counter("silent"))      # anagram test
need, have = Counter("aabc"), Counter("abcabcx")
print(not (need - have), need <= have)             # 'have' covers 'need' (<= needs 3.10+)
```

The comments name the four operations. `Counter("listen") == Counter("silent")` is `True`, the neatest test for an **anagram** (two words made of the same letters). The last line asks "does `have` contain at least everything in `need`?" in two ways: `need - have` is empty when nothing is missing, and `need <= have` says the same directly. That check is the heart of interview problems such as "ransom note" and "minimum window substring".

`most_common(k)` uses a heap (see the next lesson) when `k` is small, costing O(n log k), and a full sort otherwise. Items with **equal counts** come out in the order they were first inserted. If a problem demands that ties be broken alphabetically, sort explicitly: `sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))`.

## defaultdict

A `defaultdict` is a dictionary that is given a function when it is created, called the **factory**. The first time a missing key is looked up with `d[key]`, the dictionary calls the factory with no arguments, stores the result under that key and returns it. The factory can be anything callable with no arguments: `list` (gives `[]`), `int` (gives `0`), `set`, `dict`, or a `lambda`.

```python-run
from collections import defaultdict

by_len = defaultdict(list)
for w in ["sun", "moon", "sky", "star", "sea"]:
    by_len[len(w)].append(w)                 # no "if key not in d" dance
print(dict(by_len))

graph = defaultdict(set)                     # adjacency list
for u, v in [(1, 2), (2, 3), (1, 3)]:
    graph[u].add(v); graph[v].add(u)
print(dict(graph))

tree = lambda: defaultdict(tree)             # arbitrarily nested dict
cfg = tree()
cfg["db"]["primary"]["host"] = "localhost"
print(cfg["db"]["primary"]["host"])

counts = defaultdict(lambda: defaultdict(int))
for user, page in [("a", "/"), ("a", "/x"), ("b", "/"), ("a", "/")]:
    counts[user][page] += 1
print({u: dict(p) for u, p in counts.items()})
```

Four uses, in order:

- **Grouping.** `by_len[len(w)].append(w)` needs no check for a new key, because a missing key starts as an empty list. The words end up grouped by length.
- **A graph.** A graph is a set of points (nodes) joined by connections (edges). An **adjacency list** stores, for each node, the set of its neighbours; `defaultdict(set)` builds one directly from a list of connections.
- **Nesting without limit.** `tree` is a function that returns a defaultdict whose factory is `tree` itself, so every missing level is created on demand and `cfg["db"]["primary"]["host"]` can be assigned in one go.
- **Counting on two levels.** A defaultdict of defaultdicts of integers counts page views per user.

> [!WARNING]
> Merely *reading* `d[missing]` on a defaultdict **inserts** the key. A test such as `if d[key]:` inside a loop silently grows the dictionary, and can trigger "dictionary changed size during iteration". For lookups that should not create entries, use `key in d` or `d.get(key)`.

```python-run
from collections import defaultdict
d = defaultdict(int)
print(d["ghost"], len(d), d.get("other"), len(d))    # d["ghost"] created an entry; get() did not
```

The output `0 1 None 1` shows it: reading `d["ghost"]` returned the default 0 *and* created an entry (length 1); `d.get("other")` returned `None` and created nothing.

How the three alternatives compare: `dict.setdefault(k, [])` builds the default object on every call, whether or not it is needed; `defaultdict` builds it only when the key is missing; `Counter` is the dedicated tool when the values are counts.

## OrderedDict

Ordinary dictionaries have kept insertion order since Python 3.7, so `OrderedDict` is no longer needed merely for that. It still offers three things a plain dictionary lacks:

1. `move_to_end(key, last=True)`: move an entry to the back (or, with `last=False`, to the front) in O(1);
2. `popitem(last=False)`: remove and return the entry at the **front** (a plain dictionary's `popitem()` removes only the last);
3. equality that takes **order** into account when two OrderedDicts are compared.

The first two are exactly what an **LRU cache** needs. A cache stores a limited number of results so that they need not be computed again; LRU, "least recently used", is the rule for what to throw out when it is full: the entry that has gone unused for longest. Designing one is a very common interview task.

```python-run
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.data = OrderedDict()

    def get(self, key):
        if key not in self.data:
            return -1
        self.data.move_to_end(key)            # mark as most recently used
        return self.data[key]

    def put(self, key, value):
        if key in self.data:
            self.data.move_to_end(key)
        self.data[key] = value
        if len(self.data) > self.capacity:
            self.data.popitem(last=False)     # evict least recently used

cache = LRUCache(2)
cache.put("a", 1); cache.put("b", 2)
print(cache.get("a"))                         # 'a' is now most recent
cache.put("c", 3)                             # evicts 'b'
print(cache.get("b"), list(cache.data))

print(OrderedDict(a=1, b=2) == OrderedDict(b=2, a=1), dict(a=1, b=2) == dict(b=2, a=1))
```

The dictionary is kept in order of use, oldest at the front and newest at the back. `get` moves the key it has read to the back. `put` does the same for an existing key, stores the value, and, if the cache is now over capacity, removes the entry at the front. In the test, capacity is 2: after `a` and `b` are stored and `a` is read, storing `c` evicts `b`, the least recently used. Looking `b` up afterwards gives −1, and the remaining keys are `['a', 'c']`.

The last line prints `False True`: two OrderedDicts with the same entries in a different order are not equal, while two plain dictionaries are.

Inside, an OrderedDict combines a hash table with a doubly linked list (a chain in which every entry knows both its neighbours). That is the same design you would write by hand if an interviewer forbade the library.

## namedtuple

`namedtuple` creates a new kind of tuple whose positions also have names: as light as a tuple, as readable as a class.

```python-run
from collections import namedtuple
from typing import NamedTuple

Point = namedtuple("Point", ["x", "y"])
p = Point(3, y=4)
print(p, p.x + p.y, p[0], p._asdict(), p._replace(x=0))
x, y = p                                      # still unpacks like a tuple

class Edge(NamedTuple):                       # typed, class-style syntax
    src: str
    dst: str
    weight: float = 1.0

e = Edge("a", "b")
print(e, e.weight, sorted([Edge("b", "c", 2), Edge("a", "z", 9)]))
```

`Point(3, y=4)` can be read by name (`p.x`) or by position (`p[0]`), converted to a dictionary with `_asdict()`, and "changed" only by making a modified copy with `_replace`. It still unpacks like any tuple. The second form, a class inheriting from `typing.NamedTuple`, does the same with type hints and allows defaults; `Edge("a", "b")` gets a weight of 1.0. Because named tuples compare field by field, sorting a list of edges orders them by `src` first.

Named tuples are immutable and hashable, so they can be dictionary keys or members of a `visited` set, and they work well in heaps. Choose a dataclass when you need to change fields, compute defaults, or add methods.

## ChainMap

`ChainMap(a, b, c)` presents several dictionaries as one. A lookup tries `a`, then `b`, then `c`, and nothing is copied. Writing always goes to the first dictionary. It suits layered settings (command-line options override environment settings, which override defaults) and nested scopes; the LEGB name lookup from the scope lesson could be modelled with one.

```python-run
from collections import ChainMap
defaults = {"color": "blue", "debug": False, "port": 8000}
env = {"port": 9000}
cli = {"debug": True}
settings = ChainMap(cli, env, defaults)
print(settings["debug"], settings["port"], settings["color"])
settings["color"] = "red"                    # written to cli, the first map
print(cli, defaults["color"])
```

`debug` is found in `cli`, `port` in `env` and `color` only in `defaults`, so the first line prints `True 9000 blue`. Assigning `settings["color"]` writes into `cli`; the defaults still say `blue`.

## Worked example: top-k frequent elements, three ways

The task: return the `k` values that occur most often.

```python-run
from collections import Counter, defaultdict
import heapq

nums = [1, 1, 1, 2, 2, 3, 4, 4, 4, 4]
k = 2

# 1. Counter does it all: O(n log k)
print([x for x, _ in Counter(nums).most_common(k)])

# 2. explicit heap: O(n log k)
counts = Counter(nums)
print(heapq.nlargest(k, counts, key=counts.get))

# 3. bucket sort by frequency: O(n)
buckets = defaultdict(list)
for x, c in counts.items():
    buckets[c].append(x)
out = []
for freq in range(len(nums), 0, -1):
    out.extend(buckets.get(freq, []))
    if len(out) >= k:
        break
print(out[:k])
```

All three print `[4, 1]`. The first lets `Counter.most_common` do everything. The second counts and then asks `heapq.nlargest` for the `k` keys with the largest counts. The third avoids sorting altogether: it groups values into "buckets" by their count, then walks the possible counts from the highest downwards, collecting values until it has `k`. A count can be at most `len(nums)`, so this takes O(n) time.

> [!INTERVIEW]
> Name the right container and its cost: "I'll use a `deque` for the BFS queue, since `popleft` is O(1) and a list's `pop(0)` is O(n)"; "a `Counter` for the frequencies"; "`defaultdict(list)` to build the adjacency list"; "an `OrderedDict` gives an O(1) LRU cache with `move_to_end` and `popitem(last=False)`". Saying *why* counts as much as using them.

## Under the hood

**`defaultdict` is a dictionary with one extra hook.** When a key is absent, the ordinary `dict.__getitem__` (the method behind `d[key]`) calls a method named `__missing__`, if the class defines one. `defaultdict` defines `__missing__` to call the factory, store the result and return it. That explains why only `d[key]` produces a default, while `d.get(key)` and `key in d`, which do not go through `__getitem__`, never do. You can use the same hook in a class of your own, and your `__missing__` is even told which key was missing, which the no-argument factory is not:

```python-run
class KeyDefault(dict):
    """Like defaultdict, but the default depends on the missing key."""
    def __init__(self, factory):
        super().__init__()
        self.factory = factory
    def __missing__(self, key):
        value = self[key] = self.factory(key)
        return value

squares = KeyDefault(lambda k: k * k)
print(squares[7], squares[12], dict(squares), squares.get(99), 99 in squares)

from collections import Counter
print(Counter.__missing__(Counter(), "anything"))    # Counter's hook returns 0 and stores nothing
```

`KeyDefault` computes a default from the key itself: `squares[7]` is 49 and is stored; `get(99)` and `99 in squares` bypass the hook. The final line calls `Counter`'s own hook directly: it returns `0` *without* storing anything, which is why reading a missing count does not grow a Counter the way it grows a defaultdict.

**A `deque` is a linked chain of blocks.** Each block has room for 64 items. Appending at either end writes into the block at that end and occasionally starts a new block. No item ever moves, so both ends are O(1). Reaching the middle, however, means walking along the chain, which is why `d[i]` is O(n). A list is the mirror image: one unbroken array, giving O(1) access by position and O(n) insertion at the front.

```python-run
import timeit
from collections import deque

n = 20_000
setup = f"from collections import deque; lst = list(range({n})); dq = deque(range({n}))"
for label, stmt in [
    ("list  middle index", f"lst[{n // 2}]"),
    ("deque middle index", f"dq[{n // 2}]"),
    ("list  insert front", "lst.insert(0, 0); lst.pop(0)"),
    ("deque append front", "dq.appendleft(0); dq.popleft()"),
]:
    t = min(timeit.repeat(stmt, setup, number=2000, repeat=3))
    print(f"{label}: {t / 2000 * 1e9:8.0f} ns")
```

The four timings (in nanoseconds, billionths of a second) show the trade-off in numbers: reading the middle is far quicker on the list, and working at the front is far quicker on the deque.

**An `OrderedDict`** keeps, next to its hash table, a doubly linked list that threads the keys in order, so moving a key to either end or removing the first one means changing a few links. A plain dictionary stores its entries in a compact array in insertion order. Removing the *first* entry leaves a gap that later loops must step over, which is why repeatedly removing the oldest item from a plain dictionary (through `next(iter(d))`) gets slower and slower, while `OrderedDict.popitem(last=False)` stays O(1).

## Which container? A decision table

| You need | Use | Not |
|---|---|---|
| FIFO queue / BFS frontier | `deque` + `popleft()` | `list.pop(0)` |
| LIFO stack | `list` + `append`/`pop` | `deque` (fine, but unnecessary) |
| last N items | `deque(maxlen=N)` | manual slicing `lst = lst[-N:]` |
| counts, most common | `Counter` | `dict` + `if key in` |
| group items by key | `defaultdict(list)` | `setdefault` in a hot loop |
| nested auto-creating dict | `defaultdict(lambda: defaultdict(int))` | chains of `if` checks |
| LRU / move-to-front order | `OrderedDict` | `list.remove` + `append` (O(n)) |
| immutable record, dict key | `namedtuple` / frozen dataclass | a list or dict |
| thread-safe queue between threads | `queue.Queue` | a bare `deque` with your own locking |
| priority order | `heapq` on a list | sorting after every insert |

## Common mistakes and how to spot them

```python-run
from collections import defaultdict, Counter, deque

graph = defaultdict(list, {"a": ["b"]})
for node in list(graph):                 # list(): we may add keys while looping
    for nb in graph[node]:
        graph[nb]                        # touching a neighbour CREATES its entry
print(dict(graph))                       # 'b' appeared, with an empty list

c = Counter("aab")
c["a"] -= 5
print(c, +c, c.total() if hasattr(c, "total") else sum(c.values()))   # +c drops non-positive counts

d = deque([1, 2, 3], maxlen=3)
d.appendleft(0)                          # pushes OUT the right end, silently
print(d)
dd = defaultdict(list)
print(dd == {}, repr(dd)[:28])           # converts cleanly: dict(dd) before returning or serialising
```

What the demo shows, and how to recognise each mistake:

- A defaultdict that "contains keys nobody added": something *read* them with `[]`. In the demo, merely touching `graph[nb]` created an entry for `b`. For phases that only read, convert with `dict(d)`, or set `d.default_factory = None` so that missing keys raise an error again.
- Zero or negative counts lingering in a Counter: `+counter` returns a copy without them. Remember that `most_common` still lists them.
- A bounded deque losing data: that is its purpose. Make sure the end you add to is the opposite of the end you can afford to lose; `appendleft` on a full deque pushes an item off the *right*.
- `json.dumps` works on a `defaultdict`, `Counter` or `OrderedDict` (they are dictionaries), but a `deque` or `namedtuple` needs `list(...)` or `._asdict()` first.

## Pitfalls recap

- `list.pop(0)` in a loop where `deque.popleft()` belongs.
- Reading a missing key of a `defaultdict` inserts it.
- `Counter.most_common` breaks ties by insertion order, not alphabetically.
- Subtracting Counters with `-` drops counts that are zero or negative; the `subtract()` method keeps them.
- `extendleft` reverses the order of what it adds.
- Reaching into the middle of a deque by position is O(n).

## Summary

A `deque` gives O(1) operations at both ends and fixed-size buffers; a `Counter` counts and does multiset arithmetic; a `defaultdict` removes the missing-key ceremony from grouping; an `OrderedDict` adds reordering for LRU-style logic; a `namedtuple` makes readable immutable records; a `ChainMap` layers dictionaries.

## Glossary

- **deque** - a double-ended queue: O(1) adding and removing at both ends.
- **Queue (FIFO)** - a collection from which items leave in the order they arrived.
- **Breadth-first search (BFS)** - exploring outwards from a start, nearest positions first, using a queue.
- **Ring buffer** - a fixed-size store that overwrites its oldest items; `deque(maxlen=n)`.
- **Monotonic deque** - a deque whose values are kept always increasing or always decreasing.
- **Sliding window** - a fixed-length run of neighbouring items that moves along a sequence.
- **Counter** - a dictionary that counts hashable items.
- **Multiset** - a set in which an item can occur more than once.
- **Anagram** - a word made of exactly the same letters as another.
- **defaultdict / factory** - a dictionary that creates missing values automatically / the function it calls to create them.
- **Adjacency list** - for each node of a graph, the collection of its neighbours.
- **`__missing__`** - the hook a `dict` subclass can define to handle absent keys.
- **OrderedDict** - a dictionary with O(1) reordering and removal from either end.
- **LRU cache** - a limited store that discards the least recently used entry when full.
- **Evict** - to remove an entry from a cache to make room.
- **namedtuple** - a tuple type whose fields have names.
- **ChainMap** - a view that looks keys up in several dictionaries in turn.

```quiz
[
  {"q": "Why prefer `deque.popleft()` to `list.pop(0)` for a queue?", "options": ["It returns a copy", "popleft is O(1); list.pop(0) shifts all elements, O(n)", "Lists cannot pop from the left", "deque is thread-unsafe"], "answer": 1,
   "explain": "A deque is designed for constant-time operations at both ends."},
  {"q": "`Counter('aab')['z']` evaluates to:", "options": ["KeyError", "None", "0", "1"], "answer": 2,
   "explain": "Counter returns 0 for missing keys (and does not insert them)."},
  {"q": "What happens when you evaluate `d['x']` on `d = defaultdict(list)` and 'x' is missing?", "options": ["KeyError", "Returns [] without storing it", "Creates d['x'] = [] and returns it", "Returns None"], "answer": 2,
   "explain": "The factory is called, the result stored under the key, and returned — reading mutates the dict."},
  {"q": "Which OrderedDict methods make an O(1) LRU cache possible?", "options": ["sort and reverse", "move_to_end and popitem(last=False)", "setdefault and update", "keys and values"], "answer": 1,
   "explain": "move_to_end marks recency; popitem(last=False) evicts the oldest entry."},
  {"q": "`deque('abcde', maxlen=3)` contains:", "options": ["a, b, c", "c, d, e", "all five", "An error"], "answer": 1,
   "explain": "A bounded deque keeps the most recent maxlen items, discarding from the left as new ones arrive on the right."},
  {"q": "`Counter('aab') - Counter('abb')` is:", "options": ["Counter({'a': 1})", "Counter({'a': 1, 'b': -1})", "Counter()", "Counter({'a': 1, 'b': 0})"], "answer": 0,
   "explain": "The - operator keeps only positive counts: a: 2-1 = 1, b: 1-2 = -1 is dropped."},
  {"q": "A namedtuple instance is:", "options": ["Mutable and unhashable", "Immutable and hashable, like a tuple, with named field access", "A dict subclass", "A dataclass"], "answer": 1,
   "explain": "It is a tuple subclass; fields are accessible by name or index."}
]
```

> **Source:** Python docs, *Library Reference* `collections` — "Container datatypes"; Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, §1.11 (existing modules: collections), ch. 6 (stacks, queues, deques) and ch. 10 (maps).
