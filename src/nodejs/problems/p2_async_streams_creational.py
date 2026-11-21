"""Node.js problems, part 2: async control flow in virtual time, streams, creational patterns."""


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


def task(id, ms, fail=False, **extra):
    d = {"id": id, "ms": ms}
    if fail:
        d["fail"] = True
    d.update(extra)
    return d


SEQ_SOLUTION = r'''function runSequential(tasks) {
  const completed = [];
  let total = 0, failed = null;
  for (const task of tasks) {
    total += task.ms;                 // the task runs to its end either way
    if (task.fail) { failed = task.id; break; }
    completed.push(task.id);
  }
  return { completed, failed, total };
}
'''

PAR_SOLUTION = r'''function runParallel(tasks) {
  const byFinish = tasks
    .map((task, index) => ({ ...task, index }))
    .sort((a, b) => a.ms - b.ms || a.index - b.index);
  const total = byFinish.length > 0 ? byFinish[byFinish.length - 1].ms : 0;
  const firstBad = byFinish.find((task) => task.fail);
  return {
    order: byFinish.map((task) => task.id),
    total,
    firstError: firstBad ? firstBad.id : null,
    settledAt: firstBad ? firstBad.ms : total,
  };
}
'''

LIMITED_SOLUTION = r'''function runLimited(tasks, limit) {
  const order = [];
  const starts = new Array(tasks.length).fill(null);
  const running = [];
  let next = 0, now = 0;
  while (next < tasks.length || running.length > 0) {
    while (running.length < limit && next < tasks.length) {
      starts[next] = now;
      running.push({ index: next, end: now + tasks[next].ms });
      next++;
    }
    running.sort((a, b) => a.end - b.end || a.index - b.index);
    const done = running.shift();
    now = done.end;
    order.push(tasks[done.index].id);
  }
  return { order, starts, total: now };
}
'''

RETRY_SOLUTION = r'''function retrySchedule(outcomes, retries, baseMs, factor, maxMs) {
  const waits = [];
  let attempts = 0, success = false;
  while (attempts <= retries) {
    const ok = outcomes[attempts] === true;
    attempts++;
    if (ok) { success = true; break; }
    if (attempts <= retries) waits.push(Math.min(maxMs, baseMs * Math.pow(factor, attempts - 1)));
  }
  return { attempts, waits, totalWait: waits.reduce((sum, w) => sum + w, 0), success };
}
'''

PRIORITY_SOLUTION = r'''function schedulePriority(tasks, concurrency) {
  const pending = tasks.map((task, index) => ({ ...task, index })).sort((a, b) => a.at - b.at || a.index - b.index);
  const waiting = [], running = [], out = [];
  let now = 0, p = 0;
  while (p < pending.length || waiting.length > 0 || running.length > 0) {
    for (let k = running.length - 1; k >= 0; k--) if (running[k] <= now) running.splice(k, 1);
    while (p < pending.length && pending[p].at <= now) waiting.push(pending[p++]);
    waiting.sort((a, b) => b.priority - a.priority || a.at - b.at || a.index - b.index);
    while (running.length < concurrency && waiting.length > 0) {
      const job = waiting.shift();
      running.push(now + job.ms);
      out.push({ id: job.id, start: now, end: now + job.ms });
    }
    const candidates = running.slice();
    if (p < pending.length) candidates.push(pending[p].at);
    if (candidates.length === 0) break;
    now = Math.min(...candidates);
  }
  return out;
}
'''

PIPELINE_SOLUTION = r'''function runPipeline(chunks, transforms, highWaterMark) {
  const apply = (chunk) => {
    let items = [chunk];
    for (const [kind, arg] of transforms) {
      if (kind === "upper") items = items.map((s) => s.toUpperCase());
      else if (kind === "prefix") items = items.map((s) => arg + s);
      else if (kind === "filter") items = items.filter((s) => s.includes(arg));
      else if (kind === "split") items = items.flatMap((s) => s.split(arg).filter((part) => part !== ""));
    }
    return items;
  };
  const buffer = [], output = [];
  let size = 0, i = 0, paused = false, ticks = 0, drains = 0, maxBuffered = 0;
  while (i < chunks.length || buffer.length > 0) {
    ticks++;
    while (!paused && i < chunks.length) {            // (a) produce
      for (const item of apply(chunks[i++])) { buffer.push(item); size += item.length; }
      if (size > maxBuffered) maxBuffered = size;
      if (size >= highWaterMark) paused = true;       // write() returned false
    }
    if (buffer.length > 0) {                          // (b) consume one chunk
      const chunk = buffer.shift();
      size -= chunk.length;
      output.push(chunk);
    }
    if (paused && buffer.length === 0) { paused = false; drains++; }   // (c) drain
  }
  return { output, ticks, drains, maxBuffered };
}
'''

LINES_SOLUTION = r'''function linesFromChunks(chunks) {
  const lines = [];
  let rest = "";
  const clean = (line) => (line.endsWith("\r") ? line.slice(0, -1) : line);
  for (const chunk of chunks) {
    const parts = (rest + chunk).split("\n");
    rest = parts.pop();                      // the last piece may be an unfinished line
    for (const part of parts) lines.push(clean(part));
  }
  if (rest !== "") lines.push(clean(rest));
  return lines;
}
'''

FACTORY_SOLUTION = r'''function runFactory(requests) {
  const counters = {};                       // private to the factory
  const round = (n) => Math.round(n * 100) / 100;
  const makers = {
    circle: (o) => Math.PI * o.r * o.r,
    rect: (o) => o.w * o.h,
    square: (o) => o.side * o.side,
    triangle: (o) => (o.base * o.height) / 2,
  };
  function createShape(options) {
    if (!Object.hasOwn(makers, options.type)) return { error: "unknown shape: " + options.type };
    counters[options.type] = (counters[options.type] || 0) + 1;
    const label = options.type + "#" + counters[options.type];
    const area = () => round(makers[options.type](options));
    return { kind: options.type, label, area };
  }
  return requests.map((request) => {
    const shape = createShape(request);
    return shape.error ? shape : { kind: shape.kind, label: shape.label, area: shape.area() };
  });
}
'''

BUILDER_SOLUTION = r'''function buildQuery(steps) {
  class QueryBuilder {
    constructor() { this.table = null; this.columns = []; this.conditions = []; this.orders = []; this.max = undefined; this.skip = undefined; }
    from(table) { this.table = table; return this; }
    select(...columns) { this.columns.push(...columns); return this; }
    where(condition) { this.conditions.push(condition); return this; }
    orderBy(column, direction = "asc") { this.orders.push(column + " " + direction.toUpperCase()); return this; }
    limit(n) { this.max = n; return this; }
    offset(n) { this.skip = n; return this; }
    build() {
      if (this.table === null) return "error: from is required";
      if (this.max !== undefined && !(Number.isInteger(this.max) && this.max > 0)) return "error: limit must be a positive integer";
      if (this.skip !== undefined && this.max === undefined) return "error: offset requires limit";
      let sql = "SELECT " + (this.columns.length > 0 ? this.columns.join(", ") : "*") + " FROM " + this.table;
      if (this.conditions.length > 0) sql += " WHERE " + this.conditions.map((c) => "(" + c + ")").join(" AND ");
      if (this.orders.length > 0) sql += " ORDER BY " + this.orders.join(", ");
      if (this.max !== undefined) sql += " LIMIT " + this.max;
      if (this.skip !== undefined) sql += " OFFSET " + this.skip;
      return sql;
    }
  }
  const builder = new QueryBuilder();
  for (const [method, ...args] of steps) builder[method](...args);
  return builder.build();
}
'''

