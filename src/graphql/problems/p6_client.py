"""GraphQL track problems, part 6 (JavaScript): client cache, optimistic UI, subscriptions, persisted queries."""


def _h(q):
    h = 5381
    for ch in q:
        h = (h * 33 + ord(ch)) % 4294967296
    return "%08x" % h


Q1 = "{ recipes { id title } }"
Q2 = "query Cook($id: ID!) { cook(id: $id) { name } }"
Q3 = "{ me { id } }"

RESP1 = {"recipes": [
    {"__typename": "Recipe", "id": "r1", "title": "Lentil soup", "author": {"__typename": "Cook", "id": "c1", "name": "Amara"}},
    {"__typename": "Recipe", "id": "r2", "title": "Flatbread", "author": {"__typename": "Cook", "id": "c1", "name": "Amara"}},
]}
RESP2 = {"recipe": {"__typename": "Recipe", "id": "r1", "minutes": 35, "tags": ["vegan", "soup"],
                    "nutrition": {"__typename": "Nutrition", "kcal": 310}}}
RESP3 = {"me": {"__typename": "Cook", "id": "c1", "city": "Leeds", "favourite": {"__typename": "Recipe", "id": "r2", "title": "Flatbread (v2)"}}}

PROBLEMS = [
dict(
    id="gql-normalized-cache",
    title="A normalised client cache",
    difficulty="Hard",
    pattern="Client cache",
    kind="js",
    entry="runCache",
    description=r"""
Client libraries such as Apollo Client and Relay do not store responses as they arrive. They **normalise** them: every
object that can be identified is stored once, under its own key, and everywhere else holds a *reference* to it.
Update the object once and every screen that shows it changes.

Write `runCache(ops)` which starts with the store `{ ROOT_QUERY: {} }`, applies the operations in order and returns an
array with one result per operation.

**Normalising a value**

- An array → normalise each element.
- An object with both `__typename` and a non-null `id` is an **entity**. Its key is `` `${__typename}:${id}` ``. Normalise its
  fields, **merge** them into `store[key]` (new fields overwrite, other existing fields stay), and replace the object by `{ "__ref": key }`.
- Any other object → the same object with its fields normalised (stored inline).
- Scalars and `null` → unchanged.

**Operations**

| op | effect | result |
|---|---|---|
| `{op:"write", data}` | normalise each field of `data` and assign it into `store.ROOT_QUERY` | `null` |
| `{op:"read", selection}` | read from `ROOT_QUERY` (see below) | the data, or `null` on a cache miss |
| `{op:"modify", id, fields}` | if `store[id]` exists, shallow-merge `fields` into it | `true` / `false` |
| `{op:"evict", id}` | delete `store[id]` if it exists | `true` / `false` |
| `{op:"extract"}` | | a copy of the whole store |

**Reading.** A `selection` maps field names to `true` (leaf) or a nested selection. Follow `__ref`s into the store, map over
arrays, keep `null` as `null`. If **any** selected field is absent from the object it is read from, or a reference points to an
entity that is not in the store, the whole read is a **cache miss** and its result is `null`: partial data is never returned.

**Example:** after writing `{recipe: {__typename:"Recipe", id:"r1", title:"Soup"}}`, `extract` gives
`{ROOT_QUERY: {recipe: {__ref: "Recipe:r1"}}, "Recipe:r1": {__typename:"Recipe", id:"r1", title:"Soup"}}`.
""",
    starter='''function runCache(ops) {
  const store = { ROOT_QUERY: {} };
  const results = [];
  // ...
  return results;
}
''',
    solution='''function runCache(ops) {
  const store = { ROOT_QUERY: {} };
  const MISS = { miss: true };
  const has = (o, k) => Object.prototype.hasOwnProperty.call(o, k);

  function normalise(value) {
    if (Array.isArray(value)) return value.map(normalise);
    if (value !== null && typeof value === "object") {
      const fields = {};
      for (const k of Object.keys(value)) fields[k] = normalise(value[k]);
      if (value.__typename !== undefined && value.id !== undefined && value.id !== null) {
        const key = value.__typename + ":" + value.id;
        store[key] = Object.assign(store[key] || {}, fields);
        return { __ref: key };
      }
      return fields;
    }
    return value;
  }

  function read(value, sel) {
    if (value === null) return null;
    if (Array.isArray(value)) {
      const items = value.map((v) => read(v, sel));
      return items.includes(MISS) ? MISS : items;
    }
    if (sel === true) return value;
    if (has(value, "__ref")) {
      if (!has(store, value.__ref)) return MISS;
      value = store[value.__ref];
    }
    const out = {};
    for (const k of Object.keys(sel)) {
      if (!has(value, k)) return MISS;
      const r = read(value[k], sel[k]);
      if (r === MISS) return MISS;
      out[k] = r;
    }
    return out;
  }

  const results = [];
  for (const op of ops) {
    if (op.op === "write") {
      for (const k of Object.keys(op.data)) store.ROOT_QUERY[k] = normalise(op.data[k]);
      results.push(null);
    } else if (op.op === "read") {
      const r = read(store.ROOT_QUERY, op.selection);
      results.push(r === MISS ? null : r);
    } else if (op.op === "modify") {
      if (has(store, op.id)) { Object.assign(store[op.id], op.fields); results.push(true); }
      else results.push(false);
    } else if (op.op === "evict") {
      if (has(store, op.id)) { delete store[op.id]; results.push(true); }
      else results.push(false);
    } else {
      results.push(JSON.parse(JSON.stringify(store)));
    }
  }
  return results;
}
''',
    tests=[
        [[{"op": "write", "data": {"recipe": {"__typename": "Recipe", "id": "r1", "title": "Soup"}}}, {"op": "extract"}]],
        [[{"op": "write", "data": RESP1}, {"op": "extract"}]],
        [[{"op": "write", "data": RESP1}, {"op": "read", "selection": {"recipes": {"title": True, "author": {"name": True}}}}]],
        [[{"op": "write", "data": RESP1}, {"op": "modify", "id": "Cook:c1", "fields": {"name": "Amara O."}},
          {"op": "read", "selection": {"recipes": {"id": True, "author": {"name": True}}}}, {"op": "modify", "id": "Cook:zz", "fields": {"name": "?"}}]],
        [[{"op": "write", "data": RESP1}, {"op": "read", "selection": {"recipes": {"title": True, "minutes": True}}}]],
        [[{"op": "write", "data": RESP1}, {"op": "write", "data": RESP2},
          {"op": "read", "selection": {"recipes": {"title": True, "minutes": True}}},
          {"op": "read", "selection": {"recipe": {"title": True, "minutes": True, "tags": True, "nutrition": {"kcal": True}}}}]],
        [[{"op": "write", "data": RESP1}, {"op": "write", "data": RESP3},
          {"op": "read", "selection": {"recipes": {"title": True}, "me": {"name": True, "city": True, "favourite": {"title": True, "author": {"name": True}}}}},
          {"op": "extract"}]],
        [[{"op": "read", "selection": {"recipes": {"id": True}}}, {"op": "read", "selection": {}}, {"op": "extract"}]],
        [[{"op": "write", "data": RESP1}, {"op": "evict", "id": "Recipe:r2"}, {"op": "evict", "id": "Recipe:r2"},
          {"op": "read", "selection": {"recipes": {"title": True}}}, {"op": "extract"}]],
        [[{"op": "write", "data": {"viewer": None, "count": 0, "flags": [True, False], "banner": {"text": "Hi", "link": {"__typename": "Link", "id": 7, "url": "/x"}}}},
          {"op": "read", "selection": {"viewer": {"name": True}, "count": True, "flags": True, "banner": {"text": True, "link": {"url": True}}}},
          {"op": "extract"}]],
        [[{"op": "write", "data": {"a": {"__typename": "T", "id": None, "v": 1}, "b": {"id": "x", "v": 2}, "c": {"__typename": "T", "v": 3}}}, {"op": "extract"}]],
        [[{"op": "write", "data": {"feed": [[{"__typename": "Recipe", "id": "r1", "title": "A"}], [None, {"__typename": "Recipe", "id": "r1", "minutes": 5}]]}},
          {"op": "read", "selection": {"feed": {"title": True, "minutes": True}}},
          {"op": "write", "data": {"feed": []}}, {"op": "read", "selection": {"feed": {"title": True}}}, {"op": "extract"}]],
        [[{"op": "write", "data": RESP1}, {"op": "write", "data": {"recipes": [{"__typename": "Recipe", "id": "r2", "title": "Flatbread"}]}},
          {"op": "read", "selection": {"recipes": {"title": True, "author": {"id": True}}}}]],
    ],
    examples=2,
    wrong_solutions=[
        '''function runCache(ops) {
  const store = { ROOT_QUERY: {} };
  const results = [];
  function read(value, sel) {
    if (value === null || value === undefined) return null;
    if (Array.isArray(value)) return value.map((v) => read(v, sel));
    if (sel === true) return value;
    const out = {};
    for (const k of Object.keys(sel)) out[k] = read(value[k], sel[k]);
    return out;
  }
  for (const op of ops) {
    if (op.op === "write") { Object.assign(store.ROOT_QUERY, JSON.parse(JSON.stringify(op.data))); results.push(null); }
    else if (op.op === "read") results.push(read(store.ROOT_QUERY, op.selection));
    else if (op.op === "extract") results.push(JSON.parse(JSON.stringify(store)));
    else results.push(false);
  }
  return results;
}
''',
        '''function runCache(ops) {
  const store = { ROOT_QUERY: {} };
  const has = (o, k) => Object.prototype.hasOwnProperty.call(o, k);
  function normalise(value) {
    if (Array.isArray(value)) return value.map(normalise);
    if (value !== null && typeof value === "object") {
      const fields = {};
      for (const k of Object.keys(value)) fields[k] = normalise(value[k]);
      if (value.__typename !== undefined && value.id !== undefined && value.id !== null) {
        const key = value.__typename + ":" + value.id;
        store[key] = fields;
        return { __ref: key };
      }
      return fields;
    }
    return value;
  }
  const MISS = {};
  function read(value, sel) {
    if (value === null) return null;
    if (Array.isArray(value)) { const items = value.map((v) => read(v, sel)); return items.includes(MISS) ? MISS : items; }
    if (sel === true) return value;
    if (has(value, "__ref")) { if (!has(store, value.__ref)) return MISS; value = store[value.__ref]; }
    const out = {};
    for (const k of Object.keys(sel)) {
      if (!has(value, k)) return MISS;
      const r = read(value[k], sel[k]);
      if (r === MISS) return MISS;
      out[k] = r;
    }
    return out;
  }
  const results = [];
  for (const op of ops) {
    if (op.op === "write") { for (const k of Object.keys(op.data)) store.ROOT_QUERY[k] = normalise(op.data[k]); results.push(null); }
    else if (op.op === "read") { const r = read(store.ROOT_QUERY, op.selection); results.push(r === MISS ? null : r); }
    else if (op.op === "modify") { if (has(store, op.id)) { Object.assign(store[op.id], op.fields); results.push(true); } else results.push(false); }
    else if (op.op === "evict") { if (has(store, op.id)) { delete store[op.id]; results.push(true); } else results.push(false); }
    else results.push(JSON.parse(JSON.stringify(store)));
  }
  return results;
}
''',
        '''function runCache(ops) {
  const store = { ROOT_QUERY: {} };
  const has = (o, k) => Object.prototype.hasOwnProperty.call(o, k);
  function normalise(value) {
    if (Array.isArray(value)) return value.map(normalise);
    if (value !== null && typeof value === "object") {
      const fields = {};
      for (const k of Object.keys(value)) fields[k] = normalise(value[k]);
      if (value.__typename !== undefined && value.id !== undefined && value.id !== null) {
        const key = value.__typename + ":" + value.id;
        store[key] = Object.assign(store[key] || {}, fields);
        return { __ref: key };
      }
      return fields;
    }
    return value;
  }
  function read(value, sel) {
    if (value === null || value === undefined) return null;
    if (Array.isArray(value)) return value.map((v) => read(v, sel));
    if (sel === true) return value;
    if (has(value, "__ref")) value = store[value.__ref] || {};
    const out = {};
    for (const k of Object.keys(sel)) out[k] = read(value[k], sel[k]);
    return out;
  }
  const results = [];
  for (const op of ops) {
    if (op.op === "write") { for (const k of Object.keys(op.data)) store.ROOT_QUERY[k] = normalise(op.data[k]); results.push(null); }
    else if (op.op === "read") results.push(read(store.ROOT_QUERY, op.selection));
    else if (op.op === "modify") { if (has(store, op.id)) { Object.assign(store[op.id], op.fields); results.push(true); } else results.push(false); }
    else if (op.op === "evict") { if (has(store, op.id)) { delete store[op.id]; results.push(true); } else results.push(false); }
    else results.push(JSON.parse(JSON.stringify(store)));
  }
  return results;
}
''',
    ],
    guide=dict(
        prereqs="The lesson *The normalised cache, fetch policies, local state and optimistic UI*; JavaScript objects, `Object.keys`, `Object.assign`, recursion.",
        intuition="A response is a tree, and the same cook can appear in ten branches. Storing the tree as it arrives gives ten copies that drift apart. Normalising is what a library does with books: one copy on the shelf under a call number (`Cook:c1`), and every reading list holds the call number, not a photocopy. Reading is the reverse walk: follow call numbers back to the shelf. If any requested page is missing, say 'not in stock' for the whole request so the client knows it must ask the server.",
        hints=[
            "Write `normalise(value)` that returns what should be stored *in place of* the value: a `{__ref}` for entities, a rebuilt object otherwise. Its side effect is filling the store.",
            "Merge with `Object.assign(store[key] || {}, fields)` so a second response carrying other fields of the same entity adds to the first.",
            "For reads, return a unique sentinel object for 'miss' from the recursive function and convert it to `null` only at the top. Plain `null` is a legitimate value.",
        ],
        brute_force="Keep every response as a nested tree keyed by query. `modify` then has to search every stored tree for copies of the entity, and a read that combines data from two earlier responses is impossible.",
        approach="""**Write:** depth-first; children are normalised before the parent is stored, so the parent holds refs.

**Dry run** writing two recipes that share author `c1`:

| visiting | store change | returns |
|---|---|---|
| author of r1 | `Cook:c1 = {…name}` | `{__ref: "Cook:c1"}` |
| recipe r1 | `Recipe:r1 = {…, author: ref}` | `{__ref: "Recipe:r1"}` |
| author of r2 | `Cook:c1` merged (same data) | same ref |
| recipe r2 | `Recipe:r2 = {…}` | ref |
| root | `ROOT_QUERY.recipes = [ref, ref]` | |

**Read:** resolve refs, check every selected key exists, bubble a miss upward.""",
        complexity="Write: O(size of the response). Read: O(size of the selection applied to the data). Space: O(number of distinct entities × their fields), instead of O(total response sizes) for a non-normalised cache.",
        pitfalls="- Replacing an entity on write instead of merging erases fields learned from other queries.\n- Returning partial data on a miss: the UI would render `undefined` instead of going to the network.\n- Treating `id: 0` as missing, or `id: null` as an identity.\n- Objects without an id (or without `__typename`) must stay inline: inventing a key for them merges unrelated objects.",
        follow_up="Apollo Client lets you customise identity with `typePolicies.keyFields`, and stores fields with arguments under keys such as `recipes({\"first\":2})` (compare `gql-aliases-args`).",
    ),
),
dict(
    id="gql-optimistic-rollback",
    title="Optimistic updates and rollback",
    difficulty="Medium",
    pattern="Client cache",
    kind="js",
    entry="applyOptimistic",
    description=r"""
An **optimistic update** shows the expected result of a mutation immediately, before the server answers. If the server
later says no, the guess must disappear without disturbing anything else, including *other* guesses still in flight.

`applyOptimistic(base, ops)` where `base` is an object of confirmed server data (key → value). Keep a list of pending
**layers**. Process `ops` in order and return an array holding the result of every `read`.

| op | effect |
|---|---|
| `{type:"optimistic", id, patch}` | add a pending layer with this mutation id and patch (at the end of the list) |
| `{type:"commit", id, patch}` | the server answered: remove layer `id` (if present) and apply `patch` to the confirmed data |
| `{type:"rollback", id}` | the server refused: remove layer `id` (if present); confirmed data is untouched |
| `{type:"read"}` | result = a copy of the confirmed data with every pending layer applied in order |

**Applying a patch:** for each key, a value of `null` deletes the key; any other value sets it.

Never modify `base`.

**Example:** `base = {likes: 10}`; ops: optimistic `m1` `{likes: 11}`, read, rollback `m1`, read → `[{likes: 11}, {likes: 10}]`.
""",
    starter='''function applyOptimistic(base, ops) {
  const results = [];
  // ...
  return results;
}
''',
    solution='''function applyOptimistic(base, ops) {
  const data = Object.assign({}, base);
  let layers = [];
  const results = [];
  const apply = (target, patch) => {
    for (const k of Object.keys(patch)) {
      if (patch[k] === null) delete target[k];
      else target[k] = patch[k];
    }
  };
  for (const op of ops) {
    if (op.type === "optimistic") {
      layers.push({ id: op.id, patch: op.patch });
    } else if (op.type === "commit") {
      layers = layers.filter((l) => l.id !== op.id);
      apply(data, op.patch);
    } else if (op.type === "rollback") {
      layers = layers.filter((l) => l.id !== op.id);
    } else if (op.type === "read") {
      const view = Object.assign({}, data);
      for (const l of layers) apply(view, l.patch);
      results.push(view);
    }
  }
  return results;
}
''',
    tests=[
        [{"likes": 10}, [{"type": "optimistic", "id": "m1", "patch": {"likes": 11}}, {"type": "read"}, {"type": "rollback", "id": "m1"}, {"type": "read"}]],
        [{"likes": 10}, [{"type": "optimistic", "id": "m1", "patch": {"likes": 11}}, {"type": "commit", "id": "m1", "patch": {"likes": 12}}, {"type": "read"}]],
        [{"likes": 10, "title": "Soup"}, [
            {"type": "optimistic", "id": "m1", "patch": {"likes": 11}},
            {"type": "optimistic", "id": "m2", "patch": {"title": "Lentil soup"}},
            {"type": "read"}, {"type": "rollback", "id": "m1"}, {"type": "read"},
            {"type": "commit", "id": "m2", "patch": {"title": "Lentil Soup"}}, {"type": "read"}]],
        [{"a": 1}, [{"type": "read"}]],
        [{"a": 1}, []],
        [{"a": 1, "b": 2}, [{"type": "optimistic", "id": "m1", "patch": {"b": None, "c": 3}}, {"type": "read"}, {"type": "rollback", "id": "m1"}, {"type": "read"}]],
        [{"saved": False}, [
            {"type": "optimistic", "id": "m1", "patch": {"saved": True}},
            {"type": "optimistic", "id": "m2", "patch": {"saved": False}},
            {"type": "read"}, {"type": "commit", "id": "m1", "patch": {"saved": True}}, {"type": "read"},
            {"type": "rollback", "id": "m2"}, {"type": "read"}]],
        [{"n": 0}, [{"type": "rollback", "id": "ghost"}, {"type": "commit", "id": "ghost", "patch": {"n": 5, "m": 1}}, {"type": "read"}]],
        [{"x": 1}, [{"type": "optimistic", "id": "m1", "patch": {"x": 2}}, {"type": "optimistic", "id": "m2", "patch": {"x": 3}},
                    {"type": "commit", "id": "m2", "patch": {"x": 30}}, {"type": "read"}, {"type": "rollback", "id": "m1"}, {"type": "read"}]],
        [{"x": 1, "y": 1}, [{"type": "optimistic", "id": "m1", "patch": {"y": None}}, {"type": "commit", "id": "m9", "patch": {"x": None, "z": 0}},
                           {"type": "read"}, {"type": "commit", "id": "m1", "patch": {}}, {"type": "read"}]],
        [{}, [{"type": "optimistic", "id": "m%d" % i, "patch": {"k%d" % (i % 5): i}} for i in range(20)] + [{"type": "read"}]
             + [{"type": "rollback", "id": "m%d" % i} for i in range(19, 9, -1)] + [{"type": "read"}]],
    ],
    examples=2,
    wrong_solutions=[
        '''function applyOptimistic(base, ops) {
  let data = Object.assign({}, base);
  const snapshots = {};
  const results = [];
  const apply = (t, p) => { for (const k of Object.keys(p)) { if (p[k] === null) delete t[k]; else t[k] = p[k]; } };
  for (const op of ops) {
    if (op.type === "optimistic") { snapshots[op.id] = Object.assign({}, data); apply(data, op.patch); }
    else if (op.type === "commit") { delete snapshots[op.id]; apply(data, op.patch); }
    else if (op.type === "rollback") { if (snapshots[op.id]) { data = snapshots[op.id]; delete snapshots[op.id]; } }
    else if (op.type === "read") results.push(Object.assign({}, data));
  }
  return results;
}
''',
        '''function applyOptimistic(base, ops) {
  const data = Object.assign({}, base);
  let layers = [];
  const results = [];
  const apply = (t, p) => { for (const k of Object.keys(p)) t[k] = p[k]; };
  for (const op of ops) {
    if (op.type === "optimistic") layers.push({ id: op.id, patch: op.patch });
    else if (op.type === "commit") { layers = layers.filter((l) => l.id !== op.id); apply(data, op.patch); }
    else if (op.type === "rollback") layers = layers.filter((l) => l.id !== op.id);
    else if (op.type === "read") { const v = Object.assign({}, data); for (const l of layers) apply(v, l.patch); results.push(v); }
  }
  return results;
}
''',
        '''function applyOptimistic(base, ops) {
  const data = Object.assign({}, base);
  let layers = [];
  const results = [];
  const apply = (t, p) => { for (const k of Object.keys(p)) { if (p[k] === null) delete t[k]; else t[k] = p[k]; } };
  for (const op of ops) {
    if (op.type === "optimistic") layers.push({ id: op.id, patch: op.patch });
    else if (op.type === "commit") { apply(data, op.patch); }
    else if (op.type === "rollback") layers = layers.filter((l) => l.id !== op.id);
    else if (op.type === "read") { const v = Object.assign({}, data); for (const l of layers) apply(v, l.patch); results.push(v); }
  }
  return results;
}
''',
    ],
    guide=dict(
        prereqs="The optimistic UI section of *The normalised cache, fetch policies, local state and optimistic UI*; object spread or `Object.assign`; `Array.prototype.filter`.",
        intuition="Think of sheets of tracing paper over a printed map. The print is what the server confirmed. Each pending mutation is one transparent sheet with a correction drawn on it. What the user sees is the stack viewed from above. When the server answers, you pull out exactly that sheet: on success you also ink the real result onto the print; on failure you throw the sheet away. Nothing else moves.",
        hints=[
            "Never write optimistic values into the confirmed data. Keep them in a separate ordered list of layers.",
            "A read builds a fresh copy: start from the confirmed data, then replay every remaining layer in order.",
            "Commit and rollback both remove the layer by id; only commit touches the confirmed data.",
        ],
        brute_force="Take a snapshot of the whole data before each optimistic write and restore it on failure. With two mutations in flight, restoring the first snapshot also wipes out the second mutation's change. The snapshot approach is only correct when at most one mutation is pending.",
        approach="""**Dry run:** base `{likes: 10, title: "Soup"}`

| op | confirmed | layers | read |
|---|---|---|---|
| optimistic m1 `{likes: 11}` | 10 / Soup | m1 | |
| optimistic m2 `{title: "Lentil soup"}` | 10 / Soup | m1, m2 | |
| read | | | 11 / Lentil soup |
| rollback m1 | 10 / Soup | m2 | |
| read | | | 10 / Lentil soup |
| commit m2 `{title: "Lentil Soup"}` | 10 / Lentil Soup | | |""",
        complexity="Each read costs O(d + p) for d confirmed keys and p total patched keys in pending layers. Commit/rollback are O(l) in the number of layers. Space O(d + p).",
        pitfalls="- Snapshot-and-restore breaks with concurrent mutations.\n- Forgetting to remove the layer on commit leaves the guess covering the real server value forever.\n- Mutating `base` or returning the same object for two reads (later ops would change earlier results).\n- Not handling `null` as 'delete this key'.",
        follow_up="Apollo Client implements exactly this with optimistic layers keyed by mutation id over the normalised cache; Relay calls them optimistic updaters.",
    ),
),
dict(
    id="gql-subscription-filter",
    title="Deliver subscription events by topic and arguments",
    difficulty="Medium",
    pattern="Subscriptions",
    kind="js",
    entry="deliver",
    description=r"""
A subscription server keeps a list of who is listening for what. When something happens it *publishes* an event on a
**topic**, and only the subscribers whose topic and arguments match receive it.

`deliver(ops)` processes an array of operations in order and returns one entry **per publish**: the array of subscriber ids
that receive that event, in the order they subscribed.

| operation | meaning |
|---|---|
| `["subscribe", id, topic, args]` | start listening. `args` is an object (possibly empty). If `id` is already subscribed, the old subscription is replaced and the new one counts as the most recent |
| `["unsubscribe", id]` | stop listening (ignore unknown ids) |
| `["publish", topic, payload]` | an event with a payload object |

A subscriber receives a published event when its topic is identical and **every** argument matches: an argument whose value
is `null` matches anything; otherwise `payload[argName]` must be strictly equal (`===`) to the argument value.

**Example:**
`[["subscribe","s1","reviewAdded",{"recipeId":"r1"}], ["subscribe","s2","reviewAdded",{}], ["publish","reviewAdded",{"recipeId":"r2","stars":5}]]` → `[["s2"]]`
""",
    starter='''function deliver(ops) {
  const out = [];
  // ...
  return out;
}
''',
    solution='''function deliver(ops) {
  let subs = [];
  const out = [];
  for (const op of ops) {
    if (op[0] === "subscribe") {
      const id = op[1];
      subs = subs.filter((s) => s.id !== id);
      subs.push({ id, topic: op[2], args: op[3] || {} });
    } else if (op[0] === "unsubscribe") {
      subs = subs.filter((s) => s.id !== op[1]);
    } else if (op[0] === "publish") {
      const topic = op[1];
      const payload = op[2] || {};
      out.push(
        subs
          .filter((s) => s.topic === topic &&
            Object.keys(s.args).every((k) => s.args[k] === null || s.args[k] === payload[k]))
          .map((s) => s.id)
      );
    }
  }
  return out;
}
''',
    tests=[
        [[["subscribe", "s1", "reviewAdded", {"recipeId": "r1"}], ["subscribe", "s2", "reviewAdded", {}], ["publish", "reviewAdded", {"recipeId": "r2", "stars": 5}]]],
        [[["subscribe", "s1", "reviewAdded", {"recipeId": "r1"}], ["publish", "reviewAdded", {"recipeId": "r1", "stars": 4}], ["unsubscribe", "s1"], ["publish", "reviewAdded", {"recipeId": "r1", "stars": 2}]]],
        [[["publish", "reviewAdded", {"recipeId": "r1"}]]],
        [[]],
        [[["subscribe", "a", "recipeAdded", {}], ["subscribe", "b", "reviewAdded", {}], ["publish", "recipeAdded", {"id": "r5"}], ["publish", "reviewAdded", {"id": "v1"}], ["publish", "cookJoined", {}]]],
        [[["subscribe", "a", "reviewAdded", {"recipeId": "r1", "minStars": None}], ["subscribe", "b", "reviewAdded", {"recipeId": "r1", "stars": 5}],
          ["publish", "reviewAdded", {"recipeId": "r1", "stars": 5}], ["publish", "reviewAdded", {"recipeId": "r1", "stars": 3}]]],
        [[["subscribe", "a", "t", {"n": 1}], ["subscribe", "b", "t", {"n": "1"}], ["subscribe", "c", "t", {"n": True}], ["publish", "t", {"n": 1}], ["publish", "t", {"n": "1"}], ["publish", "t", {}]]],
        [[["subscribe", "a", "t", {}], ["subscribe", "b", "t", {}], ["subscribe", "a", "t", {"k": "x"}], ["publish", "t", {"k": "x"}], ["publish", "t", {"k": "y"}]]],
        [[["subscribe", "a", "t", {}], ["subscribe", "a", "u", {}], ["publish", "t", {}], ["publish", "u", {}], ["unsubscribe", "zzz"], ["unsubscribe", "a"], ["unsubscribe", "a"], ["publish", "u", {}]]],
        [[["subscribe", "a", "T", {}], ["publish", "t", {}], ["subscribe", "b", "t", {"x": None}], ["publish", "t", {"y": 1}]]],
        [[["subscribe", "s%d" % i, "tick", {"room": i % 3}] for i in range(30)] + [["publish", "tick", {"room": 1}], ["unsubscribe", "s4"], ["publish", "tick", {"room": 1}]]],
    ],
    examples=2,
    wrong_solutions=[
        '''function deliver(ops) {
  let subs = [];
  const out = [];
  for (const op of ops) {
    if (op[0] === "subscribe") subs.push({ id: op[1], topic: op[2], args: op[3] || {} });
    else if (op[0] === "unsubscribe") subs = subs.filter((s) => s.id !== op[1]);
    else if (op[0] === "publish") out.push(subs.filter((s) => s.topic === op[1]).map((s) => s.id));
  }
  return out;
}
''',
        '''function deliver(ops) {
  let subs = [];
  const out = [];
  for (const op of ops) {
    if (op[0] === "subscribe") { subs = subs.filter((s) => s.id !== op[1]); subs.push({ id: op[1], topic: op[2], args: op[3] || {} }); }
    else if (op[0] === "unsubscribe") subs = subs.filter((s) => s.id !== op[1]);
    else if (op[0] === "publish") {
      const p = op[2] || {};
      out.push(subs.filter((s) => s.topic === op[1] && Object.keys(s.args).every((k) => !s.args[k] || s.args[k] == p[k])).map((s) => s.id));
    }
  }
  return out;
}
''',
        '''function deliver(ops) {
  const subs = {};
  const out = [];
  for (const op of ops) {
    if (op[0] === "subscribe") subs[op[1]] = { id: op[1], topic: op[2], args: op[3] || {} };
    else if (op[0] === "unsubscribe") delete subs[op[1]];
    else if (op[0] === "publish") {
      const p = op[2] || {};
      out.push(Object.values(subs).filter((s) => s.topic === op[1] && Object.keys(s.args).every((k) => s.args[k] === null || s.args[k] === p[k])).map((s) => s.id));
    }
  }
  return out;
}
''',
    ],
    guide=dict(
        prereqs="The lesson *Subscriptions, file uploads, migration and schema-first versus code-first*; arrays, `filter`, `every`, strict equality.",
        intuition="Publish/subscribe is a noticeboard system. Topics are the boards; a subscription is a person standing at one board with a note saying 'only tell me about recipe r1'. Publishing pins a card to one board, and the server walks along the people at that board, checking each note against the card.",
        hints=[
            "Keep subscriptions in an array so order is preserved; remove by id with `filter` before adding a replacement.",
            "Matching is two tests joined by AND: same topic, and `Object.keys(args).every(...)`.",
            "`every` on an empty array is `true`, which is exactly right for a subscriber with no arguments.",
        ],
        brute_force="On each publish, loop over all subscribers and all their arguments: O(S·A) per event. That is what the reference does and it is fine here. Real servers index subscribers by topic (a `Map` from topic to subscribers) so an event only examines the people at its own board.",
        approach="""**Dry run** of the example:

| op | subscribers | output |
|---|---|---|
| subscribe s1 reviewAdded `{recipeId: "r1"}` | s1 | |
| subscribe s2 reviewAdded `{}` | s1, s2 | |
| publish reviewAdded `{recipeId: "r2"}` | s1: `"r1" === "r2"` false; s2: no args → true | `["s2"]` |""",
        complexity="Time O(S·A) per publish for S subscribers with A arguments each; subscribe/unsubscribe O(S). Space O(S·A).",
        pitfalls="- Using `==` makes the number `1` match the string `\"1\"`.\n- Treating every falsy argument (`0`, `\"\"`, `false`) as 'no filter': only `null` means that.\n- Re-subscribing with an existing id must not leave two entries, and it moves the subscriber to the end.\n- Topic names are case-sensitive.",
        follow_up="With several server instances, an in-memory list is not enough: an event published on server A must reach a WebSocket held by server B. That is why production systems put Redis, Kafka or another message broker behind the publish step.",
    ),
),
dict(
    id="gql-persisted-queries",
    title="Persisted query lookup by hash",
    difficulty="Medium",
    pattern="Security",
    kind="js",
    entry="handleRequests",
    description=r"""
With **persisted queries** a client sends a short hash instead of the full query text. The server looks the hash up in
a table of queries it already knows. This saves bandwidth, and in *locked* mode it becomes an allow-list: the server
will only run queries that were registered at build time.

**Hash function** (use exactly this one): start with `h = 5381`; for each character of the text, in order,
`h = (h * 33 + charCode) mod 2^32`; the hash is `h` written in lowercase hexadecimal, left-padded with zeros to 8 characters.

`handleRequests(requests, locked, preregistered)`

- `preregistered`: an array of query texts stored in the table before any request.
- `locked`: boolean.
- `requests`: an array of `{ hash, query }` where `query` may be absent or `null`.

For each request, in order, produce a result object:

| case | result |
|---|---|
| no `query`, hash is in the table | `{ status: "OK", query: <stored text> }` |
| no `query`, hash unknown | `{ status: "PERSISTED_QUERY_NOT_FOUND" }` |
| `query` present, its hash differs from `hash` | `{ status: "HASH_MISMATCH" }` (nothing is stored) |
| `query` present, hash correct, already in the table | `{ status: "OK", query }` |
| `query` present, hash correct, not in the table, `locked` | `{ status: "NOT_ALLOWED" }` (nothing is stored) |
| `query` present, hash correct, not in the table, not locked | store it, then `{ status: "OK", query }` |

**Example:** unlocked, empty table: `{hash: H}` → not found; `{hash: H, query: Q}` → OK (stored); `{hash: H}` → OK with `Q`.
""",
    starter='''function hashQuery(text) {
  // h = 5381; h = (h * 33 + code) mod 2^32; 8 hex digits
}

function handleRequests(requests, locked, preregistered) {
}
''',
    solution='''function hashQuery(text) {
  let h = 5381;
  for (let i = 0; i < text.length; i++) {
    h = (h * 33 + text.charCodeAt(i)) % 4294967296;
  }
  return h.toString(16).padStart(8, "0");
}

function handleRequests(requests, locked, preregistered) {
  const table = new Map();
  for (const q of preregistered || []) table.set(hashQuery(q), q);
  return requests.map((r) => {
    if (r.query === undefined || r.query === null) {
      return table.has(r.hash)
        ? { status: "OK", query: table.get(r.hash) }
        : { status: "PERSISTED_QUERY_NOT_FOUND" };
    }
    if (hashQuery(r.query) !== r.hash) return { status: "HASH_MISMATCH" };
    if (!table.has(r.hash)) {
      if (locked) return { status: "NOT_ALLOWED" };
      table.set(r.hash, r.query);
    }
    return { status: "OK", query: r.query };
  });
}
''',
    tests=[
        [[{"hash": _h(Q1)}, {"hash": _h(Q1), "query": Q1}, {"hash": _h(Q1)}], False, []],
        [[{"hash": _h(Q1)}, {"hash": _h(Q2)}], True, [Q1]],
        [[{"hash": _h(Q2), "query": Q2}, {"hash": _h(Q2)}, {"hash": _h(Q1), "query": Q1}], True, [Q1]],
        [[{"hash": _h(Q1), "query": Q2}, {"hash": _h(Q1)}, {"hash": _h(Q2)}], False, []],
        [[{"hash": "deadbeef", "query": Q3}, {"hash": "deadbeef"}], False, []],
        [[], False, [Q1, Q2]],
        [[{"hash": _h(""), "query": ""}, {"hash": _h("")}, {"hash": "00001505", "query": None}], False, []],
        [[{"hash": _h("a")}, {"hash": _h("a"), "query": "a"}, {"hash": _h("a").upper()}], False, []],
        [[{"hash": _h(Q3), "query": Q3}, {"hash": _h(Q3) + "0"}, {"hash": _h(Q3)[1:]}], False, []],
        [[{"hash": _h("{ a }" * 400), "query": "{ a }" * 400}, {"hash": _h("{ a }" * 400)}, {"hash": _h("{ a }" * 399)}], False, []],
        [[{"hash": _h(q)} for q in (Q1, Q2, Q3)] + [{"hash": _h(Q3), "query": Q3 + " "}], True, [Q3, Q1]],
        [[{"hash": _h("~~~~~~~~~~~~"), "query": "~~~~~~~~~~~~"}, {"hash": _h("zzzzzzzzzzzzzzzzzzzz"), "query": "zzzzzzzzzzzzzzzzzzzz"}, {"hash": _h("zzzzzzzzzzzzzzzzzzzz")}], False, []],
    ],
    examples=2,
    wrong_solutions=[
        '''function hashQuery(text) {
  let h = 5381;
  for (let i = 0; i < text.length; i++) h = (h * 33 + text.charCodeAt(i)) % 4294967296;
  return h.toString(16).padStart(8, "0");
}
function handleRequests(requests, locked, preregistered) {
  const table = new Map();
  for (const q of preregistered || []) table.set(hashQuery(q), q);
  return requests.map((r) => {
    if (r.query === undefined || r.query === null) {
      return table.has(r.hash) ? { status: "OK", query: table.get(r.hash) } : { status: "PERSISTED_QUERY_NOT_FOUND" };
    }
    if (!table.has(r.hash)) {
      if (locked) return { status: "NOT_ALLOWED" };
      table.set(r.hash, r.query);
    }
    return { status: "OK", query: r.query };
  });
}
''',
        '''function hashQuery(text) {
  let h = 5381;
  for (let i = 0; i < text.length; i++) h = ((h << 5) + h + text.charCodeAt(i)) | 0;
  return h.toString(16).padStart(8, "0");
}
function handleRequests(requests, locked, preregistered) {
  const table = new Map();
  for (const q of preregistered || []) table.set(hashQuery(q), q);
  return requests.map((r) => {
    if (r.query === undefined || r.query === null) {
      return table.has(r.hash) ? { status: "OK", query: table.get(r.hash) } : { status: "PERSISTED_QUERY_NOT_FOUND" };
    }
    if (hashQuery(r.query) !== r.hash) return { status: "HASH_MISMATCH" };
    if (!table.has(r.hash)) {
      if (locked) return { status: "NOT_ALLOWED" };
      table.set(r.hash, r.query);
    }
    return { status: "OK", query: r.query };
  });
}
''',
        '''function hashQuery(text) {
  let h = 5381;
  for (let i = 0; i < text.length; i++) h = (h * 33 + text.charCodeAt(i)) % 4294967296;
  return h.toString(16).padStart(8, "0");
}
function handleRequests(requests, locked, preregistered) {
  const table = new Map();
  for (const q of preregistered || []) table.set(hashQuery(q), q);
  return requests.map((r) => {
    if (!r.query) {
      return table.has(r.hash) ? { status: "OK", query: table.get(r.hash) } : { status: "PERSISTED_QUERY_NOT_FOUND" };
    }
    if (hashQuery(r.query) !== r.hash) return { status: "HASH_MISMATCH" };
    if (locked) return { status: "NOT_ALLOWED" };
    table.set(r.hash, r.query);
    return { status: "OK", query: r.query };
  });
}
''',
    ],
    guide=dict(
        prereqs="The lesson *Security and monitoring*; JavaScript `Map`, `charCodeAt`, `toString(16)`, `padStart`.",
        intuition="A coat-check ticket. The first time, you hand over the coat (the full query) and the number (its hash); afterwards the number is enough. The attendant checks that the number really belongs to the coat, otherwise anyone could swap in a different coat under a trusted number. In locked mode the cloakroom is closed to new coats: only those hung up before opening time can be collected.",
        hints=[
            "Write and test `hashQuery` on its own first. `hashQuery(\"\")` must be `\"00001505\"` (5381 in hex).",
            "Use `% 4294967296` on ordinary numbers. `h * 33 + code` stays below 2^53, so the arithmetic is exact. Bitwise operators would give signed 32-bit results.",
            "Check the cases in the table's order: no query → lookup; mismatch; known; locked; store.",
        ],
        brute_force="Store the queries in an array and compare the incoming text against each one. That is O(n) per request and, more importantly, the client still has to send the full text every time, which defeats the purpose.",
        approach="""**Dry run**, unlocked, empty table, `H = hash(Q)`:

| request | table before | result | table after |
|---|---|---|---|
| `{hash: H}` | empty | PERSISTED_QUERY_NOT_FOUND | empty |
| `{hash: H, query: Q}` | empty | hash verified → OK | H → Q |
| `{hash: H}` | H → Q | OK with Q | H → Q |

This three-step dance is the *automatic persisted queries* protocol: the client retries with the full text only after a miss.""",
        complexity="Hashing is O(L) in the query length; each lookup is O(1) on average. Space O(total stored query text).",
        pitfalls="- Skipping the hash verification lets a client poison the table: register hash X with a different, expensive query.\n- `(h << 5) + h` or `| 0` produce negative numbers once the value passes 2^31.\n- `!r.query` treats the empty string as 'no query'.\n- In locked mode, a correct hash for a pre-registered query that arrives *with* its text is still OK.",
        follow_up="Production systems use SHA-256, not this toy hash: a 32-bit hash has easy collisions. Automatic persisted queries save bandwidth but are not a security feature; only a locked allow-list (often called *trusted documents*) is.",
    ),
),
]
