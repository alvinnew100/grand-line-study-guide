"""Redis track problems 14-20: locks, semaphores, queues, pub/sub, streams and autocomplete."""
import random as _r


def _seq(seed, n, ctor, ctor_args, step):
    rng, state = _r.Random(seed), {"now": 0, "ids": [], "ms": 0}
    ops, args = [ctor], [list(ctor_args)]
    for _ in range(n):
        op, a = step(rng, state)
        ops.append(op)
        args.append(a)
    return [ops, args]


def _lock_step(rng, st):
    st["now"] += rng.choice([0, 1, 2, 4])
    now, c = st["now"], rng.choice(["A", "B"])
    op = rng.choice(["acquire", "acquire", "release", "extend", "write", "write", "read"])
    if op == "acquire":
        return op, ["job", c, rng.choice([2, 5]), now]
    if op == "release":
        return op, ["job", rng.randint(1, 5), now]
    if op == "extend":
        return op, ["job", rng.randint(1, 5), 5, now]
    if op == "write":
        return op, ["file", rng.randint(1, 5), "v%d" % rng.randint(1, 9)]
    return op, ["file"]


def _sem_step(rng, st):
    st["now"] += rng.choice([0, 1, 1, 3])
    h = rng.choice(["a", "b", "c", "d"])
    op = rng.choice(["acquire", "acquire", "acquire", "release", "holders"])
    if op == "acquire":
        return op, [h, st["now"]]
    if op == "release":
        return op, [h]
    return op, [st["now"]]


def _delay_step(rng, st):
    st["now"] += rng.choice([0, 1, 2])
    t = rng.choice(["t1", "t2", "t3", "t4", "t5"])
    op = rng.choice(["schedule", "schedule", "schedule", "pop_due", "peek", "cancel", "size"])
    if op == "schedule":
        return op, [t, st["now"] + rng.randint(0, 6)]
    if op == "pop_due":
        return op, [st["now"]]
    if op == "cancel":
        return op, [t]
    return op, []


def _rq_step(rng, st):
    st["now"] += rng.choice([0, 1, 2])
    w = rng.choice(["w1", "w2"])
    op = rng.choice(["push", "push", "pop", "pop", "ack", "requeue_expired", "stats"])
    if op == "push":
        st["ids"].append("j%d" % (len(st["ids"]) + 1))
        return op, [st["ids"][-1]]
    if op == "pop":
        return op, [w, st["now"]]
    if op == "ack":
        return op, [w, rng.choice(st["ids"]) if st["ids"] else "j0"]
    if op == "requeue_expired":
        return op, [st["now"]]
    return op, []


def _ps_step(rng, st):
    c = rng.choice(["c1", "c2", "c3"])
    op = rng.choice(["subscribe", "psubscribe", "unsubscribe", "publish", "publish", "publish", "messages"])
    if op in ("subscribe", "unsubscribe"):
        return op, [c, rng.choice(["news", "news:sport", "chat"])]
    if op == "psubscribe":
        return op, [c, rng.choice(["news*", "*", "ch*t", "news:*"])]
    if op == "publish":
        return op, [rng.choice(["news", "news:sport", "chat", "other"]), "m%d" % rng.randint(1, 9)]
    return op, [c]


def _stream_step(rng, st):
    op = rng.choice(["xadd", "xadd", "xreadgroup", "xreadgroup", "xack", "xpending", "xclaim", "xlen"])
    if op == "xadd":
        st["ms"] += rng.choice([0, 0, 1, 3, -1])
        st["ids"].append(1)
        return op, [max(st["ms"], 0), "e%d" % len(st["ids"])]
    if op == "xreadgroup":
        return op, ["g", rng.choice(["c1", "c2"]), rng.randint(1, 3)]
    if op == "xack":
        return op, ["g", "%d-%d" % (rng.randint(0, 6), rng.randint(0, 2))]
    if op == "xpending":
        return op, ["g"]
    if op == "xclaim":
        return op, ["g", rng.choice(["c1", "c2"]), ["%d-%d" % (rng.randint(0, 6), rng.randint(0, 2)) for _ in range(2)]]
    return op, []


def _ac_step(rng, st):
    words = ["man", "manchester", "Mannheim", "mantua", "madrid", "milan", "oslo", "Oslofjord", "ma"]
    op = rng.choice(["add", "add", "add", "remove", "suggest", "suggest", "count"])
    if op in ("add", "remove"):
        return op, [rng.choice(words)]
    p = rng.choice(["m", "ma", "MAN", "o", "osl", "", "x", "mi"])
    return (op, [p, rng.randint(0, 4)]) if op == "suggest" else (op, [p])


