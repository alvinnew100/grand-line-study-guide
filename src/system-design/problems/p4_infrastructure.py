"""System design problems 4: caches, load balancing, shard routing, idempotency, leases, circuit breakers, back-pressure, seat holds."""


def _ops(cls, ctor_args, calls):
    return [[cls] + [c[0] for c in calls], [list(ctor_args)] + [list(c[1]) for c in calls]]


PROBLEMS = [
dict(
    id="sd-lru-ttl-cache",
    title="LRU Cache with TTL",
    difficulty="Medium",
    pattern="Caching",
    kind="class",
    entry="LRUCache",
    description=r"""
Build a cache with the two rules almost every real cache has: entries **expire** after a time to live, and when the cache is full the **least recently used** entry is evicted.

`LRUCache(capacity)`. Every operation receives the current time `now` (an integer that never decreases) and begins by removing **all** entries whose expiry time is `<= now`.

- `put(key, value, ttl, now)` → `None`. After the purge: if `key` is present, replace its value, set its expiry to `now + ttl` and mark it most recently used. Otherwise, if the cache holds `capacity` entries, evict the least recently used one, then insert the new entry with expiry `now + ttl` as most recently used. With `capacity == 0` nothing is ever stored.
- `get(key, now)` → the value, marking the entry most recently used (its expiry is unchanged), or `-1` if the key is absent or expired.
- `size(now)` → the number of live entries.

`ttl` is a positive integer.

**Example:** `LRUCache(2)`: `put("a",1,10,0)`, `put("b",2,10,1)`, `get("a",2)` → 1, `put("c",3,10,3)` evicts `"b"`, `get("b",4)` → -1, `get("a",10)` → -1 (expired at 10), `size(10)` → 1.
""",
    starter='''class LRUCache:
    def __init__(self, capacity: int):
        pass

    def put(self, key: str, value: int, ttl: int, now: int) -> None:
        pass

    def get(self, key: str, now: int) -> int:
        pass

    def size(self, now: int) -> int:
        pass
''',
    solution='''from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.data = OrderedDict()            # key -> (value, expires_at); oldest use first

    def _purge(self, now):
        for k in [k for k, (_, exp) in self.data.items() if exp <= now]:
            del self.data[k]

    def put(self, key, value, ttl, now):
        self._purge(now)
        if self.capacity <= 0:
            return
        if key in self.data:
            del self.data[key]
        elif len(self.data) >= self.capacity:
            self.data.popitem(last=False)
        self.data[key] = (value, now + ttl)

    def get(self, key, now):
        self._purge(now)
        if key not in self.data:
            return -1
        self.data.move_to_end(key)
        return self.data[key][0]

    def size(self, now):
        self._purge(now)
        return len(self.data)
''',
    tests=[
        _ops("LRUCache", [2], [("put", ["a", 1, 10, 0]), ("put", ["b", 2, 10, 1]), ("get", ["a", 2]), ("put", ["c", 3, 10, 3]), ("get", ["b", 4]), ("get", ["a", 10]), ("size", [10])]),
        _ops("LRUCache", [0], [("put", ["a", 1, 10, 0]), ("get", ["a", 0]), ("size", [0])]),
        _ops("LRUCache", [1], [("put", ["a", 1, 5, 0]), ("put", ["b", 2, 5, 1]), ("get", ["a", 1]), ("get", ["b", 1]), ("get", ["b", 6]), ("size", [6])]),
        _ops("LRUCache", [3], [("put", ["a", 1, 100, 0]), ("put", ["b", 2, 100, 0]), ("put", ["c", 3, 100, 0]), ("get", ["a", 1]), ("get", ["b", 1]), ("put", ["d", 4, 100, 2]), ("get", ["c", 3]), ("get", ["a", 3]), ("get", ["d", 3])]),
        _ops("LRUCache", [2], [("put", ["a", 1, 5, 0]), ("put", ["a", 9, 5, 3]), ("get", ["a", 6]), ("get", ["a", 8]), ("size", [8])]),
        _ops("LRUCache", [2], [("put", ["a", 1, 2, 0]), ("put", ["b", 2, 50, 0]), ("put", ["c", 3, 50, 2]), ("get", ["b", 3]), ("get", ["c", 3]), ("size", [3])]),
        _ops("LRUCache", [2], [("put", ["a", 1, 10, 0]), ("put", ["b", 2, 10, 0]), ("put", ["a", 5, 10, 1]), ("put", ["c", 3, 10, 2]), ("get", ["a", 3]), ("get", ["b", 3]), ("get", ["c", 3])]),
        _ops("LRUCache", [3], [("get", ["missing", 0]), ("size", [0]), ("put", ["x", 7, 1, 0]), ("size", [0]), ("size", [1])]),
        _ops("LRUCache", [3], [("put", [f"k{i}", i, 4, i]) for i in range(8)] + [("size", [8]), ("get", ["k5", 8]), ("get", ["k4", 8]), ("get", ["k7", 10]), ("size", [11])]),
        _ops("LRUCache", [2], [("put", ["a", 1, 10, 0]), ("get", ["a", 9]), ("put", ["b", 2, 10, 9]), ("put", ["c", 3, 10, 9]), ("get", ["a", 9]), ("get", ["b", 9])]),
        _ops("LRUCache", [4], [("put", [f"k{i % 6}", i, 3 + i % 4, i]) for i in range(20)] + [("get", [f"k{i}", 20]) for i in range(6)] + [("size", [22])]),
    ],
    examples=1,
    wrong_solutions=[
        '''from collections import OrderedDict
class LRUCache:
    def __init__(self, capacity):
        self.capacity, self.data = capacity, OrderedDict()
    def put(self, key, value, ttl, now):
        if self.capacity <= 0:
            return
        if key in self.data:
            del self.data[key]
        elif len(self.data) >= self.capacity:
            self.data.popitem(last=False)
        self.data[key] = (value, now + ttl)
    def get(self, key, now):
        if key not in self.data:
            return -1
        self.data.move_to_end(key)
        return self.data[key][0]
    def size(self, now):
        return len(self.data)
''',
        '''from collections import OrderedDict
class LRUCache:
    def __init__(self, capacity):
        self.capacity, self.data = capacity, OrderedDict()
    def _purge(self, now):
        for k in [k for k, (_, e) in self.data.items() if e <= now]:
            del self.data[k]
    def put(self, key, value, ttl, now):
        self._purge(now)
        if self.capacity <= 0:
            return
        if key in self.data:
            del self.data[key]
        elif len(self.data) >= self.capacity:
            self.data.popitem(last=False)
        self.data[key] = (value, now + ttl)
    def get(self, key, now):
        self._purge(now)
        return self.data[key][0] if key in self.data else -1
    def size(self, now):
        self._purge(now)
        return len(self.data)
''',
        '''from collections import OrderedDict
class LRUCache:
    def __init__(self, capacity):
        self.capacity, self.data = capacity, OrderedDict()
    def _purge(self, now):
        for k in [k for k, (_, e) in self.data.items() if e < now]:
            del self.data[k]
    def put(self, key, value, ttl, now):
        self._purge(now)
        if self.capacity <= 0:
            return
        if key in self.data:
            del self.data[key]
        elif len(self.data) >= self.capacity:
            self.data.popitem(last=False)
        self.data[key] = (value, now + ttl)
    def get(self, key, now):
        self._purge(now)
        if key not in self.data:
            return -1
        self.data.move_to_end(key)
        return self.data[key][0]
    def size(self, now):
        self._purge(now)
        return len(self.data)
''',
        '''from collections import OrderedDict
class LRUCache:
    def __init__(self, capacity):
        self.capacity, self.data = capacity, OrderedDict()
    def _purge(self, now):
        for k in [k for k, (_, e) in self.data.items() if e <= now]:
            del self.data[k]
    def put(self, key, value, ttl, now):
        self._purge(now)
        if self.capacity <= 0:
            return
        if key not in self.data and len(self.data) >= self.capacity:
            self.data.popitem(last=False)
        self.data[key] = (value, now + ttl)
    def get(self, key, now):
        self._purge(now)
        if key not in self.data:
            return -1
        self.data.move_to_end(key)
        return self.data[key][0]
    def size(self, now):
        self._purge(now)
        return len(self.data)
''',
    ],
    guide=dict(
        prereqs="Lesson 'The five building blocks' (cache, TTL, eviction, LRU) and 'Building blocks I'. `collections.OrderedDict`.",
        intuition="Two independent reasons remove an entry: it is too old (TTL), or the cache is full and it is the one nobody has touched for longest (LRU). Keep the entries ordered by last use, and store each entry's expiry time next to its value.",
        hints=[
            "An `OrderedDict` keeps insertion order; `move_to_end(key)` marks a key as most recently used and `popitem(last=False)` removes the least recently used.",
            "Start every operation by deleting the entries whose expiry is `<= now`.",
            "Updating an existing key must also make it the most recent: delete it and insert it again.",
        ],
        brute_force="A plain dictionary with a 'last used' timestamp per entry: eviction scans for the minimum, O(n) per put. The ordered dictionary makes eviction O(1). (The purge here is O(n); real caches use lazy expiry on read plus sampling, or a heap of expiry times.)",
        approach="""1. `_purge(now)`: delete entries with `expires <= now`.
2. `put`: purge; if the key exists remove it; else if full remove the first (least recent) entry; insert at the end.
3. `get`: purge; if present, `move_to_end` and return the value.

**Dry run**, capacity 2: put a (expires 10), put b (expires 11). `get(a, 2)` → order is now b, a. `put(c, 3)`: full, evict the first → b goes. `get(b, 4)` → -1. `get(a, 10)`: purge removes a (10 <= 10) → -1. `size(10)` → 1 (only c).""",
        complexity="`get` and `put` O(1) for the LRU part plus O(n) for this simple purge; space O(capacity).",
        pitfalls="Treating an entry as alive at exactly its expiry time; forgetting that `get` refreshes recency but not the TTL; not refreshing recency on an update; evicting when the key was already present; capacity 0.",
        follow_up="Replace the O(n) purge with lazy expiry: check the expiry only on access, and let eviction prefer expired entries.",
    ),
),
dict(
    id="sd-cache-aside-stampede",
    title="Cache-Aside with Stampede Protection",
    difficulty="Medium",
    pattern="Caching",
    kind="class",
    entry="CacheAside",
    description=r"""
When a popular cache entry expires, many requests miss at the same moment and all of them query the database: a **cache stampede**. The cure is to let only **one** request load the value while the others wait for it.

Simulate that. `CacheAside(ttl, load_time)`: loading a key from the database takes `load_time` time units; a loaded value stays fresh for `ttl` units after the load finishes.

- `get(key, now)` returns one of:
  - `"wait"` if a load for this key is in flight (`now < ready_at`): the request waits for it and does **not** start another;
  - `"hit"` if the key has a loaded value that is still fresh (`ready_at <= now < expires_at`);
  - `"load"` otherwise (no value, or the value has expired): this request starts a database load. Then `ready_at = now + load_time` and `expires_at = ready_at + ttl`.
- `invalidate(key, now)` → called when the underlying data changes. If the key's load has finished (`ready_at <= now`), remove the entry and return `True` if it was still fresh, `False` if it had already expired. If there is no entry, or a load is in flight, change nothing and return `False`.
- `db_loads()` → the number of database loads started so far.

`now` never decreases.

**Example:** `CacheAside(10, 2)`: `get("k",0)` → `"load"`, `get("k",1)` → `"wait"`, `get("k",2)` → `"hit"`, `get("k",11)` → `"hit"`, `get("k",12)` → `"load"`, `db_loads()` → 2.
""",
    starter='''class CacheAside:
    def __init__(self, ttl: int, load_time: int):
        pass

    def get(self, key: str, now: int) -> str:
        pass

    def invalidate(self, key: str, now: int) -> bool:
        pass

    def db_loads(self) -> int:
        pass
''',
    solution='''class CacheAside:
    def __init__(self, ttl, load_time):
        self.ttl, self.load_time = ttl, load_time
        self.entries = {}                 # key -> (ready_at, expires_at)
        self.loads = 0

    def get(self, key, now):
        e = self.entries.get(key)
        if e is not None:
            if now < e[0]:
                return "wait"
            if now < e[1]:
                return "hit"
        ready = now + self.load_time
        self.entries[key] = (ready, ready + self.ttl)
        self.loads += 1
        return "load"

    def invalidate(self, key, now):
        e = self.entries.get(key)
        if e is None or now < e[0]:
            return False
        del self.entries[key]
        return now < e[1]

    def db_loads(self):
        return self.loads
''',
    tests=[
        _ops("CacheAside", [10, 2], [("get", ["k", 0]), ("get", ["k", 1]), ("get", ["k", 2]), ("get", ["k", 11]), ("get", ["k", 12]), ("db_loads", [])]),
        _ops("CacheAside", [5, 3], [("get", ["k", 0])] * 10 + [("db_loads", [])]),
        _ops("CacheAside", [5, 3], [("get", ["k", t]) for t in range(0, 25)] + [("db_loads", [])]),
        _ops("CacheAside", [5, 0], [("get", ["k", 0]), ("get", ["k", 0]), ("get", ["k", 4]), ("get", ["k", 5]), ("get", ["k", 5]), ("db_loads", [])]),
        _ops("CacheAside", [10, 2], [("invalidate", ["k", 0]), ("get", ["k", 0]), ("invalidate", ["k", 1]), ("get", ["k", 1]), ("invalidate", ["k", 2]), ("get", ["k", 2]), ("get", ["k", 3]), ("get", ["k", 4]), ("db_loads", [])]),
        _ops("CacheAside", [10, 2], [("get", ["a", 0]), ("get", ["b", 0]), ("get", ["a", 1]), ("get", ["b", 5]), ("get", ["c", 5]), ("db_loads", [])]),
        _ops("CacheAside", [3, 1], [("get", ["k", 0]), ("get", ["k", 1]), ("invalidate", ["k", 4]), ("get", ["k", 4]), ("invalidate", ["k", 5]), ("invalidate", ["k", 5]), ("db_loads", [])]),
        _ops("CacheAside", [100, 5], [("get", ["hot", t // 10]) for t in range(0, 80)] + [("db_loads", [])]),
        _ops("CacheAside", [1, 1], [("get", ["k", t]) for t in range(0, 10)] + [("db_loads", [])]),
        _ops("CacheAside", [4, 2], [("get", ["k", 0]), ("get", ["k", 2]), ("invalidate", ["k", 3]), ("get", ["k", 3]), ("get", ["k", 4]), ("get", ["k", 5]), ("get", ["k", 8]), ("get", ["k", 9]), ("db_loads", [])]),
        _ops("CacheAside", [6, 2], [("get", [f"k{i % 3}", i]) for i in range(30)] + [("db_loads", [])]),
    ],
    examples=1,
    wrong_solutions=[
        '''class CacheAside:
    def __init__(self, ttl, load_time):
        self.ttl, self.lt, self.e, self.n = ttl, load_time, {}, 0
    def get(self, key, now):
        e = self.e.get(key)
        if e is not None and e[0] <= now < e[1]:
            return "hit"
        if e is not None and now < e[0]:
            self.n += 1
            return "load"
        r = now + self.lt
        self.e[key] = (r, r + self.ttl)
        self.n += 1
        return "load"
    def invalidate(self, key, now):
        e = self.e.get(key)
        if e is None or now < e[0]:
            return False
        del self.e[key]
        return now < e[1]
    def db_loads(self):
        return self.n
''',
        '''class CacheAside:
    def __init__(self, ttl, load_time):
        self.ttl, self.lt, self.e, self.n = ttl, load_time, {}, 0
    def get(self, key, now):
        e = self.e.get(key)
        if e is not None:
            if now < e[0]:
                return "wait"
            if now <= e[1]:
                return "hit"
        r = now + self.lt
        self.e[key] = (r, r + self.ttl)
        self.n += 1
        return "load"
    def invalidate(self, key, now):
        e = self.e.get(key)
        if e is None or now < e[0]:
            return False
        del self.e[key]
        return now < e[1]
    def db_loads(self):
        return self.n
''',
        '''class CacheAside:
    def __init__(self, ttl, load_time):
        self.ttl, self.lt, self.e, self.n = ttl, load_time, {}, 0
    def get(self, key, now):
        e = self.e.get(key)
        if e is not None:
            if now < e[0]:
                return "wait"
            if now < e[1]:
                return "hit"
        self.e[key] = (now + self.lt, now + self.ttl)
        self.n += 1
        return "load"
    def invalidate(self, key, now):
        e = self.e.get(key)
        if e is None or now < e[0]:
            return False
        del self.e[key]
        return now < e[1]
    def db_loads(self):
        return self.n
''',
        '''class CacheAside:
    def __init__(self, ttl, load_time):
        self.ttl, self.lt, self.e, self.n = ttl, load_time, {}, 0
    def get(self, key, now):
        e = self.e.get(key)
        if e is not None:
            if now < e[0]:
                return "wait"
            if now < e[1]:
                return "hit"
        r = now + self.lt
        self.e[key] = (r, r + self.ttl)
        self.n += 1
        return "load"
    def invalidate(self, key, now):
        e = self.e.pop(key, None)
        return e is not None and now < e[1]
    def db_loads(self):
        return self.n
''',
    ],
    guide=dict(
        prereqs="Lessons 'The five building blocks' (cache-aside) and 'Building blocks I' (cache stampede, single flight).",
        intuition="A stampede happens because every request that misses decides, independently, to rebuild the entry. Record 'someone is already loading this' the moment the first request starts, and make the others wait for that result.",
        hints=[
            "One pair of numbers per key is enough: when the value becomes ready, and when it expires.",
            "Check 'in flight' (`now < ready_at`) before checking 'fresh'.",
            "A new load sets `ready_at = now + load_time` and `expires_at = ready_at + ttl`: freshness is counted from when the load finishes.",
        ],
        brute_force="Plain cache-aside: every miss queries the database. With R requests arriving during a load of length L, that is R database queries instead of one, exactly when the database is least able to take it.",
        approach="""For each key keep `(ready_at, expires_at)`.

1. Entry exists and `now < ready_at` → `"wait"`.
2. Entry exists and `now < expires_at` → `"hit"`.
3. Otherwise start a load: store the new pair, count it, return `"load"`.

`invalidate` only removes an entry whose load has finished.

**Dry run**, ttl 10, load time 2: `get(k,0)` → load, ready at 2, expires at 12. `get(k,1)` → wait. `get(k,2)` → hit. `get(k,11)` → hit. `get(k,12)` → 12 is not < 12 → load again. Two loads in total, however many requests arrived at time 1.""",
        complexity="O(1) per operation; O(keys) space.",
        pitfalls="Starting a second load while one is in flight (the stampede itself); counting the TTL from the start of the load instead of from its completion; serving an entry at exactly its expiry time; letting `invalidate` cancel an in-flight load.",
        follow_up="Serve-stale-while-revalidate: return the old value as a hit while one request refreshes it. Also add jitter to TTLs so that many keys do not expire together.",
    ),
),
dict(
    id="sd-load-balancer",
    title="Load Balancer: Round Robin, Weighted and Least Connections",
    difficulty="Medium",
    pattern="Load Balancing",
    kind="class",
    entry="LoadBalancer",
    description=r"""
Implement three classic server-selection algorithms with health awareness.

`LoadBalancer(servers, weights)`: `servers` is a list of distinct names and `weights` the matching list of positive integers. All servers start healthy with 0 active connections.

- `set_health(server, healthy)` → `None`.
- `round_robin()` → keep a pointer that starts at index 0. Starting from the pointer and moving forward cyclically, return the first healthy server and move the pointer to the index after it. `None` if no server is healthy.
- `weighted()` → **smooth weighted round robin**. Each server has a running value `current`, initially 0. Considering only healthy servers: add each server's weight to its `current`; choose the server with the largest `current` (ties: the one earliest in the list); subtract the **sum of the healthy servers' weights** from the chosen server's `current`; return it. `None` if no server is healthy.
- `least_connections()` → the healthy server with the fewest active connections (ties: earliest in the list). Its connection count increases by 1. `None` if no server is healthy.
- `release(server)` → `None`. That server's connection count decreases by 1, never below 0.

**Example:** `LoadBalancer(["a","b","c"], [5,1,1])`: seven calls to `weighted()` return `a, a, b, a, c, a, a`.
""",
    starter='''class LoadBalancer:
    def __init__(self, servers: List[str], weights: List[int]):
        pass

    def set_health(self, server: str, healthy: bool) -> None:
        pass

    def round_robin(self):
        pass

    def weighted(self):
        pass

    def least_connections(self):
        pass

    def release(self, server: str) -> None:
        pass
''',
    solution='''class LoadBalancer:
    def __init__(self, servers, weights):
        self.servers = list(servers)
        self.weight = dict(zip(servers, weights))
        self.healthy = {s: True for s in servers}
        self.conns = {s: 0 for s in servers}
        self.current = {s: 0 for s in servers}
        self.pointer = 0

    def set_health(self, server, healthy):
        self.healthy[server] = healthy

    def round_robin(self):
        n = len(self.servers)
        for step in range(n):
            i = (self.pointer + step) % n
            if self.healthy[self.servers[i]]:
                self.pointer = (i + 1) % n
                return self.servers[i]
        return None

    def weighted(self):
        up = [s for s in self.servers if self.healthy[s]]
        if not up:
            return None
        total = 0
        for s in up:
            self.current[s] += self.weight[s]
            total += self.weight[s]
        best = up[0]
        for s in up:
            if self.current[s] > self.current[best]:
                best = s
        self.current[best] -= total
        return best

    def least_connections(self):
        up = [s for s in self.servers if self.healthy[s]]
        if not up:
            return None
        best = min(up, key=lambda s: self.conns[s])
        self.conns[best] += 1
        return best

    def release(self, server):
        self.conns[server] = max(0, self.conns[server] - 1)
''',
    tests=[
        _ops("LoadBalancer", [["a", "b", "c"], [5, 1, 1]], [("weighted", [])] * 7),
        _ops("LoadBalancer", [["a", "b", "c"], [1, 1, 1]], [("round_robin", [])] * 4 + [("set_health", ["b", False])] + [("round_robin", [])] * 4 + [("set_health", ["b", True])] + [("round_robin", [])] * 3),
        _ops("LoadBalancer", [["a", "b"], [1, 1]], [("set_health", ["a", False]), ("set_health", ["b", False]), ("round_robin", []), ("weighted", []), ("least_connections", [])]),
        _ops("LoadBalancer", [["a", "b", "c"], [1, 1, 1]], [("least_connections", [])] * 4 + [("release", ["b"]), ("least_connections", []), ("release", ["a"]), ("release", ["a"]), ("release", ["a"]), ("least_connections", []), ("least_connections", [])]),
        _ops("LoadBalancer", [["a", "b"], [3, 1]], [("weighted", [])] * 8),
        _ops("LoadBalancer", [["a", "b", "c"], [2, 3, 1]], [("weighted", [])] * 6 + [("set_health", ["b", False])] + [("weighted", [])] * 6),
        _ops("LoadBalancer", [["only"], [4]], [("round_robin", []), ("weighted", []), ("least_connections", []), ("least_connections", []), ("release", ["only"]), ("release", ["only"]), ("release", ["only"]), ("least_connections", [])]),
        _ops("LoadBalancer", [["a", "b", "c", "d"], [1, 1, 1, 1]], [("round_robin", []), ("set_health", ["b", False]), ("set_health", ["c", False]), ("round_robin", []), ("round_robin", []), ("round_robin", []), ("set_health", ["c", True]), ("round_robin", []), ("round_robin", [])]),
        _ops("LoadBalancer", [["a", "b", "c"], [1, 1, 1]], [("least_connections", []), ("least_connections", []), ("set_health", ["c", False]), ("least_connections", []), ("least_connections", []), ("set_health", ["c", True]), ("least_connections", []), ("least_connections", []), ("least_connections", [])]),
        _ops("LoadBalancer", [["x", "y", "z"], [4, 2, 1]], [("weighted", [])] * 14),
        _ops("LoadBalancer", [["a", "b"], [1, 1]], [("release", ["a"]), ("release", ["a"]), ("least_connections", []), ("least_connections", []), ("least_connections", []), ("least_connections", [])]),
        _ops("LoadBalancer", [["a", "b", "c"], [1, 2, 3]], [("round_robin", []), ("weighted", []), ("least_connections", []), ("round_robin", []), ("weighted", []), ("least_connections", []), ("round_robin", []), ("weighted", []), ("least_connections", [])]),
    ],
    examples=1,
    wrong_solutions=[
        '''class LoadBalancer:
    def __init__(self, servers, weights):
        self.s, self.w = list(servers), dict(zip(servers, weights))
        self.h = {x: True for x in servers}; self.c = {x: 0 for x in servers}
        self.p = 0; self.seq = [x for x in servers for _ in range(self.w[x])]; self.wp = 0
    def set_health(self, s, v):
        self.h[s] = v
    def round_robin(self):
        n = len(self.s)
        for k in range(n):
            i = (self.p + k) % n
            if self.h[self.s[i]]:
                self.p = (i + 1) % n
                return self.s[i]
        return None
    def weighted(self):
        for k in range(len(self.seq)):
            i = (self.wp + k) % len(self.seq)
            if self.h[self.seq[i]]:
                self.wp = (i + 1) % len(self.seq)
                return self.seq[i]
        return None
    def least_connections(self):
        up = [x for x in self.s if self.h[x]]
        if not up:
            return None
        b = min(up, key=lambda x: self.c[x]); self.c[b] += 1; return b
    def release(self, s):
        self.c[s] = max(0, self.c[s] - 1)
''',
        '''class LoadBalancer:
    def __init__(self, servers, weights):
        self.s, self.w = list(servers), dict(zip(servers, weights))
        self.h = {x: True for x in servers}; self.c = {x: 0 for x in servers}
        self.cur = {x: 0 for x in servers}; self.p = 0
    def set_health(self, s, v):
        self.h[s] = v
    def round_robin(self):
        n = len(self.s)
        for k in range(n):
            i = (self.p + k) % n
            if self.h[self.s[i]]:
                self.p = (self.p + 1) % n
                return self.s[i]
        return None
    def weighted(self):
        up = [x for x in self.s if self.h[x]]
        if not up:
            return None
        t = 0
        for x in up:
            self.cur[x] += self.w[x]; t += self.w[x]
        b = up[0]
        for x in up:
            if self.cur[x] > self.cur[b]:
                b = x
        self.cur[b] -= t
        return b
    def least_connections(self):
        up = [x for x in self.s if self.h[x]]
        if not up:
            return None
        b = min(up, key=lambda x: self.c[x]); self.c[b] += 1; return b
    def release(self, s):
        self.c[s] = max(0, self.c[s] - 1)
''',
        '''class LoadBalancer:
    def __init__(self, servers, weights):
        self.s, self.w = list(servers), dict(zip(servers, weights))
        self.h = {x: True for x in servers}; self.c = {x: 0 for x in servers}
        self.cur = {x: 0 for x in servers}; self.p = 0
    def set_health(self, s, v):
        self.h[s] = v
    def round_robin(self):
        n = len(self.s)
        for k in range(n):
            i = (self.p + k) % n
            if self.h[self.s[i]]:
                self.p = (i + 1) % n
                return self.s[i]
        return None
    def weighted(self):
        up = [x for x in self.s if self.h[x]]
        if not up:
            return None
        for x in up:
            self.cur[x] += self.w[x]
        b = up[0]
        for x in up:
            if self.cur[x] > self.cur[b]:
                b = x
        self.cur[b] -= sum(self.w.values())
        return b
    def least_connections(self):
        up = [x for x in self.s if self.h[x]]
        if not up:
            return None
        b = min(up, key=lambda x: self.c[x]); self.c[b] += 1; return b
    def release(self, s):
        self.c[s] = max(0, self.c[s] - 1)
''',
        '''class LoadBalancer:
    def __init__(self, servers, weights):
        self.s, self.w = list(servers), dict(zip(servers, weights))
        self.h = {x: True for x in servers}; self.c = {x: 0 for x in servers}
        self.cur = {x: 0 for x in servers}; self.p = 0
    def set_health(self, s, v):
        self.h[s] = v
    def round_robin(self):
        n = len(self.s)
        for k in range(n):
            i = (self.p + k) % n
            if self.h[self.s[i]]:
                self.p = (i + 1) % n
                return self.s[i]
        return None
    def weighted(self):
        up = [x for x in self.s if self.h[x]]
        if not up:
            return None
        t = 0
        for x in up:
            self.cur[x] += self.w[x]; t += self.w[x]
        b = up[0]
        for x in up:
            if self.cur[x] > self.cur[b]:
                b = x
        self.cur[b] -= t
        return b
    def least_connections(self):
        up = [x for x in self.s if self.h[x]]
        if not up:
            return None
        b = min(up, key=lambda x: self.c[x]); self.c[b] += 1; return b
    def release(self, s):
        self.c[s] -= 1
''',
    ],
    guide=dict(
        prereqs="Lessons 'The five building blocks' (load balancer, health checks) and 'Building blocks I' (balancing algorithms).",
        intuition="Round robin takes turns. Weighted round robin takes turns in proportion to capacity, and the 'smooth' version spreads a heavy server's turns out instead of giving them in a burst. Least connections looks at how busy each server is right now, which matters when requests take very different times.",
        hints=[
            "Round robin: scan at most n positions from the pointer; set the pointer to the position after the server you return, not the pointer plus one.",
            "Smooth weighted: add weights, pick the maximum, subtract the total of the healthy weights from the winner.",
            "`min` with a key returns the first minimum, which gives the 'earliest in the list' tie-break for free.",
        ],
        brute_force="Weighted round robin by repeating each server `weight` times in a list gives the right proportions but in bursts (`a a a a a b c`). The smooth variant produces `a a b a c a a` with the same proportions.",
        approach="""**Smooth weighted dry run**, weights a 5, b 1, c 1 (total 7), `current` starts 0, 0, 0:

| add weights | pick | after subtracting 7 |
|---|---|---|
| 5, 1, 1 | a | -2, 1, 1 |
| 3, 2, 2 | a | -4, 2, 2 |
| 1, 3, 3 | b | 1, -4, 3 |
| 6, -3, 4 | a | -1, -3, 4 |
| 4, -2, 5 | c | 4, -2, -2 |
| 9, -1, -1 | a | 2, -1, -1 |
| 7, 0, 0 | a | 0, 0, 0 |

Sequence: a a b a c a a, and the state is back to zero after 7 picks.""",
        complexity="Each selection is O(n) for n servers; O(n) space.",
        pitfalls="Advancing the round-robin pointer by one instead of to just past the chosen server (skips or repeats servers when some are unhealthy); subtracting the total of all weights instead of only healthy ones; letting connection counts go negative; counting connections in the other two algorithms.",
        follow_up="'Power of two choices': pick two random servers and send the request to the less loaded one. Why does it behave almost as well as least connections with far less shared state?",
    ),
),
dict(
    id="sd-shard-router",
    title="Shard Router with a Slot Directory and Rebalancing",
    difficulty="Medium",
    pattern="Partitioning",
    kind="class",
    entry="ShardRouter",
    description=r"""
Instead of computing a key's shard directly, many systems hash keys into a fixed number of **slots** and keep a **directory** from slot to shard. Rebalancing then means reassigning slots, and keys never change slot.

`ShardRouter(num_slots, shards)`: `shards` is a non-empty list of distinct names. Initially slot `i` belongs to `shards[i % len(shards)]`.

The slot of a key is `int(hashlib.md5(key.encode()).hexdigest(), 16) % num_slots`.

- `shard_for(key)` → the shard owning the key's slot.
- `slot_counts()` → a list of `[shard, number_of_slots]` in the order the shards were added.
- `add_shard(name)` → add a new, empty shard, then move slots to it one at a time until it owns `num_slots // (number of shards including the new one)` slots. Each move takes one slot from the shard that currently owns the **most** slots (ties: the shard added earliest), and takes that shard's **highest-numbered** slot. Return the number of slots moved.
- `remove_shard(name)` → reassign each of its slots, in ascending slot order, to the remaining shard that currently owns the **fewest** slots (ties: the shard added earliest). Return the number of slots moved. There will always be at least one shard left.

**Example:** `ShardRouter(8, ["a","b"])` → `slot_counts()` is `[["a",4],["b",4]]`; `add_shard("c")` → 2 (8 // 3 = 2 slots: slot 6 from a, then slot 7 from b); `slot_counts()` → `[["a",3],["b",3],["c",2]]`.
""",
    starter='''import hashlib

class ShardRouter:
    def __init__(self, num_slots: int, shards: List[str]):
        pass

    def shard_for(self, key: str) -> str:
        pass

    def slot_counts(self) -> List[list]:
        pass

    def add_shard(self, name: str) -> int:
        pass

    def remove_shard(self, name: str) -> int:
        pass
''',
    solution='''import hashlib

class ShardRouter:
    def __init__(self, num_slots, shards):
        self.n = num_slots
        self.shards = list(shards)
        self.directory = [self.shards[i % len(self.shards)] for i in range(num_slots)]

    def _count(self, shard):
        return sum(1 for s in self.directory if s == shard)

    def shard_for(self, key):
        return self.directory[int(hashlib.md5(key.encode()).hexdigest(), 16) % self.n]

    def slot_counts(self):
        return [[s, self._count(s)] for s in self.shards]

    def add_shard(self, name):
        self.shards.append(name)
        target = self.n // len(self.shards)
        moved = 0
        while moved < target:
            donor = max(self.shards[:-1], key=lambda s: self._count(s))   # first maximum = earliest added
            slot = max(i for i, s in enumerate(self.directory) if s == donor)
            self.directory[slot] = name
            moved += 1
        return moved

    def remove_shard(self, name):
        self.shards.remove(name)
        moved = 0
        for i in range(self.n):
            if self.directory[i] == name:
                self.directory[i] = min(self.shards, key=lambda s: self._count(s))
                moved += 1
        return moved
''',
    tests=[
        _ops("ShardRouter", [8, ["a", "b"]], [("slot_counts", []), ("add_shard", ["c"]), ("slot_counts", [])]),
        _ops("ShardRouter", [16, ["s0"]], [("slot_counts", []), ("shard_for", ["user:1"]), ("add_shard", ["s1"]), ("slot_counts", []), ("add_shard", ["s2"]), ("slot_counts", []), ("add_shard", ["s3"]), ("slot_counts", [])]),
        _ops("ShardRouter", [12, ["a", "b", "c"]], [("shard_for", [f"k{i}"]) for i in range(12)]),
        _ops("ShardRouter", [12, ["a", "b", "c"]], [("add_shard", ["d"])] + [("shard_for", [f"k{i}"]) for i in range(12)] + [("slot_counts", [])]),
        _ops("ShardRouter", [12, ["a", "b", "c"]], [("remove_shard", ["b"]), ("slot_counts", [])] + [("shard_for", [f"k{i}"]) for i in range(12)]),
        _ops("ShardRouter", [10, ["a", "b", "c"]], [("slot_counts", []), ("add_shard", ["d"]), ("slot_counts", []), ("remove_shard", ["a"]), ("slot_counts", []), ("remove_shard", ["d"]), ("slot_counts", [])]),
        _ops("ShardRouter", [3, ["a", "b"]], [("slot_counts", []), ("add_shard", ["c"]), ("slot_counts", []), ("add_shard", ["d"]), ("slot_counts", []), ("add_shard", ["e"]), ("slot_counts", [])]),
        _ops("ShardRouter", [64, ["x", "y"]], [("add_shard", ["z"]), ("slot_counts", []), ("remove_shard", ["x"]), ("slot_counts", []), ("add_shard", ["w"]), ("slot_counts", [])] + [("shard_for", [f"user:{i}"]) for i in range(10)]),
        _ops("ShardRouter", [1, ["a"]], [("shard_for", ["anything"]), ("add_shard", ["b"]), ("slot_counts", []), ("shard_for", ["anything"])]),
        _ops("ShardRouter", [9, ["a", "b", "c"]], [("remove_shard", ["a"]), ("slot_counts", []), ("remove_shard", ["c"]), ("slot_counts", []), ("add_shard", ["z"]), ("slot_counts", [])]),
        _ops("ShardRouter", [20, ["a", "b", "c", "d"]], [("shard_for", [f"order:{i}"]) for i in range(8)] + [("add_shard", ["e"])] + [("shard_for", [f"order:{i}"]) for i in range(8)] + [("slot_counts", [])]),
    ],
    examples=1,
    wrong_solutions=[
        '''import hashlib
class ShardRouter:
    def __init__(self, n, shards):
        self.n, self.shards = n, list(shards)
    def shard_for(self, key):
        return self.shards[int(hashlib.md5(key.encode()).hexdigest(), 16) % len(self.shards)]
    def slot_counts(self):
        return [[s, len([i for i in range(self.n) if self.shards[i % len(self.shards)] == s])] for s in self.shards]
    def add_shard(self, name):
        self.shards.append(name)
        return self.n // len(self.shards)
    def remove_shard(self, name):
        c = len([i for i in range(self.n) if self.shards[i % len(self.shards)] == name])
        self.shards.remove(name)
        return c
''',
        '''import hashlib
class ShardRouter:
    def __init__(self, n, shards):
        self.n, self.shards = n, list(shards)
        self.d = [self.shards[i % len(self.shards)] for i in range(n)]
    def _c(self, s):
        return self.d.count(s)
    def shard_for(self, key):
        return self.d[int(hashlib.md5(key.encode()).hexdigest(), 16) % self.n]
    def slot_counts(self):
        return [[s, self._c(s)] for s in self.shards]
    def add_shard(self, name):
        self.shards.append(name)
        t, m = self.n // len(self.shards), 0
        while m < t:
            donor = max(self.shards[:-1], key=self._c)
            slot = min(i for i, s in enumerate(self.d) if s == donor)
            self.d[slot] = name; m += 1
        return m
    def remove_shard(self, name):
        self.shards.remove(name); m = 0
        for i in range(self.n):
            if self.d[i] == name:
                self.d[i] = min(self.shards, key=self._c); m += 1
        return m
''',
        '''import hashlib
class ShardRouter:
    def __init__(self, n, shards):
        self.n, self.shards = n, list(shards)
        self.d = [self.shards[i % len(self.shards)] for i in range(n)]
    def _c(self, s):
        return self.d.count(s)
    def shard_for(self, key):
        return self.d[int(hashlib.md5(key.encode()).hexdigest(), 16) % self.n]
    def slot_counts(self):
        return [[s, self._c(s)] for s in self.shards]
    def add_shard(self, name):
        self.shards.append(name)
        t, m = self.n // len(self.shards), 0
        while m < t:
            donor = max(self.shards[:-1], key=self._c)
            slot = max(i for i, s in enumerate(self.d) if s == donor)
            self.d[slot] = name; m += 1
        return m
    def remove_shard(self, name):
        self.shards.remove(name); m = 0
        first = self.shards[0]
        for i in range(self.n):
            if self.d[i] == name:
                self.d[i] = first; m += 1
        return m
''',
        '''import hashlib
class ShardRouter:
    def __init__(self, n, shards):
        self.n, self.shards = n, list(shards)
        self.d = [self.shards[i % len(self.shards)] for i in range(n)]
    def _c(self, s):
        return self.d.count(s)
    def shard_for(self, key):
        return self.d[int(hashlib.md5(key.encode()).hexdigest(), 16) % self.n]
    def slot_counts(self):
        return [[s, self._c(s)] for s in self.shards]
    def add_shard(self, name):
        self.shards.append(name)
        t, m = self.n // len(self.shards), 0
        donor = max(self.shards[:-1], key=self._c)
        while m < t:
            slot = max(i for i, s in enumerate(self.d) if s == donor)
            self.d[slot] = name; m += 1
        return m
    def remove_shard(self, name):
        self.shards.remove(name); m = 0
        for i in range(self.n):
            if self.d[i] == name:
                self.d[i] = min(self.shards, key=self._c); m += 1
        return m
''',
    ],
    guide=dict(
        prereqs="Lessons 'Scaling from zero II' (sharding, resharding), 'Design consistent hashing II' (slot directory) and 'Building blocks II' (partitioning and rebalancing).",
        intuition="Keys are glued to slots for ever; slots are movable boxes. Adding a shard means handing it a fair share of boxes taken from whoever has the most. Because only boxes move, you know exactly which data must be copied.",
        hints=[
            "Keep the directory as a list of length `num_slots` holding shard names.",
            "For `add_shard`, loop `num_slots // new_shard_count` times; each time recompute which existing shard has the most slots.",
            "`max(list, key=...)` and `min(list, key=...)` return the first best element, which matches 'earliest added' when you iterate in insertion order.",
        ],
        brute_force="Route with `hash(key) % number_of_shards` and no directory: no state to maintain, but changing the shard count remaps almost every key, the rehashing problem from the scaling lessons.",
        approach="""1. Build the directory round-robin.
2. `shard_for`: hash to a slot, look it up.
3. `add_shard`: append; move `num_slots // len(shards)` slots, each from the currently largest donor's highest slot.
4. `remove_shard`: drop it from the list; give each of its slots to the currently smallest remaining shard.

**Dry run**, 8 slots, shards a, b: directory `a b a b a b a b`. `add_shard(c)`: target 8 // 3 = 2. Move 1: a and b both have 4, the earliest is a; its highest slot is 6 → c. Move 2: b has 4, a has 3 → b's highest slot 7 → c. Counts a 3, b 3, c 2.""",
        complexity="With this simple counting, `add_shard` is O(moves x num_slots) and `shard_for` is O(1). Real systems keep per-shard slot sets to make moves cheap.",
        pitfalls="Routing with modulo over the shard count (no directory); choosing one donor up front instead of re-evaluating after each move; moving the lowest slot when the rule says highest; dumping all of a removed shard's slots on one survivor.",
        follow_up="During a real move the slot's data must be copied while writes continue. Describe a safe sequence: copy, dual-write or forward, switch the directory entry, delete the old copy.",
    ),
),
dict(
    id="sd-idempotent-payments",
    title="Idempotent Transfers with a Double-Entry Ledger",
    difficulty="Medium",
    pattern="Payments",
    kind="class",
    entry="PaymentProcessor",
    description=r"""
A payment API must be safe to retry: a client that times out sends the same request again with the same **idempotency key**, and the money must move only once. Every movement is recorded as a balanced pair of ledger entries.

`PaymentProcessor()`; all amounts are positive integers (cents). Accounts start at 0 and are created on first use.

- `deposit(account, amount)` → add money from outside and append the ledger entry `[account, amount]`. Return the new balance.
- `transfer(key, src, dst, amount)`:
  - if `key` was used before with exactly the same `(src, dst, amount)`: return the **same result as the first time** and do nothing else;
  - if `key` was used before with different parameters: return `"conflict"` and do nothing (the stored result for the key is unchanged);
  - otherwise, if `src` has at least `amount`: move the money, append the two ledger entries `[src, -amount]` and `[dst, amount]` in that order, remember the result `"ok"` for this key and return `"ok"`;
  - otherwise remember and return `"insufficient"` (a later retry with the same key still returns `"insufficient"`, even if `src` has been topped up; the client must use a new key).
- `balance(account)` → current balance (0 for an unknown account).
- `ledger()` → the list of all ledger entries in order.

**Example:** `deposit("a", 100)` → 100; `transfer("k1","a","b",30)` → `"ok"`; `transfer("k1","a","b",30)` → `"ok"` (no second movement); `balance("a")` → 70; `transfer("k1","a","b",40)` → `"conflict"`.
""",
    starter='''class PaymentProcessor:
    def __init__(self):
        pass

    def deposit(self, account: str, amount: int) -> int:
        pass

    def transfer(self, key: str, src: str, dst: str, amount: int) -> str:
        pass

    def balance(self, account: str) -> int:
        pass

    def ledger(self) -> List[list]:
        pass
''',
    solution='''class PaymentProcessor:
    def __init__(self):
        self.balances = {}
        self.entries = []
        self.keys = {}                    # key -> ((src, dst, amount), result)

    def deposit(self, account, amount):
        self.balances[account] = self.balances.get(account, 0) + amount
        self.entries.append([account, amount])
        return self.balances[account]

    def transfer(self, key, src, dst, amount):
        params = (src, dst, amount)
        if key in self.keys:
            stored_params, result = self.keys[key]
            return result if stored_params == params else "conflict"
        if self.balances.get(src, 0) >= amount:
            self.balances[src] = self.balances.get(src, 0) - amount
            self.balances[dst] = self.balances.get(dst, 0) + amount
            self.entries.append([src, -amount])
            self.entries.append([dst, amount])
            result = "ok"
        else:
            result = "insufficient"
        self.keys[key] = (params, result)
        return result

    def balance(self, account):
        return self.balances.get(account, 0)

    def ledger(self):
        return [list(e) for e in self.entries]
''',
    tests=[
        _ops("PaymentProcessor", [], [("deposit", ["a", 100]), ("transfer", ["k1", "a", "b", 30]), ("transfer", ["k1", "a", "b", 30]), ("balance", ["a"]), ("transfer", ["k1", "a", "b", 40]), ("balance", ["b"]), ("ledger", [])]),
        _ops("PaymentProcessor", [], [("balance", ["nobody"]), ("ledger", []), ("transfer", ["k", "a", "b", 1]), ("transfer", ["k", "a", "b", 1]), ("deposit", ["a", 5]), ("transfer", ["k", "a", "b", 1]), ("transfer", ["k2", "a", "b", 1]), ("balance", ["a"]), ("balance", ["b"])]),
        _ops("PaymentProcessor", [], [("deposit", ["a", 50]), ("transfer", ["x", "a", "b", 50]), ("transfer", ["y", "a", "b", 1]), ("transfer", ["z", "b", "a", 20]), ("balance", ["a"]), ("balance", ["b"]), ("ledger", [])]),
        _ops("PaymentProcessor", [], [("deposit", ["a", 10])] + [("transfer", ["same", "a", "b", 3])] * 6 + [("balance", ["a"]), ("balance", ["b"]), ("ledger", [])]),
        _ops("PaymentProcessor", [], [("deposit", ["a", 10])] + [("transfer", [f"k{i}", "a", "b", 3]) for i in range(5)] + [("balance", ["a"]), ("balance", ["b"])]),
        _ops("PaymentProcessor", [], [("deposit", ["a", 100]), ("transfer", ["k", "a", "b", 10]), ("transfer", ["k", "a", "c", 10]), ("transfer", ["k", "b", "a", 10]), ("transfer", ["k", "a", "b", 10]), ("balance", ["a"]), ("balance", ["b"]), ("balance", ["c"])]),
        _ops("PaymentProcessor", [], [("deposit", ["a", 5]), ("deposit", ["a", 5]), ("deposit", ["b", 1]), ("transfer", ["t", "a", "a", 4]), ("balance", ["a"]), ("ledger", [])]),
        _ops("PaymentProcessor", [], [("deposit", ["a", 7]), ("transfer", ["k1", "a", "b", 7]), ("transfer", ["k2", "b", "c", 7]), ("transfer", ["k3", "c", "a", 7]), ("transfer", ["k1", "a", "b", 7]), ("balance", ["a"]), ("balance", ["b"]), ("balance", ["c"]), ("ledger", [])]),
        _ops("PaymentProcessor", [], [("deposit", ["a", 1]), ("transfer", ["k", "a", "b", 2]), ("transfer", ["k", "a", "b", 1]), ("transfer", ["k", "a", "b", 2]), ("deposit", ["a", 10]), ("transfer", ["k", "a", "b", 2]), ("balance", ["a"])]),
        _ops("PaymentProcessor", [], [("deposit", [f"u{i}", 100]) for i in range(4)] + [("transfer", [f"t{i % 5}", f"u{i % 4}", f"u{(i + 1) % 4}", 10 + i % 5]) for i in range(20)] + [("balance", [f"u{i}"]) for i in range(4)]),
    ],
    examples=1,
    wrong_solutions=[
        '''class PaymentProcessor:
    def __init__(self):
        self.b, self.e = {}, []
    def deposit(self, a, n):
        self.b[a] = self.b.get(a, 0) + n; self.e.append([a, n]); return self.b[a]
    def transfer(self, key, s, d, n):
        if self.b.get(s, 0) >= n:
            self.b[s] = self.b.get(s, 0) - n; self.b[d] = self.b.get(d, 0) + n
            self.e += [[s, -n], [d, n]]
            return "ok"
        return "insufficient"
    def balance(self, a):
        return self.b.get(a, 0)
    def ledger(self):
        return [list(x) for x in self.e]
''',
        '''class PaymentProcessor:
    def __init__(self):
        self.b, self.e, self.k = {}, [], {}
    def deposit(self, a, n):
        self.b[a] = self.b.get(a, 0) + n; self.e.append([a, n]); return self.b[a]
    def transfer(self, key, s, d, n):
        if key in self.k:
            return self.k[key]
        if self.b.get(s, 0) >= n:
            self.b[s] = self.b.get(s, 0) - n; self.b[d] = self.b.get(d, 0) + n
            self.e += [[s, -n], [d, n]]
            r = "ok"
        else:
            r = "insufficient"
        self.k[key] = r
        return r
    def balance(self, a):
        return self.b.get(a, 0)
    def ledger(self):
        return [list(x) for x in self.e]
''',
        '''class PaymentProcessor:
    def __init__(self):
        self.b, self.e, self.k = {}, [], {}
    def deposit(self, a, n):
        self.b[a] = self.b.get(a, 0) + n; self.e.append([a, n]); return self.b[a]
    def transfer(self, key, s, d, n):
        p = (s, d, n)
        if key in self.k:
            return "ok" if self.k[key] == p else "conflict"
        if self.b.get(s, 0) >= n:
            self.b[s] = self.b.get(s, 0) - n; self.b[d] = self.b.get(d, 0) + n
            self.e += [[s, -n], [d, n]]
            self.k[key] = p
            return "ok"
        return "insufficient"
    def balance(self, a):
        return self.b.get(a, 0)
    def ledger(self):
        return [list(x) for x in self.e]
''',
        '''class PaymentProcessor:
    def __init__(self):
        self.b, self.e, self.k = {}, [], {}
    def deposit(self, a, n):
        self.b[a] = self.b.get(a, 0) + n; self.e.append([a, n]); return self.b[a]
    def transfer(self, key, s, d, n):
        p = (s, d, n)
        if key in self.k:
            sp, r = self.k[key]
            return r if sp == p else "conflict"
        if self.b.get(s, 0) > n:
            self.b[s] = self.b.get(s, 0) - n; self.b[d] = self.b.get(d, 0) + n
            self.e += [[s, -n], [d, n]]
            r = "ok"
        else:
            r = "insufficient"
        self.k[key] = (p, r)
        return r
    def balance(self, a):
        return self.b.get(a, 0)
    def ledger(self):
        return [list(x) for x in self.e]
''',
    ],
    guide=dict(
        prereqs="Lesson 'Design a payment system' (idempotency keys, double-entry ledger) and 'Building blocks III' (idempotency).",
        intuition="The server keeps a small table: idempotency key → what was asked and what was answered. A repeat of the same question gets the saved answer and no side effect. A different question under the same key is a client bug and is refused.",
        hints=[
            "Store for each key both the parameters and the result.",
            "Check the key table before touching any balance.",
            "Store the result for failed attempts too, so a retry of an 'insufficient' request gives the same answer.",
        ],
        brute_force="No key table: every retry moves money again. Scanning the ledger for 'a similar transfer a moment ago' is a heuristic that both blocks legitimate repeat payments and misses real duplicates.",
        approach="""1. `params = (src, dst, amount)`.
2. Key seen: return the stored result if the parameters match, else `"conflict"`.
3. New key: if funds suffice, update both balances and append the two entries; else `"insufficient"`. Store `(params, result)`.

**Dry run**: deposit a 100. `transfer(k1, a, b, 30)` → ok; a 70, b 30; ledger gains `[a,-30]`, `[b,30]`. Same call again → the key exists with identical parameters → `"ok"`, nothing moves. `transfer(k1, a, b, 40)` → parameters differ → `"conflict"`.""",
        complexity="O(1) per call; space grows with the number of keys (real systems expire them after about a day).",
        pitfalls="Replaying without comparing parameters; not storing failed results; using `>` instead of `>=` for the balance check; recording one ledger entry instead of a balanced pair. In a real service the key check, the balance update and the ledger write must happen in one database transaction.",
        follow_up="Two requests with the same new key arrive at the same instant on different servers. How does a unique constraint on the key column make exactly one of them proceed?",
    ),
),
dict(
    id="sd-lease-leader-election",
    title="Leader Election by Lease with Fencing Tokens",
    difficulty="Medium",
    pattern="Coordination",
    kind="class",
    entry="LeaseLock",
    description=r"""
A group of workers must agree that only one of them is the **leader** at a time. A simple way is a **lease**: a lock that expires by itself, so that a crashed leader does not hold it for ever. Because a paused old leader may still believe it holds the lease, every grant comes with a **fencing token**, a number that only increases; the storage system rejects writes carrying an older token.

`LeaseLock(duration)`. The lease is held while `now < expiry`.

- `acquire(node, now)`:
  - if the lease is held by another node, return `-1`;
  - if it is held by `node` itself, extend it (`expiry = now + duration`) and return its current token;
  - otherwise (free or expired) grant it: the token is the previous token plus 1 (the first token is 1), the holder becomes `node`, `expiry = now + duration`; return the new token.
- `renew(node, now)` → if `node` holds the unexpired lease, extend it and return `True`; else `False`.
- `release(node, now)` → if `node` holds the unexpired lease, free it and return `True`; else `False`.
- `leader(now)` → the current holder, or `None` if the lease is free or expired.
- `accept_write(token)` → the storage side. Return `True` if `token` is greater than or equal to the highest token it has seen so far (and remember it); otherwise `False`.

**Example:** `LeaseLock(10)`: `acquire("a",0)` → 1; `acquire("b",5)` → -1; `acquire("b",10)` → 2 (a's lease expired); `accept_write(2)` → True; `accept_write(1)` → False (a's stale write is fenced off).
""",
    starter='''class LeaseLock:
    def __init__(self, duration: int):
        pass

    def acquire(self, node: str, now: int) -> int:
        pass

    def renew(self, node: str, now: int) -> bool:
        pass

    def release(self, node: str, now: int) -> bool:
        pass

    def leader(self, now: int):
        pass

    def accept_write(self, token: int) -> bool:
        pass
''',
    solution='''class LeaseLock:
    def __init__(self, duration):
        self.duration = duration
        self.holder, self.expiry, self.token = None, 0, 0
        self.highest_seen = 0

    def _held(self, now):
        return self.holder is not None and now < self.expiry

    def acquire(self, node, now):
        if self._held(now):
            if self.holder != node:
                return -1
            self.expiry = now + self.duration
            return self.token
        self.token += 1
        self.holder, self.expiry = node, now + self.duration
        return self.token

    def renew(self, node, now):
        if self._held(now) and self.holder == node:
            self.expiry = now + self.duration
            return True
        return False

    def release(self, node, now):
        if self._held(now) and self.holder == node:
            self.holder = None
            return True
        return False

    def leader(self, now):
        return self.holder if self._held(now) else None

    def accept_write(self, token):
        if token >= self.highest_seen:
            self.highest_seen = token
            return True
        return False
''',
    tests=[
        _ops("LeaseLock", [10], [("acquire", ["a", 0]), ("acquire", ["b", 5]), ("acquire", ["b", 10]), ("accept_write", [2]), ("accept_write", [1])]),
        _ops("LeaseLock", [10], [("leader", [0]), ("renew", ["a", 0]), ("release", ["a", 0]), ("acquire", ["a", 1]), ("leader", [1]), ("leader", [10]), ("leader", [11])]),
        _ops("LeaseLock", [5], [("acquire", ["a", 0]), ("renew", ["a", 4]), ("leader", [8]), ("leader", [9]), ("renew", ["a", 9]), ("acquire", ["a", 9]), ("leader", [9])]),
        _ops("LeaseLock", [5], [("acquire", ["a", 0]), ("acquire", ["a", 3]), ("leader", [7]), ("acquire", ["b", 7]), ("acquire", ["b", 8]), ("leader", [8])]),
        _ops("LeaseLock", [5], [("acquire", ["a", 0]), ("release", ["b", 1]), ("release", ["a", 1]), ("leader", [1]), ("acquire", ["b", 1]), ("release", ["a", 2]), ("leader", [2])]),
        _ops("LeaseLock", [3], [("acquire", [n, t]) for t, n in enumerate(["a", "b", "c", "b", "c", "a", "a", "c", "b", "b"])]),
        _ops("LeaseLock", [10], [("accept_write", [0]), ("accept_write", [3]), ("accept_write", [3]), ("accept_write", [2]), ("accept_write", [4]), ("accept_write", [1])]),
        _ops("LeaseLock", [4], [("acquire", ["a", 0]), ("renew", ["a", 3]), ("renew", ["a", 6]), ("renew", ["a", 10]), ("acquire", ["b", 10]), ("renew", ["a", 11]), ("release", ["a", 11]), ("leader", [11]), ("accept_write", [1]), ("accept_write", [2]), ("accept_write", [1])]),
        _ops("LeaseLock", [1], [("acquire", ["a", 0]), ("acquire", ["b", 0]), ("acquire", ["b", 1]), ("acquire", ["a", 1]), ("acquire", ["a", 2]), ("leader", [2]), ("leader", [3])]),
        _ops("LeaseLock", [10], [("acquire", ["a", 0]), ("release", ["a", 5]), ("acquire", ["a", 5]), ("release", ["a", 20]), ("acquire", ["b", 20]), ("leader", [29]), ("leader", [30])]),
        _ops("LeaseLock", [6], [("acquire", ["a", 0]), ("leader", [5]), ("acquire", ["b", 6]), ("renew", ["a", 6]), ("release", ["a", 7]), ("leader", [7]), ("renew", ["b", 11]), ("leader", [16]), ("leader", [17])]),
    ],
    examples=1,
    wrong_solutions=[
        '''class LeaseLock:
    def __init__(self, d):
        self.d, self.h, self.t, self.hi = d, None, 0, 0
    def acquire(self, node, now):
        if self.h is not None:
            return self.t if self.h == node else -1
        self.t += 1; self.h = node
        return self.t
    def renew(self, node, now):
        return self.h == node
    def release(self, node, now):
        if self.h == node:
            self.h = None
            return True
        return False
    def leader(self, now):
        return self.h
    def accept_write(self, token):
        if token >= self.hi:
            self.hi = token
            return True
        return False
''',
        '''class LeaseLock:
    def __init__(self, d):
        self.d, self.h, self.e, self.t, self.hi = d, None, 0, 0, 0
    def _held(self, now):
        return self.h is not None and now < self.e
    def acquire(self, node, now):
        if self._held(now):
            if self.h != node:
                return -1
            self.e = now + self.d
            return self.t
        self.h, self.e = node, now + self.d
        self.t = 1
        return self.t
    def renew(self, node, now):
        if self._held(now) and self.h == node:
            self.e = now + self.d
            return True
        return False
    def release(self, node, now):
        if self._held(now) and self.h == node:
            self.h = None
            return True
        return False
    def leader(self, now):
        return self.h if self._held(now) else None
    def accept_write(self, token):
        if token >= self.hi:
            self.hi = token
            return True
        return False
''',
        '''class LeaseLock:
    def __init__(self, d):
        self.d, self.h, self.e, self.t, self.hi = d, None, 0, 0, 0
    def _held(self, now):
        return self.h is not None and now <= self.e
    def acquire(self, node, now):
        if self._held(now):
            if self.h != node:
                return -1
            self.e = now + self.d
            return self.t
        self.t += 1
        self.h, self.e = node, now + self.d
        return self.t
    def renew(self, node, now):
        if self._held(now) and self.h == node:
            self.e = now + self.d
            return True
        return False
    def release(self, node, now):
        if self._held(now) and self.h == node:
            self.h = None
            return True
        return False
    def leader(self, now):
        return self.h if self._held(now) else None
    def accept_write(self, token):
        if token >= self.hi:
            self.hi = token
            return True
        return False
''',
        '''class LeaseLock:
    def __init__(self, d):
        self.d, self.h, self.e, self.t, self.hi = d, None, 0, 0, 0
    def _held(self, now):
        return self.h is not None and now < self.e
    def acquire(self, node, now):
        if self._held(now):
            if self.h != node:
                return -1
            self.e = now + self.d
            return self.t
        self.t += 1
        self.h, self.e = node, now + self.d
        return self.t
    def renew(self, node, now):
        if self.h == node:
            self.e = now + self.d
            return True
        return False
    def release(self, node, now):
        if self._held(now) and self.h == node:
            self.h = None
            return True
        return False
    def leader(self, now):
        return self.h if self._held(now) else None
    def accept_write(self, token):
        return True
''',
    ],
    guide=dict(
        prereqs="Lessons 'Design a unique ID generator II' (leases for machine IDs) and 'Design a metrics system and a job scheduler' (leader election). The Databases track lesson on fencing tokens is useful background.",
        intuition="A lock that never expires is dangerous because its holder can die. A lock that expires is dangerous because its holder can be slow and not notice. The lease handles the first problem and the fencing token the second: the resource itself refuses anyone holding an out-of-date number.",
        hints=[
            "Write one helper `_held(now)`: there is a holder and `now < expiry`.",
            "The token increases only when the lease is granted afresh, not when the same holder extends it.",
            "`accept_write` keeps the highest token it has seen and rejects anything smaller.",
        ],
        brute_force="A lock with no expiry: correct until the leader crashes, after which nobody can ever lead again without manual intervention.",
        approach="""State: holder, expiry, token, highest_seen.

1. `acquire`: held by another → -1; held by self → extend, same token; else `token += 1`, grant.
2. `renew`, `release`: only for the current, unexpired holder.
3. `leader`: holder if held.
4. `accept_write`: compare with `highest_seen`.

**Dry run**, duration 10: `acquire(a, 0)` → token 1, expiry 10. `acquire(b, 5)` → -1. `acquire(b, 10)`: 10 is not < 10, so the lease has expired → token 2. Node a, unaware, writes with token 1 after b wrote with token 2 → rejected.""",
        complexity="O(1) per operation and O(1) state.",
        pitfalls="Treating the lease as held at exactly its expiry time; issuing a new token on every extension, or the same token to different holders; letting an expired holder renew; a storage layer that accepts any token.",
        follow_up="This model has one clock. With real clocks that drift, why should a leader stop acting somewhat *before* its lease expires?",
    ),
),
dict(
    id="sd-circuit-breaker",
    title="Circuit Breaker State Machine",
    difficulty="Hard",
    pattern="Resilience",
    kind="class",
    entry="CircuitBreaker",
    description=r"""
A circuit breaker stops a service from calling a dependency that is failing, gives it time to recover, then tests it carefully.

`CircuitBreaker(failure_threshold, reset_timeout, half_open_successes)` starts **closed**.

States:

- **closed**: calls are allowed. Count *consecutive* failures; a success resets the count to 0. When the count reaches `failure_threshold`, the breaker becomes **open** at that moment.
- **open**: calls are rejected. Once `reset_timeout` time units have passed since it opened (`now - opened_at >= reset_timeout`), it becomes **half_open**.
- **half_open**: trial calls are allowed. One failure sends it back to **open** (the timeout restarts from that moment). After `half_open_successes` consecutive successes it becomes **closed** with its failure count reset to 0.

Methods (time never decreases):

- `state(now)` → `"closed"`, `"open"` or `"half_open"`, after applying the open → half_open transition if its time has come.
- `allow(now)` → `True` unless the state at `now` is `"open"`.
- `record(success, now)` → `None`. Report the outcome of a call that finished at `now`. First apply the timeout transition; a result reported while the breaker is **open** is ignored.

**Example:** `CircuitBreaker(2, 10, 1)`: `record(False,0)`, `record(False,1)` → open; `allow(5)` → False; `state(11)` → `"half_open"`; `record(True,11)` → closed; `state(11)` → `"closed"`.
""",
    starter='''class CircuitBreaker:
    def __init__(self, failure_threshold: int, reset_timeout: int, half_open_successes: int):
        pass

    def state(self, now: int) -> str:
        pass

    def allow(self, now: int) -> bool:
        pass

    def record(self, success: bool, now: int) -> None:
        pass
''',
    solution='''class CircuitBreaker:
    def __init__(self, failure_threshold, reset_timeout, half_open_successes):
        self.threshold, self.timeout, self.needed = failure_threshold, reset_timeout, half_open_successes
        self.mode = "closed"
        self.failures = 0
        self.successes = 0
        self.opened_at = 0

    def state(self, now):
        if self.mode == "open" and now - self.opened_at >= self.timeout:
            self.mode = "half_open"
            self.successes = 0
        return self.mode

    def allow(self, now):
        return self.state(now) != "open"

    def _open(self, now):
        self.mode, self.opened_at = "open", now

    def record(self, success, now):
        mode = self.state(now)
        if mode == "open":
            return
        if mode == "closed":
            if success:
                self.failures = 0
            else:
                self.failures += 1
                if self.failures >= self.threshold:
                    self._open(now)
        else:                                   # half_open
            if success:
                self.successes += 1
                if self.successes >= self.needed:
                    self.mode, self.failures = "closed", 0
            else:
                self._open(now)
''',
    tests=[
        _ops("CircuitBreaker", [2, 10, 1], [("record", [False, 0]), ("record", [False, 1]), ("allow", [5]), ("state", [11]), ("record", [True, 11]), ("state", [11])]),
        _ops("CircuitBreaker", [3, 5, 2], [("state", [0]), ("allow", [0]), ("record", [False, 1]), ("record", [False, 2]), ("record", [True, 3]), ("record", [False, 4]), ("record", [False, 5]), ("state", [5]), ("record", [False, 6]), ("state", [6]), ("allow", [6])]),
        _ops("CircuitBreaker", [1, 10, 2], [("record", [False, 0]), ("state", [9]), ("state", [10]), ("allow", [10]), ("record", [True, 10]), ("state", [10]), ("record", [True, 11]), ("state", [11])]),
        _ops("CircuitBreaker", [1, 10, 2], [("record", [False, 0]), ("record", [True, 10]), ("record", [False, 11]), ("state", [11]), ("state", [20]), ("state", [21]), ("allow", [21])]),
        _ops("CircuitBreaker", [2, 4, 1], [("record", [False, 0]), ("record", [False, 0]), ("record", [True, 1]), ("record", [True, 2]), ("state", [3]), ("state", [4]), ("record", [False, 4]), ("allow", [7]), ("allow", [8]), ("record", [True, 8]), ("state", [8])]),
        _ops("CircuitBreaker", [3, 5, 1], [("record", [False, t]) for t in range(3)] + [("record", [False, 3]), ("record", [False, 4]), ("state", [6]), ("state", [7]), ("record", [True, 7]), ("record", [False, 8]), ("record", [False, 9]), ("state", [9]), ("record", [False, 10]), ("state", [10])]),
        _ops("CircuitBreaker", [2, 3, 3], [("record", [False, 0]), ("record", [False, 0]), ("record", [True, 3]), ("record", [True, 3]), ("state", [3]), ("record", [False, 4]), ("state", [4]), ("record", [True, 7]), ("record", [True, 7]), ("record", [True, 7]), ("state", [7])]),
        _ops("CircuitBreaker", [5, 100, 1], [("record", [i % 2 == 0, i]) for i in range(20)] + [("state", [20]), ("allow", [20])]),
        _ops("CircuitBreaker", [1, 0, 1], [("record", [False, 0]), ("state", [0]), ("allow", [0]), ("record", [False, 0]), ("state", [0]), ("record", [True, 0]), ("state", [0])]),
        _ops("CircuitBreaker", [2, 10, 2], [("record", [False, 0]), ("record", [False, 1]), ("allow", [10]), ("allow", [11]), ("record", [True, 12]), ("allow", [12]), ("record", [False, 13]), ("allow", [13]), ("allow", [22]), ("allow", [23]), ("state", [23])]),
        _ops("CircuitBreaker", [3, 5, 1], [("record", [False, 0]), ("record", [False, 1]), ("record", [False, 2]), ("record", [True, 7]), ("record", [False, 8]), ("record", [False, 9]), ("state", [9]), ("record", [False, 10]), ("state", [10])]),
    ],
    examples=1,
    wrong_solutions=[
        '''class CircuitBreaker:
    def __init__(self, th, to, need):
        self.th, self.to, self.need, self.m, self.f, self.s, self.o = th, to, need, "closed", 0, 0, 0
    def state(self, now):
        if self.m == "open" and now - self.o >= self.to:
            self.m, self.s = "half_open", 0
        return self.m
    def allow(self, now):
        return self.state(now) != "open"
    def record(self, ok, now):
        m = self.state(now)
        if m == "open":
            return
        if m == "closed":
            if not ok:
                self.f += 1
                if self.f >= self.th:
                    self.m, self.o = "open", now
        else:
            if ok:
                self.s += 1
                if self.s >= self.need:
                    self.m, self.f = "closed", 0
            else:
                self.m, self.o = "open", now
''',
        '''class CircuitBreaker:
    def __init__(self, th, to, need):
        self.th, self.to, self.need, self.m, self.f, self.s, self.o = th, to, need, "closed", 0, 0, 0
    def state(self, now):
        if self.m == "open" and now - self.o >= self.to:
            self.m, self.s = "closed", 0
            self.f = 0
        return self.m
    def allow(self, now):
        return self.state(now) != "open"
    def record(self, ok, now):
        m = self.state(now)
        if m == "open":
            return
        if ok:
            self.f = 0
        else:
            self.f += 1
            if self.f >= self.th:
                self.m, self.o = "open", now
''',
        '''class CircuitBreaker:
    def __init__(self, th, to, need):
        self.th, self.to, self.need, self.m, self.f, self.s, self.o = th, to, need, "closed", 0, 0, 0
    def state(self, now):
        if self.m == "open" and now - self.o > self.to:
            self.m, self.s = "half_open", 0
        return self.m
    def allow(self, now):
        return self.state(now) != "open"
    def record(self, ok, now):
        m = self.state(now)
        if m == "open":
            return
        if m == "closed":
            if ok:
                self.f = 0
            else:
                self.f += 1
                if self.f >= self.th:
                    self.m, self.o = "open", now
        else:
            if ok:
                self.s += 1
                if self.s >= self.need:
                    self.m, self.f = "closed", 0
            else:
                self.m, self.o = "open", now
''',
        '''class CircuitBreaker:
    def __init__(self, th, to, need):
        self.th, self.to, self.need, self.m, self.f, self.s, self.o = th, to, need, "closed", 0, 0, 0
    def state(self, now):
        if self.m == "open" and now - self.o >= self.to:
            self.m, self.s = "half_open", 0
        return self.m
    def allow(self, now):
        return self.state(now) != "open"
    def record(self, ok, now):
        m = self.state(now)
        if m == "open":
            return
        if m == "closed":
            if ok:
                self.f = 0
            else:
                self.f += 1
                if self.f >= self.th:
                    self.m, self.o = "open", now
        else:
            if ok:
                self.s += 1
                if self.s >= self.need:
                    self.m = "closed"
            else:
                self.m, self.o = "open", now
''',
    ],
    guide=dict(
        prereqs="Lesson 'Building blocks IV' (timeouts, retries, circuit breakers). The idea of a state machine: a fixed set of states and rules for moving between them.",
        intuition="It is the fuse box in a house. Too many faults and the fuse trips, cutting the circuit so the wiring does not burn. After a while you push the switch back gently (half open): if the fault is gone, power stays on; if not, it trips again at once.",
        hints=[
            "Keep the mode, a consecutive-failure count, a half-open success count and the time the breaker opened.",
            "Put the open → half_open check in `state(now)` and call `state` at the start of `allow` and `record`.",
            "On closing from half_open, reset the failure count; on entering half_open, reset the success count.",
        ],
        brute_force="No breaker: every request waits for the full timeout of a dead dependency, threads pile up and the caller fails too. Retries without a breaker multiply the load on a service that is trying to recover.",
        approach="""Transitions:

| From | Event | To |
|---|---|---|
| closed | failures reach threshold | open (opened_at = now) |
| closed | success | closed, failures = 0 |
| open | reset_timeout elapsed | half_open, successes = 0 |
| half_open | failure | open (opened_at = now) |
| half_open | enough successes | closed, failures = 0 |

**Dry run** `(2, 10, 1)`: failures at 0 and 1 → open at 1. `allow(5)`: 5 - 1 = 4 < 10 → False. `state(11)`: 11 - 1 = 10 >= 10 → half_open. `record(True, 11)`: 1 success, which is enough → closed.""",
        complexity="O(1) per call and O(1) state.",
        pitfalls="Counting total failures instead of consecutive ones (a healthy service with occasional errors would eventually trip); going straight from open to closed; not restarting the timeout after a half-open failure; leaving an old failure count in place after closing, so the next single failure trips the breaker again.",
        follow_up="Production breakers use a failure *rate* over a sliding window and limit how many trial calls run at once in half-open. Add both.",
    ),
),
dict(
    id="sd-backpressure-queue",
    title="Back-pressure: Simulate a Bounded Queue",
    difficulty="Medium",
    pattern="Queues",
    kind="function",
    entry="simulate_queue",
    description=r"""
A producer puts work into a queue of limited size and a consumer takes it out at a fixed rate. When the producer is faster, something has to give. Simulate three policies.

`simulate_queue(arrivals, capacity, service_rate, policy)`:

`arrivals[t]` items arrive at tick `t` (ticks are 0, 1, 2, ...). The queue holds at most `capacity` items and is first-in, first-out. In each tick, **admission** happens first, then **service**.

**Admission**, by `policy`:

- `"drop_new"`: each arriving item joins the queue if there is room; otherwise it is dropped.
- `"drop_old"`: each arriving item joins the queue; if the queue is full, the **oldest** queued item is dropped first to make room. (With `capacity == 0` the arriving item itself is dropped.)
- `"block"`: nothing is dropped. Items that do not fit wait outside, in arrival order, and are admitted in later ticks as soon as there is room, before that tick's new arrivals. (The producer is being slowed down: this is back-pressure.)

**Service:** remove up to `service_rate` items from the front of the queue. An item that arrived at tick `a` and is served at tick `t` waited `t - a` ticks (for `"block"`, `a` is its original arrival tick).

The simulation ends after the last tick of `arrivals`. Return `[served, dropped, max_depth, total_wait]`: items served, items dropped, the largest queue length observed right after an admission phase, and the sum of the waits of all served items.

**Example:** `simulate_queue([5, 0, 0], 3, 1, "drop_new")` → `[3, 2, 3, 3]` (3 admitted and 2 dropped at tick 0; one served per tick with waits 0, 1, 2).
""",
    starter='''def simulate_queue(arrivals: List[int], capacity: int, service_rate: int, policy: str) -> List[int]:
    pass
''',
    solution='''from collections import deque

def simulate_queue(arrivals, capacity, service_rate, policy):
    queue, outside = deque(), deque()
    served = dropped = max_depth = total_wait = 0
    for t, n in enumerate(arrivals):
        if policy == "block":
            outside.extend([t] * n)
            while outside and len(queue) < capacity:
                queue.append(outside.popleft())
        else:
            for _ in range(n):
                if len(queue) < capacity:
                    queue.append(t)
                elif policy == "drop_old" and capacity > 0:
                    queue.popleft()
                    dropped += 1
                    queue.append(t)
                else:
                    dropped += 1
        max_depth = max(max_depth, len(queue))
        for _ in range(min(service_rate, len(queue))):
            total_wait += t - queue.popleft()
            served += 1
    return [served, dropped, max_depth, total_wait]
''',
    tests=[
        [[5, 0, 0], 3, 1, "drop_new"],
        [[5, 0, 0], 3, 1, "drop_old"],
        [[5, 0, 0], 3, 1, "block"],
        [[], 3, 1, "block"],
        [[0, 0, 0], 3, 1, "drop_new"],
        [[2, 2, 2, 2], 10, 2, "drop_new"],
        [[4, 4, 4, 0, 0, 0], 2, 1, "drop_old"],
        [[4, 4, 4, 0, 0, 0], 2, 1, "drop_new"],
        [[4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 2, 1, "block"],
        [[3, 3], 0, 5, "drop_new"],
        [[3, 3], 0, 5, "drop_old"],
        [[3, 3], 0, 5, "block"],
        [[10, 0, 0, 0, 10, 0, 0, 0], 4, 3, "drop_old"],
        [[10, 0, 0, 0, 10, 0, 0, 0], 4, 3, "block"],
        [[1] * 30, 5, 0, "drop_old"],
        [[7, 1, 0, 9, 2, 0, 0, 4, 0, 0], 5, 2, "drop_new"],
    ],
    examples=3,
    wrong_solutions=[
        '''from collections import deque
def simulate_queue(arrivals, capacity, rate, policy):
    q = deque(); served = dropped = md = tw = 0
    for t, n in enumerate(arrivals):
        for _ in range(n):
            if len(q) < capacity:
                q.append(t)
            else:
                dropped += 1
        md = max(md, len(q))
        for _ in range(min(rate, len(q))):
            tw += t - q.popleft(); served += 1
    return [served, dropped, md, tw]
''',
        '''from collections import deque
def simulate_queue(arrivals, capacity, rate, policy):
    q, out = deque(), deque(); served = dropped = md = tw = 0
    for t, n in enumerate(arrivals):
        for _ in range(min(rate, len(q))):
            tw += t - q.popleft(); served += 1
        if policy == "block":
            out.extend([t] * n)
            while out and len(q) < capacity:
                q.append(out.popleft())
        else:
            for _ in range(n):
                if len(q) < capacity:
                    q.append(t)
                elif policy == "drop_old" and capacity > 0:
                    q.popleft(); dropped += 1; q.append(t)
                else:
                    dropped += 1
        md = max(md, len(q))
    return [served, dropped, md, tw]
''',
        '''from collections import deque
def simulate_queue(arrivals, capacity, rate, policy):
    q, out = deque(), deque(); served = dropped = md = tw = 0
    for t, n in enumerate(arrivals):
        if policy == "block":
            out.extend([t] * n)
            while out and len(q) < capacity:
                out.popleft(); q.append(t)
        else:
            for _ in range(n):
                if len(q) < capacity:
                    q.append(t)
                elif policy == "drop_old" and capacity > 0:
                    q.popleft(); dropped += 1; q.append(t)
                else:
                    dropped += 1
        md = max(md, len(q))
        for _ in range(min(rate, len(q))):
            tw += t - q.popleft(); served += 1
    return [served, dropped, md, tw]
''',
        '''from collections import deque
def simulate_queue(arrivals, capacity, rate, policy):
    q, out = deque(), deque(); served = dropped = md = tw = 0
    for t, n in enumerate(arrivals):
        if policy == "block":
            out.extend([t] * n)
            while out and len(q) < capacity:
                q.append(out.popleft())
        else:
            for _ in range(n):
                if len(q) < capacity:
                    q.append(t)
                elif policy == "drop_old" and capacity > 0:
                    q.pop(); dropped += 1; q.append(t)
                else:
                    dropped += 1
        md = max(md, len(q))
        for _ in range(min(rate, len(q))):
            tw += t - q.popleft(); served += 1
    return [served, dropped, md, tw]
''',
    ],
    guide=dict(
        prereqs="Lessons 'Scaling from zero II' (message queues, queue depth) and 'Building blocks III' (queues, back-pressure). `collections.deque`.",
        intuition="A queue between a fast producer and a slow consumer can only grow, shed load, or push back. Dropping new items protects work already accepted; dropping old items keeps the data fresh; blocking loses nothing and slows the producer instead. Storing each item's arrival tick lets you measure the price of each choice in waiting time.",
        hints=[
            "Represent each queued item by its arrival tick, so the wait is `t - item` when it is served.",
            "For `block`, keep a second deque of items waiting outside; admit from it first, in order, while there is room.",
            "Record `max_depth` after admission and before service.",
        ],
        brute_force="An unbounded queue: nothing is dropped and nobody is blocked, until memory runs out and everything is lost at once. Bounding the queue forces the choice to be explicit.",
        approach="""Per tick: admit according to the policy, update `max_depth`, then serve up to `service_rate` items from the front, adding `t - arrival` to the total wait.

**Dry run** `[5, 0, 0]`, capacity 3, rate 1:

- `drop_new`: tick 0 admits 3, drops 2; serves one (wait 0). Ticks 1 and 2 serve one each (waits 1, 2). → `[3, 2, 3, 3]`.
- `drop_old`: the 4th and 5th arrivals each push out the oldest; same counts here, because all items arrived in the same tick.
- `block`: tick 0 admits 3, 2 wait outside; one served. Tick 1 admits one more from outside, serves one (wait 1). Tick 2 admits the last, serves one (wait 2). → `[3, 0, 3, 3]`, with 2 items still queued when the simulation ends.""",
        complexity="O(total items + ticks x service_rate) time; O(capacity + blocked items) space.",
        pitfalls="Serving before admitting; measuring a blocked item's wait from when it entered the queue instead of from when it arrived; dropping the newest item under `drop_old`; forgetting the `capacity == 0` case.",
        follow_up="Compare the average wait of served items under `drop_new` and `drop_old` for a long overload. Which policy suits stock prices, and which suits payment requests?",
    ),
),
dict(
    id="sd-seat-booking",
    title="Seat Booking with Holds and Expiry",
    difficulty="Hard",
    pattern="Booking",
    kind="class",
    entry="SeatMap",
    description=r"""
A ticketing site lets a customer **hold** seats for a few minutes while paying. A held seat cannot be taken by anyone else; if the customer does not confirm in time, the hold lapses and the seats return to sale. No seat may ever be sold twice.

`SeatMap(seats, hold_seconds)`: `seats` is a list of distinct seat names.

A hold created at time `now` is **active** while `now < created + hold_seconds` and it has been neither confirmed nor cancelled.

- `hold(user, seat_ids, now)` → all-or-nothing. If `seat_ids` is empty, contains a name that is not a seat, contains a repeated name, or any requested seat is booked or under an active hold (anyone's, including this user's), return `-1` and change nothing. Otherwise create a hold on all of them and return its id. Hold ids are 1, 2, 3, ... in order of successful holds.
- `confirm(hold_id, now)` → if the hold exists and is active, its seats become permanently **booked** by its user and the result is `True`. Otherwise `False`.
- `cancel(hold_id, now)` → if the hold exists and is active, it ends, its seats are free again and the result is `True`. Otherwise `False`.
- `available(now)` → the sorted list of seats that are neither booked nor under an active hold.
- `booked_by(seat)` → the user who booked the seat, or `None`.

Time never decreases.

**Example:** `SeatMap(["A1","A2","A3"], 60)`: `hold("ann",["A1","A2"],0)` → 1; `hold("bob",["A2","A3"],10)` → -1; `hold("bob",["A3"],10)` → 2; `confirm(1,59)` → True; `confirm(2,70)` → False (expired at 70); `available(70)` → `["A3"]`.
""",
    starter='''class SeatMap:
    def __init__(self, seats: List[str], hold_seconds: int):
        pass

    def hold(self, user: str, seat_ids: List[str], now: int) -> int:
        pass

    def confirm(self, hold_id: int, now: int) -> bool:
        pass

    def cancel(self, hold_id: int, now: int) -> bool:
        pass

    def available(self, now: int) -> List[str]:
        pass

    def booked_by(self, seat: str):
        pass
''',
    solution='''class SeatMap:
    def __init__(self, seats, hold_seconds):
        self.seats = set(seats)
        self.duration = hold_seconds
        self.booked = {}                 # seat -> user
        self.holds = {}                  # hold_id -> [user, seats, expires_at, status]
        self.seat_hold = {}              # seat -> hold_id of the latest hold on it
        self.next_id = 1

    def _active(self, hold_id, now):
        h = self.holds.get(hold_id)
        return h is not None and h[3] == "active" and now < h[2]

    def _free(self, seat, now):
        if seat in self.booked:
            return False
        hid = self.seat_hold.get(seat)
        return hid is None or not self._active(hid, now)

    def hold(self, user, seat_ids, now):
        if not seat_ids or len(set(seat_ids)) != len(seat_ids):
            return -1
        if any(s not in self.seats or not self._free(s, now) for s in seat_ids):
            return -1
        hid = self.next_id
        self.next_id += 1
        self.holds[hid] = [user, list(seat_ids), now + self.duration, "active"]
        for s in seat_ids:
            self.seat_hold[s] = hid
        return hid

    def confirm(self, hold_id, now):
        if not self._active(hold_id, now):
            return False
        h = self.holds[hold_id]
        h[3] = "confirmed"
        for s in h[1]:
            self.booked[s] = h[0]
        return True

    def cancel(self, hold_id, now):
        if not self._active(hold_id, now):
            return False
        self.holds[hold_id][3] = "cancelled"
        return True

    def available(self, now):
        return sorted(s for s in self.seats if self._free(s, now))

    def booked_by(self, seat):
        return self.booked.get(seat)
''',
    tests=[
        _ops("SeatMap", [["A1", "A2", "A3"], 60], [("hold", ["ann", ["A1", "A2"], 0]), ("hold", ["bob", ["A2", "A3"], 10]), ("hold", ["bob", ["A3"], 10]), ("confirm", [1, 59]), ("confirm", [2, 70]), ("available", [70])]),
        _ops("SeatMap", [["A1"], 10], [("available", [0]), ("hold", ["u", [], 0]), ("hold", ["u", ["Z9"], 0]), ("hold", ["u", ["A1", "A1"], 0]), ("confirm", [1, 0]), ("cancel", [5, 0]), ("booked_by", ["A1"]), ("available", [0])]),
        _ops("SeatMap", [["A1", "A2"], 10], [("hold", ["a", ["A1"], 0]), ("hold", ["b", ["A1"], 9]), ("hold", ["b", ["A1"], 10]), ("confirm", [1, 10]), ("confirm", [2, 15]), ("booked_by", ["A1"]), ("available", [15])]),
        _ops("SeatMap", [["A1", "A2"], 10], [("hold", ["a", ["A1", "A2"], 0]), ("cancel", [1, 5]), ("cancel", [1, 6]), ("confirm", [1, 6]), ("available", [6]), ("hold", ["b", ["A2"], 6]), ("confirm", [2, 7]), ("confirm", [2, 8]), ("cancel", [2, 8]), ("booked_by", ["A2"]), ("available", [8])]),
        _ops("SeatMap", [["A1", "A2", "A3"], 5], [("hold", ["a", ["A1"], 0]), ("hold", ["a", ["A1"], 1]), ("hold", ["a", ["A2"], 1]), ("available", [1]), ("available", [5]), ("available", [6]), ("confirm", [2, 5]), ("available", [6])]),
        _ops("SeatMap", [["S1", "S2", "S3", "S4"], 30], [("hold", ["a", ["S1", "S2"], 0]), ("confirm", [1, 10]), ("hold", ["b", ["S2", "S3"], 20]), ("hold", ["b", ["S3", "S4"], 20]), ("available", [20]), ("available", [50]), ("hold", ["c", ["S1"], 100]), ("booked_by", ["S1"]), ("booked_by", ["S3"])]),
        _ops("SeatMap", [["A", "B"], 10], [("hold", ["x", ["A"], 0]), ("hold", ["y", ["B"], 0]), ("hold", ["z", ["A", "B"], 10]), ("confirm", [1, 10]), ("confirm", [2, 10]), ("confirm", [3, 19]), ("booked_by", ["A"]), ("booked_by", ["B"]), ("hold", ["w", ["A"], 100])]),
        _ops("SeatMap", [[f"R{i}" for i in range(6)], 15], [("hold", [f"u{i}", [f"R{i}", f"R{(i + 1) % 6}"], i * 4]) for i in range(8)] + [("available", [40]), ("confirm", [1, 14]), ("confirm", [2, 40])]),
        _ops("SeatMap", [["A1"], 0], [("hold", ["a", ["A1"], 0]), ("confirm", [1, 0]), ("available", [0]), ("hold", ["b", ["A1"], 0])]),
        _ops("SeatMap", [["A1", "A2"], 10], [("hold", ["a", ["A1"], 0]), ("cancel", [1, 3]), ("hold", ["b", ["A1"], 3]), ("confirm", [1, 4]), ("confirm", [2, 4]), ("booked_by", ["A1"]), ("cancel", [2, 5])]),
        _ops("SeatMap", [["A1", "A2", "A3"], 20], [("hold", ["a", ["A3", "A1"], 0]), ("available", [0]), ("hold", ["b", ["A2", "A3"], 19]), ("hold", ["b", ["A2", "A3"], 20]), ("confirm", [1, 20]), ("confirm", [2, 39]), ("available", [39]), ("booked_by", ["A3"])]),
    ],
    examples=1,
    wrong_solutions=[
        '''class SeatMap:
    def __init__(self, seats, d):
        self.seats, self.d, self.booked, self.holds, self.sh, self.n = set(seats), d, {}, {}, {}, 1
    def _free(self, s, now):
        return s not in self.booked and s not in self.sh
    def hold(self, u, ids, now):
        if not ids or len(set(ids)) != len(ids) or any(s not in self.seats or not self._free(s, now) for s in ids):
            return -1
        h = self.n; self.n += 1
        self.holds[h] = [u, list(ids), "active"]
        for s in ids:
            self.sh[s] = h
        return h
    def confirm(self, h, now):
        x = self.holds.get(h)
        if not x or x[2] != "active":
            return False
        x[2] = "confirmed"
        for s in x[1]:
            self.booked[s] = x[0]
        return True
    def cancel(self, h, now):
        x = self.holds.get(h)
        if not x or x[2] != "active":
            return False
        x[2] = "cancelled"
        for s in x[1]:
            del self.sh[s]
        return True
    def available(self, now):
        return sorted(s for s in self.seats if self._free(s, now))
    def booked_by(self, s):
        return self.booked.get(s)
''',
        '''class SeatMap:
    def __init__(self, seats, d):
        self.seats, self.d, self.booked, self.holds, self.sh, self.n = set(seats), d, {}, {}, {}, 1
    def _active(self, h, now):
        x = self.holds.get(h)
        return x is not None and x[3] == "active" and now < x[2]
    def _free(self, s, now):
        if s in self.booked:
            return False
        h = self.sh.get(s)
        return h is None or not self._active(h, now)
    def hold(self, u, ids, now):
        if not ids or len(set(ids)) != len(ids):
            return -1
        h = self.n; self.n += 1
        got = [s for s in ids if s in self.seats and self._free(s, now)]
        if len(got) != len(ids):
            return -1
        self.holds[h] = [u, list(ids), now + self.d, "active"]
        for s in ids:
            self.sh[s] = h
        return h
    def confirm(self, h, now):
        if not self._active(h, now):
            return False
        x = self.holds[h]; x[3] = "confirmed"
        for s in x[1]:
            self.booked[s] = x[0]
        return True
    def cancel(self, h, now):
        if not self._active(h, now):
            return False
        self.holds[h][3] = "cancelled"
        return True
    def available(self, now):
        return sorted(s for s in self.seats if self._free(s, now))
    def booked_by(self, s):
        return self.booked.get(s)
''',
        '''class SeatMap:
    def __init__(self, seats, d):
        self.seats, self.d, self.booked, self.holds, self.sh, self.n = set(seats), d, {}, {}, {}, 1
    def _active(self, h, now):
        x = self.holds.get(h)
        return x is not None and x[3] == "active" and now < x[2]
    def _free(self, s, now):
        if s in self.booked:
            return False
        h = self.sh.get(s)
        return h is None or not self._active(h, now)
    def hold(self, u, ids, now):
        if not ids or len(set(ids)) != len(ids):
            return -1
        if any(s not in self.seats or not self._free(s, now) for s in ids):
            return -1
        h = self.n; self.n += 1
        self.holds[h] = [u, list(ids), now + self.d, "active"]
        for s in ids:
            self.sh[s] = h
        return h
    def confirm(self, h, now):
        x = self.holds.get(h)
        if x is None or x[3] != "active":
            return False
        x[3] = "confirmed"
        for s in x[1]:
            self.booked[s] = x[0]
        return True
    def cancel(self, h, now):
        if not self._active(h, now):
            return False
        self.holds[h][3] = "cancelled"
        return True
    def available(self, now):
        return sorted(s for s in self.seats if self._free(s, now))
    def booked_by(self, s):
        return self.booked.get(s)
''',
        '''class SeatMap:
    def __init__(self, seats, d):
        self.seats, self.d, self.booked, self.holds, self.sh, self.n = set(seats), d, {}, {}, {}, 1
    def _active(self, h, now):
        x = self.holds.get(h)
        return x is not None and x[3] == "active" and now <= x[2]
    def _free(self, s, now):
        if s in self.booked:
            return False
        h = self.sh.get(s)
        return h is None or not self._active(h, now)
    def hold(self, u, ids, now):
        if not ids or len(set(ids)) != len(ids):
            return -1
        if any(s not in self.seats or not self._free(s, now) for s in ids):
            return -1
        h = self.n; self.n += 1
        self.holds[h] = [u, list(ids), now + self.d, "active"]
        for s in ids:
            self.sh[s] = h
        return h
    def confirm(self, h, now):
        if not self._active(h, now):
            return False
        x = self.holds[h]; x[3] = "confirmed"
        for s in x[1]:
            self.booked[s] = x[0]
        return True
    def cancel(self, h, now):
        if not self._active(h, now):
            return False
        self.holds[h][3] = "cancelled"
        return True
    def available(self, now):
        return sorted(s for s in self.seats if self._free(s, now))
    def booked_by(self, s):
        return self.booked.get(s)
''',
    ],
    guide=dict(
        prereqs="Lesson 'Design a ticket-booking system' (holds, expiry, overselling). Dictionaries and sets.",
        intuition="A seat is in one of three situations: booked for good, held by someone for a limited time, or free. A hold is a reservation with an end time. You never need a timer to release it: when anyone asks, compare the current time with the hold's expiry.",
        hints=[
            "Give each hold a record: user, seats, expiry time and a status (active, confirmed, cancelled).",
            "Write `_active(hold_id, now)` and `_free(seat, now)` first; every method is then a few lines.",
            "In `hold`, validate everything before changing anything, and only then take the next hold id.",
        ],
        brute_force="Check availability and then book, with no hold step: two customers both see the seat as free, both pay, and one seat is sold twice. Alternatively, hold seats with a background timer per hold, which is fragile; lazy expiry needs no timers.",
        approach="""1. `_active`: the hold exists, has status active and `now < expires_at`.
2. `_free`: not booked, and the latest hold on the seat (if any) is not active.
3. `hold`: reject empty, duplicate, unknown or unavailable seats; create the record; point each seat at it.
4. `confirm` / `cancel`: only for an active hold.

**Dry run**, 60-second holds: `hold(ann, [A1, A2], 0)` → 1, expires 60. `hold(bob, [A2, A3], 10)`: A2 is held → -1, and A3 is left untouched. `hold(bob, [A3], 10)` → 2, expires 70. `confirm(1, 59)` → True. `confirm(2, 70)`: 70 is not < 70 → False. `available(70)` → A3 (hold 2 has lapsed; A1 and A2 are booked).""",
        complexity="`hold`, `confirm`, `cancel` are O(seats in the request); `available` is O(S log S) for S seats. Space O(seats + holds).",
        pitfalls="Partial holds (taking A3 when A2 failed); consuming a hold id for a failed attempt; confirming an expired hold, which is the overselling bug; treating a hold as active at exactly its expiry; never releasing seats whose hold lapsed.",
        follow_up="In a real system two servers run `hold` at once. Which database feature makes 'check free then mark held' atomic? (A conditional update or a row lock inside one transaction.)",
    ),
),
]
