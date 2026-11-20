import numpy as _np

_rng = _np.random.RandomState(5)


def _bin(n, p=0.5):
    return [int(v) for v in (_rng.rand(n) < p)]


def _noisy_pred(y, flip=0.2):
    return [1 - v if _rng.rand() < flip else v for v in y]


PROBLEMS = [
# ---------------------------------------------------------------- k-fold
dict(
    id="ml-kfold-indices",
    title="K-Fold Cross-Validation Indices",
    difficulty="Easy",
    pattern="Model Evaluation",
    kind="function",
    entry="kfold_indices",
    compare="float",
    description=r"""
Reproduce `sklearn.model_selection.KFold(n_splits=k, shuffle=False)`. The `n` samples (indices `0..n-1`, in
order) are cut into `k` consecutive folds; the **first `n % k` folds get one extra sample**. For each fold, return
`[train_indices, test_indices]` where the test indices are the fold and the train indices are everything else in
ascending order. Return the list of `k` pairs. $2 \le k \le n$.

**Example:** `n=5, k=2` → `[[[3,4],[0,1,2]], [[0,1,2],[3,4]]]`
""",
    starter='''import numpy as np

def kfold_indices(n, k):
    pass
''',
    solution='''import numpy as np

def kfold_indices(n, k):
    sizes = np.full(k, n // k)
    sizes[: n % k] += 1
    idx = np.arange(n)
    out, start = [], 0
    for s in sizes:
        test = idx[start:start + s]
        train = np.concatenate([idx[:start], idx[start + s:]])
        out.append([train.tolist(), test.tolist()])
        start += s
    return out
''',
    tests=[[5, 2], [6, 3], [10, 3], [2, 2], [7, 7], [11, 4], [100, 5], [13, 5], [9, 2], [150, 10]],
    wrong_solutions=[
        '''def kfold_indices(n, k):
    size = n // k; out = []
    for f in range(k):
        s = f * size; e = n if f == k - 1 else s + size
        out.append([list(range(0, s)) + list(range(e, n)), list(range(s, e))])
    return out
''',
    ],
    guide=dict(
        prereqs="Cross-validation (Model evaluation, lesson 1).",
        intuition=r"""k-fold CV uses every sample for testing exactly once and for training k−1 times. The fold sizes differ by at most
one. Note that **without shuffling**, sorted data (like iris, ordered by class) gives terrible folds — which is why
scikit-learn uses *stratified* k-fold by default for classifiers.""",
        hints=[
            "Base size n // k; the first n % k folds get +1.",
            "Keep a running start offset.",
            "Train = indices before the fold + indices after it.",
        ],
        brute_force="Assign fold ids with a list and filter: O(n·k) — fine.",
        approach=r"""n=5,k=2: sizes [3,2]. Fold 0 test [0,1,2], train [3,4]; fold 1 test [3,4], train [0,1,2].""",
        complexity="O(n·k) total output size.",
        pitfalls=r"""- Putting the remainder in the last fold (scikit-learn front-loads it).
- Forgetting that iris-like sorted data needs shuffling or stratification.
- Group leakage: if several rows belong to the same patient/user, use `GroupKFold`.""",
        follow_up="StratifiedKFold (split each class separately), TimeSeriesSplit (train always precedes test), leave-one-out (k = n).",
    ),
),

# ---------------------------------------------------------------- confusion matrix
dict(
    id="ml-confusion-matrix",
    title="Multiclass Confusion Matrix",
    difficulty="Easy",
    pattern="Model Evaluation",
    kind="function",
    entry="confusion_matrix",
    compare="float",
    description=r"""
Given `y_true` and `y_pred` (same length $\ge1$, integer or string labels), return `[labels, M]` where `labels` is
the **sorted union** of labels appearing in either list and `M[i][j]` counts samples whose **true** label is
`labels[i]` and whose **predicted** label is `labels[j]` (rows = truth, columns = prediction — scikit-learn's convention).

**Example:** `y_true=[0,1,1,2]`, `y_pred=[0,1,2,2]` → `[[0,1,2], [[1,0,0],[0,1,1],[0,0,1]]]`
""",
    starter='''import numpy as np

def confusion_matrix(y_true, y_pred):
    pass
''',
    solution='''import numpy as np

def confusion_matrix(y_true, y_pred):
    labels = sorted(set(y_true) | set(y_pred))
    pos = {l: i for i, l in enumerate(labels)}
    M = np.zeros((len(labels), len(labels)), dtype=int)
    for t, p in zip(y_true, y_pred):
        M[pos[t], pos[p]] += 1
    return [labels, M.tolist()]
''',
    tests=[
        [[0, 1, 1, 2], [0, 1, 2, 2]],
        [[1, 1, 1], [1, 1, 1]],
        [[0, 0, 1, 1], [1, 1, 0, 0]],
        [["cat", "dog", "cat"], ["dog", "dog", "cat"]],
        [[0, 1], [2, 3]],
        [[1, 0, 1, 0, 1], [1, 1, 1, 0, 0]],
        [[3, 1, 2], [1, 2, 3]],
        [[int(v) for v in _rng.randint(0, 4, 50)], [int(v) for v in _rng.randint(0, 4, 50)]],
        [[int(v) for v in _rng.randint(0, 10, 300)], [int(v) for v in _rng.randint(0, 10, 300)]],
        [["b", "a"], ["a", "a"]],
    ],
    wrong_solutions=[
        '''def confusion_matrix(y_true, y_pred):
    labels = sorted(set(y_true) | set(y_pred)); pos = {l: i for i, l in enumerate(labels)}
    M = [[0] * len(labels) for _ in labels]
    for t, p in zip(y_true, y_pred): M[pos[p]][pos[t]] += 1
    return [labels, M]
''',
        '''def confusion_matrix(y_true, y_pred):
    labels = sorted(set(y_true)); pos = {l: i for i, l in enumerate(labels)}
    M = [[0] * len(labels) for _ in labels]
    for t, p in zip(y_true, y_pred):
        if p in pos: M[pos[t]][pos[p]] += 1
    return [labels, M]
''',
    ],
    guide=dict(
        prereqs="Metrics for classification (Model evaluation, lesson 3).",
        intuition=r"""The confusion matrix is the full story of a classifier's mistakes; every other classification metric
(accuracy, precision, recall, F1) is a summary of it. The diagonal holds correct predictions; off-diagonal entry (i, j)
tells you *which* class gets confused with which.""",
        hints=["Build a label → index dict.", "Rows index the truth, columns the prediction.", "Labels that only appear in predictions still need a row and column."],
        brute_force="For each pair of labels, count matching samples: O(C²·n).",
        approach=r"""One pass: `M[pos[t], pos[p]] += 1`. For the example, the sample with truth 1 predicted 2 lands in row 1, column 2.""",
        complexity="O(n + C²) time and O(C²) space.",
        pitfalls=r"""- Transposing the matrix (some textbooks put predictions in rows!).
- Missing labels that only occur in `y_pred`.""",
        follow_up="Normalise rows to get per-class recall; `np.bincount(C*t + p, minlength=C*C).reshape(C, C)` is a fully vectorised trick.",
    ),
),

# ---------------------------------------------------------------- precision/recall/F1
dict(
    id="ml-precision-recall-f1",
    title="Precision, Recall, F1 and Accuracy",
    difficulty="Easy",
    pattern="Model Evaluation",
    kind="function",
    entry="binary_scores",
    compare="float",
    description=r"""
For binary labels (1 = positive class), return `[precision, recall, f1, accuracy]`:

$$P=\frac{TP}{TP+FP},\quad R=\frac{TP}{TP+FN},\quad F_1=\frac{2PR}{P+R},\quad \text{acc}=\frac{TP+TN}{n}.$$

Whenever a denominator is 0, the corresponding metric is 0 (scikit-learn's `zero_division=0`).

**Example:** `y_true=[1,1,0,0]`, `y_pred=[1,0,1,0]` → `[0.5, 0.5, 0.5, 0.5]`
""",
    starter='''import numpy as np

def binary_scores(y_true, y_pred):
    pass
''',
    solution='''import numpy as np

def binary_scores(y_true, y_pred):
    t = np.asarray(y_true) == 1
    p = np.asarray(y_pred) == 1
    tp = int((t & p).sum()); fp = int((~t & p).sum()); fn = int((t & ~p).sum())
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    acc = float((t == p).mean())
    return [prec, rec, f1, acc]
''',
    tests=[
        [[1, 1, 0, 0], [1, 0, 1, 0]],
        [[1, 1, 1], [1, 1, 1]],
        [[0, 0, 0], [0, 0, 0]],
        [[1, 0, 0, 0], [0, 0, 0, 0]],
        [[0, 0, 0, 0], [1, 0, 0, 0]],
        [[1, 1, 1, 1, 0], [1, 0, 0, 0, 0]],
        [[1, 0, 1, 0, 1, 0, 0, 0, 0, 0], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]],
        (lambda y: [y, _noisy_pred(y, 0.2)])(_bin(100, 0.1)),
        (lambda y: [y, _noisy_pred(y, 0.4)])(_bin(500, 0.5)),
        [[1], [0]],
    ],
    wrong_solutions=[
        '''def binary_scores(y_true, y_pred):
    tp = sum(t == 1 and p == 1 for t, p in zip(y_true, y_pred))
    fp = sum(t == 0 and p == 1 for t, p in zip(y_true, y_pred))
    fn = sum(t == 1 and p == 0 for t, p in zip(y_true, y_pred))
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = (prec + rec) / 2
    acc = sum(t == p for t, p in zip(y_true, y_pred)) / len(y_true)
    return [prec, rec, f1, acc]
''',
        '''def binary_scores(y_true, y_pred):
    tp = sum(t == 1 and p == 1 for t, p in zip(y_true, y_pred))
    fp = sum(t == 0 and p == 1 for t, p in zip(y_true, y_pred))
    fn = sum(t == 1 and p == 0 for t, p in zip(y_true, y_pred))
    prec = tp / (tp + fn) if tp + fn else 0.0
    rec = tp / (tp + fp) if tp + fp else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    acc = sum(t == p for t, p in zip(y_true, y_pred)) / len(y_true)
    return [prec, rec, f1, acc]
''',
    ],
    guide=dict(
        prereqs="Confusion matrix (previous problem); metrics lesson.",
        intuition=r"""Precision answers "when the model says positive, how often is it right?" (cost of false alarms).
Recall answers "of all actual positives, how many did we catch?" (cost of misses). F1 is their **harmonic** mean,
which is dragged down by whichever is smaller — a model with P=1.0 and R=0.01 has F1≈0.02, not 0.5.""",
        hints=["Count TP, FP, FN with boolean masks.", "Guard each division.", "F1 = 2PR/(P+R), not the arithmetic mean."],
        brute_force="A single loop counting the four cells is already optimal.",
        approach=r"""Example: TP=1 (index 0), FN=1 (index 1), FP=1 (index 2), TN=1 → P=R=F1=acc=0.5.
Test 7 shows why accuracy misleads on imbalance: predicting all-ones gives recall 1 but precision 0.3.""",
        complexity="O(n).",
        pitfalls=r"""- Swapping precision and recall (FP vs FN in the denominator).
- Arithmetic instead of harmonic mean.
- Division by zero when the model never predicts positive.""",
        follow_up="F-beta: $F_\\beta = (1+\\beta^2)PR/(\\beta^2 P + R)$; macro vs micro vs weighted averaging for multiclass.",
    ),
),

