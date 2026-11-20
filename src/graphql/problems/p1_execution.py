"""GraphQL track problems, part 1: executing queries against plain data."""

COOK = {"id": "c1", "name": "Amara", "city": "Leeds", "followers": 120,
        "kitchen": {"name": "Blue Door", "seats": 12, "address": {"street": "4 Mill Lane", "postcode": "LS1"}},
        "mentor": None}

POT = {
    "__typename": "Query",
    "featured": {"__typename": "Recipe", "id": "r1", "title": "Lentil soup", "minutes": 35,
                 "author": {"__typename": "Cook", "id": "c1", "name": "Amara"}},
    "feed": [
        {"__typename": "Recipe", "id": "r1", "title": "Lentil soup", "minutes": 35, "tags": ["vegan", "soup"]},
        {"__typename": "Collection", "id": "k1", "name": "Weeknight", "size": 4},
        None,
        {"__typename": "Recipe", "id": "r2", "title": "Flatbread", "minutes": 20, "tags": []},
    ],
    "grid": [[{"__typename": "Recipe", "id": "r1", "title": "Lentil soup"}], [],
             [{"__typename": "Collection", "id": "k1", "name": "Weeknight"}, None]],
    "nothing": None,
}
FRAGS = {
    "RecipeCard": {"on": "Recipe", "selection": [{"name": "id"}, {"name": "title"}]},
    "CollectionCard": {"on": "Collection", "selection": [{"name": "id"}, {"name": "name"}]},
    "Timed": {"on": "Recipe", "selection": [{"spread": "RecipeCard"}, {"name": "minutes"}]},
    "AuthorName": {"on": "Recipe", "selection": [{"name": "author", "selection": [{"name": "name"}]}]},
    "AuthorId": {"on": "Recipe", "selection": [{"name": "author", "selection": [{"name": "id"}]}]},
    "RootBits": {"on": "Query", "selection": [{"name": "nothing"}]},
}

ARGDATA = {
    "id": "c1",
    "name": "Amara",
    "height": {"__args": {"": 1.7, 'unit:"FOOT"': 5.58, 'unit:"METRE"': 1.7}},
    "recipes": {"__args": {
        "first:1": [{"id": "r1", "title": "Lentil soup"}],
        "first:2": [{"id": "r1", "title": "Lentil soup"}, {"id": "r2", "title": "Flatbread"}],
        'category:"SOUP",first:2': [{"id": "r1", "title": "Lentil soup"}],
        "": [{"id": "r1", "title": "Lentil soup"}, {"id": "r2", "title": "Flatbread"}, {"id": "r3", "title": "Plum cake"}],
    }},
    "avatar": {"__args": {"round:true,size:64": "a-64-round.png", "round:false,size:64": "a-64.png"}},
    "best": {"__args": {"": {"id": "r3", "title": "Plum cake", "photo": {"__args": {"width:100": "p100.jpg"}}}}},
}

