"""JavaScript testing problems: bind, once, memoize, an observable, and the family of test doubles."""


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


BIND_DRIVER = r'''
// --- driver (provided, do not change) ---
function runBind(mode, thisName, preset, callArgs) {
  if (bind.toString().includes(".bind(")) return "write it without the built-in bind";
  function describe(...args) { return (this && this.name) + ":" + args.join(","); }
  const owner = { name: thisName, describe };
  if (mode === "plain") return bind(describe, owner, ...preset)(...callArgs);
  if (mode === "detached") { const loose = bind(owner.describe, owner, ...preset); return [1, 2].map(() => loose(...callArgs)); }
  if (mode === "rebind") return bind(bind(describe, owner, ...preset), { name: "second" })(...callArgs);
  if (mode === "reuse") { const bound = bind(describe, owner, ...preset); return [bound(...callArgs), bound("x"), bound()]; }
  if (mode === "method") { const other = { name: "other", run: bind(describe, owner, ...preset) }; return other.run(...callArgs); }
  return null;
}
'''

ONCE_DRIVER = r'''
// --- driver (provided, do not change) ---
function runOnce(firstResult, callArgs) {
  let runs = 0;
  const init = once((...args) => {
    runs++;
    if (firstResult === "@args") return args.join("+");
    if (firstResult === "@undefined") return undefined;
    return firstResult;
  });
  const results = callArgs.map((args) => init(...args));
  return { results, runs };
}
'''

MEMO_DRIVER = r'''
// --- driver (provided, do not change) ---
function runMemoize(calls) {
  let computed = 0;
  const slow = (a, b = 0) => { computed++; return a * a - b; };
  const wrappers = { a: memoize(slow), b: memoize(slow) };     // two independent memoized functions
  const results = calls.map(([which, ...args]) => wrappers[which](...args));
  return { results, computed };
}
'''

MEMO_SOLUTION = r'''function memoize(fn) {
  const cache = new Map();
  return function (...args) {
    const key = JSON.stringify(args);
    if (!cache.has(key)) cache.set(key, fn.apply(this, args));
    return cache.get(key);
  };
}
'''

OBS_DRIVER = r'''
// --- driver (provided, do not change) ---
function runObservable(ops) {
  const subject = createObservable();
  const log = [];
  const listeners = {};
  const listener = (id) => (listeners[id] ??= function (event, payload) {
    log.push(id + ":" + payload);
    if (id.startsWith("bad")) throw new Error(id + " failed");
    if (id.startsWith("self")) subject.unobserve(event, listeners[id]);     // removes itself while being notified
    if (id.startsWith("adder")) subject.observe(event, listener("late"));   // adds an observer while being notified
  });
  return ops.map(([op, event, arg]) => {
    if (op === "observe") { subject.observe(event, listener(arg)); return null; }
    if (op === "unobserve") { subject.unobserve(event, listener(arg)); return null; }
    log.length = 0;
    const called = subject.notify(event, event, arg);
    return [called, [...log]];
  });
}
'''

OBS_SOLUTION = r'''function createObservable() {
  const observers = new Map();
  return {
    observe(event, fn) {
      if (!observers.has(event)) observers.set(event, []);
      const list = observers.get(event);
      if (!list.includes(fn)) list.push(fn);
    },
    unobserve(event, fn) {
      const list = observers.get(event) || [];
      const index = list.indexOf(fn);
      if (index !== -1) list.splice(index, 1);
    },
    notify(event, ...args) {
      const snapshot = [...(observers.get(event) || [])];
      for (const fn of snapshot) {
        try { fn(...args); } catch (error) { /* one failing observer must not stop the rest */ }
      }
      return snapshot.length;
    },
  };
}
'''

SPY_DRIVER = r'''
// --- driver (provided, do not change) ---
function runSpy(useImpl, ops) {
  const spy = useImpl ? createSpy((...numbers) => numbers.reduce((sum, n) => sum + n, 0)) : createSpy();
  const plain = (value) => (value === undefined ? "undefined" : value);
  return ops.map(([op, args]) => {
    if (op === "call") return plain(spy(...args));
    if (op === "count") return spy.calls.length;
    if (op === "calls") return spy.calls.map((call) => [...call]);
    if (op === "results") return spy.results.map(plain);
    if (op === "calledWith") return spy.calledWith(...args);
    if (op === "reset") { spy.reset(); return "reset"; }
    return null;
  });
}
'''

SPY_SOLUTION = r'''function createSpy(impl) {
  const spy = function (...args) {
    spy.calls.push(args);
    const value = impl ? impl.apply(this, args) : undefined;
    spy.results.push(value);
    return value;
  };
  spy.calls = [];
  spy.results = [];
  spy.calledWith = (...expected) => spy.calls.some((call) => JSON.stringify(call) === JSON.stringify(expected));
  spy.reset = () => { spy.calls.length = 0; spy.results.length = 0; };
  return spy;
}
'''

STUB_DRIVER = r'''
// --- driver (provided, do not change) ---
function runStub(setup, calls) {
  const stub = createStub();
  for (const [kind, a, b] of setup) {
    if (kind === "returns") stub.returns(a);
    else if (kind === "throws") stub.throws(a);
    else if (kind === "onCall") stub.onCall(a).returns(b);
    else if (kind === "onCallThrows") stub.onCall(a).throws(b);
    else if (kind === "withArgs") stub.withArgs(...a).returns(b);
  }
  const results = calls.map((args) => {
    try { const value = stub(...args); return value === undefined ? "undefined" : value; }
    catch (error) { return "error: " + error.message; }
  });
  return { results, callCount: stub.callCount };
}
'''

STUB_SOLUTION = r'''function createStub() {
  const byCall = new Map();              // call index -> behaviour
  const byArgs = [];                     // [{ key, behaviour }]
  let fallback = () => undefined;
  const returning = (value) => () => value;
  const throwing = (message) => () => { throw new Error(message); };
  const stub = function (...args) {
    const index = stub.callCount;
    stub.callCount++;
    if (byCall.has(index)) return byCall.get(index)();
    const key = JSON.stringify(args);
    const match = byArgs.find((entry) => entry.key === key);
    if (match) return match.behaviour();
    return fallback();
  };
  stub.callCount = 0;
  stub.returns = (value) => { fallback = returning(value); return stub; };
  stub.throws = (message) => { fallback = throwing(message); return stub; };
  stub.onCall = (index) => ({
    returns(value) { byCall.set(index, returning(value)); return stub; },
    throws(message) { byCall.set(index, throwing(message)); return stub; },
  });
  stub.withArgs = (...args) => ({
    returns(value) { byArgs.push({ key: JSON.stringify(args), behaviour: returning(value) }); return stub; },
  });
  return stub;
}
'''

HTTP_DRIVER = r'''
// --- driver (provided, do not change) ---
function runLoadCart(routes, userId) {
  const requests = [];
  const http = {                                  // the mock HTTP client handed to your function
    get(url) {
      requests.push(url);
      const reply = routes[url];
      if (reply === undefined || reply === "down") throw new Error("network unreachable");
      return JSON.parse(JSON.stringify(reply));   // a fresh copy each time
    },
  };
  return { result: loadCart(http, userId), requests };
}
'''

