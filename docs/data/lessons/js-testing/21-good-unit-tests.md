# Writing good unit tests: names, focus and test smells

> **Before this lesson:** you can write tests with setup, action and assertion ([Why automate tests: your first unit test](#/lesson/js-testing/first-unit-test)), share setup safely ([Setup, teardown, suites and integration tests](#/lesson/js-testing/setup-suites-integration)) and choose between stubs, spies, mocks and fakes ([Test doubles in depth: dummies, stubs, spies, mocks and fakes](#/lesson/js-testing/test-doubles)). This lesson is about quality: what separates a test suite people rely on from one they learn to ignore.

## In plain words

Writing a test that passes is the easy part. A test earns its keep later, on the day it fails. On that day somebody, often not the author and often in a hurry, reads the failure and has to decide: is the code broken, or is the test wrong? A good test answers in seconds. A bad one costs an afternoon, and after a few such afternoons the team stops trusting the suite.

Think of a smoke alarm. A good one goes off when there is a fire and stays quiet when you make toast. It is also wired so that the panel shows which room. An alarm that shrieks at toast gets its battery pulled out. An alarm that sleeps through a real fire is worse than none, because people feel safe. Tests fail in the same two ways: they go red when nothing is wrong (false alarms), or they stay green when something is (missed fires).

Why it matters for a job: in code review, tests get reviewed like any other code, and "what makes a good unit test?" is a standard interview question. More practically, a team's speed depends on whether a green run means "safe to ship". That is a property of how the tests were written, not of how many there are.

## Three readers of every test

A test has three audiences, and they want different things.

1. **The runner** wants a function that throws when the behaviour is wrong. This is the only reader that most beginner tests are written for.
2. **The person whose change turned it red** wants to know, from the failure report alone, which behaviour broke and how.
3. **The future maintainer** wants to learn what the code is supposed to do by reading the tests as a list of facts. Tests are the only documentation that is checked on every run.

Everything below serves readers two and three.

## Names that state a behaviour

A test name is the headline of its failure report. Compare two reports for the same two bugs:

```text
FAIL  test 3                                    FAIL  deposit rejects an amount of zero
FAIL  withdraw works                            FAIL  withdraw rejects a negative amount
```

The right-hand column tells you what is broken before you open any file. A useful recipe is **subject, expected behaviour, condition**: *withdraw* / *rejects* / *a negative amount*. Write the name so that it is false whenever the test fails.

| Weak name | Why it is weak | Better |
|---|---|---|
| `test1` | Says nothing | `a new account has a balance of zero` |
| `withdraw works` | "Works" is not a behaviour | `withdraw lowers the balance by the amount` |
| `should handle errors correctly` | Which errors, handled how? | `withdraw rejects an amount above the balance` |
| `calls validate then save` | Describes the implementation | `a valid form is saved` |
| `bug 4123` | Needs a ticket system to decode | `names with an apostrophe are accepted` (mention the ticket in a comment) |

Early frameworks found tests by method name, so every test had to be a legal identifier beginning with `test`, and names were squeezed into forms like `testWithdrawNegative`. Runners now take a string, so write a sentence. Group related tests under a `describe` block named after the unit or the situation, so the report scans well:

```text
account
  when empty
    ✓ has a balance of zero
    ✓ rejects any withdrawal
  with money in it
    ✓ withdraw lowers the balance by the amount
```

## A visible shape: arrange, act, assert

Every test has the same three parts, and a reader should find them at a glance. Separate them with blank lines.

```javascript
test("withdraw lowers the balance by the amount", () => {
  const account = createAccount(100);        // arrange: the starting situation

  account.withdraw(30);                      // act: the one thing being tested

  expect(account.balance()).toBe(70);        // assert: the outcome
});
```

The same idea is also described as setup, exercise, verify. If the "act" part has several unrelated calls, the test is probably about more than one behaviour.

## One behaviour per test

The rule is one *behaviour*, not one assertion. Several assertions that together describe a single outcome belong in one test: after adding an item, the list has length 1 **and** its first entry has the right name. What should not share a test is several *independent* behaviours, because a runner stops a test at its first failed assertion and everything after it goes unreported.

The code below has two bugs. Run it and compare how much the two styles tell you.

```js-run
// --- the tiny test runner from lesson 1 ---
function test(name, fn) {
  try { fn(); console.log("PASS  " + name); }
  catch (e) { console.log("FAIL  " + name + "\n      -> " + e.message); }
}
function expect(actual) {
  const show = (v) => typeof v === "function" ? "[function]" : JSON.stringify(v);
  const fail = (msg) => { throw new Error(msg); };
  return {
    toBe(expected) {
      if (!Object.is(actual, expected)) fail("expected " + show(expected) + " but got " + show(actual));
    },
    toEqual(expected) {
      if (JSON.stringify(actual) !== JSON.stringify(expected)) fail("expected " + show(expected) + " but got " + show(actual));
    },
    toThrow(text = "") {
      try { actual(); } catch (e) {
        if (!String(e.message).includes(text)) fail("threw the wrong error: " + e.message);
        return;
      }
      fail("expected the function to throw, but it returned normally");
    },
  };
}
// --- end of runner ---

function createAccount(balance = 0) {
  return {
    balance: () => balance,
    deposit(amount) {
      if (amount < 0) throw new Error("amount must be positive");          // bug 1: zero slips through
      balance += amount;
    },
    withdraw(amount) {
      if (amount > balance) throw new Error("insufficient funds");         // bug 2: negative amounts slip through
      balance -= amount;
    },
  };
}

console.log("--- style A: one giant test");
test("account works", () => {
  const account = createAccount();
  account.deposit(100);
  expect(account.balance()).toBe(100);
  account.withdraw(30);
  expect(account.balance()).toBe(70);
  expect(() => account.withdraw(500)).toThrow("insufficient funds");
  expect(() => account.deposit(0)).toThrow("amount must be positive");
  expect(() => account.withdraw(-5)).toThrow("amount must be positive");
});

console.log("--- style B: one behaviour per test");
test("deposit raises the balance by the amount", () => {
  const account = createAccount();
  account.deposit(100);
  expect(account.balance()).toBe(100);
});
test("withdraw lowers the balance by the amount", () => {
  const account = createAccount(100);
  account.withdraw(30);
  expect(account.balance()).toBe(70);
});
test("withdraw rejects an amount above the balance", () => {
  expect(() => createAccount(100).withdraw(500)).toThrow("insufficient funds");
});
test("deposit rejects an amount of zero", () => {
  expect(() => createAccount().deposit(0)).toThrow("amount must be positive");
});
test("withdraw rejects a negative amount", () => {
  expect(() => createAccount(100).withdraw(-5)).toThrow("amount must be positive");
});
```

Style A reports one vague failure and hides the second bug until the first is fixed. Style B reports both bugs by name and shows that three other behaviours are fine. Style B also starts each test from a known state; in style A the withdrawal check silently depends on the deposit before it. A test that checks many things in sequence has a name in the catalogue of test problems: an **eager test**.

## Test each behaviour once

The mirror-image mistake is checking the same behaviour in many tests. Suppose "blank names are rejected" is asserted in the model's tests, again in the controller's tests, and again in three DOM tests. When that rule changes, five tests fail for one reason and five have to be edited. The specification gained nothing from the four repeats.

Decide which layer owns a behaviour and test it there. The model owns validation rules. The controller's tests then need a single case showing that *a rejection from the model is displayed*, using a stub that rejects; they do not need one case per rule.

## Helpers that raise the level, without hiding the story

As a suite grows, the same ten lines of setup appear in test after test. Extracting them is good, up to a point. The measure is whether each test can still be understood without scrolling.

Two kinds of helper pay off again and again.

**A test data builder** creates a valid object with sensible defaults and lets each test override only what matters to it. The override then stands out as the point of the test.

```js-run
// --- the tiny test runner from lesson 1 ---
function test(name, fn) {
  try { fn(); console.log("PASS  " + name); }
  catch (e) { console.log("FAIL  " + name + "\n      -> " + e.message); }
}
function expect(actual) {
  const show = (v) => typeof v === "function" ? "[function]" : JSON.stringify(v);
  const fail = (msg) => { throw new Error(msg); };
  return {
    toBe(expected) {
      if (!Object.is(actual, expected)) fail("expected " + show(expected) + " but got " + show(actual));
    },
    toEqual(expected) {
      if (JSON.stringify(actual) !== JSON.stringify(expected)) fail("expected " + show(expected) + " but got " + show(actual));
    },
    toThrow(text = "") {
      try { actual(); } catch (e) {
        if (!String(e.message).includes(text)) fail("threw the wrong error: " + e.message);
        return;
      }
      fail("expected the function to throw, but it returned normally");
    },
  };
}
// --- end of runner ---

// ---------- code under test ----------
function shippingCost(order) {
  const base = order.country === "SG" ? 4 : 12;
  if (order.express) return base * 2;
  return order.quantity * order.unitPrice >= 50 ? 0 : base;
}

// ---------- a test data builder ----------
function anOrder(overrides = {}) {
  return { id: 1, item: "socks", quantity: 1, unitPrice: 5, country: "SG", express: false, ...overrides };
}

test("a small local order pays the local rate", () => {
  expect(shippingCost(anOrder())).toBe(4);
});
test("an order sent abroad pays the international rate", () => {
  expect(shippingCost(anOrder({ country: "JP" }))).toBe(12);
});
test("a standard order worth 50 or more ships free", () => {
  expect(shippingCost(anOrder({ quantity: 10 }))).toBe(0);
});
test("express doubles the rate", () => {
  expect(shippingCost(anOrder({ express: true }))).toBe(8);
});
test("express is never free, whatever the order is worth", () => {
  expect(shippingCost(anOrder({ express: true, quantity: 10 }))).toBe(8);
});
```

Without the builder each test would spell out six properties, five of them irrelevant, and the reader would have to hunt for the one that differs.

**A custom assertion** gives a name to a check that needs several lines, and produces a better message:

```javascript
function expectRejectedWith(result, reason) {
  if (result.ok) throw new Error("expected the order to be rejected, but it was accepted");
  if (result.reason !== reason) throw new Error("expected rejection for: " + reason + ", but got: " + result.reason);
}
```

In Jest and Vitest, `expect.extend({ ... })` registers such a check as a matcher of your own.

The limit: production code is kept free of repetition, the principle known as **DRY** (do not repeat yourself). Tests have a different first duty, which is to be readable one at a time. Some repetition is fine when it keeps the cause and the effect of each test visible together. A test whose important input is hidden in a far-away `beforeEach` or a shared fixture file suffers from the **mystery guest** problem: the reader cannot see why `8` is the expected answer.

## No logic in tests

A test should be a straight line: values in, call, compare with a **literal** expected value. As soon as a test contains a loop, an `if` or a calculation, it can contain a bug, and nothing tests the tests.

The most tempting form of logic is computing the expected value. Look at what happens when the test uses the same formula as the code:

```js-run
// --- the tiny test runner from lesson 1 ---
function test(name, fn) {
  try { fn(); console.log("PASS  " + name); }
  catch (e) { console.log("FAIL  " + name + "\n      -> " + e.message); }
}
function expect(actual) {
  const show = (v) => typeof v === "function" ? "[function]" : JSON.stringify(v);
  const fail = (msg) => { throw new Error(msg); };
  return {
    toBe(expected) {
      if (!Object.is(actual, expected)) fail("expected " + show(expected) + " but got " + show(actual));
    },
    toEqual(expected) {
      if (JSON.stringify(actual) !== JSON.stringify(expected)) fail("expected " + show(expected) + " but got " + show(actual));
    },
    toThrow(text = "") {
      try { actual(); } catch (e) {
        if (!String(e.message).includes(text)) fail("threw the wrong error: " + e.message);
        return;
      }
      fail("expected the function to throw, but it returned normally");
    },
  };
}
// --- end of runner ---

function priceWithTax(net, ratePercent) {
  return net + net * ratePercent / 10;            // bug: should divide by 100
}

test("mirrors the implementation (passes, proves nothing)", () => {
  const net = 200, rate = 8;
  expect(priceWithTax(net, rate)).toBe(net + net * rate / 10);
});

test("states the answer worked out by hand", () => {
  expect(priceWithTax(200, 8)).toBe(216);
});
```

The first test repeats the bug and is satisfied. The second states a fact someone worked out independently: 8% of 200 is 16. Expected values should come from the requirement, not from the code.

A second trap is an assertion that sits inside a loop or condition which may never execute:

```js-run
// --- the tiny test runner from lesson 1 ---
function test(name, fn) {
  try { fn(); console.log("PASS  " + name); }
  catch (e) { console.log("FAIL  " + name + "\n      -> " + e.message); }
}
function expect(actual) {
  const show = (v) => typeof v === "function" ? "[function]" : JSON.stringify(v);
  const fail = (msg) => { throw new Error(msg); };
  return {
    toBe(expected) {
      if (!Object.is(actual, expected)) fail("expected " + show(expected) + " but got " + show(actual));
    },
    toEqual(expected) {
      if (JSON.stringify(actual) !== JSON.stringify(expected)) fail("expected " + show(expected) + " but got " + show(actual));
    },
    toThrow(text = "") {
      try { actual(); } catch (e) {
        if (!String(e.message).includes(text)) fail("threw the wrong error: " + e.message);
        return;
      }
      fail("expected the function to throw, but it returned normally");
    },
  };
}
// --- end of runner ---

const INVOICES = [
  { id: 1, due: 10, paid: false },
  { id: 2, due: 15, paid: true },
  { id: 3, due: 40, paid: false },
];
function overdueUnpaid(invoices, today) {
  return [];                                      // broken: always returns nothing
}

test("every result is unpaid (cannot fail on an empty result)", () => {
  for (const invoice of overdueUnpaid(INVOICES, 20)) {
    expect(invoice.paid).toBe(false);
  }
});

test("returns exactly the unpaid invoices that are past due", () => {
  expect(overdueUnpaid(INVOICES, 20).map((i) => i.id)).toEqual([1]);
});
```

With a broken function that returns an empty list, the loop body never runs, no assertion executes and the first test passes. The second compares against the full expected answer and fails as it should. A test that passes without checking anything is sometimes called **the liar**.

## Isolation: each test stands alone

A test is **isolated** when its result depends only on its own lines: not on which tests ran before it, not on the time of day, not on the network. The quickest check is to ask whether the tests would pass in a different order.

```js-run
// --- the tiny test runner from lesson 1 ---
function test(name, fn) {
  try { fn(); console.log("PASS  " + name); }
  catch (e) { console.log("FAIL  " + name + "\n      -> " + e.message); }
}
function expect(actual) {
  const show = (v) => typeof v === "function" ? "[function]" : JSON.stringify(v);
  const fail = (msg) => { throw new Error(msg); };
  return {
    toBe(expected) {
      if (!Object.is(actual, expected)) fail("expected " + show(expected) + " but got " + show(actual));
    },
    toEqual(expected) {
      if (JSON.stringify(actual) !== JSON.stringify(expected)) fail("expected " + show(expected) + " but got " + show(actual));
    },
    toThrow(text = "") {
      try { actual(); } catch (e) {
        if (!String(e.message).includes(text)) fail("threw the wrong error: " + e.message);
        return;
      }
      fail("expected the function to throw, but it returned normally");
    },
  };
}
// --- end of runner ---

function run(title, order, tests, reset) {
  console.log("--- " + title + ": " + order.join(" then "));
  reset();
  for (const name of order) test(name, tests[name]);
}

// shared state: one cart for all tests
let cart = [];
const sharedTests = {
  "a new cart is empty": () => { expect(cart.length).toBe(0); },
  "adding an item gives a cart of one": () => { cart.push("tea"); expect(cart.length).toBe(1); },
};
run("shared cart", ["a new cart is empty", "adding an item gives a cart of one"], sharedTests, () => { cart = []; });
run("shared cart", ["adding an item gives a cart of one", "a new cart is empty"], sharedTests, () => { cart = []; });

// isolated: every test builds its own cart
const isolatedTests = {
  "a new cart is empty": () => { const own = []; expect(own.length).toBe(0); },
  "adding an item gives a cart of one": () => { const own = []; own.push("tea"); expect(own.length).toBe(1); },
};
run("own cart", ["adding an item gives a cart of one", "a new cart is empty"], isolatedTests, () => {});
```

The shared version passes in one order and fails in the other, and nothing in the failing test is wrong. Order-dependent tests are a major source of failures that appear "at random", especially when a runner executes test files in parallel. Runners can shuffle the order on purpose to flush such tests out (for example `vitest --sequence.shuffle` or `jest --randomize`).

Isolation from slow or unpredictable collaborators is what test doubles are for. But doubles are not the only route. A collaborator that is fast, deterministic and already has its own tests can be used for real: a formatting function, an in-memory collection, an already-tested observable. Using it turns the test into a small integration test, which is fine, and it lets you assert on outcomes without having to assert on calls.

## Brittle tests: when green code turns the suite red

A **brittle test** fails after a change that altered no behaviour. Each such failure teaches the team that red does not mean broken. The usual causes:

- **Reaching into private details.** `expect(cart._items[0])` breaks when the internal array is renamed. Go through the public interface: `expect(cart.items()[0])`.
- **Asserting on how, not what.** Checking that `sort` was called, when the requirement is that the output is sorted.
- **Over-specified comparisons.** Comparing a whole object when the test is about one field, or a full error message when one phrase identifies it. Prefer `toMatchObject({ status: "paid" })` and `toThrow("insufficient")`.
- **Large snapshots.** A **snapshot test** stores a function's whole output in a file and fails on any difference. On a big structure almost every change trips it, and people get used to regenerating the file without reading the difference. Keep snapshots small, or assert on the specific values.
- **Dependence on things outside the test:** today's date, the machine's time zone or language settings, the order of keys in an object, random numbers.

The question to ask of every assertion: *would this still pass if the code were restructured without changing what its callers get?*

## Finding bugs in the tests themselves

Nobody writes tests for tests. Four habits take their place.

1. **Watch each test fail before it passes.** In test-driven development that happens naturally: the test is written first and is red for a known reason. For a test written afterwards, break the code on purpose (or the assertion) and check that the test goes red with a sensible message. A test you have never seen fail is unproven.
2. **Check the reason for the failure.** A red test that fails with `createAccount is not defined` because of a typo in the test has not yet shown that it can detect the behaviour.
3. **Attack the code.** With all tests green, change the production code in small ways and run the suite: flip a `<` to `<=`, replace a condition with `true`, delete a line, return early, change a number by one. Every change that leaves the suite green marks a behaviour nobody is checking, or code that does nothing. Doing this systematically with a tool is called **mutation testing**, covered in [Coverage, mutation testing and tests in CI](#/lesson/js-testing/coverage-mutation-ci).
4. **Let a linter catch the mechanical mistakes.** A **linter** is a program that scans source code for suspicious patterns without running it. ESLint has plugins for test code that flag a committed `test.only`, a test with no assertion, two tests with the same name, and a promise that is neither awaited nor returned.

## A short catalogue of test smells

A **test smell** is a recognisable sign that a test will cause trouble. Many of the names come from Meszaros's *xUnit Test Patterns*.

| Smell | Symptom | Cure |
|---|---|---|
| Eager test | One test checks many behaviours in a row | Split into one test per behaviour |
| Assertion roulette | Many bare assertions; the report does not say which one failed or why | Fewer assertions per test, clearer names, custom assertions with messages |
| Mystery guest | The expected value depends on data defined far away | Bring the relevant data into the test, or use a builder with visible overrides |
| Conditional test logic | `if`, loops or calculations in a test | Literal inputs and expected values; table-driven tests for many cases |
| Fragile test | Breaks on refactoring | Assert on outcomes through the public interface |
| The liar | Passes without checking anything | See it fail; require assertions (`expect.hasAssertions()`) |
| Interacting tests | Pass alone, fail together, or the reverse | Fresh fixture per test; no shared mutable state |
| Slow test | Sleeps, real network, real disk | Fake clock, doubles, move to an integration suite |
| Flaky test | Sometimes red with no change | Remove real time, randomness, order dependence, shared state |
| Excessive setup | Thirty lines of arrangement before one call | Builders and helpers; often also a sign that the code under test does too much |
| Testing the double | Assertions only confirm what a stub was told to return | Let real logic run; double only the edges |

## The FIRST checklist

A common summary of unit-test quality is the acronym **FIRST**:

- **Fast**: milliseconds each, so the whole suite runs on every save.
- **Isolated**: no dependence on other tests or on shared state.
- **Repeatable**: the same result on any machine, at any time, in any order.
- **Self-validating**: the test itself decides pass or fail; nobody inspects output by eye.
- **Timely**: written close to the code, ideally before it.

> [!TIP]
> When a test is hard to write, the code is usually telling you something. Needing eight collaborators to call one function, or a page of setup to reach one branch, points at a function that does too much or reaches too far. Listen to that before you reach for more helpers.

> [!WARNING]
> Never "fix" a failing test by loosening it until it passes, or by deleting the assertion, without first understanding why it failed. Either the code broke a requirement, or the requirement changed and the test must change with it on purpose. A third outcome, "the test was always wrong", should lead to a better test, not a weaker one.

> [!INTERVIEW]
> **"What makes a good unit test?"** Give the structure first: a name that states one behaviour, an arrange / act / assert body, a literal expected value. Then the properties: fast, isolated from other tests and from time and network, repeatable, and failing for exactly one reason. Then show judgement: it asserts on observable outcomes through the public interface and so survives refactoring; it uses doubles only at the edges; and you have seen it fail. Finish with what you look for in review: tests that cannot fail, logic in tests, shared mutable fixtures and over-specified assertions.

## Common pitfalls

- **Naming tests after methods.** `add`, `add 2`, `add edge case` tell the reader nothing. Name the behaviour.
- **One assertion per test as a dogma.** The unit is the behaviour. Splitting one outcome over five tests adds noise.
- **Extracting so much that tests become riddles.** A test consisting of `setupScenario7(); verifyAll();` cannot be read.
- **Expected values copied from the current output.** That records what the code does, not what it should do. Work the answer out independently.
- **Commented-out or skipped tests left to rot.** A skipped test protects nothing and misleads readers. Fix it or delete it.
- **Catching an exception in the test and forgetting to fail.** `try { act(); } catch (e) { expect(e.message)... }` passes when nothing is thrown.
- **Testing private functions directly.** Their behaviour is reachable through the public one. If it is too awkward to reach, the private part may deserve to be a unit of its own.
- **Treating a flaky test as background noise.** Re-running until green hides a real defect in the test or in the code.

## Cheat sheet

| Goal | Practice |
|---|---|
| Readable report | Name = subject + behaviour + condition; group with `describe` |
| Visible structure | Blank lines between arrange, act and assert |
| Precise failures | One behaviour per test; literal expected values |
| Many similar cases | `test.each([[input, expected], ...])("name %s", (input, expected) => ...)` |
| Less noise in setup | Test data builders with overrides |
| Better messages | Custom assertions, `expect.extend` |
| No vacuous passes | `expect.hasAssertions()`, `expect.assertions(n)` |
| Catch order dependence | `vitest --sequence.shuffle`, `jest --randomize` |
| Refactor-proof assertions | `toMatchObject`, `expect.objectContaining`, `toThrow("phrase")` |
| Prove a test can fail | Break the code on purpose and watch it go red |
| Mechanical mistakes | ESLint with a test plugin: no focused tests, no missing assertions, no floating promises |

## Summary

- Tests are read at the moment they fail; write them for that reader.
- A name states one behaviour and its condition, and the body shows arrange, act and assert.
- One behaviour per test gives precise reports; each behaviour is tested once, in the layer that owns it.
- Builders and custom assertions remove noise, but each test must still tell its own story.
- Keep logic out of tests: literal expected values, no loops or conditions around assertions.
- Isolate tests from each other and from time, randomness and the network.
- Brittle tests come from asserting on implementation details; assert on outcomes.
- Prove a test by watching it fail, attack the code to find gaps, and let a linter catch mechanical errors.

## Glossary

- **Arrange, act, assert**: the three parts of a test: build the situation, do the one thing, check the outcome.
- **Eager test**: a test that checks several independent behaviours.
- **Test data builder**: a helper that returns a valid object with defaults and accepts overrides.
- **Custom assertion**: a named helper that performs a check and gives a clear failure message.
- **DRY**: "do not repeat yourself", the practice of removing duplication in code.
- **Mystery guest**: test data defined out of sight of the test that depends on it.
- **Literal**: a value written directly in the code, such as `216` or `"paid"`.
- **Isolated test**: a test whose result does not depend on other tests or outside conditions.
- **Brittle (fragile) test**: a test that fails after a change that kept behaviour the same.
- **Snapshot test**: a test that compares output with a stored copy of earlier output.
- **Flaky test**: a test that passes or fails unpredictably without a code change.
- **Test smell**: a recognisable sign of a likely problem in test code.
- **Linter**: a tool that checks source code for suspicious patterns without running it.
- **Mutation testing**: deliberately altering code to see whether the tests notice.
- **FIRST**: fast, isolated, repeatable, self-validating, timely.

## Check yourself

```quiz
[
  {"q": "A test named 'account works' contains five assertions about five behaviours. The second and the fifth behaviours are broken. What does the runner report?",
   "options": ["Two failures", "One failure, at the second assertion; the fifth is never reached", "Five failures", "A pass"],
   "answer": 1,
   "explain": "A test stops at its first failed assertion. The later bug stays hidden until the first is fixed, and the name gives no hint which behaviour broke."},
  {"q": "expect(priceWithTax(net, rate)).toBe(net + net * rate / 10). The implementation uses the same formula and should divide by 100. Pass, fail, or pass for the wrong reason?",
   "options": ["Fail", "Pass for the wrong reason: the test repeats the implementation's bug", "Pass correctly", "It throws"],
   "answer": 1,
   "explain": "An expected value computed with the code's own formula cannot disagree with the code. A literal worked out by hand, 216 for 200 at 8 percent, would fail."},
  {"q": "for (const invoice of overdueUnpaid(list, today)) { expect(invoice.paid).toBe(false); } The function is broken and returns []. What happens?",
   "options": ["The test fails", "The test passes: the loop body never runs, so no assertion executes", "The runner reports zero assertions as a failure by default", "A TypeError"],
   "answer": 1,
   "explain": "An assertion inside a loop over the result is skipped when the result is empty. Compare the whole result with the expected list."},
  {"q": "Two tests share one module-level cart array. Test A pushes an item and expects length 1. Test B expects length 0. In which order do both pass?",
   "options": ["Any order", "Only B before A", "Only A before B", "Never"],
   "answer": 1,
   "explain": "If A runs first it leaves an item behind and B sees length 1. Each test should create its own cart."},
  {"q": "Blank-name validation is asserted in the model's tests, the controller's tests and three DOM tests. The rule changes to allow blank names. What is the cost?",
   "options": ["One test to update", "Five tests fail for one reason and all must be edited, although the repeats added no information", "No tests fail", "Only the DOM tests fail"],
   "answer": 1,
   "explain": "Test each behaviour once, in the layer that owns it. Other layers need one case showing that a rejection is handled."},
  {"q": "Which assertion is most likely to survive a refactoring that keeps behaviour the same?",
   "options": ["expect(cart._items).toHaveLength(2)", "expect(sortSpy).toHaveBeenCalledTimes(1)", "expect(cart.total()).toBe(17)", "expect(JSON.stringify(cart)).toBe('{\"_items\":[...]}')"],
   "answer": 2,
   "explain": "It checks an outcome through the public interface. The others pin a private field, an internal call or the exact internal structure."},
  {"q": "You wrote a test after the code and it passed on the first run. What should you do before trusting it?",
   "options": ["Nothing, green is green", "Break the code or the expectation on purpose and confirm the test fails with a sensible message", "Add a second identical test", "Raise the timeout"],
   "answer": 1,
   "explain": "A test never seen failing is unproven: it may be asserting nothing, or asserting on the wrong thing."},
  {"q": "A test uses anOrder({ express: true }) from a builder with defaults. What is the main benefit over writing the full order object in every test?",
   "options": ["It runs faster", "Only the property that matters to this test is visible, so the cause of the expected value is clear", "It avoids the need for assertions", "Builders make tests order-dependent"],
   "answer": 1,
   "explain": "Defaults hide the irrelevant fields and the override highlights the relevant one, without hiding it in a distant fixture."}
]
```

> **Source:** Johansen, *Test-Driven JavaScript Development*, ch. 17 (Writing Good Unit Tests). Smell names after Meszaros, *xUnit Test Patterns*. Docs: https://vitest.dev/api/expect.html , https://jestjs.io/docs/expect , https://vitest.dev/guide/snapshot , https://github.com/vitest-dev/eslint-plugin-vitest , https://github.com/jest-community/eslint-plugin-jest
