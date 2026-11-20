"""GraphQL track problems, part 5: resolvers, authorisation, N+1 and batching."""

RSCHEMA = {
    "Query": {"recipes": "[Recipe!]!", "recipe": "Recipe", "motd": "String", "me": "Cook"},
    "Recipe": {"id": "ID!", "title": "String!", "minutes": "Int", "author": "Cook!", "reviews": "[Review]", "tags": "[String!]!"},
    "Cook": {"id": "ID!", "name": "String!", "recipes": "[Recipe!]!", "mentor": "Cook"},
    "Review": {"id": "ID!", "stars": "Int!", "by": "Cook"},
}
R1 = {"id": "r1", "title": "Lentil soup", "minutes": 35, "tags": ["vegan"], "authorId": "c1"}
R2 = {"id": "r2", "title": "Flatbread", "minutes": 20, "tags": [], "authorId": "c2"}
R3 = {"id": "r3", "title": "Plum cake", "minutes": None, "tags": ["baking", "sweet"], "authorId": "c1"}
C1 = {"id": "c1", "name": "Amara"}
C2 = {"id": "c2", "name": "Bo"}
V1 = {"id": "v1", "stars": 5, "byId": "c2"}
V2 = {"id": "v2", "stars": 3, "byId": "c9"}
RESOLVERS = {
    "Query.recipes": {"root": [R1, R2, R3]},
    "Query.recipe": {"root": R1},
    "Query.me": {},
    "Recipe.author": {"r1": C1, "r2": C2, "r3": C1},
    "Recipe.reviews": {"r1": [V1, None, V2], "r2": []},
    "Cook.recipes": {"c1": [R1, R3], "c2": [R2]},
    "Cook.mentor": {"c2": C1},
    "Review.by": {"v1": C2},
}

AUTH_DATA = {
    "__typename": "Query",
    "version": "1.4",
    "stats": {"__typename": "Stats", "signups": 31, "revenue": 1200},
    "cooks": [
        {"__typename": "Cook", "id": "c1", "ownerId": "c1", "name": "Amara", "email": "amara@example.com",
         "drafts": [{"__typename": "Recipe", "id": "r9", "ownerId": "c1", "title": "Secret stew", "notes": "less salt"}]},
        {"__typename": "Cook", "id": "c2", "ownerId": "c2", "name": "Bo", "email": "bo@example.com", "drafts": []},
        None,
    ],
}
AUTH_RULES = {
    "Query.stats": ["ADMIN"],
    "Stats.revenue": ["FINANCE"],
    "Cook.email": ["ADMIN", "OWNER"],
    "Cook.drafts": ["OWNER"],
    "Recipe.notes": ["OWNER", "EDITOR"],
    "Query.locked": [],
}
AUTH_SEL = {"version": True, "stats": {"signups": True, "revenue": True},
            "cooks": {"name": True, "email": True, "drafts": {"title": True, "notes": True}}}

DB = {"c1": "Amara", "c2": "Bo", "c3": "Chidi", "c4": "Dee", "c5": "Eli"}

