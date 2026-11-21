PROBLEMS = [
dict(
    id="k8s-label-selector",
    title="Label Selector Matching",
    difficulty="Easy",
    pattern="Labels & Selectors",
    entry="selectObjects",
    description=r"""
Controllers and Services find their Pods with **label selectors**. Write `selectObjects(objects, selector)` that returns
the names of the objects matched by the selector, **in input order**.

- Each object is `{"name": str, "labels": {key: value}}`.
- `selector` may contain `matchLabels` (a dict) and `matchExpressions` (a list). Either may be missing.
- `matchLabels`: every listed key must be present with exactly that value.
- Each expression is `{"key": k, "operator": op, "values": [...]}` with `op` one of:

| Operator | Matches when |
|---|---|
| `In` | the object has the key and its value is in `values` |
| `NotIn` | the object does **not** have the key, or its value is not in `values` |
| `Exists` | the object has the key (any value) |
| `DoesNotExist` | the object does not have the key |

All requirements must hold (logical AND). A selector with no requirements matches every object.

**Example:** objects `a{env:prod}`, `b{env:dev}`, `c{}` with
`{"matchExpressions": [{"key": "env", "operator": "NotIn", "values": ["dev"]}]}` → `["a", "c"]`
""",
    starter='''def selectObjects(objects, selector):
    # return the list of matching object names, in input order
    pass
''',
    solution='''def selectObjects(objects, selector):
    match_labels = selector.get("matchLabels") or {}
    expressions = selector.get("matchExpressions") or []

    def ok(labels):
        for k, v in match_labels.items():
            if labels.get(k) != v:
                return False
        for e in expressions:
            key, op, values = e["key"], e["operator"], e.get("values") or []
            has = key in labels
            if op == "In":
                if not (has and labels[key] in values):
                    return False
            elif op == "NotIn":
                if has and labels[key] in values:
                    return False
            elif op == "Exists":
                if not has:
                    return False
            elif op == "DoesNotExist":
                if has:
                    return False
        return True

    return [o["name"] for o in objects if ok(o.get("labels") or {})]
''',
    tests=[
        [[{"name": "a", "labels": {"env": "prod"}}, {"name": "b", "labels": {"env": "dev"}}, {"name": "c", "labels": {}}],
         {"matchExpressions": [{"key": "env", "operator": "NotIn", "values": ["dev"]}]}],
        [[{"name": "a", "labels": {"app": "web", "tier": "fe"}}, {"name": "b", "labels": {"app": "web"}}],
         {"matchLabels": {"app": "web", "tier": "fe"}}],
        [[{"name": "a", "labels": {"app": "web"}}, {"name": "b", "labels": {}}], {}],
        [[], {"matchLabels": {"app": "web"}}],
        [[{"name": "a", "labels": {"env": "prod"}}, {"name": "b", "labels": {"env": "staging"}}, {"name": "c", "labels": {"env": "dev"}}],
         {"matchExpressions": [{"key": "env", "operator": "In", "values": ["prod", "staging"]}]}],
        [[{"name": "a", "labels": {"canary": "true"}}, {"name": "b", "labels": {"app": "x"}}],
         {"matchExpressions": [{"key": "canary", "operator": "Exists"}]}],
        [[{"name": "a", "labels": {"canary": ""}}, {"name": "b", "labels": {"app": "x"}}],
         {"matchExpressions": [{"key": "canary", "operator": "DoesNotExist"}]}],
        [[{"name": "a", "labels": {"env": "prod", "canary": "1"}}, {"name": "b", "labels": {"env": "prod"}}, {"name": "c", "labels": {"env": "dev"}}],
         {"matchLabels": {"env": "prod"}, "matchExpressions": [{"key": "canary", "operator": "DoesNotExist"}]}],
        [[{"name": "a", "labels": {"env": "prod"}}, {"name": "b", "labels": {}}],
         {"matchExpressions": [{"key": "env", "operator": "In", "values": []}]}],
        [[{"name": "a", "labels": {"app": "menu-api"}}, {"name": "b", "labels": {"app": "menu_api"}}],
         {"matchLabels": {"app": "menu-api"}}],
        [[{"name": "z", "labels": {"x": "1"}}, {"name": "y", "labels": {"x": "1"}}, {"name": "x", "labels": {"x": "2"}}],
         {"matchExpressions": [{"key": "x", "operator": "NotIn", "values": ["2", "3"]}, {"key": "x", "operator": "Exists"}]}],
        [[{"name": "p%d" % i, "labels": {"zone": "z%d" % (i % 3), "n": str(i)}} for i in range(300)],
         {"matchLabels": {"zone": "z1"}, "matchExpressions": [{"key": "n", "operator": "NotIn", "values": ["1", "4"]}]}],
    ],
    examples=2,
    wrong_solutions=[
        '''def selectObjects(objects, selector):
    match_labels = selector.get("matchLabels") or {}
    expressions = selector.get("matchExpressions") or []
    out = []
    for o in objects:
        labels = o.get("labels") or {}
        good = all(labels.get(k) == v for k, v in match_labels.items())
        for e in expressions:
            key, op, values = e["key"], e["operator"], e.get("values") or []
            if op == "In" and labels.get(key) not in values:
                good = False
            if op == "NotIn" and (key not in labels or labels[key] in values):
                good = False
            if op == "Exists" and key not in labels:
                good = False
            if op == "DoesNotExist" and key in labels:
                good = False
        if good:
            out.append(o["name"])
    return out
''',
    ],
    guide=dict(
        prereqs="Labels and selectors from the lesson *The declarative model and reconciliation loops*. Python dicts and loops.",
        intuition="A selector is a list of small yes/no tests on a label map. An object matches when every test passes. The only "
                  "subtle test is `NotIn`, which is also satisfied when the key is absent.",
        hints=[
            "Write a helper `matches(labels)` that returns False as soon as one requirement fails and True at the end.",
            "For each expression, first compute `has = key in labels`. Every operator can be written in terms of `has` and `labels[key] in values`.",
            "`NotIn` fails only when the key is present **and** its value is in the list. A missing key passes.",
        ],
        brute_force="There is nothing cheaper than checking every object against every requirement: O(objects × requirements). "
                    "That is already the intended solution.",
        approach="1. Read `matchLabels` and `matchExpressions`, treating a missing field as empty.\n"
                 "2. For each object, test all `matchLabels` pairs with `labels.get(k) == v`.\n"
                 "3. Test each expression by operator.\n"
                 "4. Keep the names that pass, preserving order.\n\n"
                 "**Dry run** with `a{env:prod}`, `b{env:dev}`, `c{}` and `env NotIn [dev]`: `a` has the key with value `prod`, "
                 "not in the list → pass. `b` has `dev` → fail. `c` lacks the key → pass. Result `[a, c]`.",
        complexity="Time O(n · r) for n objects and r requirements (value lists are short). Space O(1) beyond the output.",
        pitfalls="- Treating a missing key as a failure for `NotIn`.\n- Using `labels.get(key)` for `Exists`: a label may legitimately "
                 "have an empty string value, and it still exists.\n- Returning a sorted list instead of input order.\n"
                 "- An empty selector must match everything, not nothing.",
        follow_up="Kubernetes also accepts a string form such as `env in (prod,staging),!canary`. Try writing a parser that turns "
                  "it into this structure.",
    ),
),
dict(
    id="k8s-reconcile-replicas",
    title="Reconcile Desired and Actual Replicas",
    difficulty="Easy",
    pattern="Reconciliation",
    entry="reconcile",
    description=r"""
A ReplicaSet controller compares the desired replica count with the Pods that exist and decides what to do.
Write `reconcile(desired, pods)`.

Each Pod is `{"name": str, "phase": str, "created": int}` where `phase` is one of `Pending`, `Running`, `Succeeded`,
`Failed` and `created` is a timestamp (bigger = newer).

- Only Pods in phase `Pending` or `Running` are **active**. Finished Pods are ignored.
- If there are fewer active Pods than `desired`, return `{"create": n, "delete": []}` where `n` is the shortfall.
- If there are more, return `{"create": 0, "delete": [names]}` listing the excess Pods **in deletion order**:
  `Pending` Pods before `Running` Pods; within the same phase, **newest first**; ties broken by name ascending.
- If the counts match, return `{"create": 0, "delete": []}`.

**Example:** `desired = 2`, Pods `a(Running,1)`, `b(Running,5)`, `c(Pending,3)`, `d(Failed,9)` → three active, one too many
→ `{"create": 0, "delete": ["c"]}` (the Pending Pod goes first).
""",
    starter='''def reconcile(desired, pods):
    # return {"create": int, "delete": [names]}
    pass
''',
    solution='''def reconcile(desired, pods):
    active = [p for p in pods if p["phase"] in ("Pending", "Running")]
    diff = desired - len(active)
    if diff >= 0:
        return {"create": diff, "delete": []}
    ranked = sorted(active, key=lambda p: (0 if p["phase"] == "Pending" else 1, -p["created"], p["name"]))
    return {"create": 0, "delete": [p["name"] for p in ranked[:-diff]]}
''',
    tests=[
        [2, [{"name": "a", "phase": "Running", "created": 1}, {"name": "b", "phase": "Running", "created": 5},
             {"name": "c", "phase": "Pending", "created": 3}, {"name": "d", "phase": "Failed", "created": 9}]],
        [3, []],
        [0, []],
        [3, [{"name": "a", "phase": "Running", "created": 1}]],
        [1, [{"name": "a", "phase": "Running", "created": 1}]],
        [0, [{"name": "a", "phase": "Running", "created": 1}, {"name": "b", "phase": "Pending", "created": 2}]],
        [1, [{"name": "a", "phase": "Running", "created": 4}, {"name": "b", "phase": "Running", "created": 9},
             {"name": "c", "phase": "Running", "created": 6}]],
        [1, [{"name": "b", "phase": "Running", "created": 7}, {"name": "a", "phase": "Running", "created": 7},
             {"name": "c", "phase": "Running", "created": 7}]],
        [2, [{"name": "a", "phase": "Succeeded", "created": 1}, {"name": "b", "phase": "Failed", "created": 2}]],
        [2, [{"name": "a", "phase": "Running", "created": 10}, {"name": "b", "phase": "Pending", "created": 1},
             {"name": "c", "phase": "Pending", "created": 2}, {"name": "d", "phase": "Running", "created": 20}]],
        [1, [{"name": "old", "phase": "Pending", "created": 1}, {"name": "new", "phase": "Running", "created": 99}]],
        [50, [{"name": "p%03d" % i, "phase": "Running" if i % 4 else "Pending", "created": (i * 37) % 101} for i in range(120)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def reconcile(desired, pods):
    diff = desired - len(pods)
    if diff >= 0:
        return {"create": diff, "delete": []}
    ranked = sorted(pods, key=lambda p: (0 if p["phase"] == "Pending" else 1, -p["created"], p["name"]))
    return {"create": 0, "delete": [p["name"] for p in ranked[:-diff]]}
''',
        '''def reconcile(desired, pods):
    active = [p for p in pods if p["phase"] in ("Pending", "Running")]
    diff = desired - len(active)
    if diff >= 0:
        return {"create": diff, "delete": []}
    ranked = sorted(active, key=lambda p: (p["created"], p["name"]))
    return {"create": 0, "delete": [p["name"] for p in ranked[:-diff]]}
''',
    ],
    guide=dict(
        prereqs="The reconciliation loop from *What orchestration solves* and *The declarative model*. Sorting with a key function.",
        intuition="The controller does not care why the count is wrong. It counts the Pods that still matter, subtracts, and either "
                  "asks for more or picks victims. Victim choice is a sort: least valuable first.",
        hints=[
            "Filter first: `Succeeded` and `Failed` Pods do not count towards the replica total.",
            "When there are too many, sort the active Pods so the ones to delete come first, then slice off the excess.",
            "A sort key of `(is_running, -created, name)` gives Pending before Running, newest first, then name.",
        ],
        brute_force="Repeatedly scan for the single best Pod to delete until the count is right: O(k · n) for k deletions. "
                    "One sort does the same in O(n log n).",
        approach="1. `active` = Pods with phase Pending or Running.\n2. `diff = desired - len(active)`.\n"
                 "3. `diff >= 0` → create `diff`, delete nothing.\n4. Otherwise sort active by `(phase rank, -created, name)` and "
                 "take the first `-diff` names.\n\n"
                 "**Dry run** (example): active = a, b, c; diff = 2 − 3 = −1. Sorted: c (Pending), b (Running, 5), a (Running, 1). "
                 "Take one → `[c]`.",
        complexity="Time O(n log n) for the sort, space O(n).",
        pitfalls="- Counting finished Pods as replicas.\n- Deleting the oldest Pods instead of the newest.\n"
                 "- Forgetting the name tie-break, which makes the result depend on input order.\n- Returning a negative `create`.",
        follow_up="The real controller also prefers to delete Pods that are not ready, and Pods on nodes holding more replicas. "
                  "Extend the sort key with a `ready` flag and a per-node count.",
    ),
),
dict(
    id="k8s-owner-chain",
    title="Resolve the Ownership Chain",
    difficulty="Easy",
    pattern="Deployments",
    entry="ownerChain",
    description=r"""
Kubernetes records which object created which through **owner references**: a Pod points to its ReplicaSet, which points
to its Deployment. Write `ownerChain(objects, kind, name)` that walks upward from one object to the top.

- `objects` is a list of `{"kind": str, "name": str, "owner": [kind, name] or None}`. `(kind, name)` pairs are unique.
- Return a list of strings `"Kind/name"`, starting with the given object and ending with the top-level owner.
- If the starting object is not in `objects`, return `[]`.
- If an owner reference points to an object that is not in `objects`, append `"Kind/name (missing)"` and stop.
- If following owners would visit an object a second time (a cycle), stop without adding it again.

**Example:** Pod `web-abc` → ReplicaSet `web-7d9` → Deployment `web`
→ `["Pod/web-abc", "ReplicaSet/web-7d9", "Deployment/web"]`
""",
    starter='''def ownerChain(objects, kind, name):
    # return ["Kind/name", ...] from the object up to its top-level owner
    pass
''',
    solution='''def ownerChain(objects, kind, name):
    index = {(o["kind"], o["name"]): o for o in objects}
    key = (kind, name)
    if key not in index:
        return []
    chain, seen = [], set()
    while True:
        chain.append(key[0] + "/" + key[1])
        seen.add(key)
        owner = index[key].get("owner")
        if not owner:
            return chain
        owner = (owner[0], owner[1])
        if owner in seen:
            return chain
        if owner not in index:
            chain.append(owner[0] + "/" + owner[1] + " (missing)")
            return chain
        key = owner
''',
    tests=[
        [[{"kind": "Deployment", "name": "web", "owner": None},
          {"kind": "ReplicaSet", "name": "web-7d9", "owner": ["Deployment", "web"]},
          {"kind": "Pod", "name": "web-abc", "owner": ["ReplicaSet", "web-7d9"]}], "Pod", "web-abc"],
        [[{"kind": "Pod", "name": "debug", "owner": None}], "Pod", "debug"],
        [[{"kind": "Pod", "name": "debug", "owner": None}], "Pod", "nope"],
        [[], "Pod", "x"],
        [[{"kind": "Pod", "name": "orphan", "owner": ["ReplicaSet", "gone"]}], "Pod", "orphan"],
        [[{"kind": "CronJob", "name": "nightly", "owner": None},
          {"kind": "Job", "name": "nightly-1", "owner": ["CronJob", "nightly"]},
          {"kind": "Pod", "name": "nightly-1-x", "owner": ["Job", "nightly-1"]}], "Job", "nightly-1"],
        [[{"kind": "Deployment", "name": "web", "owner": None},
          {"kind": "ReplicaSet", "name": "web", "owner": ["Deployment", "web"]},
          {"kind": "Pod", "name": "web", "owner": ["ReplicaSet", "web"]}], "Pod", "web"],
        [[{"kind": "A", "name": "x", "owner": ["B", "y"]}, {"kind": "B", "name": "y", "owner": ["A", "x"]}], "A", "x"],
        [[{"kind": "A", "name": "self", "owner": ["A", "self"]}], "A", "self"],
        [[{"kind": "StatefulSet", "name": "db", "owner": ["Cluster", "db"]},
          {"kind": "Pod", "name": "db-0", "owner": ["StatefulSet", "db"]}], "Pod", "db-0"],
        [[{"kind": "Deployment", "name": "web", "owner": None},
          {"kind": "ReplicaSet", "name": "web-7d9", "owner": ["Deployment", "web"]}], "Deployment", "web"],
        [[{"kind": "K", "name": "n%d" % i, "owner": (["K", "n%d" % (i + 1)] if i < 199 else None)} for i in range(200)], "K", "n0"],
    ],
    examples=2,
    wrong_solutions=[
        '''def ownerChain(objects, kind, name):
    index = {(o["kind"], o["name"]): o for o in objects}
    key = (kind, name)
    chain = []
    while key in index and len(chain) < 1000:
        chain.append(key[0] + "/" + key[1])
        owner = index[key].get("owner")
        if not owner:
            break
        key = (owner[0], owner[1])
    return chain
''',
    ],
    guide=dict(
        prereqs="Owner references and garbage collection from *The declarative model* and *Deployments, ReplicaSets, self-healing and scaling*.",
        intuition="Each object has at most one arrow pointing to its owner. Following arrows is walking a linked list. The work is "
                  "in the three ways the walk can end: no owner, a missing owner, or a loop.",
        hints=[
            "Build a dictionary from `(kind, name)` to the object so each step is one lookup.",
            "Keep a set of visited keys. Check it before moving to the owner.",
            "Order of checks at each step: no owner → stop; owner already seen → stop; owner not in the index → add the `(missing)` entry and stop.",
        ],
        brute_force="Scan the whole list to find each owner: O(n) per step and O(n²) for a long chain. Indexing first makes each step O(1).",
        approach="1. Index objects by `(kind, name)`.\n2. If the start is absent return `[]`.\n3. Loop: append the current key, mark it "
                 "seen, read its owner, and decide whether to stop or continue.\n\n"
                 "**Dry run:** start `Pod/web-abc` → append, owner `ReplicaSet/web-7d9` exists → move. Append, owner "
                 "`Deployment/web` exists → move. Append, owner is None → return the three entries.",
        complexity="Time O(n) to index plus O(length of chain). Space O(n).",
        pitfalls="- Indexing by name only: a Pod, ReplicaSet and Deployment can share a name.\n- Looping forever on a cycle.\n"
                 "- Silently dropping a dangling owner instead of reporting it.\n- Returning `None` for an unknown start.",
        follow_up="Real objects may list several owners with one marked `controller: true`. How would you choose which arrow to follow?",
    ),
),
dict(
    id="k8s-service-endpoints",
    title="Which Pods Back a Service?",
    difficulty="Easy",
    pattern="Services",
    entry="serviceEndpoints",
    description=r"""
The EndpointSlice controller turns a Service's selector into a list of Pod addresses. Write
`serviceEndpoints(service, pods)` returning `[ready, notReady]`, two lists of `"ip:port"` strings, each sorted
in ascending string order.

- `service` is `{"namespace": str, "selector": {key: value}, "targetPort": int or str}`.
- Each Pod is `{"name", "namespace", "labels", "ip", "ready", "ports"}` where `ip` is a string or `None`,
  `ready` is a boolean and `ports` maps port names to numbers.

A Pod is an endpoint when **all** of these hold:

1. it is in the Service's namespace;
2. it has every label in the selector with the same value;
3. it has an IP address (`ip` is not `None`);
4. if `targetPort` is a string, the Pod has a port with that name (that port's number is used). A number is used as is.

If the selector is empty, the Service has no automatically managed endpoints: return `[[], []]`.
Ready Pods go in the first list, others in the second.

**Example:** selector `{app: api}`, targetPort `"http"`; Pods `10.0.0.5` (ready, `http=8080`) and `10.0.0.6` (not ready,
`http=8080`) → `[["10.0.0.5:8080"], ["10.0.0.6:8080"]]`
""",
    starter='''def serviceEndpoints(service, pods):
    # return [ready, notReady], each a sorted list of "ip:port"
    pass
''',
    solution='''def serviceEndpoints(service, pods):
    selector = service.get("selector") or {}
    ready, not_ready = [], []
    if not selector:
        return [ready, not_ready]
    target = service["targetPort"]
    for p in pods:
        if p["namespace"] != service["namespace"]:
            continue
        labels = p.get("labels") or {}
        if any(labels.get(k) != v for k, v in selector.items()):
            continue
        if p.get("ip") is None:
            continue
        port = target
        if isinstance(target, str):
            port = (p.get("ports") or {}).get(target)
            if port is None:
                continue
        (ready if p.get("ready") else not_ready).append("%s:%d" % (p["ip"], port))
    return [sorted(ready), sorted(not_ready)]
''',
    tests=[
        [{"namespace": "cafe", "selector": {"app": "api"}, "targetPort": "http"},
         [{"name": "a", "namespace": "cafe", "labels": {"app": "api"}, "ip": "10.0.0.5", "ready": True, "ports": {"http": 8080}},
          {"name": "b", "namespace": "cafe", "labels": {"app": "api"}, "ip": "10.0.0.6", "ready": False, "ports": {"http": 8080}}]],
        [{"namespace": "cafe", "selector": {"app": "api"}, "targetPort": 9000},
         [{"name": "a", "namespace": "cafe", "labels": {"app": "api"}, "ip": "10.0.0.5", "ready": True, "ports": {}}]],
        [{"namespace": "cafe", "selector": {}, "targetPort": 80},
         [{"name": "a", "namespace": "cafe", "labels": {"app": "api"}, "ip": "10.0.0.5", "ready": True, "ports": {}}]],
        [{"namespace": "cafe", "selector": {"app": "api"}, "targetPort": 80}, []],
        [{"namespace": "cafe", "selector": {"app": "api"}, "targetPort": 80},
         [{"name": "a", "namespace": "staging", "labels": {"app": "api"}, "ip": "10.0.0.5", "ready": True, "ports": {}}]],
        [{"namespace": "cafe", "selector": {"app": "api"}, "targetPort": 80},
         [{"name": "a", "namespace": "cafe", "labels": {"app": "api"}, "ip": None, "ready": False, "ports": {}}]],
        [{"namespace": "cafe", "selector": {"app": "api"}, "targetPort": "web"},
         [{"name": "a", "namespace": "cafe", "labels": {"app": "api"}, "ip": "10.0.0.5", "ready": True, "ports": {"http": 8080}},
          {"name": "b", "namespace": "cafe", "labels": {"app": "api"}, "ip": "10.0.0.7", "ready": True, "ports": {"web": 3000}}]],
        [{"namespace": "cafe", "selector": {"app": "api", "tier": "be"}, "targetPort": 80},
         [{"name": "a", "namespace": "cafe", "labels": {"app": "api"}, "ip": "10.0.0.5", "ready": True, "ports": {}},
          {"name": "b", "namespace": "cafe", "labels": {"app": "api", "tier": "be", "x": "y"}, "ip": "10.0.0.6", "ready": True, "ports": {}}]],
        [{"namespace": "cafe", "selector": {"app": "menu-api"}, "targetPort": 80},
         [{"name": "a", "namespace": "cafe", "labels": {"app": "menu_api"}, "ip": "10.0.0.5", "ready": True, "ports": {}}]],
        [{"namespace": "cafe", "selector": {"tier": "be"}, "targetPort": "http"},
         [{"name": "a", "namespace": "cafe", "labels": {"tier": "be"}, "ip": "10.0.0.9", "ready": True, "ports": {"http": 8080}},
          {"name": "b", "namespace": "cafe", "labels": {"tier": "be"}, "ip": "10.0.0.10", "ready": True, "ports": {"http": 9090}},
          {"name": "c", "namespace": "cafe", "labels": {"tier": "be"}, "ip": "10.0.0.2", "ready": False, "ports": {"http": 8080}}]],
        [{"namespace": "n", "selector": {"app": "x"}, "targetPort": "p"},
         [{"name": "p%d" % i, "namespace": "n" if i % 2 else "m", "labels": {"app": "x" if i % 3 else "y"},
           "ip": None if i % 7 == 0 else "10.1.%d.%d" % (i // 250, i % 250), "ready": i % 5 != 0, "ports": {"p": 7000 + i % 3}}
          for i in range(200)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def serviceEndpoints(service, pods):
    selector = service.get("selector") or {}
    ready, not_ready = [], []
    target = service["targetPort"]
    for p in pods:
        labels = p.get("labels") or {}
        if any(labels.get(k) != v for k, v in selector.items()):
            continue
        if p.get("ip") is None:
            continue
        port = target
        if isinstance(target, str):
            port = (p.get("ports") or {}).get(target)
            if port is None:
                continue
        (ready if p.get("ready") else not_ready).append("%s:%d" % (p["ip"], port))
    return [sorted(ready), sorted(not_ready)]
''',
        '''def serviceEndpoints(service, pods):
    selector = service.get("selector") or {}
    if not selector:
        return [[], []]
    out = []
    target = service["targetPort"]
    for p in pods:
        if p["namespace"] != service["namespace"]:
            continue
        labels = p.get("labels") or {}
        if any(labels.get(k) != v for k, v in selector.items()):
            continue
        if p.get("ip") is None:
            continue
        port = target if not isinstance(target, str) else (p.get("ports") or {}).get(target)
        if port is None:
            continue
        out.append("%s:%d" % (p["ip"], port))
    return [sorted(out), []]
''',
    ],
    guide=dict(
        prereqs="The lesson *Services, selectors, ClusterIP and EndpointSlices*: selectors, readiness and `targetPort`.",
        intuition="A Service is a filter over Pods followed by a split. Four conditions decide whether a Pod is a back end at all; "
                  "readiness only decides which of two lists it lands in.",
        hints=[
            "Handle the empty selector first: it means no automatic endpoints, not all Pods.",
            "Apply the filters in order: namespace, labels, IP, port. Use `continue` to skip a Pod as soon as one fails.",
            "When `targetPort` is a string, look it up in that Pod's own `ports`; different Pods may map the same name to different numbers.",
        ],
        brute_force="A single pass over the Pods is both the simplest and the optimal approach.",
        approach="1. Return `[[], []]` for an empty selector.\n2. For each Pod, skip it if the namespace differs, a selector label "
                 "is missing or different, the IP is `None`, or a named port cannot be resolved.\n3. Format `ip:port` and append to the "
                 "ready or not-ready list.\n4. Sort both lists.\n\n"
                 "**Dry run** (example): both Pods pass the filters; `http` resolves to 8080 on each; the first is ready, the second is not.",
        complexity="Time O(n · s + n log n) for n Pods and s selector labels. Space O(n).",
        pitfalls="- Selecting Pods from other namespaces.\n- Dropping not-ready Pods entirely; they are endpoints, marked not ready.\n"
                 "- Treating an empty selector as match-all.\n- Sorting numerically: the specification asks for plain string order, so "
                 "`10.0.0.10:80` sorts before `10.0.0.9:80`.",
        follow_up="Real EndpointSlices hold at most 100 endpoints each. Split the result into slices and decide which slices change "
                  "when one Pod becomes ready.",
    ),
),
dict(
    id="k8s-kubeconfig-context",
    title="Resolve a kubeconfig Context",
    difficulty="Easy",
    pattern="kubectl",
    entry="resolveContext",
    description=r"""
Before every command, `kubectl` works out which server to call, as which user, in which namespace. Write
`resolveContext(config, contextFlag, namespaceFlag)`.

`config` is:

```
{"clusters": {clusterName: serverUrl},
 "users": [userName, ...],
 "contexts": {contextName: {"cluster": c, "user": u, "namespace": ns (optional)}},
 "current-context": name (may be missing or "")}
```

`contextFlag` and `namespaceFlag` are strings; `""` means the flag was not given.

Return `[server, user, namespace]`, or one of these error strings, checked in this order:

1. the context name is `contextFlag` if given, otherwise `current-context`; if neither is set → `"error: no context"`
2. the name is not in `contexts` → `"error: context not found"`
3. the context's cluster is not in `clusters` → `"error: cluster not found"`
4. the context's user is not in `users` → `"error: user not found"`

The namespace is `namespaceFlag` if given, otherwise the context's `namespace` if present and non-empty, otherwise `"default"`.

**Example:** current context `local` → cluster `kind`, user `admin`, no namespace; no flags
→ `["https://127.0.0.1:6443", "admin", "default"]`
""",
    starter='''def resolveContext(config, contextFlag, namespaceFlag):
    # return [server, user, namespace] or an "error: ..." string
    pass
''',
    solution='''def resolveContext(config, contextFlag, namespaceFlag):
    name = contextFlag or config.get("current-context") or ""
    if not name:
        return "error: no context"
    ctx = (config.get("contexts") or {}).get(name)
    if ctx is None:
        return "error: context not found"
    clusters = config.get("clusters") or {}
    if ctx.get("cluster") not in clusters:
        return "error: cluster not found"
    if ctx.get("user") not in (config.get("users") or []):
        return "error: user not found"
    namespace = namespaceFlag or ctx.get("namespace") or "default"
    return [clusters[ctx["cluster"]], ctx["user"], namespace]
''',
    tests=[
        [{"clusters": {"kind": "https://127.0.0.1:6443"}, "users": ["admin"],
          "contexts": {"local": {"cluster": "kind", "user": "admin"}}, "current-context": "local"}, "", ""],
        [{"clusters": {"kind": "https://127.0.0.1:6443", "prod": "https://prod.example"}, "users": ["admin", "amara"],
          "contexts": {"local": {"cluster": "kind", "user": "admin", "namespace": "cafe"},
                       "prod": {"cluster": "prod", "user": "amara", "namespace": "shop"}}, "current-context": "local"}, "prod", ""],
        [{"clusters": {"kind": "https://k"}, "users": ["admin"],
          "contexts": {"local": {"cluster": "kind", "user": "admin", "namespace": "cafe"}}, "current-context": "local"}, "", "kube-system"],
        [{"clusters": {"kind": "https://k"}, "users": ["admin"],
          "contexts": {"local": {"cluster": "kind", "user": "admin", "namespace": "cafe"}}, "current-context": "local"}, "", ""],
        [{"clusters": {"kind": "https://k"}, "users": ["admin"],
          "contexts": {"local": {"cluster": "kind", "user": "admin"}}}, "", ""],
        [{"clusters": {"kind": "https://k"}, "users": ["admin"],
          "contexts": {"local": {"cluster": "kind", "user": "admin"}}, "current-context": ""}, "", "x"],
        [{"clusters": {"kind": "https://k"}, "users": ["admin"],
          "contexts": {"local": {"cluster": "kind", "user": "admin"}}, "current-context": "staging"}, "", ""],
        [{"clusters": {"kind": "https://k"}, "users": ["admin"],
          "contexts": {"local": {"cluster": "old", "user": "admin"}}, "current-context": "local"}, "", ""],
        [{"clusters": {"kind": "https://k"}, "users": ["admin"],
          "contexts": {"local": {"cluster": "kind", "user": "ghost"}}, "current-context": "local"}, "", ""],
        [{"clusters": {}, "users": [],
          "contexts": {"local": {"cluster": "old", "user": "ghost"}}, "current-context": "local"}, "", ""],
        [{"clusters": {"kind": "https://k"}, "users": ["admin"],
          "contexts": {"local": {"cluster": "kind", "user": "admin", "namespace": ""}}, "current-context": "other"}, "local", ""],
        [{"clusters": {"kind": "https://k"}, "users": ["admin"],
          "contexts": {"local": {"cluster": "kind", "user": "admin", "namespace": "cafe"}}, "current-context": "local"}, "missing", "x"],
    ],
    examples=2,
    wrong_solutions=[
        '''def resolveContext(config, contextFlag, namespaceFlag):
    name = config.get("current-context") or contextFlag or ""
    if not name:
        return "error: no context"
    ctx = (config.get("contexts") or {}).get(name)
    if ctx is None:
        return "error: context not found"
    clusters = config.get("clusters") or {}
    if ctx.get("cluster") not in clusters:
        return "error: cluster not found"
    if ctx.get("user") not in (config.get("users") or []):
        return "error: user not found"
    return [clusters[ctx["cluster"]], ctx["user"], namespaceFlag or ctx.get("namespace") or "default"]
''',
        '''def resolveContext(config, contextFlag, namespaceFlag):
    name = contextFlag or config.get("current-context") or ""
    if not name:
        return "error: no context"
    ctx = (config.get("contexts") or {}).get(name)
    if ctx is None:
        return "error: context not found"
    clusters = config.get("clusters") or {}
    if ctx.get("user") not in (config.get("users") or []):
        return "error: user not found"
    if ctx.get("cluster") not in clusters:
        return "error: cluster not found"
    return [clusters[ctx["cluster"]], ctx["user"], ctx.get("namespace") or namespaceFlag or "default"]
''',
    ],
    guide=dict(
        prereqs="The lesson *kubectl and kubeconfig*: clusters, users, contexts and `current-context`.",
        intuition="A context is a pointer to two other entries plus an optional default. Resolution is three dictionary lookups, with "
                  "command-line flags taking priority over the file at two points.",
        hints=[
            "Pick the context name first: flag, then `current-context`. An empty string counts as not set.",
            "Do the checks in the stated order and return at the first failure.",
            "For the namespace, Python's `a or b or \"default\"` expresses the three-level fallback directly.",
        ],
        brute_force="There is no search here; a direct sequence of lookups is the whole algorithm.",
        approach="1. `name = contextFlag or current-context`; empty → error.\n2. Look up the context; missing → error.\n"
                 "3. Check its cluster, then its user.\n4. Compute the namespace with the fallback chain.\n\n"
                 "**Dry run:** no flags, current `local` → context found → cluster `kind` exists → user `admin` exists → namespace: "
                 "flag empty, context has none → `default`.",
        complexity="O(1) with dictionary lookups (O(u) to search the users list).",
        pitfalls="- Letting `current-context` override an explicit `--context`.\n- Letting the context's namespace override `-n`.\n"
                 "- Checking the user before the cluster, which changes which error is reported.\n- Treating `\"\"` as a real namespace.",
        follow_up="`kubectl` merges several files listed in `KUBECONFIG`, with the first file winning for duplicate names. "
                  "Write the merge.",
    ),
),
dict(
    id="k8s-api-path",
    title="Build the REST Path for a Resource",
    difficulty="Easy",
    pattern="Kubernetes API",
    entry="apiPath",
    description=r"""
Every Kubernetes object lives at a URL derived from its group, version, resource and namespace. Write
`apiPath(apiVersion, resource, namespaced, namespace, name, subresource)` returning that path.

- `apiVersion` is either a bare version such as `"v1"` (the core group) or `"group/version"` such as `"apps/v1"`.
- Core group paths start with `/api/<version>`; all other groups start with `/apis/<group>/<version>`.
- If `namespaced` is true, add `/namespaces/<namespace>`, using `"default"` when `namespace` is `""`.
  If `namespaced` is false, ignore `namespace`.
- Add `/<resource>` (already lowercase plural).
- If `name` is not `""`, add `/<name>`, and then `/<subresource>` if `subresource` is not `""`.
  A subresource without a name is ignored.

**Examples**

- `("v1", "pods", True, "cafe", "web-1", "log")` → `/api/v1/namespaces/cafe/pods/web-1/log`
- `("apps/v1", "deployments", True, "", "", "")` → `/apis/apps/v1/namespaces/default/deployments`
- `("v1", "nodes", False, "cafe", "n1", "")` → `/api/v1/nodes/n1`
""",
    starter='''def apiPath(apiVersion, resource, namespaced, namespace, name, subresource):
    # return the URL path as a string
    pass
''',
    solution='''def apiPath(apiVersion, resource, namespaced, namespace, name, subresource):
    path = ("/apis/" if "/" in apiVersion else "/api/") + apiVersion
    if namespaced:
        path += "/namespaces/" + (namespace or "default")
    path += "/" + resource
    if name:
        path += "/" + name
        if subresource:
            path += "/" + subresource
    return path
''',
    tests=[
        ["v1", "pods", True, "cafe", "web-1", "log"],
        ["apps/v1", "deployments", True, "", "", ""],
        ["v1", "nodes", False, "cafe", "n1", ""],
        ["v1", "pods", True, "cafe", "", ""],
        ["v1", "pods", True, "cafe", "", "log"],
        ["apps/v1", "deployments", True, "shop", "web", "scale"],
        ["rbac.authorization.k8s.io/v1", "clusterroles", False, "", "view", ""],
        ["rbac.authorization.k8s.io/v1", "roles", True, "cafe", "reader", ""],
        ["v1", "namespaces", False, "", "cafe", ""],
        ["batch/v1", "cronjobs", True, "", "nightly", "status"],
        ["storage.k8s.io/v1", "storageclasses", False, "ignored", "", ""],
        ["gateway.networking.k8s.io/v1", "httproutes", True, "cafe", "api", ""],
        ["v1", "nodes", False, "", "", "status"],
    ],
    examples=3,
    wrong_solutions=[
        '''def apiPath(apiVersion, resource, namespaced, namespace, name, subresource):
    path = "/apis/" + apiVersion
    if namespaced:
        path += "/namespaces/" + (namespace or "default")
    path += "/" + resource
    if name:
        path += "/" + name
        if subresource:
            path += "/" + subresource
    return path
''',
        '''def apiPath(apiVersion, resource, namespaced, namespace, name, subresource):
    path = ("/apis/" if "/" in apiVersion else "/api/") + apiVersion
    if namespace:
        path += "/namespaces/" + namespace
    path += "/" + resource
    if name:
        path += "/" + name
    if subresource:
        path += "/" + subresource
    return path
''',
    ],
    guide=dict(
        prereqs="The lesson *Resources, groups and versions*: the core group, named groups, namespaced and cluster-scoped resources, subresources.",
        intuition="The path is assembled left to right from fixed pieces. The only decisions are `/api` versus `/apis`, whether a "
                  "namespace segment appears, and how far to go past the resource name.",
        hints=[
            "A `/` inside `apiVersion` tells you it is a named group.",
            "The namespace segment depends on the `namespaced` flag, not on whether a namespace string was supplied.",
            "Nest the subresource check inside the name check.",
        ],
        brute_force="String concatenation in order is the whole solution; there is no slower alternative worth describing.",
        approach="1. Prefix: `/api/v1` or `/apis/group/version`.\n2. Optional `/namespaces/<ns or default>`.\n3. `/<resource>`.\n"
                 "4. Optional `/<name>` and then optional `/<subresource>`.\n\n"
                 "**Dry run:** `(\"v1\", \"nodes\", False, \"cafe\", \"n1\", \"\")` → `/api/v1` → not namespaced, skip → `/nodes` → `/n1`.",
        complexity="O(length of the path).",
        pitfalls="- Using `/apis` for the core group.\n- Adding a namespace segment to a cluster-scoped resource because a namespace was passed.\n"
                 "- Omitting the namespace segment when a namespaced resource has no namespace given, instead of using `default`.\n"
                 "- Appending a subresource to a collection path.",
        follow_up="Add query parameters for `labelSelector`, `limit` and `watch=true`, with correct URL encoding.",
    ),
),
]
