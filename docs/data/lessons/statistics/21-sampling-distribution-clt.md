# Sampling distributions, standard error and the central limit theorem

> **Before this lesson:** [Random sampling and the many faces of bias](#/lesson/statistics/sampling-bias) (population, sample, random error versus bias) and [Estimates of variability](#/lesson/statistics/variability) (standard deviation). The fact that an average of $n$ independent draws has standard deviation $\sigma/\sqrt{n}$ was stated in [Probability, conditional probability and Bayes' rule](#/lesson/statistics/probability-bayes); here you will see it happen.

## In plain words

Draw a sample, compute its mean. Draw another sample from the same population: you get a slightly different mean. If you could repeat this thousands of times, the means would form their own distribution, called the **sampling distribution** of the mean. Its spread, the **standard error**, tells you how far a single sample's estimate is likely to be from the truth. The **central limit theorem** says that this distribution is close to a bell curve for large samples, even when the data themselves are not bell-shaped.

An everyday picture: ask one random person how many hours they slept last night and you might hear 3 or 11. Ask a random group of 100 and average their answers, and the average will almost certainly be within a few minutes of the population's typical value. Averages are much more stable than individuals, and this lesson tells you exactly how much more.

Why it matters for a job: the standard error is the engine of every confidence interval, every A/B test and every sample-size calculation. In interviews, "explain the central limit theorem" and "why does the standard error shrink with $\sqrt{n}$?" are among the most frequently asked statistics questions. You will be able to answer with a simulation, not only a formula.

## 1. Data distribution versus sampling distribution

Keep two distributions apart:

- The **data distribution** is the distribution of individual values in a sample or population: how individual order amounts are spread.
- The **sampling distribution** of a statistic is the distribution of that statistic (a mean, a median, a proportion) over many samples of the same size from the same population.

A **statistic** (or sample statistic) is any number computed from a sample. Every statistic has a sampling distribution, and its shape and spread depend on the statistic, the population and the sample size $n$.

## 2. Watching a sampling distribution form

Let us take a strongly skewed population: one million waiting times drawn from an **exponential distribution** (common for waiting times; most are short, a few are very long) with mean 40 seconds. For several sample sizes we draw 20,000 samples, compute each sample's mean and examine the resulting collection of means.

```python-run
import numpy as np
from scipy import stats
rng = np.random.default_rng(10)
population = rng.exponential(scale=40, size=1_000_000)
mu, sigma = population.mean(), population.std()
print(f"population: mean {mu:.2f}, SD {sigma:.2f}, skewness {stats.skew(population):.2f}")
for n in [1, 5, 30, 200]:
    means = rng.choice(population, size=(20_000, n)).mean(axis=1)
    print(f"n={n:>3}: mean of sample means {means.mean():6.2f}  SD of sample means {means.std():6.2f}"
          f"  sigma/sqrt(n) {sigma/np.sqrt(n):6.2f}  skewness {stats.skew(means):5.2f}")
```

**Reading this code line by line**

- `rng.exponential(scale=40, size=1_000_000)` creates the population; for this distribution the mean and the standard deviation both equal the scale, 40.
- `rng.choice(population, size=(20_000, n))` draws a table with 20,000 rows, each row a random sample of size `n` (with replacement, which is negligible with a million-strong population).
- `.mean(axis=1)` averages each row, producing 20,000 sample means: a simulated sampling distribution.
- For each `n` we print the centre, the spread, the theoretical spread $\sigma/\sqrt{n}$ and the skewness of the sample means.

Three things happen as $n$ grows:

1. **The centre stays at the population mean.** The mean of sample means is about 40 for every $n$: the sample mean is unbiased.
2. **The spread shrinks like $\sigma/\sqrt{n}$.** The simulated standard deviations 39.81, 17.87, 7.34 and 2.82 match the formula's 40.01, 17.89, 7.31 and 2.83 almost exactly.
3. **The shape becomes symmetric.** Skewness falls from 2.03 (the raw data) to 0.90, 0.36 and 0.15: the sampling distribution approaches a bell shape even though the data are very lopsided.

Here is the shape change as a text histogram, using the same bins for both sample sizes.

```python-run
import numpy as np
rng = np.random.default_rng(10)
population = rng.exponential(scale=40, size=1_000_000)
edges = np.arange(0, 131, 10)
for n in [2, 30]:
    means = rng.choice(population, size=(20_000, n)).mean(axis=1)
    counts, _ = np.histogram(means, bins=edges)
    print(f"--- sample means, n = {n} ---")
    for c, lo in zip(counts, edges):
        print(f"{lo:4d}-{lo + 10:<4d}| " + "#" * int(c / 200))
```

**Reading this code line by line**

- `np.arange(0, 131, 10)` gives bin edges 0, 10, ..., 130.
- `np.histogram(means, bins=edges)` counts how many sample means fall in each bin and returns the counts and the edges; `_` is a conventional name for a value we do not need.
- Each `#` stands for 200 sample means.

With $n = 2$ the means pile up on the left with a long right tail, still looking like the skewed data. With $n = 30$ they form a narrow, nearly symmetric hump around 40.

## 3. The central limit theorem

The **central limit theorem** (CLT) states: if you take random samples of size $n$ from a population with mean $\mu$ and finite standard deviation $\sigma$, then for large $n$ the sampling distribution of the sample mean is approximately **normal** (the bell curve) with mean $\mu$ and standard deviation $\sigma/\sqrt{n}$:

$$\bar{X} \approx \mathcal{N}\!\left(\mu,\ \frac{\sigma^2}{n}\right)$$

The notation $\mathcal{N}(\mu, \sigma^2)$ means "normal distribution with mean $\mu$ and variance $\sigma^2$". The CLT also applies to sums and to proportions, since a proportion is the mean of 0/1 values.

Why it is so important: it lets us use normal-distribution formulas (for confidence intervals and tests) for the mean of almost any kind of data, as long as the sample is large enough. That is why t-tests and z-tests work on revenue, durations and conversion rates, none of which are normal themselves.

How large is "large enough"? There is no single number. Rules of thumb say 30, but it depends on skewness: for nearly symmetric data 10 or 20 is plenty; for heavily skewed data such as revenue per user, where a few customers spend thousands of times the median, you may need thousands. When in doubt, simulate or bootstrap (next lesson).

> [!INTERVIEW]
> A crisp answer to "What is the central limit theorem?": "The mean of a large random sample is approximately normally distributed around the population mean, with standard deviation sigma over root n, whatever the shape of the data, provided the variance is finite. It is why we can build confidence intervals and run z- or t-tests on means and proportions of non-normal metrics." Then mention the caveats in section 6.

## 4. The standard error

The standard deviation of a statistic's sampling distribution is called its **standard error** (SE). For the sample mean:

$$SE(\bar{x}) = \frac{\sigma}{\sqrt{n}} \approx \frac{s}{\sqrt{n}}$$

We do not know $\sigma$, so we plug in the sample standard deviation $s$. Do not confuse the two: the standard deviation describes the spread of *individual values*; the standard error describes the spread of an *estimate*.

The **square-root law** has a practical sting. To halve the standard error you need four times as much data; to cut it by ten you need a hundred times as much. This is why experiments on small effects need huge samples.

For a proportion $\hat{p}$ (read "p hat", the observed share), the 0/1 values have standard deviation $\sqrt{p(1-p)}$, so

$$SE(\hat{p}) = \sqrt{\frac{p(1-p)}{n}}$$

```python-run
import numpy as np
rng = np.random.default_rng(4)
sample = rng.exponential(scale=40, size=50)
se = sample.std(ddof=1) / np.sqrt(len(sample))
print(f"one sample of 50: mean {sample.mean():.2f}, SD {sample.std(ddof=1):.2f}, SE {se:.2f}")
p, n = 0.05, 10_000
props = rng.binomial(n, p, size=20_000) / n
print(f"conversion 5%, n=10,000: SD of sample proportions {props.std():.5f}, formula {np.sqrt(p*(1-p)/n):.5f}")
```

**Reading this code line by line**

- The first part takes one realistic sample of 50 waiting times and estimates the standard error from that single sample, as you would in practice.
- `rng.binomial(n, p, size=20_000)` simulates 20,000 experiments, each counting conversions among 10,000 users with a true rate of 5%; dividing by `n` gives sample proportions.

The single sample has mean 48.39 and standard error 7.41, so a mean of 48 is entirely compatible with the true 40: about one standard error away. For proportions, the simulated spread (0.00219) matches the formula (0.00218). With 10,000 users and a 5% conversion rate, the observed rate typically wobbles by about ±0.2 percentage points by chance alone, a fact that matters greatly when interpreting A/B tests.

### The standard error of a difference

A/B tests compare two groups, so the quantity of interest is a difference of two estimates, $\bar{x}_B - \bar{x}_A$. If the groups are independent, variances add (the rule from the probability lesson), so

$$SE(\bar{x}_B - \bar{x}_A) = \sqrt{\frac{s_A^2}{n_A} + \frac{s_B^2}{n_B}}, \qquad SE(\hat{p}_B - \hat{p}_A) = \sqrt{\frac{p_A(1-p_A)}{n_A} + \frac{p_B(1-p_B)}{n_B}}$$

Note that the standard error of the difference is *larger* than either group's own standard error: two sources of noise combine. With two groups of 10,000 users each converting at about 5%, the difference has a standard error of $\sqrt{2} \times 0.00218 \approx 0.0031$, about 0.3 percentage points. An observed lift of 0.2 points is therefore well within the range of chance. This single calculation is the core of the two-proportion z-test in [t-tests, z-tests and degrees of freedom](#/lesson/statistics/t-tests).

## 5. Other statistics have sampling distributions too

The median, a percentile, a correlation and a regression slope all have sampling distributions and standard errors. For many of them there is no neat formula, and for some (like the median of skewed data) the normal approximation is poor in small samples. The general-purpose tool for these cases is the **bootstrap**, which estimates a sampling distribution by resampling the one sample you have. It is the subject of [The bootstrap](#/lesson/statistics/bootstrap).

## 6. When the CLT lets you down

The theorem has conditions, and real data sometimes break them.

- **Infinite variance.** Some heavy-tailed distributions have no finite standard deviation. The extreme example is the **Cauchy distribution**: the mean of $n$ Cauchy values has the *same* distribution as a single value, so averaging does not help at all.

```python-run
import numpy as np
rng = np.random.default_rng(6)
for n in [10, 1_000, 100_000]:
    print(f"n={n:>7}: five sample means of a Cauchy variable:",
          np.round([rng.standard_cauchy(n).mean() for _ in range(5)], 2))
```

**Reading this code line by line**

- `rng.standard_cauchy(n)` draws `n` values from the Cauchy distribution; we compute five sample means for each `n`.

Even with 100,000 values the five means range from $-3.52$ to $-0.14$: no settling down. Real metrics are rarely this extreme, but revenue with a few enormous enterprise deals can behave badly in moderate samples. Capping (winsorising) or analysing the log can help.

- **Dependence.** The CLT assumes independent observations. Page views from the same user, or daily values in a time series, are correlated; the effective sample size is smaller than the row count, and naive standard errors are too small. This is why A/B tests randomise and analyse at the user level, not the page-view level.
- **Small samples from skewed data.** The approximation may still be poor; use the bootstrap or a larger sample.

## Common mistakes

- Confusing standard deviation (spread of data) with standard error (spread of an estimate).
- Thinking the CLT makes the *data* normal. It is the sampling distribution of the mean that becomes normal.
- Treating page views or sessions as independent when they come from the same users.
- Expecting $n = 30$ to be enough for very skewed metrics like revenue.

## Summary

- A sampling distribution is the distribution of a statistic over repeated samples; its standard deviation is the standard error.
- The sample mean is unbiased and its standard error is $\sigma/\sqrt{n}$; to halve it, quadruple the sample.
- For proportions, $SE = \sqrt{p(1-p)/n}$.
- The central limit theorem: for large $n$, the sample mean is approximately normal around $\mu$, whatever the data's shape, if the variance is finite and observations are independent.
- Heavy tails, dependence and small samples weaken the approximation; the bootstrap is the general fallback.

## Glossary

- **Statistic (sample statistic)**: a number computed from a sample.
- **Data distribution**: the distribution of individual values.
- **Sampling distribution**: the distribution of a statistic over many samples of the same size.
- **Standard error (SE)**: the standard deviation of a sampling distribution.
- **Square-root law**: standard error falls in proportion to $1/\sqrt{n}$.
- **Exponential distribution**: a right-skewed distribution often used for waiting times.
- **Normal distribution $\mathcal{N}(\mu, \sigma^2)$**: the symmetric bell curve with mean $\mu$ and variance $\sigma^2$.
- **Central limit theorem (CLT)**: sample means are approximately normal for large samples.
- **$\hat{p}$ ("p hat")**: an observed proportion.
- **Cauchy distribution**: a heavy-tailed distribution with no finite mean or variance.
- **Effective sample size**: the number of independent observations the data are worth.

## Check yourself

```quiz
[
  {"q": "The central limit theorem says that, for large n, which quantity is approximately normal?", "options": ["The sample mean", "Each individual data value", "The sample standard deviation always", "The population"], "answer": 0,
   "explain": "The data keep their shape; the distribution of the sample mean across samples becomes bell-shaped."},
  {"q": "Individual order values have standard deviation 40. The standard error of the mean of 400 orders is…", "options": ["2", "40", "0.1", "20"], "answer": 0,
   "explain": "$40/\\sqrt{400} = 40/20 = 2$."},
  {"q": "To cut the standard error of an estimate in half you need roughly…", "options": ["four times as many observations", "twice as many observations", "half as many observations", "ten times as many observations"], "answer": 0,
   "explain": "SE is proportional to $1/\\sqrt{n}$, so halving it needs $n$ to grow by a factor of 4."},
  {"q": "A conversion rate is about 5% and n = 10,000. The standard error of the observed rate is about…", "options": ["0.22 percentage points", "5 percentage points", "0.05 percentage points", "2.2 percentage points"], "answer": 0,
   "explain": "$\\sqrt{0.05 \\times 0.95/10000} \\approx 0.00218$."},
  {"q": "Which situation most threatens CLT-based standard errors in an A/B test?", "options": ["Analysing page views as if independent when many come from the same user", "Having 1 million users", "Using a 0/1 metric", "Metric values that are positive"], "answer": 0,
   "explain": "Correlated observations shrink the effective sample size, so naive standard errors are too small."},
  {"q": "What is the difference between standard deviation and standard error?", "options": ["SD measures spread of individual values; SE measures spread of an estimate across samples", "They are the same thing", "SE is always larger than SD", "SD applies only to proportions"], "answer": 0,
   "explain": "SE = SD divided by $\\sqrt{n}$ for the mean."}
]
```

> **Source:** Bruce & Bruce, *Practical Statistics for Data Scientists* (O'Reilly, 2017), ch. 2, "Sampling Distribution of a Statistic" (central limit theorem, standard error); the simulations, including the Cauchy counter-example, are original.
