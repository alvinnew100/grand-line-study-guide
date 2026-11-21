# Multiple testing: Bonferroni, Holm and the false discovery rate

> **Before this lesson:** [Statistical significance, p-values and their misconceptions](#/lesson/statistics/p-values) (alpha, type I errors, the false discovery rate idea) and [t-tests, z-tests and degrees of freedom](#/lesson/statistics/t-tests). The "vast search effect" from [Random sampling and the many faces of bias](#/lesson/statistics/sampling-bias) is the same problem seen from another side.

## In plain words

A test at the 5% level has a 1-in-20 chance of a false alarm when nothing is going on. That is fine for one test. But an A/B test dashboard may show 20 metrics, each broken down by 10 countries and 3 platforms; a genomics study may test 20,000 genes. Run enough tests and false alarms become a certainty. **Multiple testing** (or multiple comparisons) is the problem, and **corrections** such as Bonferroni, Holm and Benjamini-Hochberg are the standard defences.

An everyday picture: if you flip 20 fair coins five times each, it is very likely that at least one comes up heads all five times. Announcing "this coin is biased!" would be silly; you went looking among many coins and found the luckiest one.

Why it matters for a job: experimentation platforms report dozens of metrics per test; analysts slice results by segment; data scientists test many features. Without corrections, every experiment produces a "surprising" win somewhere. Interviewers ask: "Your test has 20 metrics and one is significant: do you ship?", "What is the difference between Bonferroni and FDR?", and "How would you handle 50 segments?"

## 1. How fast false alarms pile up

If you run $m$ independent tests at level $\alpha$ and every null hypothesis is true, the probability of at least one false positive is

$$P(\text{at least one false positive}) = 1 - (1 - \alpha)^m$$

This is the complement rule from the probability lesson: the chance of no false alarms in all $m$ tests is $(1-\alpha)^m$.

```python-run
import numpy as np
from scipy import stats
for m in [1, 5, 10, 20, 50]:
    print(f"{m:>2} tests: P(at least one false positive) = {1 - 0.95 ** m:.3f}")
rng = np.random.default_rng(33)
experiments, metrics, n = 5_000, 20, 200
a = rng.normal(0, 1, size=(experiments, metrics, n))
b = rng.normal(0, 1, size=(experiments, metrics, n))
p = stats.ttest_ind(a, b, axis=2).pvalue
print("simulated share of A/A experiments with a 'winning' metric:", round(np.mean((p < 0.05).any(axis=1)), 3))
```

**Reading this code line by line**

- The loop evaluates the formula for different numbers of tests.
- The simulation creates 5,000 A/A experiments, each with 20 metrics and 200 users per arm, as a three-dimensional array (experiments × metrics × users). Nothing differs between the arms.
- `stats.ttest_ind(a, b, axis=2)` runs a t-test across users for every experiment-metric pair, giving a 5,000 × 20 table of p-values.
- `(p < 0.05).any(axis=1)` is true for an experiment if *any* of its 20 metrics is significant.

With 20 tests the chance of at least one false positive is 0.642, and the simulation agrees: 63.5% of these do-nothing experiments have a "winning" metric. With 50 tests it reaches 0.923. An experiment report with 20 metrics and no correction will usually show something green.

## 2. Two goals: FWER and FDR

There are two ways to define "controlling errors" across many tests.

- The **family-wise error rate** (FWER) is the probability of making *any* false positive among all the tests (the "family"). Controlling FWER at 5% means that in 95% of studies, not a single false claim is made. This is strict and appropriate when every false claim is costly, for example a launch decision or a medical claim.
- The **false discovery rate** (FDR) is the expected *share* of rejected hypotheses that are false positives. Controlling FDR at 5% allows some false discoveries but promises that, on average, no more than 5% of your discoveries are false. This is appropriate when you are screening many candidates for follow-up, such as segments to investigate, genes to study or features to try.

Let $V$ be the number of false positives and $R$ the total number of rejections. Then FWER $= P(V \ge 1)$ and FDR $= E[V/R]$ (with $V/R$ taken as 0 when $R = 0$).

## 3. The Bonferroni correction

The simplest method: test each of the $m$ hypotheses at level $\alpha/m$ instead of $\alpha$. Equivalently, multiply each p-value by $m$ (capping at 1) and compare with $\alpha$. With 20 metrics and $\alpha = 0.05$, a metric needs $p < 0.0025$.

Why it works: the probability of at least one of $m$ events is at most the sum of their probabilities (a fact called the union bound), so FWER $\le m \times \alpha/m = \alpha$. It holds even if the tests are dependent. The price is power: with many tests, real effects need very small p-values to survive.

## 4. Holm's method

**Holm's step-down method** controls FWER exactly as well as Bonferroni and is never less powerful, so there is little reason to use plain Bonferroni.

1. Sort the p-values from smallest to largest: $p_{(1)} \le p_{(2)} \le \dots \le p_{(m)}$.
2. Compare $p_{(1)}$ with $\alpha/m$, $p_{(2)}$ with $\alpha/(m-1)$, $p_{(3)}$ with $\alpha/(m-2)$, and so on.
3. Reject hypotheses in order until the first one that fails its threshold; stop there and keep all the rest.

The first comparison is Bonferroni's; later ones are more lenient because fewer hypotheses remain.

## 5. Benjamini-Hochberg: controlling the FDR

The **Benjamini-Hochberg** (BH) procedure controls the FDR at level $q$ (often written $\alpha$ too):

1. Sort the p-values ascending, $p_{(1)} \le \dots \le p_{(m)}$.
2. Find the largest rank $k$ such that $p_{(k)} \le \dfrac{k}{m}\,\alpha$.
3. Reject the hypotheses with the $k$ smallest p-values (all of them, even if some earlier ones were above their own line).

The threshold grows with the rank, so BH is much less strict than Bonferroni when there are many real effects. Here are ten p-values from a test with ten metrics.

```python-run
import numpy as np
pvals = np.array([0.0002, 0.0009, 0.0041, 0.0098, 0.012, 0.021, 0.033, 0.048, 0.19, 0.44])
m, alpha = len(pvals), 0.05
print("unadjusted significant:", np.sum(pvals < alpha))
print("Bonferroni threshold", alpha / m, "-> significant:", np.sum(pvals < alpha / m))
order = np.argsort(pvals)
ranked = pvals[order]
bh_line = alpha * np.arange(1, m + 1) / m
below = ranked <= bh_line
k = np.max(np.nonzero(below)[0]) + 1 if below.any() else 0
print("BH thresholds:", np.round(bh_line, 3))
print("BH: largest k with p_(k) <= k/m * alpha is", k, "-> reject the", k, "smallest p-values")
```

**Reading this code line by line**

- `pvals` is already sorted here, but `np.argsort` makes the code work for any order.
- `bh_line` is the BH threshold for each rank: $0.005, 0.010, \dots, 0.050$.
- `below` marks ranks whose p-value is under its threshold; `np.nonzero(below)[0]` lists their positions, and the largest position plus one is $k$.

Without correction, 8 metrics look significant. Bonferroni (threshold 0.005) keeps 3. BH keeps 7: the 7th smallest p-value, 0.033, is under its threshold of 0.035, so all seven smallest are rejected. (BH looks for the largest qualifying rank; a p-value above its own line at an earlier rank would still be rejected if a later rank qualifies.) The p-value 0.048 at rank 8 fails its threshold of 0.040, and so do the last two.

Statsmodels does all of this and reports **adjusted p-values**, which can be compared directly with $\alpha$:

```python-run
import numpy as np
from statsmodels.stats.multitest import multipletests
pvals = np.array([0.0002, 0.0009, 0.0041, 0.0098, 0.012, 0.021, 0.033, 0.048, 0.19, 0.44])
for method in ["bonferroni", "holm", "fdr_bh"]:
    reject, adjusted, _, _ = multipletests(pvals, alpha=0.05, method=method)
    print(f"{method:10s} rejects {reject.sum()}  adjusted p: {np.round(adjusted, 3)}")
```

**Reading this code line by line**

- `multipletests(pvals, alpha, method)` returns four things: a true/false array of rejections, the adjusted p-values, and two values we ignore (`_`).
- `"fdr_bh"` is Benjamini-Hochberg.

Bonferroni and Holm each reject 3; BH rejects 7. Holm's adjusted p-values are smaller than Bonferroni's (for example 0.069 versus 0.098 for the fourth), showing it is uniformly at least as powerful even when, as here, the count happens to be the same.

## 6. Comparing the methods by simulation

To see the trade-off, simulate many studies of 100 tests where 10 effects are real and 90 are null.

```python-run
import numpy as np
from scipy import stats
from statsmodels.stats.multitest import multipletests
rng = np.random.default_rng(7)
runs, m, m_real = 1000, 100, 10
results = {"none": [], "bonferroni": [], "fdr_bh": []}
for _ in range(runs):
    z = rng.normal(0, 1, m)
    z[:m_real] += 3.0
    p = 2 * stats.norm.sf(np.abs(z))
    for method in results:
        rej = p < 0.05 if method == "none" else multipletests(p, 0.05, method=method)[0]
        false = rej[m_real:].sum()
        true = rej[:m_real].sum()
        results[method].append((false > 0, false / max(rej.sum(), 1), true))
for method, rows in results.items():
    rows = np.array(rows, dtype=float)
    print(f"{method:10s} P(any false) {rows[:, 0].mean():.3f}  FDR {rows[:, 1].mean():.3f}  real effects found {rows[:, 2].mean():.2f} of 10")
```

**Reading this code line by line**

- Each run creates 100 z statistics; the first 10 are shifted by 3 (real effects), the rest are pure noise. Two-sided p-values follow.
- For each method we record whether any false positive occurred, the false share among rejections (`max(..., 1)` avoids dividing by zero when nothing is rejected), and how many real effects were found.

Typical output: no correction makes at least one false claim in about 99% of studies, with roughly a third of "discoveries" false. Bonferroni brings the chance of any false claim down to about 5% but finds only about 3 of the 10 real effects. BH keeps the false share near 5% while finding about 5 real effects. Choose by cost: strict FWER control for decisions where any false claim hurts, FDR for screening.

## 7. Multiple testing in practice

Corrections are only part of the answer. Practical habits matter more.

- **Pre-register a primary metric.** Decide the one metric (or very few) that determines the decision before the test starts. Secondary and guardrail metrics are monitored but are not reasons to ship by themselves.
- **Treat segment results as hypotheses.** "The feature works for iOS users in Indonesia" found by slicing is a lead for a new targeted test, not a conclusion.
- **Use holdout data.** In modelling, the multiple-testing problem appears as overfitting: try enough features or models and one will fit noise. Cross-validation and a final untouched test set are the modelling equivalent of a correction.
- **Count all the comparisons**, including the ones you looked at and discarded. Corrections only work if $m$ is honest.
- **Beware the garden of forking paths**: even without formally running many tests, analysis choices made after seeing the data (which outliers to drop, which date range, which covariates) create hidden multiplicity.

> [!INTERVIEW]
> "We tested a redesign with 20 metrics; time-on-page improved with p = 0.03, the rest are flat. Ship?" Answer: 20 metrics at 5% give about a 64% chance of a false positive somewhere; 0.03 does not survive Bonferroni or Holm (thresholds start at 0.0025). Was time-on-page the pre-registered primary metric? If not, treat it as a hypothesis and re-test. Also ask whether more time on the page is even good (it can mean confusion).

## 8. Related ideas

- **ANOVA** (next lesson) tests whether *any* of several group means differ in one test, avoiding the inflation of testing every pair.
- **Tukey's HSD** (honestly significant difference) compares all pairs of groups after ANOVA with FWER control.
- **Bayesian hierarchical models** shrink many noisy segment estimates towards a common mean, an elegant alternative for many-segment analysis.

## Summary

- With $m$ tests at level $\alpha$, the chance of at least one false positive is $1-(1-\alpha)^m$: 64% for 20 tests.
- FWER is the probability of any false positive; FDR is the expected share of discoveries that are false.
- Bonferroni tests at $\alpha/m$; Holm's step-down method controls FWER with more power.
- Benjamini-Hochberg rejects the $k$ smallest p-values where $k$ is the largest rank with $p_{(k)} \le k\alpha/m$; it controls the FDR and keeps more power.
- Prevention beats correction: pre-register a primary metric, treat segment wins as hypotheses, and validate on new data.

## Glossary

- **Multiple testing (multiple comparisons)**: running many tests, inflating the chance of false positives.
- **Family**: the set of tests considered together.
- **Family-wise error rate (FWER)**: the probability of at least one false positive in the family.
- **False discovery rate (FDR)**: the expected share of rejections that are false.
- **Bonferroni correction**: testing each hypothesis at $\alpha/m$.
- **Union bound**: the probability of any of several events is at most the sum of their probabilities.
- **Holm's step-down method**: sequential thresholds $\alpha/m, \alpha/(m-1), \dots$ on sorted p-values.
- **Benjamini-Hochberg (BH)**: an FDR-controlling step-up procedure using thresholds $k\alpha/m$.
- **Adjusted p-value**: a p-value transformed so it can be compared directly with $\alpha$ after correction.
- **Primary / secondary / guardrail metric**: the deciding metric / supporting metrics / metrics that must not get worse.
- **Garden of forking paths**: hidden multiplicity from analysis choices made after seeing the data.
- **Tukey's HSD**: a method for comparing all pairs of group means with FWER control.

## Check yourself

```quiz
[
  {"q": "You check 20 independent metrics in an A/A test at α = 0.05. The chance at least one is significant is about…", "options": ["64%", "5%", "20%", "100%"], "answer": 0,
   "explain": "$1 - 0.95^{20} \\approx 0.64$."},
  {"q": "With 10 tests and α = 0.05, the Bonferroni threshold for each test is…", "options": ["0.005", "0.05", "0.5", "0.0005"], "answer": 0,
   "explain": "$\\alpha/m = 0.05/10$."},
  {"q": "What does controlling the false discovery rate at 5% promise?", "options": ["On average at most 5% of the rejected hypotheses are false positives", "At most a 5% chance of any false positive", "95% of real effects will be found", "Each test has α = 0.05"], "answer": 0,
   "explain": "FDR is about the share of discoveries that are false, not the chance of any."},
  {"q": "Sorted p-values 0.001, 0.008, 0.02, 0.2 with m = 4 and α = 0.05. How many does Benjamini-Hochberg reject?", "options": ["3", "1", "2", "4"], "answer": 0,
   "explain": "Thresholds are 0.0125, 0.025, 0.0375, 0.05. Rank 3: $0.02 \\le 0.0375$; rank 4: $0.2 > 0.05$. So k = 3."},
  {"q": "Why prefer Holm over plain Bonferroni?", "options": ["It controls the family-wise error rate equally well and is never less powerful", "It controls the FDR instead", "It needs independent tests", "It always rejects everything"], "answer": 0,
   "explain": "Holm's later thresholds are more lenient while keeping FWER control."},
  {"q": "Slicing an experiment by 40 country × platform segments finds one with p = 0.01. The best next step is…", "options": ["Treat it as a hypothesis and test it in a new, targeted experiment", "Launch only in that segment", "Report it as a confirmed finding", "Lower α to 0.01 for that segment"], "answer": 0,
   "explain": "With 40 slices, a p of 0.01 somewhere is unsurprising; confirm with fresh data."}
]
```

> **Source:** Bruce & Bruce, *Practical Statistics for Data Scientists* (O'Reilly, 2017), ch. 3, "Multiple Testing" (type 1 error inflation, adjustment of p-values, false discovery rate, overfitting); Benjamini & Hochberg (1995) for the FDR procedure; statsmodels documentation for `multipletests`.
