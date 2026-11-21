# Interview: common testing questions and model answers

> **Before this lesson:** this is the review lesson for the whole track. It leans most on [Test-driven development: red, green, refactor](#/lesson/js-testing/red-green-refactor), [Test doubles in depth: dummies, stubs, spies, mocks and fakes](#/lesson/js-testing/test-doubles), [Writing good unit tests: names, focus and test smells](#/lesson/js-testing/good-unit-tests), [Promises, timers and async code under test](#/lesson/js-testing/async-timers-promises) and [Coverage, mutation testing and tests in CI](#/lesson/js-testing/coverage-mutation-ci). Each answer links back to the lesson that teaches the topic in full.

## In plain words

Testing questions in an interview come in three forms. There are **concept questions** ("what is the difference between a mock and a stub?"), **judgement questions** ("is 100% coverage enough?", "how would you test this feature?") and **exercises** ("write tests for this function", "implement debounce and show it works"). None of them is a quiz about one tool's syntax. The interviewer is trying to find out whether you have written tests that had to survive real change, and whether you can explain your choices.

Think of a driving examiner. You are not asked to recite the highway code; you are asked to drive while the examiner watches how you look, decide and react. An answer that begins "it depends" and then says *what* it depends on scores higher than a confident slogan.

A shape that works for almost every answer:

1. **Define** the thing in one sentence, in plain words.
2. **Give one concrete example**, preferably from something you built.
3. **State the trade-off or the limit.** This is the part that shows experience.

Why it matters for a job: for front-end and full-stack roles in particular, testing questions are a standard part of the technical rounds, and a take-home exercise without tests is commonly marked down regardless of how well it works. The model answers below are written to be said aloud in about a minute each. Do not memorise the wording. Understand each one well enough to say it your own way.

## Part 1: fundamentals

### Why write automated tests at all?

Four reasons, in order of importance. They catch **regressions**: a regression is a feature that used to work and was broken by a later change, and a suite that runs in seconds checks every old behaviour on every change. They make **refactoring** safe, because you can restructure code and know at once whether behaviour moved. They **document** what the code is meant to do, in a form that cannot go out of date without failing. And writing them pushes the **design** towards small units with explicit inputs. The honest limit: tests show that the cases you thought of work; they do not prove the absence of bugs, and they cost time to write and maintain. (See [Why automate tests: your first unit test](#/lesson/js-testing/first-unit-test).)

### What is the difference between unit, integration and end-to-end tests?

Define each by what runs for real. A **unit test** runs one function or module with its collaborators replaced; it takes about a millisecond and a failure points at one place. An **integration test** runs several real parts together, such as a rendered screen with only the network faked, or a controller with a real database. An **end-to-end test** drives the whole deployed application through a real browser. Going up, tests get slower and their failures harder to locate, but they resemble real use more. So most checks belong at the lowest level that can perform them, with a small number of end-to-end tests for the journeys that must never break. (See [Component and end-to-end tests: Testing Library and Playwright](#/lesson/js-testing/testing-library-playwright).)

### What is the test pyramid?

A picture of that split: a wide base of unit tests, a narrower layer of integration tests, a small top of end-to-end tests. Its message is about cost: do not use a slow, fragile test to check something a fast one could. Some front-end teams prefer a thicker middle because most user-interface bugs are wiring mistakes that component tests catch. Either shape is defensible if you can say why.

### Explain test-driven development. What does it give you, and what does it not?

TDD is a loop of three steps. **Red**: write one small test for behaviour that does not exist yet, and watch it fail. **Green**: write the least code that makes it pass. **Refactor**: tidy the code and the tests while everything stays green. Benefits: every line of production code is covered by a test that has been seen to fail, the design is shaped by how the code is used, and progress comes in small verified steps. Limits: it does not tell you *which* tests to write, it cannot design a user interface or an architecture for you, and it fits exploratory work poorly; for a spike, many people write a throwaway version first and then rebuild it test-first.

### What makes a good unit test?

A name that states one behaviour and its condition. A body in three visible parts: arrange, act, assert. A literal expected value that came from the requirement, not from running the code. Fast, independent of other tests and of time, network and randomness. It asserts on an observable outcome through the public interface, so it survives refactoring. And someone has seen it fail. The acronym FIRST covers the properties: fast, isolated, repeatable, self-validating, timely.

### What should you not test?

Third-party libraries and the language itself: they have their own tests; test your use of them. Private implementation details: they are covered through the public behaviour, and testing them directly makes refactoring painful. Trivial code with no logic, such as a plain getter. And the same behaviour twice at different levels. The time saved goes to the code where defects are likely or expensive: calculations, state changes, parsing, error handling.

### You are given a function. How do you decide which cases to test?

Work from the specification, not from the code, in a fixed order:

1. **The typical case**, to pin the main behaviour.
2. **Boundaries**. Inputs fall into groups that are treated alike, called **equivalence classes** (for an age limit of 18: below, exactly at, above). Take one value from each group and the values on each side of every edge. Testing the edges on purpose is **boundary value analysis**; off-by-one bugs live there.
3. **Empty and minimal inputs**: empty string, empty array, zero, one element.
4. **Invalid input**: wrong type, negative numbers, `null`, missing arguments. Decide whether the function should throw or return a default, and test that decision.
5. **Special values** for the domain: duplicates, very large inputs, non-English text, leap years, time zones.

For `paginate(totalItems, pageSize, page)` that gives, for example: a middle page; the first and the last page; a last page that is only partly filled; zero items; a page number beyond the end; a page size of zero or a negative page. Saying the list aloud before writing any code is itself what the interviewer wants to see.

## Part 2: test doubles

### What is the difference between a mock, a stub, a spy and a fake?

All four are **test doubles**: stand-ins for a real collaborator. A **stub** returns prepared answers, to steer the code under test down a chosen path. A **spy** records how it was called, so the test can check afterwards what was sent to it. A **mock** is given expectations in advance and fails the test itself if the calls do not match. A **fake** is a simplified working implementation with its own state, such as an in-memory database or a fake clock. A fifth kind, the **dummy**, only fills a parameter. Add the practical note: Jest and Vitest call every one of these a "mock", so `vi.fn()` is a spy that can also be programmed as a stub.

### When should you not mock?

When the real collaborator is fast, deterministic and already tested: a pure function, an in-memory collection. When the thing you would mock is part of the unit you are testing, because then the test checks the mock. And when you do not own the interface: mocking a third-party library directly bakes your guesses about it into the tests, so wrap it in a small module of your own and mock that. The general cost of mocking is that every double encodes a belief about the real thing, and the belief can drift out of date while the tests stay green.

### State verification or behaviour verification?

State verification asserts on the result or on the state left behind. Behaviour verification asserts on which calls were made. Prefer state: it does not care how the result was produced, so it survives refactoring. Use behaviour verification when the call *is* the requirement and leaves no state you can read, for example "one confirmation email is sent" or "nothing is charged when stock is short".

### How do you test code that calls an HTTP API?

Find the seam. Best is to pass the HTTP function or an API client into the code and hand in a stub. If the code imports its client, mock that module. If it calls `fetch` directly, stub the global or intercept at the network level with Mock Service Worker. Then cover four cases at least: success with the data mapped correctly; the request itself for writes (method, URL, headers, body); an error status, remembering that `fetch` does not reject on 404 or 500; and a network failure. Close with the limit: stubs describe the server as you believed it to be, so keep a few tests against the real service or a shared schema. (See [Stubbing HTTP requests](#/lesson/js-testing/stubbing-http) and [Mocking modules, globals and fetch](#/lesson/js-testing/mocking-modules-fetch).)

### What is dependency injection and why does it help testing?

Supplying a collaborator from outside, usually as a parameter, instead of having the code create or import it. A function `getUser(id, fetchFn)` can be tested by passing a fake `fetchFn`; no tool is needed and the dependency is visible in the signature. The cost is longer parameter lists, which a default value (`fetchFn = fetch`) keeps out of the callers' way.

### Why does `vi.mock` or `jest.mock` seem to run before the imports?

Because it does. A module mock must be registered before the code under test loads the real module, so the runner hoists mock declarations to the top of the file. Two consequences worth mentioning: a factory cannot refer to ordinary variables declared later in the file (use `vi.hoisted`, or in Jest a variable named `mock...`), and a mock declared in the middle of a file still applies to all of it.

## Part 3: asynchronous code and time

### How do you test asynchronous code?

Make the test function `async` and `await` the code under test, so the runner waits for the returned promise. Check failures with `await expect(promise).rejects.toThrow(...)`. For callback-style code, wrap it in a promise. Replace the network and timers with doubles so nothing waits in real time. Then name the classic defect: a missing `await` or `return` lets the test finish before its assertion runs, and it passes whatever the code does.

### How do you test something that uses `setTimeout`, such as a debounce?

With fake timers: install them, call the code, advance the clock by an exact number of milliseconds and assert, including a check one millisecond before the deadline. Restore real timers afterwards. If the code also awaits promises between timers, use the asynchronous advance functions, because a synchronous advance does not let promise callbacks run. The exercise below does it from scratch.

### What makes a test flaky, and what do you do about one?

A flaky test passes or fails without any code change. Causes, roughly in order of frequency: real time (sleeps, timeouts tuned to a fast machine), shared state or data between tests, dependence on execution order, unawaited promises, real network calls, and dates or random values. The response: reproduce it by running the test repeatedly or in shuffled order, remove the non-determinism at its source, and meanwhile quarantine the test with an owner so it stops blocking everyone. Re-running until green is not a fix, because users can hit the same race the test found.

### Two requests are sent and the answers arrive in the wrong order. How do you handle and test that?

It is a race condition. Guard the handler: keep a counter or the latest query, and ignore an answer that no longer belongs to the newest request, or cancel the older request with `AbortController`. To test it, stub the request function with promises the test settles by hand, resolve the second request before the first, and assert that only the newest result is shown.

## Part 4: the DOM and user interfaces

### How would you test a UI component?

Render it into a simulated DOM, find elements the way a user would (by role, label and text), act with realistic events (type, click), and assert on what the user perceives: text appears, a field is cleared, an error is announced. Fake only the network. Do not assert on internal state, class names or the exact element structure. Put the rules the component relies on (validation, calculations) in plain functions with their own unit tests, so the component tests can stay few.

### `getBy`, `queryBy`, `findBy`: what is the difference?

They differ in what happens when nothing matches. `getBy` throws at once, which suits elements that should be present. `queryBy` returns `null`, which is what you need to assert that something is absent. `findBy` returns a promise and retries until the element appears or a time limit passes, for content that shows up after asynchronous work.

### What are snapshot tests good and bad for?

A snapshot test stores output and fails when the output changes. Good for: a tripwire on output that a person has reviewed and that should rarely change, such as a serialised configuration or a small rendered fragment. Bad for: large rendered trees, where every change trips them and people update the snapshot without reading the difference. A snapshot records what the code does today, including its bugs; it never states what the code *should* do.

### jsdom or a real browser?

jsdom implements the DOM in JavaScript inside Node: fast to start, fine for behaviour that depends on structure and events. It does no layout or painting, so it cannot tell whether something is visible, covered, or laid out correctly, and it lags behind browsers on newer features. A real browser, driven by Playwright or a runner's browser mode, is the truth at a higher cost. A common split is component tests in jsdom and critical journeys in real browsers.

## Part 5: tools and process

### Is 100% code coverage a good goal?

Coverage shows which code ran during the tests, not whether its results were checked. A suite with no assertions can reach 100%. Even with assertions, it does not pin boundaries or combinations, and it cannot show requirements that were never implemented. So low coverage reliably signals missing tests, while high coverage proves little. Use it to find untested code and as a ratchet against decline; where correctness really matters, measure with mutation testing, which checks whether tests fail when the code is deliberately broken.

### What is mutation testing?

A tool makes small changes to the production code, one at a time (flip a comparison, change a constant, remove a line), and runs the tests against each changed copy, called a mutant. A mutant that makes some test fail is killed; one that passes every test survived, and it names a behaviour that no test pins down. It is slow, so teams run it on changed or critical code.

### Jest or Vitest?

Their interfaces are almost identical on purpose, so the choice is about the surrounding tooling. Vitest shares the Vite build configuration, handles ES modules and TypeScript without a transform step and has a fast watch mode: the usual pick for new projects. Jest is mature and already present in a very large number of codebases; migrating a big working suite costs effort for no new behaviour. For a small library with no build step, Node's built-in `node:test` avoids dependencies altogether.

### The test suite takes ten minutes. What do you do?

Measure first: runners report the slowest tests and files. Then remove real waiting (fake timers, doubles for network and disk), cut repeated expensive setup, stop loading a DOM environment for files that only need Node, and make sure files run in parallel. In the workflow: run affected tests while developing and on pull requests, the full suite on the main branch, and split the suite across machines with sharding. Keep isolation intact while speeding up, or the suite becomes flaky.

### You inherit code with no tests and must change it. Where do you start?

Do not begin by rewriting. First write **characterization tests**: tests that record what the code does *now*, right or wrong, by calling it with representative inputs and asserting on the actual outputs. They form a safety net. Then find or create a seam near the change, so the part you will touch can be called on its own. Make the change test-first inside that net, and leave the area better covered than you found it. Coverage numbers are useful here as a map of where no net exists.

### How do you test a private function?

Through the public function that uses it. If that is too awkward (too many cases to reach from outside), the private function is probably a unit in its own right: move it to its own module, export it there and test it directly. Exporting internals only for tests, or reaching into them with tricks, ties the tests to the implementation.

### How do you test code that depends on the current date or on randomness?

Take the source of non-determinism out of the function: pass the current time or a random-number function as an argument, or fix them in the test with `vi.setSystemTime` and `vi.spyOn(Math, "random")`. Then test exact boundaries: one second before midnight, the lowest and highest random values. Also say what you would avoid: tests that only pass on certain days or in one time zone.

## Part 6: three exercises

### Exercise 1: implement debounce and prove it works

A **debounced** function delays its work until calls have stopped arriving for a given time; a burst of calls results in one execution with the latest arguments. Interviewers like it because it needs a closure, a timer and, for the tests, control over time. The solution takes the clock as a parameter so the tests can use a fake.

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

// --- a tiny fake clock, like jest.useFakeTimers() / vi.useFakeTimers() ---
function createClock() {
  let now = 0, nextId = 1;
  const timers = [];                  // every waiting timer: { id, at, cb, every }
  const add = (cb, ms, every) => { timers.push({ id: nextId, at: now + ms, cb, every }); return nextId++; };
  const remove = (id) => { const i = timers.findIndex((t) => t.id === id); if (i >= 0) timers.splice(i, 1); };
  return {
    now: () => now,
    setTimeout: (cb, ms = 0) => add(cb, ms, 0),
    setInterval: (cb, ms) => add(cb, ms, ms),
    clearTimeout: remove,
    clearInterval: remove,
    tick(ms) {                        // move time forward, firing due timers in order
      const end = now + ms;
      for (;;) {
        timers.sort((a, b) => a.at - b.at || a.id - b.id);
        const t = timers[0];
        if (!t || t.at > end) break;
        now = t.at;
        if (t.every) t.at += t.every; else timers.shift();
        t.cb();
      }
      now = end;
    },
  };
}
// --- end of clock ---

function debounce(fn, wait, clock) {
  let timer = null;
  return function (...args) {
    if (timer !== null) clock.clearTimeout(timer);            // a new call cancels the pending run
    timer = clock.setTimeout(() => { timer = null; fn(...args); }, wait);
  };
}

function setup(wait = 300) {
  const clock = createClock();
  const calls = [];
  const save = debounce((text) => calls.push(text), wait, clock);
  return { clock, calls, save };
}

test("nothing happens before the wait has passed", () => {
  const { clock, calls, save } = setup();
  save("a");
  clock.tick(299);
  expect(calls).toEqual([]);
});

test("runs once when the wait has passed", () => {
  const { clock, calls, save } = setup();
  save("a");
  clock.tick(300);
  expect(calls).toEqual(["a"]);
});

test("a burst of calls gives one run with the last arguments", () => {
  const { clock, calls, save } = setup();
  save("h"); clock.tick(100);
  save("he"); clock.tick(100);
  save("hel"); clock.tick(300);
  expect(calls).toEqual(["hel"]);
});

test("each call restarts the wait", () => {
  const { clock, calls, save } = setup();
  save("a"); clock.tick(299);
  save("ab"); clock.tick(299);
  expect(calls).toEqual([]);                                   // 598 ms in total, but never 300 of quiet
  clock.tick(1);
  expect(calls).toEqual(["ab"]);
});

test("two separate bursts give two runs", () => {
  const { clock, calls, save } = setup();
  save("first"); clock.tick(300);
  save("second"); clock.tick(300);
  expect(calls).toEqual(["first", "second"]);
});
```

What to say while writing it: the timer id lives in the closure; each call clears the previous timer and starts a new one; the tests check one millisecond before and exactly at the deadline. If asked for follow-ups, mention a `cancel` method, a "leading edge" option that runs on the first call, and **throttle**, which runs at most once per interval however often it is called.

### Exercise 2: these tests pass. Why should that worry you?

The function below has two bugs, marked in comments. Three tests pass anyway. Under them are two repaired tests, which fail as they should. Read why each bad test cannot see the bug, then fix the function and run again until all five pass.

```js-run
// --- the tiny test runner from lesson 1, async edition ---
async function test(name, fn) {   // async: it can wait for promises
  try { await fn(); console.log("PASS  " + name); }
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

// ---------- code under test, with two bugs ----------
async function applyCoupon(cart, code, api) {
  const coupon = await api.lookup(code);
  if (!coupon) return cart;                         // BUG 1: should throw new Error("unknown coupon")
  return { total: cart.total - coupon.amount };     // BUG 2: the total must never go below zero
}

const api = { lookup: async (code) => ({ TEN: { amount: 10 }, BIG: { amount: 50 } }[code] || null) };
const rejection = async (promise) => { try { await promise; return null; } catch (e) { return e.message; } };

console.log("--- three tests that cannot fail");
await test("bad 1: rejects an unknown coupon (assertion on an unawaited promise)", async () => {
  applyCoupon({ total: 30 }, "NOPE", api).catch((e) => expect(e.message).toBe("unknown coupon"));
});
await test("bad 2: rejects an unknown coupon (assertion only inside catch)", async () => {
  try { await applyCoupon({ total: 30 }, "NOPE", api); }
  catch (e) { expect(e.message).toBe("unknown coupon"); }
});
await test("bad 3: a big coupon (expected value copied from the formula)", async () => {
  const cart = { total: 30 };
  expect((await applyCoupon(cart, "BIG", api)).total).toBe(cart.total - 50);
});

console.log("--- the same intentions, written so they can fail");
await test("good: rejects an unknown coupon", async () => {
  expect(await rejection(applyCoupon({ total: 30 }, "NOPE", api))).toBe("unknown coupon");
});
await test("good: a coupon larger than the total brings it to zero, not below", async () => {
  expect((await applyCoupon({ total: 30 }, "BIG", api)).total).toBe(0);
});
```

Bad 1 attaches its assertion to a promise nobody waits for, and to a rejection that never happens. Bad 2 only asserts inside `catch`, so when nothing is thrown, nothing is checked. Bad 3 computes its expected value with the same subtraction as the code, so it agrees with the bug. In an interview, being able to explain why a green test is worthless is at least as impressive as writing a new one.

### Exercise 3: review this test

You may be shown a test and asked for comments. A checklist to run through aloud:

```javascript
let user;
beforeAll(async () => { user = await createUser(db, "ada@example.com"); });

it("works", async () => {
  const spy = jest.spyOn(mailer, "send");
  await sleep(500);
  const result = await service.register(user);
  expect(spy).toHaveBeenCalledTimes(1);
  expect(spy.mock.calls[0][0]).toEqual({ to: "ada@example.com", subject: "Welcome", id: result.id, sentAt: result.createdAt });
  expect(result).toMatchSnapshot();
});
```

- **The name** "works" states no behaviour.
- **Shared state**: `user` is created once in `beforeAll` and reused, and it is written to a real database, so tests can affect each other.
- **A real sleep** of half a second, with no stated reason.
- **The spy calls through** to the real mailer (a real email?) and is never restored.
- **Over-specified assertion**: the full argument object, including a timestamp, will break on any harmless change. Assert on recipient and subject with `expect.objectContaining`.
- **Two behaviours** (an email is sent; the result has a shape) in one test.
- **A snapshot** of an object containing ids and dates will differ on every run.

A rewrite would create its data per test, stub the mailer, drop the sleep, and split into "sends one welcome email to the new user" and "returns the saved user".

> [!TIP]
> When you are asked to write code in an interview and nobody mentions tests, say one sentence about them anyway: "I would cover the empty input, the boundary at X and the error case; shall I write those?" It costs ten seconds and signals how you normally work.

> [!WARNING]
> Do not present any rule as absolute: "always mock", "never mock", "100% coverage", "one assertion per test". Each of these is a guideline with a reason behind it, and interviewers probe for the reason. State the guideline, then the situation where you would break it.

> [!INTERVIEW]
> **A closing question you may be asked: "How do you know your tests are good?"** Three signals. They fail when the code is broken on purpose, which is what mutation testing automates. They do not fail when the code is restructured without changing behaviour. And when one fails, its name and message tell you what broke without a debugging session. Coverage is a fourth, weaker signal: useful for finding what has no tests at all.

## Common pitfalls

- **Answering with tool syntax.** "I would call `jest.mock`" is not an explanation. Say what is being replaced and why.
- **Reciting definitions with no example.** One sentence about a real test you wrote beats a textbook paragraph.
- **Forgetting the unhappy paths** when listing test cases: errors, empty input, boundaries.
- **Claiming a rule is universal.** Give the trade-off.
- **Mixing up the doubles.** Stub answers, spy records, mock expects, fake works.
- **Saying "I would add a sleep"** for any timing problem. Control time, or wait for a condition.
- **Treating coverage as proof of quality.**
- **Going silent while coding.** Narrate the cases you are considering; the reasoning is what is being assessed.

## Summary

- Structure answers as definition, example, trade-off.
- Levels are defined by what runs for real; put each check at the cheapest level that can perform it.
- Choose test cases from the specification: typical, boundaries, empty, invalid, special.
- Know the five doubles and the difference between checking state and checking calls; prefer outcomes.
- Async tests must await; time is controlled with fake timers; races are staged with promises the test settles.
- Component tests act like a user and assert on what the user perceives.
- Coverage finds untested code; mutation testing measures whether tests detect faults.
- For untested legacy code, start with characterization tests and a seam.
- A green test that cannot fail is worse than no test; be ready to explain why.

## Glossary

- **Regression**: a behaviour that used to work and was broken by a later change.
- **Refactoring**: restructuring code without changing what it does.
- **Equivalence class**: a group of inputs that the code should treat in the same way.
- **Boundary value analysis**: choosing test inputs at and next to the edges between equivalence classes.
- **Test double**: any stand-in for a real collaborator: dummy, stub, spy, mock or fake.
- **State verification / behaviour verification**: asserting on results and state / asserting on calls made.
- **Seam**: a place where a dependency can be replaced without editing the code that uses it.
- **Flaky test**: a test whose result changes without a code change.
- **Race condition**: a bug that depends on the relative timing of events.
- **Debounce**: delaying an action until calls have stopped for a set time.
- **Throttle**: limiting an action to at most once per time interval.
- **Characterization test**: a test that records what existing code currently does, as a safety net before changing it.
- **Snapshot test**: a test comparing output with a stored copy of earlier output.
- **Mutation testing**: checking a suite by running it against deliberately broken copies of the code.

## Check yourself

```quiz
[
  {"q": "An interviewer asks: 'Mock or stub?' Which answer is the most accurate?",
   "options": ["They are the same thing", "A stub supplies prepared answers and the test checks the result; a mock holds expectations about calls and verifies them itself", "A mock is for functions and a stub is for classes", "A stub records calls and a mock returns values"],
   "answer": 1,
   "explain": "Stubs control indirect inputs; mocks verify interactions. Spies record calls for later assertions, and Jest and Vitest call all of them mocks."},
  {"q": "A validation function accepts ages from 18 to 65 inclusive. Which set of test inputs follows boundary value analysis?",
   "options": ["20, 30, 40, 50", "17, 18, 65, 66 plus one typical value such as 40", "0 and 100", "18 only"],
   "answer": 1,
   "explain": "The edges are between 17 and 18 and between 65 and 66. Testing both sides of each edge, plus a typical value, covers the three equivalence classes and the off-by-one risks."},
  {"q": "try { await applyCoupon(cart, 'NOPE', api); } catch (e) { expect(e.message).toBe('unknown coupon'); } The function wrongly returns the cart without throwing. What does the test report?",
   "options": ["Fail", "Pass, because the catch block and its assertion never run", "A timeout", "An unhandled rejection"],
   "answer": 1,
   "explain": "No error means no assertion. Use a rejects matcher, a helper that captures the rejection, or expect.assertions(1)."},
  {"q": "debounce(fn, 300): calls happen at 0 ms, 100 ms and 200 ms, then nothing. When does fn run, and how many times?",
   "options": ["At 300 ms, once", "At 500 ms, once, with the arguments of the last call", "Three times, at 300, 400 and 500 ms", "Immediately, once"],
   "answer": 1,
   "explain": "Each call cancels the pending timer and starts a new 300 ms wait. The last call at 200 ms leads to one run at 500 ms."},
  {"q": "You must change a 400-line function that has no tests. What is the safest first step?",
   "options": ["Rewrite it cleanly", "Write characterization tests that record its current outputs for representative inputs, then change it inside that safety net", "Add a snapshot of the source code", "Mock all of its internals"],
   "answer": 1,
   "explain": "Characterization tests capture existing behaviour, right or wrong, so unintended changes become visible during the modification."},
  {"q": "Which statement about code coverage is correct?",
   "options": ["100% coverage means no bugs", "Low coverage reliably indicates missing tests; high coverage does not prove the tests check anything", "Coverage measures the number of assertions", "Branch coverage is always equal to line coverage"],
   "answer": 1,
   "explain": "Coverage counts executed code. A suite without assertions can reach 100%, and coverage cannot reveal unimplemented requirements or unchecked boundaries."},
  {"q": "In a review you see expect(spy.mock.calls[0][0]).toEqual({ to, subject, id, sentAt }). What is the main objection?",
   "options": ["Spies cannot record objects", "It over-specifies the call: unrelated or unpredictable fields such as a timestamp make the test brittle; assert on the fields that matter", "toEqual does not work on objects", "It should use toBe"],
   "answer": 1,
   "explain": "expect.objectContaining({ to, subject }) keeps the assertion on the requirement and lets harmless changes pass."},
  {"q": "A test needs to assert that an error banner is NOT shown. Which query fits?",
   "options": ["getByRole('alert'), which throws when absent", "queryByRole('alert'), which returns null when absent", "findByRole('alert'), which waits for it to appear", "getAllByRole('alert')"],
   "answer": 1,
   "explain": "queryBy returns null for no match, so expect(...).not.toBeInTheDocument() can run. getBy would throw first, and findBy would wait and then reject."}
]
```

> **Source:** Johansen, *Test-Driven JavaScript Development*, Parts I, III and IV (ch. 1 to 3 and 11 to 17) as the basis for the concepts reviewed here. Docs: https://vitest.dev/guide/ , https://jestjs.io/docs/getting-started , https://testing-library.com/docs/guiding-principles , https://playwright.dev/docs/best-practices , https://martinfowler.com/articles/mocksArentStubs.html
