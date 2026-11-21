# Probability, statistics and maximum likelihood

> **Before this lesson:** basic Python, the words *sample*, *feature*, *label* and *vector* from [Linear algebra for ML](#/lesson/ml/linear-algebra), and the ideas of *loss*, *derivative* and *sigmoid* from [Calculus, gradients and gradient descent](#/lesson/ml/calculus-optimization). No statistics is assumed: we start from what a probability is.

## In plain words

**Probability** is a way of putting a number on uncertainty: 0 means "never", 1 means "always", and 0.3 means "about 3 times in 10". **Statistics** runs the other way: starting from data you have collected, it works out what you can reasonably conclude about the process that produced it.

A weather forecaster is a good picture of both. "70% chance of rain" is a probability. Deciding whether the forecaster is any good, by comparing a year of forecasts with what happened, is statistics. A machine-learning model is a forecaster too: a spam filter does not say "spam", it says "97% likely spam", and we judge it by comparing many such forecasts with the truth.

Why this matters for a job: the losses used to train models, the reason a model that looks accurate can still be useless on rare events, and the error bars on every reported result all come from this lesson. Interviewers love three topics here: Bayes' rule, maximum likelihood, and the bias-variance trade-off.

## 1. Random variables and distributions

A **random variable** is a quantity whose value depends on chance: the result of a coin flip, the number of emails arriving in an hour, tomorrow's temperature. We write it with a capital letter such as $X$, and $P(X = x)$ means "the probability that $X$ takes the value $x$".

A **distribution** is the full list of what values can occur and how likely each is. There are two kinds.

- A **discrete** variable takes separate values you can count (heads or tails; 0, 1, 2 emails). Its distribution gives a probability to each value, and the probabilities add up to 1. For a fair die, each of the six faces has probability $1/6$.
- A **continuous** variable can take any value in a range (a height, a temperature). The chance of any one exact value is zero, so its distribution is described by a **density** curve $p(x)$: the probability of landing between two values is the area under the curve between them.

Two numbers summarise a distribution.

The **expected value** (or **mean**), written $\mathbb E[X]$, is the long-run average: multiply each value by its probability and add up. For a fair die: $(1+2+3+4+5+6)/6 = 3.5$.

The **variance**, $\operatorname{Var}(X)$, measures spread: the average squared distance from the mean. Its square root is the **standard deviation**, written $\sigma$ (sigma), which is in the same units as the data.

$$\mathbb E[X] = \sum_x x\,P(x)\ \text{or}\ \int x\,p(x)\,dx,\qquad \operatorname{Var}(X) = \mathbb E[(X-\mathbb E X)^2] = \mathbb E[X^2]-(\mathbb EX)^2.$$

The $\sum$ form is for discrete variables. The $\int$ form (an integral, the continuous version of a sum) is for continuous ones; you will not need to compute one by hand here. Worked example: a coin that pays 1 for heads (probability 0.3) and 0 for tails. Mean: $1\times0.3 + 0\times0.7 = 0.3$. Variance: $(1-0.3)^2\times0.3 + (0-0.3)^2\times0.7 = 0.147 + 0.063 = 0.21$.

A handful of named distributions cover most of ML:

| distribution | settings | describes | ML connection |
|---|---|---|---|
| Bernoulli | $p$ | one yes/no outcome with chance $p$ of yes | yes/no labels, logistic regression |
| Categorical | $p_1..p_k$ | one of $k$ classes | the output of a classifier with several classes |
| Binomial | $n, p$ | number of yeses in $n$ tries | counts in A/B tests |
| Poisson | $\lambda$ | number of events in a time window, average $\lambda$ | predicting counts (`PoissonRegressor`) |
| Gaussian (normal) $\mathcal N(\mu,\sigma^2)$ | mean $\mu$, standard deviation $\sigma$ | the bell curve; measurement noise | squared-error loss, `GaussianNB`, starting weights |
| Uniform | $a,b$ | every value between $a$ and $b$ equally likely | random search over settings |
| Multinomial | $n, p_{1..k}$ | counts of each of $k$ outcomes in $n$ tries, such as word counts in a document | `MultinomialNB` for text |

```python-run
import numpy as np
rng = np.random.RandomState(0)
samples = {
    "Bernoulli(0.3)": rng.binomial(1, 0.3, 10000),
    "Poisson(4)": rng.poisson(4, 10000),
    "Normal(5, 2^2)": rng.normal(5, 2, 10000),
    "Uniform(0, 1)": rng.uniform(0, 1, 10000),
}
for name, s in samples.items():
    print(f"{name:16s} mean={s.mean():.3f} var={s.var():.3f}")
print("theory: Bernoulli mean p=0.3 var p(1-p)=0.21; Poisson mean=var=4; Normal 5, 4; Uniform 0.5, 1/12=0.083")
```

**Reading this code line by line**

- `rng = np.random.RandomState(0)` makes a random-number generator with a fixed seed, so the run is repeatable.
- Each `rng.<name>(...)` call draws 10,000 random values from a distribution. `rng.binomial(1, 0.3, 10000)` is 10,000 single yes/no tries with a 0.3 chance of yes, which is the Bernoulli. `rng.normal(5, 2, 10000)` is a bell curve with mean 5 and standard deviation 2.
- The values are stored in a dictionary so the loop can print each name with the average (`s.mean()`) and variance (`s.var()`) of its draws.
- The output shows the measured numbers landing close to the theoretical ones on the last line: for instance about 0.3 and 0.21 for the Bernoulli, matching the hand calculation above. Averages over many draws settle near the expected value.

## 2. Joint, marginal and conditional probability

Real questions involve more than one uncertain thing at once. Take 100 emails: 30 are spam, and 24 of those contain the word "prize"; of the 70 normal emails, 7 contain it.

- **Joint probability** $P(A, B)$: both things happen. $P(\text{spam}, \text{prize}) = 24/100 = 0.24$.
- **Marginal probability** $P(A)$: one thing, ignoring the other. It is found by adding up the joint probabilities over every possibility for the other: $P(A) = \sum_b P(A, B=b)$. Here $P(\text{prize}) = 0.24 + 0.07 = 0.31$.
- **Conditional probability** $P(A\mid B)$, read "probability of $A$ given $B$": the chance of $A$ among the cases where $B$ is known to hold. $P(A\mid B) = \frac{P(A,B)}{P(B)}$. Here $P(\text{prize}\mid\text{spam}) = 0.24/0.30 = 0.8$.
- **Independence**: two events are independent if knowing one tells you nothing about the other, $P(A\mid B) = P(A)$, which is the same as $P(A,B) = P(A)P(B)$. "Prize" and "spam" are not independent: the word is far more common in spam (0.8) than overall (0.31).

### Bayes' rule

We usually know the probability in one direction and want the other. We can count how often spam contains "prize", but the filter must answer "given this email contains prize, is it spam?" **Bayes' rule** turns one into the other:

$$P(y\mid x) = \frac{P(x\mid y)\,P(y)}{P(x)}\qquad\text{posterior} = \frac{\text{likelihood}\times\text{prior}}{\text{evidence}}$$

The four parts have names. The **prior** $P(y)$ is what you believed before seeing the evidence (30% of email is spam). The **likelihood** $P(x\mid y)$ is how probable the evidence is if $y$ were true (80% of spam says "prize"). The **evidence** $P(x)$ is how common the observation is overall (31%). The **posterior** $P(y\mid x)$ is your updated belief. For the emails: $0.8 \times 0.3 / 0.31 = 0.774$. Seeing "prize" lifts the chance of spam from 30% to 77%.

**Classic interview example.** A disease affects 1% of people. A test detects it 99% of the time when it is present (its **sensitivity**) and wrongly says "positive" for 5% of healthy people (its **false-positive rate**). You test positive. What is the chance you are sick?

Most people answer "99%". Count it out for 10,000 people: 100 are sick, and 99 of them test positive. 9,900 are healthy, and 5% of them, 495, also test positive. So of $99 + 495 = 594$ positives, only 99 are sick.

$$P(D\mid +) = \frac{0.99\cdot 0.01}{0.99\cdot 0.01 + 0.05\cdot 0.99} = \frac{0.0099}{0.0594}\approx 0.167.$$

About 17%. When the thing you are looking for is rare, false alarms from the huge healthy group swamp the true detections. The share of the population that has the condition is called the **base rate**, and forgetting it is the classic mistake. The same effect hits fraud detection and spam filtering, and it returns in the metrics lesson (52).

```python-run
import numpy as np
rng = np.random.RandomState(0)
n = 1_000_000
sick = rng.rand(n) < 0.01
positive = np.where(sick, rng.rand(n) < 0.99, rng.rand(n) < 0.05)
print("simulated P(sick | positive) =", round(sick[positive].mean(), 4))
print("Bayes' rule                  =", round(0.99 * 0.01 / (0.99 * 0.01 + 0.05 * 0.99), 4))
```

This checks the formula by simulation. `rng.rand(n)` draws a million random numbers between 0 and 1; comparing with `< 0.01` gives an array of True/False values that is True about 1% of the time, so `sick` marks who has the disease. `np.where(condition, a, b)` picks from `a` where the condition is True and from `b` elsewhere: sick people test positive with chance 0.99, healthy people with chance 0.05. `sick[positive]` keeps only the people who tested positive, and `.mean()` of True/False values is the fraction that are True. Both printed numbers are about 0.167.

### Naive Bayes in one line

A **naive Bayes classifier** (lesson 22) applies Bayes' rule with many features at once. Estimating how all the features behave together would need an impossible amount of data, so it makes one bold assumption: within a class, the features are independent of each other (**conditionally independent given the class**). Then the likelihood of a whole sample is the product of one factor per feature, $P(x\mid y) = \prod_j P(x_j\mid y)$, where $\prod$ (capital pi) means "multiply together". The classifier picks the class with the largest $P(y)\prod_j P(x_j\mid y)$; "the value that gives the largest result" is written $\arg\max_y$. The assumption is almost never true (words in an email are related), which is why it is called naive, yet the classifier is fast and often works well.

## 3. Estimating parameters: maximum likelihood (MLE)

A distribution has settings: the $p$ of a coin, the mean of a bell curve. Given data, how do we choose them? **Maximum likelihood estimation** (MLE) says: choose the settings under which the data you observed would have been most probable.

The data points are assumed to be **i.i.d.**, "independent and identically distributed": each is drawn from the same distribution and none influences another. Writing $\theta$ (theta) for the settings, the probability of the whole dataset is then a product, called the **likelihood**:

$$\mathcal L(\theta) = \prod_i p(x_i\mid\theta).$$

Multiplying thousands of numbers smaller than 1 gives a result too small for a computer to store (it **underflows** to zero). Taking the logarithm turns the product into a sum and does not move the position of the maximum, so we maximise the **log-likelihood** instead. Since optimisers minimise by habit, we flip the sign and minimise the **negative log-likelihood (NLL)**:

$$\hat\theta_{MLE} = \arg\min_\theta\ -\sum_i \log p(x_i\mid\theta).$$

The hat on $\hat\theta$ marks an estimate. Section 9 does a complete example with a coin. Two results to know by heart show that the standard ML losses are not arbitrary choices:

**Bernoulli gives binary cross-entropy.** Let the model say the label is 1 with probability $p_i = \sigma(w^\top x_i)$. The probability it gives to the label that was observed is $p_i$ if $y_i = 1$ and $1 - p_i$ if $y_i = 0$, which can be written in one expression as $p_i^{y_i}(1-p_i)^{1-y_i}$. Its negative log is $-[y_i\log p_i + (1-y_i)\log(1-p_i)]$, exactly the loss from the previous lesson. **Training logistic regression is maximum likelihood.**

**Gaussian noise gives mean squared error.** Suppose the label is a linear function plus bell-curve noise: $y_i = w^\top x_i + \varepsilon_i$ with $\varepsilon_i\sim\mathcal N(0,\sigma^2)$ (the $\sim$ means "is drawn from"). The negative log of the bell-curve density is $\frac{(y_i - w^\top x_i)^2}{2\sigma^2}$ plus a constant. Minimising the NLL is therefore minimising the squared error. **Least squares is maximum likelihood under Gaussian noise.**

One more fact with a practical consequence. The MLE of a Gaussian's mean is the average of the data, $\bar x$. The MLE of its variance is $\frac1n\sum(x_i-\bar x)^2$, which divides by $n$ and comes out slightly too small on average; an estimator that is wrong on average is called **biased**. Dividing by $n-1$ instead removes the bias (this is **Bessel's correction**). The libraries disagree on the default: NumPy's `std` and `var` divide by $n$ (`ddof=0`), pandas' `.std()` divides by $n-1$ (`ddof=1`), and scikit-learn's `StandardScaler` divides by $n$.

