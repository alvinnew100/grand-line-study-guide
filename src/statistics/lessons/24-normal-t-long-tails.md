# Normal, t and long-tailed distributions

> **Before this lesson:** [Sampling distributions, standard error and the central limit theorem](#/lesson/statistics/sampling-distribution-clt) (why averages become bell-shaped) and [Confidence intervals done right](#/lesson/statistics/confidence-intervals), which used critical values from the normal and t-distributions. Percentiles come from [Estimates of variability](#/lesson/statistics/variability).

## In plain words

The **normal distribution** is the famous bell curve: symmetric, with most values near the middle and fewer and fewer further out. It is the backbone of classical statistics, mainly because of the central limit theorem: averages and sums of many random pieces tend to be normal. The **t-distribution** is its slightly wider cousin, used when the standard deviation must be estimated from a small sample. And much real data is not normal at all but **long-tailed**: extreme values happen far more often than the bell curve allows.

An everyday picture: adult heights are close to normal; almost nobody is twice the average height. Wealth is long-tailed: a few people own vastly more than the average, and "twice the average" is not rare at all. Treating wealth like height leads to badly wrong conclusions.

Why it matters for a job: you will compute z-scores and normal probabilities constantly (for tests, alerts and intervals), read QQ plots to judge whether data are normal, and need to know when normal-based reasoning is dangerous. Interviewers ask about the 68-95-99.7 rule, what a z-score is, how to check normality, and why the t-distribution has heavier tails.

## 1. The normal distribution

A normal distribution is described by two numbers: its mean $\mu$ (the centre) and its standard deviation $\sigma$ (the width). Its **probability density function** (PDF), the formula for the height of the curve, is

$$f(x) = \frac{1}{\sigma\sqrt{2\pi}}\exp\!\left(-\frac{(x-\mu)^2}{2\sigma^2}\right)$$

You will rarely use this formula directly. What matters is that for a continuous distribution, probabilities are *areas* under the density curve. The **cumulative distribution function** (CDF), $F(x) = P(X \le x)$, gives the area to the left of $x$.

The **standard normal** has $\mu = 0$ and $\sigma = 1$ and is usually written $Z$. Every normal variable can be converted to it.

### The 68-95-99.7 rule

```python-run
from scipy import stats
for k in [1, 2, 3]:
    share = stats.norm.cdf(k) - stats.norm.cdf(-k)
    print(f"within {k} SD of the mean: {share:.4f}")
print("z for the 97.5th percentile:", round(stats.norm.ppf(0.975), 3))
print("P(Z > 2.5):", round(stats.norm.sf(2.5), 5))
```

**Reading this code line by line**

- `stats.norm` is SciPy's standard normal distribution. `.cdf(k)` is the area to the left of `k`, so `cdf(k) - cdf(-k)` is the area between $-k$ and $k$.
- `.ppf(q)` (percent point function) is the inverse of the CDF: the value with a share `q` of the area to its left.
- `.sf(x)` is the **survival function**, $1 - \text{CDF}$: the area to the *right* of `x`. It is more accurate than `1 - cdf(x)` for far tails.

About 68.27% of a normal distribution lies within one standard deviation of the mean, 95.45% within two and 99.73% within three. The 97.5th percentile is 1.96, which is where the "95% within 1.96 SD" of confidence intervals comes from. Values beyond 2.5 SD on one side are rare: 0.621%.

## 2. z-scores and standardisation

A **z-score** says how many standard deviations a value is from the mean:

$$z = \frac{x - \mu}{\sigma}$$

Converting every value this way is called **standardisation** (or normalisation); the result has mean 0 and standard deviation 1. Standardising puts variables measured in different units on a common scale, which is essential for distance-based methods such as k-nearest neighbours and clustering, and makes "how unusual is this value?" easy to answer.

```python-run
from scipy import stats
height = stats.norm(loc=170, scale=7)
print("P(height < 160)        :", round(height.cdf(160), 4))
print("P(180 < height < 190)  :", round(height.cdf(190) - height.cdf(180), 4))
print("90th percentile height :", round(height.ppf(0.90), 1))
z = (185 - 170) / 7
print("z-score of 185 cm      :", round(z, 3), " share taller:", round(stats.norm.sf(z), 4))
```

**Reading this code line by line**

- `stats.norm(loc=170, scale=7)` creates a **frozen** distribution object: a normal with mean 170 cm and standard deviation 7 cm whose methods no longer need the parameters.
- The probability of a range is a difference of two CDF values.
- `ppf(0.90)` gives the height below which 90% of people fall.

7.66% of people are shorter than 160 cm; 7.44% are between 180 and 190 cm; the 90th percentile is 179.0 cm. Someone 185 cm tall has $z = 2.143$, and only 1.61% of people are taller.

> [!TIP]
> Interview arithmetic without a computer: memorise 1.645 (90% two-sided, or the 95th percentile), 1.96 (95% two-sided), 2.576 (99% two-sided), and the 68-95-99.7 rule. Most normal questions reduce to these.

## 3. Is my data normal? QQ plots

Most raw data in business are *not* normal: durations, revenue, counts and ratios are skewed and bounded at zero. Normality matters mainly for small-sample methods and for residuals in regression; for large-sample means the central limit theorem takes over. Still, you should know how to check.

A **QQ plot** (quantile-quantile plot) compares the sorted, standardised sample with the quantiles a normal distribution would produce. If the data are normal, the points lie close to a straight diagonal line. Points curving away at the ends reveal skew or heavy tails. Here is the comparison as numbers.

```python-run
import numpy as np
from scipy import stats
rng = np.random.default_rng(12)
samples = {"normal": rng.normal(50, 10, 300), "lognormal": rng.lognormal(3, 0.7, 300)}
probs = [0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]
for name, x in samples.items():
    z = (x - x.mean()) / x.std(ddof=1)
    print(name, "standardised sample quantiles:", np.round(np.quantile(z, probs), 2))
print("normal theory quantiles             :", np.round(stats.norm.ppf(probs), 2))
for name, x in samples.items():
    (osm, osr), (slope, intercept, r) = stats.probplot(x, dist="norm")
    print(f"{name}: QQ-plot straightness r = {r:.4f}")
```

**Reading this code line by line**

- We draw 300 values from a normal and 300 from a skewed lognormal distribution, and standardise each sample.
- `np.quantile(z, probs)` gives the sample's quantiles at the listed probabilities; `stats.norm.ppf(probs)` gives what a perfect normal would show. A QQ plot draws one against the other.
- `stats.probplot` computes the full QQ plot data and fits a straight line through it; the unpacking `(osm, osr), (slope, intercept, r) = ...` extracts the theoretical quantiles, the ordered sample, and the line's slope, intercept and correlation `r`.

The normal sample's quantiles (−2.31, −1.70, ..., 2.18) track the theoretical ones (−2.33, −1.64, ..., 2.33) closely, and the QQ points have correlation 0.9989 with a straight line. The lognormal sample's lower quantiles are squashed (−1.13 instead of −2.33) and its upper tail stretched (3.38 instead of 2.33), and $r$ falls to 0.9027. On a plot this shows as a curve bending upward at the right: the signature of right skew.

Formal tests such as Shapiro-Wilk (`stats.shapiro`) exist, but with large samples they reject normality for tiny, harmless departures, and with small samples they miss real ones. Look at the QQ plot and think about whether the departure matters for your method.

## 4. Long-tailed distributions

A **tail** is the long, thin part of a distribution where extreme values live. A distribution is **long-tailed** (or heavy-tailed, or fat-tailed) when extreme values are much more common than under a normal distribution. Examples are everywhere in data science: income and wealth, file sizes, city populations, the number of followers per account, revenue per customer, insurance claims and daily stock returns. Many follow a **power law**, where a small share of units accounts for a large share of the total (sometimes called the 80/20 or Pareto principle).

**Kurtosis** measures tail heaviness. SciPy reports **excess kurtosis**, which is 0 for a normal distribution and positive for heavier tails.

```python-run
import numpy as np
from scipy import stats
rng = np.random.default_rng(5)
n = 250 * 20
normal_ret = rng.normal(0, 1, n)
heavy_ret = stats.t.rvs(df=3, size=n, random_state=rng)
for name, r in [("normal", normal_ret), ("t with 3 df", heavy_ret)]:
    z = (r - r.mean()) / r.std()
    print(f"{name:12s} days beyond 4 SD: {np.sum(np.abs(z) > 4):3d}   kurtosis: {stats.kurtosis(r):6.2f}")
print("normal theory expects:", round(n * 2 * stats.norm.sf(4), 2), "days beyond 4 SD")
```

**Reading this code line by line**

- We simulate 20 years of daily returns (250 trading days a year): once from a normal distribution and once from a t-distribution with 3 degrees of freedom, a common model for heavy-tailed financial returns. `stats.t.rvs` draws random values; passing our generator as `random_state` keeps it repeatable.
- Each series is standardised, and we count days more than 4 standard deviations from the mean.
- `stats.kurtosis` returns excess kurtosis.

The normal series has no 4-SD days, matching theory (0.32 expected in 5,000 days). The heavy-tailed series has 33 such days and an excess kurtosis of 34.5. If a risk model assumed normality, it would call a 4-SD day a once-in-sixty-years event; under heavy tails it happens every few months. This is a core reason why "black swan" events surprise people who rely on bell curves.

What long tails mean for analysis:

- Means and standard deviations become unstable; medians, percentiles and log transforms are more reliable.
- A/B tests on heavy-tailed metrics need far more data, or capping (winsorising), or tests on the log scale.
- Outliers may be the most important records (the few customers who generate most revenue), not errors.

## 5. Student's t-distribution

The t-distribution, met in the confidence-interval lesson, is the distribution of a standardised sample mean when the standard deviation is estimated from the sample:

$$t = \frac{\bar{x} - \mu}{s/\sqrt{n}}$$

Because $s$ itself is uncertain, $t$ varies more than $z$, and its distribution has heavier tails than the normal. How much heavier depends on the degrees of freedom (df), $n - 1$ for one sample.

```python-run
from scipy import stats
print(" df   t(0.975)  P(|T| > 3)")
for df in [2, 5, 10, 30, 100]:
    print(f"{df:>3}   {stats.t.ppf(0.975, df):7.3f}   {2 * stats.t.sf(3, df):.4f}")
print("normal", f"{stats.norm.ppf(0.975):7.3f}   {2 * stats.norm.sf(3):.4f}")
```

**Reading this code line by line**

- For each df, `stats.t.ppf(0.975, df)` is the 95% two-sided critical value and `2 * stats.t.sf(3, df)` is the probability of landing more than 3 units from 0 in either direction.

With 2 df the critical value is 4.303 and a value beyond ±3 has probability 0.0955, versus 0.0027 for the normal. By 30 df the critical value is 2.042, and by 100 df it is 1.984, nearly the normal's 1.960. In practice: t matters for small samples; for thousands of users per group, t and z give the same answers.

The t-distribution is used for confidence intervals and tests on means, for regression coefficients, and (as we saw) as a model for heavy-tailed data.

## 6. Other continuous distributions worth knowing

- **Uniform**: every value in an interval equally likely; used for random number generation and for p-values under the null hypothesis (a fact you will meet later).
- **Lognormal**: the logarithm is normal; models durations, prices and incomes.
- **Exponential**: waiting times between independent events; covered with the Poisson in [Binomial, Poisson and other common distributions](#/lesson/statistics/discrete-distributions).
- **Chi-square** and **F**: distributions of sums of squared normal values and of ratios of variances; used in the chi-square test and ANOVA.

## Common mistakes

- Assuming business data are normal without looking.
- Using the 68-95-99.7 rule on skewed data to set alert thresholds.
- Running a normality test on 100,000 rows and panicking when it rejects; the departure may be irrelevant.
- Forgetting that the t-distribution, not the normal, governs small-sample means with estimated SD.
- Deleting extreme values from long-tailed data when they carry most of the business value.

## Summary

- The normal distribution is set by its mean and SD; probabilities are areas from the CDF; 68%, 95% and 99.7% lie within 1, 2 and 3 SD.
- A z-score is (value − mean) / SD; standardising puts variables on one scale.
- QQ plots compare sample and normal quantiles; curvature reveals skew or heavy tails.
- Long-tailed data have far more extreme values than the normal predicts; prefer robust summaries, logs and capping.
- Student's t has heavier tails than the normal, depends on degrees of freedom and approaches the normal for large samples.

## Glossary

- **Normal distribution**: the symmetric bell-shaped distribution set by $\mu$ and $\sigma$.
- **Standard normal ($Z$)**: the normal with mean 0 and SD 1.
- **PDF (probability density function)**: the height of the curve; probabilities are areas under it.
- **CDF (cumulative distribution function)**: $P(X \le x)$.
- **Survival function**: $P(X > x) = 1 - \text{CDF}$.
- **Percent point function (ppf)**: the inverse CDF.
- **z-score**: the number of SDs a value lies from the mean.
- **Standardisation (normalisation)**: converting values to z-scores.
- **Frozen distribution**: a SciPy distribution object with its parameters fixed.
- **QQ plot**: a plot of sample quantiles against theoretical quantiles.
- **Tail / long-tailed distribution**: the extreme part of a distribution / one where extremes are common.
- **Power law**: a long-tailed pattern where a few units account for much of the total.
- **Kurtosis / excess kurtosis**: tail heaviness / kurtosis minus that of a normal (0 for normal).
- **Student's t-distribution**: the distribution of a standardised mean with estimated SD.

## Check yourself

```quiz
[
  {"q": "About what share of a normal distribution lies within 2 SD of the mean?", "options": ["95%", "68%", "99.7%", "50%"], "answer": 0,
   "explain": "68-95-99.7: two SDs cover about 95.45%."},
  {"q": "Heights are normal with mean 170 cm and SD 7 cm. The z-score of 184 cm is…", "options": ["2", "14", "1.4", "0.2"], "answer": 0,
   "explain": "$(184 - 170)/7 = 2$."},
  {"q": "On a QQ plot against the normal, the points bend sharply upward at the right end. The data are most likely…", "options": ["right-skewed or heavy-tailed on the right", "perfectly normal", "left-skewed", "uniform"], "answer": 0,
   "explain": "The largest values are larger than a normal would produce."},
  {"q": "Why does the t-distribution have heavier tails than the normal?", "options": ["It accounts for the extra uncertainty of estimating the SD from the sample", "It is used for skewed data only", "Its mean is larger", "It has no variance"], "answer": 0,
   "explain": "With small samples $s$ can be well off from $\\sigma$, so standardised means vary more."},
  {"q": "As degrees of freedom grow, the t critical value for 95% two-sided confidence…", "options": ["approaches 1.96", "approaches 0", "grows without bound", "stays at 2.776"], "answer": 0,
   "explain": "The t-distribution converges to the standard normal."},
  {"q": "Daily returns have excess kurtosis of 30. Compared with a normal model, 4-SD days are…", "options": ["much more common", "much rarer", "equally common", "impossible"], "answer": 0,
   "explain": "Large positive excess kurtosis means heavy tails: extreme days happen far more often."},
  {"q": "Which scipy.stats method gives $P(X > x)$ most accurately for a far tail?", "options": ["`sf`", "`pdf`", "`ppf`", "`mean`"], "answer": 0,
   "explain": "The survival function avoids the rounding error of computing 1 − cdf for tiny tail areas."}
]
```

> **Source:** Bruce & Bruce, *Practical Statistics for Data Scientists* (O'Reilly, 2017), ch. 2, "Normal Distribution" (standard normal and QQ-plots), "Long-Tailed Distributions" and "Student's t-Distribution"; SciPy documentation for `scipy.stats.norm`, `t` and `probplot`.
