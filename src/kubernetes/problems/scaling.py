def _node(name, cpu, mem, used_cpu=0, used_mem=0, labels=None, taints=None, unschedulable=False):
    return {"name": name, "cpu": cpu, "memory": mem, "usedCpu": used_cpu, "usedMemory": used_mem,
            "labels": labels or {}, "taints": taints or [], "unschedulable": unschedulable}


def _taint(key, value="", effect="NoSchedule"):
    return {"key": key, "value": value, "effect": effect}


_SCHED_NODES = [
    _node("worker-1", 4000, 8192, 3500, 4096, {"disk": "ssd"}),
    _node("worker-2", 4000, 8192, 1000, 6144, {"disk": "hdd"}),
    _node("worker-3", 8000, 16384, 2000, 4096, {"disk": "ssd"}),
    _node("gpu-1", 16000, 65536, 0, 0, {"disk": "ssd"}, [_taint("dedicated", "ml")]),
]
_SCHED_TIE = [
    _node("b-node", 4000, 8192, 1000, 2048),
    _node("a-node", 4000, 8192, 1000, 2048),
    _node("c-node", 4000, 8192, 3000, 2048),
]
_SCHED_MEM = [
    _node("cpu-rich", 8000, 8192, 0, 7168),
    _node("balanced", 8000, 8192, 4000, 2048),
]

_ZONE_NODES = [
    {"name": "a1", "labels": {"zone": "a", "host": "a1"}},
    {"name": "a2", "labels": {"zone": "a", "host": "a2"}},
    {"name": "b1", "labels": {"zone": "b", "host": "b1"}},
    {"name": "c1", "labels": {"zone": "c", "host": "c1"}},
    {"name": "x1", "labels": {"host": "x1"}},
]

_PDB_PODS = [
    {"name": "api-0", "labels": {"app": "api", "tier": "backend"}, "ready": True},
    {"name": "api-1", "labels": {"app": "api", "tier": "backend"}, "ready": True},
    {"name": "api-2", "labels": {"app": "api", "tier": "backend"}, "ready": True},
    {"name": "api-3", "labels": {"app": "api", "tier": "backend"}, "ready": False},
    {"name": "db-0", "labels": {"app": "db", "tier": "backend"}, "ready": True},
    {"name": "batch-0", "labels": {"app": "batch"}, "ready": True},
]


def _deploy(name, selector, labels, containers, ns=None):
    meta = {"name": name}
    if ns:
        meta["namespace"] = ns
    return {"kind": "Deployment", "metadata": meta,
            "spec": {"selector": {"matchLabels": selector},
                     "template": {"metadata": {"labels": labels}, "spec": {"containers": containers}}}}


def _ctr(name, image, cpu="250m", memory="256Mi", ports=(8080,)):
    requests = {}
    if cpu:
        requests["cpu"] = cpu
    if memory:
        requests["memory"] = memory
    c = {"name": name, "image": image, "ports": [{"containerPort": p} for p in ports]}
    if requests:
        c["resources"] = {"requests": requests}
    return c


def _svc(name, selector, ports, ns=None):
    meta = {"name": name}
    if ns:
        meta["namespace"] = ns
    return {"kind": "Service", "metadata": meta,
            "spec": {"selector": selector, "ports": [{"port": p, "targetPort": t} for p, t in ports]}}


_GOOD_DEPLOY = _deploy("orders", {"app": "orders"}, {"app": "orders", "tier": "backend"},
                       [_ctr("api", "ghcr.io/harbour-coffee/orders-api:2.0.4")])
_GOOD_SVC = _svc("orders", {"app": "orders"}, [(80, 8080)])

