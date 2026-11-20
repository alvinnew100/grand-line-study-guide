"""TypeScript track, Parts III and IV problems: configuration, enums, runtime utility types, routes, type descriptors."""


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


FREEZE_DRIVER = r'''
// --- driver (provided, do not change) ---
function freezeReport(value, mutations) {
  "use strict";
  const frozen = deepFreeze(value);
  let blocked = 0;
  for (const [path, replacement] of mutations) {
    let target = frozen;
    for (let i = 0; i < path.length - 1; i++) target = target[path[i]];
    try {
      target[path[path.length - 1]] = replacement;   // throws in strict mode if the target is frozen
    } catch (err) {
      blocked++;
    }
  }
  return { sameReference: frozen === value, blocked, value: frozen };
}
'''


def L(v):
    return {"kind": "literal", "value": v}


def A(e):
    return {"kind": "array", "element": e}


def U(*m):
    return {"kind": "union", "members": list(m)}


def T(*e):
    return {"kind": "tuple", "elements": list(e)}


def O(props):
    return {"kind": "object", "props": props}


def F(params, returns):
    return {"kind": "function", "params": params, "returns": returns}


def P(name, type_, optional=False):
    d = {"name": name, "type": type_}
    if optional:
        d["optional"] = True
    return d


TSCONFIGS = {
    "base": {"compilerOptions": {"target": "ES2022", "strict": True, "skipLibCheck": True}, "include": ["src", "types"],
             "references": [{"path": "../shared"}]},
    "api": {"extends": "base", "compilerOptions": {"outDir": "dist", "strict": False}, "include": ["src"]},
    "api-test": {"extends": "api", "compilerOptions": {"noEmit": True}, "exclude": ["dist"], "references": [{"path": "../api"}]},
    "web": {"extends": "base", "compilerOptions": {"jsx": "react-jsx"}, "files": ["main.tsx"]},
    "bare": {},
    "orphan": {"extends": "missing"},
    "loop-a": {"extends": "loop-b", "compilerOptions": {"a": 1}},
    "loop-b": {"extends": "loop-c"},
    "loop-c": {"extends": "loop-a"},
    "self": {"extends": "self"},
    "only-options": {"extends": "bare", "compilerOptions": {"module": "NodeNext"}},
    "deep": {"extends": "api-test", "compilerOptions": {"target": "ES5"}, "include": []},
}

