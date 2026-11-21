# Binomial, Poisson and other common distributions

> **Before this lesson:** [Probability, conditional probability and Bayes' rule](#/lesson/statistics/probability-bayes) (independence, expected value, the binomial coefficient) and [Normal, t and long-tailed distributions](#/lesson/statistics/normal-t-long-tails) (CDF, survival function, `ppf`).

## In plain words

Many quantities in product analytics are counts or waiting times: how many of 10 visitors buy, how many support tickets arrive in an hour, how long until the next order, how many tries until the first success. A small family of distributions describes these situations so well that they have names: **binomial**, **Poisson**, **exponential**, **geometric** and **Weibull**. Knowing which one fits lets you answer "how unusual is this?" instantly and simulate realistic data.

An everyday picture: a call centre. Whether each caller buys is a coin-flip-like event (binomial). The number of calls in an hour is a count of random arrivals (Poisson). The minutes between calls are waiting times (exponential). The number of calls until the first sale is a "tries until success" count (geometric).

Why it matters for a job: conversion counts are binomial, event counts are Poisson, and A/B tests on both rest on these models. Interviewers ask questions like "a site gets 4 orders an hour on average; what is the chance of none in an hour?" or "expected number of rolls until a six?", and expect you to name the distribution and compute the answer.

## 1. Bernoulli trials and the binomial distribution

A **Bernoulli trial** is a single experiment with two outcomes, called success (1) and failure (0), where success has probability $p$. A visitor converting or not, an email being opened or not, a coin landing heads: all Bernoulli trials.

The **binomial distribution** counts the number of successes $X$ in $n$ independent Bernoulli trials with the same $p$. The chance of exactly $k$ successes is

$$P(X = k) = \binom{n}{k} p^k (1-p)^{n-k}$$

Why: any particular sequence with $k$ successes and $n-k$ failures has probability $p^k(1-p)^{n-k}$ (independence lets us multiply), and there are $\binom{n}{k}$ such sequences. The **probability mass function** (PMF) is the name for this list of probabilities for a discrete variable. Its mean and variance are

$$E[X] = np, \qquad \operatorname{Var}(X) = np(1-p)$$

```python-run
from scipy import stats
from math import comb
n, p = 10, 0.2
print("P(X = 2) by formula:", round(comb(n, 2) * p**2 * (1 - p)**8, 4))
print("P(X = 2) by scipy  :", round(stats.binom.pmf(2, n, p), 4))
print("P(X >= 5)          :", round(stats.binom.sf(4, n, p), 4))
print("mean", stats.binom.mean(n, p), " variance", round(stats.binom.var(n, p), 2))
for k in range(0, 7):
    print(k, "#" * int(stats.binom.pmf(k, n, p) * 100))
```

**Reading this code line by line**

- `comb(n, 2)` is $\binom{10}{2} = 45$, from Python's `math` module.
- `stats.binom.pmf(k, n, p)` gives $P(X = k)$.
- `stats.binom.sf(4, n, p)` is $P(X > 4) = P(X \ge 5)$. For discrete distributions, be careful: "at least 5" is the survival function at 4.
- The loop prints a text bar chart of the PMF, one `#` per percentage point.

With 10 visitors each converting at 20%, exactly 2 conversions has probability 0.302; 5 or more has only 0.0328. The mean is 2 and the variance 1.6. The bar chart is skewed right because $p$ is small.

### When the normal approximation works

By the central limit theorem, a binomial count is approximately normal with mean $np$ and standard deviation $\sqrt{np(1-p)}$ when $n$ is large. A common rule of thumb asks for both $np$ and $n(1-p)$ to be at least 10. Adding 0.5 to the cut-off (a **continuity correction**) helps because we approximate a staircase by a smooth curve.

```python-run
import numpy as np
from scipy import stats
for n, p in [(1000, 0.05), (40, 0.02)]:
    mu, sd = n * p, np.sqrt(n * p * (1 - p))
    k = int(mu + 2 * sd)
    exact = stats.binom.sf(k, n, p)
    approx = stats.norm.sf(k + 0.5, mu, sd)
    print(f"n={n}, p={p}: P(X > {k}) exact {exact:.4f}  normal approx {approx:.4f}")
```

**Reading this code line by line**

- For each case we pick a cut-off about two standard deviations above the mean and compare the exact binomial tail with the normal approximation.

With $n = 1000$ and $p = 0.05$ ($np = 50$) the approximation is decent (0.0251 versus 0.0284). With $n = 40$ and $p = 0.02$ ($np = 0.8$) it is poor (0.0274 versus 0.0457). For rare events in small samples, use exact binomial calculations; `scipy.stats.binomtest` gives an exact test.

## 2. The Poisson distribution

The **Poisson distribution** models the number of events in a fixed interval of time or space when events happen independently at a constant average rate $\lambda$ (lambda): tickets per hour, server errors per day, typos per page, clicks per minute.

$$P(X = k) = \frac{\lambda^k e^{-\lambda}}{k!}, \qquad E[X] = \operatorname{Var}(X) = \lambda$$

The Poisson is also the limit of the binomial when $n$ is large and $p$ small with $np = \lambda$ fixed: many opportunities, each very unlikely.

```python-run
import numpy as np
from scipy import stats
lam = 4
print("P(0 tickets in an hour):", round(stats.poisson.pmf(0, lam), 4))
print("P(8 or more)           :", round(stats.poisson.sf(7, lam), 4))
print("99th percentile        :", stats.poisson.ppf(0.99, lam))
rng = np.random.default_rng(9)
counts = rng.poisson(lam, 10_000)
print("simulated mean", counts.mean().round(3), " variance", counts.var().round(3))
```

**Reading this code line by line**

- `lam = 4` is the average number of tickets per hour.
- `pmf(0, lam)` is $e^{-4}$; `sf(7, lam)` is $P(X \ge 8)$; `ppf(0.99, lam)` is the smallest count with at least 99% of the probability at or below it.
- `rng.poisson(lam, 10_000)` simulates 10,000 hours.

An hour with no tickets has probability 0.0183. An hour with 8 or more has probability 0.0511, so seeing 8 is not alarming; a staffing plan for the 99th percentile should cover 9 tickets an hour. The simulated mean (3.984) and variance (3.99) are equal, the Poisson's signature.

> [!WARNING]
> Real counts are often **overdispersed**: the variance is larger than the mean, because the rate itself varies (busier days, a few very active users). A Poisson model then understates uncertainty, and tests based on it find too many "significant" changes. Check the variance-to-mean ratio; if it is well above 1, use a **negative binomial** model or resample by user.

## 3. The exponential distribution

If events follow a Poisson process with rate $\lambda$ per unit time, the waiting times between consecutive events follow the **exponential distribution** with mean $1/\lambda$:

$$P(T > t) = e^{-\lambda t}$$

It has a striking property called **memorylessness**: having already waited $s$ minutes does not change the distribution of the remaining wait. $P(T > s + t \mid T > s) = P(T > t)$.

```python-run
import numpy as np
from scipy import stats
rate = 4 / 60
wait = stats.expon(scale=1 / rate)
print("mean wait (minutes):", wait.mean())
print("P(wait > 30 min)   :", round(wait.sf(30), 4))
print("P(wait > 40 | waited 10 already):", round(wait.sf(40) / wait.sf(10), 4))
rng = np.random.default_rng(2)
gaps = rng.exponential(15, 200_000)
arrivals = np.cumsum(gaps)
per_hour = np.bincount((arrivals // 60).astype(int))[:-1]
print("arrivals per hour: mean", per_hour.mean().round(3), " variance", per_hour.var().round(3))
```

**Reading this code line by line**

- The rate is 4 tickets per 60 minutes. SciPy parameterises the exponential by `scale` $= 1/\lambda = 15$ minutes.
- The conditional probability uses the definition from the first lesson: $P(T > 40 \mid T > 10) = P(T > 40)/P(T > 10)$.
- The simulation draws 200,000 exponential gaps of mean 15 minutes; `np.cumsum` adds them up into arrival times; `arrivals // 60` is the hour each arrival falls in; `np.bincount` counts arrivals per hour. The last, incomplete hour is dropped with `[:-1]`.

The mean wait is 15 minutes; a gap of more than 30 minutes has probability 0.1353 ($e^{-2}$). Having waited 10 minutes, the chance of waiting 30 more is again 0.1353: memorylessness. And counting the simulated exponential arrivals per hour gives mean 3.999 and variance 3.993: Poisson counts. The two distributions are two views of the same random process.

## 4. The geometric distribution

The **geometric distribution** counts the number of independent trials up to and including the first success, with success probability $p$ each time:

$$P(X = k) = (1-p)^{k-1}p, \qquad E[X] = \frac{1}{p}$$

It is the discrete cousin of the exponential and is also memoryless.

## 5. The Weibull distribution

The exponential assumes a constant event rate. Machines, subscriptions and customers often have a rate that changes over time: parts wear out (rate rises), and new subscribers are most likely to cancel early (rate falls). The **Weibull distribution** generalises the exponential with a **shape** parameter $\beta$ and a **scale** parameter $\eta$ (eta, also called the characteristic life). If $\beta > 1$ the failure rate rises over time; if $\beta < 1$ it falls; $\beta = 1$ gives the exponential. The instantaneous failure rate at time $t$, given survival to $t$, is called the **hazard rate**.

```python-run
import numpy as np
from scipy import stats
p = 1 / 6
print("P(first six on roll 3):", round(stats.geom.pmf(3, p), 4), " expected rolls:", stats.geom.mean(p))
life = stats.weibull_min(c=1.5, scale=5000)
print("Weibull shape 1.5: mean life", round(life.mean()), "hours; P(fail before 2000 h)", round(life.cdf(2000), 4))
for t in [1000, 5000, 10000]:
    hazard = life.pdf(t) / life.sf(t)
    print(f"failure rate at {t:>5} h: {hazard * 1000:.3f} per 1,000 hours")
```

**Reading this code line by line**

- `stats.geom.pmf(3, p)` is the probability that the first six comes on the third roll: $(5/6)^2 \times 1/6$.
- `stats.weibull_min(c=1.5, scale=5000)` is a Weibull with shape 1.5 and scale 5,000 hours (SciPy calls the shape `c`).
- The hazard rate is density divided by survival: the chance of failing right now among those still working.

The first six arrives on roll 3 with probability 0.1157, and on average it takes 6 rolls. The parts have a mean life of 4,514 hours, 22.35% fail before 2,000 hours, and the failure rate climbs from 0.134 to 0.424 per 1,000 hours as they age: wear-out. Fitting a Weibull to observed lifetimes (`stats.weibull_min.fit`) estimates both parameters; survival analysis extends this to customers who have not churned yet.

## 6. A field guide

| Situation | Distribution | Parameters | Mean | Variance |
|---|---|---|---|---|
| One yes/no trial | Bernoulli | $p$ | $p$ | $p(1-p)$ |
| Successes in $n$ trials | Binomial | $n, p$ | $np$ | $np(1-p)$ |
| Events in a fixed interval | Poisson | $\lambda$ | $\lambda$ | $\lambda$ |
| Time between events | Exponential | $\lambda$ | $1/\lambda$ | $1/\lambda^2$ |
| Trials until first success | Geometric | $p$ | $1/p$ | $(1-p)/p^2$ |
| Lifetimes with changing rate | Weibull | $\beta, \eta$ | depends on both | depends on both |

> [!INTERVIEW]
> Typical prompt: "We get on average 2 fraud cases a day. Yesterday we had 7. Is that unusual?" Answer: model daily counts as Poisson with $\lambda = 2$; $P(X \ge 7) \approx 0.0045$, so yes, roughly a 1-in-220-day event, worth investigating. Then add the caveats: is the rate really constant (weekday effects, growth), and are cases independent (one fraudster can create several)?

## Common mistakes

- Using the binomial when trials are not independent or $p$ varies across users.
- Off-by-one errors with discrete tails: $P(X \ge k)$ is `sf(k - 1)`.
- Applying the normal approximation to rare events in small samples.
- Assuming Poisson counts when data are overdispersed.
- Forgetting SciPy's parameterisations: exponential uses `scale` $= 1/\lambda$; Weibull's shape is `c`.

## Summary

- Binomial: successes in $n$ independent trials; mean $np$, variance $np(1-p)$; approximately normal when $np$ and $n(1-p)$ are both large.
- Poisson: counts of independent events at rate $\lambda$; mean = variance = $\lambda$; check for overdispersion.
- Exponential: waiting times in a Poisson process; memoryless; mean $1/\lambda$.
- Geometric: trials until the first success; mean $1/p$.
- Weibull: lifetimes whose failure rate rises ($\beta > 1$) or falls ($\beta < 1$).

## Glossary

- **Bernoulli trial**: one experiment with two outcomes.
- **Binomial distribution**: the number of successes in $n$ independent Bernoulli trials.
- **Probability mass function (PMF)**: the probabilities of each value of a discrete variable.
- **Continuity correction**: adding or subtracting 0.5 when approximating a discrete distribution by a continuous one.
- **Poisson distribution**: the number of events in an interval at a constant rate $\lambda$.
- **Overdispersion**: count variance larger than the Poisson model allows.
- **Negative binomial**: a count distribution that allows overdispersion.
- **Exponential distribution**: waiting times between Poisson events.
- **Memorylessness**: the remaining wait does not depend on time already waited.
- **Geometric distribution**: number of trials until the first success.
- **Weibull distribution**: a lifetime distribution with shape and scale parameters.
- **Hazard rate**: the instantaneous event rate among units that have survived so far.

## Check yourself

```quiz
[
  {"q": "10 visitors each convert independently with probability 0.2. The expected number of conversions and its variance are…", "options": ["2 and 1.6", "2 and 2", "0.2 and 0.16", "10 and 2"], "answer": 0,
   "explain": "$np = 2$, $np(1-p) = 10 \\times 0.2 \\times 0.8 = 1.6$."},
  {"q": "Orders arrive at 4 per hour on average (Poisson). The probability of no orders in an hour is…", "options": ["$e^{-4} \\approx 0.018$", "0.25", "0", "$4e^{-4}$"], "answer": 0,
   "explain": "$P(X = 0) = \\lambda^0 e^{-\\lambda}/0! = e^{-4}$."},
  {"q": "In scipy, P(X ≥ 5) for a binomial X is…", "options": ["`binom.sf(4, n, p)`", "`binom.sf(5, n, p)`", "`binom.cdf(5, n, p)`", "`binom.pmf(5, n, p)`"], "answer": 0,
   "explain": "`sf(k)` is $P(X > k)$, so $P(X \\ge 5) = P(X > 4)$."},
  {"q": "Your daily signup counts have mean 50 and variance 400. A Poisson model would…", "options": ["understate the variability; the data are overdispersed", "fit perfectly", "overstate the variability", "be required by the CLT"], "answer": 0,
   "explain": "Poisson forces variance = mean = 50; the real variance is 8 times larger."},
  {"q": "Waiting times are exponential with mean 15 minutes. You have waited 10 minutes. The expected remaining wait is…", "options": ["15 minutes", "5 minutes", "25 minutes", "0 minutes"], "answer": 0,
   "explain": "Memorylessness: the past wait does not change the distribution of the remaining time."},
  {"q": "A Weibull lifetime model with shape β = 0.7 describes…", "options": ["a failure rate that falls over time, as with early cancellations", "a constant failure rate", "a rising failure rate due to wear", "a normal distribution"], "answer": 0,
   "explain": "$\\beta < 1$ means the hazard decreases with age; $\\beta = 1$ is exponential; $\\beta > 1$ rises."},
  {"q": "Expected number of rolls of a fair die until the first six?", "options": ["6", "3.5", "1/6", "36"], "answer": 0,
   "explain": "Geometric distribution: $E[X] = 1/p = 6$."}
]
```

> **Source:** Bruce & Bruce, *Practical Statistics for Data Scientists* (O'Reilly, 2017), ch. 2, "Binomial Distribution" and "Poisson and Related Distributions" (Poisson, exponential, estimating the failure rate, Weibull); SciPy documentation for `scipy.stats` discrete and continuous distributions.
