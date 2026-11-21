# Vitest, Jest and node:test in daily use

> **Before this lesson:** you know what a runner, a suite, coverage and CI are from [Tools of the trade: runners, styles, coverage and CI](#/lesson/js-testing/test-runners-tools), and you have written hooks such as `beforeEach` in [Setup, teardown, suites and integration tests](#/lesson/js-testing/setup-suites-integration). You should know what npm and `package.json` are ([Node.js: modules, files, streams and npm](#/lesson/javascript/node-core)) and the difference between ES modules and CommonJS ([ES modules and CommonJS](#/lesson/javascript/es-modules-commonjs)).

## In plain words

Up to now most tests in this track ran on a tiny runner written inside the lesson. That was deliberate: it shows that nothing magical is going on. A real project uses a ready-made runner, and three of them cover nearly every JavaScript codebase you will meet: **Vitest**, **Jest** and the runner built into Node, **`node:test`**.

Think of hiring a car abroad. The pedals and the steering wheel are where you expect, so you can drive off at once. What you have to look for is the small stuff: where the lights are, how the handbrake works, which side the fuel cap is on. The three runners share the pedals: `test`, `describe`, hooks and assertions. This lesson is the walk round the car: how to install and configure each one, how to run one test and not five hundred, which assertions exist, and what the failure output is telling you.

Why it matters for a job: on your first day you will be asked to "run the tests", then to add one, then to work out why one fails in CI. None of that is theory. It is knowing the dozen commands and options in this lesson, whichever runner the team picked.

## The same test in three runners

A function to test:

```javascript
// slug.js
export function slugify(title) {
  return title.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}
```

**Vitest.** Install with `npm install --save-dev vitest`. Test functions are imported from the package.

```javascript
// slug.test.js
import { describe, test, expect } from "vitest";
import { slugify } from "./slug.js";

describe("slugify", () => {
  test("lower-cases and joins words with hyphens", () => {
    expect(slugify("Hello World")).toBe("hello-world");
  });
  test("drops punctuation at the ends", () => {
    expect(slugify("  What's new?  ")).toBe("what-s-new");
  });
});
```

**Jest.** Install with `npm install --save-dev jest`. `describe`, `test` and `expect` are **globals**: they exist in every test file without an import. The test file is otherwise identical; delete the first import line.

**`node:test`.** Nothing to install. The runner and an assertion module ship with Node.

```javascript
// slug.test.js
import { describe, test } from "node:test";
import assert from "node:assert/strict";
import { slugify } from "./slug.js";

describe("slugify", () => {
  test("lower-cases and joins words with hyphens", () => {
    assert.equal(slugify("Hello World"), "hello-world");
  });
  test("drops punctuation at the ends", () => {
    assert.equal(slugify("  What's new?  "), "what-s-new");
  });
});
```

Run them with `npx vitest run`, `npx jest` or `node --test`. `npx` runs a command from the project's installed packages. The structure is the same in all three; the visible difference is the assertion style, `expect(actual).toBe(expected)` against `assert.equal(actual, expected)`.

| | Vitest | Jest | `node:test` |
|---|---|---|---|
| Install | `vitest` | `jest` | built into Node |
| Test functions | imported (or globals with `globals: true`) | globals (or imported from `@jest/globals`) | imported from `node:test` |
| Assertions | `expect` | `expect` | `node:assert` |
| Doubles | `vi.fn`, `vi.spyOn`, `vi.mock` | `jest.fn`, `jest.spyOn`, `jest.mock` | `mock.fn`, `mock.method` |
| Fake timers | `vi.useFakeTimers()` | `jest.useFakeTimers()` | `mock.timers.enable()` |
| ES modules and TypeScript | work without setup | need a transform step (Babel, SWC or ts-jest) | ES modules yes; recent Node versions also run TypeScript that only uses removable type syntax |
| Simulated DOM | `environment: "jsdom"` or `"happy-dom"` | `testEnvironment: "jsdom"` plus the `jest-environment-jsdom` package | bring your own |
| Config file | `vitest.config.js` (or the `test` key of `vite.config.js`) | `jest.config.js` / `.mjs` (or a `jest` key in `package.json`) | command-line flags |

## Which files count as tests

Runners find test files by name, so the name matters.

- **Vitest and Jest**: any file ending in `.test.js` or `.spec.js` (also `.ts`, `.jsx`, `.tsx` and so on); Jest also picks up everything inside a folder named `__tests__`.
- **`node --test`**: files ending in `.test.js`, `-test.js` or `_test.js`, files named `test-*.js`, and every JavaScript file under a folder named `test`.

Two layouts are common: tests next to the code (`slug.js` beside `slug.test.js`), or a parallel `test/` folder. Keeping the test beside the source makes a missing test easy to spot and is the usual choice in front-end projects.

## Running a subset

Running everything is for CI. While you work you want one file or one test.

| Goal | Vitest | Jest | `node:test` |
|---|---|---|---|
| Everything, once | `npx vitest run` | `npx jest` | `node --test` |
| Watch and re-run on save | `npx vitest` | `npx jest --watch` | `node --test --watch` |
| One file | `npx vitest run slug` | `npx jest slug` | `node --test slug.test.js` |
| Tests whose name matches | `npx vitest run -t "hyphens"` | `npx jest -t "hyphens"` | `node --test --test-name-pattern="hyphens"` |
| Stop at the first failure | `--bail=1` | `--bail` | not available; narrow the run with a name pattern |
| Only tests affected by uncommitted changes | `npx vitest --changed` | `npx jest --onlyChanged` | not available |

Inside a file, every runner lets you mark tests:

```javascript
test.only("the one I am debugging", () => { /* ... */ });   // run this, skip its siblings
test.skip("broken on Windows, see ticket 812", () => { /* ... */ });
test.todo("rejects names longer than 80 characters");       // a reminder with no body
```

`node:test` spells the same options as an object, `test("name", { skip: true }, fn)`, and needs the flag `--test-only` for `only` to take effect.

> [!WARNING]
> `test.only` is a debugging tool. Committed by accident, it silently switches off every other test in the file while the run stays green. Add the lint rule `no-focused-tests`, which the ESLint plugins for Jest and for Vitest both provide, so the mistake is caught before the commit. Vitest has a second guard: when it detects a CI environment it fails the run if any `.only` is present (the `allowOnly` option controls this).

## The assertion toolbox

`expect(value)` returns an object full of **matchers**: methods that each check one kind of fact and throw a descriptive error when it does not hold. Knowing the common dozen saves you from writing awkward assertions such as `expect(list.includes(3)).toBe(true)`, whose failure message ("expected true, received false") says nothing useful.

| Category | Matcher (Vitest and Jest) | `node:assert/strict` |
|---|---|---|
| Same value or same object | `toBe(x)` | `assert.equal(a, x)` |
| Same contents | `toEqual(x)` | `assert.deepEqual(a, x)` |
| Same contents, same types, no extra `undefined` keys | `toStrictEqual(x)` | `assert.deepEqual(a, x)` (already strict) |
| Truthiness | `toBeTruthy()`, `toBeFalsy()`, `toBeNull()`, `toBeUndefined()`, `toBeDefined()` | `assert.ok(a)`, `assert.equal(a, null)` |
| Numbers | `toBeGreaterThan(n)`, `toBeLessThanOrEqual(n)`, `toBeCloseTo(n, digits)` | `assert.ok(a > n)` |
| Strings | `toMatch(/pattern/)`, `toContain("part")` | `assert.match(a, /pattern/)` |
| Arrays | `toHaveLength(n)`, `toContain(item)`, `toContainEqual(obj)` | `assert.equal(a.length, n)` |
| Part of an object | `toMatchObject({ k: v })`, `toHaveProperty("a.b", v)` | `assert.partialDeepStrictEqual` in newer Node versions |
| Errors | `expect(fn).toThrow("text")` | `assert.throws(fn, /text/)` |
| Promises | `await expect(p).resolves.toBe(x)`, `await expect(p).rejects.toThrow()` | `await assert.rejects(p, /text/)` |
| Doubles | `toHaveBeenCalledWith(...)`, `toHaveBeenCalledTimes(n)` | `assert.equal(f.mock.callCount(), n)` |
| Opposite | `expect(x).not.toBe(y)` | `assert.notEqual(a, y)` |

Inside `toEqual` and `toHaveBeenCalledWith` you may put **asymmetric matchers**, placeholders that accept a whole class of values: `expect.any(Number)`, `expect.anything()`, `expect.stringContaining("abc")`, `expect.objectContaining({ id: 7 })`, `expect.arrayContaining([1, 2])`. They let an assertion say "an id of some kind" where the exact value is unpredictable, such as a timestamp.

### How matchers work underneath

A matcher is a function that returns true or false, plus some wrapping that turns "false" into a thrown error and handles `.not`. The block below builds that wrapping, adds a matcher of its own with `expect.extend`, and shows the classic floating-point surprise.

```js-run
const matchers = {
  toBe: (actual, expected) => Object.is(actual, expected),
  toEqual: (actual, expected) => JSON.stringify(actual) === JSON.stringify(expected),
  toContain: (actual, item) => actual.includes(item),
  toBeCloseTo: (actual, expected, digits = 2) => Math.abs(actual - expected) < 10 ** -digits / 2,
  toMatchObject: (actual, part) => Object.keys(part).every((key) => JSON.stringify(actual[key]) === JSON.stringify(part[key])),
};

function expect(actual) {
  const build = (negated) => {
    const api = {};
    for (const [name, passes] of Object.entries(matchers)) {
      api[name] = (...expected) => {
        if (Boolean(passes(actual, ...expected)) === negated) {                 // wrong outcome: throw
          const shown = expected.map((e) => JSON.stringify(e)).join(", ");
          throw new Error("expected " + JSON.stringify(actual) + (negated ? " not." : " .") + name + "(" + shown + ")");
        }
      };
    }
    return api;
  };
  const api = build(false);
  api.not = build(true);                                                         // the same matchers, inverted
  return api;
}
expect.extend = (more) => Object.assign(matchers, more);                         // register your own matchers

function test(name, fn) {
  try { fn(); console.log("PASS  " + name); }
  catch (e) { console.log("FAIL  " + name + "\n      -> " + e.message); }
}

test("0.1 + 0.2 with toBe", () => expect(0.1 + 0.2).toBe(0.3));
test("0.1 + 0.2 with toBeCloseTo", () => expect(0.1 + 0.2).toBeCloseTo(0.3));
test("not.toContain", () => expect(["tea", "mug"]).not.toContain("coffee"));
test("toMatchObject ignores the fields it was not asked about", () => {
  expect({ id: 7, name: "Ada", createdAt: 1712345678 }).toMatchObject({ name: "Ada" });
});

expect.extend({ toBeEven: (actual) => actual % 2 === 0 });
test("a custom matcher", () => expect(10).toBeEven());
test("a custom matcher, failing", () => expect(7).toBeEven());
```

The first test fails because binary floating-point numbers cannot represent 0.1 or 0.2 exactly, and their sum is `0.30000000000000004`. Never compare computed decimals with `toBe`; use `toBeCloseTo`. In real Jest and Vitest, `expect.extend` takes functions that return `{ pass, message }`, and the wrapping, including `.not`, is done for you as it is here.

## Reading a failure

A failing comparison prints a **diff**: the expected and the received value side by side, with markers on the lines that differ.

```text
 FAIL  cart.test.js > cart > totals the prices
AssertionError: expected { total: 9, items: 2 } to deeply equal { total: 10, items: 2 }

- Expected
+ Received

  {
    "items": 2,
-   "total": 10,
+   "total": 9,
  }

 ❯ cart.test.js:14:26
```

Read it in this order: the test's full name (file, suite, test), the one-line summary, the lines marked `-` (what the test asked for) and `+` (what the code produced), and last the file and line of the assertion. Nine times out of ten the diff alone tells you what went wrong.

## Many cases, one test body

When the same check applies to many inputs, write the cases as rows of a table. Each row becomes its own test with its own name, so a failure names the row.

```javascript
test.each([
  [2024, true],
  [2023, false],
  [1900, false],
  [2000, true],
])("isLeapYear(%i) is %s", (year, expected) => {
  expect(isLeapYear(year)).toBe(expected);
});
```

`%i` and `%s` in the name are filled in from the row. `node:test` has no `each`; an ordinary `for` loop around `test(...)` does the same job. The block below implements `test.each` in a few lines and runs it against a leap-year function with a bug. Run it, read which row fails, and fix the function (a year divisible by 100 is a leap year only if it is also divisible by 400).

```js-run
function test(name, fn) {
  try { fn(); console.log("PASS  " + name); }
  catch (e) { console.log("FAIL  " + name + "\n      -> " + e.message); }
}
test.each = (rows) => (nameTemplate, fn) => {
  for (const row of rows) {
    let i = 0;
    const name = nameTemplate.replace(/%s/g, () => String(row[i++]));   // fill the placeholders in order
    test(name, () => fn(...row));
  }
};
function expectEqual(actual, expected) {
  if (actual !== expected) throw new Error("expected " + expected + " but got " + actual);
}

function isLeapYear(year) {
  return year % 4 === 0;                       // incomplete rule
}

test.each([
  [2024, true],
  [2023, false],
  [1900, false],
  [2000, true],
])("isLeapYear(%s) is %s", (year, expected) => {
  expectEqual(isLeapYear(year), expected);
});
```

## Hooks and where they apply

All three runners provide `beforeEach`, `afterEach`, `beforeAll` and `afterAll` (`before` and `after` in `node:test`). A hook applies to the `describe` block it is written in and to every block nested inside it.

```javascript
describe("basket", () => {
  let basket;
  beforeEach(() => { basket = createBasket(); });          // runs before every test below

  describe("with a discount code", () => {
    beforeEach(() => { basket.apply("SPRING10"); });       // runs second, only for tests in this block
    test("reduces the total by ten percent", () => { /* ... */ });
  });
});
```

For setup needed by every file, such as registering extra matchers or resetting doubles, use a **setup file**: a module the runner executes before each test file. In Vitest it is listed under `setupFiles`, in Jest under `setupFilesAfterEnv`.

## Configuration you will actually touch

```javascript
// vitest.config.js
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",                 // or "jsdom" / "happy-dom" for DOM tests
    setupFiles: ["./test/setup.js"],     // runs before every test file
    restoreMocks: true,                  // undo spies automatically after each test
    coverage: {
      provider: "v8",
      thresholds: { lines: 80, branches: 75 },
    },
  },
});
```

```javascript
// jest.config.mjs
export default {
  testEnvironment: "node",               // "jsdom" needs the jest-environment-jsdom package
  setupFilesAfterEnv: ["./test/setup.js"],
  restoreMocks: true,
  coverageThreshold: { global: { lines: 80, branches: 75 } },
};
```

A single file can ask for a different environment with a comment on its first line: `// @vitest-environment jsdom` or `/** @jest-environment jsdom */`. That keeps fast Node tests fast while a few files get a simulated DOM.

Two facts about how the runners execute tests explain many surprises:

- **Files run in parallel; tests inside one file run one after another.** Each file gets its own fresh module state, so two files cannot disturb each other's variables, but they *can* collide on anything outside the process: a shared database, a fixed port, a file on disk.
- **Jest transforms code before running it.** Out of the box Jest runs CommonJS; ES module syntax and TypeScript are converted by a transformer such as Babel. A project that mixes module systems is the usual cause of Jest errors like "Cannot use import statement outside a module". Vitest reuses Vite's pipeline, which handles ES modules and TypeScript directly.

## Snapshots

A **snapshot test** saves the output of some code in a file the first time it runs, and on later runs compares the new output with the saved copy.

```javascript
test("renders the receipt", () => {
  expect(formatReceipt(order)).toMatchSnapshot();          // stored in __snapshots__/receipt.test.js.snap
});
```

When the output changes, the test fails and shows the difference. If the change was intended, you accept the new output with `npx vitest run -u` or `npx jest -u`, and commit the updated snapshot file. The block below is a snapshot mechanism in miniature.

```js-run
const store = {};                                        // real runners keep this in a .snap file

function matchSnapshot(name, value) {
  const text = JSON.stringify(value, null, 2);
  if (!(name in store)) { store[name] = text; return "snapshot written"; }
  if (store[name] === text) return "matches the snapshot";
  throw new Error("does not match the snapshot\n--- saved ---\n" + store[name] + "\n--- now ---\n" + text);
}
function check(label, name, value) {
  try { console.log(label + ": " + matchSnapshot(name, value)); }
  catch (e) { console.log(label + ": FAIL " + e.message); }
}

let formatReceipt = (order) => ({ lines: order.items.length, total: order.items.reduce((sum, i) => sum + i.price, 0) });
const order = { items: [{ name: "tea", price: 4 }, { name: "mug", price: 6 }] };

check("run 1", "receipt", formatReceipt(order));         // nothing saved yet: written
check("run 2", "receipt", formatReceipt(order));         // same output: passes

formatReceipt = (order) => ({ lines: order.items.length, total: order.items.reduce((sum, i) => sum + i.price, 0), currency: "SGD" });
check("run 3", "receipt", formatReceipt(order));         // the output changed: fails and shows both
```

Notice what "run 1" did: it passed without anyone deciding what the right output is. A snapshot records what the code *does*, not what it *should* do. That makes snapshots useful as a tripwire for accidental changes in something already reviewed by eye, and risky as a replacement for thinking. Keep them small, read every snapshot difference before accepting it, and prefer an explicit assertion whenever you can state the expected value. An **inline snapshot** (`toMatchInlineSnapshot()`) writes the saved value into the test file itself, where reviewers see it.

## Moving between runners

Because Vitest copied Jest's interface, moving a suite from Jest to Vitest is mostly mechanical: add the import line (or set `globals: true`), replace `jest.` with `vi.`, move the configuration, and check the handful of differences, such as module-mock factories needing an explicit `default` key for default exports. Moving to `node:test` is a bigger step, because assertions and doubles are spelled differently, so it suits small libraries and services more than a large application suite.

How teams usually choose:

- A project built with Vite, or a new front-end or TypeScript project: **Vitest**, for the shared configuration and speed.
- An existing codebase that already has thousands of Jest tests, or React Native: **Jest**. Migration has a cost and brings no new behaviour.
- A small library or back-end service that wants no development dependencies at all: **`node:test`**.

> [!TIP]
> Learn your runner's watch mode on day one. In Vitest and Jest, pressing a key in the watching terminal filters by file name or test name, re-runs only failures, or updates snapshots. Most people who find tests slow are running the whole suite by hand after each change.

> [!INTERVIEW]
> **"Your team's test suite takes eight minutes. What do you look at?"** Start by measuring: the runner's slowest-test report shows where the time goes. Typical causes are real waiting (sleeps, real timers, real network) that fake timers and doubles remove; expensive setup repeated in `beforeEach` that could be cheaper or shared safely; DOM environments loaded for files that only need Node; and running serially when files could run in parallel. Then the workflow: run only affected tests while developing, the whole suite in CI, split across machines if it is still slow. End with the guard: speed-ups must not cost isolation, or the suite turns flaky.

## Common pitfalls

- **Running watch mode in CI.** `vitest` with no arguments waits for file changes. Use `vitest run`.
- **Committing `.only` or leaving `.skip` behind.** One silently drops tests; the other hides them for ever.
- **Comparing decimals with `toBe`.** Use `toBeCloseTo`, or do money arithmetic in whole cents.
- **`toEqual` when you mean identity, or `toBe` on objects.** `toBe` on two separately built objects always fails; `toEqual` passes for any two objects with equal contents.
- **`expect(list.includes(x)).toBe(true)`.** It works, but the failure message is useless. Use `toContain`.
- **Blindly updating snapshots.** `-u` accepts every difference, including the bug.
- **Forgetting `await` on `resolves` / `rejects`.** The matcher returns a promise.
- **Shared outside resources between parallel files.** A fixed port or a shared database row makes files fail only when run together.
- **Assuming Jest's globals exist in Vitest.** Import them, or switch on `globals: true`.

## Cheat sheet

| Task | Vitest | Jest | `node:test` |
|---|---|---|---|
| Group | `describe("x", fn)` | same | `describe("x", fn)` |
| Case | `test("x", fn)` / `it` | same | `test("x", fn)` / `it` |
| Table of cases | `test.each(rows)(name, fn)` | same | `for (const row of rows) test(...)` |
| Skip / focus / to-do | `test.skip`, `test.only`, `test.todo` | same | `{ skip: true }`, `{ only: true }`, `{ todo: true }` |
| Per-test timeout | `test(name, fn, 10000)` | same | `test(name, { timeout: 10000 }, fn)` |
| Recording function | `vi.fn()` | `jest.fn()` | `mock.fn()` |
| Spy on a method | `vi.spyOn(obj, "m")` | `jest.spyOn(obj, "m")` | `mock.method(obj, "m")` |
| Fake timers | `vi.useFakeTimers()` | `jest.useFakeTimers()` | `mock.timers.enable()` |
| Update snapshots | `vitest run -u` | `jest -u` | not covered here |
| Coverage | `vitest run --coverage` | `jest --coverage` | `node --test --experimental-test-coverage` |
| Machine-readable report | `--reporter=junit` | `--reporters=jest-junit` (package) | `--test-reporter=junit` |

## Summary

- Vitest, Jest and `node:test` share the same building blocks; they differ in installation, imports, assertion style and how they handle ES modules and TypeScript.
- Test files are found by name. Learn the commands to run one file, one test by name, and watch mode.
- Matchers are small predicate functions wrapped to throw readable errors; pick the specific matcher for a clearer failure, and `toBeCloseTo` for decimals.
- Read a failure top down: full test name, summary, diff, line number.
- `test.each` turns a table of cases into individually named tests.
- Hooks apply to their `describe` block and nested blocks; setup files apply to every file.
- Files run in parallel with separate module state; anything outside the process is still shared.
- A snapshot records current output. Keep snapshots small and read every difference before accepting it.

## Glossary

- **Global**: a name available in every file without an import.
- **Matcher**: a method on `expect(value)` that checks one kind of fact and throws when it does not hold.
- **Asymmetric matcher**: a placeholder such as `expect.any(Number)` that accepts a class of values inside a comparison.
- **Diff**: a line-by-line display of the differences between expected and received values.
- **Watch mode**: a runner staying open and re-running tests when files change.
- **Setup file**: a module the runner executes before each test file.
- **Environment**: the set of globals a test file runs with, such as plain Node or a simulated DOM.
- **Transform**: a step that converts source code (TypeScript, newer syntax, another module format) into code the runtime can execute.
- **Snapshot test**: a test that compares output with a previously saved copy.
- **Inline snapshot**: a snapshot stored inside the test file.
- **`npx`**: a command that runs a program from the project's installed npm packages.
- **Reporter**: the part of a runner that formats results, for people or for other tools.

## Check yourself

```quiz
[
  {"q": "expect(0.1 + 0.2).toBe(0.3) in Vitest or Jest. Pass or fail, and what should be used?",
   "options": ["Pass", "Fail, because the sum is 0.30000000000000004; use toBeCloseTo(0.3)", "Fail; use toEqual(0.3)", "It throws a TypeError"],
   "answer": 1,
   "explain": "Binary floating point cannot represent these decimals exactly. toEqual on numbers behaves like toBe; toBeCloseTo compares within a tolerance."},
  {"q": "A Jest test file is copied unchanged into a Vitest project with default settings. It uses describe, test and expect without imports. What happens?",
   "options": ["It runs", "It fails with 'describe is not defined' unless the functions are imported from vitest or globals: true is set", "Vitest converts it automatically", "Only expect is missing"],
   "answer": 1,
   "explain": "Jest injects these names as globals. Vitest expects an import by default and offers a globals option for compatibility."},
  {"q": "A snapshot test is run for the first time on a function that already has a bug. What is the result?",
   "options": ["It fails and shows the bug", "It passes and stores the buggy output as the reference", "It is skipped", "It asks for confirmation"],
   "answer": 1,
   "explain": "The first run writes whatever the code produces. A snapshot detects change, not correctness, so the initial output must be reviewed by a person."},
  {"q": "test.each([[2024, true], [1900, false]])('isLeapYear(%i) is %s', fn). The second row fails. How does it appear in the report?",
   "options": ["As one failed test named with the template", "As a failed test named 'isLeapYear(1900) is false', separate from the passing row", "The whole table is reported as one failure", "Rows after a failure are not run"],
   "answer": 1,
   "explain": "Each row becomes its own test with the placeholders filled in, so the report names the exact failing case and the other rows still run."},
  {"q": "Two test files both start a server on port 3000. Each passes alone; run together, one fails. Why?",
   "options": ["Runners execute files in parallel, and although each file has its own module state, the port is a resource outside the process that both try to use", "describe blocks cannot be nested", "Ports reset between tests", "Jest forbids servers"],
   "answer": 0,
   "explain": "Isolation between files covers JavaScript state, not the operating system. Use port 0, per-file databases or unique temporary folders."},
  {"q": "Which assertion gives the most helpful failure message when 'coffee' is missing from an array?",
   "options": ["expect(list.includes('coffee')).toBe(true)", "expect(list).toContain('coffee')", "expect(list.indexOf('coffee') >= 0).toBeTruthy()", "expect(!!list.find((x) => x === 'coffee')).toBe(true)"],
   "answer": 1,
   "explain": "toContain reports the array and the missing item. The others reduce the check to a boolean first, so the message can only say expected true, received false."},
  {"q": "Where does a beforeEach written inside describe('with a discount code', ...) run?",
   "options": ["Before every test in the file", "Before each test inside that describe block and blocks nested in it, after any outer beforeEach", "Once per file", "Only before the first test"],
   "answer": 1,
   "explain": "Hooks are scoped to their block. Outer hooks run first, then inner ones, before each test in the inner block."},
  {"q": "A CI job's command is 'npx vitest'. What is wrong?",
   "options": ["Nothing", "Without 'run' Vitest may stay in watch mode waiting for file changes; CI should use 'vitest run'", "npx is not available in CI", "It skips coverage only"],
   "answer": 1,
   "explain": "The run subcommand executes once and exits with a status code CI can act on."}
]
```

> **Source:** Johansen, *Test-Driven JavaScript Development*, ch. 3 (Tools of the Trade), brought up to date. Docs: https://vitest.dev/guide/ , https://vitest.dev/config/ , https://vitest.dev/api/expect.html , https://jestjs.io/docs/getting-started , https://jestjs.io/docs/configuration , https://jestjs.io/docs/snapshot-testing , https://nodejs.org/api/test.html , https://nodejs.org/api/assert.html
