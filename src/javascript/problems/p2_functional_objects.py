"""JavaScript problems: higher-order functions, classes, iterators and small data structures."""


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


ARRAY_DRIVER = r'''
// --- driver (provided, do not change) ---
function arrayPipeline(values, steps) {
  const mappers = { double: (x) => x * 2, square: (x) => x * x, addIndex: (x, i) => x + i, lengthOfAll: (x, i, all) => all.length };
  const tests = { even: (x) => x % 2 === 0, odd: (x) => x % 2 !== 0, evenIndex: (x, i) => i % 2 === 0, notLast: (x, i, all) => i < all.length - 1 };
  const reducers = { sum: (a, x) => a + x, max: (a, x) => (x > a ? x : a), weighted: (a, x, i) => a + x * i, join: (a, x) => a + "" + x };
  let current = values;
  for (const [kind, name, initial] of steps) {
    if (kind === "map") current = myMap(current, mappers[name]);
    else if (kind === "filter") current = myFilter(current, tests[name]);
    else return initial === undefined ? myReduce(current, reducers[name]) : myReduce(current, reducers[name], initial);
  }
  return current;
}
'''

ARRAY_SOLUTION = r'''function myMap(array, fn) {
  const out = [];
  for (let i = 0; i < array.length; i++) out.push(fn(array[i], i, array));
  return out;
}
function myFilter(array, test) {
  const out = [];
  for (let i = 0; i < array.length; i++) if (test(array[i], i, array)) out.push(array[i]);
  return out;
}
function myReduce(array, combine, initial) {
  let i = 0, acc = initial;
  if (arguments.length < 3) { acc = array[0]; i = 1; }
  for (; i < array.length; i++) acc = combine(acc, array[i], i, array);
  return acc;
}
'''

PIPE_DRIVER = r'''
// --- driver (provided, do not change) ---
function runPipeline(mode, names, x) {
  const table = { inc: (n) => n + 1, double: (n) => n * 2, square: (n) => n * n, negate: (n) => -n, half: (n) => n / 2 };
  const fns = names.map((name) => table[name]);
  const combined = mode === "compose" ? compose(...fns) : pipe(...fns);
  return combined(x);
}
'''

BANK_DRIVER = r'''
// --- driver (provided, do not change) ---
function runBank(ops) {
  const accounts = {};
  return ops.map(([op, name, a, b]) => {
    try {
      if (op === "open") { accounts[name] = b === "savings" ? new SavingsAccount(name, a) : new Account(name, a); return accounts[name].describe(); }
      const acct = accounts[name];
      if (op === "deposit") return acct.deposit(a);
      if (op === "withdraw") return acct.withdraw(a);
      if (op === "balance") return acct.balance;
      if (op === "interest") return acct.addInterest(a);
      if (op === "isSavings") return acct instanceof SavingsAccount && acct instanceof Account;
      if (op === "describe") return acct.describe();
      return "unknown operation";
    } catch (e) {
      return "error: " + e.message;
    }
  });
}
'''

BANK_SOLUTION = r'''class Account {
  #balance = 0;
  constructor(owner, opening) {
    this.owner = owner;
    this.#balance = opening;
  }
  get balance() { return this.#balance; }
  get floor() { return 0; }
  deposit(amount) {
    if (!(amount > 0)) throw new Error("invalid amount");
    this.#balance += amount;
    return this.#balance;
  }
  withdraw(amount) {
    if (!(amount > 0)) throw new Error("invalid amount");
    if (this.#balance - amount < this.floor) throw new Error("insufficient funds");
    this.#balance -= amount;
    return this.#balance;
  }
  describe() { return `${this.owner}: ${this.balance}`; }
}
class SavingsAccount extends Account {
  get floor() { return 10; }
  addInterest(percent) { return this.deposit(this.balance * percent / 100); }
  describe() { return "[savings] " + super.describe(); }
}
'''

ITER_DRIVER = r'''
// --- driver (provided, do not change) ---
function iterTools(op, args) {
  function* countFrom(n) { while (true) yield n++; }          // infinite!
  if (op === "range") return [...range(...args)];
  if (op === "take") return [...take(args[0], args[1])];
  if (op === "takeInfinite") return [...take(countFrom(args[0]), args[1])];
  if (op === "zip") return [...zip(...args)];
  if (op === "zipInfinite") return [...zip(args[0], countFrom(args[1]))];
  if (op === "lazy") { const it = range(0, 1000000000); return [it.next().value, it.next().value, typeof it[Symbol.iterator]]; }
  return null;
}
'''

EMITTER_DRIVER = r'''
// --- driver (provided, do not change) ---
function runEmitter(ops) {
  const emitter = new Emitter();
  const calls = [];
  const listeners = {};
  const listener = (id) => (listeners[id] ??= (payload) => { calls.push(id + ":" + payload); });
  return ops.map(([op, event, arg]) => {
    if (op === "on") { emitter.on(event, listener(arg)); return emitter.count(event); }
    if (op === "once") { emitter.once(event, listener(arg)); return emitter.count(event); }
    if (op === "off") { emitter.off(event, listener(arg)); return emitter.count(event); }
    calls.length = 0;
    const had = emitter.emit(event, arg);
    return [had, [...calls]];
  });
}
'''

EMITTER_SOLUTION = r'''class Emitter {
  #handlers = new Map();
  on(event, fn) {
    if (!this.#handlers.has(event)) this.#handlers.set(event, []);
    this.#handlers.get(event).push({ fn, once: false });
  }
  once(event, fn) {
    this.on(event, fn);
    this.#handlers.get(event).at(-1).once = true;
  }
  off(event, fn) {
    const list = this.#handlers.get(event) || [];
    const index = list.findIndex((h) => h.fn === fn);
    if (index >= 0) list.splice(index, 1);
  }
  emit(event, payload) {
    const list = this.#handlers.get(event) || [];
    const snapshot = [...list];
    this.#handlers.set(event, list.filter((h) => !h.once));
    for (const h of snapshot) h.fn(payload);
    return snapshot.length > 0;
  }
  count(event) { return (this.#handlers.get(event) || []).length; }
}
'''

