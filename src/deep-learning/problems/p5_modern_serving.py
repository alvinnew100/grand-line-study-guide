import numpy as _np

_rng = _np.random.RandomState(55)


def _arrivals(n, rate_per_ms):
    return _np.cumsum(_rng.exponential(1.0 / rate_per_ms, n)).round(2).tolist()


PROBLEMS = [
# ---------------------------------------------------------------- warmup + cosine
dict(
    id="dl-warmup-cosine-lr",
    title="Linear Warmup + Cosine Decay Schedule",
    difficulty="Medium",
    pattern="Learning-Rate Schedules",
    kind="function",
    entry="lr_schedule",
    compare="float",
    description=r"""
Implement the learning-rate schedule used by most modern training recipes. For an integer step `t` (starting at 0):

- **Warmup** (`t < warmup`): `lr = max_lr · (t + 1) / warmup`.
- **Cosine decay** (`t ≥ warmup`): with `progress = min(1, (t − warmup) / max(1, total − warmup))`,
  `lr = min_lr + 0.5 · (max_lr − min_lr) · (1 + cos(π · progress))`.

So the rate reaches `max_lr` at the last warmup step, starts decaying at step `warmup` (where it equals `max_lr`),
reaches `min_lr` at step `total`, and stays there afterwards. `warmup` may be 0 (no warmup).

Write `lr_schedule(steps, max_lr, min_lr, warmup, total)` returning the list of learning rates for each step in the
list `steps`.

**Example:** `steps=[0, 1, 2, 3, 6]`, `max_lr=1.0`, `min_lr=0.0`, `warmup=2`, `total=6` →
`[0.5, 1.0, 1.0, 0.8536, 0.0]`.
""",
    starter='''import math

def lr_schedule(steps, max_lr, min_lr, warmup, total):
    pass
''',
    solution='''import math

def lr_schedule(steps, max_lr, min_lr, warmup, total):
    out = []
    for t in steps:
        if t < warmup:
            out.append(max_lr * (t + 1) / warmup)
        else:
            progress = min(1.0, (t - warmup) / max(1, total - warmup))
            out.append(min_lr + 0.5 * (max_lr - min_lr) * (1 + math.cos(math.pi * progress)))
    return out
''',
    tests=[
        [[0, 1, 2, 3, 6], 1.0, 0.0, 2, 6],
        [[0, 50, 99, 100, 550, 1000, 1500], 3e-4, 3e-5, 100, 1000],
        [[0, 5, 10], 0.1, 0.0, 0, 10],
        [[0, 1, 2], 0.01, 0.001, 3, 3],
        [list(range(0, 21)), 1.0, 0.1, 5, 20],
        [[7], 2.0, 2.0, 2, 10],
        [[], 1.0, 0.0, 1, 1],
        [[0, 1, 2, 3], 1.0, 0.0, 0, 0],
        [[999, 1000, 1001], 6e-4, 6e-5, 2000, 100000],
    ],
    examples=2,
    wrong_solutions=[
        '''import math
def lr_schedule(steps, max_lr, min_lr, warmup, total):
    out = []
    for t in steps:
        if t < warmup: out.append(max_lr * t / warmup)                         # starts at 0, off by one
        else:
            p = min(1.0, (t - warmup) / max(1, total - warmup))
            out.append(min_lr + 0.5 * (max_lr - min_lr) * (1 + math.cos(math.pi * p)))
    return out
''',
        '''import math
def lr_schedule(steps, max_lr, min_lr, warmup, total):
    out = []
    for t in steps:
        if t < warmup: out.append(max_lr * (t + 1) / warmup)
        else:
            p = (t - warmup) / max(1, total - warmup)                          # not capped: rises again after total
            out.append(min_lr + 0.5 * (max_lr - min_lr) * (1 + math.cos(math.pi * p)))
    return out
''',
    ],
    guide=dict(
        prereqs="Warmup and cosine annealing in *Learning-rate schedules, warmup and gradient clipping*.",
        intuition=r"""Two pieces glued together: a straight ramp from almost zero to the peak, then half a cosine wave from
the peak down to the floor. Capping progress at 1 keeps the rate at the floor once training runs past `total`.""",
        hints=[
            "Branch on `t < warmup`.",
            "Use `max(1, total - warmup)` so the division is safe when warmup equals total.",
            "Cap progress with `min(1.0, ...)`; cos(π) = −1 gives exactly `min_lr`.",
        ],
        brute_force="Not applicable: each value is O(1).",
        approach=r"""Example (warmup 2, total 6): t=0 → 0.5, t=1 → 1.0; t=2 → progress 0 → 1.0; t=3 → progress 1/4 →
0.5·(1 + cos(π/4)) = 0.8536; t=6 → progress 1 → 0.""",
        complexity="O(len(steps)).",
        pitfalls=r"""- Warmup off by one (`t / warmup` starts at 0, so the first step does nothing).
- Not capping progress: cosine rises again after `total`.
- Dividing by zero when `total == warmup` or `warmup == 0`.""",
        follow_up="Implement it with PyTorch's `SequentialLR(LinearLR, CosineAnnealingLR)` and compare the curves; then add cosine restarts (SGDR).",
    ),
),

# ---------------------------------------------------------------- clip grad norm
dict(
    id="dl-clip-grad-norm",
    title="clip_grad_norm_ (2-norm and inf-norm)",
    difficulty="Easy",
    pattern="Training Stability",
    kind="function",
    entry="clip_grad_norm",
    compare="float",
    description=r"""
Reproduce `torch.nn.utils.clip_grad_norm_` on a list of gradients (one flat list of floats per parameter).

`clip_grad_norm(grads, max_norm, norm_type)`:

- `norm_type` is `2` (global L2 norm: square root of the sum of squares of **all** entries of all gradients) or the
  string `"inf"` (the largest absolute entry).
- `clip_coef = max_norm / (total_norm + 1e-6)`; if `clip_coef < 1`, multiply every gradient entry by `clip_coef`,
  otherwise leave them unchanged.
- Return `[total_norm, clipped_grads]`, where `total_norm` is measured **before** clipping.

**Example:** `grads=[[3, 4], [12]]`, `max_norm=1`, `norm_type=2` → total norm 13 → every entry multiplied by
`1/(13 + 1e-6)` → `[13.0, [[0.2308, 0.3077], [0.9231]]]`.
""",
    starter='''def clip_grad_norm(grads, max_norm, norm_type):
    pass
''',
    solution='''import math

def clip_grad_norm(grads, max_norm, norm_type):
    flat = [v for g in grads for v in g]
    if not flat:
        return [0.0, [list(g) for g in grads]]
    if norm_type == "inf":
        total = max(abs(v) for v in flat)
    else:
        total = math.sqrt(sum(v * v for v in flat))
    coef = max_norm / (total + 1e-6)
    if coef < 1:
        grads = [[v * coef for v in g] for g in grads]
    else:
        grads = [list(g) for g in grads]
    return [total, grads]
''',
    tests=[
        [[[3, 4], [12]], 1, 2],
        [[[0.1, -0.2], [0.05]], 1, 2],
        [[[3, -9, 4]], 2, "inf"],
        [[[1, 1, 1, 1]], 2, 2],
        [[[0, 0], [0]], 1, 2],
        [[], 1, 2],
        [[[100.0]], 0.5, 2],
        [[(_rng.randn(10) * 5).round(3).tolist(), (_rng.randn(4) * 5).round(3).tolist()], 1.0, 2],
        [[(_rng.randn(10) * 5).round(3).tolist(), (_rng.randn(4) * 5).round(3).tolist()], 1.0, "inf"],
        [[[1e-3, -1e-3]], 1.0, 2],
    ],
    examples=2,
    wrong_solutions=[
        '''import math
def clip_grad_norm(grads, max_norm, norm_type):
    out, norms = [], []
    for g in grads:                                                # clips each parameter separately
        n = max(abs(v) for v in g) if norm_type == "inf" else math.sqrt(sum(v * v for v in g)) if g else 0.0
        c = max_norm / (n + 1e-6); norms.append(n)
        out.append([v * c for v in g] if c < 1 else list(g))
    total = max(norms) if (norm_type == "inf" and norms) else math.sqrt(sum(n * n for n in norms))
    return [total, out]
''',
        '''import math
def clip_grad_norm(grads, max_norm, norm_type):
    flat = [v for g in grads for v in g]
    total = (max(abs(v) for v in flat) if norm_type == "inf" else math.sqrt(sum(v * v for v in flat))) if flat else 0.0
    out = [[max(-max_norm, min(max_norm, v)) for v in g] for g in grads]      # clips by value instead
    return [total, out]
''',
    ],
    guide=dict(
        prereqs="Gradient clipping in *Learning-rate schedules, warmup and gradient clipping*.",
        intuition=r"""Treat all gradients as one long vector. If it is longer than `max_norm`, shrink the whole vector
uniformly so its length becomes (almost exactly) `max_norm`. The direction of the update is unchanged.""",
        hints=[
            "Flatten across all parameters before computing the norm.",
            "For 'inf', the norm is the maximum absolute entry.",
            "Scale only when the coefficient is below 1; return the pre-clip norm.",
        ],
        brute_force="Already O(total number of entries).",
        approach=r"""[[3,4],[12]]: sqrt(9+16+144) = 13; coef = 1/13.000001 → [0.2308, 0.3077], [0.9231]. Small gradients
([[0.1,−0.2],[0.05]], norm 0.229) stay unchanged.""",
        complexity="O(n) over all gradient entries.",
        pitfalls=r"""- Clipping each parameter's gradient separately (that is a different, weaker rule).
- Clamping each element to [−max_norm, max_norm] (value clipping changes the direction).
- Returning the post-clip norm.
- Empty or all-zero gradients: norm 0, nothing changes.""",
        follow_up="In mixed precision with float16, the gradients are scaled; unscale them before clipping (see the GradScaler problem).",
    ),
),

# ---------------------------------------------------------------- GradScaler (class)
dict(
    id="dl-grad-scaler",
    title="Dynamic Loss Scaler (GradScaler Logic)",
    difficulty="Medium",
    pattern="Mixed Precision",
    kind="class",
    entry="GradScaler",
    compare="float",
    description=r"""
Implement the bookkeeping of `torch.amp.GradScaler` (dynamic loss scaling for float16 training).

`GradScaler(init_scale, growth_factor, backoff_factor, growth_interval)` with methods:

- `scale(loss)` → `loss * current_scale`.
- `unscale(grads)` → a new list with every gradient divided by the current scale.
- `step(found_inf)` → `True` if the optimiser step should be taken (no inf/NaN found), `False` if it must be skipped.
- `update(found_inf)` → `None`. If `found_inf`: `scale *= backoff_factor` and reset the count of consecutive good
  steps to 0. Otherwise increment that count; when it reaches `growth_interval`, `scale *= growth_factor` and reset it
  to 0.
- `get_scale()` → the current scale.

Tests are `[operations, arguments]`; the output is the list of return values (`None` for the constructor and for
`update`).

**Example:** `GradScaler(8, 2, 0.5, 2)`: `update(False)`, `update(False)` → scale 16; `update(True)` → 8;
`scale(0.5)` → 4.0.
""",
    starter='''class GradScaler:
    def __init__(self, init_scale, growth_factor, backoff_factor, growth_interval):
        pass

    def scale(self, loss):
        pass

    def unscale(self, grads):
        pass

    def step(self, found_inf):
        pass

    def update(self, found_inf):
        pass

    def get_scale(self):
        pass
''',
    solution='''class GradScaler:
    def __init__(self, init_scale, growth_factor, backoff_factor, growth_interval):
        self._scale = float(init_scale)
        self.growth_factor = growth_factor
        self.backoff_factor = backoff_factor
        self.growth_interval = growth_interval
        self._good_steps = 0

    def scale(self, loss):
        return loss * self._scale

    def unscale(self, grads):
        return [g / self._scale for g in grads]

    def step(self, found_inf):
        return not found_inf

    def update(self, found_inf):
        if found_inf:
            self._scale *= self.backoff_factor
            self._good_steps = 0
        else:
            self._good_steps += 1
            if self._good_steps == self.growth_interval:
                self._scale *= self.growth_factor
                self._good_steps = 0
        return None

    def get_scale(self):
        return self._scale
''',
    tests=[
        [["GradScaler", "update", "update", "get_scale", "update", "get_scale", "scale"],
         [[8, 2, 0.5, 2], [False], [False], [], [True], [], [0.5]]],
        [["GradScaler", "scale", "unscale", "step", "step"],
         [[65536.0, 2.0, 0.5, 2000], [0.25], [[65536.0, -131072.0, 0.0]], [False], [True]]],
        [["GradScaler", "update", "update", "update", "update", "get_scale", "update", "update", "update", "get_scale"],
         [[1024, 2, 0.5, 3], [False], [False], [True], [False], [], [False], [False], [False], []]],
        [["GradScaler", "update", "update", "update", "get_scale", "step", "unscale"],
         [[4, 2, 0.5, 5], [True], [True], [True], [], [True], [[1.0, 2.0]]]],
        [["GradScaler", "update", "get_scale", "update", "get_scale", "update", "get_scale"],
         [[1.0, 4.0, 0.25, 1], [False], [], [False], [], [True], []]],
        [["GradScaler", "get_scale", "scale", "unscale"],
         [[2.0, 2.0, 0.5, 10], [], [3.0], [[]]]],
        [["GradScaler"] + ["update"] * 7 + ["get_scale"],
         [[1, 2, 0.5, 2]] + [[False], [False], [True], [False], [False], [False], [False]] + [[]]],
    ],
    examples=2,
    wrong_solutions=[
        '''class GradScaler:
    def __init__(self, init_scale, growth_factor, backoff_factor, growth_interval):
        self.s, self.g, self.b, self.i, self.n = float(init_scale), growth_factor, backoff_factor, growth_interval, 0
    def scale(self, loss): return loss * self.s
    def unscale(self, grads): return [x / self.s for x in grads]
    def step(self, found_inf): return not found_inf
    def update(self, found_inf):
        if found_inf: self.s *= self.b                       # forgets to reset the good-step counter
        else:
            self.n += 1
            if self.n == self.i: self.s *= self.g; self.n = 0
    def get_scale(self): return self.s
''',
        '''class GradScaler:
    def __init__(self, init_scale, growth_factor, backoff_factor, growth_interval):
        self.s, self.g, self.b, self.i, self.n = float(init_scale), growth_factor, backoff_factor, growth_interval, 0
    def scale(self, loss): return loss * self.s
    def unscale(self, grads): return [x * self.s for x in grads]          # multiplies instead of dividing
    def step(self, found_inf): return True                                 # never skips
    def update(self, found_inf):
        if found_inf: self.s *= self.b; self.n = 0
        else:
            self.n += 1
            if self.n == self.i: self.s *= self.g; self.n = 0
    def get_scale(self): return self.s
''',
    ],
    guide=dict(
        prereqs="Loss scaling and GradScaler in *GPU memory and mixed precision*.",
        intuition=r"""The scaler searches for the largest loss scale that does not overflow float16: any overflow halves it
(and that step is skipped), while a long run of clean steps doubles it again. Unscaling divides the gradients by the
same factor before the optimiser (or gradient clipping) sees them.""",
        hints=[
            "Keep the scale and a counter of consecutive good steps.",
            "On overflow: multiply by backoff and reset the counter.",
            "On a good step: increment; when the counter equals growth_interval, grow and reset.",
        ],
        brute_force="Not applicable: each operation is O(1) (O(n) for unscale).",
        approach=r"""GradScaler(1024, 2, 0.5, 3): good, good → counter 2; overflow → 512, counter 0; good → counter 1 (scale 512);
then three more good steps → counter reaches 3 → 1024.""",
        complexity="O(1) per call, O(n) for unscale.",
        pitfalls=r"""- Not resetting the counter after an overflow (growth would come too early).
- Growing on every good step instead of after `growth_interval` of them.
- Taking the optimiser step even when gradients overflowed.""",
        follow_up="PyTorch's defaults are init_scale 65536, growth_factor 2, backoff_factor 0.5, growth_interval 2000. Why is no scaler needed for bfloat16?",
    ),
),

# ---------------------------------------------------------------- request batching
dict(
    id="dl-request-batching",
    title="Dynamic Request Batching Simulator",
    difficulty="Medium",
    pattern="Model Serving",
    kind="function",
    entry="batch_requests",
    compare="float",
    tolerance=1e-6,
    description=r"""
Simulate one inference worker with dynamic batching. Requests arrive at the non-decreasing times `arrivals`
(milliseconds). The worker is free at time 0. Running a batch of `n` requests takes `fixed + per_item · n` ms.

Batches are formed in arrival order:

1. The next batch starts with the earliest unprocessed request `i`. Its collection **deadline** is
   `max(arrivals[i] + max_wait, free_at)`, where `free_at` is when the worker finishes its previous batch.
2. Add requests in order while the batch has fewer than `max_batch` requests and the request's arrival time is
   `≤ deadline`.
3. If the batch is full, it starts at `max(free_at, arrival of its last request)`; otherwise it starts at the
   `deadline`.
4. It finishes at `start + fixed + per_item · size`; each request's latency is `finish − its arrival`;
   then `free_at = finish`.

Write `batch_requests(arrivals, max_batch, max_wait, fixed, per_item)` returning `[batch_sizes, latencies]`
(latencies in arrival order).

**Example:** `arrivals=[0, 1, 2, 10]`, `max_batch=2`, `max_wait=5`, `fixed=3`, `per_item=1`: batch {0, 1} is full,
starts at 1, ends at 6; batch {2}: deadline max(7, 6) = 7, request 10 is too late, starts 7, ends 11; batch {10}:
deadline 15, starts 15, ends 19 → `[[2, 1, 1], [6, 5, 9, 9]]`.
""",
    starter='''def batch_requests(arrivals, max_batch, max_wait, fixed, per_item):
    pass
''',
    solution='''def batch_requests(arrivals, max_batch, max_wait, fixed, per_item):
    sizes, lat = [], []
    i, n, free_at = 0, len(arrivals), 0.0
    while i < n:
        deadline = max(arrivals[i] + max_wait, free_at)
        j = i
        while j < n and j - i < max_batch and arrivals[j] <= deadline:
            j += 1
        size = j - i
        start = max(free_at, arrivals[j - 1]) if size == max_batch else deadline
        finish = start + fixed + per_item * size
        lat.extend(finish - arrivals[k] for k in range(i, j))
        sizes.append(size)
        free_at, i = finish, j
    return [sizes, lat]
''',
    tests=[
        [[0, 1, 2, 10], 2, 5, 3, 1],
        [[0, 1, 2, 10], 1, 0, 3, 1],
        [[0, 0, 0, 0, 0], 4, 10, 5, 0.5],
        [[], 8, 2, 8, 0.5],
        [[5], 8, 2, 8, 0.5],
        [[0, 100, 200], 8, 2, 8, 0.5],
        [_arrivals(60, 0.4), 32, 2, 8, 0.5],
        [_arrivals(60, 0.4), 1, 0, 8, 0.5],
        [_arrivals(80, 0.05), 16, 10, 4, 0.2],
        [[0, 1, 1, 1, 30, 31], 3, 4, 10, 1],
    ],
    examples=2,
    wrong_solutions=[
        '''def batch_requests(arrivals, max_batch, max_wait, fixed, per_item):
    sizes, lat, i, n, free_at = [], [], 0, len(arrivals), 0.0
    while i < n:
        deadline = arrivals[i] + max_wait                       # ignores that the worker may still be busy
        j = i
        while j < n and j - i < max_batch and arrivals[j] <= deadline: j += 1
        size = j - i
        start = max(free_at, arrivals[j - 1]) if size == max_batch else max(deadline, free_at)
        fin = start + fixed + per_item * size
        lat.extend(fin - arrivals[k] for k in range(i, j)); sizes.append(size); free_at, i = fin, j
    return [sizes, lat]
''',
        '''def batch_requests(arrivals, max_batch, max_wait, fixed, per_item):
    sizes, lat, i, n, free_at = [], [], 0, len(arrivals), 0.0
    while i < n:
        deadline = max(arrivals[i] + max_wait, free_at)
        j = i
        while j < n and j - i < max_batch and arrivals[j] <= deadline: j += 1
        size = j - i
        start = deadline                                         # full batches also wait for the deadline
        fin = start + fixed + per_item * size
        lat.extend(fin - arrivals[k] for k in range(i, j)); sizes.append(size); free_at, i = fin, j
    return [sizes, lat]
''',
    ],
    guide=dict(
        prereqs="Dynamic request batching in *Serving and exporting PyTorch models*.",
        intuition=r"""A batch keeps collecting until it is full or its waiting budget is spent, but it can never start
before the worker is free, so while the worker is busy the batch may keep collecting past `max_wait`. Full batches
start immediately (once the worker is free); partial ones start at the deadline.""",
        hints=[
            "Track `free_at`, the worker's finish time.",
            "Deadline = max(first arrival + max_wait, free_at).",
            "Start time differs for full and partial batches; latency = finish − arrival for every member.",
        ],
        brute_force="An event-driven simulation with a priority queue of events gives the same result with more machinery.",
        approach=r"""Walk through the example in the statement: the first batch fills at t = 1 and finishes at 6; the next batch
opens at t = 2 with deadline 7 (the worker is free at 6); nothing else arrives by 7, so it runs alone from 7 to 11; the
last request waits its full 5 ms budget.""",
        complexity="O(n): each request is added to exactly one batch.",
        pitfalls=r"""- Ignoring `free_at` in the deadline (requests that arrive while the worker is busy should join the next batch).
- Making full batches wait until the deadline.
- An empty arrival list returns `[[], []]`.""",
        follow_up="Add several workers, or compute the maximum sustainable request rate for given costs (the point where the batch size reaches max_batch).",
    ),
),
]