```python-run
import numpy as np
rng = np.random.RandomState(1)
true_var = 4.0
mle, unbiased = [], []
for _ in range(20000):
    x = rng.normal(0, 2, size=5)          # tiny samples make the bias visible
    mle.append(x.var(ddof=0))
    unbiased.append(x.var(ddof=1))
print("true variance:", true_var)
print("average MLE (ddof=0):     ", round(np.mean(mle), 3), "  -> (n-1)/n * 4 = 3.2")
print("average unbiased (ddof=1):", round(np.mean(unbiased), 3))
```

The loop repeats an experiment 20,000 times: draw 5 values from a bell curve whose true variance is 4, and estimate the variance both ways. Averaged over all the experiments, the divide-by-$n$ version gives about 3.2 (too small by the factor $4/5$), and the divide-by-$(n-1)$ version gives about 4. With large samples the difference vanishes.

## 4. MAP estimation and regularisation

Maximum likelihood trusts the data completely. **Maximum a posteriori** (MAP) estimation also takes into account a **prior**: a belief about which settings are plausible before seeing any data. It picks the settings that maximise likelihood times prior, $\hat\theta_{MAP} = \arg\max_\theta\, p(\text{data}\mid\theta)\,p(\theta)$, which by Bayes' rule is the most probable setting after seeing the data.