PROBLEMS = [
dict(
    id="k8s-hpa-replicas",
    title="HPA Replica Calculation",
    difficulty="Medium",
    pattern="Autoscaling",
    entry="hpaReplicas",
    description=r"""
The Horizontal Pod Autoscaler decides how many replicas a workload should have. Write
`hpaReplicas(currentReplicas, metrics, minReplicas, maxReplicas, tolerancePercent)`.

- `metrics` is a non-empty list of `[currentValue, targetValue]` pairs of integers (`targetValue > 0`), one per metric.
- For **each** metric compute a proposal:
  - if the current value is within the tolerance of the target, that is
    `|currentValue - targetValue| * 100 <= tolerancePercent * targetValue`, the proposal is `currentReplicas` (no change);
  - otherwise the proposal is `ceil(currentReplicas * currentValue / targetValue)`.
- The desired count is the **largest** proposal.
- Finally clamp the result to the range `minReplicas ... maxReplicas`.

Return the resulting integer. Use integer arithmetic throughout: floating-point division gives wrong answers for some
inputs. In Python `15 * (124 / 60)` is `31.000000000000004`, whose ceiling is 32 instead of 31, and
`abs(66 / 60 - 1) <= 0.1` is `False` although 66 is exactly 10% above 60.

**Example 1:** `hpaReplicas(4, [[90, 60]], 1, 10, 10)` → `6` (ratio 1.5, 4 × 1.5 = 6)

**Example 2:** `hpaReplicas(5, [[63, 60]], 1, 10, 10)` → `5` (63 is within 10% of 60)
""",
    starter='''def hpaReplicas(currentReplicas, metrics, minReplicas, maxReplicas, tolerancePercent):
    # return the replica count the autoscaler wants
    pass
''',
    solution='''def hpaReplicas(currentReplicas, metrics, minReplicas, maxReplicas, tolerancePercent):
    best = None
    for current, target in metrics:
        if abs(current - target) * 100 <= tolerancePercent * target:
            proposal = currentReplicas
        else:
            proposal = -(-(currentReplicas * current) // target)
        if best is None or proposal > best:
            best = proposal
    return max(minReplicas, min(maxReplicas, best))
''',
    tests=[
        [4, [[90, 60]], 1, 10, 10],
        [5, [[63, 60]], 1, 10, 10],
        [6, [[30, 60]], 1, 10, 10],
        [5, [[66, 60]], 1, 10, 10],
        [5, [[67, 60]], 1, 10, 10],
        [10, [[240, 60]], 3, 20, 10],
        [4, [[90, 60], [30, 100]], 1, 10, 10],
        [4, [[61, 60], [30, 100]], 1, 10, 10],
        [8, [[20, 50], [45, 50]], 1, 20, 10],
        [15, [[124, 60]], 1, 100, 10],
        [10, [[66, 60]], 1, 100, 5],
        [7, [[100, 70]], 1, 100, 0],
        [1, [[0, 50]], 1, 5, 10],
        [2, [[50, 50]], 5, 10, 10],
        [12, [[50, 50]], 1, 8, 10],
    ],
    examples=2,
    wrong_solutions=[
        '''import math
def hpaReplicas(currentReplicas, metrics, minReplicas, maxReplicas, tolerancePercent):
    best = 0
    for current, target in metrics:
        ratio = current / target
        if abs(ratio - 1) <= tolerancePercent / 100:
            proposal = currentReplicas
        else:
            proposal = math.ceil(currentReplicas * ratio)
        best = max(best, proposal)
    return max(minReplicas, min(maxReplicas, best))
''',
        '''def hpaReplicas(currentReplicas, metrics, minReplicas, maxReplicas, tolerancePercent):
    best = 0
    for current, target in metrics:
        best = max(best, -(-(currentReplicas * current) // target))
    return max(minReplicas, min(maxReplicas, best))
''',
        '''def hpaReplicas(currentReplicas, metrics, minReplicas, maxReplicas, tolerancePercent):
    current, target = metrics[0]
    if abs(current - target) * 100 <= tolerancePercent * target:
        proposal = currentReplicas
    else:
        proposal = -(-(currentReplicas * current) // target)
    return max(minReplicas, min(maxReplicas, proposal))
''',
    ],
    guide=dict(
        prereqs="The lesson *Autoscaling: HPA, VPA and the cluster autoscaler*: the replica formula, the tolerance band, "
                "the rule for several metrics, and `minReplicas`/`maxReplicas`.",
        intuition="If every Pod is at 150% of the target, the same total work spread over 1.5 times as many Pods would bring each back "
                  "to the target. That is the whole formula. The tolerance stops the count from twitching when the metric is "
                  "close to the target, and with several metrics the workload must satisfy the hungriest one.",
        hints=[
            "Handle one metric first: tolerance check, then the ceiling, then the clamp.",
            "`ceil(a / b)` for positive integers can be written `-(-a // b)` or `(a + b - 1) // b`, with no floating point.",
            "Compute one proposal per metric and keep the maximum. Clamp once, at the very end.",
        ],
        brute_force="There is nothing to search: one pass over the metrics is already optimal. The only 'naive' version is the one "
                    "using floating-point division, which is wrong for inputs such as 15 replicas at 124 against a target of 60 "
                    "(`15 * (124 / 60)` is `31.000000000000004`, and its ceiling is 32).",
        approach="1. For each `[current, target]`: if `abs(current - target) * 100 <= tolerancePercent * target`, propose `currentReplicas`.\n"
                 "2. Otherwise propose `-(-(currentReplicas * current) // target)`.\n3. Take the maximum proposal.\n"
                 "4. Return `max(minReplicas, min(maxReplicas, best))`.\n\n"
                 "**Dry run:** `hpaReplicas(8, [[20, 50], [45, 50]], 1, 20, 10)`. Metric 1: `|20 - 50| * 100 = 3000 > 500`, so "
                 "`ceil(8 * 20 / 50) = ceil(3.2) = 4`. Metric 2: `|45 - 50| * 100 = 500 <= 500`, within tolerance, so 8. "
                 "Maximum is 8; within 1..20; answer 8. One busy metric is enough to keep the replicas.",
        complexity="Time O(m) for m metrics, space O(1).",
        pitfalls="- Floating-point ceilings that turn an exact 31 into 32.\n- Rounding to nearest instead of up.\n"
                 "- Skipping the tolerance check, so the count changes on every small wobble.\n"
                 "- Taking the first or the smallest proposal when there are several metrics.\n"
                 "- Forgetting to clamp when the metric is within tolerance but the current count is outside the min/max range.",
        follow_up="Add a scale-down stabilisation window: given the proposals of the last N evaluations, scale down only to the "
                  "largest of them. Then add a policy limiting scale-up to 100% or 4 Pods per period, whichever is greater.",
    ),
),
dict(
    id="k8s-scheduler",
    title="Scheduler: Filter and Score",
    difficulty="Medium",
    pattern="Scheduling",
    entry="schedulePod",
    description=r"""
Implement the two phases of the Kubernetes scheduler for one Pod. Write `schedulePod(nodes, pod)` returning the name of
the chosen node, or `""` if the Pod must stay Pending.

Each node is `{"name", "cpu", "memory", "usedCpu", "usedMemory", "labels": {...}, "taints": [...], "unschedulable": bool}`.
`cpu` and `memory` are the node's allocatable amounts; `usedCpu` and `usedMemory` are the sums of the requests of Pods
already there. The Pod is `{"cpu", "memory", "nodeSelector": {...}, "tolerations": [...]}` (the last two may be missing).

**Filter.** A node is feasible only if all of these hold:

1. `unschedulable` is false;
2. `cpu - usedCpu >= pod.cpu` and `memory - usedMemory >= pod.memory`;
3. the node has every label in `nodeSelector` with the same value;
4. every taint whose effect is `NoSchedule` or `NoExecute` is tolerated. A toleration `{"key", "operator", "value", "effect"}`
   tolerates a taint `{"key", "value", "effect"}` when the keys are equal (or the toleration has no key and operator
   `Exists`), **and** the operator is `Exists` or the values are equal (operator defaults to `Equal`), **and** the
   toleration's effect is missing/empty or equals the taint's effect.

**Score** each feasible node with the *least allocated* rule, using integer division:

`cpuScore = (cpu - usedCpu - pod.cpu) * 100 // cpu`, `memScore` likewise, `score = (cpuScore + memScore) // 2`.

Return the feasible node with the highest score; break ties by the alphabetically smallest name.

**Example:** nodes `worker-1` (4000m, 3500m used), `worker-2` (4000m, 1000m used, 6144 of 8192 Mi used),
`worker-3` (8000m, 2000m used, 4096 of 16384 Mi used), and a tainted `gpu-1`; Pod `{"cpu": 1000, "memory": 1024}` →
`"worker-3"` (scores: worker-2 = 31, worker-3 = 65).
""",
    starter='''def schedulePod(nodes, pod):
    # return the chosen node name, or "" when no node is feasible
    pass
''',
    solution='''def schedulePod(nodes, pod):
    selector = pod.get("nodeSelector") or {}
    tolerations = pod.get("tolerations") or []

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

    best = None
    for n in nodes:
        if n.get("unschedulable"):
            continue
        free_cpu = n["cpu"] - n["usedCpu"] - pod["cpu"]
        free_mem = n["memory"] - n["usedMemory"] - pod["memory"]
        if free_cpu < 0 or free_mem < 0:
            continue
        labels = n.get("labels") or {}
        if any(labels.get(k) != v for k, v in selector.items()):
            continue
        hard = [t for t in (n.get("taints") or []) if t.get("effect") in ("NoSchedule", "NoExecute")]
        if any(not any(tolerates(tol, t) for tol in tolerations) for t in hard):
            continue
        score = (free_cpu * 100 // n["cpu"] + free_mem * 100 // n["memory"]) // 2
        key = (-score, n["name"])
        if best is None or key < best:
            best = key
    return best[1] if best else ""
''',
    tests=[
        [_SCHED_NODES, {"cpu": 1000, "memory": 1024}],
        [_SCHED_NODES, {"cpu": 500, "memory": 2048, "nodeSelector": {"disk": "hdd"}}],
        [_SCHED_NODES, {"cpu": 12000, "memory": 32768, "tolerations": [{"key": "dedicated", "operator": "Equal", "value": "ml", "effect": "NoSchedule"}]}],
        [_SCHED_NODES, {"cpu": 12000, "memory": 32768}],
        [_SCHED_NODES, {"cpu": 100, "memory": 128, "tolerations": [{"operator": "Exists"}]}],
        [_SCHED_NODES, {"cpu": 100, "memory": 128, "tolerations": [{"key": "dedicated", "value": "web"}]}],
        [_SCHED_NODES, {"cpu": 500, "memory": 512, "nodeSelector": {"disk": "nvme"}}],
        [_SCHED_TIE, {"cpu": 500, "memory": 512}],
        [_SCHED_MEM, {"cpu": 1000, "memory": 512}],
        [[_node("only", 2000, 4096, 0, 0, unschedulable=True)], {"cpu": 100, "memory": 100}],
        [[_node("exact", 2000, 4096, 1000, 2048)], {"cpu": 1000, "memory": 2048}],
        [[_node("soft", 4000, 8192, 0, 0, taints=[_taint("old", "true", "PreferNoSchedule")]),
          _node("hard", 8000, 16384, 0, 0, taints=[_taint("maint", "", "NoExecute")])], {"cpu": 1000, "memory": 1024}],
        [[_node("hard", 8000, 16384, 0, 0, taints=[_taint("maint", "", "NoExecute")])],
         {"cpu": 1000, "memory": 1024, "tolerations": [{"key": "maint", "operator": "Exists", "effect": "NoSchedule"}]}],
        [[], {"cpu": 100, "memory": 100}],
        [[_node("n%02d" % i, 4000 + 1000 * (i % 4), 8192, 500 * (i % 7), 1024 * (i % 5), {"pool": "p%d" % (i % 3)},
                [_taint("team", "t%d" % (i % 2))] if i % 4 == 0 else []) for i in range(40)],
         {"cpu": 1500, "memory": 2048, "nodeSelector": {"pool": "p1"}, "tolerations": [{"key": "team", "value": "t0"}]}],
    ],
    examples=1,
    wrong_solutions=[
        '''def schedulePod(nodes, pod):
    selector = pod.get("nodeSelector") or {}
    best = None
    for n in nodes:
        if n.get("unschedulable"):
            continue
        free_cpu = n["cpu"] - n["usedCpu"] - pod["cpu"]
        free_mem = n["memory"] - n["usedMemory"] - pod["memory"]
        if free_cpu < 0 or free_mem < 0:
            continue
        labels = n.get("labels") or {}
        if any(labels.get(k) != v for k, v in selector.items()):
            continue
        score = (free_cpu * 100 // n["cpu"] + free_mem * 100 // n["memory"]) // 2
        key = (-score, n["name"])
        if best is None or key < best:
            best = key
    return best[1] if best else ""
''',
        '''def schedulePod(nodes, pod):
    selector = pod.get("nodeSelector") or {}
    tolerations = pod.get("tolerations") or []
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
    for n in sorted(nodes, key=lambda n: n["name"]):
        if n.get("unschedulable"):
            continue
        if n["cpu"] - n["usedCpu"] < pod["cpu"] or n["memory"] - n["usedMemory"] < pod["memory"]:
            continue
        labels = n.get("labels") or {}
        if any(labels.get(k) != v for k, v in selector.items()):
            continue
        hard = [t for t in (n.get("taints") or []) if t.get("effect") in ("NoSchedule", "NoExecute")]
        if any(not any(tolerates(tol, t) for tol in tolerations) for t in hard):
            continue
        return n["name"]
    return ""
''',
        '''def schedulePod(nodes, pod):
    selector = pod.get("nodeSelector") or {}
    tolerations = pod.get("tolerations") or []
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
    best = None
    for n in nodes:
        if n.get("unschedulable"):
            continue
        free_cpu = n["cpu"] - n["usedCpu"] - pod["cpu"]
        free_mem = n["memory"] - n["usedMemory"] - pod["memory"]
        if free_cpu < 0 or free_mem < 0:
            continue
        labels = n.get("labels") or {}
        if any(labels.get(k) != v for k, v in selector.items()):
            continue
        hard = [t for t in (n.get("taints") or []) if t.get("effect") in ("NoSchedule", "NoExecute")]
        if any(not any(tolerates(tol, t) for tol in tolerations) for t in hard):
            continue
        key = (-free_cpu, n["name"])
        if best is None or key < best:
            best = key
    return best[1] if best else ""
''',
    ],
    guide=dict(
        prereqs="The lesson *Steering the scheduler*: the filter and score phases, node selectors, taints and tolerations, and the "
                "least-allocated scoring idea. Requests, not usage, drive the arithmetic.",
        intuition="Scheduling is elimination followed by ranking. First throw away every node that cannot host the Pod, for any of "
                  "four reasons. Then, among the survivors, prefer the one that would be left with the largest share of its "
                  "resources free. Keeping the two phases separate keeps the code simple.",
        hints=[
            "Write the four filter checks as early `continue` statements inside one loop over the nodes.",
            "A helper `tolerates(toleration, taint)` with three independent comparisons (key, value, effect) avoids tangled conditions.",
            "Track the best candidate as a tuple `(-score, name)` and keep the smallest: that handles the tie-break for free.",
        ],
        brute_force="Checking every node against every taint and toleration is O(N · T · K), and that is the intended solution: the "
                    "real scheduler does the same, and for very large clusters it scores only a sample of the feasible nodes.",
        approach="1. Skip unschedulable nodes.\n2. Compute `free_cpu` and `free_mem` after placing the Pod; skip if either is negative.\n"
                 "3. Skip if a selector label is missing or different.\n4. Skip if a hard taint has no matching toleration.\n"
                 "5. Score with integer division and keep the best `(-score, name)`.\n\n"
                 "**Dry run** (first test): `worker-1` has 500m free, less than 1000m, filtered. `gpu-1` has an untolerated taint, "
                 "filtered. `worker-2`: cpu `(3000 - 1000) * 100 // 4000 = 50`, memory `(2048 - 1024) * 100 // 8192 = 12`, score 31. "
                 "`worker-3`: cpu `(6000 - 1000) * 100 // 8000 = 62`, memory `(12288 - 1024) * 100 // 16384 = 68`, score 65. "
                 "Answer `worker-3`.",
        complexity="Time O(N · T · K) for N nodes, T taints per node and K tolerations; space O(1).",
        pitfalls="- Using `>` instead of `>=` for the fit check: a Pod that fits exactly is allowed.\n"
                 "- Treating `PreferNoSchedule` taints as blocking.\n- Letting a toleration with effect `NoSchedule` cover a `NoExecute` taint.\n"
                 "- Scoring on CPU only, or on free amounts instead of free *shares*.\n- Forgetting the name tie-break.\n"
                 "- Scoring nodes before filtering them.",
        follow_up="Add preferred node affinity as a weighted score term, then pre-emption: when no node is feasible, find a node "
                  "where removing lower-priority Pods would make room.",
    ),
),
dict(
    id="k8s-topology-spread-skew",
    title="Topology Spread: Skew and Eligible Nodes",
    difficulty="Medium",
    pattern="Scheduling",
    entry="spreadPlacement",
    description=r"""
A topology spread constraint keeps matching Pods evenly spread over **domains** such as zones. Write
`spreadPlacement(nodes, podNodes, topologyKey, maxSkew)`.

- `nodes` is a list of `{"name", "labels": {...}}`.
- `podNodes` lists, for each existing matching Pod, the name of the node it runs on (a node name may repeat).
- A node belongs to the domain named by its label `topologyKey`. Nodes **without** that label are ignored: they are not
  eligible, and Pods on them are not counted. Pods on unknown nodes are not counted either.
- The count of a domain is the number of listed Pods on its nodes. A domain with nodes and no Pods has count 0.
- The current **skew** is the largest count minus the smallest count (0 if there are no domains).
- A new Pod may be placed in a domain when `(count + 1) - smallestCount <= maxSkew`, where `smallestCount` is the smallest
  count over all domains **before** placing.

Return `[skew, eligibleNodes]`, where `eligibleNodes` is the sorted list of names of all nodes in domains that may
receive the Pod.

**Example:** zones `a` (nodes `a1`, `a2`), `b` (`b1`), `c` (`c1`); Pods on `a1`, `a2`, `b1`; `maxSkew = 1` →
`[2, ["c1"]]` (counts 2, 1, 0; only zone `c` keeps the difference within 1).
""",
    starter='''def spreadPlacement(nodes, podNodes, topologyKey, maxSkew):
    # return [currentSkew, sortedEligibleNodeNames]
    pass
''',
    solution='''def spreadPlacement(nodes, podNodes, topologyKey, maxSkew):
    domain_of = {}
    counts = {}
    for n in nodes:
        labels = n.get("labels") or {}
        if topologyKey in labels:
            domain_of[n["name"]] = labels[topologyKey]
            counts.setdefault(labels[topologyKey], 0)
    for node_name in podNodes:
        if node_name in domain_of:
            counts[domain_of[node_name]] += 1
    if not counts:
        return [0, []]
    low, high = min(counts.values()), max(counts.values())
    ok = set(d for d, c in counts.items() if c + 1 - low <= maxSkew)
    return [high - low, sorted(name for name, d in domain_of.items() if d in ok)]
''',
    tests=[
        [_ZONE_NODES, ["a1", "a2", "b1"], "zone", 1],
        [_ZONE_NODES, [], "zone", 1],
        [_ZONE_NODES, ["a1", "b1", "c1"], "zone", 1],
        [_ZONE_NODES, ["a1", "a1", "a2", "b1", "b1", "b1", "c1"], "zone", 1],
        [_ZONE_NODES, ["a1", "a1", "a2", "b1", "b1", "b1", "c1"], "zone", 2],
        [_ZONE_NODES, ["a1", "a1", "a2", "b1", "b1", "b1", "c1"], "zone", 3],
        [_ZONE_NODES, ["x1", "x1", "x1", "a1"], "zone", 1],
        [_ZONE_NODES, ["a1", "a1", "x1"], "host", 1],
        [_ZONE_NODES, ["a1", "ghost", "ghost"], "zone", 1],
        [_ZONE_NODES, ["a1"], "rack", 1],
        [[], ["a1"], "zone", 1],
        [[{"name": "solo", "labels": {"zone": "a"}}], ["solo", "solo", "solo"], "zone", 1],
        [[{"name": "n%02d" % i, "labels": ({"zone": "z%d" % (i % 4)} if i % 9 else {})} for i in range(40)],
         ["n%02d" % ((i * 7) % 40) for i in range(55)] + ["n01"] * 3, "zone", 2],
    ],
    examples=1,
    wrong_solutions=[
        '''def spreadPlacement(nodes, podNodes, topologyKey, maxSkew):
    domain_of = {}
    counts = {}
    for n in nodes:
        labels = n.get("labels") or {}
        if topologyKey in labels:
            domain_of[n["name"]] = labels[topologyKey]
            counts.setdefault(labels[topologyKey], 0)
    for node_name in podNodes:
        if node_name in domain_of:
            counts[domain_of[node_name]] += 1
    if not counts:
        return [0, []]
    low, high = min(counts.values()), max(counts.values())
    ok = set(d for d, c in counts.items() if c + 1 - high <= maxSkew)
    return [high - low, sorted(name for name, d in domain_of.items() if d in ok)]
''',
        '''def spreadPlacement(nodes, podNodes, topologyKey, maxSkew):
    counts = {}
    for n in nodes:
        if topologyKey in (n.get("labels") or {}):
            counts[n["name"]] = 0
    for node_name in podNodes:
        if node_name in counts:
            counts[node_name] += 1
    if not counts:
        return [0, []]
    low, high = min(counts.values()), max(counts.values())
    return [high - low, sorted(name for name, c in counts.items() if c + 1 - low <= maxSkew)]
''',
        '''def spreadPlacement(nodes, podNodes, topologyKey, maxSkew):
    domain_of = {}
    counts = {}
    for n in nodes:
        d = (n.get("labels") or {}).get(topologyKey, "")
        domain_of[n["name"]] = d
        counts.setdefault(d, 0)
    for node_name in podNodes:
        if node_name in domain_of:
            counts[domain_of[node_name]] += 1
    if not counts:
        return [0, []]
    low, high = min(counts.values()), max(counts.values())
    ok = set(d for d, c in counts.items() if c + 1 - low <= maxSkew)
    return [high - low, sorted(name for name, d in domain_of.items() if d in ok)]
''',
    ],
    guide=dict(
        prereqs="The lesson *Steering the scheduler*, section on topology spread constraints: domains, `topologyKey`, `maxSkew` and "
                "the rule `(count + 1) - lowest <= maxSkew`.",
        intuition="Forget nodes for a moment and think in buckets, one per zone. Count the matching Pods in each bucket. A new Pod may "
                  "go into a bucket only if that bucket would then be at most `maxSkew` above the emptiest bucket. Nodes come back at "
                  "the end: every node in an allowed bucket is eligible.",
        hints=[
            "Build two dictionaries: node name → domain, and domain → count (starting at 0 for every domain that has a node).",
            "Take the minimum over all domains *before* adding the new Pod.",
            "Nodes without the label take no part: do not create an empty-string domain for them.",
        ],
        brute_force="Trying each node, adding a Pod, recomputing every count and measuring the new skew is O(N · (N + P)). Because only "
                    "one domain's count changes, comparing with the current minimum is enough, giving one pass.",
        approach="1. Map each labelled node to its domain and initialise that domain's count to 0.\n"
                 "2. Add 1 to the domain of every Pod whose node is known and labelled.\n"
                 "3. `skew = max - min`.\n4. A domain is allowed when `count + 1 - min <= maxSkew`.\n"
                 "5. Return the sorted names of nodes in allowed domains.\n\n"
                 "**Dry run** (example): domains a → 2, b → 1, c → 0. Minimum 0, maximum 2, skew 2. Zone a: `3 - 0 = 3 > 1`. "
                 "Zone b: `2 - 0 = 2 > 1`. Zone c: `1 - 0 = 1 <= 1`. Eligible: `[\"c1\"]`. Node `x1` has no `zone` label and is ignored.",
        complexity="Time O(N + P + N log N) for the final sort; space O(N).",
        pitfalls="- Comparing with the maximum instead of the minimum, which allows every domain.\n"
                 "- Counting per node when the topology key groups several nodes.\n"
                 "- Treating unlabelled nodes as one extra domain with count 0, which changes the minimum.\n"
                 "- Forgetting domains that have nodes and no Pods: they hold the minimum.\n- Returning domains instead of node names.",
        follow_up="Handle `whenUnsatisfiable: ScheduleAnyway` by returning all labelled nodes ordered by the skew each would produce, "
                  "and add `minDomains`, which treats the global minimum as 0 while fewer than that many domains exist.",
    ),
),
dict(
    id="k8s-pdb-eviction",
    title="PodDisruptionBudget Eviction Decisions",
    difficulty="Medium",
    pattern="Scheduling",
    entry="evictPods",
    description=r"""
`kubectl drain` removes Pods through the Eviction API, which refuses an eviction that would break a PodDisruptionBudget
(PDB). Write `evictPods(pods, pdbs, requests)` that processes eviction requests in order.

- `pods` is a list of `{"name", "labels": {...}, "ready": bool}`.
- Each PDB is `{"selector": {...}, "minAvailable": v}` **or** `{"selector": {...}, "maxUnavailable": v}`, where `v` is an
  integer or a percentage string such as `"50%"`. A PDB covers the Pods whose labels contain every selector pair.
- For a PDB, `expected` is the number of covered Pods **in the original list** (it does not change as Pods are evicted),
  and `healthy` is the number of covered Pods that are ready and not yet evicted.
- `desiredHealthy` is `minAvailable`, or `expected - maxUnavailable`. A percentage means that share of `expected`,
  **rounded up**.
- `requests` is a list of Pod names. For each one, in order:
  - if no such Pod exists (or it was already evicted) the result is `"not-found"`;
  - otherwise the eviction is allowed only if **every** PDB covering the Pod still satisfies
    `healthy >= desiredHealthy` **after** the eviction (evicting a ready Pod lowers `healthy` by one; evicting an unready
    Pod leaves it unchanged);
  - an allowed eviction removes the Pod and gives `"evicted"`; otherwise the Pod stays and the result is `"blocked"`.
  - A Pod covered by no PDB is always evicted.

Return the list of results.

**Example:** four `app=api` Pods of which `api-3` is not ready, PDB `{"selector": {"app": "api"}, "minAvailable": 2}`,
requests `["api-0", "api-1", "api-2"]` → `["evicted", "blocked", "blocked"]` (three healthy; one eviction leaves two).
""",
    starter='''def evictPods(pods, pdbs, requests):
    # return a list with "evicted", "blocked" or "not-found" for each request
    pass
''',
    solution='''def evictPods(pods, pdbs, requests):
    def covers(pdb, pod):
        return all(pod["labels"].get(k) == v for k, v in pdb["selector"].items())

    def resolve(value, expected):
        if isinstance(value, str) and value.endswith("%"):
            return -(-(expected * int(value[:-1])) // 100)
        return value

    budgets = []
    for pdb in pdbs:
        expected = sum(1 for p in pods if covers(pdb, p))
        if "minAvailable" in pdb:
            desired = resolve(pdb["minAvailable"], expected)
        else:
            desired = expected - resolve(pdb["maxUnavailable"], expected)
        budgets.append((pdb, desired))

    alive = {p["name"]: p for p in pods}
    out = []
    for name in requests:
        pod = alive.get(name)
        if pod is None:
            out.append("not-found")
            continue
        allowed = True
        for pdb, desired in budgets:
            if not covers(pdb, pod):
                continue
            healthy = sum(1 for p in alive.values() if p["ready"] and covers(pdb, p))
            if pod["ready"]:
                healthy -= 1
            if healthy < desired:
                allowed = False
                break
        if allowed:
            del alive[name]
            out.append("evicted")
        else:
            out.append("blocked")
    return out
''',
    tests=[
        [_PDB_PODS, [{"selector": {"app": "api"}, "minAvailable": 2}], ["api-0", "api-1", "api-2"]],
        [_PDB_PODS, [], ["api-0", "db-0", "nope", "api-0"]],
        [_PDB_PODS, [{"selector": {"app": "api"}, "maxUnavailable": 1}], ["api-0", "api-1"]],
        [_PDB_PODS, [{"selector": {"app": "api"}, "maxUnavailable": 2}], ["api-0", "api-1"]],
        [_PDB_PODS, [{"selector": {"app": "api"}, "minAvailable": 3}], ["api-3", "api-0"]],
        [_PDB_PODS, [{"selector": {"app": "api"}, "minAvailable": 4}], ["api-3", "api-0"]],
        [_PDB_PODS, [{"selector": {"app": "api"}, "minAvailable": "50%"}], ["api-0", "api-1", "api-2"]],
        [_PDB_PODS, [{"selector": {"app": "api"}, "minAvailable": "60%"}], ["api-0", "api-1"]],
        [_PDB_PODS, [{"selector": {"app": "api"}, "maxUnavailable": "30%"}], ["api-0", "api-1"]],
        [_PDB_PODS, [{"selector": {"app": "db"}, "minAvailable": 1}], ["db-0", "batch-0"]],
        [_PDB_PODS, [{"selector": {"app": "api"}, "minAvailable": 1}, {"selector": {"tier": "backend"}, "minAvailable": 3}],
         ["api-0", "api-1", "db-0"]],
        [_PDB_PODS, [{"selector": {"tier": "backend"}, "minAvailable": 3}, {"selector": {"app": "api"}, "minAvailable": 3}],
         ["db-0", "api-0"]],
        [_PDB_PODS, [{"selector": {}, "maxUnavailable": 2}], ["batch-0", "db-0", "api-0"]],
        [[{"name": "w-%02d" % i, "labels": {"app": "w", "shard": str(i % 3)}, "ready": i % 5 != 0} for i in range(30)],
         [{"selector": {"app": "w"}, "minAvailable": "70%"}, {"selector": {"shard": "0"}, "maxUnavailable": 3}],
         ["w-%02d" % i for i in range(0, 30, 2)]],
    ],
    examples=1,
    wrong_solutions=[
        '''def evictPods(pods, pdbs, requests):
    def covers(pdb, pod):
        return all(pod["labels"].get(k) == v for k, v in pdb["selector"].items())
    def resolve(value, expected):
        if isinstance(value, str) and value.endswith("%"):
            return -(-(expected * int(value[:-1])) // 100)
        return value
    budgets = []
    for pdb in pdbs:
        expected = sum(1 for p in pods if covers(pdb, p))
        desired = resolve(pdb["minAvailable"], expected) if "minAvailable" in pdb else expected - resolve(pdb["maxUnavailable"], expected)
        budgets.append((pdb, desired))
    alive = {p["name"]: p for p in pods}
    out = []
    for name in requests:
        pod = alive.get(name)
        if pod is None:
            out.append("not-found")
            continue
        ok = True
        for pdb, desired in budgets:
            if covers(pdb, pod):
                remaining = sum(1 for p in alive.values() if covers(pdb, p)) - 1
                if remaining < desired:
                    ok = False
        if ok:
            del alive[name]
            out.append("evicted")
        else:
            out.append("blocked")
    return out
''',
        '''def evictPods(pods, pdbs, requests):
    def covers(pdb, pod):
        return all(pod["labels"].get(k) == v for k, v in pdb["selector"].items())
    def resolve(value, expected):
        if isinstance(value, str) and value.endswith("%"):
            return expected * int(value[:-1]) // 100
        return value
    budgets = []
    for pdb in pdbs:
        expected = sum(1 for p in pods if covers(pdb, p))
        desired = resolve(pdb["minAvailable"], expected) if "minAvailable" in pdb else expected - resolve(pdb["maxUnavailable"], expected)
        budgets.append((pdb, desired))
    alive = {p["name"]: p for p in pods}
    out = []
    for name in requests:
        pod = alive.get(name)
        if pod is None:
            out.append("not-found")
            continue
        ok = True
        for pdb, desired in budgets:
            if covers(pdb, pod):
                healthy = sum(1 for p in alive.values() if p["ready"] and covers(pdb, p)) - (1 if pod["ready"] else 0)
                if healthy < desired:
                    ok = False
        if ok:
            del alive[name]
            out.append("evicted")
        else:
            out.append("blocked")
    return out
''',
        '''def evictPods(pods, pdbs, requests):
    def covers(pdb, pod):
        return all(pod["labels"].get(k) == v for k, v in pdb["selector"].items())
    def resolve(value, expected):
        if isinstance(value, str) and value.endswith("%"):
            return -(-(expected * int(value[:-1])) // 100)
        return value
    alive = {p["name"]: p for p in pods}
    out = []
    for name in requests:
        pod = alive.get(name)
        if pod is None:
            out.append("not-found")
            continue
        ok = True
        for pdb in pdbs:
            if covers(pdb, pod):
                expected = sum(1 for p in pods if covers(pdb, p))
                desired = resolve(pdb["minAvailable"], expected) if "minAvailable" in pdb else expected - resolve(pdb["maxUnavailable"], expected)
                healthy = sum(1 for p in alive.values() if p["ready"] and covers(pdb, p)) - (1 if pod["ready"] else 0)
                ok = healthy >= desired
                break
        if ok:
            del alive[name]
            out.append("evicted")
        else:
            out.append("blocked")
    return out
''',
    ],
    guide=dict(
        prereqs="The lesson *Steering the scheduler*, section on disruptions and PodDisruptionBudgets: voluntary disruptions, "
                "`minAvailable`, `maxUnavailable`, and how `kubectl drain` uses the Eviction API.",
        intuition="A budget is a floor on healthy Pods. Each eviction request asks one question per covering budget: if this Pod "
                  "goes, are there still enough healthy ones? Unready Pods do not count as healthy, so they shrink the room for "
                  "evictions without being evicted themselves, and removing one of them does not lower the healthy count.",
        hints=[
            "Compute `desiredHealthy` for each PDB once, up front, from the original list.",
            "Keep a dictionary of Pods that are still present and recount `healthy` for each request.",
            "A Pod can be covered by several PDBs. One refusal is enough to block.",
        ],
        brute_force="Recounting healthy Pods for every request and every PDB is O(R · B · P). Keeping a running healthy counter per "
                    "PDB reduces it to O(R · B), which matters only for very large inputs.",
        approach="1. For each PDB: `expected` = covered Pods in the original list; `desired` = `minAvailable` or "
                 "`expected - maxUnavailable`, percentages rounded up with integer arithmetic.\n"
                 "2. For each request: missing Pod → `not-found`.\n"
                 "3. For each covering PDB: `healthy` = ready covered Pods still present, minus 1 if the target is ready. "
                 "If `healthy < desired`, block.\n4. Otherwise delete the Pod and record `evicted`.\n\n"
                 "**Dry run** (example): expected 4, desired 2, healthy 3 (`api-3` is unready). Evict `api-0`: 3 - 1 = 2 ≥ 2, "
                 "evicted. Evict `api-1`: healthy is now 2; 2 - 1 = 1 < 2, blocked. Same for `api-2`.",
        complexity="Time O(R · B · P) as written, space O(P + B).",
        pitfalls="- Counting unready Pods as healthy.\n- Rounding percentages down.\n"
                 "- Recomputing `expected` after evictions, which makes percentage budgets drift.\n"
                 "- Checking only the first covering PDB.\n- Removing a Pod whose eviction was blocked.\n"
                 "- Forgetting that an empty selector covers every Pod.",
        follow_up="Simulate a full `kubectl drain`: blocked Pods are retried after a controller has created a ready replacement on "
                  "another node. Report how many rounds the drain takes, or that it can never finish.",
    ),
),
dict(
    id="k8s-taint-toleration",
    title="Taints, Tolerations and Eviction Timing",
    difficulty="Medium",
    pattern="Scheduling",
    entry="taintEffects",
    description=r"""
Taints affect a Pod at two moments: when it is scheduled, and while it runs. Write `taintEffects(taints, tolerations)`
returning `[canSchedule, evictAfter]` for one Pod and one node.

- A taint is `{"key", "value", "effect"}` with effect `NoSchedule`, `PreferNoSchedule` or `NoExecute`.
- A toleration is `{"key", "operator", "value", "effect", "tolerationSeconds"}`; any field may be missing.
  It tolerates a taint when all three hold:
  - **key**: equal keys, or the toleration has no key (or `""`) and its operator is `Exists`;
  - **value**: operator `Exists`, or operator `Equal` (the default) with equal values (a missing value is `""`);
  - **effect**: the toleration has no effect (or `""`), or the effects are equal.
- `canSchedule` is `True` when every `NoSchedule` and every `NoExecute` taint is tolerated. `PreferNoSchedule` never blocks.
- `evictAfter` describes a Pod that is **already running** on the node when these taints are present. Only `NoExecute`
  taints matter:
  - if some `NoExecute` taint is not tolerated: `0` (evicted immediately);
  - otherwise, for each `NoExecute` taint take the **first** toleration in the list that tolerates it. If none of those
    has `tolerationSeconds`, the result is `-1` (the Pod stays). Otherwise it is the smallest `tolerationSeconds` among
    them, with negative values treated as `0`.
  - with no `NoExecute` taints at all: `-1`.

**Example:** taints `[{"key": "node.kubernetes.io/unreachable", "effect": "NoExecute"}]`, tolerations
`[{"key": "node.kubernetes.io/unreachable", "operator": "Exists", "effect": "NoExecute", "tolerationSeconds": 300}]`
→ `[True, 300]`
""",
    starter='''def taintEffects(taints, tolerations):
    # return [canSchedule, evictAfter]
    pass
''',
    solution='''def taintEffects(taints, tolerations):
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

    def first_match(taint):
        for tol in tolerations:
            if tolerates(tol, taint):
                return tol
        return None

    can_schedule = True
    evict_after = -1
    for taint in taints:
        effect = taint.get("effect")
        if effect not in ("NoSchedule", "NoExecute"):
            continue
        tol = first_match(taint)
        if tol is None:
            can_schedule = False
            if effect == "NoExecute":
                evict_after = 0
            continue
        if effect == "NoExecute" and tol.get("tolerationSeconds") is not None:
            seconds = max(0, tol["tolerationSeconds"])
            if evict_after == -1 or seconds < evict_after:
                evict_after = seconds
    return [can_schedule, evict_after]
''',
    tests=[
        [[{"key": "node.kubernetes.io/unreachable", "effect": "NoExecute"}],
         [{"key": "node.kubernetes.io/unreachable", "operator": "Exists", "effect": "NoExecute", "tolerationSeconds": 300}]],
        [[], []],
        [[{"key": "dedicated", "value": "ml", "effect": "NoSchedule"}], []],
        [[{"key": "dedicated", "value": "ml", "effect": "NoSchedule"}], [{"key": "dedicated", "value": "ml"}]],
        [[{"key": "dedicated", "value": "ml", "effect": "NoSchedule"}], [{"key": "dedicated", "value": "web"}]],
        [[{"key": "old", "value": "true", "effect": "PreferNoSchedule"}], []],
        [[{"key": "maint", "value": "", "effect": "NoExecute"}], []],
        [[{"key": "maint", "value": "", "effect": "NoExecute"}], [{"key": "maint", "operator": "Exists"}]],
        [[{"key": "maint", "value": "", "effect": "NoExecute"}], [{"key": "maint", "operator": "Exists", "effect": "NoSchedule"}]],
        [[{"key": "a", "value": "1", "effect": "NoExecute"}, {"key": "b", "value": "1", "effect": "NoExecute"}],
         [{"key": "a", "value": "1", "tolerationSeconds": 600}, {"key": "b", "value": "1", "tolerationSeconds": 60}]],
        [[{"key": "a", "value": "1", "effect": "NoExecute"}, {"key": "b", "value": "1", "effect": "NoExecute"}],
         [{"key": "a", "value": "1", "tolerationSeconds": 600}]],
        [[{"key": "a", "value": "1", "effect": "NoExecute"}],
         [{"key": "a", "operator": "Exists", "tolerationSeconds": 30}, {"key": "a", "value": "1"}]],
        [[{"key": "a", "value": "1", "effect": "NoExecute"}],
         [{"key": "a", "value": "1"}, {"key": "a", "operator": "Exists", "tolerationSeconds": 30}]],
        [[{"key": "a", "value": "1", "effect": "NoExecute"}, {"key": "gpu", "value": "x", "effect": "NoSchedule"}],
         [{"operator": "Exists", "tolerationSeconds": -5}]],
        [[{"key": "a", "value": "1", "effect": "NoSchedule"}, {"key": "b", "value": "2", "effect": "NoExecute"}],
         [{"key": "", "operator": "Equal", "value": "1"}, {"key": "b", "value": "2", "effect": "NoExecute", "tolerationSeconds": 0}]],
    ],
    examples=1,
    wrong_solutions=[
        '''def taintEffects(taints, tolerations):
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
        return True
    can, after = True, -1
    for taint in taints:
        if taint.get("effect") not in ("NoSchedule", "NoExecute"):
            continue
        tol = next((t for t in tolerations if tolerates(t, taint)), None)
        if tol is None:
            can = False
            if taint["effect"] == "NoExecute":
                after = 0
        elif taint["effect"] == "NoExecute" and tol.get("tolerationSeconds") is not None:
            s = max(0, tol["tolerationSeconds"])
            after = s if after == -1 else min(after, s)
    return [can, after]
''',
        '''def taintEffects(taints, tolerations):
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
    can, after = True, -1
    for taint in taints:
        if taint.get("effect") not in ("NoSchedule", "NoExecute"):
            continue
        matching = [t for t in tolerations if tolerates(t, taint)]
        if not matching:
            can = False
            if taint["effect"] == "NoExecute":
                after = 0
        elif taint["effect"] == "NoExecute":
            for tol in matching:
                if tol.get("tolerationSeconds") is not None:
                    after = max(after, max(0, tol["tolerationSeconds"]))
    return [can, after]
''',
        '''def taintEffects(taints, tolerations):
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
    can, after = True, -1
    for taint in taints:
        tol = next((t for t in tolerations if tolerates(t, taint)), None)
        if tol is None:
            can = False
            if taint.get("effect") == "NoExecute":
                after = 0
        elif taint.get("effect") == "NoExecute" and tol.get("tolerationSeconds") is not None:
            s = max(0, tol["tolerationSeconds"])
            after = s if after == -1 else min(after, s)
    return [can, after]
''',
    ],
    guide=dict(
        prereqs="The lesson *Steering the scheduler*, section on taints and tolerations: the three effects, the `Equal` and `Exists` "
                "operators, and `tolerationSeconds` on `NoExecute` taints (the mechanism behind the five-minute delay before Pods "
                "leave an unreachable node).",
        intuition="There are two separate questions. May the Pod be placed here? That needs every hard taint tolerated. And if it is "
                  "already here, how long may it stay? That concerns `NoExecute` taints only: an untolerated one evicts at once, a "
                  "tolerated one with a time limit starts a countdown, and several countdowns mean the shortest wins.",
        hints=[
            "Start with `tolerates(toleration, taint)`: three independent checks for key, value and effect.",
            "For each hard taint find the first toleration that tolerates it. `None` means not tolerated.",
            "Keep `evictAfter` at -1 until a `NoExecute` taint forces a number; then take minimums, with 0 as the floor.",
        ],
        brute_force="Comparing every taint with every toleration is O(T · K), and nothing better is needed for lists this small.",
        approach="1. Skip `PreferNoSchedule` taints.\n2. For each remaining taint, find the first tolerating toleration.\n"
                 "3. None found: `canSchedule = False`; if the taint is `NoExecute`, `evictAfter = 0`.\n"
                 "4. Found, taint is `NoExecute`, toleration has `tolerationSeconds`: `evictAfter` becomes the minimum seen "
                 "(negative values count as 0).\n5. Return both.\n\n"
                 "**Dry run:** taints `a=1:NoExecute` and `b=1:NoExecute`; tolerations for `a` with 600 seconds and for `b` with 60. "
                 "Both tolerated, so `canSchedule` is `True`. Countdown candidates 600 and 60, minimum 60. Result `[True, 60]`.",
        complexity="Time O(T · K) for T taints and K tolerations, space O(1).",
        pitfalls="- Ignoring the toleration's effect, so a `NoSchedule` toleration wrongly covers a `NoExecute` taint.\n"
                 "- Treating `PreferNoSchedule` as blocking.\n- Taking the largest `tolerationSeconds` instead of the smallest.\n"
                 "- Considering every matching toleration instead of the first one for each taint.\n"
                 "- Returning 0 when the Pod should stay for ever (-1), or the reverse.\n"
                 "- An empty key with operator `Equal` matches nothing.",
        follow_up="Given a timeline of taints being added to and removed from a node, compute the moment a running Pod is evicted, "
                  "remembering that removing the taint before the countdown ends cancels the eviction.",
    ),
),
dict(
    id="k8s-manifest-lint",
    title="Manifest Linter",
    difficulty="Medium",
    pattern="Packaging & Delivery",
    entry="lintManifests",
    description=r"""
Helm and Kustomize render manifests; neither checks that the result makes sense. Write `lintManifests(objects)` that
inspects a rendered list of Deployments and Services and returns the **sorted** list of problems found.

Objects look like real manifests reduced to the fields used here:

- Deployment: `metadata.name`, optional `metadata.namespace` (default `"default"`), `spec.selector.matchLabels`,
  `spec.template.metadata.labels`, and `spec.template.spec.containers`, each `{"name", "image", "ports":
  [{"containerPort": n}], "resources": {"requests": {"cpu", "memory"}}}` (`ports` and `resources` may be missing).
- Service: `metadata.name`, optional `metadata.namespace`, `spec.selector`, `spec.ports` with integer `targetPort`s.

Report these problems, using exactly these strings:

1. `deployment/NS/NAME: selector does not match template labels` — some `matchLabels` pair is missing from the template's labels.
2. `deployment/NS/NAME: container C has an unpinned image` — the image has no tag, or the tag is `latest`. An image
   with a digest (`@sha256:...`) is pinned. The tag is what follows the last `:` in the part after the last `/`
   (so `registry:5000/app` has **no** tag).
3. `deployment/NS/NAME: container C has no resource requests` — `resources.requests` lacks `cpu` or `memory`.
4. `service/NS/NAME: selector matches no deployment` — no Deployment **in the same namespace** has template labels
   containing every selector pair. An empty selector matches nothing.
5. `service/NS/NAME: targetPort P is not exposed` — the Service matches at least one Deployment, and no container of
   any matched Deployment lists `containerPort` P. (Skip this check when problem 4 was reported.)

**Example:** a Deployment `orders` with image `orders-api:latest` and a Service `orders` whose `targetPort` is 80 while
the container exposes 8080 → `["deployment/default/orders: container api has an unpinned image",
"service/default/orders: targetPort 80 is not exposed"]`
""",
    starter='''def lintManifests(objects):
    # return the sorted list of problem strings
    pass
''',
    solution='''def lintManifests(objects):
    def ns_of(obj):
        return obj["metadata"].get("namespace") or "default"

    def pinned(image):
        if "@" in image:
            return True
        last = image.rsplit("/", 1)[-1]
        if ":" not in last:
            return False
        return last.rsplit(":", 1)[1] not in ("", "latest")

    problems = []
    deployments = [o for o in objects if o.get("kind") == "Deployment"]
    for d in deployments:
        ident = "deployment/%s/%s" % (ns_of(d), d["metadata"]["name"])
        template = d["spec"]["template"]
        labels = (template.get("metadata") or {}).get("labels") or {}
        selector = (d["spec"].get("selector") or {}).get("matchLabels") or {}
        if any(labels.get(k) != v for k, v in selector.items()):
            problems.append(ident + ": selector does not match template labels")
        for c in template["spec"]["containers"]:
            if not pinned(c["image"]):
                problems.append("%s: container %s has an unpinned image" % (ident, c["name"]))
            requests = (c.get("resources") or {}).get("requests") or {}
            if "cpu" not in requests or "memory" not in requests:
                problems.append("%s: container %s has no resource requests" % (ident, c["name"]))
    for s in objects:
        if s.get("kind") != "Service":
            continue
        ident = "service/%s/%s" % (ns_of(s), s["metadata"]["name"])
        selector = s["spec"].get("selector") or {}
        matched = []
        if selector:
            for d in deployments:
                labels = (d["spec"]["template"].get("metadata") or {}).get("labels") or {}
                if ns_of(d) == ns_of(s) and all(labels.get(k) == v for k, v in selector.items()):
                    matched.append(d)
        if not matched:
            problems.append(ident + ": selector matches no deployment")
            continue
        exposed = set()
        for d in matched:
            for c in d["spec"]["template"]["spec"]["containers"]:
                for p in c.get("ports") or []:
                    exposed.add(p["containerPort"])
        for port in s["spec"].get("ports") or []:
            if port["targetPort"] not in exposed:
                problems.append("%s: targetPort %s is not exposed" % (ident, port["targetPort"]))
    return sorted(problems)
''',
    tests=[
        [[_deploy("orders", {"app": "orders"}, {"app": "orders"}, [_ctr("api", "orders-api:latest")]),
          _svc("orders", {"app": "orders"}, [(80, 80)])]],
        [[_GOOD_DEPLOY, _GOOD_SVC]],
        [[]],
        [[_deploy("web", {"app": "web", "tier": "front"}, {"app": "web"}, [_ctr("web", "web:1.0")])]],
        [[_deploy("web", {"app": "web"}, {"app": "web", "tier": "front"}, [_ctr("web", "web:1.0")])]],
        [[_deploy("imgs", {"a": "b"}, {"a": "b"}, [_ctr("c1", "nginx"), _ctr("c2", "registry:5000/app"),
                                                   _ctr("c3", "registry:5000/app:1.2"), _ctr("c4", "app@sha256:abc123"),
                                                   _ctr("c5", "ghcr.io/x/y:latest"), _ctr("c6", "ghcr.io/x/y:v1")])]],
        [[_deploy("res", {"a": "b"}, {"a": "b"}, [_ctr("no-mem", "x:1", memory=None), _ctr("no-cpu", "x:1", cpu=None),
                                                  _ctr("none", "x:1", cpu=None, memory=None), _ctr("ok", "x:1")])]],
        [[_GOOD_DEPLOY, _svc("typo", {"app": "order"}, [(80, 8080)])]],
        [[_GOOD_DEPLOY, _svc("strict", {"app": "orders", "version": "v2"}, [(80, 8080)])]],
        [[_GOOD_DEPLOY, _svc("empty", {}, [(80, 8080)])]],
        [[_deploy("orders", {"app": "orders"}, {"app": "orders"}, [_ctr("api", "o:1")], ns="cafe"),
          _svc("orders", {"app": "orders"}, [(80, 8080)], ns="cafe-prod"),
          _svc("orders", {"app": "orders"}, [(80, 8080)], ns="cafe")]],
        [[_deploy("multi", {"app": "m"}, {"app": "m"}, [_ctr("a", "a:1", ports=(8080,)), _ctr("b", "b:1", ports=(9090, 9091))]),
          _svc("multi", {"app": "m"}, [(80, 8080), (81, 9091), (82, 7000), (83, 9090)])]],
        [[_deploy("one", {"app": "shared"}, {"app": "shared", "v": "1"}, [_ctr("a", "a:1", ports=(8000,))]),
          _deploy("two", {"app": "shared"}, {"app": "shared", "v": "2"}, [_ctr("a", "a:2", ports=(9000,))]),
          _svc("both", {"app": "shared"}, [(80, 9000), (81, 8000)]),
          _svc("v1-only", {"app": "shared", "v": "1"}, [(80, 9000)])]],
        [[_deploy("noports", {"app": "np"}, {"app": "np"}, [{"name": "c", "image": "c", "resources": {"requests": {"cpu": "1"}}}]),
          _svc("noports", {"app": "np"}, [(80, 8080)])]],
    ],
    examples=1,
    wrong_solutions=[
        '''def lintManifests(objects):
    def ns_of(obj):
        return obj["metadata"].get("namespace") or "default"
    def pinned(image):
        if "@" in image:
            return True
        if ":" not in image:
            return False
        return image.rsplit(":", 1)[1] not in ("", "latest")
    problems = []
    deployments = [o for o in objects if o.get("kind") == "Deployment"]
    for d in deployments:
        ident = "deployment/%s/%s" % (ns_of(d), d["metadata"]["name"])
        template = d["spec"]["template"]
        labels = (template.get("metadata") or {}).get("labels") or {}
        selector = (d["spec"].get("selector") or {}).get("matchLabels") or {}
        if any(labels.get(k) != v for k, v in selector.items()):
            problems.append(ident + ": selector does not match template labels")
        for c in template["spec"]["containers"]:
            if not pinned(c["image"]):
                problems.append("%s: container %s has an unpinned image" % (ident, c["name"]))
            requests = (c.get("resources") or {}).get("requests") or {}
            if "cpu" not in requests or "memory" not in requests:
                problems.append("%s: container %s has no resource requests" % (ident, c["name"]))
    for s in objects:
        if s.get("kind") != "Service":
            continue
        ident = "service/%s/%s" % (ns_of(s), s["metadata"]["name"])
        selector = s["spec"].get("selector") or {}
        matched = [d for d in deployments if selector and ns_of(d) == ns_of(s) and
                   all(((d["spec"]["template"].get("metadata") or {}).get("labels") or {}).get(k) == v for k, v in selector.items())]
        if not matched:
            problems.append(ident + ": selector matches no deployment")
            continue
        exposed = set(p["containerPort"] for d in matched for c in d["spec"]["template"]["spec"]["containers"] for p in c.get("ports") or [])
        for port in s["spec"].get("ports") or []:
            if port["targetPort"] not in exposed:
                problems.append("%s: targetPort %s is not exposed" % (ident, port["targetPort"]))
    return sorted(problems)
''',
        '''def lintManifests(objects):
    def ns_of(obj):
        return obj["metadata"].get("namespace") or "default"
    def pinned(image):
        if "@" in image:
            return True
        last = image.rsplit("/", 1)[-1]
        if ":" not in last:
            return False
        return last.rsplit(":", 1)[1] not in ("", "latest")
    problems = []
    deployments = [o for o in objects if o.get("kind") == "Deployment"]
    for d in deployments:
        ident = "deployment/%s/%s" % (ns_of(d), d["metadata"]["name"])
        template = d["spec"]["template"]
        labels = (template.get("metadata") or {}).get("labels") or {}
        selector = (d["spec"].get("selector") or {}).get("matchLabels") or {}
        if labels != selector:
            problems.append(ident + ": selector does not match template labels")
        for c in template["spec"]["containers"]:
            if not pinned(c["image"]):
                problems.append("%s: container %s has an unpinned image" % (ident, c["name"]))
            requests = (c.get("resources") or {}).get("requests") or {}
            if "cpu" not in requests or "memory" not in requests:
                problems.append("%s: container %s has no resource requests" % (ident, c["name"]))
    for s in objects:
        if s.get("kind") != "Service":
            continue
        ident = "service/%s/%s" % (ns_of(s), s["metadata"]["name"])
        selector = s["spec"].get("selector") or {}
        matched = [d for d in deployments if selector and ns_of(d) == ns_of(s) and
                   all(((d["spec"]["template"].get("metadata") or {}).get("labels") or {}).get(k) == v for k, v in selector.items())]
        if not matched:
            problems.append(ident + ": selector matches no deployment")
            continue
        exposed = set(p["containerPort"] for d in matched for c in d["spec"]["template"]["spec"]["containers"] for p in c.get("ports") or [])
        for port in s["spec"].get("ports") or []:
            if port["targetPort"] not in exposed:
                problems.append("%s: targetPort %s is not exposed" % (ident, port["targetPort"]))
    return sorted(problems)
''',
        '''def lintManifests(objects):
    def ns_of(obj):
        return obj["metadata"].get("namespace") or "default"
    def pinned(image):
        if "@" in image:
            return True
        last = image.rsplit("/", 1)[-1]
        if ":" not in last:
            return False
        return last.rsplit(":", 1)[1] not in ("", "latest")
    problems = []
    deployments = [o for o in objects if o.get("kind") == "Deployment"]
    for d in deployments:
        ident = "deployment/%s/%s" % (ns_of(d), d["metadata"]["name"])
        template = d["spec"]["template"]
        labels = (template.get("metadata") or {}).get("labels") or {}
        selector = (d["spec"].get("selector") or {}).get("matchLabels") or {}
        if any(labels.get(k) != v for k, v in selector.items()):
            problems.append(ident + ": selector does not match template labels")
        for c in template["spec"]["containers"]:
            if not pinned(c["image"]):
                problems.append("%s: container %s has an unpinned image" % (ident, c["name"]))
            requests = (c.get("resources") or {}).get("requests") or {}
            if "cpu" not in requests or "memory" not in requests:
                problems.append("%s: container %s has no resource requests" % (ident, c["name"]))
    for s in objects:
        if s.get("kind") != "Service":
            continue
        ident = "service/%s/%s" % (ns_of(s), s["metadata"]["name"])
        selector = s["spec"].get("selector") or {}
        matched = [d for d in deployments if selector and
                   all(((d["spec"]["template"].get("metadata") or {}).get("labels") or {}).get(k) == v for k, v in selector.items())]
        if not matched:
            problems.append(ident + ": selector matches no deployment")
            continue
        exposed = set(p["containerPort"] for d in matched for c in d["spec"]["template"]["spec"]["containers"] for p in c.get("ports") or [])
        for port in s["spec"].get("ports") or []:
            if port["targetPort"] not in exposed:
                problems.append("%s: targetPort %s is not exposed" % (ident, port["targetPort"]))
    return sorted(problems)
''',
    ],
    guide=dict(
        prereqs="The lesson *Helm and Kustomize* (rendered output still needs checking) and the earlier lessons on Deployments "
                "(selector and template labels) and Services (selector, `port` and `targetPort`).",
        intuition="Each rule is a small question about dictionaries: is this set of labels contained in that one, does this string "
                  "end in a real tag, is this number among those. The work is in walking the nested structure carefully and in "
                  "getting the edge cases of each rule right.",
        hints=[
            "Write small helpers: `ns_of(obj)`, `pinned(image)`, and a subset test for labels.",
            "For the image tag, first cut everything up to the last `/`, then look for `:` in what remains.",
            "For a Service, collect the matched Deployments first. If there are none, report that and skip the port check.",
        ],
        brute_force="Comparing every Service with every Deployment is O(S · D) and is the natural solution. Indexing Deployments by "
                    "namespace helps only with thousands of objects.",
        approach="1. For each Deployment: selector ⊆ template labels; then each container's image and requests.\n"
                 "2. For each Service: find same-namespace Deployments whose template labels contain the selector (an empty "
                 "selector matches nothing).\n3. No match → one problem. Otherwise gather every `containerPort` of the matched "
                 "Deployments and report each `targetPort` not among them.\n4. Sort the strings.\n\n"
                 "**Dry run** (example): Deployment `orders`: selector `{app: orders}` is contained in the labels, fine. Image "
                 "`orders-api:latest`: last segment `orders-api:latest`, tag `latest`, unpinned. Requests present. Service "
                 "`orders`: matches the Deployment; exposed ports `{8080}`; `targetPort` 80 is not there. Two problems, sorted.",
        complexity="Time O(D · C + S · D · C) for D Deployments with C containers and S Services, plus the sort; space O(problems).",
        pitfalls="- Requiring the selector to *equal* the template labels; extra template labels are normal.\n"
                 "- Reading the port of `registry:5000/app` as a tag.\n- Treating a digest reference as unpinned.\n"
                 "- Matching Services against Deployments in other namespaces.\n- Letting an empty Service selector match everything.\n"
                 "- Reporting port problems for a Service that matched nothing.\n- Forgetting to sort.",
        follow_up="Add rules for probes (every container needs a readiness probe), for `replicas` left in a Deployment that an "
                  "HPA targets, and for named `targetPort`s that must match a container port's `name`.",
    ),
),
dict(
    id="k8s-gpu-bin-packing",
    title="GPU Placement: Spread or Pack",
    difficulty="Medium",
    pattern="Kubernetes for ML",
    entry="placeGpuJobs",
    description=r"""
GPUs are whole, scarce devices, so the order and strategy of placement decide whether large jobs can run at all.
Write `placeGpuJobs(nodes, jobs, strategy)`.

- `nodes` is a list of `[name, gpus]`: each node's name and its number of GPUs, all free at the start.
- `jobs` is a list of `[name, gpus]` in arrival order. A job needs all its GPUs on **one** node.
- Place the jobs one at a time. The candidates for a job are the nodes with at least that many free GPUs.
  - `strategy == "spread"`: choose the candidate with the **most** free GPUs.
  - `strategy == "pack"`: choose the candidate with the **fewest** free GPUs (the tightest fit).
  - Ties go to the node that appears first in `nodes`.
- A job with no candidate is Pending: it gets `""`, uses nothing and is not retried.

Return the list of chosen node names, one per job, in job order.

**Example:** three nodes with 4 GPUs each, six 1-GPU jobs and then one 4-GPU job. With `"spread"` every node ends up
with 2 free GPUs and the last job is Pending (`""`). With `"pack"` the small jobs fill `n1` and half of `n2`, and the
last job lands on `n3`.
""",
    starter='''def placeGpuJobs(nodes, jobs, strategy):
    # return the node name chosen for each job, "" when it stays Pending
    pass
''',
    solution='''def placeGpuJobs(nodes, jobs, strategy):
    free = [gpus for _, gpus in nodes]
    out = []
    for _, need in jobs:
        chosen = -1
        for i in range(len(nodes)):
            if free[i] < need:
                continue
            if chosen == -1:
                chosen = i
            elif strategy == "spread" and free[i] > free[chosen]:
                chosen = i
            elif strategy == "pack" and free[i] < free[chosen]:
                chosen = i
        if chosen == -1:
            out.append("")
        else:
            free[chosen] -= need
            out.append(nodes[chosen][0])
    return out
''',
    tests=[
        [[["n1", 4], ["n2", 4], ["n3", 4]], [["s%d" % i, 1] for i in range(6)] + [["big", 4]], "spread"],
        [[["n1", 4], ["n2", 4], ["n3", 4]], [["s%d" % i, 1] for i in range(6)] + [["big", 4]], "pack"],
        [[], [["a", 1]], "pack"],
        [[["n1", 2]], [], "spread"],
        [[["n1", 2]], [["a", 3], ["b", 2], ["c", 1]], "pack"],
        [[["big", 8], ["small", 2]], [["a", 1], ["b", 1], ["c", 2]], "pack"],
        [[["big", 8], ["small", 2]], [["a", 1], ["b", 1], ["c", 2]], "spread"],
        [[["a", 8], ["b", 2]], [["j1", 4], ["j2", 1], ["j3", 1], ["j4", 4], ["j5", 1]], "pack"],
        [[["a", 8], ["b", 2]], [["j1", 4], ["j2", 1], ["j3", 1], ["j4", 4], ["j5", 1]], "spread"],
        [[["x", 4], ["y", 4]], [["j1", 2], ["j2", 2], ["j3", 4], ["j4", 4]], "pack"],
        [[["x", 4], ["y", 4]], [["j1", 2], ["j2", 2], ["j3", 4], ["j4", 4]], "spread"],
        [[["x", 2], ["y", 2], ["z", 2]], [["j1", 2], ["j2", 0], ["j3", 2], ["j4", 2], ["j5", 0], ["j6", 1]], "pack"],
        [[["n%02d" % i, 1 + (i * 3) % 8] for i in range(25)], [["j%03d" % i, 1 + (i * 5) % 4] for i in range(60)], "pack"],
        [[["n%02d" % i, 1 + (i * 3) % 8] for i in range(25)], [["j%03d" % i, 1 + (i * 5) % 4] for i in range(60)], "spread"],
    ],
    examples=2,
    wrong_solutions=[
        '''def placeGpuJobs(nodes, jobs, strategy):
    free = [g for _, g in nodes]
    out = []
    for _, need in jobs:
        for i in range(len(nodes)):
            if free[i] >= need:
                free[i] -= need
                out.append(nodes[i][0])
                break
        else:
            out.append("")
    return out
''',
        '''def placeGpuJobs(nodes, jobs, strategy):
    free = [g for _, g in nodes]
    used = [0 for _ in nodes]
    out = []
    for _, need in jobs:
        chosen = -1
        for i in range(len(nodes)):
            if free[i] < need:
                continue
            if chosen == -1:
                chosen = i
            elif strategy == "spread" and used[i] < used[chosen]:
                chosen = i
            elif strategy == "pack" and used[i] > used[chosen]:
                chosen = i
        if chosen == -1:
            out.append("")
        else:
            free[chosen] -= need
            used[chosen] += need
            out.append(nodes[chosen][0])
    return out
''',
        '''def placeGpuJobs(nodes, jobs, strategy):
    free = [g for _, g in nodes]
    out = []
    for _, need in jobs:
        chosen = -1
        for i in range(len(nodes)):
            if free[i] < need:
                continue
            if chosen == -1:
                chosen = i
            elif strategy == "spread" and free[i] >= free[chosen]:
                chosen = i
            elif strategy == "pack" and free[i] <= free[chosen]:
                chosen = i
        if chosen == -1:
            out.append("")
        else:
            free[chosen] -= need
            out.append(nodes[chosen][0])
    return out
''',
    ],
    guide=dict(
        prereqs="The lesson *GPU scheduling*: GPUs as whole-number extended resources, fragmentation, and why GPU clusters prefer "
                "bin packing to the scheduler's default spreading.",
        intuition="Spreading keeps every node partly free, which is kind to small jobs and fatal to large ones: the free GPUs exist "
                  "and are scattered. Packing fills one node before touching the next, so whole nodes stay empty for jobs that need "
                  "many GPUs together. The two strategies differ in a single comparison.",
        hints=[
            "Keep a list of free GPUs per node, in the same order as `nodes`.",
            "Scan the nodes once per job, remembering the best candidate seen so far.",
            "Use a strict comparison (`>` or `<`) when replacing the best candidate, so that the earliest node wins ties.",
        ],
        brute_force="The scan is O(N) per job, O(N · J) in total, which is fine here. A real scheduler with thousands of nodes keeps "
                    "candidates in a structure ordered by free capacity.",
        approach="1. `free[i] = gpus of node i`.\n2. For each job: among nodes with `free >= need`, pick by strategy, earliest on ties.\n"
                 "3. No candidate → `\"\"`. Otherwise subtract and record the name.\n\n"
                 "**Dry run** (`pack`, nodes `big` 8 and `small` 2; jobs 1, 1, 2): job a: candidates big (8 free) and small (2 free); "
                 "fewest free is `small`. Job b: small has 1 free, still the fewest: `small`. Job c needs 2: small has 0, so `big`. "
                 "Result `[\"small\", \"small\", \"big\"]`, and `big` keeps 6 GPUs together for a large job.",
        complexity="Time O(N · J), space O(N + J).",
        pitfalls="- First-fit, which ignores the strategy.\n"
                 "- Packing by 'most GPUs in use' instead of 'fewest free': they differ when nodes have different sizes.\n"
                 "- Using `>=` or `<=` and so letting a later node win a tie.\n"
                 "- Splitting a job across nodes.\n- Retrying or reserving for Pending jobs.\n- A job needing 0 GPUs still goes through the same rule.",
        follow_up="Allow each job to be retried when capacity frees up, add job durations, and compare the average waiting time of "
                  "large jobs under both strategies. Then add gang scheduling for jobs made of several Pods.",
    ),
),
]
