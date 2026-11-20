import numpy as _np

_rng = _np.random.RandomState(0)


def _r(*shape, scale=1.0):
    return (_rng.randn(*shape) * scale).round(3).tolist()


PROBLEMS = [
# ---------------------------------------------------------------- MSE / RMSE / MAE
dict(
    id="ml-mse-mae",
    title="Regression Error Metrics (MSE, RMSE, MAE)",
    difficulty="Easy",
    pattern="Math Foundations",
    kind="function",
    entry="regression_errors",
    compare="float",
    description=r"""
Given the true targets `y_true` and the predictions `y_pred` of a regression model (two lists of
equal length $n \ge 1$), return `[mse, rmse, mae]`:

$$\text{MSE}=\frac1n\sum_{i=1}^n (y_i-\hat y_i)^2,\qquad \text{RMSE}=\sqrt{\text{MSE}},\qquad \text{MAE}=\frac1n\sum_{i=1}^n |y_i-\hat y_i|$$

Use numpy and vectorise; no Python loops needed.

**Example:** `y_true = [3, -0.5, 2, 7]`, `y_pred = [2.5, 0.0, 2, 8]` → `[0.375, 0.6124, 0.5]`
""",
    starter='''import numpy as np

def regression_errors(y_true, y_pred):
    """Return [mse, rmse, mae] as floats."""
    pass
''',
    solution='''import numpy as np

def regression_errors(y_true, y_pred):
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(y_pred, dtype=float)
    r = y - p
    mse = float(np.mean(r ** 2))
    return [mse, float(np.sqrt(mse)), float(np.mean(np.abs(r)))]
''',
    tests=[
        [[3, -0.5, 2, 7], [2.5, 0.0, 2, 8]],
        [[1, 2, 3], [1, 2, 3]],
        [[5], [2]],
        [[0, 0, 0, 0], [1, -1, 1, -1]],
        [[-2, -4, 6], [2, 4, -6]],
        [[1e6, 2e6], [1e6 + 10, 2e6 - 10]],
        [[0.1, 0.2, 0.3], [0.3, 0.2, 0.1]],
        [_rng.randn(51).round(3).tolist(), _rng.randn(51).round(3).tolist()],
        [list(range(100)), [x * 1.1 for x in range(100)]],
        [[2.5, 2.5, 2.5, 2.5], [0, 5, 0, 5]],
    ],
    wrong_solutions=[
        '''import numpy as np
def regression_errors(y_true, y_pred):
    r = np.asarray(y_true, float) - np.asarray(y_pred, float)
    mse = float(np.mean(r ** 2))
    return [mse, float(np.sqrt(mse)), float(np.abs(np.mean(r)))]
''',
        '''import numpy as np
def regression_errors(y_true, y_pred):
    r = np.asarray(y_true, float) - np.asarray(y_pred, float)
    mse = float(np.sum(r ** 2) / (len(r) - 1 if len(r) > 1 else 1))
    return [mse, float(np.sqrt(mse)), float(np.mean(np.abs(r)))]
''',
    ],
    guide=dict(
        prereqs="Vectors and norms (Math foundations, lesson 1); regression metrics (Model evaluation).",
        intuition=r"""All three numbers summarise the **residual vector** $r = y - \hat y$. MSE is the mean of
squared residuals (the squared L2 norm divided by $n$), RMSE takes a square root so the result is back in
the units of the target, and MAE is the mean absolute residual (the L1 norm divided by $n$). Squaring
punishes large errors disproportionately, so MSE/RMSE are **sensitive to outliers**, while MAE treats an
error of 10 as exactly ten times as bad as an error of 1.""",
        hints=[
            "Convert both inputs with `np.asarray(..., dtype=float)` and subtract once.",
            "`np.mean(r**2)` is MSE; `np.sqrt` of that is RMSE.",
            "MAE needs `np.abs` *before* the mean — the mean of signed residuals can be 0 even when every prediction is wrong.",
        ],
        brute_force="A Python loop accumulating `(y-p)**2` and `abs(y-p)` is O(n) too; numpy just does it in C.",
        approach=r"""1. `r = y - p` (vector of residuals).
2. `mse = mean(r**2)`; `rmse = sqrt(mse)`; `mae = mean(|r|)`.

Dry run on the example: residuals $[0.5,-0.5,0,-1]$, squares $[0.25,0.25,0,1]$ → MSE $=1.5/4=0.375$,
RMSE $\approx 0.612$, absolute values sum to 2 → MAE $=0.5$.""",
        complexity="Time O(n), space O(n) for the residual vector.",
        pitfalls=r"""- Taking `abs(mean(r))` instead of `mean(abs(r))` (positive and negative errors cancel).
- Dividing by $n-1$: that is the *sample variance* correction, which does not apply to an error metric.
- Returning numpy scalars is fine (they are normalised), but returning a 0-d array of the wrong shape is not.""",
        follow_up="Implement R² = 1 − SS_res/SS_tot, and Huber loss (quadratic near 0, linear in the tails).",
    ),
),

# ---------------------------------------------------------------- cosine similarity
dict(
    id="ml-cosine-similarity",
    title="Cosine Similarity Matrix",
    difficulty="Easy",
    pattern="Math Foundations",
    kind="function",
    entry="cosine_similarity_matrix",
    compare="float",
    description=r"""
Given two matrices `A` (shape $m\times d$) and `B` (shape $n\times d$) as nested lists, return the
$m\times n$ matrix $S$ with

$$S_{ij} = \frac{a_i\cdot b_j}{\lVert a_i\rVert_2\,\lVert b_j\rVert_2}.$$

If either vector is all zeros, define $S_{ij}=0$ (this is what `sklearn.metrics.pairwise.cosine_similarity`
does). Vectorise: compute it with one matrix product.

**Example:** `A = [[1, 0], [1, 1]]`, `B = [[0, 2], [3, 3]]` → `[[0.0, 0.7071], [0.7071, 1.0]]`
""",
    starter='''import numpy as np

def cosine_similarity_matrix(A, B):
    pass
''',
    solution='''import numpy as np

def cosine_similarity_matrix(A, B):
    A = np.asarray(A, dtype=float)
    B = np.asarray(B, dtype=float)
    na = np.linalg.norm(A, axis=1, keepdims=True)
    nb = np.linalg.norm(B, axis=1, keepdims=True)
    na[na == 0] = 1.0
    nb[nb == 0] = 1.0
    return (A / na) @ (B / nb).T
''',
    tests=[
        [[[1, 0], [1, 1]], [[0, 2], [3, 3]]],
        [[[1, 2, 3]], [[1, 2, 3]]],
        [[[1, 2, 3]], [[-1, -2, -3]]],
        [[[0, 0, 0], [1, 0, 0]], [[1, 1, 1], [0, 0, 0]]],
        [[[3, 4]], [[4, -3], [6, 8], [-3, -4]]],
        [[[1e-3, 2e-3]], [[1e3, 2e3]]],
        [_r(5, 4), _r(3, 4)],
        [_r(10, 8), _r(10, 8)],
        [[[1]], [[5], [-2], [0]]],
        [_r(30, 16), _r(20, 16)],
    ],
    wrong_solutions=[
        '''import numpy as np
def cosine_similarity_matrix(A, B):
    A = np.asarray(A, float); B = np.asarray(B, float)
    return (A @ B.T) / (np.linalg.norm(A, axis=1)[:, None] * np.linalg.norm(B, axis=1)[None, :])
''',
        '''import numpy as np
def cosine_similarity_matrix(A, B):
    A = np.asarray(A, float); B = np.asarray(B, float)
    return A @ B.T
''',
    ],
    guide=dict(
        prereqs="Dot products and norms (Math foundations, lesson 1).",
        intuition=r"""The dot product $a\cdot b = \lVert a\rVert\lVert b\rVert\cos\theta$, so dividing by both norms
leaves only $\cos\theta$: +1 for the same direction, 0 for orthogonal, −1 for opposite. It ignores vector
length, which is exactly what you want for tf-idf documents or embeddings where magnitude is a nuisance.
If you **L2-normalise every row first**, the whole matrix is just one product: $\hat A \hat B^\top$.""",
        hints=[
            "`np.linalg.norm(A, axis=1, keepdims=True)` gives an (m,1) column of row norms.",
            "Normalise rows of A and rows of B, then `A_hat @ B_hat.T`.",
            "Before dividing, replace zero norms by 1 — a zero row then stays a zero row and yields similarity 0 instead of NaN.",
        ],
        brute_force="Two nested loops over (i, j) computing dot/norm products: O(m·n·d) with Python overhead.",
        approach=r"""1. Convert to float arrays.
2. Row norms `na` (m×1) and `nb` (n×1); set zeros to 1.
3. Return `(A/na) @ (B/nb).T` — broadcasting divides each row by its own norm.

On the example: rows of A normalised are $[1,0]$ and $[0.707,0.707]$; rows of B are $[0,1]$ and $[0.707,0.707]$.
Products give $[[0,0.707],[0.707,1]]$.""",
        complexity="Time O(m·n·d) for the matrix product (BLAS-fast), space O(m·n).",
        pitfalls=r"""- Zero vectors: $0/0$ = NaN. Guard the norms.
- Forgetting `keepdims=True` (or `[:, None]`) gives a broadcasting error or divides columns instead of rows.
- Integer inputs: make sure you convert to float before in-place assignment.""",
        follow_up="Cosine *distance* is 1 − S. For unit vectors, squared Euclidean distance = 2 − 2·cos, which is why nearest-neighbour search on normalised embeddings can use either.",
    ),
),

# ---------------------------------------------------------------- softmax
dict(
    id="ml-softmax",
    title="Numerically Stable Softmax",
    difficulty="Easy",
    pattern="Math Foundations",
    kind="function",
    entry="softmax",
    compare="float",
    description=r"""
Given a 2-D list `logits` of shape $n\times k$ (one row of class scores per example), return the row-wise
softmax

$$\operatorname{softmax}(z)_j = \frac{e^{z_j}}{\sum_{c=1}^k e^{z_c}}.$$

Your implementation must be **numerically stable**: logits as large as `1000` or as small as `-1000` must
not produce `inf` or `nan`. Each output row must sum to 1.

**Example:** `[[1, 2, 3]]` → `[[0.0900, 0.2447, 0.6652]]`; `[[1000, 1000]]` → `[[0.5, 0.5]]`
""",
    starter='''import numpy as np

def softmax(logits):
    pass
''',
    solution='''import numpy as np

def softmax(logits):
    z = np.asarray(logits, dtype=float)
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)
''',
    tests=[
        [[[1, 2, 3]]],
        [[[1000, 1000]]],
        [[[0, 0, 0, 0]]],
        [[[1, 2, 3], [1, 1, 1], [-1, 0, 1]]],
        [[[1000, 0, -1000]]],
        [[[-1000, -1001]]],
        [[[5]]],
        [[[710, 700, 690], [-5, 5, 0]]],
        [_r(6, 5, scale=10)],
        [_r(20, 10, scale=100)],
    ],
    wrong_solutions=[
        '''import numpy as np
def softmax(logits):
    e = np.exp(np.asarray(logits, float))
    return e / e.sum(axis=1, keepdims=True)
''',
        '''import numpy as np
def softmax(logits):
    z = np.asarray(logits, float)
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()
''',
    ],
    guide=dict(
        prereqs="Exponentials/logs and floating point (Math foundations, lessons 2–3).",
        intuition=r"""Softmax is **invariant to adding a constant** to every logit of a row:
$\frac{e^{z_j-c}}{\sum_c e^{z_c-c}} = \frac{e^{-c}e^{z_j}}{e^{-c}\sum e^{z_c}}$. Choosing $c=\max_j z_j$ makes
the largest exponent $e^0=1$, so nothing overflows (float64 overflows past $e^{709}$), and at least one term in
the denominator is 1, so we never divide by zero.""",
        hints=[
            "Work row-wise: use `axis=1` and `keepdims=True` everywhere.",
            "Subtract each row's maximum before exponentiating.",
            "A single global max is not enough: a row of `[-1000, -1001]` next to a row of `[0, 1]` underflows to 0/0.",
        ],
        brute_force="The naive `exp(z)/sum(exp(z))` is mathematically correct but returns `nan` once any logit exceeds ~709.",
        approach=r"""1. `z = z - z.max(axis=1, keepdims=True)`
2. `e = exp(z)`
3. `return e / e.sum(axis=1, keepdims=True)`

Dry run `[1000, 0, -1000]`: shift → `[0, -1000, -2000]` → exps `[1, ~0, ~0]` → `[1, 0, 0]`.""",
        complexity="Time O(n·k), space O(n·k).",
        pitfalls=r"""- Normalising over the whole matrix instead of per row.
- Using a global max (fails when rows have very different scales).
- For losses, prefer **log-softmax** $z_j - c - \log\sum e^{z_c - c}$ (the log-sum-exp trick) instead of `log(softmax(z))`, which can produce `log(0) = -inf`.""",
        follow_up="Implement `log_softmax` and cross-entropy from logits; add a temperature parameter $T$ (softmax of $z/T$).",
    ),
),

# ---------------------------------------------------------------- train/test split
dict(
    id="ml-train-test-split",
    title="Deterministic Train/Test Split",
    difficulty="Easy",
    pattern="ML Workflow",
    kind="function",
    entry="split_indices",
    compare="float",
    description=r"""
Re-implement the index logic of `sklearn.model_selection.train_test_split` for `n` samples:

1. `n_test = ceil(test_size * n)`, `n_train = n - n_test`.
2. If `shuffle` is true, draw `perm = np.random.RandomState(seed).permutation(n)`; otherwise `perm = arange(n)`.
3. The **first** `n_test` entries of `perm` are the test indices, the rest are the train indices.

Return `[train_indices, test_indices]` (each a list, in `perm` order). `0 < test_size < 1` and $n \ge 2$.

**Example:** `n=5, test_size=0.4, seed=0, shuffle=False` → `[[2, 3, 4], [0, 1]]`
""",
    starter='''import numpy as np
import math

def split_indices(n, test_size, seed, shuffle):
    pass
''',
    solution='''import numpy as np
import math

def split_indices(n, test_size, seed, shuffle):
    n_test = int(math.ceil(test_size * n))
    perm = np.random.RandomState(seed).permutation(n) if shuffle else np.arange(n)
    return [perm[n_test:].tolist(), perm[:n_test].tolist()]
''',
    tests=[
        [5, 0.4, 0, False],
        [10, 0.25, 42, True],
        [10, 0.25, 0, True],
        [2, 0.5, 1, True],
        [7, 0.1, 3, True],
        [100, 0.2, 7, True],
        [3, 0.34, 0, False],
        [150, 0.25, 0, True],
        [12, 0.5, 123, True],
        [9, 0.99, 5, True],
    ],
    wrong_solutions=[
        '''import numpy as np
def split_indices(n, test_size, seed, shuffle):
    n_test = int(test_size * n)
    perm = np.random.RandomState(seed).permutation(n) if shuffle else np.arange(n)
    return [perm[n_test:].tolist(), perm[:n_test].tolist()]
''',
        '''import numpy as np, math
def split_indices(n, test_size, seed, shuffle):
    n_test = int(math.ceil(test_size * n))
    perm = np.random.RandomState(seed).permutation(n) if shuffle else np.arange(n)
    return [perm[:n - n_test].tolist(), perm[n - n_test:].tolist()]
''',
    ],
    guide=dict(
        prereqs="The first scikit-learn model lesson (why we hold out a test set).",
        intuition=r"""A split is just a random permutation of row indices cut into two pieces. Fixing the seed makes the
cut reproducible, which is why every example in Müller & Guido passes `random_state=0`. Shuffling matters:
iris is sorted by class, so taking the last 25% without shuffling would give a test set containing only
one species.""",
        hints=[
            "`math.ceil(test_size * n)` rounds the test size **up**, as scikit-learn does.",
            "`np.random.RandomState(seed).permutation(n)` gives a reproducible permutation.",
            "Test indices come from the *front* of the permutation.",
        ],
        brute_force="Not applicable — the whole task is O(n).",
        approach=r"""1. Compute `n_test`.
2. Build `perm` (shuffled or identity).
3. Return `[perm[n_test:], perm[:n_test]]`.

With `n=5, test_size=0.4, shuffle=False`: n_test = 2, perm = [0..4], test = [0,1], train = [2,3,4].""",
        complexity="Time O(n), space O(n).",
        pitfalls=r"""- `int(0.25*10)` = 2 but ceil(2.5) = 3: truncating changes the sizes.
- Some floating point products are slightly above an integer (e.g. `0.1*30 = 3.0000000000000004`), and `ceil` then
  rounds up — scikit-learn has the same behaviour, so do not try to "fix" it.
- Forgetting that the RNG must be **local** (`RandomState(seed)`), not the global `np.random.seed`, if you want to avoid side-effects.""",
        follow_up="Stratified split: shuffle within each class and take `test_size` of each class, so class proportions are preserved.",
    ),
),

# ---------------------------------------------------------------- kNN predict
dict(
    id="ml-knn-predict",
    title="k-Nearest Neighbours Classifier",
    difficulty="Medium",
    pattern="Supervised Learning",
    kind="function",
    entry="knn_predict",
    compare="float",
    description=r"""
Implement the prediction step of a k-NN classifier with Euclidean distance.

- `X_train`: $n\times d$ list, `y_train`: $n$ integer labels, `X_test`: $m\times d$ list, `k` ($1\le k\le n$).
- For each test point, find the `k` training points with the smallest distance. **Distance ties** are broken by
  the smaller training index (use a *stable* sort).
- Predict the label with the most votes among those `k`; **vote ties** are broken by the **smallest label**.

Return the list of $m$ predicted labels.

**Example:** `X_train=[[0],[1],[2],[10]]`, `y_train=[0,0,1,1]`, `X_test=[[1.4],[9]]`, `k=3` → `[0, 1]`
""",
    starter='''import numpy as np

def knn_predict(X_train, y_train, X_test, k):
    pass
''',
    solution='''import numpy as np

def knn_predict(X_train, y_train, X_test, k):
    Xtr = np.asarray(X_train, dtype=float)
    ytr = np.asarray(y_train)
    Xte = np.asarray(X_test, dtype=float)
    # squared distances via broadcasting: (m, n)
    d2 = ((Xte[:, None, :] - Xtr[None, :, :]) ** 2).sum(axis=2)
    out = []
    for row in d2:
        idx = np.argsort(row, kind="stable")[:k]
        labels, counts = np.unique(ytr[idx], return_counts=True)
        out.append(int(labels[np.argmax(counts)]))  # unique is sorted -> smallest label wins ties
    return out
''',
    tests=[
        [[[0], [1], [2], [10]], [0, 0, 1, 1], [[1.4], [9]], 3],
        [[[0, 0], [1, 1], [2, 2]], [5, 6, 7], [[0.1, 0.1], [1.9, 2.2]], 1],
        [[[0], [2]], [1, 0], [[1]], 2],
        [[[0], [2], [4]], [1, 0, 0], [[1]], 2],
        [[[0, 0], [0, 1], [1, 0], [1, 1]], [0, 1, 1, 0], [[0.5, 0.5]], 4],
        [[[0], [1], [2], [3], [4]], [2, 2, 1, 1, 0], [[0], [4], [2]], 5],
        [[[1, 2], [3, 4], [5, 6]], [0, 1, 2], [[1, 2], [3, 4], [5, 6]], 1],
        [[[0], [0], [0]], [3, 1, 2], [[0]], 1],
        [_r(40, 3), [i % 3 for i in range(40)], _r(15, 3), 5],
        [_r(60, 2), [int(i % 4 == 0) for i in range(60)], _r(20, 2), 7],
    ],
    wrong_solutions=[
        '''import numpy as np
def knn_predict(X_train, y_train, X_test, k):
    Xtr = np.asarray(X_train, float); ytr = np.asarray(y_train); Xte = np.asarray(X_test, float)
    out = []
    for x in Xte:
        d = ((Xtr - x) ** 2).sum(1)
        out.append(int(ytr[np.argmin(d)]))
    return out
''',
        '''import numpy as np
from collections import Counter
def knn_predict(X_train, y_train, X_test, k):
    Xtr = np.asarray(X_train, float); ytr = list(y_train); Xte = np.asarray(X_test, float)
    out = []
    for x in Xte:
        d = np.abs(Xtr - x).sum(1)
        idx = np.argsort(d, kind="stable")[:k]
        out.append(Counter(ytr[i] for i in idx).most_common(1)[0][0])
    return out
''',
    ],
    guide=dict(
        prereqs="k-NN lesson (Supervised learning, lesson 1); broadcasting.",
        intuition=r"""k-NN has no training phase: "fitting" just stores the data. To predict, measure the distance from
the query to every stored point, take the $k$ closest, and let them vote. Small $k$ = jagged, high-variance
decision boundary; large $k$ = smoother, higher-bias boundary.""",
        hints=[
            "Broadcast `Xte[:, None, :] - Xtr[None, :, :]` to get an (m, n, d) difference tensor; sum squares over the last axis. You do not need the square root — it is monotone.",
            "`np.argsort(row, kind='stable')[:k]` gives the neighbour indices with index-order tie-breaking.",
            "`np.unique(labels, return_counts=True)` returns labels sorted ascending, so `argmax` over counts picks the smallest label among ties.",
        ],
        brute_force="Loop over test points and training points computing distances in Python: O(m·n·d) with large constants. Fine for tiny data; broadcasting is the same complexity but vectorised.",
        approach=r"""1. Distance matrix $D_{ij} = \lVert x^{test}_i - x^{train}_j\rVert^2$ (m × n).
2. For each row: stable argsort, keep first k indices.
3. Count labels; return the most common (smallest on ties).

Example: query 1.4 has squared distances [1.96, 0.16, 0.36, 73.96] → nearest three are indices 1, 2, 0 with labels 0, 1, 0 → predict 0.""",
        complexity="Time O(m·n·d + m·n log n); space O(m·n·d) for the broadcast (chunk it for large data). KD-trees/ball trees or approximate NN (FAISS, HNSW) are used at scale.",
        pitfalls=r"""- `Counter.most_common` breaks ties by *first occurrence*, not smallest label.
- Using Manhattan distance when the task says Euclidean.
- Forgetting that k-NN needs **scaled features** in practice — a feature measured in thousands dominates the distance.""",
        follow_up="Distance-weighted voting (weights 1/d), k-NN regression (mean of neighbour targets), and choosing k by cross-validation.",
    ),
),
]
