import random as _random

_r = _random.Random(404)


def _linear_data(n, coefs, noise):
    X, y = [], []
    for _ in range(n):
        row = [round(_r.uniform(-5, 5), 3) for _ in coefs[1:]]
        X.append(row)
        y.append(round(coefs[0] + sum(c * v for c, v in zip(coefs[1:], row)) + _r.gauss(0, noise), 4))
    return X, y


_X1, _y1 = _linear_data(60, [3.0, 2.0], 1.0)
_X3, _y3 = _linear_data(200, [10.0, -1.5, 0.5, 4.0], 2.0)
_Xs, _ys = _linear_data(40, [1.0, 0.8], 0.5)

PROBLEMS = [
# ---------------------------------------------------------------- OLS
dict(
    id="stats-ols-normal-equations",
    title="OLS Coefficients from the Normal Equations",
    difficulty="Medium",
    pattern="Linear Regression",
    kind="function",
    entry="ols",
    compare="float",
    tolerance=1e-5,
    description=r"""
Fit ordinary least squares **with an intercept**. `X` is a list of rows (one row of `p` predictor values per record,
no intercept column) and `y` the responses. Return `[b0, b1, ..., bp]`, the coefficients minimising the residual sum of
squares, by solving the **normal equations** $(A^\top A)\,b = A^\top y$ where $A$ is `X` with a leading column of ones.

Constraints: `n > p`, and $A^\top A$ is invertible (no perfectly collinear columns).

**Example:** `X = [[1], [2], [3], [4]], y = [3, 5, 7, 9]` → `[1.0, 2.0]`

**Example:** `X = [[0, 1], [1, 0], [1, 1], [2, 1]], y = [1, 2, 3, 4]` → `[0.5, 1.5, 0.6666667]` (approximately)
""",
    starter='''import numpy as np

def ols(X, y):
    pass
''',
    solution='''import numpy as np

def ols(X, y):
    X = np.asarray(X, dtype=float)
    A = np.column_stack([np.ones(len(X)), X])
    yv = np.asarray(y, dtype=float)
    return np.linalg.solve(A.T @ A, A.T @ yv).tolist()
''',
    tests=[
        [[[1], [2], [3], [4]], [3, 5, 7, 9]],
        [[[0, 1], [1, 0], [1, 1], [2, 1]], [1, 2, 3, 4]],
        [[[1], [2], [3]], [2, 2, 2]],
        [[[0], [1]], [5, 3]],
        [[[1, 1], [2, 1], [3, 2], [4, 3], [5, 5]], [2.0, 3.1, 5.2, 6.8, 9.9]],
        [_X1, _y1],
        [_X3, _y3],
    ],
    examples=2,
    wrong_solutions=[
        '''import numpy as np

def ols(X, y):
    X = np.asarray(X, dtype=float)
    b = np.linalg.solve(X.T @ X, X.T @ np.asarray(y, dtype=float))
    return [0.0] + b.tolist()
''',
    ],
    guide=dict(
        prereqs="Least squares and multiple regression (lessons *Simple linear regression* and *Multiple regression*); matrix multiplication in NumPy.",
        intuition=r"""At the least-squares solution the residual vector is perpendicular to every column of the design matrix, which
gives $A^\top(y - Ab) = 0$, i.e. the normal equations. Adding a column of ones lets the plane float up and down
(the intercept).""",
        hints=[
            "Build A with np.column_stack([np.ones(n), X]).",
            "Compute A.T @ A and A.T @ y.",
            "Use np.linalg.solve rather than inverting the matrix explicitly.",
        ],
        brute_force="Gradient descent on the RSS converges to the same answer, slowly; np.linalg.lstsq is the most numerically robust option.",
        approach=r"""Example 1: A = [[1,1],[1,2],[1,3],[1,4]]; AᵀA = [[4,10],[10,30]], Aᵀy = [24, 70]; solving gives b = [1, 2].""",
        complexity="O(n·p²) to form AᵀA plus O(p³) to solve.",
        pitfalls=r"""- Forgetting the intercept column (the line is forced through the origin).
- Inverting AᵀA with np.linalg.inv, which is less accurate than solve.
- Collinear predictors make AᵀA singular: drop or combine them, or use ridge regression.""",
        follow_up="Add a ridge penalty: solve (AᵀA + λI) b = Aᵀy, leaving the intercept unpenalised.",
    ),
),

# ---------------------------------------------------------------- R2
dict(
    id="stats-r2-adjusted",
    title="R-Squared and Adjusted R-Squared",
    difficulty="Easy",
    pattern="Linear Regression",
    kind="function",
    entry="r2_scores",
    compare="float",
    description=r"""
Given observed `y`, fitted values `y_hat` from a model with `p` predictors (plus an intercept), return `[r2, adj_r2]`:

$$R^2 = 1 - \frac{\sum (y_i - \hat y_i)^2}{\sum (y_i - \bar y)^2}, \qquad
R^2_\text{adj} = 1 - (1 - R^2)\,\frac{n - 1}{n - p - 1}$$

Constraints: `n > p + 1`, `y` is not constant.

**Example:** `y = [3, 5, 7, 9], y_hat = [3.2, 4.8, 7.1, 8.9], p = 1` → `[0.995, 0.9925]`
""",
    starter='''def r2_scores(y, y_hat, p):
    pass
''',
    solution='''def r2_scores(y, y_hat, p):
    n = len(y)
    mean = sum(y) / n
    rss = sum((a - b) ** 2 for a, b in zip(y, y_hat))
    tss = sum((a - mean) ** 2 for a in y)
    r2 = 1 - rss / tss
    return [r2, 1 - (1 - r2) * (n - 1) / (n - p - 1)]
''',
    tests=[
        [[3, 5, 7, 9], [3.2, 4.8, 7.1, 8.9], 1],
        [[1, 2, 3], [1, 2, 3], 1],
        [[1, 2, 3, 4, 5], [3, 3, 3, 3, 3], 1],
        [[1, 2, 3, 4, 5, 6], [2, 2, 2, 5, 5, 5], 2],
        [[10, 0, 10, 0], [0, 10, 0, 10], 1],
        [[2.5, 3.1, 4.7, 5.2, 6.9, 7.4, 9.0, 9.8], [2.8, 3.5, 4.3, 5.4, 6.5, 7.6, 8.7, 9.8], 3],
        [[round(_r.gauss(0, 1), 3) for _ in range(500)], [round(_r.gauss(0, 0.3), 3) for _ in range(500)], 10],
    ],
    examples=2,
    wrong_solutions=[
        '''def r2_scores(y, y_hat, p):
    n = len(y)
    mean = sum(y) / n
    rss = sum((a - b) ** 2 for a, b in zip(y, y_hat))
    tss = sum((a - mean) ** 2 for a in y)
    r2 = 1 - rss / tss
    return [r2, 1 - (1 - r2) * n / (n - p)]
''',
    ],
    guide=dict(
        prereqs="R² and adjusted R² (lesson *Multiple regression: assessment, cross-validation and model selection*).",
        intuition=r"""R² compares the model's squared errors with those of the dumbest model, predicting the mean every time. Adjusted R²
charges a fee for each predictor, so adding useless columns can lower it.""",
        hints=[
            "RSS from residuals; TSS from deviations around the mean of y.",
            "R² = 1 − RSS/TSS (it can be negative for a model worse than the mean).",
            "Adjusted uses (n − 1)/(n − p − 1).",
        ],
        brute_force="sklearn.metrics.r2_score gives R²; adjusted R² you must compute yourself.",
        approach=r"""Example: RSS = 0.04 + 0.04 + 0.01 + 0.01 = 0.10; TSS = 9 + 1 + 1 + 9 = 20; R² = 0.995;
adjusted = 1 − 0.005 × 3/2 = 0.9925.""",
        complexity="O(n).",
        pitfalls=r"""- Using n/(n − p) instead of (n − 1)/(n − p − 1).
- Assuming R² ≥ 0: predictions worse than the mean give negative values.
- Counting the intercept in p (here p excludes it).""",
        follow_up="Compute AIC = n·log(RSS/n) + 2(p + 1) and compare models with it.",
    ),
),

# ---------------------------------------------------------------- leverage and Cook
dict(
    id="stats-leverage-cooks",
    title="Leverage and Cook's Distance",
    difficulty="Hard",
    pattern="Regression Diagnostics",
    kind="function",
    entry="influence",
    compare="float",
    tolerance=1e-6,
    description=r"""
Fit simple linear regression `y ≈ b0 + b1·x` by least squares and return `[leverage, cooks]`, two lists of length `n`:

- leverage $h_i = \dfrac{1}{n} + \dfrac{(x_i - \bar x)^2}{\sum_j (x_j - \bar x)^2}$,
- residuals $e_i = y_i - \hat y_i$ and $s^2 = \sum e_i^2 / (n - 2)$,
- Cook's distance $D_i = \dfrac{e_i^2}{2 s^2}\cdot\dfrac{h_i}{(1 - h_i)^2}$ (2 = number of coefficients).

Constraints: `n >= 3`, `x` not constant, residuals not all zero, every `h_i < 1`.

**Example:** `x = [1, 2, 3, 4, 10], y = [2, 4, 6, 8, 5]` → leverage `[0.38, 0.28, 0.22, 0.2, 0.92]` and Cook's distances
`[0.4745, 0.0162, 0.0434, 0.2344, 17.25]`: the last point dominates.
""",
    starter='''def influence(x, y):
    pass
''',
    solution='''def influence(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((v - mx) ** 2 for v in x)
    b1 = sum((a - mx) * (b - my) for a, b in zip(x, y)) / sxx
    b0 = my - b1 * mx
    e = [b - (b0 + b1 * a) for a, b in zip(x, y)]
    s2 = sum(r * r for r in e) / (n - 2)
    h = [1 / n + (a - mx) ** 2 / sxx for a in x]
    d = [ei * ei / (2 * s2) * hi / (1 - hi) ** 2 for ei, hi in zip(e, h)]
    return [h, d]
''',
    tests=[
        [[1, 2, 3, 4, 10], [2, 4, 6, 8, 5]],
        [[1, 2, 3], [1, 3, 2]],
        [[0, 1, 2, 3, 4, 5], [1.1, 2.9, 5.2, 7.1, 8.8, 11.2]],
        [[0, 1, 2, 3, 4, 5], [1.1, 2.9, 5.2, 30.0, 8.8, 11.2]],
        [[-2, -1, 0, 1, 2, 8], [-4.1, -1.8, 0.2, 2.1, 3.9, 3.0]],
        [[v[0] for v in _Xs] + [25.0], _ys + [5.0]],
    ],
    examples=1,
    wrong_solutions=[
        '''def influence(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((v - mx) ** 2 for v in x)
    b1 = sum((a - mx) * (b - my) for a, b in zip(x, y)) / sxx
    b0 = my - b1 * mx
    e = [b - (b0 + b1 * a) for a, b in zip(x, y)]
    s2 = sum(r * r for r in e) / (n - 2)
    h = [(a - mx) ** 2 / sxx for a in x]
    d = [ei * ei / (2 * s2) * hi / (1 - hi) ** 2 for ei, hi in zip(e, h)]
    return [h, d]
''',
        '''def influence(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((v - mx) ** 2 for v in x)
    b1 = sum((a - mx) * (b - my) for a, b in zip(x, y)) / sxx
    b0 = my - b1 * mx
    e = [b - (b0 + b1 * a) for a, b in zip(x, y)]
    s2 = sum(r * r for r in e) / n
    h = [1 / n + (a - mx) ** 2 / sxx for a in x]
    d = [ei * ei / (2 * s2) * hi / (1 - hi) for ei, hi in zip(e, h)]
    return [h, d]
''',
    ],
    guide=dict(
        prereqs="Leverage, influence and Cook's distance (lesson *Regression diagnostics*).",
        intuition=r"""Leverage measures how far a point's x is from the centre: points far out act like a long lever and can tilt the line.
Cook's distance multiplies "how badly the point is fitted" by "how much leverage it has", estimating how much all the
fitted values would move if the point were deleted.""",
        hints=[
            "Fit b1 = Sxy/Sxx and b0 = ȳ − b1·x̄.",
            "Leverage has two parts: 1/n plus the squared distance of x from x̄ relative to Sxx. Leverages sum to 2.",
            "Use s² with n − 2 in the denominator and the factor h/(1 − h)².",
        ],
        brute_force="Refit the model n times, each time leaving one point out, and measure the change in fitted values: that is what Cook's distance summarises in closed form.",
        approach=r"""Example: x̄ = 4, Sxx = 9 + 4 + 1 + 0 + 36 = 50; leverage of x = 10 is 1/5 + 36/50 = 0.92, the lever that drags the
line from slope 2 to a much flatter one; its Cook's distance dwarfs the others.""",
        complexity="O(n).",
        pitfalls=r"""- Leaving out the 1/n term in leverage.
- Using RSS/n instead of RSS/(n − 2) for s².
- Squaring (1 − h) is essential; without it influence is understated for high-leverage points.""",
        follow_up="Generalise to multiple regression: leverages are the diagonal of the hat matrix A(AᵀA)⁻¹Aᵀ.",
    ),
),

# ---------------------------------------------------------------- Simpson
dict(
    id="stats-simpson-detect",
    title="Detect Simpson's Paradox",
    difficulty="Medium",
    pattern="Causal Reasoning",
    kind="function",
    entry="simpson",
    compare="exact",
    description=r"""
Each row is `[group, arm, successes, trials]` with `arm` either `"A"` or `"B"`; every group has exactly one row per arm,
and all `trials > 0`. Return `[within, aggregate, paradox]`:

- `within`: `"B"` if B's success rate is **strictly higher** than A's in **every** group, `"A"` if A's is strictly
  higher in every group, otherwise `"mixed"`.
- `aggregate`: compare the pooled rates (total successes / total trials per arm): `"B"`, `"A"` or `"tie"`.
- `paradox`: `True` when `within` is `"A"` or `"B"` and `aggregate` is the **other** arm.

Compare rates exactly (cross-multiplying integers avoids floating-point issues).

**Example:** `[["easy","A",810,900], ["hard","A",120,200], ["easy","B",190,200], ["hard","B",630,900]]`
→ `["B", "A", True]` (B wins in both groups, A wins overall).
""",
    starter='''def simpson(rows):
    pass
''',
    solution='''def simpson(rows):
    def cmp(sa, ta, sb, tb):
        left, right = sb * ta, sa * tb
        return "B" if left > right else "A" if left < right else "tie"
    groups = {}
    tot = {"A": [0, 0], "B": [0, 0]}
    for g, arm, s, t in rows:
        groups.setdefault(g, {})[arm] = (s, t)
        tot[arm][0] += s
        tot[arm][1] += t
    results = {cmp(*v["A"], *v["B"]) for v in groups.values()}
    within = results.pop() if len(results) == 1 and results <= {"A", "B"} else "mixed"
    aggregate = cmp(tot["A"][0], tot["A"][1], tot["B"][0], tot["B"][1])
    paradox = within in ("A", "B") and aggregate in ("A", "B") and aggregate != within
    return [within, aggregate, paradox]
''',
    tests=[
        [[["easy", "A", 810, 900], ["hard", "A", 120, 200], ["easy", "B", 190, 200], ["hard", "B", 630, 900]]],
        [[["g1", "A", 10, 100], ["g1", "B", 20, 100], ["g2", "A", 30, 100], ["g2", "B", 40, 100]]],
        [[["g1", "A", 10, 100], ["g1", "B", 5, 100], ["g2", "A", 30, 100], ["g2", "B", 40, 100]]],
        [[["x", "A", 1, 2], ["x", "B", 2, 4]]],
        [[["x", "A", 3, 4], ["x", "B", 1, 4]]],
        [[["small", "A", 81, 87], ["small", "B", 234, 270], ["large", "A", 192, 263], ["large", "B", 55, 80]]],
        [[["d1", "B", 50, 100], ["d1", "A", 45, 100], ["d2", "A", 5, 10], ["d2", "B", 600, 1000]]],
        [[["s1", "A", 2, 10], ["s1", "B", 30, 100], ["s2", "A", 90, 100], ["s2", "B", 10, 10],
          ["s3", "A", 1, 5], ["s3", "B", 5, 20]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def simpson(rows):
    tot = {"A": [0, 0], "B": [0, 0]}
    wins = []
    for g, arm, s, t in rows:
        tot[arm][0] += s
        tot[arm][1] += t
    rate = {k: v[0] / v[1] for k, v in tot.items()}
    agg = "B" if rate["B"] > rate["A"] else "A" if rate["B"] < rate["A"] else "tie"
    return [agg, agg, False]
''',
    ],
    guide=dict(
        prereqs="Simpson's paradox and confounding (lesson *Correlation, causation and Simpson's paradox*).",
        intuition=r"""An overall rate is a weighted average of group rates, weighted by how many trials each arm has in each group. If one
arm's trials are concentrated in the easy group, its pooled rate looks better even when it loses inside every group.""",
        hints=[
            "Collect (successes, trials) per group and arm, and running totals per arm.",
            "Compare sb/tb with sa/ta by checking sb·ta versus sa·tb.",
            "within is a single arm only if every group gives that same strict winner.",
        ],
        brute_force="Compute float rates and compare: fine for most inputs, but exact integer comparison avoids ties being broken by rounding.",
        approach=r"""Example: easy 0.95 (B) > 0.90 (A), hard 0.70 (B) > 0.60 (A) → within = B. Pooled: A 930/1100 = 0.845,
B 820/1100 = 0.745 → aggregate = A. Paradox: True.""",
        complexity="O(number of rows).",
        pitfalls=r"""- Treating a tie inside a group as a win.
- Comparing pooled rates by averaging group rates (that ignores the different trial counts).
- Forgetting that rows can arrive in any order.""",
        follow_up="Compute a standardised (weighted) comparison: apply both arms' group rates to a common group mix.",
    ),
),
]
