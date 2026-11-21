import random

R = random.Random(71)
G = ("prereqs", "intuition", "hints", "brute_force", "approach", "complexity", "pitfalls", "follow_up")


def _starter(sol):
    out = []
    for ln in sol.splitlines():
        s = ln.strip()
        if ln.startswith("class "):
            out.append(ln)
        elif s.startswith("def ") and (ln.startswith("    def ") or ln.startswith("def ")) and (
                not s.startswith("def _") or s.startswith("def __init__")):
            out.append(ln)
            out.append(ln[:len(ln) - len(ln.lstrip())] + "    pass")
    return "\n".join(out) + "\n"


def P(id, title, diff, pattern, entry, desc, sol, tests, wrong, guide, **kw):
    if "class Solution" not in sol:
        kw.setdefault("kind", "class")
    return dict(id="ctci-" + id, title=title, difficulty=diff, pattern=pattern, entry=entry,
                description=desc.strip() + "\n", starter=_starter(sol), solution=sol, tests=tests,
                wrong_solutions=wrong, guide=dict(zip(G, guide)), **kw)


def _ops(name, n, makers):
    ops, args = [name[0]], [name[1]]
    for _ in range(n):
        op, fn = R.choice(makers)
        ops.append(op)
        args.append(fn())
    return [ops, args]


def _rs(n, alpha):
    return "".join(R.choice(alpha) for _ in range(n))


_ZOO = [["Animal", "", [["speak", True], ["eat", False], ["id", False]]],
        ["Dog", "Animal", [["speak", False], ["eat", False], ["fetch", True]]],
        ["Puppy", "Dog", [["fetch", False], ["nap", False]]],
        ["Cat", "Animal", [["id", False]]]]
_CHAIN = [["C0", "", [["m", False], ["v", True]]]] + [["C%d" % i, "C%d" % (i - 1), ([["m", False]] if i % 3 == 0 else []) + ([["v", False]] if i % 5 == 0 else [])] for i in range(1, 300)]
_names = ["n%03d" % i for i in range(400)]
_dict = sorted({_rs(R.randint(1, 5), "abc") for _ in range(300)})
_grid60 = [[R.randint(-20, 20) for _ in range(60)] for _ in range(60)]
_land = [[R.choice([0, 0, 1, 2, 3]) for _ in range(120)] for _ in range(120)]

