"""Redis track problems 1-6: the core data types and transactions, as small simulations."""
import random as _r


def _seq(seed, n, ctor, ctor_args, step):
    """Build one [ops, args] test: constructor first, then n random steps from step(rng, state)."""
    rng, state = _r.Random(seed), {"now": 0}
    ops, args = [ctor], [list(ctor_args)]
    for _ in range(n):
        op, a = step(rng, state)
        ops.append(op)
        args.append(a)
    return [ops, args]


def _store_step(rng, st):
    st["now"] += rng.choice([0, 1, 1, 2, 5])
    k, now = rng.choice("abc"), st["now"]
    op = rng.choice(["set", "get", "get", "expire", "ttl", "ttl", "incr", "persist"])
    if op == "set":
        return op, [k, rng.choice(["3", "7", "40"]), now]
    if op == "expire":
        return op, [k, rng.choice([1, 3, 10]), now]
    return op, [k, now]


def _list_step(rng, st):
    op = rng.choice(["lpush", "rpush", "lpop", "rpop", "lrange", "lrange", "llen", "ltrim"])
    if op in ("lpush", "rpush"):
        return op, [[rng.randint(0, 9) for _ in range(rng.randint(1, 3))]]
    if op in ("lrange", "ltrim"):
        return op, [rng.randint(-6, 5), rng.randint(-6, 6)]
    return op, []


def _hash_step(rng, st):
    f = rng.choice(["a", "b", "c", "n"])
    op = rng.choice(["hset", "hset", "hget", "hdel", "hincrby", "hexists", "hlen", "hgetall", "hsetnx"])
    if op in ("hset", "hsetnx"):
        return op, [f, rng.choice(["2", "9", "5"]) if f == "n" else rng.choice(["x", "y", "5"])]
    if op == "hincrby":
        return op, ["n", rng.randint(-3, 5)]
    if op in ("hlen", "hgetall"):
        return op, []
    return op, [f]


def _set_step(rng, st):
    keys = ["s1", "s2", "s3", "nope"]
    op = rng.choice(["sadd", "sadd", "srem", "sismember", "scard", "sinter", "sunion", "sdiff", "sdiff"])
    if op in ("sadd", "srem"):
        return op, [rng.choice(keys[:3]), [rng.randint(1, 6) for _ in range(rng.randint(1, 3))]]
    if op == "sismember":
        return op, [rng.choice(keys), rng.randint(1, 6)]
    if op == "scard":
        return op, [rng.choice(keys)]
    return op, [rng.sample(keys, rng.randint(1, 3))]


def _zset_step(rng, st):
    m = rng.choice(["ann", "bob", "cat", "dan", "eve"])
    op = rng.choice(["zadd", "zadd", "zadd", "zscore", "zrank", "zrange", "zrangebyscore", "zrem", "zincrby", "zcard"])
    if op == "zadd":
        return op, [m, rng.randint(0, 4)]
    if op == "zincrby":
        return op, [m, rng.randint(-2, 2)]
    if op == "zrange":
        return op, [rng.randint(-5, 3), rng.randint(-5, 5)]
    if op == "zrangebyscore":
        lo = rng.randint(-1, 4)
        return op, [lo, lo + rng.randint(0, 3)]
    if op == "zcard":
        return op, []
    return op, [m]


def _tx_step(rng, st):
    c, k = rng.choice([1, 2]), rng.choice(["x", "y"])
    op = rng.choice(["get", "set", "set", "incr", "watch", "multi", "exec", "exec", "discard"])
    if op == "set":
        return op, [c, k, rng.choice([1, 2, 5])]
    if op == "watch":
        return op, [c, rng.sample(["x", "y"], rng.randint(1, 2))]
    if op in ("multi", "exec", "discard"):
        return op, [c]
    return op, [c, k]


