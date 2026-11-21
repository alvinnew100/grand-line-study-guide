# Statistical significance, p-values and their misconceptions

> **Before this lesson:** [A/B tests, hypotheses and permutation tests](#/lesson/statistics/ab-tests-permutation), which introduced the null hypothesis and computed a first p-value by shuffling. Bayes' rule from [Probability, conditional probability and Bayes' rule](#/lesson/statistics/probability-bayes) explains the most important misconception below.

## In plain words

A result is called **statistically significant** when it would be surprising if only chance were at work. The **p-value** is the number that measures that surprise. It is the most used and most misunderstood number in data science. This lesson defines it carefully, shows by simulation how it behaves when there is and is not a real effect, introduces the two kinds of error a test can make, and lists the misconceptions that interviewers love to probe.

An everyday picture: a smoke alarm. The null hypothesis is "no fire". A low p-value is the alarm sounding loudly: the evidence is hard to explain without a fire. But alarms also go off for burnt toast (false alarms), and a quiet alarm does not prove there is no fire (it might be in another room). The p-value is a signal about evidence, not a verdict.

Why it matters for a job: decisions worth millions are taken on "p < 0.05". Misreading p-values leads to shipping features that do nothing, killing ones that work, and trusting results that will not replicate. Interview questions such as "what is a p-value?", "is p = 0.03 a 97% chance the feature works?" and "the test is significant but the lift is 0.1%; ship?" are routine.

## 1. Definition

Imagine a world where the null hypothesis holds and only randomness operates. The **p-value** is how often, in that world, you would see a result at least as extreme as the one you actually got.

$$p = P(\text{test statistic at least as extreme as observed} \mid H_0 \text{ true})$$

"At least as extreme" means in the direction(s) of the alternative: one tail for a one-sided test, both tails for a two-sided test. In the permutation test the p-value was the share of shuffles at least as extreme as the real data; formula-based tests compute the same tail area from a theoretical distribution such as the normal or t.

## 2. Alpha and the decision rule

Before running the test we choose a **significance level** $\alpha$ (alpha), the threshold of surprise: commonly 0.05, sometimes 0.01 or 0.10. The rule is:

- If $p \le \alpha$: reject $H_0$; the result is "statistically significant at level $\alpha$".
- If $p > \alpha$: fail to reject $H_0$.

The 5% convention goes back to R. A. Fisher in the 1920s, who suggested it as a rough guide for when a result deserves a second look, not as a law of nature. There is nothing magical about 0.05: $p = 0.049$ and $p = 0.051$ are practically identical evidence.

## 3. How p-values behave when nothing is going on

A powerful way to understand p-values is to simulate many experiments where the null is true by construction. These are **A/A tests**: both groups get the same experience. Companies run them for real to check that their experimentation system works.

```python-run
import numpy as np
from scipy import stats
rng = np.random.default_rng(31)
a = rng.normal(100, 20, size=(10_000, 50))
b = rng.normal(100, 20, size=(10_000, 50))
p = stats.ttest_ind(a, b, axis=1).pvalue
print("share of A/A tests with p < 0.05:", round(np.mean(p < 0.05), 4))
counts, _ = np.histogram(p, bins=np.linspace(0, 1, 11))
print("p-values per tenth of [0, 1]:", counts)
```

**Reading this code line by line**

- `a` and `b` each hold 10,000 rows of 50 values from the *same* normal distribution, so every row-pair is an A/A test.
- `stats.ttest_ind(a, b, axis=1)` runs a two-sample t-test (explained in the next lesson) on each row-pair at once; `.pvalue` holds the 10,000 p-values.
- `np.linspace(0, 1, 11)` makes 11 equally spaced edges, so the histogram counts p-values in each tenth of the interval.

4.83% of the A/A tests are "significant" at 0.05, as designed: when the null is true, a test at level $\alpha$ raises a false alarm a fraction $\alpha$ of the time. And the p-values are spread evenly across 0 to 1 (about 1,000 in each tenth). Under the null hypothesis, p-values are **uniformly distributed**. A p-value of 0.03 is exactly as likely as 0.53 when nothing is going on.

> [!TIP]
> If your company's A/A tests produce p-values that pile up near 0, the experimentation pipeline is broken (wrong randomisation unit, bad variance formula, or a bug). This is one of the cheapest and most valuable checks you can run.

## 4. Type I and type II errors

A test can be wrong in two ways:

| | $H_0$ true (no effect) | $H_0$ false (real effect) |
|---|---|---|
| Reject $H_0$ | **Type I error** (false positive), probability $\alpha$ | Correct: detection, probability = power |
| Fail to reject $H_0$ | Correct | **Type II error** (false negative), probability $\beta$ |

- A **type I error** is concluding there is an effect when there is none. Its rate is controlled by $\alpha$.
- A **type II error** is missing a real effect. Its rate is called $\beta$ (beta).
- **Power** $= 1 - \beta$ is the probability of detecting an effect of a given size. It depends on the effect size, the sample size, the noise and $\alpha$.

```python-run
import numpy as np
from scipy import stats
rng = np.random.default_rng(32)
tests, n = 10_000, 2_000
a = rng.binomial(n, 0.10, tests) / n
b = rng.binomial(n, 0.12, tests) / n
pool = (a + b) / 2
z = (b - a) / np.sqrt(pool * (1 - pool) * 2 / n)
p = 2 * stats.norm.sf(np.abs(z))
print("true lift 10% -> 12%, n = 2,000 per arm")
print("share of tests with p < 0.05 (power):", round(np.mean(p < 0.05), 3))
print("share of tests with p > 0.5         :", round(np.mean(p > 0.5), 3))
```

**Reading this code line by line**

- Each of 10,000 simulated experiments has 2,000 users per arm, with true conversion rates 10% (A) and 12% (B): a real 20% relative lift.
- `rng.binomial(n, rate, tests) / n` simulates each experiment's observed conversion rate.
- `z` is the two-proportion z statistic and `p` its two-sided p-value (formula details in the next lesson).

Even though the effect is real, only 52.9% of experiments reach $p < 0.05$: the power is about 53%, and nearly half of these well-intentioned tests would wrongly conclude "no significant effect". In 8.3% of them the p-value is even above 0.5. A non-significant result in an underpowered test tells you very little. Planning sample size to reach adequate power (usually 80%) is the subject of [Power and sample size](#/lesson/statistics/power-sample-size).

## 5. The big misconception: p is not the probability the null is true

The p-value is $P(\text{data this extreme} \mid H_0)$. People want $P(H_0 \mid \text{data})$, "the chance the feature does nothing". These are different, in the same way that $P(\text{positive test} \mid \text{healthy})$ differs from $P(\text{healthy} \mid \text{positive test})$ in the medical-test example. Converting one into the other needs a prior: how likely was the idea to work before testing?

Suppose a company tests many ideas, and, realistically, only 10% of them have a real effect. Tests use $\alpha = 0.05$ and have 80% power.

```python-run
import numpy as np
rng = np.random.default_rng(33)
ideas = 100_000
works = rng.random(ideas) < 0.10
alpha, power = 0.05, 0.80
significant = np.where(works, rng.random(ideas) < power, rng.random(ideas) < alpha)
false_wins = np.sum(significant & ~works)
print("significant results:", significant.sum())
print("of which the idea did nothing:", false_wins)
print("share of 'wins' that are false:", round(false_wins / significant.sum(), 3))
```

**Reading this code line by line**

- `works` marks the 10% of 100,000 ideas that truly have an effect.
- For ideas that work, a test is significant with probability 0.8 (the power); for ideas that do nothing, with probability 0.05 (the false-positive rate). `np.where` picks the right probability for each idea.
- `~works` flips true and false, selecting the ideas that do nothing.

Of 12,466 significant results, 4,522 come from ideas that did nothing: **36.3% of "wins" are false**, even though every individual test used $\alpha = 0.05$. By hand: true wins $0.10 \times 0.8 = 0.08$, false wins $0.90 \times 0.05 = 0.045$, and $0.045/0.125 = 0.36$. The share of significant results that are false is called the **false discovery rate**, and it depends heavily on the prior success rate and on power. With low power and long-shot ideas, most "discoveries" can be false. This is a central reason for the **replication crisis** in science, where many published significant findings failed to reproduce.

## 6. Significant is not the same as important

The p-value mixes two things: the size of the effect and the amount of data. With enough data, trivially small effects become highly significant; with little data, large effects can be non-significant.

```python-run
import numpy as np
from scipy import stats
for n, pa, pb in [(10_000_000, 0.1000, 0.1010), (400, 0.10, 0.15)]:
    se = np.sqrt(pa * (1 - pa) / n + pb * (1 - pb) / n)
    z = (pb - pa) / se
    p = 2 * stats.norm.sf(abs(z))
    print(f"n={n:>10,} per arm: lift {pb - pa:+.4f}, z = {z:5.2f}, p = {p:.3g}, "
          f"95% CI ({pb - pa - 1.96 * se:+.4f}, {pb - pa + 1.96 * se:+.4f})")
```

**Reading this code line by line**

- Two scenarios: a huge test (10 million users per arm) with a lift of 0.1 percentage point, and a small test (400 per arm) with a lift of 5 points.
- For each we compute the standard error of the difference, the z statistic, the two-sided p-value and a 95% confidence interval. `:.3g` prints three significant digits.

The tiny lift gets $p = 1.03 \times 10^{-13}$, overwhelmingly significant, yet a 0.1-point change in conversion may not be worth the engineering and maintenance cost. The large lift gets $p = 0.032$, barely significant, with an interval from 0.4 to 9.6 points: very uncertain about size. This is why you should always report the **effect size** (how big the difference is, in units people care about) and a confidence interval alongside the p-value. **Practical significance** (is the effect big enough to matter?) is a business judgement; statistical significance cannot answer it.

## 7. The ASA statement

In 2016 the American Statistical Association published an unusual statement on p-values because misuse had become so widespread. Its six principles, in paraphrase:

1. A p-value tells you how poorly the data fit one particular statistical model (usually the null).
2. P-values do not measure the probability that the hypothesis is true, or that the data were produced by chance alone.
3. Decisions, scientific or commercial, should never hinge on a single cut-off such as 0.05.
4. Honest inference means disclosing everything: every test you ran, not merely the winners.
5. A p-value says nothing about how large an effect is or whether it matters.
6. By itself, a p-value is not a good measure of evidence for a model or hypothesis.

## 8. Misconceptions to avoid (interview checklist)

> [!INTERVIEW]
> Each of these statements is **false**:
> - "p = 0.03 means there is a 3% chance the null hypothesis is true."
> - "p = 0.03 means there is a 97% chance the feature works."
> - "p = 0.03 means the result has a 97% chance of replicating."
> - "p > 0.05 proves there is no effect."
> - "A smaller p-value means a bigger effect."
> - "If p < 0.05, the result is important."
>
> A correct one-liner: "Assuming the change did nothing, there is a 3% chance of seeing a difference at least this large."

Other practical traps:

- **p-hacking**: trying many metrics, segments, time windows or analysis choices until something crosses 0.05. Each try is another chance for a false positive (see [Multiple testing](#/lesson/statistics/multiple-testing)).
- **Peeking**: checking the p-value every day and stopping when it dips below 0.05 inflates the false-positive rate far above 5% (see [A/B testing pitfalls](#/lesson/statistics/ab-pitfalls)).
- **Data science context**: in exploratory work and model building, p-values are less central than in published science; a model is judged by out-of-sample performance. But for go/no-go product decisions from experiments, they remain a key input.

## Summary

- The p-value is the probability, assuming the null is true, of a result at least as extreme as observed.
- Reject the null when $p \le \alpha$; $\alpha$ is the type I (false positive) rate. Under the null, p-values are uniform.
- Type II errors miss real effects; power $= 1-\beta$ depends on effect size, sample size, noise and $\alpha$.
- The p-value is not the probability that the null is true; with low prior success rates, many significant results are false.
- Statistical significance is not practical significance; always report effect sizes and confidence intervals.

## Glossary

- **Statistically significant**: a result unlikely under the null hypothesis, at a chosen level.
- **p-value**: $P(\text{result at least as extreme} \mid H_0)$.
- **Significance level ($\alpha$)**: the p-value threshold, and the type I error rate.
- **A/A test**: an experiment where both groups get the same experience.
- **Uniform distribution**: every value in an interval equally likely.
- **Type I error (false positive)**: rejecting a true null.
- **Type II error (false negative)**: failing to reject a false null.
- **$\beta$ / power**: the type II error rate / $1-\beta$, the chance of detecting a real effect.
- **False discovery rate**: the share of significant results that are false positives.
- **Replication crisis**: the failure of many published findings to reproduce.
- **Effect size**: the size of a difference in meaningful units.
- **Practical significance**: whether an effect is large enough to matter.
- **p-hacking**: trying many analyses until one is significant.

## Check yourself

```quiz
[
  {"q": "Which is the correct reading of p = 0.03 in an A/B test?", "options": ["If the change had no effect, a difference at least this large would occur 3% of the time", "There is a 3% chance the change has no effect", "There is a 97% chance the change works", "The effect is 3%"], "answer": 0,
   "explain": "The p-value conditions on the null being true; it is not a probability of the null."},
  {"q": "You run 1,000 A/A tests at α = 0.05. About how many are significant?", "options": ["50", "0", "500", "950"], "answer": 0,
   "explain": "Under the null, p-values are uniform, so about 5% fall below 0.05."},
  {"q": "A type II error is…", "options": ["failing to detect a real effect", "detecting an effect that is not there", "using the wrong test", "a data-entry error"], "answer": 0,
   "explain": "Type I = false positive, type II = false negative."},
  {"q": "10% of tested ideas truly work, power is 80% and α = 0.05. Roughly what share of significant results are false?", "options": ["About 36%", "5%", "20%", "80%"], "answer": 0,
   "explain": "False wins 0.9 × 0.05 = 0.045; true wins 0.1 × 0.8 = 0.08; 0.045/0.125 ≈ 0.36."},
  {"q": "With 10 million users per arm, a 0.1-point conversion lift has $p < 0.0001$. What should you do?", "options": ["Judge whether a 0.1-point lift is worth its cost; significance does not make it important", "Ship immediately because p is tiny", "Ignore it because the effect is fake", "Rerun with fewer users"], "answer": 0,
   "explain": "Huge samples make tiny effects significant; practical significance is a separate business question."},
  {"q": "A test has 50% power for the effect you care about and returns p = 0.4. The best conclusion is…", "options": ["Inconclusive: the test could easily miss an effect of that size", "The feature has no effect", "The feature has a 40% chance of working", "The test proves the null"], "answer": 0,
   "explain": "Low power means non-significant results carry little information."},
  {"q": "Which practice inflates false positives?", "options": ["Checking many segments and metrics and reporting the one with $p < 0.05$", "Choosing one primary metric in advance", "Running an A/A test", "Reporting confidence intervals"], "answer": 0,
   "explain": "This is p-hacking: each extra comparison is another chance for a false alarm."}
]
```

> **Source:** Bruce & Bruce, *Practical Statistics for Data Scientists* (O'Reilly, 2017), ch. 3, "Statistical Significance and P-Values" (p-value, alpha, type 1 and type 2 errors, data science and p-values, the ASA statement) and "Power and Sample Size"; American Statistical Association, "Statement on Statistical Significance and P-Values" (2016), paraphrased.
