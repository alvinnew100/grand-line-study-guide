"""Python Mastery problems: basics, built-ins, functions, iteration.

Several problems test language features (decorators, generators) that cannot be passed as JSON
arguments, so the starter ends with a small *driver* function (marked "do not edit") that exercises
the learner's code and returns plain data. The driver is the judged entry point.
"""

# ---------------------------------------------------------------- py-count-calls
CC_DRIVER = '''

# ---- driver (do not edit) ----
def run(xs):
    @count_calls
    def square(x):
        """Return x squared."""
        return x * x

    @count_calls
    def add(a, b=0):
        """Add two numbers."""
        return a + b

    out = [square(x) for x in xs]
    total = add(len(xs), b=1)
    return [out, total, square.calls, add.calls, square.__name__, add.__doc__]
'''

CC_SOLUTION = '''import functools

def count_calls(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        wrapper.calls += 1
        return func(*args, **kwargs)
    wrapper.calls = 0
    return wrapper
''' + CC_DRIVER

# ---------------------------------------------------------------- py-memoize
MEMO_DRIVER = '''

# ---- driver (do not edit) ----
def run(ns):
    calls = {"fib": 0, "power": 0}

    @memoize
    def fib(n):
        """n-th Fibonacci number."""
        calls["fib"] += 1
        return n if n < 2 else fib(n - 1) + fib(n - 2)

    @memoize
    def power(base, exp=2):
        calls["power"] += 1
        return base ** exp

    results = [fib(n) for n in ns]
    p = [power(2, exp=3), power(2, exp=3), power(2, 3), power(3), power(2)]
    return [results, calls["fib"], fib.hits, fib.misses,
            p, calls["power"], power.hits, power.misses, fib.__name__]
'''

MEMO_SOLUTION = '''import functools

def memoize(func):
    cache = {}

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        key = (args, tuple(sorted(kwargs.items())))
        if key in cache:
            wrapper.hits += 1
            return cache[key]
        wrapper.misses += 1
        result = func(*args, **kwargs)
        cache[key] = result
        return result

    wrapper.hits = 0
    wrapper.misses = 0
    return wrapper
''' + MEMO_DRIVER

# ---------------------------------------------------------------- py-retry
RETRY_DRIVER = '''

# ---- driver (do not edit) ----
def run(plan, times):
    outcomes = iter(plan)
    attempts = [0]
    errors = {"value": ValueError, "key": KeyError, "type": TypeError}

    @retry(times=times, exceptions=(ValueError, KeyError))
    def flaky(tag):
        """Pretend to call a flaky service."""
        attempts[0] += 1
        outcome = next(outcomes, "ok")
        if outcome in errors:
            raise errors[outcome](f"{tag} failed on attempt {attempts[0]}")
        return f"{tag}:{outcome}"

    try:
        result = flaky("job")
    except Exception as e:
        result = "raised " + type(e).__name__ + ": " + str(e).strip("'")
    return [result, attempts[0], flaky.__name__]
'''

RETRY_SOLUTION = '''import functools

def retry(times=3, exceptions=(Exception,)):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    if attempt == times:
                        raise
        return wrapper
    return decorator
''' + RETRY_DRIVER

# ---------------------------------------------------------------- py-deep-merge
DM_DRIVER = '''

# ---- driver (do not edit) ----
import copy as _copy

def check(a, b):
    a0, b0 = _copy.deepcopy(a), _copy.deepcopy(b)
    merged = deep_merge(a, b)
    snapshot = _copy.deepcopy(merged)

    def poison(d):
        for v in list(d.values()):
            if isinstance(v, dict):
                poison(v)
        d["__poisoned__"] = True

    poison(merged)          # if merged shares dicts with a or b, they get poisoned too
    return [snapshot, a == a0 and b == b0]
'''

DM_SOLUTION = '''def deep_merge(a, b):
    out = {}
    for k, v in a.items():
        out[k] = deep_merge(v, {}) if isinstance(v, dict) else v
    for k, v in b.items():
        if isinstance(v, dict):
            base = out.get(k)
            out[k] = deep_merge(base if isinstance(base, dict) else {}, v)
        else:
            out[k] = v
    return out
''' + DM_DRIVER

# ---------------------------------------------------------------- py-unique-everseen
UE_DRIVER = '''

# ---- driver (do not edit) ----
def run(items, ignore_case):
    key = (lambda s: s.lower() if isinstance(s, str) else s) if ignore_case else None
    gen = unique_everseen(items, key)
    assert iter(gen) is gen, "unique_everseen must return an iterator (use yield)"
    return list(gen)
'''

UE_SOLUTION = '''def unique_everseen(iterable, key=None):
    seen_hashable = set()
    seen_unhashable = []
    for item in iterable:
        k = item if key is None else key(item)
        try:
            if k in seen_hashable:
                continue
            seen_hashable.add(k)
        except TypeError:            # unhashable key, e.g. a list
            if k in seen_unhashable:
                continue
            seen_unhashable.append(k)
        yield item
''' + UE_DRIVER

# ---------------------------------------------------------------- py-custom-range
CR_DRIVER = '''

# ---- driver (do not edit) ----
def run(start, stop, step):
    r = MyRange(start, stop, step)
    probes = [p for p in range(-12, 25) if p in r]
    last = r[-1] if len(r) else None
    return [list(r), list(r), len(r), probes, last, iter(r) is not r]
'''

CR_SOLUTION = '''class MyRange:
    def __init__(self, start, stop, step=1):
        if step == 0:
            raise ValueError("step must not be zero")
        self.start, self.stop, self.step = start, stop, step

    def __len__(self):
        if self.step > 0:
            return max(0, (self.stop - self.start + self.step - 1) // self.step)
        return max(0, (self.start - self.stop - self.step - 1) // -self.step)

    def __getitem__(self, k):
        n = len(self)
        if k < 0:
            k += n
        if not 0 <= k < n:
            raise IndexError("MyRange index out of range")
        return self.start + k * self.step

    def __contains__(self, x):
        if not isinstance(x, int):
            return False
        offset = x - self.start
        if offset % self.step:
            return False
        return 0 <= offset // self.step < len(self)

    def __iter__(self):
        value, n = self.start, len(self)
        for _ in range(n):
            yield value
            value += self.step
''' + CR_DRIVER

# ---------------------------------------------------------------- py-flatten
FL_DRIVER = '''

# ---- driver (do not edit) ----
def run(nested):
    gen = flatten(nested)
    assert iter(gen) is gen, "flatten must be a generator"
    return list(gen)
'''

