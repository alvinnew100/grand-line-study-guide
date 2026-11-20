"""React track problems, part 3: real-world features and Firebase-style data, rules and auth."""


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


def _doc(i):
    return {"id": "d%02d" % i, "city": ["Oslo", "Lima", "Pune"][i % 3], "price": (i * 37) % 50, "tags": ["new"] if i % 4 == 0 else ["old", "sale"][: 1 + i % 2],
            "stock": {"count": i % 5}}


DOCS = [_doc(i) for i in range(12)]
DOCS_GAPS = DOCS[:6] + [{"id": "x1", "city": "Oslo"}, {"id": "x2", "price": "cheap", "city": "Lima"}, {"id": "x3", "price": 10, "city": None}]

RULES = [
    {"match": "/posts/{postId}", "allow": ["read"], "if": {"op": "or", "args": [
        {"op": "eq", "args": [{"var": "existing.published"}, True]},
        {"op": "and", "args": [{"op": "neq", "args": [{"var": "auth"}, None]}, {"op": "eq", "args": [{"var": "auth.uid"}, {"var": "existing.authorId"}]}]}]}},
    {"match": "/posts/{postId}", "allow": ["create"], "if": {"op": "and", "args": [
        {"op": "neq", "args": [{"var": "auth"}, None]}, {"op": "eq", "args": [{"var": "data.authorId"}, {"var": "auth.uid"}]}]}},
    {"match": "/posts/{postId}", "allow": ["update", "delete"], "if": {"op": "eq", "args": [{"var": "auth.uid"}, {"var": "existing.authorId"}]}},
    {"match": "/users/{userId}", "allow": ["read", "write"], "if": {"op": "eq", "args": [{"var": "auth.uid"}, {"var": "params.userId"}]}},
    {"match": "/public/{rest=**}", "allow": ["get"]},
    {"match": "/{path=**}", "allow": ["read", "write"], "if": {"op": "in", "args": ["admin", {"var": "auth.token.roles"}]}},
    {"match": "/scores/{id}", "allow": ["create"], "if": {"op": "and", "args": [
        {"op": "gte", "args": [{"var": "data.points"}, 0]}, {"op": "lte", "args": [{"var": "data.points"}, 100]}]}},
    {"match": "/posts/{postId}/comments/{commentId}", "allow": ["create"], "if": {"op": "not", "args": [{"op": "eq", "args": [{"var": "auth"}, None]}]}},
]
ANN = {"uid": "ann", "token": {"roles": ["member"]}}
ROOT = {"uid": "root", "token": {"roles": ["member", "admin"]}}


def _req(op, path, auth=None, data=None, existing=None):
    return {"op": op, "path": path, "auth": auth, "data": data, "existing": existing}