PROBLEMS = [
# ------------------------------------------------------------------ 14
dict(
    id="ts-strict-flags", title="Expand the strict flag", difficulty="Easy",
    pattern="Configuration", kind="js", entry="effectiveFlags",
    description=r"""
In `tsconfig.json`, `"strict": true` switches on a family of eight checks, and each member can still be set
individually. An individual setting always wins over `strict`.

The family: `noImplicitAny`, `strictNullChecks`, `strictFunctionTypes`, `strictBindCallApply`,
`strictPropertyInitialization`, `noImplicitThis`, `useUnknownInCatchVariables`, `alwaysStrict`.

Write `effectiveFlags(compilerOptions)` returning an object with exactly those eight keys, each `true` or `false`:

- if the flag is set in `compilerOptions` (to `true` or `false`), use that value;
- otherwise use the value of `compilerOptions.strict`, or `false` when `strict` is not set.

Ignore every other option.

**Example:** `effectiveFlags({"strict": true, "strictPropertyInitialization": false})` → all eight `true` except
`strictPropertyInitialization: false`.
""",
    starter='''/**
 * @param {Record<string, unknown>} compilerOptions
 * @returns {Record<string, boolean>}
 */
function effectiveFlags(compilerOptions) {
  // your code
}
''',
    solution='''function effectiveFlags(compilerOptions) {
  const family = ["noImplicitAny", "strictNullChecks", "strictFunctionTypes", "strictBindCallApply",
    "strictPropertyInitialization", "noImplicitThis", "useUnknownInCatchVariables", "alwaysStrict"];
  const base = compilerOptions.strict === true;
  const out = {};
  for (const flag of family) {
    out[flag] = typeof compilerOptions[flag] === "boolean" ? compilerOptions[flag] : base;
  }
  return out;
}
''',
    tests=[
        [{"strict": True, "strictPropertyInitialization": False}],
        [{}],
        [{"strict": True}],
        [{"strict": False}],
        [{"strictNullChecks": True}],
        [{"strict": False, "noImplicitAny": True, "strictNullChecks": True}],
        [{"strict": True, "target": "ES2022", "noUncheckedIndexedAccess": True}],
        [{"strict": True, "alwaysStrict": False, "noImplicitThis": False, "useUnknownInCatchVariables": False}],
        [{"noImplicitAny": False}],
        [{"strict": True, "noImplicitAny": True}],
    ],
    wrong_solutions=[
        '''function effectiveFlags(o) {
  const family = ["noImplicitAny", "strictNullChecks", "strictFunctionTypes", "strictBindCallApply",
    "strictPropertyInitialization", "noImplicitThis", "useUnknownInCatchVariables", "alwaysStrict"];
  const out = {};
  for (const f of family) out[f] = Boolean(o[f] || o.strict);
  return out;
}
''',
        '''function effectiveFlags(o) {
  const family = ["noImplicitAny", "strictNullChecks", "strictFunctionTypes", "strictBindCallApply",
    "strictPropertyInitialization", "noImplicitThis", "useUnknownInCatchVariables", "alwaysStrict"];
  const out = {};
  for (const f of family) out[f] = o[f] === true;
  return out;
}
''',
    ],
    guide=G(
        prereqs="The strict family (*Configuration: tsconfig.json and the strictness flags*).",
        intuition="`strict` is a default for eight switches. A switch that was set by hand keeps its own value; a switch that "
                  "was not set takes the default. The subtle case is a switch set by hand to `false`.",
        hints=["Keep the family in an array and loop over it.",
               "Decide \"was it set?\" with `typeof value === \"boolean\"`, not with truthiness.",
               "`strict` missing means the default is `false`."],
        brute_force="Write eight separate lines such as `noImplicitAny: o.noImplicitAny ?? o.strict ?? false`. It works and is "
                    "repetitive; a loop over the list of names says the same thing once.",
        approach="Compute the default, then fill in each flag.\n\n"
                 "**Dry run** on `{strict: true, strictPropertyInitialization: false}`: default is `true`. Seven flags are not set → "
                 "`true`. `strictPropertyInitialization` is a boolean (`false`) → keep `false`. Using `o[f] || o.strict` here "
                 "would turn that `false` back into `true`, which is the bug to avoid.",
        complexity="Time and space O(1): always eight flags.",
        pitfalls="`||` cannot distinguish \"explicitly false\" from \"not set\". Returning unrelated options such as `target`.",
        follow_up="`tsc --showConfig` prints the real effective configuration; compare its output with yours for a project.",
    ),
),
# ------------------------------------------------------------------ 15
dict(
    id="ts-tsconfig-extends", title="Resolve a tsconfig extends chain", difficulty="Medium",
    pattern="Configuration", kind="js", entry="resolveConfig",
    description=r"""
A `tsconfig.json` can inherit from another with `"extends"`. Implement the inheritance rules.

`resolveConfig(configs, name)`: `configs` maps a file name to its configuration object; `name` is the one to resolve.
A configuration may contain `extends` (the name of its parent), `compilerOptions` (an object), `include`, `exclude`,
`files` and `references` (arrays).

Rules:

1. If the configuration has `extends`, first resolve the parent (which may itself extend another).
2. `compilerOptions`: merged **key by key**; the child's value wins. The result always has a `compilerOptions`
   object, possibly empty.
3. `include`, `exclude`, `files`: if the child defines the key, it **replaces** the parent's list entirely (even with an
   empty list); otherwise the parent's list is inherited. A key nobody defines is absent from the result.
4. `references` is **not inherited**: the result has `references` only if the configuration named `name` defines it.
5. The result never contains `extends`.

Errors, returned as `{"error": message}`:

- a name (the starting one or any parent) that is not in `configs`: `"cannot find <name>"`;
- a cycle: `"circular extends: "` followed by the chain of names from the start, joined with `" -> "` and ending with
  the repeated name, for example `"circular extends: a -> b -> a"`.

**Example:** with `base = {compilerOptions: {strict: true, target: "ES2022"}, include: ["src", "types"]}` and
`api = {extends: "base", compilerOptions: {strict: false, outDir: "dist"}, include: ["src"]}`,
`resolveConfig(configs, "api")` → `{"compilerOptions": {"strict": false, "target": "ES2022", "outDir": "dist"}, "include": ["src"]}`
""",
    starter='''/**
 * @param {Record<string, { extends?: string, compilerOptions?: object, include?: string[], exclude?: string[], files?: string[], references?: object[] }>} configs
 * @param {string} name
 * @returns {object}
 */
function resolveConfig(configs, name) {
  // your code
}
''',
    solution='''function resolveConfig(configs, name) {
  const chain = [];
  let current = name;
  while (true) {
    if (!Object.prototype.hasOwnProperty.call(configs, current)) return { error: "cannot find " + current };
    if (chain.includes(current)) return { error: "circular extends: " + [...chain, current].join(" -> ") };
    chain.push(current);
    const parent = configs[current].extends;
    if (parent === undefined) break;
    current = parent;
  }
  const result = { compilerOptions: {} };
  for (const file of chain.reverse()) {           // root ancestor first, requested config last
    const config = configs[file];
    Object.assign(result.compilerOptions, config.compilerOptions ?? {});
    for (const key of ["include", "exclude", "files"]) {
      if (config[key] !== undefined) result[key] = config[key];
    }
  }
  if (configs[name].references !== undefined) result.references = configs[name].references;
  return result;
}
''',
    tests=[
        [TSCONFIGS, "api"],
        [TSCONFIGS, "base"],
        [TSCONFIGS, "api-test"],
        [TSCONFIGS, "web"],
        [TSCONFIGS, "bare"],
        [TSCONFIGS, "orphan"],
        [TSCONFIGS, "loop-a"],
        [TSCONFIGS, "loop-b"],
        [TSCONFIGS, "self"],
        [TSCONFIGS, "nowhere"],
        [TSCONFIGS, "only-options"],
        [TSCONFIGS, "deep"],
        [{}, "x"],
    ],
    examples=2,
    wrong_solutions=[
        # shallow spread: child's compilerOptions replace the parent's
        '''function resolveConfig(configs, name) {
  const chain = [];
  let current = name;
  while (true) {
    if (!Object.prototype.hasOwnProperty.call(configs, current)) return { error: "cannot find " + current };
    if (chain.includes(current)) return { error: "circular extends: " + [...chain, current].join(" -> ") };
    chain.push(current);
    if (configs[current].extends === undefined) break;
    current = configs[current].extends;
  }
  let result = { compilerOptions: {} };
  for (const file of chain.reverse()) result = { ...result, ...configs[file] };
  delete result.extends;
  if (configs[name].references === undefined) delete result.references;
  return result;
}
''',
        # include lists concatenated, references inherited
        '''function resolveConfig(configs, name) {
  const chain = [];
  let current = name;
  while (true) {
    if (!Object.prototype.hasOwnProperty.call(configs, current)) return { error: "cannot find " + current };
    if (chain.includes(current)) return { error: "circular extends: " + [...chain, current].join(" -> ") };
    chain.push(current);
    if (configs[current].extends === undefined) break;
    current = configs[current].extends;
  }
  const result = { compilerOptions: {} };
  for (const file of chain.reverse()) {
    const c = configs[file];
    Object.assign(result.compilerOptions, c.compilerOptions ?? {});
    for (const key of ["include", "exclude", "files", "references"]) {
      if (c[key] !== undefined) result[key] = [...(result[key] ?? []), ...c[key]];
    }
  }
  return result;
}
''',
        # no cycle detection guard beyond depth, wrong error text
        '''function resolveConfig(configs, name, seen = []) {
  if (!configs[name]) return { error: "cannot find " + name };
  if (seen.includes(name)) return { error: "circular extends: " + name };
  const c = configs[name];
  const parent = c.extends === undefined ? { compilerOptions: {} } : resolveConfig(configs, c.extends, [...seen, name]);
  if (parent.error) return parent;
  const result = { ...parent, compilerOptions: { ...parent.compilerOptions, ...(c.compilerOptions ?? {}) } };
  delete result.references;
  for (const key of ["include", "exclude", "files", "references"]) if (c[key] !== undefined) result[key] = c[key];
  return result;
}
''',
    ],
    guide=G(
        prereqs="The `extends` rules in *Configuration: tsconfig.json and the strictness flags*.",
        intuition="Inheritance is a chain: grandparent, parent, child. Lay the chain out from the most distant ancestor to the "
                  "requested file and apply each layer on top of the previous one. Different keys have different stacking rules: "
                  "options blend, file lists replace, references do not travel.",
        hints=["First walk upward collecting the names; that walk is also where missing files and cycles are detected.",
               "Reverse the chain, then fold: `Object.assign` for `compilerOptions`, plain assignment for the three lists.",
               "Add `references` at the end from the requested configuration only."],
        brute_force="Recursion: resolve the parent, then merge the child onto it. Equivalent in cost; it needs a `seen` list "
                    "passed down to detect cycles and to build the error message.",
        approach="Two phases: collect the chain, then apply it root first.\n\n"
                 "**Dry run** for `api-test` (extends `api`, which extends `base`). Chain collected: `api-test`, `api`, `base`; "
                 "reversed: `base`, `api`, `api-test`. After `base`: options `{target, strict: true, skipLibCheck}`, include "
                 "`[src, types]`. After `api`: `strict` becomes `false`, `outDir` added, include replaced by `[src]`. After "
                 "`api-test`: `noEmit` added, `exclude: [dist]` set, include still `[src]`. References: only `api-test`'s own; "
                 "`base`'s reference to `../shared` is not inherited.",
        complexity="Time O(chain length × options), space O(chain length + options).",
        pitfalls="`{...parent, ...child}` replaces the whole `compilerOptions` object. Concatenating `include` lists. Inheriting "
                 "`references`. An empty `include: []` in the child still replaces the parent's list. A config that extends itself.",
        follow_up="Real `extends` also accepts an array of parents (TypeScript 5.0 and later), applied left to right. Extend your "
                  "solution to support it.",
    ),
),
# ------------------------------------------------------------------ 16
dict(
    id="ts-enum-reverse", title="Compile an enum with reverse mapping", difficulty="Medium",
    pattern="Syntax extensions", kind="js", entry="buildEnum",
    description=r"""
A TypeScript `enum` compiles to a real object. Numeric members get entries in **both** directions (name → number and
number → name, the *reverse mapping*); string members get only name → value.

Write `buildEnum(members)` that produces that object. Each member is either

- a string `"Name"`: a member without an initialiser, or
- a pair `["Name", value]` where `value` is a number or a string.

Rules:

1. A member without an initialiser gets `0` if it is the first member, otherwise the previous member's numeric value
   plus one.
2. If the previous member has a **string** value, a member without an initialiser is an error: return
   `{"error": "Enum member must have initializer: <Name>"}` (for the first such member).
3. For a numeric member store `result[name] = number` and `result[String(number)] = name`. If two members share a
   number, the later one wins the reverse entry.
4. For a string member store only `result[name] = value`.

**Examples:** `buildEnum(["Low", "High"])` → `{"Low": 0, "High": 1, "0": "Low", "1": "High"}` ·
`buildEnum([["Port", "red"]])` → `{"Port": "red"}`
""",
    starter='''/**
 * @param {(string | [string, string | number])[]} members
 * @returns {Record<string, string | number> | { error: string }}
 */
function buildEnum(members) {
  // your code
}
''',
    solution='''function buildEnum(members) {
  const result = {};
  let previous = -1;           // numeric value of the previous member, or null after a string member
  for (const member of members) {
    let name;
    let value;
    if (Array.isArray(member)) {
      [name, value] = member;
    } else {
      name = member;
      if (previous === null) return { error: "Enum member must have initializer: " + name };
      value = previous + 1;
    }
    result[name] = value;
    if (typeof value === "number") {
      result[String(value)] = name;
      previous = value;
    } else {
      previous = null;
    }
  }
  return result;
}
''',
    tests=[
        [["Low", "High"]],
        [[["Port", "red"]]],
        [[]],
        [["Low", "Rising", "High", "Falling"]],
        [[["Ok", 200], "Created", ["NotFound", 404], "Gone"]],
        [[["Port", "red"], ["Starboard", "green"]]],
        [[["Port", "red"], "Starboard"]],
        [["A", ["B", "bee"], ["C", 10], "D"]],
        [[["A", 1], ["B", 1]]],
        [[["Minus", -1], "Zero", "One"]],
        [["A", ["B", "x"], "C", "D"]],
        [[["Half", 0.5], "Next"]],
        [[["Up", 1], ["Down", 2], ["Left", 4], ["Right", 8]]],
    ],
    wrong_solutions=[
        '''function buildEnum(members) {
  const result = {};
  members.forEach((m, i) => {
    const [name, value] = Array.isArray(m) ? m : [m, i];
    result[name] = value;
    if (typeof value === "number") result[String(value)] = name;
  });
  return result;
}
''',
        '''function buildEnum(members) {
  const result = {};
  let previous = -1;
  for (const m of members) {
    let name, value;
    if (Array.isArray(m)) [name, value] = m;
    else { name = m; if (previous === null) return { error: "Enum member must have initializer: " + name }; value = previous + 1; }
    result[name] = value;
    result[String(value)] = name;
    previous = typeof value === "number" ? value : null;
  }
  return result;
}
''',
    ],
    guide=G(
        prereqs="What an enum compiles to (*Syntax extensions*).",
        intuition="Walk the members while remembering one thing: the last numeric value. It supplies the next automatic value, "
                  "and its absence (after a string member) is what makes a bare member illegal.",
        hints=["Use a variable `previous` that starts at −1, so the first automatic value is 0.",
               "After a string member set `previous` to `null`.",
               "Only numeric members get the second, reverse entry."],
        brute_force="Number the members by their index. It gives the right answer only when no member has an initialiser; the "
                    "moment one says `= 200`, the following members must continue from 201.",
        approach="One pass.\n\n"
                 "**Dry run** on `[[\"Ok\", 200], \"Created\", [\"NotFound\", 404], \"Gone\"]`: `Ok` = 200, reverse `\"200\"` → `Ok`, "
                 "previous 200. `Created` has no initialiser → 201. `NotFound` = 404. `Gone` → 405. Eight entries in total.\n\n"
                 "For `[[\"Port\", \"red\"], \"Starboard\"]`: `Port` is a string member, previous becomes `null`; `Starboard` has no "
                 "initialiser → error.",
        complexity="Time and space O(n).",
        pitfalls="Adding reverse entries for string members (TypeScript does not, and they could collide with member names). "
                 "Using the index as the value. Forgetting that a numeric member after a string member re-enables automatic values.",
        follow_up="`Object.keys` of a numeric enum returns names and numbers mixed. Write `enumNames(e)` that returns only the "
                  "member names.",
    ),
),
# ------------------------------------------------------------------ 17
dict(
    id="ts-pick-omit", title="Runtime Pick and Omit", difficulty="Easy",
    pattern="Utility types", kind="js", entry="pickOmit",
    description=r"""
`Pick<T, K>` and `Omit<T, K>` change a **type**; nothing happens to the object at runtime. When you really need a
smaller object (to strip a password before sending a response, say) you need the value-level versions.

Write `pickOmit(mode, source, keys)`:

- `mode` is `"pick"` or `"omit"`.
- `"pick"`: return a new object with only the listed keys that `source` actually has as own properties. Listed keys
  that `source` lacks are skipped (they do **not** appear with `undefined`).
- `"omit"`: return a new object with every own key of `source` except the listed ones.
- Values are copied as they are (a shallow copy). Duplicate keys in `keys` have no extra effect.

**Examples:** `pickOmit("pick", {"id": 1, "name": "Asha", "hash": "x"}, ["id", "name"])` → `{"id": 1, "name": "Asha"}` ·
`pickOmit("omit", {"id": 1, "name": "Asha", "hash": "x"}, ["hash"])` → `{"id": 1, "name": "Asha"}`
""",
    starter='''/**
 * @param {"pick" | "omit"} mode
 * @param {Record<string, unknown>} source
 * @param {string[]} keys
 * @returns {Record<string, unknown>}
 */
function pickOmit(mode, source, keys) {
  // your code
}
''',
    solution='''function pickOmit(mode, source, keys) {
  const listed = new Set(keys);
  const out = {};
  for (const key of Object.keys(source)) {
    if (listed.has(key) === (mode === "pick")) out[key] = source[key];
  }
  return out;
}
''',
    tests=[
        ["pick", {"id": 1, "name": "Asha", "hash": "x"}, ["id", "name"]],
        ["omit", {"id": 1, "name": "Asha", "hash": "x"}, ["hash"]],
        ["pick", {"id": 1}, ["id", "missing"]],
        ["omit", {"id": 1}, ["missing"]],
        ["pick", {}, ["a"]],
        ["omit", {}, []],
        ["pick", {"a": None, "b": 0, "c": False}, ["a", "b", "c"]],
        ["pick", {"a": 1, "b": 2}, []],
        ["omit", {"a": 1, "b": 2}, ["a", "b"]],
        ["pick", {"a": 1, "b": 2}, ["a", "a", "a"]],
        ["omit", {"nested": {"x": 1}, "list": [1, 2], "keep": True}, ["list"]],
        ["pick", {"toString": "mine"}, ["toString", "constructor"]],
    ],
    wrong_solutions=[
        '''function pickOmit(mode, source, keys) {
  const out = {};
  if (mode === "pick") for (const k of keys) out[k] = source[k] ?? null;
  else for (const k of Object.keys(source)) if (!keys.includes(k)) out[k] = source[k];
  return out;
}
''',
        '''function pickOmit(mode, source, keys) {
  const out = {};
  for (const k of Object.keys(source)) {
    if (mode === "pick" ? keys.includes(k) && source[k] : !keys.includes(k)) out[k] = source[k];
  }
  return out;
}
''',
    ],
    guide=G(
        prereqs="`Pick` and `Omit` as mapped types (*Type operations*).",
        intuition="Both operations are a filter over the object's own keys. The only difference is whether \"listed\" means keep "
                  "or drop.",
        hints=["Iterate over `Object.keys(source)`, not over `keys`: that automatically skips keys the object lacks.",
               "A `Set` makes the membership test O(1).",
               "Never test the *value* to decide whether to keep a key: `null`, `0` and `false` are legitimate values."],
        brute_force="For `pick`, loop over `keys` and copy `source[key]`. It creates entries for keys the object does not have, "
                    "and reads inherited members such as `constructor`.",
        approach="Build a set of listed keys and filter.\n\n"
                 "**Dry run**: `pickOmit(\"pick\", {id: 1}, [\"id\", \"missing\"])`. Own keys: `id`. Listed? yes, and mode is pick → "
                 "keep. `missing` is never visited because the object does not own it. Result `{id: 1}`.",
        complexity="Time O(n + k) for n own keys and k listed keys; space O(n + k).",
        pitfalls="Emitting `undefined`/`null` for missing keys. Dropping falsy values. Mutating `source` with `delete`.",
        follow_up="Type it: `function pick<T extends object, K extends keyof T>(source: T, keys: K[]): Pick<T, K>`.",
    ),
),
# ------------------------------------------------------------------ 18
dict(
    id="ts-required-keys", title="Runtime Required and Partial check", difficulty="Easy",
    pattern="Utility types", kind="js", entry="checkRequired",
    description=r"""
`Required<T>` says every key must be present; `Partial<T>` says every key may be absent. A real type mixes both.
Check an object against such a description at runtime.

Write `checkRequired(value, spec)`. `spec` maps each known key to `"required"` or `"optional"`. Return:

- `missing`: required keys that `value` does not have as own properties, sorted alphabetically;
- `extra`: own keys of `value` that are not in `spec`, sorted alphabetically (this mirrors excess property checking);
- `ok`: `true` when both lists are empty.

A key whose value is `null`, `0`, `""` or `false` **is present**.

**Example:** `checkRequired({"id": 1, "nick": null, "age": 3}, {"id": "required", "name": "required", "nick": "optional"})` →
`{"missing": ["name"], "extra": ["age"], "ok": false}`
""",
    starter='''/**
 * @param {Record<string, unknown>} value
 * @param {Record<string, "required" | "optional">} spec
 * @returns {{ missing: string[], extra: string[], ok: boolean }}
 */
function checkRequired(value, spec) {
  // your code
}
''',
    solution='''function checkRequired(value, spec) {
  const has = (obj, key) => Object.prototype.hasOwnProperty.call(obj, key);
  const missing = Object.keys(spec).filter((key) => spec[key] === "required" && !has(value, key)).sort();
  const extra = Object.keys(value).filter((key) => !has(spec, key)).sort();
  return { missing, extra, ok: missing.length === 0 && extra.length === 0 };
}
''',
    tests=[
        [{"id": 1, "nick": None, "age": 3}, {"id": "required", "name": "required", "nick": "optional"}],
        [{"id": 1, "name": "Asha"}, {"id": "required", "name": "required"}],
        [{}, {"id": "required", "name": "required", "b": "required"}],
        [{}, {"a": "optional"}],
        [{}, {}],
        [{"z": 1, "y": 2, "x": 3}, {}],
        [{"id": 0, "name": "", "ok": False}, {"id": "required", "name": "required", "ok": "required"}],
        [{"id": None}, {"id": "required"}],
        [{"nick": "A"}, {"id": "required", "nick": "optional"}],
        [{"zeta": 1, "alpha": 2}, {"mid": "required", "beta": "required", "alpha": "optional"}],
        [{"toString": 1}, {"constructor": "required"}],
    ],
    wrong_solutions=[
        '''function checkRequired(value, spec) {
  const missing = Object.keys(spec).filter((k) => spec[k] === "required" && !value[k]).sort();
  const extra = Object.keys(value).filter((k) => !spec[k]).sort();
  return { missing, extra, ok: missing.length === 0 && extra.length === 0 };
}
''',
        '''function checkRequired(value, spec) {
  const has = (o, k) => Object.prototype.hasOwnProperty.call(o, k);
  const missing = Object.keys(spec).filter((k) => !has(value, k));
  const extra = Object.keys(value).filter((k) => !has(spec, k));
  return { missing, extra, ok: missing.length === 0 };
}
''',
    ],
    guide=G(
        prereqs="Optional properties and excess property checking (*Objects and structural typing*); `Required`/`Partial` "
                "(*Type operations*).",
        intuition="Two set differences. Required keys minus the keys the object has gives `missing`; the object's keys minus the "
                  "known keys gives `extra`.",
        hints=["Presence is about the key, so use an own-property test.", "Sort both lists before returning.",
               "Optional keys never appear in `missing`."],
        brute_force="Nested loops comparing every spec key with every object key: O(n × m). Own-property lookups make each test "
                    "O(1).",
        approach="Filter the spec's keys, filter the value's keys, sort.\n\n"
                 "**Dry run** on value `{id: 1, nick: null, age: 3}` and spec `{id: required, name: required, nick: optional}`: "
                 "`id` present; `name` required and absent → missing; `nick` optional, skip. Value keys: `id` known, `nick` known "
                 "(present even though `null`), `age` unknown → extra. `ok` is `false`.",
        complexity="Time O((n + m) log(n + m)) because of sorting; space O(n + m).",
        pitfalls="Truthiness reports `0`, `\"\"`, `false` and `null` as missing. `spec[k]` is truthy for inherited names like "
                 "`toString`.",
        follow_up="Add a third status `\"forbidden\"`, or nest specs to check sub-objects.",
    ),
),
# ------------------------------------------------------------------ 19
dict(
    id="ts-deep-freeze", title="Deep freeze: a runtime DeepReadonly", difficulty="Medium",
    pattern="Utility types", kind="js", entry="freezeReport",
    description=r"""
`Readonly<T>` and `as const` protect data only while compiling. `Object.freeze` protects at runtime, but only one level
deep. Combine the two ideas.

Write `deepFreeze(value)`:

- If `value` is an object or an array, freeze it **and everything reachable inside it** (nested objects and arrays at
  any depth), then return the **same** reference (do not copy).
- Any other value (number, string, boolean, `null`) is returned unchanged.

The provided driver `freezeReport(value, mutations)` calls your `deepFreeze`, then attempts each mutation in strict
mode, where writing to a frozen object throws. A mutation is `[path, replacement]`: follow `path` (a list of keys) and
assign `replacement` to the last key. The driver returns

`{ "sameReference": ..., "blocked": number of mutations that threw, "value": the object afterwards }`.

If your freeze is complete, every mutation is blocked and `value` is unchanged.

**Example:** `freezeReport({"a": {"b": 1}}, [[["a", "b"], 2], [["c"], 3]])` →
`{"sameReference": true, "blocked": 2, "value": {"a": {"b": 1}}}`
""",
    starter='''/**
 * @template T
 * @param {T} value
 * @returns {T}  in TypeScript: DeepReadonly<T>
 */
function deepFreeze(value) {
  // your code
}
''' + FREEZE_DRIVER,
    solution='''function deepFreeze(value) {
  if (typeof value !== "object" || value === null) return value;
  if (Object.isFrozen(value)) return value;
  Object.freeze(value);
  for (const key of Object.keys(value)) deepFreeze(value[key]);
  return value;
}
''' + FREEZE_DRIVER,
    tests=[
        [{"a": {"b": 1}}, [[["a", "b"], 2], [["c"], 3]]],
        [{"a": 1}, [[["a"], 2]]],
        [{"tags": ["x", "y"]}, [[["tags", 0], "z"], [["tags", 2], "new"], [["tags"], []]]],
        [[1, [2, [3, [4]]]], [[[1, 1, 1, 0], 99], [[0], 0]]],
        [{"a": {"b": {"c": {"d": {"e": 1}}}}}, [[["a", "b", "c", "d", "e"], 2], [["a", "b", "c", "d", "f"], 3]]],
        [5, []],
        [None, []],
        ["text", []],
        [{}, [[["x"], 1]]],
        [{"list": [{"id": 1}, {"id": 2}]}, [[["list", 1, "id"], 20], [["list", 0, "name"], "n"]]],
        [{"a": None, "b": {"c": None}}, [[["a"], 1], [["b", "c"], 1], [["b", "d"], 1]]],
        [{"x": {"y": 1}, "z": [1]}, []],
    ],
    wrong_solutions=[
        '''function deepFreeze(value) {
  return typeof value === "object" && value !== null ? Object.freeze(value) : value;
}
''' + FREEZE_DRIVER,
        '''function deepFreeze(value) {
  if (typeof value !== "object" || value === null) return value;
  const copy = Array.isArray(value) ? value.map(deepFreeze) : Object.fromEntries(Object.entries(value).map(([k, v]) => [k, deepFreeze(v)]));
  return Object.freeze(copy);
}
''' + FREEZE_DRIVER,
        '''function deepFreeze(value) {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return value;
  Object.freeze(value);
  for (const key of Object.keys(value)) deepFreeze(value[key]);
  return value;
}
''' + FREEZE_DRIVER,
    ],
    guide=G(
        prereqs="`readonly`, `as const` and why they are compile-time only (*Interfaces and classes*, *Type modifiers*); shallow "
                "versus deep utility types (*Type operations*).",
        intuition="Freezing is like `Readonly<T>`: one level. To get `DeepReadonly<T>` you repeat the operation on every value "
                  "inside, which is recursion over the object tree.",
        hints=["The base case is anything that is not an object, plus `null`.",
               "Freeze the current object, then recurse into `Object.keys(value)`; this works for arrays too.",
               "Return the original reference. Skipping objects that are already frozen also makes the function safe on "
               "structures that refer back to themselves."],
        brute_force="`Object.freeze(value)` alone. Top-level assignments are blocked; nested ones go straight through.",
        approach="Check, freeze, recurse, return.\n\n"
                 "**Dry run** on `{tags: [\"x\", \"y\"]}` with mutations `tags[0] = \"z\"`, `tags[2] = \"new\"`, `tags = []`. The outer "
                 "object is frozen, then the array. In strict mode all three assignments throw: changing an element, adding an "
                 "element, and replacing the property. `blocked` is 3 and the value is unchanged. With a shallow freeze only the "
                 "third would be blocked.",
        complexity="Time and space O(number of nested values); recursion depth equals nesting depth.",
        pitfalls="`typeof null === \"object\"`. Forgetting arrays. Returning a frozen copy leaves the original mutable and makes "
                 "`sameReference` false. Outside strict mode writes to frozen objects fail silently, which is why the driver "
                 "declares `\"use strict\"`.",
        follow_up="Write the matching type: `type DeepReadonly<T> = T extends object ? { readonly [K in keyof T]: DeepReadonly<T[K]> } : T`.",
    ),
),
# ------------------------------------------------------------------ 20
dict(
    id="ts-route-params", title="Match a route and extract parameters", difficulty="Medium",
    pattern="Template literal types", kind="js", entry="matchRoute",
    description=r"""
Template literal types can pull parameter names out of a route pattern at compile time
(`"/quays/:quayId"` → `"quayId"`). Web frameworks do the matching job at runtime. Write that matcher.

`matchRoute(pattern, path)` returns an object of captured parameters, or `null` if the path does not match.

Split both strings on `/` and ignore empty segments (so leading, trailing and doubled slashes do not matter). Then
compare segment by segment. A pattern segment is one of:

| pattern segment | matches | captures |
|---|---|---|
| plain text such as `berths` | exactly that text (case-sensitive) | nothing |
| `:name` | any one segment | `name` → that segment |
| `:name?` (only as the last pattern segment) | one segment, or none | `name` → the segment, or no key at all when absent |
| `*` (only as the last pattern segment) | all remaining segments, possibly none | `"*"` → the remaining segments joined with `/` (`""` when none) |

Apart from the optional and wildcard cases the number of segments must be equal. Captured values are the raw text.

**Examples:** `matchRoute("/quays/:quayId/berths/:berthId", "/quays/north/berths/12")` → `{"quayId": "north", "berthId": "12"}` ·
`matchRoute("/files/*", "/files/a/b.txt")` → `{"*": "a/b.txt"}` · `matchRoute("/quays/:id", "/quays")` → `null`
""",
    starter='''/**
 * @param {string} pattern
 * @param {string} path
 * @returns {Record<string, string> | null}
 */
function matchRoute(pattern, path) {
  // your code
}
''',
    solution='''function matchRoute(pattern, path) {
  const split = (text) => text.split("/").filter((part) => part !== "");
  const want = split(pattern);
  const have = split(path);
  const params = {};
  for (let i = 0; i < want.length; i++) {
    const segment = want[i];
    const isLast = i === want.length - 1;
    if (segment === "*" && isLast) {
      params["*"] = have.slice(i).join("/");
      return params;
    }
    if (segment.startsWith(":") && segment.endsWith("?") && isLast) {
      if (have.length > i + 1) return null;
      if (have.length === i + 1) params[segment.slice(1, -1)] = have[i];
      return params;
    }
    if (i >= have.length) return null;
    if (segment.startsWith(":")) params[segment.slice(1)] = have[i];
    else if (segment !== have[i]) return null;
  }
  return have.length === want.length ? params : null;
}
''',
    tests=[
        ["/quays/:quayId/berths/:berthId", "/quays/north/berths/12"],
        ["/files/*", "/files/a/b.txt"],
        ["/quays/:id", "/quays"],
        ["/health", "/health"],
        ["/health", "/health/"],
        ["/health", "/Health"],
        ["/quays/:id", "/quays/north/extra"],
        ["/quays/:id?", "/quays"],
        ["/quays/:id?", "/quays/north"],
        ["/quays/:id?", "/quays/north/extra"],
        ["/files/*", "/files"],
        ["*", "/anything/at/all"],
        ["/", "/"],
        ["/", "/x"],
        ["/a/:x/c", "/a//b/c"],
        ["/users/:id/posts", "/users/42/comments"],
        ["/:lang/docs/*", "/en/docs/guide/intro"],
        ["/quays/:id", "/berths/north"],
    ],
    wrong_solutions=[
        '''function matchRoute(pattern, path) {
  const want = pattern.split("/").filter(Boolean), have = path.split("/").filter(Boolean);
  const params = {};
  for (let i = 0; i < want.length; i++) {
    if (want[i] === "*") { params["*"] = have.slice(i).join("/"); return params; }
    if (want[i].startsWith(":")) params[want[i].slice(1).replace("?", "")] = have[i];
    else if (want[i] !== have[i]) return null;
  }
  return params;
}
''',
        '''function matchRoute(pattern, path) {
  const want = pattern.split("/").filter(Boolean), have = path.split("/").filter(Boolean);
  if (want.length !== have.length) return null;
  const params = {};
  for (let i = 0; i < want.length; i++) {
    if (want[i].startsWith(":")) params[want[i].slice(1)] = have[i];
    else if (want[i] !== have[i]) return null;
  }
  return params;
}
''',
    ],
    guide=G(
        prereqs="Template literal types and the `RouteParams` example (*Type operations*); route parameters in Express "
                "(*Typing React and Express*).",
        intuition="A route is a list of segments. Walk the pattern and the path side by side: text must be equal, a `:name` "
                  "takes whatever is there and remembers it. The two special endings decide how the lengths may differ.",
        hints=["Normalise both strings with `split(\"/\")` and drop empty parts.",
               "Handle `*` and `:name?` first inside the loop, and only when they are the last pattern segment; each returns "
               "immediately.",
               "After the loop the path must have no segments left over."],
        brute_force="Convert the pattern to a regular expression (`:name` → `([^/]+)`, `*` → `(.*)`) and run it. It is the approach "
                    "of many routers and is equally fast, but escaping literal text correctly and naming the captures takes care.",
        approach="Segment-by-segment comparison with early exits.\n\n"
                 "**Dry run**: pattern `/quays/:id?`, path `/quays/north/extra`. Segments `[quays, :id?]` and "
                 "`[quays, north, extra]`. `quays` equals `quays`. `:id?` is last and optional: the path has more than one "
                 "segment left (length 3 > 2) → `null`. With the path `/quays` the length equals `i` (1), so nothing is captured "
                 "and `{}` is returned.",
        complexity="Time and space O(length of pattern + length of path).",
        pitfalls="Returning a match when the path is longer than the pattern. Storing `undefined` for an absent optional "
                 "parameter instead of omitting the key. Treating matching as case-insensitive.",
        follow_up="Decode captured values with `decodeURIComponent`, and write the TypeScript type that derives "
                  "`{ quayId: string; berthId: string }` from the pattern literal.",
    ),
),
# ------------------------------------------------------------------ 21
dict(
    id="ts-combine-object-types", title="Union and intersection of object types", difficulty="Medium",
    pattern="Type operations", kind="js", entry="combine",
    description=r"""
`A | B` and `A & B` do opposite things to the **properties** you may use, which regularly confuses people:

- on a union `A | B` you can only read properties that exist in **both**, and each has the union of the two types;
- an intersection `A & B` has the properties of **either**, and a shared property has the intersection of the two types.

Model it. An object type is described as a map from property name to a list of type names (the list is a union, for
example `["string", "number"]` means `string | number`).

Write `combine(op, a, b)`:

- `op === "union"`: the result contains only the keys present in both `a` and `b`. Each maps to all names from either
  list, without duplicates.
- `op === "intersection"`: the result contains every key of `a` and of `b`. A key in only one of them keeps its list.
  A shared key maps to the names found in **both** lists; if there are none, it maps to `["never"]`.

Every list in the result is sorted alphabetically.

**Examples:** `combine("union", {"id": ["number"], "name": ["string"]}, {"id": ["string"], "age": ["number"]})` →
`{"id": ["number", "string"]}` · the same with `"intersection"` →
`{"id": ["never"], "name": ["string"], "age": ["number"]}`
""",
    starter='''/**
 * @param {"union" | "intersection"} op
 * @param {Record<string, string[]>} a
 * @param {Record<string, string[]>} b
 * @returns {Record<string, string[]>}
 */
function combine(op, a, b) {
  // your code
}
''',
    solution='''function combine(op, a, b) {
  const has = (obj, key) => Object.prototype.hasOwnProperty.call(obj, key);
  const unique = (list) => [...new Set(list)].sort();
  const out = {};
  if (op === "union") {
    for (const key of Object.keys(a)) {
      if (has(b, key)) out[key] = unique([...a[key], ...b[key]]);
    }
    return out;
  }
  for (const key of [...Object.keys(a), ...Object.keys(b)]) {
    if (has(out, key)) continue;
    if (has(a, key) && has(b, key)) {
      const shared = unique(a[key].filter((name) => b[key].includes(name)));
      out[key] = shared.length > 0 ? shared : ["never"];
    } else {
      out[key] = unique(has(a, key) ? a[key] : b[key]);
    }
  }
  return out;
}
''',
    tests=[
        ["union", {"id": ["number"], "name": ["string"]}, {"id": ["string"], "age": ["number"]}],
        ["intersection", {"id": ["number"], "name": ["string"]}, {"id": ["string"], "age": ["number"]}],
        ["union", {}, {"a": ["string"]}],
        ["intersection", {}, {"a": ["string"]}],
        ["union", {"a": ["string"]}, {"a": ["string"]}],
        ["intersection", {"a": ["string", "number"]}, {"a": ["number", "boolean"]}],
        ["union", {"a": ["string", "number"]}, {"a": ["number", "boolean"]}],
        ["intersection", {"z": ["string", "null"], "y": ["undefined", "boolean"]}, {"z": ["null", "string"]}],
        ["union", {"kind": ["circle"], "radius": ["number"]}, {"kind": ["rect"], "width": ["number"]}],
        ["intersection", {"kind": ["circle"], "radius": ["number"]}, {"kind": ["rect"], "width": ["number"]}],
        ["union", {}, {}],
        ["intersection", {"a": ["string", "string", "number"]}, {"b": ["zeta", "alpha"]}],
        ["union", {"x": ["b", "a"], "y": ["c"]}, {"y": ["c", "a"], "x": ["a"]}],
    ],
    wrong_solutions=[
        # swapped: union keeps all keys
        '''function combine(op, a, b) {
  const unique = (l) => [...new Set(l)].sort();
  const out = {};
  for (const key of [...Object.keys(a), ...Object.keys(b)]) {
    if (key in a && key in b) {
      if (op === "union") out[key] = unique([...a[key], ...b[key]]);
      else { const s = unique(a[key].filter((n) => b[key].includes(n))); out[key] = s.length ? s : ["never"]; }
    } else out[key] = unique(a[key] ?? b[key]);
  }
  return out;
}
''',
        # intersection of disjoint lists gives [] instead of never
        '''function combine(op, a, b) {
  const unique = (l) => [...new Set(l)].sort();
  const out = {};
  if (op === "union") { for (const k of Object.keys(a)) if (k in b) out[k] = unique([...a[k], ...b[k]]); return out; }
  for (const k of [...Object.keys(a), ...Object.keys(b)]) {
    if (k in a && k in b) out[k] = unique(a[k].filter((n) => b[k].includes(n)));
    else out[k] = unique(a[k] ?? b[k]);
  }
  return out;
}
''',
    ],
    guide=G(
        prereqs="Unions and intersections of object types (*Objects and structural typing*); `never` (*Type operations*).",
        intuition="Think in sets of *values*. A union has more values, so fewer properties are guaranteed: only the shared ones. "
                  "An intersection has fewer values, each of which must satisfy both descriptions: all properties, and shared "
                  "ones must satisfy both types at once.",
        hints=["For the union loop over one object's keys and keep those the other has.",
               "For the intersection loop over both key lists; treat shared and unshared keys separately.",
               "An empty overlap is the type `never`, written here as `[\"never\"]`."],
        brute_force="Nested loops over both key lists, comparing names. O(n × m) and correct; own-property lookups make it "
                    "linear in the number of keys.",
        approach="Two branches on `op`, with a small `unique` helper that removes duplicates and sorts.\n\n"
                 "**Dry run** (intersection) on `a = {id: [number], name: [string]}`, `b = {id: [string], age: [number]}`. "
                 "`id` is shared: common names of `[number]` and `[string]` → none → `[never]`. `name` only in `a` → `[string]`. "
                 "`age` only in `b` → `[number]`. This is the lesson's warning made visible: intersecting conflicting property "
                 "types silently produces `never`.",
        complexity="Time O(total number of type names × list length), space proportional to the output.",
        pitfalls="Mixing the two up (keeping all keys for a union). Returning an empty list where `never` is meant. Forgetting to "
                 "sort or to remove duplicates.",
        follow_up="A discriminated union is the case where the shared key (`kind`) has different single literals in each "
                  "member. What does `combine(\"union\", ...)` give for it, and why is that useful for narrowing?",
    ),
),
# ------------------------------------------------------------------ 22
dict(
    id="ts-print-type", title="Type descriptor pretty-printer", difficulty="Medium",
    pattern="Type operations", kind="js", entry="printType",
    description=r"""
Editors show types as text when you hover. Write the function that turns a type **descriptor** into TypeScript syntax.

`printType(type)` returns a string. Descriptors:

| descriptor | prints as |
|---|---|
| a string such as `"string"`, `"number"`, `"unknown"` | itself |
| `{"kind": "literal", "value": v}` | strings with double quotes via `JSON.stringify`; numbers and booleans as they are |
| `{"kind": "array", "element": T}` | `T[]`; if `T` is a union or a function, wrap it: `(A | B)[]` |
| `{"kind": "tuple", "elements": [T, ...]}` | `[A, B]`; empty tuple is `[]` |
| `{"kind": "object", "props": [{"name", "type", "optional"?}, ...]}` | `{ a: A; b?: B }`; no properties prints `{}` |
| `{"kind": "union", "members": [T, ...]}` | members joined with `" | "`; a function member is wrapped in parentheses; an empty union prints `never` |
| `{"kind": "function", "params": [{"name", "type", "optional"?}, ...], "returns": T}` | `(a: A, b?: B) => R` |

Properties and parameters are printed in the order given. Nested types are printed recursively with the same rules.

**Examples:** `printType({"kind":"array","element":{"kind":"union","members":["string","number"]}})` → `"(string | number)[]"` ·
`printType({"kind":"object","props":[{"name":"id","type":"number"},{"name":"tag","type":"string","optional":true}]})` →
`"{ id: number; tag?: string }"`
""",
    starter='''/**
 * @param {unknown} type  a type descriptor
 * @returns {string}
 */
function printType(type) {
  // your code
}
''',
    solution='''function printType(type) {
  if (typeof type === "string") return type;
  const named = (item) => item.name + (item.optional ? "?" : "") + ": " + printType(item.type);
  switch (type.kind) {
    case "literal":
      return typeof type.value === "string" ? JSON.stringify(type.value) : String(type.value);
    case "array": {
      const inner = printType(type.element);
      const wrap = typeof type.element === "object" && (type.element.kind === "union" || type.element.kind === "function");
      return (wrap ? "(" + inner + ")" : inner) + "[]";
    }
    case "tuple":
      return "[" + type.elements.map(printType).join(", ") + "]";
    case "object":
      return type.props.length === 0 ? "{}" : "{ " + type.props.map(named).join("; ") + " }";
    case "union":
      if (type.members.length === 0) return "never";
      return type.members
        .map((m) => (typeof m === "object" && m.kind === "function" ? "(" + printType(m) + ")" : printType(m)))
        .join(" | ");
    case "function":
      return "(" + type.params.map(named).join(", ") + ") => " + printType(type.returns);
    default:
      throw new Error("Unknown descriptor kind: " + type.kind);
  }
}
''',
    tests=[
        [A(U("string", "number"))],
        [O([P("id", "number"), P("tag", "string", True)])],
        ["unknown"],
        [L("north")],
        [L(42)],
        [L(False)],
        [A("string")],
        [A(A("number"))],
        [T("number", "number")],
        [T()],
        [O([])],
        [U()],
        [U(L("a"), L("b"), "null")],
        [F([P("a", "number"), P("b", "string", True)], "void")],
        [F([], A(U("string", "undefined")))],
        [U(F([], "void"), "undefined")],
        [A(F([P("x", "number")], "number"))],
        [O([P("pos", O([P("lat", "number"), P("lon", "number")])), P("tags", A("string")), P("on", F([P("e", "string")], "void"), True)])],
        [T("string", A(U(L(1), L(2))), O([P("k", "boolean")]))],
        [L('say "hi"')],
        [F([P("cb", F([P("err", U("Error", "null"))], "void"))], U("Promise", "void"))],
    ],
    wrong_solutions=[
        # no parentheses anywhere
        '''function printType(type) {
  if (typeof type === "string") return type;
  const named = (i) => i.name + (i.optional ? "?" : "") + ": " + printType(i.type);
  switch (type.kind) {
    case "literal": return typeof type.value === "string" ? JSON.stringify(type.value) : String(type.value);
    case "array": return printType(type.element) + "[]";
    case "tuple": return "[" + type.elements.map(printType).join(", ") + "]";
    case "object": return type.props.length === 0 ? "{}" : "{ " + type.props.map(named).join("; ") + " }";
    case "union": return type.members.length === 0 ? "never" : type.members.map(printType).join(" | ");
    case "function": return "(" + type.params.map(named).join(", ") + ") => " + printType(type.returns);
  }
}
''',
        # single quotes for strings, empty union/object not special-cased
        '''function printType(type) {
  if (typeof type === "string") return type;
  const named = (i) => i.name + (i.optional ? "?" : "") + ": " + printType(i.type);
  const paren = (t) => (typeof t === "object" && (t.kind === "union" || t.kind === "function") ? "(" + printType(t) + ")" : printType(t));
  switch (type.kind) {
    case "literal": return typeof type.value === "string" ? "'" + type.value + "'" : String(type.value);
    case "array": return paren(type.element) + "[]";
    case "tuple": return "[" + type.elements.map(printType).join(", ") + "]";
    case "object": return "{ " + type.props.map(named).join("; ") + " }";
    case "union": return type.members.map((m) => (typeof m === "object" && m.kind === "function" ? "(" + printType(m) + ")" : printType(m))).join(" | ");
    case "function": return "(" + type.params.map(named).join(", ") + ") => " + printType(type.returns);
  }
}
''',
    ],
    guide=G(
        prereqs="Type syntax for arrays, tuples, objects, unions and functions; why `(A | B)[]` needs parentheses "
                "(*Functions, arrays and tuples*).",
        intuition="A descriptor is a tree, and printing a tree is recursion: print the children, then glue them together with "
                  "the punctuation of the parent. Parentheses are needed exactly where the parent's punctuation binds tighter "
                  "than the child's: `[]` binds tighter than `|` and `=>`.",
        hints=["Strings are the base case.", "A helper that prints `name?: type` serves both object properties and parameters.",
               "Decide about parentheses in the *parent* (array or union), by looking at the child's `kind`."],
        brute_force="Wrap every nested type in parentheses. The output is unambiguous and unreadable: `((string) | (number))[]`. "
                    "The tests expect minimal parentheses.",
        approach="A `switch` on `kind` with one line per case.\n\n"
                 "**Dry run**: array of union `string | number`. The element prints as `string | number`. The parent is an array "
                 "and the child is a union → wrap → `(string | number)` + `[]`. Without the wrap the text would read as "
                 "`string | number[]`, a different type.",
        complexity="Time and space O(size of the descriptor).",
        pitfalls="Missing parentheses change the meaning. `() => void | undefined` is a function returning a union, so a function "
                 "inside a union must be wrapped. Empty object and empty union have special spellings. Quotes inside string "
                 "literals must be escaped, which `JSON.stringify` does.",
        follow_up="Print long object types across several lines with indentation, as editors do, or parse the text back into a "
                  "descriptor.",
    ),
),
]