Take negative logs as before, and the prior becomes an extra term added to the loss:

- a Gaussian prior on the weights, $w\sim\mathcal N(0, \tau^2 I)$ (each weight is probably near zero, with spread $\tau$), adds $\frac{1}{2\tau^2}\lVert w\rVert_2^2$. That is the **ridge** or **L2** penalty;
- a Laplace prior (a distribution with a sharp peak at zero) adds $\frac1b\lVert w\rVert_1$. That is the **lasso** or **L1** penalty.

Adding a penalty on the size of the weights is called **regularisation** (lesson 21), and this shows what it means: a prior belief that weights should be small. A stronger belief (smaller $\tau$) is a larger penalty: a larger `alpha` in scikit-learn's ridge, or a smaller `C` in its logistic regression.

> [!INTERVIEW]
> **"What's the probabilistic interpretation of L2 regularisation?"** It is MAP estimation with a zero-mean Gaussian prior on the weights. L1 corresponds to a Laplace prior, whose sharp peak at zero explains why it sets many weights to exactly zero.

## 5. Information theory: entropy, cross-entropy, KL

Information theory measures uncertainty in a distribution. Three quantities appear constantly in ML. In each, $p_c$ is the probability of class $c$.

- **Entropy** $H(p) = -\sum_c p_c\log p_c$ measures how unpredictable a distribution is. A fair coin, with base-2 logs: $-(0.5\log_2 0.5 + 0.5\log_2 0.5) = 1$ bit, the most uncertain a two-way choice can be. A coin that always lands heads has entropy 0. Decision trees (lesson 22) use entropy to choose their questions.
- **Cross-entropy** $H(p, q) = -\sum_c p_c\log q_c$ measures how surprised a forecaster who believes $q$ is, on average, by outcomes that really follow $p$. In classification $p$ is the true label written as a **one-hot** vector (1 for the correct class, 0 for the others) and $q$ is the model's predicted probabilities, so the sum collapses to $-\log q_{\text{true class}}$. If the model gave the right class probability 0.8, the loss is $-\ln 0.8 = 0.22$; if it gave 0.1, the loss is 2.3.
- **Kullback-Leibler (KL) divergence** $D_{KL}(p\Vert q) = H(p,q) - H(p)$ is the extra surprise caused by believing $q$ when the truth is $p$. It is never negative, it is zero only when the two distributions match, and it is not symmetric (swapping $p$ and $q$ changes the value). Because $H(p)$ depends only on the data, minimising cross-entropy is the same as minimising KL divergence between the model and the data. KL also appears in t-SNE (lesson 31), in variational autoencoders and in distilling a large model into a small one.

