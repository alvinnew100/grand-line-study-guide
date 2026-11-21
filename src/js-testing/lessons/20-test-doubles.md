# Test doubles in depth: dummies, stubs, spies, mocks and fakes

> **Before this lesson:** you have used a recording function (`mockFn`) in [The observer pattern, built test-first](#/lesson/js-testing/observer-pattern-tdd), an HTTP stub in [Stubbing HTTP requests](#/lesson/js-testing/stubbing-http), a fake clock in [Polling a server and testing time with a fake clock](#/lesson/js-testing/polling-fake-timers) and stand-in page elements in [Test-driving a DOM client: a packing list app](#/lesson/js-testing/dom-client-tdd). This lesson gives those tools their proper names and shows when each one fits.

## In plain words

Code rarely works alone. A function that places an order talks to a payment service, a stock database, an email sender and a logger. In a unit test you want to check *your* function, not those services, so you replace them with stand-ins. The general name for any such stand-in is a **test double**.

Think of a film set. The street the actor walks down is a row of painted fronts with nothing behind them. The phone on the desk is a prop that rings when the director presses a button. A hidden microphone records what the actor says. The whole set exists so that one performance can be filmed, controlled and repeated. The actor, though, performs for real. In a test, your code is the actor and the doubles are the set.

Props come in kinds, and so do doubles:

- a mannequin in a shop window that only fills space is a **dummy**;
- the phone that rings on cue is a **stub**: it feeds the scene a prepared input;
- the hidden microphone is a **spy**: it records what happened so it can be checked afterwards;
- a strict stage manager holding a list of cues, who stops the take the moment something unplanned happens, is a **mock**;
- a camping stove that really cooks, used in place of a restaurant kitchen, is a **fake**: a working but much simpler version.

Why it matters for a job: "What is the difference between a mock and a stub?" is among the most frequently asked testing questions in interviews. On the job, the wrong choice of double is the main reason test suites become fragile: tests that break whenever the code is tidied up, although nothing a user could notice has changed.

## Why replace a collaborator at all

The code being tested is called the **system under test** (SUT). The objects it calls are its **collaborators**, also called dependencies. Replacing a collaborator is worth it for five reasons:

1. **Speed.** A real database or network call takes milliseconds to seconds; a double answers at once.
2. **Determinism.** Real services change their data and their mood. A double answers the same way every time.
3. **Reaching rare paths.** You cannot ask a real payment provider to be down on demand. A double can fail whenever the test says so.
4. **Observing outputs that go elsewhere.** If the only effect of your code is "an email was sent", there is no return value to check. A double can record the request.
5. **The real thing does not exist yet**, or costs money per call, or sends real emails to real people.

Two more terms describe what crosses the border between the SUT and a collaborator. A value the SUT *receives from* a collaborator, such as "3 items in stock", is an **indirect input**. A request the SUT *sends to* a collaborator, such as "send this email", is an **indirect output**. Stubs control indirect inputs. Spies and mocks check indirect outputs.

## The five kinds at a glance

The names below come from Gerard Meszaros's catalogue *xUnit Test Patterns* and are the ones interviewers expect.

| Kind | What it does | What the test asserts on | Typical example |
|---|---|---|---|
| **Dummy** | Nothing. It fills a required parameter | Nothing about the dummy | A logger passed to a function whose logging is not under test |
| **Stub** | Returns prepared answers | The SUT's result or state | `payments.charge` that always answers "declined" |
| **Spy** | Records how it was called (and may also answer) | The recorded calls, after the SUT ran | `mailer.send` that remembers its arguments |
| **Mock** | Is told in advance which calls to expect and checks them itself | Usually only `mock.verify()` | A mailer that must receive exactly one `send` with given arguments |
| **Fake** | Works for real in a simplified way | The SUT's result, or the fake's state | An in-memory stock store; the fake clock |

Every unit test has four phases: **setup** (build the objects), **exercise** (call the SUT), **verify** (check the outcome) and **teardown** (clean up). The kinds of double differ mainly in where the checking happens. With stubs, spies and fakes the test verifies at the end, as usual. A mock carries its expectations from the setup phase and verifies during the exercise.

## A running example

```javascript
function placeOrder(order, { stock, payments, mailer, logger }) {
  logger.info("placing order " + order.id);
  if (stock.available(order.item) < order.quantity) return { ok: false, reason: "out of stock" };

  const receipt = payments.charge(order.card, order.quantity * order.unitPrice);
  if (!receipt.ok) return { ok: false, reason: "payment declined" };

  stock.remove(order.item, order.quantity);
  mailer.send(order.email, "Order " + order.id + " confirmed");
  return { ok: true, receiptId: receipt.id };
}
```

`placeOrder` receives its four collaborators in an object. In production they are a real stock database, a real payment client and so on. In the tests below each one is replaced by the kind of double that the test in question needs.

### Dummy, stub and spy in one suite

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

// --- a tiny mock function, like jest.fn() / vi.fn() ---
function mockFn(impl = () => undefined) {
  const mock = (...args) => {
    mock.calls.push(args);            // remember the arguments of every call
    const value = impl(...args);
    mock.results.push(value);         // remember what was returned
    return value;
  };
  mock.calls = [];
  mock.results = [];
  mock.mockReturnValue = (v) => { impl = () => v; return mock; };
  mock.mockImplementation = (f) => { impl = f; return mock; };
  return mock;
}
// --- end of mock ---

function placeOrder(order, { stock, payments, mailer, logger }) {
  logger.info("placing order " + order.id);
  if (stock.available(order.item) < order.quantity) return { ok: false, reason: "out of stock" };
  const receipt = payments.charge(order.card, order.quantity * order.unitPrice);
  if (!receipt.ok) return { ok: false, reason: "payment declined" };
  stock.remove(order.item, order.quantity);
  mailer.send(order.email, "Order " + order.id + " confirmed");
  return { ok: true, receiptId: receipt.id };
}

const ORDER = { id: 7, item: "socks", quantity: 2, unitPrice: 5, card: "card-1", email: "ada@example.com" };

// One helper builds a working set of doubles; each test overrides the one it cares about.
function doubles(overrides = {}) {
  return {
    logger: { info() {} },                                              // DUMMY: must exist, is never checked
    stock: { available: () => 10, remove: mockFn() },                   // STUB answer + SPY on remove
    payments: { charge: mockFn(() => ({ ok: true, id: "r-1" })) },      // STUB answer + SPY on charge
    mailer: { send: mockFn() },                                         // SPY
    ...overrides,
  };
}

test("a successful order returns the receipt id", () => {
  expect(placeOrder(ORDER, doubles())).toEqual({ ok: true, receiptId: "r-1" });
});

test("STUB forces a path: no stock means no charge", () => {
  const d = doubles({ stock: { available: () => 1, remove: mockFn() } });
  expect(placeOrder(ORDER, d)).toEqual({ ok: false, reason: "out of stock" });
  expect(d.payments.charge.calls.length).toBe(0);
});

test("STUB forces a path: a declined card", () => {
  const d = doubles({ payments: { charge: () => ({ ok: false }) } });
  expect(placeOrder(ORDER, d).reason).toBe("payment declined");
});

test("SPY checks an indirect output: the amount charged", () => {
  const d = doubles();
  placeOrder(ORDER, d);
  expect(d.payments.charge.calls).toEqual([["card-1", 10]]);            // 2 pairs at 5 each
});

test("SPY checks an indirect output: one confirmation email", () => {
  const d = doubles();
  placeOrder(ORDER, d);
  expect(d.mailer.send.calls).toEqual([["ada@example.com", "Order 7 confirmed"]]);
});

test("SPY proves something did NOT happen: no email after a declined card", () => {
  const d = doubles({ payments: { charge: () => ({ ok: false }) } });
  placeOrder(ORDER, d);
  expect(d.mailer.send.calls.length).toBe(0);
  expect(d.stock.remove.calls.length).toBe(0);
});

test("STUB causes trouble: a payment outage surfaces as an error", () => {
  const d = doubles({ payments: { charge: () => { throw new Error("gateway timeout"); } } });
  expect(() => placeOrder(ORDER, d)).toThrow("gateway timeout");
  expect(d.mailer.send.calls.length).toBe(0);
});
```

Things to take from that block:

- **The dummy** `{ info() {} }` is never mentioned in an assertion. It exists because `placeOrder` would crash on `logger.info` without it.
- **A stub is about what comes back.** `available: () => 1` is one line, and it steers the SUT down the "out of stock" branch. The three stub tests show the three classic uses: avoiding an inconvenient real service, forcing a chosen path, and causing trouble on purpose.
- **A spy is about what went out.** The amount `10` and the email text are never returned by `placeOrder`; only the recorded calls reveal them.
- **One object can play two roles.** `mockFn(() => ({ ok: true, id: "r-1" }))` both answers (stub) and records (spy). Jest and Vitest call this combined object a "mock function", which is one reason the vocabulary gets blurred in daily use.
- **Absence is a behaviour.** "No email after a declined card" is a requirement, and only a spy can check it.

### A programmable stub: different answers on different calls

Some logic only shows with a sequence of answers: fail, fail, then succeed. A stub needs a queue of answers for that.

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

function stubFn() {
  const queue = [];                                   // answers reserved for the next calls
  let fallback = () => undefined;                     // answer when the queue is empty
  const stub = (...args) => {
    stub.calls.push(args);
    const answer = queue.length > 0 ? queue.shift() : fallback;
    return answer(...args);
  };
  stub.calls = [];
  stub.returns = (value) => { fallback = () => value; return stub; };
  stub.returnsOnce = (value) => { queue.push(() => value); return stub; };
  stub.throwsOnce = (message) => { queue.push(() => { throw new Error(message); }); return stub; };
  return stub;
}

// ---------- code under test ----------
function chargeWithRetry(payments, card, amount, attempts = 3) {
  let lastError;
  for (let i = 0; i < attempts; i++) {
    try { return payments.charge(card, amount); }
    catch (error) { lastError = error; }
  }
  throw lastError;
}

test("returns at once when the first attempt works", () => {
  const charge = stubFn().returns({ ok: true });
  chargeWithRetry({ charge }, "card-1", 10);
  expect(charge.calls.length).toBe(1);
});

test("tries again after a failure and returns the later success", () => {
  const charge = stubFn().throwsOnce("timeout").throwsOnce("timeout").returns({ ok: true, id: "r-9" });
  expect(chargeWithRetry({ charge }, "card-1", 10)).toEqual({ ok: true, id: "r-9" });
  expect(charge.calls.length).toBe(3);
});

test("gives up after the allowed attempts and reports the last error", () => {
  const charge = stubFn().throwsOnce("first").throwsOnce("second").throwsOnce("third").returns({ ok: true });
  expect(() => chargeWithRetry({ charge }, "card-1", 10)).toThrow("third");
  expect(charge.calls.length).toBe(3);
});
```

In Jest and Vitest the same queue is written `vi.fn().mockReturnValueOnce(a).mockReturnValueOnce(b).mockReturnValue(c)`, with `mockImplementationOnce(() => { throw ... })` for a failure.

### Spying on a method of a real object

Sometimes the collaborator is a real object you want to keep working, and you only want to listen in. A spy can wrap an existing method: it records the call and then passes it through to the original. It must also be able to put the original back, or later tests would inherit the wrapper.

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

function spyOn(object, name) {
  const original = object[name];
  const spy = function (...args) {
    spy.calls.push(args);
    return original.apply(this, args);                // call through to the real method
  };
  spy.calls = [];
  spy.restore = () => { object[name] = original; };
  object[name] = spy;                                 // swap the method on the object
  return spy;
}

const audit = {
  entries: [],
  record(text) { this.entries.push(text); return this.entries.length; },
};
function closeAccount(id, auditLog) {
  auditLog.record("closed " + id);
}

test("the real method still works while being watched", () => {
  const spy = spyOn(audit, "record");
  closeAccount(42, audit);
  expect(spy.calls).toEqual([["closed 42"]]);         // the spy saw the call
  expect(audit.entries).toEqual(["closed 42"]);       // and the real code ran
  spy.restore();                                      // teardown
});

test("after restore the object is as it was", () => {
  const before = audit.record;
  const spy = spyOn(audit, "record");
  spy.restore();
  expect(audit.record === before).toBe(true);
});
```

`original.apply(this, args)` calls the real method with the same `this` and the same arguments, so the object cannot tell it is being watched. `vi.spyOn(object, "method")` and `jest.spyOn` work the same way, and `vi.restoreAllMocks()` in an `afterEach` puts every spied method back.

### A fake: simple, but real

A fake is not scripted per test. It is a small, working implementation that keeps its own state. Compare this to the stub `available: () => 10`, which answers 10 for ever, whatever was removed.

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

function createFakeStock(initial) {
  const levels = new Map(Object.entries(initial));
  return {
    available: (item) => levels.get(item) || 0,
    remove(item, quantity) {
      if (quantity > this.available(item)) throw new Error("cannot remove more than is in stock");
      levels.set(item, this.available(item) - quantity);
    },
  };
}

function placeOrder(order, { stock, payments, mailer, logger }) {
  logger.info("placing order " + order.id);
  if (stock.available(order.item) < order.quantity) return { ok: false, reason: "out of stock" };
  const receipt = payments.charge(order.card, order.quantity * order.unitPrice);
  if (!receipt.ok) return { ok: false, reason: "payment declined" };
  stock.remove(order.item, order.quantity);
  mailer.send(order.email, "Order " + order.id + " confirmed");
  return { ok: true, receiptId: receipt.id };
}

const ORDER = { id: 7, item: "socks", quantity: 2, unitPrice: 5, card: "card-1", email: "ada@example.com" };
const others = () => ({ logger: { info() {} }, payments: { charge: () => ({ ok: true, id: "r-1" }) }, mailer: { send() {} } });

test("a successful order lowers the stock", () => {
  const stock = createFakeStock({ socks: 3 });
  placeOrder(ORDER, { stock, ...others() });
  expect(stock.available("socks")).toBe(1);           // state verification on the fake
});

test("two orders in a row: the second finds too little stock", () => {
  const stock = createFakeStock({ socks: 3 });
  placeOrder(ORDER, { stock, ...others() });
  expect(placeOrder(ORDER, { stock, ...others() })).toEqual({ ok: false, reason: "out of stock" });
});
```

The second test would be awkward with stubs: you would have to script `available` to answer 3 and then 1. With a fake, the behaviour follows from the fake's own state. Fakes shine when several calls interact. Their cost is that a fake is code, and code can have bugs, so a fake that is used widely deserves tests of its own.

### A mock: expectations first

A mock is set up with the calls it should receive. It throws the moment it receives a call it was not told about, and at the end `verify()` throws if an expected call never came.

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

function createMock() {
  const expectations = [];
  const mock = {
    expects(method) {
      const expectation = { method, args: null, result: undefined, met: false };
      expectations.push(expectation);
      mock[method] = (...args) => {
        const match = expectations.find((e) => e.method === method && !e.met &&
          (e.args === null || JSON.stringify(e.args) === JSON.stringify(args)));
        if (!match) throw new Error("unexpected call: " + method + "(" + args.map((a) => JSON.stringify(a)).join(", ") + ")");
        match.met = true;
        return match.result;
      };
      const chain = {
        withArgs(...args) { expectation.args = args; return chain; },
        returns(value) { expectation.result = value; return chain; },
      };
      return chain;
    },
    verify() {
      const missing = expectations.filter((e) => !e.met).map((e) => e.method);
      if (missing.length > 0) throw new Error("expected call never happened: " + missing.join(", "));
    },
  };
  return mock;
}

function notifyShipped(order, mailer) {
  if (!order.email) return;
  mailer.send(order.email, "Order " + order.id + " has shipped");
}

test("sends exactly the expected email", () => {
  const mailer = createMock();
  mailer.expects("send").withArgs("ada@example.com", "Order 7 has shipped");    // expectation comes FIRST
  notifyShipped({ id: 7, email: "ada@example.com" }, mailer);
  mailer.verify();                                                              // nothing left unmet
});

test("a wrong argument fails at the moment of the call", () => {
  const mailer = createMock();
  mailer.expects("send").withArgs("ada@example.com", "Order 7 has shipped");
  expect(() => notifyShipped({ id: 8, email: "ada@example.com" }, mailer)).toThrow("unexpected call: send");
});

test("a call that never happens fails at verify", () => {
  const mailer = createMock();
  mailer.expects("send");
  notifyShipped({ id: 7, email: "" }, mailer);                                  // no address: nothing is sent
  expect(() => mailer.verify()).toThrow("expected call never happened: send");
});
```

The difference from a spy is where the judgement sits. A spy records everything quietly and the test decides afterwards. A mock judges each call as it arrives.

## Stub, spy or mock: choosing

| Question | Use |
|---|---|
| Does the SUT need an answer from the collaborator to proceed? | Stub (or a fake if several calls interact) |
| Is the effect visible in a return value or in some state you can read? | Assert on that; no spy needed |
| Is the only effect a call to a collaborator? | Spy, asserting on the one call that matters |
| Must the collaborator be present but is irrelevant to this test? | Dummy or a plain stub, never a mock |
| Is the exact conversation with the collaborator the thing being specified (a protocol, a payment sequence)? | Mock, or a spy with strict assertions |

Two reasons make most teams reach for stubs and spies far more often than strict mocks. First, with spies the test reads in the usual order: set up, act, check at the bottom. With mocks the checks are stated before the action, and a reader has to scan the whole test to find them. Second, a mock objects to *every* call it was not told about. Put a mock in a shared setup, and tests that have nothing to do with it start failing when the SUT makes one extra, harmless call.

### Why interaction checks make tests brittle

The demo below has two versions of `placeOrder`'s stock handling that are equally correct: one removes the quantity in a single call, the other removes one unit at a time. A test that checks the *conversation* breaks when the code is tidied from one style to the other. A test that checks the *outcome* through a fake does not.

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

// --- a tiny mock function, like jest.fn() / vi.fn() ---
function mockFn(impl = () => undefined) {
  const mock = (...args) => {
    mock.calls.push(args);            // remember the arguments of every call
    const value = impl(...args);
    mock.results.push(value);         // remember what was returned
    return value;
  };
  mock.calls = [];
  mock.results = [];
  mock.mockReturnValue = (v) => { impl = () => v; return mock; };
  mock.mockImplementation = (f) => { impl = f; return mock; };
  return mock;
}
// --- end of mock ---

const versions = {
  "one call":       (stock, item, quantity) => { stock.remove(item, quantity); },
  "unit by unit":   (stock, item, quantity) => { for (let i = 0; i < quantity; i++) stock.remove(item, 1); },
};
function createFakeStock(initial) {
  const levels = new Map(Object.entries(initial));
  return { available: (item) => levels.get(item) || 0, remove(item, n) { levels.set(item, this.available(item) - n); } };
}

for (const [name, takeFromStock] of Object.entries(versions)) {
  console.log("--- implementation: " + name);

  test("interaction check: remove was called once with (socks, 2)", () => {
    const stock = { remove: mockFn() };
    takeFromStock(stock, "socks", 2);
    expect(stock.remove.calls).toEqual([["socks", 2]]);
  });

  test("outcome check: one pair of socks is left", () => {
    const stock = createFakeStock({ socks: 3 });
    takeFromStock(stock, "socks", 2);
    expect(stock.available("socks")).toBe(1);
  });
}
```

A test that fails although the behaviour is still right is a **brittle test**, and it punishes refactoring. The rule that follows: **check outcomes where there is an outcome to check; check interactions only where the interaction is the requirement.** Sending one email is a requirement. Calling `remove` once and not twice is an implementation detail.

## Keeping doubles honest

Every double is a statement of belief about the real collaborator: its method names, its argument order, the shape of its answers. Nothing in JavaScript checks that belief. If the real `mailer.send` takes `(subject, address)` and your spy assumes `(address, subject)`, the unit tests pass and every customer gets a broken email. Several habits reduce the risk:

- **Derive doubles from the real thing.** `vi.spyOn(realObject, "method")` fails if the method does not exist. Automatic module mocks (`vi.mock("./mailer.js")` with no factory) create a double with the same exports as the real module. TypeScript goes further and rejects a double whose shape does not match the interface.
- **Run one set of tests against both the fake and the real implementation.** Such a shared suite is a **contract test**:

```javascript
// stock.contract.js
export function stockContract(name, makeStock) {
  test(name + ": removing lowers what is available", async () => {
    const stock = await makeStock({ socks: 3 });
    await stock.remove("socks", 2);
    expect(await stock.available("socks")).toBe(1);
  });
}

// in the unit suite:         stockContract("fake stock", createFakeStock);
// in the integration suite:  stockContract("database stock", createDatabaseStock);
```

- **Do not double what you do not own.** Faking a third-party library's interface means guessing at behaviour you cannot see. Wrap the library in a small module of your own (an **adapter**), give the adapter an interface shaped for your application, double the adapter in unit tests, and test the adapter itself against the real library in a few integration tests.
- **Trust what is already tested.** A collaborator that is fast, deterministic and has its own tests can often be used for real. A pure formatting function or an in-memory collection needs no double. Fewer doubles means fewer beliefs that can go stale.

## What the libraries call things

| Meszaros term | Jest / Vitest | Sinon | `node:test` |
|---|---|---|---|
| Dummy | any placeholder value | any placeholder value | any placeholder value |
| Stub | `vi.fn().mockReturnValue(x)`, `mockResolvedValue(x)` | `sinon.stub().returns(x)` | `mock.fn(() => x)` |
| Spy | `vi.fn()`, `vi.spyOn(obj, "m")`, then `expect(f).toHaveBeenCalledWith(...)` | `sinon.spy()`, `sinon.spy(obj, "m")` | `mock.fn()`, `mock.method(obj, "m")`, then `f.mock.calls` |
| Mock (strict, expectations first) | not built in; spies with strict assertions are used | `sinon.mock(obj).expects("m").once()` then `verify()` | not built in |
| Fake | written by hand; `vi.useFakeTimers()` is a ready-made one | `sinon.useFakeTimers()` | `mock.timers` |

So in a Jest or Vitest codebase the word "mock" covers stubs and spies, and "mocking a module" usually means stubbing it. In an interview, use the precise terms and add that the libraries use "mock" loosely.

```javascript
import { test, expect, vi, afterEach } from "vitest";

afterEach(() => { vi.restoreAllMocks(); });                 // put spied methods back

test("no email after a declined card", () => {
  const mailer = { send: vi.fn() };                                   // spy
  const payments = { charge: vi.fn().mockReturnValue({ ok: false }) }; // stub
  const stock = { available: () => 10, remove: vi.fn() };
  const logger = { info() {} };                                       // dummy

  const result = placeOrder(ORDER, { stock, payments, mailer, logger });

  expect(result).toEqual({ ok: false, reason: "payment declined" });
  expect(mailer.send).not.toHaveBeenCalled();
  expect(payments.charge).toHaveBeenCalledWith("card-1", 10);
});
```

> [!WARNING]
> A test in which nearly everything is a double mostly tests the doubles. If `placeOrder` were handed a stubbed version of its own pricing logic, the test would pass with any price. Double the collaborators at the edges of the unit, and let the logic you care about run for real.

> [!TIP]
> When writing a spy assertion, ask: "if a colleague restructured this code without changing what users get, would this assertion still pass?" If not, loosen it (`toHaveBeenCalledWith(expect.objectContaining({ ... }))`) or replace it with a check on the outcome.

> [!INTERVIEW]
> **"What is the difference between a stub and a mock?"** A stub supplies prepared answers so the code under test can run down a chosen path; the test then asserts on the result or state. A mock is set up with expectations about the calls it should receive and fails the test itself if they are not met; it verifies behaviour, not state. A spy sits between them: it records calls for assertions afterwards. Then add judgement: prefer asserting on outcomes; verify interactions only when the call is the requirement, such as sending an email or charging a card; and note that Jest and Vitest use the word "mock" for all of these.

## Common pitfalls

- **Mocking everything.** The test then repeats the implementation line by line and breaks on every refactor.
- **Asserting on every call of every double.** Assert on the one interaction the test is named after.
- **A strict mock in shared setup.** Unrelated tests fail when the SUT makes a call the mock did not expect.
- **A stub that returns a shape the real service never returns.** The test proves the code handles an imaginary world.
- **Forgetting to restore a spied or replaced method.** The wrapper leaks into later tests. Restore in `afterEach`.
- **Sharing one double instance across tests.** Recorded calls accumulate, and counts become wrong. Create doubles per test.
- **A fake with no tests.** A bug in a widely used fake produces wrong results in every suite that trusts it.
- **Doubling a third-party API directly.** Wrap it in an adapter and double the adapter.
- **Using a double where the real object is fast and deterministic.** It adds work and removes realism.

## Cheat sheet

| Need | Vitest (Jest: `jest.` in place of `vi.`) |
|---|---|
| Recording function | `const f = vi.fn()` |
| Fixed answer | `vi.fn().mockReturnValue(x)` |
| Answer per call | `vi.fn().mockReturnValueOnce(a).mockReturnValueOnce(b)` |
| Throw | `vi.fn().mockImplementation(() => { throw new Error("down"); })` |
| Promise answers | `mockResolvedValue(x)`, `mockRejectedValue(error)` |
| Watch a real method | `const spy = vi.spyOn(obj, "method")` (calls through by default) |
| Replace a real method | `vi.spyOn(obj, "method").mockReturnValue(x)` |
| Was it called? | `expect(f).toHaveBeenCalled()`, `expect(f).not.toHaveBeenCalled()` |
| How often? | `expect(f).toHaveBeenCalledTimes(1)` |
| With what? | `expect(f).toHaveBeenCalledWith(a, expect.any(Number))` |
| Raw records | `f.mock.calls`, `f.mock.results` |
| Forget recorded calls | `f.mockClear()`, or `vi.clearAllMocks()` |
| Put originals back | `vi.restoreAllMocks()` |

## Summary

- A test double replaces a collaborator so the system under test can be checked alone, quickly and repeatably.
- Dummy: fills a slot. Stub: supplies indirect inputs. Spy: records indirect outputs. Mock: checks expected calls itself. Fake: a simplified working implementation.
- Stubs force paths, including failures that the real service cannot produce on demand.
- Spies are the tool when the only effect is a call, and for proving that a call did not happen.
- Fakes fit when several calls depend on shared state.
- Prefer checking outcomes; interaction checks tie tests to the implementation and make them brittle.
- Doubles encode beliefs about the real collaborator. Derive them from the real thing, share contract tests, wrap what you do not own, and use real objects when they are fast and reliable.

## Glossary

- **Test double**: any stand-in for a real collaborator in a test.
- **System under test (SUT)**: the code a test is checking.
- **Collaborator / dependency**: an object or function the SUT calls.
- **Indirect input**: a value the SUT receives from a collaborator.
- **Indirect output**: a request the SUT sends to a collaborator.
- **Dummy**: a double that only fills a parameter.
- **Stub**: a double that returns prepared answers.
- **Spy**: a double that records the calls made to it.
- **Mock**: a double programmed with expected calls that verifies them itself.
- **Fake**: a simplified but working implementation.
- **Call through**: a spy passing the call on to the real method.
- **Brittle test**: a test that fails after a change that did not alter behaviour.
- **Contract test**: one suite run against both a double and the real implementation to keep them in agreement.
- **Adapter**: a small module of your own that wraps an outside library behind an interface you control.

## Check yourself

```quiz
[
  {"q": "A test passes logger: { info() {} } to placeOrder and never mentions the logger again. Which kind of double is it?",
   "options": ["Spy", "Dummy", "Mock", "Fake"],
   "answer": 1,
   "explain": "It only fills a required slot so the code does not crash. Nothing is recorded, answered or verified."},
  {"q": "stock.available is replaced with () => 1 so that an order for 2 items is refused. Which kind of double, and what does it control?",
   "options": ["A spy controlling indirect outputs", "A stub controlling an indirect input to force the out-of-stock path", "A mock verifying a call", "A fake with state"],
   "answer": 1,
   "explain": "A stub supplies a prepared answer. The value the SUT receives from the collaborator is an indirect input."},
  {"q": "The requirement is: after a declined card, no confirmation email is sent. placeOrder returns { ok: false, reason: 'payment declined' } either way. What must the test use to check the requirement?",
   "options": ["Nothing, the return value covers it", "A spy on mailer.send, asserting it recorded zero calls", "A dummy mailer", "A fake clock"],
   "answer": 1,
   "explain": "The email is an indirect output that never appears in the return value. Only a recording double can show that the call did not happen."},
  {"q": "Two orders for 2 pairs are placed against a stub with available: () => 3. What does the second order return, and what would a fake stock starting at 3 return?",
   "options": ["Both: out of stock", "Stub: success, because it answers 3 for ever; fake: out of stock, because its state dropped to 1", "Stub: out of stock; fake: success", "Both: success"],
   "answer": 1,
   "explain": "A stub is scripted and stateless. A fake keeps real state, so interactions across several calls behave as in production."},
  {"q": "The code is refactored from stock.remove('socks', 2) to two calls of stock.remove('socks', 1). Which test now fails although the stock level ends up the same?",
   "options": ["The outcome check on a fake stock", "The interaction check expecting calls to equal [['socks', 2]]", "Both", "Neither"],
   "answer": 1,
   "explain": "The interaction check pins how the result is reached. The outcome check only cares that one pair is left, so it survives the refactor."},
  {"q": "A strict mock mailer with one expected send is created in a shared beforeEach. A new feature makes placeOrder send a second, legitimate email. What happens to the tests?",
   "options": ["Only the email test fails", "Every test that reaches the second send fails with an unexpected call, including tests about unrelated behaviour", "Nothing", "The mock adapts"],
   "answer": 1,
   "explain": "A mock rejects any call it was not told about. Using one for a collaborator that is not the focus of a test spreads failures across the suite."},
  {"q": "A spy assumes mailer.send(address, subject), but the real mailer's signature is send(subject, address). All unit tests pass. Which practice would have caught this?",
   "options": ["More spies", "A contract or integration test against the real mailer, or types that tie the double to the real interface", "Fake timers", "Higher coverage of placeOrder"],
   "answer": 1,
   "explain": "A hand-made double only reflects the author's belief. Something has to compare that belief with the real object."},
  {"q": "In a Vitest codebase a colleague says 'mock the payment client so it returns declined'. In precise terms, what are they asking for?",
   "options": ["A mock with expectations", "A stub: a replacement that returns a prepared answer", "A dummy", "A contract test"],
   "answer": 1,
   "explain": "Jest and Vitest use 'mock' for every kind of double. Returning a canned answer to steer the code is stubbing."}
]
```

> **Source:** Johansen, *Test-Driven JavaScript Development*, ch. 16 (Mocking and Stubbing). Terminology after Meszaros, *xUnit Test Patterns*. Docs: https://vitest.dev/guide/mocking , https://vitest.dev/api/mock.html , https://jestjs.io/docs/mock-functions , https://sinonjs.org/releases/latest/ , https://nodejs.org/api/test.html#mocking
