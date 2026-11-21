# Linear models: regression, ridge, lasso and logistic regression

> **Before this lesson:** you need overfitting, underfitting, model complexity and $R^2$ from [Generalisation, overfitting and k-NN](#/lesson/ml/generalization-knn). The dot product and norms come from [Linear algebra for ML](#/lesson/ml/linear-algebra); the sigmoid, the gradient and cross-entropy from [Calculus, gradients and gradient descent](#/lesson/ml/calculus-optimization). Each is recalled briefly where it is used.

## In plain words

A **linear model** predicts by giving every feature a **weight**, multiplying each feature's value by its weight, and adding everything up. That is all. A restaurant bill works the same way: 2 coffees at 3 each plus 1 cake at 5, plus a fixed service charge of 1, comes to 12. The prices are the weights, the quantities are the features, the service charge is a constant, and the total is the prediction. Training a linear model means working out the price list from a pile of past bills.

The members of the family differ in two respects: how they measure a wrong prediction, and how they are held back from fitting the training data too eagerly. That second idea, called **regularisation**, is the heart of this lesson.

Why this matters for a job: linear models are fast, cope with huge datasets, and can be explained to a non-specialist, so they are the first serious model tried on almost any problem and the yardstick for everything fancier. Interviewers ask about ridge versus lasso, about deriving the logistic-regression gradient, and about what a coefficient means.

## 1. The prediction formula

For a regression problem with $p$ features, the prediction is

$$\hat y = w_1x_1 + w_2x_2 + \dots + w_px_p + b = w^\top x + b.$$

Here $x_1, \dots, x_p$ are the feature values of one sample, $w_1, \dots, w_p$ are the weights (also called **coefficients**), $b$ is a constant called the **intercept** (or bias term), and $\hat y$ is the prediction. The short form $w^\top x$ is the dot product of the weight vector with the feature vector.

Numbers: a house-price model with weights 3 per square metre and 10 per bedroom, and an intercept of 50, predicts $3\times80 + 10\times2 + 50 = 310$ for an 80 m² flat with two bedrooms (in thousands, say).

With one feature the formula is a straight line: $w_1$ is the slope and $b$ is where the line crosses the vertical axis. With two features it is a flat plane, and with more it is the higher-dimensional equivalent, called a **hyperplane**. scikit-learn stores $w$ in the attribute `coef_` and $b$ in `intercept_`.

A straight line looks very limiting, and with one feature it is. With many features it is not: when there are more features than training samples ($p > n$), a linear function can fit *any* set of training targets perfectly. So linear models can overfit, and they need a way to be restrained.

## 2. Ordinary least squares (linear regression)

The classic way to choose the weights is **ordinary least squares** (OLS), known in scikit-learn as `LinearRegression`. It picks the $w$ and $b$ that make the **mean squared error** (MSE) on the training set as small as possible: for each sample, take the gap between the true value and the prediction, square it, and average.

$$\min_{w,b}\ \frac1n\sum_{i=1}^n (y_i - w^\top x_i - b)^2 .$$

($\min_{w,b}$ reads "choose $w$ and $b$ to minimise what follows".) OLS has **no hyperparameters**. That is convenient, and it also means there is no dial for controlling its complexity. The best weights can be computed directly by solving a set of linear equations (problem *ml-normal-equation*), or reached by gradient descent (problem *ml-gd-linear-regression*).

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

**Reading this code line by line**

- `load_diabetes` returns a built-in dataset: 442 patients, 10 measurements each (age, body-mass index, blood pressure and so on, already rescaled), and a number describing how far their diabetes had progressed a year later.
- `LinearRegression().fit(X_tr, y_tr)` finds the least-squares weights from the training patients.
- `lr.coef_` holds the ten weights, one per feature, and `lr.intercept_` the constant.
- `.score` returns $R^2$: 1 is perfect, 0 is no better than always predicting the average.

The training $R^2$ is 0.555 and the test $R^2$ is 0.359. Even on the data it was fitted to, the model explains only about half of the variation. With only ten features the model is too limited to do better, so the main problem here is underfitting.

To see the opposite problem, give the model many more features. The next demo adds every product of two features (lesson 40 explains why you might do that), turning 10 features into 65.

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

`MinMaxScaler` squeezes every feature into the range 0 to 1, and `PolynomialFeatures(degree=2)` adds the squares and pairwise products. Now the training $R^2$ rises to 0.647 while the test $R^2$ *falls* to 0.244. The extra flexibility was spent on fitting accidents of the training patients. That gap is overfitting, and it calls for a way to restrain the model.

## 3. Ridge regression (L2 regularisation)

**Regularisation** means deliberately restricting a model so that it cannot overfit as easily. **Ridge regression** does it by adding a second term to what is minimised: a penalty on the size of the weights.

$$\min_{w,b}\ \sum_i (y_i - w^\top x_i - b)^2 + \alpha\lVert w\rVert_2^2 .$$

The first term is the squared error as before. In the second, $\lVert w\rVert_2^2$ is the sum of the squared weights ($w_1^2 + w_2^2 + \dots$), called the **L2 penalty**, and $\alpha$ (alpha) is a number you choose that sets how much the penalty counts. The model now has two aims that pull against each other: predict the training data well, and keep every weight small. A weight is allowed to be large only if it earns its keep by reducing the error a lot.

Why should small weights generalise better? A large weight means the prediction swings sharply when that feature changes a little, which is the behaviour of a model chasing noise. Small weights give a smoother, more cautious model.

- A larger `alpha` gives smaller weights and a simpler model: worse on the training data, often better on the test data.
- As `alpha` approaches 0, ridge becomes OLS.
- Ridge can still be solved directly: $w = (X^\top X + \alpha I)^{-1}X^\top y$. Adding $\alpha I$ (alpha on the diagonal) also guarantees a unique solution when some features are nearly copies of others.
- The intercept is **not** penalised; only the weights are.

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

The loop fits ridge on the same 65 features with five values of `alpha` and prints the training score, the test score and the size of the largest weight (`np.abs` removes minus signs). Reading down the table, as `alpha` grows from 0.0001 to 10 the largest weight shrinks from about 1,635 to 36, the training score slips from 0.646 to 0.558, and the test score *climbs* from 0.245 to 0.394. Trading a little training accuracy for smaller weights bought better generalisation.

One more fact from learning curves: with little data, unregularised OLS learns almost nothing useful and ridge is far better; with plenty of data the penalty matters less and less, and the two models end up alike.

## 4. Lasso (L1 regularisation)

The **lasso** uses a different penalty: the sum of the *absolute values* of the weights, $\lVert w\rVert_1 = |w_1| + |w_2| + \dots$, the **L1 penalty**.

$$\min_{w,b}\ \frac{1}{2n}\sum_i (y_i - w^\top x_i - b)^2 + \alpha\lVert w\rVert_1$$

The change looks minor and has a striking effect: the L1 penalty drives some weights to **exactly zero**. A feature with a zero weight is ignored altogether, so the lasso performs **automatic feature selection**. A model that uses 9 features out of 65 is also much easier to explain. There is no direct formula for the solution; scikit-learn uses an iterative method called coordinate descent (it improves one weight at a time, cycling through them). With a small `alpha` it may need more rounds, so raise `max_iter` if you see a convergence warning.

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

`np.sum(las.coef_ != 0)` counts the weights that are not zero. With `alpha=1.0` the lasso keeps 9 of the 65 features and scores 0.359 on the test set, matching the plain ten-feature model with fewer inputs. As `alpha` shrinks, more features come back (23, 49, 56), the training score rises and the test score falls: the overfitting returns.

**Why L1 gives zeros and L2 does not.** Think of each penalty as a budget for the weights. With two weights, the set of weight pairs within an L1 budget is a diamond whose corners sit on the axes, where one weight is zero. The set within an L2 budget is a circle, with no corners. The best fit within the budget is the point where the error first touches the shape, and a diamond is usually touched at a corner. Section 9 shows the same thing with algebra.

**Which to use?** Ridge is the usual first choice. Reach for the lasso when you have many features and expect only a few to matter, or when you need a model that is easy to interpret. `ElasticNet` combines both penalties and often works best, at the price of two settings to tune (`alpha` and `l1_ratio`, the share given to L1).

> [!INTERVIEW]
> **"Ridge vs lasso. When would you use each?"** Both shrink the weights to fight overfitting. L2 spreads weight across correlated features and keeps all of them. L1 produces sparse models (feature selection), but among a group of correlated features it keeps one somewhat arbitrarily. Elastic net is the compromise. Always put the features on the same scale first, because the penalty treats all weights alike.

## 5. Linear models for classification

A linear formula produces a number, and classification needs a category. For two classes (call them 0 and 1), the fix is to compute the same weighted sum, called the **score**, and check which side of zero it falls on:

$$\hat y = \begin{cases}1 & w^\top x + b > 0\\ 0 & \text{otherwise}\end{cases}$$

The set of points where the score is exactly zero, $w^\top x + b = 0$, is the **decision boundary**. With two features it is a straight line dividing the plane into a class-1 side and a class-0 side; in general it is a hyperplane. The different linear classifiers all predict this way. They differ in how they choose the weights.

### Logistic regression

Despite its name, **logistic regression** is a classification method. It turns the score into a probability with the **sigmoid** function $\sigma(z) = 1/(1+e^{-z})$, an S-shaped curve that maps any number into the range 0 to 1:

$$P(y=1\mid x) = \sigma(w^\top x + b) = \frac{1}{1+e^{-(w^\top x+b)}}$$

A score of 0 gives probability 0.5; a score of 2 gives $1/(1+e^{-2}) = 0.88$; a score of −2 gives 0.12. So the sign of the score decides the class, and its size says how confident the model is.

The weights are chosen by maximum likelihood (make the observed labels as probable as possible), which is the same as minimising the **log loss**, also called binary cross-entropy:

$$J(w,b) = -\frac1n\sum_i\Big[y_i\log p_i + (1-y_i)\log(1-p_i)\Big] + \text{penalty}.$$

Here $p_i$ is the predicted probability for sample $i$. When the true label is 1, the sample contributes $-\log p_i$: nearly 0 if the model said 0.99, and 4.6 if it said 0.01. Confident mistakes cost a great deal.

**The gradient.** The calculus lesson derived it step by step: with $z = w^\top x + b$ and $p=\sigma(z)$, the slope of the loss with respect to the score is $p - y$, the predicted probability minus the truth. Passing that back to the weights gives $\nabla_w J = \frac1n X^\top(p-y)$, and for the intercept the average of $p - y$. There is no direct formula for the best weights, but the loss is convex (a single bowl), so an iterative solver finds the one global minimum. scikit-learn's default solver is called `lbfgs`. You implement the gradient in *ml-logreg-gradient*.

**The odds view.** The **odds** of an event are its probability divided by the probability of its opposite: a probability of 0.8 is odds of $0.8/0.2 = 4$, or "4 to 1". Rearranging the sigmoid gives $\log\frac{p}{1-p} = w^\top x + b$: the score is the logarithm of the odds. So each weight is the change in **log-odds** when its feature goes up by one unit. A weight of 0.7 multiplies the odds by $e^{0.7}\approx 2$. This is how logistic-regression weights are read in medicine and finance.

### Linear support vector machines

`LinearSVC` chooses the weights with a different loss, the **hinge loss**: $\max(0, 1 - y_i(w^\top x_i+b))$, where the labels are written as −1 and +1. If a point is on the correct side with a score of at least 1 (a comfortable **margin**), the loss is zero and the point has no further influence. Points that are misclassified, or correct but too close to the boundary, are penalised in proportion to how far they fall short. The resulting boundaries are much like those of logistic regression, but the model gives no probabilities. Lesson 23 returns to support vector machines.

### The C parameter

For `LogisticRegression` and `LinearSVC`, the strength of regularisation is set by **`C`, which works in the opposite direction to `alpha`**: a **higher C means less regularisation**. With a high `C` the model tries hard to classify every training point correctly. With a low `C` it prefers small weights and accepts some training mistakes. `LogisticRegression` applies the L2 penalty unless told otherwise; `penalty="l1"` with `solver="liblinear"` or `"saga"` gives sparse weights.

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

The data is the 30-feature tumour dataset, standardised so that every feature has mean 0 and spread 1 (the scaler is fitted on the training part only, then applied to both). The loops try four values of `C` with each penalty. Three things show in the output. With `C=0.001` and L1, the penalty is so strong that all 30 weights are zero and the model can only guess the majority class (0.371 here). At `C=1` both penalties give about 0.99 on the test set, and L1 does it with 16 of the 30 features. At `C=100` the training accuracy reaches 1.000 while the test accuracy drops to about 0.95: too little regularisation, and the overfitting returns.

## 6. More than two classes

Many linear classifiers are built for two classes. The standard way to stretch them is **one-vs-rest** (OvR): train one two-class model per class, each answering "is it this class or any of the others?", and predict the class whose model gives the highest score. You end up with one weight vector and one intercept per class, so `coef_` has the shape (number of classes, number of features).

`LogisticRegression` instead fits a single model for all classes, called **multinomial** or **softmax** regression. Each class $c$ gets its own score $w_c^\top x + b_c$, and the **softmax** function turns the scores into probabilities that are positive and add up to 1: raise $e$ to each score, then divide by the total.

$$P(y=c\mid x) = \frac{e^{w_c^\top x + b_c}}{\sum_{k} e^{w_k^\top x + b_k}}.$$

Example: scores of 2, 1 and 0 give $e^2 = 7.39$, $e^1 = 2.72$ and $e^0 = 1$, total 11.11, so the probabilities are 0.67, 0.24 and 0.09.

```python-run
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
X, y = load_iris(return_X_y=True)
clf = LogisticRegression(max_iter=1000).fit(X, y)
print("coef_ shape:", clf.coef_.shape, " intercept_ shape:", clf.intercept_.shape)
print("probabilities for first sample:", clf.predict_proba(X[:1]).round(3), "-> sum to 1")
```

On the three-species iris data, `coef_` has shape `(3, 4)`: three classes, four features. `predict_proba` returns one probability per class; for the first flower it gives 0.982 for setosa, 0.018 for versicolor and practically 0 for virginica.

## 7. Strengths, weaknesses and parameters

- **Main setting**: the regularisation strength, `alpha` for the regression models and `C` for `LogisticRegression` and `LinearSVC`. A large `alpha` or a small `C` means a simpler model. Search over powers of ten (0.001, 0.01, 0.1, 1, 10...), which is called searching on a **log scale**, because the effect depends on the ratio between values, not the difference.
- **L1 or L2?** Use L1 if you believe only a few features matter, or if you need to explain the model; otherwise start with L2.
- **Speed.** Linear models train and predict very quickly, scale to very large datasets, and **work well with sparse data** (mostly zeros, such as word counts). For hundreds of thousands of samples or more, try `solver="sag"` or `"saga"`, or the `SGDClassifier` and `SGDRegressor` classes, which learn by stochastic gradient descent.
- **Interpretable, with a caveat.** Each weight says how the prediction moves with one feature. But when features are strongly correlated, the model can shift weight between them freely, so individual weights become hard to read, and their signs can even be the opposite of what you expect.
- **Where they shine**: when the number of features is large compared with the number of samples. With only a few features, more flexible models such as trees (lesson 22) often generalise better.

> [!WARNING]
> Weights can be compared across features only if the features are on the same scale. A feature measured in millimetres needs a weight a thousand times smaller than the same feature in metres. Standardise before interpreting weights and before regularising; otherwise the penalty falls unevenly on features according to their units.

## 8. Method chaining

`fit` returns the model itself, so you can write `LogisticRegression().fit(X_train, y_train).predict(X_test)` on one line. This is called **method chaining**. It is compact, but the fitted model is thrown away afterwards, so store it in a variable if you need it again.

## 9. Worked example: how ridge shrinks a coefficient

One feature and no intercept is enough to see exactly what the penalty does. Ridge then minimises $\sum_i (y_i - wx_i)^2 + \alpha w^2$ over the single weight $w$. At the minimum the slope is zero. Differentiating (the derivative of a square is twice the inside, times the derivative of the inside) and setting the result to zero:

$$-2\sum_i x_i(y_i - wx_i) + 2\alpha w = 0\quad\Longrightarrow\quad \hat w_{ridge} = \frac{\sum_i x_iy_i}{\sum_i x_i^2 + \alpha}.$$

With $\alpha = 0$ this is the least-squares slope. A positive $\alpha$ makes the bottom of the fraction larger, so the weight shrinks towards zero. It never reaches zero for any finite $\alpha$.

Take $x = (1, 2, 3)$ and $y = (2, 4, 7)$. Then $\sum x_iy_i = 2 + 8 + 21 = 31$ and $\sum x_i^2 = 1 + 4 + 9 = 14$.

| $\alpha$ | $\hat w = 31/(14+\alpha)$ |
|---|---|
| 0 | 2.214 |
| 1 | 2.067 |
| 14 | 1.107 |
| 100 | 0.272 |

Setting $\alpha$ equal to $\sum x_i^2$ halves the weight. The table also shows why scale matters. If $x$ were recorded in units ten times smaller, its values would be ten times larger, $\sum x_i^2$ would be 100 times larger, and the same $\alpha$ would shrink the weight far less.

For the lasso, the same one-feature problem has a different solution: reduce the least-squares weight by a fixed amount, and stop at zero. This is called **soft thresholding**. A weight whose least-squares value is smaller than the fixed amount is set exactly to zero, which is the algebra behind the lasso's feature selection. Ridge divides (never reaching zero); lasso subtracts (and can reach it).

```python-run
import numpy as np
from sklearn.linear_model import Ridge
x, y = np.array([1.0, 2.0, 3.0]), np.array([2.0, 4.0, 7.0])
for alpha in [0, 1, 14, 100]:
    by_hand = (x @ y) / (x @ x + alpha)
    sk = Ridge(alpha=alpha, fit_intercept=False).fit(x.reshape(-1, 1), y).coef_[0]
    print(f"alpha={alpha:3d}: formula {by_hand:.3f}   scikit-learn {sk:.3f}")
```

`x @ y` is the dot product $\sum x_i y_i$ and `x @ x` is $\sum x_i^2$, so `by_hand` is the formula above. `x.reshape(-1, 1)` turns the flat list into a table with one column, as scikit-learn requires, and `fit_intercept=False` switches the intercept off to match the derivation. The two columns of output agree to three decimals and reproduce the table.

## Summary

- Linear models predict with $w^\top x + b$. Linear and logistic regression differ in the loss and in what is done with the score.
- OLS has no complexity control. Ridge (L2) shrinks the weights, lasso (L1) sets some to zero, and elastic net mixes the two.
- Logistic regression is a sigmoid on a linear score, trained with log loss. Its gradient is $X^\top(p-y)/n$.
- `alpha` up or `C` down means more regularisation. Tune on a log scale, and scale the features first.
- Fast, scalable, and good with sparse data and many features. Less flexible when there are few features.

## Glossary

- **Linear model**: a model that predicts with a weighted sum of the features plus a constant.
- **Weight (coefficient)**: the number a feature is multiplied by; stored in `coef_`.
- **Intercept**: the constant added to the weighted sum; stored in `intercept_`.
- **Hyperplane**: the higher-dimensional version of a line or plane.
- **Ordinary least squares (OLS)**: choosing weights that minimise the squared error.
- **Regularisation**: restricting a model, here by penalising large weights, to reduce overfitting.
- **Ridge / L2 penalty**: penalty on the sum of squared weights; shrinks all weights.
- **Lasso / L1 penalty**: penalty on the sum of absolute weights; sets some weights to zero.
- **Elastic net**: a mix of the L1 and L2 penalties.
- **Sparse model**: a model in which most weights are zero.
- **Logistic regression**: a linear classifier that outputs probabilities through the sigmoid.
- **Sigmoid**: the S-shaped function that maps any number to a value between 0 and 1.
- **Log loss (cross-entropy)**: the loss for predicted probabilities; minus the log of the probability given to the true class.
- **Odds / log-odds**: probability divided by one minus the probability / its logarithm.
- **Hinge loss / margin**: the loss used by linear SVMs / the distance of a point from the decision boundary on the correct side.
- **`alpha`, `C`**: regularisation settings; larger `alpha` and smaller `C` both mean stronger regularisation.
- **One-vs-rest**: handling several classes with one two-class model per class.
- **Softmax**: the function that turns a list of scores into probabilities adding up to 1.

## Check yourself

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
