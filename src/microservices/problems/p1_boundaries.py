PROBLEMS = [
dict(
    id="msvc-coupling-type",
    title="Classify the Coupling Between Two Services",
    difficulty="Easy",
    pattern="Coupling & Cohesion",
    entry="classify_coupling",
    description=r"""
Service **A** and service **B** are described by a list of fact strings. Return the name of the **tightest** kind of coupling the facts reveal.

| Fact string | Meaning | Coupling it implies |
|---|---|---|
| `"calls_api"` | A calls B through B's published interface | `"domain"` |
| `"subscribes_events"` | A reacts to events B publishes | `"domain"` |
| `"forwards_opaque_data"` | A carries data it never uses, only because B needs it for a third service | `"pass-through"` |
| `"shares_datastore"` | A and B both read and write the same shared data | `"common"` |
| `"reads_private_db"` | A reads B's private tables directly | `"content"` |
| `"writes_private_db"` | A changes B's private tables directly | `"content"` |

From loosest to tightest: `"none"` < `"domain"` < `"pass-through"` < `"common"` < `"content"`.

Unknown fact strings are ignored. With no recognised fact, return `"none"`.

**Example:** `["calls_api", "shares_datastore"]` → `"common"`

**Example:** `["subscribes_events"]` → `"domain"`
""",
    starter='''def classify_coupling(facts: List[str]) -> str:
    pass
''',
    solution='''def classify_coupling(facts):
    order = ["none", "domain", "pass-through", "common", "content"]
    kind = {
        "calls_api": "domain", "subscribes_events": "domain",
        "forwards_opaque_data": "pass-through",
        "shares_datastore": "common",
        "reads_private_db": "content", "writes_private_db": "content",
    }
    best = 0
    for f in facts:
        if f in kind:
            best = max(best, order.index(kind[f]))
    return order[best]
''',
    tests=[
        [["calls_api", "shares_datastore"]],
        [["subscribes_events"]],
        [[]],
        [["forwards_opaque_data", "calls_api"]],
        [["reads_private_db"]],
        [["writes_private_db", "shares_datastore", "calls_api"]],
        [["uses_same_language", "same_office"]],
        [["shares_datastore"]],
        [["forwards_opaque_data"]],
        [["calls_api", "calls_api", "subscribes_events"]],
        [["shares_datastore", "forwards_opaque_data"]],
        [["unknown", "reads_private_db", "calls_api"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def classify_coupling(facts):
    kind = {"calls_api": "domain", "subscribes_events": "domain", "forwards_opaque_data": "pass-through",
            "shares_datastore": "common", "reads_private_db": "content", "writes_private_db": "content"}
    for f in facts:
        if f in kind:
            return kind[f]
    return "none"
''',
        '''def classify_coupling(facts):
    if "shares_datastore" in facts:
        return "common"
    if "reads_private_db" in facts or "writes_private_db" in facts:
        return "content"
    if "forwards_opaque_data" in facts:
        return "pass-through"
    return "domain"
''',
    ],
    guide=dict(
        prereqs="The four coupling types from the lesson *Information hiding, coupling and cohesion*. Python lists and dictionaries.",
        intuition="Each fact maps to one coupling type, and the types form a ladder. The answer is the highest rung any fact reaches.",
        hints=[
            "Give every coupling name a number: none 0, domain 1, pass-through 2, common 3, content 4.",
            "Use a dictionary from fact string to coupling name, and skip facts that are not in it.",
            "Track the largest number seen and convert it back to a name at the end.",
        ],
        brute_force="Check for each type from tightest to loosest with a chain of `if` statements that scan the list. It works, at O(5n), but the order of the checks is easy to get wrong.",
        approach="Build `order` (a list of the five names) and `kind` (fact → name). Start `best = 0`. For each fact that is in `kind`, set `best = max(best, order.index(kind[fact]))`. Return `order[best]`.\n\n**Dry run** on `[\"calls_api\", \"shares_datastore\"]`: `calls_api` → domain → 1, so best = 1. `shares_datastore` → common → 3, so best = 3. Answer `order[3]` = `\"common\"`.",
        complexity="Time O(n) for n facts; space O(1) because the tables have a fixed size.",
        pitfalls="Returning the first fact's type instead of the tightest. Forgetting the empty list and the all-unknown list, which must give `\"none\"`. Ranking common above content.",
        follow_up="Extend the input to many service pairs and report the pairs with content coupling first, because those block independent deployment.",
    ),
),
dict(
    id="msvc-cohesion-score",
    title="Cohesion Score of a Proposed Split",
    difficulty="Easy",
    pattern="Coupling & Cohesion",
    entry="cohesion_score",
    compare="float",
    description=r"""
A good boundary keeps the code that changes together in the same service. You are given a proposed split and the change history, and must score the split.

- `services`: a dict mapping a service name to the list of function names it would own. A function belongs to at most one service.
- `changes`: a list of past changes; each change is the list of function names edited in that change.

For each change, look only at the functions that belong to some service (ignore the others, and count a repeated function once). A change with no such function is **skipped**. A counted change is **local** if all its functions belong to one single service.

Return `local changes / counted changes`, rounded to 4 decimal places. Return `0.0` if no change is counted.

**Example:** `services = {"booking": ["reserve", "cancel"], "billing": ["charge"]}`, `changes = [["reserve", "cancel"], ["reserve", "charge"], ["charge"], ["readme"]]` → 3 counted, 2 local → `0.6667`
""",
    starter='''def cohesion_score(services: Dict[str, List[str]], changes: List[List[str]]) -> float:
    pass
''',
    solution='''def cohesion_score(services, changes):
    owner = {}
    for svc, funcs in services.items():
        for f in funcs:
            owner[f] = svc
    counted = local = 0
    for change in changes:
        touched = {owner[f] for f in change if f in owner}
        if not touched:
            continue
        counted += 1
        if len(touched) == 1:
            local += 1
    return round(local / counted, 4) if counted else 0.0
''',
    tests=[
        [{"booking": ["reserve", "cancel"], "billing": ["charge"]}, [["reserve", "cancel"], ["reserve", "charge"], ["charge"], ["readme"]]],
        [{"a": ["f"], "b": ["g"]}, [["f"], ["g"], ["f", "g"], ["f", "g"]]],
        [{"a": ["f"]}, []],
        [{"a": ["f"]}, [["x"], ["y", "z"]]],
        [{}, [["f"]]],
        [{"a": ["f", "g", "h"]}, [["f", "g"], ["h"], ["f", "h", "zzz"]]],
        [{"a": ["f"], "b": ["g"], "c": ["h"]}, [["f", "g", "h"]]],
        [{"a": ["f"], "b": ["g"]}, [["f", "f", "f"], ["g", "unknown"]]],
        [{"a": ["f1", "f2"], "b": ["g1", "g2"]}, [["f1", "g1"], ["f2", "g2"], ["f1", "f2"]]],
        [{"a": ["f"], "b": ["g"]}, [[], ["f"], []]],
        [{"s%d" % i: ["fn%d" % i] for i in range(50)}, [["fn%d" % i, "fn%d" % ((i + 1) % 50)] for i in range(50)] + [["fn3"]] * 7],
    ],
    examples=2,
    wrong_solutions=[
        '''def cohesion_score(services, changes):
    owner = {f: s for s, fs in services.items() for f in fs}
    local = 0
    for change in changes:
        touched = {owner[f] for f in change if f in owner}
        if len(touched) == 1:
            local += 1
    return round(local / len(changes), 4) if changes else 0.0
''',
        '''def cohesion_score(services, changes):
    owner = {f: s for s, fs in services.items() for f in fs}
    counted = local = 0
    for change in changes:
        counted += 1
        touched = {owner.get(f) for f in change}
        if len(touched) == 1:
            local += 1
    return round(local / counted, 4) if counted else 0.0
''',
    ],
    guide=dict(
        prereqs="Cohesion from the lesson *Information hiding, coupling and cohesion*. Python sets and dictionary comprehensions.",
        intuition="Turn each change into the set of services it touches. One service means the split kept that change local; two or more means the change would need coordinated work across teams.",
        hints=[
            "Invert `services` into a dictionary from function name to owning service.",
            "For each change build a set of owners, skipping functions with no owner.",
            "Count the changes whose set is non-empty, and separately those whose set has exactly one element.",
        ],
        brute_force="For every change and every function, scan every service's list to find the owner: O(changes × functions × total functions). The inverted dictionary removes the inner scan.",
        approach="1. Build `owner`. 2. For each change compute `touched = {owner[f] for f in change if f in owner}`. 3. Skip empty sets; count the rest; count sets of size 1 as local. 4. Divide and round.\n\n**Dry run** on the example: `[reserve, cancel]` → {booking} local. `[reserve, charge]` → {booking, billing} not local. `[charge]` → {billing} local. `[readme]` → empty, skipped. Result 2/3 = 0.6667.",
        complexity="Time O(F + T) where F is the number of owned functions and T the total number of function names in the history. Space O(F).",
        pitfalls="Dividing by the number of all changes instead of the counted ones. Treating an unknown function as a separate service. Division by zero when nothing is counted.",
        follow_up="Try several candidate splits and pick the one with the best score. That is a crude version of how change history guides real boundary decisions.",
    ),
),
dict(
    id="msvc-bounded-contexts",
    title="Find Bounded Contexts by Shared Usage",
    difficulty="Medium",
    pattern="Domain-Driven Design",
    entry="find_contexts",
    description=r"""
You have a list of use cases. Each use case lists the entities (business nouns) it reads or changes. Group the entities into candidate bounded contexts with this deterministic rule:

1. Two different entities are **linked** if they appear together in at least `threshold` use cases. (An entity repeated inside one use case counts once for that use case.)
2. A context is a group of entities connected through links, directly or through other entities.
3. An entity with no link forms a context on its own.

Return the contexts as a list of lists. Sort the names inside each context, then sort the contexts by their first name.

`threshold` is at least 1.

**Example:** `usage = [["Slot", "Vet"], ["Slot", "Vet", "Invoice"], ["Invoice", "Payment"], ["Invoice", "Payment"]]`, `threshold = 2` → `[["Invoice", "Payment"], ["Slot", "Vet"]]`
""",
    starter='''def find_contexts(usage: List[List[str]], threshold: int) -> List[List[str]]:
    pass
''',
    solution='''def find_contexts(usage, threshold):
    from itertools import combinations
    parent = {}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    counts = {}
    for case in usage:
        names = sorted(set(case))
        for n in names:
            parent.setdefault(n, n)
        for a, b in combinations(names, 2):
            counts[(a, b)] = counts.get((a, b), 0) + 1
    for (a, b), c in counts.items():
        if c >= threshold:
            parent[find(a)] = find(b)
    groups = {}
    for n in parent:
        groups.setdefault(find(n), []).append(n)
    return sorted(sorted(g) for g in groups.values())
''',
    tests=[
        [[["Slot", "Vet"], ["Slot", "Vet", "Invoice"], ["Invoice", "Payment"], ["Invoice", "Payment"]], 2],
        [[["A", "B"], ["B", "C"], ["C", "D"]], 1],
        [[], 1],
        [[["A"]], 1],
        [[["A", "B"], ["A", "B"], ["B", "C"], ["B", "C"], ["D"]], 2],
        [[["A", "A", "B"]], 2],
        [[["A", "B", "C"], ["A", "B", "C"], ["A", "B", "C"]], 3],
        [[["A", "B", "C"], ["A", "B", "C"], ["A", "B", "C"]], 4],
        [[["Z", "Y"], ["Y", "Z"], ["X", "W"], ["W", "X"], ["X", "Y"]], 2],
        [[["A", "B"], ["C", "D"], ["B", "C"], ["A", "B"], ["C", "D"], ["B", "C"]], 2],
        [[["e%d" % i, "e%d" % (i + 1)] for i in range(0, 60, 2)] * 2 + [["e1", "e2"]], 2],
        [[["Pet", "Owner"], ["Pet", "Owner", "Slot"], ["Slot", "Room"], ["Slot", "Room"], ["Drug", "Stock"], ["Drug", "Stock", "Pet"], ["Pet", "Drug"]], 2],
    ],
    examples=1,
    wrong_solutions=[
        '''def find_contexts(usage, threshold):
    parent = {}
    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x
    for case in usage:
        names = sorted(set(case))
        for n in names:
            parent.setdefault(n, n)
        for a in names:
            for b in names:
                if a < b:
                    parent[find(a)] = find(b)
    groups = {}
    for n in parent:
        groups.setdefault(find(n), []).append(n)
    return sorted(sorted(g) for g in groups.values())
''',
        '''def find_contexts(usage, threshold):
    from itertools import combinations
    parent = {}
    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x
    counts = {}
    for case in usage:
        for n in case:
            parent.setdefault(n, n)
        for a, b in combinations(sorted(case), 2):
            counts[(a, b)] = counts.get((a, b), 0) + 1
    for (a, b), c in counts.items():
        if a != b and c >= threshold:
            parent[find(a)] = find(b)
    groups = {}
    for n in parent:
        groups.setdefault(find(n), []).append(n)
    return sorted(sorted(g) for g in groups.values())
''',
    ],
    guide=dict(
        prereqs="Bounded contexts from the lesson *Domain-driven design*. Connected components with union-find or a graph search.",
        intuition="Entities that keep appearing in the same use cases probably belong to the same part of the business. Count co-appearances, keep the strong pairs as edges, and read off the connected groups.",
        hints=[
            "Count each unordered pair once per use case. `itertools.combinations(sorted(set(case)), 2)` gives the pairs.",
            "Pairs whose count reaches the threshold are edges of a graph whose nodes are all entities.",
            "Find connected components with union-find, or with a depth-first search from every unvisited entity.",
        ],
        brute_force="For every pair of entities, scan all use cases to count co-appearances: O(E² × U). Then repeatedly merge groups that share a link until nothing changes. Correct but slow for many entities.",
        approach="1. For each use case remove duplicates, register each entity, and add 1 to the counter of each pair. 2. Union the two entities of every pair with count ≥ threshold. 3. Group entities by their root, sort inside and outside.\n\n**Dry run** on the example with threshold 2: pair counts are Slot–Vet 2, Slot–Invoice 1, Vet–Invoice 1, Invoice–Payment 2. Links: Slot–Vet and Invoice–Payment. Components: {Slot, Vet} and {Invoice, Payment}. Sorted output: `[[Invoice, Payment], [Slot, Vet]]`.",
        complexity="Time O(Σ k²) over use cases of size k for the pair counting, plus near-linear union-find. Space O(number of distinct pairs).",
        pitfalls="Counting a pair twice when an entity is repeated in a use case. Dropping entities that have no link. Forgetting that links are transitive: A–B and B–C put A and C together even if A and C never met.",
        follow_up="Real context discovery uses people and language, not only data. Treat the output as a conversation starter for an event-storming session.",
    ),
),
dict(
    id="msvc-distributed-monolith",
    title="Detect a Distributed Monolith",
    difficulty="Medium",
    pattern="Deployment Dependencies",
    entry="release_analysis",
    description=r"""
`requires` maps a service to the list of services that must be released **in the same release** whenever it is released (for example because they share a library version or a database schema). The relation is directed. Every name that appears anywhere, as a key or inside a list, is a service.

The **release set** of a service is itself plus everything reachable by following `requires`.

Return a dict with three keys:

- `"lockstep_groups"`: groups of two or more services that each require one another, directly or indirectly (each one is in the release set of every other one). Use the largest such groups. Sort the names in each group, then sort the groups.
- `"largest_release"`: the size of the biggest release set (0 if there are no services).
- `"verdict"`: `"distributed monolith"` if `largest_release` is more than half of the number of services, otherwise `"coupled"` if `largest_release` is greater than 1, otherwise `"independent"`.

**Example:** `{"web": ["api"], "api": ["web"], "mail": []}` → `{"lockstep_groups": [["api", "web"]], "largest_release": 2, "verdict": "distributed monolith"}` (2 is more than half of 3).
""",
    starter='''def release_analysis(requires: Dict[str, List[str]]) -> dict:
    pass
''',
    solution='''def release_analysis(requires):
    nodes = set(requires)
    for vs in requires.values():
        nodes.update(vs)
    reach = {}
    for s in nodes:
        seen = {s}
        stack = [s]
        while stack:
            x = stack.pop()
            for y in requires.get(x, []):
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        reach[s] = seen
    groups = set()
    for s in nodes:
        g = tuple(sorted(t for t in reach[s] if s in reach[t]))
        if len(g) >= 2:
            groups.add(g)
    largest = max((len(r) for r in reach.values()), default=0)
    if largest * 2 > len(nodes):
        verdict = "distributed monolith"
    elif largest > 1:
        verdict = "coupled"
    else:
        verdict = "independent"
    if not nodes:
        verdict = "independent"
    return {"lockstep_groups": sorted(list(g) for g in groups), "largest_release": largest, "verdict": verdict}
''',
    tests=[
        [{"web": ["api"], "api": ["web"], "mail": []}],
        [{"a": [], "b": [], "c": []}],
        [{}],
        [{"a": ["b"], "b": ["c"], "c": ["a"], "d": ["a"]}],
        [{"a": ["b"], "c": [], "d": [], "e": [], "f": []}],
        [{"a": ["b"], "b": ["c"], "c": ["d"]}],
        [{"a": ["b"], "b": ["a"], "c": ["d"], "d": ["c"], "e": [], "f": [], "g": [], "h": [], "i": []}],
        [{"a": ["a"]}],
        [{"a": ["b", "c"], "b": [], "c": [], "d": [], "e": [], "f": [], "g": []}],
        [{"x": ["shared"], "y": ["shared"], "z": ["shared"]}],
        [{"s%d" % i: ["s%d" % ((i + 1) % 30)] for i in range(30)}],
        [{"a": ["b"], "b": ["a", "c"], "c": ["d"], "d": ["c"], "e": []}],
    ],
    examples=1,
    wrong_solutions=[
        '''def release_analysis(requires):
    nodes = set(requires)
    for vs in requires.values():
        nodes.update(vs)
    groups = set()
    for a in nodes:
        for b in requires.get(a, []):
            if a != b and a in requires.get(b, []):
                groups.add(tuple(sorted((a, b))))
    largest = max((1 + len(set(requires.get(s, [])) - {s}) for s in nodes), default=0)
    verdict = "distributed monolith" if largest * 2 > len(nodes) else "coupled" if largest > 1 else "independent"
    if not nodes:
        verdict = "independent"
    return {"lockstep_groups": sorted(list(g) for g in groups), "largest_release": largest, "verdict": verdict}
''',
        '''def release_analysis(requires):
    nodes = set(requires)
    reach = {}
    for s in nodes:
        seen = {s}
        stack = [s]
        while stack:
            x = stack.pop()
            for y in requires.get(x, []):
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        reach[s] = seen
    groups = set()
    for s in nodes:
        g = tuple(sorted(t for t in reach[s] if t in reach and s in reach[t]))
        if len(g) >= 2:
            groups.add(g)
    largest = max((len(r) for r in reach.values()), default=0)
    verdict = "distributed monolith" if largest * 2 >= len(nodes) else "coupled" if largest > 1 else "independent"
    if not nodes:
        verdict = "independent"
    return {"lockstep_groups": sorted(list(g) for g in groups), "largest_release": largest, "verdict": verdict}
''',
    ],
    guide=dict(
        prereqs="The distributed monolith from the lesson *The monolith in its forms*. Graph reachability with depth-first search.",
        intuition="Independent deployability means a release set of size one. A lockstep group is a cycle of release requirements: a strongly connected component of the graph. When most of the system sits in one release set, you have a monolith that also pays network costs.",
        hints=[
            "Collect every service name first, including names that only appear inside the lists.",
            "Compute the set reachable from each service with a depth-first search.",
            "Two services are in the same lockstep group when each is in the other's reachable set.",
        ],
        brute_force="Pairwise reachability, as described, is already the straightforward method: O(V × (V + E)). It is fine for a few hundred services.",
        approach="1. `nodes` = keys plus listed names. 2. For each node run a DFS to get `reach[node]`. 3. For each node, its group is every `t` in `reach[s]` with `s` in `reach[t]`; keep groups of size ≥ 2 in a set to remove repeats. 4. `largest_release` is the largest reach size. 5. Compare with half of the node count.\n\n**Dry run** on the example: reach(web) = {web, api}, reach(api) = {api, web}, reach(mail) = {mail}. Group {api, web}. Largest 2; 2 × 2 > 3, so the verdict is `distributed monolith`.",
        complexity="Time O(V × (V + E)); space O(V²) for the reachability sets. Tarjan's algorithm finds the groups in O(V + E) if you need more speed.",
        pitfalls="Only detecting direct two-way pairs and missing longer cycles. Forgetting services that appear only as values. Using ≥ instead of > for the half rule. A self-requirement does not make a group of two.",
        follow_up="Weight the edges by how often two services were in fact released together, using real release history, to find accidental lockstep that nobody declared.",
    ),
),
dict(
    id="msvc-deploy-order",
    title="Safe Deployment Order with Cycle Detection",
    difficulty="Medium",
    pattern="Deployment Dependencies",
    entry="deploy_order",
    description=r"""
`deps` maps each service to the list of services that must be deployed **before** it. Every name that appears anywhere is a service.

Produce a deployment order in which every service comes after all of its dependencies. When several services are ready at the same time, deploy the alphabetically smallest first.

Some services may be impossible to deploy because they sit on a dependency cycle, or depend (directly or indirectly) on a service that does.

Return a dict:

- `"order"`: the deployable services, in deployment order.
- `"blocked"`: the services that can never be deployed, sorted alphabetically.

**Example:** `{"web": ["api"], "api": ["db"], "db": []}` → `{"order": ["db", "api", "web"], "blocked": []}`

**Example:** `{"a": ["b"], "b": ["a"], "c": []}` → `{"order": ["c"], "blocked": ["a", "b"]}`
""",
    starter='''def deploy_order(deps: Dict[str, List[str]]) -> dict:
    pass
''',
    solution='''def deploy_order(deps):
    import heapq
    nodes = set(deps)
    for vs in deps.values():
        nodes.update(vs)
    need = {n: set(deps.get(n, [])) for n in nodes}
    users = {n: [] for n in nodes}
    for n, ds in need.items():
        for d in ds:
            users[d].append(n)
    left = {n: len(ds) for n, ds in need.items()}
    heap = [n for n in nodes if left[n] == 0]
    heapq.heapify(heap)
    order = []
    while heap:
        n = heapq.heappop(heap)
        order.append(n)
        for u in users[n]:
            left[u] -= 1
            if left[u] == 0:
                heapq.heappush(heap, u)
    done = set(order)
    return {"order": order, "blocked": sorted(nodes - done)}
''',
    tests=[
        [{"web": ["api"], "api": ["db"], "db": []}],
        [{"a": ["b"], "b": ["a"], "c": []}],
        [{}],
        [{"solo": []}],
        [{"b": [], "a": [], "c": []}],
        [{"web": ["api", "auth"], "api": ["db"], "auth": ["db"]}],
        [{"a": ["a"]}],
        [{"a": ["b"], "b": ["c"], "c": ["a"], "d": ["c"], "e": []}],
        [{"z": [], "a": ["z"], "m": ["z"], "b": ["a", "m"]}],
        [{"a": ["b", "b"], "b": []}],
        [{"s%02d" % i: ["s%02d" % (i + 1)] for i in range(40)}],
        [{"x": ["y"], "y": ["x"], "p": ["q"], "q": [], "r": ["p", "x"]}],
    ],
    examples=2,
    wrong_solutions=[
        '''def deploy_order(deps):
    nodes = set(deps)
    for vs in deps.values():
        nodes.update(vs)
    order, seen = [], set()
    def visit(n, path):
        if n in seen or n in path:
            return
        for d in sorted(deps.get(n, [])):
            visit(d, path | {n})
        seen.add(n)
        order.append(n)
    for n in sorted(nodes):
        visit(n, set())
    return {"order": order, "blocked": []}
''',
        '''def deploy_order(deps):
    nodes = set(deps)
    for vs in deps.values():
        nodes.update(vs)
    left = {n: len(deps.get(n, [])) for n in nodes}
    ready = sorted(n for n in nodes if left[n] == 0)
    order = []
    while ready:
        n = ready.pop(0)
        order.append(n)
        for u in sorted(nodes):
            if n in deps.get(u, []):
                left[u] -= 1
                if left[u] == 0:
                    ready.append(u)
    return {"order": order, "blocked": sorted(nodes - set(order))}
''',
    ],
    guide=dict(
        prereqs="Deployment dependencies from the lesson *From logical to physical*. Topological sorting (Kahn's algorithm) and a heap.",
        intuition="A service is ready when all of its dependencies are already deployed. Keep taking the smallest ready service. Whatever never becomes ready is on a cycle or behind one.",
        hints=[
            "Count, for each service, how many distinct dependencies are still missing.",
            "Keep the ready services in a min-heap so the alphabetically smallest comes out first.",
            "After the loop, every service that was never popped is blocked.",
        ],
        brute_force="Repeat: scan all services, pick the smallest one whose dependencies are all deployed, deploy it. Stop when a scan finds none. O(V² + V·E).",
        approach="Kahn's algorithm. Build `need` (sets, so duplicates collapse), reverse lists `users`, and counters `left`. Push all zero-count services into a heap. Pop, append to the order, decrement the counter of each user, pushing users that reach zero.\n\n**Dry run** on `{web: [api, auth], api: [db], auth: [db]}`: counters web 2, api 1, auth 1, db 0. Pop db → api 0, auth 0. Pop api → web 1. Pop auth → web 0. Pop web. Order db, api, auth, web.",
        complexity="Time O((V + E) log V); space O(V + E).",
        pitfalls="A duplicated dependency such as `[\"b\", \"b\"]` must be counted once. A plain FIFO queue breaks the alphabetical tie rule. A service that depends on itself is blocked.",
        follow_up="If two services really must change together, the fix is to make the change backward compatible so each can be deployed alone. See the lesson on breaking changes.",
    ),
),
dict(
    id="msvc-strangler-routing",
    title="Strangler Fig Routing Table",
    difficulty="Easy",
    pattern="Migration",
    entry="route_requests",
    description=r"""
During a strangler fig migration a proxy in front of the old system decides, for every request path, whether the `"legacy"` monolith or a `"new"` service handles it.

- `phases` is a list. Phase `i` is a list of `[prefix, target]` entries added at that phase, where `target` is `"new"` or `"legacy"`.
- The routing table at phase `p` contains the entries of phases `0..p`. If the same prefix appears more than once, the latest entry wins. (This is how a migrated path is rolled back.)
- A prefix matches a path if the path equals the prefix, or starts with the prefix followed by `/`. The prefix `"/"` matches every path.
- The **longest** matching prefix decides. With no match, the answer is `"legacy"`.

Return the target for each path in `paths`, at phase `phase`.

**Example:** `phases = [[["/reminders", "new"]], [["/appointments", "new"], ["/appointments/export", "legacy"]]]`, `phase = 1`, `paths = ["/reminders/5", "/appointments/9", "/appointments/export", "/pets"]` → `["new", "new", "legacy", "legacy"]`
""",
    starter='''def route_requests(phases: List[List[List[str]]], phase: int, paths: List[str]) -> List[str]:
    pass
''',
    solution='''def route_requests(phases, phase, paths):
    table = {}
    for entries in phases[:phase + 1]:
        for prefix, target in entries:
            table[prefix] = target
    out = []
    for path in paths:
        best, target = -1, "legacy"
        for prefix, t in table.items():
            if prefix == "/" or path == prefix or path.startswith(prefix + "/"):
                if len(prefix) > best:
                    best, target = len(prefix), t
        out.append(target)
    return out
''',
    tests=[
        [[[["/reminders", "new"]], [["/appointments", "new"], ["/appointments/export", "legacy"]]], 1, ["/reminders/5", "/appointments/9", "/appointments/export", "/pets"]],
        [[[["/reminders", "new"]], [["/appointments", "new"]]], 0, ["/reminders", "/appointments/9"]],
        [[], 0, ["/anything"]],
        [[[["/pets", "new"]]], 0, ["/pets-old", "/pets", "/pets/1/visits", "/pet"]],
        [[[["/", "new"]], [["/billing", "legacy"]]], 1, ["/x", "/billing/2", "/billing", "/"]],
        [[[["/a", "new"]], [["/a", "legacy"]], [["/a", "new"]]], 1, ["/a/1"]],
        [[[["/a", "new"]], [["/a", "legacy"]], [["/a", "new"]]], 2, ["/a/1"]],
        [[[["/a/b/c", "new"], ["/a", "legacy"], ["/a/b", "new"]]], 0, ["/a/b/c/d", "/a/b/x", "/a/x", "/b"]],
        [[[["/a", "new"]]], 0, []],
        [[[["/a/b", "legacy"]], [["/a", "new"]]], 1, ["/a/b/c", "/a/c", "/a/b"]],
        [[[], [["/lab", "new"]], []], 2, ["/lab/results", "/labs"]],
        [[[["/p%d" % i, "new"]] for i in range(30)], 14, ["/p3/x", "/p14", "/p15", "/p29/y"]],
    ],
    examples=1,
    wrong_solutions=[
        '''def route_requests(phases, phase, paths):
    table = {}
    for entries in phases[:phase + 1]:
        for prefix, target in entries:
            table[prefix] = target
    out = []
    for path in paths:
        best, target = -1, "legacy"
        for prefix, t in table.items():
            if path.startswith(prefix) and len(prefix) > best:
                best, target = len(prefix), t
        out.append(target)
    return out
''',
        '''def route_requests(phases, phase, paths):
    out = []
    for path in paths:
        target = "legacy"
        for entries in phases[:phase + 1]:
            for prefix, t in entries:
                if prefix == "/" or path == prefix or path.startswith(prefix + "/"):
                    target = t
        out.append(target)
    return out
''',
    ],
    guide=dict(
        prereqs="The strangler fig pattern from the lesson *Migration patterns and splitting the data*. String prefixes.",
        intuition="The proxy holds a small table. Later phases add or override rows. A request follows the most specific row that matches it, and falls back to the old system otherwise.",
        hints=[
            "Build the table as a dictionary by walking phases `0..phase` in order, so later entries overwrite earlier ones.",
            "A prefix matches on a segment boundary: equal, or followed by a slash. Treat `\"/\"` as a special case.",
            "Among the matching prefixes keep the longest.",
        ],
        brute_force="For each path, walk every entry of every phase and remember the longest match, resolving overrides by hand. O(paths × entries). Building the dictionary first makes the override rule automatic.",
        approach="1. Merge phases into `table`. 2. For each path test each prefix with the boundary rule and keep the longest. 3. Default `legacy`.\n\n**Dry run** for `/appointments/export` at phase 1: `/appointments` matches (length 13) and `/appointments/export` matches (length 20). The longer one says `legacy`.",
        complexity="Time O(P × T × L) for P paths, T table rows and path length L; space O(T). A trie over path segments reduces it to O(P × L).",
        pitfalls="Plain `startswith` wrongly sends `/pets-old` to the `/pets` service. Forgetting that `phase` is inclusive. Letting the last matching entry win instead of the longest.",
        follow_up="Add a percentage to each entry so only part of the traffic for a prefix goes to the new service. That turns the proxy into a canary router.",
    ),
),
dict(
    id="msvc-schema-compat",
    title="Breaking or Non-breaking Schema Change",
    difficulty="Medium",
    pattern="API Evolution",
    entry="compare_schemas",
    description=r"""
Compare two versions of a message schema and classify every difference.

A schema is a dict: field name → `{"type": <string>, "required": <bool>}`. `direction` is `"response"` (the provider sends this message and consumers read it) or `"request"` (consumers send it and the provider reads it).

For each field that differs, report exactly one change:

| change | when | `response` | `request` |
|---|---|---|---|
| `"removed"` | in old, not in new | breaking | non-breaking |
| `"added"` | in new, not in old | non-breaking | breaking if the new field is required, otherwise non-breaking |
| `"type-changed"` | types differ (report this even if `required` also changed) | breaking | breaking |
| `"now-optional"` | same type, required → not required | breaking | non-breaking |
| `"now-required"` | same type, not required → required | non-breaking | breaking |

Return a list of `[field, change, verdict]` sorted by field name, where verdict is `"breaking"` or `"non-breaking"`. Unchanged fields are not listed.

**Example:** old `{"id": {"type": "int", "required": True}, "nick": {"type": "string", "required": False}}`, new `{"id": {"type": "string", "required": True}}`, direction `"response"` → `[["id", "type-changed", "breaking"], ["nick", "removed", "breaking"]]`
""",
    starter='''def compare_schemas(old: dict, new: dict, direction: str) -> List[List[str]]:
    pass
''',
    solution='''def compare_schemas(old, new, direction):
    resp = direction == "response"
    out = []
    for f in sorted(set(old) | set(new)):
        if f not in new:
            out.append([f, "removed", "breaking" if resp else "non-breaking"])
        elif f not in old:
            bad = (not resp) and new[f]["required"]
            out.append([f, "added", "breaking" if bad else "non-breaking"])
        elif old[f]["type"] != new[f]["type"]:
            out.append([f, "type-changed", "breaking"])
        elif old[f]["required"] and not new[f]["required"]:
            out.append([f, "now-optional", "breaking" if resp else "non-breaking"])
        elif new[f]["required"] and not old[f]["required"]:
            out.append([f, "now-required", "non-breaking" if resp else "breaking"])
    return out
''',
    tests=[
        [{"id": {"type": "int", "required": True}, "nick": {"type": "string", "required": False}}, {"id": {"type": "string", "required": True}}, "response"],
        [{"id": {"type": "int", "required": True}}, {"id": {"type": "int", "required": True}, "email": {"type": "string", "required": True}}, "request"],
        [{}, {}, "response"],
        [{"a": {"type": "int", "required": True}}, {"a": {"type": "int", "required": True}}, "request"],
        [{"id": {"type": "int", "required": True}}, {"id": {"type": "int", "required": True}, "email": {"type": "string", "required": True}}, "response"],
        [{"id": {"type": "int", "required": True}}, {"id": {"type": "int", "required": True}, "note": {"type": "string", "required": False}}, "request"],
        [{"a": {"type": "int", "required": True}, "b": {"type": "int", "required": False}}, {"a": {"type": "int", "required": False}, "b": {"type": "int", "required": True}}, "response"],
        [{"a": {"type": "int", "required": True}, "b": {"type": "int", "required": False}}, {"a": {"type": "int", "required": False}, "b": {"type": "int", "required": True}}, "request"],
        [{"z": {"type": "int", "required": True}, "a": {"type": "int", "required": True}}, {}, "request"],
        [{"z": {"type": "int", "required": True}, "a": {"type": "int", "required": True}}, {}, "response"],
        [{"a": {"type": "int", "required": True}}, {"a": {"type": "float", "required": False}}, "request"],
        [{}, {"m": {"type": "bool", "required": False}, "k": {"type": "bool", "required": True}}, "request"],
    ],
    examples=2,
    wrong_solutions=[
        '''def compare_schemas(old, new, direction):
    out = []
    for f in sorted(set(old) | set(new)):
        if f not in new:
            out.append([f, "removed", "breaking"])
        elif f not in old:
            out.append([f, "added", "non-breaking"])
        elif old[f]["type"] != new[f]["type"]:
            out.append([f, "type-changed", "breaking"])
        elif old[f]["required"] and not new[f]["required"]:
            out.append([f, "now-optional", "breaking"])
        elif new[f]["required"] and not old[f]["required"]:
            out.append([f, "now-required", "non-breaking"])
    return out
''',
        '''def compare_schemas(old, new, direction):
    resp = direction == "response"
    out = []
    for f in sorted(set(old) | set(new)):
        if f not in new:
            out.append([f, "removed", "breaking" if resp else "non-breaking"])
        elif f not in old:
            out.append([f, "added", "non-breaking" if resp else "breaking"])
        elif old[f]["required"] and not new[f]["required"]:
            out.append([f, "now-optional", "breaking" if resp else "non-breaking"])
        elif new[f]["required"] and not old[f]["required"]:
            out.append([f, "now-required", "non-breaking" if resp else "breaking"])
        elif old[f]["type"] != new[f]["type"]:
            out.append([f, "type-changed", "breaking"])
    return out
''',
    ],
    guide=dict(
        prereqs="Breaking changes from the lesson *Handling change*. Python dictionaries and sets.",
        intuition="Ask who reads the message. A reader breaks when something it relies on disappears or changes shape. For a response the reader is the consumer; for a request the reader is the provider, and the old consumers are the writers who do not know about new demands.",
        hints=[
            "Walk the sorted union of the field names of both versions.",
            "Decide the change name first (removed, added, type-changed, now-optional, now-required), checking the type before the required flag.",
            "Then look up the verdict for the direction. Only `type-changed` has the same verdict in both directions.",
        ],
        brute_force="There is no meaningfully slower method; the risk is in the rules, not in the speed. Writing one `if` per row of the table is the clearest version.",
        approach="For each field in the sorted union: missing in new → removed; missing in old → added; different type → type-changed; then compare the required flags. Map to the verdict with `resp = direction == \"response\"`.\n\n**Dry run** on the first example: `id` exists in both with types int and string → type-changed, breaking. `nick` is missing in new → removed; for a response that is breaking.",
        complexity="Time O(n log n) for the sort over n distinct field names; space O(n).",
        pitfalls="Using the same verdicts for both directions. Reporting `now-optional` when the type changed as well. Treating an added optional request field as breaking.",
        follow_up="Add nested objects and enumerations: adding an enumeration value to a response is breaking for consumers that switch on it.",
    ),
),
dict(
    id="msvc-semver-bump",
    title="Semantic Version Bump for an API Change",
    difficulty="Easy",
    pattern="API Evolution",
    entry="next_version",
    description=r"""
A version has the form `"MAJOR.MINOR.PATCH"` with non-negative integers. `changes` is a list whose items are `"breaking"`, `"feature"` or `"fix"`. Return the next version.

**When MAJOR is 1 or more:**

- any `"breaking"` → MAJOR + 1, MINOR = 0, PATCH = 0
- otherwise any `"feature"` → MINOR + 1, PATCH = 0
- otherwise any `"fix"` → PATCH + 1

**When MAJOR is 0** (the API is still unstable, so the major number is kept at 0):

- any `"breaking"` → MINOR + 1, PATCH = 0
- otherwise any `"feature"` or `"fix"` → PATCH + 1

An empty list, or a list with only unknown strings, leaves the version unchanged.

**Example:** `"2.4.7", ["fix", "feature"]` → `"2.5.0"`

**Example:** `"0.3.1", ["breaking"]` → `"0.4.0"`
""",
    starter='''def next_version(current: str, changes: List[str]) -> str:
    pass
''',
    solution='''def next_version(current, changes):
    major, minor, patch = (int(x) for x in current.split("."))
    kinds = set(changes)
    if major >= 1:
        if "breaking" in kinds:
            major, minor, patch = major + 1, 0, 0
        elif "feature" in kinds:
            minor, patch = minor + 1, 0
        elif "fix" in kinds:
            patch += 1
    else:
        if "breaking" in kinds:
            minor, patch = minor + 1, 0
        elif "feature" in kinds or "fix" in kinds:
            patch += 1
    return "%d.%d.%d" % (major, minor, patch)
''',
    tests=[
        ["2.4.7", ["fix", "feature"]],
        ["0.3.1", ["breaking"]],
        ["1.0.0", []],
        ["1.9.9", ["breaking", "fix"]],
        ["1.9.9", ["fix"]],
        ["0.0.0", ["feature"]],
        ["0.0.9", ["fix", "fix"]],
        ["10.20.30", ["feature", "feature"]],
        ["3.2.1", ["typo"]],
        ["0.9.9", ["feature", "breaking"]],
        ["1.0.9", ["fix", "fix", "fix"]],
        ["9.9.9", ["breaking"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def next_version(current, changes):
    major, minor, patch = (int(x) for x in current.split("."))
    if "breaking" in changes:
        major += 1
    elif "feature" in changes:
        minor += 1
    elif "fix" in changes:
        patch += 1
    return "%d.%d.%d" % (major, minor, patch)
''',
        '''def next_version(current, changes):
    major, minor, patch = (int(x) for x in current.split("."))
    for c in changes:
        if c == "breaking":
            major, minor, patch = major + 1, 0, 0
        elif c == "feature":
            minor, patch = minor + 1, 0
        elif c == "fix":
            patch += 1
    return "%d.%d.%d" % (major, minor, patch)
''',
    ],
    guide=dict(
        prereqs="Semantic versioning from the lesson *Handling change*. String splitting and integer conversion.",
        intuition="Only the most severe change in the release decides the bump, and a bump resets every number to its right to zero.",
        hints=[
            "Split on dots and convert the three parts to integers.",
            "Check for the most severe change first, with `in`.",
            "Handle `major == 0` as a separate branch with its own two rules.",
        ],
        brute_force="Apply a bump for every change in the list one after another. This is wrong, not only slow: two fixes would bump the patch twice, and a fix after a feature would move away from `x.y.0`.",
        approach="Parse, turn `changes` into a set, branch on `major >= 1`, test `breaking`, then `feature`, then `fix`, and format with dots.\n\n**Dry run** for `2.4.7` with `[fix, feature]`: major is 2; no breaking; a feature exists → minor 5, patch 0 → `2.5.0`.",
        complexity="Time O(n) to build the set; space O(1) beyond it.",
        pitfalls="Forgetting to reset the lower numbers. Bumping once per change. Comparing version strings as text (`\"10\" < \"9\"`).",
        follow_up="Combine with the schema comparison problem: derive the list of change kinds from two schema versions automatically.",
    ),
),
]
