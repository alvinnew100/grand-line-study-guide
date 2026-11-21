# t-tests, z-tests and degrees of freedom

> **Before this lesson:** [Statistical significance, p-values and their misconceptions](#/lesson/statistics/p-values) (p-values, alpha, type I and II errors), [Normal, t and long-tailed distributions](#/lesson/statistics/normal-t-long-tails) (the t-distribution) and the standard error of a difference from [Sampling distributions, standard error and the central limit theorem](#/lesson/statistics/sampling-distribution-clt).

## In plain words

The permutation test builds the null distribution by shuffling. Long before computers made shuffling cheap, statisticians derived formulas for the null distribution instead. The most important are the **t-test** for comparing means and the **z-test** for comparing proportions. They are fast, available everywhere, and with reasonably large samples they give essentially the same answers as permutation tests. This lesson covers the one-sample, two-sample (Welch) and paired t-tests, the two-proportion z-test, the idea of degrees of freedom, and what to do when the data are badly skewed.

An everyday picture: a t-statistic is a signal-to-noise ratio. The signal is the difference you observed. The noise is how much that difference would wobble by chance (its standard error). If the signal is three times the noise, chance is an unlikely explanation; if the signal is half the noise, it is a likely one.

Why it matters for a job: A/B testing platforms run these tests under the hood, and analysts run them by hand in notebooks every day. Interviewers ask you to compute a z-statistic for two conversion rates on a whiteboard, to explain when to use a paired test, and why Welch's t-test is the safer default.

## 1. The general shape of a test statistic

Almost every classical test statistic has the form

$$\text{statistic} = \frac{\text{observed difference} - \text{difference under } H_0}{\text{standard error of the difference}}$$

Under the null hypothesis the difference is usually 0. If the null is true, this ratio follows a known distribution (normal or t), and the p-value is the tail area beyond the observed value.

## 2. The one-sample t-test

Question: is a mean different from a fixed reference value $\mu_0$? For example, is the average delivery time different from the promised 30 minutes?

$$t = \frac{\bar{x} - \mu_0}{s/\sqrt{n}}, \qquad \text{df} = n - 1$$

In SciPy: `stats.ttest_1samp(x, popmean=30)`. The t-distribution, rather than the normal, accounts for estimating the standard deviation $s$ from the sample, as explained in the confidence-interval lesson.

## 3. The two-sample t-test: Welch's version

Question: do two independent groups have different means? With group sizes $n_A, n_B$, means $\bar{x}_A, \bar{x}_B$ and standard deviations $s_A, s_B$:

$$t = \frac{\bar{x}_B - \bar{x}_A}{\sqrt{\dfrac{s_A^2}{n_A} + \dfrac{s_B^2}{n_B}}}$$

The denominator is the standard error of the difference. This is **Welch's t-test**, which does not assume the two groups have equal variances. Its degrees of freedom come from the **Welch-Satterthwaite** formula, which usually gives a non-integer:

$$\text{df} = \frac{\left(\frac{s_A^2}{n_A} + \frac{s_B^2}{n_B}\right)^2}{\frac{(s_A^2/n_A)^2}{n_A - 1} + \frac{(s_B^2/n_B)^2}{n_B - 1}}$$

```python-run
import numpy as np
from scipy import stats
a = np.array([12.1, 9.8, 11.4, 10.2, 13.0, 9.5, 10.8, 11.9, 10.1, 12.4])
b = np.array([13.5, 12.2, 14.8, 11.9, 15.1, 12.7, 13.9, 16.0])
va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
t = (b.mean() - a.mean()) / np.sqrt(va + vb)
df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
p = 2 * stats.t.sf(abs(t), df)
print(f"by hand: t = {t:.3f}, df = {df:.2f}, p = {p:.5f}")
res = stats.ttest_ind(b, a, equal_var=False)
print(f"scipy  : t = {res.statistic:.3f}, p = {res.pvalue:.5f}")
ci = res.confidence_interval(0.95)
print(f"95% CI for mean(b) - mean(a): ({ci.low:.2f}, {ci.high:.2f})")
```

**Reading this code line by line**

- `a` and `b` are task-completion times (minutes) for two versions of a checkout flow, with 10 and 8 users.
- `va` and `vb` are each group's variance divided by its size; their sum is the squared standard error of the difference.
- `df` is the Welch-Satterthwaite formula. `2 * stats.t.sf(abs(t), df)` is the two-sided p-value: twice the tail area beyond $|t|$.
- `stats.ttest_ind(b, a, equal_var=False)` runs Welch's test in one call. The result object also offers `confidence_interval()` (in recent SciPy versions).

The by-hand and SciPy results match: $t = 4.106$ on 13.59 degrees of freedom, $p = 0.00114$. The difference in means is about 2.6 minutes with a 95% CI of (1.26, 4.03). Strong evidence that the flows differ.

### Why Welch and not the classic "Student" version?

The classic two-sample t-test pools the two variances into one, assuming the groups have equal spread (`equal_var=True`, SciPy's default!). When the spreads differ, and especially when the smaller group has the larger spread, the pooled test can be badly wrong.

```python-run
import numpy as np
from scipy import stats
rng = np.random.default_rng(3)
reps = 20_000
a = rng.normal(0, 1, size=(reps, 40))
b = rng.normal(0, 4, size=(reps, 10))
p_student = stats.ttest_ind(a, b, axis=1, equal_var=True).pvalue
p_welch = stats.ttest_ind(a, b, axis=1, equal_var=False).pvalue
print("null true, unequal SDs and sizes; false-positive rate at 0.05")
print("  Student (pooled):", round(np.mean(p_student < 0.05), 3))
print("  Welch           :", round(np.mean(p_welch < 0.05), 3))
```

**Reading this code line by line**

- Each of 20,000 simulated experiments compares 40 values with standard deviation 1 and 10 values with standard deviation 4. Both groups have mean 0, so the null is true and every rejection is a false positive.
- `axis=1` runs one test per row.

The pooled test rejects 29.6% of the time instead of 5%: six times too many false alarms. Welch's test holds the line at 5.3%. When variances are equal, Welch loses almost nothing. So use Welch (`equal_var=False`) by default.

## 4. Degrees of freedom

**Degrees of freedom** (df) is the number of independent pieces of information left to estimate variability after estimating other quantities. In a one-sample t-test we use one df to estimate the mean, so $n - 1$ remain. In regression with $p$ predictors plus an intercept, $n - p - 1$ remain. Degrees of freedom set the shape of the t (and chi-square and F) distributions: fewer df, heavier tails, larger critical values.

For data scientists, df rarely matters with big samples: at $n = 10{,}000$, $n$ and $n - 1$ are interchangeable. It does matter in two places: small samples (where the t critical value is noticeably larger than 1.96) and regression with categorical variables, where a category with $k$ levels needs only $k - 1$ indicator columns. Using all $k$ makes the columns redundant, a problem discussed in [Factor variables and interpreting regression](#/lesson/statistics/factors-interpretation).

## 5. The paired t-test

Sometimes the two measurements are not independent: the same users before and after a change, the same products priced two ways, or two models scored on the same test examples. Then you should analyse the **differences** within each pair. A **paired t-test** is a one-sample t-test on those differences, testing whether their mean is 0.

```python-run
import numpy as np
from scipy import stats
rng = np.random.default_rng(4)
n = 30
baseline = rng.normal(50, 12, n)
before = baseline + rng.normal(0, 3, n)
after = baseline + 2 + rng.normal(0, 3, n)
print("paired t-test   p =", round(stats.ttest_rel(after, before).pvalue, 5))
print("unpaired t-test p =", round(stats.ttest_ind(after, before).pvalue, 5))
print("mean change:", round((after - before).mean(), 2), " SD of changes:", round((after - before).std(ddof=1), 2),
      " SD of scores:", round(before.std(ddof=1), 2))
```

**Reading this code line by line**

- Each of 30 users has a personal `baseline` score; users differ a lot (SD 12).
- `before` and `after` add small measurement noise; `after` also adds a true improvement of 2 points.
- `stats.ttest_rel` is the paired ("related samples") t-test; `stats.ttest_ind` wrongly treats the two columns as independent groups.

The paired test finds the improvement ($p = 0.028$); the unpaired test does not ($p = 0.60$). The reason is in the last line: the differences have SD 4.56, while scores vary between users with SD 13.44. Pairing removes the large between-user variation and leaves only the small within-user noise. The same idea powers variance-reduction methods in A/B tests, such as using each user's pre-experiment behaviour as a covariate (a technique known as CUPED).

## 6. The two-proportion z-test

For conversion rates the standard test is the **two-proportion z-test**. Under the null hypothesis both groups share one rate, estimated by pooling: $\hat{p} = (x_A + x_B)/(n_A + n_B)$. Then

$$z = \frac{\hat{p}_B - \hat{p}_A}{\sqrt{\hat{p}(1-\hat{p})\left(\frac{1}{n_A} + \frac{1}{n_B}\right)}}$$

and the p-value comes from the standard normal. (For a confidence interval we use the unpooled standard error, as in the CI lesson, because there we are not assuming the null.)

```python-run
import numpy as np
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest
conv = np.array([245, 200])
nobs = np.array([2000, 2000])
p1, p2 = conv / nobs
pool = conv.sum() / nobs.sum()
z = (p1 - p2) / np.sqrt(pool * (1 - pool) * (1 / nobs[0] + 1 / nobs[1]))
print(f"by hand    : z = {z:.3f}, p = {2 * stats.norm.sf(abs(z)):.4f}")
z_sm, p_sm = proportions_ztest(conv, nobs)
print(f"statsmodels: z = {z_sm:.3f}, p = {p_sm:.4f}")
```

**Reading this code line by line**

- `conv` holds conversions (treatment 245, control 200) and `nobs` the number of users in each arm.
- `pool` is the pooled conversion rate under the null.
- `proportions_ztest(count, nobs)` from statsmodels returns the z statistic and two-sided p-value.

Both give $z = 2.263$, $p = 0.0236$, matching the permutation test from the earlier lesson (0.027). The z-test is a t-test in disguise: a proportion is the mean of 0/1 values, and with thousands of users the t and normal distributions coincide.

> [!INTERVIEW]
> Whiteboard version: rates 12.25% and 10%, pooled 11.125%, SE $= \sqrt{0.11125 \times 0.88875 \times (1/2000 + 1/2000)} \approx 0.00995$; $z = 0.0225 / 0.00995 \approx 2.26$, beyond 1.96, so significant at 5%. Practise this until it is automatic.

## 7. When the data are badly skewed

The t-test compares means, and thanks to the central limit theorem it works for skewed data when samples are large. With moderate samples and heavy skew, though, a few huge values inflate the variance and the test loses power. Options:

- **Mann-Whitney U test** (also called the Wilcoxon rank-sum test): a rank-based test of whether values in one group tend to be larger than in the other. Robust to outliers.
- **Test on the log scale**: for positive, multiplicative data (revenue, durations), compare means of $\log(x)$. Note this tests a different question (roughly, the ratio of geometric means).
- **Permutation test or bootstrap** on whatever statistic matters, such as the median or a trimmed mean.

```python-run
import numpy as np
from scipy import stats
rng = np.random.default_rng(5)
a = rng.lognormal(3.0, 1.2, 60)
b = rng.lognormal(3.5, 1.2, 60)
print("Welch t-test p     :", round(stats.ttest_ind(b, a, equal_var=False).pvalue, 4))
print("Mann-Whitney U p   :", round(stats.mannwhitneyu(b, a).pvalue, 4))
print("t-test on log scale:", round(stats.ttest_ind(np.log(b), np.log(a), equal_var=False).pvalue, 4))
```

**Reading this code line by line**

- Two groups of 60 heavily skewed (lognormal) values; group B is truly shifted upward.
- We compare Welch's test on raw values, the Mann-Whitney test and Welch's test on logs.

Welch on the raw values misses the shift ($p = 0.149$) because a few giant values make the standard error large. Mann-Whitney ($p = 0.0038$) and the log-scale test ($p = 0.0039$) detect it easily. Choose the test that matches your question: if the business cares about total revenue, the mean matters and you may need more data or capping; if it cares whether typical users improved, a rank or log test is appropriate.

## 8. Which test when?

| Question | Test | Python |
|---|---|---|
| One mean vs a fixed value | one-sample t | `stats.ttest_1samp` |
| Two independent means | Welch t | `stats.ttest_ind(..., equal_var=False)` |
| Same units measured twice | paired t | `stats.ttest_rel` |
| Two proportions | two-proportion z | `proportions_ztest` |
| Skewed data, "tends to be larger" | Mann-Whitney U | `stats.mannwhitneyu` |
| More than two groups | ANOVA / chi-square | next lessons |
| Any statistic, few assumptions | permutation test | `stats.permutation_test` |

## Common mistakes

- Leaving SciPy's default `equal_var=True` on when group variances differ.
- Using an unpaired test for paired data, throwing away a huge amount of power.
- Testing at the page-view level when users were randomised (observations are not independent).
- Using the pooled standard error to build a confidence interval for the difference.
- Concluding "no effect" from a t-test on heavily skewed data with modest samples.

## Summary

- Test statistics are (observed difference − null difference) / standard error; compare with the t or normal distribution.
- Welch's t-test compares two means without assuming equal variances; use it by default.
- Degrees of freedom count the independent information left after estimation; they matter for small samples.
- Paired t-tests analyse within-unit differences and can be far more powerful.
- The two-proportion z-test uses a pooled rate under the null; it agrees with permutation tests for large samples.
- For heavy skew, consider Mann-Whitney, a log-scale test, or resampling.

## Glossary

- **t-test**: a test whose statistic follows a t-distribution under the null.
- **One-sample t-test**: compares a mean with a fixed value.
- **Welch's t-test**: compares two independent means without assuming equal variances.
- **Student's (pooled) t-test**: the version that assumes equal variances.
- **Welch-Satterthwaite formula**: the degrees-of-freedom formula for Welch's test.
- **Degrees of freedom (df)**: independent pieces of information left after estimation.
- **Paired t-test**: a one-sample t-test on within-pair differences.
- **Two-proportion z-test**: compares two rates using a pooled rate and the normal distribution.
- **Pooled rate**: the overall rate across both groups, used under the null.
- **Mann-Whitney U (Wilcoxon rank-sum) test**: a rank-based comparison of two groups.
- **CUPED**: a variance-reduction method that adjusts experiment metrics using pre-experiment data.

## Check yourself

```quiz
[
  {"q": "Why prefer Welch's t-test over the pooled (Student) two-sample t-test?", "options": ["It stays valid when group variances differ and loses little when they are equal", "It is always more powerful", "It does not need any data", "It compares medians"], "answer": 0,
   "explain": "The simulation showed the pooled test with a 30% false-positive rate under unequal variances; Welch stayed at 5%."},
  {"q": "30 users are measured before and after a change. The right test is…", "options": ["a paired t-test on the differences", "Welch's two-sample t-test", "a chi-square test", "a two-proportion z-test"], "answer": 0,
   "explain": "Measurements on the same users are dependent; differencing removes between-user variation."},
  {"q": "Control converts 200/2000 and treatment 245/2000. The pooled rate under the null is…", "options": ["11.125%", "10%", "12.25%", "22.25%"], "answer": 0,
   "explain": "(200 + 245) / 4000 = 0.11125."},
  {"q": "A t-statistic of 0.5 means…", "options": ["the observed difference is half its standard error, easily explained by chance", "the effect is 50%", "p = 0.5 exactly", "the groups have equal variances"], "answer": 0,
   "explain": "The statistic is a signal-to-noise ratio; 0.5 is small."},
  {"q": "In a one-sample t-test with n = 25, the degrees of freedom are…", "options": ["24", "25", "23", "50"], "answer": 0,
   "explain": "One degree of freedom is used to estimate the mean."},
  {"q": "Revenue per user is very skewed and a Welch test on 60 users per arm gives p = 0.15, while Mann-Whitney gives p = 0.004. What is going on?", "options": ["A few huge values inflate the standard error of the mean; the rank test detects that typical values shifted", "Mann-Whitney is wrong", "The groups are paired", "The t-test needs equal sample sizes"], "answer": 0,
   "explain": "Heavy tails hurt mean-based tests at moderate n; the tests also answer slightly different questions."}
]
```

> **Source:** Bruce & Bruce, *Practical Statistics for Data Scientists* (O'Reilly, 2017), ch. 3, "t-Tests" and "Degrees of Freedom"; SciPy documentation for `ttest_ind`, `ttest_rel`, `mannwhitneyu`; statsmodels documentation for `proportions_ztest`.
