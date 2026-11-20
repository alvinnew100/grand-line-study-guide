_LOG = [
    "SELECT * FROM journal_entry ORDER BY id LIMIT 3",
    "SELECT * FROM auth_user WHERE id = 4",
    "SELECT * FROM journal_photo WHERE entry_id = 1",
    "SELECT * FROM auth_user WHERE id = 9",
    "SELECT * FROM journal_photo WHERE entry_id = 2",
    "SELECT * FROM auth_user WHERE id = 4",
    "SELECT * FROM journal_photo WHERE entry_id = 3",
]

_REL = {"author": "fk", "region": "fk", "photos": "many", "tags": "many"}

_GRAPH = {
    "accounts.0001_initial": [],
    "stories.0001_initial": ["accounts.0001_initial"],
    "stories.0002_reply": ["stories.0001_initial"],
    "accounts.0002_member_bio": ["accounts.0001_initial"],
    "stories.0003_story_editor": ["stories.0002_reply", "accounts.0002_member_bio"],
}

PROBLEMS = [
dict(
    id="django-n-plus-one",
    title="Spot the N+1 pattern in a query log",
    difficulty="Medium",
    pattern="Performance",
    entry="detect_n_plus_one",
    description=r"""
The N+1 problem shows up in a query log as one statement followed by the **same statement shape repeated many
times** with a different id. Write the detector that tools such as the debug toolbar's "similar queries" use.

`detect_n_plus_one(log, threshold)`:

1. **Normalise** each SQL string: strip surrounding whitespace and one trailing `;` if present; replace every
   single-quoted string literal (`'...'`, no escaped quotes inside) with `?`; then replace every standalone run of
   digits (a number that is not part of a longer word such as `table2`) with `?`.
2. Count how often each normalised template occurs.
3. Report every template that occurs **at least `threshold` times**, in order of first appearance, as
   `[template, count, fix]` where `fix` is
   - `"select_related"` if the template ends with ` WHERE id = ?` (each row fetched its single related object
     by primary key: a forward foreign key),
   - `"prefetch_related"` if it ends with `_id = ?` (each row fetched its children by foreign-key column:
     a reverse or many-to-many relation),
   - `"review"` otherwise.

Return the list of reports (empty when the log is clean).

**Example:** three `SELECT * FROM auth_user WHERE id = <n>` lines with `threshold=3` →
`[["SELECT * FROM auth_user WHERE id = ?", 3, "select_related"]]`.
""",
    starter='''def detect_n_plus_one(log: list, threshold: int) -> list:
    pass
''',
    solution=r'''import re


def _normalise(sql):
    sql = sql.strip()
    if sql.endswith(";"):
        sql = sql[:-1].rstrip()
    sql = re.sub(r"'[^']*'", "?", sql)
    return re.sub(r"\b\d+\b", "?", sql)


def detect_n_plus_one(log, threshold):
    counts = {}
    for sql in log:
        template = _normalise(sql)
        counts[template] = counts.get(template, 0) + 1
    report = []
    for template, count in counts.items():
        if count < threshold:
            continue
        if template.endswith(" WHERE id = ?"):
            fix = "select_related"
        elif template.endswith("_id = ?"):
            fix = "prefetch_related"
        else:
            fix = "review"
        report.append([template, count, fix])
    return report
''',
    tests=[
        [_LOG, 3],
        [_LOG, 2],
        [_LOG, 4],
        [[], 2],
        [["SELECT * FROM auth_user WHERE id = 1;", "  SELECT * FROM auth_user WHERE id = 22  ", "SELECT * FROM auth_user WHERE id = 333 ;"], 3],
        [["SELECT * FROM shop WHERE name = 'north'", "SELECT * FROM shop WHERE name = 'south 2'", "SELECT * FROM shop WHERE name = 'e'"], 3],
        [["SELECT * FROM table2 WHERE id = 5", "SELECT * FROM table2 WHERE id = 6", "SELECT * FROM table3 WHERE id = 6"], 2],
        [["SELECT COUNT(*) FROM story"] * 5, 5],
        [["SELECT * FROM reply WHERE story_id = %d AND hidden = 0" % i for i in range(40)], 10],
        [["SELECT * FROM a WHERE id = 1", "SELECT * FROM b WHERE a_id = 1", "SELECT * FROM a WHERE id = 2", "SELECT * FROM b WHERE a_id = 2"], 2],
        [["UPDATE story SET views = views + 1 WHERE id = 7", "UPDATE story SET views = views + 1 WHERE id = 8"], 2],
        [["SELECT * FROM tag WHERE story_id = 1", "SELECT * FROM tag WHERE story_id = 1"], 1],
        [["SELECT * FROM x WHERE code = 'id = 5'", "SELECT * FROM x WHERE code = 'zz'"], 2],
    ],
    examples=2,
    wrong_solutions=[
        '''def detect_n_plus_one(log, threshold):
    counts = {}
    for sql in log:
        counts[sql] = counts.get(sql, 0) + 1
    out = []
    for t, c in counts.items():
        if c >= threshold:
            out.append([t, c, "select_related" if t.endswith(" WHERE id = ?") else "prefetch_related" if t.endswith("_id = ?") else "review"])
    return out
''',
        r'''import re
def detect_n_plus_one(log, threshold):
    counts = {}
    for sql in log:
        t = re.sub(r"\d+", "?", sql.strip().rstrip(";").rstrip())
        counts[t] = counts.get(t, 0) + 1
    out = []
    for t, c in counts.items():
        if c > threshold:
            out.append([t, c, "prefetch_related" if t.endswith("id = ?") else "review"])
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Aggregation, joins and the N+1 problem*; `re.sub`; counting with a dict.",
        intuition="Two queries are 'the same query' when they differ only in their parameters. Erase the parameters and "
                  "identical shapes collapse into one template; a template seen many times in one request is the "
                  "fingerprint of a loop that talks to the database on every iteration.",
        hints=[
            "Normalise strings before numbers, otherwise digits inside a quoted literal are replaced twice.",
            "`\\b\\d+\\b` matches a number only when it is not glued to letters or underscores.",
            "A dict preserves insertion order, so iterating it gives first-appearance order.",
        ],
        brute_force="Compare every pair of queries with a similarity function: O(n²) and fuzzy. Normalising gives an exact key and one O(n) pass.",
        approach="""1. Normalise each line (strip, drop `;`, literals → `?`, numbers → `?`).
2. Count templates in a dict.
3. Emit those at or above the threshold with the fix chosen from the template's ending.

**Dry run** on the sample log with threshold 3: templates are the entry list (1), `auth_user WHERE id = ?` (3) and
`journal_photo WHERE entry_id = ?` (3) → two reports: `select_related` for the author lookup, `prefetch_related` for the photos.""",
        complexity="O(total characters) time, O(distinct templates) space.",
        pitfalls="""- Counting raw strings: every id is different, so nothing repeats.
- Using `>` instead of `>=` for the threshold.
- Replacing digits inside identifiers (`table2`).
- Reporting in sorted order instead of first appearance.""",
        follow_up="Real ORMs log parameterised SQL (`%s`) separately from params; adapt the detector to that format and add the calling stack frame.",
    ),
),
dict(
    id="django-related-query-count",
    title="select_related vs prefetch_related: count the queries",
    difficulty="Medium",
    pattern="Performance",
    entry="count_queries",
    description=r"""
A view loads `n` rows of a model and, inside a loop, touches some of each row's relations. How many SQL queries
does the request cost?

`count_queries(n, relations, accessed, select_related, prefetch_related)`:

- `n`: number of rows returned by the main queryset (0 or more).
- `relations`: dict mapping each relation name to its kind: `"fk"` (forward foreign key or one-to-one: one
  related object per row) or `"many"` (reverse foreign key or many-to-many: a set of related objects per row).
- `accessed`: list of relation names the loop touches on **every** row (duplicates mean the same relation is
  used several times; Django caches it on the instance, so it only costs once per row).
- `select_related`, `prefetch_related`: the names passed to those queryset methods.

Rules:

1. If any name in `select_related` or `prefetch_related` is not in `relations`, or `select_related` names a
   `"many"` relation, the query is invalid: return `-1` (Django raises an error).
2. The main query costs **1**, even when it returns no rows.
3. Each relation that is listed in `prefetch_related` costs **1** extra query if `n > 0`, otherwise 0
   (whether or not the loop uses it).
4. Otherwise a relation listed in `select_related` costs **0** (it rides along as a JOIN).
5. Otherwise a relation that is accessed costs **n** queries (one lazy load per row; assume every row points
   to a different related object).
6. Relations that are neither optimised nor accessed cost nothing.

Return the total.

**Example:** `n=50`, loop uses `author` (fk) and `photos` (many): no optimisation → `1 + 50 + 50 = 101`;
with `select_related=["author"]`, `prefetch_related=["photos"]` → `1 + 0 + 1 = 2`.
""",
    starter='''def count_queries(n: int, relations: dict, accessed: list, select_related: list, prefetch_related: list) -> int:
    pass
''',
    solution='''def count_queries(n, relations, accessed, select_related, prefetch_related):
    for name in list(select_related) + list(prefetch_related):
        if name not in relations:
            return -1
    for name in select_related:
        if relations[name] == "many":
            return -1
    total = 1
    for name in relations:
        if name in prefetch_related:
            total += 1 if n > 0 else 0
        elif name in select_related:
            total += 0
        elif name in accessed:
            total += n
    return total
''',
    tests=[
        [50, _REL, ["author", "photos"], [], []],
        [50, _REL, ["author", "photos"], ["author"], ["photos"]],
        [0, _REL, ["author", "photos"], [], []],
        [0, _REL, ["author"], ["author"], ["photos", "tags"]],
        [10, _REL, [], [], []],
        [10, _REL, ["author", "author", "author"], [], []],
        [10, _REL, ["author"], ["photos"], []],
        [10, _REL, ["author"], ["editor"], []],
        [10, _REL, ["author"], [], ["editor"]],
        [10, _REL, ["author", "region", "photos", "tags"], ["author", "region"], ["photos", "tags"]],
        [10, _REL, ["author", "region", "photos", "tags"], ["author"], ["photos"]],
        [10, _REL, ["author"], [], ["author"]],
        [10, _REL, [], ["author", "region"], ["tags"]],
        [1, _REL, ["tags"], [], []],
        [1000, _REL, ["photos", "tags", "region"], ["author"], []],
        [7, _REL, ["author"], ["author"], ["author"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def count_queries(n, relations, accessed, select_related, prefetch_related):
    total = 1
    for name in set(accessed):
        if name in select_related:
            continue
        total += 1 if name in prefetch_related else n
    return total
''',
        '''def count_queries(n, relations, accessed, select_related, prefetch_related):
    for name in list(select_related) + list(prefetch_related):
        if name not in relations:
            return -1
    for name in select_related:
        if relations[name] == "many":
            return -1
    total = 1
    for name in accessed:
        if name in select_related:
            continue
        total += 1 if name in prefetch_related else n
    return total + len([p for p in prefetch_related if p not in accessed])
''',
    ],
    guide=dict(
        prereqs="Lesson *Aggregation, joins and the N+1 problem*.",
        intuition="There are only three price tags. A lazy relation is paid per row (`n`). `select_related` folds a "
                  "single-valued relation into the main query (0). `prefetch_related` pays one flat query per relation "
                  "and stitches the results together in Python (1). Classify each relation and add up.",
        hints=[
            "Validate first: unknown names and `select_related` on a many-valued relation are errors.",
            "Loop over the relations, not over `accessed`, so duplicates and unused prefetches are handled naturally.",
            "A prefetch on an empty result set issues no query; the main query always runs.",
        ],
        brute_force="Simulate the loop row by row, incrementing a counter on each cache miss. Same answer in O(n · relations) instead of O(relations).",
        approach="""1. Return `-1` for invalid optimisation lists.
2. Start at 1. For each relation: prefetch → `+1` if `n > 0`; else select → `+0`; else accessed → `+n`.

**Dry run** `n=10`, accessed all four, `select_related=["author"]`, `prefetch_related=["photos"]`:
`1 + 0 (author) + 10 (region, lazy) + 1 (photos) + 10 (tags, lazy) = 22`.""",
        complexity="O(R) for R relations (with list membership tests; use sets for large inputs).",
        pitfalls="""- Counting a relation once per mention in `accessed` instead of once per row.
- Forgetting that an unused `prefetch_related` still costs a query.
- Charging the prefetch query when the page is empty.
- `select_related` cannot follow many-valued relations because a JOIN would multiply the rows.""",
        follow_up="Extend to nested paths such as `author__country` and `photos__tags`, where prefetch costs one query per level.",
    ),
),
dict(
    id="django-migration-order",
    title="Order migrations by their dependencies",
    difficulty="Medium",
    pattern="Migrations",
    entry="plan",
    description=r"""
Every migration file lists the migrations that must run before it (`dependencies = [...]`). `migrate` loads all
of them into a graph and produces an order in which each migration comes after everything it depends on.

`plan(graph)`:

- `graph` maps a migration id such as `"stories.0002_reply"` to the list of ids it depends on.
- Return a list containing every id exactly once such that each id appears **after all of its dependencies**.
  To make the answer unique, whenever several migrations are ready to run, pick the **lexicographically
  smallest** id first.
- Return `None` if a dependency names an id that is not a key of `graph` (Django: `NodeNotFoundError`) or if
  the dependencies contain a cycle (Django: `CircularDependencyError`).

**Example:** `{"b.0001": ["a.0001"], "a.0001": [], "a.0002": ["a.0001"]}` → `["a.0001", "a.0002", "b.0001"]`.
""",
    starter='''def plan(graph: dict):
    pass
''',
    solution='''import heapq


def plan(graph):
    indegree = {node: 0 for node in graph}
    dependants = {node: [] for node in graph}
    for node, deps in graph.items():
        for dep in set(deps):
            if dep not in graph:
                return None
            indegree[node] += 1
            dependants[dep].append(node)
    ready = [node for node, d in indegree.items() if d == 0]
    heapq.heapify(ready)
    order = []
    while ready:
        node = heapq.heappop(ready)
        order.append(node)
        for nxt in dependants[node]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                heapq.heappush(ready, nxt)
    return order if len(order) == len(graph) else None
''',
    tests=[
        [{"b.0001": ["a.0001"], "a.0001": [], "a.0002": ["a.0001"]}],
        [_GRAPH],
        [{}],
        [{"only.0001": []}],
        [{"a.0001": ["b.0001"], "b.0001": ["a.0001"]}],
        [{"a.0001": ["a.0001"]}],
        [{"a.0001": [], "a.0002": ["a.0001", "ghost.0001"]}],
        [{"z.0001": [], "a.0001": ["z.0001"], "m.0001": []}],
        [{"c": ["a", "b"], "b": ["a"], "a": [], "d": ["c"], "e": []}],
        [{"a": [], "b": ["a", "a"], "c": ["b"]}],
        [{"a": [], "b": ["a"], "c": ["b"], "d": ["c"], "b2": ["d", "a"], "x": ["y"], "y": ["z"], "z": ["x"]}],
        [{"n%03d" % i: (["n%03d" % (i - 1)] if i else []) for i in range(300)}],
        [{"k%02d" % i: [] for i in range(20, 0, -1)}],
        [{"app.0002": ["app.0001"], "app.0003": ["app.0002"], "app.0001": [], "other.0001": ["app.0003"], "app.0004": ["other.0001"]}],
    ],
    examples=2,
    wrong_solutions=[
        '''def plan(graph):
    return sorted(graph)
''',
        '''def plan(graph):
    order, seen = [], set()
    def visit(node):
        if node in seen:
            return
        seen.add(node)
        for dep in sorted(graph.get(node, [])):
            visit(dep)
        order.append(node)
    for node in sorted(graph):
        visit(node)
    return order
''',
    ],
    guide=dict(
        prereqs="Lesson *Transactions, indexes, migrations in teams and raw SQL*; graphs, queues/heaps.",
        intuition="'Run each thing after its prerequisites' is a topological sort. Kahn's algorithm keeps a pool of nodes "
                  "whose prerequisites are all done; taking the smallest from the pool each time (a min-heap) makes the "
                  "order deterministic. If the pool empties while nodes remain, those nodes are waiting for each other: a cycle.",
        hints=[
            "Count, for every node, how many distinct dependencies it still waits for (its in-degree).",
            "Use `heapq` for the ready pool so you always pop the smallest id.",
            "If the output is shorter than the graph, there was a cycle.",
        ],
        brute_force="Repeatedly scan all nodes for one whose dependencies are already placed: O(V · (V + E)). The heap version does each edge once.",
        approach="""1. Build `indegree` and a reverse map `dependants`; reject unknown dependencies.
2. Heapify the nodes with in-degree 0.
3. Pop the smallest, append it, decrement its dependants, push those that reach 0.
4. Return the order if it contains every node, else `None`.

**Dry run** on the example: in-degrees a.0001=0, a.0002=1, b.0001=1. Pop a.0001 → both others ready → pop
a.0002, then b.0001.""",
        complexity="O((V + E) log V) time, O(V + E) space.",
        pitfalls="""- Plain alphabetical sort ignores cross-app dependencies (`app.0004` after `other.0001`).
- DFS without a 'visiting' state does not detect cycles and its tie-breaking differs.
- Duplicate dependencies must not be counted twice.
- An empty graph is valid and returns `[]`, which must be distinguishable from the error value `None`.""",
        follow_up="Add `run_before` (reverse edges declared by the earlier migration) and `replaces` (squashed migrations standing in for a set).",
    ),
),
dict(
    id="django-migration-squash",
    title="Optimise a list of migration operations",
    difficulty="Hard",
    pattern="Migrations",
    entry="squash",
    description=r"""
`squashmigrations` feeds all operations through an optimiser that merges and cancels them. Implement this
defined subset. Operations are lists:

| operation | meaning |
|---|---|
| `["CreateModel", model, fields]` | `fields` is a dict `name -> type` |
| `["DeleteModel", model]` | |
| `["AddField", model, field, type]` | |
| `["RemoveField", model, field]` | |
| `["AlterField", model, field, type]` | change the field's type |
| `["RenameField", model, old, new]` | |

`squash(ops)` processes the operations left to right while building an output list `out`. For an operation on
model `M`:

**Case A: `out` contains a `CreateModel` for `M`** (the model is created in this list). Fold the operation into it:
`AddField` and `AlterField` set `fields[field] = type`; `RemoveField` deletes the key; `RenameField` renames the
key (keeping its type); `DeleteModel` removes that `CreateModel` from `out` entirely. Nothing is appended.

**Case B: otherwise** (the model existed before):

- `CreateModel` → append it (with a copy of its fields).
- `AddField` → append it.
- `AlterField(M, f, t)` → if `out` has an `AddField` or `AlterField` for `(M, f)`, replace its type with `t`;
  otherwise append.
- `RemoveField(M, f)` → if `out` has an `AddField` for `(M, f)`, delete that `AddField` and append nothing.
  Otherwise delete any `AlterField` for `(M, f)` from `out` and append the `RemoveField`.
- `RenameField(M, old, new)` → if `out` has an `AddField` for `(M, old)`, rename the field inside it;
  otherwise append.
- `DeleteModel(M)` → delete every operation on `M` from `out`, then append the `DeleteModel`.

For each `(M, f)` there is at most one `AddField`/`AlterField` entry in `out` at any time when these rules are
followed. Do not mutate the input. Return `out`.

**Example:** `[["CreateModel", "Story", {"title": "char"}], ["AddField", "Story", "body", "text"], ["RenameField", "Story", "title", "headline"]]`
→ `[["CreateModel", "Story", {"headline": "char", "body": "text"}]]`.
""",
    starter='''def squash(ops: list) -> list:
    pass
''',
    solution='''def _find(out, kinds, model, field=None):
    for i, op in enumerate(out):
        if op[0] in kinds and op[1] == model and (field is None or op[2] == field):
            return i
    return -1


def squash(ops):
    out = []
    for op in ops:
        kind, model = op[0], op[1]
        created = _find(out, ("CreateModel",), model)
        if created >= 0:
            fields = out[created][2]
            if kind in ("AddField", "AlterField"):
                fields[op[2]] = op[3]
            elif kind == "RemoveField":
                fields.pop(op[2], None)
            elif kind == "RenameField":
                out[created][2] = {(op[3] if k == op[2] else k): v for k, v in fields.items()}
            elif kind == "DeleteModel":
                del out[created]
            continue
        if kind == "CreateModel":
            out.append(["CreateModel", model, dict(op[2])])
        elif kind == "AddField":
            out.append(list(op))
        elif kind == "AlterField":
            i = _find(out, ("AddField", "AlterField"), model, op[2])
            if i >= 0:
                out[i][3] = op[3]
            else:
                out.append(list(op))
        elif kind == "RemoveField":
            i = _find(out, ("AddField",), model, op[2])
            if i >= 0:
                del out[i]
            else:
                out = [o for o in out if not (o[0] == "AlterField" and o[1] == model and o[2] == op[2])]
                out.append(list(op))
        elif kind == "RenameField":
            i = _find(out, ("AddField",), model, op[2])
            if i >= 0:
                out[i][2] = op[3]
            else:
                out.append(list(op))
        elif kind == "DeleteModel":
            out = [o for o in out if o[1] != model]
            out.append(list(op))
    return out
''',
    tests=[
        [[["CreateModel", "Story", {"title": "char"}], ["AddField", "Story", "body", "text"], ["RenameField", "Story", "title", "headline"]]],
        [[["AddField", "Story", "views", "int"], ["RemoveField", "Story", "views"]]],
        [[]],
        [[["CreateModel", "Reply", {"text": "char"}], ["AlterField", "Reply", "text", "text"], ["DeleteModel", "Reply"]]],
        [[["AddField", "Story", "views", "int"], ["AlterField", "Story", "views", "bigint"], ["AlterField", "Story", "views", "float"]]],
        [[["AlterField", "Story", "title", "text"], ["AlterField", "Story", "title", "char"], ["RemoveField", "Story", "title"]]],
        [[["AddField", "Story", "lead", "char"], ["RenameField", "Story", "lead", "intro"], ["AlterField", "Story", "intro", "text"]]],
        [[["RenameField", "Story", "a", "b"], ["RemoveField", "Story", "b"]]],
        [[["AddField", "Story", "x", "int"], ["AlterField", "Story", "y", "int"], ["RenameField", "Story", "q", "r"], ["DeleteModel", "Story"], ["AddField", "Reply", "z", "int"]]],
        [[["CreateModel", "A", {}], ["CreateModel", "B", {"a": "fk"}], ["AddField", "A", "n", "int"], ["RemoveField", "B", "a"], ["AddField", "B", "m", "int"], ["RemoveField", "A", "n"]]],
        [[["CreateModel", "A", {"x": "int"}], ["DeleteModel", "A"], ["CreateModel", "A", {"y": "int"}], ["AddField", "A", "z", "int"]]],
        [[["AddField", "A", "f", "int"], ["AddField", "B", "f", "int"], ["RemoveField", "A", "f"], ["AlterField", "B", "f", "char"]]],
        [[["DeleteModel", "Old"], ["AddField", "Story", "k", "int"]]],
        [[["CreateModel", "S", {"a": "int", "b": "int"}], ["RenameField", "S", "a", "c"], ["RemoveField", "S", "b"], ["AlterField", "S", "c", "char"], ["AddField", "S", "b", "bool"]]],
        [[["AddField", "S", "a", "int"], ["RemoveField", "S", "a"], ["AddField", "S", "a", "char"], ["AlterField", "S", "a", "text"]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def squash(ops):
    return [list(o) for o in ops]
''',
        '''def squash(ops):
    out = []
    for op in ops:
        kind, model = op[0], op[1]
        if kind == "RemoveField":
            hit = [o for o in out if o[0] == "AddField" and o[1] == model and o[2] == op[2]]
            if hit:
                out.remove(hit[0])
                continue
        if kind == "DeleteModel":
            had = any(o[0] == "CreateModel" and o[1] == model for o in out)
            out = [o for o in out if o[1] != model]
            if had:
                continue
        out.append(list(op))
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Transactions, indexes, migrations in teams and raw SQL* (squashing); list and dict manipulation.",
        intuition="Think of the output as a to-do list for a fresh database. If the list already creates a model, any later "
                  "tweak to that model can be baked into the creation. If a field is added and later removed, the fresh "
                  "database never needs it. Each incoming operation either edits an earlier entry or is appended.",
        hints=[
            "Write a helper that finds the index of an entry in `out` by kind, model and optionally field.",
            "Check 'is there a CreateModel for this model in out?' first; that single case absorbs five operation kinds.",
            "Copy the fields dict of `CreateModel` and the lists you append, so the caller's data stays intact.",
        ],
        brute_force="Replay the operations into a full schema state and diff the final state with the initial one. That is "
                    "what `makemigrations` does when you delete and regenerate migrations, but it needs the starting schema, which this function is not given.",
        approach="""1. For each op, look for a `CreateModel` of its model in `out` (Case A) and fold the op into the fields dict.
2. Otherwise apply the Case B rule for its kind, editing or deleting earlier entries as specified.

**Dry run** `Add(S.a,int)`, `Remove(S.a)`, `Add(S.a,char)`, `Alter(S.a,text)`: append Add; Remove finds the Add and
deletes it (out is empty); append Add char; Alter finds the Add and rewrites its type → `[["AddField","S","a","text"]]`.""",
        complexity="O(n²) in the worst case because each operation may scan `out`; index `out` by `(model, field)` for O(n).",
        pitfalls="""- Emitting `DeleteModel` for a model that was created inside the same list.
- Keeping an `AlterField` in front of a `RemoveField` of the same field.
- Renaming must keep the field's type and, inside `CreateModel`, its position.
- A model can be created, deleted and created again in one list; each operation must look at the *current* `out`.""",
        follow_up="Django's real optimiser also has to respect cross-model references (a foreign key to a model created later blocks reordering). Read `django/db/migrations/optimizer.py`.",
    ),
),
]