## 6. Bias-variance decomposition

Why does a model do worse on new data than on the data it learned from? Suppose the true relationship is $y = f(x) + \varepsilon$, where $f$ is the real pattern and $\varepsilon$ is random noise with variance $\sigma^2$. Train a model $\hat f$ on one random set of training data; imagine repeating that with many different training sets. The average squared error at a point $x$ splits into three parts:

$$\mathbb E\big[(y - \hat f(x))^2\big] = \underbrace{\big(f(x) - \mathbb E\hat f(x)\big)^2}_{\text{bias}^2} + \underbrace{\mathbb E\big[(\hat f(x) - \mathbb E\hat f(x))^2\big]}_{\text{variance}} + \underbrace{\sigma^2}_{\text{irreducible noise}}.$$

- **Bias** is how far the *average* model (over all those training sets) is from the truth. High bias means the model is too rigid to capture the pattern: **underfitting**. A straight line through a wave-shaped curve is wrong however much data you collect.
- **Variance** is how much the model changes from one training set to another. High variance means the model is so flexible that it copies the accidental wiggles (the noise) of whichever training set it saw: **overfitting**. Retrain on a fresh sample and you get a very different curve.
- **Irreducible noise** is the randomness in the labels themselves. No model can remove it.

Picture darts: high bias is a tight group far from the bullseye; high variance is darts scattered all over the board. Making a model more flexible lowers bias and raises variance, so there is a best point in between. The levers are regularisation (less flexible), more data (lowers variance) and averaging many models (lesson 22).

