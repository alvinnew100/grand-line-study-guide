"""JavaScript problems: errors, regular expressions, modules, scheduling, parsing and virtual DOM."""


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


def h(tag, props=None, *children):
    return {"tag": tag, "props": props or {}, "children": list(children)}


RECORDS_SOLUTION = r'''class ValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = "ValidationError";
  }
}
function validate(record) {
  if (record === null || typeof record !== "object" || Array.isArray(record)) throw new ValidationError("not an object");
  if (!Number.isInteger(record.id)) throw new ValidationError("bad id");
  if (typeof record.name !== "string" || record.name === "") throw new ValidationError("bad name");
  return { id: record.id, name: record.name };
}
function parseRecords(texts) {
  return texts.map((text) => {
    try {
      return { ok: true, value: validate(JSON.parse(text)) };
    } catch (e) {
      if (e instanceof SyntaxError) return { ok: false, error: "syntax" };
      if (e instanceof ValidationError) return { ok: false, error: e.message };
      throw e;
    }
  });
}
'''

LOOP_SOLUTION = r'''function predictOrder(script) {
  const output = [], micro = [], timers = [];
  let now = 0, seq = 0;
  function run(ops) {
    for (const op of ops) {
      if (op[0] === "log") output.push(op[1]);
      else if (op[0] === "micro") micro.push(op[1]);
      else timers.push({ time: now + op[1], seq: seq++, ops: op[2] });
    }
  }
  function drain() {
    while (micro.length > 0) run(micro.shift());
  }
  run(script);
  drain();
  while (timers.length > 0) {
    let best = 0;
    for (let i = 1; i < timers.length; i++) {
      const a = timers[i], b = timers[best];
      if (a.time < b.time || (a.time === b.time && a.seq < b.seq)) best = i;
    }
    const [next] = timers.splice(best, 1);
    now = next.time;
    run(next.ops);
    drain();
  }
  return output;
}
'''

EVAL_SOLUTION = r'''function evaluate(expr) {
  let pos = 0;
  const skip = () => { while (expr[pos] === " ") pos++; };
  function parseExpression() {
    let value = parseTerm();
    for (;;) {
      skip();
      if (expr[pos] === "+") { pos++; value += parseTerm(); }
      else if (expr[pos] === "-") { pos++; value -= parseTerm(); }
      else return value;
    }
  }
  function parseTerm() {
    let value = parseFactor();
    for (;;) {
      skip();
      if (expr[pos] === "*") { pos++; value *= parseFactor(); }
      else if (expr[pos] === "/") { pos++; value /= parseFactor(); }
      else return value;
    }
  }
  function parseFactor() {
    skip();
    if (expr[pos] === "-") { pos++; return -parseFactor(); }
    if (expr[pos] === "(") { pos++; const inner = parseExpression(); skip(); pos++; return inner; }
    const start = pos;
    while (pos < expr.length && /[0-9.]/.test(expr[pos])) pos++;
    return Number(expr.slice(start, pos));
  }
  return parseExpression();
}
'''

DIFF_SOLUTION = r'''function diff(oldNode, newNode) {
  const patches = [];
  function walk(a, b, path) {
    const aText = typeof a === "string", bText = typeof b === "string";
    if (aText || bText) {
      if (aText && bText) { if (a !== b) patches.push({ type: "TEXT", path, text: b }); }
      else patches.push({ type: "REPLACE", path, node: b });
      return;
    }
    if (a.tag !== b.tag) { patches.push({ type: "REPLACE", path, node: b }); return; }
    const names = [...new Set([...Object.keys(a.props), ...Object.keys(b.props)])].sort();
    for (const name of names) {
      if (!Object.hasOwn(b.props, name)) patches.push({ type: "REMOVE_PROP", path, name });
      else if (!Object.hasOwn(a.props, name) || a.props[name] !== b.props[name]) {
        patches.push({ type: "SET_PROP", path, name, value: b.props[name] });
      }
    }
    const shared = Math.min(a.children.length, b.children.length);
    for (let i = 0; i < shared; i++) walk(a.children[i], b.children[i], [...path, i]);
    for (let i = shared; i < b.children.length; i++) patches.push({ type: "INSERT", path: [...path, i], node: b.children[i] });
    for (let i = a.children.length - 1; i >= shared; i--) patches.push({ type: "REMOVE", path: [...path, i] });
  }
  walk(oldNode, newNode, []);
  return patches;
}
'''

