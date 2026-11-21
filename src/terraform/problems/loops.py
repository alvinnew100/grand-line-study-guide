PROBLEMS = [
dict(
    id="tf-count-plan",
    title="Plan a count resource after its list changes",
    difficulty="Easy",
    pattern="Loops & Addresses",
    entry="countPlan",
    description=r"""
A resource written with `count` is a numbered row of copies: `aws_iam_user.staff[0]`, `aws_iam_user.staff[1]`
and so on. Terraform identifies each copy **by its position**, not by what it contains. Write
`countPlan(resource, old_values, new_values, force_new)` to show what that does to a plan.

- `resource` is the address without an index, for example `"aws_iam_user.staff"`.
- `old_values[i]` is the value copy `i` was created with (what state remembers).
- `new_values[i]` is the value the configuration now gives copy `i`.
- `force_new` is `True` when the value cannot be changed in place (a user's name, for instance).

For every index from `0` up to the longer list's last index, decide one action:

| Situation at index `i` | Action |
|---|---|
| Only in `new_values` | `"create"` |
| Only in `old_values` | `"delete"` |
| In both, values equal | `"no-op"` |
| In both, values differ, `force_new` is true | `"replace"` |
| In both, values differ, `force_new` is false | `"update"` |

Return a list of `[address, action]` pairs in index order, where the address is `resource[i]`.

**Example:** `countPlan("aws_iam_user.staff", ["asha", "ben", "chidi"], ["asha", "chidi"], True)` →
`[["aws_iam_user.staff[0]", "no-op"], ["aws_iam_user.staff[1]", "replace"], ["aws_iam_user.staff[2]", "delete"]]`

Ben was removed from the middle, yet the plan replaces index 1 (Ben becomes Chidi) and deletes index 2
(the original Chidi). That is the index-shifting trap.
""",
    starter='''def countPlan(resource, old_values, new_values, force_new):
    pass
''',
    solution='''def countPlan(resource, old_values, new_values, force_new):
    plan = []
    for i in range(max(len(old_values), len(new_values))):
        if i >= len(old_values):
            action = "create"
        elif i >= len(new_values):
            action = "delete"
        elif old_values[i] == new_values[i]:
            action = "no-op"
        elif force_new:
            action = "replace"
        else:
            action = "update"
        plan.append([f"{resource}[{i}]", action])
    return plan
''',
    tests=[
        ["aws_iam_user.staff", ["asha", "ben", "chidi"], ["asha", "chidi"], True],
        ["aws_iam_user.staff", ["asha", "ben", "chidi"], ["asha", "ben"], True],
        ["aws_iam_user.staff", [], [], True],
        ["aws_iam_user.staff", [], ["asha", "ben"], True],
        ["aws_iam_user.staff", ["asha", "ben"], [], False],
        ["aws_iam_user.staff", ["asha", "ben", "chidi"], ["ben", "chidi"], True],
        ["aws_instance.web", ["t3.micro", "t3.micro"], ["t3.small", "t3.micro", "t3.micro"], False],
        ["aws_iam_user.staff", ["asha", "ben"], ["asha", "ben"], True],
        ["aws_iam_user.staff", ["asha", "ben"], ["zed", "asha", "ben"], True],
        ["module.team.aws_iam_user.staff", ["a", "b", "c", "d", "e"], ["e", "d", "c", "b", "a"], True],
        ["aws_subnet.private", ["10.0.1.0/24", "10.0.2.0/24"], ["10.0.2.0/24", "10.0.1.0/24"], False],
        ["aws_iam_user.staff", [f"user{i}" for i in range(50)], [f"user{i}" for i in range(50) if i != 10], True],
        ["aws_iam_user.staff", ["asha", "asha"], ["asha"], True],
    ],
    examples=2,
    wrong_solutions=[
        '''def countPlan(resource, old_values, new_values, force_new):
    plan = []
    i = 0
    for v in old_values:
        plan.append([f"{resource}[{i}]", "no-op" if v in new_values else "delete"])
        i += 1
    for v in new_values:
        if v not in old_values:
            plan.append([f"{resource}[{i}]", "create"])
            i += 1
    return plan
''',
        '''def countPlan(resource, old_values, new_values, force_new):
    plan = []
    for i in range(max(len(old_values), len(new_values))):
        if i >= len(old_values):
            action = "create"
        elif i >= len(new_values):
            action = "delete"
        elif old_values[i] == new_values[i]:
            action = "no-op"
        else:
            action = "update"
        plan.append([f"{resource}[{i}]", action])
    return plan
''',
    ],
    guide=dict(
        prereqs="The lesson *Loops: count, for_each and the index-shifting trap*. Python lists and `range`.",
        intuition="With `count`, the address *is* the position. Terraform never asks 'where did Ben go?'. It asks 'what is at index 1 now, and what was there before?'. So compare the two lists slot by slot, like two columns of a spreadsheet, and ignore the fact that the same value may appear in a different row.",
        hints=[
            "Loop over indices, not over values. How many indices are there in total?",
            "An index past the end of the old list is new; an index past the end of the new list is going away.",
            "For an index in both lists, compare the two values at that index only. `force_new` chooses between replace and update.",
        ],
        brute_force="There is no slower natural approach: one pass over the indices is already the direct translation of the rule. The tempting *wrong* approach is a set difference between the two lists, which describes `for_each`, not `count`.",
        approach="""1. `n = max(len(old_values), len(new_values))`.
2. For each `i` in `range(n)`: past the old list → `create`; past the new list → `delete`; equal → `no-op`; otherwise `replace` or `update` depending on `force_new`.
3. Build the address with an f-string: `f"{resource}[{i}]"`.

**Dry run:** old `["asha", "ben", "chidi"]`, new `["asha", "chidi"]`, `force_new = True`.

| i | old | new | action |
|---|---|---|---|
| 0 | asha | asha | no-op |
| 1 | ben | chidi | replace |
| 2 | chidi | (none) | delete |

One person was removed, but the plan destroys two users and creates one. In the summary line that reads `1 to add, 0 to change, 2 to destroy`.""",
        complexity="Time O(n) for n = the longer list; space O(n) for the result.",
        pitfalls="Matching by value instead of by position (first wrong solution): that reports a tidy single delete, which is exactly what Terraform does *not* do. Ignoring `force_new` and always reporting `update`. Stopping at the shorter list's length and losing the creates or deletes at the tail.",
        follow_up="Removing the *last* element is the one harmless removal. Explain why, then solve *Plan a for_each resource after its keys change* and compare the two plans for the same removal.",
    ),
),
dict(
    id="tf-foreach-plan",
    title="Plan a for_each resource after its keys change",
    difficulty="Easy",
    pattern="Loops & Addresses",
    entry="forEachPlan",
    description=r"""
A resource written with `for_each` has one copy per **key**: `aws_iam_user.staff["asha"]`,
`aws_iam_user.staff["ben"]`. The key is the identity, so removing one key touches only that copy.
Write `forEachPlan(resource, old, new, force_new)`.

`old` (what state holds) and `new` (what the configuration now says) are each **either**

- a dict, standing for a map: each key maps to the value that copy is built from; **or**
- a list of strings, standing for `toset([...])`: every distinct string is a key whose value is the
  string itself. Duplicates collapse into one key, and order means nothing.

For every key in either collection decide one action:

| Situation | Action |
|---|---|
| Key only in `new` | `"create"` |
| Key only in `old` | `"delete"` |
| In both, values equal | `"no-op"` |
| In both, values differ, `force_new` true | `"replace"` |
| In both, values differ, `force_new` false | `"update"` |

Return `[address, action]` pairs sorted by key, where the address is `resource["key"]` with the key in
double quotes.

**Example:** `forEachPlan("aws_iam_user.staff", ["asha", "ben", "chidi"], ["asha", "chidi"], True)` →
`[['aws_iam_user.staff["asha"]', "no-op"], ['aws_iam_user.staff["ben"]', "delete"], ['aws_iam_user.staff["chidi"]', "no-op"]]`
""",
    starter='''def forEachPlan(resource, old, new, force_new):
    pass
''',
    solution='''def forEachPlan(resource, old, new, force_new):
    def as_map(collection):
        if isinstance(collection, dict):
            return dict(collection)
        return {item: item for item in collection}

    before, after = as_map(old), as_map(new)
    plan = []
    for key in sorted(set(before) | set(after)):
        if key not in before:
            action = "create"
        elif key not in after:
            action = "delete"
        elif before[key] == after[key]:
            action = "no-op"
        elif force_new:
            action = "replace"
        else:
            action = "update"
        plan.append([f'{resource}["{key}"]', action])
    return plan
''',
    tests=[
        ["aws_iam_user.staff", ["asha", "ben", "chidi"], ["asha", "chidi"], True],
        ["aws_instance.web", {"api": "t3.micro", "web": "t3.micro"}, {"api": "t3.small", "web": "t3.micro"}, False],
        ["aws_iam_user.staff", [], [], True],
        ["aws_iam_user.staff", [], ["ben", "asha"], True],
        ["aws_iam_user.staff", ["ben", "asha"], [], True],
        ["aws_iam_user.staff", ["chidi", "asha", "ben"], ["ben", "chidi", "asha"], True],
        ["aws_iam_user.staff", ["asha", "asha", "ben"], ["ben", "ben"], True],
        ["aws_instance.web", {"api": "t3.micro"}, {"api": "t3.small"}, True],
        ["aws_s3_bucket.site", {"docs": "private", "blog": "private"}, {"blog": "private", "shop": "private"}, False],
        ["aws_iam_user.staff", ["asha", "ben"], {"asha": "asha", "ben": "benjamin"}, True],
        ["module.net.aws_subnet.this", {"app-a": "10.0.1.0/24", "app-b": "10.0.2.0/24"},
         {"app-b": "10.0.1.0/24", "app-a": "10.0.2.0/24"}, True],
        ["aws_iam_user.staff", [f"user{i:02d}" for i in range(50)], [f"user{i:02d}" for i in range(50) if i != 10], True],
        ["aws_iam_user.staff", ["zed", "amy"], ["amy", "bob", "zed"], False],
    ],
    examples=2,
    wrong_solutions=[
        '''def forEachPlan(resource, old, new, force_new):
    old = sorted(old); new = sorted(new)
    plan = []
    for i in range(max(len(old), len(new))):
        if i >= len(old):
            plan.append([f'{resource}["{new[i]}"]', "create"])
        elif i >= len(new):
            plan.append([f'{resource}["{old[i]}"]', "delete"])
        elif old[i] == new[i]:
            plan.append([f'{resource}["{old[i]}"]', "no-op"])
        else:
            plan.append([f'{resource}["{old[i]}"]', "replace" if force_new else "update"])
    return plan
''',
        '''def forEachPlan(resource, old, new, force_new):
    plan = []
    for key in sorted(set(old) | set(new)):
        if key not in old:
            action = "create"
        elif key not in new:
            action = "delete"
        else:
            action = "no-op"
        plan.append([f'{resource}["{key}"]', action])
    return plan
''',
    ],
    guide=dict(
        prereqs="The lesson *Loops: count, for_each and the index-shifting trap*, and the problem *Plan a count resource after its list changes*. Python dicts and sets.",
        intuition="With `for_each` the address carries a name tag instead of a seat number. Names do not shift when someone leaves the row. So the plan is a comparison of two dictionaries by key: which keys appeared, which vanished, and which kept their key but changed their value.",
        hints=[
            "Turn both inputs into dicts first. A list of strings becomes `{s: s for s in items}`, which also removes duplicates.",
            "Walk the sorted union of the two key sets.",
            "Only a key present on both sides can be a no-op, an update or a replacement. Compare the two values for that key.",
        ],
        brute_force="For each key in `new`, scan `old` linearly to find a match, and the reverse for deletions: O(n·m). Dict lookups make each check O(1).",
        approach="""1. Normalise: dict stays a dict; a list becomes a dict from each string to itself.
2. `keys = sorted(set(before) | set(after))`.
3. Decide per key with the table from the statement.
4. Address: `f'{resource}["{key}"]'`. Single quotes around the f-string let you write the double quotes directly.

**Dry run** with the same removal as the count problem: old `["asha", "ben", "chidi"]`, new `["asha", "chidi"]`.

| key | in old | in new | action |
|---|---|---|---|
| asha | yes | yes | no-op |
| ben | yes | no | delete |
| chidi | yes | yes | no-op |

One person removed, one resource destroyed. Compare with the count version of the same change: one replacement and one delete.""",
        complexity="Time O(k log k) for k distinct keys because of the sort; space O(k).",
        pitfalls="Comparing by sorted position (first wrong solution), which reintroduces the index-shifting behaviour of `count`. Forgetting that a map's value can change while its key stays (second wrong solution). Forgetting to collapse duplicates in a list. Writing the address with single quotes or no quotes around the key.",
        follow_up="Terraform rejects a plain list for `for_each` and asks for `toset(...)` or a map. Explain why a positional collection would defeat the purpose of `for_each`.",
    ),
),
dict(
    id="tf-for-expression",
    title="Evaluate a for expression",
    difficulty="Medium",
    pattern="Expressions",
    entry="evalFor",
    description=r"""
A `for` expression walks a collection and builds a new list or map, optionally filtering as it goes.
Write `evalFor(collection, spec)` that evaluates one.

**Iteration.** `collection` is a list or a dict.

- A list is visited in order; the *key* is the index (0, 1, 2, …) and the *value* is the element.
- A dict stands for a map and is visited **in sorted key order**, whatever order it was written in.

**The spec** is a dict:

| key | meaning |
|---|---|
| `"out"` | `"list"` for `[for ... : value]`, `"map"` for `{for ... : key => value}` |
| `"value"` | a pair `[func, field]` producing each result value |
| `"key"` | a pair `[func, field]` producing each result key (map output only) |
| `"if"` | optional `[field, op, operand]` filter; items failing it are skipped |
| `"group"` | optional bool, map output only: the `...` grouping mode |

`field` is `"key"` or `"value"`. `func` is one of `"id"` (unchanged), `"upper"`, `"lower"`, `"length"`
(number of characters). `op` is one of `"=="`, `"!="`, `">"`, `"<"`.

**Results.**

- List output: the produced values, in iteration order.
- Map output: a dict. Result keys are always strings, so convert a numeric key with `str`.
  If two items produce the same key and `group` is not true, stop and return the string
  `Error: Duplicate object key "<key>"` for the first repeated key met.
  With `group` true, each key maps to the list of its values in iteration order.

**Example 1:** `evalFor(["web", "api"], {"out": "list", "value": ["upper", "value"]})` → `["WEB", "API"]`

**Example 2:** `evalFor({"ben": "web", "asha": "web", "chidi": "data"}, {"out": "map", "key": ["id", "value"], "value": ["id", "key"], "group": True})`
→ `{"web": ["asha", "ben"], "data": ["chidi"]}`
""",
    starter='''def evalFor(collection, spec):
    pass
''',
    solution='''def evalFor(collection, spec):
    if isinstance(collection, dict):
        items = sorted(collection.items(), key=lambda kv: kv[0])
    else:
        items = list(enumerate(collection))

    def produce(pair, k, v):
        func, field = pair
        x = k if field == "key" else v
        if func == "upper":
            return x.upper()
        if func == "lower":
            return x.lower()
        if func == "length":
            return len(x)
        return x

    def keep(k, v):
        cond = spec.get("if")
        if not cond:
            return True
        field, op, operand = cond
        x = k if field == "key" else v
        if op == "==":
            return x == operand
        if op == "!=":
            return x != operand
        if op == ">":
            return x > operand
        return x < operand

    if spec["out"] == "list":
        return [produce(spec["value"], k, v) for k, v in items if keep(k, v)]

    grouping = bool(spec.get("group"))
    result = {}
    for k, v in items:
        if not keep(k, v):
            continue
        key = str(produce(spec["key"], k, v))
        value = produce(spec["value"], k, v)
        if grouping:
            result.setdefault(key, []).append(value)
        elif key in result:
            return f'Error: Duplicate object key "{key}"'
        else:
            result[key] = value
    return result
''',
    tests=[
        [["web", "api"], {"out": "list", "value": ["upper", "value"]}],
        [{"ben": "web", "asha": "web", "chidi": "data"},
         {"out": "map", "key": ["id", "value"], "value": ["id", "key"], "group": True}],
        [{"ben": "web", "asha": "web", "chidi": "data"}, {"out": "map", "key": ["id", "value"], "value": ["id", "key"]}],
        [[], {"out": "list", "value": ["id", "value"]}],
        [{}, {"out": "map", "key": ["id", "key"], "value": ["id", "value"]}],
        [{"zeta": 1, "alpha": 2, "mid": 3}, {"out": "list", "value": ["id", "key"]}],
        [{"zeta": 1, "alpha": 2, "mid": 3}, {"out": "list", "value": ["id", "value"], "if": ["value", ">", 1]}],
        [["web", "api", "worker"], {"out": "map", "key": ["id", "value"], "value": ["id", "key"]}],
        [["web", "api", "worker", "db"], {"out": "list", "value": ["id", "value"], "if": ["key", "!=", 1]}],
        [["web", "api", "worker", "db"], {"out": "map", "key": ["length", "value"], "value": ["id", "value"], "group": True}],
        [["web", "api", "worker", "db"], {"out": "map", "key": ["length", "value"], "value": ["id", "value"]}],
        [{"Asha": "WEB", "Ben": "Data"}, {"out": "map", "key": ["lower", "key"], "value": ["lower", "value"]}],
        [{"b": "x", "a": "x", "c": "y"},
         {"out": "map", "key": ["id", "value"], "value": ["upper", "key"], "if": ["key", "!=", "a"], "group": True}],
        [["a", "b", "a"], {"out": "map", "key": ["id", "value"], "value": ["id", "key"], "if": ["key", "<", 2]}],
        [{f"k{i:02d}": i % 3 for i in range(29, -1, -1)},
         {"out": "map", "key": ["id", "value"], "value": ["id", "key"], "group": True}],
    ],
    examples=2,
    wrong_solutions=[
        '''def evalFor(collection, spec):
    items = list(collection.items()) if isinstance(collection, dict) else list(enumerate(collection))
    def produce(pair, k, v):
        func, field = pair
        x = k if field == "key" else v
        return x.upper() if func == "upper" else x.lower() if func == "lower" else len(x) if func == "length" else x
    def keep(k, v):
        c = spec.get("if")
        if not c:
            return True
        x = k if c[0] == "key" else v
        return {"==": x == c[2], "!=": x != c[2]}.get(c[1]) if c[1] in ("==", "!=") else (x > c[2] if c[1] == ">" else x < c[2])
    if spec["out"] == "list":
        return [produce(spec["value"], k, v) for k, v in items if keep(k, v)]
    out = {}
    for k, v in items:
        if keep(k, v):
            key = str(produce(spec["key"], k, v)); val = produce(spec["value"], k, v)
            if spec.get("group"):
                out.setdefault(key, []).append(val)
            elif key in out:
                return f'Error: Duplicate object key "{key}"'
            else:
                out[key] = val
    return out
''',
        '''def evalFor(collection, spec):
    items = sorted(collection.items()) if isinstance(collection, dict) else list(enumerate(collection))
    def produce(pair, k, v):
        func, field = pair
        x = k if field == "key" else v
        return x.upper() if func == "upper" else x.lower() if func == "lower" else len(x) if func == "length" else x
    def keep(k, v):
        c = spec.get("if")
        if not c:
            return True
        x = k if c[0] == "key" else v
        return x == c[2] if c[1] == "==" else x != c[2] if c[1] == "!=" else x > c[2] if c[1] == ">" else x < c[2]
    if spec["out"] == "list":
        return [produce(spec["value"], k, v) for k, v in items if keep(k, v)]
    out = {}
    for k, v in items:
        if keep(k, v):
            key = str(produce(spec["key"], k, v)); val = produce(spec["value"], k, v)
            if spec.get("group"):
                out.setdefault(key, []).append(val)
            else:
                out[key] = val
    return out
''',
    ],
    guide=dict(
        prereqs="The lesson *For expressions, string directives and conditionals*. Python list and dict building, `sorted`, `dict.setdefault`.",
        intuition="Every `for` expression is the same three-step machine: visit items in a fixed order, drop the ones the `if` rejects, and emit something for each survivor. The brackets decide the container. Two details make it Terraform rather than Python: maps are visited in sorted key order, and a map result may not receive the same key twice unless you asked for grouping.",
        hints=[
            "First build one list of `(key, value)` pairs: `enumerate` for a list, sorted items for a dict. Everything after that is the same for both.",
            "Write two small helpers: one applies a `[func, field]` pair to an item, one tests the optional filter.",
            "For map output keep a result dict. Before inserting, check whether the key is already there; what you do next depends on `group`.",
        ],
        brute_force="Handle the four combinations (list or map input, list or map output) with four separate loops. It works and costs the same, but every rule is written four times and the sorted-order rule is easy to forget in one of them.",
        approach="""1. `items` = `enumerate(collection)` for a list, `sorted(collection.items())` for a dict.
2. `produce([func, field], k, v)` picks `k` or `v` and applies the function.
3. `keep(k, v)` evaluates the filter, or returns `True` when there is none.
4. List output: a comprehension over `items`.
5. Map output: for each kept item compute `key = str(...)` and `value`. Grouping → `setdefault(key, []).append(value)`. No grouping and key already present → return the error string. Otherwise store it.

**Dry run** for `{for person, team in {"ben": "web", "asha": "web", "chidi": "data"} : team => person...}`:

| visited (sorted) | key | result so far |
|---|---|---|
| asha → web | web | `{web: [asha]}` |
| ben → web | web | `{web: [asha, ben]}` |
| chidi → data | data | `{web: [asha, ben], data: [chidi]}` |

Without the `...`, the second row meets `web` again and the answer is `Error: Duplicate object key "web"`.""",
        complexity="Time O(n log n) for a dict input because of the sort, O(n) for a list. Space O(n) for the result.",
        pitfalls="Visiting a dict in the order it was written (first wrong solution): Terraform maps have no insertion order, so results would differ from the real tool. Letting a later item silently overwrite an earlier one with the same key (second wrong solution): Terraform refuses, because losing data without a word is worse than an error. Forgetting to convert a numeric key to a string. Applying the filter after checking for duplicates instead of before.",
        follow_up="Add a `\"set\"` input kind (a list to be treated as a set of strings: de-duplicated and visited in sorted order), which is how `for_each = toset(...)` iterates.",
    ),
),
dict(
    id="tf-moved-blocks",
    title="Apply moved blocks to state addresses",
    difficulty="Medium",
    pattern="Loops & Addresses",
    entry="applyMoves",
    description=r"""
A `moved` block tells Terraform that an object has a new address, so a rename is recorded in state
instead of being planned as "destroy the old one, create a new one". Write `applyMoves(addresses, moves)`.

- `addresses` is the list of resource instance addresses currently in state, such as
  `aws_instance.web`, `aws_instance.web[0]`, `aws_iam_user.staff["asha"]` or `module.net.aws_vpc.main`.
- `moves` is a list of `[from, to]` pairs, applied **one after another in the order given**.

**What one move does.** An address `A` is affected by `[from, to]` when

- `A` equals `from`, or
- `A` starts with `from` immediately followed by `[` (an instance of that resource or module), or
- `A` starts with `from` immediately followed by `.` (something inside that module).

An affected address has its leading `from` replaced by `to`; the rest of the address is kept.
A move that affects nothing is skipped without complaint.

**Collisions.** If a rewritten address is the same as an address that this move does not affect, stop and
return a one-element list `["Error: <address> already exists"]`, using the alphabetically smallest such address.

Return the final addresses sorted alphabetically.

**Example:** `applyMoves(["aws_instance.web[0]", "aws_instance.web[1]", "aws_vpc.main"], [["aws_instance.web", "aws_instance.app"]])`
→ `["aws_instance.app[0]", "aws_instance.app[1]", "aws_vpc.main"]`
""",
    starter='''def applyMoves(addresses, moves):
    pass
''',
    solution='''def applyMoves(addresses, moves):
    current = set(addresses)
    for src, dst in moves:
        rewritten = {}
        for addr in current:
            if addr == src or addr.startswith(src + "[") or addr.startswith(src + "."):
                rewritten[addr] = dst + addr[len(src):]
        staying = current - set(rewritten)
        clashes = sorted(new for new in rewritten.values() if new in staying)
        if clashes:
            return ["Error: " + clashes[0] + " already exists"]
        current = staying | set(rewritten.values())
    return sorted(current)
''',
    tests=[
        [["aws_instance.web[0]", "aws_instance.web[1]", "aws_vpc.main"], [["aws_instance.web", "aws_instance.app"]]],
        [["aws_iam_user.staff[0]", "aws_iam_user.staff[1]"],
         [["aws_iam_user.staff[0]", "aws_iam_user.staff[\"asha\"]"], ["aws_iam_user.staff[1]", "aws_iam_user.staff[\"ben\"]"]]],
        [[], [["aws_instance.a", "aws_instance.b"]]],
        [["aws_instance.a"], []],
        [["aws_instance.a"], [["aws_instance.zzz", "aws_instance.b"]]],
        [["aws_instance.a", "aws_instance.b"], [["aws_instance.a", "aws_instance.b"]]],
        [["aws_instance.a"], [["aws_instance.a", "aws_instance.b"], ["aws_instance.b", "aws_instance.c"]]],
        [["module.net.aws_vpc.main", "module.net.aws_subnet.a[0]", "module.network.aws_vpc.main"],
         [["module.net", "module.core"]]],
        [["aws_instance.web", "aws_instance.web2", "aws_instance.web_old"], [["aws_instance.web", "aws_instance.site"]]],
        [["aws_security_group.web", "aws_instance.web"], [["aws_instance.web", "module.app.aws_instance.web"]]],
        [["aws_instance.web[1]", "aws_instance.web[10]", "aws_instance.web[11]"],
         [["aws_instance.web[1]", "aws_instance.web[\"b\"]"]]],
        [["module.app[0].aws_instance.web", "module.app[1].aws_instance.web"],
         [["module.app[0]", "module.app[\"blue\"]"], ["module.app[1]", "module.app[\"green\"]"]]],
        [["aws_instance.a", "aws_instance.b"], [["aws_instance.a", "aws_instance.tmp"], ["aws_instance.b", "aws_instance.a"],
                                               ["aws_instance.tmp", "aws_instance.b"]]],
        [["aws_instance.x[0]", "aws_instance.x[1]", "aws_instance.y[1]", "aws_instance.y[0]"],
         [["aws_instance.x", "aws_instance.y"]]],
        [["module.a.aws_instance.web", "aws_instance.web"], [["aws_instance.web", "aws_instance.site"]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def applyMoves(addresses, moves):
    current = set(addresses)
    for src, dst in moves:
        rewritten = {a: dst + a[len(src):] for a in current if a.startswith(src)}
        staying = current - set(rewritten)
        clashes = sorted(n for n in rewritten.values() if n in staying)
        if clashes:
            return ["Error: " + clashes[0] + " already exists"]
        current = staying | set(rewritten.values())
    return sorted(current)
''',
        '''def applyMoves(addresses, moves):
    current = set(addresses)
    for src, dst in moves:
        if src in current:
            if dst in current:
                return ["Error: " + dst + " already exists"]
            current.remove(src)
            current.add(dst)
    return sorted(current)
''',
        '''def applyMoves(addresses, moves):
    current = list(addresses)
    for src, dst in moves:
        current = [dst + a[len(src):] if (a == src or a.startswith(src + "[") or a.startswith(src + ".")) else a
                   for a in current]
    return sorted(set(current))
''',
    ],
    guide=dict(
        prereqs="`moved` blocks in *State surgery: moving, removing, importing and repairing* and *Zero-downtime deployment, plans that fail and safe refactoring*. Resource addresses with indices and module prefixes. Python sets and `str.startswith`.",
        intuition="State is a lookup table from address to real object. A move edits the left-hand column and never touches the objects. Because addresses nest (a module contains resources, a resource contains instances), renaming something higher up renames everything beneath it, the way renaming a folder changes the path of every file inside.",
        hints=[
            "A plain `startswith(from)` is too generous: `aws_instance.web` is a prefix of `aws_instance.web2`. Which character must come next for it to be the same resource?",
            "Process one move at a time against the *current* set, so a later move can pick up what an earlier one produced.",
            "Split the current set into addresses the move rewrites and addresses it leaves alone. A collision is a rewritten address that already sits in the second group.",
        ],
        brute_force="For each move, loop over a list of addresses and rewrite matches in place, then scan the whole list for duplicates: O(m·n²) with the duplicate scan. Sets bring the collision check down to O(1) per address.",
        approach="""For each `[from, to]`:

1. `rewritten = {A: to + A[len(from):]}` for every `A` that equals `from` or continues with `[` or `.`.
2. `staying = current - rewritten.keys()`.
3. Any rewritten address found in `staying` is a collision → return the error for the smallest one.
4. `current = staying ∪ rewritten.values()`.

**Dry run:** state `module.net.aws_vpc.main`, `module.net.aws_subnet.a[0]`, `module.network.aws_vpc.main`; move `module.net → module.core`.

| address | next character after `module.net` | affected | becomes |
|---|---|---|---|
| module.net.aws_vpc.main | `.` | yes | module.core.aws_vpc.main |
| module.net.aws_subnet.a[0] | `.` | yes | module.core.aws_subnet.a[0] |
| module.network.aws_vpc.main | `w` | no | unchanged |

The swap test (`a → tmp`, `b → a`, `tmp → b`) shows why moves must be applied in order: each step sees the result of the one before.""",
        complexity="Time O(m·n·L) for m moves, n addresses and address length L. Space O(n·L).",
        pitfalls="Prefix matching without a boundary (first wrong solution) drags along unrelated resources whose names begin the same way, and `web[1]` would capture `web[10]`. Handling only exact matches (second wrong solution) misses every instance of a renamed `count` or `for_each` resource. Skipping the collision check (third wrong solution) merges two different real objects into one address, which in real life would orphan one of them.",
        follow_up="Generate the `moved` blocks needed to convert a `count` resource to `for_each`: given the list of names, emit one `[resource[i], resource[\"name\"]]` pair per index.",
    ),
),
dict(
    id="tf-parse-address",
    title="Parse a resource address",
    difficulty="Medium",
    pattern="Loops & Addresses",
    entry="parseAddress",
    description=r"""
Every object Terraform manages has an address, and plans, state commands and error messages all speak in
addresses. Write `parseAddress(address)` to take one apart.

An address is, from left to right:

1. zero or more module steps, each written `module.<name>` and optionally followed by an instance key;
2. optionally the word `data.` (a data source, which reads something, instead of a managed resource);
3. `<type>.<name>`, optionally followed by an instance key.

An **instance key** is `[<whole number>]` (from `count`) or `["<text>"]` (from `for_each`). The text between
the double quotes may contain any characters except a double quote, **including dots and square brackets**.
Module names, types and resource names contain only letters, digits, underscores and hyphens.

Return a dict:

```
{"modules": [[name, key], ...], "mode": "managed" or "data", "type": str, "name": str, "key": key}
```

where a key is `None` when absent, an `int` for a number and a `str` for quoted text.

**Example 1:** `"aws_instance.web[2]"` →
`{"modules": [], "mode": "managed", "type": "aws_instance", "name": "web", "key": 2}`

**Example 2:** `'module.net.module.subnets["app-a"].data.aws_ami.ubuntu'` →
`{"modules": [["net", None], ["subnets", "app-a"]], "mode": "data", "type": "aws_ami", "name": "ubuntu", "key": None}`
""",
    starter='''def parseAddress(address):
    pass
''',
    solution='''def parseAddress(address):
    parts = []                      # [name, key] for each dot-separated step
    i, n = 0, len(address)
    while i < n:
        j = i
        while j < n and address[j] not in ".[":
            j += 1
        name = address[i:j]
        key = None
        if j < n and address[j] == "[":
            if address[j + 1] == '"':
                end = address.index('"', j + 2)
                key = address[j + 2:end]
                j = end + 2         # past the closing quote and the bracket
            else:
                end = address.index("]", j)
                key = int(address[j + 1:end])
                j = end + 1
        parts.append([name, key])
        i = j + 1                   # past the dot

    modules = []
    k = 0
    while parts[k][0] == "module" and len(parts) - k > 2:
        modules.append([parts[k + 1][0], parts[k + 1][1]])
        k += 2
    mode = "managed"
    if parts[k][0] == "data" and len(parts) - k > 2:
        mode = "data"
        k += 1
    return {"modules": modules, "mode": mode, "type": parts[k][0],
            "name": parts[k + 1][0], "key": parts[k + 1][1]}
''',
    tests=[
        ["aws_instance.web[2]"],
        ["module.net.module.subnets[\"app-a\"].data.aws_ami.ubuntu"],
        ["aws_vpc.main"],
        ["data.aws_caller_identity.current"],
        ["aws_iam_user.staff[\"asha\"]"],
        ["aws_route53_record.site[\"www.example.com\"]"],
        ["module.app[0].aws_instance.web[10]"],
        ["module.env[\"prod.sg\"].module.db.aws_db_instance.this"],
        ["aws_s3_bucket.logs[\"a[0].b\"]"],
        ["module.module.aws_instance.data"],
        ["module.data.data.aws_ami.module[0]"],
        ["aws_instance.web[0]"],
        ["module.a.module.b.module.c[\"x\"].module.d[3].aws_lb.front[\"blue-green\"]"],
        ["aws_iam_user.staff[\"\"]"],
        ["data.aws_subnet.by_az[\"ap-southeast-1a\"]"],
    ],
    examples=2,
    wrong_solutions=[
        '''def parseAddress(address):
    import re
    def split(step):
        m = re.fullmatch(r'([^\\[]+)(?:\\[(?:"(.*)"|(\\d+))\\])?', step)
        key = m.group(2) if m.group(2) is not None else (int(m.group(3)) if m.group(3) else None)
        return [m.group(1), key]
    parts = [split(s) for s in address.split(".")]
    modules, k = [], 0
    while parts[k][0] == "module" and len(parts) - k > 2:
        modules.append(parts[k + 1]); k += 2
    mode = "managed"
    if parts[k][0] == "data" and len(parts) - k > 2:
        mode = "data"; k += 1
    return {"modules": modules, "mode": mode, "type": parts[k][0], "name": parts[k + 1][0], "key": parts[k + 1][1]}
''',
        '''def parseAddress(address):
    parts, i, n = [], 0, len(address)
    while i < n:
        j = i
        while j < n and address[j] not in ".[":
            j += 1
        name, key = address[i:j], None
        if j < n and address[j] == "[":
            if address[j + 1] == '"':
                end = address.index('"', j + 2); key = address[j + 2:end]; j = end + 2
            else:
                end = address.index("]", j); key = address[j + 1:end]; j = end + 1
        parts.append([name, key]); i = j + 1
    modules, k = [], 0
    while parts[k][0] == "module" and len(parts) - k > 2:
        modules.append(parts[k + 1]); k += 2
    return {"modules": modules, "mode": "managed", "type": parts[k][0], "name": parts[k + 1][0], "key": parts[k + 1][1]}
''',
    ],
    guide=dict(
        prereqs="Resource addresses from *Installing Terraform, signing in safely and creating a first resource*, module addresses from *Reusable modules: inputs, outputs and locals*, and instance keys from *Loops: count, for_each and the index-shifting trap*. Scanning a string with an index.",
        intuition="An address is a path, like a file path with dots for slashes. The catch is that a `for_each` key is free text and may itself contain dots, so you cannot split on dots blindly. Read the string left to right: take a name, then check whether a bracket follows, and if it opens with a quote, jump straight to the closing quote without inspecting what lies between.",
        hints=[
            "Tokenise first, interpret second. Produce a flat list of `[name, key]` steps before thinking about modules.",
            "After a name, the next character is a dot, a `[`, or the end. For `[\"`, find the next double quote; for `[` and a digit, find the next `]`.",
            "Then consume steps from the left: while the step is `module`, the following step is a module name. After the modules, an optional `data` step, and the last two steps are type and name.",
        ],
        brute_force="Split on `.` and repair the pieces that were cut inside quotes by gluing them back together. It can be made to work, but the repair logic is harder to get right than a single left-to-right scan.",
        approach="""**Tokenise.** Keep an index `i`. Advance `j` to the next `.` or `[`. The slice is a name. If `[` follows: a quote means a string key ending at the next quote; otherwise an integer ending at `]`. Skip the dot and repeat.

**Interpret.** With steps `parts` and a cursor `k`:

1. While `parts[k]` is named `module` *and more than two steps remain*, record `parts[k+1]` as a module step and move `k` on by two.
2. If `parts[k]` is named `data` and more than two steps remain, the mode is `data`; move on by one.
3. `parts[k]` is the type; `parts[k+1]` carries the name and the resource's key.

The "more than two steps remain" guard covers odd but legal names: a resource can be *named* `module` or `data`.

**Dry run** on `module.env["prod.sg"].module.db.aws_db_instance.this`:

| step | name | key |
|---|---|---|
| 0 | module | None |
| 1 | env | "prod.sg" |
| 2 | module | None |
| 3 | db | None |
| 4 | aws_db_instance | None |
| 5 | this | None |

Modules `[["env", "prod.sg"], ["db", None]]`, type `aws_db_instance`, name `this`.""",
        complexity="Time O(L) for an address of length L: each character is examined a constant number of times. Space O(L).",
        pitfalls="Splitting on every dot (first wrong solution) breaks keys such as `\"www.example.com\"`. Leaving a numeric key as a string, or forgetting data sources (second wrong solution). Treating an empty quoted key as 'no key': `[\"\"]` is the empty string, not `None`. Looking for `]` to end a quoted key, which fails when the key contains a bracket.",
        follow_up="Write the inverse, `formatAddress(parsed)`, and check that formatting then parsing returns the original dict for every test.",
    ),
),
]