PROBLEMS = [
# ---------------------------------------------------------------------------------------------
dict(
    id="react-debounce-search", title="Debounced search controller", difficulty="Medium", pattern="Timing",
    kind="js", entry="debounceLog",
    description=r"""
A search box should not hit the server on every keystroke. *Debouncing* means: wait until the user has been quiet for
`delay` milliseconds, then search once. Timers are hard to test, so here time is explicit.

`debounceLog(events, delay)`: `events` is sorted by timestamp `t` (milliseconds) and each is one of

- `{t, type:"input", value}`: the user changed the text. Replace any pending search with one due at `t + delay`
- `{t, type:"flush"}`: the user pressed Enter. If a search is pending, run it **now** (at `t`)
- `{t, type:"cancel"}`: the box was cleared/unmounted. Drop the pending search

Rules:

- before handling an event at time `t`, a pending search whose due time is `<= t` runs first (at its due time)
- after the last event, a still-pending search runs at its due time
- "running" a search means: take the pending value, trim it; if it equals the query of the **last search that ran**
  (initially `""`), do nothing; otherwise record `{t, query}` and remember it

Return the recorded searches.

**Example:** delay 300, inputs `"r"`@0, `"re"`@100, `"rea"`@250, `"react"`@900 → `[{t:550, query:"rea"}, {t:1200, query:"react"}]`
""",
    starter="function debounceLog(events, delay) {\n  const fired = [];\n  let pending = null; // { value, due }\n  // ...\n  return fired;\n}\n",
    solution=r'''function debounceLog(events, delay) {
  const fired = [];
  let pending = null;
  let last = "";
  const run = (t) => {
    const query = pending.value.trim();
    pending = null;
    if (query !== last) {
      fired.push({ t, query });
      last = query;
    }
  };
  for (const e of events) {
    if (pending && pending.due <= e.t) run(pending.due);
    if (e.type === "input") pending = { value: e.value, due: e.t + delay };
    else if (e.type === "flush") { if (pending) run(e.t); }
    else if (e.type === "cancel") pending = null;
  }
  if (pending) run(pending.due);
  return fired;
}
''',
    tests=[
        [[{"t": 0, "type": "input", "value": "r"}, {"t": 100, "type": "input", "value": "re"}, {"t": 250, "type": "input", "value": "rea"}, {"t": 900, "type": "input", "value": "react"}], 300],
        [[], 300],
        [[{"t": 5, "type": "input", "value": "a"}], 200],
        [[{"t": 0, "type": "input", "value": "a"}, {"t": 300, "type": "input", "value": "ab"}], 300],
        [[{"t": 0, "type": "input", "value": "a"}, {"t": 299, "type": "input", "value": "ab"}], 300],
        [[{"t": 0, "type": "input", "value": "cat"}, {"t": 50, "type": "flush"}, {"t": 60, "type": "flush"}], 300],
        [[{"t": 0, "type": "input", "value": "cat"}, {"t": 50, "type": "cancel"}, {"t": 500, "type": "flush"}], 300],
        [[{"t": 0, "type": "input", "value": "cat"}, {"t": 400, "type": "input", "value": "cat "}, {"t": 900, "type": "input", "value": " cat"}], 300],
        [[{"t": 0, "type": "input", "value": "   "}], 100],
        [[{"t": 0, "type": "input", "value": "a"}, {"t": 500, "type": "input", "value": ""}, {"t": 1000, "type": "input", "value": "a"}], 100],
        [[{"t": 0, "type": "input", "value": "a"}, {"t": 10, "type": "input", "value": "b"}, {"t": 20, "type": "flush"}, {"t": 30, "type": "input", "value": "a"}, {"t": 40, "type": "cancel"}, {"t": 50, "type": "input", "value": "c"}], 25],
        [[{"t": i * 40, "type": "input", "value": "q" * (i + 1)} for i in range(20)], 100],
        [[{"t": i * 150, "type": "input", "value": "q" * (i + 1)} for i in range(6)], 100],
        [[{"t": 0, "type": "input", "value": "x"}, {"t": 0, "type": "input", "value": "xy"}], 0],
    ],
    wrong_solutions=[
        r'''function debounceLog(events, delay) {
  const fired = []; let pending = null;
  for (const e of events) {
    if (pending && pending.due <= e.t) { fired.push({ t: pending.due, query: pending.value.trim() }); pending = null; }
    if (e.type === "input") pending = { value: e.value, due: e.t + delay };
    else if (e.type === "flush") { if (pending) { fired.push({ t: e.t, query: pending.value.trim() }); pending = null; } }
    else if (e.type === "cancel") pending = null;
  }
  if (pending) fired.push({ t: pending.due, query: pending.value.trim() });
  return fired;
}
''',
        r'''function debounceLog(events, delay) {
  const fired = []; let pending = null, last = "";
  const run = (t) => { const q = pending.value.trim(); pending = null; if (q !== last) { fired.push({ t, query: q }); last = q; } };
  for (const e of events) {
    if (pending && pending.due < e.t) run(pending.due);
    if (e.type === "input") pending = pending ? { value: e.value, due: pending.due } : { value: e.value, due: e.t + delay };
    else if (e.type === "flush") { if (pending) run(e.t); }
    else if (e.type === "cancel") pending = null;
  }
  if (pending) run(pending.due);
  return fired;
}
''',
    ],
    guide=G(
        prereqs="`setTimeout`/`clearTimeout`; lesson *Interview builds: debounced search, modal, infinite scroll*.",
        intuition="There is at most one pending timer. Every keystroke throws the old timer away and starts a new one. "
                  "With explicit timestamps, 'the timer fired' becomes 'its due time is not later than the next event'.",
        hints=["Keep `pending = { value, due }` or `null`.",
               "At the top of each loop iteration, settle a pending search that is already due.",
               "Put the trim-and-deduplicate logic in one `run(t)` helper used by due timers, flushes and the final drain."],
        brute_force="Search on every input event. Twenty keystrokes become twenty requests whose responses can arrive out of order.",
        approach="**Dry run** (example, delay 300): `r`@0 → due 300. `re`@100: 300 > 100, replace → due 400. `rea`@250 → due 550. "
                 "`react`@900: 550 ≤ 900 → run at 550 with `rea`; new pending due 1200. End: run at 1200.",
        complexity="O(number of events).",
        pitfalls="Keeping the old due time when a new input arrives turns debounce into throttle. Using `<` instead of `<=` loses a "
                 "search that is due exactly when the next key arrives. Forgetting to drain after the loop.",
        follow_up="In a component the cleanup function of `useEffect` plays the role of `cancel`.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-paginate", title="Pagination maths", difficulty="Easy", pattern="Lists",
    kind="js", entry="paginate",
    description=r"""
Write `paginate(items, page, pageSize)` for client-side pagination. Pages are numbered from 1 and `pageSize >= 1`.

Return

- `totalPages`: `ceil(items.length / pageSize)`, but at least `1` (an empty list still has one empty page)
- `page`: the requested page clamped into `1..totalPages`
- `items`: the slice for that page
- `hasPrev`, `hasNext`
- `total`: `items.length`
- `from`, `to`: 1-based positions of the first and last item shown (`0` and `0` when the page is empty), for a
  "Showing 11–20 of 45" label

**Example:** `paginate(["a","b","c","d","e"], 2, 2)` →
`{items:["c","d"], page:2, totalPages:3, hasPrev:true, hasNext:true, total:5, from:3, to:4}`
""",
    starter="function paginate(items, page, pageSize) {\n}\n",
    solution=r'''function paginate(items, page, pageSize) {
  const total = items.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const current = Math.min(Math.max(page, 1), totalPages);
  const start = (current - 1) * pageSize;
  const slice = items.slice(start, start + pageSize);
  return {
    items: slice,
    page: current,
    totalPages,
    hasPrev: current > 1,
    hasNext: current < totalPages,
    total,
    from: slice.length === 0 ? 0 : start + 1,
    to: start + slice.length,
  };
}
''',
    tests=[
        [["a", "b", "c", "d", "e"], 2, 2],
        [["a", "b", "c", "d", "e"], 1, 2],
        [["a", "b", "c", "d", "e"], 3, 2],
        [["a", "b", "c", "d", "e"], 9, 2],
        [["a", "b", "c", "d", "e"], 0, 2],
        [["a", "b", "c", "d", "e"], -4, 2],
        [[], 1, 10],
        [[], 5, 10],
        [["x"], 1, 1],
        [[1, 2, 3, 4], 2, 2],
        [[1, 2, 3, 4], 1, 100],
        [list(range(45)), 2, 10],
        [list(range(45)), 5, 10],
        [list(range(1000)), 34, 30],
    ],
    wrong_solutions=[
        r'''function paginate(items, page, pageSize) {
  const total = items.length, totalPages = Math.ceil(total / pageSize);
  const start = (page - 1) * pageSize, slice = items.slice(start, start + pageSize);
  return { items: slice, page, totalPages, hasPrev: page > 1, hasNext: page < totalPages, total, from: start + 1, to: start + slice.length };
}
''',
        r'''function paginate(items, page, pageSize) {
  const total = items.length, totalPages = Math.max(1, Math.floor(total / pageSize) + 1);
  const p = Math.min(Math.max(page, 1), totalPages), start = (p - 1) * pageSize, slice = items.slice(start, start + pageSize);
  return { items: slice, page: p, totalPages, hasPrev: p > 1, hasNext: p < totalPages, total, from: slice.length ? start + 1 : 0, to: start + slice.length };
}
''',
    ],
    guide=G(
        prereqs="`Array.prototype.slice`, integer division. Lesson *Sorting, searching, pagination and optimistic updates*.",
        intuition="Everything follows from one number: the index of the first item on the page, `(page − 1) × pageSize`.",
        hints=["Compute `totalPages` first, then clamp the page.", "`slice` never throws for out-of-range indexes, it returns fewer items.",
               "`to = start + slice.length` handles the short last page."],
        brute_force="Chunk the whole list into pages on every render and index into the chunks: O(n) work where O(pageSize) is enough.",
        approach="**Dry run** 5 items, page 9, size 2: `totalPages = 3`, page clamps to 3, start 4, slice `[e]`, from 5, to 5, no next.",
        complexity="O(pageSize).",
        pitfalls="`floor(n / size) + 1` gives an extra empty page when n divides evenly. Not clamping leaves the user on page 9 of 3 "
                 "after a filter shrinks the list.",
        follow_up="Server pagination returns `total` (or a cursor) with each page; the same maths drives the buttons.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-page-window", title="Page buttons with ellipses", difficulty="Medium", pattern="Lists",
    kind="js", entry="pageWindow",
    description=r"""
A pager for 50 pages cannot show 50 buttons. Write `pageWindow(current, total, siblings)` returning what to render:
page numbers and the string `"..."` for gaps.

- `total <= 0` → `[]`. Clamp `current` into `1..total`
- always include page `1`, page `total`, and every page from `current - siblings` to `current + siblings` that exists
- list them in increasing order; between two listed pages that are not adjacent:
  - if exactly **one** page is missing, show that page (an ellipsis would take the same room)
  - otherwise show `"..."`

**Examples:** `pageWindow(5, 10, 1)` → `[1, "...", 4, 5, 6, "...", 10]` ·
`pageWindow(3, 10, 1)` → `[1, 2, 3, 4, "...", 10]`
""",
    starter="function pageWindow(current, total, siblings) {\n  return [];\n}\n",
    solution=r'''function pageWindow(current, total, siblings) {
  if (total <= 0) return [];
  const page = Math.min(Math.max(current, 1), total);
  const show = new Set([1, total]);
  for (let p = page - siblings; p <= page + siblings; p++) {
    if (p >= 1 && p <= total) show.add(p);
  }
  const sorted = [...show].sort((a, b) => a - b);
  const out = [];
  let previous = 0;
  for (const p of sorted) {
    if (p - previous === 2) out.push(previous + 1);
    else if (p - previous > 2) out.push("...");
    out.push(p);
    previous = p;
  }
  return out;
}
''',
    tests=[
        [5, 10, 1], [3, 10, 1], [1, 10, 1], [10, 10, 1], [8, 10, 1], [4, 10, 1], [7, 10, 1],
        [1, 1, 1], [1, 0, 1], [2, 2, 3], [50, 100, 2], [5, 9, 0], [1, 5, 0], [99, 7, 1], [-3, 7, 1], [6, 12, 3],
    ],
    wrong_solutions=[
        r'''function pageWindow(current, total, siblings) {
  if (total <= 0) return [];
  const out = [1];
  if (current - siblings > 2) out.push("...");
  for (let p = Math.max(2, current - siblings); p <= Math.min(total - 1, current + siblings); p++) out.push(p);
  if (current + siblings < total - 1) out.push("...");
  if (total > 1) out.push(total);
  return out;
}
''',
        r'''function pageWindow(current, total, siblings) {
  if (total <= 0) return [];
  const page = Math.min(Math.max(current, 1), total);
  const show = new Set([1, total]);
  for (let p = page - siblings; p <= page + siblings; p++) if (p >= 1 && p <= total) show.add(p);
  const sorted = [...show].sort();
  const out = []; let prev = 0;
  for (const p of sorted) { if (p - prev > 1) out.push("..."); out.push(p); prev = p; }
  return out;
}
''',
    ],
    guide=G(
        prereqs="Sets, sorting numbers. Lesson *Sorting, searching, pagination and optimistic updates*.",
        intuition="Decide *which* pages are shown first, as a set. Formatting the gaps is then a single pass over the sorted set.",
        hints=["A `Set` removes the duplicates when the window touches page 1 or the last page.",
               "Sort numerically: the default sort compares strings, so 10 lands before 2.",
               "Track the previously emitted page; the gap size `p - previous` decides between nothing, a number and `...`."],
        brute_force="Hand-written branches for 'near the start', 'near the end' and 'middle'. Works until `siblings` or `total` changes.",
        approach="**Dry run** `(3, 10, 1)`: set `{1,10,2,3,4}` → sorted `1,2,3,4,10`. Gaps: none until `4 → 10` (6 apart) → `...`.\n\n"
                 "`(4, 10, 1)`: set `{1,10,3,4,5}`; `1 → 3` is a gap of exactly one page, so show `2`.",
        complexity="O(siblings · log siblings).",
        pitfalls="Showing `1 ... 3` (an ellipsis hiding a single page); unsorted or string-sorted output; not clamping `current`.",
        follow_up="Render the numbers as buttons with `aria-current=\"page\"` on the active one and the ellipsis as plain text.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-sort-table", title="Sortable table: header clicks and stable order", difficulty="Medium", pattern="Lists",
    kind="js", entry="sortTable",
    description=r"""
A table sorts by the column whose header was clicked. Write `sortTable(rows, clicks)`.

**Sort state** starts as `{ key: null, dir: "asc" }` (unsorted). For each column name in `clicks`:

- a different column than the current `key` → `{ key: column, dir: "asc" }`
- the same column, currently `"asc"` → `"desc"`
- the same column, currently `"desc"` → back to unsorted `{ key: null, dir: "asc" }`

**Ordering** for the final state (never modify `rows`):

- unsorted → the original order
- compare the values under `key`: numbers numerically, strings **ignoring case**
- rows whose value is `null` or missing go **last in both directions**
- ties keep their original relative order in both directions (a *stable* sort)

Return `{ sort: { key, dir }, rows: sortedRows }`.

**Example:** rows `[{n:"bob",age:30},{n:"Al",age:25},{n:"cy",age:null}]`, clicks `["n"]` → order `Al, bob, cy`;
clicks `["age","age"]` → order `bob (30), Al (25), cy (null)`.
""",
    starter="function sortTable(rows, clicks) {\n  let sort = { key: null, dir: \"asc\" };\n  // 1. replay the clicks  2. sort a copy\n  return { sort, rows };\n}\n",
    solution=r'''function sortTable(rows, clicks) {
  let key = null;
  let dir = "asc";
  for (const column of clicks) {
    if (column !== key) { key = column; dir = "asc"; }
    else if (dir === "asc") dir = "desc";
    else { key = null; dir = "asc"; }
  }
  if (key === null) return { sort: { key, dir }, rows: rows.slice() };
  const missing = (v) => v === null || v === undefined;
  const norm = (v) => (typeof v === "string" ? v.toLowerCase() : v);
  const sign = dir === "asc" ? 1 : -1;
  const sorted = rows
    .map((row, index) => ({ row, index }))
    .sort((a, b) => {
      const x = a.row[key];
      const y = b.row[key];
      if (missing(x) || missing(y)) {
        if (missing(x) && missing(y)) return a.index - b.index;
        return missing(x) ? 1 : -1;
      }
      const p = norm(x);
      const q = norm(y);
      if (p < q) return -sign;
      if (p > q) return sign;
      return a.index - b.index;
    })
    .map((entry) => entry.row);
  return { sort: { key, dir }, rows: sorted };
}
''',
    tests=[
        [[{"n": "bob", "age": 30}, {"n": "Al", "age": 25}, {"n": "cy", "age": None}], ["n"]],
        [[{"n": "bob", "age": 30}, {"n": "Al", "age": 25}, {"n": "cy", "age": None}], ["age", "age"]],
        [[{"n": "bob", "age": 30}, {"n": "Al", "age": 25}, {"n": "cy", "age": None}], ["age"]],
        [[{"n": "bob", "age": 30}, {"n": "Al", "age": 25}, {"n": "cy", "age": None}], []],
        [[{"n": "bob", "age": 30}, {"n": "Al", "age": 25}, {"n": "cy", "age": None}], ["age", "age", "age"]],
        [[{"n": "bob", "age": 30}, {"n": "Al", "age": 25}, {"n": "cy", "age": None}], ["age", "age", "age", "age"]],
        [[{"n": "bob", "age": 30}, {"n": "Al", "age": 25}, {"n": "cy", "age": None}], ["age", "n"]],
        [[], ["n"]],
        [[{"id": 1, "team": "b"}, {"id": 2, "team": "a"}, {"id": 3, "team": "B"}, {"id": 4, "team": "A"}, {"id": 5, "team": "b"}], ["team"]],
        [[{"id": 1, "team": "b"}, {"id": 2, "team": "a"}, {"id": 3, "team": "B"}, {"id": 4, "team": "A"}, {"id": 5, "team": "b"}], ["team", "team"]],
        [[{"id": 1, "v": 10}, {"id": 2, "v": 9}, {"id": 3, "v": 100}, {"id": 4}, {"id": 5, "v": -1}], ["v"]],
        [[{"id": 1, "v": 10}, {"id": 2, "v": 9}, {"id": 3, "v": 100}, {"id": 4}, {"id": 5, "v": -1}], ["v", "v"]],
        [[{"id": i, "g": i % 3} for i in range(30)], ["g", "g"]],
        [[{"id": 1, "v": None}, {"id": 2, "v": None}], ["v", "v"]],
    ],
    wrong_solutions=[
        r'''function sortTable(rows, clicks) {
  let key = null, dir = "asc";
  for (const c of clicks) { if (c !== key) { key = c; dir = "asc"; } else if (dir === "asc") dir = "desc"; else { key = null; dir = "asc"; } }
  if (key === null) return { sort: { key, dir }, rows: rows.slice() };
  const sorted = rows.slice().sort((a, b) => (a[key] < b[key] ? -1 : a[key] > b[key] ? 1 : 0));
  if (dir === "desc") sorted.reverse();
  return { sort: { key, dir }, rows: sorted };
}
''',
        r'''function sortTable(rows, clicks) {
  let key = null, dir = "asc";
  for (const c of clicks) { if (c !== key) { key = c; dir = "asc"; } else dir = dir === "asc" ? "desc" : "asc"; }
  if (key === null) return { sort: { key, dir }, rows: rows.slice() };
  const miss = (v) => v === null || v === undefined, norm = (v) => (typeof v === "string" ? v.toLowerCase() : v), s = dir === "asc" ? 1 : -1;
  const sorted = rows.map((row, index) => ({ row, index })).sort((a, b) => {
    const x = a.row[key], y = b.row[key];
    if (miss(x) || miss(y)) return miss(x) && miss(y) ? a.index - b.index : miss(x) ? 1 : -1;
    const p = norm(x), q = norm(y);
    return p < q ? -s : p > q ? s : a.index - b.index;
  }).map((e) => e.row);
  return { sort: { key, dir }, rows: sorted };
}
''',
    ],
    guide=G(
        prereqs="`Array.prototype.sort` with a comparator. Lesson *Sorting, searching, pagination and optimistic updates*.",
        intuition="Two separate problems: a three-state toggle (the *state*) and a comparator (the *derived* view). The sorted rows "
                  "are never stored; they are recomputed from rows + sort state.",
        hints=["Replay the clicks with two variables, `key` and `dir`.",
               "Decorate each row with its original index so the comparator can break ties explicitly.",
               "Handle missing values before looking at the direction, so they sink in both directions."],
        brute_force="Sort ascending then `reverse()` for descending. Reversal also reverses ties and floats the empty values to the top.",
        approach="**Dry run** clicks `[age, age]`: unsorted → age/asc → age/desc. Compare 30 vs 25 descending → 30 first; `null` last.",
        complexity="O(n log n) time, O(n) space.",
        pitfalls="Sorting `rows` in place mutates props/state. Comparing mixed-case strings with `<` puts every capital before every "
                 "lower-case letter. A two-state toggle never lets the user return to the natural order.",
        follow_up="`Intl.Collator` gives locale-aware comparison (accents, numeric strings).",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-route-matcher", title="Route matcher with params", difficulty="Medium", pattern="Routing",
    kind="js", entry="matchRoute",
    description=r"""
A client-side router maps the address bar to a component. Write `matchRoute(routes, path)`.

`routes` is a list of pattern strings. A pattern is made of `/`-separated segments:

- a **static** segment such as `users` matches only that exact text
- a **param** such as `:id` matches exactly one segment and captures it under that name
- a **splat** `*` (only allowed as the last segment) matches the rest of the path, **including nothing**, and captures
  it (joined with `/`) under the name `"*"`

Before matching, drop anything from `?` onwards in `path` and ignore empty segments (so `/users/7/` equals `/users/7`).
Captured values are passed through `decodeURIComponent`.

When several patterns match, rank them: give every pattern a score list with one entry per pattern segment
(static 3, param 2, splat 1). Compare the lists left to right; the first difference decides (higher wins). If one
list is a prefix of the other, the **shorter** wins. If still tied, the earlier pattern in `routes` wins.

Return `{ pattern, params }` or `null`.

**Example:** routes `["/users/:id", "/users/new", "/*"]`, path `/users/new` → `{pattern:"/users/new", params:{}}`;
path `/users/42?tab=a` → `{pattern:"/users/:id", params:{id:"42"}}`; path `/nope/x` → `{pattern:"/*", params:{"*":"nope/x"}}`
""",
    starter="function matchRoute(routes, path) {\n  return null;\n}\n",
    solution=r'''function matchRoute(routes, path) {
  const split = (p) => p.split("?")[0].split("/").filter(Boolean);
  const parts = split(path);
  const better = (a, b) => {
    const n = Math.min(a.length, b.length);
    for (let i = 0; i < n; i++) if (a[i] !== b[i]) return a[i] > b[i];
    return a.length < b.length;
  };
  let best = null;
  for (const pattern of routes) {
    const segments = split(pattern);
    const params = {};
    const score = [];
    let ok = true;
    let splat = false;
    for (let i = 0; i < segments.length; i++) {
      const seg = segments[i];
      if (seg === "*") {
        params["*"] = parts.slice(i).map(decodeURIComponent).join("/");
        score.push(1);
        splat = true;
        break;
      }
      if (i >= parts.length) { ok = false; break; }
      if (seg[0] === ":") { params[seg.slice(1)] = decodeURIComponent(parts[i]); score.push(2); }
      else if (seg === parts[i]) score.push(3);
      else { ok = false; break; }
    }
    if (!ok || (!splat && segments.length !== parts.length)) continue;
    if (best === null || better(score, best.score)) best = { pattern, params, score };
  }
  return best ? { pattern: best.pattern, params: best.params } : null;
}
''',
    tests=[
        [["/users/:id", "/users/new", "/*"], "/users/new"],
        [["/users/:id", "/users/new", "/*"], "/users/42?tab=a"],
        [["/users/:id", "/users/new", "/*"], "/nope/x"],
        [["/users/:id", "/users/new"], "/nope"],
        [["/"], "/"],
        [["/", "/*"], "/"],
        [["/*", "/"], ""],
        [["/users/:id"], "/users/7/"],
        [["/users/:id"], "/users"],
        [["/users/:id"], "/users/7/posts"],
        [["/files/*", "/files"], "/files"],
        [["/files/*", "/files/:name"], "/files/a.txt"],
        [["/files/*"], "/files/docs/2024/report.pdf"],
        [["/shop/:category/:item", "/shop/:category/sale", "/shop/*"], "/shop/shoes/sale"],
        [["/tags/:tag"], "/tags/caf%C3%A9%20au%20lait"],
        [["/:a/:b", "/:x/:y"], "/1/2"],
        [["/:lang/docs", "/en/:page"], "/en/docs"],
    ],
    wrong_solutions=[
        r'''function matchRoute(routes, path) {
  const split = (p) => p.split("?")[0].split("/").filter(Boolean);
  const parts = split(path);
  for (const pattern of routes) {
    const segs = split(pattern); const params = {}; let ok = true, splat = false;
    for (let i = 0; i < segs.length; i++) {
      if (segs[i] === "*") { params["*"] = parts.slice(i).map(decodeURIComponent).join("/"); splat = true; break; }
      if (i >= parts.length) { ok = false; break; }
      if (segs[i][0] === ":") params[segs[i].slice(1)] = decodeURIComponent(parts[i]);
      else if (segs[i] !== parts[i]) { ok = false; break; }
    }
    if (ok && (splat || segs.length === parts.length)) return { pattern, params };
  }
  return null;
}
''',
        r'''function matchRoute(routes, path) {
  const split = (p) => p.split("/").filter(Boolean);
  const parts = split(path);
  let best = null;
  for (const pattern of routes) {
    const segs = split(pattern); const params = {}; let ok = segs.length === parts.length, score = 0;
    for (let i = 0; ok && i < segs.length; i++) {
      if (segs[i][0] === ":") { params[segs[i].slice(1)] = parts[i]; score += 2; }
      else if (segs[i] === parts[i]) score += 3; else ok = false;
    }
    if (ok && (!best || score > best.score)) best = { pattern, params, score };
  }
  return best ? { pattern: best.pattern, params: best.params } : null;
}
''',
    ],
    guide=G(
        prereqs="String splitting; lesson *Routing with React Router*.",
        intuition="Matching is a segment-by-segment comparison; ranking says 'the more literal the pattern, the better', so "
                  "`/users/new` beats `/users/:id` no matter which was declared first.",
        hints=["Normalise both sides with the same `split` helper.",
               "While matching, push 3, 2 or 1 onto a score array.",
               "A pattern without a splat must consume exactly as many segments as the path has."],
        brute_force="Return the first pattern that matches. Then the order of the route table silently decides behaviour, and a "
                    "catch-all listed first swallows everything.",
        approach="**Dry run** `/users/new` against `/users/:id` → score `[3,2]`; against `/users/new` → `[3,3]` wins; `/*` → `[1]` loses at position 0.",
        complexity="O(routes × segments).",
        pitfalls="Forgetting to strip the query string; a splat that requires at least one segment; summing scores (then a long "
                 "param-only pattern can beat a short static one).",
        follow_up="React Router ranks nested route branches with a similar scoring idea.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-optimistic-update", title="Optimistic updates with rollback", difficulty="Medium", pattern="Async UI",
    kind="js", entry="runOptimistic",
    description=r"""
An *optimistic* UI shows the result of an action before the server confirms it. The robust design keeps two things:
the last **confirmed** data and a queue of **pending** operations. What the user sees is always "confirmed data with
the pending operations replayed on top". A failure then needs no special undo: remove the operation and recompute.

`runOptimistic(initial, events)`: `initial` maps item id → like count (the confirmed data). Events:

- `{type:"mutate", reqId, id, delta}`: the user clicked. Queue the operation (ignore it when `id` is not in the
  confirmed data or `reqId` is already pending)
- `{type:"ok", reqId}`: the server accepted it. Apply its delta to the confirmed data and remove it from the queue
- `{type:"fail", reqId}`: the server rejected it. Remove it from the queue
- `{type:"refetch", data}`: fresh confirmed data arrived (same shape as `initial`). Pending operations stay queued

Unknown `reqId`s are ignored. When replaying or confirming, skip operations whose id is not present in the
confirmed data.

After **every** event record `{ view, pending }`: `view` is the id → count map the user sees, `pending` the queued
`reqId`s in order. Return the list of records.

**Example:** initial `{a:10}`; `mutate r1 +1`, `mutate r2 +1`, `fail r1`, `ok r2` → views `{a:11}`, `{a:12}`, `{a:11}`, `{a:11}`.
""",
    starter="function runOptimistic(initial, events) {\n  let confirmed = { ...initial };\n  let pending = [];\n  const out = [];\n  // ...\n  return out;\n}\n",
    solution=r'''function runOptimistic(initial, events) {
  let confirmed = { ...initial };
  let pending = [];
  const out = [];
  const has = (obj, id) => Object.prototype.hasOwnProperty.call(obj, id);
  for (const e of events) {
    if (e.type === "mutate") {
      if (has(confirmed, e.id) && !pending.some((p) => p.reqId === e.reqId)) {
        pending = [...pending, { reqId: e.reqId, id: e.id, delta: e.delta }];
      }
    } else if (e.type === "ok" || e.type === "fail") {
      const op = pending.find((p) => p.reqId === e.reqId);
      if (op) {
        pending = pending.filter((p) => p !== op);
        if (e.type === "ok" && has(confirmed, op.id)) confirmed = { ...confirmed, [op.id]: confirmed[op.id] + op.delta };
      }
    } else if (e.type === "refetch") {
      confirmed = { ...e.data };
    }
    const view = { ...confirmed };
    for (const op of pending) if (has(view, op.id)) view[op.id] += op.delta;
    out.push({ view, pending: pending.map((p) => p.reqId) });
  }
  return out;
}
''',
    tests=[
        [{"a": 10}, [{"type": "mutate", "reqId": "r1", "id": "a", "delta": 1}, {"type": "mutate", "reqId": "r2", "id": "a", "delta": 1}, {"type": "fail", "reqId": "r1"}, {"type": "ok", "reqId": "r2"}]],
        [{"a": 10}, []],
        [{"a": 10}, [{"type": "mutate", "reqId": "r1", "id": "a", "delta": 1}, {"type": "ok", "reqId": "r1"}]],
        [{"a": 10}, [{"type": "mutate", "reqId": "r1", "id": "a", "delta": 1}, {"type": "fail", "reqId": "r1"}]],
        [{"a": 10, "b": 0}, [{"type": "mutate", "reqId": "r1", "id": "zzz", "delta": 1}, {"type": "ok", "reqId": "r1"}, {"type": "fail", "reqId": "nope"}]],
        [{"a": 10, "b": 0}, [{"type": "mutate", "reqId": "r1", "id": "a", "delta": 1}, {"type": "mutate", "reqId": "r2", "id": "b", "delta": 5},
                              {"type": "mutate", "reqId": "r3", "id": "a", "delta": -1}, {"type": "fail", "reqId": "r2"}, {"type": "ok", "reqId": "r3"}, {"type": "ok", "reqId": "r1"}]],
        [{"a": 10}, [{"type": "mutate", "reqId": "r1", "id": "a", "delta": 1}, {"type": "refetch", "data": {"a": 50}}, {"type": "ok", "reqId": "r1"}]],
        [{"a": 10}, [{"type": "mutate", "reqId": "r1", "id": "a", "delta": 1}, {"type": "refetch", "data": {"a": 50}}, {"type": "fail", "reqId": "r1"}]],
        [{"a": 10, "b": 2}, [{"type": "mutate", "reqId": "r1", "id": "b", "delta": 3}, {"type": "refetch", "data": {"a": 11}}, {"type": "ok", "reqId": "r1"}, {"type": "refetch", "data": {"a": 11, "b": 9}}]],
        [{"a": 1}, [{"type": "mutate", "reqId": "r1", "id": "a", "delta": 1}, {"type": "mutate", "reqId": "r1", "id": "a", "delta": 100}, {"type": "ok", "reqId": "r1"}, {"type": "ok", "reqId": "r1"}]],
        [{"a": 0}, [{"type": "mutate", "reqId": "r%d" % i, "id": "a", "delta": 1} for i in range(8)] + [{"type": "fail" if i % 2 else "ok", "reqId": "r%d" % i} for i in range(8)]],
        [{"a": 5}, [{"type": "mutate", "reqId": "r1", "id": "a", "delta": 1}, {"type": "mutate", "reqId": "r2", "id": "a", "delta": 1}, {"type": "ok", "reqId": "r2"}, {"type": "fail", "reqId": "r1"}]],
    ],
    wrong_solutions=[
        r'''function runOptimistic(initial, events) {
  let view = { ...initial }; let pending = []; const out = [];
  for (const e of events) {
    if (e.type === "mutate") { if (e.id in view && !pending.some((p) => p.reqId === e.reqId)) { pending.push({ reqId: e.reqId, snapshot: { ...view } }); view = { ...view, [e.id]: view[e.id] + e.delta }; } }
    else if (e.type === "ok") pending = pending.filter((p) => p.reqId !== e.reqId);
    else if (e.type === "fail") { const op = pending.find((p) => p.reqId === e.reqId); if (op) { view = op.snapshot; pending = pending.filter((p) => p !== op); } }
    else if (e.type === "refetch") view = { ...e.data };
    out.push({ view: { ...view }, pending: pending.map((p) => p.reqId) });
  }
  return out;
}
''',
        r'''function runOptimistic(initial, events) {
  let confirmed = { ...initial }; let pending = []; const out = [];
  for (const e of events) {
    if (e.type === "mutate") { if (e.id in confirmed) pending.push({ reqId: e.reqId, id: e.id, delta: e.delta }); }
    else if (e.type === "ok") { const op = pending.find((p) => p.reqId === e.reqId); if (op) { pending = pending.filter((p) => p !== op); confirmed[op.id] += op.delta; } }
    else if (e.type === "fail") pending = pending.filter((p) => p.reqId !== e.reqId);
    else if (e.type === "refetch") { confirmed = { ...e.data }; pending = []; }
    const view = { ...confirmed };
    for (const op of pending) if (op.id in view) view[op.id] += op.delta;
    out.push({ view, pending: pending.map((p) => p.reqId) });
  }
  return out;
}
''',
    ],
    guide=G(
        prereqs="Lesson *Sorting, searching, pagination and optimistic updates*.",
        intuition="Do not edit the displayed data and then try to un-edit it. Keep truth and guesses apart, and derive the display: "
                  "`view = replay(pending, confirmed)`. Rollback becomes deletion.",
        hints=["Two variables: `confirmed` (object) and `pending` (array of operations).",
               "`ok` moves an operation's effect from the queue into the confirmed data; `fail` only removes it.",
               "Build the view after every event by copying `confirmed` and applying each pending delta."],
        brute_force="Snapshot the view on each click and restore the snapshot on failure. With two overlapping requests, restoring "
                    "the first snapshot also erases the second (still valid) click.",
        approach="**Dry run** (example): r1, r2 queued → view 12. `fail r1` → queue `[r2]` → view `10 + 1 = 11`. `ok r2` → confirmed 11, queue empty → view 11.",
        complexity="O(events × pending).",
        pitfalls="Clearing the queue on refetch loses clicks that are still in flight. Applying `ok` to the view as well as the "
                 "confirmed data double-counts.",
        follow_up="React 19's `useOptimistic(state, reducer)` implements exactly this replay model.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-firestore-query", title="A Firestore-style query over an array", difficulty="Medium", pattern="Firebase data",
    kind="js", entry="runQuery",
    description=r"""
Implement a small in-memory version of a Firestore collection query. `runQuery(docs, query)` returns the **ids** of
the matching documents in order. Every doc is `{ id, ...fields }`.

`query` may contain:

- `where`: a list of `[field, op, value]` filters, **all** of which must pass. `field` may be a dotted path such as
  `"stock.count"`. A document that lacks the field fails every filter on it.
  - `"=="`: strictly equal · `"!="`: field present and not strictly equal
  - `"<"`, `"<="`, `">"`, `">="`: only when the field value and `value` are **both numbers or both strings**; otherwise the filter fails
  - `"in"`: `value` is an array that contains the field value
  - `"array-contains"`: the field is an array that contains `value`
- `orderBy`: a list of `[field, "asc" | "desc"]`. Documents **missing any orderBy field are left out** (Firestore
  orders through an index, and a document without the field is not in that index). Later entries break ties of
  earlier ones. Remaining ties are broken by `id`, in the direction of the **last** orderBy entry. With no
  `orderBy`, sort by `id` ascending. Assume the values of an orderBy field are all numbers or all strings
- `startAfter`: a list of values, one per orderBy entry (a cursor). Keep only documents that come strictly **after**
  that position in the sort order (compare the orderBy fields only)
- `limit`: keep at most this many documents (applied last)

**Example:** `runQuery(docs, {where:[["city","==","Oslo"],["price",">=",20]], orderBy:[["price","desc"]], limit:2})`
""",
    starter="function runQuery(docs, query) {\n  // filter -> order -> cursor -> limit -> ids\n  return [];\n}\n",
    solution=r'''function runQuery(docs, query) {
  const get = (doc, path) => path.split(".").reduce(
    (value, key) => (value !== null && typeof value === "object" && Object.prototype.hasOwnProperty.call(value, key) ? value[key] : undefined), doc);
  const comparable = (a, b) => typeof a === typeof b && (typeof a === "number" || typeof a === "string");
  const passes = (doc, [field, op, value]) => {
    const v = get(doc, field);
    if (v === undefined) return false;
    switch (op) {
      case "==": return v === value;
      case "!=": return v !== value;
      case "<": return comparable(v, value) && v < value;
      case "<=": return comparable(v, value) && v <= value;
      case ">": return comparable(v, value) && v > value;
      case ">=": return comparable(v, value) && v >= value;
      case "in": return value.includes(v);
      case "array-contains": return Array.isArray(v) && v.includes(value);
      default: return false;
    }
  };
  const where = query.where || [];
  const orderBy = query.orderBy || [];
  const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);
  const idSign = orderBy.length > 0 && orderBy[orderBy.length - 1][1] === "desc" ? -1 : 1;
  let rows = docs
    .filter((doc) => where.every((filter) => passes(doc, filter)))
    .filter((doc) => orderBy.every(([field]) => get(doc, field) !== undefined));
  rows = rows.slice().sort((a, b) => {
    for (const [field, dir] of orderBy) {
      const c = cmp(get(a, field), get(b, field));
      if (c !== 0) return dir === "desc" ? -c : c;
    }
    return idSign * cmp(a.id, b.id);
  });
  if (query.startAfter) {
    rows = rows.filter((doc) => {
      for (let i = 0; i < orderBy.length; i++) {
        const [field, dir] = orderBy[i];
        const c = cmp(get(doc, field), query.startAfter[i]);
        if (c !== 0) return dir === "desc" ? c < 0 : c > 0;
      }
      return false;
    });
  }
  if (typeof query.limit === "number") rows = rows.slice(0, query.limit);
  return rows.map((doc) => doc.id);
}
''',
    tests=[
        [DOCS, {"where": [["city", "==", "Oslo"], ["price", ">=", 20]], "orderBy": [["price", "desc"]], "limit": 2}],
        [DOCS, {}],
        [list(reversed(DOCS)), {"limit": 3}],
        [DOCS, {"where": [["city", "!=", "Oslo"]], "orderBy": [["price", "asc"]]}],
        [DOCS, {"where": [["tags", "array-contains", "sale"]]}],
        [DOCS, {"where": [["city", "in", ["Lima", "Pune"]], ["stock.count", ">", 2]]}],
        [DOCS, {"orderBy": [["city", "asc"], ["price", "desc"]]}],
        [DOCS, {"orderBy": [["stock.count", "desc"]]}],
        [DOCS, {"orderBy": [["price", "asc"]], "limit": 4}],
        [DOCS, {"orderBy": [["price", "asc"]], "startAfter": [24], "limit": 4}],
        [DOCS, {"orderBy": [["city", "desc"], ["price", "asc"]], "startAfter": ["Oslo", 11]}],
        [DOCS_GAPS, {"where": [["price", ">=", 0]], "orderBy": [["price", "asc"]]}],
        [DOCS_GAPS, {"where": [["price", ">", 5]]}],
        [DOCS_GAPS, {"where": [["price", "!=", 10]]}],
        [DOCS_GAPS, {"where": [["city", "==", None]]}],
        [[], {"where": [["a", "==", 1]], "orderBy": [["a", "asc"]], "limit": 5}],
        [DOCS, {"where": [["price", "<", 0]]}],
        [DOCS, {"orderBy": [["price", "desc"]], "limit": 0}],
    ],
    wrong_solutions=[
        r'''function runQuery(docs, query) {
  const get = (doc, path) => path.split(".").reduce((v, k) => (v == null ? undefined : v[k]), doc);
  const ops = { "==": (a, b) => a === b, "!=": (a, b) => a !== b, "<": (a, b) => a < b, "<=": (a, b) => a <= b, ">": (a, b) => a > b, ">=": (a, b) => a >= b,
    "in": (a, b) => b.includes(a), "array-contains": (a, b) => Array.isArray(a) && a.includes(b) };
  let rows = docs.filter((d) => (query.where || []).every(([f, op, v]) => ops[op](get(d, f), v)));
  const orderBy = query.orderBy || [];
  rows = rows.slice().sort((a, b) => {
    for (const [f, dir] of orderBy) { const x = get(a, f), y = get(b, f); if (x < y) return dir === "desc" ? 1 : -1; if (x > y) return dir === "desc" ? -1 : 1; }
    return a.id < b.id ? -1 : 1;
  });
  if (typeof query.limit === "number") rows = rows.slice(0, query.limit);
  return rows.map((d) => d.id);
}
''',
        r'''function runQuery(docs, query) {
  const get = (doc, path) => path.split(".").reduce((v, k) => (v !== null && typeof v === "object" && k in v ? v[k] : undefined), doc);
  const ok = (a, b) => typeof a === typeof b && (typeof a === "number" || typeof a === "string");
  const pass = (d, [f, op, val]) => { const v = get(d, f); if (v === undefined) return false;
    return op === "==" ? v === val : op === "!=" ? v !== val : op === "<" ? ok(v, val) && v < val : op === "<=" ? ok(v, val) && v <= val :
      op === ">" ? ok(v, val) && v > val : op === ">=" ? ok(v, val) && v >= val : op === "in" ? val.includes(v) : Array.isArray(v) && v.includes(val); };
  const orderBy = query.orderBy || [];
  let rows = docs.filter((d) => (query.where || []).every((w) => pass(d, w))).filter((d) => orderBy.every(([f]) => get(d, f) !== undefined));
  if (typeof query.limit === "number") rows = rows.slice(0, query.limit);
  const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);
  rows = rows.slice().sort((a, b) => { for (const [f, dir] of orderBy) { const c = cmp(get(a, f), get(b, f)); if (c) return dir === "desc" ? -c : c; } return cmp(a.id, b.id); });
  return rows.map((d) => d.id);
}
''',
    ],
    guide=G(
        prereqs="Array `filter`/`sort`; lesson *Firestore and the Realtime Database*.",
        intuition="A query is a pipeline: filter, order, skip to the cursor, cut to the limit. The Firestore-specific twists are "
                  "that missing fields silently exclude documents and that every ordering ends with the document id as a tiebreaker.",
        hints=["Write `get(doc, \"a.b\")` first and make it return `undefined` for anything missing.",
               "Build one comparator that loops over the `orderBy` entries and falls back to the id.",
               "For `startAfter`, reuse the comparison logic: keep a doc when its first differing orderBy value lies after the cursor's."],
        brute_force="Sort first and filter afterwards, or apply the limit before ordering (second wrong solution): the top-2 of an "
                    "unsorted list are not the top-2 by price.",
        approach="**Dry run** (example): Oslo docs with price ≥ 20 → sort by price descending → first two ids.",
        complexity="O(n · f + n log n) for n docs and f filters.",
        pitfalls="JavaScript happily evaluates `\"cheap\" > 5` (false) and `undefined < 3` (false) but also `null >= 0` (true): "
                 "always check types before range comparisons. Forgetting the id tiebreak makes pagination skip or repeat rows.",
        follow_up="Real Firestore additionally requires a composite index for most multi-field queries and restricts which filter combinations are allowed.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-rules-evaluator", title="Evaluate security rules", difficulty="Hard", pattern="Firebase security",
    kind="js", entry="evaluate",
    description=r"""
Database security rules answer one question: may **this** user perform **this** operation on **this** path? Build an
evaluator for a small rule language (rules arrive as JSON, so there is nothing to parse).

`evaluate(rules, request)`

**Request:** `{ op, path, auth, data, existing }`. `op` is `"get" | "list" | "create" | "update" | "delete"`;
`auth` is `null` or `{ uid, token }`; `data` is the incoming document; `existing` the stored one (either may be `null`).

**Rule:** `{ match, allow, if }`

- `match` is a path pattern. `{name}` matches one segment and binds it; `{name=**}` (last segment only) matches
  **one or more** remaining segments and binds them joined by `/`; other segments must be equal. Segment counts must agree
- `allow` lists operations; `"read"` stands for `get` + `list` and `"write"` for `create` + `update` + `delete`
- `if` is a condition expression; a missing `if` means `true`

**Expressions**

- a string, number, boolean or `null` is a literal; an array is a list of expressions
- `{ var: "a.b.c" }` looks the path up in the scope `{ auth, data, existing, params }`. Stepping **through** `null`,
  a non-object, or a key that does not exist is an **error**. (The final value may be `null`.)
- `{ op, args }`: `"and"` / `"or"` evaluate left to right and stop early; every operand they evaluate must be a
  boolean, otherwise error. `"not"` needs a boolean. `"eq"` / `"neq"` use strict equality.
  `"lt" "lte" "gt" "gte"` need two numbers or two strings, otherwise error. `"in"`: `args[1]` must evaluate to an
  array (else error) and the result is whether it contains `args[0]`

A rule **grants** access when its path matches, its `allow` covers the operation and its condition evaluates to
exactly `true`. An error means that rule does not grant. Access is denied unless some rule grants it.

Return `{ allowed, matched, granted }`: `matched` holds the indexes of rules whose path and operation matched,
`granted` the indexes that granted.
""",
    starter="function evaluate(rules, request) {\n  return { allowed: false, matched: [], granted: [] };\n}\n",
    solution=r'''function evaluate(rules, request) {
  const expand = { read: ["get", "list"], write: ["create", "update", "delete"] };
  const reqSegs = request.path.split("/").filter(Boolean);
  const own = (obj, key) => Object.prototype.hasOwnProperty.call(obj, key);

  const matchPath = (pattern) => {
    const segs = pattern.split("/").filter(Boolean);
    const params = {};
    for (let i = 0; i < segs.length; i++) {
      const m = /^\{(\w+)(=\*\*)?\}$/.exec(segs[i]);
      if (i >= reqSegs.length) return null;
      if (m && m[2]) {
        params[m[1]] = reqSegs.slice(i).join("/");
        return params;
      }
      if (m) params[m[1]] = reqSegs[i];
      else if (segs[i] !== reqSegs[i]) return null;
    }
    return segs.length === reqSegs.length ? params : null;
  };

  const ev = (e, scope) => {
    if (e === null || typeof e !== "object") return e;
    if (Array.isArray(e)) return e.map((x) => ev(x, scope));
    if (own(e, "var")) {
      let cur = scope;
      for (const key of e.var.split(".")) {
        if (cur === null || typeof cur !== "object" || !own(cur, key)) throw new Error("lookup failed");
        cur = cur[key];
      }
      return cur;
    }
    const args = e.args || [];
    const bool = (v) => { if (typeof v !== "boolean") throw new Error("not a boolean"); return v; };
    const pair = () => {
      const a = ev(args[0], scope);
      const b = ev(args[1], scope);
      if (typeof a !== typeof b || (typeof a !== "number" && typeof a !== "string")) throw new Error("not comparable");
      return [a, b];
    };
    switch (e.op) {
      case "and": for (const x of args) if (!bool(ev(x, scope))) return false; return true;
      case "or": for (const x of args) if (bool(ev(x, scope))) return true; return false;
      case "not": return !bool(ev(args[0], scope));
      case "eq": return ev(args[0], scope) === ev(args[1], scope);
      case "neq": return ev(args[0], scope) !== ev(args[1], scope);
      case "lt": { const [a, b] = pair(); return a < b; }
      case "lte": { const [a, b] = pair(); return a <= b; }
      case "gt": { const [a, b] = pair(); return a > b; }
      case "gte": { const [a, b] = pair(); return a >= b; }
      case "in": {
        const item = ev(args[0], scope);
        const list = ev(args[1], scope);
        if (!Array.isArray(list)) throw new Error("not a list");
        return list.includes(item);
      }
      default: throw new Error("unknown op");
    }
  };

  const matched = [];
  const granted = [];
  rules.forEach((rule, index) => {
    const params = matchPath(rule.match);
    if (!params) return;
    const ops = rule.allow.flatMap((name) => expand[name] || [name]);
    if (!ops.includes(request.op)) return;
    matched.push(index);
    let ok = false;
    try {
      const scope = { auth: request.auth, data: request.data, existing: request.existing, params };
      ok = rule.if === undefined ? true : ev(rule.if, scope) === true;
    } catch (err) {
      ok = false;
    }
    if (ok) granted.push(index);
  });
  return { allowed: granted.length > 0, matched, granted };
}
''',
    tests=[
        [RULES, _req("get", "/posts/p1", None, None, {"published": True, "authorId": "ann"})],
        [RULES, _req("get", "/posts/p1", None, None, {"published": False, "authorId": "ann"})],
        [RULES, _req("get", "/posts/p1", ANN, None, {"published": False, "authorId": "ann"})],
        [RULES, _req("list", "/posts/p1", {"uid": "bob", "token": {"roles": []}}, None, {"published": False, "authorId": "ann"})],
        [RULES, _req("create", "/posts/p9", ANN, {"authorId": "ann", "title": "Hi"}, None)],
        [RULES, _req("create", "/posts/p9", ANN, {"authorId": "bob", "title": "Hi"}, None)],
        [RULES, _req("create", "/posts/p9", None, {"authorId": "ann"}, None)],
        [RULES, _req("update", "/posts/p1", None, {"title": "x"}, {"authorId": "ann"})],
        [RULES, _req("delete", "/posts/p1", ROOT, None, {"authorId": "ann"})],
        [RULES, _req("update", "/users/ann", ANN, {"name": "Ann"}, None)],
        [RULES, _req("get", "/users/bob", ANN, None, {"name": "Bob"})],
        [RULES, _req("get", "/public/img/logo.png", None, None, None)],
        [RULES, _req("list", "/public/img", None, None, None)],
        [RULES, _req("get", "/public", None, None, None)],
        [RULES, _req("create", "/scores/s1", None, {"points": 50}, None)],
        [RULES, _req("create", "/scores/s1", None, {"points": "50"}, None)],
        [RULES, _req("create", "/scores/s1", None, {"points": 101}, None)],
        [RULES, _req("create", "/posts/p1/comments/c1", ANN, {"text": "nice"}, None)],
        [RULES, _req("create", "/posts/p1/comments/c1", None, {"text": "spam"}, None)],
        [RULES, _req("get", "/secret/x", {"uid": "eve", "token": {}}, None, None)],
        [[], _req("get", "/anything", ROOT, None, None)],
        [[{"match": "/a/{id}", "allow": ["read"], "if": {"op": "or", "args": [True, {"var": "nope.deep"}]}},
          {"match": "/a/{id}", "allow": ["read"], "if": {"op": "or", "args": [{"var": "nope.deep"}, True]}},
          {"match": "/a/{id}", "allow": ["read"], "if": "yes"},
          {"match": "/a/{id}", "allow": ["read"], "if": {"op": "and", "args": []}}], _req("get", "/a/1")],
    ],
    wrong_solutions=[
        r'''function evaluate(rules, request) {
  const expand = { read: ["get", "list"], write: ["create", "update", "delete"] };
  const reqSegs = request.path.split("/").filter(Boolean);
  const matchPath = (pattern) => {
    const segs = pattern.split("/").filter(Boolean); const params = {};
    for (let i = 0; i < segs.length; i++) {
      const m = /^\{(\w+)(=\*\*)?\}$/.exec(segs[i]);
      if (i >= reqSegs.length) return null;
      if (m && m[2]) { params[m[1]] = reqSegs.slice(i).join("/"); return params; }
      if (m) params[m[1]] = reqSegs[i]; else if (segs[i] !== reqSegs[i]) return null;
    }
    return segs.length === reqSegs.length ? params : null;
  };
  const ev = (e, scope) => {
    if (e === null || typeof e !== "object") return e;
    if (Array.isArray(e)) return e.map((x) => ev(x, scope));
    if ("var" in e) return e.var.split(".").reduce((c, k) => (c == null ? undefined : c[k]), scope);
    const a = (e.args || []).map((x) => ev(x, scope));
    switch (e.op) {
      case "and": return a.every(Boolean);
      case "or": return a.some(Boolean);
      case "not": return !a[0];
      case "eq": return a[0] === a[1];
      case "neq": return a[0] !== a[1];
      case "lt": return a[0] < a[1];
      case "lte": return a[0] <= a[1];
      case "gt": return a[0] > a[1];
      case "gte": return a[0] >= a[1];
      case "in": return Array.isArray(a[1]) && a[1].includes(a[0]);
    }
  };
  const matched = [], granted = [];
  rules.forEach((rule, i) => {
    const params = matchPath(rule.match); if (!params) return;
    if (!rule.allow.flatMap((n) => expand[n] || [n]).includes(request.op)) return;
    matched.push(i);
    if (rule.if === undefined || ev(rule.if, { auth: request.auth, data: request.data, existing: request.existing, params })) granted.push(i);
  });
  return { allowed: granted.length > 0, matched, granted };
}
''',
    ],
    guide=G(
        prereqs="Recursion over expression trees; lesson *Security rules*.",
        intuition="Three independent pieces: a path matcher that produces bindings, an operation check, and a tiny interpreter. "
                  "Rules are OR-ed together, and anything unexpected (a missing field, a wrong type) counts as 'no' for that rule only.",
        hints=["Write `matchPath(pattern)` returning a params object or `null`.",
               "The interpreter is one recursive function: literal, array, `var`, operator. Throw on every error case.",
               "Wrap each rule's condition in `try/catch`; a throw means the rule does not grant."],
        brute_force="Evaluate with JavaScript truthiness and no errors (the wrong solution). Then `undefined !== null` makes "
                    "'auth is not null' checks pass on missing data, `\"50\" >= 0` passes a string where a number was required, "
                    "and unauthenticated users slip through, which is the classic way real rule sets leak.",
        approach="**Dry run** `update /posts/p1`, `auth: null`: rule 2 matches path and op; `auth.uid` steps through `null` → error → "
                 "not granted. Rule 5 (`/{path=**}`) matches; `auth.token.roles` errors → not granted. Denied, `matched: [2, 5]`.",
        complexity="O(rules × (path length + expression size)).",
        pitfalls="Letting `{name=**}` match zero segments; treating truthy non-booleans as true; aborting the whole evaluation "
                 "when one rule errors; forgetting that rules never *revoke* access another rule granted.",
        follow_up="Real Firestore rules add functions, `get()` lookups of other documents and `request.resource.data` validation.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-route-guard", title="Role-based route guard", difficulty="Easy", pattern="Auth",
    kind="js", entry="guardRoute",
    description=r"""
Before rendering a page, a protected-route component decides what to do with the visitor. Write
`guardRoute(route, session)`.

`route`: `{ path, public?, guestOnly?, requireVerified?, roles? }` · `session`: `{ status, user }` where `status` is
`"loading"` (the auth library has not yet reported whether someone is signed in), `"anonymous"` or
`"authenticated"`, and `user` is `null` or `{ roles: [...], emailVerified }`.

Apply the **first** rule that fits and return `{ action, to }` (`to` is `null` unless redirecting):

1. `route.public` → `render`
2. status `"loading"` → `wait` (show a spinner; redirecting now would kick out users who are in fact signed in)
3. `route.guestOnly` (sign-in / sign-up pages): authenticated → `redirect` to `"/"`; anonymous → `render`
4. anonymous → `redirect` to `"/signin?next="` + `encodeURIComponent(route.path)`
5. `route.requireVerified` and the email is not verified → `redirect` to `"/verify-email"`
6. `route.roles` is a non-empty list and the user has none of those roles → `redirect` to `"/forbidden"`
7. otherwise → `render`

**Example:** `guardRoute({path:"/admin/users", roles:["admin"]}, {status:"anonymous", user:null})` →
`{action:"redirect", to:"/signin?next=%2Fadmin%2Fusers"}`
""",
    starter="function guardRoute(route, session) {\n  return { action: \"render\", to: null };\n}\n",
    solution=r'''function guardRoute(route, session) {
  const render = { action: "render", to: null };
  const redirect = (to) => ({ action: "redirect", to });
  if (route.public) return render;
  if (session.status === "loading") return { action: "wait", to: null };
  const signedIn = session.status === "authenticated";
  if (route.guestOnly) return signedIn ? redirect("/") : render;
  if (!signedIn) return redirect("/signin?next=" + encodeURIComponent(route.path));
  const user = session.user;
  if (route.requireVerified && !user.emailVerified) return redirect("/verify-email");
  const roles = route.roles || [];
  if (roles.length > 0 && !roles.some((role) => user.roles.includes(role))) return redirect("/forbidden");
  return render;
}
''',
    tests=[
        [{"path": "/admin/users", "roles": ["admin"]}, {"status": "anonymous", "user": None}],
        [{"path": "/", "public": True}, {"status": "loading", "user": None}],
        [{"path": "/dashboard"}, {"status": "loading", "user": None}],
        [{"path": "/dashboard"}, {"status": "authenticated", "user": {"roles": [], "emailVerified": False}}],
        [{"path": "/signin", "guestOnly": True}, {"status": "anonymous", "user": None}],
        [{"path": "/signin", "guestOnly": True}, {"status": "authenticated", "user": {"roles": [], "emailVerified": True}}],
        [{"path": "/signin", "guestOnly": True}, {"status": "loading", "user": None}],
        [{"path": "/billing", "requireVerified": True}, {"status": "authenticated", "user": {"roles": ["member"], "emailVerified": False}}],
        [{"path": "/billing", "requireVerified": True}, {"status": "authenticated", "user": {"roles": ["member"], "emailVerified": True}}],
        [{"path": "/admin", "roles": ["admin", "owner"]}, {"status": "authenticated", "user": {"roles": ["member"], "emailVerified": True}}],
        [{"path": "/admin", "roles": ["admin", "owner"]}, {"status": "authenticated", "user": {"roles": ["member", "owner"], "emailVerified": True}}],
        [{"path": "/admin", "roles": ["admin"], "requireVerified": True}, {"status": "authenticated", "user": {"roles": [], "emailVerified": False}}],
        [{"path": "/notes", "roles": []}, {"status": "authenticated", "user": {"roles": [], "emailVerified": False}}],
        [{"path": "/search?q=a b&x=1"}, {"status": "anonymous", "user": None}],
        [{"path": "/about", "public": True, "roles": ["admin"]}, {"status": "anonymous", "user": None}],
    ],
    wrong_solutions=[
        r'''function guardRoute(route, session) {
  if (route.public) return { action: "render", to: null };
  if (!session.user) return { action: "redirect", to: "/signin?next=" + route.path };
  if (route.roles && !route.roles.some((r) => session.user.roles.includes(r))) return { action: "redirect", to: "/forbidden" };
  if (route.requireVerified && !session.user.emailVerified) return { action: "redirect", to: "/verify-email" };
  return { action: "render", to: null };
}
''',
    ],
    guide=G(
        prereqs="Lesson *Sessions, protected routes and roles*.",
        intuition="A guard is an ordered checklist. The order encodes priority: 'we do not know yet' must come before "
                  "'not signed in', and 'who are you' before 'what may you do'.",
        hints=["Return early for each rule, in the listed order.", "There are three session states, not two: handle `loading` explicitly.",
               "`roles.some(r => user.roles.includes(r))` expresses 'has at least one of'."],
        brute_force="A boolean `isLoggedIn`. On page refresh the app renders once before the auth library answers, so a signed-in "
                    "user is bounced to the sign-in page and loses their place.",
        approach="**Dry run** (example): not public; not loading; not guest-only; anonymous → redirect with the encoded path.",
        complexity="O(roles).",
        pitfalls="Not encoding the `next` parameter (a path containing `&` or `?` gets cut off). Treating an empty `roles` list as "
                 "'nobody allowed'. Remember this guard is for user experience only: real enforcement is in the database rules.",
        follow_up="Validate `next` after sign-in so it only ever points inside your own site (open-redirect protection).",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-entity-cache", title="Normalise nested data into an entity cache", difficulty="Medium", pattern="State shape",
    kind="js", entry="normalizePosts",
    description=r"""
An API returns posts with their author and comments nested inside. Storing that as-is duplicates each user many
times, so renaming one user means hunting down every copy. A *normalised* store keeps each entity once, in a table
keyed by id, and links entities by id.

`normalizePosts(posts)` receives

```
[{ id, title, author: { id, name, ... }, comments: [{ id, text, author: { id, name, ... } }] }]
```

(`comments` may be missing) and returns three tables, each `{ byId, allIds }`:

- `users`: every author found (of posts and comments)
- `posts`: each post with `author` replaced by `authorId` and `comments` replaced by `commentIds` (`[]` when missing)
- `comments`: each comment with `author` replaced by `authorId`

Rules: `allIds` lists ids in **first-seen** order without duplicates (for each post: its author first, then the
post, then each comment's author followed by the comment). When the same id appears again, **shallow-merge** the new
fields over the stored ones (later data wins). All other fields are kept as they are. Do not modify the input.
""",
    starter="function normalizePosts(posts) {\n  const table = () => ({ byId: {}, allIds: [] });\n  const users = table(), postsT = table(), comments = table();\n  // ...\n  return { users, posts: postsT, comments };\n}\n",
    solution=r'''function normalizePosts(posts) {
  const table = () => ({ byId: {}, allIds: [] });
  const users = table();
  const postTable = table();
  const comments = table();
  const upsert = (t, entity) => {
    if (!Object.prototype.hasOwnProperty.call(t.byId, entity.id)) t.allIds.push(entity.id);
    t.byId[entity.id] = { ...t.byId[entity.id], ...entity };
  };
  for (const post of posts) {
    const { author, comments: nested = [], ...postFields } = post;
    upsert(users, author);
    upsert(postTable, { ...postFields, authorId: author.id, commentIds: nested.map((c) => c.id) });
    for (const comment of nested) {
      const { author: commentAuthor, ...commentFields } = comment;
      upsert(users, commentAuthor);
      upsert(comments, { ...commentFields, authorId: commentAuthor.id });
    }
  }
  return { users, posts: postTable, comments };
}
''',
    tests=[
        [[{"id": "p1", "title": "Hello", "author": {"id": "u1", "name": "Ann"},
           "comments": [{"id": "c1", "text": "Nice", "author": {"id": "u2", "name": "Bob"}}, {"id": "c2", "text": "Thanks", "author": {"id": "u1", "name": "Ann"}}]}]],
        [[]],
        [[{"id": "p1", "title": "Solo", "author": {"id": "u1", "name": "Ann"}}]],
        [[{"id": "p1", "title": "A", "author": {"id": "u1", "name": "Ann"}, "comments": []},
          {"id": "p2", "title": "B", "author": {"id": "u1", "name": "Ann B.", "avatar": "a.png"}, "comments": []}]],
        [[{"id": "p1", "title": "A", "author": {"id": "u1", "name": "Ann", "bio": "hi"}, "comments": [{"id": "c1", "text": "x", "author": {"id": "u1", "name": "Annie"}}]}]],
        [[{"id": "p1", "title": "Old", "likes": 1, "author": {"id": "u1", "name": "Ann"}, "comments": [{"id": "c1", "text": "x", "author": {"id": "u2", "name": "Bob"}}]},
          {"id": "p1", "title": "New", "author": {"id": "u1", "name": "Ann"}, "comments": []}]],
        [[{"id": 2, "title": "Numbers", "tags": ["a", "b"], "author": {"id": 10, "name": "N"}, "comments": [{"id": 7, "text": "t", "likes": 3, "author": {"id": 11, "name": "M"}}]},
          {"id": 1, "title": "Earlier id, later seen", "author": {"id": 11, "name": "M"}}]],
        [[{"id": "p%d" % i, "title": "T%d" % i, "author": {"id": "u%d" % (i % 3), "name": "User %d" % (i % 3)},
           "comments": [{"id": "c%d-%d" % (i, j), "text": "c", "author": {"id": "u%d" % ((i + j) % 4), "name": "User %d" % ((i + j) % 4)}} for j in range(i % 3)]} for i in range(8)]],
        [[{"id": "p1", "title": "Shared comment", "author": {"id": "u1", "name": "A"}, "comments": [{"id": "c1", "text": "first", "author": {"id": "u2", "name": "B"}}]},
          {"id": "p2", "title": "Again", "author": {"id": "u2", "name": "B"}, "comments": [{"id": "c1", "text": "edited", "author": {"id": "u2", "name": "B"}}]}]],
        [[{"id": "p1", "title": "No comments key", "meta": {"views": 3}, "author": {"id": "u9", "name": "Z", "roles": ["admin"]}}]],
    ],
    wrong_solutions=[
        r'''function normalizePosts(posts) {
  const table = () => ({ byId: {}, allIds: [] });
  const users = table(), postTable = table(), comments = table();
  const put = (t, e) => { t.allIds.push(e.id); t.byId[e.id] = e; };
  for (const post of posts) {
    const { author, comments: nested = [], ...rest } = post;
    put(users, author);
    put(postTable, { ...rest, authorId: author.id, commentIds: nested.map((c) => c.id) });
    for (const c of nested) { const { author: a, ...cr } = c; put(users, a); put(comments, { ...cr, authorId: a.id }); }
  }
  return { users, posts: postTable, comments };
}
''',
        r'''function normalizePosts(posts) {
  const table = () => ({ byId: {}, allIds: [] });
  const users = table(), postTable = table(), comments = table();
  const put = (t, e) => { if (!(e.id in t.byId)) { t.allIds.push(e.id); t.byId[e.id] = e; } };
  for (const post of posts) {
    put(users, post.author);
    put(postTable, { ...post, authorId: post.author.id, commentIds: (post.comments || []).map((c) => c.id) });
    for (const c of post.comments || []) { put(users, c.author); put(comments, { ...c, authorId: c.author.id }); }
  }
  return { users, posts: postTable, comments };
}
''',
    ],
    guide=G(
        prereqs="Destructuring with rest; lesson *Context and global state* (state shape).",
        intuition="Treat the response like rows arriving for three database tables. One `upsert(table, entity)` helper does all the "
                  "work; the loop only decides which table each piece belongs to and swaps nested objects for ids.",
        hints=["Write `upsert` first: push the id if it is new, then merge.",
               "Destructure `author` and `comments` out of the post; the rest are the post's own fields.",
               "Follow the stated visiting order so `allIds` comes out right."],
        brute_force="Keep the nested array and search it on every update: O(posts × comments) per change and duplicated users that drift apart.",
        approach="**Dry run** (first test): upsert user u1; post p1 `{title, authorId:u1, commentIds:[c1,c2]}`; user u2, comment c1; user u1 again (merge, no new id), comment c2.",
        complexity="O(total entities) time and space.",
        pitfalls="Pushing ids twice; replacing instead of merging (a comment author with fewer fields wipes the fuller profile); "
                 "leaving the nested `author` object inside the stored post.",
        follow_up="Reading back ('denormalising') for one screen is a selector: `ids.map(id => byId[id])`. Firestore and the Realtime "
                  "Database push you towards the same flat, id-linked shape.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-snapshot-changes", title="Apply realtime snapshot changes", difficulty="Easy", pattern="Firebase data",
    kind="js", entry="applyChanges",
    description=r"""
A realtime listener does not have to hand you the whole list each time. Firestore's `snapshot.docChanges()` reports
what changed since the previous snapshot, with the positions involved. Write `applyChanges(list, changes)` that
applies them **in order** to a copy of `list` (an array of `{ id, ... }`) and returns the new array.

| change | meaning |
|---|---|
| `{type:"added", doc, newIndex}` | insert `doc` at `newIndex` |
| `{type:"removed", doc, oldIndex}` | remove the element at `oldIndex` |
| `{type:"modified", doc, oldIndex, newIndex}` | remove the element at `oldIndex`, then insert the new `doc` at `newIndex` (the indexes differ when the change affected the sort position) |

Indexes always refer to the list as it is at the moment that change is applied. Do not modify `list`.

**Example:** list `[{id:"a",n:1},{id:"b",n:2}]`, changes
`[{type:"modified", doc:{id:"a",n:9}, oldIndex:0, newIndex:1}, {type:"added", doc:{id:"c",n:0}, newIndex:0}]`
→ `[{id:"c",n:0},{id:"b",n:2},{id:"a",n:9}]`
""",
    starter="function applyChanges(list, changes) {\n  const next = list.slice();\n  // ...\n  return next;\n}\n",
    solution=r'''function applyChanges(list, changes) {
  const next = list.slice();
  for (const change of changes) {
    if (change.type === "removed" || change.type === "modified") next.splice(change.oldIndex, 1);
    if (change.type === "added" || change.type === "modified") next.splice(change.newIndex, 0, change.doc);
  }
  return next;
}
''',
    tests=[
        [[{"id": "a", "n": 1}, {"id": "b", "n": 2}], [{"type": "modified", "doc": {"id": "a", "n": 9}, "oldIndex": 0, "newIndex": 1}, {"type": "added", "doc": {"id": "c", "n": 0}, "newIndex": 0}]],
        [[], []],
        [[], [{"type": "added", "doc": {"id": "a"}, "newIndex": 0}, {"type": "added", "doc": {"id": "b"}, "newIndex": 1}, {"type": "added", "doc": {"id": "c"}, "newIndex": 1}]],
        [[{"id": "a"}, {"id": "b"}, {"id": "c"}], [{"type": "removed", "doc": {"id": "b"}, "oldIndex": 1}]],
        [[{"id": "a"}, {"id": "b"}, {"id": "c"}], [{"type": "removed", "doc": {"id": "a"}, "oldIndex": 0}, {"type": "removed", "doc": {"id": "c"}, "oldIndex": 1}]],
        [[{"id": "a", "v": 1}, {"id": "b", "v": 2}], [{"type": "modified", "doc": {"id": "b", "v": 20}, "oldIndex": 1, "newIndex": 1}]],
        [[{"id": "a", "v": 1}, {"id": "b", "v": 2}, {"id": "c", "v": 3}], [{"type": "modified", "doc": {"id": "c", "v": 0}, "oldIndex": 2, "newIndex": 0}]],
        [[{"id": "a", "v": 1}, {"id": "b", "v": 2}, {"id": "c", "v": 3}], [{"type": "modified", "doc": {"id": "a", "v": 5}, "oldIndex": 0, "newIndex": 2},
                                                                              {"type": "removed", "doc": {"id": "b"}, "oldIndex": 0}, {"type": "added", "doc": {"id": "d", "v": 4}, "newIndex": 1}]],
        [[{"id": "x"}], [{"type": "removed", "doc": {"id": "x"}, "oldIndex": 0}, {"type": "added", "doc": {"id": "x", "back": True}, "newIndex": 0}]],
        [[{"id": str(i)} for i in range(10)], [{"type": "removed", "doc": {"id": str(i)}, "oldIndex": 0} for i in range(5)] + [{"type": "added", "doc": {"id": "new"}, "newIndex": 5}]],
        [[{"id": "a", "v": 1}], [{"type": "unknown", "doc": {"id": "q"}}]],
    ],
    wrong_solutions=[
        r'''function applyChanges(list, changes) {
  const next = list.slice();
  for (const c of changes) {
    if (c.type === "added") next.push(c.doc);
    else if (c.type === "removed") next.splice(c.oldIndex, 1);
    else if (c.type === "modified") next[c.oldIndex] = c.doc;
  }
  return next;
}
''',
        r'''function applyChanges(list, changes) {
  let next = list.slice();
  for (const c of changes) {
    if (c.type === "added") next.splice(c.newIndex, 0, c.doc);
    else if (c.type === "removed") next = next.filter((d) => d.id !== c.doc.id);
    else if (c.type === "modified") { next.splice(c.newIndex, 0, c.doc); next.splice(c.oldIndex, 1); }
  }
  return next;
}
''',
    ],
    guide=G(
        prereqs="`Array.prototype.splice`; lesson *Firestore and the Realtime Database*.",
        intuition="Each change is a remove, an insert, or both. `modified` is 'remove from the old seat, sit down in the new seat'.",
        hints=["Copy the list once at the start.", "Do the removal before the insertion for `modified`.",
               "Two `if` statements cover all three types."],
        brute_force="Throw the list away and rebuild it from `snapshot.docs` each time. That is fine for small lists (and is what "
                    "most apps do); `docChanges` matters for animations and very long lists.",
        approach="**Dry run** (example): remove index 0 → `[b]`; insert `a(9)` at 1 → `[b, a]`; insert `c` at 0 → `[c, b, a]`.",
        complexity="O(changes × n) because `splice` shifts elements.",
        pitfalls="Appending added docs ignores the query's ordering. Inserting before removing shifts the old index.",
        follow_up="The first snapshot of a listener reports every existing document as `added`.",
    ),
),
]