PROBLEMS = [
dict(
    id="redis-lock-fencing",
    title="Distributed Lock with Expiry and Fencing Tokens",
    difficulty="Hard",
    pattern="Coordination",
    kind="class",
    entry="LockService",
    description=r"""
Simulate a Redis lock (`SET key token NX PX ttl`) together with a storage service that uses **fencing tokens**
to reject writers whose lock has expired. Time is the integer `now`, never decreasing.

A lock is **held** while `now <` its expiry.

- `acquire(name, client, ttl, now)` - if the lock is not held, grant it until `now + ttl` and return a new
  fencing token: integers `1, 2, 3, ...`, increasing across **all** locks. If it is held (even by the same
  client), return `None`.
- `release(name, token, now)` - `True` and the lock becomes free if it is held and its token equals `token`;
  otherwise `False`.
- `extend(name, token, ttl, now)` - `True` and the expiry becomes `now + ttl` if the lock is held with that
  token; otherwise `False`.
- `write(resource, token, value)` - the storage accepts the write (returns `True`, stores the value) only if
  `token` is **greater than or equal to** the highest token it has accepted so far for that resource;
  otherwise `False`.
- `read(resource)` - the stored value, or `None`.

**Example:** `acquire("job","A",5,0)` → `1`; `acquire("job","B",5,6)` → `2` (A's lock expired);
`write("file",2,"from B")` → `True`; `write("file",1,"from A")` → `False`; `release("job",1,7)` → `False`
""",
    starter='''class LockService:
    def __init__(self):
        pass

    def acquire(self, name: str, client: str, ttl: int, now: int):
        pass

    def release(self, name: str, token: int, now: int) -> bool:
        pass

    def extend(self, name: str, token: int, ttl: int, now: int) -> bool:
        pass

    def write(self, resource: str, token: int, value: str) -> bool:
        pass

    def read(self, resource: str):
        pass
''',
    solution='''class LockService:
    def __init__(self):
        self.locks = {}        # name -> [token, expiry]
        self.next_token = 1
        self.highest = {}      # resource -> highest accepted token
        self.values = {}

    def _held(self, name, now):
        return name in self.locks and now < self.locks[name][1]

    def acquire(self, name, client, ttl, now):
        if self._held(name, now):
            return None
        token = self.next_token
        self.next_token += 1
        self.locks[name] = [token, now + ttl]
        return token

    def release(self, name, token, now):
        if self._held(name, now) and self.locks[name][0] == token:
            del self.locks[name]
            return True
        return False

    def extend(self, name, token, ttl, now):
        if self._held(name, now) and self.locks[name][0] == token:
            self.locks[name][1] = now + ttl
            return True
        return False

    def write(self, resource, token, value):
        if token < self.highest.get(resource, 0):
            return False
        self.highest[resource] = token
        self.values[resource] = value
        return True

    def read(self, resource):
        return self.values.get(resource)
''',
    tests=[
        [["LockService", "acquire", "acquire", "write", "write", "release", "read"],
         [[], ["job", "A", 5, 0], ["job", "B", 5, 6], ["file", 2, "from B"], ["file", 1, "from A"], ["job", 1, 7], ["file"]]],
        [["LockService", "release", "extend", "read", "write", "read"],
         [[], ["job", 1, 0], ["job", 1, 5, 0], ["f"], ["f", 0, "x"], ["f"]]],
        [["LockService", "acquire", "acquire", "acquire", "release", "acquire", "acquire"],
         [[], ["job", "A", 5, 0], ["job", "A", 5, 1], ["job", "B", 5, 4], ["job", 1, 4], ["job", "B", 5, 4], ["other", "A", 1, 4]]],
        [["LockService", "acquire", "extend", "acquire", "extend", "acquire", "extend"],
         [[], ["job", "A", 5, 0], ["job", 1, 5, 4], ["job", "B", 5, 8], ["job", 1, 5, 9], ["job", "B", 5, 9], ["job", 1, 5, 9]]],
        [["LockService", "acquire", "release", "release", "acquire", "release", "release"],
         [[], ["job", "A", 5, 0], ["job", 2, 1], ["job", 1, 5], ["job", "B", 3, 5], ["job", 1, 6], ["job", 2, 6]]],
        [["LockService", "write", "write", "write", "write", "read", "write", "read"],
         [[], ["f", 3, "a"], ["f", 3, "b"], ["f", 2, "c"], ["g", 1, "d"], ["f"], ["f", 4, "e"], ["g"]]],
    ] + [_seq(s, 45, "LockService", [], _lock_step) for s in range(1, 7)],
    examples=2,
    wrong_solutions=[
        '''class LockService:
    def __init__(self): self.locks, self.n, self.values = {}, 1, {}
    def _held(self, name, now): return name in self.locks and now < self.locks[name][1]
    def acquire(self, name, client, ttl, now):
        if self._held(name, now): return None
        t = self.n; self.n += 1; self.locks[name] = [t, now + ttl]; return t
    def release(self, name, token, now):
        if self._held(name, now) and self.locks[name][0] == token: del self.locks[name]; return True
        return False
    def extend(self, name, token, ttl, now):
        if self._held(name, now) and self.locks[name][0] == token: self.locks[name][1] = now + ttl; return True
        return False
    def write(self, resource, token, value): self.values[resource] = value; return True   # bug: no fencing
    def read(self, resource): return self.values.get(resource)
''',
        '''class LockService:
    def __init__(self): self.locks, self.n, self.high, self.values = {}, 1, {}, {}
    def _held(self, name, now): return name in self.locks and now < self.locks[name][1]
    def acquire(self, name, client, ttl, now):
        if self._held(name, now): return None
        t = self.n; self.n += 1; self.locks[name] = [t, now + ttl]; return t
    def release(self, name, token, now):
        if name in self.locks: del self.locks[name]; return True       # bug: anyone can release
        return False
    def extend(self, name, token, ttl, now):
        if self._held(name, now) and self.locks[name][0] == token: self.locks[name][1] = now + ttl; return True
        return False
    def write(self, resource, token, value):
        if token < self.high.get(resource, 0): return False
        self.high[resource] = token; self.values[resource] = value; return True
    def read(self, resource): return self.values.get(resource)
''',
    ],
    guide=dict(
        prereqs="The lessons *Autocomplete, distributed locks and counting semaphores* and *Lua scripting: rewriting locks, semaphores and transactions*.",
        intuition="There are two separate mechanisms. The **lock** has an expiry (so a crashed holder cannot block for ever) and a token (so only the holder can release or extend it). But expiry means an old holder may still be running when a new one starts. The **storage** protects itself: it remembers the highest token it has seen and refuses anything older. The lock keeps most overlap away; fencing makes the remaining overlap harmless.",
        hints=[
            "A lock is held only while `now < expiry`; an expired lock is the same as no lock.",
            "`release` and `extend` share one condition: held **and** the stored token equals the caller's token.",
            "For `write`, keep `highest[resource]`. Reject when `token < highest`, otherwise update it and store the value.",
        ],
        brute_force="A lock without tokens or fencing: `release` deletes whatever is there and `write` always succeeds. It passes the happy path and silently corrupts data when a holder overruns its TTL.",
        approach="""**Dry run:** `acquire("job","A",5,0)` → token 1, expiry 5. `acquire("job","B",5,6)`: 6 < 5 is false, so the lock is free → token 2, expiry 11. `write("file",2,"from B")` → highest 2. `write("file",1,"from A")`: 1 < 2 → rejected. `release("job",1,7)`: the lock is held, but by token 2 → `False`.""",
        complexity="O(1) per operation; O(locks + resources) space.",
        pitfalls="Letting the same client re-acquire a lock it already holds. Releasing or extending an expired lock. Using `now <= expiry`. Resetting the token counter per lock (tokens must increase globally to be comparable). Rejecting a second write with the *same* token - the current holder must be able to write repeatedly.",
        follow_up="How does the picture change if the lock server fails over to a replica that never received the lock key? What would Redlock or a consensus system add?",
    ),
),
dict(
    id="redis-counting-semaphore",
    title="Counting Semaphore with Timeouts",
    difficulty="Medium",
    pattern="Coordination",
    kind="class",
    entry="Semaphore",
    description=r"""
Implement the sorted-set counting semaphore (members = holders, score = time of acquisition), as the atomic
script version does it. Time is the integer `now`, never decreasing.

`Semaphore(limit, timeout)`:

- `acquire(holder, now)`:
  1. remove every holder whose acquisition time is `<= now - timeout` (they are considered dead);
  2. if `holder` still holds a slot, refresh its time to `now` and return `True`;
  3. otherwise, if fewer than `limit` holders remain, add it with time `now` and return `True`;
  4. otherwise return `False`.
- `release(holder)` - `True` if the holder was recorded (even if stale) and is now removed, else `False`.
- `holders(now)` - after removing dead holders as in step 1, the remaining holder names in ascending order.

**Example:** `Semaphore(2, 10)`: `acquire("a",0)`, `acquire("b",1)` → `True, True`; `acquire("c",2)` → `False`;
`acquire("c",10)` → `True` (a timed out); `holders(10)` → `["b","c"]`
""",
    starter='''class Semaphore:
    def __init__(self, limit: int, timeout: int):
        pass

    def acquire(self, holder: str, now: int) -> bool:
        pass

    def release(self, holder: str) -> bool:
        pass

    def holders(self, now: int) -> List[str]:
        pass
''',
    solution='''class Semaphore:
    def __init__(self, limit, timeout):
        self.limit, self.timeout = limit, timeout
        self.since = {}

    def _clean(self, now):
        for h in [h for h, t in self.since.items() if t <= now - self.timeout]:
            del self.since[h]

    def acquire(self, holder, now):
        self._clean(now)
        if holder in self.since or len(self.since) < self.limit:
            self.since[holder] = now
            return True
        return False

    def release(self, holder):
        return self.since.pop(holder, None) is not None

    def holders(self, now):
        self._clean(now)
        return sorted(self.since)
''',
    tests=[
        [["Semaphore", "acquire", "acquire", "acquire", "acquire", "holders"],
         [[2, 10], ["a", 0], ["b", 1], ["c", 2], ["c", 10], [10]]],
        [["Semaphore", "acquire", "release", "holders"], [[0, 5], ["a", 0], ["a"], [0]]],
        [["Semaphore", "acquire", "acquire", "acquire", "release", "release", "acquire", "holders"],
         [[1, 5], ["a", 0], ["a", 3], ["b", 4], ["b"], ["a"], ["b", 4], [4]]],
        [["Semaphore", "acquire", "acquire", "acquire", "acquire", "holders", "holders"],
         [[2, 5], ["a", 0], ["b", 0], ["a", 4], ["c", 5], [8], [9]]],
        [["Semaphore", "acquire", "acquire", "release", "acquire", "acquire", "holders"],
         [[3, 100], ["x", 0], ["y", 0], ["z"], ["z", 1], ["w", 1], [50]]],
        [["Semaphore", "acquire", "acquire", "holders", "release", "acquire"],
         [[1, 3], ["a", 0], ["b", 2], [3], ["a"], ["b", 3]]],
    ] + [_seq(s, 45, "Semaphore", list(c), _sem_step) for s, c in
         [(11, (2, 4)), (12, (3, 6)), (13, (1, 3)), (14, (2, 2)), (15, (3, 5)), (16, (2, 8))]],
    examples=2,
    wrong_solutions=[
        '''class Semaphore:
    def __init__(self, limit, timeout): self.limit, self.since = limit, {}
    def acquire(self, holder, now):                 # bug: dead holders are never removed
        if holder in self.since or len(self.since) < self.limit:
            self.since[holder] = now; return True
        return False
    def release(self, holder): return self.since.pop(holder, None) is not None
    def holders(self, now): return sorted(self.since)
''',
        '''class Semaphore:
    def __init__(self, limit, timeout): self.limit, self.timeout, self.since = limit, timeout, {}
    def _clean(self, now):
        for h in [h for h, t in self.since.items() if t <= now - self.timeout]: del self.since[h]
    def acquire(self, holder, now):
        self._clean(now)
        if len(self.since) < self.limit:            # bug: a current holder cannot refresh when full
            self.since[holder] = now; return True
        return False
    def release(self, holder): return self.since.pop(holder, None) is not None
    def holders(self, now): self._clean(now); return sorted(self.since)
''',
    ],
    guide=dict(
        prereqs="The semaphore sections of *Autocomplete, distributed locks and counting semaphores* and the scripted version in *Lua scripting: rewriting locks, semaphores and transactions*.",
        intuition="A counting semaphore is a lock with several slots. Record each holder with the time it entered. Before any decision, throw out holders that have been silent longer than the timeout - that is what stops a crashed process from keeping a slot for ever. Then the rule is: a current holder may refresh; a newcomer gets in only if a slot is free.",
        hints=[
            "Keep a dictionary holder → time. Write `_clean(now)` to delete entries with time `<= now - timeout`.",
            "Call `_clean` first in both `acquire` and `holders`.",
            "In `acquire`, check 'already a holder' before checking the limit, so refreshing works when the semaphore is full.",
        ],
        brute_force="Add the holder, sort all holders by time, and remove it again if its position is at or beyond the limit - the multi-command version from the lesson. It works in a single thread but needs two steps, which races between real clients.",
        approach="""**Dry run, limit 2, timeout 10:** a at 0, b at 1 → both in. c at 2: cutoff -8, nobody dead, 2 holders → `False`. c at 10: cutoff 0, a (time 0) is dead → removed; 1 holder → c enters. `holders(10)` → ["b","c"].""",
        complexity="`acquire` and `holders` are O(n) for n holders here (n is at most the limit plus stale entries). Redis does the cleanup with one `ZREMRANGEBYSCORE`, O(log n + removed).",
        pitfalls="Using `<` for the cutoff. Not letting a holder refresh when the semaphore is full. Counting stale holders against the limit. Returning `False` from `release` for a stale but recorded holder (the specification says it is removed and reported).",
        follow_up="Make it fair across clients with different clocks by stamping with the server's time, as the Lua version does.",
    ),
),
dict(
    id="redis-delayed-queue",
    title="Delayed Task Queue",
    difficulty="Medium",
    pattern="Queues",
    kind="class",
    entry="DelayedQueue",
    description=r"""
Implement the delayed queue built on a sorted set whose score is the time a task becomes due.

Tasks are strings. Pending tasks are ordered by **`(run_at, task)`** ascending, like sorted-set members.

- `schedule(task, run_at)` - add the task, or if it is already pending **replace** its time (`ZADD`). Returns
  the number of pending tasks.
- `pop_due(now)` - remove and return, in order, every task with `run_at <= now`.
- `peek()` - `[task, run_at]` for the task that is first in order, or `None` if there is none.
- `cancel(task)` - `1` if the task was pending and is removed, else `0`.
- `size()` - number of pending tasks.

**Example:** `schedule("b",5)`, `schedule("a",5)`, `schedule("c",2)` → `peek()` is `["c",2]`;
`pop_due(4)` → `["c"]`; `schedule("b",9)`; `pop_due(5)` → `["a"]`; `pop_due(9)` → `["b"]`
""",
    starter='''class DelayedQueue:
    def __init__(self):
        pass

    def schedule(self, task: str, run_at: int) -> int:
        pass

    def pop_due(self, now: int) -> List[str]:
        pass

    def peek(self):
        pass

    def cancel(self, task: str) -> int:
        pass

    def size(self) -> int:
        pass
''',
    solution='''class DelayedQueue:
    def __init__(self):
        self.when = {}
        self.heap = []            # (run_at, task); may contain outdated entries

    def schedule(self, task, run_at):
        self.when[task] = run_at
        heapq.heappush(self.heap, (run_at, task))
        return len(self.when)

    def _skip_outdated(self):
        while self.heap and self.when.get(self.heap[0][1]) != self.heap[0][0]:
            heapq.heappop(self.heap)

    def pop_due(self, now):
        out = []
        while True:
            self._skip_outdated()
            if not self.heap or self.heap[0][0] > now:
                return out
            run_at, task = heapq.heappop(self.heap)
            del self.when[task]
            out.append(task)

    def peek(self):
        self._skip_outdated()
        return [self.heap[0][1], self.heap[0][0]] if self.heap else None

    def cancel(self, task):
        return 1 if self.when.pop(task, None) is not None else 0

    def size(self):
        return len(self.when)
''',
    tests=[
        [["DelayedQueue", "schedule", "schedule", "schedule", "peek", "pop_due", "schedule", "pop_due", "pop_due"],
         [[], ["b", 5], ["a", 5], ["c", 2], [], [4], ["b", 9], [5], [9]]],
        [["DelayedQueue", "peek", "pop_due", "cancel", "size"], [[], [], [100], ["x"], []]],
        [["DelayedQueue", "schedule", "schedule", "cancel", "cancel", "peek", "size", "pop_due"],
         [[], ["a", 1], ["b", 2], ["a"], ["a"], [], [], [5]]],
        [["DelayedQueue", "schedule", "schedule", "schedule", "peek", "pop_due", "size"],
         [[], ["a", 9], ["a", 3], ["a", 6], [], [5], []]],
        [["DelayedQueue", "schedule", "schedule", "schedule", "schedule", "pop_due", "pop_due", "peek"],
         [[], ["z", 1], ["y", 1], ["x", 1], ["w", 2], [0], [1], []]],
        [["DelayedQueue", "schedule", "pop_due", "schedule", "schedule", "pop_due", "size"],
         [[], ["a", 5], [5], ["a", 7], ["a", 2], [6], []]],
    ] + [_seq(s, 45, "DelayedQueue", [], _delay_step) for s in range(21, 27)],
    examples=2,
    wrong_solutions=[
        '''class DelayedQueue:
    def __init__(self): self.items = []                  # bug: insertion order, duplicates kept
    def schedule(self, task, run_at): self.items.append((task, run_at)); return len(self.items)
    def pop_due(self, now):
        out = [t for t, r in self.items if r <= now]
        self.items = [(t, r) for t, r in self.items if r > now]; return out
    def peek(self): return list(self.items[0]) if self.items else None
    def cancel(self, task):
        n = len(self.items); self.items = [(t, r) for t, r in self.items if t != task]
        return 1 if len(self.items) < n else 0
    def size(self): return len(self.items)
''',
        '''class DelayedQueue:
    def __init__(self): self.when = {}
    def _order(self): return sorted(self.when, key=lambda t: (self.when[t], t))
    def schedule(self, task, run_at): self.when[task] = run_at; return len(self.when)
    def pop_due(self, now):
        out = [t for t in self._order() if self.when[t] < now]      # bug: due exactly now is skipped
        for t in out: del self.when[t]
        return out
    def peek(self):
        o = self._order(); return [o[0], self.when[o[0]]] if o else None
    def cancel(self, task): return 1 if self.when.pop(task, None) is not None else 0
    def size(self): return len(self.when)
''',
    ],
    guide=dict(
        prereqs="`heapq` (a priority queue). The delayed-task section of *Task queues, pull messaging and file distribution*.",
        intuition="A delayed queue is a priority queue ordered by due time: you only ever look at the earliest task. Rescheduling and cancelling are awkward in a heap because you cannot remove from the middle cheaply, so use **lazy deletion**: keep the true due time in a dictionary, leave outdated heap entries in place, and skip them when they reach the top.",
        hints=[
            "Keep `when[task]` as the source of truth and push `(run_at, task)` onto a heap for ordering.",
            "A heap entry is outdated if `when.get(task) != run_at` (rescheduled or cancelled). Pop such entries before looking at the top.",
            "`pop_due` repeats: skip outdated entries, stop if the heap is empty or the top is in the future, otherwise pop and record.",
        ],
        brute_force="Keep only the dictionary and sort it on each `pop_due` or `peek`: O(n log n) per call.",
        approach="""**Dry run:** schedule b@5, a@5, c@2 → order c(2), a(5), b(5). `peek()` → ["c",2]. `pop_due(4)` → ["c"]. `schedule("b",9)` → `when[b]=9`; the heap still has the old (5,b). `pop_due(5)`: top (5,a) is valid and due → "a"; next top (5,b) is outdated → skipped; next (9,b) is in the future → stop. Result ["a"]. `pop_due(9)` → ["b"].""",
        complexity="`schedule` O(log n); `pop_due` O(k log n) for k returned tasks plus skipped entries, each of which is skipped once; `cancel` and `size` O(1).",
        pitfalls="Treating a rescheduled task as two tasks. Using `<` so that a task due exactly now waits. Returning tasks in insertion order instead of `(run_at, task)` order. Letting `size` count outdated heap entries.",
        follow_up="Add retries with exponential backoff: `fail(task, now, attempt)` reschedules at `now + 10 * 2**attempt`.",
    ),
),
dict(
    id="redis-reliable-queue",
    title="Reliable Queue with Acknowledgements",
    difficulty="Medium",
    pattern="Queues",
    kind="class",
    entry="ReliableQueue",
    description=r"""
Implement the at-least-once queue built from `BLMOVE` into an in-progress list plus `LREM` to acknowledge.
Jobs are unique strings. Time is the integer `now`, never decreasing.

`ReliableQueue(visibility_timeout)`:

- `push(job)` - append to the tail of the ready queue. Returns the ready queue's length.
- `pop(worker, now)` - take the job at the head of the ready queue, record it as in progress for `worker` with
  deadline `now + visibility_timeout`, and return it; `None` if nothing is ready.
- `ack(worker, job)` - `True` if that job is in progress **for that worker**; it is then removed for good.
  Otherwise `False`.
- `requeue_expired(now)` - every in-progress job with `deadline <= now` goes back to the **tail** of the ready
  queue, in order of `(deadline, job)`. Returns the list of jobs moved.
- `stats()` - `[ready_count, in_progress_count]`.

**Example:** `ReliableQueue(10)`: `push("j1")`, `push("j2")`, `pop("w1",0)` → `"j1"`, `pop("w2",3)` → `"j2"`,
`ack("w2","j2")` → `True`, `requeue_expired(10)` → `["j1"]`, `pop("w2",10)` → `"j1"`, `ack("w1","j1")` → `False`
""",
    starter='''class ReliableQueue:
    def __init__(self, visibility_timeout: int):
        pass

    def push(self, job: str) -> int:
        pass

    def pop(self, worker: str, now: int):
        pass

    def ack(self, worker: str, job: str) -> bool:
        pass

    def requeue_expired(self, now: int) -> List[str]:
        pass

    def stats(self) -> List[int]:
        pass
''',
    solution='''class ReliableQueue:
    def __init__(self, visibility_timeout):
        self.timeout = visibility_timeout
        self.ready = collections.deque()
        self.processing = {}          # job -> (worker, deadline)

    def push(self, job):
        self.ready.append(job)
        return len(self.ready)

    def pop(self, worker, now):
        if not self.ready:
            return None
        job = self.ready.popleft()
        self.processing[job] = (worker, now + self.timeout)
        return job

    def ack(self, worker, job):
        if job in self.processing and self.processing[job][0] == worker:
            del self.processing[job]
            return True
        return False

    def requeue_expired(self, now):
        expired = sorted((d, j) for j, (w, d) in self.processing.items() if d <= now)
        for _, job in expired:
            del self.processing[job]
            self.ready.append(job)
        return [job for _, job in expired]

    def stats(self):
        return [len(self.ready), len(self.processing)]
''',
    tests=[
        [["ReliableQueue", "push", "push", "pop", "pop", "ack", "requeue_expired", "pop", "ack"],
         [[10], ["j1"], ["j2"], ["w1", 0], ["w2", 3], ["w2", "j2"], [10], ["w2", 10], ["w1", "j1"]]],
        [["ReliableQueue", "pop", "ack", "requeue_expired", "stats"], [[5], ["w", 0], ["w", "j"], [100], []]],
        [["ReliableQueue", "push", "pop", "requeue_expired", "requeue_expired", "stats", "pop", "ack", "stats"],
         [[5], ["a"], ["w1", 0], [4], [5], [], ["w2", 5], ["w2", "a"], []]],
        [["ReliableQueue", "push", "push", "push", "pop", "pop", "pop", "requeue_expired", "pop", "pop", "pop"],
         [[5], ["c"], ["b"], ["a"], ["w", 2], ["w", 1], ["w", 1], [7], ["w", 7], ["w", 7], ["w", 7]]],
        [["ReliableQueue", "push", "pop", "ack", "ack", "push", "pop", "stats"],
         [[3], ["x"], ["w1", 0], ["w1", "x"], ["w1", "x"], ["y"], ["w1", 1], []]],
        [["ReliableQueue", "push", "push", "pop", "push", "requeue_expired", "pop", "pop", "pop"],
         [[2], ["a"], ["b"], ["w", 0], ["c"], [2], ["w", 2], ["w", 2], ["w", 2]]],
    ] + [_seq(s, 50, "ReliableQueue", [t], _rq_step) for s, t in [(31, 2), (32, 3), (33, 1), (34, 4), (35, 2), (36, 5)]],
    examples=2,
    wrong_solutions=[
        '''class ReliableQueue:
    def __init__(self, visibility_timeout): self.ready = collections.deque()
    def push(self, job): self.ready.append(job); return len(self.ready)
    def pop(self, worker, now): return self.ready.popleft() if self.ready else None   # bug: at-most-once
    def ack(self, worker, job): return False
    def requeue_expired(self, now): return []
    def stats(self): return [len(self.ready), 0]
''',
        '''class ReliableQueue:
    def __init__(self, visibility_timeout):
        self.timeout, self.ready, self.processing = visibility_timeout, collections.deque(), {}
    def push(self, job): self.ready.append(job); return len(self.ready)
    def pop(self, worker, now):
        if not self.ready: return None
        job = self.ready.popleft(); self.processing[job] = (worker, now + self.timeout); return job
    def ack(self, worker, job):
        if job in self.processing: del self.processing[job]; return True        # bug: any worker may ack
        return False
    def requeue_expired(self, now):
        expired = sorted((d, j) for j, (w, d) in self.processing.items() if d <= now)
        for _, job in expired: del self.processing[job]; self.ready.append(job)
        return [job for _, job in expired]
    def stats(self): return [len(self.ready), len(self.processing)]
''',
    ],
    guide=dict(
        prereqs="The reliable-queue section of *Task queues, pull messaging and file distribution* (at-least-once delivery, acknowledgement).",
        intuition="A job must never exist only in a worker's memory. So popping does not delete it - it *moves* it to an in-progress table with a deadline. Finishing means acknowledging, which finally removes it. If the deadline passes without an acknowledgement, the worker is presumed dead and the job goes back to the queue for someone else.",
        hints=[
            "Use a deque for the ready queue and a dictionary `job -> (worker, deadline)` for jobs in progress.",
            "`ack` must check both that the job is in progress and that it belongs to the worker calling.",
            "`requeue_expired` collects `(deadline, job)` pairs with `deadline <= now`, sorts them, and appends the jobs to the tail.",
        ],
        brute_force="A plain queue where `pop` removes the job. It is simpler and loses the job whenever a worker crashes mid-task.",
        approach="""**Dry run, timeout 10:** push j1, j2. `pop("w1",0)` → j1, deadline 10. `pop("w2",3)` → j2, deadline 13. `ack("w2","j2")` → `True`. `requeue_expired(10)`: j1's deadline 10 <= 10 → back to ready → ["j1"]. `pop("w2",10)` → j1, now owned by w2. `ack("w1","j1")` → `False`: w1 finished too late and the job is no longer its own.""",
        complexity="`push`, `pop`, `ack` O(1); `requeue_expired` O(p log p) for p jobs in progress.",
        pitfalls="Letting a worker acknowledge a job that was reassigned (the late worker's result may be a duplicate - handlers must be idempotent). Using `<` for expiry. Putting requeued jobs at the head. Forgetting to remove the in-progress record on requeue.",
        follow_up="Count deliveries per job and move a job to a dead-letter list after three failed attempts. Compare with Redis streams, where `XPENDING` and `XAUTOCLAIM` provide this bookkeeping.",
    ),
),
dict(
    id="redis-pubsub",
    title="Publish/Subscribe Delivery",
    difficulty="Medium",
    pattern="Messaging",
    kind="class",
    entry="PubSub",
    description=r"""
Simulate Redis pub/sub: messages go only to clients subscribed **at the moment of publishing**; nothing is stored
for later subscribers.

- `subscribe(client, channel)` - subscribe to an exact channel name. Returns the client's total number of
  subscriptions (channels + patterns) afterwards. Subscribing twice has no extra effect.
- `psubscribe(client, pattern)` - subscribe to a pattern, where `*` matches any run of characters (including
  none) and every other character matches itself. Returns the same total.
- `unsubscribe(client, channel)` - remove an exact-channel subscription (no effect if absent). Returns the total.
- `publish(channel, message)` - deliver to every matching subscription and return the number of deliveries.
  A client subscribed to the channel **and** to a matching pattern receives the message once for each.
- `messages(client)` - the list of `[channel, message]` pairs delivered to the client since its last
  `messages` call, oldest first, and clear it.

**Example:** `subscribe("c1","news")` → `1`; `psubscribe("c1","n*")` → `2`; `publish("news","hi")` → `2`;
`publish("chat","yo")` → `0`; `messages("c1")` → `[["news","hi"],["news","hi"]]`; `messages("c1")` → `[]`
""",
    starter='''class PubSub:
    def __init__(self):
        pass

    def subscribe(self, client: str, channel: str) -> int:
        pass

    def psubscribe(self, client: str, pattern: str) -> int:
        pass

    def unsubscribe(self, client: str, channel: str) -> int:
        pass

    def publish(self, channel: str, message: str) -> int:
        pass

    def messages(self, client: str) -> List[List[str]]:
        pass
''',
    solution='''class PubSub:
    def __init__(self):
        self.channels = {}     # client -> set of channels
        self.patterns = {}     # client -> set of patterns
        self.inbox = {}
        self.order = []        # clients in order of first appearance

    def _client(self, client):
        if client not in self.channels:
            self.channels[client], self.patterns[client], self.inbox[client] = set(), set(), []
            self.order.append(client)

    def _total(self, client):
        return len(self.channels[client]) + len(self.patterns[client])

    @staticmethod
    def _match(pattern, text):
        parts = pattern.split("*")
        if len(parts) == 1:
            return pattern == text
        if not text.startswith(parts[0]) or not text.endswith(parts[-1]):
            return False
        if len(text) < len(parts[0]) + len(parts[-1]):
            return False
        pos, end = len(parts[0]), len(text) - len(parts[-1])
        for mid in parts[1:-1]:
            found = text.find(mid, pos, end)
            if found == -1:
                return False
            pos = found + len(mid)
        return True

    def subscribe(self, client, channel):
        self._client(client)
        self.channels[client].add(channel)
        return self._total(client)

    def psubscribe(self, client, pattern):
        self._client(client)
        self.patterns[client].add(pattern)
        return self._total(client)

    def unsubscribe(self, client, channel):
        self._client(client)
        self.channels[client].discard(channel)
        return self._total(client)

    def publish(self, channel, message):
        delivered = 0
        for client in self.order:
            hits = int(channel in self.channels[client])
            hits += sum(1 for p in self.patterns[client] if self._match(p, channel))
            self.inbox[client].extend([[channel, message]] * hits)
            delivered += hits
        return delivered

    def messages(self, client):
        self._client(client)
        out, self.inbox[client] = self.inbox[client], []
        return out
''',
    tests=[
        [["PubSub", "subscribe", "psubscribe", "publish", "publish", "messages", "messages"],
         [[], ["c1", "news"], ["c1", "n*"], ["news", "hi"], ["chat", "yo"], ["c1"], ["c1"]]],
        [["PubSub", "publish", "messages", "unsubscribe"], [[], ["news", "x"], ["c1"], ["c1", "news"]]],
        [["PubSub", "publish", "subscribe", "publish", "unsubscribe", "publish", "messages"],
         [[], ["news", "early"], ["c1", "news"], ["news", "live"], ["c1", "news"], ["news", "late"], ["c1"]]],
        [["PubSub", "subscribe", "subscribe", "subscribe", "publish", "messages", "messages"],
         [[], ["a", "x"], ["a", "x"], ["b", "x"], ["x", "m"], ["a"], ["b"]]],
        [["PubSub", "psubscribe", "psubscribe", "psubscribe", "publish", "publish", "publish", "publish", "messages"],
         [[], ["a", "ch*t"], ["a", "*"], ["a", "news:*"], ["chat", "1"], ["cht", "2"], ["news:", "3"], ["chats", "4"], ["a"]]],
        [["PubSub", "psubscribe", "publish", "publish", "publish", "publish", "messages"],
         [[], ["a", "a*b*c"], ["abc", "1"], ["aXbYc", "2"], ["ac", "3"], ["abcb", "4"], ["a"]]],
        [["PubSub", "psubscribe", "publish", "publish", "messages"],
         [[], ["a", "ab*ba"], ["aba", "1"], ["abba", "2"], ["a"]]],
    ] + [_seq(s, 45, "PubSub", [], _ps_step) for s in range(41, 47)],
    examples=2,
    wrong_solutions=[
        '''class PubSub:
    def __init__(self): self.ch, self.pat, self.inbox = {}, {}, {}
    def _c(self, c): self.ch.setdefault(c, set()); self.pat.setdefault(c, set()); self.inbox.setdefault(c, [])
    def _total(self, c): return len(self.ch[c]) + len(self.pat[c])
    def subscribe(self, c, channel): self._c(c); self.ch[c].add(channel); return self._total(c)
    def psubscribe(self, c, p): self._c(c); self.pat[c].add(p); return self._total(c)
    def unsubscribe(self, c, channel): self._c(c); self.ch[c].discard(channel); return self._total(c)
    def publish(self, channel, message):
        import fnmatch
        n = 0
        for c in self.ch:                     # bug: at most one delivery per client
            if channel in self.ch[c] or any(fnmatch.fnmatchcase(channel, p) for p in self.pat[c]):
                self.inbox[c].append([channel, message]); n += 1
        return n
    def messages(self, c): self._c(c); out, self.inbox[c] = self.inbox[c], []; return out
''',
        '''class PubSub:
    def __init__(self): self.ch, self.log, self.seen = {}, [], {}
    def subscribe(self, c, channel): self.ch.setdefault(c, set()).add(channel); return len(self.ch[c])
    def psubscribe(self, c, p): self.ch.setdefault(c, set()).add(p); return len(self.ch[c])
    def unsubscribe(self, c, channel): self.ch.setdefault(c, set()).discard(channel); return len(self.ch[c])
    def publish(self, channel, message):      # bug: messages are stored and replayed to later subscribers
        self.log.append([channel, message])
        return sum(1 for c in self.ch if channel in self.ch[c])
    def messages(self, c):
        start = self.seen.get(c, 0); self.seen[c] = len(self.log)
        return [m for m in self.log[start:] if m[0] in self.ch.get(c, set())]
''',
    ],
    guide=dict(
        prereqs="The pub/sub part of *Commands in depth: publish/subscribe, sorting, transactions and key expiry*. Basic string methods.",
        intuition="Pub/sub has no memory: publishing is a loop over the subscriptions that exist *right now*, appending to each matching client's inbox. Counting per subscription, not per client, reproduces Redis's behaviour of delivering twice to a client that matches both by name and by pattern.",
        hints=[
            "Keep, per client, a set of channels, a set of patterns and an inbox list.",
            "For a pattern containing `*`: split on `*`; the first piece must be a prefix, the last a suffix, and the middle pieces must appear in order in between.",
            "`publish` adds one inbox entry per matching subscription and returns the total; `messages` returns the inbox and replaces it with an empty list.",
        ],
        brute_force="Store every published message in a global log and filter it per client on `messages`. That delivers messages published before a client subscribed - precisely what pub/sub does not do.",
        approach="""**Dry run:** c1 subscribes to `news` (total 1) and to pattern `n*` (total 2). `publish("news","hi")`: exact match +1, pattern `n*` matches +1 → returns 2, inbox has two copies. `publish("chat","yo")`: no match → 0. `messages("c1")` returns both copies; a second call returns [].

Pattern check for `a*b*c` against `abcb`: prefix `a` ok, suffix `c`? the text ends in `b` → no match.""",
        complexity="`publish` is O(clients × patterns × channel length); the other operations are O(1).",
        pitfalls="Delivering once per client instead of once per subscription. Letting prefix and suffix overlap (`ab*ba` must not match `aba`). Counting a duplicate `subscribe` twice. Keeping messages for clients that subscribe later.",
        follow_up="Add `punsubscribe`. Then contrast with a stream: what state would you need to let a client resume from the last message it saw?",
    ),
),
dict(
    id="redis-stream-groups",
    title="Stream with a Consumer Group and Pending Entries",
    difficulty="Hard",
    pattern="Messaging",
    kind="class",
    entry="MiniStream",
    description=r"""
Implement the core of a Redis stream with consumer groups. Entry ids are strings `"<ms>-<seq>"`.

- `xadd(ms, payload)` - append an entry and return its id. Let the last id be `L-S` (initially none): if
  `ms > L` the new id is `ms-0`; otherwise it is `L-(S+1)` (ids never go backwards). The first entry is `ms-0`.
- `xlen()` - number of entries.
- `create_group(group)` - create a group that starts **before the first entry** (it will receive everything).
  Returns `"OK"`, or `"BUSYGROUP"` if it exists.
- `xreadgroup(group, consumer, count)` - deliver up to `count` entries never delivered to this group, in id
  order. Each becomes **pending** for `consumer` with delivery count 1. Returns `[[id, payload], ...]`.
- `xack(group, id)` - `1` if the id was pending in the group (it is removed), else `0`.
- `xpending(group)` - `[[id, consumer, delivery_count], ...]` in id order.
- `xclaim(group, consumer, ids)` - for each listed id that is pending in the group, set its owner to
  `consumer` and add 1 to its delivery count. Returns the claimed ids in id order.

Ids compare numerically by `ms`, then by `seq`. All groups named in calls other than `create_group` exist.

**Example:** `xadd(5,"a")` → `"5-0"`, `xadd(5,"b")` → `"5-1"`, `xadd(3,"c")` → `"5-2"`, `create_group("g")`,
`xreadgroup("g","c1",2)` → `[["5-0","a"],["5-1","b"]]`, `xack("g","5-0")` → `1`,
`xclaim("g","c2",["5-1","9-9"])` → `["5-1"]`, `xpending("g")` → `[["5-1","c2",2]]`
""",
    starter='''class MiniStream:
    def __init__(self):
        pass

    def xadd(self, ms: int, payload: str) -> str:
        pass

    def xlen(self) -> int:
        pass

    def create_group(self, group: str) -> str:
        pass

    def xreadgroup(self, group: str, consumer: str, count: int) -> List[List[str]]:
        pass

    def xack(self, group: str, entry_id: str) -> int:
        pass

    def xpending(self, group: str) -> List[list]:
        pass

    def xclaim(self, group: str, consumer: str, ids: List[str]) -> List[str]:
        pass
''',
    solution='''class MiniStream:
    def __init__(self):
        self.entries = []          # (ms, seq, payload) in id order
        self.groups = {}           # group -> {"next": index of next undelivered entry, "pending": {(ms, seq): [consumer, n]}}

    @staticmethod
    def _fmt(key):
        return "%d-%d" % key

    @staticmethod
    def _parse(text):
        a, b = text.split("-")
        return (int(a), int(b))

    def xadd(self, ms, payload):
        if self.entries and ms <= self.entries[-1][0]:
            key = (self.entries[-1][0], self.entries[-1][1] + 1)
        else:
            key = (ms, 0)
        self.entries.append((key[0], key[1], payload))
        return self._fmt(key)

    def xlen(self):
        return len(self.entries)

    def create_group(self, group):
        if group in self.groups:
            return "BUSYGROUP"
        self.groups[group] = {"next": 0, "pending": {}}
        return "OK"

    def xreadgroup(self, group, consumer, count):
        g = self.groups[group]
        batch = self.entries[g["next"]:g["next"] + count]
        g["next"] += len(batch)
        for ms, seq, _ in batch:
            g["pending"][(ms, seq)] = [consumer, 1]
        return [[self._fmt((ms, seq)), payload] for ms, seq, payload in batch]

    def xack(self, group, entry_id):
        return 1 if self.groups[group]["pending"].pop(self._parse(entry_id), None) is not None else 0

    def xpending(self, group):
        p = self.groups[group]["pending"]
        return [[self._fmt(k), p[k][0], p[k][1]] for k in sorted(p)]

    def xclaim(self, group, consumer, ids):
        p = self.groups[group]["pending"]
        keys = sorted({self._parse(i) for i in ids} & set(p))
        for k in keys:
            p[k][0] = consumer
            p[k][1] += 1
        return [self._fmt(k) for k in keys]
''',
    tests=[
        [["MiniStream", "xadd", "xadd", "xadd", "create_group", "xreadgroup", "xack", "xclaim", "xpending"],
         [[], [5, "a"], [5, "b"], [3, "c"], ["g"], ["g", "c1", 2], ["g", "5-0"], ["g", "c2", ["5-1", "9-9"]], ["g"]]],
        [["MiniStream", "xlen", "create_group", "create_group", "xreadgroup", "xpending", "xack"],
         [[], [], ["g"], ["g"], ["g", "c1", 5], ["g"], ["g", "1-0"]]],
        [["MiniStream", "xadd", "create_group", "xreadgroup", "xreadgroup", "xadd", "xreadgroup", "xpending"],
         [[], [1, "a"], ["g"], ["g", "c1", 10], ["g", "c2", 10], [2, "b"], ["g", "c2", 10], ["g"]]],
        [["MiniStream", "xadd", "xadd", "create_group", "create_group", "xreadgroup", "xreadgroup", "xack", "xpending", "xpending"],
         [[], [1, "a"], [2, "b"], ["g1"], ["g2"], ["g1", "c", 1], ["g2", "c", 2], ["g1", "1-0"], ["g1"], ["g2"]]],
        [["MiniStream", "xadd", "xadd", "xadd", "xadd", "xlen", "create_group", "xreadgroup", "xpending"],
         [[], [0, "a"], [0, "b"], [10, "c"], [9, "d"], [], ["g"], ["g", "c", 4], ["g"]]],
        [["MiniStream", "xadd", "xadd", "xadd", "create_group", "xreadgroup", "xclaim", "xclaim", "xack", "xack", "xpending"],
         [[], [2, "a"], [10, "b"], [10, "c"], ["g"], ["g", "c1", 3], ["g", "c2", ["10-1", "2-0"]],
          ["g", "c1", ["10-1", "10-1"]], ["g", "10-0"], ["g", "10-0"], ["g"]]],
    ] + [_seq(s, 50, "MiniStream", [], lambda rng, st: ("create_group", ["g"]) if not st.get("made") and not st.update(made=1)
               else _stream_step(rng, st)) for s in range(51, 57)],
    examples=2,
    wrong_solutions=[
        '''class MiniStream:
    def __init__(self): self.entries, self.groups = [], {}
    def xadd(self, ms, payload):
        if self.entries and ms <= self.entries[-1][0]: key = (self.entries[-1][0], self.entries[-1][1] + 1)
        else: key = (ms, 0)
        self.entries.append((key[0], key[1], payload)); return "%d-%d" % key
    def xlen(self): return len(self.entries)
    def create_group(self, group):
        if group in self.groups: return "BUSYGROUP"
        self.groups[group] = {}; return "OK"
    def xreadgroup(self, group, consumer, count):       # bug: no delivery position, re-delivers from the start
        batch = self.entries[:count]
        for ms, seq, _ in batch: self.groups[group][(ms, seq)] = [consumer, 1]
        return [["%d-%d" % (ms, seq), p] for ms, seq, p in batch]
    def xack(self, group, entry_id):
        a, b = entry_id.split("-")
        return 1 if self.groups[group].pop((int(a), int(b)), None) is not None else 0
    def xpending(self, group):
        p = self.groups[group]; return [["%d-%d" % k, p[k][0], p[k][1]] for k in sorted(p)]
    def xclaim(self, group, consumer, ids):
        p = self.groups[group]; keys = sorted({tuple(map(int, i.split("-"))) for i in ids} & set(p))
        for k in keys: p[k][0] = consumer; p[k][1] += 1
        return ["%d-%d" % k for k in keys]
''',
        '''class MiniStream:
    def __init__(self): self.entries, self.groups = [], {}
    def xadd(self, ms, payload):
        seq = sum(1 for e in self.entries if e[0] == ms)          # bug: ids can go backwards
        self.entries.append((ms, seq, payload)); return "%d-%d" % (ms, seq)
    def xlen(self): return len(self.entries)
    def create_group(self, group):
        if group in self.groups: return "BUSYGROUP"
        self.groups[group] = {"next": 0, "pending": {}}; return "OK"
    def xreadgroup(self, group, consumer, count):
        g = self.groups[group]; batch = self.entries[g["next"]:g["next"] + count]; g["next"] += len(batch)
        for ms, seq, _ in batch: g["pending"][(ms, seq)] = [consumer, 1]
        return [["%d-%d" % (ms, seq), p] for ms, seq, p in batch]
    def xack(self, group, entry_id):
        a, b = entry_id.split("-")
        return 1 if self.groups[group]["pending"].pop((int(a), int(b)), None) is not None else 0
    def xpending(self, group):
        p = self.groups[group]["pending"]; return [["%d-%d" % k, p[k][0], p[k][1]] for k in sorted(p)]
    def xclaim(self, group, consumer, ids):
        p = self.groups[group]["pending"]; keys = sorted({tuple(map(int, i.split("-"))) for i in ids} & set(p))
        for k in keys: p[k][0] = consumer; p[k][1] += 1
        return ["%d-%d" % k for k in keys]
''',
    ],
    guide=dict(
        prereqs="The lesson *Modern Redis: streams and consumer groups* (ids, `XREADGROUP`, `XACK`, pending entries, claiming).",
        intuition="A stream is an append-only list, so the entries themselves never move. A consumer group is only bookkeeping on top: a **cursor** saying how far into the list the group has delivered, and a **pending table** of entries handed out but not yet acknowledged, each with its owner and delivery count. Reading advances the cursor and adds to the table; acknowledging removes from the table; claiming changes the owner.",
        hints=[
            "Store ids as `(ms, seq)` tuples so they compare numerically; format them as text only in return values.",
            "For `xadd`: if `ms` is not greater than the last entry's `ms`, reuse the last `ms` and add 1 to its `seq`.",
            "Per group keep `next` (an index into the entry list) and `pending` (a dictionary from id tuple to `[consumer, count]`).",
        ],
        brute_force="For each `xreadgroup`, scan all entries and skip those the group has already seen (kept in a set): O(n) per read instead of O(count).",
        approach="""**Dry run:** `xadd(5,"a")` → 5-0. `xadd(5,"b")`: 5 is not > 5 → 5-1. `xadd(3,"c")`: 3 is not > 5 → 5-2. `create_group("g")` → next = 0. `xreadgroup("g","c1",2)` → entries 0 and 1; next = 2; pending {5-0: [c1,1], 5-1: [c1,1]}. `xack("g","5-0")` → 1. `xclaim("g","c2",["5-1","9-9"])`: only 5-1 is pending → owner c2, count 2 → ["5-1"].""",
        complexity="`xadd` O(1); `xreadgroup` O(count); `xack` O(1); `xpending` O(p log p); `xclaim` O(k log k).",
        pitfalls="Comparing ids as strings (`\"10-0\" < \"9-0\"` as text). Generating an id smaller than the previous one when the clock goes backwards. Re-delivering already delivered entries on the next read. Sharing one pending table between groups. Claiming an id that is not pending.",
        follow_up="Add idle times and `xautoclaim(group, consumer, min_idle, now)`. Add `xtrim(maxlen)` and decide what happens to pending ids whose entries were trimmed.",
    ),
),
dict(
    id="redis-autocomplete",
    title="Prefix Autocomplete over a Sorted Structure",
    difficulty="Medium",
    pattern="Sorted sets",
    kind="class",
    entry="Autocomplete",
    description=r"""
Implement the autocomplete that Redis provides with an equal-score sorted set and `ZRANGE ... BYLEX`.

All words are stored and compared in **lower case**.

- `add(word)` - returns `1` if the word is new, `0` if it was already stored.
- `remove(word)` - returns `1` if it was stored, else `0`.
- `suggest(prefix, limit)` - up to `limit` stored words that start with `prefix`, in ascending lexicographic
  order. An empty prefix matches every word.
- `count(prefix)` - how many stored words start with `prefix`.

`suggest` and `count` must not scan every stored word: use binary search to find where the prefix range begins.
Words and prefixes contain only letters.

**Example:** add `"Manchester"`, `"mannheim"`, `"madrid"`, `"milan"` → `suggest("MAN", 5)` is
`["manchester","mannheim"]`, `suggest("m", 2)` is `["madrid","manchester"]`, `count("ma")` is `3`
""",
    starter='''class Autocomplete:
    def __init__(self):
        pass

    def add(self, word: str) -> int:
        pass

    def remove(self, word: str) -> int:
        pass

    def suggest(self, prefix: str, limit: int) -> List[str]:
        pass

    def count(self, prefix: str) -> int:
        pass
''',
    solution='''class Autocomplete:
    def __init__(self):
        self.words = []          # sorted, unique, lower case

    def _range(self, prefix):
        prefix = prefix.lower()
        lo = bisect.bisect_left(self.words, prefix)
        hi = bisect.bisect_left(self.words, prefix + "{")     # "{" sorts right after "z"
        return lo, hi

    def add(self, word):
        word = word.lower()
        i = bisect.bisect_left(self.words, word)
        if i < len(self.words) and self.words[i] == word:
            return 0
        self.words.insert(i, word)
        return 1

    def remove(self, word):
        word = word.lower()
        i = bisect.bisect_left(self.words, word)
        if i < len(self.words) and self.words[i] == word:
            self.words.pop(i)
            return 1
        return 0

    def suggest(self, prefix, limit):
        lo, hi = self._range(prefix)
        return self.words[lo:min(hi, lo + max(limit, 0))]

    def count(self, prefix):
        lo, hi = self._range(prefix)
        return hi - lo
''',
    tests=[
        [["Autocomplete", "add", "add", "add", "add", "suggest", "suggest", "count"],
         [[], ["Manchester"], ["mannheim"], ["madrid"], ["milan"], ["MAN", 5], ["m", 2], ["ma"]]],
        [["Autocomplete", "suggest", "count", "remove"], [[], ["a", 3], [""], ["a"]]],
        [["Autocomplete", "add", "add", "add", "remove", "remove", "suggest", "count"],
         [[], ["Oslo"], ["oslo"], ["OSLO"], ["osLO"], ["oslo"], ["o", 5], ["o"]]],
        [["Autocomplete", "add", "add", "add", "suggest", "suggest", "suggest", "count", "count"],
         [[], ["ma"], ["man"], ["mango"], ["man", 0], ["man", 1], ["mang", 9], ["m"], ["mz"]]],
        [["Autocomplete", "add", "add", "add", "add", "suggest", "suggest", "count"],
         [[], ["roman"], ["many"], ["human"], ["man"], ["man", 9], ["", 9], [""]]],
        [["Autocomplete", "add", "add", "add", "suggest", "count", "suggest"],
         [[], ["az"], ["b"], ["azz"], ["az", 9], ["a"], ["z", 3]]],
    ] + [_seq(s, 45, "Autocomplete", [], _ac_step) for s in range(61, 67)],
    examples=2,
    wrong_solutions=[
        '''class Autocomplete:
    def __init__(self): self.words = set()
    def add(self, word):
        w = word.lower(); new = w not in self.words; self.words.add(w); return int(new)
    def remove(self, word):
        w = word.lower(); had = w in self.words; self.words.discard(w); return int(had)
    def suggest(self, prefix, limit):               # bug: substring match
        return sorted(w for w in self.words if prefix.lower() in w)[:max(limit, 0)]
    def count(self, prefix): return sum(1 for w in self.words if prefix.lower() in w)
''',
        '''class Autocomplete:
    def __init__(self): self.words = []
    def add(self, word):
        if word in self.words: return 0             # bug: case is not normalised, order is insertion
        self.words.append(word); return 1
    def remove(self, word):
        if word in self.words: self.words.remove(word); return 1
        return 0
    def suggest(self, prefix, limit): return [w for w in self.words if w.startswith(prefix)][:max(limit, 0)]
    def count(self, prefix): return sum(1 for w in self.words if w.startswith(prefix))
''',
    ],
    guide=dict(
        prereqs="`bisect`. The autocomplete section of *Autocomplete, distributed locks and counting semaphores* (BYLEX prefix ranges).",
        intuition="In sorted order, all words sharing a prefix sit next to each other. So the answer is one contiguous slice: it starts at the first word that is `>= prefix` and ends before the first word that is beyond every string starting with the prefix. That upper bound is the prefix followed by a character larger than any letter - the same trick as `(prefix\\xff` in Redis.",
        hints=[
            "Keep the words in a sorted list of unique lower-case strings; use `bisect_left` to find where a word is or should be.",
            "Lower bound: `bisect_left(words, prefix)`. Upper bound: `bisect_left(words, prefix + \"{\")`, because `{` comes right after `z`.",
            "`count` is `hi - lo`; `suggest` is the slice from `lo`, cut at `hi` and at `limit` items.",
        ],
        brute_force="Filter every stored word with `startswith` and sort the matches: O(n) per keystroke, which is too slow for tens of thousands of words typed against many times a second.",
        approach="""**Dry run:** stored (sorted): madrid, manchester, mannheim, milan. `suggest("MAN",5)`: prefix `man`; lo = index of first word >= `man` = 1; hi = first word >= `man{` = 3 → slice [1:3] = manchester, mannheim. `count("ma")`: lo 0, hi 3 → 3. `suggest("m",2)` → slice [0:4] cut to 2.""",
        complexity="`suggest` and `count` are O(log n + results). `add` and `remove` are O(log n) to locate plus O(n) to shift the list; a sorted set does both in O(log n).",
        pitfalls="Matching substrings instead of prefixes. Forgetting to lower-case both stored words and the query. Using `prefix + \"z\"` as the upper bound (it misses words like `manzz...`). A negative or zero limit. Returning duplicates when the same word is added in different capitalisation.",
        follow_up="Rank suggestions by popularity: keep a small sorted set per prefix scored by use count, and compare its memory with this layout.",
    ),
),
]