DI_SOLUTION = r'''function resolveOrder(registry, target) {
  const order = [], done = new Set(), stack = [];
  function visit(name) {
    if (done.has(name)) return null;
    if (!Object.hasOwn(registry, name)) return "missing: " + name;
    const at = stack.indexOf(name);
    if (at !== -1) return "cycle: " + stack.slice(at).concat(name).join(" -> ");
    stack.push(name);
    for (const dep of registry[name]) {
      const error = visit(dep);
      if (error) return error;
    }
    stack.pop();
    done.add(name);
    order.push(name);
    return null;
  }
  const error = visit(target);
  return error ? { error } : order;
}
'''

PROBLEMS = [
dict(
    id="node-run-sequential", title="Run tasks one after another (virtual time)", difficulty="Easy", pattern="Async control flow",
    kind="js", entry="runSequential",
    description=r"""
Each task is `{id, ms, fail?}`: it takes `ms` milliseconds of *virtual* time and then either succeeds or (when `fail` is true) fails.
Run the tasks **sequentially**: a task starts only when the previous one has succeeded. The first failure stops the sequence; later tasks never start.

Return `{completed, failed, total}`:
- `completed`: ids of the tasks that succeeded, in order;
- `failed`: id of the failing task, or `null`;
- `total`: the virtual time at which the sequence ended (the failing task's duration counts: it had to run to find out it failed).

**Example:** `[{id:"a",ms:30},{id:"b",ms:10,fail:true},{id:"c",ms:5}]` → `{completed:["a"], failed:"b", total:40}`
""",
    starter="function runSequential(tasks) {\n  // return { completed, failed, total }\n}\n",
    solution=SEQ_SOLUTION,
    tests=[
        [[task("a", 30), task("b", 10, True), task("c", 5)]],
        [[task("a", 30), task("b", 10), task("c", 5)]],
        [[]],
        [[task("only", 7)]],
        [[task("bad", 7, True)]],
        [[task("x", 0), task("y", 0), task("z", 0)]],
        [[task("a", 1), task("b", 2), task("c", 3, True), task("d", 4, True)]],
        [[task("first", 100, True), task("second", 1)]],
        [[task("a", 5), task("b", 5), task("c", 5), task("d", 5), task("e", 5, True)]],
        [[task("t%d" % i, i * 3 % 11) for i in range(30)]],
        [[task("t%d" % i, i + 1, i == 17) for i in range(30)]],
    ],
    examples=2,
    wrong_solutions=[
        "function runSequential(tasks) {\n  const completed = []; let total = 0, failed = null;\n  for (const t of tasks) { if (t.fail) { failed = t.id; break; } total += t.ms; completed.push(t.id); }\n  return { completed, failed, total };\n}\n",
        "function runSequential(tasks) {\n  const completed = []; let total = 0, failed = null;\n  for (const t of tasks) { total += t.ms; if (t.fail) { if (failed === null) failed = t.id; } else completed.push(t.id); }\n  return { completed, failed, total };\n}\n",
    ],
    guide=G(
        prereqs="`for...of` loops and `break`. The lesson *Callback hell, its cures and sequential execution*.",
        intuition="Sequential flow is a relay race: the baton passes only on success. Time adds up, and a dropped baton ends the race.",
        hints=["Keep a running clock and add each task's `ms` as it runs.", "Add the duration before checking `fail`: the failing task still used its time.", "On failure record the id and `break`."],
        brute_force="Sum all durations and list all ids, ignoring failures. Wrong as soon as one task fails.",
        approach="One loop.\n\n**Dry run** on the example: `a` → clock 30, completed `[a]`. `b` → clock 40, it fails → `failed = \"b\"`, stop. `c` never starts. Result `{completed:[\"a\"], failed:\"b\", total:40}`.",
        complexity="O(n) time, O(n) space for the output.",
        pitfalls="- Continuing after a failure.\n- Not counting the failing task's duration.\n- Returning `undefined` instead of `null` when nothing failed.",
        follow_up="This is what `for (const t of tasks) await run(t)` does inside a `try` block.",
    ),
),
dict(
    id="node-run-parallel", title="Run tasks in parallel (virtual time)", difficulty="Easy", pattern="Async control flow",
    kind="js", entry="runParallel",
    description=r"""
Each task is `{id, ms, fail?}`. Start **all** tasks at virtual time 0, as `Promise.all(tasks.map(run))` would. A task finishes at time `ms`.

Return `{order, total, firstError, settledAt}`:
- `order`: every id in order of finishing time (ties: the task listed first finishes first). Failing tasks are included; starting them cannot be undone;
- `total`: the time when the last task finishes (`0` for an empty list);
- `firstError`: id of the failing task that finishes earliest (same tie rule), or `null`;
- `settledAt`: when the combined `Promise.all` promise settles: at the first failure, otherwise at `total`.

**Example:** `[{id:"a",ms:30},{id:"b",ms:10},{id:"c",ms:20,fail:true}]` → `{order:["b","c","a"], total:30, firstError:"c", settledAt:20}`
""",
    starter="function runParallel(tasks) {\n  // return { order, total, firstError, settledAt }\n}\n",
    solution=PAR_SOLUTION,
    tests=[
        [[task("a", 30), task("b", 10), task("c", 20, True)]],
        [[task("a", 30), task("b", 10), task("c", 20)]],
        [[]],
        [[task("solo", 9, True)]],
        [[task("x", 5), task("y", 5), task("z", 5)]],
        [[task("x", 5, True), task("y", 5, True), task("z", 1)]],
        [[task("slow-bad", 100, True), task("quick-bad", 2, True), task("ok", 50)]],
        [[task("late", 10), task("early", 1), task("bad-last", 99, True)]],
        [[task("z", 0), task("a", 0, True)]],
        [[task("t%d" % i, (i * 37) % 50) for i in range(40)]],
        [[task("t%d" % i, (i * 37) % 50, i % 9 == 4) for i in range(40)]],
    ],
    examples=2,
    wrong_solutions=[
        "function runParallel(tasks) {\n  const s = tasks.map((t, i) => ({ ...t, i })).sort((a, b) => a.ms - b.ms || a.i - b.i);\n  const total = tasks.reduce((sum, t) => sum + t.ms, 0);\n  const bad = s.find((t) => t.fail);\n  return { order: s.map((t) => t.id), total, firstError: bad ? bad.id : null, settledAt: bad ? bad.ms : total };\n}\n",
        "function runParallel(tasks) {\n  const s = tasks.map((t, i) => ({ ...t, i })).sort((a, b) => a.ms - b.ms || a.i - b.i);\n  const total = s.length ? s[s.length - 1].ms : 0;\n  const bad = tasks.find((t) => t.fail);\n  return { order: s.map((t) => t.id), total, firstError: bad ? bad.id : null, settledAt: bad ? bad.ms : total };\n}\n",
    ],
    guide=G(
        prereqs="Sorting with a comparator and a tie-break. The lesson *Parallel execution, race conditions and limited concurrency*.",
        intuition="Everyone starts at the same whistle, so a task's finishing time is its own duration. Sorting by duration replays the finish line. "
                  "`Promise.all` gives up at the first failure it *hears about*, which is the earliest failing finish, not the first failing task in the list.",
        hints=["Attach each task's index, then sort by `ms` and index.", "`total` is the largest `ms`, not the sum.", "`firstError` is the first failing entry of the *sorted* list; `settledAt` is its `ms`."],
        brute_force="Step a clock one millisecond at a time and check who finishes: O(max ms × n). Sorting skips straight to the events.",
        approach="Sort a copy by `(ms, index)`.\n\n**Dry run** on the example: sorted `b(10), c(20, fails), a(30)`. Order `b, c, a`; total 30; first error `c`; `Promise.all` rejects at 20 while `a` is still running.",
        complexity="O(n log n) time, O(n) space.",
        pitfalls="- Summing durations (that is sequential time).\n- Picking the first failing task in listing order.\n- Forgetting that the other tasks keep running after `Promise.all` rejects.",
        follow_up="How would the answer change for `Promise.allSettled` (settles at `total`, never rejects) or `Promise.race` (settles at the first finish)?",
    ),
),
dict(
    id="node-run-limited", title="Run tasks with a concurrency limit (virtual time)", difficulty="Medium", pattern="Async control flow",
    kind="js", entry="runLimited",
    description=r"""
Each task is `{id, ms}`. Run them with at most `limit` (≥ 1) tasks in flight at once:

- Tasks start in listing order. At time 0 the first `limit` tasks start.
- Whenever a task finishes, the next task that has not started yet starts **at that same instant**.
- If several running tasks finish at the same time, they complete in listing order.

Return `{order, starts, total}`: `order` is the ids in completion order, `starts[i]` is the start time of the task at index `i`,
and `total` is the time the last task finishes (`0` if there are no tasks).

**Example:** tasks `a:50, b:10, c:10, d:10`, `limit = 2` → `{order:["b","c","d","a"], starts:[0,0,10,20], total:50}`.
(`a` occupies one slot the whole time; `b`, `c`, `d` take turns in the other.)
""",
    starter="function runLimited(tasks, limit) {\n  // return { order, starts, total }\n}\n",
    solution=LIMITED_SOLUTION,
    tests=[
        [[task("a", 50), task("b", 10), task("c", 10), task("d", 10)], 2],
        [[task("a", 30), task("b", 20), task("c", 10)], 1],
        [[task("a", 30), task("b", 20), task("c", 10)], 3],
        [[task("a", 30), task("b", 20), task("c", 10)], 10],
        [[], 4],
        [[task("x", 5), task("y", 5), task("z", 5), task("w", 5)], 2],
        [[task("a", 10), task("b", 30), task("c", 10), task("d", 10), task("e", 5)], 2],
        [[task("a", 0), task("b", 0), task("c", 7)], 1],
        [[task("long", 100), task("s1", 1), task("s2", 1), task("s3", 1), task("s4", 1), task("s5", 1)], 3],
        [[task("a", 4), task("b", 3), task("c", 2), task("d", 1), task("e", 1), task("f", 6)], 3],
        [[task("t%d" % i, (i * 13) % 17 + 1) for i in range(40)], 4],
        [[task("t%d" % i, 10) for i in range(25)], 6],
    ],
    examples=2,
    wrong_solutions=[
        # fixed batches: waits for the whole batch before starting the next
        r'''function runLimited(tasks, limit) {
  const order = [], starts = new Array(tasks.length).fill(null);
  let now = 0;
  for (let i = 0; i < tasks.length; i += limit) {
    const batch = tasks.slice(i, i + limit).map((t, k) => ({ ...t, index: i + k }));
    batch.forEach((t) => (starts[t.index] = now));
    batch.sort((a, b) => a.ms - b.ms || a.index - b.index).forEach((t) => order.push(t.id));
    now += Math.max(...batch.map((t) => t.ms));
  }
  return { order, starts, total: now };
}
''',
    ],
    guide=G(
        prereqs="Loops, sorting, and the lesson *Parallel execution, race conditions and limited concurrency* (the task-queue section).",
        intuition="Picture a car park with `limit` spaces and a line of cars outside. Each time a car leaves, the car at the head of the line drives in at once. "
                  "You only need to jump from one departure to the next.",
        hints=["Keep a list of running tasks with their end times and an index `next` of the first task that has not started.", "Loop: fill free slots (recording `starts`), then remove the running task with the smallest end time (ties: smaller index) and move the clock there.", "Do not process a whole batch at once; refill after every single completion."],
        brute_force="Advance a clock 1 ms at a time and check for finished tasks: O(total time × limit). Jumping between completion events is independent of the durations.",
        approach="Event simulation.\n\n**Dry run** on the example (`limit = 2`): start `a` (ends 50) and `b` (ends 10). Earliest end: `b` at 10 → order `[b]`, start `c` at 10 (ends 20). "
                 "Then `c` at 20 → start `d` (ends 30). Then `d` at 30. Then `a` at 50. `starts = [0,0,10,20]`, total 50.",
        complexity="O(n × limit log limit) with the sort shown; O(n log limit) with a min-heap. Space O(n).",
        pitfalls="- Batching (`Promise.all` on slices of size `limit`): slots sit idle while the slowest task of the batch finishes. In the example batching takes 60 instead of 50.\n"
                 "- Tie-breaking by end time only.\n- Returning the last *start* instead of the last *finish* as `total`.",
        follow_up="Add failures: with a limit, should the queue stop starting new tasks after the first error?",
    ),
),
dict(
    id="node-retry-backoff", title="Retry with exponential backoff", difficulty="Easy", pattern="Async control flow",
    kind="js", entry="retrySchedule",
    description=r"""
An unreliable operation is attempted up to `retries + 1` times. `outcomes[k]` tells whether attempt number `k` (0-based) succeeds;
attempts beyond the end of the list fail. Attempts themselves take no time.

After a failed attempt, **if another attempt is allowed**, wait before retrying. The wait before retry number `k` (k = 1, 2, …) is
`min(maxMs, baseMs * factor^(k-1))`. Stop at the first success or when the attempts are used up.

Return `{attempts, waits, totalWait, success}` where `attempts` is the number of attempts made and `waits` is the list of waits in order.

**Example:** `retrySchedule([false, false, true], 5, 100, 2, 1000)` → `{attempts:3, waits:[100,200], totalWait:300, success:true}`
""",
    starter="function retrySchedule(outcomes, retries, baseMs, factor, maxMs) {\n  // return { attempts, waits, totalWait, success }\n}\n",
    solution=RETRY_SOLUTION,
    tests=[
        [[False, False, True], 5, 100, 2, 1000],
        [[True], 3, 100, 2, 1000],
        [[False, False, False, False], 3, 100, 2, 1000],
        [[], 0, 100, 2, 1000],
        [[], 6, 100, 2, 500],
        [[False, True], 0, 50, 3, 10000],
        [[False, False, False, True], 2, 10, 10, 100000],
        [[False, False, False, True], 3, 10, 10, 500],
        [[False] * 10 + [True], 10, 1, 2, 64],
        [[False, True], 4, 250, 1, 1000],
        [[False, False, False, False, False, True], 8, 3, 3, 100],
        [[True, False], 2, 100, 2, 1000],
    ],
    examples=2,
    wrong_solutions=[
        "function retrySchedule(outcomes, retries, baseMs, factor, maxMs) {\n  const waits = []; let attempts = 0, success = false;\n  while (attempts <= retries) { const ok = outcomes[attempts] === true; attempts++; if (ok) { success = true; break; } waits.push(Math.min(maxMs, baseMs * Math.pow(factor, attempts - 1))); }\n  return { attempts, waits, totalWait: waits.reduce((a, b) => a + b, 0), success };\n}\n",
        "function retrySchedule(outcomes, retries, baseMs, factor, maxMs) {\n  const waits = []; let attempts = 0, success = false;\n  while (attempts <= retries) { const ok = outcomes[attempts] === true; attempts++; if (ok) { success = true; break; } if (attempts <= retries) waits.push(baseMs * Math.pow(factor, attempts - 1)); }\n  return { attempts, waits, totalWait: waits.reduce((a, b) => a + b, 0), success };\n}\n",
    ],
    guide=G(
        prereqs="Loops and `Math.pow`. The lesson *Limited concurrency and async pitfalls*.",
        intuition="Knock on a door; if nobody answers, wait a little and knock again, waiting longer each time so you do not hammer a struggling service. "
                  "The cap stops the wait from growing without bound.",
        hints=["Count attempts from 0 up to `retries` inclusive.", "Only push a wait when another attempt will actually follow.", "Wait number k is `min(maxMs, baseMs * factor ** (k - 1))`."],
        brute_force="Pre-compute all `retries` waits and slice the list afterwards. Works, but it is easy to slice one element too many after a final failure.",
        approach="One loop.\n\n**Dry run** on the example: attempt 0 fails → wait `100 * 2^0 = 100`. Attempt 1 fails → wait `100 * 2^1 = 200`. Attempt 2 succeeds → stop. `attempts = 3`, `totalWait = 300`.",
        complexity="O(retries) time and space.",
        pitfalls="- Waiting after the last failed attempt (a pointless delay before reporting the error).\n- Forgetting the cap.\n- Off-by-one: `retries = 3` means 4 attempts.",
        follow_up="Production code adds *jitter* (a random fraction of the wait) so that many clients do not retry in lockstep.",
    ),
),
dict(
    id="node-priority-queue", title="A task queue with priorities and a concurrency limit", difficulty="Hard", pattern="Async control flow",
    kind="js", entry="schedulePriority",
    description=r"""
A job queue runs at most `concurrency` (≥ 1) jobs at once. Each job is `{id, at, ms, priority}`: it **arrives** at virtual time `at`, needs `ms` (≥ 1) milliseconds
of work, and has a numeric `priority` (larger = more urgent). Jobs are not necessarily listed in arrival order.

Whenever a slot is free and jobs are waiting, start the waiting job with the **highest priority**; ties go to the earlier `at`, then to the earlier position in the input.
A running job is never interrupted. At any instant, handle events in this order: completions, then arrivals, then starts.

Return the list of `{id, start, end}` in the order the jobs were started.

**Example:** jobs `A(at 0, 10ms, prio 1)`, `B(at 1, 5ms, prio 1)`, `C(at 2, 5ms, prio 9)`, `concurrency = 1`
→ `[{id:"A",start:0,end:10},{id:"C",start:10,end:15},{id:"B",start:15,end:20}]` (C jumps the queue, but cannot interrupt A).
""",
    starter="function schedulePriority(tasks, concurrency) {\n  // return [{ id, start, end }, ...] in start order\n}\n",
    solution=PRIORITY_SOLUTION,
    tests=[
        [[task("A", 10, at=0, priority=1), task("B", 5, at=1, priority=1), task("C", 5, at=2, priority=9)], 1],
        [[task("A", 10, at=0, priority=1), task("B", 5, at=1, priority=1), task("C", 5, at=2, priority=9)], 2],
        [[], 3],
        [[task("x", 4, at=7, priority=0)], 1],
        [[task("a", 3, at=0, priority=1), task("b", 3, at=0, priority=1), task("c", 3, at=0, priority=1)], 1],
        [[task("low", 3, at=0, priority=1), task("high", 3, at=0, priority=5), task("mid", 3, at=0, priority=3)], 1],
        [[task("late", 2, at=50, priority=9), task("early", 2, at=0, priority=0)], 1],
        [[task("a", 10, at=0, priority=0), task("b", 10, at=10, priority=0), task("c", 1, at=10, priority=5)], 1],
        [[task("a", 5, at=0, priority=2), task("b", 5, at=0, priority=2), task("c", 5, at=3, priority=7), task("d", 5, at=4, priority=7), task("e", 1, at=5, priority=1)], 2],
        [[task("z", 1, at=3, priority=1), task("y", 1, at=3, priority=1), task("x", 1, at=2, priority=1)], 1],
        [[task("j%d" % i, (i * 7) % 9 + 1, at=(i * 5) % 13, priority=i % 4) for i in range(30)], 3],
        [[task("j%d" % i, 2, at=0, priority=i % 5) for i in range(20)], 4],
    ],
    examples=2,
    wrong_solutions=[
        # plain FIFO: ignores priority
        r'''function schedulePriority(tasks, concurrency) {
  const pending = tasks.map((t, i) => ({ ...t, i })).sort((a, b) => a.at - b.at || a.i - b.i);
  const waiting = [], running = [], out = []; let now = 0, p = 0;
  while (p < pending.length || waiting.length || running.length) {
    for (let k = running.length - 1; k >= 0; k--) if (running[k] <= now) running.splice(k, 1);
    while (p < pending.length && pending[p].at <= now) waiting.push(pending[p++]);
    while (running.length < concurrency && waiting.length) { const j = waiting.shift(); running.push(now + j.ms); out.push({ id: j.id, start: now, end: now + j.ms }); }
    const c = running.slice(); if (p < pending.length) c.push(pending[p].at); if (!c.length) break; now = Math.min(...c);
  }
  return out;
}
''',
        # sorts everything by priority up front, ignoring arrival times
        r'''function schedulePriority(tasks, concurrency) {
  const jobs = tasks.map((t, i) => ({ ...t, i })).sort((a, b) => b.priority - a.priority || a.at - b.at || a.i - b.i);
  const slots = new Array(concurrency).fill(0), out = [];
  for (const j of jobs) { let k = 0; for (let s = 1; s < slots.length; s++) if (slots[s] < slots[k]) k = s; const start = Math.max(slots[k], j.at); slots[k] = start + j.ms; out.push({ id: j.id, start, end: start + j.ms }); }
  return out;
}
''',
    ],
    guide=G(
        prereqs="Solve *Run tasks with a concurrency limit* first. Sorting with several keys.",
        intuition="It is the car park again, but the line outside is sorted by urgency and cars arrive over time. "
                  "Only two kinds of moments matter: a job arrives or a job finishes. Jump from moment to moment and, at each one, fill free slots with the most urgent waiting job.",
        hints=["Sort a copy of the jobs by arrival time; keep `waiting` (arrived, not started) and `running` (end times).", "At each instant: drop finished jobs, admit arrivals with `at <= now`, sort `waiting` by `(-priority, at, index)`, start while slots are free.", "The next instant is the minimum of the running end times and the next arrival time."],
        brute_force="Tick the clock by 1 ms and redo the bookkeeping every tick: correct but O(total time). Event jumping does O(n) instants.",
        approach="Event loop over instants as in the hints.\n\n**Dry run** on the example (`concurrency = 1`): t=0: A arrives and starts (ends 10). Next instant: min(10, arrival of B at 1) = 1: B waits. t=2: C waits. "
                 "t=10: A is done; waiting sorted by priority is `[C, B]` → start C (10–15). t=15: start B (15–20).",
        complexity="O(n² log n) with re-sorting at each instant; O(n log n) with a binary heap as the waiting list. Space O(n).",
        pitfalls="- Sorting all jobs by priority once: a high-priority job that has not arrived yet cannot be started.\n- Starting jobs before admitting the arrivals of the same instant.\n- Pre-empting a running job; the model never interrupts.",
        follow_up="Add *ageing*: raise a job's priority the longer it waits, so low-priority work is not starved forever.",
    ),
),
dict(
    id="node-lines-from-chunks", title="Reassemble lines from stream chunks", difficulty="Easy", pattern="Streams",
    kind="js", entry="linesFromChunks",
    description=r"""
A stream delivers text in arbitrary **chunks**: a chunk boundary can fall anywhere, even in the middle of a line or between `\r` and `\n`.
Given the list of chunks in arrival order, return the list of lines.

- Lines end with `\n` or `\r\n`. The line terminator is not part of the line.
- Empty lines are kept.
- If the text does not end with a newline, the leftover text is the last line. If it ends with a newline, there is no extra empty line at the end.

**Example:** `["id,na", "me\n1,Ada\r", "\n2,Lin"]` → `["id,name", "1,Ada", "2,Lin"]`
""",
    starter="function linesFromChunks(chunks) {\n  // return an array of lines\n}\n",
    solution=LINES_SOLUTION,
    tests=[
        [["id,na", "me\n1,Ada\r", "\n2,Lin"]],
        [["one\ntwo\nthree\n"]],
        [[]],
        [["no newline at all"]],
        [["a", "b", "c", "\n", "d"]],
        [["\n\n\n"]],
        [["first\n\nthird"]],
        [["x\r\ny\r\n"]],
        [["", "", "late\n", ""]],
        [["tail\n", "\n"]],
        [list("h\ne\r\nll\n\no")],
        [["α,β\nγ", "δ\n"]],
        [["line%d\n" % i for i in range(50)]],
        [[("word%d" % i) + ("\n" if i % 7 == 0 else " ") for i in range(60)]],
    ],
    examples=2,
    wrong_solutions=[
        "function linesFromChunks(chunks) {\n  const lines = [];\n  for (const chunk of chunks) for (const line of chunk.split(/\\r?\\n/)) if (line !== \"\") lines.push(line);\n  return lines;\n}\n",
        "function linesFromChunks(chunks) {\n  return chunks.join(\"\").split(\"\\n\");\n}\n",
    ],
    guide=G(
        prereqs="`split`, `pop`, string concatenation. The lesson *Duplex, transform and pipeline* builds this as a Transform stream.",
        intuition="You are reading a letter that arrives torn into strips. Keep the unfinished last sentence in your hand (`rest`), glue the next strip to it, "
                  "and only put down the sentences that are certainly complete.",
        hints=["Keep a string `rest` holding text after the last newline seen so far.", "For each chunk: `(rest + chunk).split(\"\\n\")`; the **last** piece is the new `rest`, the others are finished lines.", "Strip one trailing `\\r` from each finished line; after the loop, emit `rest` if it is not empty."],
        brute_force="Join all chunks and split once. It gives the right lines for small inputs but defeats the point of streaming (the whole file is in memory), and a naive `split` leaves a trailing empty string.",
        approach="Carry-over buffer.\n\n**Dry run** on the example: chunk 1 → pieces `[\"id,na\"]`, rest `id,na`. Chunk 2 → `\"id,name\\n1,Ada\\r\"` splits into `[\"id,name\", \"1,Ada\\r\"]`: emit `id,name`, rest `1,Ada\\r`. "
                 "Chunk 3 → `\"1,Ada\\r\\n2,Lin\"` → emit `1,Ada` (after removing `\\r`), rest `2,Lin`. End → emit `2,Lin`.",
        complexity="O(total characters) time; extra space is one line at a time (plus the output).",
        pitfalls="- Splitting each chunk on its own, which cuts lines at chunk boundaries.\n- A `\\r\\n` pair split across two chunks.\n- Dropping empty lines, or adding a phantom empty line at the end.",
        follow_up="With bytes instead of strings a multi-byte UTF-8 character can also be split across chunks; Node's `StringDecoder` and `readline` handle that.",
    ),
),
dict(
    id="node-stream-pipeline", title="A transform pipeline with backpressure", difficulty="Hard", pattern="Streams",
    kind="js", entry="runPipeline",
    description=r"""
Model a pipeline `source → transforms → slow sink` and count what backpressure does.

- `chunks`: the source data, a list of non-empty strings.
- `transforms`: a list applied in order to every chunk as it flows. Each produces zero or more chunks:
  `["upper"]` (upper-case), `["prefix", s]` (put `s` in front), `["filter", s]` (keep only chunks containing `s`), `["split", sep]` (split on `sep`, dropping empty pieces).
- The sink has an internal buffer and a `highWaterMark` (≥ 1) measured in characters.

Time advances in **ticks**. While there is source data left or the buffer is not empty, one tick does:

- **(a) produce.** While the source is not paused and has chunks left: take the next source chunk, run it through the transforms, append every resulting chunk to the sink's buffer. Then, if the buffered size (total characters) is `>= highWaterMark`, the source becomes **paused** (this is `write()` returning `false`).
- **(b) consume.** The sink removes **one** chunk from the front of its buffer (if any) and appends it to the output.
- **(c) drain.** If the source is paused and the buffer is now empty, it is resumed (`'drain'` event).

Return `{output, ticks, drains, maxBuffered}`: the chunks received by the sink in order, the number of ticks, the number of drain events,
and the largest buffered size seen (measured in step (a), right after a source chunk's results are appended).

**Example:** `runPipeline(["ab","cd","ef","gh"], [["upper"]], 4)` → `{output:["AB","CD","EF","GH"], ticks:4, drains:2, maxBuffered:4}`
""",
    starter="function runPipeline(chunks, transforms, highWaterMark) {\n  // return { output, ticks, drains, maxBuffered }\n}\n",
    solution=PIPELINE_SOLUTION,
    tests=[
        [["ab", "cd", "ef", "gh"], [["upper"]], 4],
        [["ab", "cd", "ef", "gh"], [], 100],
        [[], [["upper"]], 4],
        [["a", "b", "c", "d", "e"], [], 1],
        [["a,b,c", "d,e", "f"], [["split", ","]], 3],
        [["keep me", "drop", "keep too", "nope"], [["filter", "keep"], ["upper"]], 8],
        [["x", "y", "z"], [["filter", "q"]], 2],
        [["one two", "three", "four five six"], [["split", " "], ["prefix", "> "]], 10],
        [["aaaaaaaaaa", "b", "c"], [], 4],
        [["a", "b", "cccccccc", "d", "e", "f"], [["upper"]], 5],
        [["ok;err;ok", "err", "ok;ok"], [["split", ";"], ["filter", "ok"], ["prefix", "#"]], 6],
        [["chunk%d" % i for i in range(40)], [["upper"]], 16],
        [["%d,%d" % (i, i * i) for i in range(30)], [["split", ","], ["filter", "1"]], 7],
    ],
    examples=1,
    wrong_solutions=[
        # ignores backpressure: writes everything at once
        r'''function runPipeline(chunks, transforms, highWaterMark) {
  const apply = (c) => { let it = [c]; for (const [k, a] of transforms) { if (k === "upper") it = it.map((s) => s.toUpperCase()); else if (k === "prefix") it = it.map((s) => a + s); else if (k === "filter") it = it.filter((s) => s.includes(a)); else it = it.flatMap((s) => s.split(a).filter((p) => p !== "")); } return it; };
  const buffer = chunks.flatMap(apply), output = [];
  let size = buffer.reduce((n, s) => n + s.length, 0), ticks = 0;
  const maxBuffered = size;
  while (buffer.length) { ticks++; output.push(buffer.shift()); }
  return { output, ticks, drains: 0, maxBuffered };
}
''',
        # resumes as soon as the buffer drops below the mark instead of when it is empty
        r'''function runPipeline(chunks, transforms, highWaterMark) {
  const apply = (c) => { let it = [c]; for (const [k, a] of transforms) { if (k === "upper") it = it.map((s) => s.toUpperCase()); else if (k === "prefix") it = it.map((s) => a + s); else if (k === "filter") it = it.filter((s) => s.includes(a)); else it = it.flatMap((s) => s.split(a).filter((p) => p !== "")); } return it; };
  const buffer = [], output = [];
  let size = 0, i = 0, paused = false, ticks = 0, drains = 0, maxBuffered = 0;
  while (i < chunks.length || buffer.length) {
    ticks++;
    while (!paused && i < chunks.length) { for (const x of apply(chunks[i++])) { buffer.push(x); size += x.length; } if (size > maxBuffered) maxBuffered = size; if (size >= highWaterMark) paused = true; }
    if (buffer.length) { const c = buffer.shift(); size -= c.length; output.push(c); }
    if (paused && size < highWaterMark) { paused = false; drains++; }
  }
  return { output, ticks, drains, maxBuffered };
}
''',
    ],
    guide=G(
        prereqs="Queues, `flatMap`, careful loop bookkeeping. The lessons *Why streams: readable, writable and backpressure* and *Duplex, transform and pipeline*.",
        intuition="A fast tap fills a sink with a narrow drain. The sink has a line painted on its side (the high-water mark). When the water reaches the line, "
                  "somebody shouts \"stop\" and the tap closes; when the sink has emptied, they shout \"go\". Memory stays bounded however much water there is in total.",
        hints=["Write `apply(chunk)` first: start with `[chunk]` and let each transform map the list to a new list.", "Keep `buffer`, its `size` in characters, the source index `i` and a `paused` flag; follow steps (a), (b), (c) literally inside one `while`.", "The pause check happens after *each source chunk's* outputs are appended, so the buffer may overshoot the mark; that overshoot is what `maxBuffered` records."],
        brute_force="Transform everything first, then count: the output is right but `ticks`, `drains` and `maxBuffered` are wrong, because that is exactly the no-backpressure behaviour.",
        approach="Direct simulation.\n\n**Dry run** on the example (mark 4): tick 1 (a): write `AB` (size 2), write `CD` (size 4 ≥ 4 → paused); (b) consume `AB`; buffer not empty. "
                 "Tick 2: paused; consume `CD`; buffer empty → drain 1. Tick 3: write `EF`, `GH` (size 4 → paused); consume `EF`. Tick 4: consume `GH`; empty → drain 2. "
                 "`ticks 4, drains 2, maxBuffered 4`.",
        complexity="O(total characters) time; the buffer never holds much more than `highWaterMark` characters plus one source chunk's output.",
        pitfalls="- Resuming when the size falls below the mark; `'drain'` fires when the buffer has been emptied.\n- Measuring the mark in chunks instead of characters.\n- A filter that removes everything: the loop must still end.",
        follow_up="Give every transform its own buffer and high-water mark, as real Transform streams have, and watch the pause signal travel backwards stage by stage.",
    ),
),
dict(
    id="node-factory", title="A shape factory with private counters", difficulty="Easy", pattern="Creational patterns",
    kind="js", entry="runFactory",
    description=r"""
Write a **factory**: one function that decides which kind of object to create from a plain description, so callers never use `new` or know the concrete classes.

`runFactory(requests)` receives a list of descriptions and returns one result per request.

| `type` | fields | area |
|---|---|---|
| `"circle"` | `r` | π·r² |
| `"rect"` | `w`, `h` | w·h |
| `"square"` | `side` | side² |
| `"triangle"` | `base`, `height` | base·height / 2 |

For a known type the result is `{kind, label, area}`: `kind` is the type, `area` is rounded to 2 decimals (`Math.round(x * 100) / 100`), and `label` is
`"<type>#<n>"` where `n` counts how many shapes of that type this factory has created so far (starting at 1).
For an unknown type the result is `{error: "unknown shape: <type>"}` and no counter changes.

**Example:** `[{type:"circle",r:1},{type:"hexagon"},{type:"circle",r:2}]` → `[{kind:"circle",label:"circle#1",area:3.14},{error:"unknown shape: hexagon"},{kind:"circle",label:"circle#2",area:12.57}]`
""",
    starter="function runFactory(requests) {\n  // create each shape through one factory function\n}\n",
    solution=FACTORY_SOLUTION,
    tests=[
        [[{"type": "circle", "r": 1}, {"type": "hexagon"}, {"type": "circle", "r": 2}]],
        [[{"type": "rect", "w": 3, "h": 4}, {"type": "square", "side": 5}, {"type": "triangle", "base": 3, "height": 5}]],
        [[]],
        [[{"type": "square", "side": 0}]],
        [[{"type": "square", "side": 1.5}, {"type": "square", "side": 2.5}, {"type": "rect", "w": 1.5, "h": 2.5}, {"type": "square", "side": 1}]],
        [[{"type": "toString"}, {"type": "constructor"}]],
        [[{"type": "circle", "r": 0.1}, {"type": "circle", "r": 10}, {"type": "circle", "r": 2.5}]],
        [[{"type": "triangle", "base": 1, "height": 1}, {"type": "Triangle", "base": 1, "height": 1}, {"type": "triangle", "base": 7, "height": 3}]],
        [[{"type": "rect", "w": 0.1, "h": 0.2}, {"type": "rect", "w": 1.005, "h": 1}]],
        [[{"type": ["circle", "rect", "square", "triangle", "blob"][i % 5], "r": i, "w": i, "h": i + 1, "side": i, "base": i, "height": 3} for i in range(25)]],
    ],
    examples=2,
    wrong_solutions=[
        "function runFactory(requests) {\n  let n = 0;\n  const area = { circle: (o) => Math.PI * o.r * o.r, rect: (o) => o.w * o.h, square: (o) => o.side * o.side, triangle: (o) => o.base * o.height / 2 };\n  return requests.map((o) => { if (!Object.hasOwn(area, o.type)) return { error: 'unknown shape: ' + o.type }; n++; return { kind: o.type, label: o.type + '#' + n, area: Math.round(area[o.type](o) * 100) / 100 }; });\n}\n",
        "function runFactory(requests) {\n  const c = {};\n  const area = { circle: (o) => Math.PI * o.r * o.r, rect: (o) => o.w * o.h, square: (o) => o.side * o.side, triangle: (o) => o.base * o.height / 2 };\n  return requests.map((o) => { c[o.type] = (c[o.type] || 0) + 1; if (!area[o.type]) return { error: 'unknown shape: ' + o.type }; return { kind: o.type, label: o.type + '#' + c[o.type], area: Math.round(area[o.type](o) * 100) / 100 }; });\n}\n",
    ],
    guide=G(
        prereqs="Objects as lookup tables, closures. The lesson *Factory, builder and revealing constructor*.",
        intuition="A factory is the counter at a bakery: you say what you want, the staff decide how to make it, and the kitchen (here, the counters) stays out of reach. "
                  "A table from type name to maker function replaces a long `if`/`else` chain.",
        hints=["Create a `makers` object keyed by type whose values compute the area.", "Keep the per-type counters in a variable that only the factory function can see (a closure).", "Check that the type is a real key with `Object.hasOwn(makers, type)` before touching any counter."],
        brute_force="A `switch` with one case per shape. Fine for four shapes; the lookup table scales better and makes adding a shape a one-line change.",
        approach="`createShape(options)` validates, bumps the counter, returns the object; `runFactory` maps requests through it.\n\n"
                 "**Dry run** on the example: circle r=1 → counter circle=1 → `circle#1`, area `3.14159…` → `3.14`. `hexagon` → error, counters untouched. circle r=2 → `circle#2`, area `12.566…` → `12.57`.",
        complexity="O(1) per request, O(number of types) space.",
        pitfalls="- One global counter instead of one per type.\n- Incrementing the counter for unknown types.\n- `makers[type]` being truthy for inherited names such as `toString`; use `Object.hasOwn`.",
        follow_up="Let callers `register(type, maker)` new shapes at run time, turning the factory into a plugin registry.",
    ),
),
dict(
    id="node-builder", title="A fluent query builder", difficulty="Medium", pattern="Creational patterns",
    kind="js", entry="buildQuery",
    description=r"""
Implement the **builder** pattern for SQL-like `SELECT` statements. `buildQuery(steps)` applies a list of method calls to a builder and returns
the string produced by `build()`. Each step is `[methodName, ...arguments]`:

| step | effect |
|---|---|
| `["from", table]` | set the table (a later call replaces an earlier one) |
| `["select", col1, col2, …]` | add columns (calls accumulate, order kept). No columns at all means `*` |
| `["where", condition]` | add a condition; conditions are wrapped in parentheses and joined with ` AND ` |
| `["orderBy", column, direction?]` | add a sort key; direction is `"asc"` (default) or `"desc"`, printed in upper case |
| `["limit", n]` | set the limit (last call wins) |
| `["offset", n]` | set the offset (last call wins) |

`build()` validates, checking in this order, and returns the first problem as a string:
1. no table → `"error: from is required"`;
2. a limit that is not a positive integer → `"error: limit must be a positive integer"`;
3. an offset without a limit → `"error: offset requires limit"`.

Otherwise it returns `SELECT <cols> FROM <table>[ WHERE …][ ORDER BY a ASC, b DESC][ LIMIT n][ OFFSET m]`. The order of the steps must not matter for the clause order.

**Example:** `[["where","age >= 18"],["from","users"],["select","id","name"],["orderBy","name"],["limit",10]]`
→ `"SELECT id, name FROM users WHERE (age >= 18) ORDER BY name ASC LIMIT 10"`
""",
    starter="function buildQuery(steps) {\n  // apply the steps to a builder, then return builder.build()\n}\n",
    solution=BUILDER_SOLUTION,
    tests=[
        [[["where", "age >= 18"], ["from", "users"], ["select", "id", "name"], ["orderBy", "name"], ["limit", 10]]],
        [[["from", "orders"]]],
        [[["select", "id"]]],
        [[]],
        [[["from", "t"], ["limit", 0]]],
        [[["from", "t"], ["limit", 2.5]]],
        [[["from", "t"], ["offset", 20]]],
        [[["offset", 20], ["limit", -1]]],
        [[["from", "a"], ["from", "b"], ["select", "x"], ["select", "y", "z"]]],
        [[["from", "logs"], ["where", "level = 'error'"], ["where", "ts > 100"], ["where", "host <> ''"]]],
        [[["from", "p"], ["orderBy", "price", "desc"], ["orderBy", "name"], ["orderBy", "id", "asc"]]],
        [[["limit", 5], ["limit", 50], ["offset", 100], ["offset", 0], ["from", "big"]]],
        [[["orderBy", "created", "desc"], ["limit", 3], ["offset", 6], ["where", "published = 1"], ["select", "title"], ["from", "posts"], ["select", "slug"]]],
    ],
    examples=2,
    wrong_solutions=[
        # emits clauses in call order
        r'''function buildQuery(steps) {
  let table = null, cols = [], tail = "", lim, off;
  for (const [m, ...a] of steps) {
    if (m === "from") table = a[0];
    else if (m === "select") cols.push(...a);
    else if (m === "where") tail += (tail.includes(" WHERE ") ? " AND " : " WHERE ") + "(" + a[0] + ")";
    else if (m === "orderBy") tail += (tail.includes(" ORDER BY ") ? ", " : " ORDER BY ") + a[0] + " " + (a[1] || "asc").toUpperCase();
    else if (m === "limit") lim = a[0];
    else off = a[0];
  }
  if (table === null) return "error: from is required";
  if (lim !== undefined && !(Number.isInteger(lim) && lim > 0)) return "error: limit must be a positive integer";
  if (off !== undefined && lim === undefined) return "error: offset requires limit";
  return "SELECT " + (cols.length ? cols.join(", ") : "*") + " FROM " + table + tail + (lim !== undefined ? " LIMIT " + lim : "") + (off !== undefined ? " OFFSET " + off : "");
}
''',
        # validation in the wrong order and truthiness checks
        r'''function buildQuery(steps) {
  const q = { table: null, cols: [], conds: [], orders: [] };
  for (const [m, ...a] of steps) {
    if (m === "from") q.table = a[0]; else if (m === "select") q.cols.push(...a); else if (m === "where") q.conds.push(a[0]);
    else if (m === "orderBy") q.orders.push(a[0] + " " + (a[1] || "asc").toUpperCase()); else if (m === "limit") q.lim = a[0]; else q.off = a[0];
  }
  if (q.off && !q.lim) return "error: offset requires limit";
  if (q.table === null) return "error: from is required";
  if (q.lim !== undefined && !(Number.isInteger(q.lim) && q.lim > 0)) return "error: limit must be a positive integer";
  let s = "SELECT " + (q.cols.length ? q.cols.join(", ") : "*") + " FROM " + q.table;
  if (q.conds.length) s += " WHERE " + q.conds.map((c) => "(" + c + ")").join(" AND ");
  if (q.orders.length) s += " ORDER BY " + q.orders.join(", ");
  if (q.lim) s += " LIMIT " + q.lim;
  if (q.off) s += " OFFSET " + q.off;
  return s;
}
''',
    ],
    guide=G(
        prereqs="Classes, methods that `return this`, rest parameters. The lesson *Factory, builder and revealing constructor*.",
        intuition="Ordering a custom sandwich: you call out choices in any order, the person behind the counter notes them down, and only when you say \"that's all\" "
                  "do they check the order makes sense and assemble it in the proper layering. Setters collect; `build()` validates and assembles.",
        hints=["Give the builder one field per clause: a table, and arrays for columns, conditions and sort keys.", "Every setter stores its input and returns `this`; no string is assembled until `build()`.", "In `build()` run the three validations in the stated order, then append the optional clauses in SQL order."],
        brute_force="Concatenate a string as the calls arrive. It breaks when calls come in a different order, and it cannot validate combinations (offset without limit).",
        approach="Collect, then assemble.\n\n**Dry run** on the example: after all steps the builder holds table `users`, columns `[id, name]`, conditions `[age >= 18]`, orders `[name ASC]`, limit 10. "
                 "Validation passes, so `build()` emits `SELECT id, name FROM users` + ` WHERE (age >= 18)` + ` ORDER BY name ASC` + ` LIMIT 10`.",
        complexity="O(total size of the inputs) time and space.",
        pitfalls="- `if (limit)` treats `0` as \"not set\"; compare with `undefined`.\n- `offset 0` is a legitimate value and must be printed.\n- Validating inside setters makes the result depend on call order.",
        follow_up="Never build real SQL by pasting user input into strings (SQL injection). Real builders such as Knex emit placeholders (`?`) plus a separate parameter list.",
    ),
),
dict(
    id="node-di-container", title="Dependency injection: resolution order and cycles", difficulty="Medium", pattern="Creational patterns",
    kind="js", entry="resolveOrder",
    description=r"""
A dependency-injection container knows, for every service name, the list of services it needs: `registry = {name: [dependency, …]}`.
To build `target` it must first build each dependency (in the listed order, depth-first), and each service is built **once** (a singleton).

`resolveOrder(registry, target)` returns the list of service names in the order they are instantiated, ending with `target`.

Errors are returned as an object instead:
- a name that is not registered → `{error: "missing: <name>"}`;
- a dependency cycle → `{error: "cycle: a -> b -> c -> a"}`, listing the cycle from the service where it starts back to itself.

The first problem met during the depth-first walk is the one reported.

**Example:** `registry = {app:["db","logger"], db:["config","logger"], logger:["config"], config:[]}`, `target = "app"` → `["config","logger","db","app"]`.
With `{a:["b"], b:["c"], c:["a"]}` and target `"a"` → `{error:"cycle: a -> b -> c -> a"}`.
""",
    starter="function resolveOrder(registry, target) {\n  // return an array of names, or { error }\n}\n",
    solution=DI_SOLUTION,
    tests=[
        [{"app": ["db", "logger"], "db": ["config", "logger"], "logger": ["config"], "config": []}, "app"],
        [{"a": ["b"], "b": ["c"], "c": ["a"]}, "a"],
        [{"solo": []}, "solo"],
        [{"solo": []}, "ghost"],
        [{"app": ["db", "cache"], "db": []}, "app"],
        [{"self": ["self"]}, "self"],
        [{"t": ["a"], "a": ["b"], "b": ["a"]}, "t"],
        [{"app": ["db", "logger"], "db": ["config", "logger"], "logger": ["config"], "config": []}, "logger"],
        [{"x": ["y", "z"], "y": ["w"], "z": ["w"], "w": []}, "x"],
        [{"x": ["y", "z"], "y": ["nope"], "z": ["x"]}, "x"],
        [{"x": ["y", "z"], "y": [], "z": ["x"], "unused": ["x"]}, "x"],
        [{"a": ["b", "c"], "b": ["d"], "c": ["d", "e"], "d": ["e"], "e": [], "f": ["a"]}, "f"],
        [{("s%d" % i): (["s%d" % (i + 1)] if i < 60 else []) for i in range(61)}, "s0"],
        [{**{("s%d" % i): ["s%d" % (i + 1)] for i in range(20)}, "s20": ["s7"]}, "s0"],
    ],
    examples=2,
    wrong_solutions=[
        # marks nodes as done on entry, so cycles are silently "resolved"
        r'''function resolveOrder(registry, target) {
  const order = [], seen = new Set();
  function visit(name) {
    if (seen.has(name)) return null;
    if (!Object.hasOwn(registry, name)) return "missing: " + name;
    seen.add(name);
    for (const d of registry[name]) { const e = visit(d); if (e) return e; }
    order.push(name); return null;
  }
  const e = visit(target);
  return e ? { error: e } : order;
}
''',
        # reports the whole stack as the cycle
        r'''function resolveOrder(registry, target) {
  const order = [], done = new Set(), stack = [];
  function visit(name) {
    if (done.has(name)) return null;
    if (!Object.hasOwn(registry, name)) return "missing: " + name;
    if (stack.includes(name)) return "cycle: " + stack.concat(name).join(" -> ");
    stack.push(name);
    for (const d of registry[name]) { const e = visit(d); if (e) return e; }
    stack.pop(); done.add(name); order.push(name); return null;
  }
  const e = visit(target);
  return e ? { error: e } : order;
}
''',
    ],
    guide=G(
        prereqs="Recursion and depth-first search, `Set`. The lesson *Singleton, module wiring and dependency injection*.",
        intuition="Getting dressed: socks before shoes. To put on an item, first put on everything it needs. If while dressing you find that the item you need "
                  "is one you are *currently in the middle of* putting on, the instructions are circular. So track two things: finished items, and the chain in progress.",
        hints=["Depth-first search that appends a name **after** visiting all its dependencies (post-order).", "Keep `done` (a Set of finished services) and `stack` (the chain being built right now, an array).", "If a name is already on the stack, the cycle is `stack.slice(indexOf(name))` plus the name again."],
        brute_force="Repeatedly scan the registry for a service whose dependencies are all built: O(n²), and it cannot easily say *which* services form the cycle.",
        approach="`visit(name)`: done → skip; unregistered → missing; on stack → cycle; else push, visit deps, pop, mark done, append.\n\n"
                 "**Dry run** on the first example: visit `app` → `db` → `config` (no deps) → order `[config]`; back in `db` → `logger` → `config` done → order `[config, logger]`; "
                 "`db` done → `[config, logger, db]`; back in `app`, `logger` already done; append `app`.",
        complexity="O(V + E) visits; with `indexOf` on the stack the worst case is O(V·depth). Space O(V).",
        pitfalls="- Using one `visited` set for both purposes: a cycle then looks like an already-built service and a broken order is returned.\n"
                 "- Reporting the whole path from the target instead of the cycle only (`t -> a -> b -> a` should be `a -> b -> a`).\n- Building a shared dependency twice.",
        follow_up="Extend the container so each registration has a factory function and `resolve(name)` returns the built instance; add a `transient` lifetime that builds a fresh instance every time.",
    ),
),
]
