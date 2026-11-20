PROBLEMS = [
dict(
    id="docker-rolling-update",
    title="Plan a Rolling Update",
    difficulty="Medium",
    pattern="Orchestration",
    entry="rollingUpdate",
    description=r"""
Simulate how an orchestrator such as Docker Swarm rolls out a new image version.
Write `rollingUpdate(replicas, parallelism, failing, failure_action)`.

- The service has tasks numbered `1..replicas`, all running the old version.
- Tasks are updated in order, in batches of `parallelism` tasks (the last batch may be smaller).
  `parallelism = 0` means "all tasks in one batch".
- `failing` is the list of task numbers whose new version fails to become healthy.
- `failure_action` is `"pause"`, `"continue"` or `"rollback"`.

For each batch, every task in it becomes `"new"`, or `"failed"` if its number is in `failing`. Then, if the batch
contained at least one failure:

- `pause`: stop. Tasks not yet reached stay `"old"`. Status `"paused"`.
- `continue`: carry on with the next batch.
- `rollback`: stop, and set **every** task back to `"old"`. Status `"rolled_back"`.

If all batches are processed the status is `"completed"` (even if `continue` skipped over failures).

Return `[states, status, batches]`: the list of task states (index 0 is task 1), the status, and the number of
batches that were started. With `replicas = 0` return `[[], "completed", 0]`.

**Example:** `rollingUpdate(6, 2, [3], "pause")` → `[["new","new","failed","new","old","old"], "paused", 2]`
""",
    starter='''def rollingUpdate(replicas, parallelism, failing, failure_action):
    pass
''',
    solution='''def rollingUpdate(replicas, parallelism, failing, failure_action):
    states = ["old"] * replicas
    bad = set(failing)
    step = parallelism if parallelism > 0 else max(replicas, 1)
    batches = 0
    for start in range(0, replicas, step):
        batches += 1
        failed = False
        for i in range(start, min(start + step, replicas)):
            if (i + 1) in bad:
                states[i] = "failed"
                failed = True
            else:
                states[i] = "new"
        if failed:
            if failure_action == "pause":
                return [states, "paused", batches]
            if failure_action == "rollback":
                return [["old"] * replicas, "rolled_back", batches]
    return [states, "completed", batches]
''',
    tests=[
        [6, 2, [3], "pause"],
        [6, 2, [3], "continue"],
        [6, 2, [3], "rollback"],
        [0, 2, [], "pause"],
        [5, 2, [], "rollback"],
        [5, 0, [5], "pause"],
        [5, 0, [], "pause"],
        [4, 10, [1], "continue"],
        [7, 3, [7], "pause"],
        [7, 3, [1, 4, 7], "continue"],
        [1, 1, [1], "rollback"],
        [8, 1, [9, 0, -1], "pause"],
        [9, 4, [5, 6], "pause"],
        [3, 1, [2, 3], "rollback"],
    ],
    examples=1,
    wrong_solutions=[
        '''def rollingUpdate(replicas, parallelism, failing, failure_action):
    states = ["old"] * replicas
    bad = set(failing)
    step = parallelism if parallelism > 0 else max(replicas, 1)
    batches = 0
    for start in range(0, replicas, step):
        batches += 1
        for i in range(start, min(start + step, replicas)):
            if (i + 1) in bad:
                states[i] = "failed"
                if failure_action == "pause":
                    return [states, "paused", batches]
                if failure_action == "rollback":
                    return [["old"] * replicas, "rolled_back", batches]
            else:
                states[i] = "new"
    return [states, "completed", batches]
''',
        '''def rollingUpdate(replicas, parallelism, failing, failure_action):
    states = ["old"] * replicas
    bad = set(failing)
    step = max(parallelism, 1)
    batches = 0
    for start in range(0, replicas, step):
        batches += 1
        failed = False
        for i in range(start, min(start + step, replicas)):
            states[i] = "failed" if (i + 1) in bad else "new"
            failed = failed or states[i] == "failed"
        if failed and failure_action == "pause":
            return [states, "paused", batches]
        if failed and failure_action == "rollback":
            return [["old" if s != "new" else "new" for s in states], "rolled_back", batches]
    return [states, "completed", batches]
''',
    ],
    guide=dict(
        prereqs="Lesson *Rolling updates and rollbacks*. Slicing a range into chunks.",
        intuition="A rollout is a loop over batches with a decision after each one. The decision is taken per **batch**, not per task: "
                  "the orchestrator starts the whole batch together, so the other tasks in a failing batch are still updated.",
        hints=[
            "`range(0, replicas, step)` gives the first index of every batch.",
            "Update the whole batch first, remember whether anything failed, then apply the failure action.",
            "Handle `parallelism = 0` by making the step equal to the number of replicas (and avoid a step of 0 when there are none).",
        ],
        brute_force="Simulate one task at a time and stop at the first failure. That is simpler and wrong whenever the failing task is not the last of its batch.",
        approach="Build `['old'] * replicas`; loop over batch starts; fill; decide.\n\n**Dry run** `(6, 2, [3], 'pause')`: batch 1 = tasks 1-2 → new, new. "
                 "Batch 2 = tasks 3-4 → failed, new; a failure occurred, action pause → return with tasks 5-6 still old and 2 batches started.",
        complexity="Time O(replicas), space O(replicas).",
        pitfalls="- Stopping in the middle of a batch.\n- A step of 0 causing `range` to raise.\n- On rollback, leaving already updated tasks on the new version.\n"
                 "- Reporting `paused` when the action is `continue`.",
        follow_up="Add `max_failure_ratio` (tolerate a fraction of failures) and an `order` of start-first or stop-first to compute the minimum capacity during the rollout.",
    ),
),
dict(
    id="docker-resource-accounting",
    title="CPU and Memory Accounting on a Host",
    difficulty="Medium",
    pattern="Orchestration",
    entry="scheduleContainers",
    description=r"""
A scheduler places containers by their **reservations** and lets **limits** overcommit.
Write `scheduleContainers(host_cpu, host_mem, containers)`.

- `host_cpu` is the host's capacity in millicores (1000 = one core); `host_mem` is in MB.
- Each container is `[name, cpu_reservation, mem_reservation, cpu_limit, mem_limit]` in the same units.
  A limit of `0` means "no limit".

Go through the containers in order. A container is **placed** if its CPU reservation and its memory reservation both
fit in what is still free; placing it subtracts both from the free amounts. Otherwise it is **rejected** and uses nothing.

For the placed containers, add up the limits; a limit of `0` counts as the full host capacity for that resource.
The overcommit percentage of a resource is `floor(100 * sum_of_limits / host_capacity)`.

Return `[placed_names, rejected_names, free_cpu, free_mem, cpu_limit_percent, mem_limit_percent]`.
Host capacities are positive.

**Example:** `scheduleContainers(4000, 8192, [["web",500,256,1000,512], ["db",1500,4096,2000,4096], ["batch",2500,1024,0,2048], ["cache",500,1024,500,0]])`
→ `[["web","db","cache"], ["batch"], 1500, 2816, 87, 156]`
""",
    starter='''def scheduleContainers(host_cpu, host_mem, containers):
    pass
''',
    solution='''def scheduleContainers(host_cpu, host_mem, containers):
    free_cpu, free_mem = host_cpu, host_mem
    placed, rejected = [], []
    cpu_lim = mem_lim = 0
    for name, cpu_res, mem_res, cpu_l, mem_l in containers:
        if cpu_res <= free_cpu and mem_res <= free_mem:
            free_cpu -= cpu_res
            free_mem -= mem_res
            placed.append(name)
            cpu_lim += cpu_l if cpu_l > 0 else host_cpu
            mem_lim += mem_l if mem_l > 0 else host_mem
        else:
            rejected.append(name)
    return [placed, rejected, free_cpu, free_mem, 100 * cpu_lim // host_cpu, 100 * mem_lim // host_mem]
''',
    tests=[
        [4000, 8192, [["web", 500, 256, 1000, 512], ["db", 1500, 4096, 2000, 4096], ["batch", 2500, 1024, 0, 2048], ["cache", 500, 1024, 500, 0]]],
        [1000, 1024, []],
        [1000, 1024, [["a", 1000, 1024, 1000, 1024]]],
        [1000, 1024, [["a", 1001, 10, 0, 0]]],
        [1000, 1024, [["a", 10, 1025, 0, 0], ["b", 10, 10, 0, 0]]],
        [2000, 2048, [["big", 1500, 100, 1500, 100], ["big2", 1500, 100, 1500, 100], ["small", 500, 100, 600, 100]]],
        [2000, 2048, [["a", 0, 0, 0, 0], ["b", 0, 0, 0, 0], ["c", 0, 0, 0, 0]]],
        [3000, 1000, [["a", 1000, 999, 1000, 999], ["b", 1000, 2, 1000, 2], ["c", 1000, 1, 3000, 1]]],
        [7, 3, [["x", 1, 1, 1, 1], ["y", 1, 1, 1, 1]]],
        [8000, 16000, [["c%d" % i, 300, 700, 900, 1400] for i in range(40)]],
        [1000, 1000, [["a", 600, 600, 700, 700], ["b", 600, 100, 700, 700], ["c", 400, 400, 5000, 5000]]],
        [4000, 4096, [["cpu-hog", 4000, 1, 4000, 1], ["mem-hog", 1, 4095, 1, 4095], ["late", 0, 1, 0, 1]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def scheduleContainers(host_cpu, host_mem, containers):
    free_cpu, free_mem = host_cpu, host_mem
    placed, rejected, cl, ml = [], [], 0, 0
    for name, cr, mr, c, m in containers:
        if c <= free_cpu and m <= free_mem:
            free_cpu -= c; free_mem -= m
            placed.append(name); cl += c; ml += m
        else:
            rejected.append(name)
    return [placed, rejected, free_cpu, free_mem, 100 * cl // host_cpu, 100 * ml // host_mem]
''',
        '''def scheduleContainers(host_cpu, host_mem, containers):
    free_cpu, free_mem = host_cpu, host_mem
    placed, rejected, cl, ml = [], [], 0, 0
    for name, cr, mr, c, m in containers:
        if cr <= free_cpu and mr <= free_mem:
            placed.append(name); cl += c; ml += m
        else:
            rejected.append(name)
        free_cpu -= cr; free_mem -= mr
    return [placed, rejected, free_cpu, free_mem, 100 * cl // host_cpu, 100 * ml // host_mem]
''',
    ],
    guide=dict(
        prereqs="Lessons *What a container is* (cgroup limits) and *Orchestration with Docker Swarm*. Integer arithmetic.",
        intuition="Two different numbers describe a container. A **reservation** is a promise the scheduler must be able to keep, so reservations may "
                  "never add up to more than the host. A **limit** is only a ceiling, so limits may add up to far more than the host: that is overcommit. "
                  "Place by the first, report the second.",
        hints=[
            "Keep two running 'free' values and test both before subtracting either.",
            "A rejected container must not change the free amounts.",
            "When summing limits, replace 0 by the host capacity; use integer division `//` for the floor.",
        ],
        brute_force="The single ordered pass is the specification itself. (Finding the *best* subset to place would be a knapsack problem; it is not asked here.)",
        approach="Loop once; test; subtract and accumulate, or reject; compute the two percentages.\n\n**Dry run** (example): web fits → free 3500 / 7936. "
                 "db fits → 2000 / 3840. batch needs 2500 CPU > 2000 → rejected. cache fits → 1500 / 2816. CPU limits 1000 + 2000 + 500 = 3500 → 87 %. "
                 "Memory limits 512 + 4096 + 8192 (no limit counts as the host) = 12800 → 156 %.",
        complexity="Time O(n), space O(n) for the two name lists.",
        pitfalls="- Scheduling by limits.\n- Subtracting a rejected container's reservation.\n- Treating a limit of 0 as zero instead of unlimited.\n- Floating-point division for the percentage.",
        follow_up="Spread the containers over several hosts, choosing the host with the most free memory each time.",
    ),
),
dict(
    id="docker-scan-triage",
    title="Triage an Image Vulnerability Scan",
    difficulty="Easy",
    pattern="Security",
    entry="triageScan",
    description=r"""
An image scanner returns a long list of findings. Decide what to fix first. Write `triageScan(findings, ignore)`.

Each finding is a dict with keys `id` (for example `"CVE-2026-0001"`), `package`, `severity`
(`"CRITICAL"`, `"HIGH"`, `"MEDIUM"`, `"LOW"` or `"UNKNOWN"`), `score` (a number from 0 to 10) and `fixed_version`
(a string; `""` means no fix is available yet).

1. Drop findings whose `id` is in the `ignore` list.
2. Drop duplicates: keep only the first finding for each `(id, package)` pair.
3. Sort what is left by:
   1. severity, most serious first: CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN;
   2. fixable (non-empty `fixed_version`) before unfixable;
   3. higher `score` first;
   4. `id` ascending, then `package` ascending.

Return the list of `[id, package]` pairs in that order.

**Example:** findings `A` (HIGH, 7.5, fixable), `B` (CRITICAL, 9.8, no fix), `C` (HIGH, 8.1, no fix), `D` (HIGH, 7.0, fixable)
each in package `p`, `ignore = []` → `[["B","p"], ["A","p"], ["D","p"], ["C","p"]]`
""",
    starter='''def triageScan(findings, ignore):
    pass
''',
    solution='''def triageScan(findings, ignore):
    rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNKNOWN": 4}
    skip = set(ignore)
    seen, kept = set(), []
    for f in findings:
        key = (f["id"], f["package"])
        if f["id"] in skip or key in seen:
            continue
        seen.add(key)
        kept.append(f)
    kept.sort(key=lambda f: (rank[f["severity"]], 0 if f["fixed_version"] else 1, -f["score"], f["id"], f["package"]))
    return [[f["id"], f["package"]] for f in kept]
''',
    tests=[
        [[{"id": "A", "package": "p", "severity": "HIGH", "score": 7.5, "fixed_version": "1.2"},
          {"id": "B", "package": "p", "severity": "CRITICAL", "score": 9.8, "fixed_version": ""},
          {"id": "C", "package": "p", "severity": "HIGH", "score": 8.1, "fixed_version": ""},
          {"id": "D", "package": "p", "severity": "HIGH", "score": 7.0, "fixed_version": "2.0"}], []],
        [[], []],
        [[{"id": "A", "package": "p", "severity": "LOW", "score": 2, "fixed_version": ""}], ["A"]],
        [[{"id": "A", "package": "p", "severity": "LOW", "score": 2, "fixed_version": ""},
          {"id": "A", "package": "p", "severity": "CRITICAL", "score": 10, "fixed_version": "9"},
          {"id": "A", "package": "q", "severity": "MEDIUM", "score": 5, "fixed_version": "9"}], []],
        [[{"id": "Z", "package": "b", "severity": "MEDIUM", "score": 5.0, "fixed_version": "1"},
          {"id": "Z", "package": "a", "severity": "MEDIUM", "score": 5.0, "fixed_version": "1"},
          {"id": "Y", "package": "c", "severity": "MEDIUM", "score": 5.0, "fixed_version": "1"}], []],
        [[{"id": "U", "package": "p", "severity": "UNKNOWN", "score": 10, "fixed_version": "1"},
          {"id": "L", "package": "p", "severity": "LOW", "score": 0.1, "fixed_version": ""},
          {"id": "M", "package": "p", "severity": "MEDIUM", "score": 4, "fixed_version": ""},
          {"id": "H", "package": "p", "severity": "HIGH", "score": 7, "fixed_version": ""},
          {"id": "C", "package": "p", "severity": "CRITICAL", "score": 9, "fixed_version": ""}], []],
        [[{"id": "CVE-10", "package": "p", "severity": "HIGH", "score": 7, "fixed_version": "1"},
          {"id": "CVE-9", "package": "p", "severity": "HIGH", "score": 7, "fixed_version": "1"}], []],
        [[{"id": "A", "package": "p", "severity": "HIGH", "score": 9.9, "fixed_version": ""},
          {"id": "B", "package": "p", "severity": "HIGH", "score": 1.0, "fixed_version": "3"}], []],
        [[{"id": "A", "package": "p", "severity": "HIGH", "score": 9, "fixed_version": "1"},
          {"id": "B", "package": "p", "severity": "CRITICAL", "score": 9, "fixed_version": "1"},
          {"id": "C", "package": "p", "severity": "CRITICAL", "score": 9, "fixed_version": "1"}], ["B", "NOPE"]],
        [[{"id": "V%03d" % (i % 37), "package": "pkg%d" % (i % 5), "severity": ["LOW", "HIGH", "CRITICAL", "MEDIUM", "UNKNOWN"][i % 5],
           "score": (i * 7) % 11, "fixed_version": "1" if i % 3 else ""} for i in range(200)], ["V003", "V010"]],
        [[{"id": "A", "package": "p", "severity": "MEDIUM", "score": 5, "fixed_version": "0"},
          {"id": "B", "package": "p", "severity": "MEDIUM", "score": 6, "fixed_version": ""},
          {"id": "C", "package": "p", "severity": "MEDIUM", "score": 5.5, "fixed_version": "1.0.1"}], []],
    ],
    examples=1,
    wrong_solutions=[
        '''def triageScan(findings, ignore):
    kept = [f for f in findings if f["id"] not in ignore]
    kept.sort(key=lambda f: (f["severity"], -f["score"], f["id"]))
    return [[f["id"], f["package"]] for f in kept]
''',
        '''def triageScan(findings, ignore):
    rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNKNOWN": 4}
    seen, kept = set(), []
    for f in findings:
        if f["id"] in ignore or f["id"] in seen:
            continue
        seen.add(f["id"])
        kept.append(f)
    kept.sort(key=lambda f: (rank[f["severity"]], -f["score"], 0 if f["fixed_version"] else 1, f["id"], f["package"]))
    return [[f["id"], f["package"]] for f in kept]
''',
    ],
    guide=dict(
        prereqs="Lesson *Container security: least privilege in practice*. Sorting with a tuple key.",
        intuition="Triage is a sort with several criteria, most important first. Python compares tuples left to right, so build one tuple per finding "
                  "in which every element is 'smaller means earlier'. The 'fixable first' rule reflects practice: a fix you can apply today beats a higher score you can only wait on.",
        hints=[
            "Map severity words to numbers with a dictionary; alphabetical order of the words is wrong.",
            "Use `0 if fixed_version else 1` for fixable-first and `-score` for highest-first.",
            "Deduplicate with a set of `(id, package)` tuples while filtering, before sorting.",
        ],
        brute_force="Repeatedly search the remaining list for the most urgent finding (selection sort): O(n^2). The built-in sort does the same in O(n log n).",
        approach="Filter and deduplicate in one loop, sort with the key `(rank, unfixable, -score, id, package)`, project to pairs.\n\n"
                 "**Dry run** (example): keys are A `(1, 0, -7.5)`, B `(0, 1, -9.8)`, C `(1, 1, -8.1)`, D `(1, 0, -7.0)`. Sorted: B, A, D, C. "
                 "C has the highest HIGH score but no fix, so it comes after the fixable HIGH findings.",
        complexity="Time O(n log n), space O(n).",
        pitfalls="- Sorting severities as strings (`CRITICAL < HIGH < LOW < MEDIUM < UNKNOWN` alphabetically, which misplaces LOW).\n"
                 "- Deduplicating by id only: the same CVE in two packages is two things to fix.\n- Putting score ahead of fixability.\n- Forgetting the final tie-break, which makes output unstable.",
        follow_up="Group by package and report, for each, the lowest version that fixes all of its findings.",
    ),
),
dict(
    id="docker-platform-select",
    title="Select the Manifest for a Platform",
    difficulty="Medium",
    pattern="Multi-Architecture",
    entry="selectManifest",
    description=r"""
A multi-architecture image is an index of per-platform manifests. When you pull, the client picks one.
Write `selectManifest(manifests, platform)`.

- `manifests` is a list of dicts `{"digest": str, "os": str, "arch": str, "variant": str}` (`variant` may be `""`).
- `platform` is a string `os/arch` or `os/arch/variant`, for example `linux/arm/v7`.

**Normalise** architecture names on both sides first: `x86_64` → `amd64`, `aarch64` → `arm64`, `armhf` → `arm`.
Then fill in an empty variant: for `arm64` the variant is `v8`; for `arm` it is `v7`; for anything else it stays `""`.

A manifest is a **candidate** if its `os` and normalised `arch` equal the platform's, and:

- for `arch == "arm"`: the manifest's variant number is **less than or equal to** the platform's
  (a `v7` processor can run `v6` and `v5` code, not the reverse). Variants are `v5`, `v6`, `v7`;
- for every other architecture: the variant is ignored.

Choose the candidate with the **highest variant number** for `arm`; for other architectures (and for ties) choose the
candidate that appears first in the list. Return its `digest`, or `""` if there is no candidate.

**Example:** manifests `amd64 → "d1"`, `arm64 → "d2"`, `arm/v6 → "d3"`, `arm/v7 → "d4"` (all `linux`):
`"linux/aarch64"` → `"d2"`; `"linux/arm/v6"` → `"d3"`; `"linux/arm"` → `"d4"`; `"windows/amd64"` → `""`.
""",
    starter='''def selectManifest(manifests, platform):
    pass
''',
    solution='''def selectManifest(manifests, platform):
    alias = {"x86_64": "amd64", "aarch64": "arm64", "armhf": "arm"}

    def norm(arch, variant):
        arch = alias.get(arch, arch)
        if not variant:
            variant = "v8" if arch == "arm64" else "v7" if arch == "arm" else ""
        return arch, variant

    parts = platform.split("/")
    want_os = parts[0]
    want_arch, want_var = norm(parts[1], parts[2] if len(parts) > 2 else "")
    best, best_n = "", -1
    for m in manifests:
        arch, var = norm(m["arch"], m.get("variant", ""))
        if m["os"] != want_os or arch != want_arch:
            continue
        if arch == "arm":
            n = int(var[1:])
            if n > int(want_var[1:]):
                continue
        else:
            n = 0
        if n > best_n:
            best, best_n = m["digest"], n
    return best
''',
    tests=[
        [[{"digest": "d1", "os": "linux", "arch": "amd64", "variant": ""}, {"digest": "d2", "os": "linux", "arch": "arm64", "variant": ""},
          {"digest": "d3", "os": "linux", "arch": "arm", "variant": "v6"}, {"digest": "d4", "os": "linux", "arch": "arm", "variant": "v7"}], "linux/aarch64"],
        [[{"digest": "d1", "os": "linux", "arch": "amd64", "variant": ""}, {"digest": "d2", "os": "linux", "arch": "arm64", "variant": ""},
          {"digest": "d3", "os": "linux", "arch": "arm", "variant": "v6"}, {"digest": "d4", "os": "linux", "arch": "arm", "variant": "v7"}], "linux/arm/v6"],
        [[{"digest": "d1", "os": "linux", "arch": "amd64", "variant": ""}, {"digest": "d2", "os": "linux", "arch": "arm64", "variant": ""},
          {"digest": "d3", "os": "linux", "arch": "arm", "variant": "v6"}, {"digest": "d4", "os": "linux", "arch": "arm", "variant": "v7"}], "linux/arm"],
        [[{"digest": "d1", "os": "linux", "arch": "amd64", "variant": ""}], "windows/amd64"],
        [[], "linux/amd64"],
        [[{"digest": "w", "os": "windows", "arch": "amd64", "variant": ""}, {"digest": "l", "os": "linux", "arch": "x86_64", "variant": ""}], "linux/amd64"],
        [[{"digest": "a", "os": "linux", "arch": "arm", "variant": "v7"}], "linux/arm/v6"],
        [[{"digest": "a", "os": "linux", "arch": "arm", "variant": "v5"}, {"digest": "b", "os": "linux", "arch": "armhf", "variant": ""}], "linux/arm/v7"],
        [[{"digest": "a", "os": "linux", "arch": "arm", "variant": "v5"}, {"digest": "b", "os": "linux", "arch": "arm", "variant": "v6"}], "linux/armhf"],
        [[{"digest": "a", "os": "linux", "arch": "arm64", "variant": "v8"}, {"digest": "b", "os": "linux", "arch": "aarch64", "variant": ""}], "linux/arm64/v8"],
        [[{"digest": "a", "os": "linux", "arch": "amd64", "variant": "v3"}, {"digest": "b", "os": "linux", "arch": "amd64", "variant": ""}], "linux/x86_64"],
        [[{"digest": "a", "os": "linux", "arch": "arm64", "variant": ""}], "linux/arm/v7"],
        [[{"digest": "a", "os": "linux", "arch": "riscv64", "variant": ""}, {"digest": "b", "os": "linux", "arch": "s390x", "variant": ""}], "linux/s390x"],
        [[{"digest": "x", "os": "linux", "arch": "arm", "variant": "v6"}, {"digest": "y", "os": "linux", "arch": "arm", "variant": "v6"}], "linux/arm/v7"],
    ],
    examples=3,
    wrong_solutions=[
        '''def selectManifest(manifests, platform):
    parts = platform.split("/")
    for m in manifests:
        if m["os"] == parts[0] and m["arch"] == parts[1]:
            if len(parts) < 3 or m.get("variant", "") == parts[2]:
                return m["digest"]
    return ""
''',
        '''def selectManifest(manifests, platform):
    alias = {"x86_64": "amd64", "aarch64": "arm64", "armhf": "arm"}
    parts = platform.split("/")
    arch = alias.get(parts[1], parts[1])
    for m in manifests:
        if m["os"] == parts[0] and alias.get(m["arch"], m["arch"]) == arch:
            return m["digest"]
    return ""
''',
    ],
    guide=dict(
        prereqs="Lesson *Multi-architecture images*. Dictionaries for aliases; a 'best so far' scan.",
        intuition="Pulling is a matching problem. First make both sides speak the same vocabulary (`aarch64` and `arm64` are one architecture). "
                  "Then most architectures are a plain equality test; 32-bit Arm is the exception, where newer processors can run code built for older ones, "
                  "so you want the *newest variant that is not too new*.",
        hints=[
            "Write one `norm(arch, variant)` helper and use it for the platform and for every manifest.",
            "Turn `v7` into the number 7 so that variants can be compared.",
            "Keep the best candidate with a strict `>` comparison so that the earliest one wins ties.",
        ],
        brute_force="Exact string comparison of `os/arch/variant`. It fails for aliases, for defaulted variants, and for a `v7` device offered only a `v6` build.",
        approach="Parse the platform, normalise, scan the manifests keeping the best compatible one.\n\n**Dry run** `linux/arm` with the example list: "
                 "platform becomes `(linux, arm, v7)`. `d3` is arm v6: 6 <= 7 → candidate, best 6. `d4` is arm v7: 7 <= 7 → candidate, 7 > 6 → best. Answer `d4`.",
        complexity="Time O(n) in the number of manifests, space O(1).",
        pitfalls="- Comparing un-normalised names.\n- Letting a `v6` device take a `v7` build.\n- Applying variant rules to `amd64`, where this model ignores them.\n"
                 "- Returning the last match instead of the first on ties.",
        follow_up="Add emulation: if no native manifest exists but QEMU is registered, fall back to `amd64`.",
    ),
),
dict(
    id="docker-proxy-route",
    title="Route a Request Through a Reverse Proxy",
    difficulty="Medium",
    pattern="Reverse Proxy",
    entry="routeRequest",
    description=r"""
A reverse proxy picks a backend container from the request's host name and path.
Write `routeRequest(rules, host, path)`.

Each rule is `[host_pattern, path_prefix, backend]`.

**Host matching.** Lower-case the request host and remove a trailing `:port`. Patterns are lower-case and are one of:

- an exact name, `shop.example.com`: matches only that host (specificity 2);
- a wildcard, `*.example.com`: matches any host that ends with `.example.com` and has at least one character before
  it; it does **not** match `example.com` itself (specificity 1);
- `*`: matches every host (specificity 0).

**Path matching.** A prefix always starts with `/`. Prefix `/` matches every path. Any other prefix `P` (given
without a trailing slash) matches a path that equals `P` or starts with `P + "/"`. The path has no query string.

**Choosing.** Among the rules that match both, choose the one with the highest host specificity; then the longest
path prefix; then the one that appears first. Return its `backend`, or `"404"` if no rule matches.

**Example:** rules `[["*", "/", "web"], ["shop.example.com", "/api", "api"], ["*.example.com", "/api/v2", "api-v2"]]`:
`("Shop.Example.com:8080", "/api/v2/items")` → `"api"`; `("blog.example.com", "/api/v2")` → `"api-v2"`;
`("shop.example.com", "/apiary")` → `"web"`.
""",
    starter='''def routeRequest(rules, host, path):
    pass
''',
    solution='''def routeRequest(rules, host, path):
    host = host.lower()
    if ":" in host:
        host = host.rsplit(":", 1)[0]
    best, best_key = "404", None
    for pattern, prefix, backend in rules:
        if pattern == "*":
            spec = 0
        elif pattern.startswith("*."):
            suffix = pattern[1:]
            if not (host.endswith(suffix) and len(host) > len(suffix)):
                continue
            spec = 1
        else:
            if host != pattern:
                continue
            spec = 2
        if not (prefix == "/" or path == prefix or path.startswith(prefix + "/")):
            continue
        key = (spec, len(prefix))
        if best_key is None or key > best_key:
            best, best_key = backend, key
    return best
''',
    tests=[
        [[["*", "/", "web"], ["shop.example.com", "/api", "api"], ["*.example.com", "/api/v2", "api-v2"]], "Shop.Example.com:8080", "/api/v2/items"],
        [[["*", "/", "web"], ["shop.example.com", "/api", "api"], ["*.example.com", "/api/v2", "api-v2"]], "blog.example.com", "/api/v2"],
        [[["*", "/", "web"], ["shop.example.com", "/api", "api"], ["*.example.com", "/api/v2", "api-v2"]], "shop.example.com", "/apiary"],
        [[], "a.com", "/"],
        [[["a.com", "/", "a"]], "b.com", "/"],
        [[["*.example.com", "/", "wild"]], "example.com", "/"],
        [[["*.example.com", "/", "wild"]], "a.b.example.com", "/x"],
        [[["*.example.com", "/", "wild"]], "badexample.com", "/x"],
        [[["a.com", "/", "root"], ["a.com", "/static", "files"], ["a.com", "/static/img", "img"]], "a.com", "/static/img/logo.png"],
        [[["a.com", "/", "first"], ["a.com", "/", "second"]], "a.com", "/"],
        [[["*", "/admin", "admin"], ["a.com", "/", "site"]], "a.com", "/admin/users"],
        [[["*", "/admin", "admin"], ["*.a.com", "/", "sub"]], "x.a.com:443", "/admin"],
        [[["a.com", "/api", "api"]], "a.com", "/"],
        [[["a.com", "/api", "api"]], "A.COM", "/api"],
        [[["*", "/a", "one"], ["*", "/a/b", "two"], ["*", "/a/b/c", "three"]], "h", "/a/b/cd"],
    ],
    examples=3,
    wrong_solutions=[
        '''def routeRequest(rules, host, path):
    host = host.lower().split(":")[0]
    for pattern, prefix, backend in rules:
        host_ok = pattern == "*" or host == pattern or (pattern.startswith("*.") and host.endswith(pattern[1:]))
        if host_ok and path.startswith(prefix):
            return backend
    return "404"
''',
        '''def routeRequest(rules, host, path):
    host = host.lower().split(":")[0]
    best, best_len = "404", -1
    for pattern, prefix, backend in rules:
        if pattern == "*":
            ok = True
        elif pattern.startswith("*."):
            ok = host.endswith(pattern[1:]) and len(host) > len(pattern) - 1
        else:
            ok = host == pattern
        if ok and (prefix == "/" or path == prefix or path.startswith(prefix + "/")) and len(prefix) > best_len:
            best, best_len = backend, len(prefix)
    return best
''',
    ],
    guide=dict(
        prereqs="Lesson *Reverse proxies in front of containers*. String methods; choosing a maximum by a tuple key.",
        intuition="Routing is 'most specific rule wins'. Specific has two dimensions, the host and the path, and the host is the more important one. "
                  "Score every matching rule with the pair `(host specificity, prefix length)` and take the largest; a strict comparison keeps the first on ties.",
        hints=[
            "Normalise the request host once: lower-case, then cut the port.",
            "For `*.example.com` compare against the suffix `.example.com` and require something in front of it.",
            "A path prefix must end on a segment boundary: test `path == P or path.startswith(P + '/')`.",
        ],
        brute_force="Return the first rule that matches. That makes the outcome depend on the order rules were written in, and a catch-all placed first swallows everything.",
        approach="Loop over the rules; skip those whose host or path does not match; keep the best key.\n\n**Dry run** `shop.example.com`, `/api/v2/items`: "
                 "rule 1 `*`, `/` → key `(0, 1)`. Rule 2 exact host, `/api` → path starts with `/api/` → key `(2, 4)`. Rule 3 wildcard, `/api/v2` → key `(1, 7)`. "
                 "Largest is `(2, 4)` → `api`: the exact host outranks the longer prefix.",
        complexity="Time O(R x L) for R rules and string length L, space O(1).",
        pitfalls="- Plain `startswith` for paths (`/api` would match `/apiary`).\n- A wildcard matching the bare domain or `badexample.com`.\n"
                 "- Letting prefix length outrank host specificity.\n- Case-sensitive host comparison, or forgetting the port.",
        follow_up="Add weighted load balancing across several backends per rule, or path rewriting that strips the matched prefix.",
    ),
),
]
