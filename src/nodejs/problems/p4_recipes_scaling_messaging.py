"""Node.js problems, part 4: advanced recipes, scalability and messaging."""


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


def R(*pairs):
    return [{"t": t, "key": k} for t, k in pairs]


def S(name, ms, abortable=False):
    d = {"name": name, "ms": ms}
    if abortable:
        d["abortable"] = True
    return d


BATCH_SOLUTION = r'''function batchAndCache(requests, duration, ttl) {
  const lastStart = new Map();                   // key -> time the latest fetch started
  let fetches = 0;
  const results = requests.map(({ t, key }) => {
    if (lastStart.has(key)) {
      const done = lastStart.get(key) + duration;
      if (t < done) return { source: "batched", doneAt: done };        // piggyback on the fetch in flight
      if (t < done + ttl) return { source: "cache", doneAt: t };       // fresh cached value
    }
    lastStart.set(key, t);
    fetches++;
    return { source: "fetch", doneAt: t + duration };
  });
  return { results, fetches };
}
'''

CANCEL_SOLUTION = r'''function runCancelable(steps, cancelAt) {
  const completed = [];
  let now = 0;
  for (const step of steps) {
    if (cancelAt !== null && now >= cancelAt) return { completed, status: "cancelled", endedAt: now };
    const end = now + step.ms;
    if (step.abortable && cancelAt !== null && cancelAt < end) {
      return { completed, status: "cancelled", endedAt: cancelAt };    // interrupted mid-step
    }
    now = end;
    completed.push(step.name);
  }
  return { completed, status: "done", endedAt: now };
}
'''

LRU_SOLUTION = r'''function runLru(capacity, ops) {
  const map = new Map();                         // insertion order = least to most recently used
  return ops.map(([op, key, value]) => {
    if (op === "get") {
      if (!map.has(key)) return -1;
      const found = map.get(key);
      map.delete(key);
      map.set(key, found);                       // move to the "most recent" end
      return found;
    }
    if (op === "put") {
      let evicted = null;
      if (map.has(key)) map.delete(key);
      else if (map.size >= capacity) {
        evicted = map.keys().next().value;       // the oldest entry
        map.delete(evicted);
      }
      map.set(key, value);
      return evicted;
    }
    return [...map.keys()];                      // "keys": least recent first
  });
}
'''

RR_SOLUTION = r'''function balance(workers, events) {
  const down = new Set();
  let pointer = 0;
  return events.map(([type, name]) => {
    if (type === "down") { down.add(name); return null; }
    if (type === "up") { down.delete(name); return null; }
    for (let step = 0; step < workers.length; step++) {
      const index = (pointer + step) % workers.length;
      if (!down.has(workers[index])) {
        pointer = (index + 1) % workers.length;
        return workers[index];
      }
    }
    return null;                                 // nobody is healthy
  });
}
'''

HASH_SOLUTION = r'''function consistentHash(replicas, ops) {
  const hash = (text) => {
    let h = 2166136261;
    for (let i = 0; i < text.length; i++) {
      h ^= text.charCodeAt(i);
      h = Math.imul(h, 16777619) >>> 0;
    }
    return h;
  };
  let ring = [];                                 // sorted list of { hash, label, node }
  return ops.map(([op, name]) => {
    if (op === "add") {
      if (!ring.some((point) => point.node === name)) {
        for (let i = 0; i < replicas; i++) {
          const label = name + "#" + i;
          ring.push({ hash: hash(label), label, node: name });
        }
        ring.sort((a, b) => a.hash - b.hash || (a.label < b.label ? -1 : 1));
      }
      return null;
    }
    if (op === "remove") {
      ring = ring.filter((point) => point.node !== name);
      return null;
    }
    if (ring.length === 0) return null;
    const h = hash(name);
    let low = 0, high = ring.length;             // first point with hash >= h
    while (low < high) {
      const mid = (low + high) >> 1;
      if (ring[mid].hash >= h) high = mid;
      else low = mid + 1;
    }
    return ring[low === ring.length ? 0 : low].node;
  });
}
'''

PUBSUB_SOLUTION = r'''function runBroker(ops) {
  const subscriptions = new Map();               // client -> Set of patterns
  const inbox = {};
  const deliveries = [];
  const matches = (pattern, topic) => {
    if (pattern.length === 0) return topic.length === 0;
    if (pattern[0] === "#") {
      for (let skip = 0; skip <= topic.length; skip++) {
        if (matches(pattern.slice(1), topic.slice(skip))) return true;
      }
      return false;
    }
    if (topic.length === 0) return false;
    return (pattern[0] === "*" || pattern[0] === topic[0]) && matches(pattern.slice(1), topic.slice(1));
  };
  for (const [op, a, b] of ops) {
    if (op === "sub") {
      if (!subscriptions.has(a)) { subscriptions.set(a, new Set()); inbox[a] = []; }
      subscriptions.get(a).add(b);
    } else if (op === "unsub") {
      if (subscriptions.has(a)) subscriptions.get(a).delete(b);
    } else {
      const words = a.split(".");
      const receivers = [];
      for (const [client, patterns] of subscriptions) {
        if ([...patterns].some((pattern) => matches(pattern.split("."), words))) {
          receivers.push(client);
          inbox[client].push(b);
        }
      }
      deliveries.push(receivers.sort());
    }
  }
  return { deliveries, inbox };
}
'''

WORKQ_SOLUTION = r'''function runWorkQueue(ops) {
  const ready = [];                              // messages waiting for a worker
  const idle = [];                               // idle workers, longest-idle first
  const holding = new Map();                     // worker -> unacknowledged message
  const members = new Set();
  const deliveries = [], acked = [];

  const dispatch = () => {
    while (ready.length > 0 && idle.length > 0) {
      const worker = idle.shift();
      const message = ready.shift();
      holding.set(worker, message);
      deliveries.push([worker, message]);
    }
  };

  for (const [op, a, b] of ops) {
    if (op === "send") ready.push(a);
    else if (op === "join") {
      if (!members.has(a)) { members.add(a); idle.push(a); }
    } else if (op === "leave") {
      if (members.has(a)) {
        members.delete(a);
        if (holding.has(a)) { ready.unshift(holding.get(a)); holding.delete(a); }
        else idle.splice(idle.indexOf(a), 1);
      }
    } else if (op === "ack" || op === "nack") {
      if (holding.get(a) === b && holding.has(a)) {
        holding.delete(a);
        idle.push(a);
        if (op === "ack") acked.push(b);
        else ready.unshift(b);
      }
    }
    dispatch();
  }
  const unacked = {};
  for (const [worker, message] of holding) unacked[worker] = message;
  return { deliveries, ready, unacked, acked };
}
'''

