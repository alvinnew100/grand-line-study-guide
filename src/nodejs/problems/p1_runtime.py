"""Node.js problems, part 1: the event loop, npm version ranges, modules, events and promisification."""


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


def t(id, type, delay=None, then=None):
    d = {"id": id, "type": type}
    if delay is not None:
        d["delay"] = delay
    if then:
        d["then"] = then
    return d


FLAT_SOLUTION = r'''function loopOrder(tasks) {
  const pick = (type) => tasks.filter((task) => task.type === type);
  const timers = pick("timer").map((task, index) => ({ id: task.id, due: Math.max(1, task.delay || 0), index }));
  timers.sort((a, b) => a.due - b.due || a.index - b.index);
  const early = [...pick("sync"), ...pick("tick"), ...pick("micro"), ...pick("immediate")];
  return early.map((task) => task.id).concat(timers.map((timer) => timer.id));
}
'''

NESTED_SOLUTION = r'''function simulateLoop(tasks) {
  const out = [], ticks = [], micros = [], timers = [], immediates = [];
  let now = 0, seq = 0;

  function schedule(list) {
    for (const task of list || []) {
      if (task.type === "sync") run(task);
      else if (task.type === "tick") ticks.push(task);
      else if (task.type === "micro") micros.push(task);
      else if (task.type === "immediate") immediates.push(task);
      else timers.push({ task, due: now + Math.max(1, task.delay || 0), seq: seq++ });
    }
  }
  function run(task) {
    out.push(task.id);
    schedule(task.then);
  }
  function drain() {
    while (ticks.length > 0 || micros.length > 0) {
      while (ticks.length > 0) run(ticks.shift());
      while (micros.length > 0) run(micros.shift());
    }
  }

  schedule(tasks);
  drain();
  while (timers.length > 0 || immediates.length > 0) {
    if (immediates.length === 0) {
      const first = Math.min(...timers.map((timer) => timer.due));
      if (first > now) now = first;
    }
    const due = timers.filter((timer) => timer.due <= now).sort((a, b) => a.due - b.due || a.seq - b.seq);
    for (const timer of due) {
      timers.splice(timers.indexOf(timer), 1);
      run(timer.task);
      drain();
    }
    const batch = immediates.splice(0);
    for (const task of batch) {
      run(task);
      drain();
    }
  }
  return out;
}
'''

SEMVER_SOLUTION = r'''function satisfies(version, range) {
  const parse = (text) => text.split(".").map(Number);
  const compare = (a, b) => {
    for (let i = 0; i < 3; i++) if (a[i] !== b[i]) return a[i] < b[i] ? -1 : 1;
    return 0;
  };
  const v = parse(version);
  const between = (low, high) => compare(v, low) >= 0 && compare(v, high) < 0;

  function test(comparator) {
    if (comparator === "*") return true;
    if (comparator.startsWith("^")) {
      const base = parse(comparator.slice(1));
      const high = base[0] > 0 ? [base[0] + 1, 0, 0] : base[1] > 0 ? [0, base[1] + 1, 0] : [0, 0, base[2] + 1];
      return between(base, high);
    }
    if (comparator.startsWith("~")) {
      const base = parse(comparator.slice(1));
      return between(base, [base[0], base[1] + 1, 0]);
    }
    const match = /^(>=|<=|>|<|=)?(.+)$/.exec(comparator);
    const op = match[1] || "=";
    const parts = match[2].split(".");
    if (parts[1] === "x") return v[0] === Number(parts[0]);
    if (parts[2] === "x") return v[0] === Number(parts[0]) && v[1] === Number(parts[1]);
    const d = compare(v, parse(match[2]));
    if (op === ">=") return d >= 0;
    if (op === "<=") return d <= 0;
    if (op === ">") return d > 0;
    if (op === "<") return d < 0;
    return d === 0;
  }

  return range.split("||").some((alternative) => alternative.trim().split(/\s+/).every(test));
}
'''

RESOLVE_SOLUTION = r'''function resolveModule(files, mains, from, spec) {
  const core = ["fs", "path", "http", "events", "stream", "util"];
  if (spec.startsWith("node:")) return "core:" + spec.slice(5);
  if (core.includes(spec)) return "core:" + spec;

  const have = new Set(files);
  const normalise = (path) => {
    const out = [];
    for (const part of path.split("/")) {
      if (part === "" || part === ".") continue;
      if (part === "..") out.pop();
      else out.push(part);
    }
    return "/" + out.join("/");
  };
  const dirname = (path) => {
    const cut = path.lastIndexOf("/");
    return cut <= 0 ? "/" : path.slice(0, cut);
  };
  const asFile = (x) => [x, x + ".js", x + ".json"].find((candidate) => have.has(candidate)) || null;
  const asDirectory = (x) => {
    const main = have.has(x + "/package.json") ? mains[x + "/package.json"] : undefined;
    if (main) {
      const target = normalise(x + "/" + main);
      const hit = asFile(target) || (have.has(target + "/index.js") ? target + "/index.js" : null);
      if (hit) return hit;
    }
    return [x + "/index.js", x + "/index.json"].find((candidate) => have.has(candidate)) || null;
  };
  const load = (x) => asFile(x) || asDirectory(x);

  if (spec.startsWith("./") || spec.startsWith("../") || spec.startsWith("/")) {
    return load(normalise(spec.startsWith("/") ? spec : dirname(from) + "/" + spec));
  }
  let dir = dirname(from);
  while (true) {
    const hit = load(normalise(dir + "/node_modules/" + spec));
    if (hit) return hit;
    if (dir === "/") return null;
    dir = dirname(dir);
  }
}
'''

CYCLE_SOLUTION = r'''function runModules(modules, entry) {
  const cache = new Map();
  const out = [];

  function requireModule(name) {
    if (cache.has(name)) return cache.get(name).exports;
    const mod = { exports: {} };
    cache.set(name, mod);              // cached BEFORE the body runs
    const local = new Map();
    out.push("start:" + name);
    for (const [op, a, b] of modules[name]) {
      if (op === "set") mod.exports[a] = b;
      else if (op === "replace") mod.exports = { ...a };
      else if (op === "require") local.set(a, requireModule(a));
      else if (op === "read") {
        let shown = "unbound";
        if (local.has(a)) {
          const value = local.get(a)[b];
          shown = value === undefined ? "undefined" : JSON.stringify(value);
        }
        out.push(name + ":" + a + "." + b + "=" + shown);
      }
    }
    out.push("end:" + name);
    return mod.exports;
  }

  requireModule(entry);
  return out;
}
'''

EMITTER_SOLUTION = r'''function runEmitter(ops) {
  const registry = new Map();
  const results = [];
  const listenersOf = (event) => {
    if (!registry.has(event)) registry.set(event, []);
    return registry.get(event);
  };
  for (const [op, event, arg] of ops) {
    const listeners = listenersOf(event);
    if (op === "on" || op === "once") {
      listeners.push({ id: arg, once: op === "once" });
      results.push(listeners.length);
    } else if (op === "off") {
      for (let i = listeners.length - 1; i >= 0; i--) {
        if (listeners[i].id === arg) { listeners.splice(i, 1); break; }
      }
      results.push(listeners.length);
    } else if (op === "count") {
      results.push(listeners.length);
    } else if (op === "emit") {
      if (event === "error" && listeners.length === 0) { results.push("throw:" + arg); continue; }
      const called = [];
      for (const listener of listeners.slice()) {
        if (listener.once) listeners.splice(listeners.indexOf(listener), 1);
        called.push(listener.id + ":" + arg);
      }
      results.push(called);
    }
  }
  return results;
}
'''