# ---------------------------------------------------------------- ROC AUC
dict(
    id="ml-roc-auc",
    title="ROC AUC from Scores",
    difficulty="Medium",
    pattern="Model Evaluation",
    kind="function",
    entry="roc_auc",
    compare="float",
    description=r"""
Given binary labels `y_true` (containing at least one 0 and one 1) and real-valued `scores` (higher = more likely
positive), return the area under the ROC curve. Equivalently, AUC is the probability that a randomly chosen positive
gets a higher score than a randomly chosen negative, **counting ties as 1/2**:

$$\text{AUC} = \frac{1}{n_+ n_-}\sum_{i\in +}\sum_{j\in -}\Big(\mathbb 1[s_i>s_j]+\tfrac12\mathbb 1[s_i=s_j]\Big).$$

This must match `sklearn.metrics.roc_auc_score`. Aim for $O(n\log n)$.

**Example:** `y_true=[0,0,1,1]`, `scores=[0.1,0.4,0.35,0.8]` → `0.75`
""",
    starter='''import numpy as np

def roc_auc(y_true, scores):
    pass
''',
    solution='''import numpy as np

def _avg_ranks(s):
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s), dtype=float)
    ss = s[order]
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and ss[j + 1] == ss[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0     # average 1-based rank
        i = j + 1
    return ranks

def roc_auc(y_true, scores):
    y = np.asarray(y_true) == 1
    s = np.asarray(scores, dtype=float)
    r = _avg_ranks(s)
    n_pos, n_neg = y.sum(), (~y).sum()
    # Mann-Whitney U statistic
    u = r[y].sum() - n_pos * (n_pos + 1) / 2.0
    return float(u / (n_pos * n_neg))
''',
    tests=[
        [[0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8]],
        [[0, 1], [0.2, 0.9]],
        [[0, 1], [0.9, 0.2]],
        [[0, 1], [0.5, 0.5]],
        [[1, 0, 1, 0], [1, 1, 1, 1]],
        [[0, 0, 1, 1, 0, 1], [0.1, 0.5, 0.5, 0.9, 0.5, 0.1]],
        [[1, 1, 0], [3, 3, 3]],
        (lambda y: [y, [round(float(v + 0.8 * t), 1) for v, t in zip(_rng.rand(200), y)]])(_bin(200, 0.3)),
        (lambda y: [y, [round(float(v), 2) for v in _rng.rand(1000)]])(_bin(1000, 0.5)),
        (lambda y: [y, [float(v + t) for v, t in zip(_rng.randn(300), y)]])(_bin(300, 0.2)),
    ],
    wrong_solutions=[
        '''import numpy as np
def roc_auc(y_true, scores):
    y = np.asarray(y_true) == 1; s = np.asarray(scores, float)
    pos, neg = s[y], s[~y]
    return float((pos[:, None] > neg[None, :]).mean())
''',
        '''import numpy as np
def roc_auc(y_true, scores):
    y = np.asarray(y_true) == 1; s = np.asarray(scores, float)
    r = np.argsort(np.argsort(s)) + 1.0
    n1, n0 = y.sum(), (~y).sum()
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))
''',
    ],
    guide=dict(
        prereqs="ROC curves (Model evaluation, lesson 3).",
        intuition=r"""The ROC curve plots true-positive rate against false-positive rate as the decision threshold sweeps from +∞ to −∞.
Its area has a beautiful interpretation: the chance a random positive is ranked above a random negative. It depends
only on the **ranking** of scores, so it is insensitive to class imbalance in its definition and to any monotone
rescaling of scores. 0.5 = random ranking, 1.0 = perfect.""",
        hints=[
            "The pairwise O(n₊·n₋) definition is a correct (slow) reference — handle ties as 1/2.",
            "Sort scores and compute ranks; tied scores share the average of their ranks.",
            "Mann–Whitney: U = (sum of positive ranks) − n₊(n₊+1)/2; AUC = U/(n₊n₋).",
        ],
        brute_force=r"Compare every positive with every negative: `((pos[:,None] > neg) + 0.5*(pos[:,None]==neg)).mean()`. O(n₊n₋) time and memory.",
        approach=r"""Rank all scores (1 = smallest) with average ranks for ties. The sum of positive ranks counts, for each positive,
how many items are at or below it; subtracting $n_+(n_++1)/2$ removes positive-vs-positive comparisons, leaving the number of
(positive, negative) pairs ordered correctly (ties contribute 1/2 through averaged ranks).

Example: scores sorted 0.1(−), 0.35(+), 0.4(−), 0.8(+) → positive ranks 2 and 4, sum 6, minus 3 = 3, divided by 2·2 → 0.75.""",
        complexity="O(n log n) for the sort.",
        pitfalls=r"""- Ignoring ties (strict >) undercounts.
- `argsort(argsort(s))` assigns *distinct* ranks to ties — wrong for tied scores.
- Passing hard 0/1 predictions instead of scores collapses the ROC curve to a single point.""",
        follow_up="Build the full ROC curve (FPR, TPR at each distinct threshold) and integrate it with the trapezoid rule — you'll get the same number.",
    ),
),
]
