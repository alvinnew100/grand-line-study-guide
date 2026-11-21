import math as _math
import random as _random

_r = _random.Random(505)


def _scores(n, sep):
    y = [1 if _r.random() < 0.2 else 0 for _ in range(n)]
    s = [round(_r.gauss(sep * t, 1.0), 3) for t in y]
    return y, s


_y1, _s1 = _scores(300, 1.2)
_y2, _s2 = _scores(2000, 0.5)


def _logit_data(n, b, seed):
    rr = _random.Random(seed)
    X, y = [], []
    for _ in range(n):
        x = [round(rr.gauss(0, 1), 3) for _ in b[1:]]
        z = b[0] + sum(c * v for c, v in zip(b[1:], x))
        X.append(x)
        y.append(1 if rr.random() < 1 / (1 + _math.exp(-z)) else 0)
    return X, y


_LX1, _Ly1 = _logit_data(400, [0.5, 1.2], 1)
_LX2, _Ly2 = _logit_data(800, [-1.0, 0.8, -0.5, 0.3], 2)

PROBLEMS = [
# ---------------------------------------------------------------- confusion metrics
dict(
    id="stats-confusion-metrics",
    title="Confusion-Matrix Metrics at a Threshold",
    difficulty="Easy",
    pattern="Classification Metrics",
    kind="function",
    entry="metrics_at",
    compare="float",
    description=r"""
Predict 1 when `score >= threshold`, else 0. Compare with the true 0/1 labels and return
`[precision, recall, specificity, f1, accuracy]`:

- precision = TP / (TP + FP), recall = TP / (TP + FN), specificity = TN / (TN + FP),
- f1 = 2·precision·recall / (precision + recall), accuracy = (TP + TN) / n.

Whenever a denominator is 0, that metric is `0.0`.

**Example:** `y_true = [1, 0, 1, 1, 0, 0, 0, 1], scores = [0.9, 0.8, 0.7, 0.3, 0.2, 0.6, 0.1, 0.55], threshold = 0.5`
→ TP 3, FP 2, FN 1, TN 2 → `[0.6, 0.75, 0.5, 0.6666667, 0.625]`
""",
    starter='''def metrics_at(y_true, scores, threshold):
    pass
''',
    solution='''def metrics_at(y_true, scores, threshold):
    tp = fp = fn = tn = 0
    for t, s in zip(y_true, scores):
        p = 1 if s >= threshold else 0
        if p and t:
            tp += 1
        elif p and not t:
            fp += 1
        elif t:
            fn += 1
        else:
            tn += 1
    div = lambda a, b: a / b if b else 0.0
    prec, rec, spec = div(tp, tp + fp), div(tp, tp + fn), div(tn, tn + fp)
    f1 = div(2 * prec * rec, prec + rec)
    return [prec, rec, spec, f1, (tp + tn) / len(y_true)]
''',
    tests=[
        [[1, 0, 1, 1, 0, 0, 0, 1], [0.9, 0.8, 0.7, 0.3, 0.2, 0.6, 0.1, 0.55], 0.5],
        [[1, 0, 1, 1, 0, 0, 0, 1], [0.9, 0.8, 0.7, 0.3, 0.2, 0.6, 0.1, 0.55], 0.95],
        [[1, 0, 1, 1, 0, 0, 0, 1], [0.9, 0.8, 0.7, 0.3, 0.2, 0.6, 0.1, 0.55], 0.0],
        [[0, 0, 0], [0.1, 0.4, 0.2], 0.3],
        [[1, 1], [0.5, 0.49], 0.5],
        [_y1, _s1, 0.6],
        [_y2, _s2, 0.0],
    ],
    examples=2,
    wrong_solutions=[
        '''def metrics_at(y_true, scores, threshold):
    tp = fp = fn = tn = 0
    for t, s in zip(y_true, scores):
        p = 1 if s > threshold else 0
        tp += p and t; fp += p and not t; fn += (not p) and t; tn += (not p) and not t
    div = lambda a, b: a / b if b else 0.0
    prec, rec, spec = div(tp, tp + fp), div(tp, tp + fn), div(tn, tn + fp)
    return [prec, rec, spec, div(2 * prec * rec, prec + rec), (tp + tn) / len(y_true)]
''',
        '''def metrics_at(y_true, scores, threshold):
    tp = fp = fn = tn = 0
    for t, s in zip(y_true, scores):
        p = 1 if s >= threshold else 0
        tp += p and t; fp += p and not t; fn += (not p) and t; tn += (not p) and not t
    div = lambda a, b: a / b if b else 0.0
    prec, rec = div(tp, tp + fp), div(tp, tp + fn)
    return [prec, rec, div(tn, tn + fn), (prec + rec) / 2, (tp + tn) / len(y_true)]
''',
    ],
    guide=dict(
        prereqs="Confusion matrix and its metrics (lesson *Evaluating classifiers and handling rare classes*).",
        intuition=r"""Every prediction lands in one of four cells. Precision asks "when we flag, are we right?", recall asks "of the real
positives, how many do we catch?", specificity asks "of the real negatives, how many do we leave alone?". F1 is the
harmonic mean of precision and recall, high only when both are.""",
        hints=[
            "Count TP, FP, FN, TN in one pass.",
            "The threshold rule is score >= threshold (inclusive).",
            "Guard every division against a zero denominator.",
        ],
        brute_force="sklearn.metrics functions give each metric; this problem asks you to build them from counts.",
        approach=r"""Example: predictions at 0.5 are 1, 1, 1, 0, 0, 1, 0, 1 → TP 3 (rows 0, 2, 7), FP 2 (rows 1, 5), FN 1 (row 3),
TN 2. Precision 3/5, recall 3/4, specificity 2/4, F1 = 2 × 0.6 × 0.75 / 1.35 = 0.667, accuracy 5/8.""",
        complexity="O(n).",
        pitfalls=r"""- Using > instead of >= at the threshold.
- Confusing specificity (TN/(TN + FP)) with the negative predictive value (TN/(TN + FN)).
- Arithmetic mean instead of harmonic mean for F1.""",
        follow_up="Sweep thresholds and pick the one maximising expected value given a cost per false positive and a benefit per true positive.",
    ),
),

# ---------------------------------------------------------------- AUC
dict(
    id="stats-auc-ranking",
    title="ROC AUC by Ranking",
    difficulty="Medium",
    pattern="Classification Metrics",
    kind="function",
    entry="auc",
    compare="float",
    description=r"""
Return the ROC AUC of `scores` for true 0/1 labels `y_true`: the probability that a randomly chosen positive has a
higher score than a randomly chosen negative, counting ties as one half:

$$AUC = \frac{\#\{(i, j): s_i > s_j\} + \tfrac12\#\{(i, j): s_i = s_j\}}{n_+ \, n_-}$$

over all pairs of a positive `i` and a negative `j`. Aim for $O(n \log n)$ using average ranks (the Mann-Whitney
form): $AUC = \dfrac{R_+ - n_+(n_+ + 1)/2}{n_+ n_-}$ where $R_+$ is the sum of the positives' ranks.

Constraints: at least one positive and one negative; `n <= 10^5`.

**Example:** `y_true = [0, 0, 1, 1], scores = [0.1, 0.4, 0.35, 0.8]` → `0.75`

**Example:** `y_true = [1, 0], scores = [0.5, 0.5]` → `0.5`
""",
    starter='''def auc(y_true, scores):
    pass
''',
    solution='''def auc(y_true, scores):
    n = len(scores)
    order = sorted(range(n), key=lambda i: scores[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and scores[order[j + 1]] == scores[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    n_pos = sum(1 for t in y_true if t == 1)
    n_neg = n - n_pos
    r_pos = sum(r for r, t in zip(ranks, y_true) if t == 1)
    return (r_pos - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)
''',
    tests=[
        [[0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8]],
        [[1, 0], [0.5, 0.5]],
        [[1, 1, 0, 0], [0.9, 0.8, 0.2, 0.1]],
        [[1, 1, 0, 0], [0.1, 0.2, 0.8, 0.9]],
        [[1, 0, 1, 0, 1], [3, 3, 3, 1, 2]],
        [[0, 1, 0, 1, 0, 1], [1, 1, 2, 2, 3, 3]],
        [_y1, _s1],
        [_y2, _s2],
        [[1] * 10000 + [0] * 10000, [round(_r.random(), 2) for _ in range(20000)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def auc(y_true, scores):
    pos = [s for s, t in zip(scores, y_true) if t == 1]
    neg = [s for s, t in zip(scores, y_true) if t == 0]
    wins = sum(1 for p in pos for q in neg if p > q)
    return wins / (len(pos) * len(neg))
''',
    ],
    guide=dict(
        prereqs="ROC curves and AUC as a ranking probability (lesson *Evaluating classifiers and handling rare classes*).",
        intuition=r"""AUC only cares about order. Rank all scores; if positives tend to have high ranks, AUC is high. The sum of the
positives' ranks, minus the smallest possible sum n₊(n₊ + 1)/2, counts how many (positive, negative) pairs the
positives win, with ties counted as half.""",
        hints=[
            "Sort indices by score and assign average ranks to tied scores.",
            "Sum the ranks of the positives.",
            "AUC = (R₊ − n₊(n₊ + 1)/2) / (n₊ · n₋).",
        ],
        brute_force="Compare every positive with every negative: O(n₊·n₋), slow for 20,000 records (100 million pairs).",
        approach=r"""Example: scores sorted 0.1 (neg), 0.35 (pos), 0.4 (neg), 0.8 (pos) → positive ranks 2 and 4, R₊ = 6;
(6 − 3) / (2 × 2) = 0.75. Pairwise check: (0.35 > 0.1), (0.35 < 0.4), (0.8 > both) → 3 of 4 pairs.""",
        complexity="O(n log n) time, O(n) space.",
        pitfalls=r"""- Ignoring ties (they count one half, and need average ranks).
- Quadratic pairwise loops on large inputs.
- Integer division in other languages.""",
        follow_up="Compute the full ROC curve (true and false positive rates at each distinct threshold) and integrate it with the trapezoid rule; the area matches.",
    ),
),

# ---------------------------------------------------------------- log-loss
dict(
    id="stats-logloss",
    title="Logistic Predictions and Log-Loss",
    difficulty="Easy",
    pattern="Logistic Regression",
    kind="function",
    entry="log_loss",
    compare="float",
    description=r"""
A logistic regression has coefficients `coefs = [b0, b1, ..., bp]`. For each row `x` of `X` the predicted probability is
$p = 1/(1 + e^{-(b_0 + b_1 x_1 + \dots + b_p x_p)})$. Clip each $p$ into `[1e-15, 1 - 1e-15]` and return the average
**log-loss** (negative log-likelihood per record):

$$\text{log-loss} = -\frac1n \sum_i \big[y_i \log p_i + (1 - y_i)\log(1 - p_i)\big]$$

**Example:** `X = [[0], [1], [2]], y = [0, 1, 1], coefs = [-1, 2]` → `0.2250369`

**Example:** `X = [[5]], y = [0], coefs = [0, 0]` → `0.6931472` (a probability of 0.5)
""",
    starter='''import math

def log_loss(X, y, coefs):
    pass
''',
    solution='''import math

def log_loss(X, y, coefs):
    total = 0.0
    for row, t in zip(X, y):
        z = coefs[0] + sum(c * v for c, v in zip(coefs[1:], row))
        if z >= 0:
            p = 1 / (1 + math.exp(-z))
        else:
            ez = math.exp(z)
            p = ez / (1 + ez)
        p = min(max(p, 1e-15), 1 - 1e-15)
        total += t * math.log(p) + (1 - t) * math.log(1 - p)
    return -total / len(y)
''',
    tests=[
        [[[0], [1], [2]], [0, 1, 1], [-1, 2]],
        [[[5]], [0], [0, 0]],
        [[[10], [-10]], [1, 0], [0, 3]],
        [[[10], [-10]], [0, 1], [0, 3]],
        [[[1000]], [1], [0, 1]],
        [[[-1000]], [1], [0, 1]],
        [[[0.5, -1.0], [1.5, 2.0], [-0.3, 0.2]], [1, 0, 1], [0.1, 0.8, -0.6]],
        [_LX1, _Ly1, [0.5, 1.2]],
        [_LX2, _Ly2, [-1.0, 0.8, -0.5, 0.3]],
    ],
    examples=2,
    wrong_solutions=[
        '''import math

def log_loss(X, y, coefs):
    total = 0.0
    for row, t in zip(X, y):
        z = coefs[0] + sum(c * v for c, v in zip(coefs[1:], row))
        p = 1 / (1 + math.exp(-z))
        total += (t - p) ** 2
    return total / len(y)
''',
    ],
    guide=dict(
        prereqs="The logistic function, likelihood and log-loss (lesson *Logistic regression: odds, log-odds and maximum likelihood*).",
        intuition=r"""Log-loss rewards confident correct probabilities and punishes confident mistakes severely: predicting 0.001 for an
event that happens costs log(1000) ≈ 6.9. Minimising it is exactly maximum likelihood for logistic regression.""",
        hints=[
            "Linear score z = b0 + Σ b_j x_j, then p = sigmoid(z).",
            "Avoid overflow for very negative z: compute exp(z)/(1 + exp(z)) instead of 1/(1 + exp(−z)).",
            "Clip p before taking logs so log(0) never happens.",
        ],
        brute_force="sklearn.metrics.log_loss on the probabilities gives the same answer (it also clips).",
        approach=r"""Example: z = −1, 1, 3 → p = 0.2689, 0.7311, 0.9526. The first label is 0, so its loss is −log(1 − 0.2689) =
0.3133; the others are −log(0.7311) = 0.3133 and −log(0.9526) = 0.0486. Mean = 0.6751 / 3 = 0.2250.""",
        complexity="O(n·p).",
        pitfalls=r"""- math.exp overflow for z around −1000 (OverflowError).
- Not clipping, giving log(0) = −infinity.
- Returning the sum instead of the mean, or forgetting the minus sign.""",
        follow_up="Compute the gradient Xᵀ(p − y)/n and take a gradient-descent step; repeat to fit the model.",
    ),
),

# ---------------------------------------------------------------- naive Bayes
dict(
    id="stats-naive-bayes-counts",
    title="Categorical Naive Bayes with Laplace Smoothing",
    difficulty="Medium",
    pattern="Naive Bayes",
    kind="function",
    entry="nb_posterior",
    compare="float",
    description=r"""
Training data `X` (rows of categorical values) has 0/1 labels `y`. Return $P(y = 1 \mid x_\text{new})$ under naive Bayes:

- prior $P(c) = n_c / n$ (no smoothing),
- for feature `j` with $K_j$ distinct values **in the training data**,
  $P(x_j = v \mid c) = \dfrac{\text{count}(x_j = v, y = c) + \alpha}{n_c + \alpha K_j}$ (a value never seen in training
  gets count 0),
- score $s_c = P(c)\prod_j P(x_{\text{new},j} \mid c)$, and the answer is $s_1 / (s_0 + s_1)$; if both scores are 0,
  return `0.5`.

Constraints: both classes appear in `y`; `alpha >= 0`.

**Example:** emails with features (link, caps, known sender), `alpha = 0`, see the first test → `0.1428571`.
""",
    starter='''def nb_posterior(X, y, x_new, alpha):
    pass
''',
    solution='''def nb_posterior(X, y, x_new, alpha):
    n, p = len(X), len(X[0])
    scores = {}
    for c in (0, 1):
        rows = [r for r, t in zip(X, y) if t == c]
        nc = len(rows)
        s = nc / n
        for j in range(p):
            K = len({r[j] for r in X})
            cnt = sum(1 for r in rows if r[j] == x_new[j])
            s *= (cnt + alpha) / (nc + alpha * K)
        scores[c] = s
    total = scores[0] + scores[1]
    return 0.5 if total == 0 else scores[1] / total
''',
    tests=[
        [[["yes", "yes", "no"], ["yes", "no", "no"], ["no", "yes", "no"], ["yes", "yes", "no"], ["no", "no", "yes"],
          ["no", "no", "yes"], ["yes", "yes", "no"], ["no", "no", "yes"], ["yes", "no", "yes"], ["no", "no", "yes"],
          ["no", "yes", "yes"], ["yes", "yes", "yes"]],
         [1, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1], ["yes", "no", "yes"], 0],
        [[["yes", "yes", "no"], ["yes", "no", "no"], ["no", "yes", "no"], ["yes", "yes", "no"], ["no", "no", "yes"],
          ["no", "no", "yes"], ["yes", "yes", "no"], ["no", "no", "yes"], ["yes", "no", "yes"], ["no", "no", "yes"],
          ["no", "yes", "yes"], ["yes", "yes", "yes"]],
         [1, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1], ["yes", "no", "no"], 1],
        [[[1, 1, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0], [0, 0, 1], [0, 0, 1], [1, 1, 0], [0, 0, 1], [1, 0, 1], [0, 0, 1],
          [0, 1, 1], [1, 1, 1]], [1, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1], [1, 0, 0], 0],
        [[["a"], ["b"], ["a"], ["c"]], [0, 0, 1, 1], ["d"], 1],
        [[["a"], ["b"], ["a"], ["c"]], [0, 0, 1, 1], ["d"], 0],
        [[["red", "s"], ["red", "m"], ["blue", "s"], ["blue", "l"], ["green", "m"], ["red", "l"]],
         [1, 1, 0, 0, 1, 0], ["red", "s"], 0.5],
        [[[_r.choice("abc"), _r.choice("xy"), _r.choice("pqrs")] for _ in range(300)],
         [_r.randint(0, 1) for _ in range(300)], ["a", "y", "s"], 1],
    ],
    examples=2,
    wrong_solutions=[
        '''def nb_posterior(X, y, x_new, alpha):
    n, p = len(X), len(X[0])
    scores = {}
    for c in (0, 1):
        rows = [r for r, t in zip(X, y) if t == c]
        nc = len(rows)
        s = nc / n
        for j in range(p):
            cnt = sum(1 for r in rows if r[j] == x_new[j])
            s *= (cnt + alpha) / (nc + alpha)
        scores[c] = s
    total = scores[0] + scores[1]
    return 0.5 if total == 0 else scores[1] / total
''',
    ],
    guide=dict(
        prereqs="Naive Bayes, conditional independence and Laplace smoothing (lesson *Naive Bayes and discriminant analysis*).",
        intuition=r"""Assume features are independent within each class, so the class's likelihood is a product of one-feature
frequencies. Smoothing adds alpha imaginary records of every value, so a value never seen with a class cannot force
that class's probability to exactly zero.""",
        hints=[
            "Loop over the two classes; filter the rows of each.",
            "K_j is the number of distinct values of feature j across all training rows.",
            "Multiply prior × smoothed conditional probabilities, then normalise the two scores.",
        ],
        brute_force="sklearn.naive_bayes.CategoricalNB implements a close variant (with smoothed priors optional); here the rules are spelled out so the answer is exact.",
        approach=r"""First test (alpha = 0): non-spam score 0.5 × (1/6)(5/6)(6/6) = 0.0694; spam score 0.5 × (5/6)(1/6)(1/6) = 0.0116;
posterior 0.0116 / 0.0810 = 0.143.""",
        complexity="O(n·p) per class.",
        pitfalls=r"""- Forgetting alpha × K_j in the denominator, so smoothed probabilities no longer sum to one.
- Smoothing the prior (not asked for here).
- Products of many small numbers underflow; real implementations add log-probabilities.""",
        follow_up="Rewrite it with log-probabilities and logsumexp so it works with thousands of features.",
    ),
),

# ---------------------------------------------------------------- logistic Newton
dict(
    id="stats-logistic-newton",
    title="Fit Logistic Regression by Newton-Raphson",
    difficulty="Hard",
    pattern="Logistic Regression",
    kind="function",
    entry="fit_logistic",
    compare="float",
    tolerance=1e-5,
    description=r"""
Fit logistic regression **with an intercept** by maximum likelihood using Newton-Raphson. With design matrix $A$
(a column of ones followed by `X`), start from $b = 0$ and repeat `iterations` times:

$$p = \sigma(Ab),\quad g = A^\top (y - p),\quad H = A^\top \operatorname{diag}(p(1-p))\,A,\quad b \leftarrow b + H^{-1} g$$

Return the final coefficients `[b0, b1, ..., bp]` as a list. (Solve $H\,\delta = g$ rather than inverting $H$.)

Constraints: the classes are not perfectly separable; `1 <= iterations <= 25`.

**Example:** `X = [[-2], [-1], [0], [1], [2], [0.5]], y = [0, 0, 1, 0, 1, 1], iterations = 10` → about `[-0.1459, 1.1947]`
(compare with `statsmodels.Logit`).
""",
    starter='''import numpy as np

def fit_logistic(X, y, iterations):
    pass
''',
    solution='''import numpy as np

def fit_logistic(X, y, iterations):
    A = np.column_stack([np.ones(len(X)), np.asarray(X, dtype=float)])
    yv = np.asarray(y, dtype=float)
    b = np.zeros(A.shape[1])
    for _ in range(iterations):
        p = 1 / (1 + np.exp(-(A @ b)))
        g = A.T @ (yv - p)
        H = A.T @ (A * (p * (1 - p))[:, None])
        b = b + np.linalg.solve(H, g)
    return b.tolist()
''',
    tests=[
        [[[-2], [-1], [0], [1], [2], [0.5]], [0, 0, 1, 0, 1, 1], 10],
        [[[-2], [-1], [0], [1], [2], [0.5]], [0, 0, 1, 0, 1, 1], 1],
        [[[0], [0], [1], [1]], [0, 1, 0, 1], 5],
        [[[1, 0], [0, 1], [1, 1], [2, 1], [0, 2], [2, 0], [1, 2], [3, 1]], [0, 0, 1, 1, 0, 1, 1, 0], 8],
        [_LX1, _Ly1, 12],
        [_LX2, _Ly2, 12],
    ],
    examples=2,
    wrong_solutions=[
        '''import numpy as np

def fit_logistic(X, y, iterations):
    A = np.asarray(X, dtype=float)
    yv = np.asarray(y, dtype=float)
    b = np.zeros(A.shape[1])
    for _ in range(iterations):
        p = 1 / (1 + np.exp(-(A @ b)))
        H = A.T @ (A * (p * (1 - p))[:, None])
        b = b + np.linalg.solve(H, A.T @ (yv - p))
    return [0.0] + b.tolist()
''',
        '''import numpy as np

def fit_logistic(X, y, iterations):
    A = np.column_stack([np.ones(len(X)), np.asarray(X, dtype=float)])
    yv = np.asarray(y, dtype=float)
    b = np.zeros(A.shape[1])
    for _ in range(iterations):
        p = 1 / (1 + np.exp(-(A @ b)))
        b = b + 0.1 * A.T @ (yv - p)
    return b.tolist()
''',
    ],
    guide=dict(
        prereqs="Maximum likelihood and Newton-Raphson for logistic regression (lesson *Logistic regression: odds, log-odds and maximum likelihood*); NumPy matrix operations.",
        intuition=r"""The log-likelihood is a smooth hill with a single top. Newton's method approximates the hill near the current point by
a bowl (a quadratic using the gradient g and curvature H) and jumps straight to the bowl's peak. Near the solution
each step roughly doubles the number of correct digits, so a handful of iterations suffices.""",
        hints=[
            "A = np.column_stack([np.ones(n), X]); start b at zeros.",
            "p = 1 / (1 + exp(−A b)); gradient g = Aᵀ(y − p).",
            "H = Aᵀ W A with W = diag(p(1 − p)); compute it as A.T @ (A * w[:, None]) and update b += solve(H, g).",
        ],
        brute_force="Plain gradient ascent with a small step converges too, but needs thousands of iterations and a well-chosen step size.",
        approach=r"""Iteration 1 from b = 0: every p = 0.5, so W = 0.25·I; the first step is a weighted least-squares fit of
(y − 0.5)/0.25 on A. Repeating recomputes p and W each time (this is why the method is also called iteratively
reweighted least squares).""",
        complexity="O(iterations · (n·p² + p³)).",
        pitfalls=r"""- Forgetting the intercept column.
- Sign errors: with g = Aᵀ(y − p) and the positive-definite H written here, the update is b + H⁻¹g.
- Perfectly separable data make the coefficients diverge; real software regularises or warns.""",
        follow_up="Return also the standard errors: the square roots of the diagonal of H⁻¹ at convergence.",
    ),
),

# ---------------------------------------------------------------- PCA explained variance
dict(
    id="stats-pca-explained",
    title="PCA Explained Variance Ratios",
    difficulty="Medium",
    pattern="Principal Components",
    kind="function",
    entry="explained_ratios",
    compare="float",
    tolerance=1e-6,
    description=r"""
Standardise each column of `X` (subtract its mean and divide by its standard deviation; columns are never constant),
then compute principal components via the singular value decomposition of the standardised matrix $Z = U S V^\top$.
Return the **explained variance ratios** $S_k^2 / \sum_j S_j^2$ in decreasing order (one per column of `X`).

Constraints: `n >= 2` rows, `p >= 1` columns, `n >= p`.

**Example:** `X = [[1, 2], [2, 4], [3, 6.5], [4, 8]]` → about `[0.9979, 0.0021]` (the columns are almost perfectly
correlated, so one component holds nearly everything).
""",
    starter='''import numpy as np

def explained_ratios(X):
    pass
''',
    solution='''import numpy as np

def explained_ratios(X):
    A = np.asarray(X, dtype=float)
    Z = (A - A.mean(axis=0)) / A.std(axis=0)
    s = np.linalg.svd(Z, compute_uv=False)
    ratios = s ** 2 / np.sum(s ** 2)
    out = sorted(ratios.tolist(), reverse=True)
    return out + [0.0] * (A.shape[1] - len(out))
''',
    tests=[
        [[[1, 2], [2, 4], [3, 6.5], [4, 8]]],
        [[[1, 0], [0, 1], [-1, 0], [0, -1]]],
        [[[2.0], [4.0], [9.0]]],
        [[[1, 5, 3], [2, 3, 1], [3, 8, 2], [4, 1, 5], [5, 6, 4]]],
        [[[_r.gauss(0, 1) * 1000, _r.gauss(0, 1), _r.gauss(0, 1)] for _ in range(50)]],
        [[[a, a * 0.9 + _r.gauss(0, 0.3), -a + _r.gauss(0, 0.3), _r.gauss(0, 1)] for a in [_r.gauss(0, 1) for _ in range(200)]]],
    ],
    examples=2,
    wrong_solutions=[
        '''import numpy as np

def explained_ratios(X):
    A = np.asarray(X, dtype=float)
    Z = A - A.mean(axis=0)
    s = np.linalg.svd(Z, compute_uv=False)
    return sorted((s ** 2 / np.sum(s ** 2)).tolist(), reverse=True)
''',
        '''import numpy as np

def explained_ratios(X):
    A = np.asarray(X, dtype=float)
    Z = (A - A.mean(axis=0)) / A.std(axis=0)
    s = np.linalg.svd(Z, compute_uv=False)
    return sorted((s / np.sum(s)).tolist(), reverse=True)
''',
    ],
    guide=dict(
        prereqs="PCA, standardisation and the SVD (lesson *Unsupervised learning: PCA and clustering, the statistical view*).",
        intuition=r"""After standardising, every column has variance 1, so no variable dominates because of its units. The squared singular
values of the standardised matrix are proportional to the variance captured by each principal component; dividing by
their sum gives each component's share.""",
        hints=[
            "Standardise with A.std(axis=0) (any consistent divisor works: it cancels in the ratios).",
            "np.linalg.svd(Z, compute_uv=False) returns the singular values only.",
            "Square them before normalising; return them in decreasing order.",
        ],
        brute_force="Eigen-decompose the correlation matrix (np.linalg.eigvalsh(np.corrcoef(X, rowvar=False))) and normalise the eigenvalues: same answer.",
        approach=r"""Example: the two columns have correlation ≈ 0.9959, so the correlation matrix's eigenvalues are 1 ± 0.9959, and
the ratios are (1 ± 0.9959)/2 ≈ 0.9979 and 0.0021.""",
        complexity="O(n·p²) for the SVD.",
        pitfalls=r"""- Skipping standardisation: a column in large units takes almost all the variance.
- Normalising singular values instead of their squares.
- Returning ratios in SVD order is fine (already decreasing) but sort to be safe.""",
        follow_up="Return the loadings too (rows of Vᵀ) and interpret the first component on a real dataset.",
    ),
),

# ---------------------------------------------------------------- Gower distance
dict(
    id="stats-gower-distance",
    title="Gower Distance for Mixed Data",
    difficulty="Medium",
    pattern="Clustering",
    kind="function",
    entry="gower_matrix",
    compare="float",
    description=r"""
Records mix numeric and categorical attributes. `rows` is a list of records (lists); `numeric` lists the column indices
that are numeric. Return the full `n × n` **Gower distance** matrix, where the distance between records `a` and `b` is
the average over all columns of a per-column distance:

- numeric column `j`: `|a[j] - b[j]| / range_j`, where `range_j` is the max minus the min of column `j` over all rows
  (if `range_j == 0`, the column contributes 0);
- any other column: `0` if the values are equal, else `1`.

**Example:** rows `[[25, 120.0, "basic", True], [47, 900.0, "pro", False], [31, 150.0, "basic", True]]`,
`numeric = [0, 1]` → `d(0, 2) = (6/22 + 30/780 + 0 + 0) / 4 ≈ 0.0778`.
""",
    starter='''def gower_matrix(rows, numeric):
    pass
''',
    solution='''def gower_matrix(rows, numeric):
    n, p = len(rows), len(rows[0])
    num = set(numeric)
    rng = {}
    for j in num:
        col = [r[j] for r in rows]
        rng[j] = max(col) - min(col)
    D = [[0.0] * n for _ in range(n)]
    for a in range(n):
        for b in range(a + 1, n):
            total = 0.0
            for j in range(p):
                if j in num:
                    if rng[j] > 0:
                        total += abs(rows[a][j] - rows[b][j]) / rng[j]
                else:
                    total += 0.0 if rows[a][j] == rows[b][j] else 1.0
            D[a][b] = D[b][a] = total / p
    return D
''',
    tests=[
        [[[25, 120.0, "basic", True], [47, 900.0, "pro", False], [31, 150.0, "basic", True]], [0, 1]],
        [[[25, 120.0, "basic", True], [47, 900.0, "pro", False], [31, 150.0, "basic", True], [62, 400.0, "team", False]], [0, 1]],
        [[[1], [1], [1]], [0]],
        [[["a", "x"], ["a", "y"], ["b", "y"]], []],
        [[[0.0, 10.0], [5.0, 10.0], [10.0, 10.0]], [0, 1]],
        [[[3]], [0]],
        [[[_r.randint(18, 70), round(_r.uniform(0, 500), 1), _r.choice(["sg", "my", "id"]), _r.choice([0, 1])] for _ in range(25)], [0, 1]],
    ],
    examples=1,
    wrong_solutions=[
        '''def gower_matrix(rows, numeric):
    n, p = len(rows), len(rows[0])
    D = [[0.0] * n for _ in range(n)]
    for a in range(n):
        for b in range(n):
            total = 0.0
            for j in range(p):
                if j in numeric:
                    total += abs(rows[a][j] - rows[b][j])
                else:
                    total += 0.0 if rows[a][j] == rows[b][j] else 1.0
            D[a][b] = total / p
    return D
''',
    ],
    guide=dict(
        prereqs="Scaling and categorical variables in clustering (lesson *Unsupervised learning: PCA and clustering, the statistical view*).",
        intuition=r"""Euclidean distance cannot mix dollars, ages and plan names sensibly. Gower puts every attribute on the same 0-to-1
scale (numeric differences as a share of the column's range, categories as match or mismatch) and averages them, so
each attribute gets an equal say.""",
        hints=[
            "Precompute each numeric column's range once.",
            "Skip numeric columns with zero range (they carry no information).",
            "The matrix is symmetric with zeros on the diagonal; fill both D[a][b] and D[b][a].",
        ],
        brute_force="Recomputing column ranges inside the pair loop works but costs O(n³·p).",
        approach=r"""Example pair (0, 2): age |25 − 31| / (47 − 25) = 0.2727; spend |120 − 150| / 780 = 0.0385; plan equal → 0; mobile
equal → 0; average over 4 columns = 0.0778.""",
        complexity="O(n²·p) time, O(n²) space.",
        pitfalls=r"""- Forgetting to divide numeric differences by the range.
- Dividing by zero for constant columns.
- Averaging over only the numeric columns instead of all columns.""",
        follow_up="Feed the matrix to hierarchical clustering (scipy linkage on the condensed form) or to k-medoids.",
    ),
),
]
