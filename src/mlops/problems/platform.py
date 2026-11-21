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
dict(
    id="mlops-successive-halving",
    title="Successive Halving for Hyperparameter Search",
    difficulty="Medium",
    pattern="Hyperparameter Tuning",
    entry="successiveHalving",
    description=r"""
Training every candidate **configuration** (one choice of hyperparameters such as learning rate and tree
depth) to the end is expensive. **Successive halving** trains all of them a little, keeps the best
fraction, trains the survivors longer, and repeats. Bad configurations are dropped early, so most of the
compute goes to promising ones.

You get the learning curves in advance (so the result is deterministic): `curves[name][e - 1]` is the
validation score of configuration `name` after `e` epochs. Higher is better.

`successiveHalving(curves, eta, min_budget, max_budget)` runs these **rungs** (rounds):

1. Start with all configurations alive and `budget = min_budget` epochs.
2. Rank the alive configurations by their score at `budget` (`curves[name][budget - 1]`), best first;
   break ties by name, alphabetically. Record the rung as `[budget, ranked_names]`.
3. If only one configuration is alive, or `budget * eta > max_budget`, stop: the winner is the first name
   of this rung.
4. Otherwise keep the top `max(1, len(alive) // eta)` names, multiply `budget` by `eta`, and go to step 2.

Trials **resume from checkpoints**: moving a configuration from a budget of `b_old` epochs to `b_new`
costs `b_new - b_old` extra epochs (the first rung costs `min_budget` per configuration).

Return `{"winner": name, "rungs": [[budget, ranked_names], ...], "epochs_used": total_epochs}`.

**Example:** `curves = {"a": [0.5, 0.6, 0.7], "b": [0.6, 0.62, 0.64], "c": [0.4, 0.5, 0.9]}`, `eta = 3`,
`min_budget = 1`, `max_budget = 3` -> rung 1 ranks `b, a, c`; keep `3 // 3 = 1` -> `b`; rung 3 has only
`b`. Result: `{"winner": "b", "rungs": [[1, ["b", "a", "c"]], [3, ["b"]]], "epochs_used": 5}`
(3 configurations x 1 epoch, then 2 more epochs for `b`). Note that `c` would have won with full
training: early stopping is a bet, not a guarantee.
""",
    starter='''def successiveHalving(curves, eta, min_budget, max_budget):
    alive = sorted(curves)
    budget = min_budget
    # loop over rungs: rank, record, stop or keep the top len(alive) // eta
    pass
''',
    solution='''def successiveHalving(curves, eta, min_budget, max_budget):
    alive = sorted(curves)
    budget, previous, used, rungs = min_budget, 0, 0, []
    while True:
        ranked = sorted(alive, key=lambda c: (-curves[c][budget - 1], c))
        used += (budget - previous) * len(ranked)
        rungs.append([budget, ranked])
        if len(ranked) == 1 or budget * eta > max_budget:
            return {"winner": ranked[0], "rungs": rungs, "epochs_used": used}
        alive = ranked[:max(1, len(ranked) // eta)]
        previous, budget = budget, budget * eta
''',
    tests=[
        [{"a": [0.5, 0.6, 0.7], "b": [0.6, 0.62, 0.64], "c": [0.4, 0.5, 0.9]}, 3, 1, 3],
        [{"only": [0.1, 0.2, 0.3, 0.4]}, 2, 1, 4],
        [{"x": [0.5] * 9, "y": [0.5] * 9}, 3, 1, 9],
        [{"a": [0.1, 0.2, 0.3, 0.4], "b": [0.2, 0.1, 0.5, 0.3], "c": [0.3, 0.3, 0.1, 0.6], "d": [0.0, 0.4, 0.2, 0.9]}, 2, 1, 4],
        [{"a": [0.1, 0.2], "b": [0.3, 0.1]}, 2, 2, 2],
        [{"a": [0.9, 0.1, 0.1], "b": [0.1, 0.2, 0.8]}, 3, 1, 2],
        [{"c%02d" % i: [((i * 7 + e * 3) % 11) / 10 for e in range(1, 28)] for i in range(27)}, 3, 1, 27],
        [{"c%02d" % i: [((i * 5 + e) % 13) / 13 for e in range(1, 33)] for i in range(10)}, 2, 2, 32],
        [{"cfg%03d" % i: [((i * 37 + e * 11) % 101) / 100 for e in range(1, 82)] for i in range(243)}, 3, 1, 81],
    ],
    examples=2,
    wrong_solutions=[
        '''def successiveHalving(curves, eta, min_budget, max_budget):
    alive = sorted(curves)
    budget, used, rungs = min_budget, 0, []
    while True:
        ranked = sorted(alive, key=lambda c: (-curves[c][budget - 1], c))
        used += budget * len(ranked)
        rungs.append([budget, ranked])
        if len(ranked) == 1 or budget * eta > max_budget:
            return {"winner": ranked[0], "rungs": rungs, "epochs_used": used}
        alive = ranked[:max(1, len(ranked) // eta)]
        budget *= eta
''',
        '''def successiveHalving(curves, eta, min_budget, max_budget):
    alive = sorted(curves)
    budget, previous, used, rungs = min_budget, 0, 0, []
    while True:
        ranked = sorted(alive, key=lambda c: (-curves[c][budget - 1], c))
        used += (budget - previous) * len(ranked)
        rungs.append([budget, ranked])
        if len(ranked) == 1 or budget * eta > max_budget:
            return {"winner": ranked[0], "rungs": rungs, "epochs_used": used}
        alive = ranked[:-(-len(ranked) // eta)]
        previous, budget = budget, budget * eta
''',
    ],
    guide=dict(
        prereqs="Lesson *Hyperparameter tuning at scale* (early stopping, successive halving, Hyperband, ASHA).",
        intuition="Most bad configurations look bad early. Spend a tiny budget on everyone, then repeatedly hand the survivors `eta` times more budget. With `eta = 3` and 27 configurations, rungs hold 27, 9, 3 and 1 configurations.",
        hints=["Sort with the key `(-score, name)` to get best-first with alphabetical tie-breaks.",
               "Check the stop condition *after* recording the rung.",
               "Keep track of the previous budget so promoted trials pay only the extra epochs."],
        brute_force="Train every configuration for `max_budget` epochs and take the best: `n x max_budget` epochs. In the 243-configuration test that is 19,683 epochs; successive halving uses a small fraction.",
        approach="Loop: rank alive by score at the current budget, add `(budget - previous) x len(alive)` epochs, record, stop if one left or the next budget would exceed the maximum, else keep `max(1, len // eta)` and multiply the budget.\n\nDry run of the example: rung 1 costs 3 epochs and ranks b (0.6), a (0.5), c (0.4); keep b; rung 3 costs 3 - 1 = 2 epochs; total 5.",
        complexity="O(R x n log n) for R rungs over n configurations (R is about log base eta of max/min budget).",
        pitfalls="- Forgetting checkpoint resumption and charging the full budget at every rung.\n- Ties: sorting on scores alone leaves equal scores in an order that depends on how the input was built; an explicit name tie-break makes the run reproducible.\n- Rounding the number of survivors up instead of down keeps too many configurations and wastes budget.\n- Keeping zero configurations when `len // eta` is 0: always keep at least one.",
        follow_up="Hyperband runs several successive-halving brackets with different starting budgets; ASHA promotes trials asynchronously as soon as they rank in the top 1/eta of their rung. Optuna's `SuccessiveHalvingPruner` and Ray Tune's `ASHAScheduler` implement them.",
    ),
),
dict(
    id="mlops-registry-storage",
    title="Shared Image Layers: Storage and Pull Cost",
    difficulty="Easy",
    pattern="Containers",
    entry="registryStorage",
    description=r"""
A Docker **image** is a stack of read-only **layers**. Each layer is identified by a **digest** (a hash
of its content), so two images built on the same base share those layers: a registry stores a shared
layer once, and a machine that already has a layer does not download it again.

`images` maps an image tag to its list of layers, base first, each layer given as `[digest, size_mb]`
(integers). A digest never appears twice inside one image, and a digest always has the same size.
`pulls` is a list of tags that one fresh machine pulls, in order, starting with nothing cached.

Write `registryStorage(images, pulls)` returning a dictionary with:

- `"per_image"`: tag -> total size of that image (sum of its layers).
- `"unique_total"`: storage the registry really needs: the sum of sizes over **distinct** digests.
- `"shared"`: the alphabetically sorted list of digests used by two or more different images.
- `"pull_mb"`: for each entry of `pulls`, the megabytes downloaded for that pull (only layers not
  already on the machine). Pulling the same tag twice downloads 0 the second time.

**Example:** `images = {"api:1": [["base", 120], ["deps", 300], ["code1", 5]], "api:2": [["base", 120], ["deps", 300], ["code2", 6]]}`,
`pulls = ["api:1", "api:2"]` ->
`{"per_image": {"api:1": 425, "api:2": 426}, "unique_total": 431, "shared": ["base", "deps"], "pull_mb": [425, 6]}`
""",
    starter='''def registryStorage(images, pulls):
    # remember each digest's size and which images use it; simulate a cache for pulls
    pass
''',
    solution='''def registryStorage(images, pulls):
    per_image = {tag: sum(size for _, size in layers) for tag, layers in images.items()}
    size_of, users = {}, {}
    for tag, layers in images.items():
        for digest, size in layers:
            size_of[digest] = size
            users.setdefault(digest, set()).add(tag)
    cache, pull_mb = set(), []
    for tag in pulls:
        downloaded = 0
        for digest, size in images[tag]:
            if digest not in cache:
                cache.add(digest)
                downloaded += size
        pull_mb.append(downloaded)
    return {
        "per_image": per_image,
        "unique_total": sum(size_of.values()),
        "shared": sorted(d for d, u in users.items() if len(u) > 1),
        "pull_mb": pull_mb,
    }
''',
    tests=[
        [{"api:1": [["base", 120], ["deps", 300], ["code1", 5]], "api:2": [["base", 120], ["deps", 300], ["code2", 6]]}, ["api:1", "api:2"]],
        [{}, []],
        [{"solo": [["l1", 10]]}, ["solo", "solo"]],
        [{"a": [["x", 1], ["y", 2]], "b": [["z", 3]]}, []],
        [{"train": [["cuda", 3000], ["torch", 2500], ["t", 1]], "serve": [["slim", 50], ["sk", 80], ["s", 1]],
          "train-gpu2": [["cuda", 3000], ["torch", 2500], ["t2", 2]]}, ["serve", "train", "train-gpu2", "serve"]],
        [{"a": [["base", 100], ["mid", 10]], "b": [["mid", 10], ["top", 1]]}, ["b", "a"]],
        [{"a": [["empty", 0], ["x", 5]], "b": [["empty", 0]]}, ["b", "a", "b"]],
        [{"base:only": [["os", 70]], "app": [["os", 70], ["app", 2]]}, ["app", "base:only"]],
        [{"img%d" % i: [["os", 80], ["py", 40], ["deps%d" % (i % 4), 200 + i % 4], ["app%d" % i, 3]] for i in range(60)},
         ["img%d" % (i * 7 % 60) for i in range(80)]],
    ],
    examples=1,
    wrong_solutions=[
        '''def registryStorage(images, pulls):
    per_image = {t: sum(s for _, s in L) for t, L in images.items()}
    users = {}
    for t, L in images.items():
        for d, s in L:
            users.setdefault(d, set()).add(t)
    return {"per_image": per_image, "unique_total": sum(per_image.values()),
            "shared": sorted(d for d, u in users.items() if len(u) > 1),
            "pull_mb": [per_image[t] for t in pulls]}
''',
    ],
    guide=dict(
        prereqs="Lesson *Docker fundamentals: images, layers and the build cache*. Python sets and dictionaries.",
        intuition="Content addressing means identical bytes get identical names. Storage and downloads are therefore counted per distinct digest, not per image.",
        hints=["A dictionary `digest -> size` deduplicates automatically.",
               "A dictionary `digest -> set of tags` tells you which layers are shared.",
               "For pulls, keep a `cache` set and add only sizes of digests not yet in it."],
        brute_force="Summing image sizes counts the 3 GB CUDA layer once per image. That over-estimates registry storage and node download time.",
        approach="1. Per-image sums.\n2. One pass over all layers to fill `size_of` and `users`.\n3. Simulate pulls with a set.\n4. Assemble the dictionary.",
        complexity="O(total number of layers + total layers of pulled images), plus sorting the shared digests.",
        pitfalls="- Treating a repeated pull as a full download.\n- Counting a digest as shared when only one image uses it.\n- Forgetting that ordering builds so that big, stable layers come first is what makes sharing possible.",
        follow_up="Kubernetes nodes cache images the same way, which is why a new pod of an already-pulled image starts fast while a new node pulling a 10 GB GPU image can take minutes. Pre-pulling DaemonSets and slimmer base images reduce cold starts.",
    ),
),
dict(
    id="mlops-pod-scheduling",
    title="Scheduling Pods onto GPU and CPU Nodes",
    difficulty="Medium",
    pattern="Kubernetes",
    entry="schedulePods",
    description=r"""
The Kubernetes **scheduler** decides which **node** (machine) runs each **pod** (a group of containers).
It first filters the nodes that can fit the pod, then scores the remaining ones and picks the best.

Each node is `{"name", "cpu", "mem", "gpu", "labels"}`: capacity in millicores, GiB and whole GPUs, plus a
dictionary of string labels. Each pod is `{"name", "cpu", "mem", "gpu", "selector"}`: its **requests**
(the resources it reserves) and a `selector` dictionary of labels the node must have (may be empty).

`schedulePods(nodes, pods)` places the pods **in order** and returns, for each pod, the chosen node name or
`"Pending"` when no node fits. Rules:

1. **Filter.** A node is feasible when its *remaining* CPU, memory and GPUs are each at least the pod's
   request, and every `selector` key/value appears in the node's `labels`.
2. **GPU taint.** Nodes with GPU capacity above 0 are reserved: a pod that requests `0` GPUs is never placed
   on them.
3. **Score** each feasible node as it would look *after* placing the pod:
   `score = (free_cpu_after * 100) // cpu_capacity + (free_mem_after * 100) // mem_capacity`
   (integer division). Pick the highest score; break ties by node name, alphabetically. Spreading pods
   onto the emptiest node is Kubernetes' "least allocated" strategy.
4. Subtract the pod's requests from the chosen node's remaining resources.

**Example:** nodes `cpu-a` (4000 m, 16 GiB, 0 GPU) and `cpu-b` (8000 m, 32 GiB, 0 GPU); pods `api-1`
(500 m, 1 GiB) and `api-2` (500 m, 1 GiB). `api-1` scores 87 + 93 = 180 on `cpu-a` and 93 + 96 = 189 on
`cpu-b`, so it goes to `cpu-b`; `api-2` then scores 180 on `cpu-a` and 87 + 93 = 180 on `cpu-b`, a tie
won by `cpu-a`. Result: `["cpu-b", "cpu-a"]`.
""",
    starter='''def schedulePods(nodes, pods):
    free = {n["name"]: {"cpu": n["cpu"], "mem": n["mem"], "gpu": n["gpu"]} for n in nodes}
    # for each pod: filter feasible nodes, score them, pick the best or "Pending"
    pass
''',
    solution='''def schedulePods(nodes, pods):
    free = {n["name"]: {"cpu": n["cpu"], "mem": n["mem"], "gpu": n["gpu"]} for n in nodes}
    result = []
    for pod in pods:
        best, best_key = None, None
        for node in nodes:
            f = free[node["name"]]
            if pod["gpu"] == 0 and node["gpu"] > 0:
                continue
            if f["cpu"] < pod["cpu"] or f["mem"] < pod["mem"] or f["gpu"] < pod["gpu"]:
                continue
            if any(node["labels"].get(k) != v for k, v in pod["selector"].items()):
                continue
            score = ((f["cpu"] - pod["cpu"]) * 100) // node["cpu"] + ((f["mem"] - pod["mem"]) * 100) // node["mem"]
            key = (-score, node["name"])
            if best_key is None or key < best_key:
                best, best_key = node["name"], key
        if best is None:
            result.append("Pending")
        else:
            for r in ("cpu", "mem", "gpu"):
                free[best][r] -= pod[r]
            result.append(best)
    return result
''',
    tests=[
        [[{"name": "cpu-a", "cpu": 4000, "mem": 16, "gpu": 0, "labels": {}}, {"name": "cpu-b", "cpu": 8000, "mem": 32, "gpu": 0, "labels": {}}],
         [{"name": "api-1", "cpu": 500, "mem": 1, "gpu": 0, "selector": {}}, {"name": "api-2", "cpu": 500, "mem": 1, "gpu": 0, "selector": {}}]],
        [[{"name": "n1", "cpu": 1000, "mem": 4, "gpu": 0, "labels": {}}], []],
        [[], [{"name": "p", "cpu": 1, "mem": 1, "gpu": 0, "selector": {}}]],
        [[{"name": "gpu-1", "cpu": 16000, "mem": 64, "gpu": 4, "labels": {"accel": "a100"}}],
         [{"name": "web", "cpu": 100, "mem": 1, "gpu": 0, "selector": {}}, {"name": "train", "cpu": 8000, "mem": 32, "gpu": 2, "selector": {}}]],
        [[{"name": "gpu-t4", "cpu": 8000, "mem": 32, "gpu": 1, "labels": {"accel": "t4"}}, {"name": "gpu-a100", "cpu": 8000, "mem": 32, "gpu": 8, "labels": {"accel": "a100"}}],
         [{"name": "llm", "cpu": 4000, "mem": 16, "gpu": 4, "selector": {"accel": "a100"}}, {"name": "small", "cpu": 1000, "mem": 4, "gpu": 1, "selector": {}},
          {"name": "small2", "cpu": 1000, "mem": 4, "gpu": 1, "selector": {}}, {"name": "big", "cpu": 1000, "mem": 4, "gpu": 4, "selector": {"accel": "t4"}}]],
        [[{"name": "a", "cpu": 2000, "mem": 8, "gpu": 0, "labels": {"zone": "eu"}}, {"name": "b", "cpu": 2000, "mem": 8, "gpu": 0, "labels": {"zone": "us"}}],
         [{"name": "p%d" % i, "cpu": 500, "mem": 2, "gpu": 0, "selector": {"zone": "eu"}} for i in range(6)]],
        [[{"name": "x", "cpu": 1000, "mem": 4, "gpu": 0, "labels": {}}],
         [{"name": "exact", "cpu": 1000, "mem": 4, "gpu": 0, "selector": {}}, {"name": "tiny", "cpu": 1, "mem": 0, "gpu": 0, "selector": {}}]],
        [[{"name": "m", "cpu": 4000, "mem": 2, "gpu": 0, "labels": {}}, {"name": "c", "cpu": 1000, "mem": 64, "gpu": 0, "labels": {}}],
         [{"name": "memhog", "cpu": 100, "mem": 3, "gpu": 0, "selector": {}}, {"name": "cpuhog", "cpu": 2000, "mem": 1, "gpu": 0, "selector": {}}]],
        [[{"name": "node-%02d" % i, "cpu": 4000 + 1000 * (i % 3), "mem": 16 + 8 * (i % 2), "gpu": (2 if i % 5 == 0 else 0),
           "labels": {"pool": "gpu" if i % 5 == 0 else "cpu", "zone": "z%d" % (i % 2)}} for i in range(20)],
         [{"name": "pod-%03d" % j, "cpu": 250 * (1 + j % 4), "mem": 1 + j % 3, "gpu": (1 if j % 9 == 0 else 0),
           "selector": ({"zone": "z1"} if j % 4 == 0 else {})} for j in range(150)]],
    ],
    examples=1,
    wrong_solutions=[
        '''def schedulePods(nodes, pods):
    free = {n["name"]: {"cpu": n["cpu"], "mem": n["mem"], "gpu": n["gpu"]} for n in nodes}
    out = []
    for p in pods:
        placed = "Pending"
        for n in sorted(nodes, key=lambda n: n["name"]):
            f = free[n["name"]]
            if p["gpu"] == 0 and n["gpu"] > 0: continue
            if f["cpu"] >= p["cpu"] and f["mem"] >= p["mem"] and f["gpu"] >= p["gpu"] and all(n["labels"].get(k) == v for k, v in p["selector"].items()):
                for r in ("cpu", "mem", "gpu"): f[r] -= p[r]
                placed = n["name"]; break
        out.append(placed)
    return out
''',
        '''def schedulePods(nodes, pods):
    free = {n["name"]: {"cpu": n["cpu"], "mem": n["mem"], "gpu": n["gpu"]} for n in nodes}
    out = []
    for p in pods:
        best, bk = None, None
        for n in nodes:
            f = free[n["name"]]
            if f["cpu"] < p["cpu"] or f["mem"] < p["mem"] or f["gpu"] < p["gpu"]: continue
            if any(n["labels"].get(k) != v for k, v in p["selector"].items()): continue
            s = ((f["cpu"] - p["cpu"]) * 100) // n["cpu"] + ((f["mem"] - p["mem"]) * 100) // n["mem"]
            if bk is None or (-s, n["name"]) < bk: best, bk = n["name"], (-s, n["name"])
        if best is None: out.append("Pending")
        else:
            for r in ("cpu", "mem", "gpu"): free[best][r] -= p[r]
            out.append(best)
    return out
''',
    ],
    guide=dict(
        prereqs="Lessons *Kubernetes core objects* (requests, the first-fit scheduler demo) and *Scaling, GPUs and KServe on Kubernetes* (GPU nodes, taints and tolerations, node selectors).",
        intuition="Scheduling is filter-then-score. The filter removes nodes that cannot run the pod; the score expresses a preference among the rest. Here the preference is \"leave the most room\", which spreads load.",
        hints=["Keep a separate `free` dictionary; never change the input capacities.",
               "Scores use free resources *after* the pod is placed, divided by the node's total capacity.",
               "Compare candidates with the tuple `(-score, name)`: the smallest tuple wins."],
        brute_force="First-fit (take the first node that fits, in name order) is simpler and is what the lesson demo does, but it packs pods onto one node and is not what this problem asks for.",
        approach="For each pod: loop over nodes; skip GPU nodes for CPU-only pods; skip nodes lacking room or labels; compute the score; keep the best key. If none, append Pending; else subtract the requests and append the node name.",
        complexity="O(P x N x S) for P pods, N nodes and S selector entries.",
        pitfalls="- Letting CPU-only pods land on expensive GPU nodes (the taint rule).\n- Scoring on capacity instead of remaining resources.\n- Floating-point scores: the spec uses integer division so ties are exact.",
        follow_up="Real Kubernetes adds affinity and anti-affinity, topology spread constraints, priorities and pre-emption, and a \"most allocated\" bin-packing strategy that cluster autoscalers prefer to free whole nodes.",
    ),
),
dict(
    id="mlops-instance-choice",
    title="Cheapest Fleet for a Serving Load",
    difficulty="Medium",
    pattern="Cost Optimization",
    entry="rankFleets",
    description=r"""
You must serve a model at a **peak** of `peak_rps` requests per second. A load test measured how many
requests per second one **replica** (one copy of the service) can handle on each cloud **instance
type**. Running replicas at 100% of that capacity leaves no headroom for spikes, so you size the fleet
for a **target utilisation** below 100%.

Each instance is `{"name", "cents_per_hour", "rps"}` (all integers). For every instance type:

- `replicas = max(min_replicas, ceil(peak_rps * 100 / (rps * util_pct)))`, computed with **integer**
  arithmetic (no floats): the ceiling of `a / b` for positive integers is `(a + b - 1) // b`.
- `monthly_cents = replicas * cents_per_hour * 730` (a month is counted as 730 hours).

Write `rankFleets(instances, peak_rps, util_pct, min_replicas)` returning a list of
`[name, replicas, monthly_cents]` for every instance type, sorted by `monthly_cents` ascending, then by
fewer replicas, then by name.

`min_replicas` (at least 1) keeps several copies running for availability even when one would be
enough. `util_pct` is an integer from 1 to 100.

**Example:** `instances = [{"name": "small", "cents_per_hour": 10, "rps": 50}, {"name": "large", "cents_per_hour": 38, "rps": 220}]`,
`peak_rps = 300`, `util_pct = 60`, `min_replicas = 2` -> small needs ceil(30000 / 3000) = 10 replicas
(73,000 cents), large needs ceil(30000 / 13200) = 3 replicas (83,220 cents):
`[["small", 10, 73000], ["large", 3, 83220]]`
""",
    starter='''def rankFleets(instances, peak_rps, util_pct, min_replicas):
    rows = []
    # compute replicas with integer ceiling, monthly cost, then sort
    return rows
''',
    solution='''def rankFleets(instances, peak_rps, util_pct, min_replicas):
    rows = []
    for inst in instances:
        need = peak_rps * 100
        per_replica = inst["rps"] * util_pct
        replicas = max(min_replicas, (need + per_replica - 1) // per_replica)
        rows.append([inst["name"], replicas, replicas * inst["cents_per_hour"] * 730])
    rows.sort(key=lambda r: (r[2], r[1], r[0]))
    return rows
''',
    tests=[
        [[{"name": "small", "cents_per_hour": 10, "rps": 50}, {"name": "large", "cents_per_hour": 38, "rps": 220}], 300, 60, 2],
        [[], 100, 70, 1],
        [[{"name": "only", "cents_per_hour": 100, "rps": 1000}], 1, 50, 3],
        [[{"name": "a", "cents_per_hour": 20, "rps": 100}], 300, 60, 1],
        [[{"name": "a", "cents_per_hour": 20, "rps": 100}], 300, 100, 1],
        [[{"name": "x", "cents_per_hour": 10, "rps": 100}, {"name": "y", "cents_per_hour": 20, "rps": 200}, {"name": "w", "cents_per_hour": 10, "rps": 100}], 1000, 50, 1],
        [[{"name": "cpu", "cents_per_hour": 34, "rps": 40}, {"name": "gpu-t4", "cents_per_hour": 53, "rps": 400}, {"name": "gpu-a10", "cents_per_hour": 101, "rps": 900}], 2500, 65, 2],
        [[{"name": "z", "cents_per_hour": 7, "rps": 3}], 0, 80, 2],
        [[{"name": "t%02d" % i, "cents_per_hour": 5 + (i * 13) % 97, "rps": 20 + (i * 29) % 400} for i in range(60)], 12345, 70, 2],
    ],
    examples=1,
    wrong_solutions=[
        '''import math
def rankFleets(instances, peak_rps, util_pct, min_replicas):
    rows = []
    for i in instances:
        r = max(min_replicas, math.ceil(peak_rps / i["rps"]))
        rows.append([i["name"], r, r * i["cents_per_hour"] * 730])
    rows.sort(key=lambda r: (r[2], r[1], r[0]))
    return rows
''',
        '''def rankFleets(instances, peak_rps, util_pct, min_replicas):
    rows = []
    for i in instances:
        r = max(min_replicas, (peak_rps * 100) // (i["rps"] * util_pct))
        rows.append([i["name"], r, r * i["cents_per_hour"] * 730])
    rows.sort(key=lambda r: (r[2], r[1], r[0]))
    return rows
''',
    ],
    guide=dict(
        prereqs="Lesson *Cost optimisation for ML workloads* (utilisation, right-sizing, cost per prediction).",
        intuition="Cost is replicas x price. The cheapest instance per hour is not always the cheapest fleet: a pricier machine that serves many more requests can need far fewer replicas.",
        hints=["Never use floats for the ceiling: `300 / (100 * 0.6)` is `5.000000000000001` in floating point and rounds up to 6.",
               "Integer ceiling: `(a + b - 1) // b`.",
               "Sort with the key `(monthly_cents, replicas, name)`."],
        brute_force="This is already a single pass plus a sort; the trap is the arithmetic, not the algorithm.",
        approach="For each instance compute `need = peak_rps * 100` and `per = rps * util_pct`, `replicas = max(min, ceil(need / per))`, cost = replicas x price x 730; then sort.",
        complexity="O(n log n) for n instance types.",
        pitfalls="- Floating-point ceilings giving one replica too many.\n- Forgetting `min_replicas` when traffic is tiny (one replica is a single point of failure).\n- Sizing for average traffic instead of peak.",
        follow_up="Add spot or preemptible prices with an interruption discount, reserved-instance commitments, or autoscaling: if traffic sits at 30% of peak most of the day, an autoscaled fleet costs far less than a peak-sized one.",
    ),
),
dict(
    id="mlops-token-budget-trim",
    title="Fit a Conversation into the Context Window",
    difficulty="Medium",
    pattern="LLMOps",
    entry="fitContext",
    description=r"""
A large language model reads a limited number of **tokens** (pieces of words) per request: its **context
window**. A chat application must therefore drop old messages once a conversation gets long, while
keeping the instructions and the newest messages.

Messages are dictionaries `{"role": ..., "content": ...}` where role is `"system"` (instructions),
`"user"` or `"assistant"`. In this problem a message costs `4 + number of whitespace-separated words in
content` tokens (the 4 stands for the formatting overhead each message adds).

Write `fitContext(messages, budget)` returning the **sorted list of indices** of the messages to send:

1. Every `"system"` message is always kept.
2. The **last** message must be kept (it is the question being asked); it is never a system message.
3. Then walk backwards from the second-to-last message, skipping system messages (already counted), and
   keep each message while the running total stays within `budget`. Stop at the **first** message that
   does not fit: never skip a long message to include an older one, because a conversation with a hole
   in it confuses the model.
4. If the system messages plus the last message already exceed `budget`, return `[]` (the request cannot
   be sent).

An empty `messages` list returns `[]`.

**Example:** costs `system` 4 + 5 = 9, `user` "hi" 5, `assistant` 4 + 6 = 10, `user` 4 + 3 = 7,
budget 30 -> keep system (9) and the last message (7) = 16; add the assistant reply (26); the old "hi"
would make 31 > 30, so stop. Result: `[0, 2, 3]`.
""",
    starter='''def fitContext(messages, budget):
    def cost(m):
        return 4 + len(m["content"].split())
    # keep system messages and the last message, then add older messages from newest to oldest
    pass
''',
    solution='''def fitContext(messages, budget):
    if not messages:
        return []

    def cost(m):
        return 4 + len(m["content"].split())

    last = len(messages) - 1
    keep = [i for i, m in enumerate(messages) if m["role"] == "system"]
    total = sum(cost(messages[i]) for i in keep) + cost(messages[last])
    if total > budget:
        return []
    keep.append(last)
    for i in range(last - 1, -1, -1):
        if messages[i]["role"] == "system":
            continue
        c = cost(messages[i])
        if total + c > budget:
            break
        total += c
        keep.append(i)
    return sorted(keep)
''',
    tests=[
        [[{"role": "system", "content": "you are a helpful bot"}, {"role": "user", "content": "hi"},
          {"role": "assistant", "content": "hello how can I help you"}, {"role": "user", "content": "reset my password"}], 30],
        [[], 100],
        [[{"role": "user", "content": "just one question here"}], 8],
        [[{"role": "user", "content": "just one question here"}], 7],
        [[{"role": "system", "content": " ".join(["rule"] * 50)}, {"role": "user", "content": "hello"}], 40],
        [[{"role": "system", "content": "be brief"}, {"role": "user", "content": "a"}, {"role": "assistant", "content": "b"},
          {"role": "user", "content": "c"}, {"role": "assistant", "content": "d"}, {"role": "user", "content": "e"}], 1000],
        [[{"role": "system", "content": "s"}, {"role": "user", "content": "short"},
          {"role": "assistant", "content": " ".join(["long"] * 40)}, {"role": "user", "content": "q"}], 30],
        [[{"role": "user", "content": "old"}, {"role": "system", "content": "mid conversation instruction"},
          {"role": "assistant", "content": "x y"}, {"role": "user", "content": "now"}], 20],
        [[{"role": "system", "content": "  spaced   out \t text "}, {"role": "user", "content": ""}], 9],
        [[{"role": "system", "content": "policy " * 20}] +
         [{"role": ("user" if i % 2 == 0 else "assistant"), "content": " ".join(["w%d" % i] * (1 + i % 17))} for i in range(400)], 900],
    ],
    examples=1,
    wrong_solutions=[
        '''def fitContext(messages, budget):
    if not messages: return []
    cost = lambda m: 4 + len(m["content"].split())
    last = len(messages) - 1
    keep = [i for i, m in enumerate(messages) if m["role"] == "system"]
    total = sum(cost(messages[i]) for i in keep) + cost(messages[last])
    if total > budget: return []
    keep.append(last)
    for i in range(last - 1, -1, -1):
        if messages[i]["role"] == "system": continue
        if total + cost(messages[i]) <= budget:
            total += cost(messages[i]); keep.append(i)
    return sorted(keep)
''',
        '''def fitContext(messages, budget):
    if not messages: return []
    cost = lambda m: 4 + len(m["content"].split())
    keep, total = [], 0
    for i in range(len(messages) - 1, -1, -1):
        c = cost(messages[i])
        if total + c > budget: break
        total += c; keep.append(i)
    return sorted(keep)
''',
    ],
    guide=dict(
        prereqs="Lessons *Prompt management and evaluation pipelines* (prompt templates, context) and *LLM inference optimization* (why long contexts cost latency and money).",
        intuition="Reserve the must-haves first (instructions and the question), then spend what is left of the budget on recent history, newest first, stopping at the first message that does not fit so the kept history stays contiguous.",
        hints=["`len(text.split())` counts words and ignores repeated spaces and tabs.",
               "Compute the mandatory cost first and return `[]` if it already exceeds the budget.",
               "Walk `range(last - 1, -1, -1)` and `break`, not `continue`, when a message does not fit."],
        brute_force="Trying every subset of messages is exponential and also wrong: the goal is not to pack the most tokens but to keep a contiguous recent history.",
        approach="1. Empty -> `[]`.\n2. `keep` = system indices; `total` = their cost + last message cost; if over budget -> `[]`.\n3. Walk backwards from `last - 1`, skip system messages, add while it fits, break at the first misfit.\n4. Return `sorted(keep)`.",
        complexity="O(n x w) where w is the average number of words per message.",
        pitfalls="- Dropping the system prompt to make room (the model then forgets its rules).\n- Skipping a long message and keeping an older short one, which leaves a hole in the conversation.\n- Counting a system message twice when it sits in the middle of the history.",
        follow_up="Production systems count real tokens with the model's tokenizer, summarise dropped history into a short memory message, or retrieve only relevant past turns. Keeping the stable system prompt at the start also makes prompt caching effective.",
    ),
),
]
