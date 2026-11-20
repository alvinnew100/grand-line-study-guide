PROBLEMS = [
dict(
    id="cicd-pipeline-stage-order",
    title="Pipeline Stage Order",
    difficulty="Medium",
    pattern="Graphs / Topological Sort",
    entry="stage_order",
    description=r"""
A pipeline is a set of **jobs**. Each job lists the jobs it *needs*: those must finish before it may start.

You are given `jobs`, a dictionary mapping every job name to the list of job names it needs (every needed
name is itself a key). Return one order in which a single runner could execute all the jobs.

Rules:

- A job may appear only after every job it needs.
- **Tie-break:** whenever several jobs are ready, pick the one whose name is smallest alphabetically.
  This makes the answer unique.
- If the definition contains a cycle (so no valid order exists), return an empty list `[]`.

**Example 1:** `{"build": ["lint", "test"], "lint": [], "test": [], "deploy": ["build"]}` → `["lint", "test", "build", "deploy"]`

**Example 2:** `{"a": ["b"], "b": ["a"]}` → `[]` (a cycle)
""",
    starter='''def stage_order(jobs: Dict[str, List[str]]) -> List[str]:
    pass
''',
    solution='''import heapq

def stage_order(jobs):
    waiting = {name: len(set(needs)) for name, needs in jobs.items()}
    dependants = {name: [] for name in jobs}
    for name, needs in jobs.items():
        for n in set(needs):
            dependants[n].append(name)
    ready = [name for name, k in waiting.items() if k == 0]
    heapq.heapify(ready)
    order = []
    while ready:
        job = heapq.heappop(ready)
        order.append(job)
        for d in dependants[job]:
            waiting[d] -= 1
            if waiting[d] == 0:
                heapq.heappush(ready, d)
    return order if len(order) == len(jobs) else []
''',
    tests=[
        [{"build": ["lint", "test"], "lint": [], "test": [], "deploy": ["build"]}],
        [{"a": ["b"], "b": ["a"]}],
        [{}],
        [{"only": []}],
        [{"c": [], "b": [], "a": []}],
        [{"z": [], "a": ["z"], "b": ["z"], "m": ["a", "b"]}],
        [{"deploy": ["build"], "build": ["unit"], "unit": ["lint"], "lint": []}],
        [{"a": [], "b": ["a"], "c": ["b"], "d": ["c", "a"], "e": ["x"], "x": ["e"]}],
        [{"self": ["self"]}],
        [{"b": [], "a": ["c"], "c": []}],
        [{"d": ["b", "b"], "b": [], "a": ["d"]}],
        [{f"job{i:03d}": ([f"job{i - 1:03d}"] if i else []) for i in range(300)}],
        [{f"j{i:03d}": [f"j{j:03d}" for j in range(i + 1, min(i + 4, 200))] for i in range(200)}],
    ],
    examples=2,
    wrong_solutions=[
        '''def stage_order(jobs):
    return sorted(jobs)
''',
        '''def stage_order(jobs):
    order, seen = [], set()
    def visit(j):
        if j in seen:
            return
        seen.add(j)
        for n in jobs[j]:
            visit(n)
        order.append(j)
    for j in jobs:
        visit(j)
    return order
''',
    ],
    guide=dict(
        prereqs="Dictionaries and lists. The idea of a directed graph: here an arrow runs from a job to each job that needs it. "
                "A heap (priority queue) helps but is not required. See the lesson *Stages, gates and the flow of a change*.",
        intuition="A job is *ready* when everything it needs has already run. Keep running a ready job, which may make other jobs ready. "
                  "If you run out of ready jobs before every job has run, the leftover jobs are waiting on each other in a circle.",
        hints=[
            "For every job, count how many distinct jobs it still waits for.",
            "Jobs whose count is 0 can run now. After running one, lower the count of every job that needs it.",
            "Always take the alphabetically smallest ready job (a min-heap gives this quickly). If the result is shorter than the number of jobs, return [].",
        ],
        brute_force="Repeatedly scan all jobs for the alphabetically smallest one whose needs have all run. Each scan costs O(V + E), "
                    "and you do it V times, so O(V * (V + E)). Fine for a few hundred jobs, slow for thousands.",
        approach="This is **Kahn's algorithm** with a min-heap.\n\n"
                 "1. `waiting[job]` = number of distinct jobs it needs. `dependants[x]` = jobs that need `x`.\n"
                 "2. Put every job with `waiting == 0` into a min-heap.\n"
                 "3. Pop the smallest name, append it to the answer, and decrement `waiting` for each of its dependants; push any that reach 0.\n"
                 "4. If the answer contains every job, return it; otherwise there is a cycle, so return `[]`.\n\n"
                 "**Dry run** on Example 1: waiting = build 2, lint 0, test 0, deploy 1. Heap = [lint, test]. Pop `lint` -> build 1. "
                 "Pop `test` -> build 0, push build. Pop `build` -> deploy 0, push deploy. Pop `deploy`. Answer: lint, test, build, deploy.",
        complexity="Time O((V + E) log V): each job enters and leaves the heap once and each dependency is examined once. Space O(V + E).",
        pitfalls="- A depth-first order is a valid topological order but does not respect the alphabetical tie-break.\n"
                 "- A job may list the same need twice; count distinct needs, or the count never reaches 0.\n"
                 "- A job that needs itself is a cycle.\n"
                 "- Do not forget the empty pipeline: the answer is `[]`.",
        follow_up="Group the jobs into *waves* that can run in parallel. Or compute the wall-clock time with unlimited runners (see *Pipeline Wall-Clock Time*).",
    ),
),
dict(
    id="cicd-pipeline-duration",
    title="Pipeline Wall-Clock Time",
    difficulty="Medium",
    pattern="Graphs / Longest Path in a DAG",
    entry="pipeline_duration",
    description=r"""
Every job in a pipeline has a duration in minutes and a list of jobs it needs. With **unlimited runners**, a job
starts the moment all the jobs it needs have finished (or at minute 0 if it needs nothing).

`jobs` maps each job name to a two-element list `[minutes, needs]`. Return the minute at which the last job
finishes. The definition is guaranteed to have no cycles. An empty pipeline takes `0` minutes.

**Example 1:** `{"lint": [1, []], "unit": [4, []], "build": [3, ["lint", "unit"]], "deploy": [5, ["build"]]}` → `12`
(`build` starts at 4 when `unit` ends; `deploy` starts at 7 and ends at 12)

**Example 2:** `{"a": [10, []], "b": [25, []]}` → `25` (they run side by side)
""",
    starter='''def pipeline_duration(jobs: Dict[str, list]) -> int:
    pass
''',
    solution='''import sys

def pipeline_duration(jobs):
    sys.setrecursionlimit(max(10000, len(jobs) * 3))
    finish = {}
    def end(name):
        if name not in finish:
            minutes, needs = jobs[name]
            finish[name] = minutes + max((end(n) for n in needs), default=0)
        return finish[name]
    return max((end(name) for name in jobs), default=0)
''',
    tests=[
        [{"lint": [1, []], "unit": [4, []], "build": [3, ["lint", "unit"]], "deploy": [5, ["build"]]}],
        [{"a": [10, []], "b": [25, []]}],
        [{}],
        [{"solo": [7, []]}],
        [{"a": [0, []], "b": [0, ["a"]]}],
        [{"a": [5, []], "b": [1, ["a"]], "c": [1, ["a"]], "d": [1, ["b", "c"]]}],
        [{"fast": [1, []], "slow": [30, []], "join": [2, ["fast", "slow"]], "tail": [3, ["join"]], "side": [40, ["fast"]]}],
        [{"a": [3, []], "b": [3, ["a"]], "c": [3, ["b"]], "d": [100, []]}],
        [{"x": [2, []], "y": [2, ["x", "x"]]}],
        [{f"j{i}": [i % 7 + 1, ([f"j{i - 1}"] if i else [])] for i in range(400)}],
        [{f"j{i}": [i % 5 + 1, [f"j{k}" for k in range(max(0, i - 3), i)]] for i in range(300)}],
    ],
    examples=2,
    wrong_solutions=[
        '''def pipeline_duration(jobs):
    return sum(m for m, _ in jobs.values())
''',
        '''def pipeline_duration(jobs):
    return max((m for m, _ in jobs.values()), default=0)
''',
    ],
    guide=dict(
        prereqs="Dictionaries, recursion or a topological order, and the idea of memoisation (remembering results you have already computed).",
        intuition="A job cannot start before the *slowest* of its prerequisites has finished. So its finish time is its own duration plus the "
                  "largest finish time among the jobs it needs. The pipeline ends when the last job ends.",
        hints=[
            "Parallel jobs do not add up; only chains do.",
            "finish(job) = minutes(job) + max(finish(n) for n in needs), or just minutes(job) when it needs nothing.",
            "Store each finish time the first time you compute it, then return the largest one.",
        ],
        brute_force="Enumerate every path through the graph and take the longest. A graph with many joins can have an exponential number of paths.",
        approach="Compute `finish[name]` with memoised recursion (or process jobs in topological order):\n\n"
                 "1. `finish(job) = minutes + max(finish(need) for need in needs)`; an empty `needs` contributes 0.\n"
                 "2. The answer is the maximum `finish` over all jobs.\n\n"
                 "**Dry run** on Example 1: finish(lint)=1, finish(unit)=4, finish(build)=3+max(1,4)=7, finish(deploy)=5+7=12. Maximum = 12.",
        complexity="Time O(V + E): each job is computed once and each dependency is looked at once. Space O(V) for the table.",
        pitfalls="- Summing all durations gives machine time, not wall-clock time.\n"
                 "- Taking the single longest job ignores chains.\n"
                 "- Without memoisation, shared prerequisites are recomputed again and again.\n"
                 "- Very long chains can exceed Python's default recursion limit; raise it or iterate in topological order.",
        follow_up="Limit the number of runners to k. The problem then becomes scheduling, which is much harder, and greedy heuristics are used in practice.",
    ),
),
dict(
    id="cicd-jobs-to-rerun",
    title="Which Jobs Must Rerun?",
    difficulty="Medium",
    pattern="Graphs / BFS",
    entry="jobs_to_rerun",
    description=r"""
A CI system runs a job only when a change could affect it.

- `job_paths` maps each job to a list of path patterns it watches.
- `needs` maps each job to the jobs it needs (its upstream jobs). Every job appears as a key in both dictionaries.
- `changed` is the list of files changed by a commit.

A pattern matches a file when:

- the pattern ends with `/` and the file path **starts with** the pattern (a directory), or
- the pattern equals the file path exactly, or
- the pattern is `*` (matches every file).

A job is **triggered** if any changed file matches any of its patterns. A job must also rerun if any job it needs
(directly or indirectly) reruns, because its inputs may have changed.

Return the names of all jobs that must rerun, sorted alphabetically.

**Example 1:** `job_paths = {"lint": ["src/"], "docs": ["docs/"], "build": ["Dockerfile"], "deploy": []}`,
`needs = {"lint": [], "docs": [], "build": ["lint"], "deploy": ["build"]}`, `changed = ["src/app.py"]`
→ `["build", "deploy", "lint"]`

**Example 2:** same pipeline, `changed = ["docs/index.md"]` → `["docs"]`
""",
    starter='''def jobs_to_rerun(job_paths: Dict[str, List[str]], needs: Dict[str, List[str]], changed: List[str]) -> List[str]:
    pass
''',
    solution='''from collections import deque

def jobs_to_rerun(job_paths, needs, changed):
    def matches(pattern, path):
        if pattern == "*":
            return True
        if pattern.endswith("/"):
            return path.startswith(pattern)
        return pattern == path
    triggered = {job for job, patterns in job_paths.items()
                 if any(matches(p, f) for p in patterns for f in changed)}
    downstream = {job: [] for job in needs}
    for job, ups in needs.items():
        for u in ups:
            downstream[u].append(job)
    seen, queue = set(triggered), deque(triggered)
    while queue:
        for d in downstream[queue.popleft()]:
            if d not in seen:
                seen.add(d)
                queue.append(d)
    return sorted(seen)
''',
    tests=[
        [{"lint": ["src/"], "docs": ["docs/"], "build": ["Dockerfile"], "deploy": []},
         {"lint": [], "docs": [], "build": ["lint"], "deploy": ["build"]}, ["src/app.py"]],
        [{"lint": ["src/"], "docs": ["docs/"], "build": ["Dockerfile"], "deploy": []},
         {"lint": [], "docs": [], "build": ["lint"], "deploy": ["build"]}, ["docs/index.md"]],
        [{"lint": ["src/"], "docs": ["docs/"], "build": ["Dockerfile"], "deploy": []},
         {"lint": [], "docs": [], "build": ["lint"], "deploy": ["build"]}, []],
        [{"lint": ["src/"], "docs": ["docs/"], "build": ["Dockerfile"], "deploy": []},
         {"lint": [], "docs": [], "build": ["lint"], "deploy": ["build"]}, ["Dockerfile"]],
        [{"lint": ["src/"], "docs": ["docs/"], "build": ["Dockerfile"], "deploy": []},
         {"lint": [], "docs": [], "build": ["lint"], "deploy": ["build"]}, ["Dockerfile.dev", "src2/app.py", "README.md"]],
        [{"a": ["src/app"], "b": ["src/app/"]}, {"a": [], "b": []}, ["src/application.py"]],
        [{"a": ["src/app"], "b": ["src/app/"]}, {"a": [], "b": []}, ["src/app/main.py"]],
        [{"a": ["src/app"], "b": ["src/app/"]}, {"a": [], "b": []}, ["src/app"]],
        [{"all": ["*"], "x": ["x/"], "y": []}, {"all": [], "x": [], "y": ["x"]}, ["anything.txt"]],
        [{"a": ["a/"], "b": [], "c": [], "d": []}, {"a": [], "b": ["a"], "c": ["b"], "d": ["c", "a"]}, ["a/1", "a/2"]],
        [{"a": ["a/"], "b": ["b/"], "c": []}, {"a": [], "b": [], "c": ["a", "b"]}, ["b/x"]],
        [{f"j{i:03d}": [f"p{i}/"] for i in range(200)},
         {f"j{i:03d}": ([f"j{i - 1:03d}"] if i else []) for i in range(200)}, ["p150/file"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def jobs_to_rerun(job_paths, needs, changed):
    def matches(pattern, path):
        return pattern == "*" or (pattern.endswith("/") and path.startswith(pattern)) or pattern == path
    return sorted(j for j, ps in job_paths.items() if any(matches(p, f) for p in ps for f in changed))
''',
        '''from collections import deque

def jobs_to_rerun(job_paths, needs, changed):
    triggered = {j for j, ps in job_paths.items()
                 if any(p == "*" or f.startswith(p) for p in ps for f in changed)}
    downstream = {j: [] for j in needs}
    for j, ups in needs.items():
        for u in ups:
            downstream[u].append(j)
    seen, queue = set(triggered), deque(triggered)
    while queue:
        for d in downstream[queue.popleft()]:
            if d not in seen:
                seen.add(d); queue.append(d)
    return sorted(seen)
''',
    ],
    guide=dict(
        prereqs="String methods `startswith` and `endswith`, sets, and breadth-first search on a graph. See the lesson *Designing a fast commit stage*.",
        intuition="There are two separate questions. First: which jobs are hit *directly* by the changed files? Second: which jobs sit "
                  "downstream of those? The second is a walk along the arrows of the dependency graph, turned around.",
        hints=[
            "Write a small function `matches(pattern, path)` that implements the three matching rules exactly.",
            "`needs` points upstream. Build the reverse map: for each job, which jobs need it?",
            "Start a breadth-first search from all directly triggered jobs and collect everything reachable.",
        ],
        brute_force="Repeat until nothing changes: for every job, mark it if any job it needs is marked. Each pass is O(V + E) and up to V passes "
                    "may be needed, giving O(V * (V + E)).",
        approach="1. `triggered` = jobs with at least one (pattern, file) match.\n"
                 "2. Build `downstream[u]` = list of jobs that list `u` in their `needs`.\n"
                 "3. Breadth-first search from `triggered` over `downstream`, collecting visited jobs.\n"
                 "4. Return them sorted.\n\n"
                 "**Dry run** on Example 1: `src/app.py` starts with `src/`, so `lint` is triggered. downstream: lint -> [build], build -> [deploy]. "
                 "BFS visits lint, build, deploy. Sorted: build, deploy, lint.",
        complexity="Matching costs O(P * F) for P patterns and F changed files. The search is O(V + E). Space O(V + E).",
        pitfalls="- A pattern without a trailing slash is an exact file name: `src/app` must not match `src/application.py`.\n"
                 "- `Dockerfile` must not match `Dockerfile.dev`.\n"
                 "- Forgetting downstream jobs means a deploy could reuse a stale build.\n"
                 "- With no changed files, nothing reruns.",
        follow_up="Real systems also treat some files (the lockfile, the CI configuration) as affecting every job. How would you add that?",
    ),
),
dict(
    id="cicd-monorepo-rebuild-set",
    title="Monorepo: Minimal Rebuild Set",
    difficulty="Medium",
    pattern="Graphs / BFS",
    entry="rebuild_set",
    description=r"""
A monorepo holds several projects. Given the files changed by a commit, find the smallest set of projects that
must be rebuilt.

- `roots` maps each project to its root directory (always ending with `/`). Roots can be nested, for example
  `libs/` and `libs/pricing/`.
- `deps` maps each project to the projects it depends on. Every project is a key in both dictionaries.
- `global_files` lists paths that affect **everything** (for example the lockfile). An entry ending with `/` is a
  directory prefix; any other entry is an exact file path.
- `changed` is the list of changed files.

Rules:

1. If any changed file matches an entry of `global_files`, every project must be rebuilt.
2. Otherwise each changed file belongs to the project whose root is the **longest** prefix of the file path.
   A file that is under no root belongs to no project and is ignored.
3. A project must be rebuilt if it owns a changed file, or if it depends (directly or indirectly) on a project that
   must be rebuilt.

Return the project names sorted alphabetically.

**Example 1:** `roots = {"pricing": "libs/pricing/", "orders": "services/orders/", "web": "apps/web/"}`,
`deps = {"pricing": [], "orders": ["pricing"], "web": []}`, `global_files = ["pnpm-lock.yaml"]`,
`changed = ["libs/pricing/tax.py"]` → `["orders", "pricing"]`

**Example 2:** same repository, `changed = ["README.md"]` → `[]`
""",
    starter='''def rebuild_set(roots: Dict[str, str], deps: Dict[str, List[str]], global_files: List[str], changed: List[str]) -> List[str]:
    pass
''',
    solution='''from collections import deque

def rebuild_set(roots, deps, global_files, changed):
    def is_global(path):
        return any(path.startswith(g) if g.endswith("/") else path == g for g in global_files)
    if any(is_global(f) for f in changed):
        return sorted(roots)
    direct = set()
    for f in changed:
        best, best_len = None, -1
        for project, root in roots.items():
            if f.startswith(root) and len(root) > best_len:
                best, best_len = project, len(root)
        if best is not None:
            direct.add(best)
    dependants = {p: [] for p in deps}
    for p, ds in deps.items():
        for d in ds:
            dependants[d].append(p)
    seen, queue = set(direct), deque(direct)
    while queue:
        for nxt in dependants[queue.popleft()]:
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return sorted(seen)
''',
    tests=[
        [{"pricing": "libs/pricing/", "orders": "services/orders/", "web": "apps/web/"},
         {"pricing": [], "orders": ["pricing"], "web": []}, ["pnpm-lock.yaml"], ["libs/pricing/tax.py"]],
        [{"pricing": "libs/pricing/", "orders": "services/orders/", "web": "apps/web/"},
         {"pricing": [], "orders": ["pricing"], "web": []}, ["pnpm-lock.yaml"], ["README.md"]],
        [{"pricing": "libs/pricing/", "orders": "services/orders/", "web": "apps/web/"},
         {"pricing": [], "orders": ["pricing"], "web": []}, ["pnpm-lock.yaml"], ["pnpm-lock.yaml"]],
        [{"pricing": "libs/pricing/", "orders": "services/orders/", "web": "apps/web/"},
         {"pricing": [], "orders": ["pricing"], "web": []}, ["pnpm-lock.yaml"], []],
        [{"pricing": "libs/pricing/", "orders": "services/orders/", "web": "apps/web/"},
         {"pricing": [], "orders": ["pricing"], "web": []}, [".github/workflows/"], ["apps/web/a.ts", ".github/workflows/ci.yml"]],
        [{"pricing": "libs/pricing/", "orders": "services/orders/", "web": "apps/web/"},
         {"pricing": [], "orders": ["pricing"], "web": []}, ["pnpm-lock.yaml"], ["apps/web/a.ts", "docs/x.md"]],
        [{"libs": "libs/", "pricing": "libs/pricing/", "app": "app/"},
         {"libs": [], "pricing": [], "app": ["pricing"]}, [], ["libs/pricing/x.py"]],
        [{"libs": "libs/", "pricing": "libs/pricing/", "app": "app/"},
         {"libs": [], "pricing": [], "app": ["pricing"]}, [], ["libs/util.py"]],
        [{"a": "a/", "b": "b/", "c": "c/", "d": "d/"},
         {"a": [], "b": ["a"], "c": ["b"], "d": ["a", "c"]}, ["lock"], ["a/x"]],
        [{"a": "a/", "b": "b/", "c": "c/", "d": "d/"},
         {"a": [], "b": ["a"], "c": ["b"], "d": ["a", "c"]}, ["lock"], ["c/x", "lock.bak"]],
        [{"a": "a/", "ab": "ab/"}, {"a": [], "ab": []}, ["tools/"], ["ab/file", "tools"]],
        [{f"p{i:03d}": f"pkg/p{i:03d}/" for i in range(150)},
         {f"p{i:03d}": ([f"p{i - 1:03d}"] if i else []) for i in range(150)}, ["go.sum"], ["pkg/p100/main.go"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def rebuild_set(roots, deps, global_files, changed):
    return sorted({p for f in changed for p, r in roots.items() if f.startswith(r)})
''',
        '''from collections import deque

def rebuild_set(roots, deps, global_files, changed):
    direct = {p for f in changed for p, r in roots.items() if f.startswith(r)}
    dependants = {p: [] for p in deps}
    for p, ds in deps.items():
        for d in ds:
            dependants[d].append(p)
    seen, queue = set(direct), deque(direct)
    while queue:
        for nxt in dependants[queue.popleft()]:
            if nxt not in seen:
                seen.add(nxt); queue.append(nxt)
    return sorted(seen)
''',
    ],
    guide=dict(
        prereqs="String prefixes, sets, and breadth-first search. See the lesson *Monorepo vs polyrepo and artifact versioning*.",
        intuition="Three steps: an escape hatch (global files rebuild everything), ownership (which project does each file belong to?), and "
                  "propagation (whoever depends on a rebuilt project is rebuilt too). 'Minimal' means you add nothing beyond what these rules force.",
        hints=[
            "Handle the global-file rule first; if it fires you can return all projects straight away.",
            "For ownership, compare every root that is a prefix of the file and keep the longest. A file may match none.",
            "Reverse the `deps` map and run a breadth-first search from the directly changed projects.",
        ],
        brute_force="For each project, search its dependencies recursively to see whether any directly changed project is reachable. "
                    "That repeats the same walks many times: O(V * (V + E)).",
        approach="1. If any changed file equals a global file, or starts with a global directory, return every project sorted.\n"
                 "2. For each changed file pick the project with the longest matching root; collect these in `direct`.\n"
                 "3. Build `dependants[x]` = projects that list `x` in their dependencies.\n"
                 "4. BFS from `direct` across `dependants`; return the visited set sorted.\n\n"
                 "**Dry run** on Example 1: `libs/pricing/tax.py` is under `libs/pricing/`, so direct = {pricing}. dependants: pricing -> [orders]. "
                 "BFS gives {pricing, orders}. Sorted: orders, pricing.",
        complexity="Ownership is O(F * P) for F files and P projects. The search is O(V + E). Space O(V + E).",
        pitfalls="- With nested roots, a file under `libs/pricing/` belongs to `pricing`, not also to `libs`.\n"
                 "- A global entry without a trailing slash is an exact file: `lock` must not match `lock.bak`, and `tools/` must not match a file called `tools`.\n"
                 "- Files outside every root (for example a top-level README) trigger nothing.\n"
                 "- Dependencies are followed in reverse: you want who depends on the changed project.",
        follow_up="Return the projects in a valid build order instead of alphabetically, combining this with *Pipeline Stage Order*.",
    ),
),
dict(
    id="cicd-test-sharding",
    title="Balance Tests Across Runners",
    difficulty="Medium",
    pattern="Greedy / Heap",
    entry="shard_tests",
    description=r"""
A test suite is split across `n` parallel runners ("shards"). The suite finishes when the slowest shard finishes,
so the shards should carry similar loads.

`durations[i]` is the running time of test file `i` in seconds. Assign every file to a shard using this exact
greedy rule (known as *longest processing time first*):

1. Consider the files from longest to shortest. Break ties by smaller index first.
2. Give each file to the shard whose total load so far is smallest. Break ties by smaller shard number.

Return a list `shard` where `shard[i]` is the shard number (from `0` to `n - 1`) of file `i`.

**Example 1:** `durations = [8, 3, 5, 4]`, `n = 2` → `[0, 1, 1, 0]`
(8 → shard 0; 5 → shard 1; 4 → shard 1, now 9; 3 → shard 0, now 11)

**Example 2:** `durations = [5, 5, 5]`, `n = 3` → `[0, 1, 2]`

Constraints: `1 <= n`, `0 <= len(durations) <= 10^4`, durations are non-negative integers.
""",
    starter='''def shard_tests(durations: List[int], n: int) -> List[int]:
    pass
''',
    solution='''import heapq

def shard_tests(durations, n):
    order = sorted(range(len(durations)), key=lambda i: (-durations[i], i))
    heap = [(0, s) for s in range(n)]
    heapq.heapify(heap)
    result = [0] * len(durations)
    for i in order:
        load, s = heapq.heappop(heap)
        result[i] = s
        heapq.heappush(heap, (load + durations[i], s))
    return result
''',
    tests=[
        [[8, 3, 5, 4], 2],
        [[5, 5, 5], 3],
        [[], 4],
        [[7], 1],
        [[7], 5],
        [[1, 2, 3, 4, 5, 6], 1],
        [[0, 0, 0, 0], 2],
        [[10, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], 2],
        [[4, 4, 4, 4, 4], 2],
        [[3, 9, 2, 9, 7, 1], 3],
        [[2, 1, 2, 1, 2, 1, 2], 4],
        [[(i * 37) % 101 + 1 for i in range(2000)], 8],
        [[(i * i) % 53 for i in range(5000)], 16],
    ],
    examples=2,
    wrong_solutions=[
        '''def shard_tests(durations, n):
    return [i % n for i in range(len(durations))]
''',
        '''def shard_tests(durations, n):
    loads = [0] * n
    result = []
    for d in durations:
        s = loads.index(min(loads))
        result.append(s)
        loads[s] += d
    return result
''',
    ],
    guide=dict(
        prereqs="Sorting with a key, and either `list.index(min(...))` or a heap. See the lesson *Designing a fast commit stage*.",
        intuition="Place the big items first, while there is still room to balance them, and always top up the emptiest shard. "
                  "Small items then fill the gaps. Finding the truly best split is a hard problem, so this greedy rule is what tools use.",
        hints=[
            "Sort the *indices* of the files, not the durations, so you can still fill in `shard[i]` afterwards.",
            "Sort key: `(-durations[i], i)` gives longest first with ties by smaller index.",
            "Keep `(load, shard_number)` pairs in a min-heap; the smallest pair is exactly the shard the rule asks for.",
        ],
        brute_force="Try every assignment of files to shards and keep the one with the smallest maximum load: n^m possibilities for m files. "
                    "That is impossible beyond a handful of files, which is why the task fixes a greedy rule.",
        approach="1. `order` = indices sorted by `(-duration, index)`.\n"
                 "2. Heap of `(0, s)` for each shard `s`.\n"
                 "3. For each index in `order`: pop the lightest shard, record it for that file, push it back with the file's duration added.\n\n"
                 "**Dry run** on Example 1: order = [0 (8), 2 (5), 3 (4), 1 (3)]. Heap (0,0),(0,1). File 0 -> shard 0 (8). File 2 -> shard 1 (5). "
                 "File 3 -> shard 1 (9). File 1 -> shard 0 (11). Result [0, 1, 1, 0].",
        complexity="Time O(m log m + m log n) for m files and n shards. Space O(m + n).",
        pitfalls="- Round-robin by position ignores durations and can put all the slow files on one shard.\n"
                 "- Assigning in the original order without sorting gives a different, usually worse, answer.\n"
                 "- The tie-breaks matter for a unique answer: equal durations go by smaller index, equal loads by smaller shard number.\n"
                 "- More shards than files is fine: some shards stay empty.",
        follow_up="Return the wall-clock time (the largest shard load). How close can greedy get to the ideal of total / n, and what bounds it from below?",
    ),
),
dict(
    id="cicd-cache-key",
    title="Dependency Cache Key and Lookup",
    difficulty="Easy",
    pattern="Hashing / Strings",
    entry="cache_plan",
    description=r"""
A CI job caches downloaded dependencies. The cache is stored under a **key** that must change exactly when the
dependencies change.

Build the key like this:

1. Normalise the lockfile text by replacing every Windows line ending `"\r\n"` with `"\n"`.
2. Compute the SHA-256 hash of the normalised text encoded as UTF-8, written in lowercase hexadecimal, and keep
   the **first 12 characters**.
3. The key is `"deps-" + os_name + "-" + those 12 characters`.

`saved` lists the keys of the caches that already exist, oldest first. Decide what the job restores:

- if the key is in `saved`: an **exact** hit, restoring that key;
- otherwise, if some saved key starts with `"deps-" + os_name + "-"`: a **partial** hit, restoring the *most
  recently saved* such key (the last one in the list);
- otherwise a **miss**, restoring nothing.

Return `[key, status, restored]` where `status` is `"exact"`, `"partial"` or `"miss"` and `restored` is the
restored key or `None`.

**Example 1:** `os_name = "Linux"`, `lockfile = "a==1\n"`, `saved = []` → `["deps-Linux-a6ad7b420d04", "miss", None]`

**Example 2:** `os_name = "Linux"`, `lockfile = "a==1\r\n"`, `saved = ["deps-Linux-a6ad7b420d04"]` →
`["deps-Linux-a6ad7b420d04", "exact", "deps-Linux-a6ad7b420d04"]` (line endings do not change the key)

Use `hashlib.sha256` from the standard library.
""",
    starter='''import hashlib

def cache_plan(os_name: str, lockfile: str, saved: List[str]) -> list:
    pass
''',
    solution='''import hashlib

def cache_plan(os_name, lockfile, saved):
    text = lockfile.replace("\\r\\n", "\\n")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    prefix = "deps-" + os_name + "-"
    key = prefix + digest
    if key in saved:
        return [key, "exact", key]
    partial = [k for k in saved if k.startswith(prefix)]
    if partial:
        return [key, "partial", partial[-1]]
    return [key, "miss", None]
''',
    tests=[
        ["Linux", "a==1\n", []],
        ["Linux", "a==1\r\n", ["deps-Linux-a6ad7b420d04"]],
        ["Linux", "a==2\n", ["deps-Linux-a6ad7b420d04"]],
        ["Windows", "a==1\n", ["deps-Linux-a6ad7b420d04"]],
        ["Linux", "a==2\n", ["deps-Linux-aaa", "deps-Windows-bbb", "deps-Linux-ccc", "deps-macOS-ddd"]],
        ["Linux", "", []],
        ["Linux", "", ["deps-Linux-e3b0c44298fc"]],
        ["Linux", "x\r\ny\r\nz", ["deps-Linux-old"]],
        ["Linux", "x\ny\nz", ["deps-Linux-old"]],
        ["Lin", "a==1\n", ["deps-Linux-a6ad7b420d04"]],
        ["macOS", "caf\u00e9==1\n", ["deps-macOS-1", "deps-macOS-2"]],
        ["Linux", "\n".join(f"pkg{i}=={i}" for i in range(3000)), ["deps-Linux-zzz"]],
    ],
    examples=2,
    wrong_solutions=[
        '''import hashlib

def cache_plan(os_name, lockfile, saved):
    digest = hashlib.sha256(lockfile.encode("utf-8")).hexdigest()[:12]
    prefix = "deps-" + os_name + "-"
    key = prefix + digest
    if key in saved:
        return [key, "exact", key]
    partial = [k for k in saved if k.startswith(prefix)]
    return [key, "partial", partial[-1]] if partial else [key, "miss", None]
''',
        '''import hashlib

def cache_plan(os_name, lockfile, saved):
    digest = hashlib.sha256(lockfile.replace("\\r\\n", "\\n").encode("utf-8")).hexdigest()[:12]
    prefix = "deps-" + os_name
    key = prefix + "-" + digest
    if key in saved:
        return [key, "exact", key]
    partial = [k for k in saved if k.startswith(prefix)]
    return [key, "partial", partial[0]] if partial else [key, "miss", None]
''',
    ],
    guide=dict(
        prereqs="Strings, `str.replace`, `str.startswith`, and calling `hashlib.sha256(data).hexdigest()`. "
                "See the lesson *A complete GitHub Actions pipeline, line by line*.",
        intuition="A hash is a fingerprint: the same text always gives the same fingerprint, and a tiny change gives a completely different one. "
                  "Putting the lockfile's fingerprint in the key means 'same dependencies, same key'. The operating system is in the key because "
                  "a cache built on one system is useless on another.",
        hints=[
            "Normalise first, hash second. Hashing the raw text makes Windows and Linux checkouts disagree.",
            "`hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]` gives the 12 characters.",
            "For the partial hit, the prefix must include the trailing dash, and you want the *last* matching saved key.",
        ],
        brute_force="There is no meaningfully slower correct approach; the work is one hash and one pass over `saved`.",
        approach="1. `text = lockfile.replace('\\r\\n', '\\n')`.\n"
                 "2. `digest` = first 12 hex characters of SHA-256 of `text` as UTF-8.\n"
                 "3. `prefix = 'deps-' + os_name + '-'`, `key = prefix + digest`.\n"
                 "4. Exact hit if `key in saved`. Otherwise collect saved keys starting with `prefix`; if any, partial hit with the last one. Otherwise miss.\n\n"
                 "**Dry run** on Example 2: `'a==1\\r\\n'` normalises to `'a==1\\n'`, whose digest starts `a6ad7b420d04`. "
                 "The key is in `saved`, so the answer is an exact hit.",
        complexity="Time O(L + S) for a lockfile of length L and S saved keys. Space O(L).",
        pitfalls="- Skipping the normalisation makes the same dependencies produce two keys.\n"
                 "- A prefix without the trailing dash makes `deps-Lin` match `deps-Linux-...`.\n"
                 "- Taking the first matching key restores the oldest cache instead of the newest.\n"
                 "- `.encode()` is required: `sha256` works on bytes, not on text.",
        follow_up="Real keys often include the language version too. Why would a cache built for Python 3.11 be wrong for 3.13?",
    ),
),
]
