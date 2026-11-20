"""JavaScript problems: values, functions, closures and data structures."""


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


COUNTER_DRIVER = r'''
// --- driver (provided, do not change) ---
function runCounters(setups, ops) {
  const counters = setups.map(([start, step]) => makeCounter(start, step));
  return ops.map(([index, action]) => counters[index][action]());
}
'''

MEMO_DRIVER = r'''
// --- driver (provided, do not change) ---
function runMemo(calls) {
  let computed = 0;
  const weigh = (a, b) => { computed++; return a * a + 3 * b; };
  const fast = memoize(weigh);
  const results = calls.map(([a, b]) => fast(a, b));
  return [results, computed];
}
'''

CLONE_DRIVER = r'''
// --- driver (provided, do not change) ---
function cloneCheck(value, path, replacement) {
  const copy = deepClone(value);
  let target = value;
  for (let i = 0; i < path.length - 1; i++) target = target[path[i]];
  if (path.length > 0) target[path[path.length - 1]] = replacement;   // damage the original
  return { copy, sameReference: copy === value && typeof value === "object" && value !== null };
}
'''

PROBLEMS = [
dict(
    id="js-loose-equals", title="Rebuild the == operator", difficulty="Medium", pattern="Type coercion",
    kind="js", entry="looseEquals",
    description=r"""
The loose equality operator `==` converts its operands before comparing them. Write `looseEquals(a, b)` that
returns exactly what `a == b` would return, **without using `==` or `!=`** (use `===` and explicit conversions).

Inputs are JSON primitives only: `null`, booleans, finite numbers and strings.

The rules you need:

1. Two values of the same type are compared with `===`.
2. `null` is loosely equal only to `null` (and to `undefined`, which never appears here).
3. A boolean is first turned into a number (`true` → `1`, `false` → `0`), then the comparison starts again.
4. A string compared with a number is converted with `Number(...)`.

**Examples:** `looseEquals(1, "1")` → `true` · `looseEquals(null, 0)` → `false` · `looseEquals("", false)` → `true`
""",
    starter="function looseEquals(a, b) {\n  // no == or != allowed: use === plus explicit conversions\n}\n",
    solution=r'''function looseEquals(a, b) {
  if (a === null || b === null) return a === b;
  if (typeof a === typeof b) return a === b;
  if (typeof a === "boolean") return looseEquals(Number(a), b);
  if (typeof b === "boolean") return looseEquals(a, Number(b));
  return Number(a) === Number(b);
}
''',
    tests=[[1, "1"], [None, 0], ["", False], [0, False], [None, None], [None, False], ["1", True], ["true", True],
           [" 12 ", 12], ["abc", "abc"], ["0", False], ["1", "01"], [True, 2], ["0x10", 16], [None, ""], ["a", "b"],
           [1.5, "1.50"], [False, False]],
    wrong_solutions=[
        "function looseEquals(a, b) { return a === b; }\n",
        "function looseEquals(a, b) { return String(a) === String(b); }\n",
        "function looseEquals(a, b) { return Boolean(a) === Boolean(b); }\n",
        "function looseEquals(a, b) { if (typeof a === typeof b) return a === b; return Number(a) === Number(b); }\n",
    ],
    guide=G(
        prereqs="The lesson *Type coercion and equality*: `typeof`, `Number()` conversion of strings and booleans, and why `null` is special.",
        intuition="`==` is not magic; it is a short decision table. Same types: strict comparison. `null`: only matches itself. Otherwise everything is pushed towards **numbers**: booleans first, then strings.",
        hints=[
            "Handle `null` before anything else. `typeof null` is `\"object\"`, so a type check alone will not isolate it.",
            "A boolean never gets compared as a boolean against another type. Convert it to `0` or `1` and call your function again.",
            "After nulls and booleans are gone, the only mixed pair left is string versus number: compare `Number(a) === Number(b)`.",
        ],
        brute_force="Enumerating every pair of types (4 × 4 = 16 cases) with a nested `switch` works, but most cases collapse into the three rules above.",
        approach="1. If either side is `null`, answer `a === b`.\n2. If the types match, answer `a === b`.\n3. If one side is a boolean, replace it by its number and recurse.\n4. Otherwise compare the numeric conversions.\n\n**Dry run** `looseEquals(\"1\", true)`: no nulls; types differ; `b` is boolean → `looseEquals(\"1\", 1)`; types differ, no booleans → `Number(\"1\") === 1` → `true`. And `looseEquals(\"true\", true)` → `looseEquals(\"true\", 1)` → `NaN === 1` → `false`.",
        complexity="O(1) time and space; at most two recursive calls happen.",
        pitfalls="- `null == 0` and `null == false` are **false** even though `Number(null)` is `0`; `null` is never converted.\n- `\"true\" == true` is false: the boolean becomes `1`, the string becomes `NaN`.\n- Comparing with `String()` breaks `\" 12 \" == 12` and `0 == false`.",
        follow_up="Extend the function to arrays and objects: an object is converted to a primitive (usually through `toString`) before the rules above apply, which is why `[1] == 1` is true.",
    ),
),
dict(
    id="js-collatz-steps", title="Collatz step counter", difficulty="Easy", pattern="Loops",
    kind="js", entry="collatzSteps",
    description=r"""
Start with a positive integer `n`. Repeat: if the number is even, halve it; if it is odd, replace it by
`3 * n + 1`. Return how many steps it takes to reach `1`.

`collatzSteps(1)` is `0` because no step is needed.

**Examples:** `collatzSteps(6)` → `8` (6 → 3 → 10 → 5 → 16 → 8 → 4 → 2 → 1) · `collatzSteps(16)` → `4`
""",
    starter="function collatzSteps(n) {\n  // your code\n}\n",
    solution="function collatzSteps(n) {\n  let steps = 0;\n  while (n !== 1) {\n    n = n % 2 === 0 ? n / 2 : 3 * n + 1;\n    steps++;\n  }\n  return steps;\n}\n",
    tests=[[6], [16], [1], [2], [3], [7], [27], [97], [1024], [871], [9999], [837799]],
    wrong_solutions=[
        "function collatzSteps(n) {\n  let steps = 1;\n  while (n !== 1) { n = n % 2 === 0 ? n / 2 : 3 * n + 1; steps++; }\n  return steps;\n}\n",
        "function collatzSteps(n) {\n  let steps = 0;\n  while (n > 1) { n = n % 2 === 0 ? n / 2 : (3 * n + 1) / 2; steps++; }\n  return steps;\n}\n",
    ],
    guide=G(
        prereqs="`while` loops, the remainder operator `%`, the conditional operator `? :` (lesson *Program structure*).",
        intuition="This is a direct simulation: keep one binding for the current number and one for the count, and loop until the number is 1.",
        hints=[
            "You do not know the number of iterations in advance, so a `while` loop fits better than a `for` with a fixed bound.",
            "`n % 2 === 0` tests for evenness.",
            "Increase the counter once per transformation, and make sure `n = 1` returns `0`.",
        ],
        brute_force="The simulation *is* the brute force; there is no known closed formula.",
        approach="Set `steps = 0`. While `n !== 1`: compute the next value, add one to `steps`. Return `steps`.\n\n**Dry run** for `n = 6`: 6→3 (1), 3→10 (2), 10→5 (3), 5→16 (4), 16→8 (5), 8→4 (6), 4→2 (7), 2→1 (8). Answer 8.",
        complexity="Time proportional to the length of the sequence (unknown in general, small in practice); O(1) space.",
        pitfalls="- Starting the counter at 1 gives an off-by-one error.\n- Do not use recursion without care: long chains are fine here, but a loop is simpler.\n- The values stay far below `Number.MAX_SAFE_INTEGER` for the tested inputs.",
    ),
),
dict(
    id="js-counter-factory", title="Counter factory (closures)", difficulty="Easy", pattern="Closures",
    kind="js", entry="runCounters",
    description=r"""
Write `makeCounter(start, step)` that returns an object with four methods sharing **private** state:

- `inc()` adds `step` and returns the new value
- `dec()` subtracts `step` and returns the new value
- `value()` returns the current value
- `reset()` goes back to `start` and returns it

Each counter created by the factory must be independent of every other one. The provided driver
`runCounters(setups, ops)` builds one counter per `[start, step]` pair, then performs `ops`
(`[counterIndex, methodName]`) and returns the list of results.

**Example:** `runCounters([[0, 1], [10, 5]], [[0,"inc"], [1,"inc"], [0,"inc"], [1,"dec"], [0,"value"]])` → `[1, 15, 2, 10, 2]`
""",
    starter="function makeCounter(start, step) {\n  // return { inc, dec, value, reset } that close over private state\n}\n" + COUNTER_DRIVER,
    solution="function makeCounter(start, step) {\n  let current = start;\n  return {\n    inc() { current += step; return current; },\n    dec() { current -= step; return current; },\n    value() { return current; },\n    reset() { current = start; return current; },\n  };\n}\n" + COUNTER_DRIVER,
    tests=[
        [[[0, 1], [10, 5]], [[0, "inc"], [1, "inc"], [0, "inc"], [1, "dec"], [0, "value"]]],
        [[[0, 1]], [[0, "value"]]],
        [[[5, 2]], [[0, "inc"], [0, "inc"], [0, "reset"], [0, "inc"]]],
        [[[0, 1], [0, 1]], [[0, "inc"], [0, "inc"], [1, "value"], [1, "inc"]]],
        [[[-3, 3]], [[0, "dec"], [0, "dec"], [0, "value"], [0, "reset"], [0, "value"]]],
        [[[100, 0]], [[0, "inc"], [0, "dec"], [0, "value"]]],
        [[[1, 1], [2, 2], [3, 3]], [[2, "inc"], [1, "inc"], [0, "inc"], [2, "inc"], [2, "reset"], [1, "value"], [2, "value"]]],
        [[[0, 0.5]], [[0, "inc"], [0, "inc"], [0, "inc"], [0, "dec"]]],
        [[[7, 7]], []],
        [[[0, 1], [0, 10]], [[1, "inc"], [1, "inc"], [0, "reset"], [1, "value"], [0, "dec"], [1, "reset"], [1, "inc"]]],
    ],
    wrong_solutions=[
        "let current = 0;\nfunction makeCounter(start, step) {\n  current = start;\n  return {\n    inc() { current += step; return current; },\n    dec() { current -= step; return current; },\n    value() { return current; },\n    reset() { current = start; return current; },\n  };\n}\n" + COUNTER_DRIVER,
        "function makeCounter(start, step) {\n  let current = start;\n  return {\n    inc() { current += step; return current; },\n    dec() { current -= step; return current; },\n    value() { return current; },\n    reset() { current = 0; return current; },\n  };\n}\n" + COUNTER_DRIVER,
        "function makeCounter(start, step) {\n  let current = start;\n  return {\n    inc() { return current + step; },\n    dec() { return current - step; },\n    value() { return current; },\n    reset() { current = start; return current; },\n  };\n}\n" + COUNTER_DRIVER,
    ],
    guide=G(
        prereqs="Closures (lesson *Closures and recursion*): an inner function keeps access to the bindings of the call that created it.",
        intuition="Every call of `makeCounter` creates a fresh set of local bindings. The four methods are created inside that call, so they all see the same `current`, and nobody else can.",
        hints=[
            "Declare `let current = start;` inside `makeCounter`, not outside it.",
            "Return an object literal whose methods read and write `current`.",
            "`reset` must remember the original `start`; it is a parameter, so the closure already holds it.",
        ],
        brute_force="A global variable works for one counter only; the second counter overwrites the first. That is exactly the bug closures solve.",
        approach="Create `current`, return `{ inc, dec, value, reset }`.\n\n**Dry run** with setups `[[0,1],[10,5]]`: counter A has `current=0`, counter B has `current=10`. `A.inc()` → 1, `B.inc()` → 15, `A.inc()` → 2, `B.dec()` → 10, `A.value()` → 2.",
        complexity="O(1) per operation; one small environment per counter.",
        pitfalls="- Sharing state between counters by declaring it at module level.\n- Returning `current + step` without storing it.\n- Resetting to `0` instead of the original start.",
        follow_up="Rewrite it as a `class Counter` with a `#current` private field and compare the two styles.",
    ),
),
dict(
    id="js-memoize", title="Memoize a function", difficulty="Medium", pattern="Closures",
    kind="js", entry="runMemo",
    description=r"""
Write `memoize(fn)` returning a new function that behaves like `fn` but remembers earlier results:
calling it again with the **same list of arguments** must return the stored result without calling `fn`.

Arguments are JSON values (numbers here), so `JSON.stringify(args)` is a valid cache key.

The driver calls a two-argument function through your wrapper and returns
`[results, howManyTimesTheRealFunctionRan]`.

**Example:** `runMemo([[2, 1], [2, 1], [1, 2]])` → `[[7, 7, 7], 2]` (the function computes `a*a + 3*b`)
""",
    starter="function memoize(fn) {\n  // return a caching wrapper around fn\n}\n" + MEMO_DRIVER,
    solution="function memoize(fn) {\n  const cache = new Map();\n  return function (...args) {\n    const key = JSON.stringify(args);\n    if (!cache.has(key)) cache.set(key, fn.apply(this, args));\n    return cache.get(key);\n  };\n}\n" + MEMO_DRIVER,
    tests=[
        [[[2, 1], [2, 1], [1, 2]]],
        [[]],
        [[[0, 0]]],
        [[[0, 0], [0, 0], [0, 0]]],
        [[[1, 2], [2, 1], [1, 2], [2, 1]]],
        [[[3, 4], [3, 5], [3, 4], [4, 4]]],
        [[[1, 23], [12, 3]]],
        [[[0, 1], [0, 2], [0, 1], [1, 0], [1, 0]]],
        [[[-1, -1], [1, -1], [-1, -1]]],
        [[[i % 5, i % 3] for i in range(60)]],
        [[[2, 0], [0, 0], [2, 0], [0, 0]]],
    ],
    wrong_solutions=[
        "function memoize(fn) {\n  return function (...args) { return fn(...args); };\n}\n" + MEMO_DRIVER,
        "function memoize(fn) {\n  const cache = {};\n  return function (...args) {\n    const key = args[0];\n    if (!(key in cache)) cache[key] = fn(...args);\n    return cache[key];\n  };\n}\n" + MEMO_DRIVER,
        "function memoize(fn) {\n  const cache = {};\n  return function (...args) {\n    const key = args.join('');\n    if (!cache[key]) cache[key] = fn(...args);\n    return cache[key];\n  };\n}\n" + MEMO_DRIVER,
    ],
    guide=G(
        prereqs="Closures, rest parameters `...args`, `Map` (lessons *Closures and recursion*, *Prototypes, classes and encapsulation*).",
        intuition="The wrapper owns a private table from *argument list* to *result*. Look in the table first; only call the real function on a miss.",
        hints=[
            "The cache must live in the closure created by `memoize`, so each memoized function has its own.",
            "Build one key from all the arguments, for instance with `JSON.stringify(args)`.",
            "Test membership with `cache.has(key)`, not with truthiness: a stored result may be `0`.",
        ],
        brute_force="Calling `fn` every time is correct but defeats the purpose: the driver counts real calls, so it will notice.",
        approach="```\ncache = new Map()\nwrapper(...args):\n  key = JSON.stringify(args)\n  if key not in cache: cache[key] = fn(...args)\n  return cache[key]\n```\n**Dry run** for `[[2,1],[2,1],[1,2]]`: key `[2,1]` misses → compute 7 (count 1). Same key hits → 7. Key `[1,2]` misses → 7 (count 2). Result `[[7,7,7],2]`.",
        complexity="O(k) per call to build the key for k arguments; memory grows with the number of distinct argument lists.",
        pitfalls="- Keying on the first argument only confuses `(3,4)` with `(3,5)`.\n- `args.join('')` maps `(1,23)` and `(12,3)` to the same key.\n- `if (!cache[key])` recomputes whenever the cached result is falsy (`0`, `\"\"`, `false`).",
        follow_up="Add a maximum size and evict the least recently used entry (see the LRU cache problem).",
    ),
),
dict(
    id="js-permutations", title="All permutations", difficulty="Medium", pattern="Recursion",
    kind="js", entry="permutations",
    description=r"""
Given an array of distinct values, return every ordering of them. Produce the orderings in this order:
choose the first element by going through the input from left to right, and for each choice list all
permutations of the remaining elements (keeping their relative order) in the same way.

**Examples:** `permutations([1,2,3])` → `[[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]` · `permutations([])` → `[[]]`
""",
    starter="function permutations(items) {\n  // your code\n}\n",
    solution="function permutations(items) {\n  if (items.length === 0) return [[]];\n  const out = [];\n  for (let i = 0; i < items.length; i++) {\n    const rest = [...items.slice(0, i), ...items.slice(i + 1)];\n    for (const tail of permutations(rest)) out.push([items[i], ...tail]);\n  }\n  return out;\n}\n",
    tests=[[[1, 2, 3]], [[]], [[7]], [[1, 2]], [["a", "b", "c"]], [[3, 1, 2]], [[1, 2, 3, 4]], [[True, False]],
           [["x", 1, None]], [[5, 4, 3, 2, 1]], [[1, 2, 3, 4, 5, 6]]],
    wrong_solutions=[
        "function permutations(items) {\n  const out = [];\n  for (let i = 0; i < items.length; i++) out.push([...items.slice(i), ...items.slice(0, i)]);\n  return out;\n}\n",
        "function permutations(items) {\n  if (items.length === 0) return [];\n  const out = [];\n  for (let i = 0; i < items.length; i++) {\n    const rest = [...items.slice(0, i), ...items.slice(i + 1)];\n    for (const tail of permutations(rest)) out.push([items[i], ...tail]);\n  }\n  return out;\n}\n",
        "function permutations(items) {\n  if (items.length <= 1) return [items];\n  const out = [];\n  for (let i = 0; i < items.length; i++) {\n    const rest = items.slice(i + 1).concat(items.slice(0, i));\n    for (const tail of permutations(rest)) out.push([items[i], ...tail]);\n  }\n  return out;\n}\n",
    ],
    guide=G(
        prereqs="Recursion with a base case, `slice`, spread syntax (lessons *Closures and recursion*, *Destructuring, spread, rest and JSON*).",
        intuition="A permutation is *a first element* followed by *a permutation of everything else*. That sentence is already the recursive program.",
        hints=[
            "What are the permutations of an empty array? Exactly one: the empty arrangement. So the base case returns `[[]]`, not `[]`.",
            "Loop over the index `i` of the element that goes first; build `rest` without that element.",
            "Prefix every permutation of `rest` with `items[i]` and collect the results.",
        ],
        brute_force="Generating all n^n sequences and filtering those without repeats works for tiny n but wastes almost all its effort.",
        approach="```\nperm(items): if empty → [[]]\n  for each i: for each tail in perm(items without i): emit [items[i], ...tail]\n```\n**Dry run** `[1,2,3]`: first=1, rest `[2,3]` → `[2,3]`, `[3,2]` → `[1,2,3]`, `[1,3,2]`; first=2, rest `[1,3]` → `[2,1,3]`, `[2,3,1]`; first=3 → `[3,1,2]`, `[3,2,1]`.",
        complexity="There are n! results of length n, so time and space are O(n · n!).",
        pitfalls="- Returning `[]` for the empty input makes every level return nothing.\n- Rotating instead of removing yields only n of the n! orderings.\n- Building `rest` in rotated order changes the required output order.",
        follow_up="Handle duplicates (skip a choice equal to an earlier one at the same depth), or write it as a generator that yields one permutation at a time.",
    ),
),
dict(
    id="js-deep-equal", title="Deep equality", difficulty="Medium", pattern="Objects & recursion",
    kind="js", entry="deepEqual",
    description=r"""
`===` compares objects by identity, so `{a: 1} === {a: 1}` is `false`. Write `deepEqual(a, b)` that
compares two JSON values **by content**:

- primitives and `null` are equal when `===` says so
- arrays are equal when they have the same length and equal elements position by position
- plain objects are equal when they have the same set of keys and equal values per key (key order is irrelevant)
- an array is never equal to a plain object

**Examples:** `deepEqual({a:[1,2]}, {a:[1,2]})` → `true` · `deepEqual([1,2], [2,1])` → `false` · `deepEqual({}, [])` → `false`
""",
    starter="function deepEqual(a, b) {\n  // your code\n}\n",
    solution="function deepEqual(a, b) {\n  if (a === b) return true;\n  if (a === null || b === null || typeof a !== \"object\" || typeof b !== \"object\") return false;\n  if (Array.isArray(a) !== Array.isArray(b)) return false;\n  const ka = Object.keys(a), kb = Object.keys(b);\n  if (ka.length !== kb.length) return false;\n  for (const k of ka) {\n    if (!Object.hasOwn(b, k) || !deepEqual(a[k], b[k])) return false;\n  }\n  return true;\n}\n",
    tests=[
        [{"a": [1, 2]}, {"a": [1, 2]}], [[1, 2], [2, 1]], [{}, []], [1, 1], [1, "1"], [None, None], [None, {}],
        [{"a": 1, "b": 2}, {"b": 2, "a": 1}], [{"a": 1}, {"a": 1, "b": None}], [{"a": None}, {"b": None}],
        [[1, [2, [3, {"x": [4]}]]], [1, [2, [3, {"x": [4]}]]]], [[1, [2, [3, {"x": [4]}]]], [1, [2, [3, {"x": [5]}]]]],
        [[], []], [[1, 2, 3], [1, 2]], [{"0": "a", "1": "b"}, ["a", "b"]], ["abc", "abc"], [0, False],
        [{"a": {"b": {"c": 1}}}, {"a": {"b": {"c": 1}}}],
    ],
    wrong_solutions=[
        "function deepEqual(a, b) { return JSON.stringify(a) === JSON.stringify(b); }\n",
        "function deepEqual(a, b) {\n  if (a === b) return true;\n  if (a === null || b === null || typeof a !== 'object' || typeof b !== 'object') return false;\n  for (const k of Object.keys(a)) if (!deepEqual(a[k], b[k])) return false;\n  return true;\n}\n",
        "function deepEqual(a, b) {\n  if (a === b) return true;\n  if (a === null || b === null || typeof a !== 'object' || typeof b !== 'object') return false;\n  const ka = Object.keys(a), kb = Object.keys(b);\n  if (ka.length !== kb.length) return false;\n  for (const k of ka) if (!deepEqual(a[k], b[k])) return false;\n  return true;\n}\n",
        "function deepEqual(a, b) { return a == b; }\n",
    ],
    guide=G(
        prereqs="Objects versus primitives, `typeof`, `Object.keys`, recursion (lesson *Objects, arrays and mutability*).",
        intuition="Two structures are equal when they have the same *shape* and equal *leaves*. Check the cheap things first (identity, type, size), then recurse into each key.",
        hints=[
            "`typeof null` is `\"object\"`; rule out `null` explicitly before treating a value as an object.",
            "Compare the number of keys first; then it is enough to check that every key of `a` exists in `b` with an equal value.",
            "Use `Array.isArray` on both sides so that `[\"a\"]` and `{\"0\": \"a\"}` differ.",
        ],
        brute_force="`JSON.stringify(a) === JSON.stringify(b)` is tempting, but the text depends on key order, so `{a:1,b:2}` and `{b:2,a:1}` would be reported as different.",
        approach="1. `a === b` → true. 2. If either is not a non-null object → false. 3. Array-ness must match. 4. Key counts must match. 5. Every key of `a` must be an own key of `b` with a deep-equal value.\n\n**Dry run** `{a:1}` vs `{a:1,b:null}`: not identical, both objects, both non-arrays, key counts 1 vs 2 → false. Without the count check the loop over `a`'s keys would wrongly succeed.",
        complexity="O(n) time in the total number of nodes; recursion depth equals nesting depth.",
        pitfalls="- Forgetting the key-count check (extra keys in `b` go unnoticed).\n- Reading `b[k]` without checking that the key exists: outside JSON a property can hold `undefined`, and then `{a: undefined}` and `{b: 1}` have equal key counts while `b.a` is also `undefined`. `Object.hasOwn` closes that hole.\n- Arrays and objects with the same keys.",
        follow_up="Real-world versions also handle `Date`, `Map`, `Set`, `NaN` and cyclic references (keep a set of visited pairs).",
    ),
),
dict(
    id="js-deep-clone", title="Deep clone of JSON data", difficulty="Medium", pattern="Objects & recursion",
    kind="js", entry="cloneCheck",
    description=r"""
Write `deepClone(value)` that returns a completely independent copy of a JSON value: nested arrays and
objects must be new arrays and objects all the way down, so changing the original afterwards never
affects the copy. Arrays must stay arrays. Do it with recursion (not `JSON.parse(JSON.stringify(...))`
or `structuredClone`).

The driver clones `value`, then **overwrites the original** at `path` with `replacement`, and returns
`{ copy, sameReference }`. A correct clone still shows the old data.

**Example:** `cloneCheck({a: {b: [1, 2]}}, ["a", "b", 0], 99)` → `{copy: {a: {b: [1, 2]}}, sameReference: false}`
""",
    starter="function deepClone(value) {\n  // your code\n}\n" + CLONE_DRIVER,
    solution="function deepClone(value) {\n  if (value === null || typeof value !== \"object\") return value;\n  if (Array.isArray(value)) return value.map(deepClone);\n  const out = {};\n  for (const key of Object.keys(value)) out[key] = deepClone(value[key]);\n  return out;\n}\n" + CLONE_DRIVER,
    tests=[
        [{"a": {"b": [1, 2]}}, ["a", "b", 0], 99],
        [[1, 2, 3], [1], "changed"],
        [5, [], None],
        [None, [], None],
        ["text", [], None],
        [{"a": 1}, ["a"], 2],
        [[[1, 2], [3, 4]], [1, 0], -1],
        [{"users": [{"name": "Ada", "tags": ["x"]}, {"name": "Lin", "tags": []}]}, ["users", 0, "tags", 0], "y"],
        [{"a": None, "b": False, "c": 0, "d": ""}, ["c"], 1],
        [[], [0], "pushed"],
        [{}, ["k"], "v"],
        [{"deep": {"er": {"est": {"list": [{"z": 1}]}}}}, ["deep", "er", "est", "list", 0, "z"], 2],
        [[{"a": [{"b": [{"c": 1}]}]}], [0, "a", 0, "b", 0], "gone"],
    ],
    wrong_solutions=[
        "function deepClone(value) { return value; }\n" + CLONE_DRIVER,
        "function deepClone(value) {\n  if (value === null || typeof value !== 'object') return value;\n  return Array.isArray(value) ? [...value] : { ...value };\n}\n" + CLONE_DRIVER,
        "function deepClone(value) {\n  if (value === null || typeof value !== 'object') return value;\n  const out = {};\n  for (const key of Object.keys(value)) out[key] = deepClone(value[key]);\n  return out;\n}\n" + CLONE_DRIVER,
    ],
    guide=G(
        prereqs="Reference semantics of objects, spread syntax and why it is shallow (lessons *Objects, arrays and mutability*, *Destructuring, spread, rest and JSON*).",
        intuition="Copying a container copies the *references* inside it. To be independent you have to copy every container you meet, which is a recursion over the structure.",
        hints=[
            "Primitives (and `null`) are immutable; return them as they are.",
            "For an array, build a new array whose elements are clones of the old elements.",
            "For an object, create `{}` and assign a clone of each own property.",
        ],
        brute_force="`{...value}` or `[...value]` copies one level. The driver mutates a nested location, so a shallow copy shows the damage.",
        approach="```\nclone(v): primitive → v\n          array     → v.map(clone)\n          object    → { k: clone(v[k]) for each key }\n```\n**Dry run** `{a:{b:[1,2]}}`: new outer object; key `a` → new inner object; key `b` → new array `[1,2]`. Driver sets `original.a.b[0] = 99`; the copy's array is a different one, so it still holds `[1,2]`.",
        complexity="O(n) time and space for n nodes; depth of recursion equals nesting depth.",
        pitfalls="- Treating arrays like objects produces `{\"0\": 1, \"1\": 2}`.\n- `typeof null === \"object\"`; guard it or `Object.keys(null)` throws.\n- The JSON round trip silently drops `undefined` and functions and breaks dates, so it is not a general clone.",
        follow_up="Support cycles with a `Map` from original to copy, and compare with the built-in `structuredClone`.",
    ),
),
dict(
    id="js-pick-omit", title="pick and omit", difficulty="Easy", pattern="Object utilities",
    kind="js", entry="pickOmit",
    description=r"""
Write `pickOmit(obj, keys, mode)`:

- `mode === "pick"`: return a new object holding only the listed keys that actually exist in `obj`
- `mode === "omit"`: return a new object holding every key of `obj` except the listed ones

Values of any kind (including `0`, `false`, `""` and `null`) must be kept. `obj` must not be modified.

**Examples:** `pickOmit({a:1,b:2,c:3}, ["a","c"], "pick")` → `{a:1,c:3}` · `pickOmit({a:1,b:2,c:3}, ["a"], "omit")` → `{b:2,c:3}`
""",
    starter="function pickOmit(obj, keys, mode) {\n  // your code\n}\n",
    solution="function pickOmit(obj, keys, mode) {\n  const out = {};\n  if (mode === \"pick\") {\n    for (const k of keys) if (Object.hasOwn(obj, k)) out[k] = obj[k];\n  } else {\n    const drop = new Set(keys);\n    for (const k of Object.keys(obj)) if (!drop.has(k)) out[k] = obj[k];\n  }\n  return out;\n}\n",
    tests=[
        [{"a": 1, "b": 2, "c": 3}, ["a", "c"], "pick"], [{"a": 1, "b": 2, "c": 3}, ["a"], "omit"],
        [{"a": 0, "b": False, "c": "", "d": None}, ["a", "b", "c", "d"], "pick"],
        [{"a": 0, "b": False, "c": "", "d": None}, ["z"], "omit"],
        [{"a": 1}, ["x", "y"], "pick"], [{"a": 1}, [], "pick"], [{"a": 1}, [], "omit"], [{}, ["a"], "pick"],
        [{}, ["a"], "omit"], [{"a": 1, "b": 2}, ["a", "b"], "omit"], [{"a": {"n": 1}, "b": [1, 2]}, ["a"], "pick"],
        [{"a": 1, "b": 2, "c": 3, "d": 4}, ["b", "b", "d"], "omit"], [{"length": 3, "name": "n"}, ["length"], "pick"],
    ],
    wrong_solutions=[
        "function pickOmit(obj, keys, mode) {\n  const out = {};\n  if (mode === 'pick') { for (const k of keys) if (obj[k]) out[k] = obj[k]; }\n  else { for (const k of Object.keys(obj)) if (!keys.includes(k)) out[k] = obj[k]; }\n  return out;\n}\n",
        "function pickOmit(obj, keys, mode) {\n  const out = {};\n  for (const k of keys) if (k in obj) out[k] = obj[k];\n  return out;\n}\n",
        "function pickOmit(obj, keys, mode) {\n  const out = {};\n  if (mode === 'pick') { for (const k of keys) out[k] = k in obj ? obj[k] : null; }\n  else { for (const k of Object.keys(obj)) if (!keys.includes(k)) out[k] = obj[k]; }\n  return out;\n}\n",
    ],
    guide=G(
        prereqs="Property access with brackets, `Object.keys`, `Object.hasOwn`, `Set` (lesson *Objects, arrays and mutability*).",
        intuition="Both operations build a fresh object by copying selected properties. Pick iterates over the wanted keys; omit iterates over the existing keys and skips the unwanted ones.",
        hints=[
            "Start from an empty object and copy; never `delete` from the input.",
            "Check existence with `Object.hasOwn(obj, k)` rather than by looking at the value.",
            "For omit, put the keys in a `Set` so each membership test is O(1).",
        ],
        brute_force="For omit, calling `keys.includes(k)` for every property is O(n·m). Fine for small inputs; the `Set` makes it O(n + m).",
        approach="Pick: for each `k` in `keys`, if `obj` has it, copy. Omit: for each key of `obj` not in the drop set, copy.\n\n**Dry run** pick `[\"a\",\"c\"]` from `{a:1,b:2,c:3}` → copy `a`, copy `c` → `{a:1,c:3}`.",
        complexity="O(n + m) time for n properties and m keys; O(n) extra space.",
        pitfalls="- `if (obj[k])` loses falsy values such as `0` and `\"\"`.\n- Adding missing keys with a placeholder value changes the shape of the result.\n- Mutating the argument surprises the caller.",
    ),
),
dict(
    id="js-deep-merge", title="Deep merge", difficulty="Medium", pattern="Object utilities",
    kind="js", entry="deepMerge",
    description=r"""
Write `deepMerge(base, patch)` that returns a **new** value combining two JSON values:

- if both are plain objects (not arrays, not `null`), the result has all keys of both; keys present in
  both are merged recursively
- in every other case `patch` wins and replaces `base` entirely (arrays are replaced, not concatenated;
  `null` replaces whatever was there)

Neither argument may be modified.

**Example:** `deepMerge({ui: {theme: "dark", size: 12}, tags: [1]}, {ui: {size: 14}, tags: [2]})` → `{ui: {theme: "dark", size: 14}, tags: [2]}`
""",
    starter="function deepMerge(base, patch) {\n  // your code\n}\n",
    solution="function deepMerge(base, patch) {\n  const plain = (v) => v !== null && typeof v === \"object\" && !Array.isArray(v);\n  if (!plain(base) || !plain(patch)) return patch;\n  const out = { ...base };\n  for (const key of Object.keys(patch)) {\n    out[key] = Object.hasOwn(base, key) ? deepMerge(base[key], patch[key]) : patch[key];\n  }\n  return out;\n}\n",
    tests=[
        [{"ui": {"theme": "dark", "size": 12}, "tags": [1]}, {"ui": {"size": 14}, "tags": [2]}],
        [{"a": 1}, {"b": 2}], [{"a": 1}, {"a": 2}], [{}, {}], [{"a": {"b": 1}}, {"a": None}], [{"a": None}, {"a": {"b": 1}}],
        [{"a": [1, 2, 3]}, {"a": [9]}], [{"a": {"b": {"c": 1, "d": 2}}}, {"a": {"b": {"c": 3}, "e": 4}}],
        [{"a": {"x": 1}}, {"a": [1]}], [{"a": [1]}, {"a": {"x": 1}}], [1, 2], [{"a": 1}, 5], [[1, 2], {"k": 1}],
        [{"a": {"0": "zero"}}, {"a": ["arr"]}], [{"p": {"q": {"r": {"s": 1}}}, "keep": True}, {"p": {"q": {"r": {"t": 2}}}}],
    ],
    wrong_solutions=[
        "function deepMerge(base, patch) { return { ...base, ...patch }; }\n",
        "function deepMerge(base, patch) {\n  if (base === null || patch === null || typeof base !== 'object' || typeof patch !== 'object') return patch;\n  const out = Array.isArray(base) ? [...base] : { ...base };\n  for (const key of Object.keys(patch)) out[key] = key in base ? deepMerge(base[key], patch[key]) : patch[key];\n  return out;\n}\n",
        "function deepMerge(base, patch) {\n  const plain = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);\n  if (!plain(base) || !plain(patch)) return base;\n  const out = { ...base };\n  for (const key of Object.keys(patch)) out[key] = key in base ? deepMerge(base[key], patch[key]) : patch[key];\n  return out;\n}\n",
    ],
    guide=G(
        prereqs="Spread syntax, recursion over objects, telling arrays, `null` and plain objects apart.",
        intuition="Merging only *means* something for two plain objects. Decide that first; everything else is replacement. The recursion then follows the keys of the patch.",
        hints=[
            "Write a helper `plain(v)` that is true only for non-null, non-array objects.",
            "If either side is not plain, the answer is simply `patch`.",
            "Start from a shallow copy of `base`, then for each key of `patch` either recurse (key exists in base) or copy.",
        ],
        brute_force="`{...base, ...patch}` merges only the top level: the nested `ui` object would lose its `theme`.",
        approach="**Dry run** on the example: both plain → `out = {ui, tags}`. Key `ui`: both plain → recurse → `{theme:\"dark\", size:14}`. Key `tags`: arrays are not plain → patch wins → `[2]`.",
        complexity="O(n) in the total size of both inputs; depth of recursion equals depth of the patch.",
        pitfalls="- Merging arrays index by index (`[1,2,3]` + `[9]` → `[9,2,3]`) is rarely wanted and is wrong here.\n- `typeof null === \"object\"`.\n- Returning `base` instead of `patch` in the non-object case.\n- Mutating `base` instead of copying it.",
        follow_up="Guard against prototype pollution: skip the keys `__proto__`, `constructor` and `prototype` when the patch comes from untrusted JSON.",
    ),
),
dict(
    id="js-get-path", title="Get by path", difficulty="Medium", pattern="Object utilities",
    kind="js", entry="getPath",
    description=r"""
Write `getPath(obj, path, fallback)` that reads a nested value described by a string such as
`"user.address.city"` or `"orders[0].items[2].sku"`:

- segments are separated by dots; `[n]` selects an array index (and may be chained: `"m[1][0]"`)
- if at any point the next step cannot be taken (the current value is `null`, a primitive, or lacks the
  key), return `fallback`
- a value that exists but is `null`, `0`, `false` or `""` is returned as it is, not replaced by the fallback
- an empty path returns `obj` itself

**Examples:** `getPath({a: {b: [10, 20]}}, "a.b[1]", "none")` → `20` · `getPath({a: 0}, "a", 5)` → `0` · `getPath({a: 1}, "a.b.c", "none")` → `"none"`
""",
    starter="function getPath(obj, path, fallback) {\n  // your code\n}\n",
    solution=r'''function getPath(obj, path, fallback) {
  const keys = path.match(/[^.[\]]+/g) || [];
  let current = obj;
  for (const key of keys) {
    if (current === null || typeof current !== "object" || !Object.hasOwn(current, key)) return fallback;
    current = current[key];
  }
  return current;
}
''',
    tests=[
        [{"a": {"b": [10, 20]}}, "a.b[1]", "none"], [{"a": 0}, "a", 5], [{"a": 1}, "a.b.c", "none"],
        [{"a": None}, "a", "fb"], [{"a": None}, "a.b", "fb"], [{"a": False, "b": ""}, "b", "fb"],
        [{"m": [[1, 2], [3, 4]]}, "m[1][0]", -1], [{"m": [[1, 2], [3, 4]]}, "m[2][0]", -1],
        [{"orders": [{"items": [{"sku": "x1"}, {"sku": "x2"}]}]}, "orders[0].items[1].sku", None],
        [{"a": 1}, "", "fb"], [[5, 6, 7], "[2]", 0], [{"a": "text"}, "a.length", "fb"], [{"a": [1, 2]}, "a.length", "fb"],
        [{"x": {"y": {"z": {}}}}, "x.y.z", "fb"], [{"x": {"y": 1}}, "x.toString", "fb"],
    ],
    wrong_solutions=[
        "function getPath(obj, path, fallback) {\n  const keys = path.match(/[^.[\\]]+/g) || [];\n  let current = obj;\n  for (const key of keys) { current = current ? current[key] : undefined; }\n  return current || fallback;\n}\n",
        "function getPath(obj, path, fallback) {\n  let current = obj;\n  for (const key of path.split('.')) {\n    if (current === null || typeof current !== 'object' || !Object.hasOwn(current, key)) return fallback;\n    current = current[key];\n  }\n  return current;\n}\n",
        "function getPath(obj, path, fallback) {\n  const keys = path.match(/[^.[\\]]+/g) || [];\n  let current = obj;\n  for (const key of keys) {\n    if (current == null || current[key] == null) return fallback;\n    current = current[key];\n  }\n  return current;\n}\n",
    ],
    guide=G(
        prereqs="Bracket property access, optional chaining as the built-in cousin of this function, a simple regular expression or manual tokenising.",
        intuition="Turn the path into a list of keys, then walk: keep a `current` value, and before each step check that the step is possible.",
        hints=[
            "`\"a.b[1]\"` should become `[\"a\", \"b\", \"1\"]`. A regular expression that matches runs of characters other than `.`, `[` and `]` does it in one call.",
            "Array indexes can stay strings: `arr[\"1\"]` is the same as `arr[1]`.",
            "Decide to fall back based on whether the key *exists*, not on whether the value is truthy.",
        ],
        brute_force="Chaining `&&` by hand (`obj && obj.a && obj.a.b`) works for a fixed path only and treats `0` and `\"\"` as missing.",
        approach="1. `keys = path.match(/[^.[\\]]+/g) || []`. 2. For each key: if `current` is not a non-null object or does not own the key → fallback; else step. 3. Return `current`.\n\n**Dry run** `({a:{b:[10,20]}}, \"a.b[1]\")`: keys `a,b,1`; current → `{b:[10,20]}` → `[10,20]` → `20`.",
        complexity="O(k) for k path segments; O(k) space for the key list.",
        pitfalls="- `current || fallback` replaces legitimate `0`, `false`, `\"\"`.\n- Treating a stored `null` as missing: `getPath({a:null}, \"a\", \"fb\")` is `null`.\n- Inherited members such as `toString` or a string's `length` are not data; own-property checks on objects avoid them. (An array's `length` *is* an own property.)",
        follow_up="Write the companion `setPath(obj, path, value)` that creates intermediate objects or arrays as needed.",
    ),
),
]
