# Probability, statistics and maximum likelihood

Machine learning is statistics with a computer attached. Classifiers output **probabilities**. Naive Bayes
is Bayes' rule with a simplifying assumption. Logistic regression and neural networks are trained by
**maximum likelihood**. Overfitting is explained by the **bias–variance** decomposition. This lesson
gathers the probability you need for the rest of the track and for interviews.

## 1. Random variables and distributions

A **random variable** $X$ takes values according to a distribution. If it is discrete it has a
**probability mass function** $P(X=x)$; if it is continuous it has a **density** $p(x)$, with
probabilities given by areas under it. The two summaries you use most:

$$\mathbb E[X] = \sum_x x\,P(x)\ \text{or}\ \int x\,p(x)\,dx,\qquad \operatorname{Var}(X) = \mathbb E[(X-\mathbb E X)^2] = \mathbb E[X^2]-(\mathbb EX)^2.$$

Distributions you will see in ML:

| distribution | parameters | models… | ML connection |
|---|---|---|---|
| Bernoulli | $p$ | a yes/no outcome | binary labels → logistic regression, BCE loss |
| Categorical | $p_1..p_k$ | one of $k$ classes | softmax output, cross-entropy |
| Binomial | $n, p$ | # successes in $n$ trials | A/B test counts |
| Poisson | $\lambda$ | counts per interval | count regression (`PoissonRegressor`) |
| Gaussian $\mathcal N(\mu,\sigma^2)$ | $\mu,\sigma$ | measurement noise | MSE loss, `GaussianNB`, weight init |
| Uniform | $a,b$ | "anything in a range" | random search over hyperparameters |
| Multinomial | $n, p_{1..k}$ | word counts in a document | `MultinomialNB` for text |

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

## 2. Joint, marginal and conditional probability

- **Joint**: $P(A, B)$ means both happen.
- **Marginal**: $P(A) = \sum_b P(A, B=b)$.
- **Conditional**: $P(A\mid B) = \frac{P(A,B)}{P(B)}$.
- **Independence**: $P(A,B) = P(A)P(B)$, equivalently $P(A\mid B) = P(A)$.

### Bayes' rule

$$P(y\mid x) = \frac{P(x\mid y)\,P(y)}{P(x)}\qquad\text{posterior} = \frac{\text{likelihood}\times\text{prior}}{\text{evidence}}$$

**Classic interview example.** A disease affects 1% of people. A test detects it 99% of the time
(sensitivity) and has a 5% false-positive rate. If you test positive, what is the chance you are sick?

$$P(D\mid +) = \frac{0.99\cdot 0.01}{0.99\cdot 0.01 + 0.05\cdot 0.99} = \frac{0.0099}{0.0594}\approx 0.167.$$

Only about 17%. When positives are rare, false positives swamp the true ones. The same thing happens with
fraud detection and spam: precision collapses on imbalanced data even with an accurate-sounding classifier.
We return to this in the metrics lesson.

```python-run
import numpy as np
rng = np.random.RandomState(0)
n = 1_000_000
sick = rng.rand(n) < 0.01
positive = np.where(sick, rng.rand(n) < 0.99, rng.rand(n) < 0.05)
print("simulated P(sick | positive) =", round(sick[positive].mean(), 4))
print("Bayes' rule                  =", round(0.99 * 0.01 / (0.99 * 0.01 + 0.05 * 0.99), 4))
```

### Naive Bayes in one line

A naive Bayes classifier assumes the features are **conditionally independent given the class**, so
$P(x\mid y) = \prod_j P(x_j\mid y)$, and predicts $\arg\max_y P(y)\prod_j P(x_j\mid y)$. The assumption is
almost never true, yet the classifier is fast and often works well (lesson 2.3).

## 3. Estimating parameters: maximum likelihood (MLE)

Given i.i.d. data $x_1..x_n$ and a model $p(x\mid\theta)$, the **likelihood** is
$\mathcal L(\theta) = \prod_i p(x_i\mid\theta)$. MLE picks the $\theta$ that makes the observed data most
probable. Products of many small numbers underflow, so we maximise the **log-likelihood** instead, or
equivalently minimise the **negative log-likelihood (NLL)**:

$$\hat\theta_{MLE} = \arg\min_\theta\ -\sum_i \log p(x_i\mid\theta).$$

Two derivations to know cold:

**Bernoulli → binary cross-entropy.** With $p_i = \sigma(w^\top x_i)$, the per-sample likelihood is
$p_i^{y_i}(1-p_i)^{1-y_i}$. Its negative log is $-[y_i\log p_i + (1-y_i)\log(1-p_i)]$, exactly the
logistic-regression loss. **Logistic regression is MLE.**

**Gaussian noise → MSE.** If $y_i = w^\top x_i + \varepsilon_i$ with $\varepsilon_i\sim\mathcal N(0,\sigma^2)$, then
$-\log p(y_i\mid x_i) = \frac{(y_i - w^\top x_i)^2}{2\sigma^2} + \text{const}$. Minimising the NLL is minimising the
squared error. **Least squares is MLE under Gaussian noise.**

