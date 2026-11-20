import numpy as _np

_rng = _np.random.RandomState(1)


def _r(*shape, scale=1.0):
    return (_rng.randn(*shape) * scale).round(3).tolist()


def _linreg_data(n, p, noise=0.1):
    X = _rng.randn(n, p).round(3)
    w = _rng.randn(p).round(2)
    y = (X @ w + 0.5 + noise * _rng.randn(n)).round(3)
    return X.tolist(), y.tolist()


def _mlp_params(d, h, k, n):
    X = _r(n, d)
    W1 = _r(d, h, scale=0.5)
    b1 = _r(h, scale=0.1)
    W2 = _r(h, k, scale=0.5)
    b2 = _r(k, scale=0.1)
    return X, W1, b1, W2, b2


PROBLEMS = [
# ---------------------------------------------------------------- sigmoid + BCE
dict(
    id="ml-sigmoid-bce",
    title="Sigmoid and Binary Cross-Entropy from Logits",
    difficulty="Medium",
    pattern="Linear Models",
    kind="function",
    entry="sigmoid_bce",
    compare="float",
    description=r"""
A logistic-regression model outputs **logits** $z_i$ (real numbers). Given `logits` and binary labels `y`
(0/1, same length $n\ge1$), return `[probs, loss]` where

$$p_i=\sigma(z_i)=\frac{1}{1+e^{-z_i}},\qquad \text{loss}=-\frac1n\sum_i\big[y_i\log p_i+(1-y_i)\log(1-p_i)\big].$$

Your code must be **numerically stable** for logits as extreme as $\pm 1000$: no `inf`, no `nan`, and the
loss for a confidently-wrong prediction must be large but finite (e.g. $z=-800, y=1$ gives loss 800).

**Example:** `logits=[0, 2], y=[1, 0]` → `[[0.5, 0.8808], 1.4100]`
""",
    starter='''import numpy as np

def sigmoid_bce(logits, y):
    """Return [list_of_probabilities, mean_loss]."""
    pass
''',
    solution='''import numpy as np

def sigmoid_bce(logits, y):
    z = np.asarray(logits, dtype=float)
    y = np.asarray(y, dtype=float)
    # stable sigmoid: never exponentiate a positive number
    e = np.exp(-np.abs(z))
    p = np.where(z >= 0, 1.0 / (1.0 + e), e / (1.0 + e))
    # stable BCE from logits: max(z,0) - z*y + log(1 + exp(-|z|))
    loss = np.mean(np.maximum(z, 0) - z * y + np.log1p(e))
    return [p.tolist(), float(loss)]
''',
    tests=[
        [[0, 2], [1, 0]],
        [[0], [0]],
        [[10, -10], [1, 0]],
        [[-800], [1]],
        [[800], [0]],
        [[1000, -1000, 0], [1, 0, 1]],
        [[3.5, -1.2, 0.3, 2.2], [1, 1, 0, 0]],
        [[-50, 50], [0, 1]],
        [_r(30, scale=4), [int(v) for v in (_rng.rand(30) > 0.5)]],
        [_r(100, scale=40), [int(v) for v in (_rng.rand(100) > 0.3)]],
    ],
    wrong_solutions=[
        '''import numpy as np
def sigmoid_bce(logits, y):
    z = np.asarray(logits, float); y = np.asarray(y, float)
    p = 1 / (1 + np.exp(-z))
    loss = -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
    return [p.tolist(), float(loss)]
''',
        '''import numpy as np
def sigmoid_bce(logits, y):
    z = np.asarray(logits, float); y = np.asarray(y, float)
    p = 1 / (1 + np.exp(-z))
    p = np.clip(p, 1e-7, 1 - 1e-7)
    loss = -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
    return [p.tolist(), float(loss)]
''',
    ],
    guide=dict(
        prereqs="Logistic regression (Supervised, lesson 2); log/exp rules; MLE (Math, lesson 3).",
        intuition=r"""BCE is the negative log-likelihood of Bernoulli labels. Computing $p=\sigma(z)$ first and then
$\log p$ throws away precision: for $z=-800$, $p$ underflows to exactly 0 and $\log 0=-\infty$. Instead, simplify
the loss **algebraically in terms of $z$**. Using $\log\sigma(z) = -\log(1+e^{-z})$ and
$\log(1-\sigma(z)) = -z-\log(1+e^{-z})$, the per-example loss is

$$\ell(z,y) = \log(1+e^{-z}) + (1-y)z = \max(z,0) - zy + \log\!\big(1+e^{-|z|}\big).$$

The last form only ever exponentiates a non-positive number, so it cannot overflow. This is exactly what
PyTorch's `BCEWithLogitsLoss` and TensorFlow's `sigmoid_cross_entropy_with_logits` do.""",
        hints=[
            "For the sigmoid, use $e=\\exp(-|z|)$; then $\\sigma(z)=1/(1+e)$ if $z\\ge0$ and $e/(1+e)$ otherwise.",
            "Do not compute log(p). Rewrite the loss using only z, y and log1p(exp(-|z|)).",
            "loss_i = max(z,0) - z*y + log1p(exp(-|z|)); then average.",
        ],
        brute_force="The textbook formula with `log(p)` works for moderate logits but returns inf/nan at the extremes. Clipping p to [1e-7, 1-1e-7] avoids inf but silently caps the loss at ~16, which is wrong.",
        approach=r"""Verify the identity for $y=1$: $\ell = -\log\sigma(z) = \log(1+e^{-z})$. If $z\ge0$ this equals
$\log(1+e^{-|z|})$ ✓.; if $z<0$, $\log(1+e^{-z}) = -z + \log(e^{z}+1) = -z + \log(1+e^{-|z|})$, matching
$\max(z,0)-z+\log(1+e^{-|z|})$ ✓. For the example: $z=0,y=1$ → $\log 2 = 0.693$; $z=2,y=0$ → $2+\log(1+e^{-2}) = 2.127$; mean 1.410.""",
        complexity="Time O(n), space O(n).",
        pitfalls=r"""- `np.where` evaluates both branches; that is why we pre-compute $e=\exp(-|z|)$ (always ≤1) rather than `exp(-z)` and `exp(z)`.
- `np.log1p(x)` is more accurate than `np.log(1+x)` for tiny x.
- Clipping is a hack that changes the loss value.""",
        follow_up="Derive the gradient: $\\partial \\ell/\\partial z = \\sigma(z) - y$ — the reason logistic regression's gradient is so clean.",
    ),
),

# ---------------------------------------------------------------- normal equation
dict(
    id="ml-normal-equation",
    title="Linear Regression via the Normal Equation",
    difficulty="Medium",
    pattern="Linear Models",
    kind="function",
    entry="fit_linear_regression",
    compare="float",
    tolerance=1e-5,
    description=r"""
Fit ordinary least squares **with an intercept**: find $b$ and $w$ minimising
$\sum_i (y_i - b - w^\top x_i)^2$. `X` is an $n\times p$ list (full column rank after adding the intercept
column), `y` a list of $n$ targets. Return `[b, w_1, ..., w_p]`.

Use the closed form $\theta = (\tilde X^\top \tilde X)^{-1}\tilde X^\top y$ where $\tilde X = [\mathbf 1 \mid X]$ —
but solve the linear system (`np.linalg.solve` or `lstsq`) rather than forming an explicit inverse.

**Example:** `X=[[1],[2],[3]]`, `y=[3,5,7]` → `[1.0, 2.0]`
""",
    starter='''import numpy as np

def fit_linear_regression(X, y):
    pass
''',
    solution='''import numpy as np

def fit_linear_regression(X, y):
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    Xt = np.hstack([np.ones((X.shape[0], 1)), X])
    theta, *_ = np.linalg.lstsq(Xt, y, rcond=None)
    return theta.tolist()
''',
    tests=[
        [[[1], [2], [3]], [3, 5, 7]],
        [[[0], [1]], [1, 1]],
        [[[1, 0], [0, 1], [1, 1], [2, 1]], [1, 2, 3, 4]],
        [[[1], [2], [3], [4]], [10, 10, 10, 10]],
        [[[-1], [0], [1]], [-5, 0, 5]],
        [[[1, 2], [2, 1], [3, 5], [4, 2], [5, 7]], [8, 7, 15, 10, 21]],
        _linreg_data(20, 3),
        _linreg_data(50, 5, noise=1.0),
        _linreg_data(200, 10),
        [[[1], [2], [3], [4], [5]], [1.1, 1.9, 3.2, 3.9, 5.1]],
    ],
    wrong_solutions=[
        '''import numpy as np
def fit_linear_regression(X, y):
    X = np.asarray(X, float); y = np.asarray(y, float)
    w = np.linalg.lstsq(X, y, rcond=None)[0]
    return [0.0] + w.tolist()
''',
        '''import numpy as np
def fit_linear_regression(X, y):
    X = np.asarray(X, float); y = np.asarray(y, float)
    w = np.linalg.lstsq(X - X.mean(0), y - y.mean(), rcond=None)[0]
    return [float(y.mean())] + w.tolist()
''',
    ],
    guide=dict(
        prereqs="Matrix products and gradients (Math, lessons 1–2); linear models (Supervised, lesson 2).",
        intuition=r"""Write the residual vector as $r = y - \tilde X\theta$. The loss $\lVert r\rVert^2$ is a convex bowl in $\theta$;
its minimum is where the gradient vanishes: $\nabla_\theta = -2\tilde X^\top(y - \tilde X\theta) = 0$, giving the
**normal equations** $\tilde X^\top\tilde X\,\theta = \tilde X^\top y$. Geometrically, $\tilde X\theta$ is the orthogonal
projection of $y$ onto the column space of $\tilde X$ — the residual is perpendicular ("normal") to every column.""",
        hints=[
            "Prepend a column of ones so the intercept is just another weight.",
            "Solve $A\\theta = c$ with $A = \\tilde X^T\\tilde X$, $c = \\tilde X^T y$ — or call `np.linalg.lstsq(Xt, y)` directly, which is more stable.",
            "Return the intercept first.",
        ],
        brute_force="Gradient descent also converges to the same answer, but needs a learning rate and many iterations.",
        approach=r"""1. `Xt = hstack([ones, X])`.
2. `theta = lstsq(Xt, y)` (uses an SVD internally; equivalent to the normal equation when $\tilde X$ has full column rank).
3. Return `theta`.

Example: points (1,3),(2,5),(3,7) lie exactly on $y=1+2x$, so $\theta=[1,2]$.""",
        complexity=r"Forming $\tilde X^\top\tilde X$ costs O(n·p²), solving it O(p³). Great for p up to a few thousand; for huge p or n, use (stochastic) gradient descent.",
        pitfalls=r"""- Forgetting the intercept column (fits a line through the origin).
- `np.linalg.inv(A) @ c` works but is slower and less accurate than `solve`/`lstsq`; when features are nearly collinear, $\tilde X^\top\tilde X$ is ill-conditioned (its condition number is the *square* of $\tilde X$'s).
- Ridge regression adds $\alpha I$ (but not on the intercept) — that also fixes singular matrices.""",
        follow_up="Implement ridge: $\\theta = (\\tilde X^T\\tilde X + \\alpha D)^{-1}\\tilde X^T y$ with D = diag(0,1,…,1).",
    ),
),

# ---------------------------------------------------------------- GD for linear regression
dict(
    id="ml-gd-linear-regression",
    title="Gradient Descent Steps for Linear Regression",
    difficulty="Medium",
    pattern="Optimization",
    kind="function",
    entry="gd_steps",
    compare="float",
    description=r"""
Run `steps` iterations of **full-batch** gradient descent on the mean-squared-error loss

$$L(w,b)=\frac1n\sum_{i=1}^n\left(w^\top x_i + b - y_i\right)^2$$

starting from the given `w` (list of $p$ floats) and `b`, with learning rate `lr`. Each step updates
**both** parameters simultaneously using gradients computed at the current point:

$$\nabla_w L = \frac2n X^\top(\hat y - y),\qquad \frac{\partial L}{\partial b} = \frac2n\sum_i(\hat y_i - y_i).$$

Return `[w_1, ..., w_p, b]` after the last step (`steps` may be 0).

**Example:** `X=[[1],[2]], y=[2,4], w=[0], b=0, lr=0.1, steps=1` → `[1.0, 0.6]`
""",
    starter='''import numpy as np

def gd_steps(X, y, w, b, lr, steps):
    pass
''',
    solution='''import numpy as np

def gd_steps(X, y, w, b, lr, steps):
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    w = np.asarray(w, dtype=float).copy()
    b = float(b)
    n = len(y)
    for _ in range(steps):
        r = X @ w + b - y
        gw = 2.0 / n * (X.T @ r)
        gb = 2.0 / n * r.sum()
        w -= lr * gw
        b -= lr * gb
    return w.tolist() + [b]
''',
    tests=[
        [[[1], [2]], [2, 4], [0], 0, 0.1, 1],
        [[[1], [2]], [2, 4], [0], 0, 0.1, 0],
        [[[1], [2]], [2, 4], [0], 0, 0.1, 2],
        [[[1], [2], [3]], [1, 2, 3], [1], 0, 0.05, 10],
        [[[1, 2], [3, 4], [5, 6]], [1, 0, 1], [0.5, -0.5], 0.2, 0.01, 5],
        [[[0.5], [1.5], [2.5], [3.5]], [1, 3, 5, 7], [0], 0, 0.1, 200],
        [*_linreg_data(30, 3), [0, 0, 0], 0, 0.1, 50],
        [*_linreg_data(100, 4), [1, 1, 1, 1], 1, 0.05, 25],
        [[[1]], [5], [0], 0, 0.25, 3],
        [[[2], [4]], [1, 2], [0], 0, 0.01, 1],
    ],
    wrong_solutions=[
        '''import numpy as np
def gd_steps(X, y, w, b, lr, steps):
    X = np.asarray(X, float); y = np.asarray(y, float); w = np.asarray(w, float).copy(); n = len(y)
    for _ in range(steps):
        r = X @ w + b - y
        w -= lr * (X.T @ r) / n
        b -= lr * r.sum() / n
    return w.tolist() + [b]
''',
        '''import numpy as np
def gd_steps(X, y, w, b, lr, steps):
    X = np.asarray(X, float); y = np.asarray(y, float); w = np.asarray(w, float).copy(); n = len(y)
    for _ in range(steps):
        r = X @ w + b - y
        w -= lr * 2 / n * (X.T @ r)
        r = X @ w + b - y   # bug: bias uses the already-updated weights
        b -= lr * 2 / n * r.sum()
    return w.tolist() + [b]
''',
    ],
    guide=dict(
        prereqs="Derivatives, gradients and the chain rule (Math, lesson 2).",
        intuition=r"""Gradient descent repeatedly steps "downhill": $\theta \leftarrow \theta - \eta\nabla L(\theta)$. For MSE the
gradient has a beautiful form — the residual vector $r=\hat y - y$ pushed back through the design matrix,
$\frac2n X^\top r$. Features that correlate with the residual get their weights adjusted the most.""",
        hints=[
            "Compute residuals `r = X @ w + b - y` once per step.",
            "Both gradients come from the same `r`; update w and b afterwards.",
            "Mind the factor 2/n — it comes from differentiating the square and from the mean.",
        ],
        brute_force="Computing each partial derivative with a Python loop over samples is the same algorithm, just slower.",
        approach=r"""Derivation by the chain rule: $L=\frac1n\sum r_i^2$, $\partial r_i/\partial w_j = x_{ij}$, $\partial r_i/\partial b = 1$, so
$\partial L/\partial w_j = \frac2n\sum_i r_i x_{ij}$ and $\partial L/\partial b = \frac2n\sum_i r_i$.

Example: $w=0,b=0$ → $r=[-2,-4]$, $\nabla_w = \frac22(1\cdot -2 + 2\cdot -4) = -10$, $\partial_b = -6$.
After one step with $\eta=0.1$: $w=1.0$, $b=0.6$.""",
        complexity="O(steps · n · p) time, O(n + p) extra space.",
        pitfalls=r"""- Many textbooks use $L=\frac{1}{2n}\sum r^2$, whose gradient lacks the 2 — read the spec.
- Sequential updates (b computed with the new w) is a different algorithm (closer to coordinate descent).
- Too large a learning rate diverges: for MSE GD is stable only if $\eta < 2/\lambda_{max}$ of the Hessian $\frac2n\tilde X^\top \tilde X$. Scaling features makes the bowl rounder and lets you use bigger steps.""",
        follow_up="Mini-batch SGD: use a random subset of rows per step. Add momentum: $v \\leftarrow \\beta v + g$, $\\theta \\leftarrow \\theta - \\eta v$.",
    ),
),

# ---------------------------------------------------------------- logistic regression gradient
dict(
    id="ml-logreg-gradient",
    title="Logistic Regression Loss and Gradient with L2",
    difficulty="Medium",
    pattern="Linear Models",
    kind="function",
    entry="logreg_loss_grad",
    compare="float",
    description=r"""
For binary labels $y_i\in\{0,1\}$, weights `w` (length $p$), bias `b` and L2 strength `lam`, compute

$$J(w,b) = \frac1n\sum_{i=1}^n \Big[-y_i\log\sigma(z_i)-(1-y_i)\log(1-\sigma(z_i))\Big] + \frac{\lambda}{2}\lVert w\rVert^2,\quad z_i=w^\top x_i+b$$

and its gradient. **The bias is not regularised.** Return `[J, grad_w_1, ..., grad_w_p, grad_b]`.
Use a numerically stable formulation of the log-loss (logits stay within ±30 in the tests, but stay safe).

**Example:** `X=[[1,2],[-1,0]], y=[1,0], w=[0,0], b=0, lam=0` → `[0.6931, -0.5, -0.5, 0.0]`
""",
    starter='''import numpy as np

def logreg_loss_grad(X, y, w, b, lam):
    pass
''',
    solution='''import numpy as np

def logreg_loss_grad(X, y, w, b, lam):
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    w = np.asarray(w, dtype=float)
    n = len(y)
    z = X @ w + b
    loss = np.mean(np.maximum(z, 0) - z * y + np.log1p(np.exp(-np.abs(z)))) + 0.5 * lam * (w @ w)
    p = 0.5 * (1 + np.tanh(0.5 * z))          # stable sigmoid
    r = p - y
    gw = X.T @ r / n + lam * w
    gb = r.mean()
    return [float(loss)] + gw.tolist() + [float(gb)]
''',
    tests=[
        [[[1, 2], [-1, 0]], [1, 0], [0, 0], 0, 0],
        [[[1, 2], [-1, 0]], [1, 0], [0.5, -0.5], 0.1, 0.0],
        [[[1, 2], [-1, 0]], [1, 0], [0.5, -0.5], 0.1, 1.0],
        [[[1], [2], [3]], [0, 1, 1], [1], -1.5, 0.5],
        [[[0], [0]], [0, 1], [0], 0, 0],
        [[[10], [-10]], [1, 0], [3], 0, 0.01],
        [_r(20, 3), [int(v) for v in (_rng.rand(20) > 0.5)], _r(3), 0.3, 0.1],
        [_r(50, 6), [int(v) for v in (_rng.rand(50) > 0.4)], _r(6), -0.2, 0.0],
        [_r(50, 6), [int(v) for v in (_rng.rand(50) > 0.4)], _r(6), 2.0, 2.0],
        [[[1, 1]], [1], [2, 2], 1, 0.5],
    ],
    wrong_solutions=[
        '''import numpy as np
def logreg_loss_grad(X, y, w, b, lam):
    X = np.asarray(X, float); y = np.asarray(y, float); w = np.asarray(w, float); n = len(y)
    z = X @ w + b
    loss = np.mean(np.maximum(z, 0) - z * y + np.log1p(np.exp(-np.abs(z)))) + 0.5 * lam * (w @ w + b * b)
    r = 1 / (1 + np.exp(-z)) - y
    return [float(loss)] + (X.T @ r / n + lam * w).tolist() + [float(r.mean() + lam * b)]
''',
        '''import numpy as np
def logreg_loss_grad(X, y, w, b, lam):
    X = np.asarray(X, float); y = np.asarray(y, float); w = np.asarray(w, float); n = len(y)
    z = X @ w + b
    loss = np.mean(np.maximum(z, 0) - z * y + np.log1p(np.exp(-np.abs(z)))) + 0.5 * lam * (w @ w)
    r = y - 1 / (1 + np.exp(-z))
    return [float(loss)] + (X.T @ r / n + lam * w).tolist() + [float(r.mean())]
''',
    ],
    guide=dict(
        prereqs="Sigmoid/BCE (problem ml-sigmoid-bce); chain rule (Math, lesson 2); regularisation (Supervised, lesson 2).",
        intuition=r"""The derivative of the logistic loss with respect to the logit is simply $\sigma(z)-y$: predicted
probability minus truth. By the chain rule, $\partial z_i/\partial w = x_i$ and $\partial z_i/\partial b = 1$, so the
gradient is the average of residual-weighted inputs — the same shape as linear regression's gradient, just with a
different "residual". The L2 penalty adds $\lambda w$ (weight decay), and we leave the bias out because penalising
it would bias predictions towards 50/50 for no benefit.""",
        hints=[
            "Compute z = X@w + b and p = sigmoid(z).",
            "grad_w = X.T @ (p - y) / n + lam * w; grad_b = mean(p - y).",
            "Loss: use the stable form max(z,0) - z*y + log1p(exp(-|z|)), then add 0.5*lam*||w||².",
        ],
        brute_force="Finite differences (perturb each parameter by ±ε) give the gradient in O(p·n·p) — great to *check* your analytic gradient, too slow to train with.",
        approach=r"""Derivation: $\frac{d}{dz}\big[-y\log\sigma(z)-(1-y)\log(1-\sigma(z))\big] = -y(1-\sigma) + (1-y)\sigma = \sigma(z)-y$, using $\sigma' = \sigma(1-\sigma)$.

Example with $w=0,b=0$: $p=[0.5,0.5]$, $r=[-0.5,0.5]$. grad_w $= \frac12([1,2]\cdot -0.5 + [-1,0]\cdot 0.5) = [-0.5,-0.5]$; grad_b $=0$; loss $=\log 2$.""",
        complexity="O(n·p) time per evaluation.",
        pitfalls=r"""- Sign error: residual must be $p-y$ (gradient of the *loss*, which we descend).
- Regularising the bias.
- scikit-learn's `LogisticRegression` uses `C` = inverse regularisation and a *summed* (not averaged) loss: $C\sum_i \ell_i + \frac12\lVert w\rVert^2$. Same minimiser as ours when $\lambda = 1/(nC)$.""",
        follow_up="Multinomial (softmax) regression: gradient is $X^T(P - Y)/n$ with one-hot Y.",
    ),
),

# ---------------------------------------------------------------- Gini best split
dict(
    id="ml-gini-best-split",
    title="Best Decision Stump by Gini Impurity",
    difficulty="Medium",
    pattern="Trees",
    kind="function",
    entry="best_split",
    compare="float",
    description=r"""
A decision stump splits the data with a single test `x[feature] <= threshold`. Given `X` ($n\times p$) and
integer labels `y`, find the split that **minimises the weighted Gini impurity** of the two children

$$G_{split} = \frac{n_L}{n}G(L)+\frac{n_R}{n}G(R),\qquad G(S) = 1-\sum_c p_c^2.$$

- Candidate thresholds for each feature are the **midpoints between consecutive distinct sorted values**.
- Ties: prefer the smaller feature index, then the smaller threshold (strict `<` improvement).
- If no feature has two distinct values, return `[-1, 0.0, G(y)]`.

Return `[feature, threshold, weighted_gini]`.

**Example:** `X=[[2],[3],[10],[19]]`, `y=[0,0,1,1]` → `[0, 6.5, 0.0]`
""",
    starter='''import numpy as np

def best_split(X, y):
    pass
''',
    solution='''import numpy as np

def _gini(counts):
    n = counts.sum()
    if n == 0:
        return 0.0
    p = counts / n
    return 1.0 - float((p * p).sum())

def best_split(X, y):
    X = np.asarray(X, dtype=float)
    y = np.asarray(y)
    classes, yi = np.unique(y, return_inverse=True)
    n, p = X.shape
    total = np.bincount(yi, minlength=len(classes)).astype(float)
    best = [-1, 0.0, _gini(total)]
    best_score = np.inf
    for f in range(p):
        order = np.argsort(X[:, f], kind="stable")
        xs, ys = X[order, f], yi[order]
        left = np.zeros(len(classes))
        for i in range(n - 1):
            left[ys[i]] += 1
            if xs[i] == xs[i + 1]:
                continue
            nl = i + 1
            right = total - left
            score = nl / n * _gini(left) + (n - nl) / n * _gini(right)
            if score < best_score - 1e-12:
                best_score = score
                best = [f, float((xs[i] + xs[i + 1]) / 2), float(score)]
    return best
''',
    tests=[
        [[[2], [3], [10], [19]], [0, 0, 1, 1]],
        [[[1], [1], [1]], [0, 1, 0]],
        [[[1, 5], [2, 6], [3, 7], [4, 8]], [0, 1, 0, 1]],
        [[[0, 0], [0, 1], [1, 0], [1, 1]], [0, 0, 1, 1]],
        [[[0, 0], [0, 1], [1, 0], [1, 1]], [0, 1, 0, 1]],
        [[[1], [2], [3], [4], [5], [6]], [0, 0, 1, 1, 1, 2]],
        [[[3], [1], [2], [2]], [1, 0, 1, 0]],
        [[[5]], [1]],
        [(_rng.rand(30, 3) * 10).round(1).tolist(), [int(v) for v in _rng.randint(0, 2, 30)]],
        [(_rng.rand(60, 4) * 10).round(0).tolist(), [int(v) for v in _rng.randint(0, 3, 60)]],
        [[[1, 1], [1, 2], [1, 3]], [0, 0, 1]],
    ],
    wrong_solutions=[
        '''import numpy as np
def best_split(X, y):
    X = np.asarray(X, float); y = np.asarray(y); n, p = X.shape
    def g(s):
        if len(s) == 0: return 0.0
        _, c = np.unique(s, return_counts=True); q = c / len(s); return 1 - (q * q).sum()
    best = [-1, 0.0, g(y)]; bs = np.inf
    for f in range(p):
        for t in np.unique(X[:, f])[:-1]:
            m = X[:, f] <= t
            s = (g(y[m]) + g(y[~m])) / 2      # unweighted average
            if s < bs - 1e-12:
                bs = s; best = [f, float(t), float(s)]
    return best
''',
    ],
    guide=dict(
        prereqs="Decision trees (Supervised, lesson 3).",
        intuition=r"""Gini impurity is the probability that two items drawn at random (with replacement) from a node
have different labels. A pure node has $G=0$; a 50/50 binary node has $G=0.5$. A tree greedily picks the
question that makes the children as pure as possible, weighting each child by how many samples it holds.""",
        hints=[
            "Sort each feature once; sweep a split point from left to right, moving one sample at a time from right to left child.",
            "Maintain class counts incrementally instead of recomputing them — that makes each feature O(n log n).",
            "Skip positions where the current and next sorted values are equal: you cannot split between identical values.",
        ],
        brute_force="For every feature and every candidate threshold, recount both sides: O(p · n²). Fine for tiny data.",
        approach=r"""For each feature: argsort; walk `i = 0..n-2`, add `y[i]` to the left counts; if `x[i] != x[i+1]`
evaluate the weighted Gini with right = total − left and threshold = midpoint.

Example: sorted x = 2, 3, 10, 19 with labels 0,0,1,1. Split after index 1 (threshold 6.5): both children pure,
$G=0$. No later split can beat 0, so the answer is `[0, 6.5, 0.0]`.""",
        complexity="O(p · n log n) time (sorting dominates), O(n + C) space.",
        pitfalls=r"""- Using the plain average of child impurities instead of the size-weighted average.
- Thresholding at an existing value rather than the midpoint (scikit-learn also uses midpoints).
- Floating ties: compare with a tiny epsilon so equal scores keep the earlier (smaller) candidate.""",
        follow_up="Regression trees use variance (MSE) reduction instead of Gini; information gain uses entropy (next problem).",
    ),
),

# ---------------------------------------------------------------- entropy / information gain
dict(
    id="ml-info-gain",
    title="Entropy and Information Gain",
    difficulty="Easy",
    pattern="Trees",
    kind="function",
    entry="information_gain",
    compare="float",
    description=r"""
Given class labels `y` and a boolean list `go_left` of the same length describing a split, return
`[H_parent, information_gain]` using entropy in **bits**:

$$H(S) = -\sum_c p_c\log_2 p_c\quad(0\log 0 := 0),\qquad IG = H(S) - \frac{|L|}{|S|}H(L) - \frac{|R|}{|S|}H(R).$$

An empty child contributes 0. Labels can be any hashable values (ints or strings).

**Example:** `y=[0,0,1,1]`, `go_left=[True,True,False,False]` → `[1.0, 1.0]`
""",
    starter='''import numpy as np

def information_gain(y, go_left):
    pass
''',
    solution='''import numpy as np

def _entropy(labels):
    if len(labels) == 0:
        return 0.0
    _, c = np.unique(labels, return_counts=True)
    p = c / c.sum()
    return float(-(p * np.log2(p)).sum())

def information_gain(y, go_left):
    y = np.asarray(y)
    m = np.asarray(go_left, dtype=bool)
    h = _entropy(y)
    n = len(y)
    hl, hr = _entropy(y[m]), _entropy(y[~m])
    return [h, h - m.sum() / n * hl - (~m).sum() / n * hr]
''',
    tests=[
        [[0, 0, 1, 1], [True, True, False, False]],
        [[0, 0, 1, 1], [True, False, True, False]],
        [[1, 1, 1], [True, False, True]],
        [[0, 1, 2, 3], [True, True, False, False]],
        [["a", "b", "a", "b", "a"], [True, True, True, True, True]],
        [["spam", "ham", "spam", "spam"], [True, False, True, True]],
        [[0, 0, 0, 1, 1, 1, 1, 1], [True, True, True, True, False, False, False, False]],
        [[7], [False]],
        [[int(v) for v in _rng.randint(0, 3, 40)], [bool(v) for v in _rng.rand(40) > 0.5]],
        [[int(v) for v in _rng.randint(0, 5, 100)], [bool(v) for v in _rng.rand(100) > 0.7]],
    ],
    wrong_solutions=[
        '''import numpy as np
def information_gain(y, go_left):
    def H(s):
        if len(s) == 0: return 0.0
        _, c = np.unique(s, return_counts=True); p = c / c.sum(); return float(-(p * np.log(p)).sum())
    y = np.asarray(y); m = np.asarray(go_left, bool); n = len(y)
    return [H(y), H(y) - m.sum() / n * H(y[m]) - (~m).sum() / n * H(y[~m])]
''',
    ],
    guide=dict(
        prereqs="Probability (Math, lesson 3); decision trees (Supervised, lesson 3).",
        intuition=r"""Entropy measures uncertainty: the average number of yes/no questions needed to identify a label.
A fair coin has 1 bit; a certain outcome has 0 bits; 4 equally likely classes need 2 bits. Information gain is
how much a split reduces that uncertainty on average — ID3/C4.5 trees and scikit-learn's
`criterion="entropy"` pick the split with the largest gain.""",
        hints=[
            "`np.unique(labels, return_counts=True)` works on strings too.",
            "Only classes that are present appear in the counts, so you never take log2(0).",
            "Weight child entropies by their share of samples; handle the empty child explicitly.",
        ],
        brute_force="A dictionary count per subset is equally fine — it is O(n) either way.",
        approach=r"""1. $H$ of the parent.
2. Split labels by the mask; compute $H(L)$, $H(R)$.
3. $IG = H - \frac{n_L}{n}H(L) - \frac{n_R}{n}H(R)$.

Example 2: alternating mask gives children $\{0,1\}$ and $\{0,1\}$, each with $H=1$, so $IG=0$ — a useless split.""",
        complexity="O(n log n) because of `np.unique` (sorting); O(n) with hashing.",
        pitfalls=r"""- Natural log instead of log2 (gives nats; values scale by 1/ln 2).
- Using unweighted child entropies.
- Computing $p\log p$ for $p=0$ produces `nan` — avoid by only using present classes.""",
        follow_up="Gain ratio (C4.5) divides IG by the split's own entropy to penalise many-valued features.",
    ),
),

# ---------------------------------------------------------------- MLP forward
dict(
    id="ml-mlp-forward",
    title="Two-Layer MLP Forward Pass",
    difficulty="Easy",
    pattern="Neural Networks",
    kind="function",
    entry="mlp_forward",
    compare="float",
    description=r"""
Compute class probabilities of a one-hidden-layer network with ReLU activation and softmax output:

$$H = \operatorname{ReLU}(XW_1 + b_1),\qquad P = \operatorname{softmax}(HW_2 + b_2)\ \text{(row-wise)}.$$

Shapes: `X` $n\times d$, `W1` $d\times h$, `b1` length $h$, `W2` $h\times k$, `b2` length $k$. Return $P$
($n\times k$). Use a stable softmax.

**Example:** `X=[[1,2]]`, `W1=[[1,0],[0,-1]]`, `b1=[0,0]`, `W2=[[1,0],[0,1]]`, `b2=[0,0]` → `[[0.7311, 0.2689]]`
""",
    starter='''import numpy as np

def mlp_forward(X, W1, b1, W2, b2):
    pass
''',
    solution='''import numpy as np

def mlp_forward(X, W1, b1, W2, b2):
    X, W1, b1, W2, b2 = (np.asarray(a, dtype=float) for a in (X, W1, b1, W2, b2))
    H = np.maximum(0.0, X @ W1 + b1)
    Z = H @ W2 + b2
    Z = Z - Z.max(axis=1, keepdims=True)
    E = np.exp(Z)
    return E / E.sum(axis=1, keepdims=True)
''',
    tests=[
        [[[1, 2]], [[1, 0], [0, -1]], [0, 0], [[1, 0], [0, 1]], [0, 0]],
        [[[0, 0]], [[1, 2], [3, 4]], [0, 0], [[1, 2], [3, 4]], [0, 0]],
        [[[-1, -1]], [[1, 1], [1, 1]], [0, 0], [[5, -5], [1, 2]], [1, 0]],
        [[[1, 0], [0, 1], [1, 1]], [[2, 0, -1], [0, 2, 1]], [0.5, -0.5, 0], [[1, 0], [0, 1], [1, 1]], [0, 0.1]],
        [[[100, 100]], [[1, 0], [0, 1]], [0, 0], [[10, 0], [0, 10]], [0, 0]],
        [[[3]], [[2]], [-1], [[1, 2, 3]], [0, 0, 0]],
        list(_mlp_params(4, 5, 3, 6)),
        list(_mlp_params(10, 16, 4, 20)),
        list(_mlp_params(2, 3, 2, 1)),
        [[[1, 2]], [[1, -1], [0, 1]], [0, 0], [[300, 0], [0, 0]], [0, 0]],
    ],
    wrong_solutions=[
        '''import numpy as np
def mlp_forward(X, W1, b1, W2, b2):
    X, W1, b1, W2, b2 = (np.asarray(a, float) for a in (X, W1, b1, W2, b2))
    H = X @ W1 + b1
    Z = H @ W2 + b2
    E = np.exp(Z - Z.max(1, keepdims=True))
    return E / E.sum(1, keepdims=True)
''',
        '''import numpy as np
def mlp_forward(X, W1, b1, W2, b2):
    X, W1, b1, W2, b2 = (np.asarray(a, float) for a in (X, W1, b1, W2, b2))
    H = np.maximum(0, X @ W1 + b1)
    E = np.exp(H @ W2 + b2)
    return E / E.sum(1, keepdims=True)
''',
    ],
    guide=dict(
        prereqs="Matrix multiplication (Math, lesson 1); MLPs (Supervised, lesson 4); softmax problem.",
        intuition=r"""Each layer is a linear map followed by a nonlinearity. Without the ReLU, two linear layers collapse
into one ($XW_1W_2$ is still linear), so the hidden activation is what lets the network bend decision
boundaries. Using row-major batches ($n\times d$ times $d\times h$) computes all examples at once.""",
        hints=[
            "Bias vectors broadcast across rows: `X @ W1 + b1` has shape (n, h).",
            "`np.maximum(0, ...)` is ReLU.",
            "Subtract the row max before `exp`.",
        ],
        brute_force="Looping over examples and neurons is the same arithmetic with Python overhead.",
        approach=r"""1. `A1 = X @ W1 + b1` → shape (n, h).
2. `H = max(0, A1)`.
3. `Z = H @ W2 + b2` → (n, k); subtract the row max; exponentiate; normalise rows.

Example: `W1=[[1,0],[0,-1]]` stores weights as (in, out), so $xW_1 = 1\cdot(1,0) + 2\cdot(0,-1) = (1,-2)$.
ReLU gives $(1,0)$; with $W_2=I$ the logits are $(1,0)$ and softmax gives $(e/(e+1),\,1/(e+1)) = (0.7311, 0.2689)$.
The second hidden unit is "dead" for this input — its gradient will be zero too.""",
        complexity="O(n·d·h + n·h·k) time; O(n·(h+k)) memory for activations.",
        pitfalls=r"""- Forgetting the activation (network becomes linear).
- Overflowing softmax for large logits (last test).
- Mixing up $W$ layouts: here weights are (in, out); PyTorch's `nn.Linear` stores (out, in) and computes $xW^\top$.""",
        follow_up="Add a second hidden layer, or swap ReLU for tanh/GELU. Then implement the backward pass (next problem).",
    ),
),

# ---------------------------------------------------------------- MLP backprop
dict(
    id="ml-mlp-backprop",
    title="Backpropagation for a Two-Layer MLP",
    difficulty="Hard",
    pattern="Neural Networks",
    kind="function",
    entry="mlp_grads",
    compare="float",
    tolerance=1e-6,
    description=r"""
Same network as **ml-mlp-forward** (ReLU hidden layer, softmax output). With integer class labels `y`
(values in $0..k-1$), the loss is the mean cross-entropy

$$L = -\frac1n\sum_{i=1}^n \log P_{i,y_i}.$$

Return `[L, dW1, db1, dW2, db2]` — the loss and the gradients with the same shapes as the parameters (nested
lists). Use the convention $\text{ReLU}'(0)=0$.

You can verify your gradients numerically with central differences
$\frac{L(\theta+\epsilon)-L(\theta-\epsilon)}{2\epsilon}$ — a **gradient check**.

**Example:** `X=[[1,2]], y=[0], W1=[[1,-1],[0,1]], b1=[0,0], W2=[[1,0],[0,1]], b2=[0,0]` → loss `0.6931` and gradients.
""",
    starter='''import numpy as np

def mlp_grads(X, y, W1, b1, W2, b2):
    """Return [loss, dW1, db1, dW2, db2]."""
    pass
''',
    solution='''import numpy as np

def mlp_grads(X, y, W1, b1, W2, b2):
    X, W1, b1, W2, b2 = (np.asarray(a, dtype=float) for a in (X, W1, b1, W2, b2))
    y = np.asarray(y, dtype=int)
    n = X.shape[0]
    # forward
    A1 = X @ W1 + b1
    H = np.maximum(0.0, A1)
    Z = H @ W2 + b2
    Z = Z - Z.max(axis=1, keepdims=True)
    logP = Z - np.log(np.exp(Z).sum(axis=1, keepdims=True))
    P = np.exp(logP)
    loss = -logP[np.arange(n), y].mean()
    # backward
    dZ = P.copy()
    dZ[np.arange(n), y] -= 1.0
    dZ /= n                              # dL/dZ
    dW2 = H.T @ dZ
    db2 = dZ.sum(axis=0)
    dH = dZ @ W2.T
    dA1 = dH * (A1 > 0)
    dW1 = X.T @ dA1
    db1 = dA1.sum(axis=0)
    return [float(loss), dW1, db1, dW2, db2]
''',
    tests=[
        [[[1, 2]], [0], [[1, -1], [0, 1]], [0, 0], [[1, 0], [0, 1]], [0, 0]],
        [[[1, 2]], [1], [[1, -1], [0, 1]], [0, 0], [[1, 0], [0, 1]], [0, 0]],
        [[[1, 0], [0, 1], [1, 1]], [0, 1, 1], [[2, 0, -1], [0, 2, 1]], [0.5, -0.5, 0], [[1, 0], [0, 1], [1, 1]], [0, 0.1]],
        [[[-1, -1]], [1], [[1, 1], [1, 1]], [0, 0], [[5, -5], [1, 2]], [1, 0]],
        [[[3]], [2], [[2]], [-1], [[1, 2, 3]], [0, 0, 0]],
        [[[0.5, -0.2, 0.1], [0.3, 0.8, -0.5]], [2, 0], [[0.1, 0.2], [-0.3, 0.4], [0.5, -0.6]], [0.01, -0.02],
         [[0.7, -0.1, 0.2], [0.05, 0.3, -0.4]], [0.0, 0.1, -0.1]],
        (lambda p: [p[0], [int(v) for v in _rng.randint(0, 3, 6)]] + p[1:])(list(_mlp_params(4, 5, 3, 6))),
        (lambda p: [p[0], [int(v) for v in _rng.randint(0, 4, 20)]] + p[1:])(list(_mlp_params(8, 10, 4, 20))),
        (lambda p: [p[0], [int(v) for v in _rng.randint(0, 2, 12)]] + p[1:])(list(_mlp_params(3, 7, 2, 12))),
        (lambda p: [p[0], [int(v) for v in _rng.randint(0, 5, 32)]] + p[1:])(list(_mlp_params(6, 12, 5, 32))),
    ],
    wrong_solutions=[
        '''import numpy as np
def mlp_grads(X, y, W1, b1, W2, b2):
    X, W1, b1, W2, b2 = (np.asarray(a, float) for a in (X, W1, b1, W2, b2)); y = np.asarray(y); n = len(y)
    A1 = X @ W1 + b1; H = np.maximum(0, A1); Z = H @ W2 + b2
    P = np.exp(Z - Z.max(1, keepdims=True)); P /= P.sum(1, keepdims=True)
    loss = -np.log(P[np.arange(n), y]).mean()
    dZ = P.copy(); dZ[np.arange(n), y] -= 1; dZ /= n
    dH = dZ @ W2.T          # bug: no ReLU mask
    return [float(loss), X.T @ dH, dH.sum(0), H.T @ dZ, dZ.sum(0)]
''',
        '''import numpy as np
def mlp_grads(X, y, W1, b1, W2, b2):
    X, W1, b1, W2, b2 = (np.asarray(a, float) for a in (X, W1, b1, W2, b2)); y = np.asarray(y); n = len(y)
    A1 = X @ W1 + b1; H = np.maximum(0, A1); Z = H @ W2 + b2
    P = np.exp(Z - Z.max(1, keepdims=True)); P /= P.sum(1, keepdims=True)
    loss = -np.log(P[np.arange(n), y]).mean()
    dZ = P.copy(); dZ[np.arange(n), y] -= 1      # bug: forgot to divide by n
    dA1 = (dZ @ W2.T) * (A1 > 0)
    return [float(loss), X.T @ dA1, dA1.sum(0), H.T @ dZ, dZ.sum(0)]
''',
    ],
    guide=dict(
        prereqs="Chain rule and Jacobians (Math, lesson 2); MLPs and backprop (Supervised, lesson 4).",
        intuition=r"""Backprop is the chain rule applied layer by layer, from the loss backwards, reusing the values
stored during the forward pass. Each layer receives $\partial L/\partial(\text{its output})$ and produces
(a) gradients for its parameters and (b) $\partial L/\partial(\text{its input})$ to pass further back.""",
        hints=[
            "Softmax + cross-entropy combine into a very simple gradient: dL/dZ = (P − Y_onehot) / n.",
            "For a linear layer out = in @ W + b: dW = in.T @ dout, db = dout.sum(0), din = dout @ W.T.",
            "ReLU backward: multiply the incoming gradient by (pre-activation > 0).",
        ],
        brute_force=r"Numerical differentiation of every parameter: 2 forward passes per parameter, O(#params × forward cost). Use it only to **check** backprop: relative error $\frac{|g_{num}-g_{ana}|}{|g_{num}|+|g_{ana}|}$ should be ~1e-7.",
        approach=r"""Forward: $A_1 = XW_1+b_1$, $H=\max(0,A_1)$, $Z=HW_2+b_2$, $P=\operatorname{softmax}(Z)$.

Backward:
1. $dZ = (P - Y)/n$
2. $dW_2 = H^\top dZ$, $db_2 = \sum_i dZ_i$
3. $dH = dZ\,W_2^\top$
4. $dA_1 = dH \odot \mathbb 1[A_1>0]$
5. $dW_1 = X^\top dA_1$, $db_1 = \sum_i dA_{1,i}$

Shape check is your best debugging tool: every gradient must match its parameter's shape.""",
        complexity="Backward costs about 2× the forward pass: O(n·d·h + n·h·k).",
        pitfalls=r"""- Forgetting the 1/n from the mean.
- Forgetting the ReLU mask, or using the post-activation $H$ instead of $A_1$ (identical masks for ReLU, but not for other activations).
- Computing log(softmax) naively; use log-sum-exp.""",
        follow_up="Add L2 weight decay (dW += λW), or implement the same network in PyTorch and compare with `loss.backward()`.",
    ),
),
]
