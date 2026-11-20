# Linear models: regression, ridge, lasso and logistic regression

Linear models are among the most widely used models in practice, with roots going back over a century.
They train fast, predict fast, scale to huge and sparse datasets, and are relatively easy to interpret.
Even if you end up shipping a gradient-boosted ensemble, a well-regularised linear model is the baseline
every interviewer expects you to try. This lesson follows Müller & Guido's tour of linear models and adds
the derivations they skip.

## 1. The prediction formula

For regression with $p$ features:

$$\hat y = w_1x_1 + w_2x_2 + \dots + w_px_p + b = w^\top x + b.$$

With a single feature this is a line: $w_1$ is the slope and $b$ the intercept (offset). With two features
it is a plane, and with more it is a hyperplane. scikit-learn stores $w$ in `coef_` and $b$ in
`intercept_`. Linear models differ in **how** they choose $w$ and $b$ (the loss) and in **how they control
complexity** (regularisation).

A line looks restrictive, and in one dimension it is. But Müller & Guido stress that **with many features
linear models become very powerful**. If $p > n$, any target can be fit perfectly by a linear function on
the training set.

## 2. Ordinary least squares (linear regression)

OLS minimises the **mean squared error** on the training set:

$$\min_{w,b}\ \frac1n\sum_{i=1}^n (y_i - w^\top x_i - b)^2 .$$

It has **no hyperparameters**. That is convenient, but it also means you can't control its complexity. The
closed-form solution is $\theta = (\tilde X^\top\tilde X)^{-1}\tilde X^\top y$ (problem *ml-normal-equation*),
and gradient descent gives the same answer (problem *ml-gd-linear-regression*).

```python-run
import numpy as np
from sklearn.datasets import load_diabetes
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

X, y = load_diabetes(return_X_y=True)          # 442 patients x 10 features
X_tr, X_te, y_tr, y_te = train_test_split(X, y, random_state=0)
lr = LinearRegression().fit(X_tr, y_tr)
print("coef_:", lr.coef_.round(1))
print("intercept_:", round(lr.intercept_, 1))
print(f"train R2={lr.score(X_tr, y_tr):.3f}  test R2={lr.score(X_te, y_te):.3f}")
```

With only 10 features, the training score itself is modest ($R^2pprox0.55$): the model is too simple to
explain much, so the main problem here is underfitting, not memorisation. The book
then shows the opposite case: on the extended Boston housing data with 104 engineered features, OLS reaches
$R^2\approx 0.95$ on training data but only $\approx 0.61$ on the test set. That is clear overfitting, and
we need a way to restrict the model.

```python-run
import numpy as np
from sklearn.datasets import load_diabetes
from sklearn.preprocessing import PolynomialFeatures, MinMaxScaler
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

X, y = load_diabetes(return_X_y=True)
X = PolynomialFeatures(degree=2, include_bias=False).fit_transform(MinMaxScaler().fit_transform(X))
print("expanded features:", X.shape[1])            # 10 -> 65, like the book's extended Boston
X_tr, X_te, y_tr, y_te = train_test_split(X, y, random_state=0)
lr = LinearRegression().fit(X_tr, y_tr)
print(f"OLS train R2={lr.score(X_tr, y_tr):.3f}  test R2={lr.score(X_te, y_te):.3f}  <- overfitting")
```

## 3. Ridge regression (L2 regularisation)

Ridge adds a penalty on the size of the coefficients:

$$\min_{w,b}\ \sum_i (y_i - w^\top x_i - b)^2 + \alpha\lVert w\rVert_2^2 .$$

Regularisation means **explicitly restricting a model to avoid overfitting**. Ridge wants every $w_j$ close
to zero, so each feature has as little effect on the output as possible, while still predicting well. The
hyperparameter `alpha` sets the trade-off:

- larger `alpha` gives smaller coefficients and a simpler model, which is worse on training data and often
  better on test data;
- `alpha` → 0 recovers OLS;
- ridge still has a closed form: $w = (X^\top X + \alpha I)^{-1}X^\top y$. Adding $\alpha I$ also makes the
  matrix invertible when features are collinear;
