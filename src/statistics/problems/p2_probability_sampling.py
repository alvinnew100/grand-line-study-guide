import random as _random

_r = _random.Random(202)

PROBLEMS = [
# ---------------------------------------------------------------- Bayes
dict(
    id="stats-bayes-posterior",
    title="Bayes' Rule: Repeated Positive Tests",
    difficulty="Easy",
    pattern="Probability",
    kind="function",
    entry="posteriors",
    compare="float",
    description=r"""
A condition has prior probability `prior`. A test has `sensitivity` $= P(+ \mid \text{ill})$ and `specificity`
$= P(- \mid \text{healthy})$. A person takes `k` independent tests and **all are positive**. Return the list of
posterior probabilities of being ill after the 1st, 2nd, ..., k-th positive result (the posterior after each test is
the prior for the next).

Use Bayes' rule: $P(\text{ill} \mid +) = \dfrac{\text{sens} \cdot p}{\text{sens} \cdot p + (1 - \text{spec})(1 - p)}$.
If the denominator is 0, the posterior is `0.0`.

Constraints: all probabilities in `[0, 1]`, `1 <= k <= 50`.

**Example:** `prior = 0.01, sensitivity = 0.99, specificity = 0.95, k = 2` → `[0.1666666667, 0.7983870968]`
""",
    starter='''def posteriors(prior, sensitivity, specificity, k):
    pass
''',
    solution='''def posteriors(prior, sensitivity, specificity, k):
    out = []
    p = prior
    for _ in range(k):
        num = sensitivity * p
        den = num + (1 - specificity) * (1 - p)
        p = num / den if den > 0 else 0.0
        out.append(p)
    return out
''',
    tests=[
        [0.01, 0.99, 0.95, 2],
        [0.01, 0.99, 0.95, 1],
        [0.001, 0.99, 0.99, 3],
        [0.5, 0.8, 0.8, 4],
        [0.0, 0.9, 1.0, 2],
        [0.2, 0.9, 1.0, 1],
        [0.3, 0.5, 0.5, 3],
        [0.05, 0.7, 0.9, 10],
        [0.0001, 0.999, 0.999, 5],
        [1.0, 0.6, 0.7, 2],
    ],
    examples=2,
    wrong_solutions=[
        '''def posteriors(prior, sensitivity, specificity, k):
    return [sensitivity] * k
''',
        '''def posteriors(prior, sensitivity, specificity, k):
    out = []
    for _ in range(k):
        num = sensitivity * prior
        den = num + (1 - specificity) * (1 - prior)
        out.append(num / den if den else 0.0)
    return out
''',
    ],
    guide=dict(
        prereqs="Conditional probability and Bayes' rule (lesson *Probability, conditional probability and Bayes' rule*).",
        intuition=r"""A positive result from a good test for a rare condition still leaves you probably healthy, because healthy people
vastly outnumber ill ones. But each further independent positive multiplies the evidence: the posterior after one
test becomes the prior for the next, and confidence climbs quickly.""",
        hints=[
            "Keep a running probability p, starting at the prior.",
            "Update with Bayes' rule each time and append the new p.",
            "Guard against a zero denominator (prior 0 and specificity 1).",
        ],
        brute_force="Simulate a million people and count: approximate, slow, and noisy. The formula is exact.",
        approach=r"""Prior 0.01: after test 1, 0.99 × 0.01 / (0.0099 + 0.05 × 0.99) = 0.0099 / 0.0594 = 0.1667. After test 2 with prior
0.1667: 0.165 / (0.165 + 0.05 × 0.8333) = 0.7984.""",
        complexity="O(k) time, O(k) space.",
        pitfalls=r"""- Forgetting to feed each posterior back in as the next prior.
- Using specificity instead of 1 − specificity for the false-positive rate.
- Assuming independence of repeated tests: in reality the same person can trigger the same false positive twice.""",
        follow_up="Generalise to a mix of positive and negative results; a negative uses P(− | ill) = 1 − sensitivity.",
    ),
),

# ---------------------------------------------------------------- binomial tail
dict(
    id="stats-binomial-tail",
    title="Binomial Tail Probability",
    difficulty="Easy",
    pattern="Probability Distributions",
    kind="function",
    entry="binom_tail",
    compare="float",
    description=r"""
`n` independent trials each succeed with probability `p`. Return the exact probability of **at least `k` successes**,
$P(X \ge k) = \sum_{i=k}^{n} \binom{n}{i} p^i (1-p)^{n-i}$.

Constraints: `0 <= n <= 2000`, `0 <= p <= 1`, `0 <= k <= n + 1` (so the answer can be 1 or 0).

**Example:** `n = 10, p = 0.2, k = 5` → `0.0327934976`

**Example:** `n = 10, p = 0.2, k = 0` → `1.0`
""",
    starter='''def binom_tail(n, p, k):
    pass
''',
    solution='''import math

def binom_tail(n, p, k):
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    total = 0.0
    for i in range(k, n + 1):
        total += math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i))
    return min(total, 1.0)
''',
    tests=[
        [10, 0.2, 5],
        [10, 0.2, 0],
        [10, 0.2, 11],
        [1, 0.3, 1],
        [20, 0.5, 15],
        [100, 0.05, 10],
        [40, 0.02, 3],
        [50, 0.0, 1],
        [50, 1.0, 50],
        [365, 0.01, 8],
        [1000, 0.05, 64],
    ],
    examples=2,
    wrong_solutions=[
        '''import math

def binom_tail(n, p, k):
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1, n + 1))
''',
    ],
    guide=dict(
        prereqs="The binomial distribution (lesson *Binomial, Poisson and other common distributions*).",
        intuition=r"""Each way of getting exactly i successes has probability p^i (1 − p)^(n − i), and there are C(n, i) such ways.
"At least k" means adding those exact probabilities for i = k, ..., n.""",
        hints=[
            "math.comb(n, i) gives the binomial coefficient.",
            "Sum from i = k up to n inclusive.",
            "Handle k <= 0 (answer 1) and k > n (answer 0).",
        ],
        brute_force="Enumerate all 2^n outcome sequences: impossible beyond n ≈ 25.",
        approach=r"""n = 10, p = 0.2, k = 5: P(5) + ... + P(10) = 0.02642 + 0.00551 + 0.00079 + 0.00007 + ... ≈ 0.03279.""",
        complexity="O(n) terms, each O(1) with Python's big-integer comb (O(n) arithmetic in practice).",
        pitfalls=r"""- Off-by-one: "at least k" includes k (scipy's sf(k − 1)).
- Normal approximation instead of the exact sum: poor for small np.
- Summing the complement when k is small is faster: 1 − P(X ≤ k − 1).""",
        follow_up="Compute the same tail with the Poisson approximation λ = np and compare when n is large and p small.",
    ),
),

# ---------------------------------------------------------------- bootstrap CI
dict(
    id="stats-bootstrap-ci",
    title="Bootstrap Percentile Interval (Seeded)",
    difficulty="Medium",
    pattern="Resampling",
    kind="function",
    entry="bootstrap_ci",
    compare="float",
    description=r"""
Compute a bootstrap percentile confidence interval for the **mean** of `data`, following these exact steps so the
answer is reproducible:

1. `rng = numpy.random.default_rng(seed)`.
2. `idx = rng.integers(0, n, size=(B, n))` where `n = len(data)`: row `b` holds the positions of resample `b`.
3. Compute the mean of each resample: `means[b] = mean(data[idx[b]])`.
4. Return `[lo, hi]`, the `100·alpha/2` and `100·(1 − alpha/2)` percentiles of `means` using **linear interpolation**
   (`numpy.percentile`'s default).

Constraints: `2 <= n <= 500`, `100 <= B <= 5000`, `0 < alpha < 1`.

**Example:** `data = [3, 7, 8, 12, 15, 21, 30], B = 1000, seed = 0, alpha = 0.05` → a list of two numbers, roughly
`[7.9, 20.1]` (exact values come from the seeded generator).
""",
    starter='''import numpy as np

def bootstrap_ci(data, B, seed, alpha):
    pass
''',
    solution='''import numpy as np

def bootstrap_ci(data, B, seed, alpha):
    x = np.asarray(data, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(B, len(x)))
    means = x[idx].mean(axis=1)
    lo, hi = np.percentile(means, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return [float(lo), float(hi)]
''',
    tests=[
        [[3, 7, 8, 12, 15, 21, 30], 1000, 0, 0.05],
        [[1, 2], 200, 1, 0.1],
        [[5, 5, 5, 5], 500, 2, 0.05],
        [[0, 0, 0, 1, 0, 1, 0, 0, 1, 0], 2000, 3, 0.05],
        [[-4.5, 2.0, 3.25, 10.0, -1.0, 0.5], 1500, 4, 0.2],
        [[round(_r.lognormvariate(3, 1), 2) for _ in range(60)], 3000, 5, 0.05],
        [[_r.randint(0, 100) for _ in range(300)], 1000, 6, 0.01],
        [[round(_r.gauss(50, 10), 3) for _ in range(40)], 5000, 7, 0.1],
    ],
    examples=1,
    wrong_solutions=[
        '''import numpy as np

def bootstrap_ci(data, B, seed, alpha):
    x = np.asarray(data, dtype=float)
    rng = np.random.default_rng(seed)
    means = [rng.choice(x, len(x), replace=False).mean() for _ in range(B)]
    lo, hi = np.percentile(means, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return [float(lo), float(hi)]
''',
        '''import numpy as np

def bootstrap_ci(data, B, seed, alpha):
    x = np.asarray(data, dtype=float)
    se = x.std(ddof=1) / np.sqrt(len(x))
    return [float(x.mean() - 1.96 * se), float(x.mean() + 1.96 * se)]
''',
    ],
    guide=dict(
        prereqs="The bootstrap and percentile intervals (lesson *The bootstrap*).",
        intuition=r"""Treat the sample as a stand-in for the population and draw many samples of the same size from it *with replacement*.
The spread of the resampled means approximates the sampling distribution of the mean; its middle 1 − alpha share is
the interval.""",
        hints=[
            "Convert data to a NumPy float array so you can index it with an integer array.",
            "x[idx] with idx of shape (B, n) gives all resamples at once; .mean(axis=1) gives B means.",
            "np.percentile(means, [100*alpha/2, 100*(1-alpha/2)]) returns both bounds.",
        ],
        brute_force="A Python loop over B resamples works too, as long as you draw indices with exactly the same call: rng.integers(0, n, size=(B, n)).",
        approach=r"""The single call `rng.integers(0, n, size=(B, n))` fixes every random index, so any correct implementation that follows
the steps reproduces the reference exactly. Then vectorised indexing and a percentile.""",
        complexity="O(B·n) time and memory for the index table.",
        pitfalls=r"""- Sampling without replacement (every resample is then the original data and the interval collapses).
- Drawing random numbers in a different order or with a different generator: the result will differ from the reference.
- Using a normal-theory interval (mean ± 1.96 SE) instead of percentiles.""",
        follow_up="Replace the mean with the median, or resample whole users for a ratio metric (the cluster bootstrap).",
    ),
),

# ---------------------------------------------------------------- Wilson interval
dict(
    id="stats-wilson-interval",
    title="Wilson Score Interval",
    difficulty="Medium",
    pattern="Confidence Intervals",
    kind="function",
    entry="wilson",
    compare="float",
    description=r"""
Return the **Wilson score interval** `[lo, hi]` for a proportion with `successes` out of `n` trials and critical value `z`
(1.96 for 95%). With $\hat p = \text{successes}/n$:

$$\text{centre} = \frac{\hat p + \frac{z^2}{2n}}{1 + \frac{z^2}{n}}, \qquad
\text{half} = \frac{z\sqrt{\frac{\hat p(1-\hat p)}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}$$

and the interval is `[centre − half, centre + half]`. Unlike the Wald interval it never leaves `[0, 1]` and is
sensible when `successes` is 0 or `n`.

Constraints: `n >= 1`, `0 <= successes <= n`, `z > 0`.

**Example:** `successes = 3, n = 100, z = 1.96` → `[0.0102543, 0.0845208]`

**Example:** `successes = 0, n = 50, z = 1.96` → `[0.0, 0.0713500]`
""",
    starter='''import math

def wilson(successes, n, z):
    pass
''',
    solution='''import math

def wilson(successes, n, z):
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return [max(0.0, centre - half), min(1.0, centre + half)]
''',
    tests=[
        [3, 100, 1.96],
        [0, 50, 1.96],
        [50, 50, 1.96],
        [480, 10000, 1.96],
        [1, 1, 1.96],
        [5, 10, 2.576],
        [245, 2000, 1.645],
        [7, 20, 1.0],
        [999, 1000, 3.29],
        [12345, 100000, 1.96],
    ],
    examples=2,
    wrong_solutions=[
        '''import math

def wilson(successes, n, z):
    p = successes / n
    half = z * math.sqrt(p * (1 - p) / n)
    return [max(0.0, p - half), min(1.0, p + half)]
''',
    ],
    guide=dict(
        prereqs="Confidence intervals for proportions, Wald versus Wilson (lesson *Confidence intervals done right*).",
        intuition=r"""The Wald interval plugs the observed proportion into the standard error, which collapses to zero width when you see
0 or n successes. Wilson instead asks which true proportions would make the observed count unsurprising, which pulls
the centre slightly toward 1/2 and keeps a sensible width at the extremes.""",
        hints=[
            "Compute p_hat, then the common denominator 1 + z²/n.",
            "Centre and half-width follow the formulas directly.",
            "Clamp to [0, 1] only to guard against tiny floating-point overshoots.",
        ],
        brute_force="Search a grid of candidate p values for those where |p_hat − p| <= z·sqrt(p(1 − p)/n): this is what Wilson solves in closed form.",
        approach=r"""3/100: p = 0.03, denom = 1.038416, centre = (0.03 + 0.019208)/1.038416 = 0.047388, half ≈ 0.037135,
interval ≈ (0.01025, 0.08452).""",
        complexity="O(1).",
        pitfalls=r"""- Using the Wald formula, which gives (0, 0) for 0/50.
- Forgetting the z²/(4n²) term inside the square root.
- Dividing only the centre (or only the half-width) by the denominator.""",
        follow_up="Simulate the coverage of Wald and Wilson intervals at p = 0.02, n = 100 to see why Wilson is preferred.",
    ),
),
]
