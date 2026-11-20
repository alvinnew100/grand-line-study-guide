"""GraphQL track problems, part 2: variables, the type graph and introspection."""

SCHEMA_G = {
    "Query": {"recipe": "Recipe", "cooks": "[Cook!]!"},
    "Recipe": {"id": "ID!", "title": "String!", "author": "Cook!", "steps": "[Step!]!"},
    "Cook": {"id": "ID!", "recipes": "[Recipe!]!"},
    "Step": {"text": "String!"},
    "Badge": {"label": "String!", "icon": "Icon"},
    "Icon": {"url": "String!"},
    "Mutation": {"addNote": "Note"},
    "Note": {"body": "String", "about": "Recipe"},
    "Orphan": {"self": "Orphan"},
}

INTRO = {
    "Recipe": {"kind": "OBJECT", "fields": {"id": "ID!", "title": "String!", "category": "Category", "tags": "[String!]!", "author": "Cook"}},
    "Cook": {"kind": "OBJECT", "fields": {"id": "ID!", "recipes": "[Recipe]"}},
    "Category": {"kind": "ENUM", "values": ["SOUP", "BREAD", "DESSERT"]},
    "Query": {"kind": "OBJECT", "fields": {"feed": "[[Recipe!]]!"}},
}

PROBLEMS = [
dict(
    id="gql-variables-defaults",
    title="Bind variables with defaults",
    difficulty="Medium",
    pattern="Query language",
    entry="bind_arguments",
    description=r"""
Before a server executes an operation it turns the client's **variables** into concrete argument values.

`bind_arguments(var_defs, provided, args)`

- `var_defs`: the operation's variable definitions in order, each `{"name": "n", "type": "Int!"}` with an optional `"default"` key.
- `provided`: the variables dictionary the client sent.
- `args`: an argument dictionary. Anywhere inside it (at the top, inside nested input objects, inside lists) a dictionary with
  exactly one key `"var"` (`{"var": "n"}`) is a reference to the variable `$n`.

**Step 1: coerce variables**, in definition order. A type is *required* if it ends with `!`.

| situation | outcome |
|---|---|
| name is in `provided`, value not `None` | use the provided value |
| name is in `provided`, value is `None`, type required | error `Variable "$n" of non-null type "T" must not be null.` |
| name is in `provided`, value is `None`, type not required | the variable is `None` |
| not provided, definition has `default` | use the default |
| not provided, no default, type required | error `Variable "$n" of required type "T" was not provided.` |
| not provided, no default, not required | the variable is **unset** |

Variables in `provided` that are not defined are ignored. If there is any error, return `{"errors": [...]}` (all of them, in definition order).

**Step 2: substitute.** Replace each reference with its value. A reference to an **unset** variable removes that key from the
dictionary that holds it (the argument is not passed at all); inside a list it becomes `None`. Return `{"args": new_args}`. Do not modify the inputs.

**Example:** `bind_arguments([{"name": "n", "type": "Int", "default": 10}], {}, {"first": {"var": "n"}})` → `{"args": {"first": 10}}`
""",
    starter='''def bind_arguments(var_defs, provided, args):
    pass
''',
    solution='''def bind_arguments(var_defs, provided, args):
    values, errors = {}, []
    for d in var_defs:
        name, typ = d["name"], d["type"]
        required = typ.endswith("!")
        if name in provided:
            if provided[name] is None and required:
                errors.append('Variable "$%s" of non-null type "%s" must not be null.' % (name, typ))
            else:
                values[name] = provided[name]
        elif "default" in d:
            values[name] = d["default"]
        elif required:
            errors.append('Variable "$%s" of required type "%s" was not provided.' % (name, typ))
    if errors:
        return {"errors": errors}
    unset = object()

    def sub(v):
        if isinstance(v, dict):
            if len(v) == 1 and "var" in v:
                return values.get(v["var"], unset)
            out = {}
            for k, x in v.items():
                r = sub(x)
                if r is not unset:
                    out[k] = r
            return out
        if isinstance(v, list):
            return [None if r is unset else r for r in (sub(x) for x in v)]
        return v

    return {"args": sub(args)}
''',
    tests=[
        [[{"name": "n", "type": "Int", "default": 10}], {}, {"first": {"var": "n"}}],
        [[{"name": "id", "type": "ID!"}], {"id": "r1"}, {"id": {"var": "id"}}],
        [[{"name": "id", "type": "ID!"}], {}, {"id": {"var": "id"}}],
        [[{"name": "n", "type": "Int", "default": 10}], {"n": 3}, {"first": {"var": "n"}, "after": "abc"}],
        [[{"name": "n", "type": "Int", "default": 10}], {"n": None}, {"first": {"var": "n"}}],
        [[{"name": "n", "type": "Int!", "default": 10}], {"n": None}, {"first": {"var": "n"}}],
        [[{"name": "cat", "type": "Category"}], {}, {"category": {"var": "cat"}, "first": 5}],
        [[{"name": "a", "type": "Int!"}, {"name": "b", "type": "String!"}, {"name": "c", "type": "Int"}], {"c": 1}, {"x": {"var": "a"}}],
        [[{"name": "t", "type": "String!"}, {"name": "m", "type": "Int"}], {"t": "Soup", "extra": 9},
         {"input": {"title": {"var": "t"}, "minutes": {"var": "m"}, "tags": [{"var": "t"}, "quick", {"var": "m"}]}}],
        [[{"name": "inp", "type": "RecipeInput!"}], {"inp": {"var": "x"}}, {"input": {"var": "inp"}, "other": {"var": "x", "k": 1}}],
        [[], {"n": 1}, {"first": 2}],
        [[{"name": "flag", "type": "Boolean", "default": False}, {"name": "z", "type": "Int", "default": 0}], {}, {"a": {"var": "flag"}, "b": {"deep": {"deeper": {"var": "z"}}}}],
        [[{"name": "n", "type": "Int", "default": None}], {}, {"first": {"var": "n"}}],
    ],
    examples=3,
    wrong_solutions=[
        '''def bind_arguments(var_defs, provided, args):
    values = {}
    for d in var_defs:
        values[d["name"]] = provided.get(d["name"], d.get("default"))
    def sub(v):
        if isinstance(v, dict):
            if len(v) == 1 and "var" in v:
                return values.get(v["var"])
            return {k: sub(x) for k, x in v.items()}
        if isinstance(v, list):
            return [sub(x) for x in v]
        return v
    return {"args": sub(args)}
''',
        '''def bind_arguments(var_defs, provided, args):
    values, errors = {}, []
    for d in var_defs:
        name, typ = d["name"], d["type"]
        v = provided.get(name)
        if v is None:
            v = d.get("default")
        if v is None and typ.endswith("!"):
            errors.append('Variable "$%s" of required type "%s" was not provided.' % (name, typ))
        elif v is not None:
            values[name] = v
    if errors:
        return {"errors": errors}
    unset = object()
    def sub(v):
        if isinstance(v, dict):
            if len(v) == 1 and "var" in v:
                return values.get(v["var"], unset)
            return {k: r for k, r in ((k, sub(x)) for k, x in v.items()) if r is not unset}
        if isinstance(v, list):
            return [None if r is unset else r for r in (sub(x) for x in v)]
        return v
    return {"args": sub(args)}
''',
        '''def bind_arguments(var_defs, provided, args):
    values, errors = {}, []
    for d in var_defs:
        name, typ = d["name"], d["type"]
        required = typ.endswith("!")
        if name in provided:
            if provided[name] is None and required:
                errors.append('Variable "$%s" of non-null type "%s" must not be null.' % (name, typ))
            else:
                values[name] = provided[name]
        elif "default" in d:
            values[name] = d["default"]
        elif required:
            errors.append('Variable "$%s" of required type "%s" was not provided.' % (name, typ))
            return {"errors": errors}
    if errors:
        return {"errors": errors}
    def sub(v):
        if isinstance(v, dict):
            if "var" in v:
                return values.get(v["var"])
            return {k: sub(x) for k, x in v.items()}
        if isinstance(v, list):
            return [sub(x) for x in v]
        return v
    return {"args": sub(args)}
''',
    ],
    guide=dict(
        prereqs="The lesson *Variables, mutations and subscriptions*; Python `in` on dictionaries; recursion over nested dictionaries and lists.",
        intuition="Three different states hide behind one word 'empty': the client sent a real value, the client sent an explicit `null`, or the client sent nothing. GraphQL treats them differently, and defaults only fill the third case. Python's `provided.get(name)` blurs the last two, so test membership with `name in provided` instead.",
        hints=[
            "Do the work in two passes: first build a `values` dictionary (and an `errors` list), then walk `args`.",
            "An explicit `None` for a nullable variable overrides the default. Only an *absent* variable takes the default.",
            "Use a private marker object such as `unset = object()` as the return value for references to unset variables, so the caller can tell 'unset' apart from a real `None`.",
        ],
        brute_force="Convert `args` to a JSON string and do text replacement of each `{\"var\": \"n\"}`. It cannot drop unset arguments cleanly, breaks when a user's string happens to contain the same text, and loses value types.",
        approach="""**Pass 1** follows the table row by row for each definition.

**Pass 2** is a recursive `sub(v)`:
- dictionary with exactly the key `var` → look up the value, or return `unset`;
- other dictionary → rebuild it, skipping children that came back `unset`;
- list → rebuild it, turning `unset` into `None`;
- anything else → itself.

**Dry run:** defs `[t: String!, m: Int]`, provided `{"t": "Soup"}`, args `{"input": {"title": {"var": "t"}, "minutes": {"var": "m"}}}`.

| step | state |
|---|---|
| coerce `t` | `values = {"t": "Soup"}` |
| coerce `m` | not provided, no default, nullable → unset |
| substitute `title` | `"Soup"` |
| substitute `minutes` | unset → key dropped |

Result `{"args": {"input": {"title": "Soup"}}}`.""",
        complexity="Time O(v + a) for v variable definitions and a nodes in the argument tree. Space O(a) for the rebuilt arguments.",
        pitfalls="- Returning at the first error instead of collecting all of them.\n- Treating a provided variable *value* that happens to look like `{\"var\": ...}` as a reference: only the `args` tree is scanned, never the substituted values.\n- A default of `None` is still a default: the variable is set to `None`, not unset.\n- A dictionary such as `{\"var\": \"x\", \"k\": 1}` has two keys, so it is ordinary data.",
        follow_up="Real servers also coerce the *type* of each variable (see `gql-type-check`). Combine the two problems for a full variable-coercion step.",
    ),
),
dict(
    id="gql-unused-types",
    title="Find types unreachable from the roots",
    difficulty="Easy",
    pattern="Graphs",
    entry="unused_types",
    description=r"""
A schema is a graph: each type is a node, and each field whose type is another object type is an edge.
Clients can only ever reach types that are connected to a **root type** (`Query`, `Mutation` or `Subscription`).
Anything else is dead weight.

`unused_types(schema)` receives `{type name: {field name: type string}}`. A type string is a type name possibly
wrapped in list brackets and non-null marks, for example `Recipe`, `Recipe!`, `[Recipe!]!`. Names that are not keys of
`schema` (such as `String`, `ID`, `Int`) are scalars and lead nowhere.

Return the **sorted** list of type names in `schema` that cannot be reached by following fields from any root type that
exists in the schema. Root types themselves are always reachable. If the schema has no root type, every type is unreachable.

**Example:** `{"Query": {"cook": "Cook"}, "Cook": {"name": "String!"}, "Badge": {"label": "String"}}` → `["Badge"]`
""",
    starter='''def unused_types(schema):
    pass
''',
    solution='''def unused_types(schema):
    seen = set()
    stack = [r for r in ("Query", "Mutation", "Subscription") if r in schema]
    while stack:
        t = stack.pop()
        if t in seen:
            continue
        seen.add(t)
        for type_str in schema[t].values():
            name = type_str.replace("[", "").replace("]", "").replace("!", "")
            if name in schema and name not in seen:
                stack.append(name)
    return sorted(t for t in schema if t not in seen)
''',
    tests=[
        [{"Query": {"cook": "Cook"}, "Cook": {"name": "String!"}, "Badge": {"label": "String"}}],
        [SCHEMA_G],
        [{k: v for k, v in SCHEMA_G.items() if k != "Mutation"}],
        [{}],
        [{"Query": {"ok": "Boolean"}}],
        [{"Cook": {"friend": "Cook"}, "Recipe": {"author": "Cook!"}}],
        [{"Query": {"a": "[A!]!"}, "A": {"b": "[[B]]"}, "B": {"a": "A", "c": "C!"}, "C": {"id": "ID"}, "D": {"c": "C"}}],
        [{"Subscription": {"added": "Recipe!"}, "Recipe": {"id": "ID!"}, "Cook": {"id": "ID!"}}],
        [{"Query": {"me": "Query"}, "Zed": {"q": "Query"}, "Alpha": {"z": "Zed"}}],
        [{"Query": {"x": "Missing", "y": "String"}, "Other": {"x": "Int"}}],
        [dict({"Query": {"t0": "T0"}}, **{"T%d" % i: {"next": "T%d" % (i + 1)} for i in range(300)}, **{"U%d" % i: {"n": "T0"} for i in range(5)})],
    ],
    examples=2,
    wrong_solutions=[
        '''def unused_types(schema):
    used = set(["Query", "Mutation", "Subscription"])
    for fields in schema.values():
        for t in fields.values():
            used.add(t.replace("[", "").replace("]", "").replace("!", ""))
    return sorted(t for t in schema if t not in used)
''',
        '''def unused_types(schema):
    seen = set()
    stack = ["Query"] if "Query" in schema else []
    while stack:
        t = stack.pop()
        if t in seen:
            continue
        seen.add(t)
        for type_str in schema[t].values():
            name = type_str.replace("[", "").replace("]", "").replace("!", "")
            if name in schema:
                stack.append(name)
    return sorted(t for t in schema if t not in seen)
''',
        '''def unused_types(schema):
    seen = set(r for r in ("Query", "Mutation", "Subscription") if r in schema)
    for r in list(seen):
        for type_str in schema[r].values():
            name = type_str.replace("[", "").replace("]", "").replace("!", "")
            if name in schema:
                seen.add(name)
    return sorted(t for t in schema if t not in seen)
''',
    ],
    guide=dict(
        prereqs="The lesson *Graph vocabulary: nodes, edges and paths*; Python sets and lists used as a stack.",
        intuition="Stand on the root types and walk along every edge you can. Whatever you never step on is unreachable. Being *mentioned* by some type is not enough: if the type that mentions it is itself unreachable, nobody can get there.",
        hints=[
            "Strip `[`, `]` and `!` from a type string to get the bare type name.",
            "Keep a `seen` set and a to-do list. Take a type from the list, mark it, and add the object types its fields point to.",
            "Check `if t in seen: continue` so that cycles such as `Cook.recipes -> Recipe.author -> Cook` do not loop forever.",
        ],
        brute_force="Repeat 'for every type, if it is reachable, mark the types it mentions' until a full pass changes nothing. Correct, but each pass is O(V + E) and up to V passes are needed: O(V·(V + E)).",
        approach="""Depth-first search from the roots.

**Dry run** on `{"Query": {"cook": "Cook"}, "Cook": {"name": "String!"}, "Badge": {"label": "String"}}`:

| stack | popped | seen after | pushed |
|---|---|---|---|
| `[Query]` | Query | {Query} | Cook |
| `[Cook]` | Cook | {Query, Cook} | (String is a scalar) |
| `[]` | | | |

Types not in `seen`: `["Badge"]`.""",
        complexity="Time O(V + E): every type is processed once and every field examined once. Space O(V) for the set and stack.",
        pitfalls="- Counting a type as used because *any* type refers to it (two dead types can refer to each other).\n- Starting only from `Query` and forgetting `Mutation` and `Subscription`.\n- Stopping after one hop from the roots instead of following paths of any length.\n- Recursion without a visited set never ends on cyclic schemas.",
        follow_up="Return, for each reachable type, the shortest field path from `Query` (breadth-first search).",
    ),
),
dict(
    id="gql-introspection-list",
    title="Answer an introspection query",
    difficulty="Medium",
    pattern="Schema",
    entry="introspect",
    description=r"""
Introspection lets a client ask a GraphQL server about its own schema. In the real system, the query
`{ __schema { types { name kind fields { name type { kind name ofType { ... } } } enumValues { name } } } }`
returns every type. Produce that answer from a compact schema descriptor.

`introspect(schema)` receives `{type name: descriptor}` where a descriptor is either
`{"kind": "OBJECT", "fields": {field name: type string}}` or `{"kind": "ENUM", "values": [names]}`.

Return a list with one entry per type, **sorted by type name**:

```
{"name": ..., "kind": ..., "fields": [...] or None, "enumValues": [...] or None}
```

- For an `OBJECT`: `fields` is a list of `{"name": field, "type": type_ref}` in the descriptor's order; `enumValues` is `None`.
- For an `ENUM`: `fields` is `None`; `enumValues` is a list of `{"name": value}` in order.

A **type ref** unwraps a type string one layer at a time, outermost first:

- `T!` → `{"kind": "NON_NULL", "name": None, "ofType": ref(T)}`
- `[T]` → `{"kind": "LIST", "name": None, "ofType": ref(T)}`
- a bare name → `{"kind": K, "name": name, "ofType": None}` where `K` is `"SCALAR"` for `Int`, `Float`, `String`,
  `Boolean`, `ID`, and otherwise the `kind` of that type in the schema.

**Example:** `ref("[String!]!")` is `NON_NULL → LIST → NON_NULL → SCALAR String`.
""",
    starter='''def introspect(schema):
    pass
''',
    solution='''SCALARS = {"Int", "Float", "String", "Boolean", "ID"}

def introspect(schema):
    def ref(t):
        if t.endswith("!"):
            return {"kind": "NON_NULL", "name": None, "ofType": ref(t[:-1])}
        if t.startswith("["):
            return {"kind": "LIST", "name": None, "ofType": ref(t[1:-1])}
        kind = "SCALAR" if t in SCALARS else schema[t]["kind"]
        return {"kind": kind, "name": t, "ofType": None}

    out = []
    for name in sorted(schema):
        d = schema[name]
        is_obj = d["kind"] == "OBJECT"
        out.append({
            "name": name,
            "kind": d["kind"],
            "fields": [{"name": f, "type": ref(t)} for f, t in d["fields"].items()] if is_obj else None,
            "enumValues": None if is_obj else [{"name": v} for v in d["values"]],
        })
    return out
''',
    tests=[
        [{"Cook": {"kind": "OBJECT", "fields": {"name": "String"}}}],
        [{"Cook": {"kind": "OBJECT", "fields": {"tags": "[String!]!"}}}],
        [INTRO],
        [{}],
        [{"Category": {"kind": "ENUM", "values": ["SOUP"]}}],
        [{"Zed": {"kind": "OBJECT", "fields": {}}, "Alpha": {"kind": "ENUM", "values": []}}],
        [{"A": {"kind": "OBJECT", "fields": {"m": "[[[Int]!]]", "self": "A!", "e": "[E!]"}}, "E": {"kind": "ENUM", "values": ["X", "Y"]}}],
        [{"Query": {"kind": "OBJECT", "fields": {"z": "Float", "a": "Boolean!", "m": "ID"}}}],
        [{"b": {"kind": "ENUM", "values": ["B2", "B1"]}, "a": {"kind": "ENUM", "values": ["A"]}, "C": {"kind": "OBJECT", "fields": {"x": "b!", "y": "[a]"}}}],
        [{"T%02d" % i: {"kind": "OBJECT", "fields": {"n": "T%02d" % ((i * 7) % 20), "v": "[Int!]"}} for i in range(19, -1, -1)}],
    ],
    examples=2,
    wrong_solutions=[
        '''SCALARS = {"Int", "Float", "String", "Boolean", "ID"}
def introspect(schema):
    def ref(t):
        name = t.replace("[", "").replace("]", "").replace("!", "")
        return {"kind": "SCALAR" if name in SCALARS else schema[name]["kind"], "name": name, "ofType": None}
    out = []
    for name in sorted(schema):
        d = schema[name]
        o = d["kind"] == "OBJECT"
        out.append({"name": name, "kind": d["kind"],
                    "fields": [{"name": f, "type": ref(t)} for f, t in d["fields"].items()] if o else None,
                    "enumValues": None if o else [{"name": v} for v in d["values"]]})
    return out
''',
        '''SCALARS = {"Int", "Float", "String", "Boolean", "ID"}
def introspect(schema):
    def ref(t):
        if t.startswith("["):
            return {"kind": "LIST", "name": None, "ofType": ref(t.rstrip("!")[1:-1])}
        if t.endswith("!"):
            return {"kind": "NON_NULL", "name": None, "ofType": ref(t[:-1])}
        return {"kind": "SCALAR" if t in SCALARS else schema[t]["kind"], "name": t, "ofType": None}
    out = []
    for name in sorted(schema):
        d = schema[name]
        o = d["kind"] == "OBJECT"
        out.append({"name": name, "kind": d["kind"],
                    "fields": [{"name": f, "type": ref(t)} for f, t in d["fields"].items()] if o else None,
                    "enumValues": None if o else [{"name": v} for v in d["values"]]})
    return out
''',
        '''SCALARS = {"Int", "Float", "String", "Boolean", "ID"}
def introspect(schema):
    def ref(t):
        if t.endswith("!"):
            return {"kind": "NON_NULL", "name": None, "ofType": ref(t[:-1])}
        if t.startswith("["):
            return {"kind": "LIST", "name": None, "ofType": ref(t[1:-1])}
        return {"kind": "SCALAR" if t in SCALARS else "OBJECT", "name": t, "ofType": None}
    out = []
    for name in schema:
        d = schema[name]
        o = d["kind"] == "OBJECT"
        out.append({"name": name, "kind": d["kind"],
                    "fields": [{"name": f, "type": ref(t)} for f, t in d["fields"].items()] if o else None,
                    "enumValues": None if o else [{"name": v} for v in d["values"]]})
    return out
''',
    ],
    guide=dict(
        prereqs="The lesson *Introspection and abstract syntax trees*; string slicing; recursion.",
        intuition="A type string such as `[String!]!` is an onion. Introspection reports it one layer at a time, from the outside in: non-null, then list, then non-null, then the named type at the core. Peel one layer, recurse on what is left.",
        hints=[
            "Check the **last** character first. If it is `!`, the outermost layer is NON_NULL and the rest is `t[:-1]`.",
            "Otherwise, if the string starts with `[`, the outer layer is LIST and the inside is `t[1:-1]`.",
            "The base case is a bare name: look it up in the five built-in scalars, otherwise in the schema.",
        ],
        brute_force="Hard-code the common shapes (`T`, `T!`, `[T]`, `[T!]`, `[T]!`, `[T!]!`) with six `if` branches. It fails on a list of lists and is longer than the three-line recursive version.",
        approach="""`ref(t)` peels one wrapper per call.

**Dry run** `ref("[String!]!")`:

| call | sees | emits | recurses on |
|---|---|---|---|
| 1 | ends with `!` | NON_NULL | `[String!]` |
| 2 | starts with `[` | LIST | `String!` |
| 3 | ends with `!` | NON_NULL | `String` |
| 4 | bare name | SCALAR String | |

Then build the outer list by iterating `sorted(schema)`.""",
        complexity="Time O(total characters of all type strings + T log T for sorting T types). Space O(output size).",
        pitfalls="- Testing for `[` before `!` on `[Int]!` wraps in the wrong order.\n- Reporting every non-scalar as OBJECT: an enum field must report kind ENUM.\n- Forgetting to sort types, or sorting the fields (fields keep their declared order).\n- Returning `[]` instead of `None` for the fields of an enum: real introspection returns `null`.",
        follow_up="Go the other way: turn a type ref back into its string, which is what tools such as GraphiQL do to print documentation.",
    ),
),
]
