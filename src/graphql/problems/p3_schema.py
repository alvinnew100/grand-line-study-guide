"""GraphQL track problems, part 3: the type system (type checking, validation, null propagation)."""

VSCHEMA = {
    "Query": {
        "recipe": {"type": "Recipe", "args": {"id": "ID!"}},
        "recipes": {"type": "[Recipe!]!", "args": {"first": "Int", "category": "String", "maxRating": "Float", "published": "Boolean"}},
        "me": {"type": "Cook"},
        "version": {"type": "String!"},
    },
    "Recipe": {
        "id": {"type": "ID!"},
        "title": {"type": "String!"},
        "minutes": {"type": "Int"},
        "author": {"type": "Cook!"},
        "reviews": {"type": "[Review!]!", "args": {"first": "Int!", "minStars": "Int"}},
    },
    "Cook": {
        "id": {"type": "ID!"},
        "name": {"type": "String!"},
        "recipes": {"type": "[Recipe!]!"},
    },
    "Review": {"stars": {"type": "Int!"}, "by": {"type": "Cook"}},
}

NN_SHAPE = {
    "recipe": {"fields": {
        "id": {"nonNull": True},
        "title": {"nonNull": True},
        "minutes": {},
        "author": {"nonNull": True, "fields": {"name": {"nonNull": True}, "city": {}}},
        "reviews": {"items": {"nonNull": True, "fields": {"stars": {"nonNull": True}, "by": {"fields": {"name": {"nonNull": True}}}}}},
        "tags": {"nonNull": True, "items": {"nonNull": True}},
    }},
    "version": {"nonNull": True},
    "motd": {},
}
NN_GOOD = {
    "recipe": {"id": "r1", "title": "Lentil soup", "minutes": None,
               "author": {"name": "Amara", "city": None},
               "reviews": [{"stars": 5, "by": {"name": "Bo"}}, {"stars": 4, "by": None}],
               "tags": ["vegan"]},
    "version": "1.4", "motd": None,
}


def _nn(**changes):
    import copy
    d = copy.deepcopy(NN_GOOD)
    for path, v in changes.items():
        cur = d
        parts = path.split("__")
        for p in parts[:-1]:
            cur = cur[int(p)] if p.isdigit() else cur[p]
        last = parts[-1]
        cur[int(last) if last.isdigit() else last] = v
    return d


