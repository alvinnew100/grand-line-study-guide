"""GraphQL track problems, part 7: depth, complexity, schema evolution, stitching and REST conversion."""


def _chain(n, leaf="id"):
    node = {"name": leaf}
    for i in range(n - 1):
        node = {"name": "f%d" % i, "selection": [node]}
    return [node]


DFRAGS = {
    "Card": {"selection": [{"name": "id"}, {"name": "title"}]},
    "WithAuthor": {"selection": [{"spread": "Card"}, {"name": "author", "selection": [{"name": "name"}, {"name": "recipes", "selection": [{"spread": "Card"}]}]}]},
    "LoopA": {"selection": [{"name": "friend", "selection": [{"spread": "LoopB"}]}]},
    "LoopB": {"selection": [{"name": "friend", "selection": [{"spread": "LoopA"}]}]},
    "Self": {"selection": [{"name": "x"}, {"spread": "Self"}]},
    "Empty": {"selection": []},
}

OLD = {
    "Query": {"recipe": "Recipe", "recipes": "[Recipe!]!", "legacyFeed": "[Recipe]"},
    "Recipe": {"id": "ID!", "title": "String!", "cookTime": "Int", "author": "Cook!", "rating": "Float"},
    "Cook": {"id": "ID!", "name": "String", "email": "String!"},
    "Badge": {"label": "String"},
}
NEW = {
    "Query": {"recipe": "Recipe", "recipes": "RecipeConnection!", "search": "[Recipe!]!"},
    "Recipe": {"id": "ID!", "title": "String!", "minutes": "Int", "author": "Cook", "rating": "Float!"},
    "Cook": {"id": "ID!", "name": "String!", "email": "String"},
    "RecipeConnection": {"edges": "[RecipeEdge!]!"},
}

DSCHEMA = {
    "Query": {
        "recipes": {"type": "[Recipe!]!"},
        "recipe": {"type": "Recipe"},
        "legacyFeed": {"type": "[Recipe]", "deprecated": "Use recipes."},
        "me": {"type": "Cook"},
    },
    "Recipe": {
        "id": {"type": "ID!"},
        "title": {"type": "String!"},
        "cookTime": {"type": "Int", "deprecated": "Use minutes."},
        "minutes": {"type": "Int"},
        "author": {"type": "Cook!"},
        "stars": {"type": "Float", "deprecated": "Use rating."},
    },
    "Cook": {
        "id": {"type": "ID!"},
        "name": {"type": "String!"},
        "handle": {"type": "String", "deprecated": ""},
        "recipes": {"type": "[Recipe!]!"},
    },
}
OPS = [
    {"client": "web", "query": [{"name": "recipes", "selection": [{"name": "title"}, {"name": "cookTime"}]}]},
    {"client": "ios", "query": [{"name": "legacyFeed", "selection": [{"name": "cookTime"}, {"name": "author", "selection": [{"name": "handle"}]}]}]},
    {"client": "web", "query": [{"name": "recipe", "selection": [{"name": "cookTime"}, {"name": "minutes"}]}, {"name": "me", "selection": [{"name": "recipes", "selection": [{"name": "cookTime"}]}]}]},
    {"client": "android", "query": [{"name": "legacyFeed", "selection": [{"name": "id"}]}]},
]

REST = [
    {"name": "recipe", "fields": {"id": "string", "title": "string", "cook_time_minutes": "integer", "rating": "number",
                                  "is_published": "boolean", "author_id": "ref:cook", "tag_ids": "refs:tag"},
     "required": ["id", "title", "author_id"]},
    {"name": "cook", "fields": {"id": "string", "display_name": "string"}, "required": ["id"]},
    {"name": "tag", "fields": {"id": "string", "label": "string"}},
]