FL_SOLUTION = '''def flatten(nested):
    for item in nested:
        if isinstance(item, (list, tuple)):
            yield from flatten(item)
        else:
            yield item
''' + FL_DRIVER


def _deep(depth):
    x = [depth]
    for i in range(depth - 1, 0, -1):
        x = [i, x]
    return x


# ---------------------------------------------------------------- py-chunked
CH_DRIVER = '''

# ---- driver (do not edit) ----
def run(data, n):
    pulled = [0]

    def source():
        for x in data:
            pulled[0] += 1
            yield x

    gen = chunked(source(), n)
    first = next(gen, None)
    lazy = pulled[0] <= n + 1
    chunks = ([first] if first is not None else []) + list(gen)
    return [[list(c) for c in chunks], lazy]
'''

CH_SOLUTION = '''from itertools import islice

def chunked(iterable, n):
    it = iter(iterable)
    while True:
        chunk = list(islice(it, n))
        if not chunk:
            return
        yield chunk
''' + CH_DRIVER

# ---------------------------------------------------------------- py-moving-average
MA_DRIVER = '''

# ---- driver (do not edit) ----
def run(values, k):
    gen = moving_average(iter(values), k)
    assert iter(gen) is gen, "moving_average must be a generator"
    return list(gen)
'''

MA_SOLUTION = '''from collections import deque

def moving_average(iterable, k):
    window = deque()
    total = 0
    for x in iterable:
        window.append(x)
        total += x
        if len(window) > k:
            total -= window.popleft()
        if len(window) == k:
            yield total / k
''' + MA_DRIVER

# ---------------------------------------------------------------- py-groupby
GB_DRIVER = '''

# ---- driver (do not edit) ----
KEYS = {
    "identity": None,
    "len": len,
    "lower": lambda s: s.lower(),
    "parity": lambda n: n % 2,
    "sign": lambda n: (n > 0) - (n < 0),
}

def run(items, key_name):
    gen = group_consecutive(iter(items), KEYS[key_name])
    assert iter(gen) is gen, "group_consecutive must be a generator"
    return [[k, list(g)] for k, g in gen]
'''

GB_SOLUTION = '''def group_consecutive(iterable, key=None):
    if key is None:
        key = lambda x: x
    sentinel = object()
    current_key = sentinel
    group = []
    for item in iterable:
        k = key(item)
        if group and k != current_key:
            yield current_key, group
            group = []
        current_key = k
        group.append(item)
    if group:
        yield current_key, group
''' + GB_DRIVER


