"""TypeScript track, Part II problems: overloads, tuples, key paths, generic containers, typed event bus."""


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


PROBLEMS = [
# ------------------------------------------------------------------ 8
dict(
    id="ts-overload-dispatch", title="Overload-style dispatch", difficulty="Medium",
    pattern="Functions & overloads", kind="js", entry="describeArgs",
    description=r"""
TypeScript overloads list several call signatures, but after compilation only **one** implementation exists, and it has
to work out at runtime which signature was used. Write that implementation.

`describeArgs(args)` receives the argument list as an array and must behave like a function with these overloads,
tried from top to bottom:

| # | arguments | result |
|---|---|---|
| 1 | `(n: number)` | `"num:"` + `n.toFixed(2)` |
| 2 | `(s: string)` | `"str:"` + `s` trimmed and upper-cased |
| 3 | `(a: number, b: number)` | `"range:"` + smaller + `".."` + larger |
| 4 | `(s: string, times: number)` where `times` is an integer ≥ 0 | `"repeat:"` + `s` repeated `times` times joined with `"-"` |
| 5 | `(list: unknown[])` (exactly one argument, an array) | `"list:"` + its length |

If no overload matches, return `"TypeError: no overload matches (" + tags + ")"` where `tags` is the comma-and-space
separated list of each argument's tag: `"null"`, `"array"`, or its `typeof` (`"string"`, `"number"`, `"boolean"`, `"object"`).
With zero arguments the tag list is empty: `"TypeError: no overload matches ()"`.

**Examples:** `describeArgs([3.14159])` → `"num:3.14"` · `describeArgs(["ab", 3])` → `"repeat:ab-ab-ab"` ·
`describeArgs([true, 1])` → `"TypeError: no overload matches (boolean, number)"`
""",
    starter='''/**
 * @param {unknown[]} args  the argument list of one call
 * @returns {string}
 */
function describeArgs(args) {
  // your code
}
''',
    solution='''function describeArgs(args) {
  const tag = (v) => (v === null ? "null" : Array.isArray(v) ? "array" : typeof v);
  const tags = args.map(tag);
  const [a, b] = args;
  if (tags.length === 1) {
    if (tags[0] === "number") return "num:" + a.toFixed(2);
    if (tags[0] === "string") return "str:" + a.trim().toUpperCase();
    if (tags[0] === "array") return "list:" + a.length;
  }
  if (tags.length === 2) {
    if (tags[0] === "number" && tags[1] === "number") return "range:" + Math.min(a, b) + ".." + Math.max(a, b);
    if (tags[0] === "string" && tags[1] === "number" && Number.isInteger(b) && b >= 0) {
      return "repeat:" + Array(b).fill(a).join("-");
    }
  }
  return "TypeError: no overload matches (" + tags.join(", ") + ")";
}
''',
    tests=[
        [[3.14159]],
        [["ab", 3]],
        [[True, 1]],
        [["  deck log "]],
        [[9, 2]],
        [[2, 9]],
        [[["a", "b", "c"]]],
        [[]],
        [["x", 0]],
        [["x", 2.5]],
        [["x", -1]],
        [[None]],
        [[1, 2, 3]],
        [[{"a": 1}]],
        [[[], []]],
        [[5, "five"]],
        [[0]],
    ],
    wrong_solutions=[
        '''function describeArgs(args) {
  const [a, b] = args;
  if (args.length === 1) {
    if (typeof a === "number") return "num:" + a.toFixed(2);
    if (typeof a === "string") return "str:" + a.trim().toUpperCase();
    if (typeof a === "object") return "list:" + a.length;
  }
  if (args.length === 2) {
    if (typeof a === "number" && typeof b === "number") return "range:" + Math.min(a, b) + ".." + Math.max(a, b);
    if (typeof a === "string" && typeof b === "number") return "repeat:" + Array(b).fill(a).join("-");
  }
  return "TypeError: no overload matches (" + args.map((v) => typeof v).join(", ") + ")";
}
''',
        '''function describeArgs(args) {
  const tag = (v) => (v === null ? "null" : Array.isArray(v) ? "array" : typeof v);
  const tags = args.map(tag);
  const [a, b] = args;
  if (tags[0] === "number" && tags[1] === "number") return "range:" + a + ".." + b;
  if (tags[0] === "string" && tags[1] === "number" && Number.isInteger(b) && b >= 0) return "repeat:" + Array(b).fill(a).join("-");
  if (tags[0] === "number") return "num:" + a.toFixed(2);
  if (tags[0] === "string") return "str:" + a.trim().toUpperCase();
  if (tags[0] === "array") return "list:" + a.length;
  return "TypeError: no overload matches (" + tags.join(", ") + ")";
}
''',
    ],
    guide=G(
        prereqs="Overload signatures and why only the implementation survives compilation (*Functions, arrays and tuples*).",
        intuition="Each overload is a pattern over the *count* and *runtime types* of the arguments. Compute a tag for every "
                  "argument once, then compare the tag list against each pattern in order.",
        hints=["Write `tag(v)` returning `null`, `array` or `typeof v`.",
               "Branch on `args.length` first; it halves the cases.",
               "Overload 4 has a value condition as well as a type condition: `Number.isInteger(times) && times >= 0`."],
        brute_force="A long chain of `typeof` tests on `args[0]` and `args[1]` without checking the length. It mis-handles extra "
                    "arguments and treats `null` and plain objects as arrays.",
        approach="Tags, then a decision table.\n\n"
                 "**Dry run** on `[\"x\", 2.5]`: tags `[string, number]`, length 2. Overload 3 needs two numbers: no. Overload 4 needs "
                 "string + non-negative integer: `2.5` is not an integer: no. Nothing else has two parameters → "
                 "`\"TypeError: no overload matches (string, number)\"`.",
        complexity="Time O(k) for k arguments (plus the length of the repeated string), space O(k).",
        pitfalls="`typeof null` and `typeof []` are `\"object\"`. `Array(2.5)` throws a RangeError, so validate before building. "
                 "Ignoring the argument count lets `(1, 2, 3)` match the range overload.",
        follow_up="Write the five overload signatures in TypeScript and check that the two-argument call `(\"x\", 2.5)` compiles "
                  "even though it fails at runtime: types cannot express \"integer\".",
    ),
),
# ------------------------------------------------------------------ 9
dict(
    id="ts-tuple-zip", title="Zip lists into tuples", difficulty="Easy",
    pattern="Arrays & tuples", kind="js", entry="zip",
    description=r"""
`zip` pairs up the elements of several lists by position. In TypeScript its result is an array of **tuples**:
`zip([1, 2], ["a", "b"])` has type `[number, string][]`.

Write `zip(lists)` where `lists` is an array of arrays. Return an array whose `i`-th entry is the tuple
`[lists[0][i], lists[1][i], ...]`. Stop at the length of the **shortest** list. With no lists at all, return `[]`.

**Examples:** `zip([[1, 2, 3], ["a", "b", "c"]])` → `[[1, "a"], [2, "b"], [3, "c"]]` ·
`zip([[1, 2, 3], ["a"]])` → `[[1, "a"]]`
""",
    starter='''/**
 * @param {unknown[][]} lists
 * @returns {unknown[][]}  in TypeScript: an array of tuples
 */
function zip(lists) {
  // your code
}
''',
    solution='''function zip(lists) {
  if (lists.length === 0) return [];
  const length = Math.min(...lists.map((list) => list.length));
  const out = [];
  for (let i = 0; i < length; i++) out.push(lists.map((list) => list[i]));
  return out;
}
''',
    tests=[
        [[[1, 2, 3], ["a", "b", "c"]]],
        [[[1, 2, 3], ["a"]]],
        [[]],
        [[[1, 2, 3]]],
        [[[], [1, 2]]],
        [[[1, 2], ["a", "b"], [True, False]]],
        [[[None, 0], ["", False]]],
        [[["x"], ["y"], ["z"], ["w"]]],
        [[[[1], [2]], [{"k": 1}, {"k": 2}]]],
        [[[1, 2, 3, 4], [1, 2], [1, 2, 3]]],
    ],
    wrong_solutions=[
        '''function zip(lists) {
  if (lists.length === 0) return [];
  return lists[0].map((_, i) => lists.map((list) => list[i]));
}
''',
        '''function zip(lists) {
  if (lists.length === 0) return [];
  const length = Math.max(...lists.map((l) => l.length));
  const out = [];
  for (let i = 0; i < length; i++) out.push(lists.map((l) => l[i]));
  return out;
}
''',
    ],
    guide=G(
        prereqs="Tuples versus arrays (*Functions, arrays and tuples*).",
        intuition="The result has one row per position, and a position only exists if every list has it, hence the shortest "
                  "length. Each row collects the element at that position from every list.",
        hints=["Find the minimum length first.", "Row `i` is `lists.map((list) => list[i])`.",
               "`Math.min()` with no arguments is `Infinity`, so handle the empty input separately."],
        brute_force="Loop while every list still has an element at index `i`, checking all lists on every step: the same O(n × k) "
                    "work, with the stopping test repeated.",
        approach="Compute `length`, loop `i` from 0 to `length - 1`, push a row.\n\n"
                 "**Dry run** on `[[1, 2, 3], [\"a\"]]`: lengths 3 and 1 → `length` 1. `i = 0`: row `[1, \"a\"]`. Done: `[[1, \"a\"]]`.",
        complexity="Time and space O(n × k) for k lists of shortest length n.",
        pitfalls="Mapping over the first list instead of the shortest pads rows with `undefined`. An empty outer list makes "
                 "`Math.min(...[])` return `Infinity` and the loop never ends.",
        follow_up="Type it in TypeScript for two lists: `function zip<A, B>(a: A[], b: B[]): [A, B][]`. The variadic version uses "
                  "a mapped tuple type: `{ [K in keyof T]: T[K][] }`.",
    ),
),
# ------------------------------------------------------------------ 10
dict(
    id="ts-head-tail", title="Head, tail, init and last", difficulty="Easy",
    pattern="Arrays & tuples", kind="js", entry="splitList",
    description=r"""
Type-level code often takes tuples apart with `infer`: `T extends [infer Head, ...infer Tail]`. Do the same to a real list.

Write `splitList(list)` returning an object with four keys:

- `head`: the first element, or `null` if the list is empty;
- `tail`: every element except the first (a new array);
- `init`: every element except the last (a new array);
- `last`: the last element, or `null` if the list is empty.

For a one-element list, `head` and `last` are that element and `tail` and `init` are both `[]`.

**Example:** `splitList([1, 2, 3])` → `{"head": 1, "tail": [2, 3], "init": [1, 2], "last": 3}`
""",
    starter='''/**
 * @template T
 * @param {T[]} list
 * @returns {{ head: T | null, tail: T[], init: T[], last: T | null }}
 */
function splitList(list) {
  // your code
}
''',
    solution='''function splitList(list) {
  if (list.length === 0) return { head: null, tail: [], init: [], last: null };
  return {
    head: list[0],
    tail: list.slice(1),
    init: list.slice(0, list.length - 1),
    last: list[list.length - 1],
  };
}
''',
    tests=[
        [[1, 2, 3]],
        [[]],
        [["only"]],
        [[0, False]],
        [[None, 1, None]],
        [[[1, 2], [3]]],
        [["a", "b"]],
        [[False]],
        [[1, 2, 3, 4, 5, 6]],
        [[{"k": 1}, "x", 3]],
    ],
    wrong_solutions=[
        '''function splitList(list) {
  return { head: list[0] || null, tail: list.slice(1), init: list.slice(0, -1), last: list[list.length - 1] || null };
}
''',
        '''function splitList(list) {
  if (list.length === 0) return { head: null, tail: [], init: [], last: null };
  return { head: list[0], tail: list.slice(1), init: list.slice(0, list.length - 2), last: list[list.length - 1] };
}
''',
    ],
    guide=G(
        prereqs="Array indexing and `slice`; `T | undefined` for possibly missing elements (*Functions, arrays and tuples*).",
        intuition="Four views of the same list. The only decision is what to do when there is nothing to view.",
        hints=["Handle the empty list first.", "`slice(1)` drops the first element; `slice(0, n - 1)` drops the last.",
               "Do not use `||` to supply `null`: the first element may legitimately be `0` or `false`."],
        brute_force="Build `tail` and `init` with loops that push elements one at a time. Same complexity, more code.",
        approach="One early return, then four expressions.\n\n"
                 "**Dry run** on `[0, false]`: not empty. `head` = `0`, `tail` = `[false]`, `init` = `[0]`, `last` = `false`. "
                 "A version using `list[0] || null` would report `head: null`, which is wrong.",
        complexity="Time and space O(n) for the two copies.",
        pitfalls="Falsy elements and `||`. Off-by-one in the `init` slice. Returning the same array object for `tail` when the "
                 "caller expects a copy.",
        follow_up="Write the type-level `Head<T>` and `Tail<T>` from the lesson *Interview essentials II* and compare.",
    ),
),
# ------------------------------------------------------------------ 11
dict(
    id="ts-get-path", title="Get by key path with a default", difficulty="Medium",
    pattern="keyof & indexed access", kind="js", entry="getPath",
    description=r"""
`obj?.a?.b?.[0] ?? fallback` reads a nested value safely when the path is known while writing the code. Write the
version for a path that arrives as a string.

`getPath(source, path, fallback)`:

- `path` uses dots and brackets: `"crew[0].name"`, `"a.b.c"`, `"[1][0]"`, `"grid[2][3]"`. Split it into keys; a key is
  any run of characters other than `.`, `[` and `]`. The empty path `""` has no keys.
- Start at `source` and follow the keys one at a time. A step is only possible when the current value is an object or
  an array **and** has the key as its **own** property (so `"toString"` or `"constructor"` is never found).
- If any step is impossible, return `fallback`.
- If every step succeeds, return the value found. A found `null` is returned as `null` (it exists); only "not found"
  produces the fallback.
- With the empty path, return `source` itself.

**Examples:** `getPath({"crew": [{"name": "Asha"}]}, "crew[0].name", "?")` → `"Asha"` ·
`getPath({"a": {"b": null}}, "a.b", "?")` → `null` · `getPath({"a": 1}, "a.b.c", "?")` → `"?"`
""",
    starter='''/**
 * @param {unknown} source
 * @param {string} path
 * @param {unknown} fallback
 * @returns {unknown}
 */
function getPath(source, path, fallback) {
  // your code
}
''',
    solution='''function getPath(source, path, fallback) {
  const keys = path.match(/[^.[\\]]+/g) ?? [];
  let current = source;
  for (const key of keys) {
    if (typeof current !== "object" || current === null) return fallback;
    if (!Object.prototype.hasOwnProperty.call(current, key)) return fallback;
    current = current[key];
  }
  return current;
}
''',
    tests=[
        [{"crew": [{"name": "Asha"}]}, "crew[0].name", "?"],
        [{"a": {"b": None}}, "a.b", "?"],
        [{"a": 1}, "a.b.c", "?"],
        [{"a": {"b": 0}}, "a.b", 99],
        [{"a": {"b": False}}, "a.b", True],
        [{"a": ""}, "a", "fallback"],
        [[[1, 2], [3, 4]], "[1][0]", -1],
        [{"grid": [[1, 2, 3], [4, 5, 6]]}, "grid[1][2]", 0],
        [{"a": 1}, "", "?"],
        [{"a": {"b": None}}, "a.b.c", "?"],
        [{"a": {}}, "a.toString", "none"],
        [{"list": [1, 2]}, "list.length", 0],
        [{"list": [1, 2]}, "list[5]", "out of range"],
        [None, "a", "nothing"],
        ["text", "length", 0],
        [{"a": {"b": {"c": {"d": "deep"}}}}, "a.b.c.d", None],
        [{"x": 1}, "y", None],
    ],
    wrong_solutions=[
        '''function getPath(source, path, fallback) {
  const keys = path.match(/[^.[\\]]+/g) ?? [];
  let current = source;
  for (const key of keys) {
    current = current?.[key];
  }
  return current || fallback;
}
''',
        '''function getPath(source, path, fallback) {
  const keys = path.match(/[^.[\\]]+/g) ?? [];
  let current = source;
  for (const key of keys) {
    if (current == null) return fallback;
    current = current[key];
  }
  return current ?? fallback;
}
''',
        '''function getPath(source, path, fallback) {
  let current = source;
  for (const key of path.split(".")) {
    if (typeof current !== "object" || current === null || !Object.prototype.hasOwnProperty.call(current, key)) return fallback;
    current = current[key];
  }
  return current;
}
''',
    ],
    guide=G(
        prereqs="Optional chaining and `??` (*Unions, literals and narrowing*); `keyof` and indexed access (*Type modifiers*).",
        intuition="Turn the path into a list of keys, then walk. At each step there are two questions: *can I look inside the "
                  "current value at all?* and *does it really have this key?* A \"no\" to either ends the walk with the fallback.",
        hints=["A regular expression matching runs of characters that are not `.`, `[` or `]` extracts the keys.",
               "Use `Object.prototype.hasOwnProperty.call(current, key)` (or `Object.hasOwn`) so inherited members are not found.",
               "Return `current` as is at the end: do not apply `||` or `??`, because a found `0`, `false`, `\"\"` or `null` is a "
               "real answer."],
        brute_force="`path.split(\".\")` handles dotted paths only, and `current?.[key]` with a final `|| fallback` loses falsy "
                    "values and finds inherited members. Each shortcut fails some of the tests.",
        approach="Parse, loop, check, step.\n\n"
                 "**Dry run**: `getPath({crew: [{name: \"Asha\"}]}, \"crew[0].name\", \"?\")`. Keys: `crew`, `0`, `name`. "
                 "`crew` is an own key of the object → the array. `0` is an own key of the array → `{name: \"Asha\"}`. "
                 "`name` is an own key → `\"Asha\"`. Returned.\n\n"
                 "**Second**: `getPath({a: {b: null}}, \"a.b.c\", \"?\")`: after `a`, `b` the current value is `null`; the next step "
                 "cannot look inside `null` → `\"?\"`.",
        complexity="Time O(length of path), space O(number of keys).",
        pitfalls="`typeof null === \"object\"`. Strings have a `length` but are primitives, so the rule here says no step into "
                 "them. Arrays do own `length`. Applying the fallback to found falsy values.",
        follow_up="In TypeScript the path can be typed with template literal types so that only valid paths compile; libraries "
                  "such as react-hook-form do this.",
    ),
),
# ------------------------------------------------------------------ 12
dict(
    id="ts-result-chain", title="Result container with map and flatMap", difficulty="Medium",
    pattern="Generics", kind="js", entry="runResult",
    description=r"""
A `Result<T, E>` is the generic discriminated union `{ ok: true, value: T } | { ok: false, error: E }`. Implement its
core operations and run a pipeline through them.

Write `runResult(start, ops)`. Begin with `{ ok: true, value: start }` (`start` is a number) and apply each operation
in order. An operation is an array `[name, argument]`:

| operation | effect |
|---|---|
| `["map", fn]` | on success, replace the value with `fn(value)`; on failure, do nothing |
| `["flatMap", fn]` | on success, replace the whole result with `fn(value)`, which is itself a Result; on failure, do nothing |
| `["mapErr", fn]` | on failure, replace the error with `fn(error)`; on success, do nothing |
| `["orElse", n]` | on failure, become `{ ok: true, value: n }`; on success, do nothing |

`fn` is the **name** of a function from these tables.

`map` functions: `"inc"` (x + 1), `"double"` (x × 2), `"square"` (x × x), `"negate"` (−x), `"half"` (x ÷ 2).

`flatMap` functions (each returns a Result):
`"sqrt"`: error `"negative input"` when x < 0, otherwise success with `Math.sqrt(x)`;
`"reciprocal"`: error `"division by zero"` when x is 0, otherwise success with `1 / x`;
`"even"`: error `"not even"` unless x is an even integer, otherwise success with x unchanged.

`mapErr` functions: `"upper"` (the message in upper case), `"tag"` (`"E:"` + message).

Return the final Result object.

**Examples:** `runResult(3, [["map", "inc"], ["flatMap", "sqrt"]])` → `{"ok": true, "value": 2}` ·
`runResult(0, [["flatMap", "reciprocal"], ["map", "double"]])` → `{"ok": false, "error": "division by zero"}`
""",
    starter='''/**
 * @typedef {{ ok: true, value: number } | { ok: false, error: string }} Result
 * @param {number} start
 * @param {[string, string | number][]} ops
 * @returns {Result}
 */
function runResult(start, ops) {
  // your code
}
''',
    solution='''function runResult(start, ops) {
  const ok = (value) => ({ ok: true, value });
  const err = (error) => ({ ok: false, error });
  const mappers = {
    inc: (x) => x + 1,
    double: (x) => x * 2,
    square: (x) => x * x,
    negate: (x) => -x,
    half: (x) => x / 2,
  };
  const binders = {
    sqrt: (x) => (x < 0 ? err("negative input") : ok(Math.sqrt(x))),
    reciprocal: (x) => (x === 0 ? err("division by zero") : ok(1 / x)),
    even: (x) => (Number.isInteger(x) && x % 2 === 0 ? ok(x) : err("not even")),
  };
  const errorMappers = {
    upper: (e) => e.toUpperCase(),
    tag: (e) => "E:" + e,
  };
  let result = ok(start);
  for (const [name, arg] of ops) {
    if (name === "map") { if (result.ok) result = ok(mappers[arg](result.value)); }
    else if (name === "flatMap") { if (result.ok) result = binders[arg](result.value); }
    else if (name === "mapErr") { if (!result.ok) result = err(errorMappers[arg](result.error)); }
    else if (name === "orElse") { if (!result.ok) result = ok(arg); }
  }
  return result;
}
''',
    tests=[
        [3, [["map", "inc"], ["flatMap", "sqrt"]]],
        [0, [["flatMap", "reciprocal"], ["map", "double"]]],
        [5, []],
        [-4, [["flatMap", "sqrt"], ["mapErr", "upper"]]],
        [-4, [["flatMap", "sqrt"], ["mapErr", "tag"], ["mapErr", "upper"]]],
        [4, [["mapErr", "upper"], ["map", "half"]]],
        [7, [["flatMap", "even"], ["orElse", 0], ["map", "inc"]]],
        [8, [["flatMap", "even"], ["orElse", 0], ["map", "inc"]]],
        [2, [["map", "negate"], ["flatMap", "sqrt"], ["flatMap", "reciprocal"], ["map", "square"]]],
        [4, [["flatMap", "sqrt"], ["flatMap", "even"], ["flatMap", "reciprocal"]]],
        [9, [["flatMap", "sqrt"], ["flatMap", "even"], ["mapErr", "tag"], ["orElse", -1], ["flatMap", "sqrt"]]],
        [1, [["map", "half"], ["flatMap", "even"]]],
        [0, [["flatMap", "even"], ["flatMap", "reciprocal"], ["orElse", 10], ["orElse", 20], ["map", "double"]]],
        [6, [["orElse", 100], ["map", "square"]]],
    ],
    wrong_solutions=[
        # map applied even on failure / mapErr on success
        '''function runResult(start, ops) {
  const ok = (value) => ({ ok: true, value }), err = (error) => ({ ok: false, error });
  const mappers = { inc: (x) => x + 1, double: (x) => x * 2, square: (x) => x * x, negate: (x) => -x, half: (x) => x / 2 };
  const binders = { sqrt: (x) => (x < 0 ? err("negative input") : ok(Math.sqrt(x))),
    reciprocal: (x) => (x === 0 ? err("division by zero") : ok(1 / x)),
    even: (x) => (Number.isInteger(x) && x % 2 === 0 ? ok(x) : err("not even")) };
  const errorMappers = { upper: (e) => e.toUpperCase(), tag: (e) => "E:" + e };
  let result = ok(start);
  for (const [name, arg] of ops) {
    if (name === "map") result = ok(mappers[arg](result.value));
    else if (name === "flatMap") { if (result.ok) result = binders[arg](result.value); }
    else if (name === "mapErr") { if (!result.ok) result = err(errorMappers[arg](result.error)); }
    else if (name === "orElse") { if (!result.ok) result = ok(arg); }
  }
  return result;
}
''',
        # flatMap wraps the returned Result again (nested result)
        '''function runResult(start, ops) {
  const ok = (value) => ({ ok: true, value }), err = (error) => ({ ok: false, error });
  const mappers = { inc: (x) => x + 1, double: (x) => x * 2, square: (x) => x * x, negate: (x) => -x, half: (x) => x / 2 };
  const binders = { sqrt: (x) => (x < 0 ? err("negative input") : ok(Math.sqrt(x))),
    reciprocal: (x) => (x === 0 ? err("division by zero") : ok(1 / x)),
    even: (x) => (Number.isInteger(x) && x % 2 === 0 ? ok(x) : err("not even")) };
  const errorMappers = { upper: (e) => e.toUpperCase(), tag: (e) => "E:" + e };
  let result = ok(start);
  for (const [name, arg] of ops) {
    if (name === "map") { if (result.ok) result = ok(mappers[arg](result.value)); }
    else if (name === "flatMap") { if (result.ok) result = ok(binders[arg](result.value)); }
    else if (name === "mapErr") { if (!result.ok) result = err(errorMappers[arg](result.error)); }
    else if (name === "orElse") { if (!result.ok) result = ok(arg); }
  }
  return result;
}
''',
        # orElse always replaces
        '''function runResult(start, ops) {
  const ok = (value) => ({ ok: true, value }), err = (error) => ({ ok: false, error });
  const mappers = { inc: (x) => x + 1, double: (x) => x * 2, square: (x) => x * x, negate: (x) => -x, half: (x) => x / 2 };
  const binders = { sqrt: (x) => (x < 0 ? err("negative input") : ok(Math.sqrt(x))),
    reciprocal: (x) => (x === 0 ? err("division by zero") : ok(1 / x)),
    even: (x) => (Number.isInteger(x) && x % 2 === 0 ? ok(x) : err("not even")) };
  const errorMappers = { upper: (e) => e.toUpperCase(), tag: (e) => "E:" + e };
  let result = ok(start);
  for (const [name, arg] of ops) {
    if (name === "map") { if (result.ok) result = ok(mappers[arg](result.value)); }
    else if (name === "flatMap") { if (result.ok) result = binders[arg](result.value); }
    else if (name === "mapErr") { if (!result.ok) result = err(errorMappers[arg](result.error)); }
    else if (name === "orElse") result = ok(arg);
  }
  return result;
}
''',
    ],
    guide=G(
        prereqs="Generic discriminated unions and the `Result` type (*Generics*, *Interview essentials II*).",
        intuition="A Result travels along one of two tracks, success or failure. `map` and `flatMap` act only on the success "
                  "track; `mapErr` and `orElse` act only on the failure track. Once on the failure track, success operations are "
                  "skipped, so the first error is carried to the end unless `orElse` switches tracks.",
        hints=["Keep three lookup tables from name to function.",
               "`map` wraps the function's answer in a new success; `flatMap` uses the function's answer as the new result.",
               "Every operation starts with a test of `result.ok`."],
        brute_force="Use exceptions: compute with plain numbers and `throw` on errors, catching at `orElse`. It works, but it is "
                    "exactly the style the Result type replaces, and it makes `mapErr` awkward.",
        approach="Loop over the operations, updating one `result` variable.\n\n"
                 "**Dry run**: `runResult(7, [flatMap even, orElse 0, map inc])`. Start `ok(7)`. `even`: 7 is odd → "
                 "`err(\"not even\")`. `orElse 0`: on the failure track → `ok(0)`. `map inc` → `ok(1)`. "
                 "With start 8 the first step stays `ok(8)`, `orElse` is skipped, and the answer is `ok(9)`.",
        complexity="Time O(number of operations), space O(1).",
        pitfalls="Wrapping the output of a `flatMap` function in another success gives a Result inside a Result. Calling a `map` "
                 "function on a failure reads `result.value`, which is `undefined`, and produces `NaN`.",
        follow_up="Give it TypeScript signatures: `map<T, U, E>(r: Result<T, E>, f: (t: T) => U): Result<U, E>`. Then write "
                  "`Option<T>` (some or none) the same way.",
    ),
),
# ------------------------------------------------------------------ 13
dict(
    id="ts-event-bus", title="Event bus with typed channels", difficulty="Medium",
    pattern="Generics", kind="js", entry="runBus",
    description=r"""
In TypeScript an event bus is typed by a map from channel name to payload type:

```typescript
interface Bus<Events> {
  on<K extends keyof Events>(channel: K, listener: (payload: Events[K]) => void): void;
  emit<K extends keyof Events>(channel: K, payload: Events[K]): void;
}
```

The compiler then rejects unknown channels and wrong payloads. Build the runtime equivalent, which checks the same
two things while running.

Write `runBus(channels, ops)`. `channels` maps each channel name to its payload type, one of `"string"`, `"number"`,
`"boolean"`, `"object"` (a non-null, non-array object). `ops` is a list of operations; return the list of their results.

| operation | result |
|---|---|
| `["on", channel, id]` | subscribe listener `id`; result `"ok"`. Subscribing an id already on that channel changes nothing (still `"ok"`). |
| `["once", channel, id]` | like `on`, but the listener is removed after its first delivery |
| `["off", channel, id]` | unsubscribe; result `true` if it was subscribed, otherwise `false` |
| `["emit", channel, payload]` | deliver to every listener of the channel in subscription order; result is the list of strings `id + ":" + JSON.stringify(payload)` (an empty list if nobody listens) |

Errors: `on`, `once` and `emit` on a channel that is not in `channels` give `"error: unknown channel"`; `off` on an
unknown channel gives `false`. `emit` with a payload of the wrong type gives `"error: expected <type>"` and delivers
nothing (so `once` listeners stay subscribed).

**Example:** `runBus({"tick": "number"}, [["on","tick","a"], ["emit","tick",1], ["emit","tick","x"]])` →
`["ok", ["a:1"], "error: expected number"]`
""",
    starter='''/**
 * @param {Record<string, "string" | "number" | "boolean" | "object">} channels
 * @param {[string, string, unknown][]} ops
 * @returns {unknown[]}
 */
function runBus(channels, ops) {
  // your code
}
''',
    solution='''function runBus(channels, ops) {
  const listeners = {};
  for (const name of Object.keys(channels)) listeners[name] = [];
  const known = (name) => Object.prototype.hasOwnProperty.call(channels, name);
  const matches = (type, payload) =>
    type === "object"
      ? typeof payload === "object" && payload !== null && !Array.isArray(payload)
      : typeof payload === type;
  const results = [];
  for (const [op, channel, arg] of ops) {
    if (op === "on" || op === "once") {
      if (!known(channel)) { results.push("error: unknown channel"); continue; }
      if (!listeners[channel].some((l) => l.id === arg)) listeners[channel].push({ id: arg, once: op === "once" });
      results.push("ok");
    } else if (op === "off") {
      if (!known(channel)) { results.push(false); continue; }
      const index = listeners[channel].findIndex((l) => l.id === arg);
      if (index === -1) results.push(false);
      else { listeners[channel].splice(index, 1); results.push(true); }
    } else if (op === "emit") {
      if (!known(channel)) { results.push("error: unknown channel"); continue; }
      if (!matches(channels[channel], arg)) { results.push("error: expected " + channels[channel]); continue; }
      const current = listeners[channel].slice();
      results.push(current.map((l) => l.id + ":" + JSON.stringify(arg)));
      listeners[channel] = listeners[channel].filter((l) => !l.once);
    }
  }
  return results;
}
''',
    tests=[
        [{"tick": "number"}, [["on", "tick", "a"], ["emit", "tick", 1], ["emit", "tick", "x"]]],
        [{"tick": "number"}, [["emit", "tick", 5]]],
        [{"msg": "string"}, [["on", "msg", "a"], ["on", "msg", "b"], ["emit", "msg", "hi"], ["off", "msg", "a"], ["emit", "msg", "yo"]]],
        [{"msg": "string"}, [["once", "msg", "a"], ["on", "msg", "b"], ["emit", "msg", "1"], ["emit", "msg", "2"]]],
        [{"msg": "string"}, [["on", "nope", "a"], ["emit", "nope", "x"], ["off", "nope", "a"], ["once", "nope", "b"]]],
        [{"msg": "string"}, [["on", "msg", "a"], ["on", "msg", "a"], ["emit", "msg", "x"], ["off", "msg", "a"], ["off", "msg", "a"]]],
        [{"user": "object"}, [["on", "user", "log"], ["emit", "user", {"id": 1}], ["emit", "user", None], ["emit", "user", [1]]]],
        [{"flag": "boolean", "n": "number"}, [["on", "flag", "f"], ["on", "n", "g"], ["emit", "flag", False], ["emit", "n", 0], ["emit", "flag", 0]]],
        [{"msg": "string"}, [["once", "msg", "a"], ["emit", "msg", 7], ["emit", "msg", "ok"], ["emit", "msg", "again"]]],
        [{}, [["emit", "x", 1], ["off", "x", "a"]]],
        [{"a": "string", "b": "string"}, [["on", "a", "x"], ["on", "b", "y"], ["emit", "a", ""], ["emit", "b", "b!"], ["off", "a", "y"]]],
        [{"msg": "string"}, [["once", "msg", "a"], ["once", "msg", "b"], ["on", "msg", "c"], ["emit", "msg", "1"], ["off", "msg", "a"], ["emit", "msg", "2"]]],
        [{"toString": "string"}, [["emit", "constructor", "x"], ["on", "toString", "t"], ["emit", "toString", "fine"]]],
    ],
    wrong_solutions=[
        # no payload type check
        '''function runBus(channels, ops) {
  const listeners = {}; const results = [];
  for (const [op, channel, arg] of ops) {
    const known = Object.prototype.hasOwnProperty.call(channels, channel);
    if (op === "on" || op === "once") {
      if (!known) { results.push("error: unknown channel"); continue; }
      listeners[channel] ??= [];
      if (!listeners[channel].some((l) => l.id === arg)) listeners[channel].push({ id: arg, once: op === "once" });
      results.push("ok");
    } else if (op === "off") {
      const list = known ? listeners[channel] ?? [] : [];
      const i = list.findIndex((l) => l.id === arg);
      if (i === -1) results.push(false); else { list.splice(i, 1); results.push(true); }
    } else {
      if (!known) { results.push("error: unknown channel"); continue; }
      const list = listeners[channel] ?? [];
      results.push(list.map((l) => l.id + ":" + JSON.stringify(arg)));
      listeners[channel] = list.filter((l) => !l.once);
    }
  }
  return results;
}
''',
        # typeof check only: null and arrays pass as "object"; once never removed
        '''function runBus(channels, ops) {
  const listeners = {}; const results = [];
  for (const [op, channel, arg] of ops) {
    const known = Object.prototype.hasOwnProperty.call(channels, channel);
    if (op === "on" || op === "once") {
      if (!known) { results.push("error: unknown channel"); continue; }
      listeners[channel] ??= [];
      if (!listeners[channel].some((l) => l.id === arg)) listeners[channel].push({ id: arg });
      results.push("ok");
    } else if (op === "off") {
      const list = known ? listeners[channel] ?? [] : [];
      const i = list.findIndex((l) => l.id === arg);
      if (i === -1) results.push(false); else { list.splice(i, 1); results.push(true); }
    } else {
      if (!known) { results.push("error: unknown channel"); continue; }
      if (typeof arg !== channels[channel]) { results.push("error: expected " + channels[channel]); continue; }
      results.push((listeners[channel] ?? []).map((l) => l.id + ":" + JSON.stringify(arg)));
    }
  }
  return results;
}
''',
        # duplicate subscriptions allowed
        '''function runBus(channels, ops) {
  const listeners = {}; const results = [];
  const matches = (t, p) => (t === "object" ? typeof p === "object" && p !== null && !Array.isArray(p) : typeof p === t);
  for (const [op, channel, arg] of ops) {
    const known = Object.prototype.hasOwnProperty.call(channels, channel);
    if (op === "on" || op === "once") {
      if (!known) { results.push("error: unknown channel"); continue; }
      (listeners[channel] ??= []).push({ id: arg, once: op === "once" });
      results.push("ok");
    } else if (op === "off") {
      const list = known ? listeners[channel] ?? [] : [];
      const i = list.findIndex((l) => l.id === arg);
      if (i === -1) results.push(false); else { list.splice(i, 1); results.push(true); }
    } else {
      if (!known) { results.push("error: unknown channel"); continue; }
      if (!matches(channels[channel], arg)) { results.push("error: expected " + channels[channel]); continue; }
      const list = listeners[channel] ?? [];
      results.push(list.map((l) => l.id + ":" + JSON.stringify(arg)));
      listeners[channel] = list.filter((l) => !l.once);
    }
  }
  return results;
}
''',
    ],
    guide=G(
        prereqs="`keyof` constraints and indexed access types (*Generics*); runtime type checks (*Unions, literals and narrowing*).",
        intuition="The channel map plays the role of the `Events` type. Each operation first asks the two questions the compiler "
                  "would ask (does the channel exist? does the payload fit?), then does the bookkeeping on a list of listeners "
                  "per channel.",
        hints=["Store, per channel, an ordered array of `{ id, once }`.",
               "Check the channel with an own-property test so that names like `constructor` are not treated as known.",
               "On a successful emit, build the result from the current listeners and then drop the `once` ones."],
        brute_force="One flat array of `{ channel, id, once }` records filtered on every operation. It is O(total listeners) per "
                    "operation and still passes; a map from channel to list avoids scanning unrelated channels.",
        approach="Initialise an empty list per channel, then process the operations in order.\n\n"
                 "**Dry run**: channels `{msg: string}`, ops `once msg a`, `emit msg 7`, `emit msg \"ok\"`, `emit msg \"again\"`. "
                 "`once` → `\"ok\"`, listeners `[a(once)]`. `emit 7`: wrong type → `\"error: expected string\"`, nothing delivered, "
                 "`a` stays. `emit \"ok\"` → `[\"a:\\\"ok\\\"\"]`, then `a` is removed. `emit \"again\"` → `[]`.",
        complexity="Time O(listeners on the channel) per operation, space O(total listeners).",
        pitfalls="`typeof null` and `typeof []` are `\"object\"`. A failed emit must not consume `once` listeners. "
                 "`channels[name]` is truthy for inherited names such as `toString` on a plain object.",
        follow_up="Write the TypeScript class `Bus<Events extends Record<string, unknown>>` whose `emit` only compiles for a valid "
                  "channel and payload pair.",
    ),
),
]
