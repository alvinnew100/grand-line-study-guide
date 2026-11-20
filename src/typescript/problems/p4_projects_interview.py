"""TypeScript track, real-project and interview problems: validation, state machines, variance, deep merge."""


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


MERGE_DRIVER = r'''
// --- driver (provided, do not change) ---
function mergeReport(base, patch) {
  const before = JSON.stringify(base);
  const merged = mergeDeep(base, patch);
  return { merged, baseUnchanged: JSON.stringify(base) === before };
}
'''

STR = {"type": "string"}
NUM = {"type": "number"}
BOOL = {"type": "boolean"}


def opt(s):
    return {"type": "optional", "inner": s}


def nullable(s):
    return {"type": "nullable", "inner": s}


def arr(s, **kw):
    return {"type": "array", "element": s, **kw}


def obj(shape, **kw):
    return {"type": "object", "shape": shape, **kw}


def lit(v):
    return {"type": "literal", "value": v}


def union(*o):
    return {"type": "union", "options": list(o)}


MEMBER = obj({
    "id": {"type": "number", "int": True, "min": 1},
    "name": {"type": "string", "min": 1, "max": 20},
    "email": opt(STR),
    "roles": arr(union(lit("crew"), lit("skipper"), lit("admin")), min=1),
})

HIER = {"Gull": "Bird", "Penguin": "Bird", "Bird": "Animal", "Dog": "Animal", "Herring": "Gull"}


def fn(params, returns):
    return {"params": params, "returns": returns}


