"""Node.js problems, part 3: structural and behavioural design patterns, tested through operation lists."""


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


def mw(name, type="pass"):
    return {"name": name, "type": type}


PROXY_SOLUTION = r'''function runProxy(schema, ops) {
  const target = {};
  const log = [];
  const known = (key) => {
    if (!Object.hasOwn(schema, key)) throw new Error("unknown field " + key);
  };
  const proxy = new Proxy(target, {
    get(obj, key) {
      known(key);
      log.push("get " + key);
      return Object.hasOwn(obj, key) ? obj[key] : null;
    },
    set(obj, key, value) {
      known(key);
      if (typeof value !== schema[key]) throw new Error(key + " must be a " + schema[key]);
      obj[key] = value;
      log.push("set " + key + "=" + JSON.stringify(value));
      return true;
    },
    has(obj, key) {
      log.push("has " + key);
      return Object.hasOwn(obj, key);
    },
    deleteProperty(obj, key) {
      if (!Object.hasOwn(obj, key)) return false;
      delete obj[key];
      log.push("delete " + key);
      return true;
    },
    ownKeys(obj) {
      log.push("keys");
      return Reflect.ownKeys(obj);
    },
  });

  const results = ops.map(([op, key, value]) => {
    try {
      if (op === "set") { proxy[key] = value; return true; }
      if (op === "get") return proxy[key];
      if (op === "has") return key in proxy;
      if (op === "delete") return Reflect.deleteProperty(proxy, key);
      return Object.keys(proxy);
    } catch (error) {
      return "error: " + error.message;
    }
  });
  return { results, log, target };
}
'''

DECORATOR_SOLUTION = r'''function runDecorators(data, decorators, keys) {
  let baseCalls = 0;
  const counts = [];
  let service = {
    get(key) {
      baseCalls++;
      return Object.hasOwn(data, key) ? data[key] : null;
    },
  };
  for (const name of decorators) {
    const inner = service;                       // each decorator wraps what exists so far
    if (name === "cache") {
      const memo = new Map();
      service = { get(key) { if (!memo.has(key)) memo.set(key, inner.get(key)); return memo.get(key); } };
    } else if (name === "upper") {
      service = { get(key) { const v = inner.get(key); return typeof v === "string" ? v.toUpperCase() : v; } };
    } else if (name === "count") {
      const slot = counts.length;
      counts.push(0);
      service = { get(key) { counts[slot]++; return inner.get(key); } };
    } else if (name.startsWith("default:")) {
      const fallback = name.slice("default:".length);
      service = { get(key) { const v = inner.get(key); return v === null ? fallback : v; } };
    }
  }
  return { results: keys.map((key) => service.get(key)), baseCalls, counts };
}
'''

ADAPTER_SOLUTION = r'''function runAdapter(ops) {
  // The adaptee: a string-only key-value store (like localStorage). Do not change its interface.
  const raw = {};
  const store = {
    setItem(key, value) { raw[key] = String(value); },
    getItem(key) { return Object.hasOwn(raw, key) ? raw[key] : null; },
    removeItem(key) { delete raw[key]; },
    keys() { return Object.keys(raw); },
  };

  // The adapter: offers a collection interface, implemented only with the store's methods.
  class CollectionAdapter {
    constructor(storage) { this.storage = storage; }
    add(item) {
      const id = Number(this.storage.getItem("seq") || 0) + 1;
      this.storage.setItem("seq", id);
      this.storage.setItem("item:" + id, JSON.stringify(item));
      return id;
    }
    find(id) {
      const text = this.storage.getItem("item:" + id);
      return text === null ? null : JSON.parse(text);
    }
    remove(id) {
      if (this.storage.getItem("item:" + id) === null) return false;
      this.storage.removeItem("item:" + id);
      return true;
    }
    list() {
      return this.storage.keys()
        .filter((key) => key.startsWith("item:"))
        .map((key) => Number(key.slice(5)))
        .sort((a, b) => a - b)
        .map((id) => ({ id, ...this.find(id) }));
    }
  }

  const collection = new CollectionAdapter(store);
  const results = ops.map(([op, arg]) => collection[op](arg));
  return { results, raw };
}
'''

STRATEGY_SOLUTION = r'''function checkout(items, strategy, param) {
  const lineTotal = (item) => item.price * item.qty;
  const subtotal = items.reduce((sum, item) => sum + lineTotal(item), 0);
  const cut = (amount, percent) => amount - Math.round((amount * percent) / 100);
  const strategies = {
    none: () => subtotal,
    percent: (p) => cut(subtotal, p.percent),
    bulk: (p) => items.reduce((sum, item) => sum + (item.qty >= p.min ? cut(lineTotal(item), p.percent) : lineTotal(item)), 0),
    threshold: (p) => (subtotal >= p.min ? Math.max(0, subtotal - p.amount) : subtotal),
  };
  if (!Object.hasOwn(strategies, strategy)) return { error: "unknown strategy: " + strategy };
  return { subtotal, total: strategies[strategy](param || {}) };
}
'''

STATE_SOLUTION = r'''function circuitBreaker(events, threshold, cooldown) {
  let state = "closed", failures = 0, openedAt = 0;
  const results = [];
  for (const { t, ok } of events) {
    if (state === "open") {
      if (t < openedAt + cooldown) { results.push("rejected"); continue; }
      state = "half-open";                       // cooldown is over: allow one trial request
    }
    if (ok) {
      results.push("ok");
      state = "closed";
      failures = 0;
    } else {
      results.push("fail");
      if (state === "half-open") { state = "open"; openedAt = t; }
      else if (++failures >= threshold) { state = "open"; openedAt = t; }
    }
  }
  return { results, state };
}
'''

ITERATOR_SOLUTION = r'''function runIterator(pages, ops) {
  function* flatten() {
    for (const page of pages) for (const item of page) yield item;
  }
  let iterator = flatten();
  let buffered = null;                           // a result fetched by peek and not yet consumed
  const pull = () => {
    if (buffered !== null) { const result = buffered; buffered = null; return result; }
    return iterator.next();
  };
  return ops.map(([op, n]) => {
    if (op === "next") {
      const result = pull();
      return result.done ? { done: true, value: null } : { done: false, value: result.value };
    }
    if (op === "peek") {
      if (buffered === null) buffered = iterator.next();
      return buffered.done ? null : buffered.value;
    }
    if (op === "skip") {
      let skipped = 0;
      while (skipped < n && !pull().done) skipped++;
      return skipped;
    }
    iterator = flatten();                        // reset
    buffered = null;
    return null;
  });
}
'''

MIDDLEWARE_SOLUTION = r'''function runMiddleware(stack) {
  const log = [];
  function dispatch(i) {
    if (i === stack.length) { log.push("handler"); return; }
    const { name, type } = stack[i];
    let called = false;
    const next = () => {
      if (called) throw new Error("next() called multiple times");
      called = true;
      dispatch(i + 1);
    };
    log.push(name + ":in");
    if (type === "error") throw new Error("boom from " + name);
    if (type === "pass") next();
    else if (type === "twice") { next(); next(); }
    else if (type === "catch") {
      try { next(); } catch (error) { log.push(name + ":caught " + error.message); }
    }
    log.push(name + ":out");                     // "stop" falls through to here without calling next
  }
  let error = null;
  try { dispatch(0); } catch (e) { error = e.message; }
  return { log, error };
}
'''

