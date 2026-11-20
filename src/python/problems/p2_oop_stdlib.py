"""Python Mastery problems: OOP, context managers, standard library, asyncio, files & regex."""
import random

# ---------------------------------------------------------------- py-vector
VEC_DRIVER = '''

# ---- driver (do not edit) ----
def run(a, b, k):
    v, w = Vector(*a), Vector(*b)

    def attempt(fn):
        try:
            fn()
            return "no error"
        except Exception as e:
            return type(e).__name__

    return [
        list(v + w), list(v - w), list(v * k), list(k * v), list(-v),
        v @ w, abs(v), len(v), v[0], v[-1],
        v == Vector(*a), v == w, v == list(a),
        hash(v) == hash(Vector(*a)), len({v, Vector(*a), w}),
        bool(v), bool(Vector(*([0] * len(a)))),
        repr(v),
        attempt(lambda: v + Vector(*a, 1)),
        attempt(lambda: v + 1),
        attempt(lambda: setattr(v, "x", 1) or v.__setitem__(0, 9)),
        type(v + w).__name__,
    ]
'''

VEC_SOLUTION = '''import math

class Vector:
    __slots__ = ("_c",)

    def __init__(self, *coords):
        self._c = tuple(coords)

    def __len__(self):
        return len(self._c)

    def __getitem__(self, i):
        return self._c[i]

    def __iter__(self):
        return iter(self._c)

    def __repr__(self):
        return "Vector(" + ", ".join(repr(x) for x in self._c) + ")"

    def __eq__(self, other):
        if not isinstance(other, Vector):
            return NotImplemented
        return self._c == other._c

    def __hash__(self):
        return hash(self._c)

    def __bool__(self):
        return any(x != 0 for x in self._c)

    def _check(self, other):
        if len(self) != len(other):
            raise ValueError("dimension mismatch")

    def __add__(self, other):
        if not isinstance(other, Vector):
            return NotImplemented
        self._check(other)
        return Vector(*(x + y for x, y in zip(self, other)))

    def __sub__(self, other):
        if not isinstance(other, Vector):
            return NotImplemented
        self._check(other)
        return Vector(*(x - y for x, y in zip(self, other)))

    def __neg__(self):
        return Vector(*(-x for x in self))

    def __mul__(self, k):
        if not isinstance(k, (int, float)):
            return NotImplemented
        return Vector(*(x * k for x in self))

    __rmul__ = __mul__

    def __matmul__(self, other):
        if not isinstance(other, Vector):
            return NotImplemented
        self._check(other)
        return sum(x * y for x, y in zip(self, other))

    def __abs__(self):
        return math.sqrt(sum(x * x for x in self))
''' + VEC_DRIVER

# ---------------------------------------------------------------- py-temperature
TEMP_DRIVER = '''

# ---- driver (do not edit) ----
def run(start_celsius, ops):
    out = []
    try:
        t = Temperature(start_celsius)
    except ValueError:
        return ["ValueError"]
    for op in ops:
        name, value = op[0], (op[1] if len(op) > 1 else None)
        try:
            if name == "get":
                out.append([t.celsius, t.fahrenheit, t.kelvin])
            elif name == "set_c":
                t.celsius = value
                out.append("ok")
            elif name == "set_f":
                t.fahrenheit = value
                out.append("ok")
            elif name == "set_k":
                t.kelvin = value
                out.append("ok")
            elif name == "repr":
                out.append(repr(t))
        except ValueError:
            out.append("ValueError")
        except AttributeError:
            out.append("AttributeError")
    return out
'''

TEMP_SOLUTION = '''class Temperature:
    ABSOLUTE_ZERO = -273.15

    def __init__(self, celsius=0.0):
        self.celsius = celsius          # goes through the validating setter

    @property
    def celsius(self):
        return self._celsius

    @celsius.setter
    def celsius(self, value):
        if value < self.ABSOLUTE_ZERO:
            raise ValueError("temperature below absolute zero")
        self._celsius = float(value)

    @property
    def fahrenheit(self):
        return self._celsius * 9 / 5 + 32

    @fahrenheit.setter
    def fahrenheit(self, value):
        self.celsius = (value - 32) * 5 / 9

    @property
    def kelvin(self):
        return self._celsius - self.ABSOLUTE_ZERO

    @kelvin.setter
    def kelvin(self, value):
        self.celsius = value + self.ABSOLUTE_ZERO

    def __repr__(self):
        return f"Temperature({self._celsius:.2f})"
''' + TEMP_DRIVER

# ---------------------------------------------------------------- py-dataclass-sort
DS_DRIVER = '''

# ---- driver (do not edit) ----
import dataclasses as _dc

def run(rows):
    players = [Player(name=n, score=s, team=t) for n, s, t in rows]
    ranked = sorted(players)
    same = Player(name="x", score=1, team="red") == Player(name="x", score=1, team="blue")
    best = max(players).name if players else None       # max() = LAST in ranking order
    return [
        [[p.name, p.score, p.team] for p in ranked],
        _dc.is_dataclass(Player),
        same,
        best,
        "Player(" in repr(Player(name="x", score=1, team="red")),
    ]
'''

DS_SOLUTION = '''from dataclasses import dataclass, field

@dataclass(order=True)
class Player:
    sort_key: tuple = field(init=False, repr=False)
    name: str = field(compare=False)
    score: int = field(compare=False)
    team: str = field(compare=False)

    def __post_init__(self):
        self.sort_key = (-self.score, self.name)
''' + DS_DRIVER

# ---------------------------------------------------------------- py-timer
TIMER_DRIVER = '''

# ---- driver (do not edit) ----
def run(times, failing_blocks):
    clock = iter(times).__next__            # fake clock: each call returns the next reading
    timer = Timer(clock)
    escaped = 0
    entered_self = True
    for i in range(len(times) // 2):
        try:
            with timer as t:
                entered_self = entered_self and (t is timer)
                if i in failing_blocks:
                    raise RuntimeError("boom")
        except RuntimeError:
            escaped += 1
    return [timer.laps, timer.total, timer.elapsed, escaped, entered_self]
'''

TIMER_SOLUTION = '''import time

class Timer:
    def __init__(self, clock=time.perf_counter):
        self._clock = clock
        self._start = None
        self.laps = []
        self.elapsed = None

    @property
    def total(self):
        return sum(self.laps)

    def __enter__(self):
        self._start = self._clock()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.elapsed = self._clock() - self._start
        self.laps.append(self.elapsed)
        return False                    # never swallow exceptions
''' + TIMER_DRIVER

# ---------------------------------------------------------------- py-suppress-log
SL_DRIVER = '''

# ---- driver (do not edit) ----
def run(type_names, actions):
    table = {"ValueError": ValueError, "KeyError": KeyError, "LookupError": LookupError,
             "IndexError": IndexError, "TypeError": TypeError, "ZeroDivisionError": ZeroDivisionError,
             "ArithmeticError": ArithmeticError}
    ctx = SuppressAndLog(*[table[n] for n in type_names])
    escaped, reached = [], []
    for i, action in enumerate(actions):
        try:
            with ctx as got:
                assert got is ctx, "__enter__ must return the context manager itself"
                if action != "ok":
                    raise table[action](f"step {i}")
                reached.append(i)
        except Exception as e:
            escaped.append(type(e).__name__)
    return [ctx.errors, escaped, reached]
'''

SL_SOLUTION = '''class SuppressAndLog:
    def __init__(self, *exc_types):
        self.exc_types = exc_types
        self.errors = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None and issubclass(exc_type, self.exc_types):
            self.errors.append(f"{exc_type.__name__}: {exc}")
            return True                 # suppress
        return False
''' + SL_DRIVER

# ---------------------------------------------------------------- py-async-gather
AG_DRIVER = '''

# ---- driver (do not edit) ----
import asyncio as _asyncio

def run(jobs, limit):
    state = {"active": 0, "peak": 0, "started": []}

    def make(i, delay, value):
        async def job():
            state["active"] += 1
            state["peak"] = max(state["peak"], state["active"])
            state["started"].append(i)
            await _asyncio.sleep(delay / 1000)
            state["active"] -= 1
            if value == "fail":
                raise ValueError(f"job {i} failed")
            return value
        return job

    factories = [make(i, d, v) for i, (d, v) in enumerate(jobs)]
    results = _asyncio.run(run_limited(factories, limit))
    shown = [f"error: {r}" if isinstance(r, Exception) else r for r in results]
    return [shown, state["peak"], sorted(state["started"]) == list(range(len(jobs)))]
'''

