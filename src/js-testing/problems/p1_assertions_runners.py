"""JavaScript testing problems: assertions, tiny runners, a TDD kata, test design, prototype lookup."""


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


ASSERT_DRIVER = r'''
// --- driver (provided, do not change) ---
function show(value) {
  if (typeof value === "string") return JSON.stringify(value);   // strings keep their quotes
  if (Object.is(value, -0)) return "-0";
  return String(value);
}
function decode(token) {             // JSON cannot carry these three values, so the tests spell them out
  if (token === "@NaN") return NaN;
  if (token === "@-0") return -0;
  if (token === "@undefined") return undefined;
  return token;
}
function runAssertions(pairs) {
  return pairs.map(([expected, actual]) => {
    try { assertEquals(decode(expected), decode(actual)); return "ok"; }
    catch (thrown) { return thrown instanceof Error ? thrown.message : "threw something that is not an Error"; }
  });
}
'''

RUNNER_DRIVER = r'''
// --- driver (provided, do not change) ---
function runSuite(specs) {
  const ranInOrder = [];
  const tests = specs.map(([name, kind, text]) => ({
    name,
    fn() {
      ranInOrder.push(name);
      if (kind === "fail") throw new Error(text);
      if (kind === "throwString") throw text;            // a bare string: it has no .message
    },
  }));
  return { report: runTests(tests), ranInOrder };
}
'''

RUNNER_SOLUTION = r'''function runTests(tests) {
  const report = { total: tests.length, passed: 0, failed: 0, failures: [] };
  for (const { name, fn } of tests) {
    try {
      fn();
      report.passed++;
    } catch (thrown) {
      report.failed++;
      report.failures.push({ name, message: thrown instanceof Error ? thrown.message : String(thrown) });
    }
  }
  return report;
}
'''

HOOKS_DRIVER = r'''
// --- driver (provided, do not change) ---
function runWithHooks(ops) {
  const runner = createRunner();
  const log = [];
  for (const [kind, label, outcome] of ops) {
    if (kind === "beforeEach") runner.beforeEach(() => log.push("before " + label));
    else if (kind === "afterEach") runner.afterEach(() => log.push("after " + label));
    else runner.test(label, () => { log.push("test " + label); if (outcome === "fail") throw new Error("boom"); });
  }
  const counts = runner.run();
  return { log, passed: counts.passed, failed: counts.failed };
}
'''

HOOKS_SOLUTION = r'''function createRunner() {
  const before = [], after = [], tests = [];
  return {
    beforeEach(fn) { before.push(fn); },
    afterEach(fn) { after.push(fn); },
    test(name, fn) { tests.push({ name, fn }); },
    run() {
      let passed = 0, failed = 0;
      for (const { fn } of tests) {
        for (const hook of before) hook();
        try { fn(); passed++; }
        catch (error) { failed++; }
        finally { for (const hook of after) hook(); }
      }
      return { passed, failed };
    },
  };
}
'''

CALC_DRIVER = r'''
// --- driver (provided, do not change) ---
function calc(text) {
  try { return add(text); }
  catch (error) { return "error: " + error.message; }
}
'''

CALC_SOLUTION = r'''function add(text) {
  const NEWLINE = String.fromCharCode(10);
  let body = text, separators = [",", NEWLINE];
  if (text.startsWith("//")) {
    const end = text.indexOf(NEWLINE);
    separators = [text.slice(2, end)];
    body = text.slice(end + 1);
  }
  if (body.trim() === "") return 0;
  let pieces = [body];
  for (const separator of separators) pieces = pieces.flatMap((piece) => piece.split(separator));
  const numbers = pieces.map((piece) => {
    const trimmed = piece.trim();
    const value = Number(trimmed);
    if (trimmed === "" || Number.isNaN(value)) throw new Error("not a number: " + trimmed);
    return value;
  });
  const negatives = numbers.filter((n) => n < 0);
  if (negatives.length > 0) throw new Error("negatives not allowed: " + negatives.join(", "));
  return numbers.filter((n) => n <= 1000).reduce((sum, n) => sum + n, 0);
}
'''

PROTO_DRIVER = r'''
// --- driver (provided, do not change) ---
function lookup(layers, key) {
  // layers[0] becomes the object itself, layers[1] its prototype, and so on.
  // The last layer inherits from Object.prototype, as ordinary objects do.
  let object = Object.prototype;
  for (let i = layers.length - 1; i >= 0; i--) object = Object.assign(Object.create(object), layers[i]);
  return findOwner(object, key);
}
'''

DIFF_SOLUTION = r'''function firstDifference(expected, actual) {
  const isPlainObject = (v) => v !== null && typeof v === "object" && !Array.isArray(v);
  function walk(a, b, path) {
    if (Array.isArray(a) && Array.isArray(b)) {
      if (a.length !== b.length) return path === "" ? "length" : path + ".length";
      for (let i = 0; i < a.length; i++) {
        const found = walk(a[i], b[i], path + "[" + i + "]");
        if (found !== null) return found;
      }
      return null;
    }
    if (isPlainObject(a) && isPlainObject(b)) {
      const keys = [...new Set([...Object.keys(a), ...Object.keys(b)])].sort();
      for (const key of keys) {
        const next = path === "" ? key : path + "." + key;
        if (!Object.hasOwn(a, key) || !Object.hasOwn(b, key)) return next;
        const found = walk(a[key], b[key], next);
        if (found !== null) return found;
      }
      return null;
    }
    if (Object.is(a, b)) return null;
    return path === "" ? "(root)" : path;
  }
  return walk(expected, actual, "");
}
'''