COMMAND_SOLUTION = r'''function runCommands(ops) {
  const items = [];
  const undoStack = [], redoStack = [], snapshots = [];
  const commands = {
    add: (text) => ({ run() { items.push(text); }, undo() { items.pop(); } }),
    remove: (index) => {
      let removed;
      return { run() { removed = items.splice(index, 1)[0]; }, undo() { items.splice(index, 0, removed); } };
    },
    set: (index, text) => {
      let previous;
      return { run() { previous = items[index]; items[index] = text; }, undo() { items[index] = previous; } };
    },
    clear: () => {
      let previous;
      return { run() { previous = items.splice(0); }, undo() { items.push(...previous); } };
    },
  };
  for (const [op, ...args] of ops) {
    if (op === "undo") {
      const command = undoStack.pop();
      if (command) { command.undo(); redoStack.push(command); }
    } else if (op === "redo") {
      const command = redoStack.pop();
      if (command) { command.run(); undoStack.push(command); }
    } else {
      const needsIndex = op === "remove" || op === "set";
      const valid = !needsIndex || (Number.isInteger(args[0]) && args[0] >= 0 && args[0] < items.length);
      if (valid) {
        const command = commands[op](...args);
        command.run();
        undoStack.push(command);
        redoStack.length = 0;                    // a new action discards the redo history
      }
    }
    snapshots.push(items.slice());
  }
  return snapshots;
}
'''