```python-run
import numpy as np
rng = np.random.RandomState(0)
f = lambda x: np.sin(2 * np.pi * x)
x_test = np.linspace(0, 1, 50)
for degree in [1, 3, 9]:
    preds = []
    for _ in range(200):                       # 200 different training sets
        x = rng.rand(15)
        y = f(x) + 0.3 * rng.randn(15)
        coefs = np.polyfit(x, y, degree)
        preds.append(np.polyval(coefs, x_test))
    preds = np.array(preds)
    bias2 = np.mean((preds.mean(0) - f(x_test)) ** 2)
    var = np.mean(preds.var(0))
    print(f"degree {degree}: bias^2={bias2:.3f} variance={var:.3f} total={bias2 + var:.3f}")
```

**Reading this code line by line**

- `f` is the true pattern, one full wave of a sine curve. `np.linspace(0, 1, 50)` makes 50 evenly spaced test positions.
- For each of 200 imaginary training sets, the inner loop draws 15 random positions, computes noisy labels, and fits a **polynomial** to them with `np.polyfit`. A polynomial of degree 1 is a straight line, degree 3 can bend twice, and degree 9 can wiggle a great deal. `np.polyval` evaluates the fitted curve at the test positions.
- `preds.mean(0)` is the average curve across the 200 fits; its squared gap from the truth is the bias squared. `preds.var(0)` is how much the 200 curves disagree at each position: the variance.

The straight line has high bias (0.21) and low variance (0.05). Degree 3 keeps the variance low and removes nearly all the bias, giving the smallest total. Degree 9 is a disaster: a curve with ten adjustable numbers fitted to only 15 noisy points swings so violently between and beyond those points that the variance runs into the millions. (The printed bias for degree 9 is also huge, because even an average over 200 such wild curves has not settled down.) More flexibility than the data can support is worse than too little.

## 7. Sampling, the CLT and confidence intervals

A measured accuracy is itself a random quantity, because it depends on which test examples happened to be chosen. Three facts tell you how much to trust it.

- **Law of large numbers**: the average of many independent draws gets closer and closer to the expected value.
- **Central limit theorem** (CLT): the average of $n$ independent draws, each with variance $\sigma^2$, is distributed approximately as a bell curve $\mathcal N(\mu, \sigma^2/n)$ when $n$ is large, whatever the distribution of the individual draws. The standard deviation of that average, $\sigma/\sqrt n$, is called the **standard error**.
- A **confidence interval** is a range that would contain the true value in a stated share of repetitions; a 95% interval is roughly the estimate plus or minus two standard errors.

Applied to a test set: each test example is right or wrong, a Bernoulli with variance $p(1-p)$. With 100 test examples and 90% accuracy, the standard error is $\sqrt{0.9\times0.1/100}=0.03$, or 3 percentage points, so the 95% interval is roughly 84% to 96%. Two models that differ by 2 points on 100 examples cannot be told apart. Cross-validation (lesson 50) reduces this uncertainty.

```python-run
import numpy as np
rng = np.random.RandomState(0)
acc, n = 0.9, 100
estimates = rng.binomial(n, acc, size=10000) / n
print("spread of measured accuracy over 10k test sets of 100:")
print("  std =", estimates.std().round(4), " theory sqrt(p(1-p)/n) =", round(np.sqrt(acc * (1 - acc) / n), 4))
print("  95% of measurements in", np.percentile(estimates, [2.5, 97.5]))
```

