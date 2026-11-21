"""JavaScript testing problems: fake clocks and timers, polling, dispatching, a request handler, matchers,
retry, stale answers, module mocking and role queries."""
import json


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


CLOCK_DRIVER = r'''
// --- driver (provided, do not change) ---
function runClock(ops) {
  const clock = createClock();
  const log = [];
  const ids = {};
  return ops.map(([op, a, b, c]) => {
    if (op === "timeout") { ids[a] = clock.setTimeout(() => log.push(a + "@" + clock.now()), b); return "set"; }
    if (op === "chain") {                 // a timer that re-arms itself c more times
      let left = c;
      const fire = () => { log.push(a + "@" + clock.now()); if (left-- > 0) clock.setTimeout(fire, b); };
      ids[a] = clock.setTimeout(fire, b);
      return "set";
    }
    if (op === "canceller") {             // a timer that cancels timer c when it fires
      ids[a] = clock.setTimeout(() => { log.push(a + "@" + clock.now()); clock.clearTimeout(ids[c]); }, b);
      return "set";
    }
    if (op === "clear") { clock.clearTimeout(ids[a]); return "cleared"; }
    if (op === "tick") { log.length = 0; clock.tick(a); return [...log]; }
    if (op === "now") return clock.now();
    return null;
  });
}
'''

CLOCK_SOLUTION = r'''function createClock() {
  let now = 0, nextId = 1;
  let timers = [];
  return {
    now: () => now,
    setTimeout(callback, ms = 0) {
      const id = nextId++;
      timers.push({ id, due: now + Math.max(0, ms), callback });
      return id;
    },
    clearTimeout(id) { timers = timers.filter((timer) => timer.id !== id); },
    tick(ms) {
      const end = now + ms;
      for (;;) {
        let next = null;                                   // the earliest timer that is due within this tick
        for (const timer of timers) {
          if (timer.due > end) continue;
          if (next === null || timer.due < next.due || (timer.due === next.due && timer.id < next.id)) next = timer;
        }
        if (next === null) break;
        timers = timers.filter((timer) => timer !== next);
        now = next.due;                                    // the callback sees its own due time
        next.callback();
      }
      now = end;
    },
  };
}
'''

# A compact fake clock handed to the learner's code in the debounce and poller problems.
MAKE_CLOCK = r'''
function makeClock() {                    // a ready-made fake clock: now(), setTimeout, clearTimeout, tick
  let now = 0, nextId = 1, timers = [];
  return {
    now: () => now,
    setTimeout(cb, ms) { timers.push({ id: nextId, due: now + ms, cb }); return nextId++; },
    clearTimeout(id) { timers = timers.filter((t) => t.id !== id); },
    tick(ms) {
      const end = now + ms;
      for (;;) {
        const next = timers.filter((t) => t.due <= end).sort((a, b) => a.due - b.due || a.id - b.id)[0];
        if (!next) break;
        timers = timers.filter((t) => t !== next);
        now = next.due;
        next.cb();
      }
      now = end;
    },
  };
}
'''

DEBOUNCE_DRIVER = r'''
// --- driver (provided, do not change) ---''' + MAKE_CLOCK + r'''
function debounceWithClock(wait, ops) {
  const clock = makeClock();
  const fired = [];
  const debounced = debounce((value) => fired.push([clock.now(), value]), wait, clock);
  for (const [op, arg] of ops) {
    if (op === "call") debounced(arg);
    else if (op === "tick") clock.tick(arg);
  }
  return fired;
}
'''

DEBOUNCE_SOLUTION = r'''function debounce(fn, wait, clock) {
  let timer = null;
  return function (...args) {
    if (timer !== null) clock.clearTimeout(timer);
    timer = clock.setTimeout(() => {
      timer = null;
      fn.apply(this, args);
    }, wait);
  };
}
'''

POLLER_DRIVER = r'''
// --- driver (provided, do not change) ---''' + MAKE_CLOCK + r'''
function runPoller(interval, ops) {
  const clock = makeClock();
  const pending = [];                     // callbacks of requests that have not been answered yet
  const received = [];
  let sent = 0;
  const poller = createPoller({
    request(callbacks) { sent++; pending.push(callbacks); },
    clock,
    interval,
    onData: (data) => received.push(data),
  });
  const sentAfterEachStep = ops.map(([op, arg]) => {
    if (op === "start") poller.start();
    else if (op === "stop") poller.stop();
    else if (op === "tick") clock.tick(arg);
    else if (op === "respond") { const next = pending.shift(); if (next) next.onSuccess(arg); }
    else if (op === "fail") { const next = pending.shift(); if (next) next.onError(new Error(String(arg))); }
    return sent;
  });
  return { sentAfterEachStep, received };
}
'''

POLLER_SOLUTION = r'''function createPoller({ request, clock, interval, onData }) {
  let running = false, timer = null;
  function poll() {
    timer = null;
    request({
      onSuccess(data) { onData(data); scheduleNext(); },
      onError() { scheduleNext(); },
    });
  }
  function scheduleNext() {
    if (running) timer = clock.setTimeout(poll, interval);
  }
  return {
    start() {
      if (running) return;
      running = true;
      poll();
    },
    stop() {
      running = false;
      if (timer !== null) { clock.clearTimeout(timer); timer = null; }
    },
  };
}
'''

DISPATCH_SOLUTION = r'''function dispatch(bundle, subscriptions, lastToken) {
  const result = { token: lastToken, deliveries: [] };
  if (bundle === null || typeof bundle !== "object" || Array.isArray(bundle)) return result;
  if (bundle.token !== undefined && bundle.token !== null) result.token = String(bundle.token);
  const topics = bundle.topics;
  if (topics === null || typeof topics !== "object" || Array.isArray(topics)) return result;
  for (const topic of Object.keys(topics)) {
    if (!Array.isArray(topics[topic])) continue;
    for (const message of topics[topic]) {
      for (const [subscriber, wanted] of subscriptions) {
        if (wanted === topic) result.deliveries.push([subscriber, message]);
      }
    }
  }
  return result;
}
'''

HANDLER_DRIVER = r'''
// --- driver (provided, do not change) ---
function makeBoard() {                    // the model: your handler calls board.add and board.since
  const updates = [];
  const clean = (value, label) => {
    if (typeof value !== "string" || value.trim() === "") throw new Error(label + " is required");
    return value.trim();
  };
  return {
    add(author, text) {
      const update = { id: updates.length + 1, author: clean(author, "author"), text: clean(text, "text") };
      updates.push(update);
      return update;
    },
    since: (id) => updates.filter((update) => update.id > id),
  };
}
function runRequests(requests) {
  const board = makeBoard();
  return requests.map(([method, path, body]) => {
    try { return handle({ method, path, body: body === undefined ? "" : body }, board); }
    catch (error) { return { status: 500, body: { error: "handler crashed: " + error.message } }; }
  });
}
'''

HANDLER_SOLUTION = r'''function handle(request, board) {
  const [pathname, query = ""] = request.path.split("?");
  if (pathname !== "/updates") return { status: 404, body: { error: "not found" } };

  if (request.method === "POST") {
    let data;
    try { data = JSON.parse(request.body); }
    catch (error) { return { status: 400, body: { error: "body must be JSON" } }; }
    if (data === null || typeof data !== "object") data = {};
    try { return { status: 201, body: board.add(data.author, data.text) }; }
    catch (error) { return { status: 422, body: { error: error.message } }; }
  }

  if (request.method === "GET") {
    const since = Number(new URLSearchParams(query).get("since")) || 0;
    const updates = board.since(since);
    const token = updates.length > 0 ? updates[updates.length - 1].id : since;
    return { status: 200, body: { token, updates } };
  }

  return { status: 405, body: { error: "method not allowed" } };
}
'''

EXPECT_DRIVER = r'''
// --- driver (provided, do not change) ---
function runExpect(actual, negated, matcher, args) {
  try {
    const target = negated ? expect(actual).not : expect(actual);
    target[matcher](...args);
    return "pass";
  } catch (error) {
    return error instanceof TypeError ? "matcher missing" : "fail";
  }
}
'''

EXPECT_SOLUTION = r'''function expect(actual) {
  const deepEqual = (a, b) => {
    if (Object.is(a, b)) return true;
    if (a === null || b === null || typeof a !== "object" || typeof b !== "object") return false;
    if (Array.isArray(a) !== Array.isArray(b)) return false;
    const keysA = Object.keys(a), keysB = Object.keys(b);
    return keysA.length === keysB.length && keysA.every((key) => Object.hasOwn(b, key) && deepEqual(a[key], b[key]));
  };
  const matchers = {
    toBe: (expected) => Object.is(actual, expected),
    toEqual: (expected) => deepEqual(actual, expected),
    toContain: (item) => actual.includes(item),
    toBeCloseTo: (expected, digits = 2) => Math.abs(actual - expected) < 10 ** -digits / 2,
    toBeGreaterThan: (expected) => actual > expected,
  };
  const build = (negated) => {
    const api = {};
    for (const [name, holds] of Object.entries(matchers)) {
      api[name] = (...args) => {
        if (Boolean(holds(...args)) === negated) {
          throw new Error("expected " + JSON.stringify(actual) + (negated ? " not " : " ") + name);
        }
      };
    }
    return api;
  };
  const api = build(false);
  api.not = build(true);
  return api;
}
'''