PROBLEMS = [
P("tail-lines", "Tail of a Log", "Easy", "C and C++", "lastLines",
"""
A log file is delivered as a stream of lines, far too long to keep in memory. Return its **last `k` lines in their original order**. If the stream has fewer than `k` lines, return all of them.

The stream is given as a list for convenience, but read it **once from the front**, as you would read a file in C++ with `getline`, and never hold more than `k` lines at a time: use a fixed-size circular buffer.

**Constraints:** `0 <= k <= 10^4`; up to `2·10^4` lines.

**Example 1:** `lines = ["a", "b", "c", "d", "e"], k = 2` → `["d", "e"]`

**Example 2:** `lines = ["a", "b"], k = 0` → `[]`
""",
'''class Solution:
    def lastLines(self, lines: List[str], k: int) -> List[str]:
        if k == 0:
            return []
        ring = [None] * k
        count = 0
        for line in lines:
            ring[count % k] = line
            count += 1
        if count <= k:
            return ring[:count]
        start = count % k
        return ring[start:] + ring[:start]
''',
[[["a", "b", "c", "d", "e"], 2], [["a", "b"], 0], [[], 3], [["x"], 1], [["x"], 5], [["a", "b", "c"], 3], [["a", "b", "c", "d"], 3],
 [["a", "b", "c", "d", "e", "f", "g"], 3], [["same", "same", "same"], 2], [["l%d" % i for i in range(8000)], 7],
 [["l%d" % i for i in range(8000)], 3999], [["l%d" % i for i in range(3000)], 10000], [["a", "b", "c", "d", "e", "f"], 4]],
['''class Solution:
    def lastLines(self, lines, k):
        return lines[-k:]
''', '''class Solution:
    def lastLines(self, lines, k):
        if k == 0:
            return []
        ring = [None] * k
        count = 0
        for line in lines:
            ring[count % k] = line
            count += 1
        return [x for x in ring if x is not None]
'''],
("Arrays and the modulo operator; circular buffers appear in [Queues and deques](#/lesson/dsa-foundations/queues-deques).",
 "You cannot know which lines are the last ones until the stream ends, so keep a rolling window of the most recent k. A circular buffer overwrites the oldest entry with the newest: the write position wraps around with `% k`.",
 ["Reading the file twice (once to count) works but doubles the I/O. Can one pass do it?",
  "Write line number `i` into slot `i % k`.",
  "At the end the oldest surviving line is in slot `count % k` (when at least k lines were read). Output from there, wrapping once."],
 "Read all lines into a list and slice the end: O(n) memory for an answer of size k.",
 "Fill `ring[count % k]`. If `count <= k` the buffer never wrapped: return the first `count` slots. Otherwise rotate: `ring[start:] + ring[:start]` with `start = count % k`.\n\nDry run lines a…g, k = 3: slots after each write: a/b/c, then d overwrites slot 0, e slot 1, f slot 2, g slot 0. count 7, start 1 → [e, f] + [g].",
 "Time O(n), memory O(k).",
 "`lines[-0:]` is the *whole* list in Python, so k = 0 needs its own case. Returning the buffer without rotating gives the wrong order (second wrong solution). Modulo by zero when k = 0.",
 "In C++ you would use `std::vector<std::string>` of size k or `std::deque` with `pop_front`. Discuss seeking backwards from the end of the file as an alternative that avoids reading everything.")),

P("vtable-dispatch", "Which Method Runs?", "Medium", "C and C++", "resolve",
"""
Simulate how C++ chooses a method implementation. A class hierarchy (single inheritance) is given as a list of entries `[name, parent, methods]`, where `parent` is `""` for a root class and `methods` is a list of `[method_name, declared_virtual]` pairs that the class itself defines. Parents are listed before their children.

A call `ptr->method()` is made through a pointer whose **declared (static) type** is `static_type` while the object it points to has **actual (dynamic) type** `dynamic_type`; `dynamic_type` is `static_type` or one of its descendants.

Rules:

1. Starting at `static_type` and walking up through the parents, find the nearest class that defines `method`. If there is none, the call does not compile: return `"error"`.
2. The method is **virtual** if that class, or any ancestor of it, declares a method of that name with `declared_virtual = True`.
3. If it is not virtual, the implementation found in step 1 runs. If it is virtual, the implementation that runs is the nearest one found walking up from `dynamic_type`.

Return the name of the class whose implementation runs.

**Example:** classes `Animal { virtual speak; eat }`, `Dog : Animal { speak; eat }`. Through an `Animal*` pointing at a `Dog`: `speak` → `"Dog"` (virtual), `eat` → `"Animal"` (not virtual).
""",
'''class Solution:
    def resolve(self, classes: List[List], static_type: str, dynamic_type: str, method: str) -> str:
        parent, own = {}, {}
        for name, par, methods in classes:
            parent[name] = par
            own[name] = {m: virt for m, virt in methods}

        def nearest(cls):
            while cls and method not in own[cls]:
                cls = parent[cls]
            return cls
        found = nearest(static_type)
        if not found:
            return "error"
        cls, virtual = found, False
        while cls:
            if own[cls].get(method):
                virtual = True
            cls = parent[cls]
        return nearest(dynamic_type) if virtual else found
''',
[[_ZOO, "Animal", "Dog", "speak"], [_ZOO, "Animal", "Dog", "eat"], [_ZOO, "Animal", "Dog", "fetch"], [_ZOO, "Dog", "Puppy", "fetch"],
 [_ZOO, "Animal", "Puppy", "speak"], [_ZOO, "Dog", "Puppy", "eat"], [_ZOO, "Animal", "Cat", "id"], [_ZOO, "Cat", "Cat", "id"],
 [_ZOO, "Puppy", "Puppy", "nap"], [_ZOO, "Dog", "Puppy", "nap"], [_ZOO, "Animal", "Animal", "speak"], [_ZOO, "Cat", "Cat", "speak"],
 [_ZOO, "Dog", "Puppy", "id"], [_CHAIN, "C0", "C299", "v"], [_CHAIN, "C7", "C299", "m"], [_CHAIN, "C1", "C4", "v"],
 [_CHAIN, "C100", "C298", "v"], [_ZOO, "Animal", "Dog", "missing"]],
['''class Solution:
    def resolve(self, classes, static_type, dynamic_type, method):
        parent, own = {}, {}
        for name, par, methods in classes:
            parent[name] = par
            own[name] = {m: virt for m, virt in methods}
        cls = dynamic_type
        while cls and method not in own[cls]:
            cls = parent[cls]
        return cls or "error"
''', '''class Solution:
    def resolve(self, classes, static_type, dynamic_type, method):
        parent, own = {}, {}
        for name, par, methods in classes:
            parent[name] = par
            own[name] = {m: virt for m, virt in methods}

        def nearest(cls):
            while cls and method not in own[cls]:
                cls = parent[cls]
            return cls
        found = nearest(static_type)
        if not found:
            return "error"
        return nearest(dynamic_type) if own[found][method] else found
'''],
("Inheritance and overriding; virtual functions are explained in [C and C++ essentials](#/lesson/interview-prep/c-cpp-essentials).",
 "The compiler only knows the pointer's declared type, so that type decides *whether the call is legal* and *whether it is virtual*. Only for a virtual method does the program look at the real object at run time (through its vtable) to pick the most derived implementation.",
 ["Separate the two questions: what does the compiler see, and what does the running program see?",
  "Virtual-ness is inherited: once a base class declares `virtual speak`, every override is virtual even without the keyword.",
  "Write one helper `nearest(cls)` that climbs to the first class defining the method, and call it from the static type and, if virtual, from the dynamic type."],
 "Always dispatching on the dynamic type models Java or Python, not C++: it gets every non-virtual call wrong and accepts calls that would not compile.",
 "Build `parent` and `own` maps. `found = nearest(static_type)`. Climb from `found` to the root to see whether any declaration is virtual. Return `nearest(dynamic_type)` or `found`.\n\nDry run, `Animal*` → `Dog`, `eat`: found = Animal; no virtual declaration → Animal. `speak`: found = Animal, declared virtual → nearest from Dog = Dog. `fetch` through `Animal*`: Animal has no `fetch` → error, even though Dog defines it.",
 "O(depth of the hierarchy) per query after O(total methods) to build the maps.",
 "Looking only at the `virtual` flag of the nearest definition: `Dog::speak` is virtual because `Animal::speak` is, although Dog did not repeat the keyword (second wrong solution). Allowing a call the static type cannot see.",
 "Explain how a vtable implements rule 3 in O(1), why destructors of base classes should be virtual, and what name hiding does when a derived class declares a non-virtual method with the same name.")),

P("ordered-ledger", "Ordered Ledger", "Medium", "Java", "OrderedLedger",
"""
Java's `TreeMap` keeps its keys in sorted order and can answer "nearest key" questions. Build a small version.

Implement class `OrderedLedger` with integer keys and values:

- `put(key, value)` inserts or overwrites.
- `get(key)` returns the value, or `-1` if the key is absent.
- `remove(key)` deletes the key; returns `True` if it was present.
- `floorKey(x)` returns the largest key `<= x`, or `-1` if none.
- `ceilingKey(x)` returns the smallest key `>= x`, or `-1` if none.
- `firstKeys(n)` returns the `n` smallest keys in increasing order (all keys if fewer).

**Constraints:** keys and values are in `[0, 10^9]`; up to `2·10^4` calls.

**Example:** `put(30,1), put(10,2), put(20,3), floorKey(25) → 20, ceilingKey(25) → 30, remove(20) → True, floorKey(25) → 10, firstKeys(5) → [10, 30], get(20) → -1`
""",
'''class OrderedLedger:
    def __init__(self):
        self.keys = []
        self.values = {}

    def put(self, key: int, value: int) -> None:
        if key not in self.values:
            bisect.insort(self.keys, key)
        self.values[key] = value

    def get(self, key: int) -> int:
        return self.values.get(key, -1)

    def remove(self, key: int) -> bool:
        if key not in self.values:
            return False
        del self.values[key]
        self.keys.pop(bisect.bisect_left(self.keys, key))
        return True

    def floorKey(self, x: int) -> int:
        i = bisect.bisect_right(self.keys, x)
        return self.keys[i - 1] if i else -1

    def ceilingKey(self, x: int) -> int:
        i = bisect.bisect_left(self.keys, x)
        return self.keys[i] if i < len(self.keys) else -1

    def firstKeys(self, n: int) -> List[int]:
        return self.keys[:n]
''',
[[["OrderedLedger", "put", "put", "put", "floorKey", "ceilingKey", "remove", "floorKey", "firstKeys", "get"],
  [[], [30, 1], [10, 2], [20, 3], [25], [25], [20], [25], [5], [20]]],
 [["OrderedLedger", "get", "remove", "floorKey", "ceilingKey", "firstKeys"], [[], [1], [1], [1], [1], [3]]],
 [["OrderedLedger", "put", "put", "get", "firstKeys"], [[], [5, 1], [5, 2], [5], [9]]],
 [["OrderedLedger", "put", "floorKey", "floorKey", "ceilingKey", "ceilingKey", "floorKey"], [[], [10, 0], [10], [9], [10], [11], [11]]],
 [["OrderedLedger", "put", "put", "remove", "remove", "put", "firstKeys"], [[], [3, 3], [1, 1], [3], [3], [2, 2], [2]]],
 [["OrderedLedger", "put", "put", "put", "firstKeys", "firstKeys"], [[], [9, 0], [7, 0], [8, 0], [0], [2]]],
 _ops(("OrderedLedger", []), 4000, [("put", lambda: [R.randint(0, 200), R.randint(0, 9)]), ("remove", lambda: [R.randint(0, 200)]), ("get", lambda: [R.randint(0, 200)]),
                                    ("floorKey", lambda: [R.randint(0, 200)]), ("ceilingKey", lambda: [R.randint(0, 200)])]),
 _ops(("OrderedLedger", []), 4000, [("put", lambda: [R.randint(0, 10 ** 9), 1]), ("floorKey", lambda: [R.randint(0, 10 ** 9)]), ("ceilingKey", lambda: [R.randint(0, 10 ** 9)])]),
 _ops(("OrderedLedger", []), 2000, [("put", lambda: [R.randint(0, 30), R.randint(0, 9)]), ("remove", lambda: [R.randint(0, 30)]), ("firstKeys", lambda: [R.randint(0, 6)])]),
 _ops(("OrderedLedger", []), 2000, [("put", lambda: [R.randint(0, 50), R.randint(0, 9)]), ("put", lambda: [R.randint(0, 50), R.randint(0, 9)]), ("get", lambda: [R.randint(0, 50)]), ("remove", lambda: [R.randint(0, 50)])])],
['''class OrderedLedger:
    def __init__(self):
        self.keys = []
        self.values = {}

    def put(self, key, value):
        bisect.insort(self.keys, key)
        self.values[key] = value

    def get(self, key):
        return self.values.get(key, -1)

    def remove(self, key):
        if key not in self.values:
            return False
        del self.values[key]
        self.keys.pop(bisect.bisect_left(self.keys, key))
        return True

    def floorKey(self, x):
        i = bisect.bisect_right(self.keys, x)
        return self.keys[i - 1] if i else -1

    def ceilingKey(self, x):
        i = bisect.bisect_left(self.keys, x)
        return self.keys[i] if i < len(self.keys) else -1

    def firstKeys(self, n):
        return self.keys[:n]
''', '''class OrderedLedger:
    def __init__(self):
        self.keys = []
        self.values = {}

    def put(self, key, value):
        if key not in self.values:
            bisect.insort(self.keys, key)
        self.values[key] = value

    def get(self, key):
        return self.values.get(key, -1)

    def remove(self, key):
        if key not in self.values:
            return False
        del self.values[key]
        self.keys.pop(bisect.bisect_left(self.keys, key))
        return True

    def floorKey(self, x):
        i = bisect.bisect_left(self.keys, x)
        return self.keys[i - 1] if i else -1

    def ceilingKey(self, x):
        i = bisect.bisect_right(self.keys, x)
        return self.keys[i] if i < len(self.keys) else -1

    def firstKeys(self, n):
        return self.keys[:n]
'''],
("`bisect` and the difference between hash maps and sorted maps: see [Java collections](#/lesson/java/java-collections) and [Sorted maps](#/lesson/dsa-foundations/sorted-maps-skip-lists).",
 "A hash map finds an exact key instantly but knows nothing about neighbours. A sorted structure can answer \"nearest key below/above\". Keep both: a dictionary for values and a sorted list of keys searched with binary search.",
 ["Which operations need order, and which only need exact lookup?",
  "`bisect_right(keys, x)` is the number of keys `<= x`; the floor is the key just before that position.",
  "`bisect_left(keys, x)` is the position of the first key `>= x`: the ceiling."],
 "A plain dictionary with `max(k for k in d if k <= x)`: O(n) per floor or ceiling query.",
 "`put` inserts into the sorted list only when the key is new. `floorKey`: `i = bisect_right`; answer `keys[i-1]` if `i > 0`. `ceilingKey`: `i = bisect_left`; answer `keys[i]` if in range.\n\nDry run keys [10, 20, 30]: floorKey(25): bisect_right = 2 → 20. ceilingKey(25): bisect_left = 2 → 30. After removing 20: floorKey(25) → bisect_right = 1 → 10.",
 "Queries O(log n). Insert and delete O(n) because the list shifts; Java's `TreeMap` is a red-black tree with O(log n) for everything.",
 "Inserting an existing key into the list a second time (first wrong solution) leaves a ghost key after `remove`. Swapping `bisect_left` and `bisect_right` breaks the case where `x` itself is a key (second wrong solution).",
 "Name the Java equivalents: `HashMap`, `TreeMap` (`floorKey`, `ceilingKey`, `headMap`), `LinkedHashMap` (insertion order). Explain when each is the right choice. See [Hashing, trees and MapReduce](#/lesson/interview-prep/review-hashing-trees-mapreduce) for the balancing idea.")),

P("spend-report", "Customer Spend Report", "Medium", "Databases", "spendReport",
"""
Reproduce in code what this SQL query does:

```sql
SELECT c.name, COUNT(o.order_id) AS orders, COALESCE(SUM(o.amount), 0) AS total
FROM customers c LEFT JOIN orders o ON o.customer_id = c.id
GROUP BY c.id, c.name
ORDER BY total DESC, c.name ASC, c.id ASC;
```

`customers` is a list of `[id, name]` rows (ids are unique, names may repeat). `orders` is a list of `[order_id, customer_id, amount]` rows. Return a list of `[name, orders, total]` rows in the order the query specifies.

Because it is a **left** join, customers without orders appear with `0, 0`; orders that refer to an unknown customer are ignored.

**Constraints:** up to `5000` customers and `10^4` orders. Use a hash join: do not compare every customer with every order.

**Example:** `customers = [[1,"Ana"],[2,"Bo"],[3,"Cy"]]`, `orders = [[10,1,5],[11,3,20],[12,1,7],[13,9,99]]` → `[["Cy",1,20],["Ana",2,12],["Bo",0,0]]`
""",
'''class Solution:
    def spendReport(self, customers: List[List], orders: List[List[int]]) -> List[List]:
        stats = {cid: [0, 0] for cid, _ in customers}
        for _, cid, amount in orders:
            if cid in stats:
                stats[cid][0] += 1
                stats[cid][1] += amount
        rows = [(-stats[cid][1], name, cid, stats[cid][0]) for cid, name in customers]
        rows.sort()
        return [[name, count, -neg_total] for neg_total, name, cid, count in rows]
''',
[[[[1, "Ana"], [2, "Bo"], [3, "Cy"]], [[10, 1, 5], [11, 3, 20], [12, 1, 7], [13, 9, 99]]], [[], []], [[], [[1, 1, 5]]], [[[1, "Ana"]], []],
 [[[2, "Bo"], [1, "Bo"]], [[1, 2, 4], [2, 1, 4]]], [[[1, "Zed"], [2, "Amy"]], [[1, 1, 3], [2, 2, 3]]], [[[1, "A"], [2, "B"]], [[1, 1, 0]]],
 [[[5, "Eve"]], [[1, 5, 1], [2, 5, 2], [3, 5, 3]]], [[[1, "A"], [2, "B"], [3, "C"]], [[1, 2, 10], [2, 3, 10], [3, 3, 1]]],
 [[[i, R.choice(_names)] for i in range(2500)], [[j, R.randrange(2800), R.randint(1, 500)] for j in range(5000)]],
 [[[i, "same"] for i in range(1000)], [[j, R.randrange(1000), 5] for j in range(1500)]],
 [[[i, "n%d" % (i % 50)] for i in range(1500)], []]],
['''class Solution:
    def spendReport(self, customers, orders):
        names = dict((cid, name) for cid, name in customers)
        stats = {}
        for _, cid, amount in orders:
            if cid in names:
                s = stats.setdefault(cid, [0, 0])
                s[0] += 1
                s[1] += amount
        rows = sorted((-s[1], names[cid], cid, s[0]) for cid, s in stats.items())
        return [[name, count, -neg] for neg, name, cid, count in rows]
''', '''class Solution:
    def spendReport(self, customers, orders):
        stats = {name: [0, 0] for _, name in customers}
        names = dict(customers)
        for _, cid, amount in orders:
            if cid in names:
                stats[names[cid]][0] += 1
                stats[names[cid]][1] += amount
        rows = sorted((-s[1], name, s[0]) for name, s in stats.items())
        return [[name, count, -neg] for neg, name, count in rows]
'''],
("Joins and GROUP BY: see [Outer joins](#/lesson/sql/outer-joins) and [GROUP BY](#/lesson/sql/group-by).",
 "A hash join builds a dictionary on the join key of one table, then streams the other table past it. Grouping by customer and joining on customer use the same key, so one dictionary from customer id to [count, total] does both jobs.",
 ["Start the dictionary from the *customers* table so that customers without orders exist with zeros: that is what LEFT means.",
  "Scan the orders once; skip those whose customer id is not in the dictionary.",
  "Sort by a tuple that mirrors ORDER BY: (−total, name, id)."],
 "Nested loops: for each customer scan all orders. O(customers × orders), which is what a database does only when it has no index and no memory for a hash table.",
 "Initialise `stats[id] = [0, 0]` for every customer. Accumulate over orders. Build sortable tuples and sort.\n\nDry run example: stats 1 → [2, 12], 2 → [0, 0], 3 → [1, 20]; order 13 is dropped. Sorted by total descending: Cy 20, Ana 12, Bo 0.",
 "O(c + o) for the join and grouping, O(c log c) for the sort; O(c) memory.",
 "An inner join loses customers with no orders (first wrong solution). Grouping by name merges two different customers who share a name (second wrong solution): group by the key.",
 "Write the SQL for \"customers with no orders\" (LEFT JOIN … WHERE o.order_id IS NULL), and explain when the database would choose a hash join, a merge join or an index nested-loop join. See [Query performance](#/lesson/sql/performance).")),

P("lock-order-risk", "Lock-Order Risk", "Medium", "Threads & Locks", "canDeadlock",
"""
Each thread of a program acquires a fixed sequence of locks, **keeping every lock it already holds while it requests the next one**, and releases them all at the end. `plans[t]` is the list of distinct lock ids that thread `t` acquires, in order.

A deadlock becomes possible when the threads disagree about lock order in a circular way. Build the **lock-order graph**: an arrow `a → b` for every thread that requests `b` while holding `a`. Return `True` if this graph contains a cycle (the program is at risk), `False` otherwise.

**Constraints:** up to `2000` threads; total number of lock requests up to `2·10^4`; lock ids in `[0, 10^4]`.

**Example 1:** `plans = [[1, 2], [2, 1]]` → `True`

**Example 2:** `plans = [[1, 2, 3], [1, 3], [2, 3]]` → `False`
""",
'''class Solution:
    def canDeadlock(self, plans: List[List[int]]) -> bool:
        after = collections.defaultdict(set)
        nodes = set()
        for plan in plans:
            nodes.update(plan)
            for a, b in zip(plan, plan[1:]):
                after[a].add(b)
        indeg = {v: 0 for v in nodes}
        for a in after:
            for b in after[a]:
                indeg[b] += 1
        ready = [v for v in nodes if indeg[v] == 0]
        done = 0
        while ready:
            v = ready.pop()
            done += 1
            for w in after[v]:
                indeg[w] -= 1
                if indeg[w] == 0:
                    ready.append(w)
        return done != len(nodes)
''',
[[[[1, 2], [2, 1]]], [[[1, 2, 3], [1, 3], [2, 3]]], [[]], [[[5]]], [[[1, 2], [1, 2]]], [[[1, 2], [2, 3], [3, 1]]],
 [[[1, 2, 3], [3, 4], [4, 1]]], [[[1, 3], [3, 2], [2, 1]]], [[[1, 2], [3, 4], [5, 6]]], [[[1, 2, 3, 4], [4, 5], [5, 2]]],
 [[[i, i + 1] for i in range(5000)]], [[[i, i + 1] for i in range(5000)] + [[5000, 0]]],
 [[sorted(R.sample(range(300), 8)) for _ in range(1500)]], [[sorted(R.sample(range(300), 8)) for _ in range(1500)] + [[250, 249]]],
 [[[1, 2, 3], [3, 1]]]],
['''class Solution:
    def canDeadlock(self, plans):
        pairs = set()
        for plan in plans:
            for a, b in zip(plan, plan[1:]):
                pairs.add((a, b))
        return any((b, a) in pairs for a, b in pairs)
''', '''class Solution:
    def canDeadlock(self, plans):
        return len(plans) > 1 and len({tuple(p) for p in plans}) > 1
'''],
("Deadlock conditions and cycle detection: see [Threads and locks](#/lesson/interview-prep/threads-locks) and [Cycles and topological sort](#/lesson/neet-heap-graphs/cycles-toposort).",
 "A deadlock is a circle of threads each holding a lock the next one wants. That can only happen if lock orders form a cycle: someone takes 1 then 2, someone takes 2 then 3, someone takes 3 then 1. If all threads respect one global order, the graph has no cycle and no deadlock can occur.",
 ["Draw locks as dots and \"held before\" as arrows.",
  "Arrows between consecutive requests of a thread are enough: if a thread takes 1, 2, 3 the arrow 1 → 3 is implied by 1 → 2 → 3.",
  "Detect a cycle with Kahn's algorithm: if you cannot remove every node by repeatedly deleting nodes with no incoming arrow, a cycle exists."],
 "Simulate every interleaving of the threads: exponentially many schedules.",
 "Collect edges, compute in-degrees, repeatedly remove in-degree-0 locks. Return whether some lock was never removed.\n\nDry run `[[1,2,3],[3,1]]`: edges 1→2, 2→3, 3→1. Every lock has an incoming arrow, nothing can be removed → cycle → `True`.",
 "O(L) for L lock requests in total.",
 "Looking only for directly reversed pairs misses cycles of length three or more (first wrong solution). Different plans are not automatically dangerous (second wrong solution).",
 "State the fix: impose one global lock order (for example by lock id) and always acquire in that order. Discuss `tryLock` with back-off and why the dining philosophers deadlock. This is a conservative check: a cycle shows a deadlock is possible, not that it will happen on every run.")),

P("lost-update-replay", "Lost Update Replay", "Easy", "Threads & Locks", "finalCount",
"""
Several threads run the same unsynchronised code on a shared counter that starts at 0:

```
1. local = counter      (read)
2. local = local + 1    (compute)
3. counter = local      (write)
```

then go back to step 1 and repeat forever. You are given a **schedule**: a list of thread ids, where each entry lets that thread execute its next single step. Replay the schedule and return the final value of `counter`.

A thread that has not finished its three steps when the schedule ends stops where it is.

**Constraints:** up to `2·10^4` schedule entries; thread ids in `[0, 99]`.

**Example 1:** `[0, 0, 0, 1, 1, 1]` → `2` (no interference)

**Example 2:** `[0, 1, 0, 1, 0, 1]` → `1` (both threads read 0, both write 1)
""",
'''class Solution:
    def finalCount(self, schedule: List[int]) -> int:
        counter = 0
        step, local = {}, {}
        for t in schedule:
            s = step.get(t, 0)
            if s == 0:
                local[t] = counter
            elif s == 1:
                local[t] += 1
            else:
                counter = local[t]
            step[t] = (s + 1) % 3
        return counter
''',
[[[0, 0, 0, 1, 1, 1]], [[0, 1, 0, 1, 0, 1]], [[]], [[0]], [[0, 0]], [[0, 0, 0]], [[0, 0, 0, 0, 0, 0]], [[0, 1, 1, 1, 0, 0]],
 [[0, 1, 1, 1, 1, 1, 1, 0, 0]], [[0, 0, 1, 0, 1, 1, 2, 2, 2]], [[R.randrange(3) for _ in range(20000)]],
 [[R.randrange(50) for _ in range(20000)]], [[i // 3 % 4 for i in range(12000)]], [[1, 0, 0, 0, 1, 1, 0, 0, 0]]],
['''class Solution:
    def finalCount(self, schedule):
        return len(schedule) // 3
''', '''class Solution:
    def finalCount(self, schedule):
        counter = 0
        step = {}
        for t in schedule:
            s = step.get(t, 0)
            if s == 2:
                counter += 1
            step[t] = (s + 1) % 3
        return counter
'''],
("What a race condition is: see [Threads and locks](#/lesson/interview-prep/threads-locks) and [Races and mutual exclusion](#/lesson/os/races-mutual-exclusion).",
 "`counter += 1` is not one action but three. Each thread works on a private copy between its read and its write, so a write can overwrite an update that happened in between. Replaying a schedule only needs, per thread, which step comes next and the value of its private copy.",
 ["Keep two small dictionaries: next step per thread, and local value per thread.",
  "Step 0 copies the shared counter into the thread's local; step 2 copies the local back.",
  "Use `(step + 1) % 3` to cycle."],
 "There is nothing slower to compare with: the task is a direct simulation. The mistake to avoid is *not* simulating and assuming each completed cycle adds one.",
 "For each scheduled thread run its current step and advance it.\n\nDry run `[0,1,0,1,0,1]`: T0 reads 0; T1 reads 0; T0 computes 1; T1 computes 1; T0 writes 1; T1 writes 1. Final 1, although two increments completed: one update was lost.",
 "O(length of the schedule) time, O(threads) space.",
 "Counting completed cycles (both wrong solutions) ignores overwrites. The counter can even go *down*: in the ninth test thread 0 reads 0, thread 1 completes two increments, then thread 0 writes 1 over the 2.",
 "Compute the smallest and largest final values reachable when two threads each perform n increments (the minimum is surprisingly small). Then fix the code: a mutex around the three steps, or an atomic compare-and-swap loop.")),

P("bounded-buffer-replay", "Bounded Buffer Replay", "Medium", "Threads & Locks", "replay",
"""
Producer and consumer threads share a FIFO buffer that holds at most `capacity` items. Replay a deterministic list of events and report who received what.

Each event is `["put", thread, item]` or `["get", thread]`:

- **put**: if a consumer is blocked waiting, hand the item directly to the consumer that has waited longest. Otherwise, if the buffer has space, append the item. Otherwise the producer **blocks**, keeping its item, in a FIFO line of waiting producers.
- **get**: if the buffer is non-empty, the consumer takes the item at the front; then, if a producer is blocked, the longest-waiting producer's item is appended to the buffer and that producer is released. If the buffer is empty, the consumer **blocks** in a FIFO line of waiting consumers.

A blocked thread issues no further events until released. Return the list of deliveries `[consumer_thread, item]` in the order they happen.

**Constraints:** `1 <= capacity <= 100`; up to `2·10^4` events.

**Example (capacity 1):** `[["put","P1",7], ["put","P2",8], ["get","C1"], ["get","C2"], ["get","C3"], ["put","P1",9]]` → `[["C1",7], ["C2",8], ["C3",9]]`
""",
'''class Solution:
    def replay(self, capacity: int, events: List[List]) -> List[List]:
        buffer = collections.deque()
        blocked_producers = collections.deque()
        blocked_consumers = collections.deque()
        delivered = []
        for event in events:
            if event[0] == "put":
                item = event[2]
                if blocked_consumers:
                    delivered.append([blocked_consumers.popleft(), item])
                elif len(buffer) < capacity:
                    buffer.append(item)
                else:
                    blocked_producers.append(item)
            else:
                consumer = event[1]
                if buffer:
                    delivered.append([consumer, buffer.popleft()])
                    if blocked_producers:
                        buffer.append(blocked_producers.popleft())
                else:
                    blocked_consumers.append(consumer)
        return delivered
''',
[[1, [["put", "P1", 7], ["put", "P2", 8], ["get", "C1"], ["get", "C2"], ["get", "C3"], ["put", "P1", 9]]], [3, []],
 [2, [["get", "C1"], ["get", "C2"], ["put", "P1", 1], ["put", "P1", 2], ["put", "P1", 3]]], [1, [["put", "P1", 1], ["get", "C1"]]],
 [1, [["put", "A", 1], ["put", "B", 2], ["put", "C", 3], ["get", "X"], ["get", "Y"], ["get", "Z"], ["get", "W"]]],
 [2, [["put", "A", 1], ["put", "A", 2], ["put", "B", 3], ["get", "X"], ["get", "X"], ["get", "X"]]],
 [5, [["put", "A", i] for i in range(5)] + [["get", "X"] for _ in range(5)]],
 [1, [["get", "X"], ["put", "A", 4], ["put", "A", 5], ["put", "B", 6], ["get", "Y"], ["get", "Z"]]],
 [3, [(["put", "P%d" % (i % 7), i] if R.random() < 0.5 else ["get", "C%d" % (i % 5)]) for i in range(3500)]],
 [1, [(["put", "P%d" % (i % 7), i] if R.random() < 0.6 else ["get", "C%d" % (i % 5)]) for i in range(3500)]],
 [50, [(["put", "P%d" % (i % 3), i] if R.random() < 0.4 else ["get", "C%d" % (i % 9)]) for i in range(3500)]],
 [2, [["put", "A", 1], ["get", "X"], ["get", "Y"], ["put", "A", 2], ["put", "A", 3]]]],
['''class Solution:
    def replay(self, capacity, events):
        buffer = collections.deque()
        delivered = []
        for event in events:
            if event[0] == "put":
                if len(buffer) < capacity:
                    buffer.append(event[2])
            elif buffer:
                delivered.append([event[1], buffer.popleft()])
        return delivered
''', '''class Solution:
    def replay(self, capacity, events):
        buffer = collections.deque()
        blocked_producers = collections.deque()
        blocked_consumers = collections.deque()
        delivered = []
        for event in events:
            if event[0] == "put":
                item = event[2]
                if blocked_consumers:
                    delivered.append([blocked_consumers.popleft(), item])
                elif len(buffer) < capacity:
                    buffer.append(item)
                else:
                    blocked_producers.append(item)
            else:
                consumer = event[1]
                if buffer:
                    delivered.append([consumer, buffer.popleft()])
                else:
                    blocked_consumers.append(consumer)
        return delivered
'''],
("The producer-consumer problem and condition waiting: see [Threads and locks](#/lesson/interview-prep/threads-locks) and [Semaphores and monitors](#/lesson/os/semaphores-monitors-messages).",
 "There are three queues, not one: the buffer itself, producers waiting for space, and consumers waiting for data. Each event either completes immediately or parks its thread in the right waiting line; every completed action may wake exactly one thread from the opposite line.",
 ["When can consumers be waiting? Only when the buffer is empty. When can producers be waiting? Only when it is full.",
  "A `put` that finds a waiting consumer never touches the buffer.",
  "After a `get` frees a slot, move the first blocked producer's item into the buffer."],
 "Dropping items when the buffer is full and ignoring gets on an empty buffer (first wrong solution) is how a non-blocking queue behaves; a blocking buffer loses nothing.",
 "Keep three deques and apply the rules literally.\n\nDry run (capacity 1): put 7 → buffer [7]. put 8 → P2 blocks with 8. get C1 → delivers 7; P2's 8 enters the buffer. get C2 → delivers 8. get C3 → blocks. put 9 → handed straight to C3.",
 "O(1) per event, O(events) overall.",
 "Forgetting to wake a blocked producer after a `get` (second wrong solution): its item is then stuck forever, exactly the \"lost wake-up\" bug of real concurrent code.",
 "Implement the real thing with one mutex and two condition variables (`notFull`, `notEmpty`), using `while` rather than `if` around each wait. In Java: `ArrayBlockingQueue`. See [Java synchronization](#/lesson/java/java-synchronization).")),

P("cheapest-ferry-route", "Cheapest Ferry Route", "Medium", "Additional Review", "cheapest",
"""
An archipelago has `n` islands numbered `0 … n-1`. `ferries[i] = [u, v, price]` is a one-way ferry from `u` to `v` with a non-negative ticket price.

Return the lowest total price of a trip from island `src` to island `dst`, or `-1` if `dst` cannot be reached.

**Constraints:** `1 <= n <= 5000`; up to `2·10^4` ferries; prices in `[0, 10^6]`.

**Example:** `n = 4, ferries = [[0,1,4],[0,2,1],[2,1,2],[1,3,5]], src = 0, dst = 3` → `8` (0 → 2 → 1 → 3)
""",
'''class Solution:
    def cheapest(self, n: int, ferries: List[List[int]], src: int, dst: int) -> int:
        out = [[] for _ in range(n)]
        for u, v, price in ferries:
            out[u].append((v, price))
        best = [None] * n
        best[src] = 0
        heap = [(0, src)]
        while heap:
            cost, u = heapq.heappop(heap)
            if cost > best[u]:
                continue
            if u == dst:
                return cost
            for v, price in out[u]:
                new = cost + price
                if best[v] is None or new < best[v]:
                    best[v] = new
                    heapq.heappush(heap, (new, v))
        return -1
''',
[[4, [[0, 1, 4], [0, 2, 1], [2, 1, 2], [1, 3, 5]], 0, 3], [1, [], 0, 0], [2, [], 0, 1], [2, [[0, 1, 0]], 0, 1], [2, [[0, 1, 3]], 1, 0],
 [3, [[0, 1, 5], [0, 1, 2], [1, 2, 1]], 0, 2], [3, [[0, 1, 1], [1, 2, 1], [0, 2, 3]], 0, 2], [4, [[0, 1, 1], [1, 0, 1], [2, 3, 1]], 0, 3],
 [5, [[0, 1, 10], [0, 2, 3], [2, 1, 4], [1, 3, 2], [2, 3, 8], [3, 4, 0]], 0, 4],
 [3000, [[R.randrange(3000), R.randrange(3000), R.randint(0, 1000)] for _ in range(6000)], 0, 2999],
 [3000, [[i, i + 1, 10 ** 6] for i in range(2999)], 0, 2999], [3000, [[i, i + 1, 1] for i in range(2999)] + [[0, 2999, 2998]], 0, 2999],
 [4, [[0, 1, 1], [1, 2, 1], [2, 3, 1], [0, 3, 2]], 0, 3]],
['''class Solution:
    def cheapest(self, n, ferries, src, dst):
        out = [[] for _ in range(n)]
        for u, v, price in ferries:
            out[u].append((v, price))
        seen = {src: 0}
        queue = collections.deque([src])
        while queue:
            u = queue.popleft()
            for v, price in out[u]:
                if v not in seen:
                    seen[v] = seen[u] + price
                    queue.append(v)
        return seen.get(dst, -1)
'''],
("Heaps and Dijkstra's algorithm: see [Useful maths and graph algorithms](#/lesson/interview-prep/review-math-graphs) and [Shortest paths](#/lesson/neet-heap-graphs/shortest-paths).",
 "Always settle the cheapest island not yet settled. Because prices are never negative, no later detour can make that island cheaper, so its cost is final. A min-heap hands you the cheapest candidate in O(log n).",
 ["Breadth-first search counts ferries, not money. Why does it fail on the example?",
  "Keep `best[v]`, the cheapest known price to reach each island, and a heap of (price, island).",
  "When you pop an entry that is worse than `best` for that island, it is stale: skip it."],
 "Bellman-Ford: relax every ferry n − 1 times, O(n·m). Correct (even with negative prices) but far slower here.",
 "Pop the cheapest (cost, u). If u is the destination, return. Otherwise try each ferry out of u and push improvements.\n\nDry run example: pop (0, 0) → push (4, 1), (1, 2). Pop (1, 2) → island 1 improves to 3. Pop (3, 1) → island 3 at 8. Pop (4, 1) stale. Pop (8, 3) → 8.",
 "O((n + m) log n) time, O(n + m) space.",
 "Marking an island finished when it is first *seen* instead of when it is *popped* (the BFS wrong solution returns 9 for the example). Using Dijkstra with negative prices.",
 "Return the route itself by storing a predecessor for each island. Variants: [Network Delay Time](#/problem/network-delay-time), [Cheapest Flights Within K Stops](#/problem/cheapest-flights-within-k-stops).")),

P("probe-table", "Probe Table", "Medium", "Additional Review", "ProbeTable",
"""
Build a hash table that resolves collisions by **linear probing** in a fixed array of `capacity` slots. The home slot of an integer key is `key % capacity`; on a collision, try the next slot, wrapping around at the end.

Deleting must not break later searches, so a removed entry leaves a **tombstone** marker.

Implement class `ProbeTable(capacity)`:

- `get(key)`: start at the home slot and examine slots one by one. Stop with "absent" at a **never-used** slot, or after `capacity` slots. Tombstones are skipped. Return the value or `-1`.
- `put(key, value)`: if the key is present, overwrite its value. Otherwise store it in the **first tombstone seen** during the search, or, if none was seen, in the never-used slot where the search stopped. Return `True`, or `False` if there is no room.
- `remove(key)`: replace the entry by a tombstone; return whether the key was present.
- `probes(key)`: the number of slots a `get(key)` examines.

**Constraints:** `1 <= capacity <= 1000`; keys and values in `[0, 10^9]`.

**Example (capacity 5):** `put(1,10), put(6,60), put(11,110)` fill slots 1, 2, 3. `probes(11) → 3`. `remove(6) → True`. `get(11) → 110` (the tombstone in slot 2 is skipped). `put(16,160)` reuses slot 2. `probes(16) → 2`.
""",
'''class ProbeTable:
    EMPTY, TOMB = "empty", "tomb"

    def __init__(self, capacity: int):
        self.cap = capacity
        self.slots = [self.EMPTY] * capacity

    def _scan(self, key):
        """Return (index of key or -1, first reusable slot or -1, slots examined)."""
        i = key % self.cap
        reusable = -1
        for seen in range(1, self.cap + 1):
            slot = self.slots[i]
            if slot == self.EMPTY:
                return -1, (reusable if reusable >= 0 else i), seen
            if slot == self.TOMB:
                if reusable < 0:
                    reusable = i
            elif slot[0] == key:
                return i, reusable, seen
            i = (i + 1) % self.cap
        return -1, reusable, self.cap

    def get(self, key: int) -> int:
        i, _, _ = self._scan(key)
        return self.slots[i][1] if i >= 0 else -1

    def put(self, key: int, value: int) -> bool:
        i, reusable, _ = self._scan(key)
        if i >= 0:
            self.slots[i] = (key, value)
            return True
        if reusable < 0:
            return False
        self.slots[reusable] = (key, value)
        return True

    def remove(self, key: int) -> bool:
        i, _, _ = self._scan(key)
        if i < 0:
            return False
        self.slots[i] = self.TOMB
        return True

    def probes(self, key: int) -> int:
        return self._scan(key)[2]
''',
[[["ProbeTable", "put", "put", "put", "probes", "remove", "get", "put", "probes"], [[5], [1, 10], [6, 60], [11, 110], [11], [6], [11], [16, 160], [16]]],
 [["ProbeTable", "get", "remove", "probes"], [[3], [4], [4], [4]]],
 [["ProbeTable", "put", "put", "get", "probes"], [[1], [5, 1], [6, 2], [6], [6]]],
 [["ProbeTable", "put", "put", "put", "put", "get", "get", "probes"], [[3], [0, 1], [1, 2], [2, 3], [3, 4], [2], [3], [3]]],
 [["ProbeTable", "put", "put", "get", "put", "get"], [[4], [3, 1], [7, 2], [7], [7, 9], [7]]],
 [["ProbeTable", "put", "put", "remove", "put", "get", "get", "probes"], [[4], [0, 1], [4, 2], [0], [4, 3], [4], [0], [4]]],
 [["ProbeTable", "put", "remove", "put", "remove", "put", "remove", "probes", "put", "get"], [[3], [0, 1], [0], [1, 1], [1], [2, 1], [2], [0], [9, 5], [9]]],
 [["ProbeTable", "put", "put", "put", "remove", "remove", "put", "probes", "probes"], [[5], [4, 1], [9, 2], [14, 3], [4], [9], [19, 4], [14], [19]]],
 _ops(("ProbeTable", [7]), 3000, [("put", lambda: [R.randint(0, 30), R.randint(0, 9)]), ("remove", lambda: [R.randint(0, 30)]), ("get", lambda: [R.randint(0, 30)]), ("probes", lambda: [R.randint(0, 30)])]),
 _ops(("ProbeTable", [50]), 4000, [("put", lambda: [R.randint(0, 200), R.randint(0, 9)]), ("remove", lambda: [R.randint(0, 200)]), ("get", lambda: [R.randint(0, 200)]), ("probes", lambda: [R.randint(0, 200)])]),
 _ops(("ProbeTable", [1000]), 4000, [("put", lambda: [R.randint(0, 10 ** 9), 1]), ("put", lambda: [R.randint(0, 3000), 2]), ("probes", lambda: [R.randint(0, 3000)]), ("remove", lambda: [R.randint(0, 3000)])])],
['''class ProbeTable:
    def __init__(self, capacity):
        self.cap = capacity
        self.slots = [None] * capacity

    def _find(self, key):
        i = key % self.cap
        for seen in range(1, self.cap + 1):
            if self.slots[i] is None:
                return -1, i, seen
            if self.slots[i][0] == key:
                return i, -1, seen
            i = (i + 1) % self.cap
        return -1, -1, self.cap

    def get(self, key):
        i = self._find(key)[0]
        return self.slots[i][1] if i >= 0 else -1

    def put(self, key, value):
        i, free, _ = self._find(key)
        if i < 0 and free < 0:
            return False
        self.slots[i if i >= 0 else free] = (key, value)
        return True

    def remove(self, key):
        i = self._find(key)[0]
        if i < 0:
            return False
        self.slots[i] = None
        return True

    def probes(self, key):
        return self._find(key)[2]
'''],
("Hash functions and collisions: see [Hashing, trees and MapReduce](#/lesson/interview-prep/review-hashing-trees-mapreduce) and [Collision handling](#/lesson/dsa-foundations/collisions).",
 "With open addressing every key lives somewhere along a fixed walk that begins at its home slot. A search can stop at a never-used slot because an insertion would have used it. That reasoning breaks if deletions create fresh empty slots in the middle of a walk, hence the tombstone: \"something was here, keep walking\".",
 ["Three slot states are needed, not two.",
  "Write one scanning helper that returns where the key is, where a new key could go, and how many slots were examined; all four methods use it.",
  "During the scan remember the first tombstone: `put` should reuse it, but only after confirming the key is not further along the walk."],
 "Separate chaining (a list per slot) avoids tombstones altogether; mention it as the usual alternative, but the task asks for probing.",
 "`_scan` walks at most `capacity` slots. Empty → stop. Tombstone → remember the first, continue. Matching key → found.\n\nDry run (capacity 5): keys 1, 6, 11 all have home slot 1 and occupy 1, 2, 3. Removing 6 leaves a tombstone in slot 2, so searching 11 still passes through to slot 3. Inserting 16 scans 1, tomb at 2, 3, empty at 4: not present → reuse slot 2.",
 "Expected O(1) per operation while the table is sparsely filled; O(capacity) in the worst case. Tombstones accumulate, so real tables rebuild themselves periodically.",
 "Setting a removed slot back to empty cuts the walk and makes later keys unreachable (the wrong solution loses key 11 in the example). Inserting into the first tombstone *before* checking the rest of the walk creates duplicate keys.",
 "Compare with quadratic probing and double hashing (less clustering), and with chaining. What load factor triggers a resize, and why must every key be re-inserted when the capacity changes?")),

P("rolling-hash-find", "Find Every Occurrence", "Medium", "Additional Review", "findAll",
"""
Return the list of all positions (0-based, increasing) at which `pattern` occurs in `text`. Occurrences may overlap. An empty pattern has no occurrences.

Solve it with a **rolling hash** (the Rabin-Karp method) so that the expected running time is O(len(text) + len(pattern)), and confirm each hash match by comparing the actual characters.

**Constraints:** both strings have at most `2·10^4` lower-case letters.

**Example 1:** `text = "abababa", pattern = "aba"` → `[0, 2, 4]`

**Example 2:** `text = "hello", pattern = "xyz"` → `[]`
""",
'''class Solution:
    def findAll(self, text: str, pattern: str) -> List[int]:
        n, m = len(text), len(pattern)
        if m == 0 or m > n:
            return []
        BASE, MOD = 257, (1 << 61) - 1
        top = pow(BASE, m - 1, MOD)
        want = have = 0
        for i in range(m):
            want = (want * BASE + ord(pattern[i])) % MOD
            have = (have * BASE + ord(text[i])) % MOD
        hits = []
        for start in range(n - m + 1):
            if have == want and text[start:start + m] == pattern:
                hits.append(start)
            if start + m < n:
                have = ((have - ord(text[start]) * top) * BASE + ord(text[start + m])) % MOD
        return hits
''',
[["abababa", "aba"], ["hello", "xyz"], ["", "a"], ["a", ""], ["a", "a"], ["aaaa", "a"], ["aaaa", "aa"], ["abc", "abcd"], ["abcabc", "abc"],
 ["abcabc", "cab"], ["a" * 20000, "a" * 19990], ["ab" * 10000, "ba" * 500], [_rs(20000, "ab"), "abba"], [_rs(20000, "abc"), "cabbage"],
 ["mississippi", "issi"], ["xyzxyz", "z"]],
['''class Solution:
    def findAll(self, text, pattern):
        hits, i = [], text.find(pattern) if pattern else -1
        while i != -1:
            hits.append(i)
            i = text.find(pattern, i + len(pattern))
        return hits
''', '''class Solution:
    def findAll(self, text, pattern):
        m = len(pattern)
        if m == 0:
            return []
        return [i for i in range(len(text) - m + 1) if text[i] == pattern[0] and text[i + m - 1] == pattern[-1]]
'''],
("Polynomial hashing and modular arithmetic: see [Hashing, trees and MapReduce](#/lesson/interview-prep/review-hashing-trees-mapreduce) and [Pattern matching](#/lesson/dsa-foundations/pattern-matching).",
 "Comparing the pattern with every window costs O(n·m). Instead compare one number per window: a hash. The trick is that the hash of the next window can be computed from the current one in O(1) by removing the contribution of the character that leaves and adding the one that enters.",
 ["Treat a window as a number written in base 257: h = c₀·B^(m−1) + c₁·B^(m−2) + … + c_(m−1).",
  "Sliding right: subtract c₀·B^(m−1), multiply by B, add the new character, all modulo a large prime.",
  "Equal hashes do not prove equal strings: verify with a direct comparison before recording a hit."],
 "Check every start position with a slice comparison: O(n·m), which is 4·10⁸ character comparisons for the all-`a` test.",
 "Hash the pattern and the first window. For each start: on equal hashes, verify; then roll.\n\nDry run with digits instead of letters, text 31415, pattern 14, base 10: windows 31, 14, 41, 15. Roll 31 → (31 − 3·10)·10 + 4 = 14: equal to the pattern's hash, verified → position 1.",
 "Expected O(n + m); the verification makes the worst case O(n·m) only if there are many true matches or hash collisions.",
 "Skipping ahead by the pattern length misses overlapping matches (first wrong solution). Trusting a weak fingerprint without verification reports false matches (the second wrong solution looks only at the first and last character of each window). In languages without big integers, a negative value after the subtraction must be brought back into range.",
 "Rolling hashes also detect repeated substrings: LeetCode's *Repeated DNA Sequences*, LeetCode's *Longest Duplicate Substring*. Compare with KMP, which is worst-case linear without hashing.")),

P("avl-insert-all", "AVL Insertions", "Hard", "Additional Review", "avlBuild",
"""
Insert the given **distinct** keys, in the given order, into an initially empty **AVL tree**: a binary search tree that, after every insertion, restores the rule "the heights of the two subtrees of any node differ by at most one" by rotations.

Return the root of the final tree.

**Constraints:** up to `3000` keys.

**Example 1:** `[1, 2, 3]` → root 2 with children 1 and 3 (one left rotation)

**Example 2:** `[3, 1, 2]` → root 2 with children 1 and 3 (a double rotation)
""",
'''class Solution:
    def avlBuild(self, keys: List[int]) -> Optional[TreeNode]:
        def h(node):
            return node.height if node else 0

        def update(node):
            node.height = 1 + max(h(node.left), h(node.right))

        def rotate_right(y):
            x = y.left
            y.left, x.right = x.right, y
            update(y)
            update(x)
            return x

        def rotate_left(x):
            y = x.right
            x.right, y.left = y.left, x
            update(x)
            update(y)
            return y

        def insert(node, key):
            if node is None:
                fresh = TreeNode(key)
                fresh.height = 1
                return fresh
            if key < node.val:
                node.left = insert(node.left, key)
            else:
                node.right = insert(node.right, key)
            update(node)
            balance = h(node.left) - h(node.right)
            if balance > 1:
                if h(node.left.left) < h(node.left.right):
                    node.left = rotate_left(node.left)
                return rotate_right(node)
            if balance < -1:
                if h(node.right.right) < h(node.right.left):
                    node.right = rotate_right(node.right)
                return rotate_left(node)
            return node
        root = None
        for key in keys:
            root = insert(root, key)
        return root
''',
[[[1, 2, 3]], [[3, 1, 2]], [[]], [[5]], [[2, 1, 3]], [[3, 2, 1]], [[1, 3, 2]], [[1, 2, 3, 4, 5, 6, 7]], [[7, 6, 5, 4, 3, 2, 1]],
 [[10, 20, 30, 40, 50, 25]], [[50, 20, 60, 10, 30, 25]], [list(range(3000))], [R.sample(range(100000), 3000)], [list(range(2000, 0, -1))],
 [[5, 3, 8, 1, 4, 0]]],
['''class Solution:
    def avlBuild(self, keys):
        def insert(node, key):
            if node is None:
                return TreeNode(key)
            if key < node.val:
                node.left = insert(node.left, key)
            else:
                node.right = insert(node.right, key)
            return node
        root = None
        for key in keys[:900]:
            root = insert(root, key)
        return root
''', '''class Solution:
    def avlBuild(self, keys):
        def h(node):
            return node.height if node else 0

        def update(node):
            node.height = 1 + max(h(node.left), h(node.right))

        def rotate_right(y):
            x = y.left
            y.left, x.right = x.right, y
            update(y)
            update(x)
            return x

        def rotate_left(x):
            y = x.right
            x.right, y.left = y.left, x
            update(x)
            update(y)
            return y

        def insert(node, key):
            if node is None:
                fresh = TreeNode(key)
                fresh.height = 1
                return fresh
            if key < node.val:
                node.left = insert(node.left, key)
            else:
                node.right = insert(node.right, key)
            update(node)
            balance = h(node.left) - h(node.right)
            if balance > 1:
                return rotate_right(node)
            if balance < -1:
                return rotate_left(node)
            return node
        root = None
        for key in keys:
            root = insert(root, key)
        return root
'''],
("Rotations and balance factors: see [Hashing, trees and MapReduce](#/lesson/interview-prep/review-hashing-trees-mapreduce) and the full treatment in [AVL trees](#/lesson/dsa-foundations/avl).",
 "Insert as in an ordinary search tree, then walk back up the path. At the first node whose two sides differ in height by two, a rotation lifts the taller side. If the extra height is on the *inside* (left child's right side, or the mirror), a single rotation would only move the problem, so first rotate the child to bring the height to the outside.",
 ["Store a height in every node and recompute it from the children after each change.",
  "Balance = height(left) − height(right). Values +2 and −2 need repair.",
  "Four cases: left-left → rotate right; left-right → rotate left at the child, then right; right-right → rotate left; right-left → rotate right at the child, then left."],
 "Plain BST insertion with no balancing: sorted input produces a chain of height n, O(n²) total work, and deep recursion.",
 "Recursive `insert` returns the (possibly new) root of the subtree, so parents re-link automatically.\n\nDry run `[3, 1, 2]`: insert 3; insert 1 (left of 3); insert 2 (right of 1). At node 3 the balance is +2 and the left child leans right (left-right case): rotate left at 1 → 2 becomes 3's left child with 1 below; rotate right at 3 → root 2 with children 1 and 3.",
 "Each insertion is O(log n) because the height stays below about 1.44·log₂ n; building takes O(n log n).",
 "Using a single rotation in the inside cases (second wrong solution yields a different, still unbalanced shape for `[3, 1, 2]`). Updating heights in the wrong order after a rotation: the node that moved down must be updated first.",
 "Implement deletion (rebalancing may be needed at several ancestors). Compare with red-black trees, which rebalance less strictly and are what `TreeMap` and `std::map` use.")),

P("tic-tac-winner", "Noughts and Crosses Referee", "Easy", "Mixed Practice", "winner",
"""
A game is played on an `n × n` board given as a list of strings containing `"X"`, `"O"` and `"."` (empty). A player wins by filling an **entire row, column or one of the two main diagonals** with their mark.

Return `"X"` or `"O"` if that player has a winning line, or `""` if nobody has. (You may assume at most one player has a winning line.)

**Constraints:** `1 <= n <= 300`.

**Example 1:** `["XOX", "OXO", "OXX"]` → `"X"` (main diagonal)

**Example 2:** `["XO", "OX"]` → `"X"`; `["X.", ".O"]` → `""`
""",
'''class Solution:
    def winner(self, board: List[str]) -> str:
        n = len(board)
        lines = [[(r, c) for c in range(n)] for r in range(n)]
        lines += [[(r, c) for r in range(n)] for c in range(n)]
        lines.append([(i, i) for i in range(n)])
        lines.append([(i, n - 1 - i) for i in range(n)])
        for line in lines:
            first = board[line[0][0]][line[0][1]]
            if first != "." and all(board[r][c] == first for r, c in line):
                return first
        return ""
''',
[[["XOX", "OXO", "OXX"]], [["XO", "OX"]], [["X.", ".O"]], [["X"]], [["."]], [["OOO", "X.X", "..."]], [["X.O", "X.O", "..O"]],
 [["..O", ".OX", "OXX"]], [["...", "...", "..."]], [["XOX", "XOO", "OXX"]], [["X" * 300] * 150 + ["O" + "X" * 299] * 150],
 [["." * 300 for _ in range(300)]], [["".join("O" if c == 299 - r else "." for c in range(300)) for r in range(300)]],
 [["XX.", "OOO", "X.X"]], [["XXX.", "OOOO", "X.X.", "...."]]],
['''class Solution:
    def winner(self, board):
        for row in board:
            if row[0] != "." and len(set(row)) == 1:
                return row[0]
        for col in zip(*board):
            if col[0] != "." and len(set(col)) == 1:
                return col[0]
        return ""
''', '''class Solution:
    def winner(self, board):
        n = len(board)
        for r in range(n):
            if board[r][0] != "." and (board[r] == board[r][0] * n):
                return board[r][0]
        for c in range(n):
            if board[0][c] != "." and all(board[r][c] == board[0][c] for r in range(n)):
                return board[0][c]
        if board[0][0] != "." and all(board[i][i] == board[0][0] for i in range(n)):
            return board[0][0]
        return ""
'''],
("Grids and generating coordinate lists: see [Matrix tricks](#/lesson/neet-greedy-math/matrix-tricks).",
 "There are exactly 2n + 2 lines to examine. Describe each line as a list of coordinates and run one check over all of them; this removes the four near-identical loops in which bugs hide.",
 ["How many candidate lines does an n × n board have?",
  "Build the coordinates of each row, each column, and the two diagonals.",
  "A line wins if its first cell is not empty and every cell equals the first."],
 "Hard-code the eight lines of a 3 × 3 board: impossible to extend to n × n, and the interviewer will ask.",
 "Generate `lines`, loop, return the mark of the first uniform non-empty line.\n\nDry run `XOX / OXO / OXX`: rows and columns are mixed; main diagonal (0,0), (1,1), (2,2) = X, X, X → `X`.",
 "O(n²): each of the 2n + 2 lines has n cells. Memory O(n²) for the coordinate lists (O(1) if you loop directly).",
 "Forgetting one or both diagonals. Treating a line of empty cells as a win for `\".\"`. The anti-diagonal is `(i, n−1−i)`.",
 "Ask the interviewer: will this be called once or after every move? For repeated calls keep running counts per row, column and diagonal and answer in O(1) per move: see LeetCode's *Design Tic-Tac-Toe*.")),

P("smallest-gap-pair", "Closest Pair Across Two Lists", "Medium", "Mixed Practice", "smallestGap",
"""
Two teams each have a list of integer skill ratings. Choose one player from each team so that their ratings are as close as possible, and return that smallest absolute difference.

**Constraints:** each list has between 1 and `10^4` values in `[-10^9, 10^9]`.

**Example:** `a = [12, 3, 27, 40], b = [19, 51, 30, 8]` → `3` (27 and 30)
""",
'''class Solution:
    def smallestGap(self, a: List[int], b: List[int]) -> int:
        a, b = sorted(a), sorted(b)
        i = j = 0
        best = abs(a[0] - b[0])
        while i < len(a) and j < len(b):
            gap = a[i] - b[j]
            if abs(gap) < best:
                best = abs(gap)
            if gap == 0:
                return 0
            if gap < 0:
                i += 1
            else:
                j += 1
        return best
''',
[[[12, 3, 27, 40], [19, 51, 30, 8]], [[1], [1]], [[1], [100]], [[-5, 5], [0]], [[1, 2, 3], [10, 20, 30]], [[10, 20, 30], [1, 2, 3]],
 [[5, 5, 5], [5]], [[-10 ** 9], [10 ** 9]], [[1, 100, 1000], [50, 500, 5000]], [[R.randint(-10 ** 9, 10 ** 9) for _ in range(6000)], [R.randint(-10 ** 9, 10 ** 9) for _ in range(6000)]],
 [list(range(0, 10000, 2)), list(range(1, 10001, 4))], [[i * 1000 for i in range(4000)], [i * 1000 + 499 for i in range(4000)]], [[3, 8], [5, 6]], [[1, 2, 3, 4], [4, 9, 20, 30]]],
['''class Solution:
    def smallestGap(self, a, b):
        a, b = sorted(a), sorted(b)
        return min(abs(x - y) for x, y in zip(a, b))
''', '''class Solution:
    def smallestGap(self, a, b):
        return abs(min(a) - min(b))
'''],
("Sorting and the two-pointer walk over two sorted lists: see [Two pointers](#/lesson/neet-arrays/two-pointers-pattern).",
 "Sort both lists and walk them like a merge. If `a[i]` is smaller than `b[j]`, pairing `a[i]` with any later `b` only widens the gap, so `a[i]` is finished: advance `i`. Symmetrically otherwise. Every useful pair is examined.",
 ["The brute force compares all pairs. What does sorting buy you?",
  "With pointers at the two smallest values, which pointer can you safely advance?",
  "Advance the pointer at the smaller value; record the gap at every step."],
 "All pairs: O(|a|·|b|) = 10⁸ comparisons at the limits.",
 "Sort; `i = j = 0`; loop while both in range: update best; advance the smaller side.\n\nDry run sorted a = [3, 12, 27, 40], b = [8, 19, 30, 51]: 3 vs 8 → 5, advance a; 12 vs 8 → 4, advance b; 12 vs 19 → 7, a; 27 vs 19 → 8, b; 27 vs 30 → 3, a; 40 vs 30 → 10, b; 40 vs 51 → 11, a ends. Best 3.",
 "O(n log n + m log m) for sorting, then O(n + m).",
 "Pairing by position after sorting (`zip`) is wrong when the lists are offset: for `[1, 2, 3, 4]` and `[4, 9, 20, 30]` it reports 3 although both lists contain 4. Comparing only the two minima.",
 "If one list is tiny and the other huge, binary-search each element of the small list in the large one: O(small · log large). Related: [3Sum Closest](#/problem/3sum-closest).")),

P("busiest-year", "Busiest Year", "Medium", "Mixed Practice", "busiestYear",
"""
A club keeps, for every member, the first and last year of membership as `[joined, left]` (both inclusive). Return the year in which the club had the **most members**. If several years tie, return the earliest.

**Constraints:** `1 <= number of members <= 10^4`; years in `[1, 10^9]`, `joined <= left`. The year range is far too large to count year by year.

**Example:** `[[1990, 2001], [1995, 1999], [2000, 2010], [1999, 2000]]` → `1999` (three members: the first, second and fourth)
""",
'''class Solution:
    def busiestYear(self, spans: List[List[int]]) -> int:
        change = collections.defaultdict(int)
        for joined, left in spans:
            change[joined] += 1
            change[left + 1] -= 1
        best_year, best, current = 0, 0, 0
        for year in sorted(change):
            current += change[year]
            if current > best:
                best, best_year = current, year
        return best_year
''',
[[[[1990, 2001], [1995, 1999], [2000, 2010], [1999, 2000]]], [[[5, 5]]], [[[1, 10 ** 9]]], [[[1, 2], [3, 4]]], [[[3, 4], [1, 2]]],
 [[[1, 5], [5, 9]]], [[[1, 5], [6, 9]]], [[[10, 20], [10, 20], [1, 9]]], [[[1, 3], [2, 4], [3, 5], [6, 8], [7, 9], [8, 10]]],
 [[[R.randint(1, 10 ** 9 // 2), 10 ** 9 // 2 + R.randint(0, 10 ** 9 // 2)] for _ in range(5000)]],
 [[sorted([R.randint(1, 3000), R.randint(1, 3000)]) for _ in range(6000)]], [[[i, i] for i in range(1, 5000)]],
 [[[2, 2], [1, 1]]]],
['''class Solution:
    def busiestYear(self, spans):
        change = collections.defaultdict(int)
        for joined, left in spans:
            change[joined] += 1
            change[left] -= 1
        best_year, best, current = 0, 0, 0
        for year in sorted(change):
            current += change[year]
            if current > best:
                best, best_year = current, year
        return best_year
''', '''class Solution:
    def busiestYear(self, spans):
        starts = collections.Counter(j for j, _ in spans)
        return min(y for y, c in starts.items() if c == max(starts.values()))
'''],
("Difference arrays and sweep lines: see [Interval sweeps](#/lesson/neet-greedy-math/interval-sweep).",
 "The membership count only changes in years when someone joins or has just left. Record +1 at each joining year and −1 at the year *after* each leaving year, then sweep through those years in order keeping a running total.",
 ["Counting each year separately is impossible with years up to a billion. Where can the count change?",
  "A member who leaves in year L is still counted in L, so the −1 belongs to L + 1.",
  "Sort the event years, accumulate, and remember the first year with a strictly greater total."],
 "For each candidate year (every start year), count the spans containing it: O(n²).",
 "Dictionary `change`; sweep sorted keys. Using `>` keeps the earliest year on ties.\n\nDry run example: changes 1990 +1, 1995 +1, 1999 +1, 2000 +1 −1 (the second member's exit) = 0, 2001 −1 (fourth), 2002 −1, 2011 −1. Running: 1, 2, 3 at 1999, 3 at 2000 (not greater), … Answer 1999.",
 "O(n log n) for sorting at most 2n event years; O(n) space.",
 "Putting the −1 on the leaving year itself undercounts that year (first wrong solution fails `[[1,5],[5,9]]`, where year 5 has two members). The busiest year is not necessarily a year with the most joiners.",
 "Same sweep as [Meeting Rooms II](#/problem/meeting-rooms-ii) and LeetCode's *Maximum Population Year*. If the year range is small (say 1900–2100), a plain array of deltas beats sorting.")),

P("code-peg-score", "Code Peg Scoring", "Easy", "Mixed Practice", "score",
"""
In a code-breaking game the setter hides a row of coloured pegs, written as a string of colour initials such as `"CMYK"`. The breaker submits a guess of the same length. The setter answers with two numbers:

- **exact**: positions where the guess has the right colour in the right place;
- **misplaced**: guess pegs that have a colour present in the secret but in a different position. A peg of the secret can account for at most one peg of the guess, and exact matches are counted first.

Return `[exact, misplaced]`.

**Constraints:** equal lengths between 0 and `10^4`; upper-case letters.

**Example 1:** `secret = "CMYK", guess = "MMKC"` → `[1, 2]`

**Example 2:** `secret = "AABB", guess = "BBAA"` → `[0, 4]`
""",
'''class Solution:
    def score(self, secret: str, guess: str) -> List[int]:
        exact = 0
        left_secret, left_guess = collections.Counter(), collections.Counter()
        for s, g in zip(secret, guess):
            if s == g:
                exact += 1
            else:
                left_secret[s] += 1
                left_guess[g] += 1
        misplaced = sum(min(count, left_guess[colour]) for colour, count in left_secret.items())
        return [exact, misplaced]
''',
[["CMYK", "MMKC"], ["AABB", "BBAA"], ["", ""], ["A", "A"], ["A", "B"], ["RGBY", "RGBY"], ["RGBY", "YBGR"], ["AAAA", "AAAB"],
 ["ABCD", "AAAA"], ["AAAB", "BAAA"], ["RRGG", "RGRG"], [_rs(10000, "RGBYOP"), _rs(10000, "RGBYOP")], ["A" * 5000 + "B" * 5000, "B" * 5000 + "A" * 5000],
 ["ABAB", "BBBB"]],
['''class Solution:
    def score(self, secret, guess):
        exact = sum(s == g for s, g in zip(secret, guess))
        misplaced = sum(1 for g in guess if g in secret) - exact
        return [exact, misplaced]
''', '''class Solution:
    def score(self, secret, guess):
        exact = sum(s == g for s, g in zip(secret, guess))
        common = sum((collections.Counter(secret) & collections.Counter(guess)).values())
        return [exact, common]
'''],
("Counting with dictionaries: see [Hash maps and sets](#/lesson/neet-arrays/arrays-hashing-pattern).",
 "Handle the exact matches first and set those pegs aside. Among the remaining pegs, colour by colour, the number that can be paired up is the smaller of \"how many the secret still has\" and \"how many the guess still has\".",
 ["Why can a guess of `AAAA` against `ABCD` not score 1 exact and 3 misplaced?",
  "Count leftover colours of the secret and of the guess separately, skipping exact positions.",
  "misplaced = sum over colours of min(leftover in secret, leftover in guess)."],
 "For each non-exact guess peg, scan the secret for an unused peg of the same colour and mark it used: O(n²).",
 "One pass builds `exact` and the two counters; one pass over the colours sums the minima.\n\nDry run `CMYK` / `MMKC`: position 1 is exact (M). Leftover secret: C, Y, K. Leftover guess: M, K, C. Colour C: min(1, 1) = 1. Colour K: min(1, 1) = 1. Colour Y: 0. Total `[1, 2]`.",
 "O(n + number of colours) time, O(number of colours) space.",
 "Counting every guess peg whose colour occurs anywhere in the secret (first wrong solution gives 3 misplaced for `ABCD` / `AAAA`). Forgetting to subtract the exact matches from the common total (second wrong solution).",
 "Identical in spirit to LeetCode's *Bulls and Cows*. Design question: how would you write a solver that guesses the code in few attempts?")),

P("pattern-ab-match", "Two-Symbol Pattern Match", "Medium", "Mixed Practice", "fits",
"""
A pattern is a non-empty string made of the letters `a` and `b`, for example `"abbab"`. A text **fits** the pattern if you can choose a non-empty string for `a` and a non-empty string for `b` such that replacing every letter of the pattern by its string produces exactly the text. The two strings are allowed to be equal.

Return `True` if `text` fits `pattern`.

**Constraints:** `1 <= len(pattern) <= 1000`; `0 <= len(text) <= 1000`; text is lower-case letters.

**Example 1:** `pattern = "abbab", text = "drumbassbassdrumbass"` → `True` (`a = "drum"`, `b = "bass"`)

**Example 2:** `pattern = "ab", text = "x"` → `False`
""",
'''class Solution:
    def fits(self, pattern: str, text: str) -> bool:
        n = len(text)
        count_a, count_b = pattern.count("a"), pattern.count("b")
        first, other = ("a", "b") if pattern[0] == "a" else ("b", "a")
        c1 = count_a if first == "a" else count_b
        c2 = len(pattern) - c1
        for len1 in range(1, n // c1 + 1):
            rest = n - c1 * len1
            if c2 == 0:
                if rest != 0:
                    continue
                len2 = 0
            else:
                if rest <= 0 or rest % c2:
                    continue
                len2 = rest // c2
            word1 = text[:len1]
            word2 = None
            pos, ok = 0, True
            for ch in pattern:
                if ch == first:
                    if text[pos:pos + len1] != word1:
                        ok = False
                        break
                    pos += len1
                else:
                    piece = text[pos:pos + len2]
                    if word2 is None:
                        word2 = piece
                    elif piece != word2:
                        ok = False
                        break
                    pos += len2
            if ok:
                return True
        return False
''',
[["abbab", "drumbassbassdrumbass"], ["ab", "x"], ["a", "anything"], ["a", ""], ["aa", "xyxy"], ["aa", "xyx"], ["ab", "xy"], ["ab", "xx"],
 ["ba", "stopgo"], ["abba", "redbluebluered"], ["abba", "redbluebluegreen"], ["aaaa", "zzzz"], ["bbb", "xyzxyzxyz"],
 ["ab" * 100, "pq" * 100], ["ab" * 100, "pq" * 99 + "pr"], ["a" * 500 + "b" * 500, "x" * 1000], ["abab", "aaaaaaaaab" * 2], ["aab", "tiptiptop"],
 ["aba", "tiptoptip"], ["aba", "tiptoptap"], ["aabab", "xxyzxyz"]],
['''class Solution:
    def fits(self, pattern, text):
        return len(text) >= len(pattern) and len(text) % len(pattern) == 0
'''],
("String slicing and bounding a search by arithmetic: see [The seven steps](#/lesson/interview-prep/seven-step-method) for the \"look for bottlenecks\" habit used here.",
 "Once you fix the *length* of the string for the pattern's first letter, everything else is forced: the other length follows from the total length, the first string is the text's prefix, and the second string is read off at the first place the other letter appears. So try each possible first length and verify.",
 ["If `a` occurs twice and `b` three times and the text has 20 characters, then 2·|a| + 3·|b| = 20. How many choices of |a| are there?",
  "The first letter of the pattern determines its string: it is a prefix of the text.",
  "Verify by walking the pattern and comparing slices; no need to build a new string."],
 "Try every pair of substrings for `a` and `b`: O(n⁴) pairs before verification.",
 "Let `first` be the pattern's first letter with count c1, the other letter with count c2. For `len1` from 1 to n // c1: compute `len2 = (n − c1·len1) / c2` (must be a positive integer, or the remainder must be 0 when c2 = 0). Walk the pattern comparing slices.\n\nDry run example 1: c1 = 2 (a), c2 = 3 (b), n = 20. len1 = 1 → len2 = 6: a = `d`, b = `rumbas`, but the next six characters are `sbassd` ✗. len1 = 2 and 3 → len2 is not a whole number ✗. len1 = 4 → len2 = 4: a = `drum`; walk: drum, `bass` (recorded), bass, drum, bass ✓.",
 "At most n choices of `len1`, each verified in O(n): O(n²) worst case.",
 "Assuming the pattern starts with `a`. Allowing empty strings. Testing only that the text length is a multiple of the pattern length (first wrong solution).",
 "Require `a` and `b` to be different strings (one extra comparison). The general version with many letters needs backtracking: LeetCode's *Word Pattern II*.")),

P("blot-sizes", "Ink Blot Sizes", "Medium", "Mixed Practice", "blotSizes",
"""
A scanner turns a sheet of paper into a grid of brightness values. A value of `0` is a pixel completely covered by ink; any other value means paper is showing. A **blot** is a group of ink pixels in which each pixel touches another one of the group side by side, above or below, **or corner to corner**.

Return the sizes (pixel counts) of all blots on the sheet, sorted in increasing order.

**Constraints:** `1 <= rows, cols <= 150`.

**Example:** `[[3, 0, 0, 7], [0, 5, 2, 0], [9, 4, 0, 8], [0, 6, 1, 1]]` → `[1, 5]`
""",
'''class Solution:
    def blotSizes(self, page: List[List[int]]) -> List[int]:
        rows, cols = len(page), len(page[0])
        seen = [[False] * cols for _ in range(rows)]
        sizes = []
        for r in range(rows):
            for c in range(cols):
                if page[r][c] != 0 or seen[r][c]:
                    continue
                seen[r][c] = True
                stack, size = [(r, c)], 0
                while stack:
                    y, x = stack.pop()
                    size += 1
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < rows and 0 <= nx < cols and page[ny][nx] == 0 and not seen[ny][nx]:
                                seen[ny][nx] = True
                                stack.append((ny, nx))
                sizes.append(size)
        return sorted(sizes)
''',
[[[[3, 0, 0, 7], [0, 5, 2, 0], [9, 4, 0, 8], [0, 6, 1, 1]]], [[[0]]], [[[5]]], [[[0, 0], [0, 0]]], [[[0, 1], [1, 0]]], [[[0, 1, 0], [1, 1, 1], [0, 1, 0]]],
 [[[1, 2], [3, 4]]], [[[0, 1, 0, 1, 0]]], [[[0], [0], [1], [0]]], [_land], [[[0] * 150 for _ in range(150)]],
 [[[(r + c) % 2 for c in range(100)] for r in range(100)]], [[[1 if r % 2 else 0 for c in range(80)] for r in range(80)]],
 [[[0, 1, 1], [1, 1, 1], [1, 1, 0]]]],
['''class Solution:
    def blotSizes(self, page):
        rows, cols = len(page), len(page[0])
        seen = [[False] * cols for _ in range(rows)]
        sizes = []
        for r in range(rows):
            for c in range(cols):
                if page[r][c] != 0 or seen[r][c]:
                    continue
                seen[r][c] = True
                stack, size = [(r, c)], 0
                while stack:
                    y, x = stack.pop()
                    size += 1
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < rows and 0 <= nx < cols and page[ny][nx] == 0 and not seen[ny][nx]:
                            seen[ny][nx] = True
                            stack.append((ny, nx))
                sizes.append(size)
        return sorted(sizes)
'''],
("Flood fill on a grid: see [DFS and BFS](#/lesson/neet-heap-graphs/dfs-bfs).",
 "Each ink pixel is a node, and ink pixels that touch (eight directions) are joined. A blot is a connected component. Scan the grid; each time you find an unvisited ink pixel, flood outward from it, counting pixels and marking them so that none is counted twice.",
 ["Loop over all cells; start a search only at an ink pixel that has not been visited.",
  "Use an explicit stack: a sheet that is solid ink (150 × 150) would overflow recursion.",
  "Mark a pixel as seen when you push it, not when you pop it."],
 "For every ink pixel run a fresh search without a shared visited grid: each blot is measured once per pixel, O((rows·cols)²).",
 "Double loop; iterative DFS with the eight offsets (the offset (0, 0) is harmless because the cell is already marked).\n\nDry run example: (0,1) and (0,2) sit side by side. (1,0) touches (0,1) at a corner, (1,3) touches (0,2) at a corner, and (2,2) touches (1,3) at a corner: one blot of 5. (3,0) touches no other ink: 1. Sorted `[1, 5]`.",
 "O(rows × cols) time and space: each cell is pushed at most once.",
 "Using only four directions splits blots joined at corners (wrong solution returns five blots for the example). Marking on pop pushes the same cell many times.",
 "Four-direction variants: [Number of Islands](#/problem/number-of-islands), [Max Area of Island](#/problem/max-area-of-island). To avoid the visited grid, temporarily overwrite visited ink with −1 if modifying the input is allowed.")),

P("equal-letters-digits", "Longest Balanced Stretch", "Medium", "Mixed Practice", "longestBalanced",
"""
A string contains only letters and digits. Return the **longest contiguous substring that has exactly as many letters as digits**. If several have the maximum length, return the leftmost; if none exists, return the empty string.

**Constraints:** `0 <= len(s) <= 3·10^4`.

**Example 1:** `"a1bcd23e"` → `"1bcd23"` (three letters and three digits; no longer stretch is balanced)

**Example 2:** `"abc"` → `""`
""",
'''class Solution:
    def longestBalanced(self, s: str) -> str:
        first = {0: -1}
        balance = 0
        best_len, best_start = 0, 0
        for i, ch in enumerate(s):
            balance += 1 if ch.isdigit() else -1
            if balance in first:
                length = i - first[balance]
                if length > best_len:
                    best_len, best_start = length, first[balance] + 1
            else:
                first[balance] = i
        return s[best_start:best_start + best_len]
''',
[["a1bcd23e"], ["abc"], [""], ["a"], ["7"], ["a1"], ["1a"], ["aa11"], ["a1a1a"], ["11a"], ["aaa111aaa"], ["1a2b3c"],
 [_rs(30000, "ab12")], ["a" * 10000 + "1" * 10000], ["a" * 10000 + "1" * 4000 + "b" * 5], [_rs(20000, "abcde1")], ["ab12cd"]],
['''class Solution:
    def longestBalanced(self, s):
        digits = sum(ch.isdigit() for ch in s)
        letters = len(s) - digits
        return s[:2 * min(digits, letters)]
''', '''class Solution:
    def longestBalanced(self, s):
        first = {0: -1}
        balance = 0
        best_len, best_start = 0, 0
        for i, ch in enumerate(s):
            balance += 1 if ch.isdigit() else -1
            if balance in first:
                length = i - first[balance]
                if length >= best_len:
                    best_len, best_start = length, first[balance] + 1
            else:
                first[balance] = i
        return s[best_start:best_start + best_len]
'''],
("Prefix sums with a hash map of first occurrences: see [Prefix sums and counting](#/lesson/neet-arrays/prefix-counting).",
 "Score each digit +1 and each letter −1. A substring is balanced exactly when its scores add to 0, which means the running total is the same just before it starts and where it ends. So for each running total you want the earliest position where it occurred.",
 ["Replace the characters by +1 and −1 and write the running totals under the string.",
  "Two positions with equal running totals enclose a balanced stretch.",
  "Store only the *first* index of each total; the total 0 occurs \"before the string\" at index −1."],
 "Check every substring by counting: O(n³), or O(n²) with running counts.",
 "Scan once. If the current total was seen before at index p, the stretch p+1 … i is balanced; keep it if strictly longer. Otherwise record the total.\n\nDry run `a1bcd23e`: totals −1, 0, −1, −2, −3, −2, −1, −2. Total 0 at index 1 → length 2. Total −1 at index 2 → length 2; at index 6 → length 6 (indexes 1…6 = `1bcd23`). Best 6.",
 "O(n) time, O(n) space.",
 "Overwriting the stored index with later occurrences shortens the answer. Using `>=` returns the rightmost of several longest stretches (second wrong solution). Forgetting the initial entry `{0: −1}` misses stretches that start at index 0.",
 "The 0/1 version is LeetCode's *Contiguous Array*. Generalise to \"twice as many letters as digits\" by scoring digits +2 and letters −1."),
),

P("count-digit-occurrences", "Counting a Digit", "Hard", "Mixed Practice", "countDigit",
"""
Write down every integer from `0` to `n` inclusive. How many times does the digit `d` appear in total? For instance from 0 to 35 the digit 3 appears in 3, 13, 23, 30, 31, 32, 33 (twice), 34, 35: ten times.

**Constraints:** `0 <= n <= 10^18`; `1 <= d <= 9`.

**Example 1:** `n = 35, d = 3` → `10`

**Example 2:** `n = 9, d = 9` → `1`
""",
'''class Solution:
    def countDigit(self, n: int, d: int) -> int:
        total, power = 0, 1
        while power <= n:
            higher = n // (power * 10)
            current = n // power % 10
            lower = n % power
            total += higher * power
            if current > d:
                total += power
            elif current == d:
                total += lower + 1
            power *= 10
        return total
''',
[[35, 3], [9, 9], [0, 1], [1, 1], [10, 1], [11, 1], [99, 9], [100, 1], [222, 2], [1999, 1], [10 ** 18, 1], [10 ** 18 - 1, 9],
 [123456789012345678, 7], [61523, 6], [3141, 4], [8, 9]],
['''class Solution:
    def countDigit(self, n, d):
        total, power = 0, 1
        while power <= n:
            higher = n // (power * 10)
            current = n // power % 10
            total += higher * power
            if current >= d:
                total += power
            power *= 10
        return total
''', '''class Solution:
    def countDigit(self, n, d):
        return sum(str(i).count(str(d)) for i in range(min(n, 3000) + 1))
'''],
("Place value; counting by position instead of by number: see [Number theory](#/lesson/neet-greedy-math/number-theory).",
 "Do not count per number; count per **position**. Ask: in how many of the numbers 0…n is the tens digit equal to d? The digits above that position cycle through complete blocks, each contributing a fixed amount, and the current digit of n decides how much of the final partial block counts.",
 ["Brute force for small n and look at one position at a time.",
  "For the position with weight `power`, split n into `higher`, `current`, `lower`.",
  "Complete blocks give `higher × power`. Then: current > d adds a full `power`; current == d adds `lower + 1`; current < d adds nothing."],
 "Loop from 0 to n and count digits in each number: O(n log n), impossible for 10¹⁸.",
 "Loop `power` = 1, 10, 100, … while `power <= n`.\n\nDry run n = 35, d = 3. Units: higher 3, current 5 > 3 → 3·1 + 1 = 4 (3, 13, 23, 33). Tens: higher 0, current 3 == d → lower + 1 = 6 (30…35). Total 10.",
 "O(log₁₀ n) iterations: at most 19.",
 "Treating `current == d` like `current > d` counts numbers beyond n (first wrong solution gives 14 for the example). The digit 0 needs separate treatment because of leading zeros, which is why the statement restricts d to 1…9.",
 "Handle d = 0, or count within a range [lo, hi] as count(hi) − count(lo − 1). See LeetCode's *Number of Digit One*.")),

P("name-frequency-merge", "Merging Spelling Variants", "Hard", "Mixed Practice", "mergeCounts",
"""
A food-court survey asked visitors to write down their favourite dish. `counts` is a list of `[spelling, votes]` pairs, one per distinct spelling that was written. People spell dishes in different ways, so a second list, `aliases`, holds pairs of spellings that mean **the same dish**. Sameness carries over: if A and B are the same dish and B and C are the same dish, then A, B and C form one group, even when B itself received no votes.

For each group that contains at least one counted spelling, output one row `[label, total]`, where `label` is the alphabetically smallest spelling in the group (among all its spellings, counted or not) and `total` is the group's combined votes. Return the rows sorted by label.

**Constraints:** up to `10^4` spellings and `10^4` alias pairs.

**Example:** `counts = [["prata", 5], ["roti prata", 12], ["laksa", 4], ["satay", 7]]`, `aliases = [["prata", "roti paratha"], ["roti prata", "roti paratha"], ["laksa", "curry laksa"]]` → `[["curry laksa", 4], ["prata", 17], ["satay", 7]]`
""",
'''class Solution:
    def mergeCounts(self, counts: List[List], aliases: List[List[str]]) -> List[List]:
        parent = {}

        def find(x):
            parent.setdefault(x, x)
            root = x
            while parent[root] != root:
                root = parent[root]
            while parent[x] != root:
                parent[x], x = root, parent[x]
            return root
        for a, b in aliases:
            ra, rb = find(a), find(b)
            if ra != rb:
                if ra < rb:
                    parent[rb] = ra
                else:
                    parent[ra] = rb
        totals = collections.defaultdict(int)
        for name, number in counts:
            totals[find(name)] += number
        return [[label, totals[label]] for label in sorted(totals)]
''',
[[[["prata", 5], ["roti prata", 12], ["laksa", 4], ["satay", 7]], [["prata", "roti paratha"], ["roti prata", "roti paratha"], ["laksa", "curry laksa"]]], [[], []],
 [[], [["a", "b"]]], [[["a", 1]], []], [[["b", 2], ["a", 3]], [["a", "b"]]], [[["b", 2], ["c", 3]], [["c", "a"], ["a", "b"]]],
 [[["x", 1], ["y", 2], ["z", 3]], [["x", "y"], ["y", "z"], ["z", "x"]]], [[["m", 0]], [["m", "n"]]], [[["d", 1], ["e", 1]], [["a", "b"], ["b", "c"]]],
 [[[n, R.randint(1, 100)] for n in _names], [[R.choice(_names), R.choice(_names)] for _ in range(150)]],
 [[["k%05d" % i, 1] for i in range(5000)], [["k%05d" % i, "k%05d" % (i + 1)] for i in range(4999)]],
 [[["k%05d" % i, i] for i in range(0, 8000, 2)], [["k%05d" % i, "k%05d" % (i + 1)] for i in range(0, 8000, 4)]],
 [[["zed", 1]], [["zed", "amy"], ["bob", "amy"]]]],
['''class Solution:
    def mergeCounts(self, counts, aliases):
        totals = dict((n, c) for n, c in counts)
        for a, b in aliases:
            if a in totals and b in totals and a != b:
                lo, hi = min(a, b), max(a, b)
                totals[lo] += totals.pop(hi)
        return [[n, totals[n]] for n in sorted(totals)]
''', '''class Solution:
    def mergeCounts(self, counts, aliases):
        label = {}
        for a, b in aliases:
            best = min(label.get(a, a), label.get(b, b))
            label[a] = label[b] = best
        totals = collections.defaultdict(int)
        for name, number in counts:
            totals[label.get(name, name)] += number
        return [[n, totals[n]] for n in sorted(totals)]
'''],
("Union-find (disjoint sets): see [Union-find](#/lesson/neet-heap-graphs/union-find).",
 "\"Same dish\" is an equivalence relation, so the spellings fall into groups: connected components of a graph whose edges are the alias pairs. Union-find merges groups as pairs arrive; making the alphabetically smaller root the parent keeps the group's label at the root for free.",
 ["Two spellings can be linked through a third spelling that received no votes of its own.",
  "Give every spelling a parent pointer; `find` follows pointers to the representative.",
  "When uniting two groups, attach the alphabetically larger root under the smaller root, then sum votes by `find(spelling)`."],
 "Process alias pairs one at a time by adding one count to the other: breaks when a pair mentions a spelling that is not counted, or links two spellings already merged elsewhere (first wrong solution).",
 "Union all alias pairs. For each counted spelling add its votes to `totals[find(spelling)]`. Output sorted.\n\nDry run example: prata–roti paratha → the smaller string becomes the root, and `prata < roti paratha`, so the root is prata. roti prata–roti paratha → the roots are roti prata and prata; `prata` is smaller, so it stays the root of all three. laksa–curry laksa → root curry laksa. Totals: prata 5 + 12 = 17, curry laksa 4, satay 7.",
 "Nearly O(n + p) with path compression; the final sort is O(g log g) for g groups.",
 "Updating labels pair by pair without following chains (second wrong solution) leaves stale labels when groups merge later. Dropping uncounted spellings loses the bridge between two counted ones.",
 "A graph alternative: build adjacency lists and run DFS from each unvisited counted name. Related: LeetCode's *Accounts Merge*.")),

P("unspace-text", "Restoring Spaces", "Hard", "Mixed Practice", "fewestUnknown",
"""
All spaces were stripped from a message, leaving a single string of lower-case letters. You have a dictionary of known words. Insert spaces so that the pieces are dictionary words wherever possible; any character that does not end up inside a dictionary word is **unrecognised**.

Return the smallest possible number of unrecognised characters.

**Constraints:** `0 <= len(text) <= 2000`; up to `2000` dictionary words, each of length 1 to 20.

**Example:** `text = "icanxswimwell"`, `words = ["i", "can", "swim", "well", "wim"]` → `1` (`i can x swim well`)
""",
'''class Solution:
    def fewestUnknown(self, text: str, words: List[str]) -> int:
        known = set(words)
        longest = max((len(w) for w in known), default=0)
        n = len(text)
        best = [0] * (n + 1)
        for i in range(n - 1, -1, -1):
            best[i] = 1 + best[i + 1]
            for size in range(1, min(longest, n - i) + 1):
                if text[i:i + size] in known and best[i + size] < best[i]:
                    best[i] = best[i + size]
        return best[0]
''',
[["icanxswimwell", ["i", "can", "swim", "well", "wim"]], ["", ["a"]], ["abc", []], ["abc", ["abc"]], ["abc", ["ab", "bc"]],
 ["abcd", ["ab", "bcd"]], ["aaaa", ["aa"]], ["aaaaa", ["aa"]], ["catsanddog", ["cat", "cats", "and", "sand", "dog"]],
 ["xcatsanddogy", ["cat", "cats", "and", "sand", "dog"]], [_rs(2000, "abc"), _dict], [_rs(2000, "abcd"), _dict], ["ab" * 1000, ["aba", "bab", "b"]],
 ["thequickbrownfox", ["the", "quick", "brown", "fox", "he", "row"]], ["abcde", ["abc", "cde", "de"]]],
['''class Solution:
    def fewestUnknown(self, text, words):
        known = sorted(set(words), key=len, reverse=True)
        i, bad = 0, 0
        while i < len(text):
            for w in known:
                if text.startswith(w, i):
                    i += len(w)
                    break
            else:
                bad += 1
                i += 1
        return bad
'''],
("One-dimensional DP over string positions: see [DP on linear sequences](#/lesson/neet-dp/dp-linear).",
 "Let best(i) be the fewest unrecognised characters in the suffix starting at position i. At i there are two kinds of choice: give up on character i (cost 1 plus best(i+1)), or start a dictionary word here (cost best(i + length)). The answer is best(0).",
 ["Greedy longest-match fails: taking `abc` from `abcde` with words abc, cde, de leaves `de`… try `abcd` with words ab, bcd.",
  "Define the subproblem on suffixes and fill the table from the end.",
  "Only word lengths up to the longest dictionary word need to be tried at each position."],
 "Try every way of placing spaces: 2^(n−1) splits.",
 "`best[n] = 0`. For i from n−1 down: start with `1 + best[i+1]`; for each size up to the longest word, if the slice is known, take `best[i+size]` when smaller.\n\nDry run `abcd` with {ab, bcd}: best[4] = 0; best[3] = 1; best[2] = 2; best[1] = min(1 + 2, best[4] via `bcd`) = 0; best[0] = min(1 + 0, best[2] via `ab` = 2) = 1. Answer 1: `a` + `bcd`.",
 "O(n · L) set lookups with L = longest word length (each lookup hashes up to L characters); O(n) space.",
 "Greedy matching (wrong solution returns 2 for `abcd`). Trying all n − i lengths at each position makes it O(n²) slices of growing size.",
 "Return the restored sentence by remembering the choice made at each position. A trie avoids re-hashing slices. The yes/no version is [Word Break](#/problem/word-break).")),

P("longest-compound-word", "Longest Compound Word", "Hard", "Mixed Practice", "longestCompound",
"""
Given a list of distinct lower-case words, find the **longest word that can be written as a concatenation of two or more other words from the list** (a building word may be used several times). If several qualify with the same length, return the alphabetically smallest; if none qualifies return `""`.

**Constraints:** up to `2000` words, each of length 1 to 30.

**Example:** `["rain", "bow", "rainbow", "coat", "raincoat", "bowrain", "x"]` → `"raincoat"` (length 8; `rainbow` and `bowrain` have length 7)
""",
'''class Solution:
    def longestCompound(self, words: List[str]) -> str:
        known = set(words)

        def buildable(word):
            n = len(word)
            ok = [False] * (n + 1)
            ok[0] = True
            for end in range(1, n + 1):
                for start in range(end):
                    if ok[start] and (start > 0 or end < n) and word[start:end] in known:
                        ok[end] = True
                        break
            return ok[n]
        for word in sorted(words, key=lambda w: (-len(w), w)):
            if buildable(word):
                return word
        return ""
''',
[[["rain", "bow", "rainbow", "coat", "raincoat", "bowrain", "x"]], [[]], [["a"]], [["a", "aa"]], [["a", "b", "ab", "ba"]], [["cat", "dog"]],
 [["a", "aa", "aaa", "aaaa"]], [["ab", "abab", "ababab", "c"]], [["x", "xy", "xyz"]], [["ab", "cd", "abcd", "abcde", "e"]],
 [sorted({_rs(R.randint(1, 4), "ab") for _ in range(60)} | {_rs(R.randint(20, 30), "ab") for _ in range(900)})],
 [sorted({_rs(R.randint(2, 12), "abcdef") for _ in range(1900)})], [["a" * i for i in range(1, 31)]], [["zz", "z", "y", "yy"]],
 [["sun", "flower", "sunflowers", "sunflower", "s"]]],
['''class Solution:
    def longestCompound(self, words):
        known = set(words)
        best = ""
        for w in words:
            for i in range(1, len(w)):
                if w[:i] in known and w[i:] in known:
                    if len(w) > len(best) or (len(w) == len(best) and w < best):
                        best = w
        return best
''', '''class Solution:
    def longestCompound(self, words):
        known = set(words)

        def buildable(word):
            n = len(word)
            ok = [False] * (n + 1)
            ok[0] = True
            for end in range(1, n + 1):
                for start in range(end):
                    if ok[start] and word[start:end] in known:
                        ok[end] = True
                        break
            return ok[n]
        for word in sorted(words, key=lambda w: (-len(w), w)):
            if buildable(word):
                return word
        return ""
'''],
("The word-break DP from [Restoring Spaces](#/problem/ctci-unspace-text) and hash sets.",
 "Checking one word is the classic \"can this string be segmented into dictionary words?\" problem, with one twist: the word must not use *itself* as its only piece. Sort candidates from longest to shortest and return the first that passes.",
 ["How do you decide whether a single word can be split into dictionary words? Positions reachable from the start.",
  "The whole word is in the dictionary, so forbid the split that covers positions 0…n in one piece.",
  "Try candidates in the order (longest first, then alphabetical) and stop at the first success."],
 "Check only splits into exactly two pieces: misses words built from three or more pieces (first wrong solution).",
 "`ok[end]` = prefix of length `end` can be segmented. Transition: some `start` with `ok[start]` and `word[start:end]` known, excluding `start == 0 and end == n`.\n\nDry run `raincoat`: ok[4] via `rain`; ok[8] via `coat` from 4. Passes. It is the first candidate in the sorted order, so it is returned.",
 "O(W log W) to sort plus O(L²) set lookups per candidate of length L; the search usually stops early.",
 "Forgetting to exclude the word itself makes every word \"buildable\" (second wrong solution returns the longest word outright). Using only two-piece splits.",
 "Speed up with a trie and memoisation across words. Related: LeetCode's *Concatenated Words*, which asks for all such words.")),

P("max-block-sum", "Most Profitable Block", "Hard", "Mixed Practice", "bestBlock",
"""
A farm is divided into a grid of plots; each plot has a yearly profit that may be negative. Choose a **non-empty rectangular block** of plots (aligned with the grid) with the largest total profit and return that total.

**Constraints:** `1 <= rows, cols <= 60`; values in `[-10^4, 10^4]`.

**Example:** `[[1, -5, 2], [-3, 4, 6], [2, -1, -8]]` → `10` (the block of the second row's `4, 6`)
""",
'''class Solution:
    def bestBlock(self, grid: List[List[int]]) -> int:
        rows, cols = len(grid), len(grid[0])
        best = grid[0][0]
        for top in range(rows):
            column_sum = [0] * cols
            for bottom in range(top, rows):
                row = grid[bottom]
                run = 0
                for c in range(cols):
                    column_sum[c] += row[c]
                    run = column_sum[c] if run <= 0 else run + column_sum[c]
                    if run > best:
                        best = run
        return best
''',
[[[[1, -5, 2], [-3, 4, 6], [2, -1, -8]]], [[[7]]], [[[-7]]], [[[-1, -2], [-3, -4]]], [[[1, 2], [3, 4]]], [[[1, -2, 3]]], [[[1], [-2], [3]]],
 [[[2, -1, 2], [-1, -9, -1], [2, -1, 2]]], [[[0, 0], [0, 0]]], [[[5, -6, 5], [5, -6, 5]]], [_grid60], [[[-5] * 60 for _ in range(60)]],
 [[[R.randint(-10000, 10000) for _ in range(60)] for _ in range(40)]], [[[1, 1, -10, 1, 1], [1, 1, -10, 1, 1]]]],
['''class Solution:
    def bestBlock(self, grid):
        best = max(max(row) for row in grid)
        for row in grid:
            run = 0
            for v in row:
                run = max(0, run) + v
                best = max(best, run)
        return best
''', '''class Solution:
    def bestBlock(self, grid):
        rows, cols = len(grid), len(grid[0])
        best = 0
        for top in range(rows):
            column_sum = [0] * cols
            for bottom in range(top, rows):
                run = 0
                for c in range(cols):
                    column_sum[c] += grid[bottom][c]
                    run = max(0, run + column_sum[c])
                    best = max(best, run)
        return best
'''],
("Kadane's algorithm for the best contiguous run in one array: see [Linear DP](#/lesson/neet-dp/dp-linear) and [Maximum Subarray](#/problem/maximum-subarray).",
 "Fix the top and bottom rows of the block. Squash those rows into a single array by adding each column: now a block is a contiguous run of that array, and the best run is found in one pass. Extending the bottom row by one only adds one row to the column sums.",
 ["Solve the one-row case first: maximum-sum contiguous run.",
  "For a fixed pair of rows, what single array describes all blocks spanning exactly those rows?",
  "Loop `top`; reset column sums; for each `bottom` add that row into the sums and run Kadane."],
 "Enumerate all blocks by their four borders and sum each: O(rows³·cols³), or O(rows²·cols²) with a prefix-sum table.",
 "Three nested loops: top, bottom, column. `run` restarts at the current column sum when the previous run is not positive.\n\nDry run example with top = bottom = row 1: column sums [−3, 4, 6]; runs −3, 4, 10 → 10. With rows 0–1: [−2, −1, 8] → 8. With rows 1–2: [−1, 3, −2] → 3. Best 10.",
 "O(rows² · cols) time, O(cols) extra space; use the smaller dimension for the squared factor.",
 "Initialising the best to 0 is wrong when every plot is negative: the block must be non-empty (second wrong solution returns 0). Considering single rows only.",
 "Return the block's coordinates as well. The bounded variant is LeetCode's *Max Sum of Rectangle No Larger Than K*.")),
]

for _p in PROBLEMS:
    if _p["id"] == "ctci-avl-insert-all":
        _p["return_type"] = "tree"