PROBLEMS = [
dict(
    id="js-array-methods", title="Implement map, filter and reduce", difficulty="Medium", pattern="Higher-order functions",
    kind="js", entry="arrayPipeline",
    description=r"""
Write your own versions of the three workhorse array methods **without calling the built-in
`map`, `filter`, `reduce` or `forEach`**:

- `myMap(array, fn)` → new array of `fn(element, index, array)`
- `myFilter(array, test)` → new array with the elements for which `test(element, index, array)` is truthy
- `myReduce(array, combine, initial)` → folds from the left with `combine(accumulator, element, index, array)`.
  When `initial` is **not supplied**, the first element is the starting accumulator and folding starts at index 1.

The driver runs a list of steps such as `["map", "double"]`, `["filter", "odd"]`, `["reduce", "sum", 0]`
over an array using fixed callbacks, some of which use the index and the whole-array arguments.

**Examples:** `arrayPipeline([1,2,3,4], [["map","double"], ["reduce","sum",0]])` → `20` · `arrayPipeline([-5,-2,-9], [["reduce","max"]])` → `-2`
""",
    starter="function myMap(array, fn) {\n  // your code\n}\nfunction myFilter(array, test) {\n  // your code\n}\nfunction myReduce(array, combine, initial) {\n  // remember: initial may be missing\n}\n" + ARRAY_DRIVER,
    solution=ARRAY_SOLUTION + ARRAY_DRIVER,
    tests=[
        [[1, 2, 3, 4], [["map", "double"], ["reduce", "sum", 0]]],
        [[-5, -2, -9], [["reduce", "max"]]],
        [[1, 2, 3, 4, 5, 6], [["filter", "odd"]]],
        [[10, 20, 30], [["map", "addIndex"]]],
        [[5, 6, 7, 8, 9], [["filter", "evenIndex"], ["map", "square"]]],
        [[], [["map", "double"]]],
        [[], [["filter", "even"], ["reduce", "sum", 0]]],
        [[4], [["reduce", "sum"]]],
        [[1, 2, 3], [["reduce", "join", ""]]],
        [[1, 2, 3], [["reduce", "join"]]],
        [[3, 3, 3, 3], [["reduce", "weighted", 0]]],
        [[7, 8, 9], [["map", "lengthOfAll"]]],
        [[1, 2, 3, 4], [["filter", "notLast"], ["filter", "notLast"]]],
        [[2, 4, 6], [["map", "square"], ["filter", "even"], ["reduce", "sum", 100]]],
        [[0, 0, 5], [["reduce", "sum", 0]]],
    ],
    wrong_solutions=[
        "function myMap(array, fn) { const out = []; for (const x of array) out.push(fn(x)); return out; }\nfunction myFilter(array, test) { const out = []; for (const x of array) if (test(x)) out.push(x); return out; }\nfunction myReduce(array, combine, initial) { let acc = initial; for (const x of array) acc = combine(acc, x); return acc; }\n" + ARRAY_DRIVER,
        "function myMap(array, fn) { const out = []; for (let i = 0; i < array.length; i++) out.push(fn(array[i], i, array)); return out; }\nfunction myFilter(array, test) { const out = []; for (let i = 0; i < array.length; i++) if (test(array[i], i, array)) out.push(array[i]); return out; }\nfunction myReduce(array, combine, initial) { let acc = initial || 0; for (let i = 0; i < array.length; i++) acc = combine(acc, array[i], i, array); return acc; }\n" + ARRAY_DRIVER,
        "function myMap(array, fn) { const out = []; for (let i = 0; i < array.length; i++) out.push(fn(array[i], i, array)); return out; }\nfunction myFilter(array, test) { const out = []; for (let i = 0; i < array.length; i++) if (test(array[i], i, array)) out.push(array[i]); return out; }\nfunction myReduce(array, combine, initial) { let acc = initial === undefined ? array[0] : initial; for (let i = 0; i < array.length; i++) acc = combine(acc, array[i], i, array); return acc; }\n" + ARRAY_DRIVER,
    ],
    guide=G(
        prereqs="Functions as values and callbacks (lesson *Higher-order functions: map, filter, reduce*).",
        intuition="Each method is one `for` loop with a hole in it. The callback fills the hole: *transform* for map, *decide* for filter, *combine* for reduce.",
        hints=[
            "All three callbacks receive `(element, index, array)`; reduce puts the accumulator in front.",
            "For reduce, find out whether the third argument was passed with `arguments.length < 3`, since a caller may legitimately pass `undefined`, `0` or `\"\"`.",
            "Without an initial value: accumulator = `array[0]`, loop from index 1.",
        ],
        brute_force="Calling the built-ins is the thing you are asked to rebuild; a plain indexed loop is already optimal.",
        approach="**Dry run** `myReduce([-5,-2,-9], max)` with no initial value: `acc = -5`, start at `i = 1`; `-2 > -5` → acc `-2`; `-9 > -2` no. Result `-2`. Starting from `0` instead would give `0`, which is not even in the array.",
        complexity="O(n) calls of the callback for each method; map and filter allocate one new array.",
        pitfalls="- Dropping the index argument breaks callbacks like `addIndex`.\n- `initial || 0` turns the initial value `\"\"` into `0` and invents a `0` when none is given.\n- Starting at index 0 when the first element was already used as the accumulator counts it twice.",
        follow_up="The real `reduce` throws a `TypeError` on an empty array with no initial value. Add that, then implement `flatMap` and `reduceRight`.",
    ),
),
dict(
    id="js-group-by", title="Group objects by a key", difficulty="Easy", pattern="Higher-order functions",
    kind="js", entry="groupBy",
    description=r"""
Write `groupBy(items, key)`. `items` is an array of objects; return an object whose property names are the
distinct values of `item[key]` (converted to strings, as property names always are) and whose values are
arrays of the items having that value, in their original order. Items lacking the key are collected
under the name `"undefined"`.

**Example:** `groupBy([{t:"a",n:1},{t:"b",n:2},{t:"a",n:3}], "t")` → `{a: [{t:"a",n:1},{t:"a",n:3}], b: [{t:"b",n:2}]}`
""",
    starter="function groupBy(items, key) {\n  // your code\n}\n",
    solution="function groupBy(items, key) {\n  const groups = {};\n  for (const item of items) {\n    const name = String(item[key]);\n    if (!Object.hasOwn(groups, name)) groups[name] = [];\n    groups[name].push(item);\n  }\n  return groups;\n}\n",
    tests=[
        [[{"t": "a", "n": 1}, {"t": "b", "n": 2}, {"t": "a", "n": 3}], "t"],
        [[], "t"],
        [[{"t": "a"}], "t"],
        [[{"age": 30, "name": "Ada"}, {"age": 25, "name": "Bo"}, {"age": 30, "name": "Cy"}], "age"],
        [[{"ok": True}, {"ok": False}, {"ok": True}], "ok"],
        [[{"a": 1}, {"b": 2}, {"a": None}], "a"],
        [[{"k": "x"}, {"k": "x"}, {"k": "x"}], "k"],
        [[{"k": "toString", "v": 1}, {"k": "constructor", "v": 2}], "k"],
        [[{"k": 1}, {"k": "1"}], "k"],
        [[{"k": "b"}, {"k": "a"}, {"k": "c"}, {"k": "a"}, {"k": "b"}], "k"],
        [[{"city": "Oslo", "pop": 1}, {"city": "Rome", "pop": 2}], "country"],
    ],
    wrong_solutions=[
        "function groupBy(items, key) {\n  const groups = {};\n  for (const item of items) groups[item[key]] = [item];\n  return groups;\n}\n",
        "function groupBy(items, key) {\n  const groups = {};\n  for (const item of items) {\n    if (!item[key]) continue;\n    (groups[item[key]] ??= []).push(item);\n  }\n  return groups;\n}\n",
        "function groupBy(items, key) {\n  const groups = {};\n  for (const item of items) {\n    const name = String(item[key]);\n    if (!groups[name]) groups[name] = [];\n    groups[name].push(item);\n  }\n  return groups;\n}\n",
    ],
    guide=G(
        prereqs="Objects as dictionaries, `for...of`, own versus inherited properties.",
        intuition="Walk the items once. For each one, compute its bucket name, create the bucket the first time you see it, and push.",
        hints=[
            "Use an ordinary object as the result and bracket notation to reach the bucket.",
            "Create the array only when the bucket does not exist yet.",
            "`if (!groups[name])` is fooled by names such as `toString`, which every object inherits. Test with `Object.hasOwn`.",
        ],
        brute_force="Collect the distinct key values first, then `filter` the list once per value: O(n·g) for g groups.",
        approach="**Dry run** on the example: item 1 → name `a`, new bucket, push. Item 2 → `b`, new bucket, push. Item 3 → `a` exists, push. Result `{a:[#1,#3], b:[#2]}`.",
        complexity="O(n) time, O(n) space.",
        pitfalls="- Assigning `[item]` each time keeps only the last item per group.\n- Skipping falsy key values drops `false`, `0` and missing keys.\n- Inherited names (`constructor`, `toString`): `groups.toString` is already a function, and calling `.push` on it throws.",
        follow_up="Newer runtimes ship `Object.groupBy(items, callback)` and `Map.groupBy`; accept a callback instead of a key name to match them.",
    ),
),
dict(
    id="js-flat", title="Flatten to a depth", difficulty="Medium", pattern="Recursion",
    kind="js", entry="flat",
    description=r"""
Re-create `Array.prototype.flat` **without calling it**. `flat(array, depth)` returns a new array in which
nested arrays have been spliced into their parent, up to `depth` levels deep. `depth` 0 returns a shallow
copy; if `depth` is omitted (the test passes `null`), use 1.

**Examples:** `flat([1,[2,[3,[4]]]], 1)` → `[1,2,[3,[4]]]` · `flat([1,[2,[3,[4]]]], 2)` → `[1,2,3,[4]]` · `flat([[1],[2]], null)` → `[1,2]`
""",
    starter="function flat(array, depth) {\n  // your code\n}\n",
    solution="function flat(array, depth) {\n  if (depth === null || depth === undefined) depth = 1;\n  const out = [];\n  for (const item of array) {\n    if (Array.isArray(item) && depth > 0) out.push(...flat(item, depth - 1));\n    else out.push(item);\n  }\n  return out;\n}\n",
    tests=[
        [[1, [2, [3, [4]]]], 1], [[1, [2, [3, [4]]]], 2], [[[1], [2]], None], [[1, [2, [3, [4]]]], 0],
        [[1, [2, [3, [4]]]], 99], [[], 3], [[[], [[]], [[[]]]], 1], [[[], [[]], [[[]]]], 99], [[1, 2, 3], 5],
        [[[1, 2], 3, [4, [5, 6]]], 1], [["a", ["b", ["c"]], {"k": [1, [2]]}], 99], [[[[[[["deep"]]]]]], 3],
        [[None, [None, [None]]], 2],
    ],
    wrong_solutions=[
        "function flat(array, depth) {\n  const out = [];\n  for (const item of array) {\n    if (Array.isArray(item)) out.push(...flat(item, depth));\n    else out.push(item);\n  }\n  return out;\n}\n",
        "function flat(array, depth) {\n  const out = [];\n  for (const item of array) {\n    if (Array.isArray(item)) out.push(...item);\n    else out.push(item);\n  }\n  return out;\n}\n",
        "function flat(array, depth) {\n  if (!depth) depth = 1;\n  const out = [];\n  for (const item of array) {\n    if (Array.isArray(item) && depth > 0) out.push(...flat(item, depth - 1));\n    else out.push(item);\n  }\n  return out;\n}\n",
    ],
    guide=G(
        prereqs="Recursion, `Array.isArray`, spread into `push`.",
        intuition="Flattening by depth `d` means: copy non-arrays, and replace each inner array by its own flattening with depth `d - 1`. Depth 0 stops the unwrapping.",
        hints=[
            "Carry the remaining depth as a parameter that shrinks by one per level.",
            "Only unwrap when the item is an array **and** depth is still positive.",
            "Treat only `null`/`undefined` as *missing*; `0` is a legitimate depth.",
        ],
        brute_force="Repeat a one-level flatten `depth` times. It works but re-copies the outer elements on every pass: O(n·d).",
        approach="**Dry run** `flat([1,[2,[3,[4]]]], 2)`: `1` copied. `[2,[3,[4]]]` with depth 1 → `2` copied, `[3,[4]]` with depth 0 → returns `[3,[4]]` as elements `3` and `[4]`. Result `[1,2,3,[4]]`.",
        complexity="O(n) for n total elements visited; recursion depth at most `min(depth, nesting)`.",
        pitfalls="- `if (!depth) depth = 1` turns the valid depth 0 into 1.\n- Ignoring depth flattens everything.\n- Objects containing arrays are not arrays; leave them alone.",
        follow_up="Write an iterative version with an explicit stack of `[item, depth]` pairs to survive extremely deep nesting.",
    ),
),
dict(
    id="js-compose-pipe", title="compose and pipe", difficulty="Easy", pattern="Higher-order functions",
    kind="js", entry="runPipeline",
    description=r"""
Write two function combinators:

- `pipe(f, g, h)` returns a function computing `h(g(f(x)))`: data flows **left to right**
- `compose(f, g, h)` returns a function computing `f(g(h(x)))`: the mathematical order, **right to left**

With no functions at all, both return the identity function.

The driver looks function names up in a table (`inc`, `double`, `square`, `negate`, `half`) and applies the
combined function to `x`.

**Examples:** `runPipeline("pipe", ["inc","double"], 3)` → `8` · `runPipeline("compose", ["inc","double"], 3)` → `7`
""",
    starter="function pipe(...fns) {\n  // your code\n}\nfunction compose(...fns) {\n  // your code\n}\n" + PIPE_DRIVER,
    solution="function pipe(...fns) {\n  return (x) => fns.reduce((value, fn) => fn(value), x);\n}\nfunction compose(...fns) {\n  return (x) => fns.reduceRight((value, fn) => fn(value), x);\n}\n" + PIPE_DRIVER,
    tests=[
        ["pipe", ["inc", "double"], 3], ["compose", ["inc", "double"], 3], ["pipe", [], 42], ["compose", [], 42],
        ["pipe", ["square"], 5], ["compose", ["square"], 5], ["pipe", ["inc", "square", "negate"], 2],
        ["compose", ["inc", "square", "negate"], 2], ["pipe", ["double", "double", "double"], 1],
        ["compose", ["half", "inc"], 9], ["pipe", ["half", "inc"], 9], ["pipe", ["negate", "negate"], -7],
        ["compose", ["square", "inc", "double", "negate"], 3],
    ],
    wrong_solutions=[
        "function pipe(...fns) { return (x) => fns.reduce((v, fn) => fn(v), x); }\nfunction compose(...fns) { return (x) => fns.reduce((v, fn) => fn(v), x); }\n" + PIPE_DRIVER,
        "function pipe(...fns) { return (x) => fns.reduceRight((v, fn) => fn(v), x); }\nfunction compose(...fns) { return (x) => fns.reduce((v, fn) => fn(v), x); }\n" + PIPE_DRIVER,
        "function pipe(...fns) { return (x) => fns[fns.length - 1](x); }\nfunction compose(...fns) { return (x) => fns[0](x); }\n" + PIPE_DRIVER,
    ],
    guide=G(
        prereqs="Rest parameters, `reduce` and `reduceRight`, functions returning functions.",
        intuition="A pipeline is a fold: start with `x`, and for each function replace the running value by `fn(value)`. Compose is the same fold from the other end.",
        hints=[
            "Collect the functions with `...fns` and return an arrow function of `x`.",
            "`fns.reduce((value, fn) => fn(value), x)` threads the value through left to right.",
            "With an empty list, `reduce` returns its initial value, which gives you the identity for free.",
        ],
        brute_force="A `for` loop that reassigns `value = fn(value)` is equivalent and equally fast.",
        approach="**Dry run** `pipe(inc, double)(3)`: value 3 → `inc` → 4 → `double` → 8. `compose(inc, double)(3)`: start from the right: `double(3)` = 6 → `inc(6)` = 7.",
        complexity="O(k) calls for k functions.",
        pitfalls="- Mixing up the two directions; tests with non-commuting functions (`inc` and `double`) expose it.\n- Calling `reduce` without the initial value `x` makes the first *function* the accumulator.\n- Forgetting the zero-function case.",
        follow_up="Make `pipe` accept a first function with several parameters: `(...args) => rest.reduce((v, f) => f(v), first(...args))`.",
    ),
),
dict(
    id="js-bank-account", title="Bank accounts with classes", difficulty="Medium", pattern="Classes & inheritance",
    kind="js", entry="runBank",
    description=r"""
Model bank accounts with two classes.

**`Account(owner, opening)`**

- keeps its balance truly private (a `#private` field), exposed read-only through a `balance` getter
- `deposit(amount)` and `withdraw(amount)` return the new balance
- both throw `new Error("invalid amount")` unless `amount > 0`
- `withdraw` throws `new Error("insufficient funds")` if the balance would drop below the account's floor (0)
- `describe()` returns `"owner: balance"`, e.g. `"ada: 100"`

**`SavingsAccount extends Account`**

- its floor is 10: a withdrawal may never leave less than 10
- `addInterest(percent)` deposits `balance * percent / 100` and returns the new balance
- `describe()` returns `"[savings] "` followed by the parent's description (use `super`)

The driver executes operations such as `["open", "ada", 100]`, `["open", "bo", 50, "savings"]`,
`["withdraw", "ada", 30]`, `["interest", "bo", 10]`, `["balance", "ada"]`, `["isSavings", "bo"]`, and turns
thrown errors into strings like `"error: insufficient funds"`.

**Example:** `runBank([["open","ada",100], ["withdraw","ada",30], ["withdraw","ada",500], ["balance","ada"]])` → `["ada: 100", 70, "error: insufficient funds", 70]`
""",
    starter="class Account {\n  // private balance, getter, deposit, withdraw, describe\n}\nclass SavingsAccount extends Account {\n  // floor of 10, addInterest, describe using super\n}\n" + BANK_DRIVER,
    solution=BANK_SOLUTION + BANK_DRIVER,
    tests=[
        [[["open", "ada", 100], ["withdraw", "ada", 30], ["withdraw", "ada", 500], ["balance", "ada"]]],
        [[["open", "bo", 50, "savings"], ["withdraw", "bo", 45], ["withdraw", "bo", 40], ["balance", "bo"]]],
        [[["open", "bo", 200, "savings"], ["interest", "bo", 10], ["describe", "bo"], ["isSavings", "bo"]]],
        [[["open", "ada", 0], ["deposit", "ada", 0], ["deposit", "ada", -5], ["withdraw", "ada", 0], ["balance", "ada"]]],
        [[["open", "ada", 10], ["withdraw", "ada", 10], ["balance", "ada"], ["isSavings", "ada"]]],
        [[["open", "a", 5], ["open", "b", 7], ["deposit", "a", 1], ["deposit", "b", 1], ["balance", "a"], ["balance", "b"]]],
        [[["open", "s", 10, "savings"], ["withdraw", "s", 1], ["deposit", "s", 1], ["withdraw", "s", 1], ["balance", "s"]]],
        [[["open", "ada", 100], ["deposit", "ada", 0.5], ["withdraw", "ada", 100.5], ["describe", "ada"]]],
        [[["open", "s", 100, "savings"], ["interest", "s", 0], ["interest", "s", 50], ["interest", "s", 50], ["balance", "s"]]],
        [[]],
        [[["open", "x", 1, "savings"], ["describe", "x"], ["deposit", "x", 99], ["describe", "x"], ["withdraw", "x", 90], ["withdraw", "x", 1]]],
    ],
    wrong_solutions=[
        BANK_SOLUTION.replace("get floor() { return 10; }", "get floor() { return 0; }") + BANK_DRIVER,
        BANK_SOLUTION.replace('if (this.#balance - amount < this.floor) throw new Error("insufficient funds");', 'if (amount > this.#balance) return this.#balance;') + BANK_DRIVER,
        BANK_SOLUTION.replace('describe() { return "[savings] " + super.describe(); }', '') + BANK_DRIVER,
        BANK_SOLUTION.replace('if (!(amount > 0)) throw new Error("invalid amount");\n    this.#balance += amount;', 'this.#balance += amount;') + BANK_DRIVER,
    ],
    guide=G(
        prereqs="Class syntax, private fields, getters, `extends` and `super`, exceptions (lessons *Prototypes, classes and encapsulation*, *Symbols, iterators, accessors and inheritance*, *Exceptions and error handling*).",
        intuition="Put every rule about money in one place (`Account`), and let the subclass change only what differs: one number (the floor) and one string (the description). The base `withdraw` reads `this.floor`, so it automatically picks up the subclass's value. That is polymorphism.",
        hints=[
            "Declare `#balance` in the class body; only code inside `Account` can touch it. The subclass must go through `balance`, `deposit` and `withdraw`.",
            "Make the floor an overridable getter (`get floor() { return 0; }`) instead of hard-coding `0` inside `withdraw`.",
            "`addInterest` can simply call `this.deposit(...)`; `describe` in the subclass can call `super.describe()`.",
        ],
        brute_force="Copying `withdraw` into the subclass with a different constant works but duplicates the validation; any later fix has to be made twice.",
        approach="**Dry run** `open bo 50 savings; withdraw 45; withdraw 40`: first withdrawal would leave 5 < floor 10 → `error: insufficient funds`. Second leaves exactly 10 → allowed → returns 10.",
        complexity="O(1) per operation.",
        pitfalls="- A subclass cannot read `this.#balance` declared by its parent; private names are per class.\n- Returning silently instead of throwing hides failures from the caller.\n- `addInterest` belongs to savings accounts only; do not define it on the base class.\n- Forgetting to validate `deposit` allows negative deposits, a sneaky withdrawal.",
        follow_up="Add a static `Account.transfer(from, to, amount)` that is atomic: if the deposit fails, the withdrawal is undone.",
    ),
),
dict(
    id="js-iter-tools", title="range, take and zip with generators", difficulty="Medium", pattern="Iterators & generators",
    kind="js", entry="iterTools",
    description=r"""
Write three **lazy** helpers as generator functions (`function*`):

- `range(start, end, step = 1)` yields `start, start + step, ...` while the value is below `end` (for a
  positive step) or above `end` (for a negative step). `end` is exclusive.
- `take(iterable, n)` yields at most the first `n` values of any iterable, and must not pull more values
  than it needs (the driver hands it an infinite generator)
- `zip(...iterables)` yields arrays `[a, b, ...]` made from one value of each input, stopping as soon as
  **any** input is exhausted. With no inputs it yields nothing.

The driver spreads the results into arrays.

**Examples:** `iterTools("range", [0, 10, 3])` → `[0,3,6,9]` · `iterTools("takeInfinite", [5, 3])` → `[5,6,7]` · `iterTools("zip", [[1,2,3], ["a","b"]])` → `[[1,"a"],[2,"b"]]`
""",
    starter="function* range(start, end, step = 1) {\n  // your code\n}\nfunction* take(iterable, n) {\n  // your code\n}\nfunction* zip(...iterables) {\n  // your code\n}\n" + ITER_DRIVER,
    solution="function* range(start, end, step = 1) {\n  if (step > 0) for (let v = start; v < end; v += step) yield v;\n  else if (step < 0) for (let v = start; v > end; v += step) yield v;\n}\nfunction* take(iterable, n) {\n  if (n <= 0) return;\n  let count = 0;\n  for (const value of iterable) {\n    yield value;\n    if (++count >= n) return;\n  }\n}\nfunction* zip(...iterables) {\n  if (iterables.length === 0) return;\n  const iterators = iterables.map((it) => it[Symbol.iterator]());\n  while (true) {\n    const row = [];\n    for (const it of iterators) {\n      const { value, done } = it.next();\n      if (done) return;\n      row.push(value);\n    }\n    yield row;\n  }\n}\n" + ITER_DRIVER,
    tests=[
        ["range", [0, 10, 3]], ["takeInfinite", [5, 3]], ["zip", [[1, 2, 3], ["a", "b"]]], ["range", [0, 5]],
        ["range", [5, 0, -2]], ["range", [3, 3]], ["range", [0, 5, 0]], ["range", [5, 0]], ["take", [[1, 2, 3], 2]],
        ["take", [[1, 2, 3], 10]], ["take", [[1, 2, 3], 0]], ["takeInfinite", [0, 0]], ["zip", [[1, 2], "xyz", [True, False, None]]],
        ["zip", []], ["zip", [[], [1, 2]]], ["zipInfinite", [["a", "b", "c"], 10]], ["lazy", []], ["zip", [[1, 2, 3]]],
    ],
    wrong_solutions=[
        "function* range(start, end, step = 1) {\n  for (let v = start; v < end; v += Math.abs(step) || 1) yield v;\n}\nfunction* take(iterable, n) {\n  let count = 0;\n  for (const value of iterable) { if (count++ >= n) return; yield value; }\n}\nfunction* zip(...iterables) {\n  if (iterables.length === 0) return;\n  const iterators = iterables.map((it) => it[Symbol.iterator]());\n  while (true) {\n    const row = [];\n    for (const it of iterators) { const { value, done } = it.next(); if (done) return; row.push(value); }\n    yield row;\n  }\n}\n" + ITER_DRIVER,
        "function* range(start, end, step = 1) {\n  if (step > 0) for (let v = start; v < end; v += step) yield v;\n  else if (step < 0) for (let v = start; v > end; v += step) yield v;\n}\nfunction* take(iterable, n) {\n  let count = 0;\n  for (const value of iterable) { if (count++ >= n) return; yield value; }\n}\nfunction* zip(...iterables) {\n  const arrays = iterables.map((it) => [...take(it, 50)]);\n  const longest = Math.max(0, ...arrays.map((a) => a.length));\n  for (let i = 0; i < longest; i++) yield arrays.map((a) => (i < a.length ? a[i] : null));\n}\n" + ITER_DRIVER,
        "function* range(start, end, step = 1) {\n  if (step > 0) for (let v = start; v <= end; v += step) yield v;\n  else if (step < 0) for (let v = start; v >= end; v += step) yield v;\n}\nfunction* take(iterable, n) {\n  let count = 0;\n  for (const value of iterable) { if (count++ >= n) return; yield value; }\n}\nfunction* zip(...iterables) {\n  if (iterables.length === 0) return;\n  const iterators = iterables.map((it) => it[Symbol.iterator]());\n  while (true) {\n    const row = [];\n    for (const it of iterators) { const { value, done } = it.next(); if (done) return; row.push(value); }\n    yield row;\n  }\n}\n" + ITER_DRIVER,
    ],
    guide=G(
        prereqs="The iterator protocol (`next()` returning `{value, done}`), `Symbol.iterator`, generator functions and `yield` (lessons *Symbols, iterators, accessors and inheritance*, *Async functions and generators*).",
        intuition="A generator produces values only when asked. `range` is a paused loop; `take` forwards values and stops asking after `n`; `zip` holds one iterator per input and advances them in lockstep.",
        hints=[
            "In `range`, the loop condition depends on the sign of the step; a step of 0 should yield nothing rather than loop for ever.",
            "In `take`, stop *right after* yielding the n-th value so you never request value n+1 from the source.",
            "In `zip`, get real iterators with `iterable[Symbol.iterator]()` and call `.next()` on each; return when any reports `done`.",
        ],
        brute_force="Converting inputs to arrays first (`[...iterable]`) is simple but hangs for ever on an infinite source and wastes memory on large ones.",
        approach="**Dry run** `zip([1,2,3], ['a','b'])`: round 1 → `[1,'a']`; round 2 → `[2,'b']`; round 3: first iterator gives 3, second reports done → return. Output `[[1,'a'],[2,'b']]`.",
        complexity="Each helper does O(1) work per value produced and keeps O(k) state for k inputs.",
        pitfalls="- `v <= end` makes the end inclusive.\n- A negative step with a `<` condition yields nothing or runs away.\n- Padding to the longest input is `zipLongest`, a different function.\n- Strings are iterable: `zip([1,2], 'xyz')` pairs numbers with characters.",
        follow_up="Add `map(iterable, fn)` and `filter(iterable, test)` generators and chain them into a lazy pipeline; newer engines provide these as iterator helper methods.",
    ),
),
dict(
    id="js-lru-cache", title="LRU cache", difficulty="Medium", pattern="Data structure design",
    kind="js", entry="lruCache",
    description=r"""
A least-recently-used cache holds at most `capacity` entries. When a new key arrives and the cache is full,
the entry that has gone longest without being read or written is evicted.

Write `lruCache(capacity, ops)` that processes operations in order and returns a list of results:

- `["put", key, value]` inserts or updates (and marks the key as most recently used) → result `null`
- `["get", key]` returns the value (and marks the key as most recently used), or `-1` if absent

Both operations must run in O(1) average time. Hint: a JavaScript `Map` remembers insertion order.

**Example:** `lruCache(2, [["put","a",1], ["put","b",2], ["get","a"], ["put","c",3], ["get","b"], ["get","a"], ["get","c"]])` → `[null, null, 1, null, -1, 1, 3]`
""",
    starter="function lruCache(capacity, ops) {\n  // your code\n}\n",
    solution="function lruCache(capacity, ops) {\n  const map = new Map();\n  const out = [];\n  for (const [op, key, value] of ops) {\n    if (op === \"get\") {\n      if (!map.has(key)) { out.push(-1); continue; }\n      const v = map.get(key);\n      map.delete(key);\n      map.set(key, v);\n      out.push(v);\n    } else {\n      if (map.has(key)) map.delete(key);\n      else if (map.size >= capacity) map.delete(map.keys().next().value);\n      map.set(key, value);\n      out.push(null);\n    }\n  }\n  return out;\n}\n",
    tests=[
        [2, [["put", "a", 1], ["put", "b", 2], ["get", "a"], ["put", "c", 3], ["get", "b"], ["get", "a"], ["get", "c"]]],
        [1, [["put", "a", 1], ["put", "b", 2], ["get", "a"], ["get", "b"]]],
        [2, [["get", "x"]]],
        [2, [["put", "a", 1], ["put", "a", 2], ["get", "a"]]],
        [2, [["put", "a", 1], ["put", "b", 2], ["put", "a", 10], ["put", "c", 3], ["get", "a"], ["get", "b"], ["get", "c"]]],
        [3, [["put", 1, 1], ["put", 2, 2], ["put", 3, 3], ["get", 1], ["get", 2], ["put", 4, 4], ["get", 3], ["get", 1], ["get", 4]]],
        [2, [["put", "a", 0], ["get", "a"], ["put", "b", 0], ["put", "c", 0], ["get", "a"], ["get", "b"]]],
        [2, []],
        [3, [["put", "a", 1], ["put", "b", 2], ["put", "c", 3], ["put", "d", 4], ["put", "e", 5], ["get", "a"], ["get", "b"], ["get", "c"], ["get", "d"], ["get", "e"]]],
        [2, [["put", "a", 1], ["put", "b", 2], ["get", "a"], ["get", "a"], ["put", "c", 3], ["get", "a"], ["get", "b"]]],
        [50, [["put", i % 70, i] for i in range(300)] + [["get", k] for k in range(70)]],
    ],
    wrong_solutions=[
        "function lruCache(capacity, ops) {\n  const map = new Map(); const out = [];\n  for (const [op, key, value] of ops) {\n    if (op === 'get') out.push(map.has(key) ? map.get(key) : -1);\n    else { if (!map.has(key) && map.size >= capacity) map.delete(map.keys().next().value); map.set(key, value); out.push(null); }\n  }\n  return out;\n}\n",
        "function lruCache(capacity, ops) {\n  const map = new Map(); const out = [];\n  for (const [op, key, value] of ops) {\n    if (op === 'get') { if (!map.has(key)) { out.push(-1); continue; } const v = map.get(key); map.delete(key); map.set(key, v); out.push(v); }\n    else { if (!map.has(key) && map.size >= capacity) map.delete(map.keys().next().value); map.set(key, value); out.push(null); }\n  }\n  return out;\n}\n",
        "function lruCache(capacity, ops) {\n  const map = new Map(); const out = [];\n  for (const [op, key, value] of ops) {\n    if (op === 'get') { const v = map.get(key); if (!v) { out.push(-1); continue; } map.delete(key); map.set(key, v); out.push(v); }\n    else { if (map.has(key)) map.delete(key); else if (map.size >= capacity) map.delete(map.keys().next().value); map.set(key, value); out.push(null); }\n  }\n  return out;\n}\n",
    ],
    guide=G(
        prereqs="`Map` and its guaranteed insertion-order iteration (lesson *Prototypes, classes and encapsulation*).",
        intuition="Keep the keys ordered from least to most recently used. A `Map` iterates in insertion order, so *delete and re-insert* moves a key to the fresh end, and the first key of the iteration is always the eviction victim.",
        hints=[
            "On `get` of an existing key: read it, delete it, set it again.",
            "On `put` of an existing key: delete first, so that setting it again moves it to the end.",
            "The oldest key is `map.keys().next().value`.",
        ],
        brute_force="Store `[key, value, lastUsedTick]` in an array and scan for the smallest tick on eviction: O(n) per operation.",
        approach="**Dry run** capacity 2: put a, put b → order `a,b`. get a → order `b,a`. put c → full, evict first (`b`) → order `a,c`. get b → -1. get a → 1. get c → 3.",
        complexity="O(1) average per operation; O(capacity) space.",
        pitfalls="- Not refreshing on `get` turns the cache into FIFO.\n- `map.set` on an existing key updates the value but **keeps its old position**; you must delete first.\n- Testing `if (!v)` treats a stored `0` as missing.",
        follow_up="Implement it the classic way with a hash map plus doubly linked list, as you would in a language without ordered maps.",
    ),
),
dict(
    id="js-event-emitter", title="A tiny event emitter", difficulty="Medium", pattern="Classes & callbacks",
    kind="js", entry="runEmitter",
    description=r"""
Write a class `Emitter` implementing publish/subscribe:

- `on(event, fn)` registers `fn` for the named event (the same function may be registered several times)
- `once(event, fn)` registers `fn` so that it is called for the next emission only, then removed
- `off(event, fn)` removes the **earliest** registration of `fn` for that event (no effect if absent)
- `emit(event, payload)` calls every registered function with `payload`, in registration order, and returns
  `true` if there was at least one listener, else `false`
- `count(event)` returns the number of current registrations for the event

The driver creates listeners identified by an id; each one records `"id:payload"` when called. For an
`emit` operation the result is `[returnValue, recordedCalls]`; for `on`/`once`/`off` it is the listener count
afterwards.

**Example:** `runEmitter([["on","msg","A"], ["once","msg","B"], ["emit","msg","hi"], ["emit","msg","yo"]])` → `[1, 2, [true, ["A:hi","B:hi"]], [true, ["A:yo"]]]`
""",
    starter="class Emitter {\n  on(event, fn) {}\n  once(event, fn) {}\n  off(event, fn) {}\n  emit(event, payload) {}\n  count(event) {}\n}\n" + EMITTER_DRIVER,
    solution=EMITTER_SOLUTION + EMITTER_DRIVER,
    tests=[
        [[["on", "msg", "A"], ["once", "msg", "B"], ["emit", "msg", "hi"], ["emit", "msg", "yo"]]],
        [[["emit", "nothing", 1]]],
        [[["on", "a", "L1"], ["on", "b", "L2"], ["emit", "a", 1], ["emit", "b", 2], ["emit", "c", 3]]],
        [[["on", "a", "L1"], ["on", "a", "L2"], ["off", "a", "L1"], ["emit", "a", "x"]]],
        [[["on", "a", "L1"], ["on", "a", "L1"], ["emit", "a", "x"], ["off", "a", "L1"], ["emit", "a", "y"]]],
        [[["off", "a", "L1"], ["on", "a", "L1"], ["off", "a", "L9"], ["emit", "a", 0]]],
        [[["once", "a", "L1"], ["emit", "a", 1], ["emit", "a", 2], ["once", "a", "L1"], ["emit", "a", 3]]],
        [[["on", "a", "X"], ["once", "a", "Y"], ["on", "a", "Z"], ["emit", "a", 1], ["emit", "a", 2]]],
        [[["once", "a", "Y"], ["off", "a", "Y"], ["emit", "a", 1]]],
        [[["on", "toString", "T"], ["emit", "toString", "p"], ["emit", "constructor", "q"]]],
        [[]],
        [[["on", "a", "L1"], ["on", "b", "L1"], ["off", "a", "L1"], ["emit", "a", 1], ["emit", "b", 2]]],
    ],
    wrong_solutions=[
        EMITTER_SOLUTION.replace("this.#handlers.set(event, list.filter((h) => !h.once));", "") + EMITTER_DRIVER,
        EMITTER_SOLUTION.replace("const index = list.findIndex((h) => h.fn === fn);\n    if (index >= 0) list.splice(index, 1);", "this.#handlers.set(event, list.filter((h) => h.fn !== fn));") + EMITTER_DRIVER,
        EMITTER_SOLUTION.replace("return snapshot.length > 0;", "return true;") + EMITTER_DRIVER,
        EMITTER_SOLUTION.replace("for (const h of snapshot) h.fn(payload);", "for (const h of [...snapshot].reverse()) h.fn(payload);") + EMITTER_DRIVER,
    ],
    guide=G(
        prereqs="Classes, `Map`, arrays of functions, functions as values compared by identity.",
        intuition="An emitter is a dictionary from event name to an ordered list of callbacks. Everything else is bookkeeping on those lists.",
        hints=[
            "Use a `Map` (not a plain object) so that event names like `toString` cause no trouble.",
            "Store each registration as a small record `{ fn, once }` rather than the bare function.",
            "In `emit`, take a snapshot of the list, remove the one-time entries, then call the snapshot. Listeners that register or remove others during the emission then cannot disturb the loop.",
        ],
        brute_force="One global array of `[event, fn]` pairs scanned on each emit works: O(total listeners) per emit instead of O(listeners of that event).",
        approach="**Dry run** of the example: on A → count 1; once B → count 2; emit hi → snapshot `[A, B]`, list becomes `[A]`, calls record `A:hi`, `B:hi`; emit yo → only `A:yo`.",
        complexity="`on` O(1); `off` and `emit` O(k) for k listeners of that event.",
        pitfalls="- `off` must remove one registration, not all copies of the function.\n- Forgetting to drop `once` listeners after they fire.\n- Returning `true` from `emit` when nobody listened.\n- Mutating the list while iterating over it.",
        follow_up="Make `on` return an unsubscribe function, and add a wildcard event `\"*\"` that receives everything. Node's `EventEmitter` and the browser's `EventTarget` are industrial versions of this class.",
    ),
),
]