HTTP_SOLUTION = r'''function loadCart(http, userId) {
  const tryGet = (url) => {
    try { return http.get(url); } catch (error) { return null; }
  };
  const user = tryGet("/users/" + userId);
  if (user === null) return { ok: false, reason: "offline" };
  if (user.status === 404) return { ok: false, reason: "no such user" };
  if (user.status !== 200) return { ok: false, reason: "server error " + user.status };
  const { name, cartId } = user.body;
  if (cartId === null || cartId === undefined) return { ok: true, name, total: 0 };
  const cart = tryGet("/carts/" + cartId);
  if (cart === null) return { ok: false, reason: "offline" };
  if (cart.status === 404) return { ok: true, name, total: 0 };
  if (cart.status !== 200) return { ok: false, reason: "server error " + cart.status };
  const total = cart.body.items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  return { ok: true, name, total };
}
'''

SPYON_DRIVER = r'''
// --- driver (provided, do not change) ---
function runSpyOn(ops) {
  const counter = {
    count: 0,
    add(n) { this.count += n; return this.count; },
  };
  const original = counter.add;
  let spy = null;
  return ops.map(([op, arg]) => {
    if (op === "spy") { spy = spyOn(counter, "add"); return "spying"; }
    if (op === "add") { const value = counter.add(arg); return value === undefined ? "undefined" : value; }
    if (op === "count") return counter.count;
    if (op === "calls") return spy.calls.map((call) => [...call]);
    if (op === "returns") { spy.returns(arg); return "stubbed"; }
    if (op === "restore") { spy.restore(); return "restored"; }
    if (op === "isOriginal") return counter.add === original;
    return null;
  });
}
'''

SPYON_SOLUTION = r'''function spyOn(object, name) {
  const original = object[name];
  let replacement = null;                       // { value } once returns(...) has been called
  const spy = function (...args) {
    spy.calls.push(args);
    return replacement ? replacement.value : original.apply(this, args);
  };
  spy.calls = [];
  spy.returns = (value) => { replacement = { value }; return spy; };
  spy.restore = () => { object[name] = original; };
  object[name] = spy;
  return spy;
}
'''

MOCK_DRIVER = r'''
// --- driver (provided, do not change) ---
function runMock(expected, actual) {
  const mock = createMock();
  for (const [method, args] of expected) mock.expect(method, args);
  const log = actual.map(([method, args]) => {
    try { mock.call(method, args); return "ok"; }
    catch (error) { return "error: " + error.message; }
  });
  try { mock.verify(); log.push("verified"); }
  catch (error) { log.push("error: " + error.message); }
  return log;
}
'''

MOCK_SOLUTION = r'''function createMock() {
  const queue = [];
  const show = (method, args) => method + "(" + JSON.stringify(args).slice(1, -1) + ")";
  return {
    expect(method, args) { queue.push({ method, args }); },
    call(method, args) {
      const next = queue[0];
      if (!next || next.method !== method || JSON.stringify(next.args) !== JSON.stringify(args)) {
        throw new Error("unexpected call: " + show(method, args));
      }
      queue.shift();
    },
    verify() {
      if (queue.length > 0) throw new Error("missing calls: " + queue.map((entry) => entry.method).join(", "));
    },
  };
}
'''

USER_OK = {"status": 200, "body": {"name": "Ada", "cartId": "c1"}}
CART_OK = {"status": 200, "body": {"items": [{"price": 4, "quantity": 2}, {"price": 6, "quantity": 1}]}}

