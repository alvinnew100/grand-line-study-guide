"""TypeScript track, Part I problems: type guards, narrowing, assignability, discriminated unions."""


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


S, N, B = "string", "number", "boolean"


def lit(v):
    return {"literal": v}


def L(v):
    return {"kind": "literal", "value": v}


def A(e):
    return {"kind": "array", "element": e}


def U(*m):
    return {"kind": "union", "members": list(m)}


def O(**props):
    out = {}
    for k, v in props.items():
        if k.endswith("_opt"):
            out[k[:-4]] = {"type": v, "optional": True}
        else:
            out[k] = {"type": v}
    return {"kind": "object", "props": out}


PROBLEMS = [
# ------------------------------------------------------------------ 1
dict(
    id="ts-partition-by-type", title="Partition values by runtime type", difficulty="Easy",
    pattern="Type guards", kind="js", entry="partitionByType",
    description=r"""
A value typed `unknown` must be inspected before it can be used. Practise the basic runtime checks by sorting a mixed
list into buckets.

Write `partitionByType(values)`. `values` is an array of JSON values. Return an object with exactly these keys:

| key | contains |
|---|---|
| `strings` | every string, in original order |
| `numbers` | every number |
| `booleans` | every boolean |
| `arrays` | every array (not searched inside) |
| `objects` | every plain object, that is: not `null` and not an array |
| `nullCount` | how many `null` values were seen (a number) |

Remember the two famous irregularities: `typeof null` is `"object"`, and `typeof []` is `"object"` too.

**Example:** `partitionByType(["a", 1, null, [2], {"k": true}, false])` →
`{"strings":["a"],"numbers":[1],"booleans":[false],"arrays":[[2]],"objects":[{"k":true}],"nullCount":1}`
""",
    starter='''/**
 * @param {unknown[]} values
 * @returns {{ strings: string[], numbers: number[], booleans: boolean[], arrays: unknown[][], objects: object[], nullCount: number }}
 */
function partitionByType(values) {
  // your code
}
''',
    solution='''function partitionByType(values) {
  const out = { strings: [], numbers: [], booleans: [], arrays: [], objects: [], nullCount: 0 };
  for (const v of values) {
    if (v === null) out.nullCount++;
    else if (Array.isArray(v)) out.arrays.push(v);
    else if (typeof v === "string") out.strings.push(v);
    else if (typeof v === "number") out.numbers.push(v);
    else if (typeof v === "boolean") out.booleans.push(v);
    else if (typeof v === "object") out.objects.push(v);
  }
  return out;
}
''',
    tests=[
        [["a", 1, None, [2], {"k": True}, False]],
        [[]],
        [[None, None, None]],
        [["", 0, False]],
        [[[], {}, [[]], [{}]]],
        [[1, 2.5, -3, "4"]],
        [[{"a": None}, [None], None]],
        [["x", "y", True, True, 7]],
        [[{"length": 2}, [1, 2]]],
        [[0, "", None, [], {}, False, "end"]],
        [[["a", "b"], "a", ["c"]]],
    ],
    wrong_solutions=[
        '''function partitionByType(values) {
  const out = { strings: [], numbers: [], booleans: [], arrays: [], objects: [], nullCount: 0 };
  for (const v of values) {
    if (typeof v === "string") out.strings.push(v);
    else if (typeof v === "number") out.numbers.push(v);
    else if (typeof v === "boolean") out.booleans.push(v);
    else if (typeof v === "object") out.objects.push(v);
  }
  return out;
}
''',
        '''function partitionByType(values) {
  const out = { strings: [], numbers: [], booleans: [], arrays: [], objects: [], nullCount: 0 };
  for (const v of values) {
    if (!v) { out.nullCount++; continue; }
    if (Array.isArray(v)) out.arrays.push(v);
    else if (typeof v === "string") out.strings.push(v);
    else if (typeof v === "number") out.numbers.push(v);
    else if (typeof v === "boolean") out.booleans.push(v);
    else out.objects.push(v);
  }
  return out;
}
''',
    ],
    guide=G(
        prereqs="`typeof`, `Array.isArray` and `=== null` from the lesson *Unions, literals and narrowing*.",
        intuition="Each bucket corresponds to one type guard. The only trick is the order of the checks: `null` and arrays "
                  "both answer `\"object\"` to `typeof`, so they must be picked out before the general object check.",
        hints=["Start with an object holding five empty arrays and a counter.",
               "Test `v === null` first, then `Array.isArray(v)`.",
               "Only after those two does `typeof v === \"object\"` mean a plain object."],
        brute_force="Filter the list six times, once per bucket. That is correct and O(6n); a single pass with an if/else chain "
                    "does the same work in one loop.",
        approach="Loop once. For each value run the guards from most specific to least: null, array, string, number, boolean, object.\n\n"
                 "**Dry run** on `[\"a\", null, [2]]`: `\"a\"` is not null, not an array, `typeof` is string → `strings`. "
                 "`null` hits the first test → `nullCount` becomes 1. `[2]` is not null, is an array → `arrays`. "
                 "Result: `strings: [\"a\"], arrays: [[2]], nullCount: 1`, other buckets empty.",
        complexity="Time O(n), space O(n) for the output.",
        pitfalls="Using truthiness to detect null also catches `0`, `\"\"` and `false`. Checking `typeof v === \"object\"` first "
                 "puts null and arrays in the wrong bucket.",
        follow_up="Add a `Date` bucket using `instanceof`, and think about why its check must also come before the object check.",
    ),
),
# ------------------------------------------------------------------ 2
dict(
    id="ts-is-user", title="Type guard: is this a User?", difficulty="Easy",
    pattern="Type guards", kind="js", entry="isUser",
    description=r"""
In TypeScript the function you are about to write would be declared as a **type predicate**:

```typescript
interface User { id: number; name: string; email?: string; roles?: string[] }
function isUser(value: unknown): value is User
```

The checker trusts a predicate without verifying its body, so the body has to be right. Write `isUser(value)` returning
`true` only when **all** of these hold:

1. `value` is an object, not `null` and not an array.
2. `value.id` is a number, an integer, and at least 1.
3. `value.name` is a string containing at least one non-space character.
4. If the key `email` is present, it is a string containing the character `@`.
5. If the key `roles` is present, it is an array whose every element is a string (an empty array is fine).

Extra properties are allowed (structural typing). A key that is present with a wrong value (for example `email: null`)
makes the result `false`.

**Examples:** `isUser({"id": 7, "name": "Asha"})` → `true` · `isUser({"id": "7", "name": "Asha"})` → `false` · `isUser(null)` → `false`
""",
    starter='''/**
 * @param {unknown} value
 * @returns {boolean}  in TypeScript: `value is User`
 */
function isUser(value) {
  // your code
}
''',
    solution='''function isUser(value) {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return false;
  if (typeof value.id !== "number" || !Number.isInteger(value.id) || value.id < 1) return false;
  if (typeof value.name !== "string" || value.name.trim() === "") return false;
  if ("email" in value) {
    if (typeof value.email !== "string" || !value.email.includes("@")) return false;
  }
  if ("roles" in value) {
    if (!Array.isArray(value.roles) || !value.roles.every((r) => typeof r === "string")) return false;
  }
  return true;
}
''',
    tests=[
        [{"id": 7, "name": "Asha"}],
        [{"id": "7", "name": "Asha"}],
        [None],
        [[{"id": 1, "name": "x"}]],
        [{"id": 1, "name": "Tobin", "email": "tobin@example.org", "roles": ["crew"]}],
        [{"id": 1, "name": "Tobin", "email": ""}],
        [{"id": 1, "name": "Tobin", "email": None}],
        [{"id": 1, "name": "   "}],
        [{"id": 0, "name": "Zero"}],
        [{"id": 2.5, "name": "Half"}],
        [{"id": 3, "name": "Lior", "roles": []}],
        [{"id": 3, "name": "Lior", "roles": ["crew", 5]}],
        [{"id": 3, "name": "Lior", "roles": "crew"}],
        [{"id": 4, "name": "Extra", "age": 30, "active": True}],
        ["Asha"],
        [{"name": "No id"}],
    ],
    wrong_solutions=[
        '''function isUser(value) {
  if (typeof value !== "object") return false;
  if (typeof value.id !== "number" || !Number.isInteger(value.id) || value.id < 1) return false;
  if (typeof value.name !== "string" || value.name.trim() === "") return false;
  if ("email" in value && (typeof value.email !== "string" || !value.email.includes("@"))) return false;
  if ("roles" in value && (!Array.isArray(value.roles) || !value.roles.every((r) => typeof r === "string"))) return false;
  return true;
}
''',
        '''function isUser(value) {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return false;
  if (typeof value.id !== "number" || !Number.isInteger(value.id) || value.id < 1) return false;
  if (typeof value.name !== "string" || value.name.trim() === "") return false;
  if (value.email && (typeof value.email !== "string" || !value.email.includes("@"))) return false;
  if (value.roles && (!Array.isArray(value.roles) || !value.roles.every((r) => typeof r === "string"))) return false;
  return true;
}
''',
        '''function isUser(value) {
  return typeof value === "object" && value !== null && typeof value.id === "number" && typeof value.name === "string";
}
''',
    ],
    guide=G(
        prereqs="Type predicates (lesson *Type modifiers*), optional properties (lesson *Objects and structural typing*).",
        intuition="A guard is a list of ways the data could be wrong, each ruled out in turn. Required fields are checked "
                  "unconditionally. Optional fields are checked only when the key exists, and existence is asked with `in`, "
                  "not with truthiness.",
        hints=["Handle `null` and arrays before touching any property.",
               "`Number.isInteger` rejects both non-numbers and fractions.",
               "For an optional field write `if (\"email\" in value) { ...validate... }`. An empty string is present and invalid."],
        brute_force="There is no cheaper or dearer algorithm here; the naive version is the one that checks only `id` and `name` "
                    "with `typeof` and accepts fractional ids, blank names and malformed optional fields.",
        approach="Return `false` as soon as any rule fails; return `true` at the end.\n\n"
                 "**Dry run** on `{id: 1, name: \"Tobin\", email: \"\"}`: it is a non-null, non-array object; `id` is the integer 1; "
                 "`name` trimmed is non-empty; the key `email` is present, it is a string, but it does not contain `@` → `false`. "
                 "A truthiness test (`if (value.email && ...)`) would have skipped the check because `\"\"` is falsy and wrongly "
                 "returned `true`.",
        complexity="Time O(k) where k is the number of roles; space O(1).",
        pitfalls="`typeof null === \"object\"` makes `value.id` throw if null is not excluded. Arrays are objects. "
                 "`0`, `\"\"` and `null` are falsy, so truthiness cannot tell *absent* from *present but wrong*.",
        follow_up="Return a list of reasons instead of a boolean, which is the step from a type guard to a schema validator.",
    ),
),
# ------------------------------------------------------------------ 3
dict(
    id="ts-narrow-union", title="Narrowing simulator", difficulty="Medium",
    pattern="Narrowing", kind="js", entry="narrow",
    description=r"""
Simulate what the type checker does when it meets an `if`. You are given a union as a list of **members** and one
**check**; return the members that remain in the true branch and in the false branch.

A member is either a type name, one of `"string"`, `"number"`, `"boolean"`, `"bigint"`, `"symbol"`, `"undefined"`, `"null"`,
`"object"`, `"array"`, `"function"`, or a literal written as `{"literal": value}` where value is a string, number or boolean.

Write `narrow(members, check)` returning `{"whenTrue": [...], "whenFalse": [...]}`. Keep members in their original order.

**Checks**

- `{"kind": "typeof", "value": T}` models `typeof x === T`. The runtime `typeof` of a member is its own name, except
  `"null"` → `"object"` and `"array"` → `"object"`; for a literal it is the `typeof` of its value. True branch: members
  whose `typeof` equals `T`. False branch: the others.
- `{"kind": "isArray"}` models `Array.isArray(x)`. True branch: `"array"` only. False branch: the others.
- `{"kind": "truthy"}` models `if (x)`.
  True branch: everything except `"null"`, `"undefined"` and falsy literals (`false`, `0`, `""`).
  False branch: `"null"`, `"undefined"`, the wide primitives that have a falsy value (`"string"`, `"number"`, `"boolean"`,
  `"bigint"`) and falsy literals. (`"object"`, `"array"`, `"function"`, `"symbol"` and truthy literals are never falsy.)
- `{"kind": "equals", "value": V}` models `x === V`, where `V` is a string, number, boolean or `null`.
  If `V` is `null`: true branch is `"null"` only (if present), false branch is everything else.
  Otherwise, true branch: the literal member equal to `V`, and a wide member whose name is `typeof V` is **replaced by**
  `{"literal": V}`; if that produces the same literal twice keep only the first. False branch: every member except the
  literal equal to `V` (wide members stay, since they could hold other values).

**Example:** `narrow(["string", "number", "null"], {"kind": "typeof", "value": "object"})` →
`{"whenTrue": ["null"], "whenFalse": ["string", "number"]}`
""",
    starter='''/**
 * @typedef {string | { literal: string | number | boolean }} Member
 * @param {Member[]} members
 * @param {{ kind: "typeof", value: string } | { kind: "isArray" } | { kind: "truthy" } | { kind: "equals", value: string | number | boolean | null }} check
 * @returns {{ whenTrue: Member[], whenFalse: Member[] }}
 */
function narrow(members, check) {
  // your code
}
''',
    solution='''function narrow(members, check) {
  const isLit = (m) => typeof m === "object" && m !== null;
  const typeofOf = (m) => (isLit(m) ? typeof m.literal : m === "null" || m === "array" ? "object" : m);
  const whenTrue = [];
  const whenFalse = [];
  if (check.kind === "typeof") {
    for (const m of members) (typeofOf(m) === check.value ? whenTrue : whenFalse).push(m);
  } else if (check.kind === "isArray") {
    for (const m of members) (m === "array" ? whenTrue : whenFalse).push(m);
  } else if (check.kind === "truthy") {
    const canBeFalsy = ["null", "undefined", "string", "number", "boolean", "bigint"];
    for (const m of members) {
      if (isLit(m)) (m.literal ? whenTrue : whenFalse).push(m);
      else {
        if (m !== "null" && m !== "undefined") whenTrue.push(m);
        if (canBeFalsy.includes(m)) whenFalse.push(m);
      }
    }
  } else if (check.kind === "equals") {
    const v = check.value;
    if (v === null) {
      for (const m of members) (m === "null" ? whenTrue : whenFalse).push(m);
    } else {
      let added = false;
      for (const m of members) {
        if (isLit(m)) {
          if (m.literal === v) { if (!added) { whenTrue.push(m); added = true; } }
          else whenFalse.push(m);
        } else {
          if (m === typeof v && !added) { whenTrue.push({ literal: v }); added = true; }
          whenFalse.push(m);
        }
      }
    }
  }
  return { whenTrue, whenFalse };
}
''',
    tests=[
        [[S, N, "null"], {"kind": "typeof", "value": "object"}],
        [[S, N, "null"], {"kind": "typeof", "value": "string"}],
        [[S, "undefined"], {"kind": "truthy"}],
        [[N, "null", "object"], {"kind": "truthy"}],
        [[S, "array"], {"kind": "isArray"}],
        [[lit("low"), lit("high"), N], {"kind": "equals", "value": "low"}],
        [[S, N], {"kind": "equals", "value": "a"}],
        [[S, lit("a"), N], {"kind": "equals", "value": "a"}],
        [[S, "null", "undefined"], {"kind": "equals", "value": None}],
        [[lit(0), lit(1), lit(""), lit("x"), lit(False), lit(True)], {"kind": "truthy"}],
        [["object", "array", "function", "null"], {"kind": "typeof", "value": "object"}],
        [[lit("a"), lit(1), B], {"kind": "typeof", "value": "number"}],
        [[], {"kind": "truthy"}],
        [["symbol", "bigint", "function"], {"kind": "truthy"}],
        [[lit(1), lit(2)], {"kind": "equals", "value": 3}],
        [[B, "undefined"], {"kind": "equals", "value": True}],
    ],
    wrong_solutions=[
        # forgets typeof null / array is "object"
        '''function narrow(members, check) {
  const isLit = (m) => typeof m === "object" && m !== null;
  const typeofOf = (m) => (isLit(m) ? typeof m.literal : m);
  const whenTrue = [], whenFalse = [];
  if (check.kind === "typeof") for (const m of members) (typeofOf(m) === check.value ? whenTrue : whenFalse).push(m);
  else if (check.kind === "isArray") for (const m of members) (m === "array" ? whenTrue : whenFalse).push(m);
  else if (check.kind === "truthy") {
    const canBeFalsy = ["null", "undefined", "string", "number", "boolean", "bigint"];
    for (const m of members) {
      if (isLit(m)) (m.literal ? whenTrue : whenFalse).push(m);
      else { if (m !== "null" && m !== "undefined") whenTrue.push(m); if (canBeFalsy.includes(m)) whenFalse.push(m); }
    }
  } else {
    const v = check.value;
    if (v === null) for (const m of members) (m === "null" ? whenTrue : whenFalse).push(m);
    else { let added = false; for (const m of members) {
      if (isLit(m)) { if (m.literal === v) { if (!added) { whenTrue.push(m); added = true; } } else whenFalse.push(m); }
      else { if (m === typeof v && !added) { whenTrue.push({ literal: v }); added = true; } whenFalse.push(m); } } }
  }
  return { whenTrue, whenFalse };
}
''',
        # truthy: false branch is only null/undefined (forgets "" and 0)
        '''function narrow(members, check) {
  const isLit = (m) => typeof m === "object" && m !== null;
  const typeofOf = (m) => (isLit(m) ? typeof m.literal : m === "null" || m === "array" ? "object" : m);
  const whenTrue = [], whenFalse = [];
  if (check.kind === "typeof") for (const m of members) (typeofOf(m) === check.value ? whenTrue : whenFalse).push(m);
  else if (check.kind === "isArray") for (const m of members) (m === "array" ? whenTrue : whenFalse).push(m);
  else if (check.kind === "truthy") {
    for (const m of members) {
      if (isLit(m)) (m.literal ? whenTrue : whenFalse).push(m);
      else if (m === "null" || m === "undefined") whenFalse.push(m);
      else whenTrue.push(m);
    }
  } else {
    const v = check.value;
    if (v === null) for (const m of members) (m === "null" ? whenTrue : whenFalse).push(m);
    else { let added = false; for (const m of members) {
      if (isLit(m)) { if (m.literal === v) { if (!added) { whenTrue.push(m); added = true; } } else whenFalse.push(m); }
      else { if (m === typeof v && !added) { whenTrue.push({ literal: v }); added = true; } whenFalse.push(m); } } }
  }
  return { whenTrue, whenFalse };
}
''',
        # equals: removes the wide member from the false branch
        '''function narrow(members, check) {
  const isLit = (m) => typeof m === "object" && m !== null;
  const typeofOf = (m) => (isLit(m) ? typeof m.literal : m === "null" || m === "array" ? "object" : m);
  const whenTrue = [], whenFalse = [];
  if (check.kind === "typeof") for (const m of members) (typeofOf(m) === check.value ? whenTrue : whenFalse).push(m);
  else if (check.kind === "isArray") for (const m of members) (m === "array" ? whenTrue : whenFalse).push(m);
  else if (check.kind === "truthy") {
    const canBeFalsy = ["null", "undefined", "string", "number", "boolean", "bigint"];
    for (const m of members) {
      if (isLit(m)) (m.literal ? whenTrue : whenFalse).push(m);
      else { if (m !== "null" && m !== "undefined") whenTrue.push(m); if (canBeFalsy.includes(m)) whenFalse.push(m); }
    }
  } else {
    const v = check.value;
    if (v === null) for (const m of members) (m === "null" ? whenTrue : whenFalse).push(m);
    else { let added = false; for (const m of members) {
      if (isLit(m)) { if (m.literal === v) { if (!added) { whenTrue.push(m); added = true; } } else whenFalse.push(m); }
      else if (m === typeof v) { if (!added) { whenTrue.push({ literal: v }); added = true; } }
      else whenFalse.push(m); } }
  }
  return { whenTrue, whenFalse };
}
''',
    ],
    guide=G(
        prereqs="The narrowing table in *Unions, literals and narrowing*: `typeof`, truthiness, equality, `Array.isArray`.",
        intuition="Narrowing is filtering. For every member ask two independent questions: *could a value of this member make the "
                  "check true?* and *could one make it false?* A wide type such as `string` can answer yes to both, so it may "
                  "appear in both branches.",
        hints=["Write a helper giving the runtime `typeof` of a member, with the two special cases.",
               "For the truthy check, treat literals (decided by their value) separately from names (decided by a fixed list).",
               "For equals, the wide member stays in the false branch and becomes a literal in the true branch; track whether "
               "the literal has already been added."],
        brute_force="Enumerate sample values for each member (for `string`: `\"\"` and `\"a\"`; for `number`: `0` and `1`, ...) and "
                    "actually evaluate the check on each sample. It works for a fixed member list but is longer than stating the "
                    "rules directly.",
        approach="Branch on `check.kind`, then loop over members once, pushing each to one or both result lists.\n\n"
                 "**Dry run**: `narrow([\"string\", {literal: \"a\"}, \"number\"], equals \"a\")`. `\"string\"` is the wide type of `\"a\"`: "
                 "push `{literal: \"a\"}` to `whenTrue`, mark added, and keep `\"string\"` in `whenFalse`. `{literal: \"a\"}` equals the "
                 "value but is already added, so it goes nowhere. `\"number\"` cannot equal `\"a\"` → `whenFalse`. "
                 "Result: `whenTrue: [{literal: \"a\"}]`, `whenFalse: [\"string\", \"number\"]`.",
        complexity="Time O(n), space O(n).",
        pitfalls="`typeof null` and `typeof []` are both `\"object\"`. The false branch of a truthiness check still contains `string` "
                 "and `number` because of `\"\"` and `0`. Removing a wide member after `x !== \"a\"` is wrong: other strings remain.",
        follow_up="Add an `in` check over object members described by their property lists, or chain several checks.",
    ),
),
# ------------------------------------------------------------------ 4
dict(
    id="ts-nullish-defaults", title="Apply defaults with ?? semantics", difficulty="Easy",
    pattern="Optional chaining & nullish coalescing", kind="js", entry="withDefaults",
    description=r"""
The operator `a ?? b` yields `b` only when `a` is `null` or `undefined`. The older idiom `a || b` also replaces `0`, `""`
and `false`, which is a classic source of bugs in configuration code.

Write `withDefaults(config, defaults)` that returns a **new** object:

- For each key in `defaults`: if `config` has no such key, or its value is `null`, use the default value.
- If both the config value and the default value are plain objects (not arrays, not null), apply the same rule
  recursively to them.
- Otherwise keep the config value, even when it is `0`, `""` or `false`.
- Keys that exist only in `config` are copied unchanged.
- If `config` itself is `null`, treat it as `{}`.

**Example:** `withDefaults({"volume": 0, "title": null}, {"volume": 50, "title": "untitled", "loop": true})` →
`{"volume": 0, "title": "untitled", "loop": true}`
""",
    starter='''/**
 * @param {Record<string, unknown> | null} config
 * @param {Record<string, unknown>} defaults
 * @returns {Record<string, unknown>}
 */
function withDefaults(config, defaults) {
  // your code
}
''',
    solution='''function withDefaults(config, defaults) {
  const isPlain = (v) => typeof v === "object" && v !== null && !Array.isArray(v);
  const source = config ?? {};
  const out = { ...source };
  for (const key of Object.keys(defaults)) {
    const current = source[key];
    const fallback = defaults[key];
    if (current === null || current === undefined) out[key] = fallback;
    else if (isPlain(current) && isPlain(fallback)) out[key] = withDefaults(current, fallback);
    else out[key] = current;
  }
  return out;
}
''',
    tests=[
        [{"volume": 0, "title": None}, {"volume": 50, "title": "untitled", "loop": True}],
        [{}, {"a": 1, "b": "x"}],
        [None, {"a": 1}],
        [{"name": "", "active": False, "count": 0}, {"name": "anon", "active": True, "count": 10}],
        [{"extra": 9}, {"a": 1}],
        [{"theme": {"size": 0}}, {"theme": {"size": 14, "colour": "navy"}, "wrap": True}],
        [{"theme": None}, {"theme": {"size": 14}}],
        [{"tags": []}, {"tags": ["a", "b"]}],
        [{"tags": None}, {"tags": ["a", "b"]}],
        [{"a": {"b": {"c": None}}}, {"a": {"b": {"c": 3, "d": 4}}}],
        [{"theme": "dark"}, {"theme": {"size": 14}}],
        [{"a": 1}, {}],
    ],
    wrong_solutions=[
        '''function withDefaults(config, defaults) {
  const isPlain = (v) => typeof v === "object" && v !== null && !Array.isArray(v);
  const source = config || {};
  const out = { ...source };
  for (const key of Object.keys(defaults)) {
    const current = source[key], fallback = defaults[key];
    if (isPlain(current) && isPlain(fallback)) out[key] = withDefaults(current, fallback);
    else out[key] = current || fallback;
  }
  return out;
}
''',
        '''function withDefaults(config, defaults) {
  return { ...defaults, ...(config ?? {}) };
}
''',
    ],
    guide=G(
        prereqs="`??` versus `||` from *Unions, literals and narrowing*; object spread.",
        intuition="There are exactly two *nullish* values, `null` and `undefined`. A default should replace those and nothing "
                  "else. Nested objects need the same treatment one level down, which is recursion.",
        hints=["Copy `config` first so keys without defaults survive.",
               "Compare with `=== null || === undefined` (or use `??`), never with `!value`.",
               "Recurse only when both sides are plain objects; arrays are replaced or kept as a whole."],
        brute_force="`{ ...defaults, ...config }` is the one-liner people reach for. It fails in two ways: an explicit `null` in the "
                    "config overwrites the default, and nested objects are replaced wholesale instead of merged.",
        approach="Start from a shallow copy of the config; walk the keys of `defaults` and decide per key.\n\n"
                 "**Dry run** with config `{theme: {size: 0}}` and defaults `{theme: {size: 14, colour: \"navy\"}, wrap: true}`. "
                 "Key `theme`: both plain objects → recurse; inside, `size` is `0` (not nullish) → keep `0`; `colour` missing → "
                 "`\"navy\"`. Key `wrap`: missing → `true`. Result `{theme: {size: 0, colour: \"navy\"}, wrap: true}`.",
        complexity="Time and space O(total number of keys in both objects).",
        pitfalls="`||` discards `0`, `\"\"` and `false`. `typeof [] === \"object\"`, so exclude arrays from the recursive case. "
                 "Mutating `config` instead of copying surprises callers.",
        follow_up="In TypeScript the return type could be written `T & Required<Pick<D, keyof D>>`; try expressing it.",
    ),
),
# ------------------------------------------------------------------ 5
dict(
    id="ts-is-assignable", title="Structural assignability checker", difficulty="Hard",
    pattern="Structural typing", kind="js", entry="isAssignable",
    description=r"""
Implement the heart of a type checker: *is a value of type `source` allowed where type `target` is expected?*
Types are given as plain **descriptors**:

| descriptor | meaning |
|---|---|
| `"string"`, `"number"`, `"boolean"`, `"null"`, `"undefined"` | primitives |
| `"any"`, `"unknown"`, `"never"` | the special types |
| `{"kind": "literal", "value": v}` | literal type; `v` is a string, number or boolean |
| `{"kind": "array", "element": T}` | `T[]` |
| `{"kind": "object", "props": {name: {"type": T, "optional": bool}}}` | object type (`optional` may be omitted, meaning required) |
| `{"kind": "union", "members": [T, ...]}` | `A | B | ...` |

Write `isAssignable(source, target)` returning a boolean. Apply these rules **in this order**; the first that matches decides:

1. `source` is `"never"` → `true`.
2. `source` is `"any"` → `true` unless `target` is `"never"`.
3. `target` is `"any"` or `"unknown"` → `true`.
4. `source` is a union → `true` only if **every** member is assignable to `target`.
5. `target` is a union → `true` if `source` is assignable to **some** member.
6. `source` is `"unknown"` → `false`. `target` is `"never"` → `false`.
7. Both are primitive names → `true` only if they are the same name.
8. `source` is a literal → assignable to an equal literal (same value, compared with `===`) and to the primitive name that
   equals `typeof value`; otherwise `false`.
9. Both are arrays → compare the element types (arrays are treated covariantly, as TypeScript does).
10. Both are objects → for every property of `target`: if `source` has it, the source property type must be assignable
    to the target property type, **and** an optional source property is not assignable to a required target property;
    if `source` lacks it, the target property must be optional. Extra source properties are fine.
11. Anything else → `false`.

**Examples:** `isAssignable({"kind":"literal","value":"north"}, "string")` → `true` ·
`isAssignable("string", {"kind":"literal","value":"north"})` → `false`
""",
    starter='''/**
 * @typedef {string
 *   | { kind: "literal", value: string | number | boolean }
 *   | { kind: "array", element: TypeDesc }
 *   | { kind: "object", props: Record<string, { type: TypeDesc, optional?: boolean }> }
 *   | { kind: "union", members: TypeDesc[] }} TypeDesc
 * @param {TypeDesc} source
 * @param {TypeDesc} target
 * @returns {boolean}
 */
function isAssignable(source, target) {
  // your code
}
''',
    solution='''function isAssignable(source, target) {
  const kind = (t) => (typeof t === "string" ? "name" : t.kind);
  if (source === "never") return true;
  if (source === "any") return target !== "never";
  if (target === "any" || target === "unknown") return true;
  if (kind(source) === "union") return source.members.every((m) => isAssignable(m, target));
  if (kind(target) === "union") return target.members.some((m) => isAssignable(source, m));
  if (source === "unknown") return false;
  if (target === "never") return false;
  if (kind(source) === "name" && kind(target) === "name") return source === target;
  if (kind(source) === "literal") {
    if (kind(target) === "literal") return source.value === target.value;
    if (kind(target) === "name") return typeof source.value === target;
    return false;
  }
  if (kind(source) === "array" && kind(target) === "array") return isAssignable(source.element, target.element);
  if (kind(source) === "object" && kind(target) === "object") {
    for (const name of Object.keys(target.props)) {
      const want = target.props[name];
      const have = Object.prototype.hasOwnProperty.call(source.props, name) ? source.props[name] : undefined;
      if (have === undefined) {
        if (!want.optional) return false;
        continue;
      }
      if (have.optional && !want.optional) return false;
      if (!isAssignable(have.type, want.type)) return false;
    }
    return true;
  }
  return false;
}
''',
    tests=[
        [L("north"), S],
        [S, L("north")],
        [L("a"), L("a")],
        [L(1), L("1")],
        [N, U(S, N)],
        [U(S, N), S],
        [U(L("a"), L("b")), S],
        [O(name=S, age=N), O(name=S)],
        [O(name=S), O(name=S, age=N)],
        [O(name=S), O(name=S, age_opt=N)],
        [O(name_opt=S), O(name=S)],
        [O(id=L(5)), O(id=N)],
        [O(id=S), O(id=N)],
        [A(L("x")), A(S)],
        [A(S), A(N)],
        ["any", "never"],
        ["any", S],
        ["never", S],
        ["unknown", S],
        [S, "unknown"],
        [S, "never"],
        ["null", U(S, "null")],
        ["undefined", "null"],
        [O(pos=O(lat=N, lon=N), tag=S), O(pos=O(lat=N))],
        [O(pos=O(lat=S)), O(pos=O(lat=N))],
        [A(O(a=N)), O(a=N)],
        [U(), S],
        [S, U()],
        [L(True), B],
        [U(O(kind=L("a"), x=N), O(kind=L("b"), y=N)), O(kind=S)],
    ],
    examples=3,
    wrong_solutions=[
        # objects compared by exact key set (nominal-ish / no width subtyping)
        '''function isAssignable(source, target) {
  const kind = (t) => (typeof t === "string" ? "name" : t.kind);
  if (source === "never") return true;
  if (source === "any") return target !== "never";
  if (target === "any" || target === "unknown") return true;
  if (kind(source) === "union") return source.members.every((m) => isAssignable(m, target));
  if (kind(target) === "union") return target.members.some((m) => isAssignable(source, m));
  if (source === "unknown" || target === "never") return false;
  if (kind(source) === "name" && kind(target) === "name") return source === target;
  if (kind(source) === "literal") {
    if (kind(target) === "literal") return source.value === target.value;
    return kind(target) === "name" && typeof source.value === target;
  }
  if (kind(source) === "array" && kind(target) === "array") return isAssignable(source.element, target.element);
  if (kind(source) === "object" && kind(target) === "object") {
    const a = Object.keys(source.props), b = Object.keys(target.props);
    return a.length === b.length && b.every((n) => source.props[n] && isAssignable(source.props[n].type, target.props[n].type));
  }
  return false;
}
''',
        # union source uses some instead of every
        '''function isAssignable(source, target) {
  const kind = (t) => (typeof t === "string" ? "name" : t.kind);
  if (source === "never") return true;
  if (source === "any") return target !== "never";
  if (target === "any" || target === "unknown") return true;
  if (kind(source) === "union") return source.members.some((m) => isAssignable(m, target));
  if (kind(target) === "union") return target.members.some((m) => isAssignable(source, m));
  if (source === "unknown" || target === "never") return false;
  if (kind(source) === "name" && kind(target) === "name") return source === target;
  if (kind(source) === "literal") {
    if (kind(target) === "literal") return source.value === target.value;
    return kind(target) === "name" && typeof source.value === target;
  }
  if (kind(source) === "array" && kind(target) === "array") return isAssignable(source.element, target.element);
  if (kind(source) === "object" && kind(target) === "object") {
    for (const n of Object.keys(target.props)) {
      const want = target.props[n], have = source.props[n];
      if (!have) { if (!want.optional) return false; continue; }
      if (have.optional && !want.optional) return false;
      if (!isAssignable(have.type, want.type)) return false;
    }
    return true;
  }
  return false;
}
''',
        # ignores optional flags
        '''function isAssignable(source, target) {
  const kind = (t) => (typeof t === "string" ? "name" : t.kind);
  if (source === "never") return true;
  if (source === "any") return target !== "never";
  if (target === "any" || target === "unknown") return true;
  if (kind(source) === "union") return source.members.every((m) => isAssignable(m, target));
  if (kind(target) === "union") return target.members.some((m) => isAssignable(source, m));
  if (source === "unknown" || target === "never") return false;
  if (kind(source) === "name" && kind(target) === "name") return source === target;
  if (kind(source) === "literal") {
    if (kind(target) === "literal") return source.value === target.value;
    return kind(target) === "name" && typeof source.value === target;
  }
  if (kind(source) === "array" && kind(target) === "array") return isAssignable(source.element, target.element);
  if (kind(source) === "object" && kind(target) === "object") {
    for (const n of Object.keys(target.props)) {
      const have = source.props[n];
      if (!have || !isAssignable(have.type, target.props[n].type)) return false;
    }
    return true;
  }
  return false;
}
''',
        # literal == instead of typed comparison, and literals assignable to any primitive
        '''function isAssignable(source, target) {
  const kind = (t) => (typeof t === "string" ? "name" : t.kind);
  if (source === "never") return true;
  if (source === "any") return true;
  if (target === "any" || target === "unknown") return true;
  if (kind(source) === "union") return source.members.every((m) => isAssignable(m, target));
  if (kind(target) === "union") return target.members.some((m) => isAssignable(source, m));
  if (source === "unknown" || target === "never") return false;
  if (kind(source) === "name" && kind(target) === "name") return source === target;
  if (kind(source) === "literal") {
    if (kind(target) === "literal") return source.value == target.value;
    return kind(target) === "name" && typeof source.value === target;
  }
  if (kind(source) === "array" && kind(target) === "array") return isAssignable(source.element, target.element);
  if (kind(source) === "object" && kind(target) === "object") {
    for (const n of Object.keys(target.props)) {
      const want = target.props[n], have = source.props[n];
      if (!have) { if (!want.optional) return false; continue; }
      if (have.optional && !want.optional) return false;
      if (!isAssignable(have.type, want.type)) return false;
    }
    return true;
  }
  return false;
}
''',
    ],
    guide=G(
        prereqs="The set model of types (*The type system*), structural typing and optional properties (*Objects and structural "
                "typing*), `any`/`unknown`/`never` (*Type modifiers*).",
        intuition="Assignability asks whether every value of the source is also a value of the target. Each rule is that one "
                  "question specialised: a union source needs *all* of its members to fit; a union target needs *one* member to "
                  "accept; an object source needs to supply everything the target requires.",
        hints=["Deal with the special names first; they short-circuit everything else.",
               "Handle a union on the source side before a union on the target side.",
               "For objects, loop over the *target's* properties, never the source's: extra source properties do not matter."],
        brute_force="Enumerate sample values of the source type and test each against the target. That works for literals and tiny "
                    "unions but cannot enumerate `string`, so a rule-based recursive comparison is the practical solution.",
        approach="A recursive function with the eleven rules as a chain of early returns.\n\n"
                 "**Dry run**: source `{name?: string}`, target `{name: string}`. Neither is special, neither is a union, both are "
                 "objects. Target property `name`: the source has it; the source's is optional while the target's is required → "
                 "`false`. (A value `{}` is a valid source but lacks the required `name`.)\n\n"
                 "**Second dry run**: source `\"a\" | \"b\"`, target `string`. Source is a union: is `\"a\"` assignable to `string`? "
                 "Literal, `typeof \"a\"` is `\"string\"` → yes. Same for `\"b\"` → `true`.",
        complexity="Time O(size of source × size of target) in the worst case because of unions; space O(depth) for recursion.",
        pitfalls="Checking the target union before the source union gives wrong answers for union-to-union. `any` is assignable to "
                 "everything except `never`. An empty union behaves like `never` as a source and accepts nothing as a target. "
                 "Using `==` for literals makes `1` equal `\"1\"`.",
        follow_up="Add function types with contravariant parameters (see the problem *Function assignability and variance*) and "
                  "excess property checking for a `fresh` flag on object descriptors.",
    ),
),
# ------------------------------------------------------------------ 6
dict(
    id="ts-cart-reducer", title="Discriminated-union reducer", difficulty="Medium",
    pattern="Discriminated unions", kind="js", entry="runCart",
    description=r"""
A shopping cart is driven by **actions**, objects tagged with a `type` property. In TypeScript:

```typescript
type Action =
  | { type: "add"; sku: string; qty?: number }
  | { type: "remove"; sku: string }
  | { type: "setQty"; sku: string; qty: number }
  | { type: "applyCoupon"; code: string }
  | { type: "clear" };
```

Write `runCart(actions)`. Start from the state `{ items: {}, coupon: null }` and apply the actions in order:

- `add`: increase `items[sku]` by `qty` (default `1` when `qty` is missing), creating the entry at that quantity if needed.
- `remove`: delete `items[sku]`; do nothing if it is not there.
- `setQty`: set `items[sku]` to `qty`; if `qty` is `0` or negative, delete the entry instead.
- `applyCoupon`: set `coupon` to `code` (a later coupon replaces an earlier one).
- `clear`: empty `items` and reset `coupon` to `null`.

Return `{ "items": ..., "coupon": ..., "totalQty": sum of all quantities }`.

If an action has any other `type`, stop immediately and return `{ "error": "Unhandled action: <type>" }`. This is the
runtime half of an exhaustiveness check.

**Example:** `runCart([{"type":"add","sku":"tea"},{"type":"add","sku":"tea","qty":2}])` →
`{"items":{"tea":3},"coupon":null,"totalQty":3}`
""",
    starter='''/**
 * @typedef {{ type: "add", sku: string, qty?: number }
 *   | { type: "remove", sku: string }
 *   | { type: "setQty", sku: string, qty: number }
 *   | { type: "applyCoupon", code: string }
 *   | { type: "clear" }} Action
 * @param {Action[]} actions
 */
function runCart(actions) {
  // your code
}
''',
    solution='''function runCart(actions) {
  function reduce(state, action) {
    switch (action.type) {
      case "add": {
        const qty = action.qty ?? 1;
        return { ...state, items: { ...state.items, [action.sku]: (state.items[action.sku] ?? 0) + qty } };
      }
      case "remove": {
        const items = { ...state.items };
        delete items[action.sku];
        return { ...state, items };
      }
      case "setQty": {
        const items = { ...state.items };
        if (action.qty <= 0) delete items[action.sku];
        else items[action.sku] = action.qty;
        return { ...state, items };
      }
      case "applyCoupon":
        return { ...state, coupon: action.code };
      case "clear":
        return { items: {}, coupon: null };
      default:
        throw new Error("Unhandled action: " + action.type);
    }
  }
  let state = { items: {}, coupon: null };
  try {
    for (const action of actions) state = reduce(state, action);
  } catch (err) {
    return { error: err.message };
  }
  const totalQty = Object.values(state.items).reduce((sum, n) => sum + n, 0);
  return { items: state.items, coupon: state.coupon, totalQty };
}
''',
    tests=[
        [[{"type": "add", "sku": "tea"}, {"type": "add", "sku": "tea", "qty": 2}]],
        [[]],
        [[{"type": "add", "sku": "tea", "qty": 4}, {"type": "remove", "sku": "tea"}]],
        [[{"type": "remove", "sku": "ghost"}]],
        [[{"type": "add", "sku": "a"}, {"type": "setQty", "sku": "a", "qty": 0}]],
        [[{"type": "setQty", "sku": "b", "qty": 5}, {"type": "setQty", "sku": "b", "qty": -1}]],
        [[{"type": "setQty", "sku": "c", "qty": 7}, {"type": "add", "sku": "c"}]],
        [[{"type": "applyCoupon", "code": "SPRING"}, {"type": "applyCoupon", "code": "CREW10"}]],
        [[{"type": "add", "sku": "a", "qty": 2}, {"type": "applyCoupon", "code": "X"}, {"type": "clear"}]],
        [[{"type": "add", "sku": "a"}, {"type": "refund", "sku": "a"}, {"type": "add", "sku": "b"}]],
        [[{"type": "add", "sku": "a", "qty": 2}, {"type": "add", "sku": "b", "qty": 3}, {"type": "remove", "sku": "a"},
          {"type": "add", "sku": "c"}]],
        [[{"type": "clear"}, {"type": "add", "sku": "z", "qty": 10}, {"type": "applyCoupon", "code": "LATE"}]],
    ],
    wrong_solutions=[
        '''function runCart(actions) {
  const state = { items: {}, coupon: null };
  for (const a of actions) {
    if (a.type === "add") state.items[a.sku] = (state.items[a.sku] || 0) + (a.qty || 1);
    else if (a.type === "remove") delete state.items[a.sku];
    else if (a.type === "setQty") state.items[a.sku] = a.qty;
    else if (a.type === "applyCoupon") state.coupon = a.code;
    else if (a.type === "clear") { state.items = {}; state.coupon = null; }
    else return { error: "Unhandled action: " + a.type };
  }
  return { ...state, totalQty: Object.values(state.items).reduce((s, n) => s + n, 0) };
}
''',
        '''function runCart(actions) {
  const state = { items: {}, coupon: null };
  for (const a of actions) {
    if (a.type === "add") state.items[a.sku] = (state.items[a.sku] ?? 0) + (a.qty ?? 1);
    else if (a.type === "remove") delete state.items[a.sku];
    else if (a.type === "setQty") { if (a.qty <= 0) delete state.items[a.sku]; else state.items[a.sku] = a.qty; }
    else if (a.type === "applyCoupon") state.coupon = a.code;
    else if (a.type === "clear") state.items = {};
  }
  return { ...state, totalQty: Object.values(state.items).reduce((s, n) => s + n, 0) };
}
''',
    ],
    guide=G(
        prereqs="Discriminated unions and `assertNever` (*Objects and structural typing*); reducers (*Typing React and Express*).",
        intuition="A reducer is a function `(state, action) => newState`. The `type` tag tells you which variant you hold, and a "
                  "`switch` gives each variant its own branch. The `default` branch is where anything unexpected lands.",
        hints=["Write the inner `reduce(state, action)` first; `runCart` is then a loop around it.",
               "Use `action.qty ?? 1` for the default quantity.",
               "Throw in `default` and catch in `runCart` to produce the error object."],
        brute_force="A chain of `if`/`else if` that mutates one state object works too. It is the same complexity; the `switch` "
                    "over the tag is clearer and maps directly onto TypeScript's narrowing.",
        approach="Fold the action list with the reducer, then compute `totalQty` from the final items.\n\n"
                 "**Dry run** on `[add a ×2, add b ×3, remove a, add c]`: after 1 → `{a: 2}`; after 2 → `{a: 2, b: 3}`; after 3 → "
                 "`{b: 3}`; after 4 → `{b: 3, c: 1}` (default quantity). `totalQty` = 4, coupon stays `null`.",
        complexity="Time O(n × k) with copying (k = distinct items), or O(n) if you mutate a private state; space O(k).",
        pitfalls="`setQty` with 0 must delete the key, not store 0. `clear` resets the coupon too. Silently ignoring an unknown "
                 "action hides bugs: the tests expect an error.",
        follow_up="Add an `undo` action by keeping a history stack of previous states, which is easy precisely because the reducer "
                  "returns new objects instead of mutating.",
    ),
),
# ------------------------------------------------------------------ 7
dict(
    id="ts-exhaustive-check", title="Exhaustive switch checker", difficulty="Easy",
    pattern="Discriminated unions", kind="js", entry="checkExhaustive",
    description=r"""
The compiler's exhaustiveness check answers: *does this `switch` handle every member of the union?* Reproduce it over
plain data.

Write `checkExhaustive(variants, cases, hasDefault)`:

- `variants`: the tags of the union, for example `["circle", "rect", "triangle"]` (no duplicates).
- `cases`: the labels written in the `switch`, in source order (may contain duplicates or labels that are not variants).
- `hasDefault`: whether the `switch` has a `default:` branch.

Return an object:

- `missing`: variants with no `case`, in the order of `variants`;
- `unknown`: case labels that are not variants, each once, in order of first appearance;
- `duplicates`: case labels that appear more than once, each once, in order of first appearance;
- `exhaustive`: `true` if `hasDefault` is true or `missing` is empty.

**Example:** `checkExhaustive(["circle","rect","triangle"], ["rect","circle"], false)` →
`{"missing":["triangle"],"unknown":[],"duplicates":[],"exhaustive":false}`
""",
    starter='''/**
 * @param {string[]} variants
 * @param {string[]} cases
 * @param {boolean} hasDefault
 * @returns {{ missing: string[], unknown: string[], duplicates: string[], exhaustive: boolean }}
 */
function checkExhaustive(variants, cases, hasDefault) {
  // your code
}
''',
    solution='''function checkExhaustive(variants, cases, hasDefault) {
  const handled = new Set(cases);
  const known = new Set(variants);
  const missing = variants.filter((v) => !handled.has(v));
  const unknown = [];
  const duplicates = [];
  const seen = new Set();
  for (const label of cases) {
    if (!known.has(label) && !unknown.includes(label)) unknown.push(label);
    if (seen.has(label) && !duplicates.includes(label)) duplicates.push(label);
    seen.add(label);
  }
  duplicates.sort((a, b) => cases.indexOf(a) - cases.indexOf(b));
  return { missing, unknown, duplicates, exhaustive: hasDefault || missing.length === 0 };
}
''',
    tests=[
        [["circle", "rect", "triangle"], ["rect", "circle"], False],
        [["circle", "rect", "triangle"], ["rect", "circle", "triangle"], False],
        [["circle", "rect", "triangle"], ["rect"], True],
        [["a", "b"], [], False],
        [["a", "b"], [], True],
        [[], [], False],
        [["a", "b"], ["a", "c", "b", "c", "d"], False],
        [["a", "b", "c"], ["b", "a", "b", "a", "a"], False],
        [["idle", "loading", "success", "failure"], ["loading", "success", "error"], False],
        [["x"], ["y", "y"], False],
        [["x", "y", "z"], ["z", "y", "x"], False],
        [["a", "b", "c"], ["c", "c", "a", "a"], False],
    ],
    wrong_solutions=[
        '''function checkExhaustive(variants, cases, hasDefault) {
  const missing = variants.filter((v) => !cases.includes(v));
  const unknown = cases.filter((c) => !variants.includes(c));
  const duplicates = cases.filter((c, i) => cases.indexOf(c) !== i);
  return { missing, unknown, duplicates, exhaustive: missing.length === 0 };
}
''',
        '''function checkExhaustive(variants, cases, hasDefault) {
  const missing = variants.filter((v) => !cases.includes(v));
  const unknown = [...new Set(cases.filter((c) => !variants.includes(c)))];
  const duplicates = [...new Set(cases.filter((c, i) => cases.indexOf(c) !== i))];
  return { missing, unknown, duplicates, exhaustive: hasDefault || cases.length >= variants.length };
}
''',
    ],
    guide=G(
        prereqs="Exhaustiveness checking with `never` (*Objects and structural typing*); `Set`.",
        intuition="Exhaustiveness is set difference: the variants minus the handled labels must be empty. The two other lists are "
                  "the reverse difference (labels that are not variants) and a duplicate count.",
        hints=["`missing` is a filter over `variants`.",
               "Walk `cases` once with a `seen` set to find duplicates.",
               "A `default` branch makes the switch exhaustive no matter what is missing."],
        brute_force="Nested loops comparing every variant with every case: O(v × c). Fine for a handful of tags, and sets bring "
                    "it down to O(v + c).",
        approach="Build a set of case labels and a set of variants; filter and scan.\n\n"
                 "**Dry run**: variants `[a, b]`, cases `[a, c, b, c, d]`, no default. `missing`: both `a` and `b` are handled → `[]`. "
                 "Scan: `a` known; `c` unknown → `[c]`; `b` known; `c` seen before → duplicates `[c]`; `d` unknown → `[c, d]`. "
                 "`exhaustive` is `true` because nothing is missing.",
        complexity="Time O(v + c) with sets (the small `includes` calls are on the output lists), space O(v + c).",
        pitfalls="Reporting a label three times when it appears three times. Forgetting the `default` rule. Deciding exhaustiveness "
                 "by comparing lengths, which duplicates and unknown labels defeat.",
        follow_up="In real TypeScript an unknown label is itself a compile error (`Type '\"x\"' is not comparable to type ...`). "
                  "The typed lint rule `switch-exhaustiveness-check` reports the `missing` list.",
    ),
),
]
