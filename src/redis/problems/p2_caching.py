"""Redis track problems 7-13: eviction caches, cache-aside, rate limiters and a leaderboard."""
import random as _r


def _seq(seed, n, ctor, ctor_args, step):
    rng, state = _r.Random(seed), {"now": 0, "tokens": []}
    ops, args = [ctor], [list(ctor_args)]
    for _ in range(n):
        op, a = step(rng, state)
        ops.append(op)
        args.append(a)
    return [ops, args]


def _cache_step(rng, st):
    if rng.random() < 0.5:
        return "get", [rng.randint(1, 6)]
    return "put", [rng.randint(1, 6), rng.randint(10, 99)]


def _aside_step(rng, st):
    st["now"] += rng.choice([0, 1, 2, 4])
    k = rng.choice(["home", "item"])
    op = rng.choice(["read", "read", "read", "fill", "fill", "invalidate"])
    if op == "read":
        return op, [k, st["now"]]
    if op == "fill":
        return op, [k, rng.randint(1, 6), "v%d" % rng.randint(1, 9), st["now"]]
    return op, [k]


def _limit_step(rng, st):
    st["now"] += rng.choice([0, 0, 1, 2, 3, 7])
    return "allow", [rng.choice(["ana", "raj"]), st["now"]]


def _bucket_step(rng, st):
    st["now"] += rng.choice([0, 0, 1, 1, 2, 5])
    return "allow", [rng.choice(["ana", "raj"]), st["now"], rng.choice([1, 1, 1, 2, 3])]


def _board_step(rng, st):
    p = rng.choice(["ada", "bo", "cy", "di", "eve", "fay"])
    op = rng.choice(["add_score", "add_score", "add_score", "top", "rank", "around", "remove"])
    if op == "add_score":
        return op, [p, rng.choice([5, 10, 10, 20])]
    if op == "top":
        return op, [rng.randint(0, 4)]
    if op == "around":
        return op, [p, rng.randint(0, 2)]
    return op, [p]


_LRU_OK = '''class LRUCache:
    def __init__(self, capacity):
        self.cap, self.d = capacity, collections.OrderedDict()
    def get(self, key):
        if key not in self.d: return -1
        %s
        return self.d[key]
    def put(self, key, value):
        if self.cap == 0: return None
        if key in self.d: self.d.move_to_end(key)
        elif len(self.d) >= self.cap: self.d.popitem(last=False)
        self.d[key] = value
'''