PROBLEMS = [
dict(
    id="js-parse-records", title="Parse records with selective catching", difficulty="Medium", pattern="Exceptions",
    kind="js", entry="parseRecords",
    description=r"""
You receive an array of strings, each supposed to be the JSON text of a record `{"id": <integer>, "name": <non-empty string>}`.
Write `parseRecords(texts)` returning one result per string:

- valid → `{ok: true, value: {id, name}}` (only those two properties, extras are dropped)
- `JSON.parse` fails → `{ok: false, error: "syntax"}`
- parses but is not a plain object (array, `null`, number, ...) → `{ok: false, error: "not an object"}`
- `id` is not an integer → `{ok: false, error: "bad id"}`
- `name` is not a non-empty string → `{ok: false, error: "bad name"}` (checked after `id`)

Structure it the way the exceptions lesson recommends: a `validate` function that **throws** a custom
`ValidationError`, and one `try`/`catch` that recognises exactly the two expected error types and rethrows
anything else.

**Example:** `parseRecords(['{"id":1,"name":"Ada"}', '{oops', '[1,2]'])` → `[{ok:true,value:{id:1,name:"Ada"}}, {ok:false,error:"syntax"}, {ok:false,error:"not an object"}]`
""",
    starter="class ValidationError extends Error {\n  // set this.name\n}\nfunction validate(record) {\n  // throw ValidationError or return { id, name }\n}\nfunction parseRecords(texts) {\n  // try / catch around JSON.parse + validate for each text\n}\n",
    solution=RECORDS_SOLUTION,
    tests=[
        [['{"id":1,"name":"Ada"}', '{oops', '[1,2]']],
        [[]],
        [['{"id":7,"name":"Lin","admin":true}']],
        [['null', '42', '"text"', 'true']],
        [['{"id":"7","name":"Lin"}', '{"id":7.5,"name":"Lin"}', '{"name":"Lin"}']],
        [['{"id":3,"name":""}', '{"id":3}', '{"id":3,"name":5}', '{"id":3,"name":null}']],
        [['{"id":"x","name":""}']],
        [['', ' ', '{', '}', "{'id':1,'name':'a'}", '{"id":1,"name":"a",}']],
        [['{"id":0,"name":"zero"}', '{"id":-4,"name":"neg"}']],
        [['  {"id": 12,\n "name": "spaced"}  ']],
        [['{"id":1,"name":"a"}', '{"id":2,"name":"b"}', 'nope', '{"id":3,"name":"c"}']],
        [['{"id":1e2,"name":"sci"}', '{"id":1,"name":"dup","name":"last"}']],
    ],
    wrong_solutions=[
        RECORDS_SOLUTION.replace('return { id: record.id, name: record.name };', 'return record;'),
        RECORDS_SOLUTION.replace('if (e instanceof SyntaxError) return { ok: false, error: "syntax" };\n      if (e instanceof ValidationError) return { ok: false, error: e.message };\n      throw e;', 'return { ok: false, error: "syntax" };'),
        RECORDS_SOLUTION.replace('if (record === null || typeof record !== "object" || Array.isArray(record)) throw new ValidationError("not an object");', 'if (typeof record !== "object") throw new ValidationError("not an object");'),
        RECORDS_SOLUTION.replace('if (!Number.isInteger(record.id))', 'if (typeof record.id !== "number")'),
    ],
    guide=G(
        prereqs="`try`/`catch`, `throw`, subclasses of `Error`, `instanceof` (lesson *Exceptions and error handling*); `JSON.parse` (lesson *Destructuring, spread, rest and JSON*).",
        intuition="Two different things can go wrong, at two different depths: the text is not JSON (the parser throws `SyntaxError`), or the data has the wrong shape (your code throws `ValidationError`). Let both travel as exceptions to a single handler that tells them apart by class.",
        hints=[
            "In the subclass constructor call `super(message)` and set `this.name`.",
            "`validate` checks in the stated order and throws on the first failure; when it reaches the end it returns a fresh `{ id, name }` object.",
            "In `catch`, use `instanceof` for each known class and finish with `throw e;` so that programming mistakes are not swallowed.",
        ],
        brute_force="Returning error codes from every helper (`return {error: ...}`) and checking them after each call also works, but the checks multiply. Exceptions let the happy path read straight through.",
        approach="For each text: `try { return {ok: true, value: validate(JSON.parse(text))} } catch (e) { classify }`.\n\n**Dry run** `'[1,2]'`: parses fine to an array → `validate` sees an array → throws `ValidationError(\"not an object\")` → handler returns `{ok:false, error:\"not an object\"}`.",
        complexity="O(total length of the input texts).",
        pitfalls="- `typeof null` and `typeof []` are both `\"object\"`.\n- `typeof id === \"number\"` accepts `7.5`; use `Number.isInteger`.\n- A blanket `catch` that reports everything as a syntax error hides the real reason, and would also hide your own typos.\n- Returning the parsed object itself leaks extra properties.",
        follow_up="Collect *all* validation problems of a record into an `AggregateError` instead of stopping at the first.",
    ),
),
dict(
    id="js-hex-color", title="Validate a hex colour", difficulty="Easy", pattern="Regular expressions",
    kind="js", entry="isHexColor",
    description=r"""
CSS accepts hexadecimal colours written as `#` followed by exactly 3, 4, 6 or 8 hex digits
(`0-9`, `a-f`, in either case). Write `isHexColor(text)` returning `true` only when the **whole** string is
such a colour.

**Examples:** `"#fff"` → `true` · `"#12AB9f"` → `true` · `"#12345"` → `false` · `"fff"` → `false` · `" #fff"` → `false`
""",
    starter="function isHexColor(text) {\n  // your code\n}\n",
    solution="function isHexColor(text) {\n  return /^#(?:[0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})$/i.test(text);\n}\n",
    tests=[["#fff"], ["#12AB9f"], ["#12345"], ["fff"], [" #fff"], ["#FFFF"], ["#00000000"], ["#0000000"], ["#ggg"],
           ["#"], [""], ["#fff "], ["#fff\n"], ["##fff"], ["#abcdefabc"], ["x#abc"], ["#12"], ["#A1b2C3d4"]],
    wrong_solutions=[
        "function isHexColor(text) { return /#[0-9a-f]{3,8}/i.test(text); }\n",
        "function isHexColor(text) { return /^#[0-9a-f]{3,8}$/i.test(text); }\n",
        "function isHexColor(text) { return /^#(?:[0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})$/.test(text); }\n",
        "function isHexColor(text) { return /^#[0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8}$/i.test(text); }\n",
    ],
    guide=G(
        prereqs="Character sets, counted repetition `{n,m}`, alternation, anchors and the `i` flag (lesson *Regular expressions: patterns, sets, groups*).",
        intuition="Describe the string from start to end: a hash, then one of three allowed digit counts, then nothing more.",
        hints=[
            "`[0-9a-f]` with the `i` flag covers both cases.",
            "`{3,8}` also allows 5 and 7 digits; list the allowed lengths as alternatives.",
            "Anchor with `^` and `$`, and wrap the alternatives in a group so the anchors apply to all of them.",
        ],
        brute_force="Check `text[0] === '#'`, check the length is one of 4, 5, 7, 9, then loop over the characters. Longer, but perfectly fine.",
        approach="`/^#(?:[0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})$/i`\n\n**Dry run** `\"#12345\"`: `#` matches; alternative 1 takes 4 digits then `$` fails (one digit left), backtracks to 3 digits, fails; alternatives 2 and 3 need 6 or 8 digits; overall `false`.",
        complexity="O(n) in the length of the text (the pattern has only bounded backtracking).",
        pitfalls="- Without anchors `test` succeeds if a colour appears *anywhere* in the text.\n- `^#a|b|c$` anchors only the first and last alternative: `|` has the lowest precedence.\n- Forgetting the `i` flag rejects upper-case digits.",
        follow_up="Extend it to `rgb(…)` notation, or return the colour's numeric channels instead of a boolean.",
    ),
),
dict(
    id="js-extract-dates", title="Extract ISO dates from text", difficulty="Medium", pattern="Regular expressions",
    kind="js", entry="extractDates",
    description=r"""
Find every date written as `YYYY-MM-DD` inside a text and return them, in order of appearance, as objects
`{year, month, day}` with **numeric** values.

- month must be 01-12 and day 01-31 (no calendar check beyond that), otherwise the candidate is ignored
- the date must not be glued to other digits: in `12024-03-15` or `2024-03-150` there is no date
- letters or punctuation next to the date are fine

**Example:** `extractDates("Released 2024-03-15, patched 2024-04-01.")` → `[{year:2024,month:3,day:15},{year:2024,month:4,day:1}]`
""",
    starter="function extractDates(text) {\n  // your code\n}\n",
    solution=r'''function extractDates(text) {
  const out = [];
  const pattern = /(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)/g;
  for (const match of text.matchAll(pattern)) {
    const year = Number(match[1]), month = Number(match[2]), day = Number(match[3]);
    if (month >= 1 && month <= 12 && day >= 1 && day <= 31) out.push({ year, month, day });
  }
  return out;
}
''',
    tests=[["Released 2024-03-15, patched 2024-04-01."], [""], ["no dates here"], ["12024-03-15"], ["2024-03-150"],
           ["2024-13-01 and 2024-00-10 and 2024-05-00 and 2024-05-32"], ["x2024-03-15y"], ["2024-3-5"],
           ["1999-12-31 2000-01-01"], ["2024-03-15-2024-03-16"], ["20240315"], ["(0001-01-01)"],
           ["due:2031-12-31;2031-12-311;start:2030-01-01"], ["2024-02-31"]],
    wrong_solutions=[
        r'''function extractDates(text) {
  const m = /(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)/.exec(text);
  return m ? [{ year: Number(m[1]), month: Number(m[2]), day: Number(m[3]) }] : [];
}
''',
        r'''function extractDates(text) {
  return [...text.matchAll(/(\d{4})-(\d{2})-(\d{2})/g)].map((m) => ({ year: Number(m[1]), month: Number(m[2]), day: Number(m[3]) }))
    .filter((d) => d.month >= 1 && d.month <= 12 && d.day >= 1 && d.day <= 31);
}
''',
        r'''function extractDates(text) {
  return [...text.matchAll(/(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)/g)].map((m) => ({ year: Number(m[1]), month: Number(m[2]), day: Number(m[3]) }));
}
''',
        r'''function extractDates(text) {
  return [...text.matchAll(/(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)/g)].map((m) => ({ year: m[1], month: m[2], day: m[3] }))
    .filter((d) => d.month >= 1 && d.month <= 12 && d.day >= 1 && d.day <= 31);
}
''',
    ],
    guide=G(
        prereqs="Capture groups, the `g` flag with `matchAll`, look-ahead and look-behind (lessons on regular expressions).",
        intuition="Let the pattern find the *shape* (4-2-2 digits, not touching other digits) and let ordinary code judge the *numbers*. Range rules are awkward in a pattern and trivial in an `if`.",
        hints=[
            "Three groups: `(\\d{4})-(\\d{2})-(\\d{2})`.",
            "`(?<!\\d)` in front and `(?!\\d)` behind assert that no digit is adjacent, without consuming anything.",
            "`text.matchAll(pattern)` needs the `g` flag and gives one match array per date; convert the groups with `Number`.",
        ],
        brute_force="Slide a 10-character window over the text and test each slice by hand: O(n) as well, just more code and more chances for an off-by-one.",
        approach="**Dry run** on `\"2024-03-15-2024-03-16\"`: first match at index 0 (next char is `-`, not a digit); scanning resumes after it and finds the second date, whose previous character is `-`. Both pass the range check.",
        complexity="O(n) for a text of length n.",
        pitfalls="- Without the look-arounds, `12024-03-15` yields `2024-03-15`.\n- Forgetting `g` (or using `exec` once) returns only the first date.\n- Groups are strings: `\"03\"` is not `3` until converted.\n- `\\b` is not enough: `x2024-03-15y` has no word boundary before the year, yet it should match.",
        follow_up="Validate real calendar dates by constructing `new Date(Date.UTC(y, m - 1, d))` and checking that the parts survive the round trip.",
    ),
),
dict(
    id="js-camel-snake", title="camelCase to snake_case", difficulty="Medium", pattern="Regular expressions",
    kind="js", entry="camelToSnake",
    description=r"""
Convert an identifier from camelCase or PascalCase to snake_case with `String.prototype.replace` and regular expressions.

- insert `_` between a lower-case letter or digit and a following upper-case letter: `userId` → `user_id`
- treat a run of capitals as one word, but split before its last capital when a lower-case letter follows:
  `parseHTTPResponse` → `parse_http_response`, `HTMLParser` → `html_parser`
- the result is entirely lower-case; strings that are already snake_case come back unchanged

**Examples:** `camelToSnake("version2Beta")` → `"version2_beta"` · `camelToSnake("myURL")` → `"my_url"`
""",
    starter="function camelToSnake(name) {\n  // your code\n}\n",
    solution=r'''function camelToSnake(name) {
  return name
    .replace(/([a-z0-9])([A-Z])/g, "$1_$2")
    .replace(/([A-Z]+)([A-Z][a-z])/g, "$1_$2")
    .toLowerCase();
}
''',
    tests=[["userId"], ["parseHTTPResponse"], ["HTMLParser"], ["version2Beta"], ["myURL"], [""], ["a"], ["A"],
           ["already_snake"], ["ABC"], ["getX"], ["XAxis"], ["iOSVersion"], ["simple"], ["aB"], ["fooBarBazQux"],
           ["JSONToXMLConverter"]],
    wrong_solutions=[
        "function camelToSnake(name) { return name.replace(/([a-z0-9])([A-Z])/g, '$1_$2').toLowerCase(); }\n",
        "function camelToSnake(name) { return name.replace(/[A-Z]/g, (c) => '_' + c.toLowerCase()); }\n",
        "function camelToSnake(name) { return name.replace(/([a-z0-9])([A-Z])/, '$1_$2').replace(/([A-Z]+)([A-Z][a-z])/, '$1_$2').toLowerCase(); }\n",
    ],
    guide=G(
        prereqs="`replace` with the `g` flag, capture groups and `$1` references in the replacement (lesson *Regular expressions: backtracking, replace, lastIndex, parsing*).",
        intuition="There are two kinds of word boundary in such names: *lower→Upper* (`rI` in `userId`) and *end of an acronym* (`PR` in `HTTPResponse`, where the `R` starts a new word). One replacement per kind, then lower-case everything.",
        hints=[
            "First pass: `([a-z0-9])([A-Z])` → `$1_$2`.",
            "Second pass: a run of capitals followed by a capital-plus-lower-case pair: `([A-Z]+)([A-Z][a-z])` → `$1_$2`.",
            "Call `toLowerCase()` last, otherwise the patterns can no longer see the capitals.",
        ],
        brute_force="A character loop that looks at the previous and next character can make the same decisions; the two-regex form is the same logic written declaratively.",
        approach="**Dry run** `parseHTTPResponse`: pass 1 finds `eH` → `parse_HTTPResponse`. Pass 2: `[A-Z]+` greedily takes `HTTPR`, must give back one letter so that `[A-Z][a-z]` can match `Re` → `parse_HTTP_Response`. Lower-case → `parse_http_response`.",
        complexity="O(n) per pass.",
        pitfalls="- Prefixing every capital with `_` gives `_h_t_m_l_parser`.\n- Omitting `g` converts only the first boundary.\n- Lower-casing first destroys the information you need.",
        follow_up="Write the inverse `snakeToCamel` using a replacement **function**: `name.replace(/_([a-z0-9])/g, (_, c) => c.toUpperCase())`.",
    ),
),
dict(
    id="js-load-order", title="Module load order", difficulty="Medium", pattern="Graphs / modules",
    kind="js", entry="loadOrder",
    description=r"""
A module system must evaluate every module **after** the modules it imports. You are given an object mapping
each module name to the array of names it depends on (every dependency is itself a key).

Return the order in which the modules get evaluated when the loader works like this: go through the module
names in alphabetical order; to load a module, first load its not-yet-loaded dependencies in the order
they are listed, then the module itself.

If the dependencies contain a cycle (including a module importing itself), return `null`.

**Example:** `loadOrder({app: ["ui", "data"], ui: ["dom"], data: [], dom: []})` → `["dom", "ui", "data", "app"]`
""",
    starter="function loadOrder(modules) {\n  // your code\n}\n",
    solution=r'''function loadOrder(modules) {
  const state = new Map();
  const order = [];
  function visit(name) {
    if (state.get(name) === "done") return true;
    if (state.get(name) === "loading") return false;
    state.set(name, "loading");
    for (const dep of modules[name]) {
      if (!visit(dep)) return false;
    }
    state.set(name, "done");
    order.push(name);
    return true;
  }
  for (const name of Object.keys(modules).sort()) {
    if (!visit(name)) return null;
  }
  return order;
}
''',
    tests=[
        [{"app": ["ui", "data"], "ui": ["dom"], "data": [], "dom": []}],
        [{}],
        [{"solo": []}],
        [{"a": ["b"], "b": ["a"]}],
        [{"a": ["a"]}],
        [{"a": ["b"], "b": ["c"], "c": ["d"], "d": []}],
        [{"d": ["c"], "c": ["b"], "b": ["a"], "a": []}],
        [{"main": ["z", "y", "x"], "x": [], "y": [], "z": []}],
        [{"a": ["c", "b"], "b": ["d"], "c": ["d"], "d": []}],
        [{"a": [], "b": ["c"], "c": ["d"], "d": ["b"]}],
        [{"x": ["shared"], "y": ["shared"], "shared": ["base"], "base": []}],
        [{"b": [], "a": [], "c": []}],
        [{"a": ["b", "b", "b"], "b": []}],
        [{"m%d" % i: ["m%d" % (i + 1)] if i < 60 else [] for i in range(61)}],
    ],
    wrong_solutions=[
        "function loadOrder(modules) { return Object.keys(modules).sort(); }\n",
        "function loadOrder(modules) {\n  const done = new Set(), order = [];\n  function visit(name) {\n    if (done.has(name)) return;\n    done.add(name);\n    for (const dep of modules[name]) visit(dep);\n    order.push(name);\n  }\n  for (const name of Object.keys(modules).sort()) visit(name);\n  return order;\n}\n",
        "function loadOrder(modules) {\n  const state = new Map(), order = [];\n  function visit(name) {\n    if (state.get(name) === 'done') return true;\n    if (state.get(name) === 'loading') return false;\n    state.set(name, 'loading');\n    order.push(name);\n    for (const dep of modules[name]) if (!visit(dep)) return false;\n    state.set(name, 'done');\n    return true;\n  }\n  for (const name of Object.keys(modules).sort()) if (!visit(name)) return null;\n  return order;\n}\n",
    ],
    guide=G(
        prereqs="How modules depend on each other (lesson *ES modules and CommonJS*); depth-first traversal with recursion.",
        intuition="This is a depth-first walk in which a module is written down **after** its dependencies (post-order). Three states per module tell you everything: untouched, in progress, finished. Meeting an *in progress* module again means you followed a path that came back to itself: a cycle.",
        hints=[
            "Keep a `Map` from name to `\"loading\"` or `\"done\"`.",
            "Append the module to the result only after the loop over its dependencies has finished.",
            "Let `visit` return `false` when it bumps into a `\"loading\"` module and propagate that upwards.",
        ],
        brute_force="Repeatedly scan for a module whose dependencies are all loaded: O(n²) and it produces a different (still valid) order than the one requested.",
        approach="**Dry run** on the example, alphabetical start `app`: mark app loading → dep `ui` → dep `dom` → no deps → emit `dom` → emit `ui` → dep `data` → emit `data` → emit `app`. Later roots are already done. Result `[dom, ui, data, app]`.",
        complexity="O(V + E) after the O(V log V) sort; recursion depth up to the longest dependency chain.",
        pitfalls="- A single *visited* set cannot distinguish a cycle from a diamond (two modules sharing a dependency).\n- Emitting the module before its dependencies gives pre-order, the reverse of what is needed.\n- A self-import is a cycle of length one.",
        follow_up="Real ES modules *permit* cycles: bindings exist before evaluation, and a cycle only bites if a value is used before the module providing it has run. Kahn's algorithm (in-degree counting) is the iterative alternative.",
    ),
),
dict(
    id="js-event-loop-order", title="Predict the event-loop order", difficulty="Hard", pattern="Event loop simulation",
    kind="js", entry="predictOrder",
    description=r"""
Simulate the JavaScript event loop on a miniature script. A script is a list of operations run synchronously, in order:

- `["log", label]`: output `label` immediately
- `["micro", ops]`: queue `ops` (another script) as a **microtask**, like `Promise.resolve().then(...)`
- `["timeout", delay, ops]`: schedule `ops` as a **task** after `delay` ms, like `setTimeout(..., delay)`

Rules of the model:

1. The main script is the first task and starts at time 0. Running code takes no time.
2. After each task finishes, the microtask queue is drained **completely**, first in first out, including microtasks queued by other microtasks.
3. Then the pending timer with the smallest due time runs as the next task; ties go to the timer that was scheduled first. A timer set with delay `d` while the clock reads `t` is due at `t + d`, and the clock jumps to a timer's due time when it runs.

Return the labels in output order.

**Example:** `predictOrder([["log","A"], ["timeout",0,[["log","B"]]], ["micro",[["log","C"]]], ["log","D"]])` → `["A","D","C","B"]`
""",
    starter="function predictOrder(script) {\n  // your code\n}\n",
    solution=LOOP_SOLUTION,
    tests=[
        [[["log", "A"], ["timeout", 0, [["log", "B"]]], ["micro", [["log", "C"]]], ["log", "D"]]],
        [[]],
        [[["log", "only"]]],
        [[["micro", [["log", "m1"], ["micro", [["log", "m3"]]]]], ["micro", [["log", "m2"]]], ["log", "sync"]]],
        [[["timeout", 10, [["log", "t10"]]], ["timeout", 5, [["log", "t5"]]], ["timeout", 5, [["log", "t5b"]]]]],
        [[["timeout", 0, [["log", "t1"], ["micro", [["log", "t1-micro"]]]]], ["timeout", 0, [["log", "t2"]]]]],
        [[["timeout", 5, [["log", "five"], ["timeout", 3, [["log", "eight"]]]]], ["timeout", 6, [["log", "six"]]]]],
        [[["timeout", 5, [["log", "a"], ["timeout", 5, [["log", "a-then"]]]]], ["timeout", 10, [["log", "b"]]]]],
        [[["micro", [["timeout", 0, [["log", "late"]]], ["log", "micro"]]], ["timeout", 0, [["log", "early"]]], ["log", "sync"]]],
        [[["timeout", 1, [["micro", [["log", "x"], ["micro", [["log", "y"]]]]], ["log", "w"]]], ["timeout", 1, [["log", "z"]]]]],
        [[["log", 1], ["micro", [["log", 2], ["timeout", 0, [["log", 3], ["micro", [["log", 4]]]]], ["micro", [["log", 5]]]]], ["timeout", 0, [["log", 6]]], ["log", 7]]],
        [[["timeout", 100, [["log", "slow"]]], ["timeout", 0, [["timeout", 0, [["timeout", 0, [["log", "deep"]]]]]]], ["micro", [["micro", [["micro", [["log", "mmm"]]]]]]]]],
        [[["timeout", 2, [["log", "p"]]], ["timeout", 1, [["timeout", 1, [["log", "q"]]], ["log", "r"]]]]],
    ],
    wrong_solutions=[
        LOOP_SOLUTION.replace("run(script);\n  drain();", "run(script);").replace("run(next.ops);\n    drain();", "run(next.ops);") + "",
        LOOP_SOLUTION.replace("timers.push({ time: now + op[1], seq: seq++, ops: op[2] });", "timers.push({ time: op[1], seq: seq++, ops: op[2] });"),
        LOOP_SOLUTION.replace("while (micro.length > 0) run(micro.shift());", "const batch = micro.splice(0); for (const ops of batch) run(ops);"),
        LOOP_SOLUTION.replace("if (a.time < b.time || (a.time === b.time && a.seq < b.seq)) best = i;", "if (a.time <= b.time) best = i;"),
        LOOP_SOLUTION.replace("while (micro.length > 0) run(micro.shift());", "while (micro.length > 0) run(micro.pop());"),
    ],
    guide=G(
        prereqs="Tasks versus microtasks and run-to-completion (lesson *The event loop, tasks and microtasks*).",
        intuition="The whole event loop fits in one sentence: *run a task, empty the microtask queue, pick the next task, repeat.* Model the two queues as arrays and the sentence becomes the program.",
        hints=[
            "Write one helper `run(ops)` that executes a script: log now, push microtasks to one array, push timers (with their absolute due time and a sequence number) to another.",
            "Write `drain()` as `while (queue not empty) run(queue.shift())`; because it re-checks the queue, microtasks queued during draining are handled too.",
            "Main loop: `run(script); drain();` then repeatedly remove the earliest timer, set the clock, run it, drain.",
        ],
        brute_force="There is no shortcut around simulating; but you can keep the timers sorted or scan for the minimum each time (as the reference does), which is plenty for small inputs.",
        approach="**Dry run** of the example: run main → output `A`; timer B due at 0; microtask C queued; output `D`. Drain → `C`. Next timer → `B`. Result `A D C B`.\n\nFor `timeout 5 { five; timeout 3 {eight} }` and `timeout 6 {six}`: at time 5 output `five` and schedule *eight* for 5 + 3 = 8; the timer due at 6 runs before it.",
        complexity="O(n) operations plus O(T²) for selecting among T timers by scanning (a heap would make it O(T log T)).",
        pitfalls="- Running timers before microtasks.\n- Draining only the microtasks that existed when draining began; nested ones must run in the same drain.\n- Using the delay instead of the absolute due time for nested timers.\n- Breaking ties by taking the *latest* scheduled timer.",
        follow_up="Real browsers add more detail: separate task queues per source, rendering steps between tasks, a 4 ms clamp on deeply nested timers, and in Node the `process.nextTick` queue that runs before promise microtasks.",
    ),
),
dict(
    id="js-eval-expression", title="Arithmetic expression evaluator", difficulty="Hard", pattern="Parsing",
    kind="js", entry="evaluate",
    description=r"""
Write `evaluate(expr)` that computes the value of an arithmetic expression given as a string, **without `eval`
or `new Function`**. The expression contains non-negative decimal numbers (`12`, `3.5`), the binary operators
`+ - * /`, unary minus, parentheses and spaces. It is always well formed and never divides by zero.

Usual rules: `*` and `/` bind tighter than `+` and `-`; operators of equal precedence group from the left
(`10 - 4 - 3` is `3`); unary minus binds tightest (`2 * -3` is `-6`).

**Examples:** `evaluate("1 + 2 * 3")` → `7` · `evaluate("-(2 + 3) * 2")` → `-10` · `evaluate("8 / 4 / 2")` → `1`
""",
    compare="float",
    starter="function evaluate(expr) {\n  // your code\n}\n",
    solution=EVAL_SOLUTION,
    tests=[["1 + 2 * 3"], ["-(2 + 3) * 2"], ["8 / 4 / 2"], ["(1 + 2) * 3"], ["10 - 4 - 3"], ["2 * -3"], ["1.5 * 4"],
           ["42"], ["   7   "], ["2 * (3 + (4 - 1)) / 3"], ["--5"], ["1 - -1"], ["100 / 8"], ["3 + 4 * 2 / (1 - 5)"],
           ["0.1 + 0.2"], ["((((9))))"], ["2*3+4*5-6/2"], ["1-2-3-4-5"], ["-3 * -3 - -3"], ["12.25 + 0.75 * (8 - 6)"]],
    wrong_solutions=[
        r'''function evaluate(expr) {
  const t = expr.match(/\d+\.?\d*|[-+*\/()]/g) || [];
  let v = Number(t[0]);
  for (let i = 1; i < t.length; i += 2) {
    const n = Number(t[i + 1]);
    if (t[i] === "+") v += n; else if (t[i] === "-") v -= n; else if (t[i] === "*") v *= n; else v /= n;
  }
  return v;
}
''',
        EVAL_SOLUTION.replace('if (expr[pos] === "-") { pos++; value -= parseTerm(); }', 'if (expr[pos] === "-") { pos++; return value - parseExpression(); }'),
        EVAL_SOLUTION.replace('if (expr[pos] === "/") { pos++; value /= parseFactor(); }', 'if (expr[pos] === "/") { pos++; return value / parseTerm(); }'),
        EVAL_SOLUTION.replace('if (expr[pos] === "-") { pos++; return -parseFactor(); }', ''),
    ],
    guide=G(
        prereqs="Recursion, and the idea of a grammar with one function per precedence level (lessons *Pebble part 1* and *part 2*).",
        intuition="Precedence is nesting. An *expression* is terms joined by `+`/`-`; a *term* is factors joined by `*`/`/`; a *factor* is a number, a parenthesised expression, or a minus sign followed by a factor. Three small functions that call each other mirror those three sentences.",
        hints=[
            "Keep a position index into the string shared by all three functions, plus a helper that skips spaces.",
            "Inside `parseExpression` and `parseTerm`, use a **loop** that keeps folding the next operand into the running value; that gives left-to-right grouping.",
            "`parseFactor` handles `-` by returning `-parseFactor()`, `(` by calling `parseExpression()` and then skipping the `)`, and otherwise reads digits and dots.",
        ],
        brute_force="Processing tokens strictly left to right gets `1 + 2 * 3` wrong (9 instead of 7). The classic two-stack (shunting-yard) method is a valid alternative to recursive descent.",
        approach="```\nexpression := term (('+' | '-') term)*\nterm       := factor (('*' | '/') factor)*\nfactor     := number | '(' expression ')' | '-' factor\n```\n**Dry run** `1 + 2 * 3`: expression reads term → factor 1 (no `*`) → value 1; sees `+`, reads term → factor 2, sees `*`, factor 3 → 6; value 7; end.",
        complexity="O(n) time: every character is examined a constant number of times. Recursion depth equals parenthesis nesting.",
        pitfalls="- Writing the rule recursively on the right (`term - expression`) makes `10 - 4 - 3` evaluate as `10 - (4 - 3)`.\n- Forgetting unary minus after an operator (`2 * -3`).\n- Not skipping whitespace before every decision.\n- Floating-point results are compared with a tolerance, so `0.1 + 0.2` is fine.",
        follow_up="Add exponentiation `^` (right-associative, so recursion on the right is correct there), variables, and error messages with positions for malformed input.",
    ),
),
dict(
    id="js-vdom-diff", title="Virtual DOM diff", difficulty="Hard", pattern="Trees",
    kind="js", entry="diff",
    description=r"""
UI libraries describe the page as plain objects and compute the minimal set of real DOM updates by comparing
the old description with the new one. Implement that comparison.

A virtual node is either a **string** (a text node) or an object `{tag, props, children}` where `props` maps
attribute names to primitive values and `children` is an array of virtual nodes.

`diff(oldNode, newNode)` returns an array of patches. A `path` is the list of child indexes leading from the
root to the node concerned (`[]` is the root). Compare two nodes like this:

1. both strings: if they differ → `{type: "TEXT", path, text: newText}`
2. one is a string and the other is not, or the tags differ → `{type: "REPLACE", path, node: newNode}` and stop (do not look inside)
3. same tag: go through the union of prop names **in sorted order**; a name missing from the new props →
   `{type: "REMOVE_PROP", path, name}`; a name that is new or whose value changed → `{type: "SET_PROP", path, name, value}`
4. then compare the children pairwise by index (recursively, in order)
5. then, for extra new children, `{type: "INSERT", path: [...path, index], node}` in ascending index order
6. finally, for extra old children, `{type: "REMOVE", path: [...path, index]}` in **descending** index order (so that applying them one by one never shifts a later target)

**Example:** old `{tag:"p", props:{class:"a"}, children:["hi"]}`, new `{tag:"p", props:{class:"b"}, children:["ho"]}` →
`[{type:"SET_PROP", path:[], name:"class", value:"b"}, {type:"TEXT", path:[0], text:"ho"}]`
""",
    starter="function diff(oldNode, newNode) {\n  const patches = [];\n  // walk both trees together, pushing patches\n  return patches;\n}\n",
    solution=DIFF_SOLUTION,
    tests=[
        [h("p", {"class": "a"}, "hi"), h("p", {"class": "b"}, "ho")],
        ["same", "same"],
        ["old", "new"],
        [h("p"), h("p")],
        [h("p", None, "x"), h("div", None, "x")],
        ["text", h("b", None, "text")],
        [h("b", None, "text"), "text"],
        [h("a", {"href": "/x", "title": "t", "id": "k"}), h("a", {"href": "/y", "target": "_blank", "id": "k"})],
        [h("ul", None, h("li", None, "1")), h("ul", None, h("li", None, "1"), h("li", None, "2"), h("li", None, "3"))],
        [h("ul", None, h("li", None, "1"), h("li", None, "2"), h("li", None, "3"), h("li", None, "4")), h("ul", None, h("li", None, "1"))],
        [h("div", None, h("h1", None, "T"), h("p", {"class": "x"}, "a", h("em", None, "b"))),
         h("div", None, h("h1", None, "T2"), h("p", {"class": "x"}, "a", h("strong", None, "b"), "tail"))],
        [h("input", {"checked": True, "value": 1}), h("input", {"checked": False, "value": "1"})],
        [h("div", {"z": 1, "a": 1, "m": 1}), h("div", {"b": 2, "z": 2})],
        [h("div", None, h("span"), "t", h("span")), h("div", None, "t", h("span"))],
        [h("section", {"id": "s"}, h("ul", None, h("li", {"class": "on"}, "a"), h("li", None, "b"))),
         h("section", {"id": "s"}, h("ul", None, h("li", None, "a"), h("li", {"class": "on"}, "b"), h("li", None, "c")))],
        [h("div", None), h("div", None, "only")],
    ],
    wrong_solutions=[
        DIFF_SOLUTION.replace("for (let i = a.children.length - 1; i >= shared; i--)", "for (let i = shared; i < a.children.length; i++)"),
        DIFF_SOLUTION.replace('if (!Object.hasOwn(b.props, name)) patches.push({ type: "REMOVE_PROP", path, name });', 'if (!Object.hasOwn(b.props, name)) continue;'),
        "function diff(oldNode, newNode) {\n  return JSON.stringify(oldNode) === JSON.stringify(newNode) ? [] : [{ type: 'REPLACE', path: [], node: newNode }];\n}\n",
        DIFF_SOLUTION.replace("a.props[name] !== b.props[name]", "a.props[name] != b.props[name]"),
        DIFF_SOLUTION.replace("].sort();", "];"),
    ],
    guide=G(
        prereqs="Trees and recursion; the DOM as a tree of element and text nodes (lesson *JavaScript in the browser and the DOM tree*); `Object.keys`, `Set`.",
        intuition="Walk the two trees *in parallel*. At each position you see a pair of nodes and only have to answer a local question: same kind? same tag? which props differ? Then recurse into the children that exist on both sides and deal with the leftovers.",
        hints=[
            "Write an inner function `walk(a, b, path)` and start it with `walk(oldNode, newNode, [])`.",
            "Handle the text cases first with `typeof node === \"string\"`; after that both nodes are known to be objects.",
            "`shared = Math.min(a.children.length, b.children.length)` splits the children into *compare*, *insert* (new side longer) and *remove* (old side longer).",
        ],
        brute_force="Replacing the root whenever anything differs is correct but throws away the entire DOM subtree (and its scroll position, focus and input state) on every change.",
        approach="**Dry run** of the example: tags equal. Prop union `[class]`: present in both with different values → `SET_PROP`. Children: one shared pair, both strings, `hi` ≠ `ho` → `TEXT` at path `[0]`. No leftovers.\n\nFor old children `[1,2,3,4]` vs new `[1]`: shared = 1; removals are emitted for indexes 3, 2, 1 in that order.",
        complexity="O(n) in the number of nodes visited (the smaller tree, plus leftovers), because children are matched by index only.",
        pitfalls="- Removing extra children in ascending order: after removing index 1, the old index 2 has become index 1.\n- Recursing into nodes whose tags differ.\n- Comparing prop values with `!=` hides the change from `1` to `\"1\"`.\n- Forgetting to copy the path (`[...path, i]`); pushing onto a shared array corrupts earlier patches.\n- Not sorting prop names makes the output depend on object key order.",
        follow_up="Index-based matching handles insertions at the front badly (everything after shifts). Real libraries match children by a `key` prop; try adding keyed reordering.",
    ),
),
dict(
    id="js-debounce-sim", title="Debounce, simulated", difficulty="Medium", pattern="Timers",
    kind="js", entry="debounceCalls",
    description=r"""
A debounced function postpones its work until calls have stopped arriving for `wait` milliseconds, and then
runs once with the **arguments of the last call**. Timers cannot be tested directly here, so simulate one.

`debounceCalls(calls, wait)` receives `calls` as a list of `[time, value]` pairs sorted by time, and returns
the list of `[fireTime, value]` pairs describing when the underlying function actually runs.

- every call (re)starts a timer due at `time + wait`
- a call arriving **before** the pending timer is due cancels it; a call arriving at exactly the due time or
  later finds that the timer has already fired

**Example:** `debounceCalls([[0,"a"], [50,"b"], [120,"c"], [400,"d"]], 100)` → `[[220,"c"], [500,"d"]]`
""",
    starter="function debounceCalls(calls, wait) {\n  // your code\n}\n",
    solution="function debounceCalls(calls, wait) {\n  const fired = [];\n  let pending = null;\n  for (const [time, value] of calls) {\n    if (pending !== null && pending.due <= time) fired.push([pending.due, pending.value]);\n    pending = { due: time + wait, value };\n  }\n  if (pending !== null) fired.push([pending.due, pending.value]);\n  return fired;\n}\n",
    tests=[
        [[[0, "a"], [50, "b"], [120, "c"], [400, "d"]], 100],
        [[], 100],
        [[[10, "x"]], 30],
        [[[0, "a"], [100, "b"]], 100],
        [[[0, "a"], [99, "b"]], 100],
        [[[0, "a"], [101, "b"]], 100],
        [[[0, 1], [10, 2], [20, 3], [30, 4], [40, 5]], 15],
        [[[0, 1], [10, 2], [20, 3], [30, 4], [40, 5]], 5],
        [[[0, "a"], [0, "b"], [0, "c"]], 10],
        [[[5, "k"], [6, "l"], [300, "m"], [301, "n"], [302, "o"], [900, "p"]], 250],
        [[[0, "a"], [1, "b"]], 0],
        [[[i * 3, i] for i in range(100)] + [[1000, "end"]], 4],
    ],
    wrong_solutions=[
        "function debounceCalls(calls, wait) { return calls.map(([t, v]) => [t + wait, v]); }\n",
        "function debounceCalls(calls, wait) {\n  const fired = []; let last = -Infinity;\n  for (const [time, value] of calls) { if (time - last >= wait) fired.push([time, value]); last = time; }\n  return fired;\n}\n",
        "function debounceCalls(calls, wait) {\n  const fired = []; let pending = null;\n  for (const [time, value] of calls) {\n    if (pending !== null && pending.due < time) fired.push([pending.due, pending.value]);\n    pending = { due: time + wait, value };\n  }\n  if (pending !== null) fired.push([pending.due, pending.value]);\n  return fired;\n}\n",
        "function debounceCalls(calls, wait) {\n  const fired = []; let pending = null;\n  for (const [time, value] of calls) {\n    if (pending !== null && pending.due <= time) { fired.push([pending.due, pending.value]); pending = null; }\n    if (pending === null) pending = { due: time + wait, value };\n  }\n  if (pending !== null) fired.push([pending.due, pending.value]);\n  return fired;\n}\n",
    ],
    guide=G(
        prereqs="`setTimeout`/`clearTimeout` and the debounce pattern (lesson *Keys, pointers, scrolling, timers and debouncing*).",
        intuition="At any moment there is at most one pending timer. A new call either finds it already fired (record it) or cancels it; in both cases the call then installs a fresh timer carrying its own value.",
        hints=[
            "Keep one variable `pending = {due, value}` (or `null`).",
            "When a call arrives at `time`: if `pending.due <= time`, that timer fired; record `[due, value]`.",
            "After the loop, the last timer always fires.",
        ],
        brute_force="Step a clock millisecond by millisecond and check the timer at each tick: correct, but O(total time) instead of O(number of calls).",
        approach="**Dry run** with wait 100: call a@0 → pending due 100. b@50: 100 > 50, cancelled → due 150. c@120: 150 > 120, cancelled → due 220. d@400: 220 ≤ 400 → record `[220,\"c\"]`; pending due 500. End → `[500,\"d\"]`.",
        complexity="O(n) time, O(1) extra space besides the output.",
        pitfalls="- Firing with the *first* value of a burst instead of the last (that is leading-edge behaviour).\n- Reporting the call time rather than the fire time.\n- The tie rule: a call exactly at the due time does not cancel.\n- Forgetting the final pending timer.",
        follow_up="Write the real thing: `function debounce(fn, wait) { let id; return (...args) => { clearTimeout(id); id = setTimeout(() => fn(...args), wait); }; }`, then add a `leading` option and a `cancel` method.",
    ),
),
]
