# Statistics interview essentials

> **Before this lesson:** this lesson reviews the whole track, so it is most useful after the others, especially [Statistical significance, p-values and their misconceptions](#/lesson/statistics/p-values), [Power and sample size for A/B tests](#/lesson/statistics/power-sample-size), [Correlation, causation and Simpson's paradox](#/lesson/statistics/causation-simpson) and [Logistic regression: odds, log-odds and maximum likelihood](#/lesson/statistics/logistic-regression). Each answer below links back to the lesson that explains it from scratch.

## In plain words

Statistics interviews for data science, machine learning and product analytics roles test three things: whether you understand the core ideas well enough to explain them simply, whether you can do quick calculations under pressure, and whether you have the judgement to spot when a number is misleading. This lesson is a revision kit: the concept questions that come up again and again with crisp model answers, a small toolkit of whiteboard calculations, a few classic probability puzzles solved both exactly and by simulation, and the traps that interviewers set deliberately.

An everyday picture: a driving test. You have learned the rules of the road (the earlier lessons); the test checks that you can apply them smoothly while someone watches, and that you notice the hazard the examiner planted. Practise answering out loud, briefly, then add nuance.

Why it matters for a job: at large technology companies in Singapore and elsewhere, data scientist and product analyst loops usually include a statistics round (concepts and calculations), a product or experimentation case (next lesson), and often a machine learning round. Interviewers are less impressed by jargon than by clear, correct, well-hedged explanations.

## 1. How to answer a statistics question

1. **Restate the question** and clarify assumptions: what is the unit, the population, the metric?
2. **Give the short answer first**, in one or two sentences, in plain language.
3. **Add the mechanism or formula**, then **a concrete example with numbers**.
4. **State the caveats**: assumptions that could fail and what you would do then.
5. **Offer to check**: "I could verify this with a quick simulation." Simulation is a respected way to confirm reasoning.

## 2. Core concept questions with model answers

**What is a p-value?** The probability, assuming the null hypothesis is true, of a result at least as extreme as the one observed. It is not the probability the null is true, and it says nothing about effect size. ([p-values](#/lesson/statistics/p-values))

**What does a 95% confidence interval mean?** The procedure that produced it captures the true parameter in 95% of repeated samples; this particular interval either contains it or not. ([confidence intervals](#/lesson/statistics/confidence-intervals))

**Explain the central limit theorem.** The mean of a large random sample is approximately normally distributed around the population mean with standard deviation $\sigma/\sqrt{n}$, whatever the data's shape, if the variance is finite and observations are independent. It justifies z- and t-based intervals and tests for means and proportions. ([CLT](#/lesson/statistics/sampling-distribution-clt))

**Type I versus type II error; what is power?** Type I is a false positive (rejecting a true null), rate $\alpha$; type II is a false negative, rate $\beta$; power $= 1 - \beta$, the chance of detecting a real effect of a given size. Power rises with effect size, sample size and $\alpha$, and falls with variance. ([power](#/lesson/statistics/power-sample-size))

**Standard deviation versus standard error?** SD describes the spread of individual values; SE describes the spread of an estimate across samples; for a mean, SE = SD / $\sqrt{n}$.

**When do you use a t-test versus a z-test?** Use a t-test for means with an estimated standard deviation (Welch's version by default); the z-test for proportions with large samples. With thousands of observations they agree. ([t-tests](#/lesson/statistics/t-tests))

**What is the bootstrap and when do you use it?** Resample the data with replacement many times, recompute the statistic, and use the spread for standard errors and intervals; ideal for medians, ratios and model metrics without formulas. Resample the independent unit (users). ([bootstrap](#/lesson/statistics/bootstrap))

**What is the multiple testing problem?** Many tests at 5% make at least one false positive likely ($1 - 0.95^{20} \approx 64\%$ for 20 tests). Control the family-wise error rate (Bonferroni, Holm) or the false discovery rate (Benjamini-Hochberg), and pre-register a primary metric. ([multiple testing](#/lesson/statistics/multiple-testing))

**Correlation versus causation?** Correlation can come from confounding, reverse causation, selection or chance; randomised experiments establish causation; without them use designs like difference-in-differences and state assumptions. ([causation](#/lesson/statistics/causation-simpson))

**What is Simpson's paradox?** A trend within every group reversing in the aggregate because group sizes differ by a confounder. ([Simpson's paradox](#/lesson/statistics/causation-simpson))

**Assumptions of linear regression?** Linearity, independent errors, constant error variance, normal errors (for small-sample inference). Check with residual plots; fix with transforms, extra terms, robust standard errors. ([diagnostics](#/lesson/statistics/regression-diagnostics))

**What is R² and why is it not enough?** The share of variance explained; it never falls when predictors are added, says nothing about causality or out-of-sample accuracy. Use adjusted $R^2$ and cross-validation. ([multiple regression](#/lesson/statistics/multiple-regression))

**What is multicollinearity?** Strongly correlated predictors make coefficients unstable with large standard errors; detect with VIF; drop, combine or regularise. Predictions may be fine. ([interpretation](#/lesson/statistics/factors-interpretation))

**How do you interpret a logistic regression coefficient?** The change in log-odds per unit of the predictor; $e^b$ is the odds ratio; translate into probabilities for concrete profiles because the probability effect depends on the baseline. ([logistic regression](#/lesson/statistics/logistic-regression))

**What is maximum likelihood?** Choose parameters that make the observed data most probable; logistic regression is fitted this way, iteratively.

**Bias-variance trade-off?** Expected error = bias² + variance + noise; flexible models lower bias but raise variance; cross-validation finds the balance; ensembles (bagging) reduce variance. ([statistical ML](#/lesson/statistics/statistical-ml))

**Precision, recall, AUC?** Precision: share of flagged cases that are positive. Recall: share of positives flagged. AUC: probability a random positive outranks a random negative. With rare classes, accuracy is misleading. ([classifier evaluation](#/lesson/statistics/classification-evaluation))

**Mean or median?** The median for a typical value of skewed data; the mean when totals matter (revenue forecasts). Report both for skewed metrics. ([location](#/lesson/statistics/data-and-location))

**Bayes' rule with a rare condition?** Base rates dominate: a 99%-sensitive, 95%-specific test for a 1% condition gives about a 17% chance of disease after a positive. ([probability](#/lesson/statistics/probability-bayes))

## 3. Whiteboard calculations

Three calculations come up constantly: a two-proportion test, an interval for the lift, and a sample size. Know the formulas and the rule of thumb $n \approx 16\sigma^2/\delta^2$ per arm (5% two-sided, 80% power).

```python-run
import numpy as np
from scipy import stats
def two_prop_test(x1, n1, x2, n2):
    p1, p2 = x1 / n1, x2 / n2
    pool = (x1 + x2) / (n1 + n2)
    z = (p2 - p1) / np.sqrt(pool * (1 - pool) * (1 / n1 + 1 / n2))
    se = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    return z, 2 * stats.norm.sf(abs(z)), (p2 - p1 - 1.96 * se, p2 - p1 + 1.96 * se)
def n_per_arm(p, mde, alpha=0.05, power=0.8):
    z = stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(power)
    return int(np.ceil(z**2 * (p * (1 - p) + (p + mde) * (1 - p - mde)) / mde**2))
z, p, ci = two_prop_test(480, 10_000, 540, 10_000)
print(f"z = {z:.2f}, p = {p:.4f}, 95% CI for lift ({ci[0]:.4f}, {ci[1]:.4f})")
print("users per arm for 4.8% -> 5.3%:", n_per_arm(0.048, 0.005))
```

**Reading this code line by line**

- `two_prop_test` returns the pooled z statistic, its two-sided p-value and the unpooled 95% interval for the difference.
- `n_per_arm` implements the sample-size formula for two proportions, with baseline `p` and absolute minimum detectable effect `mde`.
- The example: control converts 480 of 10,000 (4.8%), treatment 540 of 10,000 (5.4%).

The test gives $z = 1.93$, $p = 0.0538$, and the interval for the lift is $(-0.0001, 0.0121)$: narrowly short of significance at 5%, consistent with a lift anywhere from zero to 1.2 points. The sample-size calculation explains why: detecting a 0.5-point lift from 4.8% needs about 30,105 users per arm, three times what this test had. A good interview answer says exactly that: "inconclusive; the test was underpowered for effects of this size; I would extend it to about 30,000 per arm rather than declare no effect."

Mental arithmetic for the same numbers: pooled rate 5.1%, SE $\approx \sqrt{0.051 \times 0.949 \times 2/10{,}000} \approx 0.0031$; $z \approx 0.006/0.0031 \approx 1.9$. Rule of thumb for $n$: $16 \times 0.05 \times 0.95 / 0.005^2 \approx 30{,}400$.

## 4. Probability puzzles: solve, then simulate

Interviewers like short puzzles. Solve exactly if you can, and show you can check by simulation.

```python-run
import numpy as np
rng = np.random.default_rng(90)
def flips_until_hh():
    count, prev = 0, False
    while True:
        count += 1
        heads = rng.random() < 0.5
        if heads and prev:
            return count
        prev = heads
sims = [flips_until_hh() for _ in range(100_000)]
print("average flips until two heads in a row:", round(np.mean(sims), 3), "(exact 6)")
breaks = np.sort(rng.random((200_000, 2)), axis=1)
a, b, c = breaks[:, 0], breaks[:, 1] - breaks[:, 0], 1 - breaks[:, 1]
triangle = (a < 0.5) & (b < 0.5) & (c < 0.5)
print("P(three pieces of a randomly broken stick form a triangle):", round(triangle.mean(), 4), "(exact 0.25)")
```

**Reading this code line by line**

- `flips_until_hh` flips a fair coin until two heads appear consecutively, remembering whether the previous flip was heads, and returns the number of flips. `while True` loops until `return`.
- For the stick, two uniform break points are sorted (`np.sort(..., axis=1)` sorts each row) to give three pieces. Three lengths form a triangle exactly when each is less than half the total.

The simulations give 5.988 flips (exact answer 6) and 0.2493 (exact 0.25).

The exact reasoning for the coin, using expected values and conditioning (a standard technique): let $E$ be the expected number of flips from the start. The first flip is tails with probability 1/2, after which we are back at the start having used one flip. If it is heads, the second flip is heads (done after 2) or tails (back to the start after 2). So $E = \tfrac12(1 + E) + \tfrac14(2) + \tfrac14(2 + E)$, which solves to $E = 6$.

Other classics worth practising: the expected number of rolls to see all six faces (the coupon collector problem, $6 \times (1 + 1/2 + \dots + 1/6) = 14.7$); the birthday problem; the Monty Hall problem (switching wins with probability 2/3); the probability of at least one success in $n$ tries, $1 - (1-p)^n$; and expected value of games with stopping rules.

## 5. Traps interviewers set

- **"The test is significant, so ship it."** Ask about effect size, the interval, guardrails, novelty, multiple metrics and practical value.
- **"The test was not significant, so the feature does not work."** Ask about power; non-significance is not evidence of no effect.
- **"Our average session time rose 20%."** Check the median and the distribution; outliers or logging changes often drive means.
- **"Users who do X retain better, so push X."** Confounding and reverse causation; propose an experiment.
- **"We checked the experiment daily and stopped when it hit significance."** Peeking inflates false positives.
- **"Conversion fell, but every segment improved."** Simpson's paradox via mix shift.
- **"The model is 99% accurate."** Base rate? Precision and recall? Calibration?
- **"Treatment has 50.6% of users in a 50/50 test."** Sample ratio mismatch; investigate before reading results.

> [!INTERVIEW]
> Practise explaining each concept to two audiences: an engineer ("the p-value is the tail probability of the test statistic under the null") and a product manager ("if the change really did nothing, a result this big would happen about 5 times in 100 by luck alone"). Interviewers often ask for both.

## 6. A one-page formula sheet

| Quantity | Formula |
|---|---|
| Standard error of a mean | $s/\sqrt{n}$ |
| Standard error of a proportion | $\sqrt{p(1-p)/n}$ |
| SE of a difference (independent) | $\sqrt{SE_1^2 + SE_2^2}$ |
| 95% CI | estimate ± 1.96 SE (t critical value for small-sample means) |
| Two-proportion z | $(\hat p_2 - \hat p_1)/\sqrt{\hat p(1-\hat p)(1/n_1 + 1/n_2)}$ |
| Sample size per arm (5%, 80%) | $\approx 16\sigma^2/\delta^2$ |
| P(at least one false positive in m tests) | $1 - (1-\alpha)^m$ |
| Bonferroni threshold | $\alpha/m$ |
| Bayes' rule | $P(A\mid B) = P(B\mid A)P(A)/P(B)$ |
| Binomial mean / variance | $np$ / $np(1-p)$ |
| Poisson mean / variance | $\lambda$ / $\lambda$ |
| Odds ratio from logistic coefficient | $e^b$ |
| Adjusted $R^2$ | $1 - (1-R^2)(n-1)/(n-p-1)$ |

## Summary

- Answer in layers: short plain answer, mechanism, numbers, caveats, offer to simulate.
- Know crisp, correct definitions of the core concepts and their common misreadings.
- Practise the two-proportion test, the lift interval and the sample-size formula until automatic.
- Solve probability puzzles with conditioning and expected values, and check them with simulation.
- Recognise the standard traps: significance without size, underpowered nulls, means of skewed data, confounding, peeking, Simpson's paradox, accuracy on rare classes, sample ratio mismatch.

## Glossary

- **Conditioning (on the first step)**: solving an expected-value puzzle by splitting on what happens first.
- **Coupon collector problem**: the expected number of draws to see every one of $n$ equally likely items.
- **Monty Hall problem**: a puzzle where switching doors wins with probability 2/3.
- **Underpowered test**: a test with a low chance of detecting the effect of interest.
- **Formula sheet**: a short list of standard results worth memorising.

(Every other term in this lesson is defined in the lesson linked next to it.)

## Check yourself

```quiz
[
  {"q": "Control converts 4.8% and treatment 5.4% with 10,000 users each; p ≈ 0.054. The best answer to 'does it work?' is…", "options": ["Inconclusive: the interval runs from about 0 to 1.2 points and the test was underpowered for a 0.5-point lift", "No, the feature has no effect", "Yes, it is a 12.5% lift", "Yes, with 94.6% probability"], "answer": 0,
   "explain": "A non-significant result from an underpowered test does not show absence of an effect."},
  {"q": "Using the rule of thumb, users per arm to detect a lift from 10% to 11% (5%, 80% power) is about…", "options": ["14,400", "1,440", "144,000", "900"], "answer": 0,
   "explain": "$16 \\times 0.1 \\times 0.9 / 0.01^2 = 14{,}400$."},
  {"q": "What is the expected number of fair coin flips until the first head?", "options": ["2", "1", "1.5", "6"], "answer": 0,
   "explain": "Geometric distribution with p = 0.5: E = 1/p = 2. (Two heads in a row needs 6.)"},
  {"q": "An interviewer says 'every country's conversion rose, yet global conversion fell'. The first thing to check is…", "options": ["a shift in traffic mix towards lower-converting countries (Simpson's paradox)", "a bug in the p-value", "the CLT", "multicollinearity"], "answer": 0,
   "explain": "Aggregates mix rates and weights; a mix shift can reverse the direction."},
  {"q": "Which is the best plain-language explanation of a p-value of 0.03 for a product manager?", "options": ["If the change really did nothing, we would see a difference this large only about 3 times in 100 by chance", "There is a 97% chance the change works", "The change improves conversion by 3%", "We are 3% sure the result is wrong"], "answer": 0,
   "explain": "The p-value is a probability about the data assuming no effect."},
  {"q": "A model detecting a 1%-prevalence condition reports 99% accuracy. Your first question should be…", "options": ["What are its precision and recall? A model that always says 'no' is also 99% accurate", "Is the accuracy statistically significant?", "What is its R²?", "How many features does it use?"], "answer": 0,
   "explain": "With rare positives, accuracy hides whether the model finds any."},
  {"q": "With 10 independent tests at α = 0.05 and all nulls true, P(at least one false positive) is about…", "options": ["40%", "5%", "50%", "10%"], "answer": 0,
   "explain": "$1 - 0.95^{10} \\approx 0.40$."}
]
```

> **Source:** A review of the whole track, built on Bruce & Bruce, *Practical Statistics for Data Scientists* (O'Reilly, 2017), ch. 1 to 7; the puzzles and calculations are standard interview material worked here in original form.
