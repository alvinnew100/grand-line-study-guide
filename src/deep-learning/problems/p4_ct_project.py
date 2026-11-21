import numpy as _np

_rng = _np.random.RandomState(44)


def _labels_probs(n, pos_rate, sep):
    y = (_rng.rand(n) < pos_rate).astype(int)
    p = _np.clip(_rng.rand(n) * (1 - sep) + y * sep, 0, 1).round(3)
    return y.tolist(), p.tolist()


def _blobs(h, w, density):
    return (_rng.rand(h, w) < density).astype(int).tolist()


PROBLEMS = [
# ---------------------------------------------------------------- precision / recall / F1
dict(
    id="dl-precision-recall-f1",
    title="Precision, Recall and F1 at a Threshold",
    difficulty="Easy",
    pattern="Metrics",
    kind="function",
    entry="prf_at_threshold",
    compare="float",
    description=r"""
Given true binary labels and predicted probabilities, flag a sample as positive when `prob >= threshold`.

Write `prf_at_threshold(labels, probs, threshold)` returning `[precision, recall, f1, [tp, fp, fn, tn]]`:

- `precision = tp / (tp + fp)`, `recall = tp / (tp + fn)`, `f1 = 2·p·r / (p + r)`.
- Any ratio whose denominator is 0 is defined as `0.0` (so a model that flags nothing has precision 0).

**Example:** `labels=[1,0,1,0,0]`, `probs=[0.9,0.6,0.4,0.2,0.7]`, `threshold=0.5` → flags samples 0, 1, 4:
tp=1, fp=2, fn=1, tn=1 → `[0.3333, 0.5, 0.4, [1, 2, 1, 1]]`.
""",
    starter='''def prf_at_threshold(labels, probs, threshold):
    pass
''',
    solution='''def prf_at_threshold(labels, probs, threshold):
    tp = fp = fn = tn = 0
    for y, p in zip(labels, probs):
        flag = p >= threshold
        if flag and y == 1:
            tp += 1
        elif flag:
            fp += 1
        elif y == 1:
            fn += 1
        else:
            tn += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return [precision, recall, f1, [tp, fp, fn, tn]]
''',
    tests=[
        [[1, 0, 1, 0, 0], [0.9, 0.6, 0.4, 0.2, 0.7], 0.5],
        [[1, 0, 1, 0, 0], [0.9, 0.6, 0.4, 0.2, 0.7], 0.95],
        [[1, 0, 1, 0, 0], [0.9, 0.6, 0.4, 0.2, 0.7], 0.0],
        [[0, 0, 0], [0.1, 0.9, 0.5], 0.5],
        [[1, 1], [0.5, 0.49], 0.5],
        [[], [], 0.5],
        [*_labels_probs(200, 0.05, 0.5), 0.5],
        [*_labels_probs(500, 0.01, 0.6), 0.3],
        [*_labels_probs(300, 0.3, 0.2), 0.6],
        [[1, 0], [0.7, 0.7], 0.7],
    ],
    examples=2,
    wrong_solutions=[
        '''def prf_at_threshold(labels, probs, threshold):
    tp = sum(1 for y, p in zip(labels, probs) if p > threshold and y == 1)        # strict >
    fp = sum(1 for y, p in zip(labels, probs) if p > threshold and y == 0)
    fn = sum(1 for y, p in zip(labels, probs) if p <= threshold and y == 1)
    tn = sum(1 for y, p in zip(labels, probs) if p <= threshold and y == 0)
    pr = tp / (tp + fp) if tp + fp else 0.0; rc = tp / (tp + fn) if tp + fn else 0.0
    return [pr, rc, 2 * pr * rc / (pr + rc) if pr + rc else 0.0, [tp, fp, fn, tn]]
''',
        '''def prf_at_threshold(labels, probs, threshold):
    tp = sum(1 for y, p in zip(labels, probs) if p >= threshold and y == 1)
    fp = sum(1 for y, p in zip(labels, probs) if p >= threshold and y == 0)
    fn = sum(1 for y, p in zip(labels, probs) if p < threshold and y == 1)
    tn = len(labels) - tp - fp - fn
    pr = tp / (tp + fp) if tp + fp else 0.0; rc = tp / (tp + fn) if tp + fn else 0.0
    return [pr, rc, (pr + rc) / 2, [tp, fp, fn, tn]]                            # arithmetic mean
''',
    ],
    guide=dict(
        prereqs="*Rare positives: precision, recall, F1 and balanced sampling*.",
        intuition=r"""Precision is about the flags you raised (how many were right); recall is about the positives that exist
(how many you caught). F1 is high only when both are, because the harmonic mean is pulled towards the smaller.""",
        hints=[
            "Count the four confusion-matrix cells in one pass; note `>=` for the threshold.",
            "Guard every division: an empty denominator gives 0.0.",
            "F1 = 2pr/(p + r), also guarded.",
        ],
        brute_force="Already O(n).",
        approach=r"""Example: flags at 0.9, 0.6, 0.7 → labels 1, 0, 0 → tp 1, fp 2; the unflagged 0.4 is a positive → fn 1; 0.2 → tn 1.
Precision 1/3, recall 1/2, F1 = 2·(1/6)/(5/6) = 0.4.""",
        complexity="O(n) time, O(1) space.",
        pitfalls=r"""- Using `>` instead of `>=` at the threshold.
- Dividing by zero when nothing is flagged or there are no positives.
- Using the arithmetic mean instead of the harmonic mean.""",
        follow_up="Sweep all distinct thresholds to build the precision-recall curve and find the F1-maximising threshold in O(n log n) by sorting once.",
    ),
),

# ---------------------------------------------------------------- balanced sample weights
dict(
    id="dl-class-balanced-weights",
    title="Class-Balanced Sampling Weights",
    difficulty="Easy",
    pattern="Class Imbalance",
    kind="function",
    entry="balanced_sample_weights",
    compare="float",
    description=r"""
`WeightedRandomSampler` draws index `i` with probability proportional to `weights[i]`. To make every class equally
likely, give each sample a weight inversely proportional to its class's frequency.

Write `balanced_sample_weights(labels)` that returns a list of per-sample weights such that:

- every sample of the same class has the same weight;
- each class present in `labels` has the **same total weight**;
- all weights sum to **1**.

So `weight_i = 1 / (K · count[label_i])`, where `K` is the number of distinct classes present. Labels are arbitrary
integers (not necessarily 0..K−1). `labels` is non-empty.

**Example:** `labels=[0, 0, 0, 1]` → `K=2` → `[1/6, 1/6, 1/6, 1/2]`.
""",
    starter='''def balanced_sample_weights(labels):
    pass
''',
    solution='''from collections import Counter

def balanced_sample_weights(labels):
    counts = Counter(labels)
    k = len(counts)
    return [1.0 / (k * counts[y]) for y in labels]
''',
    tests=[
        [[0, 0, 0, 1]],
        [[1, 1, 1, 1]],
        [[3, 7, 3, 3, 7, 9]],
        [[0, 1, 2]],
        [[5]],
        [[0] * 400 + [1]],
        [[2, 2, 1, 1, 0, 0, 0, 0]],
        [_rng.randint(0, 4, 50).tolist()],
        [[-1, 1, -1, 1, -1]],
    ],
    examples=2,
    wrong_solutions=[
        '''from collections import Counter
def balanced_sample_weights(labels):
    c = Counter(labels)
    return [1.0 / c[y] for y in labels]                       # balanced but does not sum to 1
''',
        '''from collections import Counter
def balanced_sample_weights(labels):
    c = Counter(labels); n = len(labels)
    return [c[y] / n / len(labels) for y in labels]           # proportional to frequency: the opposite
''',
    ],
    guide=dict(
        prereqs="`WeightedRandomSampler` in *Rare positives: precision, recall, F1 and balanced sampling*.",
        intuition=r"""If class c has n_c samples each with weight w_c, its total weight is n_c·w_c. Setting w_c = 1/(K·n_c) makes
every class total exactly 1/K, so a sampler draws each class equally often, and the K totals sum to 1.""",
        hints=[
            "`collections.Counter(labels)` gives the counts per class.",
            "K is the number of distinct labels present.",
            "Weight for sample i: `1 / (K * counts[labels[i]])`.",
        ],
        brute_force="Recount the class for every sample: O(n²). Counting once is O(n).",
        approach=r"""[3, 7, 3, 3, 7, 9]: counts {3:3, 7:2, 9:1}, K = 3 → weights 1/9 for each 3, 1/6 for each 7, 1/3 for the 9.
Class totals: 3·1/9 = 1/3, 2·1/6 = 1/3, 1/3. Sum 1.""",
        complexity="O(n) time and O(K) extra space.",
        pitfalls=r"""- Forgetting to normalise (PyTorch's sampler does not need it, but the spec does).
- Assuming labels are 0..K−1 and indexing a list by label.
- Weights proportional to frequency (the opposite of what you want).""",
        follow_up="Add a `power` parameter (weights ∝ count^−power) to interpolate between natural sampling (0) and full balancing (1), a common compromise.",
    ),
),

# ---------------------------------------------------------------- augmentation
dict(
    id="dl-augment-flip-shift",
    title="Flip-and-Shift Augmentation as a Pure Function",
    difficulty="Medium",
    pattern="Data Augmentation",
    kind="function",
    entry="augment",
    description=r"""
Implement a deterministic version of two augmentations used on CT crops, as a **pure function** (it must not modify
its input; it returns a new array).

`augment(volume, flips, shift)`:

- `volume`: a nested list of numbers with `d` dimensions (d = 1, 2 or 3).
- `flips`: a list of axes to mirror (each axis at most once; may be empty).
- `shift`: a list of `d` integers. After flipping, move the content by `shift[a]` positions along axis `a`
  (positive = towards higher indices). Positions that move in from outside are filled with **0**; content that moves
  past the edge is lost (this is not a wrap-around roll).
- Return the result as a nested list of the same shape.

**Example:** `volume=[[1,2,3],[4,5,6]]`, `flips=[1]`, `shift=[1,0]` → flip columns `[[3,2,1],[6,5,4]]` → shift rows
down by one `[[0,0,0],[3,2,1]]`.
""",
    starter='''def augment(volume, flips, shift):
    pass
''',
    solution='''import numpy as np

def augment(volume, flips, shift):
    a = np.array(volume)
    for axis in flips:
        a = np.flip(a, axis=axis)
    out = np.zeros_like(a)
    src, dst = [], []
    for n, s in zip(a.shape, shift):
        if abs(s) >= n:
            return out.tolist()
        if s >= 0:
            src.append(slice(0, n - s)); dst.append(slice(s, n))
        else:
            src.append(slice(-s, n)); dst.append(slice(0, n + s))
    out[tuple(dst)] = a[tuple(src)]
    return out.tolist()
''',
    tests=[
        [[[1, 2, 3], [4, 5, 6]], [1], [1, 0]],
        [[[1, 2, 3], [4, 5, 6]], [], [0, 0]],
        [[[1, 2, 3], [4, 5, 6]], [0, 1], [0, 0]],
        [[[1, 2, 3], [4, 5, 6]], [], [0, -2]],
        [[1, 2, 3, 4, 5], [0], [2]],
        [[1, 2, 3, 4, 5], [], [-5]],
        [[1, 2, 3, 4, 5], [], [7]],
        [_rng.randint(-1000, 1000, (3, 4, 5)).tolist(), [0, 2], [1, -1, 2]],
        [_rng.randint(-1000, 1000, (4, 4, 4)).tolist(), [1], [0, 3, -3]],
        [_rng.randint(0, 9, (6, 6)).tolist(), [0], [-1, 1]],
        [[[7]], [0, 1], [0, 0]],
    ],
    examples=2,
    wrong_solutions=[
        '''import numpy as np
def augment(volume, flips, shift):
    a = np.array(volume)
    for axis in flips: a = np.flip(a, axis=axis)
    for axis, s in enumerate(shift): a = np.roll(a, s, axis=axis)      # wraps around instead of zero fill
    return a.tolist()
''',
        '''import numpy as np
def augment(volume, flips, shift):
    a = np.array(volume); out = np.zeros_like(a)
    src, dst = [], []
    for n, s in zip(a.shape, shift):
        if abs(s) >= n: return out.tolist()
        src.append(slice(0, n - s) if s >= 0 else slice(-s, n)); dst.append(slice(s, n) if s >= 0 else slice(0, n + s))
    out[tuple(dst)] = a[tuple(src)]
    for axis in flips: out = np.flip(out, axis=axis)                   # flips after shifting
    return out.tolist()
''',
    ],
    guide=dict(
        prereqs="Augmentation in *Overfitting and data augmentation*; slicing from the *Tensors* lessons.",
        intuition=r"""A shift with zero fill is a copy between two overlapping windows: the destination window starts `s` later
than the source window along each axis. Flipping first and shifting second matters: the operations do not commute.""",
        hints=[
            "`np.flip(a, axis)` mirrors one axis; apply it for each axis in `flips`.",
            "For shift s ≥ 0 along an axis of length n: source `[0, n−s)`, destination `[s, n)`; for s < 0: source `[−s, n)`, destination `[0, n+s)`.",
            "If |s| ≥ n on any axis the result is all zeros.",
        ],
        brute_force="Loop over every output index and compute its source index, checking bounds: O(size) with Python overhead.",
        approach=r"""Example: flip axis 1 → [[3,2,1],[6,5,4]]. Shift [1, 0]: rows source [0, 1) → destination [1, 2), columns unchanged
→ [[0,0,0],[3,2,1]].""",
        complexity="O(number of elements).",
        pitfalls=r"""- Using `np.roll`, which wraps content around instead of filling with zeros.
- Shifting before flipping.
- Modifying the caller's list in place (NumPy copies when you call `np.array`, so this is safe).""",
        follow_up="Generalise to a random augmentation: draw the flips and shift from a seeded generator so that training is reproducible, and apply the identical transform to a segmentation mask.",
    ),
),

# ---------------------------------------------------------------- IoU and Dice
dict(
    id="dl-iou-dice",
    title="IoU and Dice for Segmentation Masks",
    difficulty="Easy",
    pattern="Metrics",
    kind="function",
    entry="iou_dice",
    compare="float",
    description=r"""
Given a predicted binary mask and a ground-truth binary mask of the same shape (nested lists of 0/1, any number of
dimensions), return `[iou, dice]`:

- `iou = |P ∩ G| / |P ∪ G|`
- `dice = 2·|P ∩ G| / (|P| + |G|)`

where `|·|` counts the 1s. If both masks are completely empty, return `[1.0, 1.0]` (a perfect "nothing to find").

**Example:** `pred=[1,1,0,0]`, `target=[0,1,1,0]` → intersection 1, union 3, sizes 2 and 2 → `[0.3333, 0.5]`.
""",
    starter='''def iou_dice(pred, target):
    pass
''',
    solution='''import numpy as np

def iou_dice(pred, target):
    p = np.asarray(pred).astype(bool)
    g = np.asarray(target).astype(bool)
    inter = np.logical_and(p, g).sum()
    union = np.logical_or(p, g).sum()
    total = p.sum() + g.sum()
    if total == 0:
        return [1.0, 1.0]
    return [inter / union, 2 * inter / total]
''',
    tests=[
        [[1, 1, 0, 0], [0, 1, 1, 0]],
        [[0, 0, 0], [0, 0, 0]],
        [[1, 1], [1, 1]],
        [[1, 0], [0, 1]],
        [[0, 0, 0], [1, 1, 0]],
        [[[1, 1, 0], [0, 1, 0]], [[1, 0, 0], [0, 1, 1]]],
        [_blobs(16, 16, 0.3), _blobs(16, 16, 0.3)],
        [(_rng.rand(4, 8, 8) < 0.1).astype(int).tolist(), (_rng.rand(4, 8, 8) < 0.1).astype(int).tolist()],
        [[[1] * 10] * 10, [[1] * 5 + [0] * 5] * 10],
    ],
    examples=2,
    wrong_solutions=[
        '''import numpy as np
def iou_dice(pred, target):
    p, g = np.asarray(pred).astype(bool), np.asarray(target).astype(bool)
    inter, union = (p & g).sum(), (p | g).sum()
    return [inter / union if union else 0.0, 2 * inter / (p.sum() + g.sum()) if p.sum() + g.sum() else 0.0]   # empty -> 0
''',
        '''import numpy as np
def iou_dice(pred, target):
    p, g = np.asarray(pred).astype(bool), np.asarray(target).astype(bool)
    inter, union = (p & g).sum(), (p | g).sum()
    if union == 0: return [1.0, 1.0]
    return [inter / union, inter / union * 2]                                # wrong Dice formula
''',
    ],
    guide=dict(
        prereqs="Dice and IoU in *Segmentation with U-Net and Dice loss*.",
        intuition=r"""Both measure overlap and ignore the (usually huge) correctly empty background. Dice counts the overlap
twice against the sum of sizes; IoU counts it once against the union. They are monotonically related:
Dice = 2·IoU/(1 + IoU).""",
        hints=[
            "Convert to boolean arrays; `&` and `|` give intersection and union.",
            "Handle the both-empty case before dividing.",
            "Dice's denominator is |P| + |G|, not the union.",
        ],
        brute_force="Python loops over flattened lists: same O(n).",
        approach=r"""[1,1,0,0] vs [0,1,1,0]: intersection 1, union 3 → IoU 1/3; Dice 2·1/(2+2) = 0.5. Check: 2·(1/3)/(4/3) = 0.5.""",
        complexity="O(n) time.",
        pitfalls=r"""- Dividing by zero when both masks are empty.
- Using union in Dice's denominator.
- Treating non-zero values other than 1 inconsistently (cast to bool).""",
        follow_up="Compute them per class and average (mean IoU, the standard semantic-segmentation metric), or compute soft Dice on probabilities for a loss.",
    ),
),

# ---------------------------------------------------------------- connected components
dict(
    id="dl-connected-components",
    title="Group Flagged Pixels into Candidates",
    difficulty="Medium",
    pattern="Post-processing",
    kind="function",
    entry="components",
    compare="float",
    description=r"""
After segmentation, flagged pixels are grouped into objects. Write `components(grid, connectivity)` for a 2-D grid
of 0/1 values (list of equal-length rows, possibly empty):

- Two flagged cells belong to the same component if they are neighbours: with `connectivity=4`, neighbours share an
  edge (up, down, left, right); with `connectivity=8`, diagonal neighbours count too.
- For each component return `[size, centre_row, centre_col]`, where the centre is the mean row and mean column of its
  cells.
- Sort components by size (largest first), then by centre row, then by centre column.

**Example:** `grid=[[1,1,0],[0,0,0],[0,0,1]]`, `connectivity=4` → `[[2, 0.0, 0.5], [1, 2.0, 2.0]]`.
""",
    starter='''def components(grid, connectivity):
    pass
''',
    solution='''from collections import deque

def components(grid, connectivity):
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    steps = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if connectivity == 8:
        steps += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    seen = [[False] * cols for _ in range(rows)]
    out = []
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] and not seen[r][c]:
                seen[r][c] = True
                queue, cells = deque([(r, c)]), []
                while queue:
                    y, x = queue.popleft()
                    cells.append((y, x))
                    for dy, dx in steps:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < rows and 0 <= nx < cols and grid[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx] = True
                            queue.append((ny, nx))
                n = len(cells)
                out.append([n, sum(y for y, _ in cells) / n, sum(x for _, x in cells) / n])
    out.sort(key=lambda t: (-t[0], t[1], t[2]))
    return out
''',
    tests=[
        [[[1, 1, 0], [0, 0, 0], [0, 0, 1]], 4],
        [[[1, 0], [0, 1]], 4],
        [[[1, 0], [0, 1]], 8],
        [[], 4],
        [[[0, 0], [0, 0]], 8],
        [[[1, 1, 1], [1, 0, 1], [1, 1, 1]], 4],
        [[[1, 0, 1, 0, 1]], 8],
        [[[1, 0, 0, 1], [0, 1, 1, 0], [0, 1, 1, 0], [1, 0, 0, 1]], 4],
        [[[1, 0, 0, 1], [0, 1, 1, 0], [0, 1, 1, 0], [1, 0, 0, 1]], 8],
        [_blobs(20, 20, 0.35), 4],
        [_blobs(20, 20, 0.35), 8],
        [[[1] * 30 for _ in range(30)], 4],
    ],
    examples=3,
    wrong_solutions=[
        '''from collections import deque
def components(grid, connectivity):
    rows = len(grid); cols = len(grid[0]) if rows else 0
    steps = [(1, 0), (-1, 0), (0, 1), (0, -1)]                 # ignores connectivity=8
    seen = [[False] * cols for _ in range(rows)]; out = []
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] and not seen[r][c]:
                seen[r][c] = True; q, cells = deque([(r, c)]), []
                while q:
                    y, x = q.popleft(); cells.append((y, x))
                    for dy, dx in steps:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < rows and 0 <= nx < cols and grid[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx] = True; q.append((ny, nx))
                n = len(cells); out.append([n, sum(y for y, _ in cells) / n, sum(x for _, x in cells) / n])
    out.sort(key=lambda t: (-t[0], t[1], t[2]))
    return out
''',
        '''def components(grid, connectivity):
    out = []
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v: out.append([1, float(r), float(c)])            # every pixel its own component
    out.sort(key=lambda t: (-t[0], t[1], t[2]))
    return out
''',
    ],
    guide=dict(
        prereqs="Grouping voxels into candidates in *End to end: grouping, ROC/AUC and fine-tuning*.",
        intuition=r"""Each unvisited flagged cell starts a flood fill that visits every flagged cell reachable through
neighbour steps; everything it reaches is one component. Marking cells as seen when they are queued guarantees each
cell is processed once.""",
        hints=[
            "Use breadth-first search with a queue (or depth-first with an explicit stack; recursion can overflow on a 30×30 blob).",
            "Neighbour steps: 4 orthogonal moves, plus 4 diagonals for connectivity 8.",
            "Collect each component's cells, then compute size and mean row/column; sort with key (−size, row, col).",
        ],
        brute_force="Union-find over all neighbouring flagged pairs works too, also near-linear; repeated relabelling passes until stable can be O(n²).",
        approach=r"""Diagonal pair [[1,0],[0,1]]: with 4-connectivity the cells do not touch → two components of size 1; with
8-connectivity they form one component of size 2 centred at (0.5, 0.5). The ring with a hole in the middle is one
component of 8 cells centred at (1, 1).""",
        complexity="O(rows × cols): each cell is visited a constant number of times.",
        pitfalls=r"""- Forgetting diagonals for 8-connectivity (or adding them for 4).
- Marking cells as seen only when popped, which can enqueue a cell twice.
- Recursion depth limits on large components.
- An empty grid returns an empty list.""",
        follow_up="Extend to 3-D (6- or 26-connectivity) and weight centres by intensity, as `scipy.ndimage.center_of_mass` does for CT candidates.",
    ),
),
]