PROBLEMS = [
dict(
    id="jstest-bind", title="Write bind", difficulty="Medium", pattern="Functions and this",
    kind="js", entry="runBind",
    description=r"""
A method passed around as a plain function loses its `this`. `bind` repairs that. Write it yourself,
**without using the built-in `bind`**.

`bind(fn, thisArg, ...preset)` returns a new function. Calling the new function calls `fn` with

- `this` set to `thisArg`, however and wherever the new function is called
- the `preset` arguments first, followed by the arguments of the call
- and returns what `fn` returns

The returned function can be called many times; the preset arguments must be the same on every call.

The driver binds a function `describe` that returns `this.name + ":" + args.join(",")` and exercises it in
five ways: `"plain"`, `"detached"` (a method taken off its object), `"rebind"` (binding a bound function again:
the first `this` wins), `"reuse"` (three calls of one bound function) and `"method"` (the bound function stored
on another object and called as that object's method).

**Examples:** `runBind("plain", "Ada", [1], [2, 3])` → `"Ada:1,2,3"` · `runBind("method", "owner", [], ["z"])` → `"owner:z"`
""",
    starter="function bind(fn, thisArg, ...preset) {\n  // return a new function\n}\n" + BIND_DRIVER,
    solution="function bind(fn, thisArg, ...preset) {\n  return function (...later) {\n    return fn.apply(thisArg, [...preset, ...later]);\n  };\n}\n" + BIND_DRIVER,
    tests=[
        ["plain", "Ada", [1], [2, 3]],
        ["method", "owner", [], ["z"]],
        ["plain", "Ada", [], [1, 2]],
        ["plain", "Ada", [], []],
        ["detached", "Bo", ["hi"], ["there"]],
        ["rebind", "first", [1], [2]],
        ["reuse", "Cy", ["p"], ["a", "b"]],
        ["plain", "N", [1, 2, 3], [4, 5]],
        ["reuse", "R", [], []],
        ["method", "m", [1, 2], [3]],
        ["rebind", "keep", [], []],
        ["detached", "D", [], []],
    ],
    examples=2,
    wrong_solutions=[
        "function bind(fn, thisArg, ...preset) {\n  return function () {\n    return fn.apply(thisArg, preset);\n  };\n}\n" + BIND_DRIVER,
        "function bind(fn, thisArg, ...preset) {\n  return function (...later) {\n    return fn.apply(thisArg, later);\n  };\n}\n" + BIND_DRIVER,
        "function bind(fn, thisArg, ...preset) {\n  return function (...later) {\n    preset.push(...later);\n    return fn.apply(thisArg, preset);\n  };\n}\n" + BIND_DRIVER,
        "function bind(fn, thisArg, ...preset) {\n  return function (...later) {\n    return fn.apply(this, [...preset, ...later]);\n  };\n}\n" + BIND_DRIVER,
    ],
    guide=G(
        prereqs="How `this` is decided by the call, `call` and `apply`, rest and spread. Lessons *Functions under test* and *Applied functions*.",
        intuition="The returned function is a closure that remembers three things: the original function, the `this` to use, and the arguments to put in front. When it is called, it forwards everything with `apply`.",
        hints=[
            "Return `function (...later) { ... }`; inside, ignore the caller's `this` completely.",
            "`fn.apply(thisArg, arrayOfArguments)` calls `fn` with a chosen `this`.",
            "Build a new array on each call: `[...preset, ...later]`. Do not modify `preset`.",
        ],
        brute_force="Temporarily storing `fn` as a property of `thisArg` and calling it as a method (`thisArg.tmp = fn; thisArg.tmp(...)`) sets `this` too, but it changes the object and fails for frozen objects and for `null`.",
        approach="`return function (...later) { return fn.apply(thisArg, [...preset, ...later]); }`.\n\n**Dry run** `rebind`: the inner bound function always applies `fn` with the first owner, whatever `this` it receives. The outer bound function calls the inner one with `this` = `{name: \"second\"}`, which the inner one ignores. Result: the first name.",
        complexity="O(p + a) per call for p preset and a call-time arguments, to build the argument list.",
        pitfalls="- Using the caller's `this` (`fn.apply(this, ...)`) breaks the moment the bound function is stored on another object.\n- Pushing call-time arguments into `preset` makes them pile up across calls.\n- Forgetting to return the result of `fn`.",
        follow_up="The real `bind` also works with `new`: the bound `this` is then ignored but preset arguments are kept. Read about it, then explain why arrow functions cannot be re-bound.",
    ),
),
dict(
    id="jstest-once", title="Run a function only once", difficulty="Easy", pattern="Closures",
    kind="js", entry="runOnce",
    description=r"""
`once(fn)` returns a function that calls `fn` on its **first** call only. Every later call returns the result
of that first call without calling `fn` again. It is how one-time initialisation is written.

- `fn` is not called until the returned function is called
- the first call's arguments (and `this`) are passed to `fn`; arguments of later calls are ignored
- the remembered result may be **anything**, including `0`, `""`, `false`, `null` and `undefined`; none of
  those may cause a second run

The driver wraps a function that counts how often it runs and returns `firstResult` (or, for `"@args"`, its
arguments joined by `+`; for `"@undefined"`, the value `undefined`). It returns the results of all calls and
the number of real runs.

**Examples:** `runOnce(42, [[], [], []])` → `{results: [42, 42, 42], runs: 1}` ·
`runOnce("@args", [[1, 2], [3, 4]])` → `{results: ["1+2", "1+2"], runs: 1}`
""",
    starter="function once(fn) {\n  // your code\n}\n" + ONCE_DRIVER,
    solution="function once(fn) {\n  let called = false, result;\n  return function (...args) {\n    if (!called) {\n      called = true;\n      result = fn.apply(this, args);\n    }\n    return result;\n  };\n}\n" + ONCE_DRIVER,
    tests=[
        [42, [[], [], []]],
        ["@args", [[1, 2], [3, 4]]],
        [0, [[], []]],
        ["", [[], [], []]],
        [False, [[], []]],
        [None, [[], []]],
        ["@undefined", [[], [], []]],
        [7, []],
        ["@args", [[]]],
        [{"a": 1}, [[], []]],
        ["@args", [["x"], ["y"], ["z"]]],
    ],
    examples=2,
    wrong_solutions=[
        "function once(fn) {\n  let result;\n  return function (...args) {\n    if (!result) result = fn.apply(this, args);\n    return result;\n  };\n}\n" + ONCE_DRIVER,
        "function once(fn) {\n  let result;\n  return function (...args) {\n    if (result === undefined) result = fn.apply(this, args);\n    return result;\n  };\n}\n" + ONCE_DRIVER,
        "function once(fn) {\n  const result = fn();\n  return function () { return result; };\n}\n" + ONCE_DRIVER,
        "function once(fn) {\n  let called = false;\n  return function (...args) {\n    if (called) return undefined;\n    called = true;\n    return fn.apply(this, args);\n  };\n}\n" + ONCE_DRIVER,
    ],
    guide=G(
        prereqs="Closures that keep private state between calls; lesson *Applied functions: binding, closures, state and memoisation*.",
        intuition="Two facts must be remembered between calls: *has it run?* and *what did it return?*. They are different facts. A result of `0` or `undefined` does not mean it has not run.",
        hints=[
            "Keep a boolean flag in the closure next to the result variable.",
            "Set the flag before or right after calling `fn`, then store the result.",
            "Do not use the result itself as the flag; the tests return every falsy value on purpose.",
        ],
        brute_force="Calling `fn` straight away inside `once` and returning a function that hands back the stored value is simpler, but it runs the initialisation even if nobody ever needs it, and it cannot pass the first call's arguments.",
        approach="Closure variables `called = false` and `result`. The returned function checks the flag; on the first call it sets the flag and stores `fn.apply(this, args)`; it always returns `result`.\n\n**Dry run** `runOnce(0, [[], []])`: first call → flag set, `fn` runs (runs = 1), result `0`. Second call → flag is set, return `0`. With `if (!result)` the second call would run `fn` again, because `0` is falsy.",
        complexity="O(1) per call after the first.",
        pitfalls="- `if (!result)` and `if (result === undefined)` both confuse a legitimate result with 'not yet run'.\n- Running `fn` eagerly, at wrap time.\n- Returning `undefined` on later calls and discarding the stored result.",
        follow_up="What should happen if the first call throws: stay 'not called' so a retry is possible, or remember the failure? Both exist in libraries. Write tests for the behaviour you choose.",
    ),
),
dict(
    id="jstest-memoize", title="Memoize, with a call counter watching", difficulty="Medium", pattern="Closures",
    kind="js", entry="runMemoize",
    description=r"""
**Memoising** a function means remembering its results, so that calling it again with the same arguments
returns the stored answer without recomputing. Write `memoize(fn)`.

- two calls count as "the same" when their **whole argument lists** are equal in values and types
  (`f(1, 23)` is not `f(12, 3)`, and `f(1)` is not `f("1")`); build the cache key from all arguments
- a stored result may be `0` or any other falsy value and must still be reused
- every memoized function has **its own** cache: `memoize(fn)` called twice gives two independent functions

The driver memoizes one slow function twice, as `a` and `b`. The slow function computes `x * x - y` and counts
how often it really runs. Each entry of `calls` is `[which, ...args]`. The driver returns all results and the
number of real computations.

**Examples:** `runMemoize([["a", 3], ["a", 3]])` → `{results: [9, 9], computed: 1}` ·
`runMemoize([["a", 2], ["b", 2], ["a", 2]])` → `{results: [4, 4, 4], computed: 2}`
""",
    starter="function memoize(fn) {\n  // your code\n}\n" + MEMO_DRIVER,
    solution=MEMO_SOLUTION + MEMO_DRIVER,
    tests=[
        [[["a", 3], ["a", 3]]],
        [[["a", 2], ["b", 2], ["a", 2]]],
        [[["a", 3], ["a", 4], ["a", 3]]],
        [[["a", 0], ["a", 0], ["a", 0]]],
        [[["a", 2, 4], ["a", 2, 4]]],
        [[["a", 1, 23], ["a", 12, 3]]],
        [[["a", 1], ["a", "1"], ["a", 1]]],
        [[]],
        [[["a", 5, 1], ["a", 5, 2], ["a", 5, 1]]],
        [[["a", 2], ["b", 2], ["a", 2], ["b", 2], ["b", 3]]],
        [[["a", i % 4] for i in range(12)]],
        [[["a", 1, 1], ["a", 1, 1], ["a", 1, 1], ["b", 1, 1]]],
    ],
    examples=2,
    wrong_solutions=[
        "function memoize(fn) {\n  const cache = new Map();\n  return function (...args) {\n    const key = args[0];\n    if (!cache.has(key)) cache.set(key, fn.apply(this, args));\n    return cache.get(key);\n  };\n}\n" + MEMO_DRIVER,
        "function memoize(fn) {\n  const cache = {};\n  return function (...args) {\n    const key = JSON.stringify(args);\n    if (!cache[key]) cache[key] = fn.apply(this, args);\n    return cache[key];\n  };\n}\n" + MEMO_DRIVER,
        "const sharedCache = new Map();\nfunction memoize(fn) {\n  return function (...args) {\n    const key = JSON.stringify(args);\n    if (!sharedCache.has(key)) sharedCache.set(key, fn.apply(this, args));\n    return sharedCache.get(key);\n  };\n}\n" + MEMO_DRIVER,
        "function memoize(fn) {\n  const cache = new Map();\n  return function (...args) {\n    const key = args.join(\"\");\n    if (!cache.has(key)) cache.set(key, fn.apply(this, args));\n    return cache.get(key);\n  };\n}\n" + MEMO_DRIVER,
    ],
    guide=G(
        prereqs="Closures, `Map`, `JSON.stringify`. Lesson *Applied functions* test-drives a one-argument memoize.",
        intuition="A memoized function is the original function plus a private dictionary from *arguments* to *result*. Three questions decide the design: what is the key, how do you tell 'stored' from 'not stored', and where does the dictionary live.",
        hints=[
            "Create the cache inside `memoize`, so each returned function closes over its own.",
            "`JSON.stringify(args)` turns the whole argument list into a key that keeps order and types apart: `[1,23]`, `[12,3]`, `[\"1\"]`.",
            "Ask the cache with `has(key)`. Looking at the stored value fails when the value is `0`.",
        ],
        brute_force="Recomputing every time is the behaviour you are replacing: correct, and as slow as the function. The call counter in the driver shows the difference.",
        approach="`const cache = new Map()` in the closure. On each call: build the key; if the cache lacks it, compute and store; return the stored value.\n\n**Dry run** `[[\"a\", 2, 4], [\"a\", 2, 4]]`: key `[2,4]` absent → compute `2 * 2 - 4 = 0`, store. Second call: `has` is true → return `0`, no computation. `computed` is 1.",
        complexity="O(k) per call to build a key of size k; one stored entry per distinct argument list.",
        pitfalls="- Keying on the first argument only returns wrong answers for functions of two arguments.\n- `if (!cache[key])` recomputes whenever the stored result is falsy.\n- One cache shared by all memoized functions mixes up results of different functions.\n- Joining arguments without a separator makes `(1, 23)` and `(12, 3)` collide.",
        follow_up="`JSON.stringify` cannot key on functions or distinguish `undefined` from `null` inside arrays. Design a key for arguments that are objects (identity through a `WeakMap`), and add a size limit to the cache.",
    ),
),
dict(
    id="jstest-observable", title="An observable that survives its observers", difficulty="Medium", pattern="Observer pattern",
    kind="js", entry="runObservable",
    description=r"""
Write `createObservable()`. It returns an object with three methods.

- `observe(event, fn)` registers `fn` for the named event. Registering the **same function again for the same
  event** changes nothing.
- `unobserve(event, fn)` removes it. Removing something that is not registered is not an error.
- `notify(event, ...args)` calls every observer of that event, in registration order, with the arguments, and
  returns **how many observers it called**.

Two robustness rules:

1. An observer that **throws** must not stop the remaining observers (it still counts as called).
2. Observers added or removed **while a notification is running** do not change that notification: it calls
   exactly the observers that were registered when it started.

The driver creates observers by id. Each writes `id:payload` to a log. Ids starting with `bad` throw, ids
starting with `self` remove themselves when called, ids starting with `adder` register another observer
(`late`) when called. For every `notify` the driver returns `[called, logEntries]`; other operations give `null`.

**Example:** `runObservable([["observe", "save", "a"], ["observe", "save", "bad1"], ["observe", "save", "c"], ["notify", "save", "x"]])`
→ `[null, null, null, [3, ["a:x", "bad1:x", "c:x"]]]`
""",
    starter="function createObservable() {\n  // return { observe(event, fn), unobserve(event, fn), notify(event, ...args) }\n}\n" + OBS_DRIVER,
    solution=OBS_SOLUTION + OBS_DRIVER,
    tests=[
        [[["observe", "save", "a"], ["observe", "save", "bad1"], ["observe", "save", "c"], ["notify", "save", "x"]]],
        [[["observe", "save", "a"], ["notify", "save", "hi"]]],
        [[["observe", "save", "a"], ["observe", "load", "b"], ["notify", "save", 1], ["notify", "load", 2]]],
        [[["notify", "nothing", "x"]]],
        [[["observe", "e", "a"], ["observe", "e", "a"], ["notify", "e", "x"]]],
        [[["observe", "e", "a"], ["observe", "e", "b"], ["unobserve", "e", "a"], ["notify", "e", "x"]]],
        [[["observe", "e", "self1"], ["observe", "e", "b"], ["notify", "e", "x"], ["notify", "e", "y"]]],
        [[["observe", "e", "adder1"], ["observe", "e", "b"], ["notify", "e", "x"], ["notify", "e", "y"]]],
        [[["unobserve", "e", "ghost"], ["unobserve", "never", "ghost"], ["observe", "e", "a"], ["notify", "e", "x"]]],
        [[["observe", "save", "a"], ["observe", "load", "a"], ["notify", "save", 1], ["unobserve", "save", "a"], ["notify", "save", 2], ["notify", "load", 3]]],
        [[["observe", "e", "a"], ["observe", "e", "b"], ["observe", "e", "c"], ["unobserve", "e", "a"], ["observe", "e", "a"], ["notify", "e", "x"]]],
        [[["observe", "e", "bad1"], ["observe", "e", "bad2"], ["observe", "e", "self3"], ["observe", "e", "z"], ["notify", "e", 1], ["notify", "e", 2]]],
    ],
    examples=1,
    wrong_solutions=[
        OBS_SOLUTION.replace("try { fn(...args); } catch (error) { /* one failing observer must not stop the rest */ }", "fn(...args);") + OBS_DRIVER,
        OBS_SOLUTION.replace("const snapshot = [...(observers.get(event) || [])];", "const snapshot = observers.get(event) || [];") + OBS_DRIVER,
        OBS_SOLUTION.replace("if (!list.includes(fn)) list.push(fn);", "list.push(fn);") + OBS_DRIVER,
        OBS_SOLUTION.replace("return snapshot.length;", "") + OBS_DRIVER,
    ],
    guide=G(
        prereqs="`Map`, arrays of functions, `try` / `catch`. Lesson *The observer pattern, built test-first*.",
        intuition="An observable is a dictionary from event name to a list of functions. The interesting part is what happens when those functions misbehave: one throws, one edits the list you are looping over. Loop over a copy, and fence each call.",
        hints=[
            "Store one array per event in a `Map`; create it on first use.",
            "Before pushing, check `list.includes(fn)`.",
            "In `notify`, copy the list (`[...list]`) and wrap each call in its own `try` / `catch`.",
        ],
        brute_force="Looping directly over the stored array works until an observer removes itself: the array shrinks under the loop and the next observer is skipped.",
        approach="`observe`: get or create the list, push unless present. `unobserve`: `indexOf` and `splice`. `notify`: take a snapshot, call each function inside `try`, return the snapshot's length.\n\n**Dry run** with `self1` then `b`: snapshot `[self1, b]`. `self1` logs and removes itself from the *stored* list; the snapshot still holds both, so `b` is called. Result `[2, [\"self1:x\", \"b:x\"]]`; the next notification calls only `b`.",
        complexity="`observe` and `unobserve` are O(n) in the observers of that event; `notify` is O(n) plus the copy.",
        pitfalls="- No `try`: the first failing observer silences all later ones and the error escapes to the notifier.\n- Looping over the live list: self-removal skips an observer, and an observer added mid-notification gets called immediately.\n- Allowing duplicates, so one `unobserve` leaves a second registration behind.\n- Returning nothing from `notify`.",
        follow_up="Return the caught errors too, so the notifier can report them. Add `once(event, fn)`, and decide what `unobserve` inside a `once` handler should do.",
    ),
),
dict(
    id="jstest-spy", title="A spy that records calls", difficulty="Easy", pattern="Test doubles",
    kind="js", entry="runSpy",
    description=r"""
A **spy** is a function that remembers how it was called, so a test can ask afterwards. Write
`createSpy(impl)`.

The returned function `spy`

- records the arguments of every call as an array in `spy.calls`
- calls `impl` (if one was given) with the same arguments and returns its result; without `impl` it returns `undefined`
- records every returned value in `spy.results`
- has `spy.calledWith(...args)`: `true` if **any** recorded call had exactly these arguments (same number,
  same values; compare contents, so `{id: 1}` matches `{id: 1}`)
- has `spy.reset()`, which forgets all recorded calls and results

The driver creates a spy (with an adding function as `impl` when `useImpl` is true) and runs a list of
operations: `["call", args]`, `["count"]`, `["calls"]`, `["results"]`, `["calledWith", args]`, `["reset"]`.
The value `undefined` is shown as the text `"undefined"`.

**Example:** `runSpy(true, [["call", [1, 2]], ["call", [5]], ["calledWith", [1, 2]], ["results"]])` →
`[3, 5, true, [3, 5]]`
""",
    starter="function createSpy(impl) {\n  // return a function with .calls, .results, .calledWith(...) and .reset()\n}\n" + SPY_DRIVER,
    solution=SPY_SOLUTION + SPY_DRIVER,
    tests=[
        [True, [["call", [1, 2]], ["call", [5]], ["calledWith", [1, 2]], ["results"]]],
        [False, [["call", [1, 2]], ["count"], ["calls"]]],
        [False, [["call", ["a"]], ["call", ["b"]], ["calledWith", ["a"]], ["calledWith", ["b"]], ["calledWith", ["c"]]]],
        [False, [["call", [1, 2]], ["calledWith", [1]], ["calledWith", [1, 2, 3]], ["calledWith", [2, 1]]]],
        [False, [["call", [{"id": 1}]], ["calledWith", [{"id": 1}]], ["calledWith", [{"id": 2}]]]],
        [True, [["call", [1]], ["call", [2]], ["reset"], ["count"], ["results"], ["calledWith", [1]]]],
        [False, [["count"], ["calls"], ["calledWith", []]]],
        [False, [["call", []], ["calledWith", []], ["results"]]],
        [True, [["call", []], ["call", [10, 20, 30]], ["results"], ["calls"]]],
        [True, [["call", [1]], ["reset"], ["call", [2]], ["calls"], ["results"]]],
        [False, [["call", [[1, 2], "x"]], ["calledWith", [[1, 2], "x"]], ["calledWith", [[1, 2]]]]],
    ],
    examples=1,
    wrong_solutions=[
        SPY_SOLUTION.replace("spy.calls.some((call) => JSON.stringify(call) === JSON.stringify(expected))", "JSON.stringify(spy.calls[spy.calls.length - 1]) === JSON.stringify(expected)") + SPY_DRIVER,
        SPY_SOLUTION.replace("spy.calls.some((call) => JSON.stringify(call) === JSON.stringify(expected))", "spy.calls.some((call) => JSON.stringify(call[0]) === JSON.stringify(expected[0]))") + SPY_DRIVER,
        SPY_SOLUTION.replace("spy.calls.length = 0; spy.results.length = 0;", "spy.calls.length = 0;") + SPY_DRIVER,
        SPY_SOLUTION.replace("spy.calls.some((call) => JSON.stringify(call) === JSON.stringify(expected))", "spy.calls.some((call) => call.length === expected.length && call.every((value, i) => value === expected[i]))") + SPY_DRIVER,
    ],
    guide=G(
        prereqs="Functions are objects and can carry properties; rest parameters. The `mockFn` built in the observer lesson is the same idea.",
        intuition="A spy is an ordinary function with a notebook attached. Each call writes a line in the notebook (the arguments, the result) and then does whatever the real work is, if any.",
        hints=[
            "Create the function first, then attach `calls`, `results`, `calledWith` and `reset` to it as properties.",
            "Inside the function, `spy.calls.push(args)` before calling `impl`.",
            "For `calledWith`, compare `JSON.stringify(call)` with `JSON.stringify(expected)` for each recorded call.",
        ],
        brute_force="A plain array in the test (`const seen = []; const fn = (x) => seen.push(x);`) is a one-off spy. `createSpy` packages the pattern so every test does not rewrite it.",
        approach="`const spy = function (...args) { record; run impl; record result; return it; }`, then attach the properties.\n\n**Dry run** of the example: call `(1, 2)` → calls `[[1, 2]]`, result `3`. Call `(5)` → calls `[[1, 2], [5]]`, result `5`. `calledWith(1, 2)` finds the first record → `true`.",
        complexity="O(1) per call; `calledWith` is O(n · k) for n recorded calls with k arguments.",
        pitfalls="- Checking only the most recent call in `calledWith`.\n- Comparing only the first argument, so `(1, 2)` matches `(1)`.\n- Comparing with `===`, which says two separate `{id: 1}` objects differ.\n- `reset` that clears the calls and leaves the results.",
        follow_up="Add `spy.calledBefore(otherSpy)` using a shared call counter. Jest and Vitest expose the same records as `fn.mock.calls` and `fn.mock.results`.",
    ),
),
dict(
    id="jstest-stub", title="A stub with programmable answers", difficulty="Medium", pattern="Test doubles",
    kind="js", entry="runStub",
    description=r"""
A **stub** returns prepared answers so that a test can steer the code under test. Write `createStub()`,
returning a function `stub` that can be programmed:

- `stub.returns(value)`: the default answer for every call (the most recent default wins)
- `stub.throws(message)`: the default becomes throwing `new Error(message)`
- `stub.onCall(n).returns(value)` and `stub.onCall(n).throws(message)`: the answer for call number `n` only,
  counting from **0**
- `stub.withArgs(...args).returns(value)`: the answer whenever the call's arguments equal `args` (compare contents)
- `stub.callCount`: how many times the stub has been called, including calls that threw

When several rules could apply, the most specific wins: **`onCall` first, then `withArgs`, then the default**.
With no rule at all the stub returns `undefined`.

The driver applies a list of setup steps, calls the stub with each argument list in `calls`, and returns the
results (errors as `"error: message"`, `undefined` as `"undefined"`) and the call count.

**Example:** `runStub([["returns", "a"], ["onCall", 1, "b"]], [[], [], []])` → `{results: ["a", "b", "a"], callCount: 3}`
""",
    starter="function createStub() {\n  // return a function with returns, throws, onCall, withArgs and callCount\n}\n" + STUB_DRIVER,
    solution=STUB_SOLUTION + STUB_DRIVER,
    tests=[
        [[["returns", "a"], ["onCall", 1, "b"]], [[], [], []]],
        [[["returns", 7]], [[], [], [1, 2]]],
        [[], [[], []]],
        [[["onCall", 0, "first"]], [[], []]],
        [[["withArgs", [1, 2], "sum"], ["returns", "other"]], [[1, 2], [2, 1], [1, 2, 3], [1, 2]]],
        [[["throws", "down"]], [[], []]],
        [[["onCallThrows", 0, "timeout"], ["onCallThrows", 1, "timeout"], ["returns", "ok"]], [[], [], []]],
        [[["withArgs", ["x"], "by args"], ["onCall", 0, "by call"], ["returns", "default"]], [["x"], ["x"], ["y"]]],
        [[["returns", 1], ["returns", 2]], [[]]],
        [[["withArgs", [{"id": 1}], "object match"]], [[{"id": 1}], [{"id": 2}]]],
        [[["returns", 0], ["onCall", 2, None]], [[], [], [], []]],
        [[["throws", "x"], ["returns", "recovered"]], [[]]],
        [[["returns", "v"]], []],
        [[["withArgs", [1], "one"], ["withArgs", [1, 1], "one one"]], [[1, 1], [1], [1, 2]]],
    ],
    examples=1,
    wrong_solutions=[
        STUB_SOLUTION.replace("if (byCall.has(index)) return byCall.get(index)();", "if (byCall.has(index + 1)) return byCall.get(index + 1)();") + STUB_DRIVER,
        STUB_SOLUTION.replace("    if (byCall.has(index)) return byCall.get(index)();\n    const key = JSON.stringify(args);\n    const match = byArgs.find((entry) => entry.key === key);\n    if (match) return match.behaviour();\n    return fallback();", "    const key = JSON.stringify(args);\n    const match = byArgs.find((entry) => entry.key === key);\n    if (match) return match.behaviour();\n    if (byCall.has(index)) return byCall.get(index)();\n    return fallback();") + STUB_DRIVER,
        STUB_SOLUTION.replace("    const index = stub.callCount;\n    stub.callCount++;\n    if (byCall.has(index)) return byCall.get(index)();\n    const key = JSON.stringify(args);\n    const match = byArgs.find((entry) => entry.key === key);\n    if (match) return match.behaviour();\n    return fallback();", "    const index = stub.callCount;\n    const key = JSON.stringify(args);\n    const match = byArgs.find((entry) => entry.key === key);\n    const value = byCall.has(index) ? byCall.get(index)() : match ? match.behaviour() : fallback();\n    stub.callCount++;\n    return value;") + STUB_DRIVER,
        STUB_SOLUTION.replace("const key = JSON.stringify(args);\n    const match", "const key = JSON.stringify(args.slice(0, 1));\n    const match").replace("byArgs.push({ key: JSON.stringify(args), behaviour", "byArgs.push({ key: JSON.stringify(args.slice(0, 1)), behaviour") + STUB_DRIVER,
    ],
    guide=G(
        prereqs="Closures, functions with properties, `Map`. Lesson *Test doubles in depth* builds a stub with a queue of answers.",
        intuition="Treat every rule as a small function that produces the answer (returning a value or throwing). The stub keeps three shelves of such functions: by call number, by arguments, and one default. A call looks on the shelves from most to least specific.",
        hints=[
            "Represent an answer as a function: `() => value` or `() => { throw new Error(message); }`. Then 'return' and 'throw' rules are handled the same way.",
            "Read the call's index from `stub.callCount` and increment it **before** producing the answer, so that a throwing call is counted.",
            "`onCall(n)` and `withArgs(...)` each return a small object with a `returns` (and `throws`) method that stores the rule.",
        ],
        brute_force="A chain of `if` statements written separately in every test does the job once. The stub object exists so that tests state the answers as data and never repeat the plumbing.",
        approach="State: `byCall` (Map from index to answer), `byArgs` (list of `{key, answer}` with `key = JSON.stringify(args)`), `fallback`. On a call: take the index, increment the count, then `byCall` → `byArgs` → `fallback`.\n\n**Dry run** of the priority test: call 0 with `(\"x\")` → index 0 has an `onCall` rule → `by call`. Call 1 with `(\"x\")` → no rule for index 1; arguments match → `by args`. Call 2 with `(\"y\")` → default.",
        complexity="O(1) for call-number and default rules; O(r) to scan r `withArgs` rules.",
        pitfalls="- Counting calls from 1 in `onCall`.\n- Letting `withArgs` or the default override an `onCall` rule.\n- Incrementing the count after producing the answer, so calls that throw are not counted.\n- Matching `withArgs` on the first argument only.",
        follow_up="Add `resolves(value)` and `rejects(message)` for promise-returning stubs, the counterparts of `mockResolvedValue` and `mockRejectedValue`.",
    ),
),
dict(
    id="jstest-mock-http", title="A function under test, a mock HTTP client", difficulty="Medium", pattern="Stubbing HTTP",
    kind="js", entry="runLoadCart",
    description=r"""
This time the double is provided and **you write the code under test**. `loadCart(http, userId)` receives an
HTTP client with one method, `http.get(url)`, which returns `{ status, body }` or **throws** when the network
is unreachable. Your function must make the right requests and turn every outcome into a result object.

1. Request `"/users/" + userId`.
   - it throws → `{ ok: false, reason: "offline" }`
   - status 404 → `{ ok: false, reason: "no such user" }`
   - any other status except 200 → `{ ok: false, reason: "server error " + status }`
2. With status 200 the body is `{ name, cartId }`. If `cartId` is `null`, the user has no cart: return
   `{ ok: true, name, total: 0 }` **without making a second request**.
3. Otherwise request `"/carts/" + cartId`.
   - it throws → `{ ok: false, reason: "offline" }`
   - status 404 → the cart has expired: `{ ok: true, name, total: 0 }`
   - any other status except 200 → `{ ok: false, reason: "server error " + status }`
   - status 200 → body `{ items: [{ price, quantity }, ...] }`; return `{ ok: true, name, total }` where
     `total` is the sum of `price * quantity`

The driver builds the mock client from a table of routes (`"down"` means the request throws; so does a URL
that is not in the table) and returns your result together with the **list of URLs you requested**, so
unnecessary or wrong requests fail the test.

**Example:** with routes `{"/users/7": {status: 200, body: {name: "Ada", cartId: "c1"}}, "/carts/c1": {status: 200, body: {items: [{price: 4, quantity: 2}, {price: 6, quantity: 1}]}}}`,
`runLoadCart(routes, 7)` → `{result: {ok: true, name: "Ada", total: 14}, requests: ["/users/7", "/carts/c1"]}`
""",
    starter="function loadCart(http, userId) {\n  // http.get(url) returns { status, body } or throws\n}\n" + HTTP_DRIVER,
    solution=HTTP_SOLUTION + HTTP_DRIVER,
    tests=[
        [{"/users/7": USER_OK, "/carts/c1": CART_OK}, 7],
        [{"/users/7": {"status": 404, "body": None}}, 7],
        [{"/users/7": {"status": 500, "body": None}}, 7],
        [{"/users/7": "down"}, 7],
        [{"/users/7": {"status": 200, "body": {"name": "Bo", "cartId": None}}}, 7],
        [{"/users/7": USER_OK, "/carts/c1": {"status": 404, "body": None}}, 7],
        [{"/users/7": USER_OK, "/carts/c1": {"status": 503, "body": None}}, 7],
        [{"/users/7": USER_OK, "/carts/c1": "down"}, 7],
        [{"/users/7": USER_OK, "/carts/c1": {"status": 200, "body": {"items": []}}}, 7],
        [{"/users/12": {"status": 200, "body": {"name": "Cy", "cartId": "k9"}}, "/carts/k9": {"status": 200, "body": {"items": [{"price": 3, "quantity": 0}, {"price": 10, "quantity": 3}]}}}, 12],
        [{"/users/7": {"status": 403, "body": {"error": "forbidden"}}}, 7],
        [{}, 99],
        [{"/users/1": {"status": 200, "body": {"name": "Di", "cartId": "c2"}}, "/carts/c2": {"status": 200, "body": {"items": [{"price": 1, "quantity": 1}, {"price": 2, "quantity": 2}, {"price": 3, "quantity": 3}]}}}, 1],
    ],
    examples=1,
    wrong_solutions=[
        "function loadCart(http, userId) {\n  try {\n    const user = http.get(\"/users/\" + userId);\n    const cart = http.get(\"/carts/\" + user.body.cartId);\n    const total = cart.body.items.reduce((s, i) => s + i.price * i.quantity, 0);\n    return { ok: true, name: user.body.name, total };\n  } catch (error) {\n    return { ok: false, reason: \"offline\" };\n  }\n}\n" + HTTP_DRIVER,
        HTTP_SOLUTION.replace("  if (cartId === null || cartId === undefined) return { ok: true, name, total: 0 };\n", "") + HTTP_DRIVER,
        HTTP_SOLUTION.replace("  if (cart.status === 404) return { ok: true, name, total: 0 };\n", "") + HTTP_DRIVER,
        HTTP_SOLUTION.replace("  if (user.status === 404) return { ok: false, reason: \"no such user\" };\n", "") + HTTP_DRIVER,
        HTTP_SOLUTION.replace("    try { return http.get(url); } catch (error) { return null; }", "    return http.get(url);") + HTTP_DRIVER,
    ],
    guide=G(
        prereqs="HTTP status codes, `try` / `catch`, `reduce`. Lesson *Stubbing HTTP requests*.",
        intuition="Two requests, and each can end in four ways: thrown, 404, another error status, or 200. Write the same small ladder of checks twice, returning early at each rung. The mock records your requests, so 'do not ask when you do not need to' is checked as well.",
        hints=[
            "Wrap each `http.get` in its own `try` / `catch`, so you know *which* request failed and nothing else is swallowed.",
            "Check the statuses in order: 404 first, then 'anything that is not 200'.",
            "Return before the second request when `cartId` is `null`.",
        ],
        brute_force="One big `try` around everything turns every problem, including a 404 and a bug in your own code, into `offline`. It passes the happy path and little else.",
        approach="A helper `tryGet(url)` returns the response or `null` when the call throws. Then: user `null` → offline; 404 → no such user; not 200 → server error; no cart id → total 0; cart `null` → offline; 404 → total 0; not 200 → server error; else sum the items.\n\n**Dry run** of the example: `/users/7` → 200, `cartId` `c1`; `/carts/c1` → 200, items `4 × 2 + 6 × 1 = 14`.",
        complexity="O(n) for n cart items; at most two requests.",
        pitfalls="- Reading `body` before checking `status`: on a 404 the body is `null` and the code crashes.\n- Requesting `/carts/null` for a user without a cart.\n- Treating the two 404s alike; a missing user is a failure, an expired cart is an empty cart.\n- A catch-all `try` that hides programming errors as `offline`.",
        follow_up="Make `http.get` return a promise and rewrite the function with `async` / `await`; the ladder of checks is unchanged. Then add one retry for 503 answers.",
    ),
),
dict(
    id="jstest-spy-on", title="Spy on a method, then put it back", difficulty="Medium", pattern="Test doubles",
    kind="js", entry="runSpyOn",
    description=r"""
Sometimes the collaborator is a real object that should keep working while the test listens in. Write
`spyOn(object, name)`, which replaces the method `object[name]` with a spy and returns that spy.

- the spy records the arguments of each call in `spy.calls`
- by default it **calls through**: it runs the original method with the same arguments and the same `this`,
  and returns its result
- `spy.returns(value)` switches to stub mode: from then on the original is no longer called and `value` is
  returned (any value, including `0` and `null`); calls are still recorded
- `spy.restore()` puts the original method back on the object

The driver uses a counter object, `{ count: 0, add(n) { this.count += n; return this.count; } }`, and runs
operations on it: `["spy"]`, `["add", n]` (calls `counter.add(n)`), `["count"]` (reads `counter.count`),
`["calls"]`, `["returns", value]`, `["restore"]` and `["isOriginal"]` (is `counter.add` the original function?).

**Example:** `runSpyOn([["add", 2], ["spy"], ["add", 3], ["calls"], ["count"]])` → `[2, "spying", 5, [[3]], 5]`
""",
    starter="function spyOn(object, name) {\n  // replace object[name] with a spy and return the spy\n}\n" + SPYON_DRIVER,
    solution=SPYON_SOLUTION + SPYON_DRIVER,
    tests=[
        [[["add", 2], ["spy"], ["add", 3], ["calls"], ["count"]]],
        [[["spy"], ["add", 1], ["add", 4], ["calls"]]],
        [[["spy"], ["isOriginal"], ["restore"], ["isOriginal"]]],
        [[["spy"], ["add", 1], ["restore"], ["add", 1], ["calls"], ["count"]]],
        [[["spy"], ["returns", 99], ["add", 5], ["count"], ["calls"]]],
        [[["spy"], ["returns", 0], ["add", 5], ["add", 6], ["count"]]],
        [[["spy"], ["returns", 99], ["restore"], ["add", 5], ["count"]]],
        [[["add", 1], ["add", 1], ["isOriginal"]]],
        [[["spy"], ["calls"], ["count"]]],
        [[["spy"], ["add", 10], ["add", -3], ["count"], ["restore"], ["count"]]],
        [[["spy"], ["returns", None], ["add", 5], ["count"], ["calls"]]],
        [[["spy"], ["add", 2], ["returns", 7], ["add", 2], ["count"], ["calls"]]],
    ],
    examples=1,
    wrong_solutions=[
        SPYON_SOLUTION.replace("original.apply(this, args)", "original(...args)") + SPYON_DRIVER,
        SPYON_SOLUTION.replace("spy.restore = () => { object[name] = original; };", "spy.restore = () => { spy.calls.length = 0; };") + SPYON_DRIVER,
        "function spyOn(object, name) {\n  const original = object[name];\n  let stubValue;\n  const spy = function (...args) {\n    spy.calls.push(args);\n    return stubValue ? stubValue : original.apply(this, args);\n  };\n  spy.calls = [];\n  spy.returns = (value) => { stubValue = value; return spy; };\n  spy.restore = () => { object[name] = original; };\n  object[name] = spy;\n  return spy;\n}\n" + SPYON_DRIVER,
        "function spyOn(object, name) {\n  const original = object[name];\n  let replacement = null;\n  const spy = function (...args) {\n    if (replacement) return replacement.value;\n    spy.calls.push(args);\n    return original.apply(this, args);\n  };\n  spy.calls = [];\n  spy.returns = (value) => { replacement = { value }; return spy; };\n  spy.restore = () => { object[name] = original; };\n  object[name] = spy;\n  return spy;\n}\n" + SPYON_DRIVER,
    ],
    guide=G(
        prereqs="`this` in method calls and `apply`; lesson *Test doubles in depth*, section on spying on a real object.",
        intuition="Swap the method for a wrapper that takes notes and then forwards the call. Keep the original in a closure variable: you need it for forwarding and for putting things back.",
        hints=[
            "Save `object[name]` before overwriting it.",
            "Forward with `original.apply(this, args)`. Inside the spy, `this` is the object the method was called on.",
            "To tell 'no stub value set' from 'stub value is `0` or `null`', store the stub value in a wrapper object or use a separate boolean.",
        ],
        brute_force="Editing the real method to log its calls works for one debugging session and has to be undone by hand. The spy does the same from outside, and `restore` is the undo.",
        approach="Closure: `original`, `replacement = null`. The spy pushes the arguments, then returns `replacement.value` if a replacement exists, else `original.apply(this, args)`. `returns` sets `replacement = { value }`; `restore` assigns `original` back.\n\n**Dry run** of the example: `add(2)` → count 2. Spy installed. `add(3)` → recorded `[3]`, original runs with `this = counter` → count 5, returns 5.",
        complexity="O(1) per call.",
        pitfalls="- Calling `original(...args)` loses `this`: the counter is not updated and the result is `NaN`.\n- `restore` that clears the records but leaves the wrapper installed.\n- Testing the stub value for truthiness, so `returns(0)` and `returns(null)` fall through to the original.\n- Not recording calls once the spy is in stub mode.",
        follow_up="Make `spyOn` refuse (throw) when `object[name]` is not a function. That check is what protects a test from a typo in a method name.",
    ),
),
dict(
    id="jstest-mock-expectations", title="A strict mock with verify", difficulty="Medium", pattern="Test doubles",
    kind="js", entry="runMock",
    description=r"""
A **mock** is told in advance which calls to expect and judges each call as it arrives. Write `createMock()`,
returning an object with three methods.

- `expect(method, args)` adds an expected call to a queue. Order matters.
- `call(method, args)` reports an actual call. If it equals the **next** expected call (same method name, and
  arguments with the same contents), that expectation is used up. Otherwise throw
  `new Error("unexpected call: " + text)`, where `text` is the method name followed by the arguments in
  parentheses, written as JSON and separated by commas: `send("a@x","Hi")`, `ping()`. A rejected call does
  **not** use up an expectation.
- `verify()` throws `new Error("missing calls: " + names)` if expected calls remain, where `names` are their
  method names joined by `", "`. Otherwise it does nothing.

The driver registers the expected calls, plays the actual calls (collecting `"ok"` or `"error: ..."`), then
calls `verify` and appends `"verified"` or the error.

**Example:** `runMock([["open", []], ["write", ["hi"]], ["close", []]], [["open", []], ["close", []], ["write", ["hi"]]])`
→ `["ok", "error: unexpected call: close()", "ok", "error: missing calls: close"]`
""",
    starter="function createMock() {\n  // return { expect(method, args), call(method, args), verify() }\n}\n" + MOCK_DRIVER,
    solution=MOCK_SOLUTION + MOCK_DRIVER,
    tests=[
        [[["open", []], ["write", ["hi"]], ["close", []]], [["open", []], ["close", []], ["write", ["hi"]]]],
        [[["send", ["a@x", "Hi"]]], [["send", ["a@x", "Hi"]]]],
        [[["send", ["a@x", "Hi"]]], []],
        [[["send", ["a@x", "Hi"]]], [["send", ["b@x", "Hi"]]]],
        [[["send", ["a@x", "Hi"]]], [["send", ["a@x", "Hi"]], ["send", ["a@x", "Hi"]]]],
        [[], []],
        [[], [["log", []]]],
        [[["ping", []], ["ping", []]], [["ping", []]]],
        [[["a", []], ["b", []], ["c", []]], [["a", []]]],
        [[["save", [{"id": 1, "tags": ["x"]}]]], [["save", [{"id": 1, "tags": ["x"]}]]]],
        [[["save", [1]]], [["remove", [1]]]],
        [[["add", [1, 2]], ["add", [3, 4]]], [["add", [3, 4]], ["add", [1, 2]], ["add", [3, 4]]]],
        [[["set", ["k", None, True]]], [["set", ["k", None, False]], ["set", ["k", None, True]]]],
    ],
    examples=1,
    wrong_solutions=[
        MOCK_SOLUTION.replace("if (queue.length > 0) throw new Error(\"missing calls: \" + queue.map((entry) => entry.method).join(\", \"));", "") + MOCK_DRIVER,
        "function createMock() {\n  const queue = [];\n  const show = (method, args) => method + \"(\" + JSON.stringify(args).slice(1, -1) + \")\";\n  return {\n    expect(method, args) { queue.push({ method, args }); },\n    call(method, args) {\n      const index = queue.findIndex((e) => e.method === method && JSON.stringify(e.args) === JSON.stringify(args));\n      if (index === -1) throw new Error(\"unexpected call: \" + show(method, args));\n      queue.splice(index, 1);\n    },\n    verify() {\n      if (queue.length > 0) throw new Error(\"missing calls: \" + queue.map((e) => e.method).join(\", \"));\n    },\n  };\n}\n" + MOCK_DRIVER,
        MOCK_SOLUTION.replace("      const next = queue[0];\n", "      const next = queue.shift();\n").replace("      queue.shift();\n", "") + MOCK_DRIVER,
        MOCK_SOLUTION.replace("if (!next || next.method !== method || JSON.stringify(next.args) !== JSON.stringify(args)) {", "if (!next || next.method !== method) {") + MOCK_DRIVER,
    ],
    guide=G(
        prereqs="The difference between a spy (records, judged afterwards) and a mock (expects, judges at once), from *Test doubles in depth*.",
        intuition="The mock is a queue of expectations. Each actual call is compared with the head of the queue: a match removes the head, anything else is an error at that moment. `verify` asks whether the queue is empty.",
        hints=[
            "Look at `queue[0]` without removing it; remove it only after the comparison succeeds.",
            "Compare arguments by content: `JSON.stringify(expected.args) === JSON.stringify(args)`.",
            "`JSON.stringify(args).slice(1, -1)` is the argument list without the surrounding brackets.",
        ],
        brute_force="Recording every call with a spy and comparing the whole list at the end gives the same verdict, but only after the code under test has finished. A mock stops at the first wrong call, which is closer to the cause.",
        approach="`expect` pushes `{method, args}`. `call` peeks at the head: missing or different → throw `unexpected call`; equal → `shift`. `verify` throws when the queue is not empty.\n\n**Dry run** of the example: `open` matches the head → ok. `close` arrives but the head is `write` → error, nothing consumed. `write` matches → ok. `verify`: `close` is still queued → `missing calls: close`.",
        complexity="O(1) per call apart from serialising the arguments; `verify` is O(remaining).",
        pitfalls="- A `verify` that never throws turns the mock into a spy nobody reads.\n- Searching the whole queue for a match makes the mock accept calls in any order.\n- Removing the head before comparing uses up an expectation on a wrong call.\n- Comparing method names only.",
        follow_up="Add `expect(method, args).returns(value)` so the mock can also answer. Then consider when strict ordering helps (protocols) and when it only makes a test brittle.",
    ),
),
]