PROBLEMS = [
dict(
    id="node-proxy", title="A validating, logging proxy", difficulty="Medium", pattern="Structural patterns",
    kind="js", entry="runProxy",
    description=r"""
Wrap a plain object (the *subject*) in a **proxy** that validates writes against a schema and records every successful access.

`schema` maps field names to a type name (`"number"`, `"string"` or `"boolean"`). The subject starts empty.
`runProxy(schema, ops)` performs the operations through the proxy and returns `{results, log, target}` where `target` is the subject at the end.

| operation | behaviour | result | log entry (only on success) |
|---|---|---|---|
| `["set", key, value]` | key not in schema → error; `typeof value` differs from the schema type → error; otherwise store | `true` | `set key=<JSON of value>` |
| `["get", key]` | key not in schema → error; otherwise read | the value, or `null` if not set | `get key` |
| `["has", key]` | is the field currently set? (any key is allowed) | `true`/`false` | `has key` |
| `["delete", key]` | remove the field if it is set | `true` if something was removed, else `false` | `delete key` (only when removed) |
| `["keys"]` | list the fields currently set, in insertion order | array of names | `keys` |

Errors do not stop the run: the result of the failing operation is the string `"error: unknown field <key>"` or `"error: <key> must be a <type>"`, and nothing is logged for it.

**Example:** schema `{age:"number"}`, ops `[["set","age","7"],["set","age",7],["get","age"],["get","name"]]`
→ results `["error: age must be a number", true, 7, "error: unknown field name"]`, log `["set age=7","get age"]`, target `{age:7}`.

Tip: JavaScript's built-in `Proxy` has traps named `get`, `set`, `has`, `deleteProperty` and `ownKeys`.
""",
    starter="function runProxy(schema, ops) {\n  const target = {};\n  // wrap target in a proxy, run the ops through it\n  // return { results, log, target }\n}\n",
    solution=PROXY_SOLUTION,
    tests=[
        [{"age": "number"}, [["set", "age", "7"], ["set", "age", 7], ["get", "age"], ["get", "name"]]],
        [{"name": "string", "admin": "boolean"}, [["get", "name"], ["has", "name"], ["set", "name", "Ada"], ["has", "name"], ["keys"]]],
        [{}, []],
        [{}, [["set", "x", 1], ["get", "x"], ["has", "x"], ["delete", "x"], ["keys"]]],
        [{"n": "number"}, [["set", "n", 1], ["delete", "n"], ["delete", "n"], ["get", "n"], ["keys"]]],
        [{"a": "string", "b": "number", "c": "boolean"}, [["set", "c", True], ["set", "a", "x"], ["set", "b", 2], ["keys"], ["delete", "a"], ["set", "a", "y"], ["keys"]]],
        [{"flag": "boolean"}, [["set", "flag", 0], ["set", "flag", "true"], ["set", "flag", False], ["get", "flag"]]],
        [{"s": "string"}, [["set", "s", ""], ["get", "s"], ["set", "s", None], ["get", "s"]]],
        [{"n": "number"}, [["set", "n", 0], ["has", "n"], ["get", "n"], ["set", "n", -1.5], ["get", "n"]]],
        [{"toString": "string"}, [["get", "toString"], ["has", "toString"], ["set", "toString", "mine"], ["get", "toString"], ["get", "valueOf"]]],
        [{"k%d" % i: ["number", "string", "boolean"][i % 3] for i in range(9)},
         [["set", "k%d" % (i % 9), [i, str(i), i % 2 == 0][i % 3]] for i in range(18)] + [["keys"], ["delete", "k4"], ["has", "k4"], ["get", "k4"]]],
    ],
    examples=2,
    wrong_solutions=[
        # logs failed operations too and skips the type check for falsy values
        r'''function runProxy(schema, ops) {
  const target = {}, log = [];
  const results = ops.map(([op, key, value]) => {
    if (op === "set") { log.push("set " + key + "=" + JSON.stringify(value)); if (!Object.hasOwn(schema, key)) return "error: unknown field " + key; if (typeof value !== schema[key]) return "error: " + key + " must be a " + schema[key]; target[key] = value; return true; }
    if (op === "get") { log.push("get " + key); if (!Object.hasOwn(schema, key)) return "error: unknown field " + key; return Object.hasOwn(target, key) ? target[key] : null; }
    if (op === "has") { log.push("has " + key); return Object.hasOwn(target, key); }
    if (op === "delete") { const had = Object.hasOwn(target, key); delete target[key]; if (had) log.push("delete " + key); return had; }
    log.push("keys"); return Object.keys(target);
  });
  return { results, log, target };
}
''',
        # get uses truthiness, so 0, "" and false read back as null
        r'''function runProxy(schema, ops) {
  const target = {}, log = [];
  const results = ops.map(([op, key, value]) => {
    if (op === "set") { if (!Object.hasOwn(schema, key)) return "error: unknown field " + key; if (typeof value !== schema[key]) return "error: " + key + " must be a " + schema[key]; target[key] = value; log.push("set " + key + "=" + JSON.stringify(value)); return true; }
    if (op === "get") { if (!Object.hasOwn(schema, key)) return "error: unknown field " + key; log.push("get " + key); return target[key] || null; }
    if (op === "has") { log.push("has " + key); return Object.hasOwn(target, key); }
    if (op === "delete") { const had = Object.hasOwn(target, key); delete target[key]; if (had) log.push("delete " + key); return had; }
    log.push("keys"); return Object.keys(target);
  });
  return { results, log, target };
}
''',
    ],
    guide=G(
        prereqs="Objects, `typeof`, `try`/`catch`. The lesson *The proxy pattern*.",
        intuition="A proxy is a receptionist in front of an office. Visitors talk to the receptionist exactly as they would to the office, but the receptionist checks "
                  "badges (validation) and writes the visitor book (logging) before letting anything through. The office itself knows nothing about it.",
        hints=["Create `new Proxy(target, handler)` and give `handler` the traps `get`, `set`, `has`, `deleteProperty`, `ownKeys`.", "Throw an `Error` inside a trap for invalid access; catch it where you run each operation and turn it into the `\"error: …\"` string.", "Log only after the checks have passed. Use `Object.hasOwn` rather than truthiness so `0`, `\"\"` and `false` are real values."],
        brute_force="Skip `Proxy` and write an `if` chain per operation. It passes the tests, but callers would then need a special API instead of ordinary property syntax, which is the thing the proxy pattern avoids.",
        approach="Traps do validation and logging; a small dispatcher maps each op to ordinary syntax on the proxy (`proxy[key] = value`, `proxy[key]`, `key in proxy`, `Reflect.deleteProperty`, `Object.keys`).\n\n"
                 "**Dry run** on the example: `set age \"7\"` → trap sees `typeof \"7\"` is `string`, schema wants `number` → throws → result is the error string, no log. "
                 "`set age 7` passes → stored, logged `set age=7`. `get age` → logged, returns 7. `get name` → not in schema → error.",
        complexity="O(1) per operation except `keys`, which is O(number of fields).",
        pitfalls="- Logging before validating.\n- `target[key] || null` loses falsy values.\n- A schema field called `toString`: check own properties, not inherited ones.\n- In strict mode a `set` trap that returns `false` makes the assignment throw a `TypeError`; return `true` after storing.",
        follow_up="Make the proxy *reactive*: call a callback with `(key, oldValue, newValue)` on every successful change, the mechanism behind several UI frameworks.",
    ),
),
dict(
    id="node-decorator", title="Stack decorators around a service", difficulty="Medium", pattern="Structural patterns",
    kind="js", entry="runDecorators",
    description=r"""
A base service has one method, `get(key)`, which returns `data[key]`, or `null` when the key is absent. Every call that reaches the base service is counted in `baseCalls`.

**Decorators** wrap the service and offer the same `get(key)` method. `decorators` lists them from the **innermost** (applied first, closest to the base) to the **outermost**:

| name | what its `get` does |
|---|---|
| `"cache"` | remembers the result per key (including `null`) and does not call the inner service again for that key |
| `"upper"` | calls the inner service; upper-cases the result if it is a string |
| `"count"` | counts its own invocations, then calls the inner service |
| `"default:TEXT"` | calls the inner service; replaces a `null` result by `TEXT` |

Call the outermost `get` once for each entry of `keys`. Return `{results, baseCalls, counts}` where `counts` holds one number per `"count"` decorator, in the order they appear in `decorators`.

**Example:** `data = {a:"x"}`, `decorators = ["count","cache","count"]`, `keys = ["a","a","b","a"]`
→ `{results:["x","x",null,"x"], baseCalls:2, counts:[2,4]}` (the inner counter sits behind the cache and sees only the misses).
""",
    starter="function runDecorators(data, decorators, keys) {\n  // return { results, baseCalls, counts }\n}\n",
    solution=DECORATOR_SOLUTION,
    tests=[
        [{"a": "x"}, ["count", "cache", "count"], ["a", "a", "b", "a"]],
        [{"a": "x"}, [], ["a", "zzz"]],
        [{}, ["cache"], []],
        [{"k": "v"}, ["default:n/a", "upper"], ["k", "missing"]],
        [{"k": "v"}, ["upper", "default:n/a"], ["k", "missing"]],
        [{"n": 5, "s": "five", "b": True}, ["upper"], ["n", "s", "b"]],
        [{"a": "1"}, ["cache", "cache", "count"], ["a", "a", "a"]],
        [{"a": "1"}, ["count", "count", "cache", "count", "cache"], ["a", "b", "a", "b", "c"]],
        [{"x": "hello"}, ["default:none", "cache", "upper", "count"], ["x", "y", "y", "x"]],
        [{"x": "hello"}, ["cache", "default:first"], ["nope", "nope"]],
        [{"toString": "own"}, ["count"], ["toString", "valueOf"]],
        [{("k%d" % i): "v%d" % i for i in range(5)}, ["count", "cache", "upper", "count", "default:?"], ["k%d" % (i * 3 % 8) for i in range(24)]],
    ],
    examples=2,
    wrong_solutions=[
        # wraps in the opposite order (first name becomes the outermost)
        r'''function runDecorators(data, decorators, keys) {
  let baseCalls = 0; const counts = decorators.filter((d) => d === "count").map(() => 0);
  let service = { get(k) { baseCalls++; return Object.hasOwn(data, k) ? data[k] : null; } };
  let slot = counts.length;
  for (const name of decorators.slice().reverse()) {
    const inner = service;
    if (name === "cache") { const m = new Map(); service = { get(k) { if (!m.has(k)) m.set(k, inner.get(k)); return m.get(k); } }; }
    else if (name === "upper") service = { get(k) { const v = inner.get(k); return typeof v === "string" ? v.toUpperCase() : v; } };
    else if (name === "count") { const s = --slot; service = { get(k) { counts[s]++; return inner.get(k); } }; }
    else { const f = name.slice(8); service = { get(k) { const v = inner.get(k); return v === null ? f : v; } }; }
  }
  return { results: keys.map((k) => service.get(k)), baseCalls, counts };
}
''',
        # cache does not remember null results
        r'''function runDecorators(data, decorators, keys) {
  let baseCalls = 0; const counts = [];
  let service = { get(k) { baseCalls++; return Object.hasOwn(data, k) ? data[k] : null; } };
  for (const name of decorators) {
    const inner = service;
    if (name === "cache") { const m = {}; service = { get(k) { if (m[k] == null) m[k] = inner.get(k); return m[k]; } }; }
    else if (name === "upper") service = { get(k) { const v = inner.get(k); return typeof v === "string" ? v.toUpperCase() : v; } };
    else if (name === "count") { const s = counts.length; counts.push(0); service = { get(k) { counts[s]++; return inner.get(k); } }; }
    else { const f = name.slice(8); service = { get(k) { const v = inner.get(k); return v === null ? f : v; } }; }
  }
  return { results: keys.map((k) => service.get(k)), baseCalls, counts };
}
''',
    ],
    guide=G(
        prereqs="Closures, objects with methods, `Map`. The lesson *Decorator and adapter*.",
        intuition="Decorators are layers of clothing on the same person: each layer adds one thing and passes everything else through to the layer underneath. "
                  "Because every layer has the same shape as the service, layers can be stacked in any number and any order, and the order changes the outcome.",
        hints=["Start with `let service = base` and, for each decorator name, replace `service` by a new object whose `get` calls the previous `service`.", "Capture the previous service in a `const inner` inside the loop body so each layer keeps its own reference.", "Use `Map.has` for the cache so a cached `null` counts as a hit; give each `count` layer its own slot in `counts`."],
        brute_force="One big function with flags (`useCache`, `useUpper`, …). It cannot express two caches, three counters or a different order without more flags.",
        approach="Fold the decorator list over the base service, then call the result.\n\n**Dry run** on the example (`count₀`, `cache`, `count₁` from inside out): "
                 "`a` → count₁=1, cache miss → count₀=1 → base (1). `a` → count₁=2, hit. `b` → count₁=3, miss → count₀=2 → base (2) → `null`, cached. `a` → count₁=4, hit. "
                 "`baseCalls 2`, `counts [2,4]`.",
        complexity="O(layers) per call; O(distinct keys) memory per cache layer.",
        pitfalls="- Building the stack in the wrong direction.\n- `var`/shared variables so that every layer points at the last service (infinite recursion).\n- Treating `null` as \"not cached\".",
        follow_up="The same idea decorates functions: `withRetry(withTimeout(fetchUser))`. Write `compose(...decorators)`.",
    ),
),
dict(
    id="node-adapter", title="Adapt a string store to a collection API", difficulty="Medium", pattern="Structural patterns",
    kind="js", entry="runAdapter",
    description=r"""
You are given (in the starter) a tiny **string-only key-value store** with four methods: `setItem(key, value)`, `getItem(key)` (returns `null` when absent),
`removeItem(key)` and `keys()`. The rest of the application wants a **collection** interface instead. Write an **adapter** class that offers the collection
methods and implements them using *only* the store's methods.

| collection method | meaning | result |
|---|---|---|
| `add(item)` | store a plain object and give it the next id (1, 2, 3, …; ids are never reused) | the id |
| `find(id)` | fetch the object | the object, or `null` |
| `remove(id)` | delete the object | `true` if it existed, else `false` |
| `list()` | all objects in ascending id order, each with its id merged in: `{id, ...item}` | array |

Storage layout (this is checked): the item with id `n` lives under key `"item:n"` as `JSON.stringify(item)`; the last id handed out lives under key `"seq"` as a decimal string.
The key `"seq"` exists only after the first `add`.

`runAdapter(ops)` runs operations such as `["add", {name:"Ada"}]`, `["find", 1]`, `["remove", 1]`, `["list"]` and returns `{results, raw}` where `raw` is the store's final content.

**Example:** `[["add",{"name":"Ada"}],["add",{"name":"Lin"}],["remove",1],["list"]]`
→ `{results:[1,2,true,[{id:2,name:"Lin"}]], raw:{"seq":"2","item:2":"{\"name\":\"Lin\"}"}}`
""",
    starter='''function runAdapter(ops) {
  // The adaptee: a string-only key-value store. Do not change it.
  const raw = {};
  const store = {
    setItem(key, value) { raw[key] = String(value); },
    getItem(key) { return Object.hasOwn(raw, key) ? raw[key] : null; },
    removeItem(key) { delete raw[key]; },
    keys() { return Object.keys(raw); },
  };

  class CollectionAdapter {
    constructor(storage) { this.storage = storage; }
    // add(item) {}  find(id) {}  remove(id) {}  list() {}
  }

  const collection = new CollectionAdapter(store);
  const results = ops.map(([op, arg]) => collection[op](arg));
  return { results, raw };
}
''',
    solution=ADAPTER_SOLUTION,
    tests=[
        [[["add", {"name": "Ada"}], ["add", {"name": "Lin"}], ["remove", 1], ["list"]]],
        [[["list"], ["find", 1], ["remove", 1]]],
        [[]],
        [[["add", {}], ["find", 1], ["list"]]],
        [[["add", {"a": 1}], ["remove", 1], ["add", {"a": 2}], ["find", 1], ["find", 2], ["list"]]],
        [[["add", {"title": "x", "tags": ["a", "b"], "meta": {"n": None}}], ["find", 1]]],
        [[["add", {"n": i}] for i in range(12)] + [["list"]]],
        [[["add", {"n": i}] for i in range(12)] + [["remove", 3], ["remove", 3], ["remove", 11], ["list"], ["add", {"n": 99}], ["list"]]],
        [[["add", {"v": True}], ["add", {"v": False}], ["find", 2], ["find", 3], ["find", 0], ["remove", 2], ["remove", 2]]],
        [[["add", {"text": "quote \" and unicode é"}], ["list"]]],
        [[["remove", 5], ["add", {"first": 1}], ["list"]]],
    ],
    examples=2,
    wrong_solutions=[
        # keeps objects in its own array: bypasses the adaptee
        r'''function runAdapter(ops) {
  const raw = {}; const items = new Map(); let seq = 0;
  const c = { add(item) { items.set(++seq, item); return seq; }, find(id) { return items.has(id) ? items.get(id) : null; }, remove(id) { return items.delete(id); }, list() { return [...items].map(([id, it]) => ({ id, ...it })); } };
  const results = ops.map(([op, arg]) => c[op](arg));
  return { results, raw };
}
''',
        # reuses ids by counting current items; sorts ids as strings
        r'''function runAdapter(ops) {
  const raw = {};
  const store = { setItem(k, v) { raw[k] = String(v); }, getItem(k) { return Object.hasOwn(raw, k) ? raw[k] : null; }, removeItem(k) { delete raw[k]; }, keys() { return Object.keys(raw); } };
  const ids = () => store.keys().filter((k) => k.startsWith("item:")).map((k) => k.slice(5)).sort();
  const c = {
    add(item) { const id = ids().length + 1; store.setItem("seq", id); store.setItem("item:" + id, JSON.stringify(item)); return id; },
    find(id) { const t = store.getItem("item:" + id); return t === null ? null : JSON.parse(t); },
    remove(id) { if (store.getItem("item:" + id) === null) return false; store.removeItem("item:" + id); return true; },
    list() { return ids().map((id) => ({ id: Number(id), ...c.find(id) })); },
  };
  const results = ops.map(([op, arg]) => c[op](arg));
  return { results, raw };
}
''',
    ],
    guide=G(
        prereqs="Classes, `JSON.stringify`/`JSON.parse`, array sorting. The lesson *Decorator and adapter*.",
        intuition="A travel plug: your laptop's plug does not change and neither does the wall socket; a small piece in between has one shape on each side. "
                  "The adapter speaks \"collection\" to the application and \"string store\" to the storage.",
        hints=["Each collection method is one or two calls on `this.storage`. Decide the key naming first: `\"item:\" + id` and `\"seq\"`.", "`add`: read `seq` (missing means 0), add 1, write it back, write the JSON text.", "`list`: take `keys()`, keep the `item:` ones, turn the suffix into a number, sort numerically, then `find` each."],
        brute_force="Keep the objects in an array inside the adapter. It answers the calls but nothing reaches the store, so the data is lost on restart; that is not adapting, it is replacing.",
        approach="Translate method by method.\n\n**Dry run** on the example: `add Ada` → seq `\"1\"`, `item:1 = {\"name\":\"Ada\"}` → 1. `add Lin` → seq `\"2\"`, `item:2` → 2. "
                 "`remove 1` → key exists → removed → `true`. `list` → keys `seq`, `item:2` → ids `[2]` → `[{id:2, name:\"Lin\"}]`.",
        complexity="`add`/`find`/`remove` O(1) store calls; `list` O(n log n) for n items.",
        pitfalls="- Deriving the next id from the number of items: ids get reused after a removal.\n- Sorting ids as strings puts 10 before 2.\n- Storing objects without `JSON.stringify` (the store would keep `\"[object Object]\"`).",
        follow_up="Write a second adapter with the same collection interface on top of an array-of-rows store; the application code would not change at all.",
    ),
),
dict(
    id="node-strategy", title="Pluggable discount strategies", difficulty="Easy", pattern="Behavioural patterns",
    kind="js", entry="checkout",
    description=r"""
A checkout computes a total from `items` (each `{price, qty}`, price in whole cents) using a **strategy** chosen by name. All amounts are integers.

Let `subtotal` be the sum of `price * qty`. A discount of `p` percent on an amount `x` gives `x - Math.round(x * p / 100)`.

| strategy | `param` | total |
|---|---|---|
| `"none"` | (ignored) | `subtotal` |
| `"percent"` | `{percent}` | the discount applied to the subtotal |
| `"bulk"` | `{min, percent}` | each line with `qty >= min` gets the discount applied to that line; other lines are full price |
| `"threshold"` | `{min, amount}` | if `subtotal >= min`, subtract `amount` (never below 0); otherwise `subtotal` |

Return `{subtotal, total}`, or `{error: "unknown strategy: <name>"}` for any other name.

**Example:** `checkout([{price:1000,qty:3},{price:250,qty:1}], "bulk", {min:3, percent:10})` → `{subtotal:3250, total:2950}`
""",
    starter="function checkout(items, strategy, param) {\n  // return { subtotal, total } or { error }\n}\n",
    solution=STRATEGY_SOLUTION,
    tests=(lambda cart: [
        [cart, "bulk", {"min": 3, "percent": 10}],
        [cart, "none", None],
        [cart, "percent", {"percent": 15}],
        [cart, "threshold", {"min": 3000, "amount": 500}],
        [cart, "threshold", {"min": 5000, "amount": 500}],
        [cart, "threshold", {"min": 0, "amount": 99999}],
        [cart, "loyalty", {"percent": 5}],
        [[], "percent", {"percent": 50}],
        [[{"price": 333, "qty": 1}], "percent", {"percent": 10}],
        [[{"price": 199, "qty": 5}, {"price": 199, "qty": 4}, {"price": 5, "qty": 100}], "bulk", {"min": 5, "percent": 33}],
        [cart, "constructor", {}],
        [[{"price": 1, "qty": 1}], "percent", {"percent": 50}],
        [cart, "bulk", {"min": 1, "percent": 100}],
    ])([{"price": 1000, "qty": 3}, {"price": 250, "qty": 1}]),
    examples=2,
    wrong_solutions=[
        "function checkout(items, strategy, param) {\n  const subtotal = items.reduce((s, i) => s + i.price * i.qty, 0);\n  const cut = (x, p) => x - Math.round(x * p / 100);\n  const table = { none: () => subtotal, percent: (p) => cut(subtotal, p.percent), bulk: (p) => items.some((i) => i.qty >= p.min) ? cut(subtotal, p.percent) : subtotal, threshold: (p) => subtotal >= p.min ? Math.max(0, subtotal - p.amount) : subtotal };\n  if (!Object.hasOwn(table, strategy)) return { error: 'unknown strategy: ' + strategy };\n  return { subtotal, total: table[strategy](param || {}) };\n}\n",
        "function checkout(items, strategy, param) {\n  const subtotal = items.reduce((s, i) => s + i.price * i.qty, 0);\n  const cut = (x, p) => x - Math.round(x * p / 100);\n  const table = { none: () => subtotal, percent: (p) => cut(subtotal, p.percent), bulk: (p) => items.reduce((s, i) => s + (i.qty >= p.min ? cut(i.price * i.qty, p.percent) : i.price * i.qty), 0), threshold: (p) => subtotal > p.min ? subtotal - p.amount : subtotal };\n  if (!table[strategy]) return { error: 'unknown strategy: ' + strategy };\n  return { subtotal, total: table[strategy](param || {}) };\n}\n",
    ],
    guide=G(
        prereqs="`reduce`, objects holding functions. The lesson *Strategy, state and template*.",
        intuition="A sat-nav with a \"fastest / shortest / no motorways\" switch: the trip (context) is the same, the rule for choosing the route is swapped. "
                  "Here the context computes the subtotal and hands the pricing decision to whichever strategy function was selected.",
        hints=["Compute `subtotal` once, outside the strategies.", "Store the strategies in an object keyed by name; each is a function of `param` returning the total.", "Look the name up with `Object.hasOwn` and return the error object if it is not there."],
        brute_force="An `if`/`else if` chain inside `checkout`. It works, but each new discount rule edits the checkout function itself, which is what the pattern is meant to prevent.",
        approach="Table of functions.\n\n**Dry run** on the example: subtotal `3000 + 250 = 3250`. `bulk` with min 3, 10%: line 1 has qty 3 → `3000 - 300 = 2700`; line 2 has qty 1 → `250`. Total `2950`.",
        complexity="O(number of items).",
        pitfalls="- Applying the bulk discount to the whole cart instead of per line.\n- `>` instead of `>=` at the threshold.\n- A threshold discount larger than the subtotal producing a negative total.\n- `table[name]` is truthy for `\"constructor\"`.",
        follow_up="Let strategies be combined: accept a list of strategies and return the best total for the customer.",
    ),
),
dict(
    id="node-state-machine", title="A circuit breaker state machine", difficulty="Medium", pattern="Behavioural patterns",
    kind="js", entry="circuitBreaker",
    description=r"""
A **circuit breaker** protects a failing remote service from being hammered. It is a state machine with three states.

- **closed** (normal): requests go through. A failure adds 1 to a counter of *consecutive* failures; a success resets the counter to 0. When the counter reaches `threshold`, the breaker becomes **open** and remembers the time.
- **open**: requests are rejected immediately, without calling the service, while `t < openedAt + cooldown`. The first request with `t >= openedAt + cooldown` switches the breaker to **half-open** and is let through as a trial.
- **half-open**: the trial request decides. Success → **closed** with the counter at 0. Failure → **open** again, with `openedAt` set to this request's time.

`events` is a time-ordered list of `{t, ok}`: a request arrives at time `t`, and `ok` says whether the service *would* succeed if it is actually called.
Return `{results, state}`: one of `"ok"`, `"fail"`, `"rejected"` per event, and the state after the last event (`"closed"`, `"open"` or `"half-open"`).

**Example:** `threshold = 2`, `cooldown = 10`, events at t = 0 (fail), 1 (fail), 2 (ok), 11 (ok), 12 (ok)
→ `{results:["fail","fail","rejected","ok","ok"], state:"closed"}`
""",
    starter="function circuitBreaker(events, threshold, cooldown) {\n  // return { results, state }\n}\n",
    solution=STATE_SOLUTION,
    tests=(lambda E: [
        [E((0, 0), (1, 0), (2, 1), (11, 1), (12, 1)), 2, 10],
        [E((0, 1), (1, 1), (2, 1)), 2, 10],
        [[], 3, 5],
        [E((0, 0)), 1, 5],
        [E((0, 0), (1, 1), (2, 0), (3, 1), (4, 0)), 2, 10],
        [E((0, 0), (1, 0), (11, 0), (12, 1), (21, 1), (22, 0)), 2, 10],
        [E((0, 0), (1, 0), (5, 1), (10, 1), (11, 0), (12, 1)), 2, 10],
        [E((0, 0), (10, 1)), 1, 10],
        [E((0, 0), (9, 1), (10, 0), (19, 1), (20, 1), (21, 0), (22, 1)), 1, 10],
        [E((0, 0), (1, 0), (2, 0), (50, 1), (51, 0), (52, 0), (53, 0), (54, 1)), 3, 20],
        [E((0, 0), (1, 0), (100, 0), (101, 0), (150, 0), (300, 1), (301, 0), (302, 0)), 2, 100],
        [E(*[(i * 3, 1 if i % 4 == 3 else 0) for i in range(40)]), 3, 7],
        [E((5, 0), (5, 0), (5, 1), (5, 1)), 2, 0],
    ])(lambda *pairs: [{"t": t, "ok": bool(ok)} for t, ok in pairs]),
    examples=2,
    wrong_solutions=[
        # a failed trial does not reopen immediately: it needs `threshold` new failures
        r'''function circuitBreaker(events, threshold, cooldown) {
  let state = "closed", failures = 0, openedAt = 0; const results = [];
  for (const { t, ok } of events) {
    if (state === "open") { if (t < openedAt + cooldown) { results.push("rejected"); continue; } state = "closed"; failures = 0; }
    if (ok) { results.push("ok"); failures = 0; }
    else { results.push("fail"); if (++failures >= threshold) { state = "open"; openedAt = t; } }
  }
  return { results, state };
}
''',
        # counts total failures instead of consecutive ones
        r'''function circuitBreaker(events, threshold, cooldown) {
  let state = "closed", failures = 0, openedAt = 0; const results = [];
  for (const { t, ok } of events) {
    if (state === "open") { if (t < openedAt + cooldown) { results.push("rejected"); continue; } state = "half-open"; }
    if (ok) { results.push("ok"); if (state === "half-open") failures = 0; state = "closed"; }
    else { results.push("fail"); if (state === "half-open") { state = "open"; openedAt = t; } else if (++failures >= threshold) { state = "open"; openedAt = t; } }
  }
  return { results, state };
}
''',
    ],
    guide=G(
        prereqs="Loops and conditionals. The lesson *Strategy, state and template* (state section).",
        intuition="A household fuse. Too many faults in a row and it trips: nothing flows, which protects the wiring. After a while you push it back in carefully (half-open): "
                  "if the fault is gone it stays in; if not, it trips again at once.",
        hints=["Keep three variables: `state`, the consecutive-failure counter and `openedAt`.", "Handle `open` first: either reject and move on, or switch to `half-open` and fall through to the normal request handling.", "On failure, the reaction depends on the state: half-open reopens immediately; closed increments the counter and compares with `threshold`."],
        brute_force="No shortcut exists; you must process events in order. The naive mistake is to treat half-open as closed.",
        approach="Single pass with explicit transitions.\n\n**Dry run** on the example (threshold 2, cooldown 10): t=0 fail → counter 1. t=1 fail → counter 2 → open at 1. "
                 "t=2: `2 < 11` → rejected (the service would have succeeded, but it is never asked). t=11: `11 >= 11` → half-open, trial succeeds → closed. t=12 ok.",
        complexity="O(number of events) time, O(1) state.",
        pitfalls="- Counting failures that are not consecutive.\n- Using `>` instead of `>=` for the cooldown boundary.\n- Updating `openedAt` on rejected requests, which would keep the breaker open forever under steady traffic.",
        follow_up="In the lesson the same machine is written with one object per state, each implementing `request()`. Refactor your solution that way.",
    ),
),
dict(
    id="node-iterator", title="A lazy page-flattening iterator", difficulty="Medium", pattern="Behavioural patterns",
    kind="js", entry="runIterator",
    description=r"""
A paginated API returns `pages`: a list of pages, each a list of items (pages may be empty). Build an **iterator** that walks over all items, page by page,
without first copying them into one big array, and drive it with `ops`. Items are never `null`.

| operation | result |
|---|---|
| `["next"]` | `{done:false, value:item}` and advance; once everything is consumed, `{done:true, value:null}` (every time) |
| `["peek"]` | the item that the following `next` would return, without consuming it; `null` if exhausted |
| `["skip", n]` | consume up to `n` items; the result is how many were actually skipped |
| `["reset"]` | start again from the first item; result `null` |

Return the list of results.

**Example:** `pages = [[1,2],[],[3]]`, ops `[["next"],["peek"],["skip",5],["next"],["reset"],["next"]]`
→ `[{done:false,value:1}, 2, 2, {done:true,value:null}, null, {done:false,value:1}]`
""",
    starter="function runIterator(pages, ops) {\n  // return one result per operation\n}\n",
    solution=ITERATOR_SOLUTION,
    tests=[
        [[[1, 2], [], [3]], [["next"], ["peek"], ["skip", 5], ["next"], ["reset"], ["next"]]],
        [[], [["next"], ["peek"], ["skip", 2], ["next"]]],
        [[[], [], []], [["peek"], ["next"], ["reset"], ["peek"]]],
        [[["a"]], [["peek"], ["peek"], ["next"], ["peek"], ["next"], ["next"]]],
        [[[1, 2, 3], [4, 5]], [["skip", 0], ["next"], ["skip", 2], ["next"], ["skip", 1], ["skip", 1]]],
        [[[1], [2], [3]], [["peek"], ["skip", 1], ["peek"], ["skip", 1], ["peek"], ["skip", 1], ["peek"]]],
        [[[0, False, ""]], [["peek"], ["next"], ["peek"], ["next"], ["peek"], ["next"], ["next"]]],
        [[[1, 2], [3, 4]], [["next"], ["next"], ["next"], ["reset"], ["skip", 3], ["peek"], ["reset"], ["peek"]]],
        [[[], [7], [], [8, 9], []], [["next"], ["next"], ["next"], ["next"], ["next"]]],
        [[[1, 2, 3]], [["peek"], ["reset"], ["next"], ["peek"], ["skip", 10], ["peek"], ["reset"], ["skip", 2], ["next"]]],
        [[list(range(i * 10, i * 10 + i)) for i in range(8)], [["skip", 5], ["next"], ["peek"], ["skip", 20], ["next"], ["skip", 100], ["next"], ["reset"], ["next"]]],
    ],
    examples=1,
    wrong_solutions=[
        # peek consumes the element
        r'''function runIterator(pages, ops) {
  let flat = pages.flat(), i = 0;
  return ops.map(([op, n]) => {
    if (op === "next") return i < flat.length ? { done: false, value: flat[i++] } : { done: true, value: null };
    if (op === "peek") return i < flat.length ? flat[i++] : null;
    if (op === "skip") { const k = Math.min(n, flat.length - i); i += k; return k; }
    i = 0; return null;
  });
}
''',
        # uses truthiness, so falsy items look like the end
        r'''function runIterator(pages, ops) {
  let flat = pages.flat(), i = 0;
  return ops.map(([op, n]) => {
    if (op === "next") return flat[i] ? { done: false, value: flat[i++] } : { done: true, value: null };
    if (op === "peek") return flat[i] ? flat[i] : null;
    if (op === "skip") { const k = Math.min(n, flat.length - i); i += k; return k; }
    i = 0; return null;
  });
}
''',
    ],
    guide=G(
        prereqs="Generators (`function*`, `yield`) or manual index bookkeeping. The lesson *Iterators, generators and async iterators*.",
        intuition="A bookmark in a multi-volume book. `next` reads a line and moves the bookmark; `peek` reads the line and leaves the bookmark; pages without text are skipped over. "
                  "The reader never needs to photocopy the whole book first.",
        hints=["A generator with two nested `for...of` loops yields the items lazily and skips empty pages for free.", "Generators cannot look ahead, so `peek` must fetch one result and park it in a variable that `next` checks first.", "`reset` creates a fresh generator and clears the parked result. Compare with `done`, never with truthiness."],
        brute_force="`pages.flat()` and an index. Correct and short, O(total items) memory; with a real paginated API you could not load all pages up front, which is why the lazy version matters.",
        approach="Generator plus one-slot look-ahead buffer.\n\n**Dry run** on the example: `next` → 1. `peek` → pulls 2 into the buffer, returns 2. `skip 5` → consumes buffered 2, then 3, then hits the end → 2 skipped. "
                 "`next` → done. `reset` → new generator. `next` → 1.",
        complexity="O(1) amortised per consumed item, O(1) extra memory.",
        pitfalls="- `peek` advancing the position.\n- Forgetting the buffered item when skipping or resetting.\n- Treating `0`, `false` or `\"\"` as \"no more items\".",
        follow_up="Make it an *async* iterator where each page is fetched on demand: `for await (const item of iteratePages(fetchPage))`.",
    ),
),
dict(
    id="node-middleware-onion", title="Run a middleware chain (the onion model)", difficulty="Medium", pattern="Behavioural patterns",
    kind="js", entry="runMiddleware",
    description=r"""
Web frameworks such as Koa run a request through a **stack of middleware**. Each middleware receives a `next` function; calling it runs the rest of the stack
(and finally the route handler) and then *returns*, so code after `next()` runs on the way back out. This is the onion model.

`runMiddleware(stack)` receives a list of `{name, type}` and returns `{log, error}`. Every middleware first logs `"<name>:in"`. Then, depending on `type`:

| type | behaviour |
|---|---|
| `"pass"` | calls `next()`, then logs `"<name>:out"` |
| `"stop"` | does **not** call `next()` (think: authentication failed); logs `"<name>:out"` |
| `"error"` | throws `Error("boom from <name>")` |
| `"catch"` | calls `next()` inside `try`/`catch`; if an error arrives logs `"<name>:caught <message>"`; then logs `"<name>:out"` |
| `"twice"` | calls `next()` two times, then logs `"<name>:out"` |

Calling `next()` from the last middleware runs the handler, which logs `"handler"`. A middleware's `next` may be called only once: a second call throws
`Error("next() called multiple times")`. An error that nobody catches unwinds the whole stack (skipped `:out` lines are simply not logged);
`error` is then its message, otherwise `null`.

**Example:** `[{name:"log",type:"pass"},{name:"auth",type:"pass"}]` → `{log:["log:in","auth:in","handler","auth:out","log:out"], error:null}`
""",
    starter="function runMiddleware(stack) {\n  // return { log, error }\n}\n",
    solution=MIDDLEWARE_SOLUTION,
    tests=[
        [[mw("log"), mw("auth")]],
        [[]],
        [[mw("log"), mw("auth", "stop"), mw("body")]],
        [[mw("a"), mw("b", "error"), mw("c")]],
        [[mw("guard", "catch"), mw("a"), mw("b", "error"), mw("c")]],
        [[mw("a"), mw("guard", "catch"), mw("b", "error")]],
        [[mw("t", "twice")]],
        [[mw("guard", "catch"), mw("t", "twice"), mw("z")]],
        [[mw("outer", "catch"), mw("inner", "catch"), mw("bad", "error")]],
        [[mw("only", "stop")]],
        [[mw("e", "error")]],
        [[mw("a"), mw("b", "catch"), mw("c"), mw("d", "stop"), mw("e", "error")]],
        [[mw("c1", "catch"), mw("p1"), mw("c2", "catch"), mw("tw", "twice"), mw("last")]],
        [[mw("m%d" % i) for i in range(30)]],
    ],
    examples=2,
    wrong_solutions=[
        # linear: logs all "in" then all "out" in the same order
        r'''function runMiddleware(stack) {
  const log = []; let error = null;
  try {
    for (const m of stack) { log.push(m.name + ":in"); if (m.type === "error") throw new Error("boom from " + m.name); if (m.type === "stop") { log.push(m.name + ":out"); return { log, error }; } }
    log.push("handler");
    for (const m of stack) log.push(m.name + ":out");
  } catch (e) { error = e.message; }
  return { log, error };
}
''',
        # no guard against calling next twice
        r'''function runMiddleware(stack) {
  const log = [];
  function dispatch(i) {
    if (i === stack.length) { log.push("handler"); return; }
    const { name, type } = stack[i]; const next = () => dispatch(i + 1);
    log.push(name + ":in");
    if (type === "error") throw new Error("boom from " + name);
    if (type === "pass") next(); else if (type === "twice") { next(); next(); }
    else if (type === "catch") { try { next(); } catch (e) { log.push(name + ":caught " + e.message); } }
    log.push(name + ":out");
  }
  let error = null;
  try { dispatch(0); } catch (e) { error = e.message; }
  return { log, error };
}
''',
    ],
    guide=G(
        prereqs="Recursion, closures, `try`/`catch`. The lesson *Middleware and command*.",
        intuition="Russian dolls. Opening doll 1 reveals doll 2, and so on to the centre (the handler); then each doll closes again in reverse order. "
                  "`next()` means \"open the next doll and come back to me when everything inside is finished\".",
        hints=["Write `dispatch(i)`: it runs middleware `i` and gives it a `next` that calls `dispatch(i + 1)`.", "`dispatch(stack.length)` is the handler.", "Give each `next` its own `called` flag (a closure variable) to detect a second call; let errors propagate as normal exceptions and catch them once at the top."],
        brute_force="Two loops: forward for the `in` lines, backward for the `out` lines. It reproduces the happy path only; stop, errors and catching all depend on real nesting.",
        approach="Recursive dispatch.\n\n**Dry run** `[guard:catch, a:pass, b:error, c:pass]`: `guard:in` → next → `a:in` → next → `b:in` → throws. The exception leaves `a` (no `a:out`) and is caught in `guard`: "
                 "`guard:caught boom from b`, then `guard:out`. `error` is `null` because it was handled.",
        complexity="O(n) time and O(n) call-stack depth for n middleware.",
        pitfalls="- Logging `:out` for a middleware an exception passed through.\n- Sharing one `called` flag across all middleware.\n- Forgetting that `stop` still logs its own `:out`.",
        follow_up="Real Koa middleware is `async`: `await next()`. The dispatch function is the same with promises (see `koa-compose`).",
    ),
),
dict(
    id="node-command-undo", title="Commands with undo and redo", difficulty="Medium", pattern="Behavioural patterns",
    kind="js", entry="runCommands",
    description=r"""
A to-do list starts empty. Every change is made through a **command object** that knows how to `run` itself and how to `undo` itself, which gives undo/redo for free.

| operation | effect |
|---|---|
| `["add", text]` | append `text` |
| `["remove", index]` | remove the item at `index` |
| `["set", index, text]` | replace the item at `index` |
| `["clear"]` | remove all items |
| `["undo"]` | reverse the most recent command that has not been undone; nothing happens if there is none |
| `["redo"]` | re-apply the most recently undone command; nothing happens if there is none |

Rules: `remove`/`set` with an index that is not a valid position are ignored completely (they do not enter the history).
Executing a **new** command (add/remove/set/clear) empties the redo history. `clear` on an empty list is still a command.

Return a list with a snapshot (copy) of the items after each operation.

**Example:** `[["add","milk"],["add","tea"],["undo"],["redo"],["remove",0],["undo"]]`
→ `[["milk"],["milk","tea"],["milk"],["milk","tea"],["tea"],["milk","tea"]]`
""",
    starter="function runCommands(ops) {\n  // return a snapshot of the list after each operation\n}\n",
    solution=COMMAND_SOLUTION,
    tests=[
        [[["add", "milk"], ["add", "tea"], ["undo"], ["redo"], ["remove", 0], ["undo"]]],
        [[["undo"], ["redo"], ["add", "a"], ["undo"], ["undo"], ["redo"], ["redo"]]],
        [[]],
        [[["add", "a"], ["add", "b"], ["undo"], ["add", "c"], ["redo"], ["undo"], ["undo"], ["undo"]]],
        [[["add", "a"], ["add", "b"], ["add", "c"], ["clear"], ["undo"], ["redo"], ["undo"], ["remove", 1], ["undo"]]],
        [[["add", "a"], ["set", 0, "A"], ["set", 5, "nope"], ["undo"], ["undo"], ["redo"], ["redo"], ["redo"]]],
        [[["remove", 0], ["add", "x"], ["remove", -1], ["remove", 1], ["undo"]]],
        [[["add", "a"], ["add", "b"], ["add", "c"], ["remove", 1], ["remove", 0], ["undo"], ["undo"], ["redo"]]],
        [[["clear"], ["add", "a"], ["undo"], ["undo"], ["redo"], ["redo"]]],
        [[["add", "a"], ["undo"], ["remove", 0], ["redo"]]],
        [[["add", "a"], ["add", "b"], ["set", 1, "B"], ["clear"], ["undo"], ["undo"], ["set", 0, "A"], ["redo"], ["undo"], ["undo"], ["undo"], ["undo"]]],
        [[["add", "i%d" % i] for i in range(10)] + [["undo"]] * 4 + [["redo"]] * 2 + [["remove", 3], ["redo"], ["undo"], ["undo"]]],
    ],
    examples=2,
    wrong_solutions=[
        # redo history survives a new command
        r'''function runCommands(ops) {
  const items = [], undo = [], redo = [], snaps = [];
  for (const [op, a, b] of ops) {
    if (op === "undo") { if (undo.length) { redo.push(items.slice()); const prev = undo.pop(); items.length = 0; items.push(...prev); } }
    else if (op === "redo") { if (redo.length) { undo.push(items.slice()); const nxt = redo.pop(); items.length = 0; items.push(...nxt); } }
    else {
      const bad = (op === "remove" || op === "set") && !(Number.isInteger(a) && a >= 0 && a < items.length);
      if (!bad) { undo.push(items.slice()); if (op === "add") items.push(a); else if (op === "remove") items.splice(a, 1); else if (op === "set") items[a] = b; else items.length = 0; }
    }
    snaps.push(items.slice());
  }
  return snaps;
}
''',
        # invalid commands are recorded in the history
        r'''function runCommands(ops) {
  const items = [], undo = [], redo = [], snaps = [];
  for (const [op, a, b] of ops) {
    if (op === "undo") { if (undo.length) { redo.push(items.slice()); const prev = undo.pop(); items.length = 0; items.push(...prev); } }
    else if (op === "redo") { if (redo.length) { undo.push(items.slice()); const nxt = redo.pop(); items.length = 0; items.push(...nxt); } }
    else {
      undo.push(items.slice()); redo.length = 0;
      const ok = Number.isInteger(a) && a >= 0 && a < items.length;
      if (op === "add") items.push(a); else if (op === "remove") { if (ok) items.splice(a, 1); } else if (op === "set") { if (ok) items[a] = b; } else items.length = 0;
    }
    snaps.push(items.slice());
  }
  return snaps;
}
''',
    ],
    guide=G(
        prereqs="Stacks (`push`/`pop`), closures, `splice`. The lesson *Middleware and command*.",
        intuition="Instead of doing a change directly, write it on a card that says both how to do it and how to reverse it. Done cards go on one pile; undo moves the top card to a second pile "
                  "(after reversing it); redo moves it back. A fresh action throws the second pile away, because that future no longer exists.",
        hints=["Two stacks: `undoStack` and `redoStack`, holding command objects with `run()` and `undo()`.", "Each command factory captures what it needs to reverse itself (the removed item, the previous text, the cleared items).", "Validate the index *before* creating the command; on a new command set `redoStack.length = 0`."],
        brute_force="Save a full copy of the list before every change and restore copies on undo. Simple and correct, but O(n) memory per step; command objects store only the difference.",
        approach="Command objects plus two stacks.\n\n**Dry run** on the example: `add milk`, `add tea` → undo stack `[addMilk, addTea]`. `undo` → addTea reversed → `[milk]`, redo stack `[addTea]`. "
                 "`redo` → `[milk, tea]`. `remove 0` → remembers `milk`, list `[tea]`, redo cleared. `undo` → `milk` re-inserted at 0.",
        complexity="O(1) per add/set/undo/redo of those; `remove` O(n) for the splice; `clear` O(n). Memory O(history size).",
        pitfalls="- Keeping the redo pile after a new command.\n- Recording commands that did nothing because the index was invalid.\n- Undoing `remove` by appending the item at the end instead of at its old index.",
        follow_up="Serialise commands as plain data (`{type, args}`) and you can send them over the network or replay them later: the basis of job queues and event sourcing.",
    ),
),
]
