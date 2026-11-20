# collections: deque, Counter, defaultdict, OrderedDict

The `collections` module holds specialised containers that go beyond `list`, `dict`, `set` and `tuple`. In coding interviews they are the difference between a clumsy 20-line solution and a clean 6-line one, and several of them fix real performance traps (`list.pop(0)`, anyone?). This lesson covers the four you'll use constantly, plus `namedtuple` and `ChainMap`.

| Container | What it is | Reach for it when |
|---|---|---|
| `deque` | double-ended queue | queues, BFS, sliding windows, "last N items" |
| `Counter` | dict that counts hashables | frequencies, multisets, top-k, anagrams |
| `defaultdict` | dict with a default factory | grouping, adjacency lists, nested counters |
| `OrderedDict` | dict with reordering operations | LRU caches, order-sensitive equality |
| `namedtuple` | tuple with field names | lightweight immutable records |
| `ChainMap` | view over several dicts | layered configuration, scopes |

## deque

A `deque` ("deck") supports **O(1) appends and pops at both ends**. A `list` only does that at the right end; `list.pop(0)` and `list.insert(0, x)` are O(n) because every element shifts. Internally a deque is a doubly linked list of fixed-size blocks.

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

| Operation | Cost |
|---|---|
| `append`, `appendleft`, `pop`, `popleft` | O(1) |
| `d[0]`, `d[-1]` | O(1) |
| `d[i]` in the middle, `insert`, `remove`, `in` | O(n) |
| `rotate(k)` | O(k) |

So use a deque when you work at the ends, a list when you index in the middle.

### Queue for BFS

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

### Bounded deques: `maxlen`

`deque(maxlen=n)` automatically discards items from the opposite end when full — a ring buffer in one line:

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

### Monotonic deque: sliding-window maximum

A classic hard-ish interview pattern: keep indices in the deque such that their values are decreasing; the front is always the window's maximum. Each index is pushed and popped at most once → O(n).

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

## Counter

A `Counter` is a dict subclass mapping items to counts. Missing keys return `0` instead of raising.

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

### Multiset arithmetic

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

`need - have` being empty means every required character is available — the core check of "ransom note" and "minimum window substring".

`most_common(k)` uses a heap for small `k` (O(n log k)) and a full sort otherwise. **Tie order** follows first insertion, so if a problem demands alphabetical tie-breaking, sort explicitly: `sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))`.

## defaultdict

`defaultdict(factory)` calls `factory()` to create a value the first time a missing key is accessed with `d[key]`, stores it, and returns it. The factory is any zero-argument callable: `list`, `int`, `set`, `dict`, `lambda: ...`.

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

> [!WARNING]
> Merely *reading* `d[missing]` on a defaultdict **inserts** the key. Checking `if d[key]:` in a loop silently grows the dict (and can break "dictionary changed size during iteration"). Use `key in d` or `d.get(key)` for lookups that shouldn't create entries.

```python-run
from collections import defaultdict
d = defaultdict(int)
print(d["ghost"], len(d), d.get("other"), len(d))    # d["ghost"] created an entry; get() did not
```

`defaultdict` vs `dict.setdefault(k, [])` vs `Counter`: `setdefault` builds the default object on every call even when unused; `defaultdict` only when missing; `Counter` is the specialised tool for counting.

## OrderedDict

Regular dicts have preserved insertion order since Python 3.7, so `OrderedDict` is no longer needed just for ordering. It still offers three things a plain dict lacks:

1. `move_to_end(key, last=True)` — O(1) reordering;
2. `popitem(last=False)` — pop from the **front** (a plain dict's `popitem()` only pops the last);
3. order-**sensitive** equality between two OrderedDicts.

Those first two are exactly what an **LRU cache** needs:

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

Under the hood an OrderedDict pairs a hash map with a doubly linked list — the same design you'd hand-write if an interviewer bans the library.

## namedtuple

A factory for tuple subclasses with named fields: as light as a tuple, as readable as a class.

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

Named tuples are immutable, hashable (usable as dict keys, e.g. `visited` states), compare field by field, and work nicely in heaps. Choose a `dataclass` when you need mutability, defaults with logic, or methods.

## ChainMap

`ChainMap(a, b, c)` looks keys up in `a`, then `b`, then `c`, without copying. Writes go to the first map. It models layered settings (CLI args → environment → defaults) and nested scopes (it's how you'd model LEGB).

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

## Worked example: top-k frequent elements, three ways

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

> [!INTERVIEW]
> Name the right container and its complexity: "I'll use a `deque` for the BFS queue since `popleft` is O(1) — a list's `pop(0)` is O(n)"; "a `Counter` for frequencies"; "`defaultdict(list)` to build the adjacency list"; "an `OrderedDict` gives O(1) LRU with `move_to_end` and `popitem(last=False)`". Saying *why* matters as much as using them.

## Under the hood

**`defaultdict` is a dict with one extra hook.** Ordinary `dict.__getitem__` calls a method named `__missing__` when a key is absent — if the class defines one. `defaultdict` implements `__missing__` to call the factory, store the result and return it. That explains why only `d[key]` triggers the default, while `d.get(key)` and `key in d` (which don't go through `__getitem__`) never do. You can use the same hook yourself, and unlike the zero-argument factory, your `__missing__` receives the key:

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

`Counter.__missing__` returns `0` *without* inserting, which is why reading a missing count doesn't grow a Counter the way it grows a defaultdict.

**`deque` is a linked list of blocks.** Each block holds 64 item slots; appending at either end writes into the edge block and occasionally allocates a new one. No element ever moves, so both ends are O(1) — but reaching the middle means walking the chain, which is why `d[i]` is O(n). A list is the mirror image: one contiguous array, so O(1) indexing and O(n) front insertion.

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

**`OrderedDict`** keeps, in addition to the hash table, a doubly linked list threading the keys in order — so moving a key to either end or popping from the front is a few pointer updates. A plain dict stores entries in a compact array in insertion order; removing the *first* entry leaves a hole that later iteration must skip, which is why repeatedly popping the oldest item from a regular dict (`next(iter(d))`) degrades, while `OrderedDict.popitem(last=False)` stays O(1).

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

- A defaultdict that "contains keys nobody added": something *read* them with `[]`. For read-only phases, convert with `dict(d)` or set `d.default_factory = None` so missing keys raise again.
- Negative or zero counts lingering in a Counter: use `+counter` to strip them, and remember `most_common` still lists them.
- A bounded deque dropping data: that is its job — make sure the end you append to is the opposite of the end you can afford to lose.
- `json.dumps` of a `defaultdict`/`Counter`/`OrderedDict` works (they are dicts), but a `deque` or `namedtuple` needs `list(...)` / `._asdict()` first.

## Pitfalls recap

- `list.pop(0)` in a loop instead of `deque.popleft()`.
- Reading a missing key on a `defaultdict` inserts it.
- `Counter.most_common` tie order is insertion order, not alphabetical.
- `Counter` subtraction with `-` drops non-positive counts; `subtract()` keeps negatives.
- `extendleft` reverses the input order.
- Indexing the middle of a deque is O(n).

## Summary

`deque` gives O(1) operations at both ends and bounded buffers; `Counter` counts and does multiset algebra; `defaultdict` removes missing-key boilerplate for grouping; `OrderedDict` adds reordering for LRU-style logic; `namedtuple` makes readable immutable records; `ChainMap` layers mappings.

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