- the intercept is **not** penalised.

```python-run
import numpy as np
from sklearn.datasets import load_diabetes
from sklearn.preprocessing import PolynomialFeatures, MinMaxScaler
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.model_selection import train_test_split

X, y = load_diabetes(return_X_y=True)
X = PolynomialFeatures(2, include_bias=False).fit_transform(MinMaxScaler().fit_transform(X))
X_tr, X_te, y_tr, y_te = train_test_split(X, y, random_state=0)
print(" alpha     train   test   max|coef|")
for alpha in [0.0001, 0.01, 0.1, 1, 10]:
    r = Ridge(alpha=alpha).fit(X_tr, y_tr)
    print(f"{alpha:7g}   {r.score(X_tr, y_tr):.3f}  {r.score(X_te, y_te):.3f}   {np.abs(r.coef_).max():9.1f}")
```

Note how the coefficients shrink as `alpha` grows. The book also shows **learning curves** for ridge vs
OLS. With little data OLS learns nothing useful, and with enough data the regularisation matters less and
the two converge.

## 4. Lasso (L1 regularisation)

$$\min_{w,b}\ \frac{1}{2n}\sum_i (y_i - w^\top x_i - b)^2 + \alpha\lVert w\rVert_1$$

The L1 penalty drives some coefficients **exactly to zero**, so lasso performs **automatic feature
selection**. The model becomes easier to interpret, because it uses only the important features. There is
no closed form, so scikit-learn uses coordinate descent. If you lower `alpha`, raise `max_iter`.

```python-run
import numpy as np
from sklearn.datasets import load_diabetes
from sklearn.preprocessing import PolynomialFeatures, MinMaxScaler
from sklearn.linear_model import Lasso
from sklearn.model_selection import train_test_split

X, y = load_diabetes(return_X_y=True)
X = PolynomialFeatures(2, include_bias=False).fit_transform(MinMaxScaler().fit_transform(X))
X_tr, X_te, y_tr, y_te = train_test_split(X, y, random_state=0)
for alpha in [1.0, 0.1, 0.01, 0.001]:
    las = Lasso(alpha=alpha, max_iter=100000).fit(X_tr, y_tr)
    print(f"alpha={alpha:<6} train={las.score(X_tr, y_tr):.3f} test={las.score(X_te, y_te):.3f} "
          f"features used={np.sum(las.coef_ != 0)}/{X.shape[1]}")
```

**Why L1 gives zeros.** Picture the constrained form: minimise the loss subject to $\lVert w\rVert_1\le t$.
The L1 ball is a diamond with corners on the axes. The loss contours usually first touch the diamond at a
corner, where some coordinates are zero. The L2 ball is round and has no corners, so ridge shrinks weights
smoothly but rarely to exactly zero.

**Which to use?** The book's advice: in practice ridge is usually the first choice. If you have many features
and expect only a few to matter, or you want an interpretable model, use lasso. `ElasticNet` combines both
penalties and works best in practice, at the cost of two parameters to tune (`alpha` and `l1_ratio`).

> [!INTERVIEW]
> **"Ridge vs lasso. When would you use each?"** Both shrink coefficients to fight overfitting. L2 spreads
> weight across correlated features and keeps all of them. L1 yields sparse models (feature selection) but
> picks somewhat arbitrarily among correlated features. Elastic net is the compromise. Always scale features
> first, because the penalty treats all coefficients equally.

## 5. Linear models for classification

For binary classification, threshold the linear function at zero:

$$\hat y = \begin{cases}1 & w^\top x + b > 0\\ 0 & \text{otherwise}\end{cases}$$

The **decision boundary** $w^\top x + b = 0$ is a line, plane or hyperplane. Algorithms differ in the loss
they minimise and the regulariser they use. The two most common are:

### Logistic regression

Despite its name it is a **classification** algorithm. It models the probability of the positive class with
the sigmoid of the linear score:

$$P(y=1\mid x) = \sigma(w^\top x + b) = \frac{1}{1+e^{-(w^\top x+b)}}$$

and is trained by **maximum likelihood**, which means minimising the log-loss (binary cross-entropy):