REPLY_SOLUTION = r'''function correlate(events) {
  const requests = new Map();                    // id -> { expires, state }
  const resolved = {};
  const stats = { late: 0, unknown: 0, duplicate: 0 };
  for (const [type, t, id, extra] of events) {
    if (type === "request") {
      requests.set(id, { expires: t + extra, state: "pending" });
      continue;
    }
    const request = requests.get(id);
    if (!request) stats.unknown++;
    else if (request.state === "resolved") stats.duplicate++;
    else if (t >= request.expires) { request.state = "timedOut"; stats.late++; }
    else { request.state = "resolved"; resolved[id] = extra; }
  }
  const timedOut = [...requests]
    .filter(([, request]) => request.state !== "resolved")
    .sort((a, b) => a[1].expires - b[1].expires || (a[0] < b[0] ? -1 : 1))
    .map(([id]) => id);
  return { resolved, timedOut, stats };
}
'''

PROBLEMS = [
dict(
    id="node-batch-cache", title="Request batching and caching", difficulty="Medium", pattern="Advanced recipes",
    kind="js", entry="batchAndCache",
    description=r"""
An API server answers requests by key. Computing the answer for a key (a database query, say) takes `duration` ms. Two optimisations are layered on top:

- **Batching:** if a fetch for the same key is already in flight, a new request does not start another one; it waits for the running fetch and finishes when that fetch finishes.
- **Caching:** when a fetch completes at time `c`, its value stays valid for `ttl` ms: a request arriving at time `t` with `c <= t < c + ttl` is answered instantly from the cache.

`requests` is a list of `{t, key}` sorted by `t`. For each request return `{source, doneAt}` where `source` is `"fetch"` (it started a new fetch; done at `t + duration`),
`"batched"` (joined a fetch in flight; done when that fetch ends) or `"cache"` (done at `t`). Also return the number of fetches started.

A fetch started at `s` is in flight while `s <= t < s + duration`. Keys are independent of each other. `ttl` may be 0 (batching only).

**Example:** `duration = 100`, `ttl = 50`, requests for key `"a"` at t = 0, 30, 100, 149, 150
→ sources `fetch` (done 100), `batched` (100), `cache` (100), `cache` (149), `fetch` (250); `fetches = 2`.
""",
    starter="function batchAndCache(requests, duration, ttl) {\n  // return { results: [{ source, doneAt }], fetches }\n}\n",
    solution=BATCH_SOLUTION,
    tests=[
        [R((0, "a"), (30, "a"), (100, "a"), (149, "a"), (150, "a")), 100, 50],
        [R((0, "a"), (0, "a"), (0, "b"), (99, "a"), (99, "b")), 100, 0],
        [[], 100, 50],
        [R((5, "x")), 10, 10],
        [R((0, "a"), (100, "a"), (200, "a"), (300, "a")), 100, 0],
        [R((0, "a"), (100, "a"), (200, "a"), (300, "a")), 100, 1],
        [R((0, "a"), (50, "b"), (60, "a"), (120, "b"), (149, "b"), (151, "b"), (400, "a")), 100, 1000],
        [R((0, "k"), (10, "k"), (20, "k"), (30, "k"), (40, "k")), 25, 10],
        [R((0, "u1"), (1, "u2"), (2, "u1"), (3, "u2"), (4, "u3")), 1, 1],
        [R((0, "a"), (1000, "a"), (1001, "a"), (1100, "a"), (1101, "a"), (1102, "a")), 100, 1],
        [R(*[(i * 7, "k%d" % (i % 3)) for i in range(40)]), 20, 15],
        [R(*[(i, "same") for i in range(0, 200, 9)]), 30, 30],
    ],
    examples=1,
    wrong_solutions=[
        # cache window starts when the fetch starts instead of when it completes
        r'''function batchAndCache(requests, duration, ttl) {
  const last = new Map(); let fetches = 0;
  const results = requests.map(({ t, key }) => {
    if (last.has(key)) { const s = last.get(key); if (t < s + duration) return { source: "batched", doneAt: s + duration }; if (t < s + ttl) return { source: "cache", doneAt: t }; }
    last.set(key, t); fetches++; return { source: "fetch", doneAt: t + duration };
  });
  return { results, fetches };
}
''',
        # one global fetch slot instead of one per key
        r'''function batchAndCache(requests, duration, ttl) {
  let s = null, fetches = 0;
  const results = requests.map(({ t }) => {
    if (s !== null) { const done = s + duration; if (t < done) return { source: "batched", doneAt: done }; if (t < done + ttl) return { source: "cache", doneAt: t }; }
    s = t; fetches++; return { source: "fetch", doneAt: t + duration };
  });
  return { results, fetches };
}
''',
    ],
    guide=G(
        prereqs="`Map`, interval reasoning. The lesson *Async initialisation, request batching and caching*.",
        intuition="Ten colleagues want the same report. The first one asks the archive; the other nine, seeing a request is already out, wait for that same copy (batching). "
                  "For a while afterwards the copy on the desk is handed to anyone who asks (caching). Then it is considered stale and someone asks the archive again.",
        hints=["Per key you only need one number: when the latest fetch started.", "With `done = start + duration`, a request at `t` is batched if `t < done`, cached if `t < done + ttl`, otherwise it starts a new fetch.", "Batched and cached requests do not change the stored start time."],
        brute_force="For each request scan all earlier requests of the same key to find the latest fetch: O(n²). A map from key to the latest start makes it O(n).",
        approach="One pass with a `Map`.\n\n**Dry run** on the example (duration 100, ttl 50): t=0 → fetch, start 0, done 100. t=30 → `30 < 100` → batched, done 100. "
                 "t=100 → not `< 100`, but `< 150` → cache. t=149 → cache. t=150 → not `< 150` → new fetch, done 250.",
        complexity="O(n) time, O(distinct keys) space.",
        pitfalls="- Starting the cache lifetime at the fetch's start.\n- Off-by-one at the boundaries: at `t = done` the value is already cached; at `t = done + ttl` it has expired.\n- Sharing state between keys.",
        follow_up="In real code the map stores the **promise** of the running fetch: `if (running.has(key)) return running.get(key)`. Add error handling: a failed fetch must not be cached.",
    ),
),
dict(
    id="node-cancel-token", title="Cooperative cancellation", difficulty="Medium", pattern="Advanced recipes",
    kind="js", entry="runCancelable",
    description=r"""
An asynchronous operation runs `steps` one after another in virtual time, starting at 0. Each step is `{name, ms, abortable?}`.
Somebody may request cancellation at time `cancelAt` (`null` means never), as with `AbortController.abort()`.

JavaScript cannot interrupt running code from outside, so cancellation is **cooperative**:

1. Before starting each step the operation checks the cancel signal. If cancellation has been requested (`now >= cancelAt`), it stops there.
2. A normal step, once started, always runs to its end, even if the cancel request arrives in the middle.
3. An **abortable** step (one that was handed the signal, like `fetch(url, {signal})`) is interrupted at the instant of the request: if `cancelAt` is before the step's end, the operation ends at `cancelAt` and the step does not count as completed.
4. After the last step finishes the operation is done; a cancel request arriving at that moment or later has no effect.

Return `{completed, status, endedAt}` where `completed` lists the names of the finished steps and `status` is `"done"` or `"cancelled"`.

**Example:** steps `read 10ms`, `parse 20ms`, `upload 50ms (abortable)`, `cancelAt = 40` → `{completed:["read","parse"], status:"cancelled", endedAt:40}`.
With `cancelAt = 15` → `{completed:["read","parse"], status:"cancelled", endedAt:30}` (parse was already running and is not abortable).
""",
    starter="function runCancelable(steps, cancelAt) {\n  // return { completed, status, endedAt }\n}\n",
    solution=CANCEL_SOLUTION,
    tests=(lambda steps: [
        [steps, 40],
        [steps, 15],
        [steps, None],
        [steps, 0],
        [steps, 10],
        [steps, 30],
        [steps, 79],
        [steps, 80],
        [steps, 500],
        [[], 5],
        [[], None],
        [[S("a", 10, True), S("b", 10, True)], 10],
        [[S("a", 10, True), S("b", 10)], 5],
        [[S("a", 0), S("b", 0), S("c", 5)], 0],
        [[S("s%d" % i, i + 1, i % 3 == 0) for i in range(12)], 33],
    ])([S("read", 10), S("parse", 20), S("upload", 50, True)]),
    examples=2,
    wrong_solutions=[
        # every step is interrupted immediately
        "function runCancelable(steps, cancelAt) {\n  const completed = []; let now = 0;\n  for (const s of steps) {\n    if (cancelAt !== null && now >= cancelAt) return { completed, status: 'cancelled', endedAt: now };\n    if (cancelAt !== null && cancelAt < now + s.ms) return { completed, status: 'cancelled', endedAt: cancelAt };\n    now += s.ms; completed.push(s.name);\n  }\n  return { completed, status: 'done', endedAt: now };\n}\n",
        # ignores abortable steps
        "function runCancelable(steps, cancelAt) {\n  const completed = []; let now = 0;\n  for (const s of steps) {\n    if (cancelAt !== null && now >= cancelAt) return { completed, status: 'cancelled', endedAt: now };\n    now += s.ms; completed.push(s.name);\n  }\n  return { completed, status: 'done', endedAt: now };\n}\n",
        # checks after the last step too
        "function runCancelable(steps, cancelAt) {\n  const completed = []; let now = 0;\n  for (const s of steps) {\n    if (cancelAt !== null && now >= cancelAt) return { completed, status: 'cancelled', endedAt: now };\n    const end = now + s.ms;\n    if (s.abortable && cancelAt !== null && cancelAt < end) return { completed, status: 'cancelled', endedAt: cancelAt };\n    now = end; completed.push(s.name);\n  }\n  if (cancelAt !== null && now >= cancelAt) return { completed, status: 'cancelled', endedAt: now };\n  return { completed, status: 'done', endedAt: now };\n}\n",
    ],
    guide=G(
        prereqs="Loops, early `return`. The lesson *Cancelling async work and running CPU-bound tasks*.",
        intuition="A cook following a recipe who glances at the \"order cancelled\" light only between steps. Chopping, once begun, is finished; but the oven has its own off switch wired to the light, "
                  "so baking stops the moment the light comes on.",
        hints=["Walk through the steps with a clock `now`.", "At the top of each iteration: if `cancelAt !== null && now >= cancelAt`, return cancelled at `now`.", "For an abortable step compare `cancelAt` with the step's end time: if it is earlier, return cancelled at `cancelAt`."],
        brute_force="Advance the clock 1 ms at a time, checking the signal each millisecond: O(total duration) and easy to get the boundaries wrong.",
        approach="Check, then run.\n\n**Dry run** (`cancelAt = 15`): before `read`, `0 >= 15` is false → run to 10. Before `parse`, `10 >= 15` false → it starts; not abortable → runs to 30. "
                 "Before `upload`, `30 >= 15` → cancelled at 30 with `[read, parse]` completed.",
        complexity="O(number of steps).",
        pitfalls="- Interrupting ordinary steps mid-way: plain promises cannot be stopped from outside.\n- Treating `cancelAt = 0` as \"no cancellation\" because `0` is falsy; compare with `null`.\n- Reporting `cancelled` when the request arrives after everything has finished.",
        follow_up="Add a `cleanup` duration per completed step that runs in reverse order after cancellation (closing files, rolling back), as a `finally` block would.",
    ),
),
dict(
    id="node-lru-cache", title="A bounded LRU cache", difficulty="Medium", pattern="Production",
    kind="js", entry="runLru",
    description=r"""
An in-memory cache without a size limit is one of the most common memory leaks in Node.js services. Implement a cache that holds at most `capacity` (≥ 1) entries and,
when full, evicts the **least recently used** one. Both reading and writing a key count as using it.

`runLru(capacity, ops)` returns one result per operation:

| operation | result |
|---|---|
| `["get", key]` | the value, or `-1` if absent (a hit makes the key the most recently used) |
| `["put", key, value]` | inserts or updates and makes the key the most recently used. Result: the key that had to be evicted, or `null` |
| `["keys"]` | the keys from least to most recently used |

**Example:** `capacity = 2`, ops `[["put","a",1],["put","b",2],["get","a"],["put","c",3],["get","b"],["keys"]]` → `[null, null, 1, "b", -1, ["a","c"]]`
""",
    starter="function runLru(capacity, ops) {\n  // return one result per operation\n}\n",
    solution=LRU_SOLUTION,
    tests=[
        [2, [["put", "a", 1], ["put", "b", 2], ["get", "a"], ["put", "c", 3], ["get", "b"], ["keys"]]],
        [1, [["put", "a", 1], ["put", "b", 2], ["get", "a"], ["get", "b"], ["keys"]]],
        [3, []],
        [2, [["get", "nope"], ["keys"]]],
        [2, [["put", "a", 1], ["put", "a", 2], ["put", "b", 3], ["keys"], ["get", "a"], ["keys"]]],
        [2, [["put", "a", 1], ["put", "b", 2], ["put", "a", 9], ["put", "c", 3], ["keys"], ["get", "a"]]],
        [3, [["put", "x", 0], ["get", "x"], ["put", "y", ""], ["get", "y"], ["put", "z", False], ["get", "z"]]],
        [2, [["put", "a", 1], ["put", "b", 2], ["get", "missing"], ["put", "c", 3], ["keys"]]],
        [3, [["put", "a", 1], ["put", "b", 2], ["put", "c", 3], ["get", "a"], ["get", "b"], ["put", "d", 4], ["put", "e", 5], ["keys"]]],
        [4, [["put", "k%d" % (i % 6), i] for i in range(20)] + [["keys"]] + [["get", "k%d" % i] for i in range(6)] + [["keys"]]],
        [50, [["put", "k%d" % i, i] for i in range(120)] + [["get", "k%d" % i] for i in range(60, 80)] + [["put", "new", 1], ["keys"]]],
    ],
    examples=1,
    wrong_solutions=[
        # FIFO: get does not refresh recency
        r'''function runLru(capacity, ops) {
  const map = new Map();
  return ops.map(([op, key, value]) => {
    if (op === "get") return map.has(key) ? map.get(key) : -1;
    if (op === "put") { let ev = null; if (map.has(key)) map.delete(key); else if (map.size >= capacity) { ev = map.keys().next().value; map.delete(ev); } map.set(key, value); return ev; }
    return [...map.keys()];
  });
}
''',
        # updating an existing key keeps its old position
        r'''function runLru(capacity, ops) {
  const map = new Map();
  return ops.map(([op, key, value]) => {
    if (op === "get") { if (!map.has(key)) return -1; const v = map.get(key); map.delete(key); map.set(key, v); return v; }
    if (op === "put") { let ev = null; if (!map.has(key) && map.size >= capacity) { ev = map.keys().next().value; map.delete(ev); } map.set(key, value); return ev; }
    return [...map.keys()];
  });
}
''',
    ],
    guide=G(
        prereqs="`Map` and the fact that it iterates in insertion order. The lesson *Interview essentials* (memory leaks).",
        intuition="A small desk with room for a few books. Each time you use a book you put it back on the right-hand end. When the desk is full and a new book arrives, "
                  "the book at the far left, untouched the longest, goes back to the shelf.",
        hints=["A JavaScript `Map` remembers insertion order: the first key it yields is the oldest inserted.", "To mark a key as recently used, delete it and set it again.", "On `put` of a new key into a full cache, evict `map.keys().next().value` first."],
        brute_force="An array of `[key, value]` pairs with a linear search and `splice` on every access: O(n) per operation.",
        approach="Map as an ordered dictionary.\n\n**Dry run** on the example: put a, put b → order `a, b`. `get a` → 1, order `b, a`. `put c` → full, evict `b` → order `a, c`. `get b` → -1. `keys` → `[a, c]`.",
        complexity="O(1) average per `get`/`put`; `keys` is O(n). Space O(capacity).",
        pitfalls="- Forgetting that `get` refreshes recency (that gives FIFO, not LRU).\n- Evicting when updating an existing key.\n- `if (map.get(key))` fails for stored values `0`, `\"\"` or `false`; use `has`.",
        follow_up="Add a time-to-live per entry. The classic interview version asks for a doubly linked list plus a hash map; explain why `Map` gives the same complexity.",
    ),
),
dict(
    id="node-round-robin", title="Round-robin load balancer with failing workers", difficulty="Medium", pattern="Scalability",
    kind="js", entry="balance",
    description=r"""
A load balancer spreads requests over `workers` (a fixed list of distinct names, in order) using **round robin**, skipping workers that are currently down.

It keeps a `pointer`, an index into the full list, starting at 0. For a request it examines the workers starting at `pointer` and moving forward (wrapping around),
picks the first one that is up, and sets `pointer` to the position just after the chosen worker. If every worker is down the request cannot be served.

`events` is a list of `["req"]`, `["down", name]` and `["up", name]`. Return one result per event: the chosen worker name for a request (`null` if none is up), and `null` for `down`/`up`.
All workers start up. `down` on a worker that is already down, or `up` on one that is up, changes nothing.

**Example:** workers `["w1","w2","w3"]`, events `req, req, down w3, req, req, up w3, req`
→ `["w1","w2",null,"w1","w2",null,"w3"]`
""",
    starter="function balance(workers, events) {\n  // return one result per event\n}\n",
    solution=RR_SOLUTION,
    tests=(lambda W, q: [
        [W, [q, q, ["down", "w3"], q, q, ["up", "w3"], q]],
        [W, [q] * 7],
        [W, []],
        [[], [q, q]],
        [["solo"], [q, ["down", "solo"], q, ["up", "solo"], q, q]],
        [W, [["down", "w1"], ["down", "w2"], ["down", "w3"], q, ["up", "w2"], q, q]],
        [W, [q, ["down", "w2"], q, q, q, ["up", "w2"], q, q, q]],
        [W, [["down", "w1"], q, q, q, ["up", "w1"], q, q, q, q]],
        [["a", "b", "c", "d"], [q, q, ["down", "c"], ["down", "d"], q, q, q, ["up", "d"], q, q, q]],
        [["a", "b", "c", "d"], [["down", "a"], ["down", "a"], q, ["up", "a"], ["up", "a"], q, q, q, q]],
        [["n%d" % i for i in range(7)], [["down", "n3"]] + [q] * 9 + [["down", "n0"], ["up", "n3"]] + [q] * 9],
    ])(["w1", "w2", "w3"], ["req"]),
    examples=2,
    wrong_solutions=[
        # counter modulo the number of healthy workers
        r'''function balance(workers, events) {
  const down = new Set(); let n = 0;
  return events.map(([type, name]) => {
    if (type === "down") { down.add(name); return null; }
    if (type === "up") { down.delete(name); return null; }
    const alive = workers.filter((w) => !down.has(w));
    if (alive.length === 0) return null;
    return alive[n++ % alive.length];
  });
}
''',
        # advances the pointer by one regardless of who was chosen
        r'''function balance(workers, events) {
  const down = new Set(); let p = 0;
  return events.map(([type, name]) => {
    if (type === "down") { down.add(name); return null; }
    if (type === "up") { down.delete(name); return null; }
    for (let s = 0; s < workers.length; s++) { const i = (p + s) % workers.length; if (!down.has(workers[i])) { p = (p + 1) % workers.length; return workers[i]; } }
    return null;
  });
}
''',
    ],
    guide=G(
        prereqs="Modulo arithmetic, `Set`. The lesson *The scale cube, cluster and zero-downtime restarts*.",
        intuition="Dealing cards around a table. If a player has left their seat you skip them and deal to the next person who is present; the next card continues from there.",
        hints=["Keep a `Set` of down workers and an integer `pointer`.", "For a request, try at most `workers.length` positions: `(pointer + step) % workers.length`.", "After choosing index `i`, set `pointer = (i + 1) % workers.length`."],
        brute_force="Filter the healthy workers and index with a request counter modulo their count. The distribution jumps whenever a worker fails or returns, and some workers get two requests in a row.",
        approach="Pointer over the full list.\n\n**Dry run** on the example: req → w1 (pointer 1). req → w2 (pointer 2). w3 down. req → index 2 is down, wrap to 0 → w1 (pointer 1). req → w2 (pointer 2). w3 up. req → w3 (pointer 0).",
        complexity="O(n) per request in the worst case (all but one down), O(1) typically; O(n) space.",
        pitfalls="- Dividing by zero or looping forever when all workers are down.\n- Advancing the pointer by one rather than to just past the chosen worker.\n- An empty worker list.",
        follow_up="Implement *least connections* (pick the worker with the fewest requests in flight) and compare the fairness when request durations vary.",
    ),
),
dict(
    id="node-consistent-hash", title="Consistent hashing ring", difficulty="Hard", pattern="Scalability",
    kind="js", entry="consistentHash",
    description=r"""
To decide which server stores a key (a cache shard, a sticky session), `hash(key) % numberOfServers` works until a server is added or removed: then almost every key moves.
**Consistent hashing** moves only a small share of the keys.

Use this 32-bit hash (FNV-1a) exactly:

```
h = 2166136261
for each character c of the text:  h = h XOR charCode(c);  h = (h * 16777619) mod 2^32     // in JS: Math.imul(h, 16777619) >>> 0
```

The ring: every node contributes `replicas` points, the hashes of the labels `"<node>#0"`, `"<node>#1"`, … `"<node>#<replicas-1>"`.
A key belongs to the node owning the first point whose hash is `>= hash(key)`; if there is none, wrap around to the point with the smallest hash.
(If two points have the same hash, the one with the alphabetically smaller label comes first.)

`consistentHash(replicas, ops)` processes `["add", node]`, `["remove", node]` and `["get", key]` and returns one result per operation: the owning node for `get`
(`null` if the ring is empty) and `null` for `add`/`remove`. Adding a node twice or removing an unknown node changes nothing.

**Example:** `consistentHash(3, [["add","A"],["add","B"],["get","user:1"],["remove","A"],["get","user:1"]])` → a list of five results where the last is `"B"` (the only node left).
""",
    starter="function consistentHash(replicas, ops) {\n  // return one result per operation\n}\n",
    solution=HASH_SOLUTION,
    tests=[
        [3, [["add", "A"], ["add", "B"], ["get", "user:1"], ["remove", "A"], ["get", "user:1"]]],
        [1, [["get", "k"], ["add", "only"], ["get", "k"], ["get", "another"], ["remove", "only"], ["get", "k"]]],
        [4, []],
        [2, [["add", "A"], ["add", "A"], ["remove", "ghost"], ["get", "x"], ["remove", "A"], ["remove", "A"], ["get", "x"]]],
        [8, [["add", "n1"], ["add", "n2"], ["add", "n3"]] + [["get", "key%d" % i] for i in range(25)]],
        [8, [["add", "n1"], ["add", "n2"], ["add", "n3"], ["add", "n4"]] + [["get", "key%d" % i] for i in range(25)]],
        [8, [["add", "n1"], ["add", "n2"], ["add", "n3"], ["remove", "n2"]] + [["get", "key%d" % i] for i in range(25)]],
        [1, [["add", "a"], ["add", "b"], ["add", "c"], ["add", "d"]] + [["get", c] for c in "abcdefghijklmnopqrstuvwxyz"]],
        [50, [["add", "cache-%d" % i] for i in range(5)] + [["get", "session/%d" % (i * 7919)] for i in range(40)]],
        [5, [["add", "x"], ["get", "x#0"], ["get", "x#4"], ["add", "y"], ["get", "y#2"], ["get", ""], ["get", "é✓"]]],
        [16, [["add", "s1"], ["add", "s2"]] + [["get", "u%d" % i] for i in range(15)] + [["add", "s3"]] + [["get", "u%d" % i] for i in range(15)] + [["remove", "s1"]] + [["get", "u%d" % i] for i in range(15)]],
    ],
    examples=1,
    wrong_solutions=[
        # plain modulo hashing
        r'''function consistentHash(replicas, ops) {
  const hash = (s) => { let h = 2166136261; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; } return h; };
  let nodes = [];
  return ops.map(([op, name]) => {
    if (op === "add") { if (!nodes.includes(name)) { nodes.push(name); nodes.sort(); } return null; }
    if (op === "remove") { nodes = nodes.filter((n) => n !== name); return null; }
    return nodes.length ? nodes[hash(name) % nodes.length] : null;
  });
}
''',
        # no wrap-around: keys past the last point go to the last node
        r'''function consistentHash(replicas, ops) {
  const hash = (s) => { let h = 2166136261; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; } return h; };
  let ring = [];
  return ops.map(([op, name]) => {
    if (op === "add") { if (!ring.some((p) => p.node === name)) { for (let i = 0; i < replicas; i++) ring.push({ hash: hash(name + "#" + i), label: name + "#" + i, node: name }); ring.sort((a, b) => a.hash - b.hash || (a.label < b.label ? -1 : 1)); } return null; }
    if (op === "remove") { ring = ring.filter((p) => p.node !== name); return null; }
    if (!ring.length) return null;
    const h = hash(name); const hit = ring.find((p) => p.hash >= h);
    return (hit || ring[ring.length - 1]).node;
  });
}
''',
    ],
    guide=G(
        prereqs="Sorting, binary search, bitwise operators (`^`, `>>> 0`, `Math.imul`). The lesson *Reverse proxies, service discovery and microservices*.",
        intuition="Seat the servers around a round table at positions given by a hash. A key also gets a position and walks clockwise to the first server it meets. "
                  "If a server leaves, only the keys that were walking to it continue to the next one; everybody else stays put. Several seats per server (replicas) even out the gaps.",
        hints=["Implement the hash exactly; `Math.imul` does 32-bit multiplication and `>>> 0` makes the result unsigned.", "Keep the ring as an array of `{hash, label, node}` sorted by hash; rebuild or re-sort when a node is added.", "For `get`, binary-search the first point with `hash >= h`; if the search runs off the end, use index 0."],
        brute_force="For each `get`, scan every point and keep the smallest hash that is `>= h`: O(points) per lookup. Sorting once and binary searching gives O(log points).",
        approach="Sorted ring plus binary search.\n\n**Dry run** in words (`replicas = 3`, nodes A and B): the ring has six points. `get user:1` hashes the key and finds the next point clockwise; say it belongs to A. "
                 "After `remove A` only B's three points remain, so the same walk now ends at a B point: the answer becomes `B`. Keys that already belonged to B are unaffected.",
        complexity="`add` O(P log P) for P points on the ring; `remove` O(P); `get` O(log P + key length).",
        pitfalls="- Leaving the hash signed (negative numbers sort before positive ones and the ring order changes).\n- Forgetting the wrap-around.\n- Using `hash % nodes`, which is the thing being replaced.\n- Adding a node twice and doubling its points.",
        follow_up="Measure it: with 4 nodes and 1,000 keys, how many keys change owner when a fifth node joins? Compare with modulo hashing (about 80%).",
    ),
),
dict(
    id="node-pubsub-broker", title="A pub/sub broker with topic wildcards", difficulty="Medium", pattern="Messaging",
    kind="js", entry="runBroker",
    description=r"""
Build a small message **broker**. Publishers send a message to a *topic* such as `orders.eu.created` (words separated by dots). Subscribers register *patterns*:

- a word matches itself;
- `*` matches **exactly one** word;
- `#` matches **zero or more** words.

So `orders.*.created` matches `orders.eu.created` but not `orders.created`; `orders.#` matches `orders`, `orders.eu` and `orders.eu.created`; `#` matches everything.

Operations:

| operation | effect |
|---|---|
| `["sub", client, pattern]` | the client subscribes to the pattern (repeating the same subscription changes nothing) |
| `["unsub", client, pattern]` | removes that exact subscription if present |
| `["pub", topic, message]` | delivers `message` to every client with at least one matching pattern. A client receives a message **once**, even if several of its patterns match |

Return `{deliveries, inbox}`: `deliveries` has one entry per `pub`, the alphabetically sorted list of clients that received it; `inbox` maps every client that ever
subscribed to the list of messages it received, in order. Messages published before a client subscribes are not delivered later.

**Example:** `[["sub","ann","orders.*"],["sub","bob","#"],["pub","orders.new","m1"],["pub","users.new","m2"]]`
→ `{deliveries:[["ann","bob"],["bob"]], inbox:{ann:["m1"], bob:["m1","m2"]}}`
""",
    starter="function runBroker(ops) {\n  // return { deliveries, inbox }\n}\n",
    solution=PUBSUB_SOLUTION,
    tests=[
        [[["sub", "ann", "orders.*"], ["sub", "bob", "#"], ["pub", "orders.new", "m1"], ["pub", "users.new", "m2"]]],
        [[["pub", "a.b", "lost"], ["sub", "late", "a.b"], ["pub", "a.b", "found"]]],
        [[]],
        [[["sub", "c", "orders.*.created"], ["pub", "orders.eu.created", 1], ["pub", "orders.created", 2], ["pub", "orders.eu.de.created", 3]]],
        [[["sub", "c", "orders.#"], ["pub", "orders", 1], ["pub", "orders.eu", 2], ["pub", "orders.eu.created", 3], ["pub", "order", 4]]],
        [[["sub", "c", "#.error"], ["pub", "error", 1], ["pub", "db.error", 2], ["pub", "db.pool.error", 3], ["pub", "db.error.fatal", 4]]],
        [[["sub", "c", "a.*"], ["sub", "c", "a.#"], ["sub", "c", "a.b"], ["pub", "a.b", "once"], ["unsub", "c", "a.b"], ["pub", "a.b", "still"], ["unsub", "c", "a.*"], ["unsub", "c", "a.#"], ["pub", "a.b", "gone"]]],
        [[["sub", "z", "x"], ["sub", "a", "x"], ["sub", "m", "x"], ["pub", "x", "p"], ["unsub", "m", "x"], ["unsub", "m", "x"], ["unsub", "ghost", "x"], ["pub", "x", "q"]]],
        [[["sub", "c", "*"], ["pub", "one", 1], ["pub", "one.two", 2], ["sub", "d", "*.*"], ["pub", "one.two", 3], ["pub", "one", 4]]],
        [[["sub", "c", "a.#.z"], ["pub", "a.z", 1], ["pub", "a.b.z", 2], ["pub", "a.b.c.z", 3], ["pub", "a.b.c", 4], ["pub", "z", 5]]],
        [[["sub", "c", "#.#"], ["sub", "d", "*.#.*"], ["pub", "solo", 1], ["pub", "a.b", 2], ["pub", "a.b.c", 3]]],
        [[["sub", "s%d" % i, ["logs.#", "logs.*.error", "*.app.*", "metrics.cpu", "#.error"][i % 5]] for i in range(10)]
          + [["pub", topic, n] for n, topic in enumerate(["logs.app.error", "logs.db.info", "metrics.cpu", "x.app.y", "logs", "a.b.c.error"])]],
    ],
    examples=1,
    wrong_solutions=[
        # treats # like * (exactly one word)
        r'''function runBroker(ops) {
  const subs = new Map(), inbox = {}, deliveries = [];
  const ok = (p, t) => p.length === t.length && p.every((w, i) => w === "*" || w === "#" || w === t[i]);
  for (const [op, a, b] of ops) {
    if (op === "sub") { if (!subs.has(a)) { subs.set(a, new Set()); inbox[a] = []; } subs.get(a).add(b); }
    else if (op === "unsub") { if (subs.has(a)) subs.get(a).delete(b); }
    else { const got = []; for (const [c, ps] of subs) if ([...ps].some((p) => ok(p.split("."), a.split(".")))) { got.push(c); inbox[c].push(b); } deliveries.push(got.sort()); }
  }
  return { deliveries, inbox };
}
''',
        # delivers once per matching pattern
        r'''function runBroker(ops) {
  const subs = new Map(), inbox = {}, deliveries = [];
  const m = (p, t) => { if (!p.length) return !t.length; if (p[0] === "#") { for (let k = 0; k <= t.length; k++) if (m(p.slice(1), t.slice(k))) return true; return false; } if (!t.length) return false; return (p[0] === "*" || p[0] === t[0]) && m(p.slice(1), t.slice(1)); };
  for (const [op, a, b] of ops) {
    if (op === "sub") { if (!subs.has(a)) { subs.set(a, new Set()); inbox[a] = []; } subs.get(a).add(b); }
    else if (op === "unsub") { if (subs.has(a)) subs.get(a).delete(b); }
    else { const got = new Set(); for (const [c, ps] of subs) for (const p of ps) if (m(p.split("."), a.split("."))) { got.add(c); inbox[c].push(b); } deliveries.push([...got].sort()); }
  }
  return { deliveries, inbox };
}
''',
    ],
    guide=G(
        prereqs="`Map`, `Set`, recursion on arrays. The lesson *Messaging fundamentals and publish/subscribe*.",
        intuition="A newspaper kiosk: readers leave standing orders (\"anything about sport\", \"local news only\"), and each new issue goes to everyone whose order fits, without the journalist knowing who they are. "
                  "The interesting part is deciding whether an order fits a topic, word by word.",
        hints=["Split both pattern and topic on `.` and compare the word lists recursively.", "Cases for the first pattern word: an ordinary word or `*` consumes exactly one topic word; `#` may consume 0, 1, 2, … words, so try each possibility.", "Store subscriptions as `Map<client, Set<pattern>>`; on publish use `some` over a client's patterns so the message is pushed once."],
        brute_force="Translate each pattern to a regular expression (`*` → `[^.]+`, `#` → `.*`). It works but the zero-word case of `#` next to dots is fiddly (`a.#` must match `a`).",
        approach="`matches(pattern, topic)`: empty pattern matches only an empty topic; `#` loops over how many words to skip; otherwise compare one word and recurse.\n\n"
                 "**Dry run** `a.#.z` against `a.z`: `a` = `a`; then `#` tries to skip 0 words: remaining pattern `[z]` vs topic `[z]` → match. Against `a.b.c`: `#` skips 0, 1 or 2 words and `z` never lines up → no match.",
        complexity="Matching is O(p·t) with memoisation (exponential worst case without it, harmless for short topics). A publish costs O(total subscriptions).",
        pitfalls="- `#` must be able to match zero words.\n- A client with several matching patterns receiving duplicates.\n- Delivering old messages to new subscribers; plain pub/sub has no memory.",
        follow_up="Real brokers store patterns in a trie so a publish does not test every subscription. Add *durable* subscribers that receive what they missed while offline.",
    ),
),
dict(
    id="node-work-queue", title="A work queue with acknowledgements", difficulty="Hard", pattern="Messaging",
    kind="js", entry="runWorkQueue",
    description=r"""
A **work queue** hands each message to exactly one of several competing workers and keeps it until the worker confirms it is done.

State: a FIFO list of *ready* messages; the set of joined workers; for each worker at most **one** unacknowledged message (prefetch = 1); and a line of idle workers ordered by how long they have been idle.

Operations (after **every** operation run *dispatch*: while there is a ready message and an idle worker, give the oldest ready message to the worker at the head of the idle line and record `[worker, message]` in `deliveries`):

| operation | effect |
|---|---|
| `["send", message]` | append the message to the ready list |
| `["join", worker]` | a new worker joins at the back of the idle line (ignored if already joined) |
| `["ack", worker, message]` | valid only if the worker currently holds exactly that message: the message is finished (append to `acked`) and the worker goes to the back of the idle line. Otherwise ignored |
| `["nack", worker, message]` | valid under the same condition: the worker goes to the back of the idle line and the message returns to the **front** of the ready list |
| `["leave", worker]` | the worker disconnects (ignored if unknown). If it held a message, that message returns to the front of the ready list |

Return `{deliveries, ready, unacked, acked}`: all deliveries in order, the messages still ready, an object mapping each busy worker to the message it holds, and acknowledged messages in order.
Messages are distinct strings.

**Example:** `[["send","m1"],["send","m2"],["join","w1"],["join","w2"],["nack","w1","m1"],["ack","w2","m2"]]`
→ deliveries `[["w1","m1"],["w2","m2"],["w1","m1"]]`, ready `[]`, unacked `{w1:"m1"}`, acked `["m2"]`.
""",
    starter="function runWorkQueue(ops) {\n  // return { deliveries, ready, unacked, acked }\n}\n",
    solution=WORKQ_SOLUTION,
    tests=[
        [[["send", "m1"], ["send", "m2"], ["join", "w1"], ["join", "w2"], ["nack", "w1", "m1"], ["ack", "w2", "m2"]]],
        [[["send", "a"], ["send", "b"], ["send", "c"]]],
        [[]],
        [[["join", "w1"], ["join", "w2"], ["join", "w1"], ["send", "a"], ["send", "b"], ["send", "c"], ["ack", "w1", "a"], ["ack", "w2", "b"], ["ack", "w1", "c"]]],
        [[["join", "w1"], ["send", "a"], ["leave", "w1"], ["join", "w2"], ["ack", "w2", "a"]]],
        [[["join", "w1"], ["send", "a"], ["send", "b"], ["ack", "w1", "b"], ["ack", "w2", "a"], ["nack", "w1", "zzz"], ["ack", "w1", "a"], ["ack", "w1", "a"]]],
        [[["join", "w1"], ["join", "w2"], ["join", "w3"], ["send", "a"], ["ack", "w1", "a"], ["send", "b"], ["send", "c"], ["send", "d"], ["send", "e"]]],
        [[["send", "a"], ["send", "b"], ["join", "w1"], ["nack", "w1", "a"], ["nack", "w1", "a"], ["ack", "w1", "a"], ["ack", "w1", "b"]]],
        [[["join", "w1"], ["join", "w2"], ["send", "a"], ["send", "b"], ["send", "c"], ["leave", "w1"], ["ack", "w2", "b"], ["leave", "ghost"], ["ack", "w2", "a"], ["leave", "w2"]]],
        [[["join", "w1"], ["join", "w2"], ["leave", "w1"], ["send", "a"], ["join", "w1"], ["send", "b"], ["nack", "w2", "a"], ["ack", "w1", "b"]]],
        [[["join", "w%d" % i] for i in range(3)] + [["send", "m%d" % i] for i in range(10)]
         + [["ack", "w0", "m0"], ["nack", "w1", "m1"], ["ack", "w2", "m2"], ["leave", "w0"], ["ack", "w1", "m4"], ["ack", "w2", "m1"], ["join", "w9"], ["ack", "w9", "m3"]]],
    ],
    examples=1,
    wrong_solutions=[
        # a nacked or abandoned message goes to the back of the queue
        r'''function runWorkQueue(ops) {
  const ready = [], idle = [], holding = new Map(), members = new Set(), deliveries = [], acked = [];
  const dispatch = () => { while (ready.length && idle.length) { const w = idle.shift(), m = ready.shift(); holding.set(w, m); deliveries.push([w, m]); } };
  for (const [op, a, b] of ops) {
    if (op === "send") ready.push(a);
    else if (op === "join") { if (!members.has(a)) { members.add(a); idle.push(a); } }
    else if (op === "leave") { if (members.has(a)) { members.delete(a); if (holding.has(a)) { ready.push(holding.get(a)); holding.delete(a); } else idle.splice(idle.indexOf(a), 1); } }
    else if (holding.has(a) && holding.get(a) === b) { holding.delete(a); idle.push(a); if (op === "ack") acked.push(b); else ready.push(b); }
    dispatch();
  }
  const unacked = {}; for (const [w, m] of holding) unacked[w] = m;
  return { deliveries, ready, unacked, acked };
}
''',
        # message is dropped when its worker leaves (no redelivery)
        r'''function runWorkQueue(ops) {
  const ready = [], idle = [], holding = new Map(), members = new Set(), deliveries = [], acked = [];
  const dispatch = () => { while (ready.length && idle.length) { const w = idle.shift(), m = ready.shift(); holding.set(w, m); deliveries.push([w, m]); } };
  for (const [op, a, b] of ops) {
    if (op === "send") ready.push(a);
    else if (op === "join") { if (!members.has(a)) { members.add(a); idle.push(a); } }
    else if (op === "leave") { if (members.has(a)) { members.delete(a); if (holding.has(a)) holding.delete(a); else idle.splice(idle.indexOf(a), 1); } }
    else if (holding.has(a) && holding.get(a) === b) { holding.delete(a); idle.push(a); if (op === "ack") acked.push(b); else ready.unshift(b); }
    dispatch();
  }
  const unacked = {}; for (const [w, m] of holding) unacked[w] = m;
  return { deliveries, ready, unacked, acked };
}
''',
    ],
    guide=G(
        prereqs="Queues, `Map`, `Set`. The lesson *Task queues, competing consumers and request/reply*.",
        intuition="A taxi rank. Passengers (messages) queue on one side, free taxis (workers) on the other; the first passenger takes the first taxi. "
                  "The dispatcher crosses a passenger off the list only when the driver radios \"delivered\" (ack). If the taxi breaks down, the passenger goes back to the front of the line.",
        hints=["Four structures: `ready` (array), `idle` (array of workers), `holding` (`Map` worker → message), `members` (`Set`).", "Write `dispatch()` once and call it after every operation.", "For `ack`/`nack`, first check `holding.get(worker) === message`; then free the worker (push to `idle`) and either record the ack or `unshift` the message."],
        brute_force="Recompute who is idle by scanning all workers each time. It works but loses the \"longest idle first\" order unless you also track timestamps; an explicit idle line is simpler.",
        approach="State machine plus dispatch.\n\n**Dry run** on the example: two sends → ready `[m1, m2]`. `join w1` → dispatch gives `m1` to w1. `join w2` → `m2` to w2. "
                 "`nack w1 m1` → w1 idle, `m1` at the front of ready → dispatch gives `m1` to w1 again. `ack w2 m2` → acked `[m2]`, w2 idle, nothing ready.",
        complexity="O(1) amortised per operation apart from `unshift`/`splice` on arrays (O(n)); fine at this scale, a deque would make them O(1).",
        pitfalls="- Deleting a message at delivery time (that is *at-most-once*: a crash loses work).\n- Accepting an ack from a worker that does not hold the message.\n- Forgetting to remove a leaving idle worker from the idle line, so it gets a message after it has gone.",
        follow_up="Add a delivery counter per message and move it to a *dead-letter* list after three nacks, so a poisonous message cannot loop forever.",
    ),
),
dict(
    id="node-request-reply", title="Request/reply with correlation ids", difficulty="Medium", pattern="Messaging",
    kind="js", entry="correlate",
    description=r"""
Over a one-way channel (a message queue, a socket) replies come back in any order, so each request carries a **correlation id** and the requester keeps a table of pending requests.

`events` is a time-ordered list of:

- `["request", t, id, timeout]`: a request with a unique `id` is sent at time `t`; it expires at `t + timeout`;
- `["reply", t, id, payload]`: a reply carrying that id arrives at time `t`.

Handle each reply as follows:

1. no request with that id was ever sent → count it under `unknown`;
2. the request was already resolved by an earlier reply → count it under `duplicate`;
3. the reply arrives at or after the expiry time (`t >= expires`) → the request has timed out; count the reply under `late`;
4. otherwise the request is resolved with `payload`.

Return `{resolved, timedOut, stats}`: `resolved` maps id → payload; `timedOut` lists the ids of all requests that were never resolved (a request with no reply by the end
counts as timed out), ordered by expiry time and then by id; `stats` is `{late, unknown, duplicate}`.

**Example:** `[["request",0,"r1",50],["request",5,"r2",10],["reply",20,"r2","B"],["reply",30,"r1","A"],["reply",31,"r1","A again"],["reply",40,"r9","?"]]`
→ `{resolved:{r1:"A"}, timedOut:["r2"], stats:{late:1, unknown:1, duplicate:1}}`
""",
    starter="function correlate(events) {\n  // return { resolved, timedOut, stats }\n}\n",
    solution=REPLY_SOLUTION,
    tests=[
        [[["request", 0, "r1", 50], ["request", 5, "r2", 10], ["reply", 20, "r2", "B"], ["reply", 30, "r1", "A"], ["reply", 31, "r1", "A again"], ["reply", 40, "r9", "?"]]],
        [[]],
        [[["request", 0, "a", 10]]],
        [[["reply", 3, "a", 1]]],
        [[["request", 0, "a", 10], ["reply", 9, "a", "just in time"]]],
        [[["request", 0, "a", 10], ["reply", 10, "a", "exactly late"]]],
        [[["request", 0, "a", 10], ["reply", 12, "a", "late"], ["reply", 13, "a", "late again"]]],
        [[["request", 0, "b", 30], ["request", 0, "a", 30], ["request", 1, "c", 5]]],
        [[["request", 0, "x", 100], ["request", 1, "y", 100], ["request", 2, "z", 100], ["reply", 3, "z", 3], ["reply", 4, "x", 1], ["reply", 5, "y", 2]]],
        [[["request", 0, "x", 0], ["reply", 0, "x", "zero timeout"]]],
        [[["request", 0, "p", 5], ["reply", 1, "p", {"ok": True, "rows": [1, 2]}], ["reply", 2, "p", None], ["reply", 2, "q", None]]],
        [[["request", i, "id%02d" % i, 10 + (i * 7) % 13] for i in range(15)] + [["reply", 15 + i, "id%02d" % ((i * 4) % 17), i] for i in range(20)]],
    ],
    examples=1,
    wrong_solutions=[
        # no timeout handling: late replies resolve the request
        r'''function correlate(events) {
  const req = new Map(), resolved = {}, stats = { late: 0, unknown: 0, duplicate: 0 };
  for (const [type, t, id, x] of events) {
    if (type === "request") { req.set(id, { expires: t + x, done: false }); continue; }
    const r = req.get(id);
    if (!r) stats.unknown++; else if (r.done) stats.duplicate++; else { r.done = true; resolved[id] = x; }
  }
  const timedOut = [...req].filter(([, r]) => !r.done).sort((a, b) => a[1].expires - b[1].expires || (a[0] < b[0] ? -1 : 1)).map(([id]) => id);
  return { resolved, timedOut, stats };
}
''',
        # a late reply removes the entry, so the next late reply is "unknown" and timedOut misses it
        r'''function correlate(events) {
  const req = new Map(), resolved = {}, stats = { late: 0, unknown: 0, duplicate: 0 };
  for (const [type, t, id, x] of events) {
    if (type === "request") { req.set(id, { expires: t + x, done: false }); continue; }
    const r = req.get(id);
    if (!r) stats.unknown++; else if (r.done) stats.duplicate++; else if (t >= r.expires) { req.delete(id); stats.late++; } else { r.done = true; resolved[id] = x; }
  }
  const timedOut = [...req].filter(([, r]) => !r.done).sort((a, b) => a[1].expires - b[1].expires || (a[0] < b[0] ? -1 : 1)).map(([id]) => id);
  return { resolved, timedOut, stats };
}
''',
    ],
    guide=G(
        prereqs="`Map`, sorting with two keys. The lesson *Task queues, competing consumers and request/reply*.",
        intuition="A cloakroom. You hand over a coat and get a numbered ticket; coats come back in any order and the number tells which coat is whose. "
                  "A ticket nobody issued, a ticket used twice and a ticket presented after closing time are the three ways it goes wrong.",
        hints=["Store each request in a `Map` under its id with its expiry time and a state.", "For a reply, test the four cases in the order given in the statement.", "At the end, every request whose state is not `resolved` is timed out; sort those by `(expires, id)`."],
        brute_force="For each reply, search the whole event list backwards for the matching request: O(n²). The map makes each reply O(1).",
        approach="One pass, then a filter and sort.\n\n**Dry run** on the example: `r1` expires at 50, `r2` at 15. Reply for `r2` at 20: `20 >= 15` → late. Reply for `r1` at 30 → resolved `A`. "
                 "Second reply for `r1` → duplicate. Reply for `r9` → unknown. Unresolved: `r2`.",
        complexity="O(n log n) because of the final sort; O(n) space.",
        pitfalls="- Resolving a request with a reply that came after its timeout (the caller has already been told it failed).\n- Using `>` instead of `>=` at the deadline.\n- Forgetting requests that never got any reply.",
        follow_up="In real code each pending entry holds the promise's `resolve`/`reject` and a timer that deletes the entry; forgetting the deletion is a memory leak.",
    ),
),
]