AG_SOLUTION = '''import asyncio

async def run_limited(factories, limit):
    sem = asyncio.Semaphore(limit)

    async def guarded(factory):
        async with sem:
            return await factory()

    return await asyncio.gather(*(guarded(f) for f in factories), return_exceptions=True)
''' + AG_DRIVER


def _lru_case(seed, n_ops, cap, key_space):
    rnd = random.Random(seed)
    ops, args = ["LRUCache"], [[cap]]
    for _ in range(n_ops):
        if rnd.random() < 0.55:
            ops.append("put"); args.append([rnd.randrange(key_space), rnd.randrange(1000)])
        else:
            ops.append("get"); args.append([rnd.randrange(key_space)])
    return [ops, args]


def _kth_case(seed, k, n0, n_add):
    rnd = random.Random(seed)
    ops = ["KthLargest"] + ["add"] * n_add
    args = [[k, [rnd.randrange(-1000, 1000) for _ in range(n0)]]] + [[rnd.randrange(-1000, 1000)] for _ in range(n_add)]
    return [ops, args]


def _sorted_lists(seed, k, max_len):
    rnd = random.Random(seed)
    return [sorted(rnd.randrange(-500, 500) for _ in range(rnd.randrange(0, max_len))) for _ in range(k)]


_LOG_SAMPLE = [
    "2026-01-02 10:00:01 [INFO] auth: login ok (user=17)",
    "2026-01-02 10:00:05 [ERROR] auth: bad token (user=42)",
    "2026-01-02 10:00:09 [WARNING] db: slow query took 2.5s",
    "this line is garbage",
    "2026-01-02 10:01:00 [ERROR] db: connection reset (user=7)",
    "2026-01-02 10:01:02 [ERROR] auth: bad token (user=42)",
    "2026-01-02 10:02:30 [DEBUG] cache: miss key=abc",
]


def _log_lines(seed, n):
    rnd = random.Random(seed)
    levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    mods = ["auth", "db", "cache", "api_v2", "worker"]
    out = []
    for i in range(n):
        r = rnd.random()
        if r < 0.08:
            out.append(rnd.choice(["", "garbage", "2026-13-45 nope", "[ERROR] no timestamp: x",
                                   "2026-01-02 10:00:01 [error] auth: lowercase level",
                                   "2026-01-02 10:00:01 ERROR auth: no brackets"]))
            continue
        user = f" (user={rnd.randrange(1, 60)})" if rnd.random() < 0.6 else ""
        out.append(f"2026-01-{rnd.randrange(1, 29):02d} {rnd.randrange(24):02d}:{rnd.randrange(60):02d}:{rnd.randrange(60):02d} "
                   f"[{rnd.choice(levels)}] {rnd.choice(mods)}: event {i}{user}")
    return out


_JSON_DOC = {
    "user": {"name": "Robin", "tags": ["archaeologist", "reader"], "address": {"city": "Ohara", "zip": None}},
    "orders": [{"id": 1, "items": [{"sku": "A1", "qty": 2}, {"sku": "B2", "qty": 0}]}, {"id": 2, "items": []}],
    "count": 0,
    "flag": False,
    "matrix": [[1, 2], [3, 4]],
    "": {"empty": "key"},
}