PROBLEMS = [
dict(
    id="gql-select-fields",
    title="Return only the fields that were asked for",
    difficulty="Easy",
    pattern="Query execution",
    entry="select",
    description=r"""
The heart of GraphQL is one promise: **the response has the same shape as the request, and nothing extra**.
Build the smallest possible version of that promise.

Write `select(data, selection)`.

- `data` is a plain dictionary (it stands for one object on the server), or `None`.
- `selection` is a dictionary describing what the client wants. Each key is a field name. Its value is either
  `True` (a **leaf**: return the stored value as it is) or another selection dictionary (go one level deeper
  into a nested object).

Rules:

1. The result contains exactly the keys of `selection`, in the same order.
2. A field that is not stored in `data` comes back as `None`.
3. If a nested object is `None` (or missing), the result for that field is `None`; do not go deeper.
4. If `data` itself is `None`, return `None`. An empty selection gives `{}`.
5. Do not change `data`.

**Example:** `select({"id": "c1", "name": "Amara", "city": "Leeds"}, {"name": True})` → `{"name": "Amara"}`

**Example:** `select({"name": "Amara", "kitchen": {"name": "Blue Door", "seats": 12}}, {"kitchen": {"seats": True}})` → `{"kitchen": {"seats": 12}}`
""",
    starter='''def select(data, selection):
    # data: dict or None; selection: {"field": True or nested selection}
    pass
''',
    solution='''def select(data, selection):
    if data is None:
        return None
    out = {}
    for name, sub in selection.items():
        value = data.get(name)
        if sub is True or value is None:
            out[name] = value
        else:
            out[name] = select(value, sub)
    return out
''',
    tests=[
        [{"id": "c1", "name": "Amara", "city": "Leeds"}, {"name": True}],
        [COOK, {"kitchen": {"seats": True}}],
        [COOK, {"id": True, "kitchen": {"name": True, "address": {"postcode": True}}}],
        [COOK, {}],
        [None, {"name": True}],
        [COOK, {"nickname": True}],
        [COOK, {"mentor": {"name": True}}],
        [COOK, {"pantry": {"shelves": True}, "name": True}],
        [COOK, {"followers": True, "city": True, "id": True}],
        [{"a": {"b": {"c": {"d": 1, "e": 2}, "x": 0}}}, {"a": {"b": {"c": {"e": True}}}}],
        [{"zero": 0, "empty": "", "no": False}, {"zero": True, "empty": True, "no": True}],
        [COOK, {"kitchen": {}}],
    ],
    examples=2,
    wrong_solutions=[
        '''def select(data, selection):
    return data
''',
        '''def select(data, selection):
    if data is None:
        return None
    return {k: data[k] for k in selection if k in data}
''',
        '''def select(data, selection):
    if data is None:
        return None
    out = {}
    for name, sub in selection.items():
        value = data.get(name)
        out[name] = value if sub is True else select(value or {}, sub)
    return out
''',
    ],
    guide=dict(
        prereqs="Python dictionaries, `dict.get`, and a function that calls itself (recursion). Read the lesson *REST in plain words* first: this problem is the cure for over-fetching.",
        intuition="The selection is a stencil laid over the data. Wherever the stencil has a hole (`True`) the value shows through. Wherever the stencil has a smaller stencil, repeat the same job one level down. The stencil decides the shape; the data only fills it in.",
        hints=[
            "Loop over the *selection*, not over the data. The selection decides which keys exist in the answer.",
            "Use `data.get(name)` so that a missing field becomes `None` instead of raising `KeyError`.",
            "When the selection value is a dictionary and the stored value is not `None`, call `select` again with the nested value and the nested selection.",
        ],
        brute_force="Copy the whole object (`dict(data)`) and delete every key the client did not ask for, repeating for nested objects. It works but walks every stored field, including huge ones nobody requested, and it is easy to forget to add keys that are missing from the data.",
        approach="""Walk the selection once.

1. `data is None` → return `None`.
2. For each `(name, sub)` in the selection: read `value = data.get(name)`.
3. If `sub is True` or the value is `None`, store the value as it is.
4. Otherwise recurse: `select(value, sub)`.

**Dry run** with `data = {"name": "Amara", "kitchen": {"name": "Blue Door", "seats": 12}}` and `selection = {"kitchen": {"seats": True}}`:

| step | name | value | action | result so far |
|---|---|---|---|---|
| 1 | kitchen | `{"name": ..., "seats": 12}` | nested selection → recurse | |
| 1a | seats | `12` | leaf | `{"seats": 12}` |
| 2 | (done) | | | `{"kitchen": {"seats": 12}}` |""",
        complexity="Time O(s) where s is the number of fields in the selection (each is visited once); the size of the stored object does not matter. Extra space O(s) for the result plus O(d) call stack for nesting depth d.",
        pitfalls="- Testing `if value:` instead of `value is None` drops legitimate values such as `0`, `\"\"` and `False`.\n- Looping over the data returns extra keys and loses the client's field order.\n- Turning a `None` nested object into `{}` hides the fact that the object does not exist.",
        follow_up="Next: add aliases and arguments (`gql-aliases-args`), then lists and fragments (`gql-fragments-lists`).",
    ),
),
dict(
    id="gql-aliases-args",
    title="Aliases and arguments",
    difficulty="Easy",
    pattern="Query execution",
    entry="execute",
    description=r"""
Extend the tiny executor with two features of the query language.

`execute(data, selection)` where `selection` is now a **list of field nodes**. A field node is a dictionary:

| key | meaning |
|---|---|
| `"name"` | the field to read (always present) |
| `"alias"` | optional; if present, the result key is the alias instead of the name |
| `"args"` | optional dictionary of argument name → value (strings, integers, booleans) |
| `"selection"` | optional list of child field nodes |

**Arguments.** A stored value may be an *argument table*: a dictionary with the single key `"__args"` whose value maps an
**argument key** to the value to use. Build the argument key from the node's `args` like this: sort the argument names
alphabetically, write each as `name:value` with the value in JSON form (`2`, `"FOOT"`, `true`), and join them with commas.
No arguments gives the empty string `""`. If the table has no entry for the key, the field's value is `None`.
A stored value that is not an argument table ignores any arguments.

**Results.** Use the alias (or the name) as the result key, in selection order. If the value is a list and the node has a
`selection`, apply the selection to every element. `None` values stay `None`. Missing fields are `None`. If `data` is `None`, return `None`.

**Example:** with `data = {"height": {"__args": {"": 1.7, "unit:\"FOOT\"": 5.58}}}` the selection
`[{"name": "height"}, {"name": "height", "alias": "feet", "args": {"unit": "FOOT"}}]` → `{"height": 1.7, "feet": 5.58}`
""",
    starter='''def execute(data, selection):
    # selection: list of {"name", "alias"?, "args"?, "selection"?}
    pass
''',
    solution='''import json

def arg_key(args):
    return ",".join(k + ":" + json.dumps(args[k]) for k in sorted(args))

def execute(data, selection):
    if data is None:
        return None
    out = {}
    for node in selection:
        value = data.get(node["name"])
        if isinstance(value, dict) and "__args" in value:
            value = value["__args"].get(arg_key(node.get("args") or {}))
        key = node.get("alias") or node["name"]
        sub = node.get("selection")
        if sub and value is not None:
            if isinstance(value, list):
                value = [execute(item, sub) for item in value]
            else:
                value = execute(value, sub)
        out[key] = value
    return out
''',
    tests=[
        [ARGDATA, [{"name": "height"}, {"name": "height", "alias": "feet", "args": {"unit": "FOOT"}}]],
        [ARGDATA, [{"name": "name", "alias": "cook"}, {"name": "id"}]],
        [ARGDATA, [{"name": "recipes", "args": {"first": 2}, "selection": [{"name": "title"}]}]],
        [ARGDATA, [{"name": "recipes", "alias": "top", "args": {"first": 1}, "selection": [{"name": "id"}]},
                   {"name": "recipes", "alias": "all", "selection": [{"name": "id"}]}]],
        [ARGDATA, [{"name": "recipes", "args": {"first": 2, "category": "SOUP"}, "selection": [{"name": "title", "alias": "t"}]}]],
        [ARGDATA, [{"name": "avatar", "args": {"size": 64, "round": True}}, {"name": "avatar", "alias": "square", "args": {"size": 64, "round": False}}]],
        [ARGDATA, [{"name": "recipes", "args": {"first": 9}, "selection": [{"name": "title"}]}]],
        [ARGDATA, [{"name": "name", "args": {"upper": True}}]],
        [ARGDATA, [{"name": "best", "selection": [{"name": "title"}, {"name": "photo", "alias": "thumb", "args": {"width": 100}}, {"name": "photo", "args": {"width": 500}}]}]],
        [ARGDATA, [{"name": "missing", "alias": "m", "selection": [{"name": "x"}]}]],
        [None, [{"name": "name"}]],
        [ARGDATA, []],
        [ARGDATA, [{"name": "height", "args": {"unit": "MILE"}}, {"name": "height", "alias": "h2", "args": {}}]],
    ],
    examples=2,
    wrong_solutions=[
        '''import json
def execute(data, selection):
    if data is None:
        return None
    out = {}
    for node in selection:
        value = data.get(node["name"])
        if isinstance(value, dict) and "__args" in value:
            a = node.get("args") or {}
            value = value["__args"].get(",".join(k + ":" + json.dumps(a[k]) for k in a))
        sub = node.get("selection")
        if sub and value is not None:
            value = [execute(i, sub) for i in value] if isinstance(value, list) else execute(value, sub)
        out[node.get("alias") or node["name"]] = value
    return out
''',
        '''import json
def execute(data, selection):
    if data is None:
        return None
    out = {}
    for node in selection:
        value = data.get(node["name"])
        if isinstance(value, dict) and "__args" in value:
            a = node.get("args") or {}
            value = value["__args"].get(",".join(k + ":" + json.dumps(a[k]) for k in sorted(a)))
        sub = node.get("selection")
        if sub and value is not None:
            value = [execute(i, sub) for i in value] if isinstance(value, list) else execute(value, sub)
        out[node["name"]] = value
    return out
''',
        '''def execute(data, selection):
    if data is None:
        return None
    out = {}
    for node in selection:
        value = data.get(node["name"])
        if isinstance(value, dict) and "__args" in value:
            a = node.get("args") or {}
            value = value["__args"].get(",".join(k + ":" + str(a[k]) for k in sorted(a)))
        sub = node.get("selection")
        if sub and value is not None:
            value = [execute(i, sub) for i in value] if isinstance(value, list) else execute(value, sub)
        out[node.get("alias") or node["name"]] = value
    return out
''',
    ],
    guide=dict(
        prereqs="`gql-select-fields`, the lesson *Fields, arguments, aliases and fragments*, and `json.dumps` for writing a value in JSON form.",
        intuition="An argument turns a field from a stored value into a small function: the same field can give different answers. Because one field can now appear twice with different arguments, the two answers would collide under one key, which is exactly why aliases exist. The argument key is the trick real client caches use to tell `recipes(first: 1)` from `recipes(first: 2)`.",
        hints=[
            "Handle one node at a time: find the raw value, then decide the result key, then decide whether to go deeper.",
            "Sort the argument names before joining them, otherwise `{first: 2, category: \"SOUP\"}` and `{category: \"SOUP\", first: 2}` produce different keys.",
            "`json.dumps(True)` is `true`, `json.dumps(\"FOOT\")` is `\"FOOT\"` with the quotes, `json.dumps(2)` is `2`. That is the JSON form the table uses.",
        ],
        brute_force="Special-case each argument (`if name == \"recipes\" and \"first\" in args: ...`). It passes a few tests and collapses as soon as a new field or argument appears. A general key function is shorter than two special cases.",
        approach="""For each node:

1. `value = data.get(name)`.
2. If the value is an argument table, replace it with `table.get(arg_key(args))`.
3. `key = alias or name`.
4. If there is a child selection and the value is not `None`: map over a list, or recurse into an object.
5. Store `out[key] = value`.

**Dry run** for `[{"name": "height"}, {"name": "height", "alias": "feet", "args": {"unit": "FOOT"}}]`:

| node | arg key | looked-up value | result key |
|---|---|---|---|
| height | `""` | 1.7 | `height` |
| height (alias feet) | `unit:"FOOT"` | 5.58 | `feet` |

Result: `{"height": 1.7, "feet": 5.58}`.""",
        complexity="Time O(s + a log a) per node for a selection of s nodes with a arguments each (the sort), multiplied by list lengths where a selection is applied to every element. Space O(size of the result).",
        pitfalls="- Using `str(True)` gives `True`, not the JSON `true`; `str(\"FOOT\")` loses the quotes.\n- Forgetting that a node with no `args` key must still look up the `\"\"` entry.\n- Writing the result under the name instead of the alias makes the second `height` overwrite the first.\n- Applying arguments to a plain stored value: they are ignored, not an error.",
        follow_up="Real servers reject two different fields that would land on the same result key without aliases. How would you detect that?",
    ),
),
dict(
    id="gql-fragments-lists",
    title="Fragments, lists and field merging",
    difficulty="Medium",
    pattern="Query execution",
    entry="run",
    description=r"""
Implement the *collect fields, then execute* step of a GraphQL server for selections that contain **fragment spreads** and
data that contains **lists**.

`run(data, selection, fragments)`

- Every object in `data` is a dictionary with a `"__typename"` key (the root has `"__typename": "Query"`).
- `selection` is a list whose items are either a field node `{"name": ..., "selection": [...]}` (`selection` optional) or
  a spread `{"spread": "FragmentName"}`.
- `fragments` maps a fragment name to `{"on": "TypeName", "selection": [...]}`.

Rules:

1. A spread contributes its fragment's selection **only if** the fragment's `on` type equals the current object's
   `__typename`. Otherwise it contributes nothing. Fragments may spread other fragments.
2. **Collect before executing.** Walk the selection in order and group by field name. A field that appears more than once
   (directly or through fragments) appears once in the result, at the position where it was first seen, and its child
   selections are joined together.
3. Values: `None` stays `None`; a list is mapped element by element (lists may be nested, and may contain `None`);
   a dictionary is executed with the joined child selection; anything else is returned as it is.
4. The field `__typename` can be requested like any other field. Missing fields are `None`.

**Example:** on a feed holding one `Recipe` and one `Collection`, the selection
`[{"name": "feed", "selection": [{"name": "__typename"}, {"spread": "RecipeCard"}]}]` with
`RecipeCard = {"on": "Recipe", "selection": [{"name": "title"}]}` gives
`{"feed": [{"__typename": "Recipe", "title": "Lentil soup"}, {"__typename": "Collection"}]}`.
""",
    starter='''def run(data, selection, fragments):
    pass
''',
    solution='''def run(data, selection, fragments):
    def collect(obj, sel, fields):
        for item in sel:
            if "spread" in item:
                frag = fragments[item["spread"]]
                if frag["on"] == obj.get("__typename"):
                    collect(obj, frag["selection"], fields)
            else:
                fields.setdefault(item["name"], []).extend(item.get("selection") or [])
        return fields

    def complete(value, sub):
        if value is None:
            return None
        if isinstance(value, list):
            return [complete(v, sub) for v in value]
        if isinstance(value, dict):
            return exec_obj(value, sub)
        return value

    def exec_obj(obj, sel):
        out = {}
        for name, sub in collect(obj, sel, {}).items():
            out[name] = complete(obj.get(name), sub)
        return out

    return exec_obj(data, selection)
''',
    tests=[
        [POT, [{"name": "feed", "selection": [{"name": "__typename"}, {"spread": "RecipeCard"}]}], FRAGS],
        [POT, [{"name": "featured", "selection": [{"spread": "RecipeCard"}]}], FRAGS],
        [POT, [{"name": "feed", "selection": [{"spread": "RecipeCard"}, {"spread": "CollectionCard"}]}], FRAGS],
        [POT, [{"name": "featured", "selection": [{"spread": "Timed"}]}], FRAGS],
        [POT, [{"name": "featured", "selection": [{"name": "minutes"}, {"spread": "Timed"}, {"name": "id"}]}], FRAGS],
        [POT, [{"name": "featured", "selection": [{"spread": "AuthorName"}, {"spread": "AuthorId"}]}], FRAGS],
        [POT, [{"name": "featured", "selection": [{"name": "author", "selection": [{"name": "id"}]}, {"name": "title"}, {"spread": "AuthorName"}]}], FRAGS],
        [POT, [{"name": "grid", "selection": [{"spread": "RecipeCard"}, {"name": "__typename"}]}], FRAGS],
        [POT, [{"spread": "RootBits"}, {"name": "nothing", "selection": [{"name": "x"}]}], FRAGS],
        [POT, [{"name": "feed", "selection": [{"name": "tags"}, {"name": "size"}]}], FRAGS],
        [POT, [{"name": "featured", "selection": [{"spread": "CollectionCard"}]}], FRAGS],
        [POT, [], FRAGS],
        [POT, [{"name": "featured", "selection": [{"name": "title"}, {"name": "title"}]}, {"name": "featured", "selection": [{"name": "id"}]}], {}],
    ],
    examples=2,
    wrong_solutions=[
        '''def run(data, selection, fragments):
    def ex(obj, sel):
        out = {}
        for item in sel:
            if "spread" in item:
                out.update(ex(obj, fragments[item["spread"]]["selection"]))
            else:
                out[item["name"]] = comp(obj.get(item["name"]), item.get("selection") or [])
        return out
    def comp(v, sub):
        if v is None: return None
        if isinstance(v, list): return [comp(x, sub) for x in v]
        if isinstance(v, dict): return ex(v, sub)
        return v
    return ex(data, selection)
''',
        '''def run(data, selection, fragments):
    def ex(obj, sel):
        out = {}
        for item in sel:
            if "spread" in item:
                f = fragments[item["spread"]]
                if f["on"] == obj.get("__typename"):
                    out.update(ex(obj, f["selection"]))
            else:
                out[item["name"]] = comp(obj.get(item["name"]), item.get("selection") or [])
        return out
    def comp(v, sub):
        if v is None: return None
        if isinstance(v, list): return [comp(x, sub) for x in v]
        if isinstance(v, dict): return ex(v, sub)
        return v
    return ex(data, selection)
''',
        '''def run(data, selection, fragments):
    def collect(obj, sel, fields):
        for item in sel:
            if "spread" in item:
                frag = fragments[item["spread"]]
                if frag["on"] == obj.get("__typename"):
                    collect(obj, frag["selection"], fields)
            else:
                fields.setdefault(item["name"], []).extend(item.get("selection") or [])
        return fields
    def ex(obj, sel):
        out = {}
        for name, sub in collect(obj, sel, {}).items():
            v = obj.get(name)
            if isinstance(v, list):
                v = [ex(x, sub) for x in v]
            elif isinstance(v, dict):
                v = ex(v, sub)
            out[name] = v
        return out
    return ex(data, selection)
''',
    ],
    guide=dict(
        prereqs="`gql-select-fields`, recursion, and the fragments section of the lesson *Fields, arguments, aliases and fragments*.",
        intuition="A fragment is a named, reusable piece of a selection that only applies to one type. Before the server reads any data for an object it first flattens the selection for *that object's type*: spreads are opened up, and repeated fields are merged into one. Only then does it resolve each distinct field once. Two phases: **collect**, then **execute**.",
        hints=[
            "Write `collect(obj, selection)` that returns an ordered dictionary `field name -> joined child selection`. Python dictionaries keep insertion order, which gives you 'first seen position' for free.",
            "A spread calls `collect` again on the fragment's selection, but only when `fragment[\"on\"] == obj[\"__typename\"]`.",
            "Write a separate `complete(value, child_selection)` that handles `None`, lists (recursively, so nested lists work) and objects.",
        ],
        brute_force="Execute items one by one and `dict.update` the result for each spread. This ignores merging: when two fragments both select `author` with different children, the second overwrites the first and half the data disappears.",
        approach="""1. `collect`: for each item, either open the spread (type condition must match) or append the node's children to `fields[name]`.
2. `exec_obj`: for each collected `(name, children)`, call `complete(obj.get(name), children)`.
3. `complete`: `None` → `None`; list → map `complete`; dict → `exec_obj`; scalar → itself.

**Dry run** for `featured { ...AuthorName ...AuthorId }` on a `Recipe`:

| item | action | collected fields |
|---|---|---|
| `...AuthorName` | type matches, open: `author { name }` | `author: [name]` |
| `...AuthorId` | type matches, open: `author { id }` | `author: [name, id]` |

Then `author` is executed once with `[name, id]` → `{"author": {"name": "Amara", "id": "c1"}}`.""",
        complexity="Time O(total selection nodes visited × objects they apply to); each object in the data is visited once per place it appears in the result. Space O(result size) plus recursion depth.",
        pitfalls="- Skipping the type condition puts `title: None` on a `Collection`.\n- Executing a field at each occurrence instead of merging loses sibling sub-fields.\n- Forgetting `None` inside lists crashes on `None.get`.\n- Handling only one level of list breaks on a list of lists.",
        follow_up="Real GraphQL also has inline fragments (`... on Recipe { title }`) and interface/union type conditions. The collect step is the same.",
    ),
),
]
