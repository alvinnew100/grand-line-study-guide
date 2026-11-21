# Logistic regression: odds, log-odds and maximum likelihood

> **Before this lesson:** [Multiple regression: assessment, cross-validation and model selection](#/lesson/statistics/multiple-regression) and [Factor variables and interpreting regression](#/lesson/statistics/factors-interpretation) (formulas, dummy coding, interpreting coefficients). The logistic function appeared in [Correlation, causation and Simpson's paradox](#/lesson/statistics/causation-simpson). The [ML track's linear models lesson](#/lesson/ml/linear-models) covers scikit-learn's `LogisticRegression` and regularisation; here the focus is the statistics.

## In plain words

Many outcomes are yes/no: churn or stay, click or not, default or repay. Linear regression on a 0/1 outcome can predict impossible values such as 1.3 or $-0.2$. **Logistic regression** fixes this by modelling the *log-odds* of the outcome as a linear function of the predictors, then squashing it through the S-shaped **logistic function** into a probability between 0 and 1. It is the most widely used classification model in industry because it is fast, gives calibrated probabilities, and has coefficients that can be explained.

An everyday picture: a dimmer switch versus an on/off switch. Linear regression on a yes/no outcome is like an on/off switch forced to report brightness levels it cannot have. Logistic regression is a dimmer whose knob (the linear score) can turn without limit, but the light (the probability) smoothly approaches fully off or fully on and never goes past them.

Why it matters for a job: churn models, conversion models, credit scoring and propensity models are usually logistic regressions or start from one. Interviewers ask: "What does a coefficient of 0.36 mean?", "What is an odds ratio?", "How is logistic regression fitted?", and "Why not use linear regression for a binary outcome?"

## 1. Probability, odds and log-odds

The **odds** of an event compare its probability of happening with its probability of not happening:

$$\text{odds} = \frac{p}{1-p}$$

Odds of 3 (often said "3 to 1") mean the event is three times as likely to happen as not, i.e. $p = 0.75$. Converting back, $p = \text{odds}/(1 + \text{odds})$. The **log-odds** (or **logit**) is the natural logarithm of the odds.

```python-run
import numpy as np
print(" p      odds    log-odds")
for p in [0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99]:
    print(f"{p:<5} {p / (1 - p):8.3f} {np.log(p / (1 - p)):8.3f}")
z = np.array([-4, -2, 0, 2, 4])
print("logistic(z):", np.round(1 / (1 + np.exp(-z)), 3))
```

**Reading this code line by line**

- The loop converts probabilities to odds and log-odds; `{p:<5}` left-aligns the value in a 5-character space.
- `1 / (1 + np.exp(-z))` is the **logistic function** (also called the sigmoid), the inverse of the logit: it turns any log-odds $z$ back into a probability.

Probabilities live between 0 and 1, odds between 0 and infinity, and log-odds anywhere from $-\infty$ to $+\infty$, symmetric around 0 (where $p = 0.5$). That unrestricted range is what makes log-odds a suitable target for a linear model. Going back, the logistic function maps $-4, -2, 0, 2, 4$ to 0.018, 0.119, 0.5, 0.881, 0.982: an S-curve.

## 2. The model

Logistic regression assumes

$$\log\frac{p}{1-p} = b_0 + b_1 x_1 + \dots + b_q x_q, \qquad p = \frac{1}{1 + e^{-(b_0 + b_1 x_1 + \dots + b_q x_q)}}$$

where $p$ is the probability that the outcome is 1. It belongs to the family of **generalised linear models** (GLMs), which combine a linear predictor with a **link function** (here the logit) and a distribution for the outcome (here the binomial, or Bernoulli for single 0/1 outcomes). Poisson regression for counts, with a log link, is another member of the family.

## 3. Fitting and reading a logistic regression

We simulate a subscription service where churn becomes less likely with tenure (months as a customer), more likely with each support ticket, and less likely on the premium plan.

```python-run
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
rng = np.random.default_rng(51)
n = 3000
tenure = rng.uniform(0, 48, n)
tickets = rng.poisson(1.5, n)
plan = rng.choice(["basic", "premium"], n, p=[0.7, 0.3])
logit = -0.5 - 0.06 * tenure + 0.35 * tickets - 0.8 * (plan == "premium")
churn = (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int)
df = pd.DataFrame(dict(churn=churn, tenure=tenure, tickets=tickets, plan=plan))
m = smf.logit("churn ~ tenure + tickets + C(plan)", data=df).fit(disp=0)
table = pd.DataFrame({"coef": m.params, "std err": m.bse, "z": m.tvalues, "odds ratio": np.exp(m.params)})
print(table.round(3))
ci = np.exp(m.conf_int())
print("95% CI for odds ratios:\n", ci.round(3))
print(f"log-likelihood {m.llf:.1f}, null {m.llnull:.1f}, LR test p {m.llr_pvalue:.2e}, pseudo R^2 {m.prsquared:.3f}")
```

**Reading this code line by line**

- The true log-odds are built from the three predictors; `(plan == "premium")` is `True`/`False`, which NumPy treats as 1/0. Each customer churns with the corresponding probability.
- `smf.logit(...)` fits logistic regression with the same formula syntax as `ols`; `fit(disp=0)` suppresses the progress messages.
- `np.exp(m.params)` turns each coefficient into an **odds ratio**, and `np.exp(m.conf_int())` turns the coefficient intervals into odds-ratio intervals.
- `llf` and `llnull` are the log-likelihoods of the fitted model and of a model with only an intercept; `llr_pvalue` is the likelihood-ratio test explained below; `prsquared` is McFadden's pseudo-$R^2$.

How to read the coefficients:

- **tickets: 0.361**. Each extra support ticket raises the log-odds of churning by 0.361, holding tenure and plan fixed. Exponentiated, the **odds ratio** is 1.434: each ticket multiplies the odds of churning by about 1.43, a 43% increase in the odds (95% CI 1.33 to 1.55).
- **tenure: $-0.062$**. Each extra month multiplies the odds by 0.940, a 6% decrease per month. Over a year, $0.940^{12} \approx 0.48$: the odds roughly halve.
- **premium: $-0.751$**. Premium customers have 0.472 times the odds of churning of basic customers with the same tenure and tickets.
- The true values were 0.35, $-0.06$ and $-0.8$; the estimates are close.

The z column is each coefficient divided by its standard error (logistic regression uses the normal rather than the t-distribution for these tests).

> [!WARNING]
> An odds ratio is not a ratio of probabilities. "Odds multiplied by 1.43" means a large change in probability when $p$ is near 0.5 and a small one when $p$ is near 0 or 1. When stakeholders want "how much more likely", compute predicted probabilities for concrete profiles, as in section 5.

## 4. How it is fitted: maximum likelihood

There is no "residual sum of squares" to minimise for 0/1 outcomes. Instead, logistic regression uses **maximum likelihood estimation** (MLE): choose the coefficients that make the observed outcomes as probable as possible. For each record the model gives a probability $p_i$; the **likelihood** of the data is the product of $p_i$ for records with $y_i = 1$ and $1 - p_i$ for records with $y_i = 0$. Products of many small numbers are awkward, so we maximise the **log-likelihood**

$$\ell(b) = \sum_i \big[y_i \log p_i + (1 - y_i)\log(1 - p_i)\big]$$

Its negative, averaged, is the **log-loss** (cross-entropy) used throughout machine learning. There is no closed-form solution; software uses an iterative method. The classic one is **Newton-Raphson** (also known here as iteratively reweighted least squares), which uses the first and second derivatives of $\ell$.

```python-run
import numpy as np
rng = np.random.default_rng(52)
n = 2000
x = rng.normal(0, 1, n)
y = (rng.random(n) < 1 / (1 + np.exp(-(0.5 + 1.2 * x)))).astype(float)
X = np.column_stack([np.ones(n), x])
beta = np.zeros(2)
for step in range(6):
    p = 1 / (1 + np.exp(-X @ beta))
    loglik = np.sum(y * np.log(p) + (1 - y) * np.log(1 - p))
    grad = X.T @ (y - p)
    hess = X.T @ (X * (p * (1 - p))[:, None])
    beta = beta + np.linalg.solve(hess, grad)
    print(f"step {step}: log-likelihood {loglik:9.3f}  beta {np.round(beta, 4)}")
```

**Reading this code line by line**

- We simulate data with true intercept 0.5 and slope 1.2. `X` has a column of ones (for the intercept) and the predictor.
- Each step computes the current probabilities, the log-likelihood, the **gradient** `X.T @ (y - p)` (the direction of steepest increase) and the **Hessian** (the matrix of second derivatives; here written in its positive form, $X^T W X$ with weights $p(1-p)$).
- The Newton update solves `hess @ step = grad` and moves the coefficients by that step. `[:, None]` turns the weight vector into a column so it multiplies each row of `X`.

Starting from zero (log-likelihood $-1386.294$, which is $2000 \times \log 0.5$, i.e. every probability 0.5), the method converges in about four steps to intercept 0.455 and slope 1.1894, with log-likelihood $-1118.554$. Statsmodels and scikit-learn do the same thing with more safeguards.

### Deviance, likelihood-ratio tests and pseudo-R²

- **Deviance** is $-2$ times the log-likelihood (relative to a perfect model); lower is better. It plays the role of RSS.
- The **likelihood-ratio test** compares nested models: twice the improvement in log-likelihood follows approximately a chi-square distribution with degrees of freedom equal to the number of added parameters. In the churn model, the log-likelihood improved from $-1552.4$ (intercept only) to $-1340.4$, an overwhelming improvement ($p = 1.4 \times 10^{-91}$).
- **McFadden's pseudo-$R^2$**, $1 - \ell_\text{model}/\ell_\text{null}$, here 0.137, is *not* comparable to linear regression's $R^2$; values of 0.2 to 0.4 already indicate a strong model. For prediction, judge the model by held-out metrics such as AUC and log-loss (next lesson).

## 5. Predicted probabilities

```python-run
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
rng = np.random.default_rng(51)
n = 3000
tenure = rng.uniform(0, 48, n)
tickets = rng.poisson(1.5, n)
plan = rng.choice(["basic", "premium"], n, p=[0.7, 0.3])
logit = -0.5 - 0.06 * tenure + 0.35 * tickets - 0.8 * (plan == "premium")
churn = (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int)
df = pd.DataFrame(dict(churn=churn, tenure=tenure, tickets=tickets, plan=plan))
m = smf.logit("churn ~ tenure + tickets + C(plan)", data=df).fit(disp=0)
profiles = pd.DataFrame({"tenure": [2, 2, 40, 40], "tickets": [0, 1, 0, 1], "plan": ["basic"] * 4})
profiles["P(churn)"] = m.predict(profiles).round(3)
print(profiles)
```

**Reading this code line by line**

- `profiles` describes four hypothetical basic-plan customers: new (2 months) or established (40 months), with zero or one ticket.
- `m.predict(profiles)` returns churn probabilities, applying the same formula transformations as in fitting.

One extra ticket raises a new customer's churn probability from 0.363 to 0.450 (8.7 points) but an established customer's only from 0.052 to 0.073 (2.1 points). The odds ratio is the same 1.43 in both cases; the probability change depends on where you start. This is how to communicate logistic results: concrete probabilities for meaningful profiles, or average **marginal effects** (`m.get_margeff().summary()` in statsmodels).

## 6. Logistic regression versus linear regression

| | Linear regression | Logistic regression |
|---|---|---|
| Outcome | continuous | binary (0/1) |
| Models | the mean of $Y$ | the log-odds of $P(Y=1)$ |
| Fitting | least squares (closed form) | maximum likelihood (iterative) |
| Coefficient meaning | change in $Y$ per unit | change in log-odds; $e^b$ = odds ratio |
| Fit measure | RSS, $R^2$, RMSE | deviance, log-loss, AUC, pseudo-$R^2$ |
| Residual diagnostics | residual plots | harder; use calibration plots, binned residuals |

Practical notes:

- **Scikit-learn regularises by default.** `LogisticRegression()` applies an L2 penalty with `C=1.0`, so its coefficients are shrunk and will not match statsmodels unless you set `penalty=None` (in recent versions). For interpretation and inference, use statsmodels; for prediction with many features, regularisation is a feature, not a bug.
- **Perfect separation**: if a predictor perfectly separates the classes, the likelihood keeps improving as a coefficient grows without bound, and the fit fails or reports huge standard errors. Regularisation fixes it.
- **Multiclass**: multinomial logistic regression (softmax) extends the model to more than two classes; ordinal logistic regression handles ordered categories.
- **Rare events**: with very few positives, the intercept reflects the low base rate, and probabilities are small; techniques for imbalanced data are in the next lesson.

> [!INTERVIEW]
> "Interpret a logistic coefficient of 0.36 for support tickets." Each additional ticket increases the log-odds of churn by 0.36, i.e. multiplies the odds by $e^{0.36} \approx 1.43$, holding other variables fixed. In probability terms the effect depends on the baseline: about +9 points for a new customer at 36% risk, +2 points for a loyal customer at 5%.

## Summary

- Odds are $p/(1-p)$; log-odds range over all real numbers, which makes them suitable for a linear model.
- Logistic regression models log-odds linearly and maps them to probabilities with the logistic function; it is a generalised linear model with a logit link.
- Coefficients change log-odds; exponentiated, they are odds ratios.
- Fitting is by maximum likelihood, iteratively (Newton-Raphson); deviance and likelihood-ratio tests compare models; pseudo-$R^2$ is not $R^2$.
- Communicate results as predicted probabilities for concrete profiles; the probability effect of a coefficient depends on the baseline.
- Scikit-learn regularises by default; statsmodels does not.

## Glossary

- **Odds**: $p/(1-p)$.
- **Log-odds (logit)**: the natural log of the odds.
- **Logistic (sigmoid) function**: $1/(1+e^{-z})$, the inverse of the logit.
- **Logistic regression**: a model of log-odds as a linear function of predictors.
- **Generalised linear model (GLM) / link function**: a linear predictor connected to the outcome's mean through a link / that connecting function.
- **Odds ratio**: the factor by which the odds change for a one-unit increase in a predictor, $e^b$.
- **Maximum likelihood estimation (MLE)**: choosing parameters that make the observed data most probable.
- **Likelihood / log-likelihood**: probability of the data given parameters / its logarithm.
- **Log-loss (cross-entropy)**: the negative average log-likelihood.
- **Newton-Raphson**: an iterative optimiser using first and second derivatives.
- **Gradient / Hessian**: vector of first derivatives / matrix of second derivatives.
- **Deviance**: $-2 \times$ log-likelihood (relative to a perfect model).
- **Likelihood-ratio test**: compares nested models using twice the log-likelihood difference.
- **Pseudo-$R^2$ (McFadden)**: $1 - \ell_\text{model}/\ell_\text{null}$.
- **Marginal effect**: the change in predicted probability for a change in a predictor.
- **Perfect separation**: a predictor that splits the classes perfectly, breaking MLE.

## Check yourself

```quiz
[
  {"q": "A probability of 0.8 corresponds to odds of…", "options": ["4", "0.8", "1.25", "0.25"], "answer": 0,
   "explain": "$0.8/0.2 = 4$."},
  {"q": "A logistic coefficient for tickets is 0.36. What is the odds ratio per extra ticket?", "options": ["About 1.43", "0.36", "1.36", "About 0.70"], "answer": 0,
   "explain": "$e^{0.36} \\approx 1.43$: the odds are multiplied by about 1.43."},
  {"q": "How is logistic regression fitted?", "options": ["By maximum likelihood, iteratively", "By least squares in closed form", "By k-means", "By counting matches"], "answer": 0,
   "explain": "No closed form exists; Newton-Raphson or similar methods maximise the log-likelihood."},
  {"q": "The same odds ratio of 1.43 produces a larger change in probability when the baseline probability is…", "options": ["near 0.5", "near 0", "near 1", "the effect is the same at any baseline"], "answer": 0,
   "explain": "The logistic curve is steepest at p = 0.5."},
  {"q": "Why not fit ordinary linear regression to a 0/1 churn outcome?", "options": ["It can predict probabilities below 0 or above 1 and assumes constant variance that binary data cannot have", "It cannot use more than one predictor", "It always gives the wrong sign", "It is too slow"], "answer": 0,
   "explain": "A linear probability model is unbounded and heteroskedastic; logistic regression respects the [0, 1] range."},
  {"q": "Coefficients from scikit-learn's default LogisticRegression differ from statsmodels' logit. The likely reason is…", "options": ["scikit-learn applies L2 regularisation by default", "statsmodels uses least squares", "they use different data", "scikit-learn reports odds ratios"], "answer": 0,
   "explain": "The default penalty shrinks coefficients; set penalty=None to match."},
  {"q": "A logistic model's McFadden pseudo-R² is 0.14. This means…", "options": ["a meaningful improvement over the intercept-only model; it is not comparable to a linear R² of 0.14", "the model explains 14% of variance", "the model is useless", "accuracy is 14%"], "answer": 0,
   "explain": "Pseudo-R² is on a different scale; judge predictive power with held-out AUC or log-loss."}
]
```

> **Source:** Bruce & Bruce, *Practical Statistics for Data Scientists* (O'Reilly, 2017), ch. 5, "Logistic Regression" (logistic response function and logit, logistic regression and the GLM, predicted values, interpreting the coefficients and odds ratios, linear and logistic regression: similarities and differences, maximum likelihood estimation, assessing the model); statsmodels documentation for `logit`. Data are simulated.