RETRY_DRIVER = r'''
// --- driver (provided, do not change) ---
function runRetry(outcomes, attempts, baseDelay) {
  const delays = [], attemptNumbers = [];
  let calls = 0;
  const task = (attempt) => {                       // scripted: the last outcome repeats for ever
    attemptNumbers.push(attempt);
    const outcome = outcomes[Math.min(calls, outcomes.length - 1)];
    calls++;
    if (outcome.startsWith("fail:")) throw new Error(outcome.slice(5));
    return outcome.slice(3);
  };
  const sleep = (ms) => { delays.push(ms); };       // records the wait; it does not really wait
  let summary;
  try { summary = { value: retry(task, { attempts, baseDelay, sleep }) }; }
  catch (error) { summary = { error: error.message }; }
  return { ...summary, calls, delays, attemptNumbers };
}
'''

RETRY_SOLUTION = r'''function retry(task, { attempts, baseDelay, sleep }) {
  let lastError;
  for (let attempt = 1; attempt <= attempts; attempt++) {
    try {
      return task(attempt);
    } catch (error) {
      lastError = error;
      if (attempt < attempts) sleep(baseDelay * 2 ** (attempt - 1));
    }
  }
  throw lastError;
}
'''

LATEST_DRIVER = r'''
// --- driver (provided, do not change) ---
function runLatest(ops) {
  const shown = [];
  const begin = createLatestOnly((result) => shown.push(result));
  const finishers = {};
  for (const [op, name, result] of ops) {
    if (op === "begin") finishers[name] = begin();
    else if (op === "finish" && finishers[name]) finishers[name](result);
  }
  return shown;
}
'''

LATEST_SOLUTION = r'''function createLatestOnly(show) {
  let latest = 0;
  return function begin() {
    const ticket = ++latest;                 // this request's number
    let delivered = false;
    return function finish(result) {
      if (delivered || ticket !== latest) return;
      delivered = true;
      show(result);
    };
  };
}
'''

REGISTRY_DRIVER = r'''
// --- driver (provided, do not change) ---
function runRegistry(ops) {
  const registry = createRegistry();
  let loads = 0;
  return ops.map(([op, name, deps]) => {
    try {
      if (op === "define") {
        registry.define(name, deps, (...parts) => { loads++; return name + "(" + parts.join(",") + ")"; });
        return "defined";
      }
      if (op === "mock") { registry.mock(name, "mock:" + name); return "mocked"; }
      if (op === "require") return registry.require(name);
      if (op === "reset") { registry.reset(); return "reset"; }
      if (op === "loads") return loads;
      return null;
    } catch (error) { return "error: " + error.message; }
  });
}
'''

REGISTRY_SOLUTION = r'''function createRegistry() {
  const definitions = new Map();
  let cache = new Map(), mocks = new Map();
  const registry = {
    define(name, deps, factory) { definitions.set(name, { deps, factory }); },
    mock(name, value) { mocks.set(name, value); },
    require(name) {
      if (mocks.has(name)) return mocks.get(name);
      if (cache.has(name)) return cache.get(name);
      const definition = definitions.get(name);
      if (!definition) throw new Error("unknown module: " + name);
      const value = definition.factory(...definition.deps.map((dep) => registry.require(dep)));
      cache.set(name, value);
      return value;
    },
    reset() { cache = new Map(); mocks = new Map(); },
  };
  return registry;
}
'''

ROLE_SOLUTION = r'''function getByRole(tree, role, name) {
  const roleOf = (node) => {
    const attrs = node.attrs || {};
    if (attrs.role) return attrs.role;
    if (node.tag === "button") return "button";
    if (node.tag === "a") return attrs.href !== undefined ? "link" : null;
    if (node.tag === "input") return attrs.type === "checkbox" ? "checkbox" : "textbox";
    if (["h1", "h2", "h3", "h4", "h5", "h6"].includes(node.tag)) return "heading";
    if (node.tag === "ul" || node.tag === "ol") return "list";
    if (node.tag === "li") return "listitem";
    return null;
  };
  const textOf = (node) => [node.text || "", ...(node.children || []).map(textOf)]
    .map((part) => part.trim()).filter((part) => part !== "").join(" ");
  const nameOf = (node) => {
    const label = (node.attrs || {})["aria-label"];
    return label ? label.trim() : textOf(node);
  };
  const matches = [];
  const visit = (node) => {
    if (roleOf(node) === role && (name === null || name === undefined || nameOf(node) === name)) matches.push(node);
    for (const child of node.children || []) visit(child);
  };
  visit(tree);
  if (matches.length === 0) return "error: no match";
  if (matches.length > 1) return "error: multiple matches";
  const id = (matches[0].attrs || {}).id;
  return id === undefined ? null : id;
}
'''

FORM = {"tag": "form", "attrs": {"id": "f"}, "children": [
    {"tag": "h2", "attrs": {"id": "title"}, "text": "Sign in"},
    {"tag": "input", "attrs": {"id": "email", "type": "email", "aria-label": "Email"}},
    {"tag": "input", "attrs": {"id": "remember", "type": "checkbox", "aria-label": "Remember me"}},
    {"tag": "button", "attrs": {"id": "submit"}, "text": "Sign in"},
    {"tag": "button", "attrs": {"id": "cancel"}, "children": [{"tag": "span", "text": "Cancel"}, {"tag": "span", "text": " and go back "}]},
    {"tag": "div", "attrs": {"id": "fake", "class": "btn"}, "text": "Forgot password"},
    {"tag": "div", "attrs": {"id": "real", "role": "button"}, "text": "Help me"},
    {"tag": "a", "attrs": {"id": "docs", "href": "/docs"}, "text": "Docs"},
    {"tag": "a", "attrs": {"id": "anchor"}, "text": "Not a link"},
    {"tag": "ul", "attrs": {"id": "list"}, "children": [
        {"tag": "li", "attrs": {"id": "i1"}, "text": "One"},
        {"tag": "li", "attrs": {"id": "i2"}, "text": "Two"}]},
]}

POST_ADA = json.dumps({"author": "Ada", "text": "Deployed v2"})
POST_BO = json.dumps({"author": "Bo", "text": "Fixed login"})
POST_CY = json.dumps({"author": "  Cy ", "text": " Released  "})

