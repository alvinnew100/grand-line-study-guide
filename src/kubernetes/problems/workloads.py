PROBLEMS = [
dict(
    id="k8s-rolling-update-plan",
    title="Rolling Update Step Planner",
    difficulty="Hard",
    pattern="Deployments",
    entry="rollingUpdate",
    description=r"""
Plan a Deployment rolling update. Write `rollingUpdate(replicas, maxSurge, maxUnavailable)` and return the list of
`[oldPods, newPods]` counts after each round.

`maxSurge` and `maxUnavailable` are each either an integer or a percentage string such as `"25%"`. Percentages are taken
of `replicas`; **`maxSurge` rounds up and `maxUnavailable` rounds down**.

If `replicas` is 0, or both values resolve to 0 (an invalid configuration), return `[]`.

Start with `old = replicas` and `ready = 0` (new Pods that are ready). Repeat until `old == 0` and `ready == replicas`:

1. **Scale up** the new ReplicaSet by `add = min((replicas + surge) - (old + ready), replicas - ready)`, never below 0.
   These Pods are created but **not ready yet**.
2. **Scale down** the old ReplicaSet by `remove = min(old, (old + ready) - (replicas - unavailable))`, never below 0.
   Only ready new Pods and old Pods count as available here; the Pods created in step 1 do not.
3. Record `[old, ready + add]`.
4. The Pods created in step 1 become ready: `ready += add`.

**Example:** `rollingUpdate(4, 1, 0)` →
`[[4,1],[3,1],[3,2],[2,2],[2,3],[1,3],[1,4],[0,4]]`: add one, wait, remove one, repeat.
""",
    starter='''def rollingUpdate(replicas, maxSurge, maxUnavailable):
    # return [[old, new], ...] after each round
    pass
''',
    solution='''def rollingUpdate(replicas, maxSurge, maxUnavailable):
    def resolve(value, round_up):
        if isinstance(value, str):
            pct = int(value.strip().rstrip("%"))
            if round_up:
                return -((-replicas * pct) // 100)
            return (replicas * pct) // 100
        return int(value)

    surge = resolve(maxSurge, True)
    unavailable = resolve(maxUnavailable, False)
    if replicas == 0 or (surge == 0 and unavailable == 0):
        return []
    old, ready = replicas, 0
    steps = []
    while old > 0 or ready < replicas:
        add = max(0, min((replicas + surge) - (old + ready), replicas - ready))
        remove = max(0, min(old, (old + ready) - (replicas - unavailable)))
        old -= remove
        steps.append([old, ready + add])
        ready += add
    return steps
''',
    tests=[
        [4, 1, 0],
        [10, "25%", "25%"],
        [4, 0, 1],
        [0, 1, 1],
        [3, 0, 0],
        [1, "25%", "25%"],
        [1, 0, 1],
        [4, "100%", 0],
        [4, 0, "100%"],
        [5, "50%", "50%"],
        [3, "10%", "10%"],
        [7, 2, 3],
        [8, "0%", "13%"],
        [100, "25%", "25%"],
        [2, 5, 0],
    ],
    examples=2,
    wrong_solutions=[
        '''def rollingUpdate(replicas, maxSurge, maxUnavailable):
    def resolve(value):
        if isinstance(value, str):
            return (replicas * int(value.strip().rstrip("%"))) // 100
        return int(value)
    surge, unavailable = resolve(maxSurge), resolve(maxUnavailable)
    if replicas == 0 or (surge == 0 and unavailable == 0):
        return []
    old, ready = replicas, 0
    steps = []
    while old > 0 or ready < replicas:
        add = max(0, min((replicas + surge) - (old + ready), replicas - ready))
        remove = max(0, min(old, (old + ready) - (replicas - unavailable)))
        old -= remove
        steps.append([old, ready + add])
        ready += add
    return steps
''',
        '''def rollingUpdate(replicas, maxSurge, maxUnavailable):
    def resolve(value, round_up):
        if isinstance(value, str):
            pct = int(value.strip().rstrip("%"))
            return -((-replicas * pct) // 100) if round_up else (replicas * pct) // 100
        return int(value)
    surge, unavailable = resolve(maxSurge, True), resolve(maxUnavailable, False)
    if replicas == 0 or (surge == 0 and unavailable == 0):
        return []
    old, ready = replicas, 0
    steps = []
    while old > 0 or ready < replicas:
        add = max(0, min((replicas + surge) - (old + ready), replicas - ready))
        ready += add
        remove = max(0, min(old, (old + ready) - (replicas - unavailable)))
        old -= remove
        steps.append([old, ready])
    return steps
''',
    ],
    guide=dict(
        prereqs="The lesson *Rolling updates, rollbacks and strategies*: the two bounds `total <= replicas + maxSurge` and "
                "`available >= replicas - maxUnavailable`, and the rounding rules.",
        intuition="Each round the controller pushes as far as each bound allows: create new Pods up to the surge ceiling, and remove "
                  "old Pods down to the availability floor. New Pods help the floor only after they become ready, which is what spaces the steps out.",
        hints=[
            "Convert percentages first. Ceiling division without floats: `-((-a * p) // 100)`.",
            "Track `old` and `ready`. The total for the surge check is `old + ready`; so is the available count for the removal check.",
            "Compute `remove` before adding the newly created Pods to `ready`.",
        ],
        brute_force="Simulating one Pod at a time gives the same result with more iterations. Batching per round is direct and at most about 2·replicas rounds.",
        approach="1. Resolve the two values; handle the empty cases.\n2. Loop: compute `add`, compute `remove` from the pre-add ready "
                 "count, record, then promote.\n\n"
                 "**Dry run** of `(4, 0, 1)`: surge 0, unavailable 1. Round 1: add = min(4−4, 4) = 0; remove = min(4, 4−3) = 1 → `[3,0]`. "
                 "Round 2: add = min(4−3, 4) = 1; remove = min(3, 3−3) = 0 → `[3,1]`. Round 3: ready 1; add 0; remove = min(3, 4−3) = 1 → `[2,1]`. And so on to `[0,4]`.",
        complexity="O(replicas) rounds, each O(1).",
        pitfalls="- Rounding both percentages the same way.\n- Counting not-yet-ready Pods as available, which removes old Pods too early.\n"
                 "- Looping forever when both values are 0.\n- Floating-point rounding errors with percentages; use integers.",
        follow_up="Add `minReadySeconds` and a readiness time per Pod, and report the wall-clock duration of the rollout.",
    ),
),
dict(
    id="k8s-rollback-target",
    title="Rollback Target from Revision History",
    difficulty="Medium",
    pattern="Deployments",
    entry="rollback",
    description=r"""
`kubectl rollout undo` re-activates an older revision and gives it a **new** revision number. Write
`rollback(history, current, toRevision)`.

- `history` is a list of `[revision, image]` pairs with distinct revision numbers, in any order.
- `current` is the revision in use now (it is in `history`).
- `toRevision` is `0` for "the previous revision", or a specific revision number.

Rules:

1. If `toRevision` is `0`, the target is the **largest revision smaller than `current`**. If there is none, return
   `"error: no previous revision"`.
2. Otherwise the target is `toRevision`. If it is not in the history, return `"error: revision not found"`.
3. If the target equals `current`, nothing changes: return `[sortedHistory, current]`.
4. Otherwise the target is removed from the history and re-added with the same image under the number
   `max(revisions) + 1`, which becomes the current revision.

Return `[newHistory, newCurrent]` with `newHistory` sorted by revision ascending.

**Example:** `rollback([[1,"a"],[2,"b"],[3,"c"]], 3, 0)` → `[[[1,"a"],[3,"c"],[4,"b"]], 4]`
""",
    starter='''def rollback(history, current, toRevision):
    # return [newHistory, newCurrent] or an error string
    pass
''',
    solution='''def rollback(history, current, toRevision):
    images = {rev: image for rev, image in history}
    if toRevision == 0:
        older = [rev for rev in images if rev < current]
        if not older:
            return "error: no previous revision"
        target = max(older)
    else:
        if toRevision not in images:
            return "error: revision not found"
        target = toRevision
    if target == current:
        return [[[rev, images[rev]] for rev in sorted(images)], current]
    new_rev = max(images) + 1
    image = images.pop(target)
    images[new_rev] = image
    return [[[rev, images[rev]] for rev in sorted(images)], new_rev]
''',
    tests=[
        [[[1, "a"], [2, "b"], [3, "c"]], 3, 0],
        [[[1, "a"], [3, "c"], [4, "b"]], 4, 0],
        [[[1, "a"]], 1, 0],
        [[[1, "a"], [2, "b"], [3, "c"]], 3, 1],
        [[[1, "a"], [2, "b"], [3, "c"]], 3, 7],
        [[[1, "a"], [2, "b"], [3, "c"]], 3, 3],
        [[[3, "c"], [1, "a"], [2, "b"]], 3, 0],
        [[[5, "e"], [9, "i"], [12, "l"]], 9, 0],
        [[[5, "e"], [9, "i"], [12, "l"]], 5, 0],
        [[[5, "e"], [9, "i"], [12, "l"]], 5, 12],
        [[[2, "x"], [4, "x"]], 4, 0],
        [[[1, "a"], [2, "b"], [3, "c"]], 2, 3],
        [[[i, "img-%d" % i] for i in range(1, 60)], 59, 30],
    ],
    examples=2,
    wrong_solutions=[
        '''def rollback(history, current, toRevision):
    images = {rev: image for rev, image in history}
    if toRevision == 0:
        target = current - 1
        if target not in images:
            return "error: no previous revision"
    else:
        if toRevision not in images:
            return "error: revision not found"
        target = toRevision
    if target == current:
        return [[[rev, images[rev]] for rev in sorted(images)], current]
    new_rev = max(images) + 1
    images[new_rev] = images.pop(target)
    return [[[rev, images[rev]] for rev in sorted(images)], new_rev]
''',
        '''def rollback(history, current, toRevision):
    images = {rev: image for rev, image in history}
    if toRevision == 0:
        older = [rev for rev in images if rev < current]
        if not older:
            return "error: no previous revision"
        target = max(older)
    else:
        if toRevision not in images:
            return "error: revision not found"
        target = toRevision
    return [[[rev, images[rev]] for rev in sorted(images)], target]
''',
    ],
    guide=dict(
        prereqs="The rollback section of *Rolling updates, rollbacks and strategies*: revisions are ReplicaSets, and an undo renumbers the target.",
        intuition="A rollback does not rewind the counter. It takes an old entry out of the history and puts it back at the top with "
                  "a fresh number. Choosing the entry is the only branching logic.",
        hints=[
            "Turn the history into a dict from revision to image.",
            "For `toRevision == 0`, collect revisions below `current` and take the maximum; revision numbers can have gaps.",
            "Compute the new number from the maximum **before** removing the target.",
        ],
        brute_force="Sorting the history and scanning backwards from the current revision also finds the previous one in O(n log n). "
                    "A single `max` over a filter is O(n).",
        approach="1. Build the dict.\n2. Find the target or return an error.\n3. If it is the current revision, return unchanged.\n"
                 "4. `new = max + 1`; move the image; return the sorted list and `new`.\n\n"
                 "**Dry run:** history 1,3,4 with current 4 and `toRevision 0`: older = [1, 3] → target 3. New number 5. "
                 "Result `[[1,a],[4,b],[5,c]]`, current 5: a second undo returns to the version that was rolled back from.",
        complexity="Time O(n log n) for the final sort, space O(n).",
        pitfalls="- Assuming the previous revision is `current - 1`.\n- Keeping the old revision number in the history.\n"
                 "- Returning the target's old number as the new current revision.\n- Using the highest revision overall instead of the highest below `current`.",
        follow_up="Enforce `revisionHistoryLimit`: after each change, drop the oldest non-current revisions beyond the limit.",
    ),
),
dict(
    id="k8s-statefulset-ordinals",
    title="StatefulSet Names, Storage and Ordering",
    difficulty="Medium",
    pattern="StatefulSets",
    entry="statefulSet",
    description=r"""
A StatefulSet gives each Pod a predictable name, DNS name and set of claims, and acts on Pods in a strict order.
Write `statefulSet(name, service, namespace, replicas, claimTemplates, readyOrdinals, partition)` returning
`[created, updateOrder]`.

**created** — the Pods that come to exist under the default `OrderedReady` policy. Pods are created from ordinal 0
upward; after creating ordinal `i`, the controller continues only if `i` is in `readyOrdinals`. Each entry is
`[podName, dnsName, claims]`:

- `podName` = `<name>-<ordinal>`
- `dnsName` = `<podName>.<service>.<namespace>.svc.cluster.local`
- `claims` = `<template>-<podName>` for each template, in the given order

**updateOrder** — the pod names touched by a rolling update, assuming all `replicas` Pods exist. Only ordinals
`>= partition` are updated, from the highest ordinal downward. After updating an ordinal the controller continues only if
it is in `readyOrdinals`; the Pod that failed to become ready **is** included, and the update stops there.

**Example:** `statefulSet("db", "db-hs", "cafe", 3, ["data"], [0, 2], 1)`
→ created: `db-0` and `db-1` (ordinal 1 never becomes ready, so `db-2` is not created);
updateOrder: `["db-2", "db-1"]` (2 is ready, 1 is not, and 0 is below the partition anyway).
""",
    starter='''def statefulSet(name, service, namespace, replicas, claimTemplates, readyOrdinals, partition):
    # return [created, updateOrder]
    pass
''',
    solution='''def statefulSet(name, service, namespace, replicas, claimTemplates, readyOrdinals, partition):
    ready = set(readyOrdinals)
    created = []
    for i in range(replicas):
        pod = "%s-%d" % (name, i)
        dns = "%s.%s.%s.svc.cluster.local" % (pod, service, namespace)
        created.append([pod, dns, ["%s-%s" % (t, pod) for t in claimTemplates]])
        if i not in ready:
            break
    update = []
    for i in range(replicas - 1, max(partition, 0) - 1, -1):
        update.append("%s-%d" % (name, i))
        if i not in ready:
            break
    return [created, update]
''',
    tests=[
        ["db", "db-hs", "cafe", 3, ["data"], [0, 2], 1],
        ["db", "db", "cafe", 3, ["data"], [0, 1, 2], 0],
        ["db", "db", "cafe", 0, ["data"], [], 0],
        ["db", "db", "cafe", 3, ["data"], [], 0],
        ["kafka", "kafka-hs", "stream", 4, ["data", "logs"], [0, 1, 2, 3], 3],
        ["kafka", "kafka-hs", "stream", 4, [], [0, 1, 2, 3], 4],
        ["kafka", "kafka-hs", "stream", 4, ["data"], [0, 1, 3], 0],
        ["web", "web", "default", 1, ["www"], [0], 0],
        ["web", "web", "default", 1, ["www"], [], 0],
        ["cache", "cache", "shop", 5, ["d"], [0, 1, 2, 4], 2],
        ["cache", "cache", "shop", 5, ["d"], [1, 2, 3, 4], 9],
        ["cache", "cache", "shop", 5, ["d"], [0, 1, 2, 3], 0],
        ["s", "svc", "ns", 40, ["a", "b"], list(range(0, 40, 1))[:25] + list(range(30, 40)), 5],
    ],
    examples=2,
    wrong_solutions=[
        '''def statefulSet(name, service, namespace, replicas, claimTemplates, readyOrdinals, partition):
    ready = set(readyOrdinals)
    created = []
    for i in range(replicas):
        pod = "%s-%d" % (name, i)
        dns = "%s.%s.%s.svc.cluster.local" % (pod, service, namespace)
        created.append([pod, dns, ["%s-%s" % (t, pod) for t in claimTemplates]])
    update = []
    for i in range(replicas - 1, max(partition, 0) - 1, -1):
        update.append("%s-%d" % (name, i))
        if i not in ready:
            break
    return [created, update]
''',
        '''def statefulSet(name, service, namespace, replicas, claimTemplates, readyOrdinals, partition):
    ready = set(readyOrdinals)
    created = []
    for i in range(replicas):
        pod = "%s-%d" % (name, i)
        dns = "%s.%s.%s.svc.cluster.local" % (pod, service, namespace)
        created.append([pod, dns, ["%s-%s" % (t, pod) for t in claimTemplates]])
        if i not in ready:
            break
    update = []
    for i in range(max(partition, 0), replicas):
        update.append("%s-%d" % (name, i))
        if i not in ready:
            break
    return [created, update]
''',
    ],
    guide=dict(
        prereqs="Both StatefulSet lessons: ordinal names, per-Pod DNS through the headless Service, `volumeClaimTemplates`, "
                "`OrderedReady` creation and partitioned rolling updates.",
        intuition="Everything about a StatefulSet Pod follows from its ordinal by string formatting. Ordering is two loops, one "
                  "counting up and one counting down, each of which stops at the first Pod that fails to become ready.",
        hints=[
            "Build the three strings for an ordinal in one place.",
            "In the creation loop, append the Pod first and then check readiness: the unready Pod exists, the ones after it do not.",
            "The update loop runs from `replicas - 1` down to `partition`, using the same append-then-check pattern.",
        ],
        brute_force="The two loops are the direct simulation and are already linear.",
        approach="1. Convert `readyOrdinals` to a set.\n2. Loop `i = 0..replicas-1`: append, break if not ready.\n"
                 "3. Loop `i = replicas-1` down to `partition`: append the name, break if not ready.\n\n"
                 "**Dry run:** replicas 4, ready {0,1,3}, partition 0. Creation: 0 (ready), 1 (ready), 2 (not ready) → stop; three Pods. "
                 "Update: 3 (ready), 2 (not ready) → stop; `[s-3, s-2]`.",
        complexity="Time O(replicas × templates), space the same for the output.",
        pitfalls="- Updating from ordinal 0 upward.\n- Excluding the Pod that failed to become ready.\n- Creating all Pods regardless of readiness.\n"
                 "- Using the StatefulSet name instead of the Service name in the DNS name.\n- A partition larger than `replicas` means nothing is updated.",
        follow_up="Model scale-down with `persistentVolumeClaimRetentionPolicy`: which claims remain after scaling from 5 to 2 with `whenScaled: Delete`?",
    ),
),
dict(
    id="k8s-daemonset-nodes",
    title="DaemonSet Target Nodes",
    difficulty="Easy",
    pattern="Workloads",
    entry="daemonSetNodes",
    description=r"""
A DaemonSet runs one Pod on every eligible node. Write `daemonSetNodes(nodes, nodeSelector, tolerations)` returning the
sorted list of node names that get a Pod.

- Each node is `{"name", "labels": {...}, "taints": [{"key", "value", "effect"}], "unschedulable": bool}`.
- `nodeSelector` is a dict; a node must have every key with the same value. An empty selector matches all nodes.
- A node is eligible only if **every** taint whose effect is `NoSchedule` or `NoExecute` is tolerated.
  Taints with effect `PreferNoSchedule` never exclude a node.
- A toleration is `{"key", "operator", "value", "effect"}` (fields may be missing). It tolerates a taint when:
  - **key**: the toleration's key equals the taint's key, or the toleration has no key (or `""`) and operator `Exists`;
  - **value**: the operator is `Exists`, or the operator is `Equal` (the default) and the values are equal;
  - **effect**: the toleration has no effect (or `""`), or it equals the taint's effect.
- DaemonSet Pods ignore `unschedulable` (a cordoned node still gets its Pod).

**Example:** nodes `a` (no taints), `b` (taint `gpu=true:NoSchedule`), `cp` (taint
`node-role.kubernetes.io/control-plane:NoSchedule`); tolerations `[{"key": "gpu", "operator": "Exists"}]` → `["a", "b"]`
""",
    starter='''def daemonSetNodes(nodes, nodeSelector, tolerations):
    # return the sorted list of target node names
    pass
''',
    solution='''def daemonSetNodes(nodes, nodeSelector, tolerations):
    def tolerates(tol, taint):
        key = tol.get("key") or ""
        op = tol.get("operator") or "Equal"
        if key == "":
            if op != "Exists":
                return False
        elif key != taint.get("key"):
            return False
        if op != "Exists" and (tol.get("value") or "") != (taint.get("value") or ""):
            return False
        effect = tol.get("effect") or ""
        return effect == "" or effect == taint.get("effect")

    out = []
    for node in nodes:
        labels = node.get("labels") or {}
        if any(labels.get(k) != v for k, v in nodeSelector.items()):
            continue
        blocked = False
        for taint in node.get("taints") or []:
            if taint.get("effect") not in ("NoSchedule", "NoExecute"):
                continue
            if not any(tolerates(t, taint) for t in tolerations):
                blocked = True
                break
        if not blocked:
            out.append(node["name"])
    return sorted(out)
''',
    tests=[
        [[{"name": "a", "labels": {}, "taints": [], "unschedulable": False},
          {"name": "b", "labels": {}, "taints": [{"key": "gpu", "value": "true", "effect": "NoSchedule"}], "unschedulable": False},
          {"name": "cp", "labels": {}, "taints": [{"key": "node-role.kubernetes.io/control-plane", "value": "", "effect": "NoSchedule"}], "unschedulable": False}],
         {}, [{"key": "gpu", "operator": "Exists"}]],
        [[], {}, []],
        [[{"name": "z", "labels": {}, "taints": [], "unschedulable": True}, {"name": "a", "labels": {}, "taints": [], "unschedulable": False}], {}, []],
        [[{"name": "a", "labels": {"os": "linux"}, "taints": [], "unschedulable": False},
          {"name": "b", "labels": {"os": "windows"}, "taints": [], "unschedulable": False},
          {"name": "c", "labels": {}, "taints": [], "unschedulable": False}], {"os": "linux"}, []],
        [[{"name": "a", "labels": {}, "taints": [{"key": "x", "value": "1", "effect": "PreferNoSchedule"}], "unschedulable": False}], {}, []],
        [[{"name": "a", "labels": {}, "taints": [{"key": "x", "value": "1", "effect": "NoExecute"}], "unschedulable": False}], {}, []],
        [[{"name": "a", "labels": {}, "taints": [{"key": "x", "value": "1", "effect": "NoSchedule"}], "unschedulable": False},
          {"name": "b", "labels": {}, "taints": [{"key": "x", "value": "2", "effect": "NoSchedule"}], "unschedulable": False}],
         {}, [{"key": "x", "operator": "Equal", "value": "1"}]],
        [[{"name": "a", "labels": {}, "taints": [{"key": "x", "value": "1", "effect": "NoSchedule"}], "unschedulable": False},
          {"name": "b", "labels": {}, "taints": [{"key": "x", "value": "1", "effect": "NoExecute"}], "unschedulable": False}],
         {}, [{"key": "x", "value": "1", "effect": "NoSchedule"}]],
        [[{"name": "a", "labels": {}, "taints": [{"key": "x", "value": "1", "effect": "NoSchedule"}, {"key": "y", "value": "", "effect": "NoExecute"}], "unschedulable": False}],
         {}, [{"key": "x", "operator": "Exists"}]],
        [[{"name": "a", "labels": {}, "taints": [{"key": "x", "value": "1", "effect": "NoSchedule"}, {"key": "y", "value": "", "effect": "NoExecute"}], "unschedulable": False},
          {"name": "b", "labels": {}, "taints": [{"key": "q", "value": "9", "effect": "NoSchedule"}], "unschedulable": True}],
         {}, [{"operator": "Exists"}]],
        [[{"name": "a", "labels": {}, "taints": [{"key": "x", "value": "1", "effect": "NoSchedule"}], "unschedulable": False}],
         {}, [{"key": "", "operator": "Equal", "value": "1"}]],
        [[{"name": "n%02d" % i, "labels": {"pool": "p%d" % (i % 3)},
           "taints": ([{"key": "dedicated", "value": "team%d" % (i % 4), "effect": "NoSchedule"}] if i % 2 else []),
           "unschedulable": i % 5 == 0} for i in range(60)],
         {"pool": "p1"}, [{"key": "dedicated", "operator": "Equal", "value": "team1"}, {"key": "dedicated", "value": "team3", "effect": "NoSchedule"}]],
    ],
    examples=2,
    wrong_solutions=[
        '''def daemonSetNodes(nodes, nodeSelector, tolerations):
    out = []
    for node in nodes:
        labels = node.get("labels") or {}
        if any(labels.get(k) != v for k, v in nodeSelector.items()):
            continue
        if node.get("unschedulable"):
            continue
        keys = set(t.get("key") for t in tolerations)
        if all(t.get("key") in keys for t in (node.get("taints") or []) if t.get("effect") != "PreferNoSchedule"):
            out.append(node["name"])
    return sorted(out)
''',
        '''def daemonSetNodes(nodes, nodeSelector, tolerations):
    out = []
    for node in nodes:
        labels = node.get("labels") or {}
        if any(labels.get(k) != v for k, v in nodeSelector.items()):
            continue
        keys = set(t.get("key") for t in tolerations)
        if all(t.get("key") in keys for t in (node.get("taints") or []) if t.get("effect") != "PreferNoSchedule"):
            out.append(node["name"])
    return sorted(out)
''',
    ],
    guide=dict(
        prereqs="The lessons *DaemonSets, Jobs and CronJobs* and *Steering the scheduler* (taints, tolerations, node selectors).",
        intuition="A node is a target unless something rules it out. Two things can: a missing label, or a hard taint that no "
                  "toleration covers. Matching one toleration against one taint is three independent comparisons: key, value, effect.",
        hints=[
            "Write `tolerates(toleration, taint)` as a small function returning a boolean.",
            "Skip `PreferNoSchedule` taints before looking for a toleration.",
            "A toleration with an empty key and operator `Exists` matches every taint; with operator `Equal` and an empty key it matches nothing.",
        ],
        brute_force="Checking every taint of every node against every toleration is O(nodes × taints × tolerations), which is the intended solution since all three are small.",
        approach="1. For each node, check the selector.\n2. For each hard taint, require `any(tolerates(...))`.\n3. Collect and sort.\n\n"
                 "**Dry run:** taint `x=1:NoExecute`, toleration `{key: x, value: 1, effect: NoSchedule}`. Key matches, value matches, "
                 "effect differs → not tolerated → node excluded.",
        complexity="Time O(N · T · K) for N nodes, T taints per node and K tolerations; space O(N).",
        pitfalls="- Excluding cordoned nodes; DaemonSets ignore `unschedulable`.\n- Treating `PreferNoSchedule` as a hard taint.\n"
                 "- Comparing keys only and ignoring value and effect.\n- Forgetting that the default operator is `Equal`.",
        follow_up="Given the current Pods, compute which nodes need a Pod created and which Pods must be deleted because their node no longer qualifies.",
    ),
),
dict(
    id="k8s-job-completions",
    title="Job Completions, Parallelism and backoffLimit",
    difficulty="Medium",
    pattern="Workloads",
    entry="runJob",
    description=r"""
Simulate a Kubernetes Job. Write `runJob(completions, parallelism, backoffLimit, outcomes)` returning
`[status, succeeded, failed, podsStarted]`.

`outcomes` is a string of `S` (a Pod succeeds) and `F` (a Pod fails), consumed left to right as Pods finish.
`completions` and `parallelism` are at least 1.

The Job runs in rounds. In each round:

1. Start `n = min(parallelism, completions - succeeded)` Pods; `podsStarted += n`.
2. The Pods finish one after another, each taking the next character of `outcomes`:
   - `S` → `succeeded += 1`; if `succeeded == completions`, the Job is `"Complete"` and stops.
   - `F` → `failed += 1`; if `failed > backoffLimit`, the Job is `"Failed"` and stops immediately.
   - If `outcomes` has no characters left, the Job is still `"Running"`; stop.

Pods of the round that did not get to report (because the Job stopped) still count in `podsStarted`.

**Example:** `runJob(3, 2, 1, "SFSS")` → round 1 starts 2 Pods: S, F. Round 2 starts 2: S, S → complete
→ `["Complete", 3, 1, 4]`
""",
    starter='''def runJob(completions, parallelism, backoffLimit, outcomes):
    # return [status, succeeded, failed, podsStarted]
    pass
''',
    solution='''def runJob(completions, parallelism, backoffLimit, outcomes):
    succeeded = failed = started = 0
    pos = 0
    while True:
        n = min(parallelism, completions - succeeded)
        started += n
        for _ in range(n):
            if pos >= len(outcomes):
                return ["Running", succeeded, failed, started]
            ch = outcomes[pos]
            pos += 1
            if ch == "S":
                succeeded += 1
                if succeeded == completions:
                    return ["Complete", succeeded, failed, started]
            else:
                failed += 1
                if failed > backoffLimit:
                    return ["Failed", succeeded, failed, started]
''',
    tests=[
        [3, 2, 1, "SFSS"],
        [1, 1, 6, "S"],
        [1, 1, 6, ""],
        [1, 1, 0, "F"],
        [1, 1, 0, "S"],
        [5, 1, 6, "SSSSS"],
        [5, 5, 6, "SSSSS"],
        [5, 2, 6, "SSS"],
        [4, 3, 2, "FFFS"],
        [4, 3, 2, "FFSFS"],
        [3, 3, 6, "SFFFSFS"],
        [2, 4, 1, "FSFS"],
        [6, 4, 3, "SSFSSFSS"],
        [3, 10, 0, "SSF"],
        [50, 7, 20, "SF" * 60],
    ],
    examples=2,
    wrong_solutions=[
        '''def runJob(completions, parallelism, backoffLimit, outcomes):
    succeeded = failed = started = 0
    for ch in outcomes:
        started += 1
        if ch == "S":
            succeeded += 1
            if succeeded == completions:
                return ["Complete", succeeded, failed, started]
        else:
            failed += 1
            if failed > backoffLimit:
                return ["Failed", succeeded, failed, started]
    return ["Running", succeeded, failed, started]
''',
        '''def runJob(completions, parallelism, backoffLimit, outcomes):
    succeeded = failed = started = 0
    pos = 0
    while True:
        n = min(parallelism, completions - succeeded)
        started += n
        for _ in range(n):
            if pos >= len(outcomes):
                return ["Running", succeeded, failed, started]
            ch = outcomes[pos]
            pos += 1
            if ch == "S":
                succeeded += 1
                if succeeded == completions:
                    return ["Complete", succeeded, failed, started]
            else:
                failed += 1
                if failed >= backoffLimit:
                    return ["Failed", succeeded, failed, started]
''',
    ],
    guide=dict(
        prereqs="Jobs from *DaemonSets, Jobs and CronJobs*: `completions`, `parallelism` and `backoffLimit`.",
        intuition="A Job keeps launching batches of Pods until enough have succeeded or too many have failed. The batch size shrinks "
                  "as the remaining work shrinks, so the Job never starts more Pods than could still be useful.",
        hints=[
            "Use an outer loop for rounds and an inner loop for the Pods of a round.",
            "Add the whole batch to `podsStarted` before reading any outcome.",
            "Three return points inside the inner loop: out of outcomes, completed, failed. Check `failed > backoffLimit`, not `>=`.",
        ],
        brute_force="The simulation is already linear in the number of outcomes consumed; there is nothing faster to aim for.",
        approach="1. Counters at zero, a position in `outcomes`.\n2. Round: `n = min(parallelism, completions - succeeded)`; `started += n`.\n"
                 "3. For each Pod read a character and update; return when a terminal condition is met.\n\n"
                 "**Dry run** of `(4, 3, 2, \"FFFS\")`: round 1 starts 3. F (failed 1), F (2), F (3 > 2) → `[\"Failed\", 0, 3, 3]`. "
                 "The trailing S is never read.",
        complexity="Time O(len(outcomes)), space O(1).",
        pitfalls="- Counting one started Pod per outcome and ignoring parallelism.\n- Failing at `failed == backoffLimit`: the limit "
                 "is the number of retries allowed, so the Job fails on the failure after that.\n- Starting `parallelism` Pods even when "
                 "fewer completions remain.\n- An infinite loop when `outcomes` is empty.",
        follow_up="Add `activeDeadlineSeconds` with a duration per Pod, and Indexed completion mode where each index must succeed once.",
    ),
),
dict(
    id="k8s-cronjob-next-runs",
    title="CronJob Next Run Times",
    difficulty="Hard",
    pattern="Workloads",
    entry="nextRuns",
    description=r"""
A CronJob's `schedule` is a five-field cron expression: `minute hour day-of-month month day-of-week`.
Write `nextRuns(schedule, start, count)` returning the next `count` run times **strictly after** `start`.

- `start` and the results are strings `"YYYY-MM-DD HH:MM"` (UTC, no seconds).
- Field ranges: minute 0-59, hour 0-23, day-of-month 1-31, month 1-12, day-of-week 0-6 with **0 = Sunday**.
- Each field is a comma-separated list of items. An item is `*`, a number `a`, a range `a-b`, or any of those with a step:
  `*/n`, `a-b/n` (every `n`-th value starting from the low end), or `a/n` (from `a` to the field's maximum, every `n`).
- A time matches when minute, hour and month match, **and** the day matches:
  - if both day fields are exactly `*`, every day matches;
  - if only one of them is exactly `*`, the other one must match;
  - if neither is `*`, the day matches when **either** field matches.
- Search at most 8 years ahead; return fewer results if fewer exist. `count` is at most 20.

**Examples**

- `nextRuns("*/15 9-10 * * 1-5", "2026-11-20 10:40", 3)` (a Friday)
  → `["2026-11-20 10:45", "2026-11-23 09:00", "2026-11-23 09:15"]`
- `nextRuns("0 0 1 * *", "2026-11-21 08:00", 2)` → `["2026-12-01 00:00", "2027-01-01 00:00"]`
""",
    starter='''def nextRuns(schedule, start, count):
    # return a list of "YYYY-MM-DD HH:MM" strings
    pass
''',
    solution='''def nextRuns(schedule, start, count):
    import datetime

    def parse(field, lo, hi):
        values = set()
        for item in field.split(","):
            step = 1
            if "/" in item:
                item, step_text = item.split("/")
                step = int(step_text)
                if item == "*":
                    a, b = lo, hi
                elif "-" in item:
                    a, b = [int(x) for x in item.split("-")]
                else:
                    a, b = int(item), hi
            elif item == "*":
                a, b = lo, hi
            elif "-" in item:
                a, b = [int(x) for x in item.split("-")]
            else:
                a = b = int(item)
            values.update(range(a, b + 1, step))
        return values

    f = schedule.split()
    minutes = sorted(parse(f[0], 0, 59))
    hours = sorted(parse(f[1], 0, 23))
    doms = parse(f[2], 1, 31)
    months = parse(f[3], 1, 12)
    dows = parse(f[4], 0, 6)
    dom_star, dow_star = f[2] == "*", f[4] == "*"

    def day_matches(d):
        if d.month not in months:
            return False
        dom_ok = d.day in doms
        dow_ok = ((d.weekday() + 1) % 7) in dows
        if dom_star and dow_star:
            return True
        if dom_star:
            return dow_ok
        if dow_star:
            return dom_ok
        return dom_ok or dow_ok

    begin = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M")
    day = begin.date()
    out = []
    for _ in range(8 * 366 + 1):
        if len(out) >= count:
            break
        if day_matches(day):
            for h in hours:
                for m in minutes:
                    t = datetime.datetime(day.year, day.month, day.day, h, m)
                    if t > begin and len(out) < count:
                        out.append(t.strftime("%Y-%m-%d %H:%M"))
        day += datetime.timedelta(days=1)
    return out
''',
    tests=[
        ["*/15 9-10 * * 1-5", "2026-11-20 10:40", 3],
        ["0 0 1 * *", "2026-11-21 08:00", 2],
        ["* * * * *", "2026-12-31 23:58", 3],
        ["0 3 * * *", "2026-11-21 03:00", 2],
        ["0 3 * * *", "2026-11-21 02:59", 1],
        ["30 2 * * 0", "2026-11-21 00:00", 3],
        ["0 0 29 2 *", "2026-11-21 00:00", 2],
        ["0 12 13 * 5", "2026-11-01 00:00", 4],
        ["5,35 8-18/5 * * *", "2026-11-21 13:05", 4],
        ["0 0 31 * *", "2026-11-21 00:00", 3],
        ["15 10/6 * 1,7 *", "2026-11-21 00:00", 4],
        ["0 0 * * 6,0", "2026-11-20 12:00", 4],
        ["0 0 31 2 *", "2026-11-21 00:00", 2],
        ["59 23 31 12 *", "2026-12-31 23:59", 2],
        ["0 9 1-7 * 1", "2026-11-21 00:00", 5],
        ["10-20/5 0 * * *", "2026-11-21 00:12", 0],
    ],
    examples=2,
    wrong_solutions=[
        '''def nextRuns(schedule, start, count):
    import datetime

    def parse(field, lo, hi):
        values = set()
        for item in field.split(","):
            step = 1
            if "/" in item:
                item, step_text = item.split("/")
                step = int(step_text)
                if item == "*":
                    a, b = lo, hi
                elif "-" in item:
                    a, b = [int(x) for x in item.split("-")]
                else:
                    a, b = int(item), hi
            elif item == "*":
                a, b = lo, hi
            elif "-" in item:
                a, b = [int(x) for x in item.split("-")]
            else:
                a = b = int(item)
            values.update(range(a, b + 1, step))
        return values

    f = schedule.split()
    minutes = sorted(parse(f[0], 0, 59))
    hours = sorted(parse(f[1], 0, 23))
    doms, months, dows = parse(f[2], 1, 31), parse(f[3], 1, 12), parse(f[4], 0, 6)
    begin = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M")
    day = begin.date()
    out = []
    for _ in range(8 * 366 + 1):
        if len(out) >= count:
            break
        if day.month in months and day.day in doms and ((day.weekday() + 1) % 7) in dows:
            for h in hours:
                for m in minutes:
                    t = datetime.datetime(day.year, day.month, day.day, h, m)
                    if t > begin and len(out) < count:
                        out.append(t.strftime("%Y-%m-%d %H:%M"))
        day += datetime.timedelta(days=1)
    return out
''',
        '''def nextRuns(schedule, start, count):
    import datetime

    def parse(field, lo, hi):
        values = set()
        for item in field.split(","):
            step = 1
            if "/" in item:
                item, step_text = item.split("/")
                step = int(step_text)
            if item == "*":
                a, b = lo, hi
            elif "-" in item:
                a, b = [int(x) for x in item.split("-")]
            else:
                a = b = int(item)
            values.update(range(a, b + 1, step))
        return values

    f = schedule.split()
    minutes = sorted(parse(f[0], 0, 59))
    hours = sorted(parse(f[1], 0, 23))
    doms, months, dows = parse(f[2], 1, 31), parse(f[3], 1, 12), parse(f[4], 0, 6)
    dom_star, dow_star = f[2] == "*", f[4] == "*"
    begin = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M")
    day = begin.date()
    out = []
    for _ in range(8 * 366 + 1):
        if len(out) >= count:
            break
        dom_ok, dow_ok = day.day in doms, day.weekday() in dows
        ok = True if dom_star and dow_star else (dow_ok if dom_star else (dom_ok if dow_star else dom_ok or dow_ok))
        if ok and day.month in months:
            for h in hours:
                for m in minutes:
                    t = datetime.datetime(day.year, day.month, day.day, h, m)
                    if t >= begin and len(out) < count:
                        out.append(t.strftime("%Y-%m-%d %H:%M"))
        day += datetime.timedelta(days=1)
    return out
''',
    ],
    guide=dict(
        prereqs="CronJobs and cron syntax from *DaemonSets, Jobs and CronJobs*. Python's `datetime` module (standard library).",
        intuition="A cron expression describes five sets of allowed numbers. A moment matches when its fields fall in those sets, with "
                  "one quirk for the two day fields. Instead of testing every minute of several years, walk forward day by day and, on "
                  "matching days, list the matching hours and minutes directly.",
        hints=[
            "Write `parse(field, lo, hi)` that returns a set of integers, handling `*`, `a`, `a-b` and an optional `/n`.",
            "Python's `weekday()` has Monday = 0; cron has Sunday = 0. Convert with `(weekday() + 1) % 7`.",
            "Remember whether each day field was literally `*` before parsing; the OR rule depends on that, not on the resulting set.",
        ],
        brute_force="Stepping one minute at a time and testing every field is simple but needs up to 4 million iterations for a rare "
                    "schedule such as 29 February. Iterating over days first cuts that to a few thousand.",
        approach="1. Parse the five fields into sets and note which day fields are `*`.\n2. Starting from the start date, for each day: "
                 "check month and the day rule.\n3. On a matching day, iterate the sorted hours and minutes and keep times strictly after `start`.\n"
                 "4. Stop at `count` results or after 8 years.\n\n"
                 "**Dry run** of `0 12 13 * 5` from 1 November 2026: neither day field is `*`, so the day matches on the 13th **or** on any "
                 "Friday: 6, 13, 20 and 27 November at 12:00.",
        complexity="Time O(D + R) where D is the number of days scanned (at most about 2,900) and R the hour-minute combinations on matching days. Space O(count).",
        pitfalls="- Requiring both day fields to match when both are restricted; cron uses OR.\n- Getting the weekday numbering wrong.\n"
                 "- Including `start` itself.\n- Treating `a/n` as the single value `a`.\n- Dates that never occur, such as 31 February: the loop must end.",
        follow_up="Add the CronJob `timeZone` field and daylight-saving transitions, and `startingDeadlineSeconds` to decide which missed runs are still started.",
    ),
),
dict(
    id="k8s-cronjob-concurrency",
    title="CronJob Concurrency Policy",
    difficulty="Medium",
    pattern="Workloads",
    entry="cronRuns",
    description=r"""
When a CronJob's previous run is still going at the next scheduled time, `concurrencyPolicy` decides what happens.
Write `cronRuns(starts, durations, policy)` returning the runs that actually happen as `[start, end]` pairs in
chronological order.

- `starts` is a strictly increasing list of scheduled times (integers, minutes).
- `durations[i]` is how long the Job scheduled at `starts[i]` would run if left alone (a positive integer).
- A Job started at `s` with duration `d` occupies the interval `[s, s + d)`; it is **still running** at time `t`
  when `t < s + d`.
- `policy` is one of:
  - `"Allow"`: every scheduled Job runs; overlaps are fine.
  - `"Forbid"`: if the most recently **started** Job is still running at a scheduled time, that schedule is skipped.
  - `"Replace"`: if the most recently started Job is still running, it is stopped at that moment (its `end` becomes the
    new start time) and the new Job starts.

**Example:** `starts = [0, 10, 20]`, `durations = [25, 5, 5]`

- `Allow` → `[[0, 25], [10, 15], [20, 25]]`
- `Forbid` → `[[0, 25]]` (the Job from minute 0 is still running at 10 and at 20)
- `Replace` → `[[0, 10], [10, 15], [20, 25]]`
""",
    starter='''def cronRuns(starts, durations, policy):
    # return [[start, end], ...] for the jobs that actually run
    pass
''',
    solution='''def cronRuns(starts, durations, policy):
    runs = []
    for s, d in zip(starts, durations):
        if runs and policy != "Allow" and s < runs[-1][1]:
            if policy == "Forbid":
                continue
            runs[-1][1] = s
        runs.append([s, s + d])
    return runs
''',
    tests=[
        [[0, 10, 20], [25, 5, 5], "Allow"],
        [[0, 10, 20], [25, 5, 5], "Forbid"],
        [[0, 10, 20], [25, 5, 5], "Replace"],
        [[], [], "Forbid"],
        [[0], [100], "Replace"],
        [[0, 10, 20], [10, 10, 10], "Forbid"],
        [[0, 10, 20], [10, 10, 10], "Replace"],
        [[0, 10, 20, 30], [11, 11, 11, 11], "Forbid"],
        [[0, 10, 20, 30], [11, 11, 11, 11], "Replace"],
        [[0, 5, 10, 15, 60], [50, 1, 1, 1, 1], "Forbid"],
        [[0, 5, 10, 15, 60], [50, 1, 20, 1, 1], "Replace"],
        [[3, 4, 5, 6], [1, 1, 1, 1], "Forbid"],
        [list(range(0, 300, 3)), [(i * 7) % 11 + 1 for i in range(100)], "Forbid"],
        [list(range(0, 300, 3)), [(i * 7) % 11 + 1 for i in range(100)], "Replace"],
    ],
    examples=3,
    wrong_solutions=[
        '''def cronRuns(starts, durations, policy):
    runs = []
    for s, d in zip(starts, durations):
        if runs and policy != "Allow" and s <= runs[-1][1]:
            if policy == "Forbid":
                continue
            runs[-1][1] = s
        runs.append([s, s + d])
    return runs
''',
        '''def cronRuns(starts, durations, policy):
    runs = []
    for s, d in zip(starts, durations):
        if runs and policy == "Forbid" and s < runs[-1][1]:
            continue
        runs.append([s, s + d])
    return runs
''',
    ],
    guide=dict(
        prereqs="CronJob `concurrencyPolicy` from *DaemonSets, Jobs and CronJobs*.",
        intuition="Only the most recently started Job matters. At each scheduled time, ask one question: is it still running? Then "
                  "the policy says whether to go ahead anyway, skip, or cut the old one short.",
        hints=[
            "Keep the accepted runs in a list; the last element is the most recently started Job.",
            "\"Still running at `s`\" is `s < end` of that last run. A Job ending exactly at `s` has finished.",
            "For `Replace`, modify the previous run's end in place before appending the new run.",
        ],
        brute_force="For each scheduled time, scan all earlier runs to see whether any overlaps: O(n²). Because only the latest "
                    "started Job needs checking, one pass is enough.",
        approach="1. Iterate over `(start, duration)` pairs.\n2. If there is a previous run, the policy is not `Allow`, and the previous run is still going: "
                 "skip for `Forbid`; truncate the previous run for `Replace`.\n3. Append `[s, s + d]` unless skipped.\n\n"
                 "**Dry run** with `Forbid`, starts 0, 10, 20, 30 and duration 11 each: 0 runs to 11. At 10 it is still running → skip. "
                 "At 20 the last run ended at 11 → run to 31. At 30 still running → skip. Result `[[0,11],[20,31]]`.",
        complexity="Time O(n), space O(n).",
        pitfalls="- Using `<=`, which wrongly treats a Job that ends exactly at the next start as still running.\n"
                 "- For `Forbid`, comparing against the last *scheduled* time instead of the last *accepted* run.\n"
                 "- For `Replace`, forgetting to shorten the replaced run.",
        follow_up="Combine this with the previous problem: generate the start times from a cron expression, then apply the policy and `startingDeadlineSeconds`.",
    ),
),
]
