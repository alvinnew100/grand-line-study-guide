import random as _random

_r = _random.Random(303)


def _norm(n, mu, sd):
    return [round(_r.gauss(mu, sd), 2) for _ in range(n)]


PROBLEMS = [
# ---------------------------------------------------------------- exact permutation test
dict(
    id="stats-permutation-exact",
    title="Exact Permutation Test",
    difficulty="Medium",
    pattern="Hypothesis Testing",
    kind="function",
    entry="permutation_pvalue",
    compare="float",
    description=r"""
Two small groups `a` (control) and `b` (treatment) were randomly assigned. Test whether `b` has a larger mean with an
**exhaustive permutation test**:

1. The observed statistic is `mean(b) - mean(a)`.
2. Pool all `n_a + n_b` values. For **every** way of choosing which `n_b` positions of the pooled list form the
   treatment group (the rest form the control group), compute the same statistic.
3. Return the share of these splits whose statistic is **at least** the observed one (use a tolerance:
   count a split if `stat >= observed - 1e-9`).

Constraints: `1 <= n_a, n_b` and `n_a + n_b <= 16`.

**Example:** `a = [12, 15, 11, 14], b = [16, 18, 13, 19]` → `0.0571428571` (4 of the 70 splits).
""",
    starter='''from itertools import combinations

def permutation_pvalue(a, b):
    pass
''',
    solution='''from itertools import combinations

def permutation_pvalue(a, b):
    pooled = list(a) + list(b)
    n, nb = len(pooled), len(b)
    total_sum = sum(pooled)
    observed = sum(b) / nb - sum(a) / len(a)
    count = total = 0
    for idx in combinations(range(n), nb):
        sb = sum(pooled[i] for i in idx)
        stat = sb / nb - (total_sum - sb) / (n - nb)
        total += 1
        if stat >= observed - 1e-9:
            count += 1
    return count / total
''',
    tests=[
        [[12, 15, 11, 14], [16, 18, 13, 19]],
        [[1, 2, 3], [4, 5, 6]],
        [[4, 5, 6], [1, 2, 3]],
        [[5, 5, 5], [5, 5]],
        [[3], [7]],
        [[10, 12, 9, 11, 10], [11, 13, 12]],
        [[1.5, 2.25, 0.5, 3.0], [2.0, 2.75, 3.5, 1.0]],
        [[20, 22, 19, 25, 21, 18, 23, 24], [26, 21, 27, 24, 28, 22, 25, 29]],
        [[0, 0, 1, 0, 0, 1, 0], [1, 1, 0, 1, 1, 0, 1]],
    ],
    examples=2,
    wrong_solutions=[
        '''from itertools import combinations

def permutation_pvalue(a, b):
    pooled = list(a) + list(b)
    n, nb = len(pooled), len(b)
    observed = sum(b) / nb - sum(a) / len(a)
    count = total = 0
    for idx in combinations(range(n), nb):
        sb = sum(pooled[i] for i in idx)
        stat = sb / nb - (sum(pooled) - sb) / (n - nb)
        total += 1
        if stat > observed + 1e-9:
            count += 1
    return count / total
''',
        '''from itertools import combinations

def permutation_pvalue(a, b):
    pooled = list(a) + list(b)
    n, nb = len(pooled), len(b)
    observed = abs(sum(b) / nb - sum(a) / len(a))
    count = total = 0
    for idx in combinations(range(n), nb):
        sb = sum(pooled[i] for i in idx)
        stat = abs(sb / nb - (sum(pooled) - sb) / (n - nb))
        total += 1
        if stat >= observed - 1e-9:
            count += 1
    return count / total
''',
    ],
    guide=dict(
        prereqs="Permutation tests (lesson *A/B tests, hypotheses and permutation tests*).",
        intuition=r"""If the treatment did nothing, every value would have been the same whichever group it landed in, so every split of
the pooled values into groups of these sizes was equally likely. The p-value is the share of those equally likely
splits that look at least as favourable to the treatment as what actually happened.""",
        hints=[
            "itertools.combinations(range(n), n_b) lists every choice of treatment positions.",
            "The treatment sum determines the statistic: control sum = total − treatment sum.",
            "Count ties as 'at least as extreme' (use a small tolerance for floating point).",
        ],
        brute_force="Enumerating all permutations of the pooled list (n! orders) repeats each split many times; combinations visit each split once.",
        approach=r"""For `a = [12, 15, 11, 14]`, `b = [16, 18, 13, 19]`: observed = 16.5 − 13 = 3.5. Of the C(8, 4) = 70 splits,
4 have a treatment-minus-control difference of at least 3.5, so p = 4/70 ≈ 0.057.""",
        complexity="O(C(n, n_b) · n_b) time; C(16, 8) = 12,870 splits at most here.",
        pitfalls=r"""- Using `>` and missing ties, which makes the p-value too small.
- Computing a two-sided statistic (absolute difference) when the question is one-sided.
- Float equality: sums of decimals may differ in the last bit, hence the tolerance.""",
        follow_up="For larger samples, replace enumeration by a few thousand random shuffles (a Monte Carlo permutation test).",
    ),
),

# ---------------------------------------------------------------- two-proportion z
dict(
    id="stats-two-proportion-ztest",
    title="Two-Proportion Z-Test",
    difficulty="Easy",
    pattern="Hypothesis Testing",
    kind="function",
    entry="two_prop_z",
    compare="float",
    description=r"""
Control converts `x1` of `n1` users, treatment `x2` of `n2`. Return `[z, p_value]` for the two-sided two-proportion
z-test of equal rates, using the **pooled** rate $\hat p = (x_1 + x_2)/(n_1 + n_2)$:

$$z = \frac{x_2/n_2 - x_1/n_1}{\sqrt{\hat p(1 - \hat p)(1/n_1 + 1/n_2)}}, \qquad
p = 2\,P(Z > |z|) = \operatorname{erfc}(|z|/\sqrt 2)$$

If the pooled rate is 0 or 1 (no variation at all), return `[0.0, 1.0]`.

**Example:** `x1 = 200, n1 = 2000, x2 = 245, n2 = 2000` → `[2.2628, 0.02365]` (approximately).
""",
    starter='''import math

def two_prop_z(x1, n1, x2, n2):
    pass
''',
    solution='''import math

def two_prop_z(x1, n1, x2, n2):
    pool = (x1 + x2) / (n1 + n2)
    if pool <= 0 or pool >= 1:
        return [0.0, 1.0]
    se = math.sqrt(pool * (1 - pool) * (1 / n1 + 1 / n2))
    z = (x2 / n2 - x1 / n1) / se
    return [z, math.erfc(abs(z) / math.sqrt(2))]
''',
    tests=[
        [200, 2000, 245, 2000],
        [1000, 20000, 1090, 20000],
        [480, 10000, 540, 10000],
        [50, 100, 50, 100],
        [30, 100, 20, 100],
        [0, 500, 0, 500],
        [10, 10, 10, 10],
        [3, 40, 9, 35],
        [100000, 1000000, 101000, 1000000],
        [12, 1000, 30, 1500],
    ],
    examples=2,
    wrong_solutions=[
        '''import math

def two_prop_z(x1, n1, x2, n2):
    p1, p2 = x1 / n1, x2 / n2
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    if se == 0:
        return [0.0, 1.0]
    z = (p2 - p1) / se
    return [z, math.erfc(abs(z) / math.sqrt(2))]
''',
        '''import math

def two_prop_z(x1, n1, x2, n2):
    pool = (x1 + x2) / (n1 + n2)
    if pool <= 0 or pool >= 1:
        return [0.0, 1.0]
    se = math.sqrt(pool * (1 - pool) * (1 / n1 + 1 / n2))
    z = (x2 / n2 - x1 / n1) / se
    return [z, 0.5 * math.erfc(abs(z) / math.sqrt(2))]
''',
    ],
    guide=dict(
        prereqs="The two-proportion z-test (lesson *t-tests, z-tests and degrees of freedom*).",
        intuition=r"""Under the null hypothesis both groups share one conversion rate, best estimated by pooling everyone. The z statistic
is the observed difference measured in standard errors; the p-value is the two-tailed normal area beyond it.""",
        hints=[
            "Pooled rate = total conversions / total users.",
            "SE = sqrt(pool·(1 − pool)·(1/n1 + 1/n2)).",
            "Two-sided p = math.erfc(|z| / sqrt(2)); no SciPy needed.",
        ],
        brute_force="A permutation test on the 0/1 outcomes gives nearly the same p-value but costs thousands of shuffles.",
        approach=r"""200/2000 vs 245/2000: pool = 445/4000 = 0.11125; SE = sqrt(0.11125 × 0.88875 × 0.001) = 0.009944;
z = 0.0225 / 0.009944 = 2.263; p = erfc(2.263/1.4142) ≈ 0.0236.""",
        complexity="O(1).",
        pitfalls=r"""- Using the unpooled SE (that belongs to the confidence interval, not the test).
- Reporting a one-sided p-value (half of the two-sided one).
- Dividing by zero when nobody (or everybody) converted.""",
        follow_up="Add the 95% confidence interval for the difference using the unpooled standard error.",
    ),
),

# ---------------------------------------------------------------- Welch t
dict(
    id="stats-welch-t",
    title="Welch's t Statistic and Degrees of Freedom",
    difficulty="Medium",
    pattern="Hypothesis Testing",
    kind="function",
    entry="welch_t",
    compare="float",
    description=r"""
Return `[t, df]` for Welch's two-sample t-test comparing `b` with `a` (statistic positive when `b`'s mean is larger):

$$t = \frac{\bar b - \bar a}{\sqrt{v_a + v_b}}, \quad v_a = \frac{s_a^2}{n_a},\ v_b = \frac{s_b^2}{n_b}, \qquad
df = \frac{(v_a + v_b)^2}{\frac{v_a^2}{n_a - 1} + \frac{v_b^2}{n_b - 1}}$$

where $s^2$ is the sample variance with divisor $n - 1$.

Constraints: `n_a, n_b >= 2`, and at least one group has non-zero variance.

**Example:** `a = [12.1, 9.8, 11.4, 10.2, 13.0, 9.5, 10.8, 11.9, 10.1, 12.4]`,
`b = [13.5, 12.2, 14.8, 11.9, 15.1, 12.7, 13.9, 16.0]` → `[4.106, 13.59]` (approximately).
""",
    starter='''def welch_t(a, b):
    pass
''',
    solution='''def welch_t(a, b):
    def mv(x):
        n = len(x)
        m = sum(x) / n
        return m, sum((v - m) ** 2 for v in x) / (n - 1), n
    ma, sa, na = mv(a)
    mb, sb, nb = mv(b)
    va, vb = sa / na, sb / nb
    t = (mb - ma) / (va + vb) ** 0.5
    df = (va + vb) ** 2 / (va ** 2 / (na - 1) + vb ** 2 / (nb - 1))
    return [t, df]
''',
    tests=[
        [[12.1, 9.8, 11.4, 10.2, 13.0, 9.5, 10.8, 11.9, 10.1, 12.4], [13.5, 12.2, 14.8, 11.9, 15.1, 12.7, 13.9, 16.0]],
        [[1, 2, 3, 4], [2, 3, 4, 5]],
        [[5, 5, 5], [4, 6, 8]],
        [[1, 3], [2, 4]],
        [[10, 20, 30, 40, 50], [11, 12]],
        [[-1.5, 0.5, 2.0, -0.25], [3.0, 2.5, 4.0, 5.5, 1.0]],
        [_norm(40, 0, 1), _norm(10, 0, 4)],
        [_norm(500, 100, 15), _norm(700, 102, 20)],
    ],
    examples=1,
    wrong_solutions=[
        '''def welch_t(a, b):
    na, nb = len(a), len(b)
    ma, mb = sum(a) / na, sum(b) / nb
    sa = sum((v - ma) ** 2 for v in a) / (na - 1)
    sb = sum((v - mb) ** 2 for v in b) / (nb - 1)
    sp = ((na - 1) * sa + (nb - 1) * sb) / (na + nb - 2)
    t = (mb - ma) / (sp * (1 / na + 1 / nb)) ** 0.5
    return [t, na + nb - 2]
''',
    ],
    guide=dict(
        prereqs="Welch's t-test and degrees of freedom (lesson *t-tests, z-tests and degrees of freedom*).",
        intuition=r"""The t statistic is a signal-to-noise ratio: the difference in means divided by its standard error. Welch's version
lets each group keep its own variance, and the Welch-Satterthwaite formula gives the (usually fractional) degrees of
freedom of the resulting t distribution.""",
        hints=[
            "Use the n − 1 divisor for each group's variance.",
            "v = variance / n for each group; SE = sqrt(v_a + v_b).",
            "Plug v_a and v_b into the df formula exactly as written.",
        ],
        brute_force="scipy.stats.ttest_ind(b, a, equal_var=False) gives t (and the p-value); computing it by hand shows you know where it comes from.",
        approach=r"""Example: means 11.12 and 13.7625; v_a = 1.4062/10, v_b = 2.0141/8; t = 2.6425 / sqrt(0.1406 + 0.2518) ≈ 4.106;
df ≈ 13.59.""",
        complexity="O(n_a + n_b).",
        pitfalls=r"""- Pooling the variances (Student's test) and using df = n_a + n_b − 2.
- Dividing variances by n instead of n − 1.
- Reversing the sign convention (b minus a here).""",
        follow_up="Turn t and df into a p-value with scipy.stats.t.sf, or approximate with the normal for large df.",
    ),
),

# ---------------------------------------------------------------- chi-square
dict(
    id="stats-chi-square",
    title="Chi-Square Test of Independence Statistic",
    difficulty="Medium",
    pattern="Hypothesis Testing",
    kind="function",
    entry="chi_square",
    compare="float",
    description=r"""
Given an `r × c` contingency table of counts (list of rows), return `[chi2, df]`:

- expected count $E_{ij} = (\text{row}_i \text{ total}) \times (\text{column}_j \text{ total}) / \text{grand total}$,
- $\chi^2 = \sum_{ij} (O_{ij} - E_{ij})^2 / E_{ij}$ (no continuity correction),
- `df = (r − 1)(c − 1)`.

Constraints: `r, c >= 2`, every row total and column total is positive.

**Example:** `[[61, 45, 72], [1439, 1455, 1428]]` → `[6.4693, 2]` (approximately).
""",
    starter='''def chi_square(table):
    pass
''',
    solution='''def chi_square(table):
    r, c = len(table), len(table[0])
    rows = [sum(row) for row in table]
    cols = [sum(table[i][j] for i in range(r)) for j in range(c)]
    total = sum(rows)
    chi2 = 0.0
    for i in range(r):
        for j in range(c):
            e = rows[i] * cols[j] / total
            chi2 += (table[i][j] - e) ** 2 / e
    return [chi2, (r - 1) * (c - 1)]
''',
    tests=[
        [[[61, 45, 72], [1439, 1455, 1428]]],
        [[[7, 1], [3, 9]]],
        [[[10, 10], [10, 10]]],
        [[[0, 5], [5, 0]]],
        [[[20, 30, 50], [30, 20, 50], [25, 25, 50]]],
        [[[1, 2, 3, 4], [4, 3, 2, 1]]],
        [[[245, 1755], [200, 1800]]],
        [[[_r.randint(1, 200) for _ in range(6)] for _ in range(5)]],
    ],
    examples=1,
    wrong_solutions=[
        '''def chi_square(table):
    r, c = len(table), len(table[0])
    total = sum(sum(row) for row in table)
    e = total / (r * c)
    chi2 = sum((x - e) ** 2 / e for row in table for x in row)
    return [chi2, (r - 1) * (c - 1)]
''',
        '''def chi_square(table):
    r, c = len(table), len(table[0])
    rows = [sum(row) for row in table]
    cols = [sum(table[i][j] for i in range(r)) for j in range(c)]
    total = sum(rows)
    chi2 = 0.0
    for i in range(r):
        for j in range(c):
            e = rows[i] * cols[j] / total
            chi2 += (table[i][j] - e) ** 2 / e
    return [chi2, r * c - 1]
''',
    ],
    guide=dict(
        prereqs="The chi-square test (lesson *ANOVA and the chi-square test*).",
        intuition=r"""If the row variable and the column variable are independent, each cell should hold its row's share of each column's
total. The statistic adds up squared surprises, each scaled by how big the cell was expected to be.""",
        hints=[
            "Compute row totals, column totals and the grand total first.",
            "Expected = row total × column total / grand total.",
            "Degrees of freedom = (r − 1)(c − 1), not r·c − 1.",
        ],
        brute_force="A resampling version shuffles outcomes across groups thousands of times; the formula gives the statistic directly.",
        approach=r"""Example: expected opens per text = 178 × 1500 / 4500 = 59.33; contributions from the 'opened' row: 0.0468 +
3.4799 + 2.7135, plus the much smaller 'not opened' contributions → about 6.47 with df = 2.""",
        complexity="O(r·c).",
        pitfalls=r"""- Using a single overall expected count for every cell.
- Applying Yates' continuity correction (not asked for here).
- Wrong degrees of freedom.""",
        follow_up="Convert the statistic to a p-value (scipy.stats.chi2.sf) and compare with Fisher's exact test on small 2×2 tables.",
    ),
),

# ---------------------------------------------------------------- ANOVA F
dict(
    id="stats-anova-f",
    title="One-Way ANOVA F Statistic",
    difficulty="Medium",
    pattern="Hypothesis Testing",
    kind="function",
    entry="anova_f",
    compare="float",
    description=r"""
Given `k >= 2` groups of numbers, return `[F, df_between, df_within]` for one-way ANOVA:

- $SS_\text{between} = \sum_j n_j (\bar x_j - \bar x)^2$, where $\bar x$ is the grand mean of all values,
- $SS_\text{within} = \sum_j \sum_i (x_{ij} - \bar x_j)^2$,
- `df_between = k − 1`, `df_within = N − k` (N = total number of values),
- $F = \dfrac{SS_\text{between}/df_\text{between}}{SS_\text{within}/df_\text{within}}$.

Constraints: each group has at least one value, `N > k`, and $SS_\text{within} > 0$.

**Example:** groups `[[12.4, 10.9, 13.8, 11.6, 12.9, 14.1], [10.2, 11.8, 9.7, 10.9, 12.3, 10.5],
[13.5, 12.1, 14.6, 13.0, 15.2, 12.8], [11.9, 12.6, 10.8, 13.3, 11.4, 12.2]]` → `[6.277, 3, 20]` (approximately).
""",
    starter='''def anova_f(groups):
    pass
''',
    solution='''def anova_f(groups):
    allv = [x for g in groups for x in g]
    N, k = len(allv), len(groups)
    grand = sum(allv) / N
    ssb = sum(len(g) * (sum(g) / len(g) - grand) ** 2 for g in groups)
    ssw = sum(sum((x - sum(g) / len(g)) ** 2 for x in g) for g in groups)
    F = (ssb / (k - 1)) / (ssw / (N - k))
    return [F, k - 1, N - k]
''',
    tests=[
        [[[12.4, 10.9, 13.8, 11.6, 12.9, 14.1], [10.2, 11.8, 9.7, 10.9, 12.3, 10.5],
          [13.5, 12.1, 14.6, 13.0, 15.2, 12.8], [11.9, 12.6, 10.8, 13.3, 11.4, 12.2]]],
        [[[1, 2, 3], [1, 2, 3]]],
        [[[1, 2, 3], [4, 5, 6], [7, 8, 9]]],
        [[[5], [6, 7], [8, 9, 10]]],
        [[[2.5, 3.5], [10.0, 12.0]]],
        [[[-1, 0, 1], [0, 1, 2], [5, 6, 7], [1, 1, 2]]],
        [[_norm(30, 50, 10), _norm(25, 52, 10), _norm(40, 49, 10)]],
        [[_norm(200, 0, 1) for _ in range(6)]],
    ],
    examples=1,
    wrong_solutions=[
        '''def anova_f(groups):
    allv = [x for g in groups for x in g]
    N, k = len(allv), len(groups)
    grand = sum(allv) / N
    ssb = sum((sum(g) / len(g) - grand) ** 2 for g in groups)
    ssw = sum(sum((x - sum(g) / len(g)) ** 2 for x in g) for g in groups)
    return [(ssb / (k - 1)) / (ssw / (N - k)), k - 1, N - k]
''',
    ],
    guide=dict(
        prereqs="One-way ANOVA (lesson *ANOVA and the chi-square test*).",
        intuition=r"""Compare two estimates of noise: how spread out the group means are (scaled by group size) and how spread out values
are within their own groups. If the groups share one mean, both estimate the same variance and F is near 1.""",
        hints=[
            "Flatten all values to get N and the grand mean.",
            "Weight each group's squared mean deviation by its size n_j.",
            "Divide each sum of squares by its degrees of freedom before taking the ratio.",
        ],
        brute_force="scipy.stats.f_oneway gives F and the p-value; doing it by hand shows the decomposition.",
        approach=r"""Example: group means 12.62, 10.90, 13.53, 12.03; SS_between = 21.89 (3 df) and SS_within = 23.25 (20 df);
F = (21.89/3) / (23.25/20) ≈ 6.28.""",
        complexity="O(N).",
        pitfalls=r"""- Forgetting to weight by group size in SS_between (matters when groups differ in size).
- Using N − 1 instead of N − k for the within degrees of freedom.
- Integer division in other languages; Python 3 `/` is fine.""",
        follow_up="Get the p-value from the F distribution, then run Tukey's HSD to see which pairs differ.",
    ),
),

# ---------------------------------------------------------------- sample size
dict(
    id="stats-sample-size",
    title="Sample Size per Arm for a Conversion Test",
    difficulty="Medium",
    pattern="Power Analysis",
    kind="function",
    entry="n_per_arm",
    compare="exact",
    description=r"""
Return the number of users needed **per arm** to detect a change in conversion from `p1` to `p2 = p1 + mde`
with a two-sided test at level `alpha` and the given `power`:

$$n = \left\lceil \frac{(z_{1-\alpha/2} + z_{\text{power}})^2\,[p_1(1-p_1) + p_2(1-p_2)]}{(p_2 - p_1)^2} \right\rceil$$

where $z_q$ is the standard normal quantile (Python: `statistics.NormalDist().inv_cdf(q)`). `mde` may be negative
(detecting a drop). Return an `int`.

Constraints: `0 < p1 < 1`, `0 < p1 + mde < 1`, `mde != 0`, `0 < alpha < 1`, `0 < power < 1`.

**Example:** `p1 = 0.10, mde = 0.01, alpha = 0.05, power = 0.8` → `14749`
""",
    starter='''from statistics import NormalDist

def n_per_arm(p1, mde, alpha, power):
    pass
''',
    solution='''import math
from statistics import NormalDist

def n_per_arm(p1, mde, alpha, power):
    nd = NormalDist()
    z = nd.inv_cdf(1 - alpha / 2) + nd.inv_cdf(power)
    p2 = p1 + mde
    n = z ** 2 * (p1 * (1 - p1) + p2 * (1 - p2)) / mde ** 2
    return int(math.ceil(n))
''',
    tests=[
        [0.10, 0.01, 0.05, 0.8],
        [0.10, 0.005, 0.05, 0.8],
        [0.10, 0.02, 0.05, 0.8],
        [0.10, 0.01, 0.05, 0.9],
        [0.048, 0.005, 0.05, 0.8],
        [0.30, -0.03, 0.05, 0.8],
        [0.5, 0.05, 0.01, 0.8],
        [0.02, 0.004, 0.10, 0.8],
        [0.6, 0.1, 0.05, 0.95],
    ],
    examples=2,
    wrong_solutions=[
        '''import math
from statistics import NormalDist

def n_per_arm(p1, mde, alpha, power):
    nd = NormalDist()
    z = nd.inv_cdf(1 - alpha) + nd.inv_cdf(power)
    p2 = p1 + mde
    return int(math.ceil(z ** 2 * (p1 * (1 - p1) + p2 * (1 - p2)) / mde ** 2))
''',
        '''import math

def n_per_arm(p1, mde, alpha, power):
    return int(math.ceil(16 * p1 * (1 - p1) / mde ** 2))
''',
    ],
    guide=dict(
        prereqs="Power and sample size (lesson *Power and sample size for A/B tests*).",
        intuition=r"""To be detected with probability `power`, the true difference must sit z_{1−α/2} + z_power standard errors away from
zero. The standard error shrinks like 1/sqrt(n), so solving for n gives a formula with the effect size squared in the
denominator: halve the effect and you need four times the users.""",
        hints=[
            "statistics.NormalDist().inv_cdf gives normal quantiles without SciPy.",
            "Two-sided test: use 1 − alpha/2 for the alpha quantile.",
            "Round up with math.ceil.",
        ],
        brute_force="Simulate experiments at increasing n until 80% of them are significant: slow and noisy, but a good check.",
        approach=r"""p1 = 0.10, p2 = 0.11: z = 1.95996 + 0.84162 = 2.80158; variance sum = 0.09 + 0.0979 = 0.1879;
n = 7.849 × 0.1879 / 0.0001 = 14,748.03 → 14,749.""",
        complexity="O(1).",
        pitfalls=r"""- One-sided quantile (1 − alpha) for a two-sided test.
- Using the rule of thumb 16σ²/δ² when an exact answer is required (it is an approximation).
- Forgetting that this is per arm; the total is twice as large.""",
        follow_up="Invert the formula to compute power for a fixed n, or extend it to unequal allocation with a ratio κ = n2/n1.",
    ),
),

# ---------------------------------------------------------------- multiple testing
dict(
    id="stats-multiple-testing",
    title="Bonferroni, Holm and Benjamini-Hochberg",
    difficulty="Medium",
    pattern="Multiple Testing",
    kind="function",
    entry="corrections",
    compare="exact",
    description=r"""
Given `m` p-values and a level `alpha`, return `[bonferroni, holm, bh]`, each a **sorted list of the original indices**
of rejected hypotheses:

- **Bonferroni**: reject `i` if `p[i] <= alpha / m`.
- **Holm**: sort p-values ascending (ties by index). For rank `r = 1, 2, ...` reject while `p_(r) <= alpha / (m - r + 1)`;
  stop at the first failure (that one and all later ones are kept).
- **Benjamini-Hochberg**: sort ascending; find the largest rank `k` with `p_(k) <= k * alpha / m` and reject the `k`
  smallest p-values (none if no such `k`).

Constraints: `1 <= m <= 10^4`, p-values in `[0, 1]`. Tests avoid p-values exactly on a threshold.

**Example:** `p = [0.0002, 0.0009, 0.0041, 0.0098, 0.012, 0.021, 0.033, 0.048, 0.19, 0.44], alpha = 0.05` →
`[[0, 1, 2], [0, 1, 2], [0, 1, 2, 3, 4, 5, 6]]`
""",
    starter='''def corrections(pvals, alpha):
    pass
''',
    solution='''def corrections(pvals, alpha):
    m = len(pvals)
    bonf = [i for i, p in enumerate(pvals) if p <= alpha / m]
    order = sorted(range(m), key=lambda i: (pvals[i], i))
    holm = []
    for r, i in enumerate(order, start=1):
        if pvals[i] <= alpha / (m - r + 1):
            holm.append(i)
        else:
            break
    k = 0
    for r, i in enumerate(order, start=1):
        if pvals[i] <= r * alpha / m:
            k = r
    bh = order[:k]
    return [sorted(bonf), sorted(holm), sorted(bh)]
''',
    tests=[
        [[0.0002, 0.0009, 0.0041, 0.0098, 0.012, 0.021, 0.033, 0.048, 0.19, 0.44], 0.05],
        [[0.03], 0.05],
        [[0.2, 0.5, 0.9], 0.05],
        [[0.001, 0.008, 0.02, 0.2], 0.05],
        [[0.04, 0.001, 0.03, 0.002], 0.05],
        [[0.011, 0.011, 0.011, 0.5], 0.05],
        [[0.009, 0.019, 0.029, 0.039, 0.049], 0.05],
        [[0.0001, 0.6, 0.004, 0.7, 0.012, 0.03], 0.1],
        [[round(_r.random() * 0.1, 6) if i < 50 else round(_r.random(), 6) for i in range(400)], 0.05],
    ],
    examples=1,
    wrong_solutions=[
        '''def corrections(pvals, alpha):
    m = len(pvals)
    bonf = [i for i, p in enumerate(pvals) if p <= alpha / m]
    order = sorted(range(m), key=lambda i: pvals[i])
    holm = [i for r, i in enumerate(order, 1) if pvals[i] <= alpha / (m - r + 1)]
    bh = [i for r, i in enumerate(order, 1) if pvals[i] <= r * alpha / m]
    return [sorted(bonf), sorted(holm), sorted(bh)]
''',
    ],
    guide=dict(
        prereqs="Family-wise error rate, false discovery rate and the three procedures (lesson *Multiple testing*).",
        intuition=r"""Bonferroni applies the strictest threshold to every test. Holm starts with Bonferroni's threshold for the smallest
p-value and relaxes it step by step, stopping at the first failure. Benjamini-Hochberg compares the k-th smallest
p-value with a line that rises with k and rejects everything up to the *last* point under the line.""",
        hints=[
            "Sort indices by p-value (break ties by index) and work with ranks starting at 1.",
            "Holm stops at the first failure (a step-down procedure).",
            "BH keeps going to find the largest qualifying rank (a step-up procedure), then rejects all smaller ranks.",
        ],
        brute_force="statsmodels.stats.multitest.multipletests does all three; implementing them clarifies step-down versus step-up.",
        approach=r"""Example BH: thresholds 0.005, 0.010, ..., 0.050; rank 7 (0.033 ≤ 0.035) is the largest that qualifies; rank 8
(0.048 > 0.040) fails. So the 7 smallest are rejected. Holm: 0.0002 ≤ 0.005, 0.0009 ≤ 0.00556, 0.0041 ≤ 0.00625,
0.0098 > 0.00714 → stop with 3.""",
        complexity="O(m log m) for sorting.",
        pitfalls=r"""- Holm without stopping (rejecting later hypotheses that happen to pass their own threshold).
- BH rejecting only the individual hypotheses under the line instead of all ranks up to the largest qualifying one.
- Returning sorted p-values instead of original indices.""",
        follow_up="Compute adjusted p-values for each method so they can be compared directly with alpha.",
    ),
),

# ---------------------------------------------------------------- SRM
dict(
    id="stats-srm-check",
    title="Sample Ratio Mismatch Check",
    difficulty="Easy",
    pattern="Experimentation",
    kind="function",
    entry="srm_check",
    compare="float",
    description=r"""
An experiment planned to send a share `expected_share` of users to treatment. It received `n_control` and
`n_treatment` users. Return `[chi2, p_value]` for the chi-square goodness-of-fit test with 1 degree of freedom:

- expected counts: `N·(1 − expected_share)` for control and `N·expected_share` for treatment, `N = n_control + n_treatment`;
- $\chi^2 = \sum (O - E)^2 / E$ over the two cells;
- for 1 degree of freedom the p-value is $\operatorname{erfc}(\sqrt{\chi^2 / 2})$.

**Example:** `n_control = 50550, n_treatment = 49450, expected_share = 0.5` → `[12.1, 0.000504]` (approximately).
""",
    starter='''import math

def srm_check(n_control, n_treatment, expected_share):
    pass
''',
    solution='''import math

def srm_check(n_control, n_treatment, expected_share):
    N = n_control + n_treatment
    ec, et = N * (1 - expected_share), N * expected_share
    chi2 = (n_control - ec) ** 2 / ec + (n_treatment - et) ** 2 / et
    return [chi2, math.erfc(math.sqrt(chi2 / 2))]
''',
    tests=[
        [50550, 49450, 0.5],
        [50210, 49790, 0.5],
        [100400, 99600, 0.5],
        [5000, 5000, 0.5],
        [90310, 9690, 0.1],
        [9000, 1000, 0.1],
        [1, 2, 0.5],
        [1000000, 1003000, 0.5],
        [66000, 34000, 1 / 3],
    ],
    examples=2,
    wrong_solutions=[
        '''import math

def srm_check(n_control, n_treatment, expected_share):
    N = n_control + n_treatment
    chi2 = (n_control - N / 2) ** 2 / (N / 2) + (n_treatment - N / 2) ** 2 / (N / 2)
    return [chi2, math.erfc(math.sqrt(chi2 / 2))]
''',
        '''import math

def srm_check(n_control, n_treatment, expected_share):
    N = n_control + n_treatment
    ec, et = N * (1 - expected_share), N * expected_share
    chi2 = abs(n_control - ec) / ec + abs(n_treatment - et) / et
    return [chi2, math.erfc(math.sqrt(chi2 / 2))]
''',
    ],
    guide=dict(
        prereqs="Goodness-of-fit tests and sample ratio mismatch (lessons *ANOVA and the chi-square test* and *A/B testing pitfalls*).",
        intuition=r"""If assignment works as designed, arm sizes differ from the plan only by binomial noise, which is tiny relative to
large N. A chi-square statistic far above 1 (tiny p-value) means users went missing or were misassigned in one arm,
and the experiment's results cannot be trusted until the bug is found.""",
        hints=[
            "Expected treatment count = N × expected_share; control gets the rest.",
            "Add (O − E)²/E for both cells.",
            "With 1 df, chi² is a squared standard normal, so p = erfc(sqrt(chi²/2)).",
        ],
        brute_force="scipy.stats.chisquare([nc, nt], f_exp=[ec, et]) gives the same result.",
        approach=r"""Example: N = 100,000, expected 50,000 each; chi² = 550²/50,000 × 2 = 12.1; p = erfc(sqrt(6.05)) ≈ 0.0005.""",
        complexity="O(1).",
        pitfalls=r"""- Assuming a 50/50 split when the design was, say, 90/10.
- Using absolute instead of squared deviations.
- Treating a small percentage imbalance as harmless: with large N it can be overwhelming evidence of a bug.""",
        follow_up="Run the check per day and per platform: SRM often appears only in one browser or app version.",
    ),
),

# ---------------------------------------------------------------- epsilon-greedy
dict(
    id="stats-epsilon-greedy",
    title="Expected Reward of an Epsilon-Greedy Policy",
    difficulty="Easy",
    pattern="Multi-Arm Bandits",
    kind="function",
    entry="epsilon_greedy_value",
    compare="float",
    description=r"""
A bandit has arms with true success rates `rates`. An epsilon-greedy policy currently believes arm `best_guess` is best:
on each pull it explores with probability `epsilon` (choosing an arm uniformly at random, possibly `best_guess` itself)
and otherwise pulls `best_guess`.

Return `[expected_reward_per_pull, expected_regret]`, where regret over `n` pulls is
`n × (max(rates) − expected_reward_per_pull)`.

**Example:** `rates = [0.04, 0.05, 0.06], best_guess = 2, epsilon = 0.1, n = 30000` →
`[0.059, 30.0]` (reward = 0.9 × 0.06 + 0.1 × 0.05).
""",
    starter='''def epsilon_greedy_value(rates, best_guess, epsilon, n):
    pass
''',
    solution='''def epsilon_greedy_value(rates, best_guess, epsilon, n):
    explore = sum(rates) / len(rates)
    reward = (1 - epsilon) * rates[best_guess] + epsilon * explore
    return [reward, n * (max(rates) - reward)]
''',
    tests=[
        [[0.04, 0.05, 0.06], 2, 0.1, 30000],
        [[0.04, 0.05, 0.06], 0, 0.1, 30000],
        [[0.04, 0.05, 0.06], 2, 1.0, 30000],
        [[0.04, 0.05, 0.06], 1, 0.0, 1000],
        [[0.3], 0, 0.5, 10],
        [[0.1, 0.9], 1, 0.2, 500],
        [[0.02, 0.025, 0.021, 0.03, 0.018], 3, 0.05, 1000000],
        [[0.5, 0.5, 0.5], 1, 0.3, 100],
    ],
    examples=2,
    wrong_solutions=[
        '''def epsilon_greedy_value(rates, best_guess, epsilon, n):
    others = [r for i, r in enumerate(rates) if i != best_guess]
    explore = sum(others) / len(others) if others else rates[best_guess]
    reward = (1 - epsilon) * rates[best_guess] + epsilon * explore
    return [reward, n * (max(rates) - reward)]
''',
    ],
    guide=dict(
        prereqs="Exploration, exploitation and regret (lesson *Multi-arm bandits*).",
        intuition=r"""Expected value splits on what the policy does: with probability 1 − ε it exploits and earns the believed-best arm's
rate; with probability ε it explores and earns the average rate of all arms. Regret is how far that falls short of
always pulling the truly best arm.""",
        hints=[
            "Exploring picks any arm uniformly, so its expected reward is the mean of all rates.",
            "Mix exploitation and exploration with weights 1 − ε and ε.",
            "Regret per pull = max(rates) − expected reward; multiply by n.",
        ],
        brute_force="Simulate n pulls many times and average: noisy and slow; linearity of expectation gives the exact answer.",
        approach=r"""Example: exploit 0.06 with weight 0.9; explore mean 0.05 with weight 0.1 → 0.059; regret 30,000 × 0.001 = 30.""",
        complexity="O(k) for k arms.",
        pitfalls=r"""- Excluding the best-guess arm from exploration (uniform exploration can pick it).
- Using the believed-best arm's rate instead of the true maximum in the regret.
- Forgetting that if best_guess is wrong, regret grows linearly in n even with ε = 0.""",
        follow_up="Compute the expected regret of the equal-split A/B test (ε = 1) and of Thompson sampling by simulation.",
    ),
),
]