PROBLEMS = [
dict(
    id="jstest-fake-clock", title="Build a fake clock", difficulty="Medium", pattern="Fake timers",
    kind="js", entry="runClock",
    description=r"""
Tests must not wait in real time. Write the tool that makes that possible: `createClock()`, returning an
object with

- `now()`: the current fake time in milliseconds, starting at `0`
- `setTimeout(callback, ms)`: schedules `callback` to run once, `ms` after the current fake time, and returns an id
- `clearTimeout(id)`: cancels that timer; an unknown or already fired id is ignored
- `tick(ms)`: moves the fake time forward by `ms`, running every timer that falls due on the way

Rules for `tick`:

1. timers run in order of their due time; timers due at the same moment run in the order they were created
2. while a callback runs, `now()` equals **that timer's due time**
3. a callback may schedule new timers; if a new timer is due within the span being ticked, it runs in the same `tick`
4. a callback may cancel a timer that has not run yet
5. when `tick` returns, `now()` is the start time plus `ms`

The driver schedules labelled timers whose callbacks log `label@time`. `["chain", label, ms, n]` creates a
timer that schedules itself again `n` more times; `["canceller", label, ms, other]` creates a timer that cancels
timer `other` when it runs. Each `["tick", ms]` returns the log entries produced during that tick.

**Example:** `runClock([["timeout", "b", 200], ["timeout", "a", 100], ["tick", 150], ["tick", 50], ["now"]])` →
`["set", "set", ["a@100"], ["b@200"], 200]`
""",
    starter="function createClock() {\n  // return { now(), setTimeout(callback, ms), clearTimeout(id), tick(ms) }\n}\n" + CLOCK_DRIVER,
    solution=CLOCK_SOLUTION + CLOCK_DRIVER,
    tests=[
        [[["timeout", "b", 200], ["timeout", "a", 100], ["tick", 150], ["tick", 50], ["now"]]],
        [[["timeout", "a", 100], ["tick", 99], ["tick", 1], ["now"]]],
        [[["timeout", "x", 50], ["timeout", "y", 50], ["timeout", "z", 50], ["tick", 50]]],
        [[["timeout", "a", 100], ["timeout", "b", 100], ["clear", "a"], ["tick", 100]]],
        [[["chain", "p", 100, 2], ["tick", 350], ["now"]]],
        [[["chain", "p", 100, 5], ["tick", 250], ["tick", 250]]],
        [[["timeout", "soon", 0], ["tick", 0]]],
        [[["tick", 1000], ["timeout", "late", 50], ["tick", 49], ["tick", 1], ["now"]]],
        [[["timeout", "victim", 200], ["canceller", "c", 100, "victim"], ["tick", 300]]],
        [[["chain", "i", 30, 3], ["timeout", "t", 75], ["tick", 100]]],
        [[["timeout", "a", 10], ["tick", 10], ["clear", "a"], ["clear", "nope"], ["tick", 10], ["now"]]],
        [[["tick", 500], ["now"]]],
        [[["chain", "z", 0, 3], ["tick", 0], ["now"]]],
        [[["timeout", "c", 30], ["timeout", "a", 10], ["timeout", "b", 20], ["timeout", "a2", 10], ["tick", 25], ["tick", 5]]],
    ],
    examples=1,
    wrong_solutions=[
        "function createClock() {\n  let now = 0, nextId = 1, timers = [];\n  return {\n    now: () => now,\n    setTimeout(callback, ms = 0) { timers.push({ id: nextId, due: now + ms, callback }); return nextId++; },\n    clearTimeout(id) { timers = timers.filter((t) => t.id !== id); },\n    tick(ms) {\n      const end = now + ms;\n      for (;;) {\n        const next = timers.find((t) => t.due <= end);\n        if (!next) break;\n        timers = timers.filter((t) => t !== next);\n        now = next.due;\n        next.callback();\n      }\n      now = end;\n    },\n  };\n}\n" + CLOCK_DRIVER,
        "function createClock() {\n  let now = 0, nextId = 1, timers = [];\n  return {\n    now: () => now,\n    setTimeout(callback, ms = 0) { timers.push({ id: nextId, due: now + ms, callback }); return nextId++; },\n    clearTimeout(id) { timers = timers.filter((t) => t.id !== id); },\n    tick(ms) {\n      const end = now + ms;\n      const due = timers.filter((t) => t.due <= end).sort((a, b) => a.due - b.due || a.id - b.id);\n      timers = timers.filter((t) => t.due > end);\n      for (const t of due) { now = t.due; t.callback(); }\n      now = end;\n    },\n  };\n}\n" + CLOCK_DRIVER,
        CLOCK_SOLUTION.replace("        now = next.due;                                    // the callback sees its own due time\n", "") + CLOCK_DRIVER,
        CLOCK_SOLUTION.replace("      now = end;\n    },", "    },") + CLOCK_DRIVER,
    ],
    guide=G(
        prereqs="`setTimeout` and `clearTimeout`; closures. Lesson *Polling a server and testing time with a fake clock* explains a clock like this line by line.",
        intuition="A fake clock is a number and a list. `setTimeout` appends an entry with its due time; `tick` repeatedly picks the earliest entry that is due, sets the time to it, removes it and calls it. Choosing **one timer at a time** is what makes rules 3 and 4 come out right.",
        hints=[
            "Store `{ id, due, callback }` per timer, with `due = now + ms`.",
            "In `tick`, loop: find the timer with the smallest `due` that is `<= end` (smallest id on a tie). None left → stop.",
            "Remove the timer from the list *before* calling it, set `now` to its due time, and only at the very end set `now` to the end of the tick.",
        ],
        brute_force="Advancing one millisecond at a time and firing whatever is due at each step is correct and takes time proportional to the span ticked. Jumping from timer to timer is proportional to the number of timers.",
        approach="`end = now + ms`. Repeat: pick the earliest due timer within `end`; if none, break; remove it; `now = due`; call it. Finally `now = end`.\n\n**Dry run** `chain p every 100, tick(350)`: p due 100 → runs, schedules itself for 200 → loop finds it (200 ≤ 350) → runs, schedules 300 → runs, no more. `now` becomes 350. Log: `p@100, p@200, p@300`.",
        complexity="With a plain list each pick is O(t) for t waiting timers, so a tick that fires k timers costs O(k · t). A priority queue would make each pick O(log t).",
        pitfalls="- Running timers in the order they were created, not in order of due time.\n- Collecting all due timers up front: timers scheduled by a callback are missed, and a cancelled timer still runs.\n- Leaving `now` at the start of the tick while callbacks run.\n- Forgetting to advance `now` when no timer was due.",
        follow_up="Add `setInterval` and `clearInterval` (a repeating timer is re-queued with `due += period`), and a `runAll()` that keeps going until no timers remain. Why can `runAll` loop for ever?",
    ),
),
dict(
    id="jstest-debounce-clock", title="Debounce, driven by a fake clock", difficulty="Medium", pattern="Fake timers",
    kind="js", entry="debounceWithClock",
    description=r"""
Write `debounce(fn, wait, clock)`. It returns a function that postpones calling `fn` until `wait` milliseconds
have passed **without another call**. A burst of calls therefore produces a single call of `fn`, with the
arguments of the **last** call in the burst.

Timing must go through the `clock` argument, which has `setTimeout(callback, ms)` (returns an id),
`clearTimeout(id)` and `now()`. Do not use the global timer functions: the judge cannot wait in real time, and
neither should a test.

The driver gives your function a ready-made fake clock. Each `["call", value]` calls the debounced function,
each `["tick", ms]` moves the clock. It returns every real call of `fn` as `[time, value]`.

**Example:** `debounceWithClock(300, [["call", "h"], ["tick", 100], ["call", "he"], ["tick", 100], ["call", "hel"], ["tick", 300]])`
→ `[[500, "hel"]]`
""",
    starter="function debounce(fn, wait, clock) {\n  // use clock.setTimeout and clock.clearTimeout\n}\n" + DEBOUNCE_DRIVER,
    solution=DEBOUNCE_SOLUTION + DEBOUNCE_DRIVER,
    tests=[
        [300, [["call", "h"], ["tick", 100], ["call", "he"], ["tick", 100], ["call", "hel"], ["tick", 300]]],
        [300, [["call", "a"], ["tick", 299]]],
        [300, [["call", "a"], ["tick", 300]]],
        [300, [["call", "a"], ["tick", 299], ["call", "ab"], ["tick", 299], ["tick", 1]]],
        [300, [["call", "first"], ["tick", 300], ["call", "second"], ["tick", 300]]],
        [100, [["tick", 1000]]],
        [0, [["call", "x"], ["tick", 0]]],
        [50, [["call", 1], ["call", 2], ["call", 3], ["tick", 50]]],
        [100, [["call", "a"], ["tick", 50], ["call", "b"], ["tick", 50], ["call", "c"], ["tick", 50], ["call", "d"], ["tick", 100], ["call", "e"], ["tick", 100]]],
        [100, [["call", "a"], ["tick", 100], ["call", "b"], ["tick", 99]]],
        [10, [["call", {"q": "x"}], ["tick", 10]]],
        [200, [["call", "a"], ["tick", 150], ["call", "b"], ["tick", 150], ["call", "c"], ["tick", 150], ["tick", 50]]],
    ],
    examples=1,
    wrong_solutions=[
        "function debounce(fn, wait, clock) {\n  return function (...args) {\n    clock.setTimeout(() => fn.apply(this, args), wait);\n  };\n}\n" + DEBOUNCE_DRIVER,
        "function debounce(fn, wait, clock) {\n  let timer = null;\n  return function (...args) {\n    if (timer !== null) return;\n    timer = clock.setTimeout(() => { timer = null; fn.apply(this, args); }, wait);\n  };\n}\n" + DEBOUNCE_DRIVER,
        "function debounce(fn, wait, clock) {\n  let last = -Infinity;\n  return function (...args) {\n    if (clock.now() - last >= wait) { last = clock.now(); fn.apply(this, args); }\n  };\n}\n" + DEBOUNCE_DRIVER,
        "function debounce(fn, wait, clock) {\n  let timer = null, firstArgs = null;\n  return function (...args) {\n    if (firstArgs === null) firstArgs = args;\n    if (timer !== null) clock.clearTimeout(timer);\n    timer = clock.setTimeout(() => { timer = null; const a = firstArgs; firstArgs = null; fn.apply(this, a); }, wait);\n  };\n}\n" + DEBOUNCE_DRIVER,
    ],
    guide=G(
        prereqs="Closures, timers, injecting a clock. The interview lesson works through this exact exercise.",
        intuition="Keep one pending timer. Every call throws the pending timer away and starts a fresh one. Only a timer that survives `wait` milliseconds without being replaced gets to call `fn`.",
        hints=[
            "The timer id lives in a closure variable shared by all calls.",
            "On each call: clear the previous timer if there is one, then set a new one.",
            "The new timer's callback captures this call's arguments, so the surviving timer has the last arguments.",
        ],
        brute_force="Recording the time of the last call and checking it from a repeating interval works, but it fires late by up to one interval and needs a timer running all the time.",
        approach="`let timer = null`. Returned function: `if (timer !== null) clock.clearTimeout(timer); timer = clock.setTimeout(() => { timer = null; fn(...args); }, wait);`\n\n**Dry run** of the example: call at 0 → timer due 300. Call at 100 → cleared, new timer due 400. Call at 200 → cleared, new timer due 500. Tick to 500 → fires once with `hel`.",
        complexity="O(1) per call.",
        pitfalls="- Not clearing the old timer: `fn` runs once per call, only later.\n- Ignoring calls while a timer is pending: the wait is not restarted and the *first* arguments are used.\n- Calling `fn` immediately and then blocking for `wait`: that is a leading-edge throttle, a different tool.\n- Using the global `setTimeout`, which the test cannot control.",
        follow_up="Add `debounced.cancel()` and `debounced.flush()`, and an option to fire on the leading edge. Then write `throttle(fn, interval, clock)` and state the difference in one sentence.",
    ),
),
dict(
    id="jstest-poller", title="A poller that waits for the answer", difficulty="Medium", pattern="Polling",
    kind="js", entry="runPoller",
    description=r"""
Write `createPoller({ request, clock, interval, onData })`, returning `{ start(), stop() }`.

- `request(callbacks)` starts one request. Later, exactly one of `callbacks.onSuccess(data)` or
  `callbacks.onError(error)` is called by the outside world.
- `clock` has `setTimeout(callback, ms)` and `clearTimeout(id)`.

Behaviour:

1. `start()` makes the first request immediately. Calling `start()` while already running does nothing.
2. The next request is made `interval` milliseconds **after the previous one was answered**, whether it
   succeeded or failed. While a request is unanswered, no other request is made, however much time passes.
3. A successful answer is passed to `onData(data)`.
4. `stop()` cancels the scheduled next request. If an answer arrives after `stop()`, its data is still
   passed to `onData`, but **no further request is scheduled**.
5. After `stop()`, `start()` begins again with an immediate request.

The driver plays the server: `["respond", data]` answers the oldest unanswered request successfully,
`["fail", text]` answers it with an error, `["tick", ms]` moves the clock. It returns how many requests had
been sent after each step, and everything `onData` received.

**Example:** `runPoller(1000, [["start"], ["tick", 5000], ["respond", "a"], ["tick", 999], ["tick", 1]])` →
`{sentAfterEachStep: [1, 1, 1, 1, 2], received: ["a"]}`
""",
    starter="function createPoller({ request, clock, interval, onData }) {\n  // return { start(), stop() }\n}\n" + POLLER_DRIVER,
    solution=POLLER_SOLUTION + POLLER_DRIVER,
    tests=[
        [1000, [["start"], ["tick", 5000], ["respond", "a"], ["tick", 999], ["tick", 1]]],
        [1000, [["start"]]],
        [500, [["start"], ["respond", 1], ["tick", 500], ["respond", 2], ["tick", 500], ["respond", 3]]],
        [1000, [["start"], ["fail", "503"], ["tick", 1000]]],
        [1000, [["start"], ["respond", "a"], ["stop"], ["tick", 5000]]],
        [1000, [["start"], ["stop"], ["respond", "late"], ["tick", 5000]]],
        [1000, [["start"], ["start"], ["respond", "a"], ["tick", 1000]]],
        [1000, [["start"], ["respond", "a"], ["stop"], ["start"], ["respond", "b"], ["tick", 1000]]],
        [1000, [["tick", 5000], ["stop"]]],
        [1000, [["start"], ["tick", 900], ["respond", "a"], ["tick", 900], ["tick", 100]]],
        [200, [["start"], ["fail", "x"], ["tick", 200], ["fail", "y"], ["tick", 200], ["respond", "ok"], ["tick", 199], ["tick", 1]]],
        [1000, [["start"], ["respond", "a"], ["tick", 1000], ["stop"], ["respond", "b"], ["tick", 3000]]],
    ],
    examples=1,
    wrong_solutions=[
        "function createPoller({ request, clock, interval, onData }) {\n  let running = false, timer = null;\n  function poll() {\n    request({ onSuccess(data) { onData(data); }, onError() {} });\n    if (running) timer = clock.setTimeout(poll, interval);\n  }\n  return {\n    start() { if (running) return; running = true; poll(); },\n    stop() { running = false; if (timer !== null) { clock.clearTimeout(timer); timer = null; } },\n  };\n}\n" + POLLER_DRIVER,
        POLLER_SOLUTION.replace("if (running) timer = clock.setTimeout(poll, interval);", "timer = clock.setTimeout(poll, interval);") + POLLER_DRIVER,
        POLLER_SOLUTION.replace("      if (running) return;\n", "") + POLLER_DRIVER,
        POLLER_SOLUTION.replace("onError() { scheduleNext(); },", "onError() {},") + POLLER_DRIVER,
    ],
    guide=G(
        prereqs="Callbacks, a fake clock, the chained-timeout pattern. Lesson *Polling a server and testing time with a fake clock* test-drives this object.",
        intuition="The poller is a loop spread over time: request, wait for the answer, wait for the interval, repeat. Two pieces of state control it: a `running` flag, and the id of the timer for the next round (if one is waiting).",
        hints=[
            "Schedule the next request from inside the success and error handlers, never right after sending.",
            "`stop` must do two things: clear the pending timer, and set a flag so that a late answer does not schedule anything.",
            "`start` checks the flag first, so a second `start` cannot create a second loop.",
        ],
        brute_force="`setInterval(request, interval)` is the first idea. It keeps sending while earlier requests are unanswered, so a slow server ends up with a pile of overlapping requests.",
        approach="`poll()` sends a request whose handlers call `scheduleNext()`. `scheduleNext()` sets a timer for `poll` only when `running` is true. `start()` sets the flag and polls; `stop()` clears the flag and the timer.\n\n**Dry run** of the example: `start` → request 1. Five seconds pass with no answer → still 1. Answer `a` → `onData`, timer at +1000. After 999 ms → still 1; one more → request 2.",
        complexity="O(1) work per event.",
        pitfalls="- Scheduling the next round when the request is *sent*: requests overlap on a slow server.\n- `stop` that only clears the timer: a request in flight comes back and restarts the loop.\n- No guard in `start`: two loops, twice the traffic.\n- Giving up after an error; a poller should keep trying.",
        follow_up="If `stop()` and `start()` are called while a request is still unanswered, the old answer will schedule a second loop. Fix that with a generation counter, then add exponential backoff after errors.",
    ),
),
dict(
    id="jstest-topic-dispatcher", title="Dispatch a bundle of messages by topic", difficulty="Medium", pattern="Streaming",
    kind="js", entry="dispatch",
    description=r"""
One long-poll connection carries messages for many parts of a page. Each answer from the server is a **bundle**:

```
{ "token": "42", "topics": { "price": [ ...messages ], "news": [ ...messages ] } }
```

Write the pure function `dispatch(bundle, subscriptions, lastToken)`.

- `subscriptions` is a list of `[subscriber, topic]` pairs
- return `{ token, deliveries }`, where `deliveries` is the list of `[subscriber, message]` pairs to deliver

Order of deliveries: topics in the order they appear in the bundle; within a topic, messages in order; for
each message, subscribers in the order of the `subscriptions` list.

The returned `token` is `String(bundle.token)` when the bundle has a token (any value except `null` or missing,
so `0` counts), otherwise `lastToken` unchanged.

Data from a network cannot be trusted, so the function must never throw:

- a bundle that is not a plain object (`null`, a string, a number, an array) → nothing delivered, token unchanged
- `topics` missing or not a plain object → nothing delivered (the token is still updated)
- a topic whose value is not an array is skipped; other topics are still delivered

**Example:** `dispatch({token: 7, topics: {price: [101], news: ["x"]}}, [["a", "news"], ["b", "price"], ["c", "news"]], "1")` →
`{token: "7", deliveries: [["b", 101], ["a", "x"], ["c", "x"]]}`
""",
    starter="function dispatch(bundle, subscriptions, lastToken) {\n  // return { token, deliveries }\n}\n",
    solution=DISPATCH_SOLUTION,
    tests=[
        [{"token": 7, "topics": {"price": [101], "news": ["x"]}}, [["a", "news"], ["b", "price"], ["c", "news"]], "1"],
        [{"token": "42", "topics": {"news": [{"t": "A"}, {"t": "B"}]}}, [["w1", "news"]], ""],
        [None, [["a", "news"]], "5"],
        ["<html>502 Bad Gateway</html>", [["a", "news"]], "5"],
        [{"token": "9", "topics": None}, [["a", "news"]], "5"],
        [{"token": "9", "topics": {"news": "not a list", "price": [1, 2]}}, [["a", "news"], ["b", "price"]], "5"],
        [{"token": "3", "topics": {"sports": ["goal"]}}, [["a", "news"]], "2"],
        [{"topics": {"news": ["n1"]}}, [["a", "news"]], "keep"],
        [{"token": "8", "topics": {}}, [["a", "news"]], "7"],
        [{"token": "8", "topics": {"news": ["n"], "price": [5]}}, [["a", "news"], ["a", "price"]], "7"],
        [[{"token": "1"}], [["a", "news"]], "0"],
        [{"token": 0, "topics": {"t": [None, 0, "", False]}}, [["s", "t"]], "9"],
        [{"token": None, "topics": {"news": ["n"]}}, [], "9"],
        [42, [["a", "news"]], "5"],
        [{"token": "5", "topics": ["news"]}, [["a", "news"]], "4"],
    ],
    examples=1,
    wrong_solutions=[
        DISPATCH_SOLUTION.replace("if (bundle.token !== undefined && bundle.token !== null) result.token = String(bundle.token);", "if (bundle.token) result.token = String(bundle.token);"),
        "function dispatch(bundle, subscriptions, lastToken) {\n  const deliveries = [];\n  for (const topic of Object.keys(bundle.topics)) {\n    for (const message of bundle.topics[topic]) {\n      for (const [subscriber, wanted] of subscriptions) if (wanted === topic) deliveries.push([subscriber, message]);\n    }\n  }\n  return { token: String(bundle.token), deliveries };\n}\n",
        "function dispatch(bundle, subscriptions, lastToken) {\n  const result = { token: lastToken, deliveries: [] };\n  if (bundle === null || typeof bundle !== \"object\" || Array.isArray(bundle)) return result;\n  if (bundle.token !== undefined && bundle.token !== null) result.token = String(bundle.token);\n  const topics = bundle.topics;\n  if (topics === null || typeof topics !== \"object\" || Array.isArray(topics)) return result;\n  for (const [subscriber, wanted] of subscriptions) {\n    if (!Array.isArray(topics[wanted])) continue;\n    for (const message of topics[wanted]) result.deliveries.push([subscriber, message]);\n  }\n  return result;\n}\n",
        DISPATCH_SOLUTION.replace("    if (!Array.isArray(topics[topic])) continue;\n", ""),
    ],
    guide=G(
        prereqs="Objects as dictionaries, `Array.isArray`, `typeof`. Lesson *Long polling, streaming and one connection for many topics*.",
        intuition="Three nested loops (topics, messages, subscribers) with a guard in front of each level. The guards are the real work: every assumption about the shape of the data is checked before it is used.",
        hints=[
            "Start with the result for the worst case: `{ token: lastToken, deliveries: [] }`, and return it from every guard.",
            "`typeof null` is `\"object\"` and arrays are objects too, so a plain-object check needs three conditions.",
            "Update the token before looking at `topics`, and test for `null`/`undefined` explicitly so that `0` survives.",
        ],
        brute_force="Looping over the subscriptions and looking up each one's topic gives the same pairs in a different order: grouped by subscriber, not by arrival. The order is part of the contract here.",
        approach="Guard the bundle; update the token; guard `topics`; for each topic key whose value is an array, for each message, for each subscription with that topic, push `[subscriber, message]`.\n\n**Dry run** of the example: topic `price` → message `101` → subscriber `b`. Topic `news` → message `x` → subscribers `a`, then `c`. Token `7` becomes `\"7\"`.",
        complexity="O(m · s) for m messages and s subscriptions. Grouping the subscriptions by topic first makes it O(m + s + deliveries).",
        pitfalls="- No guards: the first malformed bundle throws and the feed stops.\n- `if (bundle.token)` drops a token of `0`.\n- Iterating a topic whose value is a string delivers its characters one by one.\n- Treating an array as a bundle or as `topics`.",
        follow_up="Wrap this function in an object that remembers the token, sends it with the next request (`?since=token`) and hands each delivery to the subscriber's callback inside a `try`, so one failing subscriber cannot block the others.",
    ),
),
dict(
    id="jstest-request-handler", title="A request handler you can test without a server", difficulty="Medium", pattern="Node service",
    kind="js", entry="runRequests",
    description=r"""
Write the controller of a tiny status-board service as a plain function, so that it can be tested by passing
objects in. `handle(request, board)` receives `request = { method, path, body }` (the body is a string) and
returns `{ status, body }` (the body is an object).

`board` is the model, provided by the driver: `board.add(author, text)` stores an update and returns
`{ id, author, text }`, or **throws** an `Error` such as `"text is required"`; `board.since(id)` returns the
updates with a larger id.

Routing: split `path` at `?` into a path name and a query string. Only the path name `/updates` exists.

| Request | Response |
|---|---|
| any other path name | `404`, `{ error: "not found" }` |
| `POST /updates`, body is not valid JSON | `400`, `{ error: "body must be JSON" }` |
| `POST /updates`, `board.add(data.author, data.text)` throws | `422`, `{ error: <the error's message> }` |
| `POST /updates`, stored | `201`, the stored update |
| `GET /updates?since=N` | `200`, `{ token, updates }` |
| any other method on `/updates` | `405`, `{ error: "method not allowed" }` |

Details: if the parsed JSON is not an object (for example `null` or `42`), treat it as `{}`. For `GET`, `since`
is the number in the query string, or `0` when it is missing or not a number; `updates` is `board.since(since)`;
`token` is the id of the last update returned, or `since` itself when there is none.

The driver sends a list of `[method, path, body]` requests to one fresh board and returns the responses. A
handler that throws shows up as status `500`.

**Example:** `runRequests([["POST", "/updates", "{\"author\":\"Ada\",\"text\":\"Deployed v2\"}"], ["GET", "/updates"]])` →
`[{status: 201, body: {id: 1, author: "Ada", text: "Deployed v2"}}, {status: 200, body: {token: 1, updates: [{id: 1, author: "Ada", text: "Deployed v2"}]}}]`
""",
    starter="function handle(request, board) {\n  // request: { method, path, body }   return { status, body }\n}\n" + HANDLER_DRIVER,
    solution=HANDLER_SOLUTION + HANDLER_DRIVER,
    tests=[
        [[["POST", "/updates", POST_ADA], ["GET", "/updates"]]],
        [[["GET", "/updates"]]],
        [[["POST", "/updates", POST_ADA], ["POST", "/updates", POST_BO], ["POST", "/updates", POST_CY], ["GET", "/updates?since=1"]]],
        [[["POST", "/updates", POST_ADA], ["POST", "/updates", POST_BO], ["GET", "/updates?since=5"]]],
        [[["POST", "/updates", "author=Ada"], ["POST", "/updates", ""]]],
        [[["POST", "/updates", json.dumps({"author": "Ada"})], ["POST", "/updates", json.dumps({"author": "   ", "text": "x"})]]],
        [[["GET", "/nope"], ["POST", "/updates/1", POST_ADA], ["DELETE", "/elsewhere"]]],
        [[["DELETE", "/updates"], ["PUT", "/updates", POST_ADA]]],
        [[["POST", "/updates", json.dumps({"text": "no author"})], ["POST", "/updates", POST_ADA], ["GET", "/updates?since=0"]]],
        [[["POST", "/updates", "null"], ["POST", "/updates", "42"]]],
        [[["POST", "/updates", POST_ADA], ["POST", "/updates", POST_BO], ["GET", "/updates?x=1&since=1"], ["GET", "/updates?since=abc"]]],
        [[["POST", "/updates", POST_CY]]],
        [[["POST", "/updates?since=3", POST_ADA], ["GET", "/updates?since=1"]]],
    ],
    examples=1,
    wrong_solutions=[handler + HANDLER_DRIVER for handler in [
        HANDLER_SOLUTION.replace("    try { data = JSON.parse(request.body); }\n    catch (error) { return { status: 400, body: { error: \"body must be JSON\" } }; }", "    data = JSON.parse(request.body);"),
        "function handle(request, board) {\n  const [pathname, query = \"\"] = request.path.split(\"?\");\n  if (request.method !== \"POST\" && request.method !== \"GET\") return { status: 405, body: { error: \"method not allowed\" } };\n  if (pathname !== \"/updates\") return { status: 404, body: { error: \"not found\" } };\n  if (request.method === \"POST\") {\n    let data;\n    try { data = JSON.parse(request.body); } catch (error) { return { status: 400, body: { error: \"body must be JSON\" } }; }\n    if (data === null || typeof data !== \"object\") data = {};\n    try { return { status: 201, body: board.add(data.author, data.text) }; } catch (error) { return { status: 422, body: { error: error.message } }; }\n  }\n  const since = Number(new URLSearchParams(query).get(\"since\")) || 0;\n  const updates = board.since(since);\n  return { status: 200, body: { token: updates.length > 0 ? updates[updates.length - 1].id : since, updates } };\n}\n",
        HANDLER_SOLUTION.replace("const since = Number(new URLSearchParams(query).get(\"since\")) || 0;", "const since = 0;"),
        HANDLER_SOLUTION.replace("const token = updates.length > 0 ? updates[updates.length - 1].id : since;", "const token = updates.length;"),
        HANDLER_SOLUTION.replace("    if (data === null || typeof data !== \"object\") data = {};\n", ""),
    ]],
    guide=G(
        prereqs="HTTP methods and status codes, `JSON.parse`, `try` / `catch`, `URLSearchParams`. Lesson *Test-driving a small Node HTTP service*.",
        intuition="A controller is a translator. On the way in it turns a method, a path and a body into a call on the model; on the way out it turns the model's result, or its error, into a status code and a body. Each row of the table is one `return`.",
        hints=[
            "Decide the path first: anything that is not `/updates` is a 404, whatever the method.",
            "Use two separate `try` blocks in the POST branch: one for `JSON.parse` (400), one for `board.add` (422).",
            "`new URLSearchParams(query).get(\"since\")` reads the parameter; `Number(...) || 0` covers both missing and non-numeric.",
        ],
        brute_force="One `try` around the whole function with a generic 500 answer never crashes, but the client cannot tell bad JSON from a rule violation from a bug.",
        approach="1. Split the path. 2. Unknown path → 404. 3. POST: parse (400 on failure), normalise non-objects to `{}`, add (422 on failure), else 201. 4. GET: read `since`, fetch, compute the token, 200. 5. Anything else → 405.\n\n**Dry run** `POST /updates` with `{\"author\":\"Ada\"}`: path ok; JSON parses; `board.add(\"Ada\", undefined)` throws `text is required` → `422` with that message.",
        complexity="O(u) for a GET that returns u updates; O(1) otherwise.",
        pitfalls="- `JSON.parse` without `try`: a malformed body crashes the handler.\n- Checking the method before the path: `DELETE /elsewhere` should be 404, not 405.\n- Reading `data.author` when `data` is `null`.\n- Returning the number of updates as the token; the client needs the last id it has seen.",
        follow_up="Wire it to a real server: `createServer((req, res) => ...)` collects the body from `data` and `end` events, calls `handle`, and writes the status and `JSON.stringify(body)`. Keep that file free of decisions.",
    ),
),
dict(
    id="jstest-matchers", title="expect, five matchers and .not", difficulty="Medium", pattern="Matchers",
    kind="js", entry="runExpect",
    description=r"""
Build a miniature of the assertion interface used by Jest and Vitest. `expect(actual)` returns an object with
these **matchers**. A matcher returns nothing when its fact holds and throws an `Error` (any message) when it
does not.

| Matcher | Holds when |
|---|---|
| `toBe(x)` | `Object.is(actual, x)` |
| `toEqual(x)` | `actual` and `x` have the same contents: nested arrays and plain objects, key order ignored |
| `toContain(item)` | `actual` (an array or a string) includes `item` |
| `toBeCloseTo(x, digits)` | `Math.abs(actual - x) < 10 ** -digits / 2`; `digits` defaults to `2` |
| `toBeGreaterThan(x)` | `actual > x` |

The object also has a property **`not`** holding the same five matchers with the outcome inverted:
`expect(1).not.toBe(2)` returns quietly, `expect(1).not.toBe(1)` throws.

The driver calls one matcher and returns `"pass"` if it returned normally, or `"fail"` if it threw.

**Examples:** `runExpect(0.30000000000000004, false, "toBeCloseTo", [0.3])` → `"pass"` ·
`runExpect({a: 1}, false, "toBe", [{a: 1}])` → `"fail"` · `runExpect([1, 2, 3], true, "toContain", [5])` → `"pass"`
""",
    starter="function expect(actual) {\n  // return { toBe, toEqual, toContain, toBeCloseTo, toBeGreaterThan, not: { ...the same, inverted } }\n}\n" + EXPECT_DRIVER,
    solution=EXPECT_SOLUTION + EXPECT_DRIVER,
    tests=[
        [0.30000000000000004, False, "toBeCloseTo", [0.3]],
        [{"a": 1}, False, "toBe", [{"a": 1}]],
        [[1, 2, 3], True, "toContain", [5]],
        [1, False, "toBe", [1]],
        [1, False, "toBe", ["1"]],
        [1, True, "toBe", ["1"]],
        [{"a": 1, "b": [1, 2]}, False, "toEqual", [{"b": [1, 2], "a": 1}]],
        [{"a": 1}, True, "toEqual", [{"a": 1}]],
        [[1, 2, 3], False, "toContain", [2]],
        ["hello world", False, "toContain", ["lo w"]],
        [0.30000000000000004, False, "toBe", [0.3]],
        [0.3, False, "toBeCloseTo", [0.31]],
        [0.3, False, "toBeCloseTo", [0.31, 1]],
        [5, False, "toBeGreaterThan", [5]],
        [{"a": [1, {"b": 2}]}, False, "toEqual", [{"a": [1, {"b": 3}]}]],
    ],
    examples=3,
    wrong_solutions=[
        EXPECT_SOLUTION.replace("api.not = build(true);", "api.not = build(false);") + EXPECT_DRIVER,
        EXPECT_SOLUTION.replace("toEqual: (expected) => deepEqual(actual, expected),", "toEqual: (expected) => actual === expected,") + EXPECT_DRIVER,
        EXPECT_SOLUTION.replace("toEqual: (expected) => deepEqual(actual, expected),", "toEqual: (expected) => JSON.stringify(actual) === JSON.stringify(expected),") + EXPECT_DRIVER,
        EXPECT_SOLUTION.replace("Math.abs(actual - expected) < 10 ** -digits / 2", "Math.abs(actual - expected) < 0.005") + EXPECT_DRIVER,
        EXPECT_SOLUTION.replace("toBe: (expected) => Object.is(actual, expected),", "toBe: (expected) => actual == expected,") + EXPECT_DRIVER,
    ],
    guide=G(
        prereqs="Throwing errors, closures, deep comparison of nested data. Lesson *Vitest, Jest and node:test in daily use* shows how matchers are built.",
        intuition="Write each matcher as a small function that answers true or false. Then one wrapper turns any of them into an assertion: throw when the answer is not the wanted one. `not` is the same wrapper with the wanted answer flipped.",
        hints=[
            "Put the five true/false functions in one object, keyed by matcher name.",
            "Write `build(negated)`, which loops over that object and creates, for each name, a function that throws when `Boolean(result) === negated`.",
            "`toEqual` needs a recursive comparison: same kind (array or object), same number of keys, and equal values for each key.",
        ],
        brute_force="Writing ten separate functions, five plain and five negated, works and repeats the throw logic ten times. Adding a sixth matcher then means editing two places.",
        approach="`const api = build(false); api.not = build(true); return api;`.\n\n**Dry run** `expect({a: 1}).toBe({a: 1})`: two different objects, `Object.is` is false, wanted true → throw → `fail`. With `toEqual` the contents match → `pass`. `expect(0.3).toBeCloseTo(0.31)`: the difference `0.01` is not below `0.005` → `fail`; with `digits = 1` the limit is `0.05` → `pass`.",
        complexity="`toEqual` is O(n) in the size of the values; the others are O(1) or one `includes` scan.",
        pitfalls="- A `not` that returns the same matchers un-inverted.\n- `toEqual` with `===` (identity) or with `JSON.stringify` (fails when the keys are in a different order).\n- A fixed tolerance in `toBeCloseTo` that ignores `digits`.\n- `==` in `toBe`, which makes `1` equal `\"1\"`.",
        follow_up="Add `expect.extend({ name: predicate })` to register more matchers at run time, and make the error message show the expected value as well.",
    ),
),
dict(
    id="jstest-retry", title="Retry with backoff and an injected sleep", difficulty="Medium", pattern="Retry",
    kind="js", entry="runRetry",
    description=r"""
Write `retry(task, { attempts, baseDelay, sleep })`.

- call `task(attempt)` with the attempt number, starting at `1`
- if it returns, return that value at once
- if it throws and attempts remain, call `sleep(delay)` and try again; the delay doubles each time:
  `baseDelay` after the first failure, `2 * baseDelay` after the second, `4 * baseDelay` after the third, ...
- if the last allowed attempt throws, throw that same error, **without** sleeping first
- `attempts` is at least 1 and counts all calls of `task`, including the first

The waiting function is passed in, which is what makes the helper testable: the test hands over a `sleep` that
records the requested delays. (The production version is `async` and awaits both `task` and `sleep`. The judge
runs synchronously, so here they are ordinary functions; the logic is identical.)

The driver scripts the task from `outcomes` such as `["fail:timeout", "ok:done"]` (the last entry repeats) and
returns `{ value | error, calls, delays, attemptNumbers }`.

**Example:** `runRetry(["fail:a", "fail:b", "ok:done"], 3, 100)` →
`{value: "done", calls: 3, delays: [100, 200], attemptNumbers: [1, 2, 3]}`
""",
    starter="function retry(task, { attempts, baseDelay, sleep }) {\n  // your code\n}\n" + RETRY_DRIVER,
    solution=RETRY_SOLUTION + RETRY_DRIVER,
    tests=[
        [["fail:a", "fail:b", "ok:done"], 3, 100],
        [["ok:done"], 3, 100],
        [["fail:a", "ok:done"], 3, 100],
        [["fail:a", "fail:b", "fail:c"], 3, 100],
        [["fail:x"], 1, 100],
        [["fail:x"], 5, 10],
        [["fail:a", "fail:b", "fail:c", "ok:late"], 3, 100],
        [["fail:a", "fail:b", "fail:c", "ok:late"], 4, 50],
        [["ok:first", "fail:never"], 3, 100],
        [["fail:a", "ok:b"], 2, 0],
        [["fail:a", "ok:b"], 2, 7],
        [["fail:1", "fail:2", "fail:3", "fail:4", "fail:5", "ok:6"], 6, 1],
    ],
    examples=1,
    wrong_solutions=[
        RETRY_SOLUTION.replace("if (attempt < attempts) sleep(", "sleep(") + RETRY_DRIVER,
        RETRY_SOLUTION.replace("2 ** (attempt - 1)", "2 ** attempt") + RETRY_DRIVER,
        RETRY_SOLUTION.replace("  throw lastError;\n", "") + RETRY_DRIVER,
        RETRY_SOLUTION.replace("sleep(baseDelay * 2 ** (attempt - 1))", "sleep(baseDelay)") + RETRY_DRIVER,
        RETRY_SOLUTION.replace("for (let attempt = 1; attempt <= attempts; attempt++)", "for (let attempt = 1; attempt <= attempts + 1; attempt++)").replace("if (attempt < attempts) sleep", "if (attempt <= attempts) sleep") + RETRY_DRIVER,
    ],
    guide=G(
        prereqs="Loops with `try` / `catch`, exponentiation, dependency injection. Lesson *Promises, timers and async code under test* builds the async version.",
        intuition="A `for` loop over the attempt numbers with a `try` inside. Success leaves the function through `return`. Failure remembers the error and, unless this was the last attempt, waits. After the loop there is only one thing left to do: throw what was remembered.",
        hints=[
            "`return task(attempt)` inside the `try` ends everything on success.",
            "The delay after attempt number `n` is `baseDelay * 2 ** (n - 1)`.",
            "Guard the sleep with `attempt < attempts`, so there is no wait after the final failure.",
        ],
        brute_force="Calling the task in a `while (true)` loop without a limit retries for ever against a server that is down. The limit and the growing delay are what make retrying polite.",
        approach="Loop `attempt` from 1 to `attempts`. Try the task; on success return. On failure store the error and sleep if attempts remain. After the loop, `throw lastError`.\n\n**Dry run** `[fail a, fail b, ok done]`, 3 attempts, base 100: attempt 1 fails → sleep 100. Attempt 2 fails → sleep 200. Attempt 3 returns `done`. Delays `[100, 200]`.",
        complexity="O(attempts) calls; total waiting is at most `baseDelay * (2 ** (attempts - 1) - 1)`.",
        pitfalls="- Sleeping after the last failure delays the error for nothing.\n- `2 ** attempt` starts the delays at twice the base.\n- Forgetting to throw at the end: the caller receives `undefined` and treats a failure as success.\n- Counting retries instead of attempts, which makes one call too many.",
        follow_up="Add a maximum delay (a cap), a random jitter from an injected `random` function, and a predicate `shouldRetry(error)` so that a 404 is not retried but a timeout is.",
    ),
),
dict(
    id="jstest-latest-wins", title="Only the latest request may show its result", difficulty="Medium", pattern="Async races",
    kind="js", entry="runLatest",
    description=r"""
A search box sends a request per keystroke. Answers can come back in any order, and an answer to an **older**
request must never overwrite the screen. Write the guard.

`createLatestOnly(show)` returns a function `begin`. Each call of `begin()` marks the start of a new request
and returns a function `finish(result)` to be called when that request's answer arrives.

- `finish(result)` calls `show(result)` only if **no later `begin()` has happened** since its own
- otherwise it does nothing: the request is stale, even if the newer request has not been answered yet
- each `finish` delivers at most once; calling it a second time does nothing

The driver starts requests by name and finishes them in a given order: `["begin", name]`,
`["finish", name, result]`. It returns everything that was shown.

**Examples:**
`runLatest([["begin", "ca"], ["begin", "cat"], ["finish", "cat", "CAT"], ["finish", "ca", "CA"]])` → `["CAT"]` ·
`runLatest([["begin", "ca"], ["begin", "cat"], ["finish", "ca", "CA"]])` → `[]`
""",
    starter="function createLatestOnly(show) {\n  // return begin, where begin() returns finish(result)\n}\n" + LATEST_DRIVER,
    solution=LATEST_SOLUTION + LATEST_DRIVER,
    tests=[
        [[["begin", "ca"], ["begin", "cat"], ["finish", "cat", "CAT"], ["finish", "ca", "CA"]]],
        [[["begin", "ca"], ["begin", "cat"], ["finish", "ca", "CA"]]],
        [[["begin", "a"], ["finish", "a", "A"]]],
        [[["begin", "a"], ["begin", "b"], ["finish", "a", "A"], ["finish", "b", "B"]]],
        [[["begin", "a"], ["finish", "a", "A"], ["begin", "b"], ["finish", "b", "B"]]],
        [[["begin", "a"], ["finish", "a", "A"], ["finish", "a", "again"]]],
        [[["begin", "a"], ["begin", "b"], ["begin", "c"], ["finish", "c", "C"], ["finish", "b", "B"], ["finish", "a", "A"]]],
        [[["begin", "a"], ["finish", "a", "A"], ["begin", "b"], ["finish", "a", "late"], ["finish", "b", "B"]]],
        [[]],
        [[["begin", "a"], ["finish", "a", "A"], ["begin", "b"], ["begin", "c"], ["finish", "b", "B"], ["finish", "c", "C"]]],
        [[["begin", "a"], ["finish", "a", 0], ["begin", "b"], ["finish", "b", None]]],
        [[["begin", "a"], ["begin", "b"], ["begin", "c"], ["finish", "a", "A"], ["finish", "b", "B"]]],
    ],
    examples=2,
    wrong_solutions=[
        "function createLatestOnly(show) {\n  return function begin() {\n    let delivered = false;\n    return function finish(result) { if (delivered) return; delivered = true; show(result); };\n  };\n}\n" + LATEST_DRIVER,
        "function createLatestOnly(show) {\n  let started = 0, lastShown = 0;\n  return function begin() {\n    const ticket = ++started;\n    let delivered = false;\n    return function finish(result) {\n      if (delivered || ticket < lastShown) return;\n      delivered = true;\n      lastShown = ticket;\n      show(result);\n    };\n  };\n}\n" + LATEST_DRIVER,
        LATEST_SOLUTION.replace("if (delivered || ticket !== latest) return;", "if (ticket !== latest) return;") + LATEST_DRIVER,
        "function createLatestOnly(show) {\n  let latest = 0;\n  return function begin() {\n    latest++;\n    let delivered = false;\n    return function finish(result) {\n      const ticket = latest;\n      if (delivered || ticket !== latest) return;\n      delivered = true;\n      show(result);\n    };\n  };\n}\n" + LATEST_DRIVER,
    ],
    guide=G(
        prereqs="Closures capturing a value at the time a function is created. Lesson *Promises, timers and async code under test*, section on out-of-order answers.",
        intuition="Give every request a ticket number when it starts, and keep the newest number in a shared variable. When an answer arrives, compare its ticket with the newest: equal means current, anything else means stale.",
        hints=[
            "One counter is shared by all requests (it lives in the outer closure).",
            "Each `begin()` increments the counter and remembers the new value in its own closure.",
            "`finish` compares the remembered ticket with the counter **at the time the answer arrives**.",
        ],
        brute_force="Remembering the ticket of the last result *shown* and refusing older ones stops overwriting, but it still shows the old answer first when the old one arrives before the new one. Staleness is about which request was started last.",
        approach="`let latest = 0`. `begin`: `const ticket = ++latest; let delivered = false;` and return `finish`. `finish`: return if delivered or `ticket !== latest`; otherwise mark delivered and show.\n\n**Dry run** of the second example: `ca` gets ticket 1, `cat` ticket 2. The answer for `ca` arrives: `1 !== 2` → dropped. Nothing is shown, which is right: the user is waiting for `cat`.",
        complexity="O(1) per call.",
        pitfalls="- Showing every answer: the last one to *arrive* wins, whichever request it belongs to.\n- Comparing with the last ticket shown instead of the last ticket started.\n- Reading the counter inside `finish` instead of capturing it in `begin`: every answer then looks current.\n- No once-only guard, so a duplicated callback shows twice.",
        follow_up="Cancel the older request as well, with `AbortController`, to save bandwidth. The guard is still needed, because an answer may already be on its way when you abort.",
    ),
),
dict(
    id="jstest-module-registry", title="A module registry with mocks", difficulty="Medium", pattern="Module mocking",
    kind="js", entry="runRegistry",
    description=r"""
`vi.mock` and `jest.mock` work by changing what a module loader hands out. Build a small loader to see why the
**order** of mocking and loading matters.

`createRegistry()` returns an object with

- `define(name, deps, factory)`: registers a module. `deps` is a list of module names; `factory(...exports)`
  receives the exports of those dependencies, in order, and returns this module's export.
- `require(name)`: returns the module's export.
  - if the name has been **mocked**, return the mock value (the factory does not run)
  - otherwise, the first time, load the dependencies with `require`, run the factory **once**, remember the
    result (the **cache**) and return it; later calls return the remembered export without running the factory
  - a name that is neither defined nor mocked: throw `new Error("unknown module: " + name)`
- `mock(name, value)`: from now on `require(name)` returns `value`. Modules that were **already loaded** keep
  the exports they were built with; a mock does not reach back into them.
- `reset()`: forgets all loaded exports and all mocks (definitions stay), like starting a new test file.

In the driver every factory returns the text `name(dep1,dep2,...)` built from its dependencies' exports, and a
mock of `x` is the text `mock:x`. `["loads"]` reports how many factories have run so far.

**Example:** `runRegistry([["define", "mailer", []], ["define", "signup", ["mailer"]], ["require", "signup"], ["mock", "mailer"], ["require", "signup"], ["reset"], ["mock", "mailer"], ["require", "signup"]])`
→ `["defined", "defined", "signup(mailer())", "mocked", "signup(mailer())", "reset", "mocked", "signup(mock:mailer)"]`
""",
    starter="function createRegistry() {\n  // return { define(name, deps, factory), require(name), mock(name, value), reset() }\n}\n" + REGISTRY_DRIVER,
    solution=REGISTRY_SOLUTION + REGISTRY_DRIVER,
    tests=[
        [[["define", "mailer", []], ["define", "signup", ["mailer"]], ["require", "signup"], ["mock", "mailer"], ["require", "signup"], ["reset"], ["mock", "mailer"], ["require", "signup"]]],
        [[["define", "mailer", []], ["define", "signup", ["mailer"]], ["require", "signup"]]],
        [[["define", "mailer", []], ["define", "signup", ["mailer"]], ["mock", "mailer"], ["require", "signup"], ["loads"]]],
        [[["define", "mailer", []], ["define", "signup", ["mailer"]], ["require", "signup"], ["mock", "mailer"], ["require", "mailer"], ["require", "signup"]]],
        [[["define", "a", []], ["require", "a"], ["require", "a"], ["require", "a"], ["loads"]]],
        [[["define", "a", []], ["define", "b", ["a"]], ["define", "c", ["b", "a"]], ["require", "c"], ["loads"]]],
        [[["require", "nope"]]],
        [[["define", "x", ["missing"]], ["require", "x"], ["loads"]]],
        [[["mock", "ghost"], ["require", "ghost"], ["define", "user", ["ghost"]], ["require", "user"]]],
        [[["define", "a", []], ["require", "a"], ["reset"], ["require", "a"], ["loads"]]],
        [[["define", "base", []], ["define", "left", ["base"]], ["define", "right", ["base"]], ["define", "top", ["left", "right"]], ["require", "top"], ["loads"]]],
        [[["define", "a", []], ["mock", "a"], ["require", "a"], ["reset"], ["require", "a"], ["loads"]]],
    ],
    examples=1,
    wrong_solutions=[
        REGISTRY_SOLUTION.replace("      if (cache.has(name)) return cache.get(name);\n", "") + REGISTRY_DRIVER,
        REGISTRY_SOLUTION.replace("      if (mocks.has(name)) return mocks.get(name);\n      if (cache.has(name)) return cache.get(name);", "      if (cache.has(name)) return cache.get(name);\n      if (mocks.has(name)) return mocks.get(name);") + REGISTRY_DRIVER,
        REGISTRY_SOLUTION.replace("reset() { cache = new Map(); mocks = new Map(); },", "reset() { mocks = new Map(); },") + REGISTRY_DRIVER,
        REGISTRY_SOLUTION.replace("      if (!definition) throw new Error(\"unknown module: \" + name);\n", "      if (!definition) return undefined;\n") + REGISTRY_DRIVER,
        REGISTRY_SOLUTION.replace("mock(name, value) { mocks.set(name, value); },", "mock(name, value) { mocks.set(name, value); cache = new Map(); },") + REGISTRY_DRIVER,
    ],
    guide=G(
        prereqs="`Map`, recursion, closures. Lesson *Mocking modules, globals and fetch* builds a similar loader and shows the 'mock arrives too late' bug.",
        intuition="Three tables: what is *defined* (recipes), what is *cached* (finished dishes), what is *mocked* (substitutes). `require` consults them in a fixed order: substitute first, then finished dish, then cook from the recipe and keep the result.",
        hints=[
            "`require` is recursive: loading a module means requiring each of its dependencies first.",
            "Store the factory's result in the cache before returning it, so the factory runs once.",
            "A module that is already in the cache was built with the exports its dependencies had *then*. Mocking later changes the mock table only.",
        ],
        brute_force="Running the factory on every `require` needs no cache and gives every caller a fresh copy, which is slow and wrong: two modules sharing a dependency would no longer share its state.",
        approach="`require(name)`: mocked → return the mock. Cached → return it. Not defined → throw. Otherwise map the dependencies through `require`, call the factory with the results, cache, return. `reset` replaces the cache and the mock table with empty ones.\n\n**Dry run** of the example: `signup` loads `mailer()` and becomes `signup(mailer())`, cached. Mocking `mailer` now does not touch that cached text. After `reset` and a new mock, `signup` is rebuilt and receives `mock:mailer`.",
        complexity="Each module's factory runs at most once per reset; a `require` of a loaded module is O(1).",
        pitfalls="- No cache: factories run repeatedly (watch the `loads` counter).\n- Checking the cache before the mocks: a module that was loaded earlier can no longer be mocked directly.\n- A `reset` that keeps the cache: the next test still sees modules built with the old mocks.\n- Clearing the cache inside `mock`: convenient, but it is not how real loaders behave, which is exactly why runners hoist mock calls to the top of the file.",
        follow_up="Detect circular dependencies and throw a clear error. Then add `unmock(name)` and an automatic mock that copies a real export's function names.",
    ),
),
dict(
    id="jstest-get-by-role", title="getByRole on a tree of elements", difficulty="Medium", pattern="Testing Library",
    kind="js", entry="getByRole",
    description=r"""
Testing Library finds elements the way assistive technology does: by **role** and **accessible name**.
Implement a simplified `getByRole(tree, role, name)` over a page given as nested objects:

```
{ tag: "button", attrs: { id: "save" }, text: "Save", children: [ ... ] }
```

`attrs`, `text` and `children` are optional.

**Role of a node**

- `attrs.role`, if present, wins
- otherwise by tag: `button` → `"button"`; `a` → `"link"` only when it has an `href` attribute;
  `input` → `"checkbox"` when `attrs.type` is `"checkbox"`, else `"textbox"`; `h1` to `h6` → `"heading"`;
  `ul` and `ol` → `"list"`; `li` → `"listitem"`
- every other tag (`div`, `span`, `form`, ...) has no role

**Accessible name of a node**

- `attrs["aria-label"]`, trimmed, if it is present and not empty
- otherwise the node's own `text` followed by the texts of all its descendants in document order, each
  trimmed, empty ones dropped, joined with single spaces

**Result**

Search the whole tree including its root for nodes with the given role and, unless `name` is `null`, exactly
that name. If there is exactly one, return its `attrs.id` (or `null` if it has none). Return
`"error: no match"` for none and `"error: multiple matches"` for more than one.

**Example:** in a form containing `<button id="submit">Sign in</button>` and
`<div id="fake" class="btn">Forgot password</div>`, `getByRole(form, "button", "Sign in")` → `"submit"`, while
`getByRole(form, "button", "Forgot password")` → `"error: no match"`: a styled `div` is not a button.
""",
    starter="function getByRole(tree, role, name) {\n  // your code\n}\n",
    solution=ROLE_SOLUTION,
    tests=[
        [FORM, "button", "Sign in"],
        [FORM, "button", "Forgot password"],
        [FORM, "heading", "Sign in"],
        [FORM, "button", "Help me"],
        [FORM, "button", None],
        [FORM, "textbox", "Email"],
        [FORM, "checkbox", "Remember me"],
        [FORM, "button", "Cancel and go back"],
        [FORM, "link", None],
        [FORM, "listitem", "Two"],
        [FORM, "listitem", None],
        [FORM, "list", "One Two"],
        [{"tag": "button", "attrs": {"id": "solo"}, "text": "  Go  "}, "button", "Go"],
        [{"tag": "div", "children": [{"tag": "button", "attrs": {"id": "x", "aria-label": "Close"}, "text": "X"}]}, "button", "Close"],
        [{"tag": "div", "children": [{"tag": "button", "text": "No id here"}]}, "button", "No id here"],
    ],
    examples=2,
    wrong_solutions=[
        ROLE_SOLUTION.replace("    if (attrs.role) return attrs.role;\n", ""),
        ROLE_SOLUTION.replace("const textOf = (node) => [node.text || \"\", ...(node.children || []).map(textOf)]", "const textOf = (node) => [node.text || \"\"]"),
        ROLE_SOLUTION.replace("  if (matches.length > 1) return \"error: multiple matches\";\n", ""),
        ROLE_SOLUTION.replace("if (node.tag === \"a\") return attrs.href !== undefined ? \"link\" : null;", "if (node.tag === \"a\") return \"link\";"),
        ROLE_SOLUTION.replace("return label ? label.trim() : textOf(node);", "return textOf(node);"),
    ],
    guide=G(
        prereqs="Recursion over a tree; the idea of roles and accessible names from the lesson *Component and end-to-end tests: Testing Library and Playwright*.",
        intuition="Three small functions and one walk. `roleOf(node)` and `nameOf(node)` answer questions about a single node; `textOf(node)` gathers text from a subtree; the walk visits every node and collects the ones whose role and name match.",
        hints=[
            "Write `roleOf` as a chain of `if` statements that return early, with the explicit `role` attribute first.",
            "`textOf` is recursive: the node's own text, then `textOf` of each child, with empty pieces filtered out before joining.",
            "Collect all matches in an array first, then decide between zero, one and many.",
        ],
        brute_force="Flattening the tree into a list and filtering it works equally well and is a fine first version; the recursive walk avoids building the list.",
        approach="Visit each node depth-first. A node matches when `roleOf(node) === role` and (`name` is `null` or `nameOf(node) === name`). Afterwards: 0 matches → `error: no match`; more than 1 → `error: multiple matches`; else the id.\n\n**Dry run** `getByRole(form, \"button\", \"Cancel and go back\")`: the `cancel` button has no own text; its two `span` children give `Cancel` and `and go back` after trimming, joined to `Cancel and go back` → match → `cancel`.",
        complexity="O(n · d) in the worst case for n nodes of depth d, because names are recomputed from subtrees; O(n) if names are only computed for nodes whose role already matches.",
        pitfalls="- Ignoring the explicit `role` attribute, or giving every `a` the link role.\n- Building the name from the node's own text only; real buttons often wrap their text in child elements.\n- Returning the first match when several exist. The real `getByRole` throws in that case, because the test is ambiguous.\n- Forgetting `aria-label`, which overrides the visible text.",
        follow_up="Add `queryByRole` (returns `null` for no match) and `getAllByRole` (returns every match), and make the error message list the roles and names that *are* on the page, as the real library does.",
    ),
),
]
