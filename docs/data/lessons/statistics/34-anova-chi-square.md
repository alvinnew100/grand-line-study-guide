# ANOVA and the chi-square test

> **Before this lesson:** [A/B tests, hypotheses and permutation tests](#/lesson/statistics/ab-tests-permutation) (permutation tests), [t-tests, z-tests and degrees of freedom](#/lesson/statistics/t-tests) and [Multiple testing: Bonferroni, Holm and the false discovery rate](#/lesson/statistics/multiple-testing). Contingency tables were introduced in [Correlation and exploring two or more variables](#/lesson/statistics/correlation-bivariate).

## In plain words

Real experiments often have more than two arms: four onboarding flows, three notification texts, five price points. Comparing every pair with t-tests multiplies the chance of a false alarm. **ANOVA** (analysis of variance) asks one question instead: do *any* of the group means differ more than chance would allow? For counts and categories (clicked or not, by variant), the **chi-square test** asks the analogous question: are the outcome rates the same across groups? **Fisher's exact test** handles small tables where the chi-square approximation is unreliable.

An everyday picture: a school compares four teaching methods. Instead of six separate head-to-head comparisons, the head teacher first asks: "Is the spread between the four class averages bigger than the spread you would expect from ordinary differences between pupils?" If not, there is nothing to chase. If so, look closer.

Why it matters for a job: multi-arm experiments, comparisons across regions or segments, and checks that traffic was split as intended (the sample ratio mismatch check, which is a chi-square test) all use these tools. Interviewers ask how ANOVA's F-statistic works, what the chi-square statistic measures, how to get expected counts in a contingency table, and when to switch to Fisher's exact test.

## 1. The idea of ANOVA

Suppose four onboarding flows were randomly assigned to new users, and we record minutes to finish onboarding. The **null hypothesis** is that all four flows have the same mean; the alternative is that at least one differs.

ANOVA splits the total variability of the data into two parts:

- **Between-group** variation: how far the group means are from the **grand mean** (the mean of all data). If the flows truly differ, this is large.
- **Within-group** variation: how far individual values are from their own group's mean. This is the background noise between users.

Each is measured by a **sum of squares** (SS). With $k$ groups, $N$ values in total, group sizes $n_j$, group means $\bar{x}_j$ and grand mean $\bar{x}$:

$$SS_\text{between} = \sum_j n_j(\bar{x}_j - \bar{x})^2, \qquad SS_\text{within} = \sum_j \sum_i (x_{ij} - \bar{x}_j)^2$$

Dividing each by its degrees of freedom gives a **mean square**, and their ratio is the **F-statistic**:

$$F = \frac{SS_\text{between}/(k-1)}{SS_\text{within}/(N-k)}$$

If the null is true, both mean squares estimate the same noise level, so $F$ is around 1. A large $F$ says the group means are more spread out than noise explains. Under the null (with roughly normal data and equal variances), $F$ follows the **F-distribution** with $k-1$ and $N-k$ degrees of freedom.

## 2. ANOVA in Python

```python-run
import numpy as np
from scipy import stats
groups = {
    "flowA": np.array([12.4, 10.9, 13.8, 11.6, 12.9, 14.1]),
    "flowB": np.array([10.2, 11.8, 9.7, 10.9, 12.3, 10.5]),
    "flowC": np.array([13.5, 12.1, 14.6, 13.0, 15.2, 12.8]),
    "flowD": np.array([11.9, 12.6, 10.8, 13.3, 11.4, 12.2]),
}
allv = np.concatenate(list(groups.values()))
grand = allv.mean()
k, N = len(groups), len(allv)
ss_between = sum(len(g) * (g.mean() - grand) ** 2 for g in groups.values())
ss_within = sum(((g - g.mean()) ** 2).sum() for g in groups.values())
F = (ss_between / (k - 1)) / (ss_within / (N - k))
p = stats.f.sf(F, k - 1, N - k)
print({name: round(float(g.mean()), 2) for name, g in groups.items()})
print(f"SS between {ss_between:.2f}, SS within {ss_within:.2f}, F = {F:.3f}, p = {p:.5f}")
res = stats.f_oneway(*groups.values())
print(f"scipy f_oneway: F = {res.statistic:.3f}, p = {res.pvalue:.5f}")
```

**Reading this code line by line**

- `groups` maps each flow to the minutes of its six users.
- `ss_between` adds, for each group, its size times the squared distance of its mean from the grand mean. The `sum(... for g in ...)` form is a **generator expression**: it computes one value per group and adds them.
- `ss_within` adds each group's squared deviations from its own mean.
- `stats.f.sf(F, k - 1, N - k)` is the upper-tail area of the F-distribution: the p-value.
- `stats.f_oneway(*groups.values())` runs one-way ANOVA in one call; the `*` unpacks the four arrays as separate arguments.

Flow B is fastest (10.9 minutes) and flow C slowest (13.53). The between-group sum of squares (21.89) is almost as large as the within-group one (23.25), even though it has only 3 degrees of freedom against 20. $F = 6.277$, $p = 0.00354$: strong evidence that the flows do not all have the same mean.

ANOVA tells you *that* some means differ, not *which*. Follow-up pairwise comparisons should control the family-wise error rate, for example with Tukey's HSD (`stats.tukey_hsd` in SciPy) or Holm-corrected t-tests.

## 3. ANOVA as a permutation test

The same question can be answered by shuffling, with no normality assumption: under the null, flow labels are meaningless. Use the variance of the four group means as the statistic.

```python-run
import numpy as np
rng = np.random.default_rng(34)
groups = [np.array([12.4, 10.9, 13.8, 11.6, 12.9, 14.1]), np.array([10.2, 11.8, 9.7, 10.9, 12.3, 10.5]),
          np.array([13.5, 12.1, 14.6, 13.0, 15.2, 12.8]), np.array([11.9, 12.6, 10.8, 13.3, 11.4, 12.2])]
pooled = np.concatenate(groups)
def spread_of_means(values):
    return np.var([g.mean() for g in np.split(values, 4)], ddof=1)
observed = spread_of_means(pooled)
perm = np.array([spread_of_means(rng.permutation(pooled)) for _ in range(5000)])
print(f"observed variance of group means {observed:.3f}; permutation p = {np.mean(perm >= observed):.4f}")
```

**Reading this code line by line**

- `np.split(values, 4)` cuts an array of 24 values into 4 consecutive pieces of 6, our four groups.
- `spread_of_means` returns the variance of the four group means.
- Each permutation shuffles all 24 values and re-splits them into fake groups.

The permutation p-value, 0.0034, agrees with the F-test's 0.00354. With balanced groups and well-behaved data the classical and resampling answers match; resampling is the safer choice when data are skewed or groups are tiny.

### Two-way ANOVA, in one paragraph

If users were also split by a second factor (say weekday versus weekend sign-ups), **two-way ANOVA** separates the effect of each factor and their **interaction** (whether the best flow depends on the day). In practice, this is fit as a linear regression with categorical predictors, for example `statsmodels.formula.api.ols("minutes ~ C(flow) * C(day)", data=df)` followed by `sm.stats.anova_lm`. Regression with factors is covered in [Factor variables and interpreting regression](#/lesson/statistics/factors-interpretation).

## 4. The chi-square test of independence

For categorical outcomes we use counts. Three push-notification texts were each sent to 1,500 users; the table records who opened the app.

|  | Text 1 | Text 2 | Text 3 |
|---|---|---|---|
| Opened | 61 | 45 | 72 |
| Did not open | 1,439 | 1,455 | 1,428 |

Null hypothesis: the open rate is the same for all three texts, i.e. opening is **independent** of the text. Under the null, each cell's **expected count** is

$$E_{ij} = \frac{(\text{row } i \text{ total}) \times (\text{column } j \text{ total})}{\text{grand total}}$$

and the **chi-square statistic** measures how far observed counts $O$ are from expected counts $E$:

$$\chi^2 = \sum_\text{cells} \frac{(O - E)^2}{E}$$

Each term is a squared **Pearson residual**, $(O - E)/\sqrt{E}$: how many "standard deviations" a cell is from its expected count. Under the null, $\chi^2$ approximately follows the **chi-square distribution** with $(r-1)(c-1)$ degrees of freedom for $r$ rows and $c$ columns.

```python-run
import numpy as np
from scipy import stats
observed = np.array([[61, 45, 72],
                     [1439, 1455, 1428]])
row_tot = observed.sum(axis=1, keepdims=True)
col_tot = observed.sum(axis=0, keepdims=True)
expected = row_tot * col_tot / observed.sum()
chi2 = ((observed - expected) ** 2 / expected).sum()
df = (observed.shape[0] - 1) * (observed.shape[1] - 1)
print("expected counts:\n", expected.round(2))
print(f"chi-square = {chi2:.3f}, df = {df}, p = {stats.chi2.sf(chi2, df):.4f}")
res = stats.chi2_contingency(observed)
print(f"scipy: chi2 = {res.statistic:.3f}, p = {res.pvalue:.4f}")
```

**Reading this code line by line**

- `observed.sum(axis=1, keepdims=True)` sums across each row and keeps the result as a column (shape 2 × 1); `axis=0` sums down each column (shape 1 × 3). Multiplying them uses **broadcasting**, NumPy's rule for combining arrays of compatible shapes, to produce the full 2 × 3 table of row-total × column-total products.
- Dividing by the grand total gives the expected counts.
- `stats.chi2_contingency` does everything at once and also returns the expected table.

Under the null each text would get about 59.33 opens. Text 2 is well below that and text 3 well above. $\chi^2 = 6.469$ on 2 degrees of freedom gives $p = 0.0394$: some evidence that open rates differ. (Note that `chi2_contingency` applies a small "continuity correction" only for 2 × 2 tables; this table is 2 × 3, so the hand and SciPy answers match exactly.)

## 5. The chi-square test by resampling

As with ANOVA, a resampling version avoids relying on the chi-square approximation. Under the null, the 178 opens are scattered across the 4,500 users at random. Put 178 ones and 4,322 zeros in a box, shuffle, deal three groups of 1,500, and recompute the statistic.

```python-run
import numpy as np
rng = np.random.default_rng(35)
opens = np.array([61, 45, 72]); n = 1500
total = opens.sum()
exp_open = total / 3
def chi2_stat(o):
    return (((o - exp_open) ** 2 / exp_open) + ((n - o - (n - exp_open)) ** 2 / (n - exp_open))).sum()
observed_stat = chi2_stat(opens)
box = np.array([1] * total + [0] * (3 * n - total))
sims = np.empty(5000)
for i in range(5000):
    rng.shuffle(box)
    sims[i] = chi2_stat(box.reshape(3, n).sum(axis=1))
print(f"observed statistic {observed_stat:.3f}; resampling p-value: {np.mean(sims >= observed_stat):.4f}")
```

**Reading this code line by line**

- `chi2_stat` computes the chi-square statistic from the three open counts, using the expected counts for both "opened" and "not opened" rows.
- `rng.shuffle(box)` shuffles the array in place; `box.reshape(3, n)` views it as three rows of 1,500, and `.sum(axis=1)` counts the ones in each.

The resampling p-value, 0.0402, matches the formula's 0.0394.

## 6. Fisher's exact test for small counts

The chi-square approximation becomes unreliable when expected counts are small; a common rule is to worry when any expected count is below 5. **Fisher's exact test** computes the exact probability of every table with the same row and column totals, avoiding the approximation. It is standard for 2 × 2 tables with small counts.

```python-run
from scipy import stats
table = [[7, 1],
         [3, 9]]
odds, p_exact = stats.fisher_exact(table)
chi = stats.chi2_contingency(table, correction=False)
print(f"Fisher exact p = {p_exact:.4f}; chi-square p = {chi.pvalue:.4f}")
print("smallest expected count:", chi.expected_freq.min().round(2))
```

**Reading this code line by line**

- The table might be 8 users who got a beta feature (7 kept using it, 1 stopped) versus 12 who did not (3 kept using, 9 stopped).
- `stats.fisher_exact` returns the sample odds ratio and the exact two-sided p-value.
- `correction=False` turns off the continuity correction so we see the raw chi-square approximation.

Fisher gives $p = 0.0198$; the chi-square approximation gives 0.0062, overstating the evidence by a factor of three, because the smallest expected count is only 4.0. With small counts, trust Fisher.

## 7. Goodness of fit and the sample ratio mismatch check

A **goodness-of-fit** test compares observed counts in one categorical variable with counts expected from a hypothesised distribution. Its most important use in experimentation is the **sample ratio mismatch** (SRM) check: if an A/B test is designed as a 50/50 split but the arms received 50,550 and 49,450 users, `stats.chisquare([50550, 49450])` tests whether the imbalance is plausible under a true 50/50 split. Here $p \approx 0.0005$, which means the assignment or logging is broken and the experiment's results cannot be trusted until the cause is found. More in [A/B testing pitfalls](#/lesson/statistics/ab-pitfalls).

## 8. Relevance for data science

Formal ANOVA and chi-square tests are less central in day-to-day data science than in academic research, because many practical questions are better served by estimating effect sizes with intervals, by regression, or by bandit algorithms that adaptively allocate traffic (next lessons). They remain essential for: checking that randomisation worked (SRM, balance of pre-experiment covariates), quick screens of multi-arm tests, and understanding the regression output where F-tests and chi-square statistics appear.

> [!INTERVIEW]
> "How do you compute the expected count in a contingency table?" Row total times column total divided by grand total. "Why not run all pairwise t-tests instead of ANOVA?" Six pairwise tests among four groups inflate the family-wise false-positive rate; ANOVA tests the global null once, then corrected pairwise tests locate the differences.

## Summary

- ANOVA tests whether several group means are all equal by comparing between-group and within-group variation; $F$ near 1 is consistent with the null.
- The permutation version shuffles group labels and gives the same answer without normality assumptions.
- ANOVA says some means differ; Tukey's HSD or corrected pairwise tests say which.
- The chi-square test compares observed and expected counts; expected = row total × column total / grand total; df = (r − 1)(c − 1).
- Use Fisher's exact test when expected counts are small; use a goodness-of-fit test to detect sample ratio mismatch.

## Glossary

- **ANOVA (analysis of variance)**: a test of whether several group means are equal.
- **Grand mean**: the mean of all observations together.
- **Sum of squares (SS)**: a sum of squared deviations; between-group and within-group.
- **Mean square**: a sum of squares divided by its degrees of freedom.
- **F-statistic / F-distribution**: the ratio of between- to within-group mean squares / its null distribution.
- **Generator expression**: Python syntax that produces values one at a time inside a function call such as `sum`.
- **Tukey's HSD**: pairwise comparisons after ANOVA with family-wise error control.
- **Two-way ANOVA / interaction**: ANOVA with two factors / when one factor's effect depends on the other.
- **Independence (of categorical variables)**: the distribution of one does not change with the other.
- **Expected count**: the count a cell would have under independence.
- **Chi-square statistic ($\chi^2$)**: the sum of (observed − expected)² / expected.
- **Pearson residual**: (observed − expected) / √expected for one cell.
- **Broadcasting**: NumPy's rule for combining arrays of different but compatible shapes.
- **Fisher's exact test**: an exact test for small contingency tables.
- **Goodness-of-fit test**: compares observed counts with a hypothesised distribution.
- **Sample ratio mismatch (SRM)**: an experiment whose arm sizes differ from the planned split by more than chance.

## Check yourself

```quiz
[
  {"q": "In one-way ANOVA, an F-statistic close to 1 suggests…", "options": ["the group means vary about as much as noise alone would produce", "the groups are wildly different", "the test was run incorrectly", "the variances are zero"], "answer": 0,
   "explain": "Under the null both mean squares estimate the same noise variance, so their ratio is near 1."},
  {"q": "A 2 × 3 table has row totals 178 and 4,322, column totals 1,500 each and grand total 4,500. The expected count for (row 1, column 1) is…", "options": ["59.33", "61", "178", "1,500"], "answer": 0,
   "explain": "$178 \\times 1500 / 4500 = 59.33$."},
  {"q": "Degrees of freedom for a chi-square test on a 3 × 4 contingency table are…", "options": ["6", "12", "7", "11"], "answer": 0,
   "explain": "$(3-1)(4-1) = 6$."},
  {"q": "A 2 × 2 table has an expected count of 2 in one cell. Which test is appropriate?", "options": ["Fisher's exact test", "The chi-square approximation without correction", "ANOVA", "A paired t-test"], "answer": 0,
   "explain": "Small expected counts make the chi-square approximation unreliable."},
  {"q": "ANOVA on four groups gives p = 0.003. What can you conclude?", "options": ["At least one group mean differs; follow-up tests are needed to find which", "All four means differ from each other", "Group 1 is the best", "The variances differ"], "answer": 0,
   "explain": "ANOVA tests the global null hypothesis only."},
  {"q": "A 50/50 A/B test has 50,550 and 49,450 users. A chi-square goodness-of-fit test gives p ≈ 0.0005. This signals…", "options": ["a sample ratio mismatch: assignment or logging is likely broken", "a significant treatment effect", "nothing; small imbalances are always fine", "that the test needs more users"], "answer": 0,
   "explain": "Such an imbalance is very unlikely under a true 50/50 split; investigate before trusting results."}
]
```

> **Source:** Bruce & Bruce, *Practical Statistics for Data Scientists* (O'Reilly, 2017), ch. 3, "ANOVA" (F-statistic, two-way ANOVA), "Chi-Square Test" (resampling approach, statistical theory, Fisher's exact test, relevance for data science); SciPy documentation for `f_oneway`, `chi2_contingency` and `fisher_exact`; the examples are original.