PROBLEMS = [
# ------------------------------------------------------------------ 23
dict(
    id="ts-safe-json-parse", title="Safe JSON parse with a shape check", difficulty="Easy",
    pattern="Runtime validation", kind="js", entry="safeParse",
    description=r"""
`JSON.parse(text) as Settings` checks nothing. Write the honest version: parse, verify the shape, and report the
outcome as a discriminated union without ever throwing.

`safeParse(text, shape)`: `shape` maps each expected key to a type tag: `"string"`, `"number"`, `"boolean"`, `"array"`,
`"object"` (plain object) or `"null"`. A tag ending in `?` (for example `"number?"`) marks the key as optional.

Return `{"ok": true, "value": parsed}` when everything fits, otherwise `{"ok": false, "error": message}` with the
**first** problem found, checking in this order:

1. the text is not valid JSON → `"invalid JSON"`;
2. the parsed value is not a plain object (it is an array, `null` or a primitive) → `"expected object"`;
3. then for each key of `shape`, in the order given:
   - key absent and required → `"missing key: <key>"`;
   - key absent and optional → fine;
   - key present with the wrong type → `"wrong type for <key>: expected <tag>, got <actual>"`, where `<tag>` is the tag
     without `?` and `<actual>` is `"null"`, `"array"`, or the `typeof` of the value.

Keys not mentioned in `shape` are allowed.

**Examples:** `safeParse('{"port": 8080}', {"port": "number"})` → `{"ok": true, "value": {"port": 8080}}` ·
`safeParse('{"port": "8080"}', {"port": "number"})` → `{"ok": false, "error": "wrong type for port: expected number, got string"}`
""",
    starter='''/**
 * @param {string} text
 * @param {Record<string, string>} shape
 * @returns {{ ok: true, value: object } | { ok: false, error: string }}
 */
function safeParse(text, shape) {
  // your code
}
''',
    solution='''function safeParse(text, shape) {
  const tagOf = (v) => (v === null ? "null" : Array.isArray(v) ? "array" : typeof v);
  let value;
  try {
    value = JSON.parse(text);
  } catch (err) {
    return { ok: false, error: "invalid JSON" };
  }
  if (tagOf(value) !== "object") return { ok: false, error: "expected object" };
  for (const key of Object.keys(shape)) {
    const optional = shape[key].endsWith("?");
    const expected = optional ? shape[key].slice(0, -1) : shape[key];
    if (!Object.prototype.hasOwnProperty.call(value, key)) {
      if (optional) continue;
      return { ok: false, error: "missing key: " + key };
    }
    const actual = tagOf(value[key]);
    if (actual !== expected) {
      return { ok: false, error: "wrong type for " + key + ": expected " + expected + ", got " + actual };
    }
  }
  return { ok: true, value };
}
''',
    tests=[
        ['{"port": 8080}', {"port": "number"}],
        ['{"port": "8080"}', {"port": "number"}],
        ['{port: 8080}', {"port": "number"}],
        ['', {}],
        ['[1, 2]', {}],
        ['null', {"a": "string"}],
        ['42', {}],
        ['{}', {"host": "string", "port": "number"}],
        ['{"host": "h"}', {"host": "string", "port": "number?"}],
        ['{"host": "h", "port": null}', {"host": "string", "port": "number?"}],
        ['{"tags": [], "meta": {}, "gone": null}', {"tags": "array", "meta": "object", "gone": "null"}],
        ['{"tags": {}, "meta": []}', {"tags": "array", "meta": "object"}],
        ['{"a": 1, "b": "x", "extra": true}', {"b": "string", "a": "number"}],
        ['{"on": 0}', {"on": "boolean"}],
        ['{"b": 1, "a": 2}', {"a": "string", "b": "string"}],
        ['{}', {}],
    ],
    wrong_solutions=[
        '''function safeParse(text, shape) {
  const value = JSON.parse(text);
  for (const key of Object.keys(shape)) {
    const expected = shape[key].replace("?", "");
    if (typeof value[key] !== expected) return { ok: false, error: "wrong type for " + key + ": expected " + expected + ", got " + typeof value[key] };
  }
  return { ok: true, value };
}
''',
        '''function safeParse(text, shape) {
  const tagOf = (v) => (v === null ? "null" : Array.isArray(v) ? "array" : typeof v);
  let value;
  try { value = JSON.parse(text); } catch { return { ok: false, error: "invalid JSON" }; }
  if (tagOf(value) !== "object") return { ok: false, error: "expected object" };
  for (const key of Object.keys(shape)) {
    const optional = shape[key].endsWith("?");
    const expected = shape[key].replace("?", "");
    if (value[key] == null) { if (optional) continue; return { ok: false, error: "missing key: " + key }; }
    if (tagOf(value[key]) !== expected) return { ok: false, error: "wrong type for " + key + ": expected " + expected + ", got " + tagOf(value[key]) };
  }
  return { ok: true, value };
}
''',
    ],
    guide=G(
        prereqs="Why `as` validates nothing, `unknown`, and result unions (*Runtime validation and API response typing*).",
        intuition="Three gates in a row: is it JSON, is it an object, does each expected key have the expected kind of value. "
                  "The first gate that fails names the problem; passing all three earns the `ok: true` label.",
        hints=["Wrap `JSON.parse` in `try`/`catch` and return from the `catch`.",
               "A helper `tagOf(v)` returning `null`, `array` or `typeof v` is used for both the object test and the messages.",
               "Test presence with an own-property check: a key holding `null` is present."],
        brute_force="Call `JSON.parse` and compare `typeof value[key]` directly. It throws on bad text, on `null`, and cannot tell "
                    "arrays and `null` from objects.",
        approach="Parse, check the container, loop over the shape.\n\n"
                 "**Dry run**: text `{\"host\": \"h\", \"port\": null}`, shape `{host: string, port: number?}`. Valid JSON, a plain "
                 "object. `host`: present, tag `string` → fine. `port`: optional, but it **is** present, with tag `null` → "
                 "`wrong type for port: expected number, got null`. Optional means \"may be absent\", not \"may be null\".",
        complexity="Time O(length of text + number of keys), space O(size of parsed value).",
        pitfalls="Letting the exception escape. `typeof null` and `typeof []`. Treating `null` as absent. Reporting several errors "
                 "when the first is asked for, or checking keys in the wrong order.",
        follow_up="Collect all problems with their paths instead of stopping at the first; that is the next problem, *Build a "
                  "schema validator*.",
    ),
),
# ------------------------------------------------------------------ 24
dict(
    id="ts-schema-validate", title="Build a schema validator", difficulty="Hard",
    pattern="Runtime validation", kind="js", entry="validate",
    description=r"""
Libraries such as Zod describe data with **schemas**: runtime values that can check data and report precisely what is
wrong. Build a small one.

`validate(schema, value)` returns `{"success": true, "data": value}` when there are no problems, otherwise
`{"success": false, "errors": [{"path": ..., "message": ...}, ...]}` listing **every** problem in the order found.

`path` is the location as a dotted string: object keys and array indexes joined with `.`, for example `"roles.1"`;
the root is `""`.

**Schemas**

| schema | rule and messages |
|---|---|
| `{"type": "string", "min"?, "max"?}` | not a string → `expected string`. Then length < min → `string shorter than <min>`; length > max → `string longer than <max>` |
| `{"type": "number", "int"?, "min"?, "max"?}` | not a number → `expected number`. Then, each checked independently and in this order: `int` true and not an integer → `expected integer`; value < min → `number below <min>`; value > max → `number above <max>` |
| `{"type": "boolean"}` | `expected boolean` |
| `{"type": "literal", "value": v}` | value `!== v` → `expected literal ` + `JSON.stringify(v)` |
| `{"type": "array", "element": S, "min"?}` | not an array → `expected array`. Otherwise: length < min → `array shorter than <min>` (at the array's own path); then every element is validated against `S` at `path.index` |
| `{"type": "object", "shape": {key: S}, "strict"?}` | not a plain object → `expected object`. Otherwise each key of `shape`, in order, is validated at `path.key` (a missing key is validated as `undefined`). If `strict` is true, then each own key of the value that is not in `shape`, in the value's key order → `unexpected key` at `path.key` |
| `{"type": "optional", "inner": S}` | `undefined` passes; anything else is validated against `S` |
| `{"type": "nullable", "inner": S}` | `null` passes; anything else is validated against `S` |
| `{"type": "union", "options": [S, ...]}` | passes if at least one option produces no errors; otherwise one error `no union option matched` at this path |

**One global rule, applied first:** if the value is `undefined` (a missing key) and the schema is not `optional`, the
only error is `required` at that path.

**Example:** `validate({"type":"object","shape":{"id":{"type":"number"},"name":{"type":"string"}}}, {"id":"7"})` →
`{"success": false, "errors": [{"path": "id", "message": "expected number"}, {"path": "name", "message": "required"}]}`
""",
    starter='''/**
 * @param {object} schema
 * @param {unknown} value
 * @returns {{ success: true, data: unknown } | { success: false, errors: { path: string, message: string }[] }}
 */
function validate(schema, value) {
  // your code
}
''',
    solution='''function validate(schema, value) {
  function check(schema, value, path) {
    const at = (message) => [{ path: path.join("."), message }];
    if (value === undefined && schema.type !== "optional") return at("required");
    switch (schema.type) {
      case "string": {
        if (typeof value !== "string") return at("expected string");
        if (schema.min !== undefined && value.length < schema.min) return at("string shorter than " + schema.min);
        if (schema.max !== undefined && value.length > schema.max) return at("string longer than " + schema.max);
        return [];
      }
      case "number": {
        if (typeof value !== "number") return at("expected number");
        const errors = [];
        if (schema.int && !Number.isInteger(value)) errors.push(...at("expected integer"));
        if (schema.min !== undefined && value < schema.min) errors.push(...at("number below " + schema.min));
        if (schema.max !== undefined && value > schema.max) errors.push(...at("number above " + schema.max));
        return errors;
      }
      case "boolean":
        return typeof value === "boolean" ? [] : at("expected boolean");
      case "literal":
        return value === schema.value ? [] : at("expected literal " + JSON.stringify(schema.value));
      case "array": {
        if (!Array.isArray(value)) return at("expected array");
        const errors = [];
        if (schema.min !== undefined && value.length < schema.min) errors.push(...at("array shorter than " + schema.min));
        value.forEach((item, index) => errors.push(...check(schema.element, item, [...path, index])));
        return errors;
      }
      case "object": {
        if (typeof value !== "object" || value === null || Array.isArray(value)) return at("expected object");
        const errors = [];
        for (const key of Object.keys(schema.shape)) {
          const present = Object.prototype.hasOwnProperty.call(value, key);
          errors.push(...check(schema.shape[key], present ? value[key] : undefined, [...path, key]));
        }
        if (schema.strict) {
          for (const key of Object.keys(value)) {
            if (!Object.prototype.hasOwnProperty.call(schema.shape, key)) {
              errors.push({ path: [...path, key].join("."), message: "unexpected key" });
            }
          }
        }
        return errors;
      }
      case "optional":
        return value === undefined ? [] : check(schema.inner, value, path);
      case "nullable":
        return value === null ? [] : check(schema.inner, value, path);
      case "union":
        return schema.options.some((option) => check(option, value, path).length === 0) ? [] : at("no union option matched");
      default:
        throw new Error("Unknown schema type: " + schema.type);
    }
  }
  const errors = check(schema, value, []);
  return errors.length === 0 ? { success: true, data: value } : { success: false, errors };
}
''',
    tests=[
        [obj({"id": NUM, "name": STR}), {"id": "7"}],
        [MEMBER, {"id": 7, "name": "Asha", "roles": ["crew"]}],
        [MEMBER, {"id": 0.5, "name": "", "email": 5, "roles": ["crew", "pirate", 3]}],
        [MEMBER, {"id": 7, "name": "A name that is far too long for it", "roles": []}],
        [MEMBER, None],
        [MEMBER, [1, 2]],
        [STR, "x"],
        [STR, 5],
        [{"type": "number", "int": True, "min": 10, "max": 20}, 3.5],
        [{"type": "number", "min": 0, "max": 5}, 9],
        [BOOL, 0],
        [lit("on"), "off"],
        [lit(3), 3],
        [arr(NUM), [1, "2", 3, None]],
        [arr(arr(STR)), [["a"], ["b", 2], "c"]],
        [obj({"a": STR}, strict=True), {"a": "x", "b": 1, "c": 2}],
        [obj({"a": STR}), {"a": "x", "b": 1}],
        [obj({"n": nullable(NUM), "o": opt(NUM)}), {"n": None}],
        [obj({"n": nullable(NUM), "o": opt(NUM)}), {"o": None}],
        [union(STR, NUM), True],
        [union(STR, NUM), 4],
        [obj({"pos": obj({"lat": NUM, "lon": NUM}), "tags": arr(STR, min=1)}), {"pos": {"lat": "50"}, "tags": []}],
        [obj({"kind": union(lit("circle"), lit("rect")), "size": opt(nullable(NUM))}), {"kind": "hex", "size": "big"}],
        [obj({}, strict=True), {}],
        [arr(obj({"id": NUM})), [{"id": 1}, {}, {"id": "x"}]],
    ],
    examples=2,
    wrong_solutions=[
        # stops at the first error
        '''function validate(schema, value) {
  function check(s, v, path) {
    const at = (m) => ({ path: path.join("."), message: m });
    if (v === undefined && s.type !== "optional") return at("required");
    if (s.type === "string") { if (typeof v !== "string") return at("expected string"); if (s.min !== undefined && v.length < s.min) return at("string shorter than " + s.min); if (s.max !== undefined && v.length > s.max) return at("string longer than " + s.max); return null; }
    if (s.type === "number") { if (typeof v !== "number") return at("expected number"); if (s.int && !Number.isInteger(v)) return at("expected integer"); if (s.min !== undefined && v < s.min) return at("number below " + s.min); if (s.max !== undefined && v > s.max) return at("number above " + s.max); return null; }
    if (s.type === "boolean") return typeof v === "boolean" ? null : at("expected boolean");
    if (s.type === "literal") return v === s.value ? null : at("expected literal " + JSON.stringify(s.value));
    if (s.type === "array") { if (!Array.isArray(v)) return at("expected array"); if (s.min !== undefined && v.length < s.min) return at("array shorter than " + s.min); for (let i = 0; i < v.length; i++) { const e = check(s.element, v[i], [...path, i]); if (e) return e; } return null; }
    if (s.type === "object") { if (typeof v !== "object" || v === null || Array.isArray(v)) return at("expected object"); for (const k of Object.keys(s.shape)) { const e = check(s.shape[k], v[k], [...path, k]); if (e) return e; } if (s.strict) for (const k of Object.keys(v)) if (!(k in s.shape)) return { path: [...path, k].join("."), message: "unexpected key" }; return null; }
    if (s.type === "optional") return v === undefined ? null : check(s.inner, v, path);
    if (s.type === "nullable") return v === null ? null : check(s.inner, v, path);
    if (s.type === "union") return s.options.some((o) => !check(o, v, path)) ? null : at("no union option matched");
  }
  const e = check(schema, value, []);
  return e ? { success: false, errors: [e] } : { success: true, data: value };
}
''',
        # optional also accepts null; no "required" rule; typeof object accepts arrays/null
        '''function validate(schema, value) {
  function check(s, v, path) {
    const at = (m) => [{ path: path.join("."), message: m }];
    switch (s.type) {
      case "string": if (typeof v !== "string") return at("expected string"); if (s.min !== undefined && v.length < s.min) return at("string shorter than " + s.min); if (s.max !== undefined && v.length > s.max) return at("string longer than " + s.max); return [];
      case "number": { if (typeof v !== "number") return at("expected number"); const e = []; if (s.int && !Number.isInteger(v)) e.push(...at("expected integer")); if (s.min !== undefined && v < s.min) e.push(...at("number below " + s.min)); if (s.max !== undefined && v > s.max) e.push(...at("number above " + s.max)); return e; }
      case "boolean": return typeof v === "boolean" ? [] : at("expected boolean");
      case "literal": return v === s.value ? [] : at("expected literal " + JSON.stringify(s.value));
      case "array": { if (!Array.isArray(v)) return at("expected array"); const e = []; if (s.min !== undefined && v.length < s.min) e.push(...at("array shorter than " + s.min)); v.forEach((x, i) => e.push(...check(s.element, x, [...path, i]))); return e; }
      case "object": { if (typeof v !== "object" || v === null || Array.isArray(v)) return at("expected object"); const e = []; for (const k of Object.keys(s.shape)) e.push(...check(s.shape[k], v[k], [...path, k])); if (s.strict) for (const k of Object.keys(v)) if (!(k in s.shape)) e.push({ path: [...path, k].join("."), message: "unexpected key" }); return e; }
      case "optional": return v == null ? [] : check(s.inner, v, path);
      case "nullable": return v == null ? [] : check(s.inner, v, path);
      case "union": return s.options.some((o) => check(o, v, path).length === 0) ? [] : at("no union option matched");
    }
  }
  const errors = check(schema, value, []);
  return errors.length === 0 ? { success: true, data: value } : { success: false, errors };
}
''',
        # paths lose their parents (only the last key)
        '''function validate(schema, value) {
  function check(s, v, key) {
    const at = (m) => [{ path: String(key), message: m }];
    if (v === undefined && s.type !== "optional") return at("required");
    switch (s.type) {
      case "string": if (typeof v !== "string") return at("expected string"); if (s.min !== undefined && v.length < s.min) return at("string shorter than " + s.min); if (s.max !== undefined && v.length > s.max) return at("string longer than " + s.max); return [];
      case "number": { if (typeof v !== "number") return at("expected number"); const e = []; if (s.int && !Number.isInteger(v)) e.push(...at("expected integer")); if (s.min !== undefined && v < s.min) e.push(...at("number below " + s.min)); if (s.max !== undefined && v > s.max) e.push(...at("number above " + s.max)); return e; }
      case "boolean": return typeof v === "boolean" ? [] : at("expected boolean");
      case "literal": return v === s.value ? [] : at("expected literal " + JSON.stringify(s.value));
      case "array": { if (!Array.isArray(v)) return at("expected array"); const e = []; if (s.min !== undefined && v.length < s.min) e.push(...at("array shorter than " + s.min)); v.forEach((x, i) => e.push(...check(s.element, x, i))); return e; }
      case "object": { if (typeof v !== "object" || v === null || Array.isArray(v)) return at("expected object"); const e = []; for (const k of Object.keys(s.shape)) e.push(...check(s.shape[k], Object.prototype.hasOwnProperty.call(v, k) ? v[k] : undefined, k)); if (s.strict) for (const k of Object.keys(v)) if (!Object.prototype.hasOwnProperty.call(s.shape, k)) e.push({ path: k, message: "unexpected key" }); return e; }
      case "optional": return v === undefined ? [] : check(s.inner, v, key);
      case "nullable": return v === null ? [] : check(s.inner, v, key);
      case "union": return s.options.some((o) => check(o, v, key).length === 0) ? [] : at("no union option matched");
    }
  }
  const errors = check(schema, value, "");
  return errors.length === 0 ? { success: true, data: value } : { success: false, errors };
}
''',
    ],
    guide=G(
        prereqs="The miniature schema library and the difference between compile-time types and runtime validation (*Runtime "
                "validation and API response typing*); discriminated unions for results.",
        intuition="A schema is a tree that mirrors the data. Validation walks both trees together. Each node type knows how to "
                  "check one level and hands the levels below to its children, passing along the path travelled so far. Errors "
                  "are lists, and a parent's list is the concatenation of its children's.",
        hints=["Write an inner `check(schema, value, path)` that returns an array of errors; an empty array means valid.",
               "Apply the `required` rule at the very top of `check`, before the `switch`.",
               "Containers call `check` on each child with `[...path, key]`; `union` calls it on each option and only looks at "
               "whether the result is empty."],
        brute_force="Return `true`/`false` (a type guard). It is far shorter and tells the caller nothing about *what* is wrong, "
                    "which is the whole reason schema libraries exist.",
        approach="Recursive descent with error accumulation.\n\n"
                 "**Dry run**: schema `object{id: number, name: string}`, value `{id: \"7\"}`. Root: a plain object. Key `id`: "
                 "value `\"7\"`, not a number → `{path: \"id\", message: \"expected number\"}`. Key `name`: absent → validated as "
                 "`undefined` → global rule → `{path: \"name\", message: \"required\"}`. Two errors, `success: false`.\n\n"
                 "**Union dry run**: `union(literal \"circle\", literal \"rect\")` on `\"hex\"`: option 1 yields an error, option 2 "
                 "yields an error, no option is clean → one error `no union option matched`; the options' own errors are discarded.",
        complexity="Time O(size of value × number of union options along the way), space O(depth + number of errors).",
        pitfalls="Stopping at the first error. `optional` must not accept `null`, and `nullable` must not accept a missing key. "
                 "`typeof [] === \"object\"`. Building paths without the parents. Number checks are independent: `3.5` against "
                 "`int, min 10` reports two errors.",
        follow_up="In TypeScript, add `type Infer<S>` that derives the static type from a schema with conditional types and "
                  "`infer`, so one definition gives both the validator and the type.",
    ),
),
# ------------------------------------------------------------------ 25
dict(
    id="ts-state-machine", title="Run a tagged state machine", difficulty="Medium",
    pattern="Discriminated unions", kind="js", entry="runMachine",
    description=r"""
A data-loading screen is in exactly one state at a time. In TypeScript both the states and the events are discriminated
unions:

```typescript
type State =
  | { status: "idle" }
  | { status: "loading"; attempt: number }
  | { status: "success"; data: unknown }
  | { status: "failure"; error: string; attempts: number };
```

Write `runMachine(events)`. Start in `{ "status": "idle" }`, apply each event, and return the list of states **after
each event** (so the result has the same length as `events`).

| event | allowed from | next state |
|---|---|---|
| `{"type": "fetch"}` | `idle`, `success` | `{"status": "loading", "attempt": 1}` |
| `{"type": "resolve", "data": d}` | `loading` | `{"status": "success", "data": d}` |
| `{"type": "reject", "error": e}` | `loading` | `{"status": "failure", "error": e, "attempts": <the loading attempt>}` |
| `{"type": "retry"}` | `failure` with `attempts` < 3 | `{"status": "loading", "attempt": attempts + 1}` |
| `{"type": "reset"}` | any state | `{"status": "idle"}` |

An event that is not allowed in the current state, or whose `type` is not in the table, leaves the state unchanged
(the unchanged state is still recorded in the output).

**Example:** `runMachine([{"type":"fetch"},{"type":"reject","error":"timeout"},{"type":"retry"}])` →
`[{"status":"loading","attempt":1},{"status":"failure","error":"timeout","attempts":1},{"status":"loading","attempt":2}]`
""",
    starter='''/**
 * @typedef {{ status: "idle" } | { status: "loading", attempt: number } | { status: "success", data: unknown } | { status: "failure", error: string, attempts: number }} State
 * @typedef {{ type: "fetch" } | { type: "resolve", data: unknown } | { type: "reject", error: string } | { type: "retry" } | { type: "reset" }} Event
 * @param {Event[]} events
 * @returns {State[]}
 */
function runMachine(events) {
  // your code
}
''',
    solution='''function runMachine(events) {
  function transition(state, event) {
    switch (event.type) {
      case "fetch":
        return state.status === "idle" || state.status === "success" ? { status: "loading", attempt: 1 } : state;
      case "resolve":
        return state.status === "loading" ? { status: "success", data: event.data } : state;
      case "reject":
        return state.status === "loading" ? { status: "failure", error: event.error, attempts: state.attempt } : state;
      case "retry":
        return state.status === "failure" && state.attempts < 3 ? { status: "loading", attempt: state.attempts + 1 } : state;
      case "reset":
        return { status: "idle" };
      default:
        return state;
    }
  }
  const history = [];
  let state = { status: "idle" };
  for (const event of events) {
    state = transition(state, event);
    history.push(state);
  }
  return history;
}
''',
    tests=[
        [[{"type": "fetch"}, {"type": "reject", "error": "timeout"}, {"type": "retry"}]],
        [[]],
        [[{"type": "fetch"}, {"type": "resolve", "data": ["Asha", "Tobin"]}]],
        [[{"type": "resolve", "data": 1}, {"type": "reject", "error": "x"}, {"type": "retry"}]],
        [[{"type": "fetch"}, {"type": "fetch"}, {"type": "resolve", "data": None}, {"type": "fetch"}]],
        [[{"type": "fetch"}, {"type": "reject", "error": "a"}, {"type": "retry"}, {"type": "reject", "error": "b"},
          {"type": "retry"}, {"type": "reject", "error": "c"}, {"type": "retry"}, {"type": "fetch"}]],
        [[{"type": "fetch"}, {"type": "reset"}, {"type": "resolve", "data": 5}]],
        [[{"type": "fetch"}, {"type": "explode"}, {"type": "resolve", "data": {"ok": True}}]],
        [[{"type": "fetch"}, {"type": "resolve", "data": 1}, {"type": "reject", "error": "late"}, {"type": "retry"}]],
        [[{"type": "fetch"}, {"type": "reject", "error": "a"}, {"type": "reset"}, {"type": "retry"}, {"type": "fetch"},
          {"type": "reject", "error": "b"}]],
        [[{"type": "reset"}, {"type": "reset"}]],
        [[{"type": "fetch"}, {"type": "reject", "error": "a"}, {"type": "retry"}, {"type": "resolve", "data": "second try"},
          {"type": "fetch"}, {"type": "reject", "error": "again"}]],
    ],
    wrong_solutions=[
        # ignores current state: every event transitions
        '''function runMachine(events) {
  const history = [];
  let state = { status: "idle" };
  let attempt = 0;
  for (const e of events) {
    if (e.type === "fetch") { attempt = 1; state = { status: "loading", attempt }; }
    else if (e.type === "resolve") state = { status: "success", data: e.data };
    else if (e.type === "reject") state = { status: "failure", error: e.error, attempts: attempt };
    else if (e.type === "retry") { attempt++; state = { status: "loading", attempt }; }
    else if (e.type === "reset") state = { status: "idle" };
    history.push(state);
  }
  return history;
}
''',
        # no retry limit, fetch not allowed from success
        '''function runMachine(events) {
  const history = [];
  let s = { status: "idle" };
  for (const e of events) {
    if (e.type === "fetch" && s.status === "idle") s = { status: "loading", attempt: 1 };
    else if (e.type === "resolve" && s.status === "loading") s = { status: "success", data: e.data };
    else if (e.type === "reject" && s.status === "loading") s = { status: "failure", error: e.error, attempts: s.attempt };
    else if (e.type === "retry" && s.status === "failure") s = { status: "loading", attempt: s.attempts + 1 };
    else if (e.type === "reset") s = { status: "idle" };
    history.push(s);
  }
  return history;
}
''',
    ],
    guide=G(
        prereqs="Discriminated unions for states and events (*Interview essentials II*, exercise 7; *Runtime validation and API "
                "response typing*).",
        intuition="A state machine is a table: for each pair (current state, event) there is either a next state or \"stay "
                  "where you are\". The code is that table written as a `switch` on the event with a check of the current status "
                  "inside each case.",
        hints=["Write `transition(state, event)` returning the next state, and return `state` itself when the event is not "
               "allowed.",
               "The failure state must remember which attempt failed; read it from the loading state.",
               "Push the state after every event, changed or not."],
        brute_force="Keep separate flags (`isLoading`, `error`, `data`, `attempts`) and update them per event. That is the design "
                    "the tagged union replaces: flags can drift into impossible combinations such as loading with an error.",
        approach="Fold the events through `transition`, recording each result.\n\n"
                 "**Dry run**: `fetch, reject a, retry, reject b, retry, reject c, retry, fetch`. States: loading(1), "
                 "failure(a, 1), loading(2), failure(b, 2), loading(3), failure(c, 3), then `retry` is refused because attempts is "
                 "3 → failure(c, 3) again, then `fetch` is not allowed from failure → failure(c, 3).",
        complexity="Time O(number of events), space O(number of events) for the history.",
        pitfalls="Transitions that ignore the current state (a late `resolve` overwriting a failure). Forgetting the retry limit. "
                 "Not recording ignored events. Allowing `fetch` while already loading, which would restart the attempt count.",
        follow_up="Represent the table as data (`{ idle: { fetch: ... } }`) and write a generic interpreter; libraries such as "
                  "XState work this way.",
    ),
),
# ------------------------------------------------------------------ 26
dict(
    id="ts-function-variance", title="Function assignability and variance", difficulty="Medium",
    pattern="Variance", kind="js", entry="isFunctionAssignable",
    description=r"""
When may one function be used in place of another? The practical rule: *a replacement may accept more and return
less.* Implement the check that `strictFunctionTypes` performs.

`isFunctionAssignable(source, target, parents)`:

- A function type is `{"params": [typeName, ...], "returns": typeName}`.
- `parents` maps a type name to its direct supertype, for example `{"Gull": "Bird", "Bird": "Animal"}`. Type `A` is a
  **subtype** of `B` when `A === B` or `B` is reached by following `parents` upward from `A`.

`source` is assignable to `target` when all three hold:

1. **Arity.** `source` has no more parameters than `target` (a function may ignore trailing arguments).
2. **Parameters are contravariant.** For each parameter position `i` of `source`, `target.params[i]` is a subtype of
   `source.params[i]`: the source must accept at least everything the target's callers may pass.
3. **Return type is covariant.** `source.returns` is a subtype of `target.returns`. Special case: if `target.returns`
   is `"void"`, any source return type is accepted.

**Examples** (with `Gull → Bird → Animal`):
`isFunctionAssignable({"params":["Bird"],"returns":"Gull"}, {"params":["Gull"],"returns":"Bird"}, parents)` → `true` ·
`isFunctionAssignable({"params":["Gull"],"returns":"void"}, {"params":["Bird"],"returns":"void"}, parents)` → `false`
""",
    starter='''/**
 * @typedef {{ params: string[], returns: string }} FnType
 * @param {FnType} source
 * @param {FnType} target
 * @param {Record<string, string>} parents
 * @returns {boolean}
 */
function isFunctionAssignable(source, target, parents) {
  // your code
}
''',
    solution='''function isFunctionAssignable(source, target, parents) {
  function isSubtype(a, b) {
    let current = a;
    const seen = new Set();
    while (current !== undefined && !seen.has(current)) {
      if (current === b) return true;
      seen.add(current);
      current = Object.prototype.hasOwnProperty.call(parents, current) ? parents[current] : undefined;
    }
    return false;
  }
  if (source.params.length > target.params.length) return false;
  for (let i = 0; i < source.params.length; i++) {
    if (!isSubtype(target.params[i], source.params[i])) return false;
  }
  return target.returns === "void" || isSubtype(source.returns, target.returns);
}
''',
    tests=[
        [fn(["Bird"], "Gull"), fn(["Gull"], "Bird"), HIER],
        [fn(["Gull"], "void"), fn(["Bird"], "void"), HIER],
        [fn(["Bird"], "void"), fn(["Bird"], "void"), HIER],
        [fn([], "Gull"), fn(["Bird", "Dog"], "Animal"), HIER],
        [fn(["Bird", "Dog"], "Animal"), fn(["Bird"], "Animal"), HIER],
        [fn(["Animal"], "Herring"), fn(["Herring"], "Animal"), HIER],
        [fn(["Bird"], "Animal"), fn(["Bird"], "Bird"), HIER],
        [fn(["Bird"], "Dog"), fn(["Bird"], "void"), HIER],
        [fn(["Bird"], "void"), fn(["Bird"], "Dog"), HIER],
        [fn(["Dog"], "Dog"), fn(["Gull"], "Dog"), HIER],
        [fn(["Animal", "Bird"], "Gull"), fn(["Dog", "Penguin"], "Bird"), HIER],
        [fn(["Animal", "Gull"], "Gull"), fn(["Dog", "Penguin"], "Bird"), HIER],
        [fn([], "void"), fn([], "void"), {}],
        [fn(["string"], "number"), fn(["string"], "number"), {}],
        [fn(["string"], "number"), fn(["number"], "number"), {}],
        [fn(["Bird"], "Penguin"), fn(["Herring"], "Bird"), HIER],
    ],
    wrong_solutions=[
        # parameters covariant (the classic mistake)
        '''function isFunctionAssignable(source, target, parents) {
  const isSubtype = (a, b) => { for (let c = a; c !== undefined; c = parents[c]) if (c === b) return true; return false; };
  if (source.params.length > target.params.length) return false;
  for (let i = 0; i < source.params.length; i++) if (!isSubtype(source.params[i], target.params[i])) return false;
  return target.returns === "void" || isSubtype(source.returns, target.returns);
}
''',
        # requires equal arity
        '''function isFunctionAssignable(source, target, parents) {
  const isSubtype = (a, b) => { for (let c = a; c !== undefined; c = parents[c]) if (c === b) return true; return false; };
  if (source.params.length !== target.params.length) return false;
  for (let i = 0; i < source.params.length; i++) if (!isSubtype(target.params[i], source.params[i])) return false;
  return target.returns === "void" || isSubtype(source.returns, target.returns);
}
''',
        # return type contravariant and no void rule
        '''function isFunctionAssignable(source, target, parents) {
  const isSubtype = (a, b) => { for (let c = a; c !== undefined; c = parents[c]) if (c === b) return true; return false; };
  if (source.params.length > target.params.length) return false;
  for (let i = 0; i < source.params.length; i++) if (!isSubtype(target.params[i], source.params[i])) return false;
  return isSubtype(target.returns, source.returns);
}
''',
    ],
    guide=G(
        prereqs="Variance, the Bird/Gull example and parameter-count compatibility (*Interview essentials I*, *Functions, arrays "
                "and tuples*).",
        intuition="Imagine the code that holds the `target` type. It will call the function with the target's parameter types "
                  "and use the result as the target's return type. The source must cope with those calls (so its parameters "
                  "must be at least as wide) and must hand back something usable (so its return must be at least as narrow).",
        hints=["Write `isSubtype(a, b)` by walking up the `parents` map from `a`.",
               "For parameters the arguments to `isSubtype` are swapped compared with the return type.",
               "Fewer source parameters is fine; more is not."],
        brute_force="Require identical parameter and return types. Simple and safe, but it rejects many valid substitutions, "
                    "including every callback that ignores an argument.",
        approach="Three checks in order: arity, each parameter (contravariant), return (covariant, with the `void` exception).\n\n"
                 "**Dry run**: source `(Gull) => void`, target `(Bird) => void`. Arity 1 ≤ 1. Parameter 0: is the target's `Bird` a "
                 "subtype of the source's `Gull`? Walk up from `Bird`: Bird, Animal: no `Gull` → `false`. In words: a holder of "
                 "the target may pass a penguin, and the source only handles gulls.\n\n"
                 "**Second**: source `(Bird) => Gull`, target `(Gull) => Bird`. Parameter: `Gull` is a subtype of `Bird` → ok. "
                 "Return: `Gull` is a subtype of `Bird` → ok → `true`.",
        complexity="Time O(parameters × height of the hierarchy), space O(height) for the visited set.",
        pitfalls="Checking parameters in the covariant direction. Demanding equal parameter counts. Forgetting that a `void` "
                 "target accepts any return. A cycle in `parents` would loop for ever without a visited set.",
        follow_up="Add a `method: true` flag for which parameters are checked bivariantly (either direction), mirroring "
                  "TypeScript's exception for method syntax.",
    ),
),
# ------------------------------------------------------------------ 27
dict(
    id="ts-deep-partial-merge", title="Deep partial merge", difficulty="Medium",
    pattern="Utility types", kind="js", entry="mergeReport",
    description=r"""
`DeepPartial<T>` describes a patch: any subset of the fields of `T`, at any depth. The matching runtime operation
applies such a patch to a complete object.

Write `mergeDeep(base, patch)` returning a **new** value, without modifying `base` or `patch`:

- If both `base` and `patch` are plain objects (not arrays, not `null`), the result has every key of `base` and every
  key of `patch`. For a key present in `patch`, the result is `mergeDeep(base[key], patch[key])`; keys only in `base`
  are kept.
- In every other case the patch wins: the result is `patch`. That covers primitives, `null` (an explicit `null` in the
  patch overwrites), arrays (replaced as a whole, never merged element by element), and a plain object replacing a
  non-object.

The provided driver `mergeReport(base, patch)` returns `{ "merged": ..., "baseUnchanged": true/false }`, where
`baseUnchanged` tells whether `base` still looks the same afterwards.

**Example:** `mergeDeep({"theme": {"colour": "navy", "size": 14}, "wrap": true}, {"theme": {"size": 16}})` →
`{"theme": {"colour": "navy", "size": 16}, "wrap": true}`
""",
    starter='''/**
 * @template T
 * @param {T} base
 * @param {unknown} patch  in TypeScript: DeepPartial<T>
 * @returns {T}
 */
function mergeDeep(base, patch) {
  // your code
}
''' + MERGE_DRIVER,
    solution='''function mergeDeep(base, patch) {
  const isPlain = (v) => typeof v === "object" && v !== null && !Array.isArray(v);
  if (!isPlain(base) || !isPlain(patch)) return patch;
  const result = { ...base };
  for (const key of Object.keys(patch)) {
    result[key] = Object.prototype.hasOwnProperty.call(base, key) ? mergeDeep(base[key], patch[key]) : patch[key];
  }
  return result;
}
''' + MERGE_DRIVER,
    tests=[
        [{"theme": {"colour": "navy", "size": 14}, "wrap": True}, {"theme": {"size": 16}}],
        [{"a": 1}, {}],
        [{}, {"a": 1}],
        [{"a": {"b": {"c": 1, "d": 2}, "e": 3}}, {"a": {"b": {"c": 10}}}],
        [{"tags": ["a", "b", "c"]}, {"tags": ["z"]}],
        [{"a": {"b": 1}}, {"a": None}],
        [{"a": None}, {"a": {"b": 1}}],
        [{"a": 5}, {"a": {"b": 1}}],
        [{"a": {"b": 1}}, {"a": 7}],
        [{"n": 0, "s": "", "f": False}, {"n": 1}],
        [{"n": 1, "s": "x", "f": True}, {"n": 0, "s": "", "f": False}],
        [{"list": [{"id": 1, "name": "a"}]}, {"list": [{"id": 2}]}],
        [{"a": {"x": 1}, "b": {"y": 2}}, {"b": {"z": 3}, "c": {"w": 4}}],
        [{"deep": {"er": {"est": {"v": 1, "keep": True}}}}, {"deep": {"er": {"est": {"v": 2}}, "added": 1}}],
    ],
    wrong_solutions=[
        # shallow spread
        '''function mergeDeep(base, patch) {
  return { ...base, ...patch };
}
''' + MERGE_DRIVER,
        # mutates base
        '''function mergeDeep(base, patch) {
  const isPlain = (v) => typeof v === "object" && v !== null && !Array.isArray(v);
  if (!isPlain(base) || !isPlain(patch)) return patch;
  for (const key of Object.keys(patch)) base[key] = mergeDeep(base[key], patch[key]);
  return base;
}
''' + MERGE_DRIVER,
        # arrays merged by index, null in patch ignored
        '''function mergeDeep(base, patch) {
  if (patch === null || patch === undefined) return base;
  if (typeof base !== "object" || base === null || typeof patch !== "object") return patch;
  const result = Array.isArray(base) ? [...base] : { ...base };
  for (const key of Object.keys(patch)) result[key] = mergeDeep(base[key], patch[key]);
  return result;
}
''' + MERGE_DRIVER,
    ],
    guide=G(
        prereqs="`Partial` is shallow; `DeepPartial` and the deep merge sketch (*Interview essentials II*, exercise 11).",
        intuition="Two plain objects are merged key by key, and the same question is asked again one level down. As soon as "
                  "either side is anything else, there is nothing to merge and the patch replaces the base.",
        hints=["A helper `isPlain(v)`: an object, not `null`, not an array.",
               "Start the result as a shallow copy of `base`, then overwrite each key that the patch mentions.",
               "Never assign into `base`; the driver checks that it is unchanged."],
        brute_force="`{ ...base, ...patch }`. One level deep it is right. Below that, a patch of `{theme: {size: 16}}` replaces "
                    "the whole `theme` object and `colour` disappears.",
        approach="Recursive merge returning fresh objects along the patched path.\n\n"
                 "**Dry run**: base `{a: {b: {c: 1, d: 2}, e: 3}}`, patch `{a: {b: {c: 10}}}`. Both plain → copy base; key `a`: "
                 "both plain → copy; key `b`: both plain → copy `{c: 1, d: 2}`; key `c`: `1` and `10` are not plain → `10`. "
                 "Unwinding gives `{a: {b: {c: 10, d: 2}, e: 3}}`. `base` itself was only read.",
        complexity="Time O(size of patch + number of keys copied along the patched path), space the same.",
        pitfalls="Mutating `base`. Treating arrays as objects and merging them by index. Ignoring an explicit `null` in the patch. "
                 "Using truthiness, which would drop a patch value of `0` or `false`.",
        follow_up="Write the type: `type DeepPartial<T> = T extends object ? { [K in keyof T]?: DeepPartial<T[K]> } : T`, and note "
                  "which of its cases (functions, arrays) need special handling.",
    ),
),
]
