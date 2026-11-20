_chain = ["t%04d" % i for i in range(2000)]
_chain_deps = [[_chain[i], _chain[i + 1]] for i in range(1999)]
_wide = ["w%03d" % i for i in range(300)]
_wide_deps = [["w000", w] for w in _wide[1:150]] + [[w, "w299"] for w in _wide[150:299]]

PROBLEMS = [
dict(
    id="mlops-dag-order",
    title="Pipeline DAG Execution Order",
    difficulty="Medium",
    pattern="Orchestration",
    entry="taskOrder",
    description=r"""
Orchestrators such as Airflow, Prefect, Dagster and Kubeflow Pipelines model a training pipeline as a
**directed acyclic graph** of tasks. On a single worker, the scheduler must pick an execution order that
respects every dependency.

`taskOrder(tasks, deps)`:

- `tasks`: list of unique task names.
- `deps`: list of `[upstream, downstream]` pairs meaning *upstream must finish before downstream starts*.
  Every name in `deps` appears in `tasks`. Duplicate pairs may appear.
- Whenever several tasks are ready, run the **lexicographically smallest** one first (deterministic tie-break,
  so two runs of the scheduler always produce the same order).
- If the graph contains a **cycle**, return `[]` (Airflow refuses to load such a DAG).

**Example:** `tasks = ["train", "extract", "validate", "evaluate"]`,
`deps = [["extract","validate"], ["validate","train"], ["train","evaluate"]]`
→ `["extract", "validate", "train", "evaluate"]`
""",
    starter='''def taskOrder(tasks, deps):
    pass
''',
    solution='''import heapq

def taskOrder(tasks, deps):
    indeg = {t: 0 for t in tasks}
    adj = {t: set() for t in tasks}
    for u, v in deps:
        if v not in adj[u]:
            adj[u].add(v)
            indeg[v] += 1
    heap = [t for t in tasks if indeg[t] == 0]
    heapq.heapify(heap)
    order = []
    while heap:
        t = heapq.heappop(heap)
        order.append(t)
        for v in adj[t]:
            indeg[v] -= 1
            if indeg[v] == 0:
                heapq.heappush(heap, v)
    return order if len(order) == len(tasks) else []
''',
    tests=[
        [["train", "extract", "validate", "evaluate"], [["extract", "validate"], ["validate", "train"], ["train", "evaluate"]]],
        [["c", "b", "a"], []],
        [[], []],
        [["a", "b"], [["a", "b"], ["b", "a"]]],
        [["a"], [["a", "a"]]],
        [["load", "feat_a", "feat_b", "join", "train"], [["load", "feat_b"], ["load", "feat_a"], ["feat_a", "join"], ["feat_b", "join"], ["join", "train"]]],
        [["a", "b", "c", "d"], [["a", "d"], ["a", "d"], ["b", "d"], ["c", "d"]]],
        [["z", "y", "x", "w"], [["z", "w"]]],
        [["a", "b", "c", "d", "e"], [["a", "b"], ["b", "c"], ["c", "d"], ["d", "b"], ["a", "e"]]],
        [["deploy", "test", "build", "lint"], [["lint", "build"], ["test", "build"], ["build", "deploy"]]],
        [list(reversed(_chain)), _chain_deps],
        [_wide, _wide_deps],
    ],
    examples=2,
    wrong_solutions=[
        '''def taskOrder(tasks, deps):
    from collections import deque
    indeg = {t: 0 for t in tasks}
    adj = {t: [] for t in tasks}
    for u, v in deps:
        adj[u].append(v); indeg[v] += 1
    q = deque(t for t in tasks if indeg[t] == 0)
    order = []
    while q:
        t = q.popleft(); order.append(t)
        for v in adj[t]:
            indeg[v] -= 1
            if indeg[v] == 0: q.append(v)
    return order if len(order) == len(tasks) else []
''',
        '''import heapq
def taskOrder(tasks, deps):
    indeg = {t: 0 for t in tasks}
    adj = {t: [] for t in tasks}
    for u, v in deps:
        adj[u].append(v); indeg[v] += 1
    heap = [t for t in tasks if indeg[t] == 0]; heapq.heapify(heap)
    order = []
    while heap:
        t = heapq.heappop(heap); order.append(t)
        for v in adj[t]:
            indeg[v] -= 1
            if indeg[v] == 0: heapq.heappush(heap, v)
    return order
''',
    ],
    guide=dict(
        prereqs="Lesson *Pipelines and orchestration*; topological sort (Kahn's algorithm); heaps.",
        intuition="Kahn's algorithm repeatedly runs a task whose upstreams are all done. Replace its FIFO queue with a min-heap and the 'which ready task first?' choice becomes deterministic.",
        hints=["Count in-degrees (number of unfinished upstreams) per task.", "Deduplicate repeated edges (or count and decrement per edge consistently) so in-degrees stay correct.",
               "If fewer tasks were emitted than exist, some tasks sit on a cycle → return []."],
        brute_force="Repeatedly scan all tasks for one whose upstreams are all done and pick the smallest: O(V²·E). Works but is slow for 2,000-task chains.",
        approach="1. Build adjacency sets and in-degrees.\n2. Heapify all zero in-degree tasks.\n3. Pop smallest, append, decrement children, push newly ready ones.\n4. Cycle check by length.\n\n"
                 "Dry run (example): ready={extract} → extract; ready={validate} → validate → train → evaluate.",
        complexity="O((V + E) log V) time, O(V + E) space.",
        pitfalls="- Using a plain queue: valid topological order but not the required tie-break.\n- Forgetting cycle detection (self-loops count!).\n- Recursion-based DFS hitting Python's recursion limit on long chains.",
        follow_up="Return *waves* (sets of tasks that can run in parallel given unlimited workers) — this is what `max_active_tasks` in Airflow throttles.",
    ),
),
dict(
    id="mlops-docker-layer-cache",
    title="Docker Layer Cache Invalidation",
    difficulty="Medium",
    pattern="Containers",
    entry="rebuiltLayers",
    description=r"""
Docker builds an image one instruction at a time and caches each resulting layer. A cached layer can be
reused only if **its instruction is unchanged, its inputs are unchanged, and every earlier layer was reused**.
Once one layer misses the cache, every later instruction is rebuilt.

`rebuiltLayers(prev_instructions, instructions, changed_files, dockerignore)` returns the list of indices
(0-based, into `instructions`) that will be **rebuilt**.

Rules for instruction `i`:

1. If `i >= len(prev_instructions)` or `instructions[i] != prev_instructions[i]` → miss.
2. If it is a `COPY` or `ADD` instruction, it misses when any **relevant** changed file matches one of its sources:
   - Tokens after the keyword that start with `--` are flags (e.g. `--chown=app`) and are ignored.
     The **last** remaining token is the destination; all others are sources.
   - A changed file is *relevant* unless it matches a `.dockerignore` pattern
     (`fnmatch(file, pattern)` or `file` is inside directory `pattern`).
   - File `f` matches source `s` (after stripping a leading `./` and trailing `/`) if `s` is `.` or empty,
     `f == s`, `f` starts with `s + "/"`, or `fnmatch(f, s)`.
3. Every other instruction (`FROM`, `RUN`, `ENV`, `WORKDIR`, `CMD`, ...) only misses through rules 1 or 3.
4. After the first miss, all following instructions are rebuilt.

**Example:**
```
FROM python:3.11-slim | WORKDIR /app | COPY requirements.txt . | RUN pip install -r requirements.txt | COPY . . | CMD [...]
changed_files = ["src/model.py"]  ->  [4, 5]
```
Editing only source code reuses the expensive `pip install` layer — the reason we copy `requirements.txt` first.
""",
    starter='''from fnmatch import fnmatch

def rebuiltLayers(prev_instructions, instructions, changed_files, dockerignore):
    pass
''',
    solution='''from fnmatch import fnmatch

def _ignored(f, pats):
    for p in pats:
        p2 = p.rstrip("/")
        if fnmatch(f, p) or f.startswith(p2 + "/"):
            return True
    return False

def _matches(f, s):
    if s.startswith("./"):
        s = s[2:]
    s = s.rstrip("/")
    return s in (".", "") or f == s or f.startswith(s + "/") or fnmatch(f, s)

def rebuiltLayers(prev_instructions, instructions, changed_files, dockerignore):
    relevant = [f for f in changed_files if not _ignored(f, dockerignore)]
    n = len(instructions)
    for i, ins in enumerate(instructions):
        if i >= len(prev_instructions) or ins != prev_instructions[i]:
            return list(range(i, n))
        parts = ins.split()
        if parts and parts[0].upper() in ("COPY", "ADD"):
            toks = [t for t in parts[1:] if not t.startswith("--")]
            srcs = toks[:-1]
            if any(_matches(f, s) for f in relevant for s in srcs):
                return list(range(i, n))
    return []
''',
    tests=[
        [["FROM python:3.11-slim", "WORKDIR /app", "COPY requirements.txt .", "RUN pip install -r requirements.txt", "COPY . .", 'CMD ["python", "serve.py"]'],
         ["FROM python:3.11-slim", "WORKDIR /app", "COPY requirements.txt .", "RUN pip install -r requirements.txt", "COPY . .", 'CMD ["python", "serve.py"]'],
         ["src/model.py"], []],
        [["FROM python:3.11-slim", "WORKDIR /app", "COPY requirements.txt .", "RUN pip install -r requirements.txt", "COPY . ."],
         ["FROM python:3.11-slim", "WORKDIR /app", "COPY requirements.txt .", "RUN pip install -r requirements.txt", "COPY . ."],
         ["requirements.txt"], []],
        [["FROM python:3.11-slim", "COPY . .", "RUN pip install ."], ["FROM python:3.11-slim", "COPY . .", "RUN pip install ."], ["README.md"], []],
        [["FROM python:3.11-slim", "COPY . .", "RUN pip install ."], ["FROM python:3.11-slim", "COPY . .", "RUN pip install ."], ["README.md"], ["*.md"]],
        [["FROM python:3.11-slim", "COPY . ."], ["FROM python:3.11-slim", "COPY . ."], ["notebooks/eda.ipynb", "data/raw.csv"], ["notebooks/", "data"]],
        [["FROM python:3.11-slim", "RUN apt-get update", "COPY app/ /app/"], ["FROM python:3.12-slim", "RUN apt-get update", "COPY app/ /app/"], [], []],
        [["FROM a", "RUN x"], ["FROM a", "RUN x", "RUN y"], [], []],
        [["FROM a", "RUN x"], ["FROM a", "RUN x"], ["anything.py"], []],
        [["FROM a", "COPY --chown=app:app src/ /app/src/", "COPY configs/*.yaml /app/configs/"],
         ["FROM a", "COPY --chown=app:app src/ /app/src/", "COPY configs/*.yaml /app/configs/"], ["configs/prod.yaml"], []],
        [["FROM a", "COPY --chown=app:app src/ /app/src/", "COPY configs/*.yaml /app/configs/"],
         ["FROM a", "COPY --chown=app:app src/ /app/src/", "COPY configs/*.yaml /app/configs/"], ["srcx/notes.txt", "configs/readme.txt"], []],
        [["FROM a", "COPY pyproject.toml poetry.lock ./", "RUN poetry install", "COPY ./src ./src"],
         ["FROM a", "COPY pyproject.toml poetry.lock ./", "RUN poetry install", "COPY ./src ./src"], ["poetry.lock", "src/x.py"], []],
        [["FROM a", "COPY model.pkl /m/", "ENV MODEL=/m/model.pkl"], ["FROM a", "COPY model.pkl /m/", "ENV MODEL=/m/model.pkl"], ["model.pkl.bak"], []],
        [[], ["FROM a", "RUN b"], [], []],
    ],
    examples=2,
    wrong_solutions=[
        '''def rebuiltLayers(prev_instructions, instructions, changed_files, dockerignore):
    out = []
    for i, ins in enumerate(instructions):
        if i >= len(prev_instructions) or ins != prev_instructions[i]:
            out.append(i); continue
        parts = ins.split()
        if parts[0] in ("COPY", "ADD") and any(f in ins or parts[1] == "." for f in changed_files):
            out.append(i)
    return out
''',
        '''from fnmatch import fnmatch
def rebuiltLayers(prev_instructions, instructions, changed_files, dockerignore):
    n = len(instructions)
    for i, ins in enumerate(instructions):
        if i >= len(prev_instructions) or ins != prev_instructions[i]:
            return list(range(i, n))
        parts = ins.split()
        if parts[0] in ("COPY", "ADD"):
            srcs = parts[1:-1]
            for f in changed_files:
                for s in srcs:
                    s = s.rstrip("/")
                    if s in (".", "./") or f == s or f.startswith(s) or fnmatch(f, s):
                        return list(range(i, n))
    return []
''',
    ],
    guide=dict(
        prereqs="Lesson *Docker fundamentals: images, layers and the build cache*.",
        intuition="The build cache is a chain: layer *i* is identified by (parent layer, instruction text, checksums of copied files). Find the first link that breaks; everything after it is rebuilt.",
        hints=["First filter `changed_files` through `.dockerignore` — ignored files never enter the build context, so they can't bust the cache.",
               "Parse COPY: drop `--flag` tokens, last token is the destination.",
               "`src/` must match `src/x.py` but **not** `srcx/notes.txt` — compare with `s + '/'`, not a bare `startswith(s)`."],
        brute_force="Marking only the changed COPY layer as rebuilt — wrong, because every later layer's parent changed.",
        approach="1. Relevant files = changed minus ignored.\n2. Walk instructions; on text mismatch or new instruction → return `range(i, n)`.\n3. For COPY/ADD, test every (file, source) pair; on match → return `range(i, n)`.\n4. If no miss, return `[]`.",
        complexity="O(n · F · S) for n instructions, F changed files, S sources per COPY.",
        pitfalls="- Prefix matching without the `/` boundary.\n- Forgetting `--chown`/`--from` flags are not sources.\n- Forgetting that a changed `FROM` (new base tag) invalidates everything.\n"
                 "- Real Docker also busts `RUN` when `ARG` values change and never re-runs `RUN apt-get update` on its own — a classic source of stale packages.",
        follow_up="Model multi-stage builds: a `COPY --from=builder` layer depends on the builder stage's final layer.",
    ),
),
dict(
    id="mlops-backoff-schedule",
    title="Exponential Backoff with Jitter",
    difficulty="Easy",
    pattern="Reliability",
    entry="backoffSchedule",
    description=r"""
Clients of a model API (or a pipeline task calling a feature store) should retry transient failures with
**capped exponential backoff plus jitter**, and give up when a total time budget is exhausted.

`backoffSchedule(base_ms, factor, cap_ms, max_retries, deadline_ms, jitter)` returns the list of sleep
durations (integers, ms) before each retry:

- For retry `i = 0, 1, ..., max_retries-1`: `raw = min(cap_ms, base_ms * factor**i)`.
- **Equal jitter**: `delay = int(raw / 2 + jitter[i] * raw / 2)`, where `jitter[i]` in `[0, 1)` is a
  pre-drawn random number (given so the result is deterministic).
- Stop (do not include the delay) as soon as `total_so_far + delay > deadline_ms`.

**Example:** `backoffSchedule(100, 2, 1000, 5, 10000, [0, 0, 0, 0, 0])` → `[50, 100, 200, 400, 500]`
""",
    starter='''def backoffSchedule(base_ms, factor, cap_ms, max_retries, deadline_ms, jitter):
    pass
''',
    solution='''def backoffSchedule(base_ms, factor, cap_ms, max_retries, deadline_ms, jitter):
    out, total = [], 0
    for i in range(max_retries):
        raw = min(cap_ms, base_ms * factor ** i)
        d = int(raw / 2 + jitter[i] * raw / 2)
        if total + d > deadline_ms:
            break
        out.append(d)
        total += d
    return out
''',
    tests=[
        [100, 2, 1000, 5, 10000, [0, 0, 0, 0, 0]],
        [100, 2, 1000, 5, 10000, [0.5, 0.5, 0.5, 0.5, 0.5]],
        [100, 2, 1000, 0, 10000, []],
        [100, 2, 1000, 5, 0, [0, 0, 0, 0, 0]],
        [100, 2, 1000, 6, 1000, [0.99, 0.1, 0.2, 0.3, 0.4, 0.5]],
        [200, 3, 5000, 8, 60000, [0.25, 0.75, 0.0, 0.9, 0.5, 0.1, 0.3, 0.6]],
        [50, 1.5, 400, 6, 100000, [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]],
        [1000, 2, 1000, 3, 1500, [0, 0, 0]],
        [10, 10, 10 ** 9, 10, 10 ** 12, [0.5] * 10],
        [100, 2, 30000, 40, 10 ** 7, [((i * 37) % 100) / 100 for i in range(40)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def backoffSchedule(base_ms, factor, cap_ms, max_retries, deadline_ms, jitter):
    out, total = [], 0
    for i in range(max_retries):
        d = int(min(cap_ms, base_ms * factor ** i) * jitter[i])
        if total + d > deadline_ms: break
        out.append(d); total += d
    return out
''',
        '''def backoffSchedule(base_ms, factor, cap_ms, max_retries, deadline_ms, jitter):
    out, total = [], 0
    for i in range(max_retries):
        raw = min(cap_ms, base_ms * factor ** i)
        d = int(raw / 2 + jitter[i] * raw / 2)
        out.append(d); total += d
        if total > deadline_ms: break
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *REST and gRPC serving with FastAPI* (reliability section).",
        intuition="Exponential growth backs off quickly from an overloaded server; the cap bounds worst-case waits; jitter de-synchronises thousands of clients so they don't retry in lock-step (the *thundering herd*).",
        hints=["Compute `raw` first, then apply jitter.", "Check the deadline *before* appending.", "Use `int()` (truncation), as specified."],
        brute_force="It is a direct simulation — the challenge is getting the order of cap, jitter and deadline right.",
        approach="Loop i over retries, compute capped raw delay, apply equal jitter, check budget, append.",
        complexity="O(max_retries).",
        pitfalls="- Full jitter (`raw * r`) vs equal jitter (`raw/2 + raw/2 * r`) — the spec asks for equal jitter.\n- Appending a delay that overshoots the deadline.\n- Retrying non-idempotent calls (e.g. a POST that charges money) without an idempotency key.",
        follow_up="Libraries: `tenacity` (Python), `urllib3.Retry`, and gRPC retry policies. Also respect `Retry-After` headers on HTTP 429/503.",
    ),
),
dict(
    id="mlops-hpa-replicas",
    title="Kubernetes HPA Replica Simulation",
    difficulty="Medium",
    pattern="Kubernetes",
    entry="hpaSimulate",
    description=r"""
The Kubernetes **Horizontal Pod Autoscaler** computes
$$\text{desired} = \left\lceil \text{current} \times \frac{\text{currentMetric}}{\text{targetMetric}} \right\rceil$$
skips scaling when the ratio is within a 10% tolerance, clamps to `[minReplicas, maxReplicas]`, and uses a
**scale-down stabilization window** so it doesn't flap.

`hpaSimulate(initial, metrics, target, min_r, max_r, window)` simulates successive sync periods:

- `metrics[t]` is the average per-pod utilisation (integer, e.g. CPU %) observed at step `t`.
- **Recommendation** at step `t` (with `cur` = replicas before the step):
  - if `abs(metrics[t] - target) * 10 <= target` (within 10%, integer arithmetic): `rec = cur`
  - else `rec = ceil(cur * metrics[t] / target)` (use integer ceil), then clamp to `[min_r, max_r]`.
- **Stabilization**: keep the recommendations of the last `window` steps (including step `t`).
  - if `rec > cur`: scale up immediately, `new = rec`.
  - else: `new = min(cur, max(last window recommendations))`.
- Return the replica count after each step.

**Example:** `hpaSimulate(2, [100, 20, 20, 20], 50, 1, 10, 2)` → `[4, 4, 2, 2]`

- step 0: rec = ceil(2·100/50) = 4 > 2 → scale up to 4.
- step 1: rec = ceil(4·20/50) = 2, window = [4, 2] → min(4, max) = 4 (held by the window).
- step 2: rec = 2, window = [2, 2] → scale down to 2.
- step 3: rec = ceil(2·20/50) = 1, window = [2, 1] → stays 2.
""",
    starter='''def hpaSimulate(initial, metrics, target, min_r, max_r, window):
    pass
''',
    solution='''from collections import deque

def hpaSimulate(initial, metrics, target, min_r, max_r, window):
    cur = initial
    recent = deque(maxlen=window)
    out = []
    for m in metrics:
        if abs(m - target) * 10 <= target:
            rec = cur
        else:
            rec = -(-cur * m // target)
            rec = max(min_r, min(max_r, rec))
        recent.append(rec)
        if rec > cur:
            cur = rec
        else:
            cur = min(cur, max(recent))
        out.append(cur)
    return out
''',
    tests=[
        [2, [100, 20, 20, 20], 50, 1, 10, 2],
        [3, [60, 60, 60], 60, 1, 10, 3],
        [3, [66, 54, 65], 60, 1, 10, 3],
        [4, [], 50, 1, 10, 3],
        [10, [10, 10, 10, 10, 10], 50, 1, 20, 1],
        [10, [10, 10, 10, 10, 10], 50, 1, 20, 3],
        [10, [10, 10, 10, 10, 10], 50, 3, 20, 3],
        [2, [500], 50, 1, 8, 5],
        [5, [90, 20, 95, 20, 20, 20, 20], 50, 1, 50, 3],
        [1, [51, 56, 70, 140, 30, 30, 30, 30], 50, 1, 100, 2],
        [6, [((i * 53) % 120) + 5 for i in range(300)], 60, 2, 40, 5],
    ],
    examples=2,
    wrong_solutions=[
        '''import math
def hpaSimulate(initial, metrics, target, min_r, max_r, window):
    cur = initial; out = []
    for m in metrics:
        if abs(m / target - 1) > 0.1:
            cur = max(min_r, min(max_r, math.ceil(cur * m / target)))
        out.append(cur)
    return out
''',
        '''def hpaSimulate(initial, metrics, target, min_r, max_r, window):
    cur = initial; out = []
    for m in metrics:
        if abs(m - target) * 10 > target:
            cur = max(min_r, min(max_r, cur * m // target))
        out.append(cur)
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Scaling, GPUs and KServe on Kubernetes*.",
        intuition="The HPA is a proportional controller: if pods run at 2× target utilisation, you need about 2× the pods. Tolerance and the downscale window add hysteresis so noise doesn't cause flapping.",
        hints=["Integer ceil: `-(-a // b)`.", "Clamp the recommendation *before* storing it in the window.",
               "Scale-up is immediate; scale-down picks the **highest** recommendation in the window, never above the current count."],
        brute_force="Without the window the controller flaps between sizes whenever load is spiky — try deleting it and run the long test.",
        approach="Maintain `cur` and a `deque(maxlen=window)` of recommendations. Each step: compute rec (tolerance → keep), clamp, push, then apply the up/down rule.\n\n"
                 "See the worked example in the statement: the spike at step 0 scales up instantly, while the drop at step 1 is held for one extra period by the window.",
        complexity="O(T · window).",
        pitfalls="- Float tolerance check `abs(m/target - 1) <= 0.1` misbehaves at exactly 10% due to rounding (`110/100-1 = 0.10000000000000009`).\n"
                 "- Using floor instead of ceil underprovisions.\n- Applying the window to scale-ups (the default `scaleUp.stabilizationWindowSeconds` is 0).",
        follow_up="Real HPA defaults: 15 s sync period, 300 s downscale stabilization, tolerance 0.1, plus `behavior.scaleDown.policies` that limit how many pods may be removed per period.",
    ),
),
dict(
    id="mlops-kv-cache-capacity",
    title="LLM Serving Capacity from KV-Cache Memory",
    difficulty="Easy",
    pattern="LLM Inference",
    entry="servingCapacity",
    description=r"""
For LLM serving, GPU memory holds the **weights** plus the **KV cache**, which grows with every
concurrent sequence. Following Huyen's formula (*AI Engineering*, ch. 9), the KV cache for one
sequence is

$$2 \times S \times L \times H_{kv} \times M \quad\text{bytes}$$

where `S` = sequence length, `L` = layers, `M` = bytes per cached value, and
$H_{kv} = H \cdot \frac{n_{kv}}{n_{heads}}$ is the effective KV width (grouped-query attention shares K/V
across query heads; with multi-head attention `n_kv == n_heads`).

`servingCapacity(gpu_gb, util_pct, params, weight_bytes, layers, hidden, n_heads, n_kv_heads, kv_bytes, seq_len)`:

- usable bytes = `gpu_gb * 10**9 * util_pct // 100 - params * weight_bytes`
- `kv_per_seq = 2 * seq_len * layers * (hidden * n_kv_heads // n_heads) * kv_bytes`
- `max_seqs = usable // kv_per_seq`, or `0` if usable bytes ≤ 0.

Return `[kv_per_seq, max_seqs]` (integers).

**Example (Llama-2-13B-like, FP16, MHA):** `servingCapacity(80, 90, 13_000_000_000, 2, 40, 5120, 40, 40, 2, 2048)`
→ `[1677721600, 27]` — about 1.68 GB of KV cache per 2K-token sequence.
""",
    starter='''def servingCapacity(gpu_gb, util_pct, params, weight_bytes, layers, hidden, n_heads, n_kv_heads, kv_bytes, seq_len):
    pass
''',
    solution='''def servingCapacity(gpu_gb, util_pct, params, weight_bytes, layers, hidden, n_heads, n_kv_heads, kv_bytes, seq_len):
    usable = gpu_gb * 10 ** 9 * util_pct // 100 - params * weight_bytes
    kv = 2 * seq_len * layers * (hidden * n_kv_heads // n_heads) * kv_bytes
    return [kv, usable // kv if usable > 0 else 0]
''',
    tests=[
        [80, 90, 13_000_000_000, 2, 40, 5120, 40, 40, 2, 2048],
        [80, 90, 13_000_000_000, 1, 40, 5120, 40, 40, 2, 2048],
        [24, 90, 7_000_000_000, 2, 32, 4096, 32, 32, 2, 4096],
        [24, 90, 7_000_000_000, 2, 32, 4096, 32, 8, 2, 4096],
        [24, 90, 13_000_000_000, 2, 40, 5120, 40, 40, 2, 2048],
        [80, 95, 70_000_000_000, 1, 80, 8192, 64, 8, 1, 8192],
        [16, 100, 0, 2, 2, 64, 4, 4, 2, 16],
        [80, 90, 8_000_000_000, 2, 32, 4096, 32, 8, 2, 131072],
        [40, 50, 20_000_000_000, 1, 48, 6144, 48, 48, 2, 1024],
        [141, 90, 70_000_000_000, 2, 80, 8192, 64, 8, 2, 4096],
    ],
    examples=2,
    wrong_solutions=[
        '''def servingCapacity(gpu_gb, util_pct, params, weight_bytes, layers, hidden, n_heads, n_kv_heads, kv_bytes, seq_len):
    usable = gpu_gb * 10 ** 9 * util_pct // 100 - params * weight_bytes
    kv = seq_len * layers * hidden * kv_bytes
    return [kv, max(0, usable // kv)]
''',
    ],
    guide=dict(
        prereqs="Lesson *LLM inference optimization*.",
        intuition="Weights are a fixed cost; the KV cache is a per-sequence cost. Whatever memory is left after the weights, divided by the per-sequence cost, is your concurrency ceiling — which directly bounds batch size and throughput.",
        hints=["The leading 2 is for **K and V**.", "GQA divides the KV width by `n_heads / n_kv_heads`.", "Do everything in integers to avoid float rounding."],
        brute_force="N/A — closed-form arithmetic.",
        approach="Example: usable = 72e9 − 26e9 = 46e9 bytes; kv = 2·2048·40·5120·2 = 1,677,721,600; 46e9 // 1.68e9 = 27.",
        complexity="O(1).",
        pitfalls="- Forgetting the factor 2.\n- Ignoring GQA (Llama-2-70B, Llama-3 use 8 KV heads: an 8× saving vs MHA with 64 heads).\n- Using GiB (2^30) and GB (10^9) inconsistently.",
        follow_up="PagedAttention (vLLM) allocates the KV cache in blocks so actual sequences use only what they need; KV-cache quantization (FP8) halves `kv_bytes`.",
    ),
),
]