PROBLEMS = [
dict(
    id="gql-resolver-chain",
    title="A resolver executor with the default resolver",
    difficulty="Medium",
    pattern="Resolvers",
    entry="execute",
    description=r"""
A GraphQL server answers a query by calling one small function per field, called a **resolver**. The value a resolver
returns becomes the **parent** of the resolvers one level down. This hand-over is the *resolver chain*.

Model each resolver as a lookup table and write the executor.

`execute(schema, resolvers, query)`

- `schema`: `{type name: {field name: type string}}`, root type `"Query"`. Type strings use `!` and `[ ]`.
- `resolvers`: `{"Type.field": table}`. A table maps the **parent object's `"id"`** to the value the resolver returns
  (a missing id means the resolver returns `None`). The parent of the root fields is the object `{"id": "root"}`.
- `query`: a list of field nodes `{"name": ..., "selection": [...]}` (`selection` optional).

For each field on a parent object of type `T`:

1. **Resolve.** If `resolvers` has the key `"T.field"`, the value is `table.get(parent["id"])`.
   Otherwise use the **default resolver**: the value is `parent.get(field)`.
2. **Complete** the value using the field's type string: `None` → `None`; a list type → complete every element with the
   inner type; a type that is a key of `schema` → execute the node's selection with the value as the new parent and that
   type; anything else (a scalar) → the value itself.

The result keys follow the query order. The query is always valid for the schema.

**Example:** with `resolvers = {"Query.recipe": {"root": {"id": "r1", "title": "Lentil soup", "authorId": "c1"}}, "Recipe.author": {"r1": {"id": "c1", "name": "Amara"}}}`,
the query `recipe { title author { name } }` gives `{"recipe": {"title": "Lentil soup", "author": {"name": "Amara"}}}`:
`title` and `name` use the default resolver, `recipe` and `author` use tables.
""",
    starter='''def execute(schema, resolvers, query):
    pass
''',
    solution='''def execute(schema, resolvers, query):
    def resolve(type_name, parent, field):
        table = resolvers.get(type_name + "." + field)
        if table is None:
            return parent.get(field)
        return table.get(parent.get("id"))

    def complete(value, type_str, selection):
        if value is None:
            return None
        if type_str.endswith("!"):
            type_str = type_str[:-1]
        if type_str.startswith("["):
            return [complete(v, type_str[1:-1], selection) for v in value]
        if type_str in schema:
            return run(type_str, value, selection)
        return value

    def run(type_name, parent, selection):
        out = {}
        for node in selection:
            name = node["name"]
            value = resolve(type_name, parent, name)
            out[name] = complete(value, schema[type_name][name], node.get("selection") or [])
        return out

    return run("Query", {"id": "root"}, query)
''',
    tests=[
        [RSCHEMA, RESOLVERS, [{"name": "recipe", "selection": [{"name": "title"}, {"name": "author", "selection": [{"name": "name"}]}]}]],
        [RSCHEMA, RESOLVERS, [{"name": "recipes", "selection": [{"name": "id"}, {"name": "minutes"}]}]],
        [RSCHEMA, RESOLVERS, [{"name": "recipes", "selection": [{"name": "title"}, {"name": "author", "selection": [{"name": "name"}]}]}]],
        [RSCHEMA, RESOLVERS, [{"name": "motd"}, {"name": "me", "selection": [{"name": "name"}]}]],
        [RSCHEMA, RESOLVERS, [{"name": "recipes", "selection": [{"name": "reviews", "selection": [{"name": "stars"}, {"name": "by", "selection": [{"name": "name"}]}]}]}]],
        [RSCHEMA, RESOLVERS, [{"name": "recipe", "selection": [{"name": "tags"}, {"name": "author", "selection": [{"name": "recipes", "selection": [{"name": "title"}, {"name": "tags"}]}]}]}]],
        [RSCHEMA, RESOLVERS, [{"name": "recipes", "selection": [{"name": "author", "selection": [{"name": "mentor", "selection": [{"name": "name"}, {"name": "mentor", "selection": [{"name": "id"}]}]}]}]}]],
        [RSCHEMA, RESOLVERS, []],
        [RSCHEMA, {}, [{"name": "motd"}, {"name": "recipes", "selection": [{"name": "id"}]}]],
        [RSCHEMA, {"Query.motd": {"root": "Soup season"}, "Query.recipes": {"root": []}}, [{"name": "recipes", "selection": [{"name": "id"}]}, {"name": "motd"}]],
        [RSCHEMA, {"Query.recipe": {"root": {"id": "r7", "title": "Stored", "author": {"id": "c7", "name": "Embedded"}}}, "Recipe.title": {"r7": "Computed"}},
         [{"name": "recipe", "selection": [{"name": "title"}, {"name": "id"}, {"name": "author", "selection": [{"name": "name"}]}]}]],
        [RSCHEMA, RESOLVERS, [{"name": "recipe", "selection": [{"name": "author", "selection": [{"name": "recipes", "selection": [{"name": "author", "selection": [{"name": "recipes", "selection": [{"name": "id"}]}]}]}]}]}]],
    ],
    examples=2,
    wrong_solutions=[
        '''def execute(schema, resolvers, query):
    def complete(value, type_str, selection):
        if value is None:
            return None
        type_str = type_str.rstrip("!")
        if type_str.startswith("["):
            return [complete(v, type_str[1:-1], selection) for v in value]
        if type_str in schema:
            return run(type_str, value, selection)
        return value
    def run(type_name, parent, selection):
        out = {}
        for node in selection:
            name = node["name"]
            table = resolvers.get(type_name + "." + name, {})
            out[name] = complete(table.get(parent.get("id")), schema[type_name][name], node.get("selection") or [])
        return out
    return run("Query", {"id": "root"}, query)
''',
        '''def execute(schema, resolvers, query):
    def complete(value, type_str, selection):
        if value is None:
            return None
        type_str = type_str.rstrip("!")
        if type_str.startswith("["):
            return [complete(v, type_str[1:-1], selection) for v in value]
        if type_str in schema:
            return run(type_str, value, selection)
        return value
    def run(type_name, parent, selection):
        out = {}
        for node in selection:
            name = node["name"]
            value = parent.get(name)
            if value is None:
                value = resolvers.get(type_name + "." + name, {}).get(parent.get("id"))
            out[name] = complete(value, schema[type_name][name], node.get("selection") or [])
        return out
    return run("Query", {"id": "root"}, query)
''',
        '''def execute(schema, resolvers, query):
    def run(type_name, parent, selection):
        out = {}
        for node in selection:
            name = node["name"]
            table = resolvers.get(type_name + "." + name)
            value = parent.get(name) if table is None else table.get(parent.get("id"))
            t = schema[type_name][name].replace("[", "").replace("]", "").replace("!", "")
            if value is not None and t in schema:
                if isinstance(value, list):
                    value = [run(t, v, node.get("selection") or []) for v in value]
                else:
                    value = run(t, value, node.get("selection") or [])
            out[name] = value
        return out
    return run("Query", {"id": "root"}, query)
''',
    ],
    guide=dict(
        prereqs="`gql-select-fields`, the lesson *Resolvers, the resolver chain and context*, and the type-string notation from `gql-type-check`.",
        intuition="Execution is a relay race. The root resolver fetches something and hands it on as the `parent` argument of the next runner. Most runners do nothing clever: they read a property with the same name off the object they were handed (the default resolver). You only write a resolver where the stored shape and the schema shape differ, such as turning `authorId` into a whole `author` object.",
        hints=[
            "Split the work into `resolve` (where does the raw value come from?) and `complete` (what do I do with it, given its type?).",
            "A table that exists but has no entry for this parent means the resolver returned `None`. That is different from having no table at all, where you fall back to the parent's own property.",
            "`complete` peels the type string: drop one trailing `!`, then if it starts with `[` map over the list with the inner type.",
        ],
        brute_force="Join everything up front: build one huge nested object containing every recipe with its author with their recipes and so on, then run `gql-select-fields` on it. With cycles in the graph (`Recipe.author.recipes.author…`) that object is infinite. Resolving lazily, only along the paths the query names, is the whole point.",
        approach="""`run(type, parent, selection)` loops over nodes; for each it calls `resolve` then `complete`, and `complete` calls `run` again for object types.

**Dry run** `recipe { title author { name } }`:

| field | resolver used | parent id | raw value |
|---|---|---|---|
| `Query.recipe` | table | root | `{"id": "r1", "title": "Lentil soup", "authorId": "c1"}` |
| `Recipe.title` | default | | `"Lentil soup"` |
| `Recipe.author` | table | r1 | `{"id": "c1", "name": "Amara"}` |
| `Cook.name` | default | | `"Amara"` |""",
        complexity="Time O(number of field resolutions), which is the number of (object, selected field) pairs in the result. Space O(result size + depth).",
        pitfalls="- Using the table only when the parent lacks the property: an explicit resolver always wins over a stored property.\n- Forgetting `None` elements inside lists (`[Review]`).\n- Stripping every `!` and bracket and then guessing list-ness from the value works here, but loses the type information you need for null checks.\n- Mutating the stored objects while building the result.",
        follow_up="Count how many table lookups each query makes: that is `gql-n-plus-one-count`.",
    ),
),
dict(
    id="gql-n-plus-one-count",
    title="Count resolver calls: naive versus batched",
    difficulty="Medium",
    pattern="Performance",
    entry="count_calls",
    description=r"""
The **N+1 problem**: one query fetches a list of N items, and then a resolver runs once *per item* to fetch something
related, making N more database calls. Predict the damage without running anything.

`count_calls(query)` receives a list of field nodes. A node is a dictionary with:

| key | meaning |
|---|---|
| `"name"` | field name |
| `"resolver"` | `True` if this field hits the database when resolved (default `False`: it reads a property for free) |
| `"list"` | if present, the field returns a list of exactly this many objects; if absent, it returns one object or a scalar |
| `"selection"` | child nodes, resolved once for **each** object this field returns |

Root fields are resolved once. Return `{"naive": a, "batched": b}`:

- **naive**: total database calls when every resolver call hits the database on its own. A node with `resolver: True`
  is called once per parent object.
- **batched**: total calls when a DataLoader groups all calls of the *same node* into one. Each node with
  `resolver: True` that is called at least once costs exactly 1.

A node under a list of 0 objects is never called and costs nothing in either mode.

**Example:** `recipes` (resolver, list of 10) → `author` (resolver) gives naive `1 + 10 = 11`, batched `2`.
""",
    starter='''def count_calls(query):
    pass
''',
    solution='''def count_calls(query):
    def walk(selection, parents):
        naive = batched = 0
        for node in selection:
            if node.get("resolver") and parents > 0:
                naive += parents
                batched += 1
            n, b = walk(node.get("selection") or [], parents * node.get("list", 1))
            naive += n
            batched += b
        return naive, batched

    naive, batched = walk(query, 1)
    return {"naive": naive, "batched": batched}
''',
    tests=[
        [[{"name": "recipes", "resolver": True, "list": 10, "selection": [{"name": "title"}, {"name": "author", "resolver": True}]}]],
        [[{"name": "motd"}]],
        [[{"name": "recipes", "resolver": True, "list": 20, "selection": [
            {"name": "author", "resolver": True, "selection": [{"name": "name"}]},
            {"name": "reviews", "resolver": True, "list": 5, "selection": [{"name": "by", "resolver": True, "selection": [{"name": "name"}]}]}]}]],
        [[{"name": "recipes", "resolver": True, "list": 0, "selection": [{"name": "author", "resolver": True}]}]],
        [[]],
        [[{"name": "me", "resolver": True, "selection": [{"name": "recipes", "resolver": True, "list": 3, "selection": [{"name": "title"}]}]}, {"name": "version", "resolver": True}]],
        [[{"name": "feed", "list": 4, "selection": [{"name": "author", "resolver": True}, {"name": "likes", "resolver": True}]}]],
        [[{"name": "a", "resolver": True, "list": 3, "selection": [{"name": "b", "list": 2, "selection": [{"name": "c", "resolver": True, "list": 0, "selection": [{"name": "d", "resolver": True}]}, {"name": "e", "resolver": True}]}]}]],
        [[{"name": "cooks", "resolver": True, "list": 100, "selection": [{"name": "recipes", "resolver": True, "list": 10, "selection": [{"name": "reviews", "resolver": True, "list": 10, "selection": [{"name": "by", "resolver": True}]}]}]}]],
        [[{"name": "x", "resolver": False, "list": 7, "selection": [{"name": "y", "resolver": False, "selection": [{"name": "z", "resolver": True}]}]}]],
        [[{"name": "r", "resolver": True, "list": 1, "selection": [{"name": "s", "resolver": True, "list": 1, "selection": [{"name": "t", "resolver": True}]}]}]],
    ],
    examples=2,
    wrong_solutions=[
        '''def count_calls(query):
    def walk(selection, parents):
        naive = batched = 0
        for node in selection:
            if node.get("resolver"):
                naive += parents
                batched += 1
            n, b = walk(node.get("selection") or [], parents * node.get("list", 1))
            naive += n
            batched += b
        return naive, batched
    naive, batched = walk(query, 1)
    return {"naive": naive, "batched": batched}
''',
        '''def count_calls(query):
    def walk(selection, parents):
        naive = batched = 0
        for node in selection:
            if node.get("resolver") and parents > 0:
                naive += parents
                batched += 1
            n, b = walk(node.get("selection") or [], node.get("list", 1))
            naive += n
            batched += b
        return naive, batched
    naive, batched = walk(query, 1)
    return {"naive": naive, "batched": batched}
''',
    ],
    guide=dict(
        prereqs="The lesson *The N+1 problem and DataLoader*; recursion over a tree; `gql-resolver-chain` for what a resolver call is.",
        intuition="Every list multiplies. If 20 recipes each have 5 reviews, there are 100 review objects, and any resolver under `reviews` runs 100 times. Carry one number down the tree, 'how many parent objects am I being called for?', and multiply it at each list. Batching changes the cost of a node from 'once per parent' to 'once, full stop'.",
        hints=[
            "Write `walk(selection, parents)` where `parents` is the number of objects the selection is applied to. Start with `walk(query, 1)`.",
            "A resolver node adds `parents` to the naive total and 1 to the batched total.",
            "The children of a node run for `parents * node.get(\"list\", 1)` objects. Zero is contagious: nothing below an empty list runs.",
        ],
        brute_force="Build the full list of objects level by level and count as you 'execute'. Memory and time grow with the product of the list sizes (100 × 10 × 10 objects in one of the tests), when only the product itself is needed.",
        approach="""**Dry run** on `recipes(list 20) { author, reviews(list 5) { by } }`, all with resolvers:

| node | parents | naive += | batched += |
|---|---|---|---|
| recipes | 1 | 1 | 1 |
| author | 20 | 20 | 1 |
| reviews | 20 | 20 | 1 |
| by | 100 | 100 | 1 |

Totals: naive 141, batched 4.""",
        complexity="Time O(n) for n nodes in the query tree. Space O(d) recursion depth.",
        pitfalls="- Using only the nearest list size as the multiplier instead of the running product.\n- Charging a batched call for a node that is never reached (under an empty list).\n- Forgetting that a non-resolver list still multiplies its children.",
        follow_up="This running product is exactly what query **complexity** limits estimate before execution: see `gql-complexity-score`.",
    ),
),
dict(
    id="gql-dataloader-batch",
    title="Batch and cache like DataLoader",
    difficulty="Medium",
    pattern="Performance",
    kind="js",
    entry="runLoader",
    description=r"""
DataLoader fixes the N+1 problem with two ideas: **batching** (collect every key requested during one tick of the event
loop, then fetch them together) and **caching** (never fetch the same key twice during a request).

Simulate it. `runLoader(ticks, db, maxBatch)`

- `ticks`: an array of arrays of string keys. `ticks[i]` holds the keys that resolvers asked for during tick `i`, in order.
- `db`: an object mapping key → value. A key that is not an own property of `db` loads as `null`.
- `maxBatch`: a positive integer, or `null` for no limit.

At the end of each tick the loader:

1. takes the keys of this tick that are **not already cached**, removing duplicates and keeping first-seen order;
2. if there are none, makes no database call;
3. otherwise splits them into consecutive batches of at most `maxBatch` keys and "calls the database" once per batch;
4. caches every loaded key (including keys that loaded as `null`).

Return `{ batches, results }`: `batches` is the list of every batch sent, in order (each an array of keys);
`results[i]` is the array of values for `ticks[i]`, in the order the keys were requested (duplicates included).

**Example:** `runLoader([["c1","c2","c1"],["c2","c3"]], {c1:"Amara",c2:"Bo",c3:"Chidi"}, null)` →
`{ batches: [["c1","c2"],["c3"]], results: [["Amara","Bo","Amara"],["Bo","Chidi"]] }`
""",
    starter='''function runLoader(ticks, db, maxBatch) {
  // return { batches: [...], results: [...] }
}
''',
    solution='''function runLoader(ticks, db, maxBatch) {
  const cache = new Map();
  const batches = [];
  const results = [];
  for (const keys of ticks) {
    const pending = [];
    for (const k of keys) {
      if (!cache.has(k) && !pending.includes(k)) pending.push(k);
    }
    const size = maxBatch ? maxBatch : Math.max(pending.length, 1);
    for (let i = 0; i < pending.length; i += size) {
      const batch = pending.slice(i, i + size);
      batches.push(batch);
      for (const k of batch) {
        cache.set(k, Object.prototype.hasOwnProperty.call(db, k) ? db[k] : null);
      }
    }
    results.push(keys.map((k) => cache.get(k)));
  }
  return { batches, results };
}
''',
    tests=[
        [[["c1", "c2", "c1"], ["c2", "c3"]], DB, None],
        [[["c1"], ["c1"], ["c1"]], DB, None],
        [[["c1", "c2", "c3", "c4", "c5"]], DB, 2],
        [[[], ["c9", "c9"], ["c9", "c1"]], DB, None],
        [[], DB, None],
        [[["c3", "c1", "c3", "c2", "c1"]], DB, 1],
        [[["c1", "c2"], [], ["c2", "c1"], ["c5", "c4", "c1"]], DB, 3],
        [[["toString", "c1"], ["constructor"]], DB, None],
        [[["c5", "c4", "c3", "c2", "c1"], ["c1", "c2", "c3", "c4", "c5", "c6"]], DB, 4],
        [[["k%d" % (i % 37) for i in range(200)], ["k%d" % i for i in range(30, 45)]], {"k%d" % i: i * i for i in range(40)}, 10],
        [[["a"], ["b"], ["a", "b", "c"]], {"a": 0, "b": False, "c": ""}, None],
        [[["c1", "c2", "c3"]], DB, 3],
    ],
    examples=2,
    wrong_solutions=[
        '''function runLoader(ticks, db, maxBatch) {
  const batches = [], results = [];
  for (const keys of ticks) {
    const pending = [...new Set(keys)];
    const size = maxBatch ? maxBatch : Math.max(pending.length, 1);
    for (let i = 0; i < pending.length; i += size) batches.push(pending.slice(i, i + size));
    results.push(keys.map((k) => (Object.prototype.hasOwnProperty.call(db, k) ? db[k] : null)));
  }
  return { batches, results };
}
''',
        '''function runLoader(ticks, db, maxBatch) {
  const cache = new Map(), batches = [], results = [];
  for (const keys of ticks) {
    const pending = [];
    for (const k of keys) if (!cache.has(k) && !pending.includes(k)) pending.push(k);
    const size = maxBatch ? maxBatch : Math.max(pending.length, 1);
    for (let i = 0; i < pending.length; i += size) {
      const batch = pending.slice(i, i + size);
      batches.push(batch);
      for (const k of batch) if (db[k] !== undefined) cache.set(k, db[k]);
    }
    results.push(keys.map((k) => (cache.has(k) ? cache.get(k) : null)));
  }
  return { batches, results };
}
''',
        '''function runLoader(ticks, db, maxBatch) {
  const cache = new Map(), batches = [], results = [];
  for (const keys of ticks) {
    const pending = keys.filter((k) => !cache.has(k));
    if (pending.length) batches.push(pending);
    for (const k of pending) cache.set(k, Object.prototype.hasOwnProperty.call(db, k) ? db[k] : null);
    results.push(keys.map((k) => cache.get(k)));
  }
  return { batches, results };
}
''',
    ],
    guide=dict(
        prereqs="JavaScript arrays, `Map`, and the lesson *The N+1 problem and DataLoader*.",
        intuition="A waiter who walks to the kitchen for every single order is the N+1 problem. DataLoader is the waiter who writes down every order from the table, makes one trip, and remembers what each dish was in case someone asks again. The 'tick' is the moment the waiter stops listening and walks.",
        hints=[
            "Keep one `Map` as the cache for the whole call, and build a fresh `pending` array for each tick.",
            "A key goes into `pending` only if it is neither in the cache nor already in `pending`.",
            "Chunk `pending` with `slice(i, i + size)` in a loop that steps by `size`; when `maxBatch` is `null`, the size is the whole array.",
        ],
        brute_force="Look up every key in `db` as it is requested: one database call per key, per occurrence. For a tick asking 200 times for 37 distinct keys that is 200 calls instead of 1 (or 4 with a batch limit of 10).",
        approach="""Per tick: dedupe against cache and tick → chunk → 'fetch' and cache → map the requested keys to cached values.

**Dry run** ticks `[["c1","c2","c1"],["c2","c3"]]`:

| tick | pending | batches sent | cache after |
|---|---|---|---|
| 0 | c1, c2 | `["c1","c2"]` | c1, c2 |
| 1 | c3 (c2 cached) | `["c3"]` | c1, c2, c3 |

Results: `["Amara","Bo","Amara"]`, `["Bo","Chidi"]`.""",
        complexity="Time O(K·u) with the simple `includes` check, where K is the number of requested keys and u the unique keys in a tick; use a `Set` beside `pending` for O(K). Space O(U) for all unique keys cached.",
        pitfalls="- Not caching misses: a key that loads as `null` would be fetched again every tick.\n- `db[k]` finds inherited properties such as `toString`; use `hasOwnProperty`.\n- Treating falsy values (`0`, `false`, `\"\"`) as missing.\n- Pushing an empty batch when everything was already cached.",
        follow_up="The real DataLoader is created once **per request**, so one user's cached data never leaks into another user's response. Why would a global cache be dangerous?",
    ),
),
dict(
    id="gql-field-auth",
    title="Field-level authorisation with roles",
    difficulty="Medium",
    pattern="Security",
    entry="authorize",
    description=r"""
In GraphQL, permissions are usually checked **per field**: a signed-out visitor may read a cook's `name` but not their `email`.

`authorize(data, selection, rules, user)`

- `data`: the root object. Every object is a dictionary with `"__typename"`; objects that belong to someone carry `"ownerId"`.
- `selection`: `{field: True or nested selection}` (as in `gql-select-fields`). Lists of objects are mapped; `None` stays `None`.
- `rules`: `{"Type.field": [allowed roles]}`. A field with no rule is public.
- `user`: `None` (not signed in) or `{"id": ..., "roles": [...]}`.

A field with a rule is allowed when **any** of these holds:

- the user has at least one of the listed roles;
- the list contains the special word `"OWNER"`, the user is signed in, and the object's `"ownerId"` equals the user's `id`.

A signed-out user is never allowed on a field that has a rule. An empty role list allows nobody.

When a field is **not** allowed: its value in the result is `None`, nothing below it is evaluated, and an error
`{"message": "Not authorised", "path": [...]}` is recorded, where the path lists field names and list indexes from the root.

Return `{"data": ..., "errors": [...]}` with errors in the order encountered (depth-first, selection order, list order).

**Example:** visitor (`user = None`) selecting `cooks { name email }` gets every `name`, `email: None` for each cook, and one error per cook such as `{"message": "Not authorised", "path": ["cooks", 0, "email"]}`.
""",
    starter='''def authorize(data, selection, rules, user):
    pass
''',
    solution='''def authorize(data, selection, rules, user):
    errors = []
    roles = set(user["roles"]) if user else set()

    def allowed(obj, name):
        need = rules.get(str(obj.get("__typename")) + "." + name)
        if need is None:
            return True
        if user is None:
            return False
        if roles & set(need):
            return True
        return "OWNER" in need and obj.get("ownerId") == user["id"]

    def complete(value, sub, path):
        if value is None or sub is True:
            return value
        if isinstance(value, list):
            return [complete(v, sub, path + [i]) for i, v in enumerate(value)]
        return run(value, sub, path)

    def run(obj, sel, path):
        out = {}
        for name, sub in sel.items():
            here = path + [name]
            if allowed(obj, name):
                out[name] = complete(obj.get(name), sub, here)
            else:
                out[name] = None
                errors.append({"message": "Not authorised", "path": here})
        return out

    return {"data": run(data, selection, []), "errors": errors}
''',
    tests=[
        [AUTH_DATA, {"cooks": {"name": True, "email": True}}, AUTH_RULES, None],
        [AUTH_DATA, AUTH_SEL, AUTH_RULES, {"id": "c1", "roles": []}],
        [AUTH_DATA, AUTH_SEL, AUTH_RULES, {"id": "u9", "roles": ["ADMIN"]}],
        [AUTH_DATA, AUTH_SEL, AUTH_RULES, {"id": "u8", "roles": ["ADMIN", "FINANCE", "EDITOR"]}],
        [AUTH_DATA, AUTH_SEL, AUTH_RULES, None],
        [AUTH_DATA, {"version": True}, AUTH_RULES, None],
        [AUTH_DATA, AUTH_SEL, {}, None],
        [AUTH_DATA, {"locked": True, "version": True}, AUTH_RULES, {"id": "u9", "roles": ["ADMIN", "FINANCE"]}],
        [AUTH_DATA, {"cooks": {"drafts": {"notes": True}}}, AUTH_RULES, {"id": "c2", "roles": ["EDITOR"]}],
        [AUTH_DATA, {"cooks": {"drafts": {"notes": True, "title": True}}}, dict(AUTH_RULES, **{"Cook.drafts": ["OWNER", "EDITOR"]}), {"id": "c2", "roles": ["EDITOR"]}],
        [AUTH_DATA, {"stats": {"revenue": True}}, AUTH_RULES, {"id": "u7", "roles": ["FINANCE"]}],
        [AUTH_DATA, {}, AUTH_RULES, None],
        [{"__typename": "Query", "doc": {"__typename": "Doc", "body": "x"}}, {"doc": {"body": True}}, {"Doc.body": ["OWNER"]}, {"id": None, "roles": []}],
    ],
    examples=2,
    wrong_solutions=[
        '''def authorize(data, selection, rules, user):
    errors = []
    roles = set(user["roles"]) if user else set()
    def allowed(obj, name):
        need = rules.get(str(obj.get("__typename")) + "." + name)
        return need is None or bool(roles & set(need))
    def complete(value, sub, path):
        if value is None or sub is True:
            return value
        if isinstance(value, list):
            return [complete(v, sub, path + [i]) for i, v in enumerate(value)]
        return run(value, sub, path)
    def run(obj, sel, path):
        out = {}
        for name, sub in sel.items():
            here = path + [name]
            if allowed(obj, name):
                out[name] = complete(obj.get(name), sub, here)
            else:
                out[name] = None
                errors.append({"message": "Not authorised", "path": here})
        return out
    return {"data": run(data, selection, []), "errors": errors}
''',
        '''def authorize(data, selection, rules, user):
    errors = []
    roles = set(user["roles"]) if user else set()
    def allowed(obj, name):
        need = rules.get(str(obj.get("__typename")) + "." + name)
        if not need:
            return True
        if roles & set(need):
            return True
        return "OWNER" in need and obj.get("ownerId") == (user or {}).get("id")
    def complete(value, sub, path):
        if value is None or sub is True:
            return value
        if isinstance(value, list):
            return [complete(v, sub, path + [i]) for i, v in enumerate(value)]
        return run(value, sub, path)
    def run(obj, sel, path):
        out = {}
        for name, sub in sel.items():
            here = path + [name]
            if allowed(obj, name):
                out[name] = complete(obj.get(name), sub, here)
            else:
                out[name] = None
                errors.append({"message": "Not authorised", "path": here})
        return out
    return {"data": run(data, selection, []), "errors": errors}
''',
        '''def authorize(data, selection, rules, user):
    errors = []
    roles = set(user["roles"]) if user else set()
    def allowed(obj, name):
        need = rules.get(str(obj.get("__typename")) + "." + name)
        if need is None:
            return True
        if user is None:
            return False
        if roles & set(need):
            return True
        return "OWNER" in need and obj.get("ownerId") == user["id"]
    def complete(value, sub, path):
        if value is None or sub is True:
            return value
        if isinstance(value, list):
            return [complete(v, sub, path) for v in value]
        return run(value, sub, path)
    def run(obj, sel, path):
        out = {}
        for name, sub in sel.items():
            here = path + [name]
            out[name] = complete(obj.get(name), sub, here)
            if not allowed(obj, name):
                out[name] = None
                errors.append({"message": "Not authorised", "path": here})
        return out
    return {"data": run(data, selection, []), "errors": errors}
''',
    ],
    guide=dict(
        prereqs="`gql-select-fields`; the lesson *Custom scalars, databases, authentication and authorisation*; Python sets.",
        intuition="**Authentication** answers 'who are you?' and is done once per request. **Authorisation** answers 'may you see *this*?' and is asked at every guarded field, because the answer depends on which object you are looking at: you own your own e-mail address but not mine. A denied field becomes `null` with an error beside it, so the rest of the page still loads.",
        hints=[
            "Build the rule key from the *current object's* `__typename` and the field name.",
            "Decide in this order: no rule → allowed; signed out → denied; shared role → allowed; otherwise the OWNER test.",
            "Pass a `path` list down the recursion, adding the field name, and the index when mapping a list.",
        ],
        brute_force="Check the user's roles once at the top and refuse the whole query if any guarded field appears. Simple, but a profile page then fails entirely because of one private field, and the OWNER rule cannot be evaluated without looking at each object.",
        approach="""`run` loops over the selection. For each field: `allowed`? If yes, complete the value (recursing into objects and lists). If no, write `None`, record the error, and do not descend.

**Dry run** for cook `c1` (no roles) selecting `cooks { email }`:

| object | rule `Cook.email` = ADMIN, OWNER | result |
|---|---|---|
| cook c1 | role? no. owner? `ownerId == "c1"` yes | e-mail shown |
| cook c2 | role? no. owner? `"c2" != "c1"` | `None`, error path `["cooks", 1, "email"]` |
| `None` entry | | stays `None` |""",
        complexity="Time O(f·r) for f selected field positions and r roles per rule. Space O(result + depth).",
        pitfalls="- Treating an empty rule list as 'no rule' opens a field that should be closed to everyone.\n- A signed-out user and an object with no owner both have 'id' `None`: never let `None == None` grant ownership.\n- Evaluating the children of a denied field leaks errors (and work) about data the user may not even know exists.\n- Leaving list indexes out of the path.",
        follow_up="Where should this logic live in a real server: in each resolver, in a schema directive such as `@auth(requires: ADMIN)`, or in the business-logic layer below GraphQL? The GraphQL documentation recommends the last.",
    ),
),
]
