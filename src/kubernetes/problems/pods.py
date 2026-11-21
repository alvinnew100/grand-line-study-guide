PROBLEMS = [
dict(
    id="k8s-pod-phase",
    title="Pod Phase and Status from Container States",
    difficulty="Medium",
    pattern="Pods",
    entry="podStatus",
    description=r"""
`kubectl get pods` shows a `STATUS` such as `CrashLoopBackOff`, while the Pod's real **phase** is one of only a few
values. Write `podStatus(pod)` returning `[phase, status]` using this simplified model.

`pod` is `{"nodeName": str or None, "restartPolicy": "Always" | "OnFailure" | "Never", "containers": [...]}` and each
container is `{"state": "waiting" | "running" | "terminated", "reason": str (optional), "exitCode": int (terminated only)}`.
There is at least one container.

A terminated container **will restart** if the policy is `Always`, or the policy is `OnFailure` and its exit code is not 0.

Rules, in order:

1. `nodeName` is `None` → `["Pending", "Pending"]`.
2. Every container is terminated and none will restart → the Pod is finished:
   - all exit codes 0 → `["Succeeded", "Completed"]`
   - otherwise → `["Failed", r]` where `r` is the `reason` of the first container with a non-zero exit code, or `"Error"`
     if it has no reason.
3. Otherwise the phase is `"Running"` if any container is running, **or** any terminated container will restart, **or**
   any waiting container has reason `"CrashLoopBackOff"`. If none of those hold, the phase is `"Pending"`.
4. For an unfinished Pod, the status is the `reason` of the first waiting container that has a non-empty reason; if there
   is none, the status equals the phase.

**Example:** scheduled, policy `Always`, one container waiting with reason `CrashLoopBackOff`
→ `["Running", "CrashLoopBackOff"]`
""",
    starter='''def podStatus(pod):
    # return [phase, status]
    pass
''',
    solution='''def podStatus(pod):
    if pod.get("nodeName") is None:
        return ["Pending", "Pending"]
    policy = pod["restartPolicy"]
    containers = pod["containers"]

    def will_restart(c):
        return policy == "Always" or (policy == "OnFailure" and c.get("exitCode", 0) != 0)

    terminated = [c for c in containers if c["state"] == "terminated"]
    if len(terminated) == len(containers) and not any(will_restart(c) for c in terminated):
        failed = [c for c in containers if c.get("exitCode", 0) != 0]
        if not failed:
            return ["Succeeded", "Completed"]
        return ["Failed", failed[0].get("reason") or "Error"]
    running = any(c["state"] == "running" for c in containers)
    restarting = any(will_restart(c) for c in terminated)
    crashloop = any(c["state"] == "waiting" and c.get("reason") == "CrashLoopBackOff" for c in containers)
    phase = "Running" if (running or restarting or crashloop) else "Pending"
    for c in containers:
        if c["state"] == "waiting" and c.get("reason"):
            return [phase, c["reason"]]
    return [phase, phase]
''',
    tests=[
        [{"nodeName": "n1", "restartPolicy": "Always", "containers": [{"state": "waiting", "reason": "CrashLoopBackOff"}]}],
        [{"nodeName": None, "restartPolicy": "Always", "containers": [{"state": "waiting"}]}],
        [{"nodeName": "n1", "restartPolicy": "Always", "containers": [{"state": "running"}]}],
        [{"nodeName": "n1", "restartPolicy": "Always", "containers": [{"state": "waiting", "reason": "ContainerCreating"}]}],
        [{"nodeName": "n1", "restartPolicy": "Always", "containers": [{"state": "waiting", "reason": "ImagePullBackOff"}]}],
        [{"nodeName": "n1", "restartPolicy": "Never", "containers": [{"state": "terminated", "exitCode": 0, "reason": "Completed"}]}],
        [{"nodeName": "n1", "restartPolicy": "Never", "containers": [{"state": "terminated", "exitCode": 137, "reason": "OOMKilled"}]}],
        [{"nodeName": "n1", "restartPolicy": "Never", "containers": [{"state": "terminated", "exitCode": 0},
                                                                     {"state": "terminated", "exitCode": 2}]}],
        [{"nodeName": "n1", "restartPolicy": "OnFailure", "containers": [{"state": "terminated", "exitCode": 0, "reason": "Completed"}]}],
        [{"nodeName": "n1", "restartPolicy": "OnFailure", "containers": [{"state": "terminated", "exitCode": 1, "reason": "Error"}]}],
        [{"nodeName": "n1", "restartPolicy": "Always", "containers": [{"state": "terminated", "exitCode": 0, "reason": "Completed"}]}],
        [{"nodeName": "n1", "restartPolicy": "Always", "containers": [{"state": "running"}, {"state": "waiting", "reason": "ImagePullBackOff"}]}],
        [{"nodeName": "n1", "restartPolicy": "Always", "containers": [{"state": "waiting"}, {"state": "waiting", "reason": "ErrImagePull"}]}],
        [{"nodeName": "n1", "restartPolicy": "Never", "containers": [{"state": "terminated", "exitCode": 1, "reason": "Error"},
                                                                     {"state": "running"}]}],
        [{"nodeName": "n1", "restartPolicy": "Never", "containers": [{"state": "terminated", "exitCode": 3, "reason": "ContainerCannotRun"},
                                                                     {"state": "terminated", "exitCode": 137, "reason": "OOMKilled"}]}],
    ],
    examples=3,
    wrong_solutions=[
        '''def podStatus(pod):
    if pod.get("nodeName") is None:
        return ["Pending", "Pending"]
    containers = pod["containers"]
    if all(c["state"] == "terminated" for c in containers):
        failed = [c for c in containers if c.get("exitCode", 0) != 0]
        if not failed:
            return ["Succeeded", "Completed"]
        return ["Failed", failed[0].get("reason") or "Error"]
    phase = "Running" if any(c["state"] == "running" for c in containers) else "Pending"
    for c in containers:
        if c["state"] == "waiting" and c.get("reason"):
            return [phase, c["reason"]]
    return [phase, phase]
''',
    ],
    guide=dict(
        prereqs="Pod phases, container states and restart policies from *Lifecycle, restart policies, probes, requests and limits*.",
        intuition="The phase is a coarse summary of the containers; the status column is a friendlier string that prefers a waiting "
                  "reason when one exists. The crux is deciding whether a stopped container is truly finished, which depends on the restart policy.",
        hints=[
            "Write a helper `will_restart(container)` from the policy and exit code. You need it in two rules.",
            "A Pod is finished only if every container is terminated **and** none will restart. Under `Always`, that never happens.",
            "A container waiting in `CrashLoopBackOff` belongs to a Pod whose phase is `Running`, not `Pending`.",
        ],
        brute_force="The rules are a fixed decision list; evaluating them in order with a few passes over the containers is the solution.",
        approach="1. Unscheduled → Pending.\n2. Collect terminated containers; if they are all of them and none will restart, return "
                 "Succeeded or Failed.\n3. Otherwise compute the phase from three conditions.\n4. Scan for the first waiting reason.\n\n"
                 "**Dry run:** policy `OnFailure`, one container terminated with exit code 1. It will restart, so the Pod is not finished. "
                 "Phase: restarting → `Running`. No waiting container → status `Running`.",
        complexity="Time O(c) for c containers, space O(c).",
        pitfalls="- Declaring `Succeeded` under `restartPolicy: Always`.\n- Reporting `Pending` for a crash-looping Pod.\n"
                 "- Using the reason of the first terminated container instead of the first **failed** one.\n- Missing reasons: default to `Error`.",
        follow_up="Add init containers: while any has not completed, the status is `Init:k/n`.",
    ),
),
dict(
    id="k8s-oom-throttle",
    title="Throttled, OOMKilled or Fine?",
    difficulty="Easy",
    pattern="Resources",
    entry="containerOutcome",
    description=r"""
CPU and memory behave differently when a container exceeds its limit. Write
`containerOutcome(cpuUsage, memUsage, requests, limits)` returning `[cpuState, memState]`.

`cpuUsage` is in millicores and `memUsage` in MiB. `requests` and `limits` are dicts that may contain `"cpu"` and/or
`"memory"`.

The **effective request** for a resource is the request if given; otherwise the limit if given; otherwise `0`.

CPU state:

- `"throttled"` if a CPU limit exists and usage is **greater than** it;
- otherwise `"bursting"` if usage is greater than the effective CPU request;
- otherwise `"ok"`.

Memory state:

- `"oomkilled"` if a memory limit exists and usage is greater than it;
- otherwise `"evictable"` if usage is greater than the effective memory request (first in line if the node runs short);
- otherwise `"ok"`.

Usage exactly equal to a limit or request does not exceed it.

**Example:** usage `1400m`, `530Mi`; requests `{cpu: 250, memory: 256}`; limits `{cpu: 1000, memory: 512}`
→ `["throttled", "oomkilled"]`
""",
    starter='''def containerOutcome(cpuUsage, memUsage, requests, limits):
    # return [cpuState, memState]
    pass
''',
    solution='''def containerOutcome(cpuUsage, memUsage, requests, limits):
    def effective(res):
        if res in requests:
            return requests[res]
        return limits.get(res, 0)

    if "cpu" in limits and cpuUsage > limits["cpu"]:
        cpu = "throttled"
    elif cpuUsage > effective("cpu"):
        cpu = "bursting"
    else:
        cpu = "ok"
    if "memory" in limits and memUsage > limits["memory"]:
        mem = "oomkilled"
    elif memUsage > effective("memory"):
        mem = "evictable"
    else:
        mem = "ok"
    return [cpu, mem]
''',
    tests=[
        [1400, 530, {"cpu": 250, "memory": 256}, {"cpu": 1000, "memory": 512}],
        [120, 200, {"cpu": 250, "memory": 256}, {"cpu": 1000, "memory": 512}],
        [600, 300, {"cpu": 250, "memory": 256}, {"cpu": 1000, "memory": 512}],
        [1000, 512, {"cpu": 250, "memory": 256}, {"cpu": 1000, "memory": 512}],
        [250, 256, {"cpu": 250, "memory": 256}, {"cpu": 1000, "memory": 512}],
        [5000, 9000, {}, {}],
        [0, 0, {}, {}],
        [800, 400, {}, {"cpu": 1000, "memory": 512}],
        [1200, 600, {}, {"cpu": 1000, "memory": 512}],
        [3000, 300, {"cpu": 500}, {"memory": 256}],
        [400, 100, {"cpu": 500, "memory": 128}, {}],
        [501, 129, {"cpu": 500, "memory": 128}, {}],
        [900, 512, {"memory": 512}, {"memory": 512}],
    ],
    examples=2,
    wrong_solutions=[
        '''def containerOutcome(cpuUsage, memUsage, requests, limits):
    cpu = "ok"
    if "cpu" in limits and cpuUsage > limits["cpu"]:
        cpu = "throttled"
    elif cpuUsage > requests.get("cpu", 0):
        cpu = "bursting"
    mem = "ok"
    if "memory" in limits and memUsage > limits["memory"]:
        mem = "oomkilled"
    elif memUsage > requests.get("memory", 0):
        mem = "evictable"
    return [cpu, mem]
''',
        '''def containerOutcome(cpuUsage, memUsage, requests, limits):
    def effective(res):
        return requests[res] if res in requests else limits.get(res, 0)
    cpu = "throttled" if "cpu" in limits and cpuUsage >= limits["cpu"] else ("bursting" if cpuUsage > effective("cpu") else "ok")
    mem = "oomkilled" if "memory" in limits and memUsage >= limits["memory"] else ("evictable" if memUsage > effective("memory") else "ok")
    return [cpu, mem]
''',
    ],
    guide=dict(
        prereqs="Requests, limits and compressible versus incompressible resources from *Lifecycle, restart policies, probes, requests and limits*.",
        intuition="CPU over the limit is slowed down; memory over the limit is killed. Between request and limit a container is "
                  "borrowing spare capacity. The same three-band picture applies to both resources with different words.",
        hints=[
            "Handle each resource separately with the same shape of `if / elif / else`.",
            "Check the limit first, then the effective request.",
            "When a limit is set and the request is missing, the request defaults to the limit, so there is no bursting band.",
        ],
        brute_force="Direct comparison is all that is needed.",
        approach="1. Define `effective(res)`.\n2. CPU: limit exceeded → throttled; else above effective request → bursting; else ok.\n"
                 "3. Memory: limit exceeded → oomkilled; else above effective request → evictable; else ok.\n\n"
                 "**Dry run:** usage 800m with no request and limit 1000m. Not above the limit. Effective request = 1000 (copied from the "
                 "limit), and 800 is not above it → `ok`.",
        complexity="O(1).",
        pitfalls="- Using `>=` so that usage exactly at the limit counts as exceeding it.\n- Forgetting that a missing request falls "
                 "back to the limit.\n- Calling memory overuse `throttled`: memory cannot be throttled.",
        follow_up="Given a list of usage samples over time, count the periods a container was throttled and decide whether to "
                  "recommend raising the CPU limit.",
    ),
),
dict(
    id="k8s-node-accounting-qos",
    title="Node Resource Accounting and QoS Classes",
    difficulty="Medium",
    pattern="Resources",
    entry="nodeReport",
    description=r"""
The scheduler tracks how much of a node is reserved, and the kubelet ranks Pods by Quality of Service class.
Write `nodeReport(allocatable, pods)` returning `[qosClasses, requested, free]`.

- `allocatable` is `{"cpu": millicores, "memory": MiB}`.
- Each Pod is `{"name": str, "containers": [{"requests": {...}, "limits": {...}}]}`. Either dict may be empty or missing,
  and may hold `"cpu"` and/or `"memory"`.

For one container and one resource, the **effective request** is the request if given, else the limit if given, else `0`.

- `requested` = `[cpu, memory]`, the sum of effective requests over all containers of all Pods.
- `free` = `[cpu, memory]`, allocatable minus requested (may be negative).
- `qosClasses` = one string per Pod, in input order:
  - `"BestEffort"` if no container has any request or limit;
  - `"Guaranteed"` if **every** container has a limit for both CPU and memory, and for both resources its effective
    request equals its limit;
  - `"Burstable"` otherwise.

**Example:** allocatable `{cpu: 2000, memory: 4096}`; Pod A has one container with requests and limits both
`{cpu: 500, memory: 512}`; Pod B has one container with requests `{cpu: 250}` only
→ `[["Guaranteed", "Burstable"], [750, 512], [1250, 3584]]`
""",
    starter='''def nodeReport(allocatable, pods):
    # return [qosClasses, [cpuRequested, memRequested], [cpuFree, memFree]]
    pass
''',
    solution='''def nodeReport(allocatable, pods):
    total = {"cpu": 0, "memory": 0}
    classes = []
    for pod in pods:
        any_set = False
        guaranteed = True
        for c in pod["containers"]:
            req = c.get("requests") or {}
            lim = c.get("limits") or {}
            if req or lim:
                any_set = True
            for res in ("cpu", "memory"):
                eff = req[res] if res in req else lim.get(res, 0)
                total[res] += eff
                if res not in lim or eff != lim[res]:
                    guaranteed = False
        if not any_set:
            classes.append("BestEffort")
        elif guaranteed:
            classes.append("Guaranteed")
        else:
            classes.append("Burstable")
    requested = [total["cpu"], total["memory"]]
    free = [allocatable["cpu"] - total["cpu"], allocatable["memory"] - total["memory"]]
    return [classes, requested, free]
''',
    tests=[
        [{"cpu": 2000, "memory": 4096},
         [{"name": "a", "containers": [{"requests": {"cpu": 500, "memory": 512}, "limits": {"cpu": 500, "memory": 512}}]},
          {"name": "b", "containers": [{"requests": {"cpu": 250}}]}]],
        [{"cpu": 2000, "memory": 4096}, []],
        [{"cpu": 2000, "memory": 4096}, [{"name": "a", "containers": [{}]}]],
        [{"cpu": 2000, "memory": 4096}, [{"name": "a", "containers": [{"limits": {"cpu": 300, "memory": 128}}]}]],
        [{"cpu": 2000, "memory": 4096}, [{"name": "a", "containers": [{"requests": {"cpu": 100, "memory": 64}, "limits": {"cpu": 300, "memory": 128}}]}]],
        [{"cpu": 2000, "memory": 4096}, [{"name": "a", "containers": [{"limits": {"memory": 128}}]}]],
        [{"cpu": 2000, "memory": 4096},
         [{"name": "a", "containers": [{"requests": {"cpu": 500, "memory": 512}, "limits": {"cpu": 500, "memory": 512}}, {}]}]],
        [{"cpu": 2000, "memory": 4096},
         [{"name": "a", "containers": [{"requests": {"cpu": 500, "memory": 512}, "limits": {"cpu": 500, "memory": 512}},
                                       {"limits": {"cpu": 100, "memory": 64}}]}]],
        [{"cpu": 1000, "memory": 1024},
         [{"name": "a", "containers": [{"requests": {"cpu": 800, "memory": 900}}]},
          {"name": "b", "containers": [{"requests": {"cpu": 800, "memory": 900}}]}]],
        [{"cpu": 4000, "memory": 8192},
         [{"name": "a", "containers": [{"requests": {}, "limits": {}}]},
          {"name": "b", "containers": [{"requests": {"memory": 256}, "limits": {"memory": 256}}]},
          {"name": "c", "containers": [{"requests": {"cpu": 200, "memory": 256}, "limits": {"cpu": 200, "memory": 300}}]}]],
        [{"cpu": 64000, "memory": 262144},
         [{"name": "p%d" % i, "containers": [{"requests": {"cpu": 100 + i % 5, "memory": 64},
                                              "limits": {"cpu": 100 + i % 5, "memory": 64 if i % 2 else 128}}]} for i in range(150)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def nodeReport(allocatable, pods):
    total = {"cpu": 0, "memory": 0}
    classes = []
    for pod in pods:
        any_set = False
        guaranteed = True
        for c in pod["containers"]:
            req = c.get("requests") or {}
            lim = c.get("limits") or {}
            if req or lim:
                any_set = True
            for res in ("cpu", "memory"):
                total[res] += req.get(res, 0)
                if res not in lim or res not in req or req[res] != lim[res]:
                    guaranteed = False
        classes.append("BestEffort" if not any_set else ("Guaranteed" if guaranteed else "Burstable"))
    return [classes, [total["cpu"], total["memory"]],
            [allocatable["cpu"] - total["cpu"], allocatable["memory"] - total["memory"]]]
''',
    ],
    guide=dict(
        prereqs="Requests, limits and QoS classes from *Lifecycle, restart policies, probes, requests and limits*; allocatable from *Worker nodes*.",
        intuition="Two questions share one pass. Accounting adds up what each container reserves. Classification asks, per Pod, "
                  "whether nothing is declared, everything is declared with request equal to limit, or something in between.",
        hints=[
            "Compute the effective request once per container and resource; both outputs use it.",
            "Track two flags per Pod: `any_set` and `guaranteed`. Start `guaranteed` as True and clear it when a container breaks the rule.",
            "A container with only limits is Guaranteed-compatible, because its requests default to its limits.",
        ],
        brute_force="A single pass over Pods, containers and the two resources is already optimal.",
        approach="1. For each Pod, loop over containers and both resources.\n2. Add the effective request to the totals.\n"
                 "3. Clear `guaranteed` if the limit is missing or differs from the effective request.\n4. Choose the class from the two flags.\n\n"
                 "**Dry run:** Pod B has `requests: {cpu: 250}`. `any_set` is True. For CPU there is no limit → not Guaranteed. "
                 "Class: Burstable. It adds 250 CPU and 0 memory.",
        complexity="Time O(total containers), space O(pods).",
        pitfalls="- Ignoring the limit-to-request default, which under-counts reservations.\n- Calling a Pod Guaranteed when one of "
                 "several containers has no limits.\n- Classifying an empty Pod as Burstable.\n- Clamping `free` at zero when the task allows negatives.",
        follow_up="Add init containers: the Pod's effective request per resource is the larger of the biggest init container and the sum of the app containers.",
    ),
),
dict(
    id="k8s-probe-state-machine",
    title="Probe State Machine",
    difficulty="Hard",
    pattern="Probes",
    entry="probeTimeline",
    description=r"""
Simulate how startup, liveness and readiness probes drive a container. Write `probeTimeline(results, config)`.

`results` is a string of `P` (the health endpoint passes) and `F` (it fails), one character per probe period.
`config` is `{"startup": s, "liveness": l, "readinessFailure": rf, "readinessSuccess": rs}`: all are consecutive-result
thresholds (positive integers), except that `startup` may be `0`, meaning there is no startup probe.

State: `started` (initially `False` if there is a startup probe, else `True`), `ready` (initially `False`),
`restarts = 0`, and counters for consecutive results.

For each period, in order:

- **If not started**, only the startup probe runs:
  - `P` → the container is now started; reset all counters. (Liveness and readiness begin in the *next* period.)
  - `F` → one more consecutive startup failure; when the count reaches `s`, the container is **restarted**.
- **If started**, liveness and readiness both see the result:
  - readiness: `P` → reset the readiness failure count, add one consecutive success; if not ready and successes ≥ `rs`,
    become ready. `F` → reset the success count, add one consecutive failure; if ready and failures ≥ `rf`, become not ready.
  - liveness: `P` → reset the liveness failure count. `F` → add one; when the count reaches `l`, the container is **restarted**.

A **restart** adds 1 to `restarts`, sets `ready = False`, resets every counter, and sets `started` back to its
initial value.

Return `[restarts, timeline]` where `timeline` is a string with one character per period: `1` if the container is ready
at the end of that period, else `0`.

**Example:** `results = "FFPPPF"`, `{"startup": 3, "liveness": 3, "readinessFailure": 1, "readinessSuccess": 2}`
→ periods 1-2 fail startup (2 < 3), period 3 starts the container, periods 4-5 are two successes so it becomes ready at
period 5, period 6 fails readiness → `[0, "000010"]`
""",
    starter='''def probeTimeline(results, config):
    # return [restarts, timeline]
    pass
''',
    solution='''def probeTimeline(results, config):
    s, l = config["startup"], config["liveness"]
    rf, rs = config["readinessFailure"], config["readinessSuccess"]
    initial_started = (s == 0)
    started, ready, restarts = initial_started, False, 0
    startup_fails = live_fails = ready_fails = ready_succ = 0
    out = []
    for r in results:
        restart = False
        if not started:
            if r == "P":
                started = True
                startup_fails = live_fails = ready_fails = ready_succ = 0
            else:
                startup_fails += 1
                if startup_fails >= s:
                    restart = True
        else:
            if r == "P":
                ready_fails = 0
                ready_succ += 1
                if not ready and ready_succ >= rs:
                    ready = True
                live_fails = 0
            else:
                ready_succ = 0
                ready_fails += 1
                if ready and ready_fails >= rf:
                    ready = False
                live_fails += 1
                if live_fails >= l:
                    restart = True
        if restart:
            restarts += 1
            ready = False
            started = initial_started
            startup_fails = live_fails = ready_fails = ready_succ = 0
        out.append("1" if ready else "0")
    return [restarts, "".join(out)]
''',
    tests=[
        ["FFPPPF", {"startup": 3, "liveness": 3, "readinessFailure": 1, "readinessSuccess": 2}],
        ["", {"startup": 3, "liveness": 3, "readinessFailure": 3, "readinessSuccess": 1}],
        ["PPPP", {"startup": 0, "liveness": 3, "readinessFailure": 3, "readinessSuccess": 1}],
        ["PPPP", {"startup": 2, "liveness": 3, "readinessFailure": 3, "readinessSuccess": 1}],
        ["FFFFFF", {"startup": 3, "liveness": 3, "readinessFailure": 3, "readinessSuccess": 1}],
        ["FFFFFF", {"startup": 0, "liveness": 3, "readinessFailure": 3, "readinessSuccess": 1}],
        ["PPFFPFFFPPFFFFFF", {"startup": 0, "liveness": 3, "readinessFailure": 3, "readinessSuccess": 1}],
        ["PPFFPFFFPPFFFFFF", {"startup": 0, "liveness": 5, "readinessFailure": 2, "readinessSuccess": 2}],
        ["PPPFPPPFPPP", {"startup": 0, "liveness": 2, "readinessFailure": 1, "readinessSuccess": 3}],
        ["FPFPFPFP", {"startup": 0, "liveness": 2, "readinessFailure": 1, "readinessSuccess": 1}],
        ["FFPFFFPPPP", {"startup": 4, "liveness": 3, "readinessFailure": 1, "readinessSuccess": 1}],
        ["PPPFFFPPP", {"startup": 1, "liveness": 3, "readinessFailure": 3, "readinessSuccess": 1}],
        ["FPPPFFFFPPPP", {"startup": 1, "liveness": 4, "readinessFailure": 2, "readinessSuccess": 2}],
        ["PF" * 150 + "FFF" + "P" * 20, {"startup": 0, "liveness": 3, "readinessFailure": 2, "readinessSuccess": 4}],
    ],
    examples=2,
    wrong_solutions=[
        '''def probeTimeline(results, config):
    l = config["liveness"]
    rf, rs = config["readinessFailure"], config["readinessSuccess"]
    ready, restarts = False, 0
    live_fails = ready_fails = ready_succ = 0
    out = []
    for r in results:
        if r == "P":
            ready_fails = 0
            ready_succ += 1
            if not ready and ready_succ >= rs:
                ready = True
            live_fails = 0
        else:
            ready_succ = 0
            ready_fails += 1
            if ready and ready_fails >= rf:
                ready = False
            live_fails += 1
            if live_fails >= l:
                restarts += 1
                ready = False
                live_fails = ready_fails = ready_succ = 0
        out.append("1" if ready else "0")
    return [restarts, "".join(out)]
''',
        '''def probeTimeline(results, config):
    s, l = config["startup"], config["liveness"]
    rf, rs = config["readinessFailure"], config["readinessSuccess"]
    initial_started = (s == 0)
    started, ready, restarts = initial_started, False, 0
    startup_fails = live_fails = ready_fails = 0
    out = []
    for r in results:
        if not started:
            if r == "P":
                started = True
            else:
                startup_fails += 1
                if startup_fails >= s:
                    restarts += 1
                    startup_fails = 0
        elif r == "P":
            ready = True
            live_fails = ready_fails = 0
        else:
            ready_fails += 1
            live_fails += 1
            if ready_fails >= rf:
                ready = False
            if live_fails >= l:
                restarts += 1
                ready = False
                started = initial_started
                live_fails = ready_fails = 0
        out.append("1" if ready else "0")
    return [restarts, "".join(out)]
''',
    ],
    guide=dict(
        prereqs="The three probe types and their thresholds from *Lifecycle, restart policies, probes, requests and limits*.",
        intuition="Each probe is a small counter of consecutive results that triggers an action at a threshold. The startup probe "
                  "is a gate in front of the other two. A restart sends everything back to the beginning.",
        hints=[
            "Keep four counters: startup failures, liveness failures, readiness failures, readiness successes.",
            "Process one character at a time. Branch first on `started`, then on `P` or `F`.",
            "Apply the restart at the end of the period, after readiness has been updated, and force `ready = False` there. "
            "Record the timeline character last.",
        ],
        brute_force="You could recompute the state from the start of the string for every period, O(n²). Carrying the counters "
                    "forward makes it one pass.",
        approach="1. Initialise state from the config.\n2. For each result: if not started, handle startup; else update readiness "
                 "and liveness.\n3. If a restart was triggered, bump the count and reset.\n4. Append `1` or `0`.\n\n"
                 "**Dry run** of `FFPPPF` with startup 3, readinessSuccess 2, readinessFailure 1: F (1 startup failure), F (2), "
                 "P (started), P (1 success), P (2 successes → ready), F (1 failure ≥ 1 → not ready; liveness failures 1 < 3). "
                 "Timeline `000010`, restarts 0.",
        complexity="Time O(n), space O(n) for the output string.",
        pitfalls="- Running liveness before the startup probe has passed.\n- Counting total failures instead of consecutive ones.\n"
                 "- Marking the container ready in the same period the startup probe passes.\n- Forgetting that a restart also "
                 "re-arms the startup probe and clears readiness.",
        follow_up="Add `periodSeconds` per probe so that the three probes fire at different times, and add the restart back-off delay.",
    ),
),
dict(
    id="k8s-crashloop-backoff",
    title="CrashLoopBackOff Restart Schedule",
    difficulty="Medium",
    pattern="Troubleshooting",
    entry="restartTimes",
    description=r"""
When a container keeps crashing, the kubelet waits longer before each restart. Write
`restartTimes(runSeconds, base, cap, resetAfter)` that returns the time, in seconds, at which each restart happens.

- The container first starts at time `0`.
- `runSeconds[i]` is how long the container runs on its `i`-th run before crashing.
- After a crash the kubelet waits `delay` seconds and starts the container again.
- `delay` starts at `base`. After each restart it doubles, but never exceeds `cap`.
- If the run that crashed lasted **at least** `resetAfter` seconds, the back-off is reset: the delay used for this
  crash is `base` again (and doubling continues from there).

Return a list with one start time per crash.

**Example:** `runSeconds = [1, 1, 1]`, `base = 10`, `cap = 300`, `resetAfter = 600`
→ crash at 1, restart at 11; crash at 12, wait 20, restart at 32; crash at 33, wait 40, restart at 73 → `[11, 32, 73]`
""",
    starter='''def restartTimes(runSeconds, base, cap, resetAfter):
    # return the list of restart times
    pass
''',
    solution='''def restartTimes(runSeconds, base, cap, resetAfter):
    t = 0
    delay = base
    out = []
    for run in runSeconds:
        t += run
        if run >= resetAfter:
            delay = base
        t += delay
        out.append(t)
        delay = min(delay * 2, cap)
    return out
''',
    tests=[
        [[1, 1, 1], 10, 300, 600],
        [[], 10, 300, 600],
        [[0], 10, 300, 600],
        [[1] * 8, 10, 300, 600],
        [[5, 5, 700, 5, 5], 10, 300, 600],
        [[600, 600, 600], 10, 300, 600],
        [[599, 599, 599], 10, 300, 600],
        [[1, 1, 1, 1], 10, 25, 600],
        [[2, 2, 2], 300, 300, 600],
        [[0, 0, 0, 0, 0, 0, 0], 1, 8, 100],
        [[1, 1, 1, 1, 1, 1, 1000, 1, 1], 10, 300, 600],
        [[3, 9, 27, 81, 243], 5, 40, 80],
        [[i % 7 for i in range(200)], 10, 300, 6],
    ],
    examples=2,
    wrong_solutions=[
        '''def restartTimes(runSeconds, base, cap, resetAfter):
    t = 0
    delay = base
    out = []
    for run in runSeconds:
        t += run + delay
        out.append(t)
        delay = min(delay * 2, cap)
    return out
''',
        '''def restartTimes(runSeconds, base, cap, resetAfter):
    t = 0
    out = []
    for i, run in enumerate(runSeconds):
        t += run + min(base * 2 ** i, cap)
        out.append(t)
    return out
''',
        '''def restartTimes(runSeconds, base, cap, resetAfter):
    t = 0
    delay = base
    out = []
    for run in runSeconds:
        t += run
        if run >= resetAfter:
            delay = base
        t += delay
        out.append(t)
        delay = delay * 2
    return out
''',
    ],
    guide=dict(
        prereqs="Restart policies and back-off from *Lifecycle, restart policies, probes, requests and limits* and the CrashLoopBackOff "
                "section of *Troubleshooting Pods*.",
        intuition="Time moves forward in two kinds of step: the container runs, then the kubelet waits. The wait is a variable "
                  "that doubles after every use, is capped, and snaps back to the base after a long healthy run.",
        hints=[
            "Keep two variables: the clock `t` and the current `delay`.",
            "Check the reset condition after adding the run time and before adding the delay.",
            "Double the delay after recording the restart, and apply `min(..., cap)`.",
        ],
        brute_force="Recomputing the delay for crash i from scratch by replaying crashes 0..i is O(n²). Carrying `delay` forward is O(n).",
        approach="1. `t = 0`, `delay = base`.\n2. For each run: `t += run`; if `run >= resetAfter`, `delay = base`; `t += delay`; "
                 "append `t`; `delay = min(2 * delay, cap)`.\n\n"
                 "**Dry run** of `[5, 5, 700, 5]` with base 10: crash at 5, restart 15, delay→20. Crash at 20, restart 40, delay→40. "
                 "Run 700: crash at 740, long run so delay=10, restart 750, delay→20. Crash at 755, restart 775.",
        complexity="Time O(n), space O(n) for the result.",
        pitfalls="- Computing the delay as `base * 2**i`, which ignores resets.\n- Forgetting the cap.\n- Resetting after the delay "
                 "was added instead of before.\n- Using `>` where the rule says at least `resetAfter`.",
        follow_up="Given a wall-clock time, report whether the container is running or waiting, and how many seconds remain until the next restart.",
    ),
),
dict(
    id="k8s-resource-quota",
    title="Namespace Quota Admission",
    difficulty="Medium",
    pattern="Namespaces",
    entry="admitPods",
    description=r"""
Simulate admission of Pods into a namespace that has a LimitRange and a ResourceQuota. Write
`admitPods(hard, limitRange, pods)` and return one string per Pod, in order.

- `hard` is the quota: a dict with any of the keys `"pods"`, `"requests.cpu"`, `"requests.memory"`, `"limits.cpu"`,
  `"limits.memory"`.
- `limitRange` is `{"defaultRequest": {...}, "default": {...}}`; either part may be missing. Each may hold `"cpu"` and/or
  `"memory"`. (`default` is the default **limit**.)
- Each Pod is `{"name": str, "requests": {...}, "limits": {...}}` (one container; either dict may be missing).

For each Pod, in order:

1. **Defaulting**, per resource (`cpu`, then `memory`):
   a. if the Pod gives a limit but no request, the request becomes equal to the limit;
   b. otherwise a missing request takes `defaultRequest[resource]` if defined;
   c. a missing limit takes `default[resource]` if defined.
2. If, for `cpu` or `memory`, both request and limit now exist and request > limit → `"invalid: request exceeds limit"`.
3. For each of `requests.cpu`, `requests.memory`, `limits.cpu`, `limits.memory` (in that order) that is in `hard`: if the
   Pod has no value for it → `"forbidden: must specify <key>"`.
4. For each of `pods`, `requests.cpu`, `requests.memory`, `limits.cpu`, `limits.memory` (in that order) that is in `hard`:
   if `used + amount > hard` → `"forbidden: exceeded quota <key>"` (the amount for `pods` is 1).
5. Otherwise `"admitted"`, and the Pod's amounts are added to the usage.

Rejected Pods use no quota.

**Example:** `hard = {"requests.cpu": 500}`, no LimitRange, Pods requesting 300 and 300 CPU
→ `["admitted", "forbidden: exceeded quota requests.cpu"]`
""",
    starter='''def admitPods(hard, limitRange, pods):
    # return a list of result strings, one per pod
    pass
''',
    solution='''def admitPods(hard, limitRange, pods):
    default_req = limitRange.get("defaultRequest") or {}
    default_lim = limitRange.get("default") or {}
    used = {}
    out = []
    for pod in pods:
        req = dict(pod.get("requests") or {})
        lim = dict(pod.get("limits") or {})
        for res in ("cpu", "memory"):
            if res not in req:
                if res in lim:
                    req[res] = lim[res]
                elif res in default_req:
                    req[res] = default_req[res]
            if res not in lim and res in default_lim:
                lim[res] = default_lim[res]
        if any(res in req and res in lim and req[res] > lim[res] for res in ("cpu", "memory")):
            out.append("invalid: request exceeds limit")
            continue
        amounts = {"pods": 1}
        for res in ("cpu", "memory"):
            if res in req:
                amounts["requests." + res] = req[res]
            if res in lim:
                amounts["limits." + res] = lim[res]
        verdict = None
        for key in ("requests.cpu", "requests.memory", "limits.cpu", "limits.memory"):
            if key in hard and key not in amounts:
                verdict = "forbidden: must specify " + key
                break
        if verdict is None:
            for key in ("pods", "requests.cpu", "requests.memory", "limits.cpu", "limits.memory"):
                if key in hard and used.get(key, 0) + amounts[key] > hard[key]:
                    verdict = "forbidden: exceeded quota " + key
                    break
        if verdict is None:
            for key, amount in amounts.items():
                used[key] = used.get(key, 0) + amount
            verdict = "admitted"
        out.append(verdict)
    return out
''',
    tests=[
        [{"requests.cpu": 500}, {}, [{"name": "a", "requests": {"cpu": 300}}, {"name": "b", "requests": {"cpu": 300}}]],
        [{}, {}, [{"name": "a"}, {"name": "b"}]],
        [{"pods": 2}, {}, [{"name": "a"}, {"name": "b"}, {"name": "c"}]],
        [{"requests.memory": 1024}, {}, [{"name": "a"}]],
        [{"requests.memory": 1024}, {"defaultRequest": {"memory": 128}}, [{"name": "a"}, {"name": "b", "requests": {"memory": 900}}]],
        [{"requests.cpu": 1000}, {"default": {"cpu": 500, "memory": 256}, "defaultRequest": {"cpu": 100, "memory": 128}},
         [{"name": "a", "requests": {"memory": 512}}]],
        [{"requests.cpu": 1000, "limits.cpu": 2000}, {},
         [{"name": "a", "limits": {"cpu": 600}}, {"name": "b", "limits": {"cpu": 600}}]],
        [{"requests.cpu": 1000, "requests.memory": 1024, "pods": 4},
         {"default": {"cpu": 500, "memory": 256}, "defaultRequest": {"cpu": 100, "memory": 128}},
         [{"name": "web", "requests": {"cpu": 250, "memory": 256}, "limits": {"cpu": 500, "memory": 256}},
          {"name": "scratch"},
          {"name": "api1", "requests": {"cpu": 500, "memory": 512}},
          {"name": "api2", "requests": {"cpu": 500, "memory": 512}, "limits": {"cpu": 600, "memory": 512}},
          {"name": "limit-only", "limits": {"cpu": 150, "memory": 100}},
          {"name": "extra", "requests": {"cpu": 1, "memory": 1}}]],
        [{"limits.memory": 512}, {}, [{"name": "a", "requests": {"memory": 100}}]],
        [{"limits.memory": 512, "requests.cpu": 100}, {}, [{"name": "a", "limits": {"memory": 100}}]],
        [{"requests.cpu": 300, "requests.memory": 300}, {},
         [{"name": "a", "requests": {"cpu": 200, "memory": 400}}, {"name": "b", "requests": {"cpu": 300, "memory": 300}},
          {"name": "c", "requests": {"cpu": 1, "memory": 1}}]],
        [{"pods": 1, "requests.cpu": 100}, {}, [{"name": "a", "requests": {"cpu": 200}}, {"name": "b", "requests": {"cpu": 100}},
                                                 {"name": "c", "requests": {"cpu": 0}}]],
        [{"requests.cpu": 5000, "pods": 60}, {"defaultRequest": {"cpu": 50}},
         [{"name": "p%d" % i, "requests": ({"cpu": 100 + i} if i % 3 else {})} for i in range(80)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def admitPods(hard, limitRange, pods):
    default_req = limitRange.get("defaultRequest") or {}
    default_lim = limitRange.get("default") or {}
    used = {}
    out = []
    for pod in pods:
        req = dict(pod.get("requests") or {})
        lim = dict(pod.get("limits") or {})
        for res in ("cpu", "memory"):
            if res not in req and res in default_req:
                req[res] = default_req[res]
            if res not in lim and res in default_lim:
                lim[res] = default_lim[res]
        if any(res in req and res in lim and req[res] > lim[res] for res in ("cpu", "memory")):
            out.append("invalid: request exceeds limit")
            continue
        amounts = {"pods": 1}
        for res in ("cpu", "memory"):
            if res in req:
                amounts["requests." + res] = req[res]
            if res in lim:
                amounts["limits." + res] = lim[res]
        verdict = None
        for key in ("requests.cpu", "requests.memory", "limits.cpu", "limits.memory"):
            if key in hard and key not in amounts:
                verdict = "forbidden: must specify " + key
                break
        if verdict is None:
            for key in ("pods", "requests.cpu", "requests.memory", "limits.cpu", "limits.memory"):
                if key in hard and used.get(key, 0) + amounts[key] > hard[key]:
                    verdict = "forbidden: exceeded quota " + key
                    break
        if verdict is None:
            for key, amount in amounts.items():
                used[key] = used.get(key, 0) + amount
            verdict = "admitted"
        out.append(verdict)
    return out
''',
        '''def admitPods(hard, limitRange, pods):
    used = {}
    out = []
    for pod in pods:
        req = dict(pod.get("requests") or {})
        amounts = {"pods": 1}
        for res in ("cpu", "memory"):
            amounts["requests." + res] = req.get(res, 0)
        verdict = "admitted"
        for key in ("pods", "requests.cpu", "requests.memory"):
            if key in hard and used.get(key, 0) + amounts[key] > hard[key]:
                verdict = "forbidden: exceeded quota " + key
                break
        for key, amount in amounts.items():
            used[key] = used.get(key, 0) + amount
        out.append(verdict)
    return out
''',
    ],
    guide=dict(
        prereqs="The lesson *ResourceQuotas and LimitRanges*: defaulting happens first, a compute quota makes the field mandatory, and rejected Pods consume nothing.",
        intuition="Admission is a pipeline of stages applied to one Pod at a time: fill in defaults, sanity-check, make sure every "
                  "quota-tracked field has a value, then check the running totals. Only a Pod that survives every stage changes the totals.",
        hints=[
            "Copy the Pod's `requests` and `limits` before defaulting so that you do not modify the input.",
            "Build one `amounts` dict with keys such as `requests.cpu` and `pods`; both later stages read from it.",
            "Check all quota keys before adding anything to `used`. Update `used` only on the admitted path.",
        ],
        brute_force="Recomputing namespace usage from the list of admitted Pods for each new Pod is O(n²). Keeping running totals is O(n).",
        approach="1. Default per resource: limit → request, else `defaultRequest`; then `default` for a missing limit.\n"
                 "2. Reject if a request exceeds its limit.\n3. Reject if a quota key has no value.\n4. Reject at the first key whose total would be exceeded.\n"
                 "5. Otherwise add to `used`.\n\n"
                 "**Dry run:** quota `requests.cpu: 1000`; LimitRange default limit 500 CPU, defaultRequest 100. Pod with "
                 "`requests.memory: 512`, default memory limit 256: memory request 512 stays, limit becomes 256 → 512 > 256 → invalid.",
        complexity="Time O(n) for n Pods (a constant number of keys each). Space O(1) besides the output.",
        pitfalls="- Applying `defaultRequest` when the Pod gave an explicit limit (the request should copy the limit).\n"
                 "- Charging quota for rejected Pods.\n- Reporting the wrong key because the check order differs.\n"
                 "- Using `>=` and rejecting a Pod that exactly fills the quota.",
        follow_up="Add LimitRange `min` and `max` validation, and quota scopes such as `BestEffort`.",
    ),
),
]