PROBLEMS = [
dict(
    id="gql-query-depth",
    title="Query depth and depth limiting",
    difficulty="Medium",
    pattern="Security",
    entry="check_depth",
    description=r"""
Because a schema is a graph with cycles (`Recipe.author → Cook.recipes → Recipe.author …`), a client can write a query
that nests for ever. Servers defend themselves by measuring the **depth** of a query before running it.

`check_depth(query, fragments, max_depth)`

- `query`: a list of items. An item is a field node `{"name": ..., "selection": [...]}` (`selection` optional) or a
  fragment spread `{"spread": "Name"}`.
- `fragments`: `{name: {"selection": [...]}}`.

**Depth** of a selection list: 0 if it is empty; otherwise the largest item depth, where

- a field node has depth `1 +` the depth of its own selection;
- a spread has the depth of the fragment's selection (a spread adds **no** level of its own).

If following spreads ever re-enters a fragment that is already being expanded (a fragment cycle), the query is invalid:
return `{"depth": None, "allowed": False}`.

Otherwise return `{"depth": d, "allowed": d <= max_depth}`.

**Example:** `recipes { title author { name } }` has depth 3. With `max_depth = 2` → `{"depth": 3, "allowed": False}`.
""",
    starter='''def check_depth(query, fragments, max_depth):
    pass
''',
    solution='''def check_depth(query, fragments, max_depth):
    class Cycle(Exception):
        pass

    def depth(selection, active):
        best = 0
        for item in selection:
            if "spread" in item:
                name = item["spread"]
                if name in active:
                    raise Cycle()
                d = depth(fragments[name]["selection"], active | {name})
            else:
                d = 1 + depth(item.get("selection") or [], active)
            if d > best:
                best = d
        return best

    try:
        d = depth(query, frozenset())
    except Cycle:
        return {"depth": None, "allowed": False}
    return {"depth": d, "allowed": d <= max_depth}
''',
    tests=[
        [[{"name": "recipes", "selection": [{"name": "title"}, {"name": "author", "selection": [{"name": "name"}]}]}], {}, 2],
        [[{"name": "recipes", "selection": [{"name": "title"}, {"name": "author", "selection": [{"name": "name"}]}]}], {}, 3],
        [[], {}, 0],
        [[{"name": "version"}], {}, 0],
        [[{"name": "a"}, {"name": "b", "selection": [{"name": "c", "selection": [{"name": "d"}]}]}, {"name": "e", "selection": [{"name": "f"}]}], {}, 5],
        [[{"name": "recipe", "selection": [{"spread": "Card"}]}], DFRAGS, 2],
        [[{"name": "recipe", "selection": [{"spread": "WithAuthor"}]}], DFRAGS, 3],
        [[{"spread": "Card"}, {"spread": "Empty"}], DFRAGS, 1],
        [[{"name": "me", "selection": [{"spread": "LoopA"}]}], DFRAGS, 100],
        [[{"name": "me", "selection": [{"spread": "Self"}]}], DFRAGS, 100],
        [[{"name": "a", "selection": [{"spread": "Card"}]}, {"name": "b", "selection": [{"spread": "Card"}, {"name": "c", "selection": [{"spread": "Card"}]}]}], DFRAGS, 3],
        [_chain(200), {}, 199],
        [_chain(200), {}, 200],
        [[{"name": "x", "selection": [{"spread": "Empty"}]}], DFRAGS, 1],
    ],
    examples=2,
    wrong_solutions=[
        '''def check_depth(query, fragments, max_depth):
    def depth(selection):
        best = 0
        for item in selection:
            if "spread" in item:
                d = 1 + depth(fragments[item["spread"]]["selection"])
            else:
                d = 1 + depth(item.get("selection") or [])
            best = max(best, d)
        return best
    try:
        d = depth(query)
    except RecursionError:
        return {"depth": None, "allowed": False}
    return {"depth": d, "allowed": d <= max_depth}
''',
        '''def check_depth(query, fragments, max_depth):
    seen = set()
    bad = [False]
    def depth(selection):
        best = 0
        for item in selection:
            if "spread" in item:
                if item["spread"] in seen:
                    bad[0] = True
                    continue
                seen.add(item["spread"])
                d = depth(fragments[item["spread"]]["selection"])
            else:
                d = 1 + depth(item.get("selection") or [])
            best = max(best, d)
        return best
    d = depth(query)
    if bad[0]:
        return {"depth": None, "allowed": False}
    return {"depth": d, "allowed": d <= max_depth}
''',
        '''def check_depth(query, fragments, max_depth):
    def depth(selection, active):
        total = 0
        for item in selection:
            if "spread" in item:
                if item["spread"] in active:
                    return None
                d = depth(fragments[item["spread"]]["selection"], active | {item["spread"]})
            else:
                d = depth(item.get("selection") or [], active)
                d = None if d is None else d + 1
            if d is None:
                return None
            total = d if total == 0 else total
        return total
    d = depth(query, frozenset())
    if d is None:
        return {"depth": None, "allowed": False}
    return {"depth": d, "allowed": d <= max_depth}
''',
    ],
    guide=dict(
        prereqs="The lessons *Trees as graphs, and graphs in the real world* (height of a tree) and *Security and monitoring*; recursion; Python sets.",
        intuition="A query is a tree, and its depth is the height of that tree: the number of fields on the longest path from the top to a leaf. Fragments are shortcuts drawn on the tree: opening one pastes its fields in at the same level, so it costs no level itself. A fragment that (directly or through others) contains itself would paste for ever, so it must be detected and rejected.",
        hints=[
            "Depth of a list = max over items; depth of a field = 1 + depth of its children; depth of nothing = 0.",
            "For cycles, track the fragments on the *current path* of expansion, not every fragment ever seen. Using the same fragment twice in different places is perfectly legal.",
            "Pass the set of active fragments down as an argument and extend it with `active | {name}`, so that it shrinks back automatically when the call returns.",
        ],
        brute_force="First inline all fragments into one big tree, then measure it. Inlining can blow up exponentially when fragments spread fragments, and it loops for ever on a cycle unless you add the same detection anyway.",
        approach="""**Dry run** `recipes { title author { name } }`:

| node | children depth | node depth |
|---|---|---|
| name | 0 | 1 |
| author | 1 | 2 |
| title | 0 | 1 |
| recipes | max(1, 2) = 2 | 3 |

Depth 3; allowed only if `max_depth >= 3`.""",
        complexity="Time O(n) in the number of nodes visited after expanding spreads (each use of a fragment is walked again; memoise fragment depths for O(nodes + fragments)). Space O(depth).",
        pitfalls="- Adding 1 for a spread overstates the depth.\n- A global 'seen' set flags two harmless uses of the same fragment as a cycle.\n- Summing sibling depths instead of taking the maximum.\n- Relying on `RecursionError` to detect cycles also rejects legal deep queries.",
        follow_up="Depth alone misses wide queries: `recipes(first: 10000) { title }` is shallow but huge. See `gql-complexity-score`.",
    ),
),
dict(
    id="gql-complexity-score",
    title="Query complexity with list multipliers",
    difficulty="Medium",
    pattern="Security",
    entry="complexity",
    description=r"""
A depth limit does not stop a shallow query that asks for 10,000 items. A **complexity** score estimates how much work a
query will cause, so the server can refuse or rate-limit expensive requests before running them.

`complexity(query, costs)`

- `query`: a list of field nodes `{"name": ..., "args": {...}, "selection": [...]}` (`args` and `selection` optional).
- `costs`: `{field name: cost}`; a field not listed costs **1**.

The score of a field node is

$$\text{score}(f) = \text{cost}(f) + m \times \sum_{c \in \text{children}} \text{score}(c)$$

where the multiplier $m$ is the integer value of the argument `first` if the node has one, otherwise of the argument `last`
if it has one, otherwise 1. (The field itself is fetched once; each of its `m` items needs every child.)

Return the sum of the scores of the top-level nodes.

**Example:** `recipes(first: 10) { title author { name } }` with no custom costs →
`1 + 10 × (1 + (1 + 1 × 1)) = 31`.
""",
    starter='''def complexity(query, costs):
    pass
''',
    solution='''def complexity(query, costs):
    def score(node):
        args = node.get("args") or {}
        if "first" in args:
            m = args["first"]
        elif "last" in args:
            m = args["last"]
        else:
            m = 1
        children = sum(score(c) for c in node.get("selection") or [])
        return costs.get(node["name"], 1) + m * children

    return sum(score(n) for n in query)
''',
    tests=[
        [[{"name": "recipes", "args": {"first": 10}, "selection": [{"name": "title"}, {"name": "author", "selection": [{"name": "name"}]}]}], {}],
        [[{"name": "version"}], {}],
        [[], {}],
        [[{"name": "recipes", "args": {"first": 10}, "selection": [{"name": "title"}]}, {"name": "me", "selection": [{"name": "name"}]}], {"me": 5, "title": 0}],
        [[{"name": "recipes", "args": {"first": 20}, "selection": [{"name": "reviews", "args": {"last": 5}, "selection": [{"name": "stars"}, {"name": "by", "selection": [{"name": "name"}]}]}]}], {}],
        [[{"name": "recipes", "args": {"first": 0}, "selection": [{"name": "title"}, {"name": "author", "selection": [{"name": "name"}]}]}], {"recipes": 3}],
        [[{"name": "recipes", "args": {"first": 3, "last": 50}, "selection": [{"name": "id"}]}], {}],
        [[{"name": "recipes", "args": {"category": "SOUP"}, "selection": [{"name": "id"}, {"name": "title"}]}], {}],
        [[{"name": "search", "args": {"last": 4}, "selection": [{"name": "id"}]}], {"search": 10, "id": 2}],
        [[{"name": "cooks", "args": {"first": 100}, "selection": [{"name": "recipes", "args": {"first": 100}, "selection": [{"name": "reviews", "args": {"first": 100}, "selection": [{"name": "stars"}]}]}]}], {}],
        [[{"name": "a", "args": {"first": 2}, "selection": [{"name": "b", "args": {"first": 3}}, {"name": "c", "selection": [{"name": "d", "args": {"first": 4}, "selection": [{"name": "e"}, {"name": "e"}]}]}]}], {"e": 7, "c": 0}],
        [[{"name": "x", "args": {"first": 5}}], {}],
    ],
    examples=2,
    wrong_solutions=[
        '''def complexity(query, costs):
    def score(node):
        return costs.get(node["name"], 1) + sum(score(c) for c in node.get("selection") or [])
    return sum(score(n) for n in query)
''',
        '''def complexity(query, costs):
    def score(node):
        args = node.get("args") or {}
        m = args.get("first") or args.get("last") or 1
        children = sum(score(c) for c in node.get("selection") or [])
        return m * (costs.get(node["name"], 1) + children)
    return sum(score(n) for n in query)
''',
        '''def complexity(query, costs):
    def score(node):
        args = node.get("args") or {}
        m = args.get("first") or args.get("last") or 1
        children = sum(score(c) for c in node.get("selection") or [])
        return costs.get(node["name"], 1) + m * children
    return sum(score(n) for n in query)
''',
    ],
    guide=dict(
        prereqs="`gql-n-plus-one-count` (lists multiply the work below them), `gql-query-depth`, and the lesson *Security and monitoring*.",
        intuition="Price a restaurant order before cooking it. Each dish has a price; 'ten of those, each with two sides' multiplies the sides by ten. The page size argument (`first` / `last`) is the 'ten of those'. The total tells the kitchen whether to accept the order.",
        hints=[
            "Score one node with a recursive function; the query score is the sum over the top-level nodes.",
            "The multiplier applies to the *children's* total, not to the field's own cost.",
            "`first: 0` is a real value that makes the children free. Test for the key with `in`, not with truthiness.",
        ],
        brute_force="Execute the query and count the fields actually resolved. Accurate, but by then the expensive work is already done: the point of a complexity score is to decide *before* execution, using only the query text and the schema.",
        approach="""**Dry run** `recipes(first: 10) { title author { name } }`:

| node | own cost | m | children total | score |
|---|---|---|---|---|
| name | 1 | 1 | 0 | 1 |
| author | 1 | 1 | 1 | 2 |
| title | 1 | 1 | 0 | 1 |
| recipes | 1 | 10 | 1 + 2 = 3 | 31 |""",
        complexity="Time O(n) for n nodes; space O(d) for the recursion depth.",
        pitfalls="- Ignoring the multiplier treats `first: 1` and `first: 10000` as the same cost.\n- Multiplying the field's own cost as well overcounts.\n- `args.get(\"first\") or ...` skips a legitimate `0` and falls through to `last`.\n- Unbounded lists (no `first`) score as 1 here; real servers give them a large assumed size or require a page size argument.",
        follow_up="GitHub's public GraphQL API rate-limits by a score computed much like this one. How would you turn the score into a budget of points per hour per API key?",
    ),
),
dict(
    id="gql-schema-stitch",
    title="Merge two schemas and detect conflicts",
    difficulty="Medium",
    pattern="Schema composition",
    entry="stitch",
    description=r"""
Large organisations split their graph between teams and **compose** the pieces into one schema that clients see
(schema stitching, and its successor, federation). The composition step must notice when two teams disagree.

`stitch(a, b)` receives two schemas of the form `{type name: {field name: type string}}` and returns

```
{"schema": merged, "conflicts": [sorted list of strings]}
```

Rules:

- A type that exists in only one schema is copied.
- A type in both schemas gets the union of the fields.
- A field defined in both with the **same** type string is fine.
- A field defined in both with **different** type strings is a conflict. Record `"Type.field: <type in a> vs <type in b>"`
  and keep the type from `a` in the merged schema.
- Do not modify `a` or `b`.

**Example:** `a = {"Recipe": {"id": "ID!", "title": "String!"}}`, `b = {"Recipe": {"id": "ID!", "reviews": "[Review!]!"}, "Review": {"stars": "Int!"}}` →
merged `Recipe` has `id`, `title`, `reviews`; `Review` is copied; no conflicts.
""",
    starter='''def stitch(a, b):
    pass
''',
    solution='''def stitch(a, b):
    merged = {t: dict(fields) for t, fields in a.items()}
    conflicts = []
    for t, fields in b.items():
        target = merged.setdefault(t, {})
        for f, type_str in fields.items():
            if f not in target:
                target[f] = type_str
            elif target[f] != type_str:
                conflicts.append("%s.%s: %s vs %s" % (t, f, target[f], type_str))
    return {"schema": merged, "conflicts": sorted(conflicts)}
''',
    tests=[
        [{"Recipe": {"id": "ID!", "title": "String!"}}, {"Recipe": {"id": "ID!", "reviews": "[Review!]!"}, "Review": {"stars": "Int!"}}],
        [{"Query": {"recipes": "[Recipe!]!"}, "Recipe": {"id": "ID!"}}, {"Query": {"cooks": "[Cook!]!"}, "Cook": {"id": "ID!"}}],
        [{"Recipe": {"id": "ID!", "rating": "Float"}}, {"Recipe": {"id": "ID", "rating": "Int"}}],
        [{}, {}],
        [{"A": {"x": "Int"}}, {}],
        [{}, {"A": {"x": "Int"}}],
        [{"A": {"x": "Int"}}, {"A": {"x": "Int"}}],
        [{"Z": {"b": "Int", "a": "Int"}, "A": {"k": "String"}}, {"A": {"k": "String!"}, "Z": {"a": "[Int]", "b": "Int!", "c": "ID"}}],
        [{"A": {}}, {"A": {"x": "Int"}, "B": {}}],
        [OLD, NEW],
        [NEW, OLD],
        [{"T%d" % i: {"f": "Int", "g%d" % i: "ID"} for i in range(50)}, {"T%d" % i: {"f": "Int" if i % 7 else "Float", "h": "String"} for i in range(25, 75)}],
    ],
    examples=2,
    wrong_solutions=[
        '''def stitch(a, b):
    merged = dict(a)
    merged.update(b)
    return {"schema": merged, "conflicts": []}
''',
        '''def stitch(a, b):
    merged = {t: dict(fields) for t, fields in a.items()}
    conflicts = []
    for t, fields in b.items():
        target = merged.setdefault(t, {})
        for f, type_str in fields.items():
            if f in target and target[f] != type_str:
                conflicts.append("%s.%s: %s vs %s" % (t, f, target[f], type_str))
            target[f] = type_str
    return {"schema": merged, "conflicts": sorted(conflicts)}
''',
        '''def stitch(a, b):
    merged = {t: dict(fields) for t, fields in a.items()}
    conflicts = []
    for t, fields in b.items():
        target = merged.setdefault(t, {})
        for f, type_str in fields.items():
            if f not in target:
                target[f] = type_str
            elif target[f] != type_str:
                conflicts.append("%s.%s: %s vs %s" % (t, f, target[f], type_str))
    return {"schema": merged, "conflicts": conflicts}
''',
    ],
    guide=dict(
        prereqs="Python dictionaries (`setdefault`, copying with `dict(x)`), and the federation section of *Caching, federation and rate limiting*.",
        intuition="Two teams each drew part of the same map. Laying the sheets on top of each other is easy where they cover different ground, and harmless where they agree. The only interesting spots are where both drew the same road going to different places: those must be reported to humans, not silently resolved.",
        hints=[
            "Start from a copy of `a` that is deep enough: a new outer dictionary **and** a new dictionary per type.",
            "For each field of `b`: three cases (new field, same type, different type).",
            "Sort the conflict list at the end so the output does not depend on dictionary order.",
        ],
        brute_force="`merged = {**a, **b}` replaces whole types: every field that only `a` defined on a shared type is lost, and no conflict is ever reported.",
        approach="""**Dry run** `a = {"Recipe": {"id": "ID!", "rating": "Float"}}`, `b = {"Recipe": {"id": "ID", "rating": "Int"}}`:

| field | in merged? | same? | action |
|---|---|---|---|
| Recipe.id | yes (`ID!`) | no (`ID`) | conflict `Recipe.id: ID! vs ID` |
| Recipe.rating | yes (`Float`) | no (`Int`) | conflict `Recipe.rating: Float vs Int` |

Merged keeps `a`'s types.""",
        complexity="Time O(F_a + F_b) for the total number of fields, plus O(c log c) to sort c conflicts. Space O(F_a + F_b).",
        pitfalls="- A shallow copy (`dict(a)`) shares the inner dictionaries, so adding `b`'s fields mutates `a`.\n- Letting the last writer win hides real disagreements.\n- `ID!` and `ID` are different types: nullability is part of the contract.",
        follow_up="Apollo Federation goes further: each subgraph declares which fields it *owns*, entities are matched across subgraphs by `@key` fields, and some differences (for example one subgraph being stricter about nullability) are allowed by explicit composition rules.",
    ),
),
dict(
    id="gql-schema-diff",
    title="Classify schema changes as breaking or safe",
    difficulty="Medium",
    pattern="Schema evolution",
    entry="diff_schemas",
    description=r"""
GraphQL APIs are normally evolved without version numbers. That only works if every change is checked: will it break a
client that was written against the old schema?

`diff_schemas(old, new)` compares two schemas `{type name: {field name: type string}}` (output types only) and returns a
list of changes `{"kind": ..., "path": ..., "breaking": bool}`, **sorted by `path`, then `kind`**.

| situation | kind | path | breaking |
|---|---|---|---|
| type only in `old` | `TYPE_REMOVED` | `Type` | yes |
| type only in `new` | `TYPE_ADDED` | `Type` | no |
| field only in `old` (type exists in both) | `FIELD_REMOVED` | `Type.field` | yes |
| field only in `new` (type exists in both) | `FIELD_ADDED` | `Type.field` | no |
| new type string is the old one plus a trailing `!` | `FIELD_BECAME_NON_NULL` | `Type.field` | no |
| old type string is the new one plus a trailing `!` | `FIELD_BECAME_NULLABLE` | `Type.field` | yes |
| any other difference in the type string | `FIELD_TYPE_CHANGED` | `Type.field` | yes |

Do not report the individual fields of a removed or added type. Identical schemas give `[]`.

Why the two nullability rows differ: these are **output** fields. Promising *more* (never null) cannot surprise a client;
promising *less* (now possibly null) crashes clients that did not check.

**Example:** `old = {"Cook": {"name": "String", "email": "String!"}}`, `new = {"Cook": {"name": "String!", "email": "String"}}` →
`[{"kind": "FIELD_BECAME_NULLABLE", "path": "Cook.email", "breaking": True}, {"kind": "FIELD_BECAME_NON_NULL", "path": "Cook.name", "breaking": False}]`
""",
    starter='''def diff_schemas(old, new):
    pass
''',
    solution='''def diff_schemas(old, new):
    changes = []

    def add(kind, path, breaking):
        changes.append({"kind": kind, "path": path, "breaking": breaking})

    for t, fields in old.items():
        if t not in new:
            add("TYPE_REMOVED", t, True)
            continue
        for f, before in fields.items():
            path = t + "." + f
            if f not in new[t]:
                add("FIELD_REMOVED", path, True)
                continue
            after = new[t][f]
            if after == before:
                continue
            if after == before + "!":
                add("FIELD_BECAME_NON_NULL", path, False)
            elif before == after + "!":
                add("FIELD_BECAME_NULLABLE", path, True)
            else:
                add("FIELD_TYPE_CHANGED", path, True)
        for f in new[t]:
            if f not in fields:
                add("FIELD_ADDED", t + "." + f, False)
    for t in new:
        if t not in old:
            add("TYPE_ADDED", t, False)
    changes.sort(key=lambda c: (c["path"], c["kind"]))
    return changes
''',
    tests=[
        [{"Cook": {"name": "String", "email": "String!"}}, {"Cook": {"name": "String!", "email": "String"}}],
        [OLD, NEW],
        [NEW, OLD],
        [OLD, OLD],
        [{}, {}],
        [{}, {"A": {"x": "Int"}}],
        [{"A": {"x": "Int"}}, {}],
        [{"A": {"x": "[Int]", "y": "[Int!]", "z": "[Int]!"}}, {"A": {"x": "[Int!]", "y": "[Int]!", "z": "[Int]"}}],
        [{"A": {"x": "Int"}}, {"A": {"x": "Int!!"}}],
        [{"A": {"b": "Int", "a": "Int"}, "B": {"x": "ID"}}, {"A": {"c": "Int"}, "C": {"x": "ID"}}],
        [{"A": {"x": "Recipe"}}, {"A": {"x": "Cook"}}],
        [{"T%02d" % i: {"f": "Int", "g": "String!"} for i in range(30)}, {"T%02d" % i: {"f": "Int!" if i % 2 else "Int", "h": "ID"} for i in range(10, 40)}],
    ],
    examples=1,
    wrong_solutions=[
        '''def diff_schemas(old, new):
    changes = []
    for t in old:
        if t not in new:
            changes.append({"kind": "TYPE_REMOVED", "path": t, "breaking": True})
            continue
        for f in old[t]:
            p = t + "." + f
            if f not in new[t]:
                changes.append({"kind": "FIELD_REMOVED", "path": p, "breaking": True})
            elif new[t][f] != old[t][f]:
                changes.append({"kind": "FIELD_TYPE_CHANGED", "path": p, "breaking": True})
        for f in new[t]:
            if f not in old[t]:
                changes.append({"kind": "FIELD_ADDED", "path": t + "." + f, "breaking": False})
    for t in new:
        if t not in old:
            changes.append({"kind": "TYPE_ADDED", "path": t, "breaking": False})
    changes.sort(key=lambda c: (c["path"], c["kind"]))
    return changes
''',
        '''def diff_schemas(old, new):
    changes = []
    def add(kind, path, breaking):
        changes.append({"kind": kind, "path": path, "breaking": breaking})
    for t, fields in old.items():
        if t not in new:
            add("TYPE_REMOVED", t, True)
            continue
        for f, before in fields.items():
            path = t + "." + f
            if f not in new[t]:
                add("FIELD_REMOVED", path, True)
                continue
            after = new[t][f]
            if after == before:
                continue
            if after.replace("!", "") == before.replace("!", ""):
                if after.count("!") > before.count("!"):
                    add("FIELD_BECAME_NON_NULL", path, False)
                else:
                    add("FIELD_BECAME_NULLABLE", path, True)
            else:
                add("FIELD_TYPE_CHANGED", path, True)
        for f in new[t]:
            if f not in fields:
                add("FIELD_ADDED", t + "." + f, False)
    for t in new:
        if t not in old:
            add("TYPE_ADDED", t, False)
    changes.sort(key=lambda c: (c["path"], c["kind"]))
    return changes
''',
        '''def diff_schemas(old, new):
    changes = []
    def add(kind, path, breaking):
        changes.append({"kind": kind, "path": path, "breaking": breaking})
    for t, fields in old.items():
        if t not in new:
            add("TYPE_REMOVED", t, True)
            for f in fields:
                add("FIELD_REMOVED", t + "." + f, True)
            continue
        for f, before in fields.items():
            path = t + "." + f
            if f not in new[t]:
                add("FIELD_REMOVED", path, True)
                continue
            after = new[t][f]
            if after == before:
                continue
            if after == before + "!":
                add("FIELD_BECAME_NON_NULL", path, True)
            elif before == after + "!":
                add("FIELD_BECAME_NULLABLE", path, False)
            else:
                add("FIELD_TYPE_CHANGED", path, True)
        for f in new[t]:
            if f not in fields:
                add("FIELD_ADDED", t + "." + f, False)
    for t in new:
        if t not in old:
            add("TYPE_ADDED", t, False)
    return sorted(changes, key=lambda c: (c["path"], c["kind"]))
''',
    ],
    guide=dict(
        prereqs="The lesson *Designing a schema live: versioning, errors and pagination styles*; dictionary membership tests; sorting with a tuple key.",
        intuition="A schema is a contract. A change is **breaking** when a query or a piece of client code that worked yesterday can fail today. Taking things away breaks; adding things does not. For output fields, making a promise stronger (`String` → `String!`) is safe and weakening it (`String!` → `String`) is not, because client code compiled against 'never null' has no null check.",
        hints=[
            "Three passes are enough: types in old (removed, or compare fields), fields added on shared types, types only in new.",
            "Compare type strings exactly first; then test the two special nullability shapes with `after == before + \"!\"` and `before == after + \"!\"`.",
            "Sort once at the end with `key=lambda c: (c[\"path\"], c[\"kind\"])`.",
        ],
        brute_force="Flatten both schemas into sets of `(type, field, type string)` triples and take set differences. You get 'something changed' but cannot tell a removed field from a retyped one without joining the two difference sets again, which is the per-field comparison in disguise.",
        approach="""**Dry run** of the example:

| path | before | after | rule | breaking |
|---|---|---|---|---|
| Cook.name | `String` | `String!` | after = before + `!` | no |
| Cook.email | `String!` | `String` | before = after + `!` | yes |

Sorted by path: `Cook.email` first, then `Cook.name`.""",
        complexity="Time O(F + c log c) for F total fields and c changes. Space O(c).",
        pitfalls="- Counting `!` characters treats `[Int]!` → `[Int!]` as a nullability change with equal counts; it is a different type (`FIELD_TYPE_CHANGED`).\n- Swapping which nullability direction is breaking. (For *input* arguments the rule is reversed: making an argument required is the breaking direction.)\n- Reporting every field of a removed type floods the report.\n- Forgetting to sort.",
        follow_up="Tools such as GraphQL Inspector, GraphQL Hive and Apollo schema checks run this comparison in CI, and go one step further by checking real traffic: a 'breaking' change to a field nobody has queried in 30 days is safe in practice.",
    ),
),
dict(
    id="gql-deprecation-report",
    title="Deprecated field usage report",
    difficulty="Medium",
    pattern="Schema evolution",
    entry="deprecation_report",
    description=r"""
Before a deprecated field can be deleted, someone has to prove that no client still uses it. Build that report from a
log of operations.

`deprecation_report(schema, operations)`

- `schema`: `{type name: {field name: {"type": type string, "deprecated": reason}}}`. The `"deprecated"` key is present
  (with a reason string, possibly empty) only on deprecated fields. The root type is `"Query"`.
- `operations`: a list of `{"client": name, "query": [field nodes]}`; a field node is `{"name": ..., "selection": [...]}`.

Walk every operation from `Query`, using each field's named type (the type string without `[`, `]`, `!`) to find the
type of its children. Fields that do not exist in the schema are skipped together with their children.

Return

```
{"used": [{"field": "Type.field", "reason": ..., "uses": n, "clients": [sorted unique client names]}, ...],
 "safeToRemove": [sorted "Type.field" names of deprecated fields with zero uses]}
```

`uses` counts every occurrence in every operation. Sort `used` by `uses` descending, then by `field` ascending.

**Example:** two operations from `web` select `Recipe.cookTime` once each, one from `ios` selects it once →
`{"field": "Recipe.cookTime", "reason": "Use minutes.", "uses": 3, "clients": ["ios", "web"]}`.
""",
    starter='''def deprecation_report(schema, operations):
    pass
''',
    solution='''def deprecation_report(schema, operations):
    stats = {}

    def named(t):
        return t.replace("[", "").replace("]", "").replace("!", "")

    def walk(type_name, selection, client):
        fields = schema.get(type_name, {})
        for node in selection:
            field = fields.get(node["name"])
            if field is None:
                continue
            if "deprecated" in field:
                key = type_name + "." + node["name"]
                entry = stats.setdefault(key, {"uses": 0, "clients": set()})
                entry["uses"] += 1
                entry["clients"].add(client)
            walk(named(field["type"]), node.get("selection") or [], client)

    for op in operations:
        walk("Query", op["query"], op["client"])

    used, safe = [], []
    for t, fields in schema.items():
        for f, field in fields.items():
            if "deprecated" not in field:
                continue
            key = t + "." + f
            if key in stats:
                used.append({"field": key, "reason": field["deprecated"], "uses": stats[key]["uses"], "clients": sorted(stats[key]["clients"])})
            else:
                safe.append(key)
    used.sort(key=lambda r: (-r["uses"], r["field"]))
    return {"used": used, "safeToRemove": sorted(safe)}
''',
    tests=[
        [DSCHEMA, OPS],
        [DSCHEMA, []],
        [DSCHEMA, OPS[:1]],
        [DSCHEMA, [OPS[3]]],
        [DSCHEMA, [{"client": "web", "query": [{"name": "recipes", "selection": [{"name": "title"}, {"name": "minutes"}]}]}]],
        [DSCHEMA, [{"client": "cli", "query": [{"name": "nope", "selection": [{"name": "cookTime"}]}, {"name": "me", "selection": [{"name": "handle"}, {"name": "handle"}]}]}]],
        [DSCHEMA, [{"client": "b", "query": [{"name": "recipe", "selection": [{"name": "stars"}]}]}, {"client": "a", "query": [{"name": "recipe", "selection": [{"name": "stars"}, {"name": "cookTime"}]}]}, {"client": "a", "query": [{"name": "recipe", "selection": [{"name": "cookTime"}]}]}]],
        [DSCHEMA, [{"client": "deep", "query": [{"name": "me", "selection": [{"name": "recipes", "selection": [{"name": "author", "selection": [{"name": "recipes", "selection": [{"name": "stars"}, {"name": "author", "selection": [{"name": "handle"}]}]}]}]}]}]}]],
        [{"Query": {"a": {"type": "String"}}}, [{"client": "x", "query": [{"name": "a"}]}]],
        [{}, [{"client": "x", "query": [{"name": "a"}]}]],
        [DSCHEMA, [{"client": "c%d" % (i % 4), "query": [{"name": "legacyFeed", "selection": [{"name": "cookTime"}] * (i % 3)}]} for i in range(40)]],
    ],
    examples=1,
    wrong_solutions=[
        '''def deprecation_report(schema, operations):
    stats = {}
    def walk(selection, client):
        for node in selection:
            for t, fields in schema.items():
                if node["name"] in fields and "deprecated" in fields[node["name"]]:
                    e = stats.setdefault(t + "." + node["name"], {"uses": 0, "clients": set()})
                    e["uses"] += 1
                    e["clients"].add(client)
            walk(node.get("selection") or [], client)
    for op in operations:
        walk(op["query"], op["client"])
    used, safe = [], []
    for t, fields in schema.items():
        for f, field in fields.items():
            if "deprecated" in field:
                k = t + "." + f
                if k in stats:
                    used.append({"field": k, "reason": field["deprecated"], "uses": stats[k]["uses"], "clients": sorted(stats[k]["clients"])})
                else:
                    safe.append(k)
    used.sort(key=lambda r: (-r["uses"], r["field"]))
    return {"used": used, "safeToRemove": sorted(safe)}
''',
        '''def deprecation_report(schema, operations):
    stats = {}
    def named(t):
        return t.replace("[", "").replace("]", "").replace("!", "")
    def walk(type_name, selection, client):
        fields = schema.get(type_name, {})
        for node in selection:
            field = fields.get(node["name"])
            if field is None:
                continue
            if field.get("deprecated"):
                key = type_name + "." + node["name"]
                entry = stats.setdefault(key, {"uses": 0, "clients": []})
                entry["uses"] += 1
                entry["clients"].append(client)
            walk(named(field["type"]), node.get("selection") or [], client)
    for op in operations:
        walk("Query", op["query"], op["client"])
    used, safe = [], []
    for t, fields in schema.items():
        for f, field in fields.items():
            if not field.get("deprecated"):
                continue
            key = t + "." + f
            if key in stats:
                used.append({"field": key, "reason": field["deprecated"], "uses": stats[key]["uses"], "clients": sorted(stats[key]["clients"])})
            else:
                safe.append(key)
    used.sort(key=lambda r: (-r["uses"], r["field"]))
    return {"used": used, "safeToRemove": sorted(safe)}
''',
    ],
    guide=dict(
        prereqs="`gql-validate-query` (walking a query alongside the schema); sets; sorting with a tuple key and a negated number for descending order.",
        intuition="A field name alone means nothing: `cookTime` is only deprecated *on `Recipe`*. So the walk must always know which type it is standing on, exactly as in validation. Along the way, keep a tally per `Type.field`. Afterwards, every deprecated field with an empty tally is safe to delete.",
        hints=[
            "Reuse the shape of the validator: `walk(type_name, selection, client)` with the schema telling you the children's type.",
            "Store `uses` as a counter and `clients` as a set; convert the set to a sorted list at the end.",
            "Test `\"deprecated\" in field`, not the truthiness of the reason: an empty reason string still means deprecated.",
        ],
        brute_force="Search the text of each query for the names of deprecated fields. This counts `Cook.handle` whenever any type has a field called `handle`, and it misses the type context entirely.",
        approach="""**Dry run** for the operation `legacyFeed { cookTime author { handle } }` from `ios`:

| node | on type | deprecated? | tally |
|---|---|---|---|
| legacyFeed | Query | yes | `Query.legacyFeed` 1 {ios} |
| cookTime | Recipe | yes | `Recipe.cookTime` 1 {ios} |
| author | Recipe | no | |
| handle | Cook | yes | `Cook.handle` 1 {ios} |""",
        complexity="Time O(N + D log D) for N field nodes over all operations and D deprecated fields. Space O(D + distinct clients).",
        pitfalls="- Matching by field name without the parent type.\n- Descending into children of an unknown field with a stale type.\n- Listing a client twice.\n- An empty deprecation reason `\"\"` is falsy in Python.",
        follow_up="In SDL this is `cookTime: Int @deprecated(reason: \"Use minutes.\")`. Real registries (Apollo GraphOS, GraphQL Hive) build this report from production traffic over a time window, per client name and version.",
    ),
),
dict(
    id="gql-rest-to-schema",
    title="Convert a REST resource description to a schema",
    difficulty="Medium",
    pattern="API design",
    entry="rest_to_schema",
    description=r"""
A common first step when moving from REST to GraphQL is to translate the existing resources into types, turning foreign
keys into real connections.

`rest_to_schema(resources)` receives a list of resources:

```
{"name": "recipe", "fields": {"id": "string", "title": "string", "author_id": "ref:cook", ...}, "required": ["id", "title"]}
```

`required` is optional (default: nothing is required). Resource and field names are `snake_case`.

Build a schema descriptor (a dictionary):

**One object type per resource.** The type name is the resource name in `PascalCase` (`recipe_step` → `RecipeStep`). For each field, in order:

| REST kind | GraphQL field name | GraphQL type |
|---|---|---|
| field called `id` (any kind) | `id` | `ID` |
| `string` / `integer` / `number` / `boolean` | camelCase of the name | `String` / `Int` / `Float` / `Boolean` |
| `ref:other` (one related item) | camelCase of the name without a trailing `_id` | `Other` in PascalCase |
| `refs:other` (many related items) | camelCase of the name without a trailing `_ids`, plus `s` | `[Other!]!` |

Append `!` to the type when the REST field name is listed in `required`. (`refs` fields are always `[Other!]!`, required or not.)

**A `Query` type** with two fields per resource, where `x` is the camelCase resource name and `X` its type:

- `x`: `{"type": "X", "args": {"id": "ID!"}}`
- `xs`: `{"type": "[X!]!", "args": {}}`

Return `{"Query": {...}, "Recipe": {field: type string, ...}, ...}`.

**Example:** the resource above gives `"Recipe": {"id": "ID!", "title": "String!", "author": "Cook"}` and Query fields `recipe` and `recipes`.
""",
    starter='''def rest_to_schema(resources):
    pass
''',
    solution='''SCALARS = {"string": "String", "integer": "Int", "number": "Float", "boolean": "Boolean"}

def camel(name):
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])

def pascal(name):
    return "".join(p.capitalize() for p in name.split("_"))

def rest_to_schema(resources):
    schema = {"Query": {}}
    for res in resources:
        type_name = pascal(res["name"])
        required = set(res.get("required") or [])
        fields = {}
        for raw, kind in res["fields"].items():
            if kind.startswith("refs:"):
                base = raw[:-4] if raw.endswith("_ids") else raw
                fields[camel(base) + "s"] = "[" + pascal(kind[5:]) + "!]!"
                continue
            if raw == "id":
                name, type_str = "id", "ID"
            elif kind.startswith("ref:"):
                name = camel(raw[:-3] if raw.endswith("_id") else raw)
                type_str = pascal(kind[4:])
            else:
                name, type_str = camel(raw), SCALARS[kind]
            fields[name] = type_str + ("!" if raw in required else "")
        schema[type_name] = fields
        single = camel(res["name"])
        schema["Query"][single] = {"type": type_name, "args": {"id": "ID!"}}
        schema["Query"][single + "s"] = {"type": "[" + type_name + "!]!", "args": {}}
    return schema
''',
    tests=[
        [[{"name": "recipe", "fields": {"id": "string", "title": "string", "author_id": "ref:cook"}, "required": ["id", "title"]}]],
        [REST],
        [[]],
        [[{"name": "tag", "fields": {"id": "integer", "label": "string"}}]],
        [[{"name": "recipe_step", "fields": {"id": "string", "step_number": "integer", "recipe_id": "ref:recipe", "is_optional": "boolean", "duration_in_minutes": "number"},
           "required": ["step_number", "recipe_id", "is_optional"]}]],
        [[{"name": "cook", "fields": {"id": "string", "favourite_recipe_ids": "refs:recipe", "mentor": "ref:cook", "badges": "refs:skill_badge", "home_kitchen_id": "ref:shared_kitchen"},
           "required": ["id", "favourite_recipe_ids", "mentor"]}]],
        [[{"name": "x", "fields": {}}]],
        [[{"name": "a", "fields": {"id": "string"}, "required": []}, {"name": "b", "fields": {"a_id": "ref:a", "a_ids": "refs:a", "score": "number"}, "required": ["score", "a_ids"]}]],
        [[{"name": "meal_plan_entry", "fields": {"id": "string", "planned_for_day": "string"}, "required": ["id", "planned_for_day"]}]],
        [[{"name": "r%d" % i, "fields": {"id": "string", "field_%d_value" % i: "integer", "next_id": "ref:r%d" % ((i + 1) % 12)}, "required": ["id"] if i % 2 else []} for i in range(12)]],
    ],
    examples=1,
    wrong_solutions=[
        '''SCALARS = {"string": "String", "integer": "Int", "number": "Float", "boolean": "Boolean"}
def rest_to_schema(resources):
    schema = {"Query": {}}
    for res in resources:
        t = res["name"].capitalize()
        req = set(res.get("required") or [])
        fields = {}
        for raw, kind in res["fields"].items():
            if kind.startswith("refs:"):
                fields[raw[:-4] + "s"] = "[" + kind[5:].capitalize() + "!]!"
            elif kind.startswith("ref:"):
                fields[raw[:-3]] = kind[4:].capitalize() + ("!" if raw in req else "")
            elif raw == "id":
                fields["id"] = "ID" + ("!" if raw in req else "")
            else:
                fields[raw] = SCALARS[kind] + ("!" if raw in req else "")
        schema[t] = fields
        schema["Query"][res["name"]] = {"type": t, "args": {"id": "ID!"}}
        schema["Query"][res["name"] + "s"] = {"type": "[" + t + "!]!", "args": {}}
    return schema
''',
        '''SCALARS = {"string": "String", "integer": "Int", "number": "Float", "boolean": "Boolean"}
def camel(name):
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])
def pascal(name):
    return "".join(p.capitalize() for p in name.split("_"))
def rest_to_schema(resources):
    schema = {"Query": {}}
    for res in resources:
        type_name = pascal(res["name"])
        required = set(res.get("required") or [])
        fields = {}
        for raw, kind in res["fields"].items():
            if kind.startswith("refs:"):
                fields[camel(raw.replace("_ids", "")) + "s"] = "[" + pascal(kind[5:]) + "!]!"
                continue
            if kind.startswith("ref:"):
                name, type_str = camel(raw.replace("_id", "")), pascal(kind[4:])
            elif raw == "id":
                name, type_str = "id", "ID"
            else:
                name, type_str = camel(raw), SCALARS[kind]
            fields[name] = type_str + "!"
        schema[type_name] = fields
        single = camel(res["name"])
        schema["Query"][single] = {"type": type_name, "args": {"id": "ID!"}}
        schema["Query"][single + "s"] = {"type": "[" + type_name + "!]!", "args": {}}
    return schema
''',
        '''SCALARS = {"string": "String", "integer": "Int", "number": "Float", "boolean": "Boolean"}
def camel(name):
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])
def pascal(name):
    return "".join(p.capitalize() for p in name.split("_"))
def rest_to_schema(resources):
    schema = {"Query": {}}
    for res in resources:
        type_name = pascal(res["name"])
        required = set(res.get("required") or [])
        fields = {}
        for raw, kind in res["fields"].items():
            if kind.startswith("refs:"):
                fields[camel(raw) + "s"] = "[ID!]!"
                continue
            if kind.startswith("ref:"):
                name, type_str = camel(raw), "ID"
            elif raw == "id":
                name, type_str = "id", "ID"
            else:
                name, type_str = camel(raw), SCALARS[kind]
            fields[name] = type_str + ("!" if raw in required else "")
        schema[type_name] = fields
        single = camel(res["name"])
        schema["Query"][single] = {"type": type_name, "args": {"id": "ID!"}}
        schema["Query"][single + "s"] = {"type": "[" + type_name + "!]!", "args": {}}
    return schema
''',
    ],
    guide=dict(
        prereqs="String methods (`split`, `capitalize`, `startswith`, `endswith`, slicing); the lessons *REST in plain words* and *REST vs GraphQL vs gRPC*.",
        intuition="REST responses carry **foreign keys**: `author_id: \"c1\"` tells you where to go for the next request. A graph schema replaces the key with the thing itself: `author: Cook`. That single translation, id-field to connection, is what turns a set of separate resources into one connected graph that a client can walk in a single query.",
        hints=[
            "Write `camel` and `pascal` helpers first: split on `_`, capitalise the right parts, join.",
            "Decide the *kind* of field before the name: `refs:` first, then the `id` field, then `ref:`, then scalars.",
            "Remove a suffix with `endswith` and slicing (`raw[:-3]`), not with `replace`, which would also remove `_id` from the middle of a name.",
        ],
        brute_force="Copy every REST field as a scalar, leaving `authorId: ID`. The result is a valid schema but not a graph: clients are back to making a second request per id, which is the under-fetching problem GraphQL was meant to remove.",
        approach="""**Dry run** for `recipe` with `{"id": "string", "title": "string", "author_id": "ref:cook"}`, required `id`, `title`:

| REST field | rule | GraphQL field |
|---|---|---|
| `id` | id field, required | `id: ID!` |
| `title` | scalar, required | `title: String!` |
| `author_id` | ref, strip `_id`, not required | `author: Cook` |

Query gets `recipe(id: ID!): Recipe` and `recipes: [Recipe!]!`.""",
        complexity="Time O(total characters of all field names); space O(size of the output).",
        pitfalls="- `str.capitalize()` on the whole name gives `Recipe_step`, not `RecipeStep`.\n- `replace(\"_id\", \"\")` corrupts names such as `planned_idea_id`.\n- The *REST* name decides whether a field is required, not the converted name.\n- A `ref` field that does not end in `_id` (`mentor`) keeps its name.",
        follow_up="Real converters start from an OpenAPI document. Naive plurals (`category` → `categorys`) are a known weakness: which fields would you rename by hand, and where would you add pagination arguments?",
    ),
),
]