PROBLEMS = [
dict(
    id="redis-expiring-store",
    title="String Store with EXPIRE and TTL",
    difficulty="Medium",
    pattern="Redis data types",
    kind="class",
    entry="ExpiringStore",
    description=r"""
Build a tiny model of Redis string keys with expiry. There is no real clock: every method receives the
current time `now` as an integer number of seconds, and `now` never decreases between calls.

A key that has a deadline `d` is **gone** as soon as `now >= d` (treat it exactly as if it had been deleted).

- `set(key, value, now)` - store the string `value`. **Removes any existing deadline.** Returns `"OK"`.
- `get(key, now)` - the value, or `None` if the key is missing or gone.
- `expire(key, seconds, now)` - set the deadline to `now + seconds`. Returns `1` if the key exists, else `0`.
- `ttl(key, now)` - `-2` if the key is missing, `-1` if it has no deadline, otherwise `deadline - now`.
- `incr(key, now)` - add 1 to the integer stored in the key (a missing key counts as 0) and return the new
  integer. The value is stored as a string. **Keeps the existing deadline.** Inputs are always valid integers.
- `persist(key, now)` - remove the deadline. Returns `1` if a deadline was removed, else `0`.

**Example:** `set("a","x",0)`, `expire("a",10,0)`, `ttl("a",4)` → `6`, `get("a",10)` → `None`, `ttl("a",10)` → `-2`
""",
    starter='''class ExpiringStore:
    def __init__(self):
        pass

    def set(self, key: str, value: str, now: int) -> str:
        pass

    def get(self, key: str, now: int):
        pass

    def expire(self, key: str, seconds: int, now: int) -> int:
        pass

    def ttl(self, key: str, now: int) -> int:
        pass

    def incr(self, key: str, now: int) -> int:
        pass

    def persist(self, key: str, now: int) -> int:
        pass
''',
    solution='''class ExpiringStore:
    def __init__(self):
        self.data = {}
        self.deadline = {}

    def _alive(self, key, now):
        if key in self.deadline and now >= self.deadline[key]:
            del self.data[key]
            del self.deadline[key]
        return key in self.data

    def set(self, key, value, now):
        self.data[key] = value
        self.deadline.pop(key, None)
        return "OK"

    def get(self, key, now):
        return self.data[key] if self._alive(key, now) else None

    def expire(self, key, seconds, now):
        if not self._alive(key, now):
            return 0
        self.deadline[key] = now + seconds
        return 1

    def ttl(self, key, now):
        if not self._alive(key, now):
            return -2
        if key not in self.deadline:
            return -1
        return self.deadline[key] - now

    def incr(self, key, now):
        n = int(self.data[key]) + 1 if self._alive(key, now) else 1
        self.data[key] = str(n)
        return n

    def persist(self, key, now):
        if self._alive(key, now) and key in self.deadline:
            del self.deadline[key]
            return 1
        return 0
''',
    tests=[
        [["ExpiringStore", "set", "expire", "ttl", "get", "get", "ttl"],
         [[], ["a", "x", 0], ["a", 10, 0], ["a", 4], ["a", 9], ["a", 10], ["a", 10]]],
        [["ExpiringStore", "ttl", "get", "expire", "persist"], [[], ["a", 0], ["a", 0], ["a", 5, 0], ["a", 0]]],
        [["ExpiringStore", "set", "expire", "set", "ttl", "get"],
         [[], ["k", "v", 0], ["k", 5, 0], ["k", "w", 2], ["k", 3], ["k", 100]]],
        [["ExpiringStore", "incr", "incr", "expire", "incr", "ttl", "get", "incr", "ttl"],
         [[], ["c", 0], ["c", 1], ["c", 10, 1], ["c", 5], ["c", 5], ["c", 5], ["c", 11], ["c", 11]]],
        [["ExpiringStore", "set", "expire", "persist", "persist", "ttl", "get"],
         [[], ["p", "1", 0], ["p", 3, 0], ["p", 1], ["p", 1], ["p", 50], ["p", 50]]],
        [["ExpiringStore", "set", "expire", "expire", "ttl", "expire", "get"],
         [[], ["a", "x", 0], ["a", 5, 0], ["a", 20, 3], ["a", 6], ["a", 0, 7], ["a", 7]]],
    ] + [_seq(s, 40, "ExpiringStore", [], _store_step) for s in range(1, 8)],
    examples=2,
    wrong_solutions=[
        '''class ExpiringStore:
    def __init__(self):
        self.data, self.deadline = {}, {}
    def _alive(self, key, now):
        if key in self.deadline and now >= self.deadline[key]:
            del self.data[key]; del self.deadline[key]
        return key in self.data
    def set(self, key, value, now):
        self.data[key] = value          # bug: keeps the old deadline
        return "OK"
    def get(self, key, now):
        return self.data[key] if self._alive(key, now) else None
    def expire(self, key, seconds, now):
        if not self._alive(key, now): return 0
        self.deadline[key] = now + seconds; return 1
    def ttl(self, key, now):
        if not self._alive(key, now): return -2
        return self.deadline[key] - now if key in self.deadline else -1
    def incr(self, key, now):
        n = int(self.data[key]) + 1 if self._alive(key, now) else 1
        self.data[key] = str(n); return n
    def persist(self, key, now):
        if self._alive(key, now) and key in self.deadline:
            del self.deadline[key]; return 1
        return 0
''',
        '''class ExpiringStore:
    def __init__(self):
        self.data, self.deadline = {}, {}
    def _alive(self, key, now):
        if key in self.deadline and now > self.deadline[key]:      # bug: off by one
            del self.data[key]; del self.deadline[key]
        return key in self.data
    def set(self, key, value, now):
        self.data[key] = value; self.deadline.pop(key, None); return "OK"
    def get(self, key, now):
        return self.data[key] if self._alive(key, now) else None
    def expire(self, key, seconds, now):
        if not self._alive(key, now): return 0
        self.deadline[key] = now + seconds; return 1
    def ttl(self, key, now):
        if not self._alive(key, now): return -2
        return self.deadline[key] - now if key in self.deadline else -1
    def incr(self, key, now):
        n = int(self.data[key]) + 1 if self._alive(key, now) else 1
        self.data[key] = str(n); return n
    def persist(self, key, now):
        if self._alive(key, now) and key in self.deadline:
            del self.deadline[key]; return 1
        return 0
''',
    ],
    guide=dict(
        prereqs="Python dictionaries. The lesson *Commands in depth: publish/subscribe, sorting, transactions and key expiry* (the TTL rules: -1, -2, what clears a timer).",
        intuition="Keep two dictionaries: one for values and one for deadlines. Nothing has to happen at the moment a key expires - check the deadline **lazily**, at the start of every operation that touches the key, and delete the key then. This is how Redis itself guarantees you never read an expired value.",
        hints=[
            "Write one helper, `_alive(key, now)`, that deletes the key if its deadline has passed and returns whether the key exists. Call it first in every method.",
            "Which operations change the deadline? `set` removes it, `expire` sets it, `persist` removes it, `incr` leaves it alone.",
            "A key with deadline `d` is gone when `now >= d`, so a `ttl` of 0 is never returned: at that moment the key no longer exists and the answer is -2.",
        ],
        brute_force="Sweep every key and delete the expired ones at the start of each call. It is correct but costs O(number of keys) per operation.",
        approach="""1. `data[key]` holds the string value, `deadline[key]` exists only for keys with a timer.
2. `_alive` removes a key whose deadline has been reached.
3. Each method calls `_alive` first, then does its small job.

**Dry run:** `set("a","x",0)`; `expire("a",10,0)` sets deadline 10 and returns 1. `ttl("a",4)` → 10 - 4 = 6. `get("a",9)` → `"x"`. `get("a",10)`: 10 >= 10, so the key is deleted → `None`. `ttl("a",10)` → -2.""",
        complexity="Every operation is O(1) time: a constant number of dictionary lookups. Space is O(number of live keys).",
        pitfalls="Using `>` instead of `>=` for expiry. Forgetting that `set` clears the deadline while `incr` keeps it. Returning 0 or -1 for a key that has expired (it must be -2). Storing an `int` in `incr` so that `get` returns a number instead of a string.",
        follow_up="Add `set(key, value, now, nx=True)` and you have the building block of a distributed lock. How would you add Redis's *active* expiry (sampling keys with deadlines)?",
    ),
),
dict(
    id="redis-list-commands",
    title="LPUSH, RPUSH, LPOP and LRANGE",
    difficulty="Easy",
    pattern="Redis data types",
    kind="class",
    entry="MiniList",
    description=r"""
Model a single Redis list of integers.

- `lpush(values)` - push each value of the list `values` onto the **head**, one after another, so the last
  value given ends up first. Returns the new length.
- `rpush(values)` - append each value at the **tail**, in order. Returns the new length.
- `lpop()` / `rpop()` - remove and return the first / last element, or `None` if the list is empty.
- `llen()` - the length.
- `lrange(start, stop)` - the elements from index `start` to index `stop`, **both inclusive**. Negative
  indices count from the end (`-1` is the last element). Out-of-range indices are clamped to the ends. If,
  after that, `start` is after `stop` or beyond the end, return `[]`.
- `ltrim(start, stop)` - keep only the range that `lrange(start, stop)` would return. Returns `"OK"`.

**Example:** `lpush([1,2,3])` → `3` and the list is `[3,2,1]`; `rpush([4])` → `4`; `lrange(0,-1)` → `[3,2,1,4]`;
`lrange(-2,10)` → `[1,4]`; `lrange(3,1)` → `[]`
""",
    starter='''class MiniList:
    def __init__(self):
        pass

    def lpush(self, values: List[int]) -> int:
        pass

    def rpush(self, values: List[int]) -> int:
        pass

    def lpop(self):
        pass

    def rpop(self):
        pass

    def llen(self) -> int:
        pass

    def lrange(self, start: int, stop: int) -> List[int]:
        pass

    def ltrim(self, start: int, stop: int) -> str:
        pass
''',
    solution='''class MiniList:
    def __init__(self):
        self.items = collections.deque()

    def lpush(self, values):
        for v in values:
            self.items.appendleft(v)
        return len(self.items)

    def rpush(self, values):
        self.items.extend(values)
        return len(self.items)

    def lpop(self):
        return self.items.popleft() if self.items else None

    def rpop(self):
        return self.items.pop() if self.items else None

    def llen(self):
        return len(self.items)

    def lrange(self, start, stop):
        n = len(self.items)
        if start < 0:
            start = max(n + start, 0)
        if stop < 0:
            stop = n + stop
        stop = min(stop, n - 1)
        if start > stop:
            return []
        return list(self.items)[start:stop + 1]

    def ltrim(self, start, stop):
        self.items = collections.deque(self.lrange(start, stop))
        return "OK"
''',
    tests=[
        [["MiniList", "lpush", "rpush", "lrange", "lrange", "lrange"], [[], [[1, 2, 3]], [[4]], [0, -1], [-2, 10], [3, 1]]],
        [["MiniList", "lpop", "rpop", "llen", "lrange"], [[], [], [], [], [0, -1]]],
        [["MiniList", "rpush", "lpop", "rpop", "lpop", "lpop", "llen"], [[], [[5, 6, 7]], [], [], [], [], []]],
        [["MiniList", "rpush", "lrange", "lrange", "lrange", "lrange", "lrange"],
         [[], [[0, 1, 2, 3, 4]], [1, 3], [-100, 100], [-3, -2], [5, 9], [-1, -1]]],
        [["MiniList", "rpush", "ltrim", "lrange", "ltrim", "llen", "ltrim", "llen"],
         [[], [[0, 1, 2, 3, 4, 5]], [1, -2], [0, -1], [0, 1], [], [5, 9], []]],
        [["MiniList", "lpush", "lpush", "lrange", "rpop", "lrange"], [[], [[1]], [[2, 3]], [0, -1], [], [0, 0]]],
    ] + [_seq(s, 35, "MiniList", [], _list_step) for s in range(11, 18)],
    examples=2,
    wrong_solutions=[
        '''class MiniList:
    def __init__(self): self.items = []
    def lpush(self, values):
        self.items = list(values) + self.items       # bug: keeps the given order
        return len(self.items)
    def rpush(self, values): self.items.extend(values); return len(self.items)
    def lpop(self): return self.items.pop(0) if self.items else None
    def rpop(self): return self.items.pop() if self.items else None
    def llen(self): return len(self.items)
    def lrange(self, start, stop):
        n = len(self.items)
        if start < 0: start = max(n + start, 0)
        if stop < 0: stop = n + stop
        stop = min(stop, n - 1)
        return self.items[start:stop + 1] if start <= stop else []
    def ltrim(self, start, stop): self.items = self.lrange(start, stop); return "OK"
''',
        '''class MiniList:
    def __init__(self): self.items = []
    def lpush(self, values):
        for v in values: self.items.insert(0, v)
        return len(self.items)
    def rpush(self, values): self.items.extend(values); return len(self.items)
    def lpop(self): return self.items.pop(0) if self.items else None
    def rpop(self): return self.items.pop() if self.items else None
    def llen(self): return len(self.items)
    def lrange(self, start, stop):
        return self.items[start:stop]                # bug: Python slice semantics (stop exclusive)
    def ltrim(self, start, stop): self.items = self.lrange(start, stop); return "OK"
''',
    ],
    guide=dict(
        prereqs="Python lists or `collections.deque`. The lesson *Commands in depth: strings, lists and sets* (index rules of LRANGE).",
        intuition="A Redis list is a double-ended queue. The only tricky part is that its index rules differ from Python slices: both ends are inclusive, and out-of-range values are clamped instead of raising errors. Convert the Redis indices to a normal Python slice in one helper and reuse it for `ltrim`.",
        hints=[
            "`lpush` inserts one value at a time at the head, so `lpush([1,2,3])` leaves `[3,2,1]`.",
            "Normalise indices first: a negative `start` becomes `max(n + start, 0)`, a negative `stop` becomes `n + stop`, and `stop` is capped at `n - 1`.",
            "After normalising, the answer is empty when `start > stop`; otherwise it is the Python slice `[start:stop + 1]`. `ltrim` is `lrange` followed by replacing the list.",
        ],
        brute_force="Use a plain Python list with `insert(0, v)` and `pop(0)`. It is correct, but each head operation shifts every element: O(n) per push or pop at the head.",
        approach="""Use a deque so both ends are O(1).

**Dry run:** start empty. `lpush([1,2,3])` → appendleft 1, then 2, then 3 → `[3,2,1]`, returns 3. `rpush([4])` → `[3,2,1,4]`. `lrange(-2,10)`: n=4, start = max(4-2,0) = 2, stop = min(10,3) = 3 → slice `[2:4]` = `[1,4]`. `lrange(3,1)`: start 3 > stop 1 → `[]`.""",
        complexity="Pushes and pops are O(1). `lrange` and `ltrim` are O(n) here because the deque is copied; Redis does O(start + returned).",
        pitfalls="Passing Redis indices straight to a Python slice (stop is exclusive there, and `-100` behaves differently). Forgetting that a negative `stop` such as `-7` on a short list stays negative and gives an empty result. Reversing the order of multi-value `lpush`.",
        follow_up="Add `lmove(source, destination)` between two lists and you can build the reliable queue from the queues lesson.",
    ),
),
dict(
    id="redis-hash-commands",
    title="A Hash with HSET, HINCRBY and HGETALL",
    difficulty="Easy",
    pattern="Redis data types",
    kind="class",
    entry="MiniHash",
    description=r"""
Model one Redis hash. Field names and values are strings.

- `hset(field, value)` - write the field. Returns `1` if the field is **new**, `0` if it was overwritten.
- `hsetnx(field, value)` - write only if the field does not exist. Returns `1` if written, else `0`.
- `hget(field)` - the value, or `None`.
- `hdel(field)` - returns `1` if the field existed and was removed, else `0`.
- `hexists(field)` - `1` or `0`.
- `hlen()` - number of fields.
- `hincrby(field, amount)` - treat the field as an integer (a missing field counts as 0), add `amount`,
  store the result **as a string**, and return the new value **as an integer**. The field always holds a
  valid integer when this is called.
- `hgetall()` - a list of `[field, value]` pairs sorted by field name.

**Example:** `hset("a","x")` → `1`, `hset("a","y")` → `0`, `hincrby("n",5)` → `5`, `hget("n")` → `"5"`,
`hgetall()` → `[["a","y"],["n","5"]]`
""",
    starter='''class MiniHash:
    def __init__(self):
        pass

    def hset(self, field: str, value: str) -> int:
        pass

    def hsetnx(self, field: str, value: str) -> int:
        pass

    def hget(self, field: str):
        pass

    def hdel(self, field: str) -> int:
        pass

    def hexists(self, field: str) -> int:
        pass

    def hlen(self) -> int:
        pass

    def hincrby(self, field: str, amount: int) -> int:
        pass

    def hgetall(self) -> List[List[str]]:
        pass
''',
    solution='''class MiniHash:
    def __init__(self):
        self.f = {}

    def hset(self, field, value):
        new = field not in self.f
        self.f[field] = value
        return int(new)

    def hsetnx(self, field, value):
        if field in self.f:
            return 0
        self.f[field] = value
        return 1

    def hget(self, field):
        return self.f.get(field)

    def hdel(self, field):
        return 1 if self.f.pop(field, None) is not None else 0

    def hexists(self, field):
        return int(field in self.f)

    def hlen(self):
        return len(self.f)

    def hincrby(self, field, amount):
        n = int(self.f.get(field, "0")) + amount
        self.f[field] = str(n)
        return n

    def hgetall(self):
        return [[k, self.f[k]] for k in sorted(self.f)]
''',
    tests=[
        [["MiniHash", "hset", "hset", "hincrby", "hget", "hgetall"], [[], ["a", "x"], ["a", "y"], ["n", 5], ["n"], []]],
        [["MiniHash", "hget", "hdel", "hexists", "hlen", "hgetall"], [[], ["a"], ["a"], ["a"], [], []]],
        [["MiniHash", "hsetnx", "hsetnx", "hget", "hdel", "hsetnx", "hget"],
         [[], ["k", "first"], ["k", "second"], ["k"], ["k"], ["k", "third"], ["k"]]],
        [["MiniHash", "hincrby", "hincrby", "hincrby", "hget", "hlen"], [[], ["n", 3], ["n", -5], ["n", 0], ["n"], []]],
        [["MiniHash", "hset", "hincrby", "hget", "hset", "hgetall"], [[], ["n", "41"], ["n", 1], ["n"], ["b", "z"], []]],
        [["MiniHash", "hset", "hset", "hset", "hdel", "hlen", "hgetall", "hexists"],
         [[], ["c", "3"], ["a", "1"], ["b", "2"], ["b"], [], [], ["c"]]],
    ] + [_seq(s, 35, "MiniHash", [], _hash_step) for s in range(21, 27)],
    examples=2,
    wrong_solutions=[
        '''class MiniHash:
    def __init__(self): self.f = {}
    def hset(self, field, value): self.f[field] = value; return 1      # bug: always 1
    def hsetnx(self, field, value):
        if field in self.f: return 0
        self.f[field] = value; return 1
    def hget(self, field): return self.f.get(field)
    def hdel(self, field): return 1 if self.f.pop(field, None) is not None else 0
    def hexists(self, field): return int(field in self.f)
    def hlen(self): return len(self.f)
    def hincrby(self, field, amount):
        n = int(self.f.get(field, "0")) + amount; self.f[field] = str(n); return n
    def hgetall(self): return [[k, self.f[k]] for k in sorted(self.f)]
''',
        '''class MiniHash:
    def __init__(self): self.f = {}
    def hset(self, field, value):
        new = field not in self.f; self.f[field] = value; return int(new)
    def hsetnx(self, field, value):
        if field in self.f: return 0
        self.f[field] = value; return 1
    def hget(self, field): return self.f.get(field)
    def hdel(self, field): return 1 if self.f.pop(field, None) is not None else 0
    def hexists(self, field): return int(field in self.f)
    def hlen(self): return len(self.f)
    def hincrby(self, field, amount):
        n = int(self.f.get(field, 0)) + amount; self.f[field] = n; return n   # bug: stores an int
    def hgetall(self): return [[k, self.f[k]] for k in sorted(self.f)]
''',
    ],
    guide=dict(
        prereqs="Python dictionaries. The lesson *Commands in depth: hashes and sorted sets*.",
        intuition="A Redis hash is a dictionary whose replies carry extra information: `HSET` tells you whether the field was new, `HDEL` whether anything was removed. Everything is stored as a string, even counters - only the *reply* of `HINCRBY` is a number.",
        hints=[
            "Check whether the field exists **before** you write it, so you can return 1 or 0.",
            "`hincrby` reads the string, converts with `int(...)`, adds, and writes back `str(...)`.",
            "`hgetall` must be sorted by field: build it with `sorted(self.f)`.",
        ],
        brute_force="Keep a list of `[field, value]` pairs and scan it for every operation: O(n) per call. A dictionary makes each one O(1).",
        approach="""One dictionary `f`.

**Dry run:** `hset("a","x")` - `a` is new → 1. `hset("a","y")` - exists → 0, value now `y`. `hincrby("n",5)` - missing counts as 0 → stores `"5"`, returns 5. `hget("n")` → `"5"` (a string). `hgetall()` → `[["a","y"],["n","5"]]`.""",
        complexity="O(1) for every operation except `hgetall`, which sorts: O(n log n).",
        pitfalls="Returning the number of fields written instead of the number created. Storing an integer after `hincrby` so that a later `hget` returns a number. Returning 1 from `hdel` for a field that was not there.",
        follow_up="Add per-field expiry (Redis 7.4 `HEXPIRE`) by combining this with the expiring-store problem.",
    ),
),
dict(
    id="redis-set-algebra",
    title="Sets with SINTER, SUNION and SDIFF",
    difficulty="Easy",
    pattern="Redis data types",
    kind="class",
    entry="SetStore",
    description=r"""
Model several named Redis sets of integers. A key that was never written (or whose set became empty) behaves
as an **empty set**.

- `sadd(key, members)` - add every member of the list. Returns how many were **newly** added.
- `srem(key, members)` - remove them. Returns how many were actually removed.
- `sismember(key, member)` - `1` or `0`.
- `scard(key)` - the size.
- `sinter(keys)` - members present in **every** listed set, as an ascending list.
- `sunion(keys)` - members present in **any** listed set, ascending.
- `sdiff(keys)` - members of the **first** set that are in none of the others, ascending.

`keys` always contains at least one key. Duplicates inside `members` count once.

**Example:** `sadd("a",[1,2,3])` → `3`, `sadd("b",[3,4,3])` → `2`, `sinter(["a","b"])` → `[3]`,
`sdiff(["a","b"])` → `[1,2]`, `sdiff(["b","a"])` → `[4]`, `sinter(["a","nope"])` → `[]`
""",
    starter='''class SetStore:
    def __init__(self):
        pass

    def sadd(self, key: str, members: List[int]) -> int:
        pass

    def srem(self, key: str, members: List[int]) -> int:
        pass

    def sismember(self, key: str, member: int) -> int:
        pass

    def scard(self, key: str) -> int:
        pass

    def sinter(self, keys: List[str]) -> List[int]:
        pass

    def sunion(self, keys: List[str]) -> List[int]:
        pass

    def sdiff(self, keys: List[str]) -> List[int]:
        pass
''',
    solution='''class SetStore:
    def __init__(self):
        self.sets = {}

    def _get(self, key):
        return self.sets.get(key, set())

    def sadd(self, key, members):
        s = self.sets.setdefault(key, set())
        before = len(s)
        s.update(members)
        return len(s) - before

    def srem(self, key, members):
        s = self._get(key)
        before = len(s)
        s.difference_update(members)
        return before - len(s)

    def sismember(self, key, member):
        return int(member in self._get(key))

    def scard(self, key):
        return len(self._get(key))

    def sinter(self, keys):
        out = set(self._get(keys[0]))
        for k in keys[1:]:
            out &= self._get(k)
        return sorted(out)

    def sunion(self, keys):
        out = set()
        for k in keys:
            out |= self._get(k)
        return sorted(out)

    def sdiff(self, keys):
        out = set(self._get(keys[0]))
        for k in keys[1:]:
            out -= self._get(k)
        return sorted(out)
''',
    tests=[
        [["SetStore", "sadd", "sadd", "sinter", "sdiff", "sdiff", "sinter"],
         [[], ["a", [1, 2, 3]], ["b", [3, 4, 3]], [["a", "b"]], [["a", "b"]], [["b", "a"]], [["a", "nope"]]]],
        [["SetStore", "scard", "sismember", "srem", "sunion", "sinter", "sdiff"],
         [[], ["x"], ["x", 1], ["x", [1]], [["x", "y"]], [["x"]], [["x", "y"]]]],
        [["SetStore", "sadd", "sadd", "srem", "scard", "sismember", "sismember"],
         [[], ["a", [5, 5, 6]], ["a", [6, 7]], ["a", [5, 9, 5]], ["a"], ["a", 5], ["a", 7]]],
        [["SetStore", "sadd", "sadd", "sadd", "sinter", "sunion", "sdiff", "sdiff"],
         [[], ["a", [1, 2, 3, 4]], ["b", [2, 3, 5]], ["c", [3, 4, 6]], [["a", "b", "c"]], [["a", "b", "c"]],
          [["a", "b", "c"]], [["c", "a"]]]],
        [["SetStore", "sadd", "sinter", "sunion", "sdiff", "sunion"],
         [[], ["a", [9, 8]], [["a"]], [["nope", "a"]], [["nope", "a"]], [["nope"]]]],
        [["SetStore", "sadd", "srem", "scard", "sinter", "sadd", "sdiff"],
         [[], ["a", [1]], ["a", [1]], ["a"], [["a", "a"]], ["b", [2]], [["b", "a"]]]],
    ] + [_seq(s, 35, "SetStore", [], _set_step) for s in range(31, 37)],
    examples=2,
    wrong_solutions=[
        '''class SetStore:
    def __init__(self): self.sets = {}
    def _get(self, key): return self.sets.get(key, set())
    def sadd(self, key, members):
        s = self.sets.setdefault(key, set()); b = len(s); s.update(members); return len(s) - b
    def srem(self, key, members):
        s = self._get(key); b = len(s); s.difference_update(members); return b - len(s)
    def sismember(self, key, member): return int(member in self._get(key))
    def scard(self, key): return len(self._get(key))
    def sinter(self, keys):
        out = set(self._get(keys[0]))
        for k in keys[1:]: out &= self._get(k)
        return sorted(out)
    def sunion(self, keys):
        out = set()
        for k in keys: out |= self._get(k)
        return sorted(out)
    def sdiff(self, keys):                       # bug: symmetric difference
        out = set(self._get(keys[0]))
        for k in keys[1:]: out ^= self._get(k)
        return sorted(out)
''',
        '''class SetStore:
    def __init__(self): self.sets = {}
    def _get(self, key): return self.sets.get(key, set())
    def sadd(self, key, members):
        s = self.sets.setdefault(key, set()); b = len(s); s.update(members); return len(s) - b
    def srem(self, key, members):
        s = self._get(key); b = len(s); s.difference_update(members); return b - len(s)
    def sismember(self, key, member): return int(member in self._get(key))
    def scard(self, key): return len(self._get(key))
    def sinter(self, keys):                      # bug: skips keys that do not exist
        live = [self.sets[k] for k in keys if k in self.sets]
        return sorted(set.intersection(*live)) if live else []
    def sunion(self, keys):
        out = set()
        for k in keys: out |= self._get(k)
        return sorted(out)
    def sdiff(self, keys):
        out = set(self._get(keys[0]))
        for k in keys[1:]: out -= self._get(k)
        return sorted(out)
''',
    ],
    guide=dict(
        prereqs="Python sets and the operators `&`, `|`, `-`. The lesson *Commands in depth: strings, lists and sets*.",
        intuition="Redis sets map one-to-one onto Python sets. Two details carry the marks: replies count what **changed**, and a missing key is an empty set - which makes any intersection that includes it empty.",
        hints=[
            "For `sadd` and `srem`, compare the size before and after instead of counting the arguments (they may contain duplicates or absent members).",
            "Write a helper that returns the set for a key or an empty set when the key is unknown.",
            "`sdiff` is not symmetric: start from a copy of the first set and subtract each of the others.",
        ],
        brute_force="Store each set as a list and test membership by scanning: O(n) per check and O(n·m) per intersection.",
        approach="""A dictionary from key to Python set, plus a helper for missing keys.

**Dry run:** a = {1,2,3}, b = {3,4}. `sinter(["a","b"])` → {3}. `sdiff(["a","b"])` → {1,2,3} - {3,4} = {1,2}. `sdiff(["b","a"])` → {3,4} - {1,2,3} = {4}. `sinter(["a","nope"])` → {1,2,3} ∩ {} = {}.""",
        complexity="`sadd`/`srem`/`sismember` are O(1) per member. The algebra operations are linear in the sizes of the sets involved, plus O(r log r) to sort the r results.",
        pitfalls="Returning `len(members)` from `sadd`. Ignoring a missing key in `sinter` instead of treating it as empty. Using symmetric difference for `sdiff`. Mutating the first set instead of a copy.",
        follow_up="Add `sinterstore(dest, keys)` and you have the engine of the inverted-index search problem.",
    ),
),
dict(
    id="redis-sorted-set",
    title="Sorted Set: ZADD, ZRANK, ZRANGE, ZRANGEBYSCORE",
    difficulty="Medium",
    pattern="Redis data types",
    kind="class",
    entry="SortedSet",
    description=r"""
Model one Redis sorted set. Members are strings, scores are integers. Members are ordered by **score
ascending, and members with equal scores by member name ascending**.

- `zadd(member, score)` - add the member or change its score. Returns `1` if the member is new, else `0`.
- `zincrby(member, delta)` - add `delta` to the member's score (a missing member starts at 0). Returns the new score.
- `zscore(member)` - the score, or `None`.
- `zrank(member)` - the 0-based position in the ordering, or `None`.
- `zrem(member)` - `1` if removed, `0` if it was not there.
- `zcard()` - number of members.
- `zrange(start, stop)` - members at ranks `start` to `stop`, **both inclusive**; negative ranks count from the
  end; out-of-range values are clamped; an inverted or out-of-range window gives `[]`.
- `zrangebyscore(lo, hi)` - members with `lo <= score <= hi`, in order.

**Example:** `zadd("bob",2)`, `zadd("ann",2)`, `zadd("cat",1)` → order `cat, ann, bob`; `zrank("bob")` → `2`;
`zadd("cat",5)` → `0` and order `ann, bob, cat`; `zrangebyscore(2,2)` → `["ann","bob"]`
""",
    starter='''class SortedSet:
    def __init__(self):
        pass

    def zadd(self, member: str, score: int) -> int:
        pass

    def zincrby(self, member: str, delta: int) -> int:
        pass

    def zscore(self, member: str):
        pass

    def zrank(self, member: str):
        pass

    def zrem(self, member: str) -> int:
        pass

    def zcard(self) -> int:
        pass

    def zrange(self, start: int, stop: int) -> List[str]:
        pass

    def zrangebyscore(self, lo: int, hi: int) -> List[str]:
        pass
''',
    solution='''class SortedSet:
    def __init__(self):
        self.score = {}
        self.order = []          # sorted list of (score, member)

    def _remove(self, member):
        i = bisect.bisect_left(self.order, (self.score[member], member))
        self.order.pop(i)

    def zadd(self, member, score):
        new = member not in self.score
        if not new:
            self._remove(member)
        self.score[member] = score
        bisect.insort(self.order, (score, member))
        return int(new)

    def zincrby(self, member, delta):
        self.zadd(member, self.score.get(member, 0) + delta)
        return self.score[member]

    def zscore(self, member):
        return self.score.get(member)

    def zrank(self, member):
        if member not in self.score:
            return None
        return bisect.bisect_left(self.order, (self.score[member], member))

    def zrem(self, member):
        if member not in self.score:
            return 0
        self._remove(member)
        del self.score[member]
        return 1

    def zcard(self):
        return len(self.order)

    def zrange(self, start, stop):
        n = len(self.order)
        if start < 0:
            start = max(n + start, 0)
        if stop < 0:
            stop = n + stop
        stop = min(stop, n - 1)
        if start > stop:
            return []
        return [m for _, m in self.order[start:stop + 1]]

    def zrangebyscore(self, lo, hi):
        i = bisect.bisect_left(self.order, (lo, ""))
        out = []
        while i < len(self.order) and self.order[i][0] <= hi:
            out.append(self.order[i][1])
            i += 1
        return out
''',
    tests=[
        [["SortedSet", "zadd", "zadd", "zadd", "zrange", "zrank", "zadd", "zrange", "zrangebyscore"],
         [[], ["bob", 2], ["ann", 2], ["cat", 1], [0, -1], ["bob"], ["cat", 5], [0, -1], [2, 2]]],
        [["SortedSet", "zrank", "zscore", "zrem", "zcard", "zrange", "zrangebyscore"],
         [[], ["x"], ["x"], ["x"], [], [0, -1], [0, 10]]],
        [["SortedSet", "zincrby", "zincrby", "zincrby", "zscore", "zrank", "zrange"],
         [[], ["a", 5], ["b", 5], ["a", -5], ["a"], ["b"], [0, 0]]],
        [["SortedSet", "zadd", "zadd", "zadd", "zadd", "zrange", "zrange", "zrange", "zrange"],
         [[], ["d", 4], ["c", 3], ["b", 2], ["a", 1], [1, 2], [-2, -1], [-100, 100], [3, 1]]],
        [["SortedSet", "zadd", "zadd", "zadd", "zrem", "zrem", "zrank", "zcard", "zrangebyscore"],
         [[], ["x", 1], ["y", 1], ["z", 1], ["y"], ["y"], ["z"], [], [1, 1]]],
        [["SortedSet", "zadd", "zadd", "zadd", "zrangebyscore", "zrangebyscore", "zrangebyscore"],
         [[], ["a", -3], ["b", 0], ["c", 7], [-3, 0], [1, 6], [-10, 10]]],
    ] + [_seq(s, 40, "SortedSet", [], _zset_step) for s in range(41, 48)],
    examples=2,
    wrong_solutions=[
        '''class SortedSet:
    def __init__(self): self.score = {}
    def _order(self):                               # bug: ties keep insertion order, not member order
        return [m for m, s in sorted(self.score.items(), key=lambda kv: kv[1])]
    def zadd(self, member, score):
        new = member not in self.score; self.score[member] = score; return int(new)
    def zincrby(self, member, delta):
        self.score[member] = self.score.get(member, 0) + delta; return self.score[member]
    def zscore(self, member): return self.score.get(member)
    def zrank(self, member): return self._order().index(member) if member in self.score else None
    def zrem(self, member): return 1 if self.score.pop(member, None) is not None else 0
    def zcard(self): return len(self.score)
    def zrange(self, start, stop):
        o = self._order(); n = len(o)
        if start < 0: start = max(n + start, 0)
        if stop < 0: stop = n + stop
        stop = min(stop, n - 1)
        return o[start:stop + 1] if start <= stop else []
    def zrangebyscore(self, lo, hi): return [m for m in self._order() if lo <= self.score[m] <= hi]
''',
        '''class SortedSet:
    def __init__(self): self.score = {}
    def _order(self): return [m for m, s in sorted(self.score.items(), key=lambda kv: (kv[1], kv[0]))]
    def zadd(self, member, score):
        new = member not in self.score; self.score[member] = score; return int(new)
    def zincrby(self, member, delta):
        self.score[member] = self.score.get(member, 0) + delta; return self.score[member]
    def zscore(self, member): return self.score.get(member)
    def zrank(self, member): return self._order().index(member) if member in self.score else None
    def zrem(self, member): return 1 if self.score.pop(member, None) is not None else 0
    def zcard(self): return len(self.score)
    def zrange(self, start, stop): return self._order()[start:stop]      # bug: exclusive stop, no clamping
    def zrangebyscore(self, lo, hi): return [m for m in self._order() if lo <= self.score[m] <= hi]
''',
    ],
    guide=dict(
        prereqs="The `bisect` module (binary search in a sorted list). The lesson *Commands in depth: hashes and sorted sets*.",
        intuition="Redis keeps two views of a sorted set: a dictionary from member to score (for `ZSCORE`) and an ordered structure (for ranks and ranges). Do the same: a dict plus a sorted list of `(score, member)` tuples. Python compares tuples element by element, which gives the required tie-break by member for free.",
        hints=[
            "Store `(score, member)` tuples in a list kept sorted with `bisect.insort`.",
            "To change a score, first remove the old tuple - you can find it with `bisect_left` because you know the old score from the dictionary.",
            "`zrank` is `bisect_left(order, (score, member))`. `zrangebyscore(lo, hi)` starts at `bisect_left(order, (lo, \"\"))` and walks while the score is `<= hi`.",
        ],
        brute_force="Keep only the dictionary and sort all items on every query: O(n log n) per `zrange` or `zrank`.",
        approach="""Dictionary `score` + sorted list `order`.

**Dry run:** `zadd("bob",2)` → order `[(2,"bob")]`. `zadd("ann",2)` → `[(2,"ann"),(2,"bob")]` (tie broken by name). `zadd("cat",1)` → `[(1,"cat"),(2,"ann"),(2,"bob")]`. `zrank("bob")` → 2. `zadd("cat",5)`: cat exists, remove `(1,"cat")`, insert `(5,"cat")` → returns 0, order `ann, bob, cat`. `zrangebyscore(2,2)` → `["ann","bob"]`.""",
        complexity="Lookups are O(log n) by binary search; inserts and removals are O(n) because a Python list shifts elements. Redis uses a skip list to make those O(log n) too.",
        pitfalls="Sorting by score only (ties then follow insertion order). Forgetting to remove the old tuple when a score changes, leaving a ghost entry. Treating `zrange` like a Python slice. Returning 1 from `zadd` on an update.",
        follow_up="Replace the list with a skip list or a balanced tree that stores subtree sizes to get O(log n) rank queries - what Redis does with spans.",
    ),
),
dict(
    id="redis-multi-exec-watch",
    title="MULTI / EXEC with WATCH (Optimistic Locking)",
    difficulty="Hard",
    pattern="Transactions",
    kind="class",
    entry="TxStore",
    description=r"""
Simulate Redis transactions for several clients (identified by integers) sharing one key-value store whose
values are integers.

Commands that touch data: `get(client, key)` → value or `None`; `set(client, key, value)` → `"OK"`;
`incr(client, key)` → new value (a missing key counts as 0).

Transaction control:

- `multi(client)` → `"OK"`. From now on this client's `get`/`set`/`incr` are **not executed**: they are queued
  and return `"QUEUED"`. Calling `multi` while already in a transaction returns `"ERR"`.
- `exec(client)` - if the client is not in a transaction, return `"ERR"`. Otherwise, if **any key this client
  is watching has been written since the client started watching it**, discard the queue and return `None`.
  If not, run the queued commands in order and return the list of their results. Either way the client's
  transaction state **and all its watches** are cleared.
- `discard(client)` → `"OK"` and clears the queue and watches, or `"ERR"` if not in a transaction.
- `watch(client, keys)` → `"OK"` and starts watching those keys (calling it again adds keys; a key already
  watched keeps its original starting point). Inside a transaction it returns `"ERR"`.

A **write** is any executed `set` or `incr` by any client, including this one, even if it stores the same
value that was already there.

**Example:** `watch(1,["x"])`, `multi(1)`, `incr(1,"x")` → `"QUEUED"`, `set(2,"x",9)`, `exec(1)` → `None`, `get(1,"x")` → `9`
""",
    starter='''class TxStore:
    def __init__(self):
        pass

    def get(self, client: int, key: str):
        pass

    def set(self, client: int, key: str, value: int):
        pass

    def incr(self, client: int, key: str):
        pass

    def watch(self, client: int, keys: List[str]) -> str:
        pass

    def multi(self, client: int) -> str:
        pass

    def exec(self, client: int):
        pass

    def discard(self, client: int) -> str:
        pass
''',
    solution='''class TxStore:
    def __init__(self):
        self.data = {}
        self.version = {}
        self.queue = {}       # client -> list of queued (op, key, value)
        self.watching = {}    # client -> {key: version when the watch started}

    def _run(self, op, key, value):
        if op == "get":
            return self.data.get(key)
        if op == "set":
            self.data[key] = value
            result = "OK"
        else:
            self.data[key] = self.data.get(key, 0) + 1
            result = self.data[key]
        self.version[key] = self.version.get(key, 0) + 1
        return result

    def _call(self, client, op, key, value=None):
        if client in self.queue:
            self.queue[client].append((op, key, value))
            return "QUEUED"
        return self._run(op, key, value)

    def get(self, client, key):
        return self._call(client, "get", key)

    def set(self, client, key, value):
        return self._call(client, "set", key, value)

    def incr(self, client, key):
        return self._call(client, "incr", key)

    def watch(self, client, keys):
        if client in self.queue:
            return "ERR"
        seen = self.watching.setdefault(client, {})
        for k in keys:
            seen.setdefault(k, self.version.get(k, 0))
        return "OK"

    def multi(self, client):
        if client in self.queue:
            return "ERR"
        self.queue[client] = []
        return "OK"

    def exec(self, client):
        if client not in self.queue:
            return "ERR"
        queued = self.queue.pop(client)
        seen = self.watching.pop(client, {})
        if any(self.version.get(k, 0) != v for k, v in seen.items()):
            return None
        return [self._run(*cmd) for cmd in queued]

    def discard(self, client):
        if client not in self.queue:
            return "ERR"
        del self.queue[client]
        self.watching.pop(client, None)
        return "OK"
''',
    tests=[
        [["TxStore", "watch", "multi", "incr", "set", "exec", "get"],
         [[], [1, ["x"]], [1], [1, "x"], [2, "x", 9], [1], [1, "x"]]],
        [["TxStore", "multi", "set", "incr", "get", "get", "exec", "get"],
         [[], [1], [1, "a", 5], [1, "a"], [1, "a"], [2, "a"], [1], [2, "a"]]],
        [["TxStore", "exec", "discard", "multi", "multi", "watch", "discard", "exec"],
         [[], [1], [1], [1], [1], [1, ["x"]], [1], [1]]],
        [["TxStore", "set", "watch", "set", "multi", "incr", "exec", "get"],
         [[], [1, "x", 5], [1, ["x"]], [2, "x", 5], [1], [1, "x"], [1], [1, "x"]]],
        [["TxStore", "watch", "multi", "set", "exec", "set", "multi", "incr", "exec"],
         [[], [1, ["x"]], [1], [1, "x", 1], [1], [2, "x", 7], [1], [1, "x"], [1]]],
        [["TxStore", "watch", "watch", "set", "multi", "get", "exec", "watch", "set", "multi", "exec"],
         [[], [1, ["x"]], [2, ["y"]], [1, "x", 3], [2], [2, "x"], [2], [1, ["y"]], [1, "y", 1], [1], [1]]],
        [["TxStore", "watch", "set", "watch", "multi", "incr", "exec", "get"],
         [[], [1, ["x"]], [2, "x", 1], [1, ["x"]], [1], [1, "x"], [1], [1, "x"]]],
    ] + [_seq(s, 45, "TxStore", [], _tx_step) for s in range(51, 58)],
    examples=2,
    wrong_solutions=[
        '''class TxStore:
    def __init__(self): self.data, self.queue = {}, {}
    def _run(self, op, key, value):
        if op == "get": return self.data.get(key)
        if op == "set": self.data[key] = value; return "OK"
        self.data[key] = self.data.get(key, 0) + 1; return self.data[key]
    def _call(self, c, op, key, value=None):
        if c in self.queue: self.queue[c].append((op, key, value)); return "QUEUED"
        return self._run(op, key, value)
    def get(self, c, k): return self._call(c, "get", k)
    def set(self, c, k, v): return self._call(c, "set", k, v)
    def incr(self, c, k): return self._call(c, "incr", k)
    def watch(self, c, keys): return "ERR" if c in self.queue else "OK"      # bug: watch ignored
    def multi(self, c):
        if c in self.queue: return "ERR"
        self.queue[c] = []; return "OK"
    def exec(self, c):
        if c not in self.queue: return "ERR"
        return [self._run(*cmd) for cmd in self.queue.pop(c)]
    def discard(self, c):
        if c not in self.queue: return "ERR"
        del self.queue[c]; return "OK"
''',
        '''class TxStore:
    def __init__(self): self.data, self.queue, self.watching = {}, {}, {}
    def _run(self, op, key, value):
        if op == "get": return self.data.get(key)
        if op == "set": self.data[key] = value; return "OK"
        self.data[key] = self.data.get(key, 0) + 1; return self.data[key]
    def _call(self, c, op, key, value=None):
        if c in self.queue: self.queue[c].append((op, key, value)); return "QUEUED"
        return self._run(op, key, value)
    def get(self, c, k): return self._call(c, "get", k)
    def set(self, c, k, v): return self._call(c, "set", k, v)
    def incr(self, c, k): return self._call(c, "incr", k)
    def watch(self, c, keys):
        if c in self.queue: return "ERR"
        seen = self.watching.setdefault(c, {})
        for k in keys: seen.setdefault(k, self.data.get(k))        # bug: compares values, not writes
        return "OK"
    def multi(self, c):
        if c in self.queue: return "ERR"
        self.queue[c] = []; return "OK"
    def exec(self, c):
        if c not in self.queue: return "ERR"
        queued = self.queue.pop(c); seen = self.watching.pop(c, {})
        if any(self.data.get(k) != v for k, v in seen.items()): return None
        return [self._run(*cmd) for cmd in queued]
    def discard(self, c):
        if c not in self.queue: return "ERR"
        del self.queue[c]; self.watching.pop(c, None); return "OK"
''',
    ],
    guide=dict(
        prereqs="The lessons on `MULTI`/`EXEC` and on `WATCH` (*Check-and-set with WATCH, pipelining, and measuring performance*). Dictionaries of dictionaries.",
        intuition="Two ideas. First, queueing: between `multi` and `exec` a client's commands are stored, not run. Second, detecting interference: give every key a **version number** that increases on each write. `watch` remembers the version it saw; `exec` aborts if any remembered version differs from the current one. Comparing versions instead of values matters - a key rewritten with the *same* value has still been written.",
        hints=[
            "Route `get`/`set`/`incr` through one helper that either queues the command (client in a transaction) or runs it immediately.",
            "Keep `version[key]`, bumped by every executed write. `watch` stores `{key: version}` per client, without overwriting a key that is already watched.",
            "`exec` must clear the queue and the watches in every case, then return `None` on a version mismatch or the list of results otherwise.",
        ],
        brute_force="Snapshot the whole store at `watch` time and compare at `exec`. It costs O(store size) per watch and - worse - misses a write that restores the old value.",
        approach="""State: `data`, `version`, `queue[client]`, `watching[client]`.

**Dry run:** `watch(1,["x"])` records `x: 0`. `multi(1)` opens a queue. `incr(1,"x")` → `"QUEUED"`. `set(2,"x",9)` runs at once and bumps `version["x"]` to 1. `exec(1)`: recorded 0 ≠ current 1 → queue discarded, returns `None`. `get(1,"x")` → 9 (client 1 is no longer in a transaction).""",
        complexity="O(1) per command; `exec` is O(watched keys + queued commands). Space is O(keys + queued commands).",
        pitfalls="Comparing values instead of versions. Leaving watches in place after `exec` or `discard`. Executing queued commands one by one as they arrive. Letting a queued `get` return a real value. Resetting the starting version when `watch` is called twice for the same key.",
        follow_up="Add `unwatch(client)`. Then implement a retry loop on top: `transfer(a, b, amount)` that watches both keys and retries until `exec` succeeds.",
    ),
),
]