The MLE of a Gaussian's mean is the sample mean. The MLE of its variance is $\frac1n\sum(x_i-\bar x)^2$,
which divides by $n$ and is slightly **biased** (it underestimates). The unbiased estimator divides by
$n-1$ (Bessel's correction). numpy's `std` defaults to `ddof=0` (the MLE), pandas' `.std()` defaults to
`ddof=1`, and scikit-learn's `StandardScaler` uses `ddof=0`.

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

## 4. MAP estimation and regularisation

**Maximum a posteriori** estimation adds a prior: $\hat\theta_{MAP} = \arg\max_\theta\, p(\text{data}\mid\theta)\,p(\theta)$.
Taking negative logs:

- a Gaussian prior $w\sim\mathcal N(0, \tau^2 I)$ adds $\frac{1}{2\tau^2}\lVert w\rVert_2^2$, which is **ridge / L2**;
- a Laplace prior adds $\frac1b\lVert w\rVert_1$, which is **lasso / L1**.

Regularisation is a prior belief that weights should be small. A stronger belief (smaller $\tau$) means a
larger `alpha`, or a smaller `C` in scikit-learn.

> [!INTERVIEW]
> **"What's the probabilistic interpretation of L2 regularisation?"** It is MAP estimation with a
> zero-mean Gaussian prior on the weights. L1 corresponds to a Laplace prior, whose sharp peak at zero
> explains the sparse solutions.

## 5. Information theory: entropy, cross-entropy, KL

- **Entropy** $H(p) = -\sum_c p_c\log p_c$ measures uncertainty. Decision trees use it as a split criterion.
- **Cross-entropy** $H(p, q) = -\sum_c p_c\log q_c$ is the expected code length when you encode data from $p$
  with a code built for $q$. With $p$ the one-hot true label and $q$ the model's softmax, it is the
  classification loss.
- **KL divergence** $D_{KL}(p\Vert q) = H(p,q) - H(p) \ge 0$. It is not symmetric. Since $H(p)$ does not
  depend on the model, minimising cross-entropy is the same as minimising KL to the data distribution.
  KL also appears in t-SNE, VAEs, knowledge distillation and RLHF penalties.

## 6. Bias–variance decomposition

For squared error, with $y = f(x) + \varepsilon$ and a model $\hat f$ trained on a random training set:

$$\mathbb E\big[(y - \hat f(x))^2\big] = \underbrace{\big(f(x) - \mathbb E\hat f(x)\big)^2}_{\text{bias}^2} + \underbrace{\mathbb E\big[(\hat f(x) - \mathbb E\hat f(x))^2\big]}_{\text{variance}} + \underbrace{\sigma^2}_{\text{irreducible noise}}.$$

- **High bias (underfitting)**: the model is too simple to capture $f$. A straight line through a sine
  wave is wrong no matter how much data you collect.
- **High variance (overfitting)**: the model is so flexible that it chases the noise in the particular
  training set. Retrain on a new sample and you get a very different function.
- Model complexity trades one for the other. Regularisation, more data and ensembling (bagging averages
  away variance) are the levers. This is the "sweet spot" picture Müller & Guido draw in chapter 2.

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

Degree 1 has high bias, degree 9 has huge variance, and degree 3 is the sweet spot.

## 7. Sampling, the CLT and confidence intervals

- **Law of large numbers**: sample averages converge to the expectation.
- **Central limit theorem**: the mean of $n$ i.i.d. variables with variance $\sigma^2$ is approximately
  $\mathcal N(\mu, \sigma^2/n)$ for large $n$, whatever their distribution. The **standard error** is
  $\sigma/\sqrt n$.
- This is why test-set accuracy is uncertain. With 100 test samples and 90% accuracy, the standard error is
  $\sqrt{0.9\cdot0.1/100}=3\%$, so a 95% interval is roughly 84–96%. Two models differing by 2 points on 100
  samples are statistically indistinguishable. Cross-validation (module 5) helps reduce this variance.

```python-run
import numpy as np
rng = np.random.RandomState(0)
acc, n = 0.9, 100
estimates = rng.binomial(n, acc, size=10000) / n
print("spread of measured accuracy over 10k test sets of 100:")
print("  std =", estimates.std().round(4), " theory sqrt(p(1-p)/n) =", round(np.sqrt(acc * (1 - acc) / n), 4))
print("  95% of measurements in", np.percentile(estimates, [2.5, 97.5]))
```

## 8. Hypothesis testing in one paragraph

A **p-value** is the probability, *assuming the null hypothesis is true*, of seeing data at least as extreme
as what was observed. It is not the probability that the null is true. In ML you meet it in A/B tests
(comparing a new model online), in univariate feature selection (`f_classif`, `chi2` give p-values per
feature) and when comparing models on paired CV folds. Beware multiple comparisons: test 20 useless
features at $\alpha=0.05$ and you should expect one "significant" result.

## Summary

- Know Bernoulli, categorical, Gaussian, Poisson and multinomial, and which loss each one implies.
- Bayes' rule converts likelihoods into posteriors. Base rates dominate when events are rare.
- MLE: Bernoulli gives cross-entropy, Gaussian gives MSE. MAP with Gaussian/Laplace priors gives L2/L1
  regularisation.
- Cross-entropy = entropy + KL. Training a classifier minimises KL to the data distribution.
- Error = bias² + variance + noise. Complexity trades bias for variance.
- Test metrics are estimates with standard errors. Small test sets mean wide error bars.

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
