PROBLEMS = [
dict(
    id="tf-dependency-order",
    title="Build the dependency graph and an apply order",
    difficulty="Medium",
    pattern="Dependency Graph",
    entry="applyOrder",
    description=r"""
Terraform finds dependencies by spotting references to other resources inside a resource's arguments, then
creates resources so that everything a resource refers to already exists. Write `applyOrder(config)`.

`config` maps each resource address (always of the form `type.name`, lower-case letters, digits and
underscores) to a list of expression strings taken from its arguments, for example
`{"aws_instance.web": ["aws_subnet.public.id", "[aws_security_group.web.id]"]}`.

**Finding references.** Resource `A` depends on resource `B` (with `B != A`) when `B`'s address occurs in one
of `A`'s expressions as a whole reference: the character immediately before the occurrence must not be a
letter, digit, underscore or dot, and the character immediately after must not be a letter, digit or underscore.
(So `aws_vpc.main` is referenced by `aws_vpc.main.id` and by `[aws_vpc.main.id]`, but not by
`aws_vpc.main2.id`, `my_aws_vpc.main.id` or `module.net.aws_vpc.main.id`.) Text that names something not in
`config` is ignored.

**Ordering.** Repeatedly pick, among the resources whose dependencies have all been picked already, the one
with the alphabetically smallest address. The input is guaranteed to contain no cycles.

Return the list of addresses in that order.

**Example:** `{"aws_subnet.a": ["aws_vpc.main.id"], "aws_vpc.main": ["10.0.0.0/16"], "aws_eip.x": []}`
→ `["aws_eip.x", "aws_vpc.main", "aws_subnet.a"]`
""",
    starter='''def applyOrder(config):
    pass
''',
    solution='''import heapq

def applyOrder(config):
    ident = set("abcdefghijklmnopqrstuvwxyz0123456789_")

    def references(expr, addr):
        start = 0
        while True:
            i = expr.find(addr, start)
            if i == -1:
                return False
            before = expr[i - 1] if i > 0 else ""
            after = expr[i + len(addr)] if i + len(addr) < len(expr) else ""
            if not (before in ident or before == ".") and after not in ident:
                return True
            start = i + 1

    deps = {a: set() for a in config}
    for a, exprs in config.items():
        for b in config:
            if b != a and any(references(e, b) for e in exprs):
                deps[a].add(b)

    dependents = {a: [] for a in config}
    remaining = {a: len(d) for a, d in deps.items()}
    for a, d in deps.items():
        for b in d:
            dependents[b].append(a)

    heap = [a for a, n in remaining.items() if n == 0]
    heapq.heapify(heap)
    order = []
    while heap:
        a = heapq.heappop(heap)
        order.append(a)
        for nxt in dependents[a]:
            remaining[nxt] -= 1
            if remaining[nxt] == 0:
                heapq.heappush(heap, nxt)
    return order
''',
    tests=[
        [{"aws_subnet.a": ["aws_vpc.main.id"], "aws_vpc.main": ["10.0.0.0/16"], "aws_eip.x": []}],
        [{"aws_instance.web": ["aws_subnet.public.id", "[aws_security_group.web.id]"],
          "aws_subnet.public": ["aws_vpc.main.id"], "aws_security_group.web": ["aws_vpc.main.id"],
          "aws_vpc.main": []}],
        [{}],
        [{"a.x": []}],
        [{"c.x": [], "b.x": [], "a.x": []}],
        [{"aws_vpc.main": [], "aws_vpc.main2": [], "aws_subnet.a": ["aws_vpc.main2.id"]}],
        [{"aws_vpc.main": [], "aws_subnet.a": ["module.net.aws_vpc.main.id", "my_aws_vpc.main.id"]}],
        [{"aws_instance.web": ["aws_instance.web.id", "var.name"], "aws_eip.web": ["${aws_instance.web.id}"]}],
        [{"z.last": [], "a.first": ["z.last.id"], "b.mid": ["a.first.arn"], "c.free": []}],
        [{"aws_lb.web": ["aws_subnet.a.id,aws_subnet.b.id", "aws_security_group.alb.id"],
          "aws_subnet.a": ["aws_vpc.main.id"], "aws_subnet.b": ["aws_vpc.main.id"],
          "aws_security_group.alb": ["aws_vpc.main.id"], "aws_vpc.main": [],
          "aws_lb_listener.http": ["aws_lb.web.arn", "aws_lb_target_group.web.arn"],
          "aws_lb_target_group.web": ["aws_vpc.main.id"]}],
        [{"r.b": ["join(\"-\", [r.a.id, \"x\"])"], "r.a": ["data.r.a.id"], "r.c": ["r.b[0].id", "r.a[\"k\"].id"]}],
        [{f"r.n{i:03d}": ([f"r.n{i + 1:03d}.id"] if i < 119 else []) for i in range(120)}],
        [{"a.a": ["b.b.id"], "b.b": ["c.c.id"], "c.c": [], "a.b": ["c.c.id"], "a.c": []}],
        [{"aws_subnet.b": [], "aws_vpc.c": [], "aws_eip.a": ["aws_subnet.b.id"]}],
        [{"m.root": [], "z.other": [], "a.leaf": ["m.root.id"], "b.leaf": ["a.leaf.id"], "y.other": ["z.other.id"]}],
    ],
    examples=2,
    wrong_solutions=[
        '''def applyOrder(config):
    deps = {a: {b for b in config if b != a and any(b in e for e in exprs)} for a, exprs in config.items()}
    order, done = [], set()
    while len(order) < len(config):
        ready = sorted(a for a in config if a not in done and deps[a] <= done)
        order.append(ready[0]); done.add(ready[0])
    return order
''',
        '''def applyOrder(config):
    return sorted(config)
''',
        '''def applyOrder(config):
    import re
    deps = {a: {b for b in config if b != a and any(re.search(r"(?<![a-z0-9_.])" + re.escape(b) + r"(?![a-z0-9_])", e) for e in exprs)}
            for a, exprs in config.items()}
    order, done = [], set()
    while len(order) < len(config):
        wave = sorted(a for a in config if a not in done and deps[a] <= done)
        order.extend(wave); done.update(wave)
    return order
''',
    ],
    guide=dict(
        prereqs="References and the dependency graph in *Variables, outputs, references and a configurable web server*. Topological sorting; a min-heap (`heapq`).",
        intuition="Two separate jobs. First turn text into edges by recognising whole references. Then produce a topological order, and make it deterministic by always choosing the smallest address that is ready: Kahn's algorithm with a priority queue instead of a plain queue.",
        hints=[
            "A plain substring test is not enough: `aws_vpc.main` occurs inside `aws_vpc.main2`. Check the characters on both sides of each occurrence.",
            "Count, for every resource, how many dependencies are not yet created. Those with zero are ready.",
            "Keep the ready set in a min-heap. Pop the smallest, then decrement the counts of its dependents and push any that reach zero.",
        ],
        brute_force="Recompute the full ready set and sort it after every pick: O(V) picks, each O(V log V) plus set comparisons, about O(V² log V). Correct, and fine for small inputs. The heap version is O((V + E) log V) after edge discovery.",
        approach="""**Edges.** For each pair (A, B) with A ≠ B, scan A's expressions for occurrences of B's address and accept an occurrence when the previous character is not an identifier character or a dot and the next is not an identifier character. A dot *after* is fine (`.id`); so is `[`.

**Order.** `remaining[A]` = number of dependencies. Heap = all with zero. Pop the smallest, append it, and release its dependents.

**Dry run:** `a.first` needs `z.last`; `b.mid` needs `a.first`; `c.free` and `z.last` need nothing.

| heap before | pop | released |
|---|---|---|
| c.free, z.last | c.free | — |
| z.last | z.last | a.first |
| a.first | a.first | b.mid |
| b.mid | b.mid | — |

Result `["c.free", "z.last", "a.first", "b.mid"]`. Note `a.first` could not jump ahead of `c.free` merely because it sorts first: it was not ready.""",
        complexity="Edge discovery is O(V² · L) for V resources and total expression length L in this simple form. The ordering is O((V + E) log V). Space O(V + E).",
        pitfalls="Substring matching without boundaries. Counting a self-reference as a dependency. Emitting whole 'waves' in sorted order (the third wrong solution): that differs from smallest-ready-first when a newly released resource sorts before something still waiting in the same wave. Returning plain alphabetical order.",
        follow_up="Group the result into waves of resources that can be created in parallel, as `terraform apply` does with its default parallelism of 10.",
    ),
),
dict(
    id="tf-destroy-order",
    title="Compute a destroy order",
    difficulty="Medium",
    pattern="Dependency Graph",
    entry="destroyOrder",
    description=r"""
Destroying happens in the reverse of creation order: anything that depends on a resource must go first.
Write `destroyOrder(depends_on, targets)`.

- `depends_on` maps every resource address to the list of addresses it depends on (all of them keys; no cycles).
- `targets` is a list of addresses someone asked to destroy.

**What gets destroyed.** The set `S` of every target plus every resource that depends on a member of `S`,
directly or through a chain. (You cannot leave a subnet behind when its VPC is deleted.)

**In which order.** First compute the *creation* order of `S` alone: repeatedly pick, among the members of `S`
whose dependencies inside `S` have all been picked, the alphabetically smallest. Dependencies outside `S` are
ignored. The destroy order is that list reversed.

Return the destroy order.

**Example:** `{"vpc": [], "subnet": ["vpc"], "db": ["subnet"], "app": ["subnet", "db"], "dns": []}` with
`targets = ["subnet"]` → creation order of `{subnet, db, app}` is `subnet, db, app`, so the answer is
`["app", "db", "subnet"]`. The VPC and the DNS record are untouched.
""",
    starter='''def destroyOrder(depends_on, targets):
    pass
''',
    solution='''import heapq

def destroyOrder(depends_on, targets):
    dependents = {a: [] for a in depends_on}
    for a, deps in depends_on.items():
        for d in deps:
            dependents[d].append(a)

    doomed = set()
    stack = [t for t in targets]
    while stack:
        node = stack.pop()
        if node in doomed:
            continue
        doomed.add(node)
        stack.extend(dependents[node])

    remaining = {a: len({d for d in depends_on[a] if d in doomed}) for a in doomed}
    heap = [a for a, n in remaining.items() if n == 0]
    heapq.heapify(heap)
    created = []
    while heap:
        a = heapq.heappop(heap)
        created.append(a)
        for nxt in set(dependents[a]):
            if nxt in doomed:
                remaining[nxt] -= 1
                if remaining[nxt] == 0:
                    heapq.heappush(heap, nxt)
    return created[::-1]
''',
    tests=[
        [{"vpc": [], "subnet": ["vpc"], "db": ["subnet"], "app": ["subnet", "db"], "dns": []}, ["subnet"]],
        [{"vpc": [], "subnet": ["vpc"], "db": ["subnet"], "app": ["subnet", "db"], "dns": []}, ["vpc", "dns"]],
        [{"a": []}, []],
        [{"a": []}, ["a"]],
        [{"a": [], "b": [], "c": []}, ["b", "a", "c"]],
        [{"a": [], "b": ["a"], "c": ["a"], "d": ["b", "c"]}, ["a"]],
        [{"a": [], "b": ["a"], "c": ["a"], "d": ["b", "c"]}, ["d"]],
        [{"a": [], "b": ["a"], "c": ["a"], "d": ["b", "c"]}, ["b", "d", "b"]],
        [{"net": [], "sg": ["net"], "alb": ["net", "sg"], "asg": ["sg", "alb"], "dns": ["alb"], "alarm": ["asg"]},
         ["alb"]],
        [{"z": [], "a": ["z"], "m": [], "b": ["m"]}, ["z", "m"]],
        [{"shared": [], "x": ["shared", "shared"], "y": ["x"]}, ["shared"]],
        [{f"n{i:03d}": ([f"n{i - 1:03d}"] if i else []) for i in range(200)}, ["n150"]],
        [{"a": [], "b": ["a"], "c": ["b"], "d": ["a"], "e": ["d", "c"], "f": []}, ["b", "d"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def destroyOrder(depends_on, targets):
    seen, order = set(), []
    for t in sorted(set(targets), reverse=True):
        if t not in seen:
            seen.add(t); order.append(t)
    return order
''',
        '''def destroyOrder(depends_on, targets):
    dependents = {a: [] for a in depends_on}
    for a, deps in depends_on.items():
        for d in deps:
            dependents[d].append(a)
    doomed, stack = set(), list(targets)
    while stack:
        n = stack.pop()
        if n not in doomed:
            doomed.add(n); stack.extend(dependents[n])
    return sorted(doomed, reverse=True)
''',
    ],
    guide=dict(
        prereqs="Creation and destruction order in *Variables, outputs, references and a configurable web server*. The problem *Build the dependency graph and an apply order*.",
        intuition="Destroying one thing drags along everything built on top of it. So: find the doomed set by walking *up* the graph from the targets, then order that set exactly as you would for creation and flip the list.",
        hints=[
            "Reverse the edges to get, for each resource, the list of resources that depend on it.",
            "Flood-fill from the targets along those reversed edges to collect the doomed set.",
            "Run the smallest-ready-first topological sort on the doomed set only, ignoring edges that leave the set, then reverse.",
        ],
        brute_force="Compute the creation order of the whole system, reverse it, and filter to the doomed set. That is simpler but is *not* the same definition: restricting to the set first can change which resource is 'smallest ready' at each step. Follow the stated definition.",
        approach="""1. Build `dependents`.
2. Depth-first search from each target over `dependents` → `doomed`.
3. `remaining[a]` = number of distinct dependencies of `a` inside `doomed`.
4. Min-heap Kahn's algorithm over `doomed` → creation order; reverse it.

**Dry run** with targets `["subnet"]`: doomed = `{subnet, db, app}`.

| step | ready heap | pick |
|---|---|---|
| 1 | subnet (its only dependency, vpc, is outside the set) | subnet |
| 2 | db | db |
| 3 | app | app |

Creation `[subnet, db, app]`, destroy `[app, db, subnet]`.""",
        complexity="Time O((V + E) log V); space O(V + E).",
        pitfalls="Destroying only the listed targets and leaving dependents pointing at nothing. Sorting the doomed set alphabetically and reversing, which ignores dependencies. Counting a duplicated dependency twice so a counter never reaches zero. Duplicate targets.",
        follow_up="`terraform destroy -target=X` behaves this way and prints a warning. Explain why routine use of `-target` is discouraged.",
    ),
),
dict(
    id="tf-cycle-detect",
    title="Detect a dependency cycle with a helpful message",
    difficulty="Hard",
    pattern="Dependency Graph",
    entry="findCycle",
    description=r"""
If resources depend on each other in a loop, nothing can be created first and Terraform stops with
`Error: Cycle`. A good error names the loop. Write `findCycle(depends_on)`.

`depends_on` maps each resource address to the list of addresses it depends on. Entries that are not keys of
`depends_on` are ignored. A resource may list itself.

- If there is no cycle, return the empty string `""`.
- Otherwise return `"Cycle: n1 -> n2 -> ... -> n1"` where `a -> b` means "a depends on b", chosen as follows
  so that the answer is unique:
  1. Let `s` be the alphabetically smallest address that lies on at least one cycle.
  2. Among all cycles that start and end at `s`, take the shortest (fewest arrows).
  3. If several are equally short, take the one whose sequence of addresses is alphabetically smallest
     (compare the second address, then the third, and so on).

**Example 1:** `{"a": ["b"], "b": ["c"], "c": ["a"]}` → `"Cycle: a -> b -> c -> a"`

**Example 2:** `{"web": ["sg"], "sg": ["web"], "db": []}` → `"Cycle: sg -> web -> sg"`

**Example 3:** `{"a": ["a"]}` → `"Cycle: a -> a"`
""",
    starter='''def findCycle(depends_on):
    pass
''',
    solution='''from collections import deque

def findCycle(depends_on):
    graph = {a: sorted({d for d in deps if d in depends_on}) for a, deps in depends_on.items()}
    reverse = {a: [] for a in graph}
    for a, deps in graph.items():
        for d in deps:
            reverse[d].append(a)

    for s in sorted(graph):
        # dist[x] = fewest arrows needed to get from x to s
        dist = {s: 0}
        queue = deque([s])
        while queue:
            node = queue.popleft()
            for prev in reverse[node]:
                if prev not in dist:
                    dist[prev] = dist[node] + 1
                    queue.append(prev)
        starts = [d for d in graph[s] if d in dist]
        if not starts:
            continue
        best = min(dist[d] for d in starts)
        path = [s]
        node = min(d for d in starts if dist[d] == best)
        while node != s:
            path.append(node)
            node = min(d for d in graph[node] if d in dist and dist[d] == dist[node] - 1)
        path.append(s)
        return "Cycle: " + " -> ".join(path)
    return ""
''',
    tests=[
        [{"a": ["b"], "b": ["c"], "c": ["a"]}],
        [{"web": ["sg"], "sg": ["web"], "db": []}],
        [{"a": ["a"]}],
        [{}],
        [{"a": [], "b": ["a"], "c": ["a", "b"]}],
        [{"a": ["ghost"], "ghost2": ["a"]}],
        [{"z": ["y"], "y": ["z"], "a": ["z"]}],
        [{"a": ["b", "c"], "b": ["d"], "c": ["a"], "d": ["a"]}],
        [{"a": ["c", "b"], "b": ["a"], "c": ["a"]}],
        [{"a": ["b"], "b": ["c", "d"], "c": ["e"], "d": ["e"], "e": ["a"]}],
        [{"m": ["n"], "n": ["m"], "b": ["c"], "c": ["d"], "d": ["b"], "a": ["b"]}],
        [{"a": ["b"], "b": ["c"], "c": ["b"]}],
        [{"x": ["x", "y"], "y": ["x"], "a": ["x"]}],
        [{f"n{i:03d}": [f"n{(i + 1) % 150:03d}"] for i in range(150)}],
        [{f"n{i:03d}": ([f"n{i + 1:03d}"] if i < 149 else []) for i in range(150)}],
    ],
    examples=3,
    wrong_solutions=[
        '''def findCycle(depends_on):
    for a in sorted(depends_on):
        if a in depends_on[a]:
            return f"Cycle: {a} -> {a}"
        for b in sorted(depends_on[a]):
            if b in depends_on and a in depends_on[b]:
                return f"Cycle: {a} -> {b} -> {a}"
    return ""
''',
        '''def findCycle(depends_on):
    graph = {a: sorted(d for d in deps if d in depends_on) for a, deps in depends_on.items()}
    def dfs(node, path, seen):
        for nxt in graph[node]:
            if nxt == path[0]:
                return path + [nxt]
            if nxt not in seen:
                seen.add(nxt)
                found = dfs(nxt, path + [nxt], seen)
                if found:
                    return found
        return None
    for s in sorted(graph):
        found = dfs(s, [s], {s})
        if found:
            return "Cycle: " + " -> ".join(found)
    return ""
''',
    ],
    guide=dict(
        prereqs="The dependency graph and `Error: Cycle` in *Variables, outputs, references and a configurable web server*. Breadth-first search for shortest paths.",
        intuition="'Is there a cycle?' is easy; 'which one, reproducibly?' needs a rule. A cycle through `s` is a path that leaves `s` and comes back. If you know, for every node, how many arrows it takes to get back to `s`, you can walk from `s` choosing at each step the smallest neighbour that is exactly one arrow closer to home. That walk is the shortest cycle and, among the shortest, the alphabetically smallest.",
        hints=[
            "Try each address in alphabetical order as the candidate `s`; the first one that lies on a cycle is the answer's start.",
            "Run a breadth-first search *backwards* from `s` (over reversed edges) to get `dist[x]` = arrows needed from `x` to `s`.",
            "`s` is on a cycle when one of its own dependencies has a distance. Then greedily step to the smallest neighbour with distance one less.",
        ],
        brute_force="Enumerate every simple path starting at each node with depth-first search and keep the best cycle found. Exponential in the worst case. The breadth-first approach is polynomial.",
        approach="""For `s` in sorted order:

1. Reverse BFS from `s` gives `dist`.
2. Candidates = dependencies of `s` that have a distance. None → `s` is on no cycle; try the next address.
3. `best` = smallest candidate distance. First step = smallest candidate with that distance.
4. From there, repeatedly move to the smallest dependency whose distance is exactly one less, until reaching `s`.

**Dry run** on `{"a": ["b"], "b": ["c", "d"], "c": ["e"], "d": ["e"], "e": ["a"]}` with `s = a`:
distances to `a`: e = 1, c = 2, d = 2, b = 3. Start at `a`; its only dependency `b` has distance 3. From `b`, both `c` and `d` have distance 2; pick `c`. Then `e` (1), then `a` (0).
Answer: `Cycle: a -> b -> c -> e -> a`.

Why a plain depth-first search fails (second wrong solution): on `{"a": ["b", "c"], "b": ["d"], "c": ["a"], "d": ["a"]}` it explores `b` first and reports `a -> b -> d -> a`, missing the shorter `a -> c -> a`.""",
        complexity="One reverse BFS is O(V + E); at most V candidates → O(V·(V + E)) time, O(V + E) space. The neighbour lists are sorted once.",
        pitfalls="Detecting only self-loops and two-node loops. Reporting whichever cycle depth-first search meets first, which is neither shortest nor deterministic by the stated rule. Starting from a node that leads *into* a cycle without being on it (`a` in `{\"z\": [\"y\"], \"y\": [\"z\"], \"a\": [\"z\"]}`). Following dependencies on addresses that are not declared.",
        follow_up="Real cycles often come from security groups that reference each other inline. Explain how separate rule resources break such a cycle.",
    ),
),
dict(
    id="tf-create-before-destroy",
    title="Order the steps of a replacement plan",
    difficulty="Medium",
    pattern="Lifecycle",
    entry="replacementSteps",
    description=r"""
Several resources are all being **replaced** in one apply. Some have `create_before_destroy = true`. Work out
the order of operations. Write `replacementSteps(resources)`.

`resources` is a list of dicts `{"address": str, "cbd": bool, "depends_on": [addresses]}`. Every resource in
the list is being replaced; `depends_on` only mentions addresses in the list; there are no cycles.

**Rule 1: propagation.** If a resource has `create_before_destroy`, every resource it depends on, directly or
through a chain, is treated as having it too. (Otherwise the old dependency would be destroyed while the old
dependent still needs it.) Call the result the *effective* setting.

**Rule 2: three phases.**

1. **Destroy first.** Every resource whose effective setting is false is destroyed now, dependents before
   their dependencies. Step text: `"destroy <address>"`.
2. **Create.** Every resource is created, dependencies before dependents. Step text: `"create <address>"`.
3. **Destroy deposed.** Every resource whose effective setting is true has its old object destroyed,
   dependents before their dependencies. Step text: `"destroy deposed <address>"`.

**Tie-breaking.** "Dependencies before dependents" means: repeatedly pick the alphabetically smallest address
whose dependencies (within the group being ordered) are all picked. "Dependents before dependencies" is that
same order reversed. In phases 1 and 3 the ordering is computed over only the resources in that phase.

Return the list of step strings.

**Example:** `lt` (cbd true, no dependencies) and `asg` (cbd false, depends on `lt`) →
`["destroy asg", "create lt", "create asg", "destroy deposed lt"]`
""",
    starter='''def replacementSteps(resources):
    pass
''',
    solution='''import heapq

def replacementSteps(resources):
    deps = {r["address"]: sorted(set(r["depends_on"])) for r in resources}
    effective = {r["address"]: bool(r["cbd"]) for r in resources}

    stack = [a for a, v in effective.items() if v]
    while stack:
        node = stack.pop()
        for d in deps[node]:
            if not effective[d]:
                effective[d] = True
                stack.append(d)

    def creation_order(group):
        group = set(group)
        remaining = {a: sum(1 for d in deps[a] if d in group) for a in group}
        dependents = {a: [] for a in group}
        for a in group:
            for d in deps[a]:
                if d in group:
                    dependents[d].append(a)
        heap = [a for a, n in remaining.items() if n == 0]
        heapq.heapify(heap)
        order = []
        while heap:
            a = heapq.heappop(heap)
            order.append(a)
            for nxt in dependents[a]:
                remaining[nxt] -= 1
                if remaining[nxt] == 0:
                    heapq.heappush(heap, nxt)
        return order

    early = [a for a, v in effective.items() if not v]
    late = [a for a, v in effective.items() if v]
    steps = [f"destroy {a}" for a in reversed(creation_order(early))]
    steps += [f"create {a}" for a in creation_order(deps)]
    steps += [f"destroy deposed {a}" for a in reversed(creation_order(late))]
    return steps
''',
    tests=[
        [[{"address": "lt", "cbd": True, "depends_on": []},
          {"address": "asg", "cbd": False, "depends_on": ["lt"]}]],
        [[{"address": "sg", "cbd": False, "depends_on": []},
          {"address": "lt", "cbd": True, "depends_on": ["sg"]}]],
        [[]],
        [[{"address": "a", "cbd": False, "depends_on": []}]],
        [[{"address": "a", "cbd": True, "depends_on": []}]],
        [[{"address": "a", "cbd": False, "depends_on": []},
          {"address": "b", "cbd": False, "depends_on": ["a"]},
          {"address": "c", "cbd": False, "depends_on": ["b"]}]],
        [[{"address": "a", "cbd": False, "depends_on": []},
          {"address": "b", "cbd": False, "depends_on": ["a"]},
          {"address": "c", "cbd": True, "depends_on": ["b"]}]],
        [[{"address": "net", "cbd": False, "depends_on": []},
          {"address": "sg", "cbd": False, "depends_on": ["net"]},
          {"address": "lt", "cbd": True, "depends_on": ["sg"]},
          {"address": "asg", "cbd": False, "depends_on": ["lt", "net"]},
          {"address": "dns", "cbd": False, "depends_on": []}]],
        [[{"address": "z", "cbd": False, "depends_on": []},
          {"address": "y", "cbd": False, "depends_on": []},
          {"address": "x", "cbd": True, "depends_on": []}]],
        [[{"address": "cert", "cbd": True, "depends_on": []},
          {"address": "listener", "cbd": False, "depends_on": ["cert", "lb"]},
          {"address": "lb", "cbd": False, "depends_on": []},
          {"address": "rule", "cbd": False, "depends_on": ["listener"]}]],
        [[{"address": "a", "cbd": False, "depends_on": []},
          {"address": "b", "cbd": True, "depends_on": ["a", "a"]},
          {"address": "c", "cbd": False, "depends_on": ["a"]},
          {"address": "d", "cbd": True, "depends_on": ["b", "c"]}]],
        [[{"address": f"r{i:02d}", "cbd": i == 20, "depends_on": ([f"r{i - 1:02d}"] if i else [])} for i in range(40)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def replacementSteps(resources):
    deps = {r["address"]: sorted(set(r["depends_on"])) for r in resources}
    eff = {r["address"]: bool(r["cbd"]) for r in resources}
    def order(group):
        group = set(group); done = []; s = set()
        while len(done) < len(group):
            a = min(x for x in group if x not in s and all(d in s or d not in group for d in deps[x]))
            done.append(a); s.add(a)
        return done
    steps = ["destroy " + a for a in reversed(order([a for a in eff if not eff[a]]))]
    steps += ["create " + a for a in order(deps)]
    steps += ["destroy deposed " + a for a in reversed(order([a for a in eff if eff[a]]))]
    return steps
''',
        '''def replacementSteps(resources):
    steps = []
    for r in sorted(resources, key=lambda r: r["address"]):
        a = r["address"]
        steps += ["create " + a, "destroy deposed " + a] if r["cbd"] else ["destroy " + a, "create " + a]
    return steps
''',
    ],
    guide=dict(
        prereqs="`create_before_destroy` and its spread to dependencies in *Zero-downtime deployment, plans that fail and safe refactoring*. The apply-order problem in this track.",
        intuition="Replacement order is decided per resource, but resources are linked. If the new server must exist before the old one is removed, then the old firewall it uses must also survive until then, so the setting flows *down* to dependencies. After that, the apply is three sweeps: tear down what may go first, build everything, sweep away the kept-alive old objects.",
        hints=[
            "Compute the effective setting first: start from every resource with the flag and walk its dependencies, marking each one.",
            "Write one helper that returns the smallest-ready-first creation order for any subset of resources.",
            "Phase 1 is the reversed order of the non-flagged subset, phase 2 the order of everything, phase 3 the reversed order of the flagged subset.",
        ],
        brute_force="Handle each resource independently in alphabetical order, as the second wrong solution does. It ignores dependencies entirely and produces orders such as creating a server before its launch template.",
        approach="""**Propagate.** Stack = flagged resources. Pop one, mark each unmarked dependency as flagged and push it.

**Order.** `creation_order(group)`: Kahn's algorithm with a min-heap, counting only dependencies inside the group.

**Dry run:** `net`, `sg → net`, `lt (cbd) → sg`, `asg → lt, net`, `dns`.

- Propagation: `lt` flags `sg`, which flags `net`. Effective true: `{lt, sg, net}`; false: `{asg, dns}`.
- Phase 1 (false group, creation order `asg, dns`, reversed): `destroy dns`, `destroy asg`.
- Phase 2 (all): `create dns`, `create net`, `create sg`, `create lt`, `create asg`.
- Phase 3 (true group, creation order `net, sg, lt`, reversed): `destroy deposed lt`, `destroy deposed sg`, `destroy deposed net`.""",
        complexity="Time O((V + E) log V) for three topological sorts; space O(V + E).",
        pitfalls="Skipping propagation (first wrong solution): the old dependency is destroyed in phase 1 while the old dependent still exists. Propagating in the wrong direction, to dependents. Ordering phase 1 and phase 3 by the full graph instead of within their own group. Duplicate entries in `depends_on`.",
        follow_up="Why does `create_before_destroy` require unique names? Add a `fixed_name` flag and report a name-collision error for flagged resources that have it.",
    ),
),
]