PROBLEMS = [
dict(
    id="jstest-assert-equals", title="Write assertEquals", difficulty="Easy", pattern="Assertions",
    kind="js", entry="runAssertions",
    description=r"""
An **assertion** is a function that stays silent when a fact holds and throws when it does not. Write the
most basic one.

`assertEquals(expected, actual)` must

- return nothing when the two values are **the same value**
- otherwise throw an `Error` whose message is exactly `expected <E> but got <A>`, where `<E>` and `<A>` are
  produced by the provided helper `show(value)` (it keeps the quotes on strings)

"The same value" means what `Object.is` means: no type conversion, `NaN` equals `NaN`, and `0` is different
from `-0`. That is the rule `toBe` uses in Jest and Vitest.

The driver calls your function once per `[expected, actual]` pair and collects `"ok"` or the error message.
Because JSON cannot carry `NaN`, `-0` or `undefined`, the tests write them as `"@NaN"`, `"@-0"` and
`"@undefined"`; the driver converts them before calling you.

**Example:** `runAssertions([[1, 1], [1, "1"]])` → `["ok", "expected 1 but got \"1\""]`
""",
    starter="function assertEquals(expected, actual) {\n  // throw new Error(...) when the values differ\n}\n" + ASSERT_DRIVER,
    solution="function assertEquals(expected, actual) {\n  if (!Object.is(expected, actual)) {\n    throw new Error(\"expected \" + show(expected) + \" but got \" + show(actual));\n  }\n}\n" + ASSERT_DRIVER,
    tests=[
        [[[1, 1], [1, 2]]],
        [[["a", "a"], ["a", "b"]]],
        [[[1, "1"], ["", 0], [False, 0], [None, False]]],
        [[["@NaN", "@NaN"]]],
        [[[0, "@-0"], ["@-0", "@-0"], [0, 0]]],
        [[[None, "@undefined"], ["@undefined", "@undefined"], [None, None]]],
        [[[True, 1], [True, True]]],
        [[]],
        [[[0.3, 0.30000000000000004], [3.5, 3.5]]],
        [[["@NaN", 0], [1, "@NaN"]]],
        [[["10", 10], [10, 10], ["ten", "ten"], ["", ""]]],
        [[["@undefined", None], ["@-0", 0]]],
    ],
    examples=2,
    wrong_solutions=[
        "function assertEquals(expected, actual) {\n  if (expected != actual) throw new Error(\"expected \" + show(expected) + \" but got \" + show(actual));\n}\n" + ASSERT_DRIVER,
        "function assertEquals(expected, actual) {\n  if (expected !== actual) throw new Error(\"expected \" + show(expected) + \" but got \" + show(actual));\n}\n" + ASSERT_DRIVER,
        "function assertEquals(expected, actual) {\n  if (!Object.is(expected, actual)) throw new Error(\"expected \" + show(actual) + \" but got \" + show(expected));\n}\n" + ASSERT_DRIVER,
        "function assertEquals(expected, actual) {\n  return Object.is(expected, actual);\n}\n" + ASSERT_DRIVER,
    ],
    guide=G(
        prereqs="Throwing errors with `throw new Error(message)`; the lesson *Why automate tests: your first unit test*.",
        intuition="A test passes when nothing throws. So an assertion has one job: compare, and throw a helpful message when the comparison fails. The only real decision is which comparison to use.",
        hints=[
            "The function has no `return` statement at all. Silence means success.",
            "`==` converts types (`1 == \"1\"` is true). `===` does not, but it says `NaN !== NaN` and `0 === -0`.",
            "`Object.is(a, b)` is the comparison that treats `NaN` as equal to itself and tells `0` from `-0`.",
        ],
        brute_force="Comparing with `===` and then adding special cases for `NaN` (`a !== a && b !== b`) and for the two zeros (`1 / a === 1 / b`) works, and is exactly what `Object.is` does for you.",
        approach="One `if`: when `Object.is(expected, actual)` is false, build the message from `show(expected)` and `show(actual)` and throw.\n\n**Dry run** `assertEquals(1, \"1\")`: `Object.is(1, \"1\")` is false, `show(1)` is `1`, `show(\"1\")` is `\"1\"` with quotes, so the message is `expected 1 but got \"1\"`. The quotes are what make the mistake visible.",
        complexity="O(1) time and space.",
        pitfalls="- Returning `false` when the values differ: the runner only notices a throw.\n- Swapping the two values in the message; a reader then fixes the wrong side.\n- Building the message with plain concatenation, which prints `1` for both the number and the string.",
        follow_up="Add an optional third parameter, a message prefix. Then write `assertThrows(fn, expectedText)`.",
    ),
),
dict(
    id="jstest-first-difference", title="Deep equality that says where", difficulty="Medium", pattern="Assertions",
    kind="js", entry="firstDifference",
    description=r"""
`toEqual` compares the **contents** of two values. A good failure message also says *where* they differ.

Write `firstDifference(expected, actual)`. It returns `null` when the two values are deeply equal, and otherwise
the **path** to the first difference, as a string.

Rules:

- two **arrays** are compared by length first: if the lengths differ, the path is the array's path followed by
  `.length` (or `length` at the top level); otherwise elements are compared in index order, and index `i` adds
  `[i]` to the path
- two **plain objects** are compared key by key, taking the keys of both objects together **in sorted order**;
  a key present on one side only is itself the difference; key `k` adds `.k` to the path (`k` at the top level)
- anything else (numbers, strings, booleans, `null`, or an array against an object) is compared with
  `Object.is`; a difference at the very top level is reported as `"(root)"`

**Examples:**
`firstDifference({a: 1, b: 2}, {b: 2, a: 1})` → `null` ·
`firstDifference({items: [{price: 4}, {price: 6}]}, {items: [{price: 4}, {price: 7}]})` → `"items[1].price"` ·
`firstDifference([1, 2], [1, 2, 3])` → `"length"`
""",
    starter="function firstDifference(expected, actual) {\n  // return null, or the path of the first difference\n}\n",
    solution=DIFF_SOLUTION,
    tests=[
        [{"a": 1, "b": 2}, {"b": 2, "a": 1}],
        [{"items": [{"price": 4}, {"price": 6}]}, {"items": [{"price": 4}, {"price": 7}]}],
        [[1, 2], [1, 2, 3]],
        [{"a": 1, "b": 2}, {"a": 1, "b": 3}],
        [[1, 2, 3], [1, 5, 3]],
        [{"a": 1}, {"a": 1, "extra": True}],
        [{"user": {"name": "Ada", "tags": ["x"]}}, {"user": {"name": "Ada", "tags": ["x", "y"]}}],
        [5, 5],
        [5, "5"],
        [[1, 2], {"0": 1, "1": 2}],
        [{"a": None}, {"a": {}}],
        [{"z": 1, "a": {"k": [0]}}, {"z": 2, "a": {"k": [1]}}],
        [{"a": {"b": {"c": {"d": [1, {"e": None}]}}}}, {"a": {"b": {"c": {"d": [1, {"e": None}]}}}}],
        [[[1, [2, 3]]], [[1, [2, 4]]]],
        [{"only": 1, "shared": 2}, {"shared": 2}],
    ],
    wrong_solutions=[
        "function firstDifference(expected, actual) {\n  return JSON.stringify(expected) === JSON.stringify(actual) ? null : \"(root)\";\n}\n",
        "function firstDifference(expected, actual) {\n  function walk(a, b, path) {\n    if (a !== null && b !== null && typeof a === \"object\" && typeof b === \"object\") {\n      for (const key of Object.keys(a)) {\n        const next = path === \"\" ? key : path + \".\" + key;\n        if (!(key in b)) return next;\n        const found = walk(a[key], b[key], next);\n        if (found !== null) return found;\n      }\n      return null;\n    }\n    return Object.is(a, b) ? null : (path === \"\" ? \"(root)\" : path);\n  }\n  return walk(expected, actual, \"\");\n}\n",
        DIFF_SOLUTION.replace(".sort()", ""),
        DIFF_SOLUTION.replace("if (a.length !== b.length) return path === \"\" ? \"length\" : path + \".length\";", ""),
    ],
    guide=G(
        prereqs="Recursion over nested data, `Array.isArray`, `Object.keys`; `toBe` versus `toEqual` from the first lesson.",
        intuition="Deep equality is a walk over two trees in step. Carry the path you have walked so far; the first place where the two trees disagree is the answer, and the path you are holding is its address.",
        hints=[
            "Write a helper `walk(a, b, path)` that returns `null` or a path, and return from the loop as soon as a recursive call finds something.",
            "Decide the *kind* of each pair first: both arrays, both plain objects, or everything else. `typeof null` is `\"object\"`, so exclude `null` explicitly.",
            "For objects, loop over the sorted union of both key lists, and report a key that only one side has before recursing.",
        ],
        brute_force="`JSON.stringify(a) === JSON.stringify(b)` answers yes or no for simple data, but it depends on key order and cannot say where the difference is.",
        approach="1. Both arrays: compare lengths, then each index, extending the path with `[i]`.\n2. Both plain objects: sorted union of keys; a key missing on either side is the difference; otherwise recurse with `.key`.\n3. Otherwise `Object.is`.\n\n**Dry run** on the second example: root objects, key `items` → both arrays of length 2 → index 0: objects, key `price`, `4` vs `4` fine → index 1: key `price`, `6` vs `7` differ → return `items[1].price`.",
        complexity="O(n) for n values in the smaller structure, plus sorting the keys of each object; recursion depth equals the nesting depth.",
        pitfalls="- Treating arrays as objects makes `[1, 2]` equal to `{\"0\": 1, \"1\": 2}`.\n- Looping over the expected object's keys only misses extra keys on the actual side.\n- Without sorting, the reported path depends on the order in which the keys happened to be written.\n- Forgetting that `null` has `typeof` `\"object\"`.",
        follow_up="Return *all* differences as a list of `{path, expected, actual}`; that is the data a test runner needs to print a diff.",
    ),
),
dict(
    id="jstest-tiny-runner", title="A test runner that counts", difficulty="Easy", pattern="Test runners",
    kind="js", entry="runSuite",
    description=r"""
Write the heart of every test framework. `runTests(tests)` receives an array of `{ name, fn }` objects and
returns a report:

```
{ total, passed, failed, failures: [{ name, message }, ...] }
```

- a test **passes** when calling `fn()` does not throw, and **fails** when it throws
- every test runs, whatever happened to the ones before it, in the order given
- `failures` lists the failed tests in order; `message` is the `message` of the thrown `Error`, or, if
  something that is not an `Error` was thrown (JavaScript allows `throw "text"`), that value converted with
  `String(...)`

The driver builds the test functions from short descriptions (`"pass"`, `"fail"` with a message,
`"throwString"` with a text) and also returns the order in which they actually ran.

**Example:** `runSuite([["adds", "pass"], ["subtracts", "fail", "expected 1 but got 2"]])` →
`{report: {total: 2, passed: 1, failed: 1, failures: [{name: "subtracts", message: "expected 1 but got 2"}]}, ranInOrder: ["adds", "subtracts"]}`
""",
    starter="function runTests(tests) {\n  // tests: [{ name, fn }, ...]\n  // return { total, passed, failed, failures }\n}\n" + RUNNER_DRIVER,
    solution=RUNNER_SOLUTION + RUNNER_DRIVER,
    tests=[
        [[["adds", "pass"], ["subtracts", "fail", "expected 1 but got 2"]]],
        [[["a", "pass"], ["b", "pass"], ["c", "pass"]]],
        [[["first", "fail", "boom"], ["second", "pass"], ["third", "pass"]]],
        [[]],
        [[["odd one", "throwString", "plain text, not an Error"]]],
        [[["x", "fail", "one"], ["y", "fail", "two"], ["z", "fail", "three"]]],
        [[["a", "pass"], ["b", "throwString", "oops"], ["c", "fail", "bad"], ["d", "pass"]]],
        [[["empty message", "fail", ""], ["after", "pass"]]],
        [[["same", "pass"], ["same", "fail", "second copy fails"]]],
        [[["t" + str(i), "fail" if i % 3 == 0 else "pass", "m" + str(i)] for i in range(12)]],
    ],
    examples=2,
    wrong_solutions=[
        "function runTests(tests) {\n  const report = { total: tests.length, passed: 0, failed: 0, failures: [] };\n  for (const { name, fn } of tests) {\n    try { fn(); report.passed++; }\n    catch (thrown) { report.failed++; report.failures.push({ name, message: thrown.message }); break; }\n  }\n  return report;\n}\n" + RUNNER_DRIVER,
        "function runTests(tests) {\n  const report = { total: tests.length, passed: 0, failed: 0, failures: [] };\n  for (const { name, fn } of tests) {\n    try { fn(); report.passed++; }\n    catch (thrown) { report.failed++; report.failures.push({ name, message: thrown.message }); }\n  }\n  return report;\n}\n" + RUNNER_DRIVER,
        "function runTests(tests) {\n  const report = { total: tests.length, passed: 0, failed: 0, failures: [] };\n  try {\n    for (const { name, fn } of tests) { fn(); report.passed++; }\n  } catch (thrown) {\n    report.failed++;\n    report.failures.push({ name: \"?\", message: String(thrown) });\n  }\n  return report;\n}\n" + RUNNER_DRIVER,
    ],
    guide=G(
        prereqs="`try` / `catch`, arrays of objects, destructuring. Lesson *Why automate tests: your first unit test* builds this runner step by step.",
        intuition="A runner is a loop with a `try` / `catch` inside it. The `try` must wrap a *single* test, so that one failure is recorded and the loop carries on.",
        hints=[
            "Put the `try` inside the `for` loop, not around it.",
            "Count in the `try` branch after `fn()` returns; record in the `catch` branch.",
            "`thrown instanceof Error ? thrown.message : String(thrown)` handles `throw \"text\"`.",
        ],
        brute_force="There is no slower correct approach; the common incorrect one is a single `try` around the whole loop, which stops at the first failure.",
        approach="Start with `{ total: tests.length, passed: 0, failed: 0, failures: [] }`. For each test: call `fn()` in a `try`; on success increment `passed`; on a throw increment `failed` and push `{ name, message }`.\n\n**Dry run** `[first: fail, second: pass]`: `first` throws → `failed = 1`, failure recorded; the loop continues; `second` returns → `passed = 1`.",
        complexity="O(n) calls for n tests.",
        pitfalls="- A `break` or a `try` around the loop hides every test after the first failure.\n- `thrown.message` is `undefined` when a string was thrown, and the property then disappears from the JSON report.\n- An empty message `\"\"` is still a failure; do not test the message for truthiness.",
        follow_up="Make it asynchronous: `await fn()` inside the `try`, so tests may return promises. Then add a `skip` flag per test.",
    ),
),
dict(
    id="jstest-runner-hooks", title="beforeEach and afterEach", difficulty="Medium", pattern="Test runners",
    kind="js", entry="runWithHooks",
    description=r"""
Extend a runner with **hooks**. Write `createRunner()`, which returns an object with four methods:

- `beforeEach(fn)` and `afterEach(fn)` register hook functions
- `test(name, fn)` registers a test
- `run()` executes the tests in registration order and returns `{ passed, failed }`

For **each** test, `run` calls every `beforeEach` hook (in the order they were registered), then the test
function, then every `afterEach` hook (in registration order). The `afterEach` hooks must run **even when the
test throws**: cleanup is the whole point of them. Hooks apply to all tests, including tests that were
registered before the hook was. A test passes when its function does not throw. Hooks never throw in these tests.

The driver registers hooks and tests that write to a log and returns the log with the counts.

**Example:** `runWithHooks([["beforeEach", "A"], ["afterEach", "Z"], ["test", "t1", "fail"], ["test", "t2", "pass"]])` →
`{log: ["before A", "test t1", "after Z", "before A", "test t2", "after Z"], passed: 1, failed: 1}`
""",
    starter="function createRunner() {\n  // return { beforeEach(fn), afterEach(fn), test(name, fn), run() }\n}\n" + HOOKS_DRIVER,
    solution=HOOKS_SOLUTION + HOOKS_DRIVER,
    tests=[
        [[["beforeEach", "A"], ["afterEach", "Z"], ["test", "t1", "fail"], ["test", "t2", "pass"]]],
        [[["beforeEach", "A"], ["test", "t1", "pass"], ["test", "t2", "pass"]]],
        [[["test", "t1", "pass"], ["beforeEach", "late"], ["test", "t2", "pass"]]],
        [[["beforeEach", "A"], ["beforeEach", "B"], ["afterEach", "Y"], ["afterEach", "Z"], ["test", "t1", "pass"]]],
        [[["test", "t1", "pass"], ["test", "t2", "fail"], ["test", "t3", "pass"]]],
        [[["beforeEach", "A"], ["afterEach", "Z"]]],
        [[]],
        [[["beforeEach", "A"], ["afterEach", "Z"], ["test", "a", "fail"], ["test", "b", "fail"]]],
        [[["afterEach", "cleanup"], ["test", "only", "fail"]]],
        [[["test", "x", "fail"], ["afterEach", "Z"], ["test", "y", "pass"], ["beforeEach", "A"], ["test", "z", "fail"], ["afterEach", "Y"]]],
    ],
    examples=2,
    wrong_solutions=[
        HOOKS_SOLUTION.replace("catch (error) { failed++; }\n        finally { for (const hook of after) hook(); }", "catch (error) { failed++; continue; }\n        for (const hook of after) hook();") + HOOKS_DRIVER,
        "function createRunner() {\n  const before = [], after = [], tests = [];\n  return {\n    beforeEach(fn) { before.push(fn); },\n    afterEach(fn) { after.push(fn); },\n    test(name, fn) { tests.push({ name, fn }); },\n    run() {\n      let passed = 0, failed = 0;\n      for (const hook of before) hook();\n      for (const { fn } of tests) {\n        try { fn(); passed++; } catch (error) { failed++; }\n      }\n      for (const hook of after) hook();\n      return { passed, failed };\n    },\n  };\n}\n" + HOOKS_DRIVER,
        "function createRunner() {\n  const before = [], after = [], tests = [];\n  return {\n    beforeEach(fn) { before.push(fn); },\n    afterEach(fn) { after.push(fn); },\n    test(name, fn) { tests.push({ name, fn, before: [...before], after: [...after] }); },\n    run() {\n      let passed = 0, failed = 0;\n      for (const t of tests) {\n        for (const hook of t.before) hook();\n        try { t.fn(); passed++; } catch (error) { failed++; } finally { for (const hook of t.after) hook(); }\n      }\n      return { passed, failed };\n    },\n  };\n}\n" + HOOKS_DRIVER,
    ],
    guide=G(
        prereqs="Closures holding arrays of functions; `try` / `catch` / `finally`. Lesson *Setup, teardown, suites and integration tests*.",
        intuition="Registration only stores functions in three lists. All the work happens in `run`, which wraps each test in the same sandwich: hooks, test, hooks. `finally` guarantees the bottom slice.",
        hints=[
            "Keep three arrays in the closure: before hooks, after hooks, tests.",
            "Inside the loop over tests: run the before hooks, then `try { fn(); passed++ } catch { failed++ }`.",
            "Put the after hooks in a `finally` block so they run on both paths.",
        ],
        brute_force="Copying the after-hook loop into both the success path and the `catch` block works but duplicates code; `finally` says it once.",
        approach="`run` loops over the tests. For each: every before hook; `try` the test; count; `finally` every after hook. Return the counts.\n\n**Dry run** of the example: test `t1`: `before A`, `test t1` (throws, `failed = 1`), `after Z`. Test `t2`: `before A`, `test t2`, `after Z`, `passed = 1`.",
        complexity="O(t · h) hook calls for t tests and h hooks.",
        pitfalls="- Skipping `afterEach` when a test fails leaves state behind for the next test, which is the bug hooks exist to prevent.\n- Running the hooks once for the whole suite: that is `beforeAll` / `afterAll`.\n- Copying the hook lists at the moment a test is registered, so hooks added later do not apply.",
        follow_up="Add `describe(name, body)` with hooks that apply only inside their block, and decide what should happen when a `beforeEach` hook itself throws.",
    ),
),
dict(
    id="jstest-string-calculator", title="TDD kata: the string calculator", difficulty="Easy", pattern="TDD kata",
    kind="js", entry="calc",
    description=r"""
A classic exercise for practising small test-first steps. Grow `add(text)` one rule at a time, running the
tests after each rule. The tests are ordered so that each one needs roughly one new rule.

1. An empty string (or only spaces) gives `0`.
2. A single number gives that number: `"5"` → `5`.
3. Numbers are separated by commas: `"1,2"` → `3`.
4. A line break is also a separator: `"1\n2,3"` → `6`.
5. The text may start with a line `//X` naming a **custom separator** `X` (one or more characters), which then
   replaces comma and line break: `"//;\n1;2"` → `3`, `"//sep\n2sep3"` → `5`.
6. Spaces around a number are ignored.
7. Numbers greater than 1000 are ignored: `"2,1001"` → `2` (1000 itself counts).
8. Negative numbers are an error: throw `new Error("negatives not allowed: -2, -4")`, listing **all** of them
   in order.
9. A piece that is not a number (including an empty piece, as in `"1,,2"`) is an error: throw
   `new Error("not a number: " + piece)` with the trimmed piece.

The driver calls `add` and returns its result, or the text `"error: " + message` when it throws.

**Examples:** `calc("1\n2,3")` → `6` · `calc("1,-2,3,-4")` → `"error: negatives not allowed: -2, -4"`
""",
    starter="function add(text) {\n  // start with rule 1 and add one rule at a time\n}\n" + CALC_DRIVER,
    solution=CALC_SOLUTION + CALC_DRIVER,
    tests=[
        [""],
        ["5"],
        ["1,2"],
        ["1\n2,3"],
        ["//;\n1;2"],
        ["//sep\n2sep3sep4"],
        [" 7 , 8 "],
        ["2,1001"],
        ["1000,1"],
        ["1,-2,3,-4"],
        ["1,,2"],
        ["1,a"],
        ["//|\n1|2|3"],
        ["-5"],
        ["   "],
    ],
    examples=3,
    wrong_solutions=[
        "function add(text) {\n  if (text.trim() === \"\") return 0;\n  const numbers = text.split(\",\").map((p) => { const t = p.trim(); const v = Number(t); if (t === \"\" || Number.isNaN(v)) throw new Error(\"not a number: \" + t); return v; });\n  const negatives = numbers.filter((n) => n < 0);\n  if (negatives.length) throw new Error(\"negatives not allowed: \" + negatives.join(\", \"));\n  return numbers.filter((n) => n <= 1000).reduce((s, n) => s + n, 0);\n}\n" + CALC_DRIVER,
        CALC_SOLUTION.replace("negatives.join(\", \")", "negatives[0]") + CALC_DRIVER,
        CALC_SOLUTION.replace("n <= 1000", "n < 1000") + CALC_DRIVER,
        CALC_SOLUTION.replace("if (trimmed === \"\" || Number.isNaN(value))", "if (Number.isNaN(value))") + CALC_DRIVER,
    ],
    guide=G(
        prereqs="String methods `split`, `trim`, `startsWith`, `indexOf`; `Number(...)`; the red, green, refactor loop.",
        intuition="Every rule changes one of three stages: *find the separators*, *cut the text into pieces*, *turn pieces into a sum*. Keep the stages apart and each new rule lands in exactly one place.",
        hints=[
            "Write the line break as `String.fromCharCode(10)` if you want to avoid escape sequences.",
            "For a custom separator, the header is everything between `//` and the first line break; the body is everything after it.",
            "Convert all pieces to numbers first, then check for negatives on the whole list so the message can name every one.",
        ],
        brute_force="A regular expression that splits on comma or line break handles rules 3 and 4, but the custom separator of rule 5 then needs escaping. Splitting by each separator in turn avoids that.",
        approach="1. If the text starts with `//`, read the separator and remove the header line; otherwise the separators are comma and line break.\n2. Blank body → 0.\n3. Split by every separator, trim, convert with `Number`; an empty piece or `NaN` throws.\n4. Collect negatives; if any, throw with all of them.\n5. Drop numbers above 1000 and sum.\n\n**Dry run** `\"//;\\n1;2\"`: separator `;`, body `1;2`, pieces `[\"1\", \"2\"]`, numbers `[1, 2]`, no negatives, sum 3.",
        complexity="O(n) in the length of the text.",
        pitfalls="- `Number(\"\")` is `0`, so an empty piece must be rejected before converting.\n- Throwing at the first negative reports only one of them.\n- `< 1000` drops 1000 itself.\n- Checking for the blank text before removing the header gives the wrong answer for a header with an empty body.",
        follow_up="Allow several custom separators written as `//[a][bb]`. In a real kata you would also write the tests yourself, one before each rule.",
    ),
),
dict(
    id="jstest-suite-names", title="Full names from nested describe blocks", difficulty="Easy", pattern="Test runners",
    kind="js", entry="fullNames",
    description=r"""
A test report shows each test with the names of the suites around it:
`basket > when empty > has a total of zero`. Produce those names.

`fullNames(suite)` receives a suite object

```
{ name: "basket", tests: ["starts empty"], suites: [ { name: "when empty", tests: [...], suites: [...] } ] }
```

and returns the full names of all tests, each made of the enclosing suite names and the test name joined by
`" > "`.

- within a suite, its own tests come first (in order), then its child suites (in order), recursively
- `tests` or `suites` may be missing, which means empty
- a suite whose `name` is the empty string adds nothing to the names (runners use an unnamed root suite for a file)

**Example:** `fullNames({name: "clamp", tests: ["exists"], suites: [{name: "inside the range", tests: ["returns the number"]}]})` →
`["clamp > exists", "clamp > inside the range > returns the number"]`
""",
    starter="function fullNames(suite) {\n  // your code\n}\n",
    solution="function fullNames(suite, path = []) {\n  const here = suite.name ? [...path, suite.name] : path;\n  const names = (suite.tests || []).map((test) => [...here, test].join(\" > \"));\n  for (const child of suite.suites || []) names.push(...fullNames(child, here));\n  return names;\n}\n",
    tests=[
        [{"name": "clamp", "tests": ["exists"], "suites": [{"name": "inside the range", "tests": ["returns the number"]}]}],
        [{"name": "basket", "tests": ["starts empty", "adds items"]}],
        [{"name": "", "tests": ["top level test"], "suites": [{"name": "math", "tests": ["adds"]}]}],
        [{"name": "a", "suites": [{"name": "b", "suites": [{"name": "c", "suites": [{"name": "d", "tests": ["deep"]}]}]}]}],
        [{"name": "empty suite"}],
        [{"name": "root", "tests": ["t1"], "suites": [{"name": "s1", "tests": ["t2"], "suites": [{"name": "s1a", "tests": ["t3"]}]}, {"name": "s2", "tests": ["t4", "t5"]}]}],
        [{"name": "", "suites": [{"name": "", "tests": ["nameless all the way"]}]}],
        [{"name": "outer", "tests": [], "suites": [{"name": "inner", "tests": []}]}],
        [{"name": "order", "suites": [{"name": "child", "tests": ["child test"]}], "tests": ["own test first"]}],
        [{"name": "x", "tests": ["same", "same"], "suites": [{"name": "y", "tests": ["same"]}]}],
    ],
    wrong_solutions=[
        "function fullNames(suite) {\n  const names = (suite.tests || []).map((t) => suite.name + \" > \" + t);\n  for (const child of suite.suites || []) for (const t of child.tests || []) names.push(suite.name + \" > \" + child.name + \" > \" + t);\n  return names;\n}\n",
        "function fullNames(suite, path = []) {\n  const here = suite.name ? [...path, suite.name] : path;\n  const names = [];\n  for (const child of suite.suites || []) names.push(...fullNames(child, here));\n  names.push(...(suite.tests || []).map((test) => [...here, test].join(\" > \")));\n  return names;\n}\n",
        "function fullNames(suite, path = []) {\n  const here = [...path, suite.name];\n  const names = (suite.tests || []).map((test) => [...here, test].join(\" > \"));\n  for (const child of suite.suites || []) names.push(...fullNames(child, here));\n  return names;\n}\n",
    ],
    guide=G(
        prereqs="Recursion on a tree, arrays, `join`. Lesson *Tools of the trade* builds a `describe` / `it` runner with a stack of names.",
        intuition="The suite names above a test form a path, like folders above a file. Walk the tree carrying the path; at each test, glue the path and the test name together.",
        hints=[
            "Give the function a second parameter for the path so far, with a default of `[]`.",
            "Compute this suite's path once: the parent's path plus its own name, unless the name is empty.",
            "Emit this suite's tests first, then recurse into each child and append what it returns.",
        ],
        brute_force="Two nested loops handle a suite and its direct children, and nothing deeper. Recursion handles any depth with the same few lines.",
        approach="`here = name ? [...path, name] : path`. Map the suite's tests to `[...here, test].join(\" > \")`. For each child suite, push the results of the recursive call with `here` as the path.\n\n**Dry run** of the example: `here = [\"clamp\"]`; test `exists` → `clamp > exists`; child `inside the range` → `here = [\"clamp\", \"inside the range\"]` → `clamp > inside the range > returns the number`.",
        complexity="O(total length of the output): every test is visited once and its name is built from its path.",
        pitfalls="- Hard-coding two levels of nesting.\n- Listing child suites before the suite's own tests.\n- Including an empty suite name, which produces a leading ` > `.\n- Calling `.map` on a missing `tests` property.",
        follow_up="Real runners build this list with a stack: `describe` pushes its name, runs its body and pops. Rewrite the function iteratively with an explicit stack.",
    ),
),
dict(
    id="jstest-prototype-lookup", title="Who owns this property?", difficulty="Easy", pattern="Prototypes",
    kind="js", entry="lookup",
    description=r"""
Reading `object.key` searches the object and then each object on its **prototype chain** until the property is
found. Write the search yourself, as a learning test would.

`findOwner(object, key)` returns how many steps up the chain the property is found as an **own** property:
`0` if `object` itself has it, `1` if its prototype has it, and so on. Return `-1` if no object on the chain
has it. A property counts as present whatever its value is, including `null`, `false`, `0` and `undefined`.

The driver builds a real prototype chain from a list of plain objects (`layers[0]` is the object itself,
`layers[1]` its prototype, ...). The last layer inherits from `Object.prototype`, as every ordinary object does,
so built-in names such as `toString` are found one step above the last layer.

**Examples:** `lookup([{a: 1}, {b: 2}], "a")` → `0` · `lookup([{a: 1}, {b: 2}], "b")` → `1` ·
`lookup([{a: 1}, {b: 2}], "toString")` → `2` · `lookup([{a: 1}], "zzz")` → `-1`
""",
    starter="function findOwner(object, key) {\n  // walk up with Object.getPrototypeOf until you reach null\n}\n" + PROTO_DRIVER,
    solution="function findOwner(object, key) {\n  let steps = 0;\n  for (let current = object; current !== null; current = Object.getPrototypeOf(current)) {\n    if (Object.hasOwn(current, key)) return steps;\n    steps++;\n  }\n  return -1;\n}\n" + PROTO_DRIVER,
    tests=[
        [[{"a": 1}, {"b": 2}], "a"],
        [[{"a": 1}, {"b": 2}], "b"],
        [[{"a": 1}, {"b": 2}], "toString"],
        [[{"a": 1}], "zzz"],
        [[{"x": None}], "x"],
        [[{}, {"flag": False}], "flag"],
        [[{"n": 1}, {"n": 2}, {"n": 3}], "n"],
        [[{}, {}, {}, {"deep": 0}], "deep"],
        [[{}], "hasOwnProperty"],
        [[{"toString": "mine"}], "toString"],
        [[{"a": 1}, {"b": 2}, {"c": 3}], "c"],
        [[{}, {"": "empty key"}], ""],
    ],
    examples=4,
    wrong_solutions=[
        "function findOwner(object, key) {\n  return key in object ? 0 : -1;\n}\n" + PROTO_DRIVER,
        "function findOwner(object, key) {\n  let steps = 0;\n  for (let current = object; current !== null; current = Object.getPrototypeOf(current)) {\n    if (current[key] !== undefined) return steps;\n    steps++;\n  }\n  return -1;\n}\n" + PROTO_DRIVER,
        "function findOwner(object, key) {\n  let steps = 0;\n  for (let current = object; current !== null; current = Object.getPrototypeOf(current)) {\n    if (Object.hasOwn(current, key) && current[key]) return steps;\n    steps++;\n  }\n  return -1;\n}\n" + PROTO_DRIVER,
    ],
    guide=G(
        prereqs="Own versus inherited properties and `Object.getPrototypeOf`, from the lesson *Objects and prototype chains, explored with tests*.",
        intuition="The chain is a linked list whose `next` pointer is the prototype. Walk it, counting steps, and at each stop ask one question: is the property this object's *own*?",
        hints=[
            "The chain ends when `Object.getPrototypeOf(current)` returns `null`.",
            "`Object.hasOwn(current, key)` (or `Object.prototype.hasOwnProperty.call(current, key)`) looks at one object only.",
            "Do not read the value to decide whether the property exists; a stored `null` or `false` is still a property.",
        ],
        brute_force="`key in object` tells you the property exists somewhere on the chain but not where. You need the walk to count the steps.",
        approach="Start at the object with `steps = 0`. While the current object is not `null`: if it has the key as an own property, return `steps`; otherwise move to its prototype and add one. Return `-1` after the loop.\n\n**Dry run** `lookup([{a: 1}, {b: 2}], \"toString\")`: step 0 has only `a`; step 1 has only `b`; step 2 is `Object.prototype`, which owns `toString` → `2`.",
        complexity="O(d) for a chain of depth d.",
        pitfalls="- `current[key] !== undefined` reads *through* the chain, so an inherited property looks like an own one.\n- Testing the value for truthiness loses `null`, `false`, `0` and `\"\"`.\n- Forgetting `Object.prototype`: built-in methods are inherited properties too.",
        follow_up="Return the list of all owners, which shows shadowing: the nearest owner hides the others. Then explain why `for...in` lists inherited enumerable properties and `Object.keys` does not.",
    ),
),
dict(
    id="jstest-boundary-values", title="Boundary values for a range", difficulty="Easy", pattern="Test design",
    kind="js", entry="boundaryValues",
    description=r"""
A rule such as "age must be between 18 and 65 inclusive" splits the integers into three groups: too small,
valid, too large. Off-by-one bugs sit at the edges between the groups, so a tester picks the values on both
sides of each edge. This is **boundary value analysis**.

Write `boundaryValues(min, max)` for an inclusive integer range. Return the test inputs
`min - 1, min, min + 1, max - 1, max, max + 1`, **without duplicates**, in **ascending numeric order**, each
paired with whether it is inside the range:

`[[value, isValid], ...]`

If `min > max` the range is empty: return `[]`.

**Examples:**
`boundaryValues(18, 65)` → `[[17, false], [18, true], [19, true], [64, true], [65, true], [66, false]]` ·
`boundaryValues(5, 5)` → `[[4, false], [5, true], [6, false]]`
""",
    starter="function boundaryValues(min, max) {\n  // your code\n}\n",
    solution="function boundaryValues(min, max) {\n  if (min > max) return [];\n  const candidates = [min - 1, min, min + 1, max - 1, max, max + 1];\n  const unique = [...new Set(candidates)].sort((a, b) => a - b);\n  return unique.map((value) => [value, value >= min && value <= max]);\n}\n",
    tests=[
        [18, 65], [5, 5], [1, 2], [0, 10], [-3, 3], [10, 1], [1, 3], [-10, -1], [0, 0], [100, 1000], [7, 9], [-1, 0], [9, 11],
    ],
    examples=2,
    wrong_solutions=[
        "function boundaryValues(min, max) {\n  if (min > max) return [];\n  const unique = [...new Set([min - 1, min, min + 1, max - 1, max, max + 1])].sort();\n  return unique.map((v) => [v, v >= min && v <= max]);\n}\n",
        "function boundaryValues(min, max) {\n  if (min > max) return [];\n  return [min - 1, min, min + 1, max - 1, max, max + 1].sort((a, b) => a - b).map((v) => [v, v >= min && v <= max]);\n}\n",
        "function boundaryValues(min, max) {\n  if (min > max) return [];\n  const valid = new Set([min, min + 1, max - 1, max]);\n  const unique = [...new Set([min - 1, min, min + 1, max - 1, max, max + 1])].sort((a, b) => a - b);\n  return unique.map((v) => [v, valid.has(v)]);\n}\n",
        "function boundaryValues(min, max) {\n  const unique = [...new Set([min - 1, min, min + 1, max - 1, max, max + 1])].sort((a, b) => a - b);\n  return unique.map((v) => [v, v >= min && v <= max]);\n}\n",
    ],
    guide=G(
        prereqs="`Set` for removing duplicates, `sort` with a comparison function. The idea of equivalence classes from the interview lesson.",
        intuition="Six candidate values, two per edge plus one just outside each edge. Narrow ranges make some of them coincide, so remove duplicates, and compute validity from the range itself, not from which candidate it was.",
        hints=[
            "List the six candidates first, then pass them through `new Set(...)`.",
            "`sort()` without an argument compares as text: `[-1, -10, 2, 10]` comes out in the wrong order. Use `(a, b) => a - b`.",
            "Decide `isValid` with `value >= min && value <= max`; for `min === max`, `min + 1` is outside the range.",
        ],
        brute_force="Testing every integer in the range is possible for small ranges and useless for large ones. Boundary values give the same bug-finding power with six inputs.",
        approach="Empty range → `[]`. Build the six candidates, de-duplicate, sort numerically, map each to `[value, inside]`.\n\n**Dry run** `(5, 5)`: candidates `4, 5, 6, 4, 5, 6` → unique `4, 5, 6` → `[[4, false], [5, true], [6, false]]`.",
        complexity="O(1): always at most six values.",
        pitfalls="- Default `sort()` orders numbers as strings.\n- Assuming `min + 1` and `max - 1` are always valid; they are not when the range has one value.\n- Returning candidates for an empty range.",
        follow_up="Extend to two independent ranges (for example quantity and price) and decide how many combinations are worth testing.",
    ),
),
]