$$J(w,b) = -\frac1n\sum_i\Big[y_i\log p_i + (1-y_i)\log(1-p_i)\Big] + \text{penalty}.$$

**Gradient derivation.** With $z = w^\top x + b$ and $p=\sigma(z)$:
$\frac{\partial\ell}{\partial p} = -\frac{y}{p} + \frac{1-y}{1-p}$ and $\frac{\partial p}{\partial z} = p(1-p)$,
so $\frac{\partial \ell}{\partial z} = p - y$. Then $\nabla_w J = \frac1n X^\top(p-y)$ and $\partial J/\partial b =
\overline{p - y}$. There is no closed form, but the loss is convex, so gradient methods (`lbfgs`, the default)
find the global minimum. Implement it in *ml-logreg-gradient*.

**The odds view.** $\log\frac{p}{1-p} = w^\top x + b$: each coefficient is the change in **log-odds** per unit
of its feature. A coefficient of 0.7 multiplies the odds by $e^{0.7}\approx 2$.

### Linear support vector machines

`LinearSVC` minimises the **hinge loss** $\max(0, 1 - y_i(w^\top x_i+b))$ with $y\in\{-1,+1\}$. Points that
are correctly classified with a margin of at least 1 contribute nothing. It gives very similar boundaries to
logistic regression but no probabilities.

### The C parameter

For `LogisticRegression` and `LinearSVC`, regularisation strength is set by **`C`, the inverse of `alpha`**:
**higher C means less regularisation**. With high `C` the model tries to classify every training point
correctly. With low `C` it prefers small coefficients and tolerates some mistakes. By default
`LogisticRegression` applies L2; use `penalty="l1", solver="liblinear"` or `"saga"` for sparsity.

```python-run
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

X, y = load_breast_cancer(return_X_y=True)
X_tr, X_te, y_tr, y_te = train_test_split(X, y, stratify=y, random_state=42)
sc = StandardScaler().fit(X_tr); X_tr, X_te = sc.transform(X_tr), sc.transform(X_te)
for C in [0.001, 0.01, 1, 100]:
    for pen in ["l2", "l1"]:
        lr = LogisticRegression(C=C, penalty=pen, solver="liblinear").fit(X_tr, y_tr)
        print(f"C={C:<6} {pen}: train={lr.score(X_tr, y_tr):.3f} test={lr.score(X_te, y_te):.3f} "
              f"nonzero coefs={np.sum(lr.coef_ != 0):2d}/30")
```

## 6. Multiclass with linear models

Many linear classifiers are binary by nature. The common extension is **one-vs-rest (OvR)**: train one
binary classifier per class (that class vs all the others) and predict the class whose classifier gives the
highest score. You end up with one coefficient vector and one intercept per class, so `coef_` has shape
`(n_classes, n_features)`. Modern `LogisticRegression` instead fits a true **multinomial** (softmax) model:

$$P(y=c\mid x) = \frac{e^{w_c^\top x + b_c}}{\sum_{k} e^{w_k^\top x + b_k}}.$$

```python-run
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
X, y = load_iris(return_X_y=True)
clf = LogisticRegression(max_iter=1000).fit(X, y)
print("coef_ shape:", clf.coef_.shape, " intercept_ shape:", clf.intercept_.shape)
print("probabilities for first sample:", clf.predict_proba(X[:1]).round(3), "-> sum to 1")
```

## 7. Strengths, weaknesses and parameters

From the book:

- **Main parameter**: regularisation, `alpha` for regression and `C` for `LogisticRegression`/`LinearSVC`.
  Large `alpha` or small `C` means a simple model. Search them on a **log scale** (0.001, 0.01, 0.1, …).
- **L1 or L2?** Use L1 if you believe only a few features matter or interpretability is important;
  otherwise default to L2.
- **Very fast** to train and predict. They scale to very large datasets and **work well with sparse data**.
  For hundreds of thousands to millions of samples, try `solver="sag"`/`"saga"`, or `SGDClassifier`/
  `SGDRegressor`.