PROBLEMS = [
dict(
    id="gql-type-check",
    title="Does this value fit this type?",
    difficulty="Medium",
    pattern="Type system",
    entry="conforms",
    description=r"""
Every value that enters or leaves a GraphQL server is checked against a type written in a compact notation:

- a scalar name: `Int`, `Float`, `String`, `Boolean`, `ID`
- `T!` means *non-null*: the value may not be `None`
- `[T]` means *a list whose items each fit `T`*

Wrappers nest freely: `[Int!]!`, `[[String]]`, `[[Float!]!]!`.

Write `conforms(value, type_str)` returning `True` or `False`.

| type | accepts |
|---|---|
| `Int` | a whole number in the signed 32-bit range $-2^{31} \le n \le 2^{31}-1$ (not a boolean) |
| `Float` | any integer or float (not a boolean) |
| `String` | a string |
| `Boolean` | `True` / `False` only |
| `ID` | a string, or an integer (not a boolean) |

Anything without a trailing `!` also accepts `None`. A list type accepts only a Python list (a single value is **not**
wrapped automatically), and the empty list always fits a list type. Unknown scalar names accept nothing except `None`.

**Examples:** `conforms([1, 2], "[Int!]!")` → `True` · `conforms([1, None], "[Int!]!")` → `False` · `conforms(None, "[Int!]")` → `True`
""",
    starter='''def conforms(value, type_str):
    pass
''',
    solution='''def conforms(value, type_str):
    t = type_str
    if t.endswith("!"):
        return value is not None and conforms(value, t[:-1])
    if value is None:
        return True
    if t.startswith("["):
        return isinstance(value, list) and all(conforms(v, t[1:-1]) for v in value)
    is_bool = isinstance(value, bool)
    if t == "Int":
        return isinstance(value, int) and not is_bool and -2 ** 31 <= value <= 2 ** 31 - 1
    if t == "Float":
        return isinstance(value, (int, float)) and not is_bool
    if t == "String":
        return isinstance(value, str)
    if t == "Boolean":
        return is_bool
    if t == "ID":
        return isinstance(value, str) or (isinstance(value, int) and not is_bool)
    return False
''',
    tests=[
        [[1, 2], "[Int!]!"],
        [[1, None], "[Int!]!"],
        [None, "[Int!]"],
        [7, "Int"], ["7", "Int"], [True, "Int"], [2147483648, "Int"], [-2147483648, "Int!"],
        [2.5, "Float"], [3, "Float!"], [False, "Float"], [2.5, "Int"],
        ["soup", "String!"], [None, "String!"], [None, "String"], [5, "String"],
        [True, "Boolean!"], [0, "Boolean"], ["true", "Boolean"],
        ["r1", "ID"], [42, "ID!"], [4.5, "ID"], [True, "ID"],
        [[], "[String!]!"], [None, "[String!]!"], ["a", "[String]"], [[None, "a"], "[String]!"],
        [[[1, 2], [], None], "[[Int!]]"], [[[1, None]], "[[Int!]]"], [[[1.5]], "[[Float!]!]!"], [[None], "[[Float!]!]!"],
        [[1, 2], "Int"], ["x", "Date"], [None, "Date"], [[["a"]], "[[[String!]!]!]!"], [[["a", 1]], "[[[String!]!]!]!"],
    ],
    examples=3,
    wrong_solutions=[
        '''def conforms(value, type_str):
    t = type_str
    if t.endswith("!"):
        return value is not None and conforms(value, t[:-1])
    if value is None:
        return True
    if t.startswith("["):
        return isinstance(value, list) and all(conforms(v, t[1:-1]) for v in value)
    if t == "Int":
        return isinstance(value, int)
    if t == "Float":
        return isinstance(value, (int, float))
    if t == "String":
        return isinstance(value, str)
    if t == "Boolean":
        return isinstance(value, bool)
    if t == "ID":
        return isinstance(value, (str, int))
    return False
''',
        '''def conforms(value, type_str):
    name = type_str.replace("[", "").replace("]", "").replace("!", "")
    def scalar(v):
        b = isinstance(v, bool)
        if v is None: return "!" not in type_str
        if name == "Int": return isinstance(v, int) and not b and -2 ** 31 <= v <= 2 ** 31 - 1
        if name == "Float": return isinstance(v, (int, float)) and not b
        if name == "String": return isinstance(v, str)
        if name == "Boolean": return b
        if name == "ID": return isinstance(v, str) or (isinstance(v, int) and not b)
        return False
    def flat(v):
        if isinstance(v, list):
            return all(flat(x) for x in v)
        return scalar(v)
    return flat(value)
''',
        '''def conforms(value, type_str):
    t = type_str
    if t.endswith("!"):
        return value is not None and conforms(value, t[:-1])
    if value is None:
        return True
    if t.startswith("["):
        if not isinstance(value, list):
            value = [value]
        return all(conforms(v, t[1:-1]) for v in value)
    is_bool = isinstance(value, bool)
    if t == "Int":
        return isinstance(value, int) and not is_bool
    if t == "Float":
        return isinstance(value, (int, float)) and not is_bool
    if t == "String":
        return isinstance(value, str)
    if t == "Boolean":
        return is_bool
    if t == "ID":
        return isinstance(value, str) or (isinstance(value, int) and not is_bool)
    return False
''',
    ],
    guide=dict(
        prereqs="The lesson *Types, scalars, enums, lists and non-null*; `isinstance`; recursion; string slicing.",
        intuition="The type string is a set of nested wrappers around a scalar, and the value must match wrapper for wrapper. Read the type from the outside in and let each layer answer one question: `!` asks 'is it non-null?', `[ ]` asks 'is it a list, and does every item fit the inside?', and the scalar name asks the final question about the bare value.",
        hints=[
            "Handle the trailing `!` first: the value must not be `None`, and then it must fit the type with the `!` removed.",
            "After the `!` case, a `None` value always fits (the type is nullable at this layer).",
            "In Python `True` is an instance of `int`. Test `isinstance(value, bool)` explicitly so that booleans do not pass as `Int`, `Float` or `ID`.",
        ],
        brute_force="Strip all wrappers to find the scalar, flatten the value, and check each flattened item. It cannot tell which layer is allowed to be `None`, so `[Int!]` and `[Int]!` look the same. The position of each `!` matters.",
        approach="""Recursive descent with four cases, in this order: non-null wrapper, `None`, list wrapper, scalar.

**Dry run** `conforms([[1, 2], [], None], "[[Int!]]")`:

| value | type | case | result |
|---|---|---|---|
| `[[1,2],[],None]` | `[[Int!]]` | list → check each against `[Int!]` | |
| `[1,2]` | `[Int!]` | list → each against `Int!` | True |
| `[]` | `[Int!]` | empty list | True |
| `None` | `[Int!]` | nullable → fits | True |

All items fit → `True`. Change the type to `[[Int!]!]` and the last item fails.""",
        complexity="Time O(n + d) where n is the number of values in the (nested) list and d the number of wrappers; each value is examined once per layer it sits in. Space O(d) recursion depth.",
        pitfalls="- `bool` is a subclass of `int` in Python.\n- GraphQL `Int` is 32-bit: 2147483648 is not a valid `Int`.\n- `[Int!]` allows the list itself to be null; `[Int]!` allows null items. They are different types.\n- Checking `[` before `!` mis-parses `[Int]!`.",
        follow_up="Add enum types (value must be one of a list of names) and input object types (a dictionary whose fields each have a type).",
    ),
),
dict(
    id="gql-validate-query",
    title="Validate a query against a schema",
    difficulty="Hard",
    pattern="Validation",
    entry="validate",
    description=r"""
A GraphQL server refuses to run a query that does not fit the schema. Write the validator.

`validate(schema, query)` returns a list of error strings (empty when the query is valid).

**Schema descriptor:** `{type name: {field name: {"type": type string, "args": {arg name: type string}}}}`; `args` is optional.
The root type is `"Query"`. Type strings use `!` and `[ ]`; the *named type* is what is left after removing them.
A field is an **object field** if its named type is a key of the schema; otherwise it is a **leaf**.

**Query:** a list of field nodes `{"name": ..., "args": {...}, "selection": [...]}` (`args` and `selection` optional).

Walk the query depth-first in document order. For each field node on parent type `P`, with *coordinate* `P.name`, report in this order:

1. Unknown field → `Cannot query field "name" on type "P".` Then skip this node entirely (no further checks, no children).
2. For each supplied argument, in the order supplied:
   - not declared → `Unknown argument "a" on field "P.name".`
   - wrong value → `Argument "a" on field "P.name" expects type "T".` Argument types are scalars with an optional `!`:
     `Int` (integer, not bool), `Float` (integer or float, not bool), `String`, `Boolean`, `ID` (string or integer, not bool).
     `None` is accepted only when the type has no `!`.
3. For each declared argument whose type ends in `!` and that was not supplied, in declaration order →
   `Field "P.name" argument "a" of type "T" is required.`
4. Selection rule:
   - object field with a missing or empty selection → `Field "name" of type "T" must have a selection.`
   - leaf field with a non-empty selection → `Field "name" of type "T" must not have a selection.` (do not look inside it)
   - object field with a selection → validate the children against the named type.

`T` in messages is the full type string as written in the schema.

**Example:** `[{"name": "recipe", "selection": [{"name": "name"}]}]` →
`['Field "Query.recipe" argument "id" of type "ID!" is required.', 'Cannot query field "name" on type "Recipe".']`
""",
    starter='''def validate(schema, query):
    errors = []
    return errors
''',
    solution='''def validate(schema, query):
    errors = []

    def named(t):
        return t.replace("[", "").replace("]", "").replace("!", "")

    def fits(value, t):
        if t.endswith("!"):
            return value is not None and fits(value, t[:-1])
        if value is None:
            return True
        b = isinstance(value, bool)
        if t == "Int":
            return isinstance(value, int) and not b
        if t == "Float":
            return isinstance(value, (int, float)) and not b
        if t == "String":
            return isinstance(value, str)
        if t == "Boolean":
            return b
        if t == "ID":
            return isinstance(value, str) or (isinstance(value, int) and not b)
        return True

    def walk(parent, selection):
        for node in selection:
            name = node["name"]
            field = schema[parent].get(name)
            if field is None:
                errors.append('Cannot query field "%s" on type "%s".' % (name, parent))
                continue
            coord = parent + "." + name
            given = node.get("args") or {}
            declared = field.get("args") or {}
            for a, v in given.items():
                if a not in declared:
                    errors.append('Unknown argument "%s" on field "%s".' % (a, coord))
                elif not fits(v, declared[a]):
                    errors.append('Argument "%s" on field "%s" expects type "%s".' % (a, coord, declared[a]))
            for a, t in declared.items():
                if t.endswith("!") and a not in given:
                    errors.append('Field "%s" argument "%s" of type "%s" is required.' % (coord, a, t))
            target = named(field["type"])
            sub = node.get("selection") or []
            if target in schema:
                if not sub:
                    errors.append('Field "%s" of type "%s" must have a selection.' % (name, field["type"]))
                else:
                    walk(target, sub)
            elif sub:
                errors.append('Field "%s" of type "%s" must not have a selection.' % (name, field["type"]))

    walk("Query", query)
    return errors
''',
    tests=[
        [VSCHEMA, [{"name": "recipe", "selection": [{"name": "name"}]}]],
        [VSCHEMA, [{"name": "recipe", "args": {"id": "r1"}, "selection": [{"name": "title"}, {"name": "author", "selection": [{"name": "name"}]}]}]],
        [VSCHEMA, [{"name": "version"}, {"name": "me", "selection": [{"name": "id"}]}]],
        [VSCHEMA, [{"name": "recipes", "args": {"first": "ten"}, "selection": [{"name": "id"}]}]],
        [VSCHEMA, [{"name": "recipes", "args": {"first": True, "category": 3, "maxRating": 4, "published": 1, "limit": 5}, "selection": [{"name": "id"}]}]],
        [VSCHEMA, [{"name": "recipes", "args": {"first": None, "maxRating": 4.5, "published": False}, "selection": [{"name": "title"}]}]],
        [VSCHEMA, [{"name": "recipe", "args": {"id": None}, "selection": [{"name": "id"}]}]],
        [VSCHEMA, [{"name": "recipe", "args": {"id": 7}}]],
        [VSCHEMA, [{"name": "me"}, {"name": "version", "selection": [{"name": "major"}]}]],
        [VSCHEMA, [{"name": "cooks", "args": {"x": 1}, "selection": [{"name": "nope"}]}, {"name": "version"}]],
        [VSCHEMA, [{"name": "me", "selection": [{"name": "recipes", "selection": [
            {"name": "reviews", "args": {"minStars": "5"}, "selection": [{"name": "stars"}, {"name": "by", "selection": []}, {"name": "text"}]},
            {"name": "title", "args": {"upper": True}},
            {"name": "author"}]}]}]],
        [VSCHEMA, []],
        [VSCHEMA, [{"name": "recipe", "args": {"slug": "x", "id": True}, "selection": [{"name": "minutes", "selection": [{"name": "zzz"}]}]}]],
        [VSCHEMA, [{"name": "me", "selection": [{"name": "recipes", "selection": [{"name": "author", "selection": [{"name": "recipes", "selection": [{"name": "reviews", "args": {"first": 2}, "selection": [{"name": "stars"}]}]}]}]}]}]],
    ],
    examples=2,
    wrong_solutions=[
        '''def validate(schema, query):
    errors = []
    def walk(parent, selection):
        for node in selection:
            field = schema[parent].get(node["name"])
            if field is None:
                errors.append('Cannot query field "%s" on type "%s".' % (node["name"], parent))
                continue
            target = field["type"].replace("[", "").replace("]", "").replace("!", "")
            if target in schema and node.get("selection"):
                walk(target, node["selection"])
    walk("Query", query)
    return errors
''',
        '''def validate(schema, query):
    errors = []
    def named(t):
        return t.replace("[", "").replace("]", "").replace("!", "")
    def fits(value, t):
        if t.endswith("!"):
            return value is not None and fits(value, t[:-1])
        if value is None:
            return True
        if t == "Int":
            return isinstance(value, int)
        if t == "Float":
            return isinstance(value, (int, float))
        if t == "String":
            return isinstance(value, str)
        if t == "Boolean":
            return isinstance(value, bool)
        if t == "ID":
            return isinstance(value, (str, int))
        return True
    def walk(parent, selection):
        for node in selection:
            name = node["name"]
            field = schema[parent].get(name)
            if field is None:
                errors.append('Cannot query field "%s" on type "%s".' % (name, parent))
                continue
            coord = parent + "." + name
            given = node.get("args") or {}
            declared = field.get("args") or {}
            for a, v in given.items():
                if a not in declared:
                    errors.append('Unknown argument "%s" on field "%s".' % (a, coord))
                elif not fits(v, declared[a]):
                    errors.append('Argument "%s" on field "%s" expects type "%s".' % (a, coord, declared[a]))
            for a, t in declared.items():
                if t.endswith("!") and a not in given:
                    errors.append('Field "%s" argument "%s" of type "%s" is required.' % (coord, a, t))
            target = named(field["type"])
            sub = node.get("selection") or []
            if target in schema:
                if not sub:
                    errors.append('Field "%s" of type "%s" must have a selection.' % (name, field["type"]))
                else:
                    walk(target, sub)
            elif sub:
                errors.append('Field "%s" of type "%s" must not have a selection.' % (name, field["type"]))
    walk("Query", query)
    return errors
''',
        '''def validate(schema, query):
    errors = []
    def named(t):
        return t.replace("[", "").replace("]", "").replace("!", "")
    def walk(parent, selection):
        for node in selection:
            name = node["name"]
            field = schema[parent].get(name)
            if field is None:
                errors.append('Cannot query field "%s" on type "%s".' % (name, parent))
            else:
                coord = parent + "." + name
                given = node.get("args") or {}
                declared = field.get("args") or {}
                for a, t in declared.items():
                    if t.endswith("!") and a not in given:
                        errors.append('Field "%s" argument "%s" of type "%s" is required.' % (coord, a, t))
                for a in given:
                    if a not in declared:
                        errors.append('Unknown argument "%s" on field "%s".' % (a, coord))
            target = named(field["type"]) if field else None
            sub = node.get("selection") or []
            if target in schema:
                if not sub:
                    errors.append('Field "%s" of type "%s" must have a selection.' % (name, field["type"]))
                else:
                    walk(target, sub)
            elif sub and field:
                errors.append('Field "%s" of type "%s" must not have a selection.' % (name, field["type"]))
    walk("Query", query)
    return errors
''',
    ],
    guide=dict(
        prereqs="`gql-type-check`, the lessons *Types, scalars, enums, lists and non-null* and *Introspection and abstract syntax trees* (validation walks the query tree).",
        intuition="Validation is a guided walk. You hold two things side by side: where you are in the query, and which *type* you are standing on in the schema. At every field you ask the schema four questions (does it exist, are the arguments right, are required ones present, is the selection sensible), and then the schema tells you which type to stand on for the children. No data is touched: validation happens before execution.",
        hints=[
            "Write `walk(parent_type, selection)`; start it with `walk(\"Query\", query)`.",
            "After reporting an unknown field, `continue`. You cannot check its arguments or children because you do not know its type.",
            "The type to use for the children is the field's type string with `[`, `]` and `!` removed.",
        ],
        brute_force="Check only that every field name exists somewhere in the schema. This accepts `Query { title }` because `title` exists on `Recipe`: names only mean something relative to their parent type.",
        approach="""For each node: look up `schema[parent][name]`; run the argument checks (supplied order, then missing required in declared order); decide object vs leaf; recurse.

**Dry run** `recipe { name }` (no arguments):

| step | check | error added |
|---|---|---|
| 1 | `Query.recipe` exists | none |
| 2 | supplied args: none | none |
| 3 | declared `id: ID!` not supplied | `Field "Query.recipe" argument "id" of type "ID!" is required.` |
| 4 | `Recipe` is an object, selection given → walk children on `Recipe` | |
| 5 | `Recipe.name` unknown | `Cannot query field "name" on type "Recipe".` |""",
        complexity="Time O(n + a) for n field nodes and a total arguments (declared plus supplied): each is examined once with O(1) dictionary lookups. Space O(d) recursion depth plus the error list.",
        pitfalls="- Recursing into the children of an unknown field (there is no type to check them against).\n- Accepting `True` for `Int` (bool is a subclass of int in Python).\n- Reporting a missing required argument when it was supplied as `None`: that is a *wrong type* error, not a *missing* one.\n- Using the full type string `[Recipe!]!` as the dictionary key instead of the named type `Recipe`.",
        follow_up="Add fragments (type conditions must exist; spreads must be possible) and variables (each variable used must be defined and type-compatible).",
    ),
),
dict(
    id="gql-non-null-propagation",
    title="Null propagation for non-null fields",
    difficulty="Hard",
    pattern="Execution",
    entry="apply_non_null",
    description=r"""
When a resolver fails or returns nothing for a field declared **non-null** (`String!`), GraphQL cannot put `null` there:
that would break the promise in the schema. Instead the `null` *bubbles up* to the nearest parent that is allowed to be null.

`apply_non_null(data, shape)`

- `data`: the raw result dictionary, where `None` marks a field that came back empty.
- `shape`: `{field name: node}` describing the selected fields of the root. A node is a dictionary with optional keys:
  `"nonNull"` (bool, default `False`), `"fields"` (`{name: node}` for an object) and `"items"` (a node describing each
  element of a list).

Complete each value depth-first, fields in `shape` order, list items in index order:

1. If the value is `None` (or the key is missing) and the node is nullable → the result is `None`.
2. If the value is `None` and the node is `nonNull` → record the error
   `{"message": "Cannot return null for non-nullable field.", "path": [...]}` and start bubbling.
3. Bubbling: the object or list that directly contains the failed position becomes `None` as a whole, and **completion of
   the rest of that object or list stops** (no more errors are recorded inside it). If that object or list is itself
   `nonNull`, the bubbling continues to *its* container. One failure produces exactly one error.
4. If bubbling reaches the root, `data` is `None`.

`path` lists the field names and list indexes from the root to the position that was null.
Only fields named in `shape` appear in the output. Return `{"data": ..., "errors": [...]}`.

**Example:** shape `{"recipe": {"fields": {"title": {"nonNull": True}}}, "version": {}}`, data
`{"recipe": {"title": None}, "version": "1"}` →
`{"data": {"recipe": None, "version": "1"}, "errors": [{"message": "Cannot return null for non-nullable field.", "path": ["recipe", "title"]}]}`
""",
    starter='''def apply_non_null(data, shape):
    pass
''',
    solution='''def apply_non_null(data, shape):
    errors = []

    class Bubble(Exception):
        pass

    def complete(value, node, path):
        if value is None:
            if node.get("nonNull"):
                errors.append({"message": "Cannot return null for non-nullable field.", "path": path})
                raise Bubble()
            return None
        try:
            if "fields" in node:
                out = {}
                for name, child in node["fields"].items():
                    out[name] = complete(value.get(name), child, path + [name])
                return out
            if "items" in node:
                return [complete(v, node["items"], path + [i]) for i, v in enumerate(value)]
            return value
        except Bubble:
            if node.get("nonNull"):
                raise
            return None

    return {"data": complete(data, {"fields": shape}, []), "errors": errors}
''',
    tests=[
        [{"recipe": {"title": None}, "version": "1"}, {"recipe": {"fields": {"title": {"nonNull": True}}}, "version": {}}],
        [NN_GOOD, NN_SHAPE],
        [_nn(recipe__title=None), NN_SHAPE],
        [_nn(recipe__author__name=None), NN_SHAPE],
        [_nn(recipe__author__city="Leeds", recipe__minutes=None, recipe__reviews=None), NN_SHAPE],
        [_nn(recipe__reviews__1__stars=None), NN_SHAPE],
        [_nn(recipe__reviews__0__by__name=None), NN_SHAPE],
        [_nn(recipe__tags=["a", None, "c"]), NN_SHAPE],
        [_nn(version=None), NN_SHAPE],
        [_nn(recipe=None), NN_SHAPE],
        [_nn(recipe__id=None, recipe__title=None, recipe__tags=None), NN_SHAPE],
        [_nn(recipe__reviews__0__by__name=None, recipe__reviews__1=None, recipe__tags=[]), NN_SHAPE],
        [_nn(recipe__reviews=[None, {"stars": None}]), NN_SHAPE],
        [{"a": {"b": {"c": None}}, "z": 1}, {"a": {"nonNull": True, "fields": {"b": {"nonNull": True, "fields": {"c": {"nonNull": True}}}}}, "z": {}}],
        [{"rows": [[1, 2], [3, None]], "other": [[None]], "extra": 5},
         {"rows": {"items": {"nonNull": True, "items": {"nonNull": True}}}, "other": {"nonNull": True, "items": {"items": {}}}}],
        [{}, {"a": {}, "b": {"fields": {"c": {"nonNull": True}}}}],
    ],
    examples=2,
    wrong_solutions=[
        '''def apply_non_null(data, shape):
    errors = []
    def complete(value, node, path):
        if value is None:
            if node.get("nonNull"):
                errors.append({"message": "Cannot return null for non-nullable field.", "path": path})
            return None
        if "fields" in node:
            return {n: complete(value.get(n), c, path + [n]) for n, c in node["fields"].items()}
        if "items" in node:
            return [complete(v, node["items"], path + [i]) for i, v in enumerate(value)]
        return value
    return {"data": complete(data, {"fields": shape}, []), "errors": errors}
''',
        '''def apply_non_null(data, shape):
    errors = []
    class Bubble(Exception):
        pass
    def complete(value, node, path):
        if value is None:
            if node.get("nonNull"):
                errors.append({"message": "Cannot return null for non-nullable field.", "path": path})
                raise Bubble()
            return None
        if "fields" in node:
            out = {}
            for name, child in node["fields"].items():
                out[name] = complete(value.get(name), child, path + [name])
            return out
        if "items" in node:
            return [complete(v, node["items"], path + [i]) for i, v in enumerate(value)]
        return value
    try:
        return {"data": complete(data, {"fields": shape}, []), "errors": errors}
    except Bubble:
        return {"data": None, "errors": errors}
''',
        '''def apply_non_null(data, shape):
    errors = []
    class Bubble(Exception):
        pass
    def complete(value, node, path):
        if value is None:
            if node.get("nonNull"):
                errors.append({"message": "Cannot return null for non-nullable field.", "path": path})
                raise Bubble()
            return None
        if "fields" in node:
            out = {}
            for name, child in node["fields"].items():
                try:
                    out[name] = complete(value.get(name), child, path + [name])
                except Bubble:
                    if child.get("nonNull"):
                        raise
                    out[name] = None
            return out
        if "items" in node:
            res = []
            for i, v in enumerate(value):
                try:
                    res.append(complete(v, node["items"], path + [i]))
                except Bubble:
                    res.append(None)
            return res
        return value
    try:
        return {"data": complete(data, {"fields": shape}, []), "errors": errors}
    except Bubble:
        return {"data": None, "errors": errors}
''',
    ],
    guide=dict(
        prereqs="The lesson *Types, scalars, enums, lists and non-null* (the section on what `!` promises), recursion, and Python exceptions (`raise` / `try` / `except`).",
        intuition="A non-null field is a promise: 'you will never see null here'. When the server cannot keep it, the only honest move is to remove the whole object that contains the broken promise, by making *that* null. If that container was also promised non-null, the problem moves up again. Think of a blown fuse: the nearest fuse that is allowed to trip (a nullable position) cuts the power to everything below it and protects everything above it.",
        hints=[
            "An exception is a natural model for bubbling: raise at the failed position, and catch it at each container to decide whether to absorb it or re-raise.",
            "A container absorbs the bubble (returns `None`) if it is nullable; otherwise it re-raises.",
            "Treat the root as a nullable object node `{\"fields\": shape}` so the same function handles 'data becomes null'.",
        ],
        brute_force="Complete the whole tree leaving `None` everywhere, then repeatedly scan the tree for a non-null position containing `None` and null out its parent, until nothing changes. It needs many passes, and getting the 'stop completing siblings, one error per failure' rule right is hard after the fact.",
        approach="""`complete(value, node, path)`:

1. `None` + nonNull → append error with `path`, raise `Bubble`.
2. `None` + nullable → `None`.
3. Otherwise complete children (object fields in shape order, or list items); if a `Bubble` escapes from a child, this node returns `None` when nullable or re-raises when nonNull.

**Dry run**: `recipe.reviews[1].stars` is `None`. `stars` is nonNull, review item is nonNull, `reviews` list is nullable.

| position | nullable? | action |
|---|---|---|
| `recipe.reviews.1.stars` | no | record error, raise |
| `recipe.reviews.1` (object) | no | re-raise |
| `recipe.reviews` (list) | yes | absorb → `reviews: None` |
| `recipe.tags`, later fields | | continue normally |""",
        complexity="Time O(n) in the number of positions in the shape applied to the data; each is completed at most once. Space O(d) for recursion depth plus the output.",
        pitfalls="- Putting `None` into the non-null position and carrying on: the response then violates the schema.\n- Catching the bubble in the parent loop based on the *child's* nullability. The child raising means the child could not be null; the question is whether the *current container* can.\n- A null item in `[T!]` nulls the **list**, not the item.\n- Recording a second error for siblings after the container has already been nulled.",
        follow_up="Real servers also attach `locations` (line and column in the query) to each error. Newer proposals (`@semanticNonNull`, client-controlled nullability) let clients choose where errors stop.",
    ),
),
]