`rng.binomial(n, acc, size=10000)` simulates 10,000 test sets of 100 examples for a model that is truly 90% accurate, returning the number correct in each; dividing by `n` gives 10,000 measured accuracies. Their standard deviation is about 0.03, matching the formula, and `np.percentile` shows that the middle 95% of measurements run from about 0.84 to 0.96. The same model can score 84% or 96% purely by luck of the draw.

## 8. Hypothesis testing in one paragraph

A **hypothesis test** asks whether an observed effect could be down to chance. You state a **null hypothesis** (the boring explanation: "the new model is no better than the old one") and compute a **p-value**: the probability, *assuming the null hypothesis is true*, of seeing data at least as extreme as what you observed. A small p-value (conventionally below 0.05) is taken as evidence against the null. It is not the probability that the null is true, a very common misreading. In ML you meet p-values in **A/B tests** (showing two versions to two random groups of users and comparing), in univariate feature selection (lesson 41, where `f_classif` and `chi2` give a p-value per feature) and when comparing models across cross-validation folds. Beware of running many tests: check 20 useless features at the 0.05 level and you should expect one to look "significant" by chance.

## 9. Worked example: maximum likelihood for a coin, step by step

The smallest complete MLE derivation uses a coin. You flip it $n$ times and see $k$ heads. What is the best estimate of $p$, the probability of heads?

**Likelihood.** The flips are independent, so the probability of the observed sequence is $p$ multiplied $k$ times (once per head) and $(1-p)$ multiplied $n-k$ times (once per tail):

$$\mathcal L(p) = p^k(1-p)^{n-k}.$$

**Log-likelihood.** Take the logarithm. The peak stays in the same place, and products become sums:

$$\log\mathcal L(p) = k\log p + (n-k)\log(1-p).$$

**Differentiate and set to zero.** At the peak the slope is zero. Using the rule that the derivative of $\log p$ is $1/p$:

$$\frac{d}{dp}\log\mathcal L = \frac{k}{p} - \frac{n-k}{1-p} = 0\quad\Longrightarrow\quad k(1-p) = (n-k)p\quad\Longrightarrow\quad \hat p = \frac{k}{n}.$$

The maximum-likelihood estimate is the observed fraction of heads: 7 heads in 10 flips gives 0.7. This matches intuition, and it is the same calculation that naive Bayes uses to estimate how common each class and each feature value is.

**The problem with small samples.** Flip three times and get three heads. The MLE says $\hat p = 1$: tails is impossible. That is overfitting in its purest form. A MAP estimate repairs it. With a Beta($\alpha$, $\beta$) prior (the Beta is a family of distributions over numbers between 0 and 1, suited to describing beliefs about a probability), the estimate becomes

$$\hat p_{MAP} = \frac{k + \alpha - 1}{n + \alpha + \beta - 2}.$$

With $\alpha=\beta=2$ this is $\frac{k+1}{n+2}$: add one imaginary head and one imaginary tail before counting. This is **Laplace (add-one) smoothing**, the `alpha` setting of `MultinomialNB`. Three heads out of three then gives $4/5 = 0.8$, not 1. As $n$ grows the two imaginary flips matter less and less, and MAP approaches the MLE.

```python-run
import numpy as np
n, k = 10, 7
grid = np.linspace(0.01, 0.99, 99)
log_lik = k * np.log(grid) + (n - k) * np.log(1 - grid)
print("grid search for the maximum of the log-likelihood:", grid[np.argmax(log_lik)].round(2), " formula k/n:", k / n)

print("\n   n   k   MLE    MAP with add-one smoothing")
for n, k in [(3, 3), (10, 10), (10, 7), (1000, 700)]:
    print(f"{n:4d} {k:4d}  {k / n:.3f}  {(k + 1) / (n + 2):.3f}")

rng = np.random.RandomState(0)
true_p = 0.3
for n in [5, 50, 5000]:
    estimates = rng.binomial(n, true_p, size=2000) / n
    print(f"n={n:5d}: MLE across 2000 experiments has mean {estimates.mean():.3f} and std {estimates.std():.3f}  (theory {np.sqrt(true_p * (1 - true_p) / n):.3f})")
```