- **Interpretable in principle**, but correlated features make individual coefficients hard to read. Their
  signs can even flip.
- They shine when **the number of features is large relative to the number of samples**. In
  low-dimensional spaces, more flexible models such as kernel SVMs and trees often generalise better.

> [!WARNING]
> Coefficients are only comparable across features if the features are on the same scale. Standardise
> before interpreting or regularising, because otherwise the penalty hits small-scale features harder.

## 8. Method chaining

`fit` returns `self`, so you can write `LogisticRegression().fit(X_train, y_train).predict(X_test)`, as
the book's sidebar points out. Keep a reference to the fitted model if you need it later, though.

## Summary

- Linear models predict with $w^\top x + b$. Linear and logistic regression differ only in the loss and
  the output link.
- OLS has no complexity control. Ridge (L2) shrinks weights, lasso (L1) zeroes some out, and elastic net
  mixes the two.
- Logistic regression = sigmoid + log-loss = Bernoulli MLE. Its gradient is $X^\top(p-y)/n$.
- `alpha` up / `C` down → more regularisation. Tune on a log scale, and scale features first.
- Fast, scalable, good with sparse and high-dimensional data. Less flexible in low dimensions.

```quiz
[
  {"q": "In LogisticRegression, increasing C…", "options": ["reduces regularisation, allowing a more complex fit", "increases regularisation", "changes the loss to hinge", "has no effect with L2"], "answer": 0,
   "explain": "C is the inverse regularisation strength: high C trusts the training data more."},
  {"q": "Which model can set coefficients exactly to zero?", "options": ["Lasso (L1)", "Ridge (L2)", "Ordinary least squares", "All of them equally"], "answer": 0,
   "explain": "The L1 penalty's geometry (corners on the axes) produces sparse solutions."},
  {"q": "The gradient of the mean log-loss of logistic regression w.r.t. w is…", "options": ["Xᵀ(σ(Xw+b) − y)/n", "Xᵀ(y − Xw)/n", "σ(Xw)(1 − σ(Xw))", "2Xᵀ(Xw − y)/n"], "answer": 0,
   "explain": "∂ℓ/∂z = p − y, then the chain rule through z = Xw + b gives Xᵀ(p − y)/n."},
  {"q": "Ordinary least squares on 104 polynomial features gives train R² 0.95 and test R² 0.61. The best fix is…", "options": ["Add regularisation (e.g. Ridge) and tune alpha", "Remove the intercept", "Use more polynomial features", "Evaluate on the training set instead"], "answer": 0,
   "explain": "The large gap is overfitting; regularisation restricts the model's complexity."},
  {"q": "A logistic regression coefficient of ln(2) ≈ 0.69 for a feature means…", "options": ["each unit increase doubles the odds of the positive class", "the probability doubles", "the probability increases by 0.69", "the feature is twice as important as others"], "answer": 0,
   "explain": "Coefficients act on log-odds; exp(0.69) = 2 multiplies the odds."},
  {"q": "For a 3-class problem with 4 features, LogisticRegression.coef_ has shape…", "options": ["(3, 4)", "(4, 3)", "(1, 4)", "(4,)"], "answer": 0,
   "explain": "One weight vector per class."},
  {"q": "When do linear models tend to shine?", "options": ["Many features relative to samples, including sparse data", "Two or three features with complex interactions", "Image data with raw pixels and few samples", "Only when features are binary"], "answer": 0,
   "explain": "In high dimensions a hyperplane is very flexible; in low dimensions more expressive models usually win."},
  {"q": "Why should features be standardised before fitting Ridge?", "options": ["The penalty treats all coefficients equally, so scale affects which features are shrunk", "Ridge cannot handle negative numbers", "It makes the closed form unnecessary", "It removes the intercept"], "answer": 0,
   "explain": "A feature measured in small units needs a large coefficient and gets penalised more, unless features are scaled."}
]
```

> **Source:** Müller & Guido, *Introduction to Machine Learning with Python*, ch. 2 ("Linear Models": linear regression, ridge, lasso, linear models for classification, multiclass, strengths/weaknesses, method chaining); scikit-learn User Guide, "Linear Models".
