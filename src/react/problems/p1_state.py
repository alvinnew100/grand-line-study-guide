"""React track problems, part 1: reducers, immutable updates, equality, batching and forms."""


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


FETCH_DRIVER = r'''
// --- driver (provided, do not change) ---
function runFetch(actions) {
  const initial = { status: "idle", data: null, error: null, requestId: null };
  return actions.reduce(fetchReducer, initial);
}
'''

SETIN_DRIVER = r'''
// --- driver (provided, do not change) ---
function checkSetIn(state, path, value) {
  const snapshot = JSON.stringify(state);
  const updated = setIn(state, path, value);
  const untouched = Object.keys(state).filter((k) => path.length > 0 && String(k) !== String(path[0]));
  return {
    updated,
    originalIntact: JSON.stringify(state) === snapshot,
    newRoot: updated !== state,
    siblingsShared: untouched.every((k) => updated !== null && typeof updated === "object" && updated[k] === state[k]),
  };
}
'''

LIST_DRIVER = r'''
// --- driver (provided, do not change) ---
function checkListOp(list, op) {
  const snapshot = JSON.stringify(list);
  const result = applyListOp(list, op);
  const byId = new Map(list.map((item) => [item.id, item]));
  const target = op.type === "update" || op.type === "remove" ? op.id : null;
  return {
    result,
    originalIntact: JSON.stringify(list) === snapshot,
    newArray: result !== list,
    othersShared: result.every((item) => item.id === target || !byId.has(item.id) || byId.get(item.id) === item),
  };
}
'''