The first block evaluates the log-likelihood at 99 candidate values of $p$ and uses `np.argmax` (the position of the largest entry) to find the best: 0.7, as the formula says. The table then compares the two estimates: for 3 out of 3 they differ a lot (1.000 against 0.800), for 700 out of 1,000 hardly at all. The last block shows two general properties of maximum likelihood. Across many repeated experiments the estimate is centred on the true value 0.3, and its spread shrinks like $1/\sqrt{n}$: to halve the uncertainty you need four times the data. The same law governs the error bars on a test-set accuracy in section 7.

## 10. Covariance, correlation and what they do not tell you

For two random variables, the **covariance** measures whether they move together: it is the average of (how far $X$ is above its mean) times (how far $Y$ is above its mean). It is positive when they tend to be high together, negative when one is high while the other is low.

$$\operatorname{Cov}(X, Y) = \mathbb E\big[(X - \mathbb EX)(Y - \mathbb EY)\big].$$

Its size depends on the units (centimetres or metres), so it is usually divided by both standard deviations to give the **correlation coefficient**, a pure number between −1 and 1:

$$\rho = \frac{\operatorname{Cov}(X,Y)}{\sigma_X\,\sigma_Y}\in[-1, 1].$$

A value of +1 means the points lie exactly on a rising straight line, −1 on a falling one, and 0 means no straight-line relationship. The **covariance matrix** of a dataset holds each feature's variance on its diagonal and each pair's covariance elsewhere. It is the object PCA takes apart (lesson 31), and strongly correlated features are the reason a linear model's weights can be hard to interpret.

Three cautions matter in practice:

- **Correlation measures only straight-line association.** If $y = x^2$ and $x$ is spread evenly around zero, the correlation is 0, yet $y$ is completely determined by $x$.
- **Correlation is not causation.** Ice-cream sales and drownings rise together because both depend on hot weather. A model can use such a feature to predict. It cannot tell you what would happen if you banned ice cream.
- **Independence implies zero correlation, but zero correlation does not imply independence.**

```python-run
import numpy as np
rng = np.random.RandomState(0)
x = rng.uniform(-1, 1, 5000)
pairs = {
    "y = 2x + noise": 2 * x + 0.3 * rng.randn(5000),
    "y = -x + noise": -x + 0.3 * rng.randn(5000),
    "y = x^2 (fully dependent)": x ** 2,
    "y independent of x": rng.randn(5000),
}
for name, yv in pairs.items():
    print(f"{name:27s} correlation = {np.corrcoef(x, yv)[0, 1]:+.3f}")
weather = rng.randn(5000)
ice_cream, drownings = weather + 0.5 * rng.randn(5000), weather + 0.5 * rng.randn(5000)
print("ice cream vs drownings (common cause):", round(float(np.corrcoef(ice_cream, drownings)[0, 1]), 3))
```

`np.corrcoef(x, yv)` returns a 2 × 2 grid of correlations; `[0, 1]` picks the one between the two variables. The rising line prints a correlation near +0.97, the falling line near −0.89, and both $y = x^2$ and the unrelated variable print about 0, even though the first is fully determined by $x$. The last line builds two quantities that each depend on a shared hidden cause (`weather`) and never on each other, and they come out correlated at about 0.8.

> [!INTERVIEW]
> **"Derive the MLE for a Bernoulli parameter."** Write the likelihood $p^k(1-p)^{n-k}$, take the log, differentiate, and solve to get $k/n$. Then volunteer the weakness: with few observations it can give probabilities of exactly 0 or 1, which is why smoothing (a prior) is used. Mentioning that the standard error is $\sqrt{p(1-p)/n}$ shows you understand how reliable the estimate is.

## Summary

- Know Bernoulli, categorical, Gaussian, Poisson and multinomial, and which loss each one implies.
- Bayes' rule converts likelihoods into posteriors. Base rates dominate when events are rare.
- MLE: Bernoulli gives cross-entropy, Gaussian gives MSE. MAP with Gaussian or Laplace priors gives L2 or L1 regularisation.
- Cross-entropy = entropy + KL. Training a classifier minimises the KL divergence to the data.
- Error = bias² + variance + noise. Flexibility trades bias for variance.
- Test metrics are estimates with standard errors. Small test sets mean wide error bars.

## Glossary