PROBLEMS = [
# =====================================================================================
dict(
    id="py-vector",
    title="Vector Class with Dunder Methods",
    difficulty="Medium",
    pattern="Data Model",
    entry="run",
    compare="float",
    description=r"""
Implement an **immutable, hashable** `Vector` class constructed as `Vector(1, 2, 3)` that integrates
with Python's operators:

| Expression | Result |
|---|---|
| `v + w`, `v - w` | new `Vector` (element-wise); `ValueError` if lengths differ |
| `v * k`, `k * v` | new `Vector` scaled by the number `k` |
| `-v` | negated `Vector` |
| `v @ w` | dot product (a number); `ValueError` if lengths differ |
| `abs(v)` | Euclidean length (float) |
| `len(v)`, `v[i]`, `for x in v` | sequence behaviour (negative indices work) |
| `v == w` | `True` iff `w` is a `Vector` with equal coordinates (a list is **not** equal) |
| `hash(v)` | equal vectors hash equally (usable in sets / as dict keys) |
| `bool(v)` | `False` iff all coordinates are zero |
| `repr(v)` | `"Vector(1, 2, 3)"` |

Rules: `v + 1` (or any non-Vector operand) must raise `TypeError` — do this by returning
`NotImplemented`. Vectors are immutable: `v[0] = 9` (and ideally any attribute assignment) must fail.

The driver `run(a, b, k)` (do not edit) builds `Vector(*a)` and `Vector(*b)` and returns a list of results.

**Example:** `a = [1, 2, 3], b = [4, 5, 6], k = 2` → starts with `[[5,7,9], [-3,-3,-3], [2,4,6], [2,4,6], [-1,-2,-3], 32, 3.7416..., 3, ...]`
""",
    starter='''import math

class Vector:
    def __init__(self, *coords):
        pass

    def __repr__(self):
        pass

    # add: __len__, __getitem__, __iter__, __eq__, __hash__, __bool__,
    #      __add__, __sub__, __neg__, __mul__, __rmul__, __matmul__, __abs__
''' + VEC_DRIVER,
    solution=VEC_SOLUTION,
    tests=[
        [[1, 2, 3], [4, 5, 6], 2],
        [[0, 0], [3, 4], 5],
        [[3, 4], [0, 0], -1],
        [[7], [7], 0],
        [[1.5, -2.5], [0.5, 2.5], 2],
        [[1, 2, 3, 4, 5], [5, 4, 3, 2, 1], 0.5],
        [[-1, -1, -1], [-1, -1, -1], 3],
        [[0, 0, 0], [0, 0, 0], 9],
        [[10**6, -10**6], [1, 1], 10],
        [list(range(50)), list(range(50, 100)), 3],
    ],
    examples=2,
    wrong_solutions=[
        '''import math
class Vector:
    def __init__(self, *coords): self._c = list(coords)
    def __len__(self): return len(self._c)
    def __getitem__(self, i): return self._c[i]
    def __setitem__(self, i, x): self._c[i] = x
    def __iter__(self): return iter(self._c)
    def __repr__(self): return "Vector(" + ", ".join(map(repr, self._c)) + ")"
    def __eq__(self, o): return list(self) == list(o)
    def __hash__(self): return hash(tuple(self._c))
    def __bool__(self): return any(self._c)
    def __add__(self, o): return Vector(*(x + y for x, y in zip(self, o)))
    def __sub__(self, o): return Vector(*(x - y for x, y in zip(self, o)))
    def __neg__(self): return Vector(*(-x for x in self))
    def __mul__(self, k): return Vector(*(x * k for x in self))
    __rmul__ = __mul__
    def __matmul__(self, o): return sum(x * y for x, y in zip(self, o))
    def __abs__(self): return math.sqrt(sum(x * x for x in self))
''' + VEC_DRIVER,
    ],
    guide=dict(
        prereqs="Lesson *The data model: dunder methods*; hashing rules from *Dictionaries and sets*.",
        intuition="Each operator maps to one special method. Store the coordinates in a tuple (immutable, hashable), and let binary operators return `NotImplemented` for foreign types so Python raises `TypeError` for you.",
        hints=[
            "Store `self._c = tuple(coords)`; implement `__len__`, `__getitem__`, `__iter__` by delegating to it.",
            "`__eq__` should return `NotImplemented` for non-Vectors; `__hash__` returns `hash(self._c)`.",
            "`__rmul__ = __mul__` makes `2 * v` work. `@` is `__matmul__`.",
            "Don't define `__setitem__`; `__slots__ = ('_c',)` additionally blocks new attributes.",
        ],
        brute_force="A mutable list-backed vector with permissive operators 'works' for the happy path but fails hashing safety, type errors, dimension checks and equality with lists.",
        approach="""1. Storage: tuple in `_c`, `__slots__`.
2. Sequence protocol: `__len__`, `__getitem__`, `__iter__`.
3. `__repr__` via `', '.join(repr(x) ...)`.
4. `__eq__`/`__hash__` on the tuple.
5. Arithmetic: check `isinstance(other, Vector)` → else `NotImplemented`; check lengths → `ValueError`; build a new `Vector` with `zip`.
6. `__abs__` = `sqrt(sum(x*x))`, `__bool__` = `any(...)`.""",
        complexity="All operations O(d) for dimension d.",
        pitfalls="""- `zip` silently truncates on length mismatch — check lengths yourself.
- Defining `__eq__` without `__hash__` makes the class unhashable.
- Comparing equal to plain lists breaks the `==`/hash contract expectations.
- Raising `TypeError` manually works, but returning `NotImplemented` is the protocol (it lets the other operand try).""",
        follow_up="Add `__format__` for `f'{v:.2f}'`, slicing that returns a `Vector`, and `functools.total_ordering` by magnitude.",
    ),
),
# =====================================================================================
dict(
    id="py-temperature",
    title="Temperature with Validating Properties",
    difficulty="Easy",
    pattern="Properties",
    entry="run",
    compare="float",
    description=r"""
Implement `class Temperature` storing a temperature internally in Celsius and exposing three
**properties** that stay consistent with each other:

- `celsius` (get/set)
- `fahrenheit` (get/set) — `F = C × 9/5 + 32`
- `kelvin` (get/set) — `K = C + 273.15`

Any assignment (including in the constructor `Temperature(celsius)`) that would put the temperature
below absolute zero (−273.15 °C) raises `ValueError` and leaves the object unchanged.
`repr(t)` is `"Temperature(21.50)"` (Celsius with two decimals).

The driver `run(start_celsius, ops)` (do not edit) applies operations such as `["set_f", 212]`,
`["get"]` (→ `[celsius, fahrenheit, kelvin]`) and `["repr"]`.

**Example:** `start = 0, ops = [["get"], ["set_f", 212], ["get"]]` → `[[0.0, 32.0, 273.15], "ok", [100.0, 212.0, 373.15]]`
""",
    starter='''class Temperature:
    def __init__(self, celsius=0.0):
        pass

    @property
    def celsius(self):
        pass
''' + TEMP_DRIVER,
    solution=TEMP_SOLUTION,
    tests=[
        [0, [["get"], ["set_f", 212], ["get"]]],
        [21.5, [["repr"], ["get"]]],
        [-300, [["get"]]],
        [10, [["set_c", -274], ["get"], ["set_k", -1], ["get"], ["set_f", -500], ["get"]]],
        [-273.15, [["get"], ["set_k", 0], ["get"], ["repr"]]],
        [100, [["set_k", 0], ["get"], ["set_k", 300], ["get"], ["repr"]]],
        [37, [["set_f", 98.6], ["get"], ["set_c", 36.6], ["get"], ["set_f", -40], ["get"]]],
        [0, []],
        [5, [["set_c", 5], ["set_c", 6], ["set_c", -273.15], ["get"], ["repr"]]],
        [1e6, [["get"], ["set_k", 1], ["repr"]]],
    ],
    examples=2,
    wrong_solutions=['''class Temperature:
    def __init__(self, celsius=0.0):
        if celsius < -273.15:
            raise ValueError
        self.celsius = float(celsius)
    @property
    def fahrenheit(self): return self.celsius * 9 / 5 + 32
    @fahrenheit.setter
    def fahrenheit(self, v): self.celsius = (v - 32) * 5 / 9
    @property
    def kelvin(self): return self.celsius + 273.15
    @kelvin.setter
    def kelvin(self, v): self.celsius = v - 273.15
    def __repr__(self): return f"Temperature({self.celsius:.2f})"
''' + TEMP_DRIVER],
    guide=dict(
        prereqs="Properties (lesson *Properties, dataclasses, ABCs and composition*).",
        intuition="Keep one source of truth (`_celsius`) and funnel *every* write through one validating setter. The other two properties are just conversions that delegate to it.",
        hints=[
            "In `__init__`, assign `self.celsius = celsius` so the setter validates the initial value too.",
            "The `celsius` setter checks `value < -273.15` and stores into `self._celsius`.",
            "`fahrenheit` and `kelvin` setters convert and then assign to `self.celsius`.",
        ],
        brute_force="Three independent attributes updated by hand get out of sync immediately — the reason properties exist.",
        approach="""```
@property
def celsius(self): return self._celsius
@celsius.setter
def celsius(self, v):
    if v < -273.15: raise ValueError(...)
    self._celsius = float(v)
```
`fahrenheit`/`kelvin` getters compute from `_celsius`; their setters convert to Celsius and reuse the validated setter.""",
        complexity="O(1) everything.",
        pitfalls="""- Validating only in `__init__` lets `t.celsius = -500` slip through (the wrong solution).
- Storing to `self.celsius` inside its own setter recurses forever; use `_celsius`.
- Validate *before* assigning so a failed set leaves the old value intact.""",
        follow_up="Make the class immutable and return new instances; add ordering with `functools.total_ordering`.",
    ),
),
# =====================================================================================
dict(
    id="py-dataclass-sort",
    title="Leaderboard Ordering with a Dataclass",
    difficulty="Medium",
    pattern="Dataclasses",
    entry="run",
    description=r"""
Define a **dataclass** `Player` with fields `name: str`, `score: int`, `team: str` (constructed with
keyword arguments) whose instances sort into leaderboard order with plain `sorted(players)`:

1. higher `score` first;
2. ties broken by `name` ascending.

`team` must **not** take part in comparisons at all: two players with the same name and score but
different teams are equal (`==`). Use `@dataclass(order=True)` and `field(...)` options — don't write
`__lt__` by hand.

The driver `run(rows)` (do not edit) builds players from `[name, score, team]` rows and returns
`[sorted rows, is_dataclass, equality_ignores_team, max(players).name, repr_ok]`.

**Example:** `[["zoro", 90, "A"], ["nami", 95, "B"], ["brook", 90, "A"]]` → order `nami, brook, zoro`
""",
    starter='''from dataclasses import dataclass, field

@dataclass(order=True)
class Player:
    name: str
    score: int
    team: str
''' + DS_DRIVER,
    solution=DS_SOLUTION,
    tests=[
        [[["zoro", 90, "A"], ["nami", 95, "B"], ["brook", 90, "A"]]],
        [[]],
        [[["solo", 1, "x"]]],
        [[["a", 5, "t1"], ["a", 5, "t2"], ["b", 5, "t0"]]],
        [[["b", 1, "x"], ["a", 2, "x"], ["c", 3, "x"]]],
        [[["x", -5, "r"], ["y", 0, "r"], ["w", -5, "b"]]],
        [[["Bob", 10, "t"], ["alice", 10, "t"], ["Carl", 10, "t"]]],
        [[[f"p{i:03d}", (i * 37) % 11, f"team{i % 3}"] for i in range(300)]],
        [[["m", 7, "z"], ["m", 7, "a"], ["m", 8, "q"], ["l", 7, "q"]]],
    ],
    examples=2,
    wrong_solutions=['''from dataclasses import dataclass, field

@dataclass(order=True)
class Player:
    score: int
    name: str
    team: str = field(compare=False)
''' + DS_DRIVER,
        '''from dataclasses import dataclass, field

@dataclass(order=True)
class Player:
    sort_key: tuple = field(init=False, repr=False)
    name: str
    score: int
    team: str
    def __post_init__(self):
        self.sort_key = (-self.score, self.name)
''' + DS_DRIVER],
    guide=dict(
        prereqs="Dataclasses: `order=True`, `field(compare=False, init=False)`, `__post_init__`.",
        intuition="`order=True` compares instances as tuples of their comparable fields *in declaration order*. Put a computed `sort_key` first — `(-score, name)` — and exclude everything else from comparison.",
        hints=[
            "A descending numeric key is just the negated value.",
            "Declare `sort_key: tuple = field(init=False, repr=False)` as the first field.",
            "Compute it in `__post_init__`; mark the other fields `field(compare=False)` (at least `team`).",
        ],
        brute_force="`sorted(players, key=lambda p: (-p.score, p.name))` is the right tool in everyday code; here the goal is to bake the ordering into the type.",
        approach="""```
@dataclass(order=True)
class Player:
    sort_key: tuple = field(init=False, repr=False)
    name: str = field(compare=False)
    score: int = field(compare=False)
    team: str = field(compare=False)
    def __post_init__(self):
        self.sort_key = (-self.score, self.name)
```
A field with `init=False` and no default may precede fields without defaults, because it is not an `__init__` parameter.""",
        complexity="Comparison O(1) (plus string comparison); sorting O(n log n).",
        pitfalls="""- Reordering fields to `score, name` sorts ascending by score — wrong direction.
- Leaving `team` comparable breaks the equality requirement.
- With `frozen=True` you'd need `object.__setattr__` in `__post_init__`.""",
        follow_up="Make it `frozen=True, slots=True`, and add a `@classmethod from_row`.",
    ),
),
# =====================================================================================
dict(
    id="py-timer",
    title="Context-Manager Timer",
    difficulty="Easy",
    pattern="Context Managers",
    entry="run",
    compare="float",
    description=r"""
Write a reusable context manager class `Timer(clock=time.perf_counter)`:

- `with timer as t:` — `__enter__` reads the clock and returns the timer itself.
- On exit (normal **or** via exception) it reads the clock again and stores the difference in
  `timer.elapsed`, and appends it to the list `timer.laps`.
- `timer.total` is the sum of all laps so far.
- It must **not** swallow exceptions raised in the block.
- The `clock` argument is any zero-argument callable returning a number (this makes the class
  testable without real waiting — dependency injection!).

The driver `run(times, failing_blocks)` (do not edit) uses a fake clock that returns the values of
`times` in order, runs `len(times) // 2` `with` blocks (raising `RuntimeError` inside the blocks whose
index is in `failing_blocks`) and returns `[laps, total, elapsed, escaped_exceptions, enter_returned_self]`.

**Example:** `times = [0, 1.5, 10, 12], failing_blocks = []` → `[[1.5, 2], 3.5, 2, 0, true]`
""",
    starter='''import time

class Timer:
    def __init__(self, clock=time.perf_counter):
        pass

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc, tb):
        pass
''' + TIMER_DRIVER,
    solution=TIMER_SOLUTION,
    tests=[
        [[0, 1.5, 10, 12], []],
        [[], []],
        [[5, 5], []],
        [[0, 1], [0]],
        [[0, 1, 2, 4, 8, 16], [1]],
        [[0.25, 0.75, 1.0, 1.125], [0, 1]],
        [[100, 101, 101, 103, 103, 106, 106, 110], [3]],
        [list(range(0, 40)), [0, 5, 19]],
        [[1, 2, 3], []],
    ],
    examples=2,
    wrong_solutions=[
        '''import time
class Timer:
    def __init__(self, clock=time.perf_counter):
        self._clock = clock; self.laps = []; self.elapsed = None
    @property
    def total(self): return sum(self.laps)
    def __enter__(self):
        self._start = self._clock(); return self
    def __exit__(self, exc_type, exc, tb):
        self.elapsed = self._clock() - self._start
        self.laps.append(self.elapsed)
        return True
''' + TIMER_DRIVER,
        '''import time
class Timer:
    def __init__(self, clock=time.perf_counter):
        self._clock = clock; self.laps = []; self.elapsed = None
    @property
    def total(self): return sum(self.laps)
    def __enter__(self):
        self._start = self._clock(); return self
    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self.elapsed = self._clock() - self._start
            self.laps.append(self.elapsed)
''' + TIMER_DRIVER,
    ],
    guide=dict(
        prereqs="Lesson *Context managers and contextlib*.",
        intuition="`with` calls `__enter__` before the block and `__exit__` after it — always, even when the block raises. Read the clock in both places and subtract.",
        hints=[
            "Store the clock callable in `__init__`; call it (`self._clock()`) in `__enter__` and `__exit__`.",
            "`__enter__` must `return self` for `as t` to be useful.",
            "Return `False` (or nothing) from `__exit__` so exceptions propagate.",
        ],
        brute_force="Manual `start = time.perf_counter(); ...; elapsed = time.perf_counter() - start` scattered around the code, forgetting the exception path.",
        approach="""```
def __enter__(self): self._start = self._clock(); return self
def __exit__(self, *exc):
    self.elapsed = self._clock() - self._start
    self.laps.append(self.elapsed)
    return False
```
`total` can be a property: `sum(self.laps)`.""",
        complexity="O(1) per use (O(laps) for `total` if computed on demand).",
        pitfalls="""- Returning a truthy value from `__exit__` silently swallows exceptions.
- Recording the lap only on success misses failing blocks.
- Calling `time.perf_counter()` directly instead of the injected clock makes the class untestable.""",
        follow_up="Write the same thing as a generator with `@contextlib.contextmanager`, and as a decorator via `contextlib.ContextDecorator`.",
    ),
),
# =====================================================================================
dict(
    id="py-suppress-log",
    title="Suppress-and-Log Context Manager",
    difficulty="Medium",
    pattern="Context Managers",
    entry="run",
    description=r"""
`contextlib.suppress(*excs)` silently swallows the listed exceptions. Build a more useful cousin:
a class `SuppressAndLog(*exc_types)` that

- suppresses an exception raised inside its `with` block **iff** it is an instance of one of
  `exc_types` (subclasses count, e.g. `LookupError` covers `KeyError` and `IndexError`);
- records each suppressed exception in the list attribute `errors` as the string
  `"<ExceptionClassName>: <str(exception)>"`;
- lets every other exception propagate untouched (and does not record it);
- returns itself from `__enter__` and is **reusable** across many `with` blocks.

The driver `run(type_names, actions)` (do not edit) creates one manager for the named exception
types and runs one `with` block per action (`"ok"` or an exception name to raise). It returns
`[errors, names_of_escaped_exceptions, indices_of_blocks_that_completed]`.

**Example:** `type_names = ["ValueError"], actions = ["ok", "ValueError", "TypeError"]`
→ `[["ValueError: step 1"], ["TypeError"], [0]]`
""",
    starter='''class SuppressAndLog:
    def __init__(self, *exc_types):
        pass

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc, tb):
        pass
''' + SL_DRIVER,
    solution=SL_SOLUTION,
    tests=[
        [["ValueError"], ["ok", "ValueError", "TypeError"]],
        [[], ["ok", "ValueError"]],
        [["LookupError"], ["KeyError", "IndexError", "ValueError", "ok"]],
        [["KeyError"], ["LookupError", "KeyError", "IndexError"]],
        [["ValueError", "TypeError"], ["TypeError", "ValueError", "ZeroDivisionError", "ok", "ok"]],
        [["ArithmeticError"], ["ZeroDivisionError", "ok", "ZeroDivisionError"]],
        [["ValueError"], []],
        [["ValueError"], ["ok"] * 5],
        [["IndexError", "ZeroDivisionError"], ["KeyError", "IndexError", "ArithmeticError", "ZeroDivisionError"]],
    ],
    examples=2,
    wrong_solutions=[
        '''class SuppressAndLog:
    def __init__(self, *exc_types):
        self.exc_types = exc_types; self.errors = []
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb):
        if exc_type in self.exc_types:
            self.errors.append(f"{exc_type.__name__}: {exc}")
            return True
        return False
''' + SL_DRIVER,
        '''class SuppressAndLog:
    def __init__(self, *exc_types):
        self.exc_types = exc_types; self.errors = []
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self.errors.append(f"{exc_type.__name__}: {exc}")
        return True
''' + SL_DRIVER,
    ],
    guide=dict(
        prereqs="`__enter__`/`__exit__`, exception hierarchies, `issubclass`.",
        intuition="`__exit__` receives the exception type, value and traceback (all `None` when the block succeeded). Returning a truthy value tells Python 'handled — don't re-raise'.",
        hints=[
            "Check `exc_type is not None` first: `__exit__` also runs on success.",
            "`issubclass(exc_type, self.exc_types)` accepts a tuple and handles subclasses.",
            "Return `True` only when you suppressed; otherwise `False`.",
        ],
        brute_force="A `try/except` around every block at every call site — the duplication a context manager removes.",
        approach="""```
def __exit__(self, exc_type, exc, tb):
    if exc_type is not None and issubclass(exc_type, self.exc_types):
        self.errors.append(f"{exc_type.__name__}: {exc}")
        return True
    return False
```
With an empty `exc_types` tuple, `issubclass(x, ())` is `False`, so nothing is suppressed.""",
        complexity="O(1) per block.",
        pitfalls="""- `exc_type in self.exc_types` ignores subclasses.
- Always returning `True` swallows everything, including bugs.
- `str(KeyError('k'))` includes quotes (`"'k'"`) — that's Python's behaviour; just use `str(exc)`.""",
        follow_up="Re-implement with `@contextmanager` and a `try/except` around `yield`; add logging via the `logging` module.",
    ),
),
# =====================================================================================
dict(
    id="py-top-k-words",
    title="Top-K Frequent Words with Counter",
    difficulty="Easy",
    pattern="collections.Counter",
    entry="top_k_words",
    description=r"""
Given a text and an integer `k`, return the `k` most frequent words as a list of `[word, count]`
pairs.

- Words are maximal runs of ASCII letters and apostrophes (`[A-Za-z']+`), compared
  **case-insensitively** and returned in lowercase.
- Sort by count **descending**; break ties by word **ascending** (alphabetical).
- If there are fewer than `k` distinct words, return them all.

**Example:** `text = "The cat and the hat. The END, the end!", k = 2` → `[["the", 4], ["end", 2]]`
""",
    starter='''from collections import Counter
import re

def top_k_words(text: str, k: int) -> list:
    pass
''',
    solution='''from collections import Counter
import re

def top_k_words(text, k):
    counts = Counter(re.findall(r"[a-z']+", text.lower()))
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [[w, c] for w, c in ranked[:k]]
''',
    tests=[
        ["The cat and the hat. The END, the end!", 2],
        ["", 3],
        ["one", 5],
        ["b a c b a c", 2],
        ["Don't stop; don't STOP -- DON'T!", 3],
        ["a a a b b c", 0],
        ["z y x w v", 3],
        ["tie tie apple apple zebra zebra mango", 3],
        ["x1y2z x-y_z 3x", 10],
        [" ".join(f"w{chr(97 + i % 26)}{chr(97 + (i * 7) % 26)}" for i in range(5000)), 8],
    ],
    examples=2,
    wrong_solutions=[
        '''from collections import Counter
import re
def top_k_words(text, k):
    return [[w, c] for w, c in Counter(re.findall(r"[a-z']+", text.lower())).most_common(k)]
''',
        '''from collections import Counter
def top_k_words(text, k):
    counts = Counter(text.lower().split())
    return [[w, c] for w, c in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:k]]
''',
    ],
    guide=dict(
        prereqs="`collections.Counter`, `re.findall`, sorting with a tuple key (lessons *collections* and *heapq, bisect, sorting*).",
        intuition="Tokenise, count, then sort by a composite key: negative count (so bigger comes first) and the word itself for ties.",
        hints=[
            "`re.findall(r\"[a-z']+\", text.lower())` extracts the words.",
            "`Counter(words)` counts them in one pass.",
            "`sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:k]`.",
        ],
        brute_force="For each distinct word call `words.count(w)`: O(n·d).",
        approach="Count with `Counter` (O(n)), sort the distinct items with key `(-count, word)` (O(d log d)), slice the first `k`.",
        complexity="O(n + d log d) time, O(d) space for d distinct words. With `heapq.nsmallest(k, ..., key=...)` it becomes O(n + d log k).",
        pitfalls="""- `Counter.most_common(k)` breaks ties by *first occurrence*, not alphabetically.
- `str.split()` leaves punctuation attached (`"hat."`).
- Forgetting to lowercase.""",
        follow_up="Stream a huge file line by line updating the Counter; use `heapq.nsmallest` for large d and small k.",
    ),
),
# =====================================================================================
dict(
    id="py-lru-cache",
    title="LRU Cache with OrderedDict",
    difficulty="Medium",
    pattern="collections.OrderedDict",
    leetcode="https://leetcode.com/problems/lru-cache/",
    neetcode="https://neetcode.io/problems/lru-cache",
    kind="class",
    entry="LRUCache",
    description=r"""
Design a least-recently-used cache with a fixed positive `capacity`:

- `LRUCache(capacity)` creates an empty cache.
- `get(key)` returns the value for `key`, or `-1` if absent. A successful `get` makes the key the
  most recently used.
- `put(key, value)` inserts or updates the key (making it most recently used). If the cache then
  holds more than `capacity` keys, evict the **least recently used** one.

Both operations must run in O(1) average time. Use `collections.OrderedDict`
(`move_to_end`, `popitem(last=False)`).

**Example:** ops `LRUCache(2), put(1,1), put(2,2), get(1), put(3,3), get(2), put(4,4), get(1), get(3), get(4)`
→ `[null, null, null, 1, null, -1, null, -1, 3, 4]`
""",
    starter='''from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int):
        pass

    def get(self, key: int) -> int:
        pass

    def put(self, key: int, value: int) -> None:
        pass
''',
    solution='''from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.data = OrderedDict()

    def get(self, key):
        if key not in self.data:
            return -1
        self.data.move_to_end(key)
        return self.data[key]

    def put(self, key, value):
        if key in self.data:
            self.data.move_to_end(key)
        self.data[key] = value
        if len(self.data) > self.capacity:
            self.data.popitem(last=False)
''',
    tests=[
        [["LRUCache", "put", "put", "get", "put", "get", "put", "get", "get", "get"],
         [[2], [1, 1], [2, 2], [1], [3, 3], [2], [4, 4], [1], [3], [4]]],
        [["LRUCache", "get"], [[1], [5]]],
        [["LRUCache", "put", "get", "put", "get", "get"], [[1], [1, 10], [1], [2, 20], [1], [2]]],
        [["LRUCache", "put", "put", "put", "get", "get"], [[2], [1, 1], [2, 2], [1, 100], [1], [2]]],
        [["LRUCache", "put", "put", "put", "put", "get", "get"], [[2], [1, 1], [2, 2], [1, 5], [3, 3], [2], [1]]],
        [["LRUCache", "put", "put", "get", "get", "put", "get", "get", "get"],
         [[2], [2, 1], [3, 2], [3], [2], [4, 3], [2], [3], [4]]],
        _lru_case(1, 300, 3, 6),
        _lru_case(2, 800, 10, 25),
        _lru_case(3, 3000, 50, 120),
        _lru_case(4, 500, 1, 4),
    ],
    examples=1,
    wrong_solutions=[
        '''class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity; self.data = {}
    def get(self, key):
        return self.data.get(key, -1)
    def put(self, key, value):
        if key not in self.data and len(self.data) >= self.capacity:
            del self.data[next(iter(self.data))]
        self.data[key] = value
''',
        '''from collections import OrderedDict
class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity; self.data = OrderedDict()
    def get(self, key):
        if key not in self.data: return -1
        self.data.move_to_end(key)
        return self.data[key]
    def put(self, key, value):
        self.data[key] = value
        if len(self.data) > self.capacity:
            self.data.popitem(last=False)
''',
    ],
    guide=dict(
        prereqs="Dicts, `OrderedDict` (lesson *collections*).",
        intuition="You need a hash map for O(1) lookup *and* an ordering by recency with O(1) 'move to newest' and 'drop oldest'. `OrderedDict` is exactly a hash map threaded with a doubly linked list.",
        hints=[
            "Keep the most recently used key at the end of the OrderedDict.",
            "`move_to_end(key)` on every successful get and on updates.",
            "After inserting, if `len > capacity`, `popitem(last=False)` evicts the oldest.",
        ],
        brute_force="A list of `(key, value)` ordered by recency: O(n) per operation to find and move a key.",
        approach="""- `get`: missing → -1; else `move_to_end`, return value.
- `put`: if present, `move_to_end`; assign; if over capacity, `popitem(last=False)`.

Dry run (cap 2): put 1, put 2 → order [1,2]; get 1 → [2,1]; put 3 → [2,1,3] → evict 2 → [1,3].""",
        complexity="O(1) average per operation, O(capacity) space.",
        pitfalls="""- Updating an existing key must also refresh its recency (assigning to an existing key does *not* move it).
- A plain FIFO (evict oldest insertion) is not LRU.
- Evict *after* inserting, or check `key not in data` before evicting for an update.""",
        follow_up="Implement it from scratch with a dict plus a hand-written doubly linked list; add TTL expiry.",
    ),
),
# =====================================================================================
dict(
    id="py-kth-largest",
    title="Kth Largest in a Stream (heapq)",
    difficulty="Easy",
    pattern="heapq",
    leetcode="https://leetcode.com/problems/kth-largest-element-in-a-stream/",
    neetcode="https://neetcode.io/problems/kth-largest-integer-in-a-stream",
    kind="class",
    entry="KthLargest",
    description=r"""
Design a class that reports the **k-th largest** value seen so far in a stream (k-th in sorted
order counting duplicates, not k-th distinct).

- `KthLargest(k, nums)` starts with the initial values `nums` (which may hold fewer than `k` items).
- `add(val)` inserts `val` and returns the current k-th largest value. It is guaranteed that at
  least `k` values exist whenever `add` returns.

Use a **min-heap of size k** (`heapq`), so `add` costs O(log k).

**Example:** `KthLargest(3, [4, 5, 8, 2])`, then `add(3), add(5), add(10), add(9), add(4)` → `4, 5, 5, 8, 8`
""",
    starter='''import heapq

class KthLargest:
    def __init__(self, k: int, nums: list[int]):
        pass

    def add(self, val: int) -> int:
        pass
''',
    solution='''import heapq

class KthLargest:
    def __init__(self, k, nums):
        self.k = k
        self.heap = list(nums)
        heapq.heapify(self.heap)
        while len(self.heap) > k:
            heapq.heappop(self.heap)

    def add(self, val):
        if len(self.heap) < self.k:
            heapq.heappush(self.heap, val)
        elif val > self.heap[0]:
            heapq.heapreplace(self.heap, val)
        return self.heap[0]
''',
    tests=[
        [["KthLargest", "add", "add", "add", "add", "add"], [[3, [4, 5, 8, 2]], [3], [5], [10], [9], [4]]],
        [["KthLargest", "add", "add", "add"], [[1, []], [-3], [-2], [-4]]],
        [["KthLargest", "add", "add"], [[2, [0]], [-1], [1]]],
        [["KthLargest", "add", "add", "add", "add"], [[4, [7, 7, 7, 7, 8, 3]], [2], [10], [9], [9]]],
        [["KthLargest", "add", "add", "add"], [[3, [1, 1]], [1], [1], [2]]],
        _kth_case(1, 1, 10, 30),
        _kth_case(2, 5, 3, 60),
        _kth_case(3, 50, 200, 400),
        _kth_case(4, 2, 0, 20),
        _kth_case(5, 100, 5000, 2000),
    ],
    examples=1,
    wrong_solutions=['''import heapq
class KthLargest:
    def __init__(self, k, nums):
        self.k = k
        self.vals = set(nums)
    def add(self, val):
        self.vals.add(val)
        return sorted(self.vals, reverse=True)[self.k - 1]
'''],
    guide=dict(
        prereqs="Heaps and `heapq` (lesson *heapq, bisect, sorting and math*).",
        intuition="You only care about the k largest values. Keep exactly those in a min-heap: its smallest element — the root — is the k-th largest overall.",
        hints=[
            "`heapq` is a min-heap; `heap[0]` is the smallest item.",
            "Heapify the initial numbers, then pop until only k remain.",
            "On `add`: push if the heap has fewer than k items; otherwise replace the root only when `val` is larger.",
        ],
        brute_force="Keep a sorted list and re-sort on every add: O(n log n) per add. `bisect.insort` improves it to O(n).",
        approach="""```
init: heapify(nums); pop while len > k
add(val): if len < k: heappush
          elif val > heap[0]: heapreplace(heap, val)
          return heap[0]
```
Dry run k=3, [4,5,8,2] → heap {4,5,8}. add 3 → ignored → 4. add 5 → replace 4 → {5,5,8} → 5.""",
        complexity="Init O(n + (n−k) log n); each add O(log k); space O(k).",
        pitfalls="""- Using a max-heap of everything makes each query O(k log n).
- Treating 'k-th largest' as k-th *distinct* (the wrong solution).
- Forgetting the case where the initial list has fewer than k items.""",
        follow_up="Kth largest in an unsorted array (LeetCode 215): `heapq.nlargest(k, nums)[-1]` or quickselect.",
    ),
),
# =====================================================================================
dict(
    id="py-merge-sorted",
    title="Merge K Sorted Lists with a Heap",
    difficulty="Medium",
    pattern="heapq",
    entry="merge_sorted",
    description=r"""
Given `k` lists, each sorted in non-decreasing order, return one sorted list containing all the
elements — the behaviour of `heapq.merge`, which you should implement yourself with
`heappush`/`heappop` (don't call `heapq.merge`, and don't just concatenate and sort).

Keep one entry per list in the heap: `(value, list_index, position)`. The `list_index` acts as a
tie-breaker so that equal values never force Python to compare further.

**Example:** `[[1, 4, 7], [2, 5], [], [0, 9]]` → `[0, 1, 2, 4, 5, 7, 9]`
""",
    starter='''import heapq

def merge_sorted(lists: list[list[int]]) -> list[int]:
    pass
''',
    solution='''import heapq

def merge_sorted(lists):
    heap = [(lst[0], i, 0) for i, lst in enumerate(lists) if lst]
    heapq.heapify(heap)
    out = []
    while heap:
        value, i, pos = heapq.heappop(heap)
        out.append(value)
        if pos + 1 < len(lists[i]):
            heapq.heappush(heap, (lists[i][pos + 1], i, pos + 1))
    return out
''',
    tests=[
        [[[1, 4, 7], [2, 5], [], [0, 9]]],
        [[]],
        [[[]]],
        [[[], [], []]],
        [[[1, 2, 3]]],
        [[[1, 1, 1], [1, 1], [1]]],
        [[[-5, -1], [-3, 0, 2], [-4]]],
        [[[5], [4], [3], [2], [1]]],
        [_sorted_lists(1, 6, 10)],
        [_sorted_lists(2, 40, 60)],
        [_sorted_lists(3, 200, 12)],
    ],
    examples=2,
    wrong_solutions=['''def merge_sorted(lists):
    out = []
    for i in range(max((len(l) for l in lists), default=0)):
        row = sorted(l[i] for l in lists if i < len(l))
        out.extend(row)
    return out
'''],
    guide=dict(
        prereqs="`heapq`, tuple comparison.",
        intuition="The next output element is always the smallest among the *current heads* of the k lists. A heap of the k heads gives you that minimum in O(log k); after popping, push the next element from the same list.",
        hints=[
            "Initialise the heap with the first element of each non-empty list.",
            "Store `(value, list_index, position)`.",
            "After popping `(v, i, pos)`, push `(lists[i][pos+1], i, pos+1)` if it exists.",
        ],
        brute_force="Concatenate everything and sort: O(N log N). Or scan all k heads for each output element: O(N·k).",
        approach="""1. `heap = [(lst[0], i, 0) for i, lst in enumerate(lists) if lst]`; `heapify`.
2. Pop the smallest, append its value, push its successor.
3. Stop when the heap is empty.""",
        complexity="O(N log k) time for N total elements; O(k) extra space besides the output.",
        pitfalls="""- Empty lists must be skipped when seeding the heap.
- Without the index tie-breaker, equal values would compare the next tuple field — fine for ints, a crash for uncomparable payloads.
- `lst.pop(0)` to advance is O(n) per pop; track a position instead.""",
        follow_up="Make it a generator that accepts arbitrary *iterators* (store the iterator in the tuple after the tie-breaker) — that's exactly `heapq.merge`.",
    ),
),
# =====================================================================================
dict(
    id="py-async-gather",
    title="Bounded Concurrency with asyncio",
    difficulty="Medium",
    pattern="asyncio",
    entry="run",
    description=r"""
Write a coroutine `async def run_limited(factories, limit)`.

`factories` is a list of zero-argument **async functions** (calling one returns a coroutine).
Run them all **concurrently**, but with at most `limit` running at the same time, and return a list
of their results **in the same order as `factories`**. If a job raises, put the exception object in
that job's slot instead of failing the whole batch (hint: `asyncio.gather(..., return_exceptions=True)`).

Use `asyncio.Semaphore(limit)` to bound concurrency.

The driver `run(jobs, limit)` (do not edit) turns `jobs = [[delay_ms, value], ...]` into async
functions that sleep and return `value` (or raise `ValueError` when the value is `"fail"`), runs your
coroutine with `asyncio.run`, and returns `[results, peak_concurrency, all_jobs_started]`.

**Example:** `jobs = [[3, "a"], [1, "b"], [2, "c"]], limit = 2` → `[["a", "b", "c"], 2, true]`
""",
    starter='''import asyncio

async def run_limited(factories, limit):
    pass
''' + AG_DRIVER,
    solution=AG_SOLUTION,
    tests=[
        [[[3, "a"], [1, "b"], [2, "c"]], 2],
        [[], 3],
        [[[1, 42]], 1],
        [[[1, "x"], [1, "y"], [1, "z"], [1, "w"]], 1],
        [[[2, 1], [2, 2], [2, 3], [2, 4], [2, 5]], 10],
        [[[1, "ok"], [1, "fail"], [1, "ok2"]], 2],
        [[[5, 0], [1, 1], [4, 2], [1, 3], [3, 4], [1, 5]], 3],
        [[[1, i] for i in range(30)], 4],
        [[[2, "fail"], [1, "fail"]], 2],
    ],
    examples=2,
    wrong_solutions=[
        '''import asyncio
async def run_limited(factories, limit):
    out = []
    for f in factories:
        try:
            out.append(await f())
        except Exception as e:
            out.append(e)
    return out
''' + AG_DRIVER,
        '''import asyncio
async def run_limited(factories, limit):
    return await asyncio.gather(*(f() for f in factories), return_exceptions=True)
''' + AG_DRIVER,
    ],
    guide=dict(
        prereqs="Lesson *asyncio: async/await, tasks and gather*.",
        intuition="`gather` runs awaitables concurrently and preserves order. To cap concurrency, wrap each job so it must acquire a semaphore before starting.",
        hints=[
            "Create `sem = asyncio.Semaphore(limit)` *inside* the coroutine (so it belongs to the running loop).",
            "Write an inner `async def guarded(factory): async with sem: return await factory()`.",
            "`return await asyncio.gather(*(guarded(f) for f in factories), return_exceptions=True)`.",
        ],
        brute_force="Awaiting the jobs one by one in a `for` loop is sequential: peak concurrency 1 and total time = sum of delays.",
        approach="""```
async def run_limited(factories, limit):
    sem = asyncio.Semaphore(limit)
    async def guarded(f):
        async with sem:
            return await f()
    return await asyncio.gather(*map(guarded, factories), return_exceptions=True)
```
`gather` returns results in argument order regardless of completion order.""",
        complexity="Wall time ≈ total work / limit; O(n) tasks in memory.",
        pitfalls="""- Calling the factories eagerly *outside* the semaphore doesn't start them (coroutines are lazy) — but creating **tasks** outside it would.
- Without `return_exceptions=True`, the first failure propagates and you lose the other results.
- Plain `gather` with no semaphore ignores the limit.""",
        follow_up="Use a worker pool consuming an `asyncio.Queue`; add per-job timeouts with `asyncio.wait_for` / `asyncio.timeout`.",
    ),
),
# =====================================================================================
dict(
    id="py-parse-logs",
    title="Parse Log Lines with Regex",
    difficulty="Medium",
    pattern="Regular Expressions",
    entry="parse_logs",
    description=r"""
Each valid log line has the exact shape

```
YYYY-MM-DD HH:MM:SS [LEVEL] module: message
```

where `LEVEL` is one of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` (uppercase), `module` is one
or more word characters (`\w+`), and the message is everything after `": "` (it may be any
non-empty text). The date/time fields only need the right number of digits (no calendar checks).
A message may contain a user reference of the form `(user=<digits>)`.

Write `parse_logs(lines)` returning a dictionary with:

- `"levels"`: `{level: count}` over valid lines (only levels that occur);
- `"errors_by_module"`: `{module: count}` counting lines whose level is `ERROR` or `CRITICAL`;
- `"users"`: sorted list of the distinct user ids (as ints) found in valid lines;
- `"invalid"`: the number of lines that do not match the format.

**Example:** for the 7 sample lines shown in test 1 the answer is
`{"levels": {"INFO": 1, "ERROR": 3, "WARNING": 1, "DEBUG": 1}, "errors_by_module": {"auth": 2, "db": 1}, "users": [7, 17, 42], "invalid": 1}`
""",
    starter='''import re
from collections import Counter

def parse_logs(lines: list[str]) -> dict:
    pass
''',
    solution='''import re
from collections import Counter

LINE = re.compile(
    r"(?P<date>\\d{4}-\\d{2}-\\d{2}) (?P<time>\\d{2}:\\d{2}:\\d{2}) "
    r"\\[(?P<level>DEBUG|INFO|WARNING|ERROR|CRITICAL)\\] (?P<module>\\w+): (?P<msg>.+)"
)
USER = re.compile(r"\\(user=(\\d+)\\)")

def parse_logs(lines):
    levels, errors, users, invalid = Counter(), Counter(), set(), 0
    for line in lines:
        m = LINE.fullmatch(line)
        if not m:
            invalid += 1
            continue
        levels[m["level"]] += 1
        if m["level"] in ("ERROR", "CRITICAL"):
            errors[m["module"]] += 1
        users.update(int(u) for u in USER.findall(m["msg"]))
    return {"levels": dict(levels), "errors_by_module": dict(errors),
            "users": sorted(users), "invalid": invalid}
''',
    tests=[
        [_LOG_SAMPLE],
        [[]],
        [["garbage", "", "   "]],
        [["2026-01-02 10:00:01 [INFO] a: b"]],
        [["2026-01-02 10:00:01 [INFO] a:b", "2026-01-02 10:00:01 [INFO] a: ", "2026-1-2 10:00:01 [INFO] a: b",
          "2026-01-02 10:00:01 [TRACE] a: b", " 2026-01-02 10:00:01 [INFO] a: b"]],
        [["2026-01-02 10:00:01 [CRITICAL] core: meltdown (user=1) then (user=2) and (user=1)",
          "2026-01-02 10:00:02 [ERROR] core: user=99 without parens",
          "2026-01-02 10:00:03 [INFO] api_v2: (user=abc) (user=) (user=003)"]],
        [["2026-01-02 10:00:01 [ERROR] my-module: dash not allowed in module",
          "2026-01-02 10:00:01 [ERROR] mod: colon: inside: message",
          "x 2026-01-02 10:00:01 [ERROR] mod: prefix junk"]],
        [_log_lines(1, 60)],
        [_log_lines(2, 600)],
        [_log_lines(3, 2500)],
    ],
    examples=1,
    wrong_solutions=[
        '''import re
from collections import Counter
def parse_logs(lines):
    levels, errors, users, invalid = Counter(), Counter(), set(), 0
    for line in lines:
        m = re.search(r"\\[(\\w+)\\] (\\w+): (.+)", line)
        if not m:
            invalid += 1
            continue
        levels[m[1]] += 1
        if m[1] in ("ERROR", "CRITICAL"):
            errors[m[2]] += 1
        users.update(int(u) for u in re.findall(r"user=(\\d+)", m[3]))
    return {"levels": dict(levels), "errors_by_module": dict(errors), "users": sorted(users), "invalid": invalid}
''',
    ],
    guide=dict(
        prereqs="Lesson *Regular expressions*: groups, quantifiers, `fullmatch`, `findall`; `Counter`.",
        intuition="Describe one line with a single anchored pattern using named groups; anything that doesn't `fullmatch` is invalid. A second small pattern pulls user ids out of the message.",
        hints=[
            "Compile once: `\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2} \\[(LEVELS)\\] (\\w+): (.+)`.",
            "Use `pattern.fullmatch(line)` so leading/trailing junk makes the line invalid.",
            "`re.findall(r'\\(user=(\\d+)\\)', msg)` returns just the digit groups.",
        ],
        brute_force="Chains of `split()` and index juggling — brittle around spaces in messages and missing parts.",
        approach="""1. Precompile `LINE` (named groups `level`, `module`, `msg`) and `USER`.
2. For each line: `fullmatch`; if `None`, count invalid.
3. Otherwise update `Counter`s and the user set.
4. Convert Counters to dicts and sort users.""",
        complexity="O(total characters) time; O(distinct levels + modules + users) space.",
        pitfalls="""- `re.search`/`re.match` accept lines with junk before/after; use `fullmatch` (or `^...$`).
- Forgetting to escape `[`, `]`, `(`, `)`.
- Lowercase or unknown levels must be invalid.
- `user=99` without parentheses does not count.""",
        follow_up="Parse timestamps with `datetime.strptime` and report the busiest minute; make it a generator pipeline over a file.",
    ),
),
# =====================================================================================
dict(
    id="py-csv-records",
    title="CSV Text to Typed Records",
    difficulty="Medium",
    pattern="csv & Type Conversion",
    entry="parse_csv",
    description=r"""
Given the text of a CSV file whose first row is the header, return a list of dictionaries (one per
data row, keyed by header name) with each cell converted to the most specific type:

1. empty string → `None`
2. `true` / `false` (any letter case) → `True` / `False`
3. integer literal (optional sign, digits only, e.g. `-42`) → `int`
4. otherwise a valid float (e.g. `3.5`, `1e3`, `-.5`) → `float` — but **not** `nan`/`inf` words, which stay strings
5. anything else stays a string (unchanged, including surrounding spaces)

Use the standard `csv` module so that **quoted fields** containing commas, doubled quotes (`""`) and
newlines are handled correctly. Rows are guaranteed to have as many cells as the header. An empty
text returns `[]`.

**Example:**
```
name,age,score,active,note
Ana,31,88.5,true,"likes, commas"
Ben,,7,FALSE,
```
→ `[{"name":"Ana","age":31,"score":88.5,"active":true,"note":"likes, commas"}, {"name":"Ben","age":null,"score":7,"active":false,"note":null}]`
""",
    starter='''import csv
import io

def parse_csv(text: str) -> list[dict]:
    pass
''',
    solution='''import csv
import io
import re

_INT = re.compile(r"[+-]?\\d+")
_FLOAT = re.compile(r"[+-]?(\\d+\\.?\\d*|\\.\\d+)([eE][+-]?\\d+)?")

def _convert(cell):
    if cell == "":
        return None
    low = cell.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if _INT.fullmatch(cell):
        return int(cell)
    if _FLOAT.fullmatch(cell):
        return float(cell)
    return cell

def parse_csv(text):
    reader = csv.DictReader(io.StringIO(text, newline=""))
    return [{k: _convert(v) for k, v in row.items()} for row in reader]
''',
    tests=[
        ['name,age,score,active,note\nAna,31,88.5,true,"likes, commas"\nBen,,7,FALSE,\n'],
        [""],
        ["a,b\n"],
        ["x\n1\n-2\n+3\n4.0\n1e3\n-.5\n5.\n"],
        ["v\nnan\ninf\n-inf\nNaN\n1_000\n0x10\n1e\n.\n--1\n"],
        ['q\n"say ""hi"""\n"line1\nline2"\n" 42"\n" true "\n'],
        ["id,flag\n1,True\n2,tRuE\n3,false\n4,yes\n5,0\n"],
        ["only_header_no_newline"],
        ["a,b,c\n,,\n0,0.0,-0\n"],
        ["k,v\n" + "".join(f"key{i},{i * 1.5 if i % 3 else i}\n" for i in range(400))],
    ],
    examples=1,
    wrong_solutions=[
        '''def parse_csv(text):
    lines = text.splitlines()
    if not lines: return []
    header = lines[0].split(",")
    out = []
    for ln in lines[1:]:
        row = {}
        for k, v in zip(header, ln.split(",")):
            if v == "": row[k] = None
            elif v.lower() in ("true", "false"): row[k] = v.lower() == "true"
            else:
                try: row[k] = int(v)
                except ValueError:
                    try: row[k] = float(v)
                    except ValueError: row[k] = v
        out.append(row)
    return out
''',
        '''import csv, io
def parse_csv(text):
    def conv(v):
        if v == "": return None
        if v.lower() in ("true", "false"): return v.lower() == "true"
        try: return int(v)
        except ValueError: pass
        try: return float(v)
        except ValueError: return v
    return [{k: conv(v) for k, v in row.items()} for row in csv.DictReader(io.StringIO(text, newline=""))]
''',
    ],
    guide=dict(
        prereqs="Lesson *Files, pathlib, JSON and CSV*; regex `fullmatch`.",
        intuition="Let `csv.DictReader` deal with the format (quotes, embedded commas and newlines); you only write the cell converter, checking the rules in order from most to least specific.",
        hints=[
            "`csv.DictReader(io.StringIO(text, newline=''))` yields one dict per row.",
            "Check empty → bool → int → float → string, in that order.",
            "`int()` and `float()` are more permissive than the spec (`' 42'`, `'1_000'`, `'nan'`) — validate with a regex before converting.",
        ],
        brute_force="`line.split(',')` breaks on quoted commas, doubled quotes and embedded newlines.",
        approach="""1. Wrap the text in `io.StringIO(text, newline='')` (the csv module wants to handle newlines itself).
2. `DictReader` consumes the header automatically.
3. Convert each cell with `_convert`, using `re.fullmatch` for int and float shapes.""",
        complexity="O(size of the text).",
        pitfalls="""- `float('nan')`, `float('inf')`, `int(' 42')`, `int('1_000')` all succeed in Python — try/except conversion is too permissive here.
- `bool('false')` is `True` (non-empty string!) — compare text instead.
- Opening real files for csv needs `newline=''`.""",
        follow_up="Write the inverse with `csv.DictWriter`; stream a large file lazily with a generator.",
    ),
),
# =====================================================================================
dict(
    id="py-json-path",
    title="Safe JSON Path Getter",
    difficulty="Medium",
    pattern="Dicts, Parsing & Exceptions",
    entry="get_path",
    description=r"""
Write `get_path(data, path, default)` that safely digs a value out of nested JSON-like data
(dicts, lists, scalars) using a path such as `"orders[0].items[1].sku"`:

- Path segments are separated by dots. A segment is a (possibly empty) **key**, optionally followed
  by one or more **indices** in brackets: `name`, `tags[0]`, `matrix[1][0]`, `[2]` (index only).
- A key looks up a dict; an index (which may be negative) looks up a list.
- The empty path `""` returns `data` itself.
- If at any step the lookup is impossible — missing key, index out of range, key applied to a
  non-dict, index applied to a non-list — return `default`.
- A value that exists but is `None`, `0`, `False` or empty must be returned as is (not replaced by
  the default).

**Example:** with `data = {"user": {"tags": ["a", "b"]}}`: `get_path(data, "user.tags[-1]", "?")` → `"b"`;
`get_path(data, "user.age", "?")` → `"?"`.
""",
    starter='''import re

def get_path(data, path: str, default=None):
    pass
''',
    solution='''import re

_SEGMENT = re.compile(r"([^.\\[\\]]*)((?:\\[-?\\d+\\])*)")
_INDEX = re.compile(r"\\[(-?\\d+)\\]")

def get_path(data, path, default=None):
    if path == "":
        return data
    current = data
    for segment in path.split("."):
        m = _SEGMENT.fullmatch(segment)
        if m is None:
            return default
        key, indices = m.group(1), m.group(2)
        if key or not indices:
            if not isinstance(current, dict) or key not in current:
                return default
            current = current[key]
        for idx in _INDEX.findall(indices):
            i = int(idx)
            if not isinstance(current, list) or not -len(current) <= i < len(current):
                return default
            current = current[i]
    return current
''',
    tests=[
        [_JSON_DOC, "user.name", "?"],
        [_JSON_DOC, "orders[0].items[1].sku", "?"],
        [_JSON_DOC, "user.tags[-1]", "?"],
        [_JSON_DOC, "user.age", "?"],
        [_JSON_DOC, "", "?"],
        [_JSON_DOC, "user.address.zip", "default"],
        [_JSON_DOC, "count", 99],
        [_JSON_DOC, "flag", True],
        [_JSON_DOC, "matrix[1][0]", -1],
        [_JSON_DOC, "matrix[2][0]", -1],
        [_JSON_DOC, "orders[1].items[0].sku", "none"],
        [_JSON_DOC, "orders[-3]", "oob"],
        [_JSON_DOC, "user.name.first", "not a dict"],
        [_JSON_DOC, "user[0]", "not a list"],
        [_JSON_DOC, "orders.id", "list needs index"],
        [[10, [20, 30], {"k": "v"}], "[1][1]", None],
        [[10, [20, 30], {"k": "v"}], "[2].k", None],
        [_JSON_DOC, ".empty", "?"],
        [_JSON_DOC, "user.tags[x]", "bad index"],
        [{"a": {"b": {"c": {"d": [0, [1, [2, [3, {"e": "deep"}]]]]}}}}, "a.b.c.d[1][1][1][1].e", None],
    ],
    examples=4,
    wrong_solutions=[
        '''import re
def get_path(data, path, default=None):
    cur = data
    try:
        for part in re.findall(r"[^.\\[\\]]+", path):
            cur = cur[int(part)] if isinstance(cur, list) else cur[part]
    except (KeyError, IndexError, ValueError, TypeError):
        return default
    return cur if cur else default
''',
        '''import re
def get_path(data, path, default=None):
    cur = data
    try:
        for part in re.findall(r"[^.\\[\\]]+", path):
            cur = cur[int(part)] if isinstance(cur, list) else cur[part]
    except (KeyError, IndexError, ValueError, TypeError):
        return default
    return cur
''',
    ],
    guide=dict(
        prereqs="Dicts and lists, regex groups, the difference between 'missing' and 'falsy'.",
        intuition="Split the path into steps, and walk the structure one step at a time, checking before each step that the current value has the right type and actually contains the key/index.",
        hints=[
            "Split on `.`; for each segment separate the key part from the `[i]` parts with a regex.",
            "For a key: `isinstance(cur, dict) and key in cur`. For an index: `isinstance(cur, list)` and `-len(cur) <= i < len(cur)`.",
            "Return `default` only for *missing* things — never test the final value's truthiness.",
        ],
        brute_force="Wrap `cur = cur[step]` in a broad `try/except` — close, but it confuses string indexing (`'Robin'[0]`), dict keys that look like numbers, and segments like `[x]`.",
        approach="""1. `""` → return data.
2. For each dot-separated segment, `fullmatch` `key(\\[-?\\d+\\])*`; malformed → default.
3. Apply the key (if present, or if the segment has no indices — that allows an empty-string key), then each index in turn, validating types and bounds.
4. Return what you end up holding.""",
        complexity="O(length of the path).",
        pitfalls="""- `return cur or default` replaces legitimate `0`, `False`, `None`, `[]` values.
- Strings are indexable: `"Robin"[0]` must *not* succeed for path `user.name[0]`... only lists accept indices.
- Negative indices beyond `-len` are out of range.
- `"orders.id"` applies a key to a list → default.""",
        follow_up="Support wildcards (`orders[*].id`) returning a list, and a `set_path` that creates intermediate containers.",
    ),
),
]
