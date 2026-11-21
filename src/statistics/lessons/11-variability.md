# Estimates of variability

> **Before this lesson:** [Data types and estimates of location](#/lesson/statistics/data-and-location), which introduced the mean, median, outliers and robust estimates. Variance as a property of a random variable appeared in [Probability, conditional probability and Bayes' rule](#/lesson/statistics/probability-bayes).

## In plain words

Knowing the typical value is only half the story. Two delivery services can both average 30 minutes, but if one always arrives between 28 and 32 minutes and the other anywhere from 5 to 90, you would choose the first without hesitation. **Variability** (also called dispersion or spread) measures how far values tend to be from the centre. This lesson covers the main measures: deviations, variance and standard deviation, the mean and median absolute deviation, the range, percentiles and the interquartile range.

An everyday picture: two archers who both hit the centre of the target on average. One groups every arrow within a hand's width; the other scatters arrows all over the boards. Same location, very different variability.

Why it matters for a job: variability is the heart of statistics. It decides how many users an experiment needs, how wide a confidence interval is, whether an alert should fire, and how reliable a service-level promise ("95% of orders delivered in 40 minutes") really is. Interviewers ask why sample variance divides by $n-1$, when to use the interquartile range instead of the standard deviation, and how to compute a percentile by hand. You will be able to answer all three.

## 1. Deviations

A **deviation** (also called a residual or error) is the difference between a value and an estimate of location, usually the mean: $x_i - \bar{x}$. Deviations tell you how far each value is from the centre and in which direction. A natural first idea is to average them, but that always gives exactly zero, because the positive and negative deviations cancel by construction of the mean. Every measure of variability is a way of averaging deviations without letting them cancel.

## 2. Mean absolute deviation, variance and standard deviation

There are two ways to stop cancellation: take absolute values, or square.

The **mean absolute deviation** averages the absolute deviations:

$$\text{mean absolute deviation} = \frac{1}{n}\sum_{i=1}^n |x_i - \bar{x}|$$

The **variance** averages squared deviations, with a small twist explained in section 3:

$$s^2 = \frac{1}{n-1}\sum_{i=1}^n (x_i - \bar{x})^2$$

The **standard deviation** is the square root of the variance, $s = \sqrt{s^2}$. Squaring changes the units (minutes become minutes squared), so the square root brings the measure back to the original units, which is why the standard deviation, not the variance, is what people quote.

Let us compute them for ten delivery times in minutes.

```python-run
import numpy as np
from scipy import stats
mins = np.array([22, 25, 27, 28, 30, 31, 33, 35, 38, 41])
dev = mins - mins.mean()
print("mean:", mins.mean(), " deviations:", dev)
print("mean absolute deviation:", np.mean(np.abs(dev)))
print("variance (n-1):", round(mins.var(ddof=1), 3), " std (n-1):", round(mins.std(ddof=1), 3))
print("variance (n)  :", round(mins.var(ddof=0), 3), " std (n)  :", round(mins.std(ddof=0), 3))
print("median absolute deviation:", stats.median_abs_deviation(mins))
print("range:", mins.max() - mins.min())
q1, q3 = np.percentile(mins, [25, 75])
print("Q1, Q3:", q1, q3, " IQR:", q3 - q1, " (scipy iqr:", stats.iqr(mins), ")")
```

**Reading this code line by line**

- `mins - mins.mean()` subtracts the mean (31.0) from every value at once; NumPy applies arithmetic element by element. The deviations sum to zero.
- `np.abs` takes absolute values; their mean, 4.6, is the mean absolute deviation.
- `.var(ddof=1)` and `.std(ddof=1)` compute the variance and standard deviation dividing by $n - 1$. The argument `ddof` means "delta degrees of freedom": the divisor is $n - \text{ddof}$. With `ddof=0` NumPy divides by $n$.
- `stats.median_abs_deviation` and `stats.iqr` come from SciPy and are explained in sections 4 and 5.

The standard deviation is 5.888 minutes with the $n-1$ divisor and 5.586 with $n$.

> [!WARNING]
> NumPy's `.std()` and `.var()` divide by $n$ by default (`ddof=0`), while pandas' `.std()` and `.var()` divide by $n-1$ (`ddof=1`). The same data can give two different answers depending on the library. State the divisor explicitly whenever it matters.

Why square rather than take absolute values? Mostly mathematical convenience. Squared deviations are smooth and easy to differentiate, which is why least-squares regression is so tractable; variances of independent quantities add up; and the normal distribution is described by its variance. The mean absolute deviation is easier to explain but has fewer of these handy properties.

## 3. Why divide by n − 1? Degrees of freedom

If we knew the population mean $\mu$, averaging $(x_i - \mu)^2$ with divisor $n$ would be fine. But we use $\bar{x}$, which is computed from the same data. The sample mean always sits in the middle of the sample, closer to the data points than the true mean usually is, so squared deviations from $\bar{x}$ are on average a bit too small. Dividing by $n - 1$ instead of $n$ inflates the estimate by exactly the right amount to correct this.

Another way to say it is **degrees of freedom**: the number of values that are free to vary once an estimate is fixed. Once you know the mean of 10 numbers and any 9 of them, the tenth is determined. So 10 deviations from $\bar{x}$ carry only 9 independent pieces of information. An estimate that is right on average is called **unbiased**; dividing by $n - 1$ makes the sample variance unbiased.

A simulation shows this. We take 100,000 samples of size 5 from a population whose true variance is 4 and average the two versions of the variance.

```python-run
import numpy as np
rng = np.random.default_rng(42)
true_var = 4.0
samples = rng.normal(loc=10, scale=2, size=(100_000, 5))
v_n = samples.var(axis=1, ddof=0)
v_n1 = samples.var(axis=1, ddof=1)
print("average of variance with /n    :", round(v_n.mean(), 3))
print("average of variance with /(n-1):", round(v_n1.mean(), 3))
print("true variance                  :", true_var)
```

**Reading this code line by line**

- `rng.normal(loc=10, scale=2, size=(100_000, 5))` draws a table of 100,000 rows and 5 columns from a normal (bell-shaped) distribution with mean 10 and standard deviation 2, so variance 4. Each row is one sample of size 5.
- `axis=1` tells NumPy to compute the variance across each row separately, giving 100,000 variances.

Dividing by $n$ gives 3.203 on average, about 20% too small (the expected value is $\frac{n-1}{n}\sigma^2 = 0.8 \times 4 = 3.2$). Dividing by $n-1$ gives 4.004, essentially the truth. For large samples the difference is negligible; with $n = 1{,}000$ the two divisors differ by 0.1%. For small samples it matters.

## 4. Robust measures: the median absolute deviation

The variance and standard deviation square the deviations, which makes them even more sensitive to outliers than the mean. A robust alternative is the **median absolute deviation from the median** (MAD):

$$\text{MAD} = \operatorname{median}\big(|x_1 - m|, |x_2 - m|, \dots, |x_n - m|\big)$$

where $m$ is the median. For our delivery times the median is 30.5 and the MAD is 4.0. Because the MAD is smaller than the standard deviation for bell-shaped data, it is often multiplied by the constant 1.4826; that scaled MAD estimates the same quantity as the standard deviation when the data are normal.

```python-run
import numpy as np
from scipy import stats
clean = np.array([22, 25, 27, 28, 30, 31, 33, 35, 38, 41])
dirty = clean.copy(); dirty[-1] = 410
for name, x in [("clean", clean), ("one typo", dirty)]:
    print(f"{name:9s} std={x.std(ddof=1):7.2f}  IQR={stats.iqr(x):5.2f}  "
          f"MAD={stats.median_abs_deviation(x):4.1f}  MAD*1.4826={stats.median_abs_deviation(x, scale='normal'):5.2f}")
```

**Reading this code line by line**

- `clean.copy()` makes an independent copy so that changing `dirty` does not change `clean`.
- `dirty[-1] = 410` replaces the last value (41) with a typo (410), as if someone pressed a key twice.
- `scale='normal'` multiplies the MAD by 1.4826 so it is comparable to a standard deviation.

One mistyped value pushes the standard deviation from 5.89 to 120.29, a twentyfold jump. The interquartile range (7.25), the MAD (4.0) and the scaled MAD (5.93) do not move at all. If an alerting system used the standard deviation to decide what is "unusual", this single typo would hide every real anomaly for as long as it stayed in the window.

## 5. Percentiles, quartiles and the interquartile range

Order statistics are measures based on sorted data. The **range**, the largest value minus the smallest, is the simplest, but it depends entirely on the two most extreme points, so it is very sensitive to outliers.

A **percentile** (also called a quantile) generalises the median. The $P$-th percentile is a value such that about $P$% of the data are at or below it. The median is the 50th percentile. The 25th and 75th percentiles are the first and third **quartiles**, $Q_1$ and $Q_3$. The **interquartile range** (IQR) is $Q_3 - Q_1$: the width of the middle half of the data. Being based on the middle 50%, it ignores the extreme quarter at each end, so it is robust.

For our delivery times, $Q_1 = 27.25$, $Q_3 = 34.5$, and the IQR is 7.25 minutes.

### How percentiles are computed between data points

With a finite sample, the exact percentile often falls between two sorted values, and different software uses different rules to pick a number. NumPy's default, also used by pandas, is **linear interpolation**: for $n$ sorted values $x_{(0)} \le \dots \le x_{(n-1)}$, compute the position $h = (n-1)\,p$ for the fraction $p$ (0.3 for the 30th percentile). If $h$ falls between positions $j$ and $j+1$, the percentile is

$$x_{(j)} + (h - j)\,\big(x_{(j+1)} - x_{(j)}\big)$$

i.e. move the fractional part of the way from one value to the next.

```python-run
import numpy as np
import pandas as pd
x = np.array([1, 2, 3, 4, 10])
for m in ["linear", "lower", "higher", "nearest", "midpoint"]:
    print(f"{m:8s} 30th percentile = {np.percentile(x, 30, method=m)}")
print("pandas quantile(0.3):", pd.Series(x).quantile(0.3))
```

**Reading this code line by line**

- `np.percentile(x, 30, method=m)` asks for the 30th percentile using rule `m`.
- For `linear`: $h = (5-1) \times 0.3 = 1.2$, so we go 0.2 of the way from $x_{(1)} = 2$ to $x_{(2)} = 3$: $2.2$.
- `lower` and `higher` take the sorted value immediately below or above position $h$; `nearest` rounds $h$; `midpoint` averages the two neighbours.

The rules give 2.2, 2, 3, 2 and 2.5. For large datasets these differences vanish; for small ones they can matter, and an interviewer who asks you to compute a percentile by hand usually expects the linear rule. Say which rule you are using.

> [!TIP]
> Product teams describe latency with percentiles, not means: "p50 is 120 ms, p95 is 480 ms, p99 is 1.9 s". The p99 is the 99th percentile, the time below which 99% of requests finish. A good mean can hide a terrible tail that every heavy user experiences daily.

## 6. Which measure should you use?

| Measure | Robust? | Units | Typical use |
|---|---|---|---|
| Range | No | original | quick sanity check for impossible values |
| Variance | No | squared | mathematics, adding independent sources of noise |
| Standard deviation | No | original | default spread for roughly symmetric data without outliers |
| Mean absolute deviation | Partly | original | easy-to-explain spread |
| MAD (median absolute deviation) | Yes | original | robust spread, anomaly detection |
| IQR | Yes | original | skewed data, boxplots, outlier rules |
| Percentiles | Yes | original | latency, income, service-level targets |

A common outlier rule, used by boxplots in the next lesson, flags values below $Q_1 - 1.5\,\text{IQR}$ or above $Q_3 + 1.5\,\text{IQR}$. For our clean delivery times that fence is $27.25 - 10.875 = 16.375$ to $34.5 + 10.875 = 45.375$, so nothing is flagged; the typo 410 would be.

A robust **z-score** (the number of standard deviations a value is from the centre, introduced fully in the lesson on the normal distribution) can be computed as $(x - \text{median}) / (1.4826 \times \text{MAD})$. It is a simple, sturdy anomaly detector: the typo gives $(410 - 30.5)/5.93 \approx 64$, unmistakably anomalous, while the ordinary z-score would be diluted by the typo's own effect on the standard deviation.

## Common mistakes

- Mixing up NumPy's `ddof=0` default with pandas' `ddof=1` default.
- Reporting a standard deviation for heavily skewed data such as income or latency, where percentiles say much more.
- Confusing the two "MADs": mean absolute deviation and median absolute deviation are different numbers.
- Comparing variances across metrics with different units; the coefficient of variation (standard deviation divided by mean) is a unit-free alternative when values are positive.
- Computing percentiles of percentiles (for example averaging per-server p99 latencies), which is not the p99 of all requests.

## Summary

- Variability measures how far values are from the centre; deviations average to zero, so we take absolute values or squares.
- Variance divides the sum of squared deviations by $n-1$ (degrees of freedom) to be unbiased; the standard deviation is its square root.
- Standard deviation and variance are sensitive to outliers; the MAD and the IQR are robust.
- Percentiles are order statistics; software interpolates between data points, NumPy and pandas linearly by default.
- Choose a measure that matches the data's shape and the business question; tails are usually reported as high percentiles.

## Glossary

- **Variability (dispersion, spread)**: how far values are from the centre.
- **Deviation (residual, error)**: a value minus an estimate of location.
- **Mean absolute deviation**: the average absolute deviation from the mean.
- **Variance ($s^2$)**: the sum of squared deviations from the mean divided by $n-1$.
- **Standard deviation ($s$)**: the square root of the variance.
- **Degrees of freedom**: the number of values free to vary once an estimate is fixed; $n-1$ for the sample variance.
- **Unbiased estimator**: an estimate that is correct on average over many samples.
- **ddof**: NumPy and pandas' "delta degrees of freedom" argument; the divisor is $n - \text{ddof}$.
- **MAD (median absolute deviation)**: the median of absolute deviations from the median.
- **Range**: largest value minus smallest.
- **Order statistics**: summaries based on sorted values.
- **Percentile (quantile)**: a value with a given share of data at or below it.
- **Quartiles ($Q_1$, $Q_3$)**: the 25th and 75th percentiles.
- **Interquartile range (IQR)**: $Q_3 - Q_1$.
- **Linear interpolation**: estimating a value between two known points proportionally.
- **p95 / p99**: the 95th / 99th percentile, common for latency.

## Check yourself

```quiz
[
  {"q": "Why does the sample variance divide by n − 1 rather than n?", "options": ["Deviations are measured from the sample mean, which makes them slightly too small; n − 1 corrects this so the estimate is unbiased", "To make the number larger so it looks more conservative", "Because one data point is always an outlier", "It is a historical accident with no effect"], "answer": 0,
   "explain": "One degree of freedom is used up estimating the mean. Dividing by n gives on average $(n-1)/n$ of the true variance."},
  {"q": "`np.std(x)` and `pd.Series(x).std()` give different answers. Why?", "options": ["NumPy divides by n by default (ddof=0); pandas divides by n − 1 (ddof=1)", "pandas drops outliers", "NumPy uses the median", "One of them has a bug"], "answer": 0,
   "explain": "The ddof defaults differ. Pass ddof explicitly to be safe."},
  {"q": "A data-entry error turns one value from 41 into 410. Which measure changes the most?", "options": ["Standard deviation", "Interquartile range", "Median absolute deviation", "Median"], "answer": 0,
   "explain": "Squaring makes the standard deviation very sensitive to one extreme value; the robust measures do not move."},
  {"q": "Using NumPy's default linear rule, what is the 30th percentile of [1, 2, 3, 4, 10]?", "options": ["2.2", "2", "2.5", "3"], "answer": 0,
   "explain": "Position $h = (5-1) \\times 0.3 = 1.2$: move 0.2 of the way from 2 to 3."},
  {"q": "The interquartile range is…", "options": ["the difference between the 75th and 25th percentiles", "the difference between maximum and minimum", "the average distance from the median", "the standard deviation divided by 4"], "answer": 0,
   "explain": "It is the width of the middle half of the data."},
  {"q": "With $Q_1 = 20$ and $Q_3 = 30$, the usual boxplot rule flags values above…", "options": ["45", "40", "35", "60"], "answer": 0,
   "explain": "IQR = 10, upper fence = $Q_3 + 1.5 \\times$ IQR = 30 + 15 = 45."},
  {"q": "You report service latency to engineers. The most informative summary is usually…", "options": ["several percentiles such as p50, p95 and p99", "the mean only", "the range", "the variance"], "answer": 0,
   "explain": "Latency is skewed with a long tail; high percentiles show what slow requests experience."}
]
```

> **Source:** Bruce & Bruce, *Practical Statistics for Data Scientists* (O'Reilly, 2017), ch. 1, "Estimates of Variability" (deviations, variance and standard deviation, degrees of freedom, median absolute deviation, percentiles and the interquartile range); NumPy documentation for `numpy.percentile` methods.