- **Random variable**: a quantity whose value depends on chance.
- **Distribution**: which values can occur and how likely each is.
- **Expected value (mean)**: the long-run average of a random variable.
- **Variance / standard deviation**: the average squared distance from the mean / its square root.
- **Joint, marginal, conditional probability**: both events together / one event ignoring the other / one event given that the other is known.
- **Independence**: knowing one event tells you nothing about the other.
- **Bayes' rule**: the formula that turns $P(x \mid y)$ into $P(y \mid x)$.
- **Prior / likelihood / posterior**: belief before the evidence / probability of the evidence under a hypothesis / belief after the evidence.
- **Base rate**: how common something is in the whole population.
- **i.i.d.**: independent and identically distributed; draws from the same distribution that do not affect each other.
- **Maximum likelihood estimation (MLE)**: choosing the settings that make the observed data most probable.
- **Negative log-likelihood (NLL)**: minus the log of the likelihood; the quantity MLE minimises.
- **Maximum a posteriori (MAP)**: MLE with a prior; equivalent to adding a regularisation penalty.
- **Entropy / cross-entropy / KL divergence**: uncertainty of a distribution / surprise of a model on real outcomes / the gap between the two.
- **Bias / variance**: error from a model being too rigid / error from a model changing too much with its training data.
- **Underfitting / overfitting**: too simple to capture the pattern / so flexible it learns the noise.
- **Standard error**: the standard deviation of an estimate such as a measured accuracy.
- **p-value**: probability of data at least this extreme if the null hypothesis were true.
- **Correlation**: a number from −1 to 1 measuring straight-line association between two variables.

## Check yourself

```quiz
[
  {"q": "A test is 99% sensitive with a 5% false-positive rate; prevalence is 1%. P(disease | positive) is about…", "options": ["17%", "99%", "95%", "50%"], "answer": 0,
   "explain": "0.0099 / (0.0099 + 0.0495) ≈ 0.167. Rare events make false positives dominate."},
  {"q": "Minimising mean squared error is equivalent to maximum likelihood under which noise model?", "options": ["Gaussian", "Laplace", "Bernoulli", "Poisson"], "answer": 0,
   "explain": "The Gaussian negative log-likelihood is a scaled squared error plus a constant. (Laplace noise gives MAE.)"},
  {"q": "L2 regularisation corresponds to MAP estimation with which prior on the weights?", "options": ["Zero-mean Gaussian", "Laplace", "Uniform", "Bernoulli"], "answer": 0,
   "explain": "−log of a Gaussian density is proportional to ||w||²."},
  {"q": "np.std(x) uses which denominator by default?", "options": ["n (ddof=0)", "n − 1 (ddof=1)", "n + 1", "it depends on the dtype"], "answer": 0,
   "explain": "numpy defaults to the population/MLE version; pandas defaults to ddof=1. StandardScaler uses ddof=0."},
  {"q": "A very deep, unpruned decision tree typically has…", "options": ["low bias, high variance", "high bias, low variance", "high bias, high variance", "zero error on new data"], "answer": 0,
   "explain": "It can fit the training set perfectly (low bias) but changes a lot with the training sample (high variance)."},
  {"q": "Cross-entropy H(p, q) equals…", "options": ["H(p) + KL(p || q)", "KL(q || p)", "H(q) − H(p)", "H(p) · H(q)"], "answer": 0,
   "explain": "Since H(p) is fixed by the data, minimising cross-entropy minimises the KL divergence."},
  {"q": "With 100 test samples and 90% accuracy, the standard error of the accuracy is about…", "options": ["3 percentage points", "0.3 points", "10 points", "0.09 points"], "answer": 0,
   "explain": "sqrt(0.9 × 0.1 / 100) = 0.03."},
  {"q": "A p-value of 0.03 means…", "options": ["If the null were true, data this extreme would occur 3% of the time", "The null hypothesis is true with probability 3%", "The alternative is true with probability 97%", "The effect size is 3%"], "answer": 0,
   "explain": "A p-value is computed assuming the null hypothesis; it is not a probability about the hypothesis itself."}
]
```

> **Source:** Müller & Guido, ch. 2 (naive Bayes, "Relation of model complexity to dataset size", predicting probabilities); Goodfellow et al., *Deep Learning*, ch. 3 and 5.5–5.6 (background on MLE/MAP); scikit-learn User Guide, "Naive Bayes".