PROBLEMS = [
# =====================================================================================
dict(
    id="py-count-calls",
    title="Call-Counting Decorator",
    difficulty="Easy",
    pattern="Decorators",
    kind="function",
    entry="run",
    description=r"""
Write a decorator `count_calls(func)` that wraps a function so that it **counts how many times it
has been called**. The count must be available as an attribute `calls` on the decorated function,
starting at `0`.

Requirements:

- The wrapper must accept and forward **any** positional and keyword arguments and return the
  original function's result unchanged.
- Each decorated function has its **own** counter.
- The decorated function must keep the original `__name__` and `__doc__` (use `functools.wraps`).

The starter contains a small driver `run(xs)` (do not edit it). It decorates two functions, calls
`square` once per element of `xs` and `add` once, and returns
`[squares, add_result, square.calls, add.calls, square.__name__, add.__doc__]`.

**Example:** `xs = [1, 2, 3]` → `[[1, 4, 9], 4, 3, 1, "square", "Add two numbers."]`
""",
    starter='''import functools

def count_calls(func):
    # TODO: return a wrapper that counts calls in wrapper.calls
    pass
''' + CC_DRIVER,
    solution=CC_SOLUTION,
    tests=[[[1, 2, 3]], [[]], [[5]], [[-2, 0, 2]], [list(range(10))], [[7] * 25],
           [list(range(-50, 50, 3))], [[10**6, -10**6]], [list(range(200))]],
    examples=2,
    wrong_solutions=[
        '''def count_calls(func):
    def wrapper(*args, **kwargs):
        wrapper.calls += 1
        return func(*args, **kwargs)
    wrapper.calls = 0
    return wrapper
''' + CC_DRIVER,
        '''import functools
TOTAL = [0]
def count_calls(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        TOTAL[0] += 1
        wrapper.calls = TOTAL[0]
        return func(*args, **kwargs)
    wrapper.calls = 0
    return wrapper
''' + CC_DRIVER,
    ],
    guide=dict(
        prereqs="Closures, decorators and `functools.wraps` (lessons *Scope, closures and lambdas* and *Decorators and functools*).",
        intuition="A decorator returns a new function (the wrapper) that does a little extra work and then calls the original. Functions are objects, so the wrapper can carry its own counter as an attribute.",
        hints=[
            "Inside `count_calls`, define `def wrapper(*args, **kwargs): ...` and return it.",
            "Set `wrapper.calls = 0` after defining the wrapper; increment `wrapper.calls` inside it.",
            "Decorate the wrapper with `@functools.wraps(func)` so `__name__` and `__doc__` survive.",
        ],
        brute_force="A global counter is the naive idea, but it is shared by every decorated function, so two functions would corrupt each other's counts.",
        approach="""1. `@functools.wraps(func)` on an inner `wrapper(*args, **kwargs)`.
2. In the wrapper: `wrapper.calls += 1`, then `return func(*args, **kwargs)`.
3. After the definition: `wrapper.calls = 0`; return `wrapper`.

Dry run with `xs=[1,2]`: `square(1)` → calls 1, `square(2)` → calls 2, `add(2, b=1)` → its own counter becomes 1.""",
        complexity="O(1) extra time and space per call.",
        pitfalls="""- Forgetting `return func(...)` makes every call return `None`.
- Forgetting `functools.wraps` changes `__name__` to `'wrapper'`.
- Using a `nonlocal` counter works but is invisible from outside unless you also expose it.
- A single global counter is shared across all decorated functions.""",
        follow_up="Add a `reset()` method attribute, or count calls per distinct argument tuple.",
    ),
),
# =====================================================================================
dict(
    id="py-flatten-dict",
    title="Flatten a Nested Dictionary",
    difficulty="Medium",
    pattern="Dicts & Recursion",
    entry="flatten_dict",
    description=r"""
Given a dictionary whose values may themselves be dictionaries (to any depth), return a new **flat**
dictionary whose keys are the paths to each leaf, joined with the separator `sep`.

- Keys are strings. Leaves are any non-dict value (numbers, strings, lists, `None`...); lists are
  leaves and are **not** descended into.
- An **empty nested dictionary** is kept as a leaf with value `{}`.
- Do not modify the input.

**Example 1:** `d = {"a": 1, "b": {"c": 2, "d": {"e": 3}}}, sep = "."` → `{"a": 1, "b.c": 2, "b.d.e": 3}`

**Example 2:** `d = {"x": {}, "y": [1, {"z": 2}]}, sep = "/"` → `{"x": {}, "y": [1, {"z": 2}]}`
""",
    starter='''def flatten_dict(d: dict, sep: str = ".") -> dict:
    pass
''',
    solution='''def flatten_dict(d, sep="."):
    out = {}
    def walk(node, prefix):
        for k, v in node.items():
            path = f"{prefix}{sep}{k}" if prefix else k
            if isinstance(v, dict) and v:
                walk(v, path)
            else:
                out[path] = v
    walk(d, "")
    return out
''',
    tests=[
        [{"a": 1, "b": {"c": 2, "d": {"e": 3}}}, "."],
        [{"x": {}, "y": [1, {"z": 2}]}, "/"],
        [{}, "."],
        [{"only": None}, "."],
        [{"a": {"b": {"c": {"d": {"e": "deep"}}}}}, "_"],
        [{"k1": {"k2": 1}, "k3": {"k4": {"k5": True, "k6": False}}, "k7": "s"}, "."],
        [{"a": {"": 1}}, "."],
        [{"cfg": {"db": {"host": "h", "port": 5432}, "debug": False}, "name": "app"}, "::"],
        [{f"k{i}": {f"j{j}": i * j for j in range(5)} for i in range(30)}, "."],
        [{"lvl": {"empty": {}, "full": {"x": [1, 2]}}}, "."],
    ],
    examples=2,
    wrong_solutions=['''def flatten_dict(d, sep="."):
    out = {}
    def walk(node, prefix):
        for k, v in node.items():
            path = f"{prefix}{sep}{k}" if prefix else k
            if isinstance(v, dict):
                walk(v, path)
            else:
                out[path] = v
    walk(d, "")
    return out
'''],
    guide=dict(
        prereqs="Dicts, recursion, f-strings.",
        intuition="It's a depth-first walk: carry the path so far; when you hit a non-dict (or an empty dict) you've reached a leaf and record `path -> value`.",
        hints=[
            "Write a helper `walk(node, prefix)` that loops over `node.items()`.",
            "Build the child path as `prefix + sep + key`, or just `key` at the top level.",
            "Recurse only when the value is a *non-empty* dict; everything else is a leaf.",
        ],
        brute_force="An explicit stack of `(dict, prefix)` pairs works equally well and avoids recursion limits for absurdly deep inputs.",
        approach="""```
walk(d, "")
  for k, v in node.items():
      path = prefix + sep + k if prefix else k
      if v is a non-empty dict: walk(v, path)
      else: out[path] = v
```
Dry run on `{"a": 1, "b": {"c": 2}}`: `a` is a leaf → `out["a"]=1`; `b` is a dict → recurse with prefix `b` → `out["b.c"]=2`.""",
        complexity="O(total number of keys) time; O(depth) recursion stack plus the output.",
        pitfalls="""- Empty dicts must be kept as `{}` leaves, otherwise the key disappears.
- Using `if prefix:` is fine, but note an empty-string *key* at top level would be treated like no prefix; that's acceptable here.
- Don't descend into lists.""",
        follow_up="Write the inverse `unflatten(d, sep)`; handle list indices as `a.0.b`.",
    ),
),
# =====================================================================================
dict(
    id="py-group-anagrams",
    title="Group Anagrams with defaultdict",
    difficulty="Medium",
    pattern="Dicts & Hashing",
    leetcode="https://leetcode.com/problems/group-anagrams/",
    entry="group_anagrams",
    compare="unordered_nested",
    description=r"""
Given a list of lowercase words, group together the words that are **anagrams** of each other
(same letters with the same multiplicities, in any order). Return a list of groups; the order of
groups and of words inside a group does not matter. Duplicated words stay duplicated.

Practise `collections.defaultdict(list)` and choosing a **hashable** key (a tuple or a string).

**Example:** `["eat","tea","tan","ate","nat","bat"]` → `[["eat","tea","ate"],["tan","nat"],["bat"]]`
""",
    starter='''from collections import defaultdict

def group_anagrams(words: list[str]) -> list[list[str]]:
    pass
''',
    solution='''from collections import defaultdict

def group_anagrams(words):
    groups = defaultdict(list)
    for w in words:
        counts = [0] * 26
        for c in w:
            counts[ord(c) - 97] += 1
        groups[tuple(counts)].append(w)
    return list(groups.values())
''',
    tests=[
        [["eat", "tea", "tan", "ate", "nat", "bat"]],
        [[""]],
        [["a"]],
        [[]],
        [["abc", "abc", "cba", "bca", "xyz"]],
        [["ab", "ba", "aab", "aba", "baa", "abb"]],
        [["listen", "silent", "enlist", "google", "gooegl", "inlets", "banana"]],
        [["", "", "a"]],
        [["abcdefghijklmnopqrstuvwxyz", "zyxwvutsrqponmlkjihgfedcba", "a" * 26]],
        [["".join(sorted(f"{i:04d}".translate(str.maketrans("0123456789", "abcdefghij")))) for i in range(3000)]],
    ],
    examples=2,
    wrong_solutions=['''def group_anagrams(words):
    groups = {}
    for w in words:
        groups.setdefault(frozenset(w), []).append(w)
    return list(groups.values())
'''],
    guide=dict(
        prereqs="Dicts and hashing; `defaultdict` (lesson *Dictionaries and sets*).",
        intuition="Two words are anagrams exactly when they have the same *signature*: either their sorted letters or their 26 letter counts. Use the signature as a dict key.",
        hints=[
            "What is the same for 'eat' and 'tea' but different for 'tan'?",
            "`''.join(sorted(w))` is a valid, hashable key.",
            "A tuple of 26 counts avoids the O(k log k) sort per word.",
        ],
        brute_force="Compare every pair of words with `sorted(a) == sorted(b)` and union them: O(n² · k log k).",
        approach="""1. `groups = defaultdict(list)`.
2. For each word compute `key = tuple(counts)` (or `''.join(sorted(w))`).
3. `groups[key].append(w)`.
4. Return `list(groups.values())`.""",
        complexity="O(n · k) with counting keys (O(n · k log k) with sorted keys), O(n · k) space.",
        pitfalls="""- Lists are unhashable — convert counts to a `tuple`.
- `frozenset(w)` loses multiplicities ("aab" vs "abb") — wrong.
- Remember the empty string is a valid word.""",
        follow_up="Find the largest anagram group; stream words from a file using a generator.",
    ),
),
# =====================================================================================
dict(
    id="py-deep-merge",
    title="Deep-Merge Two Dictionaries",
    difficulty="Medium",
    pattern="Dicts & Copying",
    entry="check",
    description=r"""
Write `deep_merge(a, b)` returning a **new** dictionary that combines `a` and `b` recursively:

- Keys only in one input are copied over.
- If a key exists in both and **both values are dicts**, merge them recursively.
- Otherwise the value from `b` wins (lists are replaced, not concatenated; a dict in `b` replaces a
  non-dict in `a` and vice versa).
- **Neither input may be modified**, and the result must not **share** any nested dict with the
  inputs (mutating the result must never affect `a` or `b`).

The driver `check(a, b)` (do not edit) returns `[merged, inputs_untouched_and_unshared]`.

**Example:** `a = {"db": {"host": "x", "port": 1}, "debug": False}`,
`b = {"db": {"port": 2}, "debug": True}` → `{"db": {"host": "x", "port": 2}, "debug": True}`
""",
    starter='''def deep_merge(a: dict, b: dict) -> dict:
    pass
''' + DM_DRIVER,
    solution=DM_SOLUTION,
    tests=[
        [{"db": {"host": "x", "port": 1}, "debug": False}, {"db": {"port": 2}, "debug": True}],
        [{}, {}],
        [{"a": 1}, {}],
        [{}, {"a": {"b": 1}}],
        [{"a": {"b": {"c": 1, "d": 2}}}, {"a": {"b": {"d": 3, "e": 4}}}],
        [{"a": [1, 2]}, {"a": [3]}],
        [{"a": {"x": 1}}, {"a": 5}],
        [{"a": 5}, {"a": {"x": 1}}],
        [{"keep": {"deep": {"er": {"est": 1}}}}, {"other": 2}],
        [{"l1": {"l2": {"l3": {"l4": "a"}}}, "z": None}, {"l1": {"l2": {"l3": {"l5": "b"}, "m": 0}}}],
        [{f"k{i}": {"v": i} for i in range(50)}, {f"k{i}": {"w": -i} for i in range(25, 75)}],
    ],
    examples=2,
    wrong_solutions=[
        '''def deep_merge(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict):
            deep_merge(a[k], v)
        else:
            a[k] = v
    return a
''' + DM_DRIVER,
        '''def deep_merge(a, b):
    out = dict(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out
''' + DM_DRIVER,
    ],
    guide=dict(
        prereqs="Dicts, recursion, shallow vs deep copies (lesson *Comprehensions, unpacking and copying*).",
        intuition="Start from a deep copy of `a`'s structure, then overlay `b`: whenever both sides hold a dict, recurse; otherwise `b` wins. The key subtlety is *sharing*: `dict(a)` is shallow, so nested dicts would still be shared.",
        hints=[
            "`dict(a)` or `{**a, **b}` is only a shallow merge — it replaces nested dicts wholesale and shares the rest.",
            "Recurse when `isinstance(a_val, dict) and isinstance(b_val, dict)`.",
            "Copy nested dicts that come only from `a` or only from `b` too — e.g. by merging them with `{}`.",
        ],
        brute_force="`copy.deepcopy(a)` then overlay `deepcopy(b)` values recursively — correct, just copies leaves too.",
        approach="""```
def deep_merge(a, b):
    out = {k: deep_merge(v, {}) if dict else v for a's items}
    for k, v in b.items():
        if v is dict: out[k] = deep_merge(out[k] if dict else {}, v)
        else: out[k] = v
```
Merging any dict with `{}` produces a fresh recursive copy, which handles the no-sharing rule.""",
        complexity="O(total keys in a and b) time and space.",
        pitfalls="""- Mutating `a` in place (very common!).
- Shallow `dict(a)` shares nested dicts — the driver detects this.
- Lists should be replaced, not merged.""",
        follow_up="Add a strategy parameter for lists (replace / concatenate / unique-union).",
    ),
),
# =====================================================================================
dict(
    id="py-unique-everseen",
    title="Order-Preserving Unique (Generator)",
    difficulty="Medium",
    pattern="Generators & Hashing",
    entry="run",
    description=r"""
Write a **generator** `unique_everseen(iterable, key=None)` that yields the elements of `iterable`
in order, skipping any element whose key has been seen before. The key of an element is
`key(element)` if `key` is given, otherwise the element itself.

It must also cope with **unhashable** keys (such as lists): fall back to a slower list-based check
for those, while hashable keys keep O(1) set lookups.

The driver `run(items, ignore_case)` (do not edit) passes `key=str.lower` (for strings) when
`ignore_case` is true and returns the list of yielded items.

**Example:** `items = ["A","a","b","B","a","c"], ignore_case = True` → `["A","b","c"]`

**Example:** `items = [[1], [1], 2, [2], 2], ignore_case = False` → `[[1], 2, [2]]`
""",
    starter='''def unique_everseen(iterable, key=None):
    # yield each first-seen element
    pass
''' + UE_DRIVER,
    solution=UE_SOLUTION,
    tests=[
        [["A", "a", "b", "B", "a", "c"], True],
        [[[1], [1], 2, [2], 2], False],
        [[], False],
        [[1, 1, 1, 1], False],
        [["A", "a", "b", "B", "a", "c"], False],
        [[3, 1, 3, 2, 1, 5, 2], False],
        [[1, True, 1.0, 0, False, "1"], False],
        [[[1, 2], [2, 1], [1, 2], {"k": 1}, {"k": 1}], False],
        [["x", ["x"], "X", ["x"]], True],
        [[i % 997 for i in range(20000)], False],
    ],
    examples=2,
    wrong_solutions=[
        '''def unique_everseen(iterable, key=None):
    return list(dict.fromkeys(iterable))
''' + UE_DRIVER,
        '''def unique_everseen(iterable, key=None):
    seen = []
    for x in iterable:
        if x not in seen:
            seen.append(x)
            yield x
''' + UE_DRIVER,
    ],
    guide=dict(
        prereqs="Generators, sets and hashability.",
        intuition="Remember every key you've yielded. A set gives O(1) membership but only for hashable keys; keep a list as a fallback for the rest.",
        hints=[
            "Use `yield item` the first time you see its key.",
            "Compute `k = item if key is None else key(item)`.",
            "Wrap the set check in `try/except TypeError` and fall back to a list for unhashable keys.",
        ],
        brute_force="A single list of seen keys: O(n²) on large inputs, but always correct.",
        approach="""1. `seen_set, seen_list = set(), []`.
2. For each item compute `k`; try `if k in seen_set: continue; seen_set.add(k)`.
3. On `TypeError` use `seen_list` instead.
4. `yield item`.""",
        complexity="O(n) for hashable keys, O(n·u) in the worst case for unhashable keys (u = distinct unhashable keys).",
        pitfalls="""- `1`, `True` and `1.0` are equal and hash equally, so they're duplicates.
- Returning a list instead of yielding fails the generator check.
- Forgetting to apply `key` for the comparison but yield the original item.""",
        follow_up="Implement `unique_justseen` (only remove consecutive duplicates) with `itertools.groupby`.",
    ),
),
# =====================================================================================
dict(
    id="py-memoize",
    title="Memoize Decorator with Stats",
    difficulty="Medium",
    pattern="Decorators",
    entry="run",
    description=r"""
Implement a decorator `memoize(func)` that caches results by **arguments**, like a minimal
`functools.cache`, and records statistics:

- The cache key must include positional **and** keyword arguments; calls that pass the same
  values in a different *form* (e.g. `f(2, 3)` vs `f(2, exp=3)`) may be cached separately — that's
  what `lru_cache` does too — but calls with different values must never share an entry.
- The decorated function exposes integer attributes `hits` and `misses`.
- Preserve the wrapped function's name with `functools.wraps`.
- Each decorated function has its own cache.

The driver `run(ns)` (do not edit) memoizes a recursive Fibonacci and a `power(base, exp=2)`
function, counts how many times the *underlying* bodies execute, and returns
`[fib_results, fib_body_calls, fib.hits, fib.misses, power_results, power_body_calls, power.hits, power.misses, fib.__name__]`.

**Example:** `ns = [10]` → fib body runs 11 times (n = 0..10), with 8 hits.
""",
    starter='''import functools

def memoize(func):
    pass
''' + MEMO_DRIVER,
    solution=MEMO_SOLUTION,
    tests=[[[10]], [[0]], [[1, 1, 1]], [[5, 10, 5]], [[20]], [[22, 22]], [[3, 2, 1, 0]],
           [list(range(20))], [[18, 9, 21]], [[]]],
    examples=2,
    wrong_solutions=[
        '''import functools
def memoize(func):
    cache = {}
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if args in cache:
            wrapper.hits += 1
            return cache[args]
        wrapper.misses += 1
        cache[args] = func(*args, **kwargs)
        return cache[args]
    wrapper.hits = wrapper.misses = 0
    return wrapper
''' + MEMO_DRIVER,
        '''import functools
def memoize(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        wrapper.misses += 1
        return func(*args, **kwargs)
    wrapper.hits = wrapper.misses = 0
    return wrapper
''' + MEMO_DRIVER,
    ],
    guide=dict(
        prereqs="Decorators, closures, hashing, `functools.wraps`.",
        intuition="Keep a dict in the decorator's closure. Turn the call's arguments into a hashable key; if the key is present, return the stored result (a hit), otherwise compute, store and count a miss.",
        hints=[
            "`args` is already a tuple; `kwargs` is a dict — make it hashable with `tuple(sorted(kwargs.items()))`.",
            "Recursive calls inside `fib` go through the *decorated* name, so they hit the cache automatically.",
            "Initialise `wrapper.hits = wrapper.misses = 0` after defining the wrapper.",
        ],
        brute_force="No cache: exponential time for Fibonacci (fib(30) makes ~2.7 million calls).",
        approach="""```
cache = {}
@wraps(func)
def wrapper(*args, **kwargs):
    key = (args, tuple(sorted(kwargs.items())))
    if key in cache: wrapper.hits += 1; return cache[key]
    wrapper.misses += 1
    cache[key] = result = func(*args, **kwargs)
    return result
```""",
        complexity="O(1) average per cached call; fib(n) becomes O(n) body executions. Memory grows with the number of distinct argument combinations.",
        pitfalls="""- Ignoring kwargs makes `power(2, exp=3)` and `power(2)` collide.
- Computing the value before checking the cache defeats the purpose.
- Unhashable arguments (lists) raise `TypeError`, just like `lru_cache`.""",
        follow_up="Add a `maxsize` with LRU eviction using `collections.OrderedDict` (see the LRU Cache problem).",
    ),
),
# =====================================================================================
dict(
    id="py-retry",
    title="Retry Decorator Factory",
    difficulty="Medium",
    pattern="Decorators",
    entry="run",
    description=r"""
Write a **decorator factory** `retry(times=3, exceptions=(Exception,))`. A function decorated with
`@retry(times=n, exceptions=(...))`:

- is attempted **at most `n` times in total**;
- if an attempt raises one of `exceptions` (or a subclass), it is retried;
- if an attempt raises any **other** exception, that exception propagates immediately (no retry);
- if all `n` attempts fail, the **last** exception is re-raised unchanged;
- on success, the result is returned immediately;
- the wrapper preserves `__name__`.

The driver `run(plan, times)` (do not edit) decorates a flaky function with
`@retry(times=times, exceptions=(ValueError, KeyError))`. The function consumes `plan` one outcome
per attempt: `"value"` → raises `ValueError`, `"key"` → `KeyError`, `"type"` → `TypeError`, anything
else (or an exhausted plan) → success. It returns `[result_or_error_text, attempts, name]`.

**Example:** `plan = ["value", "key", "ok"], times = 3` → `["job:ok", 3, "flaky"]`
""",
    starter='''import functools

def retry(times=3, exceptions=(Exception,)):
    pass
''' + RETRY_DRIVER,
    solution=RETRY_SOLUTION,
    tests=[
        [["value", "key", "ok"], 3],
        [["value", "value", "value", "ok"], 3],
        [["ok"], 1],
        [["value"], 1],
        [["type", "ok"], 5],
        [["value", "type", "ok"], 5],
        [["key", "key", "key", "key", "done"], 5],
        [[], 2],
        [["value"] * 9 + ["fine"], 10],
        [["value"] * 10, 10],
    ],
    examples=2,
    wrong_solutions=[
        '''import functools
def retry(times=3, exceptions=(Exception,)):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last = None
            for _ in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last = e
            raise last
        return wrapper
    return decorator
''' + RETRY_DRIVER,
        '''import functools
def retry(times=3, exceptions=(Exception,)):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last = e
            raise last
        return wrapper
    return decorator
''' + RETRY_DRIVER,
    ],
    guide=dict(
        prereqs="Decorators with arguments, exceptions (`try/except`, bare `raise`).",
        intuition="Three layers: the factory receives the options, returns a decorator that receives the function, which returns the wrapper that loops over attempts.",
        hints=[
            "`@retry(times=3)` means `f = retry(times=3)(f)`.",
            "`except exceptions:` accepts a tuple of exception classes.",
            "Inside the `except` block, if this was the last attempt, a bare `raise` re-raises the current exception.",
        ],
        brute_force="Not applicable — this is about structure. The common bug is catching `Exception` instead of only the configured exceptions.",
        approach="""```
def retry(times=3, exceptions=(Exception,)):
    def decorator(func):
        @wraps(func)
        def wrapper(*a, **k):
            for attempt in range(1, times + 1):
                try: return func(*a, **k)
                except exceptions:
                    if attempt == times: raise
        return wrapper
    return decorator
```""",
        complexity="At most `times` calls of the wrapped function; O(1) extra memory.",
        pitfalls="""- Off-by-one: `times` is the *total* number of attempts, not the number of retries.
- Catching all exceptions retries things that should fail fast (`TypeError` here).
- Writing `@retry` without parentheses passes the function as `times`.""",
        follow_up="Add exponential back-off with `time.sleep(base * 2**attempt)` and jitter, or an async version using `asyncio.sleep`.",
    ),
),
# =====================================================================================
dict(
    id="py-custom-range",
    title="Build Your Own range",
    difficulty="Medium",
    pattern="Iterator Protocol",
    entry="run",
    description=r"""
Implement a class `MyRange(start, stop, step=1)` that behaves like the built-in `range` (do not use
`range` inside it):

- **Re-iterable**: `__iter__` returns a *fresh* iterator each time (so `iter(r) is not r`) and you can
  loop over the same object many times.
- `len(r)` gives the number of elements; works for negative steps; empty ranges have length 0.
- `r[k]` supports non-negative and negative indices and raises `IndexError` when out of range.
- `x in r` must be answered in **O(1)** arithmetic (not by scanning).
- `step == 0` raises `ValueError`.

The driver `run(start, stop, step)` (do not edit) returns
`[list(r), list(r), len(r), [p for p in range(-12, 25) if p in r], r[-1] or None, iter(r) is not r]`.

**Example:** `MyRange(2, 11, 3)` → elements `[2, 5, 8]`, length 3, last element 8.
""",
    starter='''class MyRange:
    def __init__(self, start, stop, step=1):
        pass

    def __len__(self):
        pass

    def __getitem__(self, k):
        pass

    def __contains__(self, x):
        pass

    def __iter__(self):
        pass
''' + CR_DRIVER,
    solution=CR_SOLUTION,
    tests=[[2, 11, 3], [0, 5, 1], [10, 0, -3], [3, 3, 1], [5, 1, 1], [-10, 10, 4], [0, 1, 1],
           [20, -12, -5], [0, 24, 7], [7, 8, 100], [-1, -12, -1]],
    examples=3,
    wrong_solutions=[
        '''class MyRange:
    def __init__(self, start, stop, step=1):
        self.start, self.stop, self.step = start, stop, step
        self.cur = start
    def __len__(self):
        return max(0, (self.stop - self.start + self.step - 1) // self.step)
    def __getitem__(self, k):
        if k < 0: k += len(self)
        if not 0 <= k < len(self): raise IndexError
        return self.start + k * self.step
    def __iter__(self):
        return self
    def __next__(self):
        if (self.step > 0 and self.cur >= self.stop) or (self.step < 0 and self.cur <= self.stop):
            raise StopIteration
        v = self.cur
        self.cur += self.step
        return v
''' + CR_DRIVER,
    ],
    guide=dict(
        prereqs="The iterator protocol and the sequence protocol (lessons *The iterator protocol* and *The data model*).",
        intuition="A container's `__iter__` should hand out a brand-new iterator each time — a generator method is the easiest way. Length and membership are pure arithmetic on start, stop and step.",
        hints=[
            "Length for positive step: `max(0, ceil((stop - start) / step))` — do it with integer arithmetic: `(stop - start + step - 1) // step`.",
            "For negative steps mirror the formula: `(start - stop - step - 1) // -step`.",
            "`x in r` iff `(x - start) % step == 0` and `0 <= (x - start) // step < len(r)`.",
            "Make `__iter__` a generator (`yield`) so every call creates a new iterator.",
        ],
        brute_force="Store `list(...)` of all values: O(n) memory and O(n) membership — defeats the point of `range`.",
        approach="""- `__len__`: arithmetic formula above.
- `__getitem__`: normalise negative `k` by adding `len`, bounds-check, return `start + k*step`.
- `__contains__`: check type, divisibility of the offset by `step`, and that the index lies in `[0, len)`.
- `__iter__`: generator yielding `start, start+step, ...` exactly `len` times.""",
        complexity="O(1) for len, indexing and membership; O(1) memory; iteration O(n).",
        pitfalls="""- Returning `self` from `__iter__` makes the object single-use (the wrong solution).
- Off-by-one in the length formula for negative steps.
- Python's `%` with a negative step: `offset % step` is 0 exactly when divisible, which is all we need.""",
        follow_up="Support slicing: `r[1:5]` should return another `MyRange`, as the built-in does.",
    ),
),
# =====================================================================================
dict(
    id="py-flatten",
    title="Flatten Nested Lists with a Generator",
    difficulty="Easy",
    pattern="Generators",
    entry="run",
    description=r"""
Write a **generator** `flatten(nested)` that yields every non-list, non-tuple element of an
arbitrarily nested structure of lists and tuples, in left-to-right order. Strings are atoms (do not
split them into characters). Empty lists contribute nothing.

The driver `run(nested)` (do not edit) checks that `flatten` returns a generator and lists it.

**Example:** `[1, [2, [3, [4]], 5], [], "ab"]` → `[1, 2, 3, 4, 5, "ab"]`
""",
    starter='''def flatten(nested):
    pass
''' + FL_DRIVER,
    solution=FL_SOLUTION,
    tests=[
        [[1, [2, [3, [4]], 5], [], "ab"]],
        [[]],
        [[[[[]]]]],
        [[1, 2, 3]],
        [["hello", ["world", ["!"]]]],
        [[[1, [2]], [[3, 4], 5], [[[6]]], 7]],
        [[None, [False, [0, [""]]]]],
        [[[i, [i * 2, [i * 3]]] for i in range(200)]],
        [_deep(300)],
    ],
    examples=2,
    wrong_solutions=['''def flatten(nested):
    out = []
    def go(x):
        for i in x:
            if isinstance(i, list):
                go(i)
            else:
                out.append(i)
    go(nested)
    return out
''' + FL_DRIVER],
    guide=dict(
        prereqs="Generators and `yield from` (lesson *Generators and yield from*).",
        intuition="Walk the structure recursively; whenever an element is itself a list/tuple, delegate to a recursive generator with `yield from`; otherwise yield it.",
        hints=[
            "Use `isinstance(item, (list, tuple))` to decide whether to descend.",
            "`yield from flatten(item)` re-yields everything the recursive call produces.",
            "Don't treat strings as iterables to descend into — a 1-char string contains itself.",
        ],
        brute_force="Build a result list recursively and return it — correct output but not lazy (fails the generator check) and uses O(n) memory.",
        approach="""```
def flatten(nested):
    for item in nested:
        if isinstance(item, (list, tuple)):
            yield from flatten(item)
        else:
            yield item
```""",
        complexity="O(total elements) time; O(depth) generator frames.",
        pitfalls="""- Descending into strings → infinite recursion.
- Forgetting `yield from` and writing `flatten(item)` alone does nothing (it just creates a generator).
- Very deep nesting (> ~900 levels) hits the recursion limit; an explicit stack of iterators avoids it.""",
        follow_up="Rewrite it iteratively with a stack of iterators so depth is unlimited.",
    ),
),
# =====================================================================================
dict(
    id="py-chunked",
    title="Lazily Chunk an Iterable",
    difficulty="Easy",
    pattern="Generators & itertools",
    entry="run",
    description=r"""
Write a generator `chunked(iterable, n)` (with `n >= 1`) that yields consecutive **lists** of `n`
items; the last chunk may be shorter. It must work on any iterable, including one-shot iterators,
and must be **lazy**: producing the first chunk may not consume more than `n + 1` items of the source.

The driver `run(data, n)` (do not edit) feeds `data` through a counting generator, takes the first
chunk, records whether the function was lazy, then collects the rest. It returns `[chunks, lazy]`.

**Example:** `data = [1,2,3,4,5], n = 2` → `[[[1,2],[3,4],[5]], true]`
""",
    starter='''from itertools import islice

def chunked(iterable, n):
    pass
''' + CH_DRIVER,
    solution=CH_SOLUTION,
    tests=[[[1, 2, 3, 4, 5], 2], [[], 3], [[1], 1], [[1, 2, 3], 3], [[1, 2, 3], 5],
           [list(range(10)), 1], [list("abcdefgh"), 3], [list(range(1000)), 7], [list(range(8000)), 500]],
    examples=2,
    wrong_solutions=['''def chunked(iterable, n):
    items = list(iterable)
    for i in range(0, len(items), n):
        yield items[i:i + n]
''' + CH_DRIVER],
    guide=dict(
        prereqs="Iterators, generators and `itertools.islice`.",
        intuition="Grab up to `n` items at a time from a single shared iterator; stop when a grab comes back empty.",
        hints=[
            "Call `iter(iterable)` once, outside the loop.",
            "`list(islice(it, n))` takes at most n items from the iterator.",
            "An empty chunk means the source is exhausted — `return`.",
        ],
        brute_force="`list(iterable)` and slice it — simple but reads everything up front (not lazy, O(N) memory).",
        approach="""```
it = iter(iterable)
while True:
    chunk = list(islice(it, n))
    if not chunk: return
    yield chunk
```
With Python 3.12+ you could also use `itertools.batched` (which yields tuples).""",
        complexity="O(N) total time; O(n) memory per chunk.",
        pitfalls="""- Calling `iter(iterable)` inside the loop restarts lists from the beginning → infinite loop.
- Using `len()` or slicing requires a sequence, not any iterable.
- Yielding an empty final chunk.""",
        follow_up="Write `chunked_padded(iterable, n, fill)` using the `zip_longest(*[it]*n)` trick.",
    ),
),
# =====================================================================================
dict(
    id="py-moving-average",
    title="Sliding-Window Moving Average Generator",
    difficulty="Medium",
    pattern="Generators & deque",
    entry="run",
    compare="float",
    description=r"""
Write a generator `moving_average(iterable, k)` that yields the average of each **full** window of
`k` consecutive values from `iterable` (`k >= 1`). Nothing is yielded until the first `k` values have
arrived. Each new value must be processed in **O(1)** time — keep a running sum and use a
`collections.deque` to know which value leaves the window.

The driver `run(values, k)` (do not edit) passes an iterator over `values` and lists the output.

**Example:** `values = [1, 2, 3, 4, 5, 6], k = 3` → `[2.0, 3.0, 4.0, 5.0]`
""",
    starter='''from collections import deque

def moving_average(iterable, k):
    pass
''' + MA_DRIVER,
    solution=MA_SOLUTION,
    tests=[[[1, 2, 3, 4, 5, 6], 3], [[], 2], [[5], 1], [[5], 2], [[1, 2], 2], [[-1, 1, -1, 1, -1], 2],
           [[0.5, 1.5, 2.5, 3.5], 4], [[10] * 20, 5], [list(range(6000)), 50],
           [[(i * 37) % 101 - 50 for i in range(5000)], 7]],
    examples=2,
    wrong_solutions=['''from collections import deque
def moving_average(iterable, k):
    window = deque(maxlen=k)
    for x in iterable:
        window.append(x)
        yield sum(window) / k
''' + MA_DRIVER],
    guide=dict(
        prereqs="Generators, `collections.deque` (lessons *Generators* and *collections*).",
        intuition="The window slides one step at a time: add the newcomer to a running total and subtract the value that falls out. A deque holds the window so you know which value leaves.",
        hints=[
            "Keep `total` and a `deque` of the current window.",
            "When the deque grows beyond `k`, `popleft()` and subtract that value from `total`.",
            "Only `yield total / k` once the window is full.",
        ],
        brute_force="Recompute `sum(window)` for each window: O(k) per item, O(N·k) total.",
        approach="""```
window, total = deque(), 0
for x in iterable:
    window.append(x); total += x
    if len(window) > k: total -= window.popleft()
    if len(window) == k: yield total / k
```
Dry run `[1,2,3,4], k=2`: totals 1 → 3 (yield 1.5) → 5 (yield 2.5) → 7 (yield 3.5).""",
        complexity="O(1) amortised per value, O(k) memory.",
        pitfalls="""- Yielding partial windows before the window is full.
- Floating-point drift over very long streams (could periodically recompute the sum or use `math.fsum`).
- Using a list and `pop(0)` makes each step O(k).""",
        follow_up="Yield a moving median instead (two heaps with lazy deletion) — much harder!",
    ),
),
# =====================================================================================
dict(
    id="py-groupby",
    title="Implement groupby",
    difficulty="Medium",
    pattern="Generators & itertools",
    entry="run",
    description=r"""
Re-implement the core of `itertools.groupby` **without importing itertools**: write a generator
`group_consecutive(iterable, key=None)` that yields `(key_value, items)` pairs for each run of
**consecutive** elements with equal key, where `items` is a list of those elements in order. If
`key` is `None`, the element itself is the key. Equal keys separated by other keys form separate
groups (no sorting!).

The driver `run(items, key_name)` (do not edit) maps `key_name` to a function
(`"identity"` → `None`, `"len"`, `"lower"`, `"parity"` → `n % 2`, `"sign"` → −1/0/1) and returns
`[[key, items], ...]`.

**Example:** `items = [1, 1, 2, 3, 3, 1], key_name = "identity"` → `[[1,[1,1]],[2,[2]],[3,[3,3]],[1,[1]]]`
""",
    starter='''def group_consecutive(iterable, key=None):
    pass
''' + GB_DRIVER,
    solution=GB_SOLUTION,
    tests=[
        [[1, 1, 2, 3, 3, 1], "identity"],
        [[], "identity"],
        [["a"], "identity"],
        [["ant", "bee", "cow", "dodo", "emu", "frog"], "len"],
        [["A", "a", "B", "b", "b", "A"], "lower"],
        [[2, 4, 6, 1, 3, 8, 10, 12, 5], "parity"],
        [[-3, -1, 0, 0, 4, 5, -2, 0], "sign"],
        [[None, None, 0, 0, False], "identity"],
        [[i // 3 for i in range(3000)], "identity"],
    ],
    examples=2,
    wrong_solutions=['''def group_consecutive(iterable, key=None):
    key = key or (lambda x: x)
    groups = {}
    for x in iterable:
        groups.setdefault(key(x), []).append(x)
    yield from groups.items()
''' + GB_DRIVER],
    guide=dict(
        prereqs="Generators, iterators; the `groupby` section of *itertools and lazy pipelines*.",
        intuition="Walk the items once, remembering the current key and the current group. When the key changes, emit the finished group and start a new one. Don't forget the last group.",
        hints=[
            "Default `key` to the identity function.",
            "Keep `current_key` and `group = []`; compare each new key against `current_key`.",
            "After the loop, `yield` the final group if it is non-empty.",
        ],
        brute_force="A dict of key → list groups *all* equal keys together, which is a different operation (the wrong solution).",
        approach="""```
group, current = [], <sentinel>
for x in iterable:
    k = key(x)
    if group and k != current:
        yield current, group; group = []
    current = k; group.append(x)
if group: yield current, group
```
Use a fresh `object()` sentinel or the `group` emptiness check so that `None` works as a real key.""",
        complexity="O(n) time; O(size of the largest group) memory (the real `groupby` uses O(1) by yielding lazy sub-iterators).",
        pitfalls="""- Losing the last group.
- Using `None` as a "no key yet" marker breaks when `None` is a real key.
- Grouping non-consecutive equal keys together.""",
        follow_up="Yield lazy sub-iterators instead of lists, as the real `groupby` does — and handle a consumer that skips a group.",
    ),
),
# =====================================================================================
dict(
    id="py-run-length",
    title="Run-Length Encoding",
    difficulty="Easy",
    pattern="itertools.groupby",
    entry="rle",
    description=r"""
Compress a string with run-length encoding: each maximal run of the same character becomes the
character followed by the run length, except that runs of length **1** are written as the bare
character. Return the encoded string. (The input contains no digits.)

Practise `itertools.groupby` and `str.join`.

**Example:** `"aaabccdddd"` → `"a3bc2d4"`

**Example:** `"abc"` → `"abc"`
""",
    starter='''from itertools import groupby

def rle(s: str) -> str:
    pass
''',
    solution='''from itertools import groupby

def rle(s):
    parts = []
    for ch, run in groupby(s):
        n = sum(1 for _ in run)
        parts.append(ch if n == 1 else f"{ch}{n}")
    return "".join(parts)
''',
    tests=[["aaabccdddd"], ["abc"], [""], ["a"], ["aaaaaaaaaaaa"], ["aabbaa"], ["  x  "],
           ["zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"],
           ["ab" * 500 + "c" * 1000], ["AaAa"]],
    examples=2,
    wrong_solutions=['''from collections import Counter
def rle(s):
    return "".join(c if n == 1 else f"{c}{n}" for c, n in Counter(s).items())
'''],
    guide=dict(
        prereqs="`itertools.groupby`, string building with `join`.",
        intuition="`groupby` already splits a string into runs of equal consecutive characters; you just need each run's length.",
        hints=[
            "`for ch, run in groupby(s):` — `run` is an iterator over the repeated characters.",
            "Its length is `sum(1 for _ in run)` or `len(list(run))`.",
            "Collect pieces in a list and `''.join` at the end.",
        ],
        brute_force="A manual index loop comparing `s[i]` with `s[i-1]` — fine too, just more bookkeeping.",
        approach="Loop over `groupby(s)`, append `ch` or `f'{ch}{n}'`, join. Dry run: `aaab` → groups (a,3),(b,1) → `a3b`.",
        complexity="O(n) time and space.",
        pitfalls="""- `Counter` merges non-adjacent runs (`aabbaa` → wrong).
- Building the result with `+=` in a loop can be quadratic.
- Remember runs of length 1 have no number.""",
        follow_up="Write the decoder; then handle inputs containing digits by always writing counts.",
    ),
),
]
