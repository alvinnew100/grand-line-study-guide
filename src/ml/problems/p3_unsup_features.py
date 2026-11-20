import numpy as _np

_rng = _np.random.RandomState(3)


def _r(*shape, scale=1.0):
    return (_rng.randn(*shape) * scale).round(3).tolist()


def _blobs(n, d, k):
    centers = _rng.randn(k, d) * 5
    X = _np.vstack([centers[i % k] + _rng.randn(d) for i in range(n)]).round(3)
    return X.tolist()


def _corr(n, d):
    A = _rng.randn(d, d)
    scales = _np.linspace(3, 0.5, d)
    return ((_rng.randn(n, d) * scales) @ A).round(3).tolist()


PROBLEMS = [
# ---------------------------------------------------------------- standard scaler
dict(
    id="ml-standard-scaler",
    title="StandardScaler: Fit on Train, Transform Both",
    difficulty="Easy",
    pattern="Preprocessing",
    kind="function",
    entry="standard_scale",
    compare="float",
    description=r"""
Implement the behaviour of `sklearn.preprocessing.StandardScaler`. Compute the per-column mean $\mu_j$ and
**population** standard deviation $\sigma_j$ (divide by $n$, i.e. `ddof=0`) **on `X_train` only**, then return
`[Z_train, Z_test]` with

$$z_{ij} = \frac{x_{ij}-\mu_j}{\sigma_j}.$$

If a column has $\sigma_j = 0$ (constant feature), use a scale of 1 for that column (as scikit-learn does).

**Example:** `X_train=[[0],[2]]`, `X_test=[[4]]` → `[[[-1.0],[1.0]], [[3.0]]]`
""",
    starter='''import numpy as np

def standard_scale(X_train, X_test):
    pass
''',
    solution='''import numpy as np

def standard_scale(X_train, X_test):
    A = np.asarray(X_train, dtype=float)
    B = np.asarray(X_test, dtype=float)
    mu = A.mean(axis=0)
    sd = A.std(axis=0)          # ddof=0
    sd[sd == 0] = 1.0
    return [(A - mu) / sd, (B - mu) / sd]
''',
    tests=[
        [[[0], [2]], [[4]]],
        [[[1, 10], [2, 20], [3, 30]], [[2, 20], [0, 0]]],
        [[[5, 1], [5, 2], [5, 3]], [[5, 4], [6, 0]]],
        [[[1, 2, 3]], [[1, 2, 3], [0, 0, 0]]],
        [[[-1, 100], [1, -100]], [[0, 0]]],
        [[[1e6], [1e6 + 2]], [[1e6 + 1]]],
        [_r(10, 3, scale=5), _r(4, 3, scale=5)],
        [_r(50, 6, scale=100), _r(10, 6, scale=100)],
        [[[0.1], [0.2], [0.3], [0.4]], [[0.5], [-0.5]]],
        [_r(7, 2), _r(3, 2, scale=10)],
    ],
    wrong_solutions=[
        '''import numpy as np
def standard_scale(X_train, X_test):
    A = np.asarray(X_train, float); B = np.asarray(X_test, float)
    mu = A.mean(0); sd = A.std(0, ddof=1) if len(A) > 1 else np.ones(A.shape[1]); sd[sd == 0] = 1
    return [(A - mu) / sd, (B - mu) / sd]
''',
        '''import numpy as np
def standard_scale(X_train, X_test):
    A = np.asarray(X_train, float); B = np.asarray(X_test, float)
    def f(M):
        sd = M.std(0); sd[sd == 0] = 1; return (M - M.mean(0)) / sd
    return [f(A), f(B)]
''',
    ],
    guide=dict(
        prereqs="Mean/variance (Math, lesson 3); preprocessing (Unsupervised, lesson 1).",
        intuition=r"""Many models (k-NN, SVM, linear models with regularisation, neural nets, PCA) care about the *scale* of features.
Standardising puts every feature at mean 0 and unit variance. The crucial rule from Müller & Guido: the
transformation is **learned from the training data** and then applied unchanged to the test data — the test set
must be treated as data you have never seen.""",
        hints=[
            "Use `axis=0` for per-column statistics.",
            "`np.std` defaults to `ddof=0` (population), which is what scikit-learn uses.",
            "Never call `.mean()`/`.std()` on the test matrix.",
        ],
        brute_force="Nested loops over columns and rows; same O(n·d) cost.",
        approach=r"""1. $\mu = $ column means of train; $\sigma = $ column stds of train (ddof 0); replace zeros by 1.
2. Transform both matrices with the same $\mu,\sigma$.

Example: train [0,2] → μ=1, σ=1, so train becomes [−1, 1] and the test value 4 becomes 3 — far outside the
training range, which is fine and informative.""",
        complexity="O((n_train + n_test)·d).",
        pitfalls=r"""- Sample std (`ddof=1`) differs from scikit-learn for small n.
- Scaling the test set with its own statistics silently shifts it — a test point identical to a training point would get a different representation.
- Fitting the scaler on the *whole* dataset before cross-validation leaks information (see the Pipelines module).""",
        follow_up="MinMaxScaler ((x−min)/(max−min)), RobustScaler (median and IQR), Normalizer (scales each row to unit norm).",
    ),
),

# ---------------------------------------------------------------- PCA via SVD
dict(
    id="ml-pca-svd",
    title="PCA via SVD (Sign-Normalised)",
    difficulty="Medium",
    pattern="Dimensionality Reduction",
    kind="function",
    entry="pca",
    compare="float",
    tolerance=1e-5,
    description=r"""
Implement principal component analysis with the singular value decomposition.

1. Centre the data: $X_c = X - \bar x$ (column means).
2. Compute the thin SVD $X_c = U S V^\top$; the rows of $V^\top$ are the principal directions.
3. **Sign convention** (SVD signs are arbitrary): flip each component so that its entry with the largest absolute
   value is **positive** (first such entry on ties).
4. Keep the first `k` components.

Return `[components, projected, explained_variance_ratio]`:
`components` is $k\times d$, `projected = X_c @ components.T` is $n\times k$, and the ratio is
$S_j^2/\sum_i S_i^2$ for the first $k$ components.

**Example:** `X=[[1,1],[2,2],[3,3]]`, `k=1` → components `[[0.7071, 0.7071]]`, projected `[[-1.414],[0],[1.414]]`, ratio `[1.0]`
""",
    starter='''import numpy as np

def pca(X, k):
    pass
''',
    solution='''import numpy as np

def pca(X, k):
    X = np.asarray(X, dtype=float)
    Xc = X - X.mean(axis=0)
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    for i in range(Vt.shape[0]):
        j = np.argmax(np.abs(Vt[i]))
        if Vt[i, j] < 0:
            Vt[i] = -Vt[i]
    comps = Vt[:k]
    var = S ** 2
    ratio = var[:k] / var.sum()
    return [comps, Xc @ comps.T, ratio]
''',
    tests=[
        [[[1, 1], [2, 2], [3, 3]], 1],
        [[[2, 0], [0, 1], [-2, 0], [0, -1]], 2],
        [[[1, 0, 0], [0, 3, 0], [0, 0, 0], [-1, -3, 0]], 1],
        [[[3, -3], [1, -1], [-2, 2], [-2, 2]], 1],
        [_corr(20, 3), 2],
        [_corr(30, 4), 3],
        [_corr(50, 5), 2],
        [_corr(15, 2), 2],
        [_corr(40, 6), 1],
        [[[0, 4], [0, -4], [1, 0], [-1, 0]], 2],
    ],
    wrong_solutions=[
        '''import numpy as np
def pca(X, k):
    X = np.asarray(X, float)
    U, S, Vt = np.linalg.svd(X, full_matrices=False)
    for i in range(Vt.shape[0]):
        j = np.argmax(np.abs(Vt[i]))
        if Vt[i, j] < 0: Vt[i] = -Vt[i]
    var = S ** 2
    return [Vt[:k], X @ Vt[:k].T, var[:k] / var.sum()]
''',
        '''import numpy as np
def pca(X, k):
    X = np.asarray(X, float); Xc = X - X.mean(0)
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    for i in range(Vt.shape[0]):
        j = np.argmax(np.abs(Vt[i]))
        if Vt[i, j] < 0: Vt[i] = -Vt[i]
    return [Vt[:k], Xc @ Vt[:k].T, S[:k] / S.sum()]
''',
    ],
    guide=dict(
        prereqs="Eigen/SVD intuition (Math, lesson 1); PCA (Unsupervised, lesson 2).",
        intuition=r"""PCA finds orthogonal directions of maximal variance. The covariance matrix is
$C=\frac{1}{n-1}X_c^\top X_c$; with $X_c=USV^\top$ we get $C = V\frac{S^2}{n-1}V^\top$ — so the right singular vectors are
the eigenvectors of $C$ and the variances along them are $S^2/(n-1)$. SVD avoids forming $C$, which is more accurate.""",
        hints=[
            "Centre first — PCA without centring finds directions through the origin, not through the data's mean.",
            "`np.linalg.svd(Xc, full_matrices=False)` returns singular values already sorted descending.",
            "Explained variance ratio uses squared singular values, not the singular values themselves.",
        ],
        brute_force="Eigen-decompose the covariance matrix (`np.linalg.eigh`) and sort eigenvalues descending — same answer, slightly less numerically stable.",
        approach=r"""1. `Xc = X - mean`.
2. `U, S, Vt = svd(Xc)`.
3. For each row of `Vt`, flip if its largest-|·| entry is negative.
4. Return `Vt[:k]`, `Xc @ Vt[:k].T`, `S[:k]**2 / sum(S**2)`.

Example: points on the line y = x; centred data is $(-1,-1),(0,0),(1,1)$; the single direction is $(1,1)/\sqrt2$ and it
explains 100% of variance.""",
        complexity="O(n·d·min(n,d)) for the SVD.",
        pitfalls=r"""- Forgetting to centre.
- Ratio from $S$ instead of $S^2$.
- Comparing signs with another library: scikit-learn uses its own `svd_flip` convention, so outputs can differ by a sign per component — that is why a deterministic rule is specified here.""",
        follow_up="Whitening (divide projections by $S/\\sqrt{n-1}$), reconstruction $\\hat X = Z V_k^T + \\bar x$, and choosing k by cumulative explained variance ≥ 95%.",
    ),
),

# ---------------------------------------------------------------- k-means step
dict(
    id="ml-kmeans-step",
    title="One Iteration of k-Means (Lloyd's Algorithm)",
    difficulty="Medium",
    pattern="Clustering",
    kind="function",
    entry="kmeans_step",
    compare="float",
    description=r"""
Perform one iteration of Lloyd's algorithm. Given points `X` ($n\times d$) and current `centroids` ($k\times d$):

1. **Assign** each point to the nearest centroid by Euclidean distance (ties → lower centroid index).
2. **Inertia** = sum of squared distances from each point to its assigned (current) centroid.
3. **Update** each centroid to the mean of its assigned points; a centroid with no points stays where it is.

Return `[labels, new_centroids, inertia]`.

**Example:** `X=[[0],[1],[10],[11]]`, `centroids=[[0],[5]]` → `[[0,0,1,1], [[0.5],[10.5]], 62.0]`
""",
    starter='''import numpy as np

def kmeans_step(X, centroids):
    pass
''',
    solution='''import numpy as np

def kmeans_step(X, centroids):
    X = np.asarray(X, dtype=float)
    C = np.asarray(centroids, dtype=float)
    d2 = ((X[:, None, :] - C[None, :, :]) ** 2).sum(axis=2)   # (n, k)
    labels = d2.argmin(axis=1)                                # first index on ties
    inertia = float(d2[np.arange(len(X)), labels].sum())
    newC = C.copy()
    for j in range(len(C)):
        m = labels == j
        if m.any():
            newC[j] = X[m].mean(axis=0)
    return [labels.tolist(), newC, inertia]
''',
    tests=[
        [[[0], [1], [10], [11]], [[0], [5]]],
        [[[0, 0], [0, 1], [5, 5], [5, 6]], [[0, 0], [5, 5]]],
        [[[0], [2]], [[1], [3]]],
        [[[0], [1], [2]], [[0], [100]]],
        [[[1, 1], [1, 1], [1, 1]], [[1, 1], [2, 2]]],
        [[[0, 0], [10, 0], [0, 10], [10, 10]], [[5, 5], [0, 0], [10, 10]]],
        [_blobs(30, 2, 3), [[0, 0], [1, 1], [-1, -1]]],
        [_blobs(60, 3, 4), _r(4, 3, scale=5)],
        [_blobs(100, 5, 5), _r(5, 5, scale=5)],
        [[[3]], [[0], [6]]],
    ],
    wrong_solutions=[
        '''import numpy as np
def kmeans_step(X, centroids):
    X = np.asarray(X, float); C = np.asarray(centroids, float)
    d2 = ((X[:, None] - C[None]) ** 2).sum(2); lab = d2.argmin(1)
    newC = np.array([X[lab == j].mean(0) if (lab == j).any() else np.zeros(X.shape[1]) for j in range(len(C))])
    return [lab.tolist(), newC, float(d2.min(1).sum())]
''',
        '''import numpy as np
def kmeans_step(X, centroids):
    X = np.asarray(X, float); C = np.asarray(centroids, float)
    d = np.sqrt(((X[:, None] - C[None]) ** 2).sum(2)); lab = d.argmin(1)
    newC = C.copy()
    for j in range(len(C)):
        if (lab == j).any(): newC[j] = X[lab == j].mean(0)
    return [lab.tolist(), newC, float(d.min(1).sum())]
''',
    ],
    guide=dict(
        prereqs="Distances (Math, lesson 1); k-means (Unsupervised, lesson 3).",
        intuition=r"""k-means alternates two steps that each can only decrease the inertia (within-cluster sum of squares):
assigning every point to its closest centre is optimal for fixed centres, and the mean is the point that minimises
total squared distance for a fixed assignment. So the algorithm converges — to a *local* optimum, which is why
scikit-learn runs it from several initialisations (`n_init`) with k-means++ seeding.""",
        hints=[
            "Distance matrix via broadcasting: (n,1,d) − (1,k,d) → (n,k,d).",
            "`argmin(axis=1)` already prefers the lower index on ties.",
            "Inertia uses squared distances to the *current* centroids, before the update.",
        ],
        brute_force="Loops over points and centroids: O(n·k·d), same as vectorised.",
        approach=r"""Example: distances² from [0],[1],[10],[11] to centroids 0 and 5 → labels 0,0,1,1, inertia
$0+1+25+36=62$. New centroids: mean(0,1)=0.5 and mean(10,11)=10.5.""",
        complexity="O(n·k·d) per iteration; memory O(n·k·d) for the broadcast (chunk for big data).",
        pitfalls=r"""- Moving an empty cluster to the origin (or producing NaN from the mean of nothing).
- Using non-squared distances for inertia.
- Forgetting that k-means needs scaled features and assumes roughly spherical, similarly sized clusters.""",
        follow_up="Loop until labels stop changing; implement k-means++ initialisation (sample next centre with probability ∝ D(x)²).",
    ),
),

# ---------------------------------------------------------------- one-hot
dict(
    id="ml-one-hot",
    title="One-Hot Encoding with Unknown Categories",
    difficulty="Easy",
    pattern="Feature Engineering",
    kind="function",
    entry="one_hot",
    compare="float",
    description=r"""
Mimic `OneHotEncoder(handle_unknown="ignore")` for a single categorical column.

- Learn the categories from `train_values` only: the **sorted** list of distinct values.
- Encode `test_values`: each row is a 0/1 vector with a 1 at the category's position; a category not seen in
  training becomes an **all-zero** row.

Return `[categories, matrix]`. Values are all strings or all integers.

**Example:** `train=["red","green","red"]`, `test=["green","blue","red"]` → `[["green","red"], [[1,0],[0,0],[0,1]]]`
""",
    starter='''import numpy as np

def one_hot(train_values, test_values):
    pass
''',
    solution='''import numpy as np

def one_hot(train_values, test_values):
    cats = sorted(set(train_values))
    pos = {c: i for i, c in enumerate(cats)}
    M = np.zeros((len(test_values), len(cats)), dtype=int)
    for r, v in enumerate(test_values):
        if v in pos:
            M[r, pos[v]] = 1
    return [cats, M.tolist()]
''',
    tests=[
        [["red", "green", "red"], ["green", "blue", "red"]],
        [[3, 1, 2], [1, 2, 3, 4]],
        [["a"], ["a", "a", "b"]],
        [["x", "y"], []],
        [["Male", "Female", "female"], ["female", "Female", "male"]],
        [[10, 2, 33], [2, 10]],
        [["b", "a", "c", "a"], ["c", "b", "a"]],
        [["cat", "dog", "fish", "dog"], ["bird", "bird"]],
        [[0, 1], [1, 0, 1, 0, 1]],
        [["NY", "SF", "LA", "NY", "SF"], ["LA", "NY", "SF", "TX"]],
    ],
    wrong_solutions=[
        '''def one_hot(train_values, test_values):
    cats = list(dict.fromkeys(train_values))
    return [cats, [[int(v == c) for c in cats] for v in test_values]]
''',
        '''def one_hot(train_values, test_values):
    cats = sorted(set(train_values) | set(test_values))
    return [cats, [[int(v == c) for c in cats] for v in test_values]]
''',
    ],
    guide=dict(
        prereqs="Categorical features (Feature engineering, lesson 1).",
        intuition=r"""Linear models multiply features by weights, so encoding `red=0, green=1, blue=2` would invent an order and a
distance (blue is "twice" green). One-hot encoding gives each category its own binary column and its own weight.
The category list must be fixed at training time; otherwise the train and test matrices would have different columns.""",
        hints=[
            "`sorted(set(train_values))` gives the column order.",
            "A dict from category to column index makes encoding O(1) per value.",
            "Unknown test values: leave the row all zeros instead of raising an error.",
        ],
        brute_force="Comparing every value with every category: O(n·C). Fine for small C.",
        approach=r"""1. Categories = sorted distinct train values.
2. Allocate an n_test × C zero matrix; set M[r, pos[v]] = 1 for known values.

Example: categories ["green","red"]; "blue" is unseen → [0,0].""",
        complexity="O(n log n) to sort categories, O(n_test) to encode (O(n_test·C) to allocate the dense matrix).",
        pitfalls=r"""- Deriving categories from train ∪ test (pandas `get_dummies` on each split separately is a classic bug).
- Case/whitespace variants ("Male" vs "male") are different categories — clean the data first, as Müller & Guido stress.
- With an intercept, the full one-hot block is collinear; `drop="first"` removes the redundancy for unregularised linear models.""",
        follow_up="Handle high-cardinality features with hashing or target encoding (with out-of-fold statistics to avoid leakage).",
    ),
),
]