PROBLEMS = [
dict(
    id="redis-lru-cache",
    title="LRU Eviction Cache",
    difficulty="Medium",
    pattern="Caching",
    leetcode="https://leetcode.com/problems/lru-cache/",
    kind="class",
    entry="LRUCache",
    description=r"""
Redis's `allkeys-lru` policy removes the key that has gone longest without being used when memory is full.
Implement the exact version of that policy for a cache holding at most `capacity` integer keys.

- `LRUCache(capacity)` - `capacity >= 0`.
- `get(key)` - return the value, or `-1` if the key is absent. A successful `get` counts as a **use**.
- `put(key, value)` - insert or update (also a use). If inserting a new key would exceed the capacity, first
  evict the **least recently used** key. With capacity 0 nothing is ever stored. Returns nothing.

Both operations must run in O(1) average time.

**Example:** capacity 2: `put(1,1)`, `put(2,2)`, `get(1)` → `1`, `put(3,3)` evicts key 2, `get(2)` → `-1`
""",
    starter='''class LRUCache:
    def __init__(self, capacity: int):
        pass

    def get(self, key: int) -> int:
        pass

    def put(self, key: int, value: int) -> None:
        pass
''',
    solution=_LRU_OK % "self.d.move_to_end(key)",
    tests=[
        [["LRUCache", "put", "put", "get", "put", "get", "put", "get", "get", "get"],
         [[2], [1, 1], [2, 2], [1], [3, 3], [2], [4, 4], [1], [3], [4]]],
        [["LRUCache", "get", "put", "get"], [[0], [1], [1, 5], [1]]],
        [["LRUCache", "put", "put", "put", "get", "get"], [[1], [1, 1], [1, 9], [2, 2], [1], [2]]],
        [["LRUCache", "put", "put", "put", "put", "get", "get"], [[2], [1, 1], [2, 2], [1, 10], [3, 3], [1], [2]]],
        [["LRUCache", "put", "put", "put", "get", "put", "get", "get", "get", "get"],
         [[3], [1, 1], [2, 2], [3, 3], [1], [4, 4], [2], [1], [3], [4]]],
    ] + [_seq(s, 60, "LRUCache", [c], _cache_step) for s, c in [(1, 2), (2, 3), (3, 4), (4, 1), (5, 3), (6, 5)]],
    examples=2,
    wrong_solutions=[
        _LRU_OK % "pass   # bug: a read does not refresh recency (FIFO)",
        '''class LRUCache:
    def __init__(self, capacity):
        self.cap, self.d = capacity, collections.OrderedDict()
    def get(self, key):
        if key not in self.d: return -1
        self.d.move_to_end(key)
        return self.d[key]
    def put(self, key, value):
        if self.cap == 0: return None
        if len(self.d) >= self.cap: self.d.popitem(last=False)     # bug: evicts even when updating
        self.d[key] = value
        self.d.move_to_end(key)
''',
    ],
    guide=dict(
        prereqs="Dictionaries and `collections.OrderedDict` (or a doubly linked list). The eviction section of the lesson *Caching patterns*.",
        intuition="You need two things at once: find a key instantly, and know which key was used least recently. A hash map gives the first; an ordering from oldest use to newest use gives the second. Every use moves the key to the 'newest' end, so the victim is always at the 'oldest' end.",
        hints=[
            "An `OrderedDict` remembers insertion order and can move a key to the end in O(1) with `move_to_end`.",
            "On `get`, move the key to the end before returning. On `put` of an existing key, also move it to the end and do not evict.",
            "Evict with `popitem(last=False)` only when the key is new and the cache is full. Handle capacity 0 separately.",
        ],
        brute_force="Store a last-used timestamp per key and scan all keys for the smallest when evicting: O(n) per eviction.",
        approach="""Hash map + recency order (an `OrderedDict` is exactly a hash map over a doubly linked list).

**Dry run (capacity 2):** `put(1,1)` → order [1]. `put(2,2)` → [1,2]. `get(1)` → moves 1: [2,1], returns 1. `put(3,3)`: full and 3 is new → evict the oldest, 2 → [1,3]. `get(2)` → -1.""",
        complexity="O(1) average time for `get` and `put`; O(capacity) space.",
        pitfalls="Not refreshing recency on `get`. Evicting when updating an existing key. Forgetting capacity 0. Real Redis approximates this by sampling a few keys instead of keeping a full ordering.",
        follow_up="Add a TTL per entry. Then implement the sampled version: evict the least recently used among 5 random keys and compare hit ratios.",
    ),
),
dict(
    id="redis-lfu-cache",
    title="LFU Eviction Cache",
    difficulty="Hard",
    pattern="Caching",
    leetcode="https://leetcode.com/problems/lfu-cache/",
    kind="class",
    entry="LFUCache",
    description=r"""
Redis's `allkeys-lfu` policy evicts the key that is used **least often**. Implement the exact policy.

- `LFUCache(capacity)` - `capacity >= 0`.
- `get(key)` - the value or `-1`. A successful `get` increases the key's use count by 1.
- `put(key, value)` - update an existing key (its use count increases by 1) or insert a new key with use
  count 1. Before inserting a new key into a full cache, evict the key with the **smallest use count**; if
  several share it, evict the **least recently used** among them. Capacity 0 stores nothing.

Aim for O(1) average time per operation.

**Example:** capacity 2: `put(1,1)`, `put(2,2)`, `get(1)` → `1`, `put(3,3)` evicts key 2 (count 1 against 2),
`get(2)` → `-1`, `get(3)` → `3`
""",
    starter='''class LFUCache:
    def __init__(self, capacity: int):
        pass

    def get(self, key: int) -> int:
        pass

    def put(self, key: int, value: int) -> None:
        pass
''',
    solution='''class LFUCache:
    def __init__(self, capacity):
        self.cap = capacity
        self.val, self.freq = {}, {}
        self.groups = collections.defaultdict(collections.OrderedDict)   # count -> keys, oldest first
        self.min_freq = 0

    def _touch(self, key):
        f = self.freq[key]
        del self.groups[f][key]
        if not self.groups[f]:
            del self.groups[f]
            if self.min_freq == f:
                self.min_freq = f + 1
        self.freq[key] = f + 1
        self.groups[f + 1][key] = True

    def get(self, key):
        if key not in self.val:
            return -1
        self._touch(key)
        return self.val[key]

    def put(self, key, value):
        if self.cap == 0:
            return None
        if key in self.val:
            self.val[key] = value
            self._touch(key)
            return None
        if len(self.val) >= self.cap:
            victim, _ = self.groups[self.min_freq].popitem(last=False)
            if not self.groups[self.min_freq]:
                del self.groups[self.min_freq]
            del self.val[victim]
            del self.freq[victim]
        self.val[key], self.freq[key] = value, 1
        self.groups[1][key] = True
        self.min_freq = 1
''',
    tests=[
        [["LFUCache", "put", "put", "get", "put", "get", "get", "put", "get", "get", "get"],
         [[2], [1, 1], [2, 2], [1], [3, 3], [2], [3], [4, 4], [1], [3], [4]]],
        [["LFUCache", "put", "get"], [[0], [1, 1], [1]]],
        [["LFUCache", "put", "put", "put", "get", "get"], [[2], [1, 1], [2, 2], [3, 3], [1], [2]]],
        [["LFUCache", "put", "put", "put", "put", "get", "get", "get"],
         [[2], [1, 1], [1, 5], [2, 2], [3, 3], [1], [2], [3]]],
        [["LFUCache", "put", "put", "get", "get", "get", "put", "put", "get", "get", "get"],
         [[2], [1, 1], [2, 2], [1], [1], [2], [3, 3], [4, 4], [1], [3], [4]]],
    ] + [_seq(s, 70, "LFUCache", [c], _cache_step) for s, c in [(11, 2), (12, 3), (13, 4), (14, 1), (15, 3), (16, 5)]],
    examples=2,
    wrong_solutions=[
        _LRU_OK.replace("class LRUCache", "class LFUCache") % "self.d.move_to_end(key)",
        '''class LFUCache:
    def __init__(self, capacity):
        self.cap, self.val, self.freq, self.clock, self.used = capacity, {}, {}, 0, {}
    def _touch(self, key):
        self.clock += 1; self.freq[key] = self.freq.get(key, 0) + 1; self.used[key] = self.clock
    def get(self, key):
        if key not in self.val: return -1
        self._touch(key); return self.val[key]
    def put(self, key, value):
        if self.cap == 0: return None
        if key not in self.val and len(self.val) >= self.cap:
            victim = min(self.val, key=lambda k: (self.freq[k], -self.used[k]))   # bug: ties evict the newest
            del self.val[victim]; del self.freq[victim]; del self.used[victim]
        self.val[key] = value; self._touch(key)
''',
    ],
    guide=dict(
        prereqs="The LRU cache problem. `collections.OrderedDict` and `defaultdict`.",
        intuition="Group keys by how many times they have been used. Within one group, keep them in order of last use. The victim is the oldest key in the group with the smallest count. Tracking that smallest count in a variable avoids searching for it.",
        hints=[
            "Keep three maps: key → value, key → count, and count → ordered collection of keys.",
            "When a key is used, move it from group `f` to group `f + 1`. If group `f` becomes empty and `f` was the minimum, the minimum becomes `f + 1`.",
            "A newly inserted key has count 1, so after any insertion the minimum count is 1.",
        ],
        brute_force="Keep a count and a last-used time per key; on eviction scan all keys for the smallest `(count, last_used)`. O(n) per eviction.",
        approach="""**Dry run (capacity 2):** `put(1,1)`, `put(2,2)` → group 1: [1,2], min 1. `get(1)` → key 1 moves to group 2; group 1: [2]. `put(3,3)`: full → evict the oldest key of group 1, which is 2; insert 3 with count 1. `get(2)` → -1. `get(3)` → 3 (count 2). `put(4,4)`: groups are {2: [1,3]}, min 2 → evict 1, the least recently used of the tied pair.""",
        complexity="O(1) average time per operation; O(capacity) space.",
        pitfalls="Breaking ties by evicting the most recently used key. Forgetting that updating a key with `put` counts as a use. Not resetting the minimum to 1 after an insertion. Redis's real LFU uses a small probabilistic counter that also decays over time.",
        follow_up="Add decay: halve all counts every N operations so that old popularity fades, as Redis does with `lfu-decay-time`.",
    ),
),
dict(
    id="redis-cache-aside-stampede",
    title="Cache-Aside with TTL and Stampede Protection",
    difficulty="Medium",
    pattern="Caching",
    kind="class",
    entry="CacheAside",
    description=r"""
Model the cache side of the cache-aside pattern with a rebuild lock, so that when an entry is missing only
**one** caller loads it from the database. Time is passed in as the integer `now` (never decreasing).

`CacheAside(ttl, lock_ttl)`:

- `read(key, now)` returns
  - `["hit", value]` if a cached value exists and `now < its expiry`;
  - otherwise `["load", token]` if no unexpired rebuild lock exists for the key: a lock is created that expires
    at `now + lock_ttl`, and `token` is a new integer (tokens are `1, 2, 3, ...` across the whole object);
  - otherwise `["wait"]` - someone else is rebuilding.
- `fill(key, token, value, now)` - the caller finished loading. If the key has a rebuild lock with exactly this
  token and `now <` the lock's expiry: store `value` with expiry `now + ttl`, remove the lock, return `True`.
  Otherwise change nothing and return `False`.
- `invalidate(key)` - remove the cached value (not the lock). Returns `1` if a value was stored (even an
  expired one), else `0`.

**Example:** `CacheAside(10, 5)`: `read("k",0)` → `["load",1]`, `read("k",1)` → `["wait"]`,
`fill("k",1,"v",2)` → `True`, `read("k",11)` → `["hit","v"]`, `read("k",12)` → `["load",2]`
""",
    starter='''class CacheAside:
    def __init__(self, ttl: int, lock_ttl: int):
        pass

    def read(self, key: str, now: int) -> list:
        pass

    def fill(self, key: str, token: int, value: str, now: int) -> bool:
        pass

    def invalidate(self, key: str) -> int:
        pass
''',
    solution='''class CacheAside:
    def __init__(self, ttl, lock_ttl):
        self.ttl, self.lock_ttl = ttl, lock_ttl
        self.values = {}     # key -> (value, expiry)
        self.locks = {}      # key -> (token, expiry)
        self.next_token = 1

    def read(self, key, now):
        if key in self.values and now < self.values[key][1]:
            return ["hit", self.values[key][0]]
        if key in self.locks and now < self.locks[key][1]:
            return ["wait"]
        token = self.next_token
        self.next_token += 1
        self.locks[key] = (token, now + self.lock_ttl)
        return ["load", token]

    def fill(self, key, token, value, now):
        lock = self.locks.get(key)
        if lock is None or lock[0] != token or now >= lock[1]:
            return False
        self.values[key] = (value, now + self.ttl)
        del self.locks[key]
        return True

    def invalidate(self, key):
        return 1 if self.values.pop(key, None) is not None else 0
''',
    tests=[
        [["CacheAside", "read", "read", "fill", "read", "read"],
         [[10, 5], ["k", 0], ["k", 1], ["k", 1, "v", 2], ["k", 11], ["k", 12]]],
        [["CacheAside", "fill", "invalidate", "read"], [[10, 5], ["k", 1, "v", 0], ["k"], ["k", 0]]],
        [["CacheAside", "read", "read", "read", "fill", "fill", "read"],
         [[10, 5], ["k", 0], ["k", 4], ["k", 5], ["k", 1, "old", 6], ["k", 2, "new", 6], ["k", 7]]],
        [["CacheAside", "read", "fill", "invalidate", "invalidate", "read", "read", "fill", "read"],
         [[10, 5], ["k", 0], ["k", 1, "a", 0], ["k"], ["k"], ["k", 1], ["k", 1], ["k", 2, "b", 3], ["k", 3]]],
        [["CacheAside", "read", "read", "fill", "fill", "read", "read"],
         [[3, 2], ["a", 0], ["b", 0], ["a", 2, "x", 1], ["b", 2, "y", 1], ["a", 1], ["b", 1]]],
        [["CacheAside", "read", "fill", "read", "read", "fill", "read"],
         [[3, 2], ["a", 0], ["a", 1, "x", 2], ["a", 2], ["a", 3], ["a", 2, "y", 4], ["a", 4]]],
    ] + [_seq(s, 45, "CacheAside", [6, 3], _aside_step) for s in range(21, 27)],
    examples=2,
    wrong_solutions=[
        '''class CacheAside:
    def __init__(self, ttl, lock_ttl):
        self.ttl, self.values, self.n = ttl, {}, 1
    def read(self, key, now):
        if key in self.values and now < self.values[key][1]: return ["hit", self.values[key][0]]
        t = self.n; self.n += 1
        return ["load", t]                       # bug: no lock, every miss loads (a stampede)
    def fill(self, key, token, value, now):
        self.values[key] = (value, now + self.ttl); return True
    def invalidate(self, key): return 1 if self.values.pop(key, None) is not None else 0
''',
        '''class CacheAside:
    def __init__(self, ttl, lock_ttl):
        self.ttl, self.lock_ttl, self.values, self.locks, self.n = ttl, lock_ttl, {}, {}, 1
    def read(self, key, now):
        if key in self.values and now < self.values[key][1]: return ["hit", self.values[key][0]]
        if key in self.locks and now < self.locks[key][1]: return ["wait"]
        t = self.n; self.n += 1; self.locks[key] = (t, now + self.lock_ttl)
        return ["load", t]
    def fill(self, key, token, value, now):
        if key not in self.locks: return False
        self.values[key] = (value, now + self.ttl)   # bug: token and lock expiry not checked
        del self.locks[key]; return True
    def invalidate(self, key): return 1 if self.values.pop(key, None) is not None else 0
''',
    ],
    guide=dict(
        prereqs="The lesson *Caching patterns* (cache-aside, cache stampede, rebuild lock) and the lock lessons (tokens).",
        intuition="A miss should cause exactly one database load. The first reader to miss takes a short lock and is told to load; everyone else is told to wait. The lock carries a token so that a slow loader whose lock has expired cannot overwrite the work of the loader that replaced it, and it carries an expiry so that a crashed loader cannot block the key for ever.",
        hints=[
            "Keep two dictionaries: cached values with their expiry, and rebuild locks with their token and expiry.",
            "`read` checks in this order: fresh value → hit; live lock → wait; otherwise create a lock and return load.",
            "`fill` succeeds only when the lock exists, its token equals the caller's, and `now` is strictly before the lock's expiry.",
        ],
        brute_force="No lock: every miss returns 'load'. It is simple and it is the stampede - a hundred concurrent misses mean a hundred identical database queries.",
        approach="""**Dry run, `CacheAside(10, 5)`:** `read("k",0)`: no value, no lock → lock (token 1, expires 5) → `["load",1]`. `read("k",1)`: lock live → `["wait"]`. `fill("k",1,"v",2)`: token matches, 2 < 5 → value stored until 12, lock removed → `True`. `read("k",11)` → hit. `read("k",12)`: 12 is not < 12, so the value has expired → new lock, `["load",2]`.""",
        complexity="O(1) time per call; O(keys) space.",
        pitfalls="Treating `now == expiry` as still valid. Accepting a `fill` from a stale token after the lock expired and another loader took over. Removing the lock in `invalidate`. Reusing tokens.",
        follow_up="Add stale-while-revalidate: keep serving the old value as a hit while one caller holds the lock and refreshes it.",
    ),
),
dict(
    id="redis-fixed-window-limiter",
    title="Fixed-Window Rate Limiter",
    difficulty="Easy",
    pattern="Rate limiting",
    kind="class",
    entry="FixedWindowLimiter",
    description=r"""
Implement the `INCR` + `EXPIRE` rate limiter. Time is divided into windows of `window` seconds; the window
containing time `now` has index `now // window`.

- `FixedWindowLimiter(limit, window)`
- `allow(user, now)` - return `True` and count the request if the user has made fewer than `limit` **allowed**
  requests in the current window; otherwise return `False` (a rejected request is not counted). Each user is
  limited independently. `now` is an integer and never decreases.

**Example:** `FixedWindowLimiter(2, 10)`: `allow("ana",8)` → `True`, `allow("ana",9)` → `True`,
`allow("ana",9)` → `False`, `allow("ana",10)` → `True` (a new window began)
""",
    starter='''class FixedWindowLimiter:
    def __init__(self, limit: int, window: int):
        pass

    def allow(self, user: str, now: int) -> bool:
        pass
''',
    solution='''class FixedWindowLimiter:
    def __init__(self, limit, window):
        self.limit, self.window = limit, window
        self.counts = {}        # user -> (window index, count)

    def allow(self, user, now):
        w = now // self.window
        index, count = self.counts.get(user, (w, 0))
        if index != w:
            count = 0
        if count >= self.limit:
            self.counts[user] = (w, count)
            return False
        self.counts[user] = (w, count + 1)
        return True
''',
    tests=[
        [["FixedWindowLimiter", "allow", "allow", "allow", "allow"], [[2, 10], ["ana", 8], ["ana", 9], ["ana", 9], ["ana", 10]]],
        [["FixedWindowLimiter", "allow", "allow", "allow"], [[0, 5], ["ana", 0], ["ana", 5], ["raj", 5]]],
        [["FixedWindowLimiter", "allow", "allow", "allow", "allow", "allow"],
         [[1, 60], ["ana", 0], ["raj", 0], ["ana", 59], ["raj", 59], ["ana", 60]]],
        [["FixedWindowLimiter", "allow", "allow", "allow", "allow", "allow", "allow"],
         [[3, 1], ["a", 0], ["a", 0], ["a", 0], ["a", 0], ["a", 1], ["a", 1]]],
        [["FixedWindowLimiter", "allow", "allow", "allow", "allow", "allow", "allow", "allow"],
         [[2, 10], ["a", 9], ["a", 9], ["a", 10], ["a", 10], ["a", 10], ["a", 35], ["a", 39]]],
    ] + [_seq(s, 50, "FixedWindowLimiter", list(c), _limit_step) for s, c in
         [(31, (2, 5)), (32, (3, 10)), (33, (1, 3)), (34, (4, 7)), (35, (2, 2)), (36, (5, 20))]],
    examples=2,
    wrong_solutions=[
        '''class FixedWindowLimiter:
    def __init__(self, limit, window):
        self.limit, self.window, self.log = limit, window, {}
    def allow(self, user, now):                  # bug: sliding window, not fixed windows
        log = [t for t in self.log.get(user, []) if t > now - self.window]
        ok = len(log) < self.limit
        if ok: log.append(now)
        self.log[user] = log
        return ok
''',
        '''class FixedWindowLimiter:
    def __init__(self, limit, window):
        self.limit, self.window, self.counts = limit, window, {}
    def allow(self, user, now):
        w = now // self.window                   # bug: one counter shared by all users
        self.counts[w] = self.counts.get(w, 0) + 1
        return self.counts[w] <= self.limit
''',
    ],
    guide=dict(
        prereqs="Integer division. The rate-limiter section of *Redis interview essentials*.",
        intuition="All timestamps in the same window share the same value of `now // window`. So the limiter is one counter per user per window index; when the index changes, the counter starts again from zero. In Redis the window index is part of the key name and `EXPIRE` removes old windows.",
        hints=[
            "Compute `w = now // window`.",
            "Store, per user, the window index the counter belongs to and the count. If the stored index differs from `w`, reset the count.",
            "Only increase the count when the request is allowed.",
        ],
        brute_force="Keep every request timestamp per user and count those with the same window index on each call: O(requests) time and memory.",
        approach="""**Dry run, limit 2, window 10:** `allow("ana",8)`: w=0, count 0 → allow, count 1. `allow("ana",9)`: count 1 → allow, count 2. `allow("ana",9)`: count 2 ≥ 2 → reject. `allow("ana",10)`: w=1 ≠ 0 → reset → allow. Note the weakness: two requests at second 9 and two more at second 10 all pass - four in two seconds.""",
        complexity="O(1) time per call, O(users) space.",
        pitfalls="Counting rejected requests (harmless here, different in other definitions). Sharing one counter between users. Implementing a sliding window by mistake. Forgetting that a limit of 0 rejects everything.",
        follow_up="Implement the sliding-window *counter*: weight the previous window's count by how much of it still overlaps the last `window` seconds.",
    ),
),
dict(
    id="redis-sliding-log-limiter",
    title="Sliding-Window-Log Rate Limiter",
    difficulty="Medium",
    pattern="Rate limiting",
    kind="class",
    entry="SlidingLogLimiter",
    description=r"""
Implement the exact sliding-window limiter that Redis builds from a sorted set of request timestamps
(`ZREMRANGEBYSCORE`, `ZCARD`, `ZADD`).

- `SlidingLogLimiter(limit, window)`
- `allow(user, now)`:
  1. forget this user's recorded requests with timestamp `<= now - window`;
  2. if fewer than `limit` remain, record `now` and return `True`;
  3. otherwise return `False` (a rejected request is **not** recorded).

`now` is an integer and never decreases. Users are independent.

**Example:** `SlidingLogLimiter(2, 10)`: `allow("ana",8)` → `True`, `allow("ana",9)` → `True`,
`allow("ana",10)` → `False`, `allow("ana",18)` → `True` (the request at 8 has left the window), `allow("ana",18)` → `False`
""",
    starter='''class SlidingLogLimiter:
    def __init__(self, limit: int, window: int):
        pass

    def allow(self, user: str, now: int) -> bool:
        pass
''',
    solution='''class SlidingLogLimiter:
    def __init__(self, limit, window):
        self.limit, self.window = limit, window
        self.log = collections.defaultdict(collections.deque)

    def allow(self, user, now):
        q = self.log[user]
        while q and q[0] <= now - self.window:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(now)
        return True
''',
    tests=[
        [["SlidingLogLimiter", "allow", "allow", "allow", "allow", "allow"],
         [[2, 10], ["ana", 8], ["ana", 9], ["ana", 10], ["ana", 18], ["ana", 18]]],
        [["SlidingLogLimiter", "allow", "allow"], [[0, 5], ["ana", 0], ["ana", 100]]],
        [["SlidingLogLimiter", "allow", "allow", "allow", "allow", "allow"],
         [[1, 5], ["a", 0], ["b", 0], ["a", 4], ["a", 5], ["b", 5]]],
        [["SlidingLogLimiter", "allow", "allow", "allow", "allow", "allow", "allow", "allow"],
         [[3, 4], ["a", 0], ["a", 1], ["a", 2], ["a", 3], ["a", 4], ["a", 4], ["a", 5]]],
        [["SlidingLogLimiter", "allow", "allow", "allow", "allow", "allow", "allow"],
         [[2, 10], ["a", 0], ["a", 5], ["a", 7], ["a", 9], ["a", 10], ["a", 15]]],
    ] + [_seq(s, 50, "SlidingLogLimiter", list(c), _limit_step) for s, c in
         [(41, (2, 5)), (42, (3, 10)), (43, (1, 3)), (44, (4, 7)), (45, (2, 2)), (46, (5, 20))]],
    examples=2,
    wrong_solutions=[
        '''class SlidingLogLimiter:
    def __init__(self, limit, window):
        self.limit, self.window, self.counts = limit, window, {}
    def allow(self, user, now):                   # bug: fixed windows
        k = (user, now // self.window)
        if self.counts.get(k, 0) >= self.limit: return False
        self.counts[k] = self.counts.get(k, 0) + 1
        return True
''',
        '''class SlidingLogLimiter:
    def __init__(self, limit, window):
        self.limit, self.window, self.log = limit, window, {}
    def allow(self, user, now):
        q = [t for t in self.log.get(user, []) if t > now - self.window]
        q.append(now)                              # bug: rejected requests are recorded too
        self.log[user] = q
        return len(q) <= self.limit
''',
    ],
    guide=dict(
        prereqs="`collections.deque`. The sliding-window-log section of *Redis interview essentials*.",
        intuition="Instead of counting per clock-aligned window, remember *when* each allowed request happened. The requests that matter are those in the last `window` seconds measured from now, so drop older ones and count the rest. Because time only moves forward, the old ones are always at the front of the log.",
        hints=[
            "Keep a deque of timestamps per user, oldest on the left.",
            "Before deciding, pop from the left while the timestamp is `<= now - window`.",
            "Append `now` only if the request is allowed.",
        ],
        brute_force="Keep a plain list and rebuild it with a filter on every call: O(limit) per call. The deque version is O(1) amortised.",
        approach="""**Dry run, limit 2, window 10:** t=8 → log [8], allow. t=9 → [8,9], allow. t=10: cutoff 0, nothing leaves; 2 entries → reject. t=18: cutoff 8, so 8 leaves → [9] → allow → [9,18]. t=18 again → 2 entries → reject. Compare with the fixed window, which would have allowed the request at t=10.""",
        complexity="O(1) amortised time per call (each timestamp is appended and removed once). Space O(limit) per active user - the cost of exactness.",
        pitfalls="Using `<` for the cutoff (a request exactly `window` seconds old has left the window). Recording rejected requests, which lets a flood of rejected calls keep the user blocked for ever. Sharing a log across users.",
        follow_up="In Redis the three steps must run atomically; write them as one Lua script. What unique member would you use in the sorted set when two requests share a timestamp?",
    ),
),
dict(
    id="redis-token-bucket",
    title="Token-Bucket Rate Limiter",
    difficulty="Medium",
    pattern="Rate limiting",
    kind="class",
    entry="TokenBucket",
    description=r"""
Implement the token bucket that is usually written as a Lua script over a Redis hash holding two fields,
`tokens` and `stamp`.

- `TokenBucket(capacity, refill_per_second)` - both positive integers. Every user has a separate bucket that
  starts **full** the first time the user is seen.
- `allow(user, now, cost)` - `now` is an integer number of seconds (never decreasing), `cost >= 1`:
  1. refill: `tokens = min(capacity, tokens + (now - stamp) * refill_per_second)`, then `stamp = now`;
  2. if `tokens >= cost`: subtract `cost` and return `True`; otherwise return `False` and leave the tokens.

**Example:** `TokenBucket(3, 1)`: `allow("a",0,1)` ×3 → `True, True, True`; `allow("a",0,1)` → `False`;
`allow("a",2,2)` → `True` (2 tokens refilled); `allow("a",100,4)` → `False` (the bucket never holds more than 3)
""",
    starter='''class TokenBucket:
    def __init__(self, capacity: int, refill_per_second: int):
        pass

    def allow(self, user: str, now: int, cost: int) -> bool:
        pass
''',
    solution='''class TokenBucket:
    def __init__(self, capacity, refill_per_second):
        self.capacity, self.rate = capacity, refill_per_second
        self.state = {}      # user -> [tokens, stamp]

    def allow(self, user, now, cost):
        if user not in self.state:
            self.state[user] = [self.capacity, now]
        bucket = self.state[user]
        bucket[0] = min(self.capacity, bucket[0] + (now - bucket[1]) * self.rate)
        bucket[1] = now
        if bucket[0] >= cost:
            bucket[0] -= cost
            return True
        return False
''',
    tests=[
        [["TokenBucket", "allow", "allow", "allow", "allow", "allow", "allow"],
         [[3, 1], ["a", 0, 1], ["a", 0, 1], ["a", 0, 1], ["a", 0, 1], ["a", 2, 2], ["a", 100, 4]]],
        [["TokenBucket", "allow", "allow", "allow"], [[1, 1], ["a", 5, 2], ["a", 5, 1], ["a", 5, 1]]],
        [["TokenBucket", "allow", "allow", "allow", "allow"], [[2, 1], ["a", 0, 2], ["b", 0, 2], ["a", 1, 1], ["b", 1, 2]]],
        [["TokenBucket", "allow", "allow", "allow", "allow", "allow"],
         [[10, 3], ["a", 0, 10], ["a", 1, 4], ["a", 1, 3], ["a", 2, 3], ["a", 2, 1]]],
        [["TokenBucket", "allow", "allow", "allow", "allow", "allow"],
         [[5, 2], ["a", 0, 5], ["a", 1, 3], ["a", 1, 2], ["a", 50, 5], ["a", 50, 1]]],
    ] + [_seq(s, 50, "TokenBucket", list(c), _bucket_step) for s, c in
         [(51, (3, 1)), (52, (5, 2)), (53, (2, 1)), (54, (6, 1)), (55, (4, 3)), (56, (1, 1))]],
    examples=2,
    wrong_solutions=[
        '''class TokenBucket:
    def __init__(self, capacity, refill_per_second):
        self.capacity, self.rate, self.state = capacity, refill_per_second, {}
    def allow(self, user, now, cost):
        if user not in self.state: self.state[user] = [self.capacity, now]
        b = self.state[user]
        b[0] = b[0] + (now - b[1]) * self.rate          # bug: no cap at capacity
        b[1] = now
        if b[0] >= cost: b[0] -= cost; return True
        return False
''',
        '''class TokenBucket:
    def __init__(self, capacity, refill_per_second):
        self.capacity, self.rate, self.state = capacity, refill_per_second, {}
    def allow(self, user, now, cost):
        if user not in self.state: self.state[user] = [self.capacity, now]
        b = self.state[user]
        if b[0] >= cost:                                # bug: refills only after a rejection
            b[0] -= cost; return True
        b[0] = min(self.capacity, b[0] + (now - b[1]) * self.rate); b[1] = now
        return False
''',
    ],
    guide=dict(
        prereqs="The token-bucket sections of *Lua scripting: rewriting locks, semaphores and transactions* and *Redis interview essentials*.",
        intuition="You do not need a timer that adds tokens every second. It is enough to remember how many tokens there were and when you last looked; on the next request, add the tokens that *would* have dripped in since then, capped at the bucket's capacity. This 'compute on demand' trick is why two stored numbers are enough.",
        hints=[
            "Per user, store `tokens` and `stamp` (the time of the last update).",
            "First refill - `min(capacity, tokens + elapsed * rate)` - and set `stamp = now`. Do this on every call, allowed or not.",
            "Then compare with `cost`. Only subtract when the request is allowed.",
        ],
        brute_force="Simulate every second between calls, adding `rate` tokens each time: O(elapsed seconds) per call.",
        approach="""**Dry run, capacity 3, rate 1:** three calls at t=0 with cost 1 take the tokens 3→2→1→0. A fourth at t=0: 0 < 1 → reject. At t=2 with cost 2: refill 0 + 2×1 = 2 → allow → 0. At t=100 with cost 4: refill min(3, 0 + 98) = 3 → 3 < 4 → reject, tokens stay 3.""",
        complexity="O(1) time per call; O(users) space.",
        pitfalls="Forgetting the cap, which lets an idle user save up an unlimited burst. Not updating `stamp` on rejected calls, which double-counts elapsed time later. Starting new buckets empty. In Redis, doing the read and the write as separate commands - it must be one script.",
        follow_up="Use fractional refill rates (0.5 tokens per second). What must you store as a string in Lua to avoid truncation?",
    ),
),
dict(
    id="redis-leaderboard",
    title="Leaderboard with Rank Queries",
    difficulty="Medium",
    pattern="Sorted sets",
    kind="class",
    entry="Leaderboard",
    description=r"""
Build the leaderboard that a Redis sorted set provides with `ZINCRBY`, `ZRANGE ... REV`, `ZREVRANK` and `ZREM`.

Players are ranked by **total score descending; players with equal scores by name ascending**. Ranks are
**1-based**.

- `add_score(player, points)` - add `points` (a positive integer) to the player's total, creating the player
  at 0 if needed. Returns the new total.
- `top(n)` - the first `n` players as `[name, score]` pairs (fewer if there are fewer players).
- `rank(player)` - the player's rank, or `None` if unknown.
- `around(player, radius)` - `[rank, name, score]` rows for the player and up to `radius` players on each side,
  in ranking order; `[]` if the player is unknown.
- `remove(player)` - returns `1` if the player existed, else `0`.

**Example:** `add_score("bo",10)`, `add_score("ada",10)`, `add_score("cy",30)` → `top(2)` is
`[["cy",30],["ada",10]]`, `rank("bo")` → `3`, `around("ada",1)` → `[[1,"cy",30],[2,"ada",10],[3,"bo",10]]`
""",
    starter='''class Leaderboard:
    def __init__(self):
        pass

    def add_score(self, player: str, points: int) -> int:
        pass

    def top(self, n: int) -> List[list]:
        pass

    def rank(self, player: str):
        pass

    def around(self, player: str, radius: int) -> List[list]:
        pass

    def remove(self, player: str) -> int:
        pass
''',
    solution='''class Leaderboard:
    def __init__(self):
        self.score = {}
        self.order = []          # sorted list of (-score, name)

    def _drop(self, player):
        i = bisect.bisect_left(self.order, (-self.score[player], player))
        self.order.pop(i)

    def add_score(self, player, points):
        if player in self.score:
            self._drop(player)
        self.score[player] = self.score.get(player, 0) + points
        bisect.insort(self.order, (-self.score[player], player))
        return self.score[player]

    def top(self, n):
        return [[name, -neg] for neg, name in self.order[:n]]

    def rank(self, player):
        if player not in self.score:
            return None
        return bisect.bisect_left(self.order, (-self.score[player], player)) + 1

    def around(self, player, radius):
        r = self.rank(player)
        if r is None:
            return []
        start = max(0, r - 1 - radius)
        rows = self.order[start:r + radius]
        return [[start + i + 1, name, -neg] for i, (neg, name) in enumerate(rows)]

    def remove(self, player):
        if player not in self.score:
            return 0
        self._drop(player)
        del self.score[player]
        return 1
''',
    tests=[
        [["Leaderboard", "add_score", "add_score", "add_score", "top", "rank", "around"],
         [[], ["bo", 10], ["ada", 10], ["cy", 30], [2], ["bo"], ["ada", 1]]],
        [["Leaderboard", "top", "rank", "around", "remove"], [[], [3], ["x"], ["x", 2], ["x"]]],
        [["Leaderboard", "add_score", "add_score", "add_score", "rank", "rank", "top"],
         [[], ["a", 5], ["b", 5], ["a", 1], ["a"], ["b"], [10]]],
        [["Leaderboard", "add_score", "add_score", "add_score", "add_score", "around", "around", "around"],
         [[], ["a", 40], ["b", 30], ["c", 20], ["d", 10], ["a", 1], ["d", 2], ["c", 0]]],
        [["Leaderboard", "add_score", "add_score", "remove", "remove", "rank", "top", "add_score", "top"],
         [[], ["a", 7], ["b", 9], ["b"], ["b"], ["a"], [5], ["b", 1], [5]]],
        [["Leaderboard", "add_score", "add_score", "add_score", "top", "top", "around"],
         [[], ["zed", 3], ["amy", 3], ["moe", 3], [0], [2], ["moe", 5]]],
    ] + [_seq(s, 45, "Leaderboard", [], _board_step) for s in range(61, 67)],
    examples=2,
    wrong_solutions=[
        '''class Leaderboard:
    def __init__(self): self.score = {}
    def _order(self): return sorted(self.score, key=lambda p: -self.score[p])      # bug: ties not by name
    def add_score(self, player, points):
        self.score[player] = self.score.get(player, 0) + points; return self.score[player]
    def top(self, n): return [[p, self.score[p]] for p in self._order()[:n]]
    def rank(self, player): return self._order().index(player) + 1 if player in self.score else None
    def around(self, player, radius):
        r = self.rank(player)
        if r is None: return []
        o = self._order(); start = max(0, r - 1 - radius)
        return [[start + i + 1, p, self.score[p]] for i, p in enumerate(o[start:r + radius])]
    def remove(self, player): return 1 if self.score.pop(player, None) is not None else 0
''',
        '''class Leaderboard:
    def __init__(self): self.score = {}
    def _order(self): return sorted(self.score, key=lambda p: (-self.score[p], p))
    def add_score(self, player, points):
        self.score[player] = self.score.get(player, 0) + points; return self.score[player]
    def top(self, n): return [[p, self.score[p]] for p in self._order()[:n]]
    def rank(self, player): return self._order().index(player) if player in self.score else None   # bug: 0-based
    def around(self, player, radius):
        r = self.rank(player)
        if r is None: return []
        o = self._order(); start = max(0, r - radius)
        return [[start + i, p, self.score[p]] for i, p in enumerate(o[start:r + radius + 1])]
    def remove(self, player): return 1 if self.score.pop(player, None) is not None else 0
''',
    ],
    guide=dict(
        prereqs="The sorted-set problem in this track and `bisect`. The leaderboard section of *Redis interview essentials*.",
        intuition="A leaderboard is a sorted set read from the high end. Store `(-score, name)` tuples in a sorted list: negating the score puts the best player first, and the name breaks ties in ascending order automatically. A player's rank is then the position of their tuple, found by binary search.",
        hints=[
            "Keep a dictionary of totals and a sorted list of `(-total, name)`.",
            "To change a total: remove the old tuple (find it with `bisect_left`), update, insert the new tuple with `insort`.",
            "`around` is a slice: from `rank - 1 - radius` (not below 0) to `rank + radius`, numbering rows from the slice start + 1.",
        ],
        brute_force="Sort all players on every query: O(n log n) per `top` or `rank`.",
        approach="""**Dry run:** add bo 10 → [(-10,bo)]. add ada 10 → [(-10,ada),(-10,bo)]. add cy 30 → [(-30,cy),(-10,ada),(-10,bo)]. `top(2)` → cy, ada. `rank("bo")` → index 2 → 3. `around("ada",1)`: rank 2, start = max(0, 2-1-1) = 0, slice [0:3] → ranks 1, 2, 3.""",
        complexity="`rank` and `top(n)` are O(log n) and O(n requested). Updates are O(n) with a Python list; Redis's skip list makes them O(log n).",
        pitfalls="Returning 0-based ranks. Sorting ties by insertion order or by name descending. Leaving the old tuple in the list after a score change. Letting `around` produce a negative slice start, which wraps to the end of the list in Python.",
        follow_up="Break ties by who reached the score first by packing a timestamp into the score. Support weekly boards merged with `ZUNIONSTORE`.",
    ),
),
]