PROBLEMS = [
# ---------------------------------------------------------------------------------------------
dict(
    id="react-todo-reducer", title="A pure reducer for a todo list", difficulty="Easy", pattern="Reducers",
    kind="js", entry="todoReducer",
    description=r"""
`useReducer` asks you for one pure function, `(state, action) => nextState`. Write `todoReducer(state, action)`
for a todo list. `state` is an array of `{ id, text, done }`. **Never mutate `state` or its items**; return new
arrays/objects for whatever changed, and return the *same* `state` when nothing changes.

| `action.type` | other fields | behaviour |
|---|---|---|
| `"added"` | `id`, `text` | append `{ id, text: text.trim(), done: false }`. Ignore it (return `state`) when the trimmed text is empty or the id already exists |
| `"toggled"` | `id` | flip `done` of that todo |
| `"renamed"` | `id`, `text` | set the trimmed text; if the trimmed text is empty, **remove** the todo instead |
| `"removed"` | `id` | drop that todo |
| `"clearedDone"` | | drop every todo with `done: true` |
| `"allToggled"` | | if every todo is done, mark all as not done; otherwise mark all as done |
| anything else | | return `state` |

**Example:** `todoReducer([{id:1,text:"tea",done:false}], {type:"toggled", id:1})` → `[{id:1,text:"tea",done:true}]`
""",
    starter="function todoReducer(state, action) {\n  switch (action.type) {\n    // one case per action type\n    default:\n      return state;\n  }\n}\n",
    solution=r'''function todoReducer(state, action) {
  switch (action.type) {
    case "added": {
      const text = action.text.trim();
      if (text === "" || state.some((t) => t.id === action.id)) return state;
      return [...state, { id: action.id, text, done: false }];
    }
    case "toggled":
      return state.map((t) => (t.id === action.id ? { ...t, done: !t.done } : t));
    case "renamed": {
      const text = action.text.trim();
      if (text === "") return state.filter((t) => t.id !== action.id);
      return state.map((t) => (t.id === action.id ? { ...t, text } : t));
    }
    case "removed":
      return state.filter((t) => t.id !== action.id);
    case "clearedDone":
      return state.filter((t) => !t.done);
    case "allToggled": {
      const allDone = state.length > 0 && state.every((t) => t.done);
      return state.map((t) => ({ ...t, done: !allDone }));
    }
    default:
      return state;
  }
}
''',
    tests=[
        [[], {"type": "added", "id": 1, "text": "  buy tea "}],
        [[{"id": 1, "text": "tea", "done": False}], {"type": "toggled", "id": 1}],
        [[{"id": 1, "text": "tea", "done": True}, {"id": 2, "text": "milk", "done": False}], {"type": "toggled", "id": 1}],
        [[{"id": 1, "text": "tea", "done": False}], {"type": "added", "id": 1, "text": "again"}],
        [[{"id": 1, "text": "tea", "done": False}], {"type": "added", "id": 2, "text": "   "}],
        [[{"id": 1, "text": "tea", "done": False}, {"id": 2, "text": "milk", "done": True}], {"type": "renamed", "id": 2, "text": " oat milk "}],
        [[{"id": 1, "text": "tea", "done": False}, {"id": 2, "text": "milk", "done": True}], {"type": "renamed", "id": 1, "text": "  "}],
        [[{"id": 1, "text": "tea", "done": False}, {"id": 2, "text": "milk", "done": True}], {"type": "removed", "id": 1}],
        [[{"id": 1, "text": "tea", "done": False}], {"type": "removed", "id": 9}],
        [[{"id": 1, "text": "a", "done": True}, {"id": 2, "text": "b", "done": False}, {"id": 3, "text": "c", "done": True}], {"type": "clearedDone"}],
        [[{"id": 1, "text": "a", "done": True}, {"id": 2, "text": "b", "done": False}], {"type": "allToggled"}],
        [[{"id": 1, "text": "a", "done": True}, {"id": 2, "text": "b", "done": True}], {"type": "allToggled"}],
        [[], {"type": "allToggled"}],
        [[{"id": 1, "text": "a", "done": True}], {"type": "exploded", "id": 1}],
    ],
    wrong_solutions=[
        r'''function todoReducer(state, action) {
  switch (action.type) {
    case "added": return [...state, { id: action.id, text: action.text, done: false }];
    case "toggled": return state.map((t) => (t.id === action.id ? { ...t, done: true } : t));
    case "renamed": return state.map((t) => (t.id === action.id ? { ...t, text: action.text.trim() } : t));
    case "removed": return state.filter((t) => t.id !== action.id);
    case "clearedDone": return state.filter((t) => !t.done);
    case "allToggled": return state.map((t) => ({ ...t, done: true }));
    default: return state;
  }
}
''',
        r'''function todoReducer(state, action) {
  if (action.type === "added") return [...state, { id: action.id, text: action.text.trim(), done: false }];
  if (action.type === "toggled") return state.map((t) => (t.id === action.id ? { ...t, done: !t.done } : t));
  if (action.type === "removed") return state.filter((t) => t.id !== action.id);
  if (action.type === "clearedDone") return state.filter((t) => !t.done);
  if (action.type === "allToggled") return state.map((t) => ({ ...t, done: !state.every((x) => x.done) }));
  return state;
}
''',
    ],
    guide=G(
        prereqs="`useReducer` (lesson *useReducer and impossible states*), array `map`/`filter`, object spread.",
        intuition="A reducer is a pure lookup: given the old list and a description of what happened, compute the new list. "
                  "Every case is one array expression: spread to append, `map` to change one item, `filter` to drop items.",
        hints=["Start with `removed` and `clearedDone`: both are a single `filter`.",
               "For `toggled`, `map` over the list and return `{ ...t, done: !t.done }` only for the matching id; return `t` itself for the rest.",
               "`allToggled` needs one fact first: is every todo done already? Compute it once, then `map` every item to `done: !allDone`."],
        brute_force="Deep-clone the whole state with `JSON.parse(JSON.stringify(state))`, mutate the clone, return it. It works but copies "
                    "every todo on every action, so `React.memo` rows can never skip a render.",
        approach="1. `switch` on `action.type`.\n2. `added`: trim, reject blank or duplicate id, otherwise `[...state, newTodo]`.\n"
                 "3. `toggled`/`renamed`: `map`, replacing only the matching item with a spread copy. `renamed` with blank text becomes a `filter`.\n"
                 "4. `removed`/`clearedDone`: `filter`.\n5. `allToggled`: `allDone = every(done)`, then map to `!allDone`.\n\n"
                 "**Dry run** `[{1,a,done},{2,b,open}]` + `allToggled`: `allDone` is false, so both become done. Run it again: `allDone` is true, so both become open.",
        complexity="O(n) time and O(n) extra space per action: one pass over the list, sharing every untouched item.",
        pitfalls="Using `push` or assigning `t.done = ...` mutates state React still holds. Forgetting `default: return state` makes unknown "
                 "actions return `undefined`. `[].every(...)` is `true`, which is harmless here because mapping an empty list gives an empty list.",
        follow_up="Add an `\"undo\"` action by keeping `{ past, present }` in state.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-fetch-reducer", title="Loading, error and stale responses in one reducer", difficulty="Medium", pattern="Reducers",
    kind="js", entry="runFetch",
    description=r"""
A data-fetching component has four situations: nothing asked yet, waiting, got data, got an error. Model them with a
single `status` field so contradictory combinations (loading **and** error) cannot exist, and make the reducer ignore
responses that belong to an older request.

Write `fetchReducer(state, action)`. State shape: `{ status, data, error, requestId }` with
`status` one of `"idle" | "loading" | "success" | "error"`. The provided driver folds a list of actions starting from
`{ status: "idle", data: null, error: null, requestId: null }` and returns the final state.

| action | behaviour |
|---|---|
| `{type:"started", requestId}` | `status: "loading"`, remember `requestId`, clear `error`, **keep** the previous `data` (so the UI can show stale results while refreshing) |
| `{type:"succeeded", requestId, data}` | only when `status` is `"loading"` **and** `requestId` equals the remembered one: `status: "success"`, store `data`, `error: null`. Otherwise return `state` |
| `{type:"failed", requestId, error}` | same guard: `status: "error"`, store `error`, keep the previous `data`. Otherwise return `state` |
| `{type:"reset"}` | back to the initial state |
| anything else | return `state` |

**Example:** `started(1)`, `started(2)`, `succeeded(1, "old")`, `succeeded(2, "new")` → `{status:"success", data:"new", error:null, requestId:2}`
(the late answer to request 1 is dropped).
""",
    starter="function fetchReducer(state, action) {\n  // return the next state; never mutate\n  return state;\n}\n" + FETCH_DRIVER,
    solution=r'''function fetchReducer(state, action) {
  const current = state.status === "loading" && action.requestId === state.requestId;
  switch (action.type) {
    case "started":
      return { status: "loading", data: state.data, error: null, requestId: action.requestId };
    case "succeeded":
      return current ? { status: "success", data: action.data, error: null, requestId: state.requestId } : state;
    case "failed":
      return current ? { status: "error", data: state.data, error: action.error, requestId: state.requestId } : state;
    case "reset":
      return { status: "idle", data: null, error: null, requestId: null };
    default:
      return state;
  }
}
''' + FETCH_DRIVER,
    tests=[
        [[]],
        [[{"type": "started", "requestId": 1}]],
        [[{"type": "started", "requestId": 1}, {"type": "succeeded", "requestId": 1, "data": ["a", "b"]}]],
        [[{"type": "started", "requestId": 1}, {"type": "failed", "requestId": 1, "error": "offline"}]],
        [[{"type": "started", "requestId": 1}, {"type": "started", "requestId": 2},
          {"type": "succeeded", "requestId": 1, "data": "old"}, {"type": "succeeded", "requestId": 2, "data": "new"}]],
        [[{"type": "started", "requestId": 1}, {"type": "started", "requestId": 2},
          {"type": "succeeded", "requestId": 2, "data": "new"}, {"type": "succeeded", "requestId": 1, "data": "old"}]],
        [[{"type": "started", "requestId": 1}, {"type": "succeeded", "requestId": 1, "data": [1]},
          {"type": "started", "requestId": 2}]],
        [[{"type": "started", "requestId": 1}, {"type": "succeeded", "requestId": 1, "data": [1]},
          {"type": "started", "requestId": 2}, {"type": "failed", "requestId": 2, "error": "500"}]],
        [[{"type": "started", "requestId": 1}, {"type": "failed", "requestId": 1, "error": "500"},
          {"type": "started", "requestId": 2}]],
        [[{"type": "succeeded", "requestId": None, "data": "ghost"}]],
        [[{"type": "started", "requestId": 1}, {"type": "succeeded", "requestId": 1, "data": 1},
          {"type": "succeeded", "requestId": 1, "data": 2}]],
        [[{"type": "started", "requestId": 1}, {"type": "succeeded", "requestId": 1, "data": 1},
          {"type": "failed", "requestId": 1, "error": "late"}]],
        [[{"type": "started", "requestId": 1}, {"type": "succeeded", "requestId": 1, "data": 1}, {"type": "reset"}]],
        [[{"type": "started", "requestId": 7}, {"type": "unknown"}, {"type": "failed", "requestId": 3, "error": "x"}]],
    ],
    wrong_solutions=[
        r'''function fetchReducer(state, action) {
  switch (action.type) {
    case "started": return { status: "loading", data: state.data, error: null, requestId: action.requestId };
    case "succeeded": return { status: "success", data: action.data, error: null, requestId: state.requestId };
    case "failed": return { status: "error", data: state.data, error: action.error, requestId: state.requestId };
    case "reset": return { status: "idle", data: null, error: null, requestId: null };
    default: return state;
  }
}
''' + FETCH_DRIVER,
        r'''function fetchReducer(state, action) {
  const current = action.requestId === state.requestId;
  switch (action.type) {
    case "started": return { status: "loading", data: null, error: null, requestId: action.requestId };
    case "succeeded": return current ? { status: "success", data: action.data, error: null, requestId: state.requestId } : state;
    case "failed": return current ? { status: "error", data: null, error: action.error, requestId: state.requestId } : state;
    case "reset": return { status: "idle", data: null, error: null, requestId: null };
    default: return state;
  }
}
''' + FETCH_DRIVER,
    ],
    guide=G(
        prereqs="Lessons *Fetching data* and *useReducer and impossible states*.",
        intuition="Two ideas. First, one `status` string replaces a pile of booleans, so the state can only be in a legal situation. "
                  "Second, every request carries a ticket number; a response is accepted only if its ticket is the one currently being waited on.",
        hints=["Compute one boolean up front: is this action the answer to the request we are waiting for?",
               "`started` never needs the guard: a new request always wins and simply replaces the remembered id.",
               "`succeeded` after `succeeded` with the same id must be ignored too, which is why the guard also checks `status === \"loading\"`."],
        brute_force="Three independent `useState` calls (`isLoading`, `error`, `data`) updated in separate places. It is easy to forget one, "
                    "and nothing stops an old response from overwriting a newer one.",
        approach="1. `current = state.status === \"loading\" && action.requestId === state.requestId`.\n"
                 "2. `started`: loading, new id, error cleared, data kept.\n3. `succeeded`/`failed`: apply only when `current`.\n"
                 "4. `reset`: return a fresh initial object.\n\n"
                 "**Dry run:** `started(1)` → loading/1. `started(2)` → loading/2. `succeeded(1)` → id 1 ≠ 2, ignored. `succeeded(2,\"new\")` → success with `\"new\"`.",
        complexity="O(1) per action.",
        pitfalls="Clearing `data` on `started` makes the list flash empty on every refresh. Checking only the id lets a duplicate response "
                 "flip an error back to success. Mutating `state` instead of returning a new object means React sees no change.",
        follow_up="In a component the same guard is usually an `ignore` flag or an `AbortController` in the effect cleanup.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-derive-view", title="Derived state: compute, don't store", difficulty="Easy", pattern="Derived state",
    kind="js", entry="deriveView",
    description=r"""
Anything that can be calculated from existing state should be calculated during render, not kept in a second
`useState` that has to be synchronised. Write the selector `deriveView(state)`.

`state` is `{ todos: [{ id, text, done }], filter, query }` where `filter` is `"all"`, `"active"` (not done) or
`"done"`, and `query` is a search string.

Return:

- `visibleIds`: ids of todos that pass the filter **and** whose text contains `query.trim()` ignoring case
  (an empty trimmed query matches everything), in the original order
- `total`: number of todos; `doneCount`; `remaining` (not done), all counted over **all** todos, not just the visible ones
- `allDone`: `true` when there is at least one todo and none remain
- `isEmpty`: `true` when `visibleIds` is empty
- `label`: `"1 item left"` or `"N items left"` using `remaining`

**Example:** todos `[{1,"Tea",done},{2,"Milk",open}]`, filter `"active"`, query `""` →
`{visibleIds:[2], total:2, doneCount:1, remaining:1, allDone:false, isEmpty:false, label:"1 item left"}`
""",
    starter="function deriveView(state) {\n  // everything here is computed from state.todos, state.filter and state.query\n}\n",
    solution=r'''function deriveView(state) {
  const { todos, filter, query } = state;
  const q = query.trim().toLowerCase();
  const visibleIds = todos
    .filter((t) => filter === "all" || (filter === "done" ? t.done : !t.done))
    .filter((t) => t.text.toLowerCase().includes(q))
    .map((t) => t.id);
  const doneCount = todos.filter((t) => t.done).length;
  const remaining = todos.length - doneCount;
  return {
    visibleIds,
    total: todos.length,
    doneCount,
    remaining,
    allDone: todos.length > 0 && remaining === 0,
    isEmpty: visibleIds.length === 0,
    label: remaining + (remaining === 1 ? " item left" : " items left"),
  };
}
''',
    tests=[
        [{"todos": [{"id": 1, "text": "Tea", "done": True}, {"id": 2, "text": "Milk", "done": False}], "filter": "active", "query": ""}],
        [{"todos": [{"id": 1, "text": "Tea", "done": True}, {"id": 2, "text": "Milk", "done": False}], "filter": "all", "query": ""}],
        [{"todos": [{"id": 1, "text": "Tea", "done": True}, {"id": 2, "text": "Milk", "done": False}], "filter": "done", "query": ""}],
        [{"todos": [], "filter": "all", "query": ""}],
        [{"todos": [{"id": 5, "text": "Green TEA", "done": False}, {"id": 6, "text": "steak", "done": False}, {"id": 7, "text": "Tear tape", "done": True}],
          "filter": "all", "query": "  tea "}],
        [{"todos": [{"id": 5, "text": "Green TEA", "done": False}, {"id": 6, "text": "steak", "done": False}, {"id": 7, "text": "Tear tape", "done": True}],
          "filter": "done", "query": "TEA"}],
        [{"todos": [{"id": 1, "text": "a", "done": True}, {"id": 2, "text": "b", "done": True}], "filter": "all", "query": ""}],
        [{"todos": [{"id": 1, "text": "a", "done": True}, {"id": 2, "text": "b", "done": True}], "filter": "active", "query": ""}],
        [{"todos": [{"id": 1, "text": "a", "done": False}, {"id": 2, "text": "b", "done": False}], "filter": "all", "query": "zzz"}],
        [{"todos": [{"id": 3, "text": "only", "done": False}], "filter": "all", "query": "   "}],
        [{"todos": [{"id": i, "text": "task " + str(i), "done": i % 3 == 0} for i in range(1, 41)], "filter": "active", "query": "1"}],
    ],
    wrong_solutions=[
        r'''function deriveView(state) {
  const { todos, filter, query } = state;
  const visible = todos.filter((t) => filter === "all" || (filter === "done" ? t.done : !t.done))
    .filter((t) => t.text.includes(query));
  const doneCount = visible.filter((t) => t.done).length;
  const remaining = visible.length - doneCount;
  return { visibleIds: visible.map((t) => t.id), total: visible.length, doneCount, remaining,
    allDone: remaining === 0, isEmpty: visible.length === 0, label: remaining + " items left" };
}
''',
    ],
    guide=G(
        prereqs="Lesson *State with useState* (the section on derived values).",
        intuition="The only real state is the list, the chosen filter and the search text. Counts, labels and the visible rows are "
                  "*views* of that state, so a plain function can produce them on every render.",
        hints=["Normalise the query once: `query.trim().toLowerCase()`.",
               "Count `doneCount` over all todos; `remaining` is `total - doneCount`.",
               "`\"\".includes(\"\")` is true for every string, so an empty query needs no special case."],
        brute_force="Keep `visibleTodos`, `remaining` and `label` each in their own `useState` and update them in every handler. "
                    "Miss one handler and the footer lies about the list.",
        approach="1. Lower-case the trimmed query.\n2. Filter by status, then by text, then map to ids.\n3. Count done todos once.\n"
                 "4. Build the return object from those three numbers.\n\n"
                 "**Dry run:** `[Tea ✓, Milk ✗]`, filter `active`: status filter keeps Milk, query `\"\"` keeps it, `visibleIds = [2]`; "
                 "`doneCount = 1`, `remaining = 1`, label `1 item left`.",
        complexity="O(n · m) time where m is the text length (substring search), O(n) space.",
        pitfalls="Counting over the *visible* rows makes the footer change when the user types in the search box. "
                 "`allDone` must be false for an empty list, otherwise an empty app shows the 'all finished' state.",
        follow_up="Wrap the call in `useMemo` only if profiling shows the list is large enough to matter.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-set-in", title="Immutable nested update: setIn", difficulty="Medium", pattern="Immutable updates",
    kind="js", entry="checkSetIn",
    description=r"""
React compares state by reference, so a nested change needs a **new object at every level on the path** while
everything off the path is reused as-is (structural sharing).

Write `setIn(state, path, value)`:

- `path` is an array of keys; strings address object keys and numbers address array indexes
- return a copy of `state` in which the location at `path` holds `value`
- copy only the containers along the path: arrays stay arrays, objects stay objects, and every sibling keeps its
  original reference
- if a container on the path is missing (or is not an object/array), create it: an array when the **next** key is a
  number, otherwise an object
- an empty path returns `value` itself
- `state` must not be modified

The provided driver calls your function and returns `{ updated, originalIntact, newRoot, siblingsShared }`, so
mutation and over-copying are both detected.

**Example:** `setIn({user:{name:"Ann", tags:["a"]}, theme:{dark:true}}, ["user","tags",1], "b")` →
`{user:{name:"Ann", tags:["a","b"]}, theme:{dark:true}}` and `theme` is the very same object as before.
""",
    starter="function setIn(state, path, value) {\n  // copy only what lies on the path\n}\n" + SETIN_DRIVER,
    solution=r'''function setIn(state, path, value) {
  if (path.length === 0) return value;
  const [key, ...rest] = path;
  const isContainer = state !== null && typeof state === "object";
  const copy = isContainer
    ? (Array.isArray(state) ? state.slice() : { ...state })
    : (typeof key === "number" ? [] : {});
  copy[key] = setIn(isContainer ? state[key] : undefined, rest, value);
  return copy;
}
''' + SETIN_DRIVER,
    tests=[
        [{"user": {"name": "Ann", "tags": ["a"]}, "theme": {"dark": True}}, ["user", "tags", 1], "b"],
        [{"a": 1, "b": {"c": 2}}, ["a"], 5],
        [{"a": {"b": {"c": {"d": 1}}}, "x": {"y": 1}}, ["a", "b", "c", "d"], 2],
        [[{"id": 1, "done": False}, {"id": 2, "done": False}], [1, "done"], True],
        [{"list": [[1, 2], [3, 4]], "meta": {"n": 2}}, ["list", 0, 1], 9],
        [{"a": {"keep": {"deep": 1}}}, ["a", "new", "leaf"], "x"],
        [{"rows": {"keep": [1]}}, ["grid", 0, "cell"], 7],
        [{"a": 5, "other": {"k": 1}}, ["a", "b"], 1],
        [{"a": None, "other": [1]}, ["a", 0], "first"],
        [{"a": 1, "o": {"p": 1}}, [], {"replaced": True}],
        [{"a": {"b": 1}, "s": {"t": 1}}, ["a", "b"], 1],
        [{"items": [{"q": 1}, {"q": 2}, {"q": 3}], "sel": {"id": 2}}, ["items", 2, "q"], 30],
        [{"a": {"b": [{"c": 1}]}, "z": {}}, ["a", "b", 0, "c"], None],
    ],
    wrong_solutions=[
        r'''function setIn(state, path, value) {
  if (path.length === 0) return value;
  let cur = state;
  for (let i = 0; i < path.length - 1; i++) {
    if (cur[path[i]] === null || typeof cur[path[i]] !== "object") cur[path[i]] = typeof path[i + 1] === "number" ? [] : {};
    cur = cur[path[i]];
  }
  cur[path[path.length - 1]] = value;
  return Array.isArray(state) ? state.slice() : { ...state };
}
''' + SETIN_DRIVER,
        r'''function setIn(state, path, value) {
  if (path.length === 0) return value;
  const copy = JSON.parse(JSON.stringify(state));
  let cur = copy;
  for (let i = 0; i < path.length - 1; i++) {
    if (cur[path[i]] === null || typeof cur[path[i]] !== "object") cur[path[i]] = typeof path[i + 1] === "number" ? [] : {};
    cur = cur[path[i]];
  }
  cur[path[path.length - 1]] = value;
  return copy;
}
''' + SETIN_DRIVER,
        r'''function setIn(state, path, value) {
  if (path.length === 0) return value;
  const [key, ...rest] = path;
  const base = state !== null && typeof state === "object" ? state : {};
  return { ...base, [key]: setIn(base[key], rest, value) };
}
''' + SETIN_DRIVER,
    ],
    guide=G(
        prereqs="Spread syntax, recursion, lesson *State with useState* (objects and arrays in state).",
        intuition="Think of the path as a rope from the root to one leaf. Every knot on the rope gets replaced by a copy; everything "
                  "hanging off the side is tied onto the copies unchanged.",
        hints=["Recursion mirrors the path: handle the first key, then recurse into that child with the rest of the path.",
               "Copy the current container with `slice()` for arrays and `{ ...obj }` for objects before writing into it.",
               "When the current value is not a container, look at the type of the key you are about to write to decide between `[]` and `{}`."],
        brute_force="Deep-clone everything and mutate the clone. Correct values, but every reference changes, so every memoised child "
                    "re-renders and the cost is O(size of the whole state).",
        approach="1. Empty path → return `value`.\n2. Split `path` into `key` and `rest`.\n3. Shallow-copy the container (or create one).\n"
                 "4. `copy[key] = setIn(child, rest, value)`.\n5. Return the copy.\n\n"
                 "**Dry run** `setIn({a:{b:1}, s:{t:1}}, [\"a\",\"b\"], 2)`: copy root → `{a, s}`; recurse into `a` with `[\"b\"]`: copy `{b:1}`, "
                 "set `b` to `setIn(1, [], 2) = 2`. Result root and `a` are new objects, `s` is the old reference.",
        complexity="O(depth × width of the copied containers) time and space; untouched subtrees cost nothing.",
        pitfalls="Spreading an array into `{}` turns it into an object with numeric keys. Writing into `state` before copying mutates "
                 "the original. Copying the root only (a shallow copy) still leaves nested objects shared *and mutated*.",
        follow_up="Libraries such as Immer generate exactly these copies from code that looks like mutation.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-list-ops", title="Immutable list operations", difficulty="Easy", pattern="Immutable updates",
    kind="js", entry="checkListOp",
    description=r"""
Lists in state are changed with non-mutating recipes. Write `applyListOp(list, op)` where `list` is an array of
objects that each have a unique `id`. Return a **new array**; never change `list` or the objects in it, and reuse
the original object for every item the operation does not touch.

| `op` | result |
|---|---|
| `{type:"insert", index, item}` | `item` placed at `index` (clamp `index` into `0..list.length`) |
| `{type:"remove", id}` | without the item that has this id |
| `{type:"update", id, patch}` | that item replaced by `{...item, ...patch}` |
| `{type:"move", from, to}` | the item at index `from` moved so that it ends up at index `to` (clamp `to` into `0..list.length-1`); if `from` is out of range the contents stay the same |

Unknown ids simply change nothing (still return a new array). The driver reports
`{ result, originalIntact, newArray, othersShared }`.

**Example:** `applyListOp([{id:1},{id:2},{id:3}], {type:"move", from:0, to:2})` → `[{id:2},{id:3},{id:1}]`
""",
    starter="function applyListOp(list, op) {\n  // no push, splice on the original, or sort in place\n}\n" + LIST_DRIVER,
    solution=r'''function applyListOp(list, op) {
  switch (op.type) {
    case "insert": {
      const at = Math.min(Math.max(op.index, 0), list.length);
      return [...list.slice(0, at), op.item, ...list.slice(at)];
    }
    case "remove":
      return list.filter((item) => item.id !== op.id);
    case "update":
      return list.map((item) => (item.id === op.id ? { ...item, ...op.patch } : item));
    case "move": {
      const copy = list.slice();
      if (op.from < 0 || op.from >= list.length) return copy;
      const to = Math.min(Math.max(op.to, 0), list.length - 1);
      const [moved] = copy.splice(op.from, 1);
      copy.splice(to, 0, moved);
      return copy;
    }
    default:
      return list.slice();
  }
}
''' + LIST_DRIVER,
    tests=[
        [[{"id": 1}, {"id": 2}, {"id": 3}], {"type": "move", "from": 0, "to": 2}],
        [[{"id": 1, "n": "a"}, {"id": 2, "n": "b"}], {"type": "insert", "index": 1, "item": {"id": 9, "n": "z"}}],
        [[{"id": 1, "n": "a"}, {"id": 2, "n": "b"}], {"type": "update", "id": 2, "patch": {"n": "B", "x": 1}}],
        [[{"id": 1, "n": "a"}, {"id": 2, "n": "b"}], {"type": "remove", "id": 1}],
        [[], {"type": "insert", "index": 5, "item": {"id": 1}}],
        [[{"id": 1}, {"id": 2}], {"type": "insert", "index": -3, "item": {"id": 0}}],
        [[{"id": 1}, {"id": 2}], {"type": "insert", "index": 2, "item": {"id": 3}}],
        [[{"id": 1}, {"id": 2}], {"type": "remove", "id": 42}],
        [[{"id": 1, "n": "a"}], {"type": "update", "id": 42, "patch": {"n": "?"}}],
        [[{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}], {"type": "move", "from": 3, "to": 1}],
        [[{"id": 1}, {"id": 2}, {"id": 3}], {"type": "move", "from": 1, "to": 99}],
        [[{"id": 1}, {"id": 2}, {"id": 3}], {"type": "move", "from": 7, "to": 0}],
        [[{"id": 1}, {"id": 2}, {"id": 3}], {"type": "move", "from": 2, "to": -1}],
        [[{"id": 1, "tags": ["x"]}, {"id": 2, "tags": []}], {"type": "update", "id": 1, "patch": {"tags": ["x", "y"]}}],
    ],
    wrong_solutions=[
        r'''function applyListOp(list, op) {
  if (op.type === "insert") { list.splice(Math.min(Math.max(op.index, 0), list.length), 0, op.item); return list; }
  if (op.type === "remove") return list.filter((item) => item.id !== op.id);
  if (op.type === "update") { const it = list.find((i) => i.id === op.id); if (it) Object.assign(it, op.patch); return list.slice(); }
  const copy = list.slice();
  if (op.from < 0 || op.from >= list.length) return copy;
  const [m] = copy.splice(op.from, 1); copy.splice(Math.min(Math.max(op.to, 0), list.length - 1), 0, m); return copy;
}
''' + LIST_DRIVER,
        r'''function applyListOp(list, op) {
  const copy = list.map((item) => ({ ...item }));
  if (op.type === "insert") copy.splice(op.index, 0, op.item);
  if (op.type === "remove") return copy.filter((item) => item.id !== op.id);
  if (op.type === "update") return copy.map((item) => (item.id === op.id ? { ...item, ...op.patch } : item));
  if (op.type === "move") { const [m] = copy.splice(op.from, 1); copy.splice(op.to, 0, m); }
  return copy;
}
''' + LIST_DRIVER,
    ],
    guide=G(
        prereqs="Array `slice`, `filter`, `map`, spread. Lesson *State with useState*.",
        intuition="Each mutating array method has a non-mutating twin: `push` → spread, `splice` for delete → `filter`, "
                  "assignment → `map`. A move is 'copy the array, then splice the copy'.",
        hints=["`insert` is two slices with the new item between them.",
               "`update` is a `map` that returns the same object for every non-matching id.",
               "For `move`, `slice()` first; `splice` on that private copy is safe."],
        brute_force="Clone every item on every operation. The values are right, but every row gets a new identity, so memoised rows "
                    "always re-render and focus/animation state tied to identity can reset.",
        approach="Clamp indexes first, then apply the matching recipe.\n\n"
                 "**Dry run** move `from 0, to 2` on `[1,2,3]`: copy → `[1,2,3]`; remove index 0 → `[2,3]` holding `1`; insert at 2 → `[2,3,1]`.",
        complexity="O(n) time and space per operation.",
        pitfalls="`splice`, `sort` and `reverse` change the array they are called on. Splicing with a negative index counts from the "
                 "end, which is why clamping matters. Cloning items you did not change defeats structural sharing.",
        follow_up="Modern JavaScript adds `toSpliced`, `toSorted` and `with`, which return copies.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-shallow-deep-equal", title="Shallow equal vs deep equal", difficulty="Easy", pattern="Equality",
    kind="js", entry="compareBoth",
    description=r"""
`React.memo`, `PureComponent` and many selector libraries compare props **shallowly**: one level of keys, each
value compared with `Object.is`. A deep comparison walks the whole structure instead.

Write `compareBoth(a, b)` returning `{ shallow, deep }`.

**shallow**

1. `Object.is(a, b)` → `true`
2. if either side is not a non-null object → `false`
3. an array and a plain object are never equal
4. otherwise: the same number of own keys, and for every key `Object.is(a[key], b[key])`

**deep**: the same, except step 4 compares the values recursively with the deep rule.

Inputs come from JSON, so two separately written objects are always different references, exactly like two object
literals created during two renders.

**Examples:** `compareBoth({a:1}, {a:1})` → `{shallow:true, deep:true}` ·
`compareBoth({a:{}}, {a:{}})` → `{shallow:false, deep:true}`
""",
    starter="function compareBoth(a, b) {\n  return { shallow: false, deep: false };\n}\n",
    solution=r'''function compareBoth(a, b) {
  const isObj = (v) => v !== null && typeof v === "object";
  const equal = (x, y, inner) => {
    if (Object.is(x, y)) return true;
    if (!isObj(x) || !isObj(y)) return false;
    if (Array.isArray(x) !== Array.isArray(y)) return false;
    const kx = Object.keys(x), ky = Object.keys(y);
    if (kx.length !== ky.length) return false;
    return kx.every((k) => Object.prototype.hasOwnProperty.call(y, k) && inner(x[k], y[k]));
  };
  const deep = (x, y) => equal(x, y, deep);
  return { shallow: equal(a, b, Object.is), deep: deep(a, b) };
}
''',
    tests=[
        [{"a": 1}, {"a": 1}],
        [{"a": {}}, {"a": {}}],
        [1, 1],
        ["a", "a"],
        [None, None],
        [None, {}],
        [0, False],
        [[1, 2], [1, 2]],
        [[], {}],
        [{"a": 1, "b": 2}, {"b": 2, "a": 1}],
        [{"a": 1}, {"a": "1"}],
        [{"a": 1}, {"b": 1}],
        [{"a": 1}, {"a": 1, "b": 2}],
        [[1, [2]], [1, [2]]],
        [{"a": [1, {"b": 2}]}, {"a": [1, {"b": 3}]}],
        [{"a": None}, {"a": None}],
        [{"0": "x"}, ["x"]],
    ],
    wrong_solutions=[
        "function compareBoth(a, b) {\n  const s = JSON.stringify(a) === JSON.stringify(b);\n  return { shallow: s, deep: s };\n}\n",
        r'''function compareBoth(a, b) {
  const isObj = (v) => v !== null && typeof v === "object";
  const eq = (x, y, inner) => {
    if (x === y) return true;
    if (!isObj(x) || !isObj(y)) return false;
    return Object.keys(x).every((k) => inner(x[k], y[k]));
  };
  const deep = (x, y) => eq(x, y, deep);
  return { shallow: eq(a, b, (x, y) => x === y), deep: deep(a, b) };
}
''',
    ],
    guide=G(
        prereqs="`Object.is`, `Object.keys`, recursion. Lesson *memo, useMemo and useCallback*.",
        intuition="Both comparisons share one skeleton; they differ only in how the values under each key are compared: "
                  "identity for shallow, the same function again for deep.",
        hints=["Write one helper that takes the inner comparison as a parameter.",
               "Check key *counts* as well as key values, or `{a:1}` will equal `{a:1, b:2}`.",
               "`Array.isArray(x) !== Array.isArray(y)` separates `[]` from `{}`."],
        brute_force="Compare `JSON.stringify` output. It breaks on key order, treats shallow like deep, and is far slower.",
        approach="1. `Object.is` fast path.\n2. Reject non-objects and array/object mixes.\n3. Compare key counts.\n4. Every key present in "
                 "both and passing the inner comparison.\n\n"
                 "**Dry run** `{a:{}}` vs `{a:{}}`: not identical, both objects, one key each. Shallow: `Object.is({}, {})` is false. "
                 "Deep: recurse, two empty objects, zero keys, true.",
        complexity="Shallow: O(k) for k keys. Deep: O(total nodes).",
        pitfalls="`===` gets `NaN` wrong (never equal to itself); `Object.is` does not. Iterating only the left object's keys misses "
                 "extra keys on the right.",
        follow_up="This is why passing a fresh object or arrow function as a prop defeats `React.memo`.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-batch-updates", title="Batching and the update queue", difficulty="Medium", pattern="State updates",
    kind="js", entry="simulateEvents",
    description=r"""
Inside one event handler React does not re-render after each `setState` call. It collects the calls in a queue,
processes the queue once the handler has finished, and renders at most once.

Simulate that for a single number of state. `simulateEvents(initial, events)`: `events` is a list of handlers and
each handler is a list of calls made during that handler:

| call | React code it stands for | effect on the pending value |
|---|---|---|
| `{kind:"set", value}` | `setN(5)` | becomes `value` |
| `{kind:"addStale", n}` | `setN(count + n)` where `count` is the value **from the render the handler belongs to** | becomes `renderValue + n` |
| `{kind:"add", n}` | `setN(c => c + n)` | pending value `+ n` |
| `{kind:"mul", n}` | `setN(c => c * n)` | pending value `× n` |

Process a handler's calls in order starting from the current state. When the handler ends, commit the pending value.
If it differs from the previous state (`Object.is`), that is **one** render; if it is the same, React bails out and
there is no render.

Return `{ state, renders, history }` where `history` holds the committed state after each handler.

**Example:** `simulateEvents(0, [[{kind:"addStale",n:1},{kind:"addStale",n:1},{kind:"addStale",n:1}]])` →
`{state:1, renders:1, history:[1]}` (three calls, each computing `0 + 1`).
""",
    starter="function simulateEvents(initial, events) {\n  let state = initial;\n  let renders = 0;\n  const history = [];\n  // ...\n  return { state, renders, history };\n}\n",
    solution=r'''function simulateEvents(initial, events) {
  let state = initial;
  let renders = 0;
  const history = [];
  for (const handler of events) {
    const renderValue = state;
    let pending = state;
    for (const call of handler) {
      if (call.kind === "set") pending = call.value;
      else if (call.kind === "addStale") pending = renderValue + call.n;
      else if (call.kind === "add") pending = pending + call.n;
      else if (call.kind === "mul") pending = pending * call.n;
    }
    if (!Object.is(pending, state)) renders++;
    state = pending;
    history.push(state);
  }
  return { state, renders, history };
}
''',
    tests=[
        [0, [[{"kind": "addStale", "n": 1}, {"kind": "addStale", "n": 1}, {"kind": "addStale", "n": 1}]]],
        [0, [[{"kind": "add", "n": 1}, {"kind": "add", "n": 1}, {"kind": "add", "n": 1}]]],
        [0, []],
        [5, [[]]],
        [1, [[{"kind": "addStale", "n": 5}, {"kind": "add", "n": 1}]]],
        [1, [[{"kind": "add", "n": 1}, {"kind": "addStale", "n": 5}]]],
        [2, [[{"kind": "set", "value": 10}, {"kind": "mul", "n": 3}, {"kind": "add", "n": 1}]]],
        [3, [[{"kind": "set", "value": 3}], [{"kind": "add", "n": 0}], [{"kind": "mul", "n": 1}]]],
        [0, [[{"kind": "add", "n": 2}], [{"kind": "addStale", "n": 1}, {"kind": "addStale", "n": 1}], [{"kind": "mul", "n": 2}]]],
        [4, [[{"kind": "add", "n": 1}, {"kind": "add", "n": -1}], [{"kind": "set", "value": 4}]]],
        [1, [[{"kind": "mul", "n": 2}, {"kind": "mul", "n": 2}, {"kind": "addStale", "n": 0}, {"kind": "add", "n": 7}]]],
        [0, [[{"kind": "add", "n": 1}] for _ in range(50)]],
    ],
    wrong_solutions=[
        r'''function simulateEvents(initial, events) {
  let state = initial, renders = 0; const history = [];
  for (const handler of events) {
    for (const call of handler) {
      const before = state;
      if (call.kind === "set") state = call.value;
      else if (call.kind === "mul") state = state * call.n;
      else state = state + call.n;
      if (!Object.is(before, state)) renders++;
    }
    history.push(state);
  }
  return { state, renders, history };
}
''',
        r'''function simulateEvents(initial, events) {
  let state = initial, renders = 0; const history = [];
  for (const handler of events) {
    const renderValue = state; let pending = state;
    for (const call of handler) {
      if (call.kind === "set") pending = call.value;
      else if (call.kind === "addStale") pending = renderValue + call.n;
      else if (call.kind === "add") pending = pending + call.n;
      else if (call.kind === "mul") pending = pending * call.n;
    }
    renders++; state = pending; history.push(state);
  }
  return { state, renders, history };
}
''',
    ],
    guide=G(
        prereqs="Lesson *State with useState* (state as a snapshot, updater functions) and *Render, commit and batching*.",
        intuition="Within a handler there are two numbers: the frozen value the handler's closure saw, and the value the queue has "
                  "worked out so far. Plain values built from the frozen number ignore the queue; updater functions read the queue.",
        hints=["Save `renderValue = state` before looping over a handler's calls.",
               "`addStale` uses `renderValue`; `add` and `mul` use the running `pending`.",
               "Count a render only after the whole handler, and only when `Object.is` says the value changed."],
        brute_force="Treat every call as an immediate assignment followed by a render. That is how many beginners imagine `setState`, "
                    "and it gives 3 for the triple `addStale` example instead of 1.",
        approach="For each handler: `pending = state`; fold the calls; compare; commit.\n\n"
                 "**Dry run** state 1, calls `add 1`, `addStale 5`: pending 2 after the updater, then replaced by `1 + 5 = 6`. One render, state 6. "
                 "Swap the order: `addStale 5` → 6, `add 1` → 7.",
        complexity="O(total number of calls).",
        pitfalls="Counting one render per call; forgetting the bail-out when the result equals the old state; using the running value for the stale form.",
        follow_up="Since React 18 the same batching also applies inside promises, timeouts and native event listeners.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-format-phone", title="Controlled input formatter with caret", difficulty="Medium", pattern="Controlled components",
    kind="js", entry="formatPhone",
    description=r"""
A controlled input may rewrite what the user types. The awkward part is the caret: after React writes the formatted
text back, the caret has to sit where the user expects, not jump to the end.

Write `formatPhone(raw, caret)`:

- `raw` is the text the browser reports after a keystroke (it may contain anything); `caret` is the caret index in `raw`
- keep only digits, at most the first 10
- format progressively as `(AAA) BBB-CCCC`: `""` → `""`, `"5"` → `"(5"`, `"555"` → `"(555"`, `"5551"` → `"(555) 1"`,
  `"5551234"` → `"(555) 123-4"`
- new caret: count the digits in `raw` that are **left of** `caret` (capped at the number of digits kept); the new
  caret sits immediately after that many digits in the formatted value (0 when the count is 0)

Return `{ value, caret }`.

**Example:** `formatPhone("(555) 1234", 10)` → `{ value: "(555) 123-4", caret: 11 }`
""",
    starter="function formatPhone(raw, caret) {\n  return { value: raw, caret };\n}\n",
    solution=r'''function formatPhone(raw, caret) {
  const digits = raw.replace(/\D/g, "").slice(0, 10);
  let value = "";
  if (digits.length > 0) value = "(" + digits.slice(0, 3);
  if (digits.length > 3) value += ") " + digits.slice(3, 6);
  if (digits.length > 6) value += "-" + digits.slice(6);
  const before = Math.min(raw.slice(0, caret).replace(/\D/g, "").length, digits.length);
  let pos = 0;
  let seen = 0;
  while (seen < before) {
    if (/\d/.test(value[pos])) seen++;
    pos++;
  }
  return { value, caret: pos };
}
''',
    tests=[
        ["(555) 1234", 10],
        ["", 0],
        ["5", 1],
        ["555", 3],
        ["5551", 4],
        ["(555) 123-4567", 14],
        ["(555) 123-45678", 15],
        ["(5955) 123-4567", 3],
        ["abc", 3],
        ["(555) 23-4567", 6],
        ["5551234567", 0],
        ["5551234567", 3],
        ["(55) 123-4567", 3],
        ["12 34 56 78 90 12", 17],
        ["(555) 123-4567", 9],
        ["x1y2z3", 4],
    ],
    wrong_solutions=[
        r'''function formatPhone(raw, caret) {
  const d = raw.replace(/\D/g, "").slice(0, 10);
  let v = "";
  if (d.length > 0) v = "(" + d.slice(0, 3);
  if (d.length > 3) v += ") " + d.slice(3, 6);
  if (d.length > 6) v += "-" + d.slice(6);
  return { value: v, caret: v.length };
}
''',
        r'''function formatPhone(raw, caret) {
  const d = raw.replace(/\D/g, "").slice(0, 10);
  let v = "";
  if (d.length > 0) v = "(" + d.slice(0, 3);
  if (d.length > 3) v += ") " + d.slice(3, 6);
  if (d.length > 6) v += "-" + d.slice(6);
  return { value: v, caret: Math.min(caret, v.length) };
}
''',
    ],
    guide=G(
        prereqs="Lesson *Lifting state and controlled components*; basic regular expressions.",
        intuition="Punctuation comes and goes, digits do not. So describe the caret as 'after the k-th digit', reformat, and "
                  "translate that description back into an index.",
        hints=["Strip non-digits with `/\\D/g` and cut to 10.",
               "Build the value in three steps guarded by `digits.length > 0`, `> 3`, `> 6`.",
               "Walk the formatted string counting digits until you have passed `before` of them; the index you stop at is the caret."],
        brute_force="Always put the caret at the end. Fine when appending, infuriating when the user fixes a digit in the middle.",
        approach="1. Extract digits. 2. Format. 3. `before` = digits left of the caret in `raw`, capped. 4. Scan the formatted value.\n\n"
                 "**Dry run** `(\"(5955) 123-4567\", 3)`: digits `59551234567` → first ten `5955123456` → `(595) 512-3456`. "
                 "Left of index 3 in raw are `5`,`9` → `before = 2`. Scanning `(595…`: after the second digit the index is 3.",
        complexity="O(length of the input).",
        pitfalls="Forgetting the cap means a caret past the tenth digit never terminates the scan. Keeping the caret index unchanged "
                 "is wrong whenever punctuation is inserted before it.",
        follow_up="In React you apply the caret in `useLayoutEffect` with `input.setSelectionRange(caret, caret)`.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-form-machine", title="Form validation state machine", difficulty="Medium", pattern="Forms",
    kind="js", entry="runForm",
    description=r"""
A sign-in form is a small state machine. Write `runForm(events)` that starts from

```
values: { email: "", password: "" }, touched: {}, status: "editing", formError: null, submitCount: 0
```

and processes the events in order.

**Validation** (always derived from `values`):
email `""` → `"Email is required"`; not matching `/^[^\s@]+@[^\s@]+\.[^\s@]+$/` → `"Email looks wrong"`;
password `""` → `"Password is required"`; fewer than 8 characters → `"Password needs 8+ characters"`.

**Events**

| event | rule |
|---|---|
| `{type:"change", field, value}` | ignored while `status` is `"submitting"` or `"success"`. Otherwise set the value, and the status becomes `"editing"` with `formError: null` |
| `{type:"blur", field}` | mark the field as touched (ignored after `"success"`) |
| `{type:"submit"}` | ignored while `"submitting"` or `"success"`. Otherwise `submitCount + 1` and `formError: null`; if there is any validation error the status is `"editing"`, else `"submitting"` |
| `{type:"resolve"}` | only while `"submitting"` → `"success"` |
| `{type:"reject", message}` | only while `"submitting"` → `"failed"` with `formError: message` |

Return `{ status, values, visibleErrors, formError, submitCount }`. `visibleErrors` contains the error of a field
only when the field has an error **and** (it was touched **or** `submitCount > 0`), so nobody is shouted at before
they have typed.
""",
    starter="function runForm(events) {\n  let state = { values: { email: \"\", password: \"\" }, touched: {}, status: \"editing\", formError: null, submitCount: 0 };\n  // ...\n}\n",
    solution=r'''function runForm(events) {
  let s = { values: { email: "", password: "" }, touched: {}, status: "editing", formError: null, submitCount: 0 };
  const validate = (v) => {
    const errors = {};
    if (v.email === "") errors.email = "Email is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.email)) errors.email = "Email looks wrong";
    if (v.password === "") errors.password = "Password is required";
    else if (v.password.length < 8) errors.password = "Password needs 8+ characters";
    return errors;
  };
  for (const e of events) {
    const locked = s.status === "submitting" || s.status === "success";
    if (e.type === "change" && !locked) {
      s = { ...s, values: { ...s.values, [e.field]: e.value }, status: "editing", formError: null };
    } else if (e.type === "blur" && s.status !== "success") {
      s = { ...s, touched: { ...s.touched, [e.field]: true } };
    } else if (e.type === "submit" && !locked) {
      const ok = Object.keys(validate(s.values)).length === 0;
      s = { ...s, submitCount: s.submitCount + 1, status: ok ? "submitting" : "editing", formError: null };
    } else if (e.type === "resolve" && s.status === "submitting") {
      s = { ...s, status: "success" };
    } else if (e.type === "reject" && s.status === "submitting") {
      s = { ...s, status: "failed", formError: e.message };
    }
  }
  const errors = validate(s.values);
  const visibleErrors = {};
  for (const field of Object.keys(errors)) {
    if (s.touched[field] || s.submitCount > 0) visibleErrors[field] = errors[field];
  }
  return { status: s.status, values: s.values, visibleErrors, formError: s.formError, submitCount: s.submitCount };
}
''',
    tests=[
        [[]],
        [[{"type": "blur", "field": "email"}]],
        [[{"type": "change", "field": "email", "value": "ann"}, {"type": "blur", "field": "email"}]],
        [[{"type": "submit"}]],
        [[{"type": "change", "field": "email", "value": "ann@example.com"}, {"type": "change", "field": "password", "value": "short"}, {"type": "submit"}]],
        [[{"type": "change", "field": "email", "value": "ann@example.com"}, {"type": "change", "field": "password", "value": "longenough"}, {"type": "submit"}]],
        [[{"type": "change", "field": "email", "value": "ann@example.com"}, {"type": "change", "field": "password", "value": "longenough"},
          {"type": "submit"}, {"type": "change", "field": "email", "value": "other@example.com"}, {"type": "submit"}, {"type": "resolve"}]],
        [[{"type": "change", "field": "email", "value": "ann@example.com"}, {"type": "change", "field": "password", "value": "longenough"},
          {"type": "submit"}, {"type": "reject", "message": "Wrong password"}]],
        [[{"type": "change", "field": "email", "value": "ann@example.com"}, {"type": "change", "field": "password", "value": "longenough"},
          {"type": "submit"}, {"type": "reject", "message": "Wrong password"}, {"type": "change", "field": "password", "value": "betterpass1"}]],
        [[{"type": "change", "field": "email", "value": "ann@example.com"}, {"type": "change", "field": "password", "value": "longenough"},
          {"type": "submit"}, {"type": "reject", "message": "Wrong password"}, {"type": "submit"}, {"type": "resolve"},
          {"type": "change", "field": "email", "value": ""}, {"type": "blur", "field": "email"}, {"type": "submit"}]],
        [[{"type": "resolve"}, {"type": "reject", "message": "nope"}]],
        [[{"type": "change", "field": "email", "value": "a@b"}, {"type": "blur", "field": "password"}]],
        [[{"type": "change", "field": "email", "value": "a b@c.io"}, {"type": "blur", "field": "email"}, {"type": "change", "field": "password", "value": "12345678"}]],
        [[{"type": "submit"}, {"type": "change", "field": "email", "value": "x@y.zz"}, {"type": "change", "field": "password", "value": "12345678"}]],
    ],
    wrong_solutions=[
        r'''function runForm(events) {
  let s = { values: { email: "", password: "" }, touched: {}, status: "editing", formError: null, submitCount: 0 };
  const validate = (v) => {
    const errors = {};
    if (v.email === "") errors.email = "Email is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.email)) errors.email = "Email looks wrong";
    if (v.password === "") errors.password = "Password is required";
    else if (v.password.length < 8) errors.password = "Password needs 8+ characters";
    return errors;
  };
  for (const e of events) {
    if (e.type === "change") s = { ...s, values: { ...s.values, [e.field]: e.value } };
    else if (e.type === "blur") s = { ...s, touched: { ...s.touched, [e.field]: true } };
    else if (e.type === "submit") s = { ...s, submitCount: s.submitCount + 1, status: Object.keys(validate(s.values)).length ? "editing" : "submitting" };
    else if (e.type === "resolve") s = { ...s, status: "success" };
    else if (e.type === "reject") s = { ...s, status: "failed", formError: e.message };
  }
  return { status: s.status, values: s.values, visibleErrors: validate(s.values), formError: s.formError, submitCount: s.submitCount };
}
''',
    ],
    guide=G(
        prereqs="Lessons *Forms* and *useReducer and impossible states*.",
        intuition="Keep the stored state minimal (values, touched, status, formError, submitCount) and derive errors from the values. "
                  "Each event is then a guarded transition: check the status, produce the next state.",
        hints=["Write `validate(values)` first and call it wherever errors are needed; do not store errors.",
               "Compute `locked = status is submitting or success` at the top of the loop; three of the five events consult it.",
               "`visibleErrors` is a filter over `validate(values)` using `touched` and `submitCount`."],
        brute_force="Store `errors` in state and try to keep them updated in every branch. You will forget one, and stale errors appear.",
        approach="Loop over the events applying the table. At the end derive errors and filter them.\n\n"
                 "**Dry run:** valid values, `submit` → submitting (count 1). `change` → ignored. `submit` → ignored. `resolve` → success.",
        complexity="O(number of events).",
        pitfalls="Letting `resolve` succeed when nothing was submitted; accepting edits during submission (the request and the screen "
                 "then disagree); showing every error on first paint.",
        follow_up="React 19's `useActionState` gives you the pending flag and the last result of a form action without hand-rolling this.",
    ),
),
]
