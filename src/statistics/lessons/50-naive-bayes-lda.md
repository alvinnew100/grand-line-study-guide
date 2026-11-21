# Naive Bayes and discriminant analysis

> **Before this lesson:** Bayes' rule and conditional probability from [Probability, conditional probability and Bayes' rule](#/lesson/statistics/probability-bayes); the normal distribution from [Normal, t and long-tailed distributions](#/lesson/statistics/normal-t-long-tails); covariance from [Correlation and exploring two or more variables](#/lesson/statistics/correlation-bivariate). The [ML track's lesson on naive Bayes, trees and ensembles](#/lesson/ml/bayes-trees-ensembles) shows the scikit-learn workflow; this lesson focuses on the statistics behind the models.

## In plain words

**Classification** means predicting a category: spam or not, will default or not, which of several plans a user will pick. Many classifiers work by estimating, for each record, the probability of each class, then picking the most likely one (or using a threshold). This lesson covers two classic, statistically motivated classifiers. **Naive Bayes** applies Bayes' rule with a bold simplifying assumption that makes it fast and robust with many features. **Discriminant analysis** assumes each class's features follow a normal distribution and derives a boundary that best separates them.

An everyday picture: a doctor guessing a diagnosis from symptoms. Naive Bayes is like asking, for each disease, "how common is each of these symptoms among people with this disease?" and multiplying those, as if symptoms were unrelated. Discriminant analysis is like plotting patients on a chart of two measurements and drawing the straight line that best separates the healthy cloud from the sick cloud.

Why it matters for a job: naive Bayes remains a strong baseline for text classification and very high-dimensional data, and it is a favourite interview question because it tests Bayes' rule, independence and smoothing all at once. Linear discriminant analysis introduces ideas (class-conditional distributions, projections that maximise separation) that reappear in logistic regression and PCA.

## 1. The exact Bayesian classifier, and why it fails

For a record with predictor values $x_1, \dots, x_p$, the ideal classifier picks the class $C$ with the largest posterior probability $P(C \mid x_1, \dots, x_p)$. Bayes' rule gives

$$P(C \mid x_1, \dots, x_p) = \frac{P(x_1, \dots, x_p \mid C)\,P(C)}{P(x_1, \dots, x_p)}$$

With categorical predictors you could estimate $P(x_1, \dots, x_p \mid C)$ by counting records that match *all* the predictor values exactly. That fails quickly: with 20 yes/no predictors there are over a million combinations, and most new records match no training record at all.

## 2. The naive assumption

**Naive Bayes** assumes the predictors are **conditionally independent given the class**: within each class, knowing one predictor tells you nothing about another. Then the joint probability factorises into a product:

$$P(x_1, \dots, x_p \mid C) = P(x_1 \mid C)\,P(x_2 \mid C)\cdots P(x_p \mid C)$$

Each factor needs only one predictor's counts within one class, which is easy to estimate even with little data. The classifier computes, for each class,

$$\text{score}(C) = P(C) \prod_{j} P(x_j \mid C)$$

and normalises the scores so they sum to one. The assumption is usually false (words in an email are not independent), which is why the method is called "naive". It nevertheless classifies surprisingly well, because getting the *ranking* of classes right does not require exact probabilities.

## 3. Naive Bayes by hand

Twelve emails have three yes/no features: contains a link, subject in capital letters, sender known.

```python-run
import pandas as pd
emails = pd.DataFrame({
    "link":   ["yes", "yes", "no", "yes", "no", "no", "yes", "no", "yes", "no", "no", "yes"],
    "caps":   ["yes", "no", "yes", "yes", "no", "no", "yes", "no", "no", "no", "yes", "yes"],
    "known":  ["no", "no", "no", "no", "yes", "yes", "no", "yes", "yes", "yes", "yes", "yes"],
    "spam":   [1, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1],
})
new = {"link": "yes", "caps": "no", "known": "yes"}
scores = {}
for c in [0, 1]:
    sub = emails[emails.spam == c]
    prior = len(sub) / len(emails)
    like = 1.0
    for feat, val in new.items():
        like *= (sub[feat] == val).mean()
    scores[c] = prior * like
    print(f"class {c}: prior {prior:.3f}, likelihood product {like:.4f}, score {scores[c]:.5f}")
print(f"P(spam | new email) = {scores[1] / (scores[0] + scores[1]):.3f}")
```

**Reading this code line by line**

- `emails[emails.spam == c]` keeps the emails of one class.
- `prior` is the class's share of all emails, $P(C)$.
- For each feature of the new email, `(sub[feat] == val).mean()` is the share of that class's emails with the same value: the estimate of $P(x_j \mid C)$. The loop multiplies them.
- The final line normalises the two scores into a probability.

Both classes have prior 0.5. For non-spam, links are rare (1 of 6), capital-letter subjects uncommon (5 of 6 have none) and known senders universal, giving a likelihood product of $1/6 \times 5/6 \times 6/6 = 0.1389$. For spam, links are common (5/6) but subjects without capitals (1/6) and known senders (1/6) are rare: $0.0231$. The posterior probability of spam is 0.143, so the email is classified as not spam.

## 4. The zero-frequency problem and smoothing

If a feature value never appears with a class in the training data, its estimated probability is 0, and the whole product becomes 0, however strongly the other features point to that class. One unseen word can veto a classification.

```python-run
import numpy as np
from sklearn.naive_bayes import CategoricalNB
X = np.array([[1,1,0],[1,0,0],[0,1,0],[1,1,0],[0,0,1],[0,0,1],[1,1,0],[0,0,1],[1,0,1],[0,0,1],[0,1,1],[1,1,1]])
y = np.array([1,1,1,1,0,0,1,0,0,0,0,1])
new = np.array([[1, 0, 0]])
for alpha in [1e-10, 1.0]:
    nb = CategoricalNB(alpha=alpha).fit(X, y)
    print(f"alpha={alpha:g}: P(spam | link, no caps, unknown sender) = {nb.predict_proba(new)[0, 1]:.3f}")
```

**Reading this code line by line**

- The same emails coded as 0/1 columns (link, caps, known).
- `CategoricalNB(alpha=...)` is scikit-learn's naive Bayes for categorical features. `alpha` is the **smoothing** parameter: it adds `alpha` imaginary records of every value to every class's counts.
- `predict_proba(new)[0, 1]` is the predicted probability of class 1 (spam) for the single new email.

No non-spam email in the data comes from an unknown sender, so without smoothing (alpha almost 0) the model is 100% sure any unknown-sender email is spam. With **Laplace smoothing** (alpha = 1), the estimate for non-spam becomes $(0 + 1)/(6 + 2) = 0.125$ instead of 0, and the probability of spam is a more reasonable 0.857. Smoothing is standard practice, especially for text, where most words are absent from most classes.

## 5. Numeric predictors: Gaussian naive Bayes

For numeric predictors, naive Bayes needs a model for $P(x_j \mid C)$. **Gaussian naive Bayes** assumes each predictor is normally distributed within each class, estimates the class's mean and standard deviation, and plugs the normal density into the product (`GaussianNB` in scikit-learn). Alternatives are to bin numeric predictors into categories, or to use a density estimate.

## 6. Probabilities from naive Bayes are poorly calibrated

Because the independence assumption ignores correlations, naive Bayes multiplies what is really the same evidence several times. Its rankings are often good, but its probabilities are pushed towards 0 and 1: **overconfident**. A model is **calibrated** when, among cases given probability 0.9, about 90% are positive.

```python-run
import numpy as np
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LogisticRegression
rng = np.random.default_rng(51)
n = 4000
y = rng.integers(0, 2, n)
signal = rng.normal(y * 0.8, 1.0)
X = np.column_stack([signal + rng.normal(0, 0.3, n) for _ in range(5)])
for name, model in [("naive Bayes", GaussianNB()), ("logistic", LogisticRegression())]:
    p = model.fit(X[:3000], y[:3000]).predict_proba(X[3000:])[:, 1]
    confident = p > 0.95
    print(f"{name:11s}: share of test cases with P > 0.95: {confident.mean():.3f}, actual positive rate among them: {y[3000:][confident].mean():.3f}")
```

**Reading this code line by line**

- One underlying `signal` separates the classes, and five features are noisy copies of it, so the features are strongly correlated: the worst case for the naive assumption.
- Each model is trained on the first 3,000 records and predicts probabilities for the last 1,000.
- We look at test cases given a probability above 0.95 and check how many really are positive.

Naive Bayes gives 25.7% of test cases a probability above 0.95, but only 76.3% of those are actually positive: it counted the same evidence five times. Logistic regression, which accounts for correlated predictors, almost never claims such confidence here (0.2% of cases). If you need trustworthy probabilities (for expected-value decisions or ranking by risk), recalibrate naive Bayes (`CalibratedClassifierCV`) or use logistic regression.

## 7. Discriminant analysis

**Discriminant analysis** is one of the oldest classification methods, introduced by R. A. Fisher in 1936. **Linear discriminant analysis** (LDA) assumes that within each class the predictors follow a multivariate normal distribution, with a different mean per class but the **same covariance matrix** (the table of variances and covariances) for all classes. Under that assumption, the boundary where two classes are equally likely is a straight line (a hyperplane in more dimensions), which is why it is "linear".

Fisher's own view gives the intuition without any normality: find the direction $w$ such that, when the data are projected onto it, the class means are as far apart as possible relative to the spread within classes. In symbols, maximise the ratio of between-class variation to within-class variation. The solution is

$$w \propto S_W^{-1}(\mu_1 - \mu_0)$$

where $\mu_0, \mu_1$ are the class mean vectors and $S_W$ is the pooled **within-class scatter matrix** (sum of each class's covariance times its size). Records are classified by which side of a threshold their projection falls on.

```python-run
import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.linear_model import LogisticRegression
rng = np.random.default_rng(50)
cov = [[1.0, 0.6], [0.6, 1.0]]
X0 = rng.multivariate_normal([0, 0], cov, 300)
X1 = rng.multivariate_normal([1.5, 1.0], cov, 300)
X = np.vstack([X0, X1]); y = np.repeat([0, 1], 300)
mu0, mu1 = X0.mean(axis=0), X1.mean(axis=0)
Sw = np.cov(X0, rowvar=False) * 299 + np.cov(X1, rowvar=False) * 299
w = np.linalg.solve(Sw, mu1 - mu0)
print("Fisher direction (normalised):", np.round(w / np.linalg.norm(w), 3))
lda = LinearDiscriminantAnalysis().fit(X, y)
print("LDA coef direction (normalised):", np.round(lda.coef_[0] / np.linalg.norm(lda.coef_[0]), 3))
print(f"LDA accuracy {lda.score(X, y):.3f}; logistic accuracy {LogisticRegression().fit(X, y).score(X, y):.3f}")
proj = X @ (w / np.linalg.norm(w))
print(f"projected means: class 0 {proj[y == 0].mean():.2f}, class 1 {proj[y == 1].mean():.2f}")
```

**Reading this code line by line**

- `rng.multivariate_normal(mean, cov, 300)` draws 300 two-feature points from a normal distribution with the given mean vector and covariance matrix. Both classes share `cov` (the features correlate at 0.6), as LDA assumes.
- `np.vstack` stacks the two classes' rows; `np.repeat([0, 1], 300)` makes the labels.
- `np.cov(X0, rowvar=False)` is the 2 × 2 covariance matrix of class 0 (columns are variables); multiplying by $n - 1 = 299$ turns it into a scatter matrix. `np.linalg.solve(Sw, d)` computes $S_W^{-1} d$ without forming the inverse explicitly.
- `np.linalg.norm` gives a vector's length; dividing by it makes directions comparable.
- `X @ w` is matrix multiplication: each point's projection onto the direction.

Fisher's hand-computed direction (0.999, 0.037) and scikit-learn's LDA direction are identical. Interesting detail: although class 1 is shifted in *both* features (1.5 and 1.0), the best direction leans almost entirely on feature 1. Because the features are correlated, feature 2's shift is mostly explained by feature 1's; LDA accounts for that, which a naive per-feature comparison would not. Projected onto this direction, the classes' means sit at $-0.05$ and 1.56. LDA's accuracy (0.778) matches logistic regression's (0.777).

**Variants**: **quadratic discriminant analysis** (QDA) allows each class its own covariance matrix, giving curved boundaries at the cost of many more parameters. LDA can also be used for **dimension reduction**: with $k$ classes it finds up to $k - 1$ directions that best separate them, a supervised cousin of PCA.

## 8. When to use which

| Method | Assumes | Strengths | Weaknesses |
|---|---|---|---|
| Naive Bayes | predictors independent given class | very fast, many features, small data, text | probabilities overconfident; ignores interactions |
| LDA | normal classes, shared covariance | stable with small samples, interpretable direction, dimension reduction | linear boundary; sensitive to outliers |
| QDA | normal classes, separate covariances | curved boundaries | many parameters; needs more data |
| Logistic regression | linear log-odds | calibrated probabilities, fewer assumptions | needs more data than LDA when LDA's assumptions hold |

> [!INTERVIEW]
> "Why is naive Bayes called naive, and why does it still work?" It assumes features are independent within each class, which is rarely true. It works because classification only needs the correct class to have the highest score; errors in the probabilities often cancel or preserve the ranking. Mention Laplace smoothing for unseen values and that its probabilities should not be trusted without calibration.

## Summary

- Bayesian classification picks the class with the highest posterior; exact estimation is impossible with many predictors.
- Naive Bayes assumes conditional independence, so the likelihood is a product of single-predictor probabilities; it is fast and strong for high-dimensional data.
- Laplace smoothing prevents zero counts from vetoing a class.
- Naive Bayes rankings are often good but its probabilities are overconfident when predictors are correlated.
- LDA assumes normal classes with a shared covariance; Fisher's direction $S_W^{-1}(\mu_1 - \mu_0)$ maximises between-class relative to within-class separation; QDA relaxes the shared covariance.

## Glossary

- **Classification**: predicting a categorical outcome.
- **Posterior probability**: the probability of a class given the predictors.
- **Conditional independence**: independence of predictors within each class.
- **Naive Bayes**: a classifier using Bayes' rule with conditional independence.
- **Likelihood product**: the product of single-predictor probabilities within a class.
- **Zero-frequency problem**: a zero count making a whole product zero.
- **Laplace (additive) smoothing**: adding pseudo-counts to every value.
- **Gaussian naive Bayes**: naive Bayes with normal distributions for numeric predictors.
- **Calibration / overconfidence**: probabilities matching observed frequencies / being too close to 0 or 1.
- **Covariance matrix**: the table of variances and covariances of several variables.
- **Linear discriminant analysis (LDA)**: classification assuming normal classes with a shared covariance.
- **Within-class scatter matrix ($S_W$)**: the pooled spread of records around their class means.
- **Fisher's discriminant direction**: the projection that best separates class means relative to within-class spread.
- **Quadratic discriminant analysis (QDA)**: LDA with a separate covariance per class.

## Check yourself

```quiz
[
  {"q": "What is the 'naive' assumption in naive Bayes?", "options": ["Predictors are independent of each other within each class", "All classes are equally likely", "Predictors are normally distributed", "The classes are linearly separable"], "answer": 0,
   "explain": "Conditional independence lets the joint likelihood factor into a product."},
  {"q": "A word never appeared in any non-spam training email. Without smoothing, an email containing it gets…", "options": ["probability 0 of being non-spam, whatever else it contains", "a small but non-zero non-spam probability", "probability 0.5", "ignored"], "answer": 0,
   "explain": "One zero factor makes the whole product zero; Laplace smoothing fixes this."},
  {"q": "Naive Bayes is used on five highly correlated features. Its predicted probabilities will tend to be…", "options": ["too extreme (overconfident)", "too close to 0.5", "perfectly calibrated", "all equal"], "answer": 0,
   "explain": "Correlated features repeat the same evidence, which the product counts several times."},
  {"q": "LDA assumes that each class's predictors are…", "options": ["multivariate normal with a common covariance matrix", "independent within class", "uniformly distributed", "categorical"], "answer": 0,
   "explain": "QDA drops the shared-covariance assumption."},
  {"q": "Fisher's discriminant direction maximises…", "options": ["the separation of class means relative to the spread within classes", "the total variance of the data", "the number of correctly classified training points", "the correlation between features"], "answer": 0,
   "explain": "Maximising total variance would be PCA, which ignores labels."},
  {"q": "With 1,000 sparse text features and 500 training emails, a sensible first classifier is…", "options": ["naive Bayes with smoothing", "QDA", "exact Bayesian classification by matching all features", "LDA without regularisation"], "answer": 0,
   "explain": "Naive Bayes needs only per-feature counts and handles high dimensions well; QDA and exact Bayes need far more data."}
]
```

> **Source:** Bruce & Bruce, *Practical Statistics for Data Scientists* (O'Reilly, 2017), ch. 5, "Naive Bayes" (why exact Bayesian classification is impractical, the naive solution, numeric predictor variables) and "Discriminant Analysis" (covariance matrix, Fisher's linear discriminant); scikit-learn documentation for `CategoricalNB`, `GaussianNB` and `LinearDiscriminantAnalysis`. The examples are original.