PROMISIFY_SOLUTION = r'''function promisifyOutcome(steps, multiArgs) {
  let outcome = { state: "pending" };
  const settle = (next) => {
    if (outcome.state === "pending") outcome = next;   // a promise settles once
  };
  for (const step of steps) {
    if ("throw" in step) {
      settle({ state: "rejected", reason: step.throw });
      break;                                           // nothing runs after a throw
    }
    const [err, ...values] = step.cb;
    if (err) settle({ state: "rejected", reason: err });
    else if (multiArgs) settle({ state: "fulfilled", value: values });
    else settle({ state: "fulfilled", value: values.length > 0 ? values[0] : null });
  }
  return outcome;
}
'''

PROBLEMS = [
dict(
    id="node-event-loop-flat", title="Event loop order: one flat script", difficulty="Easy", pattern="Event loop",
    kind="js", entry="loopOrder",
    description=r"""
A Node.js script schedules several pieces of work **directly from the main script** (nothing is nested).
Each entry of `tasks` is `{id, type}` and `type` is one of:

| type | Node call it stands for |
|---|---|
| `"sync"` | an ordinary statement such as `console.log(id)` |
| `"tick"` | `process.nextTick(() => log(id))` |
| `"micro"` | `Promise.resolve().then(() => log(id))` |
| `"timer"` | `setTimeout(() => log(id), delay)` (the entry also has `delay` in ms) |
| `"immediate"` | `setImmediate(() => log(id))` |

Return the ids in the order they are logged, using this **model** of Node (CommonJS script):

1. The main script runs to the end first, so every `sync` id is logged in listing order.
2. Then the whole `nextTick` queue runs (listing order), then the whole promise microtask queue (listing order).
3. The event loop starts at virtual time 0. A timer's delay is at least 1 ms (`0` is treated as `1`), so no timer is due yet; the loop reaches the check phase and runs every `immediate` in listing order.
4. Finally timers fire in order of their delay (after the minimum of 1 is applied). Timers with the same delay fire in listing order.

**Example:** `[{id:"A",type:"timer",delay:0},{id:"B",type:"immediate"},{id:"C",type:"micro"},{id:"D",type:"tick"},{id:"E",type:"sync"}]` → `["E","D","C","B","A"]`

In real Node the race between `setTimeout(fn, 0)` and `setImmediate` from the main script depends on how fast the process starts; rule 3 fixes one outcome so the answer is deterministic.
""",
    starter="function loopOrder(tasks) {\n  // return the ids in logging order\n}\n",
    solution=FLAT_SOLUTION,
    tests=[
        [[t("A", "timer", 0), t("B", "immediate"), t("C", "micro"), t("D", "tick"), t("E", "sync")]],
        [[t("a", "sync"), t("b", "sync"), t("c", "sync")]],
        [[t("t1", "timer", 1), t("t0", "timer", 0), t("s", "sync")]],
        [[]],
        [[t("m1", "micro"), t("n1", "tick"), t("m2", "micro"), t("n2", "tick")]],
        [[t("slow", "timer", 50), t("fast", "timer", 5), t("mid", "timer", 20)]],
        [[t("x", "timer", 10), t("y", "timer", 10), t("z", "timer", 3)]],
        [[t("i1", "immediate"), t("t", "timer", 0), t("i2", "immediate")]],
        [[t("only", "tick")]],
        [[t("p", "micro"), t("q", "sync"), t("r", "immediate"), t("s", "timer", 2), t("u", "tick"), t("v", "sync"), t("w", "timer", 0)]],
        [[t("z2", "timer", 2), t("z0", "timer", 0), t("z1", "timer", 1), t("zz", "timer", 0)]],
        [[t(str(i), ["sync", "tick", "micro", "timer", "immediate"][i % 5], i % 7) for i in range(40)]],
    ],
    examples=2,
    wrong_solutions=[
        # timers before immediates
        r'''function loopOrder(tasks) {
  const pick = (type) => tasks.filter((x) => x.type === type);
  const timers = pick("timer").map((x, i) => ({ id: x.id, due: Math.max(1, x.delay || 0), i })).sort((a, b) => a.due - b.due || a.i - b.i);
  return [...pick("sync"), ...pick("tick"), ...pick("micro")].map((x) => x.id).concat(timers.map((x) => x.id), pick("immediate").map((x) => x.id));
}
''',
        # forgets that a delay of 0 becomes 1
        r'''function loopOrder(tasks) {
  const pick = (type) => tasks.filter((x) => x.type === type);
  const timers = pick("timer").map((x, i) => ({ id: x.id, due: x.delay, i })).sort((a, b) => a.due - b.due || a.i - b.i);
  return [...pick("sync"), ...pick("tick"), ...pick("micro"), ...pick("immediate")].map((x) => x.id).concat(timers.map((x) => x.id));
}
''',
    ],
    guide=G(
        prereqs="Arrays, `filter`, `map` and `sort` with a comparator. The lesson *The event loop in detail* explains the queues.",
        intuition="Nothing is nested, so each kind of work forms one group and the groups always leave in the same order: "
                  "synchronous code, the `nextTick` queue, promise microtasks, immediates, then timers by delay. "
                  "The task is a stable grouping plus one sort.",
        hints=[
            "Build five lists, one per type, keeping the listing order inside each list.",
            "Only the timers need sorting. Remember the minimum delay of 1 ms before comparing.",
            "Sort timers by `(max(1, delay), original position)` so equal delays keep listing order, then concatenate sync, tick, micro, immediate, timers.",
        ],
        brute_force="Simulate a full event loop with a clock and five queues. It works, but for a flat script it is far more code than needed. O(n log n).",
        approach="1. Filter the tasks by type (filter keeps listing order).\n"
                 "2. For timers compute `due = max(1, delay)` and remember the original index.\n"
                 "3. Sort timers by `due`, breaking ties by index.\n"
                 "4. Concatenate.\n\n"
                 "**Dry run** on the example: sync = `[E]`, tick = `[D]`, micro = `[C]`, immediate = `[B]`, timers = `[A (due 1)]` → `E, D, C, B, A`.",
        complexity="Time O(n log n) for the sort, space O(n).",
        pitfalls="- Treating `delay: 0` as smaller than `delay: 1`. Both become 1, so listing order decides.\n"
                 "- Putting promise callbacks before `nextTick` callbacks. In a CommonJS script the `nextTick` queue goes first.\n"
                 "- Relying on an unstable sort order without a tie-break.",
        follow_up="Try the nested version, *Event loop order: nested callbacks*, where callbacks schedule more work.",
    ),
),
dict(
    id="node-event-loop-nested", title="Event loop order: nested callbacks", difficulty="Hard", pattern="Event loop",
    kind="js", entry="simulateLoop",
    description=r"""
Simulate a small model of the Node.js event loop. A task is `{id, type, delay?, then?}`. Types are the same as in the flat
problem: `"sync"`, `"tick"` (`process.nextTick`), `"micro"` (promise callback), `"timer"` (`setTimeout`, with `delay`), `"immediate"` (`setImmediate`).
`then` is an optional list of tasks that the callback schedules **when it runs**.

**Running a task** means: log its `id`, then go through its `then` list in order and *schedule* each child.
**Scheduling** a task means: a `sync` task runs right away (inline); a `tick` goes to the back of the tick queue; a `micro` goes to the back of the microtask queue;
an `immediate` goes to the back of the immediate queue; a `timer` is registered with `due = now + max(1, delay)`.

The model:

1. `now = 0`. Schedule the top-level `tasks` in order (this is the main script).
2. **Drain**: run every task in the tick queue (including ticks added meanwhile); then every task in the microtask queue (including microtasks added meanwhile). If that left anything in the tick queue, repeat. Drain ends when both queues are empty.
3. Loop while a timer or an immediate is pending:
   - If the immediate queue is empty, set `now` to the earliest timer `due` (if that is later than `now`). Otherwise `now` does not change.
   - **Timers phase**: take the timers with `due <= now`, ordered by `due` and then by the order they were registered. Run each one, and **drain** after each.
   - **Check phase**: take the immediates that are queued *at this moment*. Run each one, and **drain** after each. Immediates scheduled during this phase wait for the next iteration.

Return the list of ids in logging order.

**Example:** `[{id:"T",type:"timer",delay:0,then:[{id:"T-i",type:"immediate"},{id:"T-t",type:"timer",delay:0},{id:"T-m",type:"micro"}]},{id:"S",type:"sync"}]`
→ `["S","T","T-m","T-i","T-t"]` (inside a callback, the immediate beats a zero timer).
""",
    starter="function simulateLoop(tasks) {\n  // return the ids in logging order\n}\n",
    solution=NESTED_SOLUTION,
    tests=[
        [[t("T", "timer", 0, [t("T-i", "immediate"), t("T-t", "timer", 0), t("T-m", "micro")]), t("S", "sync")]],
        [[t("A", "micro"), t("B", "tick"), t("C", "sync")]],
        [[]],
        [[t("m", "micro", then=[t("m-tick", "tick"), t("m-micro", "micro")]), t("k", "tick", then=[t("k-micro", "micro"), t("k-tick", "tick")])]],
        [[t("i1", "immediate", then=[t("i1-i", "immediate"), t("i1-n", "tick")]), t("i2", "immediate"), t("t1", "timer", 1)]],
        [[t("s", "sync", then=[t("s-s", "sync", then=[t("deep", "tick")]), t("s-m", "micro")]), t("last", "sync")]],
        [[t("a", "timer", 10, then=[t("a2", "timer", 5)]), t("b", "timer", 12), t("c", "timer", 15)]],
        [[t("x", "timer", 3), t("y", "timer", 3, then=[t("y-m", "micro")]), t("z", "timer", 3)]],
        [[t("p", "micro", then=[t("p1", "micro", then=[t("p2", "micro", then=[t("p-t", "tick")])])]), t("q", "immediate")]],
        [[t("t5", "timer", 5, then=[t("imm", "immediate", then=[t("t0", "timer", 0)])]), t("t6", "timer", 6)]],
        [[t("i", "immediate", then=[t("it", "timer", 0), t("ii", "immediate", then=[t("iii", "immediate")])]), t("t", "timer", 1)]],
        [[t("n", "tick", then=[t("n-s", "sync"), t("n-i", "immediate"), t("n-t", "timer", 0)]), t("m", "micro", then=[t("m-i", "immediate")])]],
        [[t("r%d" % i, "timer", (i * 7) % 5, then=[t("r%d-m" % i, "micro"), t("r%d-i" % i, "immediate", then=[t("r%d-k" % i, "tick")])]) for i in range(12)]],
    ],
    examples=2,
    wrong_solutions=[
        # ticks and microtasks share one FIFO queue
        r'''function simulateLoop(tasks) {
  const out = [], jobs = [], timers = [], immediates = [];
  let now = 0, seq = 0;
  function schedule(list) {
    for (const x of list || []) {
      if (x.type === "sync") run(x);
      else if (x.type === "tick" || x.type === "micro") jobs.push(x);
      else if (x.type === "immediate") immediates.push(x);
      else timers.push({ task: x, due: now + Math.max(1, x.delay || 0), seq: seq++ });
    }
  }
  function run(x) { out.push(x.id); schedule(x.then); }
  function drain() { while (jobs.length) run(jobs.shift()); }
  schedule(tasks); drain();
  while (timers.length || immediates.length) {
    if (!immediates.length) { const f = Math.min(...timers.map((x) => x.due)); if (f > now) now = f; }
    const due = timers.filter((x) => x.due <= now).sort((a, b) => a.due - b.due || a.seq - b.seq);
    for (const x of due) { timers.splice(timers.indexOf(x), 1); run(x.task); drain(); }
    for (const x of immediates.splice(0)) { run(x); drain(); }
  }
  return out;
}
''',
        # drains only once per phase instead of after every callback
        r'''function simulateLoop(tasks) {
  const out = [], ticks = [], micros = [], timers = [], immediates = [];
  let now = 0, seq = 0;
  function schedule(list) {
    for (const x of list || []) {
      if (x.type === "sync") run(x);
      else if (x.type === "tick") ticks.push(x);
      else if (x.type === "micro") micros.push(x);
      else if (x.type === "immediate") immediates.push(x);
      else timers.push({ task: x, due: now + Math.max(1, x.delay || 0), seq: seq++ });
    }
  }
  function run(x) { out.push(x.id); schedule(x.then); }
  function drain() { while (ticks.length || micros.length) { while (ticks.length) run(ticks.shift()); while (micros.length) run(micros.shift()); } }
  schedule(tasks); drain();
  while (timers.length || immediates.length) {
    if (!immediates.length) { const f = Math.min(...timers.map((x) => x.due)); if (f > now) now = f; }
    const due = timers.filter((x) => x.due <= now).sort((a, b) => a.due - b.due || a.seq - b.seq);
    for (const x of due) { timers.splice(timers.indexOf(x), 1); run(x.task); }
    drain();
    for (const x of immediates.splice(0)) run(x);
    drain();
  }
  return out;
}
''',
    ],
    guide=G(
        prereqs="Queues (arrays with `push`/`shift`), recursion, sorting with a tie-break. Solve *Event loop order: one flat script* first and read *The event loop in detail*.",
        intuition="The loop is a clerk with four trays. Two small trays (ticks, microtasks) are emptied completely after **every** callback. "
                  "Two big trays (timers, immediates) are visited once per lap, timers first. Write that clerk literally and the order falls out.",
        hints=[
            "Write three helpers: `schedule(list)`, `run(task)` (log, then schedule children) and `drain()` (ticks fully, then microtasks fully, repeat).",
            "A `sync` child is not queued at all: it runs inside the parent, before the parent's later children are even scheduled.",
            "For the check phase, copy the immediate queue and empty it *before* running anything, so that immediates added during the phase land in the next lap. Only jump the clock when no immediate is waiting.",
        ],
        brute_force="There is no shortcut formula once callbacks nest; simulation is the direct method. A slow simulation that rescans all timers each lap is still fine: O(n^2) for n tasks.",
        approach="Keep `out`, `ticks`, `micros`, `immediates`, `timers` (each timer stores `due` and a registration number) and `now`.\n\n"
                 "1. `schedule(tasks)` then `drain()`.\n"
                 "2. While timers or immediates remain: jump the clock if no immediate is waiting; run due timers in `(due, seq)` order with a drain after each; "
                 "snapshot the immediates, run each with a drain after each.\n\n"
                 "**Dry run** on the example: main script schedules timer `T` (due 1) and runs `S` → log `S`. Drain: nothing. "
                 "Lap 1: no immediates, so `now = 1`. Timer `T` is due → log `T`; it queues immediate `T-i`, registers timer `T-t` with due 2 and queues microtask `T-m`. "
                 "Drain → log `T-m`. Check phase → log `T-i`. Lap 2: no immediates, `now = 2`, log `T-t`. Result `S, T, T-m, T-i, T-t`.",
        complexity="With n tasks in total: O(n^2) time in this straightforward version (filtering timers each lap), O(n) space. A min-heap for timers gives O(n log n).",
        pitfalls="- Draining once per phase instead of after each callback (Node has drained after every callback since version 11).\n"
                 "- Running a microtask-scheduled `tick` before the remaining microtasks: the microtask queue empties first, then the loop goes back to ticks.\n"
                 "- Letting an immediate that was scheduled during the check phase run in the same phase.\n"
                 "- Computing a timer's `due` from 0 instead of from the current `now`.",
        follow_up="Add an `io` task type handled in a poll phase between timers and check, as in the real loop.",
    ),
),
dict(
    id="node-semver-satisfies", title="Does this version satisfy the npm range?", difficulty="Medium", pattern="npm & packages",
    kind="js", entry="satisfies",
    description=r"""
`package.json` lists dependencies with **version ranges** such as `^4.18.2`. Write `satisfies(version, range)` that returns `true`
when `version` (always a full `MAJOR.MINOR.PATCH` string of non-negative integers, no pre-release tags) is allowed by `range`.

A range is one or more **alternatives** separated by `||`; the version must satisfy at least one. An alternative is one or more
**comparators** separated by spaces; the version must satisfy all of them. A comparator is one of:

| form | meaning |
|---|---|
| `1.2.3` or `=1.2.3` | exactly that version |
| `>1.2.3`, `>=1.2.3`, `<1.2.3`, `<=1.2.3` | ordinary comparison (numeric, part by part) |
| `^1.2.3` | `>=1.2.3` and `<2.0.0`: do not change the left-most non-zero part. So `^0.2.3` means `>=0.2.3 <0.3.0` and `^0.0.3` means only `0.0.3` |
| `~1.2.3` | `>=1.2.3` and `<1.3.0`: patch updates only |
| `1.x` , `1.2.x` | any version with that major (and minor) |
| `*` | any version |

**Examples:** `satisfies("4.19.0", "^4.18.2")` → `true`; `satisfies("1.10.0", ">=1.9.0 <2.0.0")` → `true`; `satisfies("0.3.0", "^0.2.3")` → `false`.
""",
    starter="function satisfies(version, range) {\n  // return true or false\n}\n",
    solution=SEMVER_SOLUTION,
    tests=[
        ["4.19.0", "^4.18.2"], ["1.10.0", ">=1.9.0 <2.0.0"], ["0.3.0", "^0.2.3"],
        ["5.0.0", "^4.18.2"], ["4.18.1", "^4.18.2"], ["0.2.9", "^0.2.3"], ["0.0.3", "^0.0.3"], ["0.0.4", "^0.0.3"],
        ["1.2.9", "~1.2.3"], ["1.3.0", "~1.2.3"], ["2.5.1", "1.x || 2.5.x"], ["2.6.0", "1.x || 2.5.x"],
        ["3.0.0", "*"], ["1.2.3", "=1.2.3"], ["1.2.4", "1.2.3"], ["10.0.0", ">9.9.9"], ["2.0.0", ">=1.0.0 <2.0.0 || >=3.0.0"],
        ["3.1.0", ">=1.0.0 <2.0.0 || >=3.0.0"], ["1.0.0", "<=1.0.0"], ["12.4.0", "^12.3.10"],
    ],
    examples=3,
    wrong_solutions=[
        # compares versions as strings
        r'''function satisfies(version, range) {
  const test = (c) => {
    if (c === "*") return true;
    if (c.startsWith("^")) { const b = c.slice(1).split(".").map(Number), v = version.split(".").map(Number); return v[0] === b[0] && version >= c.slice(1); }
    if (c.startsWith("~")) { const b = c.slice(1).split(".").map(Number), v = version.split(".").map(Number); return v[0] === b[0] && v[1] === b[1] && v[2] >= b[2]; }
    const m = /^(>=|<=|>|<|=)?(.+)$/.exec(c), op = m[1] || "=", p = m[2].split("."), v = version.split(".");
    if (p[1] === "x") return v[0] === p[0];
    if (p[2] === "x") return v[0] === p[0] && v[1] === p[1];
    return op === ">=" ? version >= m[2] : op === "<=" ? version <= m[2] : op === ">" ? version > m[2] : op === "<" ? version < m[2] : version === m[2];
  };
  return range.split("||").some((alt) => alt.trim().split(/\s+/).every(test));
}
''',
        # caret always locks the major, even for 0.x
        r'''function satisfies(version, range) {
  const parse = (s) => s.split(".").map(Number);
  const cmp = (a, b) => { for (let i = 0; i < 3; i++) if (a[i] !== b[i]) return a[i] < b[i] ? -1 : 1; return 0; };
  const v = parse(version);
  const test = (c) => {
    if (c === "*") return true;
    if (c.startsWith("^")) { const b = parse(c.slice(1)); return cmp(v, b) >= 0 && v[0] === b[0]; }
    if (c.startsWith("~")) { const b = parse(c.slice(1)); return cmp(v, b) >= 0 && v[0] === b[0] && v[1] === b[1]; }
    const m = /^(>=|<=|>|<|=)?(.+)$/.exec(c), op = m[1] || "=", p = m[2].split(".");
    if (p[1] === "x") return v[0] === +p[0];
    if (p[2] === "x") return v[0] === +p[0] && v[1] === +p[1];
    const d = cmp(v, parse(m[2]));
    return op === ">=" ? d >= 0 : op === "<=" ? d <= 0 : op === ">" ? d > 0 : op === "<" ? d < 0 : d === 0;
  };
  return range.split("||").some((alt) => alt.trim().split(/\s+/).every(test));
}
''',
    ],
    guide=G(
        prereqs="String `split`, `map(Number)`, `some`/`every`. Semantic versioning from the lesson *npm, package.json and your first HTTP server*.",
        intuition="Every comparator, however it is written, describes an interval of versions. Turn the version into three numbers, "
                  "write one three-way `compare`, and express each comparator as lower and upper bounds. The `||` and space rules are `some` and `every`.",
        hints=[
            "Never compare version strings directly: `\"1.10.0\" < \"1.9.0\"` as text. Split on dots and compare numbers part by part.",
            "`^` and `~` are both `>= base` and `< some upper bound`. Work out the upper bound: tilde bumps the minor; caret bumps the left-most non-zero part.",
            "Structure: `range.split('||').some(alt => alt.trim().split(/\\s+/).every(test))`, where `test` handles one comparator.",
        ],
        brute_force="Enumerate candidate versions is impossible (infinitely many), so the direct method is the interval check itself. A naive string comparison is the tempting wrong shortcut.",
        approach="1. `parse(\"1.2.3\")` → `[1, 2, 3]`; `compare(a, b)` returns -1, 0 or 1 at the first differing part.\n"
                 "2. `test(comparator)`: handle `*`; `^` (upper bound `[M+1,0,0]`, or `[0,m+1,0]` when the major is 0, or `[0,0,p+1]` when major and minor are 0); "
                 "`~` (upper bound `[M, m+1, 0]`); x-ranges (compare leading parts); otherwise read the operator and compare.\n"
                 "3. Combine with `some` over `||` alternatives and `every` over space-separated comparators.\n\n"
                 "**Dry run** `satisfies(\"0.3.0\", \"^0.2.3\")`: base `[0,2,3]`, major is 0 and minor is not, so upper bound `[0,3,0]`. "
                 "`0.3.0 >= 0.2.3` is true but `0.3.0 < 0.3.0` is false → `false`.",
        complexity="O(length of the range string); constant extra space.",
        pitfalls="- String comparison of versions (`\"10.0.0\" > \"9.9.9\"` is false as text).\n"
                 "- Forgetting the special caret rule for `0.x` versions, which is exactly where real projects get surprised.\n"
                 "- Not trimming around `||`, which leaves empty comparators.",
        follow_up="Add pre-release tags (`1.2.3-beta.1`) and hyphen ranges (`1.2.3 - 2.3.4`), as the real `semver` package does.",
    ),
),
dict(
    id="node-module-resolution", title="Where does require() find the file?", difficulty="Medium", pattern="Modules",
    kind="js", entry="resolveModule",
    description=r"""
Implement a simplified version of the CommonJS resolving algorithm: `resolveModule(files, mains, from, spec)`.

- `files`: list of absolute file paths that exist (POSIX style, e.g. `"/app/src/db.js"`). Only files are listed; a directory exists if a file is inside it.
- `mains`: object mapping the path of a `package.json` to its `"main"` field (packages without a `main` are absent).
- `from`: absolute path of the file that calls `require`.
- `spec`: the string passed to `require`.

Return the absolute path of the file that would be loaded, `"core:<name>"` for a core module, or `null` if nothing is found.

**Rules**

1. **Core modules.** If `spec` starts with `node:` return `"core:"` + the rest. If `spec` is one of `fs, path, http, events, stream, util` return `"core:" + spec`. Core modules win even if a package with that name exists.
2. **Paths.** If `spec` starts with `./`, `../` or `/`, compute the target path `X` (relative to the directory of `from`, resolving `.` and `..`) and return `LOAD(X)`.
3. **Packages.** Otherwise, starting in the directory of `from` and moving up one directory at a time until `/` (inclusive), try `LOAD(dir + "/node_modules/" + spec)`. Return the first hit.

`LOAD(X)` tries, in order:
- as a file: `X`, `X.js`, `X.json`;
- as a directory: if `X/package.json` exists and has a `main` value `M`, let `Y = X/M` (normalised) and try `Y`, `Y.js`, `Y.json`, `Y/index.js`; then `X/index.js`, `X/index.json`.

**Example:** with files `["/app/src/server.js", "/app/src/db/index.js", "/app/node_modules/pino/package.json", "/app/node_modules/pino/lib/pino.js"]`
and mains `{"/app/node_modules/pino/package.json": "lib/pino"}`:
`resolveModule(files, mains, "/app/src/server.js", "./db")` → `"/app/src/db/index.js"` and `(…, "pino")` → `"/app/node_modules/pino/lib/pino.js"`.
""",
    starter="function resolveModule(files, mains, from, spec) {\n  // return a path, \"core:name\" or null\n}\n",
    solution=RESOLVE_SOLUTION,
    tests=(lambda F, M: [
        [F, M, "/app/src/server.js", "./db"],
        [F, M, "/app/src/server.js", "pino"],
        [F, M, "/app/src/server.js", "fs"],
        [F, M, "/app/src/server.js", "node:crypto"],
        [F, M, "/app/src/server.js", "./config"],
        [F, M, "/app/src/db/index.js", "../config.json"],
        [F, M, "/app/src/db/index.js", "../util"],
        [F, M, "/app/src/db/index.js", "left-pad"],
        [F, M, "/app/src/db/index.js", "lodash"],
        [F, M, "/app/packages/api/handler.js", "pino"],
        [F, M, "/app/packages/api/handler.js", "shared"],
        [F, M, "/app/src/server.js", "/app/src/util"],
        [F, M, "/app/src/server.js", "./missing"],
        [F, M, "/app/src/server.js", "broken"],
        [F, M, "/app/src/server.js", "./db/../util.js"],
    ])(
        ["/app/src/server.js", "/app/src/db/index.js", "/app/src/config.json", "/app/src/util.js", "/app/src/util/index.js",
         "/app/node_modules/pino/package.json", "/app/node_modules/pino/lib/pino.js", "/app/node_modules/pino/index.js",
         "/app/node_modules/left-pad/index.js", "/node_modules/lodash/package.json", "/node_modules/lodash/lodash.js",
         "/app/packages/api/handler.js", "/app/packages/api/node_modules/pino/index.js",
         "/app/packages/node_modules/shared/package.json", "/app/packages/node_modules/shared/src/index.js",
         "/app/node_modules/broken/package.json", "/app/node_modules/broken/index.json", "/app/node_modules/fs/index.js"],
        {"/app/node_modules/pino/package.json": "lib/pino", "/node_modules/lodash/package.json": "./lodash.js",
         "/app/packages/node_modules/shared/package.json": "src", "/app/node_modules/broken/package.json": "dist/main.js"},
    ),
    examples=2,
    wrong_solutions=[
        # looks only in the nearest node_modules, never walks up
        r'''function resolveModule(files, mains, from, spec) {
  const core = ["fs", "path", "http", "events", "stream", "util"];
  if (spec.startsWith("node:")) return "core:" + spec.slice(5);
  if (core.includes(spec)) return "core:" + spec;
  const have = new Set(files);
  const norm = (p) => { const o = []; for (const s of p.split("/")) { if (s === "" || s === ".") continue; if (s === "..") o.pop(); else o.push(s); } return "/" + o.join("/"); };
  const dirname = (p) => { const i = p.lastIndexOf("/"); return i <= 0 ? "/" : p.slice(0, i); };
  const asFile = (x) => [x, x + ".js", x + ".json"].find((c) => have.has(c)) || null;
  const asDir = (x) => { const m = have.has(x + "/package.json") ? mains[x + "/package.json"] : undefined;
    if (m) { const y = norm(x + "/" + m); const h = asFile(y) || (have.has(y + "/index.js") ? y + "/index.js" : null); if (h) return h; }
    return [x + "/index.js", x + "/index.json"].find((c) => have.has(c)) || null; };
  const load = (x) => asFile(x) || asDir(x);
  if (spec.startsWith("./") || spec.startsWith("../") || spec.startsWith("/")) return load(norm(spec.startsWith("/") ? spec : dirname(from) + "/" + spec));
  return load(norm(dirname(from) + "/node_modules/" + spec));
}
''',
        # tries the directory before the file
        r'''function resolveModule(files, mains, from, spec) {
  const core = ["fs", "path", "http", "events", "stream", "util"];
  if (spec.startsWith("node:")) return "core:" + spec.slice(5);
  if (core.includes(spec)) return "core:" + spec;
  const have = new Set(files);
  const norm = (p) => { const o = []; for (const s of p.split("/")) { if (s === "" || s === ".") continue; if (s === "..") o.pop(); else o.push(s); } return "/" + o.join("/"); };
  const dirname = (p) => { const i = p.lastIndexOf("/"); return i <= 0 ? "/" : p.slice(0, i); };
  const asFile = (x) => [x, x + ".js", x + ".json"].find((c) => have.has(c)) || null;
  const asDir = (x) => { const m = have.has(x + "/package.json") ? mains[x + "/package.json"] : undefined;
    if (m) { const y = norm(x + "/" + m); const h = asFile(y) || (have.has(y + "/index.js") ? y + "/index.js" : null); if (h) return h; }
    return [x + "/index.js", x + "/index.json"].find((c) => have.has(c)) || null; };
  const load = (x) => asDir(x) || asFile(x);
  if (spec.startsWith("./") || spec.startsWith("../") || spec.startsWith("/")) return load(norm(spec.startsWith("/") ? spec : dirname(from) + "/" + spec));
  let dir = dirname(from);
  while (true) { const h = load(norm(dir + "/node_modules/" + spec)); if (h) return h; if (dir === "/") return null; dir = dirname(dir); }
}
''',
    ],
    guide=G(
        prereqs="String slicing, `Set` lookups, loops. The lesson *CommonJS: require, resolution, the cache and cycles*.",
        intuition="Resolution is a fixed checklist. Decide which of three kinds the specifier is (core, path, package), then apply the same small `LOAD` routine "
                  "to one candidate location (paths) or to a ladder of `node_modules` folders climbing towards the root (packages).",
        hints=[
            "Write two tiny helpers first: `dirname(path)` and `normalise(path)` that removes `.` and resolves `..`.",
            "Write `asFile(x)` (exact, `.js`, `.json`) and `asDirectory(x)` (package.json main, then index files) and define `load = asFile || asDirectory`.",
            "For a bare name loop: `dir = dirname(from)`; try `dir/node_modules/spec`; if `dir` is `/` stop, else `dir = dirname(dir)`.",
        ],
        brute_force="Scan the whole file list for anything ending in the specifier. It finds wrong files (a deeper copy, a different extension order) and is O(files) per lookup.",
        approach="1. Core check.\n2. Put `files` in a `Set` for O(1) existence tests.\n3. Path specifiers: normalise and `load`.\n4. Bare specifiers: climb directories.\n\n"
                 "**Dry run** `require(\"pino\")` from `/app/packages/api/handler.js` in the test tree: first candidate `/app/packages/api/node_modules/pino`: "
                 "not a file, no `.js`, no `.json`; as a directory there is no package.json, but `index.js` exists → returned. "
                 "The copy in `/app/node_modules/pino` is never reached: the nearest one wins, which is how two versions of a package coexist.",
        complexity="O(depth of the directory tree) set lookups per call, each O(1) on average. Building the set is O(number of files).",
        pitfalls="- Checking the directory before the file: `./util` must pick `util.js` over `util/index.js`.\n"
                 "- Stopping at the first `node_modules` folder instead of walking up to the root.\n"
                 "- A `main` that points to a missing file: fall back to `index.js` / `index.json`.\n"
                 "- Letting a package named `fs` shadow the core module.",
        follow_up="Real Node also honours the `exports` field of package.json, which takes priority over `main`. Add a simplified version of it.",
    ),
),
dict(
    id="node-require-cycle", title="Predict the output of circular requires", difficulty="Hard", pattern="Modules",
    kind="js", entry="runModules",
    description=r"""
Model how CommonJS loads modules that depend on each other. `modules` maps a module name to its body: a list of statements executed in order.
`runModules(modules, entry)` loads `entry` and returns the log (a list of strings).

Statements:

| statement | meaning |
|---|---|
| `["set", key, value]` | `exports[key] = value` on the module's **current** exports object |
| `["replace", obj]` | `module.exports = {...obj}`: the module now has a brand-new exports object |
| `["require", dep]` | `const dep = require("dep")`: load `dep` and keep the returned object in a local binding named `dep` |
| `["read", dep, key]` | log `"<thisModule>:<dep>.<key>=<value>"` reading `key` from the object held by the local binding `dep` |

**Loading rule (the important part).** `require(name)`:
1. If `name` is in the cache, return its current `module.exports` immediately, even if that module has not finished running.
2. Otherwise create `module = {exports: {}}`, **store it in the cache first**, log `"start:<name>"`, run the body, log `"end:<name>"`, and return `module.exports`.

For `read`, the value is shown with `JSON.stringify`; a missing key shows `undefined`; if the module never required `dep`, show `unbound`.

**Example:** `modules = {main: [["require","a"],["read","a","done"]], a: [["set","done",false],["require","b"],["set","done",true]], b: [["require","a"],["read","a","done"],["set","x",1]]}`,
`entry = "main"` → `["start:main","start:a","start:b","b:a.done=false","end:b","end:a","main:a.done=true","end:main"]`.
Module `b` sees a half-finished `a`.
""",
    starter="function runModules(modules, entry) {\n  // return the log as an array of strings\n}\n",
    solution=CYCLE_SOLUTION,
    tests=[
        [{"main": [["require", "a"], ["read", "a", "done"]],
          "a": [["set", "done", False], ["require", "b"], ["set", "done", True]],
          "b": [["require", "a"], ["read", "a", "done"], ["set", "x", 1]]}, "main"],
        [{"main": [["set", "v", 1], ["read", "main", "v"]]}, "main"],
        [{"main": [["require", "a"], ["require", "a"], ["read", "a", "n"]], "a": [["set", "n", 42]]}, "main"],
        [{"main": [["require", "a"], ["read", "a", "name"], ["read", "a", "late"]],
          "a": [["require", "b"], ["replace", {"name": "A"}]],
          "b": [["require", "a"], ["read", "a", "name"]]}, "main"],
        [{"main": [["require", "a"], ["require", "b"], ["read", "a", "fromB"], ["read", "b", "fromA"]],
          "a": [["set", "ready", False], ["require", "b"], ["read", "b", "ready"], ["set", "fromB", "seen"], ["set", "ready", True]],
          "b": [["set", "ready", False], ["require", "a"], ["read", "a", "ready"], ["set", "fromA", "seen"], ["set", "ready", True]]}, "main"],
        [{"main": [["require", "a"], ["require", "b"], ["read", "a", "fromB"], ["read", "b", "fromA"]],
          "a": [["set", "ready", False], ["require", "b"], ["read", "b", "ready"], ["set", "fromB", "seen"], ["set", "ready", True]],
          "b": [["set", "ready", False], ["require", "a"], ["read", "a", "ready"], ["set", "fromA", "seen"], ["set", "ready", True]]}, "b"],
        [{"a": [["require", "a"], ["set", "x", 1], ["read", "a", "x"]]}, "a"],
        [{"a": [["set", "k", 1], ["require", "a"], ["replace", {"k": 2, "extra": True}], ["read", "a", "k"], ["read", "a", "extra"]]}, "a"],
        [{"main": [["require", "svc"], ["read", "svc", "v"]],
          "svc": [["require", "svc"], ["replace", {"v": "new"}], ["read", "svc", "v"], ["set", "w", 1], ["read", "svc", "w"]]}, "main"],
        [{"main": [["read", "a", "x"], ["require", "a"], ["read", "a", "x"], ["read", "a", "y"]], "a": [["set", "x", "hi"]]}, "main"],
        [{"main": [["require", "cfg"], ["require", "db"], ["read", "db", "url"]],
          "cfg": [["replace", {"url": "pg://x", "pool": 5}]],
          "db": [["require", "cfg"], ["read", "cfg", "pool"], ["set", "url", "pg://x"]]}, "main"],
        [{"main": [["require", "a"], ["read", "a", "k"]],
          "a": [["set", "k", 1], ["require", "b"], ["replace", {"k": 2}], ["require", "b"]],
          "b": [["require", "a"], ["read", "a", "k"], ["require", "c"]],
          "c": [["require", "a"], ["require", "b"], ["read", "b", "nothing"], ["read", "a", "k"]]}, "main"],
        [{"x": [["require", "y"], ["set", "v", [1, 2]], ["read", "y", "v"]],
          "y": [["require", "z"], ["set", "v", {"a": None}], ["read", "z", "v"]],
          "z": [["require", "x"], ["read", "x", "v"], ["set", "v", "z!"]]}, "x"],
        [{"m0": [["require", "m1"], ["read", "m1", "n"]], "m1": [["require", "m2"], ["set", "n", 1], ["read", "m2", "n"]],
          "m2": [["require", "m3"], ["set", "n", 2], ["read", "m3", "n"]], "m3": [["require", "m0"], ["require", "m1"], ["set", "n", 3], ["read", "m1", "n"], ["read", "m0", "n"]]}, "m0"],
    ],
    examples=1,
    wrong_solutions=[
        # "replace" mutates the old object in place, so stale references magically update
        r'''function runModules(modules, entry) {
  const cache = new Map(), out = [];
  function req(name) {
    if (cache.has(name)) return cache.get(name).exports;
    const mod = { exports: {} }; cache.set(name, mod);
    const local = new Map(); out.push("start:" + name);
    for (const [op, a, b] of modules[name]) {
      if (op === "set") mod.exports[a] = b;
      else if (op === "replace") { for (const k of Object.keys(mod.exports)) delete mod.exports[k]; Object.assign(mod.exports, a); }
      else if (op === "require") local.set(a, req(a));
      else if (op === "read") { let s = "unbound"; if (local.has(a)) { const v = local.get(a)[b]; s = v === undefined ? "undefined" : JSON.stringify(v); } out.push(name + ":" + a + "." + b + "=" + s); }
    }
    out.push("end:" + name); return mod.exports;
  }
  req(entry); return out;
}
''',
        # reads through the cache at read time instead of through the captured reference
        r'''function runModules(modules, entry) {
  const cache = new Map(), out = [];
  function req(name) {
    if (cache.has(name)) return cache.get(name).exports;
    const mod = { exports: {} }; cache.set(name, mod);
    const local = new Set(); out.push("start:" + name);
    for (const [op, a, b] of modules[name]) {
      if (op === "set") mod.exports[a] = b;
      else if (op === "replace") mod.exports = { ...a };
      else if (op === "require") { req(a); local.add(a); }
      else if (op === "read") { let s = "unbound"; if (local.has(a)) { const v = cache.get(a).exports[b]; s = v === undefined ? "undefined" : JSON.stringify(v); } out.push(name + ":" + a + "." + b + "=" + s); }
    }
    out.push("end:" + name); return mod.exports;
  }
  req(entry); return out;
}
''',
    ],
    guide=G(
        prereqs="Recursion, `Map`, object references versus copies. The lesson *CommonJS: require, resolution, the cache and cycles*.",
        intuition="Two facts explain every circular-dependency surprise. First, a module is put in the cache **before** its body runs, so a cycle gets the "
                  "half-built exports object instead of looping forever. Second, `require` hands out a **reference** to an object: if the module later swaps "
                  "in a new object with `module.exports = ...`, whoever grabbed the old one keeps looking at the old one.",
        hints=[
            "Write a recursive `requireModule(name)` that returns `module.exports` and uses a `Map` as the cache.",
            "Insert into the cache before executing the body. Each run of a body needs its own `local` map from dependency name to the object `require` returned.",
            "`read` must use the object stored in `local`, not look the module up in the cache again; that difference is what the `replace` tests check.",
        ],
        brute_force="There is nothing to search; the task is a faithful interpreter. The naive interpreter without a cache recurses forever on a cycle.",
        approach="`requireModule(name)`: cache hit → return current exports. Otherwise create the module record, cache it, log `start`, interpret statements, log `end`, return exports.\n\n"
                 "**Dry run** of the example: `main` starts and requires `a`. `a` starts, sets `done=false`, requires `b`. `b` starts and requires `a`: "
                 "cache hit, so `b` receives a's object `{done:false}` and logs `b:a.done=false`. `b` ends. Back in `a`: `done=true`, `a` ends. "
                 "`main` reads through the same object, which now says `true`.",
        complexity="O(total number of statements) time, O(number of modules) space plus recursion depth equal to the longest dependency chain.",
        pitfalls="- Caching after the body has run: infinite recursion on any cycle.\n"
                 "- Implementing `replace` by mutating the existing object: real `module.exports = {...}` creates a new object and strands earlier references.\n"
                 "- A module that requires itself gets its own partial exports; that must not crash.",
        follow_up="Model ES modules instead: bindings are live, so a reader sees the final value once the exporter has run, and reading too early throws a ReferenceError.",
    ),
),
dict(
    id="node-mini-emitter", title="Build a mini EventEmitter", difficulty="Medium", pattern="Observer",
    kind="js", entry="runEmitter",
    description=r"""
Implement the core of Node's `EventEmitter` and drive it with a list of operations. `runEmitter(ops)` returns one result per operation.

A *listener* is identified by an id string. When a listener with id `L` is called with payload `P` it produces the record `"L:P"`.

| operation | effect | result |
|---|---|---|
| `["on", event, id]` | register listener `id` for `event` (the same id may be registered several times; each registration is separate) | number of listeners now registered for `event` |
| `["once", event, id]` | like `on`, but the registration is removed the first time it is called | number of listeners for `event` |
| `["off", event, id]` | remove the **most recently added** registration of `id` for `event`, if any | number of listeners for `event` |
| `["count", event]` | nothing | number of listeners for `event` |
| `["emit", event, payload]` | call every listener of `event` in registration order | the list of records produced, e.g. `["a:5","b:5"]` (empty list if there are no listeners) |

Special rule, as in Node: emitting `"error"` when it has **no** listeners is treated as a thrown error; the result is the string `"throw:" + payload`.

**Example:** `[["on","data","a"],["once","data","b"],["emit","data",1],["emit","data",2]]` → `[1, 2, ["a:1","b:1"], ["a:2"]]`
""",
    starter="function runEmitter(ops) {\n  // return one result per operation\n}\n",
    solution=EMITTER_SOLUTION,
    tests=[
        [[["on", "data", "a"], ["once", "data", "b"], ["emit", "data", 1], ["emit", "data", 2]]],
        [[["emit", "nothing", 1], ["count", "nothing"]]],
        [[["emit", "error", "disk full"], ["on", "error", "h"], ["emit", "error", "disk full"]]],
        [[["on", "x", "a"], ["on", "x", "b"], ["on", "x", "a"], ["off", "x", "a"], ["emit", "x", 0], ["off", "x", "a"], ["emit", "x", 1], ["off", "x", "a"]]],
        [[["once", "e", "a"], ["once", "e", "a"], ["count", "e"], ["emit", "e", "p"], ["count", "e"], ["emit", "e", "q"]]],
        [[["on", "a", "l"], ["on", "b", "l"], ["emit", "a", 1], ["off", "a", "l"], ["emit", "a", 2], ["emit", "b", 3]]],
        [[["once", "e", "x"], ["off", "e", "x"], ["emit", "e", 1]]],
        [[["on", "e", "p"], ["once", "e", "q"], ["on", "e", "r"], ["emit", "e", "A"], ["emit", "e", "B"], ["count", "e"]]],
        [[["once", "error", "h"], ["emit", "error", "e1"], ["emit", "error", "e2"]]],
        [[["off", "e", "ghost"], ["on", "e", "a"], ["off", "e", "ghost"], ["count", "e"]]],
        [[]],
        [[["on", "e", "a"], ["once", "e", "a"], ["on", "e", "a"], ["off", "e", "a"], ["emit", "e", 1], ["emit", "e", 2], ["off", "e", "a"], ["emit", "e", 3]]],
        [[[("on" if i % 3 else "once"), "tick", "l%d" % (i % 4)] for i in range(12)] + [["emit", "tick", n] for n in range(3)] + [["count", "tick"]]],
    ],
    examples=2,
    wrong_solutions=[
        # once listeners are never removed
        r'''function runEmitter(ops) {
  const reg = new Map(), res = [];
  for (const [op, event, arg] of ops) {
    if (!reg.has(event)) reg.set(event, []);
    const ls = reg.get(event);
    if (op === "on" || op === "once") { ls.push(arg); res.push(ls.length); }
    else if (op === "off") { const i = ls.lastIndexOf(arg); if (i !== -1) ls.splice(i, 1); res.push(ls.length); }
    else if (op === "count") res.push(ls.length);
    else if (event === "error" && ls.length === 0) res.push("throw:" + arg);
    else res.push(ls.map((id) => id + ":" + arg));
  }
  return res;
}
''',
        # off removes every registration of the id
        r'''function runEmitter(ops) {
  const reg = new Map(), res = [];
  for (const [op, event, arg] of ops) {
    if (!reg.has(event)) reg.set(event, []);
    let ls = reg.get(event);
    if (op === "on" || op === "once") { ls.push({ id: arg, once: op === "once" }); res.push(ls.length); }
    else if (op === "off") { ls = ls.filter((l) => l.id !== arg); reg.set(event, ls); res.push(ls.length); }
    else if (op === "count") res.push(ls.length);
    else if (event === "error" && ls.length === 0) res.push("throw:" + arg);
    else { res.push(ls.map((l) => l.id + ":" + arg)); reg.set(event, ls.filter((l) => !l.once)); }
  }
  return res;
}
''',
    ],
    guide=G(
        prereqs="`Map`, arrays, `splice`. The lesson *The observer pattern and EventEmitter*.",
        intuition="An emitter is a phone book: for each event name, an ordered list of who to call. `on` appends, `off` removes one entry, `emit` walks the list. "
                  "`once` is an ordinary entry with a flag that says: cross me out as you call me.",
        hints=[
            "Use a `Map` from event name to an array of `{id, once}` records.",
            "For `off`, search from the end of the array and remove only the first match you meet.",
            "In `emit`, iterate over a copy (`slice()`) of the array so that removing `once` entries does not skip neighbours; check the `error` rule before anything else.",
        ],
        brute_force="Keep one flat list of `[event, id, once]` triples and scan all of it for every operation: O(total listeners) per emit even for unrelated events.",
        approach="Loop over the operations, fetching (or creating) the listener array for the event.\n\n"
                 "**Dry run** of the example: `on data a` → list `[a]`, result 1. `once data b` → `[a, b*]`, result 2. `emit data 1` → copy the list, call `a` (`a:1`), "
                 "call `b` and delete it (`b:1`) → `[\"a:1\",\"b:1\"]`. `emit data 2` → only `a` remains → `[\"a:2\"]`.",
        complexity="`on`/`once`/`count` O(1); `off` and `emit` O(k) for k listeners of that event. Space O(total registrations).",
        pitfalls="- Removing `once` listeners from the array you are iterating, which skips the next listener.\n"
                 "- `off` removing all registrations of an id; Node removes one, the most recent.\n"
                 "- Forgetting that an unhandled `error` event is special.",
        follow_up="Add `prependListener`, a `maxListeners` warning, and `listenerCount`, then compare with the documented API.",
    ),
),
dict(
    id="node-promisify", title="What does the promisified call settle to?", difficulty="Easy", pattern="Promises",
    kind="js", entry="promisifyOutcome",
    description=r"""
`util.promisify(fn)` wraps a callback-style function: it calls `fn` with an extra callback `(err, value) => ...` and returns a promise
that is rejected when `err` is truthy and fulfilled with `value` otherwise.

Here the callback-style function is described by a script of what it does, `steps`, executed in order. Each step is either

- `{"cb": [err, ...values]}`: the function invokes the callback with these arguments, or
- `{"throw": message}`: the function throws synchronously (nothing after it runs).

Return the final state of the promise as an object:

- `{"state": "fulfilled", "value": v}`, `{"state": "rejected", "reason": r}` or `{"state": "pending"}` (the callback was never called).

Rules:

1. A promise settles **once**. The first settling event wins; later callback calls or a later throw change nothing.
2. `err` is tested for truthiness (`null`, `undefined`, `0`, `""` and `false` all mean "no error").
3. With `multiArgs` false the value is the first value after `err` (or `null` if there is none). With `multiArgs` true the value is the array of all values after `err`.
4. A throw before any callback call rejects the promise with the message.

**Examples:** `promisifyOutcome([{"cb":[null,"data"]}], false)` → `{"state":"fulfilled","value":"data"}`;
`promisifyOutcome([{"cb":["ENOENT"]},{"cb":[null,1]}], false)` → `{"state":"rejected","reason":"ENOENT"}`.
""",
    starter="function promisifyOutcome(steps, multiArgs) {\n  // return {state, value?} or {state, reason?}\n}\n",
    solution=PROMISIFY_SOLUTION,
    tests=[
        [[{"cb": [None, "data"]}], False],
        [[{"cb": ["ENOENT"]}, {"cb": [None, 1]}], False],
        [[], False],
        [[{"throw": "bad argument"}], False],
        [[{"cb": [None, 1, 2, 3]}], False],
        [[{"cb": [None, 1, 2, 3]}], True],
        [[{"cb": [None]}], False],
        [[{"cb": [None]}], True],
        [[{"cb": [None, "first"]}, {"cb": ["late error"]}], False],
        [[{"cb": [None, "ok"]}, {"throw": "after the fact"}], False],
        [[{"cb": [0, "zero is not an error"]}], False],
        [[{"cb": ["", "empty string is not an error"]}], True],
        [[{"cb": [{"code": "EACCES"}, "ignored"]}], True],
        [[{"throw": "sync"}, {"cb": [None, "never"]}], False],
        [[{"cb": [False, None]}, {"cb": [None, "second"]}], False],
    ],
    examples=2,
    wrong_solutions=[
        # last call wins
        r'''function promisifyOutcome(steps, multiArgs) {
  let outcome = { state: "pending" };
  for (const step of steps) {
    if ("throw" in step) { outcome = { state: "rejected", reason: step.throw }; break; }
    const [err, ...values] = step.cb;
    if (err) outcome = { state: "rejected", reason: err };
    else outcome = { state: "fulfilled", value: multiArgs ? values : (values.length ? values[0] : null) };
  }
  return outcome;
}
''',
        # tests err !== null instead of truthiness
        r'''function promisifyOutcome(steps, multiArgs) {
  let outcome = { state: "pending" };
  const settle = (o) => { if (outcome.state === "pending") outcome = o; };
  for (const step of steps) {
    if ("throw" in step) { settle({ state: "rejected", reason: step.throw }); break; }
    const [err, ...values] = step.cb;
    if (err !== null) settle({ state: "rejected", reason: err });
    else settle({ state: "fulfilled", value: multiArgs ? values : (values.length ? values[0] : null) });
  }
  return outcome;
}
''',
    ],
    guide=G(
        prereqs="Destructuring with rest (`const [err, ...values] = args`), truthiness. The lesson *Promises and promisification*.",
        intuition="A promise is a one-way switch with three positions: pending, fulfilled, rejected. Promisification connects the error-first callback to that switch: "
                  "truthy first argument flips it to rejected, anything else flips it to fulfilled. Once flipped it is glued in place.",
        hints=[
            "Keep one variable `outcome`, starting as `{state: \"pending\"}`, and a helper `settle(next)` that only assigns while the state is still pending.",
            "Split the callback arguments into `err` and the rest with destructuring.",
            "A throw also goes through `settle` (so it is ignored if the promise already settled) and then stops the loop.",
        ],
        brute_force="Build a real promise with `new Promise` and inspect it. That cannot work in this judge because promise callbacks run asynchronously, after your function has returned.",
        approach="Walk the steps once.\n\n**Dry run** `[{cb:[\"ENOENT\"]},{cb:[null,1]}]`: step 1 has a truthy `err`, so the outcome becomes rejected with `ENOENT`. "
                 "Step 2 tries to fulfil, but `settle` sees the state is no longer pending and ignores it. Result: rejected, `ENOENT`.",
        complexity="O(number of steps) time, O(1) extra space.",
        pitfalls="- Letting a second callback call overwrite the first result.\n- Treating `0` or `\"\"` as an error; the convention is a truthiness test.\n"
                 "- Returning `undefined` as the value when the callback passed only `err`; JSON has no `undefined`, so use `null`.",
        follow_up="Write the real thing: `const promisify = (fn) => (...args) => new Promise((resolve, reject) => fn(...args, (err, value) => err ? reject(err) : resolve(value)));`",
    ),
),
]
